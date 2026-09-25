import unittest
from datetime import datetime

from v12_phase1l_core import Bar, BarAggregator, HAStream, bucket_start, equal_stop_budget


class Phase1LTests(unittest.TestCase):
    def test_broker_buckets(self):
        value = datetime(2025, 1, 2, 5, 47)
        self.assertEqual(bucket_start(value, 15), datetime(2025, 1, 2, 5, 45))
        self.assertEqual(bucket_start(value, 60), datetime(2025, 1, 2, 5, 0))
        self.assertEqual(bucket_start(value, 240), datetime(2025, 1, 2, 4, 0))

    def test_aggregator_closes_only_on_next_bucket(self):
        agg = BarAggregator(60)
        self.assertIsNone(agg.push(datetime(2025, 1, 1, 1, 0), 1, 2, 0, 1.5))
        done = agg.push(datetime(2025, 1, 1, 2, 0), 2, 3, 1, 2.5)
        self.assertEqual(done.start, datetime(2025, 1, 1, 1, 0))
        self.assertEqual(done.close, 1.5)

    def test_fast_ha_formula(self):
        stream = HAStream(2.0, 0.25)
        first = stream.append(Bar(datetime(2025, 1, 1), 10, 14, 8, 12))
        self.assertAlmostEqual(first.ha_close, 11.2)
        self.assertAlmostEqual(first.ha_open, 11.0)

    def test_equal_stop_budget_matches_total_stopped_units(self):
        baseline = {"children": 100.0, "stopped_units": 20.0, "net_R": 10.0}
        candidate = {"children": 400.0, "stopped_units": 80.0, "net_R": 24.0}
        scale, net_per_baseline_unit = equal_stop_budget(candidate, baseline)
        self.assertAlmostEqual(scale, 0.25)
        self.assertAlmostEqual(net_per_baseline_unit, 0.06)


if __name__ == "__main__":
    unittest.main()
