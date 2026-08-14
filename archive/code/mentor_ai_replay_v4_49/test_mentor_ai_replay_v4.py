from __future__ import annotations

import copy
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

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
    advance_pending,
    advance_position,
    advance_reaction_monitor,
    advance_source_upgrade_candidates,
    advance_trigger_watch,
    assert_runtime_invariants,
    build_plan_packet,
    build_map_packet,
    build_reaction_monitor,
    build_trigger_packet,
    discover_source_upgrade_candidates,
    delivery_replacement,
    external_authority_from_scenario,
    resolved_external_authority,
    freeze_plan,
    freeze_trigger_watch,
    local_scenario_cancel_reason,
    map_opportunity_id,
    map_schema,
    new_runtime,
    outermost_completed_sweep_events,
    parse_utc,
    plan_schema,
    reset_terminal,
    refresh_reaction_monitor,
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
        "schemaVersion": "4.11.0", "action": "NO_PLAN",
        "scenarioSelectionId": None,
        "semanticAudit": {
            "externalOwnerAndScope": "UNRESOLVED",
            "objectiveClassificationAndMaturity": "UNRESOLVED",
            "rootDisplacementCausality": "UNRESOLVED",
            "fullRefinementCausality": "UNRESOLVED",
            "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
        },
        "reason": "No synthetic family.",
    }
    Draft202012Validator(schema).validate(payload)
    atomic_packet = with_synthetic_atomic_family(packet)
    atomic_schema = plan_schema(atomic_packet)
    enum_values = atomic_schema["properties"]["scenarioSelectionId"]["anyOf"][0]["enum"]
    assert enum_values == ["scenario-synthetic"]
    assert "selectedBarIds" not in schema["properties"]
    assert "root" not in schema["properties"] and "rootSelectionId" not in schema["properties"]
    assert "refinements" not in schema["properties"] and "lineagePathSelectionId" not in schema["properties"]
    assert not any(key in schema["properties"] for key in ("state", "phase", "asOfUtc", "entry", "stop"))

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
    assert "## 3." in system_instruction and "## 5." in system_instruction
    assert "## 1." not in system_instruction and "## 9." not in system_instruction


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


def test_delivery_fvg_replacement_can_fill_past_fvg_distal_when_causal_stop_holds() -> None:
    market = synthetic_market()
    row = {
        **market.m1_row(market.m1_index_at_or_after(TOUCH_TIME - 60) + 1),
        "low": 100.0,
        "high": 102.0,
        "spreadPoints": 2,
    }
    order = {
        "direction": "LONG",
        "entry": 101.0,
        "stop": 99.0,
        "target": 120.0,
        "orderId": "delivery-replacement",
        "scenarioHash": "scenario",
        "model": "DELIVERY_FVG_REPLACEMENT",
        "executionZone": {"low": 100.5, "high": 101.0},
    }
    result, position = advance_pending(market, order, row)
    assert result == "FILLED" and position is not None
    assert position["model"] == "DELIVERY_FVG_REPLACEMENT"


def test_local_reauthorization_cancels_only_exact_owner_or_source_break() -> None:
    market = synthetic_market()
    scenario = frozen_scenario(market)
    ordinary = market.m1_row(market.m1_index_at_or_after(TOUCH_TIME - 60) + 2)
    assert local_scenario_cancel_reason(market, scenario, ordinary) is None
    broken = {**ordinary, "available": BASE + 7200}
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


def test_all_runtime_states_and_two_call_invariant() -> None:
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
    invalid = copy.deepcopy(value)
    invalid["apiCallsByScenario"] = {"abc": 3}
    try:
        assert_runtime_invariants(invalid)
    except AssertionError as exc:
        assert "exceeded two" in str(exc)
    else:
        raise AssertionError("three semantic calls were accepted")
    terminal = reset_terminal(value, "CLOSED")
    assert terminal["state"] == "FLAT" and terminal["closedTrades"] == 1


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


