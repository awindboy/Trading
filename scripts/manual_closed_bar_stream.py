"""Reveal one newly closed bar checkpoint at a time without interpretation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz, parse_utc


UTC = timezone.utc


def stamp(value: int) -> str:
    return datetime.fromtimestamp(value, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def latest_closed(series, cutoff: int):
    indexes = [
        index
        for index, available in enumerate(series.available_time)
        if int(available) <= cutoff
    ]
    return indexes[-1] if indexes else None


def print_bar(series, index: int) -> None:
    print(
        f"[{series.timeframe}] {stamp(int(series.time[index]))} "
        f"O={series.open[index]:.2f} H={series.high[index]:.2f} "
        f"L={series.low[index]:.2f} C={series.close[index]:.2f} "
        f"SP={series.spread_points[index]:.0f}",
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--warmup", required=True)
    parser.add_argument("--step-minutes", type=int, default=15)
    parser.add_argument("--timeframes", default="H1,M30,M15")
    args = parser.parse_args()

    start = parse_utc(args.start)
    end = parse_utc(args.end)
    warmup = parse_utc(args.warmup)
    m1, _ = load_m1_npz(args.dataset, warmup, end)
    frames = build_timeframes(m1)
    cursor = start
    timeframes = tuple(
        timeframe.strip()
        for timeframe in args.timeframes.split(",")
        if timeframe.strip()
    )
    if args.step_minutes <= 0:
        raise SystemExit("--step-minutes must be positive")
    if not timeframes:
        raise SystemExit("--timeframes must not be empty")
    last = {timeframe: None for timeframe in timeframes}

    print(f"READY cursor={stamp(cursor)} end={stamp(end)}", flush=True)
    while cursor < end:
        command = sys.stdin.readline()
        if not command:
            return 0
        if command.strip().lower() in {"q", "quit"}:
            return 0
        cursor = min(cursor + args.step_minutes * 60, end)
        print(f"CHECKPOINT {stamp(cursor)}", flush=True)
        for timeframe in timeframes:
            index = latest_closed(frames[timeframe], cursor)
            if index is not None and index != last[timeframe]:
                print_bar(frames[timeframe], index)
                last[timeframe] = index
        if cursor >= end:
            print("END", flush=True)
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
