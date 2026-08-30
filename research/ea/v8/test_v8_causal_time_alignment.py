"""Regression tests for the V8-B1 higher-timeframe look-ahead failure mode."""
from __future__ import annotations

import numpy as np
import pandas as pd

from v8_causal_time_alignment import (
    assert_prefix_only,
    build_partial_current_ohlc,
    resample_completed_ohlc,
    select_last_completed_bar,
)


def synthetic_m1() -> pd.DataFrame:
    idx = pd.date_range("2026-01-05 09:00", "2026-01-05 10:59", freq="1min")
    base = 100.0 + np.arange(len(idx), dtype=float) * 0.01
    frame = pd.DataFrame(
        {
            "open": base,
            "high": base + 0.05,
            "low": base - 0.05,
            "close": base + 0.01,
        },
        index=idx,
    )
    # Deliberate future spikes after the 10:25 decision. A leaky full H1/M15
    # representation would see these; a causal partial bar must not.
    frame.loc[pd.Timestamp("2026-01-05 10:40"), ["high", "close"]] = [9999.0, 9998.0]
    frame.loc[pd.Timestamp("2026-01-05 10:41"), ["low", "close"]] = [-9999.0, -9998.0]
    return frame


def test_completed_selection_uses_availability_time() -> None:
    m1 = synthetic_m1()
    decision = pd.Timestamp("2026-01-05 10:25")

    h1 = resample_completed_ohlc(m1, 60)
    got_h1 = select_last_completed_bar(h1, decision)
    assert got_h1 is not None
    assert got_h1.start == pd.Timestamp("2026-01-05 09:00")
    assert got_h1.available_at == pd.Timestamp("2026-01-05 10:00")
    assert got_h1.row["high"] < 9999.0

    m15 = resample_completed_ohlc(m1, 15)
    got_m15 = select_last_completed_bar(m15, decision)
    assert got_m15 is not None
    assert got_m15.start == pd.Timestamp("2026-01-05 10:00")
    assert got_m15.available_at == pd.Timestamp("2026-01-05 10:15")


def test_partial_current_bar_uses_only_prefix() -> None:
    m1 = synthetic_m1()
    decision = pd.Timestamp("2026-01-05 10:25")

    partial_h1 = build_partial_current_ohlc(m1, decision, 60)
    assert partial_h1 is not None
    assert partial_h1["start"] == pd.Timestamp("2026-01-05 10:00")
    assert partial_h1["source_last_m1"] == pd.Timestamp("2026-01-05 10:24")
    assert partial_h1["source_rows"] == 25
    assert partial_h1["high"] < 9999.0
    assert partial_h1["low"] > -9999.0

    partial_m15 = build_partial_current_ohlc(m1, decision, 15)
    assert partial_m15 is not None
    assert partial_m15["start"] == pd.Timestamp("2026-01-05 10:15")
    assert partial_m15["source_last_m1"] == pd.Timestamp("2026-01-05 10:24")
    assert partial_m15["source_rows"] == 10


def test_prefix_assertion_rejects_future_row() -> None:
    decision = pd.Timestamp("2026-01-05 10:25")
    assert_prefix_only(pd.date_range("2026-01-05 10:00", "2026-01-05 10:24", freq="1min"), decision)
    try:
        assert_prefix_only([pd.Timestamp("2026-01-05 10:25")], decision)
    except AssertionError:
        pass
    else:
        raise AssertionError("expected future-boundary assertion")


if __name__ == "__main__":
    test_completed_selection_uses_availability_time()
    test_partial_current_bar_uses_only_prefix()
    test_prefix_assertion_rejects_future_row()
    print("PASS: V8 causal time-alignment regression tests")
