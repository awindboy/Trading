from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz
from scripts.audit_legacy_truth_structures import (
    LEDGER,
    TRADES,
    bar_index,
    is_opposite,
    matching_fvg,
    objective_evidence,
    parse_zone,
    physical_zone_match,
)
from scripts.mentor_ai_replay import parse_utc, utc_text


SOURCE = ROOT / "output" / "mentor_50trade_oos_v2"
QUARANTINE_DECISIONS = SOURCE / "quarantine_lookahead_contaminated_decisions.jsonl"
QUARANTINE_TRADES = SOURCE / "quarantine_lookahead_contaminated_trades_37_50.csv"
OUT_DIR = ROOT / "output" / "gemini_oct28_31_protocol_v2_audit"
OUT_CSV = OUT_DIR / "LEGACY_FULL_PROTOCOL_AUDIT.csv"
OUT_REPORT = OUT_DIR / "LEGACY_FULL_PROTOCOL_AUDIT.md"
CORRECTED_TRADES = (
    ROOT / "output" / "mentor_oct27_31_high_activity_truth" / "trades_corrected.csv"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def directional_delivery(
    m1, available_at: int, low: float, high: float, direction: str, decision: int
) -> tuple[bool, str]:
    start = int(np.searchsorted(m1.time, available_at, side="left"))
    end = int(np.searchsorted(m1.available_time, decision, side="right"))
    if end <= start:
        return False, ""
    later_close = m1.close[start:end]
    if direction == "LONG":
        matches = np.flatnonzero(later_close > high + 0.01)
    else:
        matches = np.flatnonzero(later_close < low - 0.01)
    if not matches.size:
        return False, ""
    index = start + int(matches[0])
    return True, utc_text(int(m1.available_time[index]))


def exact_prefix_equal(path_a: Path, path_b: Path, count: int) -> bool:
    a = [line for line in path_a.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    b = [line for line in path_b.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    return a[:count] == b[:count]


def trade_prefix_equal() -> bool:
    with TRADES.open(encoding="utf-8-sig", newline="") as handle:
        official = list(csv.DictReader(handle))[:13]
    with QUARANTINE_TRADES.open(encoding="utf-8-sig", newline="") as handle:
        quarantined = list(csv.DictReader(handle))
    common = set(official[0]).intersection(quarantined[0]) if official and quarantined else set()
    quarantined = quarantined[:13]
    return len(official) == len(quarantined) and all(
        all(left.get(key) == right.get(key) for key in common)
        for left, right in zip(official, quarantined)
    )


def main() -> int:
    config = json.loads(
        (ROOT / "data" / "mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )["config"]
    m1, _ = load_m1_npz(ROOT / str(config["dataset"]))
    frames = build_timeframes(m1)

    with TRADES.open(encoding="utf-8-sig", newline="") as handle:
        trades = list(csv.DictReader(handle))[:13]
    decisions_list = [
        json.loads(line)
        for line in LEDGER.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    decisions = {
        str(row["trade_id"]): row
        for row in decisions_list
        if row.get("status") == "ORDER_FROZEN" and row.get("trade_id")
    }

    rows: list[dict[str, object]] = []
    for trade in trades:
        decision = decisions[trade["trade_id"]]
        direction = str(decision["direction"])
        decision_at = parse_utc(str(decision["as_of"]))
        date = str(decision["as_of"])[:10]
        root = parse_zone(str(decision.get("root_ob", "")), date)
        child = parse_zone(str(decision.get("child_ob", "")), date)
        notes: list[str] = []

        root_price_match = root_opposite = False
        child_price_match = child_opposite = child_contained = False
        root_delivery = child_delivery = False
        root_delivery_at = child_delivery_at = ""
        if root and child:
            root_series = frames[str(root["tf"])]
            child_series = frames[str(child["tf"])]
            root_index = bar_index(root_series, int(root["open"]))
            child_index = bar_index(child_series, int(child["open"]))
            if root_index is not None and child_index is not None:
                root_price_match = physical_zone_match(root_series, root_index, root)
                root_opposite = is_opposite(
                    float(root_series.open[root_index]), float(root_series.close[root_index]), direction
                )
                child_price_match = physical_zone_match(child_series, child_index, child)
                child_opposite = is_opposite(
                    float(child_series.open[child_index]), float(child_series.close[child_index]), direction
                )
                child_contained = (
                    float(child["low"]) >= float(root["low"]) - 0.011
                    and float(child["high"]) <= float(root["high"]) + 0.011
                )
                root_delivery, root_delivery_at = directional_delivery(
                    m1,
                    int(root_series.available_time[root_index]),
                    float(root["low"]),
                    float(root["high"]),
                    direction,
                    decision_at,
                )
                child_delivery, child_delivery_at = directional_delivery(
                    m1,
                    int(child_series.available_time[child_index]),
                    float(child["low"]),
                    float(child["high"]),
                    direction,
                    decision_at,
                )

        execution_exists = False
        execution_available_at: int | None = None
        if trade["execution_model"] == "DELIVERY_FVG_REPLACEMENT":
            zones = re.findall(r"\[([0-9.]+),([0-9.]+)\]", str(decision.get("execution_zone", "")))
            if zones:
                expected = tuple(sorted(map(float, zones[-1])))
                fvg_index = matching_fvg(m1, direction, expected, decision_at)
                execution_exists = fvg_index is not None
                if fvg_index is not None:
                    execution_available_at = int(m1.available_time[fvg_index])
        else:
            execution_exists = bool(decision.get("execution_ob"))
            choch_match = re.search(r"(\d\d:\d\d)\s+body break", str(decision.get("choch", "")))
            if choch_match:
                execution_available_at = parse_utc(
                    f"{date}T{choch_match.group(1)}:00Z"
                ) + 60

        filled_at = parse_utc(str(trade["filled_at"]))
        decision_time_aligned = (
            execution_available_at is None or decision_at >= execution_available_at
        )
        fill_after_evidence = (
            execution_available_at is not None and filled_at >= execution_available_at
        )
        corrected_decision_at = max(decision_at, execution_available_at or decision_at)

        objective_exists, objective_unswept, objective_origin = objective_evidence(
            m1, decision_at, direction, float(trade["take_profit"])
        )
        expected_objective = (
            "EXTERNAL_LIQUIDITY"
            if trade["scope"] == "EXTERNAL_CONTINUATION"
            else "INTERNAL_LIQUIDITY"
        )
        scope_label_valid = trade["objective_type"] == expected_objective
        corrected_scope = trade["scope"]
        if not scope_label_valid and trade["objective_type"] == "INTERNAL_LIQUIDITY":
            corrected_scope = "INTERNAL_ROTATION"
            notes.append("scope label can be made internally consistent by relabeling to INTERNAL_ROTATION")

        order_index = next(
            i
            for i, item in enumerate(decisions_list)
            if item.get("trade_id") == trade["trade_id"] and item.get("status") == "ORDER_FROZEN"
        )
        prefreeze = any(
            item.get("as_of", "") < decision.get("as_of", "")
            and item.get("root_ob") == decision.get("root_ob")
            and item.get("child_ob") == decision.get("child_ob")
            for item in decisions_list[:order_index]
        )
        if not prefreeze:
            notes.append("no independent pre-delivery root/child/objective freeze record")
        if not child_opposite:
            notes.append("child conflicts with current last-opposite-candle OB definition")

        physical_geometry = all(
            (root_price_match, child_price_match, child_contained, execution_exists, objective_exists, objective_unswept)
        )
        current_contract_prices = physical_geometry and root_opposite and child_opposite
        blind_authority = current_contract_prices and scope_label_valid and prefreeze
        has_range_pd = bool(decision.get("active_range")) and bool(decision.get("pd_location"))
        has_sweep = bool(decision.get("final_sweep") or decision.get("mature_sweep"))
        has_choch = bool(decision.get("choch") or decision.get("meaningful_choch"))
        rows.append(
            {
                "trade_id": trade["trade_id"],
                "root_price_match": root_price_match,
                "root_opposite_color": root_opposite,
                "root_full_range_delivery_before_decision": root_delivery,
                "root_full_range_delivery_available_at": root_delivery_at,
                "child_price_match": child_price_match,
                "child_opposite_color": child_opposite,
                "child_contained": child_contained,
                "child_full_range_delivery_before_decision": child_delivery,
                "child_full_range_delivery_available_at": child_delivery_at,
                "execution_structure_exists": execution_exists,
                "execution_evidence_available_at": (
                    utc_text(execution_available_at) if execution_available_at else ""
                ),
                "recorded_decision_at": utc_text(decision_at),
                "decision_time_aligned": decision_time_aligned,
                "corrected_decision_at": utc_text(corrected_decision_at),
                "fill_after_execution_evidence": fill_after_evidence,
                "objective_prior_wick_exists": objective_exists,
                "objective_unswept": objective_unswept,
                "objective_origin": utc_text(objective_origin) if objective_origin else "",
                "recorded_scope": trade["scope"],
                "objective_type": trade["objective_type"],
                "scope_label_valid": scope_label_valid,
                "corrected_scope": corrected_scope,
                "range_pd_recorded": has_range_pd,
                "sweep_recorded": has_sweep,
                "choch_recorded": has_choch,
                "prefreeze_record_present": prefreeze,
                "physical_geometry_supported": physical_geometry,
                "current_contract_price_structure_supported": current_contract_prices,
                "blind_ground_truth_authority": blind_authority,
                "notes": "; ".join(notes),
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    audits_by_id = {str(row["trade_id"]): row for row in rows}
    corrected_trades: list[dict[str, object]] = []
    for trade in trades:
        corrected: dict[str, object] = dict(trade)
        audit = audits_by_id[str(trade["trade_id"])]
        corrected["decision_at"] = audit["corrected_decision_at"]
        corrections: list[str] = []
        if corrected["decision_at"] != trade["decision_at"]:
            corrections.append("DECISION_BAR_CLOSE_TIME")
        if not audit["scope_label_valid"]:
            corrected["scope"] = audit["corrected_scope"]
            corrections.append("SCOPE_LABEL")
        if trade["trade_id"] == "OOS2-002":
            corrected["child_time"] = "2025-10-29T07:50:00Z"
            corrected["child_low"] = "3959.92"
            corrected["child_high"] = "3964.62"
            corrections.append("CAUSAL_CHILD_CANDLE")
        if trade["trade_id"] == "OOS2-013":
            corrected["closed_at"] = "2025-10-31T10:06:00Z"
            corrected["holding_minutes"] = "18"
            corrections.append("FIRST_TERMINAL_BAR")
        corrected["corrections"] = "+".join(corrections) or "NONE"
        corrected["authority"] = "STRUCTURE_CONFIRMED_NOT_BLIND_CERTIFIED"
        corrected_trades.append(corrected)
    with CORRECTED_TRADES.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(corrected_trades[0]))
        writer.writeheader()
        writer.writerows(corrected_trades)

    count = lambda key: sum(bool(row[key]) for row in rows)
    scope_rows = [str(row["trade_id"]) for row in rows if not row["scope_label_valid"]]
    child_rows = [str(row["trade_id"]) for row in rows if not row["child_opposite_color"]]
    decision_identity = exact_prefix_equal(LEDGER, QUARANTINE_DECISIONS, 41)
    trade_identity = trade_prefix_equal()
    oos2_root = parse_zone(str(decisions["OOS2-002"].get("root_ob", "")), "2025-10-29")
    corrected_child_time = parse_utc("2025-10-29T07:50:00Z")
    corrected_child_index = bar_index(frames["M5"], corrected_child_time)
    corrected_child_ok = False
    corrected_child_text = "unresolved"
    if oos2_root and corrected_child_index is not None:
        corrected_low = float(frames["M5"].low[corrected_child_index])
        corrected_high = float(frames["M5"].high[corrected_child_index])
        corrected_child_ok = (
            float(frames["M5"].close[corrected_child_index])
            < float(frames["M5"].open[corrected_child_index])
            and corrected_low >= float(oos2_root["low"]) - 0.011
            and corrected_high <= float(oos2_root["high"]) + 0.011
            and float(trades[1]["stop_loss"]) < corrected_low
        )
        corrected_child_text = (
            f"M5 2025-10-29 07:50 [{corrected_low:.2f}, {corrected_high:.2f}]"
        )
    report = f"""# Legacy 13-Trade Full Protocol Audit

## Bottom line

The previous 13 trades are not fabricated price structures. Root/child ranges,
directional delivery, execution structures and objective wicks are overwhelmingly
present in the frozen OHLC. However, physical existence and blind selection are
different claims.

## Structure checks

| Check | Result |
| --- | ---: |
| Root price range matches raw candle | {count('root_price_match')}/13 |
| Root is the required opposite color | {count('root_opposite_color')}/13 |
| Child contained in root | {count('child_contained')}/13 |
| Child price range matches raw candle | {count('child_price_match')}/13 |
| Child is the required opposite color | {count('child_opposite_color')}/13 |
| Recorded execution FVG/OB exists | {count('execution_structure_exists')}/13 |
| Recorded decision time is after execution evidence | {count('decision_time_aligned')}/13 |
| Fill occurs after execution evidence is available | {count('fill_after_execution_evidence')}/13 |
| Objective is a prior exact wick | {count('objective_prior_wick_exists')}/13 |
| Objective remained unswept at decision | {count('objective_unswept')}/13 |
| Physical geometry supported | {count('physical_geometry_supported')}/13 |
| Current-contract price structure supported | {count('current_contract_price_structure_supported')}/13 |
| Independent pre-freeze evidence | {count('prefreeze_record_present')}/13 |

`Directional delivery beyond the full source candle range` is retained in the
CSV only as a diagnostic. It is not used as a pass/fail rule because the actual
structure reference broken by displacement was not recorded for most rows.

## Missing semantic evidence

- Active dealing range and PD location are explicitly recorded for only
  {count('range_pd_recorded')}/13 trades.
- A mature/final sweep is explicitly recorded for only {count('sweep_recorded')}/13 trades.
- The meaningful CHoCH reference is explicitly recorded for only {count('choch_recorded')}/13 trades.
- The exact protected swing broken by root/child displacement is not recorded
  trade-by-trade. Candle geometry cannot reconstruct that discretionary choice
  without inventing a pivot rule after the fact.

## Label-only corrections

- Decision timestamps: {13 - count('decision_time_aligned')}/13 rows store the
  visible M1 candle-open label instead of the information-available close time.
  Their fills still occur after the evidence is available in
  {count('fill_after_execution_evidence')}/13 rows. Replace `decision_at` with
  `corrected_decision_at` from the CSV; entry, SL, TP and outcome do not change.
- Scope labels: `{', '.join(scope_rows)}` use `EXTERNAL_CONTINUATION` with an
  `INTERNAL_LIQUIDITY` objective. Relabeling these rows to `INTERNAL_ROTATION`
  makes the stored scope/objective fields internally consistent without changing
  entry, SL, TP, result or R. It does not independently prove that the external
  H1/M30 map was interpreted correctly at the time.
- Exit time: `OOS2-013` should close at `2025-10-31T10:06:00Z`; outcome and R stay unchanged.

## Definition conflict

- Child OB: `{', '.join(child_rows)}` is a real contained M5 source candle and is
  followed by directional delivery, but it is not an opposite-color bullish OB
  under the current last-opposite-candle definition. This is not a label-only
  correction. The immediately preceding `{corrected_child_text}` is bearish,
  contained in the same M15 root, precedes the bullish delivery, and leaves the
  recorded SL beyond its distal: `{corrected_child_ok}`. It is therefore the
  concrete correction candidate, subject to the missing pre-freeze evidence.

## Blind-integrity finding

- First 41 official decision rows are byte-for-byte equal to the quarantined
  exposed-window decision rows: `{decision_identity}`.
- First 13 official trade rows are field-for-field equal to the quarantined rows:
  `{trade_identity}`.
- Official decisions SHA-256: `{sha256(LEDGER)}`.
- Quarantine decisions SHA-256: `{sha256(QUARANTINE_DECISIONS)}`.

No separate PREPARED record proves that owner, objective, root and child were
selected before delivery. The old 13 rows are therefore a valid
**structure-and-execution benchmark**, but the existing files cannot certify
them as a future-blind ground truth. That limitation cannot be repaired by
renaming fields.

## Verdict

Do not discard the 13 trades. Restore them as the benchmark for whether a model
can see the same physical opportunities. Apply the five scope-label corrections,
the `OOS2-002` child correction, and the one exit-time correction. After those
changes, all 13 have a mechanically compatible root-child-execution-objective
price chain. For
strict blind-reproducibility claims, require a new append-only replay; do not
pretend the missing pre-freeze evidence exists.

The non-destructive corrected benchmark is written to
`output/mentor_oct27_31_high_activity_truth/trades_corrected.csv`. The original
ledger and trade file remain unchanged.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(f"physicalGeometry={count('physical_geometry_supported')}/13")
    print(f"currentContractPrice={count('current_contract_price_structure_supported')}/13")
    print(f"blindAuthority={count('blind_ground_truth_authority')}/13")
    print(f"officialDecisionPrefixEqualsQuarantine={decision_identity}")
    print(f"officialTradePrefixEqualsQuarantine={trade_identity}")
    print(CORRECTED_TRADES)
    print(OUT_CSV)
    print(OUT_REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
