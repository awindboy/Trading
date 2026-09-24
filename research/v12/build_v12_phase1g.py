#!/usr/bin/env python3
"""Build the frozen V12 Phase-1G continuous intraday-path study."""

from __future__ import annotations

import argparse
import json
from bisect import bisect_left, bisect_right
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase0 import parse_cutoff
from build_v12_phase1d import build_clusters, load_calendar, load_market, write_csv, write_json
from v12_phase0_core import sha256_file
from v12_phase1g_core import (
    Encoder,
    MarketIndex,
    boxes_by_family,
    clock_coordinates,
    cross_box,
    daily_prior_medians,
    fit_ridge_linear,
    fit_ridge_logistic,
    generate_boxes,
    latest_box,
    predict_logistic,
    weighted_metrics,
    weighted_regression_metrics,
)


PREFIX = "V12_PHASE1G_"
FAMILIES = ("ASIA_COMPLETE", "LONDON_AT_NEW_YORK_OPEN", "LONDON_COMPLETE", "NEW_YORK_COMPLETE")
FAMILY_PREFIX = {
    "ASIA_COMPLETE": "asia",
    "LONDON_AT_NEW_YORK_OPEN": "lonny",
    "LONDON_COMPLETE": "london",
    "NEW_YORK_COMPLETE": "ny",
}


def parse_time(value: object) -> datetime:
    return datetime.fromisoformat(str(value).replace(" ", "T"))


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(path)
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


class EventIndex:
    def __init__(self, clusters: pd.DataFrame):
        values = clusters.loc[clusters["usd_modhigh"]].sort_values("event_time").reset_index(drop=True)
        self.frame = values
        self.times = values["event_time"].to_numpy(dtype="datetime64[ns]")

    def interval(self, start: datetime, end: datetime) -> dict[str, float]:
        left = int(np.searchsorted(self.times, np.datetime64(start), side="left"))
        right = int(np.searchsorted(self.times, np.datetime64(end), side="left"))
        rows = self.frame.iloc[left:right]
        released = rows["max_abs_surprise_z"].dropna()
        return {
            "usd_events_since_box": int(len(rows)),
            "usd_max_abs_surprise_since_box": float(released.max()) if len(released) else np.nan,
        }

    def around(self, value: datetime | None, query: datetime) -> dict[str, object]:
        if value is None:
            return {"prior_minutes": np.nan, "following_minutes": np.nan,
                    "prior_codes": "", "following_codes": ""}
        position = int(np.searchsorted(self.times, np.datetime64(value), side="right"))
        prior_index = position - 1
        following_index = position
        prior = self.frame.iloc[prior_index] if prior_index >= 0 else None
        following = self.frame.iloc[following_index] if following_index < len(self.frame) else None
        return {
            "prior_minutes": ((value - prior["event_time"].to_pydatetime()).total_seconds() / 60.0) if prior is not None else np.nan,
            "following_minutes": ((following["event_time"].to_pydatetime() - value).total_seconds() / 60.0) if following is not None else np.nan,
            "prior_codes": str(prior["event_codes"]) if prior is not None else "",
            "following_codes": str(following["event_codes"]) if following is not None else "",
            "following_released_by_query": int(following is not None and following["event_time"].to_pydatetime() < query),
        }


def add_prefixed(target: dict, prefix: str, values: dict) -> None:
    for key, value in values.items():
        target[f"{prefix}_{key}"] = value


def box_record(box, norm: float) -> dict[str, object]:
    scale = max(norm, 0.01)
    return {
        "box_id": box.box_id,
        "local_date": box.local_date,
        "start": box.start.isoformat(),
        "end": box.end.isoformat(),
        "open": box.open,
        "high": box.high,
        "low": box.low,
        "close": box.close,
        "range": box.range,
        "range_norm": box.range / scale,
        "net": box.net,
        "net_norm": box.net / scale,
        "efficiency": box.efficiency,
        "observed_minutes": box.observed_minutes,
        "coverage": box.observed_minutes / max(box.scheduled_minutes, 1),
    }


