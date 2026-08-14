from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.mentor_ai_replay import (
    PROMPT_LIMIT_CONFIG_KEYS,
    ROOT,
    advance_pending_order,
    augment_candidates_with_local_root,
    previous_map_candidate_for_review,
    bounded_map_scout_prompt,
    bounded_stage_prompt,
    build_decision_prompt,
    carry_previous_across_query,
    clear_terminal_resume_decision,
    compact_evidence_for_prompt,
    consume_reviewed_map_approach,
    find_local_map_wakeup,
    find_local_trigger_wakeup,
    enforce_prompt_size,
    expected_transition_state,
    immediate_phase_transition,
    validate_initial_causal_intent,
    normalize_decision_routing,
    normalize_decision_queries,
    normalize_decision_state,
    normalize_map_rejection_audit,
    normalize_numeric_claims_from_evidence,
    normalize_review_schedule,
    output_token_limit,
    phase_token_reserve,
    load_stage_contract,
    locally_arm_child_touch,
    map_root_exclusions,
    map_candidate_ohlc_rejection,
    next_decision_index,
    parse_utc,
    phase_for,
    provider_calls_in_ledger,
    query_budget_fallback_decision,
    rejected_decision_fallback,
    recovery_queries_for_missing_origins,
    root_child_delivery_candidate_at,
    simulate_filled_position,
    utc_text,
    validate_decision,
    validate_transition_contract,
    validate_pending_entry_side,
    watch_hit,
)
from scripts.mentor_replay_v2 import (
    STAGE_SCHEMAS,
    bars_for_prompt,
    canonical_map_decision,
    canonical_stage_decision,
    compact_bars,
    evidence_for_bars,
    map_review_prompt,
    map_scout_prompt,
    refinement_candidate_table,
    refinement_candidates,
    resolve_bar,
    stage_prompt,
    structural_liquidity_candidates,
    structural_liquidity_table,
)
from scripts.gemini_replay_provider import extract_structured_payload


START = parse_utc("2024-08-22T10:20:00Z")


def test_prompt_is_canonical_and_readable() -> None:
    prompt = build_decision_prompt(
        contract="CONTRACT",
        packet={"asOfUtc": utc_text(START), "phase": "MAP", "images": []},
        phase="MAP",
        previous=None,
        candle_evidence=None,
    )
    assert "Compare EXTERNAL_CONTINUATION" in prompt
    assert "QUERY_CANDLES" in prompt
    assert "\ufffd" not in prompt

    final_prompt = build_decision_prompt(
        contract="CONTRACT",
        packet={
            "asOfUtc": utc_text(START), "phase": "MAP", "images": [],
            "candleQueryBudget": {
                "used": 2, "maximum": 2, "remaining": 0,
                "mustDecideNow": True,
            },
        },
        phase="MAP",
        previous=None,
        candle_evidence=[{"tf": "H1", "candles": []}],
    )
    assert "Do not return QUERY_CANDLES" in final_prompt

    wakeup_prompt = build_decision_prompt(
        contract="CONTRACT",
        packet={
            "asOfUtc": utc_text(START), "phase": "TRIGGER", "images": [],
            "localTriggerWakeup": {
                "kind": "LOCAL_TRIGGER_PATTERN_CANDIDATE",
                "screeningOnly": True,
            },
        },
        phase="TRIGGER",
        previous=None,
        candle_evidence=None,
    )
    assert "complete OHLC-backed trigger-chain candidates" in wakeup_prompt
    assert "triggerCandidateKey" in wakeup_prompt
    assert "does not authorize an order" in wakeup_prompt


def test_query_budget_becomes_no_trade() -> None:
    decision = query_budget_fallback_decision(
        as_of=utc_text(START),
        config={"maximumFlatReviewMinutes": 360},
        exhausted_decision={
            "candleQueries": [{
                "tf": "H1", "aroundTimeUtc": utc_text(START - 3600),
                "purpose": "ROOT_OB",
            }],
        },
    )
    assert decision["action"] == "NO_TRADE"
    assert decision["state"] == "FLAT"
    assert decision["scenario"] is None
    assert decision["nextReviewAtUtc"] == utc_text(START + 6 * 3600)
    assert "H1@" in decision["rejectionReasons"][0]


def test_flat_review_respects_bounded_analyst_schedule() -> None:
    decision = {
        "state": "FLAT", "scenario": None, "action": "NO_TRADE",
        "watchEvents": [], "nextReviewAtUtc": utc_text(START + 3 * 3600),
    }
    config = {"minimumFlatReviewMinutes": 5, "maximumFlatReviewMinutes": 360}
    normalize_review_schedule(decision, config, START)
    assert decision["nextReviewAtUtc"] == utc_text(START + 3 * 3600)

    too_soon = copy.deepcopy(decision)
    too_soon["nextReviewAtUtc"] = utc_text(START + 60)
    normalize_review_schedule(too_soon, config, START)
    assert too_soon["nextReviewAtUtc"] == utc_text(START + 5 * 60)

    too_late = copy.deepcopy(decision)
    too_late["nextReviewAtUtc"] = utc_text(START + 12 * 3600)
    normalize_review_schedule(too_late, config, START)
    assert too_late["nextReviewAtUtc"] == utc_text(START + 6 * 3600)


def test_generic_map_rejection_is_audited_and_never_retried_next_minute() -> None:
    decision = {
        "schemaVersion": "1.5.0", "asOfUtc": utc_text(START), "phase": "MAP",
        "action": "NO_TRADE", "state": "FLAT", "scenario": None,
        "candleQueries": [], "watchEvents": [],
        "nextReviewAtUtc": utc_text(START + 30 * 60), "order": None,
        "rejectionReasons": ["No verified causal root is available."],
        "reason": "Remain flat.",
    }
    evidence = [{
        "tf": "H1",
        "candles": [{
            "openTimeUtc": utc_text(START - 3600),
            "open": 2505.0, "high": 2510.0, "low": 2500.0, "close": 2507.0,
        }],
    }]
    adjustment = normalize_map_rejection_audit(decision, evidence)
    assert adjustment and "H1" in decision["rejectionReasons"][-1]
    assert "2500.00-2510.00" in decision["rejectionReasons"][-1]
    config = {
        "minimumFlatReviewMinutes": 240, "maximumFlatReviewMinutes": 360,
        "point": 0.01, "brokerStopsLevelPrice": 0.0, "brokerSpecResolved": True,
    }
    normalize_review_schedule(decision, config, START)
    assert decision["nextReviewAtUtc"] == utc_text(START + 4 * 3600)
    assert validate_decision(decision, config, START, evidence) == []

    rejected = copy.deepcopy(decision)
    rejected["rejectionReasons"] = ["generic rejection without evidence"]
    fallback = rejected_decision_fallback(
        as_of=utc_text(START),
        phase="MAP",
        rejected_decision=rejected,
        previous_decision=None,
        errors=["MAP rejection lacks concrete TF and price candidate audit"],
        config=config,
        candle_evidence=[],
    )
    assert fallback["state"] == "FLAT"
    assert fallback["nextReviewAtUtc"] == utc_text(START + 4 * 3600)
    assert validate_decision(fallback, config, START, []) == []


def test_refinement_arm_waits_for_local_trigger_event() -> None:
    decision = {
        "action": "ARM", "state": "ARMED",
        "scenario": {"refinementPath": [{"tf": "M5"}]},
    }
    assert immediate_phase_transition("REFINEMENT", decision) is None
    assert immediate_phase_transition("MAP", decision) is None


def test_local_trigger_wakeup_recovers_aug22_chain_without_m1_api_polling() -> None:
    base = parse_utc("2024-08-22T10:00:00Z")
    values = [
        (2507.38, 2508.08, 2507.22, 2507.50),
        (2507.46, 2508.01, 2507.25, 2507.95),
        (2507.95, 2508.05, 2506.50, 2507.05),
        (2507.05, 2508.95, 2506.81, 2508.94),
        (2508.83, 2509.07, 2507.80, 2507.82),
        (2507.84, 2508.42, 2507.77, 2508.36),
        (2508.42, 2508.52, 2508.17, 2508.37),
        (2508.36, 2508.45, 2507.90, 2508.35),
        (2508.27, 2508.27, 2507.60, 2507.67),
        (2507.68, 2508.37, 2507.68, 2508.26),
        (2508.26, 2509.15, 2508.23, 2509.15),
        (2509.15, 2509.36, 2508.53, 2508.91),
        (2508.94, 2509.23, 2508.38, 2508.76),
        (2508.77, 2508.77, 2508.08, 2508.48),
        (2508.53, 2508.80, 2508.12, 2508.50),
        (2508.68, 2509.13, 2507.07, 2507.17),
        (2507.18, 2507.40, 2506.95, 2507.08),
        (2507.09, 2507.35, 2506.90, 2507.02),
        (2507.03, 2507.31, 2506.88, 2506.98),
    ]
    dtype = [
        ("time", "i8"), ("open", "f8"), ("high", "f8"),
        ("low", "f8"), ("close", "f8"), ("spread", "f8"),
    ]
    rates = np.zeros(len(values), dtype=dtype)
    for index, (open_, high, low, close) in enumerate(values):
        rates[index] = (base + index * 60, open_, high, low, close, 27.0)

    config = {
        "point": 0.01,
        "localTriggerWakeupEnabled": True,
        "localTriggerLookbackBars": 90,
        "localTriggerMinimumReactionBars": 1,
    }
    wake_index, wake = find_local_trigger_wakeup(
        rates, 0, len(rates) - 1, "SHORT", config
    )
    # The only apparent reference is a one-bar micro pivot immediately before
    # the sweep, so the frozen AGENTS contract must not wake the AI for it.
    assert wake_index is None
    assert wake is None
    assert find_local_trigger_wakeup(rates, 0, 14, "SHORT", config)[0] is None
    assert find_local_trigger_wakeup(rates, 14, 15, "SHORT", config)[0] is None
    assert find_local_trigger_wakeup(rates, 15, len(rates) - 1, "SHORT", config)[0] is None

    decision = {
        "state": "ARMED",
        "scenario": {"direction": "SHORT"},
        "watchEvents": [],
        "nextReviewAtUtc": "2024-08-22T10:30:00Z",
    }
    assert next_decision_index(rates, 0, decision, config)[0] is None
    mirrored = rates.copy()
    mirrored["open"] = 5000.0 - rates["open"]
    mirrored["high"] = 5000.0 - rates["low"]
    mirrored["low"] = 5000.0 - rates["high"]
    mirrored["close"] = 5000.0 - rates["close"]
    long_index, long_wake = find_local_trigger_wakeup(
        mirrored, 0, len(mirrored) - 1, "LONG", config
    )
    assert long_index is None
    assert long_wake is None


