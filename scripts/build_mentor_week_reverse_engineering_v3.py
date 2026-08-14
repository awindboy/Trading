"""Build the post-hoc mentor-rule reverse engineering pack for 2025-06-16..20.

This script does not discover trades. Every source, trigger, entry, stop and
objective below is manually authored from the full-week chart review. The code
only replays quotes, calculates statistics and renders the frozen evidence.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz, parse_utc


UTC = timezone.utc
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = ROOT / "output" / "mentor_week_2025-06-16_20_rule_reverse_engineering_v3"
CHARTS = OUTPUT / "trade_charts"
POINT = 0.01

BG = "#080c12"
GRID = "#263241"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
BULL = "#5eead4"
BEAR = "#f87171"
RISK = "#ef4444"
REWARD = "#10b981"
SOURCE = "#8b5cf6"
ENTRY_ZONE = "#f59e0b"
LIQUIDITY = "#60a5fa"
SWEEP = "#fbbf24"

plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def iso(value: int) -> str:
    return datetime.fromtimestamp(value, tz=UTC).isoformat()


def ts(value: str) -> int:
    parsed = parse_utc(value)
    if parsed is None:
        raise ValueError(value)
    return parsed


EPISODES: list[dict[str, Any]] = [
    {
        "episodeId": "E01",
        "at": "2025-06-16T03:01:00+00:00",
        "source": "M15 bearish OB 3443.07-3449.01",
        "verdict": "NO_TRADE_OBJECTIVE_FIRST",
        "reason": "3439.42 목적 유동성이 새 M1 체인 완성 전에 먼저 소진됐다.",
    },
    {
        "episodeId": "E02",
        "at": "2025-06-16T04:04:00+00:00",
        "source": "M30 bearish OB 3437.02-3451.10",
        "verdict": "TRADE_ATTEMPT_1",
        "reason": "첫 sweep-CHoCH-FVG retest는 유효했다. 실행 구조만 무효화돼 -1R로 종료한다.",
    },
    {
        "episodeId": "E03",
        "at": "2025-06-16T05:11:00+00:00",
        "source": "same M30 bearish OB 3437.02-3451.10",
        "verdict": "TRADE_REARM",
        "reason": "부모 OB와 3431.45 목적지는 살아 있었고, 독립 sweep부터 새 체인이 완성됐다.",
    },
    {
        "episodeId": "E04",
        "at": "2025-06-16T13:07:00+00:00",
        "source": "M15 bearish OB 3415.06-3419.39",
        "verdict": "NO_TRADE_NO_SWEEP",
        "reason": "사전 고점 3415.70을 취하지 못해 하락 변위만으로는 진입하지 않는다.",
    },
    {
        "episodeId": "E05",
        "at": "2025-06-16T14:09:00+00:00",
        "source": "M30 bullish OB 3411.75-3419.21",
        "verdict": "NO_TRADE_OBJECTIVE_FIRST",
        "reason": "3421.48 목적지가 source 접촉 전에 이미 소진됐다.",
    },
    {
        "episodeId": "E06",
        "at": "2025-06-17T02:28:00+00:00",
        "source": "M15 bearish OB 3398.61-3400.67",
        "verdict": "TRADE_ATTEMPT_1",
        "reason": "유효한 short 체인이었으나 실행 무효화로 -1R. 이후 부모가 몸통 무효화됐다.",
    },
    {
        "episodeId": "E07",
        "at": "2025-06-17T03:01:00+00:00",
        "source": "M15 bullish rotation OB 3393.51-3400.15",
        "verdict": "TRADE_NEW_PARENT",
        "reason": "새 M15 상승 원인과 별도 M1 체인이 형성됐다. 가장 가까운 3402.83 유동성만 취한다.",
    },
    {
        "episodeId": "E08",
        "at": "2025-06-17T04:06:00+00:00",
        "source": "M15 bearish OB 3399.29-3403.11",
        "verdict": "WAIT_UNRESOLVED",
        "reason": "첫 접촉에는 CHoCH가 없었다. source는 닫지 않고 다음 독립 반응을 기다린다.",
    },
    {
        "episodeId": "E09",
        "at": "2025-06-17T05:44:00+00:00",
        "source": "same M15 bearish OB 3399.29-3403.11",
        "verdict": "ORDER_NOT_FILLED",
        "reason": "체인은 완성됐지만 FVG retest 전에 3381.70 목적지가 먼저 소진됐다.",
    },
    {
        "episodeId": "E10",
        "at": "2025-06-17T10:51:00+00:00",
        "source": "M15 bearish OB 3391.65-3393.83",
        "verdict": "TRADE_NEAREST_OBJECTIVE",
        "reason": "기존 원장은 3373.10을 골라 손실이었지만, 당시 가장 가까운 미소진 유동성은 3381.70이었다.",
    },
    {
        "episodeId": "E11",
        "at": "2025-06-17T15:15:00+00:00",
        "source": "M15 bullish OB 3379.26-3384.33",
        "verdict": "TRADE_BOUNDED_ROTATION",
        "reason": "외부 하락 안의 내부 회전이므로 3400.31이 아니라 첫 반대 유동성 3391.76에서 끝낸다.",
    },
    {
        "episodeId": "E12",
        "at": "2025-06-17T17:02:00+00:00",
        "source": "M15 bearish OB 3391.34-3397.33",
        "verdict": "TRADE_EXTERNAL_RESUME",
        "reason": "내부 long 목적지 소진 뒤 새 M15 하락 원인과 M1 sweep-CHoCH-FVG가 외부 하락을 재개했다.",
    },
    {
        "episodeId": "E13",
        "at": "2025-06-18T06:52:00+00:00",
        "source": "M15 bearish OB 3390.35-3395.95",
        "verdict": "NO_TRADE_PARENT_INVALIDATED",
        "reason": "M1 체인 전에 M15 source distal 위로 몸통 수용됐다.",
    },
    {
        "episodeId": "E14",
        "at": "2025-06-18T16:29:00+00:00",
        "source": "M15 bearish OB 3394.16-3397.57",
        "verdict": "WAIT_NO_SWEEP",
        "reason": "첫 접촉은 고점 수용이었으므로 source를 유지하고 다음 독립 접촉을 기다린다.",
    },
    {
        "episodeId": "E15",
        "at": "2025-06-18T19:01:00+00:00",
        "source": "same M15 bearish OB 3394.16-3397.57",
        "verdict": "TRADE_ATTEMPT_1_THEN_REARM",
        "reason": "첫 M1 short는 -1R. 부모 source가 무효화되지 않아 21:08 새 sweep부터 다시 무장한다.",
    },
    {
        "episodeId": "E16",
        "at": "2025-06-18T21:08:00+00:00",
        "source": "same M15 bearish OB 3394.16-3397.57",
        "verdict": "TRADE_ATTEMPT_2",
        "reason": "새 sweep-CHoCH-FVG 체인이 동일 3370.52 목적지까지 +4.38R을 전달했다.",
    },
    {
        "episodeId": "E17",
        "at": "2025-06-19T08:45:00+00:00",
        "source": "M15 bullish OB 3362.40-3368.89",
        "verdict": "NO_TRADE_PARENT_INVALIDATED",
        "reason": "trigger 전에 M15 source 아래로 몸통 수용됐다.",
    },
    {
        "episodeId": "E18",
        "at": "2025-06-19T13:08:00+00:00",
        "source": "M15 bearish OB 3372.70-3375.07",
        "verdict": "NO_TRADE_PARENT_INVALIDATED",
        "reason": "sweep 뒤 CHoCH가 없었고 source 위 몸통 종가로 무효화됐다.",
    },
    {
        "episodeId": "E19",
        "at": "2025-06-19T14:05:00+00:00",
        "source": "M15 bullish OB 3369.43-3373.30",
        "verdict": "NO_TRADE_NO_CHOCH",
        "reason": "저점 갱신은 이어졌지만 보호 고점 몸통 돌파가 없었다.",
    },
    {
        "episodeId": "E20",
        "at": "2025-06-19T16:53:00+00:00",
        "source": "M15 bearish OB 3371.89-3374.21",
        "verdict": "WAIT_NO_SWEEP",
        "reason": "첫 접촉은 buy-side 수용이었다. 같은 부모 source는 유지한다.",
    },
    {
        "episodeId": "E21",
        "at": "2025-06-19T20:22:00+00:00",
        "source": "same M15 bearish OB 3371.89-3374.21",
        "verdict": "TRADE_REARM",
        "reason": "3374.47을 실제로 sweep한 뒤 별도 CHoCH와 FVG retest가 완성됐다.",
    },
    {
        "episodeId": "E22",
        "at": "2025-06-20T07:06:00+00:00",
        "source": "M15 bullish OB 3344.63-3353.96",
        "verdict": "TRADE_ATTEMPT_1",
        "reason": "외부 sell-side sweep 뒤 유효한 내부 long 체인. 실행 SL 후에도 부모 source는 유지한다.",
    },
    {
        "episodeId": "E23",
        "at": "2025-06-20T08:36:00+00:00",
        "source": "same M15 bullish OB 3344.63-3353.96",
        "verdict": "TRADE_ATTEMPT_2_PARENT_FAIL",
        "reason": "새 독립 체인도 -1R. 이후 M15 source distal 아래 몸통 수용으로 부모까지 종료됐다.",
    },
]


TRADES: list[dict[str, Any]] = [
    {
        "tradeId": "R01",
        "scenario": "내부 하락 회전",
        "direction": "short",
        "decisionAt": "2025-06-16T04:07:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M30",
        "sourceZone": [3437.02, 3451.10],
        "sourceFrom": "2025-06-16T04:00:00+00:00",
        "sweepAt": "2025-06-16T04:04:00+00:00",
        "sweepPrice": 3439.32,
        "chochAt": "2025-06-16T04:05:00+00:00",
        "entryZone": [3437.25, 3438.15],
        "entryZoneType": "M1 FVG",
        "entry": 3437.25,
        "stop": 3439.66,
        "objective": 3431.45,
        "objectiveKind": "Monday sell-side",
        "parentId": "P01",
        "attempt": 1,
    },
    {
        "tradeId": "R02",
        "scenario": "내부 하락 회전 재무장",
        "direction": "short",
        "decisionAt": "2025-06-16T05:17:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M30",
        "sourceZone": [3437.02, 3451.10],
        "sourceFrom": "2025-06-16T04:00:00+00:00",
        "sweepAt": "2025-06-16T05:11:00+00:00",
        "sweepPrice": 3446.23,
        "chochAt": "2025-06-16T05:13:00+00:00",
        "entryZone": [3443.86, 3443.93],
        "entryZoneType": "M1 FVG",
        "entry": 3443.86,
        "stop": 3446.57,
        "objective": 3431.45,
        "objectiveKind": "same frozen sell-side",
        "parentId": "P01",
        "attempt": 2,
    },
    {
        "tradeId": "R03",
        "scenario": "외부 하락 지속",
        "direction": "short",
        "decisionAt": "2025-06-17T02:38:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3398.61, 3400.67],
        "sourceFrom": "2025-06-16T20:30:00+00:00",
        "sweepAt": "2025-06-17T02:32:00+00:00",
        "sweepPrice": 3400.15,
        "chochAt": "2025-06-17T02:37:00+00:00",
        "entryZone": [3396.74, 3397.13],
        "entryZoneType": "M1 FVG",
        "entry": 3396.74,
        "stop": 3400.49,
        "objective": 3381.70,
        "objectiveKind": "nearest external sell-side",
        "parentId": "P02",
        "attempt": 1,
    },
    {
        "tradeId": "R04",
        "scenario": "내부 상승 회전",
        "direction": "long",
        "decisionAt": "2025-06-17T03:04:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3393.51, 3400.15],
        "sourceFrom": "2025-06-17T03:00:00+00:00",
        "sweepAt": "2025-06-17T03:01:00+00:00",
        "sweepPrice": 3397.06,
        "chochAt": "2025-06-17T03:03:00+00:00",
        "entryZone": [3397.06, 3399.78],
        "entryZoneType": "M1 OB fallback",
        "entry": 3399.78,
        "stop": 3396.72,
        "objective": 3402.83,
        "objectiveKind": "nearest internal buy-side",
        "parentId": "P03",
        "attempt": 1,
    },
    {
        "tradeId": "R05",
        "scenario": "외부 하락 지속",
        "direction": "short",
        "decisionAt": "2025-06-17T10:54:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3391.65, 3393.83],
        "sourceFrom": "2025-06-17T09:15:00+00:00",
        "sweepAt": "2025-06-17T10:51:00+00:00",
        "sweepPrice": 3391.76,
        "chochAt": "2025-06-17T10:52:00+00:00",
        "entryZone": [3389.20, 3390.27],
        "entryZoneType": "M1 FVG",
        "entry": 3389.20,
        "stop": 3392.10,
        "objective": 3381.70,
        "objectiveKind": "nearest external sell-side",
        "parentId": "P04",
        "attempt": 1,
    },
    {
        "tradeId": "R06",
        "scenario": "내부 상승 회전",
        "direction": "long",
        "decisionAt": "2025-06-17T15:27:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3379.26, 3384.33],
        "sourceFrom": "2025-06-17T12:45:00+00:00",
        "sweepAt": "2025-06-17T15:15:00+00:00",
        "sweepPrice": 3383.60,
        "chochAt": "2025-06-17T15:24:00+00:00",
        "entryZone": [3385.85, 3386.06],
        "entryZoneType": "M1 FVG",
        "entry": 3386.06,
        "stop": 3383.26,
        "objective": 3391.76,
        "objectiveKind": "first opposing buy-side",
        "parentId": "P05",
        "attempt": 1,
    },
    {
        "tradeId": "R07",
        "scenario": "외부 하락 재개",
        "direction": "short",
        "decisionAt": "2025-06-17T17:07:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3391.34, 3397.33],
        "sourceFrom": "2025-06-17T17:00:00+00:00",
        "sweepAt": "2025-06-17T17:02:00+00:00",
        "sweepPrice": 3391.91,
        "chochAt": "2025-06-17T17:04:00+00:00",
        "entryZone": [3387.64, 3388.01],
        "entryZoneType": "M1 FVG",
        "entry": 3387.64,
        "stop": 3392.25,
        "objective": 3375.66,
        "objectiveKind": "nearest external sell-side",
        "parentId": "P06",
        "attempt": 1,
    },
    {
        "tradeId": "R08",
        "scenario": "외부 하락 지속",
        "direction": "short",
        "decisionAt": "2025-06-18T19:11:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3394.16, 3397.57],
        "sourceFrom": "2025-06-18T08:15:00+00:00",
        "sweepAt": "2025-06-18T19:01:00+00:00",
        "sweepPrice": 3394.51,
        "chochAt": "2025-06-18T19:08:00+00:00",
        "entryZone": [3391.40, 3391.73],
        "entryZoneType": "M1 FVG",
        "entry": 3391.40,
        "stop": 3394.81,
        "objective": 3370.52,
        "objectiveKind": "frozen external sell-side",
        "parentId": "P07",
        "attempt": 1,
    },
    {
        "tradeId": "R09",
        "scenario": "외부 하락 지속 재무장",
        "direction": "short",
        "decisionAt": "2025-06-18T21:24:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3394.16, 3397.57],
        "sourceFrom": "2025-06-18T08:15:00+00:00",
        "sweepAt": "2025-06-18T21:08:00+00:00",
        "sweepPrice": 3395.65,
        "chochAt": "2025-06-18T21:22:00+00:00",
        "entryZone": [3391.25, 3391.37],
        "entryZoneType": "M1 FVG",
        "entry": 3391.25,
        "stop": 3395.98,
        "objective": 3370.52,
        "objectiveKind": "same frozen external sell-side",
        "parentId": "P07",
        "attempt": 2,
    },
    {
        "tradeId": "R10",
        "scenario": "외부 하락 지속",
        "direction": "short",
        "decisionAt": "2025-06-19T20:25:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3371.89, 3374.21],
        "sourceFrom": "2025-06-19T15:00:00+00:00",
        "sweepAt": "2025-06-19T20:22:00+00:00",
        "sweepPrice": 3375.31,
        "chochAt": "2025-06-19T20:24:00+00:00",
        "entryZone": [3373.86, 3373.96],
        "entryZoneType": "M1 FVG",
        "entry": 3373.86,
        "stop": 3375.61,
        "objective": 3347.39,
        "objectiveKind": "nearest external sell-side",
        "parentId": "P08",
        "attempt": 1,
    },
    {
        "tradeId": "R11",
        "scenario": "내부 상승 회전",
        "direction": "long",
        "decisionAt": "2025-06-20T07:26:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3344.63, 3353.96],
        "sourceFrom": "2025-06-20T06:45:00+00:00",
        "sweepAt": "2025-06-20T07:06:00+00:00",
        "sweepPrice": 3353.84,
        "chochAt": "2025-06-20T07:08:00+00:00",
        "entryZone": [3356.02, 3356.03],
        "entryZoneType": "M1 FVG",
        "entry": 3356.03,
        "stop": 3353.50,
        "objective": 3360.49,
        "objectiveKind": "nearest internal buy-side",
        "parentId": "P09",
        "attempt": 1,
    },
    {
        "tradeId": "R12",
        "scenario": "내부 상승 회전 재무장",
        "direction": "long",
        "decisionAt": "2025-06-20T08:39:00+00:00",
        "mapTf": "H1",
        "sourceTf": "M15",
        "sourceZone": [3344.63, 3353.96],
        "sourceFrom": "2025-06-20T06:45:00+00:00",
        "sweepAt": "2025-06-20T08:36:00+00:00",
        "sweepPrice": 3347.63,
        "chochAt": "2025-06-20T08:38:00+00:00",
        "entryZone": [3347.63, 3350.60],
        "entryZoneType": "M1 OB fallback",
        "entry": 3350.60,
        "stop": 3347.30,
        "objective": 3360.49,
        "objectiveKind": "same nearest internal buy-side",
        "parentId": "P09",
        "attempt": 2,
    },
]


RULE_CONTRACT = {
    "schema": "mentor-week-reverse-engineered-contract-v3",
    "scope": "in-sample post-hoc rule extraction; freeze before a different blind week",
    "map": {
        "timeframes": ["H1", "M30", "M15"],
        "rule": "H1 establishes external direction and dealing range. M30/M15 may own the source when their OB explains the actual protected-level body break.",
        "source": "A parent source is the last opposite M30/M15 candle that directly precedes the causal body break. HTF FVG is context, never the root source.",
    },
    "trigger": {
        "timeframe": "M1 only",
        "sequence": [
            "parent source touch",
            "pre-existing or reaction liquidity sweep and close recovery",
            "separate body-close CHoCH",
            "CHoCH displacement creates FVG, or causal OB only when no FVG exists",
            "later retest",
        ],
    },
    "nestedState": {
        "parentScenario": "Remains active until parent OB distal body acceptance or objective consumption.",
        "executionAttempt": "Has its own M1 sweep/entry-OB invalidation and may stop without killing the parent.",
        "rearm": "A new attempt needs a new sweep, CHoCH, entry zone and retest. Reusing the same physical chain is forbidden.",
    },
    "risk": {
        "entry": "FVG proximal boundary; causal CHoCH OB proximal boundary only when no FVG exists.",
        "stop": "Outside both the reaction sweep extreme and the CHoCH execution OB distal, plus observed spread.",
        "note": "The stop judges the execution attempt. Parent scenario invalidation is tracked separately.",
    },
    "objective": {
        "externalContinuation": "Exact nearest confirmed unconsumed external liquidity in the map direction.",
        "internalRotation": "Exact first opposing internal liquidity before any active opposing source.",
        "prohibitions": ["skip-nearest target", "RR fallback", "target buffer beyond liquidity", "time exit"],
    },
    "uncertainty": {
        "definition": "MARKET_UNCERTAINTY only when map, parent source, trigger chain, local stop and nearest objective all complied.",
        "observedExamples": ["2025-06-16 first short attempt", "2025-06-17 first short attempt", "2025-06-20 two long attempts"],
    },
}


def simulate_trade(m1: Any, record: dict[str, Any]) -> dict[str, Any]:
    start = int(np.searchsorted(m1.time, ts(record["decisionAt"]), side="left"))
    status = "PENDING"
    filled_at: int | None = None
    closed_at: int | None = None
    result = "UNFILLED"
    ambiguous = False
    for index in range(start, len(m1)):
        spread = float(m1.spread_points[index]) * POINT
        bid_low = float(m1.low[index])
        bid_high = float(m1.high[index])
        ask_low = bid_low + spread
        ask_high = bid_high + spread
        available = int(m1.time[index]) + 60
        if status == "PENDING":
            touched = (
                ask_low <= record["entry"] <= ask_high
                if record["direction"] == "long"
                else bid_low <= record["entry"] <= bid_high
            )
            if not touched:
                continue
            status = "OPEN"
            filled_at = available
        if record["direction"] == "long":
            stop_hit = bid_low <= record["stop"]
            target_hit = bid_high >= record["objective"]
        else:
            stop_hit = ask_high >= record["stop"]
            target_hit = ask_low <= record["objective"]
        if stop_hit or target_hit:
            result = "SL" if stop_hit else "TP"
            ambiguous = stop_hit and target_hit
            closed_at = available
            break
    planned_r = abs(
        (float(record["objective"]) - float(record["entry"]))
        / (float(record["entry"]) - float(record["stop"]))
    )
    earned_r = -1.0 if result == "SL" else planned_r if result == "TP" else 0.0
    output = dict(record)
    output.update(
        {
            "filledAt": iso(filled_at) if filled_at else None,
            "closedAt": iso(closed_at) if closed_at else None,
            "result": result,
            "ambiguous": ambiguous,
            "plannedR": round(planned_r, 6),
            "earnedR": round(earned_r, 6),
            "holdingMinutes": int((closed_at - filled_at) / 60)
            if filled_at and closed_at
            else None,
            "classification": "MARKET_UNCERTAINTY" if result == "SL" else "PROTOCOL_WIN",
        }
    )
    return output


def nearest_index(series: Any, value: int) -> int:
    return int(np.clip(np.searchsorted(series.available_time, value, side="left"), 0, len(series) - 1))


def window(series: Any, start: int, end: int, pre: int, post: int, cap: int) -> tuple[int, int]:
    left = max(0, nearest_index(series, start) - pre)
    right = min(len(series), nearest_index(series, end) + post + 1)
    if right - left > cap:
        center = (nearest_index(series, start) + nearest_index(series, end)) // 2
        left = max(0, center - cap // 2)
        right = min(len(series), left + cap)
        left = max(0, right - cap)
    return left, right


def x_at(series: Any, left: int, right: int, value: int) -> float:
    index = int(np.searchsorted(series.available_time, value, side="left"))
    return float(np.clip(index - left, 0, max(1, right - left - 1)))


def draw_candles(axis: Any, series: Any, left: int, right: int) -> None:
    for x, index in enumerate(range(left, right)):
        colour = BULL if series.close[index] >= series.open[index] else BEAR
        axis.vlines(x, series.low[index], series.high[index], color=colour, linewidth=0.65, zorder=3)
        bottom = min(series.open[index], series.close[index])
        height = max(abs(series.close[index] - series.open[index]), 1e-6)
        axis.add_patch(
            Rectangle(
                (x - 0.34, bottom),
                0.68,
                height,
                facecolor=colour,
                edgecolor=colour,
                linewidth=0.4,
                zorder=4,
            )
        )
    count = right - left
    ticks = np.unique(np.linspace(0, count - 1, min(6, count), dtype=int))
    axis.set_xticks(ticks)
    axis.set_xticklabels(
        [
            datetime.fromtimestamp(int(series.available_time[left + item]), tz=UTC).strftime("%m-%d\n%H:%M")
            for item in ticks
        ]
    )
    axis.set_xlim(-1, max(2, count))


def draw_price_zone(
    axis: Any,
    series: Any,
    left: int,
    right: int,
    start: int,
    end: int,
    low: float,
    high: float,
    label: str,
    colour: str,
) -> None:
    x0 = x_at(series, left, right, start)
    x1 = max(x_at(series, left, right, end), x0 + 1)
    axis.add_patch(
        Rectangle(
            (x0, low),
            x1 - x0,
            high - low,
            facecolor=colour,
            edgecolor=colour,
            alpha=0.18,
            linewidth=1.0,
            zorder=2,
        )
    )
    axis.text(
        (x0 + x1) / 2,
        (low + high) / 2,
        label,
        color=TEXT,
        fontsize=7,
        ha="center",
        va="center",
        bbox={"facecolor": BG, "edgecolor": colour, "alpha": 0.75, "pad": 1.4},
        zorder=8,
    )


def draw_position_box(axis: Any, series: Any, left: int, right: int, record: dict[str, Any]) -> None:
    if not record["filledAt"] or not record["closedAt"]:
        return
    x0 = x_at(series, left, right, ts(record["filledAt"]))
    x1 = max(x_at(series, left, right, ts(record["closedAt"])), x0 + 1)
    entry = float(record["entry"])
    stop = float(record["stop"])
    target = float(record["objective"])
    axis.add_patch(
        Rectangle(
            (x0, min(entry, stop)),
            x1 - x0,
            abs(stop - entry),
            facecolor=RISK,
            edgecolor="#fb7185",
            alpha=0.18,
            linewidth=1.0,
            zorder=1,
        )
    )
    axis.add_patch(
        Rectangle(
            (x0, min(entry, target)),
            x1 - x0,
            abs(target - entry),
            facecolor=REWARD,
            edgecolor="#34d399",
            alpha=0.18,
            linewidth=1.0,
            zorder=1,
        )
    )


def style(axis: Any, title: str) -> None:
    axis.set_facecolor(BG)
    axis.set_title(title, loc="left", color=TEXT, fontsize=10, fontweight="bold")
    axis.grid(color=GRID, alpha=0.35, linewidth=0.55)
    axis.tick_params(colors=MUTED, labelsize=7)
    axis.yaxis.tick_right()
    for spine in axis.spines.values():
        spine.set_color(GRID)


def render_trade(record: dict[str, Any], frames: dict[str, Any]) -> Path:
    decision = ts(record["decisionAt"])
    filled = ts(record["filledAt"])
    closed = ts(record["closedAt"])
    sweep = ts(record["sweepAt"])
    source_from = ts(record["sourceFrom"])
    hold_minutes = int(record["holdingMinutes"])
    hold_tf = "M1" if hold_minutes <= 180 else "M5" if hold_minutes <= 1440 else "M15"
    panels = [
        ("H1", source_from, closed, 36, 12, 120, "MAP"),
        (record["sourceTf"], source_from, decision, 45, 45, 180, "SOURCE"),
        ("M1", sweep, filled, 35, 45, 140, "TRIGGER"),
        (hold_tf, filled, closed, 18, 18, 220, "HOLD"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), constrained_layout=True)
    axes = axes.ravel()
    for axis, (timeframe, start, end, pre, post, cap, role) in zip(axes, panels):
        series = frames[timeframe]
        left, right = window(series, start, end, pre, post, cap)
        draw_candles(axis, series, left, right)
        if role in {"MAP", "SOURCE"}:
            draw_price_zone(
                axis,
                series,
                left,
                right,
                source_from,
                closed,
                min(record["sourceZone"]),
                max(record["sourceZone"]),
                f"{record['sourceTf']} 원인 OB",
                SOURCE,
            )
        if role == "TRIGGER":
            draw_price_zone(
                axis,
                series,
                left,
                right,
                decision,
                closed,
                min(record["entryZone"]),
                max(record["entryZone"]),
                record["entryZoneType"],
                ENTRY_ZONE,
            )
            sx = x_at(series, left, right, sweep)
            axis.scatter(
                [sx],
                [record["sweepPrice"]],
                marker="v" if record["direction"] == "short" else "^",
                s=34,
                color=SWEEP,
                zorder=9,
            )
            cx = x_at(series, left, right, ts(record["chochAt"]))
            axis.text(
                cx,
                record["entry"],
                "CHoCH",
                color=BEAR if record["direction"] == "short" else BULL,
                fontsize=7,
                ha="center",
                va="bottom" if record["direction"] == "long" else "top",
                zorder=9,
            )
        if role in {"MAP", "HOLD"}:
            draw_position_box(axis, series, left, right, record)
        if role in {"MAP", "SOURCE"}:
            axis.axhline(
                record["objective"],
                color=LIQUIDITY,
                linewidth=0.9,
                linestyle=(0, (4, 4)),
                alpha=0.85,
                zorder=0,
            )
            axis.text(
                max(1, right - left - 3),
                record["objective"],
                record["objectiveKind"],
                color=LIQUIDITY,
                fontsize=7,
                ha="right",
                va="bottom",
            )
        if role == "HOLD":
            values = [record["entry"], record["stop"], record["objective"]]
            candle_low = float(np.min(series.low[left:right]))
            candle_high = float(np.max(series.high[left:right]))
            low = min(values + [candle_low])
            high = max(values + [candle_high])
            margin = max((high - low) * 0.07, 0.4)
            axis.set_ylim(low - margin, high + margin)
        style(axis, f"{role} · {timeframe}")
    colour = "#34d399" if record["result"] == "TP" else "#fb7185"
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"{record['tradeId']} · {record['scenario']} · {record['result']} "
        f"{record['earnedR']:+.2f}R · {record['holdingMinutes']}분",
        color=colour,
        fontsize=14,
        fontweight="bold",
    )
    destination = CHARTS / f"{record['tradeId']}.png"
    fig.savefig(destination, dpi=145, facecolor=BG)
    plt.close(fig)
    return destination


def write_outputs(records: list[dict[str, Any]]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "weekly_path_audit.jsonl").open("w", encoding="utf-8") as handle:
        for item in EPISODES:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    with (OUTPUT / "counterfactual_trades.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fields = [
            "tradeId",
            "scenario",
            "direction",
            "decisionAt",
            "filledAt",
            "closedAt",
            "sourceTf",
            "parentId",
            "attempt",
            "entry",
            "stop",
            "objective",
            "result",
            "plannedR",
            "earnedR",
            "holdingMinutes",
            "classification",
        ]
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        for item in records:
            writer.writerow({field: item.get(field) for field in fields})
    (OUTPUT / "frozen_rule_contract_v3.json").write_text(
        json.dumps(RULE_CONTRACT, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    r_values = [float(item["earnedR"]) for item in records]
    wins = [value for value in r_values if value > 0]
    losses = [value for value in r_values if value < 0]
    curve = np.cumsum(r_values)
    peaks = np.maximum.accumulate(np.r_[0.0, curve])[:-1]
    max_drawdown = float(np.max(peaks - curve))
    profit_factor = sum(wins) / abs(sum(losses)) if losses else float("inf")
    summary = f"""# Mentor Week Reverse Engineering V3

