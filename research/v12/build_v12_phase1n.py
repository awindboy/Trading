#!/usr/bin/env python3
"""Execute the frozen V12 Phase-1N lower-timeframe temporal-information audit."""

from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from build_v12_phase0 import PrefixAudit, iter_m1_prefix, parse_cutoff
from build_v12_phase1d import build_clusters, load_calendar, load_market, scope_times, write_json
from build_v12_phase1e import session_context
from build_v12_phase1g import EventIndex, path_context
from build_v12_phase1l import LaneEngine
from v12_phase0_core import sha256_file
from v12_phase1g_core import (
    Encoder, clock_coordinates, daily_prior_medians, fit_ridge_logistic, generate_boxes,
    MarketIndex, predict_logistic, weighted_metrics,
)
from v12_phase1h_core import apply_quintile_thresholds, capital_summary, train_quintile_thresholds
from v12_phase1l_core import Bar, HAStream, scorecard, true_range
from v12_phase1n_core import (
    CONTRACT_VERSION, age_hours, direction_relation, micro_path_features, wave_distribution_features,
)


PREFIX = "V12_PHASE1N_"
FOLDS = (
    ("F1", pd.Timestamp("2025-03-31 23:59:59"), pd.Timestamp("2025-04-01"), pd.Timestamp("2025-09-30 23:59:59")),
    ("F2", pd.Timestamp("2025-09-30 23:59:59"), pd.Timestamp("2025-10-01"), pd.Timestamp("2026-03-31 23:59:59")),
    ("F3", pd.Timestamp("2026-03-31 23:59:59"), pd.Timestamp("2026-04-01"), pd.Timestamp("2026-09-18 23:57:00")),
)
OUTCOMES = {"HARD_SL": "stop_hit", "RIGHT_TAIL_R_GE_3": "right_tail_ge_3", "RIGHT_TAIL_R_GE_5": "right_tail_ge_5"}
RIDGES = (0.1, 1.0, 10.0, 100.0)


