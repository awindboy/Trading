#!/usr/bin/env python3
"""Validate a complete V12 Phase-0 output pack and its provenance hashes."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_v12_event_schema import require, validate_decision
from v12_phase0_core import parent_id, sha256_file


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_pack(output: Path) -> dict:
    manifest_path = output / "V12_PHASE0_MANIFEST.json"
    quality_path = output / "V12_PHASE0_DATA_QUALITY.json"
    decision_path = output / "V12_PHASE0_DECISIONS.jsonl"
    event_path = output / "V12_PHASE0_PARENT_EVENTS.csv"
    summary_path = output / "V12_PHASE0_SUMMARY.csv"
    for path in (manifest_path, quality_path, decision_path, event_path, summary_path):
        require(path.is_file(), f"missing output file: {path}")

    manifest = read_json(manifest_path)
    quality = read_json(quality_path)
    for name, expected in manifest["files"].items():
        path = output / name
        require(path.is_file(), f"manifest file missing: {name}")
        require(path.stat().st_size == expected["bytes"], f"byte size mismatch: {name}")
        require(sha256_file(path) == expected["sha256"], f"sha256 mismatch: {name}")

    gates = quality.get("gates", {})
    require(gates and all(gates.values()), f"data-quality gate failed: {gates}")
    require(quality["contract"]["post_cutoff_price_rows_parsed"] == 0, "holdout prices were parsed")
    require(quality["contract"]["future_outcomes_joined"] is False, "future outcomes were joined")

    decisions: list[dict] = []
    with decision_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                validate_decision(record)
            except Exception as exc:  # pragma: no cover - exact failure is reported
                raise ValueError(f"invalid decision line {line_number}: {exc}") from exc
            expected_parent = parent_id(
                symbol=record["symbol"],
                lane=record["lane"],
                c1_open=datetime.fromisoformat(record["c1"]["open_time"]),
                c2_open=datetime.fromisoformat(record["c2"]["bar"]["open_time"]),
                broker_clock_spec_sha256=record["broker_clock_spec_sha256"],
                source_prefix_sha256=record["source_dataset_sha256"],
            )
            require(record["parent_id"] == expected_parent, f"parent_id mismatch on line {line_number}")
            decisions.append(record)

    decision_ids = [record["parent_id"] for record in decisions]
    require(len(decision_ids) == len(set(decision_ids)), "duplicate parent_id in decision ledger")
    require(len(decisions) == manifest["decision_records"], "decision count differs from manifest")
    require(manifest["outcome_records"] == 0, "Phase 0 must not contain outcomes")
    require(manifest["entry_authority"] is False, "Phase 0 cannot grant entry authority")
    require(manifest["performance_claim_allowed"] is False, "Phase 0 cannot claim performance")

    with event_path.open("r", encoding="utf-8", newline="") as handle:
        events = list(csv.DictReader(handle))
    event_ids = [row["parent_id"] for row in events]
    require(len(event_ids) == len(set(event_ids)), "duplicate parent_id in rich event ledger")
    require(set(event_ids) == set(decision_ids), "decision/event parent_id sets differ")
    require(all(row["outcome_fields_present"] == "False" for row in events), "rich ledger contains outcomes")

    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))
    require(sum(int(row["events"]) for row in summary_rows) == len(events), "summary event total mismatch")

    return {
        "status": "PASS",
        "output": str(output),
        "decision_records": len(decisions),
        "unique_parent_ids": len(set(decision_ids)),
        "directional_hypotheses": sum(record["hypothesis_direction"] != "NONE" for record in decisions),
        "outcome_records": 0,
        "all_manifest_hashes_verified": True,
        "all_quality_gates_passed": True,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=repo_root / "output" / "v12_phase0_event_universe_20260923",
    )
    args = parser.parse_args()
    print(json.dumps(validate_pack(args.output), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
