#!/usr/bin/env python3
"""Build the frozen V12 Phase-1S V10 weekly-journey direction audit."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from build_v12_phase0 import PrefixAudit, iter_m1_prefix, parse_cutoff
from build_v12_phase1d import build_clusters, load_calendar
from v12_phase0_core import sha256_file


VERSION = "v12-phase1s-v10-weekly-journey-direction-v1"
PREFIX = "V12_PHASE1S_"

CLOCK_FEATURES = [
    "week_phase_sin", "week_phase_cos", "day_phase_sin", "day_phase_cos",
]

PRICE_FEATURES = CLOCK_FEATURES + [
    "prev_week_range_norm", "prev_week_net_aligned_norm", "prev_week_close_location_aligned",
    "current_week_range_norm", "current_week_net_aligned_norm", "current_week_efficiency_aligned",
    "current_week_close_location_aligned", "week_favorable_excursion_norm",
    "week_adverse_excursion_norm", "prev_week_favorable_broken", "prev_week_opposed_broken",
    "prev_week_favorable_extension_norm", "prev_week_opposed_extension_norm",
    "prev_week_favorable_accepted", "prev_week_opposed_accepted",
    "prev_week_favorable_rejected", "prev_week_opposed_rejected",
    "prev_week_break_order_aligned", "prev_week_both_broken", "completed_days_in_week",
    "completed_day_direction_balance", "last_day_net_aligned_norm", "last_two_day_net_aligned_norm",
    "current_day_range_norm", "current_day_net_aligned_norm", "current_day_efficiency_aligned",
    "prev_day_boundary_state_aligned", "monday_available", "monday_range_norm",
    "monday_net_aligned_norm", "monday_boundary_state_aligned", "completed_h4_in_week",
    "last_three_h4_net_aligned_norm", "h4_direction_balance", "h4_prev_week_accept_balance",
]

EVENT_FEATURES = [
    "week_usd_modhigh_count_log", "week_usd_high_count_log", "week_max_abs_surprise_z",
    "minutes_since_last_usd_modhigh_log", "last_event_response_aligned_norm",
    "last_event_excursion_balance_norm", "last_event_response_efficiency_aligned",
]

HISTORY_FEATURES = [
    "v10_k", "v10_r7g_weight", "known_prior_children", "last_known_stop",
    "last_known_R_clipped", "last_three_known_stop_rate", "last_three_known_mean_R_clipped",
]

FEATURE_FAMILIES = {
    "WEEK_CLOCK": CLOCK_FEATURES,
    "WEEK_PRICE": PRICE_FEATURES,
    "WEEK_PRICE_EVENT": PRICE_FEATURES + EVENT_FEATURES,
    "WEEK_PRICE_EVENT_HISTORY": PRICE_FEATURES + EVENT_FEATURES + HISTORY_FEATURES,
}


@dataclass
class PeriodState:
    start: datetime
    open: float | None = None
    high: float = -math.inf
    low: float = math.inf
    close: float | None = None
    path_length: float = 0.0
    rows: int = 0
    times: list[datetime] = field(default_factory=list)
    highs: list[float] = field(default_factory=list)
    lows: list[float] = field(default_factory=list)
    closes: list[float] = field(default_factory=list)

    def update(self, ts: datetime, open_: float, high: float, low: float, close: float) -> None:
        if self.open is None:
            self.open = open_
        if self.close is not None:
            self.path_length += abs(close - self.close)
        self.high = max(self.high, high)
        self.low = min(self.low, low)
        self.close = close
        self.rows += 1
        self.times.append(ts)
        self.highs.append(high)
        self.lows.append(low)
        self.closes.append(close)

    def summary(self) -> dict[str, object]:
        return {
            "start": self.start,
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "range": float(self.high - self.low),
            "net": float(self.close - self.open),
            "path_length": float(self.path_length),
            "rows": self.rows,
        }


def week_start(value: datetime) -> datetime:
    base = value.replace(hour=0, minute=0, second=0, microsecond=0)
    return base - timedelta(days=value.weekday())


def day_start(value: datetime) -> datetime:
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def h4_start(value: datetime) -> datetime:
    return value.replace(hour=(value.hour // 4) * 4, minute=0, second=0, microsecond=0)


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output is not empty: {path}")
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def verify(path: Path, expected: str, label: str) -> None:
    observed = sha256_file(path)
    if observed.lower() != expected.lower():
        raise ValueError(f"{label} hash mismatch: {observed} != {expected}")


def finite_median(values: Iterable[float], minimum: int) -> float:
    clean = [float(value) for value in values if np.isfinite(value) and value > 0]
    if len(clean) < minimum:
        return math.nan
    return float(np.median(clean))


def aligned_close_location(period: dict[str, object] | None, sign: float) -> float:
    if period is None or float(period["range"]) <= 0:
        return math.nan
    raw = 2.0 * (float(period["close"]) - float(period["low"])) / float(period["range"]) - 1.0
    return sign * raw


def aligned_boundary_state(current_close: float | None, reference: dict[str, object] | None, sign: float) -> float:
    if current_close is None or reference is None:
        return math.nan
    favorable_accepted = current_close > float(reference["high"]) if sign > 0 else current_close < float(reference["low"])
    opposed_accepted = current_close < float(reference["low"]) if sign > 0 else current_close > float(reference["high"])
    return float(int(favorable_accepted) - int(opposed_accepted))


def boundary_path(period: PeriodState | None, reference: dict[str, object] | None,
                  sign: float, scale: float) -> dict[str, float]:
    empty = {
        "prev_week_favorable_broken": math.nan, "prev_week_opposed_broken": math.nan,
        "prev_week_favorable_extension_norm": math.nan, "prev_week_opposed_extension_norm": math.nan,
        "prev_week_favorable_accepted": math.nan, "prev_week_opposed_accepted": math.nan,
        "prev_week_favorable_rejected": math.nan, "prev_week_opposed_rejected": math.nan,
        "prev_week_break_order_aligned": math.nan, "prev_week_both_broken": math.nan,
    }
    if period is None or reference is None or not np.isfinite(scale) or period.close is None:
        return empty
    high_level, low_level = float(reference["high"]), float(reference["low"])
    high_indices = [i for i, value in enumerate(period.highs) if value > high_level]
    low_indices = [i for i, value in enumerate(period.lows) if value < low_level]
    high_broken, low_broken = bool(high_indices), bool(low_indices)
    if high_broken and low_broken:
        if high_indices[0] == low_indices[0]:
            order = 0.0
        elif high_indices[0] < low_indices[0]:
            order = 1.0 if sign > 0 else -1.0
        else:
            order = -1.0 if sign > 0 else 1.0
    elif high_broken:
        order = 1.0 if sign > 0 else -1.0
    elif low_broken:
        order = -1.0 if sign > 0 else 1.0
    else:
        order = 0.0
    favorable_broken = high_broken if sign > 0 else low_broken
    opposed_broken = low_broken if sign > 0 else high_broken
    favorable_extension = max(0.0, period.high - high_level) if sign > 0 else max(0.0, low_level - period.low)
    opposed_extension = max(0.0, low_level - period.low) if sign > 0 else max(0.0, period.high - high_level)
    favorable_accepted = period.close > high_level if sign > 0 else period.close < low_level
    opposed_accepted = period.close < low_level if sign > 0 else period.close > high_level
    return {
        "prev_week_favorable_broken": float(favorable_broken),
        "prev_week_opposed_broken": float(opposed_broken),
        "prev_week_favorable_extension_norm": favorable_extension / scale,
        "prev_week_opposed_extension_norm": opposed_extension / scale,
        "prev_week_favorable_accepted": float(favorable_accepted),
        "prev_week_opposed_accepted": float(opposed_accepted),
        "prev_week_favorable_rejected": float(favorable_broken and not favorable_accepted),
        "prev_week_opposed_rejected": float(opposed_broken and not opposed_accepted),
        "prev_week_break_order_aligned": order,
        "prev_week_both_broken": float(high_broken and low_broken),
    }


def period_net(period: dict[str, object] | None, sign: float, scale: float) -> float:
    if period is None or not np.isfinite(scale):
        return math.nan
    return sign * float(period["net"]) / scale


class WeeklyStateBuilder:
    def __init__(self, clusters: pd.DataFrame):
        self.current_week: PeriodState | None = None
        self.current_day: PeriodState | None = None
        self.current_h4: PeriodState | None = None
        self.completed_weeks: list[dict[str, object]] = []
        self.completed_days: list[dict[str, object]] = []
        self.completed_h4: list[dict[str, object]] = []
        events = clusters.loc[clusters["usd_modhigh"]].sort_values("event_time").reset_index(drop=True)
        self.events = events.to_dict("records")
        self.event_cursor = 0
        self.released_events: list[dict[str, object]] = []
        self.last_close: float | None = None
        self.last_m1_time: datetime | None = None

    def roll(self, ts: datetime) -> None:
        target_h4 = h4_start(ts)
        if self.current_h4 is not None and self.current_h4.start != target_h4:
            self.completed_h4.append(self.current_h4.summary())
            self.current_h4 = None
        target_day = day_start(ts)
        if self.current_day is not None and self.current_day.start != target_day:
            self.completed_days.append(self.current_day.summary())
            self.current_day = None
        target_week = week_start(ts)
        if self.current_week is not None and self.current_week.start != target_week:
            self.completed_weeks.append(self.current_week.summary())
            self.current_week = None

    def release_events_before(self, ts: datetime, inclusive: bool) -> None:
        while self.event_cursor < len(self.events):
            row = self.events[self.event_cursor]
            event_time = pd.Timestamp(row["event_time"]).to_pydatetime()
            ready = event_time <= ts if inclusive else event_time < ts
            if not ready:
                break
            current_week_start = week_start(event_time)
            if self.current_week is not None and self.current_week.start == current_week_start:
                row_index = self.current_week.rows
            else:
                row_index = 0
            self.released_events.append({
                "event_time": event_time,
                "week_start": current_week_start,
                "baseline_price": self.last_close,
                "row_index": row_index,
                "usd_high": int(bool(row["usd_high"])),
                "max_abs_surprise_z": float(row["max_abs_surprise_z"]) if pd.notna(row["max_abs_surprise_z"]) else math.nan,
            })
            self.event_cursor += 1

    def update(self, ts: datetime, open_: float, high: float, low: float, close: float) -> None:
        target_week, target_day, target_h4 = week_start(ts), day_start(ts), h4_start(ts)
        if self.current_week is None:
            self.current_week = PeriodState(target_week)
        if self.current_day is None:
            self.current_day = PeriodState(target_day)
        if self.current_h4 is None:
            self.current_h4 = PeriodState(target_h4)
        self.current_week.update(ts, open_, high, low, close)
        self.current_day.update(ts, open_, high, low, close)
        self.current_h4.update(ts, open_, high, low, close)
        self.last_close = close
        self.last_m1_time = ts

    def event_features(self, query: datetime, sign: float, weekly_scale: float) -> dict[str, float]:
        start = week_start(query)
        events = [row for row in self.released_events if row["week_start"] == start and row["event_time"] < query]
        surprises = [row["max_abs_surprise_z"] for row in events if np.isfinite(row["max_abs_surprise_z"])]
        result = {
            "week_usd_modhigh_count_log": math.log1p(len(events)),
            "week_usd_high_count_log": math.log1p(sum(row["usd_high"] for row in events)),
            "week_max_abs_surprise_z": max(surprises) if surprises else math.nan,
            "minutes_since_last_usd_modhigh_log": math.nan,
            "last_event_response_aligned_norm": math.nan,
            "last_event_excursion_balance_norm": math.nan,
            "last_event_response_efficiency_aligned": math.nan,
        }
        if not events or self.current_week is None or self.current_week.start != start:
            return result
        latest = events[-1]
        result["minutes_since_last_usd_modhigh_log"] = math.log1p(max(0.0, (query - latest["event_time"]).total_seconds() / 60.0))
        baseline = latest["baseline_price"]
        if baseline is None or not np.isfinite(weekly_scale) or self.current_week.close is None:
            return result
        index = min(int(latest["row_index"]), self.current_week.rows)
        highs = self.current_week.highs[index:]
        lows = self.current_week.lows[index:]
        closes = self.current_week.closes[index:]
        if not closes:
            return result
        favorable = max(0.0, max(highs) - baseline) if sign > 0 else max(0.0, baseline - min(lows))
        adverse = max(0.0, baseline - min(lows)) if sign > 0 else max(0.0, max(highs) - baseline)
        net = sign * (closes[-1] - baseline)
        sequence = [baseline] + closes
        path = sum(abs(right - left) for left, right in zip(sequence, sequence[1:]))
        result["last_event_response_aligned_norm"] = net / weekly_scale
        result["last_event_excursion_balance_norm"] = (favorable - adverse) / weekly_scale
        result["last_event_response_efficiency_aligned"] = net / path if path > 0 else 0.0
        return result

    def snapshot(self, query: datetime, direction: int) -> dict[str, object]:
        sign = 1.0 if direction > 0 else -1.0
        start = week_start(query)
        week_scale = finite_median((row["range"] for row in self.completed_weeks[-20:]), 8)
        day_scale = finite_median((row["range"] for row in self.completed_days[-60:]), 20)
        previous_week = self.completed_weeks[-1] if self.completed_weeks else None
        previous_day = self.completed_days[-1] if self.completed_days else None
        current_week = self.current_week if self.current_week is not None and self.current_week.start == start else None
        current_day = self.current_day if self.current_day is not None and self.current_day.start == day_start(query) else None
        week_summary = current_week.summary() if current_week is not None and current_week.rows else None
        day_summary = current_day.summary() if current_day is not None and current_day.rows else None
        elapsed_week = (query - start).total_seconds() / 60.0
        elapsed_day = (query - day_start(query)).total_seconds() / 60.0
        output: dict[str, object] = {
            "snapshot_last_m1_time": self.last_m1_time.isoformat() if self.last_m1_time else "",
            "weekly_scale": week_scale,
            "daily_scale": day_scale,
            "week_phase_sin": math.sin(2.0 * math.pi * elapsed_week / (7.0 * 1440.0)),
            "week_phase_cos": math.cos(2.0 * math.pi * elapsed_week / (7.0 * 1440.0)),
            "day_phase_sin": math.sin(2.0 * math.pi * elapsed_day / 1440.0),
            "day_phase_cos": math.cos(2.0 * math.pi * elapsed_day / 1440.0),
        }
        if previous_week is not None and np.isfinite(week_scale):
            output.update({
                "prev_week_range_norm": float(previous_week["range"]) / week_scale,
                "prev_week_net_aligned_norm": sign * float(previous_week["net"]) / week_scale,
                "prev_week_close_location_aligned": aligned_close_location(previous_week, sign),
            })
        else:
            output.update({key: math.nan for key in (
                "prev_week_range_norm", "prev_week_net_aligned_norm", "prev_week_close_location_aligned")})
        if week_summary is not None and np.isfinite(week_scale):
            week_range = float(week_summary["range"])
            path = float(week_summary["path_length"])
            favorable = max(0.0, float(week_summary["high"]) - float(week_summary["open"])) if sign > 0 else max(0.0, float(week_summary["open"]) - float(week_summary["low"]))
            adverse = max(0.0, float(week_summary["open"]) - float(week_summary["low"])) if sign > 0 else max(0.0, float(week_summary["high"]) - float(week_summary["open"]))
            output.update({
                "current_week_range_norm": week_range / week_scale,
                "current_week_net_aligned_norm": sign * float(week_summary["net"]) / week_scale,
                "current_week_efficiency_aligned": sign * float(week_summary["net"]) / path if path > 0 else 0.0,
                "current_week_close_location_aligned": aligned_close_location(week_summary, sign),
                "week_favorable_excursion_norm": favorable / week_scale,
                "week_adverse_excursion_norm": adverse / week_scale,
            })
        else:
            output.update({key: math.nan for key in (
                "current_week_range_norm", "current_week_net_aligned_norm", "current_week_efficiency_aligned",
                "current_week_close_location_aligned", "week_favorable_excursion_norm", "week_adverse_excursion_norm")})
        output.update(boundary_path(current_week, previous_week, sign, week_scale))

        days_this_week = [row for row in self.completed_days if start <= row["start"] < query]
        output["completed_days_in_week"] = float(len(days_this_week))
        if days_this_week:
            output["completed_day_direction_balance"] = float(np.mean([np.sign(sign * float(row["net"])) for row in days_this_week]))
            output["last_day_net_aligned_norm"] = period_net(days_this_week[-1], sign, day_scale)
            output["last_two_day_net_aligned_norm"] = sign * sum(float(row["net"]) for row in days_this_week[-2:]) / day_scale if np.isfinite(day_scale) else math.nan
        else:
            output.update({"completed_day_direction_balance": math.nan, "last_day_net_aligned_norm": math.nan,
                           "last_two_day_net_aligned_norm": math.nan})
        if day_summary is not None and np.isfinite(day_scale):
            path = float(day_summary["path_length"])
            output["current_day_range_norm"] = float(day_summary["range"]) / day_scale
            output["current_day_net_aligned_norm"] = sign * float(day_summary["net"]) / day_scale
            output["current_day_efficiency_aligned"] = sign * float(day_summary["net"]) / path if path > 0 else 0.0
        else:
            output.update({"current_day_range_norm": math.nan, "current_day_net_aligned_norm": math.nan,
                           "current_day_efficiency_aligned": math.nan})
        output["prev_day_boundary_state_aligned"] = aligned_boundary_state(
            float(day_summary["close"]) if day_summary else self.last_close, previous_day, sign)

        monday = next((row for row in reversed(days_this_week) if row["start"].weekday() == 0), None)
        output["monday_available"] = float(monday is not None)
        output["monday_range_norm"] = float(monday["range"]) / week_scale if monday is not None and np.isfinite(week_scale) else math.nan
        output["monday_net_aligned_norm"] = period_net(monday, sign, week_scale)
        output["monday_boundary_state_aligned"] = aligned_boundary_state(
            float(week_summary["close"]) if week_summary else self.last_close, monday, sign)

        h4s = [row for row in self.completed_h4 if start <= row["start"] < query]
        output["completed_h4_in_week"] = float(len(h4s))
        if h4s and np.isfinite(week_scale):
            output["last_three_h4_net_aligned_norm"] = sign * sum(float(row["net"]) for row in h4s[-3:]) / week_scale
            output["h4_direction_balance"] = float(np.mean([np.sign(sign * float(row["net"])) for row in h4s]))
            if previous_week is not None:
                favorable_accepts = sum(float(row["close"]) > float(previous_week["high"]) for row in h4s) if sign > 0 else sum(float(row["close"]) < float(previous_week["low"]) for row in h4s)
                opposed_accepts = sum(float(row["close"]) < float(previous_week["low"]) for row in h4s) if sign > 0 else sum(float(row["close"]) > float(previous_week["high"]) for row in h4s)
                output["h4_prev_week_accept_balance"] = float(favorable_accepts - opposed_accepts) / len(h4s)
            else:
                output["h4_prev_week_accept_balance"] = math.nan
        else:
            output.update({"last_three_h4_net_aligned_norm": math.nan, "h4_direction_balance": math.nan,
                           "h4_prev_week_accept_balance": math.nan})
        output.update(self.event_features(query, sign, week_scale))
        return output


def add_causal_v10_history(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    prior: list[dict[str, object]] = []
    for _, row in frame.sort_values(["decision_time", "signal_id"]).iterrows():
        decision = row["decision_time"]
        known = sorted((item for item in prior if item["exit_time"] < decision), key=lambda item: item["exit_time"])
        recent = known[-3:]
        item = row.to_dict()
        item["v10_k"] = float(row["k"])
        item["v10_r7g_weight"] = float(row["r7g_weight"])
        item["known_prior_children"] = float(len(known))
        item["last_known_stop"] = float(known[-1]["stop_hit"]) if known else math.nan
        item["last_known_R_clipped"] = float(np.clip(known[-1]["R"], -1, 5)) if known else math.nan
        item["last_three_known_stop_rate"] = float(np.mean([value["stop_hit"] for value in recent])) if recent else math.nan
        item["last_three_known_mean_R_clipped"] = float(np.mean([np.clip(value["R"], -1, 5) for value in recent])) if recent else math.nan
        rows.append(item)
        prior.append({"exit_time": row["exit_time"], "stop_hit": int(row["stop_hit"]), "R": float(row["R"])})
    return pd.DataFrame(rows)


def build_features(m1_path: Path, decisions: pd.DataFrame, clusters: pd.DataFrame,
                   cutoff: datetime) -> tuple[pd.DataFrame, PrefixAudit]:
    state = WeeklyStateBuilder(clusters)
    ordered = decisions.sort_values(["decision_time", "signal_id"]).reset_index(drop=True)
    snapshots: list[dict[str, object]] = []
    cursor = 0
    audit = PrefixAudit()
    for number, row in enumerate(iter_m1_prefix(m1_path, cutoff, audit=audit), 1):
        ts = row.timestamp
        state.roll(ts)
        while cursor < len(ordered) and ordered.at[cursor, "decision_time"].to_pydatetime() <= ts:
            decision = ordered.at[cursor, "decision_time"].to_pydatetime()
            state.release_events_before(decision, inclusive=False)
            base = {
                "signal_id": ordered.at[cursor, "signal_id"],
                "decision_time": pd.Timestamp(decision),
                "direction": ordered.at[cursor, "direction"],
            }
            base.update(state.snapshot(decision, int(ordered.at[cursor, "dir"])))
            snapshots.append(base)
            cursor += 1
        state.release_events_before(ts, inclusive=True)
        state.update(ts, row.open, row.high, row.low, row.close)
        if number % 500000 == 0:
            print(f"streamed {number} M1 rows; snapshotted {cursor}/{len(ordered)}")
    state.roll(cutoff + timedelta(minutes=1))
    while cursor < len(ordered) and ordered.at[cursor, "decision_time"].to_pydatetime() <= cutoff:
        decision = ordered.at[cursor, "decision_time"].to_pydatetime()
        state.release_events_before(decision, inclusive=False)
        base = {"signal_id": ordered.at[cursor, "signal_id"], "decision_time": pd.Timestamp(decision),
                "direction": ordered.at[cursor, "direction"]}
        base.update(state.snapshot(decision, int(ordered.at[cursor, "dir"])))
        snapshots.append(base)
        cursor += 1
    if cursor != len(ordered):
        raise ValueError(f"unsnapshotted decisions: {len(ordered) - cursor}")
    return pd.DataFrame(snapshots), audit


def make_model(features: list[str], contract: dict) -> Pipeline:
    preprocess = ColumnTransformer([
        ("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
            ("scale", StandardScaler()),
        ]), features),
    ], remainder="drop")
    model = LogisticRegression(
        C=float(contract["model"]["C"]), max_iter=int(contract["model"]["max_iter"]),
        random_state=int(contract["model"]["random_state"]), solver="lbfgs",
    )
    return Pipeline([("preprocess", preprocess), ("model", model)])


def fit_head(train: pd.DataFrame, test: pd.DataFrame, features: list[str], label: str,
             contract: dict) -> tuple[np.ndarray, np.ndarray]:
    y = train[label].astype(int)
    if y.nunique() != 2:
        raise ValueError(f"single-class training head: {label}")
    model = make_model(features, contract)
    model.fit(train[features], y)
    return model.predict_proba(train[features])[:, 1], model.predict_proba(test[features])[:, 1]


def safe_auc(y: pd.Series, prediction: np.ndarray) -> float:
    return float(roc_auc_score(y, prediction)) if y.nunique() == 2 else math.nan


def max_stop_streak(frame: pd.DataFrame) -> int:
    best = current = 0
    for stopped in frame.sort_values(["decision_time", "signal_id"])["stop_hit"].astype(int):
        current = current + 1 if stopped else 0
        best = max(best, current)
    return best


def drawdown(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    grouped = frame.groupby("exit_time", sort=True)["return_units"].sum()
    path = np.r_[0.0, grouped.cumsum().to_numpy(float)]
    return float(np.max(np.maximum.accumulate(path) - path))


def policy_score(frame: pd.DataFrame, units: pd.Series, strategy: str, scope: str) -> dict[str, object]:
    work = frame.copy()
    work["policy_units"] = pd.to_numeric(units, errors="raise").astype(float)
    work = work.loc[work["policy_units"] > 0].copy()
    work["return_units"] = work["R"].astype(float) * work["policy_units"]
    work["stopped_units"] = work["stop_hit"].astype(float) * work["policy_units"]
    returns = work["return_units"]
    funded = float(work["policy_units"].sum())
    stopped = float(work["stopped_units"].sum())
    gross_profit = float(returns.loc[returns > 0].sum())
    gross_loss = -float(returns.loc[returns < 0].sum())
    return {
        "strategy": strategy,
        "scope": scope,
        "children": int(len(work)),
        "funded_units": funded,
        "stopped_children": int(work["stop_hit"].sum()),
        "stopped_units": stopped,
        "stopped_units_per_100": stopped / funded * 100.0 if funded else math.nan,
        "win_rate": float((work["R"] > 0).mean()) if len(work) else math.nan,
        "net_R": float(returns.sum()),
        "R_per_100_funded": float(returns.sum() / funded * 100.0) if funded else math.nan,
        "profit_factor_R": gross_profit / gross_loss if gross_loss else math.nan,
        "max_drawdown_R": drawdown(work),
        "max_stop_streak": max_stop_streak(work),
        "tail_ge2_R_units": float(returns.where(work["R"] >= 2, 0.0).sum()),
        "tail_ge5_R_units": float(returns.where(work["R"] >= 5, 0.0).sum()),
        "order_fail_children": int((work["event"] == "ORDER_FAIL").sum()),
    }


def evaluate_models(frame: pd.DataFrame, contract: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    predictions, metrics = [], []
    for family, features in FEATURE_FAMILIES.items():
        for fold in contract["outer_walk_forward_folds"]:
            train_end = pd.Timestamp(fold["train_end"])
            test_start, test_end = pd.Timestamp(fold["test_start"]), pd.Timestamp(fold["test_end"])
            boundary_week = test_start.normalize() - pd.Timedelta(days=test_start.weekday())
            decision_week = frame["decision_time"].dt.normalize() - pd.to_timedelta(frame["decision_time"].dt.weekday, unit="D")
            train = frame.loc[(frame["decision_time"] <= train_end) & (frame["exit_time"] <= train_end)
                              & (decision_week < boundary_week)].copy()
            test = frame.loc[frame["decision_time"].between(test_start, test_end)].copy()
            p_stop_train, p_stop_test = fit_head(train, test, features, "stop_hit", contract)
            p_tail_train, p_tail_test = fit_head(train, test, features, "tail_ge2", contract)
            bad_train = p_stop_train - p_tail_train
            threshold = float(np.quantile(bad_train, 0.8, method="higher"))
            local = test[["signal_id", "decision_time", "exit_time", "direction", "event", "k",
                          "r7g_weight", "funded_units", "R", "stop_hit", "tail_ge2",
                          "prev_week_range_norm"]].copy()
            local.insert(0, "feature_family", family)
            local.insert(1, "fold", fold["fold"])
            local["train_rows"] = len(train)
            local["p_stop"] = p_stop_test
            local["p_tail_ge2"] = p_tail_test
            local["directional_badness"] = p_stop_test - p_tail_test
            local["train_top20_threshold"] = threshold
            local["flagged_direction"] = (local["directional_badness"] >= threshold).astype(int)
            scale_train = train["prev_week_range_norm"].dropna().astype(float)
            q1, q2 = scale_train.quantile([1.0 / 3.0, 2.0 / 3.0]).tolist()
            local["train_relative_week_range_q1"] = q1
            local["train_relative_week_range_q2"] = q2
            local["weekly_liquidity_band"] = pd.cut(
                local["prev_week_range_norm"], [-np.inf, q1, q2, np.inf], labels=["LOW", "MID", "HIGH"],
                include_lowest=True,
            ).astype(str)
            predictions.append(local)
            metrics.extend([
                {"feature_family": family, "fold": fold["fold"], "head": "STOP", "train_rows": len(train),
                 "test_rows": len(test), "positive_rows": int(test["stop_hit"].sum()),
                 "auc": safe_auc(test["stop_hit"], p_stop_test),
                 "brier": float(brier_score_loss(test["stop_hit"], p_stop_test))},
                {"feature_family": family, "fold": fold["fold"], "head": "TAIL_GE2", "train_rows": len(train),
                 "test_rows": len(test), "positive_rows": int(test["tail_ge2"].sum()),
                 "auc": safe_auc(test["tail_ge2"], p_tail_test),
                 "brier": float(brier_score_loss(test["tail_ge2"], p_tail_test))},
            ])
    return pd.concat(predictions, ignore_index=True), pd.DataFrame(metrics)


def score_policies(test_frame: pd.DataFrame, predictions: pd.DataFrame, contract: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    score_rows, fold_rows, side_rows, year_rows, liquidity_rows, flagged_rows = [], [], [], [], [], []
    baseline_units = test_frame["funded_units"].astype(float)
    baseline_score = policy_score(test_frame, baseline_units, "V10_R7G_BASELINE", "POOLED_OOS")
    score_rows.append({"feature_family": "BASELINE", **baseline_score})
    for family in FEATURE_FAMILIES:
        pred = predictions.loc[predictions["feature_family"] == family,
                               ["signal_id", "fold", "flagged_direction", "weekly_liquidity_band"]]
        work = test_frame.merge(pred, on="signal_id", how="inner", validate="one_to_one")
        if len(work) != len(test_frame):
            raise ValueError(f"prediction coverage mismatch: {family}")
        veto_units = work["funded_units"].where(work["flagged_direction"] == 0, 0.0)
        seed_units = work["funded_units"].where(work["flagged_direction"] == 0, np.minimum(work["funded_units"], 1.0))
        for strategy, units in (("FULL_DIRECTION_VETO", veto_units), ("SEED_PROTECTED_EXTRA_UNIT_GUARD", seed_units)):
            score_rows.append({"feature_family": family, **policy_score(work, units, strategy, "POOLED_OOS")})
            for fold, part in work.groupby("fold", sort=True):
                local_units = units.loc[part.index]
                fold_rows.append({"feature_family": family, **policy_score(part, local_units, strategy, fold)})
            for side, part in work.groupby("direction", sort=True):
                local_units = units.loc[part.index]
                side_rows.append({"feature_family": family, **policy_score(part, local_units, strategy, side)})
            for year, part in work.groupby(work["decision_time"].dt.year, sort=True):
                local_units = units.loc[part.index]
                year_rows.append({"feature_family": family, **policy_score(part, local_units, strategy, str(year))})
            for band, part in work.groupby("weekly_liquidity_band", sort=True):
                local_units = units.loc[part.index]
                liquidity_rows.append({"feature_family": family, **policy_score(part, local_units, strategy, str(band))})
        for fold, part in work.groupby("fold", sort=True):
            fold_rows.append({"feature_family": "BASELINE", **policy_score(part, part["funded_units"], "V10_R7G_BASELINE", fold)})
        for side, part in work.groupby("direction", sort=True):
            side_rows.append({"feature_family": "BASELINE", **policy_score(part, part["funded_units"], "V10_R7G_BASELINE", side)})
        for year, part in work.groupby(work["decision_time"].dt.year, sort=True):
            year_rows.append({"feature_family": "BASELINE", **policy_score(part, part["funded_units"], "V10_R7G_BASELINE", str(year))})
        for band, part in work.groupby("weekly_liquidity_band", sort=True):
            liquidity_rows.append({"feature_family": "BASELINE", **policy_score(part, part["funded_units"], "V10_R7G_BASELINE", str(band))})
        for state, part in work.groupby("flagged_direction", sort=True):
            flagged_rows.append({
                "feature_family": family,
                "cohort": "FLAGGED" if state else "KEPT",
                "children": len(part),
                "funded_units": float(part["funded_units"].sum()),
                "stop_rate": float(part["stop_hit"].mean()),
                "stopped_units": float((part["stop_hit"] * part["funded_units"]).sum()),
                "net_R": float((part["R"] * part["funded_units"]).sum()),
                "tail_ge2_children": int(part["tail_ge2"].sum()),
                "tail_ge5_R_units": float((part["R"] * part["funded_units"]).where(part["R"] >= 5, 0.0).sum()),
            })
    scores = pd.DataFrame(score_rows).drop_duplicates()
    folds = pd.DataFrame(fold_rows).drop_duplicates()
    sides = pd.DataFrame(side_rows).drop_duplicates()
    years = pd.DataFrame(year_rows).drop_duplicates()
    liquidity = pd.DataFrame(liquidity_rows).drop_duplicates()
    return scores, folds, sides, years, liquidity, pd.DataFrame(flagged_rows)


def evaluate_gates(scores: pd.DataFrame, folds: pd.DataFrame, sides: pd.DataFrame, contract: dict) -> pd.DataFrame:
    family = contract["primary_feature_family"]
    baseline = scores.loc[(scores["feature_family"] == "BASELINE") & (scores["strategy"] == "V10_R7G_BASELINE")].iloc[0]
    policy = scores.loc[(scores["feature_family"] == family) & (scores["strategy"] == contract["primary_policy"])].iloc[0]
    gates = contract["primary_gates"]
    child_retention = policy["children"] / baseline["children"]
    stop_density_relative = policy["stopped_units_per_100"] / baseline["stopped_units_per_100"]
    net_retention = policy["net_R"] / baseline["net_R"]
    tail_retention = policy["tail_ge5_R_units"] / baseline["tail_ge5_R_units"]
    equal_stop_budget_R = policy["net_R"] * baseline["stopped_units"] / policy["stopped_units"]
    fold_base = folds.loc[(folds["feature_family"] == "BASELINE") & (folds["strategy"] == "V10_R7G_BASELINE")].set_index("scope")
    fold_policy = folds.loc[(folds["feature_family"] == family) & (folds["strategy"] == contract["primary_policy"])].set_index("scope")
    nonnegative_folds = sum(float(fold_policy.at[name, "net_R"]) >= float(fold_base.at[name, "net_R"]) for name in fold_policy.index)
    side_base = sides.loc[(sides["feature_family"] == "BASELINE") & (sides["strategy"] == "V10_R7G_BASELINE")].set_index("scope")
    side_policy = sides.loc[(sides["feature_family"] == family) & (sides["strategy"] == contract["primary_policy"])].set_index("scope")
    both_side_stop = all(float(side_policy.at[name, "stopped_units_per_100"]) < float(side_base.at[name, "stopped_units_per_100"]) for name in side_policy.index)
    def side_R_pass(name: str) -> bool:
        base_value = float(side_base.at[name, "net_R"])
        policy_value = float(side_policy.at[name, "net_R"])
        if base_value > 0:
            return policy_value / base_value >= gates["both_sides_net_R_retention_min"]
        return policy_value >= base_value
    both_side_R = all(side_R_pass(name) for name in side_policy.index)
    rows = [
        ("CHILDREN_RETENTION", child_retention, gates["children_retention_min"], child_retention >= gates["children_retention_min"]),
        ("STOP_DENSITY_RELATIVE", stop_density_relative, gates["stopped_units_per_100_relative_max"], stop_density_relative <= gates["stopped_units_per_100_relative_max"]),
        ("NET_R_RETENTION", net_retention, gates["net_R_retention_min"], net_retention >= gates["net_R_retention_min"]),
        ("TAIL_GE5_RETENTION", tail_retention, gates["right_tail_ge5_R_retention_min"], tail_retention >= gates["right_tail_ge5_R_retention_min"]),
        ("EQUAL_STOP_BUDGET_R_RELATIVE", equal_stop_budget_R / baseline["net_R"], gates["equal_stop_budget_R_relative_min"], equal_stop_budget_R >= baseline["net_R"]),
        ("NONNEGATIVE_FOLD_DELTA_COUNT", float(nonnegative_folds), float(gates["nonnegative_fold_delta_min_count"]), nonnegative_folds >= gates["nonnegative_fold_delta_min_count"]),
        ("BOTH_SIDES_STOP_DENSITY_IMPROVES", float(both_side_stop), 1.0, both_side_stop),
        ("BOTH_SIDES_NET_R_RETENTION", float(both_side_R), 1.0, both_side_R),
    ]
    result = pd.DataFrame(rows, columns=["gate", "observed", "required", "pass"])
    result["all_primary_gates_pass"] = bool(result["pass"].all())
    return result


def save_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n")


def write_json(value: object, path: Path) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1s_contract.json")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--calendar", type=Path, default=Path.home() / "AppData/Roaming/MetaQuotes/Terminal/Common/Files/V12_PHASE1E_MQL5_CALENDAR_SNAPSHOT.csv")
    parser.add_argument("--calendar-overrides", type=Path, default=repo / "research/v12/v12_calendar_time_overrides.json")
    parser.add_argument("--v10-ledger", type=Path, default=repo / "output/v11_reassembly_stage3_20260923/V11_REASSEMBLY_STAGE3_CHILD_LEDGER.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1s_v10_weekly_journey_direction_20260925_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != VERSION:
        raise ValueError("contract version mismatch")
    hashes = contract["source_hashes"]
    for path, key, label in (
        (args.m1, "raw_m1_full_sha256", "raw M1"),
        (args.calendar, "calendar_snapshot_sha256", "calendar"),
        (args.calendar_overrides, "calendar_time_overrides_sha256", "calendar overrides"),
        (args.v10_ledger, "v10_r7g_comparator_ledger_sha256", "V10 R7G ledger"),
    ):
        verify(path, hashes[key], label)
    safe_output(args.output, args.replace)

    cutoff = parse_cutoff("2026-09-18T23:57:00")
    calendar, calendar_quality = load_calendar(args.calendar, cutoff, args.calendar_overrides)
    clusters = build_clusters(calendar)
    v10 = pd.read_csv(args.v10_ledger, low_memory=False)
    v10 = v10.loc[v10["policy"] == contract["population"]["policy"]].copy()
    if len(v10) != contract["population"]["expected_children"]:
        raise ValueError("V10 population mismatch")
    v10 = v10.rename(columns={"decision_ts": "decision_time"})
    for column in ("decision_time", "entry_time", "exit_time"):
        v10[column] = pd.to_datetime(v10[column])
    v10["direction"] = np.where(v10["dir"].astype(int) > 0, "LONG", "SHORT")
    v10["tail_ge2"] = (v10["R"].astype(float) >= 2.0).astype(int)

    features, audit = build_features(args.m1, v10, clusters, cutoff)
    if audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("raw M1 prefix hash mismatch")
    feature_outcomes = v10.merge(features, on=["signal_id", "decision_time", "direction"], how="inner", validate="one_to_one")
    feature_outcomes = add_causal_v10_history(feature_outcomes)
    if len(feature_outcomes) != len(v10):
        raise ValueError("feature coverage mismatch")

    feature_columns = sorted(set(sum(FEATURE_FAMILIES.values(), [])))
    feature_ledger = feature_outcomes[["signal_id", "decision_time", "direction", "snapshot_last_m1_time"] + feature_columns].copy()
    outcomes = feature_outcomes[["signal_id", "decision_time", "entry_time", "exit_time", "direction", "event", "k",
                                "r7g_weight", "funded_units", "R", "stop_hit", "tail_ge2"]].copy()
    predictions, model_metrics = evaluate_models(feature_outcomes, contract)
    primary_predictions = predictions.loc[predictions["feature_family"] == contract["primary_feature_family"]]
    test_ids = set(primary_predictions["signal_id"])
    test_frame = feature_outcomes.loc[feature_outcomes["signal_id"].isin(test_ids)].copy()
    scores, folds, sides, years, liquidity, flagged = score_policies(test_frame, predictions, contract)
    gates = evaluate_gates(scores, folds, sides, contract)
    inventory = pd.DataFrame([
        {"feature_family": family, "feature_order": index, "feature": name}
        for family, names in FEATURE_FAMILIES.items() for index, name in enumerate(names, 1)
    ])

    snapshot_times = pd.to_datetime(feature_ledger["snapshot_last_m1_time"], errors="coerce")
    strict_snapshots = int((snapshot_times < feature_ledger["decision_time"]).sum())
    data_quality = {
        "contract_version": VERSION,
        "source_hashes": hashes,
        "raw_m1_prefix_rows": audit.parsed_price_rows,
        "raw_m1_prefix_sha256": audit.prefix_sha256,
        "v10_children": len(v10),
        "feature_rows": len(feature_ledger),
        "strictly_prior_snapshot_rows": strict_snapshots,
        "blank_snapshot_rows": int(snapshot_times.isna().sum()),
        "primary_test_rows": len(test_frame),
        "primary_feature_count": len(FEATURE_FAMILIES[contract["primary_feature_family"]]),
        "same_week_boundary_embargo": True,
        "weekly_liquidity_breakdown": "PREVIOUS_COMPLETED_WEEK_RANGE_DIVIDED_BY_PRIOR20_WEEK_MEDIAN_WITH_TRAIN_ONLY_TERCILES",
        "discarded_process_builds": [
            "INITIAL_A_BUILD_BEFORE_BOUNDARY_WEEK_EMBARGO_FIX_NOT_USED_FOR_RESULT"
        ],
        "calendar": calendar_quality,
    }
    summary = {
        "contract_version": VERSION,
        "primary_feature_family": contract["primary_feature_family"],
        "primary_policy": contract["primary_policy"],
        "v10_children": len(v10),
        "oos_children": len(test_frame),
        "all_primary_gates_pass": bool(gates["all_primary_gates_pass"].iloc[0]),
        "trade_authority": False,
        "sizing_authority": False,
    }

    save_csv(feature_ledger, args.output / f"{PREFIX}FEATURE_LEDGER.csv")
    save_csv(outcomes, args.output / f"{PREFIX}OUTCOMES.csv")
    save_csv(predictions, args.output / f"{PREFIX}WALK_FORWARD_PREDICTIONS.csv")
    save_csv(model_metrics, args.output / f"{PREFIX}MODEL_METRICS.csv")
    save_csv(scores, args.output / f"{PREFIX}POLICY_SCORECARDS.csv")
    save_csv(folds, args.output / f"{PREFIX}FOLD_SCORECARDS.csv")
    save_csv(sides, args.output / f"{PREFIX}SIDE_SCORECARDS.csv")
    save_csv(years, args.output / f"{PREFIX}YEAR_SCORECARDS.csv")
    save_csv(liquidity, args.output / f"{PREFIX}LIQUIDITY_SCORECARDS.csv")
    save_csv(flagged, args.output / f"{PREFIX}FLAGGED_COHORTS.csv")
    save_csv(gates, args.output / f"{PREFIX}GATES.csv")
    save_csv(inventory, args.output / f"{PREFIX}FEATURE_INVENTORY.csv")
    write_json(data_quality, args.output / f"{PREFIX}DATA_QUALITY.json")
    write_json(summary, args.output / f"{PREFIX}SUMMARY.json")
    manifest = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(args.output.glob(f"{PREFIX}*"))
    }
    write_json(manifest, args.output / f"{PREFIX}RELEASE_MANIFEST.json")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
