"""Build the frozen V12 Phase-1C CRT-protected carry/repair study."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Optional

from build_v12_phase0 import PrefixAudit, iter_m1_prefix, parse_cutoff
from v12_phase0_core import iso_broker_label, sha256_file
from v12_phase1c_core import (
    CONTRACT_VERSION,
    GuardSpec,
    carry_is_eligible,
    direction_name,
    direction_sign,
    realized_r,
    repair_is_confirmed,
    stop_gap,
    stop_touched,
    summarize,
    target_open_at,
    parse_time,
)


PREFIX = "V12_PHASE1C_"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: Optional[list[str]] = None) -> None:
    names = fieldnames or (list(rows[0]) if rows else [])
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not names:
            return
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_prepare_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output directory is not empty: {path}")
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected path: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def file_manifest(path: Path) -> dict:
    rows = None
    if path.suffix.lower() == ".csv":
        with path.open("rb") as handle:
            rows = max(0, sum(1 for _ in handle) - 1)
    return {"file": path.name, "bytes": path.stat().st_size, "rows": rows, "sha256": sha256_file(path)}


def stable_id(prefix: str, payload: str) -> str:
    return prefix + hashlib.sha256(f"{CONTRACT_VERSION}|{payload}".encode("utf-8")).hexdigest()[:24]


def as_iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def build_specs(
    phase1b_dir: Path,
    selected_path: Path,
    full_path: Path,
) -> tuple[list[GuardSpec], list[dict], list[dict], dict, dict, dict]:
    child_context = {
        row["signal_id"]: row
        for row in read_csv(phase1b_dir / "V12_PHASE1B_V10_CHILD_DECISION_CONTEXT.csv")
    }
    journeys = {
        row["journey_id"]: row
        for row in read_csv(phase1b_dir / "V12_PHASE1B_JOURNEY_OUTCOMES.csv")
    }
    flips = sorted(
        read_csv(phase1b_dir / "V12_PHASE1B_NHA_DECISION_CONTEXT.csv"),
        key=lambda row: (parse_time(row["known_at"]), row["flip_id"]),
    )
    flip_at = {row["known_at"]: row for row in flips}
    flip_index = {row["flip_id"]: index for index, row in enumerate(flips)}
    full = {row["signal_id"]: row for row in read_csv(full_path)}
    k1 = {
        (row["decision"].replace(" ", "T"), direction_name(row["dir"])): row
        for row in full.values()
        if int(row["k"]) == 1
    }
    selected = [
        row for row in read_csv(selected_path)
        if row["policy"] == "ORIGINAL_FULL_R7G_PORTFOLIO"
    ]
    selected_by_signal = {row["signal_id"]: row for row in selected}

    specs: list[GuardSpec] = []
    carry_decisions: list[dict] = []
    episode_children: dict[str, list[str]] = defaultdict(list)
    episode_meta: dict[str, dict] = {}

    for selected_row in sorted(selected, key=lambda row: (row["decision_ts"], row["signal_id"])):
        signal_id = selected_row["signal_id"]
        full_row = full[signal_id]
        context = child_context[signal_id]
        exit_time = parse_time(full_row["exit_time"])
        flip = flip_at.get(as_iso(exit_time)) if exit_time else None
        if flip is None or not carry_is_eligible(context, full_row, flip):
            continue
        journey = journeys[context["journey_id"]]
        terminal = parse_time(journey["end_time"])
        if terminal is None or terminal <= exit_time:
            continue
        target_open = target_open_at(journey, exit_time)
        bridge_id = flip["flip_id"]
        spec = GuardSpec(
            spec_id=stable_id("v12carry-", signal_id),
            kind="SELECTED_CHILD_CARRY",
            direction=direction_sign(full_row["dir"]),
            entry=float(full_row["entry"]),
            stop=float(full_row["stop"]),
            start_time=exit_time,
            terminal_time=terminal,
            include_start_m1=False,
            journey_id=context["journey_id"],
            bridge_id=bridge_id,
            target_open=target_open,
            signal_id=signal_id,
            units=float(selected_row["r7g_weight"]),
        )
        specs.append(spec)
        episode_children[bridge_id].append(signal_id)
        episode_meta[bridge_id] = {"flip": flip, "journey": journey, "target_open": target_open}
        carry_decisions.append(
            {
                "contract_version": CONTRACT_VERSION,
                "carry_id": spec.spec_id,
                "signal_id": signal_id,
                "bridge_id": bridge_id,
                "journey_id": spec.journey_id,
                "direction": direction_name(spec.direction),
                "baseline_exit_time": as_iso(exit_time),
                "baseline_exit_reason": full_row["exit_reason"],
                "entry": spec.entry,
                "hard_sl": spec.stop,
                "funded_units": spec.units,
                "flip_state": flip["explanation_state"],
                "same_direction_arrivals_ending_run": int(flip["same_direction_external_arrivals_ending_run"]),
                "origin_opposite_target_open": target_open,
                "parent_terminal_time": as_iso(terminal),
                "parent_terminal_reason": journey["end_reason"],
                "outcome_fields_present": False,
            }
        )

    repair_decisions: list[dict] = []
    for bridge_id, meta in sorted(episode_meta.items(), key=lambda item: (item[1]["flip"]["known_at"], item[0])):
        start_flip = meta["flip"]
        journey = meta["journey"]
        start_index = flip_index[bridge_id]
        repair_flip = flips[start_index + 1] if start_index + 1 < len(flips) else None
        terminal = parse_time(journey["end_time"])
        repaired = bool(
            repair_flip
            and parse_time(repair_flip["known_at"]) < terminal
            and repair_is_confirmed(start_flip, repair_flip, journey["journey_id"])
        )
        repair_signal = None
        repair_status = "NO_FAST_RETURN_BEFORE_PARENT_END"
        if repaired:
            repair_signal = k1.get((repair_flip["scheduled_decision_time"], start_flip["old_fast_direction"]))
            repair_status = "REPAIR_CONFIRMED_WITH_K1" if repair_signal else "REPAIR_CONFIRMED_NO_VALID_K1"
        repair_id = stable_id("v12repair-", bridge_id)
        repair_target_open = bool(
            repaired and target_open_at(journey, parse_time(repair_flip["known_at"]))
        )
        decision = {
            "contract_version": CONTRACT_VERSION,
            "repair_id": repair_id,
            "bridge_id": bridge_id,
            "journey_id": journey["journey_id"],
            "direction": start_flip["old_fast_direction"],
            "bridge_start_time": start_flip["known_at"],
            "bridge_start_state": start_flip["explanation_state"],
            "carried_selected_children": len(episode_children[bridge_id]),
            "carried_funded_units": sum(float(selected_by_signal[s]["r7g_weight"]) for s in episode_children[bridge_id]),
            "origin_opposite_target_open_at_bridge": bool(meta["target_open"]),
            "repair_status": repair_status,
            "repair_time": repair_flip["known_at"] if repaired else None,
            "repair_k1_signal_id": repair_signal["signal_id"] if repair_signal else None,
            "repair_k1_already_r7g_selected": bool(repair_signal and repair_signal["signal_id"] in selected_by_signal),
            "origin_opposite_target_open_at_repair": repair_target_open,
            "parent_terminal_time": journey["end_time"],
            "parent_terminal_reason": journey["end_reason"],
            "outcome_fields_present": False,
        }
        repair_decisions.append(decision)
        if repair_signal:
            entry_time = parse_time(repair_signal["entry_time"])
            specs.append(
                GuardSpec(
                    spec_id=repair_id,
                    kind="REPAIR_CHILD",
                    direction=direction_sign(repair_signal["dir"]),
                    entry=float(repair_signal["entry"]),
                    stop=float(repair_signal["stop"]),
                    start_time=entry_time,
                    terminal_time=terminal,
                    include_start_m1=True,
                    journey_id=journey["journey_id"],
                    bridge_id=bridge_id,
                    target_open=repair_target_open,
                    signal_id=repair_signal["signal_id"],
                    units=1.0,
                )
            )

    aux = {
        "selected": selected,
        "selected_by_signal": selected_by_signal,
        "full": full,
        "child_context": child_context,
        "journeys": journeys,
        "episode_children": dict(episode_children),
    }
    return specs, carry_decisions, repair_decisions, aux, episode_meta, {row["flip_id"]: row for row in flips}


def run_guards(m1_path: Path, cutoff: datetime, specs: list[GuardSpec]) -> tuple[dict[str, dict], PrefixAudit]:
    pending = sorted(specs, key=lambda spec: (spec.start_time, spec.spec_id))
    index = 0
    active: dict[str, GuardSpec] = {}
    outcomes: dict[str, dict] = {}
    audit = PrefixAudit()

    for row in iter_m1_prefix(m1_path, cutoff, audit=audit):
        while index < len(pending):
            spec = pending[index]
            if spec.start_time < row.timestamp or (spec.include_start_m1 and spec.start_time <= row.timestamp):
                active[spec.spec_id] = spec
                index += 1
            else:
                break
        finished: list[str] = []
        for spec_id, spec in active.items():
            touched = stop_touched(spec, row.high, row.low)
            terminal_now = row.timestamp >= spec.terminal_time
            if touched:
                reason = "HARD_SL_PARENT_TERMINAL_SAME_M1_AMBIGUOUS" if terminal_now else (
                    "HARD_SL_GAP" if stop_gap(spec, row.open) else "HARD_SL"
                )
                exit_price = spec.stop
                alternative = row.open if terminal_now else None
                outcomes[spec_id] = {
                    "exit_time": as_iso(row.timestamp),
                    "exit_price": exit_price,
                    "exit_reason": reason,
                    "stop_hit": 1,
                    "gap_stop": int(stop_gap(spec, row.open)),
                    "same_m1_terminal_stop_ambiguous": int(terminal_now),
                    "alternative_parent_exit_price": alternative,
                    "R": realized_r(spec, exit_price),
                }
                finished.append(spec_id)
            elif terminal_now:
                outcomes[spec_id] = {
                    "exit_time": as_iso(row.timestamp),
                    "exit_price": row.open,
                    "exit_reason": "CRT_PARENT_TERMINAL",
                    "stop_hit": 0,
                    "gap_stop": 0,
                    "same_m1_terminal_stop_ambiguous": 0,
                    "alternative_parent_exit_price": None,
                    "R": realized_r(spec, row.open),
                }
                finished.append(spec_id)
        for spec_id in finished:
            active.pop(spec_id, None)

    for spec in pending[index:]:
        outcomes.setdefault(spec.spec_id, {"exit_reason": "NOT_STARTED_BY_CUTOFF"})
    for spec in active.values():
        outcomes.setdefault(spec.spec_id, {"exit_reason": "OPEN_AT_CUTOFF"})
    return outcomes, audit


def child_row(selected: dict, full: dict, outcome: Optional[dict], policy: str) -> dict:
    changed = outcome is not None and outcome.get("R") is not None
    r_value = float(outcome["R"]) if changed else float(selected["R"])
    stop = int(outcome["stop_hit"]) if changed else int(selected["stop_hit"])
    units = float(selected["r7g_weight"])
    exit_time = outcome["exit_time"] if changed else selected["exit_time"].replace(" ", "T")
    return {
        "policy": policy,
        "signal_id": selected["signal_id"],
        "entry_time": selected["entry_time"].replace(" ", "T"),
        "exit_time": exit_time,
        "year": int(selected["year"]),
        "direction": direction_name(selected["dir"]),
        "funded_units": units,
        "R": r_value,
        "combined_R_units": r_value * units,
        "stop_hit": stop,
        "stopped_loss_units": units if stop else 0.0,
        "right_tail_ge_5R_units": r_value * units if r_value * units >= 5.0 else 0.0,
        "exit_clock_changed": changed,
        "exit_reason": outcome["exit_reason"] if changed else full["exit_reason"],
    }


def scorecard_rows(policy_ledgers: dict[str, list[dict]]) -> list[dict]:
    rows: list[dict] = []
    for policy, ledger in policy_ledgers.items():
        groups = {"ALL": ledger}
        for year in sorted({row["year"] for row in ledger}):
            groups[f"YEAR={year}"] = [row for row in ledger if row["year"] == year]
        for side in ("LONG", "SHORT"):
            groups[f"SIDE={side}"] = [row for row in ledger if row["direction"] == side]
        for group, values in groups.items():
            metrics = summarize(values)
            metrics["changed_children"] = sum(bool(row["exit_clock_changed"]) for row in values)
            for metric, value in metrics.items():
                rows.append({"section": "SELECTED_PORTFOLIO", "policy": policy, "group": group, "metric": metric, "value": value})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m1", type=Path, required=True)
    parser.add_argument("--cutoff", default="2026-09-18T23:57:00")
    parser.add_argument("--phase1b-dir", type=Path, required=True)
    parser.add_argument("--selected-v10", type=Path, required=True)
    parser.add_argument("--full-v10", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace-output", action="store_true")
    args = parser.parse_args()
    cutoff = parse_cutoff(args.cutoff)
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("Phase-1C contract version mismatch")
    if parse_cutoff(contract["mechanism_cutoff"]) != cutoff:
        raise ValueError("cutoff differs from frozen contract")
    safe_prepare_output(args.output, args.replace_output)

    specs, carry_decisions, repair_decisions, aux, episode_meta, _ = build_specs(
        args.phase1b_dir, args.selected_v10, args.full_v10
    )
    outcomes, audit = run_guards(args.m1, cutoff, specs)
    spec_by_id = {spec.spec_id: spec for spec in specs}

    carry_outcomes: list[dict] = []
    carry_by_signal: dict[str, dict] = {}
    for decision in carry_decisions:
        spec = spec_by_id[decision["carry_id"]]
        result = outcomes[spec.spec_id]
        row = {
            "contract_version": CONTRACT_VERSION,
            "carry_id": spec.spec_id,
            "signal_id": spec.signal_id,
            **result,
            "combined_R_units": result.get("R") * spec.units if result.get("R") is not None else None,
            "outcome_fields_present": True,
        }
        carry_outcomes.append(row)
        carry_by_signal[spec.signal_id] = row

    selected = aux["selected"]
    full = aux["full"]
    active_ledger: list[dict] = []
    target_ledger: list[dict] = []
    baseline_ledger: list[dict] = []
    carry_decision_by_signal = {row["signal_id"]: row for row in carry_decisions}
    for selected_row in selected:
        signal_id = selected_row["signal_id"]
        baseline_ledger.append(child_row(selected_row, full[signal_id], None, "V10_BASELINE"))
        carry = carry_by_signal.get(signal_id)
        closed = carry if carry and carry.get("R") is not None else None
        active_ledger.append(child_row(selected_row, full[signal_id], closed, "CRT_ACTIVE_CARRY"))
        target_allowed = bool(carry_decision_by_signal.get(signal_id, {}).get("origin_opposite_target_open"))
        target_ledger.append(child_row(
            selected_row, full[signal_id], closed if target_allowed else None, "CRT_UNFINISHED_TARGET_CARRY"
        ))

    repair_decision_by_id = {row["repair_id"]: row for row in repair_decisions}
    repair_outcomes: list[dict] = []
    selected_by_signal = aux["selected_by_signal"]
    for spec in [item for item in specs if item.kind == "REPAIR_CHILD"]:
        result = outcomes[spec.spec_id]
        decision = repair_decision_by_id[spec.spec_id]
        base = full[spec.signal_id]
        carried_signals = aux["episode_children"][spec.bridge_id]
        carried_units = sum(float(selected_by_signal[s]["r7g_weight"]) for s in carried_signals)
        carried_value = sum(
            float(full[s]["entry"]) * float(selected_by_signal[s]["r7g_weight"])
            for s in carried_signals
        )
        old_average = carried_value / carried_units if carried_units else None
        new_average = (carried_value + spec.entry) / (carried_units + 1.0) if carried_units else None
        improvement = spec.direction * (old_average - new_average) if old_average is not None else None
        repair_outcomes.append(
            {
                "contract_version": CONTRACT_VERSION,
                "repair_id": spec.spec_id,
                "bridge_id": spec.bridge_id,
                "repair_k1_signal_id": spec.signal_id,
                "ordinary_v10_k1_exit_time": base["exit_time"].replace(" ", "T"),
                "ordinary_v10_k1_exit_reason": base["exit_reason"],
                "ordinary_v10_k1_R": float(base["R"]),
                **result,
                "parent_clock_delta_R": result.get("R") - float(base["R"]) if result.get("R") is not None else None,
                "origin_opposite_target_open_at_repair": decision["origin_opposite_target_open_at_repair"],
                "basket_average_entry_before": old_average,
                "basket_average_entry_after_one_unit": new_average,
                "direction_adjusted_average_entry_improvement": improvement,
                "average_entry_improved": improvement > 0.0 if improvement is not None else None,
                "outcome_fields_present": True,
            }
        )

    policies = {
        "V10_BASELINE": baseline_ledger,
        "CRT_ACTIVE_CARRY": active_ledger,
        "CRT_UNFINISHED_TARGET_CARRY": target_ledger,
    }
    scorecard = scorecard_rows(policies)

    for view, values in (
        ("REPAIR_ACTIVE", repair_outcomes),
        ("REPAIR_UNFINISHED_TARGET", [row for row in repair_outcomes if row["origin_opposite_target_open_at_repair"]]),
    ):
        closed = [row for row in values if row.get("R") is not None]
        stops = sum(int(row["stop_hit"]) for row in closed)
        gross_profit = sum(max(0.0, float(row["R"])) for row in closed)
        gross_loss = -sum(min(0.0, float(row["R"])) for row in closed)
        metrics = {
            "candidates": len(values),
            "closed": len(closed),
            "stops": stops,
            "stop_rate": stops / len(closed) if closed else None,
            "net_R": sum(float(row["R"]) for row in closed),
            "ordinary_k1_net_R_same_population": sum(float(row["ordinary_v10_k1_R"]) for row in closed),
            "parent_clock_delta_R": sum(float(row["parent_clock_delta_R"]) for row in closed),
            "profit_factor_R": gross_profit / gross_loss if gross_loss else None,
            "average_entry_improved_share": (
                sum(bool(row["average_entry_improved"]) for row in closed) / len(closed) if closed else None
            ),
        }
        for metric, value in metrics.items():
            scorecard.append({"section": "REPAIR_CHILD", "policy": view, "group": "ALL", "metric": metric, "value": value})

    baseline_summary = summarize(baseline_ledger)
    written: list[Path] = []
    outputs = {
        "CARRY_DECISIONS.csv": carry_decisions,
        "CARRY_OUTCOMES.csv": carry_outcomes,
        "REPAIR_DECISIONS.csv": repair_decisions,
        "REPAIR_OUTCOMES.csv": repair_outcomes,
        "PORTFOLIO_SCORECARD.csv": scorecard,
    }
    for suffix, rows in outputs.items():
        path = args.output / (PREFIX + suffix)
        write_csv(path, rows)
        written.append(path)

    diagnostics = {
        "contract_version": CONTRACT_VERSION,
        "causal_cutoff": as_iso(cutoff),
        "source": {
            "m1_path": str(args.m1),
            "m1_full_sha256": sha256_file(args.m1),
            "m1_prefix_audit": audit.to_dict(),
            "phase1b_dir": str(args.phase1b_dir),
            "phase1b_manifest_sha256": sha256_file(args.phase1b_dir / "V12_PHASE1B_MANIFEST.json"),
            "selected_v10_path": str(args.selected_v10),
            "selected_v10_sha256": sha256_file(args.selected_v10),
            "full_v10_path": str(args.full_v10),
            "full_v10_sha256": sha256_file(args.full_v10),
            "contract_sha256": sha256_file(args.contract),
        },
        "counts": {
            "selected_v10_children": len(selected),
            "carry_eligible_children": len(carry_decisions),
            "unique_bridge_episodes": len(repair_decisions),
            "repair_confirmed_with_k1": sum(row["repair_status"] == "REPAIR_CONFIRMED_WITH_K1" for row in repair_decisions),
            "repair_confirmed_no_valid_k1": sum(row["repair_status"] == "REPAIR_CONFIRMED_NO_VALID_K1" for row in repair_decisions),
            "no_repair_before_parent_end": sum(row["repair_status"] == "NO_FAST_RETURN_BEFORE_PARENT_END" for row in repair_decisions),
            "censored_guard_outcomes": sum(row.get("R") is None for row in carry_outcomes + repair_outcomes),
        },
        "baseline_invariants": baseline_summary,
        "decision_outcome_separation": True,
        "post_cutoff_price_rows_parsed": audit.post_cutoff_price_rows_parsed,
        "independent_future_validation": False,
        "trade_authority": False,
        "sizing_authority": False,
    }
    diagnostics_path = args.output / (PREFIX + "DIAGNOSTICS.json")
    write_json(diagnostics_path, diagnostics)
    written.append(diagnostics_path)
    manifest_path = args.output / (PREFIX + "MANIFEST.json")
    write_json(manifest_path, {
        "contract_version": CONTRACT_VERSION,
        "generated_at": "DETERMINISTIC_NO_WALL_CLOCK",
        "files": [file_manifest(path) for path in sorted(written)],
    })


if __name__ == "__main__":
    main()
