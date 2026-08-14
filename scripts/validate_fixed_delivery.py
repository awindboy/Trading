#!/usr/bin/env python3
"""Validate one weekly positive-atlas Delivery FVG case without future leakage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mentor_replay_v4_core import (
    MarketData,
    advance_shadow_delivery_candidate,
    detect_pre_touch_delivery_candidate,
    parse_utc,
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_truth(payload: dict[str, Any], truth_id: str) -> dict[str, Any]:
    candidates = payload.get("executionCandidates", [])
    for candidate in candidates:
        if candidate.get("truthId") == truth_id:
            return candidate
    raise ValueError(f"truth candidate not found: {truth_id}")


def close_enough(actual: float, expected: float, point: float) -> bool:
    return abs(float(actual) - float(expected)) <= max(point, 1e-9) + 1e-9


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--warmup-start", required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--truth-id", required=True)
    parser.add_argument("--point", type=float, default=0.01)
    parser.add_argument("--broker-stops-level", type=float, default=0.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    truth = select_truth(read_json(args.truth), args.truth_id)
    state = read_json(args.state)
    scenario = state.get("scenario")
    if not isinstance(scenario, dict):
        result = {
            "truthId": args.truth_id,
            "classification": "PLAN_MISS",
            "checks": {},
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result))
        return 2

    formed_at = parse_utc(truth["deliveryFvgFormedAtUtc"])
    close_at = parse_utc(truth["closedAtUtc"])
    market = MarketData.from_npz(
        args.dataset.resolve(),
        parse_utc(args.warmup_start),
        close_at + 60,
        args.point,
    )
    formed_row = market.bar(truth["deliveryFvgBarId"], formed_at)
    formed_index = int(formed_row["index"])
    if int(formed_row["available"]) != formed_at:
        raise ValueError("truth FVG bar does not close at deliveryFvgFormedAtUtc")

    candidate = detect_pre_touch_delivery_candidate(
        market, scenario, formed_row, args.broker_stops_level
    )
    checks: dict[str, bool] = {
        "direction": scenario.get("direction") == truth["direction"],
        "scope": scenario.get("scope") == truth["scope"],
        "root": scenario.get("root", {}).get("obBarId") == truth["rootObBarId"],
        "finalChild": scenario.get("finalChild", {}).get("obBarId")
        == truth["finalChildObBarId"],
        "objective": scenario.get("objective", {}).get("barId")
        == truth["objectiveBarId"],
        "candidateFound": candidate is not None,
    }
    lifecycle: list[dict[str, Any]] = []
    if candidate is not None:
        checks.update(
            {
                "deliveryFvg": candidate["formedBarId"] == truth["deliveryFvgBarId"],
                "eligible": candidate["status"] == "WAIT_FIRST_RETEST",
                "entry": close_enough(candidate["entry"], truth["entry"], args.point),
                "stop": close_enough(candidate["stop"], truth["stop"], args.point),
                "target": close_enough(candidate["target"], truth["target"], args.point),
            }
        )
        current = candidate
        close_index = market.m1_index_at_or_after(close_at) - 1
        for index in range(formed_index + 1, close_index + 1):
            current, event = advance_shadow_delivery_candidate(
                market, current, market.m1_row(index)
            )
            if event:
                lifecycle.append(
                    {
                        "event": event,
                        "atUtc": current.get("filledAtUtc") or current.get("closedAtUtc"),
                    }
                )
            if current["status"] in {
                "TP", "SL", "OBJECTIVE_FIRST", "INVALIDATED", "THROUGH_DELIVERY"
            }:
                break
        checks["filledAt"] = current.get("filledAtUtc") == truth["filledAtUtc"]
        checks["closedAt"] = current.get("closedAtUtc") == truth["closedAtUtc"]
        checks["outcome"] = current.get("status") == truth["outcome"]
        checks["resultR"] = abs(
            float(current.get("resultR", 0.0)) - float(truth["resultR"])
        ) <= 1e-9

    classification = "EXACT" if checks and all(checks.values()) else "MISMATCH"
    result = {
        "truthId": args.truth_id,
        "classification": classification,
        "checks": checks,
        "candidate": candidate,
        "lifecycle": lifecycle,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"truthId": args.truth_id, "classification": classification, "checks": checks}))
    return 0 if classification == "EXACT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
