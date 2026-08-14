from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import mentor_ai_replay_v4 as replay
from scripts.codex_replay_provider import CodexReplayError
from scripts.build_ground_truth_v2 import (
    HashChainWriter,
    M1FirstTouchIndex,
    family_local_packet,
    first_root_proximal_touch_at,
    validate_selected_trade,
    verify_hash_chain,
)
from scripts.build_mentor_api_contracts import main as build_contracts
from scripts.mentor_ai_live_v4 import (
    DemoOrderRouter,
    LiveRequestBuffer,
    adaptive_backfill,
    recover_interrupted_bar,
)
from scripts.mentor_replay_v4_core import (
    MAX_LONG_TERM_H1_FALLBACK_OBJECTIVES,
    MarketData,
    PLAN_SEMANTIC_AUDIT_KEYS,
    PIPELINE_VERSION,
    V4ContractError,
    _bounded_external_objectives,
    _body_broken_protected_candidates,
    _confirmed_liquidity_swings,
    _confirmed_long_history_h1_swings,
    advance_pending,
    build_plan_packet,
    delivery_structural_invalidation,
    freeze_plan_batch,
    mechanical_root_candidates,
    new_runtime,
    parse_utc,
    root_bar_ids_available_between,
    select_objective_from_family,
    utc_text,
)
from scripts.test_mentor_ai_replay_v4 import (
    BASE,
    PLAN_AT,
    TOUCH_TIME,
    ScriptedProvider,
    frozen_scenario,
    synthetic_market,
    with_synthetic_atomic_family,
)


def runner_for(runtime: dict, config: dict | None = None):
    temporary = tempfile.TemporaryDirectory()
    runner = replay.V4Runner(
        config={**replay.DEFAULTS, "symbol": "GOLD", **(config or {})},
        market=synthetic_market(),
        run_dir=Path(temporary.name),
        provider=ScriptedProvider([]),
        runtime=runtime,
    )
    return temporary, runner


def test_plan_batch_non_trading_selection_residue_is_inert() -> None:
    market = synthetic_market()
    as_of = PLAN_AT
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, as_of, "GOLD")
    )
    family = packet["physicalLineageFamilies"][0]
    family_id = str(family["familyId"])
    option_id = str(family["scenarioOptions"][0]["scenarioSelectionId"])
    failed_audit = {
        key: "FAIL" for key in PLAN_SEMANTIC_AUDIT_KEYS
    }
    for action in ("NO_PLAN", "DATA_ERROR"):
        payload = {
            "schemaVersion": "5.0.0",
            "decisions": [{
                "familyId": family_id,
                "action": action,
                "scenarioSelectionId": option_id,
                "semanticAudit": failed_audit,
                "reason": "non-trading response must have no execution authority",
            }],
        }
        assert freeze_plan_batch(payload, market, as_of, packet) == []

    invalid_plan = {
        "schemaVersion": "5.0.0",
        "decisions": [{
            "familyId": family_id,
            "action": "PLAN",
            "scenarioSelectionId": "not-supplied",
            "semanticAudit": {
                key: "PASS" for key in PLAN_SEMANTIC_AUDIT_KEYS
            },
            "reason": "must still fail",
        }],
    }
    try:
        freeze_plan_batch(invalid_plan, market, as_of, packet)
    except V4ContractError as exc:
        assert "outside family" in str(exc)
    else:
        raise AssertionError("invalid PLAN selection was not rejected")


def test_codex_usage_pause_is_resumable_but_contract_failure_is_not() -> None:
    assert CodexReplayError.retryable(
        CodexReplayError("You've hit your usage limit. Try again later.")
    )
    assert CodexReplayError.retryable(
        CodexReplayError("Codex CLI timed out after 1800s")
    )
    assert not CodexReplayError.retryable(
        CodexReplayError("Codex output is not valid JSON")
    )
    runtime = {
        "nonResumableReason": (
            "CodexReplayError: You've hit your usage limit. Try again later."
        )
    }
    assert replay.clear_retryable_provider_pause(runtime)
    assert "nonResumableReason" not in runtime
    assert runtime["resumeRecoveries"][-1]["type"] == (
        "RETRYABLE_CODEX_PROVIDER_PAUSE"
    )
    sealed = {"nonResumableReason": "CodexReplayError: invalid JSON"}
    assert not replay.clear_retryable_provider_pause(sealed)


