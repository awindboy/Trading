from __future__ import annotations

import copy
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mentor_ai_replay import (
    CONFIG_EXAMPLE,
    RUN_ROOT,
    SECRET,
    normalize_decision_queries,
    normalize_decision_routing,
    normalize_decision_state,
    normalize_map_rejection_audit,
    normalize_numeric_claims_from_evidence,
    normalize_review_schedule,
    parse_utc,
    rejected_decision_fallback,
    validate_decision,
)


def load_config() -> dict:
    if SECRET.exists():
        return dict(json.loads(SECRET.read_text(encoding="utf-8-sig"))["config"])
    return json.loads(CONFIG_EXAMPLE.read_text(encoding="utf-8-sig"))


def audit_run(path: Path, config: dict) -> tuple[int, int, list[str]]:
    ledger = path / "decision_ledger.jsonl"
    if not ledger.exists():
        return 0, 0, []
    previous = None
    evidence: list[dict] = []
    decisions = 0
    recovered = 0
    failures: list[str] = []
    for line_number, line in enumerate(
        ledger.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"{path.name}:{line_number}: invalid JSON: {exc}")
            continue
        event = row.get("event")
        if event in {"CANDLE_EVIDENCE_RETURNED", "CANDLE_EVIDENCE_PREFETCHED"}:
            evidence.extend(copy.deepcopy(row.get("evidence") or []))
            continue
        if event == "TRADE_CLOSED":
            previous = None
            evidence = []
            continue
        if event != "AI_DECISION" or not isinstance(row.get("decision"), dict):
            continue

        decisions += 1
        decision = copy.deepcopy(row["decision"])
        as_of = str(row.get("asOfUtc") or decision.get("asOfUtc"))
        phase = str(row.get("phase") or decision.get("phase"))
        try:
            as_of_timestamp = parse_utc(as_of)
        except (TypeError, ValueError):
            failures.append(f"{path.name}:{line_number}: invalid as-of")
            continue
        normalize_decision_routing(decision, as_of, phase)
        normalize_decision_state(decision, previous, phase)
        normalize_decision_queries(decision)
        normalize_review_schedule(decision, config, as_of_timestamp)
        scenario = decision.get("scenario")
        if isinstance(scenario, dict) and "frozenAtUtc" not in scenario:
            # Keep old ledgers auditable; live V3.8 decisions must provide this field.
            scenario["frozenAtUtc"] = scenario.get("refinedTouchTimeUtc") or as_of
        if isinstance(scenario, dict) and scenario.get("refinementPath"):
            child = scenario["refinementPath"][-1]
            scenario.setdefault("rootInvalidation", scenario.get("sourceInvalidation"))
            scenario["sourceInvalidation"] = float(
                child["low"] if scenario.get("direction") == "LONG" else child["high"]
            )
        order = decision.get("order")
        if isinstance(order, dict) and "sweepRecoveryTimeUtc" not in order:
            order["sweepRecoveryTimeUtc"] = order.get("sweepExtremeSourceTimeUtc")
        normalize_numeric_claims_from_evidence(decision, evidence, config)
        normalize_map_rejection_audit(decision, evidence)
        errors = validate_decision(
            decision, config, as_of_timestamp, evidence, previous_decision=previous
        )
        if errors:
            fallback = rejected_decision_fallback(
                as_of=as_of,
                phase=phase,
                rejected_decision=decision,
                previous_decision=previous,
                errors=errors,
                config=config,
                candle_evidence=evidence,
            )
            fallback_errors = validate_decision(
                fallback, config, as_of_timestamp, evidence, previous_decision=previous
            )
            if fallback_errors:
                failures.append(
                    f"{path.name}:{line_number}: fallback invalid: "
                    + "; ".join(fallback_errors)
                )
                continue
            if parse_utc(str(fallback["nextReviewAtUtc"])) <= as_of_timestamp:
                failures.append(f"{path.name}:{line_number}: fallback does not advance time")
                continue
            recovered += 1
            previous = fallback
        else:
            previous = decision

        if previous.get("action") in {"CANCEL", "NO_TRADE"}:
            evidence = []
    return decisions, recovered, failures


def main() -> int:
    config = load_config()
    totals = {"runs": 0, "decisions": 0, "recovered": 0}
    failures: list[str] = []
    paths = {
        path
        for pattern in ("gemini_aug22*", "gemini_aug21*")
        for path in RUN_ROOT.glob(pattern)
    }
    for path in sorted(paths):
        if not path.is_dir():
            continue
        decisions, recovered, run_failures = audit_run(path, config)
        if decisions:
            totals["runs"] += 1
            totals["decisions"] += decisions
            totals["recovered"] += recovered
        failures.extend(run_failures)
    if failures:
        print("MENTOR_AI_REPLAY_FAILURE_ARCHIVE_AUDIT_FAILED")
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("MENTOR_AI_REPLAY_FAILURE_ARCHIVE_AUDIT_OK")
    print(json.dumps(totals, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
