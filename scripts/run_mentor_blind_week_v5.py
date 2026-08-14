"""Run the frozen V5 mentor rules on an untouched week.

This runner never imports the June reverse-engineering casebook. It converts
as-of evidence candidates into chronological scenario decisions, then replays
fills with bid OHLC and recorded spread.
"""

from __future__ import annotations

from collections import defaultdict
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

from mentor_engine.data import (
    build_timeframes,
    index_at_or_before,
    load_m1_npz,
    parse_utc,
)
from mentor_engine.structure import analyze_structure
from mentor_rule_engine import EngineConfig, MentorRuleEngine, RuleCandidate


DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = ROOT / "output" / "mentor_blind_week_2025-07-07_11_v5"
WARMUP_FROM = "2025-06-15T00:00:00Z"
TRADE_FROM = "2025-07-07T00:00:00Z"
TRADE_TO = "2025-07-12T00:00:00Z"
OBSERVE_TO = "2025-07-15T00:00:00Z"
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


def traversed(
    m1: Any,
    direction: str,
    level: float,
    start_at: int,
    end_at: int,
) -> bool:
    start = int(np.searchsorted(m1.time, start_at, side="left"))
    end = int(np.searchsorted(m1.time, end_at, side="left"))
    if end <= start:
        return False
    if direction == "short":
        return bool(np.any(m1.low[start:end] < level))
    return bool(np.any(m1.high[start:end] > level))


def candidate_rank(candidate: RuleCandidate) -> tuple[float, ...]:
    refined = 1 if len(candidate.refinement_path) > 1 else 0
    timeframe = 2 if candidate.source_timeframe == "M5" else 1
    continuation = 1 if candidate.scope == "EXTERNAL_CONTINUATION" else 0
    source_width = candidate.source_top - candidate.source_bottom
    return (
        float(refined),
        float(timeframe),
        float(continuation),
        -source_width,
        -float(candidate.created_at),
    )


def choose_objective(
    candidate: RuleCandidate,
    m1: Any,
    as_of: int,
) -> dict[str, Any] | None:
    """Freeze a pre-existing HTF objective, not a nearby trigger pivot."""
    for item in candidate.objective_alternatives:
        level = float(item["level"])
        if item["timeframe"] not in {"H1", "M30", "M15"}:
            continue
        if item["rank"] != "external":
            continue
        geometry = (
            candidate.stop > candidate.entry > level
            if candidate.direction == "short"
            else candidate.stop < candidate.entry < level
        )
        if not geometry:
            continue
        if traversed(m1, candidate.direction, level, candidate.created_at, as_of):
            continue
        return item
    return None


def source_created_displacement_fvg(
    source: Any,
    frames: dict[str, Any],
) -> bool:
    """The source OB must launch a same-direction inefficiency."""
    series = frames[source.timeframe]
    start = max(2, int(source.confirm_index))
    end = min(len(series), int(source.confirm_index) + 4)
    for index in range(start, end):
        if (
            source.direction == "short"
            and float(series.high[index]) < float(series.low[index - 2])
        ):
            return True
        if (
            source.direction == "long"
            and float(series.low[index]) > float(series.high[index - 2])
        ):
            return True
    return False


def find_map_root_source(
    candidate: RuleCandidate,
    execution_sources: dict[str, Any],
    map_sources: list[Any],
    frames: dict[str, Any],
) -> Any | None:
    """Link an M15/M5 source to a pre-existing H1/M30 OB lineage."""
    parent = execution_sources[candidate.parent_source_id]
    options = [
        source
        for source in map_sources
        if (
            source.direction == candidate.direction
            and source.available_at <= candidate.sweep_at
            and source.active_at(candidate.sweep_at)
            and max(source.bottom, parent.bottom)
            <= min(source.top, parent.top)
        )
    ]
    if not options:
        return None
    return max(
        options,
        key=lambda source: (
            source.available_at,
            -source.width,
            1 if source.timeframe == "M30" else 0,
        ),
    )


