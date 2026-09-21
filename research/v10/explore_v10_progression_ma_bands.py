"""Explore V10 progression gating and volatility-normalized MA ribbons.

Research-only, consumed-data diagnostics.  This script does not promote a
strategy rule.  It reconstructs H4/H1/M15 bars directly from chronological raw
M1, uses only completed bars at each decision, and reports every result by era.

Two distinct questions are kept separate:

1. Can a parameter-free progression-credit / damage-repair state reduce
   repeated selected-Child losses without deleting the right tail?
2. Do MA-ribbon penetration, ordering, width, slope, and LTF repair coordinates
   carry stable STOP information across years after causal volatility
   normalization?
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from build_v10_causal_m1_universe_r3 import Bar, BarAggregator, HAStream


SOURCE_TS = "%Y.%m.%d %H:%M:%S"
TIMEFRAMES = {"h4": 240, "h1": 60, "m15": 15}
RIBBON_LENGTHS = (20, 60)
MA_TYPES = ("sma", "wma")
PRICE_SOURCES = ("close", "oc2", "ha_mid")


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--r7g-events", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class CompletedBar:
    bar: Bar
    available_at: datetime


def wilder_atr(bars: pd.DataFrame, period: int = 180) -> np.ndarray:
    high = bars["high"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    close = bars["close"].to_numpy(float)
    tr = np.empty(len(bars), dtype=float)
    tr[0] = high[0] - low[0]
    if len(bars) > 1:
        tr[1:] = np.maximum.reduce(
            [high[1:] - low[1:], np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])]
        )
    atr = np.full(len(bars), np.nan, dtype=float)
    if len(bars) >= period:
        atr[period - 1] = float(np.mean(tr[:period]))
        for i in range(period, len(bars)):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def build_completed_bars(path: Path) -> dict[str, pd.DataFrame]:
    aggregators = {name: BarAggregator(minutes) for name, minutes in TIMEFRAMES.items()}
    completed: dict[str, list[CompletedBar]] = {name: [] for name in TIMEFRAMES}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            ts = datetime.strptime(f"{row['<DATE>']} {row['<TIME>']}", SOURCE_TS)
            o = float(row["<OPEN>"])
            h = float(row["<HIGH>"])
            l = float(row["<LOW>"])
            c = float(row["<CLOSE>"])
            for name, aggregator in aggregators.items():
                done = aggregator.push(ts, o, h, l, c)
                if done is not None:
                    completed[name].append(CompletedBar(done, ts))

    frames: dict[str, pd.DataFrame] = {}
    for name, records in completed.items():
        minutes = TIMEFRAMES[name]
        frame = pd.DataFrame(
            {
                "start": [x.bar.start for x in records],
                "end": [x.bar.start + timedelta(minutes=minutes) for x in records],
                "available_at": [x.available_at for x in records],
                "open": [x.bar.open for x in records],
                "high": [x.bar.high for x in records],
                "low": [x.bar.low for x in records],
                "close": [x.bar.close for x in records],
                "rows": [x.bar.rows for x in records],
            }
        )
        stream = HAStream(2.0, 0.25)
        ha_records = [stream.append(x.bar) for x in records]
        frame["ha_open"] = [x.ha_open for x in ha_records]
        frame["ha_close"] = [x.ha_close for x in ha_records]
        frame["ha_mid"] = 0.5 * (frame["ha_open"] + frame["ha_close"])
        frame["oc2"] = 0.5 * (frame["open"] + frame["close"])
        frame["atr180"] = wilder_atr(frame)
        frame["atr180_rel_price"] = frame["atr180"] / frame["close"].abs().clip(lower=1e-9)
        frames[name] = frame
    return frames


def moving_average(values: np.ndarray, period: int, kind: str) -> np.ndarray:
    n = len(values)
    result = np.full(n, np.nan, dtype=float)
    if period <= 0 or n < period:
        return result
    csum = np.concatenate(([0.0], np.cumsum(values, dtype=float)))
    ends = np.arange(period, n + 1)
    starts = ends - period
    segment_sum = csum[ends] - csum[starts]
    if kind == "sma":
        result[period - 1 :] = segment_sum / period
        return result
    if kind != "wma":
        raise ValueError(kind)
    idx_values = np.arange(n, dtype=float) * values
    cidx = np.concatenate(([0.0], np.cumsum(idx_values, dtype=float)))
    segment_idx = cidx[ends] - cidx[starts]
    weighted = segment_idx - (starts - 1.0) * segment_sum
    result[period - 1 :] = weighted / (period * (period + 1.0) / 2.0)
    return result


def ribbon_arrays(frame: pd.DataFrame, source: str, length: int, kind: str) -> dict[str, np.ndarray]:
    values = frame[source].to_numpy(float)
    atr = frame["atr180"].to_numpy(float)
    count_long = np.zeros(len(frame), dtype=float)
    count_short = np.zeros(len(frame), dtype=float)
    breach_long = np.zeros(len(frame), dtype=float)
    breach_short = np.zeros(len(frame), dtype=float)
    breach_long_live = np.ones(len(frame), dtype=bool)
    breach_short_live = np.ones(len(frame), dtype=bool)
    ordered_long = np.zeros(len(frame), dtype=float)
    ordered_short = np.zeros(len(frame), dtype=float)
    first_ma: np.ndarray | None = None
    last_ma: np.ndarray | None = None
    previous_ma: np.ndarray | None = None

    for period in range(1, length + 1):
        ma = moving_average(values, period, kind)
        valid = np.isfinite(ma)
        # MA(1) equals the current source exactly.  Keep it as the fast ribbon
        # edge, but exclude that degenerate equality from support/penetration.
        if period > 1:
            count_long += valid & (values > ma)
            count_short += valid & (values < ma)
            current_breach_long = valid & (values < ma)
            current_breach_short = valid & (values > ma)
            breach_long_live &= current_breach_long
            breach_short_live &= current_breach_short
            breach_long += breach_long_live
            breach_short += breach_short_live
        if previous_ma is not None:
            pair_valid = np.isfinite(previous_ma) & valid
            ordered_long += pair_valid & (previous_ma > ma)
            ordered_short += pair_valid & (previous_ma < ma)
        if first_ma is None:
            first_ma = ma.copy()
        previous_ma = ma
        last_ma = ma

    assert first_ma is not None and last_ma is not None
    center = 0.5 * (first_ma + last_ma)
    center_delta = np.concatenate(([np.nan], np.diff(center)))
    scale = np.maximum(atr, 1e-9)
    valid_full = np.isfinite(last_ma) & np.isfinite(atr)
    out = {
        "support_long": count_long / max(1, length - 1),
        "support_short": count_short / max(1, length - 1),
        "breach_long": breach_long / max(1, length - 1),
        "breach_short": breach_short / max(1, length - 1),
        "order_long": ordered_long / max(1, length - 1),
        "order_short": ordered_short / max(1, length - 1),
        "width_long_atr": (first_ma - last_ma) / scale,
        "slope_long_atr": center_delta / scale,
        "edge_long_atr": (values - last_ma) / scale,
        "valid": valid_full,
    }
    return out


def event_indices(frame: pd.DataFrame, decisions: pd.Series) -> np.ndarray:
    ends = frame["end"].to_numpy(dtype="datetime64[ns]")
    decision_values = decisions.to_numpy(dtype="datetime64[ns]")
    return np.searchsorted(ends, decision_values, side="right") - 1


def attach_ribbon_features(
    events: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = events[["signal_id", "decision", "year", "dir", "stop_hit", "R", "L", "rid", "k"]].copy()
    feature_columns: dict[str, np.ndarray] = {}
    metadata: list[dict[str, object]] = []
    for timeframe, frame in frames.items():
        indices = event_indices(frame, events["decision"])
        ends = frame["end"].to_numpy(dtype="datetime64[ns]")
        for length in RIBBON_LENGTHS:
            for kind in MA_TYPES:
                for source in PRICE_SOURCES:
                    arrays = ribbon_arrays(frame, source, length, kind)
                    prefix = f"{timeframe}_{kind}_{source}_n{length}"
                    support = np.full(len(events), np.nan)
                    breach = np.full(len(events), np.nan)
                    order = np.full(len(events), np.nan)
                    width = np.full(len(events), np.nan)
                    slope = np.full(len(events), np.nan)
                    edge = np.full(len(events), np.nan)
                    repair = np.full(len(events), np.nan)
                    deterioration = np.full(len(events), np.nan)
                    support_change = np.full(len(events), np.nan)
                    direction = events["dir"].to_numpy(int)
                    for row_index, bar_index in enumerate(indices):
                        if bar_index < 0 or not arrays["valid"][bar_index]:
                            continue
                        is_long = direction[row_index] > 0
                        support_series = arrays["support_long"] if is_long else arrays["support_short"]
                        support[row_index] = support_series[bar_index]
                        breach[row_index] = (
                            arrays["breach_long"][bar_index]
                            if is_long
                            else arrays["breach_short"][bar_index]
                        )
                        order[row_index] = (
                            arrays["order_long"][bar_index]
                            if is_long
                            else arrays["order_short"][bar_index]
                        )
                        sign = 1.0 if is_long else -1.0
                        width[row_index] = sign * arrays["width_long_atr"][bar_index]
                        slope[row_index] = sign * arrays["slope_long_atr"][bar_index]
                        edge[row_index] = sign * arrays["edge_long_atr"][bar_index]
                        if timeframe != "h4":
                            start_time = events.iloc[row_index]["decision"] - pd.Timedelta(hours=4)
                            lo = np.searchsorted(
                                ends,
                                np.datetime64(start_time.to_datetime64()),
                                side="right",
                            )
                            segment = support_series[lo : bar_index + 1]
                            segment = segment[np.isfinite(segment)]
                            if len(segment):
                                repair[row_index] = support[row_index] - float(np.min(segment))
                                deterioration[row_index] = float(np.max(segment)) - support[row_index]
                                support_change[row_index] = support[row_index] - float(segment[0])
                    health = 0.5 * (support + order)
                    columns = {
                        f"{prefix}_support": support,
                        f"{prefix}_breach": breach,
                        f"{prefix}_order": order,
                        f"{prefix}_health": health,
                        f"{prefix}_width_atr": width,
                        f"{prefix}_slope_atr": slope,
                        f"{prefix}_edge_atr": edge,
                    }
                    if timeframe != "h4":
                        columns.update(
                            {
                                f"{prefix}_repair4h": repair,
                                f"{prefix}_deterioration4h": deterioration,
                                f"{prefix}_support_change4h": support_change,
                            }
                        )
                    for column, values in columns.items():
                        feature_columns[column] = values
                        role = column.rsplit("_", 1)[-1]
                        if column.endswith("_width_atr"):
                            role = "width_atr"
                        elif column.endswith("_slope_atr"):
                            role = "slope_atr"
                        elif column.endswith("_edge_atr"):
                            role = "edge_atr"
                        elif column.endswith("_support_change4h"):
                            role = "support_change4h"
                        elif column.endswith("_deterioration4h"):
                            role = "deterioration4h"
                        elif column.endswith("_repair4h"):
                            role = "repair4h"
                        metadata.append(
                            {
                                "feature": column,
                                "timeframe": timeframe,
                                "ma_type": kind,
                                "price_source": source,
                                "ribbon_length": length,
                                "role": role,
                                "higher_is_healthier": role not in {"breach", "deterioration4h"},
                            }
                        )
    features = pd.concat(
        [base.reset_index(drop=True), pd.DataFrame(feature_columns)], axis=1
    )
    return features, pd.DataFrame(metadata).drop_duplicates("feature")


def safe_auc(target: pd.Series, score: pd.Series) -> float:
    valid = target.notna() & score.notna() & np.isfinite(score)
    if valid.sum() < 20 or target[valid].nunique() < 2:
        return np.nan
    return float(roc_auc_score(target[valid].astype(int), score[valid].astype(float)))


def summarize_feature_stability(
    features: pd.DataFrame,
    metadata: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for meta in metadata.to_dict("records"):
        name = str(meta["feature"])
        sign = -1.0 if bool(meta["higher_is_healthier"]) else 1.0
        result = dict(meta)
        aucs: list[float] = []
        for year in sorted(features["year"].unique()):
            subset = features[features["year"] == year]
            auc = safe_auc(subset["stop_hit"], sign * subset[name])
            result[f"stop_auc_{year}"] = auc
            if year >= 2024 and math.isfinite(auc):
                aucs.append(auc)
        result["stop_auc_pooled"] = safe_auc(features["stop_hit"], sign * features[name])
        result["stop_auc_min_2024_2026"] = min(aucs) if aucs else np.nan
        result["stop_auc_mean_2024_2026"] = float(np.mean(aucs)) if aucs else np.nan
        valid = features[[name, "R"]].dropna()
        result["spearman_R_pooled"] = (
            float(valid[name].corr(valid["R"], method="spearman"))
            if len(valid) >= 20
            else np.nan
        )
        rows.append(result)
    return pd.DataFrame(rows).sort_values(
        ["stop_auc_min_2024_2026", "stop_auc_mean_2024_2026", "stop_auc_pooled"],
        ascending=False,
    )


def load_selected_events(path: Path, universe: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    events = pd.read_csv(path)
    events["decision"] = pd.to_datetime(events["decision"], format="%Y.%m.%d %H:%M")
    active = events[
        (events["decision"] >= pd.Timestamp("2024-10-01"))
        & (events["r7g_weight"] > 0)
    ].copy()
    active["selected_dir"] = active["dir"].map({"LONG": 1, "SHORT": -1}).astype(int)
    event_columns = [
        "decision",
        "event",
        "score",
        "q50",
        "q75",
        "r4_weight",
        "p_stop",
        "mu_nonstop",
        "EV",
        "feedback_R",
        "r7g_weight",
        "selected_dir",
    ]
    matched = active[event_columns].merge(
        universe,
        on="decision",
        how="inner",
        validate="many_to_one",
    )
    matched = matched[matched["selected_dir"] == matched["dir"]].copy()
    audit = {
        "event_rows": int(len(events)),
        "post_cutoff_positive_weight_rows": int(len(active)),
        "matched_resolved_rows": int(len(matched)),
        "unmatched_or_direction_mismatch": int(len(active) - len(matched)),
    }
    return matched, audit


def h4_context_for_selected(selected: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    out = selected.copy()
    idx = event_indices(h4, out["decision"])
    valid = idx >= 0
    out["launch_h4_index"] = idx
    out["launch_high"] = np.where(valid, h4["high"].to_numpy()[np.maximum(idx, 0)], np.nan)
    out["launch_low"] = np.where(valid, h4["low"].to_numpy()[np.maximum(idx, 0)], np.nan)
    out["launch_close"] = np.where(valid, h4["close"].to_numpy()[np.maximum(idx, 0)], np.nan)
    out["h4_atr180"] = np.where(valid, h4["atr180"].to_numpy()[np.maximum(idx, 0)], np.nan)
    return out


def has_favorable_settlement(
    h4: pd.DataFrame,
    after: pd.Timestamp,
    cutoff: pd.Timestamp,
    direction: int,
    extreme: float,
) -> bool:
    segment = h4[(h4["end"] > after) & (h4["end"] <= cutoff)]
    if segment.empty:
        return False
    if direction > 0:
        return bool((segment["close"] > extreme).any())
    return bool((segment["close"] < extreme).any())


def progression_actions(selected: pd.DataFrame, h4: pd.DataFrame, mode: str) -> pd.DataFrame:
    data = selected.sort_values(["decision", "signal_id"]).copy()
    allowed: list[bool] = []
    reasons: list[str] = []
    run_anchor: dict[int, dict[str, object]] = {}
    damage: dict[int, dict[str, object] | None] = {1: None, -1: None}
    scheduled_stops: list[dict[str, object]] = []

    def update_damage(now: pd.Timestamp) -> None:
        nonlocal scheduled_stops
        remaining: list[dict[str, object]] = []
        for item in scheduled_stops:
            if item["exit_time"] >= now:
                remaining.append(item)
                continue
            proved_before_stop = has_favorable_settlement(
                h4,
                item["decision"],
                item["exit_time"],
                int(item["dir"]),
                float(item["extreme"]),
            )
            if not proved_before_stop:
                damage[int(item["dir"])] = {
                    "decision": item["decision"],
                    "extreme": item["extreme"],
                }
        scheduled_stops = remaining

    for row in data.itertuples(index=False):
        decision = pd.Timestamp(row.decision)
        direction = int(row.dir)
        extreme = float(row.launch_high if direction > 0 else row.launch_low)
        if mode in {"DAMAGE_REPAIR", "COMBINED"}:
            update_damage(decision)
            current_damage = damage[direction]
            if current_damage is not None and has_favorable_settlement(
                h4,
                pd.Timestamp(current_damage["decision"]),
                decision,
                direction,
                float(current_damage["extreme"]),
            ):
                damage[direction] = None

        allow = True
        reason = "ALLOW"
        if mode in {"DAMAGE_REPAIR", "COMBINED"} and damage[direction] is not None:
            allow = False
            reason = "BLOCK_DAMAGED_UNREPAIRED"

        if allow and mode in {"PROGRESSION", "COMBINED"}:
            anchor = run_anchor.get(int(row.rid))
            if anchor is not None:
                proved = has_favorable_settlement(
                    h4,
                    pd.Timestamp(anchor["decision"]),
                    decision,
                    direction,
                    float(anchor["extreme"]),
                )
                if not proved:
                    allow = False
                    reason = "BLOCK_UNPROVEN_CHILD"

        allowed.append(allow)
        reasons.append(reason)
        if allow:
            run_anchor[int(row.rid)] = {"decision": decision, "extreme": extreme}
            if bool(row.stop_hit):
                scheduled_stops.append(
                    {
                        "exit_time": pd.Timestamp(row.exit_time),
                        "decision": decision,
                        "dir": direction,
                        "extreme": extreme,
                    }
                )

    data[f"allow_{mode.lower()}"] = allowed
    data[f"reason_{mode.lower()}"] = reasons
    return data[["signal_id", f"allow_{mode.lower()}", f"reason_{mode.lower()}"]]


def max_true_streak(values: Iterable[bool]) -> int:
    best = current = 0
    for value in values:
        if bool(value):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def policy_metrics(data: pd.DataFrame, policy: str, period: object, weight_column: str) -> dict[str, object]:
    allow = data[f"allow_{policy.lower()}"] if policy != "BASELINE" else pd.Series(True, index=data.index)
    weight = data[weight_column].astype(float)
    executed = data[allow].sort_values("decision")
    baseline_r = float((data["R"] * weight).sum())
    policy_r = float((data.loc[allow, "R"] * weight[allow]).sum())
    positive = (data["R"] > 0) & (weight > 0)
    long_tail = positive & (data["L"] >= 6)
    retained_positive = float((data.loc[allow & positive, "R"] * weight[allow & positive]).sum())
    baseline_positive = float((data.loc[positive, "R"] * weight[positive]).sum())
    retained_tail = float((data.loc[allow & long_tail, "R"] * weight[allow & long_tail]).sum())
    baseline_tail = float((data.loc[long_tail, "R"] * weight[long_tail]).sum())
    return {
        "period": period,
        "weighting": weight_column,
        "policy": policy,
        "candidates": int(len(data)),
        "executed": int(allow.sum()),
        "blocked": int((~allow).sum()),
        "blocked_stops": int((~allow & data["stop_hit"].astype(bool)).sum()),
        "blocked_positive_children": int((~allow & (data["R"] > 0)).sum()),
        "baseline_stops": int(data["stop_hit"].sum()),
        "policy_stops": int(executed["stop_hit"].sum()),
        "baseline_max_stop_streak": max_true_streak(data.sort_values("decision")["stop_hit"]),
        "policy_max_stop_streak": max_true_streak(executed["stop_hit"]),
        "baseline_R": baseline_r,
        "policy_R": policy_r,
        "delta_R": policy_r - baseline_r,
        "positive_R_retention": retained_positive / baseline_positive if baseline_positive else np.nan,
        "L6plus_positive_R_retention": retained_tail / baseline_tail if baseline_tail else np.nan,
    }


def evaluate_progression(selected: pd.DataFrame, h4: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ledger = h4_context_for_selected(selected, h4)
    for mode in ("PROGRESSION", "DAMAGE_REPAIR", "COMBINED"):
        actions = progression_actions(ledger, h4, mode)
        ledger = ledger.merge(actions, on="signal_id", how="left", validate="one_to_one")
    rows: list[dict[str, object]] = []
    for weight_column in ("r4_weight", "r7g_weight"):
        for policy in ("BASELINE", "PROGRESSION", "DAMAGE_REPAIR", "COMBINED"):
            rows.append(policy_metrics(ledger, policy, "POOLED", weight_column))
            for year, subset in ledger.groupby("year"):
                rows.append(policy_metrics(subset, policy, int(year), weight_column))
    summary = pd.DataFrame(rows)

    slices: list[dict[str, object]] = []
    for policy in ("PROGRESSION", "DAMAGE_REPAIR", "COMBINED"):
        allow = ledger[f"allow_{policy.lower()}"]
        for keys, subset in ledger.assign(allowed=allow).groupby(["year", "direction_event", "stage"], dropna=False):
            year, direction, stage = keys
            slices.append(
                {
                    "policy": policy,
                    "year": int(year),
                    "direction": direction,
                    "stage": stage,
                    "candidates": int(len(subset)),
                    "blocked": int((~subset["allowed"]).sum()),
                    "blocked_stops": int((~subset["allowed"] & subset["stop_hit"].astype(bool)).sum()),
                    "blocked_positive_children": int((~subset["allowed"] & (subset["R"] > 0)).sum()),
                    "delta_R7G": float(-(subset.loc[~subset["allowed"], "R"] * subset.loc[~subset["allowed"], "r7g_weight"]).sum()),
                }
            )
    return ledger, summary, pd.DataFrame(slices)


def liquidity_eras(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for timeframe, frame in frames.items():
        valid = frame.dropna(subset=["atr180_rel_price"]).copy()
        valid["year"] = valid["end"].dt.year
        for year, subset in valid.groupby("year"):
            rows.append(
                {
                    "timeframe": timeframe,
                    "year": int(year),
                    "bars": int(len(subset)),
                    "median_atr180": float(subset["atr180"].median()),
                    "median_atr180_pct_price": float(100.0 * subset["atr180_rel_price"].median()),
                    "q10_atr180_pct_price": float(100.0 * subset["atr180_rel_price"].quantile(0.10)),
                    "q90_atr180_pct_price": float(100.0 * subset["atr180_rel_price"].quantile(0.90)),
                }
            )
    return pd.DataFrame(rows)


def penetration_tables(
    selected_features: pd.DataFrame,
    metadata: pd.DataFrame,
    stability: pd.DataFrame,
    top_per_timeframe: int = 6,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = stability[stability["role"].isin(["health", "breach", "repair4h", "deterioration4h"])].copy()
    chosen = (
        candidates.groupby("timeframe", group_keys=False)
        .head(top_per_timeframe)
        .reset_index(drop=True)
    )
    rows: list[dict[str, object]] = []
    policy_rows: list[dict[str, object]] = []
    bins = [-np.inf, 0.2, 0.4, 0.6, 0.8, np.inf]
    labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
    for item in chosen.to_dict("records"):
        feature = str(item["feature"])
        role = str(item["role"])
        values = selected_features[feature].copy()
        if bool(item["higher_is_healthier"]):
            risk_coordinate = 1.0 - values if role in {"health", "repair4h"} else -values
        else:
            risk_coordinate = values
        if role in {"health", "breach"}:
            buckets = pd.cut(risk_coordinate, bins=bins, labels=labels, include_lowest=True)
        else:
            buckets = pd.qcut(risk_coordinate, 5, labels=labels, duplicates="drop")
        work = selected_features.assign(bucket=buckets, risk_coordinate=risk_coordinate)
        for (year, bucket), subset in work.dropna(subset=["bucket"]).groupby(["year", "bucket"], observed=True):
            weight = subset["r7g_weight"].astype(float)
            rows.append(
                {
                    "feature": feature,
                    "timeframe": item["timeframe"],
                    "role": role,
                    "year": int(year),
                    "risk_bucket": str(bucket),
                    "children": int(len(subset)),
                    "stop_rate": float(subset["stop_hit"].mean()),
                    "mean_R": float(subset["R"].mean()),
                    "weighted_R": float((subset["R"] * weight).sum()),
                }
            )

        if role not in {"health", "breach"}:
            continue
        for threshold in (0.2, 0.4, 0.6, 0.8):
            block = risk_coordinate >= threshold
            baseline = float((selected_features["R"] * selected_features["r7g_weight"]).sum())
            policy = float((selected_features.loc[~block, "R"] * selected_features.loc[~block, "r7g_weight"]).sum())
            positives = (selected_features["R"] > 0) & (selected_features["L"] >= 6)
            base_tail = float((selected_features.loc[positives, "R"] * selected_features.loc[positives, "r7g_weight"]).sum())
            kept_tail = float((selected_features.loc[positives & ~block, "R"] * selected_features.loc[positives & ~block, "r7g_weight"]).sum())
            policy_rows.append(
                {
                    "feature": feature,
                    "timeframe": item["timeframe"],
                    "role": role,
                    "risk_threshold": threshold,
                    "blocked": int(block.sum()),
                    "blocked_stops": int((block & selected_features["stop_hit"].astype(bool)).sum()),
                    "blocked_positive_children": int((block & (selected_features["R"] > 0)).sum()),
                    "delta_R7G": policy - baseline,
                    "L6plus_positive_R_retention": kept_tail / base_tail if base_tail else np.nan,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(policy_rows)


def causal_quantile_frontier(
    all_features: pd.DataFrame,
    selected_features: pd.DataFrame,
    metadata: pd.DataFrame,
    stability: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Era-adaptive extreme-tail diagnostics using prior-only feature quantiles."""
    top = stability.head(90).merge(
        metadata[["feature", "higher_is_healthier"]],
        on="feature",
        how="left",
        suffixes=("", "_meta"),
    )
    if "higher_is_healthier_meta" in top:
        top["higher_is_healthier"] = top["higher_is_healthier"].fillna(
            top["higher_is_healthier_meta"]
        )
    pooled_rows: list[dict[str, object]] = []
    year_rows: list[dict[str, object]] = []
    for item in top.to_dict("records"):
        feature = str(item["feature"])
        healthier_high = bool(item["higher_is_healthier"])
        for tail in (0.025, 0.05, 0.10, 0.20):
            pieces: list[pd.DataFrame] = []
            for year in (2024, 2025, 2026):
                boundary = pd.Timestamp(f"{year}-01-01")
                reference = all_features.loc[
                    (all_features["decision"] < boundary) & all_features[feature].notna(),
                    feature,
                ]
                test = selected_features[selected_features["year"] == year].copy()
                if reference.empty or test.empty:
                    continue
                quantile = tail if healthier_high else 1.0 - tail
                threshold = float(reference.quantile(quantile))
                if healthier_high:
                    test["block"] = test[feature] <= threshold
                else:
                    test["block"] = test[feature] >= threshold
                test["threshold"] = threshold
                pieces.append(test)
                block = test["block"]
                baseline = float((test["R"] * test["r7g_weight"]).sum())
                policy = float((test.loc[~block, "R"] * test.loc[~block, "r7g_weight"]).sum())
                year_rows.append(
                    {
                        "feature": feature,
                        "timeframe": item["timeframe"],
                        "role": item["role"],
                        "tail": tail,
                        "year": year,
                        "threshold": threshold,
                        "children": int(len(test)),
                        "blocked": int(block.sum()),
                        "blocked_stops": int((block & test["stop_hit"].astype(bool)).sum()),
                        "blocked_positive_children": int((block & (test["R"] > 0)).sum()),
                        "delta_R7G": policy - baseline,
                    }
                )
            if not pieces:
                continue
            scored = pd.concat(pieces, ignore_index=True)
            block = scored["block"]
            baseline = float((scored["R"] * scored["r7g_weight"]).sum())
            policy = float((scored.loc[~block, "R"] * scored.loc[~block, "r7g_weight"]).sum())
            positive = (scored["R"] > 0) & (scored["L"] >= 6)
            base_tail = float((scored.loc[positive, "R"] * scored.loc[positive, "r7g_weight"]).sum())
            kept_tail = float((scored.loc[positive & ~block, "R"] * scored.loc[positive & ~block, "r7g_weight"]).sum())
            executed = scored[~block].sort_values("decision")
            pooled_rows.append(
                {
                    "feature": feature,
                    "timeframe": item["timeframe"],
                    "ma_type": item["ma_type"],
                    "price_source": item["price_source"],
                    "ribbon_length": int(item["ribbon_length"]),
                    "role": item["role"],
                    "tail": tail,
                    "blocked": int(block.sum()),
                    "blocked_stops": int((block & scored["stop_hit"].astype(bool)).sum()),
                    "blocked_positive_children": int((block & (scored["R"] > 0)).sum()),
                    "policy_stops": int(executed["stop_hit"].sum()),
                    "policy_max_stop_streak": max_true_streak(executed["stop_hit"]),
                    "delta_R7G": policy - baseline,
                    "L6plus_positive_R_retention": kept_tail / base_tail if base_tail else np.nan,
                    "stop_auc_min_2024_2026": item["stop_auc_min_2024_2026"],
                }
            )
    pooled = pd.DataFrame(pooled_rows).sort_values(
        ["delta_R7G", "L6plus_positive_R_retention"], ascending=False
    )
    return pooled, pd.DataFrame(year_rows)


