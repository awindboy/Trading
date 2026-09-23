#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_v12_phase0 import PrefixAudit, iter_m1_prefix
from v12_phase0_core import (
    CompletedBar,
    M1Row,
    MultiTimeframeAggregator,
    bucket_start,
    build_parent_events,
    classify_c2,
    enrich_extreme_times,
    parent_id,
)


def bar(
    *,
    timeframe: str = "D1",
    start: datetime = datetime(2026, 1, 1),
    open_: float = 100.0,
    high: float = 110.0,
    low: float = 90.0,
    close: float = 100.0,
) -> CompletedBar:
    minutes = 1_440 if timeframe == "D1" else 10_080
    end = start + timedelta(minutes=minutes)
    return CompletedBar(
        timeframe=timeframe,
        open_time=start,
        close_time=end,
        first_m1_time=start,
        last_m1_time=end - timedelta(minutes=1),
        completed_by_observation=end,
        open=open_,
        high=high,
        low=low,
        close=close,
        m1_rows=minutes,
        tick_volume=1,
        volume=0,
        last_spread=1,
        max_spread=1,
        true_range=high - low,
        atr14=20.0,
    )


class BucketTests(unittest.TestCase):
    def test_broker_bucket_boundaries(self) -> None:
        stamp = datetime(2026, 9, 23, 17, 43)
        self.assertEqual(bucket_start(stamp, "M5"), datetime(2026, 9, 23, 17, 40))
        self.assertEqual(bucket_start(stamp, "H4"), datetime(2026, 9, 23, 16, 0))
        self.assertEqual(bucket_start(stamp, "D1"), datetime(2026, 9, 23, 0, 0))
        self.assertEqual(bucket_start(stamp, "W1"), datetime(2026, 9, 20, 0, 0))
        self.assertEqual(bucket_start(datetime(2026, 9, 20, 12), "W1"), datetime(2026, 9, 20))

    def test_stream_excludes_terminal_open_bucket(self) -> None:
        aggregator = MultiTimeframeAggregator(("M5",))
        for minute, close in ((0, 100.0), (1, 101.0), (5, 102.0)):
            timestamp = datetime(2026, 1, 1, 0, minute)
            aggregator.observe(M1Row(timestamp, close, close, close, close, 1, 0, 1))
        self.assertEqual(len(aggregator.completed["M5"]), 1)
        completed = aggregator.completed["M5"][0]
        self.assertEqual(completed.open_time, datetime(2026, 1, 1, 0, 0))
        self.assertEqual(completed.close, 101.0)
        self.assertEqual(aggregator.terminal_buckets()["M5"]["open_time"], "2026-01-01T00:05:00")


class ClassificationTests(unittest.TestCase):
    def test_all_interaction_states(self) -> None:
        c1 = bar()
        cases = [
            ((108.0, 92.0, 100.0), "NO_EXTREME_TRADE", "NONE"),
            ((112.0, 92.0, 108.0), "HIGH_SWEEP_RETURN", "SHORT"),
            ((108.0, 88.0, 92.0), "LOW_SWEEP_RETURN", "LONG"),
            ((112.0, 92.0, 111.0), "HIGH_OUTSIDE_ACCEPTANCE", "LONG"),
            ((108.0, 88.0, 89.0), "LOW_OUTSIDE_ACCEPTANCE", "SHORT"),
            ((112.0, 88.0, 100.0), "DUAL_SWEEP_INSIDE", "NONE"),
            ((112.0, 88.0, 111.0), "DUAL_OR_CONFLICTED", "NONE"),
        ]
        for (high, low, close), expected, direction in cases:
            with self.subTest(expected=expected):
                c2 = bar(start=datetime(2026, 1, 2), high=high, low=low, close=close)
                state = classify_c2(c1, c2)
                self.assertEqual(state["interaction"], expected)
                self.assertEqual(state["direction"], direction)

    def test_point_equality_is_touch_not_breach(self) -> None:
        state = classify_c2(bar(), bar(start=datetime(2026, 1, 2), high=110.0, low=90.0, close=100.0))
        self.assertEqual(state["interaction"], "NO_EXTREME_TRADE")
        self.assertTrue(state["equal_high_touch"])
        self.assertTrue(state["equal_low_touch"])
        self.assertFalse(state["traded_high"])
        self.assertFalse(state["traded_low"])


class ContractTests(unittest.TestCase):
    def test_parent_id_is_stable_and_input_sensitive(self) -> None:
        kwargs = dict(
            symbol="GOLD#",
            lane="D1_TO_H1",
            c1_open=datetime(2026, 1, 1),
            c2_open=datetime(2026, 1, 2),
            broker_clock_spec_sha256="a" * 64,
            source_prefix_sha256="b" * 64,
        )
        first = parent_id(**kwargs)
        self.assertEqual(first, parent_id(**kwargs))
        kwargs["lane"] = "W1_TO_H4"
        self.assertNotEqual(first, parent_id(**kwargs))

    def test_event_universe_contains_no_outcome_record(self) -> None:
        d1 = [bar(start=datetime(2026, 1, 1)), bar(start=datetime(2026, 1, 2), high=112, low=92, close=108)]
        w1 = [
            bar(timeframe="W1", start=datetime(2026, 1, 4)),
            bar(timeframe="W1", start=datetime(2026, 1, 11), high=112, low=92, close=108),
        ]
        decisions, rich = build_parent_events(
            {"D1": d1, "W1": w1},
            symbol="GOLD#",
            source_prefix_sha256="b" * 64,
            broker_clock_spec_sha256="a" * 64,
        )
        self.assertEqual(len(decisions), 2)
        self.assertTrue(all(row["record_type"] == "decision" for row in decisions))
        self.assertTrue(all(row["child_id"] is None for row in decisions))
        self.assertTrue(all(row["outcome_fields_present"] is False for row in rich))

    def test_same_m1_dual_breach_remains_ambiguous(self) -> None:
        c1 = bar()
        c2 = bar(start=datetime(2026, 1, 2), high=112, low=88, close=100)
        _, rich = build_parent_events(
            {"D1": [c1, c2], "W1": []},
            symbol="GOLD#",
            source_prefix_sha256="b" * 64,
            broker_clock_spec_sha256="a" * 64,
        )
        event = rich[0]
        breach = M1Row(datetime(2026, 1, 2, 12), 100, 112, 88, 100, 1, 0, 1)
        enrich_extreme_times([breach], rich)
        self.assertEqual(event["extreme_ordering"], "SAME_M1_AMBIGUOUS")
        self.assertEqual(event["ordering_precision"], "AMBIGUOUS")


class CausalReaderTests(unittest.TestCase):
    def test_post_cutoff_price_fields_are_never_parsed(self) -> None:
        content = (
            "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n"
            "2026.01.01\t00:00:00\t100\t101\t99\t100\t1\t0\t1\n"
            "2026.01.01\t00:01:00\tSECRET\tSECRET\tSECRET\tSECRET\tSECRET\tSECRET\tSECRET\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "m1.csv"
            path.write_text(content, encoding="utf-8")
            audit = PrefixAudit()
            rows = list(iter_m1_prefix(path, datetime(2026, 1, 1, 0, 0), audit=audit))
        self.assertEqual(len(rows), 1)
        self.assertEqual(audit.parsed_price_rows, 1)
        self.assertEqual(audit.post_cutoff_price_rows_parsed, 0)
        self.assertEqual(audit.first_unrevealed_timestamp, datetime(2026, 1, 1, 0, 1))


if __name__ == "__main__":
    unittest.main()
