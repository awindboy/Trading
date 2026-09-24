#!/usr/bin/env python3

import unittest
from datetime import datetime

from v12_phase1f_core import Level, advance_frontier, choose_external_cluster, state_at


class Phase1FTargetTests(unittest.TestCase):
    def test_external_cluster_has_no_family_priority(self):
        now = datetime(2025, 1, 2, 8)
        levels = [
            Level("h4", "PREVIOUS_H4", "HIGH", 101.0, now, None),
            Level("week", "PREVIOUS_WEEK", "HIGH", 101.0, now, None),
            Level("day", "PREVIOUS_DAY", "HIGH", 102.0, now, None),
        ]
        selected = choose_external_cluster(levels, "LONG", now, 100.0)
        self.assertEqual({row.level_id for row in selected}, {"h4", "week"})

    def test_consumed_same_m1_is_still_visible_at_open(self):
        now = datetime(2025, 1, 2, 8)
        level = Level("h4", "PREVIOUS_H4", "HIGH", 101.0, now, now)
        self.assertEqual(choose_external_cluster([level], "LONG", now, 100.0)[0].level_id, "h4")

    def test_frontier_never_reverses(self):
        self.assertEqual(advance_frontier("LONG", 105.0, 101.0), 105.0)
        self.assertEqual(advance_frontier("SHORT", 95.0, 99.0), 95.0)

    def test_target_completion_equal_query_remains_unfinished(self):
        journey = {
            "start_time": "2025-01-02T08:00:00",
            "end_time": "2025-01-03T08:00:00",
        }
        targets = [{
            "target_id": "t1",
            "selected_at": "2025-01-02T08:00:00",
            "completed_at": "2025-01-02T12:00:00",
            "target_kind": "EXTERNAL_ONE_USE_CLUSTER",
            "target_price": 101.0,
            "member_families": "PREVIOUS_H4",
            "distance_atr180": 1.0,
        }]
        self.assertEqual(state_at(journey, targets, datetime(2025, 1, 2, 12))["target_state"], "TARGET_UNFINISHED")
        self.assertEqual(state_at(journey, targets, datetime(2025, 1, 2, 12, 1))["target_state"], "TARGET_COMPLETE_REFRAME_PENDING")

    def test_parent_end_is_exclusive(self):
        journey = {
            "start_time": "2025-01-02T08:00:00",
            "end_time": "2025-01-02T12:00:00",
        }
        self.assertEqual(state_at(journey, [], datetime(2025, 1, 2, 12))["target_state"], "PARENT_INVALIDATED")


if __name__ == "__main__":
    unittest.main()
