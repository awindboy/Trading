from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz
from scripts.mentor_ai_replay import parse_utc, utc_text


SOURCE = ROOT / "output" / "mentor_50trade_scope_locked_v1" / "working_trades.csv"
RUN = ROOT / "output" / "mentor_ai_replay_v4_runs" / "gemini_v449_oct20_24_high_activity_lite_20260811"
OUT = RUN / "legacy_truth_rule_audit.csv"
REPORT = RUN / "LEGACY_TRUTH_RULE_AUDIT.md"
START_ID = 36
END_ID = 50
TOLERANCE = 0.011


def bool_text(value: bool) -> str:
    return "PASS" if value else "FAIL"


def bar_index(series, timestamp: int) -> int | None:
    matches = np.flatnonzero(series.time == timestamp)
    return int(matches[0]) if matches.size else None


def opposite_color(series, index: int, direction: str) -> bool:
    if direction == "long":
        return float(series.close[index]) < float(series.open[index])
    return float(series.close[index]) > float(series.open[index])


def exact_zone(series, index: int, low: float, high: float) -> bool:
    return (
        abs(float(series.low[index]) - low) <= TOLERANCE
        and abs(float(series.high[index]) - high) <= TOLERANCE
    )


def directional_delivery(series, start: int, end: int, low: float, high: float, direction: str) -> bool:
    first = int(np.searchsorted(series.available_time, start, side="left"))
    last = int(np.searchsorted(series.available_time, end, side="right"))
    if last <= first:
        return False
    closes = series.close[first:last]
    if direction == "long":
        return bool(np.any(closes > high + TOLERANCE))
    return bool(np.any(closes < low - TOLERANCE))


def objective_evidence(m1, decision: int, direction: str, price: float) -> tuple[bool, bool]:
    side = m1.high if direction == "long" else m1.low
    origins = np.flatnonzero((m1.time < decision) & (np.abs(side - price) <= TOLERANCE))
    if not origins.size:
        return False, False
    origin = int(origins[-1])
    end = int(np.searchsorted(m1.time, decision, side="left"))
    later = side[origin + 1 : end]
    if direction == "long":
        unswept = not later.size or float(np.max(later)) < price - TOLERANCE
    else:
        unswept = not later.size or float(np.min(later)) > price + TOLERANCE
    return True, bool(unswept)


def first_limit_touch(m1, start: int, direction: str, entry: float, point: float) -> int | None:
    first = int(np.searchsorted(m1.time, start, side="left"))
    for index in range(first, len(m1.time)):
        spread = float(m1.spread_points[index]) * point
        touched = (
            float(m1.low[index]) + spread <= entry + TOLERANCE
            if direction == "long"
            else float(m1.high[index]) >= entry - TOLERANCE
        )
        if touched:
            return int(m1.time[index])
    return None


def timestamp_interval_match(recorded: int, bar_open: int | None) -> bool:
    if bar_open is None:
        return False
    return recorded in {bar_open, bar_open + 60} or recorded + 60 in {bar_open, bar_open + 60}


def outcome(m1, trade: dict[str, str], point: float) -> tuple[str, int | None]:
    direction = trade["direction"]
    stop = float(trade["stop_loss"])
    target = float(trade["take_profit"])
    start = int(np.searchsorted(m1.time, parse_utc(trade["filled_at"]), side="left"))
    for index in range(start, len(m1.time)):
        spread = float(m1.spread_points[index]) * point
        if direction == "long":
            stop_hit = float(m1.low[index]) <= stop + TOLERANCE
            target_hit = float(m1.high[index]) >= target - TOLERANCE
        else:
            stop_hit = float(m1.high[index]) + spread >= stop - TOLERANCE
            target_hit = float(m1.low[index]) + spread <= target + TOLERANCE
        if stop_hit or target_hit:
            if stop_hit and target_hit:
                return "AMBIGUOUS", int(m1.time[index])
            return ("SL" if stop_hit else "TP"), int(m1.time[index])
    return "OPEN", None


def gemini_state_at(events: list[dict], timestamp: int) -> tuple[str, str, str]:
    prior = [row for row in events if parse_utc(str(row["asOfUtc"])) <= timestamp]
    if not prior:
        return "FLAT", "", ""
    latest = prior[-1]
    active_direction = ""
    active_scope = ""
    active = False
    for row in prior:
        event = str(row["event"])
        if event == "SCENARIO_PLANNED":
            scenario = row.get("details", {}).get("scenario", {})
            active_direction = str(scenario.get("direction", "")).lower()
            active_scope = str(scenario.get("scope", ""))
            active = True
        elif event in {"SCENARIO_CANCELED", "TRADE_CLOSED"}:
            active = False
            active_direction = ""
            active_scope = ""
    return str(latest.get("state", "")), active_direction if active else "", active_scope if active else ""


