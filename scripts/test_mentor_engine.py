from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from mentor_engine.casebook import validate_casebook
from mentor_engine.engine import (
    MentorScenarioEngine,
    correction_leg_matches,
    protective_stop,
)
from mentor_engine.execution import simulate_order
from mentor_engine.liquidity import _detect_sweeps
from mentor_engine.models import (
    BarSeries,
    Direction,
    EngineConfig,
    LiquidityKind,
    LiquidityPool,
    OrderPlan,
    Side,
    Zone,
    ZoneKind,
    StructureAnalysis,
    StructureEvent,
)
from mentor_engine.planner import DestinationPlanner
from mentor_engine.structure import analyze_structure
from mentor_engine.zones import detect_zones


def bars(rows: list[tuple[float, float, float, float]]) -> BarSeries:
    size = len(rows)
    time = np.arange(size, dtype=np.int64) * 60 + 1_700_000_000
    return BarSeries(
        timeframe="M1",
        seconds=60,
        time=time,
        available_time=time + 60,
        open=np.array([row[0] for row in rows], dtype=float),
        high=np.array([row[1] for row in rows], dtype=float),
        low=np.array([row[2] for row in rows], dtype=float),
        close=np.array([row[3] for row in rows], dtype=float),
        spread_points=np.ones(size, dtype=float),
    )


