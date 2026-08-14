from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = ROOT / "output" / "mentor_blind_q1" / "raw_packets"
UTC = timezone.utc

TF_SECONDS = {
    "H4": 4 * 60 * 60,
    "H1": 60 * 60,
    "M30": 30 * 60,
    "M15": 15 * 60,
    "M5": 5 * 60,
    "M1": 60,
}
WINDOWS = {"H4": 96, "H1": 144, "M30": 192, "M15": 224, "M5": 240, "M1": 300}

BG = "#080c12"
GRID = "#263241"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
BULL = "#5eead4"
BEAR = "#f87171"


def parse_utc(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=UTC).timestamp())


def load_rates(start: int, end: int) -> np.ndarray:
    with np.load(DATASET, allow_pickle=False) as payload:
        rates = payload["rates"]
    mask = (rates["time"] >= start) & (rates["time"] < end)
    return rates[mask]


def aggregate(rates: np.ndarray, timeframe: str) -> np.ndarray:
    seconds = TF_SECONDS[timeframe]
    if timeframe == "M1":
        result = np.empty(
            len(rates),
            dtype=[("time", "i8"), ("available", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"), ("close", "f8")],
        )
        result["time"] = rates["time"]
        result["available"] = rates["time"] + 60
        for field in ("open", "high", "low", "close"):
            result[field] = rates[field]
        return result

    buckets = rates["time"] // seconds * seconds
    starts = np.flatnonzero(np.r_[True, buckets[1:] != buckets[:-1]])
    ends = np.r_[starts[1:], len(rates)]
    result = np.empty(
        len(starts),
        dtype=[("time", "i8"), ("available", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"), ("close", "f8")],
    )
    for out_index, (left, right) in enumerate(zip(starts, ends)):
        result[out_index] = (
            int(buckets[left]),
            int(buckets[left] + seconds),
            float(rates["open"][left]),
            float(np.max(rates["high"][left:right])),
            float(np.min(rates["low"][left:right])),
            float(rates["close"][right - 1]),
        )
    return result


def draw_candles(axis: plt.Axes, bars: np.ndarray) -> None:
    for x, bar in enumerate(bars):
        colour = BULL if bar["close"] >= bar["open"] else BEAR
        axis.vlines(x, bar["low"], bar["high"], color=colour, linewidth=0.55, zorder=3)
        bottom = min(bar["open"], bar["close"])
        height = max(abs(bar["close"] - bar["open"]), 1e-6)
        axis.add_patch(
            Rectangle(
                (x - 0.34, bottom),
                0.68,
                height,
                facecolor=colour,
                edgecolor=colour,
                linewidth=0.3,
                zorder=4,
            )
        )
    if len(bars):
        ticks = np.unique(np.linspace(0, len(bars) - 1, min(6, len(bars)), dtype=int))
        labels = [datetime.fromtimestamp(int(bars[index]["time"]), tz=UTC).strftime("%m-%d\n%H:%M") for index in ticks]
        axis.set_xticks(ticks, labels)
    axis.set_facecolor(BG)
    axis.grid(color=GRID, linewidth=0.45, alpha=0.35)
    axis.tick_params(colors=MUTED, labelsize=7)
    axis.yaxis.tick_right()
    for spine in axis.spines.values():
        spine.set_color(GRID)


def asof(bars: np.ndarray, cutoff: int, window: int) -> np.ndarray:
    right = int(np.searchsorted(bars["available"], cutoff, side="right"))
    left = max(0, right - window)
    return bars[left:right]


def render_packet(series: dict[str, np.ndarray], cutoff: int, output: Path) -> None:
    fig, axes = plt.subplots(3, 2, figsize=(15, 12), constrained_layout=True)
    for axis, timeframe in zip(axes.ravel(), TF_SECONDS):
        bars = asof(series[timeframe], cutoff, WINDOWS[timeframe])
        draw_candles(axis, bars)
        axis.set_title(
            f"{timeframe} | CLOSED BARS ONLY | {len(bars)} bars",
            loc="left",
            color=TEXT,
            fontsize=9.5,
            fontweight="bold",
        )
    timestamp = datetime.fromtimestamp(cutoff, tz=UTC)
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"GOLD RAW AS-OF {timestamp:%Y-%m-%d %H:%M} UTC",
        color=TEXT,
        fontsize=14,
        fontweight="bold",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=145, facecolor=BG, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def checkpoints(start: int, end: int, hours: int) -> list[int]:
    values: list[int] = []
    current = datetime.fromtimestamp(start, tz=UTC)
    current = current.replace(hour=0, minute=0, second=0, microsecond=0)
    step = timedelta(hours=hours)
    while int(current.timestamp()) < end:
        timestamp = int(current.timestamp())
        if timestamp >= start:
            values.append(timestamp)
        current += step
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Render raw, candidate-free Mentor Q1 replay packets")
    parser.add_argument("--from", dest="date_from", default="2025-01-01")
    parser.add_argument("--to", dest="date_to", default="2025-04-01")
    parser.add_argument("--checkpoint-hours", type=int, default=6)
    parser.add_argument("--at", help="render one UTC checkpoint, for example 2025-01-02T12:00")
    args = parser.parse_args()

    q1_from = parse_utc(args.date_from)
    q1_to = parse_utc(args.date_to)
    warmup = q1_from - 120 * 24 * 60 * 60
    rates = load_rates(warmup, q1_to + 24 * 60 * 60)
    series = {timeframe: aggregate(rates, timeframe) for timeframe in TF_SECONDS}

    if args.at:
        targets = [parse_utc(args.at)]
    else:
        targets = checkpoints(q1_from, q1_to, args.checkpoint_hours)

    for index, cutoff in enumerate(targets, start=1):
        stamp = datetime.fromtimestamp(cutoff, tz=UTC).strftime("%Y-%m-%d_%H%M")
        render_packet(series, cutoff, OUTPUT / f"{stamp}.png")
        if index % 20 == 0 or index == len(targets):
            print(f"RENDERED={index}/{len(targets)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
