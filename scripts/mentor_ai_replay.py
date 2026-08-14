from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
from datetime import datetime, timezone
import getpass
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from mentor_engine.data import build_timeframes, load_m1_npz
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
CONFIG_EXAMPLE = ROOT / "config" / "mentor_ai_replay.example.json"
SECRET = ROOT / "data" / "mentor_ai_replay_secret.json"
RUN_ROOT = ROOT / "output" / "mentor_ai_replay_runs"
SCHEMA = ROOT / "mentor_context_pack" / "schemas" / "replay_decision.schema.json"
SCHEMA_PROBE = ROOT / "data" / "mentor_ai_schema_probe.json"
CONTRACT_DIR = ROOT / "mentor_context_pack" / "api_contracts"
CONTRACT_MANIFEST = CONTRACT_DIR / "manifest.json"
TRUTH_DEFAULT = ROOT / "output" / "mentor_aug21_truth_v3" / "trades.csv"
FUNNEL_TRUTH_DEFAULT = ROOT / "output" / "mentor_aug21_truth_v3" / "funnel_truth.json"
PIPELINE_VERSION = "3.25-engine-validated-delivery-contract"


PROMPT_LIMIT_CONFIG_KEYS = {
    "MAP_SCOUT": "maximumMapScoutPromptBytes",
    "MAP_REVIEW": "maximumMapReviewPromptBytes",
    "REFINEMENT": "maximumRefinementPromptBytes",
    "TRIGGER": "maximumTriggerPromptBytes",
    "PENDING_REVIEW": "maximumPendingPromptBytes",
}


