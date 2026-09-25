from datetime import datetime
import unittest

import numpy as np
import pandas as pd

from v12_phase1o_core import add_causal_history, policy_metrics, train_risk_threshold


class Phase1OTests(unittest.TestCase):
    def test_history_respects_label_availability(self):
        frame = pd.DataFrame([
            {"signal_id": "a", "decision_time": "2025-01-01 00:00", "label_available_at": "2025-01-01 02:00", "stop_hit": 1, "R": -1, "L": 1, "position_hours": 1, "stop_dist_atr": 1},
            {"signal_id": "b", "decision_time": "2025-01-01 01:00", "label_available_at": "2025-01-01 03:00", "stop_hit": 1, "R": -1, "L": 1, "position_hours": 1, "stop_dist_atr": 1},
            {"signal_id": "c", "decision_time": "2025-01-01 03:00", "label_available_at": "2025-01-01 04:00", "stop_hit": 0, "R": 2, "L": 2, "position_hours": 1, "stop_dist_atr": 1},
        ])
        result = add_causal_history(frame)
        self.assertEqual(result.loc[1, "hist_lag1_known"], 0)
        self.assertEqual(result.loc[1, "after_stop_cohort"], 0)
        self.assertEqual(result.loc[2, "hist_lag1_known"], 1)
        self.assertEqual(result.loc[2, "after_stop_cohort"], 1)
        self.assertEqual(result.loc[2, "hist_known_prior_stop_streak"], 2)

    def test_train_threshold_is_train_distribution_only(self):
        self.assertEqual(train_risk_threshold(np.arange(5.0)), 3.2)

    def test_policy_metrics(self):
        frame = pd.DataFrame({"stop_hit": [1, 0], "R": [-1.0, 6.0]})
        result = policy_metrics(frame)
        self.assertEqual(result["stops_per_100"], 50)
        self.assertEqual(result["net_R"], 5)
        self.assertEqual(result["tail_ge5_R"], 6)


if __name__ == "__main__":
    unittest.main()
