"""Find the first closed bar meeting a predeclared price condition."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from mentor_engine.data import build_timeframes, load_m1_npz, parse_utc


UTC = timezone.utc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--field", choices=("high", "low", "close"), required=True)
    parser.add_argument("--operator", choices=("ge", "le"), required=True)
    parser.add_argument("--price", type=float, required=True)
    parser.add_argument(
        "--timeframe",
        choices=("M1", "M5", "M15", "M30", "H1"),
        default="M1",
    )
    args = parser.parse_args()

    m1, _ = load_m1_npz(args.dataset, parse_utc(args.start), parse_utc(args.end))
    series = build_timeframes(m1)[args.timeframe]
    values = getattr(series, args.field)
    matches = values >= args.price if args.operator == "ge" else values <= args.price
    indexes = np.flatnonzero(matches)
    if not len(indexes):
        print("NONE")
        return 0
    index = int(indexes[0])
    observed = datetime.fromtimestamp(int(series.available_time[index]), tz=UTC).isoformat()
    print(
        f"TF={series.timeframe}",
        observed,
        f"O={series.open[index]:.2f}",
        f"H={series.high[index]:.2f}",
        f"L={series.low[index]:.2f}",
        f"C={series.close[index]:.2f}",
        f"SP={series.spread_points[index]:.0f}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