def path_context(rows: pd.DataFrame, timestamp_field: str, id_field: str, market: pd.DataFrame,
                 boxes, events: EventIndex, medians: dict) -> list[dict]:
    index = MarketIndex(market)
    grouped = boxes_by_family(boxes)
    output: list[dict] = []
    for number, (_, row) in enumerate(rows.iterrows(), 1):
        query = parse_time(row[timestamp_field])
        norm = medians.get(query.date(), np.nan)
        if not np.isfinite(norm):
            norm = float(np.nanmedian(list(medians.values())))
        item = row.to_dict()
        item["query_time"] = query.isoformat()
        item["query_id"] = str(row[id_field])
        item["prior60_daily_range_median"] = norm
        item.update(clock_coordinates(query))
        selected = {}
        for family in FAMILIES:
            prefix = FAMILY_PREFIX[family]
            box = latest_box(grouped.get(family, []), query)
            selected[family] = box
            if box is None:
                item[f"{prefix}_available"] = 0
                continue
            add_prefixed(item, prefix, box_record(box, norm))
            path = index.path(box, query)
            for key in ("max_high_extension", "max_low_extension", "post_net", "post_path_length"):
                path[f"{key}_norm"] = float(path[key]) / max(norm, 0.01)
            direction = str(row.get("direction", row.get("new_fast_direction", "")))
            sign = 1.0 if direction == "LONG" else -1.0
            favorable_broken = int(path["high_broken"] if sign > 0 else path["low_broken"])
            opposed_broken = int(path["low_broken"] if sign > 0 else path["high_broken"])
            favorable_extension = float(path["max_high_extension_norm"] if sign > 0 else path["max_low_extension_norm"])
            opposed_extension = float(path["max_low_extension_norm"] if sign > 0 else path["max_high_extension_norm"])
            order = str(path["break_order"])
            if order in {"NONE", "SAME_M1_AMBIGUOUS"}:
                aligned_order = order
            elif (order == "HIGH_FIRST" and sign > 0) or (order == "LOW_FIRST" and sign < 0):
                aligned_order = "FAVORABLE_FIRST"
            else:
                aligned_order = "OPPOSED_FIRST"
            path.update({
                "source_net_aligned_norm": sign * box.net / max(norm, 0.01),
                "source_efficiency_aligned": sign * box.efficiency,
                "favorable_broken": favorable_broken,
                "opposed_broken": opposed_broken,
                "aligned_break_order": aligned_order,
                "favorable_extension_norm": favorable_extension,
                "opposed_extension_norm": opposed_extension,
                "extension_balance_norm": favorable_extension - opposed_extension,
                "dwell_aligned_bias": sign * (float(path["dwell_above_fraction"]) - float(path["dwell_below_fraction"])),
                "dwell_outside_fraction": float(path["dwell_above_fraction"]) + float(path["dwell_below_fraction"]),
                "settlement_aligned": sign * float(path["settlement_location"]),
                "post_net_aligned_norm": sign * float(path["post_net_norm"]),
                "post_efficiency_aligned": sign * float(path["post_efficiency"]),
            })
            add_prefixed(item, prefix, path)
            add_prefixed(item, prefix, events.interval(box.end, query))
            for edge in ("high", "low"):
                value = path[f"first_{edge}_break_time"]
                stamp = parse_time(value) if value else None
                add_prefixed(item, f"{prefix}_{edge}_break_event", events.around(stamp, query))
        pairs = (
            ("asia_lonny", selected["ASIA_COMPLETE"], selected["LONDON_AT_NEW_YORK_OPEN"]),
            ("lonny_ny", selected["LONDON_AT_NEW_YORK_OPEN"], selected["NEW_YORK_COMPLETE"]),
            ("asia_london", selected["ASIA_COMPLETE"], selected["LONDON_COMPLETE"]),
            ("london_ny", selected["LONDON_COMPLETE"], selected["NEW_YORK_COMPLETE"]),
        )
        for name, first, second in pairs:
            add_prefixed(item, name, cross_box(first, second, norm))
        output.append(item)
        if number % 500 == 0:
            print(f"enriched {number}/{len(rows)} {timestamp_field}")
    return output


