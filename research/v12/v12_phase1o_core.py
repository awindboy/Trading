"""Pure sequence helpers for V12 Phase-1O."""

from __future__ import annotations

import numpy as np
import pandas as pd


CONTRACT_VERSION = "v12-phase1o-lower-timeframe-after-stop-sequence-v1"


def add_causal_history(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.sort_values(["decision_time", "signal_id"]).reset_index(drop=True).copy()
    work["decision_time"] = pd.to_datetime(work["decision_time"])
    work["label_available_at"] = pd.to_datetime(work["label_available_at"])
    for lag in (1, 2, 3):
        previous_decision = work["decision_time"].shift(lag)
        previous_known = work["label_available_at"].shift(lag) <= work["decision_time"]
        work[f"hist_lag{lag}_known"] = previous_known.fillna(False).astype(int)
        for source, target in (
            ("stop_hit", "stop"), ("R", "R"), ("L", "run_length"),
            ("position_hours", "position_hours"), ("stop_dist_atr", "stop_dist_atr"),
        ):
            values = pd.to_numeric(work[source].shift(lag), errors="coerce")
            if source == "R":
                values = values.clip(-5, 5)
            work[f"hist_lag{lag}_{target}"] = values.where(previous_known)
        work[f"hist_lag{lag}_elapsed_hours"] = (
            (work["decision_time"] - previous_decision).dt.total_seconds() / 3600.0
        ).where(previous_known)

    stop_streak = []
    for index, row in work.iterrows():
        streak = 0
        prior = index - 1
        while prior >= 0:
            if work.at[prior, "label_available_at"] > row["decision_time"]:
                break
            if int(work.at[prior, "stop_hit"]) != 1:
                break
            streak += 1
            prior -= 1
        stop_streak.append(streak)
    work["hist_known_prior_stop_streak"] = stop_streak
    intervals = work[[f"hist_lag{lag}_elapsed_hours" for lag in (1, 2, 3)]]
    work["hist_flip_interval_mean_hours"] = intervals.mean(axis=1, skipna=True)
    work["hist_flip_interval_std_hours"] = intervals.std(axis=1, skipna=True, ddof=0)
    work["hist_flip_interval_min_hours"] = intervals.min(axis=1, skipna=True)
    work["after_stop_cohort"] = (
        (work["hist_lag1_known"] == 1) & (work["hist_lag1_stop"] == 1)
    ).astype(int)
    return work


def policy_metrics(frame: pd.DataFrame) -> dict[str, float]:
    count = len(frame)
    stops = int(frame["stop_hit"].sum())
    tail = frame.loc[frame["R"] >= 5, "R"]
    gross_profit = float(frame.loc[frame["R"] > 0, "R"].sum())
    gross_loss = -float(frame.loc[frame["R"] < 0, "R"].sum())
    return {
        "children": count,
        "stops": stops,
        "stops_per_100": 100 * stops / count if count else np.nan,
        "win_rate": float((frame["R"] > 0).mean()) if count else np.nan,
        "net_R": float(frame["R"].sum()),
        "net_R_per_child": float(frame["R"].mean()) if count else np.nan,
        "profit_factor_R": gross_profit / gross_loss if gross_loss else np.nan,
        "tail_ge5_children": int((frame["R"] >= 5).sum()),
        "tail_ge5_R": float(tail.sum()),
    }


def train_risk_threshold(probability: np.ndarray) -> float:
    values = np.asarray(probability, dtype=float)
    if len(values) < 5 or not np.isfinite(values).all():
        raise ValueError("training probabilities must be finite")
    return float(np.quantile(values, 0.8))