def test_reviewed_map_approach_is_consumed_once() -> None:
    decision = {
        "action": "WATCH_MAP",
        "watchEvents": [
            {"kind": "ROOT_APPROACH"},
            {"kind": "SOURCE_INVALIDATION"},
            {"kind": "OBJECTIVE_REACHED"},
        ],
    }
    assert consume_reviewed_map_approach(decision, "ROOT_APPROACH")
    assert [item["kind"] for item in decision["watchEvents"]] == [
        "SOURCE_INVALIDATION", "OBJECTIVE_REACHED",
    ]
    assert not consume_reviewed_map_approach(decision, "ROOT_APPROACH")


def test_marketable_limit_is_rejected() -> None:
    packet = {
        "lastClosedM1": {"close": 100.0},
        "spreadPrice": 0.2,
    }
    long_order = {
        "action": "ORDER",
        "scenario": {"direction": "LONG"},
        "order": {"entry": 100.3},
    }
    short_order = {
        "action": "ORDER",
        "scenario": {"direction": "SHORT"},
        "order": {"entry": 99.9},
    }
    valid_long = copy.deepcopy(long_order)
    valid_long["order"]["entry"] = 99.9
    valid_short = copy.deepcopy(short_order)
    valid_short["order"]["entry"] = 100.3
    assert "buy limit" in validate_pending_entry_side(long_order, packet)[0]
    assert "sell limit" in validate_pending_entry_side(short_order, packet)[0]
    assert validate_pending_entry_side(valid_long, packet) == []
    assert validate_pending_entry_side(valid_short, packet) == []


def synthetic_rates() -> np.ndarray:
    dtype = [
        ("time", "i8"), ("open", "f8"), ("high", "f8"),
        ("low", "f8"), ("close", "f8"), ("spread", "f8"),
    ]
    rates = np.zeros(80, dtype=dtype)
    for index in range(len(rates)):
        rates[index] = (START + index * 60, 99.0, 99.2, 98.8, 99.0, 1.0)
    rates[28]["high"] = 100.2
    rates[35]["low"] = 97.8
    return rates


def scenario() -> dict:
    return {
        "scenarioId": "TEST",
        "frozenAtUtc": utc_text(START - 600),
        "direction": "SHORT",
        "scope": "INTERNAL_ROTATION",
        "objective": {
            "type": "INTERNAL_LIQUIDITY", "side": "SSL", "price": 98.0,
            "sourceTf": "M30", "sourceTime": utc_text(START - 3600),
        },
        "rootOb": {
            "tf": "H1", "originTime": utc_text(START - 7200),
            "low": 99.5, "high": 100.5, "direction": "BEARISH",
            "causalReason": "test",
        },
        "refinementPath": [{
            "tf": "M5", "originTime": utc_text(START - 1800),
            "low": 99.8, "high": 100.2, "direction": "BEARISH",
            "causalReason": "test child",
        }],
        "sourceInvalidation": 100.5,
        "rootInvalidation": 100.5,
        "refinedTouchBarId": f"M1:{START - 420}",
        "refinedTouchTimeUtc": utc_text(START - 420),
    }


def order() -> dict:
    return {
        "executionModel": "HTF_OB_REACTION",
        "entry": 100.0, "stopLoss": 101.0, "takeProfit": 98.0,
        "rootOriginTime": utc_text(START - 7200),
        "childOriginTime": utc_text(START - 1800),
        "objectiveSourceTime": utc_text(START - 3600),
        "executionOriginTime": utc_text(START),
        "executionLow": 100.0,
        "executionHigh": 100.2,
        "triggerProtectedSwing": 100.3,
        "triggerProtectedSwingSourceTimeUtc": utc_text(START - 240),
        "sweepExtreme": 100.4,
        "sweepExtremeSourceTimeUtc": utc_text(START - 180),
        "sweepRecoveryTimeUtc": utc_text(START - 180),
        "chochReferencePrice": 100.1,
        "chochReferenceSourceTimeUtc": utc_text(START - 300),
        "chochBreakTimeUtc": utc_text(START),
        "matureLiquidityPrice": 100.3,
        "matureLiquiditySourceTimeUtc": utc_text(START - 360),
        "refinedTouchBarId": f"M1:{START - 420}",
        "refinedTouchTimeUtc": utc_text(START - 420),
        "triggerLineage": (
            f"P={utc_text(START - 240)};S={utc_text(START - 180)};"
            f"R={utc_text(START - 300)};B={utc_text(START)}"
        ),
        "actualSpread": 0.01,
        "brokerStopsLevelPrice": 0.0,
        "slBuffer": 0.01,
        "lastReauthorizedAtUtc": utc_text(START + 60),
    }


def pending_decision(review_minutes: int = 60) -> dict:
    return {
        "nextReviewAtUtc": utc_text(START + review_minutes * 60),
        "watchEvents": [],
    }


def test_pending_lifecycle() -> None:
    rates = synthetic_rates()
    config = {"point": 0.01}
    status, index, event = advance_pending_order(
        rates, 0, scenario(), order(), pending_decision(60), config
    )
    assert (status, index, event) == ("FILLED", 28, "ENTRY_FILLED")
    outcome, close_index = simulate_filled_position(
        rates, index, scenario(), order(), config
    )
    assert outcome and outcome["outcome"] == "TP" and close_index == 35

    status, index, event = advance_pending_order(
        rates, 0, scenario(), order(), pending_decision(20), config
    )
    assert status == "REVIEW" and event == "SCHEDULED_REVIEW" and index == 19

    status, _, event = advance_pending_order(
        rates, 0, scenario(), order(), pending_decision(60), config,
        entry_deadline=START + 20 * 60,
    )
    assert status == "END" and event == "ENTRY_WINDOW_CLOSED"

    decision = pending_decision(60)
    decision["watchEvents"] = [{
        "eventId": "cancel", "kind": "ORDER_CANCEL_LEVEL",
        "comparison": "CROSS_ABOVE", "price": 100.1,
        "validUntilUtc": utc_text(START + 3600),
    }]
    status, _, event = advance_pending_order(
        rates, 0, scenario(), order(), decision, config
    )
    assert status == "REVIEW" and event == "ORDER_CANCEL_LEVEL"


def test_watch_events_are_edges_not_persistent_states() -> None:
    rates = synthetic_rates()
    persistent = {
        "kind": "CHOCH_REFERENCE", "comparison": "CROSS_ABOVE", "price": 98.9,
    }
    assert not watch_hit(persistent, rates[1], 0.01, rates[0])

    rates[2]["close"] = 98.7
    rates[3]["close"] = 99.1
    assert watch_hit(persistent, rates[3], 0.01, rates[2])
    rates[4]["close"] = 99.0
    assert not watch_hit(persistent, rates[4], 0.01, rates[3])


def test_source_invalidation_waits_for_source_timeframe_body_close() -> None:
    rates = synthetic_rates()
    event = {
        "kind": "SOURCE_INVALIDATION", "comparison": "CROSS_ABOVE",
        "price": 100.1, "sourceTf": "M5",
    }
    rates[1]["high"], rates[1]["close"] = 101.0, 100.5
    assert not watch_hit(event, rates[1], 0.01, rates[0])
    rates[4]["high"], rates[4]["close"] = 101.0, 100.5
    assert watch_hit(event, rates[4], 0.01, rates[3])
    rates[4]["close"] = 100.1
    assert not watch_hit(event, rates[4], 0.01, rates[3])


def test_child_touch_is_armed_locally_without_provider() -> None:
    rates = synthetic_rates()
    rates[10]["low"] = 99.7
    rates[10]["high"] = 100.0
    frozen = scenario()
    frozen.pop("refinedTouchBarId", None)
    frozen.pop("refinedTouchTimeUtc", None)
    decision, evidence = locally_arm_child_touch(
        {"state": "PREPARED", "scenario": frozen},
        rates[10],
        {"point": 0.01, "maximumScenarioReviewMinutes": 360},
    )
    assert decision["action"] == "ARM" and decision["state"] == "ARMED"
    assert decision["scenario"]["refinedTouchBarId"] == f"M1:{START + 600}"
    assert evidence["purpose"] == "CHILD_TOUCH"
    assert evidence["candles"][0]["spreadPrice"] == 0.01