def test_active_contract_surface_and_agents_hash() -> None:
    assert PIPELINE_VERSION == "4.51-ground-truth-v2"
    assert build_contracts() == 0
    manifest = json.loads(
        (ROOT / "mentor_context_pack/api_contracts/v4_manifest.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert set(manifest["contracts"]) == {"plan", "triggerWatch", "deliveryReview"}
    assert replay.DEFAULTS["enableDeliveryAddons"] is False
    delivery_contract = (
        ROOT / "mentor_context_pack/api_contracts/delivery_review_v4.md"
    ).read_text(encoding="utf-8-sig")
    assert "Addon remains disabled" in delivery_contract
    assert "FVG distal is not the hard-SL authority" in delivery_contract


def test_delivery_addon_disabled_and_structural_stop_geometry() -> None:
    assert delivery_structural_invalidation(
        "LONG",
        {"low": 99.0},
        {"low": 98.0},
        {"distal": 97.0},
    ) == 97.0
    assert delivery_structural_invalidation(
        "SHORT",
        {"high": 101.0},
        {"high": 102.0},
        {"distal": 103.0},
    ) == 103.0
    temporary, runner = runner_for(new_runtime(0))
    try:
        row = runner.market.m1_row(
            runner.market.m1_index_at_or_after(PLAN_AT)
        )
        with patch.object(
            replay, "detect_delivery_addon_candidate"
        ) as detector:
            runner.maybe_open_delivery_addons(
                row,
                [{"bookId": "book", "scenario": {}, "position": {}}],
            )
        detector.assert_not_called()
    finally:
        temporary.cleanup()


def test_june9_current_range_never_uses_long_history_objective_boundary() -> None:
    dataset = ROOT / "output/datasets/GOLD_M1_2023-12-01_2026-08-12.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2023-12-01T00:00:00Z"),
        parse_utc("2026-07-11T00:00:00Z"),
        0.01,
    )
    authority = {
        "direction": "LONG",
        "establishedAtUtc": "2026-06-09T07:30:00Z",
        "sourceScenarioHash": "june9-range-regression",
        "sourceScope": "EXTERNAL_REVERSAL",
        "dealingRange": {
            "highBarId": "M30:1780984800",
            "lowBarId": "M30:1780972200",
            "high": 4342.04,
            "low": 4312.63,
        },
        "protectedSwing": {
            "barId": "M30:1780972200", "tf": "M30",
            "high": 4322.21, "low": 4312.63,
        },
        "objective": {
            "barId": "M30:1780984800", "tf": "M30", "side": "HIGH",
            "kind": "EXTERNAL_SWING", "price": 4342.04,
        },
        "status": "ACTIVE",
        "bodyBreakBarId": None,
        "objectiveReachedBarId": None,
        "objectiveReachedAtUtc": None,
        "resolvedAtUtc": None,
        "ownerEpoch": 20,
    }
    packet = build_plan_packet(
        market,
        parse_utc("2026-06-09T09:00:00Z"),
        "GOLD",
        external_authority=authority,
    )
    families = packet["physicalLineageFamilies"]
    assert families
    for family in families:
        ranges = family["dealingRangePairCandidates"]
        assert len(ranges) <= 2
        protected_ids = set(family["eligibleProtectedSwingBarIds"])
        for dealing_range in ranges:
            assert "externalObjectiveBarId" not in dealing_range
            assert dealing_range["bodyBrokenProtectedSwingBarId"] in protected_ids
            for endpoint in (dealing_range["highBarId"], dealing_range["lowBarId"]):
                assert parse_utc("2026-06-01T00:00:00Z") <= int(endpoint.split(":")[1])
        assert len(family["scenarioOptions"]) <= 10
    for phase in ("MAP", "REFINEMENT"):
        contract, hashes = replay.load_v4_contract(phase)
        assert contract and "legacyReadOnly" in hashes


