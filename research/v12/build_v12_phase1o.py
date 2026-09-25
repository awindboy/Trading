#!/usr/bin/env python3
"""Build the frozen V12 Phase-1O after-stop sequence-interaction audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from build_v12_phase1d import write_json
from build_v12_phase1n import feature_specs
from v12_phase0_core import sha256_file
from v12_phase1g_core import Encoder, fit_ridge_logistic, predict_logistic, weighted_metrics
from v12_phase1o_core import CONTRACT_VERSION, add_causal_history, policy_metrics, train_risk_threshold


PREFIX = "V12_PHASE1O_"
FOLDS = (
    ("F1", pd.Timestamp("2025-03-31 23:59:59"), pd.Timestamp("2025-04-01"), pd.Timestamp("2025-09-30 23:59:59")),
    ("F2", pd.Timestamp("2025-09-30 23:59:59"), pd.Timestamp("2025-10-01"), pd.Timestamp("2026-03-31 23:59:59")),
    ("F3", pd.Timestamp("2026-03-31 23:59:59"), pd.Timestamp("2026-04-01"), pd.Timestamp("2026-09-18 23:57:00")),
)
OUTCOMES = {"REPEAT_HARD_SL": "stop_hit", "RIGHT_TAIL_R_GE_5": "right_tail_ge_5"}


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


def unique(values):
    return list(dict.fromkeys(values))


def ablations(frame: pd.DataFrame) -> dict[str, tuple[str, list[str], list[str]]]:
    history = [column for column in frame if column.startswith("hist_")]
    phase1n = feature_specs(frame)

    def combine(name: str):
        numeric, categorical = phase1n[name]
        return unique(history + numeric), unique(categorical)

    history_only = (history, [])
    return {
        "HISTORY_ONLY_RIDGE": ("RIDGE", *history_only),
        "HISTORY_ONLY_HGB": ("HGB", *history_only),
        "HA_HISTORY_HGB": ("HGB", *combine("HA_ONLY")),
        "STATIC_TIME_HISTORY_HGB": ("HGB", *combine("HA_PLUS_STATIC_TIME")),
        "CONTINUOUS_CLOCK_HISTORY_HGB": ("HGB", *combine("HA_PLUS_CONTINUOUS_CLOCK")),
        "EVENT_HISTORY_HGB": ("HGB", *combine("HA_PLUS_EVENT")),
        "SESSION_PATH_HISTORY_HGB": ("HGB", *combine("HA_PLUS_SESSION_PATH")),
        "MICRO_HISTORY_HGB": ("HGB", *combine("HA_PLUS_MICRO_PATH")),
        "WAVE_HISTORY_HGB": ("HGB", *combine("HA_PLUS_WAVE")),
        "FULL_SEQUENCE_HGB": ("HGB", *combine("FULL_ASSEMBLY")),
    }


def fit_head(train: pd.DataFrame, test: pd.DataFrame, numeric: list[str], categorical: list[str],
             target: str, algorithm: str, population: str, contract: dict):
    encoder = Encoder(numeric, categorical).fit(train)
    x_train = encoder.transform(train)
    x_test = encoder.transform(test)
    y_train = train[target].to_numpy(int)
    if len(np.unique(y_train)) < 2:
        constant = float(y_train[0]) if len(y_train) else 0.0
        return np.full(len(train), constant), np.full(len(test), constant)
    if algorithm == "RIDGE":
        beta = fit_ridge_logistic(x_train, y_train, np.ones(len(train)), 10.0)
        return predict_logistic(x_train, beta), predict_logistic(x_test, beta)
    spec = contract["hgb_parameters"]
    min_leaf = spec["min_samples_leaf_h1"] if population.startswith(("H1_", "H2_")) else spec["min_samples_leaf_m15"]
    model = HistGradientBoostingClassifier(
        learning_rate=spec["learning_rate"], max_iter=spec["max_iter"],
        max_leaf_nodes=spec["max_leaf_nodes"], min_samples_leaf=min_leaf,
        l2_regularization=spec["l2_regularization"], random_state=spec["random_state"],
        early_stopping=False,
    )
    model.fit(x_train, y_train)
    return model.predict_proba(x_train)[:, 1], model.predict_proba(x_test)[:, 1]


def whole_policy_row(population: str, model: str, fold: str, all_test: pd.DataFrame,
                     cohort_test: pd.DataFrame, excluded_ids: set[str]) -> dict:
    baseline = policy_metrics(all_test)
    policy = policy_metrics(all_test.loc[~all_test["signal_id"].isin(excluded_ids)])
    cohort_stops = int(cohort_test["stop_hit"].sum())
    removed_repeats = int(cohort_test.loc[cohort_test["signal_id"].isin(excluded_ids), "stop_hit"].sum())
    scale = baseline["stops"] / policy["stops"] if policy["stops"] else np.nan
    equal_net = policy["net_R"] * scale if np.isfinite(scale) else np.nan
    return {
        "population": population, "model": model, "fold": fold,
        **{f"baseline_{key}": value for key, value in baseline.items()},
        **{f"policy_{key}": value for key, value in policy.items()},
        "after_stop_children": len(cohort_test), "after_stop_repeat_stops": cohort_stops,
        "excluded_after_stop_children": len(excluded_ids), "removed_repeat_stops": removed_repeats,
        "repeat_stop_removal_rate": removed_repeats / cohort_stops if cohort_stops else np.nan,
        "child_retention": policy["children"] / baseline["children"] if baseline["children"] else np.nan,
        "tail_R_retention": policy["tail_ge5_R"] / baseline["tail_ge5_R"] if baseline["tail_ge5_R"] else np.nan,
        "equal_stop_budget_scale": scale,
        "equal_stop_budget_net_R": equal_net,
        "equal_stop_budget_R_retention": equal_net / baseline["net_R"] if baseline["net_R"] > 0 else np.nan,
    }


def run_population(population: str, frame: pd.DataFrame, contract: dict):
    work = add_causal_history(frame)
    work["right_tail_ge_5"] = (pd.to_numeric(work["R"]) >= 5).astype(int)
    cohort = work.loc[work["after_stop_cohort"] == 1].copy()
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
            print(f"fitting {population} {fold} {model}")
            heads = {}
            for outcome, target in OUTCOMES.items():
                p_train, p_test = fit_head(train, test, numeric, categorical, target, algorithm, population, contract)
                heads[outcome] = (p_train, p_test)
                metrics.append({
                    "population": population, "model": model, "algorithm": algorithm,
                    "fold": fold, "outcome": outcome, "train_rows": len(train), "test_rows": len(test),
                    "train_positive_rate": float(train[target].mean()), "test_positive_rate": float(test[target].mean()),
                    "numeric_features": len(numeric), "categorical_features": len(categorical),
                    **weighted_metrics(test[target].to_numpy(int), p_test, np.ones(len(test))),
                })
            threshold = train_risk_threshold(heads["REPEAT_HARD_SL"][0])
            local = test[["signal_id", "decision_time", "label_available_at", "direction", "R", "stop_hit",
                          "right_tail_ge_5"]].copy()
            local.insert(0, "population", population)
            local.insert(1, "model", model)
            local.insert(2, "fold", fold)
            local["p_repeat_stop"] = heads["REPEAT_HARD_SL"][1]
            local["p_tail_ge5"] = heads["RIGHT_TAIL_R_GE_5"][1]
            local["train_top_risk_threshold"] = threshold
            local["excluded_high_repeat_risk"] = (local["p_repeat_stop"] >= threshold).astype(int)
            predictions.append(local)
            excluded = set(local.loc[local["excluded_high_repeat_risk"] == 1, "signal_id"])
            policies.append(whole_policy_row(population, model, fold, all_test, test, excluded))

    prediction_frame = pd.concat(predictions, ignore_index=True)
    for model, local in prediction_frame.groupby("model"):
        all_test = work.loc[work["decision_time"].between(FOLDS[0][2], FOLDS[-1][3])]
        cohort_test = cohort.loc[cohort["decision_time"].between(FOLDS[0][2], FOLDS[-1][3])]
        excluded = set(local.loc[local["excluded_high_repeat_risk"] == 1, "signal_id"])
        policies.append(whole_policy_row(population, model, "POOLED", all_test, cohort_test, excluded))
    return work, pd.DataFrame(metrics), prediction_frame, pd.DataFrame(policies), pd.DataFrame(inventory)


def evaluate_gates(metrics: pd.DataFrame, policies: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for population in sorted(metrics["population"].unique()):
        base = metrics.loc[(metrics["population"] == population) &
                           (metrics["model"] == "HISTORY_ONLY_RIDGE") &
                           (metrics["outcome"] == "REPEAT_HARD_SL")].set_index("fold")
        for model in sorted(metrics.loc[metrics["population"] == population, "model"].unique()):
            local = metrics.loc[(metrics["population"] == population) & (metrics["model"] == model) &
                                (metrics["outcome"] == "REPEAT_HARD_SL")].set_index("fold")
            delta = local["logloss"] - base["logloss"]
            policy = policies.loc[(policies["population"] == population) & (policies["model"] == model)]
            folds = policy.loc[policy["fold"] != "POOLED"]
            pooled = policy.loc[policy["fold"] == "POOLED"].iloc[0]
            gates = {
                "repeat_logloss": int((delta < 0).sum()) >= 2,
                "repeat_removal": pooled["repeat_stop_removal_rate"] >= 0.30 and
                                  bool((folds["repeat_stop_removal_rate"] >= 0.20).all()),
                "participation": pooled["child_retention"] >= 0.75,
                "tail_retention": pooled["tail_R_retention"] >= 0.90 and
                                  bool((folds["tail_R_retention"] >= 0.80).all()),
                "equal_stop_budget": pooled["equal_stop_budget_R_retention"] >= 0.95 and
                                     bool((folds["equal_stop_budget_net_R"] > 0).all()),
            }
            rows.append({
                "population": population, "model": model,
                "repeat_logloss_mean_delta": float(delta.mean()),
                "repeat_logloss_improved_folds": int((delta < 0).sum()),
                **{f"gate_{key}": bool(value) for key, value in gates.items()},
                "all_primary_gates_pass": bool(all(gates.values()) and model != "HISTORY_ONLY_RIDGE"),
            })
    return pd.DataFrame(rows)


def save(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1o_contract.json")
    parser.add_argument("--phase1n", type=Path, default=repo / "output/v12_phase1n_lower_timeframe_temporal_information_20260925_a")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1o_lower_timeframe_after_stop_sequence_20260925_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract/core mismatch")
    safe_output(args.output, args.replace)
    sources = {
        "H1_K1": args.phase1n / "V12_PHASE1N_H1_K1_ENRICHED_LEDGER.csv",
        "M15_K1": args.phase1n / "V12_PHASE1N_M15_K1_ENRICHED_LEDGER.csv",
    }
    verify(sources["H1_K1"], contract["source_hashes"]["phase1n_h1_enriched_ledger_sha256"], "H1 source")
    verify(sources["M15_K1"], contract["source_hashes"]["phase1n_m15_enriched_ledger_sha256"], "M15 source")

    metrics_parts, prediction_parts, policy_parts, inventory_parts = [], [], [], []
    cohort_counts = {}
    for population, path in sources.items():
        frame = pd.read_csv(path, parse_dates=["decision_time", "label_available_at", "entry_time", "exit_time"])
        work, metrics, predictions, policies, inventory = run_population(population, frame, contract)
        cohort_counts[population] = int(work["after_stop_cohort"].sum())
        metrics_parts.append(metrics)
        prediction_parts.append(predictions)
        policy_parts.append(policies)
        inventory_parts.append(inventory)
    metrics = pd.concat(metrics_parts, ignore_index=True)
    predictions = pd.concat(prediction_parts, ignore_index=True)
    policies = pd.concat(policy_parts, ignore_index=True)
    inventory = pd.concat(inventory_parts, ignore_index=True)
    gates = evaluate_gates(metrics, policies)

    save(metrics, args.output / f"{PREFIX}WALK_FORWARD_METRICS.csv")
    save(predictions, args.output / f"{PREFIX}AFTER_STOP_TEST_PREDICTIONS.csv")
    save(policies, args.output / f"{PREFIX}POLICY_SCORECARDS.csv")
    save(inventory, args.output / f"{PREFIX}FEATURE_INVENTORY.csv")
    save(gates, args.output / f"{PREFIX}GATES.csv")
    summary = {
        "contract_version": CONTRACT_VERSION,
        "evidence_status": contract["evidence_status"],
        "cohort_counts": cohort_counts,
        "passing_models": gates.loc[gates["all_primary_gates_pass"], ["population", "model"]].to_dict("records"),
        "trade_authority": False, "sizing_authority": False,
    }
    write_json(args.output / f"{PREFIX}SUMMARY.json", summary)
    manifest = {path.name: sha256_file(path) for path in sorted(args.output.glob(f"{PREFIX}*"))
                if path.name != f"{PREFIX}RELEASE_MANIFEST.json"}
    write_json(args.output / f"{PREFIX}RELEASE_MANIFEST.json", manifest)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