## 성격

이 결과는 2025-06-16~20 전체 경로를 본 뒤 만든 **in-sample 사후 규칙 역설계**다.
다음 미사용 주간에 규칙을 동결해 적용하기 전까지 수익성 증거로 사용하지 않는다.

## 결과

- HTF source 접촉 에피소드: {len(EPISODES)}건
- 체결 반사실 거래: {len(records)}건
- 승/패: {len(wins)}승 / {len(losses)}패
- 승률: {len(wins) / len(records) * 100:.2f}%
- 합계: {sum(r_values):+.2f}R
- Profit Factor: {profit_factor:.2f}
- 최대 낙폭: {max_drawdown:.2f}R

## 기존 해석의 핵심 오류

1. M1 실행 시도 손절을 HTF 부모 시나리오 종료로 오해했다.
2. 같은 부모 OB 안의 후속 독립 sweep-CHoCH-FVG 체인을 놓쳤다.
3. 6월 17일 short와 long에서 가장 가까운 유동성을 건너뛰어, 맞은 방향을 손실로 바꿨다.
4. M1 entry OB를 HTF refinement와 동일시했다. V3에서는 부모 source와 실행 attempt를 별도 상태로 관리한다.
5. source 접촉 직후 트리거가 없다는 이유로 감시를 끝냈다. source distal 몸통 무효화 또는 objective 소진 전까지 유지한다.

