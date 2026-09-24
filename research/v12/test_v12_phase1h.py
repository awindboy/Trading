import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase1h import feature_specs
from v12_phase1h_core import (
    apply_quintile_thresholds,
    attach_ha_features,
    build_h4_ha_features,
    capital_summary,
    compact_path_derivatives,
    tilt_summary,
    train_quintile_thresholds,
)


class Phase1HCoreTests(unittest.TestCase):
    def test_train_thresholds_are_applied_without_test_refit(self):
        cuts = train_quintile_thresholds(np.arange(10, dtype=float))
        self.assertTrue(np.allclose(cuts, [1.8, 3.6, 5.4, 7.2]))
        bands = apply_quintile_thresholds(np.array([-100.0, 1.8, 3.5, 100.0]), cuts)
        self.assertEqual(bands.tolist(), [1, 2, 2, 5])

    def test_compact_path_derivatives(self):
        frame = pd.DataFrame({
            "asia_observed_post_minutes": [120.0, 0.0],
            "asia_outside_to_inside_reentries": [3.0, 2.0],
            "asia_minutes_since_last_transition": [9.0, np.nan],
        })
        result = compact_path_derivatives(frame, ("asia",))
        self.assertAlmostEqual(result.loc[0, "asia_reentry_rate_per_hour"], 1.5)
        self.assertEqual(result.loc[1, "asia_reentry_rate_per_hour"], 0.0)
        self.assertAlmostEqual(result.loc[0, "asia_log_minutes_since_last_transition"], np.log(10.0))

    def test_capital_and_tilt(self):
        frame = pd.DataFrame({
            "funded_units": [1.0, 2.0],
            "stopped_loss_units": [1.0, 0.0],
            "combined_R_units": [-1.0, 4.0],
            "right_tail_ge_5R_units": [0.0, 1.0],
            "conviction_band": [1, 5],
        })
        base = capital_summary(frame)
        tilt = tilt_summary(frame)
        self.assertAlmostEqual(base["net_R_per_unit"], 1.0)
        self.assertAlmostEqual(tilt["funded_units"], 3.25)
        self.assertAlmostEqual(tilt["stopped_units"], 0.75)
        self.assertAlmostEqual(tilt["net_R_units"], 4.25)

    def test_ha_features_are_prior_completed_h4_and_direction_aligned(self):
        timestamps = pd.date_range("2024-01-01", periods=220, freq="4h")
        market = pd.DataFrame({
            "timestamp": timestamps,
            "open": np.arange(220, dtype=float) + 100.0,
            "high": np.arange(220, dtype=float) + 102.0,
            "low": np.arange(220, dtype=float) + 99.0,
            "close": np.arange(220, dtype=float) + 101.0,
        })
        h4 = build_h4_ha_features(market)
        child = pd.DataFrame({
            "signal_id": ["L", "S"],
            "decision_time": [timestamps[-1] + pd.Timedelta(hours=4)] * 2,
            "direction": ["LONG", "SHORT"],
        })
        result = attach_ha_features(child, h4)
        self.assertTrue(np.isfinite(result["ha_fast_body_aligned_atr180"]).all())
        self.assertAlmostEqual(result.loc[0, "ha_fast_body_aligned_atr180"],
                               -result.loc[1, "ha_fast_body_aligned_atr180"])
        self.assertEqual(result.loc[0, "ha_fast_aligned"] + result.loc[1, "ha_fast_aligned"], 1)

    def test_primary_source_count_is_exactly_fifty(self):
        root = Path(__file__).resolve().parents[2]
        contract = json.loads((root / "research/v12/v12_phase1h_contract.json").read_text(encoding="utf-8"))
        specs = feature_specs(contract)
        numeric, categorical = specs["COMPACT_PATH"]
        self.assertEqual(len(numeric) + len(categorical), 50)
        self.assertEqual(len(numeric), len(set(numeric)))
        self.assertEqual(len(categorical), len(set(categorical)))


if __name__ == "__main__":
    unittest.main()