def fixed_band_interactions(
    all_features: pd.DataFrame,
    selected_features: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Two fixed semantic H1/H4 weakness plus M15 deterioration intersections."""
    pairs = [
        (
            "h1_wma_oc2_n20_edge_atr",
            "m15_wma_oc2_n60_deterioration4h",
            "H1_WMA_OC2_EDGE__M15_WMA_OC2_DETERIORATION",
        ),
        (
            "h4_wma_oc2_n20_slope_atr",
            "m15_wma_oc2_n60_deterioration4h",
            "H4_WMA_OC2_SLOPE__M15_WMA_OC2_DETERIORATION",
        ),
    ]
    rows: list[dict[str, object]] = []
    year_rows: list[dict[str, object]] = []
    for health_feature, ltf_feature, name in pairs:
        for tail in (0.10, 0.20):
            pieces: list[pd.DataFrame] = []
            for year in (2024, 2025, 2026):
                boundary = pd.Timestamp(f"{year}-01-01")
                reference = all_features[all_features["decision"] < boundary]
                test = selected_features[selected_features["year"] == year].copy()
                if test.empty:
                    continue
                health_q = float(reference[health_feature].dropna().quantile(tail))
                deterioration_q = float(reference[ltf_feature].dropna().quantile(1.0 - tail))
                test["block"] = (
                    (test[health_feature] <= health_q)
                    & (test[ltf_feature] >= deterioration_q)
                )
                pieces.append(test)
                block = test["block"]
                baseline = float((test["R"] * test["r7g_weight"]).sum())
                policy = float(
                    (test.loc[~block, "R"] * test.loc[~block, "r7g_weight"]).sum()
                )
                year_rows.append(
                    {
                        "policy": name,
                        "tail": tail,
                        "year": year,
                        "health_threshold": health_q,
                        "deterioration_threshold": deterioration_q,
                        "children": int(len(test)),
                        "blocked": int(block.sum()),
                        "blocked_stops": int(
                            (block & test["stop_hit"].astype(bool)).sum()
                        ),
                        "blocked_positive_children": int(
                            (block & (test["R"] > 0)).sum()
                        ),
                        "delta_R7G": policy - baseline,
                    }
                )
            scored = pd.concat(pieces, ignore_index=True)
            block = scored["block"]
            baseline = float((scored["R"] * scored["r7g_weight"]).sum())
            policy = float((scored.loc[~block, "R"] * scored.loc[~block, "r7g_weight"]).sum())
            positive = (scored["R"] > 0) & (scored["L"] >= 6)
            base_tail = float((scored.loc[positive, "R"] * scored.loc[positive, "r7g_weight"]).sum())
            kept_tail = float((scored.loc[positive & ~block, "R"] * scored.loc[positive & ~block, "r7g_weight"]).sum())
            executed = scored[~block].sort_values("decision")
            rows.append(
                {
                    "policy": name,
                    "tail": tail,
                    "blocked": int(block.sum()),
                    "blocked_stops": int((block & scored["stop_hit"].astype(bool)).sum()),
                    "blocked_positive_children": int((block & (scored["R"] > 0)).sum()),
                    "policy_stops": int(executed["stop_hit"].sum()),
                    "policy_max_stop_streak": max_true_streak(executed["stop_hit"]),
                    "delta_R7G": policy - baseline,
                    "L6plus_positive_R_retention": kept_tail / base_tail if base_tail else np.nan,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(year_rows)


def breached_line_tables(selected_features: pd.DataFrame) -> pd.DataFrame:
    """Readable summaries of consecutive MA2..MAN lines breached against direction."""
    variants = [
        ("h4_wma_oc2_n20_breach", 20),
        ("h1_wma_oc2_n20_breach", 20),
        ("h1_sma_close_n20_breach", 20),
        ("m15_wma_oc2_n60_breach", 60),
        ("m15_sma_close_n60_breach", 60),
    ]
    rows: list[dict[str, object]] = []
    for feature, length in variants:
        breached = np.rint(selected_features[feature] * (length - 1))
        if length == 20:
            bins = [-0.5, 0.5, 3.5, 7.5, 12.5, 19.5]
            labels = ["0", "1-3", "4-7", "8-12", "13-19"]
        else:
            bins = [-0.5, 0.5, 9.5, 19.5, 39.5, 59.5]
            labels = ["0", "1-9", "10-19", "20-39", "40-59"]
        bucket = pd.cut(breached, bins=bins, labels=labels, include_lowest=True)
        work = selected_features.assign(breached_lines=breached, line_bucket=bucket)
        for period, subset_period in [("POOLED", work), *[(str(year), work[work["year"] == year]) for year in (2024, 2025, 2026)]]:
            for line_bucket, subset in subset_period.dropna(subset=["line_bucket"]).groupby(
                "line_bucket", observed=True
            ):
                weight = subset["r7g_weight"].astype(float)
                rows.append(
                    {
                        "feature": feature,
                        "timeframe": feature.split("_", 1)[0],
                        "ribbon_length": length,
                        "period": period,
                        "breached_lines": str(line_bucket),
                        "children": int(len(subset)),
                        "stops": int(subset["stop_hit"].sum()),
                        "stop_rate": float(subset["stop_hit"].mean()),
                        "mean_R": float(subset["R"].mean()),
                        "weighted_R": float((subset["R"] * weight).sum()),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    universe = pd.read_csv(
        args.universe,
        parse_dates=["decision", "entry_time", "exit_time", "label_available_at"],
    )
    frames = build_completed_bars(args.m1)
    feature_ledger, metadata = attach_ribbon_features(universe, frames)
    stability = summarize_feature_stability(feature_ledger, metadata)
    selected, selected_audit = load_selected_events(args.r7g_events, universe)
    selected["direction_event"] = selected["selected_dir"].map({1: "LONG", -1: "SHORT"})
    selected["stage"] = np.select(
        [selected["k"] == 1, selected["k"] == 2],
        ["k1", "k2"],
        default="k3p",
    )
    selected_features = selected.merge(
        feature_ledger.drop(columns=["year", "dir", "stop_hit", "R", "L", "rid", "k", "decision"]),
        on="signal_id",
        how="left",
        validate="one_to_one",
    )
    progression_ledger, progression_summary, progression_slices = evaluate_progression(selected, frames["h4"])
    penetration, band_policies = penetration_tables(selected_features, metadata, stability)
    causal_frontier, causal_frontier_year = causal_quantile_frontier(
        feature_ledger, selected_features, metadata, stability
    )
    band_interactions, band_interactions_year = fixed_band_interactions(
        feature_ledger, selected_features
    )
    breached_lines = breached_line_tables(selected_features)
    era_table = liquidity_eras(frames)

    outputs = {
        "V10_PROGRESSION_ACTION_LEDGER.csv": progression_ledger,
        "V10_PROGRESSION_POLICY_SUMMARY.csv": progression_summary,
        "V10_PROGRESSION_POLICY_SLICES.csv": progression_slices,
        "V10_MA_BAND_FEATURE_LEDGER.csv": feature_ledger,
        "V10_MA_BAND_FEATURE_METADATA.csv": metadata,
        "V10_MA_BAND_STOP_STABILITY.csv": stability,
        "V10_MA_BAND_SELECTED_PENETRATION.csv": penetration,
        "V10_MA_BAND_SELECTED_POLICY_FRONTIER.csv": band_policies,
        "V10_MA_BAND_CAUSAL_QUANTILE_FRONTIER.csv": causal_frontier,
        "V10_MA_BAND_CAUSAL_QUANTILE_BY_YEAR.csv": causal_frontier_year,
        "V10_MA_BAND_FIXED_INTERACTIONS.csv": band_interactions,
        "V10_MA_BAND_FIXED_INTERACTIONS_BY_YEAR.csv": band_interactions_year,
        "V10_MA_BAND_BREACHED_LINES.csv": breached_lines,
        "V10_MA_BAND_LIQUIDITY_ERAS.csv": era_table,
    }
    for name, frame in outputs.items():
        frame.to_csv(args.out_dir / name, index=False, date_format="%Y-%m-%d %H:%M:%S")

    manifest = {
        "status": "CONSUMED-DATA EXPLORATION / NO STRATEGY OR EA AUTHORITY",
        "base_git_head": "438f6b4d588330b4cd2f1cae7cba968f14df36e4",
        "m1": str(args.m1.resolve()),
        "m1_sha256": sha256_file(args.m1),
        "universe": str(args.universe.resolve()),
        "universe_sha256": sha256_file(args.universe),
        "r7g_events": str(args.r7g_events.resolve()),
        "r7g_events_sha256": sha256_file(args.r7g_events),
        "selected_audit": selected_audit,
        "normalization": {
            "price_distance_width_slope": "same-timeframe causal Wilder ATR180",
            "penetration_support_order": "fraction of ribbon lines, scale-free",
            "era_reporting": "separate calendar-year results",
        },
        "ribbons": {
            "timeframes": list(TIMEFRAMES),
            "lengths": list(RIBBON_LENGTHS),
            "ma_types": list(MA_TYPES),
            "price_sources": list(PRICE_SOURCES),
            "degenerate_ma1_handling": "MA1 retained as fast edge; support and penetration count MA2..MAN",
        },
        "progression_contract": {
            "proof_long": "completed raw H4 close above launch-PHA raw high",
            "proof_short": "completed raw H4 close below launch-PHA raw low",
            "progression": "one unproven selected Child per FAST run",
            "damage_repair": "same-direction stopped-unproven Child blocks until proof-level repair",
            "parent_direction_veto": False,
        },
        "selection_warning": "MA variants and frontiers are post-hoc exploration on consumed evidence.",
    }
    (args.out_dir / "V10_PROGRESSION_MA_BAND_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print(json.dumps(manifest, indent=2))
    print("\nPROGRESSION R7G POOLED")
    print(
        progression_summary[
            (progression_summary["period"] == "POOLED")
            & (progression_summary["weighting"] == "r7g_weight")
        ].to_string(index=False)
    )
    print("\nTOP MA STOP FEATURES")
    print(stability.head(20).to_string(index=False))
    print("\nLIQUIDITY ERAS H4")
    print(era_table[era_table["timeframe"] == "h4"].to_string(index=False))


if __name__ == "__main__":
    main()
