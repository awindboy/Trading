from __future__ import annotations

import hashlib
import ast
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "AGENTS.md"
CORE = ROOT / "scripts" / "mentor_replay_v4_core.py"
RUNNER = ROOT / "scripts" / "mentor_ai_replay_v4.py"
OUTPUT = ROOT / "mentor_context_pack" / "api_contracts"
V451_TESTS = ROOT / "scripts" / "test_mentor_ai_replay_v451.py"


PHASE_SECTIONS: dict[str, tuple[int, ...]] = {
    "plan": (1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 14, 15, 18),
    "triggerWatch": (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 18),
    "deliveryReview": (1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 14, 15, 18),
}


CONTRACTS: dict[str, tuple[str, str]] = {
    "plan": (
        "plan_v4.md",
        """# PLAN contract - Ground Truth V2

- `AGENTS.md` is the sole strategy authority. Generic ICT/SMC, V32, scores, oracle output, move indexes, hindsight, and trade outcomes cannot authorize a scenario.
- The request is paged without deleting candidates. Return exactly one verdict for every supplied family ID. Missing, extra, or duplicate family IDs invalidate the whole page.
- For each family independently judge owner/scope, dealing range and PD half, root displacement causality, complete refinement causality, source freshness, and objective-family classification.
- The ordered objective family is engine evidence. Do not select a final TP, alter prices, reorder members, or prefer a farther level for larger R. The engine chooses the first still-live member with planned R at least 1 after Entry and hard SL exist.
- At most the two nearest unconsumed historical H1 levels from 2023-12-01 onward may be carried as inactive fallback evidence. Historical M30-or-lower levels are forbidden. The engine may activate historical H1 only when no current member remains eligible after Entry and hard SL geometry; the model must never prefer it for distance or larger R.
- INTERNAL_ROTATION stays inside the range and uses meaningful M15-or-higher liquidity. EXTERNAL_CONTINUATION preserves H1/M30 external objectives and records nearer levels as intermediate delivery.
- PLAN cannot inspect M1, create an order, or return prices, timestamps, state, schedule, watch events, entry, SL, or TP.
- Approve every defensible independent family. Do not suppress a family merely because another accepted watch lane exists; risk capacity is an engine responsibility.
""",
    ),
    "triggerWatch": (
        "trigger_watch_v4.md",
        """# TRIGGER_WATCH contract - Ground Truth V2

- `AGENTS.md` is the sole strategy authority. The frozen root, child, owner, scope, and objective family must remain intact.
- Trigger starts only after the final child is actually touched. Required chain: pre-existing mature liquidity, later independent sweep and recovery, meaningful M1 body-close CHoCH of the correction-controlling swing, causal execution OB, then first later retest.
- A newborn same-leg high/low, wick break, micro pivot, M1-only bounce against M5 correction, stale episode, or retrospective retest is invalid.
- Return only supplied role IDs. The engine prices HTF_OB_REACTION orders and applies structural invalidation, spread, broker stops level, and tick.
- API response latency cannot revive a passed first retest. Such cases are `MISSED_API_LATENCY`, not orders.
""",
    ),
    "deliveryReview": (
        "delivery_review_v4.md",
        """# DELIVERY_REVIEW contract - Ground Truth V2

- `AGENTS.md` is the sole strategy authority. A Delivery FVG cannot invent owner, scope, root, child, or objective family.
- Replacement is allowed before final-child touch only when the complete owner/root/child/objective-family lineage was already frozen, the original OB order is unfilled, and a new destination-direction body structure transfer creates a fresh FVG with causal evidence.
- Addon remains disabled until the base HTF-to-LTF OB execution model has independently demonstrated reproducibility. The active runtime must not request or approve addon orders.
- Approve only the first retest of a fresh physical FVG. One physical FVG/retest has one execution ID; unresolved competing lineages are rejected.
- Bullish FVG entry is its upper proximal and bearish entry is its lower proximal. Hard SL is outside the most conservative boundary among the displacement causal OB, protected swing, and original final-child invalidation, plus `max(actual spread, broker stops level, 1 tick)`.
- FVG distal is not the hard-SL authority. If fill-time spread exceeds the frozen buffer, cancel rather than widen SL.
- The engine deterministically chooses TP from the frozen ordered objective family. The model must not return or alter prices, state, schedule, order values, or TP.
""",
    ),
}


REQUIRED_TEXT = {
    "plan": ("every supplied family ID", "ordered objective family", "planned R at least 1"),
    "triggerWatch": ("MISSED_API_LATENCY", "final child is actually touched"),
    "deliveryReview": ("Addon remains disabled", "FVG distal is not the hard-SL authority", "most conservative boundary"),
}

