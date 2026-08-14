"""Build the corrected Jan 6-17 Mentor replay audit.

This is deliberately not a new blind replay. It re-adjudicates the two
completed manual weeks with rules frozen after the review:

* hard SL belongs outside the scenario invalidation, not the M1 trigger;
* a first retest of a delivery FVG may replace a failed local trigger;
* the original scenario objective is not moved.

The script never edits the original weekly ledgers.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import shutil
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
WEEK_ONE = ROOT / "output" / "mentor_week_2025-01-06_10_manual_ground_truth" / "replay"
WEEK_TWO = ROOT / "output" / "mentor_week_2025-01-13_17_manual_ground_truth" / "replay"
OUTPUT = ROOT / "output" / "mentor_two_week_corrected_replay_2025-01-06_17"
UTC = timezone.utc
POINT = 0.01


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def parse_time(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.astimezone(UTC).timestamp())


def iso_time(value: int) -> str:
    return datetime.fromtimestamp(value, tz=UTC).isoformat()


def decision_spread(rates: np.ndarray, value: str) -> float:
    timestamp = parse_time(value)
    index = int(np.searchsorted(rates["time"], timestamp, side="left"))
    if index >= len(rates) or int(rates[index]["time"]) != timestamp:
        index = max(0, index - 1)
    return float(rates[index]["spread"]) * POINT


def simulate_exit(
    rates: np.ndarray,
    direction: str,
    filled_at: str,
    stop_loss: float,
    take_profit: float,
) -> tuple[str, str]:
    start = int(np.searchsorted(rates["time"], parse_time(filled_at), side="left"))
    for bar in rates[start:]:
        spread = float(bar["spread"]) * POINT
        bid_low = float(bar["low"])
        bid_high = float(bar["high"])
        if direction == "long":
            stop_hit = bid_low <= stop_loss
            target_hit = bid_high >= take_profit
        else:
            stop_hit = bid_high + spread >= stop_loss
            target_hit = bid_low + spread <= take_profit
        if stop_hit or target_hit:
            # No tick history is attached to this audit. Same-bar ambiguity is
            # resolved conservatively in favor of the stop.
            return iso_time(int(bar["time"])), "SL" if stop_hit else "TP"
    raise RuntimeError(f"Position did not close: {direction} {filled_at}")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def load_week_one_fills() -> dict[str, str]:
    with (WEEK_ONE / "trade_review.csv").open(encoding="utf-8-sig", newline="") as handle:
        return {
            row["order_id"]: row["filled_at"]
            for row in csv.DictReader(handle)
            if row.get("filled_at")
        }


def load_week_two_fills() -> dict[str, str]:
    events = read_jsonl(WEEK_TWO / "execution_ledger.jsonl")
    return {
        row["orderId"]: row["at"]
        for row in events
        if row.get("event") in {"ORDER_FILLED", "ORDER_FILLED_AND_CLOSED"}
    }


def constrain_to_h1(node: Any) -> Any:
    if isinstance(node, dict):
        return {key: constrain_to_h1(value) for key, value in node.items()}
    if isinstance(node, list):
        return [constrain_to_h1(value) for value in node]
    if isinstance(node, str):
        return (
            node.replace("H4/H1", "H1")
            .replace("H4/M30", "H1/M30")
            .replace("H4", "H1")
        )
    return node


def clone_order(
    source: dict[str, Any],
    order_id: str,
    stop_loss: float,
    model: str,
    scenario_invalidation: float,
) -> dict[str, Any]:
    order = constrain_to_h1(json.loads(json.dumps(source, ensure_ascii=False)))
    order["orderId"] = order_id
    order["stopLoss"] = round(stop_loss, 2)
    order["executionModel"] = model
    if order["mapTimeframe"] == "H4":
        order["mapTimeframe"] = "H1"
    if order["sourceTimeframe"] == "H4":
        order["sourceTimeframe"] = "H1"
    order["triggerTimeframe"] = "M1"
    order["triggerInvalidation"] = float(source["sweep"]["extreme"])
    order["scenarioInvalidation"] = round(scenario_invalidation, 2)
    order["correctionAudit"] = {
        "sourceOrderId": source["orderId"],
        "originalStopLoss": float(source["stopLoss"]),
        "rule": "SCENARIO_INVALIDATION_SL",
    }
    order.pop("previousHash", None)
    order.pop("entryHash", None)
    return order


M1_EXECUTION_OVERRIDES: dict[str, dict[str, Any]] = {
    "W1-Q1M001": {
        "decisionAt": "2025-01-06T03:32:00+00:00",
        "filledAt": "2025-01-06T03:33:00+00:00",
        "entry": 2644.57,
        "entryZone": {
            "label": "First M1 bearish FVG after body acceptance below 2644.44",
            "low": 2644.57,
            "high": 2644.71,
        },
        "choch": {
            "description": "M1 bearish body acceptance through the 2644.44 live reaction low.",
            "level": 2644.44,
        },
    },
    "W1-Q1M003": {
        "decisionAt": "2025-01-06T11:30:00+00:00",
        "filledAt": "2025-01-06T11:31:00+00:00",
        "entry": 2633.09,
        "entryZone": {
            "label": "First M1 bearish FVG after acceptance below the 2633.69 live swing",
            "low": 2633.09,
            "high": 2634.04,
        },
        "choch": {
            "description": "M1 bodies confirmed the bearish change below 2633.69.",
            "level": 2633.69,
        },
    },
    "W2-Q1M006": {
        "decisionAt": "2025-01-17T11:25:00+00:00",
        "filledAt": "2025-01-17T11:32:00+00:00",
        "entry": 2707.90,
        "entryZone": {
            "label": "First M1 bearish FVG after acceptance below 2709.74",
            "low": 2707.90,
            "high": 2708.93,
        },
        "choch": {
            "description": "M1 bearish acceptance through the 2709.74 protected reaction low.",
            "level": 2709.74,
        },
    },
}


def apply_m1_execution_override(order: dict[str, Any]) -> str | None:
    override = M1_EXECUTION_OVERRIDES.get(order["orderId"])
    if override is None:
        return None
    order["decisionAt"] = override["decisionAt"]
    order["entry"] = override["entry"]
    order["entryZone"] = override["entryZone"]
    order["choch"] = override["choch"]
    order["reason"] = (
        f"{order['reason']} The execution was re-frozen on the first M1 "
        "displacement-FVG retest instead of the former M5 trigger."
    )
    order["correctionAudit"]["m1ExecutionOverride"] = True
    return str(override["filledAt"])


def delivery_fvg_replacement() -> dict[str, Any]:
    return {
        "schema": "manual-order-v2",
        "orderId": "W1-FVG01",
        "decisionAt": "2025-01-06T16:49:00+00:00",
        "direction": "long",
        "scope": "INTERNAL_ROTATION",
        "mapTimeframe": "H1",
        "sourceTimeframe": "M15",
        "triggerTimeframe": "M1",
        "map": (
            "The first 2621.68 reversal failed, but the same sell-side excursion "
            "extended to 2614.60 and then produced a new bullish displacement."
        ),
        "sourceLiquidity": (
            "Final sell-side extension to 2614.60, followed by acceptance above "
            "the post-low M1 reaction structure."
        ),
        "sourceZone": {
            "label": "M15 old-swing reversal context after the 2614.60 extension",
            "low": 2614.60,
            "high": 2624.73,
        },
        "sweep": {
            "description": "The old sell-side excursion completed at 2614.60.",
            "extreme": 2614.60,
        },
        "choch": {
            "description": "M1 bullish displacement accepted above the post-low reaction high.",
            "level": 2629.92,
        },
        "entryZone": {
            "label": "First M1 bullish delivery FVG after the final low",
            "low": 2627.68,
            "high": 2628.88,
        },
        "entry": 2628.88,
        "stopLoss": 2614.33,
        "takeProfit": 2638.19,
        "sourceInvalidation": 2614.60,
        "scenarioInvalidation": 2614.60,
        "triggerInvalidation": 2627.48,
        "executionModel": "DELIVERY_FVG_REPLACEMENT",
        "objective": "The original first internal buy-side pool at 2638.19.",
        "reason": (
            "The old local trigger was not rescued. A new final-low sweep, "
            "displacement and first FVG retest created a separate replacement "
            "ticket with the unchanged internal objective."
        ),
        "riskUnit": "1R",
        "correctionAudit": {
            "sourceOrderId": "Q1M004",
            "originalStopLoss": 2621.40,
            "rule": "NEW_CHAIN_AFTER_FINAL_SWEEP_AND_DELIVERY_FVG",
        },
    }


def build_orders(rates: np.ndarray) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, Any]]]:
    week_one_orders = {row["orderId"]: row for row in read_jsonl(WEEK_ONE / "manual_orders.jsonl")}
    week_two_orders = {row["orderId"]: row for row in read_jsonl(WEEK_TWO / "manual_orders.jsonl")}
    week_one_fills = load_week_one_fills()
    week_two_fills = load_week_two_fills()

    # The scenario extremes below were already visible when each decision was
    # made. The current decision-bar spread is applied outside that extreme.
    week_one_rules = [
        ("Q1M001", 2647.67, 2647.25, "HTF_OB_REACTION"),
        ("Q1M002", 2647.25 + decision_spread(rates, week_one_orders["Q1M002"]["decisionAt"]), 2647.25, "HTF_OB_REACTION"),
        ("Q1M003", 2647.25 + decision_spread(rates, "2025-01-06T11:30:00+00:00"), 2647.25, "DELIVERY_FVG_ADDON"),
        ("Q1M004", 2621.40, 2621.68, "OLD_SWING_FVG_REVERSAL"),
        ("Q1M005", 2614.60 - decision_spread(rates, week_one_orders["Q1M005"]["decisionAt"]), 2614.60, "DELIVERY_FVG_ADDON"),
        ("Q1M007", 2651.54, 2651.24, "HTF_OB_REACTION"),
        ("Q1M008", 2641.88 - decision_spread(rates, week_one_orders["Q1M008"]["decisionAt"]), 2641.88, "HTF_OB_REACTION"),
        ("Q1M009", 2641.88 - decision_spread(rates, week_one_orders["Q1M009"]["decisionAt"]), 2641.88, "DELIVERY_FVG_ADDON"),
        ("Q1M010", 2667.78, 2667.47, "OLD_SWING_FVG_REVERSAL"),
        ("Q1M011", 2678.18 + decision_spread(rates, week_one_orders["Q1M011"]["decisionAt"]), 2678.18, "HTF_OB_REACTION"),
        ("Q1M012", 2678.18 + decision_spread(rates, week_one_orders["Q1M012"]["decisionAt"]), 2678.18, "DELIVERY_FVG_ADDON"),
    ]
    week_two_rules = [
        ("Q1M001", 2675.13 + decision_spread(rates, week_two_orders["Q1M001"]["decisionAt"]), 2675.13, "HTF_OB_REACTION"),
        ("Q1M003", 2669.21 - decision_spread(rates, week_two_orders["Q1M003"]["decisionAt"]), 2669.21, "DELIVERY_FVG_REPLACEMENT"),
        ("Q1M004", 2700.10 - decision_spread(rates, week_two_orders["Q1M004"]["decisionAt"]), 2700.10, "HTF_OB_REACTION"),
        ("Q1M006", 2724.54 + decision_spread(rates, "2025-01-17T11:25:00+00:00"), 2724.54, "DELIVERY_FVG_REPLACEMENT"),
    ]

    orders: list[dict[str, Any]] = []
    fills: dict[str, str] = {}
    audit: list[dict[str, Any]] = []
    for source_id, stop, invalidation, model in week_one_rules:
        corrected_id = f"W1-{source_id}"
        order = clone_order(week_one_orders[source_id], corrected_id, stop, model, invalidation)
        override_fill = apply_m1_execution_override(order)
        orders.append(order)
        fills[corrected_id] = override_fill or week_one_fills[source_id]
        audit.append({
            "week": "2025-01-06~10",
            "sourceOrderId": source_id,
            "correctedOrderId": corrected_id,
            "action": (
                "CORRECT_M1_TRIGGER_AND_SCENARIO_SL"
                if override_fill
                else "KEEP"
                if round(float(week_one_orders[source_id]["stopLoss"]), 2) == round(stop, 2)
                else "CORRECT_SCENARIO_SL"
            ),
            "oldStop": float(week_one_orders[source_id]["stopLoss"]),
            "newStop": round(stop, 2),
            "reason": "Hard SL is placed outside the scenario owner extreme and decision-time spread.",
        })

    fvg_order = delivery_fvg_replacement()
    orders.append(fvg_order)
    fills[fvg_order["orderId"]] = "2025-01-06T16:50:00+00:00"
    audit.append({
        "week": "2025-01-06~10",
        "sourceOrderId": "Q1M004",
        "correctedOrderId": fvg_order["orderId"],
        "action": "ADD_DELIVERY_FVG_REPLACEMENT",
        "oldStop": "",
        "newStop": fvg_order["stopLoss"],
        "reason": "A new final-low sweep and displacement formed after the first reversal ticket was invalidated.",
    })

    for source_id, stop, invalidation, model in week_two_rules:
        corrected_id = f"W2-{source_id}"
        order = clone_order(week_two_orders[source_id], corrected_id, stop, model, invalidation)
        override_fill = apply_m1_execution_override(order)
        orders.append(order)
        fills[corrected_id] = override_fill or week_two_fills[source_id]
        audit.append({
            "week": "2025-01-13~17",
            "sourceOrderId": source_id,
            "correctedOrderId": corrected_id,
            "action": "CORRECT_M1_TRIGGER_AND_SCENARIO_SL" if override_fill else "CORRECT_SCENARIO_SL",
            "oldStop": float(week_two_orders[source_id]["stopLoss"]),
            "newStop": round(stop, 2),
            "reason": "The prior SL represented the trigger, not the frozen scenario invalidation.",
        })

    for source_id in ("Q1M006",):
        audit.append({
            "week": "2025-01-06~10",
            "sourceOrderId": source_id,
            "correctedOrderId": "",
            "action": "NO_FILL",
            "oldStop": week_one_orders[source_id]["stopLoss"],
            "newStop": "",
            "reason": "The pending entry was not reached before the objective.",
        })
    for source_id in ("Q1M002", "Q1M005", "Q1M007"):
        audit.append({
            "week": "2025-01-13~17",
            "sourceOrderId": source_id,
            "correctedOrderId": "",
            "action": "NO_FILL",
            "oldStop": week_two_orders[source_id]["stopLoss"],
            "newStop": "",
            "reason": "No first delivery-FVG retest completed before the frozen objective was delivered.",
        })

    orders.sort(key=lambda row: parse_time(row["decisionAt"]))
    return orders, fills, audit


def statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["pnlR"]) for row in rows]
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = abs(sum(value for value in values if value < 0))
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    loss_streak = 0
    max_loss_streak = 0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
        loss_streak = loss_streak + 1 if value < 0 else 0
        max_loss_streak = max(max_loss_streak, loss_streak)
    return {
        "trades": len(rows),
        "wins": sum(value > 0 for value in values),
        "losses": sum(value < 0 for value in values),
        "winRate": sum(value > 0 for value in values) / len(values) if values else 0.0,
        "netR": sum(values),
        "profitFactor": gross_profit / gross_loss if gross_loss else None,
        "expectancyR": sum(values) / len(values) if values else 0.0,
        "maxDrawdownR": max_drawdown,
        "maxConsecutiveLosses": max_loss_streak,
    }


def original_reference() -> dict[str, Any]:
    with (WEEK_ONE / "trade_review.csv").open(encoding="utf-8-sig", newline="") as handle:
        week_one_rows = [
            {"pnlR": float(row["pnl_r"])}
            for row in csv.DictReader(handle)
        ]

    week_two_orders = {
        row["orderId"]: row
        for row in read_jsonl(WEEK_TWO / "manual_orders.jsonl")
    }
    week_two_events = read_jsonl(WEEK_TWO / "execution_ledger.jsonl")
    week_two_rows: list[dict[str, Any]] = []
    for event in week_two_events:
        if event.get("event") not in {"POSITION_CLOSED", "ORDER_FILLED_AND_CLOSED"}:
            continue
        order = week_two_orders[event["orderId"]]
        entry = float(order["entry"])
        stop = float(order["stopLoss"])
        target = float(order["takeProfit"])
        risk = entry - stop if order["direction"] == "long" else stop - entry
        reward = target - entry if order["direction"] == "long" else entry - target
        week_two_rows.append({
            "pnlR": reward / risk if event["result"] == "TP" else -1.0,
        })
    return {
        "weeks": {
            "2025-01-06~10": statistics(week_one_rows),
            "2025-01-13~17": statistics(week_two_rows),
        },
        "combined": statistics(week_one_rows + week_two_rows),
    }


def holding_text(minutes: int) -> str:
    days, remainder = divmod(minutes, 1440)
    hours, mins = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    return " ".join(parts)


def write_clean_review(
    trade_rows: list[dict[str, Any]],
    orders: dict[str, dict[str, Any]],
    combined: dict[str, Any],
    by_week: dict[str, dict[str, Any]],
    original: dict[str, Any],
) -> None:
    cards: list[str] = []
    markdown = [
        "# Mentor two-week corrected replay",
        "",
        "> 이 결과는 과거 두 주를 본 뒤 교정 규칙을 적용한 재현성 감사입니다. 신규 blind 성적이 아닙니다.",
        "",
        f"- 전체: **{combined['trades']}건, {combined['wins']}승/{combined['losses']}패, {combined['netR']:+.2f}R**",
        f"- 승률 **{combined['winRate']:.2%}**, PF **{combined['profitFactor']:.2f}**, 기대값 **{combined['expectancyR']:+.2f}R**",
        f"- 최대 낙폭 **{combined['maxDrawdownR']:.2f}R**, 최대 연속 손실 **{combined['maxConsecutiveLosses']}회**",
        f"- 기존 두 주: **{original['combined']['netR']:+.2f}R**, 승률 **{original['combined']['winRate']:.2%}**",
        f"- 교정 변화: **{combined['netR'] - original['combined']['netR']:+.2f}R**, 승률 **{combined['winRate'] - original['combined']['winRate']:+.2%}p**",
        "",
    ]
    for row in trade_rows:
        order = orders[row["orderId"]]
        chart = f"final_charts/{row['orderId']}_{order['direction']}_{row['result']}.png"
        result_class = "win" if row["result"] == "TP" else "loss"
        cards.append(
            f"""
            <article class="trade">
              <header><strong>{html.escape(row['orderId'])} · {order['direction'].upper()}</strong>
              <span class="{result_class}">{row['result']} {row['pnlR']:+.2f}R</span></header>
              <p>{html.escape(str(order['executionModel']))} · {html.escape(str(order['scope']))} · 보유 {holding_text(int(row['holdingMinutes']))}</p>
              <dl>
                <dt>시나리오</dt><dd>{html.escape(str(order['map']))}</dd>
                <dt>진입 근거</dt><dd>{html.escape(str(order['reason']))}</dd>
                <dt>목적지</dt><dd>{html.escape(str(order['objective']))}</dd>
                <dt>가격</dt><dd>Entry {float(order['entry']):.2f} · SL {float(order['stopLoss']):.2f} · TP {float(order['takeProfit']):.2f}</dd>
              </dl>
              <a href="{chart}" target="_blank"><img loading="lazy" src="{chart}" alt="{html.escape(row['orderId'])}"></a>
            </article>
            """
        )
        markdown.extend([
            f"## {row['orderId']} · {order['direction'].upper()} · {row['result']} {row['pnlR']:+.2f}R",
            "",
            f"- 실행: `{order['executionModel']}`",
            f"- 보유: `{holding_text(int(row['holdingMinutes']))}`",
            f"- 시나리오: {order['map']}",
            f"- 목적지: {order['objective']}",
            f"- 가격: Entry `{float(order['entry']):.2f}` · SL `{float(order['stopLoss']):.2f}` · TP `{float(order['takeProfit']):.2f}`",
            f"- [차트 열기]({chart})",
            "",
            f"![{row['orderId']}]({chart})",
            "",
        ])

    week_blocks = "".join(
        f"<div class='metric'><small>{html.escape(week)}</small><strong>{stats['netR']:+.2f}R</strong><span>{stats['wins']}W/{stats['losses']}L · {stats['winRate']:.1%}</span></div>"
        for week, stats in by_week.items()
    )
    document = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mentor two-week corrected replay</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#080c12;color:#e2e8f0;font:14px Arial,sans-serif}}
.shell{{max-width:1500px;margin:auto;padding:20px}} h1{{margin:0 0 8px;font-size:24px}} .notice{{color:#fbbf24}}
.summary{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;margin:18px 0}}
.metric{{background:#0b1119;border:1px solid #263241;padding:12px;display:flex;flex-direction:column;gap:5px}}
.metric small,.metric span,p{{color:#94a3b8}} .metric strong{{font-size:18px}} .trade{{border-top:1px solid #263241;padding:24px 0}}
header{{display:flex;justify-content:space-between;font-size:18px}} .win{{color:#34d399}} .loss{{color:#fb7185}}
dl{{display:grid;grid-template-columns:90px 1fr;gap:7px 12px}} dt{{color:#64748b}} dd{{margin:0}}
img{{display:block;width:100%;border:1px solid #263241;margin-top:12px}}
@media(max-width:720px){{.shell{{padding:12px}} .summary{{grid-template-columns:repeat(2,1fr)}} dl{{grid-template-columns:70px 1fr;font-size:12px}}}}
</style></head><body><main class="shell">
<h1>Mentor two-week corrected replay</h1>
<p class="notice">과거 두 주를 본 뒤 교정 규칙을 적용한 재현성 감사입니다. 신규 blind 성적이 아닙니다.</p>
<p>기존 {original['combined']['trades']}건은 {original['combined']['netR']:+.2f}R, 승률 {original['combined']['winRate']:.1%}였습니다.
교정 후 순 R 변화는 {combined['netR'] - original['combined']['netR']:+.2f}R, 승률 변화는 {combined['winRate'] - original['combined']['winRate']:+.1%}p입니다.</p>
<section class="summary">
{week_blocks}
<div class="metric"><small>전체 순 R</small><strong>{combined['netR']:+.2f}R</strong><span>{combined['trades']} trades</span></div>
<div class="metric"><small>승률</small><strong>{combined['winRate']:.1%}</strong><span>{combined['wins']}W/{combined['losses']}L</span></div>
<div class="metric"><small>Profit Factor</small><strong>{combined['profitFactor']:.2f}</strong><span>기대값 {combined['expectancyR']:+.2f}R</span></div>
<div class="metric"><small>최대 낙폭</small><strong>{combined['maxDrawdownR']:.2f}R</strong><span>연속 손실 {combined['maxConsecutiveLosses']}회</span></div>
</section>
{''.join(cards)}
</main></body></html>"""
    (OUTPUT / "TRADE_REVIEW.md").write_text("\n".join(markdown), encoding="utf-8")
    (OUTPUT / "TRADE_REVIEW.html").write_text(document, encoding="utf-8")


