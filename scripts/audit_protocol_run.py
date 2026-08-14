from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mentor_ai_replay import parse_utc
from scripts.mentor_replay_v2 import compact_bars


TF_SECONDS = {"H1": 3600, "M30": 1800, "M15": 900, "M5": 300, "M1": 60}


def run_chain(run_id: str) -> list[Path]:
    runs: list[Path] = []
    seen: set[str] = set()
    current = run_id
    while current and current not in seen:
        seen.add(current)
        run = ROOT / "output" / "mentor_ai_replay_runs" / current
        if not run.exists():
            raise FileNotFoundError(run)
        runs.append(run)
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8-sig"))
        current = str(manifest.get("resumedFrom") or "")
    return list(reversed(runs))


def decisions_with_orders(chain: list[Path]) -> list[dict[str, Any]]:
    selected: dict[tuple[str, str, float], dict[str, Any]] = {}
    for run in chain:
        ledger = run / "decision_ledger.jsonl"
        if not ledger.exists():
            continue
        for line in ledger.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            decision = record.get("decision")
            order = decision.get("order") if isinstance(decision, dict) else None
            if record.get("event") != "AI_DECISION" or not isinstance(order, dict):
                continue
            key = (
                str(record.get("asOfUtc")), str(record.get("phase")),
                round(float(order.get("entry", 0.0)), 5),
            )
            selected[key] = record
    return list(selected.values())


def row_at(bars: dict[str, list[dict[str, Any]]], tf: str, time_text: str) -> dict[str, Any] | None:
    target = parse_utc(time_text)
    return next(
        (row for row in bars.get(tf, []) if int(str(row["barId"]).split(":", 1)[1]) == target),
        None,
    )


def m1_at(rates: np.ndarray, time_text: str) -> np.void | None:
    target = parse_utc(time_text)
    found = np.flatnonzero(rates["time"] == target)
    return rates[int(found[0])] if len(found) else None


def body_delivered(
    bars: dict[str, list[dict[str, Any]]], tf: str, origin: dict[str, Any],
    direction: str, known_by: int,
) -> bool:
    origin_time = int(str(origin["barId"]).split(":", 1)[1])
    origin_close = origin_time + TF_SECONDS[tf]
    ladder = ["H1", "M30", "M15", "M5", "M1"]
    for delivery_tf in ladder[ladder.index(tf):]:
        for row in bars.get(delivery_tf, []):
            row_time = int(str(row["barId"]).split(":", 1)[1])
            if row_time < origin_close or row_time + TF_SECONDS[delivery_tf] > known_by:
                continue
            if direction == "long" and float(row["c"]) > float(origin["h"]):
                return True
            if direction == "short" and float(row["c"]) < float(origin["l"]):
                return True
    return False


def first_touch_index(
    rates: np.ndarray, start: int, end: int, low: float, high: float,
) -> int | None:
    for index in range(start, end + 1):
        if float(rates[index]["high"]) >= low and float(rates[index]["low"]) <= high:
            return index
    return None


