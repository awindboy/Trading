#!/usr/bin/env python3
"""Validate V12 Phase-1Q output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1Q_"
EXPECTED_PASSES = {
    ("M15_K1", "SESSION_PATH_HISTORY_HGB"),
    ("M15_K1", "STATIC_TIME_HISTORY_HGB"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.output / f"{PREFIX}RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        path = args.output / name
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"manifest mismatch: {name}")
    summary = json.loads((args.output / f"{PREFIX}SUMMARY.json").read_text(encoding="utf-8"))
    if summary["cohort_counts"] != {"H2_K1": 357, "H1_K1": 686, "M30_K1": 1249, "M15_K1": 2285}:
        raise ValueError("cohort count mismatch")
    gates = pd.read_csv(args.output / f"{PREFIX}GATES.csv")
    passing = set(map(tuple, gates.loc[gates["all_primary_gates_pass"], ["population", "model"]].to_numpy()))
    if passing != EXPECTED_PASSES:
        raise ValueError(f"passing set mismatch: {passing}")
    policies = pd.read_csv(args.output / f"{PREFIX}POLICY_SCORECARDS.csv")
    pooled = policies.loc[(policies["fold"] == "POOLED") & policies.set_index(["population", "model"]).index.isin(EXPECTED_PASSES)]
    if not (pooled["policy_max_stop_streak"] < pooled["baseline_max_stop_streak"]).all():
        raise ValueError("maximum-streak result drift")
    if summary["trade_authority"] or summary["sizing_authority"]:
        raise ValueError("authority boundary violated")
    print(f"validated {args.output} ({len(manifest)} files)")


if __name__ == "__main__":
    main()
