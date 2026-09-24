#!/usr/bin/env python3

import unittest
from datetime import datetime

from build_v12_phase1e import collapse_event_state, session_context


class Phase1ESessionTests(unittest.TestCase):
    def test_fixed_server_clock_maps_core_sessions(self):
        self.assertEqual(session_context(datetime(2025, 1, 6, 1))["session_phase"], "OFF_CORE")
        self.assertEqual(session_context(datetime(2025, 1, 6, 5))["session_phase"], "ASIA_ONLY")
        self.assertEqual(session_context(datetime(2025, 1, 6, 13))["session_phase"], "LONDON_PRE_NY")
        self.assertEqual(session_context(datetime(2025, 1, 6, 17))["session_phase"], "LONDON_NY_OVERLAP")
        self.assertEqual(session_context(datetime(2025, 1, 6, 21))["session_phase"], "NY_AFTER_LONDON")

    def test_new_york_weekday_crosses_server_midnight(self):
        context = session_context(datetime(2025, 1, 6, 1))
        self.assertEqual(context["broker_weekday"], "MON")
        self.assertEqual(context["new_york_weekday"], "SUN")

    def test_event_state_collapse_is_frozen(self):
        self.assertEqual(collapse_event_state("PRE_30_60"), "PRE_30_60")
        self.assertEqual(collapse_event_state("POST_15_30"), "POST_0_60")
        self.assertEqual(collapse_event_state("FAR_GT_240"), "OTHER")


if __name__ == "__main__":
    unittest.main()
