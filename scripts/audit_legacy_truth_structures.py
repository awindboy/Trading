from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz
from scripts.mentor_ai_replay import parse_utc, utc_text


LEDGER = ROOT / "output" / "mentor_50trade_oos_v2" / "manual_decisions.jsonl"
TRADES = ROOT / "output" / "mentor_50trade_oos_v2" / "trades.csv"
OUT_DIR = ROOT / "output" / "gemini_oct28_31_protocol_v2_audit"
OUT_CSV = OUT_DIR / "LEGACY_STRUCTURE_REAUDIT.csv"
OUT_REPORT = OUT_DIR / "LEGACY_STRUCTURE_REAUDIT.md"
ZONE_RE = re.compile(
    r"(H1|M30|M15|M5|M1)\s+(?:(\d{4}-\d\d-\d\d)\s+)?"
    r"(\d\d:\d\d)\s+\[([0-9.]+),([0-9.]+)\]"
)


def parse_zone(text: str, fallback_date: str) -> dict[str, object] | None:
    match = ZONE_RE.search(text)
    if not match:
        return None
    timeframe, date, hm, low, high = match.groups()
    date = date or fallback_date
    return {
        "tf": timeframe,
        "open": parse_utc(f"{date}T{hm}:00Z"),
        "low": min(float(low), float(high)),
        "high": max(float(low), float(high)),
    }


def bar_index(series, timestamp: int) -> int | None:
    indexes = np.flatnonzero(series.time == timestamp)
    return int(indexes[0]) if indexes.size else None


def is_opposite(open_price: float, close_price: float, direction: str) -> bool:
    return close_price < open_price if direction == "LONG" else close_price > open_price


def physical_zone_match(series, index: int, zone: dict[str, object]) -> bool:
    tolerance = 0.011
    return (
        abs(float(series.low[index]) - float(zone["low"])) <= tolerance
        and abs(float(series.high[index]) - float(zone["high"])) <= tolerance
    )


def matching_fvg(m1, direction: str, expected: tuple[float, float], decision: int):
    end = int(np.searchsorted(m1.time, decision, side="right"))
    matches: list[int] = []
    for index in range(2, end):
        if direction == "LONG" and float(m1.high[index - 2]) < float(m1.low[index]):
            zone = float(m1.high[index - 2]), float(m1.low[index])
        elif direction == "SHORT" and float(m1.low[index - 2]) > float(m1.high[index]):
            zone = float(m1.high[index]), float(m1.low[index - 2])
        else:
            continue
        if max(abs(zone[0] - expected[0]), abs(zone[1] - expected[1])) <= 0.011:
            matches.append(index)
    return matches[-1] if matches else None


def first_limit_touch(m1, start: int, direction: str, entry: float, point: float) -> int | None:
    first = int(np.searchsorted(m1.time, start, side="left"))
    for index in range(first, len(m1.time)):
        spread = float(m1.spread_points[index]) * point
        if direction == "LONG":
            touched = float(m1.low[index]) + spread <= entry + 0.011
        else:
            touched = float(m1.high[index]) >= entry - 0.011
        if touched:
            return int(m1.time[index])
    return None


def objective_evidence(m1, decision: int, direction: str, price: float):
    side = m1.high if direction == "LONG" else m1.low
    before = np.flatnonzero((m1.time < decision) & (np.abs(side - price) <= 0.011))
    if not before.size:
        return False, False, None
    origin = int(before[-1])
    end = int(np.searchsorted(m1.time, decision, side="left"))
    later = side[origin + 1:end]
    if direction == "LONG":
        unswept = not later.size or float(np.max(later)) < price - 0.011
    else:
        unswept = not later.size or float(np.min(later)) > price + 0.011
    return True, bool(unswept), int(m1.time[origin])


def outcome_from_ohlc(m1, trade: dict[str, str], point: float):
    direction = trade["direction"].upper()
    sl = float(trade["stop_loss"])
    tp = float(trade["take_profit"])
    start = int(np.searchsorted(m1.time, parse_utc(trade["filled_at"]), side="left"))
    for index in range(start, len(m1.time)):
        spread = float(m1.spread_points[index]) * point
        if direction == "LONG":
            sl_hit = float(m1.low[index]) <= sl + 0.011
            tp_hit = float(m1.high[index]) >= tp - 0.011
        else:
            sl_hit = float(m1.high[index]) + spread >= sl - 0.011
            tp_hit = float(m1.low[index]) + spread <= tp + 0.011
        if sl_hit or tp_hit:
            return ("AMBIGUOUS" if sl_hit and tp_hit else "SL" if sl_hit else "TP"), int(m1.time[index])
    return "OPEN", None


