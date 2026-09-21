"""Evaluate a +60m forming-H4 action-value overlay for V10 R7G.

This is a consumed-data development diagnostic only.  It does not promote a
strategy, threshold, model, or EA action.

The earlier intrabar study showed that next FAST-H4 color is predictable, but
that a binary NHA warning is not a sufficient exit policy.  This follow-up
keeps the existing causal +60m NHA score and asks the economically relevant
question directly:

    weighted value(EXIT NEWEST CHILD NOW) - weighted value(HOLD)

The fixed model is robust-scaled Ridge(alpha=1.0).  The action boundary is the
natural zero of predicted weighted delta-R; no threshold or model-family scan
is performed.  2025 is fit only on eligible 2024Q4 outcomes available before
2025, and 2026 is fit only on outcomes available before 2026.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler


NUMERIC_FEATURES = [
    "p_nha",
    "early_exit_R",
    "p_stop",
    "EV",
    "feedback_R",
    "r4_weight",
    "r7g_weight",
    "score_gap_q50",
    "score_gap_q75",
]
CATEGORICAL_FEATURES = ["stage", "direction"]
TEST_YEARS = (2025, 2026)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scored", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_population(scored_path: Path, events_path: Path) -> pd.DataFrame:
    scored = pd.read_csv(
        scored_path,
        parse_dates=["decision", "entry_time", "exit_time", "checkpoint_time", "label_available_at"],
    )
    scored = scored[scored["checkpoint_min"] == 60].copy()
    scored["alive_at_checkpoint"] = (
        scored["alive_at_checkpoint"].astype(str).str.lower().isin(["true", "1"])
    )
    scored = scored[scored["alive_at_checkpoint"]].copy()

    events = pd.read_csv(events_path)
    events["decision"] = pd.to_datetime(events["decision"], format="%Y.%m.%d %H:%M")
    event_columns = [
        "decision",
        "score",
        "q50",
        "q75",
        "r4_weight",
        "p_stop",
        "mu_nonstop",
        "EV",
        "feedback_R",
        "r7g_weight",
    ]
    events = events[event_columns].drop_duplicates("decision", keep="last")
    frame = scored.drop(columns=["r7g_weight"], errors="ignore").merge(
        events,
        on="decision",
        how="inner",
        validate="one_to_one",
    )
    frame["score_gap_q50"] = frame["score"] - frame["q50"]
    frame["score_gap_q75"] = frame["score"] - frame["q75"]
    frame["stage"] = np.select(
        [frame["k"] == 1, frame["k"] == 2],
        ["k1", "k2"],
        default="k3p",
    )
    frame["direction"] = np.where(frame["dir"] > 0, "LONG", "SHORT")
    frame["delta_R_per_unit"] = frame["early_exit_R"] - frame["R"]
    frame["delta_weighted_R"] = frame["delta_R_per_unit"] * frame["r7g_weight"]
    frame["exit_better"] = (frame["delta_weighted_R"] > 0.0).astype(int)
    return frame.sort_values("decision").reset_index(drop=True)


def model_pipeline() -> Pipeline:
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", RobustScaler(quantile_range=(10, 90))),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", drop="first")),
        ]
    )
    transform = ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return Pipeline([("prep", transform), ("model", Ridge(alpha=1.0))])


def score_outer_years(population: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scored_parts: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    for year in TEST_YEARS:
        boundary = pd.Timestamp(f"{year}-01-01")
        train = population[
            (population["decision"] < boundary)
            & (population["exit_time"] < boundary)
        ].copy()
        test = population[population["year"] == year].copy()
        if train.empty or test.empty:
            continue
        model = model_pipeline()
        model.fit(train[features], train["delta_weighted_R"])
        prediction = model.predict(test[features])
        test["predicted_delta_weighted_R"] = prediction
        test["action_value_exit"] = (prediction > 0.0).astype(int)
        scored_parts.append(test)
        metric_rows.append(
            {
                "test_year": year,
                "train_rows": int(len(train)),
                "test_rows": int(len(test)),
                "train_last_decision": train["decision"].max(),
                "test_exit_better_rate": float(test["exit_better"].mean()),
                "mae_weighted_R": float(mean_absolute_error(test["delta_weighted_R"], prediction)),
                "r2_weighted_R": float(r2_score(test["delta_weighted_R"], prediction)),
                "predicted_positive": int((prediction > 0.0).sum()),
            }
        )
        names = model.named_steps["prep"].get_feature_names_out()
        coefficients = model.named_steps["model"].coef_
        for name, coefficient in zip(names, coefficients):
            coefficient_rows.append(
                {"test_year": year, "feature": str(name), "coefficient": float(coefficient)}
            )
    return (
        pd.concat(scored_parts, ignore_index=True),
        pd.DataFrame(metric_rows),
        pd.DataFrame(coefficient_rows),
    )


def max_true_streak(values: pd.Series) -> int:
    best = current = 0
    for value in values.astype(bool):
        if value:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def policy_metrics(frame: pd.DataFrame, name: str, action: pd.Series) -> dict[str, object]:
    data = frame.sort_values("decision").copy()
    action = action.astype(bool).reindex(data.index)
    data["policy_R"] = np.where(action, data["early_exit_R"], data["R"])
    data["policy_stop"] = data["stop_hit"].astype(bool) & ~action
    weight = data["r7g_weight"].astype(float)
    baseline = float((data["R"] * weight).sum())
    policy = float((data["policy_R"] * weight).sum())
    positive_base = float((data["R"].clip(lower=0.0) * weight).sum())
    positive_retained = float(
        (
            data.loc[data["R"] > 0.0, "policy_R"].clip(lower=0.0)
            * weight[data["R"] > 0.0]
        ).sum()
    )
    tail = (data["L"] >= 6) & (data["R"] > 0.0)
    tail_base = float((data.loc[tail, "R"] * weight[tail]).sum())
    tail_retained = float(
        (data.loc[tail, "policy_R"].clip(lower=0.0) * weight[tail]).sum()
    )
    good = action & (data["delta_weighted_R"] > 0.0)
    bad = action & (data["delta_weighted_R"] <= 0.0)
    return {
        "policy": name,
        "children": int(len(data)),
        "actions": int(action.sum()),
        "good_actions": int(good.sum()),
        "bad_actions": int(bad.sum()),
        "action_precision": float(good.sum() / max(1, action.sum())),
        "gain_from_good_actions_R": float(data.loc[good, "delta_weighted_R"].sum()),
        "regret_from_bad_actions_R": float(data.loc[bad, "delta_weighted_R"].sum()),
        "baseline_hard_stops": int(data["stop_hit"].sum()),
        "policy_hard_stops": int(data["policy_stop"].sum()),
        "hard_stops_prevented": int((action & data["stop_hit"].astype(bool)).sum()),
        "baseline_max_stop_streak": max_true_streak(data["stop_hit"]),
        "policy_max_stop_streak": max_true_streak(data["policy_stop"]),
        "baseline_weighted_R": baseline,
        "policy_weighted_R": policy,
        "delta_weighted_R": policy - baseline,
        "positive_R_retention": positive_retained / positive_base if positive_base > 0.0 else np.nan,
        "L6plus_positive_R_retention": tail_retained / tail_base if tail_base > 0.0 else np.nan,
    }


def policy_table(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for year in [2025, 2026, "POOLED"]:
        subset = scored if year == "POOLED" else scored[scored["year"] == year]
        for name, action in [
            ("HOLD", pd.Series(False, index=subset.index)),
            ("NHA_PRIOR_Q90", subset["warn_q90"] == 1),
            (
                "NHA_Q90_CURRENT_LOSS",
                (subset["warn_q90"] == 1) & (subset["early_exit_R"] < 0.0),
            ),
            (
                "NHA_Q90_SEED1",
                (subset["warn_q90"] == 1) & (subset["r7g_weight"] == 1),
            ),
            (
                "NHA_Q90_CURRENT_LOSS_SEED1",
                (subset["warn_q90"] == 1)
                & (subset["early_exit_R"] < 0.0)
                & (subset["r7g_weight"] == 1),
            ),
            ("ACTION_VALUE_ZERO", subset["action_value_exit"] == 1),
            ("PERFECT_ACTION_VALUE_ORACLE", subset["delta_weighted_R"] > 0.0),
        ]:
            row = policy_metrics(subset, name, action)
            row["period"] = year
            rows.append(row)
    return pd.DataFrame(rows)


def run_block_bootstrap(scored: pd.DataFrame, draws: int = 20000) -> pd.DataFrame:
    data = scored.copy()
    rules = {
        "ACTION_VALUE_ZERO": data["action_value_exit"] == 1,
        "NHA_Q90_SEED1": (data["warn_q90"] == 1) & (data["r7g_weight"] == 1),
    }
    rows: list[dict[str, object]] = []
    for offset, (name, action) in enumerate(rules.items()):
        data["realized_policy_delta"] = np.where(action, data["delta_weighted_R"], 0.0)
        blocks = data.groupby("rid", sort=False)["realized_policy_delta"].sum().to_numpy(dtype=float)
        rng = np.random.default_rng(20260921 + offset)
        values = np.empty(draws, dtype=float)
        for i in range(draws):
            values[i] = rng.choice(blocks, size=len(blocks), replace=True).sum()
        rows.append(
            {
                "policy": name,
                "blocks": int(len(blocks)),
                "draws": draws,
                "observed_delta_R": float(blocks.sum()),
                "bootstrap_mean_R": float(values.mean()),
                "q025_R": float(np.quantile(values, 0.025)),
                "q50_R": float(np.quantile(values, 0.50)),
                "q975_R": float(np.quantile(values, 0.975)),
                "p_delta_gt_0": float(np.mean(values > 0.0)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    population = load_population(args.scored, args.events)
    scored, model_metrics, coefficients = score_outer_years(population)
    policies = policy_table(scored)
    bootstrap = run_block_bootstrap(scored)

    population_path = args.out_dir / "V10_INTRAH4_ACTION_VALUE_POPULATION.csv"
    scored_path = args.out_dir / "V10_INTRAH4_ACTION_VALUE_SCORED.csv"
    metrics_path = args.out_dir / "V10_INTRAH4_ACTION_VALUE_MODEL_METRICS.csv"
    coefficients_path = args.out_dir / "V10_INTRAH4_ACTION_VALUE_COEFFICIENTS.csv"
    policies_path = args.out_dir / "V10_INTRAH4_ACTION_VALUE_POLICIES.csv"
    bootstrap_path = args.out_dir / "V10_INTRAH4_ACTION_VALUE_BOOTSTRAP.csv"
    population.to_csv(population_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    scored.to_csv(scored_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    model_metrics.to_csv(metrics_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    coefficients.to_csv(coefficients_path, index=False)
    policies.to_csv(policies_path, index=False)
    bootstrap.to_csv(bootstrap_path, index=False)

    manifest = {
        "status": "CONSUMED_DATA_DEVELOPMENT_DIAGNOSTIC_ONLY",
        "source_scored": str(args.scored.resolve()),
        "source_scored_sha256": sha256_file(args.scored),
        "source_events": str(args.events.resolve()),
        "source_events_sha256": sha256_file(args.events),
        "checkpoint_min": 60,
        "population_rule": "R7G selected newest Child with usable +60m prefix and still alive at checkpoint",
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "target": "r7g_weight * (exit_now_R - hold_R)",
        "model": "RobustScaler(10,90) + one-hot categorical + Ridge(alpha=1.0)",
        "action": "exit newest Child iff predicted weighted delta-R > 0",
        "threshold_scan": False,
        "population_rows": int(len(population)),
        "outer_scored_rows": int(len(scored)),
        "outer_year_rows": {str(int(k)): int(v) for k, v in scored.groupby("year").size().items()},
        "outputs": [
            str(population_path),
            str(scored_path),
            str(metrics_path),
            str(coefficients_path),
            str(policies_path),
            str(bootstrap_path),
        ],
    }
    manifest_path = args.out_dir / "V10_INTRAH4_ACTION_VALUE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nMODEL_METRICS")
    print(model_metrics.to_string(index=False))
    print("\nPOLICIES")
    print(policies.to_string(index=False))
    print("\nBOOTSTRAP")
    print(bootstrap.to_string(index=False))


if __name__ == "__main__":
    main()
