from __future__ import annotations

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

from mentor_engine.data import index_at_or_before, load_m1_npz, parse_utc
from mentor_engine.engine import MentorScenarioEngine
from mentor_engine.models import Direction, LiquidityKind, Side, ZoneKind, jsonable


DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = ROOT / "output" / "mentor_january_destination_replay"
TRADE_FROM = parse_utc("2025-01-01T00:00:00+00:00")
TRADE_TO = parse_utc("2025-02-01T00:00:00+00:00")
OBSERVE_TO = parse_utc("2025-03-01T00:00:00+00:00")
TF_ORDER = ("H1", "M30", "M15", "M5")
TF_SECONDS = {"H1": 3600, "M30": 1800, "M15": 900, "M5": 300}
POINT = 0.01


def iso(value: int | None) -> str | None:
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat() if value is not None else None


def overlaps(a: Any, b: Any) -> bool:
    return a.top >= b.bottom and a.bottom <= b.top


def first_m1_touch(m1: Any, zone: Any) -> int | None:
    start = int(np.searchsorted(m1.available_time, zone.available_at, side="right"))
    end = int(np.searchsorted(m1.available_time, TRADE_TO, side="left"))
    for index in range(start, end):
        if float(m1.high[index]) >= zone.bottom and float(m1.low[index]) <= zone.top:
            return int(m1.available_time[index])
    return None


def containing_parent(zone: Any, parents: list[Any]) -> Any | None:
    matches = [
        parent for parent in parents
        if parent.direction == zone.direction
        and parent.available_at <= zone.available_at
        and parent.occurred_at <= zone.occurred_at < parent.occurred_at + TF_SECONDS[parent.timeframe]
        and overlaps(parent, zone)
    ]
    return matches[0] if len(matches) == 1 else None


def refine(parent: Any, states: dict[str, Any], touch_at: int) -> tuple[Any, list[Any], str]:
    path = [parent]
    current = parent
    start_rank = TF_ORDER.index(parent.timeframe)
    reason = "NO_LOWER_CHILD"
    for timeframe in TF_ORDER[start_rank + 1:]:
        children = [
            zone for zone in states[timeframe].zones
            if zone.kind == ZoneKind.LAST_OPPOSITE_OB
            and zone.direction == parent.direction
            and zone.available_at < touch_at
            and current.occurred_at <= zone.occurred_at < current.occurred_at + TF_SECONDS[current.timeframe]
            and overlaps(current, zone)
        ]
        unique = list({zone.object_id: zone for zone in children}.values())
        if not unique:
            reason = "NO_LOWER_CHILD"
            break
        if parent.direction == Direction.SHORT:
            extreme = max(zone.top for zone in unique)
            owners = [zone for zone in unique if abs(zone.top - extreme) <= POINT]
        else:
            extreme = min(zone.bottom for zone in unique)
            owners = [zone for zone in unique if abs(zone.bottom - extreme) <= POINT]
        if len(owners) != 1:
            reason = "AMBIGUOUS_SWING_EXTREME_OWNER"
            break
        current = owners[0]
        path.append(current)
        reason = "SWING_EXTREME_CHILD"
    return current, path, reason


def bar_intersects(series: Any, index: int, zone: Any) -> bool:
    return float(series.high[index]) >= zone.bottom and float(series.low[index]) <= zone.top


def invalidation_at(m1: Any, zone: Any, direction: Direction, start_at: int) -> int:
    start = int(np.searchsorted(m1.available_time, start_at, side="left"))
    end = int(np.searchsorted(m1.available_time, OBSERVE_TO, side="left"))
    for index in range(start, end):
        close = float(m1.close[index])
        if (direction == Direction.LONG and close < zone.bottom) or (
            direction == Direction.SHORT and close > zone.top
        ):
            return int(m1.available_time[index])
    return OBSERVE_TO


def find_trigger(engine: MentorScenarioEngine, zone: Any, touch_at: int) -> tuple[Any, Any] | None:
    direction = zone.direction
    wanted_side = Side.LOW if direction == Direction.LONG else Side.HIGH
    invalid_at = invalidation_at(engine.series["M1"], zone, direction, touch_at)
    sweeps = []
    for timeframe in ("M5", "M1"):
        state = engine.states[timeframe]
        pools = {pool.object_id: pool for pool in state.liquidity}
        for sweep in state.sweeps:
            pool = pools[sweep.pool_id]
            if pool.side != wanted_side or pool.available_at >= touch_at:
                continue
            if not touch_at <= sweep.available_at < invalid_at:
                continue
            if not bar_intersects(state.series, sweep.index, zone):
                continue
            sweeps.append(sweep)
    for sweep in sorted(sweeps, key=lambda item: (item.available_at, item.timeframe)):
        triggers = [
            event for timeframe in ("M5", "M1")
            for event in engine.states[timeframe].structure.events
            if event.event_type == "CHOCH"
            and event.direction == direction
            and sweep.available_at < event.available_at < invalid_at
        ]
        if triggers:
            return sweep, min(triggers, key=lambda item: (item.available_at, item.timeframe))
    return None


