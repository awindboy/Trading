from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from .models import BarSeries


TIMEFRAME_SECONDS = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
}


def parse_utc(value: str | None) -> int | None:
    if value is None:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def load_m1_npz(
    path: str | Path,
    start: int | None = None,
    end: int | None = None,
) -> tuple[BarSeries, dict[str, object]]:
    payload = np.load(Path(path), allow_pickle=True)
    rates = payload["rates"]
    mask = np.ones(rates.shape[0], dtype=bool)
    if start is not None:
        mask &= rates["time"] >= int(start)
    if end is not None:
        mask &= rates["time"] < int(end)
    rates = rates[mask]
    if not rates.size:
        raise ValueError("selected dataset range has no M1 bars")
    metadata_raw = payload["metadata"].item()
    metadata = json.loads(str(metadata_raw))
    times = rates["time"].astype(np.int64)
    return (
        BarSeries(
            timeframe="M1",
            seconds=60,
            time=times,
            available_time=times + 60,
            open=rates["open"].astype(float),
            high=rates["high"].astype(float),
            low=rates["low"].astype(float),
            close=rates["close"].astype(float),
            spread_points=rates["spread"].astype(float),
        ),
        metadata,
    )


def aggregate_m1(m1: BarSeries, timeframe: str) -> BarSeries:
    if timeframe == "M1":
        return m1
    seconds = TIMEFRAME_SECONDS[timeframe]
    buckets = (m1.time // seconds) * seconds
    starts = np.flatnonzero(np.r_[True, buckets[1:] != buckets[:-1]])
    ends = np.r_[starts[1:] - 1, len(m1) - 1]
    return BarSeries(
        timeframe=timeframe,
        seconds=seconds,
        time=buckets[starts].astype(np.int64),
        available_time=(buckets[starts] + seconds).astype(np.int64),
        open=m1.open[starts],
        high=np.maximum.reduceat(m1.high, starts),
        low=np.minimum.reduceat(m1.low, starts),
        close=m1.close[ends],
        spread_points=m1.spread_points[ends],
    )


def build_timeframes(m1: BarSeries) -> dict[str, BarSeries]:
    return {
        timeframe: aggregate_m1(m1, timeframe)
        for timeframe in ("H1", "M30", "M15", "M5", "M1")
    }


def index_at_or_before(series: BarSeries, timestamp: int) -> int:
    return int(np.searchsorted(series.available_time, timestamp, side="right") - 1)
