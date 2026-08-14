from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from build_mentor_q1_walkforward import (  # noqa: E402
    BG,
    BULL,
    BEAR,
    GRID,
    MUTED,
    Q1_FROM,
    Q1_TO,
    TEXT,
    build_candidates,
    candles,
    projected_x,
)
from mentor_engine.data import index_at_or_before, load_m1_npz  # noqa: E402
from mentor_engine.engine import MentorScenarioEngine  # noqa: E402
from mentor_engine.execution import simulate_order  # noqa: E402
from mentor_engine.models import (  # noqa: E402
    Direction,
    LiquidityKind,
    OrderPlan,
    ScenarioScope,
    Side,
    ZoneKind,
)


UTC = timezone.utc
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = ROOT / "output" / "mentor_manual_q1" / "manual_replay"
WARMUP_FROM = int(datetime(2024, 10, 1, tzinfo=UTC).timestamp())
REPLAY_TO = int(datetime(2025, 4, 15, tzinfo=UTC).timestamp())
TF_RANK = {"H4": 0, "H1": 1, "M30": 2, "M15": 3, "M5": 4, "M1": 5}

# This list was frozen from chronological, as-of chart review before any order
# was simulated. It intentionally retains structurally valid losing candidates.
MANUAL_ACCEPTED = {
    "Q1C001", "Q1C003", "Q1C005", "Q1C007", "Q1C009", "Q1C012",
    "Q1C013", "Q1C016", "Q1C017", "Q1C018", "Q1C019", "Q1C021",
    "Q1C022", "Q1C023", "Q1C024", "Q1C025", "Q1C030", "Q1C031",
    "Q1C032", "Q1C035", "Q1C036", "Q1C038", "Q1C041", "Q1C043",
    "Q1C047", "Q1C048", "Q1C050", "Q1C052", "Q1C053", "Q1C055",
    "Q1C058", "Q1C061", "Q1C063", "Q1C064", "Q1C067", "Q1C069",
    "Q1C070", "Q1C071", "Q1C072", "Q1C073", "Q1C076", "Q1C078",
    "Q1C079", "Q1C081", "Q1C082", "Q1C084", "Q1C087", "Q1C088",
    "Q1C090", "Q1C091", "Q1C093", "Q1C095", "Q1C096", "Q1C097",
    "Q1C099", "Q1C100", "Q1C104", "Q1C106", "Q1C107", "Q1C108",
    "Q1C111", "Q1C112", "Q1C120", "Q1C123", "Q1C127", "Q1C129",
    "Q1C132", "Q1C133", "Q1C136", "Q1C138", "Q1C140", "Q1C142",
    "Q1C143", "Q1C149", "Q1C150", "Q1C151", "Q1C155", "Q1C156",
    "Q1C157", "Q1C159", "Q1C160", "Q1C161", "Q1C163", "Q1C164",
    "Q1C165", "Q1C166", "Q1C167", "Q1C169", "Q1C170", "Q1C171",
}


