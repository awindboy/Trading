"""Discover mentor scenarios without portfolio-level mutual exclusion.

The runtime reads only OHLC/spread. Each confirmed map-event/objective path
owns its own state; portfolio limits are deliberately left to a later layer.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import copy
import csv
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz, parse_utc
from mentor_engine.structure import analyze_structure
from mentor_rule_engine import EngineConfig, MentorRuleEngine, RuleCandidate
from scripts.run_mentor_blind_week_v5 import (
    adaptive_dealing_range,
    candidate_rank,
    choose_objective,
    delivered_preexisting_liquidity,
    find_map_root_source,
    has_directional_m5_fvg,
    has_new_m5_correction,
    map_event_at,
    max_drawdown,
    position_in_profit,
    position_open,
    simulate_trade,
    source_created_displacement_fvg,
)


DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = ROOT / "output" / os.environ.get(
    "MENTOR_OUTPUT",
    "mentor_scenario_week_2025-07-07_11_v6",
)
WARMUP_FROM = os.environ.get("MENTOR_WARMUP_FROM", "2025-06-15T00:00:00Z")
TRADE_FROM = os.environ.get("MENTOR_TRADE_FROM", "2025-07-07T00:00:00Z")
TRADE_TO = os.environ.get("MENTOR_TRADE_TO", "2025-07-12T00:00:00Z")
OBSERVE_TO = os.environ.get("MENTOR_OBSERVE_TO", "2025-07-15T00:00:00Z")
POINT = 0.01


def ts(value: str) -> int:
    parsed = parse_utc(value)
    if parsed is None:
        raise ValueError(value)
    return parsed


def iso(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def spread_at(m1: Any, timestamp: int) -> float:
    index = int(
        np.searchsorted(m1.available_time, timestamp, side="right") - 1
    )
    if index < 0:
        return POINT
    return max(POINT, float(m1.spread_points[index]) * POINT)


def delivery_addon_stop(
    candidate: RuleCandidate,
    m1: Any,
    after: int,
    m5_analysis: Any,
) -> float:
    """Use the causal correction candle, not the original HTF reaction."""
    end = int(np.searchsorted(m1.time, candidate.created_at, side="left"))
    start = max(
        0,
        int(np.searchsorted(m1.time, after, side="left")),
        end - 45,
    )
    opposite: int | None = None
    for index in range(end - 1, start - 1, -1):
        bullish = float(m1.close[index]) > float(m1.open[index])
        bearish = float(m1.close[index]) < float(m1.open[index])
        if (
            candidate.direction == "short"
            and bullish
            or candidate.direction == "long"
            and bearish
        ):
            opposite = index
            break
    if opposite is None:
        local_boundary = candidate.fvg_top if candidate.direction == "short" else candidate.fvg_bottom
    else:
        local_boundary = (
            float(m1.high[opposite])
            if candidate.direction == "short"
            else float(m1.low[opposite])
        )
    wave_side = "high" if candidate.direction == "short" else "low"
    confirmed_waves = [
        wave
        for wave in m5_analysis.waves
        if (
            wave.side.value == wave_side
            and after < wave.available_at <= candidate.created_at
        )
    ]
    protected_correction = (
        confirmed_waves[-1].level if confirmed_waves else local_boundary
    )
    buffer = spread_at(m1, candidate.created_at)
    if candidate.direction == "short":
        return max(
            local_boundary + buffer,
            protected_correction + buffer,
            candidate.fvg_top + buffer,
        )
    return min(
        local_boundary - buffer,
        protected_correction - buffer,
        candidate.fvg_bottom - buffer,
    )


def scenario_key(
    map_root: Any,
    candidate: RuleCandidate,
    objective: dict[str, Any],
) -> tuple[str, str]:
    return (
        candidate.parent_source_id,
        candidate.direction,
    )


def delivered_beyond_owner_source(
    candidate: RuleCandidate,
    owner: dict[str, Any],
) -> bool:
    width = float(owner["parentTop"]) - float(owner["parentBottom"])
    if candidate.direction == "short":
        return candidate.entry < float(owner["parentBottom"]) - width
    return candidate.entry > float(owner["parentTop"]) + width


def meaningful_trigger_liquidity(
    candidate: RuleCandidate,
    sweeps: dict[str, Any],
    pivots: dict[str, Any],
    m1: Any,
) -> str | None:
    sweep = sweeps[candidate.sweep_id]
    pivot = pivots[sweep.pivot_id]
    prior = [
        item
        for item in pivots.values()
        if (
            item.side == pivot.side
            and pivot.index - 90 <= item.index < pivot.index
        )
    ]
    spread = max(
        POINT,
        float(m1.spread_points[pivot.index]) * POINT,
    )
    if any(abs(item.level - pivot.level) <= spread for item in prior):
        return "EQUAL_LEVEL"
    start = max(0, pivot.index - 90)
    if pivot.side == "high":
        is_external = pivot.level >= float(
            np.max(m1.high[start : pivot.index + 1])
        )
    else:
        is_external = pivot.level <= float(
            np.min(m1.low[start : pivot.index + 1])
        )
    return "LOCAL_EXTERNAL" if is_external else None


def objective_delivered(
    direction: str,
    level: float,
    start_at: int,
    end_at: int,
    m1: Any,
) -> bool:
    start = int(np.searchsorted(m1.time, start_at, side="left"))
    end = int(np.searchsorted(m1.time, end_at, side="left"))
    if end <= start:
        return False
    if direction == "short":
        return bool(np.any(m1.low[start:end] <= level))
    return bool(np.any(m1.high[start:end] >= level))


def collapse_fvg_families(
    candidates: list[RuleCandidate],
    fvgs: dict[str, Any],
    m1: Any,
) -> list[RuleCandidate]:
    grouped: dict[tuple[str, int, int], list[RuleCandidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[
            (
                candidate.parent_source_id,
                candidate.sweep_at,
                candidate.shift_at,
            )
        ].append(candidate)
    selected: list[RuleCandidate] = []
    for family in grouped.values():
        family.sort(key=lambda item: item.created_at)
        first = family[0]
        current = first
        previous_created = current.created_at
        for candidate in family[1:]:
            if candidate.created_at != previous_created + 60:
                break
            fvg = fvgs[candidate.fvg_id]
            directional_close = (
                float(m1.close[fvg.confirmed_index])
                < float(m1.open[fvg.confirmed_index])
                if candidate.direction == "short"
                else float(m1.close[fvg.confirmed_index])
                > float(m1.open[fvg.confirmed_index])
            )
            if not directional_close:
                break
            current = candidate
            previous_created = candidate.created_at
        # Keep the first zone as the CHoCH-owned FVG. A consecutive,
        # directional gap is also retained as its pending refinement; the
        # decision-time state machine decides whether it replaces the first.
        selected.append(first)
        if current.candidate_id != first.candidate_id:
            selected.append(current)
    return sorted(
        selected,
        key=lambda item: (int(item.retest_at or 0), item.created_at),
    )


def collapse_reaction_episodes(
    candidates: list[RuleCandidate],
    sources: dict[str, Any],
) -> list[RuleCandidate]:
    """Keep one base reaction plus genuine delivery entries per sweep."""
    grouped: dict[tuple[str, str, int], list[RuleCandidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[
            (
                candidate.parent_source_id,
                candidate.direction,
                candidate.sweep_at,
            )
        ].append(candidate)
    selected: list[RuleCandidate] = []
    for family in grouped.values():
        family.sort(key=lambda item: item.created_at)
        base = family[0]
        selected.append(base)
        parent = sources[base.parent_source_id]
        width = parent.top - parent.bottom
        for candidate in family[1:]:
            delivered = (
                candidate.entry < parent.bottom - width
                if candidate.direction == "short"
                else candidate.entry > parent.top + width
            )
            if delivered:
                selected.append(candidate)
    return sorted(
        selected,
        key=lambda item: (int(item.retest_at or 0), item.created_at),
    )


def main() -> int:
    m1, metadata = load_m1_npz(
        DATASET,
        ts(WARMUP_FROM),
        ts(OBSERVE_TO),
    )
    frames = build_timeframes(m1)
    analyses = {
        timeframe: analyze_structure(frames[timeframe])
        for timeframe in ("H1", "M30", "M15", "M5")
    }
    result = MentorRuleEngine(frames).run(
        ts(TRADE_FROM),
        ts(TRADE_TO),
    )
    sources = {source.source_id: source for source in result.sources}
    sweeps = {sweep.sweep_id: sweep for sweep in result.sweeps}
    fvgs = {fvg.fvg_id: fvg for fvg in result.fvgs}
    trigger_pivots = {
        pivot.pivot_id: pivot
        for pivot in MentorRuleEngine(frames)._detect_pivots()
    }
    map_sources = MentorRuleEngine(
        frames,
        EngineConfig(source_timeframes=("H1", "M30")),
    )._detect_sources()
    raw_evidence = [
        candidate
        for candidate in result.authorized_candidates
        if (
            candidate.retest_at is not None
            and ts(TRADE_FROM) <= candidate.retest_at < ts(TRADE_TO)
        )
    ]
    evidence = collapse_fvg_families(raw_evidence, fvgs, m1)
    by_decision: dict[int, list[RuleCandidate]] = defaultdict(list)
    for candidate in evidence:
        by_decision[candidate.created_at].append(candidate)

    owners: dict[tuple[str, ...], dict[str, Any]] = {}
    trades: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    used_chains: set[tuple[Any, ...]] = set()
    owner_sequence = 0

    def log_verdict(
        candidate: RuleCandidate,
        at: int,
        verdict: str,
        **details: Any,
    ) -> None:
        audit.append(
            {
                "at": iso(at),
                "candidateId": candidate.candidate_id,
                "verdict": verdict,
                **details,
            }
        )

    def directional_progress(
        direction: str,
        candidate_entry: float,
        prior_entry: float,
    ) -> bool:
        return (
            candidate_entry < prior_entry
            if direction == "short"
            else candidate_entry > prior_entry
        )

    def beyond_source(candidate: RuleCandidate, source: Any) -> bool:
        width = source.top - source.bottom
        return (
            candidate.entry < source.bottom - width
            if candidate.direction == "short"
            else candidate.entry > source.top + width
        )

    def flush_pending(until: int) -> None:
        due: list[
            tuple[int, tuple[str, ...], dict[str, Any], dict[str, Any]]
        ] = []
        for key, owner in owners.items():
            for pending in owner.get("pendings", []):
                fill_at = int(pending["candidate"].retest_at or 0)
                if fill_at <= until:
                    due.append((fill_at, key, owner, pending))
        due.sort(key=lambda item: (item[0], item[3]["candidate"].created_at))
        for fill_at, _, owner, pending in due:
            if pending not in owner.get("pendings", []):
                continue
            candidate = pending["candidate"]
            source = sources[candidate.source_id]
            if source.invalidated_at is not None and source.invalidated_at <= fill_at:
                owner["pendings"].remove(pending)
                log_verdict(
                    candidate,
                    fill_at,
                    "CANCEL_PENDING_SOURCE_INVALIDATED",
                    ownerId=owner["ownerId"],
                )
                continue
            if objective_delivered(
                candidate.direction,
                float(owner["objective"]),
                candidate.created_at,
                fill_at,
                m1,
            ):
                owner["pendings"].remove(pending)
                log_verdict(
                    candidate,
                    fill_at,
                    "CANCEL_PENDING_OBJECTIVE_DELIVERED",
                    ownerId=owner["ownerId"],
                )
                continue
            model = str(pending["model"])
            if model == "DELIVERY_FVG_ADDON":
                active = [
                    trade
                    for trade in trades
                    if (
                        trade["ownerId"] == owner["ownerId"]
                        and position_open(trade, fill_at)
                    )
                ]
                if not active or not any(
                    position_in_profit(trade, m1, fill_at)
                    for trade in active
                ):
                    owner["pendings"].remove(pending)
                    log_verdict(
                        candidate,
                        fill_at,
                        "CANCEL_ADDON_WITHOUT_LIVE_WINNER",
                        ownerId=owner["ownerId"],
                    )
                    continue
            execution = copy.copy(candidate)
            if model == "DELIVERY_FVG_ADDON":
                base_attempts = [
                    trade
                    for trade in trades
                    if (
                        trade["ownerId"] == owner["ownerId"]
                        and trade["entryModel"] != "DELIVERY_FVG_ADDON"
                    )
                ]
                if not base_attempts:
                    owner["pendings"].remove(pending)
                    log_verdict(
                        candidate,
                        fill_at,
                        "CANCEL_ADDON_WITHOUT_BASE_ATTEMPT",
                        ownerId=owner["ownerId"],
                    )
                    continue
                execution.stop = delivery_addon_stop(
                    execution,
                    m1,
                    ts(base_attempts[-1]["filledAt"]),
                    analyses["M5"],
                )
            trade = simulate_trade(
                m1,
                execution,
                float(owner["objective"]),
                f"SCENARIO-V6-{len(trades) + 1:03d}",
                model,
                str(owner["ownerId"]),
            )
            trade["candidateId"] = candidate.candidate_id
            trade["mapRootSourceId"] = pending["mapRoot"].source_id
            trade["mapEventId"] = owner["mapRootSourceId"]
            trade["shiftReferenceKind"] = candidate.shift_reference_kind
            trade["sourceBottom"] = candidate.source_bottom
            trade["sourceTop"] = candidate.source_top
            parent = sources[candidate.parent_source_id]
            trade["parentBottom"] = parent.bottom
            trade["parentTop"] = parent.top
            trade["fvgBottom"] = candidate.fvg_bottom
            trade["fvgTop"] = candidate.fvg_top
            trade["sweepExtreme"] = candidate.sweep_extreme
            trade["shiftReference"] = candidate.shift_reference
            trade["objectiveId"] = owner["objectiveId"]
            trade["mapRootTimeframe"] = pending["mapRoot"].timeframe
            trade["mapRootBottom"] = pending["mapRoot"].bottom
            trade["mapRootTop"] = pending["mapRoot"].top
            trades.append(trade)
            owner["pendings"].remove(pending)
            owner["lastFilledAt"] = fill_at
            log_verdict(
                candidate,
                fill_at,
                "SCENARIO_FILLED",
                tradeId=trade["tradeId"],
                ownerId=owner["ownerId"],
                entryModel=model,
            )

    for at in sorted(by_decision):
        flush_pending(at)
        proposals: dict[
            tuple[str, ...],
            list[
                tuple[
                    RuleCandidate,
                    dict[str, Any],
                    str,
                    Any,
                    dict[str, Any] | None,
                ]
            ],
        ] = defaultdict(list)
        for candidate in by_decision[at]:
            chain = (
                candidate.parent_source_id,
                candidate.sweep_at,
                candidate.shift_at,
                candidate.fvg_id,
            )
            if chain in used_chains:
                log_verdict(candidate, at, "REJECT_DUPLICATE_PHYSICAL_CHAIN")
                continue
            source = sources[candidate.source_id]
            parent = sources[candidate.parent_source_id]
            if parent.timeframe != "M15":
                log_verdict(candidate, at, "REJECT_NO_M15_CAUSAL_PARENT")
                continue
            if not source_created_displacement_fvg(parent, frames):
                log_verdict(
                    candidate,
                    at,
                    "REJECT_PARENT_WITHOUT_DISPLACEMENT_FVG",
                )
                continue
            trigger_liquidity = meaningful_trigger_liquidity(
                candidate,
                sweeps,
                trigger_pivots,
                m1,
            )
            if trigger_liquidity is None:
                log_verdict(candidate, at, "REJECT_RECENT_PIVOT_ONLY")
                continue
            if source.invalidated_at is not None and source.invalidated_at <= at:
                log_verdict(candidate, at, "REJECT_SOURCE_INVALIDATED")
                continue
            map_root = find_map_root_source(
                candidate,
                sources,
                map_sources,
                frames,
            )
            if map_root is None:
                log_verdict(candidate, at, "REJECT_NO_HTF_OB_LINEAGE")
                continue
            if adaptive_dealing_range(candidate, frames, analyses) is None:
                log_verdict(candidate, at, "REJECT_WRONG_DEALING_RANGE_HALF")
                continue
            objective = choose_objective(candidate, m1, at)
            if objective is None:
                log_verdict(candidate, at, "REJECT_NO_CAUSAL_OBJECTIVE")
                continue
            key = scenario_key(map_root, candidate, objective)
            owner = owners.get(key)
            model = "HTF_OB_REACTION"
            replacement: dict[str, Any] | None = None
            if owner is None:
                delivery_owners: list[dict[str, Any]] = []
                for candidate_owner in owners.values():
                    if (
                        candidate_owner["mapRootSourceId"] != map_root.source_id
                        or candidate_owner["direction"] != candidate.direction
                        or (
                            candidate.direction == "short"
                            and float(candidate_owner["objective"])
                            >= candidate.entry
                        )
                        or (
                            candidate.direction == "long"
                            and float(candidate_owner["objective"])
                            <= candidate.entry
                        )
                        or not delivered_beyond_owner_source(
                            candidate,
                            candidate_owner,
                        )
                    ):
                        continue
                    active_positions = [
                        trade
                        for trade in trades
                        if (
                            trade["ownerId"] == candidate_owner["ownerId"]
                            and position_open(trade, at)
                        )
                    ]
                    if active_positions and any(
                        position_in_profit(trade, m1, at)
                        for trade in active_positions
                    ):
                        delivery_owners.append(candidate_owner)
                if delivery_owners:
                    owner = max(
                        delivery_owners,
                        key=lambda item: int(item["lastDecisionAt"]),
                    )
                    key = tuple(owner["scenarioKey"])
                    model = "DELIVERY_FVG_ADDON"
            if owner is not None:
                objective_delta = abs(
                    float(owner["objective"]) - float(objective["level"])
                )
                if model == "DELIVERY_FVG_ADDON":
                    if objective_delta > POINT:
                        log_verdict(
                            candidate,
                            at,
                            "INHERIT_LIVE_OWNER_OBJECTIVE",
                            ownerId=owner["ownerId"],
                            ignoredCandidateObjective=objective["level"],
                            inheritedObjective=owner["objective"],
                        )
                elif objective_delta > POINT:
                    cluster_width = spread_at(m1, candidate.created_at)
                    if objective_delta <= cluster_width:
                        log_verdict(
                            candidate,
                            at,
                            "REFINE_OBJECTIVE_CLUSTER_EDGE",
                            ownerId=owner["ownerId"],
                            previousObjective=owner["objective"],
                            refinedObjective=objective["level"],
                        )
                        owner["objective"] = float(objective["level"])
                        owner["objectiveId"] = str(objective["id"])
                    elif objective_delivered(
                        candidate.direction,
                        float(owner["objective"]),
                        int(owner["createdAt"]),
                        at,
                        m1,
                    ):
                        for pending in owner.get("pendings", []):
                            log_verdict(
                                pending["candidate"],
                                at,
                                "CANCEL_PENDING_RETIRED_OBJECTIVE",
                                ownerId=owner["ownerId"],
                            )
                        log_verdict(
                            candidate,
                            at,
                            "RETIRE_DELIVERED_OBJECTIVE",
                            ownerId=owner["ownerId"],
                            deliveredObjective=owner["objective"],
                        )
                        del owners[key]
                        owner = None
                    else:
                        log_verdict(
                            candidate,
                            at,
                            "REJECT_OWNER_OBJECTIVE_CHANGED",
                            ownerId=owner["ownerId"],
                            frozenObjective=owner["objective"],
                            candidateObjective=objective["level"],
                        )
                        continue
            if owner is not None:
                owner_trades = [
                    trade
                    for trade in trades
                    if trade["ownerId"] == owner["ownerId"]
                ]
                active = [
                    trade for trade in owner_trades if position_open(trade, at)
                ]
                base_pending = [
                    pending
                    for pending in owner.get("pendings", [])
                    if pending["model"] != "DELIVERY_FVG_ADDON"
                ]
                if model != "DELIVERY_FVG_ADDON" and base_pending:
                    prior_pending = base_pending[-1]
                    prior_candidate = prior_pending["candidate"]
                    same_reaction = (
                        candidate.parent_source_id
                        == prior_candidate.parent_source_id
                        and candidate.sweep_at == prior_candidate.sweep_at
                    )
                    progresses = directional_progress(
                        candidate.direction,
                        candidate.entry,
                        prior_candidate.entry,
                    )
                    prior_source = sources[prior_candidate.source_id]
                    if (
                        same_reaction
                        and progresses
                        and not beyond_source(prior_candidate, prior_source)
                        and not beyond_source(candidate, source)
                    ):
                        replacement = prior_pending
                        model = str(prior_pending["model"])
                    elif candidate.sweep_at != prior_candidate.sweep_at and not active:
                        replacement = prior_pending
                        model = "HTF_OB_REARM"
                    else:
                        log_verdict(
                            candidate,
                            at,
                            "REJECT_PENDING_REACTION_ALREADY_DEFINED",
                            ownerId=owner["ownerId"],
                            pendingCandidateId=prior_candidate.candidate_id,
                        )
                        continue
                elif model != "DELIVERY_FVG_ADDON":
                    if candidate.sweep_at == owner["lastSweepAt"]:
                        if (
                            active
                            and delivered_beyond_owner_source(candidate, owner)
                            and any(
                                position_in_profit(trade, m1, at)
                                for trade in active
                            )
                        ):
                            model = "DELIVERY_FVG_ADDON"
                        else:
                            log_verdict(
                                candidate,
                                at,
                                "REJECT_SAME_REACTION_EPISODE",
                                ownerId=owner["ownerId"],
                            )
                            continue
                    else:
                        model = "HTF_OB_REARM"
                        if active:
                            base_attempts = [
                                trade
                                for trade in owner_trades
                                if trade["entryModel"] != "DELIVERY_FVG_ADDON"
                            ]
                            active_winner = any(
                                position_in_profit(trade, m1, at)
                                for trade in active
                            )
                            prior_entry = (
                                float(base_attempts[-1]["entry"])
                                if base_attempts
                                else candidate.entry
                            )
                            required_progress = (
                                directional_progress(
                                    candidate.direction,
                                    candidate.entry,
                                    prior_entry,
                                )
                                if active_winner
                                else directional_progress(
                                    candidate.direction,
                                    prior_entry,
                                    candidate.entry,
                                )
                            )
                            if base_attempts and not required_progress:
                                log_verdict(
                                    candidate,
                                    at,
                                    "REJECT_ACTIVE_REARM_WITHOUT_PROGRESS",
                                    ownerId=owner["ownerId"],
                                    priorEntry=prior_entry,
                                    activeWinner=active_winner,
                                )
                                continue
                if model == "DELIVERY_FVG_ADDON" and (
                    not active
                    or not any(
                        position_in_profit(trade, m1, at)
                        for trade in active
                    )
                ):
                    log_verdict(
                        candidate,
                        at,
                        "REJECT_ADDON_WITHOUT_LIVE_WINNER",
                        ownerId=owner["ownerId"],
                    )
                    continue
            proposals[key].append(
                (candidate, objective, model, map_root, replacement)
            )
            log_verdict(
                candidate,
                at,
                "PROPOSAL",
                scenarioKey=list(key),
                entryModel=model,
                mapRootSourceId=map_root.source_id,
                triggerLiquidity=trigger_liquidity,
                replacesCandidateId=(
                    replacement["candidate"].candidate_id
                    if replacement is not None
                    else None
                ),
            )

        for key, options in proposals.items():
            options.sort(
                key=lambda item: candidate_rank(item[0]),
                reverse=True,
            )
            selected, objective, model, map_root, replacement = options[0]
            for rejected, _, rejected_model, _, _ in options[1:]:
                log_verdict(
                    rejected,
                    at,
                    "REJECT_LOWER_CAUSAL_RANK",
                    selectedCandidateId=selected.candidate_id,
                    entryModel=rejected_model,
                )
            owner = owners.get(key)
            if owner is None:
                parent = sources[selected.parent_source_id]
                owner_sequence += 1
                owner = {
                    "ownerId": f"SCN-V6-{owner_sequence:03d}",
                    "scenarioKey": list(key),
                    "direction": selected.direction,
                    "parentSourceId": selected.parent_source_id,
                    "parentBottom": parent.bottom,
                    "parentTop": parent.top,
                    "lastSweepAt": selected.sweep_at,
                    "lastDecisionAt": selected.created_at,
                    "lastShiftAt": selected.shift_at,
                    "createdAt": selected.created_at,
                    "objective": float(objective["level"]),
                    "objectiveId": str(objective["id"]),
                    "mapRootSourceId": map_root.source_id,
                    "pendings": [],
                }
                owners[key] = owner
            if replacement is not None and replacement in owner["pendings"]:
                owner["pendings"].remove(replacement)
                log_verdict(
                    replacement["candidate"],
                    at,
                    "REPLACE_PENDING_WITH_REFINED_REACTION",
                    ownerId=owner["ownerId"],
                    replacementCandidateId=selected.candidate_id,
                )
            owner["pendings"].append(
                {
                    "candidate": selected,
                    "objective": objective,
                    "model": model,
                    "mapRoot": map_root,
                }
            )
            owner["lastSweepAt"] = selected.sweep_at
            owner["lastDecisionAt"] = selected.created_at
            owner["lastShiftAt"] = selected.shift_at
            used_chains.add(
                (
                    selected.parent_source_id,
                    selected.sweep_at,
                    selected.shift_at,
                    selected.fvg_id,
                )
            )
            log_verdict(
                selected,
                at,
                "ORDER_PENDING",
                ownerId=owner["ownerId"],
                entryModel=model,
                plannedFillAt=iso(selected.retest_at),
            )

    flush_pending(ts(TRADE_TO))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    fields = list(trades[0]) if trades else ["tradeId", "result", "earnedR"]
    with (OUTPUT / "trades.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(trades)
    with (OUTPUT / "decision_audit.jsonl").open("w", encoding="utf-8") as handle:
        for row in audit:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    closed = [trade for trade in trades if trade["result"] in {"TP", "SL"}]
    wins = [trade for trade in closed if trade["result"] == "TP"]
    losses = [trade for trade in closed if trade["result"] == "SL"]
    values = [float(trade["earnedR"]) for trade in closed]
    gross_win = sum(float(trade["earnedR"]) for trade in wins)
    gross_loss = abs(sum(float(trade["earnedR"]) for trade in losses))
    summary = {
        "schema": "mentor-scenario-discovery-v6",
        "period": {"from": TRADE_FROM, "to": TRADE_TO},
        "casebookImported": False,
        "datasetMetadata": metadata,
        "engineAudit": result.audit,
        "retestEligibleEvidence": len(evidence),
        "rawRetestEligibleEvidence": len(raw_evidence),
        "scenarioOwners": len(owners),
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "open": len(trades) - len(closed),
        "winRate": len(wins) / len(closed) if closed else 0.0,
        "totalR": round(sum(values), 6),
        "profitFactor": (
            round(gross_win / gross_loss, 6) if gross_loss else None
        ),
        "maxDrawdownR": round(max_drawdown(values), 6),
        "entryModels": dict(Counter(t["entryModel"] for t in trades)),
        "rejectionCounts": dict(
            Counter(
                row["verdict"]
                for row in audit
                if row["verdict"] != "SCENARIO"
            )
        ),
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