def utc_text(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def load_stage_contract(phase: str) -> tuple[str, dict[str, str]]:
    phase_name = {
        "MAP": "map",
        "REFINEMENT": "refinement",
        "TRIGGER": "trigger",
        "PENDING_REVIEW": "pending",
    }[phase]
    manifest = json.loads(CONTRACT_MANIFEST.read_text(encoding="utf-8"))
    authority = normalized_text(ROOT / str(manifest["source"]))
    current = normalized_text(ROOT / "AGENTS.md")
    source_hash = hashlib.sha256(authority.encode("utf-8")).hexdigest()
    if source_hash != manifest["sourceSha256"] or authority != current:
        raise ValueError("API contracts are stale or AGENTS.md differs from the frozen backup")

    texts: list[str] = []
    hashes: dict[str, str] = {}
    for name in ("common", phase_name):
        item = manifest["contracts"][name]
        path = ROOT / item["path"]
        body = path.read_text(encoding="utf-8")
        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if body_hash != item["sha256"]:
            raise ValueError(f"API contract hash mismatch: {name}")
        texts.append(body.rstrip())
        hashes[name] = body_hash
    return "\n\n".join(texts), hashes


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return json.loads(CONFIG_EXAMPLE.read_text(encoding="utf-8"))
    return json.loads(path.read_text(encoding="utf-8-sig"))


def enforce_prompt_size(
    prompt: str, config: dict[str, Any], stage: str
) -> dict[str, int]:
    prompt_bytes = len(prompt.encode("utf-8"))
    key = PROMPT_LIMIT_CONFIG_KEYS[stage]
    maximum = int(config.get(key, 24000))
    if prompt_bytes > maximum:
        raise ValueError(
            f"{stage} prompt size {prompt_bytes} bytes exceeds {key}={maximum}; "
            "API request was blocked before token consumption"
        )
    return {"promptBytes": prompt_bytes, "maximumPromptBytes": maximum}


def output_token_limit(config: dict[str, Any], role: str) -> int:
    if role not in {"scout", "reviewer"}:
        raise ValueError(f"unknown provider role: {role}")
    return int(
        config.get("scoutMaxOutputTokens", 1600)
        if role == "scout"
        else config.get("reviewerMaxOutputTokens", 4096)
    )


def phase_token_reserve(
    config: dict[str, Any], phase: str, estimated_calls: int
) -> int:
    """Return a conservative token ceiling for the calls the phase can issue."""
    if estimated_calls <= 0:
        return 0
    image_tokens = int(config.get("estimatedImageTokensPerCall", 2048))
    reviewer_output = output_token_limit(config, "reviewer")
    if phase == "MAP" and estimated_calls == 2:
        scout = (
            int(config["maximumMapScoutPromptBytes"])
            + output_token_limit(config, "scout")
            + image_tokens
        )
        reviewer = (
            int(config["maximumMapReviewPromptBytes"])
            + reviewer_output
            + image_tokens
        )
        return scout + reviewer
    stage = "MAP_REVIEW" if phase == "MAP" else phase
    return (
        int(config[PROMPT_LIMIT_CONFIG_KEYS[stage]])
        + reviewer_output
        + image_tokens
    )


def provider_budget_limits(
    config: dict[str, Any], decision_provider: str
) -> tuple[int, int, int, int]:
    """Return per-run and cumulative call/token ceilings for a provider."""
    if decision_provider == "manual-codex":
        replay_minutes = max(
            1,
            math.ceil(
                (parse_utc(str(config["replayEndUtc"]))
                 - parse_utc(str(config["replayStartUtc"])))
                / 60
            ),
        )
        # A MAP minute can issue one scout and one reviewer request. Manual
        # judgments have no API cost, so the default must cover that complete
        # future-blind worst case instead of sharing the codex-cli cost guard.
        default_calls = replay_minutes * 2 + 2
        per_call_tokens = max(
            phase_token_reserve(config, "MAP", 2),
            phase_token_reserve(config, "REFINEMENT", 1),
            phase_token_reserve(config, "TRIGGER", 1),
            phase_token_reserve(config, "PENDING_REVIEW", 1),
        )
        default_tokens = default_calls * per_call_tokens
        return (
            int(config.get("maximumManualCallsPerRun", default_calls)),
            int(config.get("maximumManualCalls", default_calls)),
            int(config.get("maximumManualTokensPerRun", default_tokens)),
            int(config.get("maximumManualTotalTokens", default_tokens)),
        )

    if decision_provider == "codex-cli":
        return (
            int(config.get("maximumCodexCallsPerRun", 220)),
            int(config.get("maximumCodexCalls", 500)),
            int(config.get("maximumCodexTokensPerRun", 2_000_000)),
            int(config.get("maximumCodexTotalTokens", 4_000_000)),
        )

    return (
        int(config.get("maximumApiCallsPerRun", 20)),
        int(config.get("maximumApiCalls", 60)),
        int(config.get("maximumTokensPerRun", 150000)),
        int(config.get("maximumTotalTokens", 350000)),
    )


def bounded_map_scout_prompt(
    contract: str,
    packet: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, dict[str, int]]:
    """Fit MAP candidate evidence to the byte budget without dropping whole TF/side groups."""
    key = PROMPT_LIMIT_CONFIG_KEYS["MAP_SCOUT"]
    maximum = int(config.get(key, 24000))
    table = packet.get("structuralLiquidityCandidates")
    if not isinstance(table, dict) or not isinstance(table.get("data"), list):
        prompt = map_scout_prompt(contract, packet)
        return prompt, enforce_prompt_size(prompt, config, "MAP_SCOUT")

    rows = table["data"]
    original_count = int(table.get("totalCount", len(rows)))
    while True:
        table["omittedCount"] = original_count - len(rows)
        prompt = map_scout_prompt(contract, packet)
        prompt_bytes = len(prompt.encode("utf-8"))
        if prompt_bytes <= maximum:
            return prompt, {
                "promptBytes": prompt_bytes,
                "maximumPromptBytes": maximum,
            }
        if not rows:
            return prompt, enforce_prompt_size(prompt, config, "MAP_SCOUT")

        counts = Counter((str(row[1]), str(row[2])) for row in rows)
        status_index = (
            table.get("columns", []).index("status")
            if "status" in table.get("columns", []) else None
        )
        removable = next(
            (
                index for index in range(len(rows) - 1, -1, -1)
                if status_index is not None
                and str(rows[index][status_index]) == "CONSUMED"
                if counts[(str(rows[index][1]), str(rows[index][2]))] > 2
            ),
            next(
                (
                    index for index in range(len(rows) - 1, -1, -1)
                    if counts[(str(rows[index][1]), str(rows[index][2]))] > 2
                ),
                len(rows) - 1,
            ),
        )
        rows.pop(removable)


def bounded_map_review_prompt(
    contract: str,
    packet: dict[str, Any],
    candidates: list[dict[str, Any]],
    previous_candidate: dict[str, Any] | None,
    config: dict[str, Any],
) -> tuple[str, dict[str, int]]:
    """Fit MAP review evidence by dropping only non-judgment packet metadata."""
    key = PROMPT_LIMIT_CONFIG_KEYS["MAP_REVIEW"]
    maximum = int(config.get(key, 24000))
    prompt_packet = copy.deepcopy(packet)

    optional_metadata = (
        "contractHashes",
        "brokerStopsLevelPrice",
        "spreadPrice",
        "futureHidden",
    )
    while True:
        if prompt_packet.get("candleEvidence") == []:
            prompt_packet.pop("candleEvidence", None)
        prompt = map_review_prompt(
            contract, prompt_packet, candidates, previous_candidate
        )
        prompt_bytes = len(prompt.encode("utf-8"))
        if prompt_bytes <= maximum:
            return prompt, {
                "promptBytes": prompt_bytes,
                "maximumPromptBytes": maximum,
            }
        removable = next(
            (name for name in optional_metadata if name in prompt_packet),
            None,
        )
        if removable is None:
            return prompt, enforce_prompt_size(prompt, config, "MAP_REVIEW")
        prompt_packet.pop(removable)


def bounded_stage_prompt(
    contract: str,
    packet: dict[str, Any],
    phase: str,
    previous: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, dict[str, int]]:
    """Trim only old redundant OHLC rows until a stage packet fits its hard limit."""
    key = PROMPT_LIMIT_CONFIG_KEYS[phase]
    maximum = int(config.get(key, 24000))
    prompt_previous = {
        key: copy.deepcopy(previous.get(key))
        for key in ("state", "scenario", "order")
        if previous.get(key) is not None
    }
    prompt_scenario = prompt_previous.get("scenario")
    if isinstance(prompt_scenario, dict):
        # MAP candidate prose and detector diagnostics have already been
        # resolved into frozen root/objective geometry. Repeating them in every
        # stage burns budget and can push a valid packet over the hard limit.
        prompt_scenario.pop("mapCandidate", None)
        prompt_scenario.pop("_deliveryWakeup", None)
    compact = packet.get("compactBars")
    data = compact.get("data") if isinstance(compact, dict) else None
    if not isinstance(data, dict):
        prompt = stage_prompt(contract, packet, phase, prompt_previous)
        return prompt, enforce_prompt_size(prompt, config, phase)

    minimums = {
        "REFINEMENT": {"M30": 6, "M15": 10, "M5": 20, "M1": 12},
        "TRIGGER": {"M15": 6, "M5": 15, "M1": 60},
        "PENDING_REVIEW": {"H1": 2, "M15": 4, "M5": 6, "M1": 8},
    }[phase]
    protected_ids: set[str] = set()
    refinement = packet.get("refinementCandidates")
    if isinstance(refinement, dict):
        for row in refinement.get("data", []):
            if row:
                protected_ids.add(str(row[0]))
            if len(row) > 4 and row[4]:
                protected_ids.add(str(row[4]))
            if len(row) > 5 and row[5]:
                protected_ids.add(str(row[5]))
    omitted = {timeframe: 0 for timeframe in data}

    while True:
        packet.pop("promptCompaction", None)
        if any(omitted.values()):
            packet["promptCompaction"] = {
                "oldestRowsOmitted": {
                    timeframe: count for timeframe, count in omitted.items() if count
                },
                "protectedCandidateRowsKept": True,
            }
        prompt = stage_prompt(contract, packet, phase, prompt_previous)
        prompt_bytes = len(prompt.encode("utf-8"))
        if prompt_bytes <= maximum:
            return prompt, {
                "promptBytes": prompt_bytes,
                "maximumPromptBytes": maximum,
            }

        removable: list[tuple[int, str, int]] = []
        for timeframe, rows in data.items():
            minimum = int(minimums.get(timeframe, 0))
            if not isinstance(rows, list) or len(rows) <= minimum:
                continue
            index = next(
                (
                    candidate_index
                    for candidate_index, row in enumerate(rows)
                    if row and str(row[0]) not in protected_ids
                ),
                -1,
            )
            if index >= 0:
                removable.append((len(rows) - minimum, timeframe, index))
        if not removable:
            return prompt, enforce_prompt_size(prompt, config, phase)
        _, timeframe, index = max(removable)
        data[timeframe].pop(index)
        omitted[timeframe] += 1


def map_candidate_ohlc_rejection(
    candidate: dict[str, Any],
    root: dict[str, Any],
    objective: dict[str, Any],
    current_bid: float,
    allowed_objectives: set[tuple[str, str]] | None = None,
    compact: dict[str, list[dict[str, Any]]] | None = None,
    local_map_wakeup: dict[str, Any] | None = None,
) -> str | None:
    candidate_id = str(candidate.get("candidateId", "candidate"))
    root_id = str(candidate.get("rootBarId", ""))
    if root_id.split(":", 1)[0] not in {"H1", "M30", "M15"}:
        return f"{candidate_id}: root timeframe is not H1/M30/M15"
    direction = str(candidate.get("direction", ""))
    root_open, root_close = float(root["o"]), float(root["c"])
    root_low = float(root.get("l", min(root_open, root_close)))
    root_high = float(root.get("h", max(root_open, root_close)))
    if direction == "LONG" and current_bid < root_low:
        return f"{candidate_id}: bullish root is already body-invalidated"
    if direction == "SHORT" and current_bid > root_high:
        return f"{candidate_id}: bearish root is already body-invalidated"
    is_opposite_candle = (
        direction == "LONG" and root_close < root_open
    ) or (
        direction == "SHORT" and root_close > root_open
    )
    if not is_opposite_candle:
        return f"{candidate_id}: root is not the required opposite-color candle"
    if compact is not None:
        root_tf = root_id.split(":", 1)[0]
        root_time = int(root_id.split(":", 1)[1])
        later = [
            row for row in compact.get(root_tf, [])
            if int(str(row["barId"]).split(":", 1)[1]) > root_time
        ]
        delivered = any(
            (direction == "LONG" and float(row["c"]) > root_high)
            or (direction == "SHORT" and float(row["c"]) < root_low)
            for row in later
        )
        wake_proves_current_delivery = bool(
            isinstance(local_map_wakeup, dict)
            and str(local_map_wakeup.get("candidateRootBarId")) == root_id
            and str(local_map_wakeup.get("directionHint")) == direction
            and (
                (direction == "LONG" and current_bid > root_high)
                or (direction == "SHORT" and current_bid < root_low)
            )
        )
        if not later and not wake_proves_current_delivery:
            return f"{candidate_id}: root has no later closed delivery candle"
        if not delivered and not wake_proves_current_delivery:
            return f"{candidate_id}: root has not produced a body-close displacement beyond its range"
        timeframe_seconds = {"H1": 3600, "M30": 1800, "M15": 900}[root_tf]
        source_available = root_time + timeframe_seconds
        m1_after_source = [
            row for row in compact.get("M1", [])
            if int(str(row["barId"]).split(":", 1)[1]) + 60 >= source_available
        ]
        departed = False
        retouched = False
        for row in m1_after_source:
            row_low, row_high = float(row["l"]), float(row["h"])
            if not departed:
                departed = (
                    direction == "LONG" and row_low > root_high
                ) or (
                    direction == "SHORT" and row_high < root_low
                )
                continue
            if row_low <= root_high and row_high >= root_low:
                retouched = True
                break
        if retouched:
            return (
                f"{candidate_id}: root was retouched after its initial "
                "directional departure and is no longer fresh"
            )
    objective_side = str(candidate.get("objectiveSide", ""))
    objective_id = str(candidate.get("objectiveBarId", ""))
    if (
        allowed_objectives is not None
        and (objective_id, objective_side) not in allowed_objectives
    ):
        return f"{candidate_id}: objective is not a confirmed structural-extremum candidate"
    objective_price = float(
        objective["h"] if objective_side == "BSL" else objective["l"]
    )
    objective_ahead = (
        direction == "LONG" and objective_side == "BSL" and objective_price > current_bid
    ) or (
        direction == "SHORT" and objective_side == "SSL" and objective_price < current_bid
    )
    if not objective_ahead:
        return f"{candidate_id}: objective is not ahead in the proposed direction"
    return None


def augment_candidates_with_local_root(
    candidates: list[dict[str, Any]],
    local_map_wakeup: dict[str, Any] | None,
    liquidity_candidates: list[dict[str, Any]] | None = None,
    current_bid: float | None = None,
    maximum_objectives: int = 3,
) -> list[dict[str, Any]]:
    # The detector cannot manufacture direction, scope, or objective. It may,
    # however, preserve its exact closed root as an alternative to a scout's
    # same-direction candidate. The reviewer then compares both OHLC-backed
    # roots under the identical model-proposed objective.
    augmented = [copy.deepcopy(item) for item in candidates]
    local_alternatives: list[dict[str, Any]] = []
    if not isinstance(local_map_wakeup, dict):
        return augmented
    root_id = str(local_map_wakeup.get("candidateRootBarId", ""))
    direction = str(local_map_wakeup.get("directionHint", ""))
    if not root_id.startswith(("H1:", "M30:", "M15:")) or direction not in {
        "LONG", "SHORT"
    }:
        return augmented
    seen_pairs = {
        (str(item.get("rootBarId", "")), str(item.get("objectiveBarId", "")))
        for item in augmented
    }
    alternatives = 0
    same_direction = [
        item for item in candidates if str(item.get("direction", "")) == direction
    ]
    for item in same_direction:
        if str(item.get("direction", "")) != direction:
            continue
        objective_id = str(item.get("objectiveBarId", ""))
        if not objective_id or (root_id, objective_id) in seen_pairs:
            continue
        alternative = copy.deepcopy(item)
        alternative["candidateId"] = (
            f"{item.get('candidateId', 'MAP-CANDIDATE')}-LOCAL_ROOT"
        )
        alternative["rootBarId"] = root_id
        alternative["reason"] = (
            "Timing-detector root alternative paired with the scout's same-"
            "direction objective. Reviewer must independently prove causality."
        )
        alternative["localRootComparisonOnly"] = True
        local_alternatives.append(alternative)
        seen_pairs.add((root_id, objective_id))
        alternatives += 1
        if alternatives >= max(1, int(maximum_objectives)):
            break
    if (
        alternatives < max(1, int(maximum_objectives))
        and isinstance(liquidity_candidates, list)
        and current_bid is not None
    ):
        # A wrong-direction scout result must not suppress an exact closed
        # root detected by the neutral timing router.  This fallback creates
        # comparison candidates only; MAP_REVIEW still decides whether the
        # root owns any listed objective, and may reject every alternative.
        template = copy.deepcopy(same_direction[0]) if same_direction else {
            "candidateId": "ENGINE-LOCAL-ROOT",
            "direction": direction,
            "scope": "INTERNAL_ROTATION",
            "rootBarId": root_id,
            "objectiveBarId": "",
            "objectiveSide": "BSL" if direction == "LONG" else "SSL",
            "objectiveType": "INTERNAL_LIQUIDITY",
            "reason": (
                "Engine-created comparison shell for an exact closed local "
                "root that the scout omitted. Reviewer owns all semantic "
                "approval, scope, and objective classification."
            ),
        }
        expected_side = "BSL" if direction == "LONG" else "SSL"
        eligible = [
            item for item in liquidity_candidates
            if str(item.get("status")) == "ACTIVE"
            and str(item.get("side")) == expected_side
            and (
                (direction == "LONG" and float(item.get("price")) > current_bid)
                or (direction == "SHORT" and float(item.get("price")) < current_bid)
            )
        ]
        eligible.sort(key=lambda item: abs(float(item["price"]) - current_bid))
        seen_prices: set[float] = set()
        for item in eligible:
            objective_id = str(item.get("barId", ""))
            objective_price = round(float(item.get("price")), 8)
            if not objective_id or objective_price in seen_prices:
                continue
            seen_prices.add(objective_price)
            if (root_id, objective_id) in seen_pairs:
                continue
            alternative = copy.deepcopy(template)
            alternative["candidateId"] = (
                f"{template.get('candidateId', 'MAP-CANDIDATE')}-"
                f"LOCAL_ROOT-OBJ{alternatives + 1}"
            )
            alternative["rootBarId"] = root_id
            alternative["objectiveBarId"] = objective_id
            alternative["objectiveSide"] = expected_side
            alternative["reason"] = (
                "Timing-detector root paired with an engine-listed active "
                "same-side objective for reviewer comparison. Scope and "
                "objective type remain reviewer decisions."
            )
            alternative["localRootComparisonOnly"] = True
            alternative["localObjectiveComparisonOnly"] = True
            local_alternatives.append(alternative)
            seen_pairs.add((root_id, objective_id))
            alternatives += 1
            if alternatives >= max(1, int(maximum_objectives)):
                break
    # The current closed delivery event is why MAP woke. Present its exact
    # root alternatives before stale watched/scout candidates so list order
    # cannot anchor review on an older broad source. No candidate is removed.
    return [*local_alternatives, *augmented]


def previous_map_candidate_for_review(
    previous: dict[str, Any] | None,
    local_map_wakeup: dict[str, Any] | None,
) -> dict[str, Any] | None:
    candidate = None
    if isinstance(previous, dict) and previous.get("state") == "WATCHING_MAP":
        candidate = (previous.get("scenario") or {}).get("mapCandidate")
    if not isinstance(candidate, dict):
        return None
    if (
        isinstance(local_map_wakeup, dict)
        and str(local_map_wakeup.get("kind"))
        == "LOCAL_ROOT_CHILD_DELIVERY_CANDIDATE"
        and str(local_map_wakeup.get("candidateRootBarId", ""))
        != str(candidate.get("rootBarId", ""))
    ):
        # A newly closed root-child delivery is a new causal episode. The old
        # WATCH candidate may be proposed again by the scout, but it must not
        # receive privileged carry-over status in this independent review.
        return None
    return copy.deepcopy(candidate)


def save_secret(config: dict[str, Any], api_key: str) -> None:
    SECRET.parent.mkdir(parents=True, exist_ok=True)
    payload = {"apiKey": api_key.strip(), "config": config}
    SECRET.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_secret() -> tuple[str, dict[str, Any]]:
    if not SECRET.exists():
        raise SystemExit("API key가 없습니다. 먼저 `python scripts/mentor_ai_replay.py setup`을 실행하세요.")
    payload = json.loads(SECRET.read_text(encoding="utf-8-sig"))
    return str(payload.get("apiKey", "")).strip(), dict(payload.get("config", {}))


def discover_symbol_spec(symbol: str) -> tuple[float | None, float | None]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except ImportError:
        return None, None
    initialized_here = False
    try:
        if not mt5.initialize():
            return None, None
        initialized_here = True
        info = mt5.symbol_info(symbol)
        if info is None:
            return None, None
        point = float(info.point)
        return point, float(info.trade_stops_level) * point
    finally:
        if initialized_here:
            mt5.shutdown()


def setup(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    point, stops = discover_symbol_spec(str(config.get("symbol", "GOLD")))
    if point and point > 0:
        config["point"] = point
    if stops is not None:
        config["brokerStopsLevelPrice"] = stops
        config["brokerSpecResolved"] = True
    api_key = getpass.getpass("Gemini API key (입력 내용은 화면에 표시되지 않음): ").strip()
    if not api_key:
        raise SystemExit("빈 API key는 저장하지 않았습니다.")
    save_secret(config, api_key)
    print(f"설정 저장 완료: {SECRET}")
    print(f"model={config['model']} symbol={config['symbol']} point={config['point']} stops={config['brokerStopsLevelPrice']}")
    return 0


def dataset_path(config: dict[str, Any]) -> Path:
    path = Path(str(config["dataset"]))
    return path if path.is_absolute() else ROOT / path


def load_rates(config: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    path = dataset_path(config)
    payload = np.load(path, allow_pickle=True)
    return payload["rates"], json.loads(str(payload["metadata"].item()))


def resolve_candle_queries(
    config: dict[str, Any],
    as_of: str,
    phase: str,
    queries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    allowed = {
        "MAP": {"H1", "M30", "M15", "M5"},
        "REFINEMENT": {"M30", "M15", "M5"},
        "TRIGGER": {"M15", "M5", "M1"},
        "PENDING_REVIEW": {"H1", "M30", "M15", "M5", "M1"},
    }[phase]
    if not 1 <= len(queries) <= 4:
        raise ValueError("QUERY_CANDLES requires 1..4 queries")

    cutoff = parse_utc(as_of)
    warmup = parse_utc(str(config["warmupStartUtc"]))
    m1, _ = load_m1_npz(dataset_path(config), warmup, cutoff + 60)
    frames = build_timeframes(m1)
    point = float(config["point"])
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for query in queries:
        query_id = str(query.get("queryId", "")).strip()
        timeframe = str(query.get("tf", ""))
        if not query_id or query_id in seen_ids:
            raise ValueError("candle queryId must be nonempty and unique")
        seen_ids.add(query_id)
        if timeframe not in allowed:
            raise ValueError(f"timeframe {timeframe} is not allowed in {phase}")
        if phase == "MAP" and timeframe == "M5" and query.get("purpose") != "OBJECTIVE":
            raise ValueError("MAP may query M5 only to verify an internal objective")
        around = parse_utc(str(query.get("aroundTimeUtc", "")))
        if around > cutoff:
            raise ValueError("candle query references future time")
        before, after = int(query.get("before", -1)), int(query.get("after", -1))
        if not 0 <= before <= 3 or not 0 <= after <= 3:
            raise ValueError("candle query before/after must be within 0..3")

        series = frames[timeframe]
        closed = np.flatnonzero(series.available_time <= cutoff)
        if not len(closed):
            raise ValueError(f"no closed {timeframe} candles at as-of")
        insertion = int(np.searchsorted(series.time[closed], around, side="left"))
        candidates = [max(0, min(insertion, len(closed) - 1))]
        if insertion > 0:
            candidates.append(insertion - 1)
        center_pos = min(
            candidates,
            key=lambda position: abs(int(series.time[closed[position]]) - around),
        )
        start = max(0, center_pos - before)
        stop = min(len(closed), center_pos + after + 1)
        candles = []
        for position in range(start, stop):
            index = int(closed[position])
            if int(series.available_time[index]) > cutoff:
                raise AssertionError("future candle leaked into query result")
            candles.append({
                "openTimeUtc": utc_text(int(series.time[index])),
                "availableTimeUtc": utc_text(int(series.available_time[index])),
                "open": float(series.open[index]),
                "high": float(series.high[index]),
                "low": float(series.low[index]),
                "close": float(series.close[index]),
                "spreadPrice": float(series.spread_points[index]) * point,
            })
        results.append({
            "queryId": query_id,
            "tf": timeframe,
            "requestedAroundTimeUtc": utc_text(around),
            "purpose": str(query.get("purpose", "")),
            "candles": candles,
        })
    return results


def preflight(_: argparse.Namespace) -> int:
    api_key, config = load_secret()
    errors: list[str] = []
    warnings: list[str] = []
    if not bool(config.get("brokerSpecResolved", False)):
        point, stops = discover_symbol_spec(str(config.get("symbol", "GOLD")))
        if point and point > 0 and stops is not None:
            config["point"] = point
            config["brokerStopsLevelPrice"] = stops
            config["brokerSpecResolved"] = True
            save_secret(config, api_key)
            print(
                "BROKER_SPEC_RESOLVED "
                f"symbol={config['symbol']} point={point} stops={stops}"
            )
    data = dataset_path(config)
    if not data.exists():
        errors.append(f"dataset missing: {data}")
    if not SCHEMA.exists():
        errors.append(f"schema missing: {SCHEMA}")
    else:
        try:
            probe = json.loads(SCHEMA_PROBE.read_text(encoding="utf-8"))
            if probe.get("schemaSha256") != sha256(SCHEMA):
                errors.append("Gemini schema probe is stale; run probe-schema before replay")
            if probe.get("model") != config.get("model"):
                errors.append("Gemini schema probe model differs from configured model")
        except (OSError, KeyError, json.JSONDecodeError):
            errors.append("Gemini schema probe missing; run probe-schema before replay")
    for stage, schema_path in STAGE_SCHEMAS.items():
        if not schema_path.exists():
            errors.append(f"V2 schema missing for {stage}: {schema_path}")
            continue
        try:
            json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid V2 schema for {stage}: {exc}")
    if not bool(config.get("reviewerEnabled", False)):
        errors.append("reviewerEnabled must be true for the V2 pipeline")
    if not str(config.get("reviewerModel", "")).strip():
        errors.append("reviewerModel is required for the V2 pipeline")
    if not CONTRACT_MANIFEST.exists():
        errors.append(f"contract manifest missing: {CONTRACT_MANIFEST}")
    else:
        try:
            for phase in ("MAP", "REFINEMENT", "TRIGGER", "PENDING_REVIEW"):
                load_stage_contract(phase)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"API contract validation failed: {exc}")
    if not (ROOT / "AGENTS.md").exists():
        errors.append("AGENTS.md missing")
    if not api_key:
        errors.append("API key empty")
    if float(config.get("point", 0)) <= 0:
        errors.append("point must be positive")
    if int(config.get("maximumApiCallsPerRun", config.get("maximumApiCalls", 0))) <= 0:
        errors.append("maximumApiCallsPerRun must be positive")
    maximum_tokens_per_run = int(
        config.get("maximumTokensPerRun", config.get("maximumTotalTokens", 0))
    )
    if maximum_tokens_per_run <= 0:
        errors.append("maximumTokensPerRun must be positive")
    if int(config.get("estimatedImageTokensPerCall", 2048)) <= 0:
        errors.append("estimatedImageTokensPerCall must be positive")
    for stage, key in PROMPT_LIMIT_CONFIG_KEYS.items():
        value = int(config.get(key, 0))
        if value <= 0:
            errors.append(f"{key} must be positive ({stage})")
    if not 1 <= int(config.get("maximumCandleQueryRoundsPerPhase", 0)) <= 3:
        errors.append("maximumCandleQueryRoundsPerPhase must be between 1 and 3")
    if not bool(config.get("brokerSpecResolved", False)):
        errors.append("broker symbol specification is unresolved; start MT5 once so setup can read GOLD settings")
    if data.exists():
        rates, metadata = load_rates(config)
        start, end = parse_utc(config["replayStartUtc"]), parse_utc(config["replayEndUtc"])
        if not np.any((rates["time"] >= start) & (rates["time"] < end)):
            errors.append("dataset has no bars in replay range")
        if metadata.get("symbol") != config.get("symbol"):
            errors.append(f"symbol mismatch: dataset={metadata.get('symbol')} config={config.get('symbol')}")
    print("MENTOR_AI_REPLAY_PREFLIGHT_OK" if not errors else "MENTOR_AI_REPLAY_PREFLIGHT_FAILED")
    for item in warnings:
        print(f"WARNING: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    return 0 if not errors else 1


def probe_schema(_: argparse.Namespace) -> int:
    from scripts.gemini_replay_provider import generate_structured_decision

    api_key, config = load_secret()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    response = generate_structured_decision(
        api_key=api_key,
        model=str(config["model"]),
        prompt=(
            "Return a schema-valid DATA_ERROR decision. Use asOfUtc "
            "2024-08-22T05:25:00Z, phase TRIGGER, state FLAT, scenario null, "
            "empty arrays, nextReviewAtUtc 2024-08-22T05:26:00Z, order null, "
            "and reason schema probe."
        ),
        images=[],
        schema=schema,
        temperature=0.0,
        max_output_tokens=1000,
    )
    proof = {
        "schemaSha256": sha256(SCHEMA),
        "model": response.model,
        "probedAtUtc": utc_text(int(datetime.now(timezone.utc).timestamp())),
        "usage": response.usage,
    }
    SCHEMA_PROBE.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PROBE.write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("GEMINI_SCHEMA_PROBE_OK")
    print(json.dumps(proof, ensure_ascii=False))
    return 0


def latest_resume_source(_: argparse.Namespace) -> int:
    try:
        _, config = load_secret()
        rates, _ = load_rates(config)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        config = None
        rates = None
    candidates = sorted(
        (path for path in RUN_ROOT.glob("*") if path.is_dir()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        if (path / "INVALIDATED_REPLAY.txt").exists():
            continue
        ledger = path / "decision_ledger.jsonl"
        if not ledger.exists() or not ledger.stat().st_size:
            continue
        summary_path = path / "summary.json"
        if summary_path.exists():
            try:
                if bool(json.loads(summary_path.read_text(encoding="utf-8"))["completed"]):
                    continue
            except (KeyError, OSError, json.JSONDecodeError):
                pass
        if config is not None and rates is not None:
            try:
                reconstruct_resume_state(path, rates, config)
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                continue
        print(path.name)
        return 0
    print("MENTOR_AI_REPLAY_NO_RESUMABLE_RUN", file=sys.stderr)
    return 2


def render_packet(
    config: dict[str, Any],
    as_of: str,
    phase: str,
    output: Path,
    candle_evidence: list[dict[str, Any]] | None = None,
    local_trigger_wakeup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    modes = {
        "MAP": ["map"],
        "REFINEMENT": ["refinement"],
        "TRIGGER": ["micro"],
        "PENDING_REVIEW": ["map", "micro"],
    }[phase]
    images: list[tuple[str, str]] = []
    for mode in modes:
        command = [
            sys.executable,
            str(ROOT / "scripts" / "render_mentor_week_asof.py"),
            "--cutoff", as_of,
            "--mode", mode,
            "--dataset", str(dataset_path(config)),
            "--output", str(output),
            "--warmup", str(config["warmupStartUtc"]),
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        images.append((mode, result.stdout.strip().splitlines()[-1]))

    rates, _ = load_rates(config)
    cutoff = parse_utc(as_of)
    indexes = np.flatnonzero(rates["time"] + 60 <= cutoff)
    if not len(indexes):
        raise SystemExit("as-of 이전에 확정된 M1 봉이 없습니다.")
    row = rates[indexes[-1]]
    point = float(config["point"])
    spread = float(row["spread"]) * point
    packet = {
        "symbol": config["symbol"],
        "asOfUtc": as_of,
        "phase": phase,
        "lastClosedM1": {
            "openTimeUtc": utc_text(int(row["time"])),
            "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"]),
        },
        "spreadPrice": spread,
        "brokerStopsLevelPrice": float(config.get("brokerStopsLevelPrice", 0)),
        "images": [
            {"mode": mode, "path": str(Path(path).resolve()), "sha256": sha256(Path(path))}
            for mode, path in images
        ],
        "candleEvidence": candle_evidence or [],
        "localTriggerWakeup": local_trigger_wakeup,
        "futureHidden": True,
    }
    (output / "packet.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return packet


def normalize_decision_routing(
    decision: dict[str, Any], as_of: str, phase: str
) -> dict[str, Any] | None:
    model_routing = {
        "asOfUtc": decision.get("asOfUtc"),
        "phase": decision.get("phase"),
    }
    engine_routing = {"asOfUtc": as_of, "phase": phase}
    if model_routing == engine_routing:
        return None
    decision.update(engine_routing)
    return {
        "reason": "ENGINE_AUTHORITATIVE_ROUTING",
        "model": model_routing,
        "engine": engine_routing,
    }


PHASE_ACTIONS: dict[str, set[str]] = {
    "MAP": {"QUERY_CANDLES", "WAIT", "WATCH_MAP", "PREPARE", "NO_TRADE", "DATA_ERROR"},
    "REFINEMENT": {"QUERY_CANDLES", "WAIT", "ARM", "CANCEL", "DATA_ERROR"},
    "TRIGGER": {"QUERY_CANDLES", "WAIT", "ORDER", "CANCEL", "DATA_ERROR"},
    "PENDING_REVIEW": {"QUERY_CANDLES", "ORDER", "CANCEL", "DATA_ERROR"},
}


def expected_transition_state(
    phase: str,
    action: str,
    previous: dict[str, Any] | None,
) -> str | None:
    fixed = {
        "WATCH_MAP": "WATCHING_MAP",
        "PREPARE": "PREPARED",
        "ARM": "ARMED",
        "ORDER": "PENDING",
        "CANCEL": "CANCELED",
        "NO_TRADE": "FLAT",
    }
    if action in fixed:
        return fixed[action]
    if action not in {"WAIT", "QUERY_CANDLES", "DATA_ERROR"}:
        return None
    if phase == "TRIGGER":
        return "ARMED"
    if phase == "PENDING_REVIEW":
        return "PENDING"
    if phase == "REFINEMENT":
        return "PREPARED"
    if phase == "MAP":
        if isinstance(previous, dict) and isinstance(previous.get("scenario"), dict):
            return str(previous.get("state", "PREPARED"))
        return "FLAT"
    return None


def normalize_decision_state(
    decision: dict[str, Any],
    previous: dict[str, Any] | None,
    phase: str | None = None,
) -> dict[str, Any] | None:
    action = str(decision.get("action", ""))
    effective_phase = str(phase or decision.get("phase", ""))
    expected = expected_transition_state(effective_phase, action, previous)
    if expected is None and phase is None and action in {"WAIT", "QUERY_CANDLES", "DATA_ERROR"}:
        expected = (
            str(previous.get("state", decision.get("state", "FLAT")))
            if isinstance(previous, dict) else str(decision.get("state", "FLAT"))
        )
    if expected is None:
        return None
    model_state = str(decision.get("state", ""))
    if model_state == expected:
        return None
    decision["state"] = expected
    return {
        "reason": "ENGINE_AUTHORITATIVE_STATE_TRANSITION",
        "action": action,
        "modelState": model_state,
        "engineState": expected,
    }


def validate_transition_contract(
    decision: dict[str, Any],
    previous: dict[str, Any] | None,
) -> list[str]:
    phase = str(decision.get("phase", ""))
    action = str(decision.get("action", ""))
    state = str(decision.get("state", ""))
    errors: list[str] = []
    allowed = PHASE_ACTIONS.get(phase)
    if allowed is None:
        return [f"unknown engine phase: {phase}"]
    if action not in allowed:
        errors.append(f"action {action} is not allowed in phase {phase}")
        return errors
    expected = expected_transition_state(phase, action, previous)
    if expected is None:
        errors.append(f"no engine transition for {phase}/{action}")
    elif state != expected:
        errors.append(f"engine transition {phase}/{action} requires state={expected}")
    if phase in {"REFINEMENT", "TRIGGER", "PENDING_REVIEW"}:
        scenario = decision.get("scenario")
        previous_scenario = previous.get("scenario") if isinstance(previous, dict) else None
        if not isinstance(scenario, dict) and not isinstance(previous_scenario, dict):
            errors.append(f"{phase} requires a frozen scenario")
    if phase == "PENDING_REVIEW":
        order = decision.get("order")
        previous_order = previous.get("order") if isinstance(previous, dict) else None
        if not isinstance(order, dict) and not isinstance(previous_order, dict):
            errors.append("PENDING_REVIEW requires a frozen order")
    return errors


def normalize_decision_queries(decision: dict[str, Any]) -> dict[str, Any] | None:
    queries = list(decision.get("candleQueries") or [])
    if decision.get("action") == "QUERY_CANDLES" or not queries:
        return None
    decision["candleQueries"] = []
    decision["_prefetchQueries"] = queries
    return {
        "reason": "ENGINE_DEFERRED_NON_QUERY_ACTION_CANDLES",
        "action": decision.get("action"),
        "deferredQueries": len(queries),
    }


def validate_pending_entry_side(
    decision: dict[str, Any], packet: dict[str, Any]
) -> list[str]:
    if decision.get("action") != "ORDER":
        return []
    scenario = decision.get("scenario")
    order = decision.get("order")
    if not isinstance(scenario, dict) or not isinstance(order, dict):
        return []
    try:
        entry = float(order["entry"])
        bid = float(packet["lastClosedM1"]["close"])
        ask = bid + float(packet["spreadPrice"])
    except (KeyError, TypeError, ValueError):
        return ["cannot validate pending entry against current Bid/Ask"]
    direction_value = str(scenario.get("direction", ""))
    if direction_value == "LONG" and entry >= ask:
        return [
            f"buy limit entry {entry:.5f} is not below current ask {ask:.5f}"
        ]
    if direction_value == "SHORT" and entry <= bid:
        return [
            f"sell limit entry {entry:.5f} is not above current bid {bid:.5f}"
        ]
    return []


def build_decision_prompt(
    *,
    contract: str,
    packet: dict[str, Any],
    phase: str,
    previous: dict[str, Any] | None,
    candle_evidence: list[dict[str, Any]] | None,
) -> str:
    phase_task = {
        "MAP": (
            "Read H1, M30, and M15 directly. Compare EXTERNAL_CONTINUATION, "
            "INTERNAL_ROTATION, and EXTERNAL_REVERSAL before choosing a scope. "
            "Freeze an objective and a causal H1/M30/M15 root OB only when both "
            "are visible. M5 may be queried only to verify the exact source wick "
            "of an internal objective; it cannot become the MAP root. PREPARE is "
            "a map decision, not order authorization."
        ),
        "REFINEMENT": (
            "Find only M30/M15/M5 child OBs that explain the same price event and "
            "displacement as the frozen root. Price overlap alone is not causal refinement."
        ),
        "TRIGGER": (
            "After the refined OB touch, evaluate the M15/M5 correction and M1 reaction. "
            "Require mature pre-existing liquidity, a sweep and recovery, a meaningful body "
            "CHoCH, and the first retest of its causal execution zone. Do not reuse consumed "
            "root or child touch events."
        ),
        "PENDING_REVIEW": (
            "Reauthorize or cancel the frozen pending order. The only permitted geometry change "
            "is an atomic DELIVERY_FVG_REPLACEMENT when packet.localDeliveryFvgCandidate is present: "
            "the original OB order must still be unfilled, owner/root-child/objective stay frozen, "
            "and all five exact M1 barIds must prove fresh FVG, directional body delivery, causal OB, "
            "and protected-swing break. Otherwise KEEP or CANCEL."
        ),
    }[phase]
    query_budget = packet.get("candleQueryBudget", {})
    query_budget_exhausted = bool(query_budget.get("mustDecideNow", False))
    evidence_instruction = (
        "Exact candidate candles are not yet available. Do not estimate structural prices "
        "from pixels. Return QUERY_CANDLES for the specific timeframe and approximate origin "
        "time needed to verify the candidate."
        if not candle_evidence
        else (
        "The candle-query budget for this phase is exhausted. Do not return QUERY_CANDLES. "
        "Use the supplied candleEvidence now. If it cannot prove every required causal field, "
        "return NO_TRADE with concrete missing-evidence reasons."
        if query_budget_exhausted else
        "Use candleEvidence for exact OHLC. If any causal source candle is still absent, "
        "request it once with QUERY_CANDLES; otherwise return the current phase decision "
        "with an empty candleQueries array."
        )
    )
    packet_without_images = {key: value for key, value in packet.items() if key != "images"}
    local_wakeup_instruction = (
        "\n\n[LOCAL TRIGGER WAKE-UP]\n"
        "packet.localTriggerWakeup contains complete OHLC-backed trigger-chain candidates "
        "screened without an AI call. It does not authorize an order. Judge whether one chain "
        "is meaningful under the frozen HTF scenario. For ORDER select its exact candidateKey "
        "as triggerCandidateKey; the engine resolves all seven barIds from that chain. Reject "
        "microstructure or unrelated candidates explicitly.\n"
        if packet.get("localTriggerWakeup") else ""
    )
    return (
        contract
        + "\n\n[CURRENT PHASE]\n"
        + phase_task
        + "\n\n[NUMERIC LINEAGE]\n"
        + "Never invent or round a structural price. Use engine-supplied barIds and candidate keys "
        + "for the execution zone, protected swing, mature liquidity, final sweep, CHoCH reference, and "
        + "CHoCH break. Query only a required candle that is absent. triggerLineage format is exactly "
        + "P=<UTC>;S=<UTC>;R=<UTC>;B=<UTC>. The engine derives executable Entry, SL, TP, "
        + "spread, broker stops, and frozen references from the selected source candles. "
        + "If a source candle is absent, return QUERY_CANDLES.\n"
        + evidence_instruction
        + "\n\n[ROUTING]\n"
        + "Use packet asOfUtc and phase exactly. The images contain no data after as-of. "
        + "When waiting, provide only concrete future price events and a later review time. "
        + "Return JSON matching the supplied schema.\n\n[PACKET]\n"
        + json.dumps(packet_without_images, ensure_ascii=False, separators=(",", ":"))
        + local_wakeup_instruction
        + "\n\n[PREVIOUS STATE]\n"
        + json.dumps(previous, ensure_ascii=False, separators=(",", ":"))
    )


def consume_reviewed_map_approach(
    decision: dict[str, Any], wake_event: str,
) -> bool:
    if wake_event != "ROOT_APPROACH" or decision.get("action") != "WATCH_MAP":
        return False
    before = list(decision.get("watchEvents") or [])
    decision["watchEvents"] = [
        event for event in before if str(event.get("kind")) != "ROOT_APPROACH"
    ]
    return len(decision["watchEvents"]) != len(before)


def _invoke_stage_provider(
    *,
    api_key: str,
    config: dict[str, Any],
    decision_provider: str,
    request_dir: Path,
    prompt: str,
    packet: dict[str, Any],
    schema_path: Path,
    schema_override: dict[str, Any] | None = None,
    model: str,
    role: str,
) -> Any:
    image_paths = [Path(item["path"]) for item in packet["images"]]
    media_resolutions = [
        str(
            config.get("mapMediaResolution", "MEDIA_RESOLUTION_MEDIUM")
            if item["mode"] == "map"
            else (
                "MEDIA_RESOLUTION_MEDIUM"
                if bool(config.get("forceEfficientMediaResolution", True))
                else config.get("detailMediaResolution", "MEDIA_RESOLUTION_HIGH")
            )
        )
        for item in packet["images"]
    ]
    max_output_tokens = output_token_limit(config, role)
    request_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"[REQUEST PACKET] role={role} model={model} "
        f"promptBytes={len(prompt.encode('utf-8'))} "
        f"images={len(image_paths)} maxOutputTokens="
        f"{max_output_tokens}",
        flush=True,
    )
    (request_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (request_dir / "packet.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if decision_provider == "manual-codex":
        from scripts.manual_replay_provider import wait_for_manual_decision

        return wait_for_manual_decision(
            request_dir=request_dir,
            prompt=prompt,
            images=image_paths,
            response_schema=(
                schema_override
                if schema_override is not None
                else json.loads(schema_path.read_text(encoding="utf-8"))
            ),
        )
    if decision_provider == "codex-cli":
        from scripts.codex_replay_provider import generate_codex_decision

        return generate_codex_decision(
            request_dir=request_dir,
            prompt=prompt,
            images=image_paths,
            schema=(
                schema_override
                if schema_override is not None
                else json.loads(schema_path.read_text(encoding="utf-8"))
            ),
            model=str(config.get("codexModel", "")) or None,
        )
    from scripts.gemini_replay_provider import generate_structured_decision

    return generate_structured_decision(
        api_key=api_key,
        model=model,
        prompt=prompt,
        images=image_paths,
        media_resolutions=media_resolutions,
        schema=(
            schema_override
            if schema_override is not None
            else json.loads(schema_path.read_text(encoding="utf-8"))
        ),
        temperature=float(config.get("temperature", 0.1)),
        max_output_tokens=max_output_tokens,
        raw_response_path=request_dir / "raw_response.json",
    )


def request_v2_map_decision(
    *,
    api_key: str,
    config: dict[str, Any],
    run_dir: Path,
    as_of: str,
    previous: dict[str, Any] | None,
    decision_provider: str,
    local_map_wakeup: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from scripts.gemini_replay_provider import GeminiReplayError

    wake_event = str((previous or {}).get("_wakeEvent", ""))
    if (
        isinstance(previous, dict)
        and previous.get("state") == "WATCHING_MAP"
        and wake_event in {"SOURCE_INVALIDATION", "OBJECTIVE_REACHED"}
    ):
        decision = {
            "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": "MAP",
            "_v2MapDecision": True, "action": "NO_TRADE", "state": "FLAT",
            "scenario": None, "candleQueries": [], "watchEvents": [],
            "nextReviewAtUtc": utc_text(((parse_utc(as_of) // 3600) + 1) * 3600),
            "order": None, "rejectionReasons": [f"LOCAL_MAP_TERMINATION: {wake_event}"],
            "reason": "The watched map ended locally before root approach; no model call was required.",
        }
        return decision, {
            "inputPacket": {"asOfUtc": as_of, "phase": "MAP", "images": []},
            "model": "local-engine", "usage": {"promptTokenCount": 0, "candidatesTokenCount": 0, "totalTokenCount": 0},
            "providerCallCount": 0, "providerCalls": [], "resolvedBarEvidence": [],
            "reviewPayload": None, "modelRouting": {"asOfUtc": as_of, "phase": "MAP"},
            "routingAdjustment": None, "stateAdjustment": None, "queryAdjustment": None,
            "decision": decision,
        }
    base = run_dir / "calls" / f"{as_of.replace(':', '-')}_map_v2"
    packet = render_packet(config, as_of, "MAP", base, local_trigger_wakeup=local_map_wakeup)
    bars = compact_bars(
        dataset_path(config), str(config["warmupStartUtc"]), as_of,
        limits={"H1": 96, "M30": 192, "M15": 384, "M1": 5760},
    )
    liquidity_candidates = structural_liquidity_candidates(bars, maximum=32)
    packet["structuralLiquidityCandidates"] = structural_liquidity_table(
        liquidity_candidates
    )
    allowed_objectives = {
        (str(item["barId"]), str(item["side"]))
        for item in liquidity_candidates
        if item.get("status") == "ACTIVE"
    }
    packet["compactBars"] = bars_for_prompt(
        {timeframe: rows for timeframe, rows in bars.items() if timeframe != "M1"},
        tail_limits={"H1": 18, "M30": 24, "M15": 24},
    )
    contract, contract_hashes = load_stage_contract("MAP")
    packet["contractHashes"] = contract_hashes
    previous_candidate = previous_map_candidate_for_review(
        previous, local_map_wakeup
    )
    if isinstance(previous_candidate, dict):
        allowed_objectives.add((
            str(previous_candidate.get("objectiveBarId", "")),
            str(previous_candidate.get("objectiveSide", "")),
        ))

    provider_calls: list[dict[str, Any]] = []
    if previous_candidate and wake_event == "ROOT_APPROACH":
        candidates = [copy.deepcopy(previous_candidate)]
    else:
        scout_prompt, scout_metrics = bounded_map_scout_prompt(
            contract, packet, config
        )
        try:
            scout = _invoke_stage_provider(
                api_key=api_key, config=config, decision_provider=decision_provider,
                request_dir=base / "scout", prompt=scout_prompt, packet=packet,
                schema_path=STAGE_SCHEMAS["MAP_SCOUT"], model=str(config["model"]),
                role="scout",
            )
        except GeminiReplayError as exc:
            exc.provider_calls = [{
                "role": "scout", "model": str(config["model"]), "usage": exc.usage,
                **scout_metrics,
            }]
            if exc.recoverable:
                decision = {
                    "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": "MAP",
                    "_v2MapDecision": True, "action": "NO_TRADE", "state": "FLAT",
                    "scenario": None, "candleQueries": [], "watchEvents": [],
                    "nextReviewAtUtc": utc_text(((parse_utc(as_of) // 3600) + 1) * 3600),
                    "order": None,
                    "rejectionReasons": [f"RECOVERABLE_MAP_SCOUT_OUTPUT: {exc}"],
                    "reason": "Malformed provider output was contained as a safe MAP miss.",
                }
                record = {
                    "inputPacket": packet, "model": str(config["model"]),
                    "usage": exc.usage, "providerCallCount": exc.provider_call_count,
                    "providerCalls": exc.provider_calls, "resolvedBarEvidence": [],
                    "reviewPayload": None, "providerRecovery": str(exc),
                    "modelRouting": {"asOfUtc": as_of, "phase": "MAP"},
                    "routingAdjustment": None, "stateAdjustment": None,
                    "queryAdjustment": None, "decision": decision,
                }
                (base / "decision.json").write_text(
                    json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                return decision, record
            raise
        provider_calls.append({
            "role": "scout", "model": scout.model, "usage": scout.usage,
            **scout_metrics,
        })
        scout_payload = scout.payload
        if str(scout_payload.get("phase")) != "MAP_SCOUT":
            raise ValueError("MAP_SCOUT response phase mismatch")
        candidates = list(scout_payload.get("candidates") or [])
        if previous_candidate:
            candidates = [copy.deepcopy(previous_candidate), *candidates]

        # The local detector has timing authority only, but its closed M15
        # opposite candle must not disappear before causal review. Pair it
        # with a scout-proposed objective as a comparison candidate; the
        # reviewer still has sole authority to approve or reject causality.
        candidates = augment_candidates_with_local_root(
            candidates,
            local_map_wakeup,
            liquidity_candidates=liquidity_candidates,
            current_bid=float(packet["lastClosedM1"]["close"]),
        )

    lookup_ids = {
        str(item.get(field, ""))
        for item in candidates
        for field in ("rootBarId", "objectiveBarId")
    }
    valid_candidates: list[dict[str, Any]] = []
    candidate_filter_rejections: list[str] = []
    current_bid = float(packet["lastClosedM1"]["close"])
    for candidate in candidates:
        try:
            root_id = str(candidate["rootBarId"])
            objective_id = str(candidate["objectiveBarId"])
            root = resolve_bar(bars, root_id)
            objective = resolve_bar(bars, objective_id)
            rejection = map_candidate_ohlc_rejection(
                candidate, root, objective, current_bid, allowed_objectives,
                compact=bars, local_map_wakeup=local_map_wakeup,
            )
            if rejection:
                candidate_filter_rejections.append(rejection)
                continue
            enriched = copy.deepcopy(candidate)
            enriched["resolvedRootOhlc"] = root
            enriched["resolvedObjectiveOhlc"] = objective
            enriched["objectiveStructure"] = next(
                (
                    copy.deepcopy(item)
                    for item in liquidity_candidates
                    if str(item.get("barId")) == objective_id
                    and str(item.get("side")) == str(candidate.get("objectiveSide"))
                ),
                None,
            )
            valid_candidates.append(enriched)
        except (KeyError, ValueError):
            candidate_filter_rejections.append(
                f"{candidate.get('candidateId')}: unavailable or malformed barId evidence"
            )
            continue

    for index, candidate in enumerate(valid_candidates, start=1):
        candidate["scoutCandidateId"] = str(candidate.get("candidateId", ""))
        candidate["candidateId"] = f"MAP-CANDIDATE-{index}"

    if not valid_candidates:
        decision = {
            "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": "MAP",
            "_v2MapDecision": True,
            "action": "NO_TRADE", "state": "FLAT", "scenario": None,
            "candleQueries": [], "watchEvents": [],
            "nextReviewAtUtc": utc_text(((parse_utc(as_of) // 3600) + 1) * 3600),
            "order": None, "rejectionReasons": [
                "MAP_SCOUT found no valid barId-backed candidate",
                *candidate_filter_rejections,
            ],
            "reason": "No root/objective candidate survived deterministic OHLC validation.",
        }
        evidence: list[dict[str, Any]] = []
        review_payload = None
    else:
        review_prompt, review_metrics = bounded_map_review_prompt(
            contract, packet, valid_candidates, previous_candidate, config
        )
        if decision_provider != "manual-codex":
            time.sleep(float(config.get("minimumCallIntervalSeconds", 15)))
        try:
            reviewer = _invoke_stage_provider(
                api_key=api_key, config=config, decision_provider=decision_provider,
                request_dir=base / "review", prompt=review_prompt, packet=packet,
                schema_path=STAGE_SCHEMAS["MAP_REVIEW"],
                model=str(config["reviewerModel"]),
                role="reviewer",
            )
        except GeminiReplayError as exc:
            failed_usage = dict(exc.usage)
            exc.provider_call_count += len(provider_calls)
            exc.usage = {
                key: sum(int(call["usage"].get(key, 0)) for call in provider_calls)
                + int(failed_usage.get(key, 0))
                for key in ("promptTokenCount", "candidatesTokenCount", "totalTokenCount")
            }
            exc.provider_calls = [*provider_calls, {
                "role": "reviewer", "model": str(config["reviewerModel"]),
                "usage": failed_usage,
                **review_metrics,
            }]
            if exc.recoverable:
                decision = {
                    "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": "MAP",
                    "_v2MapDecision": True, "action": "NO_TRADE", "state": "FLAT",
                    "scenario": None, "candleQueries": [], "watchEvents": [],
                    "nextReviewAtUtc": utc_text(((parse_utc(as_of) // 3600) + 1) * 3600),
                    "order": None,
                    "rejectionReasons": [f"RECOVERABLE_MAP_REVIEW_OUTPUT: {exc}"],
                    "reason": "Unreviewed MAP candidates were discarded without stopping replay.",
                }
                record = {
                    "inputPacket": packet,
                    "model": "+".join(str(call["model"]) for call in exc.provider_calls),
                    "usage": exc.usage, "providerCallCount": exc.provider_call_count,
                    "providerCalls": exc.provider_calls, "resolvedBarEvidence": [],
                    "reviewPayload": None, "providerRecovery": str(exc),
                    "modelRouting": {"asOfUtc": as_of, "phase": "MAP"},
                    "routingAdjustment": None, "stateAdjustment": None,
                    "queryAdjustment": None, "decision": decision,
                }
                (base / "decision.json").write_text(
                    json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                return decision, record
            raise
        provider_calls.append({
            "role": "reviewer", "model": reviewer.model, "usage": reviewer.usage,
            **review_metrics,
        })
        review_payload = reviewer.payload
        if str(review_payload.get("phase")) != "MAP_REVIEW":
            raise ValueError("MAP_REVIEW response phase mismatch")
        review_action_adjustment = None
        if str(review_payload.get("action")) == "WATCH":
            reviewed_id = str(review_payload.get("candidateId", ""))
            reviewed_candidate = next(
                (
                    item for item in valid_candidates
                    if str(item.get("candidateId")) == reviewed_id
                ),
                None,
            )
            if reviewed_candidate is not None:
                root_ohlc = reviewed_candidate.get("resolvedRootOhlc") or {}
                current_bar = packet["lastClosedM1"]
                overlaps_now = (
                    float(current_bar["low"]) <= float(root_ohlc["h"])
                    and float(current_bar["high"]) >= float(root_ohlc["l"])
                )
                if overlaps_now:
                    review_payload = copy.deepcopy(review_payload)
                    review_payload["action"] = "APPROVE"
                    review_action_adjustment = {
                        "reason": "WATCH_ROOT_ALREADY_TOUCHED_BY_LAST_CLOSED_M1",
                        "candidateId": reviewed_id,
                    }
        try:
            decision, selected_ids = canonical_map_decision(
                as_of=as_of, review=review_payload, candidates=valid_candidates, compact=bars,
                watch_review_minutes=int(config.get("maximumFlatReviewMinutes", 360)),
                delivery_wakeup=local_map_wakeup,
            )
        except (KeyError, TypeError, ValueError) as exc:
            decision = {
                "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": "MAP",
                "_v2MapDecision": True, "action": "NO_TRADE", "state": "FLAT",
                "scenario": None, "candleQueries": [], "watchEvents": [],
                "nextReviewAtUtc": utc_text(((parse_utc(as_of) // 3600) + 1) * 3600),
                "order": None, "rejectionReasons": [f"MAP_REVIEW_ADAPTER_REJECTED: {exc}"],
                "reason": "Reviewer output did not resolve to a valid engine-owned barId candidate.",
            }
            selected_ids = []
        consume_reviewed_map_approach(decision, wake_event)
        evidence = evidence_for_bars(bars, selected_ids, float(config["point"]))

    usage = {
        key: sum(int(call["usage"].get(key, 0)) for call in provider_calls)
        for key in ("promptTokenCount", "candidatesTokenCount", "totalTokenCount")
    }
    record = {
        "inputPacket": packet,
        "model": "+".join(str(call["model"]) for call in provider_calls),
        "usage": usage,
        "providerCallCount": len(provider_calls),
        "providerCalls": provider_calls,
        "resolvedBarEvidence": evidence,
        "reviewPayload": review_payload,
        "reviewActionAdjustment": locals().get("review_action_adjustment"),
        "candidateFilterRejections": candidate_filter_rejections,
        "modelRouting": {"asOfUtc": as_of, "phase": "MAP"},
        "routingAdjustment": None, "stateAdjustment": None, "queryAdjustment": None,
        "decision": decision,
    }
    (base / "decision.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return decision, record


def request_v2_stage_decision(
    *,
    api_key: str,
    config: dict[str, Any],
    run_dir: Path,
    as_of: str,
    phase: str,
    previous: dict[str, Any],
    candle_evidence: list[dict[str, Any]] | None,
    decision_provider: str,
    local_trigger_wakeup: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from scripts.gemini_replay_provider import GeminiReplayError

    base = run_dir / "calls" / f"{as_of.replace(':', '-')}_{phase.lower()}_v2"
    packet = render_packet(config, as_of, phase, base, candle_evidence, local_trigger_wakeup)
    limits = {
        "REFINEMENT": {"M30": 8, "M15": 16, "M5": 36, "M1": 30},
        "TRIGGER": {"M15": 12, "M5": 30, "M1": 90},
        "PENDING_REVIEW": {"H1": 12, "M15": 24, "M5": 36, "M1": 30},
    }[phase]
    bars = compact_bars(dataset_path(config), str(config["warmupStartUtc"]), as_of, limits=limits)
    # Pre-freeze M1 bars may prove that a lower-TF child created the delivery
    # which caused MAP to wake. They are source evidence, not retrospective
    # touch/trigger authority. canonical_stage_decision separately rejects any
    # child touch that predates the frozen MAP time.
    for block in candle_evidence or []:
        timeframe = str(block.get("tf", ""))
        if timeframe not in bars:
            bars[timeframe] = []
        known = {str(item.get("barId")) for item in bars[timeframe]}
        for candle in block.get("candles", []):
            origin = str(candle.get("openTimeUtc", ""))
            try:
                selected_id = f"{timeframe}:{parse_utc(origin)}"
            except ValueError:
                continue
            if selected_id in known:
                continue
            bars[timeframe].append({
                "barId": selected_id, "time": origin,
                "o": float(candle["open"]), "h": float(candle["high"]),
                "l": float(candle["low"]), "c": float(candle["close"]),
                "spreadPoints": float(candle.get("spreadPrice", 0.0)) / float(config["point"]),
            })
    if phase == "REFINEMENT":
        packet["refinementCandidates"] = refinement_candidate_table(
            refinement_candidates(bars, previous["scenario"])
        )
    if phase == "PENDING_REVIEW" and str(previous.get("_wakeEvent", "")) == "LOCAL_DELIVERY_FVG":
        packet["localDeliveryFvgCandidate"] = local_delivery_fvg_candidate_from_compact(
            bars, as_of, str(previous.get("scenario", {}).get("direction", ""))
        )
    packet["compactBars"] = bars_for_prompt(bars)
    contract, hashes = load_stage_contract(phase)
    packet["contractHashes"] = hashes
    prompt, prompt_metrics = bounded_stage_prompt(
        contract, packet, phase, previous, config
    )
    schema_override = None
    if phase == "REFINEMENT":
        allowed_child_ids = [
            str(row[0]) for row in packet["refinementCandidates"].get("data", [])
            if row
        ]
        if allowed_child_ids:
            schema_override = json.loads(
                STAGE_SCHEMAS[phase].read_text(encoding="utf-8")
            )
            schema_override["properties"]["childBarIds"]["items"]["enum"] = allowed_child_ids
    if phase == "TRIGGER" and isinstance(local_trigger_wakeup, dict):
        candidate_keys = [
            str(item.get("candidateKey"))
            for item in local_trigger_wakeup.get("candidates", [])
            if item.get("candidateKey")
        ]
        if candidate_keys:
            schema_override = json.loads(
                STAGE_SCHEMAS[phase].read_text(encoding="utf-8")
            )
            schema_override["properties"]["triggerCandidateKey"] = {
                "type": ["string", "null"],
                "enum": list(dict.fromkeys(candidate_keys)) + [None],
                "description": (
                    "For ORDER select exactly one engine-enumerated complete trigger chain. "
                    "The engine resolves its OHLC-backed barIds."
                ),
            }
            if "triggerCandidateKey" not in schema_override["required"]:
                schema_override["required"].append("triggerCandidateKey")
    try:
        response = _invoke_stage_provider(
            api_key=api_key, config=config, decision_provider=decision_provider,
            request_dir=base / "review", prompt=prompt, packet=packet,
            schema_path=STAGE_SCHEMAS[phase], schema_override=schema_override,
            model=str(config["reviewerModel"]),
            role="reviewer",
        )
    except GeminiReplayError as exc:
        exc.provider_calls = [{
            "role": "reviewer", "model": str(config["reviewerModel"]),
            "usage": exc.usage,
            **prompt_metrics,
        }]
        if exc.recoverable:
            cancel = phase == "PENDING_REVIEW"
            decision = {
                "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": phase,
                "action": "CANCEL" if cancel else "WAIT",
                "state": "CANCELED" if cancel else (
                    "ARMED" if phase == "TRIGGER" else "PREPARED"
                ),
                "scenario": copy.deepcopy(previous.get("scenario")),
                "candleQueries": [],
                "watchEvents": [] if phase == "TRIGGER" else copy.deepcopy(previous.get("watchEvents") or []),
                "nextReviewAtUtc": utc_text(parse_utc(as_of) + (900 if cancel else 3600)),
                "order": None,
                "rejectionReasons": [f"RECOVERABLE_{phase}_OUTPUT: {exc}"],
                "reason": "Malformed provider output was contained without authorizing an order.",
            }
            record = {
                "inputPacket": packet, "model": str(config["reviewerModel"]),
                "usage": exc.usage, "providerCallCount": exc.provider_call_count,
                "providerCalls": exc.provider_calls, "resolvedBarEvidence": [],
                "stagePayload": None, "providerRecovery": str(exc),
                "modelRouting": {"asOfUtc": as_of, "phase": phase},
                "routingAdjustment": None, "stateAdjustment": None,
                "queryAdjustment": None, "decision": decision,
            }
            (base / "decision.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            return decision, record
        raise
    payload = response.payload
    if str(payload.get("phase")) != phase:
        raise ValueError(f"{phase} response phase mismatch")
    if phase == "TRIGGER" and str(payload.get("action")) == "ORDER":
        selected_key = str(payload.get("triggerCandidateKey") or "")
        candidates = (
            local_trigger_wakeup.get("candidates", [])
            if isinstance(local_trigger_wakeup, dict) else []
        )
        selected_chain = next(
            (item for item in candidates if str(item.get("candidateKey")) == selected_key),
            None,
        )
        if selected_chain is None:
            payload = copy.deepcopy(payload)
            payload.update({
                "action": "WAIT", "triggerCandidateKey": None,
                "protectedSwingBarId": None, "matureLiquidityBarId": None,
                "sweepBarId": None, "sweepRecoveryBarId": None,
                "chochReferenceBarId": None, "chochBreakBarId": None,
                "executionBarId": None, "executionModel": None,
                "candleQueries": [],
                "reason": "ORDER rejected: no engine-enumerated trigger chain was present.",
            })
        else:
            payload = copy.deepcopy(payload)
            payload.update({
                "protectedSwingBarId": selected_chain["protectedSwingBarId"],
                "matureLiquidityBarId": selected_chain["matureLiquidityBarId"],
                "sweepBarId": selected_chain["sweepBarId"],
                "sweepRecoveryBarId": selected_chain["sweepRecoveryBarId"],
                "chochReferenceBarId": selected_chain["chochReferenceBarId"],
                "chochBreakBarId": selected_chain["chochBreakBarId"],
                "executionBarId": selected_chain["executionBarId"],
            })
    adapter_error = None
    try:
        decision, selected_ids = canonical_stage_decision(
            as_of=as_of, phase=phase, payload=payload, previous=previous, compact=bars,
            point=float(config["point"]),
            broker_stops=float(config.get("brokerStopsLevelPrice", 0.0)),
            spread_price=float(packet["spreadPrice"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        adapter_error = str(exc)
        fallback_action = "CANCEL" if phase == "PENDING_REVIEW" else "WAIT"
        fallback_state = "CANCELED" if phase == "PENDING_REVIEW" else (
            "ARMED" if phase == "TRIGGER" else "PREPARED"
        )
        decision = {
            "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": phase,
            "action": fallback_action, "state": fallback_state,
            "scenario": copy.deepcopy(previous.get("scenario")), "candleQueries": [],
            "watchEvents": (
                [] if phase == "TRIGGER"
                else copy.deepcopy(previous.get("watchEvents") or [])
            ),
            "nextReviewAtUtc": utc_text(parse_utc(as_of) + 3600),
            "order": None, "rejectionReasons": [f"STAGE_ADAPTER_REJECTED: {exc}"],
            "reason": "Invalid model barId selection was rejected without stopping replay.",
        }
        if phase == "TRIGGER" and isinstance(local_trigger_wakeup, dict):
            consumed = set(previous.get("_consumedTriggerSweepTimes") or [])
            consumed.update(
                str(item.get("candidateKey") or (
                    f"{item.get('sweepTimeUtc')}|{item.get('chochReferenceTimeUtc')}"
                ))
                for item in local_trigger_wakeup.get("candidates", [])
                if item.get("sweepTimeUtc")
            )
            decision["_consumedTriggerSweepTimes"] = sorted(consumed)
        selected_ids = []
    if (
        phase == "TRIGGER"
        and decision.get("action") == "WAIT"
        and isinstance(local_trigger_wakeup, dict)
    ):
        consumed = set(previous.get("_consumedTriggerSweepTimes") or [])
        consumed.update(
            str(item.get("candidateKey") or (
                f"{item.get('sweepTimeUtc')}|{item.get('chochReferenceTimeUtc')}"
            ))
            for item in local_trigger_wakeup.get("candidates", [])
            if item.get("sweepTimeUtc")
        )
        decision["_consumedTriggerSweepTimes"] = sorted(consumed)
    evidence = evidence_for_bars(bars, selected_ids, float(config["point"]))
    record = {
        "inputPacket": packet, "model": response.model, "usage": response.usage,
        "providerCallCount": 1,
        "providerCalls": [{
            "role": "reviewer", "model": response.model,
            "usage": response.usage, **prompt_metrics,
        }],
        "resolvedBarEvidence": evidence, "stagePayload": payload,
        "adapterError": adapter_error,
        "modelRouting": {"asOfUtc": as_of, "phase": phase},
        "routingAdjustment": None, "stateAdjustment": None, "queryAdjustment": None,
        "decision": decision,
    }
    (base / "decision.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return decision, record


def request_decision(
    *,
    api_key: str,
    config: dict[str, Any],
    run_dir: Path,
    as_of: str,
    phase: str,
    previous: dict[str, Any] | None,
    candle_evidence: list[dict[str, Any]] | None = None,
    query_round: int = 0,
    decision_provider: str = "gemini",
    local_trigger_wakeup: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if phase == "MAP":
        return request_v2_map_decision(
            api_key=api_key, config=config, run_dir=run_dir, as_of=as_of,
            previous=previous, decision_provider=decision_provider,
            local_map_wakeup=local_trigger_wakeup,
        )
    if not isinstance(previous, dict):
        raise ValueError(f"{phase} requires a frozen previous state")
    return request_v2_stage_decision(
        api_key=api_key, config=config, run_dir=run_dir, as_of=as_of,
        phase=phase, previous=previous, candle_evidence=candle_evidence,
        decision_provider=decision_provider, local_trigger_wakeup=local_trigger_wakeup,
    )

    # Legacy request path retained below for archived run reconstruction only.
    suffix = f"_q{query_round}" if query_round else ""
    output = run_dir / "calls" / f"{as_of.replace(':', '-')}_{phase.lower()}{suffix}"
    packet = render_packet(
        config, as_of, phase, output, candle_evidence, local_trigger_wakeup
    )
    maximum_query_rounds = int(config.get("maximumCandleQueryRoundsPerPhase", 2))
    packet["candleQueryBudget"] = {
        "used": query_round,
        "maximum": maximum_query_rounds,
        "remaining": max(0, maximum_query_rounds - query_round),
        "mustDecideNow": query_round >= maximum_query_rounds,
    }
    contract, contract_hashes = load_stage_contract(phase)
    packet["contractHashes"] = contract_hashes
    (output / "packet.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # Replace the legacy supplemental prompt, whose Korean literals were
    # corrupted in an earlier encoding conversion, with one canonical prompt.
    prompt = build_decision_prompt(
        contract=contract,
        packet=packet,
        phase=phase,
        previous=previous,
        candle_evidence=candle_evidence,
    )
    (output / "prompt.txt").write_text(prompt, encoding="utf-8")
    media_resolutions = [
        str(
            config.get("mapMediaResolution", "MEDIA_RESOLUTION_MEDIUM")
            if item["mode"] == "map"
            else (
                "MEDIA_RESOLUTION_MEDIUM"
                if bool(config.get("forceEfficientMediaResolution", True))
                else config.get("detailMediaResolution", "MEDIA_RESOLUTION_HIGH")
            )
        )
        for item in packet["images"]
    ]
    image_paths = [Path(item["path"]) for item in packet["images"]]
    if decision_provider == "manual-codex":
        from scripts.manual_replay_provider import wait_for_manual_decision

        response = wait_for_manual_decision(
            request_dir=output,
            prompt=prompt,
            images=image_paths,
            response_schema=json.loads(SCHEMA.read_text(encoding="utf-8")),
        )
    else:
        from scripts.gemini_replay_provider import generate_structured_decision

        response = generate_structured_decision(
            api_key=api_key,
            model=str(config["model"]),
            prompt=prompt,
            images=image_paths,
            media_resolutions=media_resolutions,
            schema=json.loads(SCHEMA.read_text(encoding="utf-8")),
            temperature=float(config.get("temperature", 0.1)),
            max_output_tokens=int(config.get("maxOutputTokens", 4096)),
        )
    decision = response.payload
    model_routing = {
        "asOfUtc": decision.get("asOfUtc"),
        "phase": decision.get("phase"),
    }
    routing_adjustment = normalize_decision_routing(decision, as_of, phase)
    state_adjustment = normalize_decision_state(decision, previous, phase)
    query_adjustment = normalize_decision_queries(decision)
    record = {
        "inputPacket": packet,
        "model": response.model,
        "usage": response.usage,
        "modelRouting": model_routing,
        "routingAdjustment": routing_adjustment,
        "stateAdjustment": state_adjustment,
        "queryAdjustment": query_adjustment,
        "decision": decision,
    }
    (output / "decision.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return decision, record


def query_budget_fallback_decision(
    *, as_of: str, config: dict[str, Any], exhausted_decision: dict[str, Any]
) -> dict[str, Any]:
    requested = [
        f"{item.get('tf')}@{item.get('aroundTimeUtc')}:{item.get('purpose')}"
        for item in exhausted_decision.get("candleQueries", [])
        if isinstance(item, dict)
    ]
    next_review = parse_utc(as_of) + int(
        config.get("maximumFlatReviewMinutes", 360)
    ) * 60
    return {
        "schemaVersion": "1.5.0",
        "asOfUtc": as_of,
        "phase": "MAP",
        "action": "NO_TRADE",
        "state": "FLAT",
        "scenario": None,
        "candleQueries": [],
        "watchEvents": [],
        "nextReviewAtUtc": utc_text(next_review),
        "order": None,
        "rejectionReasons": [
            "INSUFFICIENT_EVIDENCE_AFTER_QUERY_BUDGET: "
            + (", ".join(requested) if requested else "no concrete query supplied")
        ],
        "reason": (
            "The model did not reach an evidence-backed decision within the phase query "
            "budget. The ambiguous scenario is rejected without stopping the replay."
        ),
    }


def normalize_map_rejection_audit(
    decision: dict[str, Any],
    candle_evidence: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    """Attach factual queried OHLC to a generic MAP rejection without inventing structure."""
    if not (
        decision.get("phase") == "MAP"
        and decision.get("action") != "QUERY_CANDLES"
        and decision.get("scenario") is None
    ):
        return None

    rejection_reasons = [str(item) for item in decision.get("rejectionReasons", [])]
    existing = " ".join(rejection_reasons)
    if (
        re.search(r"\b(?:H1|M30|M15)\b", existing, flags=re.IGNORECASE)
        and re.search(r"\d{3,}(?:\.\d+)?", existing)
    ):
        return None

    evidence_items: list[str] = []
    used_timeframes: set[str] = set()
    for block in reversed(candle_evidence or []):
        timeframe = str(block.get("tf", ""))
        candles = list(block.get("candles") or [])
        if timeframe not in {"H1", "M30", "M15"} or timeframe in used_timeframes or not candles:
            continue
        candle = candles[-1]
        try:
            evidence_items.append(
                f"{timeframe} {candle['openTimeUtc']} "
                f"{float(candle['low']):.2f}-{float(candle['high']):.2f}"
            )
        except (KeyError, TypeError, ValueError):
            continue
        used_timeframes.add(timeframe)
        if len(evidence_items) == 3:
            break

    if not evidence_items:
        return None
    audit = (
        "ENGINE_MAP_EVIDENCE_AUDIT: queried candidates "
        + ", ".join(reversed(evidence_items))
        + "; the model did not authorize a causal root-objective pair."
    )
    decision["rejectionReasons"] = [*rejection_reasons, audit]
    return {"addedEvidenceAudit": audit}


def rejected_decision_fallback(
    *,
    as_of: str,
    phase: str,
    rejected_decision: dict[str, Any],
    previous_decision: dict[str, Any] | None,
    errors: list[str],
    config: dict[str, Any],
    candle_evidence: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Convert a nonfatal model error into a conservative event-gated state."""
    as_of_timestamp = parse_utc(as_of)
    if isinstance(previous_decision, dict) and isinstance(previous_decision.get("scenario"), dict):
        fallback = copy.deepcopy(previous_decision)
        fallback["asOfUtc"] = as_of
        fallback["phase"] = phase
        phase_state_action = {
            "MAP": ("PREPARED", "PREPARE"),
            "REFINEMENT": ("PREPARED", "WAIT"),
            "TRIGGER": ("ARMED", "WAIT"),
            "PENDING_REVIEW": ("PENDING", "ORDER"),
        }
        state, action = phase_state_action.get(phase, ("PREPARED", "WAIT"))
        fallback["state"] = state
        fallback["action"] = action
        fallback["candleQueries"] = []
        if phase == "PENDING_REVIEW" and isinstance(fallback.get("order"), dict):
            fallback["order"]["lastReauthorizedAtUtc"] = as_of
            fallback["nextReviewAtUtc"] = utc_text(as_of_timestamp + 3600)
        fallback["rejectionReasons"] = [
            *[str(item) for item in fallback.get("rejectionReasons", [])],
            "ENGINE_PRESERVED_LAST_VALID_STATE: " + "; ".join(errors),
        ]
        fallback["reason"] = (
            "The latest model response failed semantic validation. The engine preserved the "
            "last validated scenario without authorizing a new order or changing frozen fields."
        )
    else:
        requested_review = rejected_decision.get("nextReviewAtUtc")
        try:
            next_review = parse_utc(str(requested_review))
        except (TypeError, ValueError):
            next_review = as_of_timestamp
        minimum_review = as_of_timestamp + int(
            config.get("minimumFlatReviewMinutes", 240)
        ) * 60
        maximum_review = as_of_timestamp + int(
            config.get("maximumFlatReviewMinutes", 360)
        ) * 60
        fallback = {
            "_engineFallback": True,
            "schemaVersion": "1.5.0",
            "asOfUtc": as_of,
            "phase": "MAP",
            "action": "NO_TRADE",
            "state": "FLAT",
            "scenario": None,
            "candleQueries": [],
            "watchEvents": [],
            "nextReviewAtUtc": utc_text(min(max(next_review, minimum_review), maximum_review)),
            "order": None,
            "rejectionReasons": [
                "ENGINE_REJECTED_UNVERIFIED_MODEL_DECISION: " + "; ".join(errors)
            ],
            "reason": (
                "The latest model response was not safe to execute. The engine remains flat "
                "and waits for the next coarse MAP review instead of polling every M1 bar."
            ),
        }
        normalize_map_rejection_audit(fallback, candle_evidence)

    normalize_review_schedule(fallback, config, as_of_timestamp)
    return fallback


def evidence_candle_keys(
    candle_evidence: list[dict[str, Any]] | None,
) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()
    for result in candle_evidence or []:
        timeframe = str(result.get("tf", ""))
        for candle in result.get("candles", []):
            try:
                keys.add((timeframe, parse_utc(str(candle["openTimeUtc"]))))
            except (KeyError, TypeError, ValueError):
                continue
    return keys


def evidence_candles_by_key(
    candle_evidence: list[dict[str, Any]] | None,
) -> dict[tuple[str, int], dict[str, Any]]:
    candles: dict[tuple[str, int], dict[str, Any]] = {}
    for result in candle_evidence or []:
        timeframe = str(result.get("tf", ""))
        for candle in result.get("candles", []):
            try:
                candles[(timeframe, parse_utc(str(candle["openTimeUtc"])))] = candle
            except (KeyError, TypeError, ValueError):
                continue
    return candles


def price_matches_candle_ohlc(price_value: float, candle: dict[str, Any], point: float) -> bool:
    return any(
        math.isfinite(candidate) and abs(price_value - candidate) <= point
        for candidate in (
            float(candle.get("open", math.nan)),
            float(candle.get("high", math.nan)),
            float(candle.get("low", math.nan)),
            float(candle.get("close", math.nan)),
        )
    )


def expand_trigger_lineage(order: dict[str, Any]) -> None:
    raw = str(order.get("triggerLineage", ""))
    values: dict[str, str] = {}
    for item in raw.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        values[key.strip().upper()] = value.strip()
    required = {"P", "S", "R", "B"}
    if set(values) != required:
        raise ValueError("triggerLineage must contain exactly P,S,R,B")
    for value in values.values():
        parse_utc(value)
    order["triggerProtectedSwingSourceTimeUtc"] = values["P"]
    order["sweepExtremeSourceTimeUtc"] = values["S"]
    order["chochReferenceSourceTimeUtc"] = values["R"]
    order["chochBreakTimeUtc"] = values["B"]


def normalize_numeric_claims_from_evidence(
    decision: dict[str, Any],
    candle_evidence: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    adjustments: list[dict[str, Any]] = []
    scenario = decision.get("scenario")
    if not isinstance(scenario, dict):
        return adjustments
    evidence = evidence_candles_by_key(candle_evidence)
    point = float(config.get("point", 0.0))

    def replace(
        container: dict[str, Any], field: str, value: Any, reason: str,
        *, authoritative: bool = False,
    ) -> None:
        old = container.get(field)
        if old is None:
            container[field] = value
            adjustments.append({"field": field, "model": old, "engine": value, "reason": reason})
            return
        try:
            difference = abs(float(old) - float(value))
        except (TypeError, ValueError):
            if authoritative and old != value:
                container[field] = value
                adjustments.append({"field": field, "model": old, "engine": value, "reason": reason})
            return
        # Semantic prices must not be silently moved to another structure. Only
        # absorb point-sized serialization drift; broker-owned values are exact.
        if difference > point / 10 and (authoritative or difference <= point * 1.01):
            container[field] = value
            adjustments.append({"field": field, "model": old, "engine": value, "reason": reason})

    objective = scenario.get("objective")
    if isinstance(objective, dict):
        try:
            candle = evidence.get((
                str(objective["sourceTf"]), parse_utc(str(objective["sourceTime"])),
            ))
            if candle is not None:
                field = "high" if objective.get("side") == "BSL" else "low"
                replace(
                    objective, "price", float(candle[field]),
                    f"objective source {field}", authoritative=True,
                )
        except (KeyError, TypeError, ValueError):
            pass

    zones = [scenario.get("rootOb"), *scenario.get("refinementPath", [])]
    for zone_index, zone in enumerate(zones):
        if not isinstance(zone, dict):
            continue
        try:
            candle = evidence.get((str(zone["tf"]), parse_utc(str(zone["originTime"]))))
        except (KeyError, TypeError, ValueError):
            candle = None
        if candle is None:
            continue
        ohlc = [float(candle[name]) for name in ("open", "high", "low", "close")]
        for boundary in ("low", "high"):
            try:
                claimed = float(zone[boundary])
            except (KeyError, TypeError, ValueError):
                continue
            nearest = min(ohlc, key=lambda value: abs(value - claimed))
            replace(
                zone, boundary, nearest,
                f"{'root' if zone_index == 0 else 'child'} origin nearest OHLC",
            )

    for event in decision.get("watchEvents", []):
        if not isinstance(event, dict):
            continue
        kind = str(event.get("kind", ""))
        if kind not in {"SWEEP_CANDIDATE", "CHOCH_REFERENCE", "ORDER_CANCEL_LEVEL"}:
            continue
        try:
            candle = evidence.get((
                str(event["sourceTf"]), parse_utc(str(event["sourceTimeUtc"])),
            ))
        except (KeyError, TypeError, ValueError):
            candle = None
        if candle is None:
            continue
        comparison = str(event.get("comparison", ""))
        if comparison == "CROSS_ABOVE":
            price_value = float(candle["high"])
        elif comparison == "CROSS_BELOW":
            price_value = float(candle["low"])
        else:
            claimed = float(event.get("price", math.nan))
            price_value = min(
                (float(candle["high"]), float(candle["low"])),
                key=lambda value: abs(value - claimed),
            )
        # The model owns the semantic source candle; the engine owns its exact
        # executable price. This prevents rounding or copied-price drift from
        # consuming another model call.
        replace(event, "price", price_value, f"{kind} source wick", authoritative=True)

    order = decision.get("order")
    if isinstance(order, dict):
        try:
            expand_trigger_lineage(order)
        except ValueError:
            return adjustments
        direction_value = str(scenario.get("direction", ""))
        try:
            execution = evidence.get(("M1", parse_utc(str(order["executionOriginTime"]))))
        except (KeyError, TypeError, ValueError):
            execution = None
        if execution is not None:
            ohlc = [float(execution[name]) for name in ("open", "high", "low", "close")]
            for boundary in ("executionLow", "executionHigh"):
                claimed = float(order.get(boundary, math.nan))
                replace(order, boundary, min(ohlc, key=lambda value: abs(value - claimed)), "execution origin OHLC")
            proximal = float(order["executionHigh"] if direction_value == "LONG" else order["executionLow"])
            replace(order, "entry", proximal, "execution proximal boundary")
            replace(order, "actualSpread", float(execution.get("spreadPrice", 0.0)), "execution spread", authoritative=True)
        lineage_fields = (
            (
                "triggerProtectedSwing", "triggerProtectedSwingSourceTimeUtc",
                "low" if direction_value == "LONG" else "high",
            ),
            (
                "sweepExtreme", "sweepExtremeSourceTimeUtc",
                "low" if direction_value == "LONG" else "high",
            ),
            (
                "chochReferencePrice", "chochReferenceSourceTimeUtc",
                "high" if direction_value == "LONG" else "low",
            ),
        )
        for price_field, time_field, wick_field in lineage_fields:
            try:
                source = evidence.get(("M1", parse_utc(str(order[time_field]))))
            except (KeyError, TypeError, ValueError):
                source = None
            if source is not None:
                replace(
                    order, price_field, float(source[wick_field]),
                    f"{price_field} source {wick_field}",
                )
        root = scenario.get("rootOb", {})
        children = list(scenario.get("refinementPath", []))
        replace(order, "rootOriginTime", str(root.get("originTime", "")), "frozen root", authoritative=True)
        replace(
            order, "childOriginTime",
            str(children[-1].get("originTime", "")) if children else "",
            "frozen final child", authoritative=True,
        )
        replace(
            order, "objectiveSourceTime", str(objective.get("sourceTime", "")),
            "frozen objective source", authoritative=True,
        )
        order["lastReauthorizedAtUtc"] = str(decision.get("asOfUtc", ""))
        replace(order, "brokerStopsLevelPrice", float(config.get("brokerStopsLevelPrice", 0.0)), "broker specification", authoritative=True)
        required_buffer = max(
            point,
            float(order.get("actualSpread", 0.0)),
            float(config.get("brokerStopsLevelPrice", 0.0)),
        )
        if float(order.get("slBuffer", 0.0)) < required_buffer:
            replace(order, "slBuffer", required_buffer, "hard SL buffer minimum", authoritative=True)
        if isinstance(objective, dict):
            replace(order, "takeProfit", float(objective["price"]), "frozen objective", authoritative=True)
        required_prices = (
            "executionLow", "executionHigh", "triggerProtectedSwing",
            "sweepExtreme", "slBuffer",
        )
        if all(order.get(field) is not None for field in required_prices):
            if direction_value == "LONG":
                stop_loss = min(
                    float(order["executionLow"]),
                    float(order["triggerProtectedSwing"]),
                    float(order["sweepExtreme"]),
                    float(children[-1]["low"]) if children else float(root["low"]),
                    float(scenario["sourceInvalidation"]),
                ) - float(order["slBuffer"])
            else:
                stop_loss = max(
                    float(order["executionHigh"]),
                    float(order["triggerProtectedSwing"]),
                    float(order["sweepExtreme"]),
                    float(children[-1]["high"]) if children else float(root["high"]),
                    float(scenario["sourceInvalidation"]),
                ) + float(order["slBuffer"])
            replace(order, "stopLoss", stop_loss, "deterministic structural SL", authoritative=True)
    return adjustments


def evidence_price_anchors(
    candle_evidence: list[dict[str, Any]] | None,
) -> list[float]:
    anchors: list[float] = []
    for result in candle_evidence or []:
        for candle in result.get("candles", []):
            for field in ("high", "low"):
                try:
                    anchors.append(float(candle[field]))
                except (KeyError, TypeError, ValueError):
                    continue
    return anchors


def compact_evidence_for_prompt(
    evidence: list[dict[str, Any]],
    previous: dict[str, Any] | None,
    phase: str,
) -> list[dict[str, Any]]:
    scenario = previous.get("scenario") if isinstance(previous, dict) else None
    if not isinstance(scenario, dict):
        return evidence[-4:]
    wanted: set[tuple[str, str]] = set()
    root = scenario.get("rootOb")
    if isinstance(root, dict):
        wanted.add((str(root.get("tf", "")), str(root.get("originTime", ""))))
    objective = scenario.get("objective")
    if isinstance(objective, dict):
        wanted.add((str(objective.get("sourceTf", "")), str(objective.get("sourceTime", ""))))
    for child in scenario.get("refinementPath", []):
        if isinstance(child, dict):
            wanted.add((str(child.get("tf", "")), str(child.get("originTime", ""))))

    selected: list[dict[str, Any]] = []
    seen_blocks: set[tuple[str, tuple[str, ...]]] = set()
    for block in evidence:
        timeframe = str(block.get("tf", ""))
        candles = list(block.get("candles", []))
        times = [str(candle.get("openTimeUtc", "")) for candle in candles]
        backs_claim = any((timeframe, timestamp) in wanted for timestamp in times)
        purpose = str(block.get("purpose", ""))
        phase_candidate = (
            phase == "REFINEMENT" and purpose == "CHILD_OB"
        ) or (
            phase in {"TRIGGER", "PENDING_REVIEW"}
            and purpose in {"SWEEP", "CHOCH", "EXECUTION_ZONE"}
        )
        if not (backs_claim or phase_candidate):
            continue
        relevant_positions = [
            index for index, timestamp in enumerate(times)
            if (timeframe, timestamp) in wanted
        ]
        if relevant_positions and not phase_candidate:
            center = relevant_positions[-1]
            candles = candles[max(0, center - 1):center + 2]
        key = (timeframe, tuple(str(candle.get("openTimeUtc", "")) for candle in candles))
        if key in seen_blocks:
            continue
        seen_blocks.add(key)
        selected.append({**block, "candles": candles})
    return selected or evidence[-2:]


def recovery_queries_for_missing_origins(
    decision: dict[str, Any],
    errors: list[str],
) -> list[dict[str, Any]]:
    missing = "\n".join(errors)
    scenario = decision.get("scenario")
    order = decision.get("order")
    if not isinstance(scenario, dict):
        return []
    candidates: list[tuple[str, str, str, str]] = []
    root = scenario.get("rootOb")
    if "root origin is not backed" in missing and isinstance(root, dict):
        candidates.append(("recover-root", str(root.get("tf", "")), str(root.get("originTime", "")), "ROOT_OB"))
    for index, child in enumerate(scenario.get("refinementPath", [])):
        if f"child[{index}] origin is not backed" in missing and isinstance(child, dict):
            candidates.append((f"recover-child-{index}", str(child.get("tf", "")), str(child.get("originTime", "")), "CHILD_OB"))
    objective = scenario.get("objective")
    if "objective origin is not backed" in missing and isinstance(objective, dict):
        candidates.append((
            "recover-objective", str(objective.get("sourceTf", "")),
            str(objective.get("sourceTime", "")), "OBJECTIVE",
        ))
    if "execution origin is not backed" in missing and isinstance(order, dict):
        candidates.append((
            "recover-execution", "M1", str(order.get("executionOriginTime", "")),
            "EXECUTION_ZONE",
        ))
    if isinstance(order, dict):
        order_sources = (
            ("triggerProtectedSwing", "triggerProtectedSwingSourceTimeUtc", "CHOCH"),
            ("sweepExtreme", "sweepExtremeSourceTimeUtc", "SWEEP"),
            ("chochReference", "chochReferenceSourceTimeUtc", "CHOCH"),
            ("chochBreak", "chochBreakTimeUtc", "CHOCH"),
        )
        for label, time_field, purpose in order_sources:
            if f"{label} source is not backed" in missing:
                candidates.append((
                    f"recover-{label}", "M1", str(order.get(time_field, "")), purpose,
                ))
    for index, event in enumerate(decision.get("watchEvents", [])):
        if not isinstance(event, dict):
            continue
        kind = str(event.get("kind", ""))
        if f"watch event {kind} origin is not backed" not in missing:
            continue
        purpose = {
            "SWEEP_CANDIDATE": "SWEEP",
            "CHOCH_REFERENCE": "CHOCH",
            "ORDER_CANCEL_LEVEL": "INVALIDATION",
        }.get(kind)
        if purpose:
            candidates.append((
                f"recover-watch-{index}", str(event.get("sourceTf", "")),
                str(event.get("sourceTimeUtc", "")), purpose,
            ))
    queries: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for query_id, timeframe, origin, purpose in candidates:
        key = (timeframe, origin)
        if not timeframe or not origin or key in seen:
            continue
        seen.add(key)
        queries.append({
            "queryId": query_id,
            "tf": timeframe,
            "aroundTimeUtc": origin,
            "before": 2,
            "after": 2,
            "purpose": purpose,
        })
    return queries[:4]


def validate_decision(
    decision: dict[str, Any],
    config: dict[str, Any],
    as_of: int,
    candle_evidence: list[dict[str, Any]] | None = None,
    previous_decision: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = validate_transition_contract(decision, previous_decision)
    action = str(decision.get("action", ""))
    state = str(decision.get("state", ""))
    required_states = {
        "WATCH_MAP": "WATCHING_MAP",
        "PREPARE": "PREPARED",
        "ARM": "ARMED",
        "ORDER": "PENDING",
        "CANCEL": "CANCELED",
        "NO_TRADE": "FLAT",
    }
    expected_state = required_states.get(action)
    if expected_state and state != expected_state:
        errors.append(f"{action} requires state={expected_state}")
    queries = decision.get("candleQueries", [])
    if action == "QUERY_CANDLES":
        if not isinstance(queries, list) or not 1 <= len(queries) <= 4:
            errors.append("QUERY_CANDLES requires 1..4 candleQueries")
    elif queries:
        errors.append("candleQueries must be empty unless action is QUERY_CANDLES")
    try:
        next_review = parse_utc(str(decision["nextReviewAtUtc"]))
    except (KeyError, TypeError, ValueError):
        return ["invalid nextReviewAtUtc"]
    if next_review <= as_of:
        errors.append("next review must be later than as-of")
    state = str(decision.get("state", "FLAT"))
    if state in {"FLAT", "WATCHING_MAP"}:
        maximum = int(config["maximumFlatReviewMinutes"])
    elif state == "PENDING":
        maximum = int(config.get("maximumPendingReviewMinutes", 60))
    else:
        maximum = int(config.get("maximumScenarioReviewMinutes", 360))
    if next_review > as_of + maximum * 60:
        errors.append(f"next review exceeds {maximum} minute state limit")
    for event in decision.get("watchEvents", []):
        try:
            if parse_utc(str(event["validUntilUtc"])) <= as_of:
                errors.append(f"expired watch event: {event.get('eventId')}")
            if not math.isfinite(float(event["price"])):
                errors.append(f"invalid watch price: {event.get('eventId')}")
        except (KeyError, TypeError, ValueError):
            errors.append("malformed watch event")
    scenario = decision.get("scenario")
    if isinstance(scenario, dict):
        point = float(config.get("point", 0.0))
        evidence_by_key = evidence_candles_by_key(candle_evidence)
        zones = [scenario.get("rootOb"), *scenario.get("refinementPath", [])]
        for zone_index, zone in enumerate(zones):
            if not isinstance(zone, dict):
                errors.append("missing root/refinement zone")
                continue
            if float(zone.get("low", math.nan)) >= float(zone.get("high", math.nan)):
                errors.append("zone low must be below high")
            try:
                if parse_utc(str(zone["originTime"])) > as_of:
                    errors.append("future zone origin")
            except (KeyError, TypeError, ValueError):
                errors.append("invalid zone origin time")
            if action != "QUERY_CANDLES":
                try:
                    zone_key = (str(zone["tf"]), parse_utc(str(zone["originTime"])))
                    source_candle = evidence_by_key.get(zone_key)
                    if source_candle is not None:
                        for boundary in ("low", "high"):
                            if not price_matches_candle_ohlc(
                                float(zone[boundary]), source_candle, point
                            ):
                                label = "root" if zone_index == 0 else f"child[{zone_index - 1}]"
                                errors.append(
                                    f"{label} {boundary} is not an OHLC boundary of its origin candle"
                                )
                except (KeyError, TypeError, ValueError):
                    pass
        if action != "QUERY_CANDLES":
            evidence_keys = evidence_candle_keys(candle_evidence)
            claimed: list[tuple[str, str, str]] = []
            root = scenario.get("rootOb")
            if isinstance(root, dict):
                claimed.append(("root", str(root.get("tf", "")), str(root.get("originTime", ""))))
            for index, zone in enumerate(scenario.get("refinementPath", [])):
                if isinstance(zone, dict):
                    claimed.append((f"child[{index}]", str(zone.get("tf", "")), str(zone.get("originTime", ""))))
            objective = scenario.get("objective")
            if isinstance(objective, dict):
                claimed.append(("objective", str(objective.get("sourceTf", "")), str(objective.get("sourceTime", ""))))
            for label, timeframe, origin in claimed:
                try:
                    key = (timeframe, parse_utc(origin))
                except ValueError:
                    continue
                if key not in evidence_keys:
                    errors.append(f"{label} origin is not backed by queried candle OHLC")
        root = scenario.get("rootOb", {})
        children = scenario.get("refinementPath", [])
        objective = scenario.get("objective", {})
        direction_value = str(scenario.get("direction", ""))
        expected_zone_direction = "BULLISH" if direction_value == "LONG" else "BEARISH"
        expected_objective_side = "BSL" if direction_value == "LONG" else "SSL"
        if isinstance(root, dict) and root.get("direction") != expected_zone_direction:
            errors.append("root OB direction conflicts with scenario direction")
        if any(
            isinstance(child, dict) and child.get("direction") != expected_zone_direction
            for child in children
        ):
            errors.append("refinement direction conflicts with scenario direction")
        if isinstance(objective, dict) and objective.get("side") != expected_objective_side:
            errors.append("objective side conflicts with scenario direction")
        if isinstance(root, dict) and isinstance(objective, dict):
            try:
                objective_price = float(objective["price"])
                if direction_value == "LONG" and objective_price <= float(root["high"]):
                    errors.append("LONG objective is not beyond the root OB delivery range")
                if direction_value == "SHORT" and objective_price >= float(root["low"]):
                    errors.append("SHORT objective is not beyond the root OB delivery range")
            except (KeyError, TypeError, ValueError):
                errors.append("invalid objective/root delivery geometry")
        if action != "QUERY_CANDLES" and isinstance(objective, dict):
            try:
                objective_key = (
                    str(objective["sourceTf"]),
                    parse_utc(str(objective["sourceTime"])),
                )
                objective_candle = evidence_by_key.get(objective_key)
                expected_field = "high" if objective.get("side") == "BSL" else "low"
                if (
                    objective_candle is not None
                    and abs(float(objective["price"]) - float(objective_candle[expected_field])) > point
                ):
                    errors.append(
                        f"objective price is not the source candle {expected_field}"
                    )
            except (KeyError, TypeError, ValueError):
                pass
        for event in decision.get("watchEvents", []):
            kind = str(event.get("kind", ""))
            price_value = float(event.get("price", math.nan))
            source_candle = None
            try:
                source_key = (
                    str(event["sourceTf"]),
                    parse_utc(str(event["sourceTimeUtc"])),
                )
                source_candle = evidence_by_key.get(source_key)
            except (KeyError, TypeError, ValueError):
                errors.append(f"watch event {kind} has invalid source origin")
            if source_candle is not None:
                try:
                    available = parse_utc(str(source_candle["availableTimeUtc"]))
                except (KeyError, TypeError, ValueError):
                    available = source_key[1]
                if available > as_of:
                    errors.append(f"watch event {kind} uses future source candle")
            expected_comparison = {
                "ROOT_APPROACH": "CROSS_BELOW" if direction_value == "LONG" else "CROSS_ABOVE",
                "CHILD_TOUCH": "TOUCH",
                "SOURCE_INVALIDATION": "CROSS_BELOW" if direction_value == "LONG" else "CROSS_ABOVE",
                "OBJECTIVE_REACHED": "CROSS_ABOVE" if expected_objective_side == "BSL" else "CROSS_BELOW",
                "SWEEP_CANDIDATE": "CROSS_BELOW" if direction_value == "LONG" else "CROSS_ABOVE",
                "CHOCH_REFERENCE": "CROSS_ABOVE" if direction_value == "LONG" else "CROSS_BELOW",
            }.get(kind)
            if expected_comparison and event.get("comparison") != expected_comparison:
                errors.append(f"watch event {kind} comparison conflicts with scenario direction")
            if kind in {"SWEEP_CANDIDATE", "CHOCH_REFERENCE"} and event.get("sourceTf") != "M1":
                errors.append(f"watch event {kind} source must be M1")
            if kind == "ROOT_APPROACH":
                anchors = [float(
                    root.get("high" if scenario.get("direction") == "LONG" else "low", math.nan)
                )]
            elif kind == "CHILD_TOUCH" and children:
                anchors = [float(children[-1].get(
                    "high" if scenario.get("direction") == "LONG" else "low",
                    math.nan,
                ))]
            elif kind == "SOURCE_INVALIDATION":
                anchors = [float(scenario.get("sourceInvalidation", math.nan))]
            elif kind == "OBJECTIVE_REACHED":
                anchors = [float(objective.get("price", math.nan))]
            elif kind in {"SWEEP_CANDIDATE", "CHOCH_REFERENCE", "ORDER_CANCEL_LEVEL"}:
                if source_candle is None:
                    errors.append(f"watch event {kind} origin is not backed by queried candle OHLC")
                    anchors = []
                elif event.get("comparison") == "CROSS_ABOVE":
                    anchors = [float(source_candle["high"])]
                elif event.get("comparison") == "CROSS_BELOW":
                    anchors = [float(source_candle["low"])]
                else:
                    anchors = [float(source_candle["high"]), float(source_candle["low"])]
            else:
                anchors = []
            if not any(
                math.isfinite(anchor) and abs(price_value - anchor) <= point
                for anchor in anchors
            ):
                errors.append(f"watch event {kind} price is not backed by frozen/query evidence")
    initial_intent = (
        isinstance(decision.get("order"), dict)
        and decision["order"].get("executionModel") == "HTF_OB_REACTION_INTENT"
        and decision["order"].get("intentOnly") is True
        and decision.get("phase") == "REFINEMENT"
    )
    if initial_intent:
        errors.extend(validate_initial_causal_intent(decision, config, as_of))
        return errors
    if decision.get("action") == "ORDER":
        order = decision.get("order")
        if not isinstance(scenario, dict) or not isinstance(order, dict):
            errors.append("ORDER requires scenario and order")
        else:
            is_delivery_replacement = (
                order.get("executionModel") == "DELIVERY_FVG_REPLACEMENT"
            )
            is_causal_intent = (
                order.get("executionModel") == "HTF_OB_REACTION_INTENT"
                and order.get("intentOnly") is True
            )
            if is_causal_intent:
                common_intent_fields = (
                    "entry", "stopLoss", "takeProfit", "rootOriginTime",
                    "childOriginTime", "objectiveSourceTime", "actualSpread",
                    "brokerStopsLevelPrice", "slBuffer", "lastReauthorizedAtUtc",
                )
                missing = [field for field in common_intent_fields if field not in order]
                if missing:
                    errors.append("causal intent could not be normalized: " + ",".join(missing))
                    return errors
                try:
                    if parse_utc(str(order["lastReauthorizedAtUtc"])) != as_of:
                        errors.append("intent lastReauthorizedAtUtc must equal current as-of")
                except (TypeError, ValueError):
                    errors.append("invalid intent lastReauthorizedAtUtc")
                root = scenario.get("rootOb", {})
                children = scenario.get("refinementPath", [])
                objective = scenario.get("objective", {})
                if order.get("rootOriginTime") != root.get("originTime"):
                    errors.append("intent rootOriginTime differs from scenario root")
                if children and order.get("childOriginTime") != children[-1].get("originTime"):
                    errors.append("intent childOriginTime differs from final refinement")
                if order.get("objectiveSourceTime") != objective.get("sourceTime"):
                    errors.append("intent objectiveSourceTime differs from scenario objective")
                previous_order = (
                    previous_decision.get("order")
                    if isinstance(previous_decision, dict) else None
                )
                if not isinstance(previous_order, dict) or not previous_order.get("intentOnly"):
                    errors.append("causal intent reauthorization has no frozen prior intent")
                else:
                    changed = [
                        field for field in sorted(set(previous_order) | set(order))
                        if field != "lastReauthorizedAtUtc"
                        and previous_order.get(field) != order.get(field)
                    ]
                    if changed:
                        errors.append("frozen causal intent changed: " + ",".join(changed))
                if decision.get("phase") != "PENDING_REVIEW" or decision.get("state") != "PENDING":
                    errors.append("causal intent reauthorization must remain PENDING_REVIEW/PENDING")
                return errors
            if not is_delivery_replacement:
                try:
                    expand_trigger_lineage(order)
                except ValueError as exc:
                    errors.append(str(exc))
            common_engine_fields = (
                "entry", "stopLoss", "takeProfit", "rootOriginTime",
                "childOriginTime", "objectiveSourceTime",
                "actualSpread", "brokerStopsLevelPrice", "slBuffer",
                "lastReauthorizedAtUtc",
            )
            trigger_engine_fields = (
                "executionOriginTime",
                "executionLow", "executionHigh", "triggerProtectedSwing",
                "triggerProtectedSwingSourceTimeUtc", "sweepExtreme",
                "sweepExtremeSourceTimeUtc", "chochReferencePrice",
                "chochReferenceSourceTimeUtc", "chochBreakTimeUtc",
                "matureLiquidityPrice", "matureLiquiditySourceTimeUtc",
                "sweepRecoveryTimeUtc",
                "refinedTouchBarId", "refinedTouchTimeUtc",
            )
            engine_fields = common_engine_fields + (
                () if is_delivery_replacement else trigger_engine_fields
            )
            missing_engine_fields = [field for field in engine_fields if field not in order]
            if missing_engine_fields:
                errors.append(
                    "ORDER could not be normalized: " + ",".join(missing_engine_fields)
                )
                return errors
            entry, sl, tp = float(order["entry"]), float(order["stopLoss"]), float(order["takeProfit"])
            direction_value = scenario.get("direction")
            if direction_value == "LONG" and not (sl < entry < tp):
                errors.append("invalid LONG price geometry")
            if direction_value == "SHORT" and not (tp < entry < sl):
                errors.append("invalid SHORT price geometry")
            minimum = max(float(config["point"]), float(config.get("brokerStopsLevelPrice", 0)))
            if not bool(config.get("brokerSpecResolved", False)):
                errors.append("broker symbol specification is unknown")
            if min(abs(entry - sl), abs(entry - tp)) < minimum:
                errors.append("order distance is inside hard minimum")
            if not scenario.get("refinementPath"):
                errors.append("ORDER has no causal refinement")
            execution_low = float(order.get(
                "deliveryFvgLow" if is_delivery_replacement else "executionLow", math.nan
            ))
            execution_high = float(order.get(
                "deliveryFvgHigh" if is_delivery_replacement else "executionHigh", math.nan
            ))
            protected = float(order.get(
                "deliveryProtectedSwing" if is_delivery_replacement
                else "triggerProtectedSwing", math.nan
            ))
            sweep_extreme = (
                protected if is_delivery_replacement
                else float(order.get("sweepExtreme", math.nan))
            )
            actual_spread = float(order.get("actualSpread", math.nan))
            broker_stops = float(order.get("brokerStopsLevelPrice", math.nan))
            sl_buffer = float(order.get("slBuffer", math.nan))
            if not math.isfinite(actual_spread) or actual_spread < 0:
                errors.append("invalid actualSpread")
                actual_spread = math.inf
            if not math.isfinite(broker_stops) or broker_stops < 0:
                errors.append("invalid brokerStopsLevelPrice")
                broker_stops = math.inf
            if abs(broker_stops - float(config.get("brokerStopsLevelPrice", 0))) > point:
                errors.append("order brokerStopsLevelPrice differs from frozen broker spec")
            required_buffer = max(point, actual_spread, broker_stops)
            if not math.isfinite(sl_buffer) or sl_buffer + point < required_buffer:
                errors.append("SL buffer is below spread/stops/tick hard minimum")
            if not execution_low < execution_high:
                errors.append("invalid execution zone geometry")
            if direction_value == "LONG":
                if abs(entry - execution_high) > point:
                    errors.append("LONG entry must use execution zone proximal high")
                if (
                    not is_delivery_replacement
                    and sl > min(execution_low, protected, sweep_extreme) - sl_buffer + point
                ):
                    errors.append("LONG SL is not beyond execution/protected/sweep invalidation")
            if direction_value == "SHORT":
                if abs(entry - execution_low) > point:
                    errors.append("SHORT entry must use execution zone proximal low")
                if (
                    not is_delivery_replacement
                    and sl < max(execution_high, protected, sweep_extreme) + sl_buffer - point
                ):
                    errors.append("SHORT SL is not beyond execution/protected/sweep invalidation")
            if abs(tp - float(scenario.get("objective", {}).get("price", math.nan))) > point:
                errors.append("TP differs from frozen objective liquidity")
            try:
                if parse_utc(str(order["lastReauthorizedAtUtc"])) != as_of:
                    errors.append("ORDER lastReauthorizedAtUtc must equal current as-of")
            except (KeyError, TypeError, ValueError):
                errors.append("invalid ORDER lastReauthorizedAtUtc")
            root = scenario.get("rootOb", {})
            children = scenario.get("refinementPath", [])
            objective = scenario.get("objective", {})
            if order.get("rootOriginTime") != root.get("originTime"):
                errors.append("order rootOriginTime differs from scenario root")
            if children and order.get("childOriginTime") != children[-1].get("originTime"):
                errors.append("order childOriginTime differs from final refinement")
            if order.get("objectiveSourceTime") != objective.get("sourceTime"):
                errors.append("order objectiveSourceTime differs from scenario objective")
            if not is_delivery_replacement:
                try:
                    execution_key = ("M1", parse_utc(str(order["executionOriginTime"])))
                    execution_candle = evidence_by_key.get(execution_key)
                    if execution_candle is None:
                        errors.append("execution origin is not backed by queried M1 candle OHLC")
                    else:
                        if abs(actual_spread - float(execution_candle.get("spreadPrice", math.nan))) > point:
                            errors.append("actualSpread differs from execution candle spreadPrice")
                        for boundary in ("executionLow", "executionHigh"):
                            if not price_matches_candle_ohlc(
                                float(order[boundary]), execution_candle, point
                            ):
                                errors.append(
                                    f"{boundary} is not an OHLC boundary of execution candle"
                                )
                except (KeyError, TypeError, ValueError):
                    errors.append("invalid executionOriginTime")
            if is_delivery_replacement:
                replacement_fields = (
                    "originalExecutionModel", "originalEntry", "originalOrderCanceledAtUtc",
                    "deliveryFvgLeftTimeUtc", "deliveryFvgMiddleTimeUtc",
                    "deliveryFvgRightTimeUtc", "deliveryFvgLow", "deliveryFvgHigh",
                    "deliveryCausalObTimeUtc", "deliveryProtectedSwing",
                    "deliveryProtectedSwingTimeUtc", "deliveryFirstRetestRequired",
                )
                missing_replacement = [
                    field for field in replacement_fields if field not in order
                ]
                if missing_replacement:
                    errors.append(
                        "delivery replacement could not be normalized: "
                        + ",".join(missing_replacement)
                    )
                previous_order = (
                    previous_decision.get("order")
                    if isinstance(previous_decision, dict) else None
                )
                # A KEEP review of an already-created replacement is a frozen
                # order reauthorization, not a second atomic replacement.  Its
                # original three-candle evidence belongs to the creation
                # decision and is intentionally absent from later compact
                # packets.  Revalidate immutability here and leave the exact
                # FVG/causal checks to the creation branch below.
                if (
                    isinstance(previous_order, dict)
                    and previous_order.get("executionModel")
                    == "DELIVERY_FVG_REPLACEMENT"
                ):
                    mutable_fields = {"lastReauthorizedAtUtc"}
                    changed = [
                        field
                        for field in sorted(set(previous_order) | set(order))
                        if field not in mutable_fields
                        and previous_order.get(field) != order.get(field)
                    ]
                    if changed:
                        errors.append(
                            "frozen delivery replacement changed: " + ",".join(changed)
                        )
                    previous_scenario = (
                        previous_decision.get("scenario")
                        if isinstance(previous_decision, dict) else None
                    )
                    if scenario != previous_scenario:
                        errors.append("delivery replacement reauthorization changed frozen scenario")
                    if decision.get("phase") != "PENDING_REVIEW":
                        errors.append("delivery replacement reauthorization must be PENDING_REVIEW")
                    if decision.get("state") != "PENDING":
                        errors.append("delivery replacement reauthorization must remain PENDING")
                    return errors
                if (
                    not isinstance(previous_order, dict)
                    or previous_order.get("executionModel") not in {
                        "HTF_OB_REACTION", "HTF_OB_REACTION_INTENT",
                    }
                ):
                    errors.append("delivery replacement has no unfilled original OB order")
                else:
                    if abs(float(order.get("originalEntry", math.nan)) - float(previous_order["entry"])) > point:
                        errors.append("delivery replacement originalEntry differs from frozen OB order")
                    if abs(tp - float(previous_order["takeProfit"])) > point:
                        errors.append("delivery replacement changed the frozen objective")
                try:
                    left_time = parse_utc(str(order["deliveryFvgLeftTimeUtc"]))
                    middle_time = parse_utc(str(order["deliveryFvgMiddleTimeUtc"]))
                    right_time = parse_utc(str(order["deliveryFvgRightTimeUtc"]))
                    causal_time = parse_utc(str(order["deliveryCausalObTimeUtc"]))
                    delivery_protected_time = parse_utc(str(order["deliveryProtectedSwingTimeUtc"]))
                    left_candle = evidence_by_key.get(("M1", left_time))
                    middle_candle = evidence_by_key.get(("M1", middle_time))
                    right_candle = evidence_by_key.get(("M1", right_time))
                    causal_candle = evidence_by_key.get(("M1", causal_time))
                    delivery_protected_candle = evidence_by_key.get(("M1", delivery_protected_time))
                    if not all((left_candle, middle_candle, right_candle, causal_candle, delivery_protected_candle)):
                        errors.append("delivery replacement lineage is not backed by queried M1 OHLC")
                    else:
                        if not (middle_time == left_time + 60 and right_time == middle_time + 60):
                            errors.append("delivery FVG bars are not consecutive")
                        if right_time + 60 != as_of:
                            errors.append("delivery replacement was not decided at FVG confirmation")
                        expected_low = float(
                            left_candle["high"] if direction_value == "LONG" else right_candle["high"]
                        )
                        expected_high = float(
                            right_candle["low"] if direction_value == "LONG" else left_candle["low"]
                        )
                        if abs(execution_low - expected_low) > point or abs(execution_high - expected_high) > point:
                            errors.append("delivery FVG boundaries differ from three-candle OHLC")
                        if not execution_low < execution_high:
                            errors.append("delivery candles do not form a directional FVG")
                        if abs(actual_spread - float(right_candle.get("spreadPrice", math.nan))) > point:
                            errors.append("delivery replacement spread differs from confirmation candle")
                        protected_wick = float(
                            delivery_protected_candle["high"]
                            if direction_value == "LONG" else delivery_protected_candle["low"]
                        )
                        if abs(float(order["deliveryProtectedSwing"]) - protected_wick) > point:
                            errors.append("delivery protected swing differs from source wick")
                        if direction_value == "LONG":
                            if float(middle_candle["close"]) <= float(middle_candle["open"]):
                                errors.append("bullish delivery middle candle is not bullish")
                            if float(middle_candle["close"]) <= protected_wick:
                                errors.append("bullish delivery did not body-break protected swing")
                            if float(causal_candle["close"]) >= float(causal_candle["open"]):
                                errors.append("bullish delivery causal OB is not bearish")
                            if (
                                isinstance(previous_order, dict)
                                and sl > min(
                                    float(previous_order["stopLoss"]),
                                    float(causal_candle["low"]) - sl_buffer,
                                ) + point
                            ):
                                errors.append("bullish delivery SL is not beyond causal OB/original invalidation")
                        else:
                            if float(middle_candle["close"]) >= float(middle_candle["open"]):
                                errors.append("bearish delivery middle candle is not bearish")
                            if float(middle_candle["close"]) >= protected_wick:
                                errors.append("bearish delivery did not body-break protected swing")
                            if float(causal_candle["close"]) <= float(causal_candle["open"]):
                                errors.append("bearish delivery causal OB is not bullish")
                            if (
                                isinstance(previous_order, dict)
                                and sl < max(
                                    float(previous_order["stopLoss"]),
                                    float(causal_candle["high"]) + sl_buffer,
                                ) - point
                            ):
                                errors.append("bearish delivery SL is not beyond causal OB/original invalidation")
                        if causal_time > middle_time or delivery_protected_time >= middle_time:
                            errors.append("delivery cause/protected swing does not predate displacement")
                    if str(order["originalOrderCanceledAtUtc"]) != utc_text(as_of):
                        errors.append("original OB order was not canceled atomically at replacement")
                    if order.get("originalExecutionModel") not in {
                        "HTF_OB_REACTION", "HTF_OB_REACTION_INTENT",
                    }:
                        errors.append("delivery replacement original order was not a causal OB intent")
                    if order.get("deliveryFirstRetestRequired") is not True:
                        errors.append("delivery replacement does not require the first retest")
                except (KeyError, TypeError, ValueError):
                    errors.append("invalid delivery replacement lineage")
                previous_scenario_for_replacement = (
                    previous_decision.get("scenario")
                    if isinstance(previous_decision, dict) else None
                )
                if not isinstance(previous_scenario_for_replacement, dict):
                    errors.append("delivery replacement has no frozen previous scenario")
                else:
                    for field in (
                        "scenarioId", "direction", "scope", "objective",
                        "rootOb", "sourceInvalidation", "refinementPath",
                    ):
                        if scenario.get(field) != previous_scenario_for_replacement.get(field):
                            errors.append(
                                f"delivery replacement changed frozen scenario field: {field}"
                            )
                if decision.get("phase") != "PENDING_REVIEW":
                    errors.append("delivery replacement must be created in PENDING_REVIEW")
                if decision.get("state") != "PENDING":
                    errors.append("delivery replacement must remain PENDING")
                # DELIVERY_FVG_REPLACEMENT has its own causal contract above.
                # It must not be forced through the POI/sweep/CHoCH fields used
                # by an HTF_OB_REACTION trigger.
                return errors
            lineage = (
                (
                    "triggerProtectedSwing", "triggerProtectedSwingSourceTimeUtc",
                    "low" if direction_value == "LONG" else "high",
                ),
                (
                    "sweepExtreme", "sweepExtremeSourceTimeUtc",
                    "low" if direction_value == "LONG" else "high",
                ),
                (
                    "chochReference", "chochReferenceSourceTimeUtc",
                    "high" if direction_value == "LONG" else "low",
                ),
            )
            for label, time_field, wick_field in lineage:
                price_field = "chochReferencePrice" if label == "chochReference" else label
                try:
                    source_time = parse_utc(str(order[time_field]))
                    source_candle = evidence_by_key.get(("M1", source_time))
                    if source_time > as_of:
                        errors.append(f"{label} source is in the future")
                    if source_candle is None:
                        errors.append(f"{label} source is not backed by queried M1 candle OHLC")
                    elif abs(float(order[price_field]) - float(source_candle[wick_field])) > point:
                        errors.append(f"{label} price differs from source candle {wick_field}")
                except (KeyError, TypeError, ValueError):
                    errors.append(f"invalid {label} source lineage")
            try:
                touch_time = parse_utc(str(order["refinedTouchTimeUtc"]))
                mature_time = parse_utc(str(order["matureLiquiditySourceTimeUtc"]))
                sweep_time = parse_utc(str(order["sweepExtremeSourceTimeUtc"]))
                recovery_time = parse_utc(str(order["sweepRecoveryTimeUtc"]))
                reference_time = parse_utc(str(order["chochReferenceSourceTimeUtc"]))
                break_time = parse_utc(str(order["chochBreakTimeUtc"]))
                execution_time = parse_utc(str(order["executionOriginTime"]))
                if order.get("refinedTouchBarId") != scenario.get("refinedTouchBarId"):
                    errors.append("order refined touch differs from frozen scenario touch")
                if str(order.get("refinedTouchTimeUtc")) != str(scenario.get("refinedTouchTimeUtc")):
                    errors.append("order refined touch time differs from frozen scenario touch")
                frozen_at = scenario.get("frozenAtUtc")
                if not frozen_at:
                    errors.append("scenario is missing frozenAtUtc")
                elif touch_time < parse_utc(str(frozen_at)):
                    errors.append("refined child touch predates frozen MAP scenario")
                touch_candle = evidence_by_key.get(("M1", touch_time))
                mature_candle = evidence_by_key.get(("M1", mature_time))
                sweep_candle = evidence_by_key.get(("M1", sweep_time))
                recovery_candle = evidence_by_key.get(("M1", recovery_time))
                execution_candle = evidence_by_key.get(("M1", execution_time))
                if touch_candle is None:
                    errors.append("refined child touch is not backed by queried M1 candle OHLC")
                if mature_candle is None:
                    errors.append("mature liquidity is not backed by queried M1 candle OHLC")
                if not touch_time < sweep_time:
                    errors.append("final sweep must occur after refined child touch on a later M1 bar")
                if not mature_time < sweep_time:
                    errors.append("swept liquidity was not mature before final sweep")
                if mature_time == sweep_time:
                    errors.append("mature liquidity and final sweep reuse the same candle")
                if not sweep_time <= recovery_time < break_time:
                    errors.append("sweep recovery must occur from the sweep candle through before CHoCH")
                if sweep_time >= break_time:
                    errors.append("CHoCH break must occur after final sweep")
                if reference_time >= break_time:
                    errors.append("CHoCH reference must exist before its body break")
                if not sweep_time <= execution_time <= break_time:
                    errors.append("execution OB is outside the sweep-to-CHoCH displacement")
                if mature_candle is not None and sweep_candle is not None and recovery_candle is not None:
                    mature_price = float(
                        mature_candle["low"] if direction_value == "LONG" else mature_candle["high"]
                    )
                    if abs(float(order["matureLiquidityPrice"]) - mature_price) > point:
                        errors.append("mature liquidity price differs from source candle wick")
                    if direction_value == "LONG" and not (
                        float(sweep_candle["low"]) < mature_price
                        and float(recovery_candle["close"]) > mature_price
                    ):
                        errors.append("LONG sweep did not pierce mature SSL and recover above before CHoCH")
                    if direction_value == "SHORT" and not (
                        float(sweep_candle["high"]) > mature_price
                        and float(recovery_candle["close"]) < mature_price
                    ):
                        errors.append("SHORT sweep did not pierce mature BSL and recover below before CHoCH")
                if execution_candle is not None:
                    opposite = (
                        direction_value == "LONG"
                        and float(execution_candle["close"]) < float(execution_candle["open"])
                    ) or (
                        direction_value == "SHORT"
                        and float(execution_candle["close"]) > float(execution_candle["open"])
                    )
                    if not opposite:
                        errors.append("execution OB is not an opposite-color candle")
            except (KeyError, TypeError, ValueError):
                errors.append("invalid touch/maturity/trigger chronology")
            try:
                break_time = parse_utc(str(order["chochBreakTimeUtc"]))
                break_candle = evidence_by_key.get(("M1", break_time))
                if break_time > as_of:
                    errors.append("chochBreak source is in the future")
                if break_candle is None:
                    errors.append("chochBreak source is not backed by queried M1 candle OHLC")
                else:
                    reference = float(order["chochReferencePrice"])
                    close = float(break_candle["close"])
                    if direction_value == "LONG" and close <= reference:
                        errors.append("LONG CHoCH break candle did not close above reference")
                    if direction_value == "SHORT" and close >= reference:
                        errors.append("SHORT CHoCH break candle did not close below reference")
                if parse_utc(str(order["sweepExtremeSourceTimeUtc"])) > break_time:
                    errors.append("CHoCH break precedes the final sweep")
            except (KeyError, TypeError, ValueError):
                errors.append("invalid chochBreakTimeUtc")
    if decision.get("state") == "PENDING" and not isinstance(decision.get("order"), dict):
        errors.append("PENDING state requires the frozen order")
    if (
        decision.get("phase") == "TRIGGER"
        and action in {"WAIT", "PREPARE", "ARM"}
        and isinstance(decision.get("scenario"), dict)
    ):
        trigger_watch_kinds = {
            str(event.get("kind")) for event in decision.get("watchEvents", [])
        }
        if trigger_watch_kinds & {"ROOT_APPROACH", "CHILD_TOUCH"}:
            errors.append("TRIGGER cannot reuse consumed root/child touch events")
        if (
            not bool(config.get("localTriggerWakeupEnabled", True))
            and not trigger_watch_kinds & {"SWEEP_CANDIDATE", "CHOCH_REFERENCE"}
        ):
            errors.append("TRIGGER WAIT requires a concrete sweep or CHoCH watch level")
    previous_scenario = (
        previous_decision.get("scenario")
        if isinstance(previous_decision, dict)
        else None
    )
    if (
        action != "QUERY_CANDLES"
        and decision.get("phase") == "MAP"
        and decision.get("scenario") is None
        and not bool(decision.get("_engineFallback", False))
        and not bool(decision.get("_v2MapDecision", False))
    ):
        evidence = " ".join(str(item) for item in decision.get("rejectionReasons", []))
        has_tf = bool(re.search(r"\b(?:H1|M30|M15)\b", evidence, flags=re.IGNORECASE))
        has_price = bool(re.search(r"\d{3,}(?:\.\d+)?", evidence))
        if not (has_tf and has_price):
            errors.append("MAP rejection lacks concrete TF and price candidate audit")
    if (
        decision.get("phase") == "MAP"
        and action == "PREPARE"
        and isinstance(decision.get("scenario"), dict)
        and not (
            isinstance(previous_scenario, dict)
            and previous_scenario.get("scenarioId") == decision["scenario"].get("scenarioId")
        )
    ):
        audit_text = " ".join([
            str(decision["scenario"].get("scope", "")),
            str(decision.get("reason", "")),
            *(str(item) for item in decision.get("rejectionReasons", [])),
        ])
        missing_scopes = [
            scope for scope in (
                "EXTERNAL_CONTINUATION",
                "INTERNAL_ROTATION",
                "EXTERNAL_REVERSAL",
            )
            if scope not in audit_text
        ]
        if missing_scopes:
            errors.append(
                "MAP scope comparison missing: " + ",".join(missing_scopes)
            )
    current_scenario = decision.get("scenario")
    if (
        decision.get("action") != "QUERY_CANDLES"
        and decision.get("phase") in {"REFINEMENT", "TRIGGER", "PENDING_REVIEW"}
        and isinstance(previous_scenario, dict)
        and isinstance(current_scenario, dict)
    ):
        frozen_fields = ["scenarioId", "direction", "scope", "objective", "rootOb"]
        if decision.get("phase") != "REFINEMENT":
            frozen_fields.append("sourceInvalidation")
        for field in frozen_fields:
            if current_scenario.get(field) != previous_scenario.get(field):
                errors.append(f"frozen scenario field changed: {field}")
        previous_path = list(previous_scenario.get("refinementPath", []))
        current_path = list(current_scenario.get("refinementPath", []))
        if current_path[:len(previous_path)] != previous_path:
            errors.append("frozen refinement lineage was changed or removed")
        if decision.get("phase") in {"TRIGGER", "PENDING_REVIEW"} and current_path != previous_path:
            errors.append("refinement lineage cannot change after trigger phase begins")
        if decision.get("phase") == "REFINEMENT" and current_path:
            child = current_path[-1]
            expected_invalidation = float(
                child["low"] if current_scenario.get("direction") == "LONG" else child["high"]
            )
            if abs(float(current_scenario.get("sourceInvalidation", math.nan)) - expected_invalidation) > point:
                errors.append("causal child did not inherit execution invalidation authority")
    previous_order = (
        previous_decision.get("order")
        if isinstance(previous_decision, dict)
        else None
    )
    current_order = decision.get("order")
    if (
        decision.get("phase") == "PENDING_REVIEW"
        and isinstance(previous_order, dict)
        and isinstance(current_order, dict)
    ):
        atomic_replacement = (
            previous_order.get("executionModel") in {
                "HTF_OB_REACTION", "HTF_OB_REACTION_INTENT",
            }
            and current_order.get("executionModel") == "DELIVERY_FVG_REPLACEMENT"
            and current_order.get("originalExecutionModel")
            == previous_order.get("executionModel")
        )
        if not atomic_replacement:
            mutable_fields = {"lastReauthorizedAtUtc"}
            changed = [
                field for field in sorted(set(previous_order) | set(current_order))
                if field not in mutable_fields and previous_order.get(field) != current_order.get(field)
            ]
            if changed:
                errors.append("frozen pending order changed: " + ",".join(changed))
    return errors


def normalize_review_schedule(
    decision: dict[str, Any], config: dict[str, Any], as_of: int
) -> dict[str, Any] | None:
    adjustments: dict[str, Any] = {}
    if (
        decision.get("state") == "FLAT"
        and decision.get("scenario") is None
        and decision.get("action") in {"WAIT", "NO_TRADE"}
    ):
        old_value = str(decision.get("nextReviewAtUtc", ""))
        removed_events = len(decision.get("watchEvents") or [])
        decision["watchEvents"] = []
        minimum_review = as_of + int(
            config.get("minimumFlatReviewMinutes", 240)
        ) * 60
        maximum_review = as_of + int(
            config.get("maximumFlatReviewMinutes", 360)
        ) * 60
        try:
            requested_review = parse_utc(old_value)
        except (TypeError, ValueError):
            requested_review = maximum_review
        # The analyst may request an earlier map review when a structure is
        # developing. The engine only prevents minute-by-minute polling and
        # reviews that are so late they would structurally miss new objectives.
        new_value = utc_text(
            min(max(requested_review, minimum_review), maximum_review)
        )
        decision["nextReviewAtUtc"] = new_value
        if old_value != new_value or removed_events:
            adjustments.update({
                "reason": "FLAT_WITHOUT_CAUSAL_SCENARIO",
                "modelNextReviewAtUtc": old_value,
                "engineNextReviewAtUtc": new_value,
                "removedUnownedWatchEvents": removed_events,
            })
    scenario = decision.get("scenario")
    state = str(decision.get("state", ""))
    if isinstance(scenario, dict) and state in {"WATCHING_MAP", "PREPARED", "ARMED", "TRIGGERED", "PENDING"}:
        direction_value = str(scenario.get("direction", ""))
        root = scenario.get("rootOb", {})
        children = scenario.get("refinementPath", [])
        events = list(decision.get("watchEvents") or [])
        if decision.get("phase") == "REFINEMENT" and children:
            removed_root = any(
                str(event.get("kind")) == "ROOT_APPROACH" for event in events
            )
            events = [
                event for event in events
                if str(event.get("kind")) != "ROOT_APPROACH"
            ]
            if not any(str(event.get("kind")) == "CHILD_TOUCH" for event in events):
                child = children[-1]
                events.append({
                    "eventId": "engine-final-child-touch",
                    "kind": "CHILD_TOUCH",
                    "comparison": "TOUCH",
                    "price": float(child.get(
                        "high" if direction_value == "LONG" else "low"
                    )),
                    "sourceTf": child.get("tf"),
                    "sourceTimeUtc": child.get("originTime"),
                })
                adjustments["addedFinalChildTouch"] = True
            if removed_root:
                adjustments["removedConsumedRootApproach"] = True
        if decision.get("phase") == "TRIGGER":
            consumed = {"ROOT_APPROACH", "CHILD_TOUCH"}
            removed = [
                str(event.get("kind")) for event in events
                if str(event.get("kind")) in consumed
            ]
            events = [
                event for event in events
                if str(event.get("kind")) not in consumed
            ]
            if removed:
                adjustments["removedConsumedEvents"] = removed
        normalized_prices: list[dict[str, Any]] = []
        for event in events:
            kind = str(event.get("kind", ""))
            expected = None
            if kind == "ROOT_APPROACH" and isinstance(root, dict):
                expected = root.get("high" if direction_value == "LONG" else "low")
                event["sourceTf"] = root.get("tf")
                event["sourceTimeUtc"] = root.get("originTime")
            elif kind == "CHILD_TOUCH" and children:
                expected = children[-1].get("high" if direction_value == "LONG" else "low")
                event["sourceTf"] = children[-1].get("tf")
                event["sourceTimeUtc"] = children[-1].get("originTime")
            if expected is not None and float(event.get("price", math.nan)) != float(expected):
                normalized_prices.append({
                    "eventId": event.get("eventId"),
                    "kind": kind,
                    "modelPrice": event.get("price"),
                    "enginePrice": float(expected),
                })
                event["price"] = float(expected)

        objective = scenario.get("objective", {})
        required_events = {
            "SOURCE_INVALIDATION": {
                "eventId": "engine-source-invalidation",
                "kind": "SOURCE_INVALIDATION",
                "comparison": "CROSS_BELOW" if direction_value == "LONG" else "CROSS_ABOVE",
                "price": float(scenario.get("sourceInvalidation")),
                "sourceTf": root.get("tf"),
                "sourceTimeUtc": root.get("originTime"),
            },
            "OBJECTIVE_REACHED": {
                "eventId": "engine-objective-reached",
                "kind": "OBJECTIVE_REACHED",
                "comparison": "CROSS_ABOVE" if objective.get("side") == "BSL" else "CROSS_BELOW",
                "price": float(objective.get("price")),
                "sourceTf": objective.get("sourceTf"),
                "sourceTimeUtc": objective.get("sourceTime"),
            },
        }
        existing_kinds = {str(event.get("kind")) for event in events}
        if state == "PENDING":
            target_review = as_of + int(
                config.get("maximumPendingReviewMinutes", 60)
            ) * 60
            for event in events:
                event["validUntilUtc"] = utc_text(target_review)
            adjustments["reason"] = "PENDING_REAUTHORIZATION_WINDOW"
        else:
            scenario_limit = as_of + int(
                config.get("maximumScenarioReviewMinutes", 360)
            ) * 60
            # Prepared/armed scenarios are event-gated. Model-proposed short
            # expiries must not create hourly re-analysis loops.
            target_review = scenario_limit
        for event in events:
            event["validUntilUtc"] = utc_text(target_review)
        for kind, event in required_events.items():
            if kind not in existing_kinds:
                event["validUntilUtc"] = utc_text(target_review)
                events.append(event)
        old_review = str(decision.get("nextReviewAtUtc", ""))
        if parse_utc(old_review) <= as_of or parse_utc(old_review) < target_review:
            decision["nextReviewAtUtc"] = utc_text(target_review)
        decision["watchEvents"] = events
        if normalized_prices:
            adjustments["normalizedEventPrices"] = normalized_prices
        if old_review != decision.get("nextReviewAtUtc"):
            adjustments.update({
                "reason": adjustments.get("reason", "EVENT_GATED_SCENARIO_REVIEW"),
                "modelNextReviewAtUtc": old_review,
                "engineNextReviewAtUtc": decision.get("nextReviewAtUtc"),
            })
        added = [kind for kind in required_events if kind not in existing_kinds]
        if added:
            adjustments["addedSafetyEvents"] = added
    return adjustments or None


def append_hash_record(path: Path, payload: dict[str, Any], previous_hash: str) -> str:
    body = {"previousHash": previous_hash, **payload}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    current = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    body["recordHash"] = current
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(body, ensure_ascii=False, separators=(",", ":")) + "\n")
    return current


def verify_hash_chain(rows: list[dict[str, Any]], source_run: Path) -> None:
    expected_previous = "GENESIS"
    for index, row in enumerate(rows, start=1):
        if row.get("previousHash") != expected_previous:
            raise ValueError(f"broken ledger previousHash at row {index}: {source_run.name}")
        claimed = str(row.get("recordHash", ""))
        body = {key: value for key, value in row.items() if key != "recordHash"}
        canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        actual = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if claimed != actual:
            raise ValueError(f"broken ledger recordHash at row {index}: {source_run.name}")
        expected_previous = claimed


def watch_hit(
    event: dict[str, Any], row: np.void, point: float,
    previous_row: np.void | None = None,
) -> bool:
    price_value = float(event["price"])
    comparison = event["comparison"]
    if comparison == "TOUCH":
        current = float(row["low"]) - point <= price_value <= float(row["high"]) + point
        if previous_row is None:
            return current
        previous = (
            float(previous_row["low"]) - point
            <= price_value
            <= float(previous_row["high"]) + point
        )
        return current and not previous
    kind = str(event.get("kind", ""))
    if kind == "SOURCE_INVALIDATION":
        timeframe_seconds = {
            "M1": 60, "M5": 300, "M15": 900, "M30": 1800, "H1": 3600,
        }.get(str(event.get("sourceTf", "")))
        # A HTF OB is invalidated by a closed body on its own timeframe, not
        # by an intrabar M1 wick through the distal boundary.
        if timeframe_seconds is None or (int(row["time"]) + 60) % timeframe_seconds:
            return False
        close_value = float(row["close"])
        if comparison == "CROSS_ABOVE":
            return close_value > price_value + point
        return close_value < price_value - point
    if kind == "CHOCH_REFERENCE":
        current_value = float(row["close"])
        previous_value = float(previous_row["close"]) if previous_row is not None else math.nan
    elif comparison == "CROSS_ABOVE":
        current_value = float(row["high"])
        previous_value = float(previous_row["high"]) if previous_row is not None else math.nan
    else:
        current_value = float(row["low"])
        previous_value = float(previous_row["low"]) if previous_row is not None else math.nan
    if comparison == "CROSS_ABOVE":
        return current_value >= price_value and (
            previous_row is None or previous_value < price_value
        )
    return current_value <= price_value and (
        previous_row is None or previous_value > price_value
    )


def watch_active_at(event: dict[str, Any], available: int) -> bool:
    kind = str(event.get("kind", ""))
    if kind not in {"SWEEP_CANDIDATE", "CHOCH_REFERENCE"}:
        return True
    try:
        source_open = parse_utc(str(event["sourceTimeUtc"]))
    except (KeyError, TypeError, ValueError):
        return False
    # A just-closed M1 extreme is not mature liquidity. Require one complete
    # subsequent M1 reaction bar before it can trigger a later sweep/break.
    return available >= source_open + 180


def find_local_trigger_wakeup(
    rates: np.ndarray,
    start_cursor: int,
    end_cursor: int,
    direction: str,
    config: dict[str, Any],
    refined_touch_time: int | None = None,
    excluded_sweep_times: set[str] | None = None,
) -> tuple[int | None, dict[str, Any] | None]:
    """Find a new M1 sweep/body-break candidate without authorizing a trade."""
    if (
        not bool(config.get("localTriggerWakeupEnabled", True))
        or direction not in {"LONG", "SHORT"}
        or end_cursor <= start_cursor
    ):
        return None, None

    point = float(config.get("point", 0.0))
    lookback = max(12, int(config.get("localTriggerLookbackBars", 90)))
    reaction_bars = max(1, int(config.get("localTriggerMinimumReactionBars", 1)))
    scan_start = max(1, start_cursor - lookback)
    pivots: list[int] = []
    sweeps: list[dict[str, Any]] = []

    for index in range(scan_start + 1, end_cursor + 1):
        for candidate in sweeps:
            if candidate.get("recoveryIndex") is not None:
                continue
            liquidity_price = float(candidate["liquidityPrice"])
            recovered = (
                float(rates[index]["close"]) > liquidity_price
                if direction == "LONG"
                else float(rates[index]["close"]) < liquidity_price
            )
            if recovered and index >= int(candidate["sweepIndex"]):
                candidate["recoveryIndex"] = index
        if index > start_cursor:
            completed = []
            for candidate in sweeps:
                recovery_index = candidate.get("recoveryIndex")
                if recovery_index is None:
                    continue
                reference_index = candidate.get("referenceIndex")
                if reference_index is None:
                    post_sweep_references: list[int] = []
                    for candidate_index in range(
                        max(int(candidate["sweepIndex"]) + 1, int(recovery_index)),
                        index,
                    ):
                        if candidate_index <= 0 or candidate_index + 1 >= len(rates):
                            continue
                        if direction == "SHORT":
                            is_reference = (
                                float(rates[candidate_index]["low"])
                                < float(rates[candidate_index - 1]["low"])
                                and float(rates[candidate_index]["low"])
                                <= float(rates[candidate_index + 1]["low"])
                            )
                        else:
                            is_reference = (
                                float(rates[candidate_index]["high"])
                                > float(rates[candidate_index - 1]["high"])
                                and float(rates[candidate_index]["high"])
                                >= float(rates[candidate_index + 1]["high"])
                            )
                        if is_reference:
                            post_sweep_references.append(candidate_index)
                    if post_sweep_references:
                        reference_index = (
                            min(
                                post_sweep_references,
                                key=lambda item: float(rates[item]["low"]),
                            )
                            if direction == "SHORT"
                            else max(
                                post_sweep_references,
                                key=lambda item: float(rates[item]["high"]),
                            )
                        )
                        candidate["referenceIndex"] = reference_index
                        candidate["referencePrice"] = float(
                            rates[reference_index][
                                "low" if direction == "SHORT" else "high"
                            ]
                        )
                if reference_index is None:
                    continue
                sweep_time_text = utc_text(
                    int(rates[int(candidate["sweepIndex"])]["time"])
                )
                reference_time_text = utc_text(
                    int(rates[int(reference_index)]["time"])
                )
                chain_key = f"{sweep_time_text}|{reference_time_text}"
                full_chain_key = (
                    f"{utc_text(int(rates[int(candidate['sourceIndex'])]['time']))}|"
                    f"{chain_key}"
                )
                if (
                    full_chain_key in (excluded_sweep_times or set())
                    or chain_key in (excluded_sweep_times or set())
                    or sweep_time_text in (excluded_sweep_times or set())
                ):
                    continue
                later_excursion = rates[int(candidate["sweepIndex"]) + 1:index + 1]
                superseded = (
                    any(
                        float(row["high"]) > float(candidate["sweepExtreme"]) + point / 2
                        for row in later_excursion
                    )
                    if direction == "SHORT"
                    else any(
                        float(row["low"]) < float(candidate["sweepExtreme"]) - point / 2
                        for row in later_excursion
                    )
                )
                if superseded:
                    continue
                reference_price = float(candidate["referencePrice"])
                close = float(rates[index]["close"])
                previous_close = float(rates[index - 1]["close"])
                broke = (
                    close > reference_price + point / 2
                    and previous_close <= reference_price + point / 2
                    if direction == "LONG"
                    else close < reference_price - point / 2
                    and previous_close >= reference_price - point / 2
                )
                if broke and index > int(recovery_index):
                    completed.append(candidate)
            if completed:
                # A final sweep consumes the nearest pre-existing mature pool
                # on its path. Lower pools pierced by the same excursion are
                # context, not alternative sweep sources. Keep one source per
                # sweep/reference chain and its first valid recovery.
                by_chain: dict[tuple[int, int], dict[str, Any]] = {}
                for item in completed:
                    key = (int(item["sweepIndex"]), int(item["referenceIndex"]))
                    existing = by_chain.get(key)
                    if existing is None:
                        by_chain[key] = item
                        continue
                    nearer = (
                        float(item["liquidityPrice"]) > float(existing["liquidityPrice"])
                        if direction == "SHORT"
                        else float(item["liquidityPrice"]) < float(existing["liquidityPrice"])
                    )
                    if nearer:
                        by_chain[key] = item
                ordered = sorted(
                    by_chain.values(),
                    key=lambda item: (
                        -float(item["sweepExtreme"])
                        if direction == "SHORT"
                        else float(item["sweepExtreme"]),
                        -int(item["sweepIndex"]),
                        int(item["referenceIndex"]),
                    ),
                )[:6]
                candidates = []
                for item in ordered:
                    source_index = int(item["sourceIndex"])
                    sweep_index = int(item["sweepIndex"])
                    reference_index = int(item["referenceIndex"])
                    recovery_index = int(item["recoveryIndex"])
                    opposite_indices = [
                        candidate_index
                        for candidate_index in range(sweep_index, index + 1)
                        if (
                            direction == "LONG"
                            and float(rates[candidate_index]["close"])
                            < float(rates[candidate_index]["open"])
                        ) or (
                            direction == "SHORT"
                            and float(rates[candidate_index]["close"])
                            > float(rates[candidate_index]["open"])
                        )
                    ]
                    if not opposite_indices:
                        continue
                    execution_index = opposite_indices[-1]
                    source_time = utc_text(int(rates[source_index]["time"]))
                    sweep_time = utc_text(int(rates[sweep_index]["time"]))
                    reference_time = utc_text(int(rates[reference_index]["time"]))
                    candidates.append({
                        "liquiditySourceTimeUtc": source_time,
                        "liquidityPrice": float(item["liquidityPrice"]),
                        "sweepTimeUtc": sweep_time,
                        "sweepExtreme": float(item["sweepExtreme"]),
                        "sweepRecoveryTimeUtc": utc_text(int(rates[recovery_index]["time"])),
                        "chochReferenceTimeUtc": reference_time,
                        "chochReferencePrice": float(item["referencePrice"]),
                        "candidateKey": f"{sweep_time}|{reference_time}",
                        "protectedSwingBarId": f"M1:{int(rates[sweep_index]['time'])}",
                        "matureLiquidityBarId": f"M1:{int(rates[source_index]['time'])}",
                        "sweepBarId": f"M1:{int(rates[sweep_index]['time'])}",
                        "sweepRecoveryBarId": f"M1:{int(rates[recovery_index]['time'])}",
                        "chochReferenceBarId": f"M1:{int(rates[reference_index]['time'])}",
                        "chochBreakBarId": f"M1:{int(rates[index]['time'])}",
                        "executionBarId": f"M1:{int(rates[execution_index]['time'])}",
                    })
                if not candidates:
                    continue
                context = {
                    "kind": "LOCAL_TRIGGER_PATTERN_CANDIDATE",
                    "screeningOnly": True,
                    "direction": direction,
                    "detectedAtUtc": utc_text(int(rates[index]["time"]) + 60),
                    "bodyBreakTimeUtc": utc_text(int(rates[index]["time"])),
                    "bodyBreakClose": float(rates[index]["close"]),
                    "candidates": candidates,
                }
                return index, context

        pivot_index = index - reaction_bars
        if pivot_index > scan_start:
            previous_index = pivot_index - 1
            reaction_slice = rates[pivot_index + 1:index + 1]
            if direction == "SHORT":
                is_pivot = (
                    float(rates[pivot_index]["high"]) > float(rates[previous_index]["high"])
                    and all(
                        float(row["high"]) < float(rates[pivot_index]["high"])
                        for row in reaction_slice
                    )
                )
            else:
                is_pivot = (
                    float(rates[pivot_index]["low"]) < float(rates[previous_index]["low"])
                    and all(
                        float(row["low"]) > float(rates[pivot_index]["low"])
                        for row in reaction_slice
                    )
                )
            if is_pivot:
                pivots.append(pivot_index)

        pivots = [item for item in pivots if item >= index - lookback]
        for source_index in reversed(pivots):
            if refined_touch_time is not None and (
                int(rates[source_index]["time"]) >= refined_touch_time
                or int(rates[index]["time"]) <= refined_touch_time
            ):
                continue
            if index - source_index < reaction_bars + 1:
                continue
            between = rates[source_index + 1:index]
            if not len(between):
                continue
            if direction == "SHORT":
                liquidity_price = float(rates[source_index]["high"])
                swept = (
                    float(rates[index]["high"]) > liquidity_price + point / 2
                )
                sweep_extreme = float(rates[index]["high"])
            else:
                liquidity_price = float(rates[source_index]["low"])
                swept = (
                    float(rates[index]["low"]) < liquidity_price - point / 2
                )
                sweep_extreme = float(rates[index]["low"])
            if not swept:
                continue
            reference_indices: list[int] = []
            for candidate_index in range(index - 1, source_index + 1, -1):
                if refined_touch_time is not None and int(
                    rates[candidate_index]["time"]
                ) <= refined_touch_time:
                    continue
                # A one- or two-candle micro pivot immediately before the
                # sweep is not the live swing governing the M1 correction.
                if index - candidate_index < 3:
                    continue
                if direction == "SHORT":
                    is_reference = (
                        float(rates[candidate_index]["low"])
                        < float(rates[candidate_index - 1]["low"])
                        and float(rates[candidate_index]["low"])
                        <= float(rates[candidate_index + 1]["low"])
                    )
                else:
                    is_reference = (
                        float(rates[candidate_index]["high"])
                        > float(rates[candidate_index - 1]["high"])
                        and float(rates[candidate_index]["high"])
                        >= float(rates[candidate_index + 1]["high"])
                    )
                if is_reference:
                    reference_indices.append(candidate_index)
            if reference_indices:
                # CHoCH must break the swing that governed the post-touch
                # correction, not whichever recent micro pivot breaks first.
                reference_indices = [
                    min(reference_indices, key=lambda item: float(rates[item]["low"]))
                    if direction == "SHORT"
                    else max(reference_indices, key=lambda item: float(rates[item]["high"]))
                ]
            if not reference_indices:
                reference_indices = [None]
            for reference_index in reference_indices:
                reference_price = (
                    float(
                        rates[reference_index]["low"]
                        if direction == "SHORT"
                        else rates[reference_index]["high"]
                    )
                    if reference_index is not None else None
                )
                sweeps.append({
                    "sourceIndex": source_index,
                    "sweepIndex": index,
                    "referenceIndex": reference_index,
                    "liquidityPrice": liquidity_price,
                    "sweepExtreme": sweep_extreme,
                    "referencePrice": reference_price,
                    "recoveryIndex": (
                        index
                        if (
                            (direction == "LONG" and float(rates[index]["close"]) > liquidity_price)
                            or (direction == "SHORT" and float(rates[index]["close"]) < liquidity_price)
                        )
                        else None
                    ),
                })
    return None, None


def find_local_map_wakeup(
    rates: np.ndarray,
    start_cursor: int,
    end_cursor: int,
    config: dict[str, Any],
    excluded_root_ids: set[str] | None = None,
    strict_only: bool = False,
) -> tuple[int | None, dict[str, Any] | None]:
    """Wake MAP only after a closed M15/M30 root-to-displacement pair exists."""
    if (
        not bool(config.get("localMapWakeupEnabled", True))
        or end_cursor <= start_cursor
    ):
        return None, None

    body_percentile = float(config.get("localMapBodyPercentile", 75.0))
    history_bars = max(12, int(config.get("localMapBodyHistoryBars", 30)))

    for index in range(start_cursor + 1, end_cursor + 1):
        available = int(rates[index]["time"]) + 60
        source_candidate = (
            None
            if strict_only
            else root_child_delivery_candidate_at(rates, index, config)
        )
        if (
            source_candidate is not None
            and str(source_candidate.get("candidateRootBarId"))
            not in (excluded_root_ids or set())
        ):
            return index, source_candidate
        delivery_candidate = (
            None if strict_only else flat_delivery_candidate_at(rates, index, config)
        )
        if (
            delivery_candidate is not None
            and str(delivery_candidate.get("candidateRootBarId"))
            not in (excluded_root_ids or set())
        ):
            return index, delivery_candidate
        for timeframe, seconds in (("M30", 1800), ("M15", 900)):
            if available % seconds:
                continue
            delivery_open = available - seconds
            root_open = delivery_open - seconds
            root_id = f"{timeframe}:{root_open}"
            if root_id in (excluded_root_ids or set()):
                continue
            root_rows = rates[
                (rates["time"] >= root_open)
                & (rates["time"] < delivery_open)
            ]
            delivery_rows = rates[
                (rates["time"] >= delivery_open)
                & (rates["time"] < available)
            ]
            expected_rows = seconds // 60
            if len(root_rows) != expected_rows or len(delivery_rows) != expected_rows:
                continue
            root_o, root_c = float(root_rows[0]["open"]), float(root_rows[-1]["close"])
            root_h, root_l = float(np.max(root_rows["high"])), float(np.min(root_rows["low"]))
            delivery_o = float(delivery_rows[0]["open"])
            delivery_c = float(delivery_rows[-1]["close"])
            if root_c > root_o and delivery_c < root_l:
                direction = "SHORT"
            elif root_c < root_o and delivery_c > root_h:
                direction = "LONG"
            else:
                continue
            history_start = root_open - history_bars * seconds
            history_rows = rates[
                (rates["time"] >= history_start)
                & (rates["time"] < root_open)
            ]
            bodies = []
            for bucket_open in range(history_start, root_open, seconds):
                bucket = history_rows[
                    (history_rows["time"] >= bucket_open)
                    & (history_rows["time"] < bucket_open + seconds)
                ]
                if len(bucket) == expected_rows:
                    bodies.append(abs(float(bucket[-1]["close"]) - float(bucket[0]["open"])))
            delivery_body = abs(delivery_c - delivery_o)
            body_threshold = (
                float(np.percentile(bodies, body_percentile))
                if bodies else 0.0
            )
            if delivery_body < body_threshold:
                continue
            return index, {
                "kind": "LOCAL_MAP_ACTIVITY_CANDIDATE",
                "screeningOnly": True,
                "detectedAtUtc": utc_text(available),
                "directionHint": direction,
                "candidateRootBarId": root_id,
                "deliveryBarId": f"{timeframe}:{delivery_open}",
                "body": delivery_body,
                "rollingBodyPercentile": body_threshold,
                "warning": "Timing alarm only; AI must independently prove map, root and objective.",
            }
    return None, None


def root_child_delivery_candidate_at(
    rates: np.ndarray, index: int, config: dict[str, Any]
) -> dict[str, Any] | None:
    """Wake MAP when a closed M15 root/M5 child starts delivering on M1.

    This deliberately performs only chronology and physical-containment checks.
    Swing ownership, objective quality, PD location and causal meaning remain
    provider decisions; putting those filters in the router previously hid
    valid analyst-visible sources before their execution FVG appeared.
    """
    if not bool(config.get("localRootChildWakeupEnabled", False)) or index < 32:
        return None
    row = rates[index]
    available = int(row["time"]) + 60
    body = abs(float(row["close"]) - float(row["open"]))
    history = rates[index - 30:index]
    threshold = float(np.percentile(
        np.abs(history["close"].astype(float) - history["open"].astype(float)),
        float(config.get("localRootChildBodyPercentile", 70.0)),
    ))
    if body < threshold:
        return None
    direction = (
        "LONG" if float(row["close"]) > float(row["open"])
        else "SHORT" if float(row["close"]) < float(row["open"])
        else ""
    )
    if not direction:
        return None
    previous = rates[index - 1]
    previous_body = abs(float(previous["close"]) - float(previous["open"]))
    previous_direction = (
        "LONG" if float(previous["close"]) > float(previous["open"])
        else "SHORT" if float(previous["close"]) < float(previous["open"])
        else ""
    )
    # Wake once per contiguous physical impulse. Otherwise consecutive M1
    # bodies in one displacement surface progressively older overlapping roots.
    if previous_direction == direction and previous_body >= threshold:
        return None

    current_m15_open = (available // 900) * 900
    current_m5_open = (available // 300) * 300
    lookback = max(2, int(config.get("localFlatDeliveryRootLookbackBars", 8)))
    for offset in range(1, lookback + 1):
        root_open = current_m15_open - offset * 900
        root = _closed_ohlc_bucket(rates, root_open, 900)
        if root is None:
            continue
        root_opposite = (
            direction == "LONG" and root["close"] < root["open"]
        ) or (
            direction == "SHORT" and root["close"] > root["open"]
        )
        if not root_opposite:
            continue
        selected_child_open: int | None = None
        for child_open in range(root_open, current_m5_open, 300):
            child = _closed_ohlc_bucket(rates, child_open, 300)
            if child is None:
                continue
            child_opposite = (
                direction == "LONG" and child["close"] < child["open"]
            ) or (
                direction == "SHORT" and child["close"] > child["open"]
            )
            child_contained = (
                child["low"] >= root["low"] - 0.011
                and child["high"] <= root["high"] + 0.011
            )
            delivered = (
                direction == "LONG" and float(row["close"]) > child["high"]
            ) or (
                direction == "SHORT" and float(row["close"]) < child["low"]
            )
            if not (child_opposite and child_contained and delivered):
                continue
            selected_child_open = child_open
        if selected_child_open is not None:
            return {
                "kind": "LOCAL_ROOT_CHILD_DELIVERY_CANDIDATE",
                "screeningOnly": True,
                "detectedAtUtc": utc_text(available),
                "directionHint": direction,
                "candidateRootBarId": f"M15:{root_open}",
                "candidateChildBarId": f"M5:{selected_child_open}",
                "deliveryBarId": f"M1:{int(row['time'])}",
                "body": body,
                "rollingBodyPercentile": threshold,
                "warning": (
                    "Timing alarm only. Provider must independently prove map, "
                    "objective, root ownership and causal refinement."
                ),
            }
    return None


def _closed_ohlc_bucket(
    rates: np.ndarray, bucket_open: int, seconds: int
) -> dict[str, float] | None:
    times = rates["time"]
    start = int(np.searchsorted(times, bucket_open, side="left"))
    end = int(np.searchsorted(times, bucket_open + seconds, side="left"))
    rows = rates[start:end]
    if len(rows) != seconds // 60:
        return None
    return {
        "open": float(rows[0]["open"]),
        "high": float(np.max(rows["high"])),
        "low": float(np.min(rows["low"])),
        "close": float(rows[-1]["close"]),
    }


def flat_delivery_candidate_at(
    rates: np.ndarray, right_index: int, config: dict[str, Any]
) -> dict[str, Any] | None:
    """Surface a fresh M1 delivery episode while FLAT; never authorize a trade."""
    if (
        not bool(config.get("localFlatDeliveryWakeupEnabled", True))
        or right_index < 32
    ):
        return None
    left, middle, right = rates[right_index - 2:right_index + 1]
    middle_body = abs(float(middle["close"]) - float(middle["open"]))
    history = rates[right_index - 31:right_index - 1]
    history_bodies = np.abs(
        history["close"].astype(float) - history["open"].astype(float)
    )
    threshold = float(np.percentile(
        history_bodies,
        float(config.get("localFlatDeliveryBodyPercentile", 80.0)),
    ))
    bullish = (
        float(left["high"]) < float(right["low"])
        and float(middle["close"]) > float(middle["open"])
        and middle_body >= threshold
    )
    bearish = (
        float(left["low"]) > float(right["high"])
        and float(middle["close"]) < float(middle["open"])
        and middle_body >= threshold
    )
    if not (bullish or bearish):
        return None
    direction = "LONG" if bullish else "SHORT"
    available = int(right["time"]) + 60
    map_start = int(np.searchsorted(rates["time"], available - 24 * 3600, side="left"))
    map_end = int(np.searchsorted(rates["time"], available, side="left"))
    map_rows = rates[map_start:map_end]
    if len(map_rows) < 12 * 60:
        return None
    broad_map_low = float(np.min(map_rows["low"]))
    broad_map_high = float(np.max(map_rows["high"]))
    broad_eq = (broad_map_low + broad_map_high) / 2.0
    m15_open = (available // 900) * 900
    root: tuple[int, dict[str, float]] | None = None
    child: tuple[int, dict[str, float]] | None = None
    m5_open = (available // 300) * 300
    for offset in range(1, max(2, int(config.get("localFlatDeliveryRootLookbackBars", 8))) + 1):
        root_origin = m15_open - offset * 900
        root_candidate = _closed_ohlc_bucket(rates, root_origin, 900)
        if root_candidate is None:
            continue
        opposite = (
            direction == "LONG" and root_candidate["close"] < root_candidate["open"]
        ) or (
            direction == "SHORT" and root_candidate["close"] > root_candidate["open"]
        )
        if not opposite:
            continue
        previous_root = _closed_ohlc_bucket(rates, root_origin - 900, 900)
        local_extreme = bool(
            previous_root is not None
            and (
                (
                    direction == "LONG"
                    and root_candidate["low"] <= previous_root["low"]
                )
                or (
                    direction == "SHORT"
                    and root_candidate["high"] >= previous_root["high"]
                )
            )
        )
        parent_aligned = False
        for parent_seconds in (1800, 3600):
            parent_origin = (root_origin // parent_seconds) * parent_seconds
            if parent_origin + parent_seconds > available:
                continue
            parent = _closed_ohlc_bucket(rates, parent_origin, parent_seconds)
            if parent is None:
                continue
            parent_aligned = parent_aligned or (
                (direction == "LONG" and parent["close"] < parent["open"])
                or (direction == "SHORT" and parent["close"] > parent["open"])
            )
        if not (local_extreme or parent_aligned):
            continue
        root_midpoint = (root_candidate["low"] + root_candidate["high"]) / 2.0
        correct_pd_half = (
            direction == "LONG" and root_midpoint <= broad_eq
        ) or (
            direction == "SHORT" and root_midpoint >= broad_eq
        )
        if not correct_pd_half:
            continue
        candidate_child: tuple[int, dict[str, float]] | None = None
        for child_origin in range(root_origin, m5_open, 300):
            child_row = _closed_ohlc_bucket(rates, child_origin, 300)
            if child_row is None:
                continue
            child_opposite = (
                direction == "LONG" and child_row["close"] < child_row["open"]
            ) or (
                direction == "SHORT" and child_row["close"] > child_row["open"]
            )
            overlaps_root = (
                child_row["low"] <= root_candidate["high"]
                and child_row["high"] >= root_candidate["low"]
            )
            delivered = (
                direction == "LONG" and float(right["close"]) > child_row["high"]
            ) or (
                direction == "SHORT" and float(right["close"]) < child_row["low"]
            )
            if child_opposite and overlaps_root and delivered:
                candidate_child = (child_origin, child_row)
        if candidate_child is not None:
            root = (root_origin, root_candidate)
            child = candidate_child
            break
    if root is None or child is None:
        return None
    root_open, root_row = root
    root_delivered = (
        direction == "LONG" and float(right["close"]) > root_row["high"]
    ) or (
        direction == "SHORT" and float(right["close"]) < root_row["low"]
    )
    if not root_delivered:
        return None
    return {
        "kind": "LOCAL_FLAT_DELIVERY_CANDIDATE",
        "screeningOnly": True,
        "detectedAtUtc": utc_text(available),
        "directionHint": direction,
        "candidateRootBarId": f"M15:{root_open}",
        "candidateChildBarId": f"M5:{child[0]}",
        "fvgLeftBarId": f"M1:{int(left['time'])}",
        "fvgMiddleBarId": f"M1:{int(middle['time'])}",
        "fvgRightBarId": f"M1:{int(right['time'])}",
        "middleBody": middle_body,
        "rollingBodyThreshold": threshold,
        "warning": (
            "Timing alarm only. MAP must independently prove owner, objective, "
            "root and causal child before any delivery replacement."
        ),
    }


def map_root_exclusions(decision: dict[str, Any]) -> set[str]:
    excluded = set(decision.get("_consumedMapWakeRoots") or [])
    scenario = decision.get("scenario")
    if isinstance(scenario, dict):
        candidate = scenario.get("mapCandidate")
        if isinstance(candidate, dict) and candidate.get("rootBarId"):
            excluded.add(str(candidate["rootBarId"]))
    return excluded


def next_decision_index(rates: np.ndarray, cursor: int, decision: dict[str, Any], config: dict[str, Any]) -> tuple[int | None, str]:
    next_review = parse_utc(str(decision["nextReviewAtUtc"]))
    point = float(config["point"])
    events = decision.get("watchEvents", [])
    local_wakeup_index = None
    local_map_wakeup_index = None
    state = str(decision.get("state", ""))
    if (
        state in {"ARMED", "TRIGGERED"}
        and isinstance(decision.get("scenario"), dict)
    ):
        review_positions = np.flatnonzero(rates["time"] + 60 >= next_review)
        scan_end = (
            min(len(rates) - 1, int(review_positions[0]))
            if len(review_positions) else len(rates) - 1
        )
        local_wakeup_index, _ = find_local_trigger_wakeup(
            rates,
            cursor,
            scan_end,
            str(decision["scenario"].get("direction", "")),
            config,
            parse_utc(str(decision["scenario"].get("refinedTouchTimeUtc")))
            if decision["scenario"].get("refinedTouchTimeUtc") else None,
            set(decision.get("_consumedTriggerSweepTimes") or []),
        )
    if state in {"FLAT", "WATCHING_MAP", "PREPARED", "ARMED", "TRIGGERED"}:
        review_positions = np.flatnonzero(rates["time"] + 60 >= next_review)
        scan_end = (
            min(len(rates) - 1, int(review_positions[0]))
            if len(review_positions) else len(rates) - 1
        )
        local_map_wakeup_index, _ = find_local_map_wakeup(
            rates, cursor, scan_end, config,
            excluded_root_ids=map_root_exclusions(decision),
            strict_only=state in {"PREPARED", "ARMED", "TRIGGERED"},
        )
    for index in range(cursor + 1, len(rates)):
        available = int(rates[index]["time"]) + 60
        if local_map_wakeup_index is not None and index == local_map_wakeup_index:
            return index, "LOCAL_MAP_ACTIVITY"
        if local_wakeup_index is not None and index == local_wakeup_index:
            return index, "LOCAL_TRIGGER_PATTERN"
        hits = []
        for event in events:
            if (
                available <= parse_utc(str(event["validUntilUtc"]))
                and watch_active_at(event, available)
                and watch_hit(
                    event, rates[index], point,
                    rates[index - 1] if index > 0 else None,
                )
            ):
                hits.append(str(event["kind"]))
        if hits:
            priority = {
                "SOURCE_INVALIDATION": 0, "OBJECTIVE_REACHED": 1,
                "ORDER_CANCEL_LEVEL": 2, "ROOT_APPROACH": 3,
                "CHILD_TOUCH": 4, "SWEEP_CANDIDATE": 5, "CHOCH_REFERENCE": 6,
            }
            return index, min(hits, key=lambda item: priority.get(item, 99))
        if available >= next_review:
            return index, "SCHEDULED_REVIEW"
    return None, "END_OF_DATA"


def phase_for(state: str, event_kind: str) -> str:
    if state == "PENDING":
        return "PENDING_REVIEW"
    if event_kind in {
        "LOCAL_MAP_ACTIVITY", "SOURCE_INVALIDATION", "OBJECTIVE_REACHED",
    }:
        return "MAP"
    if state == "WATCHING_MAP":
        return "MAP"
    if event_kind == "ROOT_APPROACH":
        return "REFINEMENT"
    if state == "PREPARED" and event_kind == "CHILD_TOUCH":
        return "REFINEMENT"
    if state in {"ARMED", "TRIGGERED"} or event_kind in {
        "CHILD_TOUCH", "SWEEP_CANDIDATE", "CHOCH_REFERENCE",
        "LOCAL_TRIGGER_PATTERN",
    }:
        return "TRIGGER"
    return "MAP"


def locally_arm_child_touch(
    previous: dict[str, Any],
    m1_bar: np.void,
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convert an engine-observed child retest into ARMED without an AI call."""
    scenario = copy.deepcopy(previous.get("scenario"))
    if previous.get("state") != "PREPARED" or not isinstance(scenario, dict):
        raise ValueError("local child touch requires a PREPARED scenario")
    children = list(scenario.get("refinementPath") or [])
    if not children:
        raise ValueError("local child touch requires a frozen causal child")
    child = children[-1]
    bar_open = int(m1_bar["time"])
    as_of = bar_open + 60
    frozen_at = parse_utc(str(scenario.get("frozenAtUtc", "")))
    child_seconds = {"M30": 1800, "M15": 900, "M5": 300}[str(child["tf"])]
    child_available = parse_utc(str(child["originTime"])) + child_seconds
    if bar_open < max(frozen_at, child_available):
        raise ValueError("local child touch predates frozen scenario or child availability")
    if not (
        float(m1_bar["low"]) <= float(child["high"])
        and float(m1_bar["high"]) >= float(child["low"])
    ):
        raise ValueError("local child touch bar does not overlap frozen child")
    touch_id = f"M1:{bar_open}"
    scenario["refinedTouchBarId"] = touch_id
    scenario["refinedTouchTimeUtc"] = utc_text(bar_open)
    decision = {
        "schemaVersion": "1.5.0",
        "asOfUtc": utc_text(as_of),
        "phase": "REFINEMENT",
        "action": "ARM",
        "state": "ARMED",
        "scenario": scenario,
        "candleQueries": [],
        "watchEvents": [
            copy.deepcopy(event)
            for event in previous.get("watchEvents", [])
            if str(event.get("kind")) not in {"ROOT_APPROACH", "CHILD_TOUCH"}
        ],
        "nextReviewAtUtc": utc_text(
            as_of + int(config.get("maximumScenarioReviewMinutes", 360)) * 60
        ),
        "order": None,
        "rejectionReasons": [],
        "reason": "The local engine observed the first post-freeze retest of the frozen causal child.",
    }
    spread_field = (
        "spread_points"
        if "spread_points" in (m1_bar.dtype.names or ())
        else "spread"
    )
    evidence = {
        "queryId": "local-child-touch",
        "tf": "M1",
        "requestedAroundTimeUtc": utc_text(bar_open),
        "purpose": "CHILD_TOUCH",
        "candles": [{
            "openTimeUtc": utc_text(bar_open),
            "availableTimeUtc": utc_text(as_of),
            "open": float(m1_bar["open"]),
            "high": float(m1_bar["high"]),
            "low": float(m1_bar["low"]),
            "close": float(m1_bar["close"]),
            "spreadPrice": float(m1_bar[spread_field]) * float(config["point"]),
            "barId": touch_id,
        }],
    }
    return decision, evidence


def immediate_phase_transition(
    phase: str, decision: dict[str, Any]
) -> str | None:
    if (
        phase == "MAP"
        and decision.get("action") == "PREPARE"
        and decision.get("state") == "PREPARED"
        and isinstance(decision.get("scenario"), dict)
    ):
        return "REFINEMENT"
    if (
        phase == "REFINEMENT"
        and decision.get("action") == "WAIT"
        and decision.get("state") == "PREPARED"
        and isinstance(decision.get("order"), dict)
        and decision["order"].get("executionModel") == "HTF_OB_REACTION_INTENT"
    ):
        return "PENDING_REVIEW"
    return None


def validate_initial_causal_intent(
    decision: dict[str, Any],
    config: dict[str, Any],
    as_of: int,
) -> list[str]:
    """Validate the locally held OB intent before it can wait for delivery."""
    errors: list[str] = []
    scenario = decision.get("scenario")
    order = decision.get("order")
    if not isinstance(scenario, dict) or not isinstance(order, dict):
        return ["initial causal intent requires scenario and order"]
    if not (
        decision.get("phase") == "REFINEMENT"
        and decision.get("action") == "WAIT"
        and decision.get("state") == "PREPARED"
        and order.get("executionModel") == "HTF_OB_REACTION_INTENT"
        and order.get("intentOnly") is True
    ):
        return ["initial causal intent must be REFINEMENT/WAIT/PREPARED"]

    required = (
        "entry", "stopLoss", "takeProfit", "rootOriginTime",
        "childOriginTime", "objectiveSourceTime", "actualSpread",
        "brokerStopsLevelPrice", "slBuffer", "lastReauthorizedAtUtc",
    )
    missing = [field for field in required if field not in order]
    if missing:
        return ["initial causal intent is incomplete: " + ",".join(missing)]

    root = scenario.get("rootOb") or {}
    children = scenario.get("refinementPath") or []
    objective = scenario.get("objective") or {}
    if not children:
        errors.append("initial causal intent has no causal child")
        return errors
    child = children[-1]
    if order.get("rootOriginTime") != root.get("originTime"):
        errors.append("intent rootOriginTime differs from scenario root")
    if order.get("childOriginTime") != child.get("originTime"):
        errors.append("intent childOriginTime differs from final refinement")
    if order.get("objectiveSourceTime") != objective.get("sourceTime"):
        errors.append("intent objectiveSourceTime differs from scenario objective")
    try:
        if parse_utc(str(order["lastReauthorizedAtUtc"])) != as_of:
            errors.append("intent lastReauthorizedAtUtc must equal current as-of")
    except (TypeError, ValueError):
        errors.append("invalid intent lastReauthorizedAtUtc")

    point = float(config["point"])
    entry = float(order["entry"])
    stop = float(order["stopLoss"])
    take_profit = float(order["takeProfit"])
    actual_spread = float(order["actualSpread"])
    broker_stops = float(order["brokerStopsLevelPrice"])
    sl_buffer = float(order["slBuffer"])
    required_buffer = max(point, actual_spread, broker_stops)
    if sl_buffer + point < required_buffer:
        errors.append("intent SL buffer is below spread/stops/tick hard minimum")
    if abs(take_profit - float(objective.get("price", math.nan))) > point:
        errors.append("intent TP differs from frozen objective liquidity")

    child_low = float(child.get("low", math.nan))
    child_high = float(child.get("high", math.nan))
    direction_value = scenario.get("direction")
    if direction_value == "LONG":
        if not (stop < entry < take_profit):
            errors.append("invalid LONG intent price geometry")
        if abs(entry - child_high) > point:
            errors.append("LONG intent entry must use child proximal high")
        if stop > child_low - sl_buffer + point:
            errors.append("LONG intent SL is not beyond child invalidation")
    elif direction_value == "SHORT":
        if not (take_profit < entry < stop):
            errors.append("invalid SHORT intent price geometry")
        if abs(entry - child_low) > point:
            errors.append("SHORT intent entry must use child proximal low")
        if stop < child_high + sl_buffer - point:
            errors.append("SHORT intent SL is not beyond child invalidation")
    else:
        errors.append("initial causal intent has invalid direction")
    return errors


def carry_previous_across_query(
    previous: dict[str, Any] | None,
    query_decision: dict[str, Any],
) -> dict[str, Any] | None:
    if query_decision.get("action") != "QUERY_CANDLES":
        raise ValueError("carry_previous_across_query requires QUERY_CANDLES")
    return previous


def is_local_delivery_fvg(
    rates: np.ndarray,
    right_index: int,
    direction: str,
) -> bool:
    """Wake only when a fresh gap also body-breaks the latest confirmed swing."""
    if right_index < 2 or direction not in {"LONG", "SHORT"}:
        return False
    left, middle, right = rates[right_index - 2:right_index + 1]
    bullish_gap = (
        direction == "LONG"
        and float(left["high"]) < float(right["low"])
        and float(middle["close"]) > float(middle["open"])
    )
    bearish_gap = (
        direction == "SHORT"
        and float(left["low"]) > float(right["high"])
        and float(middle["close"]) < float(middle["open"])
    )
    if not (bullish_gap or bearish_gap):
        return False
    middle_index = right_index - 1
    for pivot_index in range(middle_index - 1, 0, -1):
        pivot = rates[pivot_index]
        previous_bar = rates[pivot_index - 1]
        next_bar = rates[pivot_index + 1]
        is_pivot = (
            float(pivot["high"]) > float(previous_bar["high"])
            and float(pivot["high"]) >= float(next_bar["high"])
            if direction == "LONG"
            else float(pivot["low"]) < float(previous_bar["low"])
            and float(pivot["low"]) <= float(next_bar["low"])
        )
        if not is_pivot:
            continue
        body_break = (
            float(middle["close"]) > float(pivot["high"])
            if direction == "LONG"
            else float(middle["close"]) < float(pivot["low"])
        )
        causal_exists = any(
            (
                float(row["close"]) < float(row["open"])
                if direction == "LONG"
                else float(row["close"]) > float(row["open"])
            )
            for row in rates[pivot_index:middle_index + 1]
        )
        return body_break and causal_exists
    return False


def local_delivery_fvg_candidate_from_compact(
    compact: dict[str, list[dict[str, Any]]],
    as_of: str,
    direction: str,
) -> dict[str, Any] | None:
    rows = compact.get("M1", [])
    if len(rows) < 3:
        return None
    left, middle, right = rows[-3:]
    if parse_utc(str(right["time"])) + 60 != parse_utc(as_of):
        return None
    bullish = (
        direction == "LONG"
        and float(left["h"]) < float(right["l"])
        and float(middle["c"]) > float(middle["o"])
    )
    bearish = (
        direction == "SHORT"
        and float(left["l"]) > float(right["h"])
        and float(middle["c"]) < float(middle["o"])
    )
    if not (bullish or bearish):
        return None
    middle_index = len(rows) - 2
    protected: dict[str, Any] | None = None
    causal_ob: dict[str, Any] | None = None
    for pivot_index in range(middle_index - 1, 0, -1):
        pivot = rows[pivot_index]
        previous_bar = rows[pivot_index - 1]
        next_bar = rows[pivot_index + 1]
        is_pivot = (
            float(pivot["h"]) > float(previous_bar["h"])
            and float(pivot["h"]) >= float(next_bar["h"])
            if direction == "LONG"
            else float(pivot["l"]) < float(previous_bar["l"])
            and float(pivot["l"]) <= float(next_bar["l"])
        )
        if not is_pivot:
            continue
        body_break = (
            float(middle["c"]) > float(pivot["h"])
            if direction == "LONG"
            else float(middle["c"]) < float(pivot["l"])
        )
        opposite_rows = [
            row for row in rows[pivot_index:middle_index + 1]
            if (
                float(row["c"]) < float(row["o"])
                if direction == "LONG"
                else float(row["c"]) > float(row["o"])
            )
        ]
        if body_break and opposite_rows:
            protected = pivot
            causal_ob = opposite_rows[-1]
        break
    if protected is None or causal_ob is None:
        return None
    return {
        "engineValidatedStructure": True,
        "detectedAtUtc": as_of,
        "direction": direction,
        "fvgLeftBarId": left["barId"],
        "fvgMiddleBarId": middle["barId"],
        "fvgRightBarId": right["barId"],
        "causalObBarId": causal_ob["barId"],
        "deliveryProtectedSwingBarId": protected["barId"],
        "zoneLow": float(left["h"] if bullish else right["h"]),
        "zoneHigh": float(right["l"] if bullish else left["l"]),
        "validation": (
            "The engine verified a newly closed three-candle FVG, directional middle candle, "
            "body break of the latest confirmed M1 swing, and an opposite-color causal candle. "
            "The reviewer must decide only whether the frozen owner, scope, source lineage, "
            "objective, and first-retest eligibility remain valid."
        ),
    }


def advance_pending_order(
    rates: np.ndarray,
    start_index: int,
    scenario: dict[str, Any],
    order: dict[str, Any],
    decision: dict[str, Any],
    config: dict[str, Any],
    entry_deadline: int | None = None,
) -> tuple[str, int, str]:
    direction_value = scenario["direction"]
    entry = float(order["entry"])
    point = float(config["point"])
    next_review = parse_utc(str(decision["nextReviewAtUtc"]))
    cancellation_kinds = {
        "SOURCE_INVALIDATION", "OBJECTIVE_REACHED", "ORDER_CANCEL_LEVEL",
    }
    for index in range(start_index + 1, len(rates)):
        row = rates[index]
        available = int(row["time"]) + 60
        if entry_deadline is not None and available > entry_deadline:
            return "END", index - 1, "ENTRY_WINDOW_CLOSED"
        spread = float(row["spread"]) * point
        # An intent preserves an unfilled HTF reaction scenario while waiting for
        # a causal delivery FVG. It is not a broker order and must never fill at
        # the old OB price.
        intent_only = bool(order.get("intentOnly")) or (
            order.get("executionModel") == "HTF_OB_REACTION_INTENT"
        )
        if intent_only:
            filled = False
        elif direction_value == "LONG":
            filled = float(row["low"]) + spread <= entry
        else:
            filled = float(row["high"]) >= entry
        for event in decision.get("watchEvents", []):
            if (
                str(event.get("kind")) in cancellation_kinds
                and available <= parse_utc(str(event["validUntilUtc"]))
                and watch_hit(
                    event, row, point,
                    rates[index - 1] if index > 0 else None,
                )
            ):
                return "REVIEW", index, str(event["kind"])
        if filled:
            return "FILLED", index, "ENTRY_FILLED"
        if (
            order.get("executionModel") in {
                "HTF_OB_REACTION", "HTF_OB_REACTION_INTENT",
            }
            and index >= 2
            and is_local_delivery_fvg(rates, index, direction_value)
        ):
            return "REVIEW", index, "LOCAL_DELIVERY_FVG"
        if available >= next_review:
            return "REVIEW", index, "SCHEDULED_REVIEW"
    return "END", len(rates) - 1, "END_OF_DATA"


def simulate_filled_position(
    rates: np.ndarray,
    filled_index: int,
    scenario: dict[str, Any],
    order: dict[str, Any],
    config: dict[str, Any],
) -> tuple[dict[str, Any] | None, int]:
    direction_value = scenario["direction"]
    entry, sl, tp = float(order["entry"]), float(order["stopLoss"]), float(order["takeProfit"])
    point = float(config["point"])
    for index in range(filled_index, len(rates)):
        row = rates[index]
        spread = float(row["spread"]) * point
        if direction_value == "LONG":
            sl_hit = float(row["low"]) <= sl
            tp_hit = float(row["high"]) >= tp
        else:
            sl_hit = float(row["high"]) + spread >= sl
            tp_hit = float(row["low"]) + spread <= tp
        if sl_hit or tp_hit:
            outcome = "SL" if sl_hit else "TP"
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            return ({
                "filled_at": utc_text(int(rates[filled_index]["time"]) + 60),
                "closed_at": utc_text(int(row["time"]) + 60),
                "outcome": outcome,
                "r": -1.0 if outcome == "SL" else reward / risk,
            }, index)
    return None, len(rates) - 1


def provider_calls_in_ledger(rows: list[dict[str, Any]]) -> int:
    total = 0
    for row in rows:
        if row.get("event") != "AI_DECISION":
            continue
        calls = row.get("providerCalls")
        total += len(calls) if isinstance(calls, list) and calls else 1
    return total


def clear_terminal_resume_decision(
    previous: dict[str, Any] | None,
    lifecycle_as_of: str | None,
) -> tuple[dict[str, Any] | None, str | None, bool]:
    """Prevent a terminal cancellation from reviving its scenario on resume."""
    if not isinstance(previous, dict):
        return previous, lifecycle_as_of, False
    if previous.get("action") != "CANCEL" and previous.get("state") != "CANCELED":
        return previous, lifecycle_as_of, False
    return None, str(previous.get("asOfUtc", lifecycle_as_of or "")), True


def reconstruct_resume_state(
    source_run: Path,
    rates: np.ndarray,
    config: dict[str, Any],
    seen_runs: set[str] | None = None,
) -> dict[str, Any]:
    seen = set(seen_runs or set())
    if source_run.name in seen:
        raise ValueError("resume chain contains a cycle")
    seen.add(source_run.name)
    manifest_path = source_run / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"resume source has no manifest: {source_run}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("pipelineVersion") != PIPELINE_VERSION:
        raise ValueError(
            "resume source was created by an incompatible replay pipeline; "
            "start a fresh run"
        )
    ledger_path = source_run / "decision_ledger.jsonl"
    if not ledger_path.exists():
        raise ValueError(f"resume source has no decision ledger: {source_run}")
    rows = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    verify_hash_chain(rows, source_run)
    resume_markers = [row for row in rows if row.get("event") == "RUN_RESUMED"]
    parent_state = None
    if resume_markers and resume_markers[-1].get("sourceRun"):
        parent_state = reconstruct_resume_state(
            RUN_ROOT / str(resume_markers[-1]["sourceRun"]),
            rates,
            config,
            seen,
        )
    reset_positions = [
        index for index, row in enumerate(rows)
        if row.get("event") in {
            "TRADE_CLOSED", "PENDING_REVIEW_REJECTED",
            "CANDLE_QUERY_BUDGET_FALLBACK", "LOCAL_SCENARIO_TERMINATED",
            "LOCAL_SCENARIO_CANCELED",
        }
    ]
    evidence_source_rows = (
        rows[reset_positions[-1] + 1:] if reset_positions else rows
    )
    evidence_rows = [
        row for row in evidence_source_rows
        if row.get("event") in {
            "CANDLE_EVIDENCE_RETURNED", "CANDLE_EVIDENCE_PREFETCHED",
            "SEMANTIC_EVIDENCE_RECOVERY",
        }
    ]
    parent_archive = (
        [] if reset_positions
        else list(parent_state.get("candleEvidenceArchive", []) if parent_state else [])
    )
    archive = parent_archive + [
        block
        for row in evidence_rows
        for block in row.get("evidence", [])
    ]

    # Re-evaluate stored responses with all evidence that was recovered later in
    # the same run. The first valid response for an as-of/phase pair is
    # authoritative; a retry is never allowed to overwrite it.
    accepted: list[dict[str, Any]] = []
    last_substantive = copy.deepcopy(parent_state.get("previous")) if parent_state else None
    direct_evidence_archive: list[dict[str, Any]] = []
    accepted_slots: set[tuple[str, str]] = set()
    lifecycle_reset = False
    lifecycle_as_of: str | None = None
    for row in rows:
        if row.get("event") == "TRADE_CLOSED":
            accepted.clear()
            accepted_slots.clear()
            last_substantive = None
            direct_evidence_archive = []
            lifecycle_reset = True
            lifecycle_as_of = str(row.get("trade", {}).get("closed_at", ""))
            continue
        if row.get("event") == "PENDING_REVIEW_REJECTED":
            accepted.clear()
            accepted_slots.clear()
            last_substantive = None
            direct_evidence_archive = []
            lifecycle_reset = True
            lifecycle_as_of = str(row.get("asOfUtc", ""))
            continue
        if row.get("event") == "LOCAL_SCENARIO_TERMINATED":
            accepted.clear()
            accepted_slots.clear()
            last_substantive = None
            direct_evidence_archive = []
            lifecycle_reset = True
            lifecycle_as_of = str(row.get("asOfUtc", ""))
            continue
        if row.get("event") == "LOCAL_SCENARIO_CANCELED":
            accepted.clear()
            accepted_slots.clear()
            last_substantive = None
            direct_evidence_archive = []
            lifecycle_reset = True
            lifecycle_as_of = str(row.get("asOfUtc", ""))
            continue
        if row.get("event") == "CANDLE_QUERY_BUDGET_FALLBACK":
            accepted.clear()
            accepted_slots.clear()
            last_substantive = copy.deepcopy(row.get("decision"))
            direct_evidence_archive = []
            lifecycle_reset = True
            lifecycle_as_of = str(row.get("asOfUtc", ""))
            continue
        if row.get("event") != "AI_DECISION":
            continue
        raw_decision = row.get("decision", {})
        if raw_decision.get("action") == "QUERY_CANDLES":
            continue
        slot = (str(row.get("asOfUtc", "")), str(row.get("phase", "")))
        if slot in accepted_slots:
            continue
        try:
            decision = copy.deepcopy(raw_decision)
            decision_as_of = parse_utc(str(decision["asOfUtc"]))
            row_evidence = list(row.get("resolvedBarEvidence") or [])
            validation_evidence = [
                *archive, *direct_evidence_archive, *row_evidence,
            ]
            normalize_decision_state(decision, last_substantive)
            normalize_decision_queries(decision)
            normalize_review_schedule(decision, config, decision_as_of)
            normalize_numeric_claims_from_evidence(
                decision, validation_evidence, config
            )
            errors = validate_decision(
                decision, config, decision_as_of, validation_evidence,
                previous_decision=last_substantive,
            )
        except (KeyError, TypeError, ValueError):
            continue
        if errors:
            continue
        accepted.append({**row, "decision": decision, "validationErrors": []})
        accepted_slots.add(slot)
        last_substantive = decision
        direct_evidence_archive.extend(row_evidence)

    if not rows:
        raise ValueError("resume source has no decision ledger entries")
    if not accepted and last_substantive is None and not lifecycle_reset:
        summary_path = source_run / "summary.json"
        summary = (
            json.loads(summary_path.read_text(encoding="utf-8"))
            if summary_path.exists() else {}
        )
        query_decisions = [
            row for row in rows
            if row.get("event") == "AI_DECISION"
            and row.get("decision", {}).get("action") == "QUERY_CANDLES"
        ]
        if summary.get("stoppedReason") == "CANDLE_QUERY_BUDGET" and query_decisions:
            last_query = query_decisions[-1]
            last_substantive = query_budget_fallback_decision(
                as_of=str(last_query["asOfUtc"]),
                config=config,
                exhausted_decision=dict(last_query["decision"]),
            )
            lifecycle_reset = True
            lifecycle_as_of = str(last_query["asOfUtc"])
            archive = []
        else:
            raise ValueError("resume source has no decision valid under the current contract")
    previous = accepted[-1]["decision"] if accepted else last_substantive
    # Older ledgers predate LOCAL_SCENARIO_CANCELED.  A terminal CANCEL must
    # still resume as a clean FLAT/MAP lifecycle rather than reviving its
    # scenario and watch events.
    previous, lifecycle_as_of, cleared_terminal = clear_terminal_resume_decision(
        previous, lifecycle_as_of
    )
    if cleared_terminal:
        archive = []
        direct_evidence_archive = []
    as_of_text = (
        str(previous.get("asOfUtc", ""))
        if isinstance(previous, dict) else str(lifecycle_as_of or "")
    )
    phase = str(previous.get("phase", "MAP")) if isinstance(previous, dict) else "MAP"
    as_of = parse_utc(as_of_text)
    indexes = np.flatnonzero(rates["time"] + 60 <= as_of)
    if not len(indexes):
        raise ValueError("resume as-of is outside the dataset")
    query_round = (
        sum(
            row.get("asOfUtc") == as_of_text and row.get("phase") == phase
            for row in evidence_rows
        )
        if isinstance(previous, dict) else 0
    )
    decision_calls = [row for row in rows if row.get("event") == "AI_DECISION"]
    carried_calls = int(resume_markers[-1].get("carriedApiCalls", 0)) if resume_markers else 0
    carried_tokens = int(resume_markers[-1].get("carriedTokenBudget", 0)) if resume_markers else 0
    recorded_tokens = sum(
        int(row.get("usage", {}).get("totalTokenCount", 0))
        for row in decision_calls
    )
    trades = list(parent_state.get("trades", []) if parent_state else [])
    trades.extend(row["trade"] for row in rows if row.get("event") == "TRADE_CLOSED")
    active_order = (
        previous.get("order")
        if isinstance(previous, dict) and previous.get("state") == "PENDING"
        else None
    )
    active_scenario = previous.get("scenario") if active_order and isinstance(previous, dict) else None
    return {
        "sourceRun": source_run.name,
        "cursor": int(indexes[-1]),
        "previous": previous,
        "activeOrder": active_order,
        "activeScenario": active_scenario,
        # Provider failures have no usage metadata and must not consume the
        # successful-call or token budget merely because a call folder exists.
        "callCount": carried_calls + provider_calls_in_ledger(rows),
        "totalTokens": carried_tokens + recorded_tokens,
        "trades": trades,
        "phase": phase,
        "queryRound": query_round,
        "candleEvidenceArchive": [*archive, *direct_evidence_archive],
    }


def run_replay(args: argparse.Namespace) -> int:
    from scripts.gemini_replay_provider import GeminiReplayError
    from scripts.manual_replay_provider import ManualReplayError
    from scripts.codex_replay_provider import CodexReplayError

    api_key, config = load_secret()
    decision_provider = str(getattr(args, "decision_provider", "gemini"))
    rates, metadata = load_rates(config)
    replay_start, replay_end = parse_utc(config["replayStartUtc"]), parse_utc(config["replayEndUtc"])
    start_indexes = np.flatnonzero(rates["time"] + 60 >= replay_start)
    if not len(start_indexes):
        raise SystemExit("replay start is outside the dataset")
    resume_state = None
    if getattr(args, "resume_run", None):
        source_run = RUN_ROOT / str(args.resume_run)
        try:
            resume_state = reconstruct_resume_state(source_run, rates, config)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(
                f"MENTOR_AI_REPLAY_RESUME_FAILED source={source_run.name} "
                f"reason={exc}",
                flush=True,
            )
            return 2
    cursor = int(resume_state["cursor"] if resume_state else start_indexes[0])
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RUN_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "runId": run_id,
        "createdAtUtc": utc_text(int(datetime.now(timezone.utc).timestamp())),
        "symbol": config["symbol"],
        "replayStartUtc": config["replayStartUtc"],
        "replayEndUtc": config["replayEndUtc"],
        "dataset": str(dataset_path(config).relative_to(ROOT)),
        "datasetSha256": sha256(dataset_path(config)),
        "datasetMetadata": metadata,
        "authoritySha256": sha256(ROOT / "AGENTS.md"),
        "apiContractManifestSha256": sha256(CONTRACT_MANIFEST),
        "model": config["model"],
        "reviewerModel": config.get("reviewerModel"),
        "decisionProvider": decision_provider,
        "pipelineVersion": PIPELINE_VERSION,
        "forbiddenTruthLoaded": False,
        "resumedFrom": resume_state["sourceRun"] if resume_state else None,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ledger = run_dir / "decision_ledger.jsonl"
    trades_path = run_dir / "trades.csv"
    previous: dict[str, Any] | None = resume_state["previous"] if resume_state else None
    active_order: dict[str, Any] | None = resume_state["activeOrder"] if resume_state else None
    active_scenario: dict[str, Any] | None = resume_state["activeScenario"] if resume_state else None
    previous_hash = "GENESIS"
    call_count = int(resume_state["callCount"] if resume_state else 0)
    total_tokens = int(resume_state["totalTokens"] if resume_state else 0)
    run_call_count = 0
    run_tokens = 0
    scout_call_count = 0
    reviewer_call_count = 0
    scout_tokens = 0
    reviewer_tokens = 0
    local_wakeup_count = 0
    local_map_wakeup_count = 0
    stopped_reason = "REPLAY_END"
    last_call_started = 0.0
    trades: list[dict[str, Any]] = list(resume_state["trades"] if resume_state else [])
    phase = str(resume_state["phase"] if resume_state else "MAP")
    query_round = int(resume_state["queryRound"] if resume_state else 0)
    current_candle_evidence: list[dict[str, Any]] = []
    candle_evidence_archive: list[dict[str, Any]] = list(
        resume_state["candleEvidenceArchive"] if resume_state else []
    )
    local_trigger_wakeup: dict[str, Any] | None = None
    consumed_map_roots: set[str] = set(
        (previous or {}).get("_consumedMapWakeRoots") or []
    )
    if resume_state:
        source_ledger = RUN_ROOT / str(resume_state["sourceRun"]) / "decision_ledger.jsonl"
        if source_ledger.exists():
            for line in source_ledger.read_text(encoding="utf-8-sig").splitlines():
                if not line.strip():
                    continue
                try:
                    historical = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if historical.get("event") == "LOCAL_MAP_WAKEUP":
                    root_id = str(
                        (historical.get("candidate") or {}).get("candidateRootBarId", "")
                    )
                    if root_id:
                        consumed_map_roots.add(root_id)

    if resume_state:
        if previous and previous.get("state") != "PENDING":
            normalize_review_schedule(
                previous, config, int(rates[cursor]["time"]) + 60
            )
            immediate_resume_phase = immediate_phase_transition(phase, previous)
            if immediate_resume_phase is not None:
                phase = immediate_resume_phase
                query_round = 0
            else:
                resume_cursor = cursor
                next_index, resume_event = next_decision_index(
                    rates, cursor, previous, config
                )
                if next_index is not None and int(rates[next_index]["time"]) < replay_end:
                    if resume_event == "LOCAL_TRIGGER_PATTERN":
                        _, local_trigger_wakeup = find_local_trigger_wakeup(
                            rates,
                            resume_cursor,
                            next_index,
                            str(previous["scenario"].get("direction", "")),
                            config,
                            parse_utc(str(previous["scenario"].get("refinedTouchTimeUtc")))
                            if previous["scenario"].get("refinedTouchTimeUtc") else None,
                            set(previous.get("_consumedTriggerSweepTimes") or []),
                        )
                    cursor = next_index
                    phase = phase_for(
                        str(previous.get("state", "FLAT")), resume_event
                    )
                    previous["_wakeEvent"] = resume_event
                    query_round = 0
        previous_hash = append_hash_record(ledger, {
            "event": "RUN_RESUMED",
            "sourceRun": resume_state["sourceRun"],
            "asOfUtc": utc_text(int(rates[cursor]["time"]) + 60),
            "phase": phase,
            "carriedApiCalls": call_count,
            "carriedTokenBudget": total_tokens,
            "evidenceBlocks": len(candle_evidence_archive),
        }, previous_hash)

    (
        run_call_limit,
        total_call_limit,
        run_token_limit,
        total_token_limit,
    ) = provider_budget_limits(
        config, decision_provider
    )

    print(
        f"[REPLAY START] run={run_id} symbol={config['symbol']} "
        f"range={config['replayStartUtc']}..{config['replayEndUtc']}",
        flush=True,
    )
    print(
        f"[BUDGET] perRunCalls={run_call_limit} "
        f"perRunTokens={run_token_limit} "
        f"carriedCalls={call_count} carriedTokens={total_tokens} "
        f"mapReserve={phase_token_reserve(config, 'MAP', 2)} "
        f"reviewReserve={phase_token_reserve(config, 'TRIGGER', 1)}",
        flush=True,
    )

    if active_order is not None and active_scenario is not None and previous is not None:
        pending_status, pending_cursor, pending_event = advance_pending_order(
            rates, cursor, active_scenario, active_order, previous, config,
            entry_deadline=replay_end,
        )
        if pending_status == "REVIEW":
            print(
                f"[RESUME PENDING] {utc_text(int(rates[cursor]['time']) + 60)} -> "
                f"{utc_text(int(rates[pending_cursor]['time']) + 60)} "
                f"event={pending_event}",
                flush=True,
            )
            cursor = pending_cursor
            phase = "PENDING_REVIEW"
            previous["_wakeEvent"] = pending_event
            query_round = 0
            current_candle_evidence = []
        elif pending_status == "FILLED":
            outcome, next_cursor = simulate_filled_position(
                rates, pending_cursor, active_scenario, active_order, config
            )
            if outcome is None:
                stopped_reason = "OPEN_POSITION_END_OF_DATA"
            else:
                scenario = active_scenario
                order = active_order
                trades.append({
                    "trade_id": f"GEM-{len(trades)+1:03d}",
                    "decision_at": str(previous.get("asOfUtc")),
                    **outcome,
                    "direction": scenario["direction"].lower(),
                    "scope": scenario["scope"],
                    "execution_model": order["executionModel"],
                    "root_tf": scenario["rootOb"]["tf"],
                    "child_tf": scenario["refinementPath"][-1]["tf"],
                    "entry": order["entry"], "sl": order["stopLoss"],
                    "tp": order["takeProfit"],
                    "objective": scenario["objective"]["price"],
                })
                previous_hash = append_hash_record(
                    ledger, {"event": "TRADE_CLOSED", "trade": trades[-1]},
                    previous_hash,
                )
                print(
                    f"[RESUME TRADE CLOSED] id={trades[-1]['trade_id']} "
                    f"outcome={trades[-1]['outcome']} R={trades[-1]['r']:.2f}",
                    flush=True,
                )
                cursor = next_cursor
                previous = None
                active_order = None
                active_scenario = None
                phase = "MAP"
                query_round = 0
                current_candle_evidence = []
                candle_evidence_archive = []
        else:
            stopped_reason = "PENDING_END_OF_DATA"

    while (
        stopped_reason == "REPLAY_END"
        and int(rates[cursor]["time"]) < replay_end
    ):
        watched_wake = str((previous or {}).get("_wakeEvent", ""))
        estimated_calls = (
            0 if phase == "MAP" and watched_wake in {"SOURCE_INVALIDATION", "OBJECTIVE_REACHED"}
            else 2 if phase == "MAP" and not (
                isinstance(previous, dict)
                and previous.get("state") == "WATCHING_MAP"
                and watched_wake == "ROOT_APPROACH"
            ) else 1
        )
        if run_call_count + estimated_calls > run_call_limit:
            stopped_reason = "API_CALL_BUDGET"
            break
        if call_count + estimated_calls > total_call_limit:
            stopped_reason = "API_CALL_BUDGET"
            print(
                f"[BUDGET STOP] cumulativeCalls={call_count} planned={estimated_calls} "
                f"maximum={total_call_limit} - API call not sent",
                flush=True,
            )
            break
        maximum_tokens = run_token_limit
        estimated_token_cost = phase_token_reserve(
            config, phase, estimated_calls
        )
        if run_tokens + estimated_token_cost > maximum_tokens:
            stopped_reason = "TOKEN_BUDGET"
            print(
                f"[BUDGET STOP] runTokens={run_tokens} reserve={estimated_token_cost} "
                f"maximum={maximum_tokens} - API call not sent",
                flush=True,
            )
            break
        maximum_total_tokens = total_token_limit
        if total_tokens + estimated_token_cost > maximum_total_tokens:
            stopped_reason = "TOKEN_BUDGET"
            print(
                f"[BUDGET STOP] cumulativeTokens={total_tokens} "
                f"reserve={estimated_token_cost} maximum={maximum_total_tokens} "
                "- API call not sent",
                flush=True,
            )
            break
        as_of = utc_text(int(rates[cursor]["time"]) + 60)
        minimum_interval = (
            0.0 if decision_provider in {"manual-codex", "codex-cli"}
            else float(config.get("minimumCallIntervalSeconds", 15))
        )
        remaining_wait = minimum_interval - (time.monotonic() - last_call_started)
        if remaining_wait > 0:
            time.sleep(remaining_wait)
        last_call_started = time.monotonic()
        call_started = time.monotonic()
        previous_state = previous.get("state", "FLAT") if previous else "FLAT"
        print(
            f"[API cumulative={call_count + estimated_calls:02d} "
            f"run={run_call_count + estimated_calls:02d} plannedCalls={estimated_calls}] "
            f"as-of={as_of} phase={phase} state={previous_state} "
            f"cumulativeTokens={total_tokens} runTokens={run_tokens} - rendering/requesting",
            flush=True,
        )
        try:
            prompt_evidence = compact_evidence_for_prompt(
                candle_evidence_archive, previous, phase
            )
            decision, record = request_decision(
                api_key=api_key, config=config, run_dir=run_dir, as_of=as_of,
                phase=phase, previous=previous,
                candle_evidence=prompt_evidence,
                query_round=query_round,
                decision_provider=decision_provider,
                local_trigger_wakeup=local_trigger_wakeup,
            )
        except (
            GeminiReplayError, ManualReplayError, CodexReplayError, ValueError, OSError,
            subprocess.CalledProcessError,
        ) as exc:
            stopped_reason = (
                "PROVIDER_ERROR"
                if isinstance(exc, (GeminiReplayError, ManualReplayError, CodexReplayError))
                else "REQUEST_PIPELINE_ERROR"
            )
            failed_calls = int(getattr(exc, "provider_call_count", 0))
            failed_usage = dict(getattr(exc, "usage", {}) or {})
            failed_tokens = int(failed_usage.get("totalTokenCount", 0) or 0)
            failed_provider_calls = list(getattr(exc, "provider_calls", []) or [])
            call_count += failed_calls
            run_call_count += failed_calls
            total_tokens += failed_tokens
            run_tokens += failed_tokens
            for provider_call in failed_provider_calls:
                role = str(provider_call.get("role", "reviewer"))
                role_tokens = int(provider_call.get("usage", {}).get("totalTokenCount", 0))
                if role == "scout":
                    scout_call_count += 1
                    scout_tokens += role_tokens
                else:
                    reviewer_call_count += 1
                    reviewer_tokens += role_tokens
            print(f"[REQUEST ERROR] {type(exc).__name__}: {exc}", flush=True)
            previous_hash = append_hash_record(ledger, {
                "asOfUtc": as_of, "phase": phase, "event": stopped_reason,
                "reason": str(exc), "usage": failed_usage,
                "providerCallCount": failed_calls,
                "providerCalls": failed_provider_calls,
            }, previous_hash)
            break
        provider_call_count = int(record.get("providerCallCount", 1))
        call_count += provider_call_count
        run_call_count += provider_call_count
        call_tokens = int(record["usage"].get("totalTokenCount", 0))
        total_tokens += call_tokens
        run_tokens += call_tokens
        for provider_call in record.get("providerCalls", []):
            role = str(provider_call.get("role", "reviewer"))
            role_tokens = int(provider_call.get("usage", {}).get("totalTokenCount", 0))
            if role == "scout":
                scout_call_count += 1
                scout_tokens += role_tokens
            else:
                reviewer_call_count += 1
                reviewer_tokens += role_tokens
        resolved_bar_evidence = list(record.get("resolvedBarEvidence") or [])
        if resolved_bar_evidence:
            current_candle_evidence.extend(resolved_bar_evidence)
            candle_evidence_archive.extend(resolved_bar_evidence)
        schedule_adjustment = normalize_review_schedule(
            decision, config, parse_utc(as_of)
        )
        numeric_adjustments = normalize_numeric_claims_from_evidence(
            decision, candle_evidence_archive, config
        )
        map_audit_adjustment = normalize_map_rejection_audit(
            decision, candle_evidence_archive
        )
        elapsed = time.monotonic() - call_started
        print(
            f"[DECISION] action={decision.get('action')} state={decision.get('state')} "
            f"watch={len(decision.get('watchEvents') or [])} "
            f"callTokens={record['usage'].get('totalTokenCount', 0)} "
            f"totalTokens={total_tokens} elapsed={elapsed:.1f}s",
            flush=True,
        )
        for provider_call in record.get("providerCalls", []):
            usage = provider_call.get("usage", {})
            print(
                f"[USAGE] role={provider_call.get('role')} "
                f"promptBytes={provider_call.get('promptBytes', 0)} "
                f"text={usage.get('promptTextTokenCount', usage.get('promptTokenCount', 0))} "
                f"image={usage.get('promptImageTokenCount', 0)} "
                f"thoughts={usage.get('thoughtsTokenCount', 0)} "
                f"output={usage.get('candidatesTokenCount', 0)} "
                f"total={usage.get('totalTokenCount', 0)}",
                flush=True,
            )
        if record.get("routingAdjustment"):
            adjustment = record["routingAdjustment"]
            print(
                f"[ROUTING NORMALIZED] model={adjustment['model']} "
                f"engine={adjustment['engine']}",
                flush=True,
            )
        if record.get("stateAdjustment"):
            adjustment = record["stateAdjustment"]
            print(
                f"[STATE NORMALIZED] action={adjustment['action']} "
                f"model={adjustment['modelState']} engine={adjustment['engineState']}",
                flush=True,
            )
        if record.get("queryAdjustment"):
            adjustment = record["queryAdjustment"]
            print(
                f"[QUERIES DEFERRED] action={adjustment['action']} "
                f"count={adjustment['deferredQueries']}",
                flush=True,
            )
        if schedule_adjustment:
            print(
                "[SCHEDULE] " + json.dumps(schedule_adjustment, ensure_ascii=False),
                flush=True,
            )
        errors = validate_decision(
            decision, config, parse_utc(as_of), candle_evidence_archive,
            previous_decision=previous,
        )
        errors.extend(validate_pending_entry_side(decision, record["inputPacket"]))
        previous_hash = append_hash_record(ledger, {
            "asOfUtc": as_of, "phase": phase, "event": "AI_DECISION",
            "usage": record["usage"], "decision": decision,
            "providerCalls": record.get("providerCalls", []),
            "resolvedBarEvidence": resolved_bar_evidence,
            "reviewPayload": record.get("reviewPayload"),
            "stagePayload": record.get("stagePayload"),
            "candidateFilterRejections": record.get("candidateFilterRejections", []),
            "providerRecovery": record.get("providerRecovery"),
            "modelRouting": record.get("modelRouting"),
            "routingAdjustment": record.get("routingAdjustment"),
            "stateAdjustment": record.get("stateAdjustment"),
            "queryAdjustment": record.get("queryAdjustment"),
            "scheduleAdjustment": schedule_adjustment,
            "mapAuditAdjustment": map_audit_adjustment,
            "numericAdjustments": numeric_adjustments,
            "validationErrors": errors,
        }, previous_hash)
        if errors:
            recovery_queries = recovery_queries_for_missing_origins(decision, errors)
            maximum_query_rounds = int(config.get("maximumCandleQueryRoundsPerPhase", 2))
            if recovery_queries and query_round < maximum_query_rounds:
                try:
                    resolved = resolve_candle_queries(
                        config, as_of, phase, recovery_queries
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    stopped_reason = "CANDLE_QUERY_ERROR"
                    print(f"[RECOVERY QUERY ERROR] {exc}", flush=True)
                    break
                current_candle_evidence.extend(resolved)
                candle_evidence_archive.extend(resolved)
                query_round += 1
                recovery_adjustments = normalize_numeric_claims_from_evidence(
                    decision, candle_evidence_archive, config
                )
                recovered_errors = validate_decision(
                    decision, config, parse_utc(as_of), candle_evidence_archive,
                    previous_decision=previous,
                )
                previous_hash = append_hash_record(ledger, {
                    "asOfUtc": as_of,
                    "phase": phase,
                    "event": "SEMANTIC_EVIDENCE_RECOVERY",
                    "queryRound": query_round,
                    "recoveredErrors": errors,
                    "queries": recovery_queries,
                    "evidence": resolved,
                    "numericAdjustments": recovery_adjustments,
                    "revalidatedErrors": recovered_errors,
                }, previous_hash)
                print(
                    f"[EVIDENCE RECOVERY] errors={len(errors)} "
                    f"queries={len(resolved)} candles="
                    f"{sum(len(item['candles']) for item in resolved)} "
                    "- same as-of correction",
                    flush=True,
                )
                if recovered_errors:
                    print(
                        f"[VALIDATION ERROR AFTER RECOVERY] {'; '.join(recovered_errors)}",
                        flush=True,
                    )
                    errors = recovered_errors
                else:
                    print(
                        "[EVIDENCE RECOVERY ACCEPTED] original decision validated "
                        "without another API call",
                        flush=True,
                    )
                    errors = []
            if errors:
                fatal_markers = (
                    "future ", "uses future", "broker symbol specification is unknown",
                    "broken ledger", "outside the dataset",
                )
                fatal_errors = [
                    error for error in errors
                    if any(marker in error.lower() for marker in fatal_markers)
                ]
                if fatal_errors:
                    stopped_reason = "SEMANTIC_VALIDATION_ERROR"
                    print(f"[FATAL VALIDATION ERROR] {'; '.join(fatal_errors)}", flush=True)
                    break
                previous_hash = append_hash_record(ledger, {
                    "asOfUtc": as_of, "phase": phase,
                    "event": "AI_DECISION_REJECTED",
                    "errors": errors,
                    "action": decision.get("action"),
                    "state": decision.get("state"),
                }, previous_hash)
                print(
                    f"[DECISION REJECTED] {'; '.join(errors)} - replay continues",
                    flush=True,
                )
                fallback = rejected_decision_fallback(
                    as_of=as_of,
                    phase=phase,
                    rejected_decision=decision,
                    previous_decision=previous,
                    errors=errors,
                    config=config,
                    candle_evidence=candle_evidence_archive,
                )
                fallback_errors = validate_decision(
                    fallback,
                    config,
                    parse_utc(as_of),
                    candle_evidence_archive,
                    previous_decision=previous,
                )
                if fallback_errors:
                    stopped_reason = "ENGINE_RECOVERY_ERROR"
                    previous_hash = append_hash_record(ledger, {
                        "asOfUtc": as_of,
                        "phase": phase,
                        "event": "REJECTED_DECISION_FALLBACK_FAILED",
                        "errors": fallback_errors,
                        "fallback": fallback,
                    }, previous_hash)
                    print(
                        f"[ENGINE RECOVERY ERROR] {'; '.join(fallback_errors)}",
                        flush=True,
                    )
                    break
                previous_hash = append_hash_record(ledger, {
                    "asOfUtc": as_of,
                    "phase": phase,
                    "event": "REJECTED_DECISION_FALLBACK_ACCEPTED",
                    "fallback": fallback,
                }, previous_hash)
                print(
                    f"[SAFE FALLBACK] state={fallback['state']} "
                    f"nextReview={fallback['nextReviewAtUtc']} - no M1 retry",
                    flush=True,
                )
                previous = fallback
                active_scenario = fallback.get("scenario")
                active_order = fallback.get("order")
                query_round = 0
                current_candle_evidence = []
                local_trigger_wakeup = None
                next_index, event_kind = next_decision_index(
                    rates, cursor, fallback, config
                )
                if next_index is None or int(rates[next_index]["time"]) >= replay_end:
                    break
                cursor = next_index
                phase = phase_for(str(fallback["state"]), event_kind)
                fallback["_wakeEvent"] = event_kind
                continue

        if decision.get("action") == "QUERY_CANDLES":
            if query_round >= int(config.get("maximumCandleQueryRoundsPerPhase", 2)):
                fallback = query_budget_fallback_decision(
                    as_of=as_of,
                    config=config,
                    exhausted_decision=decision,
                )
                previous_hash = append_hash_record(ledger, {
                    "asOfUtc": as_of,
                    "phase": phase,
                    "event": "CANDLE_QUERY_BUDGET_FALLBACK",
                    "queryRound": query_round,
                    "rejectedQueries": decision.get("candleQueries", []),
                    "decision": fallback,
                }, previous_hash)
                print(
                    "[QUERY BUDGET] model remained inconclusive - scenario rejected; "
                    f"next map review={fallback['nextReviewAtUtc']}",
                    flush=True,
                )
                previous = fallback
                active_order = None
                active_scenario = None
                candle_evidence_archive = []
                current_candle_evidence = []
                query_round = 0
                next_index, _ = next_decision_index(
                    rates, cursor, fallback, config
                )
                if (
                    next_index is None
                    or int(rates[next_index]["time"]) >= replay_end
                ):
                    break
                cursor = next_index
                phase = "MAP"
                local_trigger_wakeup = None
                continue
            try:
                resolved = resolve_candle_queries(
                    config, as_of, phase, list(decision.get("candleQueries", []))
                )
            except (KeyError, TypeError, ValueError) as exc:
                stopped_reason = "CANDLE_QUERY_ERROR"
                print(f"[QUERY ERROR] {exc}", flush=True)
                break
            current_candle_evidence.extend(resolved)
            candle_evidence_archive.extend(resolved)
            previous_hash = append_hash_record(ledger, {
                "asOfUtc": as_of,
                "phase": phase,
                "event": "CANDLE_EVIDENCE_RETURNED",
                "queryRound": query_round + 1,
                "evidence": resolved,
            }, previous_hash)
            previous = carry_previous_across_query(previous, decision)
            query_round += 1
            print(
                f"[CANDLE QUERY] round={query_round} requests={len(resolved)} "
                f"candles={sum(len(item['candles']) for item in resolved)} - same as-of retry",
                flush=True,
            )
            continue

        consumed_map_roots = set(
            (previous or {}).get("_consumedMapWakeRoots") or []
        ) | consumed_map_roots
        previous = decision
        consumed_map_roots.update(map_root_exclusions(decision))
        if (
            phase == "MAP"
            and isinstance(local_trigger_wakeup, dict)
            and local_trigger_wakeup.get("kind") in {
                "LOCAL_MAP_ACTIVITY_CANDIDATE", "LOCAL_FLAT_DELIVERY_CANDIDATE",
                "LOCAL_ROOT_CHILD_DELIVERY_CANDIDATE",
            }
        ):
            consumed_map_roots.add(str(
                local_trigger_wakeup.get("candidateRootBarId", "")
            ))
        if consumed_map_roots:
            previous["_consumedMapWakeRoots"] = sorted(
                item for item in consumed_map_roots if item
            )
        previous.pop("_wakeEvent", None)
        local_trigger_wakeup = None
        immediate_phase = immediate_phase_transition(phase, decision)
        if immediate_phase == "REFINEMENT":
            deferred_queries = list(decision.pop("_prefetchQueries", []))
            if deferred_queries:
                try:
                    prefetched = resolve_candle_queries(
                        config, as_of, "REFINEMENT", deferred_queries
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    stopped_reason = "CANDLE_QUERY_ERROR"
                    print(f"[PREFETCH ERROR] {exc}", flush=True)
                    break
                candle_evidence_archive.extend(prefetched)
                previous_hash = append_hash_record(ledger, {
                    "asOfUtc": as_of, "phase": "REFINEMENT",
                    "event": "CANDLE_EVIDENCE_PREFETCHED",
                    "evidence": prefetched,
                }, previous_hash)
                print(
                    f"[PREFETCH] requests={len(prefetched)} candles="
                    f"{sum(len(item['candles']) for item in prefetched)}",
                    flush=True,
                )
            print(
                "[STATE] MAP plan frozen - requesting causal refinement at the same as-of",
                flush=True,
            )
            phase = "REFINEMENT"
            query_round = 0
            current_candle_evidence = []
            continue
        if immediate_phase == "TRIGGER":
            print(
                "[STATE] causal child touched and armed - requesting M1 trigger "
                "at the same as-of",
                flush=True,
            )
            phase = "TRIGGER"
            query_round = 0
            current_candle_evidence = []
            continue
        if immediate_phase == "PENDING_REVIEW":
            active_order = dict(decision["order"])
            active_scenario = dict(decision["scenario"])
            decision["phase"] = "PENDING_REVIEW"
            decision["state"] = "PENDING"
            previous_hash = append_hash_record(ledger, {
                "event": "CAUSAL_INTENT_FROZEN",
                "asOfUtc": as_of,
                "rootOriginTime": active_order.get("rootOriginTime"),
                "childOriginTime": active_order.get("childOriginTime"),
                "objectiveSourceTime": active_order.get("objectiveSourceTime"),
                "entry": active_order.get("entry"),
                "stopLoss": active_order.get("stopLoss"),
                "takeProfit": active_order.get("takeProfit"),
            }, previous_hash)
            print(
                "[STATE] unfilled causal-child intent frozen - fast-forwarding locally "
                "to delivery FVG, invalidation, objective, or scheduled review",
                flush=True,
            )
        if decision["action"] in {"CANCEL", "NO_TRADE"}:
            active_order = None
            active_scenario = None
            candle_evidence_archive = []
        if decision["action"] == "CANCEL":
            consumed_roots = list(previous.get("_consumedMapWakeRoots") or [])
            decision = {
                "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": "MAP",
                "action": "NO_TRADE", "state": "FLAT", "scenario": None,
                "candleQueries": [], "watchEvents": [],
                "nextReviewAtUtc": utc_text(
                    parse_utc(as_of)
                    + max(60, int(config.get("maximumFlatReviewMinutes", 1440))) * 60
                ),
                "order": None, "rejectionReasons": ["RESET_AFTER_CANCEL"],
                "reason": "Canceled scenario returned to event-gated FLAT state.",
                "_consumedMapWakeRoots": consumed_roots,
            }
            previous = decision
            phase = "MAP"
            previous_hash = append_hash_record(ledger, {
                "event": "LOCAL_SCENARIO_CANCELED", "asOfUtc": as_of,
                "reason": "CANCEL_DECISION_RESET_TO_FLAT",
            }, previous_hash)
        if decision["action"] == "ORDER":
            active_order = dict(decision["order"])
            active_scenario = dict(decision["scenario"])
        elif active_order is not None and decision["state"] == "PENDING":
            proposed = decision["order"]
            frozen_fields = (
                "executionModel", "entry", "stopLoss", "takeProfit",
                "rootOriginTime", "childOriginTime", "objectiveSourceTime",
                "executionOriginTime", "executionLow", "executionHigh",
                "triggerLineage", "triggerProtectedSwing",
                "triggerProtectedSwingSourceTimeUtc", "sweepExtreme",
                "sweepExtremeSourceTimeUtc", "chochReferencePrice",
                "chochReferenceSourceTimeUtc", "chochBreakTimeUtc", "actualSpread",
                "brokerStopsLevelPrice", "slBuffer",
            )
            changed = [field for field in frozen_fields if proposed.get(field) != active_order.get(field)]
            if changed:
                previous_hash = append_hash_record(ledger, {
                    "event": "PENDING_REVIEW_REJECTED", "asOfUtc": as_of,
                    "reason": f"unreachable invariant: frozen order changed: {','.join(changed)}",
                }, previous_hash)
                stopped_reason = "ENGINE_INVARIANT_BREACH"
                print(
                    f"[ENGINE INVARIANT BREACH] frozen order changed: {','.join(changed)}",
                    flush=True,
                )
                break
            active_order["lastReauthorizedAtUtc"] = proposed["lastReauthorizedAtUtc"]

        if active_order is not None and active_scenario is not None:
            pending_status, pending_cursor, pending_event = advance_pending_order(
                rates, cursor, active_scenario, active_order, decision, config,
                entry_deadline=replay_end,
            )
            if pending_status == "REVIEW":
                print(
                    f"[PENDING REVIEW] {as_of} -> "
                    f"{utc_text(int(rates[pending_cursor]['time']) + 60)} "
                    f"event={pending_event}",
                    flush=True,
                )
                cursor = pending_cursor
                phase = "PENDING_REVIEW"
                decision["_wakeEvent"] = pending_event
                query_round = 0
                current_candle_evidence = []
                continue
            if pending_status == "END":
                stopped_reason = "PENDING_END_OF_DATA"
                break
            outcome, next_cursor = simulate_filled_position(
                rates, pending_cursor, active_scenario, active_order, config
            )
            if outcome is not None:
                scenario = active_scenario
                order = active_order
                trades.append({
                    "trade_id": f"GEM-{len(trades)+1:03d}", "decision_at": as_of,
                    **outcome, "direction": scenario["direction"].lower(), "scope": scenario["scope"],
                    "execution_model": order["executionModel"], "root_tf": scenario["rootOb"]["tf"],
                    "child_tf": scenario["refinementPath"][-1]["tf"], "entry": order["entry"],
                    "sl": order["stopLoss"], "tp": order["takeProfit"],
                    "objective": scenario["objective"]["price"],
                })
                previous_hash = append_hash_record(ledger, {"event": "TRADE_CLOSED", "trade": trades[-1]}, previous_hash)
                print(
                    f"[TRADE CLOSED] id={trades[-1]['trade_id']} "
                    f"outcome={trades[-1]['outcome']} R={trades[-1]['r']:.2f} "
                    f"closed={trades[-1]['closed_at']}",
                    flush=True,
                )
                cursor = next_cursor
                previous = None
                active_order = None
                active_scenario = None
                phase = "MAP"
                query_round = 0
                current_candle_evidence = []
                candle_evidence_archive = []
                local_trigger_wakeup = None
                continue
            stopped_reason = "OPEN_POSITION_END_OF_DATA"
            break
        next_index, event_kind = next_decision_index(rates, cursor, decision, config)
        if next_index is None or int(rates[next_index]["time"]) >= replay_end:
            break
        if event_kind == "LOCAL_MAP_ACTIVITY":
            _, local_trigger_wakeup = find_local_map_wakeup(
                rates, cursor, next_index, config,
                excluded_root_ids=map_root_exclusions(decision),
                strict_only=str(decision.get("state", ""))
                in {"PREPARED", "ARMED", "TRIGGERED"},
            )
            local_map_wakeup_count += 1
            detected_root = str(
                (local_trigger_wakeup or {}).get("candidateRootBarId", "")
            )
            if detected_root:
                consumed_map_roots.add(detected_root)
            print(
                f"[LOCAL MAP WAKEUP] as-of="
                f"{utc_text(int(rates[next_index]['time']) + 60)} "
                f"rootCandidate={(local_trigger_wakeup or {}).get('candidateRootBarId')} "
                "- screening only; no trade authority",
                flush=True,
            )
            previous_hash = append_hash_record(ledger, {
                "event": "LOCAL_MAP_WAKEUP",
                "asOfUtc": utc_text(int(rates[next_index]["time"]) + 60),
                "candidate": local_trigger_wakeup,
            }, previous_hash)
        elif event_kind == "LOCAL_TRIGGER_PATTERN":
            _, local_trigger_wakeup = find_local_trigger_wakeup(
                rates,
                cursor,
                next_index,
                str(decision["scenario"].get("direction", "")),
                config,
                parse_utc(str(decision["scenario"].get("refinedTouchTimeUtc")))
                if decision["scenario"].get("refinedTouchTimeUtc") else None,
                set(decision.get("_consumedTriggerSweepTimes") or []),
            )
            local_wakeup_count += 1
            print(
                f"[LOCAL TRIGGER WAKEUP] as-of="
                f"{utc_text(int(rates[next_index]['time']) + 60)} "
                f"candidates={len((local_trigger_wakeup or {}).get('candidates', []))} "
                "- no API polling used during scan",
                flush=True,
            )
            previous_hash = append_hash_record(ledger, {
                "event": "LOCAL_TRIGGER_WAKEUP",
                "asOfUtc": utc_text(int(rates[next_index]["time"]) + 60),
                "candidate": local_trigger_wakeup,
            }, previous_hash)
        else:
            local_trigger_wakeup = None
        next_as_of = utc_text(int(rates[next_index]["time"]) + 60)
        print(
            f"[FAST FORWARD] {as_of} -> {next_as_of} event={event_kind} "
            f"nextPhase={phase_for(str(decision['state']), event_kind)}",
            flush=True,
        )
        cursor = next_index
        if event_kind == "CHILD_TOUCH" and decision.get("state") == "PREPARED":
            try:
                armed, touch_evidence = locally_arm_child_touch(
                    decision, rates[cursor], config
                )
            except (KeyError, TypeError, ValueError) as exc:
                stopped_reason = "ENGINE_INVARIANT_BREACH"
                print(f"[ENGINE INVARIANT BREACH] local child touch: {exc}", flush=True)
                break
            armed_errors = validate_decision(
                armed, config, parse_utc(next_as_of),
                [*candle_evidence_archive, touch_evidence],
                previous_decision=decision,
            )
            if armed_errors:
                stopped_reason = "ENGINE_INVARIANT_BREACH"
                print(
                    "[ENGINE INVARIANT BREACH] local ARM invalid: "
                    + "; ".join(armed_errors),
                    flush=True,
                )
                break
            candle_evidence_archive.append(touch_evidence)
            previous_hash = append_hash_record(ledger, {
                "asOfUtc": next_as_of,
                "phase": "REFINEMENT",
                "event": "AI_DECISION",
                "decisionSource": "local-engine-child-touch",
                "usage": {
                    "promptTokenCount": 0,
                    "candidatesTokenCount": 0,
                    "totalTokenCount": 0,
                },
                "providerCalls": [],
                "resolvedBarEvidence": [touch_evidence],
                "decision": armed,
                "validationErrors": [],
            }, previous_hash)
            print(
                f"[LOCAL CHILD TOUCH] {next_as_of} bar="
                f"{armed['scenario']['refinedTouchBarId']} - ARMED without API call",
                flush=True,
            )
            previous = armed
            query_round = 0
            current_candle_evidence = []
            local_trigger_wakeup = None
            trigger_index, trigger_event = next_decision_index(
                rates, cursor, armed, config
            )
            if (
                trigger_index is None
                or int(rates[trigger_index]["time"]) >= replay_end
            ):
                break
            if trigger_event == "LOCAL_TRIGGER_PATTERN":
                _, local_trigger_wakeup = find_local_trigger_wakeup(
                    rates,
                    cursor,
                    trigger_index,
                    str(armed["scenario"].get("direction", "")),
                    config,
                    parse_utc(str(armed["scenario"]["refinedTouchTimeUtc"])),
                    set(armed.get("_consumedTriggerSweepTimes") or []),
                )
                local_wakeup_count += 1
                previous_hash = append_hash_record(ledger, {
                    "event": "LOCAL_TRIGGER_WAKEUP",
                    "asOfUtc": utc_text(int(rates[trigger_index]["time"]) + 60),
                    "candidate": local_trigger_wakeup,
                }, previous_hash)
            trigger_as_of = utc_text(int(rates[trigger_index]["time"]) + 60)
            if trigger_event in {"SOURCE_INVALIDATION", "OBJECTIVE_REACHED"}:
                previous_hash = append_hash_record(ledger, {
                    "event": "LOCAL_SCENARIO_TERMINATED",
                    "asOfUtc": trigger_as_of,
                    "reason": trigger_event,
                    "scenarioId": armed.get("scenario", {}).get("scenarioId"),
                }, previous_hash)
                print(
                    f"[LOCAL TERMINATION] {trigger_as_of} reason={trigger_event} "
                    "- returning to MAP without API call",
                    flush=True,
                )
                cursor = trigger_index
                previous = None
                active_order = None
                active_scenario = None
                phase = "MAP"
                query_round = 0
                current_candle_evidence = []
                candle_evidence_archive = []
                local_trigger_wakeup = None
                continue
            print(
                f"[FAST FORWARD] {next_as_of} -> {trigger_as_of} "
                f"event={trigger_event} nextPhase=TRIGGER",
                flush=True,
            )
            cursor = trigger_index
            phase = "TRIGGER"
            previous["_wakeEvent"] = trigger_event
            continue
        if event_kind in {"SOURCE_INVALIDATION", "OBJECTIVE_REACHED"}:
            previous_hash = append_hash_record(ledger, {
                "event": "LOCAL_SCENARIO_TERMINATED",
                "asOfUtc": next_as_of,
                "reason": event_kind,
                "scenarioId": (decision.get("scenario") or {}).get("scenarioId"),
            }, previous_hash)
            print(
                f"[LOCAL TERMINATION] {next_as_of} reason={event_kind} "
                "- returning to MAP without API call",
                flush=True,
            )
            previous = None
            active_order = None
            active_scenario = None
            phase = "MAP"
            query_round = 0
            current_candle_evidence = []
            candle_evidence_archive = []
            local_trigger_wakeup = None
            continue
        phase = phase_for(str(decision["state"]), event_kind)
        previous["_wakeEvent"] = event_kind
        query_round = 0
        current_candle_evidence = []

    fields = ["trade_id", "decision_at", "filled_at", "closed_at", "direction", "scope", "execution_model", "root_tf", "child_tf", "entry", "sl", "tp", "outcome", "r", "objective"]
    with trades_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(trades)
    summary = {
        "runId": run_id,
        "decisionProvider": decision_provider,
        # Primary usage fields describe only this process invocation. Carried
        # usage is retained separately for audit and never consumes this run's budget.
        "apiCalls": run_call_count if decision_provider == "gemini" else 0,
        "codexJudgmentInvocations": (
            run_call_count if decision_provider in {"manual-codex", "codex-cli"} else 0
        ),
        "totalTokens": run_tokens,
        "carriedApiCalls": call_count - run_call_count,
        "carriedTokens": total_tokens - run_tokens,
        "cumulativeApiCalls": call_count,
        "cumulativeTokens": total_tokens,
        "localTriggerWakeups": local_wakeup_count,
        "localMapWakeups": local_map_wakeup_count,
        "scoutCalls": scout_call_count,
        "reviewerCalls": reviewer_call_count,
        "scoutTokens": scout_tokens,
        "reviewerTokens": reviewer_tokens,
        "targetTokenBudget": 120000,
        "targetTokenBudgetExceeded": run_tokens > 120000,
        "trades": len(trades), "totalR": sum(float(row["r"]) for row in trades),
        "stoppedReason": stopped_reason,
        "completed": stopped_reason == "REPLAY_END",
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print(run_dir)
    return 0 if summary["completed"] else 2


def audit_resume(args: argparse.Namespace) -> int:
    _, config = load_secret()
    rates, _ = load_rates(config)
    source_run = RUN_ROOT / str(args.source_run)
    state = reconstruct_resume_state(source_run, rates, config)
    previous = copy.deepcopy(state["previous"])
    if previous is None:
        result = {
            "sourceRun": state["sourceRun"],
            "asOfUtc": utc_text(int(rates[state["cursor"]]["time"]) + 60),
            "phase": "MAP", "action": "NONE", "state": "FLAT",
            "nextEvent": "IMMEDIATE_MAP", "nextAsOfUtc": utc_text(
                int(rates[state["cursor"]]["time"]) + 60
            ),
            "carriedApiCalls": state["callCount"],
            "carriedTokens": state["totalTokens"],
            "evidenceBlocks": len(state["candleEvidenceArchive"]),
        }
        print("MENTOR_AI_REPLAY_RESUME_AUDIT_OK")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    as_of = parse_utc(str(previous["asOfUtc"]))
    normalize_review_schedule(previous, config, as_of)
    normalize_numeric_claims_from_evidence(
        previous, state["candleEvidenceArchive"], config
    )
    errors = validate_decision(
        previous, config, as_of, state["candleEvidenceArchive"],
    )
    if errors:
        print("MENTOR_AI_REPLAY_RESUME_AUDIT_FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 2
    immediate = immediate_phase_transition(str(previous["phase"]), previous)
    if immediate is not None:
        next_index = int(state["cursor"])
        next_event = f"IMMEDIATE_{immediate}"
    else:
        next_index, next_event = next_decision_index(
            rates, int(state["cursor"]), previous, config
        )
    result = {
        "sourceRun": state["sourceRun"],
        "asOfUtc": previous["asOfUtc"],
        "phase": previous["phase"],
        "action": previous["action"],
        "state": previous["state"],
        "nextEvent": next_event,
        "nextAsOfUtc": (
            utc_text(int(rates[next_index]["time"]) + 60)
            if next_index is not None else None
        ),
        "carriedApiCalls": state["callCount"],
        "carriedTokens": state["totalTokens"],
        "evidenceBlocks": len(state["candleEvidenceArchive"]),
    }
    print("MENTOR_AI_REPLAY_RESUME_AUDIT_OK")
    print(json.dumps(result, ensure_ascii=False))
    return 0


def judge(args: argparse.Namespace) -> int:
    api_key, config = load_secret()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RUN_ROOT / run_id
    previous = None
    if args.state and args.state.exists():
        previous = json.loads(args.state.read_text(encoding="utf-8-sig"))
    _, record = request_decision(api_key=api_key, config=config, run_dir=run_dir, as_of=args.as_of, phase=args.phase, previous=previous)
    destination = run_dir / "calls" / f"{args.as_of.replace(':', '-')}_{args.phase.lower()}" / "decision.json"
    print(destination)
    return 0


def load_trade_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def trade_time(row: dict[str, str]) -> int:
    value = row.get("decision_at") or row.get("decisionAt") or row.get("filled_at") or row.get("filledAt")
    if not value:
        raise ValueError("trade row has no decision/fill time")
    return parse_utc(value)


def direction(row: dict[str, str]) -> str:
    return str(row.get("direction", "")).strip().lower()


def price(row: dict[str, str], *keys: str) -> float:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return float(value)
    return math.nan


def compare(args: argparse.Namespace) -> int:
    truth = load_trade_rows(args.truth)
    candidate = load_trade_rows(args.candidate)
    if args.start:
        start = parse_utc(args.start)
        truth = [row for row in truth if trade_time(row) >= start]
        candidate = [row for row in candidate if trade_time(row) >= start]
    if args.end:
        end = parse_utc(args.end)
        truth = [row for row in truth if trade_time(row) < end]
        candidate = [row for row in candidate if trade_time(row) < end]
    unmatched = set(range(len(candidate)))
    rows: list[dict[str, Any]] = []
    for expected in truth:
        expected_time = trade_time(expected)
        options = [
            (abs(trade_time(candidate[index]) - expected_time), index)
            for index in unmatched
            if direction(candidate[index]) == direction(expected)
            and abs(trade_time(candidate[index]) - expected_time) <= args.window_hours * 3600
        ]
        if not options:
            rows.append({"truth_id": expected.get("trade_id"), "candidate_id": "", "classification": "MISS"})
            continue
        _, selected = min(options)
        unmatched.remove(selected)
        actual = candidate[selected]
        risk = abs(price(expected, "entry") - price(expected, "sl", "stop_loss", "stopLoss"))
        tolerance = max(args.tick_tolerance, risk * args.risk_fraction_tolerance)
        diffs = {
            "entry": abs(price(expected, "entry") - price(actual, "entry")),
            "sl": abs(price(expected, "sl", "stop_loss", "stopLoss") - price(actual, "sl", "stop_loss", "stopLoss")),
            "tp": abs(price(expected, "tp", "take_profit", "takeProfit") - price(actual, "tp", "take_profit", "takeProfit")),
        }
        same_scope = expected.get("scope") == actual.get("scope")
        same_roots = expected.get("root_tf") == actual.get("root_tf") and expected.get("child_tf") == actual.get("child_tf")
        if max(diffs.values()) <= args.tick_tolerance and same_scope and same_roots:
            classification = "EXACT"
        elif max(diffs.values()) <= tolerance and same_scope and same_roots:
            classification = "CAUSAL_MATCH"
        else:
            classification = "DIRECTION_ONLY"
        rows.append({
            "truth_id": expected.get("trade_id"),
            "candidate_id": actual.get("trade_id") or actual.get("tradeId"),
            "classification": classification,
            **{f"{key}_diff": f"{value:.5f}" for key, value in diffs.items()},
        })
    for index in sorted(unmatched):
        rows.append({"truth_id": "", "candidate_id": candidate[index].get("trade_id", ""), "classification": "EXTRA"})

    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["truth_id", "candidate_id", "classification", "entry_diff", "sl_diff", "tp_diff"]
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    counts = {kind: sum(row["classification"] == kind for row in rows) for kind in ("EXACT", "CAUSAL_MATCH", "DIRECTION_ONLY", "MISS", "EXTRA")}
    print(json.dumps(counts, ensure_ascii=False))
    print(output)
    return 0


def compare_funnel(args: argparse.Namespace) -> int:
    truth = json.loads(args.truth.read_text(encoding="utf-8-sig"))
    records = [
        json.loads(line)
        for line in args.ledger.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    decisions = [row for row in records if row.get("event") == "AI_DECISION"]
    output_rows: list[dict[str, Any]] = []
    for benchmark in truth.get("executableBenchmarks", []):
        expected_map = benchmark["map"]
        expected_root = expected_map["root"]
        expected_objective = expected_map["objective"]
        map_matches = []
        for row in decisions:
            decision = row.get("decision") or {}
            scenario = decision.get("scenario") or {}
            if (
                scenario.get("direction") == expected_map["direction"]
                and scenario.get("scope") == expected_map["scope"]
            ):
                map_matches.append(row)
        classification = "MAP_MISS"
        detail = "direction/scope candidate absent"
        root_matches = [
            row for row in map_matches
            if (
                row.get("decision", {}).get("scenario", {}).get("rootOb", {}).get("originTime")
                == expected_root["timeUtc"]
                and row.get("decision", {}).get("scenario", {}).get("rootOb", {}).get("tf")
                == str(expected_root["barId"]).split(":", 1)[0]
            )
        ]
        if map_matches:
            classification, detail = "ROOT_MISS", "map found but root candle differs"
        objective_matches = [
            row for row in root_matches
            if (
                row.get("decision", {}).get("scenario", {}).get("objective", {}).get("sourceTime")
                == expected_objective["timeUtc"]
                and row.get("decision", {}).get("scenario", {}).get("objective", {}).get("sourceTf")
                == str(expected_objective["barId"]).split(":", 1)[0]
                and abs(float(row.get("decision", {}).get("scenario", {}).get("objective", {}).get("price", math.inf))
                        - float(expected_objective["price"])) <= args.tick_tolerance
            )
        ]
        if root_matches:
            classification, detail = "OBJECTIVE_MISS", "root found but objective differs"
        refinement_truth = benchmark["refinement"]
        expected_path = refinement_truth.get("path") or [refinement_truth["child"]]
        child_times = [str(item["timeUtc"]) for item in expected_path]
        refinement_matches = [
            row for row in objective_matches
            if [
                str(child.get("originTime"))
                for child in row.get("decision", {}).get("scenario", {}).get("refinementPath", [])
            ] == child_times
        ]
        if objective_matches:
            classification, detail = "REFINEMENT_MISS", "map/root/objective matched; child absent"
        trigger_expected = benchmark["triggerAudit"]
        trigger_matches = []
        for row in refinement_matches:
            order = row.get("decision", {}).get("order") or {}
            if (
                order.get("triggerProtectedSwingSourceTimeUtc") == trigger_expected["protectedSwingTimeUtc"]
                and order.get("sweepExtremeSourceTimeUtc") == trigger_expected["sweepTimeUtc"]
                and order.get("sweepRecoveryTimeUtc") == trigger_expected.get(
                    "sweepRecoveryTimeUtc", trigger_expected["sweepTimeUtc"]
                )
                and order.get("chochReferenceSourceTimeUtc") == trigger_expected["chochReferenceTimeUtc"]
                and order.get("chochBreakTimeUtc") == trigger_expected["chochBreakTimeUtc"]
                and order.get("executionOriginTime") == trigger_expected["executionTimeUtc"]
            ):
                trigger_matches.append(row)
        if refinement_matches:
            classification, detail = "TRIGGER_MISS", "refinement matched; trigger lineage absent or different"
        order_matches = [
            row for row in trigger_matches
            if row.get("decision", {}).get("action") == "ORDER"
        ]
        if trigger_matches:
            classification, detail = "ORDER_MISS", "causal trigger matched but no order was authorized"
        if order_matches:
            classification, detail = "CAUSAL_MATCH", "all causal stages matched the frozen benchmark"
        output_rows.append({
            "truth_id": benchmark["tradeId"],
            "classification": classification,
            "map_candidates": len(map_matches), "root_matches": len(root_matches),
            "objective_matches": len(objective_matches),
            "refinement_matches": len(refinement_matches), "trigger_matches": len(trigger_matches),
            "order_matches": len(order_matches), "detail": detail,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "truth_id", "classification", "map_candidates", "root_matches",
        "objective_matches", "refinement_matches", "trigger_matches", "order_matches", "detail",
    ]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)
    print(json.dumps({row["classification"]: sum(item["classification"] == row["classification"] for item in output_rows) for row in output_rows}, ensure_ascii=False))
    print(args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Future-blind Gemini mentor replay tools")
    sub = parser.add_subparsers(dest="command", required=True)
    setup_parser = sub.add_parser("setup", help="API key와 로컬 설정 저장")
    setup_parser.add_argument("--config", type=Path, default=CONFIG_EXAMPLE)
    setup_parser.set_defaults(func=setup)
    preflight_parser = sub.add_parser("preflight", help="키/데이터/설정 확인")
    preflight_parser.set_defaults(func=preflight)
    probe_parser = sub.add_parser(
        "probe-schema", help="verify the complete response schema with a minimal API call"
    )
    probe_parser.set_defaults(func=probe_schema)
    latest_resume_parser = sub.add_parser(
        "latest-resume-source", help="가장 최근의 미완료 replay run ID 출력"
    )
    latest_resume_parser.set_defaults(func=latest_resume_source)
    judge_parser = sub.add_parser("judge", help="단일 as-of Gemini 판단 호출")
    judge_parser.add_argument("--as-of", required=True)
    judge_parser.add_argument("--phase", choices=("MAP", "REFINEMENT", "TRIGGER", "PENDING_REVIEW"), required=True)
    judge_parser.add_argument("--state", type=Path)
    judge_parser.add_argument("--run-id")
    judge_parser.set_defaults(func=judge)
    run_parser = sub.add_parser("run", help="설정 기간을 미래 차단 사건 기반으로 자동 재생")
    run_parser.add_argument("--run-id")
    run_parser.add_argument("--resume-run", help="기존 실패 run ID의 유효 상태에서 재개")
    run_parser.add_argument(
        "--decision-provider",
        choices=("gemini", "manual-codex", "codex-cli"),
        default="gemini",
    )
    run_parser.set_defaults(func=run_replay)
    audit_parser = sub.add_parser(
        "audit-resume", help="offline audit of a resume chain without an API call"
    )
    audit_parser.add_argument("--source-run", required=True)
    audit_parser.set_defaults(func=audit_resume)
    compare_parser = sub.add_parser("compare", help="완료된 후보 거래와 정답지 비교")
    compare_parser.add_argument("--candidate", type=Path, required=True)
    compare_parser.add_argument("--truth", type=Path, default=TRUTH_DEFAULT)
    compare_parser.add_argument("--output", type=Path, default=RUN_ROOT / "latest_parity.csv")
    compare_parser.add_argument("--window-hours", type=float, default=36.0)
    compare_parser.add_argument("--tick-tolerance", type=float, default=0.03)
    compare_parser.add_argument("--risk-fraction-tolerance", type=float, default=0.10)
    compare_parser.add_argument("--start", help="정답지 비교 시작 UTC")
    compare_parser.add_argument("--end", help="정답지 비교 종료 UTC")
    compare_parser.set_defaults(func=compare)
    funnel_parser = sub.add_parser("compare-funnel", help="compare stage-level causal parity")
    funnel_parser.add_argument("--ledger", type=Path, required=True)
    funnel_parser.add_argument("--truth", type=Path, default=FUNNEL_TRUTH_DEFAULT)
    funnel_parser.add_argument("--output", type=Path, default=RUN_ROOT / "latest_funnel_parity.csv")
    funnel_parser.add_argument("--tick-tolerance", type=float, default=0.03)
    funnel_parser.set_defaults(func=compare_funnel)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
