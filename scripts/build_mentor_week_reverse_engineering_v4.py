"""Rebuild the 2025-06-16..20 mentor benchmark with the current rule contract.

This remains an in-sample reverse-engineering exercise. The trade decisions are
manually authored from the full weekly path. Code is limited to quote replay,
causality checks, statistics, and chart/report generation.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz, parse_utc


UTC = timezone.utc
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = ROOT / "output" / "mentor_week_2025-06-16_20_current_rules_reverse_v4"
CHARTS = OUTPUT / "trade_charts"


def ts(value: str) -> int:
    parsed = parse_utc(value)
    if parsed is None:
        raise ValueError(value)
    return parsed


def load_legacy_renderer() -> Any:
    path = ROOT / "scripts" / "build_mentor_week_reverse_engineering_v3.py"
    spec = importlib.util.spec_from_file_location("mentor_reverse_v3_renderer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import renderer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUTPUT = OUTPUT
    module.CHARTS = CHARTS
    return module


CURRENT_RULE_CONTRACT: dict[str, Any] = {
    "schema": "mentor-week-current-rules-reverse-v4",
    "nature": (
        "in-sample reverse engineering; useful as a current-rule benchmark, "
        "not evidence of out-of-sample edge"
    ),
    "map": {
        "timeframes": ["H1", "M30", "M15", "M5"],
        "rule": (
            "H1 owns external direction and scope. M30/M15/M5 may own the "
            "source only when the candle precedes the causal body break."
        ),
        "source": (
            "Initial source is a swing-owned OB. HTF FVG is context only. "
            "A unique causal child replaces a broad parent; when no unique "
            "child exists, the last proven parent remains the source."
        ),
    },
    "trigger": {
        "timeframe": "M1 only",
        "sequence": [
            "predeclared source touch",
            "pre-existing or reaction liquidity wick sweep and close recovery",
            "separate body-close CHoCH through a live protected reference",
            "CHoCH displacement creates a fresh M1 FVG",
            "later retest after FVG availability",
        ],
        "prohibitions": [
            "OB fallback when CHoCH displacement has no FVG",
            "source chosen before its causal body break is known",
            "tiny post-sweep fluctuation promoted to CHoCH",
        ],
    },
    "state": {
        "parent": (
            "Survives an execution-chain failure until objective consumption "
            "or body-close invalidation of the parent/source structure."
        ),
        "rearm": (
            "Requires a new physical sweep, CHoCH, fresh FVG, and retest. "
            "The same chain cannot be counted twice."
        ),
        "deliveryAddon": (
            "Allowed only under the same owner/objective after a new protected "
            "correction and causal displacement create a fresh M1 FVG."
        ),
    },
    "risk": {
        "hardStop": (
            "Outside the causal source/refinement OB distal, its protected "
            "swing, and the expected sweep path. Delivery add-ons use the new "
            "delivery family's causal OB and protected correction."
        ),
        "buffer": "observed spread or one tick, whichever is greater",
        "prohibitions": [
            "M1 sweep extreme as the automatic hard stop",
            "stop narrowed to manufacture R",
        ],
    },
    "objective": {
        "rule": (
            "Exact nearest confirmed unconsumed liquidity appropriate to the "
            "scenario scope; no offset beyond the liquidity."
        ),
        "prohibitions": ["skip-nearest target", "RR fallback", "maximum R", "time exit"],
    },
}


def trade(
    trade_id: str,
    scenario: str,
    direction: str,
    decision_at: str,
    map_tf: str,
    source_tf: str,
    source_zone: tuple[float, float],
    source_formed_at: str,
    source_available_at: str,
    sweep_at: str,
    sweep_price: float,
    choch_at: str,
    entry_zone: tuple[float, float],
    entry_available_at: str,
    entry: float,
    scenario_invalidation: float,
    stop: float,
    objective: float,
    objective_formed_at: str,
    objective_kind: str,
    parent_id: str,
    attempt: int,
    entry_model: str = "HTF_OB_REACTION",
) -> dict[str, Any]:
    return {
        "tradeId": trade_id,
        "scenario": scenario,
        "direction": direction,
        "decisionAt": decision_at,
        "mapTf": map_tf,
        "sourceTf": source_tf,
        "sourceZone": list(source_zone),
        "sourceFrom": source_formed_at,
        "sourceAvailableAt": source_available_at,
        "sweepAt": sweep_at,
        "sweepPrice": sweep_price,
        "chochAt": choch_at,
        "entryZone": list(entry_zone),
        "entryZoneType": "M1 FVG",
        "entryAvailableAt": entry_available_at,
        "entry": entry,
        "scenarioInvalidation": scenario_invalidation,
        "stop": stop,
        "objective": objective,
        "objectiveFormedAt": objective_formed_at,
        "objectiveKind": objective_kind,
        "parentId": parent_id,
        "attempt": attempt,
        "entryModel": entry_model,
    }


TRADES: list[dict[str, Any]] = [
    trade(
        "V4R01",
        "내부 하락 회전",
        "short",
        "2025-06-16T05:31:00+00:00",
        "H1",
        "M5",
        (3445.92, 3450.46),
        "2025-06-16T03:20:00+00:00",
        "2025-06-16T03:45:00+00:00",
        "2025-06-16T05:11:00+00:00",
        3446.23,
        "2025-06-16T05:29:00+00:00",
        (3442.75, 3443.06),
        "2025-06-16T05:31:00+00:00",
        3442.75,
        3451.10,
        3451.50,
        3433.08,
        "2025-06-16T04:05:00+00:00",
        "nearest unconsumed M5 sell-side swing",
        "P01",
        1,
    ),
    trade(
        "V4R02",
        "외부 하락 지속",
        "short",
        "2025-06-17T02:38:00+00:00",
        "H1",
        "M15",
        (3398.61, 3400.67),
        "2025-06-16T19:30:00+00:00",
        "2025-06-16T20:45:00+00:00",
        "2025-06-17T02:32:00+00:00",
        3400.15,
        "2025-06-17T02:37:00+00:00",
        (3396.74, 3397.13),
        "2025-06-17T02:38:00+00:00",
        3396.74,
        3400.67,
        3400.94,
        3381.70,
        "2025-06-13T01:30:00+00:00",
        "nearest confirmed external sell-side",
        "P02",
        1,
    ),
    trade(
        "V4R03",
        "외부 하락 지속",
        "short",
        "2025-06-17T10:54:00+00:00",
        "H1",
        "M15",
        (3391.65, 3393.83),
        "2025-06-17T08:15:00+00:00",
        "2025-06-17T09:45:00+00:00",
        "2025-06-17T10:51:00+00:00",
        3391.76,
        "2025-06-17T10:52:00+00:00",
        (3389.20, 3390.27),
        "2025-06-17T10:54:00+00:00",
        3389.20,
        3393.83,
        3394.17,
        3381.70,
        "2025-06-13T01:30:00+00:00",
        "nearest confirmed external sell-side",
        "P03",
        1,
    ),
    trade(
        "V4R04",
        "내부 상승 회전",
        "long",
        "2025-06-17T15:27:00+00:00",
        "H1",
        "M15",
        (3379.26, 3384.33),
        "2025-06-17T12:15:00+00:00",
        "2025-06-17T13:15:00+00:00",
        "2025-06-17T15:15:00+00:00",
        3383.60,
        "2025-06-17T15:24:00+00:00",
        (3385.85, 3386.06),
        "2025-06-17T15:27:00+00:00",
        3386.06,
        3379.26,
        3378.92,
        3391.76,
        "2025-06-16T20:55:00+00:00",
        "first opposing internal buy-side",
        "P04",
        1,
    ),
    trade(
        "V4R05",
        "외부 하락 재개",
        "short",
        "2025-06-17T17:07:00+00:00",
        "H1",
        "M15",
        (3391.34, 3397.33),
        "2025-06-17T16:30:00+00:00",
        "2025-06-17T17:00:00+00:00",
        "2025-06-17T17:02:00+00:00",
        3391.91,
        "2025-06-17T17:04:00+00:00",
        (3387.64, 3388.01),
        "2025-06-17T17:07:00+00:00",
        3387.64,
        3397.33,
        3397.67,
        3375.66,
        "2025-06-17T12:15:00+00:00",
        "nearest confirmed external sell-side",
        "P05",
        1,
    ),
    trade(
        "V4R06",
        "외부 하락 지속",
        "short",
        "2025-06-18T19:11:00+00:00",
        "H1",
        "M15",
        (3394.16, 3397.57),
        "2025-06-18T07:30:00+00:00",
        "2025-06-18T08:45:00+00:00",
        "2025-06-18T19:01:00+00:00",
        3394.51,
        "2025-06-18T19:08:00+00:00",
        (3391.40, 3391.73),
        "2025-06-18T19:11:00+00:00",
        3391.40,
        3397.57,
        3397.89,
        3370.52,
        "2025-06-18T05:35:00+00:00",
        "nearest confirmed external sell-side",
        "P06",
        1,
    ),
    trade(
        "V4R07",
        "외부 하락 지속 재무장",
        "short",
        "2025-06-18T21:24:00+00:00",
        "H1",
        "M15",
        (3394.16, 3397.57),
        "2025-06-18T07:30:00+00:00",
        "2025-06-18T08:45:00+00:00",
        "2025-06-18T21:08:00+00:00",
        3395.65,
        "2025-06-18T21:22:00+00:00",
        (3391.25, 3391.37),
        "2025-06-18T21:24:00+00:00",
        3391.25,
        3397.57,
        3397.91,
        3370.52,
        "2025-06-18T05:35:00+00:00",
        "same frozen external sell-side",
        "P06",
        2,
    ),
    trade(
        "V4R08",
        "외부 하락 지속",
        "short",
        "2025-06-19T20:25:00+00:00",
        "H1",
        "M15",
        (3371.89, 3374.21),
        "2025-06-19T14:15:00+00:00",
        "2025-06-19T15:15:00+00:00",
        "2025-06-19T20:22:00+00:00",
        3375.31,
        "2025-06-19T20:24:00+00:00",
        (3373.86, 3373.96),
        "2025-06-19T20:25:00+00:00",
        3373.86,
        3375.31,
        3375.72,
        3347.39,
        "2025-06-19T09:45:00+00:00",
        "nearest confirmed external sell-side",
        "P07",
        1,
    ),
    trade(
        "V4R09",
        "외부 하락 전달 FVG 추가진입",
        "short",
        "2025-06-19T20:44:00+00:00",
        "H1",
        "M5",
        (3369.81, 3371.56),
        "2025-06-19T20:35:00+00:00",
        "2025-06-19T20:38:00+00:00",
        "2025-06-19T20:22:00+00:00",
        3375.31,
        "2025-06-19T20:31:00+00:00",
        (3366.32, 3366.70),
        "2025-06-19T20:44:00+00:00",
        3366.32,
        3371.56,
        3371.96,
        3347.39,
        "2025-06-19T09:45:00+00:00",
        "same frozen external sell-side",
        "P07",
        2,
        "DELIVERY_FVG_ADDON",
    ),
    trade(
        "V4R10",
        "외부 하락 전달 FVG 추가진입",
        "short",
        "2025-06-20T04:11:00+00:00",
        "H1",
        "M5",
        (3367.13, 3369.12),
        "2025-06-20T03:55:00+00:00",
        "2025-06-20T04:10:00+00:00",
        "2025-06-20T03:00:00+00:00",
        3370.24,
        "2025-06-20T04:10:00+00:00",
        (3363.76, 3363.93),
        "2025-06-20T04:11:00+00:00",
        3363.76,
        3370.31,
        3370.66,
        3347.39,
        "2025-06-19T09:45:00+00:00",
        "same frozen external sell-side",
        "P07",
        3,
        "DELIVERY_FVG_ADDON",
    ),
    trade(
        "V4R11",
        "내부 상승 회전",
        "long",
        "2025-06-20T07:26:00+00:00",
        "H1",
        "M15",
        (3344.63, 3353.96),
        "2025-06-20T06:00:00+00:00",
        "2025-06-20T06:45:00+00:00",
        "2025-06-20T07:06:00+00:00",
        3353.84,
        "2025-06-20T07:08:00+00:00",
        (3356.02, 3356.03),
        "2025-06-20T07:26:00+00:00",
        3356.03,
        3344.63,
        3344.26,
        3360.49,
        "2025-06-20T05:10:00+00:00",
        "nearest confirmed internal buy-side",
        "P08",
        1,
    ),
]


CANDIDATE_AUDIT: list[dict[str, Any]] = [
    {
        "candidateId": "A01",
        "at": "2025-06-16T04:04:00+00:00",
        "verdict": "NO_TRADE_REFINED_SOURCE_NOT_TOUCHED",
        "reason": (
            "Broad M30 OB contact did not reach the already-proven M5 causal "
            "source 3445.92-3450.46; the old R01 used the discarded broad zone."
        ),
    },
    {
        "candidateId": "A02",
        "at": "2025-06-16T05:11:00+00:00",
        "verdict": "TRADE_V4R01",
        "reason": "Causal M5 source touch, EQH sweep, separate CHoCH, FVG, retest.",
    },
    {
        "candidateId": "A03",
        "at": "2025-06-17T02:32:00+00:00",
        "verdict": "TRADE_V4R02",
        "reason": "Valid chain; the structurally widened stop is still reached.",
    },
    {
        "candidateId": "A04",
        "at": "2025-06-17T03:03:00+00:00",
        "verdict": "NO_TRADE_NO_CHOCH_FVG",
        "reason": "The old R04 used an OB fallback; the current first-entry contract forbids it.",
    },
    {
        "candidateId": "A05",
        "at": "2025-06-17T05:44:00+00:00",
        "verdict": "NO_FILL_OBJECTIVE_FIRST",
        "reason": "The frozen 3381.70 objective is consumed before the FVG retest.",
    },
    {
        "candidateId": "A06",
        "at": "2025-06-17T10:51:00+00:00",
        "verdict": "TRADE_V4R03",
        "reason": "Nearest external objective retained; stop moved beyond the M15 source.",
    },
    {
        "candidateId": "A07",
        "at": "2025-06-17T15:15:00+00:00",
        "verdict": "TRADE_V4R04",
        "reason": "Internal rotation is bounded at the first opposing liquidity.",
    },
    {
        "candidateId": "A08",
        "at": "2025-06-17T17:02:00+00:00",
        "verdict": "TRADE_V4R05",
        "reason": (
            "The old source timestamp was wrong. The actual M15 source is the "
            "16:30 candle, known before the M1 trigger."
        ),
    },
    {
        "candidateId": "A09",
        "at": "2025-06-18T06:52:00+00:00",
        "verdict": "NO_TRADE_PARENT_INVALIDATED",
        "reason": "Source body invalidation occurs before a complete M1 chain.",
    },
    {
        "candidateId": "A10",
        "at": "2025-06-18T19:01:00+00:00",
        "verdict": "TRADE_V4R06",
        "reason": (
            "The old execution stop sat inside the still-valid M15 source. "
            "The scenario stop survives the second reaction."
        ),
    },
    {
        "candidateId": "A11",
        "at": "2025-06-18T21:08:00+00:00",
        "verdict": "TRADE_V4R07_REARM",
        "reason": "A new sweep, CHoCH, FVG and retest create a distinct attempt.",
    },
    {
        "candidateId": "A12",
        "at": "2025-06-19T13:08:00+00:00",
        "verdict": "NO_TRADE_NO_LIVE_REFERENCE_CHOCH",
        "reason": "The small post-sweep fluctuation is not a protected-structure CHoCH.",
    },
    {
        "candidateId": "A13",
        "at": "2025-06-19T20:22:00+00:00",
        "verdict": "TRADE_V4R08",
        "reason": "The 14:15 M15 parent remains alive and is rearmed by the later sweep.",
    },
    {
        "candidateId": "A14",
        "at": "2025-06-19T20:44:00+00:00",
        "verdict": "TRADE_V4R09_DELIVERY_ADDON",
        "reason": "Same owner/objective; first retest of the new causal delivery FVG family.",
    },
    {
        "candidateId": "A15",
        "at": "2025-06-20T01:15:00+00:00",
        "verdict": "NO_TRADE_MARKET_BREAK_DISCONTINUITY",
        "reason": "The apparent gap spans the daily quote break and is not used as delivery evidence.",
    },
    {
        "candidateId": "A16",
        "at": "2025-06-20T04:11:00+00:00",
        "verdict": "TRADE_V4R10_DELIVERY_ADDON",
        "reason": "A new M5 correction and body displacement create an independent M1 FVG family.",
    },
    {
        "candidateId": "A17",
        "at": "2025-06-20T07:06:00+00:00",
        "verdict": "TRADE_V4R11",
        "reason": "Valid bounded rotation, but the scenario-level source invalidation is later reached.",
    },
    {
        "candidateId": "A18",
        "at": "2025-06-20T08:36:00+00:00",
        "verdict": "NO_TRADE_NO_CHOCH_FVG",
        "reason": "The old R12 was an OB fallback without a fresh CHoCH-owned FVG.",
    },
]


def validate_authorship(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    seen_physical: set[tuple[str, str, float]] = set()
    for record in records:
        decision = ts(record["decisionAt"])
        source_available = ts(record["sourceAvailableAt"])
        entry_available = ts(record["entryAvailableAt"])
        objective_formed = ts(record["objectiveFormedAt"])
        direction = record["direction"]
        source_low, source_high = [float(value) for value in record["sourceZone"]]
        invalidation = float(record["scenarioInvalidation"])
        stop = float(record["stop"])
        geometry_ok = (
            stop < invalidation <= source_low
            if direction == "long"
            else stop > invalidation >= source_high
        )
        physical_key = (
            record["sweepAt"],
            record["chochAt"],
            float(record["entry"]),
        )
        unique_physical = physical_key not in seen_physical
        seen_physical.add(physical_key)
        row = {
            "tradeId": record["tradeId"],
            "sourceKnownBeforeDecision": source_available <= decision,
            "entryZoneKnownBeforeDecision": entry_available <= decision,
            "objectiveKnownBeforeDecision": objective_formed <= decision,
            "stopOutsideScenarioInvalidation": geometry_ok,
            "uniquePhysicalChain": unique_physical,
        }
        row["ok"] = all(value for key, value in row.items() if key != "tradeId")
        checks.append(row)
    failed = [row for row in checks if not row["ok"]]
    if failed:
        raise RuntimeError(f"Authorship audit failed: {failed}")
    return checks


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def max_concurrent_risk(records: list[dict[str, Any]]) -> int:
    events: list[tuple[int, int]] = []
    for record in records:
        if not record.get("filledAt") or not record.get("closedAt"):
            continue
        events.append((ts(record["filledAt"]), 1))
        events.append((ts(record["closedAt"]), -1))
    active = 0
    maximum = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        maximum = max(maximum, active)
    return maximum


def write_outputs(
    records: list[dict[str, Any]],
    authorship_audit: list[dict[str, Any]],
) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "frozen_rule_contract_v4.json").write_text(
        json.dumps(CURRENT_RULE_CONTRACT, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (OUTPUT / "candidate_audit.jsonl").open("w", encoding="utf-8") as handle:
        for row in CANDIDATE_AUDIT:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    (OUTPUT / "causality_audit.json").write_text(
        json.dumps(
            {
                "ok": True,
                "trades": authorship_audit,
                "candidateCount": len(CANDIDATE_AUDIT),
                "forbiddenObFallbackTrades": 0,
                "futureSourceTrades": 0,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    fields = [
        "tradeId",
        "scenario",
        "entryModel",
        "direction",
        "decisionAt",
        "filledAt",
        "closedAt",
        "sourceTf",
        "parentId",
        "attempt",
        "entry",
        "scenarioInvalidation",
        "stop",
        "objective",
        "result",
        "plannedR",
        "earnedR",
        "holdingMinutes",
        "classification",
    ]
    with (OUTPUT / "current_rule_trades.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    values = [float(record["earnedR"]) for record in records]
    wins = [record for record in records if record["result"] == "TP"]
    losses = [record for record in records if record["result"] == "SL"]
    gross_win = sum(float(record["earnedR"]) for record in wins)
    gross_loss = abs(sum(float(record["earnedR"]) for record in losses))
    stats = {
        "trades": len(records),
        "wins": len(wins),
        "losses": len(losses),
        "winRate": len(wins) / len(records) if records else 0.0,
        "totalR": sum(values),
        "profitFactor": gross_win / gross_loss if gross_loss else None,
        "maxDrawdownR": max_drawdown(values),
        "maxConcurrentRiskR": max_concurrent_risk(records),
        "deliveryAddons": sum(
            record["entryModel"] == "DELIVERY_FVG_ADDON" for record in records
        ),
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    old_total = 27.305065
    blind_total = -0.894857
    summary = f"""# Current Rules Reverse Engineering V4

