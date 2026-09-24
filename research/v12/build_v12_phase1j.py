#!/usr/bin/env python3
"""Build the frozen V12 Phase-1J within-run causal timeline study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase0 import parse_cutoff
from build_v12_phase1d import load_market, write_csv, write_json
from v12_phase0_core import sha256_file
from v12_phase1j_core import (
    CONTRACT_VERSION, EVENTS, build_run_timeline, event_snapshots, first_touch_time,
    rank_auc, standardized_difference, weighted_tail_price,
)


PREFIX = "V12_PHASE1J_"


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
        raise ValueError(f"{member.name} absent from Phase-1I manifest")
    verify_hash(member, expected, member.name)


def load_funded_children(path_context: Path, wave_path: Path) -> pd.DataFrame:
    context = pd.read_csv(
        path_context,
        usecols=["signal_id", "event", "right_tail_ge_5R_units"],
        low_memory=False,
    )
    context = context.loc[context["event"] == "ENTRY", ["signal_id", "right_tail_ge_5R_units"]]
    wave = pd.read_csv(
        wave_path,
        usecols=["signal_id", "rid", "r7g_weight", "entry", "stop", "entry_time", "exit_time", "stop_hit", "dir"],
    )
    children = context.merge(wave, on="signal_id", how="left", validate="one_to_one")
    if children["rid"].isna().any():
        raise ValueError("funded Child missing from Wave ledger")
    for field in ("entry_time", "exit_time"):
        children[field] = pd.to_datetime(children[field])
    return children.sort_values(["entry_time", "signal_id"]).reset_index(drop=True)


def build_terminals(runs: pd.DataFrame, children: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, run in runs.iterrows():
        local = children.loc[children["rid"] == run["run_id"]].sort_values(["entry_time", "signal_id"])
        if len(local) != int(run["child_count"]):
            raise ValueError(f"funded Child count mismatch for run {run['run_id']}: {len(local)}")
        first = local.iloc[0]
        terminal_source = ""
        terminal_signal = ""
        tail_target = np.nan
        if run["run_class"] == "STOP_ONLY_RUN":
            stopped = local.loc[local["stop_hit"].astype(int) == 1].sort_values("exit_time")
            if stopped.empty:
                raise ValueError(f"stop-only run has no stopped Child: {run['run_id']}")
            terminal_child = stopped.iloc[0]
            terminal_time = pd.Timestamp(terminal_child["exit_time"])
            terminal_source = "FIRST_STOPPED_CHILD_EXIT"
            terminal_signal = terminal_child["signal_id"]
        else:
            touches: list[tuple[pd.Timestamp, str, float]] = []
            tail_children = local.loc[pd.to_numeric(local["right_tail_ge_5R_units"]) > 0]
            if tail_children.empty:
                raise ValueError(f"tail run has no labeled tail Child: {run['run_id']}")
            for _, child in tail_children.iterrows():
                target = weighted_tail_price(
                    float(child["entry"]), float(child["stop"]), int(child["dir"]), float(child["r7g_weight"])
                )
                touch = first_touch_time(
                    market, pd.Timestamp(child["entry_time"]), pd.Timestamp(child["exit_time"]), target, int(child["dir"])
                )
                if touch is not None:
                    touches.append((touch, child["signal_id"], target))
            if not touches:
                raise ValueError(f"tail threshold has no raw-M1 touch: {run['run_id']}")
            terminal_time, terminal_signal, tail_target = min(touches, key=lambda value: value[0])
            terminal_source = "FIRST_WEIGHTED_5R_M1_TOUCH"
        rows.append({
            "run_id": int(run["run_id"]), "run_start": run["run_start"], "run_class": run["run_class"],
            "after_stop_candidate": int(run["after_stop_candidate"]), "direction": run["direction"],
            "timeline_start": first["entry_time"], "first_signal_id": first["signal_id"],
            "first_entry": float(first["entry"]), "first_stop": float(first["stop"]),
            "first_risk": abs(float(first["entry"]) - float(first["stop"])),
            "terminal_time": terminal_time, "terminal_source": terminal_source,
            "terminal_signal_id": terminal_signal, "tail_target_price": tail_target,
            "minutes_start_to_terminal": (terminal_time - pd.Timestamp(first["entry_time"])).total_seconds() / 60.0,
            "child_count": int(run["child_count"]), "funded_units": float(run["funded_units"]),
            "stopped_units": float(run["stopped_units"]), "tail_units": float(run["tail_units"]),
        })
    return pd.DataFrame(rows)


def occurrence_table(runs: pd.DataFrame, snapshots: pd.DataFrame) -> pd.DataFrame:
    names = sorted(set(snapshots["snapshot"]))
    rows: list[dict] = []
    for cohort, cohort_runs in (
        ("ALL_CLASSIFIED_RUNS", runs),
        ("AFTER_STOP_CANDIDATES", runs.loc[runs["after_stop_candidate"] == 1]),
    ):
        for period in ("POOLED", "TRAIN", "F1", "F2", "F3"):
            local_runs = cohort_runs if period == "POOLED" else cohort_runs.loc[cohort_runs["period"] == period]
            for run_class in ("STOP_ONLY_RUN", "TAIL_JOURNEY_RUN"):
                denominator_ids = set(local_runs.loc[local_runs["run_class"] == run_class, "run_id"])
                for name in names:
                    observed = snapshots.loc[
                        snapshots["run_id"].isin(denominator_ids) & (snapshots["snapshot"] == name)
                    ]
                    rows.append({
                        "cohort": cohort, "period": period, "snapshot": name, "run_class": run_class,
                        "eligible_runs": len(denominator_ids), "observed_runs": int(observed["run_id"].nunique()),
                        "occurrence_fraction": observed["run_id"].nunique() / len(denominator_ids) if denominator_ids else np.nan,
                        "median_elapsed_minutes": float(observed["elapsed_minutes"].median()) if len(observed) else np.nan,
                    })
    return pd.DataFrame(rows)


def contrast_table(runs: pd.DataFrame, snapshots: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    rows: list[dict] = []
    for cohort, ids in (
        ("ALL_CLASSIFIED_RUNS", set(runs["run_id"])),
        ("AFTER_STOP_CANDIDATES", set(runs.loc[runs["after_stop_candidate"] == 1, "run_id"])),
    ):
        cohort_snapshots = snapshots.loc[snapshots["run_id"].isin(ids)]
        for period in ("POOLED", "TRAIN", "F1", "F2", "F3"):
            local = cohort_snapshots if period == "POOLED" else cohort_snapshots.loc[cohort_snapshots["period"] == period]
            for snapshot, frame in local.groupby("snapshot", sort=True):
                for field in fields:
                    stop = pd.to_numeric(frame.loc[frame["run_class"] == "STOP_ONLY_RUN", field], errors="coerce").dropna().to_numpy(float)
                    tail = pd.to_numeric(frame.loc[frame["run_class"] == "TAIL_JOURNEY_RUN", field], errors="coerce").dropna().to_numpy(float)
                    values = np.concatenate((stop, tail)) if len(stop) + len(tail) else np.array([])
                    y = np.concatenate((np.zeros(len(stop), dtype=int), np.ones(len(tail), dtype=int)))
                    auc = rank_auc(y, values) if len(values) else np.nan
                    difference = float(np.mean(tail) - np.mean(stop)) if len(stop) and len(tail) else np.nan
                    rows.append({
                        "cohort": cohort, "period": period, "snapshot": snapshot, "feature": field,
                        "stop_runs": len(stop), "tail_runs": len(tail),
                        "stop_mean": float(np.mean(stop)) if len(stop) else np.nan,
                        "tail_mean": float(np.mean(tail)) if len(tail) else np.nan,
                        "tail_minus_stop": difference,
                        "standardized_difference": standardized_difference(stop, tail) if len(stop) and len(tail) else np.nan,
                        "auc_tail_raw": auc,
                        "auc_tail_oriented": max(auc, 1.0 - auc) if np.isfinite(auc) else np.nan,
                    })
    return pd.DataFrame(rows)


def promotion_screen(occurrence: pd.DataFrame, contrasts: pd.DataFrame, contract: dict) -> pd.DataFrame:
    screen = contract["promotion_screen"]
    pooled_occ = occurrence.loc[
        (occurrence["cohort"] == "ALL_CLASSIFIED_RUNS") & (occurrence["period"] == "POOLED")
    ]
    all_contrasts = contrasts.loc[contrasts["cohort"] == "ALL_CLASSIFIED_RUNS"]
    rows: list[dict] = []
    for _, pooled in all_contrasts.loc[
        (all_contrasts["period"] == "POOLED") & (~all_contrasts["snapshot"].str.startswith("CHECKPOINT"))
    ].iterrows():
        event = pooled["snapshot"]
        feature = pooled["feature"]
        event_occ = pooled_occ.loc[pooled_occ["snapshot"] == event].set_index("run_class")
        occurrence_pass = (
            set(event_occ.index) == {"STOP_ONLY_RUN", "TAIL_JOURNEY_RUN"}
            and (event_occ["occurrence_fraction"] >= screen["minimum_event_occurrence_each_class_pooled"]).all()
        )
        folds = all_contrasts.loc[
            (all_contrasts["snapshot"] == event) & (all_contrasts["feature"] == feature)
            & all_contrasts["period"].isin(["F1", "F2", "F3"])
        ].set_index("period")
        count_pass = len(folds) == 3 and (
            (folds["stop_runs"] >= screen["minimum_class_count_per_test_fold"])
            & (folds["tail_runs"] >= screen["minimum_class_count_per_test_fold"])
        ).all()
        signs = np.sign(folds["tail_minus_stop"].to_numpy(float)) if len(folds) == 3 else np.array([])
        sign_pass = len(signs) == 3 and np.all(signs == signs[0]) and signs[0] != 0
        effect_pass = (
            abs(float(pooled["standardized_difference"])) >= 0.50
            or float(pooled["auc_tail_oriented"]) >= 0.70
        )
        rows.append({
            "snapshot": event, "feature": feature,
            "pooled_standardized_difference": pooled["standardized_difference"],
            "pooled_auc_tail_oriented": pooled["auc_tail_oriented"],
            "occurrence_pass": bool(occurrence_pass), "fold_count_pass": bool(count_pass),
            "stable_sign_pass": bool(sign_pass), "effect_pass": bool(effect_pass),
            "promotion_screen_pass": bool(occurrence_pass and count_pass and sign_pass and effect_pass),
        })
    return pd.DataFrame(rows)


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1j_contract.json")
    parser.add_argument("--phase1i", type=Path, default=repo / "output/v12_phase1i_run_episode_reverse_engineering_20260924_a")
    parser.add_argument("--phase1g-context", type=Path, default=repo / "output/v12_phase1g_continuous_intraday_path_20260924_a/V12_PHASE1G_V10_CHILD_PATH_CONTEXT.csv")
    parser.add_argument("--wave", type=Path, default=repo / "output/v11_wave_edge_20260922/V11_COMPLETED_WAVE_LEDGER.csv")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1j_within_run_causal_timeline_20260924_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract/core version mismatch")
    safe_output(args.output, args.replace)
    hashes = contract["source_hashes"]
    manifest_path = args.phase1i / "V12_PHASE1I_MANIFEST.json"
    run_path = args.phase1i / "V12_PHASE1I_RUN_EPISODES.csv"
    verify_hash(manifest_path, hashes["phase1i_manifest_sha256"], "Phase-1I manifest")
    verify_manifest_member(manifest_path, run_path)
    verify_hash(args.phase1g_context, hashes["phase1g_child_path_context_sha256"], "Phase-1G Child context")
    verify_hash(args.wave, hashes["v11_completed_wave_ledger_sha256"], "Wave ledger")
    verify_hash(args.m1, hashes["raw_m1_full_sha256"], "raw M1")

    cutoff = parse_cutoff(contract["mechanism_cutoff"])
    market, audit = load_market(args.m1, cutoff)
    if audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("raw M1 prefix hash mismatch")
    runs = pd.read_csv(run_path)
    runs = runs.loc[runs["run_class"].isin(["STOP_ONLY_RUN", "TAIL_JOURNEY_RUN"])].copy()
    runs["run_start"] = pd.to_datetime(runs["run_start"])
    runs["period"] = np.select(
        [runs["run_start"] <= "2025-03-31 23:59:59", runs["run_start"] <= "2025-09-30 23:59:59",
         runs["run_start"] <= "2026-03-31 23:59:59"], ["TRAIN", "F1", "F2"], default="F3",
    )
    children = load_funded_children(args.phase1g_context, args.wave)
    terminals = build_terminals(runs, children, market)
    terminal_map = terminals.set_index("run_id")["terminal_time"]
    timeline_parts: list[pd.DataFrame] = []
    for _, run in runs.sort_values(["run_start", "run_id"]).iterrows():
        local_children = children.loc[children["rid"] == run["run_id"]].copy()
        timeline = build_run_timeline(market, local_children, run, pd.Timestamp(terminal_map.loc[run["run_id"]]))
        if len(timeline):
            timeline_parts.append(timeline)
    timeline = pd.concat(timeline_parts, ignore_index=True) if timeline_parts else pd.DataFrame()
    snapshots = event_snapshots(timeline)
    fields = list(contract["path_fields"])
    occurrence = occurrence_table(runs, snapshots)
    contrasts = contrast_table(runs, snapshots, fields)
    promotion = promotion_screen(occurrence, contrasts, contract)

    output_files = {
        "V12_PHASE1J_RUN_TERMINALS.csv": terminals,
        "V12_PHASE1J_M15_TIMELINE.csv": timeline,
        "V12_PHASE1J_EVENT_SNAPSHOTS.csv": snapshots.drop(columns=["events"], errors="ignore"),
        "V12_PHASE1J_EVENT_OCCURRENCE.csv": occurrence,
        "V12_PHASE1J_FEATURE_CONTRASTS.csv": contrasts,
        "V12_PHASE1J_PROMOTION_SCREEN.csv": promotion,
    }
    for name, frame in output_files.items():
        write_csv(args.output / name, frame.to_dict("records"), list(frame.columns))
    diagnostics = {
        "contract_version": CONTRACT_VERSION,
        "classified_runs": int(len(runs)),
        "stop_only_runs": int((runs["run_class"] == "STOP_ONLY_RUN").sum()),
        "tail_journey_runs": int((runs["run_class"] == "TAIL_JOURNEY_RUN").sum()),
        "after_stop_classified_runs": int(runs["after_stop_candidate"].sum()),
        "timeline_runs": int(timeline["run_id"].nunique()),
        "timeline_rows": int(len(timeline)),
        "snapshot_rows": int(len(snapshots)),
        "runs_without_preterminal_completed_m15": int(len(runs) - timeline["run_id"].nunique()),
        "promotion_screen_passes": int(promotion["promotion_screen_pass"].sum()),
        "post_cutoff_price_rows_parsed": int(audit.post_cutoff_price_rows_parsed),
        "raw_m1_prefix_sha256": audit.prefix_sha256,
    }
    write_json(args.output / "V12_PHASE1J_DIAGNOSTICS.json", diagnostics)
    members = []
    for path in sorted(args.output.glob(f"{PREFIX}*")):
        if path.name == "V12_PHASE1J_MANIFEST.json":
            continue
        members.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(args.output / "V12_PHASE1J_MANIFEST.json", {"contract_version": CONTRACT_VERSION, "files": members})
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