def select_features(frame: pd.DataFrame, kind: str) -> dict[str, tuple[list[str], list[str]]]:
    clocks = [column for column in frame if column.startswith("clock_")]
    exact_events = [
        column for column in (
            "usd_modhigh_minutes_since", "usd_modhigh_minutes_until",
            "usd_modhigh_previous_max_abs_surprise_z",
        ) if column in frame
    ]
    compact_suffixes = (
        "available", "coverage", "range_norm", "source_net_aligned_norm", "source_efficiency_aligned",
        "minutes_since_end",
        "favorable_broken", "opposed_broken", "favorable_extension_norm", "opposed_extension_norm",
        "extension_balance_norm", "dwell_aligned_bias", "dwell_outside_fraction",
        "boundary_transitions", "outside_to_inside_reentries", "minutes_since_last_transition",
        "settlement_aligned", "post_net_aligned_norm", "post_efficiency_aligned",
        "usd_events_since_box", "usd_max_abs_surprise_since_box",
    )
    path_numeric = [
        f"{prefix}_{suffix}" for prefix in ("asia", "lonny", "london", "ny") for suffix in compact_suffixes
        if f"{prefix}_{suffix}" in frame.columns
    ]
    cross_numeric = [
        column for column in frame
        if column.startswith(("asia_lonny_", "lonny_ny_", "asia_london_", "london_ny_"))
        and pd.to_numeric(frame[column], errors="coerce").notna().any()
    ]
    break_cats = [f"{prefix}_aligned_break_order" for prefix in ("asia", "lonny", "london", "ny")
                  if f"{prefix}_aligned_break_order" in frame.columns]
    if kind == "child":
        structure_num = ["reinforcement_count_known", "journey_age_hours"]
        structure_cat = ["direction", "k", "relation", "journey_stage", "aligned_ordinal_bucket",
                         "target_parent_origin_interaction"]
        static_cat = ["entry_session_phase", "entry_new_york_weekday", "broker_hour", "usd_event_state"]
    else:
        structure_num = ["same_direction_external_arrivals_ending_run"]
        structure_cat = ["old_fast_direction", "new_fast_direction", "explanation_state",
                         "target_parent_origin_interaction"]
        static_cat = ["known_session_phase", "known_new_york_weekday", "broker_hour", "usd_event_state"]
    existing = lambda values: [value for value in values if value in frame.columns]
    structure_num, structure_cat, static_cat = map(existing, (structure_num, structure_cat, static_cat))
    return {
        "STRUCTURE_ONLY": (structure_num, structure_cat),
        "STRUCTURE_PLUS_STATIC_BUCKETS": (structure_num, structure_cat + static_cat),
        "STRUCTURE_PLUS_CONTINUOUS_TIME": (structure_num + clocks + exact_events, structure_cat),
        "STRUCTURE_PLUS_CONTINUOUS_PATH": (
            sorted(set(structure_num + clocks + exact_events + path_numeric + cross_numeric)),
            sorted(set(structure_cat + break_cats)),
        ),
    }


def diagnostic_feature_groups(frame: pd.DataFrame, kind: str) -> dict[str, tuple[list[str], list[str]]]:
    primary = select_features(frame, kind)
    base_num, base_cat = primary["STRUCTURE_ONLY"]
    full_num, full_cat = primary["STRUCTURE_PLUS_CONTINUOUS_PATH"]
    prefixes = ("asia", "lonny", "london", "ny")
    def fields(suffixes: tuple[str, ...]) -> list[str]:
        return [f"{prefix}_{suffix}" for prefix in prefixes for suffix in suffixes if f"{prefix}_{suffix}" in frame]
    range_fields = fields(("available", "coverage", "range_norm", "source_net_aligned_norm", "source_efficiency_aligned", "minutes_since_end"))
    boundary_fields = fields(("favorable_broken", "opposed_broken", "favorable_extension_norm",
                              "opposed_extension_norm", "extension_balance_norm"))
    settlement_fields = fields(("dwell_aligned_bias", "dwell_outside_fraction", "boundary_transitions",
                                "outside_to_inside_reentries", "minutes_since_last_transition",
                                "settlement_aligned", "post_net_aligned_norm", "post_efficiency_aligned"))
    cross_fields = [column for column in full_num if column.startswith(("asia_lonny_", "lonny_ny_", "asia_london_", "london_ny_"))]
    event_fields = [column for column in frame if column.startswith(prefixes) and (
        "usd_events_since_box" in column or "usd_max_abs_surprise_since_box" in column
        or "_break_event_prior_minutes" in column or "_break_event_following_minutes" in column
        or "_break_event_following_released_by_query" in column
    )]
    exact_event = [column for column in ("usd_modhigh_minutes_since", "usd_modhigh_minutes_until",
                                         "usd_modhigh_previous_max_abs_surprise_z") if column in frame]
    break_cats = [column for column in full_cat if column.endswith("_aligned_break_order")]
    non_event_full = [column for column in full_num if column not in exact_event and "usd_" not in column and "_break_event_" not in column]
    return {
        "DIAG_RANGE_FORMATION": (sorted(set(base_num + range_fields)), base_cat),
        "DIAG_BOUNDARY_CONSUMPTION": (sorted(set(base_num + boundary_fields)), sorted(set(base_cat + break_cats))),
        "DIAG_SETTLEMENT_REPAIR": (sorted(set(base_num + settlement_fields)), base_cat),
        "DIAG_CROSS_BOX_HANDOFF": (sorted(set(base_num + cross_fields)), base_cat),
        "DIAG_EVENT_SEQUENCE": (sorted(set(base_num + exact_event + event_fields)), base_cat),
        "DIAG_PATH_WITHOUT_EVENTS": (sorted(set(non_event_full)), full_cat),
    }


