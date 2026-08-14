from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "output" / "mentor_50trade_scope_locked_v1" / "working_trades.csv"
EVENTS = ROOT / "output" / "mentor_sep2025_ea_parity" / "mt5_events_v2.csv"
OUTPUT = ROOT / "output" / "mentor_sep2025_ea_parity" / "PARITY_SUMMARY.json"


def load_reference() -> dict[str, dict[str, str]]:
    with REFERENCE.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            row["trade_id"]: row
            for row in csv.DictReader(handle)
            if row["filled_at"].startswith("2025-09")
        }


def load_events() -> list[dict[str, str]]:
    with EVENTS.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def extract_int(text: str, key: str) -> int | None:
    match = re.search(rf"\b{re.escape(key)}=(-?\d+)\b", text)
    return int(match.group(1)) if match else None


def extract_word(text: str, key: str) -> str | None:
    match = re.search(rf"\b{re.escape(key)}=([^ ]+)", text)
    return match.group(1) if match else None


def main() -> int:
    references = load_reference()
    events = load_events()
    grouped: dict[str, list[dict[str, str]]] = {}
    for event in events:
        grouped.setdefault(event["reference_id"], []).append(event)

    rows: list[dict[str, object]] = []
    for reference_id, reference in references.items():
        actual = grouped.get(reference_id, [])
        sent = [item for item in actual if item["event"] == "ORDER_SENT"]
        fills = [item for item in actual if item["event"] == "FILLED"]
        closes = [item for item in actual if item["event"] == "CLOSED"]
        rejected = [
            item
            for item in actual
            if item["event"]
            in {"EVIDENCE_REJECTED", "ORDER_REJECTED", "ORDER_EXPIRED"}
        ]
        close_result = extract_word(closes[-1]["detail"], "result") if closes else None
        rows.append(
            {
                "referenceId": reference_id,
                "sent": len(sent) == 1,
                "filled": len(fills) == 1,
                "closed": len(closes) == 1,
                "resultExpected": reference["result"],
                "resultActual": close_result,
                "resultMatch": close_result == reference["result"],
                "fillDeltaSeconds": (
                    extract_int(fills[-1]["detail"], "delta_seconds") if fills else None
                ),
                "closeDeltaSeconds": (
                    extract_int(closes[-1]["detail"], "delta_seconds") if closes else None
                ),
                "rejections": [item["event"] for item in rejected],
            }
        )

    fill_deltas = [
        abs(int(row["fillDeltaSeconds"]))
        for row in rows
        if row["fillDeltaSeconds"] is not None
    ]
    close_deltas = [
        abs(int(row["closeDeltaSeconds"]))
        for row in rows
        if row["closeDeltaSeconds"] is not None
    ]
    summary = {
        "referenceMonth": "2025-09",
        "referenceCount": len(references),
        "orderSentCount": sum(bool(row["sent"]) for row in rows),
        "fillCount": sum(bool(row["filled"]) for row in rows),
        "closeCount": sum(bool(row["closed"]) for row in rows),
        "resultMatchCount": sum(bool(row["resultMatch"]) for row in rows),
        "rejectionCount": sum(len(row["rejections"]) for row in rows),
        "maxAbsoluteFillDeltaSeconds": max(fill_deltas, default=None),
        "maxAbsoluteCloseDeltaSeconds": max(close_deltas, default=None),
        "executionParityPassed": all(
            row["sent"]
            and row["filled"]
            and row["closed"]
            and row["resultMatch"]
            and not row["rejections"]
            for row in rows
        ),
        "signalGenerationParityPassed": False,
        "signalGenerationBoundary": (
            "Reference decisions are still scheduled by the calibration EA. "
            "The autonomous state machine must emit them without fixture access."
        ),
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, ensure_ascii=False, indent=2))
    return 0 if summary["executionParityPassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
