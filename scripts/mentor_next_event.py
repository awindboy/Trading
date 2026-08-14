"""Return only the earliest of several predeclared replay events."""

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
    parser.add_argument(
        "--event",
        action="append",
        required=True,
        help="NAME:TF:FIELD:OP:PRICE, where OP is ge or le",
    )
    args = parser.parse_args()

    m1, _ = load_m1_npz(args.dataset, parse_utc(args.start), parse_utc(args.end))
    frames = build_timeframes(m1)
    found: list[tuple[int, int, str, object, int]] = []
    for priority, raw in enumerate(args.event):
        name, timeframe, field, operator, price_raw = raw.split(":", 4)
        if timeframe not in frames or field not in {"high", "low", "close"}:
            raise SystemExit(f"Invalid event: {raw}")
        if operator not in {"ge", "le"}:
            raise SystemExit(f"Invalid operator: {operator}")
        price = float(price_raw)
        series = frames[timeframe]
        values = getattr(series, field)
        matches = values >= price if operator == "ge" else values <= price
        indexes = np.flatnonzero(matches)
        if len(indexes):
            index = int(indexes[0])
            found.append((int(series.available_time[index]), priority, name, series, index))

    if not found:
        print("NONE")
        return 0

    observed, _, name, series, index = min(found, key=lambda item: (item[0], item[1]))
    stamp = datetime.fromtimestamp(observed, tz=UTC).isoformat()
    print(
        f"EVENT={name}",
        f"TF={series.timeframe}",
        stamp,
        f"O={series.open[index]:.2f}",
        f"H={series.high[index]:.2f}",
        f"L={series.low[index]:.2f}",
        f"C={series.close[index]:.2f}",
        f"SP={series.spread_points[index]:.0f}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
