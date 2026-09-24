#!/usr/bin/env python3
"""Validate V12 Phase-1I output integrity and causal invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1I_"
EXPECTED = {
    f"{PREFIX}RUN_EPISODES.csv",
    f"{PREFIX}FEATURE_SCHEMA.csv",
    f"{PREFIX}MODEL_METRICS.csv",
    f"{PREFIX}PREDICTIONS.csv",
    f"{PREFIX}THRESHOLD_SEARCH.csv",
    f"{PREFIX}POLICY_SCORECARD.csv",
    f"{PREFIX}MECHANISM_CONTRASTS.csv",
    f"{PREFIX}GATES.csv",
    f"{PREFIX}DIAGNOSTICS.json",
    f"{PREFIX}MANIFEST.json",
}


def validate_pack(path: Path, contract: dict) -> dict:
    files = {item.name for item in path.iterdir() if item.is_file()}
    if files != EXPECTED:
        raise AssertionError(f"unexpected files: missing={EXPECTED-files}, extra={files-EXPECTED}")
    manifest = json.loads((path / f"{PREFIX}MANIFEST.json").read_text(encoding="utf-8"))
    listed = {row["name"]: row for row in manifest["files"]}
    if set(listed) != EXPECTED - {f"{PREFIX}MANIFEST.json"}:
        raise AssertionError("manifest file set mismatch")
    for name, row in listed.items():
        item = path / name
        if sha256_file(item) != row["sha256"] or item.stat().st_size != row["bytes"]:
            raise AssertionError(f"manifest mismatch: {name}")

    diagnostics = json.loads((path / f"{PREFIX}DIAGNOSTICS.json").read_text(encoding="utf-8"))
    if diagnostics["contract_version"] != contract["contract_version"]:
        raise AssertionError("contract mismatch")
    if diagnostics["post_cutoff_price_rows_parsed"] != 0:
        raise AssertionError("post-cutoff price access")
    if diagnostics["m1_prefix_sha256"] != contract["source_hashes"]["raw_m1_prefix_sha256"]:
        raise AssertionError("prefix hash mismatch")
    expected_counts = {
        "entry_children": 1409,
        "funded_fast_runs": 679,
        "after_stop_candidates": 180,
        "repeat_stop_runs": 46,
        "strict_repeat_stop_runs": 34,
    }
    for key, value in expected_counts.items():
        if diagnostics[key] != value:
            raise AssertionError(f"population mismatch: {key}")
    if diagnostics["trade_authority"] or diagnostics["sizing_authority"]:
        raise AssertionError("authority escalation")

    runs = pd.read_csv(path / f"{PREFIX}RUN_EPISODES.csv")
    if len(runs) != 679 or runs["run_id"].duplicated().any():
        raise AssertionError("run grain mismatch")
    if not (runs["prior_funded_run_known"] == 1).all():
        raise AssertionError("unknown prior run used")
    classes = runs["run_class"].value_counts().to_dict()
    if classes != {"NEUTRAL_RUN": 441, "STOP_ONLY_RUN": 181, "TAIL_JOURNEY_RUN": 57}:
        raise AssertionError("run class mismatch")

    metrics = pd.read_csv(path / f"{PREFIX}MODEL_METRICS.csv")
    if len(metrics) != 6 or metrics[["fold", "head"]].duplicated().any():
        raise AssertionError("metric grain mismatch")
    predictions = pd.read_csv(path / f"{PREFIX}PREDICTIONS.csv")
    if len(predictions) != 497 or predictions[["fold", "run_id"]].duplicated().any():
        raise AssertionError("prediction grain mismatch")
    thresholds = pd.read_csv(path / f"{PREFIX}THRESHOLD_SEARCH.csv")
    if not (thresholds.groupby("fold")["selected"].sum() == 1).all():
        raise AssertionError("threshold selection mismatch")
    scorecards = pd.read_csv(path / f"{PREFIX}POLICY_SCORECARD.csv")
    if len(scorecards) != 16:
        raise AssertionError("scorecard grain mismatch")
    contrasts = pd.read_csv(path / f"{PREFIX}MECHANISM_CONTRASTS.csv")
    if len(contrasts) < 500 or set(contrasts["cohort"]) != {"ALL_FUNDED_RUNS", "AFTER_STOP_CANDIDATES"}:
        raise AssertionError("mechanism contrast mismatch")
    gates = pd.read_csv(path / f"{PREFIX}GATES.csv")
    overall = gates.loc[gates["gate"] == "OVERALL", "passed"].astype(str).str.lower()
    if len(overall) != 1 or overall.iloc[0] != "false":
        raise AssertionError("unexpected overall gate")
    return {
        "files": len(files), "runs": len(runs), "predictions": len(predictions),
        "primary_pass": diagnostics["primary_overall_pass"], "post_cutoff_rows": 0,
    }


def compare(first: Path, second: Path) -> None:
    for name in EXPECTED:
        if sha256_file(first / name) != sha256_file(second / name):
            raise AssertionError(f"independent pack differs: {name}")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1i_contract.json")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    receipt = validate_pack(args.output, contract)
    if args.compare is not None:
        validate_pack(args.compare, contract)
        compare(args.output, args.compare)
        receipt["byte_identical_compare"] = True
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