def test_timeframe_and_future_bar_boundaries() -> None:
    market = synthetic_market()
    latest = market.bars("H1", PLAN_AT, 1)[-1]
    assert int(latest["available"]) <= PLAN_AT
    future_id = f"H1:{int(latest['time']) + 3600}"
    try:
        market.bar(future_id, PLAN_AT)
    except V4ContractError:
        pass
    else:
        raise AssertionError("future HTF candle was visible")


def test_long_history_liquidity_cache_does_not_materialize_all_bar_dicts() -> None:
    market = synthetic_market()
    with patch.object(
        type(market), "bars", side_effect=AssertionError("full bar materialization used")
    ):
        swings = _confirmed_long_history_h1_swings(market, PLAN_AT)
    assert isinstance(swings, list)


def test_duplicate_physical_delivery_is_blocked_before_semantic_review() -> None:
    runtime = new_runtime(0)
    temporary, runner = runner_for(runtime)
    try:
        first = frozen_scenario(runner.market)
        second = copy.deepcopy(first)
        second["scenarioHash"] = "distinct-scenario"
        runner.runtime["scenarioSlots"] = [
            {
                "slotId": "slot-a", "state": "PLANNED", "scenario": first,
                "createdAtUtc": utc_text(PLAN_AT),
            },
            {
                "slotId": "slot-b", "state": "PLANNED", "scenario": second,
                "createdAtUtc": utc_text(PLAN_AT),
            },
        ]
        row = runner.market.m1_row(runner.market.m1_index_at_or_after(PLAN_AT))
        candidate = {
            "direction": "LONG", "formedBarId": row["barId"],
            "causalObBarId": "M1:1", "transferSwingBarId": "M1:2",
            "fvg": {"low": 100.0, "high": 101.0},
        }
        with (
            patch.object(replay, "zone_touched", return_value=False),
            patch.object(
                replay, "detect_pre_touch_delivery_candidate",
                return_value=copy.deepcopy(candidate),
            ),
        ):
            runner.prepare_delivery_candidates(row)
        physical_key = runner.physical_delivery_key(candidate)
        assert physical_key in runner._blocked_delivery_physical_keys
        assert set(runner._delivery_candidate_cache) == {"slot-a", "slot-b"}
        assert runner.stats["semanticRequests"] == 0
    finally:
        temporary.cleanup()


def test_objective_family_scope_lifecycle() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    scenario["scope"] = "INTERNAL_ROTATION"
    scenario["objectiveFamily"] = {
        "objectiveFamilyId": "internal-first",
        "orderedMembers": [
            {"barId": scenario["objective"]["barId"]},
            {"barId": f"H1:{BASE}"},
        ],
    }
    with patch(
        "scripts.mentor_replay_v4_core._objective_consumed",
        side_effect=lambda _market, item, _as_of: item["barId"]
        == scenario["objective"]["barId"],
    ):
        try:
            select_objective_from_family(
                market, scenario, entry=100.0, stop=99.0, as_of=PLAN_AT
            )
        except V4ContractError as exc:
            assert "INTERNAL_OBJECTIVE_PRECONSUMED_CANCEL" in str(exc)
        else:
            raise AssertionError("consumed first internal objective was replaced")


def test_current_external_objectives_are_not_capped() -> None:
    market = synthetic_market()
    rows = market.bars("H1", PLAN_AT, 8)
    assert len(rows) >= 4
    decision_close = float(rows[-1]["close"])
    candidates = []
    for index, row in enumerate(rows[-4:], start=1):
        candidates.append({
            "barId": row["barId"],
            "side": "HIGH",
            "price": decision_close + float(index),
            "matureAtUtc": utc_text(int(row["available"])),
        })
    selected = _bounded_external_objectives(
        market, candidates, PLAN_AT, decision_close
    )
    assert len(candidates) == 4
    assert MAX_LONG_TERM_H1_FALLBACK_OBJECTIVES == 2
    assert len(selected) == len(candidates) == 4
    assert [item["price"] for item in selected] == [
        decision_close + float(index) for index in range(1, 5)
    ]