## 성격

2025-06-16~20 전체 경로를 현재 규칙으로 다시 판정한 in-sample 역설계다.
구 V3의 거래 가격만 수정하지 않고 source 시각, FVG 유무, 구조 SL, objective,
parent rearm, delivery add-on을 모두 다시 감사했다. 이 결과는 현재 규칙의
기준점이며 OOS 수익성 증거는 아니다.

## 결과

- 후보 감사: {len(CANDIDATE_AUDIT)}건
- 거래: {stats['trades']}건
- 승/패: {stats['wins']}승 / {stats['losses']}패
- 승률: {stats['winRate'] * 100:.2f}%
- 합계: {stats['totalR']:+.6f}R
- Profit Factor: {stats['profitFactor']:.2f}
- 최대 낙폭: {stats['maxDrawdownR']:.2f}R
- 최대 동시 위험: {stats['maxConcurrentRiskR']}R
- Delivery FVG 추가진입: {stats['deliveryAddons']}건

## 구 V3에서 폐기하거나 교정한 것

1. 넓은 M30 OB만 접촉하고 causal M5 refinement에 닿지 않은 첫 short는 폐기했다.
2. CHoCH displacement FVG가 없던 OB fallback long 2건을 폐기했다.
3. source candle 시각을 실제 OHLC 형성 시각으로 전수 교정했다.
4. M1 sweep 바깥의 짧은 execution SL을 폐기하고 source/refinement 및 protected
   structure 바깥의 scenario hard SL로 다시 계산했다.
