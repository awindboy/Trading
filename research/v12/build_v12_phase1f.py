#!/usr/bin/env python3
"""Build the frozen V12 Phase-1F Parent target-succession study."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Iterable, Optional

import numpy as np

from build_v12_phase1d import child_summary, nha_summary, read_csv, write_csv, write_json
from build_v12_phase1e import bootstrap_child
from v12_phase0_core import price_points, sha256_file
from v12_phase1f_core import (
    CONTRACT_VERSION,
    Level,
    advance_frontier,
    ahead,
    choose_external_cluster,
    parse_time,
    state_at,
    target_id,
)


PREFIX = "V12_PHASE1F_"


def safe_prepare_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output directory is not empty: {path}")
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected path: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def as_float(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    return float(value)


def load_levels(phase1b: Path) -> list[Level]:
    outcomes = {
        row["level_id"]: row
        for row in read_csv(phase1b / "V12_PHASE1B_KEY_LEVEL_OUTCOMES.csv")
    }
    levels = []
    for row in read_csv(phase1b / "V12_PHASE1B_KEY_LEVEL_DECISIONS.csv"):
        outcome = outcomes[row["level_id"]]
        levels.append(
            Level(
                level_id=row["level_id"],
                family=row["family"],
                side=row["side"],
                price=float(row["price"]),
                known_at=parse_time(row["known_at"]),
                consumed_at=parse_time(outcome["consumed_at"]),
            )
        )
    return levels


def load_h4_reviews(phase1b: Path) -> list[dict]:
    unique: dict[datetime, dict] = {}
    for row in read_csv(phase1b / "V12_PHASE1B_H4_CRT_DECISIONS.csv"):
        timestamp = parse_time(row["c2_completed_by"])
        item = {
            "timestamp": timestamp,
            "close": float(row["c2_close"]),
            "atr180": as_float(row["h4_atr180"]),
            "h4_open_time": row["c2_open_time"],
        }
        previous = unique.get(timestamp)
        if previous and (previous["close"] != item["close"] or previous["atr180"] != item["atr180"]):
            raise ValueError(f"conflicting H4 review at {timestamp}")
        unique[timestamp] = item
    return [unique[key] for key in sorted(unique)]


def load_journeys(phase1b: Path) -> list[dict]:
    starts = {}
    for row in read_csv(phase1b / "V12_PHASE1B_JOURNEY_DECISIONS.csv"):
        if row["state_action"] == "START":
            starts[row["journey_id"]] = row
    output = []
    for outcome in read_csv(phase1b / "V12_PHASE1B_JOURNEY_OUTCOMES.csv"):
        start = starts[outcome["journey_id"]]
        output.append({**outcome, "origin": start})
    return sorted(output, key=lambda row: (row["start_time"], row["journey_id"]))


def internal_candidates(journey: dict) -> list[dict]:
    origin = journey["origin"]
    return [
        {
            "kind": "ORIGIN_C1_MIDPOINT",
            "price": float(origin["c1_midpoint"]),
            "touch_time": parse_time(journey["midpoint_time"]),
        },
        {
            "kind": "ORIGIN_C1_OPPOSITE_EDGE",
            "price": float(origin["opposite_edge"]),
            "touch_time": parse_time(journey["opposite_edge_time"]),
        },
    ]


def first_review_after(reviews: list[dict], timestamp: datetime, end: datetime) -> Optional[dict]:
    return next((row for row in reviews if timestamp < row["timestamp"] < end), None)


def build_target_inventory(
    journeys: list[dict], levels: list[Level], reviews: list[dict]
) -> tuple[list[dict], list[dict], dict[str, list[dict]]]:
    decisions: list[dict] = []
    outcomes: list[dict] = []
    merged_by_journey: dict[str, list[dict]] = defaultdict(list)

    for journey in journeys:
        journey_id_value = journey["journey_id"]
        direction = journey["direction"]
        start = parse_time(journey["start_time"])
        end = parse_time(journey["end_time"])
        if end is None or end <= start:
            raise ValueError(f"invalid journey interval: {journey_id_value}")
        origin = journey["origin"]
        start_price = float(origin["activation_price"])
        frontier = start_price
        used_internal: set[str] = set()
        candidates = internal_candidates(journey)
        current_time = start
        reference_price = start_price
        atr = as_float(origin["h4_atr180"])
        reason = "JOURNEY_START"
        iterations = 0

        while current_time < end:
            iterations += 1
            if iterations > 10000:
                raise RuntimeError(f"target loop did not converge: {journey_id_value}")
            frontier = advance_frontier(direction, frontier, reference_price)
            skipped_internal: list[str] = []
            selected_internal = None
            for candidate in candidates:
                if candidate["kind"] in used_internal:
                    continue
                touched = candidate["touch_time"]
                if touched is not None and touched < current_time:
                    used_internal.add(candidate["kind"])
                    frontier = advance_frontier(direction, frontier, candidate["price"])
                    skipped_internal.append(candidate["kind"] + ":COMPLETED_BEFORE_REFRAME")
                    continue
                if not ahead(direction, candidate["price"], frontier):
                    used_internal.add(candidate["kind"])
                    skipped_internal.append(candidate["kind"] + ":NOT_AHEAD_OF_FRONTIER")
                    continue
                selected_internal = candidate
                break

            cluster: list[Level] = []
            if selected_internal:
                kind = selected_internal["kind"]
                price = selected_internal["price"]
                member_ids = [kind]
                member_families = ["ORIGIN_C1"]
                completed_at = selected_internal["touch_time"]
                used_internal.add(kind)
            else:
                cluster = choose_external_cluster(levels, direction, current_time, frontier)
                if cluster:
                    kind = "EXTERNAL_ONE_USE_CLUSTER"
                    price = cluster[0].price
                    member_ids = [level.level_id for level in cluster]
                    member_families = sorted({level.family for level in cluster})
                    completions = {level.consumed_at for level in cluster if level.consumed_at is not None}
                    if len(completions) > 1:
                        raise ValueError(f"same-price cluster consumed at different times: {member_ids}")
                    completed_at = next(iter(completions), None)
                else:
                    kind = None
                    price = None
                    member_ids = []
                    member_families = []
                    completed_at = None

            distance = None if price is None else abs(price - reference_price)
            distance_atr = distance / atr if distance is not None and atr else None
            selection_status = "TARGET_SELECTED" if price is not None else "NO_FORWARD_TARGET"
            target_id_value = (
                target_id(journey_id_value, current_time, kind, price, member_ids)
                if price is not None
                else None
            )
            decisions.append(
                {
                    "contract_version": CONTRACT_VERSION,
                    "journey_id": journey_id_value,
                    "direction": direction,
                    "reframe_time": iso(current_time),
                    "reframe_reason": reason,
                    "reference_price": reference_price,
                    "progress_frontier": frontier,
                    "h4_atr180": atr,
                    "selection_status": selection_status,
                    "target_id": target_id_value,
                    "target_kind": kind,
                    "target_price": price,
                    "distance_price": distance,
                    "distance_atr180": distance_atr,
                    "member_count": len(member_ids),
                    "member_level_ids": "|".join(member_ids),
                    "member_families": "|".join(member_families),
                    "skipped_internal_targets": "|".join(skipped_internal),
                    "outcome_fields_present": False,
                }
            )

            if price is None:
                review = first_review_after(reviews, current_time, end)
                if not review:
                    break
                current_time = review["timestamp"]
                reference_price = review["close"]
                atr = review["atr180"]
                reason = "RETRY_NO_SUCCESSOR"
                continue

            completed_before_end = completed_at is not None and completed_at < end
            terminal_reason = "TARGET_COMPLETED" if completed_before_end else (
                "PARENT_ENDED_BEFORE_TARGET" if journey["end_reason"] != "OPEN_AT_CUTOFF" else "CENSORED_AT_CUTOFF"
            )
            outcome = {
                "contract_version": CONTRACT_VERSION,
                "target_id": target_id_value,
                "journey_id": journey_id_value,
                "selected_at": iso(current_time),
                "target_kind": kind,
                "target_price": price,
                "distance_atr180": distance_atr,
                "member_families": "|".join(member_families),
                "selection_reason": reason,
                "skipped_internal_targets": "|".join(skipped_internal),
                "completed_at": iso(completed_at) if completed_before_end else None,
                "completed_before_parent_end": completed_before_end,
                "terminal_reason": terminal_reason,
                "parent_end_time": journey["end_time"],
                "parent_end_reason": journey["end_reason"],
                "outcome_fields_present": True,
            }
            outcomes.append(outcome)
            merged_by_journey[journey_id_value].append(outcome)
            if not completed_before_end:
                break
            frontier = advance_frontier(direction, frontier, price)
            review = first_review_after(reviews, completed_at, end)
            if not review:
                break
            current_time = review["timestamp"]
            reference_price = review["close"]
            atr = review["atr180"]
            reason = "AFTER_TARGET_COMPLETION"

    return decisions, outcomes, merged_by_journey


def target_context(journeys: dict[str, dict], targets: dict[str, list[dict]], journey_id_value: str, timestamp: datetime) -> dict:
    if not journey_id_value:
        return {"target_state": "NO_ACTIVE_PARENT", "target_id": None}
    journey = journeys[journey_id_value]
    context = state_at(journey, targets.get(journey_id_value, []), timestamp)
    context["target_parent_direction"] = journey["direction"]
    context["target_parent_origin_interaction"] = journey["origin"]["interaction"]
    context["target_parent_origin_activation_status"] = journey["origin"]["activation_status"]
    return context


def prefixed(context: dict, prefix: str = "") -> dict:
    return {f"{prefix}{key}": value for key, value in context.items()}


def enrich_children(phase1e: Path, journeys: dict[str, dict], targets: dict[str, list[dict]]) -> list[dict]:
    output = []
    for row in read_csv(phase1e / "V12_PHASE1E_V10_CHILD_SESSION_CONTEXT.csv"):
        item = dict(row)
        item.update(target_context(journeys, targets, row.get("journey_id", ""), parse_time(row["decision_time"])))
        item["target_kind"] = item.get("target_kind") or "NONE"
        ordinal = row.get("aligned_child_ordinal", "")
        item["aligned_ordinal_bucket"] = (
            "FIRST_ALIGNED" if ordinal not in (None, "") and int(float(ordinal)) == 1
            else "LATER_ALIGNED" if ordinal not in (None, "")
            else "NOT_ALIGNED"
        )
        output.append(item)
    return output


def enrich_nha(phase1e: Path, journeys: dict[str, dict], targets: dict[str, list[dict]]) -> list[dict]:
    output = []
    for row in read_csv(phase1e / "V12_PHASE1E_NHA_SESSION_CONTEXT.csv"):
        item = dict(row)
        journey_id_value = row.get("active_journey_id") or row.get("old_journey_id") or ""
        item.update(target_context(journeys, targets, journey_id_value, parse_time(row["known_at"])))
        item["target_kind"] = item.get("target_kind") or "NONE"
        output.append(item)
    return output


def grouped_rows(rows: list[dict], fields: list[str]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups["|".join(str(row.get(field, "")) for field in fields)].append(row)
    return groups


def child_scorecards(rows: list[dict]) -> list[dict]:
    dimensions = {
        "TARGET_STATE": ["target_state"],
        "TARGET_KIND": ["target_kind"],
        "RELATION_X_TARGET_STATE": ["relation", "target_state"],
        "RELATION_X_TARGET_KIND": ["relation", "target_kind"],
        "TARGET_STATE_X_ENTRY_SESSION": ["target_state", "entry_session_phase"],
        "TARGET_STATE_X_NEW_YORK_WEEKDAY": ["target_state", "entry_new_york_weekday"],
        "TARGET_STATE_X_USD_EVENT_STATE": ["target_state", "usd_event_state"],
        "TARGET_STATE_X_YEAR": ["target_state", "analysis_year"],
        "TARGET_STATE_X_SIDE": ["target_state", "direction"],
        "TARGET_STATE_X_V10_EVENT": ["target_state", "event"],
        "TARGET_STATE_X_BROKER_HOUR": ["target_state", "broker_hour"],
        "TARGET_KIND_X_YEAR": ["target_kind", "analysis_year"],
        "TARGET_KIND_X_SELECTION_REASON": ["target_kind", "target_selection_reason"],
        "RELATION_X_TARGET_KIND_X_YEAR": ["relation", "target_kind", "analysis_year"],
        "RELATION_X_TARGET_KIND_X_SIDE": ["relation", "target_kind", "direction"],
        "RELATION_X_ORIGIN_INTERACTION_X_TARGET_KIND": ["relation", "target_parent_origin_interaction", "target_kind"],
        "ALIGNED_ORDINAL_X_TARGET_KIND": ["aligned_ordinal_bucket", "target_kind"],
        "ALIGNED_ORDINAL_X_TARGET_KIND_X_YEAR": ["aligned_ordinal_bucket", "target_kind", "analysis_year"],
        "ALIGNED_ORDINAL_X_TARGET_KIND_X_SIDE": ["aligned_ordinal_bucket", "target_kind", "direction"],
        "ALIGNED_ORDINAL_X_TARGET_KIND_X_SELECTION_REASON": ["aligned_ordinal_bucket", "target_kind", "target_selection_reason"],
        "ALIGNED_ORDINAL_X_ORIGIN_INTERACTION_X_TARGET_KIND": ["aligned_ordinal_bucket", "target_parent_origin_interaction", "target_kind"],
        "FIRST_ALIGNED_X_ORIGIN_INTERACTION_X_TARGET_KIND_X_YEAR": ["aligned_ordinal_bucket", "target_parent_origin_interaction", "target_kind", "analysis_year"],
        "FIRST_ALIGNED_EXTERNAL_REASON_X_YEAR": ["aligned_ordinal_bucket", "target_kind", "target_selection_reason", "analysis_year"],
        "FIRST_ALIGNED_EXTERNAL_REASON_X_ORIGIN_INTERACTION": ["target_selection_reason", "target_parent_origin_interaction"],
        "JOURNEY_STAGE_X_TARGET_KIND": ["journey_stage", "target_kind"],
        "H20_GROUP_X_TARGET_STATE": ["h20_group", "target_state"],
    }
    output = [{"dimension": "ALL", "group": "ALL", **child_summary(rows), **bootstrap_child(rows, "PHASE1F:ALL")}]
    for dimension, fields in dimensions.items():
        if dimension == "H20_GROUP_X_TARGET_STATE":
            selected = [row for row in rows if row.get("h20_group")]
        elif dimension in {"FIRST_ALIGNED_EXTERNAL_REASON_X_YEAR", "FIRST_ALIGNED_EXTERNAL_REASON_X_ORIGIN_INTERACTION"}:
            selected = [
                row for row in rows
                if row["aligned_ordinal_bucket"] == "FIRST_ALIGNED"
                and row["target_kind"] == "EXTERNAL_ONE_USE_CLUSTER"
            ]
        elif dimension == "FIRST_ALIGNED_X_ORIGIN_INTERACTION_X_TARGET_KIND_X_YEAR":
            selected = [row for row in rows if row["aligned_ordinal_bucket"] == "FIRST_ALIGNED"]
        else:
            selected = rows
        for group, values in sorted(grouped_rows(selected, fields).items()):
            output.append({
                "dimension": dimension,
                "group": group,
                **child_summary(values),
                **bootstrap_child(values, f"PHASE1F:{dimension}:{group}"),
            })
    return output


def nha_scorecards(rows: list[dict]) -> list[dict]:
    dimensions = {
        "TARGET_STATE": ["target_state"],
        "EXPLANATION_X_TARGET_STATE": ["explanation_state", "target_state"],
        "TARGET_STATE_X_SESSION": ["target_state", "known_session_phase"],
        "TARGET_STATE_X_NEW_YORK_WEEKDAY": ["target_state", "known_new_york_weekday"],
        "TARGET_STATE_X_USD_EVENT_STATE": ["target_state", "usd_event_state"],
        "TARGET_STATE_X_YEAR": ["target_state", "analysis_year"],
    }
    output = [{"dimension": "ALL", "group": "ALL", **nha_summary(rows)}]
    for dimension, fields in dimensions.items():
        for group, values in sorted(grouped_rows(rows, fields).items()):
            output.append({"dimension": dimension, "group": group, **nha_summary(values)})
    return output


def carry_summary(rows: Iterable[dict]) -> dict:
    values = list(rows)
    funded = sum(float(row["funded_units"]) for row in values)
    baseline_stopped = sum(float(row["stopped_loss_units"]) for row in values)
    carry_stopped = sum(float(row["funded_units"]) * int(float(row["carry_stop_hit"])) for row in values)
    baseline_r = sum(float(row["combined_R_units"]) for row in values)
    carry_r = sum(float(row["carry_combined_R_units"]) for row in values)
    baseline_tail = sum(float(row["right_tail_ge_5R_units"]) for row in values)
    carry_tail = sum(
        float(row["carry_combined_R_units"])
        if float(row["carry_combined_R_units"]) >= 5.0 else 0.0
        for row in values
    )
    return {
        "changed_children": len(values),
        "funded_units": funded,
        "baseline_stopped_children": sum(int(float(row["stop_hit"])) for row in values),
        "carry_stopped_children": sum(int(float(row["carry_stop_hit"])) for row in values),
        "baseline_stopped_units_per_100": 100.0 * baseline_stopped / funded if funded else np.nan,
        "carry_stopped_units_per_100": 100.0 * carry_stopped / funded if funded else np.nan,
        "baseline_net_R": baseline_r,
        "carry_net_R": carry_r,
        "delta_R": carry_r - baseline_r,
        "baseline_ge5R_tail": baseline_tail,
        "carry_ge5R_tail": carry_tail,
        "delta_ge5R_tail": carry_tail - baseline_tail,
    }


def build_bridge_context(
    phase1c: Path,
    children_by_signal: dict[str, dict],
    journeys: dict[str, dict],
    targets: dict[str, list[dict]],
) -> tuple[list[dict], list[dict]]:
    carry_outcomes = {
        row["carry_id"]: row for row in read_csv(phase1c / "V12_PHASE1C_CARRY_OUTCOMES.csv")
    }
    carry_rows = []
    for decision in read_csv(phase1c / "V12_PHASE1C_CARRY_DECISIONS.csv"):
        baseline = children_by_signal[decision["signal_id"]]
        outcome = carry_outcomes[decision["carry_id"]]
        item = dict(decision)
        for key in ("decision_time", "entry_time", "exit_time", "R", "stop_hit", "combined_R_units", "stopped_loss_units", "funded_units", "right_tail_ge_5R_units", "iso_week", "entry_session_phase", "entry_new_york_weekday", "usd_event_state", "analysis_year"):
            item[key] = baseline.get(key, "")
        item.update(prefixed(target_context(journeys, targets, decision["journey_id"], parse_time(decision["baseline_exit_time"])), "bridge_"))
        item["carry_stop_hit"] = outcome["stop_hit"]
        item["carry_R"] = outcome["R"]
        item["carry_combined_R_units"] = outcome["combined_R_units"]
        carry_rows.append(item)

    repair_outcomes = {
        row["repair_id"]: row for row in read_csv(phase1c / "V12_PHASE1C_REPAIR_OUTCOMES.csv")
    }
    repair_rows = []
    for decision in read_csv(phase1c / "V12_PHASE1C_REPAIR_DECISIONS.csv"):
        item = dict(decision)
        item.update(prefixed(target_context(journeys, targets, decision["journey_id"], parse_time(decision["bridge_start_time"])), "bridge_"))
        if decision.get("repair_time"):
            item.update(prefixed(target_context(journeys, targets, decision["journey_id"], parse_time(decision["repair_time"])), "repair_"))
        else:
            item["repair_target_state"] = "NO_REPAIR"
        outcome = repair_outcomes.get(decision["repair_id"])
        if outcome:
            for key, value in outcome.items():
                if key not in {"contract_version", "repair_id", "bridge_id", "outcome_fields_present"}:
                    item[f"outcome_{key}"] = value
        repair_rows.append(item)
    return carry_rows, repair_rows


def carry_scorecards(rows: list[dict]) -> list[dict]:
    dimensions = {
        "BRIDGE_TARGET_STATE": ["bridge_target_state"],
        "BRIDGE_TARGET_KIND": ["bridge_target_kind"],
        "BRIDGE_TARGET_STATE_X_SESSION": ["bridge_target_state", "entry_session_phase"],
        "BRIDGE_TARGET_STATE_X_USD_EVENT_STATE": ["bridge_target_state", "usd_event_state"],
        "BRIDGE_TARGET_STATE_X_YEAR": ["bridge_target_state", "analysis_year"],
        "FLIP_STATE_X_BRIDGE_TARGET_STATE": ["flip_state", "bridge_target_state"],
    }
    output = [{"dimension": "ALL", "group": "ALL", **carry_summary(rows)}]
    for dimension, fields in dimensions.items():
        for group, values in sorted(grouped_rows(rows, fields).items()):
            output.append({"dimension": dimension, "group": group, **carry_summary(values)})
    return output


def repair_scorecards(rows: list[dict]) -> list[dict]:
    dimensions = {
        "BRIDGE_TARGET_STATE": ["bridge_target_state"],
        "REPAIR_TARGET_STATE": ["repair_target_state"],
        "REPAIR_STATUS_X_BRIDGE_TARGET_STATE": ["repair_status", "bridge_target_state"],
    }
    output = []
    for dimension, fields in dimensions.items():
        for group, values in sorted(grouped_rows(rows, fields).items()):
            outcomes = [row for row in values if row.get("outcome_R") not in (None, "")]
            output.append({
                "dimension": dimension,
                "group": group,
                "bridge_episodes": len(values),
                "repairs_with_k1": len(outcomes),
                "repair_stops": sum(int(float(row["outcome_stop_hit"])) for row in outcomes),
                "repair_net_R": sum(float(row["outcome_R"]) for row in outcomes),
                "parent_clock_delta_R": sum(float(row["outcome_parent_clock_delta_R"]) for row in outcomes),
                "incremental_not_r7g_selected": sum(row.get("repair_k1_already_r7g_selected", "").lower() == "false" for row in outcomes),
            })
    return output


def target_scorecards(outcomes: list[dict]) -> list[dict]:
    output = []
    for kind, values in sorted(grouped_rows(outcomes, ["target_kind"]).items()):
        completed = [row for row in values if str(row["completed_before_parent_end"]).lower() == "true"]
        durations = [
            (parse_time(row["completed_at"]) - parse_time(row["selected_at"])).total_seconds() / 3600.0
            for row in completed
        ]
        output.append({
            "dimension": "TARGET_KIND",
            "group": kind,
            "selected_targets": len(values),
            "completed_targets": len(completed),
            "completion_rate": len(completed) / len(values) if values else np.nan,
            "median_hours_to_completion": median(durations) if durations else np.nan,
        })
    return output


def file_manifest(path: Path) -> dict:
    rows = None
    if path.suffix == ".csv":
        with path.open("rb") as handle:
            rows = max(0, sum(1 for _ in handle) - 1)
    return {"file": path.name, "bytes": path.stat().st_size, "rows": rows, "sha256": sha256_file(path)}


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1f_contract.json")
    parser.add_argument("--phase1b", type=Path, default=repo / "output/v12_phase1b_h4m5_journey_overlay_20260923")
    parser.add_argument("--phase1c", type=Path, default=repo / "output/v12_phase1c_crt_protected_carry_repair_20260924")
    parser.add_argument("--phase1e", type=Path, default=repo / "output/v12_phase1e_session_weekday_event_20260924_a")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1f_parent_target_succession_20260924")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract version mismatch")
    cutoff = parse_time(contract["mechanism_cutoff"])
    safe_prepare_output(args.output, args.replace)

    levels = load_levels(args.phase1b)
    reviews = load_h4_reviews(args.phase1b)
    journey_rows = load_journeys(args.phase1b)
    journeys = {row["journey_id"]: row for row in journey_rows}
    target_decisions, target_outcomes, targets = build_target_inventory(journey_rows, levels, reviews)
    children = enrich_children(args.phase1e, journeys, targets)
    nhas = enrich_nha(args.phase1e, journeys, targets)
    children_by_signal = {row["signal_id"]: row for row in children}
    carry_rows, repair_rows = build_bridge_context(args.phase1c, children_by_signal, journeys, targets)

    outputs = {
        "TARGET_DECISIONS.csv": target_decisions,
        "TARGET_OUTCOMES.csv": target_outcomes,
        "TARGET_SCORECARD.csv": target_scorecards(target_outcomes),
        "V10_CHILD_TARGET_CONTEXT.csv": children,
        "V10_CHILD_TARGET_SCORECARD.csv": child_scorecards(children),
        "NHA_TARGET_CONTEXT.csv": nhas,
        "NHA_TARGET_SCORECARD.csv": nha_scorecards(nhas),
        "CARRY_TARGET_CONTEXT.csv": carry_rows,
        "CARRY_TARGET_SCORECARD.csv": carry_scorecards(carry_rows),
        "REPAIR_TARGET_CONTEXT.csv": repair_rows,
        "REPAIR_TARGET_SCORECARD.csv": repair_scorecards(repair_rows),
    }
    paths = []
    for name, rows in outputs.items():
        path = args.output / f"{PREFIX}{name}"
        write_csv(path, rows)
        paths.append(path)

    incomplete_children = sum(row["target_state"] == "TARGET_UNFINISHED" for row in children)
    pending_children = sum(row["target_state"] == "TARGET_COMPLETE_REFRAME_PENDING" for row in children)
    incomplete_carry = sum(row["bridge_target_state"] == "TARGET_UNFINISHED" for row in carry_rows)
    pending_carry = sum(row["bridge_target_state"] == "TARGET_COMPLETE_REFRAME_PENDING" for row in carry_rows)
    pending_children_rows = [row for row in children if row["target_state"] == "TARGET_COMPLETE_REFRAME_PENDING"]
    diagnostics = {
        "contract_version": CONTRACT_VERSION,
        "contract_sha256": sha256_file(args.contract),
        "causal_cutoff": cutoff.isoformat(),
        "phase1b_manifest_sha256": sha256_file(args.phase1b / "V12_PHASE1B_MANIFEST.json"),
        "phase1c_manifest_sha256": sha256_file(args.phase1c / "V12_PHASE1C_MANIFEST.json"),
        "phase1e_manifest_sha256": sha256_file(args.phase1e / "V12_PHASE1E_MANIFEST.json"),
        "journeys": len(journeys),
        "levels": len(levels),
        "h4_reviews": len(reviews),
        "target_reframes": len(target_decisions),
        "selected_targets": len(target_outcomes),
        "completed_targets": sum(str(row["completed_before_parent_end"]).lower() == "true" for row in target_outcomes),
        "v10_children": len(children),
        "v10_children_unfinished_target": incomplete_children,
        "v10_children_reframe_pending": pending_children,
        "v10_reframe_pending_order_fail": sum(row.get("event") == "ORDER_FAIL" for row in pending_children_rows),
        "v10_reframe_pending_exit_pending_block": sum(row.get("event") == "EXIT_PENDING_BLOCK" for row in pending_children_rows),
        "v10_reframe_pending_entry": sum(row.get("event") == "ENTRY" for row in pending_children_rows),
        "nha_flips": len(nhas),
        "carry_children": len(carry_rows),
        "carry_children_unfinished_target": incomplete_carry,
        "carry_children_reframe_pending": pending_carry,
        "repair_episodes": len(repair_rows),
        "post_cutoff_price_rows_parsed": 0,
        "derived_from_byte_frozen_causal_packs": True,
        "trade_authority": False,
        "sizing_authority": False,
    }
    diagnostics_path = args.output / f"{PREFIX}DIAGNOSTICS.json"
    write_json(diagnostics_path, diagnostics)
    paths.append(diagnostics_path)
    manifest = {
        "contract_version": CONTRACT_VERSION,
        "contract_sha256": sha256_file(args.contract),
        "frozen_at": contract["frozen_at"],
        "files": [file_manifest(path) for path in paths],
    }
    write_json(args.output / f"{PREFIX}MANIFEST.json", manifest)
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