def test_displacement_episode_and_nonpivot_protected() -> None:
    market = synthetic_market()
    roots = mechanical_root_candidates(market, PLAN_AT, maximum=None)
    assert roots
    assert all(item["displacementEpisodeBarIds"] for item in roots)
    assert all(
        item["rootBarId"] == item["displacementEpisodeBarIds"][0]
        for item in roots
    )
    root = roots[0]
    root_row = market.bar(root["rootBarId"], PLAN_AT)
    displacement = market.bar(root["displacementBarId"], PLAN_AT)
    protected = _body_broken_protected_candidates(
        market,
        root_row["tf"],
        root_row,
        displacement,
        root["direction"],
        PLAN_AT,
        maximum=None,
    )
    assert isinstance(protected, list)
    assert len(protected) == len(set(protected))


def test_proximal_touch_keeps_zone_active_until_distal_or_body_invalidation() -> None:
    market = synthetic_market()
    all_roots = mechanical_root_candidates(
        market, PLAN_AT, maximum=None, active_only=False
    )
    active_roots = mechanical_root_candidates(
        market, PLAN_AT, maximum=None, active_only=True
    )
    proximal_only = [
        item for item in all_roots
        if item["laterProximalTouched"]
        and not item["laterDistalTouched"]
        and not item["laterBodyInvalidated"]
    ]
    assert proximal_only
    active_ids = {
        (item["rootBarId"], item["displacementBarId"])
        for item in active_roots
    }
    assert all(
        (item["rootBarId"], item["displacementBarId"]) in active_ids
        for item in proximal_only
    )


def test_focused_plan_packet_never_leaks_another_root_family() -> None:
    market = synthetic_market()
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    selected_root = packet["physicalLineageFamilies"][0]["rootBarId"]
    focused = build_plan_packet(
        market,
        PLAN_AT,
        "GOLD",
        focus_root_bar_ids={selected_root},
    )
    assert all(
        family["rootBarId"] == selected_root
        for family in focused["physicalLineageFamilies"]
    )


def test_first_touch_index_matches_raw_m1_and_family_packet_is_local() -> None:
    market = synthetic_market()
    candidate = next(
        item for item in mechanical_root_candidates(
            market, PLAN_AT, maximum=None, active_only=False
        )
        if item["laterProximalTouched"]
    )
    indexed = first_root_proximal_touch_at(
        market,
        candidate,
        PLAN_AT,
        M1FirstTouchIndex(market.rates),
    )
    brute = first_root_proximal_touch_at(market, candidate, PLAN_AT)
    assert indexed == brute

    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    family = packet["physicalLineageFamilies"][0]
    local = family_local_packet(packet, family, market, PLAN_AT)
    assert local["familyLocalId"] == family["familyId"]
    assert [item["familyId"] for item in local["physicalLineageFamilies"]] == [
        family["familyId"]
    ]
    assert not local["roleEvidenceAudit"]["missingRoleIds"]


def test_lineage_paging_roundtrip() -> None:
    market = synthetic_market()
    packet = with_synthetic_atomic_family(build_plan_packet(market, PLAN_AT, "GOLD"))
    packet["swingCandidates"] = [
        {"barId": f"H1:{BASE}", "padding": "x" * 256}
        for _ in range(300)
    ]
    family = copy.deepcopy(packet["physicalLineageFamilies"][0])
    base_option = family["scenarioOptions"][0]
    family["scenarioOptions"] = [
        {**copy.deepcopy(base_option), "scenarioSelectionId": f"scenario-{index:03d}"}
        for index in range(300)
    ]
    temporary, runner = runner_for(
        new_runtime(0), {"maximumPlanPromptBytes": 18000}
    )
    try:
        pages = runner.deterministic_plan_subpages(packet, family, PLAN_AT)
        assert len(pages) > 1
        restored = [
            item["scenarioSelectionId"]
            for page in pages
            for item in page["physicalLineageFamilies"][0]["scenarioOptions"]
        ]
        assert restored == [item["scenarioSelectionId"] for item in family["scenarioOptions"]]
        assert len({page["subPage"]["sourceFamilyHash"] for page in pages}) == 1
        assert all(
            len(replay.prompt_for("PLAN", page).encode("utf-8")) <= 18000
            for page in pages
        )
        assert all(page["swingCandidates"] == [] for page in pages)
    finally:
        temporary.cleanup()