def test_scripted_responses_never_pollute_shared_model_cache() -> None:
    market = synthetic_market()
    packet = with_synthetic_atomic_family(
        build_plan_packet(market, PLAN_AT, "GOLD")
    )
    schema = plan_schema(packet)
    invalid = scenario_plan_payload(packet)
    invalid["scenarioSelectionId"] = "scenario-not-supplied"
    valid = scenario_plan_payload(packet)
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
            assert freeze_plan(payload, market, PLAN_AT, set(), packet) is not None
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
        "schemaVersion": "4.11.0", "action": "NO_PLAN",
        "scenarioSelectionId": None,
        "semanticAudit": {
            "externalOwnerAndScope": "UNRESOLVED",
            "objectiveClassificationAndMaturity": "UNRESOLVED",
            "rootDisplacementCausality": "UNRESOLVED",
            "fullRefinementCausality": "UNRESOLVED",
            "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
        },
        "reason": "Synthetic no-plan response.",
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
            assert runner.stats["flatPlanFingerprintSkips"] == 1
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
                provider=ScriptedProvider([scenario_plan_payload(packet)]),
                runtime=new_runtime(market.m1_index_at_or_after(PLAN_AT)),
            )
            assert runner.schedule_flat_plan(PLAN_AT)
            assert runner.runtime["state"] == "PLANNED"
            assert runner.runtime["scenario"]["childTouchAtUtc"] is None
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
            assert resumed.runtime["state"] == "PLANNED"
            assert resumed.stats["semanticRequests"] == before
            assert resumed.stats["activeZeroTokenBars"] > 0
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_flat_h1_scheduler_does_not_repeat_unchanged_plan() -> None:
    market = synthetic_market()
    no_plan = {
        "schemaVersion": "4.11.0", "action": "NO_PLAN",
        "scenarioSelectionId": None,
        "semanticAudit": {
            "externalOwnerAndScope": "UNRESOLVED",
            "objectiveClassificationAndMaturity": "UNRESOLVED",
            "rootDisplacementCausality": "UNRESOLVED",
            "fullRefinementCausality": "UNRESOLVED",
            "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
        },
        "reason": "Synthetic no-plan response.",
    }
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
            assert runner.stats["flatPlanFingerprintSkips"] == 1
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_continuous_flat_run_calls_once_when_root_is_approached() -> None:
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
    assert packet["physicalLineageFamilies"]
    no_plan = {
        "schemaVersion": "4.11.0", "action": "NO_PLAN",
        "scenarioSelectionId": None,
        "semanticAudit": {
            "externalOwnerAndScope": "UNRESOLVED",
            "objectiveClassificationAndMaturity": "UNRESOLVED",
            "rootDisplacementCausality": "UNRESOLVED",
            "fullRefinementCausality": "UNRESOLVED",
            "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
        },
        "reason": "Synthetic no-plan response.",
    }
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
    no_plan = {
        "schemaVersion": "4.11.0", "action": "NO_PLAN",
        "scenarioSelectionId": None,
        "semanticAudit": {
            "externalOwnerAndScope": "UNRESOLVED",
            "objectiveClassificationAndMaturity": "UNRESOLVED",
            "rootDisplacementCausality": "UNRESOLVED",
            "fullRefinementCausality": "UNRESOLVED",
            "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
        },
        "reason": "Synthetic no-plan response.",
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
            height = root["high"] - root["low"]
            far = {
                "available": PLAN_AT + 60,
                "low": root["high"] + height * 2.0,
                "high": root["high"] + height * 2.5,
                "close": root["high"] + height * 2.2,
            }
            assert not runner.schedule_event_driven_flat_plan(far)
            assert runner.stats["semanticRequests"] == 0
            near = {
                "available": PLAN_AT + 120,
                # Parent proximal touch is still a valid planning wakeup. The
                # contract only requires the selected final child to be frozen
                # before its own touch.
                "low": root["low"] + height * 0.5,
                "high": root["high"] + height,
                "close": root["high"] + height * 0.25,
            }
            assert runner.schedule_event_driven_flat_plan(near)
            assert runner.stats["semanticRequests"] == 1
            assert not runner.schedule_event_driven_flat_plan(near)
            assert runner.stats["semanticRequests"] == 1
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.build_plan_packet = original_builder


def test_active_plan_only_wakes_for_an_opposite_root_family() -> None:
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
    no_plan = {
        "schemaVersion": "4.11.0", "action": "NO_PLAN",
        "scenarioSelectionId": None,
        "semanticAudit": {
            "externalOwnerAndScope": "UNRESOLVED",
            "objectiveClassificationAndMaturity": "UNRESOLVED",
            "rootDisplacementCausality": "UNRESOLVED",
            "fullRefinementCausality": "UNRESOLVED",
            "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
        },
        "reason": "Synthetic challenger rejected.",
    }
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
                provider=ScriptedProvider([no_plan]), runtime=runtime,
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
            assert runner.schedule_event_driven_flat_plan(near)
            assert runner.stats["semanticRequests"] == 1
            assert runner.stats["challengerPlanWakeups"] == 1
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


def test_accepted_challenger_parks_prior_plan_but_external_reversal_replaces_it() -> None:
    market = synthetic_market()
    original = frozen_scenario(market)
    packet = with_synthetic_atomic_family(build_plan_packet(market, PLAN_AT, "GOLD"))
    packet["physicalLineageFamilies"][0]["direction"] = "SHORT"
    response = {
        "schemaVersion": "4.11.0", "action": "NO_PLAN",
        "scenarioSelectionId": None,
        "semanticAudit": {
            "externalOwnerAndScope": "UNRESOLVED",
            "objectiveClassificationAndMaturity": "UNRESOLVED",
            "rootDisplacementCausality": "UNRESOLVED",
            "fullRefinementCausality": "UNRESOLVED",
            "dealingRangePdAndCompetingLiquidity": "UNRESOLVED",
        },
        "reason": "Synthetic response replaced by the frozen fixture.",
    }
    config = {
        **replay_v4.DEFAULTS,
        "symbol": "GOLD", "brokerStopsLevelPrice": 0.0, "point": 0.01,
        "dataset": "unused", "warmupStartUtc": utc_text(BASE - 10800),
    }
    original_renderer = replay_v4.render_images
    original_freezer = replay_v4.freeze_plan
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
        with tempfile.TemporaryDirectory() as temporary:
            runtime = new_runtime(0)
            runtime.update({
                "state": "PLANNED", "scenario": copy.deepcopy(original),
                "acceptedScenarioHashes": [original["scenarioHash"]],
                "apiCallsByScenario": {original["scenarioHash"]: 1},
            })
            runner = V4Runner(
                config=config, market=market, run_dir=Path(temporary),
                provider=ScriptedProvider([response]), runtime=runtime,
            )
            runner.request_plan(
                PLAN_AT + 60, packet=copy.deepcopy(packet),
                plan_fingerprint="challenger", challenger=True,
            )
            assert runner.runtime["scenario"]["scenarioHash"] == "internal-challenger"
            assert len(runner.runtime["parkedScenarios"]) == 1
            assert runner.runtime["parkedScenarios"][0]["scenario"]["scenarioHash"] == original["scenarioHash"]
            runner.cancel(PLAN_AT + 120, "SYNTHETIC_CHALLENGER_CANCELED")
            assert runner.runtime["scenario"]["scenarioHash"] == original["scenarioHash"]
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
        with tempfile.TemporaryDirectory() as temporary:
            runtime = new_runtime(0)
            runtime.update({
                "state": "PLANNED", "scenario": copy.deepcopy(original),
                "acceptedScenarioHashes": [original["scenarioHash"]],
                "apiCallsByScenario": {original["scenarioHash"]: 1},
            })
            runner = V4Runner(
                config=config, market=market, run_dir=Path(temporary),
                provider=ScriptedProvider([response]), runtime=runtime,
            )
            runner.request_plan(
                PLAN_AT + 60, packet=copy.deepcopy(packet),
                plan_fingerprint="reversal", challenger=True,
            )
            assert runner.runtime["scenario"]["scenarioHash"] == "external-reversal-challenger"
            assert runner.runtime["parkedScenarios"] == []
    finally:
        replay_v4.render_images = original_renderer
        replay_v4.freeze_plan = original_freezer
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
    no_plan = {
        "schemaVersion": "4.11.0",
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
    }

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
            replay_v4.build_plan_packet = lambda *_args, **_kwargs: packet  # type: ignore[assignment]
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
    assert '"scopeOwnerRule":"IR"' in prompt
    schema = replay_v4.plan_schema(packet)
    assert schema["properties"]["semanticAudit"]["properties"][
        "externalOwnerAndScope"
    ]["enum"] == ["PASS"]
    packet["externalMapAuthority"] = None
    ir_only_schema = replay_v4.plan_schema(packet)
    assert ir_only_schema["properties"]["semanticAudit"]["properties"][
        "externalOwnerAndScope"
    ]["enum"] == ["PASS"]


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
    assert len(packet["physicalLineageFamilies"]) == 4
    for full, compact in zip(
        packet["physicalLineageFamilies"],
        model_packet["physicalLineageFamilies"],
    ):
        assert "childCandidates" in full
        assert "childCandidates" not in compact
        assert compact["lineagePathOptions"] == full["lineagePathOptions"]
        assert [
            {key: value for key, value in option.items() if key != "scopeOwnerRule"}
            for option in compact["scenarioOptions"]
        ] == full["scenarioOptions"]
        assert all("scopeOwnerRule" in option for option in compact["scenarioOptions"])
    assert len(prompt_for("PLAN", packet).encode("utf-8")) <= 36000


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
    assert len(candidates) == 1
    assert candidates[0]["root"]["obBarId"] == "M15:1757002500"
    assert candidates[0]["finalChild"]["obBarId"] == "M5:1757003700"
    scenario["sourceUpgradeCandidates"] = candidates
    start = market.m1_index_at_or_after(parse_utc("2025-09-04T18:00:00Z"))
    end = market.m1_index_at_or_after(parse_utc("2025-09-04T19:00:00Z"))
    touched = []
    for index in range(start, end):
        touched.extend(advance_source_upgrade_candidates(scenario, market.m1_row(index)))
    assert [item["touchBarId"] for item in touched] == ["M1:1757012220"]


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
            },
            market=market,
            run_dir=Path(temporary),
            provider=ScriptedProvider([]),
            runtime=runtime,
        )

        def record_schedule(as_of: int, *, api_allowed: bool = True) -> bool:
            latest = runner.latest_h1_available(int(as_of))
            if latest != runner.runtime.get("lastPlanH1Available"):
                calls.append(int(as_of))
                runner.runtime["lastPlanH1Available"] = latest
            return False

        runner.schedule_flat_plan = record_schedule  # type: ignore[method-assign]
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
    family = next(
        item for item in packet["physicalLineageFamilies"]
        if item["rootBarId"] == "M30:1761922800"
    )
    child = next(
        item for item in family["childCandidates"]
        if item["rootBarId"] == "M5:1761924000"
    )
    assert any(
        item["barId"] == "M30:1761915600"
        for item in family["unconsumedDirectionalLiquidityCandidates"]
    )
    assert child["rootBarId"] == "M5:1761924000"

    payload = {
        "schemaVersion": "4.7.0",
        "action": "PLAN",
        "direction": "SHORT",
        "scope": "INTERNAL_ROTATION",
        "dealingRange": {
            "highBarId": "H1:1761922800",
            "lowBarId": "H1:1761915600",
        },
        "objective": {
            "barId": "M30:1761915600",
            "side": "LOW",
            "kind": "INTERNAL_SWING",
        },
        "mapProtectedSwingBarId": "H1:1761922800",
        "ownerBreakTargetBarId": None,
        "ownerBreakBarId": None,
        "root": {
            "obBarId": "M15:1761922800",
            "displacementBarId": "M15:1761924600",
            "protectedSwingBarId": "M15:1761921900",
        },
        "refinements": [
            {
                "obBarId": "M5:1761924000",
                "displacementBarId": "M5:1761924600",
                "protectedSwingBarId": "M5:1761923700",
            }
        ],
        "intermediateLiquidityBarIds": [],
        "reason": "Regression fixture for a pre-existing internal objective.",
    }
    scenario = freeze_plan(payload, market, as_of, set())
    assert scenario is not None
    assert scenario["objective"]["price"] == 4001.59

    try:
        freeze_plan(payload, market, parse_utc("2025-10-31T16:15:00Z"), set())
    except V4ContractError as exc:
        assert "already touched before PLAN" in str(exc)
    else:
        raise AssertionError("stale final child was accepted after its first touch")


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
        if item["rootBarId"] == "H1:1756846800"
    )
    assert [
        item["rootBarId"] for item in family["childCandidates"]
    ] == ["M15:1756849500", "M5:1756849800"]

    focused = build_plan_packet(
        market, as_of, "GOLD", {str(family["familyId"])}
    )
    scenario_enum = plan_schema(focused)["properties"]["scenarioSelectionId"][
        "anyOf"
    ][0]["enum"]
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
    assert "M30:1756848600" not in selected_ob_ids
    assert "M15:1756849500" in selected_ob_ids
    assert "M5:1756849800" in selected_ob_ids
    assert any(
        [node["obBarId"] for node in option["refinements"]]
        == ["M15:1756849500", "M5:1756849800"]
        for option in matching_family["lineagePathOptions"]
    )
    assert not any(
        [node["obBarId"] for node in option["refinements"]]
        == ["M15:1756849500"]
        for option in matching_family["lineagePathOptions"]
    )
    bad_mixed_tuple = {
        "obBarId": "M5:1756849800",
        "displacementBarId": "M5:1756850400",
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


def test_external_scenario_option_cannot_skip_nearest_h1_m30_liquidity() -> None:
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
        if item["rootBarId"] == "H1:1756882800"
    )
    external_options = [
        option for option in family["scenarioOptions"]
        if option["scope"] == "EXTERNAL_CONTINUATION"
    ]
    assert external_options
    assert {
        option["objective"]["barId"] for option in external_options
    } == {"H1:1756864800"}
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
    assert continuation
    assert {item["direction"] for item in continuation} == {"LONG"}
    assert {item["objective"]["barId"] for item in continuation} == {
        "H1:1756868400"
    }

    corrected_second = {
        "scenarioHash": "second-long",
        "frozenAtUtc": "2025-09-03T04:01:00Z",
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
        option["objective"]["barId"]
        for family in packet_1000["physicalLineageFamilies"]
        for option in family["scenarioOptions"]
        if option["direction"] == "LONG"
        and option["scope"] == "EXTERNAL_CONTINUATION"
    }
    assert continued_objectives == {"H1:1756868400"}


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
    assert {
        option["objective"]["barId"] for option in continuations
    } == {"H1:1756785600"}
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
    roots = {
        family["rootBarId"] for family in packet["physicalLineageFamilies"]
        if any(
            option["scope"] == "EXTERNAL_CONTINUATION"
            for option in family["scenarioOptions"]
        )
    }
    assert "H1:1756825200" not in roots
    assert "H1:1756846800" in roots


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