def main() -> int:
    if OUTPUT.exists():
        resolved = OUTPUT.resolve()
        if resolved.parent != (ROOT / "output").resolve():
            raise RuntimeError(f"Refusing to replace unexpected path: {resolved}")
        shutil.rmtree(resolved)
    OUTPUT.mkdir(parents=True)

    with np.load(DATASET, allow_pickle=False) as payload:
        rates = payload["rates"]
    orders, fills, audit_rows = build_orders(rates)

    events: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    for order in orders:
        order_id = order["orderId"]
        filled_at = fills[order_id]
        closed_at, result = simulate_exit(
            rates,
            order["direction"],
            filled_at,
            float(order["stopLoss"]),
            float(order["takeProfit"]),
        )
        entry = float(order["entry"])
        stop = float(order["stopLoss"])
        target = float(order["takeProfit"])
        risk = entry - stop if order["direction"] == "long" else stop - entry
        reward = target - entry if order["direction"] == "long" else entry - target
        pnl_r = reward / risk if result == "TP" else -1.0
        holding_minutes = (parse_time(closed_at) - parse_time(filled_at)) // 60
        events.extend([
            {"orderId": order_id, "event": "ORDER_FROZEN", "at": order["decisionAt"]},
            {"orderId": order_id, "event": "ORDER_FILLED", "at": filled_at},
            {
                "orderId": order_id,
                "event": "POSITION_CLOSED",
                "at": closed_at,
                "result": result,
                "ambiguous": False,
                "bestCase": result,
            },
        ])
        trade_rows.append({
            "orderId": order_id,
            "week": "2025-01-06~10" if order_id.startswith("W1-") else "2025-01-13~17",
            "decisionAt": order["decisionAt"],
            "filledAt": filled_at,
            "closedAt": closed_at,
            "direction": order["direction"],
            "executionModel": order["executionModel"],
            "entry": entry,
            "stopLoss": stop,
            "takeProfit": target,
            "result": result,
            "pnlR": pnl_r,
            "holdingMinutes": holding_minutes,
        })

    write_jsonl(OUTPUT / "manual_orders.jsonl", orders)
    write_jsonl(OUTPUT / "execution_ledger.jsonl", events)
    maps = read_jsonl(WEEK_ONE / "hourly_map_ledger.jsonl") + read_jsonl(WEEK_TWO / "hourly_map_ledger.jsonl")
    maps.sort(key=lambda row: parse_time(row["asOf"]))
    write_jsonl(OUTPUT / "hourly_map_ledger.jsonl", maps)

    with (OUTPUT / "trades.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trade_rows[0]))
        writer.writeheader()
        writer.writerows(trade_rows)
    with (OUTPUT / "order_audit.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)

    combined = statistics(trade_rows)
    by_week = {
        week: statistics([row for row in trade_rows if row["week"] == week])
        for week in ("2025-01-06~10", "2025-01-13~17")
    }
    original = original_reference()
    manifest = {
        "schema": "mentor-two-week-corrected-replay-v1",
        "dataset": str(DATASET.relative_to(ROOT)).replace("\\", "/"),
        "periods": list(by_week),
        "method": "Post-review corrected-policy reproducibility audit",
        "notBlind": True,
        "rules": [
            "Scenario invalidation SL",
            "Decision-time spread outside the scenario extreme",
            "Delivery FVG replacement/add-on",
            "Frozen objective",
            "Conservative same-bar stop priority",
        ],
        "summary": combined,
        "weeks": by_week,
        "originalReference": original,
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    os.environ["MENTOR_REPLAY_OUTPUT"] = str(OUTPUT)
    import render_mentor_manual_trade_review as renderer

    renderer.main()
    orders_by_id = {row["orderId"]: row for row in orders}
    write_clean_review(trade_rows, orders_by_id, combined, by_week, original)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
