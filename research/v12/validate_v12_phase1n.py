#!/usr/bin/env python3
"""Validate a complete V12 Phase-1N output pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1N_"
EXPECTED_MODELS = {
    "HA_ONLY", "HA_PLUS_STATIC_TIME", "HA_PLUS_CONTINUOUS_CLOCK", "HA_PLUS_EVENT",
    "HA_PLUS_SESSION_PATH", "HA_PLUS_CRT_PARENT", "HA_PLUS_MICRO_PATH", "HA_PLUS_WAVE",
    "ALL_TIME_INFORMATION", "FULL_ASSEMBLY",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest_path = args.output / f"{PREFIX}RELEASE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        path = args.output / name
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"manifest mismatch: {name}")
    summary = json.loads((args.output / f"{PREFIX}SUMMARY.json").read_text(encoding="utf-8"))
    if summary["population_rows"] != {"H1_K1": 8666, "M15_K1": 34519}:
        raise ValueError("population count mismatch")
    if summary["prefix_sha256"] != "04e074ca77f449f02ac65a0b11f8efcb06254272be1a99b7273db8876ec4c939":
        raise ValueError("prefix mismatch")
    if summary["trade_authority"] or summary["sizing_authority"]:
        raise ValueError("authority boundary violated")
    metrics = pd.read_csv(args.output / f"{PREFIX}WALK_FORWARD_METRICS.csv")
    if set(metrics["model"]) != EXPECTED_MODELS or set(metrics["population"]) != {"H1_K1", "M15_K1"}:
        raise ValueError("model/population mismatch")
    if set(metrics["fold"]) != {"F1", "F2", "F3"} or set(metrics["outcome"]) != {
        "HARD_SL", "RIGHT_TAIL_R_GE_3", "RIGHT_TAIL_R_GE_5"
    }:
        raise ValueError("fold/outcome mismatch")
    predictions = pd.read_csv(args.output / f"{PREFIX}TEST_PREDICTIONS.csv", usecols=["population", "model", "signal_id"])
    if predictions.duplicated(["population", "model", "signal_id"]).any():
        raise ValueError("duplicate test predictions")
    screen = pd.read_csv(args.output / f"{PREFIX}PROMOTION_SCREEN.csv")
    passing = set(map(tuple, screen.loc[screen["promotion_screen_pass"], ["population", "model"]].to_numpy()))
    expected = {("H1_K1", "HA_PLUS_MICRO_PATH"), ("H1_K1", "HA_PLUS_STATIC_TIME"),
                ("M15_K1", "HA_PLUS_STATIC_TIME")}
    if passing != expected:
        raise ValueError(f"promotion screen mismatch: {passing}")
    print(f"validated {args.output} ({len(manifest)} files)")


if __name__ == "__main__":
    main()