def adaptive_dealing_range(
    candidate: RuleCandidate,
    frames: dict[str, Any],
    analyses: dict[str, Any],
) -> dict[str, Any] | None:
    """Find the highest meaningful range that places the source correctly."""
    midpoint = (candidate.source_bottom + candidate.source_top) / 2.0
    states: list[dict[str, Any]] = []
    for timeframe in ("H1", "M30", "M15", "M5"):
        series = frames[timeframe]
        analysis = analyses[timeframe]
        index = index_at_or_before(series, candidate.created_at)
        if index < 0:
            continue
        low = float(analysis.range_low[index])
        high = float(analysis.range_high[index])
        if not (np.isfinite(low) and np.isfinite(high) and high > low):
            continue
        equilibrium = (low + high) / 2.0
        correct_half = (
            midpoint >= equilibrium
            if candidate.direction == "short"
            else midpoint <= equilibrium
        )
        states.append(
            {
                "timeframe": timeframe,
                "low": low,
                "high": high,
                "equilibrium": equilibrium,
                "trend": int(analysis.trend[index]),
                "correctHalf": correct_half,
            }
        )
    return next((state for state in states if state["correctHalf"]), None)


def map_event_at(
    candidate: RuleCandidate,
    analyses: dict[str, Any],
) -> dict[str, Any] | None:
    """Attach the setup to the map event known before its trigger."""
    for timeframe in ("H1", "M30", "M15"):
        events = [
            event
            for event in analyses[timeframe].events
            if event.available_at <= candidate.created_at
        ]
        if not events:
            continue
        event = events[-1]
        if timeframe == "H1" or event.direction.value == candidate.map_direction:
            return {
                "timeframe": timeframe,
                "eventId": event.event_id,
                "direction": event.direction.value,
                "eventType": event.event_type,
            }
    return None


def current_bid(m1: Any, at: int) -> float:
    index = int(np.searchsorted(m1.available_time, at, side="right") - 1)
    if index < 0:
        raise ValueError("No market price available")
    return float(m1.close[index])


def position_in_profit(
    trade: dict[str, Any],
    m1: Any,
    at: int,
) -> bool:
    price = current_bid(m1, at)
    return (
        price < float(trade["entry"])
        if trade["direction"] == "short"
        else price > float(trade["entry"])
    )


def has_new_m5_correction(
    direction: str,
    after: int,
    before: int,
    m5_analysis: Any,
) -> bool:
    required_side = "high" if direction == "short" else "low"
    return any(
        wave.side.value == required_side
        and after < wave.available_at <= before
        for wave in m5_analysis.waves
    )


def has_directional_m5_fvg(
    direction: str,
    after: int,
    before: int,
    m5: Any,
) -> bool:
    start = max(
        2,
        int(np.searchsorted(m5.available_time, after, side="right")),
    )
    end = int(np.searchsorted(m5.available_time, before, side="right"))
    for index in range(start, end):
        if (
            direction == "short"
            and float(m5.high[index]) < float(m5.low[index - 2])
        ):
            return True
        if (
            direction == "long"
            and float(m5.low[index]) > float(m5.high[index - 2])
        ):
            return True
    return False


def delivered_preexisting_liquidity(
    direction: str,
    entry: float,
    after: int,
    before: int,
    liquidity: list[Any],
) -> bool:
    target_side = "low" if direction == "short" else "high"
    return any(
        level.side == target_side
        and level.timeframe in {"M15", "M5"}
        and level.available_at <= after
        and level.consumed_at is not None
        and after < level.consumed_at <= before
        and (
            level.level < entry
            if direction == "short"
            else level.level > entry
        )
        for level in liquidity
    )


