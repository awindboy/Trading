from __future__ import annotations

import copy
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

import numpy as np
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.mentor_ai_replay_v4 as replay_v4
from scripts.gemini_replay_provider import (
    GeminiReplayError,
    GeminiResponse,
    build_generate_content_body,
)
from mentor_engine.models import BarSeries
from scripts.mentor_ai_replay_v4 import (
    HashLedger,
    ScriptedProvider,
    V4Runner,
    compare_funnel,
    enforce_gemini_schema_subset,
    enforce_system_instruction_bound,
    load_v4_contract,
    model_packet_for_phase,
    prompt_for,
    runtime_agents_text,
    system_instruction_for,
)
from scripts.mentor_replay_v4_core import (
    MarketData,
    V4ContractError,
    _bounded_external_objectives,
    _confirmed_liquidity_swings,
    _confirmed_long_history_h1_swings,
    advance_pending,
    advance_position,
    advance_shadow_delivery_candidate,
    advance_reaction_monitor,
    advance_source_upgrade_candidates,
    advance_trigger_watch,
    assert_runtime_invariants,
    build_plan_packet,
    build_map_packet,
    build_reaction_monitor,
    build_trigger_packet,
    discover_source_upgrade_candidates,
    delivery_candidate_order,
    delivery_replacement,
    detect_pre_touch_delivery_candidate,
    discovery_event_fingerprint,
    external_authority_from_scenario,
    resolved_external_authority,
    freeze_plan,
    freeze_plan_batch,
    freeze_trigger_watch,
    local_scenario_cancel_reason,
    map_opportunity_id,
    map_schema,
    mechanical_root_candidates,
    new_runtime,
    outermost_completed_sweep_events,
    parse_utc,
    plan_schema,
    reset_terminal,
    refresh_reaction_monitor,
    reaction_source_episode_end_reason,
    resolve_delivery_lineage_variants,
    trigger_watch_schema,
    utc_text,
)


BASE = 1_700_006_400
PLAN_AT = BASE + 3600
TOUCH_TIME = PLAN_AT + 5 * 60


def make_series(tf: str, rows: list[tuple[int, float, float, float, float, float]]) -> BarSeries:
    seconds = {"H1": 3600, "M30": 1800, "M15": 900, "M5": 300, "M1": 60}[tf]
    values = np.asarray(rows, dtype=float)
    times = values[:, 0].astype(np.int64)
    return BarSeries(
        timeframe=tf,
        seconds=seconds,
        time=times,
        available_time=times + seconds,
        open=values[:, 1],
        high=values[:, 2],
        low=values[:, 3],
        close=values[:, 4],
        spread_points=values[:, 5],
    )


def synthetic_market() -> MarketData:
    dtype = [
        ("time", "<i8"), ("open", "<f8"), ("high", "<f8"), ("low", "<f8"),
        ("close", "<f8"), ("tick_volume", "<u8"), ("spread", "<i4"), ("real_volume", "<u8"),
    ]
    m1_values: list[tuple[int, float, float, float, float, int]] = []
    start = BASE - 1800
    for minute in range(100):
        timestamp = start + minute * 60
        m1_values.append((timestamp, 102.0, 102.4, 101.7, 102.1, 2))
    touch_index = next(index for index, row in enumerate(m1_values) if row[0] + 60 == TOUCH_TIME)
    m1_values[touch_index - 8] = (m1_values[touch_index - 8][0], 101.2, 101.5, 100.3, 101.3, 2)
    m1_values[touch_index - 7] = (m1_values[touch_index - 7][0], 101.3, 102.2, 101.2, 102.0, 2)
    m1_values[touch_index - 4] = (m1_values[touch_index - 4][0], 101.0, 101.5, 100.7, 101.2, 2)
    m1_values[touch_index] = (m1_values[touch_index][0], 101.0, 101.2, 100.0, 100.4, 2)
    m1_values[touch_index + 1] = (m1_values[touch_index + 1][0], 100.5, 100.6, 99.8, 100.4, 2)
    m1_values[touch_index + 2] = (m1_values[touch_index + 2][0], 100.2, 101.3, 100.1, 100.6, 2)
    m1_values[touch_index + 3] = (m1_values[touch_index + 3][0], 100.6, 102.2, 100.5, 102.0, 2)
    m1_values[touch_index + 4] = (m1_values[touch_index + 4][0], 102.0, 102.1, 100.4, 101.4, 2)
    m1_values[touch_index + 5] = (m1_values[touch_index + 5][0], 101.4, 121.0, 101.3, 120.5, 2)
    rates = np.zeros(len(m1_values), dtype=dtype)
    for index, row in enumerate(m1_values):
        rates[index] = (*row[:5], 1, row[5], 0)
    frames = {
        "H1": make_series(
            "H1",
            [
                (BASE - 10800, 95, 96, 90, 94, 2),
                (BASE - 7200, 110, 120, 109, 115, 2),
                (BASE - 3600, 100.8, 101.0, 99.0, 99.5, 2),
                (BASE, 99.5, 104.0, 99.4, 103.0, 2),
                (BASE + 3600, 103.0, 104.0, 100.0, 102.0, 2),
            ],
        ),
        "M30": make_series(
            "M30",
            [
                (BASE - 3600, 101, 102, 99, 100, 2),
                (BASE - 1800, 100, 103, 99.5, 102, 2),
                (BASE, 102, 103, 101, 102.5, 2),
                (BASE + 1800, 102.5, 104, 101.5, 103, 2),
            ],
        ),
        "M15": make_series(
            "M15",
            [
                (BASE - 900, 100.4, 100.5, 99.5, 99.8, 2),
                (BASE, 99.8, 102.0, 99.7, 101.5, 2),
                (BASE + 900, 101.5, 103, 101, 102, 2),
                (BASE + 1800, 102, 103, 101.5, 102.5, 2),
                (BASE + 2700, 102.5, 103.5, 101.8, 102.2, 2),
            ],
        ),
        "M5": make_series(
            "M5",
            [
                (BASE - 300, 100.1, 100.2, 99.7, 99.9, 2),
                (BASE, 99.9, 101.0, 99.8, 100.8, 2),
                (BASE + 300, 100.8, 102, 100.5, 101.5, 2),
                (BASE + 600, 101.5, 102.2, 101, 102, 2),
                (BASE + 900, 102, 102.5, 101.2, 102.1, 2),
                (BASE + 1200, 102.1, 102.4, 101.4, 102, 2),
                (BASE + 1500, 102, 102.4, 101.4, 102.1, 2),
                (BASE + 1800, 102.1, 102.4, 101.4, 102, 2),
                (BASE + 2100, 102, 102.4, 101.4, 102.1, 2),
                (BASE + 2400, 102.1, 102.4, 101.4, 102, 2),
                (BASE + 2700, 102, 102.4, 101.4, 102.1, 2),
                (BASE + 3000, 102.1, 102.4, 101.4, 102, 2),
                (BASE + 3300, 102, 102.4, 101.4, 102.1, 2),
                (BASE + 3600, 102.1, 102.4, 100, 100.4, 2),
                (BASE + 3900, 100.4, 102.2, 99.8, 102, 2),
            ],
        ),
        "M1": make_series("M1", [(row[0], row[1], row[2], row[3], row[4], row[5]) for row in m1_values]),
    }
    return MarketData(rates=rates, frames=frames, point=0.01)


def long_history_h1_market() -> MarketData:
    """Build enough closed H1 history to exercise month-old objectives."""
    count = 1_100
    h1_rows: list[tuple[int, float, float, float, float, float]] = []
    for index in range(count):
        timestamp = BASE - count * 3600 + index * 3600
        high = 110.0
        low = 90.0
        if index == 20:
            high = 130.0
        elif index == 40:
            high = 125.0
        elif index in {count - 20, count - 15, count - 10, count - 5}:
            high = 111.0 + (index % 4)
        h1_rows.append((timestamp, 100.0, high, low, 100.0, 2.0))
    h1 = make_series("H1", h1_rows)
    final_time = int(h1.time[-1])
    m30 = make_series(
        "M30",
        [(final_time - 1800, 100.0, 105.0, 99.0, 101.0, 2.0)],
    )
    frames = {
        "H1": h1,
        "M30": m30,
        "M15": make_series("M15", [(final_time - 900, 100, 104, 99, 101, 2)]),
        "M5": make_series("M5", [(final_time - 300, 100, 103, 99, 101, 2)]),
        "M1": make_series("M1", [(final_time, 100, 102, 99, 101, 2)]),
    }
    dtype = [
        ("time", "<i8"), ("open", "<f8"), ("high", "<f8"), ("low", "<f8"),
        ("close", "<f8"), ("tick_volume", "<u8"), ("spread", "<i4"),
        ("real_volume", "<u8"),
    ]
    rates = np.zeros(1, dtype=dtype)
    rates[0] = (final_time, 100, 102, 99, 101, 1, 2, 0)
    return MarketData(rates=rates, frames=frames, point=0.01)


def test_v474_current_objectives_plus_two_long_history_h1_fallbacks() -> None:
    market = long_history_h1_market()
    as_of = int(market.frames["H1"].available_time[-1])
    current_swings = _confirmed_liquidity_swings(market, as_of)
    assert any(
        item["timeframe"] == "H1"
        and parse_utc(item["matureAtUtc"]) < as_of - 30 * 86400
        for item in current_swings
    )
    swings = _confirmed_long_history_h1_swings(market, as_of)
    old_highs = [
        item for item in swings
        if item["timeframe"] == "H1"
        and item["side"] == "HIGH"
        and float(item["price"]) >= 125.0
    ]
    assert len(old_highs) == 2
    assert all(parse_utc(item["matureAtUtc"]) < as_of - 30 * 86400 for item in old_highs)

    recent_h1 = [
        {
            "barId": f"H1:{int(market.frames['H1'].time[index])}",
            "side": "HIGH",
            "price": float(market.frames["H1"].high[index]),
        }
        for index in (-20, -15, -10, -5)
    ]
    m30_id = f"M30:{int(market.frames['M30'].time[-1])}"
    selected = _bounded_external_objectives(
        market,
        [
            {"barId": m30_id, "side": "HIGH", "price": 105.0},
            *recent_h1,
            *old_highs,
            {
                "barId": f"M15:{int(market.frames['M15'].time[-1])}",
                "side": "HIGH",
                "price": 104.0,
            },
        ],
        as_of,
        100.0,
    )
    selected_ids = {str(item["barId"]) for item in selected}
    assert m30_id in selected_ids
    assert all(str(item["barId"]) in selected_ids for item in recent_h1)
    assert all(str(item["barId"]) in selected_ids for item in old_highs)
    assert not any(item.startswith("M15:") for item in selected_ids)

    fallback = _bounded_external_objectives(
        market, old_highs, as_of, 100.0
    )
    assert {str(item["barId"]) for item in fallback} == {
        str(item["barId"]) for item in old_highs
    }
    assert all(
        item["destinationContext"]["historyTier"] == "LONG_TERM_H1"
        and item["destinationContext"]["beyondRecentH1Range"] is True
        for item in fallback
    )


def valid_plan_payload() -> dict:
    return {
        "schemaVersion": "4.0.0",
        "action": "PLAN",
        "selectedBarIds": [
            f"H1:{BASE - 7200}",
            f"H1:{BASE - 10800}",
            f"H1:{BASE - 3600}",
            f"H1:{BASE}",
            f"M15:{BASE - 900}",
            f"M15:{BASE}",
            f"M5:{BASE - 300}",
            f"M5:{BASE}",
        ],
        "direction": "LONG",
        "scope": "EXTERNAL_CONTINUATION",
        "dealingRange": {"highIndex": 0, "lowIndex": 1},
        "objective": {"barIndex": 0, "side": "HIGH", "kind": "EXTERNAL_SWING"},
        "mapProtectedSwingIndex": 1,
        "ownerBreakTargetIndex": None,
        "ownerBreakIndex": None,
        "root": {
            "obIndex": 2,
            "displacementIndex": 3,
            "protectedSwingIndex": 2,
        },
        "refinements": [
            {
                "obIndex": 4,
                "displacementIndex": 5,
                "protectedSwingIndex": 4,
            },
            {
                "obIndex": 6,
                "displacementIndex": 7,
                "protectedSwingIndex": 6,
            },
        ],
        "intermediateLiquidityIndexes": [],
        "reason": "Synthetic causal long continuation.",
    }


def direct_plan_payload() -> dict:
    legacy = valid_plan_payload()
    selected = legacy["selectedBarIds"]
    node = lambda item: {
        "obBarId": selected[item["obIndex"]],
        "displacementBarId": selected[item["displacementIndex"]],
        "protectedSwingBarId": selected[item["protectedSwingIndex"]],
    }
    return {
        "schemaVersion": "4.7.0",
        "action": "PLAN",
        "direction": legacy["direction"],
        "scope": legacy["scope"],
        "dealingRange": {
            "highBarId": selected[legacy["dealingRange"]["highIndex"]],
            "lowBarId": selected[legacy["dealingRange"]["lowIndex"]],
        },
        "objective": {
            "barId": selected[legacy["objective"]["barIndex"]],
            "side": legacy["objective"]["side"],
            "kind": legacy["objective"]["kind"],
        },
        "mapProtectedSwingBarId": selected[legacy["mapProtectedSwingIndex"]],
        "ownerBreakTargetBarId": None,
        "ownerBreakBarId": None,
        "root": node(legacy["root"]),
        "refinements": [node(item) for item in legacy["refinements"]],
        "intermediateLiquidityBarIds": [],
        "reason": legacy["reason"],
    }


def atomic_plan_payload(packet: dict) -> dict:
    direct = direct_plan_payload()
    expected_root = direct["root"]
    expected_children = direct["refinements"]
    root_selection = None
    child_selections: list[str] = []
    for family in packet["physicalLineageFamilies"]:
        root_selection = next(
            (
                item["selectionId"] for item in family.get("rootSelections", [])
                if all(item[key] == expected_root[key] for key in expected_root)
            ),
            None,
        )
        if root_selection is None:
            continue
        for expected in expected_children:
            selected = next(
                (
                    option["selectionId"]
                    for child in family.get("childCandidates", [])
                    for option in child.get("selectionOptions", [])
                    if all(option[key] == expected[key] for key in expected)
                ),
                None,
            )
            assert selected is not None
            child_selections.append(selected)
        break
    assert root_selection is not None and child_selections
    return {
        "schemaVersion": "4.8.0",
        "action": direct["action"],
        "direction": direct["direction"],
        "scope": direct["scope"],
        "dealingRange": direct["dealingRange"],
        "objective": direct["objective"],
        "mapProtectedSwingBarId": direct["mapProtectedSwingBarId"],
        "ownerBreakTargetBarId": direct["ownerBreakTargetBarId"],
        "ownerBreakBarId": direct["ownerBreakBarId"],
        "rootSelectionId": root_selection,
        "refinementSelectionIds": child_selections,
        "intermediateLiquidityBarIds": direct["intermediateLiquidityBarIds"],
        "reason": direct["reason"],
    }


def with_synthetic_atomic_family(packet: dict) -> dict:
    packet = copy.deepcopy(packet)
    direct = direct_plan_payload()
    family = {
            "familyId": "synthetic-causal-family",
            "direction": direct["direction"],
            "rootBarId": direct["root"]["obBarId"],
            "initialDisplacementBarId": direct["root"]["displacementBarId"],
            "rootLaterBodyInvalidated": False,
            "rootLaterDistalTouched": False,
            "rootLaterProximalTouched": False,
            "eligibleProtectedSwingBarIds": [direct["root"]["protectedSwingBarId"]],
            "rootSelections": [
                {"selectionId": "root-synthetic", **direct["root"]}
            ],
            "childCandidates": [
                {
                    "rootBarId": node["obBarId"],
                    "deliveryOptions": [],
                    "selectionOptions": [
                        {"selectionId": f"child-synthetic-{index}", **node}
                    ],
                }
                for index, node in enumerate(direct["refinements"])
            ],
            "unconsumedDirectionalLiquidityCandidates": [
                {"barId": direct["objective"]["barId"]}
            ],
            "dealingRangePairCandidates": [
                {
                    "highBarId": direct["dealingRange"]["highBarId"],
                    "lowBarId": direct["dealingRange"]["lowBarId"],
                }
            ],
            "mapProtectedSwingCandidateBarIds": [direct["mapProtectedSwingBarId"]],
        }
    family["lineagePathOptions"] = [
        {
            "pathSelectionId": "path-synthetic",
            "root": direct["root"],
            "refinements": direct["refinements"],
        }
    ]
    family["scenarioOptions"] = [
        {
            "scenarioSelectionId": "scenario-synthetic",
            "direction": direct["direction"],
            "scope": direct["scope"],
            "dealingRange": direct["dealingRange"],
            "objective": direct["objective"],
            "mapProtectedSwingBarId": direct["mapProtectedSwingBarId"],
            "ownerBreakTargetBarId": direct["ownerBreakTargetBarId"],
            "ownerBreakBarId": direct["ownerBreakBarId"],
            "lineagePathSelectionId": "path-synthetic",
            "intermediateLiquidityBarIds": direct["intermediateLiquidityBarIds"],
        }
    ]
    packet["physicalLineageFamilies"] = [family]
    return packet


def path_plan_payload(packet: dict) -> dict:
    direct = direct_plan_payload()
    path_id = packet["physicalLineageFamilies"][0]["lineagePathOptions"][0][
        "pathSelectionId"
    ]
    return {
        "schemaVersion": "4.9.0",
        "action": direct["action"],
        "direction": direct["direction"],
        "scope": direct["scope"],
        "dealingRange": direct["dealingRange"],
        "objective": direct["objective"],
        "mapProtectedSwingBarId": direct["mapProtectedSwingBarId"],
        "ownerBreakTargetBarId": direct["ownerBreakTargetBarId"],
        "ownerBreakBarId": direct["ownerBreakBarId"],
        "lineagePathSelectionId": path_id,
        "intermediateLiquidityBarIds": direct["intermediateLiquidityBarIds"],
        "reason": direct["reason"],
    }


def scenario_plan_payload(packet: dict) -> dict:
    scenario_id = packet["physicalLineageFamilies"][0]["scenarioOptions"][0][
        "scenarioSelectionId"
    ]
    return {
        "schemaVersion": "4.11.0",
        "action": "PLAN",
        "scenarioSelectionId": scenario_id,
        "semanticAudit": {
            "externalOwnerAndScope": "PASS",
            "objectiveClassificationAndMaturity": "PASS",
            "rootDisplacementCausality": "PASS",
            "fullRefinementCausality": "PASS",
            "dealingRangePdAndCompetingLiquidity": "PASS",
        },
        "reason": "Approve the complete synthetic scenario option.",
    }


def batch_scenario_plan_payload(packet: dict) -> dict:
    legacy = scenario_plan_payload(packet)
    return {
        "schemaVersion": "5.0.0",
        "decisions": [{
            "familyId": str(packet["physicalLineageFamilies"][0]["familyId"]),
            "action": legacy["action"],
            "scenarioSelectionId": legacy["scenarioSelectionId"],
            "semanticAudit": legacy["semanticAudit"],
            "reason": legacy["reason"],
        }],
    }


def batch_no_plan_payload(packet: dict, reason: str = "Synthetic no-plan response.") -> dict:
    return {
        "schemaVersion": "5.0.0",
        "decisions": [
            {
                "familyId": str(family["familyId"]),
                "action": "NO_PLAN",
                "scenarioSelectionId": None,
                "semanticAudit": {
                    "externalOwnerAndScope": "UNRESOLVED",
                    "objectiveClassificationAndMaturity": "UNRESOLVED",
                    "rootDisplacementCausality": "UNRESOLVED",
                    "fullRefinementCausality": "UNRESOLVED",
                    "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
                },
                "reason": reason,
            }
            for family in packet.get("physicalLineageFamilies", [])
        ],
    }


def valid_trigger_payload(market: MarketData) -> dict:
    touch_index = market.m1_index_at_or_after(TOUCH_TIME - 60)
    selected = [
        market.m1_row(touch_index - 8)["barId"],
        f"M5:{BASE - 300}",
        market.m1_row(touch_index - 4)["barId"],
    ]
    return {
        "schemaVersion": "4.0.0",
        "action": "ARM_REACTION",
        "selectedBarIds": selected,
        "matureLiquidityIndex": 0,
        "m5CorrectionSwingIndex": 1,
        "chochReferenceIndex": 2,
        "reason": "Pre-existing SSL and correction-governing M1 high.",
    }


def completed_trigger_payload(market: MarketData) -> dict:
    touch_index = market.m1_index_at_or_after(TOUCH_TIME - 60)
    return {
        "schemaVersion": "4.6.0",
        "action": "ARM_REACTION",
        "selectedBarIds": [
            market.m1_row(touch_index - 8)["barId"],
            f"M5:{BASE - 300}",
            market.m1_row(touch_index - 4)["barId"],
            market.m1_row(touch_index + 3)["barId"],
        ],
        "matureLiquidityIndex": 0,
        "m5CorrectionSwingIndex": 1,
        "chochReferenceIndex": 2,
        "chochBreakIndex": 3,
        "reason": "Completed synthetic sweep and M1/M5 CHoCH transfer.",
    }