def test_orchestrator_state_transitions() -> None:
    assert phase_for("ARMED", "LOCAL_MAP_ACTIVITY") == "MAP"
    assert phase_for("ARMED", "SOURCE_INVALIDATION") == "MAP"
    assert phase_for("PENDING", "SOURCE_INVALIDATION") == "PENDING_REVIEW"
    assert phase_for("PREPARED", "ROOT_APPROACH") == "REFINEMENT"
    assert phase_for("PREPARED", "CHILD_TOUCH") == "REFINEMENT"
    assert phase_for("WATCHING_MAP", "ROOT_APPROACH") == "MAP"
    assert phase_for("ARMED", "SCHEDULED_REVIEW") == "TRIGGER"
    assert phase_for("PENDING", "SOURCE_INVALIDATION") == "PENDING_REVIEW"

    frozen = {"state": "PREPARED", "scenario": scenario()}
    query = {"action": "QUERY_CANDLES", "state": "PREPARED", "scenario": None}
    assert carry_previous_across_query(frozen, query) is frozen

    routed = {"asOfUtc": "2024-08-22T01:01:00Z", "phase": "REFINEMENT"}
    adjustment = normalize_decision_routing(
        routed, "2024-08-22T02:00:00Z", "MAP"
    )
    assert routed == {"asOfUtc": "2024-08-22T02:00:00Z", "phase": "MAP"}
    assert adjustment and adjustment["model"]["phase"] == "REFINEMENT"

    ordered = {"action": "ORDER", "state": "ARMED"}
    state_adjustment = normalize_decision_state(
        ordered, {"state": "ARMED"}
    )
    assert ordered["state"] == "PENDING"
    assert state_adjustment and state_adjustment["modelState"] == "ARMED"

    queried = {"action": "QUERY_CANDLES", "state": "FLAT"}
    normalize_decision_state(queried, {"state": "PREPARED"})
    assert queried["state"] == "PREPARED"

    mixed = {
        "action": "PREPARE",
        "candleQueries": [{"queryId": "child"}],
    }
    query_adjustment = normalize_decision_queries(mixed)
    assert mixed["candleQueries"] == []
    assert mixed["_prefetchQueries"] == [{"queryId": "child"}]
    assert query_adjustment and query_adjustment["deferredQueries"] == 1

    missing_objective = {
        "scenario": scenario(),
        "order": None,
    }
    recovery = recovery_queries_for_missing_origins(
        missing_objective,
        ["objective origin is not backed by queried candle OHLC"],
    )
    assert recovery == [{
        "queryId": "recover-objective",
        "tf": "M30",
        "aroundTimeUtc": utc_text(START - 3600),
        "before": 2,
        "after": 2,
        "purpose": "OBJECTIVE",
    }]

    evidence_sample = [
        {"tf": "H1", "purpose": "ROOT_OB", "candles": [
            {"openTimeUtc": utc_text(START - 10800)},
            {"openTimeUtc": scenario()["rootOb"]["originTime"]},
            {"openTimeUtc": utc_text(START - 3600)},
        ]},
        {"tf": "M5", "purpose": "CHILD_OB", "candles": [
            {"openTimeUtc": scenario()["refinementPath"][0]["originTime"]},
        ]},
        {"tf": "M1", "purpose": "SWEEP", "candles": [
            {"openTimeUtc": utc_text(START)},
        ]},
    ]
    compacted = compact_evidence_for_prompt(
        evidence_sample, {"scenario": scenario()}, "TRIGGER"
    )
    assert [block["tf"] for block in compacted] == ["H1", "M5", "M1"]

    scheduled = {
        "state": "PREPARED",
        "scenario": scenario(),
        "watchEvents": [{
            "eventId": "child", "kind": "CHILD_TOUCH", "comparison": "TOUCH",
            "price": 100.2, "validUntilUtc": utc_text(START + 4 * 3600),
        }],
        "nextReviewAtUtc": utc_text(START + 900),
    }
    adjustment = normalize_review_schedule(
        scheduled, {"maximumScenarioReviewMinutes": 360}, START
    )
    assert scheduled["watchEvents"][0]["price"] == 99.8
    assert scheduled["nextReviewAtUtc"] == utc_text(START + 6 * 3600)
    assert all(
        event["validUntilUtc"] == utc_text(START + 6 * 3600)
        for event in scheduled["watchEvents"]
    )
    assert adjustment and set(adjustment["addedSafetyEvents"]) == {
        "SOURCE_INVALIDATION", "OBJECTIVE_REACHED",
    }

    refinement_wait = copy.deepcopy(scheduled)
    refinement_wait["phase"] = "REFINEMENT"
    refinement_wait["watchEvents"] = [{
        "eventId": "old-root", "kind": "ROOT_APPROACH", "comparison": "TOUCH",
        "price": 99.5, "sourceTf": "H1",
        "sourceTimeUtc": scenario()["rootOb"]["originTime"],
        "validUntilUtc": utc_text(START + 3600),
    }]
    refinement_adjustment = normalize_review_schedule(
        refinement_wait, {"maximumScenarioReviewMinutes": 360}, START
    )
    kinds = {event["kind"] for event in refinement_wait["watchEvents"]}
    assert "ROOT_APPROACH" not in kinds and "CHILD_TOUCH" in kinds
    assert refinement_adjustment and refinement_adjustment["addedFinalChildTouch"]

    trigger_wait = copy.deepcopy(scheduled)
    trigger_wait.update({
        "schemaVersion": "1.5.0", "asOfUtc": utc_text(START),
        "phase": "TRIGGER", "action": "WAIT", "candleQueries": [],
        "order": None, "rejectionReasons": [], "reason": "waiting",
    })
    trigger_wait["watchEvents"] = [{
        "eventId": "old-child", "kind": "CHILD_TOUCH", "comparison": "TOUCH",
        "price": 99.8, "validUntilUtc": utc_text(START + 3600),
    }]
    normalize_review_schedule(trigger_wait, {"maximumScenarioReviewMinutes": 360}, START)
    trigger_errors = validate_decision(
        trigger_wait,
        {
            "maximumScenarioReviewMinutes": 360, "maximumFlatReviewMinutes": 360,
            "point": 0.01, "brokerStopsLevelPrice": 0.0, "brokerSpecResolved": True,
            "localTriggerWakeupEnabled": False,
        },
        START,
        [],
    )
    assert "TRIGGER WAIT requires a concrete sweep or CHoCH watch level" in trigger_errors
    assert all(event["kind"] != "CHILD_TOUCH" for event in trigger_wait["watchEvents"])


def test_all_phase_action_transitions_are_engine_owned() -> None:
    actions = {
        "QUERY_CANDLES", "WAIT", "PREPARE", "ARM", "ORDER", "CANCEL",
        "NO_TRADE", "DATA_ERROR",
    }
    states = {"FLAT", "PREPARED", "ARMED", "TRIGGERED", "PENDING", "CANCELED"}
    allowed = {
        "MAP": {"QUERY_CANDLES", "WAIT", "PREPARE", "NO_TRADE", "DATA_ERROR"},
        "REFINEMENT": {"QUERY_CANDLES", "WAIT", "ARM", "CANCEL", "DATA_ERROR"},
        "TRIGGER": {"QUERY_CANDLES", "WAIT", "ORDER", "CANCEL", "DATA_ERROR"},
        "PENDING_REVIEW": {"QUERY_CANDLES", "ORDER", "CANCEL", "DATA_ERROR"},
    }
    previous_by_phase = {
        "MAP": None,
        "REFINEMENT": {"state": "PREPARED", "scenario": scenario(), "order": None},
        "TRIGGER": {"state": "PREPARED", "scenario": scenario(), "order": None},
        "PENDING_REVIEW": {
            "state": "PENDING", "scenario": scenario(), "order": order(),
        },
    }
    for phase, phase_actions in allowed.items():
        previous = previous_by_phase[phase]
        for action in actions:
            expected = expected_transition_state(phase, action, previous)
            for state in states:
                decision = {
                    "phase": phase,
                    "action": action,
                    "state": state,
                    "scenario": previous.get("scenario") if previous else None,
                    "order": previous.get("order") if previous else None,
                }
                errors = validate_transition_contract(decision, previous)
                if action in phase_actions:
                    assert not any("not allowed" in error for error in errors), (
                        phase, action, state, errors,
                    )
                    has_state_error = any("requires state=" in error for error in errors)
                    assert has_state_error == (state != expected), (
                        phase, action, state, expected, errors,
                    )
                else:
                    assert any("not allowed" in error for error in errors), (
                        phase, action, state, errors,
                    )

    trigger_query = {
        "phase": "TRIGGER", "action": "QUERY_CANDLES", "state": "PREPARED",
        "scenario": scenario(), "order": None,
    }
    adjustment = normalize_decision_state(
        trigger_query, previous_by_phase["TRIGGER"], "TRIGGER"
    )
    assert adjustment and trigger_query["state"] == "ARMED"

    pending_review = {
        "schemaVersion": "1.5.0", "asOfUtc": utc_text(START),
        "phase": "PENDING_REVIEW", "action": "ORDER", "state": "PENDING",
        "scenario": scenario(), "candleQueries": [], "watchEvents": [],
        "order": order(), "nextReviewAtUtc": utc_text(START),
        "rejectionReasons": [], "reason": "reauthorize pending order",
    }
    pending_review["watchEvents"] = [{
        "eventId": "expired-source", "kind": "SOURCE_INVALIDATION",
        "comparison": "CROSS_ABOVE", "price": 100.5,
        "sourceTf": "H1", "sourceTimeUtc": scenario()["rootOb"]["originTime"],
        "validUntilUtc": utc_text(START),
    }]
    pending_config = {
        "maximumPendingReviewMinutes": 60,
        "maximumScenarioReviewMinutes": 360,
    }
    pending_adjustment = normalize_review_schedule(
        pending_review, pending_config, START
    )
    assert pending_review["nextReviewAtUtc"] == utc_text(START + 3600)
    assert all(
        event["validUntilUtc"] == utc_text(START + 3600)
        for event in pending_review["watchEvents"]
    )
    assert pending_adjustment and pending_adjustment["reason"] == "PENDING_REAUTHORIZATION_WINDOW"


def test_map_validation_contract() -> None:
    as_of = START
    root_time = utc_text(START - 7200)
    objective_time = utc_text(START - 3600)
    evidence = [
        {"tf": "H1", "candles": [{
            "openTimeUtc": root_time, "open": 100.5, "high": 100.8,
            "low": 99.5, "close": 100.2,
        }]},
        {"tf": "M30", "candles": [{
            "openTimeUtc": objective_time, "open": 98.8, "high": 99.2,
            "low": 98.0, "close": 98.5,
        }]},
    ]
    mapped = scenario()
    mapped["refinementPath"] = []
    decision = {
        "schemaVersion": "1.5.0", "asOfUtc": utc_text(as_of), "phase": "MAP",
        "action": "PREPARE", "state": "PREPARED", "scenario": mapped,
        "candleQueries": [], "watchEvents": [],
        "nextReviewAtUtc": utc_text(as_of + 3600), "order": None,
        "rejectionReasons": [
            "EXTERNAL_CONTINUATION rejected by test evidence",
            "EXTERNAL_REVERSAL rejected by test evidence",
        ],
        "reason": "INTERNAL_ROTATION selected",
    }
    config = {
        "maximumPreparedReviewMinutes": 60,
        "maximumFlatReviewMinutes": 360,
        "point": 0.01,
        "brokerStopsLevelPrice": 0.0,
        "brokerSpecResolved": True,
    }
    assert validate_decision(decision, config, as_of, evidence) == []

    reauthorization = copy.deepcopy(decision)
    reauthorization["rejectionReasons"] = []
    reauthorization["reason"] = "same frozen scenario reauthorized"
    assert validate_decision(
        reauthorization, config, as_of, evidence, previous_decision=decision
    ) == []

    bad_state = copy.deepcopy(decision)
    bad_state["state"] = "FLAT"
    assert "PREPARE requires state=PREPARED" in validate_decision(
        bad_state, config, as_of, evidence
    )

    unbacked = copy.deepcopy(decision)
    unbacked["scenario"]["rootOb"]["originTime"] = utc_text(START - 10800)
    assert any(
        "root origin is not backed" in error
        for error in validate_decision(unbacked, config, as_of, evidence)
    )

    valid_event = copy.deepcopy(decision)
    valid_event["watchEvents"] = [{
        "eventId": "root", "kind": "ROOT_APPROACH", "comparison": "CROSS_ABOVE",
        "price": 99.5, "sourceTf": "H1", "sourceTimeUtc": root_time,
        "validUntilUtc": utc_text(as_of + 3600),
    }]
    assert validate_decision(valid_event, config, as_of, evidence) == []

    arbitrary_event = copy.deepcopy(valid_event)
    arbitrary_event["watchEvents"][0]["price"] = 99.73
    assert any(
        "watch event ROOT_APPROACH price is not backed" in error
        for error in validate_decision(arbitrary_event, config, as_of, evidence)
    )

    arbitrary_zone = copy.deepcopy(decision)
    arbitrary_zone["scenario"]["rootOb"]["low"] = 99.73
    assert any(
        "root low is not an OHLC boundary" in error
        for error in validate_decision(arbitrary_zone, config, as_of, evidence)
    )


