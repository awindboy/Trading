from __future__ import annotations

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
OUTPUT = ROOT / "output" / "mentor_january_destination_replay" / "raw_packets"
UTC = timezone.utc
BG, GRID, TEXT = "#080c12", "#263241", "#e2e8f0"
BULL, BEAR = "#5eead4", "#f87171"


def draw(ax, series, start: int, end: int, title: str) -> None:
    mask = (series.time >= start) & (series.time < end)
    indexes = np.flatnonzero(mask)
    if not len(indexes):
        return
    for x, index in enumerate(indexes):
        o, h, l, c = map(float, (series.open[index], series.high[index], series.low[index], series.close[index]))
        color = BULL if c >= o else BEAR
        ax.vlines(x, l, h, color=color, linewidth=0.7)
        ax.add_patch(Rectangle((x - 0.34, min(o, c)), 0.68, max(abs(c - o), 0.01), color=color))
    labels = np.linspace(0, len(indexes) - 1, min(8, len(indexes)), dtype=int)
    ax.set_xticks(labels)
    ax.set_xticklabels([
        datetime.fromtimestamp(int(series.time[indexes[item]]), tz=UTC).strftime("%m-%d\n%H:%M")
        for item in labels
    ])
    ax.set_xlim(-1, len(indexes))
    ax.set_title(title, color=TEXT, loc="left", fontsize=11, fontweight="bold")
    ax.grid(color=GRID, linewidth=0.5, alpha=0.7)
    ax.tick_params(colors="#94a3b8", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(GRID)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    warmup = parse_utc("2024-11-01T00:00:00+00:00")
    finish = parse_utc("2025-02-03T00:00:00+00:00")
    m1, _ = load_m1_npz(DATASET, warmup, finish)
    frames = build_timeframes(m1)
    weeks = [
        ("W1", "2025-01-01T00:00:00+00:00", "2025-01-06T00:00:00+00:00"),
        ("W2", "2025-01-06T00:00:00+00:00", "2025-01-13T00:00:00+00:00"),
        ("W3", "2025-01-13T00:00:00+00:00", "2025-01-20T00:00:00+00:00"),
        ("W4", "2025-01-20T00:00:00+00:00", "2025-01-27T00:00:00+00:00"),
        ("W5", "2025-01-27T00:00:00+00:00", "2025-02-01T00:00:00+00:00"),
    ]
    for label, start_text, end_text in weeks:
        start, end = parse_utc(start_text), parse_utc(end_text)
        fig, axes = plt.subplots(3, 1, figsize=(18, 13), facecolor=BG)
        for ax in axes:
            ax.set_facecolor(BG)
        draw(axes[0], frames["H4"], max(warmup, start - 45 * 86400), end, f"{label} as-of H4")
        draw(axes[1], frames["H1"], max(warmup, start - 14 * 86400), end, f"{label} as-of H1")
        draw(axes[2], frames["M30"], start, end, f"{label} M30 detail")
        fig.tight_layout()
        fig.savefig(OUTPUT / f"{label}.png", dpi=130, facecolor=BG)
        plt.close(fig)
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
