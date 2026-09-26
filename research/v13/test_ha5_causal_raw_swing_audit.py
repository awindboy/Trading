"""Small causal-state regression tests; not economic strategy tests."""

import unittest
from datetime import datetime

from ha5_causal_raw_swing_audit import Bar, Pivot, interaction


class InteractionTests(unittest.TestCase):
    def setUp(self):
        self.origin = datetime(2025, 1, 1)
        self.level = Pivot(100.0, self.origin, datetime(2025, 1, 2), 1)

    def bar(self, high, low, close):
        t = datetime(2025, 1, 3)
        return Bar(t, t, 100.0, high, low, close)

    def test_favorable_states(self):
        self.assertEqual(interaction(self.bar(99, 97, 98), self.level, 1,
                                     98, self.origin)[0], "no_break")
        self.assertEqual(interaction(self.bar(101, 97, 99), self.level, 1,
                                     98, self.origin)[0], "probe_rejected")
        self.assertEqual(interaction(self.bar(102, 97, 101), self.level, 1,
                                     98, self.origin)[0], "fresh_close_beyond")
        self.assertEqual(interaction(self.bar(102, 97, 101), self.level, 1,
                                     101, self.origin)[0], "held_close_beyond")
        self.assertEqual(interaction(self.bar(102, 97, 99), self.level, 1,
                                     101, self.origin)[0], "return_inside")

    def test_changed_level_is_never_held_or_return(self):
        other_origin = datetime(2024, 12, 1)
        self.assertEqual(interaction(self.bar(102, 97, 101), self.level, 1,
                                     101, other_origin)[0], "fresh_close_beyond")
        self.assertEqual(interaction(self.bar(102, 97, 99), self.level, 1,
                                     101, other_origin)[0], "probe_rejected")

    def test_short_mirrors_long_and_touch_is_not_break(self):
        self.assertEqual(interaction(self.bar(103, 100, 100), self.level, -1,
                                     101, self.origin)[0], "no_break")
        self.assertEqual(interaction(self.bar(103, 99, 101), self.level, -1,
                                     101, self.origin)[0], "probe_rejected")
        self.assertEqual(interaction(self.bar(103, 98, 99), self.level, -1,
                                     101, self.origin)[0], "fresh_close_beyond")
        self.assertEqual(interaction(self.bar(103, 98, 101), self.level, -1,
                                     99, self.origin)[0], "return_inside")

    def test_no_level(self):
        self.assertEqual(interaction(self.bar(103, 97, 101), None, 1,
                                     None, None), ("no_level", False))


if __name__ == "__main__":
    unittest.main()
