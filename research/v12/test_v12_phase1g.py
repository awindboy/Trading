#!/usr/bin/env python3
"""Focused causal and numeric tests for V12 Phase-1G."""

from datetime import date, datetime, time

import numpy as np
import pandas as pd

from v12_phase1g_core import (
    Encoder,
    LONDON,
    MarketIndex,
    NEW_YORK,
    daily_prior_medians,
    fit_ridge_linear,
    fit_ridge_logistic,
    local_to_broker,
    predict_logistic,
)


def market(rows):
    return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close"])


def test_dst() -> None:
    assert local_to_broker(date(2025, 1, 15), time(8, 30), NEW_YORK) == datetime(2025, 1, 15, 16, 30)
    assert local_to_broker(date(2025, 7, 15), time(8, 30), NEW_YORK) == datetime(2025, 7, 15, 15, 30)
    assert local_to_broker(date(2025, 1, 15), time(8), LONDON) == datetime(2025, 1, 15, 11)
    assert local_to_broker(date(2025, 7, 15), time(8), LONDON) == datetime(2025, 7, 15, 10)


def test_causal_path() -> None:
    rows = [
        (datetime(2025, 1, 2, 10, 0), 100, 101, 99, 100),
        (datetime(2025, 1, 2, 10, 1), 100, 102, 100, 101),
        # equality is only a touch
        (datetime(2025, 1, 2, 10, 2), 101, 102, 99, 102),
        # both edges strictly break in one M1
        (datetime(2025, 1, 2, 10, 3), 102, 103, 98, 103),
        (datetime(2025, 1, 2, 10, 4), 103, 103, 99, 100),
        # this row must not be visible at query 10:05
        (datetime(2025, 1, 2, 10, 5), 100, 110, 90, 100),
    ]
    index = MarketIndex(market(rows))
    box = index.build_box("TEST", date(2025, 1, 2), datetime(2025, 1, 2, 10), datetime(2025, 1, 2, 10, 2))
    assert box is not None and box.high == 102 and box.low == 99
    path = index.path(box, datetime(2025, 1, 2, 10, 5))
    assert path["break_order"] == "SAME_M1_AMBIGUOUS"
    assert path["observed_post_minutes"] == 3
    assert path["max_high_extension"] == 1
    assert path["max_low_extension"] == 1
    assert path["outside_to_inside_reentries"] == 1


def test_prior_daily_range() -> None:
    rows = []
    for day in range(1, 23):
        stamp = datetime(2025, 1, day)
        rows.append((stamp, 100, 100 + day, 100, 100))
    values = daily_prior_medians(market(rows), window=60)
    # 22 January sees only days 1..21, median 11; current range 22 is excluded.
    assert values[date(2025, 1, 22)] == 11


def test_train_only_encoder_and_determinism() -> None:
    train = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0], "cat": ["A", "A", "B", "B"]})
    test = pd.DataFrame({"x": [100.0], "cat": ["UNSEEN"]})
    encoder = Encoder(["x"], ["cat"]).fit(train)
    assert "UNSEEN" not in encoder.levels["cat"]
    x = encoder.transform(train)
    y = np.array([0, 0, 1, 1])
    w = np.ones(4)
    first = fit_ridge_logistic(x, y, w, 1.0)
    second = fit_ridge_logistic(x, y, w, 1.0)
    assert np.allclose(first, second)
    assert predict_logistic(encoder.transform(test), first).shape == (1,)
    linear_first = fit_ridge_linear(x, y.astype(float), w, 1.0)
    linear_second = fit_ridge_linear(x, y.astype(float), w, 1.0)
    assert np.allclose(linear_first, linear_second)


if __name__ == "__main__":
    test_dst()
    test_causal_path()
    test_prior_daily_range()
    test_train_only_encoder_and_determinism()
    print("phase1g tests passed")
