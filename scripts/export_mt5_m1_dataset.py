"""Export a closed MT5 M1 UTC range to the replay engine's NPZ format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mt5_rate_source import load_mt5_m1_rates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="GOLD")
    parser.add_argument("--from-utc", required=True)
    parser.add_argument("--to-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = args.output.resolve()
    if output.exists() and not args.force:
        print(f"DATASET_EXISTS {output}")
        return 0
    if args.force:
        output.unlink(missing_ok=True)
    rates, metadata = load_mt5_m1_rates(
        symbol=args.symbol,
        bars=0,
        from_utc=args.from_utc,
        to_utc=args.to_utc,
        cache_path=output,
    )
    print("MT5_M1_DATASET_OK")
    print(json.dumps({**metadata, "bars": len(rates)}, ensure_ascii=False))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
