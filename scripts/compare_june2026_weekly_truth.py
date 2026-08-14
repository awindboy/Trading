"""Compare one V4 run with a June oracle causal-atlas weekly slice."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from mentor_ai_replay_v4 import (  # noqa: E402
    _same_physical_bar_event,
    _scenario_lineage_matches,
)
from mentor_replay_v4_core import parse_utc  # noqa: E402


def load_ledger(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def geometry_matches(order: dict, truth: dict, tolerance: float = 0.011) -> bool:
    return all(
        abs(float(order[field]) - float(truth[truth_field])) <= tolerance
        for field, truth_field in (
            ("entry", "entry"),
            ("stop", "stop"),
            ("target", "target"),
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (args.run_dir / "june_oracle_parity.csv")
    truth = json.loads(args.truth.read_text(encoding="utf-8-sig"))
    records = load_ledger(args.run_dir / "decision_ledger.jsonl")
    plans = [
        row for row in records
        if row.get("event") in {"SCENARIO_PLANNED", "CHALLENGER_SCENARIO_PLANNED"}
    ]
    delivery_orders = [
        row for row in records
        if row.get("event") == "DELIVERY_FVG_REPLACEMENT_ORDER_CREATED"
    ]
    ob_orders = [row for row in records if row.get("event") == "ORDER_CREATED"]
    trades = [row for row in records if row.get("event") == "TRADE_CLOSED"]
    rows: list[dict[str, Any]] = []

    for expected in truth["candidates"]:
        direction_scope = [
            row for row in plans
            if row["details"]["scenario"]["direction"] == expected["direction"]
            and row["details"]["scenario"]["scope"] == expected["scope"]
        ]
        root_matches = [
            row for row in direction_scope
            if _scenario_lineage_matches(
                row["details"]["scenario"],
                expected["rootObBarId"],
                expected["refinementPath"],
            )
        ]
        objective_matches = [
            row for row in root_matches
            if _same_physical_bar_event(
                row["details"]["scenario"]["objective"]["barId"],
                expected["objectiveBarId"],
            )
        ]
        on_time = [
            row for row in objective_matches
            if parse_utc(row["asOfUtc"]) <= parse_utc(
                expected["deliveryFvgFormedAtUtc"] or expected["filledAtUtc"]
            )
        ]
        classification = "MAP_MISS"
        detail = "direction/scope scenario was never frozen"
        if direction_scope:
            classification, detail = "ROOT_REFINEMENT_MISS", "root/child lineage differs"
        if root_matches:
            classification, detail = "OBJECTIVE_MISS", "lineage matched but objective differs"
        if objective_matches:
            classification, detail = "LATE_PLAN", "matching scenario was frozen after execution evidence"
        scenario_hashes = {
            row["details"]["scenario"]["scenarioHash"] for row in on_time
        }
        matching_orders: list[dict[str, Any]] = []
        if on_time and expected["executionModel"] == "DELIVERY_FVG_REPLACEMENT":
            classification, detail = "DELIVERY_FVG_MISS", "matching PLAN did not create the expected replacement"
            matching_orders = [
                row for row in delivery_orders
                if row["details"]["order"].get("scenarioHash") in scenario_hashes
                and row["details"]["candidate"].get("formedBarId")
                == expected["deliveryFvgBarId"]
            ]
        elif on_time:
            classification, detail = "ORDER_MISS", "matching PLAN did not create the expected OB order"
            matching_orders = [
                row for row in ob_orders
                if row["details"]["order"].get("scenarioHash") in scenario_hashes
            ]
        if matching_orders:
            geometry = [
                row for row in matching_orders
                if geometry_matches(row["details"]["order"], expected)
            ]
            if not geometry:
                classification, detail = "ORDER_GEOMETRY_MISS", "entry/SL/TP differs"
            else:
                order_hashes = {
                    row["details"]["order"].get("scenarioHash") for row in geometry
                }
                closed = [
                    row for row in trades
                    if row["details"]["trade"].get("scenarioHash") in order_hashes
                    and abs(
                        parse_utc(row["details"]["trade"]["entryAtUtc"])
                        - parse_utc(expected["filledAtUtc"])
                    ) <= 60
                ]
                if closed:
                    classification, detail = "CAUSAL_MATCH", "PLAN, execution family, geometry, and fill matched"
                else:
                    classification, detail = "FILL_OR_CLOSE_MISS", "order matched but no matching closed trade"
        rows.append({
            "truth_id": expected["truthId"],
            "target_kind": (
                "EXECUTION"
                if expected.get("executionEligibility", "SELECTED") == "SELECTED"
                else "ATLAS_BLOCKED_ACTIVE"
            ),
            "blocked_by_truth_id": expected.get("blockedByTruthId") or "",
            "execution_model": expected["executionModel"],
            "filled_at": expected["filledAtUtc"],
            "classification": classification,
            "detail": detail,
            "matching_plan_count": len(on_time),
            "matching_order_count": len(matching_orders),
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = {
        name: sum(row["classification"] == name for row in rows)
        for name in sorted({row["classification"] for row in rows})
    }
    execution_rows = [row for row in rows if row["target_kind"] == "EXECUTION"]
    execution_counts = {
        name: sum(row["classification"] == name for row in execution_rows)
        for name in sorted({row["classification"] for row in execution_rows})
    }

    atlas = truth["candidates"]
    unmatched_extra_trades = []
    for record in trades:
        trade = record["details"]["trade"]
        if any(
            trade.get("direction") == item["direction"]
            and abs(parse_utc(trade["entryAtUtc"]) - parse_utc(item["filledAtUtc"])) <= 60
            and all(
                abs(float(trade[field]) - float(item[truth_field])) <= 0.011
                for field, truth_field in (
                    ("entry", "entry"), ("stop", "stop"), ("target", "target")
                )
            )
            for item in atlas
        ):
            continue
        unmatched_extra_trades.append({
            "tradeId": trade.get("tradeId"),
            "entryAtUtc": trade.get("entryAtUtc"),
            "direction": trade.get("direction"),
        })

    passed = (
        bool(execution_rows)
        and execution_counts.get("CAUSAL_MATCH", 0) == len(execution_rows)
        and not unmatched_extra_trades
    )
    summary = {
        "weekId": truth["weekId"],
        "atlasCandidates": len(rows),
        "executionCandidates": len(execution_rows),
        "atlasCounts": counts,
        "executionCounts": execution_counts,
        "unmatchedExtraTrades": unmatched_extra_trades,
        "passed": passed,
        "boundary": truth["coverage"],
    }
    (output.parent / "june_oracle_parity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    print(output)
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