def test_trigger_latency_and_through_delivery() -> None:
    market = synthetic_market()
    row = market.m1_row(market.m1_index_at_or_after(TOUCH_TIME - 60) + 1)
    order = {
        "direction": "LONG",
        "entry": float(row["high"]),
        "stop": float(row["low"]) - 1.0,
        "target": float(row["high"]) + 10.0,
        "orderId": "latency",
        "scenarioHash": "scenario",
        "model": "DELIVERY_FVG_REPLACEMENT",
        "executionZone": {"low": float(row["low"]), "high": float(row["high"])},
        "buffer": float(row["spreadPoints"]) * market.point,
        "semanticReadyAtUtc": utc_text(int(row["available"]) + 60),
    }
    assert advance_pending(market, order, row)[0] == "CANCELED_MISSED_API_LATENCY"


def test_delivery_fvg_dedup_addon_reentry() -> None:
    runtime = new_runtime(0)
    temporary, runner = runner_for(runtime)
    try:
        scenario = frozen_scenario(runner.market)
        order = {
            "direction": "LONG", "model": "DELIVERY_FVG_ADDON",
            "deliveryFvgBarId": f"M1:{BASE}", "entry": 100.0,
            "stop": 99.0, "target": 110.0, "orderId": "addon-one",
        }
        key = runner.execution_signal_key(scenario, order)
        assert key == runner.execution_signal_key(scenario, copy.deepcopy(order))
        assert runner.risk_order_block_reason({"direction": "LONG"}, scenario) is None
    finally:
        temporary.cleanup()


def test_risk_slot_arbitration_and_geometry() -> None:
    scenario = frozen_scenario(synthetic_market())
    later = {
        "slotId": "later", "createdAtUtc": "2025-01-01T01:00:00Z",
        "scenario": scenario, "order": {"orderId": "b", "createdAtUtc": "2025-01-01T01:00:00Z"},
    }
    earlier = {
        "slotId": "earlier", "createdAtUtc": "2025-01-01T00:00:00Z",
        "scenario": scenario, "order": {"orderId": "a", "createdAtUtc": "2025-01-01T00:00:00Z"},
    }
    assert sorted([later, earlier], key=replay.V4Runner.lane_arbitration_key)[0] is earlier


def test_immediate_no_trade_contracts() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    scenario["objectiveFamily"] = {"objectiveFamilyId": "empty", "orderedMembers": []}
    try:
        select_objective_from_family(market, scenario, 100.0, 99.0, PLAN_AT)
    except V4ContractError as exc:
        assert "OBJECTIVE_FAMILY_EMPTY" in str(exc)
    else:
        raise AssertionError("missing objective did not fail closed")


def test_shared_advance_clock_and_restart() -> None:
    runtime = new_runtime(0)
    runtime["inFlightRequests"] = {"request-one": {"contentHash": "same"}}
    with tempfile.TemporaryDirectory() as temporary:
        run_dir = Path(temporary)
        (run_dir / "decision_ledger.jsonl").write_text("", encoding="utf-8")
        (run_dir / "trades.jsonl").write_text("", encoding="utf-8")
        (run_dir / "state.json").write_text(json.dumps(runtime), encoding="utf-8")
        (run_dir / "bar_transaction.json").write_text(json.dumps({
            "runtimeBefore": new_runtime(0), "ledgerBytes": 0, "tradesBytes": 0,
        }), encoding="utf-8")
        assert recover_interrupted_bar(run_dir)
        restored = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        assert "request-one" in restored["inFlightRequests"]


def test_ground_truth_independent_audits() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "audit.jsonl"
        writer = HashChainWriter(path)
        writer.append({
            "auditType": "CHRONOLOGICAL", "auditorId": "one",
            "auditSessionId": "session-one", "familyId": "family",
        })
        assert len(verify_hash_chain(path, "CHRONOLOGICAL")) == 1
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("family", "tampered", 1), encoding="utf-8")
        try:
            verify_hash_chain(path, "CHRONOLOGICAL")
        except V4ContractError:
            pass
        else:
            raise AssertionError("tampered independent audit was accepted")