FORBIDDEN_TEXT = (
    "FVG structural SL",
    "M5 final TP",
    "Select one supplied scenarioSelectionId",
    "replacement hard SL is based only on the displacement causal OB",
    "hard SL은 fresh FVG distal",
    "hard SL belongs to the fresh FVG distal",
    "FVG hard SL 계산에는 포함하지 않는다",
    '"enableDeliveryAddons": True',
)


def normalized_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pipeline_version() -> str:
    match = re.search(r'^PIPELINE_VERSION\s*=\s*"([^"]+)"', normalized_text(CORE), re.M)
    if not match:
        raise SystemExit("PIPELINE_VERSION is missing")
    return match.group(1)


def authority_sections(authority: str) -> dict[int, dict[str, Any]]:
    lines = authority.splitlines()
    headings: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines, 1):
        match = re.match(r"^##\s+(\d+)\.\s+(.+)$", line)
        if match:
            headings.append((int(match.group(1)), index, match.group(2)))
    output: dict[int, dict[str, Any]] = {}
    for position, (number, start, title) in enumerate(headings):
        end = headings[position + 1][1] - 1 if position + 1 < len(headings) else len(lines)
        output[number] = {"title": title, "start": start, "end": end}
    return output


def validate_contracts(rendered: dict[str, str]) -> None:
    combined = "\n".join([
        *rendered.values(),
        normalized_text(AUTHORITY),
        normalized_text(CORE),
        normalized_text(RUNNER),
    ])
    for phrase in FORBIDDEN_TEXT:
        if phrase.lower() in combined.lower():
            raise SystemExit(f"forbidden legacy contract phrase remains: {phrase}")
    for contract, phrases in REQUIRED_TEXT.items():
        for phrase in phrases:
            if phrase.lower() not in rendered[contract].lower():
                raise SystemExit(f"required {contract} contract phrase missing: {phrase}")


