"""Causal continuous-time path primitives for V12 Phase-1G.

All timestamps are naive broker labels (fixed UTC+3).  A query at timestamp T
may use M1 rows strictly before T only.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Optional
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


BROKER_OFFSET = timedelta(hours=3)
UTC = timezone.utc
TOKYO = ZoneInfo("Asia/Tokyo")
LONDON = ZoneInfo("Europe/London")
NEW_YORK = ZoneInfo("America/New_York")


def local_to_broker(day: date, clock: time, zone: ZoneInfo) -> datetime:
    aware = datetime.combine(day, clock, tzinfo=zone)
    return aware.astimezone(UTC).replace(tzinfo=None) + BROKER_OFFSET


def broker_to_local(value: datetime, zone: ZoneInfo) -> datetime:
    utc = (value - BROKER_OFFSET).replace(tzinfo=UTC)
    return utc.astimezone(zone)


def clock_coordinates(value: datetime) -> dict[str, float]:
    output: dict[str, float] = {}
    for label, zone in (("tokyo", TOKYO), ("london", LONDON), ("new_york", NEW_YORK)):
        local = broker_to_local(value, zone)
        minute = local.hour * 60 + local.minute
        angle = 2.0 * np.pi * minute / 1440.0
        output[f"clock_{label}_sin"] = float(np.sin(angle))
        output[f"clock_{label}_cos"] = float(np.cos(angle))
    broker_minute = value.hour * 60 + value.minute
    angle = 2.0 * np.pi * broker_minute / 1440.0
    output["clock_broker_sin"] = float(np.sin(angle))
    output["clock_broker_cos"] = float(np.cos(angle))
    week_angle = 2.0 * np.pi * (value.weekday() * 1440 + broker_minute) / (7.0 * 1440.0)
    output["clock_week_sin"] = float(np.sin(week_angle))
    output["clock_week_cos"] = float(np.cos(week_angle))
    return output


@dataclass(frozen=True)
class Box:
    box_id: str
    family: str
    local_date: str
    start: datetime
    end: datetime
    open: float
    high: float
    low: float
    close: float
    observed_minutes: int
    scheduled_minutes: int
    path_length: float

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def net(self) -> float:
        return self.close - self.open

    @property
    def efficiency(self) -> float:
        return self.net / self.path_length if self.path_length > 0 else 0.0


class MarketIndex:
    def __init__(self, market: pd.DataFrame):
        ordered = market.sort_values("timestamp").reset_index(drop=True)
        self.times = ordered["timestamp"].to_numpy(dtype="datetime64[ns]")
        self.opens = ordered["open"].to_numpy(dtype=float)
        self.highs = ordered["high"].to_numpy(dtype=float)
        self.lows = ordered["low"].to_numpy(dtype=float)
        self.closes = ordered["close"].to_numpy(dtype=float)

    def bounds(self, start: datetime, end: datetime) -> tuple[int, int]:
        left = int(np.searchsorted(self.times, np.datetime64(start), side="left"))
        right = int(np.searchsorted(self.times, np.datetime64(end), side="left"))
        return left, right

    def build_box(self, family: str, local_day: date, start: datetime, end: datetime) -> Optional[Box]:
        left, right = self.bounds(start, end)
        if right <= left:
            return None
        close_path = np.concatenate(([self.opens[left]], self.closes[left:right]))
        path_length = float(np.abs(np.diff(close_path)).sum())
        return Box(
            box_id=f"{family}:{local_day.isoformat()}",
            family=family,
            local_date=local_day.isoformat(),
            start=start,
            end=end,
            open=float(self.opens[left]),
            high=float(self.highs[left:right].max()),
            low=float(self.lows[left:right].min()),
            close=float(self.closes[right - 1]),
            observed_minutes=right - left,
            scheduled_minutes=int((end - start).total_seconds() // 60),
            path_length=path_length,
        )

    def path(self, box: Box, query: datetime, point: float = 0.01) -> dict[str, object]:
        """Describe the post-box path using rows in [box.end, query)."""
        left, right = self.bounds(box.end, query)
        scale = max(box.range, point)
        base = {
            "available": 1,
            "minutes_since_end": (query - box.end).total_seconds() / 60.0,
            "observed_post_minutes": right - left,
        }
        if right <= left:
            return {
                **base,
                "high_broken": 0,
                "low_broken": 0,
                "break_order": "NONE",
                "first_high_break_time": "",
                "first_low_break_time": "",
                "minutes_since_high_break": np.nan,
                "minutes_since_low_break": np.nan,
                "max_high_extension": 0.0,
                "max_low_extension": 0.0,
                "dwell_above_fraction": 0.0,
                "dwell_inside_fraction": 0.0,
                "dwell_below_fraction": 0.0,
                "boundary_transitions": 0,
                "outside_to_inside_reentries": 0,
                "minutes_since_last_transition": np.nan,
                "settlement_location": (box.close - (box.high + box.low) / 2.0) / scale,
                "post_net": 0.0,
                "post_path_length": 0.0,
                "post_efficiency": 0.0,
            }
        highs = np.rint(self.highs[left:right] / point).astype(np.int64)
        lows = np.rint(self.lows[left:right] / point).astype(np.int64)
        closes = np.rint(self.closes[left:right] / point).astype(np.int64)
        high_edge = int(round(box.high / point))
        low_edge = int(round(box.low / point))
        high_hits = np.flatnonzero(highs > high_edge)
        low_hits = np.flatnonzero(lows < low_edge)
        hi = int(high_hits[0]) if len(high_hits) else None
        lo = int(low_hits[0]) if len(low_hits) else None
        if hi is None and lo is None:
            order = "NONE"
        elif hi is None:
            order = "LOW_FIRST"
        elif lo is None:
            order = "HIGH_FIRST"
        elif hi == lo:
            order = "SAME_M1_AMBIGUOUS"
        else:
            order = "HIGH_FIRST" if hi < lo else "LOW_FIRST"
        zones = np.where(closes > high_edge, 1, np.where(closes < low_edge, -1, 0))
        changes = np.flatnonzero(zones[1:] != zones[:-1]) + 1
        reentries = int(sum(zones[index - 1] != 0 and zones[index] == 0 for index in changes))
        last_transition_time = None if not len(changes) else pd.Timestamp(self.times[left + int(changes[-1])]).to_pydatetime()
        high_time = None if hi is None else pd.Timestamp(self.times[left + hi]).to_pydatetime()
        low_time = None if lo is None else pd.Timestamp(self.times[left + lo]).to_pydatetime()
        start_close = box.close
        close_path = np.concatenate(([start_close], self.closes[left:right]))
        path_length = float(np.abs(np.diff(close_path)).sum())
        final_close = float(self.closes[right - 1])
        return {
            **base,
            "high_broken": int(hi is not None),
            "low_broken": int(lo is not None),
            "break_order": order,
            "first_high_break_time": high_time.isoformat() if high_time else "",
            "first_low_break_time": low_time.isoformat() if low_time else "",
            "minutes_since_high_break": (query - high_time).total_seconds() / 60.0 if high_time else np.nan,
            "minutes_since_low_break": (query - low_time).total_seconds() / 60.0 if low_time else np.nan,
            "max_high_extension": max(0.0, float(self.highs[left:right].max()) - box.high),
            "max_low_extension": max(0.0, box.low - float(self.lows[left:right].min())),
            "dwell_above_fraction": float(np.mean(zones == 1)),
            "dwell_inside_fraction": float(np.mean(zones == 0)),
            "dwell_below_fraction": float(np.mean(zones == -1)),
            "boundary_transitions": int(len(changes)),
            "outside_to_inside_reentries": reentries,
            "minutes_since_last_transition": (
                (query - last_transition_time).total_seconds() / 60.0 if last_transition_time else np.nan
            ),
            "settlement_location": (final_close - (box.high + box.low) / 2.0) / scale,
            "post_net": final_close - start_close,
            "post_path_length": path_length,
            "post_efficiency": (final_close - start_close) / path_length if path_length > 0 else 0.0,
        }


def generate_boxes(index: MarketIndex, first_day: date, last_day: date) -> list[Box]:
    boxes: list[Box] = []
    day = first_day
    while day <= last_day:
        specs = [
            ("ASIA_COMPLETE", local_to_broker(day, time(8, 45), TOKYO), local_to_broker(day, time(15, 45), TOKYO)),
            (
                "LONDON_AT_NEW_YORK_OPEN",
                local_to_broker(day, time(8), LONDON),
                local_to_broker(day, time(8, 30), NEW_YORK),
            ),
            ("LONDON_COMPLETE", local_to_broker(day, time(8), LONDON), local_to_broker(day, time(16, 30), LONDON)),
            ("NEW_YORK_COMPLETE", local_to_broker(day, time(8, 30), NEW_YORK), local_to_broker(day, time(16), NEW_YORK)),
        ]
        for family, start, end in specs:
            box = index.build_box(family, day, start, end)
            if box is not None:
                boxes.append(box)
        day += timedelta(days=1)
    return sorted(boxes, key=lambda value: (value.end, value.family, value.box_id))


def boxes_by_family(boxes: Iterable[Box]) -> dict[str, list[Box]]:
    output: dict[str, list[Box]] = {}
    for box in boxes:
        output.setdefault(box.family, []).append(box)
    return output


def latest_box(values: list[Box], query: datetime) -> Optional[Box]:
    ends = [box.end for box in values]
    index = bisect_right(ends, query) - 1
    return values[index] if index >= 0 else None


def daily_prior_medians(market: pd.DataFrame, window: int = 60) -> dict[date, float]:
    work = market.assign(broker_date=pd.to_datetime(market["timestamp"]).dt.date)
    daily = work.groupby("broker_date").agg(high=("high", "max"), low=("low", "min"))
    values = (daily["high"] - daily["low"]).astype(float)
    prior = values.shift(1).rolling(window=window, min_periods=20).median()
    return {key: float(value) for key, value in prior.items() if np.isfinite(value)}


def cross_box(a: Optional[Box], b: Optional[Box], normalizer: float) -> dict[str, float]:
    if a is None or b is None:
        return {"available": 0, "overlap_ratio": np.nan, "center_separation_norm": np.nan,
                "range_ratio": np.nan, "directional_alignment": np.nan}
    overlap = max(0.0, min(a.high, b.high) - max(a.low, b.low))
    union = max(a.high, b.high) - min(a.low, b.low)
    return {
        "available": 1,
        "overlap_ratio": overlap / union if union > 0 else 0.0,
        "center_separation_norm": (((b.high + b.low) - (a.high + a.low)) / 2.0) / max(normalizer, 0.01),
        "range_ratio": b.range / max(a.range, 0.01),
        "directional_alignment": float(np.sign(a.net) * np.sign(b.net)),
    }


def weighted_metrics(y: np.ndarray, p: np.ndarray, w: np.ndarray) -> dict[str, float]:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    total = float(w.sum())
    brier = float(np.sum(w * (p - y) ** 2) / total)
    logloss = float(-np.sum(w * (y * np.log(p) + (1 - y) * np.log(1 - p))) / total)
    pos = y == 1
    neg = y == 0
    denom = float(w[pos].sum() * w[neg].sum())
    if denom == 0:
        auc = np.nan
    else:
        order = np.argsort(p, kind="mergesort")
        ps, ys, ws = p[order], y[order], w[order]
        concordant = 0.0
        neg_before = 0.0
        i = 0
        while i < len(ps):
            j = i + 1
            while j < len(ps) and ps[j] == ps[i]:
                j += 1
            block_pos = float(ws[i:j][ys[i:j] == 1].sum())
            block_neg = float(ws[i:j][ys[i:j] == 0].sum())
            concordant += block_pos * (neg_before + 0.5 * block_neg)
            neg_before += block_neg
            i = j
        auc = concordant / denom
    return {"brier": brier, "logloss": logloss, "auc": float(auc)}


class Encoder:
    def __init__(self, numeric: list[str], categorical: list[str]):
        self.numeric = numeric
        self.categorical = categorical
        self.medians: dict[str, float] = {}
        self.means: dict[str, float] = {}
        self.stds: dict[str, float] = {}
        self.levels: dict[str, list[str]] = {}

    def fit(self, frame: pd.DataFrame) -> "Encoder":
        for column in self.numeric:
            values = pd.to_numeric(frame[column], errors="coerce")
            median = float(values.median()) if values.notna().any() else 0.0
            filled = values.fillna(median).to_numpy(float)
            self.medians[column] = median
            self.means[column] = float(filled.mean())
            std = float(filled.std())
            self.stds[column] = std if std > 1e-12 else 1.0
        for column in self.categorical:
            self.levels[column] = sorted(set(frame[column].fillna("__MISSING__").astype(str)))
        return self

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        columns = [np.ones(len(frame), dtype=float)]
        for column in self.numeric:
            values = pd.to_numeric(frame[column], errors="coerce").fillna(self.medians[column]).to_numpy(float)
            columns.append((values - self.means[column]) / self.stds[column])
        for column in self.categorical:
            values = frame[column].fillna("__MISSING__").astype(str).to_numpy()
            for level in self.levels[column]:
                columns.append((values == level).astype(float))
        return np.column_stack(columns)


def fit_ridge_logistic(x: np.ndarray, y: np.ndarray, w: np.ndarray, ridge: float,
                       max_iter: int = 80) -> np.ndarray:
    beta = np.zeros(x.shape[1], dtype=float)
    penalty = np.ones(x.shape[1], dtype=float)
    penalty[0] = 0.0
    weight_scale = w / max(float(w.mean()), 1e-12)
    for _ in range(max_iter):
        p = 1.0 / (1.0 + np.exp(-np.clip(x @ beta, -35, 35)))
        curvature = weight_scale * np.maximum(p * (1.0 - p), 1e-6)
        gradient = x.T @ (weight_scale * (p - y)) + ridge * penalty * beta
        hessian = x.T @ (curvature[:, None] * x) + np.diag(ridge * penalty + 1e-8)
        step = np.linalg.solve(hessian, gradient)
        beta_next = beta - step
        if float(np.max(np.abs(beta_next - beta))) < 1e-8:
            beta = beta_next
            break
        beta = beta_next
    return beta


def predict_logistic(x: np.ndarray, beta: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x @ beta, -35, 35)))


def fit_ridge_linear(x: np.ndarray, y: np.ndarray, w: np.ndarray, ridge: float) -> np.ndarray:
    weight_scale = w / max(float(w.mean()), 1e-12)
    penalty = np.ones(x.shape[1], dtype=float)
    penalty[0] = 0.0
    lhs = x.T @ (weight_scale[:, None] * x) + np.diag(ridge * penalty + 1e-8)
    rhs = x.T @ (weight_scale * y)
    return np.linalg.solve(lhs, rhs)


def weighted_regression_metrics(y: np.ndarray, p: np.ndarray, w: np.ndarray) -> dict[str, float]:
    total = float(w.sum())
    error = p - y
    mse = float(np.sum(w * error ** 2) / total)
    mae = float(np.sum(w * np.abs(error)) / total)
    center = float(np.sum(w * y) / total)
    variance = float(np.sum(w * (y - center) ** 2) / total)
    return {"rmse": float(np.sqrt(mse)), "mae": mae, "r2": 1.0 - mse / variance if variance > 0 else np.nan}
