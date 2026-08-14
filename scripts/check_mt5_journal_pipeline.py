from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JOURNAL_FILE = ROOT / "data" / "journal.json"
BRIDGE_URL = "http://127.0.0.1:8765"


def fetch_json(path: str) -> dict[str, Any]:
    url = f"{BRIDGE_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc), "url": url}


def read_journal() -> list[dict[str, Any]]:
    if not JOURNAL_FILE.exists():
        return []
    try:
        payload = json.loads(JOURNAL_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    trades = payload.get("trades") if isinstance(payload, dict) else []
    return trades if isinstance(trades, list) else []


def status_line(ok: bool, label: str, detail: str = "") -> str:
    prefix = "OK" if ok else "WARN"
    return f"{prefix}: {label}{' - ' + detail if detail else ''}"


def main() -> int:
    health = fetch_json("/health")
    ea_response = fetch_json("/ea-events?days=14")
    snapshot = fetch_json("/snapshot?days=14")
    trades = read_journal()

    errors = 0
    warnings = 0

    def emit(ok: bool, label: str, detail: str = "", hard: bool = False) -> None:
        nonlocal errors, warnings
        print(status_line(ok, label, detail))
        if ok:
            return
        if hard:
            errors += 1
        else:
            warnings += 1

    emit(bool(health.get("ok")), "Bridge health", str(health.get("error") or health.get("journalStorage") or ""), hard=True)

    ea = ea_response.get("ea") if isinstance(ea_response, dict) else {}
    if not isinstance(ea, dict):
        ea = {}
    attachment = str(ea.get("attachmentState") or "missing")
    emit(
        attachment == "connected",
        "EA attachment",
        f"{attachment}; {ea.get('attachmentMessage') or ''}",
        hard=True,
    )
    emit(
        bool(ea.get("eventFileExists")),
        "EA JSONL event file",
        str(ea.get("eventFile") or ""),
        hard=True,
    )
    emit(
        bool(ea.get("csvFileExists")),
        "EA CSV event file",
        str(ea.get("csvFile") or "CSV will appear after reattaching the updated EA."),
    )
    emit(
        bool(ea.get("lastStatusEaVersion")),
        "EA version heartbeat",
        str(ea.get("lastStatusEaVersion") or "Missing. Reattach the updated TradeJournalExporterEA to the MT5 chart."),
    )
    emit(
        int(ea.get("tradeEventCount") or 0) > 0,
        "EA trade events",
        f"{ea.get('tradeEventCount') or 0} trade events. This stays 0 until the next MT5 position opens/updates/closes.",
    )

    positions = snapshot.get("positions") if isinstance(snapshot, dict) else []
    if not isinstance(positions, list):
        positions = []
    emit(bool(snapshot.get("ok")), "MT5 snapshot", str(snapshot.get("error") or f"{len(positions)} open positions"), hard=True)

    emit(bool(trades), "Journal storage", f"{len(trades)} trades in {JOURNAL_FILE}", hard=True)
    emit(
        all(all(field in trade for field in ("thesis", "good", "bad", "lesson")) for trade in trades),
        "User memo fields",
        "thesis/good/bad/lesson present on all journal rows",
        hard=True,
    )
    emit(
        not any(str(trade.get("thesis") or "").startswith("MT5 comment:") for trade in trades),
        "Memo fields stay manual",
        "No MT5 comment text in thesis fields",
        hard=True,
    )

    print(
        json.dumps(
            {
                "ok": errors == 0,
                "errors": errors,
                "warnings": warnings,
                "ea": {
                    "attachmentState": attachment,
                    "eventSource": ea.get("eventSource"),
                    "jsonEventCount": ea.get("jsonEventCount"),
                    "csvEventCount": ea.get("csvEventCount"),
                    "tradeEventCount": ea.get("tradeEventCount"),
                    "lastStatusChartSymbol": ea.get("lastStatusChartSymbol"),
                    "lastStatusPositionsTotal": ea.get("lastStatusPositionsTotal"),
                    "lastStatusEaVersion": ea.get("lastStatusEaVersion"),
                    "lastStatusFeatures": ea.get("lastStatusFeatures"),
                },
                "journalTrades": len(trades),
            },
            ensure_ascii=False,
        )
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
