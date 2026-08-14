from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_ground_truth_v2 import (
    snapshot_family,
    validate_no_trade_audit_conclusion,
    validate_scenario_authority_at_order,
    validate_global_risk_exposure,
    with_lossless_role_evidence,
)
from scripts.audit_ground_truth_v2_codex import semantic_signature
from scripts.mentor_ai_replay_v4 import ScriptedProvider, V4Runner
from scripts.mentor_replay_v4_core import (
    V4ContractError,
    advance_pending,
    build_plan_packet,
    delivery_candidate_order,
    new_runtime,
    parse_utc,
    select_objective_from_family,
    utc_text,
)
from scripts.test_mentor_ai_replay_v4 import (
    BASE,
    PLAN_AT,
    TOUCH_TIME,
    frozen_scenario,
    synthetic_market,
    with_synthetic_atomic_family,
)


def runner_for(runtime: dict) -> tuple[tempfile.TemporaryDirectory, V4Runner]:
    temporary = tempfile.TemporaryDirectory()
    market = synthetic_market()
    runner = V4Runner(
        config={
            "symbol": "GOLD",
            "point": 0.01,
            "brokerStopsLevelPrice": 0.0,
            "maximumRiskSlots": 3,
            "maximumScenarioSlots": 256,
        },
        market=market,
        run_dir=Path(temporary.name),
        provider=ScriptedProvider([]),
        runtime=runtime,
    )
    return temporary, runner


def test_lossless_packet_contains_every_htf_role() -> None:
    market = synthetic_market()
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    packet = with_lossless_role_evidence(packet, market, PLAN_AT)
    assert packet["roleEvidenceAudit"]["missingRoleIds"] == []
    supplied = {
        row[0]
        for rows in packet["bars"]["data"].values()
        for row in rows
    }
    assert set(packet["roleEvidenceAudit"]["requiredRoleIds"]) <= supplied


def test_ground_truth_cannot_freeze_with_a_missed_no_trade_family() -> None:
    validate_no_trade_audit_conclusion({
        "dayUtc": "2026-06-01",
        "conclusion": "NO_MISSED_PROTOCOL_COMPLETE_FAMILY",
    })
    try:
        validate_no_trade_audit_conclusion({
            "dayUtc": "2026-06-02",
            "conclusion": "POTENTIAL_MISSED_FAMILY",
        })
    except V4ContractError as exc:
        assert "potentially missed" in str(exc)
    else:
        raise AssertionError("a missed no-trade family did not block Ground Truth")


def test_stateful_repeat_signature_ignores_wording_but_not_authority() -> None:
    first = {
        "candidateId": "candidate",
        "action": "APPROVE_REPLACEMENT",
        "sourceEpisodeContinuity": "PASS",
        "ownerObjectiveContinuity": "PASS",
        "meaningfulStructureTransfer": "PASS",
        "causalFvgAndOb": "PASS",
        "firstRetestEligibility": "PASS",
        "reason": "first wording",
    }
    second = {**first, "reason": "different wording"}
    assert semantic_signature("DELIVERY_REVIEW", first) == semantic_signature(
        "DELIVERY_REVIEW", second
    )
    second["meaningfulStructureTransfer"] = "FAIL"
    assert semantic_signature("DELIVERY_REVIEW", first) != semantic_signature(
        "DELIVERY_REVIEW", second
    )


def test_objective_family_uses_first_live_member_at_least_one_r() -> None:
    market = synthetic_market()
    h1 = market.frames["H1"]
    later_index = next(
        index for index, value in enumerate(h1.time)
        if int(value) == BASE
    )
    h1.high[later_index] = 130.0
    scenario = frozen_scenario(market)
    scenario["objectiveFamily"] = {
        "objectiveFamilyId": "objective-family-test",
        "orderedMembers": [
            {
                "barId": scenario["objective"]["barId"],
                "destinationContext": {"historyTier": "CURRENT_STRUCTURE"},
            },
            {
                "barId": f"H1:{BASE}",
                "destinationContext": {"historyTier": "LONG_TERM_H1"},
            },
        ],
    }
    selected, intermediate = select_objective_from_family(
        market, scenario, entry=119.0, stop=117.0, as_of=PLAN_AT
    )
    assert selected["barId"] == f"H1:{BASE}"
    assert selected["plannedR"] == 5.5
    assert [item["barId"] for item in intermediate] == [
        scenario["objective"]["barId"]
    ]


