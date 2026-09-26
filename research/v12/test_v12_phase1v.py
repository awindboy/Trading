"""Regression tests for Phase-1V entry-episode accounting."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_v12_phase1v import (  # noqa: E402
    annotate_policy_sequence,
    apply_policy,
    episode_summary,
)


def synthetic_episodes() -> pd.DataFrame:
    return pd.DataFrame({
        "run_id": [1, 2, 3, 4, 5],
        "run_start": pd.date_range("2025-01-01", periods=5, freq="4h"),
        "direction": ["LONG", "SHORT", "LONG", "LONG", "SHORT"],
        "ownership_state": [
            "FAST_WITH_MEMORY", "FAST_ONLY_CHALLENGE", "TRANSFER_CONFIRMED",
            "STD_LEADS_TRANSFER", "FAST_WITH_MEMORY",
        ],
        "first_child_hard_sl": [1, 1, 0, 0, 1],
        "positive_episode": [0, 0, 1, 0, 1],
        "negative_episode": [1, 1, 0, 1, 0],
        "tail_episode": [0, 0, 1, 0, 0],
        "episode_count_score": [-1, -1, 1, -1, 1],
        "non_tail_count_score": [-1, -1, 0, -1, 1],
        "net_R_units": [-1.0, -1.0, 6.0, -0.4, 0.5],
        "first_child_stopped_units": [1, 1, 0, 0, 1],
        "later_child_stopped_units": [0, 0, 0, 1, 0],
        "first_child_R": [-1.0, -1.0, 2.0, 0.5, -1.0],
        "later_child_R": [0.0, 0.0, 4.0, -0.9, 1.5],
        "funded_units": [1, 1, 3, 2, 2],
        "stopped_units": [1, 1, 0, 1, 1],
        "tail_units": [0, 0, 3, 0, 0],
    })


class Phase1VTests(unittest.TestCase):
    def test_repeated_start_stops_and_negative_streaks_are_separate(self) -> None:
        sequenced = annotate_policy_sequence(synthetic_episodes())
        self.assertEqual(sequenced["repeat_first_child_stop"].tolist(), [0, 1, 0, 0, 0])
        self.assertEqual(sequenced["alternating_repeat_first_stop"].sum(), 1)
        self.assertEqual(sequenced.attrs["max_first_stop_streak"], 2)
        self.assertEqual(sequenced["repeat_negative_episode"].tolist(), [0, 1, 0, 0, 0])
        self.assertEqual(sequenced.attrs["max_negative_episode_streak"], 2)

    def test_episode_count_curve_ignores_r_magnitude(self) -> None:
        summary = episode_summary(synthetic_episodes())
        self.assertEqual(summary["positive_episodes"], 2)
        self.assertEqual(summary["negative_episodes"], 3)
        self.assertEqual(summary["episode_count_balance"], -1)
        self.assertEqual(summary["tail_episodes"], 1)
        self.assertEqual(summary["non_tail_count_balance"], -2)
        self.assertAlmostEqual(summary["non_tail_count_slope"], -0.5)
        self.assertAlmostEqual(summary["net_R_units"], 4.1)

    def test_entry_policy_keeps_complete_authorized_episodes(self) -> None:
        admitted = apply_policy(
            synthetic_episodes(), "ENTRY_OWNERSHIP_AUTHORIZED",
            {"FAST_WITH_MEMORY", "TRANSFER_CONFIRMED"},
        )
        self.assertEqual(admitted["run_id"].tolist(), [1, 3, 5])
        self.assertAlmostEqual(admitted["net_R_units"].sum(), 5.5)
        self.assertAlmostEqual(admitted["later_child_R"].sum(), 5.5)


if __name__ == "__main__":
    unittest.main()
