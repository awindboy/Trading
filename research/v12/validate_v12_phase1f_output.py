#!/usr/bin/env python3
"""Validate a complete V12 Phase-1F output pack."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from v12_phase0_core import sha256_file


REQUIRED = {
    "V12_PHASE1F_TARGET_DECISIONS.csv",
    "V12_PHASE1F_TARGET_OUTCOMES.csv",
    "V12_PHASE1F_TARGET_SCORECARD.csv",
    "V12_PHASE1F_V10_CHILD_TARGET_CONTEXT.csv",
    "V12_PHASE1F_V10_CHILD_TARGET_SCORECARD.csv",
    "V12_PHASE1F_NHA_TARGET_CONTEXT.csv",
    "V12_PHASE1F_NHA_TARGET_SCORECARD.csv",
    "V12_PHASE1F_CARRY_TARGET_CONTEXT.csv",
    "V12_PHASE1F_CARRY_TARGET_SCORECARD.csv",
    "V12_PHASE1F_REPAIR_TARGET_CONTEXT.csv",
    "V12_PHASE1F_REPAIR_TARGET_SCORECARD.csv",
    "V12_PHASE1F_DIAGNOSTICS.json",
    "V12_PHASE1F_MANIFEST.json",
}


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    observed = {path.name for path in args.output.iterdir() if path.is_file()}
    if observed != REQUIRED:
        raise ValueError(f"output file set mismatch missing={REQUIRED-observed} extra={observed-REQUIRED}")

    diagnostics = json.loads((args.output / "V12_PHASE1F_DIAGNOSTICS.json").read_text(encoding="utf-8"))
    if diagnostics["journeys"] != 2649 or diagnostics["levels"] != 17610:
        raise ValueError("frozen Phase-1B universe changed")
    if diagnostics["v10_children"] != 1649 or diagnostics["nha_flips"] != 2234:
        raise ValueError("frozen overlay count changed")
    if diagnostics["carry_children"] != 118 or diagnostics["repair_episodes"] != 60:
        raise ValueError("frozen Phase-1C population changed")
    if diagnostics["post_cutoff_price_rows_parsed"] != 0:
        raise ValueError("post-cutoff price row parsed")
    if diagnostics["trade_authority"] or diagnostics["sizing_authority"]:
        raise ValueError("unauthorized action flag")

    decisions = read_csv(args.output / "V12_PHASE1F_TARGET_DECISIONS.csv")
    outcomes = read_csv(args.output / "V12_PHASE1F_TARGET_OUTCOMES.csv")
    children = read_csv(args.output / "V12_PHASE1F_V10_CHILD_TARGET_CONTEXT.csv")
    nhas = read_csv(args.output / "V12_PHASE1F_NHA_TARGET_CONTEXT.csv")
    carries = read_csv(args.output / "V12_PHASE1F_CARRY_TARGET_CONTEXT.csv")
    repairs = read_csv(args.output / "V12_PHASE1F_REPAIR_TARGET_CONTEXT.csv")
    if any(row["outcome_fields_present"].lower() != "false" for row in decisions):
        raise ValueError("outcome field leaked into target decision ledger")
    if any(row["outcome_fields_present"].lower() != "true" for row in outcomes):
        raise ValueError("target outcome marker missing")
    outcome_ids = [row["target_id"] for row in outcomes]
    if len(outcome_ids) != len(set(outcome_ids)):
        raise ValueError("duplicate target outcome ID")
    selected_ids = [row["target_id"] for row in decisions if row["selection_status"] == "TARGET_SELECTED"]
    if set(selected_ids) != set(outcome_ids):
        raise ValueError("target decision/outcome ID mismatch")
    if len(children) != 1649 or len(nhas) != 2234 or len(carries) != 118 or len(repairs) != 60:
        raise ValueError("context row count mismatch")
    if sum(row["bridge_target_state"] == "TARGET_UNFINISHED" for row in carries) != diagnostics["carry_children_unfinished_target"]:
        raise ValueError("carry target-state count mismatch")

    manifest = json.loads((args.output / "V12_PHASE1F_MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = args.output / item["file"]
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"manifest hash mismatch: {path.name}")
    print(json.dumps({"status": "PASS", "files": len(REQUIRED), "targets": len(outcomes), "children": len(children)}, indent=2))


if __name__ == "__main__":
    main()