def test_watch_lanes_are_free_but_pending_and_filled_stop_at_three_r() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    runtime = new_runtime(0)
    runtime["scenarioSlots"] = [
        {
            "slotId": "watch",
            "sourceFamilyKey": "watch-family",
            "state": "PLANNED",
            "scenario": copy.deepcopy(scenario),
            "reactionMonitor": None,
            "triggerWatch": None,
            "order": None,
            "position": None,
            "shadowDeliveryCandidates": [],
            "terminalAtUtc": None,
        },
        *[
            {
                "slotId": f"pending-{index}",
                "sourceFamilyKey": f"family-{index}",
                "state": "PENDING",
                "scenario": copy.deepcopy(scenario),
                "reactionMonitor": None,
                "triggerWatch": {"armed": True},
                "order": {"direction": "LONG"},
                "position": None,
                "shadowDeliveryCandidates": [],
                "terminalAtUtc": None,
            }
            for index in range(2)
        ],
    ]
    runtime["openPositions"] = [{
        "bookId": "book-one",
        "sourceFamilyKey": "family-filled",
        "executionSignalKey": "execution-filled",
        "scenario": copy.deepcopy(scenario),
        "order": {"direction": "LONG"},
        "position": {"direction": "LONG"},
    }]
    temporary, runner = runner_for(runtime)
    try:
        assert runner.risk_slot_count() == 3
        assert runner.risk_order_block_reason(
            {"direction": "LONG"}, scenario
        ) == "CAPACITY_MAX_THREE_RISK_SLOTS"
        runtime["scenarioSlots"] = runtime["scenarioSlots"][:1]
        assert runner.risk_slot_count() == 1
        assert runner.risk_order_block_reason(
            {"direction": "SHORT"}, scenario
        ) == "OPPOSITE_DIRECTION_RISK_EXISTS"
    finally:
        temporary.cleanup()


def test_frozen_ground_truth_rechecks_capacity_and_opposite_exposure() -> None:
    base = {
        "direction": "LONG",
        "orderCreatedAtUtc": "2026-06-01T00:00:00Z",
        "closedAtUtc": "2026-06-01T04:00:00Z",
    }
    validate_global_risk_exposure([
        {**base, "executionId": "one"},
        {**base, "executionId": "two", "orderCreatedAtUtc": "2026-06-01T01:00:00Z"},
        {**base, "executionId": "three", "orderCreatedAtUtc": "2026-06-01T02:00:00Z"},
    ])
    for invalid in (
        [
            {**base, "executionId": "one"},
            {**base, "executionId": "two", "orderCreatedAtUtc": "2026-06-01T01:00:00Z"},
            {**base, "executionId": "three", "orderCreatedAtUtc": "2026-06-01T02:00:00Z"},
            {**base, "executionId": "four", "orderCreatedAtUtc": "2026-06-01T03:00:00Z"},
        ],
        [
            {**base, "executionId": "long"},
            {
                **base,
                "executionId": "short",
                "direction": "SHORT",
                "orderCreatedAtUtc": "2026-06-01T01:00:00Z",
            },
        ],
    ):
        try:
            validate_global_risk_exposure(invalid)
        except V4ContractError:
            pass
        else:
            raise AssertionError("invalid frozen risk exposure was accepted")


def test_api_and_broker_latency_are_not_backfilled() -> None:
    market = synthetic_market()
    row = market.m1_row(market.m1_index_at_or_after(TOUCH_TIME - 60) + 1)
    base = {
        "direction": "LONG",
        "entry": float(row["high"]),
        "stop": float(row["low"]) - 1.0,
        "target": float(row["high"]) + 50.0,
        "orderId": "latency",
        "scenarioHash": "scenario",
        "model": "DELIVERY_FVG_REPLACEMENT",
        "executionZone": {"low": float(row["low"]), "high": float(row["high"])},
        "buffer": float(row["spreadPoints"]) * market.point,
    }
    api_order = {
        **base,
        "semanticReadyAtUtc": utc_text(int(row["available"]) + 60),
    }
    assert advance_pending(market, api_order, row)[0] == "CANCELED_MISSED_API_LATENCY"
    broker_order = {
        **base,
        "brokerAuthorizedAtUtc": utc_text(int(row["available"]) + 60),
    }
    assert advance_pending(market, broker_order, row)[0] == "CANCELED_MISSED_ORDER_LATENCY"
    ambiguous = {
        **base,
        "semanticReadyAtUtc": utc_text(int(row["time"]) + 30),
    }
    assert advance_pending(market, ambiguous, row)[0] == "CANCELED_LATENCY_INTRABAR_AMBIGUOUS"