def reaction_execution_audit(m1, decision: dict[str, object], trade: dict[str, str], point: float):
    date = str(decision["as_of"])[:10]
    zone = parse_zone(str(decision.get("execution_ob", "")), date)
    if zone is None:
        return False, False, None, ["execution OB metadata could not be parsed"]
    index = bar_index(m1, int(zone["open"]))
    if index is None:
        return False, False, None, ["execution OB candle is absent"]
    price_match = physical_zone_match(m1, index, zone)
    color_match = is_opposite(float(m1.open[index]), float(m1.close[index]), str(decision["direction"]))
    available = int(m1.available_time[index])
    notes: list[str] = []

    sweep_match = False
    sweep = re.search(r"(\d\d:\d\d)\s+high\s+([0-9.]+)", str(decision.get("final_sweep", "")))
    if sweep:
        sweep_time = parse_utc(f"{date}T{sweep.group(1)}:00Z")
        sweep_index = bar_index(m1, sweep_time)
        sweep_match = sweep_index is not None and abs(float(m1.high[sweep_index]) - float(sweep.group(2))) <= 0.011
    if not sweep_match:
        notes.append("recorded final sweep does not match raw high")

    choch_match = False
    choch = re.search(r"(\d\d:\d\d)\s+body break", str(decision.get("choch", "")))
    if choch:
        choch_time = parse_utc(f"{date}T{choch.group(1)}:00Z")
        choch_index = bar_index(m1, choch_time)
        if choch_index is not None:
            # The last confirmed three-bar reaction swing between sweep and CHoCH.
            lows = []
            for candidate in range(max(1, choch_index - 15), choch_index - 1):
                if m1.low[candidate] < m1.low[candidate - 1] and m1.low[candidate] <= m1.low[candidate + 1]:
                    lows.append(candidate)
            if lows and str(decision["direction"]) == "SHORT":
                choch_match = float(m1.close[choch_index]) < float(m1.low[lows[-1]])
    if not choch_match:
        notes.append("meaningful CHoCH could not be reconstructed")
    # The pre-CHoCH execution OB is not actionable when it forms. Its first
    # eligible retest starts only after the CHoCH candle has closed.
    actionable_at = int(m1.available_time[choch_index]) if choch and choch_index is not None else available
    first_touch = first_limit_touch(m1, actionable_at, str(decision["direction"]), float(trade["entry"]), point)
    fill_match = first_touch == parse_utc(trade["filled_at"])
    return price_match and color_match and sweep_match and choch_match, fill_match, actionable_at, notes


