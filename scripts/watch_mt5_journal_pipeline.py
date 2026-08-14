from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any


BRIDGE_URL = "http://127.0.0.1:8765"


def fetch_json(path: str) -> dict[str, Any]:
    url = f"{BRIDGE_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc), "url": url}


def summarize(ea: dict[str, Any]) -> str:
    return (
        f"state={ea.get('attachmentState') or '-'} "
        f"source={ea.get('eventSource') or '-'} "
        f"version={ea.get('lastStatusEaVersion') or '-'} "
        f"csv={bool(ea.get('csvFileExists'))} "
        f"tradeEvents={ea.get('tradeEventCount') or 0} "
        f"trades={ea.get('tradeCount') or 0} "
        f"chart={ea.get('lastStatusChartSymbol') or '-'} "
        f"positions={ea.get('lastStatusPositionsTotal') if ea.get('lastStatusPositionsTotal') is not None else '-'}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch MT5 EA journal bridge state until requested conditions are met.")
    parser.add_argument("--timeout", type=int, default=300, help="Maximum seconds to wait.")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds.")
    parser.add_argument("--version", default="1.10", help="Expected EA version.")
    parser.add_argument("--wait-version", action="store_true", help="Wait until the expected EA version appears in heartbeat.")
    parser.add_argument("--wait-csv", action="store_true", help="Wait until events.csv exists.")
    parser.add_argument("--wait-trade", action="store_true", help="Wait until at least one EA trade event appears.")
    parser.add_argument("--wait-connected", action="store_true", help="Wait until the EA attachment state is connected.")
    args = parser.parse_args()

    targets = {
        "version": args.wait_version,
        "csv": args.wait_csv,
        "trade": args.wait_trade,
        "connected": args.wait_connected,
    }
    if not any(targets.values()):
        targets = {"version": True, "csv": True, "trade": True}

    start = time.monotonic()
    last_summary = ""
    while True:
        payload = fetch_json("/ea-events?days=14")
        if not payload.get("ok"):
            print(f"WARN: bridge read failed - {payload.get('error') or payload}")
            current = {}
        else:
            current = payload.get("ea") if isinstance(payload.get("ea"), dict) else {}

        summary = summarize(current)
        if summary != last_summary:
            elapsed = int(time.monotonic() - start)
            print(f"{elapsed:>4}s {summary}")
            last_summary = summary

        checks = {
            "version": str(current.get("lastStatusEaVersion") or "") == args.version,
            "csv": bool(current.get("csvFileExists")),
            "trade": int(current.get("tradeEventCount") or 0) > 0,
            "connected": str(current.get("attachmentState") or "") == "connected",
        }
        waiting_for = [name for name, enabled in targets.items() if enabled and not checks[name]]
        if not waiting_for:
            print("MT5_JOURNAL_WATCH_OK", json.dumps({"ea": current}, ensure_ascii=False))
            return 0

        if time.monotonic() - start >= args.timeout:
            print(
                "MT5_JOURNAL_WATCH_TIMEOUT",
                json.dumps({"waitingFor": waiting_for, "ea": current}, ensure_ascii=False),
            )
            return 1

        time.sleep(max(0.5, args.interval))


if __name__ == "__main__":
    sys.exit(main())
