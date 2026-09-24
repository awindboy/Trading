#!/usr/bin/env python3
"""Validate one or two V12 Phase-1J result packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file
from v12_phase1j_core import CONTRACT_VERSION


REQUIRED = {
    "V12_PHASE1J_RUN_TERMINALS.csv",
    "V12_PHASE1J_M15_TIMELINE.csv",
    "V12_PHASE1J_EVENT_SNAPSHOTS.csv",
    "V12_PHASE1J_EVENT_OCCURRENCE.csv",
    "V12_PHASE1J_FEATURE_CONTRASTS.csv",
    "V12_PHASE1J_PROMOTION_SCREEN.csv",
    "V12_PHASE1J_DIAGNOSTICS.json",
}


def validate_pack(path: Path) -> dict:
    manifest_path = path / "V12_PHASE1J_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["contract_version"] != CONTRACT_VERSION:
        raise ValueError("manifest contract version mismatch")
    listed = {item["name"] for item in manifest["files"]}
    if listed != REQUIRED:
        raise ValueError(f"manifest members mismatch: {sorted(listed ^ REQUIRED)}")
    for item in manifest["files"]:
        member = path / item["name"]
        if member.stat().st_size != item["bytes"] or sha256_file(member) != item["sha256"]:
            raise ValueError(f"manifest mismatch: {member.name}")
    diagnostics = json.loads((path / "V12_PHASE1J_DIAGNOSTICS.json").read_text(encoding="utf-8"))
    terminals = pd.read_csv(path / "V12_PHASE1J_RUN_TERMINALS.csv")
    timeline = pd.read_csv(path / "V12_PHASE1J_M15_TIMELINE.csv")
    snapshots = pd.read_csv(path / "V12_PHASE1J_EVENT_SNAPSHOTS.csv")
    if terminals["run_id"].duplicated().any():
        raise ValueError("duplicate terminal run")
    if snapshots.duplicated(["run_id", "snapshot"]).any():
        raise ValueError("duplicate run snapshot")
    if not (pd.to_datetime(timeline["bar_end"]) < pd.to_datetime(timeline["terminal_time"])).all():
        raise ValueError("post-terminal M15 row")
    if diagnostics["classified_runs"] != len(terminals):
        raise ValueError("classified run count mismatch")
    if diagnostics["timeline_rows"] != len(timeline) or diagnostics["snapshot_rows"] != len(snapshots):
        raise ValueError("timeline diagnostics mismatch")
    if diagnostics["post_cutoff_price_rows_parsed"] != 0:
        raise ValueError("post-cutoff row parsed")
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    diagnostics = validate_pack(args.output)
    identical = None
    if args.compare:
        other = validate_pack(args.compare)
        if other != diagnostics:
            raise ValueError("diagnostics differ")
        names = REQUIRED | {"V12_PHASE1J_MANIFEST.json"}
        identical = all((args.output / name).read_bytes() == (args.compare / name).read_bytes() for name in names)
        if not identical:
            raise ValueError("result packs are not byte-identical")
    print(json.dumps({
        "files": len(REQUIRED) + 1,
        "classified_runs": diagnostics["classified_runs"],
        "timeline_rows": diagnostics["timeline_rows"],
        "promotion_screen_passes": diagnostics["promotion_screen_passes"],
        "post_cutoff_rows": diagnostics["post_cutoff_price_rows_parsed"],
        "byte_identical_compare": identical,
    }, indent=2))


if __name__ == "__main__":
    main()
