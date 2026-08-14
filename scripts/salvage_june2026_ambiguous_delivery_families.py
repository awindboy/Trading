"""Salvage ambiguous delivery families using only frozen AGENTS invariants."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from build_june2026_causal_benchmark import simulate_scenario  # noqa: E402
from build_june2026_oracle_atlas import load_joined, timestamp  # noqa: E402
from mentor_replay_v4_core import (  # noqa: E402
    MarketData,
    TIMEFRAME_SECONDS,
    parse_utc,
    utc_text,
)

RUN = ROOT / "output/mentor_june2026_causal_benchmark"


def lineage_tuple(scenario: dict) -> tuple[str, str, str, str]:
    return (
        scenario["scope"], scenario["root"]["obBarId"],
        scenario["finalChild"]["obBarId"], scenario["objective"]["barId"],
    )


def contained_path(scenario: dict) -> bool:
    parent = scenario["root"]
    for child in scenario["refinements"]:
        parent_tf, parent_time = parent["obBarId"].split(":", 1)
        _, child_time = child["obBarId"].split(":", 1)
        time_contained = (
            int(parent_time) <= int(child_time)
            < int(parent_time) + TIMEFRAME_SECONDS[parent_tf]
        )
        price_contained = (
            float(parent["low"]) <= float(child["low"])
            and float(child["high"]) <= float(parent["high"])
        )
        if not time_contained or not price_contained:
            return False
        parent = child
    return True


def main() -> int:
    rates, _ = load_joined(
        ROOT / "output/datasets/GOLD_M1_2023-12-01_2025-12-31.npz",
        ROOT / "output/datasets/GOLD_M1_2026-01-01_2026-08-12.npz",
    )
    market = MarketData.from_rates(rates, 0.01)
    scenario_lookup: dict[tuple[str, str, str, str], list[dict]] = {}
    for path in RUN.glob("formal_scenario_index_v2_pretouch.part*.json"):
        for scenario in json.loads(path.read_text(encoding="utf-8")):
            scenario_lookup.setdefault(lineage_tuple(scenario), []).append(scenario)

    families = json.loads(
        (RUN / "strict_delivery_replacement_ambiguous_families.json").read_text(encoding="utf-8")
    )
    salvaged: list[dict] = []
    unresolved: list[dict] = []
    entry_end = timestamp("2026-07-01T00:00:00Z")
    follow_end = timestamp("2026-07-15T00:00:00Z")
    for number, family in enumerate(families, 1):
        family_id = f"J26-AMB-{number:03d}"
        candidates: list[dict] = []
        for raw_lineage in family["lineages"]:
            scenarios = scenario_lookup.get(tuple(raw_lineage), [])
            # Keep the latest pre-FVG freeze for identical semantic lineage.
            formed_time = int(family["formedBarId"].split(":", 1)[1]) + 60
            eligible = [
                item for item in scenarios
                if parse_utc(item["frozenAtUtc"]) <= formed_time
            ]
            if not eligible:
                continue
            scenario = sorted(eligible, key=lambda item: item["frozenAtUtc"])[-1]
            if contained_path(scenario):
                candidates.append(scenario)

        path_groups: dict[tuple, list[dict]] = {}
        for scenario in candidates:
            path_key = (
                scenario["root"]["obBarId"],
                tuple(item["obBarId"] for item in scenario["refinements"]),
            )
            path_groups.setdefault(path_key, []).append(scenario)
        if not path_groups:
            unresolved.append({
                "familyId": family_id, "direction": family["direction"],
                "fvgBarId": family["formedBarId"], "firstRetestAtUtc": family["filledAtUtc"],
                "reason": "NO_FULLY_CONTAINED_CAUSAL_LINEAGE",
                "remainingPathCount": 0,
            })
            continue
        if len(path_groups) > 1:
            unresolved.append({
                "familyId": family_id, "direction": family["direction"],
                "fvgBarId": family["formedBarId"], "firstRetestAtUtc": family["filledAtUtc"],
                "reason": "MULTIPLE_FULLY_CONTAINED_CAUSAL_LINEAGES",
                "remainingPathCount": len(path_groups),
            })
            continue

        variants = next(iter(path_groups.values()))
        direction = family["direction"]
        formed_index = market.m1_index_at_or_after(int(family["formedBarId"].split(":", 1)[1]))
        formed_row = market.m1_row(formed_index)
        entry = float(formed_row["low"] if direction == "LONG" else formed_row["high"])

        external = [item for item in variants if item["scope"] == "EXTERNAL_CONTINUATION"]
        if external:
            directional = [
                item for item in external
                if (
                    float(item["objective"]["price"]) > entry
                    if direction == "LONG" else
                    float(item["objective"]["price"]) < entry
                )
            ]
            if not directional:
                unresolved.append({
                    "familyId": family_id, "direction": direction,
                    "fvgBarId": family["formedBarId"], "firstRetestAtUtc": family["filledAtUtc"],
                    "reason": "NO_DIRECTIONAL_EXTERNAL_OBJECTIVE",
                    "remainingPathCount": 1,
                })
                continue
            chosen = min(
                directional,
                key=lambda item: abs(float(item["objective"]["price"]) - entry),
            )
            resolution = (
                "UNIQUE_CONTAINED_LINEAGE" if len(variants) == 1 else
                "SAME_DIRECTION_EXTERNAL_OWNER_INTERNAL_LIQUIDITY_IS_INTERMEDIATE"
            )
        else:
            internal = [item for item in variants if item["scope"] == "INTERNAL_ROTATION"]
            if len(internal) != 1:
                unresolved.append({
                    "familyId": family_id, "direction": direction,
                    "fvgBarId": family["formedBarId"], "firstRetestAtUtc": family["filledAtUtc"],
                    "reason": "NON_UNIQUE_INTERNAL_OBJECTIVE",
                    "remainingPathCount": 1,
                })
                continue
            chosen = internal[0]
            resolution = "UNIQUE_CONTAINED_LINEAGE"

        root_tf = chosen["root"]["obBarId"].split(":", 1)[0]
        protected_tf = chosen["mapProtectedSwing"]["barId"].split(":", 1)[0]
        if chosen["scope"] == "EXTERNAL_CONTINUATION" and (
            root_tf not in {"H1", "M30"} or protected_tf not in {"H1", "M30"}
        ):
            unresolved.append({
                "familyId": family_id, "direction": direction,
                "fvgBarId": family["formedBarId"], "firstRetestAtUtc": family["filledAtUtc"],
                "reason": "EXTERNAL_OWNER_NOT_BACKED_BY_H1_M30",
                "remainingPathCount": 1,
            })
            continue

        intermediate = sorted({
            item["objective"]["barId"]
            for item in variants
            if item["scope"] == "INTERNAL_ROTATION"
        })

        # Selection is complete before this simulation. The result is appended
        # only after causal lineage and objective ambiguity have been resolved.
        result = simulate_scenario(market, chosen, entry_end, follow_end)
        replacement = result.get("replacement") or {}
        if (
            replacement.get("formedBarId") != family["formedBarId"]
            or replacement.get("filledAtUtc") != family["filledAtUtc"]
            or replacement.get("status") not in {"TP", "SL"}
        ):
            unresolved.append({
                "familyId": family_id, "direction": direction,
                "fvgBarId": family["formedBarId"], "firstRetestAtUtc": family["filledAtUtc"],
                "reason": "SELECTED_LINEAGE_DOES_NOT_REPRODUCE_PHYSICAL_TRADE",
                "remainingPathCount": 1,
            })
            continue

        salvaged.append({
            "salvageId": f"J26-SALV-{len(salvaged) + 1:03d}",
            "sourceFamilyId": family_id,
            "direction": direction,
            "scope": chosen["scope"],
            "frozenAtUtc": chosen["frozenAtUtc"],
            "fvgBarId": family["formedBarId"],
            "fvgFormedAtUtc": utc_text(formed_time),
            "firstRetestAtUtc": family["filledAtUtc"],
            "rootObBarId": chosen["root"]["obBarId"],
            "refinementPath": ";".join(item["obBarId"] for item in chosen["refinements"]),
            "finalChildObBarId": chosen["finalChild"]["obBarId"],
            "objectiveBarId": chosen["objective"]["barId"],
            "objectivePrice": chosen["objective"]["price"],
            "intermediateLiquidityBarIds": ";".join(intermediate),
            "entry": replacement["entry"],
            "stop": replacement["stop"],
            "target": replacement["target"],
            "outcome": replacement["status"],
            "resultR": replacement["resultR"],
            "closedAtUtc": replacement["closedAtUtc"],
            "resolutionRule": resolution,
            "discardedVariantCount": family["lineageVariantCount"] - 1,
            "auditStatus": "SALVAGED_WITHOUT_RESULT_SELECTION",
        })

    salvage_path = RUN / "salvaged_ambiguous_delivery_candidates.csv"
    with salvage_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(salvaged[0]))
        writer.writeheader(); writer.writerows(salvaged)
    unresolved_path = RUN / "unresolved_ambiguous_delivery_families.csv"
    with unresolved_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(unresolved[0]))
        writer.writeheader(); writer.writerows(unresolved)

    scheduled: list[dict] = []
    overlap_blocked: list[dict] = []
    free_at = 0
    for row in sorted(salvaged, key=lambda item: parse_utc(item["firstRetestAtUtc"])):
        filled_at = parse_utc(row["firstRetestAtUtc"])
        if filled_at >= free_at:
            scheduled.append(row)
            free_at = parse_utc(row["closedAtUtc"])
        else:
            overlap_blocked.append(row)
    scheduled_path = RUN / "salvaged_ambiguous_delivery_single_position.csv"
    with scheduled_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(scheduled[0]))
        writer.writeheader(); writer.writerows(scheduled)

    report = [
        "# June 2026 Ambiguous Delivery Family Salvage",
        "",
        "This audit resolves causal ambiguity before reading trade outcomes. It does not add a June-specific strategy filter.",
        "",
        f"- Source ambiguous physical families: {len(families)}",
        f"- Causally salvaged standalone candidates: {len(salvaged)}",
        f"- Still unresolved: {len(unresolved)}",
        f"- Executable with one-position scheduling: {len(scheduled)}",
        f"- Blocked only by an already-open position: {len(overlap_blocked)}",
        "",
        "## Resolution contract",
        "",
        "1. Every child OB must be fully inside its immediate parent in price and parent-candle time.",
        "2. The scenario must have been frozen before the delivery FVG formed.",
        "3. Multiple contained physical root/refinement paths remain unresolved.",
        "4. For one H1/M30 external owner, internal objectives are intermediate delivery; the nearest directional unconsumed external liquidity remains the objective.",
        "5. The selected lineage must reproduce the same FVG and first retest through the existing execution engine.",
        "6. Outcome is appended only after steps 1-5 select the scenario.",
        "",
        "## Standalone candidates",
        "",
        "| Family | Formed | Side | Scope | Root | Child | Objective | Result | R | Resolution |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- | ---: | --- |",
    ]
    for row in salvaged:
        report.append(
            f"| {row['sourceFamilyId']} | {row['fvgFormedAtUtc']} | {row['direction']} | "
            f"{row['scope']} | {row['rootObBarId']} | {row['finalChildObBarId']} | "
            f"{float(row['objectivePrice']):.2f} | {row['outcome']} | "
            f"{float(row['resultR']):+.3f} | {row['resolutionRule']} |"
        )
    report.extend([
        "",
        "## Unresolved families",
        "",
        "| Family | Side | FVG | Reason | Remaining paths |",
        "| --- | --- | --- | --- | ---: |",
    ])
    for row in unresolved:
        report.append(
            f"| {row['familyId']} | {row['direction']} | {row['fvgBarId']} | "
            f"{row['reason']} | {row['remainingPathCount']} |"
        )
    report.extend([
        "",
        "## Interpretation boundary",
        "",
        "All standalone candidates came from an objective-first research population. Their outcomes are therefore not an independent profitability estimate. Only the causal salvage count is used to repair the benchmark; PnL must be evaluated later in a future-blind replay.",
    ])
    report_path = RUN / "AMBIGUOUS_DELIVERY_SALVAGE_REPORT.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    summary = {
        "sourceFamilies": len(families),
        "salvaged": len(salvaged),
        "unresolved": len(unresolved),
        "uniqueContained": sum(
            row["resolutionRule"] == "UNIQUE_CONTAINED_LINEAGE" for row in salvaged
        ),
        "scopeResolved": sum(
            row["resolutionRule"] == "SAME_DIRECTION_EXTERNAL_OWNER_INTERNAL_LIQUIDITY_IS_INTERMEDIATE"
            for row in salvaged
        ),
        "outcomes": {
            "TP": sum(row["outcome"] == "TP" for row in salvaged),
            "SL": sum(row["outcome"] == "SL" for row in salvaged),
        },
        "totalR": sum(float(row["resultR"]) for row in salvaged),
        "singlePositionCandidates": len(scheduled),
        "singlePositionTotalR": sum(float(row["resultR"]) for row in scheduled),
        "overlapBlocked": len(overlap_blocked),
        "salvageOutput": str(salvage_path),
        "unresolvedOutput": str(unresolved_path),
        "singlePositionOutput": str(scheduled_path),
        "report": str(report_path),
    }
    (RUN / "ambiguous_delivery_salvage_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
