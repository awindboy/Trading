"""Boundary and future-isolation tests for failed-seed footprints."""
import unittest
import pandas as pd
from build_v12_phase1w import decisions, footprint_state


def seed(run, decision, exit_time, result):
    return dict(run_id=run, decision=pd.Timestamp(decision), exit_time=pd.Timestamp(exit_time),
                direction="LONG", entry=101., stop=97., signal_low=98.,
                signal_high=102., signal_close=100., stop_dist_atr=1., causal_atr180=4., R=result)


class FootprintTests(unittest.TestCase):
    def test_mirrored_boundaries(self):
        self.assertEqual(footprint_state(102, 98, 102, 1), "INSIDE")
        self.assertEqual(footprint_state(103, 98, 102, 1), "OUTSIDE_FAVORABLE")
        self.assertEqual(footprint_state(97, 98, 102, -1), "OUTSIDE_FAVORABLE")
        self.assertEqual(footprint_state(103, 98, 102, -1), "OUTSIDE_OPPOSED")

    def test_unresolved_and_equal_exit_not_used(self):
        for end in ("2025-01-02 04:00", "2025-01-02 05:00"):
            frame = pd.DataFrame([seed(1, "2025-01-02", end, -1),
                                  seed(2, "2025-01-02 04:00", "2025-01-02 08:00", 10)])
            result = decisions(frame).iloc[1]
            self.assertEqual(result.known_prior_loss, 0)
            self.assertEqual(result.skip_h4, 0)

    def test_current_future_outcome_cannot_change_decision(self):
        frame = pd.DataFrame([seed(1, "2025-01-02", "2025-01-02 03:59", -1),
                              seed(2, "2025-01-02 04:00", "2025-01-02 08:00", 10)])
        before = decisions(frame)
        frame.loc[1, "R"] = -100
        frame.loc[1, "exit_time"] = pd.Timestamp("2025-02-01")
        pd.testing.assert_frame_equal(before, decisions(frame))
        self.assertEqual(before.iloc[1].skip_h4, 1)

    def test_prefix_invariance_and_previous_winner(self):
        frame = pd.DataFrame([seed(1, "2025-01-02", "2025-01-02 03:59", 1),
                              seed(2, "2025-01-02 04:00", "2025-01-02 08:00", -1)])
        pd.testing.assert_frame_equal(decisions(frame.iloc[:1]), decisions(frame).iloc[:1], check_dtype=False)
        self.assertEqual(decisions(frame).iloc[1].skip_h4, 0)


if __name__ == "__main__":
    unittest.main()
