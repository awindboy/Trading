"""Build a full-path June 2026 MTF atlas without authorizing trades.

The atlas is deliberately outcome-visible. It is used only to discover every
plausible scenario. A separate as-of audit must approve any benchmark trade.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
BG = "#0f1419"
GRID = "#29323b"
UP = "#22c55e"
DOWN = "#ef4444"
TEXT = "#e5e7eb"


def timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def load_joined(first: Path, second: Path) -> tuple[np.ndarray, dict[str, object]]:
    left = np.load(first, allow_pickle=True)["rates"]
    right = np.load(second, allow_pickle=True)["rates"]
    combined = np.sort(np.concatenate([left, right]), order="time")
    times = np.asarray(combined["time"], dtype=np.int64)
    duplicate_count = int(np.sum(times[1:] == times[:-1]))
    keep = np.r_[True, times[1:] != times[:-1]]
    combined = combined[keep]
    times = np.asarray(combined["time"], dtype=np.int64)
    backward = int(np.sum(times[1:] < times[:-1]))
    boundary_gap = int(right[0]["time"] - left[-1]["time"])
    large_gaps = [
        {
            "leftUtc": datetime.fromtimestamp(int(times[i]), UTC).isoformat(),
            "rightUtc": datetime.fromtimestamp(int(times[i + 1]), UTC).isoformat(),
            "seconds": int(times[i + 1] - times[i]),
        }
        for i in np.flatnonzero(np.diff(times) > 3 * 24 * 3600)
    ]
    audit = {
        "firstUtc": datetime.fromtimestamp(int(times[0]), UTC).isoformat(),
        "lastUtc": datetime.fromtimestamp(int(times[-1]), UTC).isoformat(),
        "rows": int(len(combined)),
        "duplicatesRemoved": duplicate_count,
        "backwardTimestamps": backward,
        "sourceBoundarySeconds": boundary_gap,
        "largeGaps": large_gaps,
        "note": "Weekend and broker-session gaps are retained; no candles are synthesized.",
    }
    return combined, audit


def aggregate(rates: np.ndarray, seconds: int) -> list[dict[str, float | int]]:
    result: list[dict[str, float | int]] = []
    if not len(rates):
        return result
    keys = np.asarray(rates["time"], dtype=np.int64) // seconds * seconds
    starts = np.r_[0, np.flatnonzero(keys[1:] != keys[:-1]) + 1]
    ends = np.r_[starts[1:], len(rates)]
    for left, right in zip(starts, ends):
        rows = rates[left:right]
        result.append(
            {
                "time": int(keys[left]),
                "open": float(rows[0]["open"]),
                "high": float(np.max(rows["high"])),
                "low": float(np.min(rows["low"])),
                "close": float(rows[-1]["close"]),
            }
        )
    return result


def draw(axis, bars: list[dict[str, float | int]], title: str) -> None:
    axis.set_facecolor(BG)
    axis.grid(True, color=GRID, linewidth=0.45, alpha=0.7)
    axis.tick_params(colors="#aeb8c2", labelsize=7)
    axis.yaxis.tick_right()
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M", tz=UTC))
    for spine in axis.spines.values():
        spine.set_color(GRID)
    if not bars:
        axis.text(0.5, 0.5, "NO DATA", transform=axis.transAxes, color=TEXT)
        return
    xs = [mdates.date2num(datetime.fromtimestamp(int(row["time"]), UTC)) for row in bars]
    width = (xs[1] - xs[0]) * 0.68 if len(xs) > 1 else 0.0004
    for x, row in zip(xs, bars):
        colour = UP if row["close"] >= row["open"] else DOWN
        axis.vlines(x, row["low"], row["high"], color=colour, linewidth=0.7)
        bottom = min(row["open"], row["close"])
        height = max(abs(row["close"] - row["open"]), 0.01)
        axis.add_patch(Rectangle((x - width / 2, bottom), width, height,
                                 facecolor=colour, edgecolor=colour, linewidth=0.3))
    axis.set_title(title, loc="left", color=TEXT, fontsize=9, pad=5)


def render_day(rates: np.ndarray, day: datetime, output: Path) -> Path:
    day_start = int(day.timestamp())
    day_end = day_start + 24 * 3600
    contexts = [
        ("H1 | prior 10 days + current day", 3600, day_start - 10 * 86400, day_end),
        ("M30 | prior 3 days + current day", 1800, day_start - 3 * 86400, day_end),
        ("M15 | prior day + current day", 900, day_start - 86400, day_end),
        ("M5 | current day", 300, day_start, day_end),
    ]
    fig, axes = plt.subplots(4, 1, figsize=(16, 13), dpi=140)
    fig.patch.set_facecolor(BG)
    for axis, (title, seconds, start, end) in zip(axes, contexts):
        selected = rates[(rates["time"] >= start) & (rates["time"] < end)]
        draw(axis, aggregate(selected, seconds), title)
        axis.axvline(mdates.date2num(day), color="#f8fafc", linestyle=(0, (3, 3)),
                     linewidth=0.8, alpha=0.75)
    fig.suptitle(day.strftime("GOLD Oracle Atlas | %Y-%m-%d UTC"), color=TEXT, fontsize=13)
    fig.subplots_adjust(left=0.035, right=0.965, top=0.955, bottom=0.04, hspace=0.24)
    path = output / f"{day:%Y-%m-%d}.png"
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def render_warmup_context(rates: np.ndarray, cutoff: datetime, output: Path) -> Path:
    """Render only information that was available at the June open."""
    end = int(cutoff.timestamp())
    contexts = [
        ("H1 | prior 30 days", 3600, end - 30 * 86400, end),
        ("H1 | prior 120 days", 3600, end - 120 * 86400, end),
        ("H4 | prior 365 days (context only)", 4 * 3600, end - 365 * 86400, end),
        ("D1 | full available history (context only)", 86400,
         int(rates[0]["time"]), end),
    ]
    fig, axes = plt.subplots(4, 1, figsize=(18, 13), dpi=150)
    fig.patch.set_facecolor(BG)
    for axis, (title, seconds, start, stop) in zip(axes, contexts):
        selected = rates[(rates["time"] >= start) & (rates["time"] < stop)]
        draw(axis, aggregate(selected, seconds), title)
    fig.suptitle(
        "GOLD pre-June structure context | as-of 2026-06-01 00:00 UTC",
        color=TEXT,
        fontsize=13,
    )
    fig.subplots_adjust(left=0.035, right=0.965, top=0.955, bottom=0.04, hspace=0.24)
    path = output / "WARMUP_CONTEXT_ASOF_2026-06-01.png"
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    charts = output / "oracle_atlas"
    charts.mkdir(parents=True, exist_ok=True)
    rates, audit = load_joined(args.first.resolve(), args.second.resolve())
    (output / "data_continuity_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    start = datetime(2026, 6, 1, tzinfo=UTC)
    paths = []
    warmup_chart = render_warmup_context(rates, start, charts)
    day = start
    while day < datetime(2026, 7, 1, tzinfo=UTC):
        selected = rates[(rates["time"] >= int(day.timestamp())) &
                         (rates["time"] < int((day + timedelta(days=1)).timestamp()))]
        if len(selected):
            paths.append(render_day(rates, day, charts))
        day += timedelta(days=1)
    (output / "atlas_manifest.json").write_text(
        json.dumps(
            {
                "warmupContext": str(warmup_chart),
                "charts": [str(path) for path in paths],
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"charts": len(paths), **audit}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