def iso(timestamp: int | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def trend_at(engine: MentorScenarioEngine, timeframe: str, timestamp: int) -> int:
    state = engine.states[timeframe]
    index = index_at_or_before(state.series, timestamp)
    return int(state.structure.trend[index]) if index >= 0 else 0


def range_at(engine: MentorScenarioEngine, timeframe: str, timestamp: int) -> tuple[float, float]:
    state = engine.states[timeframe]
    index = index_at_or_before(state.series, timestamp)
    if index < 0:
        return float("nan"), float("nan")
    return float(state.structure.range_low[index]), float(state.structure.range_high[index])


def choose_source_zone(candidate: Any, zone_by_id: dict[str, Any]) -> Any | None:
    zones = [zone_by_id[item] for item in candidate.context_zone_ids if item in zone_by_id]
    if not zones:
        return None
    causal = [zone for zone in zones if zone.linked_structure_event_id]
    pool = causal or zones
    return max(pool, key=lambda zone: (TF_RANK[zone.timeframe], zone.available_at))


def choose_entry_zone(candidate: Any, zone_by_id: dict[str, Any]) -> Any | None:
    zones = [zone_by_id[item] for item in candidate.entry_zone_ids if item in zone_by_id]
    if not zones:
        return None
    fvg = [zone for zone in zones if zone.kind == ZoneKind.FVG]
    pool = fvg or [zone for zone in zones if zone.kind == ZoneKind.FVG_ORIGIN_OB]
    pool = pool or zones
    return min(pool, key=lambda zone: (zone.available_at, zone.top - zone.bottom, zone.object_id))


def classify_scope(engine: MentorScenarioEngine, direction: Direction, timestamp: int) -> tuple[ScenarioScope, str, dict[str, int]]:
    trends = {timeframe: trend_at(engine, timeframe, timestamp) for timeframe in ("H4", "H1", "M30")}
    sign = 1 if direction == Direction.LONG else -1
    aligned = [timeframe for timeframe, trend in trends.items() if trend == sign]
    if len(aligned) >= 2:
        return ScenarioScope.EXTERNAL_CONTINUATION, aligned[0], trends
    opposing = [timeframe for timeframe, trend in trends.items() if trend == -sign]
    return ScenarioScope.INTERNAL_ROTATION, (opposing[0] if opposing else "M30"), trends


def target_candidates(
    engine: MentorScenarioEngine,
    direction: Direction,
    timestamp: int,
    entry: float,
    scope: ScenarioScope,
    map_timeframe: str,
    trigger_level: float,
) -> list[tuple[float, int, int, str, str]]:
    if scope == ScenarioScope.EXTERNAL_CONTINUATION:
        timeframes = [map_timeframe] + [item for item in ("H4", "H1", "M30", "M15") if item != map_timeframe]
    else:
        timeframes = ["M15", "M30", "M5", "H1"]
    tf_order = {timeframe: index for index, timeframe in enumerate(timeframes)}
    kind_order = {
        LiquidityKind.EXTERNAL_SWING: 0,
        LiquidityKind.REACTION_TRAP: 1,
        LiquidityKind.RANGE_EDGE: 2,
        LiquidityKind.TRENDLINE_CLUSTER: 3,
    }
    result: list[tuple[float, int, int, str, str]] = []
    wanted_side = Side.HIGH if direction == Direction.LONG else Side.LOW
    for timeframe in timeframes:
        for pool in engine.states[timeframe].liquidity:
            if pool.side != wanted_side or not pool.active_at(timestamp):
                continue
            price = float(pool.level)
            if (direction == Direction.LONG and price <= max(entry, trigger_level)) or (
                direction == Direction.SHORT and price >= min(entry, trigger_level)
            ):
                continue
            result.append((abs(price - entry), tf_order[timeframe], kind_order[pool.kind], pool.object_id, "LIQUIDITY"))
    if result:
        return result
    # The mentor examples also use an unfilled delivery zone when it is the
    # first coherent destination inside the scenario scope.
    wanted_direction = Direction.SHORT if direction == Direction.LONG else Direction.LONG
    for timeframe in timeframes:
        for zone in engine.states[timeframe].zones:
            if zone.direction != wanted_direction or not zone.active_at(timestamp):
                continue
            bottom, top = zone.bounds_at(timestamp)
            price = bottom if direction == Direction.LONG else top
            if (direction == Direction.LONG and price <= max(entry, trigger_level)) or (
                direction == Direction.SHORT and price >= min(entry, trigger_level)
            ):
                continue
            result.append((abs(price - entry), tf_order[timeframe], 4, zone.object_id, "DELIVERY_ZONE"))
    return result


def choose_objective(
    engine: MentorScenarioEngine,
    direction: Direction,
    timestamp: int,
    entry: float,
    scope: ScenarioScope,
    map_timeframe: str,
    trigger_level: float,
) -> tuple[str, str, float] | None:
    candidates = target_candidates(
        engine,
        direction,
        timestamp,
        entry,
        scope,
        map_timeframe,
        trigger_level,
    )
    if not candidates:
        return None
    # Scope comes before distance: prefer the intended map/context timeframe,
    # then the first reachable object on that timeframe.
    distance, _, _, object_id, kind = min(candidates, key=lambda item: (item[1], item[0], item[2], item[3]))
    if kind == "LIQUIDITY":
        obj = next(pool for state in engine.states.values() for pool in state.liquidity if pool.object_id == object_id)
        return kind, object_id, float(obj.level)
    obj = next(zone for state in engine.states.values() for zone in state.zones if zone.object_id == object_id)
    bottom, top = obj.bounds_at(timestamp)
    return kind, object_id, float(bottom if direction == Direction.LONG else top)


def build_plan(engine: MentorScenarioEngine, candidate: Any, zone_by_id: dict[str, Any]) -> tuple[OrderPlan | None, dict[str, Any]]:
    direction = Direction(candidate.direction)
    source_zone = choose_source_zone(candidate, zone_by_id)
    entry_zone = choose_entry_zone(candidate, zone_by_id)
    decision: dict[str, Any] = {
        "candidateId": candidate.candidate_id,
        "direction": direction.value,
        "sweepAt": iso(candidate.sweep_at),
        "triggerAt": iso(candidate.trigger_at),
        "manualSelectedBeforeReplay": candidate.candidate_id in MANUAL_ACCEPTED,
    }
    if candidate.candidate_id not in MANUAL_ACCEPTED:
        decision.update(state="REJECTED", reason="MANUAL_ASOF_MAP_CONTRACT_NOT_COMPLETE")
        return None, decision
    if source_zone is None or entry_zone is None or candidate.trigger_at is None:
        decision.update(state="REJECTED", reason="MISSING_SOURCE_OR_ENTRY_LINEAGE")
        return None, decision

    scope, map_timeframe, trends = classify_scope(engine, direction, candidate.trigger_at)
    entry_bottom, entry_top = entry_zone.bounds_at(entry_zone.available_at)
    entry = float(entry_top if direction == Direction.LONG else entry_bottom)
    low, high = range_at(engine, map_timeframe, candidate.trigger_at)
    midpoint = (low + high) / 2.0 if np.isfinite(low) and np.isfinite(high) and high > low else None
    pd_ok = midpoint is None or (
        candidate.sweep_extreme <= midpoint if direction == Direction.LONG else candidate.sweep_extreme >= midpoint
    )
    if scope == ScenarioScope.EXTERNAL_CONTINUATION and not pd_ok:
        decision.update(
            state="REJECTED",
            reason="CONTINUATION_OUTSIDE_REQUIRED_50_PERCENT_HALF",
            scope=scope.value,
            mapTimeframe=map_timeframe,
            mapTrends=trends,
            dealingRangeMid=midpoint,
        )
        return None, decision

    objective = choose_objective(
        engine,
        direction,
        entry_zone.available_at,
        entry,
        scope,
        map_timeframe,
        float(candidate.trigger_level),
    )
    if objective is None:
        decision.update(state="REJECTED", reason="NO_SCOPE_COMPATIBLE_LIVE_OBJECTIVE")
        return None, decision

    m1 = engine.states["M1"].series
    m1_index = index_at_or_before(m1, entry_zone.available_at)
    excursion_start = int(np.searchsorted(m1.available_time, candidate.sweep_at - 45 * 60, side="left"))
    excursion_end = int(np.searchsorted(m1.available_time, candidate.trigger_at, side="right"))
    if direction == Direction.LONG:
        reaction_extreme = float(np.min(m1.low[excursion_start:excursion_end]))
    else:
        reaction_extreme = float(np.max(m1.high[excursion_start:excursion_end]))
    spread = float(m1.spread_points[m1_index]) * engine.config.point
    buffer = max(spread, engine.config.point, engine.config.broker_stops_level_price)
    stop = (
        min(reaction_extreme, float(entry_bottom)) - buffer
        if direction == Direction.LONG
        else max(reaction_extreme, float(entry_top)) + buffer
    )
    objective_kind, objective_id, take_profit = objective
    valid = stop < entry < take_profit if direction == Direction.LONG else take_profit < entry < stop
    if not valid:
        decision.update(state="REJECTED", reason="INVALID_STRUCTURAL_GEOMETRY")
        return None, decision

    plan = OrderPlan(
        order_id=f"manual:{candidate.candidate_id}",
        scenario_id=f"manual-scenario:{candidate.candidate_id}",
        direction=direction,
        created_at=int(entry_zone.available_at),
        entry=entry,
        stop_loss=float(stop),
        take_profit=float(take_profit),
        entry_zone_id=entry_zone.object_id,
        entry_zone_bottom=float(entry_bottom),
        entry_zone_top=float(entry_top),
        source_sweep_extreme=reaction_extreme,
        spread_price=float(spread),
        map_timeframe=map_timeframe,
        context_timeframe=source_zone.timeframe,
        trigger_timeframe=str(candidate.trigger_timeframe),
        objective_id=objective_id,
        cancel_structure_level=None,
        protective_zone_bottom=float(entry_bottom),
        protective_zone_top=float(entry_top),
        entry_family_zone_ids=tuple(candidate.entry_zone_ids),
        parent_zone_ids=tuple(candidate.context_zone_ids),
    )
    decision.update(
        state="ORDER_PLANNED",
        reason="COMPLETE_MENTOR_CONTRACT",
        scope=scope.value,
        mapTimeframe=map_timeframe,
        mapTrends=trends,
        sourceTimeframe=source_zone.timeframe,
        sourceZoneId=source_zone.object_id,
        triggerTimeframe=candidate.trigger_timeframe,
        triggerEventId=candidate.trigger_event_id,
        entryZoneId=entry_zone.object_id,
        objectiveKind=objective_kind,
        objectiveId=objective_id,
        dealingRangeMid=midpoint,
        pdOk=pd_ok,
        sourceSweepCandleExtreme=float(candidate.sweep_extreme),
        finalReactionExcursionExtreme=reaction_extreme,
    )
    return plan, decision


def adaptive_timeframe(holding_minutes: int | None) -> str:
    holding = holding_minutes or 0
    if holding <= 6 * 60:
        return "M1"
    if holding <= 24 * 60:
        return "M5"
    if holding <= 3 * 24 * 60:
        return "M15"
    if holding <= 7 * 24 * 60:
        return "M30"
    return "H1"


def draw_position_box(axis: Any, series: Any, left: int, right: int, plan: OrderPlan, trade: Any) -> None:
    if trade.entry_time is None:
        return
    end_time = trade.exit_time or int(series.available_time[right - 1])
    x0 = projected_x(series, left, right, trade.entry_time)
    x1 = max(x0 + 0.8, projected_x(series, left, right, end_time))
    reward_bottom = min(plan.entry, plan.take_profit)
    reward_top = max(plan.entry, plan.take_profit)
    risk_bottom = min(plan.entry, plan.stop_loss)
    risk_top = max(plan.entry, plan.stop_loss)
    axis.add_patch(Rectangle((x0, reward_bottom), x1 - x0, reward_top - reward_bottom, facecolor="#34d399", edgecolor="#34d399", linewidth=0.8, alpha=0.20, zorder=2))
    axis.add_patch(Rectangle((x0, risk_bottom), x1 - x0, risk_top - risk_bottom, facecolor="#fb7185", edgecolor="#fb7185", linewidth=0.8, alpha=0.20, zorder=2))


def draw_relevant_zones(axis: Any, series: Any, left: int, right: int, zones: list[Any], cutoff: int) -> None:
    colours = {ZoneKind.FVG: "#2563eb", ZoneKind.FVG_ORIGIN_OB: "#d97706", ZoneKind.LAST_OPPOSITE_OB: "#7c3aed"}
    for zone in zones:
        start = max(int(series.available_time[left]), zone.available_at)
        end = min(cutoff, zone.consumed_at or cutoff)
        if end <= start:
            continue
        x0 = projected_x(series, left, right, start)
        x1 = max(x0 + 0.8, projected_x(series, left, right, end))
        colour = colours[zone.kind]
        axis.add_patch(Rectangle((x0, zone.bottom), x1 - x0, zone.top - zone.bottom, facecolor=colour, edgecolor=colour, linewidth=0.7, alpha=0.12, zorder=1))
        axis.text((x0 + x1) / 2.0, (zone.bottom + zone.top) / 2.0, "FVG" if zone.kind == ZoneKind.FVG else "OB", color="#cbd5e1", fontsize=5.8, ha="center", va="center", zorder=3)


def render_trade(engine: MentorScenarioEngine, candidate: Any, plan: OrderPlan, trade: Any, zone_by_id: dict[str, Any], number: int) -> str:
    detail_tf = adaptive_timeframe(trade.holding_minutes)
    panels = (plan.map_timeframe, plan.context_timeframe, detail_tf)
    start = min(candidate.sweep_at, trade.entry_time or plan.created_at)
    end = trade.exit_time or min(REPLAY_TO, start + 3 * 24 * 60 * 60)
    fig, axes = plt.subplots(3, 1, figsize=(12, 11), constrained_layout=True)
    relevant = [zone_by_id[item] for item in list(plan.parent_zone_ids) + list(plan.entry_family_zone_ids) if item in zone_by_id]
    for axis, timeframe in zip(axes, panels):
        series = engine.states[timeframe].series
        pad_before = {"H4": 18, "H1": 40, "M30": 55, "M15": 70, "M5": 100, "M1": 150}[timeframe]
        pad_after = max(8, pad_before // 4)
        left = max(0, int(np.searchsorted(series.available_time, start, side="left")) - pad_before)
        right = min(len(series), int(np.searchsorted(series.available_time, end, side="right")) + pad_after)
        right = max(left + 2, right)
        candles(axis, series, left, right)
        draw_relevant_zones(axis, series, left, right, [zone for zone in relevant if zone.timeframe == timeframe], end)
        draw_position_box(axis, series, left, right, plan, trade)
        visible_low = float(np.min(series.low[left:right]))
        visible_high = float(np.max(series.high[left:right]))
        low = min(visible_low, plan.entry, plan.stop_loss, plan.take_profit)
        high = max(visible_high, plan.entry, plan.stop_loss, plan.take_profit)
        margin = max((high - low) * 0.05, 0.25)
        axis.set_ylim(low - margin, high + margin)
        axis.set_title(f"{timeframe}  |  map={plan.map_timeframe} context={plan.context_timeframe} trigger={plan.trigger_timeframe}", loc="left", color=TEXT, fontsize=9.5, fontweight="bold")
        axis.set_facecolor(BG)
        axis.grid(color=GRID, linewidth=0.45, alpha=0.30)
        axis.tick_params(colors=MUTED, labelsize=7)
        axis.yaxis.tick_right()
        for spine in axis.spines.values():
            spine.set_color(GRID)
    result_colour = "#34d399" if trade.result == "TP" else "#fb7185" if trade.result == "SL" else "#fbbf24"
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"#{number:02d} {candidate.candidate_id}  {candidate.direction.upper()}  {trade.result}  {trade.pnl_r:+.2f}R  |  hold {trade.holding_minutes if trade.holding_minutes is not None else '-'}m",
        color=result_colour,
        fontsize=14,
        fontweight="bold",
    )
    directory = OUTPUT / "trade_charts"
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{number:02d}_{candidate.candidate_id}_{candidate.direction}_{trade.result}.png"
    fig.savefig(directory / filename, dpi=125, facecolor=BG, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return f"trade_charts/{filename}"


def write_csv(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with (OUTPUT / "trades.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-charts", action="store_true", help="calculate the replay without rendering trade charts")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    m1, _ = load_m1_npz(DATASET, start=WARMUP_FROM, end=REPLAY_TO)
    engine = MentorScenarioEngine(m1)
    engine.prepare()
    candidates = build_candidates(engine)
    candidate_by_id = {item.candidate_id: item for item in candidates}
    zone_by_id = {zone.object_id: zone for state in engine.states.values() for zone in state.zones}

    decisions: list[dict[str, Any]] = []
    plans: list[tuple[Any, OrderPlan, dict[str, Any]]] = []
    for candidate in candidates:
        plan, decision = build_plan(engine, candidate, zone_by_id)
        decisions.append(decision)
        if plan is not None:
            plans.append((candidate, plan, decision))

    rows: list[dict[str, Any]] = []
    results = []
    for candidate, plan, decision in sorted(plans, key=lambda item: (item[1].created_at, item[0].candidate_id)):
        trade = simulate_order(m1, plan, zone_by_id[plan.entry_zone_id], engine.config.point, REPLAY_TO)
        results.append((candidate, plan, trade, decision))

    filled = [item for item in results if item[2].entry_time is not None]
    if not args.no_charts:
        chart_directory = OUTPUT / "trade_charts"
        if chart_directory.exists():
            for path in chart_directory.glob("*.png"):
                path.unlink()
    for number, (candidate, plan, trade, decision) in enumerate(filled, start=1):
        chart = "" if args.no_charts else render_trade(engine, candidate, plan, trade, zone_by_id, number)
        risk = abs(plan.entry - plan.stop_loss)
        rows.append(
            {
                "trade_no": number,
                "candidate_id": candidate.candidate_id,
                "direction": candidate.direction,
                "scope": decision["scope"],
                "map_tf": plan.map_timeframe,
                "context_tf": plan.context_timeframe,
                "trigger_tf": plan.trigger_timeframe,
                "sweep_time": iso(candidate.sweep_at),
                "order_time": iso(plan.created_at),
                "entry_time": iso(trade.entry_time),
                "exit_time": iso(trade.exit_time),
                "entry": round(plan.entry, 3),
                "stop_loss": round(plan.stop_loss, 3),
                "take_profit": round(plan.take_profit, 3),
                "planned_r": round(abs(plan.take_profit - plan.entry) / risk, 3),
                "result": trade.result,
                "pnl_r": round(trade.pnl_r, 3),
                "holding_minutes": trade.holding_minutes,
                "source_zone_id": decision["sourceZoneId"],
                "entry_zone_id": plan.entry_zone_id,
                "objective_id": plan.objective_id,
                "chart": chart,
            }
        )

    decision_by_id = {item["candidateId"]: item for item in decisions}
    for candidate, plan, trade, _ in results:
        decision_by_id[candidate.candidate_id]["executionResult"] = trade.result
        decision_by_id[candidate.candidate_id]["entryTime"] = iso(trade.entry_time)
        decision_by_id[candidate.candidate_id]["exitTime"] = iso(trade.exit_time)

    write_csv(rows)
    (OUTPUT / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / "trades.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    closed = [row for row in rows if row["result"] in {"TP", "SL"}]
    wins = [row for row in closed if row["result"] == "TP"]
    losses = [row for row in closed if row["result"] == "SL"]
    gross_win = sum(float(row["pnl_r"]) for row in wins)
    gross_loss = abs(sum(float(row["pnl_r"]) for row in losses))
    summary = {
        "schema": "mentor-q1-manual-asof-replay-v1",
        "period": {"candidateFrom": iso(Q1_FROM), "candidateTo": iso(Q1_TO), "executionObservedTo": iso(REPLAY_TO)},
        "method": "Chronological as-of manual Mentor Protocol selection frozen before deterministic bid/ask replay.",
        "candidateEpisodes": len(candidates),
        "manualAcceptedBeforeGeometry": len(MANUAL_ACCEPTED),
        "ordersPlannedAfterGeometry": len(plans),
        "executionStates": dict(Counter(item[2].result for item in results)),
        "filledTrades": len(rows),
        "closedTrades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "winRatePct": round(100.0 * len(wins) / len(closed), 2) if closed else 0.0,
        "netR": round(sum(float(row["pnl_r"]) for row in closed), 3),
        "profitFactor": round(gross_win / gross_loss, 3) if gross_loss else None,
        "averageR": round(sum(float(row["pnl_r"]) for row in closed) / len(closed), 3) if closed else 0.0,
        "medianHoldingMinutes": int(np.median([row["holding_minutes"] for row in closed if row["holding_minutes"] is not None])) if closed else None,
        "decisionStates": dict(Counter(item["reason"] for item in decisions)),
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Mentor Q1 Manual As-Of Replay",
        "",
        "후보 선정은 체결 결과 계산 전에 고정했으며, 각 후보는 해당 trigger 시점 이전 데이터만으로 판단했다.",
        "",
        f"- Q1 physical sweep episodes: {summary['candidateEpisodes']}",
        f"- frozen manual selections: {summary['manualAcceptedBeforeGeometry']}",
        f"- filled / closed: {summary['filledTrades']} / {summary['closedTrades']}",
        f"- wins / losses: {summary['wins']} / {summary['losses']}",
        f"- win rate: {summary['winRatePct']}%",
        f"- net: {summary['netR']:+.3f}R",
        f"- profit factor: {summary['profitFactor']}",
        "",
        "| # | 시각(UTC) | 방향 | 범위 | MTF | 결과 | R | 보유 | 차트 |",
        "|---:|---|---|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        holding = f"{row['holding_minutes'] // 60}h {row['holding_minutes'] % 60}m" if row["holding_minutes"] is not None else "-"
        chart_link = f"[{row['candidate_id']}]({row['chart']})" if row["chart"] else row["candidate_id"]
        lines.append(
            f"| {row['trade_no']} | {row['entry_time'][:16] if row['entry_time'] else '-'} | {row['direction']} | {row['scope']} | {row['map_tf']}→{row['context_tf']}→{row['trigger_tf']} | {row['result']} | {row['pnl_r']:+.3f} | {holding} | {chart_link} |"
        )
    (OUTPUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