5. 가장 가까운 미소진 유동성만 TP로 사용했다.
6. 같은 parent의 새 물리적 chain과 새 correction이 확인된 delivery FVG add-on만
   별도 거래로 허용했다.
7. 일일 quote break를 가로지른 gap은 FVG add-on 근거에서 제외했다.

## 이전 결과와 차이

| 원장 | 거래 | 승률 | 합계 R |
|---|---:|---:|---:|
| Blind V4 | 3 | 33.33% | {blind_total:+.6f}R |
| 구 Reverse V3 | 12 | 58.33% | {old_total:+.6f}R |
| Current Rules Reverse V4 | {stats['trades']} | {stats['winRate'] * 100:.2f}% | {stats['totalR']:+.6f}R |

- 구 역설계 대비: {stats['totalR'] - old_total:+.6f}R
- 블라인드 대비: {stats['totalR'] - blind_total:+.6f}R

## 해석

성과 개선의 주원인은 손실을 사후 삭제한 것이 아니다. V4R02와 V4R11은
구조 SL을 적용해도 실제로 손실로 남았다. 차이는 정상 되돌림 경로 안에 있던
구 R08의 짧은 SL을 바로잡았고, 살아 있는 하락 owner 아래에서 독립 chain과
delivery FVG add-on을 일관되게 기록한 데서 발생했다.