def audit_trade(
    trade: dict[str, str], record: dict[str, Any], rates: np.ndarray,
    dataset: Path, warmup: str, point: float,
) -> dict[str, Any]:
    errors: list[str] = []
    decision = record["decision"]
    scenario = decision["scenario"]
    order = decision["order"]
    direction = str(trade["direction"]).lower()
    decision_time = parse_utc(trade["decision_at"])
    frozen_time = parse_utc(str(scenario["frozenAtUtc"]))
    bars = compact_bars(
        dataset, warmup, trade["decision_at"],
        limits={"H1": 240, "M30": 480, "M15": 960, "M5": 2880, "M1": 6000},
    )
    root = row_at(bars, str(scenario["rootOb"]["tf"]), str(scenario["rootOb"]["originTime"]))
    child_info = (scenario.get("refinementPath") or [None])[-1]
    child = (
        row_at(bars, str(child_info["tf"]), str(child_info["originTime"]))
        if isinstance(child_info, dict) else None
    )
    objective = row_at(
        bars, str(scenario["objective"]["sourceTf"]),
        str(scenario["objective"]["sourceTime"]),
    )
    if root is None:
        errors.append("ROOT_OHLC_MISSING")
    else:
        root_opposite = (
            float(root["c"]) < float(root["o"])
            if direction == "long" else float(root["c"]) > float(root["o"])
        )
        if not root_opposite:
            errors.append("ROOT_NOT_OPPOSITE_CANDLE")
        if not body_delivered(bars, str(scenario["rootOb"]["tf"]), root, direction, frozen_time):
            errors.append("ROOT_BODY_DELIVERY_NOT_KNOWN_AT_FREEZE")
    if child is None:
        errors.append("CHILD_OHLC_MISSING")
    else:
        child_opposite = (
            float(child["c"]) < float(child["o"])
            if direction == "long" else float(child["c"]) > float(child["o"])
        )
        if not child_opposite:
            errors.append("CHILD_NOT_OPPOSITE_CANDLE")
        if not body_delivered(bars, str(child_info["tf"]), child, direction, decision_time):
            errors.append("CHILD_BODY_DELIVERY_MISSING")
    if objective is None:
        errors.append("OBJECTIVE_OHLC_MISSING")
    else:
        objective_price = float(scenario["objective"]["price"])
        expected = float(objective["h"] if direction == "long" else objective["l"])
        if abs(objective_price - expected) > point:
            errors.append("OBJECTIVE_NOT_SOURCE_WICK")
        start = int(np.searchsorted(rates["time"], frozen_time, side="left"))
        end = int(np.searchsorted(rates["time"] + 60, decision_time, side="right")) - 1
        if end >= start:
            reached = (
                np.any(rates[start:end + 1]["high"] >= objective_price)
                if direction == "long"
                else np.any(rates[start:end + 1]["low"] <= objective_price)
            )
            if reached:
                errors.append("OBJECTIVE_REACHED_BEFORE_ORDER")
    execution_model = str(order["executionModel"])
    if execution_model == "HTF_OB_REACTION":
        touch_time = parse_utc(str(order.get("refinedTouchTimeUtc")))
        if touch_time < frozen_time:
            errors.append("CHILD_TOUCH_BEFORE_MAP_FREEZE")
        if child is not None:
            touch_row = m1_at(rates, str(order.get("refinedTouchTimeUtc")))
            if touch_row is None or not (
                float(touch_row["high"]) >= float(child["l"])
                and float(touch_row["low"]) <= float(child["h"])
            ):
                errors.append("CHILD_TOUCH_NOT_OHLC_BACKED")

        mature_time = parse_utc(str(order.get("matureLiquiditySourceTimeUtc")))
        sweep_time = parse_utc(str(order.get("sweepExtremeSourceTimeUtc")))
        recovery_time = parse_utc(str(order.get("sweepRecoveryTimeUtc")))
        reference_time = parse_utc(str(order.get("chochReferenceSourceTimeUtc")))
        break_time = parse_utc(str(order.get("chochBreakTimeUtc")))
        if not (mature_time < touch_time <= sweep_time <= recovery_time < break_time < decision_time
                and touch_time <= reference_time < break_time):
            errors.append("TRIGGER_CHRONOLOGY_INVALID")
        mature = m1_at(rates, str(order.get("matureLiquiditySourceTimeUtc")))
        sweep = m1_at(rates, str(order.get("sweepExtremeSourceTimeUtc")))
        recovery = m1_at(rates, str(order.get("sweepRecoveryTimeUtc")))
        reference = m1_at(rates, str(order.get("chochReferenceSourceTimeUtc")))
        breaker = m1_at(rates, str(order.get("chochBreakTimeUtc")))
        execution = m1_at(rates, str(order.get("executionOriginTime")))
        if any(row is None for row in (mature, sweep, recovery, reference, breaker, execution)):
            errors.append("TRIGGER_OHLC_MISSING")
        else:
            liquidity = float(order["matureLiquidityPrice"])
            if direction == "short":
                if abs(liquidity - float(mature["high"])) > point:
                    errors.append("MATURE_BSL_NOT_SOURCE_HIGH")
                if float(sweep["high"]) <= liquidity or float(recovery["close"]) >= liquidity:
                    errors.append("SHORT_SWEEP_RECOVERY_INVALID")
                if abs(float(order["chochReferencePrice"]) - float(reference["low"])) > point:
                    errors.append("SHORT_CHOCH_REFERENCE_INVALID")
                if float(breaker["close"]) >= float(reference["low"]):
                    errors.append("SHORT_CHOCH_BODY_BREAK_MISSING")
                if float(execution["close"]) <= float(execution["open"]):
                    errors.append("SHORT_EXECUTION_OB_NOT_BULLISH")
            else:
                if abs(liquidity - float(mature["low"])) > point:
                    errors.append("MATURE_SSL_NOT_SOURCE_LOW")
                if float(sweep["low"]) >= liquidity or float(recovery["close"]) <= liquidity:
                    errors.append("LONG_SWEEP_RECOVERY_INVALID")
                if abs(float(order["chochReferencePrice"]) - float(reference["high"])) > point:
                    errors.append("LONG_CHOCH_REFERENCE_INVALID")
                if float(breaker["close"]) <= float(reference["high"]):
                    errors.append("LONG_CHOCH_BODY_BREAK_MISSING")
                if float(execution["close"]) >= float(execution["open"]):
                    errors.append("LONG_EXECUTION_OB_NOT_BEARISH")

    delivery_boundary: float | None = None
    delivery_protected: float | None = None
    if execution_model == "DELIVERY_FVG_REPLACEMENT":
        left = m1_at(rates, str(order.get("deliveryFvgLeftTimeUtc")))
        middle = m1_at(rates, str(order.get("deliveryFvgMiddleTimeUtc")))
        right = m1_at(rates, str(order.get("deliveryFvgRightTimeUtc")))
        if any(row is None for row in (left, middle, right)):
            errors.append("FVG_OHLC_MISSING")
        else:
            if direction == "long":
                zone_low, zone_high = float(left["high"]), float(right["low"])
                valid_gap = zone_low < zone_high
                expected_entry = zone_high
            else:
                zone_low, zone_high = float(right["high"]), float(left["low"])
                valid_gap = zone_low < zone_high
                expected_entry = zone_low
            if not valid_gap:
                errors.append("NO_THREE_CANDLE_WICK_GAP")
            if max(
                abs(zone_low - float(order["deliveryFvgLow"])),
                abs(zone_high - float(order["deliveryFvgHigh"])),
                abs(expected_entry - float(order["entry"])),
            ) > point:
                errors.append("FVG_ZONE_OR_ENTRY_MISMATCH")
            left_time = parse_utc(str(order["deliveryFvgLeftTimeUtc"]))
            if frozen_time >= left_time:
                errors.append("LINEAGE_NOT_FROZEN_BEFORE_DELIVERY")
            causal = m1_at(rates, str(order.get("deliveryCausalObTimeUtc")))
            protected = m1_at(rates, str(order.get("deliveryProtectedSwingTimeUtc")))
            if causal is None or protected is None:
                errors.append("DELIVERY_CAUSAL_EVIDENCE_MISSING")
            else:
                delivery_boundary = float(causal["low"] if direction == "long" else causal["high"])
                delivery_protected = float(order["deliveryProtectedSwing"])
                # This field is the swing crossed by delivery, not the SL-side
                # invalidation swing: long crosses a high and short crosses a low.
                expected_protected = float(protected["high"] if direction == "long" else protected["low"])
                if abs(delivery_protected - expected_protected) > point:
                    errors.append("DELIVERY_PROTECTED_SWING_NOT_OHLC_BACKED")
                causal_opposite = (
                    float(causal["close"]) < float(causal["open"])
                    if direction == "long" else float(causal["close"]) > float(causal["open"])
                )
                if not causal_opposite:
                    errors.append("DELIVERY_CAUSAL_OB_NOT_OPPOSITE")
                delivered = (
                    max(float(middle["close"]), float(right["close"])) > delivery_protected
                    if direction == "long"
                    else min(float(middle["close"]), float(right["close"])) < delivery_protected
                )
                if not delivered:
                    errors.append("DELIVERY_BODY_STRUCTURE_TRANSFER_MISSING")

    spread = max(float(order.get("actualSpread", 0.0)), point)
    if child is not None:
        if direction == "long":
            components = [float(child["l"])]
            if execution_model == "HTF_OB_REACTION":
                components.append(float(order["sweepExtreme"]))
            if delivery_boundary is not None:
                components.append(delivery_boundary)
            boundary = min(components)
            if float(order["stopLoss"]) > boundary - spread + point:
                errors.append("LONG_SL_NOT_OUTSIDE_STRUCTURE")
        else:
            components = [float(child["h"])]
            if execution_model == "HTF_OB_REACTION":
                components.append(float(order["sweepExtreme"]))
            if delivery_boundary is not None:
                components.append(delivery_boundary)
            boundary = max(components)
            if float(order["stopLoss"]) < boundary + spread - point:
                errors.append("SHORT_SL_NOT_OUTSIDE_STRUCTURE")
    if abs(float(order["takeProfit"]) - float(scenario["objective"]["price"])) > point:
        errors.append("TP_CHANGED_FROM_OBJECTIVE")
    if parse_utc(trade["filled_at"]) <= decision_time:
        errors.append("FILL_NOT_AFTER_DECISION")
    fill_start = int(np.searchsorted(rates["time"] + 60, decision_time, side="right"))
    fill_end = int(np.searchsorted(rates["time"] + 60, parse_utc(trade["filled_at"]), side="right")) - 1
    first = first_touch_index(
        rates, fill_start, fill_end, float(order["entry"]), float(order["entry"])
    ) if fill_end >= fill_start else None
    if first is None or int(rates[first]["time"]) + 60 != parse_utc(trade["filled_at"]):
        errors.append("FILL_NOT_FIRST_POST_DECISION_RETEST")
    return {
        "trade_id": trade["trade_id"], "status": "PASS" if not errors else "FAIL",
        "errors": errors, "decision_at": trade["decision_at"],
        "direction": direction, "execution_model": order["executionModel"],
        "entry": float(order["entry"]), "sl": float(order["stopLoss"]),
        "tp": float(order["takeProfit"]), "r": float(trade["r"]),
        "scenario": scenario, "order": order,
    }


