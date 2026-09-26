"""Validate a retained Phase-1V entry-episode output pack."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


PREFIX = "V12_PHASE1V_"
EXPECTED_STATES = {
    "FAST_ONLY_CHALLENGE", "FAST_WITH_MEMORY", "SLOW_ONLY_CONFLICT",
    "STD_LEADS_TRANSFER", "TRANSFER_CONFIRMED",
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
        "--pack", type=Path,
        default=repo / "output/v12_phase1v_entry_episode_accounting_20260926_b",
    )
    args = parser.parse_args()

    manifest = json.loads((args.pack / f"{PREFIX}MANIFEST.json").read_text(encoding="utf-8"))
    for receipt in manifest["outputs"]:
        path = args.pack / receipt["name"]
        require(path.is_file(), f"missing output: {receipt['name']}")
        require(path.stat().st_size == receipt["bytes"], f"size mismatch: {path.name}")
        require(sha256_file(path) == receipt["sha256"], f"hash mismatch: {path.name}")

    quality = json.loads((args.pack / f"{PREFIX}DATA_QUALITY.json").read_text(encoding="utf-8"))
    summary = json.loads((args.pack / f"{PREFIX}SUMMARY.json").read_text(encoding="utf-8"))
    episodes = pd.read_csv(args.pack / f"{PREFIX}ENTRY_EPISODES.csv")
    cards = pd.read_csv(args.pack / f"{PREFIX}POLICY_SCORECARDS.csv").set_index("policy")
    states = pd.read_csv(args.pack / f"{PREFIX}STATE_SCORECARDS.csv")
    roles = pd.read_csv(args.pack / f"{PREFIX}OUTCOME_ROLE_SCORECARDS.csv")
    gates = pd.read_csv(args.pack / f"{PREFIX}GATES.csv").set_index("gate")

    require(quality["source_run_rows"] == 679, "source run count changed")
    require(quality["source_baseline_child_rows"] == 1409, "source Child count changed")
    require(quality["common_episode_rows"] == 679, "common episode count changed")
    require(quality["common_first_child_rows"] == 679, "first Child coverage changed")
    require(quality["common_later_child_rows"] == 730, "later Child coverage changed")
    for field in (
        "run_child_left_only", "run_child_right_only", "run_child_count_mismatches",
        "duplicate_common_run_ids", "duplicate_first_child_signal_ids", "missing_first_child",
        "missing_ownership_state", "first_signal_id_mismatches",
        "first_entry_decision_mismatches", "direction_mismatches",
        "post_common_window_raw_market_rows_parsed",
    ):
        require(quality[field] == 0, f"quality failure: {field}")
    require(quality["episode_decomposition_max_R_error"] < 1e-10, "R decomposition mismatch")
    require(quality["episode_decomposition_max_stop_error"] < 1e-10, "stop decomposition mismatch")
    require(len(episodes) == 679 and not episodes["run_id"].duplicated().any(),
            "episode ledger identity changed")
    require(set(episodes["ownership_state"].unique()) == EXPECTED_STATES,
            "ownership state inventory changed")

    control = cards.loc["V10_ENTRY_EPISODE_CONTROL"]
    primary = cards.loc["ENTRY_OWNERSHIP_AUTHORIZED"]
    expected_control = {
        "episodes": 679,
        "first_child_hard_sl_episodes": 145,
        "repeat_first_child_stop_episodes": 28,
        "max_first_stop_streak": 3,
        "repeat_negative_episodes": 345,
        "max_negative_episode_streak": 17,
        "positive_episodes": 197,
        "negative_episodes": 482,
        "tail_episodes": 57,
        "non_tail_count_balance": -342,
    }
    for field, expected in expected_control.items():
        require(int(control[field]) == expected, f"control {field} changed")
    expected_primary = {
        "episodes": 420,
        "first_child_hard_sl_episodes": 80,
        "repeat_first_child_stop_episodes": 12,
        "max_first_stop_streak": 3,
        "repeat_negative_episodes": 202,
        "max_negative_episode_streak": 12,
        "positive_episodes": 127,
        "negative_episodes": 293,
        "tail_episodes": 41,
        "non_tail_count_balance": -207,
    }
    for field, expected in expected_primary.items():
        require(int(primary[field]) == expected, f"primary {field} changed")
    require((states["non_tail_count_slope"] < 0).all(), "a state unexpectedly has positive ordinary slope")

    start_roles = roles.loc[roles["grouping"].eq("START_OUTCOME_ROLE")].set_index("role")
    require(int(start_roles.loc["FIRST_STOP_EPISODE_NEGATIVE", "episodes"]) == 144,
            "first-stop negative count changed")
    require(int(start_roles.loc["FIRST_STOP_EPISODE_RECOVERED_POSITIVE", "episodes"]) == 1,
            "first-stop recovery count changed")
    require(int(start_roles.loc["NO_FIRST_STOP_EPISODE_NEGATIVE", "episodes"]) == 338,
            "non-first-stop negative count changed")
    management = roles.loc[roles["grouping"].eq("MANAGEMENT_ROLE")].set_index("role")
    require(int(management.loc["POSITIVE_FIRST_CHILD_LATE_DAMAGE", "episodes"]) == 48,
            "late-damage episode count changed")

    require(summary["status"] == "PRIMARY_FAILED_CONSUMED_GATE", "failure status changed")
    require(summary["primary_gates_passed"] == 6, "passed-gate count changed")
    require(not bool(gates.loc["positive_episode_retention", "passed"]),
            "positive retention unexpectedly passed")
    require(not bool(gates.loc["tail_episode_retention", "passed"]),
            "tail retention unexpectedly passed")
    require(not bool(gates.loc["non_tail_count_curve_positive", "passed"]),
            "ordinary curve unexpectedly became positive")
    require(not summary["action_authority"] and summary["consumed_development_only"],
            "authority boundary changed")

    print(json.dumps({
        "status": "PASS_ARTIFACT_INTEGRITY_PRIMARY_FAILED",
        "pack": str(args.pack.resolve()),
        "manifest_members_verified": len(manifest["outputs"]),
        "episodes": len(episodes),
        "first_stops_saved": 65,
        "positive_episodes_lost": 70,
        "tail_episodes_lost": 16,
        "ordinary_count_curve_positive": False,
        "action_authority": False,
    }, indent=2))


if __name__ == "__main__":
    main()