def direct_completed_trigger_payload(market: MarketData) -> dict:
    legacy = completed_trigger_payload(market)
    selected = legacy["selectedBarIds"]
    return {
        "schemaVersion": "4.8.0",
        "action": "ARM_REACTION",
        "matureLiquidityBarId": selected[legacy["matureLiquidityIndex"]],
        "m5CorrectionSwingBarId": selected[legacy["m5CorrectionSwingIndex"]],
        "chochReferenceBarId": selected[legacy["chochReferenceIndex"]],
        "chochBreakBarId": selected[legacy["chochBreakIndex"]],
        "sourceUpgradeSelectionId": None,
        "reason": legacy["reason"],
    }


def frozen_scenario(market: MarketData) -> dict:
    scenario = freeze_plan(valid_plan_payload(), market, PLAN_AT, set())
    assert scenario is not None
    touch = market.m1_row(market.m1_index_at_or_after(TOUCH_TIME - 60))
    scenario["childTouchAtUtc"] = utc_text(touch["available"])
    scenario["childTouchBarId"] = touch["barId"]
    return scenario


def test_plan_packet_excludes_m1_and_schema_uses_dynamic_ids() -> None:
    market = synthetic_market()
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    assert "M1" not in packet["bars"]["data"]
    schema = plan_schema(packet)
    enforce_gemini_schema_subset(schema)
    payload = {
        "schemaVersion": "5.0.0",
        "decisions": [{
            "familyId": "synthetic-causal-family",
            "action": "NO_PLAN",
            "scenarioSelectionId": None,
            "semanticAudit": {
                "externalOwnerAndScope": "UNRESOLVED",
                "objectiveClassificationAndMaturity": "UNRESOLVED",
                "rootDisplacementCausality": "UNRESOLVED",
                "fullRefinementCausality": "UNRESOLVED",
                "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
            },
            "reason": "No synthetic family.",
        }],
    }
    Draft202012Validator(schema).validate(payload)
    atomic_packet = with_synthetic_atomic_family(packet)
    atomic_schema = plan_schema(atomic_packet)
    item_schema = atomic_schema["properties"]["decisions"]["items"]
    enum_values = item_schema["properties"]["scenarioSelectionId"]["anyOf"][0]["enum"]
    assert enum_values == ["scenario-synthetic"]
    assert "selectedBarIds" not in item_schema["properties"]
    assert "root" not in item_schema["properties"] and "rootSelectionId" not in item_schema["properties"]
    assert "refinements" not in item_schema["properties"] and "lineagePathSelectionId" not in item_schema["properties"]
    assert not any(key in item_schema["properties"] for key in ("state", "phase", "asOfUtc", "entry", "stop"))

    map_packet = build_map_packet(market, PLAN_AT, "GOLD")
    map_response_schema = map_schema(map_packet)
    assert "side" not in map_response_schema["properties"]["objective"]["properties"]


def test_complete_agents_contract_is_sent_as_gemini_system_instruction() -> None:
    market = synthetic_market()
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    contract, _ = load_v4_contract("PLAN")
    system_instruction = system_instruction_for("PLAN", contract)
    dynamic_prompt = prompt_for("PLAN", packet)
    agents = runtime_agents_text("PLAN")
    metrics = enforce_system_instruction_bound(system_instruction, replay_v4.DEFAULTS)

    assert agents in system_instruction
    assert contract.rstrip() in system_instruction
    assert agents not in dynamic_prompt
    assert contract.rstrip() not in dynamic_prompt
    assert "## 16." not in system_instruction
    assert "## 17." not in system_instruction
    assert "3347.99" not in system_instruction
    assert "2025-08-21 short" not in system_instruction
    assert metrics["systemInstructionBytes"] == len(system_instruction.encode("utf-8"))

    body = build_generate_content_body(
        prompt=dynamic_prompt,
        system_instruction=system_instruction,
        images=[],
        media_resolutions=[],
        schema=plan_schema(packet),
        temperature=0.1,
        max_output_tokens=4096,
        thinking_level="low",
    )
    assert body["systemInstruction"]["parts"][0]["text"] == system_instruction
    assert body["contents"][0]["parts"][0]["text"] == dynamic_prompt
    assert body["generationConfig"]["maxOutputTokens"] == 4096
    assert body["generationConfig"]["thinkingConfig"] == {
        "thinkingLevel": "low"
    }

    map_contract, _ = load_v4_contract("MAP")
    map_instruction = system_instruction_for("MAP", map_contract)
    assert "## 3." in map_instruction and "## 4." in map_instruction
    assert "## 6." not in map_instruction and "## 8." not in map_instruction
    for section in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15):
        assert f"## {section}." in system_instruction


def test_plan_freezes_complete_lineage_and_rejects_wrong_pd_half() -> None:
    market = synthetic_market()
    scenario = freeze_plan(valid_plan_payload(), market, PLAN_AT, set())
    assert scenario and scenario["finalChild"]["tf"] == "M5"
    assert scenario["objective"]["price"] == 120.0
    assert scenario["scenarioHash"]
    direct_scenario = freeze_plan(direct_plan_payload(), market, PLAN_AT, set())
    assert direct_scenario and direct_scenario["semanticHash"] == scenario["semanticHash"]
    direct = direct_plan_payload()
    packet = {
        "physicalLineageFamilies": [
            {
                "familyId": "synthetic-causal-family",
                "rootSelections": [
                    {"selectionId": "root-synthetic", **direct["root"]}
                ],
                "childCandidates": [
                    {
                        "selectionOptions": [
                            {"selectionId": f"child-synthetic-{index}", **node}
                        ]
                    }
                    for index, node in enumerate(direct["refinements"])
                ],
            }
        ]
    }
    atomic_scenario = freeze_plan(
        atomic_plan_payload(packet), market, PLAN_AT, set(), packet
    )
    assert atomic_scenario and atomic_scenario["semanticHash"] == scenario["semanticHash"]
    path_packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    path_scenario = freeze_plan(
        path_plan_payload(path_packet), market, PLAN_AT, set(), path_packet
    )
    assert path_scenario and path_scenario["semanticHash"] == scenario["semanticHash"]
    atomic_scenario = freeze_plan(
        scenario_plan_payload(path_packet), market, PLAN_AT, set(), path_packet
    )
    assert atomic_scenario and atomic_scenario["semanticHash"] == scenario["semanticHash"]
    unresolved = scenario_plan_payload(path_packet)
    unresolved["semanticAudit"]["externalOwnerAndScope"] = "UNRESOLVED"
    try:
        freeze_plan(unresolved, market, PLAN_AT, set(), path_packet)
    except V4ContractError as exc:
        assert "unresolved semantic audit" in str(exc)
    else:
        raise AssertionError("PLAN with unresolved owner/scope audit was accepted")
    duplicate = {scenario["scenarioHash"]}
    try:
        freeze_plan(valid_plan_payload(), market, PLAN_AT, duplicate)
    except V4ContractError as exc:
        assert "duplicate scenario" in str(exc)
    else:
        raise AssertionError("duplicate scenario was accepted")


def test_continuation_objective_may_form_after_root_delivery_before_plan() -> None:
    market = synthetic_market()
    payload = valid_plan_payload()
    payload["selectedBarIds"].append(f"M30:{BASE + 1800}")
    payload["objective"] = {
        "barIndex": len(payload["selectedBarIds"]) - 1,
        "side": "HIGH",
        "kind": "EXTERNAL_SWING",
    }
    scenario = freeze_plan(payload, market, PLAN_AT, set())
    assert scenario is not None
    assert scenario["objective"]["barId"] == f"M30:{BASE + 1800}"
    root_delivery = market.bar(scenario["root"]["displacementBarId"], PLAN_AT)
    objective = market.bar(scenario["objective"]["barId"], PLAN_AT)
    assert objective["available"] > root_delivery["time"]


def test_post_touch_liquidity_matures_before_separate_sweep() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    touch_index = market.m1_index_at_or_after(TOUCH_TIME - 60)

    # Create a post-touch SSL, two closed confirming bars, then a separate sweep/recovery.
    updates = {
        touch_index + 1: (100.3, 100.5, 99.8, 100.2),
        touch_index + 2: (100.2, 101.3, 100.1, 100.6),
        touch_index + 3: (100.6, 101.2, 100.0, 100.8),
        touch_index + 4: (100.8, 101.0, 99.6, 100.1),
    }
    frame = market.frames["M1"]
    for index, values in updates.items():
        open_, high, low, close = values
        market.rates[index]["open"] = frame.open[index] = open_
        market.rates[index]["high"] = frame.high[index] = high
        market.rates[index]["low"] = frame.low[index] = low
        market.rates[index]["close"] = frame.close[index] = close

    monitor = build_reaction_monitor(market, scenario, TOUCH_TIME)
    dynamic_id = market.m1_row(touch_index + 1)["barId"]
    assert dynamic_id not in {item["liquidityBarId"] for item in monitor["candidates"]}

    events: list[dict] = []
    for index in range(touch_index + 1, touch_index + 5):
        row = market.m1_row(index)
        monitor = refresh_reaction_monitor(market, scenario, monitor, row["time"])
        monitor, created = advance_reaction_monitor(monitor, row, scenario["direction"])
        events.extend(created)

    candidate = next(
        item for item in monitor["candidates"]
        if item["liquidityBarId"] == dynamic_id
    )
    event = next(item for item in events if item["liquidityBarId"] == dynamic_id)
    assert candidate["qualifiedAtUtc"] < event["detectedAtUtc"]
    assert event["excursionBarId"] == market.m1_row(touch_index + 4)["barId"]

    current_price_is_premium_but_child_is_discount = valid_plan_payload()
    current_price_is_premium_but_child_is_discount["dealingRange"] = {
        "highIndex": 3,
        "lowIndex": 2,
    }
    assert freeze_plan(
        current_price_is_premium_but_child_is_discount, market, PLAN_AT, set()
    ) is not None

    wrong = valid_plan_payload()
    wrong["dealingRange"] = {"highIndex": 2, "lowIndex": 1}
    try:
        freeze_plan(wrong, market, PLAN_AT, set())
    except V4ContractError as exc:
        assert "child POI is not in discount" in str(exc)
    else:
        raise AssertionError("premium continuation long child POI was accepted")

    duplicate_objective = valid_plan_payload()
    duplicate_objective["intermediateLiquidityIndexes"] = [
        duplicate_objective["objective"]["barIndex"]
    ]
    try:
        freeze_plan(duplicate_objective, market, PLAN_AT, set())
    except V4ContractError as exc:
        assert "cannot also be intermediate" in str(exc)
    else:
        raise AssertionError("final objective was also accepted as intermediate liquidity")

    missing_kind = valid_plan_payload()
    missing_kind["objective"]["kind"] = None
    try:
        freeze_plan(missing_kind, market, PLAN_AT, set())
    except V4ContractError as exc:
        assert "liquidity kind" in str(exc)
    else:
        raise AssertionError("PLAN with no objective liquidity kind was accepted")


def test_final_sweep_extends_only_across_contiguous_excursion() -> None:
    liquidity_id = f"M1:{BASE - 600}"
    monitor = {
        "armedAtUtc": utc_text(BASE - 60),
        "candidates": [
            {"liquidityBarId": liquidity_id, "side": "BSL", "level": 100.0}
        ],
        "excursions": {},
        "completedLiquidityBarIds": [],
        "sweepEvents": [],
    }

    def row(offset: int, high: float, close: float) -> dict:
        timestamp = BASE + offset * 60
        return {
            "barId": f"M1:{timestamp}", "time": timestamp, "available": timestamp + 60,
            "open": 99.5, "high": high, "low": 99.0, "close": close,
        }

    monitor, _ = advance_reaction_monitor(monitor, row(0, 100.5, 99.8), "SHORT")
    monitor, _ = advance_reaction_monitor(monitor, row(1, 101.5, 100.8), "SHORT")
    monitor, _ = advance_reaction_monitor(monitor, row(2, 101.0, 99.7), "SHORT")
    event = monitor["sweepEvents"][0]
    assert event["excursionBarId"] == f"M1:{BASE + 60}"
    assert event["recoveryBarId"] == f"M1:{BASE + 120}"

    monitor, _ = advance_reaction_monitor(monitor, row(3, 99.8, 99.6), "SHORT")
    monitor, created = advance_reaction_monitor(monitor, row(4, 101.8, 99.5), "SHORT")
    assert created == []
    assert monitor["sweepEvents"] == [event]


def test_immediate_resweep_preserves_deepest_physical_extreme() -> None:
    liquidity_id = f"M1:{BASE - 600}"
    monitor = {
        "armedAtUtc": utc_text(BASE - 60),
        "candidates": [
            {"liquidityBarId": liquidity_id, "side": "SSL", "level": 100.0}
        ],
        "excursions": {},
        "completedLiquidityBarIds": [],
        "sweepEvents": [],
    }

    def row(offset: int, low: float, close: float) -> dict:
        timestamp = BASE + offset * 60
        return {
            "barId": f"M1:{timestamp}", "time": timestamp, "available": timestamp + 60,
            "open": 100.5, "high": 101.0, "low": low, "close": close,
        }

    monitor, _ = advance_reaction_monitor(monitor, row(0, 99.5, 99.8), "LONG")
    monitor, _ = advance_reaction_monitor(monitor, row(1, 98.0, 100.2), "LONG")
    first = monitor["sweepEvents"][0]
    assert first["excursionBarId"] == f"M1:{BASE + 60}"

    # The very next bar pierces again but is shallower. It extends the same
    # episode, so the original 98.0 extreme must remain the final SL anchor.
    monitor, created = advance_reaction_monitor(monitor, row(2, 99.0, 100.1), "LONG")
    assert len(created) == 1
    final = monitor["sweepEvents"][0]
    assert final["excursionBarId"] == f"M1:{BASE + 60}"
    assert final["recoveryBarId"] == f"M1:{BASE + 120}"


def test_external_reversal_separates_old_owner_break_from_new_owner_invalidation() -> None:
    market = synthetic_market()
    payload = valid_plan_payload()
    payload["scope"] = "EXTERNAL_REVERSAL"
    payload["ownerBreakTargetIndex"] = 2
    payload["ownerBreakIndex"] = 3
    scenario = freeze_plan(payload, market, PLAN_AT, set())
    assert scenario is not None
    assert scenario["mapProtectedSwing"]["barId"] == f"H1:{BASE - 10800}"
    assert scenario["ownerBreakTargetBarId"] == f"H1:{BASE - 3600}"
    assert scenario["ownerBreakBarId"] == f"H1:{BASE}"

    wrong_target = copy.deepcopy(payload)
    wrong_target["ownerBreakTargetIndex"] = 0
    try:
        freeze_plan(wrong_target, market, PLAN_AT, set())
    except V4ContractError as exc:
        assert "did not body-break" in str(exc)
    else:
        raise AssertionError("external reversal used the new-owner swing as the old-owner break target")


def test_rejection_actions_cannot_smuggle_semantic_evidence() -> None:
    market = synthetic_market()
    schema_shaped_no_plan = {
        "schemaVersion": "4.0.0",
        "action": "NO_PLAN",
        "selectedBarIds": [],
        "direction": None,
        "scope": None,
        "dealingRange": None,
        "objective": {"barIndex": None, "side": None, "kind": None},
        "mapProtectedSwingIndex": None,
        "ownerBreakTargetIndex": None,
        "ownerBreakIndex": None,
        "root": None,
        "refinements": [],
        "intermediateLiquidityIndexes": [],
        "reason": "No plan",
    }
    assert freeze_plan(schema_shaped_no_plan, market, PLAN_AT, set()) is None

    invalid_no_plan = valid_plan_payload()
    invalid_no_plan["action"] = "NO_PLAN"
    try:
        freeze_plan(invalid_no_plan, market, PLAN_AT, set())
    except V4ContractError as exc:
        assert "must not contain PLAN evidence" in str(exc)
    else:
        raise AssertionError("NO_PLAN retained hidden PLAN evidence")

    scenario = frozen_scenario(market)
    invalid_rejection = valid_trigger_payload(market)
    invalid_rejection["action"] = "REJECT_REACTION"
    try:
        freeze_trigger_watch(invalid_rejection, market, TOUCH_TIME, scenario)
    except V4ContractError as exc:
        assert "must not contain trigger evidence" in str(exc)
    else:
        raise AssertionError("REJECT_REACTION retained hidden trigger evidence")


def test_trigger_schema_has_no_engine_owned_fields() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    packet = build_trigger_packet(market, TOUCH_TIME + 4 * 60, "GOLD", scenario)
    schema = trigger_watch_schema(packet)
    enforce_gemini_schema_subset(schema)
    Draft202012Validator(schema).validate(direct_completed_trigger_payload(market))
    assert set(schema["properties"]) == {
        "schemaVersion", "action", "matureLiquidityBarId",
        "m5CorrectionSwingBarId", "chochReferenceBarId", "chochBreakBarId",
        "sourceUpgradeSelectionId", "reason",
    }
    try:
        enforce_gemini_schema_subset({"type": "array", "items": {"type": "string"}, "uniqueItems": True})
    except V4ContractError as exc:
        assert "unsupported keys" in str(exc)
    else:
        raise AssertionError("unsupported Gemini schema keyword reached the provider boundary")
    assert not any(key in schema["properties"] for key in ("price", "state", "phase", "asOfUtc", "watchEvents"))


def test_touch_then_separate_sweep_choch_order_fill_and_tp() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    watch = freeze_trigger_watch(valid_trigger_payload(market), market, TOUCH_TIME, scenario)
    assert watch is not None and watch["sweep"] is None
    touch_index = market.m1_index_at_or_after(TOUCH_TIME - 60)
    watch, order = advance_trigger_watch(market, scenario, watch, market.m1_row(touch_index), 0.0)
    assert watch["sweep"] is None and order is None
    watch, order = advance_trigger_watch(market, scenario, watch, market.m1_row(touch_index + 1), 0.0)
    assert watch["sweep"] is not None and order is None
    watch, order = advance_trigger_watch(market, scenario, watch, market.m1_row(touch_index + 2), 0.0)
    assert order is None
    watch, order = advance_trigger_watch(market, scenario, watch, market.m1_row(touch_index + 3), 0.0)
    assert order and order["model"] == "HTF_OB_REACTION"
    result, position = advance_pending(market, order, market.m1_row(touch_index + 4))
    assert result == "FILLED" and position
    trade = advance_position(market, position, market.m1_row(touch_index + 5))
    assert trade and trade["outcome"] == "TP" and trade["resultR"] > 0


def test_premature_sweep_and_through_delivery_are_rejected() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    watch = freeze_trigger_watch(valid_trigger_payload(market), market, TOUCH_TIME, scenario)
    touch_index = market.m1_index_at_or_after(TOUCH_TIME - 60)
    watch, order = advance_trigger_watch(market, scenario, watch, market.m1_row(touch_index), 0.0)
    assert watch["sweep"] is None and order is None
    fake_order = {
        "direction": "LONG", "entry": 101.0, "stop": 99.0, "target": 120.0,
        "orderId": "x", "scenarioHash": "s", "model": "HTF_OB_REACTION",
        "executionZone": {"low": 99.5, "high": 101.0},
    }
    row = {**market.m1_row(touch_index + 1), "low": 98.5, "high": 102.0, "spreadPoints": 2}
    result, position = advance_pending(market, fake_order, row)
    assert result == "CANCELED_THROUGH_DELIVERY" and position is None

    consumed_order = {
        **fake_order,
        "stop": 98.0,
        "executionZone": {"low": 100.0, "high": 101.0},
    }
    consumed_row = {**market.m1_row(touch_index + 1), "low": 99.9, "high": 101.2, "spreadPoints": 2}
    result, position = advance_pending(market, consumed_order, consumed_row)
    assert result == "CANCELED_EXECUTION_POI_CONSUMED" and position is None


def test_delivery_fvg_replacement_rejects_a_first_touch_through_fvg_distal() -> None:
    market = synthetic_market()
    row = {
        **market.m1_row(market.m1_index_at_or_after(TOUCH_TIME - 60) + 1),
        "low": 100.0,
        "high": 102.0,
        "close": 100.6,
        "spreadPoints": 2,
    }
    order = {
        "direction": "LONG",
        "entry": 101.0,
        "stop": 100.48,
        "target": 120.0,
        "orderId": "delivery-replacement",
        "scenarioHash": "scenario",
        "model": "DELIVERY_FVG_REPLACEMENT",
        "executionZone": {"low": 100.5, "high": 101.0},
        "deliveryFvg": {"low": 100.5, "high": 101.0},
        "buffer": 0.02,
    }
    result, position = advance_pending(market, order, row)
    assert result == "CANCELED_THROUGH_DELIVERY" and position is None


def test_local_reauthorization_cancels_only_exact_owner_or_source_break() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    ordinary = market.m1_row(market.m1_index_at_or_after(TOUCH_TIME - 60) + 2)
    assert local_scenario_cancel_reason(market, scenario, ordinary) is None
    broken = {**ordinary, "available": BASE + 7200}
    scenario["objective"]["price"] = 130.0
    scenario["objectiveFamily"]["orderedMembers"][0]["price"] = 130.0
    scenario["mapProtectedSwing"]["low"] = 100.0
    h1 = market.frames["H1"]
    h1.close[-1] = 99.5
    reason = local_scenario_cancel_reason(market, scenario, broken)
    assert reason == "OPPOSING_OWNER_CONFIRMED"
    rotation = copy.deepcopy(scenario)
    rotation["scope"] = "INTERNAL_ROTATION"
    assert local_scenario_cancel_reason(market, rotation, broken) is None


