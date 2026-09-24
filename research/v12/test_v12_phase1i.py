import unittest

import numpy as np
import pandas as pd

from v12_phase1i_core import (
    annotate_prior_run_state,
    choose_train_threshold,
    classify_run,
    enrich_comparison,
    policy_mask,
    policy_summary,
)


def sample_runs() -> pd.DataFrame:
    return pd.DataFrame({
        "run_id": [10, 11, 13, 14],
        "run_start": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]),
        "run_exit": pd.to_datetime(["2025-01-01 20:00", "2025-01-02 20:00", "2025-01-03 20:00", "2025-01-04 20:00"]),
        "direction": ["LONG", "SHORT", "LONG", "SHORT"],
        "run_class": ["STOP_ONLY_RUN", "STOP_ONLY_RUN", "TAIL_JOURNEY_RUN", "NEUTRAL_RUN"],
        "child_count": [2, 1, 2, 1],
        "winning_children": [0, 0, 2, 1],
        "funded_units": [2.0, 1.0, 2.0, 1.0],
        "stopped_units": [2.0, 1.0, 0.0, 0.0],
        "net_R_units": [-2.0, -1.0, 8.0, 1.0],
        "tail_units": [0.0, 0.0, 6.0, 0.0],
    })


class Phase1ICoreTests(unittest.TestCase):
    def test_classification_priority(self):
        self.assertEqual(classify_run(2.0, 1.0), "TAIL_JOURNEY_RUN")
        self.assertEqual(classify_run(2.0, 0.0), "STOP_ONLY_RUN")
        self.assertEqual(classify_run(0.0, 0.0), "NEUTRAL_RUN")

    def test_prior_state_and_repeat_are_causal(self):
        result = annotate_prior_run_state(sample_runs())
        self.assertEqual(result.loc[1, "known_consecutive_stop_only_runs"], 1)
        self.assertEqual(result.loc[1, "repeat_stop_run"], 1)
        self.assertEqual(result.loc[1, "strict_adjacent_repeat_stop_run"], 1)
        self.assertEqual(result.loc[2, "known_consecutive_stop_only_runs"], 2)
        self.assertEqual(result.loc[2, "funded_run_id_gap"], 2.0)
        self.assertTrue((result["prior_funded_run_known"] == 1).all())

    def test_unresolved_prior_run_is_rejected(self):
        frame = sample_runs()
        frame.loc[0, "run_exit"] = pd.Timestamp("2025-01-03")
        with self.assertRaises(ValueError):
            annotate_prior_run_state(frame)

    def test_policy_metrics_measure_repeat_and_tail_tradeoff(self):
        runs = annotate_prior_run_state(sample_runs())
        baseline = policy_summary(runs, np.ones(len(runs), dtype=bool))
        policy = policy_summary(runs, np.array([True, False, True, True]))
        result = enrich_comparison(policy, baseline)
        self.assertEqual(baseline["repeat_stopped_units"], 1.0)
        self.assertEqual(result["repeat_stopped_units_removed_fraction"], 1.0)
        self.assertEqual(result["tail_unit_retention"], 1.0)
        self.assertGreater(result["child_win_rate_change_pp"], 0)

    def test_threshold_selection_uses_candidate_scores_and_constraints(self):
        runs = annotate_prior_run_state(sample_runs())
        scores = np.array([0.0, -1.0, 1.0, 0.5])
        constraints = {
            "overall_tail_units_retained": 1.0,
            "overall_tail_journey_runs_retained": 1.0,
            "overall_funded_children_retained": 0.5,
            "after_stop_candidate_runs_retained": 0.0,
        }
        threshold, records = choose_train_threshold(runs, scores, constraints)
        mask = policy_mask(runs, scores, threshold)
        self.assertFalse(mask[1])
        self.assertTrue(mask[2])
        self.assertTrue(records)


if __name__ == "__main__":
    unittest.main()
