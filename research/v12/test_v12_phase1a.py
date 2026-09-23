#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from v12_phase0_core import M1Row
from v12_phase1a_core import (
    ChildSpec,
    ExecutionBar,
    score_outcomes,
    select_model1_trigger,
    simulate_children,
    stable_child_id,
    next_completed_parent_bar,
)


def execution_bar(hour: int, open_: float, high: float, low: float, close: float, atr: float = 10.0) -> ExecutionBar:
    start = datetime(2026, 1, 2, hour)
    return ExecutionBar("H1", start, start + timedelta(hours=1), open_, high, low, close, atr)


def child_spec(
    *,
    direction: str = "LONG",
    decision_minute: int = 0,
    expiry_minute: int = 10,
    stop: float = 90.0,
    target1: float = 110.0,
    target2: float = 120.0,
    suffix: str = "a",
) -> ChildSpec:
    start = datetime(2026, 1, 3, 0, 0)
    return ChildSpec(
        child_id=f"child-{suffix}",
        parent_id="parent-1",
        lane="D1_TO_H1",
        interaction="LOW_SWEEP_RETURN" if direction == "LONG" else "HIGH_SWEEP_RETURN",
        direction=direction,
        family="MODEL1_RELATIVE_THICK_V1",
        risk_variant="C2_EXTREME",
        watch_start=start,
        parent_sweep_time=start,
        target_guard_start=start,
        stop_guard_start=start,
        decision_time=start + timedelta(minutes=decision_minute),
        expiry_time=start + timedelta(minutes=expiry_minute),
        stop_price=stop,
        target1_price=target1,
        target2_price=target2,
        c1_high=120.0,
        c1_low=80.0,
        c2_high=105.0,
        c2_low=89.99,
        trigger_open_time=None,
        trigger_close_time=None,
        trigger_open=None,
        trigger_high=None,
        trigger_low=None,
        trigger_close=None,
        trigger_body_atr=None,
        trigger_body_ratio=None,
        trigger_sweep_depth=None,
        trigger_eligible_count=0,
        confirmation_time=None,
        confirmation_phase="TEST",
    )


class TriggerTests(unittest.TestCase):
    def test_relative_thick_ranking_and_confirmation(self) -> None:
        bars = [
            execution_bar(0, 108, 112, 107, 111),  # body/ATR 0.3
            execution_bar(1, 106, 111, 100, 110),  # body/ATR 0.4 -> selected
            execution_bar(2, 109, 109, 98, 99),    # closes below selected low
        ]
        selected, status, count = select_model1_trigger(
            direction="SHORT",
            c1_high=110,
            c1_low=90,
            c2_open_time=datetime(2026, 1, 2, 0),
            c2_close_time=datetime(2026, 1, 2, 4),
            c3_close_time=datetime(2026, 1, 3, 0),
            execution_bars=bars,
        )
        self.assertEqual(status, "MODEL1_SELECTED")
        self.assertEqual(count, 2)
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected.trigger.open_time.hour, 1)
        self.assertEqual(selected.confirmation.open_time.hour, 2)
        self.assertEqual(selected.confirmation_phase, "PRECONFIRMED_INSIDE_C2")

    def test_wrong_color_sweep_is_not_trigger(self) -> None:
        bars = [execution_bar(0, 112, 113, 105, 106)]
        selected, status, count = select_model1_trigger(
            direction="SHORT",
            c1_high=110,
            c1_low=90,
            c2_open_time=datetime(2026, 1, 2),
            c2_close_time=datetime(2026, 1, 2, 4),
            c3_close_time=datetime(2026, 1, 3),
            execution_bars=bars,
        )
        self.assertIsNone(selected)
        self.assertEqual(status, "NO_SWEEP_DIRECTION_BODY_CANDLE")
        self.assertEqual(count, 0)