def test_delivery_fvg_replacement_is_single_use() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    watch = freeze_trigger_watch(valid_trigger_payload(market), market, TOUCH_TIME, scenario)
    assert watch
    touch_index = market.m1_index_at_or_after(TOUCH_TIME - 60)
    sweep = market.m1_row(touch_index + 1)
    watch["sweep"] = sweep
    watch["triggerProtectedSwing"] = sweep
    watch["executionOb"] = market.m1_row(touch_index + 2)
    order = {
        "orderId": "original", "scenarioHash": scenario["scenarioHash"], "model": "HTF_OB_REACTION",
        "direction": "LONG", "createdAtUtc": utc_text(sweep["available"]),
        "lastReauthorizedAtUtc": scenario["lastReauthorizedAtUtc"], "entry": 99.0,
        "stop": 98.0, "target": 120.0, "executionObBarId": watch["executionOb"]["barId"],
        "executionZone": {"low": 98.5, "high": 99.0}, "structuralInvalidation": 98.1,
        "spreadAtCreation": 0.02, "buffer": 0.02, "replacementUsed": False, "originalOrderId": None,
    }
    row = market.m1_row(touch_index + 3)
    first = market.m1_row(touch_index + 1)
    first["high"] = 100.0
    # Use a local copy with a clear bullish FVG relative to index-2.
    market.rates[touch_index + 1]["high"] = 100.0
    market.rates[touch_index + 3]["low"] = 100.5
    market.rates[touch_index + 3]["close"] = 102.0
    row = market.m1_row(touch_index + 3)
    replacement = delivery_replacement(market, scenario, watch, order, row, 0.0)
    assert replacement and replacement["replacementUsed"] is True
    assert delivery_replacement(market, scenario, watch, replacement, row, 0.0) is None


def test_all_runtime_states_and_per_execution_trigger_calls() -> None:
    runtime = new_runtime(0)
    assert_runtime_invariants(runtime)
    mapped = {"mapHash": "map-abc", "finalChild": None}
    mapped_value = copy.deepcopy(runtime)
    mapped_value["state"] = "MAPPED"
    mapped_value["scenario"] = mapped
    mapped_value["apiCallsByMap"] = {"map-abc": 1}
    assert_runtime_invariants(mapped_value)
    scenario = {"scenarioHash": "abc", "finalChild": {"obBarId": "M5:1"}}
    for state in ("PLANNED", "REACTION_MONITOR", "TRIGGER_WATCH", "PENDING", "FILLED"):
        value = copy.deepcopy(runtime)
        value["state"] = state
        value["scenario"] = scenario
        if state == "REACTION_MONITOR":
            value["reactionMonitor"] = {"candidates": []}
        if state in {"TRIGGER_WATCH", "PENDING", "FILLED"}:
            value["triggerWatch"] = {"x": 1}
        if state in {"PENDING", "FILLED"}:
            value["order"] = {"x": 1}
        if state == "FILLED":
            value["position"] = {"x": 1}
        value["acceptedScenarioHashes"] = ["abc"]
        value["apiCallsByScenario"] = {"abc": 2}
        assert_runtime_invariants(value)
    repeated_chains = copy.deepcopy(value)
    repeated_chains["apiCallsByScenario"] = {"abc": 3}
    assert_runtime_invariants(repeated_chains)
    invalid = copy.deepcopy(value)
    invalid["apiCallsByScenario"] = {"abc": -1}
    try:
        assert_runtime_invariants(invalid)
    except AssertionError as exc:
        assert "negative API call count" in str(exc)
    else:
        raise AssertionError("negative semantic call count was accepted")
    terminal = reset_terminal(value, "CLOSED")
    assert terminal["state"] == "FLAT" and terminal["closedTrades"] == 1


def test_multi_position_book_uses_book_identity_and_rejects_duplicate_execution() -> None:
    runtime = new_runtime(0)
    base = {
        "scenario": {},
        "order": {},
        "position": {"entryBarId": "M1:1700000000"},
    }
    runtime["openPositions"] = [
        {
            **copy.deepcopy(base),
            "bookId": "BOOK-A",
            "sourceFamilyKey": "SOURCE-A",
            "executionSignalKey": "EXEC-A",
        },
        {
            **copy.deepcopy(base),
            "bookId": "BOOK-B",
            "sourceFamilyKey": "SOURCE-B",
            "executionSignalKey": "EXEC-B",
        },
    ]
    # Independent positions may legitimately fill on the same M1 candle.
    assert_runtime_invariants(runtime)

    runtime["openPositions"][1]["executionSignalKey"] = "EXEC-A"
    try:
        assert_runtime_invariants(runtime)
    except AssertionError as exc:
        assert "physical execution" in str(exc)
    else:
        raise AssertionError("duplicate physical execution was accepted")


def test_scripted_provider_and_hash_ledger_are_deterministic() -> None:
    provider = ScriptedProvider([{"action": "NO_PLAN"}, {"action": "NO_PLAN"}])
    assert provider.decide().payload["action"] == "NO_PLAN"
    assert provider.decide().payload["action"] == "NO_PLAN"
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "ledger.jsonl"
        ledger = HashLedger(path)
        ledger.append("A", PLAN_AT, "FLAT", {"n": 1})
        ledger.append("B", PLAN_AT + 60, "PLANNED", {"n": 2})
        reopened = HashLedger(path)
        assert reopened.sequence == 2


def test_two_key_slots_are_local_selectable_and_never_written_to_config() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        original_secret = replay_v4.SECRET
        replay_v4.SECRET = Path(temporary) / "secret.json"
        try:
            replay_v4.save_secret(
                ["test-key-slot-one", "test-key-slot-two"],
                {**replay_v4.DEFAULTS, "apiKey": "must-not-survive"},
                active_slot=2,
            )
            selected, config = replay_v4.load_secret()
            assert selected == "test-key-slot-two"
            assert config["apiKeySlot"] == 2
            first, first_config = replay_v4.load_secret(1)
            assert first == "test-key-slot-one"
            assert first_config["apiKeySlot"] == 1
            raw = replay_v4.read_json(replay_v4.SECRET)
            assert "apiKey" not in raw
            assert "apiKey" not in raw["config"]
            assert raw["activeApiKeySlot"] == 2
            assert replay_v4.configured_key_count() == 2
        finally:
            replay_v4.SECRET = original_secret


def test_scripted_responses_never_pollute_shared_model_cache() -> None:
    market = synthetic_market()
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    schema = plan_schema(packet)
    invalid = batch_scenario_plan_payload(packet)
    invalid["decisions"][0]["scenarioSelectionId"] = "scenario-not-supplied"
    valid = batch_scenario_plan_payload(packet)
    config = {
        "symbol": "GOLD",
        "maximumPlanPromptBytes": 36000,
        "maximumTriggerWatchPromptBytes": 36000,
        "maximumApiCallsPerRun": 10,
        "maximumTokensPerRun": 100000,
        "planMaxOutputTokens": 1800,
        "triggerWatchMaxOutputTokens": 1200,
        "temperature": 0.1,
    }
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        original_cache = replay_v4.CACHE_ROOT
        replay_v4.CACHE_ROOT = root / "cache"
        try:
            runner = V4Runner(
                config=config,
                market=market,
                run_dir=root / "run",
                provider=ScriptedProvider([invalid, valid]),
                runtime=new_runtime(0),
            )
            try:
                runner._request("PLAN", PLAN_AT, packet, schema, [])
            except V4ContractError as exc:
                assert "structured response is invalid" in str(exc)
            else:
                raise AssertionError("unknown scenario option passed response schema")
            request_id = next((root / "run" / "requests").iterdir()).name
            request_dir = root / "run" / "requests" / request_id
            request_meta = json.loads(
                (request_dir / "request.json").read_text(encoding="utf-8")
            )
            saved_instruction_hash = hashlib.sha256(
                (request_dir / "system_instruction.txt").read_bytes()
            ).hexdigest()
            assert saved_instruction_hash == request_meta["systemInstructionMetrics"]["systemInstructionSha256"]
            assert not (replay_v4.CACHE_ROOT / request_id / "response.json").exists()

            payload, repeated_id, _ = runner._request("PLAN", PLAN_AT, packet, schema, [])
            assert repeated_id == request_id
            assert freeze_plan_batch(payload, market, PLAN_AT, packet, set())
            runner.promote_response_cache(repeated_id)
            assert not (replay_v4.CACHE_ROOT / repeated_id / "response.json").exists()
        finally:
            replay_v4.CACHE_ROOT = original_cache


def test_runner_never_calls_semantic_provider_between_engine_events() -> None:
    market = synthetic_market()
    scenario = freeze_plan(valid_plan_payload(), market, PLAN_AT, set())
    assert scenario
    scenario["parentApproachPrepared"] = True
    runtime = new_runtime(0)
    runtime.update(
        {
            "state": "PLANNED",
            "scenario": scenario,
            "acceptedScenarioHashes": [scenario["scenarioHash"]],
            "apiCallsByScenario": {scenario["scenarioHash"]: 1},
        }
    )
    config = {
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config=config,
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=runtime,
        )
        calls: list[tuple[int, list[dict]]] = []
        runner.request_trigger_watch = (  # type: ignore[method-assign]
            lambda as_of, events=None, choch=None, correction=None, breaks=None: calls.append(
                (as_of, list(events or []))
            )
        )
        touch_index = market.m1_index_at_or_after(TOUCH_TIME - 60)
        runner.process_bar(market.m1_row(touch_index - 1))
        assert calls == []
        runner.process_bar(market.m1_row(touch_index))
        assert calls == []
        assert runner.runtime["state"] == "REACTION_MONITOR"
        runner.process_bar(market.m1_row(touch_index + 1))
        assert calls == []
        runner.process_bar(market.m1_row(touch_index + 2))
        assert calls == []
        runner.process_bar(market.m1_row(touch_index + 3))
        assert calls == []
        runner.process_bar(market.m1_row(touch_index + 4))
        assert calls == []

        runner.runtime["state"] = "PENDING"
        runner.runtime["reactionMonitor"] = None
        runner.runtime["triggerWatch"] = {"triggerProtectedSwing": None}
        runner.runtime["order"] = {
            "orderId": "wait", "scenarioHash": scenario["scenarioHash"], "model": "HTF_OB_REACTION",
            "direction": "LONG", "entry": 90.0, "stop": 80.0, "target": 120.0,
            "executionZone": {"low": 89.0, "high": 90.0},
            "replacementUsed": True,
        }
        runner.process_bar(market.m1_row(touch_index + 2))
        assert calls == []

        runner.runtime["scenario"]["lastReauthorizedAtUtc"] = utc_text(BASE)
        aligned_index = market.m1_index_at_or_after(BASE + 3540)
        aligned_row = market.m1_row(aligned_index)
        assert aligned_row["available"] == BASE + 3600
        before = runner.stats["localReauthorizations"]
        runner.process_bar(aligned_row)
        assert runner.runtime["scenario"]["lastReauthorizedAtUtc"] == utc_text(BASE + 3600)
        assert runner.stats["localReauthorizations"] == before + 1
        assert calls == []

        runner.runtime["state"] = "FILLED"
        runner.runtime["position"] = {
            "orderId": "wait", "scenarioHash": scenario["scenarioHash"], "model": "HTF_OB_REACTION",
            "direction": "LONG", "entry": 100.0, "stop": 80.0, "target": 120.0,
            "risk": 20.0, "entryAtUtc": utc_text(TOUCH_TIME), "entryBarId": "M1:test",
        }
        runner.process_bar(market.m1_row(touch_index + 2))
        assert calls == []


def test_flat_plan_is_requested_before_contact_and_fingerprint_dedupes() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    assert packet["physicalLineageFamilies"]
    no_plan = {
        "schemaVersion": "5.0.0",
        "decisions": [{
            "familyId": "synthetic-causal-family",
            "action": "NO_PLAN",
            "scenarioSelectionId": None,
            "semanticAudit": {
                "externalOwnerAndScope": "UNRESOLVED",
                "objectiveClassificationAndMaturity": "UNRESOLVED",
                "rootDisplacementCausality": "UNRESOLVED",
                "fullRefinementCausality": "UNRESOLVED",
                "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
            },
            "reason": "Synthetic no-plan response.",
        }],
    }
    original_renderer = replay_v4.render_images
    original_builder = replay_v4.build_plan_packet
    replay_v4.render_images = lambda *_args, **_kwargs: []
    replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            runner = V4Runner(
                config=config,
                market=market,
                run_dir=Path(temporary),
                provider=ScriptedProvider([no_plan]),
                runtime=new_runtime(0),
            )
            assert runner.schedule_flat_plan(PLAN_AT)
            assert runner.stats["semanticRequests"] == 1
            assert runner.stats["flatPlanWakeups"] == 1
            assert not runner.schedule_flat_plan(PLAN_AT + 3600)
            assert runner.stats["semanticRequests"] == 1
            assert (
                runner.stats["flatPlanFingerprintSkips"]
                + runner.stats["flatLocalEvidenceSkips"]
            ) == 1
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_active_wait_loop_uses_no_semantic_calls() -> None:
    market = synthetic_market()
    scenario = freeze_plan(valid_plan_payload(), market, PLAN_AT, set())
    assert scenario
    scenario["parentApproachPrepared"] = True
    runtime = new_runtime(market.m1_index_at_or_after(PLAN_AT))
    runtime.update(
        {
            "state": "PLANNED",
            "scenario": scenario,
            "acceptedScenarioHashes": [scenario["scenarioHash"]],
            "apiCallsByScenario": {scenario["scenarioHash"]: 1},
        }
    )
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config=config,
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=runtime,
        )
        result = runner.run(PLAN_AT, TOUCH_TIME - 60, TOUCH_TIME - 60)
        assert result == "FOLLOW_THROUGH_EXHAUSTED"
        assert runner.runtime["state"] == "PLANNED"
        assert runner.stats["semanticRequests"] == 0
        assert runner.stats["activeZeroTokenBars"] > 0


def test_precontact_plan_survives_restart_and_waits_without_api() -> None:
    market = synthetic_market()
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    original_renderer = replay_v4.render_images
    original_builder = replay_v4.build_plan_packet
    replay_v4.render_images = lambda *_args, **_kwargs: []
    replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            runner = V4Runner(
                config=config,
                market=market,
                run_dir=run_dir,
                provider=ScriptedProvider([batch_scenario_plan_payload(packet)]),
                runtime=new_runtime(market.m1_index_at_or_after(PLAN_AT)),
            )
            assert runner.schedule_flat_plan(PLAN_AT)
            assert runner.runtime["state"] == "FLAT"
            assert len(runner.runtime["scenarioSlots"]) == 1
            assert runner.runtime["scenarioSlots"][0]["state"] == "PLANNED"
            assert runner.runtime["scenarioSlots"][0]["scenario"]["childTouchAtUtc"] is None
            assert runner.stats["semanticRequests"] == 1
            runner.save()

            restored = replay_v4.read_json(run_dir / "state.json")
            resumed = V4Runner(
                config=config,
                market=market,
                run_dir=run_dir,
                provider=ScriptedProvider([]),
                runtime=restored,
            )
            before = resumed.stats["semanticRequests"]
            result = resumed.run(PLAN_AT, TOUCH_TIME - 60, TOUCH_TIME - 60)
            assert result == "FOLLOW_THROUGH_EXHAUSTED"
            assert resumed.runtime["state"] == "FLAT"
            assert resumed.runtime["scenarioSlots"][0]["state"] == "PLANNED"
            assert resumed.stats["semanticRequests"] == before
            assert (
                resumed.stats["activeZeroTokenBars"]
                + resumed.stats["flatZeroTokenBars"]
            ) > 0
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_flat_h1_scheduler_does_not_repeat_unchanged_plan() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    original_renderer = replay_v4.render_images
    original_builder = replay_v4.build_plan_packet
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    no_plan = batch_no_plan_payload(packet)
    assert packet["physicalLineageFamilies"]
    replay_v4.render_images = lambda *_args, **_kwargs: []
    replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            runner = V4Runner(
                config=config,
                market=market,
                run_dir=Path(temporary),
                provider=ScriptedProvider([no_plan]),
                runtime=new_runtime(market.m1_index_at_or_after(PLAN_AT)),
            )
            runner.schedule_flat_plan(PLAN_AT)
            assert runner.stats["semanticRequests"] == 1
            runner.schedule_flat_plan(PLAN_AT + 3600)
            assert runner.stats["semanticRequests"] == 1
            assert (
                runner.stats["flatPlanFingerprintSkips"]
                + runner.stats["flatLocalEvidenceSkips"]
            ) == 1
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_continuous_flat_run_calls_once_when_root_is_approached() -> None:
    market = synthetic_market()
    # Leave one completed M1 candle between root delivery becoming knowable and
    # the first root touch. The event scheduler must wake during this window.
    first_after_delivery = market.m1_index_at_or_after(PLAN_AT)
    market.rates["open"][first_after_delivery] = 104.0
    market.rates["high"][first_after_delivery] = 104.6
    market.rates["low"][first_after_delivery] = 103.8
    market.rates["close"][first_after_delivery] = 104.2
    market.rates["open"][first_after_delivery + 1] = 102.0
    market.rates["high"][first_after_delivery + 1] = 102.2
    market.rates["low"][first_after_delivery + 1] = 100.9
    market.rates["close"][first_after_delivery + 1] = 101.1
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    original_renderer = replay_v4.render_images
    original_builder = replay_v4.build_plan_packet
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    assert packet["physicalLineageFamilies"]
    no_plan = batch_no_plan_payload(packet)
    replay_v4.render_images = lambda *_args, **_kwargs: []
    replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            runner = V4Runner(
                config=config,
                market=market,
                run_dir=Path(temporary),
                provider=ScriptedProvider([no_plan]),
                runtime=new_runtime(market.m1_index_at_or_after(PLAN_AT)),
            )
            result = runner.run(PLAN_AT, TOUCH_TIME - 60, TOUCH_TIME - 60)
            assert result == "COMPLETED"
            assert runner.stats["semanticRequests"] == 1
            assert runner.stats["flatZeroTokenBars"] > 0
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_event_driven_plan_calls_once_on_root_approach() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    family = packet["physicalLineageFamilies"][0]
    root = market.bar(family["rootBarId"], PLAN_AT)
    no_plan = batch_no_plan_payload(packet)
    original_renderer = replay_v4.render_images
    original_builder = replay_v4.build_plan_packet
    replay_v4.render_images = lambda *_args, **_kwargs: []
    replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            runner = V4Runner(
                config=config,
                market=market,
                run_dir=Path(temporary),
                provider=ScriptedProvider([no_plan]),
                runtime=new_runtime(0),
            )
            far = {
                "available": PLAN_AT + 60,
                "low": root["high"] + 2.0,
                "high": root["high"] + 2.5,
                "close": root["high"] + 2.2,
            }
            assert not runner.schedule_event_driven_flat_plan(far)
            assert runner.stats["semanticRequests"] == 0
            near = {
                "available": PLAN_AT + 120,
                "low": root["high"] - 0.1,
                "high": root["high"] + 1.0,
                "close": root["high"] + 0.2,
            }
            assert runner.schedule_event_driven_flat_plan(near)
            assert runner.stats["semanticRequests"] == 1
            assert not runner.schedule_event_driven_flat_plan(near)
            assert runner.stats["semanticRequests"] == 1
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_candidate_discovered_on_current_bar_cannot_trigger_plan() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    packet = with_synthetic_atomic_family(build_plan_packet(market, PLAN_AT, "GOLD"))
    family = packet["physicalLineageFamilies"][0]
    root = market.bar(family["rootBarId"], PLAN_AT)
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config=config, market=market, run_dir=Path(temporary),
            provider=ScriptedProvider([]), runtime=new_runtime(0),
        )
        now = PLAN_AT + 120
        runner.runtime["flatPlanCandidates"] = [{
            "familyId": family["familyId"], "direction": family["direction"],
            "rootBarId": family["rootBarId"],
            "initialDisplacementBarId": family["initialDisplacementBarId"],
            "rootLow": float(root["low"]), "rootHigh": float(root["high"]),
            "displacementAvailable": now, "knownAtUtc": utc_text(now),
            "firstSeenAtUtc": utc_text(now), "lastSeenAtUtc": utc_text(now),
            "authorityKeyAtDiscovery": "NO_EXTERNAL_AUTHORITY",
            "status": "REGISTERED", "previousClose": None,
            "lastObservedAtUtc": None, "approachEvent": None,
        }]
        row = {
            "available": now, "barId": f"M1:{now - 60}", "index": 10,
            "open": float(root["high"]) + 1.0,
            "high": float(root["high"]) + 1.2,
            "low": float(root["high"]), "close": float(root["high"]),
        }
        events = runner.advance_plan_candidate_ledger(row, "FLAT")
        assert events == []
        assert runner.runtime["flatPlanCandidates"][0]["approachEvent"] is None


def test_short_poi_departure_is_not_directional_approach() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config=config, market=market, run_dir=Path(temporary),
            provider=ScriptedProvider([]), runtime=new_runtime(0),
        )
        known = PLAN_AT
        runner.runtime["flatPlanCandidates"] = [{
            "familyId": "short-family", "direction": "SHORT",
            "rootBarId": "M15:0", "initialDisplacementBarId": "M15:0",
            "rootLow": 100.0, "rootHigh": 102.0,
            "displacementAvailable": known, "knownAtUtc": utc_text(known),
            "firstSeenAtUtc": utc_text(known), "lastSeenAtUtc": utc_text(known),
            "authorityKeyAtDiscovery": "NO_EXTERNAL_AUTHORITY",
            "status": "REGISTERED", "previousClose": 99.0,
            "lastObservedAtUtc": None, "approachEvent": None,
        }]
        # Supply proximal is 100. Price is already below it and continues away;
        # a one-sided high>=proximal check would falsely wake PLAN here.
        row = {
            "available": known + 120, "barId": f"M1:{known + 60}",
            "open": 99.0, "high": 99.2, "low": 97.0, "close": 97.2,
        }
        events = runner.advance_plan_candidate_ledger(row, "FLAT")
        assert events == []


