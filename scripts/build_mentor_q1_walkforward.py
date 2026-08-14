from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
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

from mentor_engine.data import index_at_or_before, load_m1_npz
from mentor_engine.engine import MentorScenarioEngine
from mentor_engine.models import Direction, Side, ZoneKind


UTC = timezone.utc
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = ROOT / "output" / "mentor_manual_q1"
Q1_FROM = int(datetime(2025, 1, 1, tzinfo=UTC).timestamp())
Q1_TO = int(datetime(2025, 4, 1, tzinfo=UTC).timestamp())
WARMUP_FROM = int(datetime(2024, 10, 1, tzinfo=UTC).timestamp())

TIMEFRAMES = ("H4", "H1", "M30", "M15", "M5", "M1")
SOURCE_TIMEFRAMES = ("H4", "H1", "M30", "M15")
TRIGGER_TIMEFRAMES = ("M5", "M1")
WINDOWS = {"H4": 95, "H1": 135, "M30": 170, "M15": 210, "M5": 260, "M1": 330}
TF_RANK = {"H4": 0, "H1": 1, "M30": 2, "M15": 3, "M5": 4, "M1": 5}

BG = "#080c12"
GRID = "#263241"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
BULL = "#5eead4"
BEAR = "#f87171"
ZONE_COLOURS = {
    ZoneKind.FVG: "#2563eb",
    ZoneKind.FVG_ORIGIN_OB: "#d97706",
    ZoneKind.LAST_OPPOSITE_OB: "#7c3aed",
}


