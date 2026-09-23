from __future__ import annotations

from datetime import datetime
import unittest

from v12_phase1c_core import (
    GuardSpec,
    carry_is_eligible,
    maximum_concurrent_units,
    realized_r,
    repair_is_confirmed,
    stop_touched,
    target_open_at,
)


class Phase1CCoreTests(unittest.TestCase):
    def test_target_touch_same_m1_is_not_preknown(self) -> None:
        row = {"opposite_edge_forward_eligible": "True", "opposite_edge_time": "2026-01-01T08:00:00"}
        self.assertTrue(target_open_at(row, datetime.fromisoformat("2026-01-01T08:00:00")))
        self.assertFalse(target_open_at(row, datetime.fromisoformat("2026-01-01T08:01:00")))

    def test_carry_requires_same_active_parent(self) -> None:
        context = {"relation": "ALIGNED_ACTIVE_JOURNEY", "journey_id": "j1", "direction": "LONG"}
        child = {"exit_reason": "FAST_NHA"}
        flip = {
            "explanation_state": "OLD_JOURNEY_COUNTERFLOW",
            "active_journey_id": "j1",
            "old_fast_direction": "LONG",
        }
        self.assertTrue(carry_is_eligible(context, child, flip))
        flip["active_journey_id"] = "j2"
        self.assertFalse(carry_is_eligible(context, child, flip))

    def test_repair_must_return_to_same_parent(self) -> None:
        start = {"old_fast_direction": "SHORT"}
        repair = {"new_fast_direction": "SHORT", "active_journey_id": "j1"}
        self.assertTrue(repair_is_confirmed(start, repair, "j1"))
        repair["active_journey_id"] = "j2"
        self.assertFalse(repair_is_confirmed(start, repair, "j1"))

    def test_long_and_short_stop_and_r(self) -> None:
        long = GuardSpec("a", "CARRY", 1, 100.0, 90.0, datetime.min, datetime.max, False, "j", "b", True)
        short = GuardSpec("b", "CARRY", -1, 100.0, 110.0, datetime.min, datetime.max, False, "j", "b", True)
        self.assertTrue(stop_touched(long, 101.0, 89.0))
        self.assertTrue(stop_touched(short, 111.0, 99.0))
        self.assertEqual(realized_r(long, 120.0), 2.0)
        self.assertEqual(realized_r(short, 80.0), 2.0)

    def test_concurrency_exit_then_entry(self) -> None:
        rows = [
            {"entry_time": "2026-01-01T00:00:00", "exit_time": "2026-01-01T04:00:00", "funded_units": 1},
            {"entry_time": "2026-01-01T04:00:00", "exit_time": "2026-01-01T08:00:00", "funded_units": 3},
        ]
        self.assertEqual(maximum_concurrent_units(rows), 3.0)


if __name__ == "__main__":
    unittest.main()
