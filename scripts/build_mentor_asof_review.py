from __future__ import annotations

import csv
from datetime import datetime, timezone
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

from mentor_engine.data import load_m1_npz
from mentor_engine.engine import MentorScenarioEngine


RUN_DIR = ROOT / "output" / "mentor_engine" / "GOLD_2025_Q1_FINAL"
OUT_DIR = RUN_DIR / "mentor_asof_review"
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
UTC = timezone.utc
TIMEFRAMES = ("H4", "H1", "M30", "M15", "M5", "M1")
WINDOWS = {"H4": 90, "H1": 110, "M30": 120, "M15": 140, "M5": 160, "M1": 180}

BG = "#080c12"
GRID = "#263241"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
BULL = "#5eead4"
BEAR = "#f87171"
ZONE_COLOURS = {"FVG": "#2563eb", "FVG_ORIGIN_OB": "#d97706", "LAST_OPPOSITE_OB": "#7c3aed"}


def ts(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp())


def candles(axis: Any, series: Any, left: int, right: int) -> None:
    for x, index in enumerate(range(left, right)):
        colour = BULL if series.close[index] >= series.open[index] else BEAR
        axis.vlines(x, series.low[index], series.high[index], color=colour, linewidth=0.58, zorder=4)
        bottom = min(series.open[index], series.close[index])
        height = max(abs(series.close[index] - series.open[index]), 1e-6)
        axis.add_patch(Rectangle((x - 0.34, bottom), 0.68, height, facecolor=colour, edgecolor=colour, linewidth=0.35, zorder=5))
    count = right - left
    axis.set_xlim(-1, count)
    positions = np.unique(np.linspace(0, count - 1, min(6, count), dtype=int))
    labels = [datetime.fromtimestamp(int(series.available_time[left + i]), tz=UTC).strftime("%m-%d\n%H:%M") for i in positions]
    axis.set_xticks(positions, labels)


def projected_x(series: Any, left: int, right: int, value: int) -> float:
    index = int(np.searchsorted(series.available_time, value, side="left"))
    return float(np.clip(index - left, 0, max(1, right - left - 1)))


def active_candidates(engine: MentorScenarioEngine, timeframe: str, at: int, price: float) -> tuple[list[Any], list[Any]]:
    state = engine.states[timeframe]
    active_zones = [zone for zone in state.zones if zone.active_at(at) and zone.available_at <= at]
    active_zones.sort(key=lambda zone: (abs((zone.bottom + zone.top) / 2 - price), -zone.available_at))
    zones: list[Any] = []
    direction_counts = {"long": 0, "short": 0}
    for zone in active_zones:
        side = zone.direction.value
        if direction_counts[side] >= 2:
            continue
        if abs((zone.bottom + zone.top) / 2 - price) / max(price, 1.0) > 0.025:
            continue
        zones.append(zone)
        direction_counts[side] += 1
        if len(zones) >= 4:
            break
    active_pools = [pool for pool in state.liquidity if pool.active_at(at) and pool.available_at <= at]
    above = sorted((p for p in active_pools if p.level >= price), key=lambda p: p.level)[:2]
    below = sorted((p for p in active_pools if p.level < price), key=lambda p: p.level, reverse=True)[:2]
    return zones, above + below


def draw_zone(axis: Any, series: Any, left: int, right: int, zone: Any) -> None:
    panel_start = int(series.available_time[left])
    panel_end = int(series.available_time[right - 1])
    start = max(zone.available_at, panel_start)
    end = min(zone.consumed_at or panel_end, panel_end)
    if end <= start:
        return
    x0 = projected_x(series, left, right, start)
    x1 = max(projected_x(series, left, right, end), x0 + 1)
    colour = ZONE_COLOURS.get(zone.kind.value, "#64748b")
    axis.add_patch(Rectangle((x0, zone.bottom), x1 - x0, zone.top - zone.bottom,
                             facecolor=colour, edgecolor=colour, linewidth=0.8, alpha=0.14, zorder=2))
    axis.text((x0 + x1) / 2, (zone.bottom + zone.top) / 2,
              zone.kind.value.replace("LAST_OPPOSITE_", ""), fontsize=6.2, color=TEXT,
              ha="center", va="center", zorder=7)


def draw_event(axis: Any, series: Any, left: int, right: int, event: Any) -> None:
    try:
        start_time = int(event.broken_swing_id.rsplit(":", 1)[-1])
    except ValueError:
        start_time = event.occurred_at
    panel_start = int(series.available_time[left])
    panel_end = int(series.available_time[right - 1])
    if event.available_at < panel_start or start_time > panel_end:
        return
    x0 = projected_x(series, left, right, max(start_time, panel_start))
    x1 = projected_x(series, left, right, min(event.available_at, panel_end))
    colour = "#34d399" if event.direction.value == "long" else "#fb7185"
    axis.hlines(event.broken_level, x0, max(x1, x0 + 1), color=colour, linewidth=0.85, linestyle=(0, (5, 3)), zorder=6)
    axis.text((x0 + max(x1, x0 + 1)) / 2, event.broken_level, event.event_type.replace("INITIAL_", ""),
              fontsize=6.3, color=colour, ha="center",
              va="bottom" if event.direction.value == "long" else "top", zorder=7)


