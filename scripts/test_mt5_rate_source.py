from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.mt5_rate_source import load_rate_cache, parse_utc, rate_fingerprint, save_rate_cache


RATE_DTYPE = np.dtype(
    [
        ("time", "<i8"),
        ("open", "<f8"),
        ("high", "<f8"),
        ("low", "<f8"),
        ("close", "<f8"),
        ("tick_volume", "<u8"),
        ("spread", "<i4"),
        ("real_volume", "<u8"),
    ]
)


class Mt5RateSourceTests(unittest.TestCase):
    def test_parse_utc_normalizes_naive_and_z_suffix(self) -> None:
        self.assertEqual(parse_utc("2025-01-01T00:00:00Z").isoformat(), "2025-01-01T00:00:00+00:00")
        self.assertEqual(parse_utc("2025-01-01 00:00:00").isoformat(), "2025-01-01T00:00:00+00:00")

    def test_npz_cache_round_trip_preserves_rates_and_fingerprint(self) -> None:
        rates = np.zeros(120, dtype=RATE_DTYPE)
        rates["time"] = np.arange(120, dtype=np.int64) * 60 + 1_700_000_000
        rates["open"] = np.linspace(100.0, 101.0, 120)
        rates["high"] = rates["open"] + 1.0
        rates["low"] = rates["open"] - 1.0
        rates["close"] = rates["open"] + 0.25
        rates["tick_volume"] = 10
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "rates.npz"
            save_rate_cache(path, rates, {"symbol": "GOLD", "timeframe": "M1"})
            loaded, metadata = load_rate_cache(path)
        self.assertTrue(np.array_equal(rates, loaded))
        self.assertEqual(metadata["sha256"], rate_fingerprint(rates))
        self.assertEqual(metadata["symbol"], "GOLD")


if __name__ == "__main__":
    unittest.main()
