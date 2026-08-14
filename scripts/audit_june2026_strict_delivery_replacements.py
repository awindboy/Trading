"""Re-run objective-first scenarios through the frozen Delivery-FVG contract.

The June prefilter historically stopped a scenario as soon as its objective was
reached before the final child OB.  That prevented the already implemented
pre-touch replacement detector from ever seeing those scenarios.  This audit
bypasses only that prefilter and changes no strategy rule.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from build_june2026_causal_benchmark import simulate_scenario  # noqa: E402
from build_june2026_oracle_atlas import load_joined, timestamp  # noqa: E402
from audit_june2026_objective_first_retracements import fvg_ledger  # noqa: E402
from mentor_replay_v4_core import MarketData, parse_utc, zone_touched  # noqa: E402

RUN = ROOT / "output" / "mentor_june2026_causal_benchmark"


def load_scenarios() -> dict[str, dict]:
    output: dict[str, dict] = {}
    for path in RUN.glob("formal_scenario_index_v2_pretouch.part*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")):
            output[item["semanticHash"]] = item
    return output


def objective_first_hashes() -> set[str]:
    output: set[str] = set()
    for path in RUN.glob("event_race_prefilter_v2_pretouch.part*.csv"):
        with path.open(encoding="utf-8-sig") as handle:
            for item in csv.DictReader(handle):
                if item["reason"] == "OBJECTIVE_REACHED_BEFORE_CHILD_TOUCH":
                    output.add(item["semanticHash"])
    return output


def physical_key(record: dict) -> tuple:
    replacement = record["result"]["replacement"]
    return (
        record["scenario"]["direction"],
        replacement["formedBarId"],
        replacement.get("filledAtUtc", ""),
    )


def lineage_key(record: dict) -> tuple:
    scenario = record["scenario"]
    return (
        scenario["scope"], scenario["root"]["obBarId"],
        scenario["finalChild"]["obBarId"], scenario["objective"]["barId"],
    )


def main() -> int:
    rates, _ = load_joined(
        ROOT / "output/datasets/GOLD_M1_2023-12-01_2025-12-31.npz",
        ROOT / "output/datasets/GOLD_M1_2026-01-01_2026-08-12.npz",
    )
    market = MarketData.from_rates(rates, 0.01)
    scenarios = load_scenarios()
    selected = [scenarios[key] for key in objective_first_hashes()]
    selected.sort(key=lambda item: (item["frozenAtUtc"], item["semanticHash"]))

    entry_end = timestamp("2026-07-01T00:00:00Z")
    follow_end = timestamp("2026-07-15T00:00:00Z")
    raw: list[dict] = []
    terminal_counts: Counter[str] = Counter()
    for number, scenario in enumerate(selected, 1):
        result = simulate_scenario(market, scenario, entry_end, follow_end)
        terminal_counts[result["status"]] += 1
        replacement = result.get("replacement")
        if not replacement or replacement.get("status") not in {"TP", "SL"}:
            continue
        formed_at = parse_utc(replacement["formedAtUtc"])
        formed_row = market.bar(replacement["formedBarId"], formed_at)
        # If the formation M1 bar also touched the original child, M1 OHLC
        # cannot prove that the original order remained unfilled first.
        if zone_touched(formed_row, scenario["finalChild"]):
            terminal_counts["REJECT_FORMATION_BAR_ALSO_TOUCHED_CHILD"] += 1
            continue
        raw.append({"scenario": scenario, "result": result})
        if number % 50 == 0:
            print(f"[PROGRESS] {number}/{len(selected)}", flush=True)

    families: dict[tuple, list[dict]] = {}
    for record in raw:
        key = physical_key(record)
        families.setdefault(key, []).append(record)

    unambiguous: list[tuple[dict, int]] = []
    ambiguous_families: list[dict] = []
    for key, variants in families.items():
        unique = {lineage_key(item): item for item in variants}
        if len(unique) != 1:
            ambiguous_families.append({
                "direction": key[0], "formedBarId": key[1], "filledAtUtc": key[2],
                "lineageVariantCount": len(unique),
                "lineages": [list(item) for item in sorted(unique)],
            })
            continue
        unambiguous.append((next(iter(unique.values())), len(variants)))

    records = sorted(
        unambiguous,
        key=lambda item: item[0]["result"]["replacement"].get("filledAtUtc", ""),
    )
    rows: list[dict] = []
    for number, (record, duplicate_count) in enumerate(records, 1):
        scenario = record["scenario"]
        replacement = record["result"]["replacement"]
        rows.append({
            "candidateId": f"J26-DFVG-{number:03d}",
            "direction": scenario["direction"],
            "scope": scenario["scope"],
            "frozenAtUtc": scenario["frozenAtUtc"],
            "rootObBarId": scenario["root"]["obBarId"],
            "finalChildObBarId": scenario["finalChild"]["obBarId"],
            "objectiveBarId": scenario["objective"]["barId"],
            "objectivePrice": scenario["objective"]["price"],
            "fvgFormedAtUtc": replacement["formedAtUtc"],
            "fvgBarId": replacement["formedBarId"],
            "fvgZone": f"{replacement['fvg']['low']:.2f}-{replacement['fvg']['high']:.2f}",
            "causalObBarId": replacement["causalObBarId"],
            "transferSwingBarId": replacement["transferSwingBarId"],
            "protectedSwingBarId": replacement["protectedSwingBarId"],
            "firstRetestAtUtc": replacement.get("filledAtUtc", ""),
            "entry": replacement["entry"],
            "stop": replacement["stop"],
            "target": replacement["target"],
            "outcome": replacement["status"],
            "resultR": replacement.get("resultR", ""),
            "closedAtUtc": replacement.get("closedAtUtc", ""),
            "scenarioVariantCount": duplicate_count,
            "auditStatus": "STRICT_AGENTS_DELIVERY_REPLACEMENT",
        })

    all_fvgs = fvg_ledger(market)
    tf_rank = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60}
    for row in rows:
        formed_at = parse_utc(row["fvgFormedAtUtc"])
        fvg_low, fvg_high = (float(value) for value in row["fvgZone"].split("-"))
        active_higher: list[dict] = []
        for fvg in all_fvgs:
            if (
                fvg["tf"] == "M1" or fvg["direction"] != row["direction"]
                or fvg["formedAt"] > formed_at
                or fvg["high"] < fvg_low or fvg["low"] > fvg_high
            ):
                continue
            left = int(np.searchsorted(rates["time"], fvg["formedAt"], side="left"))
            right = int(np.searchsorted(rates["time"], formed_at - 60, side="right"))
            block = rates[left:right]
            invalidated = bool(len(block)) and (
                bool(np.any(block["low"] <= fvg["low"]))
                if row["direction"] == "LONG" else
                bool(np.any(block["high"] >= fvg["high"]))
            )
            if not invalidated:
                active_higher.append(fvg)
        higher_tfs = sorted({item["tf"] for item in active_higher}, key=tf_rank.get)
        row["fvgTimeframes"] = "+".join(["M1", *higher_tfs])
        row["overlappingHigherFvgs"] = ";".join(
            f"{item['fvgId']}:{item['low']:.2f}-{item['high']:.2f}"
            for item in active_higher
        )

    output = RUN / "strict_delivery_replacement_candidates.csv"
    if rows:
        with output.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    else:
        output.write_text("", encoding="utf-8")

    outcome_counts = Counter(row["outcome"] for row in rows)
    (RUN / "strict_delivery_replacement_ambiguous_families.json").write_text(
        json.dumps(ambiguous_families, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report = [
        "# June 2026 Strict Delivery-FVG Replacement Audit",
        "",
        "The audit bypasses only the objective-before-child prefilter. All AGENTS.md replacement conditions are enforced by the existing detector and first-retest simulator.",
        "",
        f"- Objective-first scenario variants: {len(selected)}",
        f"- Physical FVG/retest families before lineage conflict audit: {len(families)}",
        f"- Ambiguous lineage/objective families rejected: {len(ambiguous_families)}",
        f"- Strict unambiguous replacement candidates: {len(rows)}",
        f"- TP: {outcome_counts['TP']}",
        f"- SL: {outcome_counts['SL']}",
        "",
        "| Candidate | Direction | Scope | FVG formed | First retest | Entry | SL | TP | Outcome | R |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        result_r = f"{float(row['resultR']):+.3f}" if row["resultR"] != "" else "-"
        report.append(
            f"| {row['candidateId']} | {row['direction']} | {row['scope']} | "
            f"{row['fvgFormedAtUtc']} | {row['firstRetestAtUtc']} | "
            f"{float(row['entry']):.2f} | {float(row['stop']):.2f} | "
            f"{float(row['target']):.2f} | {row['outcome']} | {result_r} |"
        )
    (RUN / "STRICT_DELIVERY_REPLACEMENT_AUDIT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    summary = {
        "objectiveFirstVariants": len(selected),
        "terminalVariantCounts": dict(terminal_counts),
        "strictVariantPasses": len(raw),
        "physicalFvgFamilies": len(families),
        "ambiguousFamilies": len(ambiguous_families),
        "strictPhysicalCandidates": len(rows),
        "outcomes": dict(outcome_counts),
        "totalR": sum(float(row["resultR"]) for row in rows if row["resultR"] != ""),
        "output": str(output),
    }
    (RUN / "strict_delivery_replacement_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
