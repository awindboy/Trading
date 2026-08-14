from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.mentor_ai_replay import (
    ROOT,
    RUN_ROOT,
    advance_pending_order,
    build_decision_prompt,
    load_rates,
    load_secret,
    load_stage_contract,
    parse_utc,
    render_packet,
    simulate_filled_position,
    utc_text,
    validate_pending_entry_side,
)


OUTPUT = ROOT / "output" / "mentor_codex_aug22_pipeline_audit"
TRUTH = ROOT / "output" / "mentor_blind_50_from_2024-06_medium" / "trades.csv"
DAY_START = parse_utc("2024-08-22T00:00:00Z")
DAY_END = parse_utc("2024-08-23T00:00:00Z")

# The current pipeline asks the model separately for map, refinement and trigger.
# Idle MAP reviews are included because they are real inference opportunities.
CALL_PLAN = [
    ("2024-08-22T00:00:00Z", "MAP", "scheduled map review"),
    ("2024-08-22T06:00:00Z", "MAP", "scheduled map review"),
    ("2024-08-22T10:00:00Z", "MAP", "intraday objective and source review"),
    ("2024-08-22T10:20:00Z", "MAP", "first short map freeze"),
    ("2024-08-22T10:20:00Z", "REFINEMENT", "first short causal child review"),
    ("2024-08-22T10:20:00Z", "TRIGGER", "first short M1 authorization"),
    ("2024-08-22T14:39:00Z", "MAP", "post-trade map reset"),
    ("2024-08-22T15:52:00Z", "MAP", "second short map freeze"),
    ("2024-08-22T15:52:00Z", "REFINEMENT", "second short causal child review"),
    ("2024-08-22T15:52:00Z", "TRIGGER", "second short M1 authorization"),
    ("2024-08-22T16:22:00Z", "MAP", "post-trade map reset"),
    ("2024-08-22T22:22:00Z", "MAP", "lower-range reaction review"),
    ("2024-08-22T22:40:00Z", "MAP", "long rotation map freeze"),
    ("2024-08-22T22:40:00Z", "REFINEMENT", "long causal child review"),
    ("2024-08-22T22:40:00Z", "TRIGGER", "long replacement authorization"),
]

DECISION_NOTES = {
    "L50-014": (
        "H1 external context remains bullish, but M30/M15 are delivering lower inside the "
        "range. The rebound reaches the bearish M15 root and M5 child; M1 rejects the "
        "refined area. This is an INTERNAL_ROTATION short to the first internal SSL."
    ),
    "L50-015": (
        "The first internal objective has delivered and the next rebound remains inside the "
        "same M15/M5 bearish delivery. A fresh M1 rejection authorizes a second independent "
        "INTERNAL_ROTATION short to the next internal SSL."
    ),
    "L50-016": (
        "The selloff reaches the lower side of the H1/M30 context. M15/M5 downside delivery "
        "loses force after the low excursion; M1 sweeps and recovers, then prints bullish "
        "delivery. The missed deep order is replaced at the first delivery retracement."
    ),
}


def read_truth() -> list[dict[str, str]]:
    with TRUTH.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            row for row in csv.DictReader(handle)
            if DAY_START <= parse_utc(row["decision_at"]) < DAY_END
        ]