def simulate_trade(
    m1: Any,
    candidate: RuleCandidate,
    objective: float,
    trade_id: str,
    entry_model: str,
    owner_id: str,
) -> dict[str, Any]:
    fill_at = int(candidate.retest_at or candidate.created_at)
    start = int(np.searchsorted(m1.available_time, fill_at, side="left"))
    result = "OPEN"
    closed_at: int | None = None
    ambiguous = False
    for index in range(start, len(m1)):
        if int(m1.time[index]) >= ts(OBSERVE_TO):
            break
        spread = max(POINT, float(m1.spread_points[index]) * POINT)
        bid_low = float(m1.low[index])
        bid_high = float(m1.high[index])
        ask_low = bid_low + spread
        ask_high = bid_high + spread
        if candidate.direction == "long":
            stop_hit = bid_low <= candidate.stop
            target_hit = bid_high >= objective
        else:
            stop_hit = ask_high >= candidate.stop
            target_hit = ask_low <= objective
        if stop_hit or target_hit:
            ambiguous = stop_hit and target_hit
            result = "SL" if stop_hit else "TP"
            closed_at = int(m1.available_time[index])
            break
    planned_r = abs(
        (objective - candidate.entry) / (candidate.entry - candidate.stop)
    )
    earned_r = -1.0 if result == "SL" else planned_r if result == "TP" else 0.0
    return {
        "tradeId": trade_id,
        "ownerId": owner_id,
        "direction": candidate.direction,
        "scope": candidate.scope,
        "entryModel": entry_model,
        "sourceTf": candidate.source_timeframe,
        "sourceId": candidate.source_id,
        "parentSourceId": candidate.parent_source_id,
        "sweepAt": iso(candidate.sweep_at),
        "shiftAt": iso(candidate.shift_at),
        "fvgId": candidate.fvg_id,
        "decisionAt": iso(candidate.created_at),
        "filledAt": iso(fill_at),
        "closedAt": iso(closed_at),
        "entry": candidate.entry,
        "stop": candidate.stop,
        "objective": objective,
        "result": result,
        "ambiguous": ambiguous,
        "plannedR": round(planned_r, 6),
        "earnedR": round(earned_r, 6),
        "holdingMinutes": (
            int((closed_at - fill_at) / 60) if closed_at is not None else None
        ),
    }


