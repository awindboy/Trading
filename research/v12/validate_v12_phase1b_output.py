#!/usr/bin/env python3
"""Validate one deterministic V12 Phase-1B output pack."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path

from v12_phase0_core import sha256_file
from v12_phase1b_core import CONTRACT_VERSION


PREFIX = "V12_PHASE1B_"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def unique(rows: list[dict], key: str, label: str, allow_blank: bool = False) -> None:
    values = [row[key] for row in rows if row[key] or not allow_blank]
    require(len(values) == len(set(values)), f"duplicate {label} {key}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-prefix-sha256", required=True)
    args = parser.parse_args()
    root = args.output

    diagnostics = json.loads((root / f"{PREFIX}DIAGNOSTICS.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / f"{PREFIX}MANIFEST.json").read_text(encoding="utf-8"))
    require(diagnostics["contract_version"] == CONTRACT_VERSION, "contract mismatch")
    require(diagnostics["post_cutoff_price_rows_parsed"] == 0, "post-cutoff rows parsed")
    for key in ("prefix_audit_first_pass", "prefix_audit_outcome_pass"):
        require(diagnostics["source"][key]["prefix_sha256"] == args.expected_prefix_sha256, f"{key} hash mismatch")
        require(diagnostics["source"][key]["post_cutoff_price_rows_parsed"] == 0, f"{key} contaminated")

    for item in manifest["files"]:
        path = root / item["file"]
        require(path.exists(), f"missing manifest file {path.name}")
        require(path.stat().st_size == item["bytes"], f"size mismatch {path.name}")
        require(sha256_file(path) == item["sha256"], f"hash mismatch {path.name}")

    level_d = read_csv(root / f"{PREFIX}KEY_LEVEL_DECISIONS.csv")
    level_o = read_csv(root / f"{PREFIX}KEY_LEVEL_OUTCOMES.csv")
    h4_d = read_csv(root / f"{PREFIX}H4_CRT_DECISIONS.csv")
    journey_d = read_csv(root / f"{PREFIX}JOURNEY_DECISIONS.csv")
    journey_o = read_csv(root / f"{PREFIX}JOURNEY_OUTCOMES.csv")
    v10_d = read_csv(root / f"{PREFIX}V10_CHILD_DECISION_CONTEXT.csv")
    v10_o = read_csv(root / f"{PREFIX}V10_CHILD_OUTCOME_LINK.csv")
    nha_d = read_csv(root / f"{PREFIX}NHA_DECISION_CONTEXT.csv")
    nha_o = read_csv(root / f"{PREFIX}NHA_OUTCOME_LINK.csv")

    unique(level_d, "level_id", "level decision")
    unique(level_o, "level_id", "level outcome")
    require({row["level_id"] for row in level_d} == {row["level_id"] for row in level_o}, "level ID sets differ")
    unique(h4_d, "h4_event_id", "H4 decision")
    unique(journey_o, "journey_id", "journey outcome")
    unique(v10_d, "signal_id", "V10 decision")
    unique(v10_o, "signal_id", "V10 outcome")
    require({row["signal_id"] for row in v10_d} == {row["signal_id"] for row in v10_o}, "V10 ID sets differ")
    unique(nha_d, "flip_id", "NHA decision")
    unique(nha_o, "flip_id", "NHA outcome")
    require({row["flip_id"] for row in nha_d} == {row["flip_id"] for row in nha_o}, "NHA ID sets differ")

    require(len(v10_d) == 1649, "selected V10 child count changed")
    require(abs(sum(float(row["combined_R_units"]) for row in v10_o) - 741.0108654450728) < 1e-9, "V10 R changed")
    require(abs(sum(float(row["funded_units"]) for row in v10_o) - 3881.0) < 1e-9, "V10 funded units changed")
    require(abs(sum(float(row["stopped_loss_units"]) for row in v10_o) - 486.0) < 1e-9, "V10 stopped units changed")

    require(all(row["outcome_fields_present"] == "False" for row in level_d + h4_d + journey_d + v10_d + nha_d), "outcome marker in decision file")
    require(all(row["outcome_fields_present"] == "True" for row in level_o + journey_o + v10_o + nha_o), "decision marker in outcome file")
    forbidden = {
        "R", "stop_hit", "combined_R_units", "stopped_loss_units", "funded_units",
        "full_3unit_stop", "right_tail_ge_5R_units", "end_reason", "end_price",
        "midpoint_time", "opposite_edge_time", "new_fast_run_h4_bars", "linked_v10_k1_R",
    }
    for name, rows in (("H4", h4_d), ("journey", journey_d), ("V10", v10_d), ("NHA", nha_d)):
        if rows:
            overlap = forbidden.intersection(rows[0])
            require(not overlap, f"future fields in {name} decisions: {sorted(overlap)}")

    cutoff = datetime.fromisoformat(diagnostics["causal_cutoff"])
    for row in h4_d:
        require(datetime.fromisoformat(row["c2_completed_by"]) <= cutoff, "post-cutoff H4 decision")
        if row["activation_time"]:
            require(datetime.fromisoformat(row["activation_time"]) <= cutoff, "post-cutoff activation")
    for row in v10_d:
        require(datetime.fromisoformat(row["decision_time"]) <= cutoff, "post-cutoff V10 overlay")
        require(
            datetime.fromisoformat(row["level_coordinate_known_at"])
            <= datetime.fromisoformat(row["decision_time"]),
            "future V10 level coordinate",
        )
    for row in nha_d:
        require(datetime.fromisoformat(row["known_at"]) <= cutoff, "post-cutoff NHA overlay")

    counts = diagnostics["counts"]
    require(len(level_d) == counts["levels"], "level count mismatch")
    require(len(h4_d) == counts["h4_pair_decisions"], "H4 count mismatch")
    require(len(journey_d) == counts["journey_state_decisions"], "journey decision count mismatch")
    require(len(journey_o) == counts["journeys"], "journey outcome count mismatch")
    require(len(nha_d) == counts["fast_flips"], "NHA count mismatch")
    require(len([row for row in journey_d if row["state_action"] == "START"]) == len(journey_o), "start/outcome mismatch")

    print(json.dumps({
        "status": "PASS",
        "contract_version": CONTRACT_VERSION,
        "levels": len(level_d),
        "h4_decisions": len(h4_d),
        "journeys": len(journey_o),
        "v10_children": len(v10_d),
        "fast_flips": len(nha_d),
    }, indent=2))


if __name__ == "__main__":
    main()
