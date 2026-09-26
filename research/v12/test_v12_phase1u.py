"""Regression tests for the Phase-1U multi-speed HA diagnostic."""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_v12_phase1u import classify_h4, maximum_stop_streak, outcome_counts


class Phase1UTests(unittest.TestCase):
    def test_memory_is_classified_before_current_bar_updates_it(self) -> None:
        frame = pd.DataFrame(
            {
                "h4_start": pd.date_range("2025-01-01", periods=4, freq="4h"),
                "decision": pd.date_range("2025-01-01 04:00", periods=4, freq="4h"),
                "fast_dir": [1, -1, -1, -1],
                "std_dir": [1, 1, -1, -1],
                "slow_dir": [1, 1, 1, -1],
            }
        )
        result = classify_h4(frame)
        self.assertEqual(
            result["ownership_state"].tolist(),
            [
                "MEMORY_UNAVAILABLE",
                "FAST_ONLY_CHALLENGE",
                "STD_LEADS_TRANSFER",
                "TRANSFER_CONFIRMED",
            ],
        )
        self.assertEqual(result["memory_owner_before"].tolist(), [0, 1, 1, 1])
        self.assertEqual(result["memory_owner_after"].tolist(), [1, 1, 1, -1])
        self.assertEqual(
            result["transition_signature"].tolist(),
            ["INITIAL", "00_TO_00", "00_TO_10", "10_TO_11"],
        )

    def test_return_to_memory_is_not_a_new_transfer(self) -> None:
        frame = pd.DataFrame(
            {
                "h4_start": pd.date_range("2025-02-01", periods=3, freq="4h"),
                "decision": pd.date_range("2025-02-01 04:00", periods=3, freq="4h"),
                "fast_dir": [1, -1, 1],
                "std_dir": [1, 1, 1],
                "slow_dir": [1, 1, 1],
            }
        )
        result = classify_h4(frame)
        self.assertEqual(result.iloc[2]["ownership_state"], "FAST_WITH_MEMORY")
        self.assertEqual(result.iloc[2]["event_role"], "RETURN_TO_MEMORY")
        self.assertEqual(result.iloc[2]["transition_signature"], "11_TO_11")

    def test_count_metrics_and_streak_are_child_based(self) -> None:
        frame = pd.DataFrame(
            {
                "decision": pd.date_range("2025-03-01", periods=5, freq="4h"),
                "stop_hit": [1, 1, 0, 1, 1],
                "R": [-1.0, -1.0, 5.2, -1.0, 0.4],
                "r7g_weight": [3, 1, 2, 2, 1],
                "dir": [1, -1, 1, 1, -1],
            }
        )
        counts = outcome_counts(frame)
        self.assertEqual(counts["hard_sl_children"], 4)
        self.assertEqual(counts["positive_children"], 2)
        self.assertEqual(counts["positive_ge5r"], 1)
        self.assertEqual(counts["repeat_stop_children"], 2)
        self.assertEqual(counts["alternating_stop_pairs"], 2)
        self.assertEqual(counts["stopped_units"], 7)
        self.assertEqual(maximum_stop_streak(frame), 2)


if __name__ == "__main__":
    unittest.main()
