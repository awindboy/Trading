from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable

from .models import OrderPlan, Scenario


def _timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp())


def validate_q1_regression(
    orders: Iterable[OrderPlan],
    scenarios: Iterable[Scenario],
    fixture_path: str | Path,
) -> dict[str, Any]:
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    order_list = list(orders)
    scenario_by_id = {item.scenario_id: item for item in scenarios}
    window = int(fixture.get("matchingWindowMinutes", 5)) * 60
    positive_window = int(fixture.get("mentorConsistentWindowMinutes", 45)) * 60
    checks: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []

    for case in fixture.get("cases", []):
        decision_at = _timestamp(case["decisionAtUtc"])
        case_window = (
            positive_window
            if case["expected"] == "MENTOR_CONSISTENT"
            else window
        )
        matches = [
            order
            for order in order_list
            if order.direction.value == case["direction"]
            and abs(order.created_at - decision_at) <= case_window
        ]
        check = {
            "caseId": case["id"],
            "expected": case["expected"],
            "decisionAtUtc": case["decisionAtUtc"],
            "matchedOrderIds": [item.order_id for item in matches],
        }
        checks.append(check)
        if case["expected"] == "NO_TRADE" and matches:
            violations.append(
                {
                    **check,
                    "reason": "A manually rejected as-of setup reappeared as an order.",
                }
            )
        if case["expected"] == "MENTOR_CONSISTENT" and not matches:
            violations.append(
                {
                    **check,
                    "reason": "A manually confirmed as-of setup disappeared from the engine.",
                }
            )
        if case["expected"] == "MENTOR_CONSISTENT" and matches:
            geometry_matches = [
                order
                for order in matches
                if case["entryRange"][0] <= order.entry <= case["entryRange"][1]
                and case["stopRange"][0]
                <= order.stop_loss
                <= case["stopRange"][1]
                and case["takeProfitRange"][0]
                <= order.take_profit
                <= case["takeProfitRange"][1]
            ]
            check["geometryMatchedOrderIds"] = [
                item.order_id for item in geometry_matches
            ]
            if not geometry_matches:
                violations.append(
                    {
                        **check,
                        "reason": "The setup survived, but its entry, SL, or TP no longer matches the as-of scenario.",
                    }
                )

    lineage_violations: list[dict[str, Any]] = []
    for order in order_list:
        scenario = scenario_by_id[order.scenario_id]
        missing = []
        if not scenario.plan_id:
            missing.append("plan_id")
        if scenario.planned_at is None or scenario.planned_at >= scenario.created_at:
            missing.append("plan_before_sweep")
        if not scenario.map_structure_event_id:
            missing.append("map_structure_event_id")
        if not scenario.objective_id:
            missing.append("objective_id")
        if not scenario.source_pool_id or not scenario.source_zone_ids:
            missing.append("source_lineage")
        if not scenario.trigger_event_id or not scenario.entry_zone_id:
            missing.append("trigger_lineage")
        if missing:
            lineage_violations.append(
                {"orderId": order.order_id, "missing": missing}
            )

    violations.extend(lineage_violations)
    return {
        "schema": "mentor-q1-regression-result-v1",
        "passed": not violations,
        "checks": checks,
        "lineageViolations": lineage_violations,
        "violations": violations,
    }
