"""Verify the frozen mentor rule contract against the June 16-20 casebook.

The casebook is a regression oracle only. MentorRuleEngine receives raw OHLC
and never imports reference IDs, dates, entry prices, or outcomes.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz, parse_utc
from mentor_rule_engine import MentorRuleEngine
from mentor_rule_engine.regression import ReferenceSetup, compare_reference_setups


DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
CASEBOOK = (
    ROOT
    / "research"
    / "ict-system"
    / "mentor_week_2025-06-16_20_reverse_casebook_v5.json"
)
OUTPUT = ROOT / "output" / "mentor_week_2025-06-16_20_rule_reverse_engineering_v5"
POINT = 0.01


def timestamp(value: str) -> int:
    result = parse_utc(value)
    if result is None:
        raise ValueError(value)
    return result


def iso(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def load_casebook() -> dict[str, Any]:
    return json.loads(CASEBOOK.read_text(encoding="utf-8"))


def references(casebook: dict[str, Any]) -> list[ReferenceSetup]:
    return [
        ReferenceSetup(
            reference_id=row["referenceId"],
            direction=row["direction"],
            created_at=timestamp(row["createdAt"]),
            entry_bottom=float(row["entryZone"][0]),
            entry_top=float(row["entryZone"][1]),
            source_bottom=float(row["sourceZone"][0]),
            source_top=float(row["sourceZone"][1]),
            sweep_at=timestamp(row["sweepAt"]),
            objective=float(row["objective"]),
        )
        for row in casebook["references"]
    ]


def simulate(m1: Any, row: dict[str, Any]) -> dict[str, Any]:
    decision = timestamp(row["decisionAt"])
    start = int(np.searchsorted(m1.time, decision, side="left"))
    entry = float(row["entry"])
    stop = float(row["stop"])
    target = float(row["objective"])
    filled_at: int | None = None
    closed_at: int | None = None
    result = "UNFILLED"
    ambiguous = False
    for index in range(start, len(m1)):
        spread = max(POINT, float(m1.spread_points[index]) * POINT)
        bid_low = float(m1.low[index])
        bid_high = float(m1.high[index])
        ask_low = bid_low + spread
        ask_high = bid_high + spread
        available_at = int(m1.available_time[index])
        if filled_at is None:
            touched = (
                ask_low <= entry <= ask_high
                if row["direction"] == "long"
                else bid_low <= entry <= bid_high
            )
            if not touched:
                continue
            filled_at = available_at
        if row["direction"] == "long":
            stop_hit = bid_low <= stop
            target_hit = bid_high >= target
        else:
            stop_hit = ask_high >= stop
            target_hit = ask_low <= target
        if stop_hit or target_hit:
            ambiguous = stop_hit and target_hit
            result = "SL" if stop_hit else "TP"
            closed_at = available_at
            break
    planned_r = abs((target - entry) / (entry - stop))
    earned_r = -1.0 if result == "SL" else planned_r if result == "TP" else 0.0
    return {
        "tradeId": row["referenceId"],
        "legacyId": row["legacyId"],
        "direction": row["direction"],
        "entryModel": row["entryModel"],
        "decisionAt": row["decisionAt"],
        "filledAt": iso(filled_at),
        "closedAt": iso(closed_at),
        "entry": entry,
        "stop": stop,
        "objective": target,
        "result": result,
        "ambiguous": ambiguous,
        "plannedR": round(planned_r, 6),
        "earnedR": round(earned_r, 6),
        "holdingMinutes": (
            int((closed_at - filled_at) / 60)
            if filled_at is not None and closed_at is not None
            else None
        ),
    }


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def contract() -> dict[str, Any]:
    return {
        "schema": "mentor-rule-contract-v5",
        "status": "FROZEN_FOR_BLIND_REPLAY",
        "source": [
            "M15/M5 last opposite candle before its confirming displacement",
            "earlier same-colour candles in the displacement leg are not OBs",
            "M5 replaces M15 only when it is the unique nested source touched",
        ],
        "reaction": [
            "group consecutive reclaimed pivots into one physical sweep episode",
            "use the furthest reclaimed level inside the latest episode",
            "wick breach without close recovery is not a sweep",
        ],
        "trigger": [
            "M1 only",
            "body-close CHoCH through a confirmed pivot or the latest live opposite body origin",
            "fresh three-candle wick FVG created after the shift",
            "entry at FVG proximal boundary on a later tradable bar",
        ],
        "state": [
            "a stopped execution does not kill its HTF owner",
            "rearm requires a new sweep, shift, FVG, and retest",
            "delivery add-on requires a new protected correction and FVG",
            "delivery add-ons inherit the still-live owner objective",
        ],
        "risk": [
            "stop outside source/refinement distal and protected correction extreme",
            "buffer is max(observed spread, one tick)",
        ],
        "objective": [
            "freeze exact live liquidity; never offset beyond it",
            "consumed liquidity cannot be reused",
            "continuation objective is frozen by the owner",
            "rotation objective is the first meaningful opposing liquidity",
            "no RR fallback, R cap, or time exit",
        ],
        "reverseEngineeringCompletion": (
            "all casebook entries must be rediscovered from as-of OHLC; "
            "blind replay may add valid entries but may not miss them"
        ),
    }


def write_outputs(
    casebook: dict[str, Any],
    engine_result: Any,
    regression: dict[str, Any],
    trades: list[dict[str, Any]],
) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    values = [float(row["earnedR"]) for row in trades]
    wins = [row for row in trades if row["result"] == "TP"]
    losses = [row for row in trades if row["result"] == "SL"]
    gross_win = sum(float(row["earnedR"]) for row in wins)
    gross_loss = abs(sum(float(row["earnedR"]) for row in losses))
    summary = {
        "casebookEntries": len(casebook["references"]),
        "entryRecall": regression["entryRecall"],
        "matchedEntries": regression["matchedCount"],
        "objectiveAlternativeRecall": regression["objectiveAlternativeRecall"],
        "rawEvidenceCandidates": len(engine_result.candidates),
        "retestEligibleEvidenceCandidates": len(
            engine_result.authorized_candidates
        ),
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "winRate": len(wins) / len(trades) if trades else 0.0,
        "totalR": round(sum(values), 6),
        "profitFactor": round(gross_win / gross_loss, 6) if gross_loss else None,
        "maxDrawdownR": round(max_drawdown(values), 6),
        "ambiguousTrades": sum(bool(row["ambiguous"]) for row in trades),
        "runtimeBoundaryPassed": bool(
            engine_result.audit["runtimeReadsCasebook"] is False
            and engine_result.audit["hardcodedTradeDates"] is False
            and engine_result.audit["hardcodedTradePrices"] is False
        ),
    }
    (OUTPUT / "frozen_rule_contract_v5.json").write_text(
        json.dumps(contract(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT / "engine_audit.json").write_text(
        json.dumps(engine_result.audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT / "regression.json").write_text(
        json.dumps(regression, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rejection_count = len(casebook.get("rejections", []))
    report = f"""# Mentor Rule Reverse Engineering V5

