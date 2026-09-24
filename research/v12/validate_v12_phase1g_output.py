#!/usr/bin/env python3
"""Validate a complete V12 Phase-1G output pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file


REQUIRED = {
    "V12_PHASE1G_SOURCE_BOXES.csv",
    "V12_PHASE1G_V10_CHILD_PATH_CONTEXT.csv",
    "V12_PHASE1G_NHA_PATH_CONTEXT.csv",
    "V12_PHASE1G_BRIDGE_PATH_CONTEXT.csv",
    "V12_PHASE1G_REPAIR_PATH_CONTEXT.csv",
    "V12_PHASE1G_MODEL_METRICS.csv",
    "V12_PHASE1G_PREDICTIONS.csv",
    "V12_PHASE1G_QUINTILE_CAPITAL.csv",
    "V12_PHASE1G_JOINT_SCORE_CAPITAL.csv",
    "V12_PHASE1G_CONVICTION_SCORE_CAPITAL.csv",
    "V12_PHASE1G_MECHANISM_ABLATION_METRICS.csv",
    "V12_PHASE1G_RUN_LENGTH_MODEL_METRICS.csv",
    "V12_PHASE1G_DIAGNOSTICS.json",
    "V12_PHASE1G_MANIFEST.json",
}


def validate_context(path: Path, expected: int) -> None:
    frame = pd.read_csv(path, low_memory=False)
    if len(frame) != expected:
        raise ValueError(f"row mismatch {path.name}: {len(frame)} != {expected}")
    query = pd.to_datetime(frame["query_time"])
    for prefix in ("asia", "lonny", "london", "ny"):
        available = frame[f"{prefix}_available"] == 1
        ends = pd.to_datetime(frame.loc[available, f"{prefix}_end"])
        if (ends > query.loc[available]).any():
            raise ValueError(f"future source box in {path.name}: {prefix}")
        for edge in ("high", "low"):
            values = pd.to_datetime(frame.loc[available, f"{prefix}_first_{edge}_break_time"], errors="coerce")
            valid = values.notna()
            if (values.loc[valid] >= query.loc[available].loc[valid]).any():
                raise ValueError(f"same/future M1 break in {path.name}: {prefix} {edge}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    observed = {path.name for path in args.output.iterdir() if path.is_file()}
    if observed != REQUIRED:
        raise ValueError(f"file set mismatch missing={REQUIRED-observed} extra={observed-REQUIRED}")
    diagnostics = json.loads((args.output / "V12_PHASE1G_DIAGNOSTICS.json").read_text(encoding="utf-8"))
    expected = {
        "m1_prefix_rows": 1669073,
        "source_boxes": 4868,
        "v10_context_rows": 1649,
        "v10_entry_model_rows": 1409,
        "nha_context_rows": 2234,
        "nha_linked_k1_model_rows": 2101,
        "bridge_context_rows": 60,
        "repair_context_rows": 31,
        "model_metric_rows": 36,
        "mechanism_ablation_metric_rows": 54,
        "run_length_metric_rows": 12,
    }
    for key, value in expected.items():
        if diagnostics[key] != value:
            raise ValueError(f"diagnostic mismatch {key}: {diagnostics[key]} != {value}")
    if diagnostics["post_cutoff_price_rows_parsed"] != 0:
        raise ValueError("post-cutoff price row parsed")
    if diagnostics["trade_authority"] or diagnostics["sizing_authority"]:
        raise ValueError("unauthorized action flag")
    validate_context(args.output / "V12_PHASE1G_V10_CHILD_PATH_CONTEXT.csv", 1649)
    validate_context(args.output / "V12_PHASE1G_NHA_PATH_CONTEXT.csv", 2234)
    validate_context(args.output / "V12_PHASE1G_BRIDGE_PATH_CONTEXT.csv", 60)
    validate_context(args.output / "V12_PHASE1G_REPAIR_PATH_CONTEXT.csv", 31)
    metrics = pd.read_csv(args.output / "V12_PHASE1G_MODEL_METRICS.csv")
    if set(metrics["fold"]) != {"F1", "F2", "F3"} or metrics.isna().any().any():
        raise ValueError("primary model metrics incomplete")
    if set(metrics["model"]) != {
        "STRUCTURE_ONLY", "STRUCTURE_PLUS_STATIC_BUCKETS", "STRUCTURE_PLUS_CONTINUOUS_TIME",
        "STRUCTURE_PLUS_CONTINUOUS_PATH",
    }:
        raise ValueError("primary model set mismatch")
    manifest = json.loads((args.output / "V12_PHASE1G_MANIFEST.json").read_text(encoding="utf-8"))
    if len(manifest["files"]) != len(REQUIRED) - 1:
        raise ValueError("manifest file count mismatch")
    for item in manifest["files"]:
        path = args.output / item["name"]
        if sha256_file(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise ValueError(f"manifest mismatch: {path.name}")
    print(json.dumps({"status": "PASS", "files": len(REQUIRED), **expected}, indent=2))


if __name__ == "__main__":
    main()
