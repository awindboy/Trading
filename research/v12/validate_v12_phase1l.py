#!/usr/bin/env python3
"""Validate one or two V12 Phase-1L output packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file
from v12_phase1l_core import CONTRACT_VERSION


REQUIRED = {
    "V12_PHASE1L_H4_CHILD_LEDGER.csv", "V12_PHASE1L_H1_CHILD_LEDGER.csv",
    "V12_PHASE1L_SCORECARD.csv", "V12_PHASE1L_FEATURE_AUC.csv",
    "V12_PHASE1L_FEATURE_SCREEN.csv", "V12_PHASE1L_GATES.csv",
    "V12_PHASE1L_DIAGNOSTICS.json",
}


def validate(path: Path) -> dict:
    manifest = json.loads((path / "V12_PHASE1L_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract version mismatch")
    if {row["name"] for row in manifest["files"]} != REQUIRED:
        raise ValueError("manifest members mismatch")
    for row in manifest["files"]:
        member = path / row["name"]
        if member.stat().st_size != row["bytes"] or sha256_file(member) != row["sha256"]:
            raise ValueError(f"manifest mismatch: {member.name}")
    diagnostics = json.loads((path / "V12_PHASE1L_DIAGNOSTICS.json").read_text(encoding="utf-8"))
    h4 = pd.read_csv(path / "V12_PHASE1L_H4_CHILD_LEDGER.csv")
    h1 = pd.read_csv(path / "V12_PHASE1L_H1_CHILD_LEDGER.csv")
    gates = pd.read_csv(path / "V12_PHASE1L_GATES.csv")
    parity = diagnostics["parity"]
    if len(h4) != 6857 or len(h1) != 26881:
        raise ValueError("population mismatch")
    if parity["matched_rows"] != 6770 or parity["old_rows"] != 6770 or parity["new_rows"] != 6770:
        raise ValueError("H4 parity population mismatch")
    if parity["entry_max_abs_diff"] != 0 or parity["stop_hit_mismatches"] != 0:
        raise ValueError("H4 parity mismatch")
    if parity["stop_max_abs_diff"] > 1e-9 or parity["R_max_abs_diff"] > 1e-12:
        raise ValueError("H4 numeric parity mismatch")
    if bool(gates.set_index("gate").loc["OVERALL", "passed"]) or diagnostics["h1_viability_pass"]:
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
        names = REQUIRED | {"V12_PHASE1L_MANIFEST.json"}
        identical = all((args.output / name).read_bytes() == (args.compare / name).read_bytes() for name in names)
        if not identical:
            raise ValueError("packs differ")
    print(json.dumps({"files": 8, "h4_rows": diagnostics["h4_rows"],
                      "h1_rows": diagnostics["h1_rows"],
                      "h1_viability_pass": diagnostics["h1_viability_pass"],
                      "post_cutoff_rows": diagnostics["post_cutoff_price_rows_parsed"],
                      "byte_identical_compare": identical}, indent=2))


if __name__ == "__main__":
    main()
