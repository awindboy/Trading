#!/usr/bin/env python3
"""Validate one or two V12 Phase-1K result packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file
from v12_phase1k_core import CONTRACT_VERSION, POLICIES


REQUIRED = {
    "V12_PHASE1K_RUN_EVENT_TIMES.csv", "V12_PHASE1K_CHILD_POLICY_LEDGER.csv",
    "V12_PHASE1K_POLICY_SCORECARD.csv", "V12_PHASE1K_GATES.csv",
    "V12_PHASE1K_DIAGNOSTICS.json",
}


def validate(path: Path) -> dict:
    manifest = json.loads((path / "V12_PHASE1K_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract version mismatch")
    if {row["name"] for row in manifest["files"]} != REQUIRED:
        raise ValueError("manifest members mismatch")
    for row in manifest["files"]:
        member = path / row["name"]
        if member.stat().st_size != row["bytes"] or sha256_file(member) != row["sha256"]:
            raise ValueError(f"manifest mismatch: {member.name}")
    diagnostics = json.loads((path / "V12_PHASE1K_DIAGNOSTICS.json").read_text(encoding="utf-8"))
    events = pd.read_csv(path / "V12_PHASE1K_RUN_EVENT_TIMES.csv")
    ledger = pd.read_csv(path / "V12_PHASE1K_CHILD_POLICY_LEDGER.csv")
    scorecard = pd.read_csv(path / "V12_PHASE1K_POLICY_SCORECARD.csv")
    gates = pd.read_csv(path / "V12_PHASE1K_GATES.csv")
    if len(events) != 679 or events["run_id"].duplicated().any():
        raise ValueError("run-event population mismatch")
    if set(scorecard["policy"]) != set(POLICIES):
        raise ValueError("policy set mismatch")
    if diagnostics["policy_rows"] != len(ledger):
        raise ValueError("policy ledger count mismatch")
    if bool(gates.set_index("gate").loc["OVERALL", "passed"]) != diagnostics["primary_pass"]:
        raise ValueError("gate mismatch")
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
        names = REQUIRED | {"V12_PHASE1K_MANIFEST.json"}
        identical = all((args.output / name).read_bytes() == (args.compare / name).read_bytes() for name in names)
        if not identical:
            raise ValueError("packs differ")
    print(json.dumps({"files": 6, "funded_runs": diagnostics["funded_runs"],
                      "entry_children": diagnostics["entry_children"],
                      "primary_pass": diagnostics["primary_pass"],
                      "post_cutoff_rows": diagnostics["post_cutoff_price_rows_parsed"],
                      "byte_identical_compare": identical}, indent=2))


if __name__ == "__main__":
    main()