def position_open(trade: dict[str, Any], at: int) -> bool:
    filled = ts(trade["filledAt"])
    closed = ts(trade["closedAt"]) if trade["closedAt"] else None
    return filled <= at and (closed is None or at < closed)


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


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
    engine = MentorRuleEngine(frames)
    map_sources = MentorRuleEngine(
        frames,
        EngineConfig(
            source_timeframes=("H1", "M30"),
            source_max_age_minutes=14 * 24 * 60,
        ),
    )._detect_sources()
    result = engine.run(ts(TRADE_FROM), ts(TRADE_TO))
    sources = {source.source_id: source for source in result.sources}
    evidence = [
        candidate
        for candidate in result.authorized_candidates
        if (
            candidate.retest_at is not None
            and ts(TRADE_FROM) <= candidate.retest_at < ts(TRADE_TO)
        )
    ]
    by_retest: dict[int, list[RuleCandidate]] = defaultdict(list)
    for candidate in evidence:
        by_retest[int(candidate.retest_at)].append(candidate)

    trades: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    used_chains: set[tuple[Any, ...]] = set()
    retired_paths: set[tuple[str, str, str]] = set()
    owner: dict[str, Any] | None = None
    owner_attempt = 0
    last_entry: float | None = None
    last_entry_at: int | None = None

    for at in sorted(by_retest):
        active_positions = [trade for trade in trades if position_open(trade, at)]
        if owner is not None:
            owner_source = sources.get(owner["sourceId"])
            source_invalid = bool(
                owner_source
                and owner_source.invalidated_at is not None
                and owner_source.invalidated_at <= at
            )
            objective_done = traversed(
                m1,
                owner["direction"],
                float(owner["objective"]),
                int(owner["createdAt"]),
                at,
            )
            if (source_invalid or objective_done) and not active_positions:
                retired_paths.add(
                    (
                        str(owner["mapEvent"]["eventId"]),
                        str(owner["direction"]),
                        str(owner["objectiveId"]),
                    )
                )
                owner = None
                owner_attempt = 0
                last_entry = None
                last_entry_at = None

        group = by_retest[at]
        viable: list[tuple[RuleCandidate, dict[str, Any], str]] = []
        for candidate in group:
            chain = (
                candidate.parent_source_id,
                candidate.sweep_at,
                candidate.shift_at,
                candidate.fvg_id,
            )
            if chain in used_chains:
                audit.append(
                    {
                        "at": iso(at),
                        "candidateId": candidate.candidate_id,
                        "verdict": "REJECT_DUPLICATE_PHYSICAL_CHAIN",
                    }
                )
                continue
            source = sources[candidate.source_id]
            if source.invalidated_at is not None and source.invalidated_at <= at:
                audit.append(
                    {
                        "at": iso(at),
                        "candidateId": candidate.candidate_id,
                        "verdict": "REJECT_SOURCE_INVALIDATED",
                    }
                )
                continue
            if active_positions and any(
                trade["direction"] != candidate.direction
                for trade in active_positions
            ):
                audit.append(
                    {
                        "at": iso(at),
                        "candidateId": candidate.candidate_id,
                        "verdict": "REJECT_OPPOSITE_OPEN_POSITION",
                    }
                )
                continue
            if owner is not None and owner["direction"] != candidate.direction:
                audit.append(
                    {
                        "at": iso(at),
                        "candidateId": candidate.candidate_id,
                        "verdict": "REJECT_COMPETING_OWNER",
                    }
                )
                continue
            if owner is not None:
                objective = {
                    "level": owner["objective"],
                    "id": owner["objectiveId"],
                    "kind": owner["objectiveKind"],
                }
                on_path = (
                    float(objective["level"]) < candidate.entry <= candidate.stop
                    if candidate.direction == "short"
                    else candidate.stop <= candidate.entry < float(objective["level"])
                )
                if not on_path:
                    audit.append(
                        {
                            "at": iso(at),
                            "candidateId": candidate.candidate_id,
                            "verdict": "REJECT_NOT_ON_OWNER_DELIVERY_PATH",
                        }
                    )
                    continue
                same_parent = (
                    candidate.parent_source_id == owner["parentSourceId"]
                )
                active_same_direction = [
                    trade
                    for trade in active_positions
                    if trade["direction"] == candidate.direction
                ]
                progressed = bool(
                    last_entry is None
                    or (
                        candidate.entry < last_entry - POINT
                        if candidate.direction == "short"
                        else candidate.entry > last_entry + POINT
                    )
                )
                if not progressed:
                    audit.append(
                        {
                            "at": iso(at),
                            "candidateId": candidate.candidate_id,
                            "verdict": "REJECT_NO_DELIVERY_PROGRESS",
                        }
                    )
                    continue
                if (
                    last_entry_at is None
                    or not has_directional_m5_fvg(
                        candidate.direction,
                        last_entry_at,
                        at,
                        frames["M5"],
                    )
                    or not delivered_preexisting_liquidity(
                        candidate.direction,
                        float(last_entry),
                        last_entry_at,
                        at,
                        result.liquidity,
                    )
                ):
                    audit.append(
                        {
                            "at": iso(at),
                            "candidateId": candidate.candidate_id,
                            "verdict": "REJECT_ADDON_WITHOUT_PROVEN_DELIVERY_LEG",
                        }
                    )
                    continue
                if same_parent:
                    same_sweep = candidate.sweep_at == owner["lastSweepAt"]
                    if same_sweep:
                        if not active_same_direction or not all(
                            position_in_profit(trade, m1, at)
                            for trade in active_same_direction
                        ):
                            audit.append(
                                {
                                    "at": iso(at),
                                    "candidateId": candidate.candidate_id,
                                    "verdict": "REJECT_ADDON_OWNER_NOT_IN_PROFIT",
                                }
                            )
                            continue
                        entry_model = "DELIVERY_FVG_ADDON"
                    else:
                        if (
                            last_entry_at is None
                            or not has_new_m5_correction(
                                candidate.direction,
                                last_entry_at,
                                candidate.sweep_at,
                                analyses["M5"],
                            )
                        ):
                            audit.append(
                                {
                                    "at": iso(at),
                                    "candidateId": candidate.candidate_id,
                                    "verdict": "REJECT_REARM_NO_NEW_M5_CORRECTION",
                                }
                            )
                            continue
                        entry_model = "HTF_OB_REARM"
                else:
                    parent = sources[candidate.parent_source_id]
                    if not source_created_displacement_fvg(parent, frames):
                        audit.append(
                            {
                                "at": iso(at),
                                "candidateId": candidate.candidate_id,
                                "verdict": "REJECT_ADDON_SOURCE_WITHOUT_DISPLACEMENT_FVG",
                            }
                        )
                        continue
                    if not active_same_direction or not all(
                        position_in_profit(trade, m1, at)
                        for trade in active_same_direction
                    ):
                        audit.append(
                            {
                                "at": iso(at),
                                "candidateId": candidate.candidate_id,
                                "verdict": "REJECT_NEW_SOURCE_WITHOUT_LIVE_WINNER",
                            }
                        )
                        continue
                    if parent.available_at <= owner["firstFilledAt"]:
                        audit.append(
                            {
                                "at": iso(at),
                                "candidateId": candidate.candidate_id,
                                "verdict": "REJECT_ADDON_SOURCE_PREDATES_OWNER",
                            }
                        )
                        continue
                    if (
                        last_entry_at is None
                        or not has_new_m5_correction(
                            candidate.direction,
                            last_entry_at,
                            candidate.sweep_at,
                            analyses["M5"],
                        )
                    ):
                        audit.append(
                            {
                                "at": iso(at),
                                "candidateId": candidate.candidate_id,
                                "verdict": "REJECT_ADDON_NO_NEW_M5_CORRECTION",
                            }
                        )
                        continue
                    entry_model = "DELIVERY_FVG_ADDON"
            else:
                parent = sources[candidate.parent_source_id]
                map_root = find_map_root_source(
                    candidate,
                    sources,
                    map_sources,
                    frames,
                )
                if map_root is None:
                    audit.append(
                        {
                            "at": iso(at),
                            "candidateId": candidate.candidate_id,
                            "verdict": "REJECT_NO_HTF_OB_LINEAGE",
                        }
                    )
                    continue
                if not source_created_displacement_fvg(parent, frames):
                    audit.append(
                        {
                            "at": iso(at),
                            "candidateId": candidate.candidate_id,
                            "verdict": "REJECT_SOURCE_WITHOUT_DISPLACEMENT_FVG",
                        }
                    )
                    continue
                dealing_range = adaptive_dealing_range(
                    candidate,
                    frames,
                    analyses,
                )
                if dealing_range is None:
                    audit.append(
                        {
                            "at": iso(at),
                            "candidateId": candidate.candidate_id,
                            "verdict": "REJECT_SOURCE_WRONG_DEALING_RANGE_HALF",
                        }
                    )
                    continue
                map_event = map_event_at(candidate, analyses)
                if map_event is None:
                    audit.append(
                        {
                            "at": iso(at),
                            "candidateId": candidate.candidate_id,
                            "verdict": "REJECT_NO_CONFIRMED_MAP_EVENT",
                        }
                    )
                    continue
                objective = choose_objective(candidate, m1, at)
                if objective is None:
                    audit.append(
                        {
                            "at": iso(at),
                            "candidateId": candidate.candidate_id,
                            "verdict": "REJECT_NO_LIVE_OBJECTIVE",
                        }
                    )
                    continue
                path_key = (
                    str(map_event["eventId"]),
                    candidate.direction,
                    str(objective["id"]),
                )
                if path_key in retired_paths:
                    audit.append(
                        {
                            "at": iso(at),
                            "candidateId": candidate.candidate_id,
                            "verdict": "REJECT_RETIRED_MAP_OBJECTIVE_PATH",
                            "mapEventId": map_event["eventId"],
                            "objectiveId": objective["id"],
                        }
                    )
                    continue
                entry_model = "HTF_OB_REACTION"
            viable.append((candidate, objective, entry_model))

        directions = {candidate.direction for candidate, _, _ in viable}
        if len(directions) > 1 and owner is None and not active_positions:
            for candidate, _, _ in viable:
                audit.append(
                    {
                        "at": iso(at),
                        "candidateId": candidate.candidate_id,
                        "verdict": "WAIT_INCOMPARABLE_DIRECTIONS",
                    }
                )
            continue
        if not viable:
            continue
        viable.sort(key=lambda item: candidate_rank(item[0]), reverse=True)
        selected, objective, entry_model = viable[0]
        for candidate, _, _ in viable[1:]:
            audit.append(
                {
                    "at": iso(at),
                    "candidateId": candidate.candidate_id,
                    "verdict": "REJECT_LOWER_CAUSAL_REFINEMENT",
                    "selectedId": selected.candidate_id,
                }
            )

        if owner is None:
            selected_map_root = find_map_root_source(
                selected,
                sources,
                map_sources,
                frames,
            )
            if selected_map_root is None:
                raise AssertionError("Selected initial scenario lost its HTF root")
            owner = {
                "ownerId": f"OWNER-{len(trades) + 1:03d}",
                "direction": selected.direction,
                "sourceId": selected.source_id,
                "parentSourceId": selected.parent_source_id,
                "objective": float(objective["level"]),
                "objectiveId": str(objective["id"]),
                "objectiveKind": str(objective["kind"]),
                "createdAt": selected.created_at,
                "firstFilledAt": int(selected.retest_at or selected.created_at),
                "rootSweepAt": selected.sweep_at,
                "lastSweepAt": selected.sweep_at,
                "mapRootSourceId": selected_map_root.source_id,
                "mapRootTimeframe": selected_map_root.timeframe,
                "dealingRange": adaptive_dealing_range(
                    selected,
                    frames,
                    analyses,
                ),
                "mapEvent": map_event_at(selected, analyses),
            }
            owner_attempt = 0
        owner_attempt += 1
        trade_id = f"BLIND-V5-{len(trades) + 1:03d}"
        trade = simulate_trade(
            m1,
            selected,
            float(owner["objective"]),
            trade_id,
            entry_model,
            str(owner["ownerId"]),
        )
        trades.append(trade)
        last_entry = selected.entry
        last_entry_at = int(selected.retest_at or selected.created_at)
        owner["lastSweepAt"] = selected.sweep_at
        used_chains.add(
            (
                selected.parent_source_id,
                selected.sweep_at,
                selected.shift_at,
                selected.fvg_id,
            )
        )
        audit.append(
            {
                "at": iso(at),
                "candidateId": selected.candidate_id,
                "verdict": "TRADE",
                "tradeId": trade_id,
                "ownerId": owner["ownerId"],
                "attempt": owner_attempt,
                "entryModel": entry_model,
            }
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    fields = list(trades[0]) if trades else [
        "tradeId",
        "direction",
        "filledAt",
        "closedAt",
        "result",
        "earnedR",
    ]
    with (OUTPUT / "trades.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(trades)
    with (OUTPUT / "decision_audit.jsonl").open("w", encoding="utf-8") as handle:
        for row in audit:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    values = [float(trade["earnedR"]) for trade in trades]
    wins = [trade for trade in trades if trade["result"] == "TP"]
    losses = [trade for trade in trades if trade["result"] == "SL"]
    gross_win = sum(float(trade["earnedR"]) for trade in wins)
    gross_loss = abs(sum(float(trade["earnedR"]) for trade in losses))
    summary = {
        "schema": "mentor-blind-week-v5",
        "period": {"from": TRADE_FROM, "to": TRADE_TO},
        "dataset": str(DATASET.relative_to(ROOT)),
        "datasetMetadata": metadata,
        "casebookImported": False,
        "engineAudit": result.audit,
        "retestEligibleEvidence": len(evidence),
        "decisionEvents": len(audit),
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "open": sum(trade["result"] == "OPEN" for trade in trades),
        "winRate": len(wins) / (len(wins) + len(losses))
        if wins or losses
        else 0.0,
        "totalR": round(sum(values), 6),
        "profitFactor": round(gross_win / gross_loss, 6)
        if gross_loss
        else None,
        "maxDrawdownR": round(max_drawdown(values), 6),
        "ambiguous": sum(bool(trade["ambiguous"]) for trade in trades),
        "ownerCount": len({trade["ownerId"] for trade in trades}),
        "entryModels": dict(
            __import__("collections").Counter(
                trade["entryModel"] for trade in trades
            )
        ),
        "rejectionCounts": dict(
            __import__("collections").Counter(
                row["verdict"] for row in audit if row["verdict"] != "TRADE"
            )
        ),
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT / "frozen_v5_boundary.json").write_text(
        json.dumps(
            {
                "engine": "mentor_rule_engine.MentorRuleEngine",
                "casebookImported": False,
                "tradeFrom": TRADE_FROM,
                "tradeTo": TRADE_TO,
                "noRuleMutationDuringReplay": True,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