def objective(engine: MentorScenarioEngine, direction: Direction, decision_at: int, entry: float) -> Any | None:
    side = Side.HIGH if direction == Direction.LONG else Side.LOW
    allowed = {
        LiquidityKind.EXTERNAL_SWING,
        LiquidityKind.REACTION_TRAP,
        LiquidityKind.RANGE_EDGE,
        LiquidityKind.TRENDLINE_CLUSTER,
    }
    candidates = []
    for rank, timeframe in enumerate(("H1", "M30", "M5", "H4")):
        for pool in engine.states[timeframe].liquidity:
            if pool.kind not in allowed or pool.side != side or not pool.active_at(decision_at):
                continue
            if (direction == Direction.LONG and pool.level <= entry) or (
                direction == Direction.SHORT and pool.level >= entry
            ):
                continue
            candidates.append((abs(pool.level - entry), rank, pool))
    return min(candidates, key=lambda item: (item[0], item[1], item[2].object_id))[2] if candidates else None


def valid_arrival_location(engine: MentorScenarioEngine, zone: Any) -> bool:
    state = engine.states["H1"]
    index = index_at_or_before(state.series, zone.available_at)
    if index < 0:
        return False
    low = float(state.structure.range_low[index])
    high = float(state.structure.range_high[index])
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        return False
    midpoint = (low + high) / 2.0
    return zone.bottom >= midpoint if zone.direction == Direction.SHORT else zone.top <= midpoint