def test_order_validation_contract() -> None:
    as_of = START + 60
    trade_scenario = scenario()
    trade_order = order()
    evidence = [
        {"tf": "H1", "candles": [{
            "openTimeUtc": trade_scenario["rootOb"]["originTime"],
            "open": 100.5, "high": 100.8, "low": 99.5, "close": 100.2,
        }]},
        {"tf": "M5", "candles": [{
            "openTimeUtc": trade_scenario["refinementPath"][0]["originTime"],
            "open": 100.2, "high": 100.4, "low": 99.8, "close": 100.0,
        }]},
        {"tf": "M30", "candles": [{
            "openTimeUtc": trade_scenario["objective"]["sourceTime"],
            "open": 98.8, "high": 99.2, "low": 98.0, "close": 98.5,
        }]},
        {"tf": "M1", "candles": [
        {
            "openTimeUtc": trade_order["refinedTouchTimeUtc"],
            "open": 100.0, "high": 100.2, "low": 99.8, "close": 100.1,
            "spreadPrice": 0.01,
        }, {
            "openTimeUtc": trade_order["matureLiquiditySourceTimeUtc"],
            "open": 100.1, "high": 100.3, "low": 100.0, "close": 100.05,
            "spreadPrice": 0.01,
        },
        {
            "openTimeUtc": trade_order["chochReferenceSourceTimeUtc"],
            "open": 100.2, "high": 100.25, "low": 100.1, "close": 100.2,
            "spreadPrice": 0.01,
        }, {
            "openTimeUtc": trade_order["triggerProtectedSwingSourceTimeUtc"],
            "open": 100.1, "high": 100.3, "low": 100.0, "close": 100.2,
            "spreadPrice": 0.01,
        }, {
            "openTimeUtc": trade_order["sweepExtremeSourceTimeUtc"],
            "open": 100.2, "high": 100.4, "low": 100.0, "close": 100.1,
            "spreadPrice": 0.01,
        }, {
            "openTimeUtc": trade_order["executionOriginTime"],
            "open": 100.0, "high": 100.2, "low": 100.0, "close": 100.05,
            "spreadPrice": 0.01,
        }]},
    ]
    decision = {
        "schemaVersion": "1.5.0", "asOfUtc": utc_text(as_of), "phase": "TRIGGER",
        "action": "ORDER", "state": "PENDING", "scenario": trade_scenario,
        "candleQueries": [], "watchEvents": [],
        "nextReviewAtUtc": utc_text(as_of + 3600), "order": trade_order,
        "rejectionReasons": [], "reason": "contract test",
    }
    config = {
        "maximumPreparedReviewMinutes": 60,
        "maximumFlatReviewMinutes": 360,
        "point": 0.01,
        "brokerStopsLevelPrice": 0.0,
        "brokerSpecResolved": True,
    }
    assert validate_decision(decision, config, as_of, evidence) == []

    compact_order = {
        key: trade_order[key]
        for key in (
            "executionModel", "executionOriginTime", "executionLow",
            "executionHigh", "triggerLineage",
        )
    }
    compact_decision = copy.deepcopy(decision)
    compact_decision["order"] = compact_order
    normalize_numeric_claims_from_evidence(compact_decision, evidence, config)
    assert compact_decision["order"]["takeProfit"] == 98.0
    assert compact_decision["order"]["entry"] == 100.0
    assert abs(compact_decision["order"]["stopLoss"] - 100.51) < 1e-9
    compact_errors = validate_decision(compact_decision, config, as_of, evidence)
    assert any("could not be normalized" in error for error in compact_errors)

    stale = copy.deepcopy(decision)
    stale["order"]["lastReauthorizedAtUtc"] = utc_text(START)
    assert any(
        "lastReauthorizedAtUtc" in error
        for error in validate_decision(stale, config, as_of, evidence)
    )

    invented_execution = copy.deepcopy(decision)
    invented_execution["order"]["executionLow"] = 100.03
    invented_execution["order"]["entry"] = 100.03
    assert any(
        "executionLow is not an OHLC boundary" in error
        for error in validate_decision(invented_execution, config, as_of, evidence)
    )

    unsafe_buffer = copy.deepcopy(decision)
    unsafe_buffer["order"]["actualSpread"] = 0.05
    unsafe_buffer["order"]["slBuffer"] = 0.01
    assert any(
        "SL buffer is below" in error
        for error in validate_decision(unsafe_buffer, config, as_of, evidence)
    )

    previous = copy.deepcopy(decision)
    previous["phase"] = "REFINEMENT"
    previous["action"] = "PREPARE"
    previous["state"] = "PREPARED"
    previous["order"] = None
    changed_root = copy.deepcopy(decision)
    changed_root["scenario"]["rootOb"]["high"] = 100.8
    assert any(
        "frozen scenario field changed: rootOb" in error
        for error in validate_decision(
            changed_root, config, as_of, evidence, previous_decision=previous
        )
    )

    changed_lineage = copy.deepcopy(decision)
    changed_lineage["scenario"]["refinementPath"] = []
    transition_errors = validate_decision(
        changed_lineage, config, as_of, evidence, previous_decision=previous
    )
    assert "frozen refinement lineage was changed or removed" in transition_errors


def test_delivery_replacement_keep_is_reauthorization_not_recreation() -> None:
    as_of = START + 3600
    trade_scenario = scenario()
    replacement = order()
    replacement.update({
        "executionModel": "DELIVERY_FVG_REPLACEMENT",
        "entry": 100.0,
        "stopLoss": 99.0,
        "takeProfit": float(trade_scenario["objective"]["price"]),
        "executionLow": 99.9,
        "executionHigh": 100.0,
        "lastReauthorizedAtUtc": utc_text(as_of),
        "originalExecutionModel": "HTF_OB_REACTION_INTENT",
        "originalEntry": 99.8,
        "originalOrderCanceledAtUtc": utc_text(START),
        "deliveryFvgLeftTimeUtc": utc_text(START - 180),
        "deliveryFvgMiddleTimeUtc": utc_text(START - 120),
        "deliveryFvgRightTimeUtc": utc_text(START - 60),
        "deliveryFvgLow": 99.9,
        "deliveryFvgHigh": 100.0,
        "deliveryCausalObTimeUtc": utc_text(START - 240),
        "deliveryProtectedSwing": 99.7,
        "deliveryProtectedSwingTimeUtc": utc_text(START - 300),
        "deliveryFirstRetestRequired": True,
    })
    previous = {
        "schemaVersion": "1.5.0", "asOfUtc": utc_text(START),
        "phase": "PENDING_REVIEW", "action": "ORDER", "state": "PENDING",
        "scenario": copy.deepcopy(trade_scenario), "candleQueries": [],
        "watchEvents": [], "nextReviewAtUtc": utc_text(as_of),
        "order": copy.deepcopy(replacement), "rejectionReasons": [], "reason": "created",
    }
    previous["order"]["lastReauthorizedAtUtc"] = utc_text(START)
    current = copy.deepcopy(previous)
    current.update({"asOfUtc": utc_text(as_of), "reason": "keep"})
    current["order"]["lastReauthorizedAtUtc"] = utc_text(as_of)
    evidence = [
        {"tf": "H1", "candles": [{
            "openTimeUtc": trade_scenario["rootOb"]["originTime"],
            "open": 100.5, "high": 100.8, "low": 99.5, "close": 100.2,
        }]},
        {"tf": "M5", "candles": [{
            "openTimeUtc": trade_scenario["refinementPath"][0]["originTime"],
            "open": 100.2, "high": 100.4, "low": 99.8, "close": 100.0,
        }]},
        {"tf": "M30", "candles": [{
            "openTimeUtc": trade_scenario["objective"]["sourceTime"],
            "open": 98.8, "high": 99.2, "low": 98.0, "close": 98.5,
        }]},
    ]
    config = {
        "maximumPreparedReviewMinutes": 60, "maximumFlatReviewMinutes": 360,
        "point": 0.01, "brokerStopsLevelPrice": 0.0, "brokerSpecResolved": True,
    }
    errors = validate_decision(
        current, config, as_of, evidence, previous_decision=previous
    )
    assert not any("delivery replacement" in error for error in errors), errors
    assert not any("FVG confirmation" in error for error in errors), errors

    intent = {
        "executionModel": "HTF_OB_REACTION_INTENT", "intentOnly": True,
        "entry": 100.0, "stopLoss": 99.0,
        "takeProfit": float(trade_scenario["objective"]["price"]),
        "rootOriginTime": trade_scenario["rootOb"]["originTime"],
        "childOriginTime": trade_scenario["refinementPath"][-1]["originTime"],
        "objectiveSourceTime": trade_scenario["objective"]["sourceTime"],
        "actualSpread": 0.01, "brokerStopsLevelPrice": 0.0,
        "slBuffer": 0.01, "lastReauthorizedAtUtc": utc_text(START),
    }
    previous_intent = copy.deepcopy(previous)
    previous_intent["order"] = copy.deepcopy(intent)
    current_intent = copy.deepcopy(previous_intent)
    current_intent["asOfUtc"] = utc_text(as_of)
    current_intent["order"]["lastReauthorizedAtUtc"] = utc_text(as_of)
    intent_errors = validate_decision(
        current_intent, config, as_of, evidence, previous_decision=previous_intent
    )
    assert not any("triggerLineage" in error for error in intent_errors), intent_errors
    assert not any("ORDER could not be normalized" in error for error in intent_errors), intent_errors

    local_screening = copy.deepcopy(previous_intent)
    local_screening["_wakeEvent"] = "LOCAL_DELIVERY_FVG"
    preserved, selected = canonical_stage_decision(
        as_of=utc_text(as_of), phase="PENDING_REVIEW",
        payload={
            "action": "CANCEL", "fvgLeftBarId": None,
            "fvgMiddleBarId": None, "fvgRightBarId": None,
            "causalObBarId": None, "deliveryProtectedSwingBarId": None,
            "reason": "screening FVG is not causal",
        },
        previous=local_screening, compact={}, point=0.01,
        broker_stops=0.0, spread_price=0.01,
    )
    assert selected == []
    assert preserved["action"] == "ORDER" and preserved["state"] == "PENDING"
    assert preserved["order"]["executionModel"] == "HTF_OB_REACTION_INTENT"
    assert preserved["rejectionReasons"] == [
        "LOCAL_DELIVERY_FVG_REJECTED_SCENARIO_PRESERVED"
    ]


