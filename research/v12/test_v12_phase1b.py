from __future__ import annotations

from datetime import datetime, timedelta
import unittest

from v12_phase0_core import CompletedBar, M1Row
from v12_phase1b_core import (
    LiquidityBook,
    activation_id,
    build_journey_state,
    compute_ha_states,
    journey_at,
    make_level,
    milestone_stage,
)


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2025, 1, 6, hour, minute)


def m1(timestamp: datetime, high: float, low: float) -> M1Row:
    return M1Row(timestamp, 100.0, high, low, 100.0, 1, 0, 1)


def bar(open_time: datetime, completed_by: datetime, open_: float = 100, high: float = 110, low: float = 90, close: float = 100) -> CompletedBar:
    return CompletedBar(
        timeframe="H4",
        open_time=open_time,
        close_time=open_time + timedelta(hours=4),
        first_m1_time=open_time,
        last_m1_time=open_time + timedelta(hours=3, minutes=59),
        completed_by_observation=completed_by,
        open=open_, high=high, low=low, close=close,
        m1_rows=240, tick_volume=1, volume=0, last_spread=1, max_spread=1,
    )


def activation(name: str, timestamp: datetime, direction: str, interaction: str, c2_open: datetime) -> dict:
    return {
        "activation_id": name,
        "h4_event_id": name,
        "activation_time": timestamp,
        "activation_price": 100.0,
        "direction": direction,
        "interaction": interaction,
        "c1_high": 110.0,
        "c1_low": 90.0,
        "c1_midpoint": 100.0,
        "opposite_edge": 110.0 if direction == "LONG" else 90.0,
        "c2_open_time": c2_open,
        "c2_high": 108.0,
        "c2_low": 92.0,
        "h4_atr180": 10.0,
    }


class LiquidityTests(unittest.TestCase):
    def test_equality_is_touch_not_consumption(self) -> None:
        book = LiquidityBook()
        level = make_level("PREVIOUS_H4", "HIGH", dt(0), 101.0, dt(4))
        book.add(level)
        book.observe(m1(dt(4), 101.0, 99.0))
        self.assertIsNone(level.consumed_at)
        book.observe(m1(dt(4, 1), 101.01, 99.0))
        self.assertEqual(level.consumed_at, dt(4, 1))

    def test_birth_and_gap_breach_same_m1(self) -> None:
        book = LiquidityBook()
        level = make_level("PREVIOUS_DAY", "LOW", dt(0), 99.0, dt(4))
        book.add(level)
        book.observe(m1(dt(4), 102.0, 98.0))
        self.assertEqual(level.consumed_at, dt(4))
        self.assertTrue(level.birth_and_consumption_same_m1)


class JourneyTests(unittest.TestCase):
    def test_same_direction_reinforces_and_latest_boundary_wins(self) -> None:
        first = activation("a", dt(4), "LONG", "LOW_SWEEP_RETURN", dt(0))
        second = activation("b", dt(4), "LONG", "HIGH_OUTSIDE_ACCEPTANCE", dt(1))
        journeys, decisions = build_journey_state([second, first], [], dt(20))
        self.assertEqual(len(journeys), 1)
        self.assertEqual(journeys[0].origin["activation_id"], "a")
        self.assertEqual(journeys[0].boundary["activation_id"], "b")
        self.assertEqual([row["state_action"] for row in decisions], ["START", "REINFORCEMENT"])

    def test_opposite_activation_replaces(self) -> None:
        first = activation("a", dt(4), "LONG", "LOW_SWEEP_RETURN", dt(0))
        second = activation("b", dt(8), "SHORT", "HIGH_SWEEP_RETURN", dt(4))
        journeys, _ = build_journey_state([first, second], [], dt(20))
        self.assertEqual(journeys[0].end_reason, "OPPOSITE_ACTIVATION")
        self.assertEqual(journeys[0].end_time, dt(8))
        self.assertEqual(journeys[1].direction, "SHORT")

    def test_conflict_ends_current_and_stays_neutral(self) -> None:
        first = activation("a", dt(4), "LONG", "LOW_SWEEP_RETURN", dt(0))
        long = activation("b", dt(8), "LONG", "LOW_SWEEP_RETURN", dt(4))
        short = activation("c", dt(8), "SHORT", "HIGH_SWEEP_RETURN", dt(5))
        journeys, decisions = build_journey_state([first, long, short], [], dt(20))
        self.assertEqual(len(journeys), 1)
        self.assertEqual(journeys[0].end_reason, "SIMULTANEOUS_CONFLICT")
        self.assertIsNone(journey_at(journeys, dt(9)))
        self.assertEqual([row["state_action"] for row in decisions[-2:]], ["CONFLICT_NO_START", "CONFLICT_NO_START"])

    def test_failure_is_resolved_before_same_timestamp_activation(self) -> None:
        first = activation("a", dt(4), "LONG", "LOW_SWEEP_RETURN", dt(0))
        replacement = activation("b", dt(8), "LONG", "HIGH_OUTSIDE_ACCEPTANCE", dt(4))
        failure_bar = bar(dt(4), dt(8), close=91.0)
        journeys, decisions = build_journey_state([first, replacement], [failure_bar], dt(20))
        self.assertEqual(journeys[0].end_reason, "STRUCTURAL_FAILURE")
        self.assertEqual(decisions[-1]["state_action"], "START")
        self.assertNotEqual(journeys[0].journey_id, journeys[1].journey_id)

    def test_cutoff_keeps_open_journey(self) -> None:
        first = activation("a", dt(4), "LONG", "LOW_SWEEP_RETURN", dt(0))
        journeys, _ = build_journey_state([first], [], dt(20))
        self.assertEqual(journeys[0].end_reason, "OPEN_AT_CUTOFF")
        self.assertEqual(journeys[0].end_time, dt(20))

    def test_milestone_already_passed_is_not_future_attainment(self) -> None:
        first = activation("a", dt(4), "LONG", "HIGH_OUTSIDE_ACCEPTANCE", dt(0))
        journeys, _ = build_journey_state([first], [], dt(20))
        outcome = {
            "midpoint_time": None,
            "opposite_edge_time": None,
            "midpoint_forward_eligible": False,
            "opposite_edge_forward_eligible": False,
        }
        self.assertEqual(
            milestone_stage(journeys[0], dt(8), outcome),
            "AFTER_OPPOSITE_EDGE_AT_ACTIVATION",
        )


class HATests(unittest.TestCase):
    def test_fast_std_slow_match_frozen_parameters(self) -> None:
        bars = [bar(dt(0), dt(4), open_=100, high=110, low=90, close=108)]
        row = compute_ha_states(bars)[0]
        self.assertAlmostEqual(row["fast_close"], (100 + 110 + 90 + 2 * 108) / 5)
        self.assertAlmostEqual(row["std_close"], (100 + 110 + 90 + 108) / 4)
        self.assertAlmostEqual(row["slow_close"], row["fast_close"])


if __name__ == "__main__":
    unittest.main()
