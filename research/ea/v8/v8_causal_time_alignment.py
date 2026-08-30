"""Causal time-alignment primitives for V8 research.

The availability timestamp, not the higher-timeframe bar-start timestamp, is the
information boundary. This module exists because V8-B1 was invalidated after a
left-labeled M15/H1 resample was selected by bar start and exposed the future
remainder of the current HTF bar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


OHLC_AGG = {
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
}


@dataclass(frozen=True)
class CausalBarSelection:
    start: pd.Timestamp
    available_at: pd.Timestamp
    row: pd.Series


def _require_datetime_index(frame: pd.DataFrame) -> None:
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("frame.index must be a pandas.DatetimeIndex")
    if not frame.index.is_monotonic_increasing:
        raise ValueError("timestamps must be monotonic increasing")
    if frame.index.has_duplicates:
        raise ValueError("timestamps must be unique")


def resample_completed_ohlc(m1: pd.DataFrame, timeframe_minutes: int) -> pd.DataFrame:
    """Return left-labeled HTF OHLC plus explicit causal availability timestamp.

    A row labeled 10:00 for H1 is available at 11:00, never at 10:00.
    Partial final groups are retained in the table but are still not selectable
    before their nominal end; callers can separately choose to reject sparse bars.
    """
    if timeframe_minutes <= 0:
        raise ValueError("timeframe_minutes must be positive")
    _require_datetime_index(m1)
    missing = [c for c in OHLC_AGG if c not in m1.columns]
    if missing:
        raise KeyError(f"missing OHLC columns: {missing}")

    rule = f"{timeframe_minutes}min"
    out = m1.resample(rule, label="left", closed="left").agg(OHLC_AGG).dropna()
    out["available_at"] = out.index + pd.Timedelta(minutes=timeframe_minutes)
    return out


def select_last_completed_bar(
    htf: pd.DataFrame,
    decision_time: pd.Timestamp,
) -> CausalBarSelection | None:
    """Select the latest HTF row whose explicit availability is <= decision_time."""
    _require_datetime_index(htf)
    if "available_at" not in htf.columns:
        raise KeyError("HTF table must contain explicit available_at")

    t = pd.Timestamp(decision_time)
    ends = pd.DatetimeIndex(htf["available_at"])
    pos = int(ends.searchsorted(t, side="right") - 1)
    if pos < 0:
        return None
    row = htf.iloc[pos]
    available_at = pd.Timestamp(row["available_at"])
    if available_at > t:
        raise AssertionError("future HTF bar selected")
    return CausalBarSelection(
        start=pd.Timestamp(htf.index[pos]),
        available_at=available_at,
        row=row,
    )


def build_partial_current_ohlc(
    m1: pd.DataFrame,
    decision_time: pd.Timestamp,
    timeframe_minutes: int,
) -> pd.Series | None:
    """Build the current partial HTF bar from M1 rows strictly before decision_time.

    The decision timestamp is interpreted as an information timestamp. An M1 row
    stamped exactly at the decision time is not used, because that minute has not
    completed yet at the instant of decision.
    """
    if timeframe_minutes <= 0:
        raise ValueError("timeframe_minutes must be positive")
    _require_datetime_index(m1)
    missing = [c for c in OHLC_AGG if c not in m1.columns]
    if missing:
        raise KeyError(f"missing OHLC columns: {missing}")

    t = pd.Timestamp(decision_time)
    start = t.floor(f"{timeframe_minutes}min")
    prefix = m1[(m1.index >= start) & (m1.index < t)]
    if prefix.empty:
        return None

    return pd.Series(
        {
            "start": start,
            "available_at": t,
            "source_last_m1": pd.Timestamp(prefix.index[-1]),
            "source_rows": int(len(prefix)),
            "open": float(prefix["open"].iloc[0]),
            "high": float(prefix["high"].max()),
            "low": float(prefix["low"].min()),
            "close": float(prefix["close"].iloc[-1]),
        }
    )


def assert_prefix_only(source_times: Iterable[pd.Timestamp], decision_time: pd.Timestamp) -> None:
    """Fail if any source timestamp is at/after the decision information boundary."""
    t = pd.Timestamp(decision_time)
    idx = pd.DatetimeIndex(source_times)
    if len(idx) and idx.max() >= t:
        raise AssertionError(f"future/non-completed source row used: {idx.max()} >= {t}")
