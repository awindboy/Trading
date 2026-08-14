"""Discover Mentor scenarios with an HTF thesis arbiter.

V6 proved that causal evidence recall is not the same as a trade decision.
V7 keeps the V6 evidence engine, but owns state by the frozen HTF objective,
compares competing directions, and refuses M1-only rearming after a failed
thesis.  Runtime inputs remain OHLC and spread only.
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

from mentor_engine.data import (
    build_timeframes,
    index_at_or_before,
    load_m1_npz,
    parse_utc,
)
from mentor_engine.structure import analyze_structure
from mentor_rule_engine import EngineConfig, MentorRuleEngine, RuleCandidate
from scripts.run_mentor_blind_week_v5 import (
    adaptive_dealing_range,
    candidate_rank,
    choose_objective,
    delivered_preexisting_liquidity,
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
    "mentor_scenario_week_2025-07-07_11_v7",
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
) -> tuple[str, int]:
    """One delivery path is one thesis, even when several M15 OBs overlap it."""
    return (
        candidate.direction,
        round(float(objective["level"]) / POINT),
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
    liquidity: list[Any],
    m1: Any,
) -> str | None:
    """Classify a pre-existing M1 reaction pool without inventing a level."""
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
        return "M1_EQUAL_REACTION_LEVEL"
    start = max(0, pivot.index - 90)
    if pivot.side == "high":
        is_reaction_edge = pivot.level >= float(
            np.max(m1.high[start : pivot.index + 1])
        )
    else:
        is_reaction_edge = pivot.level <= float(
            np.min(m1.low[start : pivot.index + 1])
        )
    return "M1_REACTION_EDGE" if is_reaction_edge else None


def map_root_dealing_range(
    candidate: RuleCandidate,
    map_root: Any,
    frames: dict[str, Any],
    analyses: dict[str, Any],
) -> dict[str, Any] | None:
    """Validate premium/discount on the timeframe that owns the thesis."""
    timeframe = map_root.timeframe
    series = frames[timeframe]
    analysis = analyses[timeframe]
    index = index_at_or_before(series, candidate.sweep_at)
    if index < 0:
        return None
    low = float(analysis.range_low[index])
    high = float(analysis.range_high[index])
    if not (np.isfinite(low) and np.isfinite(high) and high > low):
        return None
    equilibrium = (low + high) / 2.0
    source_midpoint = (float(map_root.bottom) + float(map_root.top)) / 2.0
    correct_half = (
        source_midpoint >= equilibrium
        if candidate.direction == "short"
        else source_midpoint <= equilibrium
    )
    if not correct_half:
        return None
    return {
        "timeframe": timeframe,
        "low": low,
        "high": high,
        "equilibrium": equilibrium,
    }


def map_root_wave_owner(
    map_root: Any,
    analysis: Any,
    known_at: int,
) -> Any | None:
    """Return the external swing whose wick region owns this HTF OB.

    An OB candle need not itself print the exact swing extreme. It does need to
    sit in the wick region of a confirmed external swing on the same timeframe.
    This preserves the mentor's swing-area interpretation without accepting an
    arbitrary opposite candle that merely displaced later.
    """
    required_side = "high" if map_root.direction == "short" else "low"
    owners = [
        wave
        for wave in analysis.waves
        if (
            wave.side.value == required_side
            and wave.rank == "external"
            and wave.available_at <= known_at
            and max(float(map_root.bottom), float(wave.wick_bottom))
            <= min(float(map_root.top), float(wave.wick_top))
        )
    ]
    if not owners:
        return None
    return max(
        owners,
        key=lambda wave: (
            int(wave.rank_available_at or wave.available_at),
            wave.available_at,
        ),
    )


def find_causal_map_root_source(
    candidate: RuleCandidate,
    execution_sources: dict[str, Any],
    map_sources: list[Any],
    analyses: dict[str, Any],
) -> tuple[Any, Any] | None:
    """Find the newest overlapping H1/M30 OB with a real swing owner."""
    parent = execution_sources[candidate.parent_source_id]
    options: list[tuple[Any, Any]] = []
    for source in map_sources:
        if not (
            source.direction == candidate.direction
            and source.available_at <= candidate.sweep_at
            and source.active_at(candidate.sweep_at)
            and max(source.bottom, parent.bottom)
            <= min(source.top, parent.top)
        ):
            continue
        owner = map_root_wave_owner(
            source,
            analyses[source.timeframe],
            candidate.sweep_at,
        )
        if owner is not None:
            options.append((source, owner))
    if not options:
        return None
    return max(
        options,
        key=lambda item: (
            item[0].available_at,
            int(item[1].rank_available_at or item[1].available_at),
            -item[0].width,
            1 if item[0].timeframe == "M30" else 0,
        ),
    )


def has_new_htf_confirmation(
    direction: str,
    after: int,
    before: int,
    analyses: dict[str, Any],
) -> bool:
    """A stopped thesis can rearm only after a new M30/H1 body-break event."""
    return any(
        event.direction.value == direction
        and after < event.available_at <= before
        for timeframe in ("H1", "M30")
        for event in analyses[timeframe].events
    )


def latest_m5_correction(
    direction: str,
    after: int,
    before: int,
    m5_analysis: Any,
) -> Any | None:
    required_side = "high" if direction == "short" else "low"
    waves = [
        wave
        for wave in m5_analysis.waves
        if (
            wave.side.value == required_side
            and after < wave.available_at <= before
        )
    ]
    return waves[-1] if waves else None


def adaptive_map_direction_at(
    timestamp: int,
    frames: dict[str, Any],
    analyses: dict[str, Any],
) -> tuple[str, str, str] | None:
    """Let the latest confirmed H1/M30 body break own the live map.

    H1 remains the broad context. M30 may take ownership when it exposes a
    newer structure change hidden inside a still-unbroken, stale H1 range.
    """
    events = [
        event
        for timeframe in ("H1", "M30")
        for event in analyses[timeframe].events
        if event.available_at <= timestamp
    ]
    if events:
        event = max(
            events,
            key=lambda item: (
                item.available_at,
                1 if item.timeframe == "H1" else 0,
            ),
        )
        return event.direction.value, event.timeframe, event.event_id
    for timeframe in ("H1", "M30"):
        index = index_at_or_before(frames[timeframe], timestamp)
        if index < 0:
            continue
        trend = int(analyses[timeframe].trend[index])
        if trend:
            return (
                "long" if trend > 0 else "short",
                timeframe,
                f"{timeframe}:TREND_STATE:{int(frames[timeframe].time[index])}",
            )
    return None


def internal_rotation_context(
    candidate: RuleCandidate,
    map_root: Any,
    liquidity: list[Any],
    analyses: dict[str, Any],
) -> dict[str, Any] | None:
    """Require external liquidity delivery and an M15 turn against H1."""
    required_side = "high" if candidate.direction == "short" else "low"
    root_width = max(POINT, float(map_root.top) - float(map_root.bottom))
    delivered = [
        level
        for level in liquidity
        if (
            level.side == required_side
            and level.timeframe in {"H1", "M30", "M15"}
            and level.rank == "external"
            and level.available_at <= candidate.sweep_at
            and level.consumed_at is not None
            and candidate.sweep_at - 24 * 3600
            <= level.consumed_at
            <= candidate.sweep_at
            and float(map_root.bottom) - root_width
            <= float(level.level)
            <= float(map_root.top) + root_width
        )
    ]
    if not delivered:
        return None
    delivered.sort(key=lambda level: int(level.consumed_at), reverse=True)
    source_liquidity = delivered[0]
    rotations = [
        event
        for event in analyses["M15"].events
        if (
            event.direction.value == candidate.direction
            and int(source_liquidity.consumed_at)
            <= event.available_at
            <= candidate.created_at
        )
    ]
    if not rotations:
        return None
    return {
        "sourceLiquidityId": source_liquidity.liquidity_id,
        "sourceLiquidityConsumedAt": iso(source_liquidity.consumed_at),
        "m15RotationEventId": rotations[-1].event_id,
    }


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


def first_touch_in_planned_reaction(
    parent: Any,
    planning_boundary: int,
    sweep_at: int,
    m1: Any,
    reaction_minutes: int = 25,
) -> int | None:
    """Return the first parent-OB touch after the H1 plan became actionable."""
    start = int(np.searchsorted(m1.time, planning_boundary, side="left"))
    end = int(np.searchsorted(m1.time, sweep_at, side="right"))
    touch_at: int | None = None
    for index in range(start, end):
        overlaps = (
            float(m1.low[index]) <= float(parent.top)
            and float(m1.high[index]) >= float(parent.bottom)
        )
        if overlaps:
            touch_at = int(m1.time[index])
            break
    if touch_at is None:
        return None
    if sweep_at - touch_at > reaction_minutes * 60:
        return None
    return touch_at


def nearer_live_objective_owner(
    candidate: RuleCandidate,
    objective: dict[str, Any],
    owners: dict[tuple[Any, ...], dict[str, Any]],
    at: int,
    m1: Any,
) -> dict[str, Any] | None:
    candidate_level = float(objective["level"])
    blockers: list[dict[str, Any]] = []
    for owner in owners.values():
        if owner["direction"] != candidate.direction:
            continue
        owner_level = float(owner["objective"])
        is_nearer = (
            candidate.entry > owner_level > candidate_level
            if candidate.direction == "short"
            else candidate.entry < owner_level < candidate_level
        )
        if not is_nearer:
            continue
        if objective_delivered(
            candidate.direction,
            owner_level,
            int(owner["createdAt"]),
            at,
            m1,
        ):
            continue
        blockers.append(owner)
    if not blockers:
        return None
    return (
        max(blockers, key=lambda owner: float(owner["objective"]))
        if candidate.direction == "short"
        else min(blockers, key=lambda owner: float(owner["objective"]))
    )


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
    liquidity = list(result.liquidity)
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

    owners: dict[tuple[Any, ...], dict[str, Any]] = {}
    trades: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    used_chains: set[tuple[Any, ...]] = set()
    delivery_corrections: dict[str, Any] = {}
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
            parent = sources[candidate.parent_source_id]
            opposite_active = [
                trade
                for trade in trades
                if (
                    trade["direction"] != candidate.direction
                    and position_open(trade, fill_at)
                )
            ]
            if opposite_active:
                owner["pendings"].remove(pending)
                log_verdict(
                    candidate,
                    fill_at,
                    "CANCEL_PENDING_OPPOSITE_POSITION_ACTIVE",
                    ownerId=owner["ownerId"],
                    opposingTradeIds=[
                        trade["tradeId"] for trade in opposite_active
                    ],
                )
                continue
            if source.invalidated_at is not None and source.invalidated_at <= fill_at:
                owner["pendings"].remove(pending)
                log_verdict(
                    candidate,
                    fill_at,
                    "CANCEL_PENDING_SOURCE_INVALIDATED",
                    ownerId=owner["ownerId"],
                )
                continue
            if parent.invalidated_at is not None and parent.invalidated_at <= fill_at:
                owner["pendings"].remove(pending)
                log_verdict(
                    candidate,
                    fill_at,
                    "CANCEL_PENDING_PARENT_SOURCE_INVALIDATED",
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
                f"SCENARIO-V7-{len(trades) + 1:03d}",
                model,
                str(owner["ownerId"]),
            )
            trade["candidateId"] = candidate.candidate_id
            trade["mapRootSourceId"] = pending["mapRoot"].source_id
            trade_map = adaptive_map_direction_at(
                candidate.created_at,
                frames,
                analyses,
            )
            trade["mapDirection"] = trade_map[0] if trade_map else None
            trade["mapTimeframe"] = trade_map[1] if trade_map else None
            trade["mapEventId"] = trade_map[2] if trade_map else None
            root_wave = map_root_wave_owner(
                pending["mapRoot"],
                analyses[pending["mapRoot"].timeframe],
                candidate.sweep_at,
            )
            trade["mapRootWaveId"] = (
                root_wave.object_id if root_wave is not None else None
            )
            trade["shiftReferenceKind"] = candidate.shift_reference_kind
            trade["sourceBottom"] = candidate.source_bottom
            trade["sourceTop"] = candidate.source_top
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
                liquidity,
                m1,
            )
            if trigger_liquidity is None:
                log_verdict(candidate, at, "REJECT_RECENT_PIVOT_ONLY")
                continue
            if source.invalidated_at is not None and source.invalidated_at <= at:
                log_verdict(candidate, at, "REJECT_SOURCE_INVALIDATED")
                continue
            if parent.invalidated_at is not None and parent.invalidated_at <= at:
                log_verdict(candidate, at, "REJECT_PARENT_SOURCE_INVALIDATED")
                continue
            map_root_match = find_causal_map_root_source(
                candidate,
                sources,
                map_sources,
                analyses,
            )
            if map_root_match is None:
                log_verdict(candidate, at, "REJECT_NO_HTF_OB_LINEAGE")
                continue
            map_root, map_root_wave = map_root_match

            map_state = adaptive_map_direction_at(
                candidate.created_at,
                frames,
                analyses,
            )
            if map_state is None:
                log_verdict(candidate, at, "REJECT_NO_CONFIRMED_H1_MAP")
                continue
            map_direction, map_timeframe, map_event_id = map_state
            candidate.map_direction = map_direction
            candidate.scope = (
                "EXTERNAL_CONTINUATION"
                if candidate.direction == map_direction
                else "INTERNAL_ROTATION"
            )
            rotation_context: dict[str, Any] | None = None
            if candidate.scope == "EXTERNAL_CONTINUATION":
                dealing_range = map_root_dealing_range(
                    candidate,
                    map_root,
                    frames,
                    analyses,
                )
                if dealing_range is None:
                    log_verdict(
                        candidate,
                        at,
                        "REJECT_MAP_ROOT_WRONG_DEALING_RANGE_HALF",
                    )
                    continue
            else:
                dealing_range = None
                rotation_context = internal_rotation_context(
                    candidate,
                    map_root,
                    liquidity,
                    analyses,
                )
                if rotation_context is None:
                    log_verdict(
                        candidate,
                        at,
                        "REJECT_INTERNAL_ROTATION_WITHOUT_EXTERNAL_SWEEP_AND_M15_TURN",
                    )
                    continue
            objective = choose_objective(candidate, m1, at)
            if objective is None:
                log_verdict(candidate, at, "REJECT_NO_CAUSAL_OBJECTIVE")
                continue
            objective_blocker = nearer_live_objective_owner(
                candidate,
                objective,
                owners,
                at,
                m1,
            )
            if objective_blocker is not None:
                log_verdict(
                    candidate,
                    at,
                    "REJECT_FARTHER_OBJECTIVE_BEFORE_NEARER_PATH_RESOLVED",
                    blockerOwnerId=objective_blocker["ownerId"],
                    blockerObjective=objective_blocker["objective"],
                    candidateObjective=objective["level"],
                )
                continue
            key = scenario_key(map_root, candidate, objective)
            owner = owners.get(key)
            model = "HTF_OB_REACTION"
            replacement: dict[str, Any] | None = None

            opposite_active = [
                trade
                for trade in trades
                if (
                    trade["direction"] != candidate.direction
                    and position_open(trade, at)
                )
            ]
            if opposite_active:
                log_verdict(
                    candidate,
                    at,
                    "REJECT_OPPOSITE_POSITION_ACTIVE",
                    opposingTradeIds=[trade["tradeId"] for trade in opposite_active],
                )
                continue

            live_challengers = [
                challenger
                for challenger in owners.values()
                if (
                    challenger["direction"] != candidate.direction
                    and not objective_delivered(
                        challenger["direction"],
                        float(challenger["objective"]),
                        int(challenger["createdAt"]),
                        at,
                        m1,
                    )
                )
            ]
            if candidate.scope == "INTERNAL_ROTATION" and any(
                challenger.get("scope") == "EXTERNAL_CONTINUATION"
                for challenger in live_challengers
            ):
                log_verdict(
                    candidate,
                    at,
                    "REJECT_EXTERNAL_CONTINUATION_CHALLENGER",
                    challengerOwnerIds=[
                        challenger["ownerId"] for challenger in live_challengers
                        if challenger.get("scope") == "EXTERNAL_CONTINUATION"
                    ],
                )
                continue
            if candidate.scope == "EXTERNAL_CONTINUATION":
                for challenger in live_challengers:
                    for pending in list(challenger.get("pendings", [])):
                        challenger["pendings"].remove(pending)
                        log_verdict(
                            pending["candidate"],
                            at,
                            "CANCEL_PENDING_SUPERSEDED_BY_EXTERNAL_CHALLENGER",
                            ownerId=challenger["ownerId"],
                            challengerCandidateId=candidate.candidate_id,
                        )
                    challenger["challengedAt"] = at
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
            h1_planning_boundary = (candidate.sweep_at // 3600) * 3600
            if (
                model != "DELIVERY_FVG_ADDON"
                and parent.available_at > h1_planning_boundary
            ):
                log_verdict(
                    candidate,
                    at,
                    "REJECT_SOURCE_NOT_PREDECLARED_AT_H1_MAP_CLOSE",
                    parentAvailableAt=iso(parent.available_at),
                    planningBoundary=iso(h1_planning_boundary),
                )
                continue
            if model != "DELIVERY_FVG_ADDON":
                planned_touch_at = first_touch_in_planned_reaction(
                    parent,
                    h1_planning_boundary,
                    candidate.sweep_at,
                    m1,
                )
                if planned_touch_at is None:
                    log_verdict(
                        candidate,
                        at,
                        "REJECT_NOT_FIRST_PLANNED_OB_REACTION_EPISODE",
                        planningBoundary=iso(h1_planning_boundary),
                    )
                    continue
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
                base_attempts = [
                    trade
                    for trade in owner_trades
                    if trade["entryModel"] != "DELIVERY_FVG_ADDON"
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
                elif model != "DELIVERY_FVG_ADDON" and active:
                    model = "DELIVERY_FVG_ADDON"
                elif model != "DELIVERY_FVG_ADDON":
                    if candidate.sweep_at == owner["lastSweepAt"]:
                        log_verdict(
                            candidate,
                            at,
                            "REJECT_SAME_REACTION_EPISODE",
                            ownerId=owner["ownerId"],
                        )
                        continue
                    model = "HTF_OB_REARM"

                if model == "DELIVERY_FVG_ADDON":
                    active_winners = [
                        trade
                        for trade in active
                        if position_in_profit(trade, m1, at)
                    ]
                    if not active_winners:
                        log_verdict(
                            candidate,
                            at,
                            "REJECT_ADDON_WITHOUT_LIVE_WINNER",
                            ownerId=owner["ownerId"],
                        )
                        continue
                    sweep_key = str(candidate.sweep_at)
                    if owner.get("addonSweepCounts", {}).get(sweep_key, 0) >= 1:
                        log_verdict(
                            candidate,
                            at,
                            "REJECT_DUPLICATE_ADDON_FOR_SWEEP",
                            ownerId=owner["ownerId"],
                            sweepAt=iso(candidate.sweep_at),
                        )
                        continue
                    if not delivered_beyond_owner_source(candidate, owner):
                        log_verdict(
                            candidate,
                            at,
                            "REJECT_ADDON_BEFORE_DIRECTIONAL_DELIVERY",
                            ownerId=owner["ownerId"],
                        )
                        continue
                    correction_after = int(
                        owner.get("lastDeliveryCorrectionAt")
                        or owner.get("lastFilledAt")
                        or owner["createdAt"]
                    )
                    correction = latest_m5_correction(
                        candidate.direction,
                        correction_after,
                        candidate.sweep_at,
                        analyses["M5"],
                    )
                    if correction is None:
                        log_verdict(
                            candidate,
                            at,
                            "REJECT_ADDON_WITHOUT_NEW_M5_CORRECTION",
                            ownerId=owner["ownerId"],
                        )
                        continue
                    if correction.object_id in owner.get(
                        "addonCorrectionIds", set()
                    ):
                        log_verdict(
                            candidate,
                            at,
                            "REJECT_DUPLICATE_ADDON_FOR_M5_CORRECTION",
                            ownerId=owner["ownerId"],
                            correctionId=correction.object_id,
                        )
                        continue
                    if not has_directional_m5_fvg(
                        candidate.direction,
                        correction.available_at,
                        candidate.created_at,
                        frames["M5"],
                    ):
                        log_verdict(
                            candidate,
                            at,
                            "REJECT_ADDON_WITHOUT_M5_DISPLACEMENT_FVG",
                            ownerId=owner["ownerId"],
                            correctionId=correction.object_id,
                        )
                        continue
                    delivery_corrections[candidate.candidate_id] = correction
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
                mapRootWaveId=map_root_wave.object_id,
                mapDirection=map_direction,
                mapTimeframe=map_timeframe,
                mapEventId=map_event_id,
                triggerLiquidity=trigger_liquidity,
                dealingRange=dealing_range,
                rotationContext=rotation_context,
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
                    "ownerId": f"SCN-V7-{owner_sequence:03d}",
                    "scenarioKey": list(key),
                    "direction": selected.direction,
                    "scope": selected.scope,
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
                    "mapRootSourceIds": [map_root.source_id],
                    "addonSweepCounts": {},
                    "addonCorrectionIds": set(),
                    "pendings": [],
                }
                owners[key] = owner
            elif map_root.source_id not in owner["mapRootSourceIds"]:
                owner["mapRootSourceIds"].append(map_root.source_id)
                if map_root.available_at > sources.get(
                    owner["mapRootSourceId"],
                    map_root,
                ).available_at:
                    owner["mapRootSourceId"] = map_root.source_id
                if selected.scope == "EXTERNAL_CONTINUATION":
                    owner["scope"] = selected.scope
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
            if model == "DELIVERY_FVG_ADDON":
                correction = delivery_corrections[selected.candidate_id]
                owner["lastDeliveryCorrectionAt"] = correction.available_at
                owner["addonCorrectionIds"].add(correction.object_id)
                sweep_key = str(selected.sweep_at)
                owner["addonSweepCounts"][sweep_key] = (
                    owner["addonSweepCounts"].get(sweep_key, 0) + 1
                )
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
        "schema": "mentor-scenario-discovery-v7",
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