def main() -> int:
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
    test_delivery_fvg_replacement_can_fill_past_fvg_distal_when_causal_stop_holds()
    test_local_reauthorization_cancels_only_exact_owner_or_source_break()
    test_delivery_fvg_replacement_is_single_use()
    test_all_runtime_states_and_two_call_invariant()
    test_scripted_provider_and_hash_ledger_are_deterministic()
    test_scripted_responses_never_pollute_shared_model_cache()
    test_runner_never_calls_semantic_provider_between_engine_events()
    test_flat_plan_is_requested_before_contact_and_fingerprint_dedupes()
    test_active_wait_loop_uses_no_semantic_calls()
    test_precontact_plan_survives_restart_and_waits_without_api()
    test_flat_h1_scheduler_does_not_repeat_unchanged_plan()
    test_continuous_flat_run_calls_once_when_root_is_approached()
    test_event_driven_plan_calls_once_on_root_approach()
    test_active_plan_only_wakes_for_an_opposite_root_family()
    test_parked_plan_restores_without_api_and_stale_touch_is_discarded()
    test_accepted_challenger_parks_prior_plan_but_external_reversal_replaces_it()
    test_resume_gets_a_fresh_operational_budget_without_resetting_totals()
    test_plan_budget_pause_does_not_consume_the_h1_event()
    test_recoverable_json_cutoff_retries_with_minimal_thinking_and_counts_all_tokens()
    test_gemini_quota_circuit_skips_exhausted_primary_after_first_429()
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
    test_external_scenario_option_cannot_skip_nearest_h1_m30_liquidity()
    test_persistent_external_owner_survives_trade_and_blocks_opposite_continuation()
    test_active_external_authority_cannot_be_redefined_by_new_internal_delivery()
    test_newer_causal_delivery_dominates_an_older_source_for_the_same_objective()
    test_one_excursion_exposes_only_outermost_mature_liquidity()
    test_causal_parity_accepts_only_nested_root_with_same_execution_lineage()
    test_funnel_comparison_attributes_the_complete_chain()
    print("MENTOR_AI_REPLAY_V4_TESTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