def test_protocol_classification_taxonomy() -> None:
    source = (ROOT / "scripts/mentor_ai_replay_v4.py").read_text(encoding="utf-8-sig")
    for legacy in (
        '"MAP_MISS"', '"ROOT_MISS"', '"OBJECTIVE_MISS"',
        '"REFINEMENT_MISS"', '"TRIGGER_WATCH_MISS"', '"ORDER_MISS"',
    ):
        assert legacy not in source
    for category in (
        "ENGINE_CANDIDATE", "OWNER", "LINEAGE", "OBJECTIVE",
        "MODEL", "CAPACITY", "LATENCY", "BROKER",
    ):
        assert category in (source + (ROOT / "scripts/build_ground_truth_v2.py").read_text(encoding="utf-8-sig"))


def test_ground_truth_final_declaration_fields() -> None:
    market = synthetic_market()
    packet = with_synthetic_atomic_family(build_plan_packet(market, PLAN_AT, "GOLD"))
    family = packet["physicalLineageFamilies"][0]
    try:
        validate_selected_trade(
            market,
            family,
            {"familyId": family["familyId"]},
            {},
        )
    except V4ContractError as exc:
        assert "accepted execution is incomplete" in str(exc)
    else:
        raise AssertionError("incomplete final declaration was accepted")


def test_frozen_ground_truth_v2_gate_and_jsonl_loader() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        row = {
            "executionId": "execution-one",
            "decisionAtUtc": "2026-06-01T00:00:00Z",
            "filledAtUtc": "2026-06-01T00:01:00Z",
            "closedAtUtc": "2026-06-01T00:02:00Z",
            "direction": "LONG",
            "scope": "EXTERNAL_CONTINUATION",
            "executionModel": "HTF_OB_REACTION",
            "entry": 100.0,
            "stop": 99.0,
            "target": 110.0,
            "rootObBarId": f"H1:{BASE}",
            "finalChildObBarId": f"M5:{BASE}",
            "objectiveBarId": f"H1:{BASE + 3600}",
            "previousHash": "GENESIS",
        }
        row["recordHash"] = replay.canonical_hash(row)
        ledger = directory / "accepted_ground_truth.jsonl"
        ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
        (directory / "manifest.json").write_text(json.dumps({
            "pipelineVersion": PIPELINE_VERSION,
            "status": "FROZEN_GROUND_TRUTH_V2",
            "groundTruthComplete": True,
            "agentsSha256": replay.sha256_file(ROOT / "AGENTS.md"),
            "contractsManifestSha256": replay.sha256_file(replay.V4_MANIFEST),
            "acceptedTradeCount": 1,
            "acceptedLedgerTipHash": row["recordHash"],
        }), encoding="utf-8")
        assert replay.validate_frozen_ground_truth_v2(ledger)
        loaded = replay.load_trade_rows(ledger)
        assert loaded[0]["root_ob_bar_id"] == f"H1:{BASE}"
        assert loaded[0]["child_ob_bar_id"] == f"M5:{BASE}"