def executable_coverage_tests() -> set[str]:
    if not V451_TESTS.exists():
        raise SystemExit(f"coverage test module is missing: {V451_TESTS}")
    tree = ast.parse(V451_TESTS.read_text(encoding="utf-8-sig"))
    return {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def main() -> int:
    authority = normalized_text(AUTHORITY)
    sections = authority_sections(authority)
    missing = sorted({item for values in PHASE_SECTIONS.values() for item in values} - set(sections))
    if missing:
        raise SystemExit(f"AGENTS authority sections are missing: {missing}")

    rendered = {key: body.strip() + "\n" for key, (_, body) in CONTRACTS.items()}
    validate_contracts(rendered)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    legacy_dir = OUTPUT / "legacy"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    for legacy_name in ("map_v4.md", "refinement_v4.md"):
        legacy_path = OUTPUT / legacy_name
        if legacy_path.exists():
            legacy_path.replace(legacy_dir / legacy_name)
    manifest: dict[str, Any] = {
        "pipelineVersion": pipeline_version(),
        "authority": AUTHORITY.name,
        "agentsSha256": hashlib.sha256(AUTHORITY.read_bytes()).hexdigest(),
        "generationMode": "AGENTS_SECTION_DERIVED_GROUND_TRUTH_V2",
        "contracts": {},
    }
    for key, (filename, _) in CONTRACTS.items():
        destination = OUTPUT / filename
        destination.write_text(rendered[key], encoding="utf-8", newline="\n")
        manifest["contracts"][key] = {
            "path": destination.relative_to(ROOT).as_posix(),
            "sha256": sha256_text(rendered[key]),
            "authoritySections": list(PHASE_SECTIONS[key]),
            "mode": "semantic-compaction-no-new-permissions",
        }

    evidence_by_section = {
        3: "objectiveFamily, dealingRange, protectedSwing",
        4: "rootBarId, displacementBarId, protectedSwing IDs and raw OHLC",
        5: "lineagePathOptions and parent-child raw OHLC",
        6: "touch, mature liquidity, sweep, CHoCH, execution IDs",
        7: "fresh FVG, causal OB, first-retest evidence",
        8: "entry, distal, spread, stops level, selected objective family member",
        10: "closed-M1 as-of clock and frozen event IDs",
        11: "complete order evidence record",
        12: "protocolPassed and violation reason",
        18: "family pages, ownerEpoch, lanes, latency and broker fields",
    }
    invariant_by_section = {
        3: "deterministic objective-family selection",
        4: "root structure-transfer and lifecycle validation",
        5: "causal lineage freeze and unresolved-lineage rejection",
        6: "post-touch ordered trigger chain",
        7: "causal structural SL, add-on disabled, and one physical execution ID",
        8: "risk geometry and exact liquidity TP",
        10: "future-hidden advance_closed_m1_bar",
        11: "order precondition completeness",
        12: "protocol violation excluded regardless of PnL",
        18: "exhaustive paging, 3R slots, latency and restart invariants",
    }
    ledger_by_section = {
        3: "objectiveFamilyId, selectedObjective, intermediateDelivery",
        4: "rootObBarId, displacementBarId, protectedSwingBarId",
        5: "refinementObBarIds, sourceFamilyKey",
        6: "childTouchAtUtc, sweepBarId, chochBreakBarId, executionObBarId",
        7: "executionModel, deliveryFvgBarId, executionSignalKey",
        8: "entry, stop, target, buffer, plannedR",
        10: "asOfUtc, lastClosedM1BarId, contentHash",
        11: "lastReauthorizedAtUtc, evidence IDs",
        12: "protocolPassed, terminalReason",
        18: "ownerEpoch, slotId, orderId, bookId, latency status",
    }
    coverage_test_by_section = {
        1: "test_active_contract_surface_and_agents_hash",
        2: "test_timeframe_and_future_bar_boundaries",
        3: "test_objective_family_scope_lifecycle",
        4: "test_displacement_episode_and_nonpivot_protected",
        5: "test_lineage_paging_roundtrip",
        6: "test_trigger_latency_and_through_delivery",
        7: "test_delivery_fvg_dedup_addon_reentry",
        8: "test_risk_slot_arbitration_and_geometry",
        9: "test_immediate_no_trade_contracts",
        10: "test_shared_advance_clock_and_restart",
        11: "test_ground_truth_independent_audits",
        12: "test_protocol_classification_taxonomy",
        14: "test_ground_truth_final_declaration_fields",
        15: "test_active_contract_surface_and_agents_hash",
        18: "test_live_backfill_buffer_and_fake_demo_router",
    }
    available_tests = executable_coverage_tests()
    section_lines = authority.splitlines()
    coverage_records: list[dict[str, Any]] = []
    for section_id, metadata in sorted(sections.items()):
        if section_id not in {item for values in PHASE_SECTIONS.values() for item in values}:
            continue
        body = section_lines[int(metadata["start"]):int(metadata["end"])]
        rules = [
            line.strip()[2:].strip()
            for line in body
            if line.strip().startswith("- ")
        ]
        if not rules:
            rules = [str(metadata["title"])]
        phases = [
            phase for phase, values in PHASE_SECTIONS.items()
            if section_id in values
        ]
        for index, rule in enumerate(rules, 1):
            coverage_records.append({
                "ruleId": f"S{section_id:02d}-R{index:03d}",
                "authoritySection": section_id,
                "authorityText": rule,
                "geminiContracts": phases,
                "packetEvidence": evidence_by_section.get(
                    section_id, "AGENTS authority text and supplied role IDs"
                ),
                "codeInvariant": invariant_by_section.get(
                    section_id, "fail-closed semantic contract validation"
                ),
                "testId": coverage_test_by_section[section_id],
                "ledgerFields": ledger_by_section.get(
                    section_id, "requestId, reason, evidence IDs"
                ),
            })

    missing_test_functions = sorted({
        str(item["testId"]) for item in coverage_records
    } - available_tests)
    if missing_test_functions:
        raise SystemExit(
            "coverage matrix references missing executable tests: "
            + ",".join(missing_test_functions)
        )

    coverage_lines = [
        "# AGENTS to Gemini Coverage Matrix",
        "",
        "| Rule | Gemini contract | Packet evidence | Code invariant | Test | Ledger fields |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in coverage_records:
        coverage_lines.append(
            f"| {record['ruleId']} | {', '.join(record['geminiContracts'])} | "
            f"{record['packetEvidence']} | {record['codeInvariant']} | "
            f"{record['testId']} | {record['ledgerFields']} |"
        )
    coverage = "\n".join(coverage_lines) + "\n"
    coverage_path = OUTPUT / "coverage_matrix.md"
    coverage_path.write_text(coverage, encoding="utf-8", newline="\n")
    manifest["coverageMatrix"] = {
        "path": coverage_path.relative_to(ROOT).as_posix(),
        "sha256": sha256_text(coverage),
    }
    coverage_json_path = OUTPUT / "coverage_matrix.json"
    coverage_json_path.write_text(
        json.dumps(coverage_records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    manifest["coverageMatrix"]["jsonPath"] = coverage_json_path.relative_to(ROOT).as_posix()
    manifest["coverageMatrix"]["jsonSha256"] = sha256_text(
        normalized_text(coverage_json_path)
    )

    manifest_path = OUTPUT / "v4_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"MENTOR_API_CONTRACTS_OK pipeline={manifest['pipelineVersion']} "
        f"contracts={len(CONTRACTS)} authority={manifest['agentsSha256'][:12]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
