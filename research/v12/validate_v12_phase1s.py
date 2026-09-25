"""Validate a V12 Phase-1S output pack."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


PREFIX = "V12_PHASE1S_"
EXPECTED = {
    f"{PREFIX}FEATURE_LEDGER.csv", f"{PREFIX}OUTCOMES.csv",
    f"{PREFIX}WALK_FORWARD_PREDICTIONS.csv", f"{PREFIX}MODEL_METRICS.csv",
    f"{PREFIX}POLICY_SCORECARDS.csv", f"{PREFIX}FOLD_SCORECARDS.csv",
    f"{PREFIX}SIDE_SCORECARDS.csv", f"{PREFIX}YEAR_SCORECARDS.csv",
    f"{PREFIX}LIQUIDITY_SCORECARDS.csv", f"{PREFIX}FLAGGED_COHORTS.csv",
    f"{PREFIX}GATES.csv", f"{PREFIX}FEATURE_INVENTORY.csv",
    f"{PREFIX}DATA_QUALITY.json", f"{PREFIX}SUMMARY.json",
    f"{PREFIX}RELEASE_MANIFEST.json",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    files = {path.name for path in args.output.iterdir() if path.is_file()}
    if files != EXPECTED:
        raise ValueError(f"pack mismatch missing={sorted(EXPECTED-files)} extra={sorted(files-EXPECTED)}")
    manifest = json.loads((args.output / f"{PREFIX}RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        actual = hashlib.sha256((args.output / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"manifest mismatch: {name}")
    features = pd.read_csv(args.output / f"{PREFIX}FEATURE_LEDGER.csv")
    if len(features) != 1649 or features["signal_id"].duplicated().any():
        raise ValueError("feature ledger population mismatch")
    forbidden = {"R", "stop_hit", "tail_ge2", "exit_time", "funded_units"}
    if forbidden.intersection(features.columns):
        raise ValueError("outcome field leaked into feature ledger")
    decision = pd.to_datetime(features["decision_time"])
    snapshot = pd.to_datetime(features["snapshot_last_m1_time"], errors="coerce")
    if not (snapshot.dropna() < decision.loc[snapshot.notna()]).all():
        raise ValueError("non-causal snapshot timestamp")
    predictions = pd.read_csv(args.output / f"{PREFIX}WALK_FORWARD_PREDICTIONS.csv")
    if set(predictions["fold"]) != {"F1", "F2", "F3"}:
        raise ValueError("fold mismatch")
    if set(predictions["feature_family"]) != {"WEEK_CLOCK", "WEEK_PRICE", "WEEK_PRICE_EVENT", "WEEK_PRICE_EVENT_HISTORY"}:
        raise ValueError("feature family mismatch")
    if not predictions["p_stop"].between(0, 1).all() or not predictions["p_tail_ge2"].between(0, 1).all():
        raise ValueError("probability range violation")
    if set(predictions["weekly_liquidity_band"].dropna()) != {"LOW", "MID", "HIGH"}:
        raise ValueError("weekly liquidity bands mismatch")
    summary = json.loads((args.output / f"{PREFIX}SUMMARY.json").read_text(encoding="utf-8"))
    if summary["trade_authority"] or summary["sizing_authority"]:
        raise ValueError("authority violation")
    quality = json.loads((args.output / f"{PREFIX}DATA_QUALITY.json").read_text(encoding="utf-8"))
    if quality["feature_rows"] != 1649 or quality["strictly_prior_snapshot_rows"] + quality["blank_snapshot_rows"] != 1649:
        raise ValueError("snapshot audit mismatch")
    print(f"validated {args.output} ({len(files)} files)")


if __name__ == "__main__":
    main()