다만 V4R08 한 거래와 그 두 add-on이 주간 수익의 대부분을 차지한다. 그러므로
이 원장은 현재 규칙의 설명 가능한 in-sample 기준점이지, 다음 주에도 같은
성과가 난다는 증거가 아니다.
"""
    (OUTPUT / "CURRENT_RULES_REVERSE_V4_SUMMARY.md").write_text(
        summary, encoding="utf-8"
    )

    rows = "\n".join(
        "<tr>"
        f"<td>{record['tradeId']}</td><td>{record['scenario']}</td>"
        f"<td>{record['result']}</td><td>{float(record['earnedR']):+.2f}R</td>"
        f"<td>{record['holdingMinutes']}분</td>"
        "</tr>"
        for record in records
    )
    cards = "\n".join(
        "<section><h2>"
        f"{record['tradeId']} · {record['scenario']}"
        "</h2>"
        f"<img src=\"trade_charts/{record['tradeId']}.png\" "
        f"alt=\"{record['tradeId']} chart\"></section>"
        for record in records
    )
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Current Rules Reverse V4</title>
<style>
body{{margin:0;background:#080c12;color:#e2e8f0;font:15px Arial,sans-serif}}
main{{max-width:1500px;margin:auto;padding:24px}} h1{{margin:0 0 8px}}
.note{{color:#94a3b8}} table{{border-collapse:collapse;width:100%;margin:24px 0}}
th,td{{padding:10px;border-bottom:1px solid #263241;text-align:left}}
section{{margin:28px 0}} img{{width:100%;display:block;border:1px solid #263241}}
</style></head><body><main><h1>Current Rules Reverse Engineering V4</h1>
<p class="note">현재 규칙으로 동일 주간을 다시 판정한 in-sample 기준 원장입니다.</p>
<table><thead><tr><th>ID</th><th>시나리오</th><th>결과</th><th>R</th><th>보유</th>
</tr></thead><tbody>{rows}</tbody></table>{cards}</main></body></html>"""
    (OUTPUT / "TRADE_REVIEW.html").write_text(html, encoding="utf-8")


def main() -> int:
    legacy = load_legacy_renderer()
    warmup = ts("2025-06-09T00:00:00+00:00")
    end = ts("2025-06-21T23:59:00+00:00")
    m1, _ = load_m1_npz(DATASET, warmup, end)
    frames = build_timeframes(m1)
    authorship_audit = validate_authorship(TRADES)
    records = [legacy.simulate_trade(m1, record) for record in TRADES]
    unresolved = [
        record["tradeId"]
        for record in records
        if record["result"] not in {"TP", "SL"} or record["ambiguous"]
    ]
    if unresolved:
        raise RuntimeError(f"Unresolved or ambiguous trades: {unresolved}")
    write_outputs(records, authorship_audit)
    for record in records:
        legacy.render_trade(record, frames)
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "candidates": len(CANDIDATE_AUDIT),
                "trades": len(records),
                "wins": sum(record["result"] == "TP" for record in records),
                "losses": sum(record["result"] == "SL" for record in records),
                "totalR": round(
                    sum(float(record["earnedR"]) for record in records), 6
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
