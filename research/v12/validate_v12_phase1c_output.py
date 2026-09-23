"""Validate a complete V12 Phase-1C output pack."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from v12_phase1c_core import CONTRACT_VERSION


PREFIX = "V12_PHASE1C_"
EXPECTED = {
    PREFIX + "CARRY_DECISIONS.csv",
    PREFIX + "CARRY_OUTCOMES.csv",
    PREFIX + "REPAIR_DECISIONS.csv",
    PREFIX + "REPAIR_OUTCOMES.csv",
    PREFIX + "PORTFOLIO_SCORECARD.csv",
    PREFIX + "DIAGNOSTICS.json",
    PREFIX + "MANIFEST.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-prefix-sha256", required=True)
    args = parser.parse_args()
    present = {path.name for path in args.output.iterdir() if path.is_file()}
    if present != EXPECTED:
        raise ValueError(f"unexpected output files: missing={EXPECTED-present}, extra={present-EXPECTED}")

    manifest_path = args.output / (PREFIX + "MANIFEST.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["contract_version"] != CONTRACT_VERSION:
        raise ValueError("manifest contract mismatch")
    for item in manifest["files"]:
        path = args.output / item["file"]
        if sha256(path) != item["sha256"]:
            raise ValueError(f"hash mismatch: {path.name}")
        if item["rows"] is not None and len(rows(path)) != item["rows"]:
            raise ValueError(f"row mismatch: {path.name}")

    diagnostics = json.loads((args.output / (PREFIX + "DIAGNOSTICS.json")).read_text(encoding="utf-8"))
    if diagnostics["contract_version"] != CONTRACT_VERSION:
        raise ValueError("diagnostics contract mismatch")
    if diagnostics["post_cutoff_price_rows_parsed"] != 0:
        raise ValueError("post-cutoff price rows were parsed")
    if diagnostics["source"]["m1_prefix_audit"]["prefix_sha256"] != args.expected_prefix_sha256:
        raise ValueError("prefix hash mismatch")
    baseline = diagnostics["baseline_invariants"]
    if int(baseline["children"]) != 1649 or float(baseline["funded_units"]) != 3881.0:
        raise ValueError("V10 population invariant mismatch")
    if abs(float(baseline["net_R"]) - 741.0108654450728) > 1e-9:
        raise ValueError("V10 R invariant mismatch")
    if float(baseline["stopped_units"]) != 486.0:
        raise ValueError("V10 stopped-unit invariant mismatch")

    carry_decisions = rows(args.output / (PREFIX + "CARRY_DECISIONS.csv"))
    carry_outcomes = rows(args.output / (PREFIX + "CARRY_OUTCOMES.csv"))
    repair_decisions = rows(args.output / (PREFIX + "REPAIR_DECISIONS.csv"))
    repair_outcomes = rows(args.output / (PREFIX + "REPAIR_OUTCOMES.csv"))
    if {row["carry_id"] for row in carry_decisions} != {row["carry_id"] for row in carry_outcomes}:
        raise ValueError("carry decision/outcome keys differ")
    if not {row["repair_id"] for row in repair_outcomes}.issubset({row["repair_id"] for row in repair_decisions}):
        raise ValueError("repair outcome lacks decision")
    if any(row["outcome_fields_present"] != "False" for row in carry_decisions + repair_decisions):
        raise ValueError("decision record contains outcome marker")
    if any(row["outcome_fields_present"] != "True" for row in carry_outcomes + repair_outcomes):
        raise ValueError("outcome record marker mismatch")
    counts = diagnostics["counts"]
    if int(counts["carry_eligible_children"]) != len(carry_decisions):
        raise ValueError("carry count mismatch")
    if int(counts["unique_bridge_episodes"]) != len(repair_decisions):
        raise ValueError("bridge count mismatch")

    print(json.dumps({
        "status": "PASS",
        "contract_version": CONTRACT_VERSION,
        "carry_children": len(carry_decisions),
        "bridge_episodes": len(repair_decisions),
        "repair_children": len(repair_outcomes),
        "post_cutoff_price_rows_parsed": 0,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