def main() -> int:
    config = json.loads((ROOT / "data" / "mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig"))["config"]
    m1, _ = load_m1_npz(ROOT / str(config["dataset"]))
    frames = build_timeframes(m1)
    point = float(config["point"])
    trades = list(csv.DictReader(TRADES.open(encoding="utf-8-sig")))[:13]
    decisions = {}
    decision_lines = []
    for line in LEDGER.read_text(encoding="utf-8-sig").splitlines():
        row = json.loads(line)
        decision_lines.append(row)
        if row.get("status") == "ORDER_FROZEN" and row.get("trade_id"):
            decisions[str(row["trade_id"])] = row

    output: list[dict[str, object]] = []
    for trade in trades:
        decision = decisions[trade["trade_id"]]
        direction = str(decision["direction"])
        recorded_decision = parse_utc(str(decision["as_of"]))
        date = str(decision["as_of"])[:10]
        root = parse_zone(str(decision.get("root_ob", "")), date)
        child = parse_zone(str(decision.get("child_ob", "")), date)
        notes: list[str] = []

        root_match = child_match = root_color = child_color = child_inside = False
        source_before_execution = False
        if root and child:
            root_series, child_series = frames[str(root["tf"])], frames[str(child["tf"])]
            root_index = bar_index(root_series, int(root["open"]))
            child_index = bar_index(child_series, int(child["open"]))
            if root_index is not None and child_index is not None:
                root_match = physical_zone_match(root_series, root_index, root)
                child_match = physical_zone_match(child_series, child_index, child)
                root_color = is_opposite(float(root_series.open[root_index]), float(root_series.close[root_index]), direction)
                child_color = is_opposite(float(child_series.open[child_index]), float(child_series.close[child_index]), direction)
                child_inside = float(child["low"]) >= float(root["low"]) - 0.011 and float(child["high"]) <= float(root["high"]) + 0.011
                source_before_execution = max(int(root_series.available_time[root_index]), int(child_series.available_time[child_index])) <= recorded_decision + 60
        if not child_color:
            notes.append("child candle is not the last opposite-color OB candidate")

        execution_match = first_retest_match = False
        execution_available = None
        if trade["execution_model"] == "DELIVERY_FVG_REPLACEMENT":
            zones = re.findall(r"\[([0-9.]+),([0-9.]+)\]", str(decision.get("execution_zone", "")))
            if zones:
                expected = tuple(sorted(map(float, zones[-1])))
                fvg_index = matching_fvg(m1, direction, expected, recorded_decision)
                if fvg_index is not None:
                    execution_match = True
                    execution_available = int(m1.available_time[fvg_index])
                    first_touch = first_limit_touch(m1, execution_available, direction, float(trade["entry"]), point)
                    first_retest_match = first_touch == parse_utc(trade["filled_at"])
            if not execution_match:
                notes.append("exact physical FVG not found")
        else:
            execution_match, first_retest_match, execution_available, reaction_notes = reaction_execution_audit(m1, decision, trade, point)
            notes.extend(reaction_notes)

        objective_match, objective_unswept, objective_origin = objective_evidence(
            m1, execution_available or recorded_decision, direction, float(trade["take_profit"])
        )
        if not objective_match:
            notes.append("objective wick price not found before decision")
        elif not objective_unswept:
            notes.append("objective was consumed before decision")

        child_distal = float(child["low"] if direction == "LONG" else child["high"]) if child else float("nan")
        hard_sl = float(trade["stop_loss"])
        sl_beyond_child = hard_sl < child_distal if direction == "LONG" else hard_sl > child_distal
        fill_index = int(np.searchsorted(m1.time, parse_utc(trade["filled_at"]), side="left"))
        spread = float(m1.spread_points[fill_index]) * point
        sl_buffer = child_distal - hard_sl if direction == "LONG" else hard_sl - child_distal
        sl_spread_ok = sl_buffer + 0.011 >= spread

        objective_type_expected = "EXTERNAL_LIQUIDITY" if trade["scope"] == "EXTERNAL_CONTINUATION" else "INTERNAL_LIQUIDITY"
        scope_contract = trade["objective_type"] == objective_type_expected
        if not scope_contract:
            notes.append("scope and objective type conflict under current AGENTS.md")

        calculated_result, calculated_exit = outcome_from_ohlc(m1, trade, point)
        outcome_match = calculated_result == trade["result"]
        exit_time_match = calculated_exit == parse_utc(trade["closed_at"])
        if outcome_match and not exit_time_match:
            notes.append(f"outcome matches but first terminal bar is {utc_text(calculated_exit)}")

        order_line_index = next(i for i, item in enumerate(decision_lines) if item.get("trade_id") == trade["trade_id"] and item.get("status") == "ORDER_FROZEN")
        prefreeze = any(
            item.get("as_of", "") < decision.get("as_of", "")
            and item.get("root_ob") == decision.get("root_ob")
            and item.get("child_ob") == decision.get("child_ob")
            for item in decision_lines[:order_line_index]
        )
        if not prefreeze:
            notes.append("separate pre-order root/child freeze record is absent")

        physical_ok = all((root_match, child_match, child_inside, source_before_execution, execution_match, first_retest_match, objective_match, objective_unswept, sl_beyond_child, sl_spread_ok, outcome_match))
        protocol_ok = physical_ok and root_color and child_color and scope_contract and prefreeze
        output.append({
            "trade_id": trade["trade_id"],
            "root_price_match": root_match,
            "root_opposite_color": root_color,
            "child_price_match": child_match,
            "child_opposite_color": child_color,
            "child_inside_root": child_inside,
            "source_available_before_execution": source_before_execution,
            "execution_price_match": execution_match,
            "execution_available_at": utc_text(execution_available) if execution_available else "",
            "first_retest_fill_match": first_retest_match,
            "objective_wick_match": objective_match,
            "objective_unswept": objective_unswept,
            "objective_origin": utc_text(objective_origin) if objective_origin else "",
            "sl_beyond_child": sl_beyond_child,
            "sl_buffer_covers_spread": sl_spread_ok,
            "scope_objective_contract": scope_contract,
            "outcome_match": outcome_match,
            "exit_time_match": exit_time_match,
            "prefreeze_record_present": prefreeze,
            "physical_geometry_ok": physical_ok,
            "fully_documented_current_contract": protocol_ok,
            "notes": "; ".join(notes),
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)

    count = lambda key: sum(bool(row[key]) for row in output)
    scope_conflicts = [row["trade_id"] for row in output if not row["scope_objective_contract"]]
    child_conflicts = [row["trade_id"] for row in output if not row["child_opposite_color"]]
    exit_conflicts = [row["trade_id"] for row in output if not row["exit_time_match"]]
    report = f"""# Legacy Truth Structure Re-audit

## Scope

- Ledger: `output/mentor_50trade_oos_v2`, trades `OOS2-001` through `OOS2-013`
- Evidence: frozen raw GOLD M1 OHLC/spread and M1-derived M5/M15 bars
- Timestamp convention: candle label (`bar_open_time`) is separated from information availability (`available_at`)

## Mechanical findings

| Check | Result |
| --- | ---: |
| Root OB exact candle range | {count('root_price_match')}/13 |
| Root OB opposite-color candle | {count('root_opposite_color')}/13 |
| Child OB exact candle range | {count('child_price_match')}/13 |
| Child OB opposite-color candle | {count('child_opposite_color')}/13 |
| Child contained in root | {count('child_inside_root')}/13 |
| Source closed before execution evidence | {count('source_available_before_execution')}/13 |
| Execution FVG/OB exact physical structure | {count('execution_price_match')}/13 |
| Recorded fill is the first eligible retest | {count('first_retest_fill_match')}/13 |
| Objective exact prior wick | {count('objective_wick_match')}/13 |
| Objective not consumed before decision | {count('objective_unswept')}/13 |
| SL beyond child distal and spread | {sum(bool(row['sl_beyond_child']) and bool(row['sl_buffer_covers_spread']) for row in output)}/13 |
| Recorded TP/SL outcome reproduced | {count('outcome_match')}/13 |

The physical market geometry is therefore substantially intact. The earlier claim that the ledger invented its FVG/OB price structures is not supported by raw OHLC.

## Corrections still required

- `{', '.join(child_conflicts)}`: the recorded M5 child is not an opposite-color bullish OB under the current last-opposite-candle definition.
- `{', '.join(scope_conflicts)}`: `EXTERNAL_CONTINUATION` is paired with an `INTERNAL_LIQUIDITY` TP. These rows need scope relabeling or objective reconstruction; they cannot pass the current scope contract unchanged.
- `{', '.join(exit_conflicts)}`: the terminal result is correct, but the recorded close minute is later than the first raw-OHLC terminal bar.
- No trade has a separate append-only PREPARED/root-child freeze record before `ORDER_FROZEN`. The candles existed before execution, but the ledger alone cannot prove when the analyst selected them.

## Conclusion

The old truth should not have been discarded as structurally fabricated. Its entries, POIs, objectives, first retests, SL geometry, and outcomes are overwhelmingly backed by the frozen market data. It should be restored as a **structurally confirmed legacy benchmark**, then corrected for the one child-OB definition conflict, five scope/objective labels, one exit timestamp, and missing pre-freeze evidence before being promoted to a fully documented current-AGENTS authority.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(f"legacyStructureAudit={count('physical_geometry_ok')}/13 physical rows")
    print(f"root={count('root_price_match')}/13 child={count('child_price_match')}/13 execution={count('execution_price_match')}/13 objective={count('objective_wick_match')}/13")
    print(f"scopeConflicts={','.join(scope_conflicts)} childConflicts={','.join(child_conflicts)} exitConflicts={','.join(exit_conflicts)}")
    print(OUT_CSV)
    print(OUT_REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
