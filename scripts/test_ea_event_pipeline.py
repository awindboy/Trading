from __future__ import annotations

import base64
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import bridge.mt5_bridge as bridge


PNG_1X1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lrQa2wAAAABJRU5ErkJggg=="
ACCOUNT = {"login": 1, "server": "TEST", "currency": "USD", "balance": 1000}


def write_sample_screenshot(root: Path) -> None:
    screenshot_dir = root / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    (screenshot_dir / "sample.png").write_bytes(base64.b64decode(PNG_1X1))


def json_event(**overrides: Any) -> dict[str, Any]:
    event = {
        "schema": "trade-journal-ea-v1",
        "eaVersion": "1.10",
        "features": "jsonl,csv,screenshot,heartbeat,sl_tp_updates",
        "event": "open",
        "eventId": "10:open:1",
        "time": "2026.07.04 20:01:00",
        "accountLogin": 1,
        "server": "TEST",
        "ticket": 100,
        "positionId": 10,
        "symbol": "GOLD",
        "direction": "long",
        "volume": 0.1,
        "entryPrice": 2400.0,
        "stopLoss": 2390.0,
        "takeProfit": 2420.0,
        "floatingProfit": 0.0,
        "swap": 0.0,
        "openTime": "2026.07.04 20:01:00",
        "comment": "",
        "screenshot": "screenshots\\sample.png",
    }
    event.update(overrides)
    return event


def write_jsonl(root: Path) -> None:
    events = [
        {
            "schema": "trade-journal-ea-v1",
            "eaVersion": "1.10",
            "features": "jsonl,csv,screenshot,heartbeat,sl_tp_updates",
            "event": "ea_start",
            "eventId": "status:ea_start:1",
            "time": "2026.07.04 20:00:00",
            "accountLogin": 1,
            "server": "TEST",
            "chartSymbol": "GOLD",
            "positionsTotal": 0,
        },
        json_event(),
        json_event(event="update", eventId="10:update:2", time="2026.07.04 20:02:00", stopLoss=2395.0, takeProfit=2430.0, floatingProfit=3.0, screenshot=""),
        json_event(
            event="close",
            eventId="10:close:3",
            time="2026.07.04 20:03:00",
            stopLoss=2395.0,
            takeProfit=2430.0,
            floatingProfit=0.0,
            closeDeal=101,
            closeTime="2026.07.04 20:03:00",
            closePrice=2425.0,
            closeVolume=0.1,
            profit=2.5,
            commission=-0.1,
            closeSwap=0.0,
            fee=0.0,
        ),
    ]
    (root / "events.jsonl").write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")


def write_csv(root: Path) -> None:
    lines = [
        "schema,event,eventId,time,accountLogin,server,chartSymbol,positionsTotal,ticket,positionId,symbol,direction,volume,entryPrice,stopLoss,takeProfit,floatingProfit,swap,openTime,comment,screenshot,closeDeal,closeTime,closePrice,closeVolume,profit,commission,closeSwap,fee",
        "trade-journal-ea-v1,ea_start,status:1,2026.07.04 20:00:00,1,TEST,GOLD,0,0,0,,,0,0,0,0,0,0,,,,0,,0,0,0,0,0,0",
        "trade-journal-ea-v1,open,10:open:1,2026.07.04 20:01:00,1,TEST,,0,100,10,GOLD,long,0.1,2400.0,2390.0,2420.0,0,0,2026.07.04 20:01:00,,screenshots\\sample.png,0,,0,0,0,0,0,0",
        "trade-journal-ea-v1,update,10:update:2,2026.07.04 20:02:00,1,TEST,,0,100,10,GOLD,long,0.1,2400.0,2395.0,2430.0,3,0,2026.07.04 20:01:00,,,0,,0,0,0,0,0,0",
        "trade-journal-ea-v1,close,10:close:3,2026.07.04 20:03:00,1,TEST,,0,100,10,GOLD,long,0.1,2400.0,2395.0,2430.0,0,0,2026.07.04 20:01:00,,screenshots\\sample.png,101,2026.07.04 20:03:00,2425.0,0.1,2.5,-0.1,0,0",
    ]
    (root / "events.csv").write_text("\n".join(lines), encoding="utf-8")


def with_export_dir(root: Path):
    old_dir = bridge.EA_EXPORT_DIR
    bridge.EA_EXPORT_DIR = str(root)
    return old_dir


def assert_trade_shape(trade: dict[str, Any]) -> None:
    assert trade["externalId"] == "mt5:1:10", trade
    assert trade["status"] == "closed", trade
    assert trade["symbol"] == "GOLD", trade
    assert trade["stopPrice"] == 2395.0, trade
    assert trade["targetPrice"] == 2430.0, trade
    assert trade["exitPrice"] == 2425.0, trade
    assert abs(trade["brokerPnl"] - 2.4) < 1e-9, trade
    assert trade["screenshotName"] == "sample.png", trade
    assert str(trade["screenshot"]).startswith("data:image/png;base64,"), trade


def run_case(kind: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "trading_journal"
        root.mkdir()
        write_sample_screenshot(root)
        if kind == "jsonl":
            write_jsonl(root)
        elif kind == "csv":
            write_csv(root)
        else:
            raise AssertionError(f"Unknown case: {kind}")

        old_dir = with_export_dir(root)
        try:
            trades, meta = bridge.ea_events_payload(14, ACCOUNT)
        finally:
            bridge.EA_EXPORT_DIR = old_dir

    assert len(trades) == 1, trades
    assert_trade_shape(trades[0])
    assert meta["eventSource"] == kind, meta
    assert meta["tradeEventCount"] == 3, meta
    assert meta["tradeCount"] == 1, meta
    return {"source": kind, "events": meta["eventCount"], "tradeEvents": meta["tradeEventCount"]}


def main() -> None:
    results = [run_case("jsonl"), run_case("csv")]
    print("EA_EVENT_PIPELINE_TEST_OK", json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
