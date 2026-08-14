from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np


def utc_text(value: int) -> str:
    return datetime.fromtimestamp(int(value), timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge ordered MT5 M1 NPZ archives.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args()

    arrays = [np.load(path, allow_pickle=True)["rates"] for path in args.inputs]
    combined = np.sort(np.concatenate(arrays), order="time")
    times = np.asarray(combined["time"], dtype=np.int64)
    keep = np.r_[True, times[1:] != times[:-1]]
    duplicates = int(np.sum(~keep))
    combined = combined[keep]
    times = np.asarray(combined["time"], dtype=np.int64)
    if np.any(times[1:] <= times[:-1]):
        raise ValueError("merged timestamps are not strictly increasing")

    metadata = {
        "symbol": "GOLD",
        "timeframe": "M1",
        "firstUtc": utc_text(int(times[0])),
        "lastUtc": utc_text(int(times[-1])),
        "rows": int(len(combined)),
        "duplicatesRemoved": duplicates,
        "sources": [str(path.resolve()) for path in args.inputs],
        "note": "Weekend and broker-session gaps retained; no candles synthesized.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        rates=combined,
        metadata=np.asarray(json.dumps(metadata, ensure_ascii=False)),
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
