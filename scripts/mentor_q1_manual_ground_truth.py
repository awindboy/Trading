"""Blind manual Q1 chart replay and evidence recorder.

This tool is deliberately decision-neutral. It renders raw MT5 candles, moves a
monotonic replay clock, records human-authored map/order decisions, and checks
their later execution. It never detects or recommends structure, liquidity,
FVG/OB, direction, entry, stop, or target.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
from typing import Any
import uuid

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

try:
    from scripts.mentor_semantic_validation import (
        summarize_semantic_audits,
        validate_causal_ob,
        validate_order_semantics,
        validate_raw_fvg,
    )
except ModuleNotFoundError:
    from mentor_semantic_validation import (
        summarize_semantic_audits,
        validate_causal_ob,
        validate_order_semantics,
        validate_raw_fvg,
    )


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = Path(
    os.environ.get(
        "MENTOR_REPLAY_OUTPUT",
        str(ROOT / "output" / "mentor_q1_manual_ground_truth"),
    )
).resolve()
CAUSAL_MODE = os.environ.get("MENTOR_REQUIRE_CAUSAL_SOURCE", "").strip().lower() in {"1", "true", "yes"}
STRICT_HTF_CAUSAL_MODE = os.environ.get("MENTOR_REQUIRE_HTF_CAUSAL_ZONE", "").strip().lower() in {"1", "true", "yes"}
REQUIRE_HTF_ROOT = os.environ.get("MENTOR_REQUIRE_HTF_ROOT", "1").strip().lower() in {"1", "true", "yes"}
MANIFEST = OUTPUT / "manifest.json"
STATE = OUTPUT / "replay_state.json"
MAP_LEDGER = OUTPUT / "hourly_map_ledger.jsonl"
ORDER_LEDGER = OUTPUT / "manual_orders.jsonl"
EXECUTION_LEDGER = OUTPUT / "execution_ledger.jsonl"
NO_TRADE_LEDGER = OUTPUT / "no_trade_audit.jsonl"
POI_LEDGER = OUTPUT / "manual_poi_ledger.jsonl"
INCIDENT_LEDGER = OUTPUT / "replay_incidents.jsonl"
BASELINE_ELIGIBILITY = OUTPUT / "BASELINE_TRADE_ELIGIBILITY.json"
CAUSAL_PROOF = OUTPUT / "MANUAL_ORDER_CAUSAL_PROOF.json"
SEMANTIC_AUDIT = OUTPUT / "semantic_audit.json"
SEMANTIC_ELIGIBILITY = OUTPUT / "SEMANTIC_TRADE_ELIGIBILITY.json"
PROGRESS = OUTPUT / "PROGRESS.md"
CURRENT_CHART = OUTPUT / "current.png"

UTC = timezone.utc
WARMUP_FROM = int(datetime(2024, 10, 1, tzinfo=UTC).timestamp())
Q1_FROM = int(
    datetime.fromisoformat(
        os.environ.get("MENTOR_REPLAY_ENTRY_FROM", "2025-01-01T00:00:00+00:00")
    ).astimezone(UTC).timestamp()
)
Q1_TO = int(
    datetime.fromisoformat(
        os.environ.get("MENTOR_REPLAY_ENTRY_TO", "2025-04-01T00:00:00+00:00")
    ).astimezone(UTC).timestamp()
)
OBSERVE_TO = int(
    datetime.fromisoformat(
        os.environ.get("MENTOR_REPLAY_OBSERVE_TO", "2025-05-01T00:00:00+00:00")
    ).astimezone(UTC).timestamp()
)
POINT = 0.01

TF_SECONDS = {
    "H4": 4 * 60 * 60,
    "H1": 60 * 60,
    "M30": 30 * 60,
    "M15": 15 * 60,
    "M5": 5 * 60,
    "M1": 60,
}
WINDOWS = {"H4": 96, "H1": 144, "M30": 192, "M15": 224, "M5": 240, "M1": 300}

BG = "#080c12"
GRID = "#263241"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
BULL = "#5eead4"
BEAR = "#f87171"
ZERO_HASH = "0" * 64
CAUSAL_ZONE_TYPES = {"FVG", "OB_LAST_OPPOSITE", "OB_FVG_ORIGIN"}
INITIAL_SOURCE_ZONE_TYPES = {"OB_LAST_OPPOSITE", "OB_FVG_ORIGIN"}


def parse_time(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.astimezone(UTC).timestamp())


def iso(timestamp: int | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(int(timestamp), tz=UTC).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def parse_json_list(value: str | None, option: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid {option}: {exc}") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, dict) for item in parsed):
        raise SystemExit(f"{option} must contain a JSON list of objects.")
    return parsed


def causal_order_contract(args: argparse.Namespace, decision_at: int) -> dict[str, Any] | None:
    """Validate the explicit HTF source -> LTF refinement lineage."""
    if not CAUSAL_MODE:
        return None
    required_names = (
        "parent_zone_id",
        "parent_zone_tf",
        "parent_zone_type",
        "parent_zone_low",
        "parent_zone_high",
        "parent_zone_formed_at",
        "parent_zone_origin",
        "parent_displacement",
        "parent_break_level",
        "parent_break_level_formed_at",
        "parent_break_at",
        "parent_zone_state",
        "source_zone_type",
        "source_zone_formed_at",
        "source_zone_origin",
        "source_displacement",
        "source_break_level",
        "source_break_level_formed_at",
        "source_break_at",
        "source_touch_at",
        "source_causal_relation",
        "sweep_at",
        "choch_at",
        "choch_reference_formed_at",
        "entry_zone_type",
        "entry_zone_tf",
        "entry_zone_formed_at",
        "entry_zone_origin",
        "entry_displacement",
        "source_liquidity_kind",
        "source_liquidity_price",
        "source_liquidity_formed_at",
        "source_liquidity_tf",
        "trigger_liquidity_kind",
        "trigger_liquidity_price",
        "trigger_liquidity_formed_at",
        "trigger_liquidity_tf",
        "objective_kind",
        "objective_price",
        "objective_formed_at",
        "objective_tf",
    )
    missing = [name for name in required_names if getattr(args, name, None) in (None, "")]
    if missing:
        raise SystemExit(f"Causal replay requires explicit fields: {', '.join(missing)}")

    if args.parent_zone_type not in CAUSAL_ZONE_TYPES or args.source_zone_type not in CAUSAL_ZONE_TYPES:
        raise SystemExit("Parent and source zones must use a supported explicit zone definition.")
    if REQUIRE_HTF_ROOT and args.parent_zone_tf not in {"H4", "H1", "M30", "M15"}:
        raise SystemExit(
            "Mentor first-entry protocol requires an H4/H1/M30/M15 root OB; "
            "M5 may only be a causal refinement inside that pre-existing parent."
        )
    if STRICT_HTF_CAUSAL_MODE and (
        args.parent_zone_type not in INITIAL_SOURCE_ZONE_TYPES
        or args.source_zone_type not in INITIAL_SOURCE_ZONE_TYPES
    ):
        raise SystemExit("Strict mentor first-entry replay requires an HTF-to-LTF OB source lineage; a standalone FVG cannot authorize the first position.")
    if args.entry_zone_type not in CAUSAL_ZONE_TYPES:
        raise SystemExit("The entry zone must use a supported explicit zone definition.")
    if args.parent_zone_low >= args.parent_zone_high:
        raise SystemExit("Parent zone geometry must satisfy low < high.")
    if args.source_zone_low >= args.source_zone_high or args.entry_zone_low >= args.entry_zone_high:
        raise SystemExit("Source and entry zone geometry must satisfy low < high.")

    parent_formed_at = parse_time(args.parent_zone_formed_at)
    parent_break_level_formed_at = parse_time(args.parent_break_level_formed_at)
    parent_break_at = parse_time(args.parent_break_at)
    source_formed_at = parse_time(args.source_zone_formed_at)
    source_break_level_formed_at = parse_time(args.source_break_level_formed_at)
    source_break_at = parse_time(args.source_break_at)
    source_liquidity_formed_at = parse_time(args.source_liquidity_formed_at)
    trigger_liquidity_formed_at = parse_time(args.trigger_liquidity_formed_at)
    source_touch_at = parse_time(args.source_touch_at)
    sweep_at = parse_time(args.sweep_at)
    choch_at = parse_time(args.choch_at)
    choch_reference_formed_at = parse_time(args.choch_reference_formed_at)
    entry_formed_at = parse_time(args.entry_zone_formed_at)
    objective_formed_at = parse_time(args.objective_formed_at)
    source_liquidity_witnesses = parse_json_list(
        args.source_liquidity_witnesses_json,
        "--source-liquidity-witnesses-json",
    )
    trigger_liquidity_witnesses = parse_json_list(
        args.trigger_liquidity_witnesses_json,
        "--trigger-liquidity-witnesses-json",
    )
    objective_witnesses = parse_json_list(
        args.objective_witnesses_json,
        "--objective-witnesses-json",
    )
    known_times = (
        parent_formed_at,
        parent_break_level_formed_at,
        parent_break_at,
        source_formed_at,
        source_break_level_formed_at,
        source_break_at,
        source_liquidity_formed_at,
        trigger_liquidity_formed_at,
        source_touch_at,
        sweep_at,
        choch_at,
        choch_reference_formed_at,
        entry_formed_at,
        objective_formed_at,
    )
    if any(value > decision_at for value in known_times):
        raise SystemExit("A causal source field references information unavailable at decision time.")
    if not (
        source_liquidity_formed_at <= source_touch_at
        and trigger_liquidity_formed_at <= sweep_at
        and source_touch_at <= sweep_at < choch_at <= decision_at
    ):
        raise SystemExit(
            "Causal time order must be source formation <= source touch <= trigger sweep "
            "< separate-candle CHoCH <= decision."
        )
    entry_matches_refined_source = (
        args.entry_zone_tf == args.source_tf
        and args.entry_zone_type == args.source_zone_type
        and abs(float(args.entry_zone_low) - float(args.source_zone_low)) <= POINT
        and abs(float(args.entry_zone_high) - float(args.source_zone_high)) <= POINT
        and entry_formed_at == source_formed_at
    )
    choch_ob_fallback = (
        args.entry_zone_type in INITIAL_SOURCE_ZONE_TYPES
        and sweep_at <= entry_formed_at < choch_at
        and args.entry_zone_tf == args.trigger_tf
    )
    if not (
        entry_matches_refined_source
        or choch_ob_fallback
        or choch_at <= entry_formed_at <= decision_at
    ):
        raise SystemExit(
            "The entry zone must be the refined source OB, the final opposing trigger candle owned by the CHoCH, "
            "or a raw FVG/OB physically formed by the recorded CHoCH."
        )
    if abs(float(args.objective_price) - float(args.target)) > POINT:
        raise SystemExit("The frozen TP must match the explicit objective-liquidity price.")

    refinement_payload = args.refinement_path_json or "[]"
    if args.refinement_path_file:
        refinement_file = Path(args.refinement_path_file)
        if not refinement_file.is_absolute():
            refinement_file = ROOT / refinement_file
        try:
            refinement_payload = refinement_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"Cannot read --refinement-path-file: {exc}") from exc
    try:
        refinement_path = json.loads(refinement_payload)
    except json.JSONDecodeError as exc:
        source = "--refinement-path-file" if args.refinement_path_file else "--refinement-path-json"
        raise SystemExit(f"Invalid {source}: {exc}") from exc
    if not isinstance(refinement_path, list):
        raise SystemExit("--refinement-path-json must contain a JSON list.")

    parent = {
        "id": args.parent_zone_id,
        "timeframe": args.parent_zone_tf,
        "type": args.parent_zone_type,
        "low": float(args.parent_zone_low),
        "high": float(args.parent_zone_high),
        "formedAt": iso(parent_formed_at),
        "originCandles": args.parent_zone_origin,
        "displacementAndStructureRole": args.parent_displacement,
        "breakLevel": float(args.parent_break_level),
        "breakLevelFormedAt": iso(parent_break_level_formed_at),
        "breakAt": iso(parent_break_at),
        "stateAtDecision": args.parent_zone_state,
    }
    source = {
        "timeframe": args.source_tf,
        "type": args.source_zone_type,
        "low": float(args.source_zone_low),
        "high": float(args.source_zone_high),
        "formedAt": iso(source_formed_at),
        "originCandles": args.source_zone_origin,
        "displacementAndStructureRole": args.source_displacement,
        "breakLevel": float(args.source_break_level),
        "breakLevelFormedAt": iso(source_break_level_formed_at),
        "breakAt": iso(source_break_at),
        "causalRelationToParent": args.source_causal_relation,
    }

    nodes = [parent]
    for position, node in enumerate(refinement_path, start=1):
        if not isinstance(node, dict):
            raise SystemExit(f"Refinement node {position} must be an object.")
        required = {"timeframe", "type", "low", "high", "formedAt", "originCandles", "causalRelationToParent"}
        absent = sorted(required - set(node))
        if absent:
            raise SystemExit(f"Refinement node {position} is missing: {', '.join(absent)}")
        if node["type"] not in CAUSAL_ZONE_TYPES:
            raise SystemExit(f"Refinement node {position} has an unsupported zone type.")
        if STRICT_HTF_CAUSAL_MODE and node["type"] not in INITIAL_SOURCE_ZONE_TYPES:
            raise SystemExit(f"Strict mentor refinement node {position} must be an OB.")
        if parse_time(str(node["formedAt"])) > decision_at:
            raise SystemExit(f"Refinement node {position} was unavailable at decision time.")
        nodes.append(node)
    same_source_as_parent = args.parent_zone_tf == args.source_tf
    if same_source_as_parent:
        if refinement_path:
            raise SystemExit("A direct parent source cannot also contain a refinement path.")
        if (
            args.parent_zone_type != args.source_zone_type
            or abs(float(args.parent_zone_low) - float(args.source_zone_low)) > POINT
            or abs(float(args.parent_zone_high) - float(args.source_zone_high)) > POINT
        ):
            raise SystemExit("A direct parent source must preserve the parent's exact type and price geometry.")
        if "DIRECT" not in args.source_causal_relation.upper() and "NO UNIQUE" not in args.source_causal_relation.upper():
            raise SystemExit("A direct parent source must explain that no unique causal child was available.")
    else:
        nodes.append(source)

    for position, (upper, child) in enumerate(zip(nodes, nodes[1:]), start=1):
        if upper["timeframe"] not in TF_SECONDS or child["timeframe"] not in TF_SECONDS:
            raise SystemExit(f"Refinement edge {position} contains an unknown timeframe.")
        if TF_SECONDS[child["timeframe"]] >= TF_SECONDS[upper["timeframe"]]:
            raise SystemExit(f"Refinement edge {position} must move to a strictly lower timeframe.")
        tolerance = POINT
        if float(child["high"]) < float(upper["low"]) - tolerance or float(child["low"]) > float(upper["high"]) + tolerance:
            raise SystemExit(f"Refinement edge {position} does not overlap its parent swing zone.")
        if not str(child.get("causalRelationToParent") or "").strip():
            raise SystemExit(f"Refinement edge {position} lacks a causal relation explanation.")

    if STRICT_HTF_CAUSAL_MODE:
        if args.parent_zone_tf not in {"H4", "H1", "M30", "M15"}:
            raise SystemExit("Strict mentor replay requires a pre-existing H4/H1/M30/M15 parent cause zone; M5 cannot be the root cause.")
        if parent_formed_at > sweep_at or source_formed_at > sweep_at:
            raise SystemExit("Strict mentor replay requires the parent and selected source zones to exist before the liquidity sweep.")
        for position, node in enumerate(refinement_path, start=1):
            if parse_time(str(node["formedAt"])) > sweep_at:
                raise SystemExit(f"Strict refinement node {position} formed after the sweep and cannot explain the reaction context.")

    frozen_map = current_map()
    replay_state = load_json(STATE) if STATE.exists() else {}
    active_poi = replay_state.get("activePoi") or {}
    declared_family = active_poi.get("family") or (frozen_map.get("poiFamily") if frozen_map else None)
    context_declaration = None
    if not declared_family:
        plain_context_map = next((
            row for row in reversed(read_jsonl(MAP_LEDGER))
            if row.get("decision") in {"WAIT_POI", "MONITOR"}
            and parse_time(str(row.get("asOf"))) <= sweep_at
            and isinstance(row.get("poi"), dict)
            and row["poi"].get("direction") == args.direction
            and abs(float(row["poi"].get("low")) - float(parent["low"])) <= POINT
            and abs(float(row["poi"].get("high")) - float(parent["high"])) <= POINT
            and str(args.objective_price) in str(row.get("objective") or "")
        ), None)
        plain_map_as_of = parse_time(str(plain_context_map.get("asOf"))) if plain_context_map else decision_at + 1
        direct_strict_source = (
            STRICT_HTF_CAUSAL_MODE
            and same_source_as_parent
            and (
                "DIRECT" in args.source_causal_relation.upper()
                or "NO UNIQUE" in args.source_causal_relation.upper()
            )
        )
        predeclared_parent_poi = (
            plain_context_map is not None
            and parent_formed_at <= plain_map_as_of <= sweep_at
            and source_formed_at <= sweep_at
            and (not STRICT_HTF_CAUSAL_MODE or direct_strict_source)
        )
        if predeclared_parent_poi:
            context_declaration = {
                "type": (
                    "PREDECLARED_DIRECT_CAUSAL_PARENT"
                    if direct_strict_source
                    else "PREDECLARED_PARENT_POI"
                ),
                "mapAsOf": iso(plain_map_as_of),
                "parentLow": float(parent["low"]),
                "parentHigh": float(parent["high"]),
                "note": (
                    "The direct M30/M15 causal parent and objective were hash-sealed before the sweep; "
                    "no unique lower-timeframe source OB was asserted."
                    if direct_strict_source
                    else "The parent cause zone and objective were hash-sealed before the sweep; lower-timeframe refinement was resolved inside that parent at the trigger review."
                ),
            }

        # At a price-discovery range edge there cannot be a pre-existing HTF
        # supply/demand zone beyond the historical extreme. Permit the sweep to
        # create a direct M5 source only when the H1 range boundary and opposing
        # objective were frozen before the sweep. This is not a generic bypass
        # for missing source lineage.
        source_key = "dealingRangeLow" if args.direction == "long" else "dealingRangeHigh"
        objective_key = "dealingRangeHigh" if args.direction == "long" else "dealingRangeLow"
        range_context_map = next((
            row for row in reversed(read_jsonl(MAP_LEDGER))
            if row.get("decision") in {"WAIT_POI", "MONITOR"}
            and parse_time(str(row.get("asOf"))) <= sweep_at
            and row.get(source_key) is not None
            and row.get(objective_key) is not None
            and abs(float(row[source_key]) - float(args.source_liquidity_price)) <= POINT
            and abs(float(row[objective_key]) - float(args.objective_price)) <= POINT
        ), None)
        map_as_of = parse_time(str(range_context_map.get("asOf"))) if range_context_map else decision_at + 1
        source_boundary = range_context_map.get(source_key) if range_context_map else None
        objective_boundary = range_context_map.get(objective_key) if range_context_map else None
        range_edge_source = (
            range_context_map is not None
            and args.source_liquidity_kind == "RANGE_EDGE"
            and source_boundary is not None
            and objective_boundary is not None
            and abs(float(source_boundary) - float(args.source_liquidity_price)) <= POINT
            and abs(float(objective_boundary) - float(args.objective_price)) <= POINT
            and source_liquidity_formed_at <= map_as_of <= sweep_at
            and sweep_at <= parent_formed_at <= decision_at
            and sweep_at <= source_formed_at <= decision_at
            and same_source_as_parent
        )
        if not predeclared_parent_poi and not range_edge_source:
            raise SystemExit("Causal orders require a predeclared source family, except for a predeclared H1 range edge that creates a direct post-sweep M5 source.")
        if range_edge_source:
            context_declaration = {
                "type": "PREDECLARED_H1_RANGE_EDGE",
                "mapAsOf": iso(map_as_of),
                "sourceBoundary": float(source_boundary),
                "objectiveBoundary": float(objective_boundary),
                "note": "No pre-existing HTF OB is asserted beyond the price-discovery extreme; the sweep-created M5 OB source is explicit.",
            }
    else:
        declared_member = next((member for member in declared_family if member.get("id") == args.parent_zone_id), None)
        if declared_member is None:
            raise SystemExit("The selected parent zone was not predeclared in the active source family.")
        comparable_fields = ("timeframe", "type", "low", "high", "formedAt")
        for field in comparable_fields:
            expected = parent[field]
            actual = declared_member.get(field)
            if field in {"low", "high"}:
                matches = abs(float(expected) - float(actual)) <= POINT
            elif field == "formedAt":
                matches = parse_time(str(expected)) == parse_time(str(actual))
            else:
                matches = expected == actual
            if not matches:
                raise SystemExit(f"Parent zone field {field} does not match its predeclared source-family member.")

        if STRICT_HTF_CAUSAL_MODE:
            declared_at_value = active_poi.get("declaredAt") or (frozen_map.get("asOf") if frozen_map else None)
            if not declared_at_value or parse_time(str(declared_at_value)) > sweep_at:
                raise SystemExit("The HTF causal family must be declared before the recorded sweep.")
            if declared_family[0].get("id") != args.parent_zone_id:
                raise SystemExit("The order parent must be the root of the predeclared strict HTF family.")
            selected_family_id = active_poi.get("selectedFamilyId") or ((frozen_map.get("poi") or {}).get("selectedFamilyId") if frozen_map else None)
            if selected_family_id != declared_family[-1].get("id"):
                raise SystemExit("The order must use the predeclared final refinement node as its selected source.")

            chain_nodes = list(refinement_path)
            if not same_source_as_parent:
                chain_nodes.append(source)
            if len(declared_family) != 1 + len(chain_nodes):
                raise SystemExit("The strict order lineage must reproduce the entire predeclared HTF refinement chain without skipping nodes.")
            for position, (member, node) in enumerate(zip(declared_family[1:], chain_nodes), start=1):
                matches = (
                    member.get("timeframe") == node.get("timeframe")
                    and member.get("type") == node.get("type")
                    and abs(float(member.get("low")) - float(node.get("low"))) <= POINT
                    and abs(float(member.get("high")) - float(node.get("high"))) <= POINT
                    and parse_time(str(member.get("formedAt"))) == parse_time(str(node.get("formedAt")))
                )
                if not matches:
                    raise SystemExit(f"Strict refinement/source node {position} differs from the predeclared HTF family path.")

    return {
        "protocol": (
            "MENTOR_STRICT_HTF_CAUSAL_REFINEMENT_V3"
            if STRICT_HTF_CAUSAL_MODE
            else "MENTOR_CAUSAL_RANGE_EDGE_SOURCE_V2"
            if context_declaration
            else "MENTOR_CAUSAL_SOURCE_REFINEMENT_V2"
        ),
        **({"contextDeclaration": context_declaration} if context_declaration else {}),
        "parentZone": parent,
        "refinementPath": refinement_path,
        "sourceZone": source,
        "sourceLiquidity": {
            "kind": args.source_liquidity_kind,
            "price": float(args.source_liquidity_price),
            "formedAt": iso(source_liquidity_formed_at),
            "timeframe": args.source_liquidity_tf,
            "witnesses": source_liquidity_witnesses,
        },
        "triggerLiquidity": {
            "kind": args.trigger_liquidity_kind,
            "price": float(args.trigger_liquidity_price),
            "formedAt": iso(trigger_liquidity_formed_at),
            "timeframe": args.trigger_liquidity_tf,
            "witnesses": trigger_liquidity_witnesses,
        },
        "sourceTouchAt": iso(source_touch_at),
        "sweepAt": iso(sweep_at),
        "chochAt": iso(choch_at),
        "chochReferenceFormedAt": iso(choch_reference_formed_at),
        "entryZone": {
            "timeframe": args.entry_zone_tf,
            "type": args.entry_zone_type,
            "low": float(args.entry_zone_low),
            "high": float(args.entry_zone_high),
            "formedAt": iso(entry_formed_at),
            "originCandles": args.entry_zone_origin,
            "displacementAndStructureRole": args.entry_displacement,
            "ownedBy": "REFINED_SOURCE_OB" if entry_matches_refined_source else "RECORDED_CHOCH",
        },
        "objectiveLiquidity": {
            "kind": args.objective_kind,
            "price": float(args.objective_price),
            "formedAt": iso(objective_formed_at),
            "timeframe": args.objective_tf,
            "witnesses": objective_witnesses,
        },
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text_atomic(path: Path, content: str) -> None:
    """Replace a file atomically, with retries for short OneDrive locks."""
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error: OSError | None = None
    for attempt in range(6):
        temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            return
        except OSError as exc:
            last_error = exc
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            time.sleep(0.05 * (attempt + 1))
    raise OSError(f"Atomic write failed for {path}: {last_error}") from last_error


def save_json(path: Path, payload: dict[str, Any]) -> None:
    write_text_atomic(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_chain(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    rows = read_jsonl(path)
    previous = rows[-1]["entryHash"] if rows else ZERO_HASH
    sealed = dict(record)
    sealed["previousHash"] = previous
    sealed["entryHash"] = hashlib.sha256(previous.encode("ascii") + canonical(sealed)).hexdigest()
    rows.append(sealed)
    write_text_atomic(
        path,
        "".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            for row in rows
        ),
    )
    return sealed


def load_rates() -> np.ndarray:
    with np.load(DATASET, allow_pickle=False) as payload:
        rates = payload["rates"]
    return rates[(rates["time"] >= WARMUP_FROM) & (rates["time"] < OBSERVE_TO)]


def aggregate(rates: np.ndarray, seconds: int) -> np.ndarray:
    buckets = (rates["time"] // seconds) * seconds
    starts = np.flatnonzero(np.r_[True, buckets[1:] != buckets[:-1]])
    ends = np.r_[starts[1:], len(rates)]
    dtype = [
        ("time", "i8"),
        ("available", "i8"),
        ("open", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("close", "f8"),
    ]
    result = np.empty(len(starts), dtype=dtype)
    for output_index, (left, right) in enumerate(zip(starts, ends)):
        result[output_index] = (
            int(buckets[left]),
            int(buckets[left] + seconds),
            float(rates["open"][left]),
            float(np.max(rates["high"][left:right])),
            float(np.min(rates["low"][left:right])),
            float(rates["close"][right - 1]),
        )
    return result


def series_by_timeframe(rates: np.ndarray) -> dict[str, np.ndarray]:
    return {timeframe: aggregate(rates, seconds) for timeframe, seconds in TF_SECONDS.items()}


def expected_h1_times(series: dict[str, np.ndarray]) -> list[int]:
    return [
        int(value)
        for value in series["H1"]["available"]
        if Q1_FROM < int(value) <= Q1_TO
    ]


def require_workspace() -> tuple[dict[str, Any], dict[str, Any], np.ndarray, dict[str, np.ndarray]]:
    if not MANIFEST.exists() or not STATE.exists():
        raise SystemExit("Ground-truth workspace is not initialized. Run init first.")
    manifest = load_json(MANIFEST)
    global WARMUP_FROM, Q1_FROM, Q1_TO, OBSERVE_TO
    global CAUSAL_MODE, STRICT_HTF_CAUSAL_MODE, REQUIRE_HTF_ROOT
    WARMUP_FROM = parse_time(manifest["warmupFrom"])
    Q1_FROM = parse_time(manifest["newEntriesFrom"])
    Q1_TO = parse_time(manifest["newEntriesThrough"]) + 1
    OBSERVE_TO = parse_time(manifest["openPositionsObservedThrough"]) + 1
    CAUSAL_MODE = bool(manifest.get("causalSourceRequired", CAUSAL_MODE))
    STRICT_HTF_CAUSAL_MODE = bool(
        manifest.get("strictPreExistingHtfCauseRequired", STRICT_HTF_CAUSAL_MODE)
    )
    REQUIRE_HTF_ROOT = bool(
        manifest.get("preExistingHtfRootRequired", REQUIRE_HTF_ROOT)
    )
    rates = load_rates()
    return manifest, load_json(STATE), rates, series_by_timeframe(rates)


def draw_candles(axis: Any, bars: np.ndarray) -> None:
    for x, bar in enumerate(bars):
        colour = BULL if bar["close"] >= bar["open"] else BEAR
        axis.vlines(x, bar["low"], bar["high"], color=colour, linewidth=0.55, zorder=3)
        bottom = min(float(bar["open"]), float(bar["close"]))
        height = max(abs(float(bar["close"]) - float(bar["open"])), 1e-6)
        axis.add_patch(
            Rectangle(
                (x - 0.34, bottom),
                0.68,
                height,
                facecolor=colour,
                edgecolor=colour,
                linewidth=0.3,
                zorder=4,
            )
        )
    if len(bars):
        ticks = np.unique(np.linspace(0, len(bars) - 1, min(6, len(bars)), dtype=int))
        labels = [datetime.fromtimestamp(int(bars[index]["time"]), tz=UTC).strftime("%m-%d\n%H:%M") for index in ticks]
        axis.set_xticks(ticks, labels)
    axis.set_facecolor(BG)
    axis.grid(color=GRID, linewidth=0.45, alpha=0.35)
    axis.tick_params(colors=MUTED, labelsize=7)
    axis.yaxis.tick_right()
    for spine in axis.spines.values():
        spine.set_color(GRID)


def render_raw(series: dict[str, np.ndarray], cutoff: int, destination: Path) -> None:
    fig, axes = plt.subplots(3, 2, figsize=(15, 12), constrained_layout=True)
    for axis, timeframe in zip(axes.ravel(), TF_SECONDS):
        values = series[timeframe]
        right = int(np.searchsorted(values["available"], cutoff, side="right"))
        left = max(0, right - WINDOWS[timeframe])
        bars = values[left:right]
        if len(bars) and int(np.max(bars["available"])) > cutoff:
            raise AssertionError("Future bar leaked into rendering")
        draw_candles(axis, bars)
        axis.set_title(
            f"{timeframe} | CLOSED BARS ONLY | {len(bars)} bars",
            loc="left",
            color=TEXT,
            fontsize=9.5,
            fontweight="bold",
        )
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"GOLD BLIND MANUAL REPLAY | AS-OF {datetime.fromtimestamp(cutoff, tz=UTC):%Y-%m-%d %H:%M} UTC",
        color=TEXT,
        fontsize=14,
        fontweight="bold",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=145, facecolor=BG, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def render_zoom(series: dict[str, np.ndarray], cutoff: int, timeframe: str, count: int, destination: Path) -> None:
    values = series[timeframe]
    right = int(np.searchsorted(values["available"], cutoff, side="right"))
    left = max(0, right - count)
    bars = values[left:right]
    if len(bars) and int(np.max(bars["available"])) > cutoff:
        raise AssertionError("Future bar leaked into zoom rendering")
    fig, axis = plt.subplots(figsize=(16, 7), constrained_layout=True)
    draw_candles(axis, bars)
    axis.set_title(
        f"GOLD {timeframe} BLIND ZOOM | CLOSED BARS ONLY | AS-OF {datetime.fromtimestamp(cutoff, tz=UTC):%Y-%m-%d %H:%M} UTC",
        loc="left",
        color=TEXT,
        fontsize=13,
        fontweight="bold",
    )
    fig.patch.set_facecolor(BG)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=160, facecolor=BG, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def current_map(timestamp: int | None = None) -> dict[str, Any] | None:
    rows = read_jsonl(MAP_LEDGER)
    if timestamp is not None:
        rows = [row for row in rows if parse_time(row["asOf"]) < timestamp]
    return rows[-1] if rows else None


def parse_poi_family(
    raw: str | None,
    current: int,
    series: dict[str, np.ndarray],
    direction: str | None,
    source_file: str | None = None,
) -> list[dict[str, Any]] | None:
    if source_file:
        raw = Path(source_file).read_text(encoding="utf-8")
    if not raw:
        return None
    try:
        family = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid --poi-family-json: {exc}") from exc
    if not isinstance(family, list) or not family:
        raise SystemExit("--poi-family-json must be a non-empty JSON list.")
    required = {
        "id",
        "timeframe",
        "type",
        "low",
        "high",
        "formedAt",
        "originCandles",
        "displacementAndStructureRole",
        "state",
    }
    if STRICT_HTF_CAUSAL_MODE:
        required |= {"breakLevel", "breakLevelFormedAt", "breakAt"}
    identifiers: set[str] = set()
    for position, member in enumerate(family, start=1):
        if not isinstance(member, dict):
            raise SystemExit(f"POI family member {position} must be an object.")
        missing = sorted(required - set(member))
        if missing:
            raise SystemExit(f"POI family member {position} is missing: {', '.join(missing)}")
        if member["id"] in identifiers:
            raise SystemExit(f"Duplicate POI family id: {member['id']}")
        identifiers.add(str(member["id"]))
        if member["timeframe"] not in {"H4", "H1", "M30", "M15", "M5"}:
            raise SystemExit(f"POI family member {position} must be an H4-to-M5 context zone.")
        if member["type"] not in CAUSAL_ZONE_TYPES:
            raise SystemExit(f"POI family member {position} has an unsupported zone type.")
        if STRICT_HTF_CAUSAL_MODE and member["type"] not in INITIAL_SOURCE_ZONE_TYPES:
            raise SystemExit(f"Strict mentor POI family member {position} must be an OB; standalone HTF/LTF FVG sources are disabled.")
        if float(member["low"]) >= float(member["high"]):
            raise SystemExit(f"POI family member {position} has invalid geometry.")
        if parse_time(str(member["formedAt"])) > current:
            raise SystemExit(f"POI family member {position} was unavailable at map time.")
        if member["state"] not in {"FRESH", "PARTIAL"}:
            raise SystemExit(f"POI family member {position} must be FRESH or PARTIAL.")
        if direction is None:
            raise SystemExit("A POI family requires an explicit direction.")
        if "OB" in str(member["type"]).upper():
            checks, _ = validate_causal_ob(
                series,
                str(member["timeframe"]),
                member,
                direction,
                current,
                POINT,
                element=f"poiFamily{position}",
                touch_at=None,
                upper_bound=current,
                require_touch=False,
            )
        else:
            checks, _ = validate_raw_fvg(
                series,
                str(member["timeframe"]),
                member,
                direction,
                current,
                POINT,
                element=f"poiFamily{position}",
            )
        failures = [check["reason"] for check in checks if check["required"] and not check["valid"]]
        if failures:
            raise SystemExit(
                f"POI family member {position} failed OHLC validation: "
                + "; ".join(failures)
            )
    if STRICT_HTF_CAUSAL_MODE:
        if family[0]["timeframe"] not in {"H4", "H1", "M30", "M15"}:
            raise SystemExit("A strict POI family must start from a pre-existing H4/H1/M30/M15 cause zone.")
        for position, (parent, child) in enumerate(zip(family, family[1:]), start=1):
            if TF_SECONDS[child["timeframe"]] >= TF_SECONDS[parent["timeframe"]]:
                raise SystemExit(f"Strict POI edge {position} must move to a lower timeframe.")
            if (
                float(child["low"]) < float(parent["low"]) - POINT
                or float(child["high"]) > float(parent["high"]) + POINT
            ):
                raise SystemExit(f"Strict POI edge {position} is not price-contained in its parent zone.")
            if not str(child.get("causalRelationToParent") or "").strip():
                raise SystemExit(f"Strict POI edge {position} must explain its causal refinement relation.")
    return family


def active_order(state: dict[str, Any]) -> dict[str, Any] | None:
    value = state.get("activeOrder")
    return value if isinstance(value, dict) else None


def poi_key(poi: dict[str, Any]) -> str:
    selected = poi.get("selectedFamilyId")
    if selected:
        return f"family:{selected}"
    return (
        f"{poi.get('direction')}:{float(poi.get('low')):.4f}:"
        f"{float(poi.get('high')):.4f}:{poi.get('declaredAt') or ''}"
    )


def require_replay_unlocked(state: dict[str, Any]) -> None:
    lock = state.get("recordingErrorLock")
    if lock:
        raise SystemExit(
            "Replay is locked because an order recording failed. Correct the same "
            "record-order command, or use clear-error-lock with an explicit reason. "
            f"Original error: {lock.get('error')}"
        )


def set_recording_error_lock(command: str, error: str) -> None:
    if not STATE.exists():
        return
    try:
        state = load_json(STATE)
        state["recordingErrorLock"] = {
            "at": iso(int(state.get("viewerTime") or 0)),
            "command": command,
            "error": error,
        }
        save_json(STATE, state)
    except (OSError, ValueError, TypeError):
        return


def clear_recording_error_lock(state: dict[str, Any]) -> None:
    state.pop("recordingErrorLock", None)


def next_h1_after(expected: list[int], timestamp: int) -> int | None:
    index = int(np.searchsorted(np.asarray(expected, dtype=np.int64), timestamp, side="right"))
    return expected[index] if index < len(expected) else None


def map_recorded_at(timestamp: int) -> bool:
    # An intrahour decision uses the latest completed H1 map available at that time;
    # requiring an exact timestamp incorrectly rejects valid replay recoveries.
    return any(parse_time(item["asOf"]) <= timestamp for item in read_jsonl(MAP_LEDGER))


def map_recorded_exactly_at(timestamp: int) -> bool:
    return any(parse_time(item["asOf"]) == timestamp for item in read_jsonl(MAP_LEDGER))


def command_init(_: argparse.Namespace) -> int:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty workspace: {OUTPUT}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "entry_charts").mkdir(exist_ok=True)
    (OUTPUT / "final_charts").mkdir(exist_ok=True)
    rates = load_rates()
    series = series_by_timeframe(rates)
    expected = expected_h1_times(series)
    manifest = {
        "schema": (
            "mentor-january-strict-htf-causal-manual-ground-truth-v3"
            if STRICT_HTF_CAUSAL_MODE
            else "mentor-q1-causal-manual-ground-truth-v2"
            if CAUSAL_MODE
            else "mentor-q1-blind-manual-ground-truth-v1"
        ),
        "symbol": "GOLD",
        "dataset": str(DATASET.relative_to(ROOT)).replace("\\", "/"),
        "datasetSha256": file_sha256(DATASET),
        "warmupFrom": iso(WARMUP_FROM),
        "newEntriesFrom": iso(Q1_FROM),
        "newEntriesThrough": iso(Q1_TO - 1),
        "openPositionsObservedThrough": iso(OBSERVE_TO),
        "point": POINT,
        "expectedH1Reviews": len(expected),
        "decisionInputs": "raw MT5 M1 OHLC and spread only",
        "forbiddenDecisionInputs": ["mentor_engine", "candidate manifests", "prior Q1 outcomes", "prior manual order ledgers"],
        "causalSourceRequired": CAUSAL_MODE,
        "strictPreExistingHtfCauseRequired": STRICT_HTF_CAUSAL_MODE,
        "preExistingHtfRootRequired": REQUIRE_HTF_ROOT,
        "initialSourcePolicy": "HTF_OB_TO_CAUSAL_LTF_OB_REFINEMENT",
        "minimumLowerTimeframeObRefinements": 1,
        "firstEntryMode": "REFINED_SOURCE_OB_RETEST_AFTER_CHOCH",
        "fvgFirstEntryEnabled": False,
        "fvgPositionAddonEnabled": False,
        "stopPolicy": (
            "Beyond the selected causal source distal and sweep extreme, "
            "buffered by max(decision spread, 1 tick)"
        ),
    }
    state = {
        "viewerTime": expected[0],
        "maxRevealedTime": expected[0],
        "activePoi": None,
        "activeOrder": None,
        "completed": False,
    }
    save_json(MANIFEST, manifest)
    save_json(STATE, state)
    for path in (MAP_LEDGER, ORDER_LEDGER, EXECUTION_LEDGER, NO_TRADE_LEDGER, INCIDENT_LEDGER):
        path.touch()
    render_raw(series, expected[0], CURRENT_CHART)
    write_progress(state, expected)
    print(json.dumps({"workspace": str(OUTPUT), "firstReview": iso(expected[0]), "expectedH1Reviews": len(expected)}, ensure_ascii=False, indent=2))
    return 0


def require_current_h1_reviewed(state: dict[str, Any], expected: list[int]) -> None:
    current = int(state["viewerTime"])
    if current in expected and not map_recorded_exactly_at(current):
        raise SystemExit(f"Record the H1 map at {iso(current)} before advancing.")


def spread_price(bar: Any) -> float:
    return float(bar["spread"]) * POINT


def structural_stop_boundary(
    args: argparse.Namespace,
    rates: np.ndarray,
    decision_at: int,
) -> tuple[float, float]:
    """Return the nearest valid stop and its spread buffer for the selected causal source."""
    index = int(np.searchsorted(rates["time"], decision_at - 60, side="right") - 1)
    if index < 0:
        raise SystemExit("Cannot calculate the structural stop before the first available M1 bar.")
    buffer = max(spread_price(rates[index]), POINT)
    if args.direction == "long":
        invalidation = min(
            float(args.source_zone_low),
            float(args.source_invalidation),
            float(args.sweep_extreme),
        )
        return invalidation - buffer, buffer
    invalidation = max(
        float(args.source_zone_high),
        float(args.source_invalidation),
        float(args.sweep_extreme),
    )
    return invalidation + buffer, buffer


def require_structural_stop(
    args: argparse.Namespace,
    rates: np.ndarray,
    decision_at: int,
) -> None:
    required_stop, buffer = structural_stop_boundary(args, rates, decision_at)
    tolerance = POINT / 2
    if args.direction == "long" and float(args.stop) > required_stop + tolerance:
        raise SystemExit(
            f"Long SL {args.stop:.2f} is inside the causal source invalidation. "
            f"Use {required_stop:.2f} or lower "
            f"(source/sweep distal with {buffer:.2f} spread buffer)."
        )
    if args.direction == "short" and float(args.stop) < required_stop - tolerance:
        raise SystemExit(
            f"Short SL {args.stop:.2f} is inside the causal source invalidation. "
            f"Use {required_stop:.2f} or higher "
            f"(source/sweep distal with {buffer:.2f} spread buffer)."
        )


def require_semantic_order(
    record: dict[str, Any],
    series: dict[str, np.ndarray],
) -> dict[str, Any]:
    audit = validate_order_semantics(record, series, POINT)
    if not audit["valid"]:
        save_json(
            OUTPUT / "last_semantic_rejection.json",
            {
                "recordedAt": iso(parse_time(record["decisionAt"])),
                "order": record,
                "audit": audit,
            },
        )
        summary = "; ".join(audit["failureReasons"][:8])
        remaining = len(audit["failureReasons"]) - 8
        if remaining > 0:
            summary += f"; and {remaining} more failures"
        raise SystemExit(f"Semantic evidence rejected the order: {summary}")
    return audit


def bar_available(bar: Any) -> int:
    return int(bar["time"]) + 60


def append_execution(record: dict[str, Any]) -> None:
    append_chain(EXECUTION_LEDGER, record)


def order_event_on_bar(
    order: dict[str, Any],
    bar: Any,
    *,
    source_close_due: bool,
) -> dict[str, Any] | None:
    direction = order["direction"]
    status = order["status"]
    entry = float(order["entry"])
    stop = float(order["stopLoss"])
    target = float(order["takeProfit"])
    spread = spread_price(bar)
    bid_low = float(bar["low"])
    bid_high = float(bar["high"])
    bid_open = float(bar["open"])
    ask_low = bid_low + spread
    ask_high = bid_high + spread
    ask_open = bid_open + spread
    bid_close = float(bar["close"])
    timestamp = bar_available(bar)

    if status == "PENDING":
        source_invalidation = float(order["sourceInvalidation"])
        if direction == "long":
            touched = ask_low <= entry
            fill_price = min(entry, ask_open)
            invalidated = source_close_due and bid_close <= source_invalidation
            objective_delivered = bid_high >= target
        else:
            touched = bid_high >= entry
            fill_price = max(entry, bid_open)
            invalidated = source_close_due and bid_close >= source_invalidation
            objective_delivered = bid_low <= target
        if objective_delivered and not touched:
            return {"type": "ORDER_CANCELLED", "reason": "OBJECTIVE_DELIVERED_BEFORE_FILL", "at": timestamp}
        if invalidated and not touched:
            return {"type": "ORDER_CANCELLED", "reason": "SOURCE_INVALIDATED_BEFORE_FILL", "at": timestamp}
        if not touched:
            return None
        if direction == "long":
            stop_hit = bid_low <= stop
            target_hit = bid_high >= target
        else:
            stop_hit = ask_high >= stop
            target_hit = ask_low <= target
        if stop_hit or target_hit:
            primary = "SL" if stop_hit else "TP"
            ambiguous = stop_hit and target_hit or stop_hit
            return {
                "type": "ORDER_FILLED_AND_CLOSED",
                "at": timestamp,
                "result": primary,
                "ambiguous": ambiguous,
                "bestCase": "TP" if target_hit else primary,
                "entrySpread": spread,
                "fillPrice": fill_price,
            }
        return {
            "type": "ORDER_FILLED",
            "at": timestamp,
            "entrySpread": spread,
            "fillPrice": fill_price,
        }

    if status == "OPEN":
        if direction == "long":
            stop_hit = bid_low <= stop
            target_hit = bid_high >= target
        else:
            stop_hit = ask_high >= stop
            target_hit = ask_low <= target
        if not stop_hit and not target_hit:
            return None
        if stop_hit and target_hit:
            return {"type": "POSITION_CLOSED", "at": timestamp, "result": "SL", "ambiguous": True, "bestCase": "TP"}
        return {"type": "POSITION_CLOSED", "at": timestamp, "result": "SL" if stop_hit else "TP", "ambiguous": False, "bestCase": "SL" if stop_hit else "TP"}
    return None


def process_order_until(state: dict[str, Any], rates: np.ndarray, stop_at: int) -> tuple[int | None, dict[str, Any] | None]:
    order = active_order(state)
    if order is None:
        return None, None
    start = int(state["viewerTime"])
    left = int(np.searchsorted(rates["time"], start, side="left"))
    right = int(np.searchsorted(rates["time"], stop_at, side="left"))
    for bar in rates[left:right]:
        source_timeframe = str(order.get("sourceTimeframe") or "M1")
        source_close_due = bar_available(bar) % TF_SECONDS[source_timeframe] == 0
        event = order_event_on_bar(order, bar, source_close_due=source_close_due)
        if event is not None:
            return int(event["at"]), event
    return None, None


def process_poi_until(state: dict[str, Any], rates: np.ndarray, stop_at: int) -> int | None:
    poi = state.get("activePoi")
    if not poi or poi.get("touchedAt") is not None:
        return None
    start = int(state["viewerTime"])
    left = int(np.searchsorted(rates["time"], start, side="left"))
    right = int(np.searchsorted(rates["time"], stop_at, side="left"))
    low = float(poi["low"])
    high = float(poi["high"])
    for bar in rates[left:right]:
        if float(bar["high"]) >= low and float(bar["low"]) <= high:
            return bar_available(bar)
    return None


def manual_watches(state: dict[str, Any]) -> list[dict[str, Any]]:
    watches = state.get("manualWatches")
    if isinstance(watches, list):
        return watches
    legacy = state.get("manualWatch")
    return [legacy] if isinstance(legacy, dict) else []


def process_manual_watches_until(
    state: dict[str, Any],
    rates: np.ndarray,
    stop_at: int,
) -> tuple[int | None, list[dict[str, Any]]]:
    watches = manual_watches(state)
    if not watches:
        return None, []
    start = int(state["viewerTime"])
    left = int(np.searchsorted(rates["time"], start, side="left"))
    right = int(np.searchsorted(rates["time"], stop_at, side="left"))
    first_at: int | None = None
    triggered: list[dict[str, Any]] = []
    for bar in rates[left:right]:
        available = bar_available(bar)
        hits = [
            watch for watch in watches
            if float(bar["high"]) >= float(watch["low"])
            and float(bar["low"]) <= float(watch["high"])
        ]
        if hits:
            first_at = available
            triggered = hits
            break
    return first_at, triggered


def apply_poi_and_watch_events(
    state: dict[str, Any],
    destination: int,
    poi_at: int | None,
    watch_at: int | None,
    triggered_watches: list[dict[str, Any]],
) -> None:
    if poi_at == destination:
        poi = state.get("activePoi")
        if not poi:
            raise AssertionError("POI touch event without an active POI")
        poi["touchedAt"] = iso(destination)
        append_execution({"event": "MANUAL_POI_TOUCHED", "at": iso(destination), "poi": poi})
    if watch_at != destination:
        return
    triggered_ids = {watch["id"] for watch in triggered_watches}
    state["manualWatches"] = [
        watch for watch in manual_watches(state)
        if watch.get("id") not in triggered_ids
    ]
    state.pop("manualWatch", None)
    review_watches = [
        watch for watch in triggered_watches
        if watch.get("mode", "REVIEW") == "REVIEW"
    ]
    if review_watches:
        state["manualMicroReview"] = {
            "triggeredAt": iso(destination),
            "watches": review_watches,
        }
    for watch in triggered_watches:
        append_execution({"event": "MANUAL_WATCH_TRIGGERED", "at": iso(destination), "watch": watch})


def apply_order_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    order = active_order(state)
    if order is None:
        raise AssertionError("Execution event without active order")
    event_record = {"orderId": order["orderId"], "event": event["type"], "at": iso(event["at"])}
    event_record.update({key: value for key, value in event.items() if key not in {"type", "at"}})
    if event["type"] == "ORDER_FILLED":
        order["status"] = "OPEN"
        order["filledAt"] = iso(event["at"])
        order["entrySpread"] = event["entrySpread"]
        order["fillPrice"] = event["fillPrice"]
    elif event["type"] == "ORDER_FILLED_AND_CLOSED":
        order["status"] = "CLOSED"
        order["filledAt"] = iso(event["at"])
        order["closedAt"] = iso(event["at"])
        order["result"] = event["result"]
        order["ambiguous"] = event["ambiguous"]
        order["bestCase"] = event["bestCase"]
        order["entrySpread"] = event["entrySpread"]
        order["fillPrice"] = event["fillPrice"]
        state["activeOrder"] = None
    elif event["type"] == "POSITION_CLOSED":
        order["status"] = "CLOSED"
        order["closedAt"] = iso(event["at"])
        order["result"] = event["result"]
        order["ambiguous"] = event["ambiguous"]
        order["bestCase"] = event["bestCase"]
        state["activeOrder"] = None
    elif event["type"] == "ORDER_CANCELLED":
        order["status"] = "CANCELLED"
        order["closedAt"] = iso(event["at"])
        order["cancelReason"] = event["reason"]
        state["activeOrder"] = None
    append_execution(event_record)


def recent_closed_view(series: dict[str, np.ndarray], cutoff: int) -> dict[str, list[dict[str, Any]]]:
    """Return only already-available raw bars for the manual reviewer."""
    counts = {"H4": 2, "H1": 2, "M15": 4, "M5": 12}
    result: dict[str, list[dict[str, Any]]] = {}
    for timeframe, count in counts.items():
        values = series[timeframe]
        right = int(np.searchsorted(values["available"], cutoff, side="right"))
        result[timeframe] = [
            {
                "time": iso(int(bar["time"])),
                "available": iso(int(bar["available"])),
                "open": float(bar["open"]),
                "high": float(bar["high"]),
                "low": float(bar["low"]),
                "close": float(bar["close"]),
            }
            for bar in values[max(0, right - count):right]
        ]
    return result


def command_next(args: argparse.Namespace) -> int:
    _, state, rates, series = require_workspace()
    require_replay_unlocked(state)
    expected = expected_h1_times(series)
    require_current_h1_reviewed(state, expected)
    current = int(state["viewerTime"])
    next_h1 = next_h1_after(expected, current)
    if next_h1 is None:
        if active_order(state) is None:
            print("Q1 H1 review boundary reached; no active order.")
            return 0
        stop_at = OBSERVE_TO
    else:
        stop_at = next_h1

    # A touched POI or triggered secondary watch enters an explicit M1 review
    # state. It remains active until the reviewer records an order/no-trade or
    # clears the watch, so a later CHoCH/FVG cannot be skipped accidentally.
    poi_review_step = None
    active_poi = state.get("activePoi")
    manual_micro_review = state.get("manualMicroReview")
    if (
        active_order(state) is None
        and (
            (active_poi and active_poi.get("touchedAt") is not None)
            or manual_micro_review
        )
        and current < stop_at
    ):
        poi_review_step = min(current + 60, stop_at)
        stop_at = poi_review_step

    order_at, event = process_order_until(state, rates, stop_at)
    poi_at = process_poi_until(state, rates, stop_at)
    watch_at, triggered_watches = process_manual_watches_until(state, rates, stop_at)
    targets = [item for item in (order_at, poi_at, watch_at, stop_at) if item is not None]
    destination = min(targets)
    state["viewerTime"] = destination
    state["maxRevealedTime"] = max(int(state["maxRevealedTime"]), destination)
    if order_at == destination and event is not None:
        apply_order_event(state, event)
    apply_poi_and_watch_events(state, destination, poi_at, watch_at, triggered_watches)
    save_json(STATE, state)
    if poi_review_step != destination:
        render_raw(series, destination, CURRENT_CHART)
    write_progress(state, expected)
    stopped_for = (
        "ORDER_EVENT"
        if order_at == destination
        else "POI_TOUCH"
        if poi_at == destination
        else "MANUAL_WATCH"
        if watch_at == destination
        else "POI_REVIEW"
        if poi_review_step == destination
        else "H1_CLOSE"
    )
    payload = {
        "viewerTime": iso(destination),
        "stoppedFor": stopped_for,
        "activeOrder": state.get("activeOrder"),
        "activePoi": state.get("activePoi"),
    }
    recent = recent_closed_view(series, destination)
    if args.micro:
        if payload["activePoi"]:
            poi = payload["activePoi"]
            payload["activePoi"] = {
                "low": poi["low"],
                "high": poi["high"],
                "direction": poi["direction"],
                "label": poi["label"],
                "declaredAt": poi.get("declaredAt"),
                "touchedAt": poi.get("touchedAt"),
            }
        latest_h1 = recent["H1"][-1] if recent["H1"] else None
        latest_h4 = recent["H4"][-1] if recent["H4"] else None
        payload["latestH1"] = latest_h1
        payload["newH4Close"] = (
            latest_h4
            if latest_h4 is not None and latest_h4["available"] == iso(destination)
            else None
        )
        right = int(np.searchsorted(rates["time"], destination, side="left"))
        if right:
            bar = rates[right - 1]
            payload["latestM1"] = {
                "time": iso(int(bar["time"])),
                "open": float(bar["open"]),
                "high": float(bar["high"]),
                "low": float(bar["low"]),
                "close": float(bar["close"]),
                "spread": int(bar["spread"]),
            }
    else:
        payload["recentClosed"] = (
            {"H4": recent["H4"], "H1": recent["H1"]}
            if args.compact
            else recent
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_set_watch(args: argparse.Namespace) -> int:
    _, state, _, series = require_workspace()
    expected = expected_h1_times(series)
    require_current_h1_reviewed(state, expected)
    if active_order(state) is not None:
        raise SystemExit("Cannot set a manual review watch while an order is active.")
    if args.low > args.high:
        raise SystemExit("Watch low must be <= watch high.")
    watches = manual_watches(state)
    duplicate = next((
        item for item in watches
        if abs(float(item["low"]) - float(args.low)) <= POINT
        and abs(float(item["high"]) - float(args.high)) <= POINT
        and item.get("mode") == args.mode
    ), None)
    if duplicate is not None:
        print(json.dumps(duplicate, ensure_ascii=False, indent=2))
        return 0
    watch = {
        "id": f"W{len(read_jsonl(EXECUTION_LEDGER)) + 1:04d}",
        "low": float(args.low),
        "high": float(args.high),
        "reason": args.reason,
        "mode": args.mode,
        "setAt": iso(int(state["viewerTime"])),
        "suspendMicro": bool(args.suspend_micro),
    }
    state["manualWatches"] = [*watches, watch]
    state.pop("manualWatch", None)
    append_execution({"event": "MANUAL_WATCH_SET", "at": watch["setAt"], "watch": watch})
    save_json(STATE, state)
    write_progress(state, expected)
    print(json.dumps(watch, ensure_ascii=False, indent=2))
    return 0


def command_clear_watch(args: argparse.Namespace) -> int:
    _, state, _, series = require_workspace()
    expected = expected_h1_times(series)
    require_current_h1_reviewed(state, expected)
    watches = manual_watches(state)
    state.pop("manualWatch", None)
    if args.keep_pending:
        deduplicated: list[dict[str, Any]] = []
        for watch in watches:
            if not any(
                abs(float(existing["low"]) - float(watch["low"])) <= POINT
                and abs(float(existing["high"]) - float(watch["high"])) <= POINT
                and existing.get("mode") == watch.get("mode")
                for existing in deduplicated
            ):
                deduplicated.append(watch)
        state["manualWatches"] = deduplicated
    else:
        deduplicated = []
        state["manualWatches"] = []
    micro_review = state.pop("manualMicroReview", None)
    if not args.keep_pending:
        for watch in watches:
            append_execution({
                "event": "MANUAL_WATCH_CLEARED",
                "at": iso(int(state["viewerTime"])),
                "watch": watch,
            })
    if micro_review is not None:
        append_execution({
            "event": "MANUAL_MICRO_REVIEW_CLEARED",
            "at": iso(int(state["viewerTime"])),
            "review": micro_review,
        })
    save_json(STATE, state)
    write_progress(state, expected)
    print(json.dumps({
        "clearedWatches": [] if args.keep_pending else watches,
        "remainingWatches": deduplicated if args.keep_pending else [],
        "clearedMicroReview": micro_review,
    }, ensure_ascii=False, indent=2))
    return 0


def command_clear_error_lock(args: argparse.Namespace) -> int:
    _, state, _, series = require_workspace()
    lock = state.get("recordingErrorLock")
    if not lock:
        print(json.dumps({"cleared": False, "reason": "No recording error lock is active."}, ensure_ascii=False))
        return 0
    incident = append_chain(
        INCIDENT_LEDGER,
        {
            "schema": "manual-replay-incident-v1",
            "at": iso(int(state["viewerTime"])),
            "type": "ORDER_RECORDING_ABANDONED",
            "recordingErrorLock": lock,
            "reason": args.reason,
            "futureExposure": "Replay remained frozen until this explicit acknowledgement.",
        },
    )
    clear_recording_error_lock(state)
    save_json(STATE, state)
    write_progress(state, expected_h1_times(series))
    print(json.dumps({"cleared": True, "incident": incident}, ensure_ascii=False, indent=2))
    return 0


def command_carry_next(args: argparse.Namespace) -> int:
    """Seal an unchanged H1 review, then reveal exactly one next H1 close."""
    _, state, _, _ = require_workspace()
    require_replay_unlocked(state)
    command_record_map(argparse.Namespace(
        carry=True,
        decision=args.decision,
        reason=args.reason,
        quiet=True,
    ))
    return command_next(argparse.Namespace(compact=False, micro=True))


def command_step(args: argparse.Namespace) -> int:
    _, state, rates, series = require_workspace()
    require_replay_unlocked(state)
    expected = expected_h1_times(series)
    require_current_h1_reviewed(state, expected)
    current = int(state["viewerTime"])
    next_h1 = next_h1_after(expected, current)
    requested = current + args.minutes * 60
    stop_at = min(requested, next_h1 or requested, OBSERVE_TO)
    active_poi = state.get("activePoi")
    if (
        active_order(state) is None
        and (
            (active_poi and active_poi.get("touchedAt") is not None)
            or state.get("manualMicroReview")
        )
    ):
        stop_at = min(stop_at, current + 60)
    order_at, event = process_order_until(state, rates, stop_at)
    poi_at = process_poi_until(state, rates, stop_at)
    watch_at, triggered_watches = process_manual_watches_until(state, rates, stop_at)
    destination = min(
        item for item in (order_at, poi_at, watch_at, stop_at)
        if item is not None
    )
    state["viewerTime"] = destination
    state["maxRevealedTime"] = max(int(state["maxRevealedTime"]), destination)
    if event is not None and order_at == destination:
        apply_order_event(state, event)
    apply_poi_and_watch_events(state, destination, poi_at, watch_at, triggered_watches)
    save_json(STATE, state)
    render_raw(series, destination, CURRENT_CHART)
    write_progress(state, expected)
    payload = {
        "viewerTime": iso(destination),
        "stoppedFor": (
            "ORDER_EVENT"
            if event is not None and order_at == destination
            else "POI_TOUCH"
            if poi_at == destination
            else "MANUAL_WATCH"
            if watch_at == destination
            else "MICRO_REVIEW"
            if destination < requested
            else "MANUAL_STEP"
        ),
    }
    if getattr(args, "micro", False):
        right = int(np.searchsorted(rates["time"], destination, side="left"))
        if right:
            bar = rates[right - 1]
            payload["latestM1"] = {
                "time": iso(int(bar["time"])),
                "open": float(bar["open"]),
                "high": float(bar["high"]),
                "low": float(bar["low"]),
                "close": float(bar["close"]),
                "spread": int(bar["spread"]),
            }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def command_render(_: argparse.Namespace) -> int:
    _, state, _, series = require_workspace()
    render_raw(series, int(state["viewerTime"]), CURRENT_CHART)
    print(CURRENT_CHART)
    return 0


def command_zoom(args: argparse.Namespace) -> int:
    _, state, _, series = require_workspace()
    destination = OUTPUT / f"current_{args.timeframe.lower()}_zoom.png"
    render_zoom(series, int(state["viewerTime"]), args.timeframe, args.bars, destination)
    print(destination)
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    _, state, rates, series = require_workspace()
    cutoff = int(state["viewerTime"])
    rows: list[dict[str, Any]] = []
    if args.timeframe == "M1":
        right = int(np.searchsorted(rates["time"], cutoff, side="left"))
        values = rates[max(0, right - args.bars):right]
        for bar in values:
            rows.append({
                "time": iso(int(bar["time"])),
                "open": float(bar["open"]),
                "high": float(bar["high"]),
                "low": float(bar["low"]),
                "close": float(bar["close"]),
                "spread": int(bar["spread"]),
            })
    else:
        values = series[args.timeframe]
        right = int(np.searchsorted(values["available"], cutoff, side="right"))
        for bar in values[max(0, right - args.bars):right]:
            rows.append({
                "time": iso(int(bar["time"])),
                "available": iso(int(bar["available"])),
                "open": float(bar["open"]),
                "high": float(bar["high"]),
                "low": float(bar["low"]),
                "close": float(bar["close"]),
            })
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def command_record_map(args: argparse.Namespace) -> int:
    _, state, _, series = require_workspace()
    require_replay_unlocked(state)
    expected = expected_h1_times(series)
    as_of = getattr(args, "as_of", None)
    current = parse_time(as_of) if as_of else int(state["viewerTime"])
    if current > int(state["viewerTime"]):
        raise SystemExit("A recovered map cannot be recorded after the current replay clock.")
    if current not in expected:
        raise SystemExit("Map records can only be written at a Q1 H1 close.")
    if map_recorded_exactly_at(current):
        raise SystemExit(f"Map already recorded at {iso(current)}")
    previous = current_map(current)
    if args.carry:
        if previous is None:
            raise SystemExit("The first map record cannot use --carry.")
        fields = {key: previous.get(key) for key in ("externalStructure", "internalStructure", "dealingRangeLow", "dealingRangeHigh", "pdLocation", "objective", "opposingContext", "poi", "poiFamily", "invalidation")}
        fields["decision"] = args.decision
        fields["reason"] = args.reason
    else:
        required = (args.external, args.internal, args.pd, args.objective, args.context, args.decision, args.reason)
        if any(value is None for value in required):
            raise SystemExit("A changed map requires all descriptive fields.")
        poi_family = parse_poi_family(
            args.poi_family_json,
            current,
            series,
            args.poi_direction,
            args.poi_family_file,
        )
        poi = None
        if poi_family is not None:
            if args.poi_direction is None or args.poi_label is None:
                raise SystemExit("A POI family requires --poi-direction and --poi-label.")
            selected_id = getattr(args, "poi_selected_id", None)
            if STRICT_HTF_CAUSAL_MODE and selected_id != poi_family[-1]["id"]:
                raise SystemExit("Strict mentor replay requires --poi-selected-id to name the final causal refinement node.")
            selected_member = None
            if selected_id:
                selected_member = next((member for member in poi_family if member["id"] == selected_id), None)
                if selected_member is None:
                    raise SystemExit("--poi-selected-id must match a member of the declared family.")
            poi = {
                "low": float(selected_member["low"]) if selected_member else min(float(member["low"]) for member in poi_family),
                "high": float(selected_member["high"]) if selected_member else max(float(member["high"]) for member in poi_family),
                "direction": args.poi_direction,
                "label": args.poi_label,
                **({"selectedFamilyId": selected_id} if selected_id else {}),
            }
        elif args.poi_low is not None or args.poi_high is not None:
            if args.poi_low is None or args.poi_high is None or args.poi_low > args.poi_high:
                raise SystemExit("POI requires valid --poi-low and --poi-high bounds.")
            poi = {"low": args.poi_low, "high": args.poi_high, "direction": args.poi_direction, "label": args.poi_label}
        fields = {
            "externalStructure": args.external,
            "internalStructure": args.internal,
            "dealingRangeLow": args.range_low,
            "dealingRangeHigh": args.range_high,
            "pdLocation": args.pd,
            "objective": args.objective,
            "opposingContext": args.context,
            "poi": poi,
            "poiFamily": poi_family,
            "invalidation": args.invalidation,
            "decision": args.decision,
            "reason": args.reason,
        }
    record = {"schema": "manual-h1-map-v1", "asOf": iso(current), "manualReviewed": True, "stateChanged": not args.carry, **fields}
    sealed = append_chain(MAP_LEDGER, record)
    should_arm_poi = (
        not args.carry
        and sealed["decision"] == "WAIT_POI"
        and sealed["poi"] is not None
        and active_order(state) is None
    )
    if args.carry:
        if sealed["decision"] != "WAIT_POI":
            state["activePoi"] = None
            state.pop("manualWatch", None)
            state["manualWatches"] = []
            state.pop("manualMicroReview", None)
    elif should_arm_poi:
        existing_poi = state.get("activePoi")
        candidate = {
            **sealed["poi"],
            "family": sealed.get("poiFamily"),
            "declaredAt": sealed["asOf"],
            "touchedAt": None,
        }
        candidate["key"] = poi_key(candidate)
        resolved_keys = set(state.get("resolvedPoiKeys") or [])
        same_active_poi = (
            existing_poi is not None
            and existing_poi.get("key") == candidate["key"]
        )
        state["activePoi"] = (
            existing_poi
            if same_active_poi
            else None
            if candidate["key"] in resolved_keys
            else candidate
        )
    else:
        state["activePoi"] = None
    save_json(STATE, state)
    write_progress(state, expected)
    if not args.quiet:
        print(json.dumps(sealed, ensure_ascii=False, indent=2))
    return 0


def command_record_no_trade(args: argparse.Namespace) -> int:
    _, state, _, series = require_workspace()
    require_replay_unlocked(state)
    poi = state.get("activePoi")
    explicit_poi = args.poi_low is not None or args.poi_high is not None
    if explicit_poi:
        required = (args.poi_low, args.poi_high, args.poi_direction, args.poi_label, args.declared_at)
        if any(value is None for value in required) or args.poi_low > args.poi_high:
            raise SystemExit("An explicit POI closure requires valid bounds, direction, label, and declared time.")
        poi = {
            "low": args.poi_low,
            "high": args.poi_high,
            "direction": args.poi_direction,
            "label": args.poi_label,
            "declaredAt": iso(parse_time(args.declared_at)),
            "touchedAt": iso(parse_time(args.touched_at)) if args.touched_at else None,
        }
    if not poi:
        raise SystemExit("No active manually declared POI is available. Use explicit POI fields only for an append-only correction.")
    if args.supersedes and not args.correction_reason:
        raise SystemExit("--supersedes requires --correction-reason.")
    record_time = parse_time(args.as_of) if args.as_of else int(state["viewerTime"])
    record = {
        "schema": "manual-no-trade-v1",
        "asOf": iso(record_time),
        "poi": poi,
        "reason": args.reason,
        "observedLtf": args.observed_ltf,
        "manualDecision": "NO_TRADE",
    }
    if args.supersedes:
        record["supersedesEntryHash"] = args.supersedes
        record["correctionReason"] = args.correction_reason
    sealed = append_chain(NO_TRADE_LEDGER, record)
    if args.supersedes:
        append_chain(INCIDENT_LEDGER, {
            "schema": "manual-replay-incident-v1",
            "at": iso(int(state["viewerTime"])),
            "type": "NO_TRADE_POI_REFERENCE_ERROR",
            "supersededEntryHash": args.supersedes,
            "correctedEntryHash": sealed["entryHash"],
            "reason": args.correction_reason,
            "futureExposure": "None; replay time and market decisions were unchanged.",
        })
    if getattr(args, "keep_poi", False):
        if state.get("activePoi") is not None:
            state["activePoi"]["touchedAt"] = None
        state.pop("manualMicroReview", None)
    else:
        resolved_keys = set(state.get("resolvedPoiKeys") or [])
        resolved_keys.add(poi.get("key") or poi_key(poi))
        state["resolvedPoiKeys"] = sorted(resolved_keys)
        state["activePoi"] = None
        state.pop("manualWatch", None)
        state["manualWatches"] = []
        state.pop("manualMicroReview", None)
    save_json(STATE, state)
    write_progress(state, expected_h1_times(series))
    print(json.dumps(sealed, ensure_ascii=False, indent=2))
    return 0


def command_declare_poi(args: argparse.Namespace) -> int:
    _, state, _, series = require_workspace()
    expected = expected_h1_times(series)
    require_current_h1_reviewed(state, expected)
    if active_order(state) is not None:
        raise SystemExit("Cannot declare a new POI while an order is active.")
    current = int(state["viewerTime"])
    family = parse_poi_family(
        args.poi_family_json,
        current,
        series,
        args.poi_direction,
        args.poi_family_file,
    )
    if not family:
        raise SystemExit("An intrahour POI declaration requires a non-empty causal family.")
    selected_member = None
    if STRICT_HTF_CAUSAL_MODE and args.poi_selected_id != family[-1]["id"]:
        raise SystemExit("Strict mentor replay requires --poi-selected-id to name the final causal refinement node.")
    if args.poi_selected_id:
        selected_member = next((member for member in family if member["id"] == args.poi_selected_id), None)
        if selected_member is None:
            raise SystemExit("--poi-selected-id must match a member of the declared family.")
    poi = {
        "low": float(selected_member["low"]) if selected_member else min(float(member["low"]) for member in family),
        "high": float(selected_member["high"]) if selected_member else max(float(member["high"]) for member in family),
        "direction": args.poi_direction,
        "label": args.poi_label,
        **({"selectedFamilyId": args.poi_selected_id} if args.poi_selected_id else {}),
        "family": family,
        "declaredAt": iso(current),
        "touchedAt": None,
    }
    poi["key"] = poi_key(poi)
    if poi["key"] in set(state.get("resolvedPoiKeys") or []):
        raise SystemExit(
            "This physical POI was already resolved. Declare a new causal family id "
            "for a genuinely new liquidity-to-trigger chain."
        )
    sealed = append_chain(POI_LEDGER, {
        "schema": "manual-poi-declaration-v1",
        "at": iso(current),
        "poi": poi,
        "invalidation": args.invalidation,
        "reason": args.reason,
    })
    state["activePoi"] = poi
    save_json(STATE, state)
    append_execution({"event": "MANUAL_POI_DECLARED", "at": iso(current), "poiHash": sealed["entryHash"], "poi": poi})
    write_progress(state, expected)
    print(json.dumps(sealed, ensure_ascii=False, indent=2))
    return 0


def command_record_order(args: argparse.Namespace) -> int:
    _, state, rates, series = require_workspace()
    if active_order(state) is not None:
        raise SystemExit("Only one pending order or open position is allowed.")
    current = int(state["viewerTime"])
    if current >= Q1_TO:
        raise SystemExit("New Q1 entries are closed after 2025-03-31 23:59 UTC.")
    if args.direction == "long" and not (args.stop < args.entry < args.target):
        raise SystemExit("Long geometry must satisfy SL < entry < TP.")
    if args.direction == "short" and not (args.target < args.entry < args.stop):
        raise SystemExit("Short geometry must satisfy TP < entry < SL.")
    order_number = len(read_jsonl(ORDER_LEDGER)) + 1
    order_id = f"Q1M{order_number:03d}"
    causal_contract = causal_order_contract(args, current)
    if causal_contract:
        require_structural_stop(args, rates, current)
    record = {
        "schema": "manual-causal-order-v3" if causal_contract else "manual-order-v1",
        "orderId": order_id,
        "decisionAt": iso(current),
        "direction": args.direction,
        "scope": args.scope,
        "mapTimeframe": args.map_tf,
        "sourceTimeframe": args.source_tf,
        "triggerTimeframe": args.trigger_tf,
        "map": args.map,
        "sourceLiquidity": args.source_liquidity,
        "sourceZone": {
            "label": args.source_zone_label,
            "low": args.source_zone_low,
            "high": args.source_zone_high,
            **({
                "type": causal_contract["sourceZone"]["type"],
                "formedAt": causal_contract["sourceZone"]["formedAt"],
                "originCandles": causal_contract["sourceZone"]["originCandles"],
            } if causal_contract else {}),
        },
        "sweep": {"description": args.sweep, "extreme": args.sweep_extreme, **({"at": causal_contract["sweepAt"]} if causal_contract else {})},
        "choch": {"description": args.choch, "level": args.choch_level, **({"at": causal_contract["chochAt"]} if causal_contract else {})},
        "entryZone": {
            "label": args.entry_zone_label,
            "low": args.entry_zone_low,
            "high": args.entry_zone_high,
            **({
                "type": causal_contract["entryZone"]["type"],
                "formedAt": causal_contract["entryZone"]["formedAt"],
                "originCandles": causal_contract["entryZone"]["originCandles"],
                "ownedBy": causal_contract["entryZone"]["ownedBy"],
            } if causal_contract else {}),
        },
        "entry": args.entry,
        "stopLoss": args.stop,
        "takeProfit": args.target,
        "sourceInvalidation": args.source_invalidation,
        "objective": args.objective,
        "reason": args.reason,
        "riskUnit": "1R",
        **({"causalLineage": causal_contract} if causal_contract else {}),
    }
    semantic_audit = require_semantic_order(record, series) if causal_contract else None
    if semantic_audit:
        record["semanticValidation"] = {
            "schema": semantic_audit["schema"],
            "valid": True,
            "performanceEligible": True,
            "failureCodes": [],
        }
    sealed = append_chain(ORDER_LEDGER, record)
    state["activeOrder"] = {
        "orderId": order_id,
        "decisionAt": sealed["decisionAt"],
        "direction": args.direction,
        "entry": args.entry,
        "stopLoss": args.stop,
        "takeProfit": args.target,
        "sourceInvalidation": args.source_invalidation,
        "sourceTimeframe": args.source_tf,
        "status": "PENDING",
    }
    active_poi = state.get("activePoi")
    if active_poi:
        resolved_keys = set(state.get("resolvedPoiKeys") or [])
        resolved_keys.add(active_poi.get("key") or poi_key(active_poi))
        state["resolvedPoiKeys"] = sorted(resolved_keys)
    state["activePoi"] = None
    state.pop("manualWatch", None)
    state["manualWatches"] = []
    state.pop("manualMicroReview", None)
    clear_recording_error_lock(state)
    save_json(STATE, state)
    render_raw(series, current, OUTPUT / "entry_charts" / f"{order_id}_asof.png")
    append_execution({"orderId": order_id, "event": "ORDER_FROZEN", "at": iso(current), "orderHash": sealed["entryHash"]})
    write_progress(state, expected_h1_times(series))
    print(json.dumps(sealed, ensure_ascii=False, indent=2))
    return 0


def command_recover_order(args: argparse.Namespace) -> int:
    """Recover a manually frozen order after a recorder-only CLI failure."""
    _, state, rates, series = require_workspace()
    if active_order(state) is not None:
        raise SystemExit("Only one pending order or open position is allowed.")
    recorded_at = int(state["viewerTime"])
    decision_at = parse_time(args.decision_at)
    if not (Q1_FROM <= decision_at < recorded_at):
        raise SystemExit("Recovery decision time must be inside Q1 and before the current replay clock.")
    if not map_recorded_at(decision_at):
        raise SystemExit("Recovery requires an existing manual H1 map at the original decision time.")
    if args.direction == "long" and not (args.stop < args.entry < args.target):
        raise SystemExit("Long geometry must satisfy SL < entry < TP.")
    if args.direction == "short" and not (args.target < args.entry < args.stop):
        raise SystemExit("Short geometry must satisfy TP < entry < SL.")

    order_number = len(read_jsonl(ORDER_LEDGER)) + 1
    order_id = f"Q1M{order_number:03d}"
    causal_contract = causal_order_contract(args, decision_at)
    if causal_contract:
        require_structural_stop(args, rates, decision_at)
    record = {
        "schema": "manual-causal-order-v3" if causal_contract else "manual-order-v1",
        "orderId": order_id,
        "decisionAt": iso(decision_at),
        "direction": args.direction,
        "scope": args.scope,
        "mapTimeframe": args.map_tf,
        "sourceTimeframe": args.source_tf,
        "triggerTimeframe": args.trigger_tf,
        "map": args.map,
        "sourceLiquidity": args.source_liquidity,
        "sourceZone": {
            "label": args.source_zone_label,
            "low": args.source_zone_low,
            "high": args.source_zone_high,
            **({
                "type": causal_contract["sourceZone"]["type"],
                "formedAt": causal_contract["sourceZone"]["formedAt"],
                "originCandles": causal_contract["sourceZone"]["originCandles"],
            } if causal_contract else {}),
        },
        "sweep": {"description": args.sweep, "extreme": args.sweep_extreme, **({"at": causal_contract["sweepAt"]} if causal_contract else {})},
        "choch": {"description": args.choch, "level": args.choch_level, **({"at": causal_contract["chochAt"]} if causal_contract else {})},
        "entryZone": {
            "label": args.entry_zone_label,
            "low": args.entry_zone_low,
            "high": args.entry_zone_high,
            **({
                "type": causal_contract["entryZone"]["type"],
                "formedAt": causal_contract["entryZone"]["formedAt"],
                "originCandles": causal_contract["entryZone"]["originCandles"],
                "ownedBy": causal_contract["entryZone"]["ownedBy"],
            } if causal_contract else {}),
        },
        "entry": args.entry,
        "stopLoss": args.stop,
        "takeProfit": args.target,
        "sourceInvalidation": args.source_invalidation,
        "objective": args.objective,
        "reason": args.reason,
        "riskUnit": "1R",
        **({"causalLineage": causal_contract} if causal_contract else {}),
        "recordingRecovery": {"recordedAt": iso(recorded_at), "incident": args.incident},
    }
    semantic_audit = require_semantic_order(record, series) if causal_contract else None
    if semantic_audit:
        record["semanticValidation"] = {
            "schema": semantic_audit["schema"],
            "valid": True,
            "performanceEligible": True,
            "failureCodes": [],
        }
    sealed = append_chain(ORDER_LEDGER, record)
    replay_state = dict(state)
    replay_state["viewerTime"] = decision_at
    replay_state["activeOrder"] = {
        "orderId": order_id,
        "decisionAt": sealed["decisionAt"],
        "direction": args.direction,
        "entry": args.entry,
        "stopLoss": args.stop,
        "takeProfit": args.target,
        "sourceInvalidation": args.source_invalidation,
        "sourceTimeframe": args.source_tf,
        "status": "PENDING",
    }
    append_execution({
        "orderId": order_id,
        "event": "ORDER_FROZEN",
        "at": iso(decision_at),
        "orderHash": sealed["entryHash"],
        "recordingRecovery": True,
    })
    while active_order(replay_state) is not None:
        event_at, event = process_order_until(replay_state, rates, recorded_at)
        if event_at is None or event is None:
            break
        replay_state["viewerTime"] = event_at
        apply_order_event(replay_state, event)
    state["activeOrder"] = replay_state.get("activeOrder")
    state["activePoi"] = None
    clear_recording_error_lock(state)
    save_json(STATE, state)
    render_raw(series, decision_at, OUTPUT / "entry_charts" / f"{order_id}_asof.png")
    incident = append_chain(INCIDENT_LEDGER, {
        "schema": "manual-replay-incident-v1",
        "at": iso(recorded_at),
        "originalDecisionAt": iso(decision_at),
        "orderId": order_id,
        "reason": args.incident,
        "evidence": "The manual H1 map was hash-sealed at the decision time before the recorder command failed.",
        "futureExposure": f"Replay advanced from {iso(decision_at)} to {iso(recorded_at)} before recovery.",
    })
    write_progress(state, expected_h1_times(series))
    print(json.dumps({"order": sealed, "incident": incident, "activeOrder": state.get("activeOrder")}, ensure_ascii=False, indent=2))
    return 0


def command_supersede_cancellation(args: argparse.Namespace) -> int:
    """Restore an order cancelled by a recorder-only semantic defect."""
    _, state, rates, series = require_workspace()
    if active_order(state) is not None:
        raise SystemExit("Cannot supersede a cancellation while another order is active.")
    orders = {str(item["orderId"]): item for item in read_jsonl(ORDER_LEDGER)}
    order = orders.get(args.order_id)
    if order is None:
        raise SystemExit(f"Unknown order: {args.order_id}")
    events = [
        item for item in read_jsonl(EXECUTION_LEDGER)
        if str(item.get("orderId") or "") == args.order_id
    ]
    if not events or events[-1].get("event") != "ORDER_CANCELLED":
        raise SystemExit("The latest order event is not a cancellation.")
    cancelled_at = parse_time(str(events[-1]["at"]))
    current = int(state["viewerTime"])
    if cancelled_at != current:
        raise SystemExit("Cancellation repair is only allowed at the unchanged replay clock.")

    restored = {
        "orderId": args.order_id,
        "decisionAt": order["decisionAt"],
        "direction": order["direction"],
        "entry": float(order["entry"]),
        "stopLoss": float(order["stopLoss"]),
        "takeProfit": float(order["takeProfit"]),
        "sourceInvalidation": float(order["sourceInvalidation"]),
        "sourceTimeframe": str(order["sourceTimeframe"]),
        "status": "PENDING",
    }
    append_execution({
        "orderId": args.order_id,
        "event": "ORDER_CANCELLATION_SUPERSEDED",
        "at": iso(current),
        "supersededEventHash": events[-1]["entryHash"],
        "reason": args.reason,
    })
    state["activeOrder"] = restored

    index = int(np.searchsorted(rates["time"], current - 60, side="left"))
    if index >= len(rates) or bar_available(rates[index]) != current:
        raise SystemExit("Cannot locate the M1 bar that produced the cancelled event.")
    source_close_due = current % TF_SECONDS[restored["sourceTimeframe"]] == 0
    corrected_event = order_event_on_bar(
        restored,
        rates[index],
        source_close_due=source_close_due,
    )
    if corrected_event is not None:
        apply_order_event(state, corrected_event)
    save_json(STATE, state)
    render_raw(series, current, CURRENT_CHART)
    write_progress(state, expected_h1_times(series))
    print(json.dumps({
        "orderId": args.order_id,
        "supersededAt": iso(current),
        "correctedEvent": corrected_event,
        "activeOrder": state.get("activeOrder"),
    }, ensure_ascii=False, indent=2))
    return 0


def verify_chain(path: Path) -> list[str]:
    errors: list[str] = []
    previous = ZERO_HASH
    for line_number, row in enumerate(read_jsonl(path), start=1):
        stored = row.get("entryHash")
        if row.get("previousHash") != previous:
            errors.append(f"{path.name}:{line_number}: previous hash mismatch")
        payload = {key: value for key, value in row.items() if key != "entryHash"}
        expected = hashlib.sha256(previous.encode("ascii") + canonical(payload)).hexdigest()
        if stored != expected:
            errors.append(f"{path.name}:{line_number}: entry hash mismatch")
        previous = stored or previous
    return errors


def command_audit(_: argparse.Namespace) -> int:
    manifest, state, _, series = require_workspace()
    errors: list[str] = []
    for path in (MAP_LEDGER, ORDER_LEDGER, EXECUTION_LEDGER, NO_TRADE_LEDGER, INCIDENT_LEDGER):
        errors.extend(verify_chain(path))
    expected = expected_h1_times(series)
    maps = read_jsonl(MAP_LEDGER)
    actual = [parse_time(item["asOf"]) for item in maps]
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    duplicates = len(actual) - len(set(actual))
    orders = read_jsonl(ORDER_LEDGER)
    semantic_audits = [
        validate_order_semantics(order, series, POINT)
        for order in orders
    ]
    semantic_summary = summarize_semantic_audits(semantic_audits)
    save_json(SEMANTIC_AUDIT, semantic_summary)
    save_json(
        SEMANTIC_ELIGIBILITY,
        {
            "schema": "mentor-semantic-trade-eligibility-v1",
            "orders": [
                {
                    "orderId": audit["orderId"],
                    "performanceEligible": audit["performanceEligible"],
                    "failureCodes": audit["failureCodes"],
                    "failureReasons": audit["failureReasons"],
                }
                for audit in semantic_audits
            ],
        },
    )
    eligibility = load_json(BASELINE_ELIGIBILITY) if BASELINE_ELIGIBILITY.exists() else {}
    eligibility_by_order = {
        item.get("orderId"): item
        for item in eligibility.get("orders", [])
        if item.get("orderId")
    }
    causal_proof = load_json(CAUSAL_PROOF) if CAUSAL_PROOF.exists() else {}
    proof_by_order = {
        item.get("orderId"): item
        for item in causal_proof.get("orders", [])
        if item.get("orderId")
    }
    protocol_violations: list[str] = []
    unresolved_protocol_violations: list[str] = []
    for order in orders:
        order_id = str(order.get("orderId") or "UNKNOWN")
        proof = proof_by_order.get(order_id) or {}
        if proof:
            if proof.get("sourceOrderHash") != order.get("entryHash"):
                errors.append(f"{order_id}: causal proof source hash mismatch")
                proof = {}
            elif proof.get("decisionAt") != order.get("decisionAt"):
                errors.append(f"{order_id}: causal proof decision time mismatch")
                proof = {}
        sweep_value = (order.get("sweep") or {}).get("at") or proof.get("sweepAt")
        choch_value = (order.get("choch") or {}).get("at") or proof.get("chochAt")
        if not sweep_value or not choch_value or parse_time(sweep_value) >= parse_time(choch_value):
            protocol_violations.append(order_id)
            classification = eligibility_by_order.get(order_id) or {}
            if classification.get("baselineEligible") is not False:
                unresolved_protocol_violations.append(order_id)
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden_references = [value for value in manifest["forbiddenDecisionInputs"] if value in source]
    # The literal names are present in the manifest and audit code itself. Only
    # imports and reads from those sources are forbidden.
    forbidden_imports = [line for line in source.splitlines() if line.startswith(("from mentor_engine", "import mentor_engine"))]
    if missing:
        errors.append(f"missing H1 reviews: {len(missing)}")
    if unexpected:
        errors.append(f"unexpected H1 reviews: {len(unexpected)}")
    if duplicates:
        errors.append(f"duplicate H1 reviews: {duplicates}")
    if forbidden_imports:
        errors.append(f"forbidden decision imports: {forbidden_imports}")
    if unresolved_protocol_violations:
        errors.append(
            "orders without a separate post-sweep CHoCH and no baseline exclusion: "
            + ", ".join(unresolved_protocol_violations)
        )
    if semantic_summary["invalidOrders"]:
        errors.append(
            f"orders with unverified semantic evidence: {semantic_summary['invalidOrders']}"
        )
    if int(state["maxRevealedTime"]) < int(state["viewerTime"]):
        errors.append("viewer time exceeds max revealed time")
    result = {
        "ok": not errors,
        "expectedH1Reviews": len(expected),
        "actualH1Reviews": len(actual),
        "missingH1Reviews": len(missing),
        "unexpectedH1Reviews": len(unexpected),
        "duplicates": duplicates,
        "rawProtocolViolations": protocol_violations,
        "unresolvedProtocolViolations": unresolved_protocol_violations,
        "baselineExcludedOrders": sorted(
            order_id
            for order_id, item in eligibility_by_order.items()
            if item.get("baselineEligible") is False
        ),
        "causalProofOrders": sorted(proof_by_order),
        "semanticEvidence": {
            "validOrders": semantic_summary["validOrders"],
            "invalidOrders": semantic_summary["invalidOrders"],
            "elementCounts": semantic_summary["elementCounts"],
            "failureCounts": semantic_summary["failureCounts"],
        },
        "activeOrder": state.get("activeOrder"),
        "forbiddenImports": forbidden_imports,
        "forbiddenNamesDocumented": forbidden_references,
        "errors": errors,
    }
    save_json(OUTPUT / "audit.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


def write_progress(state: dict[str, Any], expected: list[int]) -> None:
    maps = read_jsonl(MAP_LEDGER)
    orders = read_jsonl(ORDER_LEDGER)
    executions = read_jsonl(EXECUTION_LEDGER)
    no_trades = read_jsonl(NO_TRADE_LEDGER)
    eligibility = load_json(BASELINE_ELIGIBILITY) if BASELINE_ELIGIBILITY.exists() else None
    eligible_count = None
    excluded_count = None
    if eligibility:
        classifications = eligibility.get("orders") or []
        eligible_count = sum(1 for item in classifications if item.get("baselineEligible") is True)
        excluded_count = sum(1 for item in classifications if item.get("baselineEligible") is False)
    completed = len(maps)
    percent = 100.0 * completed / len(expected) if expected else 0.0
    lines = [
        "# Q1 Mentor Blind Manual Ground Truth Progress",
        "",
        f"- Replay clock: `{iso(int(state['viewerTime']))}`",
        f"- Maximum revealed time: `{iso(int(state['maxRevealedTime']))}`",
        f"- H1 reviews: `{completed} / {len(expected)}` (`{percent:.2f}%`)",
        f"- Manual orders frozen: `{len(orders)}`",
        *(
            [f"- Corrected OB-refinement baseline: `{eligible_count} eligible / {excluded_count} excluded`"]
            if eligible_count is not None and excluded_count is not None
            else []
        ),
        f"- No-trade POI audits: `{len(no_trades)}`",
        f"- Execution events: `{len(executions)}`",
        f"- Active POI: `{json.dumps(state.get('activePoi'), ensure_ascii=False)}`",
        f"- Active order/position: `{json.dumps(state.get('activeOrder'), ensure_ascii=False)}`",
        "",
        "Decision source: raw closed candles only. Existing candidate ledgers and mentor_engine outputs are not imported.",
    ]
    PROGRESS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_status(_: argparse.Namespace) -> int:
    _, state, _, series = require_workspace()
    expected = expected_h1_times(series)
    write_progress(state, expected)
    print(PROGRESS.read_text(encoding="utf-8"))
    return 0


def add_map_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--carry", action="store_true")
    parser.add_argument("--external")
    parser.add_argument("--internal")
    parser.add_argument("--range-low", type=float)
    parser.add_argument("--range-high", type=float)
    parser.add_argument("--pd")
    parser.add_argument("--objective")
    parser.add_argument("--context")
    parser.add_argument("--poi-low", type=float)
    parser.add_argument("--poi-high", type=float)
    parser.add_argument("--poi-direction", choices=("long", "short"))
    parser.add_argument("--poi-label")
    parser.add_argument("--poi-family-json")
    parser.add_argument("--poi-family-file")
    parser.add_argument("--poi-selected-id")
    parser.add_argument("--invalidation")
    parser.add_argument("--decision", required=True, choices=("WAIT_POI", "NO_TRADE", "MONITOR", "HOLD_POSITION"))
    parser.add_argument("--reason", required=True)


def add_order_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--direction", required=True, choices=("long", "short"))
    parser.add_argument("--scope", required=True, choices=("EXTERNAL_CONTINUATION", "INTERNAL_ROTATION", "EXTERNAL_REVERSAL"))
    parser.add_argument("--map-tf", required=True, choices=("H4", "H1", "M30"))
    parser.add_argument("--source-tf", required=True, choices=("H4", "H1", "M30", "M15", "M5"))
    parser.add_argument("--trigger-tf", required=True, choices=("M5", "M1"))
    parser.add_argument("--map", required=True)
    parser.add_argument("--source-liquidity", required=True)
    parser.add_argument("--source-zone-label", required=True)
    parser.add_argument("--source-zone-low", required=True, type=float)
    parser.add_argument("--source-zone-high", required=True, type=float)
    parser.add_argument("--sweep", required=True)
    parser.add_argument("--sweep-extreme", required=True, type=float)
    parser.add_argument("--choch", required=True)
    parser.add_argument("--choch-level", required=True, type=float)
    parser.add_argument("--entry-zone-label", required=True)
    parser.add_argument("--entry-zone-low", required=True, type=float)
    parser.add_argument("--entry-zone-high", required=True, type=float)
    parser.add_argument("--entry", required=True, type=float)
    parser.add_argument("--stop", required=True, type=float)
    parser.add_argument("--target", required=True, type=float)
    parser.add_argument("--source-invalidation", required=True, type=float)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--parent-zone-id")
    parser.add_argument("--parent-zone-tf", choices=("H4", "H1", "M30", "M15", "M5"))
    parser.add_argument("--parent-zone-type", choices=tuple(sorted(CAUSAL_ZONE_TYPES)))
    parser.add_argument("--parent-zone-low", type=float)
    parser.add_argument("--parent-zone-high", type=float)
    parser.add_argument("--parent-zone-formed-at")
    parser.add_argument("--parent-zone-origin")
    parser.add_argument("--parent-displacement")
    parser.add_argument("--parent-break-level", type=float)
    parser.add_argument("--parent-break-level-formed-at")
    parser.add_argument("--parent-break-at")
    parser.add_argument("--parent-zone-state", choices=("FRESH", "PARTIAL"))
    parser.add_argument("--source-zone-type", choices=tuple(sorted(CAUSAL_ZONE_TYPES)))
    parser.add_argument("--source-zone-formed-at")
    parser.add_argument("--source-zone-origin")
    parser.add_argument("--source-displacement")
    parser.add_argument("--source-break-level", type=float)
    parser.add_argument("--source-break-level-formed-at")
    parser.add_argument("--source-break-at")
    parser.add_argument("--source-touch-at")
    parser.add_argument("--source-causal-relation")
    parser.add_argument("--refinement-path-json", default="[]")
    parser.add_argument("--refinement-path-file")
    parser.add_argument("--source-liquidity-kind")
    parser.add_argument("--source-liquidity-price", type=float)
    parser.add_argument("--source-liquidity-formed-at")
    parser.add_argument("--source-liquidity-tf", choices=tuple(TF_SECONDS))
    parser.add_argument("--source-liquidity-witnesses-json", default="[]")
    parser.add_argument("--trigger-liquidity-kind")
    parser.add_argument("--trigger-liquidity-price", type=float)
    parser.add_argument("--trigger-liquidity-formed-at")
    parser.add_argument("--trigger-liquidity-tf", choices=tuple(TF_SECONDS))
    parser.add_argument("--trigger-liquidity-witnesses-json", default="[]")
    parser.add_argument("--sweep-at")
    parser.add_argument("--choch-at")
    parser.add_argument("--choch-reference-formed-at")
    parser.add_argument("--entry-zone-type", choices=tuple(sorted(CAUSAL_ZONE_TYPES)))
    parser.add_argument("--entry-zone-tf", choices=("H4", "H1", "M30", "M15", "M5", "M1"))
    parser.add_argument("--entry-zone-formed-at")
    parser.add_argument("--entry-zone-origin")
    parser.add_argument("--entry-displacement")
    parser.add_argument("--objective-kind")
    parser.add_argument("--objective-price", type=float)
    parser.add_argument("--objective-formed-at")
    parser.add_argument("--objective-tf", choices=tuple(TF_SECONDS))
    parser.add_argument("--objective-witnesses-json", default="[]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Decision-neutral Q1 blind manual replay")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init").set_defaults(handler=command_init)
    next_parser = commands.add_parser("next")
    next_parser.add_argument("--compact", action="store_true")
    next_parser.add_argument("--micro", action="store_true")
    next_parser.set_defaults(handler=command_next)
    watch_parser = commands.add_parser("set-watch")
    watch_parser.add_argument("--low", required=True, type=float)
    watch_parser.add_argument("--high", required=True, type=float)
    watch_parser.add_argument("--reason", required=True)
    watch_parser.add_argument("--mode", choices=("REVIEW", "OBJECTIVE", "INVALIDATION"), default="REVIEW")
    watch_parser.add_argument("--suspend-micro", action="store_true")
    watch_parser.set_defaults(handler=command_set_watch)
    clear_watch = commands.add_parser("clear-watch")
    clear_watch.add_argument("--keep-pending", action="store_true")
    clear_watch.set_defaults(handler=command_clear_watch)
    clear_error = commands.add_parser("clear-error-lock")
    clear_error.add_argument("--reason", required=True)
    clear_error.set_defaults(handler=command_clear_error_lock)
    carry_next = commands.add_parser("carry-next")
    carry_next.add_argument("--decision", required=True, choices=("WAIT_POI", "NO_TRADE", "MONITOR", "HOLD_POSITION"))
    carry_next.add_argument("--reason", required=True)
    carry_next.set_defaults(handler=command_carry_next)
    step = commands.add_parser("step")
    step.add_argument("--minutes", type=int, choices=(1, 5, 15, 30), default=5)
    step.add_argument("--micro", action="store_true")
    step.set_defaults(handler=command_step)
    commands.add_parser("render").set_defaults(handler=command_render)
    zoom = commands.add_parser("zoom")
    zoom.add_argument("--timeframe", choices=tuple(TF_SECONDS), default="M1")
    zoom.add_argument("--bars", type=int, default=240)
    zoom.set_defaults(handler=command_zoom)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--timeframe", choices=tuple(TF_SECONDS), default="M1")
    inspect.add_argument("--bars", type=int, default=20)
    inspect.set_defaults(handler=command_inspect)
    map_parser = commands.add_parser("record-map")
    add_map_arguments(map_parser)
    map_parser.add_argument("--quiet", action="store_true")
    map_parser.add_argument("--as-of")
    map_parser.set_defaults(handler=command_record_map)
    poi_parser = commands.add_parser("declare-poi")
    poi_parser.add_argument("--poi-family-json")
    poi_parser.add_argument("--poi-family-file")
    poi_parser.add_argument("--poi-selected-id")
    poi_parser.add_argument("--poi-direction", required=True, choices=("long", "short"))
    poi_parser.add_argument("--poi-label", required=True)
    poi_parser.add_argument("--invalidation", required=True)
    poi_parser.add_argument("--reason", required=True)
    poi_parser.set_defaults(handler=command_declare_poi)
    no_trade = commands.add_parser("record-no-trade")
    no_trade.add_argument("--reason", required=True)
    no_trade.add_argument("--observed-ltf", required=True, choices=("M5", "M1", "M5+M1"))
    no_trade.add_argument("--poi-low", type=float)
    no_trade.add_argument("--poi-high", type=float)
    no_trade.add_argument("--poi-direction", choices=("long", "short"))
    no_trade.add_argument("--poi-label")
    no_trade.add_argument("--declared-at")
    no_trade.add_argument("--touched-at")
    no_trade.add_argument("--as-of")
    no_trade.add_argument("--supersedes")
    no_trade.add_argument("--correction-reason")
    no_trade.add_argument("--keep-poi", action="store_true")
    no_trade.set_defaults(handler=command_record_no_trade)
    order = commands.add_parser("record-order")
    add_order_arguments(order)
    order.set_defaults(handler=command_record_order)
    recover = commands.add_parser("recover-order")
    add_order_arguments(recover)
    recover.add_argument("--decision-at", required=True)
    recover.add_argument("--incident", required=True)
    recover.set_defaults(handler=command_recover_order)
    supersede = commands.add_parser("supersede-cancellation")
    supersede.add_argument("--order-id", required=True)
    supersede.add_argument("--reason", required=True)
    supersede.set_defaults(handler=command_supersede_cancellation)
    commands.add_parser("audit").set_defaults(handler=command_audit)
    commands.add_parser("status").set_defaults(handler=command_status)
    return parser


def main() -> int:
    parser = build_parser()
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        args = parser.parse_args()
        return int(args.handler(args))
    except SystemExit as exc:
        if command in {"record-order", "recover-order"} and exc.code not in (None, 0):
            set_recording_error_lock(command, str(exc.code))
        raise
    except Exception as exc:
        if command in {"record-order", "recover-order"}:
            set_recording_error_lock(command, f"{type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