FOLDS = (
    ("F1", "2025-03-31T23:59:59", "2025-04-01T00:00:00", "2025-09-30T23:59:59"),
    ("F2", "2025-09-30T23:59:59", "2025-10-01T00:00:00", "2026-03-31T23:59:59"),
    ("F3", "2026-03-31T23:59:59", "2026-04-01T00:00:00", "2026-09-18T23:57:00"),
)


def fit_models(frame: pd.DataFrame, kind: str, time_field: str, id_field: str,
               outcomes: dict[str, tuple[str, str]], feature_specs=None,
               emit_predictions: bool = True) -> tuple[list[dict], list[dict], list[dict]]:
    work = frame.copy()
    work["_time"] = pd.to_datetime(work[time_field])
    features = feature_specs or select_features(work, kind)
    metrics: list[dict] = []
    predictions: list[dict] = []
    quintiles: list[dict] = []
    for outcome_name, (target_field, weight_field) in outcomes.items():
        valid = work.loc[pd.to_numeric(work[target_field], errors="coerce").notna()].copy()
        valid["_y"] = pd.to_numeric(valid[target_field], errors="coerce").astype(int)
        valid["_w"] = pd.to_numeric(valid[weight_field], errors="coerce").fillna(1.0).astype(float)
        for fold, train_end, test_start, test_end in FOLDS:
            train = valid.loc[valid["_time"] <= train_end].sort_values("_time")
            test = valid.loc[(valid["_time"] >= test_start) & (valid["_time"] <= test_end)].sort_values("_time")
            if len(train) < 100 or len(test) < 10 or train["_y"].nunique() < 2 or test["_y"].nunique() < 2:
                continue
            cut = max(50, int(len(train) * 0.8))
            inner_train, inner_valid = train.iloc[:cut], train.iloc[cut:]
            for model, (numeric, categorical) in features.items():
                best_lambda, best_loss = None, float("inf")
                for ridge in (0.1, 1.0, 10.0, 100.0):
                    encoder = Encoder(numeric, categorical).fit(inner_train)
                    beta = fit_ridge_logistic(encoder.transform(inner_train), inner_train["_y"].to_numpy(),
                                              inner_train["_w"].to_numpy(), ridge)
                    probability = predict_logistic(encoder.transform(inner_valid), beta)
                    loss = weighted_metrics(inner_valid["_y"].to_numpy(), probability,
                                            inner_valid["_w"].to_numpy())["logloss"]
                    if loss < best_loss:
                        best_lambda, best_loss = ridge, loss
                encoder = Encoder(numeric, categorical).fit(train)
                beta = fit_ridge_logistic(encoder.transform(train), train["_y"].to_numpy(),
                                          train["_w"].to_numpy(), float(best_lambda))
                probability = predict_logistic(encoder.transform(test), beta)
                score = weighted_metrics(test["_y"].to_numpy(), probability, test["_w"].to_numpy())
                metrics.append({
                    "population": kind, "outcome": outcome_name, "fold": fold, "model": model,
                    "train_rows": len(train), "test_rows": len(test), "positive_rate": np.average(test["_y"], weights=test["_w"]),
                    "selected_lambda": best_lambda, "inner_logloss": best_loss, "numeric_features": len(numeric),
                    "categorical_features": len(categorical), **score,
                })
                local = test[[id_field, "_time", "_y", "_w"]].copy()
                local["prediction"] = probability
                local["population"] = kind
                local["outcome"] = outcome_name
                local["fold"] = fold
                local["model"] = model
                for field in ("funded_units", "stopped_loss_units", "combined_R_units", "right_tail_ge_5R_units"):
                    if field in test:
                        local[field] = test[field].to_numpy()
                if emit_predictions:
                    predictions.extend(local.rename(columns={id_field: "record_id", "_time": "query_time", "_y": "actual", "_w": "weight"}).to_dict("records"))
                if kind == "child" and emit_predictions:
                    ranks = pd.Series(probability).rank(method="first")
                    bins = pd.qcut(ranks, q=min(5, len(test)), labels=False, duplicates="drop") + 1
                    capital = test.reset_index(drop=True).copy()
                    capital["quintile"] = bins.to_numpy()
                    for quintile, group in capital.groupby("quintile"):
                        quintiles.append({
                            "outcome": outcome_name, "fold": fold, "model": model, "prediction_quintile": int(quintile),
                            "children": len(group), "funded_units": group["funded_units"].sum(),
                            "stopped_units": group["stopped_loss_units"].sum(), "net_R_units": group["combined_R_units"].sum(),
                            "right_tail_ge_5R_units": group["right_tail_ge_5R_units"].sum(),
                            "actual_rate": np.average(group["_y"], weights=group["_w"]),
                        })
    return metrics, predictions, quintiles


