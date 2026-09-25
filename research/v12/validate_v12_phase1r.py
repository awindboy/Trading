"""Validate a V12 Phase-1R output pack."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


PREFIX = "V12_PHASE1R_"
EXPECTED = {
    f"{PREFIX}M30_CAUSAL_PREDICTIONS.csv",
    f"{PREFIX}NORMALIZED_COMPARISON.csv",
    f"{PREFIX}SCORECARDS.csv",
    f"{PREFIX}SUMMARY.json",
    f"{PREFIX}YEAR_SCORECARDS.csv",
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

    predictions = pd.read_csv(args.output / f"{PREFIX}M30_CAUSAL_PREDICTIONS.csv")
    predictions["decision_time"] = pd.to_datetime(predictions["decision_time"])
    predictions["label_available_at"] = pd.to_datetime(predictions["label_available_at"])
    if set(predictions["fold"]) != {"Y2023", "Y2024", "Y2025", "Y2026"}:
        raise ValueError("walk-forward folds mismatch")
    if predictions["decision_time"].min() < pd.Timestamp("2023-01-01"):
        raise ValueError("warmup was backfilled")
    if predictions["decision_time"].max() > pd.Timestamp("2026-09-18 23:57"):
        raise ValueError("post-cutoff prediction")
    if not predictions["train_top_risk_threshold"].between(0, 1).all():
        raise ValueError("invalid threshold")

    scores = pd.read_csv(args.output / f"{PREFIX}SCORECARDS.csv")
    required = {
        ("M30_K1_BASELINE", "FULL_M30_HISTORY"),
        ("M30_SESSION_PATH_CAUSAL", "FULL_M30_HISTORY"),
        ("M30_K1_BASELINE", "MATCHED_V10_WINDOW"),
        ("M30_SESSION_PATH_CAUSAL", "MATCHED_V10_WINDOW"),
        ("V10_R7G_ACTUAL_UNITS", "MATCHED_V10_WINDOW"),
    }
    if set(zip(scores["strategy"], scores["scope"])) != required:
        raise ValueError("scorecard population mismatch")

    summary = json.loads((args.output / f"{PREFIX}SUMMARY.json").read_text(encoding="utf-8"))
    if summary["m30_candidates"] != 17012 or summary["v10_children"] != 1649:
        raise ValueError("population count mismatch")
    if summary["trade_authority"] or summary["sizing_authority"]:
        raise ValueError("authority violation")
    print(f"validated {args.output} ({len(files)} files)")


if __name__ == "__main__":
    main()
