#!/usr/bin/env python3

from datetime import datetime
import unittest

from build_v12_phase1d import child_summary, proximity_state


class Phase1DTest(unittest.TestCase):
    def test_proximity_is_causal_and_boundary_exact(self) -> None:
        event = datetime(2026, 1, 2, 12, 30)
        self.assertEqual(proximity_state(datetime(2026, 1, 2, 12, 0), [event])[0], "PRE_15_30")
        self.assertEqual(proximity_state(event, [event])[0], "AT_RELEASE")
        self.assertEqual(proximity_state(datetime(2026, 1, 2, 13, 30), [event])[0], "POST_30_60")
        self.assertEqual(proximity_state(datetime(2026, 1, 2, 17, 0), [event])[0], "FAR_GT_240")

    def test_child_summary_preserves_exposure_and_right_tail(self) -> None:
        rows = [
            {
                "decision_time": "2026-01-01T00:00:00",
                "funded_units": "3",
                "stopped_loss_units": "3",
                "combined_R_units": "-3",
                "right_tail_ge_5R_units": "0",
                "stop_hit": "1",
            },
            {
                "decision_time": "2026-01-01T04:00:00",
                "funded_units": "1",
                "stopped_loss_units": "0",
                "combined_R_units": "6",
                "right_tail_ge_5R_units": "6",
                "stop_hit": "0",
            },
        ]
        value = child_summary(rows)
        self.assertEqual(value["stopped_units_per_100_funded"], 75.0)
        self.assertEqual(value["net_R"], 3.0)
        self.assertEqual(value["right_tail_ge_5R_units"], 6.0)
        self.assertEqual(value["max_stop_chain"], 1)


if __name__ == "__main__":
    unittest.main()