def test_watch_evidence_recovery_without_second_model_call() -> None:
    as_of = START + 60
    trade_scenario = scenario()
    evidence = [
        {"tf": "H1", "candles": [{
            "openTimeUtc": trade_scenario["rootOb"]["originTime"],
            "open": 100.5, "high": 100.8, "low": 99.5, "close": 100.2,
        }]},
        {"tf": "M5", "candles": [{
            "openTimeUtc": trade_scenario["refinementPath"][0]["originTime"],
            "open": 100.2, "high": 100.4, "low": 99.8, "close": 100.0,
        }]},
        {"tf": "M30", "candles": [{
            "openTimeUtc": trade_scenario["objective"]["sourceTime"],
            "open": 98.8, "high": 99.2, "low": 98.0, "close": 98.5,
        }]},
        {"tf": "M1", "candles": [{
            "openTimeUtc": utc_text(START),
            "open": 99.0, "high": 99.5, "low": 97.5, "close": 98.5,
            "spreadPrice": 0.01,
        }]},
    ]
    decision = {
        "schemaVersion": "1.5.0", "asOfUtc": utc_text(as_of),
        "phase": "TRIGGER", "action": "WAIT", "state": "ARMED",
        "scenario": trade_scenario, "candleQueries": [], "order": None,
        "watchEvents": [{
            "eventId": "sweep", "kind": "SWEEP_CANDIDATE",
            "comparison": "CROSS_ABOVE", "price": 99.0,
            "sourceTf": "M1", "sourceTimeUtc": utc_text(START),
            "validUntilUtc": utc_text(as_of + 3600),
        }],
        "nextReviewAtUtc": utc_text(as_of + 3600),
        "rejectionReasons": [], "reason": "wait for sweep",
    }
    config = {
        "maximumScenarioReviewMinutes": 360, "maximumFlatReviewMinutes": 360,
        "point": 0.01, "brokerStopsLevelPrice": 0.0, "brokerSpecResolved": True,
    }
    normalize_review_schedule(decision, config, as_of)
    adjustments = normalize_numeric_claims_from_evidence(decision, evidence, config)
    assert decision["watchEvents"][0]["price"] == 99.5
    assert any(item["reason"] == "SWEEP_CANDIDATE source wick" for item in adjustments)
    assert validate_decision(decision, config, as_of, evidence) == []

    point_drift = copy.deepcopy(decision)
    point_drift["watchEvents"][0]["price"] = 99.49
    adjustments = normalize_numeric_claims_from_evidence(point_drift, evidence, config)
    assert point_drift["watchEvents"][0]["price"] == 99.5
    assert any(item["reason"] == "SWEEP_CANDIDATE source wick" for item in adjustments)
    assert validate_decision(point_drift, config, as_of, evidence) == []