## 판정

현재 주간에서 최종 기준으로 남은 진입 {summary['casebookEntries']}건을
casebook 가격이나 날짜를 읽지 않는 런타임 엔진이 {summary['matchedEntries']}건
모두 재발견했다. 진입 회귀율과 목적 유동성 후보 회귀율은 각각
{summary['entryRecall'] * 100:.1f}%, {summary['objectiveAlternativeRecall'] * 100:.1f}%다.

V4R11은 기준 진입에서 제외했다. 07:26 주문 결정 뒤 가장 가까운 살아 있는
M5 상방 유동성 3356.77이 07:27에 먼저 소진되고 지정가 재테스트는 07:49에
발생했으므로 `NO_TRADE_OBJECTIVE_FIRST`가 맞다. 공식 비매매 교정은
{rejection_count}건이다.

## 교정된 결과

- 거래: {summary['trades']}건
- 승패: {summary['wins']}승 / {summary['losses']}패
- 승률: {summary['winRate'] * 100:.2f}%
- 합계: {summary['totalR']:+.6f}R
- Profit Factor: {summary['profitFactor']:.4f}
- 최대 낙폭: {summary['maxDrawdownR']:.2f}R
- intrabar 모호성: {summary['ambiguousTrades']}건

## V4에서 바로잡은 핵심

1. OB는 displacement 앞의 **마지막 반대색 캔들**만 인정한다.
2. 새 source가 확정되면 이전 sweep과 새 반응을 같은 episode로 합치지 않는다.
3. sweep은 관통만이 아니라 종가 회복된 수준 중 물리적으로 가장 먼 수준을 쓴다.
4. CHoCH는 sweep 전 고정 창이 아니라 displacement 직전의 live body origin도 추적한다.
5. 이미 소진된 3381.70을 R02/R03이 공유하던 오류를 제거했다.
6. R04의 이미 소진된 3391.76 TP를 다음 살아 있는 3400.04로 교정했다.
7. R09/R10은 최초 반응 진입과 구분되는 delivery FVG 추가진입 계보다.

## 경계

`rawEvidenceCandidates`와 `retestEligibleEvidenceCandidates`는 source, sweep,
shift, FVG의 가능한 인과 조합 수이지 주문 수가 아니다. 실제 blind replay에서는
한 시점의 owner, competing scenario, pending 상태를 적용해 하나의 판단으로
축약해야 한다. 이 V5는 **동일 구간 기준 진입을 놓치지 않는 규칙 역설계**를
동결한 것이며, OOS 수익성이나 EA 완성을 주장하는 결과가 아니다.
"""
    (OUTPUT / "REVERSE_ENGINEERING_V5_REPORT.md").write_text(
        report, encoding="utf-8"
    )
    with (OUTPUT / "corrected_casebook_trades.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trades[0]))
        writer.writeheader()
        writer.writerows(trades)
    matched = {
        row["reference"]["reference_id"]: row["candidate"]
        for row in regression["rows"]
        if row["candidate"] is not None
    }
    with (OUTPUT / "matched_engine_candidates.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for reference_id, candidate in matched.items():
            handle.write(
                json.dumps(
                    {"referenceId": reference_id, "candidate": candidate},
                    ensure_ascii=False,
                )
                + "\n"
            )
    return summary


def main() -> int:
    casebook = load_casebook()
    period = casebook["period"]
    m1, _ = load_m1_npz(
        DATASET,
        timestamp(period["warmupFrom"]),
        timestamp("2025-06-22T00:00:00Z"),
    )
    result = MentorRuleEngine(build_timeframes(m1)).run(
        timestamp(period["from"]),
        timestamp(period["to"]),
    )
    regression = compare_reference_setups(
        references(casebook),
        result.authorized_candidates,
        point=POINT,
        sweep_tolerance_minutes=10,
        creation_tolerance_minutes=0,
    )
    trades = [simulate(m1, row) for row in casebook["references"]]
    summary = write_outputs(casebook, result, regression, trades)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if regression["entryRecall"] != 1.0:
        return 2
    if summary["ambiguousTrades"]:
        return 3
    if not summary["runtimeBoundaryPassed"]:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
