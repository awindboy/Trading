"""Audit what price retraced to when an objective preceded child-OB touch.

This is a retrospective geometry audit.  It does not authorize an entry.  A
reported FVG must exist before its touch, receive its first touch during the
episode, and remain structurally unbroken until the frozen objective is hit.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from build_june2026_oracle_atlas import load_joined, timestamp  # noqa: E402
from mentor_replay_v4_core import MarketData, utc_text  # noqa: E402


RUN = ROOT / "output" / "mentor_june2026_causal_benchmark"
TF_ORDER = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60}


def load_scenarios() -> dict[str, dict]:
    output: dict[str, dict] = {}
    for path in RUN.glob("formal_scenario_index_v2_pretouch.part*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")):
            output[item["semanticHash"]] = item
    return output


def load_prefilter() -> dict[str, dict]:
    output: dict[str, dict] = {}
    for path in RUN.glob("event_race_prefilter_v2_pretouch.part*.csv"):
        with path.open(encoding="utf-8-sig") as handle:
            for item in csv.DictReader(handle):
                output[item["semanticHash"]] = item
    return output


def fvg_ledger(market: MarketData) -> list[dict]:
    start = timestamp("2026-05-01T00:00:00Z")
    end = timestamp("2026-07-15T00:00:00Z")
    output: list[dict] = []
    for timeframe in ("M1", "M5", "M15", "M30", "H1"):
        series = market.frames[timeframe]
        left = int(np.searchsorted(series.available_time, start, side="left"))
        right = int(np.searchsorted(series.available_time, end, side="right"))
        for index in range(max(2, left), right):
            first_high = float(series.high[index - 2])
            first_low = float(series.low[index - 2])
            third_low = float(series.low[index])
            third_high = float(series.high[index])
            direction = ""
            low = high = 0.0
            if third_low > first_high:
                direction, low, high = "LONG", first_high, third_low
            elif third_high < first_low:
                direction, low, high = "SHORT", third_high, first_low
            if not direction:
                continue
            output.append({
                "fvgId": f"{timeframe}:{int(series.time[index])}",
                "tf": timeframe,
                "direction": direction,
                "formedAt": int(series.available_time[index]),
                "low": low,
                "high": high,
            })
    return output


def first_touch_index(
    rates: np.ndarray, formed_at: int, episode_start: int, episode_end: int,
    low: float, high: float,
) -> int | None:
    # Search from formation, not episode start, so an already mitigated FVG
    # cannot be relabelled as fresh merely because a new scenario was frozen.
    left = int(np.searchsorted(rates["time"], formed_at, side="left"))
    right = int(np.searchsorted(rates["time"], episode_end, side="left"))
    if right <= left:
        return None
    block = rates[left:right]
    indexes = np.flatnonzero((block["high"] >= low) & (block["low"] <= high))
    return left + int(indexes[0]) if len(indexes) else None


def survives_to_objective(
    rates: np.ndarray, start_index: int, end: int, direction: str,
    distal: float,
) -> bool:
    right = int(np.searchsorted(rates["time"], end, side="left"))
    block = rates[start_index:right]
    if not len(block):
        return False
    if direction == "LONG":
        return float(np.min(block["low"])) >= distal - 0.011
    return float(np.max(block["high"])) <= distal + 0.011


def zone_touched_between(
    rates: np.ndarray, start: int, end: int, low: float, high: float,
) -> bool:
    left = int(np.searchsorted(rates["time"], start, side="left"))
    right = int(np.searchsorted(rates["time"], end, side="left"))
    block = rates[left:right]
    return bool(len(block) and np.any((block["high"] >= low) & (block["low"] <= high)))


def main() -> int:
    rates, _ = load_joined(
        ROOT / "output/datasets/GOLD_M1_2023-12-01_2025-12-31.npz",
        ROOT / "output/datasets/GOLD_M1_2026-01-01_2026-08-12.npz",
    )
    market = MarketData.from_rates(rates, 0.01)
    scenarios = load_scenarios()
    prefilter = load_prefilter()
    fvgs = fvg_ledger(market)

    by_event: dict[tuple[str, str], list[tuple[dict, dict]]] = defaultdict(list)
    for semantic_hash, audit in prefilter.items():
        if audit["reason"] != "OBJECTIVE_REACHED_BEFORE_CHILD_TOUCH":
            continue
        scenario = scenarios[semantic_hash]
        by_event[(scenario["frozenAtUtc"], scenario["direction"])].append((scenario, audit))

    with (RUN / "oracle_move_index.csv").open(encoding="utf-8-sig") as handle:
        oracle = list(csv.DictReader(handle))

    rows: list[dict] = []
    for candidate in oracle:
        variants = by_event.get((candidate["pivotTimeUtc"], candidate["direction"]), [])
        if not variants:
            continue
        # The earliest frozen objective is the first physical delivery event;
        # farther objective variants are not separate pullbacks.
        scenario, audit = min(variants, key=lambda item: item[1]["eventAtUtc"])
        start = timestamp(scenario["frozenAtUtc"])
        end = timestamp(audit["eventAtUtc"])
        direction = scenario["direction"]
        episode_left = int(np.searchsorted(rates["time"], start, side="left"))
        episode_right = int(np.searchsorted(rates["time"], end, side="left"))
        episode_block = rates[episode_left:episode_right]
        episode_low = float(np.min(episode_block["low"]))
        episode_high = float(np.max(episode_block["high"]))
        valid_fvgs: list[tuple[dict, int]] = []
        for fvg in fvgs:
            if fvg["direction"] != direction or fvg["formedAt"] >= end:
                continue
            if fvg["formedAt"] < start - 7 * 86400:
                continue
            if fvg["high"] < episode_low or fvg["low"] > episode_high:
                continue
            touch_index = first_touch_index(
                rates, fvg["formedAt"], start, end, fvg["low"], fvg["high"]
            )
            if touch_index is None or int(rates["time"][touch_index]) < start:
                continue
            distal = fvg["low"] if direction == "LONG" else fvg["high"]
            if survives_to_objective(rates, touch_index, end, direction, distal):
                valid_fvgs.append((fvg, touch_index))

        family: list[tuple[dict, int]] = []
        if valid_fvgs:
            # Last fresh, structurally defended FVG touch before delivery.
            anchor, anchor_index = max(valid_fvgs, key=lambda item: int(rates["time"][item[1]]))
            anchor_bar_high = float(rates["high"][anchor_index])
            anchor_bar_low = float(rates["low"][anchor_index])
            overlapping = [
                (fvg, index) for fvg, index in valid_fvgs
                if index <= anchor_index
                and fvg["high"] >= anchor_bar_low
                and fvg["low"] <= anchor_bar_high
            ]
            # Preserve one representative active FVG per timeframe.  A wider
            # TF may have received an earlier partial touch and still overlap
            # the lower-TF first-retest reaction; that is genuine MTF overlap.
            per_timeframe: dict[str, tuple[dict, int]] = {}
            for item in overlapping:
                timeframe = item[0]["tf"]
                previous = per_timeframe.get(timeframe)
                if previous is None or item[1] > previous[1]:
                    per_timeframe[timeframe] = item
            family = sorted(per_timeframe.values(), key=lambda item: TF_ORDER[item[0]["tf"]])
            structure = "+".join(item[0]["tf"] for item in family) + " FVG"
            reaction_time = utc_text(int(rates["time"][anchor_index]) + 60)
            reaction_price = (
                float(rates["low"][anchor_index])
                if direction == "LONG" else float(rates["high"][anchor_index])
            )
            zones = ";".join(
                f"{item[0]['tf']}:{item[0]['low']:.2f}-{item[0]['high']:.2f}"
                for item in family
            )
            classification = (
                "FVG_TOUCH_OBJECTIVE_SAME_M1_AMBIGUOUS"
                if reaction_time == audit["eventAtUtc"] else
                "FVG_FIRST_RETEST_CONTINUATION"
            )
        else:
            root = scenario["root"]
            root_touch = zone_touched_between(
                rates, start, end, float(root["low"]), float(root["high"])
            )
            structure = "ROOT OB" if root_touch else "NO_FRESH_FVG_OR_ROOT_OB_TOUCH"
            classification = "ROOT_OB_REACTION" if root_touch else "DIRECT_OR_UNCLASSIFIED_DELIVERY"
            reaction_time = ""
            reaction_price = ""
            zones = f"{root['tf']}:{float(root['low']):.2f}-{float(root['high']):.2f}" if root_touch else ""

        rows.append({
            "candidateId": candidate["candidateId"],
            "direction": direction,
            "scenarioFrozenAtUtc": scenario["frozenAtUtc"],
            "objectiveReachedAtUtc": audit["eventAtUtc"],
            "objectiveBarId": scenario["objective"]["barId"],
            "objectivePrice": scenario["objective"]["price"],
            "waitingChild": scenario["finalChild"]["obBarId"],
            "waitingChildZone": f"{float(scenario['finalChild']['low']):.2f}-{float(scenario['finalChild']['high']):.2f}",
            "reactionStructure": structure,
            "reactionAtUtc": reaction_time,
            "reactionPrice": reaction_price,
            "reactionZones": zones,
            "classification": classification,
            "scenarioVariantCount": len(variants),
        })

    output_csv = RUN / "objective_first_retracement_audit.csv"
    with output_csv.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["reactionStructure"] for row in rows)
    class_counts = Counter(row["classification"] for row in rows)
    report = [
        "# June 2026 Objective-First Retracement Audit",
        "",
        "This is a retrospective geometry audit, not an entry authorization or PnL result.",
        "A FVG is counted only when it formed before touch, received its first touch during the episode, and its distal was not crossed before the frozen objective was reached.",
        "",
        f"- Physical oracle episodes audited: {len(rows)}",
        f"- FVG first-retest continuations: {class_counts['FVG_FIRST_RETEST_CONTINUATION']}",
        f"- FVG touch/objective same-M1 ambiguous: {class_counts['FVG_TOUCH_OBJECTIVE_SAME_M1_AMBIGUOUS']}",
        f"- Root OB reactions: {class_counts['ROOT_OB_REACTION']}",
        f"- Direct or unclassified deliveries: {class_counts['DIRECT_OR_UNCLASSIFIED_DELIVERY']}",
        "",
        "## Reaction structure counts",
        "",
        "| Structure | Episodes |",
        "| --- | ---: |",
    ]
    report.extend(f"| {key} | {value} |" for key, value in counts.most_common())
    report.extend([
        "",
        "## Episodes",
        "",
        "| Candidate | Direction | Frozen | Objective reached | Reaction structure | Reaction time | Reaction price |",
        "| --- | --- | --- | --- | --- | --- | ---: |",
    ])
    for row in rows:
        report.append(
            f"| {row['candidateId']} | {row['direction']} | {row['scenarioFrozenAtUtc']} | "
            f"{row['objectiveReachedAtUtc']} | {row['reactionStructure']} | "
            f"{row['reactionAtUtc'] or '-'} | {row['reactionPrice'] or '-'} |"
        )
    (RUN / "OBJECTIVE_FIRST_RETRACEMENT_AUDIT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "episodes": len(rows),
        "classifications": class_counts,
        "structures": counts,
        "csv": str(output_csv),
    }, ensure_ascii=False, default=dict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
