from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_utc(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_ledger(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "decision_ledger.jsonl"
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def enrich_trades(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions: dict[str, list[dict[str, Any]]] = {}
    for row in ledger:
        if row.get("event") != "AI_DECISION":
            continue
        decision = row.get("decision") or {}
        if decision.get("action") == "ORDER" and isinstance(decision.get("order"), dict):
            decisions.setdefault(str(row.get("asOfUtc")), []).append(decision)

    trades: list[dict[str, Any]] = []
    for row in ledger:
        if row.get("event") != "TRADE_CLOSED":
            continue
        trade = dict(row["trade"])
        matching = decisions.get(str(trade.get("decision_at")), [])
        decision = next(
            (
                item for item in reversed(matching)
                if item.get("order", {}).get("executionModel")
                == trade.get("execution_model")
            ),
            matching[-1] if matching else {},
        )
        scenario = decision.get("scenario") or {}
        order = decision.get("order") or {}
        children = scenario.get("refinementPath") or []
        child = children[-1] if children else {}
        trade.update({
            "root_time": (scenario.get("rootOb") or {}).get("originTime"),
            "root_low": (scenario.get("rootOb") or {}).get("low"),
            "root_high": (scenario.get("rootOb") or {}).get("high"),
            "child_time": child.get("originTime"),
            "child_low": child.get("low"),
            "child_high": child.get("high"),
            "objective_type": (scenario.get("objective") or {}).get("type"),
            "fvg_left": order.get("deliveryFvgLeftTimeUtc"),
            "fvg_middle": order.get("deliveryFvgMiddleTimeUtc"),
            "fvg_right": order.get("deliveryFvgRightTimeUtc"),
            "causal_ob": order.get("deliveryCausalObTimeUtc"),
            "protected_swing": order.get("deliveryProtectedSwingTimeUtc"),
        })
        trades.append(trade)
    return trades


def number(row: dict[str, Any], *keys: str) -> float:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return float(value)
    return math.nan


def same_time(left: Any, right: Any) -> bool:
    return bool(left and right and str(left) == str(right))


def classify(expected: dict[str, Any], actual: dict[str, Any], point: float) -> str:
    direction_match = str(expected["direction"]).lower() == str(actual["direction"]).lower()
    root_match = (
        str(expected.get("root_tf")) == str(actual.get("root_tf"))
        and same_time(expected.get("root_time"), actual.get("root_time"))
    )
    child_match = (
        str(expected.get("child_tf")) == str(actual.get("child_tf"))
        and same_time(expected.get("child_time"), actual.get("child_time"))
    )
    execution_match = str(expected.get("execution_model")) == str(actual.get("execution_model"))
    entry_match = abs(number(expected, "entry") - number(actual, "entry")) <= point
    tp_match = abs(number(expected, "take_profit", "tp") - number(actual, "tp")) <= point
    sl_match = abs(number(expected, "stop_loss", "sl") - number(actual, "sl")) <= point
    if all((direction_match, root_match, child_match, execution_match, entry_match, tp_match, sl_match)):
        return "EXACT"
    if all((direction_match, root_match, child_match, execution_match, entry_match, tp_match)):
        return "CAUSAL_MATCH"
    if direction_match:
        return "DIRECTION_ONLY"
    return "MISMATCH"


def stage_counts(ledger: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in ledger:
        if row.get("event") != "AI_DECISION":
            continue
        decision = row.get("decision") or {}
        key = f"{row.get('phase')}:{decision.get('action')}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def compare_run(
    truth: list[dict[str, Any]],
    run_dir: Path,
    *,
    window_seconds: int,
    point: float,
) -> dict[str, Any]:
    ledger = read_ledger(run_dir)
    candidates = enrich_trades(ledger)
    unmatched = set(range(len(candidates)))
    parity: list[dict[str, Any]] = []
    for expected in truth:
        expected_time = parse_utc(str(expected["decision_at"]))
        options = [
            (abs(parse_utc(str(candidates[index]["decision_at"])) - expected_time), index)
            for index in unmatched
            if str(candidates[index]["direction"]).lower()
            == str(expected["direction"]).lower()
            and abs(parse_utc(str(candidates[index]["decision_at"])) - expected_time)
            <= window_seconds
        ]
        if not options:
            parity.append({
                "truth_id": expected["trade_id"], "candidate_id": "",
                "classification": "MISS", "truth_time": expected["decision_at"],
                "candidate_time": "", "time_delta_minutes": "",
            })
            continue
        delta, selected = min(options)
        unmatched.remove(selected)
        actual = candidates[selected]
        parity.append({
            "truth_id": expected["trade_id"],
            "candidate_id": actual["trade_id"],
            "classification": classify(expected, actual, point),
            "truth_time": expected["decision_at"],
            "candidate_time": actual["decision_at"],
            "time_delta_minutes": delta / 60,
            "truth_entry": expected["entry"], "candidate_entry": actual["entry"],
            "truth_sl": expected["stop_loss"], "candidate_sl": actual["sl"],
            "truth_tp": expected["take_profit"], "candidate_tp": actual["tp"],
            "root_match": same_time(expected.get("root_time"), actual.get("root_time")),
            "child_match": same_time(expected.get("child_time"), actual.get("child_time")),
        })
    extras = [candidates[index] for index in sorted(unmatched)]
    summary_path = run_dir / "summary.json"
    summary = (
        json.loads(summary_path.read_text(encoding="utf-8-sig"))
        if summary_path.exists() else {}
    )
    return {
        "runId": run_dir.name,
        "summary": summary,
        "parity": parity,
        "extras": extras,
        "stageCounts": stage_counts(ledger),
    }


def write_outputs(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    parity_path = output_dir / "parity.csv"
    fieldnames = sorted({key for row in result["parity"] for key in row})
    with parity_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result["parity"])

    counts: dict[str, int] = {}
    for row in result["parity"]:
        label = str(row["classification"])
        counts[label] = counts.get(label, 0) + 1
    lines = [
        f"# Replay parity audit: {result['runId']}", "",
        "## Status", "",
        f"- Completed: `{result['summary'].get('completed', False)}`",
        f"- Stopped reason: `{result['summary'].get('stoppedReason', 'UNKNOWN')}`",
        f"- Candidate trades: `{result['summary'].get('trades', len(result['extras']))}`",
        f"- Parity: `{json.dumps(counts, ensure_ascii=False, sort_keys=True)}`",
        f"- Extra trades: `{len(result['extras'])}`", "",
        "## Truth parity", "",
        "| Truth | Candidate | Class | Truth time | Candidate time |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["parity"]:
        lines.append(
            f"| {row['truth_id']} | {row['candidate_id'] or '-'} | "
            f"{row['classification']} | {row['truth_time']} | {row['candidate_time'] or '-'} |"
        )
    lines.extend(["", "## Extra trades", ""])
    for trade in result["extras"]:
        lines.append(
            f"- `{trade['trade_id']}` {trade['decision_at']} {trade['direction']} "
            f"{trade['execution_model']} entry={trade['entry']} sl={trade['sl']} "
            f"tp={trade['tp']} result={trade['outcome']} R={float(trade['r']):.4f}"
        )
    lines.extend(["", "## Stage counts", ""])
    for key, value in sorted(result["stageCounts"].items()):
        lines.append(f"- `{key}`: {value}")
    (output_dir / "PARITY_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    (output_dir / "audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--window-hours", type=float, default=2.0)
    parser.add_argument("--point", type=float, default=0.01)
    args = parser.parse_args()
    result = compare_run(
        read_csv(args.truth), args.run_dir,
        window_seconds=int(args.window_hours * 3600), point=args.point,
    )
    write_outputs(result, args.output_dir)
    print(json.dumps({
        "runId": result["runId"],
        "parity": {
            label: sum(1 for row in result["parity"] if row["classification"] == label)
            for label in ("EXACT", "CAUSAL_MATCH", "DIRECTION_ONLY", "MISS", "MISMATCH")
        },
        "extras": len(result["extras"]),
        "output": str(args.output_dir),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