def test_plan_wakes_only_at_the_actual_root_proximal_boundary() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config=config, market=market, run_dir=Path(temporary),
            provider=ScriptedProvider([]), runtime=new_runtime(0),
        )
        known = PLAN_AT
        runner.runtime["flatPlanCandidates"] = [{
            "familyId": "short-family", "direction": "SHORT",
            "rootBarId": "M15:0", "initialDisplacementBarId": "M15:0",
            "rootLow": 100.0, "rootHigh": 110.0,
            "displacementAvailable": known, "knownAtUtc": utc_text(known),
            "firstSeenAtUtc": utc_text(known), "lastSeenAtUtc": utc_text(known),
            "authorityKeyAtDiscovery": "NO_EXTERNAL_AUTHORITY",
            "status": "REGISTERED", "previousClose": 89.0,
            "lastObservedAtUtc": None, "approachEvent": None,
        }]
        far = {
            "available": known + 60, "barId": f"M1:{known}",
            "open": 89.0, "high": 91.0, "low": 88.5, "close": 90.5,
        }
        assert runner.advance_plan_candidate_ledger(far, "FLAT") == []
        near = {
            "available": known + 120, "barId": f"M1:{known + 60}",
            "open": 90.5, "high": 100.2, "low": 90.0, "close": 99.5,
        }
        events = runner.advance_plan_candidate_ledger(near, "FLAT")
        assert len(events) == 1
        assert events[0]["threshold"] == 100.0


def test_root_approach_that_traverses_the_whole_source_expires_locally() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config=config, market=market, run_dir=Path(temporary),
            provider=ScriptedProvider([]), runtime=new_runtime(0),
        )
        known = PLAN_AT
        runner.runtime["flatPlanCandidates"] = [{
            "familyId": "long-through", "direction": "LONG",
            "rootBarId": "M15:0", "initialDisplacementBarId": "M15:0",
            "rootLow": 100.0, "rootHigh": 110.0,
            "displacementAvailable": known, "knownAtUtc": utc_text(known),
            "firstSeenAtUtc": utc_text(known), "lastSeenAtUtc": utc_text(known),
            "authorityKeyAtDiscovery": "NO_EXTERNAL_AUTHORITY",
            "status": "REGISTERED", "previousClose": 112.0,
            "lastObservedAtUtc": None, "approachEvent": None,
        }]
        row = {
            "available": known + 60, "barId": f"M1:{known}",
            "open": 112.0, "high": 112.2, "low": 99.5, "close": 105.0,
        }
        assert runner.advance_plan_candidate_ledger(row, "FLAT") == []
        candidate = runner.runtime["flatPlanCandidates"][0]
        assert candidate["status"] == "EXPIRED_APPROACH_THROUGH_SOURCE"
        assert runner.stats["planApproachesExpiredThroughSource"] == 1


def test_new_family_already_touched_before_discovery_is_not_queued() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    packet = with_synthetic_atomic_family(build_plan_packet(market, PLAN_AT, "GOLD"))
    packet["physicalLineageFamilies"][0]["rootLaterProximalTouched"] = True
    original_builder = replay_v4.build_plan_packet
    replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            runner = V4Runner(
                config=config, market=market, run_dir=Path(temporary),
                provider=ScriptedProvider([]), runtime=new_runtime(0),
            )
            runner.refresh_flat_plan_candidates(PLAN_AT)
            assert runner.runtime["flatPlanCandidates"] == []
            assert runner.stats["flatPlanCandidatesSkippedAlreadyTouched"] == 1
            runner.runtime["lastPlanCandidateRefreshM5"] = None
            runner.refresh_flat_plan_candidates(PLAN_AT)
            assert runner.stats["flatPlanCandidatesSkippedAlreadyTouched"] == 1
    finally:
        replay_v4.build_plan_packet = original_builder


def test_simultaneous_root_approaches_are_reviewed_in_one_plan_packet() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    packet = with_synthetic_atomic_family(build_plan_packet(market, PLAN_AT, "GOLD"))
    captured: dict[str, Any] = {}
    original_builder = replay_v4.build_plan_packet

    def capture_builder(*_args: Any, **kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return packet

    replay_v4.build_plan_packet = capture_builder  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            runner = V4Runner(
                config=config, market=market, run_dir=Path(temporary),
                provider=ScriptedProvider([]), runtime=new_runtime(0),
            )
            runner.request_plan = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
            row = {
                "available": PLAN_AT, "barId": f"M1:{PLAN_AT - 60}",
                "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0,
            }
            events = [
                {"familyId": "family-a", "knownAtUtc": utc_text(PLAN_AT - 600), "eligible": True},
                {"familyId": "family-b", "knownAtUtc": utc_text(PLAN_AT - 300), "eligible": True},
            ]
            assert runner.schedule_event_driven_flat_plan(row, approach_events=events)
            assert captured["focus_family_ids"] == {"family-a", "family-b"}
            assert captured["approach_events"] == events
    finally:
        replay_v4.build_plan_packet = original_builder


def test_active_bar_approach_cannot_be_resurrected_after_terminal() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    with tempfile.TemporaryDirectory() as temporary:
        runtime = new_runtime(0)
        runtime.update({"state": "PLANNED", "scenario": copy.deepcopy(scenario)})
        runner = V4Runner(
            config=config, market=market, run_dir=Path(temporary),
            provider=ScriptedProvider([]), runtime=runtime,
        )
        known = PLAN_AT
        runner.runtime["flatPlanCandidates"] = [{
            "familyId": "new-long", "direction": "LONG",
            "rootBarId": "M15:0", "initialDisplacementBarId": "M15:0",
            "rootLow": 100.0, "rootHigh": 102.0,
            "displacementAvailable": known, "knownAtUtc": utc_text(known),
            "firstSeenAtUtc": utc_text(known), "lastSeenAtUtc": utc_text(known),
            "authorityKeyAtDiscovery": "NO_EXTERNAL_AUTHORITY",
            "status": "REGISTERED", "previousClose": 105.0,
            "lastObservedAtUtc": None, "approachEvent": None,
        }]
        row = {
            "available": known + 120, "barId": f"M1:{known + 60}",
            "open": 105.0, "high": 105.2, "low": 101.8, "close": 102.2,
        }
        events = runner.advance_plan_candidate_ledger(row, "PLANNED")
        assert events == []
        candidate = runner.runtime["flatPlanCandidates"][0]
        assert candidate["status"] == "MISSED_ACTIVE_SCENARIO"
        runner.runtime = reset_terminal(runner.runtime, "CANCELED")
        assert not runner.schedule_event_driven_flat_plan(row, approach_events=events)
        assert runner.stats["semanticRequests"] == 0


def test_plan_packet_uses_exact_m1_clock_and_keeps_latest_m5_context() -> None:
    market = synthetic_market()
    packet = build_plan_packet(market, PLAN_AT, "GOLD")
    latest_m1 = market.bars("M1", PLAN_AT, 1)[-1]
    latest_m5 = market.bars("M5", PLAN_AT, 1)[-1]
    assert packet["executionReference"]["barId"] == latest_m1["barId"]
    assert packet["executionReference"]["close"] == latest_m1["close"]
    assert packet["decisionReference"]["barId"] == latest_m5["barId"]


def test_june_0643_short_family_is_departure_not_poi_approach() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2026-01-01_2026-08-12.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2026-05-20T00:00:00Z"),
        parse_utc("2026-06-08T00:00:00Z"),
        0.01,
    )
    as_of = parse_utc("2026-06-01T06:43:00Z")
    packet = build_plan_packet(market, as_of, "GOLD")
    assert all(
        family["familyId"] != "dce0154c5130"
        for family in packet["physicalLineageFamilies"]
    )
    assert packet["executionReference"]["close"] == 4512.8
    assert packet["decisionReference"]["close"] == 4515.48


def test_event_driven_plan_wakes_on_root_touch_before_child_touch() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    family = packet["physicalLineageFamilies"][0]
    root = market.bar(family["rootBarId"], PLAN_AT)
    original_renderer = replay_v4.render_images
    original_builder = replay_v4.build_plan_packet
    replay_v4.render_images = lambda *_args, **_kwargs: []
    replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            runner = V4Runner(
                config=config,
                market=market,
                run_dir=Path(temporary),
                provider=ScriptedProvider([
                    batch_no_plan_payload(packet, "Synthetic root-touch review.")
                ]),
                runtime=new_runtime(0),
            )
            height = float(root["high"]) - float(root["low"])
            far = {
                "available": PLAN_AT + 60,
                "low": float(root["high"]) + height * 1.5,
                "high": float(root["high"]) + height * 2.0,
                "close": float(root["high"]) + height * 1.75,
            }
            assert not runner.schedule_event_driven_flat_plan(far)
            midpoint = (float(root["low"]) + float(root["high"])) / 2.0
            touched = {
                "available": PLAN_AT + 120,
                "low": midpoint if family["direction"] == "LONG" else float(root["low"]) - 1.0,
                "high": midpoint if family["direction"] == "SHORT" else float(root["high"]) + 1.0,
                "close": midpoint,
            }
            assert runner.schedule_event_driven_flat_plan(touched)
            assert runner.stats["semanticRequests"] == 1
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_active_plan_never_wakes_a_second_plan() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    base_packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    original_renderer = replay_v4.render_images
    original_builder = replay_v4.build_plan_packet
    replay_v4.render_images = lambda *_args, **_kwargs: []
    try:
        with tempfile.TemporaryDirectory() as temporary:
            runtime = new_runtime(0)
            runtime.update({
                "state": "PLANNED", "scenario": copy.deepcopy(scenario),
                "acceptedScenarioHashes": [scenario["scenarioHash"]],
                "apiCallsByScenario": {scenario["scenarioHash"]: 1},
            })
            runner = V4Runner(
                config=config, market=market, run_dir=Path(temporary),
                provider=ScriptedProvider([]), runtime=runtime,
            )
            replay_v4.build_plan_packet = lambda *_args, **_kwargs: copy.deepcopy(base_packet)  # type: ignore[assignment]
            family = base_packet["physicalLineageFamilies"][0]
            root = market.bar(family["rootBarId"], PLAN_AT)
            near = {
                "available": PLAN_AT + 120,
                "low": root["low"], "high": root["high"], "close": root["high"],
            }
            assert not runner.schedule_event_driven_flat_plan(near)
            assert runner.stats["semanticRequests"] == 0

        with tempfile.TemporaryDirectory() as temporary:
            opposite_packet = copy.deepcopy(base_packet)
            opposite_packet["physicalLineageFamilies"][0]["direction"] = "SHORT"
            runtime = new_runtime(0)
            runtime.update({
                "state": "PLANNED", "scenario": copy.deepcopy(scenario),
                "acceptedScenarioHashes": [scenario["scenarioHash"]],
                "apiCallsByScenario": {scenario["scenarioHash"]: 1},
            })
            runner = V4Runner(
                config=config, market=market, run_dir=Path(temporary),
                provider=ScriptedProvider([]), runtime=runtime,
            )
            replay_v4.build_plan_packet = lambda *_args, **_kwargs: copy.deepcopy(opposite_packet)  # type: ignore[assignment]
            family = opposite_packet["physicalLineageFamilies"][0]
            root = market.bar(family["rootBarId"], PLAN_AT)
            midpoint = (float(root["low"]) + float(root["high"])) / 2.0
            near = {
                "available": PLAN_AT + 120,
                "low": float(root["low"]) - 0.1,
                "high": midpoint,
                "close": midpoint,
            }
            assert not runner.schedule_event_driven_flat_plan(near)
            assert runner.stats["semanticRequests"] == 0
            assert runner.stats["challengerPlanWakeups"] == 0
            assert runner.runtime["state"] == "PLANNED"
            assert runner.runtime["scenario"]["scenarioHash"] == scenario["scenarioHash"]
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_parked_plan_restores_without_api_and_stale_touch_is_discarded() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }

    def runtime_with_parked() -> dict:
        active = copy.deepcopy(scenario)
        active["scenarioHash"] = "active-challenger"
        runtime = new_runtime(0)
        runtime.update({
            "state": "PLANNED", "scenario": active,
            "acceptedScenarioHashes": [scenario["scenarioHash"], active["scenarioHash"]],
            "apiCallsByScenario": {scenario["scenarioHash"]: 1, active["scenarioHash"]: 1},
            "parkedScenarios": [{
                "state": "PLANNED",
                "scenario": copy.deepcopy(scenario),
                "reactionMonitor": None,
                "parkedAtUtc": utc_text(PLAN_AT),
                "externalAuthorityKeyAtPark": "NO_EXTERNAL_AUTHORITY",
                "externalAuthorityDirectionAtPark": None,
            }],
        })
        return runtime

    with tempfile.TemporaryDirectory() as temporary:
        run_dir = Path(temporary)
        runner = V4Runner(
            config=config, market=market, run_dir=run_dir,
            provider=ScriptedProvider([]), runtime=runtime_with_parked(),
        )
        runner.save()
        runner = V4Runner(
            config=config, market=market, run_dir=run_dir,
            provider=ScriptedProvider([]),
            runtime=replay_v4.read_json(run_dir / "state.json"),
        )
        assert len(runner.runtime["parkedScenarios"]) == 1
        runner.cancel(PLAN_AT + 60, "SYNTHETIC_CHALLENGER_CANCELED")
        assert runner.runtime["state"] == "PLANNED"
        assert runner.runtime["scenario"]["scenarioHash"] == scenario["scenarioHash"]
        assert runner.stats["semanticRequests"] == 0
        assert runner.stats["scenariosRestored"] == 1

    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config=config, market=market, run_dir=Path(temporary),
            provider=ScriptedProvider([]), runtime=runtime_with_parked(),
        )
        runner.cancel(TOUCH_TIME + 60, "SYNTHETIC_CHALLENGER_CANCELED")
        assert runner.runtime["state"] == "FLAT"
        assert runner.stats["semanticRequests"] == 0
        assert runner.stats["parkedScenariosDiscarded"] == 1


def test_accepted_challenger_isolated_in_lane_and_external_reversal_advances_owner() -> None:
    market = synthetic_market()
    original = frozen_scenario(market)
    packet = with_synthetic_atomic_family(build_plan_packet(market, PLAN_AT, "GOLD"))
    packet["physicalLineageFamilies"][0]["direction"] = "SHORT"
    response = batch_no_plan_payload(
        packet, "Synthetic response replaced by the frozen fixture."
    )
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    original_renderer = replay_v4.render_images
    original_freezer = replay_v4.freeze_plan
    original_batch_freezer = replay_v4.freeze_plan_batch
    original_builder = replay_v4.build_plan_packet
    replay_v4.render_images = lambda *_args, **_kwargs: []
    replay_v4.build_plan_packet = lambda *_args, **_kwargs: copy.deepcopy(packet)  # type: ignore[assignment]
    try:
        challenger = copy.deepcopy(original)
        challenger.update({
            "scenarioHash": "internal-challenger",
            "semanticHash": "internal-challenger-semantic",
            "direction": "SHORT",
            "scope": "INTERNAL_ROTATION",
        })
        replay_v4.freeze_plan = lambda *_args, **_kwargs: copy.deepcopy(challenger)  # type: ignore[assignment]
        replay_v4.freeze_plan_batch = lambda *_args, **_kwargs: [copy.deepcopy(challenger)]  # type: ignore[assignment]
        with tempfile.TemporaryDirectory() as temporary:
            runtime = new_runtime(0)
            runtime.update({
                "state": "PLANNED", "scenario": copy.deepcopy(original),
                "acceptedScenarioHashes": [original["scenarioHash"]],
                "apiCallsByScenario": {original["scenarioHash"]: 1},
                "externalMapAuthority": external_authority_from_scenario(original),
            })
            runner = V4Runner(
                config=config, market=market, run_dir=Path(temporary),
                provider=ScriptedProvider([response]), runtime=runtime,
            )
            runner.request_plan(
                PLAN_AT + 60, packet=copy.deepcopy(packet),
                plan_fingerprint="challenger", challenger=True,
            )
            assert runner.runtime["scenario"]["scenarioHash"] == original["scenarioHash"]
            assert len(runner.runtime["scenarioSlots"]) == 1
            assert runner.runtime["scenarioSlots"][0]["scenario"]["scenarioHash"] == "internal-challenger"
            assert runner.runtime["scenarioSlots"][0]["scenario"]["ownerStatus"] == "CHALLENGER"
            assert runner.runtime["parkedScenarios"] == []
            assert runner.stats["semanticRequests"] == 1

        reversal = copy.deepcopy(original)
        reversal.update({
            "scenarioHash": "external-reversal-challenger",
            "semanticHash": "external-reversal-semantic",
            "direction": "SHORT",
            "scope": "EXTERNAL_REVERSAL",
            "frozenAtUtc": utc_text(PLAN_AT + 60),
        })
        replay_v4.freeze_plan = lambda *_args, **_kwargs: copy.deepcopy(reversal)  # type: ignore[assignment]
        replay_v4.freeze_plan_batch = lambda *_args, **_kwargs: [copy.deepcopy(reversal)]  # type: ignore[assignment]
        with tempfile.TemporaryDirectory() as temporary:
            runtime = new_runtime(0)
            runtime.update({
                "state": "PLANNED", "scenario": copy.deepcopy(original),
                "acceptedScenarioHashes": [original["scenarioHash"]],
                "apiCallsByScenario": {original["scenarioHash"]: 1},
                "externalMapAuthority": {
                    **external_authority_from_scenario(original),
                    "status": "REMAP_REQUIRED",
                },
            })
            runner = V4Runner(
                config=config, market=market, run_dir=Path(temporary),
                provider=ScriptedProvider([response]), runtime=runtime,
            )
            runner.request_plan(
                PLAN_AT + 60, packet=copy.deepcopy(packet),
                plan_fingerprint="reversal", challenger=True,
            )
            assert runner.runtime["scenario"]["scenarioHash"] == original["scenarioHash"]
            assert len(runner.runtime["scenarioSlots"]) == 1
            assert runner.runtime["scenarioSlots"][0]["scenario"]["scenarioHash"] == "external-reversal-challenger"
            assert runner.runtime["scenarioSlots"][0]["scenario"]["ownerStatus"] == "ACTIVE"
            assert runner.runtime["ownerEpoch"] == 1
            assert runner.runtime["parkedScenarios"] == []
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.freeze_plan = original_freezer
        replay_v4.freeze_plan_batch = original_batch_freezer
        replay_v4.build_plan_packet = original_builder


def test_resume_gets_a_fresh_operational_budget_without_resetting_totals() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD",
        "brokerStopsLevelPrice": 0.0,
        "point": 0.01,
        "dataset": "unused",
        "warmupStartUtc": utc_text(BASE - 10800),
        "providerRetries": 0,
        "geminiFallbackModel": "",
        "planFallbackModel": "",
        "authorityPlanFallbackModel": "",
        "maximumApiCallsPerRun": 1,
        "maximumTokensPerRun": 100000,
    }
    no_plan: dict = {}

    class CountingGemini(replay_v4.GeminiProvider):
        def decide(self, **_kwargs: object) -> replay_v4.ProviderResult:
            self.last_attempt_count = 1
            return replay_v4.ProviderResult(
                payload=no_plan,
                usage={
                    "promptTokenCount": 80,
                    "candidatesTokenCount": 20,
                    "totalTokenCount": 100,
                },
                model="synthetic-gemini",
                provider_calls=1,
            )

    original_renderer = replay_v4.render_images
    original_builder = replay_v4.build_plan_packet
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    replay_v4.render_images = lambda *_args, **_kwargs: []
    try:
        with tempfile.TemporaryDirectory() as temporary:
            packet = copy.deepcopy(packet)
            packet["physicalLineageFamilies"][0]["familyId"] += (
                "-" + Path(temporary).name
            )
            no_plan = batch_no_plan_payload(packet)
            runtime = new_runtime(market.m1_index_at_or_after(PLAN_AT))
            seed = V4Runner(
                config=config,
                market=market,
                run_dir=Path(temporary),
                provider=ScriptedProvider([]),
                runtime=runtime,
            )
            seed.stats["providerApiCalls"] = 99
            seed.stats["totalTokens"] = 500000

            replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
            first = V4Runner(
                config=config,
                market=market,
                run_dir=Path(temporary),
                provider=CountingGemini("unused", config),
                runtime=runtime,
            )
            first.schedule_flat_plan(PLAN_AT)
            assert first.stats["providerApiCalls"] == 100
            assert first.stats["totalTokens"] == 500100
            assert first.segment_usage() == {
                "segmentProviderApiCalls": 1,
                "segmentTotalTokens": 100,
            }

            packet = copy.deepcopy(packet)
            packet["physicalLineageFamilies"][0]["familyId"] += "-next-segment"
            no_plan = batch_no_plan_payload(packet)
            replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
            # Simulate a newly registered local structure event.  A process
            # restart alone must not rebuild an unchanged family.
            runtime["lastLocalDiscoveryFingerprint"] = None
            resumed = V4Runner(
                config=config,
                market=market,
                run_dir=Path(temporary),
                provider=CountingGemini("unused", config),
                runtime=runtime,
            )
            resumed.schedule_flat_plan(PLAN_AT + 3600)
            assert resumed.stats["providerApiCalls"] == 101
            assert resumed.stats["totalTokens"] == 500200
            assert resumed.segment_usage() == {
                "segmentProviderApiCalls": 1,
                "segmentTotalTokens": 100,
            }
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_plan_budget_pause_does_not_consume_the_h1_event() -> None:
    market = synthetic_market()
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD",
        "brokerStopsLevelPrice": 0.0,
        "point": 0.01,
    }
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    original_builder = replay_v4.build_plan_packet
    replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            runner = V4Runner(
                config=config,
                market=market,
                run_dir=Path(temporary),
                provider=ScriptedProvider([]),
                runtime=new_runtime(market.m1_index_at_or_after(PLAN_AT)),
            )

            def budget_stop(*_args: object, **_kwargs: object) -> None:
                raise V4ContractError("TOKEN_BUDGET_BEFORE_REQUEST")

            runner.request_plan = budget_stop  # type: ignore[method-assign]
            try:
                runner.schedule_flat_plan(PLAN_AT)
            except V4ContractError as exc:
                assert str(exc) == "TOKEN_BUDGET_BEFORE_REQUEST"
            else:
                raise AssertionError("synthetic budget stop did not propagate")
            assert runner.runtime.get("lastPlanH1Available") is None

            runner.request_plan = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
            assert runner.schedule_flat_plan(PLAN_AT)
            assert runner.runtime["lastPlanH1Available"] == runner.latest_h1_available(PLAN_AT)
    finally:
        replay_v4.build_plan_packet = original_builder