def simulate(m1: Any, direction: Direction, decision_at: int, entry: float, stop: float, target: float) -> dict[str, Any]:
    start = int(np.searchsorted(m1.available_time, decision_at, side="right"))
    end = int(np.searchsorted(m1.available_time, OBSERVE_TO, side="left"))
    filled = None
    for index in range(start, end):
        spread = float(m1.spread_points[index]) * POINT
        ask_low, ask_high = float(m1.low[index]) + spread, float(m1.high[index]) + spread
        bid_low, bid_high = float(m1.low[index]), float(m1.high[index])
        if filled is None:
            target_first = bid_high >= target if direction == Direction.LONG else ask_low <= target
            invalid_first = bid_low <= stop if direction == Direction.LONG else ask_high >= stop
            touched = ask_low <= entry <= ask_high if direction == Direction.LONG else bid_low <= entry <= bid_high
            if target_first or invalid_first:
                return {"result": "CANCELLED", "entryAt": None, "exitAt": int(m1.available_time[index]), "r": 0.0}
            if not touched:
                continue
            filled = index
        stop_hit = bid_low <= stop if direction == Direction.LONG else ask_high >= stop
        target_hit = bid_high >= target if direction == Direction.LONG else ask_low <= target
        if stop_hit:
            return {"result": "SL", "entryAt": int(m1.available_time[filled]), "exitAt": int(m1.available_time[index]), "r": -1.0}
        if target_hit:
            risk = entry - stop if direction == Direction.LONG else stop - entry
            reward = target - entry if direction == Direction.LONG else entry - target
            return {"result": "TP", "entryAt": int(m1.available_time[filled]), "exitAt": int(m1.available_time[index]), "r": reward / risk}
    return {"result": "OPEN", "entryAt": int(m1.available_time[filled]) if filled is not None else None, "exitAt": None, "r": 0.0}


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    m1, _ = load_m1_npz(DATASET, parse_utc("2024-10-01T00:00:00+00:00"), OBSERVE_TO)
    engine = MentorScenarioEngine(m1)
    engine.prepare()
    parents_h1 = [zone for zone in engine.states["H1"].zones if zone.kind == ZoneKind.LAST_OPPOSITE_OB and zone.linked_structure_event_id]
    parents_m30 = [zone for zone in engine.states["M30"].zones if zone.kind == ZoneKind.LAST_OPPOSITE_OB and zone.linked_structure_event_id]
    roots = list(parents_h1)
    roots.extend(zone for zone in parents_m30 if containing_parent(zone, parents_h1) is None)

    records = []
    seen_touch: set[tuple[Any, ...]] = set()
    for root in sorted(roots, key=lambda item: (item.available_at, item.object_id)):
        touch_at = first_m1_touch(m1, root)
        if touch_at is None or not TRADE_FROM <= touch_at < TRADE_TO:
            continue
        selected, path, stop_reason = refine(root, engine.states, touch_at)
        if len(path) < 2:
            continue
        key = (selected.direction, selected.object_id, touch_at)
        if key in seen_touch:
            continue
        seen_touch.add(key)
        trigger = find_trigger(engine, selected, touch_at)
        record: dict[str, Any] = {
            "rootZoneId": root.object_id,
            "rootTimeframe": root.timeframe,
            "direction": selected.direction.value,
            "declaredAt": iso(root.available_at),
            "touchAt": iso(touch_at),
            "selectedZoneId": selected.object_id,
            "selectedTimeframe": selected.timeframe,
            "zoneLow": selected.bottom,
            "zoneHigh": selected.top,
            "refinementPath": [zone.timeframe for zone in path],
            "refinementStop": stop_reason,
        }
        if trigger is None:
            record["result"] = "NO_TRIGGER"
            records.append(record)
            continue
        sweep, choch = trigger
        decision_at = choch.available_at
        entry = selected.top if selected.direction == Direction.LONG else selected.bottom
        idx = index_at_or_before(m1, decision_at)
        spread = float(m1.spread_points[idx]) * POINT
        buffer = max(spread, POINT)
        stop = min(selected.bottom, sweep.extreme) - buffer if selected.direction == Direction.LONG else max(selected.top, sweep.extreme) + buffer
        target_pool = objective(engine, selected.direction, decision_at, entry)
        if target_pool is None:
            record["result"] = "NO_OBJECTIVE"
            records.append(record)
            continue
        target = float(target_pool.level)
        if not (stop < entry < target if selected.direction == Direction.LONG else target < entry < stop):
            record["result"] = "INVALID_GEOMETRY"
            records.append(record)
            continue
        outcome = simulate(m1, selected.direction, decision_at, entry, stop, target)
        record.update({
            "sweepAt": iso(sweep.available_at),
            "sweepKind": sweep.pool_kind.value,
            "triggerAt": iso(decision_at),
            "triggerTimeframe": choch.timeframe,
            "entry": entry,
            "stopLoss": stop,
            "takeProfit": target,
            "objectiveId": target_pool.object_id,
            "plannedR": abs(target - entry) / abs(entry - stop),
            **outcome,
            "entryAt": iso(outcome["entryAt"]),
            "exitAt": iso(outcome["exitAt"]),
        })
        records.append(record)

    executable = [item for item in records if item["result"] in {"TP", "SL", "CANCELLED", "OPEN"}]
    # One live position/order at a time; retain the first chronologically completed decision.
    kept = []
    busy_until = 0
    for item in sorted(executable, key=lambda value: value.get("triggerAt") or ""):
        decision = parse_utc(item["triggerAt"])
        if decision < busy_until:
            item["portfolioResult"] = "SKIPPED_POSITION_BUSY"
            continue
        item["portfolioResult"] = item["result"]
        kept.append(item)
        busy_until = parse_utc(item["exitAt"]) if item.get("exitAt") else OBSERVE_TO

    closed = [item for item in kept if item["portfolioResult"] in {"TP", "SL"}]
    pnl = [float(item["r"]) for item in closed]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    summary = {
        "protocol": "MENTOR_DESTINATION_OB_REPLAY_V1",
        "rootObTouches": len(records),
        "triggeredOrders": len(executable),
        "portfolioOrders": len(kept),
        "closedTrades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "winRate": len(wins) / len(closed) if closed else 0.0,
        "netR": sum(pnl),
        "profitFactor": sum(wins) / abs(sum(losses)) if losses else None,
        "expectancyR": sum(pnl) / len(closed) if closed else 0.0,
        "resultCounts": {name: sum(item.get("portfolioResult", item["result"]) == name for item in records) for name in ("TP", "SL", "CANCELLED", "OPEN", "NO_TRIGGER", "NO_OBJECTIVE", "INVALID_GEOMETRY", "SKIPPED_POSITION_BUSY")},
        "boundary": "Deterministic destination-OB research replay; not the blind manual ground truth and not approved for live trading.",
    }
    (OUTPUT / "ledger.jsonl").write_text("".join(json.dumps(jsonable(item), ensure_ascii=False) + "\n" for item in records), encoding="utf-8")
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if records:
        keys = sorted({key for item in records for key in item})
        with (OUTPUT / "trades.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
