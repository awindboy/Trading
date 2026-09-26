"""Validate a retained Phase-1U diagnostic output pack."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


PREFIX = "V12_PHASE1U_"
EXPECTED_CONTROL = {
    "children": 1649,
    "hard_sl_children": 232,
    "positive_children": 635,
    "positive_ge3r": 58,
    "positive_ge5r": 16,
    "max_stop_streak": 5,
    "funded_units": 3881,
    "stopped_units": 486,
}
EXPECTED_STATES = {
    "FAST_WITH_MEMORY",
    "FAST_ONLY_CHALLENGE",
    "STD_LEADS_TRANSFER",
    "SLOW_ONLY_CONFLICT",
    "TRANSFER_CONFIRMED",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pack",
        type=Path,
        default=repo / "output/v12_phase1u_multispeed_ha_ownership_20260926_b",
    )
    args = parser.parse_args()

    manifest_path = args.pack / f"{PREFIX}MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(not manifest["action_authority"], "action authority must remain false")
    for receipt in manifest["outputs"]:
        path = args.pack / receipt["name"]
        require(path.is_file(), f"missing output: {receipt['name']}")
        require(path.stat().st_size == receipt["bytes"], f"size mismatch: {path.name}")
        require(sha256_file(path) == receipt["sha256"], f"hash mismatch: {path.name}")

    quality = json.loads((args.pack / f"{PREFIX}DATA_QUALITY.json").read_text(encoding="utf-8"))
    summary = json.loads((args.pack / f"{PREFIX}SUMMARY.json").read_text(encoding="utf-8"))
    ledger = pd.read_csv(args.pack / f"{PREFIX}CHILD_LEDGER.csv")
    states = pd.read_csv(args.pack / f"{PREFIX}STATE_SCORECARDS.csv")
    transitions = pd.read_csv(args.pack / f"{PREFIX}K1_TRANSITION_SCORECARDS.csv")
    cards = pd.read_csv(args.pack / f"{PREFIX}POLICY_SCORECARDS.csv").set_index("policy")
    gates = pd.read_csv(args.pack / f"{PREFIX}GATES.csv").set_index("gate")

    require(quality["raw_m1"]["m1_rows"] == 1648545, "raw M1 row count changed")
    require(quality["h4_state_rows"] == 7199, "H4 state row count changed")
    require(quality["universe_rows"] == 6770, "V10 universe row count changed")
    require(quality["economic_universe_rows"] == 2839, "economic window changed")
    require(quality["joined_rows"] == 2839, "MT5 join coverage changed")
    require(quality["universe_only_rows"] == 0 and quality["mt5_only_rows"] == 0,
            "MT5 join is not exact")
    require(quality["selected_children"] == 1649, "selected Child population changed")
    require(quality["universe_h4_state_missing"] == 0, "missing H4 ownership state")
    require(quality["universe_fast_direction_mismatches"] == 0, "FAST direction mismatch")
    require(quality["universe_fast_k_mismatches"] == 0, "FAST k mismatch")
    require(quality["selected_duplicate_signal_ids"] == 0, "duplicate selected signal")
    require(quality["post_cutoff_price_rows_parsed"] == 0, "post-cutoff row parsed")

    require(len(ledger) == 1649, "Child ledger coverage changed")
    require(not ledger["signal_id"].duplicated().any(), "duplicate Child ledger signal")
    require(set(ledger["ownership_state"].unique()) == EXPECTED_STATES,
            "ownership-state inventory changed")
    require(not transitions["transition_signature"].eq("INITIAL").any(),
            "economic k1 population unexpectedly contains warmup rows")
    require(set(states.loc[states["population"].eq("MT5_SELECTED"), "ownership_state"].unique())
            == EXPECTED_STATES, "selected scorecard state inventory changed")

    for field, expected in EXPECTED_CONTROL.items():
        require(int(cards.loc["V10_CONTROL", field]) == expected, f"control {field} changed")
    primary = cards.loc["OWNERSHIP_AUTHORIZED"]
    require(int(primary["hard_sl_children"]) == 158, "primary stop count changed")
    require(int(primary["positive_children"]) == 528, "primary positive count changed")
    require(int(primary["positive_ge5r"]) == 9, "primary tail count changed")
    require(int(primary["max_stop_streak"]) == 4, "primary streak changed")
    require(summary["status"] == "PRIMARY_FAILED_CONSUMED_GATE", "failure status changed")
    require(summary["primary_gates_passed"] == 5, "passed-gate count changed")
    require(not bool(gates.loc["positive_child_retention", "passed"]),
            "positive-retention gate unexpectedly passed")
    require(not bool(gates.loc["ge5r_child_retention", "passed"]),
            "tail-retention gate unexpectedly passed")
    require(not summary["action_authority"] and summary["consumed_development_only"],
            "authority boundary changed")

    print(json.dumps({
        "status": "PASS_ARTIFACT_INTEGRITY_PRIMARY_FAILED",
        "pack": str(args.pack.resolve()),
        "manifest_members_verified": len(manifest["outputs"]),
        "children": len(ledger),
        "hard_sl_saved": 74,
        "positive_children_lost": 107,
        "primary_pass": False,
        "action_authority": False,
    }, indent=2))


if __name__ == "__main__":
    main()