def main() -> int:
    secret = json.loads((ROOT / "data" / "mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig"))
    config = secret["config"]
    m1, _ = load_m1_npz(ROOT / str(config["dataset"]))
    frames = build_timeframes(m1)
    point = float(config["point"])

    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        all_trades = list(csv.DictReader(handle))
    trades = [
        row for row in all_trades
        if START_ID <= int(row["trade_id"].split("-")[-1]) <= END_ID
    ]
    events = [
        json.loads(line)
        for line in (RUN / "decision_ledger.jsonl").read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]

    rows: list[dict[str, object]] = []
    for trade in trades:
        direction = trade["direction"]
        decision = parse_utc(trade["decision_at"])
        filled = parse_utc(trade["filled_at"])
        root_tf = trade["root_tf"]
        child_tf = trade["child_tf"]
        root_time = parse_utc(trade["root_time"])
        child_time = parse_utc(trade["child_time"])
        root_series = frames[root_tf]
        child_series = frames[child_tf]
        root_i = bar_index(root_series, root_time)
        child_i = bar_index(child_series, child_time)
        root_low, root_high = float(trade["root_low"]), float(trade["root_high"])
        child_low, child_high = float(trade["child_low"]), float(trade["child_high"])

        root_exact = root_i is not None and exact_zone(root_series, root_i, root_low, root_high)
        child_exact = child_i is not None and exact_zone(child_series, child_i, child_low, child_high)
        root_opposite = root_i is not None and opposite_color(root_series, root_i, direction)
        child_opposite = child_i is not None and opposite_color(child_series, child_i, direction)
        child_inside = child_low >= root_low - TOLERANCE and child_high <= root_high + TOLERANCE
        root_available = int(root_series.available_time[root_i]) if root_i is not None else decision + 1
        child_available = int(child_series.available_time[child_i]) if child_i is not None else decision + 1
        source_preexists = max(root_available, child_available) <= decision + 60
        root_delivery = directional_delivery(
            m1, root_available, decision + 60, root_low, root_high, direction
        )
        child_delivery = directional_delivery(
            m1, child_available, decision + 60, child_low, child_high, direction
        )

        objective_exists, objective_unswept = objective_evidence(
            m1, decision + 60, direction, float(trade["take_profit"])
        )
        expected_objective = (
            "INTERNAL_LIQUIDITY" if trade["scope"] == "INTERNAL_ROTATION"
            else "EXTERNAL_LIQUIDITY"
        )
        scope_contract = trade["objective_type"] == expected_objective

        strict_touch = first_limit_touch(m1, decision + 60, direction, float(trade["entry"]), point)
        fill_interval_match = timestamp_interval_match(filled, strict_touch)
        same_minute_decision_fill = decision == filled
        sl_beyond_child = (
            float(trade["stop_loss"]) < child_low
            if direction == "long"
            else float(trade["stop_loss"]) > child_high
        )
        calculated_outcome, calculated_exit = outcome(m1, trade, point)
        outcome_match = calculated_outcome == trade["result"]
        exit_interval_match = timestamp_interval_match(parse_utc(trade["closed_at"]), calculated_exit)
        gemini_state, gemini_direction, gemini_scope = gemini_state_at(events, filled)

        hard_conflicts: list[str] = []
        if not root_exact:
            hard_conflicts.append("ROOT_OHLC_MISMATCH")
        if not child_exact:
            hard_conflicts.append("CHILD_OHLC_MISMATCH")
        if not root_opposite:
            hard_conflicts.append("ROOT_NOT_OPPOSITE_CANDLE")
        if not child_opposite:
            hard_conflicts.append("CHILD_NOT_OPPOSITE_CANDLE")
        if not child_inside:
            hard_conflicts.append("CHILD_OUTSIDE_ROOT")
        if not source_preexists:
            hard_conflicts.append("SOURCE_NOT_AVAILABLE")
        if not scope_contract:
            hard_conflicts.append("SCOPE_OBJECTIVE_CONFLICT")
        if not objective_exists:
            hard_conflicts.append("OBJECTIVE_WICK_NOT_FOUND")
        elif not objective_unswept:
            hard_conflicts.append("OBJECTIVE_ALREADY_SWEPT")
        if not sl_beyond_child:
            hard_conflicts.append("SL_INSIDE_CHILD")
        if not fill_interval_match:
            hard_conflicts.append("NOT_FIRST_POST_DECISION_TOUCH")
        if not outcome_match:
            hard_conflicts.append("OUTCOME_MISMATCH")

        missing_evidence = [
            "PRE_FREEZE_MAP",
            "DEALING_RANGE_PD",
            "PROTECTED_SWING_BODY_BREAK",
            "MATURE_SWEEP",
            "MEANINGFUL_M1_CHOCH",
            "EXECUTION_OB",
            "H1_M15_REAUTHORIZATION",
        ]
        verdict = "CURRENT_RULE_CONFLICT" if hard_conflicts else "STRUCTURE_SUPPORTED_EVIDENCE_INCOMPLETE"
        rows.append(
            {
                "trade_id": trade["trade_id"],
                "direction": direction,
                "scope": trade["scope"],
                "filled_at": trade["filled_at"],
                "root_exact": bool_text(root_exact),
                "root_opposite": bool_text(root_opposite),
                "child_exact": bool_text(child_exact),
                "child_opposite": bool_text(child_opposite),
                "child_inside": bool_text(child_inside),
                "source_preexists": bool_text(source_preexists),
                "root_delivery": bool_text(root_delivery),
                "child_delivery": bool_text(child_delivery),
                "objective_exists": bool_text(objective_exists),
                "objective_unswept": bool_text(objective_unswept),
                "scope_objective_contract": bool_text(scope_contract),
                "first_touch_time": utc_text(strict_touch) if strict_touch else "",
                "fill_interval_match": bool_text(fill_interval_match),
                "same_minute_decision_fill": str(same_minute_decision_fill),
                "sl_beyond_child": bool_text(sl_beyond_child),
                "outcome_match": bool_text(outcome_match),
                "exit_interval_match": bool_text(exit_interval_match),
                "gemini_state_at_truth_fill": gemini_state,
                "gemini_active_direction": gemini_direction,
                "gemini_active_scope": gemini_scope,
                "verdict": verdict,
                "hard_conflicts": ";".join(hard_conflicts),
                "missing_evidence": ";".join(missing_evidence),
            }
        )

    with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    count = lambda field: sum(row[field] == "PASS" for row in rows)
    conflicts = [row for row in rows if row["verdict"] == "CURRENT_RULE_CONFLICT"]
    supported = [row for row in rows if row["verdict"] != "CURRENT_RULE_CONFLICT"]
    conflict_counts: dict[str, int] = {}
    for row in conflicts:
        for reason in str(row["hard_conflicts"]).split(";"):
            if reason:
                conflict_counts[reason] = conflict_counts.get(reason, 0) + 1

    lines = [
        "# 2025-10-20~24 legacy truth rule audit",
        "",
        "## Bottom line",
        "",
        f"- Current-rule hard conflict: **{len(conflicts)}/15**",
        f"- Mechanically supported but not fully documented: **{len(supported)}/15**",
        "- Fully certified under current AGENTS.md: **0/15**",
        "",
        "A missing certificate is not the same as a proven invalid trade. The saved ledger has no pre-order sweep, CHoCH, execution-OB, dealing-range or reauthorization records, so those elements cannot be reconstructed honestly from final prices alone.",
        "",
        "## Mechanical checks",
        "",
        "| Check | Pass |",
        "| --- | ---: |",
        f"| Root exact OHLC | {count('root_exact')}/15 |",
        f"| Root opposite-color OB candle | {count('root_opposite')}/15 |",
        f"| Child exact OHLC | {count('child_exact')}/15 |",
        f"| Child opposite-color OB candle | {count('child_opposite')}/15 |",
        f"| Child contained in root | {count('child_inside')}/15 |",
        f"| Objective exact prior wick | {count('objective_exists')}/15 |",
        f"| Objective unswept at decision | {count('objective_unswept')}/15 |",
        f"| Scope/objective contract | {count('scope_objective_contract')}/15 |",
        f"| First post-decision touch with +/-1 minute convention | {count('fill_interval_match')}/15 |",
        f"| SL beyond child distal | {count('sl_beyond_child')}/15 |",
        f"| Recorded outcome reproduced | {count('outcome_match')}/15 |",
        "",
        "## Hard-conflict counts",
        "",
    ]
    lines.extend(f"- `{reason}`: {amount}" for reason, amount in sorted(conflict_counts.items()))
    lines.extend([
        "",
        "## Per-trade verdict",
        "",
        "| Trade | Verdict | Hard conflicts | Gemini state at truth fill |",
        "| --- | --- | --- | --- |",
    ])
    for row in rows:
        reasons = str(row["hard_conflicts"]) or "none proven"
        state = str(row["gemini_state_at_truth_fill"])
        if row["gemini_active_direction"]:
            state += f" / {row['gemini_active_direction']} {row['gemini_active_scope']}"
        lines.append(f"| {row['trade_id']} | {row['verdict']} | {reasons} | {state} |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- A one-minute timestamp correction is accepted only when the same physical M1 candle and OHLC event are preserved.",
        "- The comparator's 15 MISS results are not explained by that correction; Gemini fills are 11 to 14 hours from the nearest same-direction truth fills.",
        "- The legacy ledger cannot be promoted to current-rule authority without the missing pre-freeze and trigger evidence.",
        "- Conversely, trades with no hard conflict should not be called false merely because the old ledger omitted evidence. Their correct status is evidence-incomplete.",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"hardConflicts={len(conflicts)}/15 supportedIncomplete={len(supported)}/15 certified=0/15")
    print(json.dumps(conflict_counts, ensure_ascii=False, sort_keys=True))
    print(OUT)
    print(REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
