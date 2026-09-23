#!/usr/bin/env python3
"""Validate the complete V12 Phase-1A output pack and key score invariants."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from v12_phase0_core import sha256_file
from v12_phase1a_core import CONTRACT_VERSION, score_outcomes, stable_child_id


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def numeric(value: str | None) -> float | None:
    return float(value) if value not in (None, "") else None


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    require(abs(actual - expected) <= tolerance, f"{label}: {actual} != {expected}")


def validate_pack(output: Path) -> dict:
    manifest = read_json(output / "V12_PHASE1A_MANIFEST.json")
    require(manifest["contract_version"] == CONTRACT_VERSION, "contract version mismatch")
    require(manifest["post_cutoff_price_rows_parsed"] == 0, "holdout prices were parsed")
    require(manifest["trade_authority"] is False, "Phase 1A cannot have trade authority")
    require(manifest["independent_validation"] is False, "consumed evidence mislabeled independent")
    for name, expected in manifest["files"].items():
        path = output / name
        require(path.is_file(), f"manifest output missing: {name}")
        require(path.stat().st_size == expected["bytes"], f"byte mismatch: {name}")
        require(sha256_file(path) == expected["sha256"], f"sha mismatch: {name}")

    decisions = read_csv(output / "V12_PHASE1A_CHILD_DECISIONS.csv")
    outcomes = read_csv(output / "V12_PHASE1A_CHILD_OUTCOMES.csv")
    dispositions = read_csv(output / "V12_PHASE1A_PARENT_DISPOSITIONS.csv")
    require(len(dispositions) == manifest["parent_records"] == 1459, "parent count mismatch")
    require(len(decisions) == manifest["child_decisions"], "decision count mismatch")
    require(len(outcomes) == manifest["outcome_records"], "outcome count mismatch")
    decision_ids = [row["child_id"] for row in decisions]
    outcome_ids = [row["child_id"] for row in outcomes]
    require(len(decision_ids) == len(set(decision_ids)), "duplicate child decision ID")
    require(len(outcome_ids) == len(set(outcome_ids)), "duplicate child outcome ID")
    require(set(decision_ids) == set(outcome_ids), "decision/outcome child ID sets differ")
    require(all(row["outcome_fields_present"] == "False" for row in decisions), "decision contains outcome marker")
    require(all(row["outcome_fields_present"] == "True" for row in outcomes), "outcome marker missing")

    for row in decisions:
        expected_id = stable_child_id(row["parent_id"], row["family"], row["risk_variant"])
        require(row["child_id"] == expected_id, f"unstable child ID: {row['child_id']}")
        require(datetime.fromisoformat(row["watch_start"]) <= datetime.fromisoformat(row["decision_time"]), "watch after decision")
        require(datetime.fromisoformat(row["decision_time"]) < datetime.fromisoformat(row["expiry_time"]), "decision at/after expiry")

    outcome_by_id = {row["child_id"]: row for row in outcomes}
    for decision in decisions:
        row = outcome_by_id[decision["child_id"]]
        if row["execution_state"] == "FILLED":
            entry = datetime.fromisoformat(row["entry_time"])
            require(entry >= datetime.fromisoformat(row["decision_time"]), "entry precedes decision")
            require(entry < datetime.fromisoformat(row["expiry_time"]), "entry at/after expiry")
            require(numeric(row["risk_distance"]) is not None and float(row["risk_distance"]) > 0, "non-positive risk")
            require(row["no_execution_reason"] == "", "filled child has no-execution reason")
            for target in (1, 2):
                state = row[f"t{target}_state"]
                require(state in {f"TARGET{target}", "STOPPED", "STOPPED_GAP", "EXPIRED", "AMBIGUOUS"}, "bad terminal state")
                if state == "AMBIGUOUS":
                    require(row[f"t{target}_r"] == "", "ambiguous outcome has R")
                else:
                    require(row[f"t{target}_r"] != "", "resolved outcome missing R")
        else:
            require(row["entry_time"] == "", "no-execution child has entry")
            require(row["t1_r"] == "" and row["t2_r"] == "", "no-execution child has R")
            require(bool(row["no_execution_reason"]), "no-execution reason missing")

    scorecard = read_csv(output / "V12_PHASE1A_SCORECARD.csv")
    for family, risk_variant in sorted(set((row["family"], row["risk_variant"]) for row in outcomes)):
        variant = [row for row in outcomes if row["family"] == family and row["risk_variant"] == risk_variant]
        expected = score_outcomes(
            [
                {
                    **row,
                    "t1_r": numeric(row["t1_r"]),
                    "t2_r": numeric(row["t2_r"]),
                }
                for row in variant
            ],
            1,
        )
        recorded = next(
            row for row in scorecard
            if row["scope"] == "FULL_CONSUMED"
            and row["family"] == family
            and row["risk_variant"] == risk_variant
            and row["target"] == "T1"
            and row["slice_type"] == "OVERALL"
        )
        for field in ("decisions", "filled_children", "stops", "targets", "expiries"):
            require(int(recorded[field]) == expected[field], f"scorecard count mismatch: {family}/{risk_variant}/{field}")
        for field in ("net_r", "gross_profit_r", "gross_loss_r", "max_drawdown_r"):
            assert_close(float(recorded[field]), float(expected[field]), f"scorecard {field}")

    comparison = read_csv(output / "V12_PHASE1A_V10_COMPARISON.csv")
    v10_one = next(row for row in comparison if row["strategy"] == "V10_SELECTED_CHILDREN_1U")
    v10_weighted = next(row for row in comparison if row["strategy"] == "V10_R7G_HISTORICAL_FUNDED_UNITS")
    require(int(v10_one["children"]) == 1649, "V10 selected-child count drift")
    assert_close(float(v10_one["net_r"]), 284.367480716489, "V10 one-unit net")
    assert_close(float(v10_weighted["funded_units"]), 3881.0, "V10 funded units")
    assert_close(float(v10_weighted["net_r"]), 741.010865445073, "V10 R7G net")

    detail = read_csv(output / "V12_PHASE1A_COUNTERFACTUAL_DETAIL.csv")
    summary = read_csv(output / "V12_PHASE1A_COUNTERFACTUAL_SUMMARY.csv")
    require(len(detail) > 0 and len(summary) == 4, "counterfactual audit incomplete")
    require({row["effect"] for row in summary} == {"CONFIRMATION_EFFECT", "STOP_REFERENCE_EFFECT"}, "counterfactual effect missing")

    return {
        "status": "PASS",
        "output": str(output),
        "parent_records": len(dispositions),
        "child_decisions": len(decisions),
        "filled_children": sum(row["execution_state"] == "FILLED" for row in outcomes),
        "all_manifest_hashes_verified": True,
        "decision_outcome_separation_verified": True,
        "scorecard_recomputed": True,
        "v10_comparator_invariants_verified": True,
        "counterfactual_audit_present": True,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=repo_root / "output" / "v12_phase1a_no_ml_baseline_20260923",
    )
    args = parser.parse_args()
    print(json.dumps(validate_pack(args.output), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
