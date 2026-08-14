"""Render the blind manual replay trades as review-ready MTF charts.

The renderer does not discover structure. It only visualizes the price levels,
timeframes, and execution events already frozen in the append-only manual
ground-truth ledgers.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import textwrap
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(
    os.environ.get(
        "MENTOR_REPLAY_OUTPUT",
        str(ROOT / "output" / "mentor_january_causal_ground_truth"),
    )
).resolve()
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
ORDER_LEDGER = WORKSPACE / "manual_orders.jsonl"
EXECUTION_LEDGER = WORKSPACE / "execution_ledger.jsonl"
MAP_LEDGER = WORKSPACE / "hourly_map_ledger.jsonl"
BASELINE_ELIGIBILITY = WORKSPACE / "BASELINE_TRADE_ELIGIBILITY.json"
CHART_DIR = WORKSPACE / "final_charts"
UTC = timezone.utc

TF_SECONDS = {
    "H4": 4 * 60 * 60,
    "H1": 60 * 60,
    "M30": 30 * 60,
    "M15": 15 * 60,
    "M5": 5 * 60,
    "M1": 60,
}

BG = "#080c12"
PANEL = "#0b1119"
GRID = "#263241"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
BULL = "#5eead4"
BEAR = "#f87171"
REWARD = "#34d399"
RISK = "#fb7185"
FVG = "#3b82f6"
OB = "#f59e0b"
OB_ORIGIN = "#a78bfa"
SOURCE = "#22d3ee"
STRUCTURE = "#cbd5e1"


def parse_time(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.astimezone(UTC).timestamp())


def iso_short(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%d %H:%M UTC")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_rates() -> np.ndarray:
    with np.load(DATASET, allow_pickle=False) as payload:
        return payload["rates"]


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


def build_series(rates: np.ndarray) -> dict[str, np.ndarray]:
    return {timeframe: aggregate(rates, seconds) for timeframe, seconds in TF_SECONDS.items()}


def select_window(
    values: np.ndarray,
    start: int,
    end: int,
    before_bars: int,
    after_bars: int,
    available_through: int | None = None,
) -> tuple[np.ndarray, int]:
    if available_through is not None:
        values = values[values["available"] <= available_through]
    left_anchor = int(np.searchsorted(values["time"], start, side="left"))
    right_anchor = int(np.searchsorted(values["time"], end, side="right"))
    left = max(0, left_anchor - before_bars)
    right = min(len(values), right_anchor + after_bars)
    return values[left:right], left


def x_for_time(bars: np.ndarray, timestamp: int) -> float:
    if not len(bars):
        return 0.0
    index = int(np.searchsorted(bars["time"], timestamp, side="right") - 1)
    return float(np.clip(index, 0, len(bars) - 1))


def draw_candles(axis: Any, bars: np.ndarray) -> None:
    for x, bar in enumerate(bars):
        colour = BULL if bar["close"] >= bar["open"] else BEAR
        axis.vlines(x, bar["low"], bar["high"], color=colour, linewidth=0.58, zorder=4)
        bottom = min(float(bar["open"]), float(bar["close"]))
        height = max(abs(float(bar["close"]) - float(bar["open"])), 1e-6)
        axis.add_patch(
            Rectangle(
                (x - 0.34, bottom),
                0.68,
                height,
                facecolor=colour,
                edgecolor=colour,
                linewidth=0.25,
                zorder=5,
            )
        )
    if len(bars):
        ticks = np.unique(np.linspace(0, len(bars) - 1, min(7, len(bars)), dtype=int))
        labels = [datetime.fromtimestamp(int(bars[index]["time"]), tz=UTC).strftime("%m-%d\n%H:%M") for index in ticks]
        axis.set_xticks(ticks, labels)
    axis.set_facecolor(PANEL)
    axis.grid(color=GRID, linewidth=0.45, alpha=0.32)
    axis.tick_params(colors=MUTED, labelsize=7)
    axis.yaxis.tick_right()
    for spine in axis.spines.values():
        spine.set_color(GRID)


def label_for_zone(zone: dict[str, Any], prefix: str) -> tuple[str, str]:
    zone_type = str(zone.get("type") or "").upper()
    label = str(zone.get("label") or "").upper()
    if zone_type == "FVG" or "FVG" in label and "OB" not in zone_type:
        return f"{prefix} FVG", FVG
    if zone_type == "OB_FVG_ORIGIN":
        return f"{prefix} OB ORIGIN", OB_ORIGIN
    if "OB" in zone_type or "OB" in label or "ORDER BLOCK" in label:
        return f"{prefix} OB", OB
    return f"{prefix} ZONE", SOURCE


def zone_timeframe(zone: dict[str, Any], fallback: str) -> str:
    return str(zone.get("timeframe") or fallback)


def zone_origin_time(bars: np.ndarray, zone: dict[str, Any], fallback: int) -> int:
    """Locate the visible origin candle without inventing a structure detector."""
    if not len(bars):
        return fallback
    formed_at = parse_time(str(zone.get("formedAt"))) if zone.get("formedAt") else fallback
    zone_type = str(zone.get("type") or "").upper()
    low = float(zone["low"])
    high = float(zone["high"])
    tolerance = max((high - low) * 0.03, 0.03)
    eligible = np.flatnonzero(
        (bars["time"] <= formed_at)
        & (bars["low"] <= low + tolerance)
        & (bars["high"] >= high - tolerance)
    )
    if "OB" in zone_type and len(eligible):
        return int(bars[int(eligible[-1])]["time"])
    if zone_type == "FVG":
        timeframe = zone_timeframe(zone, "M1")
        return formed_at - (3 * TF_SECONDS.get(timeframe, 60))
    return formed_at


def last_overlap_index(bars: np.ndarray, zone: dict[str, Any], cutoff: int) -> int:
    eligible = np.flatnonzero(
        (bars["time"] <= cutoff)
        & (bars["high"] >= float(zone["low"]))
        & (bars["low"] <= float(zone["high"]))
    )
    return int(eligible[-1]) if len(eligible) else max(0, len(bars) - 8)


def draw_zone(
    axis: Any,
    bars: np.ndarray,
    zone: dict[str, Any],
    prefix: str,
    start_at: int,
    end_at: int,
    show_label: bool = True,
) -> None:
    if not len(bars):
        return
    label, colour = label_for_zone(zone, prefix)
    x0 = x_for_time(bars, start_at)
    x1 = max(x0 + 1.0, x_for_time(bars, end_at))
    low = float(zone["low"])
    high = float(zone["high"])
    axis.add_patch(
        Rectangle(
            (x0, low),
            x1 - x0,
            max(high - low, 1e-6),
            facecolor=colour,
            edgecolor=colour,
            linewidth=0.9,
            alpha=0.16,
            zorder=2,
        )
    )
    if not show_label:
        return
    upper_prefix = prefix.upper()
    if upper_prefix.startswith(("HTF", "PARENT")):
        text_x = x0 + (x1 - x0) * 0.30
        text_y = high
        vertical_alignment = "bottom"
    elif upper_prefix.startswith("SELECTED"):
        text_x = x0 + (x1 - x0) * 0.70
        text_y = high
        vertical_alignment = "top"
    elif upper_prefix.startswith("ENTRY") or "ENTRY" in upper_prefix:
        text_x = x0 + (x1 - x0) * 0.35
        text_y = high
        vertical_alignment = "bottom"
    else:
        text_x = (x0 + x1) / 2.0
        text_y = (low + high) / 2.0
        vertical_alignment = "center"
    axis.text(
        text_x,
        text_y,
        label,
        color=TEXT,
        fontsize=6.4,
        ha="center",
        va=vertical_alignment,
        fontweight="bold",
        bbox={"facecolor": BG, "edgecolor": "none", "alpha": 0.64, "pad": 1.2},
        zorder=7,
    )


def draw_panel_note(axis: Any, text_value: str, colour: str = TEXT) -> None:
    axis.text(
        0.012,
        0.965,
        text_value,
        transform=axis.transAxes,
        color=colour,
        fontsize=6.4,
        ha="left",
        va="top",
        fontweight="bold",
        bbox={"facecolor": BG, "edgecolor": GRID, "alpha": 0.88, "pad": 3.2},
        zorder=10,
    )


def draw_liquidity_context(
    axis: Any,
    bars: np.ndarray,
    liquidity: dict[str, Any] | str | None,
    decision_at: int,
) -> None:
    # Manual replay orders keep the liquidity thesis as prose and record the
    # executable price separately in the sweep object. Only structured ledger
    # liquidity can be drawn as a price line here.
    if not isinstance(liquidity, dict) or not len(bars) or liquidity.get("price") is None:
        return
    price = float(liquidity["price"])
    formed_at = parse_time(str(liquidity.get("formedAt"))) if liquidity.get("formedAt") else decision_at
    x0 = max(0.0, x_for_time(bars, formed_at) - 2.0)
    x1 = x_for_time(bars, decision_at)
    kind = str(liquidity.get("kind") or "LIQUIDITY").replace("_", " ")
    axis.hlines(price, x0, x1, color="#fbbf24", linewidth=0.8, linestyles=(0, (5, 4)), alpha=0.85, zorder=3)
    axis.text(
        x0 + (x1 - x0) * 0.40,
        price,
        kind,
        color="#fbbf24",
        fontsize=6.1,
        ha="center",
        va="bottom",
        fontweight="bold",
        bbox={"facecolor": BG, "edgecolor": "none", "alpha": 0.64, "pad": 1.0},
        zorder=8,
    )


def draw_context_declaration(
    axis: Any,
    bars: np.ndarray,
    declaration: dict[str, Any] | None,
    decision_at: int,
) -> None:
    if not declaration or not len(bars):
        return
    source = declaration.get("sourceBoundary")
    boundary_text = f" | SOURCE H1 RANGE EDGE {float(source):.2f}" if source is not None else ""
    axis.text(
        0.012,
        0.965,
        f"NO PRE-EXISTING HTF OB/FVG | PRICE-DISCOVERY RANGE CONTEXT{boundary_text}",
        transform=axis.transAxes,
        color="#fbbf24",
        fontsize=7.2,
        ha="left",
        va="top",
        fontweight="bold",
        bbox={"facecolor": BG, "edgecolor": "#92400e", "alpha": 0.9, "pad": 3.5},
        zorder=10,
    )


def nearest_sweep_index(bars: np.ndarray, direction: str, extreme: float, decision_at: int) -> int:
    eligible = np.flatnonzero(bars["time"] <= decision_at)
    if not len(eligible):
        return 0
    recent = eligible[-min(240, len(eligible)) :]
    values = bars["low"][recent] if direction == "long" else bars["high"][recent]
    return int(recent[int(np.argmin(np.abs(values - extreme)))])


def choch_index(bars: np.ndarray, direction: str, level: float, decision_at: int) -> int:
    eligible = np.flatnonzero(bars["time"] <= decision_at)
    if len(eligible) < 2:
        return int(eligible[-1]) if len(eligible) else 0
    crossings: list[int] = []
    for index in eligible[1:]:
        previous = float(bars[index - 1]["close"])
        current = float(bars[index]["close"])
        crossed = previous <= level < current if direction == "long" else previous >= level > current
        if crossed:
            crossings.append(int(index))
    return crossings[-1] if crossings else int(eligible[-1])


def draw_trigger_structure(axis: Any, bars: np.ndarray, order: dict[str, Any], decision_at: int, fill_at: int) -> None:
    if not len(bars):
        return
    direction = order["direction"]
    sweep_extreme = float(order["sweep"]["extreme"])
    sweep_x = nearest_sweep_index(bars, direction, sweep_extreme, decision_at)
    visible_span = max(float(np.max(bars["high"]) - np.min(bars["low"])), 0.01)
    offset = visible_span * 0.026
    sweep_text = "SS" if direction == "long" else "BS"
    sweep_y = sweep_extreme - offset if direction == "long" else sweep_extreme + offset
    axis.scatter(
        [sweep_x],
        [sweep_extreme],
        s=18,
        facecolors="none",
        edgecolors="#fbbf24",
        linewidths=0.9,
        zorder=8,
    )
    axis.text(
        sweep_x,
        sweep_y,
        sweep_text,
        color="#fbbf24",
        fontsize=7,
        ha="center",
        va="top" if direction == "long" else "bottom",
        fontweight="bold",
        zorder=8,
    )

    level = float(order["choch"]["level"])
    structure_x = choch_index(bars, direction, level, decision_at)
    line_start = max(0, structure_x - 12)
    line_end = min(len(bars) - 1, max(structure_x + 8, int(x_for_time(bars, fill_at))))
    axis.hlines(level, line_start, line_end, color=STRUCTURE, linewidth=0.85, linestyles=(0, (4, 4)), zorder=3)
    axis.text(
        line_start + (line_end - line_start) * 0.23,
        level + (offset * 0.45 if direction == "long" else -offset * 0.45),
        "CHoCH",
        color=STRUCTURE,
        fontsize=7,
        ha="center",
        va="bottom" if direction == "long" else "top",
        fontweight="bold",
        zorder=8,
    )


def draw_dealing_range(axis: Any, bars: np.ndarray, map_row: dict[str, Any] | None, decision_at: int) -> None:
    if not map_row or not len(bars):
        return
    low = map_row.get("dealingRangeLow")
    high = map_row.get("dealingRangeHigh")
    if low is None or high is None or float(high) <= float(low):
        return
    x1 = x_for_time(bars, decision_at)
    x0 = max(0.0, x1 - min(80.0, float(len(bars) - 1)))
    midpoint = (float(low) + float(high)) / 2.0
    for level, label, colour in (
        (float(high), "RANGE HIGH", "#f59e0b"),
        (midpoint, "EQ", "#94a3b8"),
        (float(low), "RANGE LOW", "#22d3ee"),
    ):
        axis.hlines(level, x0, x1, color=colour, linewidth=0.65, linestyles=(0, (5, 5)), alpha=0.75, zorder=1)
        axis.text(x1, level, f" {label}", color=colour, fontsize=6.5, ha="left", va="center", zorder=8)


def draw_position_box(
    axis: Any,
    bars: np.ndarray,
    order: dict[str, Any],
    fill_at: int,
    close_at: int,
) -> None:
    if not len(bars):
        return
    x0 = x_for_time(bars, fill_at)
    x1 = max(x0 + 0.8, x_for_time(bars, close_at))
    entry = float(order["entry"])
    stop = float(order["stopLoss"])
    target = float(order["takeProfit"])
    reward_low, reward_high = sorted((entry, target))
    risk_low, risk_high = sorted((entry, stop))
    axis.add_patch(
        Rectangle(
            (x0, reward_low),
            x1 - x0,
            reward_high - reward_low,
            facecolor=REWARD,
            edgecolor=REWARD,
            linewidth=0.75,
            alpha=0.18,
            zorder=2,
        )
    )
    axis.add_patch(
        Rectangle(
            (x0, risk_low),
            x1 - x0,
            risk_high - risk_low,
            facecolor=RISK,
            edgecolor=RISK,
            linewidth=0.75,
            alpha=0.18,
            zorder=2,
        )
    )


def ensure_limits(axis: Any, bars: np.ndarray, extra: tuple[float, ...] = ()) -> None:
    if not len(bars):
        return
    low = min([float(np.min(bars["low"])), *extra]) if extra else float(np.min(bars["low"]))
    high = max([float(np.max(bars["high"])), *extra]) if extra else float(np.max(bars["high"]))
    margin = max((high - low) * 0.055, 0.25)
    axis.set_ylim(low - margin, high + margin)


def adaptive_outcome_timeframe(holding_minutes: int) -> str:
    if holding_minutes <= 6 * 60:
        return "M1"
    if holding_minutes <= 24 * 60:
        return "M5"
    if holding_minutes <= 3 * 24 * 60:
        return "M15"
    if holding_minutes <= 10 * 24 * 60:
        return "M30"
    return "H1"


def map_row_for(maps: list[dict[str, Any]], decision_at: int) -> dict[str, Any] | None:
    eligible = [row for row in maps if parse_time(row["asOf"]) <= decision_at]
    return eligible[-1] if eligible else None


def holding_text(minutes: int) -> str:
    days, remaining = divmod(minutes, 24 * 60)
    hours, mins = divmod(remaining, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    return " ".join(parts)


def render_trade(
    order: dict[str, Any],
    fill_event: dict[str, Any],
    close_event: dict[str, Any],
    map_row: dict[str, Any] | None,
    series: dict[str, np.ndarray],
) -> tuple[Path, dict[str, Any]]:
    decision_at = parse_time(order["decisionAt"])
    fill_at = parse_time(fill_event["at"])
    close_at = parse_time(close_event["at"])
    holding_minutes = max(0, (close_at - fill_at) // 60)
    risk_distance = abs(float(order["entry"]) - float(order["stopLoss"]))
    reward_distance = abs(float(order["takeProfit"]) - float(order["entry"]))
    planned_r = reward_distance / risk_distance if risk_distance else 0.0
    pnl_r = planned_r if close_event["result"] == "TP" else -1.0
    outcome_tf = adaptive_outcome_timeframe(holding_minutes)
    lineage = order.get("causalLineage") or {}
    parent_zone = lineage.get("parentZone") or order["sourceZone"]
    refinements = list(lineage.get("refinementPath") or [])
    context_declaration = lineage.get("contextDeclaration")
    source_liquidity = lineage.get("sourceLiquidity") or order.get("sourceLiquidity")
    parent_tf = zone_timeframe(parent_zone, order["sourceTimeframe"])

    panel_specs = [
        ("MAP + HTF CAUSE", order["mapTimeframe"], decision_at, decision_at, 96, 0, decision_at),
        ("SOURCE + REFINEMENT", order["sourceTimeframe"], decision_at, decision_at, 90, 0, decision_at),
        ("LTF TRIGGER", order["triggerTimeframe"], decision_at, decision_at, 130, 0, decision_at),
        ("OUTCOME", outcome_tf, fill_at, close_at, 30, 20, close_at + TF_SECONDS[outcome_tf]),
    ]
    fig, axes = plt.subplots(4, 1, figsize=(14, 14), constrained_layout=False)
    fig.subplots_adjust(left=0.045, right=0.965, top=0.925, bottom=0.105, hspace=0.34)

    for axis, (role, timeframe, start, end, before, after, cutoff) in zip(axes, panel_specs):
        bars, _ = select_window(series[timeframe], start, end, before, after, available_through=cutoff)
        draw_candles(axis, bars)
        if role == "MAP + HTF CAUSE":
            draw_dealing_range(axis, bars, map_row, decision_at)
            if not context_declaration:
                parent_start = zone_origin_time(bars, parent_zone, decision_at)
                draw_zone(axis, bars, parent_zone, f"HTF {parent_tf}", parent_start, decision_at)
            draw_context_declaration(axis, bars, context_declaration, decision_at)
            map_levels = [float(parent_zone["low"]), float(parent_zone["high"])] if not context_declaration else []
            ensure_limits(axis, bars, tuple(map_levels))
        elif role == "SOURCE + REFINEMENT":
            zone_levels: list[float] = []
            source_note_parts: list[str] = []
            if not context_declaration and parent_tf != timeframe:
                parent_start = zone_origin_time(bars, parent_zone, decision_at)
                draw_zone(axis, bars, parent_zone, f"PARENT {parent_tf}", parent_start, decision_at, show_label=False)
                zone_levels.extend((float(parent_zone["low"]), float(parent_zone["high"])))
                source_note_parts.append(f"PARENT {zone_description(parent_zone, parent_tf)}")
            for refinement in refinements:
                refinement_tf = zone_timeframe(refinement, timeframe)
                refinement_start = zone_origin_time(bars, refinement, decision_at)
                draw_zone(axis, bars, refinement, f"CHILD {refinement_tf}", refinement_start, decision_at, show_label=False)
                zone_levels.extend((float(refinement["low"]), float(refinement["high"])))
                source_note_parts.append(f"CHILD {zone_description(refinement, refinement_tf)}")
            source_start = zone_origin_time(bars, order["sourceZone"], decision_at)
            draw_zone(axis, bars, order["sourceZone"], f"SELECTED {timeframe}", source_start, decision_at, show_label=False)
            draw_liquidity_context(axis, bars, source_liquidity, decision_at)
            zone_levels.extend((float(order["sourceZone"]["low"]), float(order["sourceZone"]["high"])))
            if not source_note_parts:
                source_note_parts.append("DIRECT PARENT/SOURCE")
            source_note_parts.append(f"SELECTED {zone_description(order['sourceZone'], timeframe)}")
            draw_panel_note(axis, textwrap.shorten(" > ".join(source_note_parts), width=180, placeholder="..."))
            ensure_limits(axis, bars, tuple(zone_levels))
        elif role == "LTF TRIGGER":
            structure_time = zone_origin_time(bars, order["entryZone"], decision_at)
            draw_zone(axis, bars, order["entryZone"], "ENTRY", structure_time, decision_at, show_label=False)
            draw_trigger_structure(axis, bars, order, decision_at, fill_at)
            draw_panel_note(axis, f"ENTRY {zone_description(order['entryZone'], timeframe)}")
            ensure_limits(
                axis,
                bars,
                (
                    float(order["entryZone"]["low"]),
                    float(order["entryZone"]["high"]),
                    float(order["sweep"]["extreme"]),
                    float(order["choch"]["level"]),
                ),
            )
        else:
            draw_position_box(axis, bars, order, fill_at, close_at)
            ensure_limits(axis, bars, (float(order["entry"]), float(order["stopLoss"]), float(order["takeProfit"])))
        axis.set_title(
            f"{role}  |  {timeframe}  |  {len(bars)} as-of closed bars",
            loc="left",
            color=TEXT,
            fontsize=9.5,
            fontweight="bold",
        )

    result = close_event["result"]
    result_colour = REWARD if result == "TP" else RISK
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"{order['orderId']}  {order['direction'].upper()}  {result}  {pnl_r:+.2f}R  |  HOLD {holding_text(holding_minutes)}",
        color=result_colour,
        fontsize=15,
        fontweight="bold",
        y=0.977,
    )
    fig.text(
        0.5,
        0.945,
        f"{order['scope']}  |  {order['mapTimeframe']} map > {parent_tf} parent > {order['sourceTimeframe']} source > {order['triggerTimeframe']} trigger  |  filled {iso_short(fill_at)}",
        color=MUTED,
        fontsize=8.5,
        ha="center",
    )
    map_text = textwrap.shorten(str(order["map"]), width=180, placeholder="...")
    objective_text = textwrap.shorten(str(order["objective"]), width=180, placeholder="...")
    fig.text(0.05, 0.057, f"MAP: {map_text}", color=TEXT, fontsize=8.2, ha="left")
    fig.text(0.05, 0.035, f"OBJECTIVE: {objective_text}", color=MUTED, fontsize=8.2, ha="left")
    fig.text(
        0.95,
        0.035,
        "Position values are shown only by the translucent reward/risk box.",
        color=MUTED,
        fontsize=7.5,
        ha="right",
    )

    CHART_DIR.mkdir(parents=True, exist_ok=True)
    destination = CHART_DIR / f"{order['orderId']}_{order['direction']}_{result}.png"
    fig.savefig(destination, dpi=135, facecolor=BG, bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)
    row = {
        "order_id": order["orderId"],
        "decision_at": order["decisionAt"],
        "filled_at": fill_event["at"],
        "closed_at": close_event["at"],
        "direction": order["direction"],
        "result": result,
        "pnl_r": round(pnl_r, 6),
        "planned_r": round(planned_r, 6),
        "holding_minutes": holding_minutes,
        "scope": order["scope"],
        "map_timeframe": order["mapTimeframe"],
        "parent_timeframe": parent_tf,
        "parent_zone_type": parent_zone.get("type", ""),
        "source_timeframe": order["sourceTimeframe"],
        "source_zone_type": order["sourceZone"].get("type", ""),
        "trigger_timeframe": order["triggerTimeframe"],
        "context_type": context_declaration.get("type", "") if context_declaration else "HTF_CAUSAL_ZONE",
        "refinement_count": len(refinements),
        "causal_protocol": lineage.get("protocol", ""),
        "chart": destination.name,
    }
    return destination, row


def zone_description(zone: dict[str, Any], fallback_timeframe: str) -> str:
    timeframe = zone_timeframe(zone, fallback_timeframe)
    zone_type = str(zone.get("type") or "ZONE").replace("_", " ")
    return f"{timeframe} {zone_type} {float(zone['low']):.2f}-{float(zone['high']):.2f}"


def causal_description(order: dict[str, Any]) -> tuple[str, str]:
    lineage = order.get("causalLineage") or {}
    declaration = lineage.get("contextDeclaration")
    parent = lineage.get("parentZone") or order["sourceZone"]
    refinements = list(lineage.get("refinementPath") or [])
    if declaration and declaration.get("type") == "PREDECLARED_H1_RANGE_EDGE":
        cause = (
            f"H1 range edge {float(declaration['sourceBoundary']):.2f}; "
            "pre-existing HTF OB/FVG 없음. Sweep 이후 생성된 M5 source를 사용."
        )
    else:
        cause = zone_description(parent, order["sourceTimeframe"])
    chain_parts = [zone_description(parent, order["sourceTimeframe"])]
    chain_parts.extend(zone_description(item, order["sourceTimeframe"]) for item in refinements)
    selected = zone_description(order["sourceZone"], order["sourceTimeframe"])
    if selected != chain_parts[-1]:
        chain_parts.append(selected)
    return cause, " > ".join(chain_parts)


def review_statistics(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    pnls = [float(row["pnl_r"]) for row in rows]
    wins = [value for value in pnls if value > 0]
    losses = [value for value in pnls if value < 0]
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    consecutive_losses = 0
    max_consecutive_losses = 0
    for value in pnls:
        equity += value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
        if value < 0:
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        else:
            consecutive_losses = 0
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    return {
        "trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": (len(wins) / len(rows) * 100.0) if rows else 0.0,
        "total_r": sum(pnls),
        "expectancy_r": (sum(pnls) / len(rows)) if rows else 0.0,
        "profit_factor": (gross_profit / gross_loss) if gross_loss else float("inf"),
        "max_drawdown_r": max_drawdown,
        "max_consecutive_losses": max_consecutive_losses,
    }


def write_review_files(
    rows: list[dict[str, Any]],
    orders: dict[str, dict[str, Any]],
    excluded_order_ids: list[str],
) -> None:
    for filename in ("trades.csv", "trade_review.csv"):
        csv_path = WORKSPACE / filename
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    stats = review_statistics(rows)
    decision_dates = sorted(parse_time(row["decision_at"]) for row in rows)
    period_start = datetime.fromtimestamp(decision_dates[0], tz=UTC).strftime("%Y-%m-%d")
    period_end = datetime.fromtimestamp(decision_dates[-1], tz=UTC).strftime("%Y-%m-%d")
    period_label = period_start if period_start == period_end else f"{period_start} ~ {period_end}"
    report_title = f"Mentor Blind Manual Trade Review | {period_label}"
    markdown = [
        f"# {report_title}",
        "",
        "포지션 가격은 OUTCOME 차트의 반투명 위험/보상 박스로만 표시한다. MAP, parent, refinement, source, trigger 구조는 주문 전에 동결된 수동 원장만 사용한다.",
        "",
        f"- 체결·종료 거래: **{stats['trades']}건**",
        f"- 승률: **{stats['win_rate']:.2f}%** ({stats['wins']}승 / {stats['losses']}패)",
        f"- 합계: **{stats['total_r']:+.2f}R** | PF **{stats['profit_factor']:.2f}** | 기대값 **{stats['expectancy_r']:+.2f}R**",
        f"- 최대 낙폭: **{stats['max_drawdown_r']:.2f}R** | 최대 연속 손실: **{stats['max_consecutive_losses']}회**",
        *(
            [f"- 프로토콜 제외: **{', '.join(excluded_order_ids)}** (sweep 이후 별도 CHoCH 미충족)"]
            if excluded_order_ids
            else []
        ),
        "",
    ]
    for row in rows:
        order = orders[row["order_id"]]
        cause, chain = causal_description(order)
        source_liquidity = (order.get("causalLineage") or {}).get("sourceLiquidity") or order.get("sourceLiquidity")
        markdown.extend(
            [
                f"## {row['order_id']} | {row['direction'].upper()} | {row['result']} | {row['pnl_r']:+.2f}R",
                "",
                f"- 계약: `{row['map_timeframe']} map > {row['parent_timeframe']} parent > {row['source_timeframe']} source > {row['trigger_timeframe']} trigger`",
                f"- 범위: `{row['scope']}`",
                f"- HTF 원인: {cause}",
                f"- refinement: {chain}",
                f"- 유동성: {source_liquidity}",
                f"- 목적지: {order['objective']}",
                f"- 보유: {holding_text(int(row['holding_minutes']))} | 계획 손익비 {float(row['planned_r']):.2f}R",
                f"- Chart: [open](final_charts/{row['chart']})",
                "",
                f"![{row['order_id']}](final_charts/{row['chart']})",
                "",
            ]
        )
    (WORKSPACE / "TRADE_REVIEW.md").write_text("\n".join(markdown), encoding="utf-8")

    cards: list[str] = []
    for row in rows:
        order = orders[row["order_id"]]
        cause, chain = causal_description(order)
        source_liquidity = (order.get("causalLineage") or {}).get("sourceLiquidity") or order.get("sourceLiquidity")
        no_htf_zone = row["context_type"] == "PREDECLARED_H1_RANGE_EDGE"
        badge = '<span class="range-context">HTF ZONE 없음</span>' if no_htf_zone else '<span class="causal-zone">HTF CAUSAL ZONE</span>'
        cards.append(
            f"""
            <article class="trade" data-result="{row['result']}" data-scope="{row['scope']}" data-trigger="{row['trigger_timeframe']}">
              <header><strong>{row['order_id']} {row['direction'].upper()}</strong><span class="{row['result'].lower()}">{row['result']} {row['pnl_r']:+.2f}R</span></header>
              <div class="badges">{badge}<span>{html.escape(row['scope'])}</span></div>
              <dl>
                <dt>계약</dt><dd>{html.escape(row['map_timeframe'])} map &gt; {html.escape(row['parent_timeframe'])} parent &gt; {html.escape(row['source_timeframe'])} source &gt; {html.escape(row['trigger_timeframe'])} trigger</dd>
                <dt>HTF 원인</dt><dd>{html.escape(cause)}</dd>
                <dt>Refinement</dt><dd>{html.escape(chain)}</dd>
                <dt>유동성</dt><dd>{html.escape(str(source_liquidity))}</dd>
                <dt>목적지</dt><dd>{html.escape(str(order['objective']))}</dd>
                <dt>결과</dt><dd>계획 {float(row['planned_r']):.2f}R | 보유 {holding_text(int(row['holding_minutes']))}</dd>
              </dl>
              <a href="final_charts/{row['chart']}" target="_blank"><img loading="lazy" src="final_charts/{row['chart']}" alt="{row['order_id']} chart"></a>
            </article>
            """
        )
    document = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(report_title)}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#080c12;color:#e2e8f0;font:14px Arial,sans-serif}} .shell{{max-width:1500px;margin:auto;padding:20px}}
h1{{font-size:22px;margin:0 0 6px}} .intro{{color:#94a3b8;margin:0 0 14px}} .summary{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;margin:14px 0}} .metric{{background:#0b1119;border:1px solid #263241;padding:10px}} .metric small{{display:block;color:#94a3b8;margin-bottom:4px}} .metric strong{{font-size:17px}}
.filters{{position:sticky;top:0;z-index:4;background:#080c12;padding:10px 0;display:flex;gap:8px;flex-wrap:wrap}}
button{{border:1px solid #334155;background:#111827;color:#cbd5e1;padding:8px 12px;border-radius:5px;cursor:pointer}} button.active{{border-color:#34d399;color:#34d399}}
.trade{{border-top:1px solid #263241;padding:22px 0}} header{{display:flex;justify-content:space-between;font-size:17px}} .tp{{color:#34d399}} .sl{{color:#fb7185}}
p{{color:#94a3b8;margin:7px 0}} .badges{{display:flex;gap:6px;margin:10px 0}} .badges span{{font-size:11px;border:1px solid #334155;color:#94a3b8;padding:4px 6px}} .badges .causal-zone{{border-color:#3b82f6;color:#60a5fa}} .badges .range-context{{border-color:#f59e0b;color:#fbbf24}}
dl{{display:grid;grid-template-columns:90px 1fr;gap:6px 12px;margin:12px 0;color:#cbd5e1}} dt{{color:#64748b}} dd{{margin:0}} img{{display:block;width:100%;height:auto;border:1px solid #263241;background:#0b1119;margin-top:12px}}
.hidden{{display:none}} @media(max-width:700px){{.shell{{padding:12px}} h1{{font-size:18px}} header{{font-size:15px}} .summary{{grid-template-columns:repeat(2,minmax(0,1fr))}} dl{{grid-template-columns:72px 1fr;font-size:12px}}}}
</style></head><body><main class="shell"><h1>{html.escape(report_title)}</h1>
<p class="intro">주문 전에 동결된 구조만 표시합니다. 포지션 가격은 OUTCOME 패널의 반투명 위험/보상 박스로만 표현됩니다.</p>
{f'<p class="intro">프로토콜 제외: {html.escape(", ".join(excluded_order_ids))} (sweep 이후 별도 CHoCH 미충족)</p>' if excluded_order_ids else ''}
<section class="summary">
  <div class="metric"><small>거래</small><strong>{stats['trades']}</strong></div>
  <div class="metric"><small>승률</small><strong>{stats['win_rate']:.2f}%</strong></div>
  <div class="metric"><small>합계</small><strong>{stats['total_r']:+.2f}R</strong></div>
  <div class="metric"><small>PF</small><strong>{stats['profit_factor']:.2f}</strong></div>
  <div class="metric"><small>기대값</small><strong>{stats['expectancy_r']:+.2f}R</strong></div>
  <div class="metric"><small>최대 낙폭</small><strong>{stats['max_drawdown_r']:.2f}R</strong></div>
</section>
<nav class="filters"><button class="active" data-filter="ALL">ALL ({len(rows)})</button><button data-filter="TP">TP</button><button data-filter="SL">SL</button><button data-filter="EXTERNAL_CONTINUATION">CONTINUATION</button><button data-filter="M1">M1 TRIGGER</button><button data-filter="M5">M5 TRIGGER</button></nav>
{''.join(cards)}</main><script>
const buttons=[...document.querySelectorAll('button')], trades=[...document.querySelectorAll('.trade')];
buttons.forEach(button=>button.addEventListener('click',()=>{{buttons.forEach(x=>x.classList.remove('active'));button.classList.add('active');const f=button.dataset.filter;trades.forEach(t=>t.classList.toggle('hidden',!(f==='ALL'||t.dataset.result===f||t.dataset.scope===f||t.dataset.trigger===f)));}}));
</script></body></html>"""
    (WORKSPACE / "TRADE_REVIEW.html").write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", default="2025-01-01T00:00:00+00:00")
    parser.add_argument("--to", dest="date_to", default="2025-02-01T00:00:00+00:00")
    args = parser.parse_args()
    date_from = parse_time(args.date_from)
    date_to = parse_time(args.date_to)

    orders = {
        row["orderId"]: row
        for row in read_jsonl(ORDER_LEDGER)
        if date_from <= parse_time(row["decisionAt"]) < date_to
    }
    excluded_order_ids: list[str] = []
    if BASELINE_ELIGIBILITY.exists():
        eligibility = json.loads(BASELINE_ELIGIBILITY.read_text(encoding="utf-8"))
        classifications = {
            item["orderId"]: item
            for item in eligibility.get("orders", [])
            if item.get("orderId")
        }
        excluded_order_ids = sorted(
            order_id
            for order_id, item in classifications.items()
            if item.get("baselineEligible") is False and order_id in orders
        )
        orders = {
            order_id: order
            for order_id, order in orders.items()
            if classifications.get(order_id, {}).get("baselineEligible") is not False
        }
    events = read_jsonl(EXECUTION_LEDGER)
    maps = read_jsonl(MAP_LEDGER)
    filled = {
        row["orderId"]: row
        for row in events
        if row.get("event") in {"ORDER_FILLED", "ORDER_FILLED_AND_CLOSED"}
        and row.get("orderId") in orders
    }
    closed = {
        row["orderId"]: row
        for row in events
        if row.get("event") in {"POSITION_CLOSED", "ORDER_FILLED_AND_CLOSED"}
        and row.get("orderId") in orders
    }
    trade_ids = sorted(set(filled) & set(closed))
    if not trade_ids:
        raise SystemExit("No closed manual trades found in the requested decision period.")

    rates = load_rates()
    series = build_series(rates)
    rows: list[dict[str, Any]] = []
    for number, order_id in enumerate(trade_ids, start=1):
        order = orders[order_id]
        decision_at = parse_time(order["decisionAt"])
        _, row = render_trade(order, filled[order_id], closed[order_id], map_row_for(maps, decision_at), series)
        rows.append(row)
        print(f"[{number:02d}/{len(trade_ids):02d}] {order_id} {row['result']} {row['pnl_r']:+.2f}R")
    write_review_files(rows, orders, excluded_order_ids)
    print(json.dumps({
        "trades": len(rows),
        "wins": sum(row["result"] == "TP" for row in rows),
        "losses": sum(row["result"] == "SL" for row in rows),
        "totalR": round(sum(float(row["pnl_r"]) for row in rows), 6),
        "excludedOrderIds": excluded_order_ids,
        "chartDirectory": str(CHART_DIR),
        "reviewHtml": str(WORKSPACE / "TRADE_REVIEW.html"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
