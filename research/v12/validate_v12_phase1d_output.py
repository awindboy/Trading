#!/usr/bin/env python3
"""Validate a V12 Phase-1D output pack without rebuilding it."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1D_"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def csv_rows(path: Path) -> int:
    with path.open("rb") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    diagnostics = json.loads((args.output / f"{PREFIX}DIAGNOSTICS.json").read_text(encoding="utf-8"))
    manifest = json.loads((args.output / f"{PREFIX}MANIFEST.json").read_text(encoding="utf-8"))
    require(diagnostics["contract_version"] == "v12-phase1d-temporal-event-state-v1", "wrong contract")
    require(diagnostics["post_cutoff_price_rows_parsed"] == 0, "post-cutoff price parsed")
    require(diagnostics["market"]["last_timestamp"] == diagnostics["causal_cutoff"], "market cutoff mismatch")
    require(diagnostics["market"]["first_unrevealed_timestamp"] > diagnostics["causal_cutoff"], "holdout boundary invalid")
    require(diagnostics["calendar"]["duplicate_conflict_groups_excluded"] == 8, "calendar conflicts not excluded")
    require(diagnostics["clock_alignment"]["best_offset_by_overall_median_range_lift"] == 0, "clock alignment changed")
    require(not diagnostics["trade_authority"] and not diagnostics["sizing_authority"], "authority leak")

    for item in manifest["files"]:
        path = args.output / item["file"]
        require(path.exists(), f"missing file: {path.name}")
        require(sha256_file(path) == item["sha256"], f"hash mismatch: {path.name}")
        if item["rows"] is not None:
            require(csv_rows(path) == item["rows"], f"row mismatch: {path.name}")

    child = read_csv(args.output / f"{PREFIX}V10_CHILD_EVENT_CONTEXT.csv")
    nha = read_csv(args.output / f"{PREFIX}NHA_EVENT_CONTEXT.csv")
    require(len(child) == diagnostics["v10_children"] == 1649, "V10 child count mismatch")
    require(len(nha) == diagnostics["nha_flips"] == 2234, "NHA count mismatch")
    interactions = read_csv(args.output / f"{PREFIX}INTERACTION_SCORECARD.csv")
    candidate = [row for row in interactions if row["year"] == "ALL" and row["group"] == "H20_ALIGNED_PRE_USD_MODHIGH_30_60"]
    require(len(candidate) == 1 and int(float(candidate[0]["children"])) == 35, "interaction candidate changed")
    print(json.dumps({"status": "PASS", "files": len(manifest["files"]), "children": len(child), "nha_flips": len(nha)}))


if __name__ == "__main__":
    main()
