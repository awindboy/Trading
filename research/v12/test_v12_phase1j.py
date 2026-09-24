import unittest

import numpy as np
import pandas as pd

from v12_phase1j_core import event_snapshots, rank_auc, standardized_difference, weighted_tail_price


class Phase1JCoreTests(unittest.TestCase):
    def test_weighted_tail_price(self):
        self.assertEqual(weighted_tail_price(100, 95, 1, 1), 125)
        self.assertEqual(weighted_tail_price(100, 105, -1, 2.5), 90)

    def test_rank_auc(self):
        self.assertEqual(rank_auc(np.array([0, 0, 1, 1]), np.array([1, 2, 3, 4])), 1.0)
        self.assertEqual(rank_auc(np.array([0, 0, 1, 1]), np.array([4, 3, 2, 1])), 0.0)

    def test_standardized_difference_direction(self):
        self.assertGreater(standardized_difference(np.array([0, 1]), np.array([2, 3])), 0)

    def test_event_snapshot_and_checkpoint(self):
        frame = pd.DataFrame([{"events": "FIRST_FAVORABLE_CLOSE", "completed_m15_bars": 1}])
        observed = set(event_snapshots(frame)["snapshot"])
        self.assertEqual(observed, {"FIRST_FAVORABLE_CLOSE", "CHECKPOINT_M15_1"})


if __name__ == "__main__":
    unittest.main()
