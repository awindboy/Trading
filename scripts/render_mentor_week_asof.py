"""Render decision-neutral as-of charts for the one-week mentor replay."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz, parse_utc


DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = ROOT / "output" / "mentor_week_2025-01-06_10_manual_ground_truth" / "asof"
UTC = timezone.utc
BG, GRID, TEXT = "#080c12", "#263241", "#e2e8f0"
BULL, BEAR = "#5eead4", "#f87171"


def draw(ax, series, cutoff: int, count: int, title: str) -> None:
    indexes = np.flatnonzero(series.available_time <= cutoff)[-count:]
    if not len(indexes):
        raise SystemExit(f"No closed bars available for {title}")
    if int(series.available_time[indexes[-1]]) > cutoff:
        raise AssertionError("Future bar leaked into as-of chart")
    for x, index in enumerate(indexes):
        o, h, l, c = map(
            float,
            (series.open[index], series.high[index], series.low[index], series.close[index]),
        )
        color = BULL if c >= o else BEAR
        ax.vlines(x, l, h, color=color, linewidth=0.8)
        ax.add_patch(
            Rectangle(
                (x - 0.34, min(o, c)),
                0.68,
                max(abs(c - o), 0.01),
                facecolor=color,
                edgecolor=color,
                linewidth=0.6,
            )
        )
    labels = np.linspace(0, len(indexes) - 1, min(8, len(indexes)), dtype=int)
    ax.set_xticks(labels)
    ax.set_xticklabels(
        [
            datetime.fromtimestamp(int(series.time[indexes[item]]), tz=UTC).strftime("%m-%d\n%H:%M")
            for item in labels
        ]
    )
    ax.set_xlim(-1, len(indexes))
    ax.set_title(title, color=TEXT, loc="left", fontsize=11, fontweight="bold")
    ax.grid(color=GRID, linewidth=0.5, alpha=0.7)
    ax.tick_params(colors="#94a3b8", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(GRID)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutoff", required=True, help="ISO-8601 UTC replay time")
    parser.add_argument(
        "--mode", choices=("map", "refinement", "plan", "micro"), default="map"
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATASET,
        help="M1 NPZ dataset to render",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="Directory for rendered charts (defaults to the original January replay folder)",
    )
    parser.add_argument(
        "--warmup",
        default="2024-10-01T00:00:00+00:00",
        help="ISO-8601 UTC start used only to provide historical chart context",
    )
    parser.add_argument("--h1-count", type=int, default=144)
    parser.add_argument("--m30-count", type=int, default=144)
    parser.add_argument("--m15-count", type=int, default=160)
    parser.add_argument("--m5-count", type=int, default=216)
    parser.add_argument("--m1-count", type=int, default=300)
    args = parser.parse_args()

    cutoff = parse_utc(args.cutoff)
    warmup = parse_utc(args.warmup)
    if warmup >= cutoff:
        raise SystemExit("--warmup must be earlier than --cutoff")
    dataset = args.dataset if args.dataset.is_absolute() else ROOT / args.dataset
    m1, _ = load_m1_npz(dataset, warmup, cutoff + 60)
    frames = build_timeframes(m1)
    stamp = datetime.fromtimestamp(cutoff, tz=UTC).strftime("%Y%m%d_%H%M")
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)

    if args.mode == "map":
        specs = (("H1", args.h1_count), ("M30", args.m30_count), ("M15", args.m15_count))
    elif args.mode == "refinement":
        specs = (("M30", min(args.m30_count, 120)), ("M15", args.m15_count), ("M5", min(args.m5_count, 216)))
    elif args.mode == "plan":
        specs = (
            ("H1", min(args.h1_count, 120)),
            ("M30", min(args.m30_count, 72)),
            ("M15", min(args.m15_count, 96)),
            ("M5", min(args.m5_count, 120)),
        )
    else:
        specs = (("M15", min(args.m15_count, 96)), ("M5", min(args.m5_count, 144)), ("M1", min(args.m1_count, 240)))

    fig, axes = plt.subplots(
        len(specs), 1, figsize=(14, 3 * len(specs)), facecolor=BG
    )
    for ax, (timeframe, count) in zip(axes, specs):
        ax.set_facecolor(BG)
        draw(ax, frames[timeframe], cutoff, count, f"{timeframe} as-of {args.cutoff}")
    fig.tight_layout()
    destination = output / f"{stamp}_{args.mode}.png"
    fig.savefig(destination, dpi=110, facecolor=BG)
    plt.close(fig)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
