from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import numpy as np


class ReplayWorkspaceApiTest(unittest.TestCase):
    def test_ob_needs_departure_structure_break_and_later_retest(self) -> None:
        from scripts.mentor_semantic_validation import validate_causal_ob

        series = {
            "M15": [
                {"time": 0, "open": 99.0, "high": 101.0, "low": 97.0, "close": 100.0},
                {"time": 900, "open": 100.0, "high": 100.5, "low": 98.0, "close": 99.0},
                {"time": 1800, "open": 102.0, "high": 102.0, "low": 98.0, "close": 99.0},
                {"time": 2700, "open": 99.0, "high": 104.0, "low": 99.0, "close": 103.0},
                {"time": 3600, "open": 103.0, "high": 105.0, "low": 102.5, "close": 104.0},
            ],
            "M1": [
                {"time": 4200, "open": 103.0, "high": 103.5, "low": 101.0, "close": 102.0},
            ],
        }
        raw_only = {
            "type": "OB_LAST_OPPOSITE",
            "low": 98.0,
            "high": 102.0,
            "formedAt": "1970-01-01T00:30:00+00:00",
        }
        invalid_checks, _ = validate_causal_ob(
            series,
            "M15",
            raw_only,
            "long",
            5000,
            0.01,
            element="source",
            touch_at=4200,
            upper_bound=4500,
        )
        causal = {
            **raw_only,
            "breakLevel": 101.0,
            "breakLevelFormedAt": "1970-01-01T00:00:00+00:00",
            "breakAt": "1970-01-01T00:45:00+00:00",
        }
        valid_checks, _ = validate_causal_ob(
            series,
            "M15",
            causal,
            "long",
            5000,
            0.01,
            element="source",
            touch_at=4200,
            upper_bound=4500,
        )

        self.assertFalse(all(item["valid"] for item in invalid_checks if item["required"]))
        self.assertTrue(all(item["valid"] for item in valid_checks if item["required"]))

    def test_fvg_sweep_choch_and_objective_need_exact_raw_witnesses(self) -> None:
        from scripts.mentor_semantic_validation import (
            validate_choch,
            validate_objective_unconsumed,
            validate_raw_fvg,
            validate_sweep,
        )

        series = {
            "M1": [
                {"time": 0, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
                {"time": 60, "open": 100.0, "high": 103.0, "low": 100.0, "close": 102.0},
                {"time": 120, "open": 103.0, "high": 104.0, "low": 103.0, "close": 103.5},
                {"time": 240, "open": 100.0, "high": 101.0, "low": 99.5, "close": 100.5},
                {"time": 300, "open": 100.0, "high": 100.5, "low": 98.0, "close": 99.5},
                {"time": 360, "open": 100.5, "high": 103.0, "low": 100.0, "close": 102.0},
                {"time": 900, "open": 105.0, "high": 107.0, "low": 104.0, "close": 106.0},
                {"time": 1200, "open": 106.0, "high": 109.0, "low": 105.0, "close": 108.0},
                {"time": 1800, "open": 108.0, "high": 110.0, "low": 107.0, "close": 109.0},
            ],
            "M5": [
                {"time": 0, "open": 104.0, "high": 106.0, "low": 102.0, "close": 105.0},
                {"time": 300, "open": 105.0, "high": 108.0, "low": 103.0, "close": 107.0},
                {"time": 600, "open": 107.0, "high": 110.0, "low": 106.0, "close": 108.0},
                {"time": 900, "open": 108.0, "high": 109.0, "low": 105.0, "close": 106.0},
                {"time": 1200, "open": 106.0, "high": 108.0, "low": 104.0, "close": 105.0},
            ],
        }
        fvg_checks, _ = validate_raw_fvg(
            series,
            "M1",
            {
                "type": "FVG",
                "low": 101.0,
                "high": 103.0,
                "formedAt": "1970-01-01T00:02:00+00:00",
            },
            "long",
            1500,
            0.01,
            element="entry",
        )
        sweep_checks = validate_sweep(
            series,
            {"price": 99.0},
            {"at": "1970-01-01T00:05:00+00:00", "extreme": 98.0},
            "long",
            1500,
            0.01,
        )
        choch_checks = validate_choch(
            series,
            {
                "at": "1970-01-01T00:06:00+00:00",
                "level": 101.0,
                "referenceFormedAt": "1970-01-01T00:04:00+00:00",
            },
            "long",
            "M1",
            300,
            1500,
            0.01,
        )
        objective_checks = validate_objective_unconsumed(
            series,
            {
                "kind": "EXTERNAL_SWING",
                "price": 110.0,
                "formedAt": "1970-01-01T00:10:00+00:00",
                "timeframe": "M5",
            },
            "long",
            1500,
            0.01,
        )
        consumed_checks = validate_objective_unconsumed(
            series,
            {
                "kind": "EXTERNAL_SWING",
                "price": 110.0,
                "formedAt": "1970-01-01T00:10:00+00:00",
                "timeframe": "M5",
            },
            "long",
            1900,
            0.01,
        )

        self.assertTrue(all(item["valid"] for item in fvg_checks if item["required"]))
        self.assertTrue(all(item["valid"] for item in sweep_checks if item["required"]))
        self.assertTrue(all(item["valid"] for item in choch_checks if item["required"]))
        self.assertTrue(all(item["valid"] for item in objective_checks if item["required"]))
        self.assertFalse(all(item["valid"] for item in consumed_checks if item["required"]))

    def test_manual_step_cannot_skip_poi_or_watch(self) -> None:
        from scripts import mentor_q1_manual_ground_truth as replay

        rates = np.array(
            [
                (0, 100.0, 102.0, 98.0, 101.0, 10),
                (60, 101.0, 103.0, 100.0, 102.0, 10),
            ],
            dtype=[
                ("time", "<i8"),
                ("open", "<f8"),
                ("high", "<f8"),
                ("low", "<f8"),
                ("close", "<f8"),
                ("spread", "<i4"),
            ],
        )
        state = {
            "viewerTime": 0,
            "maxRevealedTime": 0,
            "activePoi": {
                "low": 99.0,
                "high": 100.0,
                "direction": "long",
                "label": "test",
                "touchedAt": None,
            },
            "activeOrder": None,
            "manualWatches": [
                {
                    "id": "W1",
                    "low": 101.5,
                    "high": 102.5,
                    "mode": "REVIEW",
                }
            ],
        }
        with (
            patch.object(replay, "require_workspace", return_value=({}, state, rates, {})),
            patch.object(replay, "expected_h1_times", return_value=[]),
            patch.object(replay, "require_current_h1_reviewed"),
            patch.object(replay, "append_execution"),
            patch.object(replay, "save_json"),
            patch.object(replay, "render_raw"),
            patch.object(replay, "write_progress"),
        ):
            replay.command_step(SimpleNamespace(minutes=15, micro=False))

        self.assertEqual(state["viewerTime"], 60)
        self.assertIsNotNone(state["activePoi"]["touchedAt"])
        self.assertEqual(state["manualWatches"], [])
        self.assertIsNotNone(state.get("manualMicroReview"))

    def test_recording_error_lock_blocks_replay_advance(self) -> None:
        from scripts import mentor_q1_manual_ground_truth as replay

        with self.assertRaises(SystemExit):
            replay.require_replay_unlocked(
                {
                    "recordingErrorLock": {
                        "command": "record-order",
                        "error": "invalid numeric argument",
                    }
                }
            )
        replay.require_replay_unlocked({})

    def test_carry_map_does_not_rearm_a_resolved_poi(self) -> None:
        from scripts import mentor_q1_manual_ground_truth as replay

        state = {
            "viewerTime": 3600,
            "maxRevealedTime": 3600,
            "activePoi": None,
            "activeOrder": None,
            "resolvedPoiKeys": ["family:source-1"],
        }
        previous = {
            "externalStructure": "up",
            "internalStructure": "pullback",
            "dealingRangeLow": 90.0,
            "dealingRangeHigh": 110.0,
            "pdLocation": "discount",
            "objective": "110",
            "opposingContext": "source OB",
            "poi": {
                "low": 98.0,
                "high": 100.0,
                "direction": "long",
                "label": "source",
                "selectedFamilyId": "source-1",
            },
            "poiFamily": [],
            "invalidation": "below 98",
        }
        args = SimpleNamespace(
            carry=True,
            decision="WAIT_POI",
            reason="unchanged",
            quiet=True,
            as_of=None,
        )
        with (
            patch.object(replay, "require_workspace", return_value=({}, state, np.array([]), {})),
            patch.object(replay, "expected_h1_times", return_value=[3600]),
            patch.object(replay, "map_recorded_exactly_at", return_value=False),
            patch.object(replay, "current_map", return_value=previous),
            patch.object(replay, "append_chain", side_effect=lambda _path, record: record),
            patch.object(replay, "save_json"),
            patch.object(replay, "write_progress"),
        ):
            replay.command_record_map(args)

        self.assertIsNone(state["activePoi"])

    def test_strict_poi_family_allows_a_direct_htf_parent(self) -> None:
        from scripts import mentor_q1_manual_ground_truth as replay

        family = [
            {
                "id": "M15_PARENT",
                "timeframe": "M15",
                "type": "OB_LAST_OPPOSITE",
                "low": 100.0,
                "high": 110.0,
                "formedAt": "1970-01-01T00:00:00+00:00",
                "originCandles": "last opposite candle",
                "displacementAndStructureRole": "body break",
                "breakLevel": 111.0,
                "breakLevelFormedAt": "1970-01-01T00:00:00+00:00",
                "breakAt": "1970-01-01T00:01:00+00:00",
                "state": "FRESH",
            }
        ]
        valid_checks = ([{"required": True, "valid": True, "reason": ""}], {})
        with (
            patch.object(replay, "STRICT_HTF_CAUSAL_MODE", True),
            patch.object(replay, "validate_causal_ob", return_value=valid_checks),
        ):
            parsed = replay.parse_poi_family(
                json.dumps(family),
                current=120,
                series={},
                direction="long",
            )

        self.assertEqual(parsed, family)

    def test_strict_poi_family_rejects_overlap_without_full_containment(self) -> None:
        from scripts import mentor_q1_manual_ground_truth as replay

        family = [
            {
                "id": "M15_PARENT",
                "timeframe": "M15",
                "type": "OB_LAST_OPPOSITE",
                "low": 100.0,
                "high": 110.0,
                "formedAt": "1970-01-01T00:00:00+00:00",
                "originCandles": "parent",
                "displacementAndStructureRole": "parent break",
                "breakLevel": 111.0,
                "breakLevelFormedAt": "1970-01-01T00:00:00+00:00",
                "breakAt": "1970-01-01T00:01:00+00:00",
                "state": "FRESH",
            },
            {
                "id": "M5_CHILD",
                "timeframe": "M5",
                "type": "OB_LAST_OPPOSITE",
                "low": 99.0,
                "high": 105.0,
                "formedAt": "1970-01-01T00:00:00+00:00",
                "originCandles": "child",
                "displacementAndStructureRole": "child break",
                "breakLevel": 106.0,
                "breakLevelFormedAt": "1970-01-01T00:00:00+00:00",
                "breakAt": "1970-01-01T00:01:00+00:00",
                "state": "FRESH",
                "causalRelationToParent": "overlap only",
            },
        ]
        valid_checks = ([{"required": True, "valid": True, "reason": ""}], {})
        with (
            patch.object(replay, "STRICT_HTF_CAUSAL_MODE", True),
            patch.object(replay, "validate_causal_ob", return_value=valid_checks),
            self.assertRaisesRegex(SystemExit, "not price-contained"),
        ):
            replay.parse_poi_family(
                json.dumps(family),
                current=120,
                series={},
                direction="long",
            )

    def test_each_h1_boundary_requires_its_own_map_review(self) -> None:
        from scripts import mentor_q1_manual_ground_truth as replay

        with (
            patch.object(replay, "map_recorded_exactly_at", return_value=False),
            self.assertRaises(SystemExit),
        ):
            replay.require_current_h1_reviewed({"viewerTime": 3600}, [3600, 7200])

    def test_limit_order_fills_on_a_gap_at_the_better_open(self) -> None:
        from scripts.mentor_q1_manual_ground_truth import order_event_on_bar

        bar = {
            "time": 0,
            "open": 98.0,
            "high": 99.0,
            "low": 97.0,
            "close": 98.5,
            "spread": 10,
        }
        order = {
            "direction": "long",
            "status": "PENDING",
            "entry": 100.0,
            "stopLoss": 95.0,
            "takeProfit": 110.0,
            "sourceInvalidation": 94.0,
        }
        event = order_event_on_bar(order, bar, source_close_due=False)

        self.assertEqual(event["type"], "ORDER_FILLED")
        self.assertAlmostEqual(event["fillPrice"], 98.1)

    def test_structural_stop_uses_source_distal_sweep_and_spread(self) -> None:
        from scripts.mentor_q1_manual_ground_truth import structural_stop_boundary

        rates = np.array(
            [(60, 35)],
            dtype=[("time", "<i8"), ("spread", "<i4")],
        )
        short = SimpleNamespace(
            direction="short",
            source_zone_low=3356.44,
            source_zone_high=3361.92,
            source_invalidation=3361.92,
            sweep_extreme=3356.87,
        )
        long = SimpleNamespace(
            direction="long",
            source_zone_low=3281.26,
            source_zone_high=3289.01,
            source_invalidation=3281.26,
            sweep_extreme=3285.44,
        )

        short_stop, short_buffer = structural_stop_boundary(short, rates, 120)
        long_stop, long_buffer = structural_stop_boundary(long, rates, 120)

        self.assertAlmostEqual(short_buffer, 0.35)
        self.assertAlmostEqual(short_stop, 3362.27)
        self.assertAlmostEqual(long_buffer, 0.35)
        self.assertAlmostEqual(long_stop, 3280.91)

    def test_replay_drawings_require_raw_ob_or_fvg_evidence(self) -> None:
        from scripts.import_manual_ledger_to_replay_session import validate_zone_evidence

        series = {
            "M1": [
                {"time": 0, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5},
                {"time": 60, "open": 100.5, "high": 102.0, "low": 100.0, "close": 101.5},
                {"time": 120, "open": 103.0, "high": 104.0, "low": 103.0, "close": 103.5},
            ],
            "M5": [
                {"time": 0, "open": 105.0, "high": 106.0, "low": 100.0, "close": 101.0},
            ],
        }
        bullish_fvg = validate_zone_evidence(
            series,
            "M1",
            {"label": "bullish FVG", "low": 101.0, "high": 103.0},
            180,
            "long",
            0.01,
        )
        bullish_ob = validate_zone_evidence(
            series,
            "M5",
            {"label": "bullish OB", "low": 100.0, "high": 106.0},
            300,
            "long",
            0.01,
        )
        generic_zone = validate_zone_evidence(
            series,
            "M5",
            {"label": "reaction source", "low": 100.0, "high": 106.0},
            300,
            "long",
            0.01,
        )

        self.assertTrue(bullish_fvg["valid"])
        self.assertTrue(bullish_ob["valid"])
        self.assertFalse(generic_zone["valid"])

    def test_week_data_and_session_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            os.environ["TRADING_JOURNAL_DB"] = str(Path(temporary) / "journal.db")
            from bridge import mt5_bridge as bridge

            bridge.JOURNAL_DB_READY = False
            bridge.JOURNAL_DB_FILE = Path(os.environ["TRADING_JOURNAL_DB"])
            datasets = bridge.replay_datasets_payload()["datasets"]
            dataset = next(item for item in datasets if item["name"].startswith("GOLD_M1_2023"))
            week = bridge.replay_data_payload(dataset["name"], "2025-01-06T00:00:00Z", 7, 14)

            self.assertGreater(week["replayBars"], 0)
            self.assertGreater(week["warmupBars"], 0)
            self.assertTrue(all(bar["time"] < week["replayEnd"] for bar in week["bars"]))

            session = {
                "id": "test-replay-session",
                "name": "Replay API test",
                "symbol": "GOLD",
                "dataset": dataset["name"],
                "weekStart": week["replayStart"],
                "weekEnd": week["replayEnd"],
                "cursorTime": week["replayStart"],
                "maxSeenTime": week["replayStart"],
                "events": [],
                "drawings": [],
                "orders": [],
                "scenarios": [],
            }
            self.assertTrue(bridge.save_replay_session(session)["ok"])
            restored = bridge.replay_session_payload(session["id"])["session"]
            self.assertEqual(restored["name"], session["name"])
            self.assertEqual(bridge.replay_sessions_payload()["sessions"][0]["id"], session["id"])
            self.assertTrue(bridge.delete_replay_session(session["id"])["deleted"])


if __name__ == "__main__":
    unittest.main()