def joint_score_capital(predictions: list[dict]) -> list[dict]:
    frame = pd.DataFrame(predictions)
    frame = frame.loc[(frame["population"] == "child") & (frame["model"] == "STRUCTURE_PLUS_CONTINUOUS_PATH")]
    index = ["fold", "record_id"]
    scores = frame.pivot_table(index=index, columns="outcome", values="prediction", aggfunc="first").reset_index()
    capital = frame.loc[frame["outcome"] == "STOP_HIT", index + ["funded_units", "stopped_loss_units",
                                                                   "combined_R_units", "right_tail_ge_5R_units"]]
    joined = scores.merge(capital, on=index, how="inner")
    rows = []
    for fold, group in joined.groupby("fold"):
        group = group.copy()
        group["stop_quintile"] = pd.qcut(group["STOP_HIT"].rank(method="first"), 5, labels=False) + 1
        group["tail_quintile"] = pd.qcut(group["GE5R_RIGHT_TAIL"].rank(method="first"), 5, labels=False) + 1
        for keys, cell in group.groupby(["stop_quintile", "tail_quintile"]):
            rows.append({
                "fold": fold, "stop_quintile": int(keys[0]), "tail_quintile": int(keys[1]),
                "children": len(cell), "funded_units": cell["funded_units"].sum(),
                "stopped_units": cell["stopped_loss_units"].sum(), "net_R_units": cell["combined_R_units"].sum(),
                "right_tail_ge_5R_units": cell["right_tail_ge_5R_units"].sum(),
            })
    return rows


def conviction_score_capital(predictions: list[dict]) -> list[dict]:
    frame = pd.DataFrame(predictions)
    frame = frame.loc[frame["population"] == "child"]
    index = ["model", "fold", "record_id"]
    scores = frame.pivot_table(index=index, columns="outcome", values="prediction", aggfunc="first").reset_index()
    capital = frame.loc[frame["outcome"] == "STOP_HIT", index + ["funded_units", "stopped_loss_units",
                                                                            "combined_R_units", "right_tail_ge_5R_units"]]
    joined = scores.merge(capital, on=index, how="inner")
    joined["conviction_score"] = joined["GE5R_RIGHT_TAIL"] - joined["STOP_HIT"]
    rows = []
    for keys, group in joined.groupby(["model", "fold"]):
        group = group.copy()
        group["conviction_quintile"] = pd.qcut(group["conviction_score"].rank(method="first"), 5, labels=False) + 1
        for quintile, cell in group.groupby("conviction_quintile"):
            rows.append({
                "model": keys[0], "fold": keys[1], "conviction_quintile": int(quintile),
                "children": len(cell), "funded_units": cell["funded_units"].sum(),
                "stopped_units": cell["stopped_loss_units"].sum(), "net_R_units": cell["combined_R_units"].sum(),
                "right_tail_ge_5R_units": cell["right_tail_ge_5R_units"].sum(),
            })
    return rows


