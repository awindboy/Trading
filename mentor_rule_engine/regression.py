from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .engine import RuleCandidate


@dataclass(frozen=True)
class ReferenceSetup:
    reference_id: str
    direction: str
    created_at: int
    entry_bottom: float
    entry_top: float
    source_bottom: float
    source_top: float
    sweep_at: int
    objective: float


def compare_reference_setups(
    references: list[ReferenceSetup],
    candidates: list[RuleCandidate],
    *,
    point: float = 0.01,
    sweep_tolerance_minutes: int = 5,
    creation_tolerance_minutes: int = 0,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    used: set[str] = set()
    for reference in references:
        compatible = [
            candidate
            for candidate in candidates
            if (
                candidate.direction == reference.direction
                and abs(candidate.created_at - reference.created_at)
                <= creation_tolerance_minutes * 60
                and abs(candidate.fvg_bottom - reference.entry_bottom) <= point * 3
                and abs(candidate.fvg_top - reference.entry_top) <= point * 3
                and abs(candidate.sweep_at - reference.sweep_at)
                <= sweep_tolerance_minutes * 60
            )
        ]
        compatible.sort(
            key=lambda candidate: (
                abs(candidate.source_bottom - reference.source_bottom)
                + abs(candidate.source_top - reference.source_top),
                abs(candidate.sweep_at - reference.sweep_at),
            )
        )
        match = compatible[0] if compatible else None
        objective_match = False
        if match:
            objective_match = any(
                abs(float(item["level"]) - reference.objective) <= point * 3
                for item in match.objective_alternatives
            )
            used.add(match.candidate_id)
        rows.append(
            {
                "reference": asdict(reference),
                "matched": match is not None,
                "candidateId": match.candidate_id if match else None,
                "sourceExact": bool(
                    match
                    and abs(match.source_bottom - reference.source_bottom)
                    <= point * 3
                    and abs(match.source_top - reference.source_top)
                    <= point * 3
                ),
                "sourceParentOrRefinement": bool(
                    match
                    and (
                        abs(match.source_bottom - reference.source_bottom)
                        <= max(reference.source_top - reference.source_bottom, point)
                        or len(match.refinement_path) > 1
                    )
                ),
                "objectiveInCausalAlternatives": objective_match,
                "candidate": match.to_dict() if match else None,
            }
        )
    matched = sum(1 for row in rows if row["matched"])
    objectives = sum(
        1 for row in rows if row["objectiveInCausalAlternatives"]
    )
    return {
        "referenceCount": len(references),
        "matchedCount": matched,
        "entryRecall": matched / len(references) if references else 1.0,
        "objectiveAlternativeMatches": objectives,
        "objectiveAlternativeRecall": (
            objectives / len(references) if references else 1.0
        ),
        "extraCandidateCount": max(0, len(candidates) - len(used)),
        "rows": rows,
    }