def packet_for(engine: MentorScenarioEngine, trade: dict[str, str], at: int) -> dict[str, Any]:
    m1 = engine.series["M1"]
    m1_index = int(np.searchsorted(m1.available_time, at, side="right") - 1)
    price = float(m1.close[m1_index])
    result: dict[str, Any] = {
        "trade": {key: trade[key] for key in ("direction", "scope", "map_timeframe", "context_timeframe", "trigger_timeframe", "entry", "stop_loss", "take_profit", "result", "holding_minutes", "source_pool_id", "source_zone_ids", "trigger_event_id", "entry_zone_id", "objective_kind", "objective_id")},
        "asOf": datetime.fromtimestamp(at, tz=UTC).isoformat(),
        "price": price,
        "timeframes": {},
    }
    for timeframe in TIMEFRAMES:
        state = engine.states[timeframe]
        index = int(np.searchsorted(state.series.available_time, at, side="right") - 1)
        zones, pools = active_candidates(engine, timeframe, at, price)
        events = [event for event in state.structure.events if event.available_at <= at][-4:]
        result["timeframes"][timeframe] = {
            "trend": int(state.structure.trend[index]),
            "rangeLow": None if np.isnan(state.structure.range_low[index]) else float(state.structure.range_low[index]),
            "rangeHigh": None if np.isnan(state.structure.range_high[index]) else float(state.structure.range_high[index]),
            "protectedLow": None if np.isnan(state.structure.protected_low[index]) else float(state.structure.protected_low[index]),
            "protectedHigh": None if np.isnan(state.structure.protected_high[index]) else float(state.structure.protected_high[index]),
            "events": [{"type": e.event_type, "direction": e.direction.value, "level": e.broken_level, "at": e.available_at} for e in events],
            "zones": [{"kind": z.kind.value, "direction": z.direction.value, "bottom": z.bottom, "top": z.top, "availableAt": z.available_at} for z in zones],
            "liquidity": [{"kind": p.kind.value, "side": p.side.value, "level": p.level, "availableAt": p.available_at} for p in pools],
        }
    return result


def render_case(engine: MentorScenarioEngine, number: int, packet: dict[str, Any], at: int) -> Path:
    price = packet["price"]
    fig, axes = plt.subplots(3, 2, figsize=(15, 12), constrained_layout=True)
    axes = axes.ravel()
    for axis, timeframe in zip(axes, TIMEFRAMES):
        state = engine.states[timeframe]
        series = state.series
        end = int(np.searchsorted(series.available_time, at, side="right"))
        left = max(0, end - WINDOWS[timeframe])
        right = max(left + 2, end)
        candles(axis, series, left, right)
        zones, pools = active_candidates(engine, timeframe, at, price)
        for zone in zones:
            draw_zone(axis, series, left, right, zone)
        for pool in pools:
            colour = "#c084fc"
            axis.axhline(pool.level, color=colour, linewidth=0.65, linestyle=(0, (4, 3)), alpha=0.8)
            axis.text(0.995, pool.level, "BSL" if pool.side.value == "high" else "SSL",
                      transform=axis.get_yaxis_transform(), color=colour, fontsize=6.2,
                      ha="right", va="bottom" if pool.side.value == "high" else "top")
        events = [event for event in state.structure.events if event.available_at <= at][-4:]
        for event in events:
            draw_event(axis, series, left, right, event)
        trend = packet["timeframes"][timeframe]["trend"]
        trend_text = "UP" if trend > 0 else "DOWN" if trend < 0 else "UNSET"
        axis.set_title(f"{timeframe} · {trend_text}", loc="left", fontsize=10, color=TEXT, fontweight="bold")
        axis.set_facecolor(BG)
        axis.grid(color=GRID, alpha=0.3, linewidth=0.5)
        axis.tick_params(colors=MUTED, labelsize=7)
        axis.yaxis.tick_right()
        for spine in axis.spines.values():
            spine.set_color(GRID)
    fig.patch.set_facecolor(BG)
    fig.suptitle(f"CASE #{number:02d} · AS-OF {datetime.fromtimestamp(at, tz=UTC):%Y-%m-%d %H:%M} UTC · price {price:.2f}",
                 color=TEXT, fontsize=14, fontweight="bold")
    path = OUT_DIR / f"{number:02d}_{datetime.fromtimestamp(at, tz=UTC):%Y-%m-%d_%H%M}_asof.png"
    fig.savefig(path, dpi=145, facecolor=BG, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return path


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trades = [row for row in csv.DictReader((RUN_DIR / "trades.csv").open("r", encoding="utf-8-sig", newline="")) if row["result"] in {"SL", "TP"}]
    start = int(datetime(2024, 10, 1, tzinfo=UTC).timestamp())
    end = int(datetime(2025, 4, 1, tzinfo=UTC).timestamp())
    m1, _ = load_m1_npz(DATASET, start=start, end=end)
    engine = MentorScenarioEngine(m1)
    engine.prepare()
    packets = []
    for number, trade in enumerate(trades, start=1):
        at = ts(trade["order_time_utc"])
        packet = packet_for(engine, trade, at)
        packet["number"] = number
        packet["chart"] = render_case(engine, number, packet, at).name
        packets.append(packet)
    (OUT_DIR / "asof_packets.json").write_text(json.dumps(packets, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"CASES={len(packets)}")
    print(f"OUTPUT={OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
