"""Small deterministic HA-8B causal/preprocessing regression checks."""

import csv
import io
import unittest
from collections import deque
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import ha8b_child_economic_model as m


class HA8BChecks(unittest.TestCase):
    def test_range_scale_uses_previous_twenty_only(self):
        start = datetime(2022, 1, 3)
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter="\t")
        writer.writerow(("<DATE>", "<TIME>", "<HIGH>", "<LOW>"))
        for i in range(22):
            when = start + timedelta(hours=4 * i)
            writer.writerow((when.strftime("%Y.%m.%d"), when.strftime("%H:%M:%S"),
                             100 if i == 20 else i + 1, 0))
        buf.seek(0)
        reader = csv.DictReader(buf, delimiter="\t")
        ranges = deque(maxlen=20)
        with self.assertRaisesRegex(ValueError, "missing causal prior-20"):
            m.preceding_range_at_signal(reader, ranges, start)
        # The first call consumed the first bar. Continue sequentially.
        for i in range(1, 20):
            with self.assertRaisesRegex(ValueError, "missing causal prior-20"):
                m.preceding_range_at_signal(reader, ranges, start + timedelta(hours=4*i))
        self.assertAlmostEqual(m.preceding_range_at_signal(reader, ranges, start + timedelta(hours=80)), 10.5)
        self.assertAlmostEqual(m.preceding_range_at_signal(reader, ranges, start + timedelta(hours=84)), 11.5)

    def test_preprocessing_fits_past_rows_only(self):
        train = pd.DataFrame({"journey_bar": [1, 3], "side": ["1", "-1"]})
        test = pd.DataFrame({"journey_bar": [100], "side": ["unknown"]})
        x_train, x_test = m.prep(train, test, ("journey_bar",), ("side",))
        self.assertEqual(x_train.shape[1], x_test.shape[1])
        self.assertGreater(x_test[0, 0], 90)
        self.assertTrue(np.isfinite(x_test).all())

    def test_model_whitelist_excludes_outcomes_and_absolute_price(self):
        allowed = {field for numeric, categorical in m.SPECS.values() for field in numeric + categorical}
        forbidden = {"audit_execution_open", "range20", "journey", "year", "exit_known_at",
                     "child_pnl_points", "child_pnl_ranges", "tail_journey"}
        self.assertFalse(allowed & forbidden)

    def test_stage_mean_keeps_birth_and_addon_separate(self):
        train = pd.DataFrame({"journey_bar": [1, 1, 2, 2], "child_pnl_ranges": [-1., 2., -3., 4.]})
        test = pd.DataFrame({"journey_bar": [1, 4]})
        p, plus, minus = m.stage_mean(train, test)
        np.testing.assert_allclose(p, [0.5, 0.5])
        np.testing.assert_allclose(plus, [2., 4.])
        np.testing.assert_allclose(minus, [1., 3.])


if __name__ == "__main__":
    unittest.main()