class MentorEngineTests(unittest.TestCase):
    def test_execution_timeframe_is_m1_only(self) -> None:
        self.assertEqual(EngineConfig().trigger_timeframes, ("M1",))
        self.assertEqual(EngineConfig().map_timeframes, ("H1", "M30"))
        self.assertEqual(
            EngineConfig().context_timeframes,
            ("H1", "M30", "M15", "M5"),
        )

    def test_three_opposite_candles_confirm_wave(self) -> None:
        series = bars(
            [
                (10, 11.2, 9.8, 11),
                (11, 12.2, 10.8, 12),
                (12, 13.2, 11.8, 13),
                (13, 14.2, 12.8, 14),
                (14, 14.1, 12.8, 13),
                (13, 13.1, 11.8, 12),
                (12, 12.1, 10.8, 11),
            ]
        )
        analysis = analyze_structure(series)
        highs = [wave for wave in analysis.waves if wave.side == Side.HIGH]
        self.assertEqual(len(highs), 1)
        self.assertEqual(highs[0].confirmed_index, 6)
        self.assertEqual(highs[0].level, 14.2)

    def test_doji_interrupts_wave_confirmation(self) -> None:
        series = bars(
            [
                (10, 11.2, 9.8, 11),
                (11, 12.2, 10.8, 12),
                (12, 13.2, 11.8, 13),
                (13, 13.1, 11.8, 12),
                (12, 12.1, 11.8, 12),
                (12, 12.1, 10.8, 11),
            ]
        )
        highs = [
            wave
            for wave in analyze_structure(series).waves
            if wave.side == Side.HIGH
        ]
        self.assertFalse(highs)

    def test_wick_breach_is_sweep_body_break_is_not(self) -> None:
        series = bars(
            [
                (9.5, 9.8, 9.2, 9.6),
                (9.6, 10.4, 9.4, 9.8),
                (9.8, 10.5, 9.7, 10.2),
            ]
        )
        pool = LiquidityPool(
            object_id="pool",
            timeframe="M1",
            kind=LiquidityKind.EXTERNAL_SWING,
            side=Side.HIGH,
            created_index=0,
            occurred_at=int(series.time[0]),
            available_at=int(series.available_time[0]),
            bottom=9.9,
            top=10.0,
            source_wave_ids=["wave"],
        )
        sweeps = _detect_sweeps(series, [pool])
        self.assertEqual(len(sweeps), 1)
        self.assertEqual(sweeps[0].index, 1)

    def test_fvg_and_two_ob_definitions_are_preserved(self) -> None:
        series = bars(
            [
                (10.0, 10.2, 9.8, 9.9),
                (10.0, 11.2, 9.95, 11.0),
                (10.8, 11.6, 10.5, 11.4),
                (11.4, 11.7, 10.7, 11.0),
            ]
        )
        structure = analyze_structure(series)
        zones = detect_zones(series, structure)
        kinds = {zone.kind.value for zone in zones}
        self.assertIn("FVG", kinds)
        self.assertIn("FVG_ORIGIN_OB", kinds)
        self.assertIn("LAST_OPPOSITE_OB", kinds)

    def test_fvg_partial_fill_shrinks_then_full_fill_retires(self) -> None:
        series = bars(
            [
                (10.0, 10.2, 9.8, 10.1),
                (10.1, 10.8, 10.0, 10.7),
                (10.7, 11.0, 10.5, 10.9),
                (10.9, 11.0, 10.35, 10.5),
                (10.5, 10.6, 10.1, 10.2),
            ]
        )
        zones = detect_zones(series, analyze_structure(series))
        target = next(
            zone
            for zone in zones
            if zone.kind == ZoneKind.FVG
            and zone.direction == Direction.LONG
            and zone.bottom == 10.2
            and zone.top == 10.5
        )
        self.assertEqual(
            target.bounds_at(int(series.available_time[3])),
            (10.2, 10.35),
        )
        self.assertEqual(target.consumed_at, int(series.available_time[4]))
        self.assertFalse(target.active_at(int(series.available_time[4])))

    def test_fvg_is_linked_to_later_break_in_same_displacement_leg(self) -> None:
        series = bars(
            [
                (10.0, 10.2, 9.8, 10.0),
                (10.0, 10.9, 9.9, 10.8),
                (10.8, 11.3, 10.5, 11.1),
                (11.1, 11.6, 10.9, 11.5),
                (11.5, 12.1, 11.3, 12.0),
            ]
        )
        event = StructureEvent(
            event_id="M1:delayed-bos",
            timeframe="M1",
            index=4,
            occurred_at=int(series.time[4]),
            available_at=int(series.available_time[4]),
            direction=Direction.LONG,
            event_type="BOS",
            broken_swing_id="high",
            broken_level=11.8,
            protected_swing_id="low",
            protected_level=9.8,
            range_low=9.8,
            range_high=12.1,
        )
        structure = StructureAnalysis(
            timeframe="M1",
            waves=[],
            events=[event],
            trend=np.ones(len(series), dtype=np.int8),
            protected_high=np.full(len(series), np.nan),
            protected_low=np.full(len(series), 9.8),
            range_low=np.full(len(series), 9.8),
            range_high=np.full(len(series), 12.1),
        )
        fvg = next(
            zone
            for zone in detect_zones(series, structure)
            if zone.kind == ZoneKind.FVG and zone.origin_index == 0
        )
        self.assertEqual(fvg.linked_structure_event_id, event.event_id)

    def test_casebook_explicit_contract_is_complete(self) -> None:
        result = validate_casebook("research/mentor-youtube/MENTOR_CASEBOOK.json")
        self.assertTrue(result["semanticPassed"])
        self.assertFalse(result["protocolPassed"])
        self.assertEqual(result["semanticCoverage"], 1.0)
        self.assertIsNone(result["replayParity"])

    def test_trigger_family_distal_is_included_in_stop(self) -> None:
        self.assertEqual(
            protective_stop(Direction.LONG, 99.0, 100.0, 101.0, 97.0, 103.0, 0.5),
            96.5,
        )

    def test_first_entry_uses_choch_ob_not_fvg(self) -> None:
        series = bars([(10.0, 10.5, 9.5, 10.2)])
        event = StructureEvent(
            event_id="M1:choch",
            timeframe="M1",
            index=0,
            occurred_at=int(series.time[0]),
            available_at=int(series.available_time[0]),
            direction=Direction.LONG,
            event_type="CHOCH",
            broken_swing_id="high",
            broken_level=10.4,
            protected_swing_id="low",
            protected_level=9.5,
            range_low=9.5,
            range_high=10.5,
        )
        family_id = "M1:family:choch"
        zones = [
            Zone(
                object_id="fvg",
                family_id=family_id,
                timeframe="M1",
                kind=ZoneKind.FVG,
                direction=Direction.LONG,
                origin_index=0,
                confirmed_index=0,
                occurred_at=int(series.time[0]),
                available_at=int(series.available_time[0]),
                bottom=10.0,
                top=10.2,
                linked_structure_event_id=event.event_id,
            ),
            Zone(
                object_id="ob",
                family_id=family_id,
                timeframe="M1",
                kind=ZoneKind.LAST_OPPOSITE_OB,
                direction=Direction.LONG,
                origin_index=0,
                confirmed_index=0,
                occurred_at=int(series.time[0]),
                available_at=int(series.available_time[0]),
                bottom=9.6,
                top=9.9,
                linked_structure_event_id=event.event_id,
            ),
        ]
        engine = MentorScenarioEngine(series)
        engine.states["M1"] = SimpleNamespace(zones=zones)
        selected = engine._linked_entry_family(event)
        self.assertIsNotNone(selected)
        self.assertEqual(selected[0].kind, ZoneKind.LAST_OPPOSITE_OB)
        self.assertEqual([item.object_id for item in selected[1]], ["ob"])

    def test_pending_cancellation_has_terminal_time(self) -> None:
        series = bars(
            [
                (10.0, 10.3, 9.8, 10.1),
                (10.1, 11.2, 10.0, 11.0),
            ]
        )
        entry_zone = Zone(
            object_id="entry-ob",
            family_id="entry-family",
            timeframe="M1",
            kind=ZoneKind.LAST_OPPOSITE_OB,
            direction=Direction.LONG,
            origin_index=0,
            confirmed_index=0,
            occurred_at=int(series.time[0]),
            available_at=int(series.available_time[0]),
            bottom=9.7,
            top=9.9,
        )
        plan = OrderPlan(
            order_id="order",
            scenario_id="scenario",
            direction=Direction.LONG,
            created_at=int(series.available_time[0]),
            entry=9.9,
            stop_loss=9.5,
            take_profit=11.0,
            entry_zone_id=entry_zone.object_id,
            entry_zone_bottom=entry_zone.bottom,
            entry_zone_top=entry_zone.top,
            source_sweep_extreme=9.6,
            spread_price=0.01,
            map_timeframe="H1",
            context_timeframe="M5",
            trigger_timeframe="M1",
            objective_id="objective",
            cancel_structure_level=9.4,
            protective_zone_bottom=9.7,
            protective_zone_top=9.9,
        )
        result = simulate_order(series, plan, entry_zone, 0.01, None)
        self.assertEqual(result.result, "CANCELLED_OBJECTIVE_DELIVERED")
        self.assertEqual(result.exit_time, int(series.available_time[1]))

    def test_m5_internal_correction_is_separate_from_external_trend(self) -> None:
        self.assertTrue(correction_leg_matches(Direction.LONG, Side.HIGH))
        self.assertTrue(correction_leg_matches(Direction.SHORT, Side.LOW))
        self.assertFalse(correction_leg_matches(Direction.LONG, Side.LOW))
        self.assertEqual(
            protective_stop(Direction.SHORT, 101.0, 99.0, 100.0, 97.0, 104.0, 0.5),
            104.5,
        )

    def test_nearest_complete_destination_owns_the_map(self) -> None:
        def state(timeframe: str, trend: int, direction: Direction) -> SimpleNamespace:
            series = BarSeries(
                timeframe=timeframe,
                seconds=60,
                time=np.array([1_700_000_000], dtype=np.int64),
                available_time=np.array([1_700_000_060], dtype=np.int64),
                open=np.array([100.0]),
                high=np.array([110.0]),
                low=np.array([90.0]),
                close=np.array([100.0]),
                spread_points=np.array([1.0]),
            )
            event = StructureEvent(
                event_id=f"{timeframe}:owner",
                timeframe=timeframe,
                index=0,
                occurred_at=1_700_000_000,
                available_at=1_700_000_060,
                direction=direction,
                event_type="BOS",
                broken_swing_id="broken",
                broken_level=100.0,
                protected_swing_id="protected",
                protected_level=90.0,
                range_low=90.0,
                range_high=110.0,
            )
            structure = StructureAnalysis(
                timeframe=timeframe,
                waves=[],
                events=[event],
                trend=np.array([trend], dtype=np.int8),
                protected_high=np.array([109.0]),
                protected_low=np.array([91.0]),
                range_low=np.array([90.0]),
                range_high=np.array([110.0]),
            )
            target = LiquidityPool(
                object_id=f"{timeframe}:target",
                timeframe=timeframe,
                kind=LiquidityKind.EXTERNAL_SWING,
                side=Side.HIGH,
                created_index=0,
                occurred_at=1_700_000_000,
                available_at=1_700_000_060,
                bottom=107.9 if timeframe == "H4" else 101.9,
                top=108.0 if timeframe == "H4" else 102.0,
                source_wave_ids=[f"{timeframe}:wave"],
            )
            return SimpleNamespace(
                series=series,
                structure=structure,
                zones=[],
                liquidity=[target] if timeframe in {"H4", "M30"} else [],
                sweeps=[],
            )

        states = {
            "H4": state("H4", 1, Direction.LONG),
            "H1": state("H1", -1, Direction.SHORT),
            "M30": state("M30", -1, Direction.SHORT),
            "M15": state("M15", -1, Direction.SHORT),
            "M5": state("M5", -1, Direction.SHORT),
            "M1": state("M1", -1, Direction.SHORT),
        }
        planner = DestinationPlanner(states, EngineConfig())
        source_pool = LiquidityPool(
            object_id="M30:source",
            timeframe="M30",
            kind=LiquidityKind.REACTION_TRAP,
            side=Side.LOW,
            created_index=0,
            occurred_at=1_700_000_000,
            available_at=1_700_000_060,
            bottom=95.0,
            top=95.1,
            source_wave_ids=["M30:source-wave"],
        )
        selected = planner._destination_context(
            Direction.LONG,
            1_700_000_060,
            94.0,
            96.0,
            "M30",
            source_pool,
        )
        self.assertIsNotNone(selected)
        self.assertEqual(selected[0], "M30")
        self.assertEqual(selected[4][2], 102.0)

    def test_architecture_gate_files_exist(self) -> None:
        self.assertTrue(
            Path("research/mentor-youtube/IMPLEMENTATION_GATES.md").exists()
        )
        self.assertTrue(
            Path(
                "research/mentor-youtube/Q1_SCENARIO_REVIEW_FIXTURES.json"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