def test_warmup_family_baseline_does_not_call_plan() -> None:
    runtime = new_runtime(0)
    temporary, runner = runner_for(runtime, {"planOnFamilyFormation": True})
    try:
        packet = with_synthetic_atomic_family(
            build_plan_packet(runner.market, PLAN_AT, "GOLD")
        )
        with patch.object(replay, "build_plan_packet", return_value=packet):
            runner.seed_warmup_family_baseline(PLAN_AT)
        assert runner.runtime["flatPlanCandidates"]
        assert all(
            item["status"] == "REGISTERED" and item["isWarmupBaseline"]
            for item in runner.runtime["flatPlanCandidates"]
        )
        assert runner.runtime["newPlanFamilyIdsAtLastRefresh"] == []
        assert runner.runtime["newPlanEventsAtLastRefresh"] == []
        updated = copy.deepcopy(packet)
        family = updated["physicalLineageFamilies"][0]
        extra = copy.deepcopy(family["scenarioOptions"][0])
        extra["scenarioSelectionId"] = "scenario-warmup-new-objective"
        alternative = runner.market.bars("H1", PLAN_AT, 2)[0]["barId"]
        extra["objective"] = {**extra["objective"], "barId": alternative}
        family["scenarioOptions"].append(extra)
        with patch.object(replay, "build_plan_packet", return_value=updated):
            runner.refresh_flat_plan_candidates(PLAN_AT + 300)
        assert runner.runtime["newPlanEventsAtLastRefresh"] == []
        row = runner.market.m1_row(runner.market.m1_index_at_or_after(PLAN_AT))
        assert not runner.schedule_formation_driven_flat_plan(
            row, state_at_bar_start="FLAT", api_allowed=True
        )
        assert runner.stats["semanticRequests"] == 0
    finally:
        temporary.cleanup()


def test_incremental_refresh_skips_full_packet_without_new_events() -> None:
    runtime = new_runtime(0)
    temporary, runner = runner_for(runtime, {"planOnFamilyFormation": True})
    try:
        packet = with_synthetic_atomic_family(
            build_plan_packet(runner.market, PLAN_AT, "GOLD")
        )
        with patch.object(replay, "build_plan_packet", return_value=packet):
            runner.seed_warmup_family_baseline(PLAN_AT)
        with (
            patch.object(replay, "root_bar_ids_available_between", return_value=set()),
            patch.object(
                replay, "liquidity_bar_ids_matured_between", return_value=set()
            ),
            patch.object(replay, "build_plan_packet") as packet_builder,
        ):
            runner.refresh_flat_plan_candidates(PLAN_AT + 300)
        packet_builder.assert_not_called()
        assert runner.runtime["lastPlanCandidateRefreshM5"] == (
            runner.latest_m5_available(PLAN_AT + 300)
        )
    finally:
        temporary.cleanup()


