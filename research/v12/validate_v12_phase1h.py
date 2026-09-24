#!/usr/bin/env python3
"""Validate V12 Phase-1H output integrity and causal-contract invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1H_"
EXPECTED = {
    f"{PREFIX}FEATURE_SCHEMA.csv",
    f"{PREFIX}MODEL_METRICS.csv",
    f"{PREFIX}PREDICTIONS.csv",
    f"{PREFIX}CAPITAL_BANDS.csv",
    f"{PREFIX}SHADOW_TILT.csv",
    f"{PREFIX}STABILITY.csv",
    f"{PREFIX}GATES.csv",
    f"{PREFIX}DIAGNOSTICS.json",
    f"{PREFIX}MANIFEST.json",
}


def validate_pack(path: Path, contract: dict) -> dict:
    observed = {item.name for item in path.iterdir() if item.is_file()}
    if observed != EXPECTED:
        raise AssertionError(f"unexpected file set: missing={EXPECTED-observed}, extra={observed-EXPECTED}")
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
        raise AssertionError("contract version mismatch")
    if diagnostics["post_cutoff_price_rows_parsed"] != 0:
        raise AssertionError("post-cutoff price row parsed")
    if diagnostics["m1_prefix_sha256"] != contract["source_hashes"]["raw_m1_prefix_sha256"]:
        raise AssertionError("prefix hash mismatch")
    if diagnostics["source"]["entry_children"] != 1409 or diagnostics["source"]["wave_missing_rows"] != 0:
        raise AssertionError("source population mismatch")
    if diagnostics["trade_authority"] or diagnostics["sizing_authority"]:
        raise AssertionError("authority escalation")
    if diagnostics["feature_source_counts"]["COMPACT_PATH"] > contract["maximum_primary_source_fields"]:
        raise AssertionError("primary source field cap breached")

    metrics = pd.read_csv(path / f"{PREFIX}MODEL_METRICS.csv")
    if len(metrics) != 36 or metrics[["model", "outcome", "fold"]].duplicated().any():
        raise AssertionError("model metric grain mismatch")
    predictions = pd.read_csv(path / f"{PREFIX}PREDICTIONS.csv")
    if len(predictions) != 6264 or predictions[["model", "fold", "signal_id"]].duplicated().any():
        raise AssertionError("prediction grain mismatch")
    if set(predictions["band_threshold_source"]) != {"TRAIN_PREDICTION_ECDF"}:
        raise AssertionError("test-derived band detected")
    times = pd.to_datetime(predictions["decision_time"])
    fold_bounds = {
        "F1": (pd.Timestamp("2025-04-01"), pd.Timestamp("2025-09-30 23:59:59")),
        "F2": (pd.Timestamp("2025-10-01"), pd.Timestamp("2026-03-31 23:59:59")),
        "F3": (pd.Timestamp("2026-04-01"), pd.Timestamp("2026-09-18 23:57:00")),
    }
    for fold, (start, end) in fold_bounds.items():
        values = times.loc[predictions["fold"] == fold]
        if not ((values >= start) & (values <= end)).all():
            raise AssertionError(f"fold time leakage: {fold}")

    gates = pd.read_csv(path / f"{PREFIX}GATES.csv")
    overall = gates.loc[gates["gate"] == "OVERALL"]
    if len(overall) != 4 or overall["passed"].astype(str).str.lower().eq("true").any():
        raise AssertionError("unexpected overall gate state")
    return {
        "files": len(observed),
        "metrics": len(metrics),
        "predictions": len(predictions),
        "primary_pass": diagnostics["primary_overall_pass"],
        "post_cutoff_rows": diagnostics["post_cutoff_price_rows_parsed"],
    }


def compare_packs(first: Path, second: Path) -> None:
    for name in sorted(EXPECTED):
        if sha256_file(first / name) != sha256_file(second / name):
            raise AssertionError(f"independent pack differs: {name}")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1h_contract.json")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    receipt = validate_pack(args.output, contract)
    if args.compare is not None:
        validate_pack(args.compare, contract)
        compare_packs(args.output, args.compare)
        receipt["byte_identical_compare"] = True
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
