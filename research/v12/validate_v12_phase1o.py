#!/usr/bin/env python3
"""Validate a complete V12 Phase-1O output pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1O_"
EXPECTED_MODELS = {
    "HISTORY_ONLY_RIDGE", "HISTORY_ONLY_HGB", "HA_HISTORY_HGB", "STATIC_TIME_HISTORY_HGB",
    "CONTINUOUS_CLOCK_HISTORY_HGB", "EVENT_HISTORY_HGB", "SESSION_PATH_HISTORY_HGB",
    "MICRO_HISTORY_HGB", "WAVE_HISTORY_HGB", "FULL_SEQUENCE_HGB",
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
    if summary["cohort_counts"] != {"H1_K1": 2586, "M15_K1": 9657}:
        raise ValueError("cohort count mismatch")
    if summary["passing_models"] or summary["trade_authority"] or summary["sizing_authority"]:
        raise ValueError("authority/gate boundary mismatch")
    metrics = pd.read_csv(args.output / f"{PREFIX}WALK_FORWARD_METRICS.csv")
    if set(metrics["model"]) != EXPECTED_MODELS or set(metrics["population"]) != {"H1_K1", "M15_K1"}:
        raise ValueError("model/population mismatch")
    if set(metrics["outcome"]) != {"REPEAT_HARD_SL", "RIGHT_TAIL_R_GE_5"} or set(metrics["fold"]) != {"F1", "F2", "F3"}:
        raise ValueError("outcome/fold mismatch")
    predictions = pd.read_csv(args.output / f"{PREFIX}AFTER_STOP_TEST_PREDICTIONS.csv")
    if predictions.duplicated(["population", "model", "signal_id"]).any():
        raise ValueError("duplicate predictions")
    gates = pd.read_csv(args.output / f"{PREFIX}GATES.csv")
    if gates["all_primary_gates_pass"].any():
        raise ValueError("unexpected primary gate pass")
    h1 = gates.loc[(gates["population"] == "H1_K1") & gates["model"].str.endswith("_HGB")]
    if not (h1.loc[~h1["model"].eq("HISTORY_ONLY_HGB"), "gate_repeat_logloss"].all()):
        raise ValueError("H1 temporal repeat-stop result drift")
    print(f"validated {args.output} ({len(manifest)} files)")


if __name__ == "__main__":
    main()