def truth_bar(bars: dict[str, list[dict[str, Any]]], tf: str, time_text: str) -> dict[str, Any]:
    row = row_at(bars, tf, time_text)
    if row is None:
        raise ValueError(f"truth OHLC missing: {tf} {time_text}")
    return {
        "barId": row["barId"], "timeUtc": time_text,
        "ohlc": {key: float(row[key]) for key in ("o", "h", "l", "c")},
    }


def build_truth(
    audits: list[dict[str, Any]], trades: list[dict[str, str]], dataset: Path,
    warmup: str, start_utc: str, end_utc: str,
) -> dict[str, Any]:
    trade_by_id = {row["trade_id"]: row for row in trades}
    benchmarks: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for audit in audits:
        if audit["status"] != "PASS":
            excluded.append({
                "tradeId": audit["trade_id"],
                "reasonCode": ";".join(audit["errors"]),
                "reason": "Codex replay order failed the frozen AGENTS.md protocol audit.",
            })
            continue
        scenario, order = audit["scenario"], audit["order"]
        bars = compact_bars(
            dataset, warmup, audit["decision_at"],
            limits={"H1": 240, "M30": 480, "M15": 960, "M5": 2880, "M1": 6000},
        )
        root_tf = str(scenario["rootOb"]["tf"])
        root_time = str(scenario["rootOb"]["originTime"])
        objective_tf = str(scenario["objective"]["sourceTf"])
        objective_time = str(scenario["objective"]["sourceTime"])
        path = []
        for child in scenario["refinementPath"]:
            payload = truth_bar(bars, str(child["tf"]), str(child["originTime"]))
            path.append(payload)
        benchmark = {
            "tradeId": audit["trade_id"],
            "minimumClassification": "CAUSAL_MATCH",
            "map": {
                "decisionTimeUtc": str(scenario["frozenAtUtc"]),
                "direction": str(scenario["direction"]),
                "scope": str(scenario["scope"]),
                "root": truth_bar(bars, root_tf, root_time),
                "objective": {
                    **truth_bar(bars, objective_tf, objective_time),
                    "side": str(scenario["objective"]["side"]),
                    "price": float(scenario["objective"]["price"]),
                },
            },
            "refinement": {
                "path": path,
                "touchBarId": str(order["refinedTouchBarId"]),
                "touchTimeUtc": str(order["refinedTouchTimeUtc"]),
            },
            "triggerAudit": {
                "protectedSwingTimeUtc": str(order["triggerProtectedSwingSourceTimeUtc"]),
                "matureLiquidityTimeUtc": str(order["matureLiquiditySourceTimeUtc"]),
                "matureLiquidityPrice": float(order["matureLiquidityPrice"]),
                "sweepTimeUtc": str(order["sweepExtremeSourceTimeUtc"]),
                "sweepExtreme": float(order["sweepExtreme"]),
                "sweepRecoveryTimeUtc": str(order["sweepRecoveryTimeUtc"]),
                "chochReferenceTimeUtc": str(order["chochReferenceSourceTimeUtc"]),
                "chochReferencePrice": float(order["chochReferencePrice"]),
                "chochBreakTimeUtc": str(order["chochBreakTimeUtc"]),
                "executionTimeUtc": str(order["executionOriginTime"]),
                "status": "AGENTS_CONTRACT_SUPPORTED",
            },
            "order": {
                "executionModel": str(order["executionModel"]),
                "entry": float(order["entry"]),
                "stopLoss": float(order["stopLoss"]),
                "takeProfit": float(order["takeProfit"]),
                "spreadPrice": float(order["actualSpread"]),
                "brokerStopsLevelPrice": float(order["brokerStopsLevelPrice"]),
            },
            "result": {
                "outcome": str(trade_by_id[audit["trade_id"]]["outcome"]),
                "r": float(trade_by_id[audit["trade_id"]]["r"]),
            },
        }
        benchmarks.append(benchmark)
    return {
        "schemaVersion": "3.0.0", "authority": "AGENTS.md",
        "sourceRun": "Codex same-pipeline blind replay plus raw-OHLC protocol audit",
        "period": {"startUtc": start_utc, "endUtc": end_utc},
        "executableBenchmarks": benchmarks, "excludedRecords": excluded,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    chain = run_chain(args.run_id)
    final_run = chain[-1]
    manifest = json.loads((final_run / "manifest.json").read_text(encoding="utf-8-sig"))
    secret = json.loads(
        (ROOT / "data" / "mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )["config"]
    dataset = ROOT / str(manifest["dataset"])
    rates = np.load(dataset, allow_pickle=True)["rates"]
    trades = list(csv.DictReader((final_run / "trades.csv").open(encoding="utf-8-sig")))
    orders = decisions_with_orders(chain)
    audits = []
    for trade in trades:
        matches = [
            record for record in orders
            if str(record.get("asOfUtc")) == trade["decision_at"]
            and abs(float(record["decision"]["order"]["entry"]) - float(trade["entry"])) <= float(secret["point"])
        ]
        if not matches:
            audits.append({"trade_id": trade["trade_id"], "status": "FAIL", "errors": ["FINAL_ORDER_RECORD_MISSING"]})
            continue
        audits.append(audit_trade(
            trade, matches[-1], rates, dataset, str(secret["warmupStartUtc"]),
            float(secret["point"]),
        ))
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    (output / "protocol_audit.json").write_text(
        json.dumps(audits, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (output / "protocol_audit.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["trade_id", "status", "errors", "decision_at", "direction", "execution_model", "entry", "sl", "tp", "r"])
        for row in audits:
            writer.writerow([
                row["trade_id"], row["status"], ";".join(row["errors"]),
                row.get("decision_at", ""), row.get("direction", ""),
                row.get("execution_model", ""), row.get("entry", ""),
                row.get("sl", ""), row.get("tp", ""), row.get("r", ""),
            ])
    truth = build_truth(
        audits, trades, dataset, str(secret["warmupStartUtc"]),
        str(manifest["replayStartUtc"]), str(manifest["replayEndUtc"]),
    )
    (output / "funnel_truth.json").write_text(
        json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    passed_ids = {row["trade_id"] for row in audits if row["status"] == "PASS"}
    with (output / "trades.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
        writer.writeheader()
        writer.writerows(row for row in trades if row["trade_id"] in passed_ids)
    passed = sum(row["status"] == "PASS" for row in audits)
    print(f"PROTOCOL_AUDIT pass={passed} fail={len(audits) - passed} total={len(audits)}")
    for row in audits:
        print(row["trade_id"], row["status"], ",".join(row["errors"]))
    return 0 if passed == len(audits) else 1


if __name__ == "__main__":
    raise SystemExit(main())
