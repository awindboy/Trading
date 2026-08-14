from __future__ import annotations

import argparse
from copy import deepcopy
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gemini_replay_provider import GeminiReplayError, generate_structured_decision
from scripts.manual_replay_provider import ManualReplayError, wait_for_manual_decision
from scripts.codex_replay_provider import CodexReplayError, generate_codex_decision
from scripts.mentor_replay_v4_core import (
    PIPELINE_VERSION,
    MarketData,
    V4ContractError,
    advance_pending,
    advance_position,
    advance_reaction_monitor,
    advance_source_upgrade_candidates,
    advance_trigger_watch,
    apply_source_upgrade,
    assert_runtime_invariants,
    build_map_packet,
    build_order,
    build_plan_packet,
    build_reaction_monitor,
    build_refinement_packet,
    build_trigger_packet,
    canonical_hash,
    delivery_replacement,
    discover_source_upgrade_candidates,
    external_authority_from_scenario,
    freeze_map,
    freeze_plan,
    freeze_refinement,
    freeze_trigger_watch,
    local_scenario_cancel_reason,
    map_opportunity_id,
    map_schema,
    mechanical_choch_break_candidates,
    mechanical_choch_reference_candidates,
    mechanical_m5_correction_swing_candidates,
    new_runtime,
    outermost_completed_sweep_events,
    parent_zone,
    parse_utc,
    plan_schema,
    refinement_schema,
    refresh_reaction_monitor,
    reset_terminal,
    should_reauthorize,
    split_bar_id,
    TIMEFRAME_SECONDS,
    trigger_watch_schema,
    utc_text,
    zone_distal_crossed,
    zone_touched,
)


SECRET = ROOT / "data" / "mentor_ai_replay_secret.json"
CONFIG_EXAMPLE = ROOT / "config" / "mentor_ai_replay.example.json"
RUN_ROOT = ROOT / "output" / "mentor_ai_replay_v4_runs"
FIXED_ROOT = ROOT / "output" / "mentor_ai_replay_v4_fixed_packets"
CACHE_ROOT = ROOT / "output" / "mentor_ai_replay_v4_cache"
CONTRACT_DIR = ROOT / "mentor_context_pack" / "api_contracts"
V4_MANIFEST = CONTRACT_DIR / "v4_manifest.json"
LEGACY_MANIFEST = ROOT / "config" / "mentor_ai_replay_v3_25_legacy_manifest.json"
RUNNER_PATH = Path(__file__).resolve()
CORE_PATH = ROOT / "scripts" / "mentor_replay_v4_core.py"
RENDERER_PATH = ROOT / "scripts" / "render_mentor_week_asof.py"
RUNTIME_AGENT_SECTIONS_BY_PHASE = {
    "MAP": frozenset({1, 2, 3, 4, 15}),
    "REFINEMENT": frozenset({1, 2, 3, 4, 5, 15}),
    "TRIGGER_WATCH": frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15}),
    "PLAN": frozenset({3, 4, 5, 15}),
}


