#!/usr/bin/env python3
"""Validate V12 Phase-1P intermediate-clock output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1P_"
EXPECTED_PASSES = {
    ("H2_K1", "CONTINUOUS_CLOCK_HISTORY_HGB"), ("H2_K1", "EVENT_HISTORY_HGB"),
    ("H2_K1", "HA_HISTORY_HGB"), ("H2_K1", "STATIC_TIME_HISTORY_HGB"),
    ("M30_K1", "CONTINUOUS_CLOCK_HISTORY_HGB"), ("M30_K1", "HA_HISTORY_HGB"),
    ("M30_K1", "MICRO_HISTORY_HGB"), ("M30_K1", "SESSION_PATH_HISTORY_HGB"),
    ("M30_K1", "STATIC_TIME_HISTORY_HGB"), ("M30_K1", "WAVE_HISTORY_HGB"),
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
    if summary["candidate_counts"] != {"H2_K1": 4246, "M30_K1": 17012}:
        raise ValueError("candidate count mismatch")
    if summary["cohort_counts"] != {"H2_K1": 1309, "M30_K1": 4820}:
        raise ValueError("cohort count mismatch")
    if summary["prefix_sha256"] != "04e074ca77f449f02ac65a0b11f8efcb06254272be1a99b7273db8876ec4c939":
        raise ValueError("prefix mismatch")
    gates = pd.read_csv(args.output / f"{PREFIX}GATES.csv")
    passing = set(map(tuple, gates.loc[gates["all_primary_gates_pass"], ["population", "model"]].to_numpy()))
    if passing != EXPECTED_PASSES:
        raise ValueError(f"passing set mismatch: {passing}")
    stability = pd.read_csv(args.output / f"{PREFIX}POSTHOC_STABILITY.csv")
    if (stability.loc[stability["dimension"].isin(["YEAR", "LIQUIDITY_TERCILE"]), "policy_net_R"] <= 0).any():
        raise ValueError("year/liquidity stability drift")
    if summary["trade_authority"] or summary["sizing_authority"]:
        raise ValueError("authority boundary violated")
    print(f"validated {args.output} ({len(manifest)} files)")


if __name__ == "__main__":
    main()