def test_new_root_displacement_interval_is_not_replayed_twice() -> None:
    market = synthetic_market()
    roots = mechanical_root_candidates(
        market, PLAN_AT, maximum=None, active_only=False
    )
    selected = roots[len(roots) // 2]
    displacement = market.bar(selected["displacementBarId"], PLAN_AT)
    available = int(displacement["available"])
    first = root_bar_ids_available_between(
        market, available - 1, available,
        timeframes=(str(selected["timeframe"]),),
    )
    second = root_bar_ids_available_between(
        market, available, available + 300,
        timeframes=(str(selected["timeframe"]),),
    )
    assert str(selected["rootBarId"]) in first
    assert str(selected["rootBarId"]) not in second


def test_root_waits_for_later_objective_without_retroactive_reconstruction() -> None:
    runtime = new_runtime(0)
    temporary, runner = runner_for(runtime, {"planOnFamilyFormation": True})
    try:
        baseline = with_synthetic_atomic_family(
            build_plan_packet(runner.market, PLAN_AT, "GOLD")
        )
        with patch.object(replay, "build_plan_packet", return_value=baseline):
            runner.seed_warmup_family_baseline(PLAN_AT)

        waiting_root = str(
            baseline["physicalLineageFamilies"][0]["rootBarId"]
        )
        empty_packet = {
            **baseline,
            "physicalLineageFamilies": [],
        }
        with (
            patch.object(
                replay, "root_bar_ids_available_between", return_value={waiting_root}
            ),
            patch.object(
                replay, "liquidity_bar_ids_matured_between", return_value=set()
            ),
            patch.object(replay, "build_plan_packet", return_value=empty_packet),
        ):
            runner.refresh_flat_plan_candidates(PLAN_AT + 300)
        assert runner.runtime["pendingPlanRootBarIds"] == [waiting_root]
        runner.runtime["lastPlanCandidateRefreshM5"] = int(
            runner.runtime["lastPlanCandidateRefreshM5"]
        ) - 300

        completed = copy.deepcopy(baseline)
        completed_family = completed["physicalLineageFamilies"][0]
        completed_family["rootBarId"] = waiting_root
        completed_family["familyId"] = "family-completed-by-later-objective"
        with (
            patch.object(replay, "root_bar_ids_available_between", return_value=set()),
            patch.object(
                runner, "latest_m15_available", return_value=PLAN_AT + 600
            ),
            patch.object(
                replay,
                "liquidity_bar_ids_matured_between",
                return_value={"M15:new-objective"},
            ),
            patch.object(replay, "build_plan_packet", return_value=completed),
        ):
            runner.refresh_flat_plan_candidates(PLAN_AT + 600)
        assert runner.runtime["pendingPlanRootBarIds"] == [waiting_root]
        assert "family-completed-by-later-objective" in {
            item["familyId"] for item in runner.runtime["flatPlanCandidates"]
        }
    finally:
        temporary.cleanup()


class FakeLiveFeed:
    def __init__(self, rates) -> None:
        self.rates = rates
        self.orders: list[dict] = []
        self.positions: list[dict] = []
        self.requests: list[int] = []

    def connect(self):
        return {
            "tradeMode": 0, "demoTradeMode": 0, "terminalConnected": True,
            "tradeAllowed": True, "volumeMin": 0.01, "volumeStep": 0.01,
            "volumeMax": 100.0,
        }

    def closed_rates(self, bars: int):
        self.requests.append(int(bars))
        count = min(len(self.rates), max(2, int(bars)))
        return self.rates[-count:].copy(), {
            "serverNow": int(self.rates[-1]["time"]) + 60,
            "bid": float(self.rates[-1]["close"]),
            "ask": float(self.rates[-1]["close"]) + 0.01,
        }

    def broker_snapshot(self):
        return {"orders": copy.deepcopy(self.orders), "positions": copy.deepcopy(self.positions)}

    def submit_pending(self, order, volume, client_id):
        ticket = 1000 + len(self.orders)
        self.orders.append({
            "ticket": ticket, "comment": client_id, "type": 0,
            "volume": volume, "price": order["entry"], "sl": order["stop"],
            "tp": order["target"],
        })
        return {"ticket": ticket, "retcode": 10008, "clientId": client_id}

    def cancel_pending(self, ticket, client_id):
        self.orders = [item for item in self.orders if int(item["ticket"]) != int(ticket)]
        return {"ticket": int(ticket), "retcode": 10009}

    def shutdown(self):
        return None


def test_live_backfill_buffer_and_fake_demo_router() -> None:
    rates = synthetic_market().rates
    feed = FakeLiveFeed(rates)
    existing = rates[:-8].copy()
    incoming, _, used = adaptive_backfill(
        feed, existing, initial_bars=2, maximum_bars=16, offset_seconds=0
    )
    assert used > 2 and int(incoming[0]["time"]) <= int(existing[-1]["time"])
    with tempfile.TemporaryDirectory() as temporary:
        buffer = LiveRequestBuffer(
            feed, Path(temporary), offset_seconds=0, poll_seconds=0.02, poll_bars=2
        )
        buffer.before_request({"requestId": "buffered", "phase": "PLAN"})
        time.sleep(0.06)
        buffer.after_request({})
        rows = (Path(temporary) / "request_market_buffer.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        assert rows and json.loads(rows[0])["tick"]["ask"] > 0

    runtime = new_runtime(0)
    runtime["orders"] = [{
        "orderId": "one", "status": "PENDING", "clientId": "MENTOR-one"
    }]
    runtime["scenarioSlots"] = [{
        "slotId": "slot", "state": "PENDING",
        "order": {
            "orderId": "one", "direction": "LONG", "entry": 100.0,
            "stop": 99.0, "target": 110.0,
        },
    }]
    router = DemoOrderRouter(feed, feed.connect(), enabled=True)
    assert router.sync(runtime)["submitted"] == 1
    assert router.sync(runtime)["reconciled"] == 1
    runtime["orders"][0]["status"] = "CANCELED"
    assert router.sync(runtime)["canceled"] == 1


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"MENTOR_AI_REPLAY_V451_TESTS_OK tests={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
