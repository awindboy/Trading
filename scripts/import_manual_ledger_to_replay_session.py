"""Import a completed blind-manual ledger into the interactive replay workspace."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge import mt5_bridge  # noqa: E402
from scripts.mentor_semantic_validation import (  # noqa: E402
    summarize_semantic_audits,
    validate_order_semantics,
)


UTC = timezone.utc
TF_SECONDS = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800, "H1": 3600, "H4": 14400}
BULL = "#2dd4bf"
BEAR = "#fb7185"
SWEEP = "#fbbf24"


def parse_time(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.astimezone(UTC).timestamp())


def parse_origin_time(zone: dict[str, Any]) -> int | None:
    text = str(zone.get("originCandles") or "")
    matched = re.search(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})", text)
    if not matched:
        return None
    return parse_time(f"{matched.group(1)}T{matched.group(2)}:00+00:00")


def iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def aggregate(rates: np.ndarray, seconds: int) -> list[dict[str, float | int]]:
    buckets = (rates["time"] // seconds) * seconds
    starts = np.flatnonzero(np.r_[True, buckets[1:] != buckets[:-1]])
    ends = np.r_[starts[1:], len(rates)]
    return [
        {
            "time": int(buckets[left]),
            "open": float(rates["open"][left]),
            "high": float(np.max(rates["high"][left:right])),
            "low": float(np.min(rates["low"][left:right])),
            "close": float(rates["close"][right - 1]),
        }
        for left, right in zip(starts, ends)
    ]


def prices_match(left: float, right: float, point: float) -> bool:
    return abs(left - right) <= max(point * 1.1, 1e-9)


def validate_fvg(
    series: dict[str, list[dict[str, float | int]]],
    timeframe: str,
    zone: dict[str, Any],
    cutoff: int,
    direction: str,
    point: float,
) -> dict[str, Any]:
    low = float(zone["low"])
    high = float(zone["high"])
    seconds = TF_SECONDS[timeframe]
    bars = [
        bar
        for bar in series[timeframe]
        if int(bar["time"]) + seconds <= cutoff
    ]
    for index in range(len(bars) - 1, 1, -1):
        first = bars[index - 2]
        third = bars[index]
        if direction == "long":
            gap_low = float(first["high"])
            gap_high = float(third["low"])
            valid_gap = gap_high > gap_low
        else:
            gap_low = float(third["high"])
            gap_high = float(first["low"])
            valid_gap = gap_high > gap_low
        if (
            valid_gap
            and prices_match(gap_low, low, point)
            and prices_match(gap_high, high, point)
        ):
            return {
                "valid": True,
                "originTime": int(third["time"]),
                "reason": f"{timeframe} 3캔들 wick gap 일치",
            }
    return {
        "valid": False,
        "originTime": None,
        "reason": f"{timeframe} 원본 봉에서 {low:.2f}~{high:.2f} FVG를 확인할 수 없음",
    }


def validate_ob(
    series: dict[str, list[dict[str, float | int]]],
    timeframe: str,
    zone: dict[str, Any],
    cutoff: int,
    direction: str,
    point: float,
) -> dict[str, Any]:
    low = float(zone["low"])
    high = float(zone["high"])
    seconds = TF_SECONDS[timeframe]
    declared_origin = parse_origin_time(zone)
    matching_prices = False
    for bar in reversed(series[timeframe]):
        if int(bar["time"]) + seconds > cutoff:
            continue
        if declared_origin is not None and int(bar["time"]) != declared_origin:
            continue
        actual_low = float(bar["low"])
        actual_high = float(bar["high"])
        geometry_matches = prices_match(actual_low, low, point) and prices_match(actual_high, high, point)
        if declared_origin is None and not geometry_matches:
            continue
        is_opposite_candle = (
            float(bar["close"]) < float(bar["open"])
            if direction == "long"
            else float(bar["close"]) > float(bar["open"])
        )
        if is_opposite_candle:
            return {
                "valid": True,
                "originTime": int(bar["time"]),
                "actualLow": actual_low,
                "actualHigh": actual_high,
                "geometryCorrected": not geometry_matches,
                "reason": (
                    f"{timeframe} 원본 반대색 캔들 일치"
                    if geometry_matches
                    else f"{timeframe} 원본 시각은 일치하며 표시 범위를 실제 캔들 {actual_low:.2f}~{actual_high:.2f}로 교정"
                ),
            }
        matching_prices = geometry_matches
    if matching_prices:
        return {
            "valid": False,
            "originTime": None,
            "reason": f"{timeframe} 가격 범위는 있으나 방향상 반대색 OB 캔들이 아님",
        }
    return {
        "valid": False,
        "originTime": None,
        "reason": f"{timeframe} 원본 봉에서 {low:.2f}~{high:.2f} 단일 OB 캔들을 확인할 수 없음",
    }


def validate_zone_evidence(
    series: dict[str, list[dict[str, float | int]]],
    timeframe: str,
    zone: dict[str, Any],
    cutoff: int,
    direction: str,
    point: float,
) -> dict[str, Any]:
    kind = zone_kind(zone)
    if kind == "fvg":
        return {"kind": kind, **validate_fvg(series, timeframe, zone, cutoff, direction, point)}
    if kind == "ob":
        return {"kind": kind, **validate_ob(series, timeframe, zone, cutoff, direction, point)}
    return {
        "kind": kind,
        "valid": False,
        "originTime": None,
        "reason": f"{timeframe} 원장 구간이 OB 또는 FVG로 정의되지 않음",
    }


def zone_kind(zone: dict[str, Any]) -> str:
    zone_type = str(zone.get("type") or "").upper()
    if "FVG" in zone_type:
        return "fvg"
    if "OB" in zone_type:
        return "ob"
    label = str(zone.get("label") or "").upper()
    if "FVG" in label:
        return "fvg"
    if re.search(r"\bOB\b", label):
        return "ob"
    return "poi"


def semantic_issue_text(audit: dict[str, Any]) -> str:
    labels = {
        "CAUSAL_TIME_ORDER": "인과 순서 미증명",
        "OB_STRUCTURED_BREAK_WITNESS": "OB 구조 돌파 증거 누락",
        "OB_CONFIRMED_DEPARTURE": "OB 이탈 미확인",
        "OB_RETEST_TIME_DECLARED": "OB 재접촉 시각 누락",
        "LIQUIDITY_WITNESS_DECLARED": "유동성 원본 증거 누락",
        "TRIGGER_LIQUIDITY_PRESENT": "trigger 유동성 누락",
        "SWEEP_WITNESS_DECLARED": "Sweep 원본 봉 미증명",
        "SWEEP_PENETRATES_AND_RECLAIMS": "Sweep 관통·회복 불일치",
        "CHOCH_WITNESS_DECLARED": "CHoCH 기준 봉 누락",
        "CHOCH_BODY_CLOSE_BREAK": "CHoCH 몸통 돌파 불일치",
        "FVG_THREE_BARS_AVAILABLE": "FVG 3봉 증거 누락",
        "FVG_WICK_GAP_GEOMETRY": "FVG 가격 범위 불일치",
        "ENTRY_CAUSAL_OWNERSHIP": "진입 POI 인과 귀속 실패",
        "OBJECTIVE_UNCONSUMED_AT_DECISION": "목적 유동성 선소진",
        "TP_EQUALS_OBJECTIVE": "TP와 목적 유동성 불일치",
        "SL_OUTSIDE_SOURCE_AND_SWEEP": "SL이 구조 무효화 안쪽",
    }
    issues: list[str] = []
    for code in audit.get("failureCodes") or []:
        label = labels.get(str(code), str(code))
        if label not in issues:
            issues.append(label)
    visible = issues[:5]
    suffix = f" 외 {len(issues) - 5}개" if len(issues) > 5 else ""
    return " / ".join(visible) + suffix


def add_event(events: list[dict[str, Any]], event_id: str, at: int, event_type: str, title: str, detail: str = "") -> None:
    events.append(
        {
            "id": event_id,
            "time": at,
            "type": event_type,
            "title": title,
            "detail": detail,
        }
    )


def add_drawing(
    drawings: list[dict[str, Any]],
    events: list[dict[str, Any]],
    *,
    drawing_id: str,
    kind: str,
    timeframe: str,
    direction: str,
    label: str,
    color: str,
    created_at: int,
    anchors: list[dict[str, float | int]],
) -> None:
    drawings.append(
        {
            "id": drawing_id,
            "kind": kind,
            "timeframe": timeframe,
            "direction": direction,
            "label": label,
            "color": color,
            "createdAt": created_at,
            "anchors": anchors,
            "evidenceStatus": "validated",
        }
    )
    add_event(
        events,
        f"event-{drawing_id}",
        created_at,
        "drawing",
        f"[{timeframe}] {label}",
        "동결 원장의 차트 구조 표시",
    )


def order_invalidations(order: dict[str, Any], point: float) -> tuple[float, float]:
    direction = order["direction"]
    entry = float(order["entry"])
    stop = float(order["stopLoss"])
    source = float(order.get("sourceInvalidation") or order["sweep"]["extreme"])
    zone = order["entryZone"]
    if direction == "long":
        scenario = max(stop + point, min(source, entry - point))
        trigger = max(scenario, min(float(zone["low"]), entry - point))
    else:
        scenario = min(stop - point, max(source, entry + point))
        trigger = min(scenario, max(float(zone["high"]), entry + point))
    return trigger, scenario


def decision_spread_price(rates: np.ndarray, decision_at: int, point: float) -> float:
    index = int(np.searchsorted(rates["time"], decision_at - 60, side="right") - 1)
    if index < 0:
        return point
    return max(float(rates["spread"][index]) * point, point)


def front_run_target(direction: str, objective_price: float, spread: float, point: float) -> tuple[float, float]:
    digits = max(0, int(np.ceil(-np.log10(point))))
    buffer = max(abs(spread), point)
    target = objective_price - buffer if direction == "long" else objective_price + buffer
    return round(target, digits), round(buffer, digits)


def evaluate_order(
    order: dict[str, Any],
    rates: np.ndarray,
    point: float,
    cutoff: int,
) -> dict[str, Any]:
    created_at = int(order["createdAt"])
    cancelled_at = int(order["cancelledAt"]) if order.get("cancelledAt") is not None else None
    fill_at: int | None = None
    for bar in rates:
        available_at = int(bar["time"]) + 60
        if available_at <= created_at or available_at > cutoff:
            continue
        if cancelled_at is not None and available_at >= cancelled_at:
            break
        spread = float(bar["spread"]) * point
        ask_low = float(bar["low"]) + spread
        ask_high = float(bar["high"]) + spread
        if fill_at is None:
            if order["orderType"] == "market":
                fill_at = available_at
            elif order["direction"] == "long" and ask_low <= float(order["entry"]):
                fill_at = available_at
            elif order["direction"] == "short" and float(bar["high"]) >= float(order["entry"]):
                fill_at = available_at
            else:
                continue
        stop_hit = (
            float(bar["low"]) <= float(order["stop"])
            if order["direction"] == "long"
            else ask_high >= float(order["stop"])
        )
        target_hit = (
            float(bar["high"]) >= float(order["target"])
            if order["direction"] == "long"
            else ask_low <= float(order["target"])
        )
        if stop_hit:
            return {"status": "loss", "filledAt": fill_at, "closedAt": available_at}
        if target_hit:
            return {"status": "win", "filledAt": fill_at, "closedAt": available_at}
    if fill_at is not None:
        return {"status": "filled", "filledAt": fill_at, "closedAt": None}
    if cancelled_at is not None and cancelled_at <= cutoff:
        return {"status": "cancelled", "filledAt": None, "closedAt": cancelled_at}
    return {"status": "pending", "filledAt": None, "closedAt": None}


def validate_execution_parity(
    orders: list[dict[str, Any]],
    rates: np.ndarray,
    point: float,
    execution: list[dict[str, Any]],
    cutoff: int,
) -> list[dict[str, Any]]:
    events_by_order: dict[str, list[dict[str, Any]]] = {}
    for event in execution:
        order_id = event.get("orderId")
        if order_id:
            events_by_order.setdefault(str(order_id), []).append(event)
    parity: list[dict[str, Any]] = []
    mismatches: list[str] = []
    for order in orders:
        order_id = str(order["id"])
        actual = evaluate_order(order, rates, point, cutoff)
        events = events_by_order.get(order_id, [])
        superseded_cancel_hashes = {
            str(item.get("supersededEventHash"))
            for item in events
            if item.get("event") == "ORDER_CANCELLATION_SUPERSEDED"
        }
        fill = next(
            (item for item in events if item.get("event") in {"ORDER_FILLED", "ORDER_FILLED_AND_CLOSED"}),
            None,
        )
        close = next(
            (item for item in events if item.get("event") in {"POSITION_CLOSED", "ORDER_FILLED_AND_CLOSED"}),
            None,
        )
        cancel = next(
            (
                item for item in events
                if item.get("event") == "ORDER_CANCELLED"
                and str(item.get("entryHash")) not in superseded_cancel_hashes
            ),
            None,
        )
        expected_status = (
            "cancelled"
            if cancel
            else "win"
            if close and close.get("result") == "TP"
            else "loss"
            if close and close.get("result") == "SL"
            else "filled"
            if fill
            else "pending"
        )
        expected_fill = parse_time(fill["at"]) if fill else None
        expected_close = parse_time((cancel or close)["at"]) if cancel or close else None
        matches = (
            actual["status"] == expected_status
            and actual["filledAt"] == expected_fill
            and actual["closedAt"] == expected_close
        )
        parity.append(
            {
                "orderId": order_id,
                "matches": matches,
                "expected": {
                    "status": expected_status,
                    "filledAt": expected_fill,
                    "closedAt": expected_close,
                },
                "replay": actual,
            }
        )
        if not matches:
            mismatches.append(
                f"{order_id}: expected {expected_status}/{expected_fill}/{expected_close}, "
                f"replay {actual['status']}/{actual['filledAt']}/{actual['closedAt']}"
            )
    if mismatches:
        raise RuntimeError("Replay execution parity failed:\n" + "\n".join(mismatches))
    return parity


def build_session(source: Path, session_id: str, name: str, target_mode: str) -> dict[str, Any]:
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    orders = sorted(read_jsonl(source / "manual_orders.jsonl"), key=lambda item: parse_time(item["decisionAt"]))
    execution = read_jsonl(source / "execution_ledger.jsonl")
    maps = read_jsonl(source / "hourly_map_ledger.jsonl")
    no_trades = read_jsonl(source / "no_trade_audit.jsonl")
    proof_path = source / "MANUAL_ORDER_CAUSAL_PROOF.json"
    proof_payload = json.loads(proof_path.read_text(encoding="utf-8")) if proof_path.exists() else {"orders": []}
    proofs = {item["orderId"]: item for item in proof_payload["orders"]}
    superseded_cancel_hashes = {
        str(item.get("supersededEventHash"))
        for item in execution
        if item.get("event") == "ORDER_CANCELLATION_SUPERSEDED"
    }
    cancels = {
        item["orderId"]: item
        for item in execution
        if item.get("event") == "ORDER_CANCELLED"
        and item.get("orderId")
        and str(item.get("entryHash")) not in superseded_cancel_hashes
    }
    fills = {
        item["orderId"]: item
        for item in execution
        if item.get("event") in {"ORDER_FILLED", "ORDER_FILLED_AND_CLOSED"} and item.get("orderId")
    }

    dataset_path = (ROOT / manifest["dataset"]).resolve()
    with np.load(dataset_path, allow_pickle=False) as payload:
        rates = payload["rates"]
    series = {timeframe: aggregate(rates, seconds) for timeframe, seconds in TF_SECONDS.items()}
    point = float(manifest["point"])

    week_start = parse_time(manifest["newEntriesFrom"])
    observed_through = max(
        [parse_time(item["at"]) for item in execution if item.get("at")]
        + [parse_time(manifest["newEntriesThrough"]) + 1]
    )
    week_end = max(week_start + 7 * 86400, observed_through)
    now = iso_now()
    drawings: list[dict[str, Any]] = []
    scenarios: list[dict[str, Any]] = []
    replay_orders: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    evidence_audit: list[dict[str, Any]] = []
    semantic_audits: list[dict[str, Any]] = []

    add_event(
        events,
        "event-session-start",
        week_start,
        "session",
        "OOS 주간 블라인드 재생 시작",
        "미래 봉을 보지 않고 동결한 수동 원장을 재생 프로그램에 복원한 세션",
    )

    for index, map_row in enumerate(maps, start=1):
        if not map_row.get("stateChanged"):
            continue
        at = parse_time(map_row["asOf"])
        add_event(
            events,
            f"event-map-{index:03d}",
            at,
            "note",
            f"H1 MAP · {map_row.get('decision', 'MONITOR')}",
            str(map_row.get("reason") or map_row.get("objective") or ""),
        )

    for order in orders:
        order_id = str(order["orderId"])
        decision_at = parse_time(order["decisionAt"])
        proof = proofs.get(order_id) or order.get("causalLineage") or {}
        sweep_at = parse_time(str(proof.get("sweepAt") or order["sweep"]["at"]))
        choch_at = parse_time(str(proof.get("chochAt") or order["choch"]["at"]))
        direction = str(order["direction"])
        color = BULL if direction == "long" else BEAR
        lineage = order.get("causalLineage") or {}
        parent_zone = lineage.get("parentZone")
        source_zone = lineage.get("sourceZone") or order["sourceZone"]
        source_tf = str(source_zone.get("timeframe") or order["sourceTimeframe"])
        trigger_tf = str(order["triggerTimeframe"])
        map_tf = str(order["mapTimeframe"])
        objective_price = float(order["takeProfit"])
        spread_at_decision = decision_spread_price(rates, decision_at, float(manifest["point"]))
        if target_mode == "front-run":
            target_price, target_buffer = front_run_target(
                direction,
                objective_price,
                spread_at_decision,
                float(manifest["point"]),
            )
        else:
            target_price, target_buffer = objective_price, 0.0
        lineage_entry_zone = lineage.get("entryZone") or {}
        entry_zone = {**order["entryZone"], **lineage_entry_zone}
        entry_tf = str(entry_zone.get("timeframe") or trigger_tf)
        semantic_audit = validate_order_semantics(order, series, point)
        semantic_audits.append(semantic_audit)
        trade_semantic_valid = bool(semantic_audit["valid"])
        semantic_elements = semantic_audit["elements"]
        parent_semantic_valid = bool(semantic_elements.get("parent"))
        source_semantic_valid = bool(semantic_elements.get("source"))
        entry_semantic_valid = bool(semantic_elements.get("entry"))
        sweep_semantic_valid = bool(
            semantic_elements.get("triggerLiquidity")
            and semantic_elements.get("sweep")
        )
        choch_semantic_valid = bool(semantic_elements.get("choch"))
        objective_semantic_valid = bool(semantic_elements.get("objective"))
        stop_semantic_valid = bool(semantic_elements.get("risk"))
        parent_evidence = (
            validate_zone_evidence(
                series,
                str(parent_zone["timeframe"]),
                parent_zone,
                decision_at,
                direction,
                point,
            )
            if parent_zone
            else {"kind": "ob", "valid": False, "originTime": None, "reason": "부모 HTF OB 없음"}
        )
        source_evidence = validate_zone_evidence(
            series,
            source_tf,
            source_zone,
            decision_at,
            direction,
            point,
        )
        source_is_parent = bool(
            parent_zone
            and source_tf == str(parent_zone["timeframe"])
            and zone_kind(source_zone) == zone_kind(parent_zone)
            and prices_match(float(source_zone["low"]), float(parent_zone["low"]), point)
            and prices_match(float(source_zone["high"]), float(parent_zone["high"]), point)
        )
        entry_matches_source = (
            zone_kind(entry_zone) == zone_kind(source_zone)
            and prices_match(float(entry_zone["low"]), float(source_zone["low"]), point)
            and prices_match(float(entry_zone["high"]), float(source_zone["high"]), point)
        )
        entry_evidence = {
            **source_evidence,
            "valid": bool(source_evidence["valid"] and entry_matches_source),
            "reason": (
                "진입 영역이 검증된 causal child OB와 정확히 일치"
                if source_evidence["valid"] and entry_matches_source
                else "진입 영역이 검증된 causal child OB와 일치하지 않음"
            ),
        }
        entry_evidence = validate_zone_evidence(
            series,
            entry_tf,
            entry_zone,
            decision_at,
            direction,
            point,
        )
        structural_buffer = max(spread_at_decision, point)
        if direction == "long":
            required_stop = min(
                float(source_zone["low"]),
                float(order["sourceInvalidation"]),
                float(order["sweep"]["extreme"]),
            ) - structural_buffer
            stop_valid = float(order["stopLoss"]) <= required_stop + point / 2
        else:
            required_stop = max(
                float(source_zone["high"]),
                float(order["sourceInvalidation"]),
                float(order["sweep"]["extreme"]),
            ) + structural_buffer
            stop_valid = float(order["stopLoss"]) >= required_stop - point / 2
        stop_evidence = {
            "valid": stop_valid,
            "actual": float(order["stopLoss"]),
            "required": round(required_stop, 8),
            "buffer": structural_buffer,
            "reason": (
                "선택한 causal source와 sweep의 바깥에 구조 SL이 있음"
                if stop_valid
                else (
                    f"SL {float(order['stopLoss']):.2f}이 causal source 무효화 안쪽에 있음; "
                    f"필요 구조 SL {'이하' if direction == 'long' else '이상'} {required_stop:.2f}"
                )
            ),
        }
        evidence_audit.append(
            {
                "orderId": order_id,
                "parent": parent_evidence,
                "source": source_evidence,
                "entry": entry_evidence,
                "stop": stop_evidence,
                "semantic": semantic_audit,
                "valid": bool(semantic_audit["valid"]),
            }
        )
        cancel = cancels.get(order_id)
        fill = fills.get(order_id)
        entry_end = (
            parse_time(fill["at"])
            if fill
            else parse_time(cancel["at"])
            if cancel
            else decision_at
        )
        entry_end_bar = max(week_start, entry_end - TF_SECONDS["M1"])
        if trade_semantic_valid and parent_semantic_valid and parent_zone:
            add_drawing(
                drawings,
                events,
                drawing_id=f"drawing-{order_id}-parent",
                kind=str(parent_evidence["kind"]),
                timeframe=str(parent_zone["timeframe"]),
                direction=direction,
                label="ROOT / SOURCE OB" if source_is_parent else "ROOT OB",
                color=color,
                created_at=decision_at,
                anchors=[
                    {
                        "time": int(parent_evidence["originTime"]),
                        "price": float(parent_evidence.get("actualHigh", parent_zone["high"])),
                    },
                    {
                        "time": max(decision_at - TF_SECONDS["M1"], entry_end_bar),
                        "price": float(parent_evidence.get("actualLow", parent_zone["low"])),
                    },
                ],
            )
        elif not parent_semantic_valid:
            add_event(
                events,
                f"event-{order_id}-parent-invalid",
                decision_at,
                "note",
                f"{order_id} 부모 OB 근거 무효",
                str(parent_evidence["reason"]),
            )
        if trade_semantic_valid and source_semantic_valid and not source_is_parent:
            add_drawing(
                drawings,
                events,
                drawing_id=f"drawing-{order_id}-source",
                kind=str(source_evidence["kind"]),
                timeframe=source_tf,
                direction=direction,
                label="REFINED OB",
                color=color,
                created_at=decision_at,
                anchors=[
                    {
                        "time": int(source_evidence["originTime"]),
                        "price": float(source_evidence.get("actualHigh", source_zone["high"])),
                    },
                    {
                        "time": max(decision_at - TF_SECONDS["M1"], entry_end_bar),
                        "price": float(source_evidence.get("actualLow", source_zone["low"])),
                    },
                ],
            )
        elif not source_semantic_valid:
            add_event(
                events,
                f"event-{order_id}-source-invalid",
                decision_at,
                "note",
                f"{order_id} SOURCE 근거 무효",
                str(source_evidence["reason"]),
            )
        if trade_semantic_valid and entry_semantic_valid:
            entry_kind = str(entry_evidence["kind"])
            add_drawing(
                drawings,
                events,
                drawing_id=f"drawing-{order_id}-entry",
                kind=entry_kind,
                timeframe=entry_tf,
                direction=direction,
                label="ENTRY FVG" if entry_kind == "fvg" else "ENTRY OB",
                color=color,
                created_at=decision_at,
                anchors=[
                    {
                        "time": int(entry_evidence["originTime"]),
                        "price": float(entry_evidence.get("actualHigh", entry_zone["high"])),
                    },
                    {
                        "time": max(decision_at - TF_SECONDS["M1"], entry_end_bar),
                        "price": float(entry_evidence.get("actualLow", entry_zone["low"])),
                    },
                ],
            )
        elif not entry_semantic_valid:
            add_event(
                events,
                f"event-{order_id}-entry-invalid",
                decision_at,
                "note",
                f"{order_id} ENTRY 근거 무효",
                str(entry_evidence["reason"]),
            )
        if trade_semantic_valid and sweep_semantic_valid:
            add_drawing(
            drawings,
            events,
            drawing_id=f"drawing-{order_id}-sweep",
            kind="sweep",
            timeframe=trigger_tf,
            direction=direction,
            label="SS" if direction == "long" else "BS",
            color=SWEEP,
            created_at=min(decision_at, sweep_at),
            anchors=[{"time": sweep_at, "price": float(order["sweep"]["extreme"])}],
        )
        if trade_semantic_valid and choch_semantic_valid:
            add_drawing(
            drawings,
            events,
            drawing_id=f"drawing-{order_id}-choch",
            kind="choch",
            timeframe=trigger_tf,
            direction=direction,
            label="CHoCH",
            color=color,
            created_at=min(decision_at, choch_at),
            anchors=[
                {
                    "time": max(sweep_at, choch_at - 15 * 60),
                    "price": float(order["choch"]["level"]),
                },
                {"time": choch_at, "price": float(order["choch"]["level"])},
            ],
        )
        if not semantic_audit["valid"] and entry_semantic_valid:
            add_event(
                events,
                f"event-{order_id}-semantic-invalid",
                decision_at,
                "note",
                f"{order_id} ENTRY 근거 무효",
                semantic_issue_text(semantic_audit),
            )
        objective_tf = str(
            ((lineage.get("objectiveLiquidity") or {}).get("timeframe"))
            or map_tf
        )
        if trade_semantic_valid and objective_semantic_valid:
            add_drawing(
            drawings,
            events,
            drawing_id=f"drawing-{order_id}-objective",
            kind="liquidity",
            timeframe=objective_tf,
            direction=direction,
            label=f"OBJECTIVE {objective_price:.2f}",
            color="#22d3ee",
            created_at=decision_at,
            anchors=[
                {"time": decision_at - 12 * TF_SECONDS[objective_tf], "price": objective_price},
                {"time": decision_at - TF_SECONDS["M1"], "price": objective_price},
            ],
        )

        scenario_id = f"scenario-{order_id}"
        scenarios.append(
            {
                "id": scenario_id,
                "createdAt": decision_at,
                "title": f"{order_id} · {order['scope']}",
                "scope": str(order["scope"]),
                "direction": direction,
                "mapTimeframe": map_tf,
                "sourceTimeframe": source_tf,
                "objective": str(order["objective"]),
                "invalidation": f"{float(order['sourceInvalidation']):.2f} source invalidation 바깥에서 시나리오 무효",
                "waitingFor": f"{order['sweep']['description']} → {order['choch']['description']} → refined OB 첫 retest",
                "thesis": f"{order['map']} {order['reason']}",
            }
        )
        add_event(
            events,
            f"event-{scenario_id}",
            decision_at,
            "scenario",
            f"{order_id} {order['scope']}",
            f"{direction.upper()} · {map_tf}→{source_tf}→{trigger_tf}",
        )

        trigger_invalidation, scenario_invalidation = order_invalidations(order, float(manifest["point"]))
        entry_label = str(entry_zone.get("label") or entry_zone.get("type") or "").upper()
        replay_order = {
            "id": order_id,
            "createdAt": decision_at,
            "sourceEvidenceValid": bool(parent_semantic_valid and source_semantic_valid),
            "entryEvidenceValid": entry_semantic_valid,
            "stopEvidenceValid": stop_semantic_valid,
            "semanticEvidenceValid": bool(semantic_audit["valid"]),
            "performanceEligible": bool(semantic_audit["performanceEligible"]),
            "semanticAudit": {
                "elements": semantic_elements,
                "failureCodes": semantic_audit["failureCodes"],
                "failureReasons": semantic_audit["failureReasons"],
            },
            "requiredStructuralStop": float(stop_evidence["required"]),
            "evidenceIssue": " · ".join(
                reason
                for valid, reason in (
                    (bool(parent_evidence["valid"]), f"PARENT: {parent_evidence['reason']}"),
                    (bool(source_evidence["valid"]), f"SOURCE: {source_evidence['reason']}"),
                    (bool(entry_evidence["valid"]), f"ENTRY: {entry_evidence['reason']}"),
                    (bool(stop_evidence["valid"]), f"SL: {stop_evidence['reason']}"),
                )
                if not valid
            ),
            "evidenceIssue": semantic_issue_text(semantic_audit),
            "direction": direction,
            "executionModel": "delivery-fvg-replacement" if "FVG" in entry_label else "refined-ob-retest",
            "orderType": "limit",
            "entry": float(order["entry"]),
            "triggerInvalidation": trigger_invalidation,
            "scenarioInvalidation": scenario_invalidation,
            "stop": float(order["stopLoss"]),
            "objectivePrice": objective_price,
            "targetBuffer": target_buffer,
            "target": target_price,
            "rationale": str(order["reason"]),
            "scenarioId": scenario_id,
            "scenarioScope": str(order["scope"]),
        }
        if cancel:
            replay_order["cancelledAt"] = parse_time(cancel["at"])
            replay_order["cancelReason"] = str(cancel.get("reason") or "주문 취소")
        replay_orders.append(replay_order)
        add_event(
            events,
            f"event-order-{order_id}",
            decision_at,
            "order",
            f"{order_id} {direction.upper()} LIMIT 주문 동결",
            f"{float(order['entry']):.2f} · objective {objective_price:.2f} · TP {target_price:.2f} · buffer {target_buffer:.2f}",
        )
        if cancel:
            add_event(
                events,
                f"event-cancel-{order_id}",
                parse_time(cancel["at"]),
                "order",
                f"{order_id} 주문 취소",
                str(cancel.get("reason") or "주문 취소"),
            )

    for index, no_trade in enumerate(no_trades, start=1):
        add_event(
            events,
            f"event-no-trade-{index:02d}",
            parse_time(no_trade["asOf"]),
            "note",
            f"NO TRADE · {no_trade['poi']['label']}",
            str(no_trade["reason"]),
        )

    parity: list[dict[str, Any]] = []
    recalculated: list[dict[str, Any]] = []
    if target_mode == "original":
        parity = validate_execution_parity(
            replay_orders,
            rates,
            float(manifest["point"]),
            execution,
            observed_through,
        )
    else:
        recalculated = [
            {
                "orderId": str(order["id"]),
                **evaluate_order(order, rates, float(manifest["point"]), observed_through),
            }
            for order in replay_orders
        ]
    semantic_summary = summarize_semantic_audits(semantic_audits)
    session = {
        "id": session_id,
        "name": name,
        "symbol": str(manifest["symbol"]),
        "dataset": dataset_path.name,
        "weekStart": week_start,
        "weekEnd": week_end,
        "cursorTime": week_start,
        "maxSeenTime": observed_through,
        "timeframe": "H1",
        "speed": 60,
        "createdAt": now,
        "updatedAt": now,
        "drawings": sorted(drawings, key=lambda item: (item["createdAt"], item["id"])),
        "scenarios": sorted(scenarios, key=lambda item: item["createdAt"]),
        "orders": replay_orders,
        "events": sorted(events, key=lambda item: (item["time"], item["id"])),
        "importAudit": {
            "executionParity": True if target_mode == "original" else None,
            "verifiedOrders": len(parity),
            "recalculatedOrders": len(recalculated),
            "targetMode": target_mode,
            "targetFormula": (
                "TP=objective liquidity exactly"
                if target_mode == "original"
                else "long=objective-buffer; short=objective+buffer; buffer=max(decision spread, 1 tick)"
            ),
            "recalculatedExecutions": recalculated,
            "sourceManifest": str(source / "manifest.json"),
            "evidenceValidation": {
                "semantic": {
                    "validOrders": semantic_summary["validOrders"],
                    "invalidOrders": semantic_summary["invalidOrders"],
                    "elementCounts": semantic_summary["elementCounts"],
                    "failureCounts": semantic_summary["failureCounts"],
                },
                "validOrders": sum(1 for item in evidence_audit if item["valid"]),
                "invalidOrders": sum(1 for item in evidence_audit if not item["valid"]),
                "parentValid": sum(1 for item in evidence_audit if item["parent"]["valid"]),
                "sourceValid": sum(1 for item in evidence_audit if item["source"]["valid"]),
                "entryValid": sum(1 for item in evidence_audit if item["entry"]["valid"]),
                "structuralStopValid": sum(1 for item in evidence_audit if item["stop"]["valid"]),
                "structuralStopInvalid": sum(1 for item in evidence_audit if not item["stop"]["valid"]),
                "geometryCorrections": [
                    {
                        "orderId": item["orderId"],
                        "layer": layer,
                        "reason": item[layer]["reason"],
                    }
                    for item in evidence_audit
                    for layer in ("parent", "source")
                    if item[layer].get("geometryCorrected")
                ],
                "orders": evidence_audit,
            },
        },
    }
    return session


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--target-mode", choices=("original", "front-run"), default="original")
    args = parser.parse_args()
    source = args.source.resolve()
    session = build_session(source, args.session_id, args.name, args.target_mode)
    exported = source / (
        "interactive_replay_session_front_run.json"
        if args.target_mode == "front-run"
        else "interactive_replay_session.json"
    )
    exported.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    saved = mt5_bridge.save_replay_session(session)
    print(
        json.dumps(
            {
                "ok": saved["ok"],
                "sessionId": session["id"],
                "orders": len(session["orders"]),
                "scenarios": len(session["scenarios"]),
                "drawings": len(session["drawings"]),
                "events": len(session["events"]),
                "targetMode": session["importAudit"]["targetMode"],
                "executionParityOrders": session["importAudit"]["verifiedOrders"],
                "recalculatedOrders": session["importAudit"]["recalculatedOrders"],
                "weekStart": session["weekStart"],
                "weekEnd": session["weekEnd"],
                "maxSeenTime": session["maxSeenTime"],
                "exported": str(exported),
                "storage": saved["storage"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