def test_addon_order_keeps_distinct_execution_identity() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    formed_id = f"M1:{BASE + 60}"
    causal_id = f"M1:{BASE}"
    candidate = {
        "executionModel": "DELIVERY_FVG_ADDON",
        "direction": "LONG",
        "formedAtUtc": utc_text(BASE + 120),
        "formedBarId": formed_id,
        "causalObBarId": causal_id,
        "protectedSwingBarId": causal_id,
        "originalChildObBarId": scenario["finalChild"]["obBarId"],
        "entry": 102.0,
        "stop": 100.0,
        "target": 120.0,
        "fvg": {"low": 100.02, "high": 102.0},
        "buffer": 0.02,
        "spreadAtFormation": 0.02,
        "transferSwingBarId": causal_id,
        "sourcePositionOrderId": "source-position",
        "selectedObjective": scenario["objective"],
        "objectiveFamilyId": scenario["objectiveFamily"]["objectiveFamilyId"],
        "intermediateDelivery": [],
    }
    order, _ = delivery_candidate_order(market, scenario, candidate)
    assert order["model"] == "DELIVERY_FVG_ADDON"
    assert order["sourcePositionOrderId"] == "source-position"
    assert order["deliveryFvgBarId"] == formed_id


def test_order_authority_rejects_stale_or_unresolved_owner() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    scenario["direction"] = "LONG"
    scenario["scope"] = "EXTERNAL_CONTINUATION"
    opposing = {
        "direction": "SHORT",
        "status": "ACTIVE",
        "establishedAtUtc": scenario["frozenAtUtc"],
        "sourceScenarioHash": "other",
        "sourceScope": "EXTERNAL_CONTINUATION",
        "dealingRange": copy.deepcopy(scenario["dealingRange"]),
        "protectedSwing": copy.deepcopy(scenario["mapProtectedSwing"]),
        "objective": copy.deepcopy(scenario["objective"]),
    }
    try:
        validate_scenario_authority_at_order(scenario, opposing)
    except V4ContractError:
        pass
    else:
        raise AssertionError("opposite intact owner accepted a continuation order")
    scenario["scope"] = "INTERNAL_ROTATION"
    opposing["status"] = "REMAP_REQUIRED"
    try:
        validate_scenario_authority_at_order(scenario, opposing)
    except V4ContractError:
        pass
    else:
        raise AssertionError("internal rotation was accepted before external remap")


def test_family_snapshot_changes_when_objective_becomes_knowable() -> None:
    family = {
        "familyId": "physical-family",
        "scenarioOptions": [{
            "scenarioSelectionId": "old-option",
            "direction": "LONG",
            "scope": "INTERNAL_ROTATION",
            "objective": {"barId": "M15:100", "side": "HIGH"},
            "lineagePathSelectionId": "path-1",
            "ownerBreakTargetBarId": None,
            "ownerBreakBarId": None,
        }],
    }
    old_id, physical_id, old_snapshot = snapshot_family(family)
    updated = copy.deepcopy(family)
    updated["scenarioOptions"][0]["objective"] = {
        "barId": "M15:200", "side": "HIGH"
    }
    new_id, new_physical_id, new_snapshot = snapshot_family(updated)
    assert old_id != new_id
    assert physical_id == new_physical_id == "physical-family"
    assert old_snapshot["familyId"] == old_id
    assert new_snapshot["familyId"] == new_id


def test_invalidated_june_ground_truth_cannot_claim_completion() -> None:
    ground_truth = ROOT / "output/ground_truth_v2_june2026_v451"
    if not ground_truth.exists():
        return
    assert (ground_truth / "BLOCKED_REPORT.md").exists()
    completion = (ground_truth / "COMPLETION_REPORT.md").read_text(
        encoding="utf-8-sig"
    )
    assert "INVALIDATED" in completion
    assert "Ground truth complete: `false`" in completion


def test_corrected_scan_exposes_june_four_dynamic_objective() -> None:
    corrected = ROOT / "output/ground_truth_v2_june2026_v451_r3"
    ledger = corrected / "family_ledger.jsonl"
    if not ledger.exists():
        return
    matches = []
    for line in ledger.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        family = json.loads(line)
        if family.get("rootBarId") != "M30:1780534800":
            continue
        for option in family.get("scenarioOptions", []):
            if (
                (option.get("objective") or {}).get("barId")
                == "M15:1780542000"
            ):
                matches.append(family)
    assert matches
    assert min(item["firstKnownAtUtc"] for item in matches) == (
        "2026-06-04T03:45:00Z"
    )


def main() -> int:
    test_lossless_packet_contains_every_htf_role()
    test_objective_family_uses_first_live_member_at_least_one_r()
    test_watch_lanes_are_free_but_pending_and_filled_stop_at_three_r()
    test_frozen_ground_truth_rechecks_capacity_and_opposite_exposure()
    test_api_and_broker_latency_are_not_backfilled()
    test_addon_order_keeps_distinct_execution_identity()
    test_order_authority_rejects_stale_or_unresolved_owner()
    test_family_snapshot_changes_when_objective_becomes_knowable()
    test_invalidated_june_ground_truth_cannot_claim_completion()
    test_corrected_scan_exposes_june_four_dynamic_objective()
    print("GROUND_TRUTH_V2_INTEGRATION_TESTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