def test_recoverable_json_cutoff_retries_with_minimal_thinking_and_counts_all_tokens() -> None:
    config = {
        **replay_v4.DEFAULTS,
        "planModel": "gemini-test",
        "geminiFallbackModel": "",
        "providerRetries": 1,
        "planThinkingLevel": "low",
        "minimumCallIntervalSeconds": 0,
    }
    thinking_levels: list[str | None] = []
    original_generate = replay_v4.generate_structured_decision

    def fake_generate(**kwargs: object) -> GeminiResponse:
        thinking_levels.append(str(kwargs.get("thinking_level")))
        if len(thinking_levels) == 1:
            raise GeminiReplayError(
                "structured JSON truncated (finishReason=MAX_TOKENS)",
                usage={
                    "promptTokenCount": 20,
                    "thoughtsTokenCount": 8,
                    "candidatesTokenCount": 2,
                    "totalTokenCount": 30,
                },
                request_was_sent=True,
                recoverable=True,
            )
        return GeminiResponse(
            payload={"ok": True},
            usage={
                "promptTokenCount": 10,
                "thoughtsTokenCount": 1,
                "candidatesTokenCount": 4,
                "totalTokenCount": 15,
            },
            model="gemini-test",
        )

    replay_v4.generate_structured_decision = fake_generate  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as temporary:
            result = replay_v4.GeminiProvider("unused", config).decide(
                phase="PLAN",
                request_dir=Path(temporary),
                prompt="test",
                system_instruction="test",
                images=[],
                schema={"type": "object"},
            )
        assert thinking_levels == ["low", "minimal"]
        assert result.provider_calls == 2
        assert result.usage["promptTokenCount"] == 30
        assert result.usage["thoughtsTokenCount"] == 9
        assert result.usage["candidatesTokenCount"] == 6
        assert result.usage["totalTokenCount"] == 45
    finally:
        replay_v4.generate_structured_decision = original_generate


def test_gemini_quota_circuit_skips_exhausted_primary_after_first_429() -> None:
    config = {
        **replay_v4.DEFAULTS,
        "planModel": "gemini-flash",
        "geminiFallbackModel": "gemini-flash-lite",
        "planFallbackModel": "gemini-flash-lite",
        "providerRetries": 0,
        "minimumCallIntervalSeconds": 0,
    }
    called_models: list[str] = []
    original_generate = replay_v4.generate_structured_decision

    def fake_generate(**kwargs: object) -> GeminiResponse:
        model = str(kwargs["model"])
        called_models.append(model)
        if model == "gemini-flash":
            raise GeminiReplayError(
                "Gemini HTTP 429: quota exhausted",
                request_was_sent=True,
            )
        return GeminiResponse(
            payload={"ok": True},
            usage={"totalTokenCount": 10},
            model=model,
        )

    replay_v4.generate_structured_decision = fake_generate  # type: ignore[assignment]
    try:
        provider = replay_v4.GeminiProvider("unused", config)
        with tempfile.TemporaryDirectory() as temporary:
            for suffix in ("first", "second"):
                provider.decide(
                    phase="PLAN",
                    request_dir=Path(temporary) / suffix,
                    prompt="test",
                    system_instruction="test",
                    images=[],
                    schema={"type": "object"},
                )
        assert called_models == [
            "gemini-flash", "gemini-flash-lite", "gemini-flash-lite"
        ]
    finally:
        replay_v4.generate_structured_decision = original_generate


def test_gemini_429_switches_key_before_model_fallback() -> None:
    config = {
        **replay_v4.DEFAULTS,
        "planModel": "gemini-flash-lite",
        "planFallbackModel": "",
        "geminiFallbackModel": "",
        "providerRetries": 0,
        "minimumCallIntervalSeconds": 0,
    }
    called: list[tuple[str, str]] = []
    original_generate = replay_v4.generate_structured_decision

    def fake_generate(**kwargs: object) -> GeminiResponse:
        key = str(kwargs["api_key"])
        model = str(kwargs["model"])
        called.append((key, model))
        if key == "paid-project-one":
            raise GeminiReplayError(
                "Gemini HTTP 429: project quota exhausted",
                request_was_sent=True,
            )
        return GeminiResponse(
            payload={"ok": True},
            usage={"totalTokenCount": 10},
            model=model,
        )

    replay_v4.generate_structured_decision = fake_generate  # type: ignore[assignment]
    try:
        provider = replay_v4.GeminiProvider(
            [(1, "paid-project-one"), (2, "paid-project-two")],
            config,
        )
        with tempfile.TemporaryDirectory() as temporary:
            first = provider.decide(
                phase="PLAN",
                request_dir=Path(temporary) / "first",
                prompt="test",
                system_instruction="test",
                images=[],
                schema={"type": "object"},
            )
            second = provider.decide(
                phase="PLAN",
                request_dir=Path(temporary) / "second",
                prompt="test",
                system_instruction="test",
                images=[],
                schema={"type": "object"},
            )
        assert called == [
            ("paid-project-one", "gemini-flash-lite"),
            ("paid-project-two", "gemini-flash-lite"),
            ("paid-project-two", "gemini-flash-lite"),
        ]
        assert first.provider_calls == 2
        assert first.api_key_slot == 2
        assert second.provider_calls == 1
        assert second.api_key_slot == 2
        assert provider.active_key_slot == 2
        assert provider.disabled_key_models == {(1, "gemini-flash-lite")}
    finally:
        replay_v4.generate_structured_decision = original_generate


def test_trigger_watch_inherits_global_lite_fallback_on_quota() -> None:
    config = {
        **replay_v4.DEFAULTS,
        "triggerWatchModel": "gemini-flash",
        "geminiFallbackModel": "gemini-flash-lite",
        "triggerWatchFallbackModel": "",
        "providerRetries": 0,
        "minimumCallIntervalSeconds": 0,
    }
    called_models: list[str] = []
    original_generate = replay_v4.generate_structured_decision

    def fake_generate(**kwargs: object) -> GeminiResponse:
        model = str(kwargs["model"])
        called_models.append(model)
        if model == "gemini-flash":
            raise GeminiReplayError(
                "Gemini HTTP 429: quota exhausted",
                request_was_sent=True,
            )
        return GeminiResponse(
            payload={"ok": True},
            usage={"totalTokenCount": 10},
            model=model,
        )

    replay_v4.generate_structured_decision = fake_generate  # type: ignore[assignment]
    try:
        provider = replay_v4.GeminiProvider("unused", config)
        with tempfile.TemporaryDirectory() as temporary:
            result = provider.decide(
                phase="TRIGGER_WATCH",
                request_dir=Path(temporary),
                prompt="test",
                system_instruction="test",
                images=[],
                schema={"type": "object"},
            )
            assert result.model == "gemini-flash-lite"
        assert called_models == ["gemini-flash", "gemini-flash-lite"]
    finally:
        replay_v4.generate_structured_decision = original_generate


def test_successful_server_retry_does_not_poison_the_next_flash_request() -> None:
    config = {
        **replay_v4.DEFAULTS,
        "triggerWatchModel": "gemini-flash",
        "triggerWatchFallbackModel": "",
        "providerRetries": 1,
        "minimumCallIntervalSeconds": 0,
    }
    called_models: list[str] = []
    original_generate = replay_v4.generate_structured_decision
    original_sleep = replay_v4.time.sleep

    def fake_generate(**kwargs: object) -> GeminiResponse:
        model = str(kwargs["model"])
        called_models.append(model)
        if len(called_models) == 1:
            raise GeminiReplayError(
                "Gemini HTTP 500: retry in 0s",
                request_was_sent=True,
            )
        return GeminiResponse(
            payload={"ok": True},
            usage={"totalTokenCount": 10},
            model=model,
        )

    replay_v4.generate_structured_decision = fake_generate  # type: ignore[assignment]
    replay_v4.time.sleep = lambda _seconds: None  # type: ignore[assignment]
    try:
        provider = replay_v4.GeminiProvider("unused", config)
        with tempfile.TemporaryDirectory() as temporary:
            for suffix in ("first", "second"):
                result = provider.decide(
                    phase="TRIGGER_WATCH",
                    request_dir=Path(temporary) / suffix,
                    prompt="test",
                    system_instruction="test",
                    images=[],
                    schema={"type": "object"},
                )
                assert result.payload == {"ok": True}
        assert called_models == ["gemini-flash", "gemini-flash", "gemini-flash"]
        assert provider.quota_disabled_models == set()
        assert provider.last_attempt_count == 1
    finally:
        replay_v4.generate_structured_decision = original_generate
        replay_v4.time.sleep = original_sleep  # type: ignore[assignment]


def test_plan_model_routing_spends_flash_only_on_owner_authority_decisions() -> None:
    family = {
        "familyId": "family-long",
        "direction": "LONG",
        "lineagePathOptions": [{"pathSelectionId": "only-path"}],
        "scenarioOptions": [{"scope": "EXTERNAL_CONTINUATION"}],
    }
    packet = {
        "focusedFamilyIds": ["family-long"],
        "physicalLineageFamilies": [family],
        "externalMapAuthority": None,
    }
    assert replay_v4.plan_requires_authority_model(packet)

    packet["externalMapAuthority"] = {
        "direction": "LONG",
        "status": "ACTIVE",
    }
    assert not replay_v4.plan_requires_authority_model(packet)

    family["lineagePathOptions"] = [
        {"pathSelectionId": "parent-path"},
        {"pathSelectionId": "terminal-child-path"},
    ]
    assert replay_v4.plan_requires_authority_model(packet)
    family["lineagePathOptions"] = [{"pathSelectionId": "only-path"}]

    family["scenarioOptions"] = [
        {"scope": "EXTERNAL_CONTINUATION"},
        {"scope": "INTERNAL_ROTATION"},
    ]
    assert replay_v4.plan_requires_authority_model(packet)
    family["scenarioOptions"] = [{"scope": "EXTERNAL_CONTINUATION"}]

    packet["physicalLineageFamilies"] = [
        {"familyId": "family-long", "direction": "SHORT"}
    ]
    assert replay_v4.plan_requires_authority_model(packet)

    packet["physicalLineageFamilies"] = [family]
    packet["externalMapAuthority"]["status"] = "BROKEN"
    assert replay_v4.plan_requires_authority_model(packet)

    config = {
        **replay_v4.DEFAULTS,
        "planModel": "gemini-flash-lite",
        "authorityPlanModel": "gemini-flash",
        "authorityPlanFallbackModel": "",
    }
    model, fallback, thinking = replay_v4.routed_gemini_settings(
        config, "PLAN", packet
    )
    assert (model, fallback, thinking) == (
        "gemini-flash", "gemini-3.5-flash-lite", "low"
    )


def test_plan_prompt_does_not_forbid_opposite_internal_rotation() -> None:
    packet = {
        "physicalLineageFamilies": [
            {
                "familyId": "short-family",
                "direction": "SHORT",
                "scenarioOptions": [
                    {
                        "scenarioSelectionId": "internal-option",
                        "scope": "INTERNAL_ROTATION",
                    }
                ],
            }
        ],
        "externalMapAuthority": {"direction": "LONG", "status": "ACTIVE"},
        "bars": {"columns": [], "data": {}},
    }
    prompt = replay_v4.prompt_for("PLAN", packet)
    system = replay_v4.system_instruction_for("PLAN", "test contract")
    required = (
        "INTERNAL_ROTATION may oppose the intact owner",
        "Never reject INTERNAL_ROTATION merely for opposing the external owner",
        "permits an opposite-direction INTERNAL_ROTATION",
    )
    assert all(text in prompt + system for text in required)
    assert "option direction and scope match the intact H1/M30 external owner" not in prompt
    assert '"scopeOwnerRule"' in prompt and '"IR"' in prompt
    schema = replay_v4.plan_schema(packet)
    decision_schema = schema["properties"]["decisions"]["items"]
    assert decision_schema["properties"]["semanticAudit"]["properties"][
        "externalOwnerAndScope"
    ]["enum"] == ["PASS", "FAIL", "UNRESOLVED"]
    packet["externalMapAuthority"] = None
    ir_only_schema = replay_v4.plan_schema(packet)
    assert ir_only_schema["properties"]["decisions"]["items"]["properties"][
        "semanticAudit"
    ]["properties"][
        "externalOwnerAndScope"
    ]["enum"] == ["PASS", "FAIL", "UNRESOLVED"]
    assert "do not shrink it to a same-direction INTERNAL_ROTATION target" in system


def test_exact_source_rejudgment_reuses_model_evidence_and_hides_prior_response() -> None:
    as_of = PLAN_AT
    request_id = "source-request-id"

    class CapturingProvider:
        def __init__(self) -> None:
            self.received: dict[str, object] = {}

        def decide(self, **kwargs: object) -> replay_v4.ProviderResult:
            self.received = kwargs
            return replay_v4.ProviderResult(
                payload={"answer": "independent"},
                usage={"totalTokenCount": 7},
                model="test-model",
                provider_calls=1,
            )

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source"
        target = root / "target"
        request_dir = source / "requests" / request_id
        request_dir.mkdir(parents=True)
        (request_dir / "prompt.txt").write_text("EXACT PROMPT", encoding="utf-8")
        (request_dir / "system_instruction.txt").write_text(
            "EXACT SYSTEM", encoding="utf-8"
        )
        (request_dir / "response_schema.json").write_text(
            json.dumps(
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["answer"],
                    "properties": {"answer": {"type": "string"}},
                }
            ),
            encoding="utf-8",
        )
        (request_dir / "request.json").write_text(
            json.dumps({"images": []}), encoding="utf-8"
        )
        (request_dir / "response.json").write_text(
            json.dumps({"payload": {"answer": "SHOULD_NOT_BE_READ"}}),
            encoding="utf-8",
        )
        ledger = HashLedger(source / "decision_ledger.jsonl")
        ledger.append(
            "PLAN_RESPONSE", as_of, "FLAT", {"requestId": request_id}
        )
        provider = CapturingProvider()
        result = replay_v4.rejudge_exact_source_request(
            source_run=source,
            run_dir=target,
            phase="PLAN",
            as_of=as_of,
            provider=provider,
        )
        assert result == 0
        assert provider.received["prompt"] == "EXACT PROMPT"
        assert provider.received["system_instruction"] == "EXACT SYSTEM"
        output = json.loads(
            (target / "summary.json").read_text(encoding="utf-8")
        )
        assert output["priorResponseHidden"] is True
        assert output["payload"] == {"answer": "independent"}


def test_plan_model_view_keeps_all_selectable_options_under_sep1_prompt_bound() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-05-01T00:00:00Z"),
        parse_utc("2025-09-06T00:00:00Z"),
        0.01,
    )
    authority = {
        "direction": "LONG",
        "establishedAtUtc": "2025-09-01T09:00:00Z",
        "sourceScenarioHash": "test-authority",
        "sourceScope": "EXTERNAL_CONTINUATION",
        "dealingRange": {
            "highBarId": "H1:1756706400",
            "lowBarId": "H1:1756695600",
            "high": 3485.77,
            "low": 3442.19,
        },
        "protectedSwing": {
            "barId": "H1:1756695600",
            "tf": "H1",
            "high": 3447.8,
            "low": 3442.19,
        },
        "objective": {
            "barId": "H1:1756706400",
            "tf": "H1",
            "side": "HIGH",
            "kind": "EXTERNAL_SWING",
            "price": 3485.77,
        },
        "status": "ACTIVE",
        "bodyBreakBarId": None,
    }
    packet = build_plan_packet(
        market,
        parse_utc("2025-09-01T12:00:00Z"),
        "GOLD",
        external_authority=authority,
    )
    model_packet = model_packet_for_phase("PLAN", packet)
    # The semantic packet must preserve every structurally valid family.  It
    # must not preserve the former arbitrary containing-candle ranges merely to
    # satisfy a historical candidate count.
    assert packet["physicalLineageFamilies"]
    assert packet["discoveryDiagnostics"]["globalCandidateCapApplied"] is False
    for full, compact in zip(
        packet["physicalLineageFamilies"],
        model_packet["physicalLineageFamilies"],
    ):
        assert "childCandidates" in full
        assert "childCandidates" not in compact
        assert "lineagePathOptions" not in compact
        assert "scenarioOptions" not in compact
        assert len(compact["lineagePathRows"]) == len(full["lineagePathOptions"])
        assert len(compact["scenarioOptionRows"]) == len(full["scenarioOptions"])
        assert {
            row[0] for row in compact["scenarioOptionRows"]
        } == {
            option["scenarioSelectionId"] for option in full["scenarioOptions"]
        }
    page_family_ids: list[str] = []
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config={**replay_v4.DEFAULTS, "symbol": "GOLD"},
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=new_runtime(0),
        )
        for family in packet["physicalLineageFamilies"]:
            page = runner.compact_plan_page(packet, [family], parse_utc("2025-09-01T12:00:00Z"))
            assert len(prompt_for("PLAN", page).encode("utf-8")) <= 64000
            assert page["roleEvidenceAudit"]["missingRoleIds"] == []
            page_family_ids.append(str(family["familyId"]))
    assert page_family_ids == [
        str(item["familyId"]) for item in packet["physicalLineageFamilies"]
    ]


def test_sep4_later_causal_source_upgrade_is_found_and_touched_without_api() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-05-01T00:00:00Z"),
        parse_utc("2025-09-06T00:00:00Z"),
        0.01,
    )
    scenario = {
        "scenarioHash": "sep4-source-upgrade-regression",
        "frozenAtUtc": "2025-09-04T07:00:00Z",
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "dealingRange": {
            "highBarId": "H1:1756954800", "lowBarId": "H1:1756965600",
            "high": 3562.48, "low": 3510.52, "eq": 3536.5,
        },
        "objective": {
            "barId": "H1:1756965600", "tf": "H1", "side": "LOW",
            "kind": "EXTERNAL_SWING", "price": 3510.52,
        },
        "mapProtectedSwing": {
            "barId": "H1:1756954800", "tf": "H1", "high": 3562.48, "low": 3551.68,
        },
        "root": {"obBarId": "H1:1756954800", "low": 3551.68, "high": 3562.48},
        "finalChild": {"obBarId": "M15:1756957500", "distal": 3562.48},
        "childTouchAtUtc": "2025-09-04T16:38:00Z",
        "childTouchBarId": "M1:1757003820",
    }
    candidates = discover_source_upgrade_candidates(
        market, scenario, parse_utc("2025-09-04T18:00:00Z"), "GOLD"
    )
    raw_roots = mechanical_root_candidates(
        market, parse_utc("2025-09-04T18:00:00Z"), maximum=None
    )
    assert any(
        item["rootBarId"] == "M15:1757002500"
        and item["direction"] == "SHORT"
        for item in raw_roots
    )
    # A later source upgrade is optional in Ground Truth V2. It must never be
    # invented when the full causal child path is absent from the as-of packet.
    assert candidates == []


def test_first_m1_after_market_gap_refreshes_closed_h1_map() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-08-25T00:00:00Z"),
        parse_utc("2025-09-03T03:00:00Z"),
        0.01,
    )
    start = parse_utc("2025-09-02T23:00:00Z")
    end = parse_utc("2025-09-03T02:30:00Z")
    runtime = new_runtime(market.m1_index_at_or_after(start))
    calls: list[int] = []
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config={
                **replay_v4.DEFAULTS,
                "symbol": "GOLD",
                "brokerStopsLevelPrice": 0.0,
                "point": 0.01,
                "planOnFamilyFormation": False,
            },
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=runtime,
        )

        def record_schedule(
            row: dict, *, api_allowed: bool = True, approach_events=None
        ) -> bool:
            as_of = int(row["available"])
            latest = runner.latest_h1_available(as_of)
            if latest != runner.runtime.get("lastPlanH1Available"):
                calls.append(as_of)
                runner.runtime["lastPlanH1Available"] = latest
            return False

        runner.schedule_event_driven_flat_plan = record_schedule  # type: ignore[method-assign]
        assert runner.run(start, end, end) == "COMPLETED"
        assert calls[0] == start + 60
        assert parse_utc("2025-09-03T01:01:00Z") in calls
        assert runner.latest_h1_available(
            parse_utc("2025-09-03T01:01:00Z")
        ) == parse_utc("2025-09-03T00:00:00Z")

