#!/usr/bin/env python3
"""Build the frozen V12 Phase-1I run-episode reverse-engineering study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase0 import parse_cutoff
from build_v12_phase1d import load_market, write_csv, write_json
from build_v12_phase1h import feature_specs as phase1h_feature_specs
from v12_phase0_core import sha256_file
from v12_phase1g_core import Encoder, fit_ridge_logistic, predict_logistic, weighted_metrics
from v12_phase1h_core import attach_ha_features, build_h4_ha_features, compact_path_derivatives
from v12_phase1i_core import (
    CONTRACT_VERSION,
    annotate_prior_run_state,
    choose_train_threshold,
    classify_run,
    enrich_comparison,
    policy_mask,
    policy_summary,
)


PREFIX = "V12_PHASE1I_"
FOLDS = (
    ("F1", "2025-03-31T23:59:59", "2025-04-01T00:00:00", "2025-09-30T23:59:59"),
    ("F2", "2025-09-30T23:59:59", "2025-10-01T00:00:00", "2026-03-31T23:59:59"),
    ("F3", "2026-03-31T23:59:59", "2026-04-01T00:00:00", "2026-09-18T23:57:00"),
)


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


def prepare_runs(path_context: Path, wave_path: Path, market: pd.DataFrame,
                 phase1h_contract: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    children = pd.read_csv(path_context, low_memory=False)
    children = children.loc[children["event"] == "ENTRY"].copy()
    children["decision_time"] = pd.to_datetime(children["decision_time"])
    children["exit_time"] = pd.to_datetime(children["exit_time"])
    children = compact_path_derivatives(children, tuple(phase1h_contract["source_box_families"]))
    children = attach_ha_features(children, build_h4_ha_features(market))
    wave = pd.read_csv(wave_path, usecols=["signal_id", "rid", "L"])
    children = children.merge(wave, on="signal_id", validate="one_to_one")
    children["winning_child"] = (pd.to_numeric(children["combined_R_units"]) > 0).astype(int)
    children = children.sort_values(["decision_time", "signal_id"]).reset_index(drop=True).copy()

    compact_num, compact_cat = phase1h_feature_specs(phase1h_contract)["COMPACT_PATH"]
    first_fields = list(dict.fromkeys(
        ["rid", "signal_id", "decision_time", "direction", "L"]
        + compact_num + compact_cat + list(phase1h_contract["ha_ablation_fields"])
    ))
    first = children[first_fields].copy().groupby("rid", sort=False).first().reset_index()
    aggregate = children.groupby("rid", sort=False).agg(
        run_start=("decision_time", "min"),
        run_exit=("exit_time", "max"),
        direction_run=("direction", "first"),
        child_count=("signal_id", "size"),
        winning_children=("winning_child", "sum"),
        funded_units=("funded_units", "sum"),
        stopped_units=("stopped_loss_units", "sum"),
        net_R_units=("combined_R_units", "sum"),
        tail_units=("right_tail_ge_5R_units", "sum"),
        fast_run_h4_bars=("L", "first"),
    ).reset_index()
    runs = first.merge(aggregate, on="rid", validate="one_to_one", suffixes=("", "_aggregate"))
    runs = runs.rename(columns={"rid": "run_id", "signal_id": "first_signal_id"})
    runs["direction"] = runs["direction_run"]
    runs["run_class"] = [
        classify_run(stops, tail) for stops, tail in zip(runs["stopped_units"], runs["tail_units"])
    ]
    runs = annotate_prior_run_state(runs)
    runs["stop_only_target"] = (runs["run_class"] == "STOP_ONLY_RUN").astype(int)
    runs["tail_journey_target"] = (runs["run_class"] == "TAIL_JOURNEY_RUN").astype(int)
    return runs, children


def feature_sets(phase1h_contract: dict, phase1i_contract: dict) -> dict[str, tuple[list[str], list[str]]]:
    compact_num, compact_cat = phase1h_feature_specs(phase1h_contract)["COMPACT_PATH"]
    history_num = list(phase1i_contract["prior_run_numeric_fields"])
    history_cat = list(phase1i_contract["prior_run_categorical_fields"])
    ha = list(phase1h_contract["ha_ablation_fields"])
    return {
        "STOP_ONLY_RUN": (compact_num + history_num + ha, compact_cat + history_cat),
        "TAIL_JOURNEY_RUN": (compact_num + history_num, compact_cat + history_cat),
    }


def fit_head(train: pd.DataFrame, test: pd.DataFrame, target: str,
             numeric: list[str], categorical: list[str], ridges: list[float]) -> tuple[dict, np.ndarray, np.ndarray]:
    cut = max(50, int(len(train) * 0.8))
    inner_train, inner_valid = train.iloc[:cut], train.iloc[cut:]
    best_ridge, best_loss = None, float("inf")
    for ridge in ridges:
        encoder = Encoder(numeric, categorical).fit(inner_train)
        beta = fit_ridge_logistic(
            encoder.transform(inner_train), inner_train[target].to_numpy(int),
            inner_train["funded_units"].to_numpy(float), ridge,
        )
        probability = predict_logistic(encoder.transform(inner_valid), beta)
        loss = weighted_metrics(
            inner_valid[target].to_numpy(int), probability,
            inner_valid["funded_units"].to_numpy(float),
        )["logloss"]
        if loss < best_loss:
            best_ridge, best_loss = ridge, loss
    encoder = Encoder(numeric, categorical).fit(train)
    beta = fit_ridge_logistic(
        encoder.transform(train), train[target].to_numpy(int),
        train["funded_units"].to_numpy(float), float(best_ridge),
    )
    train_probability = predict_logistic(encoder.transform(train), beta)
    test_probability = predict_logistic(encoder.transform(test), beta)
    metrics = weighted_metrics(
        test[target].to_numpy(int), test_probability, test["funded_units"].to_numpy(float)
    )
    return {
        "selected_lambda": best_ridge,
        "inner_logloss": best_loss,
        "numeric_features": len(numeric),
        "categorical_features": len(categorical),
        **metrics,
    }, train_probability, test_probability


def comparator_masks(frame: pd.DataFrame, primary: np.ndarray) -> dict[str, np.ndarray]:
    baseline = np.ones(len(frame), dtype=bool)
    cooldown = frame["after_stop_candidate"].to_numpy(int) == 0
    oracle = frame["repeat_stop_run"].to_numpy(int) == 0
    return {
        "BASELINE": baseline,
        "PRIMARY_ASYMMETRIC": np.asarray(primary, dtype=bool),
        "BROAD_SKIP_ALL_AFTER_STOP": cooldown,
        "PERFECT_REPEAT_STOP_ORACLE": oracle,
    }


def scorecards_for(frame: pd.DataFrame, masks: dict[str, np.ndarray], fold: str,
                   threshold: float) -> list[dict]:
    baseline = policy_summary(frame, masks["BASELINE"])
    rows = []
    for policy, mask in masks.items():
        summary = enrich_comparison(policy_summary(frame, mask), baseline)
        rows.append({"fold": fold, "policy": policy, "threshold": threshold if policy == "PRIMARY_ASYMMETRIC" else np.nan,
                     **summary})
    return rows


def evaluate_gates(scorecards: pd.DataFrame) -> list[dict]:
    primary = scorecards.loc[scorecards["policy"] == "PRIMARY_ASYMMETRIC"].set_index("fold")
    folds = primary.loc[["F1", "F2", "F3"]]
    pooled = primary.loc["POOLED"]
    checks = {
        "REPEAT_STOP_REMOVAL": (
            pooled["repeat_stopped_units_removed_fraction"] >= 0.40
            and (folds["repeat_stopped_units_removed_fraction"] >= 0.15).all()
        ),
        "ALL_STOP_REMOVAL": pooled["all_stopped_units_removed_fraction"] >= 0.15,
        "TAIL_UNIT_RETENTION": (
            pooled["tail_unit_retention"] >= 0.85 and (folds["tail_unit_retention"] >= 0.70).all()
        ),
        "TAIL_JOURNEY_RETENTION": (
            pooled["tail_journey_run_retention"] >= 0.85
            and (folds["tail_journey_run_retention"] >= 0.70).all()
        ),
        "CHILD_FREQUENCY": (folds["child_retention"] >= 0.80).all(),
        "WIN_RATE": (
            pooled["child_win_rate_change_pp"] >= 3.0
            and int((folds["child_win_rate_change_pp"] >= 0).sum()) >= 2
        ),
        "RAW_ECONOMICS": (folds["net_R_units"] > 0).all(),
        "EQUAL_STOP_BUDGET": (
            pooled["equal_stop_budget_net_R_per_baseline_unit"] > pooled["baseline_net_R_per_unit"]
            and int((folds["equal_stop_budget_net_R_per_baseline_unit"] > folds["baseline_net_R_per_unit"]).sum()) >= 2
        ),
    }
    rows = []
    for gate, passed in checks.items():
        rows.append({"gate": gate, "passed": bool(passed)})
    rows.append({"gate": "OVERALL", "passed": bool(all(checks.values()))})
    return rows


def numeric_mechanism_contrasts(runs: pd.DataFrame, fields: list[str]) -> list[dict]:
    work = runs.copy()
    work["period"] = np.select(
        [
            work["_time"].between("2025-04-01", "2025-09-30 23:59:59"),
            work["_time"].between("2025-10-01", "2026-03-31 23:59:59"),
            work["_time"].between("2026-04-01", "2026-09-18 23:57:00"),
        ],
        ["F1", "F2", "F3"],
        default="TRAIN",
    )
    rows: list[dict] = []
    for cohort, cohort_frame in (
        ("ALL_FUNDED_RUNS", work),
        ("AFTER_STOP_CANDIDATES", work.loc[work["after_stop_candidate"] == 1]),
    ):
        classified = cohort_frame.loc[cohort_frame["run_class"].isin(["STOP_ONLY_RUN", "TAIL_JOURNEY_RUN"])]
        for period in ("POOLED", "TRAIN", "F1", "F2", "F3"):
            frame = classified if period == "POOLED" else classified.loc[classified["period"] == period]
            stop = frame.loc[frame["run_class"] == "STOP_ONLY_RUN"]
            tail = frame.loc[frame["run_class"] == "TAIL_JOURNEY_RUN"]
            for field in fields:
                stop_values = pd.to_numeric(stop[field], errors="coerce").dropna().to_numpy(float)
                tail_values = pd.to_numeric(tail[field], errors="coerce").dropna().to_numpy(float)
                combined = np.concatenate((stop_values, tail_values))
                scale = float(np.std(combined)) if len(combined) else np.nan
                difference = (
                    float(np.mean(tail_values) - np.mean(stop_values))
                    if len(stop_values) and len(tail_values) else np.nan
                )
                rows.append({
                    "cohort": cohort,
                    "period": period,
                    "feature": field,
                    "stop_runs": len(stop_values),
                    "tail_runs": len(tail_values),
                    "stop_mean": float(np.mean(stop_values)) if len(stop_values) else np.nan,
                    "tail_mean": float(np.mean(tail_values)) if len(tail_values) else np.nan,
                    "tail_minus_stop": difference,
                    "standardized_difference": difference / scale if np.isfinite(scale) and scale > 0 else np.nan,
                })
    return rows


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1i_contract.json")
    parser.add_argument("--phase1h-contract", type=Path, default=repo / "research/v12/v12_phase1h_contract.json")
    parser.add_argument("--phase1g", type=Path, default=repo / "output/v12_phase1g_continuous_intraday_path_20260924_a")
    parser.add_argument("--phase1h", type=Path, default=repo / "output/v12_phase1h_compact_conviction_head_20260924_a")
    parser.add_argument("--wave", type=Path, default=repo / "output/v11_wave_edge_20260922/V11_COMPLETED_WAVE_LEDGER.csv")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1i_run_episode_reverse_engineering_20260924_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    phase1h_contract = json.loads(args.phase1h_contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract/core version mismatch")
    safe_output(args.output, args.replace)
    hashes = contract["source_hashes"]
    verify_hash(args.phase1g / "V12_PHASE1G_MANIFEST.json", hashes["phase1g_manifest_sha256"], "Phase-1G manifest")
    verify_hash(args.phase1h / "V12_PHASE1H_MANIFEST.json", hashes["phase1h_manifest_sha256"], "Phase-1H manifest")
    verify_hash(args.wave, hashes["v11_completed_wave_ledger_sha256"], "Wave ledger")
    verify_hash(args.m1, hashes["raw_m1_full_sha256"], "raw M1")
    cutoff = parse_cutoff(contract["mechanism_cutoff"])
    market, audit = load_market(args.m1, cutoff)
    if audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("raw M1 prefix hash mismatch")

    runs, children = prepare_runs(
        args.phase1g / "V12_PHASE1G_V10_CHILD_PATH_CONTEXT.csv", args.wave, market, phase1h_contract
    )
    specs = feature_sets(phase1h_contract, contract)
    required = sorted({field for numeric, categorical in specs.values() for field in numeric + categorical})
    missing = [field for field in required if field not in runs]
    if missing:
        raise ValueError(f"missing contracted fields: {missing}")
    feature_rows = [
        {"head": head, "feature": field, "kind": kind}
        for head, (numeric, categorical) in specs.items()
        for kind, fields in (("NUMERIC", numeric), ("CATEGORICAL", categorical))
        for field in fields
    ]

    runs["_time"] = pd.to_datetime(runs["run_start"])
    metrics_rows: list[dict] = []
    prediction_parts: list[pd.DataFrame] = []
    threshold_rows: list[dict] = []
    scorecard_rows: list[dict] = []
    masks_by_fold: dict[str, dict[str, np.ndarray]] = {}
    test_by_fold: dict[str, pd.DataFrame] = {}
    for fold, train_end, test_start, test_end in FOLDS:
        train = runs.loc[runs["_time"] <= train_end].sort_values(["_time", "run_id"]).reset_index(drop=True)
        test = runs.loc[(runs["_time"] >= test_start) & (runs["_time"] <= test_end)].sort_values(["_time", "run_id"]).reset_index(drop=True)
        head_probability = {}
        for head, target in (("STOP_ONLY_RUN", "stop_only_target"), ("TAIL_JOURNEY_RUN", "tail_journey_target")):
            numeric, categorical = specs[head]
            score, train_p, test_p = fit_head(
                train, test, target, numeric, categorical, list(contract["regularization_grid"])
            )
            metrics_rows.append({
                "fold": fold, "head": head, "train_runs": len(train), "test_runs": len(test),
                "test_positive_runs": int(test[target].sum()), **score,
            })
            head_probability[head] = (train_p, test_p)
        train_conviction = head_probability["TAIL_JOURNEY_RUN"][0] - head_probability["STOP_ONLY_RUN"][0]
        test_conviction = head_probability["TAIL_JOURNEY_RUN"][1] - head_probability["STOP_ONLY_RUN"][1]
        threshold, search = choose_train_threshold(train, train_conviction, contract["threshold_selection"]["constraints"])
        for row in search:
            threshold_rows.append({"fold": fold, "selected": int(np.isclose(row["threshold"], threshold)), **row})
        primary = policy_mask(test, test_conviction, threshold)
        masks = comparator_masks(test, primary)
        masks_by_fold[fold] = masks
        test_by_fold[fold] = test
        scorecard_rows.extend(scorecards_for(test, masks, fold, threshold))
        local = test[[
            "run_id", "run_start", "direction", "run_class", "after_stop_candidate", "repeat_stop_run",
            "strict_adjacent_repeat_stop_run", "child_count", "funded_units", "stopped_units", "net_R_units",
            "tail_units", "winning_children", "known_consecutive_stop_only_runs",
        ]].copy()
        local.insert(0, "fold", fold)
        local["p_stop_only_run"] = head_probability["STOP_ONLY_RUN"][1]
        local["p_tail_journey_run"] = head_probability["TAIL_JOURNEY_RUN"][1]
        local["conviction_score"] = test_conviction
        local["selected_threshold"] = threshold
        local["primary_admitted"] = primary.astype(int)
        prediction_parts.append(local)

    pooled = pd.concat([test_by_fold[fold] for fold in ("F1", "F2", "F3")], ignore_index=True)
    pooled_masks = {
        policy: np.concatenate([masks_by_fold[fold][policy] for fold in ("F1", "F2", "F3")])
        for policy in ("BASELINE", "PRIMARY_ASYMMETRIC", "BROAD_SKIP_ALL_AFTER_STOP", "PERFECT_REPEAT_STOP_ORACLE")
    }
    scorecard_rows.extend(scorecards_for(pooled, pooled_masks, "POOLED", np.nan))
    scorecards = pd.DataFrame(scorecard_rows)
    gates = evaluate_gates(scorecards)
    predictions = pd.concat(prediction_parts, ignore_index=True)
    contrast_fields = sorted(set(specs["STOP_ONLY_RUN"][0] + specs["TAIL_JOURNEY_RUN"][0]))
    contrasts = numeric_mechanism_contrasts(runs, contrast_fields)

    run_output_fields = [
        "run_id", "run_start", "run_exit", "first_signal_id", "direction", "run_class", "child_count",
        "winning_children", "funded_units", "stopped_units", "net_R_units", "tail_units", "fast_run_h4_bars",
        "prior_funded_run_class", "prior_funded_run_direction", "known_consecutive_stop_only_runs",
        "prior_funded_run_stopped_units", "prior_funded_run_net_R_per_unit", "funded_run_id_gap",
        "hours_since_prior_funded_run_start", "prior_funded_run_known", "after_stop_candidate",
        "repeat_stop_run", "strict_adjacent_repeat_stop_run",
    ]
    outputs = {
        "RUN_EPISODES.csv": runs[run_output_fields].to_dict("records"),
        "FEATURE_SCHEMA.csv": feature_rows,
        "MODEL_METRICS.csv": metrics_rows,
        "PREDICTIONS.csv": predictions.to_dict("records"),
        "THRESHOLD_SEARCH.csv": threshold_rows,
        "POLICY_SCORECARD.csv": scorecard_rows,
        "MECHANISM_CONTRASTS.csv": contrasts,
        "GATES.csv": gates,
    }
    paths: list[Path] = []
    for name, rows in outputs.items():
        path = args.output / f"{PREFIX}{name}"
        write_csv(path, rows)
        paths.append(path)
    diagnostics = {
        "contract_version": contract["contract_version"],
        "contract_sha256": sha256_file(args.contract),
        "frozen_contract_commit": "f8e15f5",
        "cutoff": cutoff.isoformat(),
        "raw_m1_sha256": sha256_file(args.m1),
        "m1_prefix_rows": audit.parsed_price_rows,
        "m1_prefix_sha256": audit.prefix_sha256,
        "first_unrevealed_timestamp": audit.first_unrevealed_timestamp.isoformat() if audit.first_unrevealed_timestamp else None,
        "post_cutoff_price_rows_parsed": audit.post_cutoff_price_rows_parsed,
        "entry_children": len(children),
        "funded_fast_runs": len(runs),
        "run_classes": runs["run_class"].value_counts().sort_index().to_dict(),
        "after_stop_candidates": int(runs["after_stop_candidate"].sum()),
        "repeat_stop_runs": int(runs["repeat_stop_run"].sum()),
        "repeat_stopped_units": float(runs.loc[runs["repeat_stop_run"] == 1, "stopped_units"].sum()),
        "strict_repeat_stop_runs": int(runs["strict_adjacent_repeat_stop_run"].sum()),
        "strict_repeat_stopped_units": float(
            runs.loc[runs["strict_adjacent_repeat_stop_run"] == 1, "stopped_units"].sum()
        ),
        "primary_overall_pass": next(row["passed"] for row in gates if row["gate"] == "OVERALL"),
        "evidence_status": contract["evidence_status"],
        "trade_authority": False,
        "sizing_authority": False,
    }
    diagnostics_path = args.output / f"{PREFIX}DIAGNOSTICS.json"
    write_json(diagnostics_path, diagnostics)
    paths.append(diagnostics_path)
    manifest = {
        "contract_version": contract["contract_version"],
        "files": [{"name": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size}
                  for path in paths],
    }
    write_json(args.output / f"{PREFIX}MANIFEST.json", manifest)
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
