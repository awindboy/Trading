from datetime import datetime
from types import SimpleNamespace
import unittest

import numpy as np

from v12_phase1h_core import apply_quintile_thresholds, train_quintile_thresholds
from v12_phase1n_core import age_hours, direction_relation, micro_path_features, wave_distribution_features


def row(o, h, l, c, direction=1, body=1.0):
    return SimpleNamespace(raw_open=o, raw_high=h, raw_low=l, raw_close=c, ha_dir=direction, ha_body=body)


class Phase1NTests(unittest.TestCase):
    def test_wave_distribution_is_bounded_and_directional(self):
        values = [row(10, 11, 9, 10.5), row(10.5, 12, 10, 11.5), row(11.5, 13, 11, 12.5)]
        out = wave_distribution_features(values, 1, 10, 13, 9, 2)
        self.assertTrue(0 <= out["wave_price_time_median"] <= 1)
        self.assertTrue(0 <= out["wave_entropy_8bin"] <= 1)
        self.assertGreater(out["wave_settlement_aligned"], 0)
        self.assertGreater(out["wave_path_efficiency_aligned"], 0)

    def test_micro_path_uses_completed_sequence(self):
        values = [row(10, 11, 9, 11, 1, 1), row(11, 12, 10, 10.5, -1, -0.5)]
        out = micro_path_features(values, 1, 10, 2, "m5")
        self.assertEqual(out["m5_aligned_fraction"], 0.5)
        self.assertEqual(out["m5_transitions"], 1)

    def test_parent_relation_and_causal_age(self):
        self.assertEqual(direction_relation(1, "LONG"), "ALIGNED")
        self.assertEqual(direction_relation(-1, "LONG"), "OPPOSED")
        self.assertEqual(direction_relation(1, "NONE"), "NO_DIRECTION")
        self.assertEqual(age_hours(datetime(2025, 1, 2), "2025-01-01T12:00:00"), 12)

    def test_train_only_quintile_boundaries_apply_to_extreme_test_scores(self):
        cuts = train_quintile_thresholds(np.arange(10, dtype=float))
        self.assertEqual(apply_quintile_thresholds(np.asarray([-99.0, 99.0]), cuts).tolist(), [1, 5])


if __name__ == "__main__":
    unittest.main()