def test_no_future_bar_can_be_resolved() -> None:
    market = synthetic_market()
    future_id = f"H1:{BASE + 3600}"
    try:
        market.bar(future_id, PLAN_AT)
    except V4ContractError as exc:
        assert "future" in str(exc)
    else:
        raise AssertionError("future H1 bar leaked into PLAN")


def test_preexisting_objective_and_fresh_child_regression() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-10-01T00:00:00Z"),
        parse_utc("2025-11-02T00:00:00Z"),
        0.01,
    )
    as_of = parse_utc("2025-10-31T16:00:00Z")
    packet = build_plan_packet(market, as_of, "GOLD")
    raw_roots = mechanical_root_candidates(market, as_of, maximum=None)
    assert any(
        item["rootBarId"] == "M15:1761922800" for item in raw_roots
    )
    assert not any(
        item["rootBarId"] == "M15:1761922800"
        for item in packet["physicalLineageFamilies"]
    ), "an unconfirmed HTF source swing was promoted into a tradable range"


def test_plan_freshness_and_schema_share_the_same_m1_clock() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    as_of = parse_utc("2025-09-03T01:01:00Z")
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-08-01T00:00:00Z"),
        parse_utc("2025-09-04T00:00:00Z"),
        0.01,
    )
    packet = build_plan_packet(market, as_of, "GOLD")
    family = next(
        item for item in packet["physicalLineageFamilies"]
        if item["rootBarId"] == "H1:1756825200"
    )
    child_ids = {
        item["rootBarId"] for item in family["childCandidates"]
    }
    assert {"M15:1756831500", "M5:1756831800"} <= child_ids
    assert all(
        market.bar(bar_id, as_of)["available"] <= as_of
        for bar_id in child_ids
    )

    focused = build_plan_packet(
        market, as_of, "GOLD", {str(family["familyId"])}
    )
    scenario_enum = plan_schema(focused)["properties"]["decisions"]["items"][
        "properties"
    ]["scenarioSelectionId"]["anyOf"][0]["enum"]
    matching_family = focused["physicalLineageFamilies"][0]
    assert scenario_enum == [
        option["scenarioSelectionId"]
        for option in matching_family["scenarioOptions"]
    ]
    selected_path_ids = {
        option["lineagePathSelectionId"]
        for option in matching_family["scenarioOptions"]
        if option["scenarioSelectionId"] in scenario_enum
    }
    selected_ob_ids = {
        node["obBarId"]
        for item in focused["physicalLineageFamilies"]
        for option in item["lineagePathOptions"]
        if option["pathSelectionId"] in selected_path_ids
        for node in option["refinements"]
    }
    assert "M30:1756827000" in selected_ob_ids
    assert "M15:1756831500" in selected_ob_ids
    assert "M5:1756831800" in selected_ob_ids
    assert any(
        [node["obBarId"] for node in option["refinements"]]
        == ["M15:1756831500", "M5:1756831800"]
        for option in matching_family["lineagePathOptions"]
    )
    assert not any(
        [node["obBarId"] for node in option["refinements"]]
        == ["M15:1756831500"]
        for option in matching_family["lineagePathOptions"]
    )
    bad_mixed_tuple = {
        "obBarId": "M5:1756831800",
        "displacementBarId": "M5:1756832400",
        "protectedSwingBarId": "M5:1756848900",
    }
    assert not any(
        all(option[key] == value for key, value in bad_mixed_tuple.items())
        for item in focused["physicalLineageFamilies"]
        for child in item["childCandidates"]
        for option in child["selectionOptions"]
    )


def test_m15_pivot_cannot_be_promoted_to_external_objective() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    as_of = parse_utc("2025-09-03T04:01:00Z")
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-08-01T00:00:00Z"),
        parse_utc("2025-09-04T00:00:00Z"),
        0.01,
    )
    payload = {
        "schemaVersion": "4.7.0",
        "action": "PLAN",
        "direction": "LONG",
        "scope": "EXTERNAL_CONTINUATION",
        "dealingRange": {
            "highBarId": "H1:1756868400",
            "lowBarId": "H1:1756861200",
        },
        "objective": {
            "barId": "M15:1756869300",
            "side": "HIGH",
            "kind": "EXTERNAL_SWING",
        },
        "mapProtectedSwingBarId": "H1:1756861200",
        "ownerBreakTargetBarId": None,
        "ownerBreakBarId": None,
        "root": {
            "obBarId": "H1:1756861200",
            "displacementBarId": "H1:1756868400",
            "protectedSwingBarId": "H1:1756839600",
        },
        "refinements": [
            {
                "obBarId": "M30:1756864800",
                "displacementBarId": "M30:1756868400",
                "protectedSwingBarId": "M30:1756855800",
            }
        ],
        "intermediateLiquidityBarIds": [],
        "reason": "Regression fixture for a wrongly promoted M15 pivot.",
    }
    try:
        freeze_plan(payload, market, as_of, set())
    except V4ContractError as exc:
        assert "must originate from H1 or M30" in str(exc)
    else:
        raise AssertionError("M15 pivot was promoted to external objective")


def test_external_scenario_options_keep_nearest_and_expose_h1_alternative() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    as_of = parse_utc("2025-09-03T09:01:00Z")
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-08-01T00:00:00Z"),
        parse_utc("2025-09-04T00:00:00Z"),
        0.01,
    )
    packet = build_plan_packet(market, as_of, "GOLD")
    family = next(
        item for item in packet["physicalLineageFamilies"]
        if item["rootBarId"] == "H1:1756825200"
    )
    external_options = [
        option for option in family["scenarioOptions"]
        if option["scope"] == "EXTERNAL_CONTINUATION"
    ]
    assert external_options
    objective_ids = {
        member["barId"]
        for option in external_options
        for member in option["objectiveFamily"]["orderedMembers"]
    }
    # The nearest M30 pool must remain visible, but it is no longer the only
    # answer: H1 context can justify a farther still-live destination.
    assert "M30:1756884600" in objective_ids
    assert "H1:1756868400" in objective_ids
    assert all(
        option["objective"]["barId"] not in option["intermediateLiquidityBarIds"]
        for option in external_options
    )


def test_persistent_external_owner_survives_trade_and_blocks_opposite_continuation() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-08-01T00:00:00Z"),
        parse_utc("2025-09-04T00:00:00Z"),
        0.01,
    )
    authority = {
        "direction": "LONG",
        "establishedAtUtc": "2025-09-03T01:01:00Z",
        "sourceScenarioHash": "first-long",
        "sourceScope": "EXTERNAL_CONTINUATION",
        "dealingRange": {
            "highBarId": "H1:1756850400",
            "lowBarId": "H1:1756846800",
            "high": 3539.90,
            "low": 3525.08,
        },
        "protectedSwing": {
            "barId": "H1:1756846800",
            "tf": "H1",
            "high": 3531.89,
            "low": 3525.08,
        },
        "objective": {
            "barId": "M30:1756852200",
            "tf": "M30",
            "side": "HIGH",
            "kind": "EXTERNAL_SWING",
            "price": 3539.90,
        },
        "status": "ACTIVE",
        "bodyBreakBarId": None,
    }
    packet_0401 = build_plan_packet(
        market,
        parse_utc("2025-09-03T04:01:00Z"),
        "GOLD",
        external_authority=authority,
    )
    continuation = [
        option
        for family in packet_0401["physicalLineageFamilies"]
        for option in family["scenarioOptions"]
        if option["scope"] == "EXTERNAL_CONTINUATION"
    ]
    assert continuation == []

    packet_0601 = build_plan_packet(
        market,
        parse_utc("2025-09-03T06:01:00Z"),
        "GOLD",
        external_authority=authority,
    )
    mature_continuation = [
        option
        for family in packet_0601["physicalLineageFamilies"]
        for option in family["scenarioOptions"]
        if option["scope"] == "EXTERNAL_CONTINUATION"
    ]
    assert mature_continuation
    assert {item["objective"]["barId"] for item in mature_continuation} == {
        "H1:1756868400"
    }
    assert {
        item["objective"]["matureAtUtc"] for item in mature_continuation
    } == {"2025-09-03T06:00:00Z"}

    corrected_second = {
        "scenarioHash": "second-long",
        "frozenAtUtc": "2025-09-03T06:01:00Z",
        "direction": "LONG",
        "scope": "EXTERNAL_CONTINUATION",
        "dealingRange": {
            "highBarId": "H1:1756868400",
            "lowBarId": "H1:1756861200",
            "high": 3546.72,
            "low": 3528.69,
        },
        "mapProtectedSwing": {
            "barId": "H1:1756861200",
            "tf": "H1",
            "high": 3534.87,
            "low": 3528.69,
        },
        "objective": {
            "barId": "H1:1756868400",
            "tf": "H1",
            "side": "HIGH",
            "kind": "EXTERNAL_SWING",
            "price": 3546.72,
        },
    }
    resolved_authority = resolved_external_authority(
        market, authority, parse_utc("2025-09-03T04:01:00Z")
    )
    assert resolved_authority
    assert resolved_authority["status"] == "OBJECTIVE_REACHED"
    updated = external_authority_from_scenario(
        corrected_second, resolved_authority
    )
    assert updated
    runtime = new_runtime(0)
    runtime["externalMapAuthority"] = updated
    terminal = reset_terminal(runtime, "CLOSED")
    assert terminal["externalMapAuthority"] == updated

    packet_0901 = build_plan_packet(
        market,
        parse_utc("2025-09-03T09:01:00Z"),
        "GOLD",
        external_authority=terminal["externalMapAuthority"],
    )
    opposite_external = [
        option
        for family in packet_0901["physicalLineageFamilies"]
        for option in family["scenarioOptions"]
        if option["direction"] == "SHORT"
        and option["scope"] in {"EXTERNAL_CONTINUATION", "EXTERNAL_REVERSAL"}
    ]
    assert opposite_external == []
    assert all(
        family["rootBarId"] != "H1:1756882800"
        for family in packet_0901["physicalLineageFamilies"]
    )

    packet_1000 = build_plan_packet(
        market,
        parse_utc("2025-09-03T10:00:00Z"),
        "GOLD",
        external_authority=terminal["externalMapAuthority"],
    )
    continued_objectives = {
        member["barId"]
        for family in packet_1000["physicalLineageFamilies"]
        for option in family["scenarioOptions"]
        if option["direction"] == "LONG"
        and option["scope"] == "EXTERNAL_CONTINUATION"
        for member in option["objectiveFamily"]["orderedMembers"]
    }
    assert {
        "H1:1756868400",
        "M30:1756884600",
    }.issubset(continued_objectives)


def test_active_owner_exposes_newly_mature_nearer_h1_objective_for_new_scenario() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2026-01-01_2026-08-12.npz"
    as_of = parse_utc("2026-06-03T15:00:00Z")
    market = MarketData.from_npz(
        dataset,
        parse_utc("2026-01-01T00:00:00Z"),
        parse_utc("2026-06-04T00:00:00Z"),
        0.01,
    )
    authority = {
        "direction": "SHORT",
        "establishedAtUtc": "2026-06-03T08:30:00Z",
        "sourceScenarioHash": "older-short",
        "sourceScope": "EXTERNAL_CONTINUATION",
        "dealingRange": {
            "highBarId": "M30:1780425000",
            "lowBarId": "M30:1779980400",
            "high": 4508.33,
            "low": 4379.44,
        },
        "protectedSwing": {
            "barId": "M30:1780425000",
            "tf": "M30",
            "high": 4508.33,
            "low": 4499.99,
        },
        "objective": {
            "barId": "M30:1779980400",
            "tf": "M30",
            "side": "LOW",
            "kind": "EXTERNAL_SWING",
            "price": 4379.44,
        },
        "status": "ACTIVE",
        "bodyBreakBarId": None,
        "objectiveReachedBarId": None,
        "objectiveReachedAtUtc": None,
        "resolvedAtUtc": None,
    }
    packet = build_plan_packet(
        market, as_of, "GOLD", external_authority=authority
    )
    selected = None
    for family in packet["physicalLineageFamilies"]:
        if family["rootBarId"] != "H1:1780466400":
            continue
        paths = {
            item["pathSelectionId"]: item
            for item in family["lineagePathOptions"]
        }
        for option in family["scenarioOptions"]:
            path = paths[option["lineagePathSelectionId"]]
            if (
                option["scope"] == "EXTERNAL_CONTINUATION"
                and option["objective"]["barId"] == "H1:1780488000"
                and path["refinements"][-1]["obBarId"] == "M30:1780468200"
            ):
                selected = option
                break
    assert selected is not None
    assert market.bar(selected["objective"]["barId"], as_of)["low"] == 4438.81
    assert selected["objective"]["matureAtUtc"] == "2026-06-03T15:00:00Z"

    scenario = freeze_plan(
        {
            "schemaVersion": "4.10.0",
            "action": "PLAN",
            "scenarioSelectionId": selected["scenarioSelectionId"],
            "reason": "June truth objective promotion regression",
        },
        market,
        as_of,
        None,
        packet,
    )
    assert scenario is not None
    assert scenario["root"]["obBarId"] == "H1:1780466400"
    assert scenario["finalChild"]["obBarId"] == "M30:1780468200"
    assert scenario["objective"]["barId"] == "H1:1780488000"

    advanced = external_authority_from_scenario(scenario, authority)
    assert advanced is not None
    assert advanced["objective"]["barId"] == "H1:1780488000"
    assert authority["objective"]["barId"] == "M30:1779980400"
    exposed_prices = {
        float(
            market.bar(option["objective"]["barId"], as_of)[
                "high" if option["objective"]["side"] == "HIGH" else "low"
            ]
        )
        for family in packet["physicalLineageFamilies"]
        for option in family["scenarioOptions"]
        if option["scope"] == "EXTERNAL_CONTINUATION"
    }
    assert not any(price < 4379.44 for price in exposed_prices)


def test_active_external_authority_cannot_be_redefined_by_new_internal_delivery() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-05-01T00:00:00Z"),
        parse_utc("2025-09-06T00:00:00Z"),
        0.01,
    )
    authority = {
        "direction": "LONG",
        "establishedAtUtc": "2025-09-02T06:00:00Z",
        "sourceScenarioHash": "sep2-authority",
        "sourceScope": "EXTERNAL_CONTINUATION",
        "dealingRange": {
            "highBarId": "H1:1756785600",
            "lowBarId": "H1:1756774800",
            "high": 3508.51,
            "low": 3474.13,
        },
        "protectedSwing": {
            "barId": "H1:1756774800",
            "tf": "H1",
            "high": 3479.64,
            "low": 3474.13,
        },
        "objective": {
            "barId": "H1:1756785600",
            "tf": "H1",
            "side": "HIGH",
            "kind": "EXTERNAL_SWING",
            "price": 3508.51,
        },
        "status": "ACTIVE",
        "bodyBreakBarId": None,
    }
    packet = build_plan_packet(
        market,
        parse_utc("2025-09-02T14:00:00Z"),
        "GOLD",
        external_authority=authority,
    )
    assert packet["externalMapAuthority"]["status"] == "ACTIVE"
    options = [
        option
        for family in packet["physicalLineageFamilies"]
        for option in family["scenarioOptions"]
    ]
    assert options
    assert all(
        option["dealingRange"] == {
            "highBarId": "H1:1756785600",
            "lowBarId": "H1:1756774800",
        }
        for option in options
    )
    assert all(
        option["mapProtectedSwingBarId"] == "H1:1756774800"
        for option in options
    )
    continuations = [
        option for option in options
        if option["scope"] == "EXTERNAL_CONTINUATION"
    ]
    assert continuations
    continuation_objectives = {
        member["barId"]
        for option in continuations
        for member in option["objectiveFamily"]["orderedMembers"]
    }
    assert {
        "H1:1756785600",
        "M30:1756798200",
    }.issubset(continuation_objectives)
    assert all(
        option["dealingRange"] != {
            "highBarId": "H1:1756796400",
            "lowBarId": "H1:1756814400",
        }
        for option in options
    )


def test_newer_causal_delivery_dominates_an_older_source_for_the_same_objective() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2025-05-01T00:00:00Z"),
        parse_utc("2025-09-06T00:00:00Z"),
        0.01,
    )
    authority = {
        "direction": "LONG",
        "establishedAtUtc": "2025-09-02T06:00:00Z",
        "sourceScenarioHash": "sep2-authority",
        "sourceScope": "EXTERNAL_CONTINUATION",
        "dealingRange": {
            "highBarId": "H1:1756785600",
            "lowBarId": "H1:1756774800",
            "high": 3508.51,
            "low": 3474.13,
        },
        "protectedSwing": {
            "barId": "H1:1756774800",
            "tf": "H1",
            "high": 3479.64,
            "low": 3474.13,
        },
        "objective": {
            "barId": "H1:1756785600",
            "tf": "H1",
            "side": "HIGH",
            "kind": "EXTERNAL_SWING",
            "price": 3508.51,
        },
        "status": "ACTIVE",
        "bodyBreakBarId": None,
    }
    packet = build_plan_packet(
        market,
        parse_utc("2025-09-03T01:01:00Z"),
        "GOLD",
        external_authority=authority,
    )
    assert packet["externalMapAuthority"]["status"] == "OBJECTIVE_REACHED"
    assert (
        packet["externalMapAuthority"]["objectiveReachedAtUtc"]
        == "2025-09-02T17:45:00Z"
    )
    assert all(
        option["scope"] in {"EXTERNAL_CONTINUATION", "INTERNAL_ROTATION"}
        for family in packet["physicalLineageFamilies"]
        for option in family["scenarioOptions"]
    )
    for family in packet["physicalLineageFamilies"]:
        for option in family["scenarioOptions"]:
            if option["scope"] != "INTERNAL_ROTATION":
                continue
            selected_range = next(
                item for item in family["dealingRangePairCandidates"]
                if item["highBarId"] == option["dealingRange"]["highBarId"]
                and item["lowBarId"] == option["dealingRange"]["lowBarId"]
            )
            objective = next(
                item for item in family["unconsumedDirectionalLiquidityCandidates"]
                if item["barId"] == option["objective"]["barId"]
            )
            assert float(selected_range["low"]) <= float(objective["price"]) <= float(
                selected_range["high"]
            )
    roots = {
        family["rootBarId"] for family in packet["physicalLineageFamilies"]
        if any(
            option["scope"] == "EXTERNAL_CONTINUATION"
            for option in family["scenarioOptions"]
        )
    }
    # A newer-looking OB cannot supersede an older valid source unless the new
    # episode has its own confirmed H1/M30 source swing and causal range.
    assert "H1:1756825200" in roots
    assert "H1:1756846800" not in roots


def test_one_excursion_exposes_only_outermost_mature_liquidity() -> None:
    events = [
        {
            "liquidityBarId": "M1:1756866600",
            "side": "SSL",
            "level": 3527.12,
            "excursionBarId": "M1:1756867440",
            "recoveryBarId": "M1:1756867500",
        },
        {
            "liquidityBarId": "M1:1756867140",
            "side": "SSL",
            "level": 3526.06,
            "excursionBarId": "M1:1756867440",
            "recoveryBarId": "M1:1756867500",
        },
    ]
    assert [
        item["liquidityBarId"] for item in outermost_completed_sweep_events(events)
    ] == ["M1:1756867140"]


def test_causal_parity_accepts_only_nested_root_with_same_execution_lineage() -> None:
    expected = {
        "scope": "EXTERNAL_CONTINUATION",
        "execution_model": "DELIVERY_FVG_REPLACEMENT",
        "root_ob_bar_id": "M15:1756849500",
        "child_ob_bar_id": "M5:1756849800",
        "objective_bar_id": "M30:1756852200",
    }
    actual = {
        **expected,
        "root_ob_bar_id": "H1:1756846800",
        "objective_bar_id": "H1:1756850400",
    }
    assert replay_v4._bar_contains(actual["root_ob_bar_id"], expected["root_ob_bar_id"])
    assert replay_v4._bar_contains(actual["objective_bar_id"], expected["objective_bar_id"])
    assert replay_v4._causal_trade_identity(expected, actual)

    unrelated = {**actual, "root_ob_bar_id": "H1:1756850400"}
    assert not replay_v4._causal_trade_identity(expected, unrelated)

    wrong_child = {**actual, "child_ob_bar_id": "M5:1756850100"}
    assert not replay_v4._causal_trade_identity(expected, wrong_child)


