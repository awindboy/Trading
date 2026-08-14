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
    advance_shadow_delivery_candidate,
    advance_reaction_monitor,
    advance_source_upgrade_candidates,
    advance_trigger_watch,
    audit_pre_touch_delivery_lineages,
    apply_source_upgrade,
    assert_runtime_invariants,
    build_map_packet,
    build_order,
    build_plan_packet,
    build_reaction_monitor,
    build_refinement_packet,
    build_trigger_packet,
    canonical_hash,
    delivery_candidate_order,
    delivery_review_schema,
    delivery_replacement,
    detect_delivery_addon_candidate,
    detect_pre_touch_delivery_candidate,
    discovery_event_fingerprint,
    discover_source_upgrade_candidates,
    external_authority_from_scenario,
    freeze_map,
    freeze_plan,
    freeze_plan_batch,
    freeze_refinement,
    freeze_trigger_watch,
    local_scenario_cancel_reason,
    liquidity_bar_ids_matured_between,
    map_opportunity_id,
    map_schema,
    mechanical_root_candidates,
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
    reaction_source_episode_end_reason,
    reset_terminal,
    root_bar_ids_available_between,
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
V44950_LEGACY_MANIFEST = (
    ROOT / "config" / "mentor_ai_replay_v4_49_50_legacy_manifest.json"
)
RUNNER_PATH = Path(__file__).resolve()
CORE_PATH = ROOT / "scripts" / "mentor_replay_v4_core.py"
RENDERER_PATH = ROOT / "scripts" / "render_mentor_week_asof.py"
RUNTIME_AGENT_SECTIONS_BY_PHASE = {
    # Read-only documentation views retained for legacy regression tests. The
    # runner blocks these phases before contract loading.
    "MAP": frozenset({1, 2, 3, 4, 15, 18}),
    "REFINEMENT": frozenset({1, 2, 3, 4, 5, 15, 18}),
    "TRIGGER_WATCH": frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 18}),
    "DELIVERY_REVIEW": frozenset({1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 14, 15, 18}),
    "PLAN": frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 18}),
}
COMPARISON_CATEGORIES = frozenset({
    "ENGINE_CANDIDATE", "OWNER", "LINEAGE", "OBJECTIVE",
    "MODEL", "CAPACITY", "LATENCY", "BROKER",
})


DEFAULTS: dict[str, Any] = {
    "provider": "gemini",
    "model": "gemini-3.5-flash-lite",
    "planModel": "gemini-3.5-flash-lite",
    "authorityPlanModel": "gemini-3.5-flash-lite",
    "mapModel": "gemini-3.5-flash-lite",
    "refinementModel": "gemini-3.5-flash-lite",
    "triggerWatchModel": "gemini-3.5-flash-lite",
    "deliveryReviewModel": "gemini-3.5-flash-lite",
    "geminiFallbackModel": "gemini-3.5-flash-lite",
    "planFallbackModel": "gemini-3.5-flash-lite",
    "authorityPlanFallbackModel": "",
    "triggerWatchFallbackModel": "",
    "deliveryReviewFallbackModel": "",
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
    "maximumApiCallsPerRun": 400,
    "maximumTokensPerRun": 5000000,
    "maximumPlanPromptBytes": 64000,
    "maximumMapPromptBytes": 32000,
    "maximumRefinementPromptBytes": 32000,
    "maximumTriggerWatchPromptBytes": 36000,
    "maximumDeliveryReviewPromptBytes": 52000,
    "maximumSystemInstructionBytes": 65536,
    "planMaxOutputTokens": 12288,
    "mapMaxOutputTokens": 12288,
    "refinementMaxOutputTokens": 12288,
    "triggerWatchMaxOutputTokens": 12288,
    "deliveryReviewMaxOutputTokens": 8192,
    "planThinkingLevel": "low",
    "authorityPlanThinkingLevel": "low",
    "mapThinkingLevel": "low",
    "refinementThinkingLevel": "low",
    "triggerWatchThinkingLevel": "low",
    "deliveryReviewThinkingLevel": "low",
    "geminiFallbackThinkingLevel": "low",
    "temperature": 0.0,
    "timeoutSeconds": 120,
    "codexTimeoutSeconds": 1800,
    "providerRetries": 2,
    # Keep below the previously observed 15 RPM Lite allowance while avoiding
    # the obsolete free-tier 4 RPM throttle during paid validation runs.
    "minimumCallIntervalSeconds": 5,
    "requireSolGate": True,
    "mapMediaResolution": "MEDIA_RESOLUTION_ULTRA_HIGH",
    "detailMediaResolution": "MEDIA_RESOLUTION_ULTRA_HIGH",
    "planOnFamilyFormation": True,
    # A mechanical three-candle gap is not enough to authorize an execution
    # replacement.  AGENTS assigns causal continuity and meaningful delivery
    # to semantic chart judgment, so production replays must review every
    # locally surfaced candidate before it can replace the frozen OB intent.
    "enableSemanticDeliveryReview": True,
    # AGENTS.md section 7 keeps add-ons disabled until the base OB-refinement
    # execution model has independently demonstrated reproducibility.
    "enableDeliveryAddons": False,
    # Historical replay has no real provider-time market clock. Live shadow
    # enables this and compares buffered broker bars with the response wall
    # timestamp so a passed first retest can never be filled retroactively.
    "applyLiveLatencyClock": False,
    "brokerOrderLatencyMs": 0,
    # Watch lanes consume no risk. Only PENDING + FILLED exposure is capped.
    "maximumRiskSlots": 3,
    "maximumConcurrentPositions": 3,
    "maximumScenarioSlots": 256,
    "maximumPlanFamiliesPerPage": 1,
}

V450_OPERATIONAL_DEFAULTS: dict[str, Any] = {
    "model": "gemini-3.5-flash-lite",
    "planModel": "gemini-3.5-flash-lite",
    "authorityPlanModel": "gemini-3.5-flash-lite",
    "mapModel": "gemini-3.5-flash-lite",
    "refinementModel": "gemini-3.5-flash-lite",
    "triggerWatchModel": "gemini-3.5-flash-lite",
    "deliveryReviewModel": "gemini-3.5-flash-lite",
    "geminiFallbackModel": "gemini-3.5-flash-lite",
    "planThinkingLevel": "low",
    "authorityPlanThinkingLevel": "low",
    "mapThinkingLevel": "low",
    "refinementThinkingLevel": "low",
    "triggerWatchThinkingLevel": "low",
    "deliveryReviewThinkingLevel": "low",
    "geminiFallbackThinkingLevel": "low",
    "temperature": 0.0,
    "maximumApiCallsPerRun": 400,
    "maximumTokensPerRun": 5000000,
    "maximumPlanPromptBytes": 64000,
    "mapMediaResolution": "MEDIA_RESOLUTION_ULTRA_HIGH",
    "detailMediaResolution": "MEDIA_RESOLUTION_ULTRA_HIGH",
    "planOnFamilyFormation": True,
    "enableSemanticDeliveryReview": True,
}


def clear_retryable_provider_pause(runtime: dict[str, Any]) -> bool:
    """Unseal a run only when the failed provider produced no decision."""
    reason = str(runtime.get("nonResumableReason") or "")
    if not reason.startswith("CodexReplayError:"):
        return False
    error = CodexReplayError(reason.split(":", 1)[1].strip())
    if not CodexReplayError.retryable(error):
        return False
    runtime.pop("nonResumableReason", None)
    runtime.setdefault("resumeRecoveries", []).append({
        "type": "RETRYABLE_CODEX_PROVIDER_PAUSE",
        "reason": reason,
    })
    return True


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def validate_frozen_ground_truth_v2(path: Path) -> dict[str, Any] | None:
    """Validate an accepted Ground Truth V2 ledger and its binding manifest."""
    if path.suffix.lower() != ".jsonl" or path.name != "accepted_ground_truth.jsonl":
        return None
    manifest_path = path.parent / "manifest.json"
    if not manifest_path.exists():
        raise V4ContractError("GROUND_TRUTH_V2_MANIFEST_MISSING")
    manifest = read_json(manifest_path)
    if (
        manifest.get("pipelineVersion") != PIPELINE_VERSION
        or manifest.get("status") != "FROZEN_GROUND_TRUTH_V2"
        or manifest.get("groundTruthComplete") is not True
    ):
        raise V4ContractError("GROUND_TRUTH_V2_NOT_FROZEN")
    if manifest.get("agentsSha256") != sha256_file(ROOT / "AGENTS.md"):
        raise V4ContractError("GROUND_TRUTH_V2_AGENTS_MISMATCH")
    if manifest.get("contractsManifestSha256") != sha256_file(V4_MANIFEST):
        raise V4ContractError("GROUND_TRUTH_V2_CONTRACTS_MISMATCH")
    rows = read_jsonl(path)
    previous = "GENESIS"
    for index, row in enumerate(rows):
        if row.get("previousHash") != previous:
            raise V4ContractError(
                f"GROUND_TRUTH_V2_HASH_CHAIN_BROKEN:{index}"
            )
        body = dict(row)
        recorded = str(body.pop("recordHash", ""))
        if canonical_hash(body) != recorded:
            raise V4ContractError(
                f"GROUND_TRUTH_V2_RECORD_HASH_INVALID:{index}"
            )
        previous = recorded
    if len(rows) != int(manifest.get("acceptedTradeCount", -1)):
        raise V4ContractError("GROUND_TRUTH_V2_ACCEPTED_COUNT_MISMATCH")
    if previous != str(manifest.get("acceptedLedgerTipHash", "")):
        raise V4ContractError("GROUND_TRUTH_V2_LEDGER_TIP_MISMATCH")
    return manifest


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


def _secret_key_slots(raw: dict[str, Any]) -> list[str]:
    values = raw.get("apiKeys")
    if isinstance(values, list):
        keys = [str(item).strip() for item in values]
    else:
        legacy = str(raw.get("apiKey", "")).strip()
        keys = [legacy] if legacy else []
    return [item for item in keys if item]


def load_secret(api_key_slot: int | None = None) -> tuple[str, dict[str, Any]]:
    if not SECRET.exists():
        raise SystemExit("Gemini setup is missing. Run launchers/Gemini_Replay_Setup.cmd first.")
    raw = read_json(SECRET)
    keys = _secret_key_slots(raw)
    selected_slot = int(
        api_key_slot
        if api_key_slot is not None
        else raw.get("activeApiKeySlot", 1)
    )
    if selected_slot < 1 or selected_slot > len(keys):
        raise SystemExit(
            f"Gemini API key slot {selected_slot} is unavailable; configured slots={len(keys)}"
        )
    stored = dict(raw.get("config", {}))
    config = {key: stored.get(key, default) for key, default in DEFAULTS.items()}
    config["apiKeySlot"] = selected_slot
    for key in (
        "maximumMapPromptBytes", "maximumRefinementPromptBytes",
        "maximumTriggerWatchPromptBytes", "mapMaxOutputTokens",
        "refinementMaxOutputTokens", "triggerWatchMaxOutputTokens",
    ):
        config[key] = max(int(config[key]), int(DEFAULTS[key]))
    return keys[selected_slot - 1], config


def load_secret_pool(
    preferred_slot: int | None = None,
) -> tuple[list[tuple[int, str]], dict[str, Any]]:
    """Return all configured keys, ordered from the selected slot, without exposing them."""
    selected_key, config = load_secret(preferred_slot)
    raw = read_json(SECRET)
    keys = _secret_key_slots(raw)
    selected_slot = int(config["apiKeySlot"])
    ordered_slots = [selected_slot] + [
        slot for slot in range(1, len(keys) + 1) if slot != selected_slot
    ]
    pool = [(slot, keys[slot - 1]) for slot in ordered_slots]
    if not pool or pool[0][1] != selected_key:
        raise V4ContractError("Gemini API key pool selection is inconsistent")
    return pool, config


def save_secret(
    api_keys: str | list[str],
    config: dict[str, Any],
    active_slot: int = 1,
) -> None:
    SECRET.parent.mkdir(parents=True, exist_ok=True)
    keys = (
        [api_keys.strip()]
        if isinstance(api_keys, str)
        else [str(item).strip() for item in api_keys if str(item).strip()]
    )
    if not keys:
        raise V4ContractError("at least one Gemini API key is required")
    if active_slot < 1 or active_slot > len(keys):
        raise V4ContractError("active Gemini API key slot is unavailable")
    safe_config = {
        key: value for key, value in config.items()
        if key not in {"apiKey", "apiKeys"}
    }
    atomic_json(
        SECRET,
        {
            "apiKeys": keys,
            "activeApiKeySlot": int(active_slot),
            "config": safe_config,
        },
    )


def configured_key_count() -> int:
    if not SECRET.exists():
        return 0
    return len(_secret_key_slots(read_json(SECRET)))


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
    if phase in {"MAP", "REFINEMENT"}:
        legacy_name = "map_v4.md" if phase == "MAP" else "refinement_v4.md"
        legacy_path = CONTRACT_DIR / "legacy" / legacy_name
        if not legacy_path.exists():
            raise V4ContractError(f"legacy {phase} contract is missing")
        return legacy_path.read_text(encoding="utf-8-sig"), {
            "agents": manifest["agentsSha256"],
            "legacyReadOnly": sha256_file(legacy_path),
        }
    key_by_phase = {
        "PLAN": "plan",
        "TRIGGER_WATCH": "triggerWatch",
        "DELIVERY_REVIEW": "deliveryReview",
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
    if not V44950_LEGACY_MANIFEST.exists():
        raise V4ContractError("V4.49/V4.50 legacy manifest is missing")
    later = read_json(V44950_LEGACY_MANIFEST)
    if later.get("status") != "READ_ONLY_LEGACY" or later.get("writePolicy") != "FORBIDDEN":
        raise V4ContractError("V4.49/V4.50 legacy manifest is not read-only")
    for item in later.get("codeArchive", []):
        path = ROOT / item["path"]
        if (
            not path.exists()
            or path.stat().st_size != int(item["bytes"])
            or sha256_file(path) != item["sha256"]
        ):
            raise V4ContractError(
                f"V4.49/V4.50 legacy code changed after archival: {path}"
            )


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
            "swing body break. First determine the intact H1/M30 external owner. When a candidate direction "
            "follows that owner and the same family has a valid EXTERNAL_CONTINUATION to live external "
            "liquidity, do not shrink it to a same-direction INTERNAL_ROTATION target. Select that internal "
            "rotation only when the external continuation fails for a concrete map or objective reason."
        ),
        "TRIGGER_WATCH": (
            "TRIGGER_WATCH is evaluated only after the engine has frozen a valid PLAN and observed the "
            "final child contact. Judge only the supplied post-contact reaction chain. Never replace the "
            "frozen owner or objective. A supplied sourceUpgradeSelectionId may replace the original source "
            "only when that later, already-touched root-to-child lineage explains the same owner and objective "
            "more precisely; otherwise return null."
        ),
        "DELIVERY_REVIEW": (
            "DELIVERY_REVIEW is evaluated only for one locally detected pre-touch Delivery FVG candidate "
            "after a valid PLAN has already frozen owner, scope, objective, root, and final child. Judge "
            "whether this exact displacement and FVG remain causally attached to the frozen source episode. "
            "Do not approve merely because the old source distal has not broken. Do not reject because the "
            "original OB was not retested; that is the reason this replacement path exists. The replacement "
            "hard SL belongs outside the most conservative boundary among the displacement causal OB, protected "
            "swing, and original final-child invalidation plus the frozen execution buffer. The FVG distal is "
            "zone and through-delivery evidence, not the sole hard-SL authority. Never "
            "change any frozen semantic or price."
        ),
        "MAP": "MAP is a read-only legacy documentation phase.",
        "REFINEMENT": "REFINEMENT is a read-only legacy documentation phase.",
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


