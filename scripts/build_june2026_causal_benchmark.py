"""Build an outcome-visible but causally replayed June 2026 benchmark ledger.

Future data is used only to enumerate the gross move index and to score outcomes.
Every scenario, trigger and order is reconstructed at its own as-of timestamp.
The resulting formal-pass ledger still requires a final chart semantic audit.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_june2026_oracle_atlas import load_joined, timestamp
from mentor_replay_v4_core import (
    MarketData,
    PLAN_SEMANTIC_AUDIT_KEYS,
    V4ContractError,
    _atomic_scenario_options,
    advance_pending,
    advance_position,
    advance_reaction_monitor,
    advance_shadow_delivery_candidate,
    build_order,
    build_plan_packet,
    build_reaction_monitor,
    detect_pre_touch_delivery_candidate,
    freeze_plan,
    freeze_trigger_watch,
    local_scenario_cancel_reason,
    mechanical_choch_break_candidates,
    mechanical_choch_reference_candidates,
    mechanical_m5_correction_swing_candidates,
    mechanical_root_candidates,
    outermost_completed_sweep_events,
    parse_utc,
    refresh_reaction_monitor,
    utc_text,
    zone_touched,
)


UTC = timezone.utc


def read_schedule(path: Path) -> list[int]:
    values: set[int] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("event") == "LOCAL_PLAN_SCHEDULED":
                values.add(parse_utc(record["asOfUtc"]))
    return sorted(values)


def oracle_review_schedule(path: Path, start: int, end: int) -> list[int]:
    """Rewind each outcome-discovered M5 pivot to its pre-touch open time."""
    values: set[int] = {start + 60}
    with path.open(encoding="utf-8-sig") as handle:
        for item in csv.DictReader(handle):
            pivot = parse_utc(str(item["pivotTimeUtc"]))
            for delay in (0,):
                as_of = pivot + delay
                if start <= as_of < end:
                    values.add(as_of)
    return sorted(values)


def rows_after(market: MarketData, start: int, end: int) -> list[dict[str, Any]]:
    times = market.rates["time"]
    left = int(__import__("numpy").searchsorted(times, start, side="left"))
    right = int(__import__("numpy").searchsorted(times, end - 60, side="right"))
    return [market.m1_row(index) for index in range(left, right)]


def _first_m1_event(
    market: MarketData,
    start: int,
    end: int,
    predicate: Any,
) -> tuple[int, str] | None:
    rates = market.rates
    left = int(np.searchsorted(rates["time"], start, side="left"))
    right = int(np.searchsorted(rates["time"], end - 60, side="right"))
    if right <= left:
        return None
    indexes = np.flatnonzero(predicate(rates[left:right]))
    if not len(indexes):
        return None
    index = left + int(indexes[0])
    available = int(rates["time"][index]) + 60
    return available, f"M1:{int(rates['time'][index])}"


def _first_body_invalidation(
    market: MarketData,
    node: dict[str, Any],
    direction: str,
    start: int,
    end: int,
) -> tuple[int, str] | None:
    series = market.frames[node["tf"]]
    left = int(np.searchsorted(series.available_time, start, side="right"))
    right = int(np.searchsorted(series.available_time, end, side="right"))
    closes = np.asarray(series.close[left:right], dtype=float)
    crossed = closes < float(node["distal"]) if direction == "LONG" else closes > float(node["distal"])
    indexes = np.flatnonzero(crossed)
    if not len(indexes):
        return None
    index = left + int(indexes[0])
    return int(series.available_time[index]), f"{node['tf']}:{int(series.time[index])}"


def prefilter_scenario(
    market: MarketData,
    scenario: dict[str, Any],
    follow_end: int,
) -> dict[str, Any]:
    """Resolve the first post-freeze causal event without trigger inference."""
    start = parse_utc(scenario["frozenAtUtc"])
    direction = scenario["direction"]
    child = scenario["finalChild"]
    objective = float(scenario["objective"]["price"])
    rates = market.rates

    objective_event = _first_m1_event(
        market, start, follow_end,
        (lambda block: block["high"] >= objective)
        if direction == "LONG" else
        (lambda block: block["low"] <= objective),
    )
    touch_event = _first_m1_event(
        market, start, follow_end,
        lambda block: (block["high"] >= float(child["low"]))
        & (block["low"] <= float(child["high"])),
    )
    consumed_event = _first_m1_event(
        market, start, follow_end,
        (lambda block: block["low"] <= float(child["distal"]))
        if direction == "LONG" else
        (lambda block: block["high"] >= float(child["distal"])),
    )

    source_events: list[tuple[int, str, str]] = []
    for node in [scenario["root"], *scenario["refinements"]]:
        event = _first_body_invalidation(market, node, direction, start, follow_end)
        if event:
            source_events.append((event[0], event[1], node["obBarId"]))

    owner_event: tuple[int, str] | None = None
    if scenario["scope"] != "INTERNAL_ROTATION":
        swing = scenario["mapProtectedSwing"]
        series = market.frames[swing["tf"]]
        left = int(np.searchsorted(series.available_time, start, side="right"))
        right = int(np.searchsorted(series.available_time, follow_end, side="right"))
        closes = np.asarray(series.close[left:right], dtype=float)
        crossed = closes < float(swing["low"]) if direction == "LONG" else closes > float(swing["high"])
        indexes = np.flatnonzero(crossed)
        if len(indexes):
            index = left + int(indexes[0])
            owner_event = int(series.available_time[index]), f"{swing['tf']}:{int(series.time[index])}"

    events: list[tuple[int, int, str, str, str]] = []
    # Lower priority number wins ties. A same-bar ambiguity cannot rescue a trade.
    if objective_event:
        events.append((objective_event[0], 0, "REJECT", "OBJECTIVE_REACHED_BEFORE_CHILD_TOUCH", objective_event[1]))
    for available, bar_id, node_id in source_events:
        events.append((available, 1, "REJECT", f"SOURCE_BODY_INVALIDATED:{node_id}", bar_id))
    if owner_event:
        events.append((owner_event[0], 2, "REJECT", "OPPOSING_OWNER_CONFIRMED", owner_event[1]))
    if consumed_event:
        events.append((consumed_event[0], 3, "REJECT", "POI_FULLY_CONSUMED", consumed_event[1]))
    if touch_event:
        events.append((touch_event[0], 4, "KEEP", "CLEAN_CHILD_TOUCH", touch_event[1]))

    if not events:
        return {
            "status": "REJECT", "reason": "NO_TERMINAL_EVENT_BEFORE_FOLLOW_END",
            "eventAtUtc": "", "eventBarId": "",
        }
    event = min(events, key=lambda item: (item[0], item[1]))
    return {
        "status": event[2], "reason": event[3],
        "eventAtUtc": utc_text(event[0]), "eventBarId": event[4],
    }


def physical_scenario_key(scenario: dict[str, Any]) -> tuple[str, ...]:
    return (
        scenario["direction"], scenario["scope"],
        scenario["root"]["obBarId"], scenario["finalChild"]["obBarId"],
        scenario["objective"]["barId"],
    )


def append_m1_choch_reference(
    history: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    direction: str,
) -> list[dict[str, Any]]:
    if len(history) < 3:
        return candidates
    previous, row, following = history[-3:]
    if direction == "SHORT":
        pivot = row["low"] < previous["low"] and row["low"] <= following["low"]
        reacted = following["high"] > row["high"]
        side, level = "LIVE_LOW", row["low"]
    else:
        pivot = row["high"] > previous["high"] and row["high"] >= following["high"]
        reacted = following["low"] < row["low"]
        side, level = "LIVE_HIGH", row["high"]
    if pivot and reacted and all(item["barId"] != row["barId"] for item in candidates):
        candidates = [*candidates, {
            "barId": row["barId"], "timeUtc": utc_text(row["time"]),
            "side": side, "level": level, "confirmedByBarId": following["barId"],
        }][-12:]
    return candidates


def append_reaction_liquidity_candidate(
    monitor: dict[str, Any],
    history: list[dict[str, Any]],
    scenario: dict[str, Any],
    point: float,
) -> dict[str, Any]:
    """Incrementally mature the center of a five-bar M1 pivot window."""
    if len(history) < 5:
        return monitor
    left = history[:2]
    row = history[2]
    right = history[3:]
    direction = scenario["direction"]
    lineage = [scenario["root"], *scenario["refinements"]]
    context_low = min(float(node["low"]) for node in lineage)
    context_high = max(float(node["high"]) for node in lineage)
    if direction == "SHORT":
        pivot = row["high"] > max(item["high"] for item in left) and row["high"] >= max(item["high"] for item in right)
        level = row["high"]
        unswept = not any(item["high"] > level for item in right)
        reacted = any(item["low"] < row["low"] for item in right)
        side = "BSL"
    else:
        pivot = row["low"] < min(item["low"] for item in left) and row["low"] <= min(item["low"] for item in right)
        level = row["low"]
        unswept = not any(item["low"] < level for item in right)
        reacted = any(item["high"] > row["high"] for item in right)
        side = "SSL"
    inside = context_low - point <= level <= context_high + point
    existing = {str(item["liquidityBarId"]): item for item in monitor.get("candidates", [])}
    completed = set(str(item) for item in monitor.get("completedLiquidityBarIds", []))
    if pivot and unswept and reacted and inside and row["barId"] not in completed:
        existing[row["barId"]] = {
            "liquidityBarId": row["barId"], "timeUtc": utc_text(row["time"]),
            "availableAtUtc": utc_text(row["available"]),
            "qualifiedAtUtc": utc_text(history[-1]["available"]),
            "side": side, "level": level,
        }
    ordered = sorted(existing.values(), key=lambda item: parse_utc(item["timeUtc"]))[-12:]
    return {**monitor, "candidates": ordered}


def append_m5_correction_reference(
    market: MarketData,
    candidates: list[dict[str, Any]],
    direction: str,
    as_of: int,
    frozen_at: int,
) -> list[dict[str, Any]]:
    rows = [row for row in market.bars("M5", as_of, 3) if row["available"] >= frozen_at]
    if len(rows) < 3:
        return candidates
    previous, row, following = rows
    if direction == "LONG":
        pivot = row["high"] > previous["high"] and row["high"] >= following["high"]
        reacted = following["low"] < row["low"]
        side, level = "CORRECTION_HIGH", row["high"]
    else:
        pivot = row["low"] < previous["low"] and row["low"] <= following["low"]
        reacted = following["high"] > row["high"]
        side, level = "CORRECTION_LOW", row["low"]
    if pivot and reacted and all(item["barId"] != row["barId"] for item in candidates):
        candidates = [*candidates, {
            "barId": row["barId"], "timeUtc": utc_text(row["time"]),
            "side": side, "level": level, "confirmedByBarId": following["barId"],
        }][-12:]
    return candidates


def current_choch_break_candidates(
    market: MarketData,
    scenario: dict[str, Any],
    row: dict[str, Any],
    sweep_events: list[dict[str, Any]],
    choch_candidates: list[dict[str, Any]],
    correction_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    direction = scenario["direction"]
    output: list[dict[str, Any]] = []
    directional_body = row["close"] > row["open"] if direction == "LONG" else row["close"] < row["open"]
    if not directional_body:
        return output
    broken_references = [
        item for item in choch_candidates
        if (row["close"] > float(item["level"]) if direction == "LONG" else row["close"] < float(item["level"]))
    ]
    broken_corrections = [
        item for item in correction_candidates
        if (row["close"] > float(item["level"]) if direction == "LONG" else row["close"] < float(item["level"]))
    ]
    if not broken_references or not broken_corrections:
        return output
    eligible_sweeps = [
        item for item in sweep_events
        if row["time"] > int(str(item["recoveryBarId"]).split(":", 1)[1])
    ]
    if not eligible_sweeps:
        return output
    sweep = max(
        eligible_sweeps,
        key=lambda item: int(str(item["recoveryBarId"]).split(":", 1)[1]),
    )
    correction = max(
        broken_corrections,
        key=lambda item: int(str(item["barId"]).split(":", 1)[1]),
    )
    reference = (
        max(broken_references, key=lambda item: (float(item["level"]), int(str(item["barId"]).split(":", 1)[1])))
        if direction == "LONG" else
        min(broken_references, key=lambda item: (float(item["level"]), -int(str(item["barId"]).split(":", 1)[1])))
    )
    return [{
        "liquidityBarId": str(sweep["liquidityBarId"]),
        "sweepExcursionBarId": str(sweep["excursionBarId"]),
        "sweepRecoveryBarId": str(sweep["recoveryBarId"]),
        "referenceBarId": reference["barId"],
        "m5CorrectionSwingBarId": correction["barId"],
        "breakBarId": row["barId"],
        "detectedAtUtc": utc_text(row["available"]),
    }]


def prefilter_scenarios(
    market: MarketData,
    scenarios: list[dict[str, Any]],
    follow_end: int,
) -> tuple[list[tuple[int, dict[str, Any]]], list[dict[str, Any]]]:
    audit: list[dict[str, Any]] = []
    earliest_physical: dict[tuple[str, ...], tuple[int, dict[str, Any]]] = {}
    for number, scenario in enumerate(scenarios, 1):
        key = physical_scenario_key(scenario)
        prior = earliest_physical.get(key)
        if prior is None or parse_utc(scenario["frozenAtUtc"]) < parse_utc(prior[1]["frozenAtUtc"]):
            earliest_physical[key] = (number, scenario)

    selected_numbers = {number for number, _ in earliest_physical.values()}
    survivors: list[tuple[int, dict[str, Any]]] = []
    for number, scenario in enumerate(scenarios, 1):
        if number not in selected_numbers:
            result = {
                "status": "REJECT", "reason": "DUPLICATE_PHYSICAL_SCENARIO_LATER_FREEZE",
                "eventAtUtc": scenario["frozenAtUtc"], "eventBarId": "",
            }
        else:
            result = prefilter_scenario(market, scenario, follow_end)
            if result["status"] == "KEEP":
                survivors.append((number, scenario))
        audit.append({
            "benchmarkId": f"J26-B-{number:04d}",
            "semanticHash": scenario["semanticHash"],
            "frozenAtUtc": scenario["frozenAtUtc"],
            "direction": scenario["direction"], "scope": scenario["scope"],
            "rootObBarId": scenario["root"]["obBarId"],
            "finalChildObBarId": scenario["finalChild"]["obBarId"],
            "objectiveBarId": scenario["objective"]["barId"],
            **result,
        })
    return survivors, audit


def formal_scenarios(market: MarketData, schedule: list[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scenarios: dict[str, dict[str, Any]] = {}
    rejections: list[dict[str, Any]] = []
    for number, as_of in enumerate(schedule, 1):
        print(f"[PLAN {number:02d}/{len(schedule):02d}] {utc_text(as_of)}", flush=True)
        packet = build_plan_packet(market, as_of, "GOLD")
        for selection_id in sorted(_atomic_scenario_options(packet)):
            payload = {
                "schemaVersion": "4.11.0",
                "action": "PLAN",
                "scenarioSelectionId": selection_id,
                "semanticAudit": {key: "PASS" for key in PLAN_SEMANTIC_AUDIT_KEYS},
                "reason": "Oracle formal enumeration; pending independent chart semantic audit.",
            }
            try:
                scenario = freeze_plan(payload, market, as_of, packet=packet)
            except V4ContractError as exc:
                rejections.append({
                    "stage": "FORMAL_PLAN", "asOfUtc": utc_text(as_of),
                    "selectionId": selection_id, "reason": str(exc),
                })
                continue
            if scenario is not None and scenario["semanticHash"] not in scenarios:
                scenario["sourceSelectionId"] = selection_id
                scenarios[scenario["semanticHash"]] = scenario
    return list(scenarios.values()), rejections


def simulate_order(
    market: MarketData,
    scenario: dict[str, Any],
    order: dict[str, Any],
    start_at: int,
    end_at: int,
) -> dict[str, Any]:
    position = None
    for row in rows_after(market, start_at, end_at):
        if position is None:
            cancel = local_scenario_cancel_reason(market, scenario, row)
            if cancel:
                return {"status": "CANCELED", "closedAtUtc": utc_text(row["available"]), "reason": cancel}
            status, position = advance_pending(market, order, row)
            if status == "WAIT":
                continue
            if status != "FILLED":
                return {"status": status, "closedAtUtc": utc_text(row["available"]), "reason": status}
        else:
            closed = advance_position(market, position, row)
            if closed:
                return {"status": closed["outcome"], "trade": closed}
    return {"status": "OPEN_AT_FOLLOW_END", "trade": position}


def simulate_scenario(
    market: MarketData,
    scenario: dict[str, Any],
    entry_end: int,
    follow_end: int,
) -> dict[str, Any]:
    frozen = parse_utc(scenario["frozenAtUtc"])
    monitor = None
    touched = dict(scenario)
    used_breaks: set[str] = set()
    post_touch_m1: list[dict[str, Any]] = []
    reaction_m1: list[dict[str, Any]] = []
    choch_candidates: list[dict[str, Any]] = []
    correction_candidates: list[dict[str, Any]] = []
    m1_history = market.frames["M1"]
    for row in rows_after(market, frozen, entry_end):
        direction = touched["direction"]
        child = touched["finalChild"]
        child_consumed = (
            row["low"] <= child["distal"]
            if direction == "LONG" else row["high"] >= child["distal"]
        )
        if monitor is not None and child_consumed:
            return {
                "status": "CANCELED", "closedAtUtc": utc_text(row["available"]),
                "reason": "POI_FULLY_CONSUMED",
            }
        if monitor is not None and row["available"] % 900 == 0:
            cancel = local_scenario_cancel_reason(market, touched, row)
            if cancel:
                return {"status": "CANCELED", "closedAtUtc": utc_text(row["available"]), "reason": cancel}
        if monitor is None:
            objective_hit = (
                row["high"] >= touched["objective"]["price"]
                if direction == "LONG" else row["low"] <= touched["objective"]["price"]
            )
            if objective_hit:
                return {"status": "CANCELED", "closedAtUtc": utc_text(row["available"]), "reason": "OBJECTIVE_REACHED_BEFORE_FILL"}
            if row["available"] % 900 == 0:
                cancel = local_scenario_cancel_reason(market, touched, row)
                if cancel:
                    return {"status": "CANCELED", "closedAtUtc": utc_text(row["available"]), "reason": cancel}

            index = int(row["index"])
            is_directional_fvg = False
            if index >= 2:
                first_high = float(m1_history.high[index - 2])
                first_low = float(m1_history.low[index - 2])
                is_directional_fvg = (
                    row["low"] > first_high and row["close"] > row["open"]
                    if direction == "LONG"
                    else row["high"] < first_low and row["close"] < row["open"]
                )
            replacement = (
                detect_pre_touch_delivery_candidate(market, touched, row, 0.0)
                if is_directional_fvg else None
            )
            if replacement is not None and replacement["status"] == "WAIT_FIRST_RETEST":
                candidate = replacement
                for future in rows_after(market, row["available"], follow_end):
                    candidate, event = advance_shadow_delivery_candidate(market, candidate, future)
                    if event in {"TP", "SL", "OBJECTIVE_FIRST", "THROUGH_DELIVERY", "INVALIDATED"}:
                        return {"status": candidate["status"], "replacement": candidate}
                return {"status": candidate["status"], "replacement": candidate}

            if zone_touched(row, touched["finalChild"]):
                if child_consumed:
                    return {
                        "status": "CANCELED", "closedAtUtc": utc_text(row["available"]),
                        "reason": "POI_FULLY_CONSUMED_AT_FIRST_TOUCH",
                    }
                touched["childTouchAtUtc"] = utc_text(row["available"])
                touched["childTouchBarId"] = row["barId"]
                monitor = build_reaction_monitor(market, touched, row["available"])
                post_touch_m1 = [row]
                reaction_m1 = market.bars("M1", row["available"], 5)
                correction_candidates = mechanical_m5_correction_swing_candidates(
                    market, touched, row["available"]
                )
            continue

        post_touch_m1.append(row)
        if len(post_touch_m1) > 3:
            post_touch_m1 = post_touch_m1[-3:]
        reaction_m1.append(row)
        if len(reaction_m1) > 5:
            reaction_m1 = reaction_m1[-5:]
        choch_candidates = append_m1_choch_reference(
            post_touch_m1, choch_candidates, touched["direction"]
        )
        monitor = append_reaction_liquidity_candidate(
            monitor, reaction_m1, touched, market.point
        )
        if row["available"] % 300 == 0:
            correction_candidates = append_m5_correction_reference(
                market, correction_candidates, touched["direction"], row["available"], frozen
            )
        monitor, new_sweeps = advance_reaction_monitor(monitor, row, touched["direction"])
        sweep_events = outermost_completed_sweep_events(monitor.get("sweepEvents", []))
        if not sweep_events:
            continue
        breaks = current_choch_break_candidates(
            market, touched, row, sweep_events, choch_candidates, correction_candidates
        )
        for chain in sorted(breaks, key=lambda item: parse_utc(item["detectedAtUtc"])):
            chain_id = "|".join(
                str(chain[key]) for key in (
                    "liquidityBarId", "referenceBarId", "m5CorrectionSwingBarId"
                )
            )
            if chain_id in used_breaks:
                continue
            used_breaks.add(chain_id)
            payload = {
                "schemaVersion": "4.8.0", "action": "ARM_REACTION",
                "matureLiquidityBarId": chain["liquidityBarId"],
                "m5CorrectionSwingBarId": chain["m5CorrectionSwingBarId"],
                "chochReferenceBarId": chain["referenceBarId"],
                "chochBreakBarId": chain["breakBarId"],
                "sourceUpgradeSelectionId": None,
                "reason": "Oracle formal trigger enumeration; pending chart semantic audit.",
            }
            try:
                watch = freeze_trigger_watch(
                    payload, market, row["available"], touched,
                    sweep_events=sweep_events,
                    liquidity_candidates=monitor.get("candidates", []),
                    choch_candidates=choch_candidates,
                    correction_candidates=correction_candidates,
                    choch_break_candidates=breaks,
                )
                break_bar = market.bar(chain["breakBarId"], row["available"])
                order = build_order(
                    market, touched, watch, watch["executionOb"], break_bar, 0.0
                )
            except V4ContractError:
                continue
            result = simulate_order(market, touched, order, row["available"], follow_end)
            return {**result, "order": order, "trigger": {
                "liquidityBarId": chain["liquidityBarId"],
                "sweepExcursionBarId": chain["sweepExcursionBarId"],
                "sweepRecoveryBarId": chain["sweepRecoveryBarId"],
                "m5CorrectionSwingBarId": chain["m5CorrectionSwingBarId"],
                "chochReferenceBarId": chain["referenceBarId"],
                "chochBreakBarId": chain["breakBarId"],
            }}
    return {"status": "NO_EXECUTION"}


def flatten_result(number: int, scenario: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    trade = result.get("trade") or {}
    replacement = result.get("replacement") or {}
    order = result.get("order") or {}
    return {
        "benchmarkId": f"J26-B-{number:04d}",
        "semanticHash": scenario["semanticHash"],
        "frozenAtUtc": scenario["frozenAtUtc"],
        "direction": scenario["direction"],
        "scope": scenario["scope"],
        "rootObBarId": scenario["root"]["obBarId"],
        "finalChildObBarId": scenario["finalChild"]["obBarId"],
        "objectiveBarId": scenario["objective"]["barId"],
        "objectivePrice": scenario["objective"]["price"],
        "status": result["status"],
        "executionModel": order.get("model") or ("DELIVERY_FVG_REPLACEMENT" if replacement else ""),
        "entryAtUtc": trade.get("entryAtUtc") or replacement.get("filledAtUtc") or "",
        "exitAtUtc": trade.get("exitAtUtc") or replacement.get("closedAtUtc") or result.get("closedAtUtc", ""),
        "entry": trade.get("entry") or replacement.get("entry") or order.get("entry", ""),
        "stop": trade.get("stop") or replacement.get("stop") or order.get("stop", ""),
        "target": trade.get("target") or replacement.get("target") or order.get("target", ""),
        "resultR": trade.get("resultR") if trade else replacement.get("resultR", ""),
        "reason": result.get("reason", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--schedule-ledger", type=Path, required=True)
    parser.add_argument("--move-index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--part", type=int)
    parser.add_argument("--parts", type=int, default=1)
    parser.add_argument("--only-number", type=int)
    parser.add_argument("--independent-plan-part", action="store_true")
    args = parser.parse_args()
    rates, audit = load_joined(args.first.resolve(), args.second.resolve())
    market = MarketData.from_rates(rates, 0.01)
    june_start = timestamp("2026-06-01T00:00:00Z")
    june_end = timestamp("2026-07-01T00:00:00Z")
    legacy_schedule = read_schedule(args.schedule_ledger.resolve())
    schedule = sorted(set(legacy_schedule) | set(
        oracle_review_schedule(args.move_index.resolve(), june_start, june_end)
    ))
    if args.independent_plan_part:
        if args.part is None:
            raise ValueError("--independent-plan-part requires --part")
        schedule = [
            value for index, value in enumerate(schedule)
            if index % args.parts == args.part
        ]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    independent_suffix = f".part{args.part:02d}" if args.independent_plan_part else ""
    scenario_cache = output / f"formal_scenario_index_v2_pretouch{independent_suffix}.json"
    if scenario_cache.exists():
        scenarios = json.loads(scenario_cache.read_text(encoding="utf-8"))
        formal_rejections = []
        print(f"[CACHE] formal scenarios={len(scenarios)}", flush=True)
    else:
        scenarios, formal_rejections = formal_scenarios(market, schedule)
        scenario_cache.write_text(
            json.dumps(scenarios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / f"formal_rejections{independent_suffix}.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in formal_rejections), encoding="utf-8"
        )
    follow_end = timestamp("2026-07-15T00:00:00Z")
    rows: list[dict[str, Any]] = []
    detailed: list[dict[str, Any]] = []
    prefilter_path = output / f"event_race_prefilter_v2_pretouch{independent_suffix}.csv"
    survivor_path = output / f"event_race_survivors_v2_pretouch{independent_suffix}.json"
    if prefilter_path.exists() and survivor_path.exists():
        with prefilter_path.open(encoding="utf-8-sig") as handle:
            prefilter_audit = list(csv.DictReader(handle))
        survivor_numbers = set(json.loads(survivor_path.read_text(encoding="utf-8")))
        indexed_scenarios = [
            (number, scenario) for number, scenario in enumerate(scenarios, 1)
            if number in survivor_numbers
        ]
    else:
        indexed_scenarios, prefilter_audit = prefilter_scenarios(market, scenarios, follow_end)
        survivor_path.write_text(
            json.dumps([number for number, _ in indexed_scenarios], indent=2) + "\n",
            encoding="utf-8",
        )
    if prefilter_audit and not prefilter_path.exists():
        with prefilter_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(prefilter_audit[0]))
            writer.writeheader()
            writer.writerows(prefilter_audit)
    print(
        f"[PREFILTER] formal={len(scenarios)} clean-touch={len(indexed_scenarios)} "
        f"rejected={len(scenarios) - len(indexed_scenarios)}",
        flush=True,
    )
    if args.part is not None and not args.independent_plan_part:
        indexed_scenarios = [
            item for item in indexed_scenarios
            if (item[0] - 1) % args.parts == args.part
        ]
    if args.only_number is not None:
        indexed_scenarios = [item for item in indexed_scenarios if item[0] == args.only_number]
    for progress, (number, scenario) in enumerate(indexed_scenarios, 1):
        print(f"[REPLAY {progress:04d}/{len(indexed_scenarios):04d}] #{number:04d} {scenario['frozenAtUtc']}", flush=True)
        result = simulate_scenario(market, scenario, june_end, follow_end)
        detailed.append({"scenario": scenario, "result": result})
        rows.append(flatten_result(number, scenario, result))

    suffix = f".part{args.part:02d}" if args.part is not None else ""
    (output / f"formal_scenarios{suffix}.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in detailed), encoding="utf-8"
    )
    fields = list(rows[0]) if rows else []
    with (output / f"formal_results{suffix}.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    trades = [row for row in rows if row["status"] in {"TP", "SL"}]
    total_r = sum(float(row["resultR"]) for row in trades)
    summary = {
        "dataAudit": audit,
        "scheduleEvents": len(schedule),
        "uniqueFormalScenarios": len(scenarios),
        "cleanChildTouchScenarios": sum(item["status"] == "KEEP" for item in prefilter_audit),
        "prefilterRejected": sum(item["status"] == "REJECT" for item in prefilter_audit),
        "formalPlanRejections": len(formal_rejections),
        "formalTradesBeforeSemanticAudit": len(trades),
        "formalWins": sum(row["status"] == "TP" for row in trades),
        "formalLosses": sum(row["status"] == "SL" for row in trades),
        "formalTotalR": total_r,
        "warning": "Not ground truth until every trade and same-rule no-trade passes chart semantic audit.",
    }
    (output / f"formal_summary{suffix}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
