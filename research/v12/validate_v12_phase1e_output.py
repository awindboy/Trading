#!/usr/bin/env python3
"""Validate a complete V12 Phase-1E output pack."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from v12_phase0_core import sha256_file


REQUIRED = {
    "V12_PHASE1E_CLOCK_SENTINEL_VALIDATION.csv",
    "V12_PHASE1E_SESSION_ACTIVITY.csv",
    "V12_PHASE1E_V10_CHILD_SESSION_CONTEXT.csv",
    "V12_PHASE1E_V10_CHILD_SESSION_SCORECARD.csv",
    "V12_PHASE1E_NHA_SESSION_CONTEXT.csv",
    "V12_PHASE1E_NHA_SESSION_SCORECARD.csv",
    "V12_PHASE1E_H20_INTERACTION_CONTEXT.csv",
    "V12_PHASE1E_H20_INTERACTION_SCORECARD.csv",
    "V12_PHASE1E_DIAGNOSTICS.json",
    "V12_PHASE1E_MANIFEST.json",
}


def csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    observed = {path.name for path in args.output.iterdir() if path.is_file()}
    if observed != REQUIRED:
        raise ValueError(f"output file set mismatch missing={REQUIRED-observed} extra={observed-REQUIRED}")
    diagnostics = json.loads((args.output / "V12_PHASE1E_DIAGNOSTICS.json").read_text(encoding="utf-8"))
    if diagnostics["calendar_quality"]["duplicate_rows"] != 0:
        raise ValueError("calendar duplicate rows remain")
    if not diagnostics["calendar_quality"]["all_sentinels_pass"]:
        raise ValueError("calendar clock sentinel failed")
    if diagnostics["post_cutoff_price_rows_parsed"] != 0:
        raise ValueError("post-cutoff price row parsed")
    if diagnostics["v10_children"] != 1649 or diagnostics["nha_flips"] != 2234:
        raise ValueError("frozen overlay count changed")
    if diagnostics["trade_authority"] or diagnostics["sizing_authority"]:
        raise ValueError("unauthorized action flag")
    if csv_rows(args.output / "V12_PHASE1E_V10_CHILD_SESSION_CONTEXT.csv") != 1649:
        raise ValueError("child context count mismatch")
    if csv_rows(args.output / "V12_PHASE1E_NHA_SESSION_CONTEXT.csv") != 2234:
        raise ValueError("NHA context count mismatch")
    manifest = json.loads((args.output / "V12_PHASE1E_MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = args.output / item["file"]
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"manifest hash mismatch: {path.name}")
    print(json.dumps({"status": "PASS", "files": len(REQUIRED), "children": 1649, "nha_flips": 2234}, indent=2))


if __name__ == "__main__":
    main()