DEFAULTS: dict[str, Any] = {
    "provider": "gemini",
    "model": "gemini-3.5-flash",
    "planModel": "gemini-3.5-flash-lite",
    "authorityPlanModel": "gemini-3.5-flash",
    "mapModel": "gemini-3.5-flash",
    "refinementModel": "gemini-3.5-flash",
    "triggerWatchModel": "gemini-3.5-flash",
    "geminiFallbackModel": "gemini-3.5-flash-lite",
    "planFallbackModel": "gemini-3.5-flash-lite",
    "authorityPlanFallbackModel": "",
    "triggerWatchFallbackModel": "",
    "codexModel": "gpt-5.6-sol",
    "codexReasoningEffort": "xhigh",
    "symbol": "GOLD",
    "dataset": "output/datasets/GOLD_M1_2023-12-01_2025-12-31.npz",
    "warmupStartUtc": "2025-05-01T00:00:00Z",
    "replayStartUtc": "2025-08-21T00:00:00Z",
    "replayEndUtc": "2025-08-22T00:00:00Z",
    "followThroughDays": 14,
    "point": 0.01,
    "brokerStopsLevelPrice": 0.0,
    "brokerSpecResolved": False,
    "maximumApiCallsPerRun": 80,
    "maximumTokensPerRun": 350000,
    "maximumPlanPromptBytes": 36000,
    "maximumMapPromptBytes": 32000,
    "maximumRefinementPromptBytes": 32000,
    "maximumTriggerWatchPromptBytes": 36000,
    "maximumSystemInstructionBytes": 65536,
    "planMaxOutputTokens": 12288,
    "mapMaxOutputTokens": 12288,
    "refinementMaxOutputTokens": 12288,
    "triggerWatchMaxOutputTokens": 12288,
    "planThinkingLevel": "medium",
    "authorityPlanThinkingLevel": "low",
    "mapThinkingLevel": "medium",
    "refinementThinkingLevel": "medium",
    "triggerWatchThinkingLevel": "medium",
    "geminiFallbackThinkingLevel": "low",
    "temperature": 0.1,
    "timeoutSeconds": 120,
    "codexTimeoutSeconds": 1800,
    "providerRetries": 2,
    "minimumCallIntervalSeconds": 0,
    "requireSolGate": True,
    "mapMediaResolution": "MEDIA_RESOLUTION_MEDIUM",
    "detailMediaResolution": "MEDIA_RESOLUTION_HIGH",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def plan_opportunity_records(packet: dict[str, Any]) -> list[dict[str, str]]:
    """Identify one stable opportunity per physical root-delivery family."""
    records: list[dict[str, str]] = []
    for family in packet.get("physicalLineageFamilies", []):
        root_id = str(family["rootBarId"])
        root_tf, _ = split_bar_id(root_id)
        displacement_id = str(family.get("initialDisplacementBarId", root_id))
        identity = str(family.get("familyId") or canonical_hash(
            {
                "direction": family["direction"],
                "rootBarId": root_id,
                "initialDisplacementBarId": displacement_id,
            }
        )[:12])
        records.append(
            {
                "opportunityId": identity,
                "rootTimeframe": root_tf,
                "rootBarId": root_id,
                "initialDisplacementBarId": displacement_id,
            }
        )
    unique = {item["opportunityId"]: item for item in records}
    return list(unique.values())


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    last_error: OSError | None = None
    for attempt in range(5):
        try:
            os.replace(temporary, path)
            return
        except OSError as exc:
            last_error = exc
            time.sleep(0.05 * (attempt + 1))
    temporary.unlink(missing_ok=True)
    raise OSError(f"could not atomically update {path}: {last_error}")


def load_secret() -> tuple[str, dict[str, Any]]:
    if not SECRET.exists():
        raise SystemExit("Gemini setup is missing. Run launchers/Gemini_Replay_Setup.cmd first.")
    raw = read_json(SECRET)
    stored = dict(raw.get("config", {}))
    config = {key: stored.get(key, default) for key, default in DEFAULTS.items()}
    for key in (
        "maximumMapPromptBytes", "maximumRefinementPromptBytes",
        "maximumTriggerWatchPromptBytes", "mapMaxOutputTokens",
        "refinementMaxOutputTokens", "triggerWatchMaxOutputTokens",
    ):
        config[key] = max(int(config[key]), int(DEFAULTS[key]))
    return str(raw.get("apiKey", "")).strip(), config


def save_secret(api_key: str, config: dict[str, Any]) -> None:
    SECRET.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(SECRET, {"apiKey": api_key.strip(), "config": config})


def dataset_path(config: dict[str, Any]) -> Path:
    path = Path(str(config["dataset"]))
    return path if path.is_absolute() else ROOT / path


def load_v4_contract(phase: str) -> tuple[str, dict[str, str]]:
    if not V4_MANIFEST.exists():
        raise V4ContractError("V4 contract manifest is missing")
    manifest = read_json(V4_MANIFEST)
    agents = ROOT / "AGENTS.md"
    if sha256_file(agents) != manifest.get("agentsSha256"):
        raise V4ContractError("AGENTS.md changed after the V4 contract was frozen")
    key_by_phase = {
        "MAP": "map",
        "REFINEMENT": "refinement",
        "PLAN": "plan",
        "TRIGGER_WATCH": "triggerWatch",
    }
    if phase not in key_by_phase:
        raise V4ContractError(f"unsupported contract phase: {phase}")
    key = key_by_phase[phase]
    item = manifest["contracts"][key]
    path = ROOT / item["path"]
    if sha256_file(path) != item["sha256"]:
        raise V4ContractError(f"V4 {phase} contract hash mismatch")
    return path.read_text(encoding="utf-8-sig"), {
        "agents": manifest["agentsSha256"], key: item["sha256"]
    }


def verify_legacy_manifest() -> None:
    if not LEGACY_MANIFEST.exists():
        raise V4ContractError("V3.25 legacy manifest is missing")
    manifest = read_json(LEGACY_MANIFEST)
    if manifest.get("status") != "READ_ONLY_LEGACY":
        raise V4ContractError("V3.25 legacy manifest is not read-only")
    for item in manifest.get("files", []):
        path = ROOT / item["path"]
        if not path.exists():
            raise V4ContractError(f"V3.25 legacy file is missing: {path}")
        if path.stat().st_size != int(item["bytes"]) or sha256_file(path) != item["sha256"]:
            raise V4ContractError(f"V3.25 legacy file changed after archival: {path}")


def runtime_agents_text(phase: str = "PLAN") -> str:
    allowed_sections = RUNTIME_AGENT_SECTIONS_BY_PHASE.get(phase)
    if allowed_sections is None:
        raise V4ContractError(f"unsupported AGENTS runtime phase: {phase}")
    lines = (ROOT / "AGENTS.md").read_text(encoding="utf-8-sig").splitlines()
    selected: list[str] = []
    section: int | None = None
    for line in lines:
        match = re.match(r"^##\s+(\d+)\.", line)
        if match:
            section = int(match.group(1))
        if section is None or section in allowed_sections:
            selected.append(line)
    return "\n".join(selected).rstrip()


def system_instruction_for(phase: str, contract: str) -> str:
    agents = runtime_agents_text(phase)
    phase_boundary = {
        "PLAN": (
            "PLAN freezes only the scenario prerequisites that AGENTS.md requires before M1 is inspected: "
            "objective, map/scope, dealing range, root OB, and causal child refinement. It does not "
            "authorize an order. Child contact, sweep, CHoCH, execution OB, entry, SL, and TP execution "
            "evidence are future stages, so their absence is expected and is not a NO_PLAN reason. "
            "An intact external owner permits an opposite-direction INTERNAL_ROTATION inside its dealing "
            "range; that rotation is not an EXTERNAL_REVERSAL and does not require an external protected-"
            "swing body break."
        ),
        "TRIGGER_WATCH": (
            "TRIGGER_WATCH is evaluated only after the engine has frozen a valid PLAN and observed the "
            "final child contact. Judge only the supplied post-contact reaction chain. Never replace the "
            "frozen owner or objective. A supplied sourceUpgradeSelectionId may replace the original source "
            "only when that later, already-touched root-to-child lineage explains the same owner and objective "
            "more precisely; otherwise return null."
        ),
        "MAP": "MAP freezes no child or M1 evidence.",
        "REFINEMENT": "REFINEMENT freezes no M1 evidence or order.",
    }[phase]
    return (
        "The AGENTS.md runtime rules below are the sole strategy authority. Follow them exactly. "
        "Date-specific regression evidence is intentionally absent to prevent future-data leakage. "
        f"The current decision phase is {phase}. Apply the phase contract after AGENTS.md; "
        "if the phase contract conflicts with AGENTS.md, AGENTS.md wins. "
        + phase_boundary
        + "\n\n"
        "[BEGIN AGENTS.md RUNTIME RULES]\n"
        + agents
        + "\n[END AGENTS.md RUNTIME RULES]\n\n"
        "[BEGIN PHASE CONTRACT]\n"
        + contract.rstrip()
        + "\n[END PHASE CONTRACT]"
    )


PLAN_MODEL_FAMILY_KEYS = (
    "familyId",
    "direction",
    "rootBarId",
    "initialDisplacementBarId",
    "rootLaterBodyInvalidated",
    "rootLaterDistalTouched",
    "rootLaterProximalTouched",
    "lineagePathOptions",
    "scenarioOptions",
)


def model_packet_for_phase(
    phase: str, packet: dict[str, Any]
) -> dict[str, Any]:
    """Remove redundant PLAN scaffolding without removing selectable semantics."""
    if phase != "PLAN":
        return packet
    families = []
    for family in packet.get("physicalLineageFamilies", []):
        compact = {
            key: family[key]
            for key in PLAN_MODEL_FAMILY_KEYS
            if key in family
        }
        compact["scenarioOptions"] = [
            {
                **option,
                "scopeOwnerRule": {
                    "EXTERNAL_CONTINUATION": "EC",
                    "INTERNAL_ROTATION": "IR",
                    "EXTERNAL_REVERSAL": "ER",
                }.get(str(option.get("scope", "")), "UNKNOWN"),
            }
            for option in family.get("scenarioOptions", [])
        ]
        families.append(compact)
    return {
        **packet,
        "physicalLineageFamilies": families,
        "scopeOwnerRuleLegend": {
            "EC": "must follow active owner",
            "IR": "may oppose active owner; no external break; first internal objective",
            "ER": "requires recorded H1/M30 owner break",
        },
        "modelPacketBoundary": (
            "Every selectable maximal lineage and scenario option is present. Raw root/child "
            "selection scaffolding duplicated by lineagePathOptions was removed only from this "
            "model view; the engine retains it for deterministic validation."
        ),
    }


def prompt_for(phase: str, packet: dict[str, Any]) -> str:
    if phase == "PLAN":
        instruction = (
            "Return only JSON matching the supplied response schema. Select one supplied scenarioSelectionId. "
            "Each option is an indivisible, engine-prevalidated combination of direction, scope, dealing range, "
            "objective, protected swing, complete maximal OB lineage, and intermediate liquidity. Judge whether "
            "the whole option is semantically the Mentor setup; never decompose or recombine it. Do not return "
            "bar IDs, prices, state, phase, as-of time, schedules, watch events, or order values."
        )
    elif phase == "TRIGGER_WATCH":
        instruction = (
            "Return only JSON matching the supplied response schema. Copy each chosen supplied barId "
            "directly into its named semantic role. Do not create selectedBarIds and do not use array "
            "indexes. Do not return state, phase, as-of time, prices, schedules, watch events, or order values."
        )
    else:
        instruction = (
            "Return only JSON matching the supplied response schema. Put each chosen listed barId once "
            "in selectedBarIds, then reference its zero-based array index for every semantic role. Do not "
            "return state, phase, as-of time, prices, schedules, watch events, or order values."
        )
    phase_checklist = {
        "MAP": (
            "\n[FINAL MAP CHECK BEFORE JSON]\n"
            "1. Use decisionReference.close for premium/discount.\n"
            "2. LONG means the selected objective candle HIGH; SHORT means its LOW.\n"
            "3. The objective must be a real, closed, unconsumed liquidity pool at this MAP decision. "
            "It may have been created by the selected root delivery before price returned to the root.\n"
            "4. The objective origin candle creates the liquidity; it does not sweep itself. "
            "Only later candles can consume it.\n"
            "5. INTERNAL_ROTATION may oppose the intact external owner and must end at the first mature internal liquidity.\n"
            "6. If no fresh root satisfies all checks, return NO_MAP instead of using an older attractive OB."
        ),
        "REFINEMENT": (
            "\n[FINAL REFINEMENT CHECK BEFORE JSON]\n"
            "Every child must explain the same price event and displacement lineage as the frozen root; "
            "price overlap alone is insufficient."
        ),
        "TRIGGER_WATCH": (
            "\n[FINAL TRIGGER CHECK BEFORE JSON]\n"
            "The selected liquidity must have matured before its later independent sweep and have a matching completed sweep. "
            "Choose one completed chain from chochBreakCandidates. Its M1 reference and M5 correction swing "
            "must govern the reaction; a micro M1 pivot that does not transfer M5 correction structure is invalid. "
            "Select sourceUpgradeSelectionId only for a touched later causal lineage that preserves the frozen "
            "owner and objective while providing a structurally tighter source; otherwise return null."
        ),
        "PLAN": (
            "\n[FINAL PLAN CHECK BEFORE JSON]\n"
            "1. Compare EXTERNAL_CONTINUATION, INTERNAL_ROTATION, and EXTERNAL_REVERSAL for every viable "
            "family before returning NO_PLAN. A failed continuation is not a reason to skip a valid internal rotation.\n"
            "2. Premium/discount entry permission is determined by the proximal boundary of the selected final "
            "child POI, not by decisionReference.close, and this half-range gate applies only to "
            "EXTERNAL_CONTINUATION. The decision close only describes current location.\n"
            "3. Freeze map, objective, root, and the complete causal child path in this one response.\n"
            "4. The objective must be closed and unconsumed at this decision; a continuation root delivery "
            "may have created that later swing before price returned to the root.\n"
            "5. A liquidity objective may also pre-exist the root displacement; do not discard a real unswept "
            "external or internal pool merely because it formed earlier.\n"
            "6. INTERNAL_ROTATION must label its first mature internal swing objective as INTERNAL_SWING, "
            "REACTION_TRAP, or RANGE_EDGE. EXTERNAL_SWING is reserved for an external objective.\n"
            "7. Every child must explain the same physical price event and delivery lineage as its parent; "
            "overlap alone is not causality.\n"
            "8. Select one scenarioSelectionId. Each supplied scenario is an indivisible engine-prevalidated "
            "structural combination, not a semantically authorized trade. Approve the whole option or reject it; never shorten, "
            "mix, or rewrite its fields.\n"
            "9. An opposite M15/M5 family inside the intact H1/M30 range can be the correction into the "
            "selected child. It is not an opposing owner without an H1/M30 protected-swing body break.\n"
            "10. If externalMapAuthority is present, it is the persisted external owner from an earlier "
            "approved MAP, not a candidate to reinterpret. Its ACTIVE direction, dealing range, protected "
            "swing, and objective remain binding across trade close, cancellation, and internal rotation. "
            "OBJECTIVE_REACHED permits only a new same-direction continuation map; BROKEN plus its exact "
            "bodyBreakBarId permits an opposite EXTERNAL_REVERSAL. If authority is absent, infer the owner "
            "from the closed HTF chart.\n"
            "11. Scope-owner audit: EXTERNAL_CONTINUATION follows the active owner; EXTERNAL_REVERSAL "
            "requires its recorded H1/M30 body break; INTERNAL_ROTATION may oppose the intact owner without "
            "an external break but must target the first internal liquidity inside the active range. Never "
            "reject INTERNAL_ROTATION merely for opposing the external owner.\n"
            "12. objectiveClassificationAndMaturity is PASS only when the objective type matches the selected "
            "scope and the exact liquidity is still live. INTERNAL_ROTATION cannot relabel an H1/M30 external "
            "wick represented on M15 as internal liquidity.\n"
            "13. Return PLAN only when all five semanticAudit verdicts are PASS. Otherwise return NO_PLAN with "
            "FAIL or UNRESOLVED verdicts. Do not infer M1 evidence or reject a complete PLAN because M1 is absent."
        ),
    }[phase]
    model_packet = model_packet_for_phase(phase, packet)
    return (
        f"[V4 {phase} REQUEST]\n{instruction}\n"
        + "The `bars` object is columnar; read each row using its `columns` list.\n\n[PACKET]\n"
        + json.dumps(model_packet, ensure_ascii=False, separators=(",", ":"))
        + phase_checklist
    )


def enforce_prompt_bound(prompt: str, config: dict[str, Any], phase: str) -> dict[str, int]:
    size = len(prompt.encode("utf-8"))
    key = {
        "MAP": "maximumMapPromptBytes",
        "REFINEMENT": "maximumRefinementPromptBytes",
        "PLAN": "maximumPlanPromptBytes",
        "TRIGGER_WATCH": "maximumTriggerWatchPromptBytes",
    }[phase]
    maximum = int(config[key])
    if size > maximum:
        raise V4ContractError(f"{phase} prompt is {size} bytes, above {key}={maximum}")
    return {"promptBytes": size, "maximumPromptBytes": maximum}


def enforce_system_instruction_bound(
    system_instruction: str,
    config: dict[str, Any],
) -> dict[str, int | str]:
    size = len(system_instruction.encode("utf-8"))
    maximum = int(
        config.get(
            "maximumSystemInstructionBytes",
            DEFAULTS["maximumSystemInstructionBytes"],
        )
    )
    if size > maximum:
        raise V4ContractError(
            f"system instruction is {size} bytes, above maximumSystemInstructionBytes={maximum}"
        )
    return {
        "systemInstructionBytes": size,
        "maximumSystemInstructionBytes": maximum,
        "systemInstructionSha256": hashlib.sha256(
            system_instruction.encode("utf-8")
        ).hexdigest(),
    }


def system_instruction_evidence(config: dict[str, Any]) -> dict[str, dict[str, int | str]]:
    evidence: dict[str, dict[str, int | str]] = {}
    for phase in ("PLAN", "TRIGGER_WATCH"):
        contract, _ = load_v4_contract(phase)
        evidence[phase] = enforce_system_instruction_bound(
            system_instruction_for(phase, contract), config
        )
        evidence[phase]["runtimeAgentSections"] = ",".join(
            str(item) for item in sorted(RUNTIME_AGENT_SECTIONS_BY_PHASE[phase])
        )
    return evidence


def enforce_gemini_schema_subset(schema: dict[str, Any]) -> None:
    supported = {
        "$id", "$defs", "$ref", "$anchor", "type", "format", "title", "description",
        "enum", "items", "prefixItems", "minItems", "maxItems", "minimum", "maximum",
        "anyOf", "oneOf", "properties", "additionalProperties", "required", "propertyOrdering",
    }

    def visit(node: Any, location: str) -> None:
        if not isinstance(node, dict):
            return
        unsupported = set(node) - supported
        if unsupported:
            names = ",".join(sorted(unsupported))
            raise V4ContractError(f"Gemini response schema uses unsupported keys at {location}: {names}")
        properties = node.get("properties", {})
        if isinstance(properties, dict):
            for name, child in properties.items():
                visit(child, f"{location}.properties.{name}")
        for key in ("items", "additionalProperties"):
            child = node.get(key)
            if isinstance(child, dict):
                visit(child, f"{location}.{key}")
        for key in ("prefixItems", "anyOf", "oneOf"):
            children = node.get(key, [])
            if isinstance(children, list):
                for index, child in enumerate(children):
                    visit(child, f"{location}.{key}[{index}]")

    visit(schema, "$")


def render_images(config: dict[str, Any], phase: str, as_of: int, output: Path) -> list[Path]:
    modes_by_phase = {
        "MAP": ("map",),
        "REFINEMENT": ("refinement",),
        "PLAN": ("plan",),
        "TRIGGER_WATCH": ("micro",),
    }
    modes = modes_by_phase[phase]
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for mode in modes:
        command = [
            sys.executable,
            str(ROOT / "scripts" / "render_mentor_week_asof.py"),
            "--cutoff", utc_text(as_of),
            "--mode", mode,
            "--dataset", str(dataset_path(config)),
            "--output", str(output),
            "--warmup", str(config["warmupStartUtc"]),
        ]
        if mode == "plan":
            command.extend(
                [
                    "--h1-count", "120",
                    "--m30-count", "72",
                    "--m15-count", "96",
                    "--m5-count", "120",
                ]
            )
        elif mode == "refinement":
            command.extend(
                [
                    "--m30-count", "48",
                    "--m15-count", "64",
                    "--m5-count", "96",
                ]
            )
        elif mode == "micro":
            command.extend(
                [
                    "--m15-count", "32",
                    "--m5-count", "48",
                    "--m1-count", "120",
                ]
            )
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        paths.append(Path(result.stdout.strip().splitlines()[-1]).resolve())
    return paths


@dataclass(frozen=True)
class ProviderResult:
    payload: dict[str, Any]
    usage: dict[str, int]
    model: str
    provider_calls: int


class ScriptedProvider:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.index = 0

    @classmethod
    def from_path(cls, path: Path) -> "ScriptedProvider":
        if path.suffix.lower() == ".jsonl":
            responses = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        else:
            value = read_json(path)
            responses = value if isinstance(value, list) else value["responses"]
        return cls(responses)

    def decide(self, **_: Any) -> ProviderResult:
        if self.index >= len(self.responses):
            raise V4ContractError("scripted provider response queue is exhausted")
        payload = self.responses[self.index]
        self.index += 1
        return ProviderResult(payload=payload, usage={"totalTokenCount": 0}, model="scripted", provider_calls=0)


class ManualProvider:
    def decide(
        self,
        *,
        request_dir: Path,
        prompt: str,
        system_instruction: str,
        images: list[Path],
        schema: dict[str, Any],
        **_: Any,
    ) -> ProviderResult:
        response = wait_for_manual_decision(
            request_dir=request_dir,
            prompt=(
                "[SYSTEM INSTRUCTION]\n"
                + system_instruction
                + "\n\n[USER REQUEST]\n"
                + prompt
            ),
            images=images,
            response_schema=schema,
        )
        return ProviderResult(response.payload, response.usage, response.model, 0)


def phase_model_key(phase: str) -> str:
    return {
        "MAP": "mapModel",
        "REFINEMENT": "refinementModel",
        "PLAN": "planModel",
        "TRIGGER_WATCH": "triggerWatchModel",
    }[phase]


def phase_output_key(phase: str) -> str:
    return {
        "MAP": "mapMaxOutputTokens",
        "REFINEMENT": "refinementMaxOutputTokens",
        "PLAN": "planMaxOutputTokens",
        "TRIGGER_WATCH": "triggerWatchMaxOutputTokens",
    }[phase]


def phase_thinking_key(phase: str) -> str:
    return {
        "MAP": "mapThinkingLevel",
        "REFINEMENT": "refinementThinkingLevel",
        "PLAN": "planThinkingLevel",
        "TRIGGER_WATCH": "triggerWatchThinkingLevel",
    }[phase]


def phase_fallback_model(config: dict[str, Any], phase: str) -> str:
    key = {
        "MAP": "mapFallbackModel",
        "REFINEMENT": "refinementFallbackModel",
        "PLAN": "planFallbackModel",
        "TRIGGER_WATCH": "triggerWatchFallbackModel",
    }[phase]
    phase_model = str(config.get(key, "")).strip()
    if phase_model:
        return phase_model
    return str(config.get("geminiFallbackModel", "")).strip()


def plan_requires_authority_model(packet: dict[str, Any]) -> bool:
    """Use Flash when PLAN contains owner or causal-refinement arbitration.

    Lite is safe only for an already frozen owner with one same-direction
    physical family and one unambiguous lineage path. Choosing between a broad
    parent and competing terminal children is part of the trading judgment,
    not a cheap navigation task.
    """
    authority = packet.get("externalMapAuthority")
    if not isinstance(authority, dict) or not authority.get("direction"):
        return True
    if str(authority.get("status", "ACTIVE")) == "BROKEN":
        return True
    authority_direction = str(authority["direction"]).upper()
    focused_ids = {str(item) for item in packet.get("focusedFamilyIds", [])}
    families = [
        item
        for item in packet.get("physicalLineageFamilies", [])
        if not focused_ids or str(item.get("familyId")) in focused_ids
    ]
    directions = {
        str(item.get("direction", "")).upper()
        for item in families
        if item.get("direction")
    }
    if not directions or any(
        direction != authority_direction for direction in directions
    ):
        return True
    if len(families) != 1:
        return True
    family = families[0]
    lineage_paths = list(family.get("lineagePathOptions", []))
    if len(lineage_paths) != 1:
        return True
    semantic_scopes = {
        str(option.get("scope", ""))
        for option in family.get("scenarioOptions", [])
        if option.get("scope")
    }
    return len(semantic_scopes) != 1


def routed_gemini_settings(
    config: dict[str, Any], phase: str, packet: dict[str, Any]
) -> tuple[str, str, str]:
    if phase == "PLAN" and plan_requires_authority_model(packet):
        return (
            str(config.get("authorityPlanModel", config["planModel"])),
            str(config.get("authorityPlanFallbackModel", "")).strip()
            or phase_fallback_model(config, "PLAN"),
            validate_thinking_level(
                config.get("authorityPlanThinkingLevel", "low"),
                "authorityPlanThinkingLevel",
            ),
        )
    return (
        str(config[phase_model_key(phase)]),
        phase_fallback_model(config, phase),
        validate_thinking_level(
            config.get(phase_thinking_key(phase), "low"),
            phase_thinking_key(phase),
        ),
    )


def validate_thinking_level(value: Any, key: str) -> str:
    normalized = str(value).strip().lower()
    if normalized not in {"minimal", "low", "medium", "high"}:
        raise V4ContractError(
            f"{key} must be one of minimal, low, medium, high"
        )
    return normalized


class GeminiProvider:
    def __init__(self, api_key: str, config: dict[str, Any]) -> None:
        self.api_key = api_key
        self.config = config
        self.last_call_at = 0.0
        self.last_attempt_count = 0
        self.quota_disabled_models: set[str] = set()

    @staticmethod
    def retryable(error: GeminiReplayError) -> bool:
        text = str(error)
        return bool(
            error.recoverable
            or re.search(r"Gemini HTTP (429|5\d\d)", text)
            or "request failed:" in text
        )

    @staticmethod
    def merge_usage(
        target: dict[str, int], source: dict[str, int]
    ) -> dict[str, int]:
        for key, value in source.items():
            target[key] = int(target.get(key, 0)) + int(value or 0)
        return target

    @staticmethod
    def retry_delay(error: GeminiReplayError, attempt: int) -> float:
        match = re.search(r"retry in ([0-9.]+)s", str(error), flags=re.IGNORECASE)
        return float(match.group(1)) + 0.5 if match else min(60.0, 2.0 ** attempt)

    def decide(
        self,
        *,
        phase: str,
        request_dir: Path,
        prompt: str,
        system_instruction: str,
        images: list[Path],
        schema: dict[str, Any],
        model_override: str | None = None,
        fallback_model_override: str | None = None,
        thinking_level_override: str | None = None,
        **_: Any,
    ) -> ProviderResult:
        self.last_attempt_count = 0
        primary_model = str(
            model_override or self.config[phase_model_key(phase)]
        )
        fallback_model = (
            str(fallback_model_override).strip()
            if fallback_model_override is not None
            else phase_fallback_model(self.config, phase)
        )
        configured_models = [primary_model]
        if fallback_model and fallback_model != primary_model:
            configured_models.append(fallback_model)
        models = [model for model in configured_models if model not in self.quota_disabled_models]
        if not models:
            raise GeminiReplayError(
                "all configured Gemini models are quota-disabled for this process",
                request_was_sent=False,
                recoverable=True,
            )
        skipped = [model for model in configured_models if model in self.quota_disabled_models]
        if skipped:
            print(
                f"[QUOTA CIRCUIT OPEN] phase={phase} skipped={','.join(skipped)} using={models[0]}",
                flush=True,
            )
        max_tokens = int(self.config[phase_output_key(phase)])
        resolutions = [
            str(
                self.config["mapMediaResolution"]
                if phase in {"MAP", "PLAN"}
                else self.config["detailMediaResolution"]
            )
        ] * len(images)
        retries = int(self.config.get("providerRetries", 2))
        calls = 0
        accumulated_usage: dict[str, int] = {}
        for model_index, model in enumerate(models):
            using_fallback = model != primary_model
            configured_thinking_level = validate_thinking_level(
                (
                    self.config.get("geminiFallbackThinkingLevel", "minimal")
                    if using_fallback
                    else thinking_level_override
                    if thinking_level_override is not None
                    else self.config.get(phase_thinking_key(phase), "low")
                ),
                "geminiFallbackThinkingLevel"
                if using_fallback
                else phase_thinking_key(phase),
            )
            model_slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", model)
            force_minimal_thinking = False
            for attempt in range(retries + 1):
                interval = float(self.config.get("minimumCallIntervalSeconds", 0))
                remaining = interval - (time.monotonic() - self.last_call_at)
                if remaining > 0:
                    time.sleep(remaining)
                try:
                    calls += 1
                    self.last_attempt_count = calls
                    response = generate_structured_decision(
                        api_key=self.api_key,
                        model=model,
                        prompt=prompt,
                        system_instruction=system_instruction,
                        images=images,
                        media_resolutions=resolutions,
                        schema=schema,
                        temperature=float(self.config.get("temperature", 0.1)),
                        max_output_tokens=max_tokens,
                        thinking_level=(
                            "minimal"
                            if force_minimal_thinking
                            else configured_thinking_level
                        ),
                        timeout_seconds=int(self.config.get("timeoutSeconds", 120)),
                        raw_response_path=(
                            request_dir / f"provider_raw_{model_slug}_attempt_{attempt + 1}.json"
                        ),
                    )
                    self.last_call_at = time.monotonic()
                    self.merge_usage(accumulated_usage, response.usage)
                    self.quota_disabled_models.discard(model)
                    return ProviderResult(
                        response.payload,
                        accumulated_usage,
                        response.model,
                        calls,
                    )
                except GeminiReplayError as exc:
                    self.last_call_at = time.monotonic()
                    self.merge_usage(accumulated_usage, exc.usage)
                    quota_error = "Gemini HTTP 429" in str(exc)
                    if quota_error and model_index + 1 < len(models):
                        self.quota_disabled_models.add(model)
                        print(
                            f"[MODEL FALLBACK] phase={phase} {model} -> {models[model_index + 1]} reason=HTTP_429",
                            flush=True,
                        )
                        break
                    retryable = self.retryable(exc)
                    if retryable and exc.recoverable:
                        force_minimal_thinking = True
                    if attempt >= retries or not retryable:
                        if model_index + 1 < len(models) and retryable:
                            if quota_error:
                                self.quota_disabled_models.add(model)
                            print(
                                f"[MODEL FALLBACK] phase={phase} {model} -> "
                                f"{models[model_index + 1]} reason=RECOVERABLE_RESPONSE",
                                flush=True,
                            )
                            break
                        raise GeminiReplayError(
                            str(exc),
                            usage=accumulated_usage,
                            request_was_sent=True,
                            provider_call_count=calls,
                            recoverable=bool(exc.recoverable or quota_error),
                        ) from exc
                    delay = self.retry_delay(exc, attempt)
                    print(
                        f"[PROVIDER RETRY] model={model} request={request_dir.name} "
                        f"wait={delay:.1f}s thinking="
                        f"{'minimal' if force_minimal_thinking else configured_thinking_level} "
                        f"reason={exc}",
                        flush=True,
                    )
                    time.sleep(delay)
        raise AssertionError("unreachable Gemini retry loop")


class CodexCliProvider:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def decide(
        self,
        *,
        request_dir: Path,
        prompt: str,
        system_instruction: str,
        images: list[Path],
        schema: dict[str, Any],
        **_: Any,
    ) -> ProviderResult:
        response = generate_codex_decision(
            request_dir=request_dir,
            prompt=(
                "[SYSTEM INSTRUCTION]\n"
                + system_instruction
                + "\n\n[USER REQUEST]\n"
                + prompt
            ),
            images=images,
            schema=schema,
            model=str(self.config.get("codexModel", "")).strip() or None,
            reasoning_effort=str(
                self.config.get("codexReasoningEffort", "xhigh")
            ).strip(),
            timeout_seconds=int(self.config.get("codexTimeoutSeconds", 1800)),
        )
        return ProviderResult(response.payload, response.usage, response.model, 0)


class HashLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.previous = "0" * 64
        self.sequence = 0
        if path.exists():
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("previousHash") != self.previous:
                    raise V4ContractError("decision ledger hash chain is broken")
                body = {key: value for key, value in row.items() if key != "recordHash"}
                expected = canonical_hash(body)
                if expected != row.get("recordHash"):
                    raise V4ContractError("decision ledger record hash is invalid")
                self.previous = expected
                self.sequence = int(row["sequence"])

    def append(self, event: str, as_of: int, state: str, details: dict[str, Any]) -> dict[str, Any]:
        self.sequence += 1
        body = {
            "pipelineVersion": PIPELINE_VERSION,
            "sequence": self.sequence,
            "event": event,
            "asOfUtc": utc_text(as_of),
            "state": state,
            "details": details,
            "previousHash": self.previous,
        }
        row = {**body, "recordHash": canonical_hash(body)}
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.previous = row["recordHash"]
        return row


class V4Runner:
    def __init__(
        self,
        *,
        config: dict[str, Any],
        market: MarketData,
        run_dir: Path,
        provider: Any,
        runtime: dict[str, Any],
    ) -> None:
        self.config = config
        self.market = market
        self.run_dir = run_dir
        self.provider = provider
        self.runtime = runtime
        self.ledger = HashLedger(run_dir / "decision_ledger.jsonl")
        self.stats = runtime.setdefault(
            "stats",
            {
                "semanticRequests": 0,
                "providerApiCalls": 0,
                "totalTokens": 0,
                "cacheHits": 0,
                "mapRequests": 0,
                "planRequests": 0,
                "authorityPlanRequests": 0,
                "litePlanRequests": 0,
                "refinementRequests": 0,
                "triggerWatchRequests": 0,
                "localReauthorizations": 0,
                "localSweepWakeups": 0,
                "localMapSkips": 0,
                "localMapDeferrals": 0,
                "activeZeroTokenBars": 0,
                "flatZeroTokenBars": 0,
                "flatPlanSchedulerChecks": 0,
                "flatPlanFingerprintSkips": 0,
                "flatPlanEmptySkips": 0,
                "flatPlanWakeups": 0,
                "flatPlanCandidateRefreshes": 0,
                "flatPlanCandidatesQueued": 0,
                "flatPlanApproachSkips": 0,
                "flatPlanExpiredCandidates": 0,
                "challengerPlanWakeups": 0,
                "scenariosParked": 0,
                "scenariosRestored": 0,
                "parkedScenariosDiscarded": 0,
                "parentApproachPrefetches": 0,
                "promptTokens": 0,
                "freshPromptTokens": 0,
                "cachedContentTokens": 0,
                "thoughtTokens": 0,
                "candidateTokens": 0,
                "effectiveTokens": 0,
                "providerLatencyMsTotal": 0,
                "providerLatencyMsMax": 0,
            },
        )
        for key in (
            "mapRequests", "planRequests", "authorityPlanRequests", "litePlanRequests",
            "refinementRequests", "triggerWatchRequests",
            "promptTokens", "cachedContentTokens", "thoughtTokens", "candidateTokens",
            "freshPromptTokens", "effectiveTokens",
            "localSweepWakeups",
            "localMapSkips",
            "localMapDeferrals",
            "activeZeroTokenBars",
            "flatZeroTokenBars",
            "flatPlanSchedulerChecks",
            "flatPlanFingerprintSkips",
            "flatPlanEmptySkips",
            "flatPlanWakeups",
            "flatPlanCandidateRefreshes",
            "flatPlanCandidatesQueued",
            "flatPlanApproachSkips",
            "flatPlanExpiredCandidates",
            "challengerPlanWakeups",
            "scenariosParked",
            "scenariosRestored",
            "parkedScenariosDiscarded",
            "providerLatencyMsTotal",
            "providerLatencyMsMax",
        ):
            self.stats.setdefault(key, 0)
        # Runtime statistics are cumulative across resumes. Operational limits
        # apply to this process invocation so a free-tier replay can pause and
        # continue on the next quota window without losing market state.
        self.segment_provider_call_base = int(self.stats["providerApiCalls"])
        self.segment_token_base = int(self.stats["totalTokens"])
        self.trades: list[dict[str, Any]] = []
        trades_path = run_dir / "trades.jsonl"
        if trades_path.exists():
            self.trades = [json.loads(line) for line in trades_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]

    def save(self) -> None:
        assert_runtime_invariants(self.runtime)
        atomic_json(self.run_dir / "state.json", self.runtime)

    def event(self, name: str, as_of: int, details: dict[str, Any]) -> None:
        self.ledger.append(name, as_of, self.runtime["state"], details)
        self.save()

    def _request(
        self,
        phase: str,
        as_of: int,
        packet: dict[str, Any],
        schema: dict[str, Any],
        images: list[Path],
        *,
        allow_plan_challenger: bool = False,
    ) -> tuple[dict[str, Any], str, bool]:
        from jsonschema import Draft202012Validator

        state = str(self.runtime["state"])
        if phase == "PLAN" and state != "FLAT" and not (
            allow_plan_challenger and state == "PLANNED"
        ):
            raise V4ContractError(f"PLAN API call is forbidden while state={state}")
        if phase == "TRIGGER_WATCH" and state != "REACTION_MONITOR":
            raise V4ContractError(
                f"TRIGGER_WATCH API call is forbidden while state={state}"
            )
        if state in {"PENDING", "FILLED"}:
            raise V4ContractError(f"semantic API call is forbidden while state={state}")

        contract, hashes = load_v4_contract(phase)
        system_instruction = system_instruction_for(phase, contract)
        prompt = prompt_for(phase, packet)
        system_metrics = enforce_system_instruction_bound(system_instruction, self.config)
        prompt_metrics = enforce_prompt_bound(prompt, self.config, phase)
        enforce_gemini_schema_subset(schema)
        image_evidence = [{"path": str(path), "sha256": sha256_file(path)} for path in images]
        selected_fallback_model: str | None = None
        thinking_level: str | None = None
        if isinstance(self.provider, CodexCliProvider):
            provider_model = str(self.config.get("codexModel", "codex-cli-default"))
        elif isinstance(self.provider, GeminiProvider):
            (
                provider_model,
                selected_fallback_model,
                thinking_level,
            ) = routed_gemini_settings(self.config, phase, packet)
        else:
            provider_model = type(self.provider).__name__
        max_output_tokens = int(self.config[phase_output_key(phase)])
        media_resolution = str(
            self.config.get("mapMediaResolution", DEFAULTS["mapMediaResolution"])
            if phase in {"MAP", "PLAN"}
            else self.config.get(
                "detailMediaResolution", DEFAULTS["detailMediaResolution"]
            )
        )
        request_body = {
            "pipelineVersion": PIPELINE_VERSION,
            "phase": phase,
            "provider": type(self.provider).__name__,
            "model": provider_model,
            "fallbackModel": (
                selected_fallback_model
                if isinstance(self.provider, GeminiProvider) else None
            ),
            "temperature": float(self.config.get("temperature", 0.1)),
            "maxOutputTokens": max_output_tokens,
            "thinkingLevel": thinking_level,
            "fallbackThinkingLevel": (
                validate_thinking_level(
                    self.config.get("geminiFallbackThinkingLevel", "minimal"),
                    "geminiFallbackThinkingLevel",
                )
                if isinstance(self.provider, GeminiProvider)
                else None
            ),
            "mediaResolution": media_resolution,
            "systemInstructionSha256": system_metrics["systemInstructionSha256"],
            "prompt": prompt,
            "schema": schema,
            "images": [{"sha256": item["sha256"]} for item in image_evidence],
            "contractHashes": hashes,
            "implementationHashes": {
                "runner": sha256_file(RUNNER_PATH),
                "core": sha256_file(CORE_PATH),
                "renderer": sha256_file(RENDERER_PATH),
            },
        }
        request_id = canonical_hash(request_body)
        request_dir = self.run_dir / "requests" / request_id
        cache_dir = CACHE_ROOT / request_id
        print(
            f"[DECISION REQUEST] phase={phase} asOf={utc_text(as_of)} "
            f"provider={type(self.provider).__name__} model={provider_model} "
            f"request={request_id[:12]}",
            flush=True,
        )
        request_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(
            request_dir / "request.json",
            {
                "requestId": request_id,
                "phase": phase,
                "asOfUtc": utc_text(as_of),
                "model": provider_model,
                "fallbackModel": selected_fallback_model,
                "promptMetrics": prompt_metrics,
                "systemInstructionMetrics": system_metrics,
                "images": image_evidence,
                "contractHashes": hashes,
                "implementationHashes": request_body["implementationHashes"],
                "thinkingLevel": thinking_level,
                "fallbackThinkingLevel": request_body["fallbackThinkingLevel"],
            },
        )
        (request_dir / "prompt.txt").write_bytes(prompt.encode("utf-8"))
        (request_dir / "system_instruction.txt").write_bytes(
            system_instruction.encode("utf-8")
        )
        atomic_json(request_dir / "response_schema.json", schema)

        cached = cache_dir / "response.json"
        shared_cache_enabled = isinstance(self.provider, (GeminiProvider, CodexCliProvider))
        cache_hit = shared_cache_enabled and cached.exists()
        provider_latency_ms = 0
        if cache_hit:
            print(f"[CACHE HIT] phase={phase} request={request_id[:12]}", flush=True)
            result_payload = read_json(cached)
            result = ProviderResult(
                payload=result_payload["payload"],
                usage=result_payload.get("usage", {"totalTokenCount": 0}),
                model=str(result_payload.get("model", "cache")),
                provider_calls=0,
            )
            self.stats["cacheHits"] += 1
        else:
            retry_reserve = 0
            if isinstance(self.provider, GeminiProvider):
                primary_model = provider_model
                fallback_model = str(selected_fallback_model or "")
                model_count = 1 + int(
                    bool(fallback_model and fallback_model != primary_model)
                )
                retry_reserve = (int(self.config.get("providerRetries", 2)) + 1) * model_count
            segment_calls = (
                int(self.stats["providerApiCalls"])
                - self.segment_provider_call_base
            )
            if segment_calls + retry_reserve > int(self.config["maximumApiCallsPerRun"]):
                raise V4ContractError("API_CALL_BUDGET_BEFORE_REQUEST")
            output_reserve = max_output_tokens
            input_bytes = int(prompt_metrics["promptBytes"]) + int(
                system_metrics["systemInstructionBytes"]
            )
            image_reserve_by_resolution = {
                "MEDIA_RESOLUTION_LOW": 2048,
                "MEDIA_RESOLUTION_MEDIUM": 4096,
                "MEDIA_RESOLUTION_HIGH": 6144,
                "MEDIA_RESOLUTION_ULTRA_HIGH": 8192,
            }
            image_reserve = image_reserve_by_resolution.get(
                media_resolution, 8192
            ) * len(images)
            token_reserve = (input_bytes + 3) // 4 + output_reserve + image_reserve
            segment_tokens = int(self.stats["totalTokens"]) - self.segment_token_base
            if segment_tokens + token_reserve > int(self.config["maximumTokensPerRun"]):
                raise V4ContractError("TOKEN_BUDGET_BEFORE_REQUEST")
            try:
                provider_started = time.perf_counter()
                result = self.provider.decide(
                    phase=phase,
                    request_dir=request_dir,
                    prompt=prompt,
                    system_instruction=system_instruction,
                    images=images,
                    schema=schema,
                    request_id=request_id,
                    model_override=provider_model,
                    fallback_model_override=selected_fallback_model,
                    thinking_level_override=thinking_level,
                )
                provider_latency_ms = int((time.perf_counter() - provider_started) * 1000)
            except GeminiReplayError as exc:
                provider_latency_ms = int((time.perf_counter() - provider_started) * 1000)
                self.stats["providerLatencyMsTotal"] += provider_latency_ms
                self.stats["providerLatencyMsMax"] = max(
                    int(self.stats["providerLatencyMsMax"]), provider_latency_ms
                )
                failed_calls = int(getattr(self.provider, "last_attempt_count", 0))
                self.stats["providerApiCalls"] += failed_calls
                self._accumulate_usage(exc.usage)
                self.event(
                    "PROVIDER_REQUEST_FAILED",
                    as_of,
                    {"requestId": request_id, "phase": phase, "providerCalls": failed_calls, "error": str(exc)},
                )
                raise
        errors = sorted(Draft202012Validator(schema).iter_errors(result.payload), key=lambda item: list(item.path))
        if errors:
            first = errors[0]
            location = "/".join(str(item) for item in first.absolute_path)
            raise V4ContractError(f"{phase} structured response is invalid at {location}: {first.message}")
        self.stats["semanticRequests"] += 1
        self.stats["providerApiCalls"] += int(result.provider_calls)
        self.stats["providerLatencyMsTotal"] += provider_latency_ms
        self.stats["providerLatencyMsMax"] = max(
            int(self.stats["providerLatencyMsMax"]), provider_latency_ms
        )
        if not cache_hit:
            self._accumulate_usage(result.usage)
        request_counter = {
            "MAP": "mapRequests",
            "PLAN": "planRequests",
            "REFINEMENT": "refinementRequests",
            "TRIGGER_WATCH": "triggerWatchRequests",
        }[phase]
        self.stats[request_counter] += 1
        if phase == "PLAN" and isinstance(self.provider, GeminiProvider):
            route_counter = (
                "authorityPlanRequests"
                if provider_model == str(self.config.get("authorityPlanModel", ""))
                and provider_model != str(self.config.get("planModel", ""))
                else "litePlanRequests"
            )
            self.stats[route_counter] += 1
        atomic_json(
            request_dir / "response.json",
            {
                "requestId": request_id,
                "payload": result.payload,
                "usage": result.usage,
                "model": result.model,
                "providerLatencyMs": provider_latency_ms,
            },
        )
        return result.payload, request_id, cache_hit

    def _accumulate_usage(self, usage: dict[str, int]) -> None:
        total = int(usage.get("totalTokenCount", 0))
        prompt = int(usage.get("promptTokenCount", 0))
        cached = int(usage.get("cachedContentTokenCount", 0))
        self.stats["totalTokens"] += total
        self.stats["promptTokens"] += prompt
        self.stats["cachedContentTokens"] += cached
        self.stats["freshPromptTokens"] += max(0, prompt - cached)
        self.stats["effectiveTokens"] += max(0, total - cached)
        self.stats["thoughtTokens"] += int(usage.get("thoughtsTokenCount", 0))
        self.stats["candidateTokens"] += int(
            usage.get("candidatesTokenCount", 0)
        )

    def segment_usage(self) -> dict[str, int]:
        return {
            "segmentProviderApiCalls": (
                int(self.stats["providerApiCalls"])
                - self.segment_provider_call_base
            ),
            "segmentTotalTokens": (
                int(self.stats["totalTokens"]) - self.segment_token_base
            ),
        }

    def promote_response_cache(self, request_id: str) -> None:
        if not isinstance(self.provider, (GeminiProvider, CodexCliProvider)):
            return
        source = self.run_dir / "requests" / request_id / "response.json"
        if not source.exists():
            raise V4ContractError(f"validated response is missing before cache promotion: {request_id}")
        destination = CACHE_ROOT / request_id / "response.json"
        if destination.exists():
            return
        atomic_json(destination, read_json(source))

    def request_map(self, as_of: int) -> None:
        packet = build_map_packet(self.market, as_of, str(self.config["symbol"]))
        opportunity_ids = [
            map_opportunity_id(item)
            for item in packet.get("mechanicalRootCandidates", [])
        ]
        seen = list(self.runtime.get("seenMapOpportunityIds", []))
        self.runtime["seenMapOpportunityIds"] = list(
            dict.fromkeys([*seen, *opportunity_ids])
        )[-2048:]
        request_output = self.run_dir / "charts" / utc_text(as_of).replace(":", "-") / "map"
        images = render_images(self.config, "MAP", as_of, request_output)
        payload, request_id, cache_hit = self._request(
            "MAP", as_of, packet, map_schema(packet), images
        )
        self.runtime["lastPlanH1Available"] = as_of
        self.event(
            "MAP_RESPONSE", as_of,
            {"requestId": request_id, "cacheHit": cache_hit, "payload": payload},
        )
        try:
            mapped = freeze_map(payload, self.market, as_of)
        except V4ContractError as exc:
            self.event(
                "MAP_SEMANTIC_REJECTED",
                as_of,
                {"requestId": request_id, "reason": str(exc)},
            )
            print(
                f"[MAP REJECTED] {utc_text(as_of)} {exc}",
                flush=True,
            )
            return
        self.promote_response_cache(request_id)
        if mapped is None:
            self.event(
                "MAP_NOT_ACCEPTED", as_of,
                {"action": payload["action"], "reason": payload["reason"]},
            )
            return
        self.runtime["state"] = "MAPPED"
        self.runtime["scenario"] = mapped
        self.runtime["apiCallsByMap"][mapped["mapHash"]] = 1
        self.event("MAP_FROZEN", as_of, {"map": mapped, "requestId": request_id})
        print(
            f"[MAP FROZEN] {utc_text(as_of)} {mapped['direction']} {mapped['scope']} "
            f"root={mapped['root']['obBarId']} objective={mapped['objective']['price']:.2f}",
            flush=True,
        )

    @staticmethod
    def flat_plan_fingerprint(packet: dict[str, Any]) -> str:
        """Hash market meaning, excluding the moving clock and rendered evidence."""
        return canonical_hash(
            {
                "externalMapAuthority": packet.get("externalMapAuthority"),
                "physicalLineageFamilies": packet.get("physicalLineageFamilies", []),
            }
        )

    @staticmethod
    def external_authority_key(authority: dict[str, Any] | None) -> str:
        """Return the stable semantic version of the persisted external map."""
        if authority is None:
            return "NO_EXTERNAL_AUTHORITY"
        return canonical_hash(
            {
                "direction": authority.get("direction"),
                "status": authority.get("status", "ACTIVE"),
                "dealingRange": authority.get("dealingRange"),
                "protectedSwing": authority.get("protectedSwing"),
                "objective": authority.get("objective"),
                "bodyBreakBarId": authority.get("bodyBreakBarId"),
                "objectiveReachedBarId": authority.get("objectiveReachedBarId"),
            }
        )[:16]

    def latest_m15_available(self, as_of: int) -> int | None:
        rows = self.market.bars("M15", as_of, 1)
        return int(rows[-1]["available"]) if rows else None

    def refresh_flat_plan_candidates(self, as_of: int) -> None:
        """Queue mechanical families locally without spending model tokens."""
        if self.runtime["state"] not in {"FLAT", "PLANNED"}:
            return
        latest_m15 = self.latest_m15_available(as_of)
        if latest_m15 is None:
            return
        if self.runtime.get("lastPlanCandidateRefreshM15") == latest_m15:
            return
        packet = build_plan_packet(
            self.market,
            as_of,
            str(self.config["symbol"]),
            external_authority=self.runtime.get("externalMapAuthority"),
        )
        self.runtime["lastPlanCandidateRefreshM15"] = latest_m15
        self.runtime["externalMapAuthority"] = packet.get("externalMapAuthority")
        authority_key = self.external_authority_key(
            self.runtime.get("externalMapAuthority")
        )
        queued = {
            str(item["familyId"]): item
            for item in self.runtime.get("flatPlanCandidates", [])
        }
        added = 0
        active_direction = (
            str(self.runtime["scenario"]["direction"])
            if self.runtime.get("scenario") is not None else None
        )
        for family in packet.get("physicalLineageFamilies", []):
            if active_direction is not None and str(family["direction"]) == active_direction:
                continue
            if any(
                bool(family.get(key))
                for key in (
                    "rootLaterBodyInvalidated",
                    "rootLaterDistalTouched",
                )
            ):
                continue
            family_id = str(family["familyId"])
            root = self.market.bar(str(family["rootBarId"]), as_of)
            displacement = self.market.bar(
                str(family["initialDisplacementBarId"]), as_of
            )
            if family_id not in queued:
                added += 1
            queued[family_id] = {
                "familyId": family_id,
                "direction": str(family["direction"]),
                "rootBarId": str(family["rootBarId"]),
                "initialDisplacementBarId": str(
                    family["initialDisplacementBarId"]
                ),
                "rootLow": float(root["low"]),
                "rootHigh": float(root["high"]),
                "displacementAvailable": int(displacement["available"]),
                "firstSeenAtUtc": queued.get(family_id, {}).get(
                    "firstSeenAtUtc", utc_text(as_of)
                ),
                "lastSeenAtUtc": utc_text(as_of),
                "authorityKeyAtDiscovery": authority_key,
            }
        candidates = sorted(
            queued.values(),
            key=lambda item: (
                int(item["displacementAvailable"]), str(item["familyId"])
            ),
        )[-2048:]
        self.runtime["flatPlanCandidates"] = candidates
        self.stats["flatPlanCandidateRefreshes"] += 1
        self.stats["flatPlanCandidatesQueued"] += added
        self.event(
            "LOCAL_PLAN_CANDIDATES_REFRESHED",
            as_of,
            {
                "newCandidates": added,
                "queuedCandidates": len(candidates),
                "authorityKey": authority_key,
                "apiCalled": False,
            },
        )

    def approaching_flat_family_ids(
        self, row: dict[str, Any]
    ) -> tuple[set[str], set[str]]:
        """Find untouched roots one root-height away and expire missed roots."""
        if self.runtime["state"] not in {"FLAT", "PLANNED"}:
            return set(), set()
        active_direction = (
            str(self.runtime["scenario"]["direction"])
            if self.runtime.get("scenario") is not None else None
        )
        authority_key = self.external_authority_key(
            self.runtime.get("externalMapAuthority")
        )
        evaluated = set(self.runtime.get("evaluatedPlanOpportunityKeys", []))
        approaching: set[str] = set()
        expired: set[str] = set()
        for candidate in self.runtime.get("flatPlanCandidates", []):
            family_id = str(candidate["familyId"])
            evaluation_key = f"{authority_key}:{family_id}"
            if evaluation_key in evaluated:
                continue
            if int(row["available"]) <= int(candidate["displacementAvailable"]):
                continue
            low = float(candidate["rootLow"])
            high = float(candidate["rootHigh"])
            height = max(high - low, float(self.market.point))
            direction = str(candidate["direction"])
            if active_direction is not None and direction == active_direction:
                continue
            if direction == "LONG":
                if float(row["close"]) < low or float(row["low"]) <= low:
                    expired.add(family_id)
                elif float(row["low"]) <= high + height:
                    approaching.add(family_id)
            else:
                if float(row["close"]) > high or float(row["high"]) >= high:
                    expired.add(family_id)
                elif float(row["high"]) >= low - height:
                    approaching.add(family_id)
        return approaching, expired

    def schedule_event_driven_flat_plan(
        self, row: dict[str, Any], *, api_allowed: bool = True
    ) -> bool:
        """Call PLAN only when an untouched queued root is actually approached."""
        if self.runtime["state"] not in {"FLAT", "PLANNED"}:
            return False
        challenger = self.runtime["state"] != "FLAT"
        self.refresh_flat_plan_candidates(int(row["available"]))
        approaching, expired = self.approaching_flat_family_ids(row)
        if expired:
            self.runtime["flatPlanCandidates"] = [
                item
                for item in self.runtime.get("flatPlanCandidates", [])
                if str(item["familyId"]) not in expired
            ]
            self.stats["flatPlanExpiredCandidates"] += len(expired)
            self.event(
                "LOCAL_PLAN_CANDIDATES_EXPIRED",
                int(row["available"]),
                {"familyIds": sorted(expired), "apiCalled": False},
            )
        if not approaching:
            self.stats["flatPlanApproachSkips"] += 1
            return False
        if not api_allowed:
            return False
        authority_key = self.external_authority_key(
            self.runtime.get("externalMapAuthority")
        )
        packet = build_plan_packet(
            self.market,
            int(row["available"]),
            str(self.config["symbol"]),
            focus_family_ids=approaching,
            external_authority=self.runtime.get("externalMapAuthority"),
        )
        if not packet.get("physicalLineageFamilies"):
            self.runtime["flatPlanCandidates"] = [
                item
                for item in self.runtime.get("flatPlanCandidates", [])
                if str(item["familyId"]) not in approaching
            ]
            self.stats["flatPlanExpiredCandidates"] += len(approaching)
            self.event(
                "LOCAL_ROOT_APPROACH_STALE",
                int(row["available"]),
                {"familyIds": sorted(approaching), "apiCalled": False},
            )
            return False
        fingerprint = canonical_hash(
            {
                "authorityKey": authority_key,
                "familyIds": sorted(approaching),
            }
        )
        self.stats["flatPlanWakeups"] += 1
        if challenger:
            self.stats["challengerPlanWakeups"] += 1
        self.event(
            "LOCAL_ROOT_APPROACH_PLAN_SCHEDULED",
            int(row["available"]),
            {
                "familyIds": sorted(approaching),
                "authorityKey": authority_key,
                "apiCalled": True,
            },
        )
        self.request_plan(
            int(row["available"]),
            packet=packet,
            plan_fingerprint=fingerprint,
            challenger=challenger,
        )
        return True

    def latest_h1_available(self, as_of: int) -> int | None:
        rows = self.market.bars("H1", as_of, 1)
        return int(rows[-1]["available"]) if rows else None

    def schedule_flat_plan(self, as_of: int, *, api_allowed: bool = True) -> bool:
        """Review the complete HTF map once per new H1 evidence set.

        PLAN is a map decision, not a root-proximity callback.  The model sees
        every currently viable family together and may freeze only one.  Once a
        scenario is active this scheduler is silent until local invalidation or
        trade completion returns the runtime to FLAT.
        """
        if self.runtime["state"] != "FLAT":
            return False
        self.stats["flatPlanSchedulerChecks"] += 1
        latest_h1_available = self.latest_h1_available(as_of)
        if latest_h1_available is None:
            return False
        if self.runtime.get("lastPlanH1Available") == latest_h1_available:
            self.stats["localMapSkips"] += 1
            return False
        if not api_allowed:
            return False
        packet = build_plan_packet(
            self.market,
            as_of,
            str(self.config["symbol"]),
            external_authority=self.runtime.get("externalMapAuthority"),
        )
        if not packet.get("physicalLineageFamilies"):
            self.runtime["lastPlanH1Available"] = latest_h1_available
            self.stats["flatPlanEmptySkips"] += 1
            self.event(
                "LOCAL_PLAN_SKIPPED_NO_FAMILY",
                as_of,
                {"apiCalled": False},
            )
            return False
        authority_key = self.external_authority_key(
            packet.get("externalMapAuthority")
        )
        evaluated_opportunities = set(
            self.runtime.get("evaluatedPlanOpportunityKeys", [])
        )
        opportunity_ids = {
            item["opportunityId"] for item in plan_opportunity_records(packet)
        }
        if opportunity_ids and all(
            f"{authority_key}:{opportunity_id}" in evaluated_opportunities
            for opportunity_id in opportunity_ids
        ):
            self.runtime["lastPlanH1Available"] = latest_h1_available
            self.stats["flatPlanFingerprintSkips"] += 1
            self.event(
                "LOCAL_PLAN_SKIPPED_NO_NEW_FAMILY",
                as_of,
                {
                    "authorityKey": authority_key,
                    "familyCount": len(opportunity_ids),
                    "apiCalled": False,
                },
            )
            return False
        fingerprint = self.flat_plan_fingerprint(packet)
        evaluated = set(self.runtime.get("evaluatedFlatPlanFingerprints", []))
        if fingerprint in evaluated:
            self.runtime["lastPlanH1Available"] = latest_h1_available
            self.runtime["lastFlatPlanFingerprint"] = fingerprint
            self.stats["flatPlanFingerprintSkips"] += 1
            self.event(
                "LOCAL_PLAN_SKIPPED_UNCHANGED",
                as_of,
                {"planFingerprint": fingerprint, "apiCalled": False},
            )
            return False
        self.stats["flatPlanWakeups"] += 1
        self.event(
            "LOCAL_PLAN_SCHEDULED",
            as_of,
            {
                "planFingerprint": fingerprint,
                "familyCount": len(packet["physicalLineageFamilies"]),
                "apiCalled": True,
            },
        )
        try:
            self.request_plan(as_of, packet=packet, plan_fingerprint=fingerprint)
        except Exception as exc:
            self.event(
                "LOCAL_PLAN_REQUEST_DEFERRED",
                as_of,
                {
                    "planFingerprint": fingerprint,
                    "reason": f"{type(exc).__name__}: {exc}",
                    "apiCalled": False,
                },
            )
            raise
        self.runtime["lastPlanH1Available"] = latest_h1_available
        return True

    def request_refinement(self, as_of: int) -> None:
        mapped = self.runtime["scenario"]
        packet = build_refinement_packet(
            self.market, as_of, str(self.config["symbol"]), mapped
        )
        request_output = (
            self.run_dir / "charts" / utc_text(as_of).replace(":", "-") / "refinement"
        )
        images = render_images(self.config, "REFINEMENT", as_of, request_output)
        payload, request_id, cache_hit = self._request(
            "REFINEMENT", as_of, packet, refinement_schema(packet), images
        )
        self.event(
            "REFINEMENT_RESPONSE", as_of,
            {"requestId": request_id, "cacheHit": cache_hit, "payload": payload},
        )
        try:
            scenario = freeze_refinement(
                payload, self.market, as_of, mapped,
                set(self.runtime["acceptedScenarioHashes"]),
            )
        except V4ContractError as exc:
            self.event(
                "REFINEMENT_SEMANTIC_REJECTED",
                as_of,
                {"requestId": request_id, "reason": str(exc)},
            )
            self.cancel(as_of, "REFINEMENT_SEMANTIC_REJECTED", {"reason": str(exc)})
            return
        self.promote_response_cache(request_id)
        if scenario is None:
            self.cancel(
                as_of, f"REFINEMENT_{payload['action']}", {"reason": payload["reason"]}
            )
            return
        self.runtime["state"] = "PLANNED"
        self.runtime["scenario"] = scenario
        self.runtime["externalMapAuthority"] = external_authority_from_scenario(
            scenario, self.runtime.get("externalMapAuthority")
        )
        self.runtime["acceptedScenarioHashes"].append(scenario["scenarioHash"])
        self.runtime["apiCallsByScenario"][scenario["scenarioHash"]] = 1
        self.event(
            "SCENARIO_PLANNED", as_of,
            {
                "scenario": scenario,
                "requestId": request_id,
                "externalMapAuthority": self.runtime.get("externalMapAuthority"),
            },
        )
        print(
            f"[REFINEMENT FROZEN] {utc_text(as_of)} root={scenario['root']['obBarId']} "
            f"child={scenario['finalChild']['obBarId']}",
            flush=True,
        )

    def request_plan(
        self,
        as_of: int,
        focus_family_ids: set[str] | None = None,
        *,
        packet: dict[str, Any] | None = None,
        plan_fingerprint: str | None = None,
        challenger: bool = False,
    ) -> None:
        prior = None
        if challenger:
            if self.runtime["state"] != "PLANNED":
                raise V4ContractError(
                    f"challenger PLAN requires a pre-order active scenario, got {self.runtime['state']}"
                )
            prior = {
                "state": str(self.runtime["state"]),
                "scenario": deepcopy(self.runtime["scenario"]),
                "reactionMonitor": deepcopy(self.runtime.get("reactionMonitor")),
                "externalMapAuthority": deepcopy(
                    self.runtime.get("externalMapAuthority")
                ),
            }
        packet = packet or build_plan_packet(
            self.market,
            as_of,
            str(self.config["symbol"]),
            focus_family_ids=focus_family_ids,
            external_authority=self.runtime.get("externalMapAuthority"),
        )
        if focus_family_ids is not None and not packet["physicalLineageFamilies"]:
            self.event(
                "LOCAL_ROOT_APPROACH_STALE",
                as_of,
                {"familyIds": sorted(focus_family_ids), "apiCalled": False},
            )
            return
        if plan_fingerprint is None:
            plan_fingerprint = self.flat_plan_fingerprint(packet)
        opportunity_ids = [
            item["opportunityId"] for item in plan_opportunity_records(packet)
        ]
        seen = list(self.runtime.get("seenPlanOpportunityIds", []))
        self.runtime["seenPlanOpportunityIds"] = list(
            dict.fromkeys([*seen, *opportunity_ids])
        )[-2048:]
        request_output = self.run_dir / "charts" / utc_text(as_of).replace(":", "-") / "plan"
        images = render_images(self.config, "PLAN", as_of, request_output)
        payload, request_id, cache_hit = self._request(
            "PLAN",
            as_of,
            packet,
            plan_schema(packet),
            images,
            allow_plan_challenger=challenger,
        )
        latest_h1_available = self.latest_h1_available(as_of)
        self.runtime["lastPlanH1Available"] = (
            latest_h1_available
            if latest_h1_available is not None
            else as_of
        )
        self.runtime["lastPlanRequestAtUtc"] = utc_text(as_of)
        self.runtime["lastPlanRequestH1Bucket"] = as_of - (as_of % 3600)
        self.runtime["lastFlatPlanFingerprint"] = plan_fingerprint
        evaluated = list(self.runtime.get("evaluatedFlatPlanFingerprints", []))
        self.runtime["evaluatedFlatPlanFingerprints"] = list(
            dict.fromkeys([*evaluated, plan_fingerprint])
        )[-2048:]
        authority_key = self.external_authority_key(
            packet.get("externalMapAuthority")
        )
        evaluated_opportunities = list(
            self.runtime.get("evaluatedPlanOpportunityKeys", [])
        )
        self.runtime["evaluatedPlanOpportunityKeys"] = list(
            dict.fromkeys(
                [
                    *evaluated_opportunities,
                    *(
                        f"{authority_key}:{opportunity_id}"
                        for opportunity_id in opportunity_ids
                    ),
                ]
            )
        )[-4096:]
        self.event("PLAN_RESPONSE", as_of, {"requestId": request_id, "cacheHit": cache_hit, "payload": payload})
        try:
            scenario = freeze_plan(
                payload,
                self.market,
                as_of,
                set(self.runtime["acceptedScenarioHashes"]),
                packet,
            )
        except V4ContractError as exc:
            self.event(
                "PLAN_SEMANTIC_REJECTED",
                as_of,
                {"requestId": request_id, "reason": str(exc)},
            )
            print(f"[PLAN REJECTED] {utc_text(as_of)} {exc}", flush=True)
            return
        self.promote_response_cache(request_id)
        if scenario is None:
            self.event("PLAN_NOT_ACCEPTED", as_of, {"action": payload["action"], "reason": payload["reason"]})
            return
        previous_authority = (
            packet.get("externalMapAuthority")
            if packet.get("externalMapAuthority") is not None
            else self.runtime.get("externalMapAuthority")
        )
        try:
            next_authority = external_authority_from_scenario(
                scenario, previous_authority
            )
        except V4ContractError as exc:
            self.event(
                "PLAN_AUTHORITY_REJECTED",
                as_of,
                {"requestId": request_id, "reason": str(exc)},
            )
            print(f"[PLAN AUTHORITY REJECTED] {utc_text(as_of)} {exc}", flush=True)
            return

        parked_scenario_hash: str | None = None
        replaced_scenario_hash: str | None = None
        if challenger and prior is not None:
            if scenario["scope"] == "EXTERNAL_REVERSAL":
                replaced_scenario_hash = str(
                    prior["scenario"]["scenarioHash"]
                )
            else:
                parked = {
                    "state": prior["state"],
                    "scenario": prior["scenario"],
                    "reactionMonitor": prior["reactionMonitor"],
                    "parkedAtUtc": utc_text(as_of),
                    "externalAuthorityKeyAtPark": self.external_authority_key(
                        prior["externalMapAuthority"]
                    ),
                    "externalAuthorityDirectionAtPark": (
                        prior["externalMapAuthority"].get("direction")
                        if prior["externalMapAuthority"] else None
                    ),
                }
                existing = {
                    str(item["scenario"]["scenarioHash"])
                    for item in self.runtime.get("parkedScenarios", [])
                }
                if str(prior["scenario"]["scenarioHash"]) not in existing:
                    self.runtime.setdefault("parkedScenarios", []).append(parked)
                    self.stats["scenariosParked"] += 1
                    parked_scenario_hash = str(
                        prior["scenario"]["scenarioHash"]
                    )

        self.runtime["state"] = "PLANNED"
        self.runtime["scenario"] = scenario
        self.runtime["reactionMonitor"] = None
        self.runtime["triggerWatch"] = None
        self.runtime["order"] = None
        self.runtime["position"] = None
        self.runtime["externalMapAuthority"] = next_authority
        self.runtime["acceptedScenarioHashes"].append(scenario["scenarioHash"])
        self.runtime["apiCallsByScenario"][scenario["scenarioHash"]] = 1
        if parked_scenario_hash is not None:
            self.event(
                "SCENARIO_PARKED",
                as_of,
                {
                    "scenarioHash": parked_scenario_hash,
                    "challengerScenarioHash": scenario["scenarioHash"],
                },
            )
        if replaced_scenario_hash is not None:
            self.event(
                "ACTIVE_SCENARIO_REPLACED_BY_EXTERNAL_REVERSAL",
                as_of,
                {
                    "replacedScenarioHash": replaced_scenario_hash,
                    "replacementScenarioHash": scenario["scenarioHash"],
                },
            )
        self.event(
            "CHALLENGER_SCENARIO_PLANNED" if challenger else "SCENARIO_PLANNED",
            as_of,
            {
                "scenario": scenario,
                "requestId": request_id,
                "externalMapAuthority": self.runtime.get("externalMapAuthority"),
            },
        )
        print(
            f"[PLAN ACCEPTED] {utc_text(as_of)} {scenario['direction']} {scenario['scope']} "
            f"root={scenario['root']['obBarId']} child={scenario['finalChild']['obBarId']} "
            f"objective={scenario['objective']['price']:.2f}",
            flush=True,
        )

    def request_trigger_watch(
        self,
        as_of: int,
        sweep_events: list[dict[str, Any]] | None = None,
        choch_candidates: list[dict[str, Any]] | None = None,
        correction_candidates: list[dict[str, Any]] | None = None,
        choch_break_candidates: list[dict[str, Any]] | None = None,
    ) -> None:
        scenario = self.runtime["scenario"]
        monitor = self.runtime.get("reactionMonitor") or {}
        packet = build_trigger_packet(
            self.market,
            as_of,
            str(self.config["symbol"]),
            scenario,
            sweep_events,
            monitor.get("candidates", []),
            choch_candidates,
            correction_candidates,
            choch_break_candidates,
        )
        request_output = self.run_dir / "charts" / utc_text(as_of).replace(":", "-") / "trigger"
        images = render_images(self.config, "TRIGGER_WATCH", as_of, request_output)
        payload, request_id, cache_hit = self._request(
            "TRIGGER_WATCH", as_of, packet, trigger_watch_schema(packet), images
        )
        self.event("TRIGGER_WATCH_RESPONSE", as_of, {"requestId": request_id, "cacheHit": cache_hit, "payload": payload})
        try:
            watch = freeze_trigger_watch(
                payload,
                self.market,
                as_of,
                scenario,
                sweep_events,
                monitor.get("candidates", []),
                choch_candidates,
                correction_candidates,
                choch_break_candidates,
            )
        except V4ContractError as exc:
            self.event(
                "TRIGGER_SEMANTIC_REJECTED",
                as_of,
                {"requestId": request_id, "reason": str(exc)},
            )
            self.cancel(as_of, "TRIGGER_SEMANTIC_REJECTED", {"reason": str(exc)})
            return
        self.promote_response_cache(request_id)
        if watch is None:
            self.cancel(as_of, f"TRIGGER_WATCH_{payload['action']}", {"reason": payload["reason"]})
            return
        apply_source_upgrade(scenario, watch)
        self.runtime["reactionMonitor"] = None
        self.runtime["triggerWatch"] = watch
        scenario_hash = scenario["scenarioHash"]
        self.runtime["apiCallsByScenario"][scenario_hash] = 2
        self.runtime["state"] = "TRIGGER_WATCH"
        self.event(
            "TRIGGER_WATCH_ARMED",
            as_of,
            {"scenarioHash": scenario_hash, "watch": watch, "requestId": request_id},
        )
        print(
            f"[TRIGGER WATCH] {utc_text(as_of)} liquidity={watch['matureLiquidity']['barId']} "
            f"chochRef={watch['chochReference']['barId']}",
            flush=True,
        )
        execution = watch.get("executionOb")
        break_bar = watch.get("chochBreak")
        if execution is None or break_bar is None:
            raise V4ContractError("TRIGGER_WATCH did not freeze a completed execution chain")
        order = build_order(
            self.market,
            scenario,
            watch,
            execution,
            break_bar,
            float(self.config["brokerStopsLevelPrice"]),
        )
        self.runtime["order"] = order
        self.runtime["state"] = "PENDING"
        self.event(
            "ORDER_CREATED",
            as_of,
            {
                "order": order,
                "triggerEvidence": {
                    "matureLiquidityBarId": watch["matureLiquidity"]["barId"],
                    "m5CorrectionSwingBarId": watch["m5CorrectionSwing"]["barId"],
                    "chochReferenceBarId": watch["chochReference"]["barId"],
                    "triggerProtectedSwingBarId": watch["triggerProtectedSwing"]["barId"],
                    "sweepBarId": watch["sweep"]["barId"],
                    "chochBreakBarId": break_bar["barId"],
                    "executionBarId": execution["barId"],
                },
            },
        )
        print(
            f"[ORDER] {utc_text(as_of)} {order['direction']} entry={order['entry']:.2f} "
            f"sl={order['stop']:.2f} tp={order['target']:.2f}",
            flush=True,
        )

    def parked_scenario_discard_reason(
        self, parked: dict[str, Any], as_of: int
    ) -> str | None:
        scenario = parked["scenario"]
        authority = self.runtime.get("externalMapAuthority")
        parked_authority_direction = parked.get("externalAuthorityDirectionAtPark")
        if (
            authority is not None
            and parked_authority_direction is not None
            and str(authority.get("direction")) != str(parked_authority_direction)
        ):
            return "EXTERNAL_OWNER_CHANGED_WHILE_PARKED"

        parked_at = parse_utc(str(parked["parkedAtUtc"]))
        for historical in self.market.between("M1", parked_at, as_of):
            reason = local_scenario_cancel_reason(
                self.market, scenario, historical, None
            )
            if reason:
                return f"{reason}_WHILE_PARKED"
            if zone_touched(historical, scenario["finalChild"]):
                return "FINAL_CHILD_CONTACT_PASSED_WHILE_PARKED"
        return None

    def restore_parked_scenario(self, as_of: int) -> bool:
        """Restore a still-pristine pre-order plan without another model call."""
        if self.runtime["state"] != "FLAT":
            raise V4ContractError("parked scenario restoration requires FLAT state")
        if not self.runtime.get("parkedScenarios"):
            return False

        authority_packet = build_plan_packet(
            self.market,
            as_of,
            str(self.config["symbol"]),
            external_authority=self.runtime.get("externalMapAuthority"),
        )
        self.runtime["externalMapAuthority"] = authority_packet.get(
            "externalMapAuthority"
        )
        while self.runtime.get("parkedScenarios"):
            parked = self.runtime["parkedScenarios"].pop()
            reason = self.parked_scenario_discard_reason(parked, as_of)
            if reason:
                self.stats["parkedScenariosDiscarded"] += 1
                self.event(
                    "PARKED_SCENARIO_DISCARDED",
                    as_of,
                    {
                        "scenarioHash": parked["scenario"]["scenarioHash"],
                        "reason": reason,
                        "apiCalled": False,
                    },
                )
                continue
            self.runtime["state"] = str(parked["state"])
            self.runtime["scenario"] = parked["scenario"]
            self.runtime["reactionMonitor"] = parked.get("reactionMonitor")
            self.runtime["triggerWatch"] = None
            self.runtime["order"] = None
            self.runtime["position"] = None
            stamp = utc_text(as_of)
            self.runtime["scenario"]["lastReauthorizedAtUtc"] = stamp
            self.stats["scenariosRestored"] += 1
            self.event(
                "SCENARIO_RESTORED",
                as_of,
                {
                    "scenarioHash": self.runtime["scenario"]["scenarioHash"],
                    "parkedAtUtc": parked["parkedAtUtc"],
                    "apiCalled": False,
                },
            )
            return True
        return False

    def cancel(self, as_of: int, reason: str, detail: dict[str, Any] | None = None) -> None:
        scenario_hash = self.runtime.get("scenario", {}).get("scenarioHash") if self.runtime.get("scenario") else None
        self.runtime["state"] = "CANCELED"
        self.event("SCENARIO_CANCELED", as_of, {"scenarioHash": scenario_hash, "reason": reason, **(detail or {})})
        print(f"[CANCELED] {utc_text(as_of)} {reason}", flush=True)
        self.runtime["terminalAtUtc"] = utc_text(as_of)
        self.runtime = reset_terminal(self.runtime, "CANCELED")
        self.restore_parked_scenario(as_of)
        self.save()

    def close(self, as_of: int, trade: dict[str, Any]) -> None:
        scenario = self.runtime["scenario"]
        enriched = {
            **trade,
            "tradeId": f"V4-{len(self.trades) + 1:04d}",
            "scope": scenario["scope"],
            "rootTf": scenario["root"]["tf"],
            "childTf": scenario["finalChild"]["tf"],
            "rootObBarId": scenario["root"]["obBarId"],
            "childObBarId": scenario["finalChild"]["obBarId"],
            "objectiveBarId": scenario["objective"]["barId"],
        }
        self.trades.append(enriched)
        with (self.run_dir / "trades.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(enriched, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.runtime["state"] = "CLOSED"
        self.event("TRADE_CLOSED", as_of, {"trade": enriched})
        print(
            f"[TRADE CLOSED] {enriched['tradeId']} {enriched['outcome']} {enriched['resultR']:+.2f}R",
            flush=True,
        )
        self.runtime["terminalAtUtc"] = utc_text(as_of)
        self.runtime = reset_terminal(self.runtime, "CLOSED")
        self.restore_parked_scenario(as_of)
        self.save()

    def local_reauthorize(self, row: dict[str, Any]) -> bool:
        if not should_reauthorize(row):
            return True
        reason = local_scenario_cancel_reason(
            self.market,
            self.runtime["scenario"],
            row,
            self.runtime.get("triggerWatch"),
        )
        if reason:
            self.cancel(row["available"], reason)
            return False
        if (
            row["available"] % TIMEFRAME_SECONDS["H1"] == 0
            and self.runtime["state"] in {"PLANNED", "REACTION_MONITOR"}
        ):
            existing = {
                item["selectionId"]
                for item in self.runtime["scenario"].get("sourceUpgradeCandidates", [])
            }
            discovered = [
                item for item in discover_source_upgrade_candidates(
                    self.market,
                    self.runtime["scenario"],
                    row["available"],
                    str(self.config["symbol"]),
                )
                if item["selectionId"] not in existing
            ]
            if discovered:
                self.runtime["scenario"].setdefault(
                    "sourceUpgradeCandidates", []
                ).extend(discovered)
                self.event(
                    "LOCAL_SOURCE_UPGRADE_CANDIDATES",
                    row["available"],
                    {
                        "selectionIds": [item["selectionId"] for item in discovered],
                        "apiCalled": False,
                    },
                )
        stamp = utc_text(row["available"])
        self.runtime["scenario"]["lastReauthorizedAtUtc"] = stamp
        if self.runtime.get("order"):
            self.runtime["order"]["lastReauthorizedAtUtc"] = stamp
        self.stats["localReauthorizations"] += 1
        identity = self.runtime["scenario"].get("scenarioHash") or self.runtime["scenario"].get("mapHash")
        self.event(
            "LOCAL_H1_M15_REAUTHORIZED",
            row["available"],
            {"scenarioOrMapHash": identity},
        )
        return True

    def arm_child_touch(self, row: dict[str, Any]) -> bool:
        """Consume a child-touch event once, including the bar that completed an API transition."""
        if self.runtime["state"] != "PLANNED":
            return False
        scenario = self.runtime["scenario"]
        child = scenario["finalChild"]
        if not zone_touched(row, child):
            return False
        if zone_distal_crossed(row, child, scenario["direction"], body=False):
            self.cancel(row["available"], "POI_FULLY_CONSUMED_ON_TOUCH")
            return True
        scenario["childTouchAtUtc"] = utc_text(row["available"])
        scenario["childTouchBarId"] = row["barId"]
        self.runtime["reactionMonitor"] = build_reaction_monitor(
            self.market, scenario, row["available"]
        )
        self.runtime["state"] = "REACTION_MONITOR"
        self.event(
            "FINAL_CHILD_TOUCHED",
            row["available"],
            {
                "childObBarId": child["obBarId"],
                "touchBarId": row["barId"],
                "localLiquidityCandidates": len(
                    self.runtime["reactionMonitor"]["candidates"]
                ),
                "apiCalled": False,
            },
        )
        return True

    def process_bar(self, row: dict[str, Any]) -> None:
        state = self.runtime["state"]
        if state == "FLAT":
            return
        scenario = self.runtime["scenario"]
        if state in {"PLANNED", "REACTION_MONITOR"}:
            touched_upgrades = advance_source_upgrade_candidates(scenario, row)
            if touched_upgrades:
                self.event(
                    "LOCAL_SOURCE_UPGRADE_TOUCHED",
                    row["available"],
                    {
                        "candidates": [
                            {
                                "selectionId": item["selectionId"],
                                "touchBarId": item["touchBarId"],
                            }
                            for item in touched_upgrades
                        ],
                        "apiCalled": False,
                    },
                )
        if state != "FILLED":
            reason = local_scenario_cancel_reason(self.market, scenario, row, self.runtime.get("triggerWatch"))
            if reason:
                self.cancel(row["available"], reason)
                return
            if not self.local_reauthorize(row):
                return

        if state == "MAPPED":
            root = scenario["root"]
            if zone_touched(row, root):
                scenario["rootApproachAtUtc"] = utc_text(row["available"])
                scenario["rootApproachBarId"] = row["barId"]
                self.event(
                    "ROOT_APPROACHED",
                    row["available"],
                    {"rootObBarId": root["obBarId"], "approachBarId": row["barId"]},
                )
                self.request_refinement(row["available"])
                if self.runtime["state"] == "PLANNED":
                    self.arm_child_touch(row)
            return

        if state == "PLANNED":
            parent = parent_zone(scenario)
            if not scenario["parentApproachPrepared"] and zone_touched(row, parent):
                scenario["parentApproachPrepared"] = True
                scenario["parentApproachAtUtc"] = utc_text(row["available"])
                output = self.run_dir / "prefetch" / utc_text(row["available"]).replace(":", "-")
                paths = render_images(self.config, "PLAN", row["available"], output)
                self.stats["parentApproachPrefetches"] += 1
                self.event(
                    "PARENT_APPROACH_PREFETCHED",
                    row["available"],
                    {"parentObBarId": parent["obBarId"], "images": [str(path) for path in paths], "apiCalled": False},
                )
            self.arm_child_touch(row)
            return

        if state == "REACTION_MONITOR":
            self.runtime["reactionMonitor"] = refresh_reaction_monitor(
                self.market,
                scenario,
                self.runtime["reactionMonitor"],
                row["time"],
            )
            monitor, sweep_events = advance_reaction_monitor(
                self.runtime["reactionMonitor"], row, scenario["direction"]
            )
            self.runtime["reactionMonitor"] = monitor
            if sweep_events:
                self.event(
                    "LOCAL_SWEEP_RECOVERY_DETECTED",
                    row["available"],
                    {"candidates": sweep_events, "apiCalled": False},
                )
            all_sweeps = outermost_completed_sweep_events(
                monitor.get("sweepEvents", [])
            )
            choch_candidates = mechanical_choch_reference_candidates(
                self.market, scenario, row["available"]
            )
            correction_candidates = mechanical_m5_correction_swing_candidates(
                self.market, scenario, row["available"]
            )
            choch_break_candidates = mechanical_choch_break_candidates(
                self.market,
                scenario,
                row["available"],
                all_sweeps,
                choch_candidates,
                correction_candidates,
            )
            if choch_break_candidates:
                self.stats["localSweepWakeups"] += 1
                self.event(
                    "LOCAL_TRIGGER_CONTEXT_READY",
                    row["available"],
                    {
                        "sweepCandidates": len(all_sweeps),
                        "chochReferenceCandidates": len(choch_candidates),
                        "m5CorrectionSwingCandidates": len(correction_candidates),
                        "chochBreakCandidates": len(choch_break_candidates),
                        "apiCalled": False,
                    },
                )
                self.request_trigger_watch(
                    row["available"],
                    all_sweeps,
                    choch_candidates,
                    correction_candidates,
                    choch_break_candidates,
                )
            return

        if state == "TRIGGER_WATCH":
            watch, order = advance_trigger_watch(
                self.market,
                scenario,
                self.runtime["triggerWatch"],
                row,
                float(self.config["brokerStopsLevelPrice"]),
            )
            self.runtime["triggerWatch"] = watch
            if order:
                self.runtime["order"] = order
                self.runtime["state"] = "PENDING"
                self.event(
                    "ORDER_CREATED",
                    row["available"],
                    {
                        "order": order,
                        "triggerEvidence": {
                            "matureLiquidityBarId": watch["matureLiquidity"]["barId"],
                            "m5CorrectionSwingBarId": watch["m5CorrectionSwing"]["barId"],
                            "chochReferenceBarId": watch["chochReference"]["barId"],
                            "triggerProtectedSwingBarId": watch["triggerProtectedSwing"]["barId"],
                            "sweepBarId": watch["sweep"]["barId"],
                            "chochBreakBarId": watch["chochBreak"]["barId"],
                            "executionBarId": watch["executionOb"]["barId"],
                        },
                        "apiCalled": False,
                    },
                )
                print(
                    f"[ORDER] {utc_text(row['available'])} {order['direction']} "
                    f"entry={order['entry']:.2f} sl={order['stop']:.2f} tp={order['target']:.2f}",
                    flush=True,
                )
            return

        if state == "PENDING":
            outcome, position = advance_pending(self.market, self.runtime["order"], row)
            if outcome == "CANCELED_OBJECTIVE_FIRST":
                self.cancel(row["available"], "OBJECTIVE_REACHED_BEFORE_FILL")
                return
            if outcome == "CANCELED_THROUGH_DELIVERY":
                self.cancel(row["available"], "THROUGH_DELIVERY")
                return
            if outcome == "CANCELED_EXECUTION_POI_CONSUMED":
                self.cancel(row["available"], "EXECUTION_POI_FULLY_CONSUMED")
                return
            if outcome == "FILLED":
                self.runtime["position"] = position
                self.runtime["state"] = "FILLED"
                self.event("ORDER_FILLED", row["available"], {"position": position})
                return
            replacement = delivery_replacement(
                self.market,
                scenario,
                self.runtime["triggerWatch"],
                self.runtime["order"],
                row,
                float(self.config["brokerStopsLevelPrice"]),
            )
            if replacement:
                previous_id = self.runtime["order"]["orderId"]
                self.runtime["order"] = replacement
                self.event(
                    "DELIVERY_FVG_ORDER_REPLACED",
                    row["available"],
                    {"canceledOrderId": previous_id, "replacement": replacement, "apiCalled": False},
                )
            return

        if state == "FILLED":
            trade = advance_position(self.market, self.runtime["position"], row)
            if trade:
                self.close(row["available"], trade)

    def run(self, replay_start: int, replay_end: int, follow_end: int) -> str:
        first = self.market.m1_index_at_or_after(replay_start)
        if self.runtime["cursor"] < first:
            self.runtime["cursor"] = first
        total = len(self.market.rates)
        while self.runtime["cursor"] < total:
            index = int(self.runtime["cursor"])
            row = self.market.m1_row(index)
            if row["time"] >= follow_end:
                break
            if row["time"] >= replay_end and self.runtime["state"] == "FLAT":
                break
            state_before = self.runtime["state"]
            semantic_before = int(self.stats["semanticRequests"])
            self.process_bar(row)
            if (
                self.runtime["state"] == "FLAT"
                and row["available"] < replay_end
            ):
                self.schedule_flat_plan(int(row["available"]))
            if int(self.stats["semanticRequests"]) == semantic_before:
                if state_before == "FLAT":
                    self.stats["flatZeroTokenBars"] += 1
                else:
                    self.stats["activeZeroTokenBars"] += 1
            self.runtime["cursor"] = index + 1
            if row["available"] % 3600 == 0:
                print(
                    f"[PROGRESS] {utc_text(row['available'])} state={self.runtime['state']} "
                    f"requests={self.stats['semanticRequests']} api={self.stats['providerApiCalls']} "
                    f"tokens={self.stats['totalTokens']} planSkips={self.stats['flatPlanFingerprintSkips']} "
                    f"zeroTokenBars={self.stats['flatZeroTokenBars'] + self.stats['activeZeroTokenBars']} "
                    f"trades={len(self.trades)}",
                    flush=True,
                )
                self.save()
        self.save()
        if self.runtime["state"] != "FLAT":
            return "FOLLOW_THROUGH_EXHAUSTED"
        return "COMPLETED"


def write_trades_csv(run_dir: Path, trades: list[dict[str, Any]]) -> None:
    fields = [
        "trade_id", "decision_at", "filled_at", "closed_at", "direction", "scope",
        "execution_model", "root_tf", "child_tf", "entry", "sl", "tp", "outcome", "r",
        "root_ob_bar_id", "child_ob_bar_id", "objective_bar_id",
    ]
    with (run_dir / "trades.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for trade in trades:
            writer.writerow(
                {
                    "trade_id": trade["tradeId"],
                    "decision_at": trade.get("entryAtUtc"),
                    "filled_at": trade.get("entryAtUtc"),
                    "closed_at": trade.get("exitAtUtc"),
                    "direction": str(trade["direction"]).lower(),
                    "scope": trade["scope"],
                    "execution_model": trade["model"],
                    "root_tf": trade["rootTf"],
                    "child_tf": trade["childTf"],
                    "entry": trade["entry"],
                    "sl": trade["stop"],
                    "tp": trade["target"],
                    "outcome": trade["outcome"],
                    "r": trade["resultR"],
                    "root_ob_bar_id": trade["rootObBarId"],
                    "child_ob_bar_id": trade["childObBarId"],
                    "objective_bar_id": trade["objectiveBarId"],
                }
            )


def setup(args: argparse.Namespace) -> int:
    _, old = load_secret() if SECRET.exists() else ("", {**DEFAULTS})
    config = {**DEFAULTS, **old}
    api_key = getpass.getpass("Gemini API key: ").strip()
    if not api_key:
        raise SystemExit("API key was not saved because it was empty")
    save_secret(api_key, config)
    print(f"V4 setup saved: {SECRET}")
    return 0


def preflight(_: argparse.Namespace) -> int:
    api_key, config = load_secret()
    errors: list[str] = []
    instructions: dict[str, dict[str, int | str]] = {}
    if config.get("provider", "gemini") == "gemini" and not api_key:
        errors.append("Gemini API key is empty")
    path = dataset_path(config)
    if not path.exists():
        errors.append(f"dataset is missing: {path}")
    if not bool(config.get("brokerSpecResolved")):
        errors.append("broker symbol specification is unresolved")
    try:
        instructions = system_instruction_evidence(config)
    except (OSError, KeyError, V4ContractError) as exc:
        errors.append(str(exc))
    try:
        verify_legacy_manifest()
    except (OSError, KeyError, V4ContractError) as exc:
        errors.append(str(exc))
    if errors:
        print("MENTOR_AI_REPLAY_V4_PREFLIGHT_FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("MENTOR_AI_REPLAY_V4_PREFLIGHT_OK")
    print(f"dataset={path}")
    print(f"period={config['replayStartUtc']}..{config['replayEndUtc']}")
    print(
        f"models=Gemini(PLAN={config['planModel']}, "
        f"AUTHORITY_PLAN={config['authorityPlanModel']}, "
        f"TRIGGER_WATCH={config['triggerWatchModel']}; "
        f"planFallback={config['planFallbackModel']}, "
        f"authorityFallback={config['authorityPlanFallbackModel']}, "
        f"triggerFallback={config['triggerWatchFallbackModel']}) "
        f"Codex({config['codexModel']})"
    )
    print(
        "thinkingLevels="
        f"PLAN:{config['planThinkingLevel']}, "
        f"AUTHORITY_PLAN:{config['authorityPlanThinkingLevel']}, "
        f"TRIGGER_WATCH:{config['triggerWatchThinkingLevel']}, "
        f"fallback:{config['geminiFallbackThinkingLevel']}"
    )
    print(
        "systemInstructions="
        + ", ".join(
            f"{phase}:{item['systemInstructionBytes']}B:{str(item['systemInstructionSha256'])[:12]}"
            for phase, item in instructions.items()
        )
    )
    return 0


def create_provider(args: argparse.Namespace, api_key: str, config: dict[str, Any]) -> Any:
    name = args.decision_provider or str(config.get("provider", "gemini"))
    if name == "gemini":
        return GeminiProvider(api_key, config)
    if name == "manual-codex":
        return ManualProvider()
    if name == "codex-cli":
        return CodexCliProvider(config)
    if name == "scripted":
        if not args.scripted_responses:
            raise V4ContractError("scripted provider requires --scripted-responses")
        return ScriptedProvider.from_path(args.scripted_responses)
    raise V4ContractError(f"unsupported provider: {name}")


def run_replay(args: argparse.Namespace) -> int:
    api_key, config = load_secret()
    run_id = args.run_id or f"mentor_v4_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    run_dir = RUN_ROOT / run_id
    diagnostic_ungated = bool(getattr(args, "diagnostic_bypass_sol_gate", False))
    if args.resume:
        if not (run_dir / "manifest.json").exists() or not (run_dir / "state.json").exists():
            raise V4ContractError(f"resume manifest/state is missing: {run_dir}")
        manifest = read_json(run_dir / "manifest.json")
        if manifest.get("pipelineVersion") != PIPELINE_VERSION:
            raise V4ContractError("resume source is not a V4 run")
        config = {**config, **dict(manifest["config"])}
        provider_name = str(manifest["decisionProvider"])
        validation_mode = str(manifest.get("validationMode", "SOL_GATED"))
        if args.decision_provider and args.decision_provider != provider_name:
            raise V4ContractError("resume cannot change the original decision provider")
        if (
            getattr(args, "dataset", None)
            or getattr(args, "warmup_start", None)
            or getattr(args, "follow_through_days", None) is not None
        ):
            raise V4ContractError(
                "resume cannot change the original dataset, warm-up start, or follow-through"
            )
        if getattr(args, "gemini_model", None):
            raise V4ContractError("resume cannot change the original Gemini model")
        if (
            getattr(args, "plan_model", None)
            or getattr(args, "authority_plan_model", None)
            or getattr(args, "trigger_watch_model", None)
        ):
            raise V4ContractError("resume cannot change phase-specific Gemini models")
        if getattr(args, "gemini_max_output_tokens", None):
            raise V4ContractError("resume cannot change the original Gemini output budget")
        if getattr(args, "gemini_thinking_level", None):
            raise V4ContractError("resume cannot change the original Gemini thinking level")
        if getattr(args, "gemini_media_resolution", None):
            raise V4ContractError("resume cannot change the original Gemini media resolution")
        if getattr(args, "codex_reasoning_effort", None):
            raise V4ContractError("resume cannot change the original Codex reasoning effort")
        if getattr(args, "maximum_tokens_per_run", None):
            raise V4ContractError("resume cannot change the original run token ceiling")
        if getattr(args, "maximum_api_calls_per_run", None):
            raise V4ContractError("resume cannot change the original run API-call ceiling")
        if diagnostic_ungated and validation_mode != "DIAGNOSTIC_UNGATED":
            raise V4ContractError("resume cannot change a gated run into DIAGNOSTIC_UNGATED")
        config["provider"] = provider_name
        if int(args.extend_follow_through_days) > 0:
            config["followThroughDays"] = int(config.get("followThroughDays", 14)) + int(args.extend_follow_through_days)
            manifest["config"] = config
            atomic_json(run_dir / "manifest.json", manifest)
    else:
        if getattr(args, "dataset", None):
            config["dataset"] = str(Path(args.dataset).resolve())
        if getattr(args, "warmup_start", None):
            config["warmupStartUtc"] = str(args.warmup_start)
        if getattr(args, "follow_through_days", None) is not None:
            if int(args.follow_through_days) < 0:
                raise V4ContractError("--follow-through-days cannot be negative")
            config["followThroughDays"] = int(args.follow_through_days)
        if args.start:
            config["replayStartUtc"] = args.start
        if args.end:
            config["replayEndUtc"] = args.end
        if args.benchmark_truth:
            config["benchmarkTruth"] = str(args.benchmark_truth)
        provider_name = args.decision_provider or str(config.get("provider", "gemini"))
        if getattr(args, "gemini_model", None):
            if provider_name != "gemini":
                raise V4ContractError("--gemini-model is only valid for Gemini runs")
            config["model"] = str(args.gemini_model)
            config["planModel"] = str(args.gemini_model)
            config["authorityPlanModel"] = str(args.gemini_model)
            config["mapModel"] = str(args.gemini_model)
            config["refinementModel"] = str(args.gemini_model)
            config["triggerWatchModel"] = str(args.gemini_model)
        if (
            getattr(args, "plan_model", None)
            or getattr(args, "authority_plan_model", None)
            or getattr(args, "trigger_watch_model", None)
        ):
            if provider_name != "gemini":
                raise V4ContractError("phase-specific models are only valid for Gemini runs")
            if getattr(args, "plan_model", None):
                config["planModel"] = str(args.plan_model)
            if getattr(args, "authority_plan_model", None):
                config["authorityPlanModel"] = str(args.authority_plan_model)
            if getattr(args, "trigger_watch_model", None):
                config["triggerWatchModel"] = str(args.trigger_watch_model)
        if getattr(args, "gemini_max_output_tokens", None):
            if provider_name != "gemini":
                raise V4ContractError("--gemini-max-output-tokens is only valid for Gemini runs")
            output_budget = int(args.gemini_max_output_tokens)
            if output_budget < 256:
                raise V4ContractError("--gemini-max-output-tokens must be at least 256")
            config["planMaxOutputTokens"] = output_budget
            config["mapMaxOutputTokens"] = output_budget
            config["refinementMaxOutputTokens"] = output_budget
            config["triggerWatchMaxOutputTokens"] = output_budget
        if getattr(args, "gemini_thinking_level", None):
            if provider_name != "gemini":
                raise V4ContractError("--gemini-thinking-level is only valid for Gemini runs")
            thinking_level = validate_thinking_level(
                args.gemini_thinking_level, "--gemini-thinking-level"
            )
            config["planThinkingLevel"] = thinking_level
            config["mapThinkingLevel"] = thinking_level
            config["refinementThinkingLevel"] = thinking_level
            config["triggerWatchThinkingLevel"] = thinking_level
        if getattr(args, "gemini_media_resolution", None):
            if provider_name != "gemini":
                raise V4ContractError("--gemini-media-resolution is only valid for Gemini runs")
            config["mapMediaResolution"] = str(args.gemini_media_resolution)
            config["detailMediaResolution"] = str(args.gemini_media_resolution)
        if getattr(args, "codex_reasoning_effort", None):
            if provider_name not in {"codex-cli", "manual-codex"}:
                raise V4ContractError(
                    "--codex-reasoning-effort is only valid for Codex runs"
                )
            config["codexReasoningEffort"] = str(args.codex_reasoning_effort)
        if getattr(args, "maximum_tokens_per_run", None):
            run_token_ceiling = int(args.maximum_tokens_per_run)
            if run_token_ceiling < 50000:
                raise V4ContractError(
                    "--maximum-tokens-per-run must be at least 50000"
                )
            config["maximumTokensPerRun"] = run_token_ceiling
        if getattr(args, "maximum_api_calls_per_run", None):
            run_call_ceiling = int(args.maximum_api_calls_per_run)
            if run_call_ceiling < 1:
                raise V4ContractError(
                    "--maximum-api-calls-per-run must be at least 1"
                )
            config["maximumApiCallsPerRun"] = run_call_ceiling
        if diagnostic_ungated and provider_name != "gemini":
            raise V4ContractError("--diagnostic-bypass-sol-gate is only valid for Gemini runs")
        if diagnostic_ungated:
            validation_mode = "DIAGNOSTIC_UNGATED"
        elif provider_name == "gemini":
            validation_mode = "SOL_GATED"
        elif provider_name in {"manual-codex", "codex-cli"}:
            validation_mode = "SOL_VALIDATION"
        else:
            validation_mode = "SCRIPTED_TEST"
    start = parse_utc(str(config["replayStartUtc"]))
    end = parse_utc(str(config["replayEndUtc"]))
    if start >= end:
        raise V4ContractError("replayStartUtc must be earlier than replayEndUtc")
    follow_end = end + int(config.get("followThroughDays", 14)) * 86400
    path = dataset_path(config)
    instructions = system_instruction_evidence(config)
    instructions_sha256 = canonical_hash(instructions)
    if args.resume:
        resume_identity = {
            "agentsSha256": sha256_file(ROOT / "AGENTS.md"),
            "contractsManifestSha256": sha256_file(V4_MANIFEST),
            "runnerSha256": sha256_file(RUNNER_PATH),
            "coreSha256": sha256_file(CORE_PATH),
            "rendererSha256": sha256_file(RENDERER_PATH),
            "systemInstructionsSha256": instructions_sha256,
        }
        if any(manifest.get(key) != value for key, value in resume_identity.items()):
            raise V4ContractError("resume source was created by different V4 rules, contracts, or code")
        if manifest.get("dataset", {}).get("sha256") != sha256_file(path):
            raise V4ContractError("resume dataset changed after the run was created")
    if validation_mode == "DIAGNOSTIC_UNGATED":
        print(
            "[WARNING] DIAGNOSTIC_UNGATED: Sol gate bypassed explicitly; "
            "this run cannot establish reproducibility.",
            flush=True,
        )
    if (
        provider_name == "gemini"
        and bool(config.get("requireSolGate", True))
        and validation_mode != "DIAGNOSTIC_UNGATED"
    ):
        gate_path = ROOT / "output" / "mentor_ai_replay_v4_validation" / "sol_gate.json"
        if not gate_path.exists():
            raise V4ContractError("SOL_VALIDATION_GATE_MISSING: run the identical period with codex-cli/manual-codex first")
        gate = read_json(gate_path)
        expected_gate = {
            "pipelineVersion": PIPELINE_VERSION,
            "datasetSha256": sha256_file(path),
            "agentsSha256": sha256_file(ROOT / "AGENTS.md"),
            "contractsManifestSha256": sha256_file(V4_MANIFEST),
            "runnerSha256": sha256_file(RUNNER_PATH),
            "coreSha256": sha256_file(CORE_PATH),
            "rendererSha256": sha256_file(RENDERER_PATH),
            "systemInstructionsSha256": instructions_sha256,
            "replayStartUtc": utc_text(start),
            "replayEndUtc": utc_text(end),
        }
        if any(gate.get(key) != value for key, value in expected_gate.items()):
            raise V4ContractError("SOL_VALIDATION_GATE_MISMATCH: dataset, rules, or period changed")
        benchmark_value = config.get("benchmarkTruth")
        if not benchmark_value:
            raise V4ContractError("Gemini replay requires --benchmark-truth for Sol gate binding")
        benchmark_path = Path(str(benchmark_value))
        if not benchmark_path.is_absolute():
            benchmark_path = ROOT / benchmark_path
        if not benchmark_path.exists() or gate.get("truthSha256") != sha256_file(benchmark_path):
            raise V4ContractError("SOL_VALIDATION_GATE_TRUTH_MISMATCH: benchmark changed or was not gated")
    market = MarketData.from_npz(
        path,
        parse_utc(str(config["warmupStartUtc"])),
        follow_end,
        float(config["point"]),
    )
    if args.resume:
        runtime = read_json(run_dir / "state.json")
        if runtime.get("nonResumableReason"):
            raise V4ContractError(f"run is sealed as non-resumable: {runtime['nonResumableReason']}")
    else:
        if run_dir.exists() and any(run_dir.iterdir()):
            raise V4ContractError(f"run directory already exists: {run_dir}")
        run_dir.mkdir(parents=True, exist_ok=True)
        runtime = new_runtime(market.m1_index_at_or_after(start))
        atomic_json(
            run_dir / "manifest.json",
            {
                "pipelineVersion": PIPELINE_VERSION,
                "runId": run_id,
                "decisionProvider": provider_name,
                "validationMode": validation_mode,
                "createdAtUtc": utc_text(int(datetime.now(timezone.utc).timestamp())),
                "config": {key: value for key, value in config.items() if key != "apiKey"},
                "dataset": {"path": str(path), "sha256": sha256_file(path)},
                "agentsSha256": sha256_file(ROOT / "AGENTS.md"),
                "contractsManifestSha256": sha256_file(V4_MANIFEST),
                "systemInstructions": instructions,
                "systemInstructionsSha256": instructions_sha256,
                "runnerSha256": sha256_file(RUNNER_PATH),
                "coreSha256": sha256_file(CORE_PATH),
                "rendererSha256": sha256_file(RENDERER_PATH),
                "legacyManifest": str(LEGACY_MANIFEST),
            },
        )
    provider = create_provider(args, api_key, config)
    runner = V4Runner(config=config, market=market, run_dir=run_dir, provider=provider, runtime=runtime)
    stopped_reason = "COMPLETED"
    error: str | None = None
    resumable_pause = False
    try:
        stopped_reason = runner.run(start, end, follow_end)
    except (
        GeminiReplayError, ManualReplayError, CodexReplayError, V4ContractError,
        OSError, subprocess.CalledProcessError,
    ) as exc:
        stopped_reason = type(exc).__name__
        error = str(exc)
        retryable_provider_failure = isinstance(exc, GeminiReplayError) and GeminiProvider.retryable(exc)
        resumable_pause = (
            retryable_provider_failure
            or (
                isinstance(exc, V4ContractError)
                and str(exc) in {
                    "API_CALL_BUDGET_BEFORE_REQUEST",
                    "TOKEN_BUDGET_BEFORE_REQUEST",
                }
            )
        )
        if not resumable_pause:
            runner.runtime["nonResumableReason"] = f"{type(exc).__name__}: {exc}"
        runner.save()
        print(f"[V4 STOP] {type(exc).__name__}: {exc}", flush=True)
    write_trades_csv(run_dir, runner.trades)
    completed = stopped_reason == "COMPLETED"
    summary = {
        "runId": run_id,
        "pipelineVersion": PIPELINE_VERSION,
        "validationMode": validation_mode,
        "completed": completed,
        "stoppedReason": stopped_reason,
        "error": error,
        **runner.stats,
        **runner.segment_usage(),
        "trades": len(runner.trades),
        "totalR": sum(float(item["resultR"]) for item in runner.trades),
        "state": runner.runtime["state"],
        "nonResumableReason": runner.runtime.get("nonResumableReason"),
        "resumable": bool(not completed and resumable_pause),
    }
    atomic_json(run_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    print(run_dir, flush=True)
    return 0 if completed else 2


def latest_resume_source(_: argparse.Namespace) -> int:
    candidates = sorted(
        (path for path in RUN_ROOT.glob("*") if (path / "state.json").exists()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        summary = read_json(path / "summary.json") if (path / "summary.json").exists() else {}
        state = read_json(path / "state.json")
        if not summary.get("completed", False) and not state.get("nonResumableReason"):
            print(path.name)
            return 0
    return 2


def rejudge_exact_source_request(
    *,
    source_run: Path,
    run_dir: Path,
    phase: str,
    as_of: int,
    provider: Any,
    refresh_current_contract: bool = False,
) -> int:
    """Rejudge the exact model-visible evidence from a prior run.

    This deliberately does not rebuild a market packet: rebuilding can change
    persisted owner authority or option enumeration and invalidates a model
    comparison. The prior response is never loaded into the new provider call.
    """
    from jsonschema import Draft202012Validator

    ledger_path = source_run / "decision_ledger.jsonl"
    if not ledger_path.exists():
        raise V4ContractError(f"source run has no decision ledger: {source_run}")
    response_event = f"{phase}_RESPONSE"
    matches = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    matches = [
        row for row in matches
        if row.get("event") == response_event and row.get("asOfUtc") == utc_text(as_of)
    ]
    if len(matches) != 1:
        raise V4ContractError(
            f"source run must contain exactly one {response_event} at {utc_text(as_of)}"
        )
    source_request_id = str(matches[0]["details"]["requestId"])
    source_request_dir = source_run / "requests" / source_request_id
    required = (
        source_request_dir / "prompt.txt",
        source_request_dir / "system_instruction.txt",
        source_request_dir / "response_schema.json",
        source_request_dir / "request.json",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise V4ContractError("source request evidence is incomplete: " + ",".join(missing))
    prompt = required[0].read_text(encoding="utf-8-sig")
    system_instruction = required[1].read_text(encoding="utf-8-sig")
    schema = read_json(required[2])
    if refresh_current_contract:
        marker = "[PACKET]\n"
        if marker not in prompt:
            raise V4ContractError("source prompt has no model packet marker")
        raw_packet = prompt.split(marker, 1)[1].lstrip()
        try:
            packet, _ = json.JSONDecoder().raw_decode(raw_packet)
        except json.JSONDecodeError as exc:
            raise V4ContractError("source model packet cannot be decoded") from exc
        if not isinstance(packet, dict):
            raise V4ContractError("source model packet is not an object")
        contract, _ = load_v4_contract(phase)
        prompt = prompt_for(phase, packet)
        system_instruction = system_instruction_for(phase, contract)
        schema = plan_schema(packet) if phase == "PLAN" else trigger_watch_schema(packet)
    request_meta = read_json(required[3])
    images: list[Path] = []
    for item in request_meta.get("images", []):
        candidate = Path(str(item.get("path", "")))
        if not candidate.exists():
            filename = candidate.name
            found = list((source_run / "charts").rglob(filename))
            if len(found) != 1:
                raise V4ContractError(f"source request image cannot be resolved: {filename}")
            candidate = found[0]
        expected_hash = str(item.get("sha256", ""))
        if expected_hash and sha256_file(candidate) != expected_hash:
            raise V4ContractError(f"source request image hash changed: {candidate}")
        images.append(candidate)
    request_dir = run_dir / "requests" / ("exact-" + source_request_id)
    request_dir.mkdir(parents=True, exist_ok=True)
    result = provider.decide(
        phase=phase,
        request_dir=request_dir,
        prompt=prompt,
        system_instruction=system_instruction,
        images=images,
        schema=schema,
        request_id="exact-" + source_request_id,
    )
    errors = sorted(
        Draft202012Validator(schema).iter_errors(result.payload),
        key=lambda item: list(item.path),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path)
        raise V4ContractError(
            f"exact source response is invalid at {location}: {first.message}"
        )
    evidence = {
        "sourceRun": source_run.name,
        "sourceRequestId": source_request_id,
        "sourcePromptSha256": sha256_file(required[0]),
        "sourceSystemInstructionSha256": sha256_file(required[1]),
        "sourceSchemaSha256": sha256_file(required[2]),
        "sourceImageSha256": [sha256_file(path) for path in images],
        "priorResponseHidden": True,
        "currentContractRefreshed": bool(refresh_current_contract),
        "appliedPromptSha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "appliedSystemInstructionSha256": hashlib.sha256(
            system_instruction.encode("utf-8")
        ).hexdigest(),
        "payload": result.payload,
        "model": result.model,
        "providerCalls": result.provider_calls,
        "usage": result.usage,
    }
    ledger = HashLedger(run_dir / "decision_ledger.jsonl")
    ledger.append("EXACT_SOURCE_REJUDGMENT", as_of, "DIAGNOSTIC", evidence)
    atomic_json(request_dir / "response.json", evidence)
    atomic_json(
        run_dir / "summary.json",
        {
            "pipelineVersion": PIPELINE_VERSION,
            "phase": phase,
            "asOfUtc": utc_text(as_of),
            "exactSourceEvidence": True,
            **evidence,
        },
    )
    print(run_dir)
    return 0


def fixed_packet(args: argparse.Namespace) -> int:
    api_key, config = load_secret()
    as_of = parse_utc(args.as_of)
    path = dataset_path(config)
    market = MarketData.from_npz(
        path,
        parse_utc(str(config["warmupStartUtc"])),
        as_of + 60,
        float(config["point"]),
    )
    packet_id = args.packet_id or f"fixed_{args.phase.lower()}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    run_dir = FIXED_ROOT / packet_id
    if run_dir.exists() and any(run_dir.iterdir()):
        raise V4ContractError(f"fixed packet directory already exists: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    runtime = new_runtime(market.m1_index_at_or_after(as_of))
    provider_name = args.decision_provider
    if args.refresh_current_contract and not args.source_run:
        raise V4ContractError("--refresh-current-contract requires --source-run")
    config["provider"] = provider_name
    if args.gemini_model:
        if provider_name != "gemini":
            raise V4ContractError("--gemini-model is only valid with Gemini")
        config["planModel"] = str(args.gemini_model)
        config["authorityPlanModel"] = str(args.gemini_model)
        config["triggerWatchModel"] = str(args.gemini_model)
    if args.gemini_thinking_level:
        if provider_name != "gemini":
            raise V4ContractError("--gemini-thinking-level is only valid with Gemini")
        config["planThinkingLevel"] = str(args.gemini_thinking_level)
        config["triggerWatchThinkingLevel"] = str(args.gemini_thinking_level)
    if args.gemini_media_resolution:
        if provider_name != "gemini":
            raise V4ContractError("--gemini-media-resolution is only valid with Gemini")
        config["mapMediaResolution"] = str(args.gemini_media_resolution)
        config["detailMediaResolution"] = str(args.gemini_media_resolution)
    atomic_json(
        run_dir / "manifest.json",
        {
            "pipelineVersion": PIPELINE_VERSION,
            "packetId": packet_id,
            "phase": args.phase,
            "asOfUtc": utc_text(as_of),
            "decisionProvider": provider_name,
            "sourceRun": str(args.source_run) if args.source_run else None,
            "exactSourceEvidence": bool(args.source_run),
            "currentContractRefreshed": bool(args.refresh_current_contract),
            "dataset": {"path": str(path), "sha256": sha256_file(path)},
            "agentsSha256": sha256_file(ROOT / "AGENTS.md"),
            "contractsManifestSha256": sha256_file(V4_MANIFEST),
            "runnerSha256": sha256_file(RUNNER_PATH),
            "coreSha256": sha256_file(CORE_PATH),
            "rendererSha256": sha256_file(RENDERER_PATH),
            "diagnosticOnly": True,
        },
    )
    provider = create_provider(args, api_key, config)
    if args.source_run:
        return rejudge_exact_source_request(
            source_run=RUN_ROOT / str(args.source_run),
            run_dir=run_dir,
            phase=str(args.phase),
            as_of=as_of,
            provider=provider,
            refresh_current_contract=bool(args.refresh_current_contract),
        )
    runner = V4Runner(config=config, market=market, run_dir=run_dir, provider=provider, runtime=runtime)
    if args.phase == "PLAN":
        focus_family_ids: set[str] | None = None
        if args.focus_root_bar_id:
            packet = build_plan_packet(market, as_of, str(config["symbol"]))
            family = next(
                (
                    item for item in packet["physicalLineageFamilies"]
                    if item["rootBarId"] == args.focus_root_bar_id
                ),
                None,
            )
            if family is None:
                raise V4ContractError(
                    f"focused root is not a selectable fresh family: {args.focus_root_bar_id}"
                )
            focus_family_ids = {str(family["familyId"])}
        runner.request_plan(as_of, focus_family_ids)
    else:
        if not args.source_run:
            raise V4ContractError("TRIGGER_WATCH fixed packet requires --source-run")
        source = RUN_ROOT / args.source_run
        state = read_json(source / "state.json")
        scenario = state.get("scenario")
        if not scenario or not scenario.get("childTouchAtUtc"):
            raise V4ContractError("source run has no frozen child-touch scenario")
        runner.runtime.update(
            {
                "state": "PLANNED",
                "scenario": scenario,
                "acceptedScenarioHashes": [scenario["scenarioHash"]],
                "apiCallsByScenario": {scenario["scenarioHash"]: 1},
            }
        )
        runner.request_trigger_watch(as_of)
    atomic_json(
        run_dir / "summary.json",
        {
            "pipelineVersion": PIPELINE_VERSION,
            "packetId": packet_id,
            "phase": args.phase,
            "state": runner.runtime["state"],
            **runner.stats,
        },
    )
    print(run_dir)
    return 0


def compare_fixed_plan(args: argparse.Namespace) -> int:
    state = read_json(args.state)
    scenario = state.get("scenario")
    truth = read_json(args.truth)
    benchmark = next(
        (
            item for item in truth.get("executableBenchmarks", [])
            if not args.trade_id or item.get("tradeId") == args.trade_id
        ),
        None,
    )
    if not benchmark:
        raise V4ContractError("fixed PLAN benchmark was not found")
    if not scenario:
        result = {"classification": "MAP_MISS", "detail": "PLAN did not freeze a scenario"}
    else:
        expected = benchmark["map"]
        expected_lineage = [
            expected["root"]["barId"],
            *[
                item["barId"]
                for item in benchmark["refinement"].get("path", [])
            ],
        ]
        actual_lineage = [
            scenario["root"]["obBarId"],
            *[item["obBarId"] for item in scenario["refinements"]],
        ]
        exact_lineage = actual_lineage == expected_lineage
        nested_lineage = (
            len(actual_lineage) >= len(expected_lineage)
            and actual_lineage[-len(expected_lineage):] == expected_lineage
            and _bar_contains(actual_lineage[0], expected_lineage[0])
        )
        causal_lineage = exact_lineage or nested_lineage
        checks = {
            "map": scenario["direction"] == expected["direction"] and scenario["scope"] == expected["scope"],
            "root": causal_lineage,
            "objective": scenario["objective"]["barId"] == expected["objective"]["barId"],
            "refinement": causal_lineage,
        }
        first_failure = next((name for name, passed in checks.items() if not passed), None)
        result = {
            "classification": "MAP_CAUSAL_MATCH" if first_failure is None else f"{first_failure.upper()}_MISS",
            "checks": checks,
            "lineageMode": "EXACT" if exact_lineage else "NESTED_PARENT" if nested_lineage else "MISMATCH",
            "expectedLineage": expected_lineage,
            "actualLineage": actual_lineage,
            "scenarioHash": scenario["scenarioHash"],
        }
    atomic_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False))
    print(args.output)
    return 0 if result["classification"] == "MAP_CAUSAL_MATCH" else 3


def audit_truth(args: argparse.Namespace) -> int:
    truth = read_json(args.truth)
    issues: list[dict[str, str]] = []
    benchmarks = truth.get("executableBenchmarks", [])
    if not isinstance(benchmarks, list) or not benchmarks:
        issues.append({"tradeId": "", "reason": "no executable benchmarks"})
    for benchmark in benchmarks if isinstance(benchmarks, list) else []:
        trade_id = str(benchmark.get("tradeId", ""))
        map_data = benchmark.get("map", {})
        refinement = benchmark.get("refinement", {})
        trigger = benchmark.get("triggerAudit", {})
        decision_text = map_data.get("decisionTimeUtc")
        touch_text = refinement.get("touchTimeUtc")
        if not decision_text:
            issues.append({"tradeId": trade_id, "reason": "missing MAP decisionTimeUtc"})
            continue
        decision = parse_utc(str(decision_text))
        if decision % TIMEFRAME_SECONDS["M15"] != 0:
            issues.append({"tradeId": trade_id, "reason": "MAP decision is not an M15/H1 close"})
        selected = [map_data.get("root", {}).get("barId")]
        selected.extend(item.get("barId") for item in refinement.get("path", []))
        if not refinement.get("path"):
            issues.append({"tradeId": trade_id, "reason": "causal refinement path is empty"})
        for selected_id in selected:
            if not selected_id:
                issues.append({"tradeId": trade_id, "reason": "root/refinement barId is missing"})
                continue
            timeframe, timestamp = split_bar_id(str(selected_id))
            if timestamp + TIMEFRAME_SECONDS[timeframe] > decision:
                issues.append(
                    {"tradeId": trade_id, "reason": f"{selected_id} was not closed at PLAN time"}
                )
        if not touch_text:
            issues.append({"tradeId": trade_id, "reason": "child touch time is missing"})
            continue
        touch = parse_utc(str(touch_text))
        if touch <= decision:
            issues.append({"tradeId": trade_id, "reason": "child touch is not later than PLAN"})
        event_times: dict[str, int] = {}
        for key in (
            "matureLiquidityTimeUtc", "sweepTimeUtc", "chochReferenceTimeUtc",
            "chochBreakTimeUtc", "executionTimeUtc",
        ):
            if trigger.get(key):
                event_times[key] = parse_utc(str(trigger[key]))
            else:
                issues.append({"tradeId": trade_id, "reason": f"missing {key}"})
        if event_times.get("sweepTimeUtc", touch) <= touch:
            issues.append({"tradeId": trade_id, "reason": "final sweep is not a later event after child touch"})
        if event_times.get("matureLiquidityTimeUtc", touch) >= event_times.get("sweepTimeUtc", touch):
            issues.append({"tradeId": trade_id, "reason": "mature liquidity did not pre-exist final sweep"})
        choch_reference = event_times.get("chochReferenceTimeUtc", touch)
        choch_break = event_times.get("chochBreakTimeUtc", touch)
        if not touch < choch_reference < choch_break:
            issues.append({
                "tradeId": trade_id,
                "reason": "CHoCH reference was not formed after touch and before the body break",
            })
        if choch_break <= event_times.get("sweepTimeUtc", touch):
            issues.append({"tradeId": trade_id, "reason": "CHoCH break is not later than final sweep"})
        execution = event_times.get("executionTimeUtc", touch)
        if not event_times.get("sweepTimeUtc", touch) <= execution < event_times.get("chochBreakTimeUtc", touch):
            issues.append({"tradeId": trade_id, "reason": "execution OB is outside the sweep-to-CHoCH displacement"})
    result = {"compatible": not issues, "benchmarks": len(benchmarks) if isinstance(benchmarks, list) else 0, "issues": issues}
    if args.output:
        atomic_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not issues else 3


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_trade_rows(path: Path) -> list[dict[str, str]]:
    """Load either the executable benchmark JSON or its flattened trade CSV."""
    if path.suffix.lower() != ".json":
        return load_csv(path)
    payload = read_json(path)
    rows: list[dict[str, str]] = []
    for benchmark in payload.get("executableBenchmarks", []):
        map_evidence = benchmark["map"]
        refinement = benchmark.get("refinement", {}).get("path", [])
        order = benchmark["order"]
        rows.append(
            {
                "trade_id": str(benchmark["tradeId"]),
                "decision_at": str(map_evidence["decisionTimeUtc"]),
                "filled_at": str(order["filledAtUtc"]),
                "direction": str(map_evidence["direction"]).lower(),
                "scope": str(map_evidence["scope"]),
                "execution_model": str(order["executionModel"]),
                "entry": str(order["entry"]),
                "sl": str(order["stopLoss"]),
                "tp": str(order["takeProfit"]),
                "root_ob_bar_id": str(map_evidence["root"]["barId"]),
                "child_ob_bar_id": str(refinement[-1]["barId"] if refinement else ""),
                "objective_bar_id": str(map_evidence["objective"]["barId"]),
            }
        )
    return rows


def _trade_timestamp(row: dict[str, str]) -> int:
    # Trade parity compares executions. A benchmark MAP decision can precede the
    # eventual limit fill by hours, while candidate CSV decision_at is the order time.
    value = row.get("filled_at") or row.get("filledAt") or row.get("decision_at") or row.get("decisionAt")
    if not value:
        raise V4ContractError("trade row has no decision/fill time")
    return parse_utc(value)


def _bar_contains(outer_bar_id: str, inner_bar_id: str) -> bool:
    """Return true when both IDs describe the same physical event window."""
    try:
        outer_tf, outer_time = split_bar_id(outer_bar_id)
        inner_tf, inner_time = split_bar_id(inner_bar_id)
        outer_seconds = TIMEFRAME_SECONDS[outer_tf]
        inner_seconds = TIMEFRAME_SECONDS[inner_tf]
    except (KeyError, TypeError, ValueError):
        return False
    return (
        outer_seconds >= inner_seconds
        and outer_time <= inner_time
        and inner_time + inner_seconds <= outer_time + outer_seconds
    )


def _same_physical_bar_event(first_bar_id: str, second_bar_id: str) -> bool:
    return first_bar_id == second_bar_id or (
        bool(first_bar_id and second_bar_id)
        and (
            _bar_contains(first_bar_id, second_bar_id)
            or _bar_contains(second_bar_id, first_bar_id)
        )
    )


def _causal_trade_identity(expected: dict[str, str], actual: dict[str, str]) -> bool:
    if expected.get("scope") != actual.get("scope"):
        return False
    for field in ("execution_model", "child_ob_bar_id"):
        if expected.get(field) and expected.get(field) != actual.get(field):
            return False
    if expected.get("objective_bar_id") and not _same_physical_bar_event(
        expected["objective_bar_id"], actual.get("objective_bar_id", "")
    ):
        return False
    expected_root = expected.get("root_ob_bar_id", "")
    actual_root = actual.get("root_ob_bar_id", "")
    return _same_physical_bar_event(expected_root, actual_root)


def _scenario_contains_root(scenario: dict[str, Any], expected_root_id: str) -> bool:
    actual_root_id = scenario["root"]["obBarId"]
    if actual_root_id == expected_root_id:
        return True
    actual_children = [item["obBarId"] for item in scenario.get("refinements", [])]
    if expected_root_id in actual_children:
        return True
    return _bar_contains(actual_root_id, expected_root_id)


def _scenario_lineage_matches(
    scenario: dict[str, Any],
    expected_root_id: str,
    expected_child_ids: list[str],
) -> bool:
    """Accept the same causal chain when the engine preserves an HTF parent."""
    actual = [
        scenario["root"]["obBarId"],
        *[item["obBarId"] for item in scenario.get("refinements", [])],
    ]
    expected = [expected_root_id, *expected_child_ids]
    if actual == expected:
        return True
    if len(actual) < len(expected) or actual[-len(expected):] != expected:
        return False
    return _bar_contains(actual[0], expected[0])


def compare_trades(args: argparse.Namespace) -> int:
    truth_coverage = "EXHAUSTIVE_EXECUTED_TRADES"
    if args.truth.suffix.lower() == ".json":
        truth_coverage = str(
            read_json(args.truth).get("coverage", "EXHAUSTIVE_EXECUTED_TRADES")
        )
    else:
        # CSV benchmarks may carry their authority boundary in a sibling
        # metadata file. Do not label unmatched candidate trades as EXTRA when
        # the CSV contains only selected legacy executions.
        metadata_path = args.truth.parent / "metadata.json"
        if metadata_path.exists():
            truth_coverage = str(
                read_json(metadata_path).get(
                    "coverage", "EXHAUSTIVE_EXECUTED_TRADES"
                )
            )
    if truth_coverage == "TRADE_SUMMARY_ONLY_NOT_GROUND_TRUTH":
        raise V4ContractError(
            "truth source is an executed-trade summary without a causal "
            "scenario ledger; parity comparison is not authorized"
        )
    truth_is_exhaustive = truth_coverage == "EXHAUSTIVE_EXECUTED_TRADES"
    truth = load_trade_rows(args.truth)
    candidate = load_trade_rows(args.candidate)
    start = parse_utc(args.start) if args.start else None
    end = parse_utc(args.end) if args.end else None
    if start is not None:
        truth = [row for row in truth if _trade_timestamp(row) >= start]
        candidate = [row for row in candidate if _trade_timestamp(row) >= start]
    if end is not None:
        truth = [row for row in truth if _trade_timestamp(row) < end]
        candidate = [row for row in candidate if _trade_timestamp(row) < end]
    unmatched = set(range(len(candidate)))
    output: list[dict[str, Any]] = []
    for expected in truth:
        options = [
            (abs(_trade_timestamp(candidate[index]) - _trade_timestamp(expected)), index)
            for index in unmatched
            if candidate[index].get("direction", "").lower() == expected.get("direction", "").lower()
            and abs(_trade_timestamp(candidate[index]) - _trade_timestamp(expected)) <= args.window_hours * 3600
        ]
        if not options:
            output.append({"truth_id": expected.get("trade_id", ""), "candidate_id": "", "classification": "MISS"})
            continue
        _, selected = min(options)
        unmatched.remove(selected)
        actual = candidate[selected]
        diffs = {
            key: abs(float(expected[key]) - float(actual[key]))
            for key in ("entry", "sl", "tp")
        }
        same_cause = _causal_trade_identity(expected, actual)
        tolerance = max(args.tick_tolerance, abs(float(expected["entry"]) - float(expected["sl"])) * 0.10)
        classification = (
            "EXACT" if same_cause and max(diffs.values()) <= args.tick_tolerance
            else "CAUSAL_MATCH" if same_cause and max(diffs.values()) <= tolerance
            else "DIRECTION_ONLY"
        )
        output.append(
            {
                "truth_id": expected.get("trade_id", ""),
                "candidate_id": actual.get("trade_id", ""),
                "classification": classification,
                **{f"{key}_diff": f"{value:.5f}" for key, value in diffs.items()},
            }
        )
    for index in sorted(unmatched):
        output.append({
            "truth_id": "",
            "candidate_id": candidate[index].get("trade_id", ""),
            "classification": "EXTRA" if truth_is_exhaustive else "UNASSESSED",
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["truth_id", "candidate_id", "classification", "entry_diff", "sl_diff", "tp_diff"]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output)
    counts = {
        kind: sum(row["classification"] == kind for row in output)
        for kind in ("EXACT", "CAUSAL_MATCH", "DIRECTION_ONLY", "MISS", "EXTRA", "UNASSESSED")
    }
    counts["truthCoverage"] = truth_coverage
    print(json.dumps(counts, ensure_ascii=False))
    print(args.output)
    passed = (
        truth_is_exhaustive
        and bool(output)
        and all(row["classification"] in {"EXACT", "CAUSAL_MATCH"} for row in output)
    )
    return 0 if passed else 3


def compare_funnel(args: argparse.Namespace) -> int:
    truth = read_json(args.truth)
    truth_coverage = str(truth.get("coverage", "EXHAUSTIVE_EXECUTED_TRADES"))
    truth_is_exhaustive = truth_coverage == "EXHAUSTIVE_EXECUTED_TRADES"
    records = [json.loads(line) for line in args.ledger.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    plans = [row for row in records if row.get("event") == "SCENARIO_PLANNED"]
    watches = [row for row in records if row.get("event") == "TRIGGER_WATCH_ARMED"]

    def scenario_variants(row: dict[str, Any]) -> list[dict[str, Any]]:
        scenario = row["details"]["scenario"]
        variants = [scenario]
        for watch_row in watches:
            if watch_row["details"].get("scenarioHash") != scenario["scenarioHash"]:
                continue
            upgrade = watch_row["details"].get("watch", {}).get("sourceUpgrade")
            if not upgrade:
                continue
            variants.append(
                {
                    **scenario,
                    "root": upgrade["root"],
                    "refinements": upgrade["refinements"],
                    "finalChild": upgrade["finalChild"],
                }
            )
        return variants
    orders = [row for row in records if row.get("event") == "ORDER_CREATED"]
    closed_trades = [row for row in records if row.get("event") == "TRADE_CLOSED"]
    rows: list[dict[str, Any]] = []
    unmatched_closed = set(range(len(closed_trades)))
    for benchmark in truth.get("executableBenchmarks", []):
        expected_map = benchmark["map"]
        expected_path = [item["barId"] for item in benchmark["refinement"].get("path", [])]
        expected_order = benchmark["order"]
        expected_fill = parse_utc(expected_order["filledAtUtc"])
        trade_options: list[tuple[float, int, int]] = []
        for index in unmatched_closed:
            trade = closed_trades[index]["details"]["trade"]
            if trade.get("direction", "").upper() != expected_map["direction"].upper():
                continue
            fill_delta = abs(parse_utc(trade["entryAtUtc"]) - expected_fill)
            if fill_delta > 24 * 3600:
                continue
            trade_options.append(
                (abs(float(trade["entry"]) - float(expected_order["entry"])), fill_delta, index)
            )
        if trade_options:
            _, _, paired_index = min(trade_options)
            unmatched_closed.remove(paired_index)
        map_matches = [
            row for row in plans
            if row["details"]["scenario"]["direction"] == expected_map["direction"]
            and row["details"]["scenario"]["scope"] == expected_map["scope"]
        ]
        classification, detail = "MAP_MISS", "direction/scope absent"
        root_matches = [
            row for row in map_matches
            if any(
                _scenario_contains_root(variant, expected_map["root"]["barId"])
                for variant in scenario_variants(row)
            )
        ]
        if map_matches:
            classification, detail = "ROOT_MISS", "map matched but root differs"
        objective_matches = [
            row for row in root_matches
            if _same_physical_bar_event(
                row["details"]["scenario"]["objective"]["barId"],
                expected_map["objective"]["barId"],
            )
            and (
                "price" not in expected_map["objective"]
                or abs(
                    float(row["details"]["scenario"]["objective"]["price"])
                    - float(expected_map["objective"]["price"])
                ) <= 1e-9
            )
        ]
        if root_matches:
            classification, detail = "OBJECTIVE_MISS", "root matched but objective differs"
        refinement_matches = [
            row for row in objective_matches
            if any(
                _scenario_lineage_matches(
                    variant,
                    expected_map["root"]["barId"],
                    expected_path,
                )
                for variant in scenario_variants(row)
            )
        ]
        if objective_matches:
            classification, detail = "REFINEMENT_MISS", "objective matched but child lineage differs"
        scenario_hashes = {row["details"]["scenario"]["scenarioHash"] for row in refinement_matches}
        expected_trigger = benchmark.get("triggerAudit", {})
        watch_matches = [
            row for row in watches
            if row["details"].get("scenarioHash") in scenario_hashes
            and row["details"]["watch"]["matureLiquidity"]["barId"] == expected_trigger.get("matureLiquidityBarId")
            and row["details"]["watch"]["chochReference"]["barId"] == expected_trigger.get("chochReferenceBarId")
        ]
        if refinement_matches:
            classification, detail = "TRIGGER_WATCH_MISS", "lineage matched but frozen trigger semantics differ"
        order_matches = []
        for row in orders:
            evidence = row["details"].get("triggerEvidence", {})
            order = row["details"].get("order", {})
            if order.get("scenarioHash") not in scenario_hashes:
                continue
            checks = {
                "sweepBarId": expected_trigger.get("sweepBarId"),
                "chochBreakBarId": expected_trigger.get("chochBreakBarId"),
                "executionBarId": expected_trigger.get("executionBarId"),
            }
            if all(not expected or evidence.get(key) == expected for key, expected in checks.items()):
                order_matches.append(row)
        if watch_matches:
            classification, detail = "ORDER_MISS", "trigger watch matched but local chain/order differs"
        if order_matches:
            classification, detail = "CAUSAL_MATCH", "MAP through local order chain matched"
        rows.append(
            {
                "truth_id": benchmark["tradeId"],
                "classification": classification,
                "map_candidates": len(map_matches),
                "root_matches": len(root_matches),
                "objective_matches": len(objective_matches),
                "refinement_matches": len(refinement_matches),
                "trigger_watch_matches": len(watch_matches),
                "order_matches": len(order_matches),
                "detail": detail,
            }
        )
    extras = [
        closed_trades[index] for index in sorted(unmatched_closed)
    ]
    for row in extras:
        rows.append(
            {
                "truth_id": "",
                "classification": "EXTRA" if truth_is_exhaustive else "UNASSESSED",
                "map_candidates": 0, "root_matches": 0, "objective_matches": 0,
                "refinement_matches": 0, "trigger_watch_matches": 0, "order_matches": 1,
                "detail": row["details"]["trade"]["tradeId"],
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "truth_id", "classification", "map_candidates", "root_matches", "objective_matches",
        "refinement_matches", "trigger_watch_matches", "order_matches", "detail",
    ]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    counts = {kind: sum(row["classification"] == kind for row in rows) for kind in sorted({row["classification"] for row in rows})}
    print(json.dumps(counts, ensure_ascii=False))
    print(args.output)
    passed = (
        truth_is_exhaustive
        and bool(rows)
        and all(row["classification"] == "CAUSAL_MATCH" for row in rows)
    )
    if args.write_sol_gate:
        run_dir = args.ledger.parent
        manifest = read_json(run_dir / "manifest.json")
        if manifest.get("decisionProvider") not in {"codex-cli", "manual-codex"}:
            raise V4ContractError("only codex-cli/manual-codex validation may write the Sol gate")
        if not passed:
            raise V4ContractError("Sol gate was not written because funnel parity did not pass")
        if not args.trade_parity:
            raise V4ContractError("Sol gate requires a closed-loop trade parity file")
        trade_parity = load_csv(args.trade_parity)
        if not trade_parity or any(
            row.get("classification") not in {"EXACT", "CAUSAL_MATCH"} for row in trade_parity
        ):
            raise V4ContractError("Sol gate was not written because trade parity did not pass")
        gate_path = ROOT / "output" / "mentor_ai_replay_v4_validation" / "sol_gate.json"
        gate = {
            "pipelineVersion": PIPELINE_VERSION,
            "runId": manifest["runId"],
            "decisionProvider": manifest["decisionProvider"],
            "datasetSha256": manifest["dataset"]["sha256"],
            "agentsSha256": manifest["agentsSha256"],
            "contractsManifestSha256": manifest["contractsManifestSha256"],
            "systemInstructionsSha256": manifest["systemInstructionsSha256"],
            "runnerSha256": manifest["runnerSha256"],
            "coreSha256": manifest["coreSha256"],
            "rendererSha256": manifest["rendererSha256"],
            "replayStartUtc": manifest["config"]["replayStartUtc"],
            "replayEndUtc": manifest["config"]["replayEndUtc"],
            "truthSha256": sha256_file(args.truth),
            "funnelParitySha256": sha256_file(args.output),
            "tradeParitySha256": sha256_file(args.trade_parity),
        }
        atomic_json(gate_path, gate)
        print(f"SOL_VALIDATION_GATE_WRITTEN {gate_path}")
    return 0 if passed else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AGENTS-first event-driven Mentor AI Replay V4")
    sub = parser.add_subparsers(dest="command", required=True)
    setup_parser = sub.add_parser("setup")
    setup_parser.set_defaults(func=setup)
    preflight_parser = sub.add_parser("preflight")
    preflight_parser.set_defaults(func=preflight)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--run-id")
    run_parser.add_argument(
        "--dataset",
        type=Path,
        help="M1 NPZ dataset for a new run. The resolved path and hash are frozen in its manifest.",
    )
    run_parser.add_argument(
        "--warmup-start",
        help="UTC warm-up start for a new run, for example 2026-01-01T00:00:00Z.",
    )
    run_parser.add_argument(
        "--follow-through-days",
        type=int,
        help="Days after the entry window used only to resolve already-open orders and positions.",
    )
    run_parser.add_argument("--start")
    run_parser.add_argument("--end")
    run_parser.add_argument("--decision-provider", choices=("gemini", "manual-codex", "codex-cli", "scripted"))
    run_parser.add_argument(
        "--gemini-model",
        help="Override both PLAN and TRIGGER_WATCH Gemini models for this new run.",
    )
    run_parser.add_argument(
        "--plan-model",
        help="Use a low-cost Gemini model for PLAN only (for example Flash Lite).",
    )
    run_parser.add_argument(
        "--authority-plan-model",
        help=(
            "Use a stronger Gemini model only when PLAN establishes or changes "
            "the external owner."
        ),
    )
    run_parser.add_argument(
        "--trigger-watch-model",
        help="Use a stronger Gemini model for TRIGGER_WATCH only (for example Flash).",
    )
    run_parser.add_argument(
        "--gemini-max-output-tokens",
        type=int,
        help="Override both PLAN and TRIGGER_WATCH output-token limits for this new run.",
    )
    run_parser.add_argument(
        "--gemini-thinking-level",
        choices=("minimal", "low", "medium", "high"),
        help="Override the Gemini 3.x thinking level for every decision phase.",
    )
    run_parser.add_argument(
        "--gemini-media-resolution",
        choices=(
            "MEDIA_RESOLUTION_LOW",
            "MEDIA_RESOLUTION_MEDIUM",
            "MEDIA_RESOLUTION_HIGH",
            "MEDIA_RESOLUTION_ULTRA_HIGH",
        ),
        help="Override the per-image Gemini processing resolution for this new run.",
    )
    run_parser.add_argument(
        "--codex-reasoning-effort",
        choices=("low", "medium", "high", "xhigh"),
        help="Override Codex CLI reasoning effort for this new validation run.",
    )
    run_parser.add_argument(
        "--maximum-tokens-per-run",
        type=int,
        help=(
            "Hard safety ceiling for one run. This is not a spending target; it prevents "
            "a nearly complete replay from being abandoned by an older lower config value."
        ),
    )
    run_parser.add_argument(
        "--maximum-api-calls-per-run",
        type=int,
        help=(
            "Per-invocation provider-call ceiling. A budget pause is resumable and "
            "the cumulative replay state is preserved."
        ),
    )
    run_parser.add_argument("--benchmark-truth", type=Path)
    run_parser.add_argument("--scripted-responses", type=Path)
    run_parser.add_argument("--resume", action="store_true")
    run_parser.add_argument(
        "--diagnostic-bypass-sol-gate",
        action="store_true",
        help="Run Gemini without a Sol gate and mark all output DIAGNOSTIC_UNGATED.",
    )
    run_parser.add_argument("--extend-follow-through-days", type=int, default=0)
    run_parser.set_defaults(func=run_replay)
    latest = sub.add_parser("latest-resume-source")
    latest.set_defaults(func=latest_resume_source)
    fixed = sub.add_parser("fixed-packet")
    fixed.add_argument("--phase", choices=("PLAN", "TRIGGER_WATCH"), required=True)
    fixed.add_argument("--as-of", required=True)
    fixed.add_argument("--packet-id")
    fixed.add_argument("--source-run")
    fixed.add_argument(
        "--refresh-current-contract",
        action="store_true",
        help=(
            "Keep the source packet, images, and as-of evidence fixed while applying "
            "the current prompt, system instruction, and response schema."
        ),
    )
    fixed.add_argument(
        "--decision-provider",
        choices=("gemini", "manual-codex", "codex-cli", "scripted"),
        default="codex-cli",
    )
    fixed.add_argument("--scripted-responses", type=Path)
    fixed.add_argument("--focus-root-bar-id")
    fixed.add_argument("--gemini-model")
    fixed.add_argument(
        "--gemini-thinking-level", choices=("minimal", "low", "medium", "high")
    )
    fixed.add_argument(
        "--gemini-media-resolution",
        choices=(
            "MEDIA_RESOLUTION_LOW",
            "MEDIA_RESOLUTION_MEDIUM",
            "MEDIA_RESOLUTION_HIGH",
            "MEDIA_RESOLUTION_ULTRA_HIGH",
        ),
    )
    fixed.set_defaults(func=fixed_packet)
    fixed_compare = sub.add_parser("compare-fixed-plan")
    fixed_compare.add_argument("--state", type=Path, required=True)
    fixed_compare.add_argument("--truth", type=Path, required=True)
    fixed_compare.add_argument("--trade-id")
    fixed_compare.add_argument("--output", type=Path, required=True)
    fixed_compare.set_defaults(func=compare_fixed_plan)
    truth_audit = sub.add_parser("audit-truth")
    truth_audit.add_argument("--truth", type=Path, required=True)
    truth_audit.add_argument("--output", type=Path)
    truth_audit.set_defaults(func=audit_truth)
    compare_parser = sub.add_parser("compare")
    compare_parser.add_argument("--candidate", type=Path, required=True)
    compare_parser.add_argument("--truth", type=Path, required=True)
    compare_parser.add_argument("--output", type=Path, required=True)
    compare_parser.add_argument("--start")
    compare_parser.add_argument("--end")
    compare_parser.add_argument("--window-hours", type=float, default=2.0)
    compare_parser.add_argument("--tick-tolerance", type=float, default=0.03)
    compare_parser.set_defaults(func=compare_trades)
    funnel_parser = sub.add_parser("compare-funnel")
    funnel_parser.add_argument("--ledger", type=Path, required=True)
    funnel_parser.add_argument("--truth", type=Path, required=True)
    funnel_parser.add_argument("--output", type=Path, required=True)
    funnel_parser.add_argument("--write-sol-gate", action="store_true")
    funnel_parser.add_argument("--trade-parity", type=Path)
    funnel_parser.set_defaults(func=compare_funnel)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except (V4ContractError, OSError, KeyError, ValueError) as exc:
        print(f"MENTOR_AI_REPLAY_V4_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
    map_schema,