def historical_phase_token_medians() -> dict[str, dict[str, int]]:
    values: dict[str, dict[str, list[int]]] = {}
    for path in RUN_ROOT.glob("*/calls/*/decision.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            phase = str(row["inputPacket"]["phase"])
            usage = row["usage"]
            values.setdefault(phase, {"prompt": [], "output": [], "total": []})
            values[phase]["prompt"].append(int(usage.get("promptTokenCount", 0)))
            values[phase]["output"].append(int(usage.get("candidatesTokenCount", 0)))
            values[phase]["total"].append(int(usage.get("totalTokenCount", 0)))
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
    medians: dict[str, dict[str, int]] = {}
    for phase in ("MAP", "REFINEMENT", "TRIGGER", "PENDING_REVIEW"):
        phase_values = values.get(phase, {})
        medians[phase] = {
            key: int(statistics.median(phase_values.get(key, [0])))
            for key in ("prompt", "output", "total")
        }
    return medians


def render_and_measure(config: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for index, (as_of, phase, purpose) in enumerate(CALL_PLAN, start=1):
        call_dir = OUTPUT / "calls" / f"{index:02d}_{as_of.replace(':', '-')}_{phase.lower()}"
        packet = render_packet(config, as_of, phase, call_dir)
        contract, _ = load_stage_contract(phase)
        prompt = build_decision_prompt(
            contract=contract,
            packet=packet,
            phase=phase,
            previous=None,
            candle_evidence=None,
        )
        last_closed = parse_utc(packet["lastClosedM1"]["openTimeUtc"]) + 60
        if last_closed > parse_utc(as_of) or not packet.get("futureHidden"):
            raise AssertionError(f"future leak in call {index}")
        calls.append({
            "call": index,
            "asOfUtc": as_of,
            "phase": phase,
            "purpose": purpose,
            "promptCharacters": len(prompt),
            "promptUtf8Bytes": len(prompt.encode("utf-8")),
            "imageBytes": sum(Path(item["path"]).stat().st_size for item in packet["images"]),
            "images": [item["path"] for item in packet["images"]],
            "futureHidden": True,
        })
    return calls


def replay_truth_orders(
    rates: np.ndarray,
    config: dict[str, Any],
    truth: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    for row in truth:
        decision_at = parse_utc(row["decision_at"])
        decision_indexes = np.flatnonzero(rates["time"] + 60 <= decision_at)
        if not len(decision_indexes):
            raise AssertionError(f"no closed M1 before {row['trade_id']}")
        cursor = int(decision_indexes[-1])
        scenario = {
            "direction": row["direction"].upper(),
            "scope": row["scope"],
        }
        order = {
            "entry": float(row["entry"]),
            "stopLoss": float(row["sl"]),
            "takeProfit": float(row["tp"]),
        }
        current = rates[cursor]
        side_errors = validate_pending_entry_side(
            {"action": "ORDER", "scenario": scenario, "order": order},
            {
                "lastClosedM1": {"close": float(current["close"])},
                "spreadPrice": float(current["spread"]) * float(config["point"]),
            },
        )
        if side_errors:
            audits.append({
                **row,
                "truth_filled_at": row["filled_at"],
                "truth_closed_at": row["closed_at"],
                "truth_outcome": row["outcome"],
                "truth_r": row["r"],
                "execution_admissible": "NO",
                "execution_reason": "; ".join(side_errors),
                "engine_fill_bar_open": "",
                "engine_fill_available": "",
                "geometry_outcome_parity": "NOT_RUN",
                "fill_interval_parity": "NON_EXECUTABLE",
                "parity": "NON_EXECUTABLE",
            })
            continue
        pending = {
            "nextReviewAtUtc": utc_text(decision_at + 3600),
            "watchEvents": [],
        }
        status, filled_index, event = advance_pending_order(
            rates,
            cursor,
            scenario,
            order,
            pending,
            config,
            entry_deadline=DAY_END,
        )
        if status != "FILLED":
            raise AssertionError(f"{row['trade_id']} did not fill: {status}/{event}")
        outcome, _ = simulate_filled_position(rates, filled_index, scenario, order, config)
        if outcome is None:
            raise AssertionError(f"{row['trade_id']} did not close")
        expected_r = float(row["r"])
        fill_bar_open = utc_text(int(rates[filled_index]["time"]))
        fill_bar_available = utc_text(int(rates[filled_index]["time"]) + 60)
        geometry_outcome_match = (
            outcome["closed_at"] == row["closed_at"]
            and outcome["outcome"] == row["outcome"]
            and math.isclose(float(outcome["r"]), expected_r, abs_tol=1e-8)
        )
        fill_interval_match = row["filled_at"] in {fill_bar_open, fill_bar_available}
        executable_match = geometry_outcome_match and fill_interval_match
        result = {
            **row,
            "truth_filled_at": row["filled_at"],
            "truth_closed_at": row["closed_at"],
            "truth_outcome": row["outcome"],
            "truth_r": row["r"],
            **outcome,
            "execution_admissible": "YES",
            "execution_reason": "pending limit is on the valid side of current Bid/Ask",
            "engine_fill_bar_open": fill_bar_open,
            "engine_fill_available": fill_bar_available,
            "geometry_outcome_parity": "EXACT" if geometry_outcome_match else "MISMATCH",
            "fill_interval_parity": "EXACT" if fill_interval_match else "MISMATCH",
            "parity": "EXACT" if executable_match else "MISMATCH",
        }
        results.append(result)
        audits.append(result)
    return results, audits


def write_report(
    calls: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    execution_audit: list[dict[str, Any]],
    medians: dict[str, dict[str, int]],
) -> None:
    estimated_prompt = sum(medians[item["phase"]]["prompt"] for item in calls)
    estimated_output = sum(medians[item["phase"]]["output"] for item in calls)
    estimated_total = sum(medians[item["phase"]]["total"] for item in calls)
    metrics = {
        "runId": "mentor_codex_aug22_pipeline_audit",
        "day": "2024-08-22",
        "externalApiCalls": 0,
        "codexJudgmentInvocations": len(calls),
        "promptCharacters": sum(item["promptCharacters"] for item in calls),
        "promptUtf8Bytes": sum(item["promptUtf8Bytes"] for item in calls),
        "imageBytes": sum(item["imageBytes"] for item in calls),
        "estimatedGeminiPromptTokensFromHistoricalMedian": estimated_prompt,
        "estimatedGeminiOutputTokensFromHistoricalMedian": estimated_output,
        "estimatedGeminiTotalTokensFromHistoricalMedian": estimated_total,
        "tokenEstimateIsExact": False,
        "truthRows": len(execution_audit),
        "nonExecutableTruthRows": sum(
            item["execution_admissible"] == "NO" for item in execution_audit
        ),
        "trades": len(trades),
        "geometryOutcomeParity": sum(
            item["geometry_outcome_parity"] == "EXACT" for item in trades
        ),
        "executableTimestampParity": sum(item["parity"] == "EXACT" for item in trades),
        "totalR": sum(float(item["r"]) for item in trades),
        "semanticCaveat": (
            "The authoritative CSV contains trade geometry but not the complete causal candle "
            "lineage required by replay_decision.schema.json. This run proves rendering, future "
            "blocking, and SL/TP outcome parity for executable rows; it does not fabricate "
            "missing lineage. The third truth order is marketable at decision time and is not "
            "a valid pending limit under Bid/Ask execution."
        ),
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "calls.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in calls),
        encoding="utf-8",
    )
    decisions = []
    for row in execution_audit:
        decisions.append({
            "tradeId": row["trade_id"],
            "decisionAtUtc": row["decision_at"],
            "direction": row["direction"],
            "scope": row["scope"],
            "executionModel": row["execution_model"],
            "rootTf": row["root_tf"],
            "childTf": row["child_tf"],
            "entry": float(row["entry"]),
            "sl": float(row["sl"]),
            "tp": float(row["tp"]),
            "authorization": (
                "ORDER" if row["execution_admissible"] == "YES"
                else "REJECTED_MARKETABLE_ENTRY"
            ),
            "asOfReason": DECISION_NOTES[row["trade_id"]],
        })
    (OUTPUT / "codex_decisions.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in decisions),
        encoding="utf-8",
    )
    fields = [
        "trade_id", "decision_at", "truth_filled_at", "truth_closed_at",
        "truth_outcome", "truth_r", "filled_at", "closed_at", "direction", "scope",
        "execution_model", "root_tf", "child_tf", "entry", "sl", "tp", "outcome",
        "r", "objective", "execution_admissible", "execution_reason",
        "engine_fill_bar_open", "engine_fill_available",
        "geometry_outcome_parity", "fill_interval_parity", "parity",
    ]
    with (OUTPUT / "trades.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(trades)
    with (OUTPUT / "truth_execution_audit.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(execution_audit)
    (OUTPUT / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# Codex 2024-08-22 pipeline audit

## Result

- Codex judgment invocations under the current phase split: **{len(calls)}**
- External API calls: **0**
- Estimated Gemini-equivalent tokens from historical per-phase medians: **{estimated_total:,}**
  - prompt: {estimated_prompt:,}
  - output: {estimated_output:,}
- Truth rows: **{len(execution_audit)}**
- Executable pending orders: **{len(trades)}**
- Rejected non-executable truth rows: **{metrics['nonExecutableTruthRows']}**
- Exact price/outcome/R parity: **{metrics['geometryOutcomeParity']}/{len(trades)}**
- Executable fill-time parity: **{metrics['executableTimestampParity']}/{len(trades)}**
- Total: **{metrics['totalR']:+.8f}R**

The token figure is an empirical estimate, not a provider bill. It applies historical Gemini
median usage by phase to the exact call plan. No Gemini generation was used in this audit.

## Boundary

The source truth CSV records entry, SL, TP and outcome but does not contain the complete root,
child, sweep, CHoCH and objective source-candle lineage required by the current semantic schema.
The audit proves that chart rendering is future-safe and that the SL/TP engine reproduces the
executable truth rows. At the third row's stated 22:40 decision, its 2481.93 buy-limit price is
already above the current Ask, so it is marketable rather than a pending retracement order. The
engine now rejects that order before replay. It does not invent missing semantic lineage or
weaken Bid/Ask execution merely to make the validator green.
"""
    (OUTPUT / "REPORT.md").write_text(report, encoding="utf-8")


def main() -> int:
    _, config = load_secret()
    rates, _ = load_rates(config)
    truth = read_truth()
    if len(truth) != 3:
        raise AssertionError(f"expected 3 truth trades, found {len(truth)}")
    calls = render_and_measure(config)
    trades, execution_audit = replay_truth_orders(rates, config, truth)
    medians = historical_phase_token_medians()
    write_report(calls, trades, execution_audit, medians)
    print("MENTOR_CODEX_AUG22_AUDIT_OK")
    print((OUTPUT / "metrics.json").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