def fit_run_length_models(frame: pd.DataFrame) -> list[dict]:
    work = frame.copy()
    work["_time"] = pd.to_datetime(work["known_at"])
    work["_target"] = np.log1p(pd.to_numeric(work["new_fast_run_h4_bars"], errors="coerce"))
    work = work.loc[work["_target"].notna()].sort_values("_time")
    features = select_features(work, "nha")
    rows = []
    for fold, train_end, test_start, test_end in FOLDS:
        train = work.loc[work["_time"] <= train_end]
        test = work.loc[(work["_time"] >= test_start) & (work["_time"] <= test_end)]
        if len(train) < 100 or len(test) < 10:
            continue
        cut = max(50, int(len(train) * 0.8))
        inner_train, inner_valid = train.iloc[:cut], train.iloc[cut:]
        for model, (numeric, categorical) in features.items():
            best_lambda, best_mse = None, float("inf")
            for ridge in (0.1, 1.0, 10.0, 100.0):
                encoder = Encoder(numeric, categorical).fit(inner_train)
                beta = fit_ridge_linear(encoder.transform(inner_train), inner_train["_target"].to_numpy(),
                                        np.ones(len(inner_train)), ridge)
                prediction = encoder.transform(inner_valid) @ beta
                mse = weighted_regression_metrics(inner_valid["_target"].to_numpy(), prediction,
                                                  np.ones(len(inner_valid)))["rmse"] ** 2
                if mse < best_mse:
                    best_lambda, best_mse = ridge, mse
            encoder = Encoder(numeric, categorical).fit(train)
            beta = fit_ridge_linear(encoder.transform(train), train["_target"].to_numpy(), np.ones(len(train)), float(best_lambda))
            prediction = encoder.transform(test) @ beta
            score = weighted_regression_metrics(test["_target"].to_numpy(), prediction, np.ones(len(test)))
            rows.append({"population": "nha", "outcome": "LOG1P_FAST_RUN_H4_BARS", "fold": fold,
                         "model": model, "train_rows": len(train), "test_rows": len(test),
                         "selected_lambda": best_lambda, "inner_mse": best_mse,
                         "numeric_features": len(numeric), "categorical_features": len(categorical), **score})
    return rows


