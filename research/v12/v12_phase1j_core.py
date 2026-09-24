"""Pure causal-timeline helpers for V12 Phase 1J."""

from __future__ import annotations

import numpy as np
import pandas as pd


CONTRACT_VERSION = "v12-phase1j-within-run-causal-timeline-v1"
CHECKPOINTS = (1, 2, 4, 8)
EVENTS = (
    "FIRST_FAVORABLE_CLOSE",
    "FIRST_OPPOSED_CLOSE",
    "FIRST_REPAIR_CLOSE_AFTER_OPPOSED",
    "FIRST_TWO_CONSECUTIVE_FAVORABLE_CLOSES",
    "FIRST_TWO_CONSECUTIVE_OPPOSED_CLOSES",
    "FIRST_REPAIRED_DEPARTURE_ABOVE_PRE_OPPOSED_FAVORABLE_CLOSE_MAX",
)


def weighted_tail_price(entry: float, stop: float, direction: int, weight: float) -> float:
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    risk = abs(float(entry) - float(stop))
    if risk <= 0 or float(weight) <= 0:
        raise ValueError("risk and weight must be positive")
    return float(entry) + direction * risk * 5.0 / float(weight)


def first_touch_time(m1: pd.DataFrame, entry_time: pd.Timestamp, exit_time: pd.Timestamp,
                     target: float, direction: int) -> pd.Timestamp | None:
    frame = m1.loc[(m1["timestamp"] >= entry_time) & (m1["timestamp"] <= exit_time)]
    touched = frame["high"] >= target if direction == 1 else frame["low"] <= target
    if not touched.any():
        return None
    return pd.Timestamp(frame.loc[touched, "timestamp"].iloc[0])


def period_label(value: pd.Timestamp) -> str:
    if value <= pd.Timestamp("2025-03-31 23:59:59"):
        return "TRAIN"
    if value <= pd.Timestamp("2025-09-30 23:59:59"):
        return "F1"
    if value <= pd.Timestamp("2026-03-31 23:59:59"):
        return "F2"
    return "F3"


def rank_auc(y: np.ndarray, score: np.ndarray) -> float:
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    valid = np.isfinite(score)
    y, score = y[valid], score[valid]
    positives = int(y.sum())
    negatives = int(len(y) - positives)
    if positives == 0 or negatives == 0:
        return np.nan
    ranks = pd.Series(score).rank(method="average").to_numpy(float)
    return float((ranks[y == 1].sum() - positives * (positives + 1) / 2) / (positives * negatives))


def standardized_difference(stop: np.ndarray, tail: np.ndarray) -> float:
    stop = np.asarray(stop, dtype=float)
    tail = np.asarray(tail, dtype=float)
    combined = np.concatenate((stop[np.isfinite(stop)], tail[np.isfinite(tail)]))
    if not len(combined):
        return np.nan
    scale = float(np.std(combined))
    if scale <= 0:
        return np.nan
    return float((np.nanmean(tail) - np.nanmean(stop)) / scale)


