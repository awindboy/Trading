#!/usr/bin/env python3
"""Build the frozen V12 Phase-1K staged-funding counterfactual."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase0 import parse_cutoff
from build_v12_phase1d import load_market, write_csv, write_json
from v12_phase0_core import sha256_file
from v12_phase1j_core import build_run_timeline, event_snapshots, period_label
from v12_phase1k_core import CONTRACT_VERSION, POLICIES, admit_child, capital_summary, compare_summary


PREFIX = "V12_PHASE1K_"


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(path)
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def verify_hash(path: Path, expected: str, label: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} hash mismatch: {observed} != {expected}")


def verify_manifest_member(manifest_path: Path, member: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {item["name"]: item["sha256"] for item in manifest["files"]}.get(member.name)
    if not expected:
        raise ValueError(f"{member.name} absent from manifest")
    verify_hash(member, expected, member.name)


def load_children(context_path: Path, wave_path: Path) -> pd.DataFrame:
    context = pd.read_csv(context_path, low_memory=False)
    fields = [
        "signal_id", "event", "decision_time", "entry_time", "exit_time", "direction",
        "combined_R_units", "stopped_loss_units", "funded_units", "right_tail_ge_5R_units",
    ]
    context = context.loc[context["event"] == "ENTRY", fields].copy()
    wave = pd.read_csv(wave_path, usecols=["signal_id", "rid", "entry", "stop", "dir", "r7g_weight"])
    children = context.merge(wave, on="signal_id", validate="one_to_one")
    for field in ("decision_time", "entry_time", "exit_time"):
        children[field] = pd.to_datetime(children[field])
    return children.sort_values(["entry_time", "signal_id"]).reset_index(drop=True)


def event_times_for_runs(runs: pd.DataFrame, children: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, run in runs.sort_values(["run_start", "run_id"]).iterrows():
        local = children.loc[children["rid"] == run["run_id"]].sort_values(["entry_time", "signal_id"]).copy()
        terminal = pd.Timestamp(run["run_exit"]) + pd.Timedelta(minutes=1)
        timeline = build_run_timeline(market, local, run, terminal)
        snapshot = event_snapshots(timeline) if len(timeline) else pd.DataFrame()
        times = {}
        if len(snapshot):
            times = snapshot.set_index("snapshot")["bar_end"].to_dict()
        rows.append({
            "run_id": int(run["run_id"]),
            "first_two_favorable_time": times.get("FIRST_TWO_CONSECUTIVE_FAVORABLE_CLOSES"),
            "first_two_opposed_time": times.get("FIRST_TWO_CONSECUTIVE_OPPOSED_CLOSES"),
            "first_repaired_departure_time": times.get("FIRST_REPAIRED_DEPARTURE_ABOVE_PRE_OPPOSED_FAVORABLE_CLOSE_MAX"),
        })
    frame = pd.DataFrame(rows)
    for field in frame.columns[1:]:
        frame[field] = pd.to_datetime(frame[field])
    return frame


def make_policy_ledger(runs: pd.DataFrame, children: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    run_fields = runs[["run_id", "run_start", "run_class", "repeat_stop_run"]]
    merged = children.merge(run_fields, left_on="rid", right_on="run_id", validate="many_to_one")
    merged = merged.merge(events, on="run_id", validate="many_to_one")
    merged["child_ordinal"] = merged.groupby("run_id").cumcount() + 1
    merged["period"] = merged["run_start"].map(lambda value: period_label(pd.Timestamp(value)))
    rows: list[dict] = []
    for _, child in merged.iterrows():
        for policy in POLICIES:
            admitted = admit_child(
                policy, int(child["child_ordinal"]), pd.Timestamp(child["entry_time"]),
                child["first_two_favorable_time"] if pd.notna(child["first_two_favorable_time"]) else None,
                child["first_two_opposed_time"] if pd.notna(child["first_two_opposed_time"]) else None,
                child["first_repaired_departure_time"] if pd.notna(child["first_repaired_departure_time"]) else None,
            )
            item = child.to_dict()
            item["policy"] = policy
            item["admitted"] = int(admitted)
            rows.append(item)
    return pd.DataFrame(rows)


def scorecards(ledger: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    scopes = {
        "TRAIN": ["TRAIN"], "F1": ["F1"], "F2": ["F2"], "F3": ["F3"],
        "POOLED_TEST": ["F1", "F2", "F3"], "ALL": ["TRAIN", "F1", "F2", "F3"],
    }
    for scope, periods in scopes.items():
        local = ledger.loc[ledger["period"].isin(periods)]
        baseline_children = local.loc[(local["policy"] == "BASELINE") & (local["admitted"] == 1)]
        baseline = capital_summary(baseline_children)
        for policy in POLICIES:
            selected = local.loc[(local["policy"] == policy) & (local["admitted"] == 1)]
            rows.append({"scope": scope, "policy": policy, **compare_summary(capital_summary(selected), baseline)})
    return pd.DataFrame(rows)


def gates(scorecard: pd.DataFrame) -> pd.DataFrame:
    primary = scorecard.loc[scorecard["policy"] == "PROGRESSION_RELEASE"].set_index("scope")
    folds = primary.loc[["F1", "F2", "F3"]]
    pooled = primary.loc["POOLED_TEST"]
    checks = {
        "REPEAT_STOP_REMOVAL": pooled["repeat_stopped_units_removed_fraction"] >= 0.40 and (folds["repeat_stopped_units_removed_fraction"] >= 0.15).all(),
        "ALL_STOP_REMOVAL": pooled["all_stopped_units_removed_fraction"] >= 0.15,
        "TAIL_UNITS": pooled["tail_unit_retention"] >= 0.85 and (folds["tail_unit_retention"] >= 0.70).all(),
        "TAIL_JOURNEY_RUNS": pooled["tail_journey_run_retention"] >= 0.85 and (folds["tail_journey_run_retention"] >= 0.70).all(),
        "CHILD_FREQUENCY": (folds["child_retention"] >= 0.70).all(),
        "WIN_RATE": pooled["child_win_rate_change_pp"] >= 3.0 and int((folds["child_win_rate_change_pp"] >= 0).sum()) >= 2,
        "RAW_ECONOMICS": (folds["net_R_units"] > 0).all(),
        "EQUAL_STOP_BUDGET": pooled["equal_stop_budget_net_R_per_baseline_unit"] > pooled["baseline_net_R_per_unit"] and int((folds["equal_stop_budget_net_R_per_baseline_unit"] > folds["baseline_net_R_per_unit"]).sum()) >= 2,
    }
    return pd.DataFrame([{"gate": key, "passed": bool(value)} for key, value in checks.items()] + [{"gate": "OVERALL", "passed": bool(all(checks.values()))}])


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1k_contract.json")
    parser.add_argument("--phase1i", type=Path, default=repo / "output/v12_phase1i_run_episode_reverse_engineering_20260924_a")
    parser.add_argument("--phase1j", type=Path, default=repo / "output/v12_phase1j_within_run_causal_timeline_20260924_a")
    parser.add_argument("--phase1g-context", type=Path, default=repo / "output/v12_phase1g_continuous_intraday_path_20260924_a/V12_PHASE1G_V10_CHILD_PATH_CONTEXT.csv")
    parser.add_argument("--wave", type=Path, default=repo / "output/v11_wave_edge_20260922/V11_COMPLETED_WAVE_LEDGER.csv")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1k_staged_funding_counterfactual_20260924_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract/core version mismatch")
    safe_output(args.output, args.replace)
    hashes = contract["source_hashes"]
    i_manifest = args.phase1i / "V12_PHASE1I_MANIFEST.json"
    j_manifest = args.phase1j / "V12_PHASE1J_MANIFEST.json"
    run_path = args.phase1i / "V12_PHASE1I_RUN_EPISODES.csv"
    verify_hash(i_manifest, hashes["phase1i_manifest_sha256"], "Phase-1I manifest")
    verify_hash(j_manifest, hashes["phase1j_manifest_sha256"], "Phase-1J manifest")
    verify_manifest_member(i_manifest, run_path)
    verify_hash(args.phase1g_context, hashes["phase1g_child_path_context_sha256"], "Phase-1G Child context")
    verify_hash(args.wave, hashes["v11_completed_wave_ledger_sha256"], "Wave ledger")
    verify_hash(args.m1, hashes["raw_m1_full_sha256"], "raw M1")
    cutoff = parse_cutoff(contract["mechanism_cutoff"])
    market, audit = load_market(args.m1, cutoff)
    if audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("raw M1 prefix hash mismatch")
    runs = pd.read_csv(run_path)
    runs["run_start"] = pd.to_datetime(runs["run_start"])
    runs["run_exit"] = pd.to_datetime(runs["run_exit"])
    children = load_children(args.phase1g_context, args.wave)
    if len(runs) != 679 or len(children) != 1409:
        raise ValueError("frozen population mismatch")
    events = event_times_for_runs(runs, children, market)
    ledger = make_policy_ledger(runs, children, events)
    scorecard = scorecards(ledger)
    gate_frame = gates(scorecard)
    admitted = ledger.loc[ledger["admitted"] == 1].copy()
    output_files = {
        "V12_PHASE1K_RUN_EVENT_TIMES.csv": events,
        "V12_PHASE1K_CHILD_POLICY_LEDGER.csv": admitted[[
            "policy", "run_id", "run_start", "period", "run_class", "repeat_stop_run", "signal_id",
            "child_ordinal", "entry_time", "combined_R_units", "stopped_loss_units", "funded_units",
            "right_tail_ge_5R_units", "first_two_favorable_time", "first_two_opposed_time",
            "first_repaired_departure_time",
        ]],
        "V12_PHASE1K_POLICY_SCORECARD.csv": scorecard,
        "V12_PHASE1K_GATES.csv": gate_frame,
    }
    for name, frame in output_files.items():
        write_csv(args.output / name, frame.to_dict("records"), list(frame.columns))
    diagnostics = {
        "contract_version": CONTRACT_VERSION, "funded_runs": len(runs), "entry_children": len(children),
        "policy_rows": len(admitted), "primary_pass": bool(gate_frame.set_index("gate").loc["OVERALL", "passed"]),
        "post_cutoff_price_rows_parsed": audit.post_cutoff_price_rows_parsed,
        "raw_m1_prefix_sha256": audit.prefix_sha256,
    }
    write_json(args.output / "V12_PHASE1K_DIAGNOSTICS.json", diagnostics)
    members = []
    for path in sorted(args.output.glob(f"{PREFIX}*")):
        if path.name != "V12_PHASE1K_MANIFEST.json":
            members.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(args.output / "V12_PHASE1K_MANIFEST.json", {"contract_version": CONTRACT_VERSION, "files": members})
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
