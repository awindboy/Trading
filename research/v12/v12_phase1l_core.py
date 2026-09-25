"""Pure bar, HA, and scorecard primitives for V12 Phase 1L."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

import numpy as np
import pandas as pd


CONTRACT_VERSION = "v12-phase1l-h1-main-timeframe-feasibility-v1"


def bucket_start(ts: datetime, minutes: int) -> datetime:
    if minutes == 15:
        return ts.replace(minute=(ts.minute // 15) * 15, second=0, microsecond=0)
    if minutes == 60:
        return ts.replace(minute=0, second=0, microsecond=0)
    if minutes == 240:
        return ts.replace(hour=(ts.hour // 4) * 4, minute=0, second=0, microsecond=0)
    raise ValueError(minutes)


@dataclass
class Bar:
    start: datetime
    open: float
    high: float
    low: float
    close: float
    rows: int = 1


class BarAggregator:
    def __init__(self, minutes: int):
        self.minutes = minutes
        self.current: Bar | None = None

    def push(self, ts: datetime, o: float, h: float, l: float, c: float) -> Bar | None:
        start = bucket_start(ts, self.minutes)
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


@dataclass
class HARecord:
    start: datetime
    raw_open: float
    raw_high: float
    raw_low: float
    raw_close: float
    ha_open: float
    ha_close: float
    ha_high: float
    ha_low: float
    ha_dir: int
    ha_body: float


class HAStream:
    def __init__(self, close_weight: float, alpha: float):
        self.close_weight = close_weight
        self.alpha = alpha
        self.records: list[HARecord] = []

    def append(self, bar: Bar) -> HARecord:
        close = (bar.open + bar.high + bar.low + self.close_weight * bar.close) / (3.0 + self.close_weight)
        if not self.records:
            open_ = 0.5 * (bar.open + bar.close)
        else:
            previous = self.records[-1]
            open_ = self.alpha * previous.ha_open + (1.0 - self.alpha) * previous.ha_close
        record = HARecord(
            bar.start, bar.open, bar.high, bar.low, bar.close, open_, close,
            max(bar.high, open_, close), min(bar.low, open_, close),
            1 if close >= open_ else -1, close - open_,
        )
        self.records.append(record)
        return record


def true_range(bar: Bar, previous: Bar | None) -> float:
    if previous is None:
        return bar.high - bar.low
    return max(bar.high - bar.low, abs(bar.high - previous.close), abs(bar.low - previous.close))


def rank_auc(target: np.ndarray, score: np.ndarray) -> float:
    target = np.asarray(target, dtype=int)
    score = np.asarray(score, dtype=float)
    valid = np.isfinite(score)
    target, score = target[valid], score[valid]
    positive = int(target.sum())
    negative = int(len(target) - positive)
    if positive == 0 or negative == 0:
        return math.nan
    ranks = pd.Series(score).rank(method="average").to_numpy(float)
    return float((ranks[target == 1].sum() - positive * (positive + 1) / 2) / (positive * negative))


def max_stop_streak(frame: pd.DataFrame) -> int:
    best = current = 0
    for stopped in frame.sort_values(["decision", "signal_id"])["stop_hit"].astype(int):
        current = current + 1 if stopped else 0
        best = max(best, current)
    return best


def max_concurrent(frame: pd.DataFrame) -> int:
    events: list[tuple[pd.Timestamp, int, int]] = []
    for row in frame.itertuples(index=False):
        events.append((pd.Timestamp(row.entry_time), 1, 1))
        events.append((pd.Timestamp(row.exit_time), 0, -1))
    active = best = 0
    for _, _, delta in sorted(events):
        active += delta
        best = max(best, active)
    return best


def scorecard(frame: pd.DataFrame) -> dict[str, float]:
    values = frame.sort_values(["decision", "signal_id"])
    count = len(values)
    stops = int(values["stop_hit"].sum())
    positive = values.loc[values["R"] > 0, "R"].sort_values(ascending=False)
    negative = -float(values.loc[values["R"] < 0, "R"].sum())
    tail = values.loc[values["R"] >= 5.0, "R"]
    top_n = max(1, int(math.ceil(len(positive) * 0.01))) if len(positive) else 0
    return {
        "children": count,
        "wins": int((values["R"] > 0).sum()),
        "win_rate": float((values["R"] > 0).mean()) if count else math.nan,
        "stopped_units": float(stops),
        "stopped_units_per_100": stops / count * 100.0 if count else math.nan,
        "net_R": float(values["R"].sum()),
        "net_R_per_unit": float(values["R"].mean()) if count else math.nan,
        "profit_factor_R": float(positive.sum() / negative) if negative > 0 else math.nan,
        "tail_ge_5_children": int(len(tail)),
        "tail_ge_5_R": float(tail.sum()),
        "tail_ge_5_R_per_100": float(tail.sum() / count * 100.0) if count else math.nan,
        "top_1pct_positive_R_share": float(positive.head(top_n).sum() / positive.sum()) if len(positive) and positive.sum() else math.nan,
        "max_stop_streak": max_stop_streak(values),
        "max_concurrent_units": max_concurrent(values),
        "same_m1_ambiguities": int(values["same_m1_exit_stop_ambiguous"].sum()),
    }


def equal_stop_budget(candidate: dict[str, float], baseline: dict[str, float]) -> tuple[float, float]:
    """Scale candidate units so total stopped units equal the baseline scope."""
    candidate_stops = float(candidate["stopped_units"])
    baseline_children = float(baseline["children"])
    if candidate_stops <= 0 or baseline_children <= 0:
        return math.nan, math.nan
    scale = float(baseline["stopped_units"]) / candidate_stops
    net_r_per_baseline_unit = float(candidate["net_R"]) * scale / baseline_children
    return scale, net_r_per_baseline_unit
