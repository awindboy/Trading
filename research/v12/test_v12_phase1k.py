import unittest

import pandas as pd

from v12_phase1k_core import admit_child


class Phase1KTests(unittest.TestCase):
    def test_first_child_is_always_retained(self):
        time = pd.Timestamp("2025-01-01 12:00")
        for policy in ("PROGRESSION_RELEASE", "DAMAGE_STOP", "PROGRESSION_OR_REPAIRED_DEPARTURE", "FIRST_CHILD_ONLY"):
            self.assertTrue(admit_child(policy, 1, time, None, time, None))

    def test_progression_must_be_known(self):
        entry = pd.Timestamp("2025-01-01 12:00")
        self.assertTrue(admit_child("PROGRESSION_RELEASE", 2, entry, entry, None, None))
        self.assertFalse(admit_child("PROGRESSION_RELEASE", 2, entry, entry + pd.Timedelta(minutes=15), None, None))

    def test_damage_stops_only_after_known_event(self):
        entry = pd.Timestamp("2025-01-01 12:00")
        self.assertTrue(admit_child("DAMAGE_STOP", 2, entry, None, entry + pd.Timedelta(minutes=15), None))
        self.assertFalse(admit_child("DAMAGE_STOP", 2, entry, None, entry, None))


if __name__ == "__main__":
    unittest.main()
