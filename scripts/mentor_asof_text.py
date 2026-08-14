"""Print closed OHLC bars through one as-of timestamp without interpretation."""

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--warmup", required=True)
    parser.add_argument("--timeframes", default="H1,M30,M15")
    parser.add_argument("--count", type=int, default=32)
    args = parser.parse_args()

    cutoff = parse_utc(args.cutoff)
    warmup = parse_utc(args.warmup)
    if warmup >= cutoff:
        raise SystemExit("--warmup must be earlier than --cutoff")
    m1, _ = load_m1_npz(args.dataset, warmup, cutoff)
    frames = build_timeframes(m1)

    for timeframe in args.timeframes.split(","):
        series = frames[timeframe.strip()]
        indexes = [i for i, available in enumerate(series.available_time) if int(available) <= cutoff]
        print(f"[{series.timeframe}] AS_OF={args.cutoff}")
        for index in indexes[-args.count :]:
            stamp = datetime.fromtimestamp(int(series.time[index]), tz=UTC).strftime("%Y-%m-%d %H:%M")
            print(
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
