#!/usr/bin/env python3
"""Validate one or two V12 Phase-1M output packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file


CONTRACT_VERSION = "v12-phase1m-h1-transition-child-v1"
REQUIRED = {
    "V12_PHASE1M_H1_K1_LEDGER.csv",
    "V12_PHASE1M_H1_K1_H4_FAST_ALIGNED_LEDGER.csv",
    "V12_PHASE1M_H1_K1_H4_FAST_STD_ALIGNED_LEDGER.csv",
    "V12_PHASE1M_SCORECARD.csv", "V12_PHASE1M_GATES.csv",
    "V12_PHASE1M_DIAGNOSTICS.json",
}


def validate(path: Path) -> dict:
    manifest = json.loads((path / "V12_PHASE1M_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract version mismatch")
    if {row["name"] for row in manifest["files"]} != REQUIRED:
        raise ValueError("manifest members mismatch")
    for row in manifest["files"]:
        member = path / row["name"]
        if member.stat().st_size != row["bytes"] or sha256_file(member) != row["sha256"]:
            raise ValueError(f"manifest mismatch: {member.name}")
    diagnostics = json.loads((path / "V12_PHASE1M_DIAGNOSTICS.json").read_text(encoding="utf-8"))
    gates = pd.read_csv(path / "V12_PHASE1M_GATES.csv")
    expected = {"H4_CORE": 6857, "H1_K1": 8514,
                "H1_K1_H4_FAST_ALIGNED": 3608,
                "H1_K1_H4_FAST_STD_ALIGNED": 3202}
    if diagnostics["rows"] != expected:
        raise ValueError("population mismatch")
    if bool(gates["OVERALL"].any()) or diagnostics["overall_passes"] != 0:
        raise ValueError("failed viability gate unexpectedly passed")
    if diagnostics["post_cutoff_price_rows_parsed"] != 0:
        raise ValueError("post-cutoff row parsed")
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    diagnostics = validate(args.output)
    identical = None
    if args.compare:
        if validate(args.compare) != diagnostics:
            raise ValueError("diagnostics differ")
        names = REQUIRED | {"V12_PHASE1M_MANIFEST.json"}
        identical = all((args.output / name).read_bytes() == (args.compare / name).read_bytes() for name in names)
        if not identical:
            raise ValueError("packs differ")
    print(json.dumps({"files": 7, "rows": diagnostics["rows"],
                      "overall_passes": diagnostics["overall_passes"],
                      "post_cutoff_rows": diagnostics["post_cutoff_price_rows_parsed"],
                      "byte_identical_compare": identical}, indent=2))


if __name__ == "__main__":
    main()