## 반복 가능한 결론

- 부모 시나리오: H1 map + M30/M15 원인 OB + 동결 objective.
- 실행 시도: source 접촉 후 M1 sweep → 별도 CHoCH → FVG/OB → retest.
- 실행 SL: sweep extreme과 CHoCH 실행 OB distal 중 더 먼 곳 밖에 spread를 더한다.
- 실행 SL은 부모 시나리오를 죽이지 않는다. 새 물리적 체인이 생기면 같은 objective로 재무장한다.
- 외부 지속 TP는 가장 가까운 미소진 외부 유동성, 내부 회전 TP는 첫 반대 유동성이다.
- 위 계약을 모두 지킨 손절만 `MARKET_UNCERTAINTY`로 분류한다.

## 손실의 의미

- R01/R03: 첫 실행 구조가 무효화됐지만 같은 규칙의 후속 구조가 손실을 회수했다.
- R08: 첫 short가 손절된 뒤 같은 M15 source에서 R09가 새 체인으로 +4.38R을 냈다.
- R11/R12: 두 실행 시도 모두 손절되고 부모 M15 OB까지 무효화됐다. 이 둘은 방향 설명 오류가 아니라 주간 표본 안의 진짜 시장 불확실성이다.
"""
    (OUTPUT / "WEEK_REVERSE_ENGINEERING_V3_SUMMARY.md").write_text(
        summary, encoding="utf-8"
    )

    rows = "\n".join(
        f"<tr><td>{item['tradeId']}</td><td>{item['scenario']}</td>"
        f"<td>{item['result']}</td><td>{item['earnedR']:+.2f}R</td>"
        f"<td>{item['holdingMinutes']}분</td></tr>"
        for item in records
    )
    cards = "\n".join(
        f"<section><h2>{item['tradeId']} · {item['scenario']} · "
        f"{item['result']} {item['earnedR']:+.2f}R</h2>"
        f"<img src='trade_charts/{item['tradeId']}.png' alt='{item['tradeId']}'></section>"
        for item in records
    )
    html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>Mentor Week V3</title>
<style>
body{{margin:0;background:#080c12;color:#e2e8f0;font-family:Segoe UI,Malgun Gothic,sans-serif}}
main{{max-width:1500px;margin:auto;padding:24px}} table{{border-collapse:collapse;width:100%;margin:18px 0 30px}}
th,td{{border-bottom:1px solid #263241;padding:10px;text-align:left}} section{{margin:32px 0}}
img{{width:100%;display:block;border:1px solid #263241}} .note{{color:#fbbf24}}
</style></head><body><main><h1>Mentor Week Reverse Engineering V3</h1>
<p class="note">전체 경로를 본 사후 규칙 역설계입니다. 다음 미사용 주간 블라인드 검증 전에는 edge 증거가 아닙니다.</p>
<table><thead><tr><th>ID</th><th>시나리오</th><th>결과</th><th>R</th><th>보유</th></tr></thead>
<tbody>{rows}</tbody></table>{cards}</main></body></html>"""
    (OUTPUT / "TRADE_REVIEW.html").write_text(html, encoding="utf-8")


def main() -> int:
    warmup = ts("2025-06-09T00:00:00+00:00")
    end = ts("2025-06-21T23:59:00+00:00")
    m1, _ = load_m1_npz(DATASET, warmup, end)
    frames = build_timeframes(m1)
    records = [simulate_trade(m1, record) for record in TRADES]
    unexpected = [
        item["tradeId"]
        for item in records
        if item["result"] not in {"SL", "TP"} or item["ambiguous"]
    ]
    if unexpected:
        raise SystemExit(f"Unresolved or ambiguous replay results: {unexpected}")
    write_outputs(records)
    for record in records:
        render_trade(record, frames)
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "episodes": len(EPISODES),
                "trades": len(records),
                "wins": sum(item["result"] == "TP" for item in records),
                "losses": sum(item["result"] == "SL" for item in records),
                "totalR": round(sum(float(item["earnedR"]) for item in records), 4),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
