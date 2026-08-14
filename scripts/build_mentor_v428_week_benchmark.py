from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = ROOT / "output" / "mentor_ai_replay_v4_benchmarks"
DAY_SOURCE = BENCHMARK_ROOT / "sep03_2025_complete_v428"
WEEK_SOURCE = BENCHMARK_ROOT / "sep01_05_2025_current"
OUTPUT = BENCHMARK_ROOT / "sep01_05_2025_complete_v428"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def trade_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["trade_id"]: row for row in csv.DictReader(handle)}


def main() -> int:
    day = read_json(DAY_SOURCE / "truth.json")
    week = read_json(WEEK_SOURCE / "truth.json")
    day_by_id = {
        item["tradeId"]: item for item in day["executableBenchmarks"]
    }
    week_by_id = {
        item["tradeId"]: item for item in week["executableBenchmarks"]
    }
    ordered_ids = [
        "M50-001-CORRECTED",
        "SEP03-002-AUDITED",
    ]
    combined = {**week_by_id, **day_by_id}
    missing = [trade_id for trade_id in ordered_ids if trade_id not in combined]
    if missing:
        raise ValueError(f"audited source trades are missing: {missing}")
    benchmarks = [combined[trade_id] for trade_id in ordered_ids]
    if len({item["tradeId"] for item in benchmarks}) != len(benchmarks):
        raise ValueError("duplicate benchmark trade IDs")

    payload = {
        "schemaVersion": "4.28.0",
        "authority": "AGENTS.md",
        # This file combines independently audited cases. It is not evidence
        # that every valid scenario in the whole week was reviewed in order.
        "coverage": "COMPOSITE_AUDITED_CASES_NOT_EXHAUSTIVE",
        "period": {
            "startUtc": "2025-09-01T00:00:00Z",
            "endUtc": "2025-09-06T00:00:00Z",
        },
        "executableBenchmarks": benchmarks,
        "excludedLegacyTrades": [
            *week.get("excludedLegacyTrades", []),
            {
                "sourceTradeId": "SCW003-CORRECTED",
                "reason": (
                    "The isolated short pending is canceled at the 2025-09-04 "
                    "19:00 H1 body break, when the opposing long owner is confirmed. "
                    "It cannot remain pending until its legacy 19:29 fill under AGENTS.md."
                ),
            },
        ],
        "sourceBenchmarks": [
            str(DAY_SOURCE.relative_to(ROOT)).replace("\\", "/"),
            str(WEEK_SOURCE.relative_to(ROOT)).replace("\\", "/"),
        ],
    }

    rows = {**trade_rows(WEEK_SOURCE / "trades.csv"), **trade_rows(DAY_SOURCE / "trades.csv")}
    missing_rows = [trade_id for trade_id in ordered_ids if trade_id not in rows]
    if missing_rows:
        raise ValueError(f"CSV source trades are missing: {missing_rows}")
    for benchmark in benchmarks:
        row = rows[benchmark["tradeId"]]
        if row["root_ob_bar_id"] != benchmark["map"]["root"]["barId"]:
            raise ValueError(f"root mismatch: {benchmark['tradeId']}")
        if row["objective_bar_id"] != benchmark["map"]["objective"]["barId"]:
            raise ValueError(f"objective mismatch: {benchmark['tradeId']}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT / "truth.json", payload)
    fieldnames = list(rows[ordered_ids[0]].keys())
    with (OUTPUT / "trades.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows[trade_id] for trade_id in ordered_ids)
    (OUTPUT / "README.md").write_text(
        "# 2025-09-01~05 complete V4.28 benchmark\n\n"
        "- Authority: frozen `AGENTS.md`\n"
        "- Coverage: composite audited cases; not an exhaustive sequential week audit\n"
        "- Executable trades: 2\n"
        "- Contract result: 1 TP, 1 SL, `+1.997361R`\n"
        "- Sep 3 uses the independently audited complete-day benchmark.\n"
        "- SCW003 is excluded because the sequential 19:00 H1 owner break cancels its short pending.\n"
        "- SCW002 and SCW004 remain excluded for the documented contract violations.\n",
        encoding="utf-8",
    )
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
