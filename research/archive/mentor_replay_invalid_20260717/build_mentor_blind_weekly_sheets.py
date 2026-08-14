from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "mentor_blind_q1" / "weekly_sheets"
UTC = timezone.utc

from build_mentor_blind_q1_packets import aggregate, draw_candles, load_rates, parse_utc


def day_slice(bars: np.ndarray, start: int, end: int, prefix: int) -> np.ndarray:
    left = int(np.searchsorted(bars["available"], start, side="right"))
    right = int(np.searchsorted(bars["available"], end, side="right"))
    return bars[max(0, left - prefix) : right]


def render_week(series: dict[str, np.ndarray], monday: int) -> None:
    timeframes = ("M30", "M15", "M5")
    prefixes = {"M30": 20, "M15": 28, "M5": 36}
    fig, axes = plt.subplots(5, 3, figsize=(18, 20), constrained_layout=True)
    for day_offset in range(5):
        start = monday + day_offset * 24 * 60 * 60
        end = start + 24 * 60 * 60
        day_label = datetime.fromtimestamp(start, tz=UTC).strftime("%Y-%m-%d")
        for column, timeframe in enumerate(timeframes):
            axis = axes[day_offset, column]
            bars = day_slice(series[timeframe], start, end, prefixes[timeframe])
            draw_candles(axis, bars)
            axis.set_title(
                f"{day_label} | {timeframe} | full day with prior context",
                loc="left",
                color="#e2e8f0",
                fontsize=9,
                fontweight="bold",
            )
    week = datetime.fromtimestamp(monday, tz=UTC).strftime("%Y-%m-%d")
    fig.patch.set_facecolor("#080c12")
    fig.suptitle(
        f"GOLD MENTOR BLIND REVIEW | WEEK OF {week} UTC | RAW OHLC ONLY",
        color="#e2e8f0",
        fontsize=15,
        fontweight="bold",
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT / f"week_{week}.png", dpi=135, facecolor="#080c12", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", default="2025-01-06")
    parser.add_argument("--to", dest="date_to", default="2025-04-01")
    args = parser.parse_args()

    start = parse_utc(args.date_from)
    end = parse_utc(args.date_to)
    rates = load_rates(start - 14 * 24 * 60 * 60, end + 24 * 60 * 60)
    series = {timeframe: aggregate(rates, timeframe) for timeframe in ("M30", "M15", "M5")}

    monday = datetime.fromtimestamp(start, tz=UTC)
    monday = monday - timedelta(days=monday.weekday())
    current = int(monday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    count = 0
    while current < end:
        render_week(series, current)
        count += 1
        current += 7 * 24 * 60 * 60
    print(f"WEEKLY_SHEETS={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
