#!/usr/bin/env python3
"""Build and score the frozen V12 Phase-1A no-ML structural baseline."""

from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import Counter
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from statistics import mean, median
from typing import Optional

from build_v12_phase0 import iter_m1_prefix, parse_cutoff
from v12_phase0_core import sha256_file
from v12_phase1a_core import (
    AUTHORIZED_INTERACTIONS,
    CONTRACT_VERSION,
    LANE_EXECUTION_TF,
    ChildSpec,
    ExecutionBar,
    make_child_spec,
    next_completed_parent_bar,
    score_outcomes,
    select_model1_trigger,
    simulate_children,
)
from render_v12_phase1a_summary import render as render_summary


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def optional_float(value: Optional[str]) -> Optional[float]:
    return float(value) if value not in (None, "") else None


def load_bars(path: Path) -> list[ExecutionBar]:
    bars: list[ExecutionBar] = []
    for row in read_csv(path):
        bars.append(
            ExecutionBar(
                timeframe=row["timeframe"],
                open_time=datetime.fromisoformat(row["open_time"]),
                close_time=datetime.fromisoformat(row["close_time"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                atr14=optional_float(row["atr14"]),
            )
        )
    bars.sort(key=lambda bar: bar.open_time)
    return bars


def write_csv(path: Path, rows: list[dict], fieldnames: Optional[list[str]] = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_prepare_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output directory is not empty: {path}; pass --replace-output")
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith("V12_PHASE1A_"):
                raise ValueError(f"refusing to replace unexpected output path: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def _time_slice(bars: list[ExecutionBar], opens: list[datetime], start: datetime, end: datetime) -> list[ExecutionBar]:
    first = bisect_left(opens, start)
    last = bisect_left(opens, end)
    return bars[first:last]


def build_specs(
    phase0_dir: Path,
    events: list[dict],
) -> tuple[list[ChildSpec], list[dict], dict]:
    bars = {
        timeframe: load_bars(phase0_dir / f"V12_PHASE0_{timeframe}_BARS.csv")
        for timeframe in ("H1", "H4", "D1", "W1")
    }
    opens = {timeframe: [bar.open_time for bar in values] for timeframe, values in bars.items()}
    specs: list[ChildSpec] = []
    dispositions: list[dict] = []
    reason_counts: Counter = Counter()

    for parent in events:
        lane = parent["lane"]
        parent_tf = parent["parent_timeframe"]
        direction = parent["hypothesis_direction"]
        interaction = parent["interaction"]
        c2_close = datetime.fromisoformat(parent["c2_close_time"])
        disposition = {
            "parent_id": parent["parent_id"],
            "lane": lane,
            "interaction": interaction,
            "hypothesis_direction": direction,
            "c2_close_time": parent["c2_close_time"],
            "c3_open_time": None,
            "c3_close_time": None,
            "control_status": "NOT_ELIGIBLE",
            "model1_status": "NOT_EVALUATED",
            "model1_candidate_bars": 0,
            "model1_trigger_open_time": None,
            "model1_confirmation_time": None,
            "model1_confirmation_phase": None,
            "children_created": 0,
        }
        if interaction not in AUTHORIZED_INTERACTIONS:
            if interaction in {"HIGH_OUTSIDE_ACCEPTANCE", "LOW_OUTSIDE_ACCEPTANCE"}:
                reason = "OUTSIDE_ACCEPTANCE_BRANCH_NOT_IMPLEMENTED_PHASE1A"
            elif interaction in {"DUAL_SWEEP_INSIDE", "DUAL_OR_CONFLICTED"}:
                reason = "DUAL_BRANCH_NOT_DIRECTIONALLY_AUTHORIZED"
            else:
                reason = "NO_EXTREME_INTERACTION"
            disposition["model1_status"] = reason
            reason_counts[reason] += 1
            dispositions.append(disposition)
            continue

        c2_open = datetime.fromisoformat(parent["c2_open_time"])
        c3 = next_completed_parent_bar(bars[parent_tf], c2_open)
        if c3 is None:
            disposition["model1_status"] = "COMPLETED_C3_UNAVAILABLE"
            reason_counts["COMPLETED_C3_UNAVAILABLE"] += 1
            dispositions.append(disposition)
            continue
        disposition["c3_open_time"] = c3.open_time.isoformat(timespec="seconds")
        disposition["c3_close_time"] = c3.close_time.isoformat(timespec="seconds")

        control = make_child_spec(
            parent=parent,
            family="C3_OPEN_CONTROL",
            risk_variant="C2_EXTREME",
            c3_close_time=c3.close_time,
        )
        specs.append(control)
        disposition["control_status"] = "CHILD_CREATED"

        execution_tf = LANE_EXECUTION_TF[lane]
        execution_window = _time_slice(
            bars[execution_tf],
            opens[execution_tf],
            datetime.fromisoformat(parent["c2_open_time"]),
            c3.close_time,
        )
        selection, status, candidate_count = select_model1_trigger(
            direction=direction,
            c1_high=float(parent["c1_high"]),
            c1_low=float(parent["c1_low"]),
            c2_open_time=datetime.fromisoformat(parent["c2_open_time"]),
            c2_close_time=c2_close,
            c3_close_time=c3.close_time,
            execution_bars=execution_window,
        )
        disposition["model1_status"] = status
        disposition["model1_candidate_bars"] = candidate_count
        if selection is not None and selection.confirmation.close_time < c3.close_time:
            disposition["model1_trigger_open_time"] = selection.trigger.open_time.isoformat(timespec="seconds")
            disposition["model1_confirmation_time"] = selection.confirmation.close_time.isoformat(timespec="seconds")
            disposition["model1_confirmation_phase"] = selection.confirmation_phase
            for risk_variant in ("C2_EXTREME", "TRIGGER_STRUCTURE"):
                specs.append(
                    make_child_spec(
                        parent=parent,
                        family="MODEL1_RELATIVE_THICK_V1",
                        risk_variant=risk_variant,
                        c3_close_time=c3.close_time,
                        trigger=selection,
                    )
                )
        elif selection is not None:
            disposition["model1_status"] = "CONFIRMATION_AT_C3_CLOSE_NO_ENTRY_TIME"
        reason_counts[disposition["model1_status"]] += 1
        disposition["children_created"] = len(
            [spec for spec in specs[-3:] if spec.parent_id == parent["parent_id"]]
        )
        dispositions.append(disposition)

    child_ids = [spec.child_id for spec in specs]
    if len(child_ids) != len(set(child_ids)):
        raise ValueError("duplicate Phase-1A child_id")
    return specs, dispositions, dict(sorted(reason_counts.items()))


def build_scorecard(outcomes: list[dict], matched_start: datetime, matched_end: datetime) -> list[dict]:
    rows: list[dict] = []
    variants = sorted(set((row["family"], row["risk_variant"]) for row in outcomes))
    scopes: list[tuple[str, list[dict]]] = [
        ("FULL_CONSUMED", outcomes),
        (
            "MATCHED_V10_WINDOW",
            [
                row
                for row in outcomes
                if datetime.fromisoformat(row["decision_time"]) >= matched_start
                and datetime.fromisoformat(row["expiry_time"]) <= matched_end
            ],
        ),
    ]
    for scope_name, scope_rows in scopes:
        for family, risk_variant in variants:
            base = [row for row in scope_rows if row["family"] == family and row["risk_variant"] == risk_variant]
            for target_number in (1, 2):
                overall = score_outcomes(base, target_number)
                rows.append(
                    {
                        "scope": scope_name,
                        "family": family,
                        "risk_variant": risk_variant,
                        "target": f"T{target_number}",
                        "slice_type": "OVERALL",
                        "slice_value": "ALL",
                        "drawdown_method": "REALIZED_R_AGGREGATED_BY_TERMINAL_TIMESTAMP",
                        **overall,
                    }
                )
                for slice_type, values in (
                    ("LANE", sorted(set(row["lane"] for row in base))),
                    ("DIRECTION", sorted(set(row["direction"] for row in base))),
                    ("YEAR", sorted(set((row["decision_time"] or "")[:4] for row in base))),
                ):
                    for value in values:
                        key = "lane" if slice_type == "LANE" else "direction" if slice_type == "DIRECTION" else "decision_time"
                        if slice_type == "YEAR":
                            subset = [row for row in base if row[key][:4] == value]
                        else:
                            subset = [row for row in base if row[key] == value]
                        rows.append(
                            {
                                "scope": scope_name,
                                "family": family,
                                "risk_variant": risk_variant,
                                "target": f"T{target_number}",
                                "slice_type": slice_type,
                                "slice_value": value,
                                "drawdown_method": "REALIZED_R_AGGREGATED_BY_TERMINAL_TIMESTAMP",
                                **score_outcomes(subset, target_number),
                            }
                        )
    return rows


def _max_drawdown(values_by_time: list[tuple[str, float]]) -> float:
    grouped: dict[str, float] = {}
    for timestamp, value in values_by_time:
        grouped[timestamp] = grouped.get(timestamp, 0.0) + value
    equity = peak = drawdown = 0.0
    for timestamp in sorted(grouped):
        equity += grouped[timestamp]
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def _max_v10_stop_streak(rows: list[dict]) -> int:
    streak = maximum = 0
    for row in sorted(rows, key=lambda item: (item["entry_time"], item["signal_id"])):
        if row["stop_hit"] == "1":
            streak += 1
            maximum = max(maximum, streak)
        else:
            streak = 0
    return maximum


def score_v10(rows: list[dict], weighted: bool) -> dict:
    value_field = "combined_R_units" if weighted else "R"
    values = [float(row[value_field]) for row in rows]
    units = sum(float(row["funded_units"]) for row in rows) if weighted else float(len(rows))
    stops = [row for row in rows if row["stop_hit"] == "1"]
    stopped_units = sum(float(row["funded_units"]) for row in stops) if weighted else float(len(stops))
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    net = sum(values)
    return {
        "children": len(rows),
        "funded_units": units,
        "stops": len(stops),
        "stopped_units": stopped_units,
        "stop_rate_children": len(stops) / len(rows) if rows else None,
        "stopped_units_per_100": stopped_units / units * 100.0 if units else None,
        "net_r": net,
        "gross_profit_r": gross_profit,
        "gross_loss_r": gross_loss,
        "pf_r": gross_profit / gross_loss if gross_loss else None,
        "net_r_per_100_funded_units": net / units * 100.0 if units else None,
        "mean_child_r": mean(values) if values else None,
        "median_child_r": median(values) if values else None,
        "max_drawdown_r": _max_drawdown([(row["exit_time"], float(row[value_field])) for row in rows]),
        "max_stop_streak": _max_v10_stop_streak(rows),
        "ge_2r_children": sum(value >= 2.0 for value in values),
        "ge_5r_children": sum(value >= 5.0 for value in values),
    }


def score_v12_for_comparison(rows: list[dict]) -> dict:
    filled = [row for row in rows if row["execution_state"] == "FILLED"]
    resolved = [row for row in filled if row["t1_r"] is not None]
    values = [float(row["t1_r"]) for row in resolved]
    stops = [row for row in filled if row["t1_state"] in {"STOPPED", "STOPPED_GAP"}]
    units = float(len(filled))
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    net = sum(values)
    return {
        "children": len(rows),
        "funded_units": units,
        "stops": len(stops),
        "stopped_units": float(len(stops)),
        "stop_rate_children": len(stops) / len(filled) if filled else None,
        "stopped_units_per_100": len(stops) / units * 100.0 if units else None,
        "net_r": net,
        "gross_profit_r": gross_profit,
        "gross_loss_r": gross_loss,
        "pf_r": gross_profit / gross_loss if gross_loss else None,
        "net_r_per_100_funded_units": net / units * 100.0 if units else None,
        "mean_child_r": mean(values) if values else None,
        "median_child_r": median(values) if values else None,
        "max_drawdown_r": _max_drawdown(
            [(row["t1_terminal_time"], float(row["t1_r"])) for row in resolved if row["t1_terminal_time"]]
        ),
        "max_stop_streak": score_outcomes(rows, 1)["max_stop_streak"],
        "ge_2r_children": sum(value >= 2.0 for value in values),
        "ge_5r_children": sum(value >= 5.0 for value in values),
    }


def build_comparison(
    outcomes: list[dict],
    v10_path: Path,
    matched_start: datetime,
    matched_end: datetime,
) -> list[dict]:
    v10 = [
        row
        for row in read_csv(v10_path)
        if row["policy"] == "ORIGINAL_FULL_R7G_PORTFOLIO"
        and matched_start <= datetime.strptime(row["entry_time"], "%Y-%m-%d %H:%M:%S") <= matched_end
        and datetime.strptime(row["exit_time"], "%Y-%m-%d %H:%M:%S") <= matched_end
    ]
    comparison = [
        {
            "strategy": "V10_SELECTED_CHILDREN_1U",
            "family": "V10_R7G_SELECTION",
            "risk_variant": "V10_STRUCTURAL_SL",
            **score_v10(v10, weighted=False),
        },
        {
            "strategy": "V10_R7G_HISTORICAL_FUNDED_UNITS",
            "family": "V10_R7G_SELECTION_AND_SIZING",
            "risk_variant": "V10_STRUCTURAL_SL",
            **score_v10(v10, weighted=True),
        },
    ]
    for family, risk_variant in sorted(set((row["family"], row["risk_variant"]) for row in outcomes)):
        selected = [
            row
            for row in outcomes
            if row["family"] == family
            and row["risk_variant"] == risk_variant
            and datetime.fromisoformat(row["decision_time"]) >= matched_start
            and datetime.fromisoformat(row["expiry_time"]) <= matched_end
        ]
        comparison.append(
            {
                "strategy": f"V12_{family}_{risk_variant}_T1",
                "family": family,
                "risk_variant": risk_variant,
                **score_v12_for_comparison(selected),
            }
        )
    for row in comparison:
        row["matched_start"] = matched_start.isoformat(timespec="seconds")
        row["matched_end"] = matched_end.isoformat(timespec="seconds")
        row["cost_mode"] = "SPREADLESS_STRUCTURAL_R"
        row["drawdown_method"] = "REALIZED_R_AGGREGATED_BY_TERMINAL_TIMESTAMP"
    return comparison


def build_counterfactual_audit(
    outcomes: list[dict],
    matched_start: datetime,
    matched_end: datetime,
) -> tuple[list[dict], list[dict]]:
    lookup = {
        (row["parent_id"], row["family"], row["risk_variant"]): row
        for row in outcomes
    }
    pairs = (
        (
            "CONFIRMATION_EFFECT",
            ("C3_OPEN_CONTROL", "C2_EXTREME"),
            ("MODEL1_RELATIVE_THICK_V1", "C2_EXTREME"),
        ),
        (
            "STOP_REFERENCE_EFFECT",
            ("MODEL1_RELATIVE_THICK_V1", "C2_EXTREME"),
            ("MODEL1_RELATIVE_THICK_V1", "TRIGGER_STRUCTURE"),
        ),
    )
    detail: list[dict] = []
    parent_ids = sorted(set(row["parent_id"] for row in outcomes))
    for effect, a_key, b_key in pairs:
        for parent_id in parent_ids:
            a = lookup.get((parent_id, *a_key))
            b = lookup.get((parent_id, *b_key))
            if a is None or b is None:
                continue
            a_r = optional_float(a["t1_r"])
            b_r = optional_float(b["t1_r"])
            detail.append(
                {
                    "effect": effect,
                    "parent_id": parent_id,
                    "lane": a["lane"],
                    "direction": a["direction"],
                    "decision_time_a": a["decision_time"],
                    "decision_time_b": b["decision_time"],
                    "expiry_time": a["expiry_time"],
                    "a_family": a["family"],
                    "a_risk_variant": a["risk_variant"],
                    "a_execution_state": a["execution_state"],
                    "a_no_execution_reason": a["no_execution_reason"],
                    "a_t1_state": a["t1_state"],
                    "a_t1_r": a_r,
                    "b_family": b["family"],
                    "b_risk_variant": b["risk_variant"],
                    "b_execution_state": b["execution_state"],
                    "b_no_execution_reason": b["no_execution_reason"],
                    "b_t1_state": b["t1_state"],
                    "b_t1_r": b_r,
                    "b_incrementally_blocked_a_fill": (
                        a["execution_state"] == "FILLED" and b["execution_state"] == "NO_EXECUTION"
                    ),
                    "common_fill_r_delta_b_minus_a": (
                        b_r - a_r
                        if a["execution_state"] == "FILLED"
                        and b["execution_state"] == "FILLED"
                        and a_r is not None
                        and b_r is not None
                        else None
                    ),
                }
            )

    summary: list[dict] = []
    for scope, start, end in (
        ("FULL_CONSUMED", datetime(1900, 1, 1), datetime(2100, 1, 1)),
        ("MATCHED_V10_WINDOW", matched_start, matched_end),
    ):
        for effect, _, _ in pairs:
            rows = [
                row
                for row in detail
                if row["effect"] == effect
                and datetime.fromisoformat(row["decision_time_a"]) >= start
                and datetime.fromisoformat(row["expiry_time"]) <= end
            ]
            blocked = [row for row in rows if row["b_incrementally_blocked_a_fill"]]
            blocked_resolved = [row for row in blocked if row["a_t1_r"] is not None]
            common = [
                row
                for row in rows
                if row["a_execution_state"] == "FILLED"
                and row["b_execution_state"] == "FILLED"
                and row["a_t1_r"] is not None
                and row["b_t1_r"] is not None
            ]
            summary.append(
                {
                    "scope": scope,
                    "effect": effect,
                    "paired_parents": len(rows),
                    "a_filled": sum(row["a_execution_state"] == "FILLED" for row in rows),
                    "b_filled": sum(row["b_execution_state"] == "FILLED" for row in rows),
                    "incrementally_blocked_a_fills": len(blocked),
                    "blocked_a_stops": sum(row["a_t1_state"] in {"STOPPED", "STOPPED_GAP"} for row in blocked),
                    "blocked_a_targets": sum(row["a_t1_state"] == "TARGET1" for row in blocked),
                    "blocked_a_expiries": sum(row["a_t1_state"] == "EXPIRED" for row in blocked),
                    "blocked_a_net_r": sum(float(row["a_t1_r"]) for row in blocked_resolved),
                    "common_fills": len(common),
                    "common_a_stops": sum(row["a_t1_state"] in {"STOPPED", "STOPPED_GAP"} for row in common),
                    "common_b_stops": sum(row["b_t1_state"] in {"STOPPED", "STOPPED_GAP"} for row in common),
                    "common_a_net_r": sum(float(row["a_t1_r"]) for row in common),
                    "common_b_net_r": sum(float(row["b_t1_r"]) for row in common),
                    "common_net_r_delta_b_minus_a": sum(
                        float(row["common_fill_r_delta_b_minus_a"]) for row in common
                    ),
                }
            )
    return detail, summary


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase0-dir", type=Path, default=repo_root / "output" / "v12_phase0_event_universe_20260923")
    parser.add_argument("--m1-source", type=Path, default=repo_root / "data" / "GOLD#" / "GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--contract", type=Path, default=Path(__file__).with_name("v12_phase1a_contract.json"))
    parser.add_argument("--v10-ledger", type=Path, default=repo_root / "output" / "v11_reassembly_stage3_20260923" / "V11_REASSEMBLY_STAGE3_CHILD_LEDGER.csv")
    parser.add_argument("--output", type=Path, default=repo_root / "output" / "v12_phase1a_no_ml_baseline_20260923")
    parser.add_argument("--replace-output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    safe_prepare_output(args.output, args.replace_output)
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("Phase-1A contract version mismatch")
    phase0_decisions = args.phase0_dir / "V12_PHASE0_DECISIONS.jsonl"
    if sha256_file(phase0_decisions) != contract["source_phase0_decisions_sha256"]:
        raise ValueError("Phase-0 decision ledger hash mismatch")

    events = read_csv(args.phase0_dir / "V12_PHASE0_PARENT_EVENTS.csv")
    specs, dispositions, reason_counts = build_specs(args.phase0_dir, events)
    outcomes = simulate_children(
        iter_m1_prefix(args.m1_source, parse_cutoff(contract["causal_cutoff"])),
        specs,
    )
    if {row["child_id"] for row in outcomes} != {spec.child_id for spec in specs}:
        raise ValueError("decision/outcome child sets differ")

    v10_rows = [row for row in read_csv(args.v10_ledger) if row["policy"] == "ORIGINAL_FULL_R7G_PORTFOLIO"]
    matched_start = min(datetime.strptime(row["entry_time"], "%Y-%m-%d %H:%M:%S") for row in v10_rows)
    matched_end = datetime(2026, 8, 28, 23, 57)
    scorecard = build_scorecard(outcomes, matched_start, matched_end)
    comparison = build_comparison(outcomes, args.v10_ledger, matched_start, matched_end)
    counterfactual_detail, counterfactual_summary = build_counterfactual_audit(
        outcomes, matched_start, matched_end
    )

    write_csv(args.output / "V12_PHASE1A_PARENT_DISPOSITIONS.csv", dispositions)
    write_csv(args.output / "V12_PHASE1A_CHILD_DECISIONS.csv", [spec.decision_record() for spec in specs])
    write_csv(args.output / "V12_PHASE1A_CHILD_OUTCOMES.csv", outcomes)
    write_csv(args.output / "V12_PHASE1A_SCORECARD.csv", scorecard)
    write_csv(args.output / "V12_PHASE1A_V10_COMPARISON.csv", comparison)
    write_csv(args.output / "V12_PHASE1A_COUNTERFACTUAL_DETAIL.csv", counterfactual_detail)
    write_csv(args.output / "V12_PHASE1A_COUNTERFACTUAL_SUMMARY.csv", counterfactual_summary)
    diagnostics = {
        "contract_version": CONTRACT_VERSION,
        "phase0_parent_records": len(events),
        "child_decisions": len(specs),
        "child_outcomes": len(outcomes),
        "families": dict(Counter((spec.family, spec.risk_variant) for spec in specs)),
        "parent_disposition_reasons": reason_counts,
        "filled": sum(row["execution_state"] == "FILLED" for row in outcomes),
        "no_execution_reasons": dict(sorted(Counter(
            row["no_execution_reason"] for row in outcomes if row["no_execution_reason"]
        ).items())),
        "ambiguous_t1": sum(row["t1_state"] == "AMBIGUOUS" for row in outcomes),
        "ambiguous_t2": sum(row["t2_state"] == "AMBIGUOUS" for row in outcomes),
        "post_cutoff_price_rows_parsed": 0,
    }
    # JSON cannot encode tuple keys.
    diagnostics["families"] = {
        f"{family}|{risk}": count
        for (family, risk), count in Counter((spec.family, spec.risk_variant) for spec in specs).items()
    }
    write_json(args.output / "V12_PHASE1A_DIAGNOSTICS.json", diagnostics)
    render_summary(args.output)

    output_hashes = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in sorted(args.output.glob("V12_PHASE1A_*"))
        if path.name != "V12_PHASE1A_MANIFEST.json"
    }
    pipeline_paths = (
        Path(__file__).resolve(),
        Path(__file__).with_name("v12_phase1a_core.py"),
        Path(__file__).with_name("test_v12_phase1a.py"),
        Path(__file__).with_name("validate_v12_phase1a_output.py"),
        Path(__file__).with_name("render_v12_phase1a_summary.py"),
        args.contract.resolve(),
    )
    manifest = {
        "generation": "V12",
        "phase": "PHASE_1A_NO_ML_BASELINE",
        "contract_version": CONTRACT_VERSION,
        "causal_cutoff": contract["causal_cutoff"],
        "post_cutoff_price_rows_parsed": 0,
        "phase0_decisions_sha256": sha256_file(phase0_decisions),
        "phase0_events_sha256": sha256_file(args.phase0_dir / "V12_PHASE0_PARENT_EVENTS.csv"),
        "m1_full_file_sha256": sha256_file(args.m1_source),
        "v10_comparator_sha256": sha256_file(args.v10_ledger),
        "matched_start": matched_start.isoformat(timespec="seconds"),
        "matched_end": matched_end.isoformat(timespec="seconds"),
        "parent_records": len(events),
        "child_decisions": len(specs),
        "outcome_records": len(outcomes),
        "trade_authority": False,
        "independent_validation": False,
        "pipeline_files": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in pipeline_paths
        },
        "files": output_hashes,
    }
    write_json(args.output / "V12_PHASE1A_MANIFEST.json", manifest)

    print(json.dumps({
        "status": "PASS",
        "output": str(args.output),
        "parents": len(events),
        "child_decisions": len(specs),
        "filled": diagnostics["filled"],
        "ambiguous_t1": diagnostics["ambiguous_t1"],
        "comparison": comparison,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