def test_funnel_comparison_attributes_the_complete_chain() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    watch = freeze_trigger_watch(valid_trigger_payload(market), market, TOUCH_TIME, scenario)
    assert watch
    touch_index = market.m1_index_at_or_after(TOUCH_TIME - 60)
    order = None
    for index in range(touch_index, touch_index + 4):
        watch, order = advance_trigger_watch(market, scenario, watch, market.m1_row(index), 0.0)
    assert order
    evidence = {
        "matureLiquidityBarId": watch["matureLiquidity"]["barId"],
        "m5CorrectionSwingBarId": watch["m5CorrectionSwing"]["barId"],
        "chochReferenceBarId": watch["chochReference"]["barId"],
        "triggerProtectedSwingBarId": watch["triggerProtectedSwing"]["barId"],
        "sweepBarId": watch["sweep"]["barId"],
        "chochBreakBarId": watch["chochBreak"]["barId"],
        "executionBarId": watch["executionOb"]["barId"],
    }
    truth = {
        "executableBenchmarks": [
            {
                "tradeId": "SYNTH-1",
                "map": {
                    "direction": scenario["direction"],
                    "scope": scenario["scope"],
                    "root": {"barId": scenario["refinements"][0]["obBarId"]},
                    "objective": {"barId": scenario["objective"]["barId"]},
                },
                "refinement": {
                    "path": [
                        {"barId": item["obBarId"]}
                        for item in scenario["refinements"][1:]
                    ]
                },
                "triggerAudit": evidence,
                "order": {
                    "filledAtUtc": utc_text(market.m1_row(touch_index + 3)["available"]),
                    "entry": order["entry"],
                },
            }
        ]
    }
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        ledger = HashLedger(root / "decision_ledger.jsonl")
        ledger.append("SCENARIO_PLANNED", PLAN_AT, "PLANNED", {"scenario": scenario})
        ledger.append(
            "TRIGGER_WATCH_ARMED",
            TOUCH_TIME,
            "TRIGGER_WATCH",
            {"scenarioHash": scenario["scenarioHash"], "watch": watch},
        )
        ledger.append(
            "ORDER_CREATED",
            market.m1_row(touch_index + 3)["available"],
            "PENDING",
            {"order": order, "triggerEvidence": evidence},
        )
        canceled_order = {
            **order,
            "orderId": "canceled-order",
            "scenarioHash": "canceled-scenario",
        }
        ledger.append(
            "ORDER_CREATED",
            market.m1_row(touch_index + 3)["available"],
            "PENDING",
            {"order": canceled_order, "triggerEvidence": evidence},
        )
        ledger.append(
            "TRADE_CLOSED",
            market.m1_row(touch_index + 3)["available"],
            "CLOSED",
            {
                "trade": {
                    "tradeId": "SYNTH-1-CANDIDATE",
                    "scenarioHash": scenario["scenarioHash"],
                    "direction": scenario["direction"],
                    "entry": order["entry"],
                    "entryAtUtc": utc_text(market.m1_row(touch_index + 3)["available"]),
                }
            },
        )
        truth_path = root / "truth.json"
        truth_path.write_text(json.dumps(truth), encoding="utf-8")
        output = root / "parity.csv"
        result = compare_funnel(
            argparse.Namespace(
                truth=truth_path,
                ledger=root / "decision_ledger.jsonl",
                output=output,
                write_sol_gate=False,
            )
        )
        assert result == 0
        assert "CAUSAL_MATCH" in output.read_text(encoding="utf-8-sig")
        assert "EXTRA" not in output.read_text(encoding="utf-8-sig")


def test_v450_june_authority_remaps_without_candidate_cap_or_deadlock() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2026-01-01_2026-08-12.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2026-05-01T00:00:00Z"),
        parse_utc("2026-07-02T00:00:00Z"),
        0.01,
    )
    authority = {
        "direction": "SHORT",
        "status": "ACTIVE",
        "establishedAtUtc": "2026-06-15T21:00:00Z",
        "dealingRange": {
            "highBarId": "H1:1781542800",
            "lowBarId": "H1:1781514000",
            "high": 4369.14,
            "low": 4300.71,
        },
        "protectedSwing": {
            "barId": "H1:1781542800",
            "high": 4369.14,
            "low": 4353.67,
        },
        "objective": {
            "barId": "H1:1781514000",
            "side": "LOW",
            "price": 4300.71,
        },
        "bodyBreakBarId": None,
        "objectiveReachedBarId": None,
    }
    first = resolved_external_authority(
        market, authority, parse_utc("2026-06-23T12:00:00Z")
    )
    assert first is not None
    assert first["status"] == "REMAP_REQUIRED"
    assert first["historicalResolution"] == "RESOLVED_BROKEN"
    assert first["bodyBreakBarId"] == "H1:1781726400"

    family_counts = []
    for moment in (
        "2026-06-23T12:00:00Z",
        "2026-06-24T12:00:00Z",
        "2026-06-30T12:00:00Z",
    ):
        packet = build_plan_packet(
            market, parse_utc(moment), "GOLD", external_authority=authority
        )
        diagnostics = packet["discoveryDiagnostics"]
        assert diagnostics["globalCandidateCapApplied"] is False
        assert diagnostics["rootCandidatesByTf"]["H1"] > 10
        assert diagnostics["rootCandidatesByTf"]["M30"] > 10
        family_counts.append(diagnostics["physicalFamilies"])
        assert all(
            option["scope"] != "INTERNAL_ROTATION"
            for family in packet["physicalLineageFamilies"]
            for option in family["scenarioOptions"]
        )
    # REMAP_REQUIRED exposes both directions immediately and the permanent
    # event ledger retains already-knowable families at every checkpoint.
    assert all(count > 0 for count in family_counts)

    before = discovery_event_fingerprint(
        market, parse_utc("2026-06-24T12:00:00Z"), authority
    )
    ordinary_m5 = discovery_event_fingerprint(
        market, parse_utc("2026-06-24T12:05:00Z"), authority
    )
    assert before == ordinary_m5


def test_v450_internal_rotation_objective_must_stay_inside_range() -> None:
    market = synthetic_market()
    payload = valid_plan_payload()
    payload["scope"] = "INTERNAL_ROTATION"
    payload["dealingRange"] = {"highIndex": 3, "lowIndex": 2}
    payload["objective"]["kind"] = "INTERNAL_SWING"
    try:
        freeze_plan(payload, market, PLAN_AT, set())
    except V4ContractError as exc:
        assert "inside its selected dealing range" in str(exc)
    else:
        raise AssertionError("range-external INTERNAL_ROTATION objective was accepted")


def test_v450_external_continuation_records_every_internal_delivery() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2026-01-01_2026-08-12.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2026-05-01T00:00:00Z"),
        parse_utc("2026-07-02T00:00:00Z"),
        0.01,
    )
    as_of = parse_utc("2026-06-24T12:00:00Z")
    packet = build_plan_packet(market, as_of, "GOLD")
    checked = 0
    for family in packet["physicalLineageFamilies"]:
        paths = {
            item["pathSelectionId"]: item
            for item in family["lineagePathOptions"]
        }
        internal = [
            item for item in family["unconsumedDirectionalLiquidityCandidates"]
            if item["barId"].startswith(("M15:", "M5:"))
        ]
        for option in family["scenarioOptions"]:
            if option["scope"] != "EXTERNAL_CONTINUATION":
                continue
            path = paths[option["lineagePathSelectionId"]]
            child = market.bar(path["refinements"][-1]["obBarId"], as_of)
            proximal = (
                child["high"] if option["direction"] == "LONG" else child["low"]
            )
            target = market.bar(option["objective"]["barId"], as_of)
            target_price = (
                target["high"] if option["objective"]["side"] == "HIGH" else target["low"]
            )
            expected = {
                item["barId"] for item in internal
                if (
                    proximal < float(item["price"]) < target_price
                    if option["direction"] == "LONG"
                    else target_price < float(item["price"]) < proximal
                )
            }
            assert set(option["intermediateLiquidityBarIds"]) == expected
            checked += 1
    assert checked > 0


def test_v450_rejects_m5_trigger_from_before_child_touch_episode() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    payload = valid_trigger_payload(market)
    old_correction = {"barId": payload["selectedBarIds"][1]}
    try:
        freeze_trigger_watch(
            payload,
            market,
            TOUCH_TIME,
            scenario,
            correction_candidates=[old_correction],
        )
    except V4ContractError as exc:
        assert "predates the active child-touch reaction episode" in str(exc)
    else:
        raise AssertionError("pre-touch M5 correction swing was reused")


def test_v452_delivery_replacement_creates_one_first_retest_order() -> None:
    market = synthetic_market()
    formed = market.m1_row(market.m1_index_at_or_after(TOUCH_TIME - 60) + 3)
    candidate = {
        "shadowId": "shadow-test",
        "scenarioHash": "scenario-test",
        "status": "WAIT_FIRST_RETEST",
        "direction": "LONG",
        "formedAtUtc": utc_text(formed["available"]),
        "formedBarId": formed["barId"],
        "fvg": {"low": 100.0, "high": 101.0},
        "causalObBarId": formed["barId"],
        "transferSwingBarId": formed["barId"],
        "protectedSwingBarId": formed["barId"],
        "originalChildObBarId": "M5:test",
        "entry": 101.0,
        "stop": 99.0,
        "target": 120.0,
        "risk": 2.0,
        "spreadAtFormation": 0.02,
        "buffer": 0.02,
    }
    retest = {
        **market.m1_row(formed["index"] + 1),
        "low": 100.5,
        "high": 102.0,
        "spreadPoints": 2,
    }
    candidate, event_name = advance_shadow_delivery_candidate(
        market, candidate, retest
    )
    assert event_name == "FILLED" and candidate["status"] == "FILLED"

    scenario = frozen_scenario(market)
    candidate["scenarioHash"] = scenario["scenarioHash"]
    candidate["originalChildObBarId"] = scenario["finalChild"]["obBarId"]
    candidate["causalObBarId"] = formed["barId"]
    candidate["protectedSwingBarId"] = formed["barId"]
    candidate["transferSwingBarId"] = formed["barId"]
    order, watch = delivery_candidate_order(market, scenario, candidate)
    assert order["model"] == "DELIVERY_FVG_REPLACEMENT"
    assert order["originalOrderId"] is not None
    assert watch["triggerProtectedSwing"]["barId"] == formed["barId"]
    invalidating = {
        **market.m1_row(formed["index"] + 1),
        "close": 99.9, "low": 99.8, "high": 101.2,
    }
    outcome, position = advance_pending(market, order, invalidating)
    assert outcome == "FILLED" and position is not None


def test_v462_delivery_fvg_accepts_m5_or_completed_m1_transfer() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2026-01-01_2026-08-12.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2026-05-01T00:00:00Z"),
        parse_utc("2026-06-09T00:00:00Z"),
        0.01,
    )
    child = market.bar("M5:1780085700", parse_utc("2026-06-01T01:01:00Z"))
    scenario = {
        "scenarioHash": "june-w01-initial-short",
        "frozenAtUtc": "2026-06-01T01:01:00Z",
        "childTouchAtUtc": None,
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "dealingRange": {"low": 4512.58, "high": 4595.04},
        "objective": {
            "barId": "H1:1780066800", "side": "LOW",
            "kind": "EXTERNAL_SWING", "price": 4512.58,
        },
        "root": {"proximal": 4557.61},
        "finalChild": {
            "obBarId": child["barId"],
            "distal": float(child["high"]),
        },
    }

    micro_only = market.m1_row(
        market.m1_index_at_or_after(parse_utc("2026-06-01T01:40:00Z") - 60)
    )
    candidate = detect_pre_touch_delivery_candidate(
        market, scenario, micro_only, 0.0
    )
    # The old FVG-distal stop made this micro transfer look executable. With
    # the AGENTS structural stop, its nearby objective is below 1R and the
    # engine must reject it before an order can exist.
    assert candidate is None

    meaningful = market.m1_row(
        market.m1_index_at_or_after(parse_utc("2026-06-01T06:11:00Z") - 60)
    )
    candidate = detect_pre_touch_delivery_candidate(
        market, scenario, meaningful, 0.0
    )
    assert candidate is None

    morning_child = market.bar(
        "M5:1780286100", parse_utc("2026-06-01T06:46:00Z")
    )
    morning = {
        "scenarioHash": "june-w01-morning-short",
        "frozenAtUtc": "2026-06-01T06:46:00Z",
        "childTouchAtUtc": None,
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "dealingRange": {"low": 4502.51, "high": 4545.69},
        "objective": {
            "barId": "H1:1780041600", "side": "LOW",
            "kind": "EXTERNAL_SWING", "price": 4502.51,
        },
        "root": {"proximal": 4535.15},
        "finalChild": {
            "obBarId": morning_child["barId"],
            "distal": float(morning_child["high"]),
        },
    }
    before_governing_low = market.m1_row(
        market.m1_index_at_or_after(parse_utc("2026-06-01T07:46:00Z") - 60)
    )
    candidate = detect_pre_touch_delivery_candidate(
        market, morning, before_governing_low, 0.0
    )
    assert candidate is None

    after_governing_low = market.m1_row(
        market.m1_index_at_or_after(parse_utc("2026-06-01T07:48:00Z") - 60)
    )
    candidate = detect_pre_touch_delivery_candidate(
        market, morning, after_governing_low, 0.0
    )
    assert candidate is None

    afternoon_child = market.bar(
        "M15:1780301700", parse_utc("2026-06-01T14:00:00Z")
    )
    afternoon = {
        "scenarioHash": "june-w01-afternoon-short",
        "frozenAtUtc": "2026-06-01T14:00:00Z",
        "childTouchAtUtc": None,
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "dealingRange": {"low": 4489.0, "high": 4525.04},
        "objective": {
            "barId": "H1:1780315200", "side": "LOW",
            "kind": "EXTERNAL_SWING", "price": 4489.0,
        },
        "root": {"proximal": 4512.56},
        "finalChild": {
            "obBarId": afternoon_child["barId"],
            "distal": float(afternoon_child["high"]),
        },
    }
    root_reconfirmed = market.m1_row(
        market.m1_index_at_or_after(parse_utc("2026-06-01T14:34:00Z") - 60)
    )
    candidate = detect_pre_touch_delivery_candidate(
        market, afternoon, root_reconfirmed, 0.0
    )
    assert candidate is not None
    assert candidate["formedBarId"] == "M1:1780324380"
    assert candidate["deliveryConfirmation"] == {
        "mode": "FROZEN_ROOT_PROXIMAL_REJECTION",
        "barId": "M1:1780323780",
        "level": 4512.56,
    }
    assert candidate["entry"] == 4507.62
    assert candidate["stop"] == 4523.95
    assert candidate["target"] == 4489.0
    assert candidate["stopBasis"] == {
        "model": "DELIVERY_CAUSAL_STRUCTURE",
        "fvgDistal": 4509.17,
        "causalObBoundary": 4510.97,
        "protectedSwingBoundary": 4511.78,
        "structuralInvalidation": 4523.44,
        "originalChildDistal": 4523.44,
    }

    fast_child = market.bar(
        "M30:1780468200", parse_utc("2026-06-03T15:00:00Z")
    )
    fast_plan = {
        "scenarioHash": "june-w01-fast-m1-transfer-short",
        "frozenAtUtc": "2026-06-03T15:00:00Z",
        "childTouchAtUtc": None,
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "dealingRange": {"low": 4438.81, "high": 4487.94},
        "objective": {
            "barId": "H1:1780488000", "side": "LOW",
            "kind": "EXTERNAL_SWING", "price": 4438.81,
        },
        "root": {"proximal": 4481.63},
        "finalChild": {
            "obBarId": fast_child["barId"],
            "distal": float(fast_child["high"]),
        },
    }
    fast_fvg = market.bar(
        "M1:1780499280", parse_utc("2026-06-03T15:09:00Z")
    )
    candidate = detect_pre_touch_delivery_candidate(
        market, fast_plan, fast_fvg, 0.0
    )
    assert candidate is None


def test_v463_reaction_episode_ends_on_untriggered_m5_delivery() -> None:
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2026-01-01_2026-08-12.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2026-05-01T00:00:00Z"),
        parse_utc("2026-06-03T00:00:00Z"),
        0.01,
    )
    scenario = {
        "frozenAtUtc": "2026-06-02T16:00:00Z",
        "direction": "SHORT",
    }
    monitor = {
        "armedAtUtc": "2026-06-02T16:07:00Z",
        "sweepEvents": [],
    }
    before = market.m1_row(
        market.m1_index_at_or_after(parse_utc("2026-06-02T16:50:00Z")) - 1
    )
    assert reaction_source_episode_end_reason(
        market, scenario, monitor, before
    ) is None
    delivered = market.m1_row(
        market.m1_index_at_or_after(parse_utc("2026-06-02T16:55:00Z")) - 1
    )
    assert reaction_source_episode_end_reason(
        market, scenario, monitor, delivered
    ) == "SOURCE_EPISODE_ENDED_WITHOUT_TRIGGER:M5:1780418100"
    with_sweep = {**monitor, "sweepEvents": [{"liquidityBarId": "M1:test"}]}
    assert reaction_source_episode_end_reason(
        market, scenario, with_sweep, delivered
    ) is None


def test_v457_plan_is_frozen_at_family_formation_before_root_retest() -> None:
    market = synthetic_market()
    runtime = new_runtime(market.m1_index_at_or_after(PLAN_AT))
    row = market.m1_row(runtime["cursor"])
    runtime["newPlanFamilyIdsAtLastRefresh"] = ["family-a", "family-b"]
    runtime["flatPlanCandidates"] = [
        {"familyId": "family-a", "status": "REGISTERED"},
        {"familyId": "family-b", "status": "REGISTERED"},
    ]
    packet = {
        "externalMapAuthority": None,
        "physicalLineageFamilies": [
            {"familyId": "family-a"},
            {"familyId": "family-b"},
        ],
    }
    captured: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config={**replay_v4.DEFAULTS, "symbol": "GOLD"},
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=runtime,
        )
        original_builder = replay_v4.build_plan_packet
        replay_v4.build_plan_packet = lambda *args, **kwargs: packet
        runner.request_plan = lambda as_of, **kwargs: captured.append(  # type: ignore[method-assign]
            {"asOf": as_of, **kwargs}
        )
        try:
            assert runner.schedule_formation_driven_flat_plan(
                row, state_at_bar_start="FLAT"
            )
        finally:
            replay_v4.build_plan_packet = original_builder
        assert len(captured) == 1
        assert {
            item["familyId"] for item in captured[0]["packet"]["physicalLineageFamilies"]
        } == {"family-a", "family-b"}
        assert runner.runtime["newPlanFamilyIdsAtLastRefresh"] == []
    assert runner.stats["formationPlanWakeups"] == 1
    with tempfile.TemporaryDirectory() as temporary:
        runtime = new_runtime(market.m1_index_at_or_after(PLAN_AT))
        runtime["state"] = "PLANNED"
        runtime["scenario"] = frozen_scenario(market)
        runtime["newPlanFamilyIdsAtLastRefresh"] = ["family-c"]
        active_runner = V4Runner(
            config={**replay_v4.DEFAULTS, "symbol": "GOLD"},
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=runtime,
        )
        assert not active_runner.schedule_formation_driven_flat_plan(
            row, state_at_bar_start="PLANNED", api_allowed=False
        )
        assert active_runner.runtime["deferredPlanEvents"][0]["familyId"] == "family-c"
        assert active_runner.stats["planFamiliesBlockedWhileActive"] == 1


def test_v467_forced_remap_excludes_retired_and_unrelated_families() -> None:
    market = synthetic_market()
    runtime = new_runtime(market.m1_index_at_or_after(PLAN_AT))
    row = market.m1_row(runtime["cursor"])
    runtime["forcedRemapFamilyIds"] = ["family-new"]
    runtime["deferredPlanEvents"] = [
        {
            "familyId": "family-old",
            "reason": "DEFERRED_ACTIVE_SCENARIO",
            "scenarioOptionIds": ["old-option"],
        },
        {
            "familyId": "family-new",
            "reason": "NEWER_CAUSAL_SOURCE_REMAP",
            "scenarioOptionIds": ["new-option"],
        },
    ]
    runtime["newPlanEventsAtLastRefresh"] = [
        {
            "familyId": "family-unrelated",
            "reason": "PHYSICAL_FAMILY_DISCOVERED",
            "scenarioOptionIds": ["other-option"],
        }
    ]
    packet = {
        "externalMapAuthority": None,
        "physicalLineageFamilies": [{"familyId": "family-new"}],
    }
    captured: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config={**replay_v4.DEFAULTS, "symbol": "GOLD"},
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=runtime,
        )
        original_builder = replay_v4.build_plan_packet

        def capture_builder(*args: Any, **kwargs: Any) -> dict[str, Any]:
            assert kwargs["focus_family_ids"] == {"family-new"}
            return packet

        replay_v4.build_plan_packet = capture_builder
        runner.request_plan = lambda as_of, **kwargs: captured.append(  # type: ignore[method-assign]
            {"asOf": as_of, **kwargs}
        )
        try:
            assert runner.schedule_formation_driven_flat_plan(
                row, state_at_bar_start="FLAT"
            )
        finally:
            replay_v4.build_plan_packet = original_builder
    assert len(captured) == 1
    assert runner.runtime["forcedRemapFamilyIds"] == []
    assert runner.runtime["deferredPlanEvents"] == []
    assert {
        item["familyId"]
        for item in captured[0]["packet"]["physicalLineageFamilies"]
    } == {"family-new"}