def model_packet_for_phase(
    phase: str, packet: dict[str, Any]
) -> dict[str, Any]:
    """Remove redundant PLAN scaffolding without removing selectable semantics."""
    if phase != "PLAN":
        return packet
    families = []
    referenced_liquidity_ids: set[str] = set()
    for family in packet.get("physicalLineageFamilies", []):
        compact = {
            key: family[key]
            for key in (
                "familyId", "direction", "rootBarId",
                "initialDisplacementBarId", "rootLaterBodyInvalidated",
                "rootLaterDistalTouched", "rootLaterProximalTouched",
            )
            if key in family
        }
        compact["displacementEpisodes"] = [
            {
                "role": "ROOT",
                "barIds": list(
                    family.get("rootDisplacementEpisodeBarIds") or []
                ),
            },
            *[
                {
                    "role": f"CHILD:{child.get('rootBarId')}",
                    "barIds": list(option.get("episodeBarIds") or []),
                }
                for child in family.get("childCandidates", [])
                for option in child.get("deliveryOptions", [])
            ],
        ]
        compact["lineagePathColumns"] = [
            "pathId", "rootOb", "rootDisplacement", "rootProtected",
            "children[ob,displacement,protected]",
        ]
        compact["lineagePathRows"] = [
            [
                path["pathSelectionId"],
                path["root"]["obBarId"],
                path["root"]["displacementBarId"],
                path["root"]["protectedSwingBarId"],
                [
                    [
                        child["obBarId"], child["displacementBarId"],
                        child["protectedSwingBarId"],
                    ]
                    for child in path["refinements"]
                ],
            ]
            for path in family.get("lineagePathOptions", [])
        ]
        compact["scenarioOptionColumns"] = [
            "scenarioId", "direction", "scope", "rangeHigh", "rangeLow",
            "objectiveBar", "objectiveSide", "objectiveKind", "objectiveMatureAt",
            "objectiveContext",
            "mapProtected",
            "ownerBreakTarget", "ownerBreak", "pathId", "intermediateBars",
            "objectiveFamily",
            "scopeOwnerRule",
        ]
        compact["scenarioOptionRows"] = [
            [
                option.get("scenarioSelectionId"),
                option.get("direction", family.get("direction")),
                option.get("scope"),
                (option.get("dealingRange") or {}).get("highBarId"),
                (option.get("dealingRange") or {}).get("lowBarId"),
                (option.get("objective") or {}).get("barId"),
                (option.get("objective") or {}).get("side"),
                (option.get("objective") or {}).get("kind"),
                (option.get("objective") or {}).get("matureAtUtc"),
                (option.get("objective") or {}).get("destinationContext"),
                option.get("mapProtectedSwingBarId"),
                option.get("ownerBreakTargetBarId"),
                option.get("ownerBreakBarId"),
                option.get("lineagePathSelectionId"),
                option.get("intermediateLiquidityBarIds", []),
                option.get("objectiveFamily"),
                {
                    "EXTERNAL_CONTINUATION": "EC",
                    "INTERNAL_ROTATION": "IR",
                    "EXTERNAL_REVERSAL": "ER",
                }.get(str(option.get("scope", "")), "UNKNOWN"),
            ]
            for option in family.get("scenarioOptions", [])
        ]
        for option in family.get("scenarioOptions", []):
            objective_id = (option.get("objective") or {}).get("barId")
            if objective_id:
                referenced_liquidity_ids.add(str(objective_id))
            referenced_liquidity_ids.update(
                str(item) for item in option.get("intermediateLiquidityBarIds", [])
            )
            referenced_liquidity_ids.update(
                str(item.get("barId"))
                for item in (option.get("objectiveFamily") or {}).get(
                    "orderedMembers", []
                )
                if item.get("barId")
            )
        families.append(compact)
    return {
        **packet,
        "physicalLineageFamilies": families,
        "swingCandidates": [
            item for item in packet.get("swingCandidates", [])
            if str(item.get("barId")) in referenced_liquidity_ids
        ],
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
            "Return only JSON matching the supplied response schema. Return exactly one decision for every supplied familyId. "
            "Each option is an indivisible mechanically enumerated combination of direction, scope, dealing range, "
            "ordered objective family, protected swing, complete maximal OB lineage, and intermediate liquidity. Judge whether "
            "each whole option is semantically the Mentor setup; never omit, decompose, or recombine a family. Do not return "
            "bar IDs, prices, state, phase, as-of time, schedules, watch events, or order values."
        )
    elif phase == "DELIVERY_REVIEW":
        instruction = (
            "Return only JSON matching the supplied response schema. Review only the supplied candidateId. "
            "Do not create or return any market identifiers or prices other than that candidateId."
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
        "DELIVERY_REVIEW": (
            "\n[FINAL DELIVERY REVIEW CHECK BEFORE JSON]\n"
            "1. The frozen OB lineage must still be the causal source episode, not merely an old unbroken price zone.\n"
            "2. Distinguish the first mechanically visible gap from the first semantically valid delivery FVG. "
            "An isolated M1 gap, a micro-pivot break, or one impulse candle that has not completed a distinct "
            "destination-direction delivery leg is not meaningful structure transfer.\n"
            "3. Prefer a body transfer of the M5 correction-controlling swing or a clear rejection and resumption "
            "from the frozen root. An M1 transfer is sufficient only when the selected completed M1 swing actually "
            "governed the correction and the chart shows a separate, completed reaction; do not approve it merely "
            "because the engine found a two-sided pivot.\n"
            "4. The FVG and causal OB must belong to that same displacement, and the original owner, objective, "
            "root, and child must remain the reason for the move. A fresh FVG may not become a new scenario.\n"
            "5. The supplied local invalidation must be defended by the same delivery displacement. The old "
            "final-child distal is not replacement stop protection and must not rescue a locally failed delivery.\n"
            "6. The candidate must be available before its first retest. Rejecting this candidate preserves the "
            "frozen PLAN so a later, independently completed delivery episode can be reviewed. Never use later "
            "price action, expected outcome, gap size, or R to decide.\n"
            "7. APPROVE_REPLACEMENT requires five PASS verdicts. Any FAIL or UNRESOLVED verdict requires REJECT_CANDIDATE."
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
            "5a. H1 external liquidity can remain live for months. The engine may carry at most the two nearest "
            "LONG_TERM_H1 objectives as inactive fallback evidence; old M30-or-lower levels are forbidden. "
            "They become executable only after Entry and hard SL exist and no current objective remains eligible. "
            "Treat that as a fallback search, not permission to maximize distance. Compare the supplied old H1 pools against the current H1/M30 "
            "owner, recentH1Range, and whether price is actually delivering into that old unswept price area. "
            "Never prefer an old pool merely because it produces more R.\n"
            "6. INTERNAL_ROTATION must label its first mature internal swing objective as INTERNAL_SWING, "
            "REACTION_TRAP, or RANGE_EDGE. EXTERNAL_SWING is reserved for an external objective.\n"
            "7. Every child must explain the same physical price event and delivery lineage as its parent; "
            "overlap alone is not causality.\n"
            "8. Select one scenarioSelectionId. Each supplied scenario is an indivisible engine-prevalidated "
            "structural combination only in the sense that its IDs and OHLC relationships are mechanically valid; "
            "it is not a semantically authorized trade. Approve the whole option or reject it; never shorten, "
            "mix, or rewrite its fields.\n"
            "9. An opposite M15/M5 family inside the intact H1/M30 range can be the correction into the "
            "selected child. It is not an opposing owner without an H1/M30 protected-swing body break.\n"
            "10. If externalMapAuthority is present, it is the persisted external owner from an earlier "
            "approved MAP, not a candidate to reinterpret. Its ACTIVE direction, dealing range, protected "
            "swing, and objective remain binding across trade close, cancellation, and internal rotation. "
            "OBJECTIVE_REACHED permits a newly formed INTERNAL_ROTATION inside its own causal dealing range, "
            "or a new same-direction continuation map. REMAP_REQUIRED means "
            "the old owner is archived: choose either a post-break same-direction reclaim continuation or "
            "an opposite EXTERNAL_REVERSAL using its exact bodyBreakBarId. If authority is absent, infer the owner "
            "from the closed HTF chart.\n"
            "11. Scope-owner audit: EXTERNAL_CONTINUATION follows the active owner; EXTERNAL_REVERSAL "
            "requires its recorded H1/M30 body break; INTERNAL_ROTATION may oppose the intact owner without "
            "an external break but must target the first internal liquidity inside the active range. Never "
            "reject INTERNAL_ROTATION merely for opposing the external owner.\n"
            "12. objectiveClassificationAndMaturity is PASS only when the objective type matches the selected "
            "scope and the exact liquidity is still live. INTERNAL_ROTATION cannot relabel an H1/M30 external "
            "wick represented on M15 as internal liquidity.\n"
            "13. Return PLAN only when all five semanticAudit verdicts are PASS. Otherwise return NO_PLAN with "
            "FAIL or UNRESOLVED verdicts. Do not infer M1 trigger evidence. executionReference is the exact latest "
            "completed M1 engine-clock candle. focusReason=ROOT_APPROACH includes an approachEvent that is a local "
            "proximity fact, not a trigger. focusReason=FAMILY_FORMATION means the complete root-child-objective "
            "family has just become knowable after its causal displacement; the source being behind current price is "
            "therefore expected and is not a rejection reason while it remains fresh and unfilled. Freeze that intent "
            "now so either a later OB retest or a same-objective Delivery-FVG replacement can be monitored without "
            "retrospective planning. Reject an option only when its objective already arrived, source was consumed or "
            "invalidated, or the family was actually known earlier and is now being reconstructed late. "
            "14. When activeScenarioSupersession is present, it cannot change direction, scope, or owner. Select "
            "the supplied newer lineage only when it replaces an unfilled older source with a more recent causal "
            "source. It may preserve the same physical objective, or use a newly mature H1/M30 external objective "
            "that lies between current market and the old objective and is the next external liquidity for that newer source. "
            "Otherwise return NO_PLAN and the engine will keep the current PLAN."
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
        "DELIVERY_REVIEW": "maximumDeliveryReviewPromptBytes",
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
    for phase in ("PLAN", "TRIGGER_WATCH", "DELIVERY_REVIEW"):
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
        "DELIVERY_REVIEW": ("plan", "micro"),
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
    api_key_slot: int | None = None


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
        "DELIVERY_REVIEW": "deliveryReviewModel",
    }[phase]


def phase_output_key(phase: str) -> str:
    return {
        "MAP": "mapMaxOutputTokens",
        "REFINEMENT": "refinementMaxOutputTokens",
        "PLAN": "planMaxOutputTokens",
        "TRIGGER_WATCH": "triggerWatchMaxOutputTokens",
        "DELIVERY_REVIEW": "deliveryReviewMaxOutputTokens",
    }[phase]


def phase_thinking_key(phase: str) -> str:
    return {
        "MAP": "mapThinkingLevel",
        "REFINEMENT": "refinementThinkingLevel",
        "PLAN": "planThinkingLevel",
        "TRIGGER_WATCH": "triggerWatchThinkingLevel",
        "DELIVERY_REVIEW": "deliveryReviewThinkingLevel",
    }[phase]


def phase_fallback_model(config: dict[str, Any], phase: str) -> str:
    key = {
        "MAP": "mapFallbackModel",
        "REFINEMENT": "refinementFallbackModel",
        "PLAN": "planFallbackModel",
        "TRIGGER_WATCH": "triggerWatchFallbackModel",
        "DELIVERY_REVIEW": "deliveryReviewFallbackModel",
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
    if str(authority.get("status", "ACTIVE")) in {"BROKEN", "REMAP_REQUIRED"}:
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
    def __init__(
        self,
        api_key: str | list[tuple[int, str]],
        config: dict[str, Any],
    ) -> None:
        if isinstance(api_key, str):
            pool = [(int(config.get("apiKeySlot", 1)), api_key)]
        else:
            pool = [(int(slot), str(value)) for slot, value in api_key]
        if not pool or any(slot < 1 or not value for slot, value in pool):
            raise V4ContractError("Gemini provider requires at least one valid API key slot")
        if len({slot for slot, _ in pool}) != len(pool):
            raise V4ContractError("Gemini provider API key slots must be unique")
        self.api_keys = pool
        self.active_key_slot, self.api_key = pool[0]
        self.config = config
        self.last_call_at = 0.0
        self.last_attempt_count = 0
        self.quota_disabled_models: set[str] = set()
        self.disabled_key_models: set[tuple[int, str]] = set()

    def available_keys(self, model: str) -> list[tuple[int, str]]:
        active = [item for item in self.api_keys if item[0] == self.active_key_slot]
        remaining = [item for item in self.api_keys if item[0] != self.active_key_slot]
        return [
            item for item in active + remaining
            if (item[0], model) not in self.disabled_key_models
        ]

    def activate_key(self, slot: int, api_key: str) -> None:
        self.active_key_slot = int(slot)
        self.api_key = api_key

    @staticmethod
    def key_failover_reason(error: GeminiReplayError) -> str | None:
        match = re.search(r"Gemini HTTP (401|403|429)", str(error))
        return f"HTTP_{match.group(1)}" if match else None

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
            key_entries = self.available_keys(model)
            if not key_entries:
                self.quota_disabled_models.add(model)
                continue
            move_to_next_model = False
            for slot, key_value in key_entries:
                if (slot, model) in self.disabled_key_models:
                    continue
                self.activate_key(slot, key_value)
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
                                request_dir
                                / f"provider_raw_{model_slug}_slot_{slot}_attempt_{attempt + 1}.json"
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
                            slot,
                        )
                    except GeminiReplayError as exc:
                        self.last_call_at = time.monotonic()
                        self.merge_usage(accumulated_usage, exc.usage)
                        failover_reason = self.key_failover_reason(exc)
                        quota_error = failover_reason == "HTTP_429"
                        if failover_reason:
                            self.disabled_key_models.add((slot, model))
                            next_keys = self.available_keys(model)
                            if next_keys:
                                print(
                                    f"[API KEY FAILOVER] phase={phase} model={model} "
                                    f"slot={slot} -> slot={next_keys[0][0]} "
                                    f"reason={failover_reason}",
                                    flush=True,
                                )
                                break
                            self.quota_disabled_models.add(model)
                            if model_index + 1 < len(models):
                                print(
                                    f"[MODEL FALLBACK] phase={phase} {model} -> "
                                    f"{models[model_index + 1]} reason=ALL_KEY_SLOTS_UNAVAILABLE",
                                    flush=True,
                                )
                                move_to_next_model = True
                                break
                            raise GeminiReplayError(
                                str(exc),
                                usage=accumulated_usage,
                                request_was_sent=True,
                                provider_call_count=calls,
                                recoverable=True,
                            ) from exc
                        retryable = self.retryable(exc)
                        if retryable and exc.recoverable:
                            force_minimal_thinking = True
                        if attempt >= retries or not retryable:
                            if model_index + 1 < len(models) and retryable:
                                print(
                                    f"[MODEL FALLBACK] phase={phase} {model} -> "
                                    f"{models[model_index + 1]} reason=RECOVERABLE_RESPONSE",
                                    flush=True,
                                )
                                move_to_next_model = True
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
                            f"[PROVIDER RETRY] model={model} slot={slot} "
                            f"request={request_dir.name} wait={delay:.1f}s thinking="
                            f"{'minimal' if force_minimal_thinking else configured_thinking_level} "
                            f"reason={exc}",
                            flush=True,
                        )
                        time.sleep(delay)
                if move_to_next_model:
                    break
            if move_to_next_model:
                continue
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
        request_observer: Any | None = None,
    ) -> None:
        self.config = config
        self.market = market
        self.run_dir = run_dir
        self.provider = provider
        self.runtime = runtime
        self.request_observer = request_observer
        self.ledger = HashLedger(run_dir / "decision_ledger.jsonl")
        self._candidate_refresh_packet: tuple[int, dict[str, Any]] | None = None
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
                "deliveryReviewRequests": 0,
                "localReauthorizations": 0,
                "localSweepWakeups": 0,
                "localMapSkips": 0,
                "localMapDeferrals": 0,
                "activeZeroTokenBars": 0,
                "flatZeroTokenBars": 0,
                "flatPlanSchedulerChecks": 0,
                "flatPlanFingerprintSkips": 0,
                "flatLocalEvidenceSkips": 0,
                "flatPlanEmptySkips": 0,
                "flatPlanWakeups": 0,
                "flatPlanCandidateRefreshes": 0,
                "flatPlanCandidatesQueued": 0,
                "flatPlanCandidatesSkippedAlreadyTouched": 0,
                "formationPlanWakeups": 0,
                "planFamiliesBlockedWhileActive": 0,
                "flatPlanApproachSkips": 0,
                "flatPlanExpiredCandidates": 0,
                "directionalPlanApproaches": 0,
                "planApproachesExpiredThroughSource": 0,
                "planApproachesBlockedWhileActive": 0,
                "planCandidatesExpiredBySource": 0,
                "challengerPlanWakeups": 0,
                "planSupersessionWakeups": 0,
                "scenariosParked": 0,
                "scenariosRestored": 0,
                "parkedScenariosDiscarded": 0,
                "parentApproachPrefetches": 0,
                "authorityTransitions": 0,
                "shadowDeliveryDetected": 0,
                "shadowDeliveryFilled": 0,
                "shadowDeliveryTp": 0,
                "shadowDeliverySl": 0,
                "deliveryReplacementOrders": 0,
                "deliveryReplacementBlockedCloserLiquidity": 0,
                "deliveryReplacementBlockedLineageAmbiguity": 0,
                "deliveryReviewApproved": 0,
                "deliveryReviewRejected": 0,
                "ordersBlockedObjectiveContract": 0,
                "childTouches": 0,
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
            "refinementRequests", "triggerWatchRequests", "deliveryReviewRequests",
            "promptTokens", "cachedContentTokens", "thoughtTokens", "candidateTokens",
            "freshPromptTokens", "effectiveTokens",
            "localSweepWakeups",
            "localMapSkips",
            "localMapDeferrals",
            "activeZeroTokenBars",
            "flatZeroTokenBars",
            "flatPlanSchedulerChecks",
            "flatPlanFingerprintSkips",
            "flatLocalEvidenceSkips",
            "flatPlanEmptySkips",
            "flatPlanWakeups",
            "flatPlanCandidateRefreshes",
            "flatPlanCandidatesQueued",
            "flatPlanCandidatesSkippedAlreadyTouched",
            "formationPlanWakeups",
            "planFamiliesBlockedWhileActive",
            "flatPlanApproachSkips",
            "flatPlanExpiredCandidates",
            "directionalPlanApproaches",
            "planApproachesExpiredThroughSource",
            "planApproachesBlockedWhileActive",
            "planCandidatesExpiredBySource",
            "challengerPlanWakeups",
            "planSupersessionWakeups",
            "scenariosParked",
            "scenariosRestored",
            "parkedScenariosDiscarded",
            "providerLatencyMsTotal",
            "providerLatencyMsMax",
            "authorityTransitions",
            "shadowDeliveryDetected",
            "shadowDeliveryFilled",
            "shadowDeliveryTp",
            "shadowDeliverySl",
            "deliveryReplacementOrders",
            "deliveryReplacementBlockedCloserLiquidity",
            "deliveryReplacementBlockedLineageAmbiguity",
            "deliveryReviewApproved",
            "deliveryReviewRejected",
            "ordersBlockedObjectiveContract",
            "childTouches",
        ):
            self.stats.setdefault(key, 0)
        self.stats.setdefault("discoveryNoFamilyReasons", {})
        self.stats.setdefault("discoveryRootCandidatesByTf", {})
        self.stats.setdefault("discoveryChildCandidatesByTf", {})
        self.stats.setdefault("cancellationReasons", {})
        # Runtime statistics are cumulative across resumes. Operational limits
        # apply to this process invocation so a free-tier replay can pause and
        # continue on the next quota window without losing market state.
        self.segment_provider_call_base = int(self.stats["providerApiCalls"])
        self.segment_token_base = int(self.stats["totalTokens"])
        self.trades: list[dict[str, Any]] = []
        self._loaded_slot_id: str | None = None
        self._request_timing: dict[str, dict[str, Any]] = {}
        self._delivery_candidate_cache: dict[str, dict[str, Any] | None] = {}
        self._blocked_delivery_physical_keys: set[str] = set()
        self._legacy_semantic_response_index: dict[str, Path] | None = None
        trades_path = run_dir / "trades.jsonl"
        if trades_path.exists():
            self.trades = [json.loads(line) for line in trades_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]

    def save(self) -> None:
        self._sync_loaded_slot()
        snapshot = deepcopy(self.runtime)
        if self._loaded_slot_id is not None:
            snapshot.update({
                "state": "FLAT", "scenario": None, "reactionMonitor": None,
                "triggerWatch": None, "order": None, "position": None,
                "shadowDeliveryCandidates": [],
            })
        assert_runtime_invariants(snapshot)
        atomic_json(self.run_dir / "state.json", snapshot)

    @staticmethod
    def semantic_request_key(
        *,
        phase: str,
        model: str,
        fallback_model: str | None,
        thinking_level: str | None,
        fallback_thinking_level: str | None,
        temperature: float,
        max_output_tokens: int,
        media_resolution: str,
        prompt: str,
        system_instruction: str,
        schema: dict[str, Any],
        image_hashes: list[str],
        contract_hashes: dict[str, Any],
    ) -> str:
        """Hash only bytes and provider settings that can affect the response."""
        return canonical_hash({
            "phase": phase,
            "model": model,
            "fallbackModel": fallback_model,
            "thinkingLevel": thinking_level,
            "fallbackThinkingLevel": fallback_thinking_level,
            "temperature": float(temperature),
            "maxOutputTokens": int(max_output_tokens),
            "mediaResolution": media_resolution,
            "promptSha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "systemInstructionSha256": hashlib.sha256(
                system_instruction.encode("utf-8")
            ).hexdigest(),
            "schemaSha256": canonical_hash(schema),
            "imageSha256": image_hashes,
            "contractHashes": contract_hashes,
        })

    def legacy_semantic_response_index(self) -> dict[str, Path]:
        if self._legacy_semantic_response_index is not None:
            return self._legacy_semantic_response_index
        index: dict[str, Path] = {}
        for run_dir in RUN_ROOT.glob("*"):
            manifest_path = run_dir / "manifest.json"
            requests_dir = run_dir / "requests"
            if run_dir == self.run_dir or not manifest_path.exists() or not requests_dir.exists():
                continue
            try:
                legacy_manifest = read_json(manifest_path)
                legacy_config = legacy_manifest.get("config", {})
            except Exception:
                continue
            if (
                str(legacy_manifest.get("pipelineVersion")) != PIPELINE_VERSION
                or str(legacy_config.get("replayStartUtc"))
                != str(self.config.get("replayStartUtc"))
                or str(legacy_config.get("replayEndUtc"))
                != str(self.config.get("replayEndUtc"))
                or str(legacy_config.get("warmupStartUtc"))
                != str(self.config.get("warmupStartUtc"))
                or str(legacy_config.get("dataset"))
                != str(self.config.get("dataset"))
            ):
                continue
            for request_dir in requests_dir.iterdir():
                response_path = request_dir / "response.json"
                metadata_path = request_dir / "request.json"
                prompt_path = request_dir / "prompt.txt"
                system_path = request_dir / "system_instruction.txt"
                schema_path = request_dir / "response_schema.json"
                if not all(path.exists() for path in (
                    response_path, metadata_path, prompt_path, system_path, schema_path
                )):
                    continue
                try:
                    metadata = read_json(metadata_path)
                    phase = str(metadata["phase"])
                    output_key = phase_output_key(phase)
                    media_resolution = str(
                        legacy_config.get("mapMediaResolution", DEFAULTS["mapMediaResolution"])
                        if phase in {"MAP", "PLAN"}
                        else legacy_config.get(
                            "detailMediaResolution", DEFAULTS["detailMediaResolution"]
                        )
                    )
                    key = self.semantic_request_key(
                        phase=phase,
                        model=str(metadata["model"]),
                        fallback_model=metadata.get("fallbackModel"),
                        thinking_level=metadata.get("thinkingLevel"),
                        fallback_thinking_level=metadata.get("fallbackThinkingLevel"),
                        temperature=float(legacy_config.get("temperature", 0.0)),
                        max_output_tokens=int(legacy_config.get(
                            output_key, DEFAULTS[output_key]
                        )),
                        media_resolution=media_resolution,
                        prompt=prompt_path.read_text(encoding="utf-8"),
                        system_instruction=system_path.read_text(encoding="utf-8"),
                        schema=read_json(schema_path),
                        image_hashes=[
                            str(item["sha256"]) for item in metadata.get("images", [])
                        ],
                        contract_hashes=dict(metadata.get("contractHashes", {})),
                    )
                except Exception:
                    continue
                index.setdefault(key, response_path)
        self._legacy_semantic_response_index = index
        return index

    @staticmethod
    def _lane_fields() -> tuple[str, ...]:
        return (
            "state", "scenario", "reactionMonitor", "triggerWatch", "order",
            "position", "shadowDeliveryCandidates", "terminalAtUtc",
        )

    def _sync_loaded_slot(self) -> None:
        if self._loaded_slot_id is None:
            return
        slot = next(
            (item for item in self.runtime.get("scenarioSlots", [])
             if item.get("slotId") == self._loaded_slot_id),
            None,
        )
        if slot is None:
            return
        for key in self._lane_fields():
            slot[key] = deepcopy(self.runtime.get(key))

    def load_scenario_slot(self, slot_id: str) -> None:
        if self._loaded_slot_id is not None:
            raise V4ContractError("cannot load a second scenario slot")
        slot = next(
            item for item in self.runtime.get("scenarioSlots", [])
            if item.get("slotId") == slot_id
        )
        for key in self._lane_fields():
            self.runtime[key] = deepcopy(slot.get(key))
        self._loaded_slot_id = slot_id

    def unload_scenario_slot(self) -> None:
        self._sync_loaded_slot()
        self.runtime["scenarioSlots"] = [
            item for item in self.runtime.get("scenarioSlots", [])
            if item.get("state") != "FLAT"
        ]
        self.runtime.update({
            "state": "FLAT", "scenario": None, "reactionMonitor": None,
            "triggerWatch": None, "order": None, "position": None,
            "shadowDeliveryCandidates": [],
        })
        self._loaded_slot_id = None

    def store_planned_scenario_slot(self, as_of: int) -> None:
        if self.runtime.get("state") != "PLANNED":
            return
        scenario = self.runtime["scenario"]
        self.append_scenario_slot(scenario, as_of)
        self.runtime.update({
            "state": "FLAT", "scenario": None, "reactionMonitor": None,
            "triggerWatch": None, "order": None, "position": None,
            "shadowDeliveryCandidates": [],
        })

    def append_scenario_slot(self, scenario: dict[str, Any], as_of: int) -> None:
        maximum = int(self.config.get("maximumScenarioSlots", 256))
        if len(self.runtime.get("scenarioSlots", [])) >= maximum:
            raise V4ContractError("maximum watch-lane capacity exceeded")
        source_key = self.source_family_key(scenario)
        if any(
            item.get("sourceFamilyKey") == source_key
            for item in self.runtime.get("scenarioSlots", [])
        ):
            raise V4ContractError("duplicate pre-fill source family slot")
        slot = {
            "slotId": f"SLOT-{canonical_hash({'scenario': scenario['scenarioHash'], 'at': as_of})[:16]}",
            "sourceFamilyKey": source_key,
            "createdAtUtc": utc_text(as_of),
        }
        slot.update({
            "state": "PLANNED",
            "scenario": deepcopy(scenario),
            "reactionMonitor": None,
            "triggerWatch": None,
            "order": None,
            "position": None,
            "shadowDeliveryCandidates": [],
            "terminalAtUtc": None,
        })
        self.runtime.setdefault("scenarioSlots", []).append(slot)
        self.event(
            "SCENARIO_SLOT_OPENED",
            as_of,
            {
                "slotId": slot["slotId"],
                "scenarioHash": scenario["scenarioHash"],
                "scenario": deepcopy(scenario),
                "sourceFamilyKey": source_key,
                "activeSlots": len(self.runtime["scenarioSlots"]),
            },
        )

    def append_reentry_slot(self, scenario: dict[str, Any], as_of: int) -> None:
        """Re-arm a valid frozen source after SL with a wholly new trigger chain."""
        maximum = int(self.config.get("maximumScenarioSlots", 256))
        if len(self.runtime.get("scenarioSlots", [])) >= maximum:
            raise V4ContractError("maximum watch-lane capacity exceeded")
        source_key = self.source_family_key(scenario)
        if source_key in self.locked_source_keys():
            return
        rearmed = deepcopy(scenario)
        rearmed["reentryArmedAtUtc"] = utc_text(as_of)
        rearmed["reentryOrdinal"] = int(rearmed.get("reentryOrdinal", 0)) + 1
        rearmed["childTouchAtUtc"] = utc_text(as_of)
        rearmed["childTouchBarId"] = self.market.m1_row(
            max(0, self.market.m1_index_at_or_after(as_of) - 1)
        )["barId"]
        monitor = build_reaction_monitor(self.market, rearmed, as_of)
        slot = {
            "slotId": "SLOT-" + canonical_hash({
                "scenario": rearmed["scenarioHash"],
                "reentry": rearmed["reentryOrdinal"],
                "at": as_of,
            })[:16],
            "sourceFamilyKey": source_key,
            "createdAtUtc": utc_text(as_of),
            "state": "REACTION_MONITOR",
            "scenario": rearmed,
            "reactionMonitor": monitor,
            "triggerWatch": None,
            "order": None,
            "position": None,
            "shadowDeliveryCandidates": [],
            "terminalAtUtc": None,
        }
        self.runtime.setdefault("scenarioSlots", []).append(slot)
        self.event(
            "SCENARIO_REENTRY_REARMED",
            as_of,
            {
                "slotId": slot["slotId"],
                "scenarioHash": rearmed["scenarioHash"],
                "sourceFamilyKey": source_key,
                "reentryOrdinal": rearmed["reentryOrdinal"],
                "monitorArmedAtUtc": monitor["armedAtUtc"],
            },
        )

    def append_pending_slot(
        self,
        scenario: dict[str, Any],
        order: dict[str, Any],
        watch: dict[str, Any],
        as_of: int,
    ) -> dict[str, Any]:
        maximum = int(self.config.get("maximumScenarioSlots", 256))
        if len(self.runtime.get("scenarioSlots", [])) >= maximum:
            raise V4ContractError("maximum watch-lane capacity exceeded")
        slot = {
            "slotId": "SLOT-" + canonical_hash(
                {"orderId": order["orderId"], "createdAt": as_of}
            )[:16],
            "sourceFamilyKey": self.source_family_key(scenario),
            "createdAtUtc": utc_text(as_of),
            "state": "PENDING",
            "scenario": deepcopy(scenario),
            "reactionMonitor": None,
            "triggerWatch": deepcopy(watch),
            "order": deepcopy(order),
            "position": None,
            "shadowDeliveryCandidates": [],
            "terminalAtUtc": None,
        }
        self.runtime.setdefault("scenarioSlots", []).append(slot)
        self.runtime.setdefault("orders", []).append({
            "slotId": slot["slotId"],
            "orderId": order["orderId"],
            "status": "PENDING",
            "createdAtUtc": utc_text(as_of),
            "clientId": "MENTOR-" + order["orderId"],
        })
        self.runtime.setdefault("executionChains", []).append({
            "executionSignalKey": self.execution_signal_key(scenario, order),
            "scenarioHash": scenario["scenarioHash"],
            "orderId": order["orderId"],
            "model": order["model"],
            "createdAtUtc": utc_text(as_of),
        })
        self.event(
            "PENDING_SLOT_OPENED",
            as_of,
            {"slotId": slot["slotId"], "order": order},
        )
        return slot

    def register_order_record(self, order: dict[str, Any], as_of: int) -> None:
        records = self.runtime.setdefault("orders", [])
        if any(item.get("orderId") == order["orderId"] for item in records):
            return
        records.append({
            "slotId": self._loaded_slot_id,
            "orderId": order["orderId"],
            "status": "PENDING",
            "createdAtUtc": utc_text(as_of),
            "clientId": "MENTOR-" + order["orderId"],
        })
        self.runtime.setdefault("executionChains", []).append({
            "executionSignalKey": self.execution_signal_key(
                self.runtime["scenario"], order
            ),
            "scenarioHash": self.runtime["scenario"]["scenarioHash"],
            "orderId": order["orderId"],
            "model": order["model"],
            "createdAtUtc": utc_text(as_of),
        })

    def source_family_key(self, scenario: dict[str, Any]) -> str:
        """Identify one owner/root/objective lineage across execution chains."""
        root = scenario.get("root") or {}
        _, root_time = split_bar_id(str(root.get("obBarId")))
        return canonical_hash({
            "direction": scenario.get("direction"),
            "rootTime": root_time,
            "rootLowTicks": round(float(root.get("low")) / self.market.point),
            "rootHighTicks": round(float(root.get("high")) / self.market.point),
        })[:24]

    def execution_signal_key(
        self, scenario: dict[str, Any], order: dict[str, Any]
    ) -> str:
        """Identify one physical execution, independent of its HTF narrative.

        Several valid map families can converge on the same M1 execution FVG
        and objective.  They are supporting explanations for one trade, not
        permission to multiply exposure at an identical price event.
        """
        execution_bar_id = (
            order.get("deliveryFvgBarId")
            or order.get("executionObBarId")
            or order.get("orderId")
        )
        return canonical_hash({
            "direction": order.get("direction"),
            "model": order.get("model"),
            "executionBarId": execution_bar_id,
            "entryTicks": round(float(order.get("entry")) / self.market.point),
        })[:24]

    @staticmethod
    def _execution_candidate_priority(item: dict[str, Any]) -> tuple[int, int, str]:
        """Prefer the latest causal root, then the most refined child TF."""
        scenario = item["scenario"]
        _, root_time = split_bar_id(str(scenario["root"]["obBarId"]))
        child_seconds = TIMEFRAME_SECONDS[str(scenario["finalChild"]["tf"])]
        return (-int(root_time), int(child_seconds), str(item.get("identity") or ""))

    def deduplicate_physical_execution_signals(self, as_of: int) -> None:
        """Collapse duplicate exposure before the next market bar is applied.

        A crash can persist one lane as FILLED before it is detached.  If no
        later market bar has been consumed, that lane is still eligible for
        the same deterministic merge as ordinary pending lanes.
        """
        groups: dict[str, list[dict[str, Any]]] = {}
        for item in self.runtime.get("openPositions", []):
            scenario = item.get("scenario")
            order = item.get("order")
            if not isinstance(scenario, dict) or not isinstance(order, dict):
                continue
            key = str(
                item.get("executionSignalKey")
                or self.execution_signal_key(scenario, order)
            )
            item["executionSignalKey"] = key
            groups.setdefault(key, []).append({
                "kind": "position",
                "identity": str(item["bookId"]),
                "scenario": scenario,
                "record": item,
                "durable": parse_utc(str(item["openedAtUtc"])) < as_of,
            })
        for item in self.runtime.get("scenarioSlots", []):
            if item.get("state") not in {"PENDING", "FILLED"}:
                continue
            scenario = item.get("scenario")
            order = item.get("order")
            if not isinstance(scenario, dict) or not isinstance(order, dict):
                continue
            key = self.execution_signal_key(scenario, order)
            item["executionSignalKey"] = key
            groups.setdefault(key, []).append({
                "kind": "slot",
                "identity": str(item["slotId"]),
                "scenario": scenario,
                "record": item,
                "durable": False,
            })

        merged: list[dict[str, Any]] = []
        remove_books: set[str] = set()
        remove_slots: set[str] = set()
        for key, candidates in groups.items():
            if len(candidates) < 2:
                continue
            lineage_keys = {
                self.source_family_key(item["scenario"]) for item in candidates
            }
            if len(lineage_keys) > 1:
                if any(item["durable"] for item in candidates):
                    raise V4ContractError(
                        "UNRESOLVED_LINEAGE discovered after a durable fill"
                    )
                for item in candidates:
                    if item["kind"] == "slot":
                        remove_slots.add(item["identity"])
                merged.append({
                    "executionSignalKey": key,
                    "kept": None,
                    "removed": [item["identity"] for item in candidates],
                    "reason": "UNRESOLVED_LINEAGE",
                })
                continue
            durable = [item for item in candidates if item["durable"]]
            pool = durable if durable else candidates
            winner = sorted(pool, key=self._execution_candidate_priority)[0]
            losers = [item for item in candidates if item is not winner]
            for loser in losers:
                if loser["kind"] == "position":
                    remove_books.add(loser["identity"])
                else:
                    remove_slots.add(loser["identity"])
            merged.append({
                "executionSignalKey": key,
                "kept": winner["identity"],
                "removed": [item["identity"] for item in losers],
            })
        if not merged:
            return
        self.runtime["openPositions"] = [
            item for item in self.runtime.get("openPositions", [])
            if str(item.get("bookId")) not in remove_books
        ]
        self.runtime["scenarioSlots"] = [
            item for item in self.runtime.get("scenarioSlots", [])
            if str(item.get("slotId")) not in remove_slots
        ]
        self.stats["duplicatePhysicalExecutionsMerged"] = int(
            self.stats.get("duplicatePhysicalExecutionsMerged", 0)
        ) + sum(len(item["removed"]) for item in merged)
        self.event(
            "DUPLICATE_PHYSICAL_EXECUTIONS_MERGED",
            as_of,
            {"families": merged, "apiCalled": False},
        )

    def locked_source_keys(self) -> set[str]:
        locked = {
            str(item["sourceFamilyKey"])
            for item in self.runtime.get("openPositions", [])
        }
        scenario = self.runtime.get("scenario")
        if isinstance(scenario, dict):
            locked.add(self.source_family_key(scenario))
        locked.update({
            str(item["sourceFamilyKey"])
            for item in self.runtime.get("scenarioSlots", [])
            if isinstance(item.get("scenario"), dict)
        })
        return locked

    def risk_slot_count(self) -> int:
        pending = sum(
            1 for item in self.runtime.get("scenarioSlots", [])
            if item.get("state") in {"PENDING", "FILLED"}
        )
        return pending + len(self.runtime.get("openPositions", []))

    def active_risk_directions(self) -> set[str]:
        directions = {
            str(item["position"]["direction"])
            for item in self.runtime.get("openPositions", [])
            if isinstance(item.get("position"), dict)
        }
        directions.update(
            str(item["order"]["direction"])
            for item in self.runtime.get("scenarioSlots", [])
            if item.get("state") in {"PENDING", "FILLED"}
            and isinstance(item.get("order"), dict)
        )
        return directions

    def risk_order_block_reason(
        self,
        order: dict[str, Any],
        scenario: dict[str, Any] | None = None,
    ) -> str | None:
        if self.risk_slot_count() >= int(self.config.get("maximumRiskSlots", 3)):
            return "CAPACITY_MAX_THREE_RISK_SLOTS"
        directions = self.active_risk_directions()
        if directions and str(order["direction"]) not in directions:
            return "OPPOSITE_DIRECTION_RISK_EXISTS"
        selected = scenario or self.runtime.get("scenario") or {}
        authority = self.runtime.get("externalMapAuthority") or {}
        if (
            selected.get("ownerStatus") == "CHALLENGER"
            and authority.get("status", "ACTIVE") == "ACTIVE"
            and str(authority.get("direction")) != str(order["direction"])
        ):
            return "OPPOSING_OWNER_NOT_CONFIRMED"
        return None

    @staticmethod
    def lane_arbitration_key(item: dict[str, Any]) -> tuple[int, int, int, str]:
        rank = {"H1": 0, "M30": 1, "M15": 2, "M5": 3}
        scenario = item.get("scenario") or {}
        root = scenario.get("root") or {}
        tf = str(root.get("tf") or split_bar_id(str(root.get("obBarId")))[0])
        order = item.get("order") or {}
        order_created = parse_utc(str(
            order.get("createdAtUtc") or item.get("createdAtUtc")
        ))
        source_recognized = parse_utc(str(
            root.get("deliveryAvailableAtUtc") or scenario.get("frozenAtUtc")
        ))
        signal_id = str(
            item.get("executionSignalKey")
            or order.get("orderId")
            or item.get("slotId")
        )
        return (order_created, rank.get(tf, 9), source_recognized, signal_id)

    def packet_source_family_key(
        self, family: dict[str, Any], as_of: int
    ) -> str:
        root = self.market.bar(str(family["rootBarId"]), as_of)
        _, root_time = split_bar_id(str(family["rootBarId"]))
        return canonical_hash({
            "direction": family.get("direction"),
            "rootTime": root_time,
            "rootLowTicks": round(float(root["low"]) / self.market.point),
            "rootHighTicks": round(float(root["high"]) / self.market.point),
        })[:24]

    def filter_locked_source_families(
        self, packet: dict[str, Any], as_of: int
    ) -> dict[str, Any]:
        """Suppress duplicate initial-entry PLANs for an already active source.

        Addons and re-entry are generated as new execution chains from the
        frozen family, not by creating another initial PLAN for the same root.
        """
        locked = self.locked_source_keys()
        if not locked:
            return packet
        retained: list[dict[str, Any]] = []
        blocked: list[dict[str, str]] = []
        for family in packet.get("physicalLineageFamilies", []):
            key = self.packet_source_family_key(family, as_of)
            if key in locked:
                blocked.append({
                    "familyId": str(family["familyId"]),
                    "rootBarId": str(family["rootBarId"]),
                })
            else:
                retained.append(family)
        if blocked:
            self.event(
                "LOCAL_DUPLICATE_INITIAL_SOURCE_SUPPRESSED",
                as_of,
                {"blockedFamilies": blocked, "apiCalled": False},
            )
        return {**packet, "physicalLineageFamilies": retained}

    def detach_filled_position(self, as_of: int) -> None:
        scenario = deepcopy(self.runtime["scenario"])
        order = deepcopy(self.runtime["order"])
        position = deepcopy(self.runtime["position"])
        family_key = self.source_family_key(scenario)
        execution_key = self.execution_signal_key(scenario, order)
        maximum = int(self.config.get("maximumRiskSlots", 3))
        # The loaded FILLED lane already occupies one risk slot and is removed
        # immediately after detaching, so only reject if the portfolio was
        # already beyond its invariant.
        if self.risk_slot_count() > maximum:
            raise V4ContractError("maximum PENDING+FILLED risk capacity exceeded")
        book_item = {
            "bookId": f"BOOK-{canonical_hash({'scenario': scenario['scenarioHash'], 'entry': position['entryBarId']})[:16]}",
            "sourceFamilyKey": family_key,
            "executionSignalKey": execution_key,
            "scenario": scenario,
            "order": order,
            "position": position,
            "openedAtUtc": utc_text(as_of),
        }
        self.runtime.setdefault("openPositions", []).append(book_item)
        for record in self.runtime.setdefault("orders", []):
            if record.get("orderId") == order["orderId"]:
                record.update({"status": "FILLED", "filledAtUtc": utc_text(as_of)})
        self.runtime.setdefault("positions", []).append({
            "bookId": book_item["bookId"],
            "orderId": order["orderId"],
            "status": "OPEN",
            "openedAtUtc": utc_text(as_of),
        })
        self.runtime.update({
            "state": "FLAT",
            "scenario": None,
            "reactionMonitor": None,
            "triggerWatch": None,
            "order": None,
            "position": None,
            "flatSinceAtUtc": utc_text(as_of),
        })
        self.event(
            "POSITION_BOOK_OPENED",
            as_of,
            {
                "bookId": book_item["bookId"],
                "scenarioHash": scenario["scenarioHash"],
                "sourceFamilyKey": family_key,
                "openPositions": len(self.runtime["openPositions"]),
            },
        )

    def record_book_trade(
        self, as_of: int, item: dict[str, Any], trade: dict[str, Any]
    ) -> None:
        scenario = item["scenario"]
        enriched = {
            **trade,
            "tradeId": f"V4-{len(self.trades) + 1:04d}",
            "scope": scenario["scope"],
            "rootTf": scenario["root"]["tf"],
            "childTf": scenario["finalChild"]["tf"],
            "rootObBarId": scenario["root"]["obBarId"],
            "childObBarId": scenario["finalChild"]["obBarId"],
            "objectiveBarId": (
                item["order"].get("selectedObjective") or scenario["objective"]
            )["barId"],
            "sourceFamilyKey": item["sourceFamilyKey"],
        }
        self.trades.append(enriched)
        with (self.run_dir / "trades.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(enriched, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.runtime["closedTrades"] = int(self.runtime.get("closedTrades", 0)) + 1
        for record in self.runtime.setdefault("positions", []):
            if record.get("bookId") == item["bookId"]:
                record.update({
                    "status": "CLOSED",
                    "closedAtUtc": utc_text(as_of),
                    "outcome": enriched["outcome"],
                })
        if enriched.get("outcome") == "TP" and scenario.get("physicalFamilyId"):
            self.runtime["retiredSourceFamilyKeys"] = list(dict.fromkeys([
                *self.runtime.get("retiredSourceFamilyKeys", []), item["sourceFamilyKey"],
            ]))
            self.runtime["completedDeliveryFamilyIds"] = list(dict.fromkeys([
                *self.runtime.get("completedDeliveryFamilyIds", []),
                str(scenario["physicalFamilyId"]),
            ]))
        elif enriched.get("outcome") == "SL" and scenario.get("physicalFamilyId"):
            # A loss does not retire an otherwise intact source family.  Start
            # from a new reaction monitor at the close time so no old sweep or
            # CHoCH can be reused as a retrospective re-entry trigger.
            row_index = max(0, self.market.m1_index_at_or_after(as_of) - 1)
            exit_row = self.market.m1_row(row_index)
            invalidation = local_scenario_cancel_reason(
                self.market, scenario, exit_row, None
            )
            if invalidation is None:
                self.append_reentry_slot(scenario, as_of)
            else:
                self.event(
                    "SCENARIO_REENTRY_REJECTED",
                    as_of,
                    {
                        "scenarioHash": scenario["scenarioHash"],
                        "reason": invalidation,
                    },
                )
        self.event(
            "POSITION_BOOK_CLOSED",
            as_of,
            {"bookId": item["bookId"], "trade": enriched},
        )
        print(
            f"[TRADE CLOSED] {enriched['tradeId']} {enriched['outcome']} "
            f"{enriched['resultR']:+.2f}R open={len(self.runtime.get('openPositions', []))}",
            flush=True,
        )

    def maybe_open_delivery_addons(
        self, row: dict[str, Any], positions: list[dict[str, Any]]
    ) -> None:
        if not bool(self.config.get("enableDeliveryAddons", False)):
            return
        if not positions:
            return
        known_execution_ids = {
            str(item.get("executionSignalKey"))
            for item in self.runtime.get("executionChains", [])
        }
        for item in sorted(positions, key=lambda value: str(value["bookId"])):
            if self.risk_slot_count() >= int(self.config.get("maximumRiskSlots", 3)):
                return
            scenario = item["scenario"]
            position = item["position"]
            candidate = detect_delivery_addon_candidate(
                self.market,
                scenario,
                position,
                row,
                float(self.config["brokerStopsLevelPrice"]),
            )
            if candidate is None or candidate.get("status") != "WAIT_FIRST_RETEST":
                continue
            provisional_order, watch = delivery_candidate_order(
                self.market, scenario, candidate
            )
            execution_key = self.execution_signal_key(scenario, provisional_order)
            if execution_key in known_execution_ids:
                continue
            semantic_review_used = bool(
                self.config.get("enableSemanticDeliveryReview", False)
            )
            if semantic_review_used and not self.request_delivery_review(
                row, candidate, scenario_override=scenario
            ):
                known_execution_ids.add(execution_key)
                continue
            semantic_ready = str(
                candidate.get("semanticReadyAtUtc") or utc_text(row["available"])
            )
            provisional_order["semanticReadyAtUtc"] = semantic_ready
            provisional_order["brokerAuthorizedAtUtc"] = self.broker_authorized_at(
                semantic_ready
            )
            blocked = self.risk_order_block_reason(provisional_order, scenario)
            if blocked:
                self.event(
                    "DELIVERY_FVG_ADDON_BLOCKED",
                    row["available"],
                    {"reason": blocked, "candidate": candidate, "apiCalled": semantic_review_used},
                )
                known_execution_ids.add(execution_key)
                continue
            self.append_pending_slot(
                scenario, provisional_order, watch, int(row["available"])
            )
            known_execution_ids.add(execution_key)
            self.event(
                "DELIVERY_FVG_ADDON_ORDER_CREATED",
                row["available"],
                {
                    "sourceBookId": item["bookId"],
                    "candidate": candidate,
                    "order": provisional_order,
                    "apiCalled": semantic_review_used,
                },
            )

    def advance_position_book(self, row: dict[str, Any]) -> None:
        retained: list[dict[str, Any]] = []
        for item in list(self.runtime.get("openPositions", [])):
            trade = advance_position(self.market, item["position"], row)
            if trade is None:
                retained.append(item)
                continue
            # Remove before the ledger save so runtime state and reported open
            # count are already authoritative at the close event.
            self.runtime["openPositions"] = [
                other for other in self.runtime.get("openPositions", [])
                if other.get("bookId") != item.get("bookId")
            ]
            self.record_book_trade(row["available"], item, trade)
        self.runtime["openPositions"] = retained
        self.maybe_open_delivery_addons(row, retained)

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
        allow_delivery_position: bool = False,
    ) -> tuple[dict[str, Any], str, bool]:
        from jsonschema import Draft202012Validator

        if phase not in {"PLAN", "TRIGGER_WATCH", "DELIVERY_REVIEW"}:
            raise V4ContractError(
                f"LEGACY_CONTRACT_DISABLED_V451: runner cannot call {phase}"
            )

        state = str(self.runtime["state"])
        if phase == "PLAN" and state != "FLAT" and not (
            allow_plan_challenger and state == "PLANNED"
        ):
            raise V4ContractError(f"PLAN API call is forbidden while state={state}")
        if phase == "TRIGGER_WATCH" and state != "REACTION_MONITOR":
            raise V4ContractError(
                f"TRIGGER_WATCH API call is forbidden while state={state}"
            )
        if phase == "DELIVERY_REVIEW" and state != "PLANNED" and not (
            allow_delivery_position and state == "FLAT"
        ):
            raise V4ContractError(
                f"DELIVERY_REVIEW API call is forbidden while state={state}"
            )
        if state in {"PENDING", "FILLED"} and not allow_delivery_position:
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
        semantic_key = self.semantic_request_key(
            phase=phase,
            model=provider_model,
            fallback_model=selected_fallback_model,
            thinking_level=thinking_level,
            fallback_thinking_level=request_body["fallbackThinkingLevel"],
            temperature=float(request_body["temperature"]),
            max_output_tokens=max_output_tokens,
            media_resolution=media_resolution,
            prompt=prompt,
            system_instruction=system_instruction,
            schema=schema,
            image_hashes=[str(item["sha256"]) for item in image_evidence],
            contract_hashes=hashes,
        )
        request_dir = self.run_dir / "requests" / request_id
        cache_dir = CACHE_ROOT / request_id
        semantic_cache_dir = CACHE_ROOT / "semantic" / semantic_key
        request_started_wall = int(time.time())
        self.runtime.setdefault("inFlightRequests", {})[request_id] = {
            "requestId": request_id,
            "phase": phase,
            "asOfUtc": utc_text(as_of),
            "contentHash": request_id,
            "startedWallUtc": utc_text(request_started_wall),
        }
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
        # Keep the exact structured evidence beside the rendered prompt.  The
        # Ground Truth finalizer audits role IDs against this as-of packet; a
        # prompt-only archive cannot prove that the selected candle was
        # available to the model before the order decision.
        atomic_json(request_dir / "packet.json", packet)
        (request_dir / "system_instruction.txt").write_bytes(
            system_instruction.encode("utf-8")
        )
        atomic_json(request_dir / "response_schema.json", schema)
        # Persist the content-addressed in-flight identity before any provider
        # side effect. A restart can reuse the exact local response or retry
        # the same request ID without creating a second semantic request.
        self.save()

        local_response = request_dir / "response.json"
        cached = cache_dir / "response.json"
        semantic_cached = semantic_cache_dir / "response.json"
        shared_cache_enabled = isinstance(self.provider, (GeminiProvider, CodexCliProvider))
        legacy_semantic = (
            self.legacy_semantic_response_index().get(semantic_key)
            if shared_cache_enabled else None
        )
        response_source = (
            local_response if local_response.exists()
            else cached if shared_cache_enabled and cached.exists()
            else semantic_cached if shared_cache_enabled and semantic_cached.exists()
            else legacy_semantic
        )
        cache_hit = response_source is not None
        provider_latency_ms = 0
        if cache_hit:
            print(f"[CACHE HIT] phase={phase} request={request_id[:12]}", flush=True)
            result_payload = read_json(response_source)
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
                key_count = max(1, len(self.provider.api_keys))
                retry_reserve = (
                    (int(self.config.get("providerRetries", 2)) + 1)
                    * model_count
                    * key_count
                )
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
                if self.request_observer is not None:
                    self.request_observer.before_request({
                        "requestId": request_id,
                        "phase": phase,
                        "asOfUtc": utc_text(as_of),
                    })
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
            finally:
                if self.request_observer is not None:
                    self.request_observer.after_request({
                        "requestId": request_id,
                        "phase": phase,
                        "asOfUtc": utc_text(as_of),
                    })
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
            "DELIVERY_REVIEW": "deliveryReviewRequests",
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
                "apiKeySlot": result.api_key_slot,
                "providerLatencyMs": provider_latency_ms,
            },
        )
        if shared_cache_enabled and not semantic_cached.exists():
            atomic_json(semantic_cached, read_json(request_dir / "response.json"))
        response_wall = int(time.time())
        self._request_timing[request_id] = {
            "requestedAtMarketUtc": utc_text(as_of),
            "startedWallUtc": utc_text(request_started_wall),
            "responseWallUtc": utc_text(response_wall),
            "providerLatencyMs": provider_latency_ms,
            "cacheHit": cache_hit,
        }
        self.runtime.setdefault("inFlightRequests", {}).pop(request_id, None)
        return result.payload, request_id, cache_hit

    def semantic_ready_at(self, request_id: str, as_of: int) -> str:
        timing = self._request_timing.get(request_id)
        if not timing:
            return utc_text(as_of)
        if bool(self.config.get("applyLiveLatencyClock", False)):
            return str(timing["responseWallUtc"])
        return utc_text(as_of)

    def broker_authorized_at(self, semantic_ready_at: str) -> str:
        delay_ms = max(0, int(self.config.get("brokerOrderLatencyMs", 0)))
        delay_seconds = (delay_ms + 999) // 1000
        return utc_text(parse_utc(semantic_ready_at) + delay_seconds)

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
        raise V4ContractError(
            "LEGACY_CONTRACT_DISABLED_V451: MAP is integrated into PLAN"
        )
        packet = build_map_packet(self.market, as_of, str(self.config["symbol"]))
        opportunity_ids = [
            map_opportunity_id(item)
            for item in packet.get("mechanicalRootCandidates", [])
        ]
        seen = list(self.runtime.get("seenMapOpportunityIds", []))
        self.runtime["seenMapOpportunityIds"] = list(
            dict.fromkeys([*seen, *opportunity_ids])
        )
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

    def sync_resolved_authority(
        self, authority: dict[str, Any] | None, as_of: int
    ) -> None:
        """Persist an owner resolution once and retain its immutable history."""
        previous = self.runtime.get("externalMapAuthority")
        previous_key = self.external_authority_key(previous)
        next_key = self.external_authority_key(authority)
        if previous_key == next_key:
            if authority is not None:
                authority["ownerEpoch"] = int(self.runtime.get("ownerEpoch", 0))
            self.runtime["externalMapAuthority"] = authority
            return
        previous_owner_identity = (
            str(previous.get("direction")) if previous else None,
            str(previous.get("status", "ACTIVE")) if previous else None,
            str((previous.get("protectedSwing") or {}).get("barId")) if previous else None,
        )
        next_owner_identity = (
            str(authority.get("direction")) if authority else None,
            str(authority.get("status", "ACTIVE")) if authority else None,
            str((authority.get("protectedSwing") or {}).get("barId")) if authority else None,
        )
        if previous_owner_identity != next_owner_identity:
            epoch = int(self.runtime.get("ownerEpoch", 0)) + 1
            self.runtime["ownerEpoch"] = epoch
            transition = {
                "ownerEpoch": epoch,
                "changedAtUtc": utc_text(as_of),
                "previous": previous_owner_identity,
                "next": next_owner_identity,
            }
            self.runtime.setdefault("ownerEpochHistory", []).append(transition)
        if authority is not None:
            authority["ownerEpoch"] = int(self.runtime.get("ownerEpoch", 0))
        previous_status = str(previous.get("status")) if previous else None
        next_status = str(authority.get("status")) if authority else None
        if next_status == "REMAP_REQUIRED" and previous_status != "REMAP_REQUIRED":
            history = self.runtime.setdefault("externalAuthorityHistory", [])
            archived = {
                **deepcopy(authority),
                "status": "RESOLVED_BROKEN",
                "archivedAtUtc": utc_text(as_of),
            }
            archive_key = canonical_hash(archived)
            if not any(item.get("archiveKey") == archive_key for item in history):
                history.append({**archived, "archiveKey": archive_key})
            self.stats["authorityTransitions"] += 1
            self.runtime["externalMapAuthority"] = authority
            self.event(
                "EXTERNAL_AUTHORITY_REMAP_REQUIRED",
                as_of,
                {
                    "previousAuthorityKey": previous_key,
                    "nextAuthorityKey": next_key,
                    "bodyBreakBarId": authority.get("bodyBreakBarId"),
                    "historicalResolution": "RESOLVED_BROKEN",
                    "apiCalled": False,
                },
            )
            return
        self.runtime["externalMapAuthority"] = authority

    @staticmethod
    def _merge_count_map(target: dict[str, Any], values: dict[str, Any]) -> None:
        for key, value in values.items():
            target[key] = int(target.get(key, 0)) + int(value)

    def record_discovery_diagnostics(
        self, packet: dict[str, Any], as_of: int
    ) -> None:
        diagnostics = dict(packet.get("discoveryDiagnostics") or {})
        self._merge_count_map(
            self.stats["discoveryRootCandidatesByTf"],
            dict(diagnostics.get("rootCandidatesByTf") or {}),
        )
        self._merge_count_map(
            self.stats["discoveryChildCandidatesByTf"],
            dict(diagnostics.get("childCandidatesByTf") or {}),
        )
        reason = diagnostics.get("noFamilyReason")
        if reason:
            reasons = self.stats["discoveryNoFamilyReasons"]
            reasons[str(reason)] = int(reasons.get(str(reason), 0)) + 1
        if diagnostics and (
            int(diagnostics.get("physicalFamilies", 0)) > 0
            or as_of % TIMEFRAME_SECONDS["H1"] == 0
        ):
            self.event(
                "LOCAL_DISCOVERY_DIAGNOSTICS",
                as_of,
                {**diagnostics, "apiCalled": False},
            )

    def latest_m15_available(self, as_of: int) -> int | None:
        rows = self.market.bars("M15", as_of, 1)
        return int(rows[-1]["available"]) if rows else None

    @staticmethod
    def stable_plan_option_key(option: dict[str, Any]) -> str:
        """Identify strategy meaning without volatile intermediate pools."""
        return canonical_hash({
            "direction": option.get("direction"),
            "scope": option.get("scope"),
            "objectiveBarId": (option.get("objective") or {}).get("barId"),
            "objectiveSide": (option.get("objective") or {}).get("side"),
            "lineagePathSelectionId": option.get("lineagePathSelectionId"),
            "ownerBreakTargetBarId": option.get("ownerBreakTargetBarId"),
            "ownerBreakBarId": option.get("ownerBreakBarId"),
        })

    def plan_option_event_available(
        self, option: dict[str, Any], as_of: int
    ) -> int:
        objective = option.get("objective") or {}
        mature_at = objective.get("matureAtUtc")
        if mature_at:
            times = [parse_utc(str(mature_at))]
        else:
            times = [
                int(self.market.bar(str(objective["barId"]), as_of)["available"])
            ]
        for key in ("ownerBreakTargetBarId", "ownerBreakBarId"):
            selected = option.get(key)
            if selected:
                times.append(int(self.market.bar(str(selected), as_of)["available"]))
        return max(times)

    def refresh_flat_plan_candidates(self, as_of: int) -> None:
        """Maintain the mechanical family ledger in every runtime state.

        Candidate knowledge is a market fact, not a FLAT-state side effect. If
        discovery stops while another scenario is active, a family can be
        rediscovered only after its reaction and then look falsely fresh.
        """
        latest_m5 = self.latest_m5_available(as_of)
        if latest_m5 is None:
            return
        if self.runtime.get("lastPlanCandidateRefreshM5") == latest_m5:
            return
        self.runtime["newPlanFamilyIdsAtLastRefresh"] = []
        previous_refresh = self.runtime.get("lastPlanCandidateRefreshM5")
        incremental = bool(
            self.runtime.get("warmupFamilyBaselineAtUtc")
            and previous_refresh is not None
        )
        focus_root_bar_ids: set[str] | None = None
        new_root_bar_ids: set[str] = set()
        new_objectives: set[str] = set()
        if incremental:
            new_root_bar_ids = root_bar_ids_available_between(
                self.market,
                int(previous_refresh),
                int(latest_m5),
            )
            focus_root_bar_ids = set(new_root_bar_ids)
            # A newly mature destination can complete a family that formed
            # after replay start. Warm-up families remain event-driven and are
            # rebuilt only at their actual root approach.
            latest_m15 = self.latest_m15_available(as_of)
            if latest_m15 is not None and int(previous_refresh) < latest_m15:
                new_objectives = liquidity_bar_ids_matured_between(
                    self.market,
                    int(previous_refresh),
                    int(latest_m5),
                )
                if new_objectives:
                    focus_root_bar_ids.update(
                        str(item)
                        for item in self.runtime.get("pendingPlanRootBarIds", [])
                    )
                    focus_root_bar_ids.update(
                        str(item["rootBarId"])
                        for item in self.runtime.get("flatPlanCandidates", [])
                        if not bool(item.get("isWarmupBaseline"))
                        and str(item.get("status", "REGISTERED"))
                        in {"REGISTERED", "DEFERRED_ACTIVE_SCENARIO"}
                    )
            if not focus_root_bar_ids:
                self.runtime["lastPlanCandidateRefreshM5"] = latest_m5
                return
        previous_authority = deepcopy(self.runtime.get("externalMapAuthority"))
        packet = build_plan_packet(
            self.market,
            as_of,
            str(self.config["symbol"]),
            external_authority=self.runtime.get("externalMapAuthority"),
            focus_root_bar_ids=focus_root_bar_ids,
        )
        self._candidate_refresh_packet = (int(as_of), packet)
        self.runtime["lastPlanCandidateRefreshM5"] = latest_m5
        self.sync_resolved_authority(packet.get("externalMapAuthority"), as_of)
        resolved_authority = packet.get("externalMapAuthority") or {}
        objective_just_advanced = bool(
            previous_authority
            and str(previous_authority.get("status", "ACTIVE")) == "ACTIVE"
            and str(resolved_authority.get("status")) == "OBJECTIVE_REACHED"
        )
        previous_objective_id = str(
            ((previous_authority or {}).get("objective") or {}).get("barId", "")
        )
        self.record_discovery_diagnostics(packet, as_of)
        pending_roots = {
            str(item) for item in self.runtime.get("pendingPlanRootBarIds", [])
        }
        # A root can already form one complete family while a different, more
        # relevant objective has not matured yet. Family completion therefore
        # must not retire the physical source. Keep every new active root until
        # its OB is consumed/invalidated, and re-evaluate it only when objective
        # evidence changes.
        pending_roots.update(new_root_bar_ids)
        if new_objectives and pending_roots:
            still_active = {
                str(item["rootBarId"])
                for item in mechanical_root_candidates(
                    self.market,
                    as_of,
                    maximum=None,
                    active_only=True,
                    focus_root_bar_ids=pending_roots,
                )
            }
            pending_roots.intersection_update(still_active)
        self.runtime["pendingPlanRootBarIds"] = sorted(pending_roots)
        authority_key = self.external_authority_key(
            self.runtime.get("externalMapAuthority")
        )
        queued = {
            str(item["familyId"]): item
            for item in self.runtime.get("flatPlanCandidates", [])
        }
        completed_delivery_families = {
            str(item)
            for item in self.runtime.get("completedDeliveryFamilyIds", [])
        }
        for family_id in completed_delivery_families:
            queued.pop(family_id, None)
        skipped_touch_keys = set(
            self.runtime.get("skippedAlreadyTouchedOpportunityKeys", [])
        )
        added = 0
        new_family_ids: list[str] = []
        new_plan_events: list[dict[str, Any]] = []
        for family in packet.get("physicalLineageFamilies", []):
            if any(
                bool(family.get(key))
                for key in (
                    "rootLaterBodyInvalidated",
                    "rootLaterDistalTouched",
                )
            ):
                continue
            family_id = str(family["familyId"])
            if family_id in completed_delivery_families:
                continue
            option_by_key = {
                self.stable_plan_option_key(item): item
                for item in family.get("scenarioOptions", [])
            }
            option_ids = sorted(
                str(item["scenarioSelectionId"])
                for item in family.get("scenarioOptions", [])
            )
            previous = queued.get(family_id, {})
            prior_option_keys = set(previous.get("knownScenarioOptionKeys", []))
            added_option_keys = sorted(set(option_by_key) - prior_option_keys)
            added_option_ids = sorted(
                str(option_by_key[key]["scenarioSelectionId"])
                for key in added_option_keys
            )
            root = self.market.bar(str(family["rootBarId"]), as_of)
            displacement = self.market.bar(
                str(family["initialDisplacementBarId"]), as_of
            )
            if family_id not in queued:
                added += 1
                new_family_ids.append(family_id)
                new_plan_events.append({
                    "familyId": family_id,
                    "reason": "PHYSICAL_FAMILY_DISCOVERED",
                    "scenarioOptionIds": option_ids,
                })
            elif added_option_keys and not bool(previous.get("isWarmupBaseline")):
                previous_seen_text = (
                    previous.get("lastSeenAtUtc")
                    or previous.get("firstSeenAtUtc")
                    or utc_text(as_of - TIMEFRAME_SECONDS["M5"])
                )
                previous_seen = parse_utc(str(previous_seen_text))
                genuinely_new = [
                    option_by_key[key]
                    for key in added_option_keys
                    if self.plan_option_event_available(
                        option_by_key[key], as_of
                    ) > previous_seen
                    or (
                        objective_just_advanced
                        and option_by_key[key].get("scope")
                        == "EXTERNAL_CONTINUATION"
                        and str(
                            (option_by_key[key].get("objective") or {}).get(
                                "barId", ""
                            )
                        ) != previous_objective_id
                    )
                ]
                # Scenario IDs can change when only intermediate liquidity
                # changes. Old objectives can also reappear after an authority
                # transition. Neither is a new causal PLAN event.
                if genuinely_new:
                    added += 1
                    new_family_ids.append(family_id)
                    new_plan_events.append({
                        "familyId": family_id,
                        "reason": (
                            "AUTHORITY_OBJECTIVE_ADVANCED"
                            if objective_just_advanced
                            else "NEW_CAUSAL_OPTION_MATURED"
                        ),
                        "scenarioOptionIds": sorted(
                            str(item["scenarioSelectionId"])
                            for item in genuinely_new
                        ),
                    })
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
                # Do not backdate knowledge to the old displacement candle.
                # The complete family/objective became actionable only when
                # this replay first enumerated it.
                "knownAtUtc": previous.get("knownAtUtc", utc_text(as_of)),
                "firstSeenAtUtc": previous.get(
                    "firstSeenAtUtc", utc_text(as_of)
                ),
                "lastSeenAtUtc": utc_text(as_of),
                "authorityKeyAtDiscovery": previous.get(
                    "authorityKeyAtDiscovery", authority_key
                ),
                "status": previous.get("status", "REGISTERED"),
                "knownScenarioOptionIds": option_ids,
                "knownScenarioOptionKeys": sorted(option_by_key),
                "newScenarioOptionIds": added_option_ids,
                "previousClose": previous.get("previousClose"),
                "lastObservedAtUtc": previous.get("lastObservedAtUtc"),
                "approachEvent": previous.get("approachEvent"),
                "isWarmupBaseline": bool(previous.get("isWarmupBaseline", False)),
            }
        candidates = sorted(
            queued.values(),
            key=lambda item: (
                int(item["displacementAvailable"]), str(item["familyId"])
            ),
        )
        self.runtime["flatPlanCandidates"] = candidates
        retained_ids = {str(item["familyId"]) for item in candidates}
        self.runtime["newPlanFamilyIdsAtLastRefresh"] = [
            family_id for family_id in new_family_ids if family_id in retained_ids
        ]
        self.runtime["newPlanEventsAtLastRefresh"] = [
            item for item in new_plan_events
            if item["familyId"] in retained_ids
        ]
        self.runtime["skippedAlreadyTouchedOpportunityKeys"] = sorted(
            skipped_touch_keys
        )
        self.stats["flatPlanCandidateRefreshes"] += 1
        self.stats["flatPlanCandidatesQueued"] += added
        self.event(
            "LOCAL_PLAN_CANDIDATES_REFRESHED",
            as_of,
            {
                "newCandidates": added,
                "newFamilyIds": self.runtime["newPlanFamilyIdsAtLastRefresh"],
                "newPlanEvents": self.runtime["newPlanEventsAtLastRefresh"],
                "queuedCandidates": len(candidates),
                "pendingRootCount": len(pending_roots),
                "pendingRootIdsHash": canonical_hash(sorted(pending_roots)),
                "authorityKey": authority_key,
                "apiCalled": False,
            },
        )

    def seed_warmup_family_baseline(self, as_of: int) -> None:
        """Register pre-existing families without treating them as new events."""
        if self.runtime.get("warmupFamilyBaselineAtUtc"):
            return
        if self.runtime.get("flatPlanCandidates"):
            raise V4ContractError("warm-up family baseline requires an empty ledger")
        self.refresh_flat_plan_candidates(as_of)
        baseline_ids = sorted(
            str(item["familyId"])
            for item in self.runtime.get("flatPlanCandidates", [])
        )
        self.runtime["newPlanFamilyIdsAtLastRefresh"] = []
        self.runtime["newPlanEventsAtLastRefresh"] = []
        self.runtime["deferredPlanEvents"] = []
        self.runtime["warmupFamilyBaselineAtUtc"] = utc_text(as_of)
        for candidate in self.runtime.get("flatPlanCandidates", []):
            candidate["isWarmupBaseline"] = True
        self.event(
            "WARMUP_FAMILY_BASELINE_SEEDED",
            as_of,
            {
                "familyCount": len(baseline_ids),
                "familyIdsHash": canonical_hash(baseline_ids),
                "apiCalled": False,
            },
        )

    def schedule_formation_driven_flat_plan(
        self,
        row: dict[str, Any],
        *,
        state_at_bar_start: str,
        api_allowed: bool = True,
    ) -> bool:
        """Freeze a causal family when it becomes knowable, before any retest.

        Delivery-FVG replacement cannot work if PLAN is delayed until the
        original root OB is revisited: the entire replacement case is that
        price leaves the frozen OB intent unfilled.  A newly completed family
        is therefore the semantic event.  All families discovered on the same
        closed M5 candle are reviewed in one request.
        """
        if not bool(self.config.get("planOnFamilyFormation", False)):
            return False
        new_events = list(self.runtime.get("newPlanEventsAtLastRefresh", []))
        deferred_events = list(self.runtime.get("deferredPlanEvents", []))
        if not new_events and self.runtime.get("newPlanFamilyIdsAtLastRefresh"):
            new_events = [
                {
                    "familyId": str(item),
                    "reason": "PHYSICAL_FAMILY_DISCOVERED",
                    "scenarioOptionIds": [],
                }
                for item in self.runtime["newPlanFamilyIdsAtLastRefresh"]
            ]
        merged_events: dict[tuple[str, str], dict[str, Any]] = {}
        for item in [*deferred_events, *new_events]:
            key = (str(item["familyId"]), str(item["reason"]))
            previous = merged_events.get(key, {})
            merged_events[key] = {
                "familyId": key[0],
                "reason": key[1],
                "scenarioOptionIds": sorted(set(
                    [*previous.get("scenarioOptionIds", []), *item.get("scenarioOptionIds", [])]
                )),
            }
        events = list(merged_events.values())
        family_ids = {str(item["familyId"]) for item in events}
        forced_remap_ids = {
            str(item) for item in self.runtime.get("forcedRemapFamilyIds", [])
        }
        if forced_remap_ids:
            # A supersession is not a general rescan. Only the locally proven
            # replacement families may compete; otherwise the model can pick
            # the just-retired source again from an older deferred event.
            events = [
                item for item in events
                if str(item["familyId"]) in forced_remap_ids
            ]
            family_ids = {str(item["familyId"]) for item in events}
        if not family_ids:
            return False
        if state_at_bar_start != "FLAT" or self.runtime["state"] != "FLAT":
            self.runtime["deferredPlanEvents"] = events
            self.runtime["newPlanFamilyIdsAtLastRefresh"] = []
            self.runtime["newPlanEventsAtLastRefresh"] = []
            self.stats["planFamiliesBlockedWhileActive"] += len(family_ids)
            for candidate in self.runtime.get("flatPlanCandidates", []):
                if str(candidate["familyId"]) in family_ids:
                    candidate["status"] = "DEFERRED_ACTIVE_SCENARIO"
            self.event(
                "LOCAL_PLAN_FORMATION_DEFERRED_ACTIVE",
                int(row["available"]),
                {"familyIds": sorted(family_ids), "apiCalled": False},
            )
            return False
        if not api_allowed:
            return False
        self.runtime["newPlanFamilyIdsAtLastRefresh"] = []
        self.runtime["newPlanEventsAtLastRefresh"] = []
        self.runtime["deferredPlanEvents"] = (
            []
            if forced_remap_ids
            else [
                item for item in deferred_events
                if str(item.get("familyId")) not in family_ids
            ]
        )
        self.runtime["forcedRemapFamilyIds"] = []

        focused_root_ids = {
            str(item["rootBarId"])
            for item in self.runtime.get("flatPlanCandidates", [])
            if str(item["familyId"]) in family_ids and item.get("rootBarId")
        }
        cached = self._candidate_refresh_packet
        cached_families = {
            str(item["familyId"])
            for item in (
                cached[1].get("physicalLineageFamilies", [])
                if cached and cached[0] == int(row["available"])
                else []
            )
        }
        if family_ids.issubset(cached_families):
            packet = deepcopy(cached[1])
            packet["physicalLineageFamilies"] = [
                item for item in packet["physicalLineageFamilies"]
                if str(item["familyId"]) in family_ids
            ]
            packet["focusReason"] = "FAMILY_FORMATION"
            packet["focusedFamilyFormation"] = True
            packet["focusedRootApproach"] = False
            packet["focusedFamilyIds"] = sorted(family_ids)
        else:
            packet = build_plan_packet(
                self.market,
                int(row["available"]),
                str(self.config["symbol"]),
                focus_family_ids=family_ids,
                focus_root_bar_ids=focused_root_ids or None,
                external_authority=self.runtime.get("externalMapAuthority"),
            )
        selectable = {
            str(item["familyId"])
            for item in packet.get("physicalLineageFamilies", [])
        }
        if not selectable:
            self.stats["flatPlanExpiredCandidates"] += len(family_ids)
            self.event(
                "LOCAL_PLAN_FORMATION_STALE",
                int(row["available"]),
                {"familyIds": sorted(family_ids), "apiCalled": False},
            )
            return False

        authority_key = self.external_authority_key(
            self.runtime.get("externalMapAuthority")
        )
        for candidate in self.runtime.get("flatPlanCandidates", []):
            if str(candidate["familyId"]) in selectable:
                candidate["status"] = "EVALUATED_AT_FORMATION"
        fingerprint = canonical_hash(
            {
                "event": "CAUSAL_FAMILY_FORMED",
                "authorityKey": authority_key,
                "familyIds": sorted(selectable),
            }
        )
        self.stats["formationPlanWakeups"] += 1
        self.event(
            "LOCAL_CAUSAL_FAMILY_PLAN_SCHEDULED",
            int(row["available"]),
            {
                "familyIds": sorted(selectable),
                "authorityKey": authority_key,
                "apiCalled": True,
            },
        )
        self.request_plan(
            int(row["available"]),
            packet=packet,
            plan_fingerprint=fingerprint,
        )
        return True

    def schedule_active_plan_supersession(
        self, row: dict[str, Any], *, state_at_bar_start: str
    ) -> bool:
        """Retain later families without superseding a valid active PLAN.

        AGENTS does not list a newer causal source as a cancellation event.
        Later families may be evaluated only after the active scenario reaches
        an explicit terminal condition and the engine is FLAT again.
        """
        new_events = list(self.runtime.get("newPlanEventsAtLastRefresh", []))
        if not new_events and self.runtime.get("newPlanFamilyIdsAtLastRefresh"):
            new_events = [
                {
                    "familyId": str(item),
                    "reason": "PHYSICAL_FAMILY_DISCOVERED",
                    "scenarioOptionIds": [],
                }
                for item in self.runtime["newPlanFamilyIdsAtLastRefresh"]
            ]
        if new_events:
            self.defer_plan_events(new_events)
            self.stats["planFamiliesBlockedWhileActive"] += len({
                str(item["familyId"]) for item in new_events
            })
            self.event(
                "LOCAL_NEWER_CAUSAL_SOURCE_DEFERRED_ACTIVE",
                int(row["available"]),
                {
                    "familyIds": sorted({
                        str(item["familyId"]) for item in new_events
                    }),
                    "apiCalled": False,
                },
            )
        self.runtime["newPlanFamilyIdsAtLastRefresh"] = []
        self.runtime["newPlanEventsAtLastRefresh"] = []
        return False

        # Legacy V4.69 supersession implementation is intentionally unreachable.
        # It is retained temporarily only to keep old run forensics readable.
        events_by_family: dict[str, list[dict[str, Any]]] = {}
        for event in [*self.runtime.get("deferredPlanEvents", []), *new_events]:
            events_by_family.setdefault(str(event["familyId"]), []).append(event)
        family_ids = set(events_by_family)
        if not family_ids:
            return False
        self.runtime["newPlanFamilyIdsAtLastRefresh"] = []
        self.runtime["newPlanEventsAtLastRefresh"] = []
        if state_at_bar_start != "PLANNED" or self.runtime["state"] != "PLANNED":
            self.defer_plan_events(new_events)
            self.stats["planFamiliesBlockedWhileActive"] += len(family_ids)
            return False
        scenario = self.runtime["scenario"]
        if scenario.get("childTouchAtUtc") is not None:
            self.defer_plan_events(new_events)
            self.stats["planFamiliesBlockedWhileActive"] += len(family_ids)
            return False
        current_family_id = str(scenario.get("physicalFamilyId") or "")
        family_ids.discard(current_family_id)
        if not family_ids:
            self.defer_plan_events(new_events)
            return False

        # Build without the persisted authority first. The active authority can
        # hide a newer bar representing the same physical liquidity pool and
        # thereby prevent a valid later root/child lineage from being compared.
        packet = build_plan_packet(
            self.market,
            int(row["available"]),
            str(self.config["symbol"]),
            focus_family_ids=family_ids,
            external_authority=None,
        )
        spread = max(
            self.market.point,
            float(row["spreadPoints"]) * self.market.point,
        )
        current_objective = float(scenario["objective"]["price"])
        current_source_available = max(
            parse_utc(str(scenario["root"]["deliveryAvailableAtUtc"])),
            parse_utc(str(scenario["finalChild"]["deliveryAvailableAtUtc"])),
        )
        evaluated = set(self.runtime.get("evaluatedPlanSupersessionKeys", []))
        retained: list[dict[str, Any]] = []
        evaluated_now: list[str] = []
        attempted_family_ids: set[str] = set()
        for family in packet.get("physicalLineageFamilies", []):
            family_id = str(family["familyId"])
            if family_id not in family_ids:
                continue
            paths = {
                str(path["pathSelectionId"]): path
                for path in family.get("lineagePathOptions", [])
            }
            relevant_options = [
                option for option in family.get("scenarioOptions", [])
                if option.get("direction") == scenario.get("direction")
                and option.get("scope") == scenario.get("scope")
            ]
            meaning_key = canonical_hash({
                "activeScenarioHash": scenario["scenarioHash"],
                "familyId": family_id,
                "options": sorted(
                    self.stable_plan_option_key(option)
                    for option in relevant_options
                ),
            })
            if meaning_key in evaluated:
                continue
            attempted_family_ids.add(family_id)
            evaluated_now.append(meaning_key)
            options: list[dict[str, Any]] = []
            for option in relevant_options:
                objective = option.get("objective") or {}
                bar = self.market.bar(
                    str(objective["barId"]), int(row["available"])
                )
                candidate_price = (
                    float(bar["high"])
                    if objective.get("side") == "HIGH"
                    else float(bar["low"])
                )
                path = paths.get(str(option.get("lineagePathSelectionId")))
                if path is None:
                    continue
                nodes = [path["root"], *path.get("refinements", [])]
                candidate_source_available = max(
                    int(self.market.bar(
                        str(node["displacementBarId"]), int(row["available"])
                    )["available"])
                    for node in nodes
                )
                # Supersession is monotonic. An older source cannot regain
                # authority merely because its family remains deferred.
                if candidate_source_available <= current_source_available:
                    continue
                same_objective = (
                    abs(candidate_price - current_objective) <= spread + 1e-9
                )
                market_price = float(row["close"])
                nearer_external_checkpoint = (
                    scenario.get("scope") == "EXTERNAL_CONTINUATION"
                    and str(objective.get("kind")) == "EXTERNAL_SWING"
                    and str(objective.get("barId", "")).startswith(("H1:", "M30:"))
                    and isinstance(objective.get("matureAtUtc"), str)
                    # The destination liquidity must already exist when the
                    # newer causal source starts delivering. The former
                    # comparison was reversed, which kept a stale source alive
                    # whenever the valid nearer objective predated the source.
                    and parse_utc(str(objective["matureAtUtc"])) <= candidate_source_available
                    and (
                        current_objective < candidate_price < market_price
                        if scenario.get("direction") == "SHORT"
                        else market_price < candidate_price < current_objective
                    )
                )
                if same_objective or nearer_external_checkpoint:
                    options.append(option)
            if options:
                retained.append({**family, "scenarioOptions": options})
        packet["physicalLineageFamilies"] = retained
        if evaluated_now:
            self.runtime["evaluatedPlanSupersessionKeys"] = list(
                dict.fromkeys([
                    *self.runtime.get("evaluatedPlanSupersessionKeys", []),
                    *evaluated_now,
                ])
            )
        if not attempted_family_ids:
            self.defer_plan_events(new_events)
            return False
        if not retained:
            self.defer_plan_events(new_events)
            self.event(
                "LOCAL_PLAN_SUPERSESSION_NOT_COMPARABLE",
                int(row["available"]),
                {"familyIds": sorted(family_ids), "apiCalled": False},
            )
            return False
        retained_family_ids = {
            str(family["familyId"]) for family in retained
        }
        self.stats["planSupersessionWakeups"] += 1
        self.event(
            "LOCAL_NEWER_CAUSAL_SOURCE_DETECTED",
            int(row["available"]),
            {
                "activeScenarioHash": scenario["scenarioHash"],
                "familyIds": sorted(retained_family_ids),
                "objectivePrice": current_objective,
                "apiCalled": False,
            },
        )
        replacement_events: list[dict[str, Any]] = []
        for family_id in sorted(retained_family_ids):
            family_events = events_by_family.get(family_id, [])
            option_ids = sorted({
                str(option_id)
                for item in family_events
                for option_id in item.get("scenarioOptionIds", [])
            })
            replacement_events.append({
                "familyId": family_id,
                "reason": "NEWER_CAUSAL_SOURCE_REMAP",
                "scenarioOptionIds": option_ids,
            })
        # Replace, rather than merge, the queue. The old active family and any
        # unrelated deferred family must not enter the mandatory remap packet.
        self.runtime["deferredPlanEvents"] = replacement_events
        self.runtime["forcedRemapFamilyIds"] = sorted(retained_family_ids)
        self.runtime["newPlanFamilyIdsAtLastRefresh"] = []
        self.runtime["newPlanEventsAtLastRefresh"] = []
        self.cancel(
            int(row["available"]),
            "NEWER_CAUSAL_SOURCE_REQUIRES_REMAP",
            {
                "replacementFamilyIds": sorted(retained_family_ids),
                "apiCalled": False,
            },
        )
        return True

    def defer_plan_events(self, events: list[dict[str, Any]]) -> None:
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        for item in [*self.runtime.get("deferredPlanEvents", []), *events]:
            key = (str(item["familyId"]), str(item["reason"]))
            previous = merged.get(key, {})
            merged[key] = {
                "familyId": key[0],
                "reason": key[1],
                "scenarioOptionIds": sorted(set(
                    [*previous.get("scenarioOptionIds", []), *item.get("scenarioOptionIds", [])]
                )),
            }
        self.runtime["deferredPlanEvents"] = list(merged.values())

    def advance_plan_candidate_ledger(
        self, row: dict[str, Any], state_at_bar_start: str
    ) -> list[dict[str, Any]]:
        """Advance POI approach lifecycle from the actual completed M1 candle.

        LONG demand is approached from above and SHORT supply from below. A
        candidate discovered on the current candle cannot create an approach
        event on that same candle. Events that occur while another scenario is
        active are recorded as missed/blocked and cannot be resurrected after
        the active scenario terminates later on the same bar.
        """
        available = int(row["available"])
        if self.runtime.get("lastCandidateLedgerBarAvailable") == available:
            return []
        self.runtime["lastCandidateLedgerBarAvailable"] = available
        authority_key = self.external_authority_key(
            self.runtime.get("externalMapAuthority")
        )
        evaluated = set(self.runtime.get("evaluatedPlanOpportunityKeys", []))
        events: list[dict[str, Any]] = []
        candidates: list[dict[str, Any]] = []
        for source in self.runtime.get("flatPlanCandidates", []):
            candidate = dict(source)
            family_id = str(candidate["familyId"])
            evaluation_key = f"{authority_key}:{family_id}"
            status = str(candidate.get("status", "REGISTERED"))
            if evaluation_key in evaluated and status == "REGISTERED":
                status = "EVALUATED"
                candidate["status"] = status
            low = float(candidate["rootLow"])
            high = float(candidate["rootHigh"])
            direction = str(candidate["direction"])
            body_invalidated = (
                float(row["close"]) < low
                if direction == "LONG"
                else float(row["close"]) > high
            )
            if status == "REGISTERED" and body_invalidated:
                candidate["status"] = "EXPIRED_SOURCE_BODY_BREAK"
                self.stats["planCandidatesExpiredBySource"] += 1
                candidates.append(candidate)
                continue
            known_at = parse_utc(str(candidate["knownAtUtc"]))
            previous_close = candidate.get("previousClose")
            if available <= known_at:
                candidate["previousClose"] = float(row["close"])
                candidate["lastObservedAtUtc"] = utc_text(available)
                candidates.append(candidate)
                continue
            if previous_close is None:
                index = row.get("index")
                if index is not None and int(index) > 0:
                    prior = self.market.m1_row(int(index) - 1)
                    if int(prior["available"]) > known_at:
                        previous_close = float(prior["close"])
                if previous_close is None:
                    candidate["previousClose"] = float(row["close"])
                    candidate["lastObservedAtUtc"] = utc_text(available)
                    candidates.append(candidate)
                    continue
            # AGENTS defines the wakeup as the predeclared root-OB approach.
            # A full zone-height offset woke Gemini while price was still far
            # from the POI and converted ordinary delivery into retrospective
            # scenario planning.  The proximal boundary itself is the only
            # non-arbitrary event price: demand is reached from above at its
            # high, supply is reached from below at its low.
            threshold = high if direction == "LONG" else low
            crossed = (
                float(previous_close) > threshold
                and float(row["low"]) <= threshold
                if direction == "LONG"
                else float(previous_close) < threshold
                and float(row["high"]) >= threshold
            )
            if status == "REGISTERED" and crossed:
                traversed_source = (
                    float(row["low"]) <= low
                    if direction == "LONG"
                    else float(row["high"]) >= high
                )
                if traversed_source:
                    candidate["status"] = "EXPIRED_APPROACH_THROUGH_SOURCE"
                    candidate["previousClose"] = float(row["close"])
                    candidate["lastObservedAtUtc"] = utc_text(available)
                    self.stats["planApproachesExpiredThroughSource"] += 1
                    self.event(
                        "LOCAL_ROOT_APPROACH_THROUGH_SOURCE",
                        available,
                        {
                            "familyId": family_id,
                            "direction": direction,
                            "rootLow": low,
                            "rootHigh": high,
                            "barId": row.get("barId"),
                            "open": float(row.get("open", row["close"])),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "apiCalled": False,
                        },
                    )
                    candidates.append(candidate)
                    continue
                eligible = state_at_bar_start == "FLAT"
                event = {
                    "familyId": family_id,
                    "direction": direction,
                    "knownAtUtc": candidate["knownAtUtc"],
                    "eventAtUtc": utc_text(available),
                    "approachSide": (
                        "FROM_ABOVE" if direction == "LONG" else "FROM_BELOW"
                    ),
                    "threshold": threshold,
                    "previousClose": float(previous_close),
                    "barId": row.get("barId"),
                    "open": float(row.get("open", row["close"])),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "eligible": eligible,
                    "blockedReason": None if eligible else "ACTIVE_SCENARIO_AT_EVENT",
                }
                candidate["approachEvent"] = event
                candidate["status"] = (
                    "APPROACH_EVENT" if eligible else "MISSED_ACTIVE_SCENARIO"
                )
                if eligible:
                    events.append(event)
                    self.stats["directionalPlanApproaches"] += 1
                else:
                    self.stats["planApproachesBlockedWhileActive"] += 1
                    self.event(
                        "LOCAL_PLAN_APPROACH_BLOCKED_ACTIVE",
                        available,
                        {**event, "apiCalled": False},
                    )
            candidate["previousClose"] = float(row["close"])
            candidate["lastObservedAtUtc"] = utc_text(available)
            candidates.append(candidate)
        self.runtime["flatPlanCandidates"] = candidates
        return events

    def schedule_event_driven_flat_plan(
        self,
        row: dict[str, Any],
        *,
        api_allowed: bool = True,
        approach_events: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Call PLAN only for a prior-known, directional M1 approach event."""
        if self.runtime["state"] != "FLAT":
            return False
        if approach_events is None:
            self.refresh_flat_plan_candidates(int(row["available"]))
            approach_events = self.advance_plan_candidate_ledger(row, "FLAT")
        eligible = [item for item in approach_events if item.get("eligible")]
        if not eligible:
            self.stats["flatPlanApproachSkips"] += 1
            return False
        if not api_allowed:
            return False
        # One API request reviews every family whose predeclared proximal was
        # reached by this same completed M1 candle. Selecting only the oldest
        # family silently discarded simultaneous alternatives.
        ordered_events = sorted(
            eligible,
            key=lambda item: (parse_utc(str(item["knownAtUtc"])), str(item["familyId"])),
        )
        event = ordered_events[0]
        approaching = {str(item["familyId"]) for item in ordered_events}
        authority_key = self.external_authority_key(
            self.runtime.get("externalMapAuthority")
        )
        current_close = float(row["close"])
        active_candidates = [
            item for item in self.runtime.get("flatPlanCandidates", [])
            if item.get("status") in {"REGISTERED", "APPROACH_EVENT"}
        ]
        active_candidates.sort(
            key=lambda item: min(
                abs(current_close - float(item["rootLow"])),
                abs(current_close - float(item["rootHigh"])),
            )
        )
        candidate_context = []
        for item in active_candidates[:24]:
            low = float(item["rootLow"])
            high = float(item["rootHigh"])
            candidate_context.append({
                key: item.get(key)
                for key in (
                    "familyId", "direction", "knownAtUtc", "status",
                    "rootLow", "rootHigh", "lastObservedAtUtc",
                )
            } | {
                "currentClose": current_close,
                "distanceToRoot": (
                    low - current_close if current_close < low
                    else current_close - high if current_close > high
                    else 0.0
                ),
            })
        focused_root_ids = {
            str(item["rootBarId"])
            for item in self.runtime.get("flatPlanCandidates", [])
            if str(item["familyId"]) in approaching and item.get("rootBarId")
        }
        packet = build_plan_packet(
            self.market,
            int(row["available"]),
            str(self.config["symbol"]),
            focus_family_ids=approaching,
            focus_root_bar_ids=focused_root_ids or None,
            external_authority=self.runtime.get("externalMapAuthority"),
            approach_event=event,
            approach_events=ordered_events,
            candidate_context=candidate_context,
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
        for candidate in self.runtime.get("flatPlanCandidates", []):
            if str(candidate["familyId"]) in approaching:
                candidate["status"] = "EVALUATED"
        fingerprint = canonical_hash(
            {
                "authorityKey": authority_key,
                "familyIds": sorted(approaching),
            }
        )
        self.stats["flatPlanWakeups"] += 1
        self.event(
            "LOCAL_ROOT_APPROACH_PLAN_SCHEDULED",
            int(row["available"]),
            {
                "familyIds": sorted(approaching),
                "authorityKey": authority_key,
                "approachEvent": event,
                "approachEvents": ordered_events,
                "apiCalled": True,
            },
        )
        self.request_plan(
            int(row["available"]),
            packet=packet,
            plan_fingerprint=fingerprint,
        )
        return True

    def latest_h1_available(self, as_of: int) -> int | None:
        rows = self.market.bars("H1", as_of, 1)
        return int(rows[-1]["available"]) if rows else None

    def latest_m5_available(self, as_of: int) -> int | None:
        rows = self.market.bars("M5", as_of, 1)
        return int(rows[-1]["available"]) if rows else None

    def schedule_flat_plan(self, as_of: int, *, api_allowed: bool = True) -> bool:
        """Review only when a newly closed M5 bar changes the causal family set.

        PLAN is a map decision, not a root-proximity callback.  The model sees
        every currently viable family together and may freeze only one.  Once a
        scenario is active this scheduler is silent until local invalidation or
        trade completion returns the runtime to FLAT.
        """
        if self.runtime["state"] != "FLAT":
            return False
        self.stats["flatPlanSchedulerChecks"] += 1
        latest_m5_available = self.latest_m5_available(as_of)
        if latest_m5_available is None:
            return False
        if self.runtime.get("lastPlanM5Available") == latest_m5_available:
            self.stats["localMapSkips"] += 1
            return False
        if not api_allowed:
            return False
        local_evidence_fingerprint = discovery_event_fingerprint(
            self.market,
            as_of,
            self.runtime.get("externalMapAuthority"),
        )
        if (
            self.runtime.get("lastLocalDiscoveryFingerprint")
            == local_evidence_fingerprint
        ):
            self.runtime["lastPlanM5Available"] = latest_m5_available
            self.stats["flatLocalEvidenceSkips"] += 1
            return False
        packet = build_plan_packet(
            self.market,
            as_of,
            str(self.config["symbol"]),
            external_authority=self.runtime.get("externalMapAuthority"),
        )
        self.sync_resolved_authority(packet.get("externalMapAuthority"), as_of)
        self.record_discovery_diagnostics(packet, as_of)
        latest_h1_available = self.latest_h1_available(as_of)
        if not packet.get("physicalLineageFamilies"):
            self.runtime["lastPlanM5Available"] = latest_m5_available
            self.runtime["lastLocalDiscoveryFingerprint"] = local_evidence_fingerprint
            self.runtime["lastPlanH1Available"] = latest_h1_available
            self.stats["flatPlanEmptySkips"] += 1
            self.event(
                "LOCAL_PLAN_SKIPPED_NO_FAMILY",
                as_of,
                {
                    "apiCalled": False,
                    "diagnostics": packet.get("discoveryDiagnostics"),
                },
            )
            return False
        authority_key = self.external_authority_key(
            packet.get("externalMapAuthority")
        )
        fingerprint = self.flat_plan_fingerprint(packet)
        evaluated = set(self.runtime.get("evaluatedFlatPlanFingerprints", []))
        if fingerprint in evaluated:
            self.runtime["lastPlanM5Available"] = latest_m5_available
            self.runtime["lastLocalDiscoveryFingerprint"] = local_evidence_fingerprint
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
        self.runtime["lastPlanM5Available"] = latest_m5_available
        self.runtime["lastLocalDiscoveryFingerprint"] = local_evidence_fingerprint
        return True

    def request_refinement(self, as_of: int) -> None:
        raise V4ContractError(
            "LEGACY_CONTRACT_DISABLED_V451: REFINEMENT is integrated into PLAN"
        )
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

    def compact_plan_page(
        self,
        packet: dict[str, Any],
        families: list[dict[str, Any]],
        as_of: int,
    ) -> dict[str, Any]:
        """Build lossless family-local OHLC evidence for one PLAN page."""
        projected_families: list[dict[str, Any]] = []
        objective_role_ids: set[str] = set()
        for family in families:
            options: list[dict[str, Any]] = []
            for raw_option in family.get("scenarioOptions", []):
                option = deepcopy(raw_option)
                objective_family = option.get("objectiveFamily")
                if objective_family is None:
                    objective = option.get("objective") or {}
                    if objective.get("barId"):
                        objective_role_ids.add(str(objective["barId"]))
                    options.append(option)
                    continue
                compact_members = []
                for raw_member in objective_family.get("orderedMembers", []):
                    member = {
                        key: raw_member.get(key)
                        for key in (
                            "barId", "side", "price", "matureAtUtc",
                        )
                        if raw_member.get(key) is not None
                    }
                    compact_members.append(member)
                    objective_role_ids.add(str(raw_member["barId"]))
                option["objectiveFamily"] = {
                    "objectiveFamilyId": objective_family.get("objectiveFamilyId"),
                    "orderedMembers": compact_members,
                }
                options.append(option)
            selected_path_ids = {
                str(option.get("lineagePathSelectionId")) for option in options
            }
            projected_families.append({
                key: family.get(key)
                for key in (
                    "familyId", "direction", "rootBarId",
                    "initialDisplacementBarId", "rootDisplacementEpisodeBarIds",
                    "externalAuthorityAtDecision",
                )
            } | {
                "lineagePathOptions": [
                    path for path in family.get("lineagePathOptions", [])
                    if str(path.get("pathSelectionId")) in selected_path_ids
                ],
                "scenarioOptions": options,
            })
        families = projected_families
        bar_pattern = re.compile(r"^(H1|M30|M15|M5|M1):\d+$")
        role_ids: set[str] = set()

        def visit(value: Any) -> None:
            if isinstance(value, str) and bar_pattern.match(value):
                role_ids.add(value)
            elif isinstance(value, dict):
                for nested in value.values():
                    visit(nested)
            elif isinstance(value, list):
                for nested in value:
                    visit(nested)

        visit(families)
        rows_by_tf: dict[str, dict[str, dict[str, Any]]] = {
            timeframe: {} for timeframe in ("H1", "M30", "M15", "M5")
        }
        # PLAN is intentionally HTF/LTF-map only. M1 event metadata may exist
        # on a discovery family, but exposing its candles would violate the
        # trigger-after-child-touch boundary.
        role_ids = {
            role_id
            for role_id in role_ids
            if split_bar_id(role_id)[0] in rows_by_tf
        }
        # Family pages carry every role and displacement-episode candle.  The
        # generic recent context is deliberately small so it cannot crowd out
        # causal evidence; oversized role sets are split by the sub-page layer.
        for timeframe, count in (("H1", 8), ("M30", 12), ("M15", 16), ("M5", 24)):
            for row in self.market.bars(timeframe, as_of, count):
                rows_by_tf[timeframe][str(row["barId"])] = row
        for role_id in sorted(role_ids):
            timeframe, timestamp = split_bar_id(role_id)
            if timeframe not in rows_by_tf:
                continue
            role = self.market.bar(role_id, as_of)
            if role_id in objective_role_ids:
                rows_by_tf[timeframe][role_id] = role
                continue
            series = self.market.frames[timeframe]
            left = max(0, int(role["index"]) - 3)
            right = min(len(series.time), int(role["index"]) + 5)
            for index in range(left, right):
                if int(series.available_time[index]) > int(as_of):
                    continue
                candidate_id = f"{timeframe}:{int(series.time[index])}"
                candidate = self.market.bar(candidate_id, as_of)
                rows_by_tf[timeframe][candidate_id] = candidate
        compact = {
            "columns": ["barId", "open", "high", "low", "close"],
            "data": {
                timeframe: [
                    [
                        row["barId"],
                        round(float(row["open"]), 5),
                        round(float(row["high"]), 5),
                        round(float(row["low"]), 5),
                        round(float(row["close"]), 5),
                    ]
                    for row in sorted(values.values(), key=lambda item: item["time"])
                ]
                for timeframe, values in rows_by_tf.items()
            },
        }
        supplied_ids = {
            str(row[0])
            for rows in compact["data"].values()
            for row in rows
        }
        missing = sorted(role_ids - supplied_ids)
        if missing:
            raise V4ContractError(
                "PLAN page omitted role OHLC IDs: " + ",".join(missing[:12])
            )
        return {
            **packet,
            "physicalLineageFamilies": families,
            # Objective and protected-swing metadata are already embedded in
            # the selected scenario/path projection and every referenced bar
            # is present in `bars`. Repeating the full lifecycle records here
            # can multiply a lossless objective page by hundreds of kilobytes.
            "swingCandidates": [],
            "bars": compact,
            "roleEvidenceAudit": {
                "requiredRoleIds": sorted(role_ids),
                "suppliedRoleIdsHash": canonical_hash(sorted(supplied_ids)),
                "missingRoleIds": [],
            },
        }

    def deterministic_plan_subpages(
        self,
        packet: dict[str, Any],
        family: dict[str, Any],
        as_of: int,
    ) -> list[dict[str, Any]]:
        """Partition one oversized family without dropping selectable options."""
        options = list(family.get("scenarioOptions", []))
        if not options:
            raise V4ContractError("oversized PLAN family has no scenario options")
        maximum = int(self.config.get("maximumPlanPromptBytes", 64000))
        groups: list[list[dict[str, Any]]] = []
        start = 0
        while start < len(options):
            best_end: int | None = None
            low = start + 1
            high = len(options)
            while low <= high:
                end = (low + high) // 2
                trial = options[start:end]
                path_ids = {str(item.get("lineagePathSelectionId")) for item in trial}
                fragment_family = {
                    **family,
                    "scenarioOptions": trial,
                    "lineagePathOptions": [
                        item for item in family.get("lineagePathOptions", [])
                        if str(item.get("pathSelectionId")) in path_ids
                    ],
                }
                # Account for the metadata added to the final page.  The old
                # partition measured the packet before adding `subPage`, which
                # allowed a page only a few bytes over the hard provider bound.
                trial_packet = {
                    **self.compact_plan_page(packet, [fragment_family], as_of),
                    "subPage": {
                        "kind": "LOSSLESS_SCENARIO_OPTIONS",
                        "index": 999999,
                        "count": 999999,
                        "sourceFamilyId": str(family["familyId"]),
                        "sourceFamilyHash": canonical_hash(family),
                        "allScenarioOptionIdsHash": canonical_hash([
                            str(item["scenarioSelectionId"]) for item in options
                        ]),
                    },
                }
                if len(prompt_for("PLAN", trial_packet).encode("utf-8")) <= maximum:
                    best_end = end
                    low = end + 1
                else:
                    high = end - 1
            if best_end is None:
                raise V4ContractError(
                    "PLAN single-option evidence exceeds maximumPlanPromptBytes; "
                    "lossless sub-page cannot be formed"
                )
            groups.append(options[start:best_end])
            start = best_end
        all_option_ids = [
            str(item["scenarioSelectionId"]) for group in groups for item in group
        ]
        expected_ids = [str(item["scenarioSelectionId"]) for item in options]
        if all_option_ids != expected_ids:
            raise V4ContractError("PLAN sub-page partition lost or reordered options")
        family_hash = canonical_hash(family)
        output: list[dict[str, Any]] = []
        for index, group in enumerate(groups, 1):
            path_ids = {str(item.get("lineagePathSelectionId")) for item in group}
            fragment = {
                **family,
                "scenarioOptions": group,
                "lineagePathOptions": [
                    item for item in family.get("lineagePathOptions", [])
                    if str(item.get("pathSelectionId")) in path_ids
                ],
            }
            output.append({
                **self.compact_plan_page(packet, [fragment], as_of),
                "subPage": {
                    "kind": "LOSSLESS_SCENARIO_OPTIONS",
                    "index": index,
                    "count": len(groups),
                    "sourceFamilyId": str(family["familyId"]),
                    "sourceFamilyHash": family_hash,
                    "allScenarioOptionIdsHash": canonical_hash(expected_ids),
                },
            })
        oversized = [
            len(prompt_for("PLAN", page).encode("utf-8"))
            for page in output
            if len(prompt_for("PLAN", page).encode("utf-8")) > maximum
        ]
        if oversized:
            raise V4ContractError(
                "PLAN sub-page final serialization exceeds maximumPlanPromptBytes"
            )
        return output

    def commit_plan_scenarios(
        self,
        scenarios: list[dict[str, Any]],
        as_of: int,
        request_id: str,
    ) -> list[str]:
        """Commit already validated PLAN scenarios exactly once per source family."""
        accepted_ids: list[str] = []
        existing_source_keys = {
            str(item.get("sourceFamilyKey"))
            for item in self.runtime.get("scenarioSlots", [])
        }
        for scenario in scenarios:
            source_key = self.source_family_key(scenario)
            if source_key in existing_source_keys:
                self.event(
                    "PLAN_DUPLICATE_SOURCE_FAMILY_SKIPPED",
                    as_of,
                    {
                        "requestId": request_id,
                        "familyId": scenario.get("physicalFamilyId"),
                        "sourceFamilyKey": source_key,
                        "apiCalled": False,
                    },
                )
                continue
            scenario["semanticReadyAtUtc"] = self.semantic_ready_at(
                request_id, as_of
            )
            previous_authority = self.runtime.get("externalMapAuthority")
            try:
                if (
                    isinstance(previous_authority, dict)
                    and str(previous_authority.get("status", "ACTIVE")) == "ACTIVE"
                    and str(previous_authority.get("direction"))
                    != str(scenario.get("direction"))
                ):
                    raise V4ContractError(
                        "opposing watch lane cannot own risk while external owner is intact"
                    )
                next_authority = external_authority_from_scenario(
                    scenario, previous_authority
                )
            except V4ContractError as exc:
                scenario["ownerEpoch"] = int(self.runtime.get("ownerEpoch", 0))
                scenario["ownerStatus"] = "CHALLENGER"
                self.event(
                    "PLAN_CHALLENGER_RETAINED",
                    as_of,
                    {
                        "requestId": request_id,
                        "familyId": scenario.get("physicalFamilyId"),
                        "reason": str(exc),
                    },
                )
            else:
                self.sync_resolved_authority(next_authority, as_of)
                scenario["ownerEpoch"] = int(self.runtime.get("ownerEpoch", 0))
                scenario["ownerStatus"] = "ACTIVE"
            self.runtime["acceptedScenarioHashes"].append(scenario["scenarioHash"])
            self.runtime["apiCallsByScenario"][scenario["scenarioHash"]] = 1
            self.append_scenario_slot(scenario, as_of)
            existing_source_keys.add(source_key)
            accepted_ids.append(str(scenario.get("physicalFamilyId")))
        return accepted_ids

    def request_plan(
        self,
        as_of: int,
        focus_family_ids: set[str] | None = None,
        *,
        packet: dict[str, Any] | None = None,
        plan_fingerprint: str | None = None,
        challenger: bool = False,
        superseding: bool = False,
        collect_only: bool = False,
    ) -> list[dict[str, Any]] | None:
        prior = None
        if superseding and not challenger:
            raise V4ContractError("PLAN supersession requires challenger mode")
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
        if not packet.get("subPage"):
            packet = self.filter_locked_source_families(packet, as_of)
        maximum_page = max(1, int(self.config.get("maximumPlanFamiliesPerPage", 8)))
        families = list(packet.get("physicalLineageFamilies", []))
        if len(families) > maximum_page:
            page_count = (len(families) + maximum_page - 1) // maximum_page
            all_ids: list[str] = []
            for page_index in range(page_count):
                page_families = families[
                    page_index * maximum_page:(page_index + 1) * maximum_page
                ]
                all_ids.extend(str(item["familyId"]) for item in page_families)
                page_packet = {
                    **self.compact_plan_page(packet, page_families, as_of),
                    "page": {
                        "index": page_index + 1,
                        "count": page_count,
                        "allFamilyIdsHash": canonical_hash(
                            [str(item["familyId"]) for item in families]
                        ),
                    },
                }
                self.request_plan(
                    as_of,
                    packet=page_packet,
                    plan_fingerprint=(
                        f"{plan_fingerprint or self.flat_plan_fingerprint(packet)}:"
                        f"page-{page_index + 1}-of-{page_count}"
                    ),
                    challenger=challenger,
                    superseding=superseding,
                )
            if set(all_ids) != {str(item["familyId"]) for item in families}:
                raise V4ContractError("PLAN paging lost or duplicated family IDs")
            return
        if len(families) == 1 and not packet.get("subPage"):
            full_page = self.compact_plan_page(packet, families, as_of)
            if len(prompt_for("PLAN", full_page).encode("utf-8")) > int(
                self.config.get("maximumPlanPromptBytes", 64000)
            ):
                subpages = self.deterministic_plan_subpages(
                    packet, families[0], as_of
                )
                runtime_before = deepcopy(self.runtime)
                ledger_path = self.run_dir / "decision_ledger.jsonl"
                ledger_bytes = ledger_path.stat().st_size if ledger_path.exists() else 0
                collected_scenarios: list[dict[str, Any]] = []
                try:
                    for subpage in subpages:
                        page_scenarios = self.request_plan(
                            as_of,
                            packet=subpage,
                            plan_fingerprint=(
                                f"{plan_fingerprint or self.flat_plan_fingerprint(packet)}:"
                                f"subpage-{subpage['subPage']['index']}-of-"
                                f"{subpage['subPage']['count']}"
                            ),
                            challenger=challenger,
                            superseding=superseding,
                            collect_only=True,
                        )
                        collected_scenarios.extend(page_scenarios or [])
                except Exception:
                    self.runtime = runtime_before
                    if ledger_path.exists():
                        with ledger_path.open("r+b") as handle:
                            handle.truncate(ledger_bytes)
                    self.ledger = HashLedger(ledger_path)
                    self.save()
                    raise
                unique_scenarios = {
                    str(item["scenarioHash"]): item for item in collected_scenarios
                }
                if len(unique_scenarios) > 1:
                    self.event(
                        "PLAN_FAMILY_SUBPAGES_UNRESOLVED",
                        as_of,
                        {
                            "sourceFamilyId": str(families[0]["familyId"]),
                            "approvedScenarioHashes": sorted(unique_scenarios),
                            "reason": "MULTIPLE_APPROVED_OPTIONS_ACROSS_SUBPAGES",
                            "apiCalled": False,
                        },
                    )
                elif len(unique_scenarios) == 1:
                    scenario = next(iter(unique_scenarios.values()))
                    semantic_request_id = str(
                        scenario.pop("_semanticRequestId", "subpage-aggregate")
                    )
                    self.commit_plan_scenarios(
                        [scenario], as_of, semantic_request_id
                    )
                self.event(
                    "PLAN_FAMILY_SUBPAGES_COMMITTED",
                    as_of,
                    {
                        "sourceFamilyId": str(families[0]["familyId"]),
                        "sourceFamilyHash": canonical_hash(families[0]),
                        "pageCount": len(subpages),
                        "allPagesCompleted": True,
                    },
                )
                return [] if collect_only else None
        packet = self.compact_plan_page(packet, families, as_of)
        if not packet.get("physicalLineageFamilies"):
            self.event(
                "LOCAL_PLAN_SKIPPED_SOURCE_FAMILY_LOCK",
                as_of,
                {"apiCalled": False},
            )
            return
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
        )
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
        )
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
        )
        self.event("PLAN_RESPONSE", as_of, {"requestId": request_id, "cacheHit": cache_hit, "payload": payload})
        if payload.get("schemaVersion") == "5.0.0":
            try:
                scenarios = freeze_plan_batch(
                    payload,
                    self.market,
                    as_of,
                    packet,
                    set(self.runtime["acceptedScenarioHashes"]),
                )
            except V4ContractError as exc:
                if (
                    "family-set mismatch" in str(exc)
                    or "duplicate family decisions" in str(exc)
                ):
                    self.event(
                        "PLAN_PAGE_INCOMPLETE_RETRY",
                        as_of,
                        {"requestId": request_id, "reason": str(exc)},
                    )
                    retry_payload, retry_id, retry_cache_hit = self._request(
                        "PLAN",
                        as_of,
                        packet,
                        plan_schema(packet),
                        images,
                        allow_plan_challenger=challenger,
                    )
                    if retry_id != request_id:
                        raise V4ContractError(
                            "PLAN retry changed the content hash"
                        )
                    self.event(
                        "PLAN_RESPONSE_RETRY",
                        as_of,
                        {
                            "requestId": retry_id,
                            "cacheHit": retry_cache_hit,
                            "payload": retry_payload,
                        },
                    )
                    scenarios = freeze_plan_batch(
                        retry_payload,
                        self.market,
                        as_of,
                        packet,
                        set(self.runtime["acceptedScenarioHashes"]),
                    )
                    payload = retry_payload
                else:
                    self.event(
                        "PLAN_PAGE_REJECTED",
                        as_of,
                        {"requestId": request_id, "reason": str(exc)},
                    )
                    raise
            self.promote_response_cache(request_id)
            if collect_only:
                for scenario in scenarios:
                    scenario["_semanticRequestId"] = request_id
                return scenarios
            accepted_ids: list[str] = []
            accepted_ids.extend(
                self.commit_plan_scenarios(scenarios, as_of, request_id)
            )
            self.event(
                "PLAN_PAGE_COMPLETED",
                as_of,
                {
                    "requestId": request_id,
                    "inputFamilyIds": [
                        str(item["familyId"])
                        for item in packet.get("physicalLineageFamilies", [])
                    ],
                    "acceptedFamilyIds": accepted_ids,
                },
            )
            return [] if collect_only else None
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
        scenario["semanticReadyAtUtc"] = self.semantic_ready_at(request_id, as_of)
        selected_family_id = next(
            (
                str(family["familyId"])
                for family in packet.get("physicalLineageFamilies", [])
                if any(
                    str(option.get("scenarioSelectionId"))
                    == str(payload.get("scenarioSelectionId"))
                    for option in family.get("scenarioOptions", [])
                )
            ),
            None,
        )
        if selected_family_id is not None:
            scenario["physicalFamilyId"] = selected_family_id
            self.runtime["deferredPlanEvents"] = [
                item for item in self.runtime.get("deferredPlanEvents", [])
                if str(item.get("familyId")) != selected_family_id
            ]
        previous_authority = (
            packet.get("externalMapAuthority")
            if packet.get("externalMapAuthority") is not None
            else self.runtime.get("externalMapAuthority")
        )
        try:
            if superseding and scenario["scope"] != "INTERNAL_ROTATION":
                # The scheduler has already proven same owner/scope and the
                # same physical objective within current spread. Rebuild the
                # authority from the newer causal map instead of rejecting it
                # merely because its bar IDs are more precise.
                next_authority = external_authority_from_scenario(scenario, None)
            else:
                next_authority = external_authority_from_scenario(
                    scenario, previous_authority
                )
        except V4ContractError as exc:
            next_authority = previous_authority
            scenario["ownerEpoch"] = int(self.runtime.get("ownerEpoch", 0))
            scenario["ownerStatus"] = "CHALLENGER"
            self.event(
                "PLAN_CHALLENGER_RETAINED",
                as_of,
                {"requestId": request_id, "reason": str(exc)},
            )
        else:
            self.sync_resolved_authority(next_authority, as_of)
            scenario["ownerEpoch"] = int(self.runtime.get("ownerEpoch", 0))
            scenario["ownerStatus"] = "ACTIVE"

        parked_scenario_hash: str | None = None
        replaced_scenario_hash: str | None = None
        if challenger and prior is not None:
            if superseding:
                replaced_scenario_hash = str(prior["scenario"]["scenarioHash"])
            elif scenario["scope"] == "EXTERNAL_REVERSAL":
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
        if (
            previous_authority
            and str(previous_authority.get("status")) == "REMAP_REQUIRED"
            and next_authority
            and str(next_authority.get("status")) == "ACTIVE"
        ):
            self.stats["authorityTransitions"] += 1
            self.event(
                "EXTERNAL_AUTHORITY_REESTABLISHED",
                as_of,
                {
                    "previousDirection": previous_authority.get("direction"),
                    "newDirection": next_authority.get("direction"),
                    "scope": scenario.get("scope"),
                    "bodyBreakBarId": previous_authority.get("bodyBreakBarId"),
                    "apiCalled": False,
                },
            )
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
                (
                    "ACTIVE_SCENARIO_SUPERSEDED_BY_CAUSAL_FAMILY"
                    if superseding
                    else "ACTIVE_SCENARIO_REPLACED_BY_EXTERNAL_REVERSAL"
                ),
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
        scenario_hash = scenario["scenarioHash"]
        self.runtime["apiCallsByScenario"][scenario_hash] = (
            int(self.runtime["apiCallsByScenario"].get(scenario_hash, 1)) + 1
        )

        def reject_current_execution_chain(reason: str) -> None:
            rejected = list(monitor.get("rejectedChochBreakBarIds", []))
            rejected.extend(
                str(item["breakBarId"])
                for item in (choch_break_candidates or [])
                if item.get("breakBarId")
            )
            monitor["rejectedChochBreakBarIds"] = list(dict.fromkeys(rejected))
            rejected_sweeps = list(monitor.get("rejectedSweepEventIds", []))
            rejected_sweeps.extend(
                "|".join((
                    str(item.get("liquidityBarId")),
                    str(item.get("excursionBarId")),
                    str(item.get("recoveryBarId")),
                ))
                for item in (sweep_events or [])
            )
            monitor["rejectedSweepEventIds"] = list(
                dict.fromkeys(rejected_sweeps)
            )
            self.runtime["reactionMonitor"] = monitor
            self.runtime["triggerWatch"] = None
            self.runtime["state"] = "REACTION_MONITOR"
            self.event(
                "TRIGGER_EXECUTION_CHAIN_REJECTED",
                as_of,
                {
                    "scenarioHash": scenario_hash,
                    "reason": reason,
                    "rejectedChochBreakBarIds": monitor[
                        "rejectedChochBreakBarIds"
                    ],
                    "rejectedSweepEventIds": monitor[
                        "rejectedSweepEventIds"
                    ],
                    "sourceFamilyPreserved": True,
                },
            )
            self.save()
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
            reject_current_execution_chain(str(exc))
            return
        self.promote_response_cache(request_id)
        if watch is None:
            reject_current_execution_chain(
                f"TRIGGER_WATCH_{payload['action']}: {payload['reason']}"
            )
            return
        semantic_ready = self.semantic_ready_at(request_id, as_of)
        watch["semanticReadyAtUtc"] = semantic_ready
        apply_source_upgrade(scenario, watch)
        self.runtime["reactionMonitor"] = None
        self.runtime["triggerWatch"] = watch
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
        try:
            order = build_order(
                self.market,
                scenario,
                watch,
                execution,
                break_bar,
                float(self.config["brokerStopsLevelPrice"]),
            )
        except V4ContractError as exc:
            if str(exc).startswith("INTERNAL_OBJECTIVE_"):
                self.stats["ordersBlockedObjectiveContract"] += 1
                self.cancel(
                    as_of,
                    "OBJECTIVE_CONTRACT_FAILED_AT_ORDER",
                    {"reason": str(exc)},
                )
                return
            raise
        order["semanticReadyAtUtc"] = semantic_ready
        order["brokerAuthorizedAtUtc"] = self.broker_authorized_at(
            semantic_ready
        )
        self.runtime["order"] = order
        self.runtime["state"] = "PENDING"
        self.register_order_record(order, as_of)
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
        cancellation_reasons = self.stats["cancellationReasons"]
        cancellation_reasons[reason] = int(cancellation_reasons.get(reason, 0)) + 1
        scenario_hash = self.runtime.get("scenario", {}).get("scenarioHash") if self.runtime.get("scenario") else None
        active_order = self.runtime.get("order")
        if isinstance(active_order, dict):
            for record in self.runtime.setdefault("orders", []):
                if record.get("orderId") == active_order.get("orderId"):
                    record.update({
                        "status": "CANCELED",
                        "canceledAtUtc": utc_text(as_of),
                        "reason": reason,
                    })
        if scenario_hash:
            updated_shadows: list[dict[str, Any]] = []
            for candidate in self.runtime.get("shadowDeliveryCandidates", []):
                if (
                    candidate.get("scenarioHash") == scenario_hash
                    and candidate.get("status") == "WAIT_FIRST_RETEST"
                ):
                    candidate = {
                        **candidate,
                        "status": "INVALIDATED",
                        "closedAtUtc": utc_text(as_of),
                        "invalidationReason": reason,
                    }
                    self.event(
                        "SHADOW_DELIVERY_CANCELED",
                        as_of,
                        {
                            "shadowId": candidate["shadowId"],
                            "reason": reason,
                            "apiCalled": False,
                        },
                    )
                updated_shadows.append(candidate)
            self.runtime["shadowDeliveryCandidates"] = updated_shadows
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
            "objectiveBarId": (
                (self.runtime.get("order") or {}).get("selectedObjective")
                or scenario["objective"]
            )["barId"],
        }
        self.trades.append(enriched)
        if enriched.get("outcome") == "TP" and scenario.get("physicalFamilyId"):
            family_id = str(scenario["physicalFamilyId"])
            self.runtime["completedDeliveryFamilyIds"] = list(dict.fromkeys([
                *self.runtime.get("completedDeliveryFamilyIds", []), family_id,
            ]))
            self.runtime["deferredPlanEvents"] = [
                item for item in self.runtime.get("deferredPlanEvents", [])
                if str(item.get("familyId")) != family_id
            ]
            self.event(
                "CAUSAL_SOURCE_DELIVERY_COMPLETED",
                as_of,
                {
                    "familyId": family_id,
                    "objectiveBarId": scenario["objective"]["barId"],
                    "apiCalled": False,
                },
            )
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
        authority = self.runtime.get("externalMapAuthority") or {}
        scenario = self.runtime.get("scenario") or {}
        if (
            scenario.get("ownerStatus") == "CHALLENGER"
            and authority.get("status") == "ACTIVE"
            and str(authority.get("direction")) == str(scenario.get("direction"))
        ):
            scenario["ownerStatus"] = "ACTIVE"
            scenario["ownerEpoch"] = int(self.runtime.get("ownerEpoch", 0))
            self.event(
                "CHALLENGER_OWNER_CONFIRMED_LOCALLY",
                row["available"],
                {
                    "scenarioHash": scenario.get("scenarioHash"),
                    "ownerEpoch": scenario["ownerEpoch"],
                    "apiCalled": False,
                },
            )
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
        semantic_ready = scenario.get("semanticReadyAtUtc")
        if semantic_ready:
            ready_at = parse_utc(str(semantic_ready))
            row_start = int(row.get("time", int(row["available"]) - 60))
            if row_start < ready_at <= int(row["available"]):
                self.cancel(
                    row["available"],
                    "LATENCY_INTRABAR_AMBIGUOUS",
                    {"stage": "PLAN_TO_CHILD_TOUCH", "semanticReadyAtUtc": semantic_ready},
                )
                return True
            if int(row["available"]) <= ready_at:
                self.cancel(
                    row["available"],
                    "MISSED_API_LATENCY",
                    {"stage": "PLAN_TO_CHILD_TOUCH", "semanticReadyAtUtc": semantic_ready},
                )
                return True
        if zone_distal_crossed(row, child, scenario["direction"], body=False):
            self.cancel(row["available"], "POI_FULLY_CONSUMED_ON_TOUCH")
            return True
        scenario["childTouchAtUtc"] = utc_text(row["available"])
        scenario["childTouchBarId"] = row["barId"]
        self.runtime["reactionMonitor"] = build_reaction_monitor(
            self.market, scenario, row["available"]
        )
        self.runtime["state"] = "REACTION_MONITOR"
        self.stats["childTouches"] += 1
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

    def advance_shadow_deliveries(self, row: dict[str, Any]) -> None:
        updated: list[dict[str, Any]] = []
        for candidate in self.runtime.get("shadowDeliveryCandidates", []):
            advanced, event_name = advance_shadow_delivery_candidate(
                self.market, candidate, row
            )
            if event_name:
                if event_name == "FILLED":
                    self.stats["shadowDeliveryFilled"] += 1
                elif event_name == "TP":
                    self.stats["shadowDeliveryTp"] += 1
                elif event_name == "SL":
                    self.stats["shadowDeliverySl"] += 1
                self.event(
                    f"SHADOW_DELIVERY_{event_name}",
                    row["available"],
                    {
                        "shadowId": advanced["shadowId"],
                        "candidate": advanced,
                        "apiCalled": False,
                    },
                )
            updated.append(advanced)
        self.runtime["shadowDeliveryCandidates"] = updated

    @staticmethod
    def delivery_review_fingerprint(
        scenario: dict[str, Any], candidate: dict[str, Any]
    ) -> str:
        confirmation = candidate["deliveryConfirmation"]
        return canonical_hash(
            {
                "scenarioHash": scenario["scenarioHash"],
                "executionModel": candidate.get("executionModel"),
                "sourcePositionOrderId": candidate.get("sourcePositionOrderId"),
                "confirmationMode": confirmation["mode"],
                "confirmationBarId": confirmation["barId"],
            }
        )

    @staticmethod
    def physical_delivery_key(candidate: dict[str, Any]) -> str:
        return canonical_hash({
            "direction": candidate.get("direction"),
            "formedBarId": candidate.get("formedBarId"),
            "causalObBarId": candidate.get("causalObBarId"),
            "transferSwingBarId": candidate.get("transferSwingBarId"),
            "fvg": candidate.get("fvg"),
        })

    def prepare_delivery_candidates(self, row: dict[str, Any]) -> None:
        """Detect each physical Delivery FVG once before lane processing.

        A single physical FVG that is explained by more than one active frozen
        lineage is not assigned to whichever lane happens to run first.  All
        such lanes are blocked before any semantic API request is made.
        """
        self._delivery_candidate_cache = {}
        self._blocked_delivery_physical_keys = set()
        grouped: dict[str, list[tuple[str, str]]] = {}
        for slot in self.runtime.get("scenarioSlots", []):
            if str(slot.get("state")) != "PLANNED":
                continue
            scenario = slot.get("scenario")
            if not isinstance(scenario, dict) or zone_touched(
                row, scenario["finalChild"]
            ):
                continue
            candidate = detect_pre_touch_delivery_candidate(
                self.market,
                scenario,
                row,
                float(self.config["brokerStopsLevelPrice"]),
            )
            slot_id = str(slot["slotId"])
            self._delivery_candidate_cache[slot_id] = candidate
            if candidate is None:
                continue
            physical_key = self.physical_delivery_key(candidate)
            grouped.setdefault(physical_key, []).append(
                (slot_id, str(scenario["scenarioHash"]))
            )
        for physical_key, owners in grouped.items():
            if len({scenario_hash for _, scenario_hash in owners}) > 1:
                self._blocked_delivery_physical_keys.add(physical_key)
                self.event(
                    "DELIVERY_FVG_REPLACEMENT_BLOCKED_UNRESOLVED_LINEAGE",
                    int(row["available"]),
                    {
                        "physicalDeliveryKey": physical_key,
                        "slotIds": [slot_id for slot_id, _ in owners],
                        "scenarioHashes": [scenario_hash for _, scenario_hash in owners],
                        "apiCalled": False,
                    },
                )

    def request_delivery_review(
        self,
        row: dict[str, Any],
        candidate: dict[str, Any],
        *,
        scenario_override: dict[str, Any] | None = None,
    ) -> bool:
        scenario = scenario_override or self.runtime["scenario"]
        execution_model = str(
            candidate.get("executionModel", "DELIVERY_FVG_REPLACEMENT")
        )
        approve_action = (
            "APPROVE_ADDON"
            if execution_model == "DELIVERY_FVG_ADDON"
            else "APPROVE_REPLACEMENT"
        )
        fingerprint = self.delivery_review_fingerprint(scenario, candidate)
        prior = next(
            (
                item
                for item in self.runtime.get("deliveryReviewHistory", [])
                if item.get("fingerprint") == fingerprint
            ),
            None,
        )
        if prior is not None:
            return prior.get("action") == approve_action

        packet = {
            "schemaVersion": "4.61.0",
            "phase": "DELIVERY_REVIEW",
            "decisionAtUtc": utc_text(row["available"]),
            "frozenScenario": {
                key: scenario[key]
                for key in (
                    "scenarioHash", "frozenAtUtc", "lastReauthorizedAtUtc",
                    "direction", "scope", "dealingRange", "objective",
                    "objectiveFamily",
                    "mapProtectedSwing", "root", "refinements", "finalChild",
                    "intermediateLiquidityBarIds",
                )
            },
            "candidate": candidate,
            "bars": self.market.compact(
                row["available"],
                {"H1": 48, "M30": 48, "M15": 64, "M5": 96, "M1": 120},
            ),
            "engineBoundary": (
                "The engine has validated raw FVG geometry, later first-retest availability, "
                "broker geometry, local blocking liquidity, and a hard SL outside the most conservative "
                "boundary among the causal OB, protected swing, and original final-child invalidation "
                "plus the frozen spread/stops/tick buffer. FVG distal is zone and through-delivery "
                "evidence rather than the sole replacement SL geometry. The model "
                "alone judges whether the supplied structure "
                "transfer and local invalidation still belong to the frozen causal source episode."
            ),
        }
        image_dir = self.run_dir / "delivery_review_images" / candidate["shadowId"]
        images = render_images(
            self.config, "DELIVERY_REVIEW", row["available"], image_dir
        )
        payload, request_id, cache_hit = self._request(
            "DELIVERY_REVIEW",
            row["available"],
            packet,
            delivery_review_schema(packet),
            images,
            allow_delivery_position=scenario_override is not None,
        )
        verdict_keys = (
            "sourceEpisodeContinuity",
            "ownerObjectiveContinuity",
            "meaningfulStructureTransfer",
            "causalFvgAndOb",
            "firstRetestEligibility",
        )
        all_pass = all(payload[key] == "PASS" for key in verdict_keys)
        if payload["action"] == "DATA_ERROR":
            raise V4ContractError(
                f"DELIVERY_REVIEW_DATA_ERROR: {payload['reason']}"
            )
        if (payload["action"] == approve_action) != all_pass:
            raise V4ContractError(
                "DELIVERY_REVIEW action is inconsistent with semantic verdicts"
            )
        record = {
            "fingerprint": fingerprint,
            "candidateId": candidate["shadowId"],
            "scenarioHash": scenario["scenarioHash"],
            "confirmation": candidate["deliveryConfirmation"],
            "reviewedAtUtc": utc_text(row["available"]),
            "action": payload["action"],
            "verdicts": {key: payload[key] for key in verdict_keys},
            "reason": payload["reason"],
            "requestId": request_id,
        }
        self.runtime.setdefault("deliveryReviewHistory", []).append(record)
        approved = payload["action"] == approve_action
        candidate["semanticReadyAtUtc"] = self.semantic_ready_at(
            request_id, int(row["available"])
        )
        self.stats[
            "deliveryReviewApproved" if approved else "deliveryReviewRejected"
        ] += 1
        self.event(
            "DELIVERY_REVIEW_APPROVED" if approved else "DELIVERY_REVIEW_REJECTED",
            row["available"],
            {
                "candidate": candidate,
                "review": record,
                "cacheHit": cache_hit,
            },
        )
        return approved

    def activate_delivery_replacement(self, row: dict[str, Any]) -> bool:
        if self.runtime["state"] != "PLANNED":
            return False
        scenario = self.runtime["scenario"]
        if zone_touched(row, scenario["finalChild"]):
            return False
        candidate = self._delivery_candidate_cache.get(self._loaded_slot_id)
        if self._loaded_slot_id not in self._delivery_candidate_cache:
            candidate = detect_pre_touch_delivery_candidate(
                self.market,
                scenario,
                row,
                float(self.config["brokerStopsLevelPrice"]),
            )
        if candidate is None:
            return False
        physical_key = self.physical_delivery_key(candidate)
        if physical_key in self._blocked_delivery_physical_keys:
            self.stats["deliveryReplacementBlockedLineageAmbiguity"] += 1
            return False
        if candidate.get("status") == "BLOCKED_CLOSER_LIQUIDITY":
            self.stats["deliveryReplacementBlockedCloserLiquidity"] += 1
            self.event(
                "DELIVERY_FVG_REPLACEMENT_BLOCKED_CLOSER_LIQUIDITY",
                row["available"],
                {
                    "candidate": candidate,
                    "apiCalled": False,
                },
            )
            return False
        lineage_audit = audit_pre_touch_delivery_lineages(
            self.market,
            scenario,
            row,
            float(self.config["brokerStopsLevelPrice"]),
            str(self.config["symbol"]),
            self.runtime.get("externalMapAuthority"),
        )
        if not lineage_audit["approved"]:
            self.stats["deliveryReplacementBlockedLineageAmbiguity"] += 1
            self.event(
                "DELIVERY_FVG_REPLACEMENT_BLOCKED_LINEAGE_AUDIT",
                row["available"],
                {
                    "candidate": candidate,
                    "lineageAudit": lineage_audit,
                    "apiCalled": False,
                },
            )
            return False
        candidate["lineageAudit"] = lineage_audit
        semantic_review_used = bool(
            self.config.get("enableSemanticDeliveryReview", False)
        )
        if semantic_review_used and not self.request_delivery_review(row, candidate):
            return False
        order, watch = delivery_candidate_order(
            self.market, scenario, candidate
        )
        semantic_ready = str(
            candidate.get("semanticReadyAtUtc") or utc_text(row["available"])
        )
        order["semanticReadyAtUtc"] = semantic_ready
        order["brokerAuthorizedAtUtc"] = self.broker_authorized_at(
            semantic_ready
        )
        blocked = self.risk_order_block_reason(order)
        if blocked:
            self.cancel(row["available"], blocked, {"order": order})
            return True
        self.runtime["order"] = order
        self.runtime["triggerWatch"] = watch
        self.runtime["reactionMonitor"] = None
        self.runtime["state"] = "PENDING"
        self.register_order_record(order, int(row["available"]))
        self.stats["deliveryReplacementOrders"] += 1
        self.event(
            "DELIVERY_FVG_REPLACEMENT_ORDER_CREATED",
            row["available"],
            {
                "candidate": candidate,
                "order": order,
                "apiCalled": semantic_review_used,
                "originalChildOrderCanceled": True,
                "firstRetestPending": True,
            },
        )
        print(
            f"[DELIVERY REPLACEMENT] {utc_text(row['available'])} "
            f"{order['direction']} entry={order['entry']:.2f} "
            f"sl={order['stop']:.2f} tp={order['target']:.2f}",
            flush=True,
        )
        return True

    def process_bar(self, row: dict[str, Any]) -> None:
        self.advance_shadow_deliveries(row)
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
            if self.activate_delivery_replacement(row):
                return
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
            episode_end = reaction_source_episode_end_reason(
                self.market, scenario, monitor, row
            )
            if episode_end:
                self.cancel(row["available"], episode_end)
                return
            all_sweeps = outermost_completed_sweep_events(
                monitor.get("sweepEvents", [])
            )
            rejected_sweeps = set(
                monitor.get("rejectedSweepEventIds", [])
            )
            all_sweeps = [
                item for item in all_sweeps
                if "|".join((
                    str(item.get("liquidityBarId")),
                    str(item.get("excursionBarId")),
                    str(item.get("recoveryBarId")),
                )) not in rejected_sweeps
            ]
            choch_candidates = list(
                self.runtime["reactionMonitor"].get("chochCandidates", [])
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
            rejected_breaks = set(
                self.runtime["reactionMonitor"].get(
                    "rejectedChochBreakBarIds", []
                )
            )
            choch_break_candidates = [
                item for item in choch_break_candidates
                if str(item.get("breakBarId")) not in rejected_breaks
            ]
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
            try:
                watch, order = advance_trigger_watch(
                    self.market,
                    scenario,
                    self.runtime["triggerWatch"],
                    row,
                    float(self.config["brokerStopsLevelPrice"]),
                )
            except V4ContractError as exc:
                if str(exc).startswith("INTERNAL_OBJECTIVE_"):
                    self.stats["ordersBlockedObjectiveContract"] += 1
                    self.cancel(
                        row["available"],
                        "OBJECTIVE_CONTRACT_FAILED_AT_ORDER",
                        {"reason": str(exc)},
                    )
                    return
                raise
            self.runtime["triggerWatch"] = watch
            if order:
                semantic_ready = str(
                    watch.get("semanticReadyAtUtc")
                    or scenario.get("semanticReadyAtUtc")
                    or utc_text(row["available"])
                )
                order["semanticReadyAtUtc"] = semantic_ready
                order["brokerAuthorizedAtUtc"] = self.broker_authorized_at(
                    semantic_ready
                )
                blocked = self.risk_order_block_reason(order)
                if blocked:
                    self.cancel(row["available"], blocked, {"order": order})
                    return
                self.runtime["order"] = order
                self.runtime["state"] = "PENDING"
                self.register_order_record(order, int(row["available"]))
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
            if outcome == "CANCELED_SPREAD_EXPANSION":
                self.cancel(row["available"], "FILL_SPREAD_EXCEEDED_FROZEN_BUFFER")
                return
            if outcome == "CANCELED_MISSED_API_LATENCY":
                self.cancel(row["available"], "MISSED_API_LATENCY")
                return
            if outcome == "CANCELED_MISSED_ORDER_LATENCY":
                self.cancel(row["available"], "MISSED_ORDER_LATENCY")
                return
            if outcome == "CANCELED_LATENCY_INTRABAR_AMBIGUOUS":
                self.cancel(row["available"], "LATENCY_INTRABAR_AMBIGUOUS")
                return
            if outcome == "FILLED":
                self.runtime["position"] = position
                self.runtime["state"] = "FILLED"
                self.event("ORDER_FILLED", row["available"], {"position": position})
                self.detach_filled_position(row["available"])
                return
            return

        if state == "FILLED":
            trade = advance_position(self.market, self.runtime["position"], row)
            if trade:
                self.close(row["available"], trade)

    def advance_closed_m1_bar(
        self,
        row: dict[str, Any],
        *,
        planning_enabled: bool,
        api_allowed: bool = True,
    ) -> dict[str, Any]:
        """Advance one confirmed M1 bar through the single replay/live core."""
        index = int(row["index"])
        if index != int(self.runtime["cursor"]):
            raise V4ContractError(
                f"closed-M1 cursor mismatch: runtime={self.runtime['cursor']} row={index}"
            )
        semantic_before = int(self.stats["semanticRequests"])
        plan_before = int(self.stats["planRequests"])
        self.deduplicate_physical_execution_signals(int(row["available"]))
        self.advance_position_book(row)
        state_before = str(self.runtime["state"])
        self.refresh_flat_plan_candidates(int(row["available"]))
        approach_events = self.advance_plan_candidate_ledger(row, "FLAT")
        self.prepare_delivery_candidates(row)
        for slot_id in [
            str(item["slotId"])
            for item in sorted(
                list(self.runtime.get("scenarioSlots", [])),
                key=self.lane_arbitration_key,
            )
        ]:
            self.load_scenario_slot(slot_id)
            self.process_bar(row)
            self.unload_scenario_slot()
        if (
            planning_enabled
            and self.runtime["state"] == "FLAT"
            and len(self.runtime.get("scenarioSlots", []))
            < int(self.config.get("maximumScenarioSlots", 256))
        ):
            planned = self.schedule_formation_driven_flat_plan(
                row,
                state_at_bar_start=state_before,
                api_allowed=api_allowed,
            )
            if not planned:
                self.schedule_event_driven_flat_plan(
                    row,
                    api_allowed=api_allowed,
                    approach_events=approach_events,
                )
            if self.runtime.get("state") == "PLANNED":
                self.store_planned_scenario_slot(int(row["available"]))
        if int(self.stats["semanticRequests"]) == semantic_before:
            if state_before == "FLAT":
                self.stats["flatZeroTokenBars"] += 1
            else:
                self.stats["activeZeroTokenBars"] += 1
        self.runtime["cursor"] = index + 1
        self.runtime["lastClosedM1BarId"] = row["barId"]
        return {
            "semanticRequests": int(self.stats["semanticRequests"]) - semantic_before,
            "planRequests": int(self.stats["planRequests"]) - plan_before,
            "stateBefore": state_before,
            "stateAfter": str(self.runtime["state"]),
        }

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
            if (
                row["time"] >= replay_end
                and self.runtime["state"] == "FLAT"
                and not self.runtime.get("openPositions")
                and not self.runtime.get("scenarioSlots")
            ):
                break
            self.advance_closed_m1_bar(
                row,
                planning_enabled=int(row["available"]) < replay_end,
                api_allowed=True,
            )
            if row["available"] % 3600 == 0:
                print(
                    f"[PROGRESS] {utc_text(row['available'])} state={self.runtime['state']} "
                    f"slots={len(self.runtime.get('scenarioSlots', []))} "
                    f"positions={len(self.runtime.get('openPositions', []))} "
                    f"requests={self.stats['semanticRequests']} api={self.stats['providerApiCalls']} "
                    f"tokens={self.stats['totalTokens']} planSkips={self.stats['flatPlanFingerprintSkips']} "
                    f"zeroTokenBars={self.stats['flatZeroTokenBars'] + self.stats['activeZeroTokenBars']} "
                    f"trades={len(self.trades)}",
                    flush=True,
                )
                self.save()
        self.save()
        if (
            self.runtime["state"] != "FLAT"
            or self.runtime.get("scenarioSlots")
            or self.runtime.get("openPositions")
        ):
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


def write_shadow_delivery_csv(
    run_dir: Path, candidates: list[dict[str, Any]]
) -> None:
    fields = [
        "shadow_id", "scenario_hash", "direction", "formed_at", "filled_at",
        "closed_at", "status", "entry", "sl", "tp", "r", "fvg_bar_id",
        "causal_ob_bar_id", "transfer_swing_bar_id", "protected_swing_bar_id",
        "original_child_ob_bar_id", "invalidation_reason",
    ]
    with (run_dir / "shadow_delivery.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in candidates:
            writer.writerow(
                {
                    "shadow_id": item.get("shadowId"),
                    "scenario_hash": item.get("scenarioHash"),
                    "direction": str(item.get("direction", "")).lower(),
                    "formed_at": item.get("formedAtUtc"),
                    "filled_at": item.get("filledAtUtc"),
                    "closed_at": item.get("closedAtUtc"),
                    "status": item.get("status"),
                    "entry": item.get("entry"),
                    "sl": item.get("stop"),
                    "tp": item.get("target"),
                    "r": item.get("resultR"),
                    "fvg_bar_id": item.get("formedBarId"),
                    "causal_ob_bar_id": item.get("causalObBarId"),
                    "transfer_swing_bar_id": item.get("transferSwingBarId"),
                    "protected_swing_bar_id": item.get("protectedSwingBarId"),
                    "original_child_ob_bar_id": item.get("originalChildObBarId"),
                    "invalidation_reason": item.get("invalidationReason"),
                }
            )


def setup(args: argparse.Namespace) -> int:
    _, old = load_secret(1) if SECRET.exists() else ("", {**DEFAULTS})
    config = {**DEFAULTS, **old}
    api_key = getpass.getpass("Gemini API key: ").strip()
    if not api_key:
        raise SystemExit("API key was not saved because it was empty")
    save_secret(api_key, config)
    print(f"V4 setup saved: {SECRET}")
    return 0


def manage_keys(args: argparse.Namespace) -> int:
    if args.key_action == "status":
        if not SECRET.exists():
            print("GEMINI_KEY_SLOTS configured=0 active=none")
            return 0
        raw = read_json(SECRET)
        keys = _secret_key_slots(raw)
        active = int(raw.get("activeApiKeySlot", 1)) if keys else 0
        print(f"GEMINI_KEY_SLOTS configured={len(keys)} active={active}")
        return 0

    if not SECRET.exists():
        raise SystemExit("Run Gemini_Replay_Setup.cmd before adding a second key")
    raw = read_json(SECRET)
    keys = _secret_key_slots(raw)
    config = {**DEFAULTS, **dict(raw.get("config", {}))}
    active = int(raw.get("activeApiKeySlot", 1))
    slot = int(args.slot)
    if args.key_action == "add":
        value = getpass.getpass(f"Gemini API key for slot {slot}: ").strip()
        if not value:
            raise SystemExit("API key was not saved because it was empty")
        if slot > len(keys) + 1:
            raise SystemExit("Key slots must be added without gaps")
        if slot == len(keys) + 1:
            keys.append(value)
        else:
            keys[slot - 1] = value
        save_secret(keys, config, active_slot=active)
        print(f"GEMINI_KEY_SLOT_SAVED slot={slot} configured={len(keys)}")
        return 0
    if slot < 1 or slot > len(keys):
        raise SystemExit(f"Key slot {slot} is unavailable; configured={len(keys)}")
    save_secret(keys, config, active_slot=slot)
    print(f"GEMINI_KEY_SLOT_SELECTED slot={slot}")
    return 0


def preflight(args: argparse.Namespace) -> int:
    api_key, config = load_secret(getattr(args, "api_key_slot", None))
    config = {**config, **V450_OPERATIONAL_DEFAULTS}
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
    key_count = configured_key_count()
    print(
        f"apiKeyPool={key_count} preferredSlot={config['apiKeySlot']} "
        f"autoFailover={'enabled' if key_count > 1 else 'waiting-for-second-key'}"
    )
    print(f"dataset={path}")
    print(f"period={config['replayStartUtc']}..{config['replayEndUtc']}")
    print(
        f"models=Gemini(PLAN={config['planModel']}, "
        f"AUTHORITY_PLAN={config['authorityPlanModel']}, "
        f"TRIGGER_WATCH={config['triggerWatchModel']}; "
        f"DELIVERY_REVIEW={config['deliveryReviewModel']}; "
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
        f"DELIVERY_REVIEW:{config['deliveryReviewThinkingLevel']}, "
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
        key_pool, _ = load_secret_pool(int(config.get("apiKeySlot", 1)))
        return GeminiProvider(key_pool, config)
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
    api_key, config = load_secret(getattr(args, "api_key_slot", None))
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
        frozen_slot = int(config.get("apiKeySlot", 1))
        requested_slot = getattr(args, "api_key_slot", None)
        if requested_slot is not None and int(requested_slot) != frozen_slot:
            raise V4ContractError(
                "resume must reuse the API key slot frozen by the original run"
            )
        api_key, _ = load_secret(frozen_slot)
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
        # V4.49 secret files may carry low-reasoning and small-budget defaults.
        # A fresh V4.50 run starts from its frozen operational profile; explicit
        # CLI flags below can still override the profile for diagnostics.
        config = {**config, **V450_OPERATIONAL_DEFAULTS}
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
            config["deliveryReviewModel"] = str(args.gemini_model)
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
            config["deliveryReviewMaxOutputTokens"] = output_budget
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
            config["deliveryReviewThinkingLevel"] = thinking_level
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
        benchmark_value = config.get("benchmarkTruth")
        if not benchmark_value:
            raise V4ContractError("Gemini replay requires --benchmark-truth for Sol gate binding")
        benchmark_path = Path(str(benchmark_value))
        if not benchmark_path.is_absolute():
            benchmark_path = ROOT / benchmark_path
        if not benchmark_path.exists():
            raise V4ContractError("benchmark truth does not exist")
        ground_truth_manifest = validate_frozen_ground_truth_v2(benchmark_path)
        if ground_truth_manifest is not None:
            period = ground_truth_manifest.get("period", {})
            if (
                ground_truth_manifest.get("datasetSha256") != sha256_file(path)
                or period.get("warmupStartUtc")
                != utc_text(parse_utc(str(config["warmupStartUtc"])))
                or period.get("replayStartUtc") != utc_text(start)
                or period.get("replayEndUtc") != utc_text(end)
            ):
                raise V4ContractError(
                    "GROUND_TRUTH_V2_GATE_MISMATCH: dataset, warm-up, or period changed"
                )
            validation_mode = "GROUND_TRUTH_V2_GATED"
            print(
                "[GROUND TRUTH V2 GATE] frozen ledger, authority, dataset, and period verified",
                flush=True,
            )
        else:
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
            if gate.get("truthSha256") != sha256_file(benchmark_path):
                raise V4ContractError("SOL_VALIDATION_GATE_TRUTH_MISMATCH: benchmark changed or was not gated")
    market = MarketData.from_npz(
        path,
        parse_utc(str(config["warmupStartUtc"])),
        follow_end,
        float(config["point"]),
    )
    if args.resume:
        runtime = read_json(run_dir / "state.json")
        if clear_retryable_provider_pause(runtime):
            atomic_json(run_dir / "state.json", runtime)
            print(
                "[RESUME RECOVERY] retryable Codex provider pause cleared; "
                "the same closed M1 bar will be retried",
                flush=True,
            )
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
    if not args.resume:
        runner.seed_warmup_family_baseline(start)
        runner.save()
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
        retryable_provider_failure = (
            isinstance(exc, GeminiReplayError) and GeminiProvider.retryable(exc)
        ) or (
            isinstance(exc, CodexReplayError) and CodexReplayError.retryable(exc)
        )
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
    write_shadow_delivery_csv(
        run_dir, runner.runtime.get("shadowDeliveryCandidates", [])
    )
    atomic_json(
        run_dir / "discovery_report.json",
        {
            "pipelineVersion": PIPELINE_VERSION,
            "rootCandidatesObservedByTf": runner.stats.get(
                "discoveryRootCandidatesByTf", {}
            ),
            "childCandidatesObservedByTf": runner.stats.get(
                "discoveryChildCandidatesByTf", {}
            ),
            "noFamilyReasons": runner.stats.get("discoveryNoFamilyReasons", {}),
            "cancellationReasons": runner.stats.get("cancellationReasons", {}),
            "authorityTransitions": runner.stats.get("authorityTransitions", 0),
            "authorityHistory": runner.runtime.get("externalAuthorityHistory", []),
            "childTouches": runner.stats.get("childTouches", 0),
            "shadowDelivery": {
                "detected": runner.stats.get("shadowDeliveryDetected", 0),
                "filled": runner.stats.get("shadowDeliveryFilled", 0),
                "tp": runner.stats.get("shadowDeliveryTp", 0),
                "sl": runner.stats.get("shadowDeliverySl", 0),
            },
            "deliveryReview": {
                "requests": runner.stats.get("deliveryReviewRequests", 0),
                "approved": runner.stats.get("deliveryReviewApproved", 0),
                "rejected": runner.stats.get("deliveryReviewRejected", 0),
                "history": runner.runtime.get("deliveryReviewHistory", []),
            },
        },
    )
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
    if getattr(args, "dataset", None):
        config["dataset"] = str(Path(args.dataset).resolve())
    if getattr(args, "warmup_start", None):
        config["warmupStartUtc"] = str(args.warmup_start)
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
        config["deliveryReviewModel"] = str(args.gemini_model)
    if args.gemini_thinking_level:
        if provider_name != "gemini":
            raise V4ContractError("--gemini-thinking-level is only valid with Gemini")
        config["planThinkingLevel"] = str(args.gemini_thinking_level)
        config["triggerWatchThinkingLevel"] = str(args.gemini_thinking_level)
        config["deliveryReviewThinkingLevel"] = str(args.gemini_thinking_level)
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
    benchmarks = truth.get("executableBenchmarks")
    if not isinstance(benchmarks, list):
        benchmarks = truth.get("executionCandidates", [])
    benchmark = next(
        (
            item for item in benchmarks
            if not args.trade_id
            or item.get("tradeId") == args.trade_id
            or item.get("truthId") == args.trade_id
        ),
        None,
    )
    if not benchmark:
        raise V4ContractError("fixed PLAN benchmark was not found")
    if not scenario:
        result = {"classification": "MODEL", "detail": "PLAN did not freeze a scenario"}
    else:
        if "map" in benchmark:
            expected = benchmark["map"]
            expected_direction = expected["direction"]
            expected_scope = expected["scope"]
            expected_objective = expected["objective"]["barId"]
            expected_lineage = [
                expected["root"]["barId"],
                *[
                    item["barId"]
                    for item in expected["refinement"].get("path", [])
                ],
            ]
        else:
            expected_direction = benchmark["direction"]
            expected_scope = benchmark["scope"]
            expected_objective = benchmark["objectiveBarId"]
            expected_lineage = [
                benchmark["rootObBarId"],
                *benchmark.get("refinementPath", []),
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
            "map": scenario["direction"] == expected_direction and scenario["scope"] == expected_scope,
            "root": causal_lineage,
            "objective": scenario["objective"]["barId"] == expected_objective,
            "refinement": causal_lineage,
        }
        first_failure = next((name for name, passed in checks.items() if not passed), None)
        result = {
            "classification": (
                "CAUSAL_MATCH" if first_failure is None
                else {
                    "map": "OWNER",
                    "root": "LINEAGE",
                    "objective": "OBJECTIVE",
                    "refinement": "LINEAGE",
                }[str(first_failure)]
            ),
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
    if path.suffix.lower() == ".jsonl":
        validate_frozen_ground_truth_v2(path)
        return [
            {
                "trade_id": str(item["executionId"]),
                "decision_at": str(item["decisionAtUtc"]),
                "filled_at": str(item["filledAtUtc"]),
                "closed_at": str(item["closedAtUtc"]),
                "direction": str(item["direction"]).lower(),
                "scope": str(item["scope"]),
                "execution_model": str(item["executionModel"]),
                "entry": str(item["entry"]),
                "sl": str(item["stop"]),
                "tp": str(item["target"]),
                "root_ob_bar_id": str(item["rootObBarId"]),
                "child_ob_bar_id": str(item["finalChildObBarId"]),
                "objective_bar_id": str(item["objectiveBarId"]),
            }
            for item in read_jsonl(path)
        ]
    if path.suffix.lower() != ".json":
        return load_csv(path)
    payload = read_json(path)
    rows: list[dict[str, str]] = []
    weekly_candidates = payload.get("multiPositionExecutionCandidates")
    if not isinstance(weekly_candidates, list):
        if payload.get("schemaVersion") == "june-oracle-multi-position-v1":
            weekly_candidates = payload.get("candidates")
        else:
            weekly_candidates = payload.get("executionCandidates")
    if isinstance(weekly_candidates, list):
        for benchmark in weekly_candidates:
            refinement = benchmark.get("refinementPath", [])
            rows.append(
                {
                    "trade_id": str(benchmark["truthId"]),
                    "decision_at": str(benchmark["planFrozenAtUtc"]),
                    "filled_at": str(benchmark["filledAtUtc"]),
                    "direction": str(benchmark["direction"]).lower(),
                    "scope": str(benchmark["scope"]),
                    "execution_model": str(benchmark["executionModel"]),
                    "entry": str(benchmark["entry"]),
                    "sl": str(benchmark["stop"]),
                    "tp": str(benchmark["target"]),
                    "root_ob_bar_id": str(benchmark["rootObBarId"]),
                    "child_ob_bar_id": str(
                        benchmark.get("finalChildObBarId")
                        or (refinement[-1] if refinement else "")
                    ),
                    "objective_bar_id": str(benchmark["objectiveBarId"]),
                }
            )
        return rows
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


def _trade_closed_timestamp(row: dict[str, str]) -> int | None:
    value = row.get("closed_at") or row.get("closedAt")
    return parse_utc(value) if value else None


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
    multi_position_truth = args.truth.suffix.lower() == ".jsonl"
    if args.truth.suffix.lower() == ".json":
        truth_payload = read_json(args.truth)
        truth_coverage = str(
            truth_payload.get("coverage", "EXHAUSTIVE_EXECUTED_TRADES")
        )
        multi_position_truth = bool(
            truth_payload.get("schemaVersion") == "june-oracle-multi-position-v1"
            or isinstance(truth_payload.get("multiPositionExecutionCandidates"), list)
        )
    elif args.truth.suffix.lower() != ".jsonl":
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
        causal_options = [
            (
                abs(_trade_timestamp(candidate[index]) - _trade_timestamp(expected)),
                index,
            )
            for index in unmatched
            if candidate[index].get("direction", "").lower() == expected.get("direction", "").lower()
            and _causal_trade_identity(expected, candidate[index])
        ]
        if causal_options:
            _, selected = min(causal_options)
        else:
            expected_fill = _trade_timestamp(expected)
            blockers = [
                index for index in range(len(candidate))
                if _trade_timestamp(candidate[index]) <= expected_fill
                and (_trade_closed_timestamp(candidate[index]) or expected_fill)
                >= expected_fill
            ]
            if blockers and not multi_position_truth:
                blocker = max(blockers, key=lambda index: _trade_timestamp(candidate[index]))
                output.append({
                    "truth_id": expected.get("trade_id", ""),
                    "candidate_id": candidate[blocker].get("trade_id", ""),
                    "classification": "BLOCKED_BY_ACTIVE_CANDIDATE",
                    "execution_variant": "SINGLE_POSITION_OCCUPANCY",
                })
                continue
            directional_options = [
                (
                    abs(_trade_timestamp(candidate[index]) - expected_fill),
                    index,
                )
                for index in unmatched
                if candidate[index].get("direction", "").lower()
                == expected.get("direction", "").lower()
                and abs(_trade_timestamp(candidate[index]) - expected_fill)
                <= args.window_hours * 3600
            ]
            if not directional_options:
                output.append({"truth_id": expected.get("trade_id", ""), "candidate_id": "", "classification": "MISS"})
                continue
            _, selected = min(directional_options)
        unmatched.remove(selected)
        actual = candidate[selected]
        diffs = {
            key: abs(float(expected[key]) - float(actual[key]))
            for key in ("entry", "sl", "tp")
        }
        same_cause = _causal_trade_identity(expected, actual)
        tolerance = max(args.tick_tolerance, abs(float(expected["entry"]) - float(expected["sl"])) * 0.10)
        exact_geometry = max(diffs.values()) <= args.tick_tolerance
        alternate_delivery_execution = bool(
            same_cause
            and expected.get("execution_model") == "DELIVERY_FVG_REPLACEMENT"
            and actual.get("execution_model") == "DELIVERY_FVG_REPLACEMENT"
            and not exact_geometry
        )
        classification = (
            "EXACT" if same_cause and exact_geometry
            else "CAUSAL_MATCH" if same_cause and (
                alternate_delivery_execution or max(diffs.values()) <= tolerance
            )
            else "DIRECTION_ONLY"
        )
        output.append(
            {
                "truth_id": expected.get("trade_id", ""),
                "candidate_id": actual.get("trade_id", ""),
                "classification": classification,
                "execution_variant": (
                    "ALTERNATE_DELIVERY_FVG"
                    if alternate_delivery_execution else ""
                ),
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
    fields = [
        "truth_id", "candidate_id", "classification", "execution_variant",
        "entry_diff", "sl_diff", "tp_diff",
    ]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output)
    counts = {
        kind: sum(row["classification"] == kind for row in output)
        for kind in (
            "EXACT", "CAUSAL_MATCH", "DIRECTION_ONLY", "MISS",
            "BLOCKED_BY_ACTIVE_CANDIDATE", "EXTRA", "UNASSESSED",
        )
    }
    counts["truthCoverage"] = truth_coverage
    positive_atlas_gate = bool(
        getattr(args, "positive_atlas_gate", False)
        and not truth_is_exhaustive
    )
    positive_cases_passed = bool(truth) and all(
        row["classification"] in {"EXACT", "CAUSAL_MATCH"}
        for row in output
        if row["truth_id"]
    )
    counts["positiveAtlasGateRequested"] = bool(
        getattr(args, "positive_atlas_gate", False)
    )
    counts["positiveCasesPassed"] = positive_cases_passed
    counts["negativeAuditRequired"] = bool(
        not truth_is_exhaustive and any(
            row["classification"] == "UNASSESSED" for row in output
        )
    )
    print(json.dumps(counts, ensure_ascii=False))
    print(args.output)
    passed = (
        (
            truth_is_exhaustive
            and bool(output)
            and all(
                row["classification"] in {"EXACT", "CAUSAL_MATCH"}
                for row in output
            )
        )
        or (positive_atlas_gate and positive_cases_passed)
    )
    return 0 if passed else 3


def compare_funnel(args: argparse.Namespace) -> int:
    if args.truth.suffix.lower() == ".jsonl":
        validate_frozen_ground_truth_v2(args.truth)
        accepted = read_jsonl(args.truth)
        truth = {
            "coverage": "EXHAUSTIVE_EXECUTED_TRADES",
            "executableBenchmarks": [
                {
                    "tradeId": str(row["executionId"]),
                    "map": {
                        "direction": str(row["direction"]),
                        "scope": str(row["scope"]),
                        "root": {"barId": str(row["rootObBarId"])},
                        "objective": {
                            "barId": str(row["objectiveBarId"]),
                            "price": float(row["target"]),
                        },
                    },
                    "refinement": {
                        "path": [
                            {"barId": str(item["obBarId"])}
                            for item in row["selectedLineagePath"].get(
                                "refinements", []
                            )
                        ]
                    },
                    "order": {
                        "filledAtUtc": str(row["filledAtUtc"]),
                        "entry": float(row["entry"]),
                        "stop": float(row["stop"]),
                        "target": float(row["target"]),
                    },
                    "triggerAudit": {
                        "sweepBarId": row.get("sweepBarId"),
                        "chochBreakBarId": row.get("chochBreakBarId"),
                        "executionBarId": row.get("executionObBarId"),
                    },
                }
                for row in accepted
            ],
        }
    else:
        truth = read_json(args.truth)
    truth_coverage = str(truth.get("coverage", "EXHAUSTIVE_EXECUTED_TRADES"))
    truth_is_exhaustive = truth_coverage == "EXHAUSTIVE_EXECUTED_TRADES"
    records = [json.loads(line) for line in args.ledger.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    plans = [
        row for row in records
        if row.get("event") in {"SCENARIO_PLANNED", "SCENARIO_SLOT_OPENED"}
        and isinstance(row.get("details", {}).get("scenario"), dict)
    ]
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
    orders = [
        row for row in records
        if row.get("event") == "ORDER_CREATED"
        or str(row.get("event", "")).endswith("_ORDER_CREATED")
    ]
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
        classification, detail = "OWNER", "direction/scope absent"
        root_matches = [
            row for row in map_matches
            if any(
                _scenario_contains_root(variant, expected_map["root"]["barId"])
                for variant in scenario_variants(row)
            )
        ]
        if map_matches:
            classification, detail = "LINEAGE", "map matched but root differs"
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
            classification, detail = "OBJECTIVE", "root matched but objective differs"
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
            classification, detail = "LINEAGE", "objective matched but child lineage differs"
        scenario_hashes = {row["details"]["scenario"]["scenarioHash"] for row in refinement_matches}
        expected_trigger = benchmark.get("triggerAudit", {})
        watch_matches = []
        for row in watches:
            if row["details"].get("scenarioHash") not in scenario_hashes:
                continue
            watch = row["details"].get("watch", {})
            mature_expected = expected_trigger.get("matureLiquidityBarId")
            choch_expected = expected_trigger.get("chochReferenceBarId")
            if mature_expected and (
                (watch.get("matureLiquidity") or {}).get("barId")
                != mature_expected
            ):
                continue
            if choch_expected and (
                (watch.get("chochReference") or {}).get("barId")
                != choch_expected
            ):
                continue
            watch_matches.append(row)
        if refinement_matches:
            classification, detail = "MODEL", "lineage matched but frozen trigger semantics differ"
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
            prices_match = all(
                key not in expected_order
                or abs(float(order.get(key, float("nan"))) - float(expected_order[key]))
                <= 1e-9
                for key in ("entry", "stop", "target")
            )
            if prices_match and all(
                not expected or evidence.get(key) == expected
                for key, expected in checks.items()
            ):
                order_matches.append(row)
        if watch_matches:
            classification, detail = "LATENCY", "trigger watch matched but local chain/order differs"
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
    keys_parser = sub.add_parser("keys")
    keys_parser.add_argument("key_action", choices=("add", "select", "status"))
    keys_parser.add_argument("--slot", type=int, default=2)
    keys_parser.set_defaults(func=manage_keys)
    preflight_parser = sub.add_parser("preflight")
    preflight_parser.add_argument("--api-key-slot", type=int, choices=(1, 2))
    preflight_parser.set_defaults(func=preflight)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--run-id")
    run_parser.add_argument(
        "--api-key-slot",
        type=int,
        choices=(1, 2),
        help=(
            "Use one configured Gemini key slot for this run. The slot is frozen "
            "in the run manifest and reused by resume."
        ),
    )
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
        "--dataset",
        type=Path,
        help="Override the configured NPZ dataset for this fixed packet.",
    )
    fixed.add_argument(
        "--warmup-start",
        help="Override the configured warm-up start UTC for this fixed packet.",
    )
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
    compare_parser.add_argument(
        "--positive-atlas-gate",
        action="store_true",
        help=(
            "For a non-exhaustive positive causal atlas, require every labelled "
            "positive case to match while leaving unmatched candidate trades as "
            "UNASSESSED. This does not authorize exact sequence or profitability claims."
        ),
    )
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