class SimulationTests(unittest.TestCase):
    def test_midpoint_target_then_opposite_path_stop(self) -> None:
        spec = child_spec()
        rows = [
            M1Row(datetime(2026, 1, 3, 0, 0), 100, 111, 99, 108, 1, 0, 1),
            M1Row(datetime(2026, 1, 3, 0, 1), 108, 109, 89, 90, 1, 0, 1),
        ]
        outcome = simulate_children(rows, [spec])[0]
        self.assertEqual(outcome["execution_state"], "FILLED")
        self.assertEqual(outcome["t1_state"], "TARGET1")
        self.assertAlmostEqual(outcome["t1_r"], 1.0)
        self.assertEqual(outcome["t2_state"], "STOPPED")
        self.assertAlmostEqual(outcome["t2_r"], -1.0)

    def test_same_m1_stop_and_target_is_ambiguous(self) -> None:
        spec = child_spec()
        rows = [M1Row(datetime(2026, 1, 3, 0, 0), 100, 111, 89, 100, 1, 0, 1)]
        outcome = simulate_children(rows, [spec])[0]
        self.assertEqual(outcome["t1_state"], "AMBIGUOUS")
        self.assertIsNone(outcome["t1_r"])
        self.assertEqual(outcome["ordering_precision"], "AMBIGUOUS")

    def test_preentry_target_consumption_prevents_fill(self) -> None:
        spec = child_spec(decision_minute=2)
        rows = [
            M1Row(datetime(2026, 1, 3, 0, 0), 100, 105, 99, 104, 1, 0, 1),
            M1Row(datetime(2026, 1, 3, 0, 1), 104, 111, 103, 108, 1, 0, 1),
            M1Row(datetime(2026, 1, 3, 0, 2), 100, 101, 99, 100, 1, 0, 1),
        ]
        outcome = simulate_children(rows, [spec])[0]
        self.assertEqual(outcome["execution_state"], "NO_EXECUTION")
        self.assertEqual(outcome["no_execution_reason"], "PREENTRY_TARGET1_CONSUMED")

    def test_carried_trade_adverse_gap_uses_open(self) -> None:
        spec = child_spec(expiry_minute=10)
        rows = [
            M1Row(datetime(2026, 1, 3, 0, 0), 100, 105, 99, 104, 1, 0, 1),
            M1Row(datetime(2026, 1, 3, 0, 1), 88, 89, 87, 88, 1, 0, 1),
        ]
        outcome = simulate_children(rows, [spec])[0]
        self.assertEqual(outcome["t1_state"], "STOPPED_GAP")
        self.assertAlmostEqual(outcome["t1_r"], -1.2)
        self.assertTrue(outcome["gap_stop"])

    def test_scorecard_counts_exposure_and_stops(self) -> None:
        specs = [child_spec(suffix="a"), child_spec(suffix="b", stop=95, target1=105, target2=110)]
        rows = [M1Row(datetime(2026, 1, 3, 0, 0), 100, 111, 89, 100, 1, 0, 1)]
        outcomes = simulate_children(rows, specs)
        score = score_outcomes(outcomes, 1)
        self.assertEqual(score["filled_children"], 2)
        self.assertEqual(score["ambiguous_children"], 2)


class IdentityTests(unittest.TestCase):
    def test_child_id_is_stable_and_variant_sensitive(self) -> None:
        first = stable_child_id("parent", "FAMILY", "A")
        self.assertEqual(first, stable_child_id("parent", "FAMILY", "A"))
        self.assertNotEqual(first, stable_child_id("parent", "FAMILY", "B"))

    def test_next_completed_parent_skips_weekend_clock_gap(self) -> None:
        friday = ExecutionBar(
            "D1",
            datetime(2026, 1, 2),
            datetime(2026, 1, 3),
            100,
            101,
            99,
            100,
            10,
        )
        monday = ExecutionBar(
            "D1",
            datetime(2026, 1, 5),
            datetime(2026, 1, 6),
            100,
            102,
            98,
            101,
            10,
        )
        self.assertIs(next_completed_parent_bar([friday, monday], friday.open_time), monday)


if __name__ == "__main__":
    unittest.main()
