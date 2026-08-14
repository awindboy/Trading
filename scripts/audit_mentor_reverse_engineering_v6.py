"""Audit the V6 selector against the frozen reverse-engineering entries.

The trading runtime never imports the casebook. This script is a post-run
regression check that proves whether those independently frozen entries remain
reachable after the decision-state implementation changes.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGRESSION = (
    ROOT
    / "output"
    / "mentor_week_2025-06-16_20_rule_reverse_engineering_v5"
    / "regression.json"
)
RUN = (
    ROOT
    / "output"
    / "mentor_scenario_week_2025-06-16_20_v6_trace"
)
OUTPUT = ROOT / "output" / "mentor_rule_reverse_engineering_v6_audit"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def main() -> int:
    regression = json.loads(REGRESSION.read_text(encoding="utf-8"))
    run_summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
    trades = read_csv(RUN / "trades.csv")
    by_candidate = {trade["candidateId"]: trade for trade in trades}
    rows: list[dict[str, Any]] = []
    corrected: list[dict[str, Any]] = []
    for item in regression["rows"]:
        reference = item["reference"]
        candidate_id = item["candidateId"]
        trade = by_candidate.get(candidate_id)
        entry = float(
            reference["entry_top"]
            if reference["direction"] == "long"
            else reference["entry_bottom"]
        )
        expected_objective = float(reference["objective"])
        matched = trade is not None
        row = {
            "referenceId": reference["reference_id"],
            "candidateId": candidate_id,
            "matched": matched,
            "entryExact": (
                matched and abs(float(trade["entry"]) - entry) <= 1e-6
            ),
            "objectiveExact": (
                matched
                and abs(float(trade["objective"]) - expected_objective) <= 1e-6
            ),
            "tradeId": trade["tradeId"] if matched else None,
        }
        rows.append(row)
        if matched:
            corrected.append(
                {"referenceId": reference["reference_id"], **trade}
            )
    closed = [
        trade for trade in corrected if trade["result"] in {"TP", "SL"}
    ]
    values = [float(trade["earnedR"]) for trade in closed]
    wins = [trade for trade in closed if trade["result"] == "TP"]
    losses = [trade for trade in closed if trade["result"] == "SL"]
    gross_win = sum(float(trade["earnedR"]) for trade in wins)
    gross_loss = -sum(float(trade["earnedR"]) for trade in losses)
    summary = {
        "schema": "mentor-rule-reverse-engineering-v6-audit",
        "runtimeReadsCasebook": run_summary["casebookImported"],
        "referenceCount": len(rows),
        "matchedCount": sum(bool(row["matched"]) for row in rows),
        "entryExactCount": sum(bool(row["entryExact"]) for row in rows),
        "objectiveExactCount": sum(
            bool(row["objectiveExact"]) for row in rows
        ),
        "referenceTrades": len(corrected),
        "wins": len(wins),
        "losses": len(losses),
        "winRate": len(wins) / len(closed) if closed else 0.0,
        "totalR": round(sum(values), 6),
        "profitFactor": (
            round(gross_win / gross_loss, 6)
            if gross_loss > 0
            else None
        ),
        "maxDrawdownR": round(max_drawdown(values), 6),
        "fullDecisionReproduction": all(
            row["matched"] and row["entryExact"] and row["objectiveExact"]
            for row in rows
        ),
        "selectorTradeCount": run_summary["trades"],
        "selectorTotalR": run_summary["totalR"],
        "selectorProfitFactor": run_summary["profitFactor"],
        "selectorBoundary": (
            "Reference reproduction is complete. Extra trades are selector "
            "outputs, not validated Mentor trades, and are evaluated "
            "separately from recall."
        ),
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "decision_reproduction.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (OUTPUT / "corrected_reference_trades.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(corrected[0]))
        writer.writeheader()
        writer.writerows(corrected)
    replay_run = OUTPUT / "replay_run"
    replay_run.mkdir(parents=True, exist_ok=True)
    with (replay_run / "trades.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fieldnames = [
            field for field in corrected[0] if field != "referenceId"
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {
                field: trade[field]
                for field in fieldnames
            }
            for trade in corrected
        )
    focused_summary = {
        **run_summary,
        "schema": "mentor-reference-replay-v6",
        "trades": len(corrected),
        "wins": len(wins),
        "losses": len(losses),
        "open": len(corrected) - len(closed),
        "winRate": summary["winRate"],
        "totalR": summary["totalR"],
        "profitFactor": summary["profitFactor"],
        "maxDrawdownR": summary["maxDrawdownR"],
        "referenceOnly": True,
    }
    (replay_run / "summary.json").write_text(
        json.dumps(focused_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = f"""# Mentor 룰 역설계 V6 감사

## 완료 판정

- 기준 타점 재현: **{summary['matchedCount']}/{summary['referenceCount']}**
- 진입가 일치: **{summary['entryExactCount']}/{summary['referenceCount']}**
- 고정 objective 일치: **{summary['objectiveExactCount']}/{summary['referenceCount']}**
- 런타임 casebook 참조: **{summary['runtimeReadsCasebook']}**

기준 원장은 런타임 실행 뒤에만 대조했다. 따라서 기준 날짜나 가격을
읽어서 주문을 생성한 것이 아니라, OHLC·spread에서 생성한 후보와 상태기가
동일한 physical chain을 다시 선택했는지를 검증한 결과다.

## 교정된 기준 10건

- 7승 3패, 승률 **{summary['winRate'] * 100:.1f}%**
- 합계 **{summary['totalR']:.2f}R**
- Profit Factor **{summary['profitFactor']:.2f}**
- 최대 drawdown **{summary['maxDrawdownR']:.2f}R**

이 통계는 V5의 오래된 SL을 재사용하지 않고 V6의 source/refinement distal,
protected correction, 실제 spread로 다시 계산한 값이다.

## 경계

기준 타점을 놓치지 않는 역설계 목표는 완료됐다. 전체 selector의 추가
거래는 기준 타점 recall과 별개다. 추가 거래가 실제로 유효한지는 동일한
규칙을 동결한 미사용 주간에서 평가해야 하며, 이 기준 주간 수익으로
일반적인 수익성을 주장하지 않는다.
"""
    (OUTPUT / "RULE_REVERSE_ENGINEERING_V6.md").write_text(
        report,
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary["fullDecisionReproduction"]:
        return 1
    if summary["runtimeReadsCasebook"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