def build_run_timeline(m1: pd.DataFrame, children: pd.DataFrame, run: pd.Series,
                       terminal_time: pd.Timestamp) -> pd.DataFrame:
    ordered_children = children.sort_values(["entry_time", "signal_id"]).copy()
    first = ordered_children.iloc[0]
    start = pd.Timestamp(first["entry_time"])
    terminal = pd.Timestamp(terminal_time)
    direction = int(first["dir"])
    entry = float(first["entry"])
    risk = abs(entry - float(first["stop"]))
    if risk <= 0:
        raise ValueError(f"non-positive first-child risk for run {run['run_id']}")

    raw = m1.loc[(m1["timestamp"] >= start) & (m1["timestamp"] < terminal)].copy()
    if raw.empty:
        return pd.DataFrame()
    raw["bucket"] = raw["timestamp"].dt.floor("15min")
    bars = raw.groupby("bucket", sort=True).agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), tick_volume=("tick_volume", "sum"),
        observed_m1=("timestamp", "size"), first_m1=("timestamp", "min"), last_m1=("timestamp", "max"),
    ).reset_index()
    bars["bar_end"] = bars["bucket"] + pd.Timedelta(minutes=15)
    bars = bars.loc[bars["bar_end"] < terminal].reset_index(drop=True)
    if bars.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    previous_close = entry
    path = 0.0
    mfe = -np.inf
    mae = np.inf
    favorable_count = opposed_count = 0
    favorable_streak = opposed_streak = 0
    max_favorable_streak = max_opposed_streak = 0
    last_nonzero_sign = 0
    crossings = repairs = 0
    first_opposed_seen = False
    pre_opposed_favorable_max = 0.0
    favorable_close_max = 0.0
    occurred: set[str] = set()

    for index, bar in bars.iterrows():
        aligned_close = direction * (float(bar["close"]) - entry) / risk
        favorable_price = float(bar["high"]) if direction == 1 else float(bar["low"])
        opposed_price = float(bar["low"]) if direction == 1 else float(bar["high"])
        aligned_high = direction * (favorable_price - entry) / risk
        aligned_low = direction * (opposed_price - entry) / risk
        mfe = max(mfe, aligned_high)
        mae = min(mae, aligned_low)
        path += abs(float(bar["close"]) - previous_close) / risk
        previous_close = float(bar["close"])
        sign = 1 if aligned_close > 0 else (-1 if aligned_close < 0 else 0)
        if sign == 1:
            favorable_count += 1
            favorable_streak += 1
            opposed_streak = 0
        elif sign == -1:
            opposed_count += 1
            opposed_streak += 1
            favorable_streak = 0
        else:
            favorable_streak = opposed_streak = 0
        max_favorable_streak = max(max_favorable_streak, favorable_streak)
        max_opposed_streak = max(max_opposed_streak, opposed_streak)
        if sign and last_nonzero_sign and sign != last_nonzero_sign:
            crossings += 1
            if last_nonzero_sign == -1 and sign == 1:
                repairs += 1
        if sign:
            last_nonzero_sign = sign

        events: list[str] = []
        if sign == 1 and "FIRST_FAVORABLE_CLOSE" not in occurred:
            events.append("FIRST_FAVORABLE_CLOSE")
        if sign == -1 and "FIRST_OPPOSED_CLOSE" not in occurred:
            events.append("FIRST_OPPOSED_CLOSE")
            first_opposed_seen = True
            pre_opposed_favorable_max = favorable_close_max
        if first_opposed_seen and sign == 1 and "FIRST_REPAIR_CLOSE_AFTER_OPPOSED" not in occurred:
            events.append("FIRST_REPAIR_CLOSE_AFTER_OPPOSED")
        if favorable_streak >= 2 and "FIRST_TWO_CONSECUTIVE_FAVORABLE_CLOSES" not in occurred:
            events.append("FIRST_TWO_CONSECUTIVE_FAVORABLE_CLOSES")
        if opposed_streak >= 2 and "FIRST_TWO_CONSECUTIVE_OPPOSED_CLOSES" not in occurred:
            events.append("FIRST_TWO_CONSECUTIVE_OPPOSED_CLOSES")
        if (first_opposed_seen and sign == 1 and aligned_close > pre_opposed_favorable_max
                and "FIRST_REPAIRED_DEPARTURE_ABOVE_PRE_OPPOSED_FAVORABLE_CLOSE_MAX" not in occurred):
            events.append("FIRST_REPAIRED_DEPARTURE_ABOVE_PRE_OPPOSED_FAVORABLE_CLOSE_MAX")
        occurred.update(events)
        favorable_close_max = max(favorable_close_max, aligned_close)

        bar_end = pd.Timestamp(bar["bar_end"])
        child_mask = ordered_children["entry_time"] <= bar_end
        row = {
            "run_id": int(run["run_id"]), "run_start": run["run_start"],
            "run_class": run["run_class"], "after_stop_candidate": int(run["after_stop_candidate"]),
            "direction": run["direction"], "period": period_label(pd.Timestamp(run["run_start"])),
            "timeline_start": start, "terminal_time": terminal, "bar_open": bar["bucket"],
            "bar_end": bar_end, "observed_m1": int(bar["observed_m1"]),
            "elapsed_minutes": (bar_end - start).total_seconds() / 60.0,
            "completed_m15_bars": int(index + 1), "aligned_close_r": aligned_close,
            "cumulative_mfe_r": mfe, "cumulative_mae_r": mae,
            "cumulative_close_path_r": path,
            "signed_path_efficiency": aligned_close / path if path > 0 else 0.0,
            "favorable_close_fraction": favorable_count / (index + 1),
            "opposed_close_fraction": opposed_count / (index + 1),
            "zero_crossings": crossings, "repairs_to_favorable": repairs,
            "current_favorable_streak": favorable_streak, "current_opposed_streak": opposed_streak,
            "max_favorable_streak": max_favorable_streak, "max_opposed_streak": max_opposed_streak,
            "favorable_close_max_r": favorable_close_max,
            "opposed_close_min_r": min(0.0, aligned_close, *(r["aligned_close_r"] for r in rows)) if rows else min(0.0, aligned_close),
            "giveback_from_favorable_max_r": favorable_close_max - aligned_close,
            "children_entered_by_snapshot": int(child_mask.sum()),
            "funded_units_entered_by_snapshot": float(ordered_children.loc[child_mask, "r7g_weight"].sum()),
            "events": "|".join(events),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def event_snapshots(timeline: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, row in timeline.iterrows():
        for event in str(row.get("events", "")).split("|"):
            if event:
                item = row.to_dict()
                item["snapshot"] = event
                rows.append(item)
        if int(row["completed_m15_bars"]) in CHECKPOINTS:
            item = row.to_dict()
            item["snapshot"] = f"CHECKPOINT_M15_{int(row['completed_m15_bars'])}"
            rows.append(item)
    return pd.DataFrame(rows)
