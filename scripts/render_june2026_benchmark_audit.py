"""Merge and render formal June benchmark executions for semantic review."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import glob
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

from build_june2026_oracle_atlas import load_joined
from mentor_replay_v4_core import MarketData, parse_utc

UTC = timezone.utc
BG, GRID, TEXT = "#090d14", "#273343", "#e5e7eb"
BULL, BEAR = "#2dd4bf", "#fb7185"


def candles(axis: Any, series: Any, left: int, right: int) -> None:
    for x, index in enumerate(range(left, right)):
        colour = BULL if series.close[index] >= series.open[index] else BEAR
        axis.vlines(x, series.low[index], series.high[index], color=colour, linewidth=0.6, zorder=3)
        bottom = min(series.open[index], series.close[index])
        axis.add_patch(Rectangle((x - .34, bottom), .68, max(abs(series.close[index] - series.open[index]), .001),
                                 facecolor=colour, edgecolor=colour, linewidth=.3, zorder=4))


def xpos(series: Any, left: int, right: int, timestamp: int) -> float:
    return float(np.clip(np.searchsorted(series.available_time, timestamp, side="left") - left, 0, right - left - 1))


def zone(axis: Any, series: Any, left: int, right: int, node: dict[str, Any], start: int, end: int, label: str, colour: str) -> None:
    x0, x1 = xpos(series, left, right, start), xpos(series, left, right, end)
    x1 = max(x0 + 1, x1)
    axis.add_patch(Rectangle((x0, node["low"]), x1 - x0, node["high"] - node["low"],
                             facecolor=colour, edgecolor=colour, alpha=.18, linewidth=1.0, zorder=2))
    axis.text((x0 + x1) / 2, (node["low"] + node["high"]) / 2, label, color=TEXT,
              fontsize=7, ha="center", va="center", zorder=8)


def render(item: dict[str, Any], market: MarketData, output: Path) -> Path:
    scenario, result = item["scenario"], item["result"]
    trade = result.get("trade") or result.get("replacement")
    replacement = result.get("replacement")
    if replacement:
        order = {
            "createdAtUtc": replacement["formedAtUtc"],
            "executionZone": replacement["fvg"],
        }
        trigger = {}
    else:
        order, trigger = result["order"], result["trigger"]
    frozen = parse_utc(scenario["frozenAtUtc"])
    entry = parse_utc(trade.get("entryAtUtc") or trade["filledAtUtc"])
    exit_at = parse_utc(trade.get("exitAtUtc") or trade["closedAtUtc"])
    panels = [("H1", 90), ("M15", 160), ("M5", 220), ("M1", 260)]
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), constrained_layout=True)
    for axis, (tf, maximum) in zip(axes.ravel(), panels):
        series = market.frames[tf]
        center_left = int(np.searchsorted(series.available_time, frozen, side="left"))
        center_right = int(np.searchsorted(series.available_time, exit_at, side="right"))
        left = max(0, center_left - maximum // 3)
        right = min(len(series.time), max(center_right + maximum // 8, left + 30))
        if right - left > maximum:
            right = min(len(series.time), left + maximum)
        candles(axis, series, left, right)
        zone(axis, series, left, right, scenario["root"], parse_utc(scenario["root"]["formedAtUtc"]), exit_at,
             f"ROOT {scenario['root']['tf']}", "#8b5cf6")
        zone(axis, series, left, right, scenario["finalChild"], parse_utc(scenario["finalChild"]["formedAtUtc"]), exit_at,
             f"CHILD {scenario['finalChild']['tf']}", "#3b82f6")
        execution = order["executionZone"]
        zone(axis, series, left, right, execution, parse_utc(order["createdAtUtc"]), entry,
             "EXEC OB", "#f59e0b")
        x0, x1 = xpos(series, left, right, entry), xpos(series, left, right, exit_at)
        x1 = max(x0 + 1, x1)
        risk = sorted((float(trade["entry"]), float(trade["stop"])))
        reward = sorted((float(trade["entry"]), float(trade["target"])))
        axis.add_patch(Rectangle((x0, risk[0]), x1-x0, risk[1]-risk[0], facecolor="#ef4444", edgecolor="none", alpha=.20, zorder=1))
        axis.add_patch(Rectangle((x0, reward[0]), x1-x0, reward[1]-reward[0], facecolor="#22c55e", edgecolor="none", alpha=.20, zorder=1))
        objective_time = int(scenario["objective"]["barId"].split(":", 1)[1])
        ox = xpos(series, left, right, objective_time)
        axis.hlines(float(scenario["objective"]["price"]), ox, max(ox + 1, x1), color="#c084fc", linestyle=(0, (4, 3)), linewidth=1)
        for key, label in [("sweepExcursionBarId", "SWEEP"), ("chochBreakBarId", "CHoCH")]:
            if key not in trigger:
                continue
            event_time = int(trigger[key].split(":", 1)[1]) + 60
            axis.text(xpos(series, left, right, event_time), float(trade["entry"]), label,
                      color="#fde68a", fontsize=7, ha="center", va="bottom", zorder=9)
        axis.set_facecolor(BG); axis.grid(color=GRID, alpha=.3); axis.tick_params(colors="#94a3b8", labelsize=7)
        axis.yaxis.tick_right(); axis.set_title(tf, color=TEXT, loc="left")
    fig.suptitle(
        f"{scenario['direction']} {scenario['scope']} | {result['status']} {float(trade['resultR']):+.2f}R\n"
        f"freeze {scenario['frozenAtUtc']} | entry {trade.get('entryAtUtc') or trade['filledAtUtc']} | "
        f"exit {trade.get('exitAtUtc') or trade['closedAtUtc']} | objective {scenario['objective']['barId']}",
        color=TEXT, fontsize=12,
    )
    fig.patch.set_facecolor(BG)
    entry_text = trade.get("entryAtUtc") or trade["filledAtUtc"]
    path = output / f"{scenario['semanticHash'][:10]}_{entry_text[:10]}_{scenario['objective']['barId'].replace(':','-')}.png"
    fig.savefig(path, dpi=150, facecolor=BG)
    plt.close(fig)
    return path


def main() -> int:
    run = ROOT / "output" / "mentor_june2026_causal_benchmark"
    with (run / "causal_benchmark.jsonl").open(encoding="utf-8") as handle:
        trades = [json.loads(line) for line in handle if line.strip()]
    rates, _ = load_joined(
        ROOT / "output/datasets/GOLD_M1_2023-12-01_2025-12-31.npz",
        ROOT / "output/datasets/GOLD_M1_2026-01-01_2026-08-12.npz",
    )
    market = MarketData.from_rates(rates, .01)
    output = run / "selected_trade_charts"
    output.mkdir(exist_ok=True)
    manifest = []
    for item in trades:
        path = render(item, market, output)
        manifest.append({"semanticHash": item["scenario"]["semanticHash"], "path": str(path), "scenario": item["scenario"], "result": item["result"]})
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"formalTrades": len(trades), "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