def test_v2_stage_contracts_and_barid_adapters() -> None:
    schemas = {
        stage: json.loads(path.read_text(encoding="utf-8"))
        for stage, path in STAGE_SCHEMAS.items()
    }
    scout_text = json.dumps(schemas["MAP_SCOUT"])
    assert '"price"' not in scout_text
    assert "refinement" not in scout_text.lower()
    assert "order" not in scout_text.lower()
    assert schemas["PENDING_REVIEW"]["properties"]["action"]["enum"] == [
        "KEEP", "REPLACE_DELIVERY_FVG", "CANCEL", "DATA_ERROR"
    ]
    assert "pending limit immediately" in (
        schemas["TRIGGER"]["properties"]["action"]["description"]
    )

    bars = {
        "H1": [{"barId": "H1:1", "time": "2024-08-22T08:00:00Z", "o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0, "spreadPoints": 2.0}],
        "M30": [{"barId": "M30:2", "time": "2024-08-22T07:30:00Z", "o": 96.0, "h": 98.0, "l": 95.0, "c": 97.0, "spreadPoints": 2.0}],
        "M15": [{"barId": "M15:3", "time": "2024-08-22T09:00:00Z", "o": 100.0, "h": 101.0, "l": 99.5, "c": 100.5, "spreadPoints": 2.0}],
        "M5": [
            {"barId": "M5:4", "time": "2024-08-22T10:00:00Z", "o": 100.2, "h": 101.0, "l": 100.0, "c": 100.8, "spreadPoints": 2.0},
            {"barId": "M5:10", "time": "2024-08-22T10:05:00Z", "o": 100.7, "h": 100.8, "l": 99.4, "c": 99.5, "spreadPoints": 2.0},
        ],
        "M1": [
            {"barId": "M1:5", "time": "2024-08-22T10:15:00Z", "o": 100.2, "h": 100.8, "l": 99.8, "c": 100.0, "spreadPoints": 2.0},
            {"barId": "M1:6", "time": "2024-08-22T10:16:00Z", "o": 100.0, "h": 100.8, "l": 100.0, "c": 100.5, "spreadPoints": 2.0},
            {"barId": "M1:7", "time": "2024-08-22T10:17:00Z", "o": 100.5, "h": 100.7, "l": 99.9, "c": 100.1, "spreadPoints": 2.0},
            {"barId": "M1:8", "time": "2024-08-22T10:18:00Z", "o": 100.1, "h": 101.0, "l": 100.0, "c": 100.5, "spreadPoints": 2.0},
            {"barId": "M1:9", "time": "2024-08-22T10:19:00Z", "o": 100.1, "h": 100.2, "l": 99.0, "c": 99.2, "spreadPoints": 2.0},
        ],
    }
    candidate = {
        "candidateId": "c1", "direction": "SHORT", "scope": "INTERNAL_ROTATION",
        "rootBarId": "H1:1", "objectiveBarId": "M30:2", "objectiveSide": "SSL",
        "objectiveType": "INTERNAL_LIQUIDITY", "reason": "test",
    }
    watched, selected = canonical_map_decision(
        as_of="2024-08-22T10:14:00Z",
        review={"action": "WATCH", "candidateId": "c1", "rootCausality": "root", "objectiveCausality": "objective", "competingLiquidity": "none", "reason": "wait"},
        candidates=[candidate], compact=bars,
    )
    assert watched["state"] == "WATCHING_MAP" and watched["action"] == "WATCH_MAP"
    assert selected == ["H1:1", "M30:2"]
    assert watched["scenario"]["objective"]["price"] == 95.0
    assert len(evidence_for_bars(bars, selected, 0.01)) == 2

    scout_misclassified = copy.deepcopy(candidate)
    scout_misclassified["scope"] = "EXTERNAL_CONTINUATION"
    scout_misclassified["objectiveType"] = "EXTERNAL_LIQUIDITY"
    reviewer_corrected, _ = canonical_map_decision(
        as_of="2024-08-22T10:14:00Z",
        review={
            "action": "APPROVE", "candidateId": "c1",
            "scope": "INTERNAL_ROTATION",
            "objectiveType": "INTERNAL_LIQUIDITY",
            "rootCausality": "root", "objectiveCausality": "objective",
            "competingLiquidity": "none", "reason": "reviewer correction",
        },
        candidates=[scout_misclassified], compact=bars,
    )
    assert reviewer_corrected["scenario"]["scope"] == "INTERNAL_ROTATION"
    assert reviewer_corrected["scenario"]["objective"]["type"] == "INTERNAL_LIQUIDITY"

    prepared = copy.deepcopy(watched)
    prepared["state"], prepared["action"] = "PREPARED", "PREPARE"
    refined, child_ids = canonical_stage_decision(
        as_of="2024-08-22T10:20:00Z", phase="REFINEMENT",
        payload={"action": "SELECT_CHILD", "childBarIds": ["M5:4"], "touchBarId": "M1:5", "candleQueries": [], "reason": "same displacement"},
        previous=prepared, compact=bars, point=0.01, broker_stops=0.0, spread_price=0.02,
    )
    assert child_ids == ["M5:4", "M1:5"]
    assert refined["scenario"]["refinementPath"][-1]["originTime"] == "2024-08-22T10:00:00Z"

    stale_prepared = copy.deepcopy(prepared)
    stale_prepared["scenario"]["frozenAtUtc"] = "2024-08-22T10:20:00Z"
    stale_refined, stale_ids = canonical_stage_decision(
        as_of="2024-08-22T10:20:00Z", phase="REFINEMENT",
        payload={"action": "SELECT_CHILD", "childBarIds": ["M5:4"], "touchBarId": "M1:5", "candleQueries": [], "reason": "stale touch"},
        previous=stale_prepared, compact=bars, point=0.01,
        broker_stops=0.0, spread_price=0.02,
    )
    assert stale_refined["state"] == "PREPARED"
    assert stale_refined["scenario"]["refinementPath"]
    assert not stale_refined["scenario"].get("refinedTouchTimeUtc")
    assert stale_ids == ["M5:4"]
    assert "IGNORED_HISTORICAL_TOUCH" in stale_refined["rejectionReasons"][0]
    assert stale_refined["order"]["executionModel"] == "HTF_OB_REACTION_INTENT"
    assert stale_refined["order"]["intentOnly"] is True
    assert stale_refined["order"]["entry"] == 100.0
    assert stale_refined["order"]["stopLoss"] == 101.02
    assert immediate_phase_transition("REFINEMENT", stale_refined) == "PENDING_REVIEW"
    assert validate_initial_causal_intent(
        stale_refined, {"point": 0.01}, parse_utc("2024-08-22T10:20:00Z")
    ) == []
    broken_intent = copy.deepcopy(stale_refined)
    broken_intent["order"]["stopLoss"] = 100.5
    assert "SHORT intent SL is not beyond child invalidation" in (
        validate_initial_causal_intent(
            broken_intent, {"point": 0.01}, parse_utc("2024-08-22T10:20:00Z")
        )
    )

    refined["state"] = "ARMED"
    ordered, trigger_ids = canonical_stage_decision(
        as_of="2024-08-22T10:20:00Z", phase="TRIGGER",
        payload={
            "action": "ORDER", "protectedSwingBarId": "M1:6",
            "matureLiquidityBarId": "M1:6", "sweepBarId": "M1:8",
            "sweepRecoveryBarId": "M1:8",
            "chochReferenceBarId": "M1:7", "chochBreakBarId": "M1:9",
            "executionBarId": "M1:8", "executionModel": "HTF_OB_REACTION",
            "candleQueries": [], "reason": "complete chain",
        },
        previous=refined, compact=bars, point=0.01, broker_stops=0.0, spread_price=0.02,
    )
    assert len(trigger_ids) == 7
    assert ordered["state"] == "PENDING" and ordered["order"]["takeProfit"] == 95.0
    assert ordered["order"]["slBuffer"] == 0.02

    normalized_execution, normalized_ids = canonical_stage_decision(
        as_of="2024-08-22T10:20:00Z", phase="TRIGGER",
        payload={
            "action": "ORDER", "protectedSwingBarId": "M1:6",
            "matureLiquidityBarId": "M1:6", "sweepBarId": "M1:8",
            "sweepRecoveryBarId": "M1:8",
            "chochReferenceBarId": "M1:7", "chochBreakBarId": "M1:9",
            "executionBarId": "M1:9", "executionModel": "HTF_OB_REACTION",
            "candleQueries": [], "reason": "wrong execution candle",
        },
        previous=refined, compact=bars, point=0.01,
        broker_stops=0.0, spread_price=0.02,
    )
    assert normalized_ids[-1] == "M1:8"
    assert normalized_execution["order"]["executionOriginTime"] == bars["M1"][3]["time"]

    trigger_contract, _ = load_stage_contract("TRIGGER")
    trigger_packet = {
        "asOfUtc": "2024-08-22T10:20:00Z", "phase": "TRIGGER",
        "images": [], "compactBars": bars,
    }
    trigger_prompt = stage_prompt(
        trigger_contract, trigger_packet, "TRIGGER", refined
    )
    assert "Never WAIT because a valid execution OB has not yet been retested" in trigger_prompt


def test_map_candidate_deterministic_ohlc_prefilter() -> None:
    short_candidate = {
        "candidateId": "short", "direction": "SHORT",
        "rootBarId": "M15:1", "objectiveBarId": "M15:1",
        "objectiveSide": "SSL",
    }
    bullish_root = {"o": 100.0, "c": 101.0}
    bearish_root = {"o": 101.0, "c": 100.0}
    lower_objective = {"h": 99.0, "l": 95.0}
    assert map_candidate_ohlc_rejection(
        short_candidate, bullish_root, lower_objective, 100.0
    ) is None
    allowed = {("M15:2", "SSL")}
    assert "structural-extremum" in str(map_candidate_ohlc_rejection(
        short_candidate, bullish_root, lower_objective, 100.0, allowed
    ))
    allowed.add(("M15:1", "SSL"))
    assert map_candidate_ohlc_rejection(
        short_candidate, bullish_root, lower_objective, 100.0, allowed
    ) is None
    assert "no later closed delivery" in str(map_candidate_ohlc_rejection(
        short_candidate, {**bullish_root, "l": 99.0, "h": 101.0},
        lower_objective, 100.0, allowed,
        compact={"M15": [{"barId": "M15:1", "c": 100.5}]},
    ))
    assert map_candidate_ohlc_rejection(
        short_candidate, {**bullish_root, "l": 99.0, "h": 101.0},
        lower_objective, 98.8, allowed,
        compact={"M15": [{"barId": "M15:1", "c": 100.5}]},
        local_map_wakeup={
            "candidateRootBarId": "M15:1", "directionHint": "SHORT",
        },
    ) is None
    assert map_candidate_ohlc_rejection(
        short_candidate, {**bullish_root, "l": 99.0, "h": 101.0},
        lower_objective, 100.0, allowed,
        compact={"M15": [
            {"barId": "M15:1", "c": 100.5},
            {"barId": "M15:2", "c": 98.8},
        ]},
    ) is None
    assert "opposite-color" in str(map_candidate_ohlc_rejection(
        short_candidate, bearish_root, lower_objective, 100.0
    ))
    stale = map_candidate_ohlc_rejection(
        {**short_candidate, "rootBarId": "M15:0"},
        {**bullish_root, "l": 99.0, "h": 101.0},
        lower_objective,
        98.0,
        allowed,
        compact={
            "M15": [
                {"barId": "M15:0", "c": 100.5},
                {"barId": "M15:900", "c": 98.0},
            ],
            "M1": [
                {"barId": "M1:900", "l": 97.0, "h": 98.5, "c": 98.0},
                {"barId": "M1:960", "l": 98.0, "h": 99.5, "c": 98.8},
            ],
        },
    )
    assert "no longer fresh" in str(stale)
    wrong_side = copy.deepcopy(short_candidate)
    wrong_side["objectiveSide"] = "BSL"
    assert "objective is not ahead" in str(map_candidate_ohlc_rejection(
        wrong_side, bullish_root, {"h": 99.0, "l": 95.0}, 100.0
    ))

    augmented = augment_candidates_with_local_root(
        [{
            **short_candidate, "candidateId": "scout",
            "rootBarId": "M15:1", "reason": "scout objective",
        }],
        {
            "kind": "LOCAL_MAP_ACTIVITY_CANDIDATE",
            "directionHint": "SHORT", "candidateRootBarId": "M15:2",
        },
    )
    assert [item["rootBarId"] for item in augmented] == ["M15:2", "M15:1"]
    assert augmented[1]["candidateId"] == "scout"
    assert augmented[0]["objectiveBarId"] == short_candidate["objectiveBarId"]
    assert augmented[0]["candidateId"] == "scout-LOCAL_ROOT"
    assert augmented[0]["localRootComparisonOnly"] is True
    expanded = augment_candidates_with_local_root(
        [{
            **short_candidate, "candidateId": "scout",
            "rootBarId": "M15:1", "objectiveBarId": "M15:near",
        }],
        {
            "kind": "LOCAL_ROOT_CHILD_DELIVERY_CANDIDATE",
            "directionHint": "SHORT", "candidateRootBarId": "M15:2",
        },
        liquidity_candidates=[
            {"barId": "M15:near", "side": "SSL", "price": 95.0, "status": "ACTIVE"},
            {"barId": "H1:far", "side": "SSL", "price": 90.0, "status": "ACTIVE"},
        ],
        current_bid=100.0,
        maximum_objectives=3,
    )
    assert any(
        item["rootBarId"] == "M15:2" and item["objectiveBarId"] == "H1:far"
        for item in expanded
    )
    opposite_only = augment_candidates_with_local_root(
        [{
            "candidateId": "wrong-long", "direction": "LONG",
            "scope": "EXTERNAL_CONTINUATION", "rootBarId": "M30:1",
            "objectiveBarId": "H1:upper", "objectiveSide": "BSL",
            "objectiveType": "EXTERNAL_LIQUIDITY", "reason": "wrong direction",
        }],
        {
            "kind": "LOCAL_ROOT_CHILD_DELIVERY_CANDIDATE",
            "directionHint": "SHORT", "candidateRootBarId": "M15:2",
        },
        liquidity_candidates=[
            {"barId": "M15:near", "side": "SSL", "price": 95.0, "status": "ACTIVE"},
            {"barId": "H1:far", "side": "SSL", "price": 90.0, "status": "ACTIVE"},
        ],
        current_bid=100.0,
        maximum_objectives=3,
    )
    local_short = [
        item for item in opposite_only
        if item["rootBarId"] == "M15:2" and item["direction"] == "SHORT"
    ]
    assert {item["objectiveBarId"] for item in local_short} == {"M15:near", "H1:far"}
    assert all(item["localRootComparisonOnly"] is True for item in local_short)
    watched = {
        "state": "WATCHING_MAP",
        "scenario": {"mapCandidate": {"rootBarId": "H1:old", "direction": "SHORT"}},
    }
    assert previous_map_candidate_for_review(watched, None) == watched["scenario"]["mapCandidate"]
    assert previous_map_candidate_for_review(
        watched,
        {
            "kind": "LOCAL_ROOT_CHILD_DELIVERY_CANDIDATE",
            "candidateRootBarId": "M15:new",
        },
    ) is None


def test_v2_prompt_size_regression_guard() -> None:
    secret = json.loads(
        (ROOT / "data/mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )
    config = secret["config"]
    assert config["model"] == config["reviewerModel"] == "gemini-3.5-flash-lite"
    assert output_token_limit(config, "scout") == 1600
    assert output_token_limit(config, "reviewer") == 2048
    assert phase_token_reserve(config, "MAP", 2) == 25744
    assert phase_token_reserve(config, "TRIGGER", 1) == 20096
    assert 133304 + phase_token_reserve(config, "MAP", 2) <= 180000
    as_of = "2024-08-22T10:20:00Z"
    fixture_warmup = "2024-05-01T00:00:00Z"
    dataset = ROOT / str(config["dataset"])
    packet = {
        "symbol": config["symbol"], "asOfUtc": as_of, "phase": "MAP",
        "lastClosedM1": {
            "openTimeUtc": "2024-08-22T10:19:00Z",
            "open": 2508.27, "high": 2508.27,
            "low": 2507.60, "close": 2507.67,
        },
        "spreadPrice": 0.27,
        "brokerStopsLevelPrice": float(config["brokerStopsLevelPrice"]),
        "images": [{"mode": "map", "path": "fixture.png", "sha256": "fixture"}],
        "candleEvidence": [], "localTriggerWakeup": None, "futureHidden": True,
    }
    map_bars = compact_bars(
        dataset, fixture_warmup, as_of,
        limits={"H1": 24, "M30": 32, "M15": 32, "M1": 120},
    )
    packet["compactBars"] = bars_for_prompt(
        map_bars, tail_limits={"H1": 24, "M30": 32, "M15": 32, "M1": 15}
    )
    packet["structuralLiquidityCandidates"] = structural_liquidity_table(
        structural_liquidity_candidates(map_bars, maximum=32)
    )
    contract, _ = load_stage_contract("MAP")
    scout_prompt, scout_metrics = bounded_map_scout_prompt(contract, packet, config)
    assert scout_metrics["promptBytes"] <= 10000
    assert packet["structuralLiquidityCandidates"]["data"]
    assert (
        packet["structuralLiquidityCandidates"]["omittedCount"]
        < packet["structuralLiquidityCandidates"]["totalCount"]
    )

    oversized_packet = copy.deepcopy(packet)
    oversized_packet["paddingForBudgetRegression"] = "x" * 400
    _, bounded_metrics = bounded_map_scout_prompt(contract, oversized_packet, config)
    assert bounded_metrics["promptBytes"] <= 12000
    assert oversized_packet["structuralLiquidityCandidates"]["omittedCount"] > 0

    candidate = {
        "candidateId": "truth-014", "direction": "SHORT",
        "scope": "INTERNAL_ROTATION", "rootBarId": "M15:1724320800",
        "objectiveBarId": "M30:1724311800", "objectiveSide": "SSL",
        "objectiveType": "INTERNAL_LIQUIDITY", "reason": "fixture",
        "resolvedRootOhlc": resolve_bar(map_bars, "M15:1724320800"),
        "resolvedObjectiveOhlc": resolve_bar(map_bars, "M30:1724311800"),
    }
    review_prompt = map_review_prompt(contract, packet, [candidate], None)
    assert enforce_prompt_size(review_prompt, config, "MAP_REVIEW")["promptBytes"] < 6000
    review_stress_candidates = []
    for index in range(6):
        stressed = copy.deepcopy(candidate)
        stressed["candidateId"] = f"stress-{index}"
        stressed["reason"] = "causal explanation " * 100
        review_stress_candidates.append(stressed)
    stressed_review_prompt = map_review_prompt(
        contract, packet, review_stress_candidates, None
    )
    assert enforce_prompt_size(
        stressed_review_prompt, config, "MAP_REVIEW"
    )["promptBytes"] <= 8000

    mapped, _ = canonical_map_decision(
        as_of=as_of,
        review={
            "action": "APPROVE", "candidateId": "truth-014",
            "rootCausality": "fixture", "objectiveCausality": "fixture",
            "competingLiquidity": "none", "reason": "fixture",
        },
        candidates=[candidate], compact=map_bars,
    )
    stage_limits = {
        "REFINEMENT": {"M30": 16, "M15": 32, "M5": 72, "M1": 60},
        "TRIGGER": {"M15": 12, "M5": 30, "M1": 90},
        "PENDING_REVIEW": {"H1": 12, "M15": 24, "M5": 36, "M1": 30},
    }
    expected_maximums = {
        "REFINEMENT": 12000, "TRIGGER": 14000, "PENDING_REVIEW": 12000,
    }
    for phase, limits in stage_limits.items():
        stage_packet = copy.deepcopy(packet)
        stage_packet["phase"] = phase
        stage_packet.pop("structuralLiquidityCandidates", None)
        stage_packet["compactBars"] = bars_for_prompt(compact_bars(
            dataset, fixture_warmup, as_of, limits=limits,
        ))
        if phase == "REFINEMENT":
            stage_bars = compact_bars(
                dataset, fixture_warmup, as_of, limits=limits,
            )
            stage_packet["refinementCandidates"] = refinement_candidate_table(
                refinement_candidates(stage_bars, mapped["scenario"])
            )
        stage_contract, _ = load_stage_contract(phase)
        prompt, metrics = bounded_stage_prompt(
            stage_contract, stage_packet, phase, mapped, config
        )
        assert metrics["promptBytes"] < expected_maximums[phase]

        oversized_packet = copy.deepcopy(stage_packet)
        oversized_packet["paddingForBudgetRegression"] = "x" * 600
        _, bounded_metrics = bounded_stage_prompt(
            stage_contract, oversized_packet, phase, mapped, config
        )
        assert bounded_metrics["promptBytes"] <= int(
            config[PROMPT_LIMIT_CONFIG_KEYS[phase]]
        )


def test_resume_counts_provider_calls_not_decision_rows() -> None:
    rows = [
        {"event": "AI_DECISION", "providerCalls": [{"role": "scout"}, {"role": "reviewer"}]},
        {"event": "AI_DECISION", "providerCalls": [{"role": "reviewer"}]},
        {"event": "LOCAL_MAP_WAKEUP"},
    ]
    assert provider_calls_in_ledger(rows) == 3


def test_terminal_cancel_cannot_revive_scenario_on_resume() -> None:
    canceled = {
        "asOfUtc": "2025-10-28T21:15:00Z",
        "phase": "PENDING_REVIEW",
        "action": "CANCEL",
        "state": "CANCELED",
        "scenario": {"scenarioId": "must-not-revive"},
        "watchEvents": [{"eventId": "expired-source"}],
    }
    previous, lifecycle_as_of, cleared = clear_terminal_resume_decision(
        canceled, None
    )
    assert cleared is True
    assert previous is None
    assert lifecycle_as_of == "2025-10-28T21:15:00Z"

    active = {**canceled, "action": "KEEP", "state": "PENDING"}
    previous, _, cleared = clear_terminal_resume_decision(active, None)
    assert cleared is False
    assert previous == active


def test_gemini_structured_payload_ignores_thinking_parts() -> None:
    raw = {
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [
                {"thought": True, "text": "I should compare three scopes first."},
                {"text": '{"phase":"MAP_REVIEW","action":"REJECT"}'},
            ]},
        }]
    }
    assert extract_structured_payload(raw) == {
        "phase": "MAP_REVIEW", "action": "REJECT"
    }
    fenced = {
        "candidates": [{"content": {"parts": [
            {"text": '```json\n{"phase":"MAP_SCOUT","action":"NO_CANDIDATE"}\n```'}
        ]}}]
    }
    assert extract_structured_payload(fenced)["phase"] == "MAP_SCOUT"


def test_v2_aug21_agents_compliant_truth_is_reachable_from_raw_ohlc() -> None:
    secret = json.loads(
        (ROOT / "data/mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )
    config = secret["config"]
    dataset = ROOT / str(config["dataset"])
    rates = np.load(dataset, allow_pickle=False)["rates"]
    bars = compact_bars(
        dataset, "2025-08-18T00:00:00Z", "2025-08-21T17:46:00Z",
        limits={"H1": 200, "M30": 300, "M15": 600, "M5": 1800, "M1": 1500},
    )
    liquidity = structural_liquidity_candidates(bars)
    assert any(
        item["barId"] == "M15:1755784800"
        and item["side"] == "SSL"
        and item["price"] == 3325.03
        for item in liquidity
    )


    candidate = {
        "candidateId": "agents-regression-c-corrected", "direction": "SHORT",
        "scope": "INTERNAL_ROTATION", "rootBarId": "M30:1755792000",
        "objectiveBarId": "M15:1755784800", "objectiveSide": "SSL",
        "objectiveType": "INTERNAL_LIQUIDITY", "reason": "AGENTS regression C corrected chain",
    }
    mapped, map_ids = canonical_map_decision(
        as_of="2025-08-21T17:00:00Z",
        review={
            "action": "APPROVE", "candidateId": "agents-regression-c-corrected",
            "scope": "INTERNAL_ROTATION",
            "objectiveType": "INTERNAL_LIQUIDITY",
            "rootCausality": "fixture", "objectiveCausality": "fixture",
            "competingLiquidity": "3325.03 is the first internal SSL",
            "reason": "EXTERNAL_CONTINUATION INTERNAL_ROTATION EXTERNAL_REVERSAL compared",
        },
        candidates=[candidate], compact=bars,
    )
    evidence = evidence_for_bars(bars, map_ids, float(config["point"]))
    assert validate_decision(mapped, config, parse_utc(mapped["asOfUtc"]), evidence) == []

    child_candidates = refinement_candidates(bars, mapped["scenario"])
    assert any(
        item["barId"] == "M15:1755792900"
        for item in child_candidates
    )
    assert any(
        item["barId"] == "M5:1755793800"
        and item["deliveryBarId"] == "M5:1755794400"
        for item in child_candidates
    )
    assert not any(
        item["barId"] == "M5:1755792300"
        for item in child_candidates
    )
    try:
        canonical_stage_decision(
            as_of="2025-08-21T17:00:00Z", phase="REFINEMENT",
            payload={
                "action": "SELECT_CHILD",
                "childBarIds": ["M30:1755792000"],
                "touchBarId": None, "candleQueries": [], "reason": "invalid root reuse",
            },
            previous=mapped, compact=bars, point=float(config["point"]),
            broker_stops=float(config["brokerStopsLevelPrice"]), spread_price=0.38,
        )
    except ValueError as exc:
        assert "root/non-candidate" in str(exc)
    else:
        raise AssertionError("root candle was accepted as its own refinement child")
    try:
        canonical_stage_decision(
            as_of="2025-08-21T17:00:00Z", phase="REFINEMENT",
            payload={
                "action": "SELECT_CHILD",
                "childBarIds": ["M15:1755792900", "M15:1755792000"],
                "touchBarId": None, "candleQueries": [], "reason": "invalid same-TF path",
            },
            previous=mapped, compact=bars, point=float(config["point"]),
            broker_stops=float(config["brokerStopsLevelPrice"]), spread_price=0.38,
        )
    except ValueError as exc:
        assert (
            "one candidate per timeframe" in str(exc)
            or "root/non-candidate" in str(exc)
        )
    else:
        raise AssertionError("two competing M15 candidates were accepted as one path")

    refined, refinement_ids = canonical_stage_decision(
        as_of="2025-08-21T17:30:00Z", phase="REFINEMENT",
        payload={
            "action": "SELECT_CHILD",
            "childBarIds": ["M15:1755792900", "M5:1755793800"],
            "touchBarId": "M1:1755797400", "candleQueries": [],
            "reason": "same Aug 21 bearish displacement lineage",
        },
        previous=mapped, compact=bars, point=float(config["point"]),
        broker_stops=float(config["brokerStopsLevelPrice"]), spread_price=0.38,
    )
    evidence.extend(evidence_for_bars(bars, refinement_ids, float(config["point"])))
    assert refined["state"] == "ARMED"
    assert validate_decision(
        refined, config, parse_utc(refined["asOfUtc"]), evidence, mapped
    ) == []

    ordered, trigger_ids = canonical_stage_decision(
        as_of="2025-08-21T17:46:00Z", phase="TRIGGER",
        payload={
            "action": "ORDER", "protectedSwingBarId": "M1:1755797880",
            "matureLiquidityBarId": "M1:1755793860",
            "sweepBarId": "M1:1755797880",
            "sweepRecoveryBarId": "M1:1755797940",
            "chochReferenceBarId": "M1:1755796800",
            "chochBreakBarId": "M1:1755798300",
            "executionBarId": "M1:1755798120",
            "executionModel": "HTF_OB_REACTION", "candleQueries": [], "reason": "fixture",
        },
        previous=refined, compact=bars, point=float(config["point"]),
        broker_stops=float(config["brokerStopsLevelPrice"]), spread_price=0.38,
    )
    evidence.extend(evidence_for_bars(bars, trigger_ids, float(config["point"])))
    assert validate_decision(
        ordered, config, parse_utc(ordered["asOfUtc"]), evidence, refined
    ) == []
    assert float(ordered["order"]["entry"]) == 3343.94
    assert abs(float(ordered["order"]["stopLoss"]) - 3348.37) <= 0.01
    assert float(ordered["order"]["takeProfit"]) == 3325.03
    assert ordered["order"]["sweepRecoveryTimeUtc"] == "2025-08-21T17:39:00Z"

    replay_slice = rates[
        (rates["time"] >= parse_utc("2025-08-21T15:30:00Z"))
        & (rates["time"] < parse_utc("2025-08-21T17:46:00Z"))
    ]
    resume_cursor = int(np.where(
        replay_slice["time"] == parse_utc("2025-08-21T17:44:00Z")
    )[0][0])
    wake_index, wake = find_local_trigger_wakeup(
        replay_slice, resume_cursor, len(replay_slice) - 1, "SHORT",
        {
            "point": float(config["point"]),
            "localTriggerWakeupEnabled": True,
            "localTriggerLookbackBars": int(config.get("localTriggerLookbackBars", 90)),
            "localTriggerMinimumReactionBars": 1,
        },
        parse_utc("2025-08-21T17:12:00Z"),
    )
    assert wake_index is not None and wake["detectedAtUtc"] == "2025-08-21T17:46:00Z"
    assert any(
        item["liquiditySourceTimeUtc"] == "2025-08-21T16:31:00Z"
        and item["sweepTimeUtc"] == "2025-08-21T17:38:00Z"
        and item["sweepRecoveryTimeUtc"] == "2025-08-21T17:39:00Z"
        and item["matureLiquidityBarId"] == "M1:1755793860"
        and item["chochReferenceBarId"] == "M1:1755796800"
        and item["chochBreakBarId"] == "M1:1755798300"
        and item["executionBarId"] == "M1:1755798120"
        for item in wake["candidates"]
    )


def test_reaction_trap_liquidity_survives_wide_previous_wick() -> None:
    secret = json.loads(
        (ROOT / "data/mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )
    config = secret["config"]
    dataset = ROOT / str(config["dataset"])
    bars = compact_bars(
        dataset, "2025-10-20T00:00:00Z", "2025-10-29T09:48:00Z",
        limits={"H1": 200, "M30": 300, "M15": 600, "M5": 1800, "M1": 1500},
    )
    liquidity = structural_liquidity_candidates(bars)
    assert any(
        item["barId"] == "M15:1761727500"
        and item["side"] == "SSL"
        and item["price"] == 3974.63
        and "REACTION_TRAP" in item["candidateKind"]
        for item in liquidity
    )


def test_active_objective_survives_recent_candidate_cap() -> None:
    secret = json.loads(
        (ROOT / "data/mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )
    config = secret["config"]
    dataset = ROOT / str(config["dataset"])
    bars = compact_bars(
        dataset, config["warmupStartUtc"], "2025-10-31T05:15:00Z",
        limits={"H1": 96, "M30": 192, "M15": 384, "M1": 5760},
    )
    liquidity = structural_liquidity_candidates(bars, maximum=32)
    assert any(
        item["barId"] == "H1:1761832800"
        and item["side"] == "SSL"
        and item["price"] == 3960.87
        and item["status"] == "ACTIVE"
        for item in liquidity
    )
    assert not any(
        item["barId"] == "M30:1761850800"
        and item["side"] == "SSL"
        and item["status"] == "ACTIVE"
        for item in liquidity
    )


def test_post_sweep_live_swing_can_be_choch_reference() -> None:
    secret = json.loads(
        (ROOT / "data/mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )
    config = secret["config"]
    rates = np.load(ROOT / str(config["dataset"]), allow_pickle=True)["rates"]
    start = int(np.flatnonzero(rates["time"] == 1761926580)[0])
    end = int(np.flatnonzero(rates["time"] == 1761927120)[0])
    wake_index, wake = find_local_trigger_wakeup(
        rates, start, end, "SHORT", config,
        refined_touch_time=1761926580,
    )
    assert wake_index is not None and wake is not None
    assert wake["detectedAtUtc"] == "2025-10-31T16:12:00Z"
    assert any(
        item["sweepTimeUtc"] == "2025-10-31T16:07:00Z"
        and item["sweepRecoveryTimeUtc"] == "2025-10-31T16:08:00Z"
        and item["chochReferenceTimeUtc"] == "2025-10-31T16:09:00Z"
        and item["chochReferencePrice"] == 4020.84
        for item in wake["candidates"]
    )


def test_current_map_root_is_excluded_from_challenger_wakeup() -> None:
    decision = {
        "_consumedMapWakeRoots": ["M15:older"],
        "scenario": {"mapCandidate": {"rootBarId": "M15:current"}},
    }
    assert map_root_exclusions(decision) == {"M15:older", "M15:current"}


def test_aug21_local_map_wakeup_is_bounded_and_includes_truth_root() -> None:
    secret = json.loads(
        (ROOT / "data/mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )
    config = dict(secret["config"])
    config["localFlatDeliveryWakeupEnabled"] = False
    config["localRootChildWakeupEnabled"] = False
    payload = np.load(ROOT / str(config["dataset"]), allow_pickle=True)
    rates = payload["rates"]
    start = int(np.flatnonzero(
        rates["time"] + 60 >= parse_utc("2025-08-21T00:00:00Z")
    )[0])
    end = int(np.flatnonzero(
        rates["time"] + 60 >= parse_utc("2025-08-22T00:00:00Z")
    )[0]) - 1

    cursor = start
    consumed: set[str] = set()
    wakeups: list[dict[str, object]] = []
    while True:
        index, wakeup = find_local_map_wakeup(
            rates, cursor, end, config, excluded_root_ids=consumed
        )
        if index is None or wakeup is None:
            break
        wakeups.append(wakeup)
        consumed.add(str(wakeup["candidateRootBarId"]))
        cursor = index

    assert len(wakeups) <= 3
    truth = next(
        item for item in wakeups
        if item["candidateRootBarId"] == "M30:1755792000"
    )
    assert truth["detectedAtUtc"] == "2025-08-21T17:00:00Z"
    assert truth["deliveryBarId"] == "M30:1755793800"
    assert truth["directionHint"] == "SHORT"

    prepared_cursor = int(np.flatnonzero(
        rates["time"] + 60 >= parse_utc("2025-08-21T15:25:00Z")
    )[0])
    challenger_index, challenger_event = next_decision_index(
        rates,
        prepared_cursor,
        {
            "state": "PREPARED",
            "scenario": {},
            "nextReviewAtUtc": "2025-08-21T21:25:00Z",
            "watchEvents": [],
        },
        config,
    )
    assert challenger_event == "LOCAL_MAP_ACTIVITY"
    assert utc_text(int(rates[challenger_index]["time"]) + 60) == "2025-08-21T17:00:00Z"
    armed_config = {**config, "localTriggerWakeupEnabled": False}
    armed_index, armed_event = next_decision_index(
        rates,
        prepared_cursor,
        {
            "state": "ARMED",
            "scenario": {"direction": "SHORT"},
            "nextReviewAtUtc": "2025-08-21T21:25:00Z",
            "watchEvents": [],
        },
        armed_config,
    )
    assert armed_event == "LOCAL_MAP_ACTIVITY"
    assert utc_text(int(rates[armed_index]["time"]) + 60) == "2025-08-21T17:00:00Z"


def test_flat_delivery_alarm_cannot_retroactively_prepare_map() -> None:
    root_time = "2025-10-28T01:00:00Z"
    objective_time = "2025-10-27T22:00:00Z"
    compact = {
        "M15": [{
            "barId": f"M15:{parse_utc(root_time)}", "time": root_time,
            "o": 3990.0, "h": 3991.5, "l": 3982.8, "c": 3985.0,
        }],
        "M30": [{
            "barId": f"M30:{parse_utc(objective_time)}", "time": objective_time,
            "o": 3995.0, "h": 4000.1, "l": 3990.0, "c": 3998.0,
        }],
        "M1": [{
            "barId": f"M1:{parse_utc('2025-10-28T01:22:00Z')}",
            "time": "2025-10-28T01:22:00Z",
            "o": 3992.0, "h": 3996.0, "l": 3992.0, "c": 3995.0,
        }],
    }
    candidate = {
        "candidateId": "C1", "direction": "LONG", "scope": "INTERNAL_ROTATION",
        "rootBarId": f"M15:{parse_utc(root_time)}",
        "objectiveBarId": f"M30:{parse_utc(objective_time)}",
        "objectiveSide": "BSL", "objectiveType": "INTERNAL_LIQUIDITY",
    }
    decision, _ = canonical_map_decision(
        as_of="2025-10-28T01:23:00Z",
        review={"action": "APPROVE", "candidateId": "C1"},
        candidates=[candidate], compact=compact,
        delivery_wakeup={
            "kind": "LOCAL_FLAT_DELIVERY_CANDIDATE", "directionHint": "LONG",
            "candidateRootBarId": candidate["rootBarId"],
        },
    )
    assert decision["state"] == "WATCHING_MAP"
    assert decision["action"] == "WATCH_MAP"
    assert "_deliveryWakeup" not in decision["scenario"]


def test_oct28_root_child_source_wakes_before_execution_fvg() -> None:
    secret = json.loads(
        (ROOT / "data/mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )
    config = secret["config"]
    config = {**config, "localRootChildWakeupEnabled": True}
    rates = np.load(ROOT / str(config["dataset"]), allow_pickle=True)["rates"]
    # The causal M15 03:45 root and M5 04:00 child must wake MAP during
    # directional delivery and before the 04:12/04:14 execution FVG is known.
    start = int(np.flatnonzero(
        rates["time"] == parse_utc("2025-10-28T04:00:00Z")
    )[0])
    end = int(np.flatnonzero(
        rates["time"] == parse_utc("2025-10-28T04:14:00Z")
    )[0])
    wakeup = next(
        (
            item
            for index in range(start, end + 1)
            if (item := root_child_delivery_candidate_at(rates, index, config))
            and item["candidateRootBarId"]
            == f"M15:{parse_utc('2025-10-28T03:45:00Z')}"
        ),
        None,
    )
    assert wakeup is not None
    assert parse_utc(wakeup["detectedAtUtc"]) < parse_utc("2025-10-28T04:15:00Z")
    assert wakeup["directionHint"] == "SHORT"
    assert wakeup["candidateRootBarId"] == f"M15:{parse_utc('2025-10-28T03:45:00Z')}"
    assert wakeup["candidateChildBarId"] == f"M5:{parse_utc('2025-10-28T04:00:00Z')}"


def main() -> int:
    active_manifest = ROOT / "mentor_context_pack/api_contracts/v4_manifest.json"
    if active_manifest.exists():
        pipeline = str(
            json.loads(active_manifest.read_text(encoding="utf-8-sig")).get(
                "pipelineVersion", ""
            )
        )
        if pipeline.startswith("5.0-"):
            print(
                "LEGACY_MENTOR_AI_REPLAY_CONTRACT_TEST_NOT_ACTIVE "
                f"pipeline={pipeline}"
            )
            return 0
    json.loads((ROOT / "mentor_context_pack/schemas/replay_decision.schema.json").read_text(encoding="utf-8"))
    test_prompt_is_canonical_and_readable()
    test_query_budget_becomes_no_trade()
    test_flat_review_respects_bounded_analyst_schedule()
    test_generic_map_rejection_is_audited_and_never_retried_next_minute()
    test_reviewed_map_approach_is_consumed_once()
    test_refinement_arm_waits_for_local_trigger_event()
    test_local_trigger_wakeup_recovers_aug22_chain_without_m1_api_polling()
    test_marketable_limit_is_rejected()
    test_pending_lifecycle()
    test_watch_events_are_edges_not_persistent_states()
    test_source_invalidation_waits_for_source_timeframe_body_close()
    test_child_touch_is_armed_locally_without_provider()
    test_orchestrator_state_transitions()
    test_all_phase_action_transitions_are_engine_owned()
    test_map_validation_contract()
    test_order_validation_contract()
    test_delivery_replacement_keep_is_reauthorization_not_recreation()
    test_watch_evidence_recovery_without_second_model_call()
    test_v2_stage_contracts_and_barid_adapters()
    test_map_candidate_deterministic_ohlc_prefilter()
    test_v2_prompt_size_regression_guard()
    test_resume_counts_provider_calls_not_decision_rows()
    test_terminal_cancel_cannot_revive_scenario_on_resume()
    test_gemini_structured_payload_ignores_thinking_parts()
    test_v2_aug21_agents_compliant_truth_is_reachable_from_raw_ohlc()
    test_reaction_trap_liquidity_survives_wide_previous_wick()
    test_active_objective_survives_recent_candidate_cap()
    test_post_sweep_live_swing_can_be_choch_reference()
    test_current_map_root_is_excluded_from_challenger_wakeup()
    test_aug21_local_map_wakeup_is_bounded_and_includes_truth_root()
    test_flat_delivery_alarm_cannot_retroactively_prepare_map()
    test_oct28_root_child_source_wakes_before_execution_fvg()
    print("MENTOR_AI_REPLAY_CONTRACT_TESTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
