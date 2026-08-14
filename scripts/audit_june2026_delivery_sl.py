"""Decompose the structural stop used by strict June delivery candidates."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from build_june2026_oracle_atlas import load_joined  # noqa: E402
from mentor_replay_v4_core import MarketData, parse_utc  # noqa: E402

RUN = ROOT / "output/mentor_june2026_causal_benchmark"


def main() -> int:
    rates, _ = load_joined(
        ROOT / "output/datasets/GOLD_M1_2023-12-01_2025-12-31.npz",
        ROOT / "output/datasets/GOLD_M1_2026-01-01_2026-08-12.npz",
    )
    market = MarketData.from_rates(rates, 0.01)
    scenarios = {}
    for path in RUN.glob("formal_scenario_index_v2_pretouch.part*.json"):
        for scenario in json.loads(path.read_text(encoding="utf-8")):
            key = (
                scenario["root"]["obBarId"], scenario["finalChild"]["obBarId"],
                scenario["objective"]["barId"], scenario["direction"], scenario["scope"],
            )
            scenarios[key] = scenario

    with (RUN / "strict_delivery_replacement_candidates.csv").open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        as_of = parse_utc(row["fvgFormedAtUtc"])
        direction = row["direction"]
        causal = market.bar(row["causalObBarId"], as_of)
        protected = market.bar(row["protectedSwingBarId"], as_of)
        formed = market.bar(row["fvgBarId"], as_of)
        scenario = scenarios[(
            row["rootObBarId"], row["finalChildObBarId"], row["objectiveBarId"],
            direction, row["scope"],
        )]
        child = scenario["finalChild"]
        components = {
            "CAUSAL_OB": causal["low"] if direction == "LONG" else causal["high"],
            "PROTECTED_SWING": protected["low"] if direction == "LONG" else protected["high"],
            "ORIGINAL_CHILD": float(child["distal"]),
        }
        structural = min(components.values()) if direction == "LONG" else max(components.values())
        driver = next(key for key, value in components.items() if abs(value - structural) < 1e-7)
        delivery_boundary = (
            min(components["CAUSAL_OB"], components["PROTECTED_SWING"])
            if direction == "LONG" else
            max(components["CAUSAL_OB"], components["PROTECTED_SWING"])
        )
        buffer = max(0.01, float(formed["spreadPoints"]) * 0.01)
        alternative_stop = (
            delivery_boundary - buffer if direction == "LONG" else delivery_boundary + buffer
        )
        entry, stop, target = float(row["entry"]), float(row["stop"]), float(row["target"])
        fill_time = parse_utc(row["firstRetestAtUtc"])
        left = int(np.searchsorted(rates["time"], fill_time, side="left"))
        right = int(np.searchsorted(rates["time"], parse_utc(row["closedAtUtc"]), side="right"))
        alternative_outcome = "OPEN"
        alternative_closed_at = ""
        alternative_ambiguous = False
        path_extreme = entry
        path_extreme_time = 0
        target_time = 0
        for raw in rates[left:right]:
            spread = float(raw["spread"]) * market.point
            if direction == "LONG":
                adverse = float(raw["low"])
                stop_hit = float(raw["low"]) <= alternative_stop
                target_hit = float(raw["high"]) >= target
                if adverse < path_extreme:
                    path_extreme, path_extreme_time = adverse, int(raw["time"]) + 60
            else:
                adverse = float(raw["high"]) + spread
                stop_hit = float(raw["high"]) + spread >= alternative_stop
                target_hit = float(raw["low"]) + spread <= target
                if adverse > path_extreme:
                    path_extreme, path_extreme_time = adverse, int(raw["time"]) + 60
            if target_hit:
                target_time = int(raw["time"]) + 60
            if not stop_hit and not target_hit:
                continue
            alternative_ambiguous = stop_hit and target_hit
            alternative_outcome = "SL" if stop_hit else "TP"
            alternative_closed_at = int(raw["time"]) + 60
            break
        alternative_r = (
            -1.0 if alternative_outcome == "SL" else
            abs(target - entry) / abs(entry - alternative_stop)
            if alternative_outcome == "TP" else 0.0
        )
        # Counterfactual survival geometry must continue past the tighter SL
        # and inspect the complete path until the original frozen TP.
        path_extreme = entry
        path_extreme_time = 0
        target_time = 0
        for raw in rates[left:right]:
            spread = float(raw["spread"]) * market.point
            if direction == "LONG":
                adverse = float(raw["low"])
                target_hit = float(raw["high"]) >= target
                if adverse < path_extreme:
                    path_extreme, path_extreme_time = adverse, int(raw["time"]) + 60
            else:
                adverse = float(raw["high"]) + spread
                target_hit = float(raw["low"]) + spread <= target
                if adverse > path_extreme:
                    path_extreme, path_extreme_time = adverse, int(raw["time"]) + 60
            if target_hit:
                target_time = int(raw["time"]) + 60
                break
        survival_stop = (
            path_extreme - market.point if direction == "LONG"
            else path_extreme + market.point
        )
        extra_room = (
            alternative_stop - survival_stop if direction == "LONG"
            else survival_stop - alternative_stop
        )
        survival_r = abs(target - entry) / abs(entry - survival_stop)
        row.update({
            "causalObBoundary": components["CAUSAL_OB"],
            "protectedSwingBoundary": components["PROTECTED_SWING"],
            "originalChildDistal": components["ORIGINAL_CHILD"],
            "slDriver": driver,
            "structuralBoundary": structural,
            "buffer": buffer,
            "riskDistance": abs(entry - stop),
            "rewardDistance": abs(target - entry),
            "currentR": abs(target - entry) / abs(entry - stop),
            "deliveryOnlyStop": alternative_stop,
            "deliveryOnlyR": abs(target - entry) / abs(entry - alternative_stop),
            "deliveryOnlyOutcome": alternative_outcome,
            "deliveryOnlyResultR": alternative_r,
            "deliveryOnlyClosedAtEpoch": alternative_closed_at,
            "deliveryOnlyIntrabarAmbiguous": alternative_ambiguous,
            "maxAdverseBidAsk": path_extreme,
            "maxAdverseAtEpoch": path_extreme_time,
            "targetAtEpoch": target_time,
            "minimumSurvivalStop": survival_stop,
            "extraRoomPoints": max(0.0, extra_room),
            "survivalR": survival_r,
        })

    output = RUN / "strict_delivery_replacement_sl_audit.csv"
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({
        "candidates": len(rows),
        "slDrivers": dict(Counter(row["slDriver"] for row in rows)),
        "currentTotalR": sum(float(row["currentR"]) for row in rows),
        "deliveryOnlyOutcomeCounts": dict(Counter(row["deliveryOnlyOutcome"] for row in rows)),
        "deliveryOnlyActualTotalR": sum(float(row["deliveryOnlyResultR"]) for row in rows),
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
