"""Index outcome-visible June moves for later human causal audit.

This script does not authorize a trade or identify ICT structure. It only makes
sure that the Oracle pass reviews both directions across the entire month.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from build_june2026_oracle_atlas import aggregate, load_joined, timestamp


UTC = timezone.utc


def iso(value: int) -> str:
    return datetime.fromtimestamp(int(value), UTC).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-move", type=float, default=22.0)
    args = parser.parse_args()

    rates, _ = load_joined(args.first.resolve(), args.second.resolve())
    start = timestamp("2026-06-01T00:00:00Z")
    end = timestamp("2026-07-01T00:00:00Z")
    selected = rates[(rates["time"] >= start - 6 * 3600) & (rates["time"] < end + 18 * 3600)]
    bars = aggregate(selected, 300)
    opportunities: list[dict[str, object]] = []

    # Twelve M5 bars establish a local turning area. The next twelve hours are
    # visible only for Oracle discovery, never for the later as-of audit.
    for index in range(12, len(bars) - 144):
        bar = bars[index]
        if not (start <= int(bar["time"]) < end):
            continue
        past = bars[index - 12:index + 1]
        future = bars[index + 1:index + 145]
        future_high = max(future, key=lambda row: float(row["high"]))
        future_low = min(future, key=lambda row: float(row["low"]))
        if float(bar["low"]) <= min(float(row["low"]) for row in past):
            move = float(future_high["high"]) - float(bar["low"])
            if move >= args.minimum_move:
                opportunities.append({
                    "direction": "LONG", "pivotTimeUtc": iso(int(bar["time"])),
                    "pivotPrice": float(bar["low"]), "deliveryEndUtc": iso(int(future_high["time"])),
                    "deliveryPrice": float(future_high["high"]), "grossMove": move,
                })
        if float(bar["high"]) >= max(float(row["high"]) for row in past):
            move = float(bar["high"]) - float(future_low["low"])
            if move >= args.minimum_move:
                opportunities.append({
                    "direction": "SHORT", "pivotTimeUtc": iso(int(bar["time"])),
                    "pivotPrice": float(bar["high"]), "deliveryEndUtc": iso(int(future_low["time"])),
                    "deliveryPrice": float(future_low["low"]), "grossMove": move,
                })

    # Collapse adjacent bars describing the same physical turn. Opposite
    # directions remain independent so both sides of a range are reviewed.
    clustered: list[dict[str, object]] = []
    for direction in ("LONG", "SHORT"):
        same_side = sorted(
            (item for item in opportunities if item["direction"] == direction),
            key=lambda row: timestamp(str(row["pivotTimeUtc"])),
        )
        side_clusters: list[list[dict[str, object]]] = []
        for item in same_side:
            pivot = timestamp(str(item["pivotTimeUtc"]))
            if not side_clusters or pivot - timestamp(
                str(side_clusters[-1][-1]["pivotTimeUtc"])
            ) > 3 * 3600:
                side_clusters.append([item])
            else:
                side_clusters[-1].append(item)
        clustered.extend(
            max(group, key=lambda row: float(row["grossMove"]))
            for group in side_clusters
        )
    clustered.sort(key=lambda row: timestamp(str(row["pivotTimeUtc"])))

    for number, item in enumerate(clustered, 1):
        item["candidateId"] = f"J26-O-{number:03d}"
        item["status"] = "ORACLE_DISCOVERY_ONLY"

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fields = [
        "candidateId", "direction", "pivotTimeUtc", "pivotPrice",
        "deliveryEndUtc", "deliveryPrice", "grossMove", "status",
    ]
    with (output / "oracle_move_index.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(clustered)
    (output / "oracle_move_index.json").write_text(
        json.dumps(clustered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"candidates": len(clustered)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
