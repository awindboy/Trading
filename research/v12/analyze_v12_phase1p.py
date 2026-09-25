#!/usr/bin/env python3
"""Post-hoc side/year/streak stability audit for passing Phase-1P models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from v12_phase0_core import sha256_file
from v12_phase1o_core import policy_metrics


PREFIX = "V12_PHASE1P_"
TEST_START = pd.Timestamp("2025-04-01")
TEST_END = pd.Timestamp("2026-09-18 23:57:00")


def max_stop_streak(frame: pd.DataFrame) -> int:
    best = current = 0
    for stopped in frame.sort_values(["decision_time", "signal_id"])["stop_hit"].astype(int):
        current = current + 1 if stopped else 0
        best = max(best, current)
    return best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    gates = pd.read_csv(args.output / f"{PREFIX}GATES.csv")
    passing = gates.loc[gates["all_primary_gates_pass"], ["population", "model"]]
    predictions = pd.read_csv(args.output / f"{PREFIX}AFTER_STOP_TEST_PREDICTIONS.csv")
    rows = []
    for population, population_models in passing.groupby("population"):
        ledger = pd.read_csv(
            args.output / f"{PREFIX}{population}_ENRICHED_LEDGER.csv",
            usecols=["signal_id", "decision_time", "direction", "R", "stop_hit", "prior60_daily_range_median"],
            parse_dates=["decision_time"],
        )
        ledger = ledger.loc[ledger["decision_time"].between(TEST_START, TEST_END)].copy()
        ledger["year"] = ledger["decision_time"].dt.year
        liquidity_cuts = np.quantile(ledger["prior60_daily_range_median"].dropna(), [1 / 3, 2 / 3])
        ledger["liquidity_tercile"] = np.searchsorted(liquidity_cuts, ledger["prior60_daily_range_median"], side="right") + 1
        for model in population_models["model"]:
            local_predictions = predictions.loc[(predictions["population"] == population) &
                                                 (predictions["model"] == model)]
            excluded = set(local_predictions.loc[local_predictions["excluded_high_repeat_risk"] == 1, "signal_id"])
            for dimension in ("direction", "year", "liquidity_tercile"):
                for level, cell in ledger.groupby(dimension):
                    policy = cell.loc[~cell["signal_id"].isin(excluded)]
                    baseline_summary = policy_metrics(cell)
                    policy_summary = policy_metrics(policy)
                    rows.append({
                        "population": population, "model": model, "dimension": dimension.upper(), "level": level,
                        **{f"baseline_{key}": value for key, value in baseline_summary.items()},
                        **{f"policy_{key}": value for key, value in policy_summary.items()},
                        "baseline_max_stop_streak": max_stop_streak(cell),
                        "policy_max_stop_streak": max_stop_streak(policy),
                        "child_retention": len(policy) / len(cell),
                        "tail_R_retention": policy_summary["tail_ge5_R"] / baseline_summary["tail_ge5_R"]
                        if baseline_summary["tail_ge5_R"] else np.nan,
                    })
            baseline_summary = policy_metrics(ledger)
            policy = ledger.loc[~ledger["signal_id"].isin(excluded)]
            policy_summary = policy_metrics(policy)
            rows.append({
                "population": population, "model": model, "dimension": "POOLED", "level": "ALL",
                **{f"baseline_{key}": value for key, value in baseline_summary.items()},
                **{f"policy_{key}": value for key, value in policy_summary.items()},
                "baseline_max_stop_streak": max_stop_streak(ledger),
                "policy_max_stop_streak": max_stop_streak(policy),
                "child_retention": len(policy) / len(ledger),
                "tail_R_retention": policy_summary["tail_ge5_R"] / baseline_summary["tail_ge5_R"],
            })
    result = pd.DataFrame(rows)
    path = args.output / f"{PREFIX}POSTHOC_STABILITY.csv"
    result.to_csv(path, index=False, lineterminator="\n")
    receipt = pd.DataFrame([{
        "file": path.name, "rows": len(result), "sha256": sha256_file(path),
        "status": "POSTHOC_CONSUMED_DEVELOPMENT_DIAGNOSTIC_ONLY",
    }])
    receipt.to_csv(args.output / f"{PREFIX}POSTHOC_RECEIPT.csv", index=False, lineterminator="\n")
    manifest = {
        item.name: sha256_file(item)
        for item in sorted(args.output.glob(f"{PREFIX}*"))
        if item.name != f"{PREFIX}RELEASE_MANIFEST.json"
    }
    (args.output / f"{PREFIX}RELEASE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
