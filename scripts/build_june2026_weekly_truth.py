"""Build weekly June oracle slices without turning them into live PnL claims."""

from __future__ import annotations

import csv
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from mentor_replay_v4_core import parse_utc, utc_text  # noqa: E402

SOURCE = ROOT / "output/mentor_june2026_causal_benchmark"
OUTPUT = SOURCE / "weekly_truth"
WEEKS = (
    ("W01", "2026-06-01T00:00:00Z", "2026-06-08T00:00:00Z"),
    ("W02", "2026-06-08T00:00:00Z", "2026-06-15T00:00:00Z"),
    ("W03", "2026-06-15T00:00:00Z", "2026-06-22T00:00:00Z"),
    ("W04", "2026-06-22T00:00:00Z", "2026-06-29T00:00:00Z"),
    ("W05", "2026-06-29T00:00:00Z", "2026-07-01T00:00:00Z"),
)

SCOPE_PRIORITY = {
    "EXTERNAL_CONTINUATION": 0,
    "INTERNAL_ROTATION": 1,
    "EXTERNAL_REVERSAL": 2,
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def delivery_record(raw: dict[str, str], source: str, truth_id: str) -> dict:
    refinement = raw.get("refinementPath", "")
    child_ids = [item for item in refinement.split(";") if item]
    if not child_ids and raw.get("finalChildObBarId"):
        child_ids = [raw["finalChildObBarId"]]
    return {
        "truthId": truth_id,
        "source": source,
        "executionModel": "DELIVERY_FVG_REPLACEMENT",
        "planFrozenAtUtc": raw["frozenAtUtc"],
        "direction": raw["direction"],
        "scope": raw["scope"],
        "rootObBarId": raw["rootObBarId"],
        "refinementPath": child_ids,
        "finalChildObBarId": raw["finalChildObBarId"],
        "objectiveBarId": raw["objectiveBarId"],
        "objectivePrice": float(raw["objectivePrice"]),
        "deliveryFvgBarId": raw["fvgBarId"],
        "deliveryFvgFormedAtUtc": raw["fvgFormedAtUtc"],
        "filledAtUtc": raw["firstRetestAtUtc"],
        "closedAtUtc": raw["closedAtUtc"],
        "entry": float(raw["entry"]),
        "stop": float(raw["stop"]),
        "target": float(raw["target"]),
        "outcome": raw["outcome"],
        "resultR": float(raw["resultR"]),
    }


def select_execution_sequence(candidates: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """Apply the frozen one-active-scenario contract without using outcomes.

    The causal atlas may contain several valid opportunities that overlap in
    wall-clock time.  They remain useful detection truth, but cannot all be an
    executable benchmark for the V4 single-scenario state machine.  Selection
    uses only information frozen before execution: PLAN time and, for options
    on the same physical lineage at that instant, AGENTS.md's preference for a
    valid external continuation over shrinking the target to internal rotation.
    """
    grouped: dict[int, list[dict]] = {}
    for item in candidates:
        grouped.setdefault(parse_utc(item["planFrozenAtUtc"]), []).append(item)

    selected: list[dict] = []
    blocked_by: dict[str, str] = {}
    active_until = -1
    active_truth_id = ""
    for plan_time in sorted(grouped):
        group = grouped[plan_time]
        if plan_time < active_until:
            for item in group:
                blocked_by[item["truthId"]] = active_truth_id
            continue

        ranked = sorted(
            group,
            key=lambda item: (
                SCOPE_PRIORITY.get(item["scope"], 99),
                item["rootObBarId"],
                tuple(item["refinementPath"]),
                item["objectiveBarId"],
            ),
        )
        winner = ranked[0]
        winner_rank = SCOPE_PRIORITY.get(winner["scope"], 99)
        unresolved = [
            item for item in ranked[1:]
            if SCOPE_PRIORITY.get(item["scope"], 99) == winner_rank
        ]
        if unresolved:
            ids = ", ".join(item["truthId"] for item in ranked)
            raise RuntimeError(
                f"execution truth has an unresolved same-time semantic tie: {ids}"
            )
        selected.append(winner)
        active_until = parse_utc(winner["closedAtUtc"])
        active_truth_id = winner["truthId"]
        for item in ranked[1:]:
            blocked_by[item["truthId"]] = winner["truthId"]
    return selected, blocked_by


def select_multi_position_sequence(
    candidates: list[dict], *, maximum_slots: int = 3, maximum_positions: int = 3
) -> tuple[list[dict], dict[str, dict[str, str | None]]]:
    """Compose the atlas under AGENTS plus the explicit multi-position waiver.

    This selection does not prefer TP over SL.  It uses only PLAN time and the
    mechanical lifecycle needed to enforce concurrency.  A second candidate
    under the same directional root while its first scenario/position remains
    active is an add-on, not an independent initial entry, and stays disabled.
    Same-time INTERNAL/EXTERNAL scopes under one root are semantic alternatives.
    """
    grouped: dict[int, list[dict]] = {}
    for item in candidates:
        grouped.setdefault(parse_utc(item["planFrozenAtUtc"]), []).append(item)
    selected: list[dict] = []
    rejected: dict[str, dict[str, str | None]] = {}
    external_owner_direction: str | None = None
    for plan_time in sorted(grouped):
        by_source: dict[tuple[str, str], list[dict]] = {}
        for item in grouped[plan_time]:
            by_source.setdefault(
                (str(item["direction"]), str(item["rootObBarId"])), []
            ).append(item)
        choices: list[dict] = []
        for options in by_source.values():
            ranked = sorted(
                options,
                key=lambda item: (
                    SCOPE_PRIORITY.get(item["scope"], 99), item["truthId"]
                ),
            )
            winner = ranked[0]
            choices.append(winner)
            for item in ranked[1:]:
                rejected[item["truthId"]] = {
                    "reason": "SAME_TIME_SCOPE_ALTERNATIVE",
                    "blockedByTruthId": winner["truthId"],
                }
        for item in sorted(choices, key=lambda value: value["truthId"]):
            next_owner_direction = external_owner_direction
            if item["scope"] in {"EXTERNAL_CONTINUATION", "EXTERNAL_REVERSAL"}:
                if external_owner_direction is None:
                    if item["scope"] != "EXTERNAL_CONTINUATION":
                        rejected[item["truthId"]] = {
                            "reason": "EXTERNAL_REVERSAL_WITHOUT_PRIOR_OWNER",
                            "blockedByTruthId": None,
                        }
                        continue
                    next_owner_direction = str(item["direction"])
                elif str(item["direction"]) == external_owner_direction:
                    if item["scope"] != "EXTERNAL_CONTINUATION":
                        rejected[item["truthId"]] = {
                            "reason": "SAME_OWNER_MISLABELED_EXTERNAL_REVERSAL",
                            "blockedByTruthId": None,
                        }
                        continue
                else:
                    if item["scope"] != "EXTERNAL_REVERSAL":
                        rejected[item["truthId"]] = {
                            "reason": "GLOBAL_OWNER_TRANSITION_UNPROVEN",
                            "blockedByTruthId": None,
                        }
                        continue
                    next_owner_direction = str(item["direction"])
            active = [
                prior for prior in selected
                if parse_utc(prior["planFrozenAtUtc"]) <= plan_time
                < parse_utc(prior["closedAtUtc"])
            ]
            same_source = next(
                (
                    prior for prior in active
                    if prior["direction"] == item["direction"]
                    and prior["rootObBarId"] == item["rootObBarId"]
                ),
                None,
            )
            if same_source is not None:
                rejected[item["truthId"]] = {
                    "reason": "SOURCE_FAMILY_BUSY_ADDON_DISABLED",
                    "blockedByTruthId": same_source["truthId"],
                }
                continue
            waiting = [
                prior for prior in active
                if plan_time < parse_utc(prior["filledAtUtc"])
            ]
            open_positions = [
                prior for prior in active
                if parse_utc(prior["filledAtUtc"]) <= plan_time
            ]
            if len(waiting) >= maximum_slots:
                rejected[item["truthId"]] = {
                    "reason": "SCENARIO_SLOT_CAPACITY",
                    "blockedByTruthId": None,
                }
                continue
            if len(open_positions) >= maximum_positions:
                rejected[item["truthId"]] = {
                    "reason": "POSITION_BOOK_CAPACITY",
                    "blockedByTruthId": None,
                }
                continue
            selected.append(item)
            external_owner_direction = next_owner_direction
    return selected, rejected


def main() -> int:
    strict = [
        delivery_record(item, "STRICT_UNAMBIGUOUS", item["candidateId"])
        for item in rows(SOURCE / "strict_delivery_replacement_candidates.csv")
    ]
    salvaged_rows = rows(SOURCE / "salvaged_ambiguous_delivery_candidates.csv")
    salvaged = [
        delivery_record(item, "SALVAGED_AMBIGUOUS", item["sourceFamilyId"])
        for item in salvaged_rows
        if item["sourceFamilyId"] != "J26-AMB-020"
    ]
    promoted = rows(SOURCE / "trades.csv")
    original_delivery = next(item for item in promoted if item["tradeId"] == "J26-GT-001")
    duplicate_geometry = next(
        item for item in salvaged_rows if item["sourceFamilyId"] == "J26-AMB-020"
    )
    gt1 = {
        "truthId": "J26-GT-001",
        "source": "ORIGINAL_PROMOTED",
        "executionModel": "DELIVERY_FVG_REPLACEMENT",
        "planFrozenAtUtc": original_delivery["decisionAtUtc"],
        "direction": original_delivery["direction"],
        "scope": original_delivery["scope"],
        "rootObBarId": original_delivery["rootObBarId"],
        "refinementPath": [original_delivery["childObBarId"]],
        "finalChildObBarId": original_delivery["childObBarId"],
        "objectiveBarId": original_delivery["objectiveBarId"],
        "objectivePrice": float(original_delivery["target"]),
        "deliveryFvgBarId": duplicate_geometry["fvgBarId"],
        "deliveryFvgFormedAtUtc": duplicate_geometry["fvgFormedAtUtc"],
        "filledAtUtc": original_delivery["entryAtUtc"],
        "closedAtUtc": original_delivery["exitAtUtc"],
        "entry": float(original_delivery["entry"]),
        "stop": float(original_delivery["stop"]),
        "target": float(original_delivery["target"]),
        "outcome": original_delivery["result"],
        "resultR": float(original_delivery["resultR"]),
    }
    original_ob = next(item for item in promoted if item["tradeId"] == "J26-GT-002")
    gt2 = {
        "truthId": "J26-GT-002",
        "source": "ORIGINAL_PROMOTED",
        "executionModel": "HTF_OB_REACTION",
        "planFrozenAtUtc": original_ob["decisionAtUtc"],
        "direction": original_ob["direction"],
        "scope": original_ob["scope"],
        "rootObBarId": original_ob["rootObBarId"],
        "refinementPath": [original_ob["childObBarId"]],
        "finalChildObBarId": original_ob["childObBarId"],
        "objectiveBarId": original_ob["objectiveBarId"],
        "objectivePrice": float(original_ob["target"]),
        "deliveryFvgBarId": None,
        "deliveryFvgFormedAtUtc": None,
        "filledAtUtc": original_ob["entryAtUtc"],
        "closedAtUtc": original_ob["exitAtUtc"],
        "entry": float(original_ob["entry"]),
        "stop": float(original_ob["stop"]),
        "target": float(original_ob["target"]),
        "outcome": original_ob["result"],
        "resultR": float(original_ob["resultR"]),
    }
    candidates = sorted(
        [*strict, *salvaged, gt1, gt2],
        key=lambda item: (parse_utc(item["filledAtUtc"]), item["truthId"]),
    )
    if len(candidates) != 40:
        raise RuntimeError(f"expected 40 distinct candidates, got {len(candidates)}")
    physical = {
        (item["direction"], item["filledAtUtc"], round(item["entry"], 2))
        for item in candidates
    }
    if len(physical) != len(candidates):
        raise RuntimeError("weekly truth still contains duplicate physical entries")

    execution_sequence, blocked_by = select_execution_sequence(candidates)
    execution_ids = {item["truthId"] for item in execution_sequence}
    multi_sequence, multi_rejected = select_multi_position_sequence(candidates)
    multi_ids = {item["truthId"] for item in multi_sequence}

    OUTPUT.mkdir(parents=True, exist_ok=True)
    summary: list[dict] = []
    for week_id, start_text, end_text in WEEKS:
        start, end = parse_utc(start_text), parse_utc(end_text)
        selected = [
            item for item in candidates
            if start <= parse_utc(item["filledAtUtc"]) < end
        ]
        annotated = []
        for item in selected:
            copy = deepcopy(item)
            if item["truthId"] in execution_ids:
                copy["executionEligibility"] = "SELECTED"
                copy["blockedByTruthId"] = None
            else:
                copy["executionEligibility"] = "BLOCKED_BY_ACTIVE_SCENARIO"
                copy["blockedByTruthId"] = blocked_by[item["truthId"]]
            annotated.append(copy)
        executable = [
            item for item in annotated
            if item["executionEligibility"] == "SELECTED"
        ]
        multi_executable = [
            item for item in annotated if item["truthId"] in multi_ids
        ]
        for item in annotated:
            if item["truthId"] in multi_ids:
                item["multiPositionEligibility"] = "SELECTED"
                item["multiPositionBlockReason"] = None
                item["multiPositionBlockedByTruthId"] = None
            else:
                rejection = multi_rejected[item["truthId"]]
                item["multiPositionEligibility"] = "BLOCKED"
                item["multiPositionBlockReason"] = rejection["reason"]
                item["multiPositionBlockedByTruthId"] = rejection["blockedByTruthId"]
        payload = {
            "schemaVersion": "june-oracle-weekly-v2",
            "coverage": "CAUSAL_OPPORTUNITY_ATLAS_AND_MONTH_CONTINUOUS_SINGLE_SCENARIO_SEQUENCE",
            "authorityBoundary": {
                "positiveCases": "RULE_COMPLIANT_CAUSAL_OPPORTUNITIES",
                "negativeCases": "NOT_ENUMERATED",
                "unmatchedCandidateClassification": "UNASSESSED",
                "exactTradeSequenceParityAuthorized": False,
                "profitabilityValidationAuthorized": False,
            },
            "weekId": week_id,
            "startUtc": start_text,
            "endUtc": end_text,
            "candidateCount": len(annotated),
            "executionCandidateCount": len(executable),
            "multiPositionExecutionCandidateCount": len(multi_executable),
            "candidates": annotated,
            "executionCandidates": executable,
            "multiPositionExecutionCandidates": multi_executable,
        }
        (OUTPUT / f"{week_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary.append({
            "weekId": week_id,
            "startUtc": start_text,
            "endUtc": end_text,
            "candidates": len(annotated),
            "executionCandidates": len(executable),
            "multiPositionExecutionCandidates": len(multi_executable),
            "deliveryFvg": sum(
                item["executionModel"] == "DELIVERY_FVG_REPLACEMENT"
                for item in annotated
            ),
            "htfObReaction": sum(
                item["executionModel"] == "HTF_OB_REACTION"
                for item in annotated
            ),
        })
    (OUTPUT / "summary.json").write_text(
        json.dumps(
            {
                "totalAtlasCandidates": len(candidates),
                "totalExecutionCandidates": len(execution_sequence),
                "totalMultiPositionExecutionCandidates": len(multi_sequence),
                "multiPositionTotalR": sum(
                    float(item["resultR"]) for item in multi_sequence
                ),
                "authorityBoundary": {
                    "negativeCases": "NOT_ENUMERATED",
                    "exactTradeSequenceParityAuthorized": False,
                    "profitabilityValidationAuthorized": False,
                },
                "weeks": summary,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUTPUT / "multi_position_truth.json").write_text(
        json.dumps(
            {
                "schemaVersion": "june-oracle-multi-position-v1",
                "authority": "AGENTS.md_WITH_SINGLE_POSITION_WAIVER_ONLY",
                "maximumScenarioSlots": 3,
                "maximumConcurrentPositions": 3,
                "candidateCount": len(multi_sequence),
                "totalR": sum(float(item["resultR"]) for item in multi_sequence),
                "candidates": multi_sequence,
                "rejections": multi_rejected,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