def test_v468_tp_retires_the_completed_physical_source_family() -> None:
    market = synthetic_market()
    runtime = new_runtime(market.m1_index_at_or_after(PLAN_AT))
    runtime["state"] = "FILLED"
    runtime["scenario"] = {
        **frozen_scenario(market),
        "physicalFamilyId": "delivered-family",
    }
    runtime["order"] = {"orderId": "order"}
    runtime["position"] = {"orderId": "order"}
    runtime["triggerWatch"] = {"model": "DELIVERY_FVG_REPLACEMENT"}
    runtime["deferredPlanEvents"] = [
        {
            "familyId": "delivered-family",
            "reason": "NEW_CAUSAL_OPTION_MATURED",
            "scenarioOptionIds": [],
        }
    ]
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config={**replay_v4.DEFAULTS, "symbol": "GOLD"},
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=runtime,
        )
        runner.close(
            PLAN_AT + 60,
            {
                "orderId": "order",
                "scenarioHash": runtime["scenario"]["scenarioHash"],
                "direction": "LONG",
                "model": "DELIVERY_FVG_REPLACEMENT",
                "entryAtUtc": utc_text(PLAN_AT),
                "entry": 100.0,
                "stop": 99.0,
                "target": 120.0,
                "risk": 1.0,
                "entryBarId": "M1:1700002800",
                "exitAtUtc": utc_text(PLAN_AT + 60),
                "exitBarId": "M1:1700002860",
                "exit": 120.0,
                "outcome": "TP",
                "resultR": 20.0,
                "intrabarAmbiguous": False,
            },
        )
    assert runner.runtime["completedDeliveryFamilyIds"] == ["delivered-family"]
    assert runner.runtime["deferredPlanEvents"] == []


def test_v470_newer_source_is_deferred_until_active_plan_terminates() -> None:
    """A newer source is not an AGENTS-authorized active PLAN cancellation."""
    dataset = ROOT / "output" / "datasets" / "GOLD_M1_2026-01-01_2026-08-12.npz"
    market = MarketData.from_npz(
        dataset,
        parse_utc("2026-01-01T00:00:00Z"),
        parse_utc("2026-06-04T00:00:00Z"),
        0.01,
    )
    # At 10:00 the newer 06:00 H1 source has a still-unreached 4447.50
    # external objective that matured before the source. V4.68 rejected this
    # exact remap because its objective-maturity comparison was reversed.
    as_of = parse_utc("2026-06-03T10:00:00Z")
    runtime = new_runtime(market.m1_index_at_or_after(as_of))
    runtime["state"] = "PLANNED"
    runtime["scenario"] = {
        "scenarioHash": "stale-june-source",
        "physicalFamilyId": "e6ac6b83f0a0",
        "childTouchAtUtc": None,
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "objective": {
            "barId": "H1:1779980400", "side": "LOW",
            "kind": "EXTERNAL_SWING", "price": 4379.44,
        },
        "root": {"deliveryAvailableAtUtc": "2026-06-02T21:00:00Z"},
        "finalChild": {"deliveryAvailableAtUtc": "2026-06-02T19:15:00Z"},
    }
    runtime["newPlanEventsAtLastRefresh"] = [{
        "familyId": "f62dbd2fe627",
        "reason": "PHYSICAL_FAMILY_DISCOVERED",
        "scenarioOptionIds": [],
    }]
    row = market.m1_row(market.m1_index_at_or_after(as_of))
    with tempfile.TemporaryDirectory() as temporary:
        runner = V4Runner(
            config={**replay_v4.DEFAULTS, "symbol": "GOLD"},
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=runtime,
        )
        assert not runner.schedule_active_plan_supersession(
            row, state_at_bar_start="PLANNED"
        )
    assert runner.runtime["state"] == "PLANNED"
    assert runner.runtime["forcedRemapFamilyIds"] == []
    assert runner.stats["cancellationReasons"] == {}
    assert runner.runtime["deferredPlanEvents"][0]["familyId"] == "f62dbd2fe627"


def test_v458_plan_option_identity_ignores_intermediate_liquidity_churn() -> None:
    base = {
        "scenarioSelectionId": "volatile-a",
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "objective": {"barId": "H1:objective", "side": "LOW"},
        "lineagePathSelectionId": "path-a",
        "ownerBreakTargetBarId": None,
        "ownerBreakBarId": None,
        "intermediateLiquidityBarIds": ["M5:first"],
    }
    changed = {
        **base,
        "scenarioSelectionId": "volatile-b",
        "intermediateLiquidityBarIds": ["M5:first", "M5:second"],
    }
    assert V4Runner.stable_plan_option_key(base) == V4Runner.stable_plan_option_key(changed)


def test_weekly_positive_atlas_loader_and_explicit_gate() -> None:
    expected = {
        "truthId": "truth-1",
        "planFrozenAtUtc": "2026-06-01T01:00:00Z",
        "filledAtUtc": "2026-06-01T01:10:00Z",
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "executionModel": "DELIVERY_FVG_REPLACEMENT",
        "entry": 100.0,
        "stop": 110.0,
        "target": 90.0,
        "rootObBarId": "H1:1000",
        "refinementPath": ["M15:2000"],
        "finalChildObBarId": "M15:2000",
        "objectiveBarId": "H1:3000",
    }
    extra = {
        **expected,
        "truthId": "unlabelled-2",
        "planFrozenAtUtc": "2026-06-01T02:00:00Z",
        "filledAtUtc": "2026-06-01T02:10:00Z",
    }
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        truth = root / "truth.json"
        candidate = root / "candidate.json"
        output = root / "parity.csv"
        truth.write_text(
            json.dumps(
                {
                    "coverage": "CAUSAL_OPPORTUNITY_ATLAS_AND_MONTH_CONTINUOUS_SINGLE_SCENARIO_SEQUENCE",
                    "executionCandidates": [expected],
                }
            ),
            encoding="utf-8",
        )
        candidate.write_text(
            json.dumps({"executionCandidates": [expected, extra]}),
            encoding="utf-8",
        )
        base = {
            "candidate": candidate,
            "truth": truth,
            "output": output,
            "start": None,
            "end": None,
            "window_hours": 2.0,
            "tick_tolerance": 0.03,
        }
        assert replay_v4.compare_trades(
            argparse.Namespace(**base, positive_atlas_gate=False)
        ) == 3
        assert replay_v4.compare_trades(
            argparse.Namespace(**base, positive_atlas_gate=True)
        ) == 0
        parity = output.read_text(encoding="utf-8-sig")
        assert "EXACT" in parity
        assert "UNASSESSED" in parity


def test_trade_parity_prefers_same_cause_and_reports_alternate_delivery_fvg() -> None:
    expected = {
        "truthId": "truth-delivery",
        "planFrozenAtUtc": "2026-06-01T01:00:00Z",
        "filledAtUtc": "2026-06-01T06:10:00Z",
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "executionModel": "DELIVERY_FVG_REPLACEMENT",
        "entry": 100.0,
        "stop": 110.0,
        "target": 90.0,
        "rootObBarId": "H1:1000",
        "refinementPath": ["M15:2000"],
        "finalChildObBarId": "M15:2000",
        "objectiveBarId": "H1:3000",
    }
    nearer_wrong_cause = {
        **expected,
        "truthId": "nearer-wrong-cause",
        "filledAtUtc": "2026-06-01T06:09:00Z",
        "rootObBarId": "H1:4000",
    }
    earlier_same_cause = {
        **expected,
        "truthId": "earlier-same-cause",
        "filledAtUtc": "2026-06-01T02:00:00Z",
        "entry": 125.0,
        "stop": 140.0,
    }
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        truth = root / "truth.json"
        candidate = root / "candidate.json"
        output = root / "parity.csv"
        truth.write_text(
            json.dumps(
                {
                    "coverage": "CAUSAL_OPPORTUNITY_ATLAS_AND_MONTH_CONTINUOUS_SINGLE_SCENARIO_SEQUENCE",
                    "executionCandidates": [expected],
                }
            ),
            encoding="utf-8",
        )
        candidate.write_text(
            json.dumps(
                {"executionCandidates": [nearer_wrong_cause, earlier_same_cause]}
            ),
            encoding="utf-8",
        )
        result = replay_v4.compare_trades(
            argparse.Namespace(
                candidate=candidate,
                truth=truth,
                output=output,
                start=None,
                end=None,
                window_hours=1.0,
                tick_tolerance=0.03,
                positive_atlas_gate=True,
            )
        )
        assert result == 0
        rows = replay_v4.load_csv(output)
        matched = next(row for row in rows if row["truth_id"] == "truth-delivery")
        assert matched["candidate_id"] == "earlier-same-cause"
        assert matched["classification"] == "CAUSAL_MATCH"
        assert matched["execution_variant"] == "ALTERNATE_DELIVERY_FVG"


def test_positive_atlas_reports_single_position_occupancy_instead_of_miss() -> None:
    expected = {
        "truthId": "truth-blocked",
        "planFrozenAtUtc": "2026-06-01T14:00:00Z",
        "filledAtUtc": "2026-06-01T14:30:00Z",
        "direction": "SHORT",
        "scope": "EXTERNAL_CONTINUATION",
        "executionModel": "DELIVERY_FVG_REPLACEMENT",
        "entry": 100.0,
        "stop": 110.0,
        "target": 90.0,
        "rootObBarId": "H1:1000",
        "finalChildObBarId": "M15:2000",
        "objectiveBarId": "H1:3000",
    }
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        truth = root / "truth.json"
        candidate = root / "candidate.csv"
        output = root / "parity.csv"
        truth.write_text(json.dumps({
            "coverage": "CAUSAL_OPPORTUNITY_ATLAS_AND_MONTH_CONTINUOUS_SINGLE_SCENARIO_SEQUENCE",
            "executionCandidates": [expected],
        }), encoding="utf-8")
        candidate.write_text(
            "trade_id,decision_at,filled_at,closed_at,direction,scope,execution_model,entry,sl,tp,root_ob_bar_id,child_ob_bar_id,objective_bar_id\n"
            "active,2026-06-01T10:00:00Z,2026-06-01T10:05:00Z,2026-06-01T16:00:00Z,short,EXTERNAL_CONTINUATION,DELIVERY_FVG_REPLACEMENT,120,130,80,H1:4000,M15:5000,H1:6000\n",
            encoding="utf-8",
        )
        result = replay_v4.compare_trades(argparse.Namespace(
            candidate=candidate,
            truth=truth,
            output=output,
            start=None,
            end=None,
            # The active trade is also a nearby same-direction candidate. It
            # must remain an occupancy blocker rather than being consumed as
            # a weak DIRECTION_ONLY match.
            window_hours=8.0,
            tick_tolerance=0.03,
            positive_atlas_gate=True,
        ))
        assert result == 3
        row = replay_v4.load_csv(output)[0]
        assert row["classification"] == "BLOCKED_BY_ACTIVE_CANDIDATE"
        assert row["candidate_id"] == "active"


def test_delivery_review_is_semantic_and_deduped_per_delivery_episode() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    scenario["childTouchAtUtc"] = None
    scenario["childTouchBarId"] = None
    runtime = new_runtime(market.m1_index_at_or_after(PLAN_AT))
    runtime["state"] = "PLANNED"
    runtime["scenario"] = scenario
    row = market.m1_row(runtime["cursor"])
    candidate = {
        "shadowId": "delivery-review-candidate",
        "scenarioHash": scenario["scenarioHash"],
        "status": "WAIT_FIRST_RETEST",
        "direction": scenario["direction"],
        "formedAtUtc": utc_text(row["available"]),
        "formedBarId": row["barId"],
        "fvg": {"low": 108.0, "high": 109.0},
        "causalObBarId": row["barId"],
        "deliveryConfirmation": {
            "mode": "M5_STRUCTURE_TRANSFER",
            "barId": "M5:1700006100",
            "level": 108.0,
        },
    }
    response = {
        "schemaVersion": "4.61.0",
        "candidateId": candidate["shadowId"],
        "action": "APPROVE_REPLACEMENT",
        "sourceEpisodeContinuity": "PASS",
        "ownerObjectiveContinuity": "PASS",
        "meaningfulStructureTransfer": "PASS",
        "causalFvgAndOb": "PASS",
        "firstRetestEligibility": "PASS",
        "reason": "The supplied delivery remains causally attached to the frozen lineage.",
    }
    with tempfile.TemporaryDirectory() as temp:
        run_dir = Path(temp)
        image = run_dir / "review.png"
        image.write_bytes(b"delivery-review-fixture")
        original_render = replay_v4.render_images
        replay_v4.render_images = lambda *_args, **_kwargs: [image]
        try:
            runner = V4Runner(
                config=copy.deepcopy(replay_v4.DEFAULTS),
                market=market,
                run_dir=run_dir,
                provider=ScriptedProvider([response]),
                runtime=runtime,
            )
            assert runner.request_delivery_review(row, candidate)
            assert runner.request_delivery_review(row, candidate)
            assert runner.stats["deliveryReviewRequests"] == 1
            assert runner.stats["deliveryReviewApproved"] == 1
            assert len(runner.runtime["deliveryReviewHistory"]) == 1
        finally:
            replay_v4.render_images = original_render

def test_v470_delivery_lineage_resolution_is_pre_outcome_and_unambiguous() -> None:
    def scenario(root: str, child: str, scope: str, objective: str, price: float) -> dict[str, Any]:
        return {
            "direction": "LONG",
            "scope": scope,
            "root": {"obBarId": root},
            "refinements": [{"obBarId": child}],
            "objective": {"barId": objective, "price": price},
        }

    active = scenario(
        "H1:1700000000", "M15:1700000900",
        "EXTERNAL_CONTINUATION", "H1:1700010000", 120.0,
    )
    active_candidate = {"entry": 105.0}

    def variant(item: dict[str, Any], *, result: str) -> dict[str, Any]:
        return {
            "selectionId": result,
            "rootObBarId": item["root"]["obBarId"],
            "refinementObBarIds": [node["obBarId"] for node in item["refinements"]],
            "scope": item["scope"],
            "objectiveBarId": item["objective"]["barId"],
            "objectivePrice": item["objective"]["price"],
            "fullyContained": True,
            "scenario": item,
            "futureOutcomeMustBeIgnored": result,
        }

    same_path_internal = scenario(
        "H1:1700000000", "M15:1700000900",
        "INTERNAL_ROTATION", "M5:1700005000", 110.0,
    )
    resolved = resolve_delivery_lineage_variants(
        active,
        active_candidate,
        [
            variant(active, result="SL"),
            variant(same_path_internal, result="TP"),
        ],
        "M1:1700007000",
    )
    assert resolved["approved"]
    assert resolved["reason"] == "UNIQUE_CAUSAL_LINEAGE_AND_OBJECTIVE"

    adjacent_unique = variant(active, result="TP")
    adjacent_unique["fullyContained"] = False
    adjacent = resolve_delivery_lineage_variants(
        active,
        active_candidate,
        [adjacent_unique],
        "M1:1700007000",
    )
    assert adjacent["approved"]
    assert adjacent["reason"] == "UNIQUE_CAUSAL_LINEAGE_AND_OBJECTIVE"

    competing = scenario(
        "H1:1699990000", "M30:1699991800",
        "EXTERNAL_CONTINUATION", "H1:1700010000", 120.0,
    )
    ambiguous = resolve_delivery_lineage_variants(
        active,
        active_candidate,
        [variant(active, result="TP"), variant(competing, result="SL")],
        "M1:1700007000",
    )
    assert not ambiguous["approved"]
    assert ambiguous["reason"] == "MULTIPLE_FULLY_CONTAINED_CAUSAL_LINEAGES"

    wrong_objective = copy.deepcopy(active)
    wrong_objective["objective"] = {"barId": "H1:1700020000", "price": 130.0}
    objective_mismatch = resolve_delivery_lineage_variants(
        wrong_objective,
        active_candidate,
        [variant(active, result="SL")],
        "M1:1700007000",
    )
    assert not objective_mismatch["approved"]
    assert objective_mismatch["reason"] == "ACTIVE_OBJECTIVE_DIFFERS_FROM_CAUSAL_RESOLUTION"


def main() -> int:
    test_v474_current_objectives_plus_two_long_history_h1_fallbacks()
    test_plan_packet_excludes_m1_and_schema_uses_dynamic_ids()
    test_complete_agents_contract_is_sent_as_gemini_system_instruction()
    test_plan_freezes_complete_lineage_and_rejects_wrong_pd_half()
    test_continuation_objective_may_form_after_root_delivery_before_plan()
    test_post_touch_liquidity_matures_before_separate_sweep()
    test_final_sweep_extends_only_across_contiguous_excursion()
    test_immediate_resweep_preserves_deepest_physical_extreme()
    test_external_reversal_separates_old_owner_break_from_new_owner_invalidation()
    test_rejection_actions_cannot_smuggle_semantic_evidence()
    test_trigger_schema_has_no_engine_owned_fields()
    test_touch_then_separate_sweep_choch_order_fill_and_tp()
    test_premature_sweep_and_through_delivery_are_rejected()
    test_delivery_fvg_replacement_rejects_a_first_touch_through_fvg_distal()
    test_local_reauthorization_cancels_only_exact_owner_or_source_break()
    test_delivery_fvg_replacement_is_single_use()
    test_all_runtime_states_and_per_execution_trigger_calls()
    test_multi_position_book_uses_book_identity_and_rejects_duplicate_execution()
    test_scripted_provider_and_hash_ledger_are_deterministic()
    test_two_key_slots_are_local_selectable_and_never_written_to_config()
    test_scripted_responses_never_pollute_shared_model_cache()
    test_runner_never_calls_semantic_provider_between_engine_events()
    test_flat_plan_is_requested_before_contact_and_fingerprint_dedupes()
    test_active_wait_loop_uses_no_semantic_calls()
    test_precontact_plan_survives_restart_and_waits_without_api()
    test_flat_h1_scheduler_does_not_repeat_unchanged_plan()
    test_continuous_flat_run_calls_once_when_root_is_approached()
    test_event_driven_plan_calls_once_on_root_approach()
    test_candidate_discovered_on_current_bar_cannot_trigger_plan()
    test_short_poi_departure_is_not_directional_approach()
    test_plan_wakes_only_at_the_actual_root_proximal_boundary()
    test_active_bar_approach_cannot_be_resurrected_after_terminal()
    test_plan_packet_uses_exact_m1_clock_and_keeps_latest_m5_context()
    test_june_0643_short_family_is_departure_not_poi_approach()
    test_event_driven_plan_wakes_on_root_touch_before_child_touch()
    test_active_plan_never_wakes_a_second_plan()
    test_parked_plan_restores_without_api_and_stale_touch_is_discarded()
    test_accepted_challenger_isolated_in_lane_and_external_reversal_advances_owner()
    test_resume_gets_a_fresh_operational_budget_without_resetting_totals()
    test_plan_budget_pause_does_not_consume_the_h1_event()
    test_recoverable_json_cutoff_retries_with_minimal_thinking_and_counts_all_tokens()
    test_gemini_quota_circuit_skips_exhausted_primary_after_first_429()
    test_gemini_429_switches_key_before_model_fallback()
    test_trigger_watch_inherits_global_lite_fallback_on_quota()
    test_successful_server_retry_does_not_poison_the_next_flash_request()
    test_plan_model_routing_spends_flash_only_on_owner_authority_decisions()
    test_plan_prompt_does_not_forbid_opposite_internal_rotation()
    test_exact_source_rejudgment_reuses_model_evidence_and_hides_prior_response()
    test_plan_model_view_keeps_all_selectable_options_under_sep1_prompt_bound()
    test_sep4_later_causal_source_upgrade_is_found_and_touched_without_api()
    test_first_m1_after_market_gap_refreshes_closed_h1_map()
    test_no_future_bar_can_be_resolved()
    test_preexisting_objective_and_fresh_child_regression()
    test_plan_freshness_and_schema_share_the_same_m1_clock()
    test_m15_pivot_cannot_be_promoted_to_external_objective()
    test_external_scenario_options_keep_nearest_and_expose_h1_alternative()
    test_persistent_external_owner_survives_trade_and_blocks_opposite_continuation()
    test_active_owner_exposes_newly_mature_nearer_h1_objective_for_new_scenario()
    test_active_external_authority_cannot_be_redefined_by_new_internal_delivery()
    test_newer_causal_delivery_dominates_an_older_source_for_the_same_objective()
    test_one_excursion_exposes_only_outermost_mature_liquidity()
    test_causal_parity_accepts_only_nested_root_with_same_execution_lineage()
    test_funnel_comparison_attributes_the_complete_chain()
    test_v450_june_authority_remaps_without_candidate_cap_or_deadlock()
    test_v450_internal_rotation_objective_must_stay_inside_range()
    test_v450_external_continuation_records_every_internal_delivery()
    test_v450_rejects_m5_trigger_from_before_child_touch_episode()
    test_v452_delivery_replacement_creates_one_first_retest_order()
    test_v462_delivery_fvg_accepts_m5_or_completed_m1_transfer()
    test_v463_reaction_episode_ends_on_untriggered_m5_delivery()
    test_v457_plan_is_frozen_at_family_formation_before_root_retest()
    test_v467_forced_remap_excludes_retired_and_unrelated_families()
    test_v468_tp_retires_the_completed_physical_source_family()
    test_v470_newer_source_is_deferred_until_active_plan_terminates()
    test_v458_plan_option_identity_ignores_intermediate_liquidity_churn()
    test_weekly_positive_atlas_loader_and_explicit_gate()
    test_trade_parity_prefers_same_cause_and_reports_alternate_delivery_fvg()
    test_positive_atlas_reports_single_position_occupancy_instead_of_miss()
    test_delivery_review_is_semantic_and_deduped_per_delivery_episode()
    test_v470_delivery_lineage_resolution_is_pre_outcome_and_unambiguous()
    print("MENTOR_AI_REPLAY_V4_TESTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