def source_box_rows(boxes, medians: dict) -> list[dict]:
    fallback = float(np.nanmedian(list(medians.values())))
    rows = []
    for box in boxes:
        norm = medians.get(box.end.date(), fallback)
        rows.append({"box_family": box.family, **box_record(box, norm)})
    return rows


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1g_contract.json")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--calendar", type=Path, default=Path.home() / "AppData/Roaming/MetaQuotes/Terminal/Common/Files/V12_PHASE1E_MQL5_CALENDAR_SNAPSHOT.csv")
    parser.add_argument("--calendar-overrides", type=Path, default=repo / "research/v12/v12_calendar_time_overrides.json")
    parser.add_argument("--phase1f", type=Path, default=repo / "output/v12_phase1f_parent_target_succession_20260924_a")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1g_continuous_intraday_path_20260924_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    cutoff = parse_cutoff(contract["mechanism_cutoff"])
    safe_output(args.output, args.replace)

    market, audit = load_market(args.m1, cutoff)
    calendar, calendar_diagnostics = load_calendar(args.calendar, cutoff, args.calendar_overrides)
    clusters = build_clusters(calendar)
    events = EventIndex(clusters)
    index = MarketIndex(market)
    boxes = generate_boxes(index, market["timestamp"].min().date() - timedelta(days=4), cutoff.date())
    medians = daily_prior_medians(market)

    child_source = pd.read_csv(args.phase1f / "V12_PHASE1F_V10_CHILD_TARGET_CONTEXT.csv", low_memory=False)
    nha_source = pd.read_csv(args.phase1f / "V12_PHASE1F_NHA_TARGET_CONTEXT.csv", low_memory=False)
    repair_source = pd.read_csv(args.phase1f / "V12_PHASE1F_REPAIR_TARGET_CONTEXT.csv", low_memory=False)
    children = pd.DataFrame(path_context(child_source, "decision_time", "signal_id", market, boxes, events, medians))
    nhas = pd.DataFrame(path_context(nha_source, "known_at", "flip_id", market, boxes, events, medians))
    bridges = pd.DataFrame(path_context(repair_source, "bridge_start_time", "repair_id", market, boxes, events, medians))
    confirmed_repairs_source = repair_source.loc[repair_source["repair_time"].notna()].copy()
    repairs = pd.DataFrame(path_context(confirmed_repairs_source, "repair_time", "repair_id", market, boxes, events, medians))

    entry_children = children.loc[children["event"] == "ENTRY"].copy()
    child_outcomes = {
        "STOP_HIT": ("stop_hit", "funded_units"),
        "GE5R_RIGHT_TAIL": ("right_tail_presence", "funded_units"),
    }
    entry_children["right_tail_presence"] = (pd.to_numeric(entry_children["right_tail_ge_5R_units"], errors="coerce") > 0).astype(int)
    child_metrics, child_predictions, child_quintiles = fit_models(
        entry_children, "child", "decision_time", "signal_id", child_outcomes
    )
    linked_nha = nhas.loc[pd.to_numeric(nhas["linked_v10_k1_stop_hit"], errors="coerce").notna()].copy()
    linked_nha["unit_weight"] = 1.0
    nha_metrics, nha_predictions, _ = fit_models(
        linked_nha, "nha", "known_at", "flip_id", {"LINKED_K1_STOP": ("linked_v10_k1_stop_hit", "unit_weight")}
    )
    child_diag_metrics, _, _ = fit_models(
        entry_children, "child", "decision_time", "signal_id", child_outcomes,
        feature_specs=diagnostic_feature_groups(entry_children, "child"), emit_predictions=False,
    )
    nha_diag_metrics, _, _ = fit_models(
        linked_nha, "nha", "known_at", "flip_id", {"LINKED_K1_STOP": ("linked_v10_k1_stop_hit", "unit_weight")},
        feature_specs=diagnostic_feature_groups(linked_nha, "nha"), emit_predictions=False,
    )
    run_length_metrics = fit_run_length_models(nhas)

    outputs = {
        "SOURCE_BOXES.csv": source_box_rows(boxes, medians),
        "V10_CHILD_PATH_CONTEXT.csv": children.to_dict("records"),
        "NHA_PATH_CONTEXT.csv": nhas.to_dict("records"),
        "BRIDGE_PATH_CONTEXT.csv": bridges.to_dict("records"),
        "REPAIR_PATH_CONTEXT.csv": repairs.to_dict("records"),
        "MODEL_METRICS.csv": child_metrics + nha_metrics,
        "PREDICTIONS.csv": child_predictions + nha_predictions,
        "QUINTILE_CAPITAL.csv": child_quintiles,
        "JOINT_SCORE_CAPITAL.csv": joint_score_capital(child_predictions),
        "CONVICTION_SCORE_CAPITAL.csv": conviction_score_capital(child_predictions),
        "MECHANISM_ABLATION_METRICS.csv": child_diag_metrics + nha_diag_metrics,
        "RUN_LENGTH_MODEL_METRICS.csv": run_length_metrics,
    }
    paths = []
    for name, rows in outputs.items():
        path = args.output / f"{PREFIX}{name}"
        write_csv(path, rows)
        paths.append(path)
    diagnostics = {
        "contract_version": contract["contract_version"],
        "contract_sha256": sha256_file(args.contract),
        "cutoff": cutoff.isoformat(),
        "raw_m1_sha256": sha256_file(args.m1),
        "m1_prefix_rows": audit.parsed_price_rows,
        "m1_prefix_sha256": audit.prefix_sha256,
        "first_unrevealed_timestamp": audit.first_unrevealed_timestamp.isoformat() if audit.first_unrevealed_timestamp else None,
        "post_cutoff_price_rows_parsed": audit.post_cutoff_price_rows_parsed,
        "calendar": calendar_diagnostics,
        "usd_modhigh_event_clusters": len(events.frame),
        "source_boxes": len(boxes),
        "v10_context_rows": len(children),
        "v10_entry_model_rows": len(entry_children),
        "nha_context_rows": len(nhas),
        "nha_linked_k1_model_rows": len(linked_nha),
        "bridge_context_rows": len(bridges),
        "repair_context_rows": len(repairs),
        "model_metric_rows": len(child_metrics) + len(nha_metrics),
        "mechanism_ablation_metric_rows": len(child_diag_metrics) + len(nha_diag_metrics),
        "run_length_metric_rows": len(run_length_metrics),
        "trade_authority": False,
        "sizing_authority": False,
    }
    diagnostics_path = args.output / f"{PREFIX}DIAGNOSTICS.json"
    write_json(diagnostics_path, diagnostics)
    paths.append(diagnostics_path)
    manifest = {
        "contract_version": contract["contract_version"],
        "files": [{"name": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in paths],
    }
    write_json(args.output / f"{PREFIX}MANIFEST.json", manifest)
    print(json.dumps(diagnostics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
