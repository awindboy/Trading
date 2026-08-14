"""Export a frozen V6 scenario run into the interactive replay workspace."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge import mt5_bridge


TF_SECONDS = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800, "H1": 3600}


def timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def source_origin(source_id: str) -> int:
    return int(source_id.split(":")[-2])


def fvg_origin(fvg_id: str) -> int:
    return int(fvg_id.rsplit(":", 1)[1])


def read_trades(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def box(
    order_id: str,
    suffix: str,
    kind: str,
    timeframe: str,
    label: str,
    color: str,
    created_at: int,
    left: int,
    right: int,
    bottom: float,
    top: float,
) -> dict[str, Any]:
    return {
        "id": f"drawing-{order_id}-{suffix}",
        "kind": kind,
        "timeframe": timeframe,
        "label": label,
        "color": color,
        "createdAt": created_at,
        "anchors": [
            {"time": left, "price": bottom},
            {"time": right, "price": top},
        ],
        "evidenceStatus": "validated",
    }


def line(
    order_id: str,
    suffix: str,
    kind: str,
    timeframe: str,
    label: str,
    color: str,
    created_at: int,
    left: int,
    right: int,
    level: float,
) -> dict[str, Any]:
    return {
        "id": f"drawing-{order_id}-{suffix}",
        "kind": kind,
        "timeframe": timeframe,
        "label": label,
        "color": color,
        "createdAt": created_at,
        "anchors": [
            {"time": left, "price": level},
            {"time": right, "price": level},
        ],
        "evidenceStatus": "validated",
    }


def build_session(
    run_dir: Path,
    session_id: str,
    name: str,
) -> dict[str, Any]:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    trades = read_trades(run_dir / "trades.csv")
    week_start = timestamp(summary["period"]["from"])
    trade_to = timestamp(summary["period"]["to"])
    observed_to = max(
        [trade_to]
        + [
            timestamp(trade["closedAt"])
            for trade in trades
            if trade.get("closedAt")
        ]
    )
    now = datetime.now(timezone.utc).isoformat()
    drawings: list[dict[str, Any]] = []
    scenarios: list[dict[str, Any]] = []
    orders: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = [
        {
            "id": f"event-{session_id}-start",
            "time": week_start,
            "type": "session",
            "title": "동결 규칙 블라인드 재생",
            "detail": "V6 런타임은 역설계 casebook의 날짜와 가격을 읽지 않았습니다.",
        }
    ]
    for trade in trades:
        order_id = trade["tradeId"]
        direction = trade["direction"]
        color = "#fb7185" if direction == "short" else "#2dd4bf"
        decision_at = timestamp(trade["decisionAt"])
        filled_at = timestamp(trade["filledAt"])
        closed_at = (
            timestamp(trade["closedAt"])
            if trade.get("closedAt")
            else observed_to
        )
        parent_tf = trade["parentSourceId"].split(":", 1)[0]
        source_tf = trade["sourceTf"]
        root_tf = trade["mapRootTimeframe"]
        root_id = trade["mapRootSourceId"]
        parent_id = trade["parentSourceId"]
        source_id = trade["sourceId"]
        root_bottom = float(trade["mapRootBottom"])
        root_top = float(trade["mapRootTop"])
        parent_bottom = float(trade["parentBottom"])
        parent_top = float(trade["parentTop"])
        source_bottom = float(trade["sourceBottom"])
        source_top = float(trade["sourceTop"])
        fvg_bottom = float(trade["fvgBottom"])
        fvg_top = float(trade["fvgTop"])
        objective = float(trade["objective"])
        sweep_at = timestamp(trade["sweepAt"])
        shift_at = timestamp(trade["shiftAt"])
        scenario_id = f"scenario-{order_id}"
        drawings.append(
            box(
                order_id,
                "root",
                "ob",
                root_tf,
                "ROOT OB",
                color,
                decision_at,
                source_origin(root_id),
                closed_at,
                root_bottom,
                root_top,
            )
        )
        drawings.append(
            box(
                order_id,
                "parent",
                "ob",
                parent_tf,
                "M15 SOURCE OB",
                color,
                decision_at,
                source_origin(parent_id),
                closed_at,
                parent_bottom,
                parent_top,
            )
        )
        if source_id != parent_id:
            drawings.append(
                box(
                    order_id,
                    "source",
                    "ob",
                    source_tf,
                    "REFINED OB",
                    color,
                    decision_at,
                    source_origin(source_id),
                    closed_at,
                    source_bottom,
                    source_top,
                )
            )
        drawings.append(
            box(
                order_id,
                "entry",
                "fvg",
                "M1",
                "ENTRY FVG",
                "#fbbf24",
                decision_at,
                fvg_origin(trade["fvgId"]),
                filled_at,
                fvg_bottom,
                fvg_top,
            )
        )
        drawings.append(
            line(
                order_id,
                "objective",
                "liquidity",
                root_tf,
                "OBJECTIVE LIQUIDITY",
                "#22d3ee",
                decision_at,
                decision_at - 3 * TF_SECONDS[root_tf],
                closed_at,
                objective,
            )
        )
        drawings.append(
            {
                "id": f"drawing-{order_id}-sweep",
                "kind": "sweep",
                "timeframe": "M1",
                "direction": direction,
                "label": "BS" if direction == "short" else "SS",
                "color": color,
                "createdAt": decision_at,
                "anchors": [
                    {
                        "time": sweep_at,
                        "price": float(trade["sweepExtreme"]),
                    }
                ],
                "evidenceStatus": "validated",
            }
        )
        drawings.append(
            line(
                order_id,
                "choch",
                "choch",
                "M1",
                "CHoCH",
                color,
                decision_at,
                shift_at - 3 * TF_SECONDS["M1"],
                shift_at,
                float(trade["shiftReference"]),
            )
        )
        scope = trade["scope"]
        model = trade["entryModel"]
        rationale = (
            f"{root_tf} 지도 OB -> {parent_tf} source OB"
            f"{' -> ' + source_tf + ' refinement' if source_id != parent_id else ''}"
            f" -> M1 liquidity sweep -> {trade['shiftReferenceKind']} CHoCH"
            f" -> fresh FVG retest. TP는 {trade['objectiveId']}에 동결."
        )
        scenarios.append(
            {
                "id": scenario_id,
                "createdAt": decision_at,
                "title": f"{scope} · {model}",
                "scope": scope,
                "direction": direction,
                "mapTimeframe": root_tf,
                "sourceTimeframe": source_tf,
                "objective": f"{trade['objectiveId']} @ {objective:.2f}",
                "invalidation": (
                    f"source/refinement distal 및 protected correction 바깥 "
                    f"{float(trade['stop']):.2f}"
                ),
                "waitingFor": "M1 entry FVG의 결정 이후 첫 retest",
                "thesis": rationale,
            }
        )
        orders.append(
            {
                "id": order_id,
                "createdAt": decision_at,
                "sourceEvidenceValid": True,
                "entryEvidenceValid": True,
                "stopEvidenceValid": True,
                "semanticEvidenceValid": True,
                "performanceEligible": True,
                "direction": direction,
                "executionModel": (
                    "delivery-fvg-addon"
                    if model == "DELIVERY_FVG_ADDON"
                    else "refined-ob-retest"
                ),
                "orderType": "limit",
                "entry": float(trade["entry"]),
                "stop": float(trade["stop"]),
                "objectivePrice": objective,
                "targetBuffer": 0.0,
                "target": objective,
                "rationale": rationale,
                "scenarioId": scenario_id,
                "scenarioScope": scope,
            }
        )
        events.extend(
            [
                {
                    "id": f"event-{order_id}-decision",
                    "time": decision_at,
                    "type": "scenario",
                    "title": f"{order_id} 시나리오 동결",
                    "detail": rationale,
                },
                {
                    "id": f"event-{order_id}-fill",
                    "time": filled_at,
                    "type": "fill",
                    "title": f"{order_id} 체결",
                    "detail": f"{float(trade['entry']):.2f}",
                },
                {
                    "id": f"event-{order_id}-close",
                    "time": closed_at,
                    "type": "win" if trade["result"] == "TP" else "loss",
                    "title": f"{order_id} {trade['result']}",
                    "detail": f"{float(trade['earnedR']):.2f}R",
                },
            ]
        )
    return {
        "id": session_id,
        "name": name,
        "symbol": "GOLD",
        "dataset": Path(
            summary["datasetMetadata"].get(
                "path",
                "GOLD_M1_2023-12-01_2025-12-31.npz",
            )
        ).name,
        "weekStart": week_start,
        "weekEnd": observed_to,
        "cursorTime": week_start,
        "maxSeenTime": observed_to,
        "timeframe": "H1",
        "speed": 60,
        "createdAt": now,
        "updatedAt": now,
        "drawings": drawings,
        "scenarios": scenarios,
        "orders": orders,
        "events": sorted(events, key=lambda item: (item["time"], item["id"])),
        "importAudit": {
            "sourceRun": str(run_dir),
            "runtimeReadsCasebook": summary["casebookImported"],
            "selectorSummary": {
                "trades": summary["trades"],
                "wins": summary["wins"],
                "losses": summary["losses"],
                "totalR": summary["totalR"],
                "profitFactor": summary["profitFactor"],
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    session = build_session(run_dir, args.session_id, args.name)
    exported = run_dir / "interactive_replay_session.json"
    exported.write_text(
        json.dumps(session, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    saved = mt5_bridge.save_replay_session(session)
    print(
        json.dumps(
            {
                "ok": saved["ok"],
                "sessionId": session["id"],
                "orders": len(session["orders"]),
                "drawings": len(session["drawings"]),
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
