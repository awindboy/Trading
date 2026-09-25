#!/usr/bin/env python3
"""Build the frozen V12 Phase-1Q third-and-later stop-chain audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase1d import write_json
from build_v12_phase1o import FOLDS, OUTCOMES, ablations, fit_head
from v12_phase0_core import sha256_file
from v12_phase1g_core import weighted_metrics
from v12_phase1o_core import add_causal_history, policy_metrics, train_risk_threshold


PREFIX = "V12_PHASE1Q_"
CONTRACT_VERSION = "v12-phase1q-third-stop-chain-v1"


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(path)
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def verify(path: Path, expected: str, label: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} hash mismatch: {observed} != {expected}")


def max_stop_streak(frame: pd.DataFrame) -> int:
    best = current = 0
    for stopped in frame.sort_values(["decision_time", "signal_id"])["stop_hit"].astype(int):
        current = current + 1 if stopped else 0
        best = max(best, current)
    return best


def policy_row(population: str, model: str, fold: str, all_test: pd.DataFrame,
               cohort_test: pd.DataFrame, excluded: set[str]) -> dict:
    baseline = policy_metrics(all_test)
    policy_frame = all_test.loc[~all_test["signal_id"].isin(excluded)]
    policy = policy_metrics(policy_frame)
    chain_stops = int(cohort_test["stop_hit"].sum())
    removed = int(cohort_test.loc[cohort_test["signal_id"].isin(excluded), "stop_hit"].sum())
    scale = baseline["stops"] / policy["stops"] if policy["stops"] else np.nan
    equal_net = policy["net_R"] * scale if np.isfinite(scale) else np.nan
    return {
        "population": population, "model": model, "fold": fold,
        **{f"baseline_{key}": value for key, value in baseline.items()},
        **{f"policy_{key}": value for key, value in policy.items()},
        "baseline_max_stop_streak": max_stop_streak(all_test),
        "policy_max_stop_streak": max_stop_streak(policy_frame),
        "third_plus_children": len(cohort_test), "third_plus_stops": chain_stops,
        "excluded_third_plus_children": len(excluded), "removed_third_plus_stops": removed,
        "third_plus_stop_removal_rate": removed / chain_stops if chain_stops else np.nan,
        "child_retention": policy["children"] / baseline["children"] if baseline["children"] else np.nan,
        "tail_R_retention": policy["tail_ge5_R"] / baseline["tail_ge5_R"] if baseline["tail_ge5_R"] else np.nan,
        "equal_stop_budget_scale": scale, "equal_stop_budget_net_R": equal_net,
        "equal_stop_budget_R_retention": equal_net / baseline["net_R"] if baseline["net_R"] > 0 else np.nan,
    }


def run_population(population: str, frame: pd.DataFrame, contract: dict):
    work = add_causal_history(frame)
    work["right_tail_ge_5"] = (pd.to_numeric(work["R"]) >= 5).astype(int)
    cohort = work.loc[work["hist_known_prior_stop_streak"] >= 2].copy()
    specs = ablations(work)
    metrics, predictions, policies, inventory = [], [], [], []
    for model, (algorithm, numeric, categorical) in specs.items():
        inventory.append({"population": population, "model": model, "algorithm": algorithm,
                          "numeric_count": len(numeric), "categorical_count": len(categorical),
                          "numeric": "|".join(numeric), "categorical": "|".join(categorical)})
    for fold, train_end, test_start, test_end in FOLDS:
        train = cohort.loc[(cohort["decision_time"] <= train_end) & (cohort["label_available_at"] <= train_end)]
        test = cohort.loc[(cohort["decision_time"] >= test_start) & (cohort["decision_time"] <= test_end)]
        all_test = work.loc[(work["decision_time"] >= test_start) & (work["decision_time"] <= test_end)]
        for model, (algorithm, numeric, categorical) in specs.items():
            print(f"fitting {population} {fold} {model} rows={len(train)}/{len(test)}")
            heads = {}
            for outcome, target in OUTCOMES.items():
                p_train, p_test = fit_head(train, test, numeric, categorical, target, algorithm, population, contract)
                heads[outcome] = (p_train, p_test)
                metrics.append({
                    "population": population, "model": model, "algorithm": algorithm, "fold": fold,
                    "outcome": outcome, "train_rows": len(train), "test_rows": len(test),
                    "train_positive_rate": float(train[target].mean()), "test_positive_rate": float(test[target].mean()),
                    **weighted_metrics(test[target].to_numpy(int), p_test, np.ones(len(test))),
                })
            threshold = train_risk_threshold(heads["REPEAT_HARD_SL"][0])
            local = test[["signal_id", "decision_time", "label_available_at", "direction", "R", "stop_hit",
                          "right_tail_ge_5", "hist_known_prior_stop_streak"]].copy()
            local.insert(0, "population", population); local.insert(1, "model", model); local.insert(2, "fold", fold)
            local["p_third_plus_stop"] = heads["REPEAT_HARD_SL"][1]
            local["p_tail_ge5"] = heads["RIGHT_TAIL_R_GE_5"][1]
            local["train_top_risk_threshold"] = threshold
            local["excluded_high_chain_risk"] = (local["p_third_plus_stop"] >= threshold).astype(int)
            predictions.append(local)
            excluded = set(local.loc[local["excluded_high_chain_risk"] == 1, "signal_id"])
            policies.append(policy_row(population, model, fold, all_test, test, excluded))
    prediction_frame = pd.concat(predictions, ignore_index=True)
    for model, local in prediction_frame.groupby("model"):
        all_test = work.loc[work["decision_time"].between(FOLDS[0][2], FOLDS[-1][3])]
        cohort_test = cohort.loc[cohort["decision_time"].between(FOLDS[0][2], FOLDS[-1][3])]
        excluded = set(local.loc[local["excluded_high_chain_risk"] == 1, "signal_id"])
        policies.append(policy_row(population, model, "POOLED", all_test, cohort_test, excluded))
    return work, cohort, pd.DataFrame(metrics), prediction_frame, pd.DataFrame(policies), pd.DataFrame(inventory)


def gates(metrics: pd.DataFrame, policies: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for population in sorted(metrics["population"].unique()):
        base = metrics.loc[(metrics["population"] == population) & (metrics["model"] == "HISTORY_ONLY_RIDGE") &
                           (metrics["outcome"] == "REPEAT_HARD_SL")].set_index("fold")
        for model in sorted(metrics.loc[metrics["population"] == population, "model"].unique()):
            local = metrics.loc[(metrics["population"] == population) & (metrics["model"] == model) &
                                (metrics["outcome"] == "REPEAT_HARD_SL")].set_index("fold")
            delta = local["logloss"] - base["logloss"]
            policy = policies.loc[(policies["population"] == population) & (policies["model"] == model)]
            folds = policy.loc[policy["fold"] != "POOLED"]
            pooled = policy.loc[policy["fold"] == "POOLED"].iloc[0]
            checks = {
                "repeat_logloss": int((delta < 0).sum()) >= 2,
                "third_plus_removal": pooled["third_plus_stop_removal_rate"] >= .30 and
                                      bool((folds["third_plus_stop_removal_rate"] >= .15).all()),
                "participation": pooled["child_retention"] >= .90,
                "tail_retention": pooled["tail_R_retention"] >= .95 and bool((folds["tail_R_retention"] >= .90).all()),
                "max_streak": pooled["policy_max_stop_streak"] <= pooled["baseline_max_stop_streak"] - 1 and
                              bool((folds["policy_max_stop_streak"] <= folds["baseline_max_stop_streak"]).all()),
                "equal_stop_budget": pooled["equal_stop_budget_R_retention"] >= .95 and
                                     bool((folds["equal_stop_budget_net_R"] > 0).all()),
            }
            rows.append({"population": population, "model": model,
                         "repeat_logloss_mean_delta": float(delta.mean()),
                         "repeat_logloss_improved_folds": int((delta < 0).sum()),
                         **{f"gate_{key}": bool(value) for key, value in checks.items()},
                         "all_primary_gates_pass": bool(all(checks.values()) and model != "HISTORY_ONLY_RIDGE")})
    return pd.DataFrame(rows)


def save(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1q_contract.json")
    parser.add_argument("--phase1n", type=Path, default=repo / "output/v12_phase1n_lower_timeframe_temporal_information_20260925_a")
    parser.add_argument("--phase1p", type=Path, default=repo / "output/v12_phase1p_intermediate_clock_boundary_20260925_a")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1q_third_stop_chain_20260925_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract mismatch")
    safe_output(args.output, args.replace)
    sources = {
        "H2_K1": args.phase1p / "V12_PHASE1P_H2_K1_ENRICHED_LEDGER.csv",
        "H1_K1": args.phase1n / "V12_PHASE1N_H1_K1_ENRICHED_LEDGER.csv",
        "M30_K1": args.phase1p / "V12_PHASE1P_M30_K1_ENRICHED_LEDGER.csv",
        "M15_K1": args.phase1n / "V12_PHASE1N_M15_K1_ENRICHED_LEDGER.csv",
    }
    keys = {"H2_K1": "h2_ledger_sha256", "H1_K1": "h1_ledger_sha256",
            "M30_K1": "m30_ledger_sha256", "M15_K1": "m15_ledger_sha256"}
    for population, path in sources.items():
        verify(path, contract["source_hashes"][keys[population]], population)
    metrics_parts, prediction_parts, policy_parts, inventory_parts = [], [], [], []
    cohort_counts = {}
    for population, path in sources.items():
        frame = pd.read_csv(path, parse_dates=["decision_time", "label_available_at"])
        _, cohort, metric, prediction, policy, inventory = run_population(population, frame, contract)
        cohort_counts[population] = len(cohort)
        metrics_parts.append(metric); prediction_parts.append(prediction)
        policy_parts.append(policy); inventory_parts.append(inventory)
    metrics = pd.concat(metrics_parts, ignore_index=True)
    predictions = pd.concat(prediction_parts, ignore_index=True)
    policies = pd.concat(policy_parts, ignore_index=True)
    inventory = pd.concat(inventory_parts, ignore_index=True)
    gate_frame = gates(metrics, policies)
    save(metrics, args.output / f"{PREFIX}WALK_FORWARD_METRICS.csv")
    save(predictions, args.output / f"{PREFIX}CHAIN_TEST_PREDICTIONS.csv")
    save(policies, args.output / f"{PREFIX}POLICY_SCORECARDS.csv")
    save(inventory, args.output / f"{PREFIX}FEATURE_INVENTORY.csv")
    save(gate_frame, args.output / f"{PREFIX}GATES.csv")
    summary = {"contract_version": CONTRACT_VERSION, "cohort_counts": cohort_counts,
               "passing_models": gate_frame.loc[gate_frame["all_primary_gates_pass"], ["population", "model"]].to_dict("records"),
               "trade_authority": False, "sizing_authority": False}
    write_json(args.output / f"{PREFIX}SUMMARY.json", summary)
    manifest = {path.name: sha256_file(path) for path in sorted(args.output.glob(f"{PREFIX}*"))
                if path.name != f"{PREFIX}RELEASE_MANIFEST.json"}
    write_json(args.output / f"{PREFIX}RELEASE_MANIFEST.json", manifest)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
