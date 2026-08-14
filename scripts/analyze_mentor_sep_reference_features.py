from __future__ import annotations

import csv
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz, parse_utc
from mentor_engine.models import BarSeries


DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
REFERENCE = ROOT / "output" / "mentor_50trade_scope_locked_v1" / "working_trades.csv"
OUTPUT = ROOT / "output" / "mentor_sep2025_ea_parity" / "reference_source_features.csv"


def iso(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def bar_index(series: BarSeries, timestamp: int) -> int:
    matches = np.flatnonzero(series.time == timestamp)
    return int(matches[0]) if matches.size else -1


def true_range(series: BarSeries) -> np.ndarray:
    previous = np.r_[series.close[0], series.close[:-1]]
    return np.maximum(
        series.high - series.low,
        np.maximum(np.abs(series.high - previous), np.abs(series.low - previous)),
    )


def rolling_mean(values: np.ndarray, index: int, length: int) -> float:
    start = max(0, index - length)
    window = values[start:index]
    return float(np.mean(window)) if window.size else 0.0


def first_confirmation(series: BarSeries, origin: int, bullish: bool) -> int:
    end = min(len(series.time) - 1, origin + 8)
    for index in range(origin + 1, end + 1):
        opposite = series.close[index] < series.open[index] if bullish else series.close[index] > series.open[index]
        if opposite:
            return -1
        if bullish and series.close[index] > series.high[origin]:
            return index
        if not bullish and series.close[index] < series.low[origin]:
            return index
    return -1


def first_touch_after(series: BarSeries, confirmation: int, low: float, high: float) -> int:
    for index in range(confirmation + 1, len(series.time)):
        if series.high[index] >= low and series.low[index] <= high:
            return index
    return -1


@dataclass
class SourceFeature:
    trade_id: str
    role: str
    timeframe: str
    origin: str
    bullish: bool
    low: float
    high: float
    confirmation: str
    confirmation_bars: int
    first_touch: str
    first_touch_bars: int
    atr14: float
    zone_atr: float
    impulse_atr: float
    body_impulse_atr: float
    break_high_3: bool
    break_high_5: bool
    break_high_10: bool
    break_high_20: bool
    break_low_3: bool
    break_low_5: bool
    break_low_10: bool
    break_low_20: bool
    origin_range_percent_20: float
    child_inside_parent: bool
    child_same_parent_bar: bool


def source_feature(
    trade_id: str,
    role: str,
    series: BarSeries,
    origin_timestamp: int,
    low: float,
    high: float,
    parent: tuple[int, int, float, float] | None,
) -> SourceFeature:
    origin = bar_index(series, origin_timestamp)
    if origin < 0:
        raise ValueError(f"missing {trade_id} {role} origin {iso(origin_timestamp)}")
    bullish = bool(series.close[origin] < series.open[origin])
    confirmation = first_confirmation(series, origin, bullish)
    tr = true_range(series)
    atr = rolling_mean(tr, origin, 14)
    if confirmation >= 0:
        impulse_high = float(np.max(series.high[origin : confirmation + 1]))
        impulse_low = float(np.min(series.low[origin : confirmation + 1]))
        body_high = float(np.max(np.maximum(series.open[origin : confirmation + 1], series.close[origin : confirmation + 1])))
        body_low = float(np.min(np.minimum(series.open[origin : confirmation + 1], series.close[origin : confirmation + 1])))
        touch = first_touch_after(series, confirmation, low, high)
    else:
        impulse_high = impulse_low = body_high = body_low = 0.0
        touch = -1

    def prior_high(length: int) -> float:
        return float(np.max(series.high[max(0, origin - length) : origin]))

    def prior_low(length: int) -> float:
        return float(np.min(series.low[max(0, origin - length) : origin]))

    confirm_close = float(series.close[confirmation]) if confirmation >= 0 else float("nan")
    recent_low = prior_low(20)
    recent_high = prior_high(20)
    range_width = recent_high - recent_low
    midpoint = (low + high) / 2.0
    range_percent = (midpoint - recent_low) / range_width if range_width > 0 else float("nan")
    parent_inside = False
    same_parent_bar = False
    if parent is not None:
        parent_time, parent_seconds, parent_low, parent_high = parent
        parent_inside = low >= parent_low - 1e-9 and high <= parent_high + 1e-9
        same_parent_bar = parent_time <= origin_timestamp < parent_time + parent_seconds

    return SourceFeature(
        trade_id=trade_id,
        role=role,
        timeframe=series.timeframe,
        origin=iso(origin_timestamp),
        bullish=bullish,
        low=low,
        high=high,
        confirmation=iso(int(series.available_time[confirmation])) if confirmation >= 0 else "",
        confirmation_bars=confirmation - origin if confirmation >= 0 else -1,
        first_touch=iso(int(series.time[touch])) if touch >= 0 else "",
        first_touch_bars=touch - confirmation if touch >= 0 and confirmation >= 0 else -1,
        atr14=atr,
        zone_atr=(high - low) / atr if atr else float("nan"),
        impulse_atr=(impulse_high - impulse_low) / atr if atr and confirmation >= 0 else float("nan"),
        body_impulse_atr=(body_high - body_low) / atr if atr and confirmation >= 0 else float("nan"),
        break_high_3=confirmation >= 0 and confirm_close > prior_high(3),
        break_high_5=confirmation >= 0 and confirm_close > prior_high(5),
        break_high_10=confirmation >= 0 and confirm_close > prior_high(10),
        break_high_20=confirmation >= 0 and confirm_close > prior_high(20),
        break_low_3=confirmation >= 0 and confirm_close < prior_low(3),
        break_low_5=confirmation >= 0 and confirm_close < prior_low(5),
        break_low_10=confirmation >= 0 and confirm_close < prior_low(10),
        break_low_20=confirmation >= 0 and confirm_close < prior_low(20),
        origin_range_percent_20=range_percent,
        child_inside_parent=parent_inside,
        child_same_parent_bar=same_parent_bar,
    )


def main() -> int:
    m1, _ = load_m1_npz(
        DATASET,
        start=parse_utc("2025-08-01T00:00:00Z"),
        end=parse_utc("2025-10-15T00:00:00Z"),
    )
    timeframes = build_timeframes(m1)
    rows: list[SourceFeature] = []
    with REFERENCE.open("r", encoding="utf-8-sig", newline="") as handle:
        for trade in csv.DictReader(handle):
            if not trade["decision_at"].startswith("2025-09"):
                continue
            root_time = int(parse_utc(trade["root_time"]) or 0)
            root_low = float(trade["root_low"])
            root_high = float(trade["root_high"])
            root_series = timeframes[trade["root_tf"]]
            rows.append(
                source_feature(
                    trade["trade_id"],
                    "root",
                    root_series,
                    root_time,
                    root_low,
                    root_high,
                    None,
                )
            )
            child_series = timeframes[trade["child_tf"]]
            child_time = int(parse_utc(trade["child_time"]) or 0)
            rows.append(
                source_feature(
                    trade["trade_id"],
                    "child",
                    child_series,
                    child_time,
                    float(trade["child_low"]),
                    float(trade["child_high"]),
                    (root_time, root_series.seconds, root_low, root_high),
                )
            )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)

    detected = sum(row.confirmation_bars >= 0 for row in rows)
    print(f"wrote={OUTPUT}")
    print(f"rows={len(rows)} raw_source_detected={detected}")
    for role in ("root", "child"):
        subset = [row for row in rows if row.role == role]
        print(
            role,
            "detected",
            sum(row.confirmation_bars >= 0 for row in subset),
            "break5",
            sum((row.break_high_5 if row.bullish else row.break_low_5) for row in subset),
            "break10",
            sum((row.break_high_10 if row.bullish else row.break_low_10) for row in subset),
            "same_parent_bar",
            sum(row.child_same_parent_bar for row in subset),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
