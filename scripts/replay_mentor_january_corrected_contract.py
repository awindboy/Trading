from __future__ import annotations

import csv
from datetime import datetime
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output" / "mentor_january_ob_refinement_manual"
OUTPUT = ROOT / "output" / "mentor_january_ob_refinement_corrected"
POINT = 0.01


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def matching_touch(order: dict[str, Any], touches: list[dict[str, Any]]) -> dict[str, Any] | None:
    zone = order["sourceZone"]
    decision = timestamp(order["decisionAt"])
    matches = []
    for event in touches:
        poi = event["poi"]
        if poi.get("direction") != order["direction"]:
            continue
        if abs(float(poi["low"]) - float(zone["low"])) > POINT:
            continue
        if abs(float(poi["high"]) - float(zone["high"])) > POINT:
            continue
        if timestamp(event["at"]) <= decision:
            matches.append(event)
    return max(matches, key=lambda item: timestamp(item["at"])) if matches else None


def validate(order: dict[str, Any], touch: dict[str, Any] | None, legacy_ok: bool) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not legacy_ok:
        failures.append("PRIOR_BASELINE_EXCLUSION")
    if touch is None:
        failures.append("NO_MATCHED_PREDECLARED_POI_TOUCH")
        return False, failures
    lineage = order["causalLineage"]
    formed = timestamp(lineage["sourceLiquidity"]["formedAt"])
    touched = timestamp(touch["at"])
    swept = timestamp(order["sweep"]["at"])
    choch = timestamp(order["choch"]["at"])
    decision = timestamp(order["decisionAt"])
    if not formed < touched:
        failures.append("LIQUIDITY_NOT_PREEXISTING_BEFORE_POI_TOUCH")
    if not touched <= swept < choch <= decision:
        failures.append("INVALID_TOUCH_SWEEP_CHOCH_ORDER")
    entry = order["entryZone"]
    source = order["sourceZone"]
    if entry.get("ownedBy") != "REFINED_SOURCE_OB":
        failures.append("ENTRY_NOT_OWNED_BY_REFINED_SOURCE_OB")
    if any(abs(float(entry[key]) - float(source[key])) > POINT for key in ("low", "high")):
        failures.append("ENTRY_SOURCE_GEOMETRY_MISMATCH")
    path = lineage.get("refinementPath", [])
    timeframes = [lineage["parentZone"]["timeframe"]] + [item["timeframe"] for item in path] + [lineage["sourceZone"]["timeframe"]]
    if len(timeframes) != len(set(timeframes)):
        failures.append("DUPLICATE_TIMEFRAME_IN_REFINEMENT")
    return not failures, failures


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    orders = read_jsonl(SOURCE / "manual_orders.jsonl")
    events = read_jsonl(SOURCE / "execution_ledger.jsonl")
    touches = [item for item in events if item.get("event") == "MANUAL_POI_TOUCHED"]
    prior = json.loads((SOURCE / "BASELINE_TRADE_ELIGIBILITY.json").read_text(encoding="utf-8-sig"))
    prior_map = {
        item["orderId"]: bool(item.get("baselineEligible", item.get("eligible", True)))
        for item in prior["orders"]
    }

    audit: list[dict[str, Any]] = []
    eligible: set[str] = set()
    for order in orders:
        touch = matching_touch(order, touches)
        ok, failures = validate(order, touch, prior_map.get(order["orderId"], True))
        if ok:
            eligible.add(order["orderId"])
        audit.append({
            "orderId": order["orderId"],
            "eligible": ok,
            "poiTouchedAt": touch["at"] if touch else None,
            "sourceLiquidityFormedAt": order["causalLineage"]["sourceLiquidity"]["formedAt"],
            "sweepAt": order["sweep"]["at"],
            "chochAt": order["choch"]["at"],
            "failures": failures,
        })

    with (SOURCE / "trade_review.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row["order_id"] in eligible]
    with (OUTPUT / "trades.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(selected)

    pnl = [float(row["pnl_r"]) for row in selected]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in pnl:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    summary = {
        "protocol": "MENTOR_OB_REFINEMENT_PRETOUCH_LIQUIDITY_V4",
        "source": str(SOURCE),
        "scope": "Frozen January HTF maps and all 21 recorded POI-touch episodes; LTF contract re-adjudication only.",
        "ordersReviewed": len(orders),
        "eligibleOrders": len(eligible),
        "closedTrades": len(selected),
        "wins": len(wins),
        "losses": len(losses),
        "winRate": len(wins) / len(selected) if selected else 0.0,
        "netR": sum(pnl),
        "profitFactor": gross_profit / gross_loss if gross_loss else None,
        "expectancyR": sum(pnl) / len(selected) if selected else 0.0,
        "maxDrawdownR": max_dd,
        "importantBoundary": "This is not a new independent HTF map. It preserves the blind January map and revisits only its recorded OB contacts.",
    }
    (OUTPUT / "eligibility.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# January corrected-contract replay",
        "",
        f"- eligible orders: {summary['eligibleOrders']} / {summary['ordersReviewed']}",
        f"- closed trades: {summary['closedTrades']} ({summary['wins']}W/{summary['losses']}L)",
        f"- win rate: {summary['winRate']:.2%}",
        f"- net: {summary['netR']:.2f}R",
        f"- profit factor: {summary['profitFactor']:.2f}",
        f"- expectancy: {summary['expectancyR']:.2f}R",
        f"- max drawdown: {summary['maxDrawdownR']:.2f}R",
        "",
        "This replay reuses the frozen January HTF map and all recorded POI contacts. It does not import automated candidate locations or search new HTF opportunities retrospectively.",
    ]
    (OUTPUT / "REVIEW.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
