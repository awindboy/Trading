#!/usr/bin/env python3
"""Aggregate independent PLAN and Delivery-FVG parity for one weekly atlas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--packets-root", type=Path, required=True)
    parser.add_argument("--packet-prefix", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    truth = read_json(args.truth)
    rows: list[dict[str, Any]] = []
    for candidate in truth.get("executionCandidates", []):
        truth_id = str(candidate["truthId"])
        matches = sorted(args.packets_root.glob(f"{args.packet_prefix}{truth_id}_*"))
        packet_dir = matches[-1] if matches else None
        plan = (
            read_json(packet_dir / "plan_parity.json")
            if packet_dir and (packet_dir / "plan_parity.json").exists()
            else None
        )
        delivery = (
            read_json(packet_dir / "delivery_parity.json")
            if packet_dir and (packet_dir / "delivery_parity.json").exists()
            else None
        )
        rows.append(
            {
                "truthId": truth_id,
                "packetDir": str(packet_dir) if packet_dir else None,
                "plan": plan.get("classification") if plan else "MISSING",
                "planChecks": plan.get("checks", {}) if plan else {},
                "delivery": delivery.get("classification") if delivery else "MISSING",
                "deliveryChecks": delivery.get("checks", {}) if delivery else {},
                "passed": bool(
                    plan
                    and plan.get("classification") == "MAP_CAUSAL_MATCH"
                    and delivery
                    and delivery.get("classification") == "EXACT"
                ),
            }
        )

    passed = sum(1 for row in rows if row["passed"])
    result = {
        "weekId": truth.get("weekId"),
        "coverage": truth.get("coverage"),
        "positiveCases": len(rows),
        "passed": passed,
        "positiveAtlasGate": passed == len(rows) and bool(rows),
        "negativeAuditRequired": True,
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    report = args.output.with_suffix(".md")
    lines = [
        f"# {truth.get('weekId')} Positive Atlas Validation",
        "",
        f"- Positive cases: `{len(rows)}`",
        f"- Passed: `{passed}`",
        f"- Positive-atlas gate: `{'PASS' if result['positiveAtlasGate'] else 'FAIL'}`",
        "- Negative/unmatched trades: `NOT ENUMERATED BY THIS ATLAS`",
        "",
        "| Truth | PLAN | Delivery geometry/lifecycle | Result |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['truthId']} | {row['plan']} | {row['delivery']} | "
            f"{'PASS' if row['passed'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "This gate proves that every labeled positive case can be independently",
            "reconstructed without injecting its objective, child, FVG, or order prices.",
            "It does not prove that every unmatched closed-loop trade is invalid.",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"weekId": result["weekId"], "passed": passed, "total": len(rows)}))
    print(args.output)
    return 0 if result["positiveAtlasGate"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