class Aggregator:
    def __init__(self, minutes: int):
        self.minutes = minutes
        self.current: Bar | None = None

    def push(self, ts: datetime, o: float, h: float, l: float, c: float) -> Bar | None:
        minute = (ts.hour * 60 + ts.minute) // self.minutes * self.minutes
        start = ts.replace(hour=minute // 60, minute=minute % 60, second=0, microsecond=0)
        if self.current is None:
            self.current = Bar(start, o, h, l, c)
            return None
        if start != self.current.start:
            done = self.current
            self.current = Bar(start, o, h, l, c)
            return done
        self.current.high = max(self.current.high, h)
        self.current.low = min(self.current.low, l)
        self.current.close = c
        self.current.rows += 1
        return None


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(path)
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def verify_hash(path: Path, expected: str, label: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} hash mismatch: {observed} != {expected}")


def predict_ha(stream: HAStream, bar: Bar) -> tuple[int, float]:
    close = (bar.open + bar.high + bar.low + stream.close_weight * bar.close) / (3.0 + stream.close_weight)
    if stream.records:
        previous = stream.records[-1]
        open_ = stream.alpha * previous.ha_open + (1.0 - stream.alpha) * previous.ha_close
    else:
        open_ = 0.5 * (bar.open + bar.close)
    return (1 if close >= open_ else -1), close - open_


def causal_scale(lane: LaneEngine, bar: Bar) -> float:
    if len(lane.bars) < 180 or not lane.atr180 or not math.isfinite(lane.atr180[-1]):
        return math.nan
    return float(lane.atr180[-1])


def higher_features(lane: LaneEngine, direction: int, prefix: str) -> dict[str, float]:
    output: dict[str, float] = {}
    for name in ("fast", "std", "slow"):
        stream = getattr(lane, name)
        latest = stream.records[-1] if stream.records else None
        output[f"{prefix}_{name}_align"] = int(latest is not None and latest.ha_dir == direction)
        output[f"{prefix}_{name}_body_aligned"] = direction * latest.ha_body if latest is not None else np.nan
    output[f"{prefix}_fast_run_age_bars"] = lane.run_k if lane.last_dir else 0
    return output


def current_ha_features(lane: LaneEngine, bar: Bar, direction: int, scale: float) -> dict[str, float]:
    output = {}
    for name in ("fast", "std", "slow"):
        predicted_direction, body = predict_ha(getattr(lane, name), bar)
        output[f"main_{name}_align"] = int(predicted_direction == direction)
        output[f"main_{name}_body_aligned_atr"] = direction * body / scale
    output["main_raw_body_aligned_atr"] = direction * (bar.close - bar.open) / scale
    output["main_range_atr"] = (bar.high - bar.low) / scale
    output["main_close_location_aligned"] = direction * (bar.close - (bar.high + bar.low) / 2.0) / max(bar.high - bar.low, 0.01)
    return output


def subset_records(records: list, start: datetime, end: datetime, count: int) -> list:
    return [row for row in records[-max(count * 3, count):] if start <= row.start < end][-count:]


def build_ledgers(m1_path: Path, cutoff: datetime) -> tuple[dict[str, pd.DataFrame], PrefixAudit]:
    audit = PrefixAudit()
    aggregators = {minutes: Aggregator(minutes) for minutes in (5, 15, 60, 240)}
    m5_stream = HAStream(2.0, 0.25)
    h4 = LaneEngine("H4", 240)
    h1 = LaneEngine("H1", 60)
    m15 = LaneEngine("M15", 15)
    recent_m1: deque[SimpleNamespace] = deque(maxlen=90)

    for number, row in enumerate(iter_m1_prefix(m1_path, cutoff, audit=audit), 1):
        recent_m1.append(SimpleNamespace(
            start=row.timestamp, raw_open=row.open, raw_high=row.high, raw_low=row.low, raw_close=row.close,
        ))
        completed = {
            minutes: aggregate.push(row.timestamp, row.open, row.high, row.low, row.close)
            for minutes, aggregate in aggregators.items()
        }
        if completed[5] is not None:
            m5_stream.append(completed[5])
        if completed[240] is not None:
            h4.on_complete(completed[240], row.timestamp, row.open, row.high, row.low)

        if completed[15] is not None:
            bar = completed[15]
            decision = bar.start + timedelta(minutes=15)
            scale = causal_scale(m15, bar)
            direction, _ = predict_ha(m15.fast, bar)
            features = {}
            if math.isfinite(scale):
                features.update(current_ha_features(m15, bar, direction, scale))
                features.update(higher_features(h1, direction, "h1"))
                features.update(higher_features(h4, direction, "h4"))
                lower = subset_records(m5_stream.records, bar.start, decision, 3)
                features.update(micro_path_features(lower, direction, bar.open, scale, "m5"))
                raw_lower = [value for value in recent_m1 if bar.start <= value.start < decision]
                features.update(wave_distribution_features(raw_lower, direction, bar.open, bar.high, bar.low, scale))
            m15.on_complete(bar, row.timestamp, row.open, row.high, row.low, features)

        if completed[60] is not None:
            bar = completed[60]
            decision = bar.start + timedelta(hours=1)
            scale = causal_scale(h1, bar)
            direction, _ = predict_ha(h1.fast, bar)
            features = {}
            if math.isfinite(scale):
                features.update(current_ha_features(h1, bar, direction, scale))
                features.update(higher_features(h4, direction, "h4"))
                lower = subset_records(m15.fast.records, bar.start, decision, 4)
                features.update(micro_path_features(lower, direction, bar.open, scale, "m15"))
                wave_lower = subset_records(m5_stream.records, bar.start, decision, 12)
                features.update(wave_distribution_features(wave_lower, direction, bar.open, bar.high, bar.low, scale))
            h1.on_complete(bar, row.timestamp, row.open, row.high, row.low, features)

        h4.check_stops(row.timestamp, row.open, row.high, row.low)
        h1.check_stops(row.timestamp, row.open, row.high, row.low)
        m15.check_stops(row.timestamp, row.open, row.high, row.low)
        if number % 500000 == 0:
            print(f"streamed {number} M1 rows")

    output = {}
    for population, lane in (("H1_K1", h1), ("M15_K1", m15)):
        frame = lane.frame()
        frame = frame.loc[frame["k"] == 1].copy()
        frame["population"] = population
        frame["direction"] = np.where(frame["dir"] > 0, "LONG", "SHORT")
        frame["decision_time"] = pd.to_datetime(frame["decision"])
        frame["right_tail_ge_3"] = (frame["R"] >= 3.0).astype(int)
        frame["right_tail_ge_5"] = (frame["R"] >= 5.0).astype(int)
        frame["funded_units"] = 1.0
        frame["stopped_loss_units"] = frame["stop_hit"].astype(float)
        frame["combined_R_units"] = frame["R"].astype(float)
        frame["right_tail_ge_5R_units"] = np.where(frame["R"] >= 5.0, frame["R"], 0.0)
        frame["right_tail_presence"] = frame["right_tail_ge_5"]
        output[population] = frame.sort_values(["decision_time", "signal_id"]).reset_index(drop=True)
    return output, audit


def add_static_and_clock(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.itertuples(index=False):
        value = row._asdict()
        timestamp = pd.Timestamp(value["decision_time"]).to_pydatetime()
        value.update(session_context(timestamp))
        value.update(clock_coordinates(timestamp))
        value["broker_hour"] = timestamp.hour
        rows.append(value)
    return pd.DataFrame(rows)


def add_event_features(frame: pd.DataFrame, clusters: pd.DataFrame) -> pd.DataFrame:
    events = clusters.loc[clusters["usd_modhigh"]].sort_values("event_time").reset_index(drop=True)
    times = events["event_time"].to_numpy(dtype="datetime64[ns]")
    result = frame.copy()
    since, until, surprise, prior_sector, prior_codes = [], [], [], [], []
    for value in pd.to_datetime(result["decision_time"]):
        position = int(np.searchsorted(times, np.datetime64(value), side="left"))
        previous = events.iloc[position - 1] if position else None
        following = events.iloc[position] if position < len(events) else None
        since.append((value - previous["event_time"]).total_seconds() / 60 if previous is not None else np.nan)
        until.append((following["event_time"] - value).total_seconds() / 60 if following is not None else np.nan)
        surprise.append(previous["max_signed_surprise_z"] if previous is not None else np.nan)
        prior_sector.append(str(previous["sectors"]) if previous is not None else "NONE")
        prior_codes.append(str(previous["event_codes"]) if previous is not None else "NONE")
    result["usd_modhigh_minutes_since"] = since
    result["usd_modhigh_minutes_until"] = until
    result["usd_modhigh_previous_surprise_z"] = surprise
    result["usd_modhigh_previous_sectors"] = prior_sector
    result["usd_modhigh_previous_codes"] = prior_codes
    return result


def attach_parent(frame: pd.DataFrame, source: pd.DataFrame, observed_field: str,
                  parent_direction_field: str, prefix: str) -> pd.DataFrame:
    left = frame.sort_values("decision_time").copy()
    right = source.copy()
    right["_observed"] = pd.to_datetime(right[observed_field])
    right = right.sort_values("_observed")
    keep = ["_observed", "interaction", parent_direction_field]
    for column in ("sweep_depth_c1_range", "sweep_depth_atr", "close_location_c1", "activation_status", "h4_atr180"):
        if column in right:
            keep.append(column)
    right = right[keep].rename(columns={
        "interaction": f"{prefix}_interaction", parent_direction_field: f"{prefix}_direction",
        "sweep_depth_c1_range": f"{prefix}_sweep_depth_c1_range",
        "sweep_depth_atr": f"{prefix}_sweep_depth_atr",
        "close_location_c1": f"{prefix}_close_location_c1",
        "activation_status": f"{prefix}_activation_status",
        "h4_atr180": f"{prefix}_atr180",
    })
    merged = pd.merge_asof(left, right, left_on="decision_time", right_on="_observed", direction="backward")
    merged[f"{prefix}_direction_relation"] = [
        direction_relation(child, parent)
        for child, parent in zip(merged["dir"], merged[f"{prefix}_direction"])
    ]
    merged[f"{prefix}_age_hours"] = [
        age_hours(pd.Timestamp(decision).to_pydatetime(), observed)
        if pd.notna(observed) else np.nan
        for decision, observed in zip(merged["decision_time"], merged["_observed"])
    ]
    return merged.drop(columns=["_observed"])


def path_enrich(frame: pd.DataFrame, market: pd.DataFrame, boxes, events: EventIndex, medians: dict) -> pd.DataFrame:
    source = frame.copy()
    source["decision_time"] = pd.to_datetime(source["decision_time"])
    return pd.DataFrame(path_context(source, "decision_time", "signal_id", market, boxes, events, medians))


def feature_specs(frame: pd.DataFrame) -> dict[str, tuple[list[str], list[str]]]:
    def present(values):
        return [value for value in values if value in frame.columns]

    ha_num = present([
        "stop_dist_atr", "fast_body_atr", "main_fast_body_aligned_atr", "main_std_body_aligned_atr",
        "main_slow_body_aligned_atr", "main_raw_body_aligned_atr", "main_range_atr",
        "main_close_location_aligned", "h1_fast_body_aligned", "h1_std_body_aligned", "h1_slow_body_aligned",
        "h4_fast_body_aligned", "h4_std_body_aligned", "h4_slow_body_aligned", "h1_fast_run_age_bars",
        "h4_fast_run_age_bars",
    ])
    ha_cat = present(["std_align", "slow_align", "main_fast_align", "main_std_align", "main_slow_align",
                      "h1_fast_align", "h1_std_align", "h1_slow_align", "h4_fast_align", "h4_std_align", "h4_slow_align"])
    static_cat = present(["session_phase", "new_york_weekday", "broker_hour"])
    clock_num = [column for column in frame if column.startswith("clock_")]
    event_num = present(["usd_modhigh_minutes_since", "usd_modhigh_minutes_until", "usd_modhigh_previous_surprise_z"])
    event_cat = present(["usd_modhigh_previous_sectors"])
    path_suffix = (
        "range_norm", "source_net_aligned_norm", "source_efficiency_aligned", "minutes_since_end",
        "favorable_broken", "opposed_broken", "favorable_extension_norm", "opposed_extension_norm",
        "extension_balance_norm", "dwell_aligned_bias", "dwell_outside_fraction", "boundary_transitions",
        "outside_to_inside_reentries", "minutes_since_last_transition", "settlement_aligned",
        "post_net_aligned_norm", "post_efficiency_aligned", "usd_events_since_box", "usd_max_abs_surprise_since_box",
    )
    path_num = present([f"{prefix}_{suffix}" for prefix in ("asia", "lonny", "london", "ny") for suffix in path_suffix])
    path_num += [column for column in frame if column.startswith(("asia_lonny_", "lonny_ny_", "asia_london_", "london_ny_"))
                 and pd.to_numeric(frame[column], errors="coerce").notna().any()]
    parent_num = [column for column in frame if column.endswith(("_sweep_depth_c1_range", "_sweep_depth_atr", "_close_location_c1", "_age_hours", "_atr180"))]
    parent_cat = [column for column in frame if column.endswith(("_interaction", "_direction_relation", "_activation_status"))]
    micro_num = [column for column in frame if column.startswith(("m5_", "m15_"))]
    wave_num = [column for column in frame if column.startswith("wave_")]

    def joined(*groups):
        values = []
        for group in groups:
            values.extend(group)
        return list(dict.fromkeys(values))

    return {
        "HA_ONLY": (ha_num, ha_cat),
        "HA_PLUS_STATIC_TIME": (ha_num, joined(ha_cat, static_cat)),
        "HA_PLUS_CONTINUOUS_CLOCK": (joined(ha_num, clock_num), ha_cat),
        "HA_PLUS_EVENT": (joined(ha_num, event_num), joined(ha_cat, event_cat)),
        "HA_PLUS_SESSION_PATH": (joined(ha_num, path_num), ha_cat),
        "HA_PLUS_CRT_PARENT": (joined(ha_num, parent_num), joined(ha_cat, parent_cat)),
        "HA_PLUS_MICRO_PATH": (joined(ha_num, micro_num), ha_cat),
        "HA_PLUS_WAVE": (joined(ha_num, wave_num), ha_cat),
        "ALL_TIME_INFORMATION": (joined(ha_num, clock_num, event_num, path_num), joined(ha_cat, static_cat, event_cat)),
        "FULL_ASSEMBLY": (joined(ha_num, clock_num, event_num, path_num, parent_num, micro_num, wave_num),
                          joined(ha_cat, static_cat, event_cat, parent_cat)),
    }


def select_ridge(train: pd.DataFrame, numeric: list[str], categorical: list[str], target: str) -> tuple[float, float]:
    cut = max(50, int(len(train) * 0.8))
    inner_start = pd.Timestamp(train.iloc[cut]["decision_time"])
    inside = train.loc[(train["decision_time"] < inner_start) & (train["label_available_at"] <= inner_start)]
    validation = train.loc[train["decision_time"] >= inner_start]
    if len(validation) < 20:
        raise ValueError("insufficient inner validation rows")
    best = (None, float("inf"))
    for ridge in RIDGES:
        encoder = Encoder(numeric, categorical).fit(inside)
        beta = fit_ridge_logistic(encoder.transform(inside), inside[target].to_numpy(int), np.ones(len(inside)), ridge)
        probability = predict_logistic(encoder.transform(validation), beta)
        loss = weighted_metrics(validation[target].to_numpy(int), probability, np.ones(len(validation)))["logloss"]
        if loss < best[1]:
            best = (ridge, loss)
    return float(best[0]), float(best[1])


def fit_models(population: str, frame: pd.DataFrame, specs: dict[str, tuple[list[str], list[str]]]):
    metrics, predictions, thresholds = [], [], []
    work = frame.sort_values(["decision_time", "signal_id"]).copy()
    work["label_available_at"] = pd.to_datetime(work["label_available_at"])
    for fold, train_end, test_start, test_end in FOLDS:
        train = work.loc[(work["decision_time"] <= train_end) & (work["label_available_at"] <= train_end)]
        test = work.loc[(work["decision_time"] >= test_start) & (work["decision_time"] <= test_end)]
        liquidity = pd.to_numeric(train["prior60_daily_range_median"], errors="coerce").dropna()
        liquidity_cuts = np.quantile(liquidity, [1 / 3, 2 / 3])
        for model, (numeric, categorical) in specs.items():
            print(f"fitting {population} {fold} {model}")
            heads = {}
            for outcome, target in OUTCOMES.items():
                ridge, inner_loss = select_ridge(train, numeric, categorical, target)
                encoder = Encoder(numeric, categorical).fit(train)
                beta = fit_ridge_logistic(encoder.transform(train), train[target].to_numpy(int), np.ones(len(train)), ridge)
                p_train = predict_logistic(encoder.transform(train), beta)
                p_test = predict_logistic(encoder.transform(test), beta)
                heads[outcome] = (p_train, p_test)
                metrics.append({
                    "population": population, "model": model, "outcome": outcome, "fold": fold,
                    "train_rows": len(train), "test_rows": len(test), "selected_lambda": ridge,
                    "inner_logloss": inner_loss, "numeric_features": len(numeric), "categorical_features": len(categorical),
                    **weighted_metrics(test[target].to_numpy(int), p_test, np.ones(len(test))),
                })
            train_score = heads["RIGHT_TAIL_R_GE_5"][0] - heads["HARD_SL"][0]
            test_score = heads["RIGHT_TAIL_R_GE_5"][1] - heads["HARD_SL"][1]
            cuts = train_quintile_thresholds(train_score)
            for index, value in enumerate(cuts, 1):
                thresholds.append({"population": population, "model": model, "fold": fold,
                                   "threshold_number": index, "conviction_score_threshold": float(value)})
            local = test[["signal_id", "decision_time", "year", "direction", "R", "stop_hit",
                          "funded_units", "stopped_loss_units", "combined_R_units", "right_tail_ge_5R_units",
                          "right_tail_presence", "prior60_daily_range_median"]].copy()
            local.insert(0, "population", population)
            local.insert(1, "model", model)
            local.insert(2, "fold", fold)
            local["p_stop"] = heads["HARD_SL"][1]
            local["p_ge3"] = heads["RIGHT_TAIL_R_GE_3"][1]
            local["p_ge5"] = heads["RIGHT_TAIL_R_GE_5"][1]
            local["conviction_score"] = test_score
            local["conviction_band"] = apply_quintile_thresholds(test_score, cuts)
            local["liquidity_tercile"] = np.searchsorted(liquidity_cuts, local["prior60_daily_range_median"], side="right") + 1
            predictions.append(local)
    return pd.DataFrame(metrics), pd.concat(predictions, ignore_index=True), pd.DataFrame(thresholds)


def capital_tables(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, stability = [], []
    group_fields = ["population", "model"]
    for keys, group in predictions.groupby(group_fields, sort=True):
        population, model = keys
        for fold, cell in list(group.groupby("fold")) + [("POOLED", group)]:
            base = capital_summary(cell)
            rows.append({"population": population, "model": model, "fold": fold, "segment": "ALL", **base})
            for band, segment in cell.groupby("conviction_band"):
                summary = capital_summary(segment)
                scale = base["stopped_units"] / summary["stopped_units"] if summary["stopped_units"] else np.nan
                rows.append({"population": population, "model": model, "fold": fold, "segment": f"Q{int(band)}",
                             "equal_total_stop_budget_scale": scale,
                             "equal_total_stop_budget_net_R": summary["net_R_units"] * scale if np.isfinite(scale) else np.nan,
                             **summary})
        for dimension in ("direction", "year", "liquidity_tercile"):
            for level, cell in group.groupby(dimension):
                for segment, selected in (("ALL", cell), ("Q5", cell.loc[cell["conviction_band"] == 5])):
                    stability.append({"population": population, "model": model, "dimension": dimension.upper(),
                                      "level": level, "segment": segment, **capital_summary(selected)})
    return pd.DataFrame(rows), pd.DataFrame(stability)


def promotion_screen(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for population in sorted(metrics["population"].unique()):
        baseline = metrics.loc[(metrics["population"] == population) & (metrics["model"] == "HA_ONLY")]
        for model in sorted(metrics.loc[metrics["population"] == population, "model"].unique()):
            local = metrics.loc[(metrics["population"] == population) & (metrics["model"] == model)]
            detail = {}
            passed_heads = []
            for outcome in ("HARD_SL", "RIGHT_TAIL_R_GE_5"):
                left = local.loc[local["outcome"] == outcome].set_index("fold")["logloss"]
                right = baseline.loc[baseline["outcome"] == outcome].set_index("fold")["logloss"]
                delta = left - right
                detail[f"{outcome.lower()}_mean_logloss_delta"] = float(delta.mean())
                detail[f"{outcome.lower()}_improved_folds"] = int((delta < 0).sum())
                passed_heads.append(delta.mean() < 0 and int((delta < 0).sum()) >= 2)
            rows.append({"population": population, "model": model, **detail,
                         "promotion_screen_pass": bool(all(passed_heads) and model != "HA_ONLY")})
    return pd.DataFrame(rows)


def baseline_scorecards(populations: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for population, frame in populations.items():
        for scope, cell in [("POOLED", frame)] + [(str(year), frame.loc[frame["year"] == year]) for year in range(2022, 2027)]:
            if len(cell):
                rows.append({"population": population, "scope": scope, **scorecard(cell)})
    return pd.DataFrame(rows)


def save_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n")


def finalize_existing(args, contract: dict, cutoff: datetime) -> None:
    hashes = contract["source_hashes"]
    audit = PrefixAudit()
    for _ in iter_m1_prefix(args.m1, cutoff, audit=audit):
        pass
    if audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("finalization prefix hash mismatch")
    _, calendar_diagnostics = load_calendar(args.calendar, cutoff, args.calendar_overrides)
    screen = pd.read_csv(args.output / f"{PREFIX}PROMOTION_SCREEN.csv")
    population_rows = {}
    for population in ("H1_K1", "M15_K1"):
        path = args.output / f"{PREFIX}{population}_ENRICHED_LEDGER.csv"
        with path.open("r", encoding="utf-8") as handle:
            population_rows[population] = max(0, sum(1 for _ in handle) - 1)
    summary = {
        "contract_version": CONTRACT_VERSION,
        "evidence_status": contract["evidence_status"],
        "population_rows": population_rows,
        "prefix_rows": audit.parsed_price_rows,
        "prefix_sha256": audit.prefix_sha256,
        "calendar": calendar_diagnostics,
        "promotion_passes": screen.loc[screen["promotion_screen_pass"]].to_dict("records"),
        "trade_authority": False,
        "sizing_authority": False,
    }
    write_json(args.output / f"{PREFIX}SUMMARY.json", summary)
    manifest = {
        path.name: sha256_file(path)
        for path in sorted(args.output.glob(f"{PREFIX}*"))
        if path.name != f"{PREFIX}RELEASE_MANIFEST.json"
    }
    write_json(args.output / f"{PREFIX}RELEASE_MANIFEST.json", manifest)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


def rerun_models_existing(output: Path) -> None:
    metrics_parts, prediction_parts, threshold_parts, feature_inventory = [], [], [], []
    for population in ("H1_K1", "M15_K1"):
        path = output / f"{PREFIX}{population}_ENRICHED_LEDGER.csv"
        work = pd.read_csv(path, parse_dates=["decision_time", "label_available_at"])
        specs = feature_specs(work)
        for model, (numeric, categorical) in specs.items():
            feature_inventory.append({"population": population, "model": model,
                                      "numeric_count": len(numeric), "categorical_count": len(categorical),
                                      "numeric": "|".join(numeric), "categorical": "|".join(categorical)})
        metric, prediction, threshold = fit_models(population, work, specs)
        metrics_parts.append(metric)
        prediction_parts.append(prediction)
        threshold_parts.append(threshold)
    metrics = pd.concat(metrics_parts, ignore_index=True)
    predictions = pd.concat(prediction_parts, ignore_index=True)
    thresholds = pd.concat(threshold_parts, ignore_index=True)
    capital_rows, stability = capital_tables(predictions)
    screen = promotion_screen(metrics)
    save_csv(metrics, output / f"{PREFIX}WALK_FORWARD_METRICS.csv")
    save_csv(predictions, output / f"{PREFIX}TEST_PREDICTIONS.csv")
    save_csv(thresholds, output / f"{PREFIX}TRAIN_ONLY_THRESHOLDS.csv")
    save_csv(capital_rows, output / f"{PREFIX}CAPITAL_BANDS.csv")
    save_csv(stability, output / f"{PREFIX}STABILITY.csv")
    save_csv(screen, output / f"{PREFIX}PROMOTION_SCREEN.csv")
    save_csv(pd.DataFrame(feature_inventory), output / f"{PREFIX}FEATURE_INVENTORY.csv")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1n_contract.json")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--calendar", type=Path, default=Path.home() / "AppData/Roaming/MetaQuotes/Terminal/Common/Files/V12_PHASE1E_MQL5_CALENDAR_SNAPSHOT.csv")
    parser.add_argument("--calendar-overrides", type=Path, default=repo / "research/v12/v12_calendar_time_overrides.json")
    parser.add_argument("--phase0", type=Path, default=repo / "output/v12_phase0_event_universe_20260923/V12_PHASE0_PARENT_EVENTS.csv")
    parser.add_argument("--phase1b", type=Path, default=repo / "output/v12_phase1b_h4m5_journey_overlay_20260923/V12_PHASE1B_H4_CRT_DECISIONS.csv")
    parser.add_argument("--source-boxes", type=Path, default=repo / "output/v12_phase1g_continuous_intraday_path_20260924_a/V12_PHASE1G_SOURCE_BOXES.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1n_lower_timeframe_temporal_information_20260925_a")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--finalize-only", action="store_true")
    parser.add_argument("--models-only", action="store_true")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract/core mismatch")
    cutoff = parse_cutoff(contract["mechanism_cutoff"])
    if args.finalize_only:
        finalize_existing(args, contract, cutoff)
        return
    if args.models_only:
        rerun_models_existing(args.output)
        return
    safe_output(args.output, args.replace)
    hashes = contract["source_hashes"]
    for path, key, label in (
        (args.m1, "raw_m1_full_sha256", "raw M1"), (args.calendar, "calendar_snapshot_sha256", "calendar"),
        (args.phase0, "phase0_parent_events_sha256", "Phase0 parent"),
        (args.phase1b, "phase1b_h4_crt_decisions_sha256", "Phase1B H4 CRT"),
        (args.source_boxes, "phase1g_source_boxes_sha256", "Phase1G source boxes"),
    ):
        verify_hash(path, hashes[key], label)

    populations, stream_audit = build_ledgers(args.m1, cutoff)
    if stream_audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("streaming prefix hash mismatch")
    market, market_audit = load_market(args.m1, cutoff)
    if market_audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("market prefix hash mismatch")
    calendar, calendar_diagnostics = load_calendar(args.calendar, cutoff, args.calendar_overrides)
    clusters = build_clusters(calendar)
    event_index = EventIndex(clusters)
    boxes = generate_boxes(MarketIndex(market), market["timestamp"].min().date(), cutoff.date())
    medians = daily_prior_medians(market)
    phase0 = pd.read_csv(args.phase0)
    phase0 = phase0.loc[phase0["lane"] == "D1_TO_H1"].copy()
    phase1b = pd.read_csv(args.phase1b)

    enriched = {}
    metrics_parts, prediction_parts, threshold_parts = [], [], []
    feature_inventory = []
    for population, frame in populations.items():
        print(f"enriching {population}: {len(frame)} candidates")
        work = add_static_and_clock(frame)
        work = add_event_features(work, clusters)
        work = path_enrich(work, market, boxes, event_index, medians)
        if population == "H1_K1":
            work = attach_parent(work, phase0, "completion_observed_at", "hypothesis_direction", "parent")
        else:
            work = attach_parent(work, phase1b, "c2_completed_by", "direction", "parent")
        work["decision_time"] = pd.to_datetime(work["decision_time"])
        if (work["decision_time"] > cutoff).any():
            raise ValueError("post-cutoff candidate detected")
        specs = feature_specs(work)
        for model, (numeric, categorical) in specs.items():
            feature_inventory.append({"population": population, "model": model,
                                      "numeric_count": len(numeric), "categorical_count": len(categorical),
                                      "numeric": "|".join(numeric), "categorical": "|".join(categorical)})
        metric, prediction, threshold = fit_models(population, work, specs)
        metrics_parts.append(metric)
        prediction_parts.append(prediction)
        threshold_parts.append(threshold)
        enriched[population] = work

    metrics = pd.concat(metrics_parts, ignore_index=True)
    predictions = pd.concat(prediction_parts, ignore_index=True)
    thresholds = pd.concat(threshold_parts, ignore_index=True)
    capital, stability = capital_tables(predictions)
    screen = promotion_screen(metrics)
    scorecards = baseline_scorecards(populations)

    save_csv(scorecards, args.output / f"{PREFIX}POPULATION_SCORECARDS.csv")
    save_csv(metrics, args.output / f"{PREFIX}WALK_FORWARD_METRICS.csv")
    save_csv(predictions, args.output / f"{PREFIX}TEST_PREDICTIONS.csv")
    save_csv(thresholds, args.output / f"{PREFIX}TRAIN_ONLY_THRESHOLDS.csv")
    save_csv(capital, args.output / f"{PREFIX}CAPITAL_BANDS.csv")
    save_csv(stability, args.output / f"{PREFIX}STABILITY.csv")
    save_csv(screen, args.output / f"{PREFIX}PROMOTION_SCREEN.csv")
    save_csv(pd.DataFrame(feature_inventory), args.output / f"{PREFIX}FEATURE_INVENTORY.csv")
    for population, work in enriched.items():
        save_csv(work, args.output / f"{PREFIX}{population}_ENRICHED_LEDGER.csv")

    summary = {
        "contract_version": CONTRACT_VERSION,
        "evidence_status": contract["evidence_status"],
        "population_rows": {name: len(frame) for name, frame in populations.items()},
        "prefix_rows": stream_audit.parsed_price_rows,
        "prefix_sha256": stream_audit.prefix_sha256,
        "calendar": calendar_diagnostics,
        "promotion_passes": screen.loc[screen["promotion_screen_pass"]].to_dict("records"),
        "trade_authority": False,
        "sizing_authority": False,
    }
    write_json(args.output / f"{PREFIX}SUMMARY.json", summary)
    manifest = {
        path.name: sha256_file(path)
        for path in sorted(args.output.glob(f"{PREFIX}*"))
        if path.name != f"{PREFIX}RELEASE_MANIFEST.json"
    }
    write_json(args.output / f"{PREFIX}RELEASE_MANIFEST.json", manifest)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
