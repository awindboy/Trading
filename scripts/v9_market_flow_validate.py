#!/usr/bin/env python3
"""Validate a generated V9 Market Flow Atlas bundle.

Checks the strict consumed-data boundaries, required files/columns, and several
headline metrics so the next session can detect accidental drift or leakage.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import pandas as pd

REQUIRED = {
    "CONTINUOUS_H4_FLOW_STATE_LEDGER.csv": ["block","dt","known_at","flow_state","macro_state_majority","macro_agree_n"],
    "CONTINUOUS_H1_NESTED_STATE_LEDGER.csv": ["block","dt","known_at","h1_state_consensus","h1_vs_h4_relation"],
    "H1_AUCTION_INTERRUPTION_LEDGER.csv": ["block","start","resolution","outcome"],
    "MIGRATION_INTERRUPTION_LEDGER.csv": ["block","start","resolution","outcome"],
    "DIRECTIONAL_TRANSITION_BUFFER_LEDGER.csv": ["block","start","end","from_side","to_side"],
    "H4_UNRESOLVED_RESOLUTION_LEDGER.csv": ["block","start","outcome"],
    "H4_AMBIGUOUS_RESOLUTION_LEDGER.csv": ["block","start","outcome"],
    "H4_H1_MONTHLY_STATE_STRESS_PROFILE.csv": ["month","h1_realign_rate","directional_side_changes"],
}


def fail(msg: str) -> None:
    raise AssertionError(msg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()
    root = Path(args.dir)

    for fn, cols in REQUIRED.items():
        p = root / fn
        if not p.exists():
            fail(f"missing required file: {fn}")
        d = pd.read_csv(p)
        missing = [c for c in cols if c not in d.columns]
        if missing:
            fail(f"{fn} missing columns: {missing}")
        if d.empty:
            fail(f"{fn} is empty")

    h4 = pd.read_csv(root / "CONTINUOUS_H4_FLOW_STATE_LEDGER.csv", parse_dates=["known_at"])
    h1 = pd.read_csv(root / "CONTINUOUS_H1_NESTED_STATE_LEDGER.csv", parse_dates=["known_at"])

    for name, d in [("H4", h4), ("H1", h1)]:
        y25 = d[d.block == "2025H1"]
        y26 = d[d.block == "2026JF"]
        if not y25.empty and y25.known_at.max() >= pd.Timestamp("2025-07-01"):
            fail(f"{name}: 2025-07 information-known boundary leaked: {y25.known_at.max()}")
        if not y26.empty and y26.known_at.max() >= pd.Timestamp("2026-03-01"):
            fail(f"{name}: 2026-03 boundary leaked: {y26.known_at.max()}")

    cycles = pd.read_csv(root / "H1_AUCTION_INTERRUPTION_LEDGER.csv")
    intr = pd.read_csv(root / "MIGRATION_INTERRUPTION_LEDGER.csv")
    trans = pd.read_csv(root / "DIRECTIONAL_TRANSITION_BUFFER_LEDGER.csv")

    expected = {
        "h1_cycles_2025": 145,
        "h1_cycles_2026": 41,
        "h4_interruptions_2025": 66,
        "h4_interruptions_2026": 17,
        "side_changes_2025": 33,
        "side_changes_2026": 8,
    }
    got = {
        "h1_cycles_2025": int((cycles.block == "2025H1").sum()),
        "h1_cycles_2026": int((cycles.block == "2026JF").sum()),
        "h4_interruptions_2025": int((intr.block == "2025H1").sum()),
        "h4_interruptions_2026": int((intr.block == "2026JF").sum()),
        "side_changes_2025": int((trans.block == "2025H1").sum()),
        "side_changes_2026": int((trans.block == "2026JF").sum()),
    }
    for k, v in expected.items():
        if got[k] != v:
            fail(f"headline parity drift: {k}: expected {v}, got {got[k]}")

    print("PASS: required files/columns")
    print("PASS: strict consumed-data information-known boundaries")
    print("PASS: headline ledger parity")
    for k in expected:
        print(f"  {k}: {got[k]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise
