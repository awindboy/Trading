from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz, parse_utc


DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
REFERENCE = ROOT / "output" / "mentor_50trade_scope_locked_v1" / "working_trades.csv"
MANUAL_WEEK = ROOT / "output" / "mentor_blind_week_2025-09-01_05_scope_v1" / "manual_orders.jsonl"
OUTPUT = ROOT / "output" / "mentor_sep2025_ea_parity" / "REFERENCE_CONTRACT_AUDIT.json"
REPORT = ROOT / "output" / "mentor_sep2025_ea_parity" / "REFERENCE_CONTRACT_AUDIT.md"


def iso(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def is_bullish(open_price: float, close_price: float) -> bool:
    return close_price > open_price


def close_enough(left: float, right: float, tolerance: float = 0.08) -> bool:
    return abs(left - right) <= tolerance


def candle_index(series, timestamp: int) -> int:
    matches = np.flatnonzero(series.time == timestamp)
    return int(matches[0]) if matches.size else -1


def source_confirmation(series, origin: int, bullish: bool) -> int:
    for index in range(origin + 1, min(len(series), origin + 9)):
        opposite = is_bullish(series.open[index], series.close[index]) != bullish
        if opposite:
            return -1
        if bullish and series.close[index] > series.high[origin]:
            return index
        if not bullish and series.close[index] < series.low[origin]:
            return index
    return -1


def raw_fvgs(series, start: int, end: int, bullish: bool) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for index in range(max(2, start), min(len(series), end + 1)):
        if series.time[index] - series.time[index - 2] != 120:
            continue
        if bullish and series.low[index] > series.high[index - 2]:
            low = float(series.high[index - 2])
            high = float(series.low[index])
        elif not bullish and series.high[index] < series.low[index - 2]:
            low = float(series.high[index])
            high = float(series.low[index - 2])
        else:
            continue
        output.append(
            {
                "formedAt": iso(int(series.time[index])),
                "knownAt": iso(int(series.available_time[index])),
                "low": low,
                "high": high,
                "proximal": high if bullish else low,
            }
        )
    return output


def execution_obs(series, start: int, end: int, bullish: bool) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for origin in range(max(0, start), min(len(series), end + 1)):
        if is_bullish(series.open[origin], series.close[origin]) == bullish:
            continue
        confirmation = source_confirmation(series, origin, bullish)
        if confirmation < 0 or confirmation > end:
            continue
        output.append(
            {
                "formedAt": iso(int(series.time[origin])),
                "knownAt": iso(int(series.available_time[confirmation])),
                "low": float(series.low[origin]),
                "high": float(series.high[origin]),
                "proximal": float(series.high[origin] if bullish else series.low[origin]),
            }
        )
    return output


def prior_level_match(series, decision_index: int, price: float, high_side: bool) -> dict[str, object] | None:
    start = max(2, decision_index - 60 * 24 * 5)
    values = series.high if high_side else series.low
    best: tuple[float, int] | None = None
    for index in range(start, decision_index):
        distance = abs(float(values[index]) - price)
        if best is None or distance < best[0]:
            best = (distance, index)
    if best is None:
        return None
    return {
        "distance": best[0],
        "time": iso(int(series.time[best[1]])),
        "price": float(values[best[1]]),
    }


def main() -> int:
    m1, _ = load_m1_npz(
        DATASET,
        start=parse_utc("2025-08-01T00:00:00Z"),
        end=parse_utc("2025-10-15T00:00:00Z"),
    )
    timeframes = build_timeframes(m1)
    detailed = {
        row["orderId"]: row
        for row in (
            json.loads(line)
            for line in MANUAL_WEEK.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    rows: list[dict[str, object]] = []
    with REFERENCE.open("r", encoding="utf-8-sig", newline="") as handle:
        for reference in csv.DictReader(handle):
            if not reference["decision_at"].startswith("2025-09"):
                continue
            trade_number = int(reference["trade_id"].split("-")[-1])
            weekly_id = f"SCW{trade_number:03d}"
            bullish = reference["direction"] == "long"
            decision = int(parse_utc(reference["decision_at"]) or 0)
            decision_index = int(np.searchsorted(m1.available_time, decision, side="right") - 1)

            root = timeframes[reference["root_tf"]]
            child = timeframes[reference["child_tf"]]
            root_index = candle_index(root, int(parse_utc(reference["root_time"]) or 0))
            child_index = candle_index(child, int(parse_utc(reference["child_time"]) or 0))
            root_direction = bool(
                root_index >= 0
                and is_bullish(root.open[root_index], root.close[root_index]) != bullish
            )
            child_direction = bool(
                child_index >= 0
                and is_bullish(child.open[child_index], child.close[child_index]) != bullish
            )
            root_confirmation = source_confirmation(root, root_index, bullish) if root_index >= 0 else -1
            child_confirmation = source_confirmation(child, child_index, bullish) if child_index >= 0 else -1
            child_low = float(reference["child_low"])
            child_high = float(reference["child_high"])
            root_low = float(reference["root_low"])
            root_high = float(reference["root_high"])
            child_same_bar = bool(
                root_index >= 0
                and child_index >= 0
                and int(root.time[root_index]) <= int(child.time[child_index]) < int(root.time[root_index]) + root.seconds
            )
            child_within_root_displacement = bool(
                root_index >= 0
                and root_confirmation >= 0
                and child_index >= 0
                and int(root.time[root_index])
                <= int(child.time[child_index])
                < int(root.available_time[root_confirmation])
            )
            child_related_price = bool(
                max(root_low, child_low) <= min(root_high, child_high) + 0.08
            )

            search_start = max(0, decision_index - 45)
            search_end = min(len(m1) - 1, decision_index + 1)
            fvgs = raw_fvgs(m1, search_start, search_end, bullish)
            obs = execution_obs(m1, search_start, search_end, bullish)
            entry = float(reference["entry"])
            matching_fvgs = [item for item in fvgs if close_enough(float(item["proximal"]), entry)]
            matching_obs = [item for item in obs if close_enough(float(item["proximal"]), entry)]
            expected_entry_kind = "FVG" if reference["execution_model"] == "DELIVERY_FVG_REPLACEMENT" else "OB"
            entry_match = bool(matching_fvgs if expected_entry_kind == "FVG" else matching_obs)
            objective = float(reference["take_profit"])
            objective_match = prior_level_match(m1, decision_index, objective, high_side=bullish)
            detailed_evidence = detailed.get(weekly_id)

            hard_failures: list[str] = []
            if not root_direction:
                hard_failures.append("ROOT_NOT_OPPOSITE_CANDLE")
            if root_confirmation < 0:
                hard_failures.append("ROOT_RAW_DISPLACEMENT_NOT_RECONSTRUCTED")
            if not child_direction:
                hard_failures.append("CHILD_NOT_SAME_DIRECTION")
            if child_confirmation < 0:
                hard_failures.append("CHILD_RAW_DISPLACEMENT_NOT_RECONSTRUCTED")
            if not child_within_root_displacement:
                hard_failures.append("CHILD_NOT_IN_PARENT_DISPLACEMENT_TIME")
            if not child_related_price:
                hard_failures.append("CHILD_NOT_PRICE_RELATED")
            if not entry_match:
                hard_failures.append(f"{expected_entry_kind}_ENTRY_NOT_RECONSTRUCTED")
            if objective_match is None or float(objective_match["distance"]) > 0.08:
                hard_failures.append("OBJECTIVE_LIQUIDITY_NOT_RECONSTRUCTED")

            rows.append(
                {
                    "tradeId": reference["trade_id"],
                    "direction": reference["direction"],
                    "scope": reference["scope"],
                    "executionModel": reference["execution_model"],
                    "hasFullManualEvidence": detailed_evidence is not None,
                    "rootOppositeCandle": root_direction,
                    "rootRawConfirmationAt": iso(int(root.available_time[root_confirmation])) if root_confirmation >= 0 else None,
                    "childOppositeCandle": child_direction,
                    "childRawConfirmationAt": iso(int(child.available_time[child_confirmation])) if child_confirmation >= 0 else None,
                    "childSameParentFormationBar": child_same_bar,
                    "childWithinParentDisplacement": child_within_root_displacement,
                    "childPriceRelated": child_related_price,
                    "expectedEntryKind": expected_entry_kind,
                    "entryMatches": entry_match,
                    "entryCandidates": matching_fvgs if expected_entry_kind == "FVG" else matching_obs,
                    "objectiveMatch": objective_match,
                    "hardFailures": hard_failures,
                    "contractReconstructible": not hard_failures and detailed_evidence is not None,
                }
            )

    summary = {
        "referenceMonth": "2025-09",
        "tradeCount": len(rows),
        "fullManualEvidenceCount": sum(bool(row["hasFullManualEvidence"]) for row in rows),
        "entryGeometryMatchCount": sum(bool(row["entryMatches"]) for row in rows),
        "zeroHardFailureCount": sum(not row["hardFailures"] for row in rows),
        "fullyReconstructibleCount": sum(bool(row["contractReconstructible"]) for row in rows),
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# September 2025 Reference Contract Audit",
        "",
        f"- Trades: {summary['tradeCount']}",
        f"- Full pre-trade causal evidence: {summary['fullManualEvidenceCount']}",
        f"- Entry geometry reconstructed: {summary['entryGeometryMatchCount']}",
        f"- No hard structural failure: {summary['zeroHardFailureCount']}",
        f"- Fully contract-reconstructible: {summary['fullyReconstructibleCount']}",
        "",
        "| Trade | Model | Full evidence | Entry | Hard failures |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        failures = ", ".join(row["hardFailures"]) if row["hardFailures"] else "-"
        lines.append(
            f"| {row['tradeId']} | {row['executionModel']} | "
            f"{'YES' if row['hasFullManualEvidence'] else 'NO'} | "
            f"{'MATCH' if row['entryMatches'] else 'MISS'} | {failures} |"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