def iso(timestamp: int | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


@dataclass
class Candidate:
    candidate_id: str
    direction: str
    sweep_at: int
    sweep_timeframes: list[str]
    sweep_ids: list[str]
    sweep_pool_kinds: list[str]
    sweep_levels: list[float]
    sweep_extreme: float
    context_zone_ids: list[str]
    context_timeframes: list[str]
    trigger_at: int | None
    trigger_timeframe: str | None
    trigger_event_id: str | None
    trigger_level: float | None
    entry_zone_ids: list[str]
    review_state: str
    chart: str | None = None


def candle_bounds(engine: MentorScenarioEngine, timeframe: str, timestamp: int) -> tuple[float, float]:
    series = engine.states[timeframe].series
    index = index_at_or_before(series, timestamp)
    if index < 0:
        return float("nan"), float("nan")
    return float(series.low[index]), float(series.high[index])


def zones_touched_by_sweep(engine: MentorScenarioEngine, sweep: Any, direction: Direction) -> list[Any]:
    low, high = candle_bounds(engine, sweep.timeframe, sweep.available_at)
    if not np.isfinite(low) or not np.isfinite(high):
        return []
    matches: list[Any] = []
    for timeframe in ("H4", "H1", "M30", "M15", "M5"):
        for zone in engine.states[timeframe].zones:
            if zone.direction != direction or zone.available_at > sweep.available_at:
                continue
            if zone.consumed_at is not None and zone.consumed_at < sweep.available_at:
                continue
            bottom, top = zone.bounds_at(sweep.available_at)
            if high >= bottom and low <= top:
                matches.append(zone)
    matches.sort(
        key=lambda zone: (
            TF_RANK[zone.timeframe],
            abs(((zone.bottom + zone.top) / 2.0) - sweep.extreme),
            -zone.available_at,
        )
    )
    selected: list[Any] = []
    used_tf: set[str] = set()
    for zone in matches:
        if zone.timeframe in used_tf:
            continue
        selected.append(zone)
        used_tf.add(zone.timeframe)
        if len(selected) == 4:
            break
    return selected


def group_sweeps(engine: MentorScenarioEngine) -> list[list[Any]]:
    source = sorted(
        (
            sweep
            for timeframe in SOURCE_TIMEFRAMES
            for sweep in engine.states[timeframe].sweeps
            if Q1_FROM <= sweep.available_at < Q1_TO
        ),
        key=lambda item: (item.available_at, TF_RANK[item.timeframe], item.event_id),
    )
    groups: list[list[Any]] = []
    for sweep in source:
        direction = Direction.SHORT if sweep.side == Side.HIGH else Direction.LONG
        compatible = None
        for group in reversed(groups[-5:]):
            first = group[0]
            first_direction = Direction.SHORT if first.side == Side.HIGH else Direction.LONG
            if first_direction != direction:
                continue
            if sweep.available_at - max(item.available_at for item in group) > 45 * 60:
                continue
            # One reaction can sweep nested levels on several timeframes. Price
            # distance is deliberately not used to invent a relationship.
            compatible = group
            break
        if compatible is None:
            groups.append([sweep])
        else:
            compatible.append(sweep)
    return groups


def linked_entry_zones(engine: MentorScenarioEngine, event: Any) -> list[Any]:
    zones = [
        zone
        for zone in engine.states[event.timeframe].zones
        if zone.direction == event.direction
        and zone.linked_structure_event_id == event.event_id
        and zone.available_at >= event.available_at
    ]
    zones.sort(
        key=lambda zone: (
            0 if zone.kind == ZoneKind.FVG else 1,
            zone.available_at,
            zone.object_id,
        )
    )
    return zones


def first_trigger(engine: MentorScenarioEngine, group: list[Any], direction: Direction) -> tuple[Any | None, list[Any]]:
    start = max(item.available_at for item in group)
    # The horizon only bounds the review packet. It is not a trading expiry;
    # a later reversal is treated as a new market episode.
    stop = start + 12 * 60 * 60
    events = sorted(
        (
            event
            for timeframe in TRIGGER_TIMEFRAMES
            for event in engine.states[timeframe].structure.events
            if event.event_type == "CHOCH"
            and event.direction == direction
            and start < event.available_at <= stop
        ),
        key=lambda item: (item.available_at, TF_RANK[item.timeframe], item.event_id),
    )
    for event in events:
        zones = linked_entry_zones(engine, event)
        if zones:
            return event, zones
    return None, []


def build_candidates(engine: MentorScenarioEngine) -> list[Candidate]:
    candidates: list[Candidate] = []
    for number, group in enumerate(group_sweeps(engine), start=1):
        group = sorted(group, key=lambda item: (item.available_at, TF_RANK[item.timeframe]))
        direction = Direction.SHORT if group[-1].side == Side.HIGH else Direction.LONG
        all_context = []
        for sweep in group:
            all_context.extend(zones_touched_by_sweep(engine, sweep, direction))
        unique_context = {zone.object_id: zone for zone in all_context}
        context = sorted(unique_context.values(), key=lambda zone: (TF_RANK[zone.timeframe], zone.available_at))
        trigger, entry_zones = first_trigger(engine, group, direction)
        if not context:
            state = "NO_SOURCE_ZONE"
        elif trigger is None:
            state = "NO_LTF_CHOCH_ZONE"
        else:
            state = "REQUIRES_MANUAL_MAP_REVIEW"
        candidates.append(
            Candidate(
                candidate_id=f"Q1C{number:03d}",
                direction=direction.value,
                sweep_at=max(item.available_at for item in group),
                sweep_timeframes=sorted({item.timeframe for item in group}, key=TF_RANK.get),
                sweep_ids=[item.event_id for item in group],
                sweep_pool_kinds=sorted({item.pool_kind.value for item in group}),
                sweep_levels=[float(item.close) for item in group],
                sweep_extreme=(
                    max(float(item.extreme) for item in group)
                    if direction == Direction.SHORT
                    else min(float(item.extreme) for item in group)
                ),
                context_zone_ids=[zone.object_id for zone in context[:6]],
                context_timeframes=sorted({zone.timeframe for zone in context}, key=TF_RANK.get),
                trigger_at=trigger.available_at if trigger else None,
                trigger_timeframe=trigger.timeframe if trigger else None,
                trigger_event_id=trigger.event_id if trigger else None,
                trigger_level=float(trigger.broken_level) if trigger else None,
                entry_zone_ids=[zone.object_id for zone in entry_zones],
                review_state=state,
            )
        )
    return candidates


def projected_x(series: Any, left: int, right: int, timestamp: int) -> float:
    index = int(np.searchsorted(series.available_time, timestamp, side="left"))
    return float(np.clip(index - left, 0, max(1, right - left - 1)))


def candles(axis: Any, series: Any, left: int, right: int) -> None:
    for x, index in enumerate(range(left, right)):
        colour = BULL if series.close[index] >= series.open[index] else BEAR
        axis.vlines(x, series.low[index], series.high[index], color=colour, linewidth=0.55, zorder=4)
        bottom = min(series.open[index], series.close[index])
        height = max(abs(series.close[index] - series.open[index]), 1e-6)
        axis.add_patch(Rectangle((x - 0.34, bottom), 0.68, height, facecolor=colour, edgecolor=colour, linewidth=0.3, zorder=5))
    count = right - left
    ticks = np.unique(np.linspace(0, count - 1, min(6, count), dtype=int))
    labels = [datetime.fromtimestamp(int(series.available_time[left + item]), tz=UTC).strftime("%m-%d\n%H:%M") for item in ticks]
    axis.set_xticks(ticks, labels)


def draw_zone(axis: Any, series: Any, left: int, right: int, zone: Any, cutoff: int, strong: bool = False) -> None:
    panel_start = int(series.available_time[left])
    start = max(zone.available_at, panel_start)
    end = min(zone.consumed_at or cutoff, cutoff)
    if end <= start:
        return
    x0 = projected_x(series, left, right, start)
    x1 = max(projected_x(series, left, right, end), x0 + 1.0)
    colour = ZONE_COLOURS.get(zone.kind, "#64748b")
    axis.add_patch(
        Rectangle(
            (x0, zone.bottom),
            x1 - x0,
            zone.top - zone.bottom,
            facecolor=colour,
            edgecolor=colour,
            linewidth=1.35 if strong else 0.65,
            alpha=0.28 if strong else 0.10,
            zorder=2,
        )
    )
    if strong:
        axis.text((x0 + x1) / 2, (zone.bottom + zone.top) / 2, zone.kind.value.replace("LAST_OPPOSITE_", ""), color=TEXT, fontsize=6.0, ha="center", va="center", zorder=7)


def nearby_objects(engine: MentorScenarioEngine, timeframe: str, cutoff: int, price: float) -> tuple[list[Any], list[Any]]:
    state = engine.states[timeframe]
    zones = [zone for zone in state.zones if zone.active_at(cutoff) and zone.available_at <= cutoff]
    zones.sort(key=lambda zone: (abs((zone.bottom + zone.top) / 2 - price), -zone.available_at))
    pools = [pool for pool in state.liquidity if pool.active_at(cutoff) and pool.available_at <= cutoff]
    above = sorted((pool for pool in pools if pool.level >= price), key=lambda pool: pool.level)[:2]
    below = sorted((pool for pool in pools if pool.level < price), key=lambda pool: pool.level, reverse=True)[:2]
    return zones[:5], above + below


def render_candidate(engine: MentorScenarioEngine, candidate: Candidate, zone_by_id: dict[str, Any]) -> str:
    cutoff = candidate.trigger_at or candidate.sweep_at
    m1 = engine.states["M1"].series
    m1_index = index_at_or_before(m1, cutoff)
    price = float(m1.close[m1_index])
    fig, axes = plt.subplots(3, 2, figsize=(15, 12), constrained_layout=True)
    axes = axes.ravel()
    context_ids = set(candidate.context_zone_ids)
    entry_ids = set(candidate.entry_zone_ids)
    for axis, timeframe in zip(axes, TIMEFRAMES):
        state = engine.states[timeframe]
        series = state.series
        right = int(np.searchsorted(series.available_time, cutoff, side="right"))
        right = max(2, right)
        left = max(0, right - WINDOWS[timeframe])
        candles(axis, series, left, right)
        zones, pools = nearby_objects(engine, timeframe, cutoff, price)
        chosen = {zone.object_id: zone for zone in zones}
        for object_id in context_ids | entry_ids:
            zone = zone_by_id.get(object_id)
            if zone is not None and zone.timeframe == timeframe:
                chosen[object_id] = zone
        for zone in chosen.values():
            draw_zone(axis, series, left, right, zone, cutoff, zone.object_id in context_ids | entry_ids)
        for pool in pools:
            axis.axhline(pool.level, color="#c084fc", linewidth=0.55, linestyle=(0, (4, 3)), alpha=0.65)
        axis.axhline(candidate.sweep_extreme, color="#fbbf24", linewidth=0.85, linestyle=(0, (6, 3)), alpha=0.95)
        axis.text(0.995, candidate.sweep_extreme, "SWEEP", transform=axis.get_yaxis_transform(), color="#fbbf24", fontsize=6.1, ha="right", va="bottom")
        if candidate.trigger_level is not None:
            axis.axhline(candidate.trigger_level, color="#38bdf8", linewidth=0.8, linestyle=(0, (3, 2)), alpha=0.9)
            axis.text(0.01, candidate.trigger_level, "CHoCH", transform=axis.get_yaxis_transform(), color="#38bdf8", fontsize=6.1, ha="left", va="bottom")
        index = index_at_or_before(series, cutoff)
        trend = int(state.structure.trend[index]) if index >= 0 else 0
        axis.set_title(f"{timeframe}  trend={trend:+d}", loc="left", color=TEXT, fontsize=9.5, fontweight="bold")
        axis.set_facecolor(BG)
        axis.grid(color=GRID, linewidth=0.45, alpha=0.3)
        axis.tick_params(colors=MUTED, labelsize=7)
        axis.yaxis.tick_right()
        for spine in axis.spines.values():
            spine.set_color(GRID)
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"{candidate.candidate_id}  {candidate.direction.upper()}  AS-OF {datetime.fromtimestamp(cutoff, tz=UTC):%Y-%m-%d %H:%M} UTC  |  {candidate.review_state}",
        color=TEXT,
        fontsize=13,
        fontweight="bold",
    )
    directory = OUTPUT / "candidate_charts"
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{candidate.candidate_id}_{datetime.fromtimestamp(candidate.sweep_at, tz=UTC):%Y-%m-%d_%H%M}_{candidate.direction}.png"
    fig.savefig(directory / filename, dpi=135, facecolor=BG, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return f"candidate_charts/{filename}"


def _panel_range(series: Any, start: int, end: int, prefix: int) -> tuple[int, int]:
    left = int(np.searchsorted(series.available_time, start, side="left"))
    right = int(np.searchsorted(series.available_time, end, side="right"))
    left = max(0, left - prefix)
    right = min(len(series), max(left + 2, right))
    return left, right


def render_daily_overview(
    engine: MentorScenarioEngine,
    day: str,
    candidates: list[Candidate],
    zone_by_id: dict[str, Any],
) -> str:
    day_start = int(datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp())
    day_end = day_start + 24 * 60 * 60
    m1 = engine.states["M1"].series
    price_index = index_at_or_before(m1, day_start)
    price = float(m1.close[price_index])
    fig, axes = plt.subplots(3, 2, figsize=(15, 12), constrained_layout=True)
    plot_axes = axes.ravel()
    plot_specs = (
        ("H4", day_start, WINDOWS["H4"]),
        ("H1", day_start, WINDOWS["H1"]),
        ("M30", day_end, 20),
        ("M15", day_end, 28),
        ("M5", day_end, 48),
    )
    day_zone_ids = {
        object_id
        for candidate in candidates
        for object_id in candidate.context_zone_ids + candidate.entry_zone_ids
    }
    for axis, (timeframe, cutoff, prefix) in zip(plot_axes[:5], plot_specs):
        state = engine.states[timeframe]
        series = state.series
        if timeframe in {"H4", "H1"}:
            right = int(np.searchsorted(series.available_time, day_start, side="right"))
            right = max(2, right)
            left = max(0, right - prefix)
            panel_cutoff = day_start
        else:
            left, right = _panel_range(series, day_start, day_end, prefix)
            panel_cutoff = day_end
        candles(axis, series, left, right)
        zones, pools = nearby_objects(engine, timeframe, min(panel_cutoff, day_end), price)
        chosen = {zone.object_id: zone for zone in zones}
        for object_id in day_zone_ids:
            zone = zone_by_id.get(object_id)
            if zone is not None and zone.timeframe == timeframe and zone.available_at <= panel_cutoff:
                chosen[object_id] = zone
        for zone in chosen.values():
            draw_zone(axis, series, left, right, zone, panel_cutoff, zone.object_id in day_zone_ids)
        for pool in pools:
            axis.axhline(pool.level, color="#c084fc", linewidth=0.5, linestyle=(0, (4, 3)), alpha=0.55)
        for candidate in candidates:
            if timeframe in {"H4", "H1"}:
                continue
            x = projected_x(series, left, right, candidate.sweep_at)
            colour = "#fb7185" if candidate.direction == "short" else "#34d399"
            axis.axvline(x, color=colour, linewidth=0.65, alpha=0.65)
            axis.text(x, candidate.sweep_extreme, candidate.candidate_id, color=colour, fontsize=5.5, ha="center", va="bottom")
        index = index_at_or_before(series, min(panel_cutoff, day_end))
        trend = int(state.structure.trend[index]) if index >= 0 else 0
        suffix = "MAP @ 00:00" if timeframe in {"H4", "H1"} else "FULL DAY REPLAY"
        axis.set_title(f"{timeframe}  trend={trend:+d}  |  {suffix}", loc="left", color=TEXT, fontsize=9.5, fontweight="bold")
        axis.set_facecolor(BG)
        axis.grid(color=GRID, linewidth=0.45, alpha=0.3)
        axis.tick_params(colors=MUTED, labelsize=7)
        axis.yaxis.tick_right()
        for spine in axis.spines.values():
            spine.set_color(GRID)

    text_axis = plot_axes[5]
    text_axis.set_facecolor(BG)
    text_axis.axis("off")
    lines = [f"{day} candidate episodes", ""]
    if not candidates:
        lines.append("No H4/H1/M30/M15 liquidity-sweep episode")
    for candidate in candidates:
        sweep_text = datetime.fromtimestamp(candidate.sweep_at, tz=UTC).strftime("%H:%M")
        trigger_text = datetime.fromtimestamp(candidate.trigger_at, tz=UTC).strftime("%H:%M") if candidate.trigger_at else "-"
        lines.extend(
            [
                f"{candidate.candidate_id}  {candidate.direction.upper()}  sweep {sweep_text}  trigger {trigger_text}",
                f"  sweep TF {','.join(candidate.sweep_timeframes)}  source TF {','.join(candidate.context_timeframes) or '-'}",
                f"  {candidate.review_state}",
                "",
            ]
        )
    text_axis.text(0.02, 0.98, "\n".join(lines), transform=text_axis.transAxes, color=TEXT, fontsize=8.5, ha="left", va="top", family="monospace")
    fig.patch.set_facecolor(BG)
    fig.suptitle(f"MENTOR Q1 DAILY WALK-FORWARD  |  {day} UTC", color=TEXT, fontsize=14, fontweight="bold")
    directory = OUTPUT / "daily_overviews"
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{day}.png"
    fig.savefig(directory / filename, dpi=135, facecolor=BG, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return f"daily_overviews/{filename}"


def write_manifest(
    engine: MentorScenarioEngine,
    candidates: list[Candidate],
    render: bool,
    render_daily: bool,
    render_ids: set[str],
) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    zone_by_id = {
        zone.object_id: zone
        for state in engine.states.values()
        for zone in state.zones
    }
    if render or render_ids:
        for index, candidate in enumerate(candidates, start=1):
            selected = render or candidate.candidate_id in render_ids
            if selected and candidate.review_state == "REQUIRES_MANUAL_MAP_REVIEW":
                candidate.chart = render_candidate(engine, candidate, zone_by_id)
            if index % 25 == 0:
                print(f"RENDERED={index}/{len(candidates)}", flush=True)

    payload = []
    for candidate in candidates:
        item = asdict(candidate)
        item["sweep_at_utc"] = iso(candidate.sweep_at)
        item["trigger_at_utc"] = iso(candidate.trigger_at)
        payload.append(item)
    (OUTPUT / "candidate_manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    m1 = engine.states["M1"].series
    q1_mask = (m1.available_time >= Q1_FROM) & (m1.available_time < Q1_TO)
    trading_days = sorted({datetime.fromtimestamp(int(value), tz=UTC).date().isoformat() for value in m1.available_time[q1_mask]})
    by_day: dict[str, list[str]] = defaultdict(list)
    for candidate in candidates:
        by_day[datetime.fromtimestamp(candidate.sweep_at, tz=UTC).date().isoformat()].append(candidate.candidate_id)
    day_rows = [
        {
            "date": day,
            "candidateIds": by_day.get(day, []),
            "manualStatus": "PENDING_REVIEW" if by_day.get(day) else "NO_H4_H1_M30_M15_SWEEP_EPISODE",
        }
        for day in trading_days
    ]
    if render_daily:
        for index, row in enumerate(day_rows, start=1):
            selected = [candidate for candidate in candidates if candidate.candidate_id in row["candidateIds"]]
            row["chart"] = render_daily_overview(engine, row["date"], selected, zone_by_id)
            if index % 10 == 0:
                print(f"DAILY_RENDERED={index}/{len(day_rows)}", flush=True)
    (OUTPUT / "daily_walkforward_index.json").write_text(json.dumps(day_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = defaultdict(int)
    for candidate in candidates:
        counts[candidate.review_state] += 1
    summary = {
        "schema": "mentor-q1-manual-walkforward-candidate-v1",
        "period": {"from": iso(Q1_FROM), "to": iso(Q1_TO)},
        "candidateRule": "H4/H1/M30/M15 meaningful-liquidity sweeps grouped into 45-minute physical episodes; candidate generation never authorizes a trade.",
        "tradingDays": len(trading_days),
        "physicalSweepEpisodes": len(candidates),
        "states": dict(sorted(counts.items())),
        "renderedCharts": sum(1 for item in candidates if item.chart),
    }
    (OUTPUT / "candidate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true", help="render only candidates with source context and LTF CHoCH zone")
    parser.add_argument(
        "--render-ids",
        default="",
        help="comma-separated candidate ids to render without generating every chart",
    )
    parser.add_argument("--render-daily", action="store_true", help="render every Q1 trading day as a chronological overview")
    args = parser.parse_args()
    m1, _ = load_m1_npz(DATASET, start=WARMUP_FROM, end=Q1_TO)
    engine = MentorScenarioEngine(m1)
    engine.prepare()
    candidates = build_candidates(engine)
    render_ids = {item.strip() for item in args.render_ids.split(",") if item.strip()}
    write_manifest(engine, candidates, args.render, args.render_daily, render_ids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
