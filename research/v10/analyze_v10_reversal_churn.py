"""Diagnose and reduce V10 PHA->NHA reversal churn on causal numeric state.

Inputs are frozen prefix-causal feature ledgers.  Outcome labels are used only
as answer sheets after their persisted ``label_available_at``.  The primary
question is deliberately sequence-level: can the next opposite k1 be put in
NEUTRAL often enough to reduce repeated Hard-SL campaigns while preserving
later k2+ participation and the long-run right tail?

Nothing produced by this script is strategy or production authority.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import OrderedDict
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler


EVAL_YEARS = (2024, 2025, 2026)
RISK_QUANTILES = (0.50, 0.60, 0.70, 0.80, 0.90)

CORE_REGIME_DIRECTION = [
    "fast_body_atr",
    "std_body_rng",
    "slow_body_rng",
    "adx28_rel",
    "adx28_delta3_rel",
    "di14_signed",
    "di28_signed",
    "ema8_21_signed",
    "ema8_slope",
    "path_eff4_rel",
    "path_eff12_rel",
    "path_eff4_delta",
    "flip8",
    "ltf_align_mean",
    "direction_vote",
]

MICRO_SETTLEMENT = [
    "raw_body_atr",
    "raw_range_atr",
    "raw_close_location",
    "opposing_wick_rng",
    "m1_path_eff_signed",
    "m1_aligned_return_rate",
    "m1_flip_rate",
    "m1_return_autocorr",
    "mfe_atr",
    "mae_atr",
    "settle_giveback_frac",
    "q4_signed_return_atr",
    "late_minus_early_atr",
    "tick_volume_rel",
    "spread_rel",
    "range_rel",
    "previous_bar_overlap_current",
    "inside_previous_bar",
    "close_break_previous_atr",
    "wick_break_previous_atr",
    "wick_break_without_close",
]

SEQUENCE_STATE = [
    "prev_run_len",
    "prev4_run_mean",
    "prev4_run_std",
    "prev4_short_rate",
    "prior_outcome_available",
    "prev_k1_R",
    "prev_k1_stop",
    "prior_short_loss_streak",
    "prior_stop_streak",
    "prior4_short_loss_rate",
    "prior4_stop_rate",
]

LTF_DETAIL = [
    f"{timeframe}_{feature}"
    for timeframe in ("m15", "m30", "h1")
    for feature in ("aligned", "transition", "streak", "body_eff", "body_rng", "opp_wick")
]

FEATURE_SETS = OrderedDict(
    [
        ("CORE", CORE_REGIME_DIRECTION),
        ("CORE_PLUS_SEQUENCE", CORE_REGIME_DIRECTION + SEQUENCE_STATE),
        ("CORE_PLUS_MICRO", CORE_REGIME_DIRECTION + MICRO_SETTLEMENT),
        (
            "INTEGRATED_COMPACT",
            CORE_REGIME_DIRECTION + MICRO_SETTLEMENT + SEQUENCE_STATE,
        ),
        (
            "INTEGRATED_PLUS_LTF",
            CORE_REGIME_DIRECTION + MICRO_SETTLEMENT + SEQUENCE_STATE + LTF_DETAIL,
        ),
    ]
)

TARGETS = OrderedDict(
    [
        ("IMMEDIATE_NHA_LOSS", "immediate_nha_loss"),
        ("SHORT_CHOP_LOSS", "short_chop_loss"),
        ("HARD_STOP", "hard_stop_target"),
    ]
)

PRIMARY_FEATURE_SET = "INTEGRATED_COMPACT"
DEFAULT_PRIMARY_TARGET = "immediate_nha_loss"


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--policy-ledger", required=True, type=Path)
    parser.add_argument("--micro-ledger", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument(
        "--primary-target",
        choices=tuple(TARGETS.values()),
        default=DEFAULT_PRIMARY_TARGET,
        help="Outcome used to create the prior-only risk score and policy frontier.",
    )
    return parser.parse_args()


def max_drawdown(values: np.ndarray, times: pd.Series) -> float:
    ordered = pd.DataFrame({"time": times, "value": values}).sort_values(
        "time", kind="mergesort"
    )
    equity = ordered["value"].cumsum().to_numpy(dtype=float)
    if not len(equity):
        return 0.0
    high_water = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    return float(np.max(high_water - equity))


def peak_concurrent_units(frame: pd.DataFrame, units: np.ndarray) -> float:
    events: list[tuple[pd.Timestamp, int, float]] = []
    for entry, exit_time, size in zip(frame["entry_time"], frame["exit_time"], units):
        if size <= 0.0:
            continue
        events.append((entry, 1, float(size)))
        events.append((exit_time, 0, -float(size)))
    running = 0.0
    peak = 0.0
    for _, _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        running += delta
        peak = max(peak, running)
    return peak


def consecutive_lengths(flags: list[bool]) -> list[int]:
    lengths: list[int] = []
    current = 0
    for flag in flags:
        if flag:
            current += 1
        elif current:
            lengths.append(current)
            current = 0
    if current:
        lengths.append(current)
    return lengths


def campaign_table(frame: pd.DataFrame, units: np.ndarray) -> pd.DataFrame:
    work = frame.copy()
    work["policy_W"] = units
    work = work[work["policy_W"] > 0.0].copy()
    if work.empty:
        return pd.DataFrame()
    work["weighted_R"] = work["R"] * work["policy_W"]
    work["weighted_pnl"] = work["pnl"] * work["policy_W"]
    work["selected_stop"] = work["stop_hit"].astype(int)
    work["selected_k1_stop"] = ((work["k"] == 1) & (work["stop_hit"] == 1)).astype(int)
    work["selected_short_loss_k1"] = (
        (work["k"] == 1) & (work["L"] <= 2) & (work["R"] < 0.0)
    ).astype(int)
    return (
        work.sort_values("decision")
        .groupby("rid", as_index=False, sort=False)
        .agg(
            start=("decision", "min"),
            end=("run_end_decision", "max"),
            year=("year", "first"),
            direction=("dir", "first"),
            L=("L", "first"),
            entries=("decision", "size"),
            units=("policy_W", "sum"),
            R=("weighted_R", "sum"),
            pnl=("weighted_pnl", "sum"),
            stop_rows=("selected_stop", "sum"),
            k1_stop_rows=("selected_k1_stop", "sum"),
            short_loss_k1_rows=("selected_short_loss_k1", "sum"),
        )
        .sort_values("start")
        .reset_index(drop=True)
    )


def streak_metrics(campaigns: pd.DataFrame) -> dict[str, object]:
    if campaigns.empty:
        return {
            "campaigns": 0,
            "losing_campaigns": 0,
            "stop_campaigns": 0,
            "max_loss_streak": 0,
            "loss_streaks_ge3": 0,
            "max_stop_streak": 0,
            "stop_streaks_ge3": 0,
        }
    loss_lengths = consecutive_lengths((campaigns["R"] < 0.0).tolist())
    stop_lengths = consecutive_lengths((campaigns["stop_rows"] > 0).tolist())
    return {
        "campaigns": int(len(campaigns)),
        "losing_campaigns": int((campaigns["R"] < 0.0).sum()),
        "stop_campaigns": int((campaigns["stop_rows"] > 0).sum()),
        "max_loss_streak": int(max(loss_lengths, default=0)),
        "loss_streaks_ge3": int(sum(length >= 3 for length in loss_lengths)),
        "max_stop_streak": int(max(stop_lengths, default=0)),
        "stop_streaks_ge3": int(sum(length >= 3 for length in stop_lengths)),
    }


def policy_metrics(
    frame: pd.DataFrame,
    units: np.ndarray,
    policy: str,
    period: str,
    baseline_units: np.ndarray,
) -> dict[str, object]:
    pnl = frame["pnl"].to_numpy(dtype=float) * units
    risk_r = frame["R"].to_numpy(dtype=float) * units
    selected = units > 0.0
    baseline_selected = baseline_units > 0.0
    gains = pnl[pnl > 0.0]
    losses = pnl[pnl < 0.0]
    r_gains = risk_r[risk_r > 0.0]
    r_losses = risk_r[risk_r < 0.0]
    stop = frame["stop_hit"].eq(1).to_numpy()
    k1 = frame["k"].eq(1).to_numpy()
    k1_short_loss = k1 & frame["L"].le(2).to_numpy() & frame["R"].lt(0.0).to_numpy()
    k1_immediate_loss = k1 & frame["L"].eq(1).to_numpy() & frame["R"].lt(0.0).to_numpy()
    positive_l6 = frame["L"].ge(6).to_numpy() & frame["pnl"].gt(0.0).to_numpy()
    baseline_stop_rows = int((baseline_selected & stop).sum())
    baseline_k1_stops = int((baseline_selected & stop & k1).sum())
    campaigns = campaign_table(frame, units)
    streak = streak_metrics(campaigns)
    removed = baseline_selected & ~selected
    return {
        "period": period,
        "policy": policy,
        "rows": int(len(frame)),
        "entries": int(selected.sum()),
        "units": float(units.sum()),
        "pnl": float(pnl.sum()),
        "gross_profit": float(gains.sum()),
        "gross_loss": float(losses.sum()),
        "pf": float(gains.sum() / -losses.sum()) if losses.sum() < 0.0 else float("inf"),
        "R": float(risk_r.sum()),
        "gross_R_profit": float(r_gains.sum()),
        "gross_R_loss": float(r_losses.sum()),
        "pf_R": float(r_gains.sum() / -r_losses.sum()) if r_losses.sum() < 0.0 else float("inf"),
        "dd_R": max_drawdown(risk_r, frame["exit_time"]),
        "hard_stop_rows": int((selected & stop).sum()),
        "k1_stop_rows": int((selected & stop & k1).sum()),
        "short_loss_k1_rows": int((selected & k1_short_loss).sum()),
        "immediate_nha_loss_rows": int((selected & k1_immediate_loss).sum()),
        "hard_stop_recall_removed": (
            (baseline_stop_rows - int((selected & stop).sum())) / baseline_stop_rows
            if baseline_stop_rows
            else float("nan")
        ),
        "k1_stop_recall_removed": (
            (baseline_k1_stops - int((selected & stop & k1).sum())) / baseline_k1_stops
            if baseline_k1_stops
            else float("nan")
        ),
        "removed_entries": int(removed.sum()),
        "removed_winners": int((removed & frame["R"].gt(0.0).to_numpy()).sum()),
        "removed_positive_R": float(
            np.sum(
                baseline_units
                * frame["R"].clip(lower=0.0).to_numpy(dtype=float)
                * removed
            )
        ),
        "l6_positive_pnl_retention": (
            float(np.sum(frame.loc[selected & positive_l6, "pnl"] * units[selected & positive_l6]))
            / float(
                np.sum(
                    frame.loc[baseline_selected & positive_l6, "pnl"]
                    * baseline_units[baseline_selected & positive_l6]
                )
            )
            if np.sum(
                frame.loc[baseline_selected & positive_l6, "pnl"]
                * baseline_units[baseline_selected & positive_l6]
            )
            > 0.0
            else float("nan")
        ),
        "weighted_position_hours": float(
            np.sum(units * frame["position_hours"].to_numpy(dtype=float))
        ),
        "max_single_units": float(units.max()) if len(units) else 0.0,
        "max_committed_units": peak_concurrent_units(frame, units),
        **streak,
    }


def make_logistic() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", RobustScaler(quantile_range=(10.0, 90.0))),
            ("model", LogisticRegression(C=0.1, max_iter=4000)),
        ]
    )


def make_histgb() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            (
                "model",
                HistGradientBoostingClassifier(
                    learning_rate=0.04,
                    max_iter=180,
                    max_leaf_nodes=7,
                    min_samples_leaf=50,
                    l2_regularization=3.0,
                    random_state=20260917,
                ),
            ),
        ]
    )


def score_metrics(y_true: pd.Series, score: np.ndarray) -> dict[str, float]:
    return {
        "auc": float(roc_auc_score(y_true, score)) if y_true.nunique() > 1 else float("nan"),
        "average_precision": float(average_precision_score(y_true, score)),
        "brier": float(brier_score_loss(y_true, score)),
    }


def attach_sequence_state(k1: pd.DataFrame) -> pd.DataFrame:
    work = k1.sort_values("decision").copy().reset_index(drop=True)
    work["hard_stop_target"] = work["stop_hit"].astype(int)
    work["immediate_nha_loss"] = ((work["L"] == 1) & (work["R"] < 0.0)).astype(int)
    work["short_chop_loss"] = ((work["L"] <= 2) & (work["R"] < 0.0)).astype(int)
    work["prior_outcome_available"] = 0
    work["prev_k1_R"] = np.nan
    work["prev_k1_stop"] = np.nan
    work["prior_short_loss_streak"] = 0
    work["prior_stop_streak"] = 0
    work["prior4_short_loss_rate"] = np.nan
    work["prior4_stop_rate"] = np.nan

    short_streak = 0
    stop_streak = 0
    prior_short: list[int] = []
    prior_stop: list[int] = []
    previous_row: pd.Series | None = None
    previous_rid: int | None = None
    for index, row in work.iterrows():
        rid = int(row["rid"])
        consecutive = previous_rid is not None and rid == previous_rid + 1
        available = (
            consecutive
            and previous_row is not None
            and pd.Timestamp(previous_row["label_available_at"]) <= pd.Timestamp(row["decision"])
        )
        if available and previous_row is not None:
            work.at[index, "prior_outcome_available"] = 1
            work.at[index, "prev_k1_R"] = float(previous_row["R"])
            work.at[index, "prev_k1_stop"] = int(previous_row["stop_hit"])
            work.at[index, "prior_short_loss_streak"] = short_streak
            work.at[index, "prior_stop_streak"] = stop_streak
            if prior_short:
                work.at[index, "prior4_short_loss_rate"] = float(np.mean(prior_short[-4:]))
                work.at[index, "prior4_stop_rate"] = float(np.mean(prior_stop[-4:]))
        else:
            short_streak = 0
            stop_streak = 0
            prior_short = []
            prior_stop = []

        current_short = int(row["short_chop_loss"])
        current_stop = int(row["hard_stop_target"])
        short_streak = short_streak + 1 if current_short else 0
        stop_streak = stop_streak + 1 if current_stop else 0
        prior_short.append(current_short)
        prior_stop.append(current_stop)
        previous_row = row
        previous_rid = rid
    return work


def bridge_weights(
    frame: pd.DataFrame,
    baseline_units: np.ndarray,
    trigger: str,
    minimum_persistence_k: int = 2,
) -> tuple[np.ndarray, pd.DataFrame]:
    work = frame.sort_values("decision").copy()
    units = pd.Series(baseline_units, index=frame.index, dtype=float)
    neutral = False
    audit_rows: list[dict[str, object]] = []
    for rid, group in work.groupby("rid", sort=False):
        indices = group.index
        neutral_before = neutral
        if neutral:
            suppressed_indices = group.index[group["k"] < minimum_persistence_k]
            units.loc[suppressed_indices] = 0.0
        selected = units.loc[indices].to_numpy(dtype=float) > 0.0
        later_admission = bool(
            np.any(selected & group["k"].ge(minimum_persistence_k).to_numpy())
        )
        any_admission = bool(np.any(selected))
        weighted_r = float(
            np.sum(group["R"].to_numpy(dtype=float) * units.loc[indices].to_numpy(dtype=float))
        )
        any_stop = bool(
            np.any(selected & group["stop_hit"].eq(1).to_numpy())
        )
        immediate_loss = bool(
            np.any(
                selected
                & group["k"].eq(1).to_numpy()
                & group["L"].eq(1).to_numpy()
                & group["R"].lt(0.0).to_numpy()
            )
        )
        short_loss = bool(
            np.any(
                selected
                & group["k"].eq(1).to_numpy()
                & group["L"].le(2).to_numpy()
                & group["R"].lt(0.0).to_numpy()
            )
        )
        if trigger == "stop":
            triggered = any_stop
        elif trigger == "immediate_nha_loss":
            triggered = immediate_loss
        elif trigger == "short_chop_loss":
            triggered = short_loss
        elif trigger == "campaign_loss":
            triggered = any_admission and weighted_r < 0.0
        else:
            raise ValueError(f"unsupported bridge trigger: {trigger}")
        if neutral_before and not later_admission:
            neutral = True
        else:
            neutral = triggered
        audit_rows.append(
            {
                "rid": int(rid),
                "start": group["decision"].min(),
                "neutral_before": int(neutral_before),
                "k1_suppressed": int(
                    neutral_before
                    and bool(np.any(group["k"].eq(1).to_numpy() & (baseline_units[indices] > 0.0)))
                ),
                "later_admission": int(later_admission),
                "any_admission": int(any_admission),
                "campaign_R": weighted_r,
                "any_stop": int(any_stop),
                "immediate_nha_loss": int(immediate_loss),
                "short_chop_loss": int(short_loss),
                "neutral_after": int(neutral),
                "trigger": trigger,
                "minimum_persistence_k": int(minimum_persistence_k),
            }
        )
    return units.sort_index().to_numpy(dtype=float), pd.DataFrame(audit_rows)


def paired_run_bootstrap(
    frame: pd.DataFrame,
    baseline_units: np.ndarray,
    candidate_units: np.ndarray,
    iterations: int = 2000,
) -> dict[str, float]:
    run = pd.DataFrame(
        {
            "rid": frame["rid"].to_numpy(),
            "delta_R": frame["R"].to_numpy(dtype=float)
            * (candidate_units - baseline_units),
        }
    ).groupby("rid", as_index=False)["delta_R"].sum()
    values = run["delta_R"].to_numpy(dtype=float)
    if not len(values):
        return {"bootstrap_delta_R_p05": 0.0, "bootstrap_delta_R_p95": 0.0, "bootstrap_p_gt_0": 0.0}
    rng = np.random.default_rng(20260917)
    draws = rng.choice(values, size=(iterations, len(values)), replace=True).sum(axis=1)
    return {
        "bootstrap_delta_R_p05": float(np.quantile(draws, 0.05)),
        "bootstrap_delta_R_p95": float(np.quantile(draws, 0.95)),
        "bootstrap_p_gt_0": float(np.mean(draws > 0.0)),
    }


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    primary_target = args.primary_target
    primary_target_name = next(
        name for name, column in TARGETS.items() if column == primary_target
    )

    universe = pd.read_csv(
        args.universe,
        parse_dates=["decision", "entry_time", "exit_time", "run_end_decision", "label_available_at"],
    )
    policy = pd.read_csv(args.policy_ledger, parse_dates=["decision"])[
        ["decision", "W", "score", "shock_score"]
    ]
    micro = pd.read_csv(args.micro_ledger, parse_dates=["decision", "h4_start"])

    if universe["decision"].duplicated().any():
        raise ValueError("universe decision timestamps are not unique")
    if policy["decision"].duplicated().any():
        raise ValueError("policy decision timestamps are not unique")
    if micro["decision"].duplicated().any():
        raise ValueError("micro decision timestamps are not unique")

    joined = universe.merge(
        micro.drop(columns=["year"]), on="decision", how="left", validate="one_to_one"
    )
    if joined["fast_dir"].isna().any():
        raise ValueError("micro ledger does not cover every universe decision")
    direction_mismatch = int((joined["dir"] != joined["fast_dir"]).sum())
    k_mismatch = int((joined["k"] != joined["run_k"]).sum())
    if direction_mismatch or k_mismatch:
        raise ValueError(f"micro parity mismatch: direction={direction_mismatch}, k={k_mismatch}")

    policy_join_check = policy.merge(
        universe[["decision"]], on="decision", how="left", indicator=True
    )
    if not policy_join_check["_merge"].eq("both").all():
        raise ValueError("policy ledger contains decisions absent from the causal universe")
    joined = joined.merge(policy, on="decision", how="left", validate="one_to_one")
    joined["W"] = joined["W"].fillna(0.0)
    joined = joined.sort_values("decision").reset_index(drop=True)

    k1 = attach_sequence_state(joined[joined["k"] == 1].copy())
    missing_features = sorted(
        set(sum(FEATURE_SETS.values(), [])) - set(k1.columns)
    )
    if missing_features:
        raise ValueError(f"missing required features: {missing_features}")

    model_metrics_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []
    primary_models: dict[str, Pipeline] = {}
    threshold_records: dict[str, dict[str, float]] = {}
    scored_parts: list[pd.DataFrame] = []

    for year in EVAL_YEARS:
        boundary = pd.Timestamp(f"{year}-01-01")
        train = k1[
            (k1["decision"] < boundary)
            & (k1["label_available_at"] < boundary)
        ].copy()
        test = k1[k1["year"] == year].copy()
        if train.empty or test.empty:
            raise ValueError(f"empty chronological split for {year}")

        for target_name, target_column in TARGETS.items():
            for feature_set_name, features in FEATURE_SETS.items():
                model = make_logistic()
                model.fit(train[features], train[target_column])
                score = model.predict_proba(test[features])[:, 1]
                model_metrics_rows.append(
                    {
                        "eval_year": year,
                        "model": "ROBUST_LOGISTIC_C01",
                        "target": target_name,
                        "feature_set": feature_set_name,
                        "train_rows": int(len(train)),
                        "test_rows": int(len(test)),
                        "train_positive_rate": float(train[target_column].mean()),
                        "test_positive_rate": float(test[target_column].mean()),
                        **score_metrics(test[target_column], score),
                    }
                )

                if feature_set_name == PRIMARY_FEATURE_SET:
                    imputer = model.named_steps["imputer"]
                    transformed_names = imputer.get_feature_names_out(features)
                    coefficients = model.named_steps["model"].coef_[0]
                    for name, coefficient in zip(transformed_names, coefficients):
                        coefficient_rows.append(
                            {
                                "eval_year": year,
                                "target": target_name,
                                "feature_set": feature_set_name,
                                "feature": str(name),
                                "coefficient": float(coefficient),
                            }
                        )

                if target_column == primary_target and feature_set_name == PRIMARY_FEATURE_SET:
                    primary_models[str(year)] = model
                    train_score = model.predict_proba(train[features])[:, 1]
                    threshold_records[str(year)] = {
                        f"q{int(quantile * 100):02d}": float(np.quantile(train_score, quantile))
                        for quantile in RISK_QUANTILES
                    }
                    scored = test[[
                        "decision", "year", "rid", "dir", "k", "L", "R", "stop_hit",
                        "immediate_nha_loss", "short_chop_loss", "W",
                    ]].copy()
                    scored["primary_risk"] = score
                    scored_parts.append(scored)

            hist_features = FEATURE_SETS[PRIMARY_FEATURE_SET]
            histgb = make_histgb()
            histgb.fit(train[hist_features], train[target_column])
            hist_score = histgb.predict_proba(test[hist_features])[:, 1]
            model_metrics_rows.append(
                {
                    "eval_year": year,
                    "model": "SHALLOW_HISTGB",
                    "target": target_name,
                    "feature_set": PRIMARY_FEATURE_SET,
                    "train_rows": int(len(train)),
                    "test_rows": int(len(test)),
                    "train_positive_rate": float(train[target_column].mean()),
                    "test_positive_rate": float(test[target_column].mean()),
                    **score_metrics(test[target_column], hist_score),
                }
            )

    scored_k1 = pd.concat(scored_parts, ignore_index=True).sort_values("decision")
    scored_k1.to_csv(
        args.out_dir / "V10_REVERSAL_CHURN_SCORED_K1_2024_2026.csv",
        index=False,
        date_format="%Y-%m-%d %H:%M:%S",
    )
    pd.DataFrame(model_metrics_rows).to_csv(
        args.out_dir / "V10_REVERSAL_CHURN_MODEL_METRICS.csv", index=False
    )
    pd.DataFrame(coefficient_rows).to_csv(
        args.out_dir / "V10_REVERSAL_CHURN_LOGISTIC_COEFFICIENTS.csv", index=False
    )
    joblib.dump(
        primary_models,
        args.out_dir / "V10_REVERSAL_CHURN_PRIMARY_MODELS.joblib",
    )

    analysis = joined[joined["year"].isin(EVAL_YEARS)].copy().reset_index(drop=True)
    baseline_units = analysis["W"].to_numpy(dtype=float)
    score_map = scored_k1.set_index("decision")["primary_risk"]
    analysis["primary_risk"] = analysis["decision"].map(score_map)

    policies: dict[str, np.ndarray] = {"BASELINE": baseline_units.copy()}
    for quantile in RISK_QUANTILES:
        name = f"MODEL_NEUTRAL_Q{int(quantile * 100):02d}"
        candidate = baseline_units.copy()
        reject = np.zeros(len(analysis), dtype=bool)
        for year in EVAL_YEARS:
            threshold = threshold_records[str(year)][f"q{int(quantile * 100):02d}"]
            reject |= (
                analysis["year"].eq(year).to_numpy()
                & analysis["k"].eq(1).to_numpy()
                & analysis["primary_risk"].ge(threshold).fillna(False).to_numpy()
            )
        candidate[reject] = 0.0
        policies[name] = candidate

    no_k1 = baseline_units.copy()
    no_k1[analysis["k"].eq(1).to_numpy()] = 0.0
    policies["DIAGNOSTIC_NO_K1"] = no_k1

    oracle_short = baseline_units.copy()
    oracle_short[
        analysis["k"].eq(1).to_numpy()
        & analysis["L"].le(2).to_numpy()
        & analysis["R"].lt(0.0).to_numpy()
    ] = 0.0
    policies["ORACLE_REMOVE_SHORT_CHOP_LOSS_K1"] = oracle_short

    oracle_stop = baseline_units.copy()
    oracle_stop[
        analysis["k"].eq(1).to_numpy()
        & analysis["stop_hit"].eq(1).to_numpy()
    ] = 0.0
    policies["ORACLE_REMOVE_K1_HARD_STOP"] = oracle_stop

    bridge_audits: list[pd.DataFrame] = []
    for trigger_name, policy_label in (
        ("stop", "STOP"),
        ("immediate_nha_loss", "IMMEDIATE_NHA_LOSS"),
        ("short_chop_loss", "SHORT_CHOP_LOSS"),
        ("campaign_loss", "CAMPAIGN_LOSS"),
    ):
        for minimum_k in (2, 3):
            bridge, bridge_audit = bridge_weights(
                analysis,
                baseline_units,
                trigger_name,
                minimum_persistence_k=minimum_k,
            )
            policies[f"PERSISTENCE_BRIDGE_AFTER_{policy_label}_K{minimum_k}"] = bridge
            bridge_audits.append(bridge_audit)
    pd.concat(bridge_audits, ignore_index=True).to_csv(
        args.out_dir / "V10_REVERSAL_CHURN_BRIDGE_STATE_LEDGER.csv",
        index=False,
        date_format="%Y-%m-%d %H:%M:%S",
    )

    policy_rows: list[dict[str, object]] = []
    bootstrap_rows: list[dict[str, object]] = []
    for period, mask in [
        *((str(year), analysis["year"].eq(year).to_numpy()) for year in EVAL_YEARS),
        ("POOLED_2024_2026", np.ones(len(analysis), dtype=bool)),
    ]:
        subset = analysis.loc[mask].copy().reset_index(drop=True)
        baseline_subset = baseline_units[mask]
        for policy_name, policy_units in policies.items():
            units_subset = policy_units[mask]
            policy_rows.append(
                policy_metrics(
                    subset,
                    units_subset,
                    policy_name,
                    period,
                    baseline_subset,
                )
            )
            if policy_name != "BASELINE":
                bootstrap_rows.append(
                    {
                        "period": period,
                        "policy": policy_name,
                        "observed_delta_R": float(
                            np.sum(
                                subset["R"].to_numpy(dtype=float)
                                * (units_subset - baseline_subset)
                            )
                        ),
                        **paired_run_bootstrap(
                            subset, baseline_subset, units_subset
                        ),
                    }
                )

    policy_frame = pd.DataFrame(policy_rows)
    policy_frame.to_csv(
        args.out_dir / "V10_REVERSAL_CHURN_POLICY_FRONTIER.csv", index=False
    )
    pd.DataFrame(bootstrap_rows).to_csv(
        args.out_dir / "V10_REVERSAL_CHURN_POLICY_BOOTSTRAP.csv", index=False
    )

    # Pooled feature contrasts and quantile response curves are descriptive only.
    selected_k1 = k1[(k1["year"].isin(EVAL_YEARS)) & (k1["W"] > 0.0)].copy()
    effect_rows: list[dict[str, object]] = []
    for feature in FEATURE_SETS[PRIMARY_FEATURE_SET]:
        values = pd.to_numeric(selected_k1[feature], errors="coerce")
        standard_deviation = float(values.std())
        for target in ("short_chop_loss", "hard_stop_target", "immediate_nha_loss"):
            positive = selected_k1[target].eq(1)
            effect_rows.append(
                {
                    "feature": feature,
                    "target": target,
                    "rows": int(values.notna().sum()),
                    "standardized_mean_difference": (
                        float((values[positive].mean() - values[~positive].mean()) / standard_deviation)
                        if standard_deviation > 1e-12
                        else 0.0
                    ),
                    "positive_median": float(values[positive].median()),
                    "negative_median": float(values[~positive].median()),
                }
            )
    effects = pd.DataFrame(effect_rows)
    effects.to_csv(args.out_dir / "V10_REVERSAL_CHURN_FEATURE_EFFECTS.csv", index=False)

    primary_effects = (
        effects[effects["target"].eq(primary_target)]
        .assign(abs_effect=lambda frame: frame["standardized_mean_difference"].abs())
        .sort_values("abs_effect", ascending=False)
        .head(12)
    )
    quantile_rows: list[dict[str, object]] = []
    for feature in primary_effects["feature"]:
        usable = selected_k1.dropna(subset=[feature]).copy()
        try:
            usable["quintile"] = pd.qcut(usable[feature], 5, duplicates="drop")
        except ValueError:
            continue
        for quintile, group in usable.groupby("quintile", observed=True):
            quantile_rows.append(
                {
                    "feature": feature,
                    "quintile": str(quintile),
                    "rows": int(len(group)),
                    "feature_median": float(group[feature].median()),
                    "short_chop_loss_rate": float(group["short_chop_loss"].mean()),
                    "hard_stop_rate": float(group["hard_stop_target"].mean()),
                    "immediate_nha_loss_rate": float(group["immediate_nha_loss"].mean()),
                    "weighted_R": float(np.sum(group["R"] * group["W"])),
                }
            )
    pd.DataFrame(quantile_rows).to_csv(
        args.out_dir / "V10_REVERSAL_CHURN_FEATURE_QUINTILES.csv", index=False
    )

    baseline_pooled = policy_frame[
        policy_frame["period"].eq("POOLED_2024_2026")
        & policy_frame["policy"].eq("BASELINE")
    ].iloc[0]
    validation = {
        "ok": True,
        "status": "consumed-data shadow diagnostic; no strategy authority",
        "source_rows": {
            "universe": int(len(universe)),
            "policy": int(len(policy)),
            "micro": int(len(micro)),
            "joined": int(len(joined)),
            "selected_2024_2026": int((analysis["W"] > 0.0).sum()),
            "selected_k1_2024_2026": int(((analysis["W"] > 0.0) & (analysis["k"] == 1)).sum()),
        },
        "parity": {
            "micro_universe_matches": int(joined["fast_dir"].notna().sum()),
            "direction_mismatch": direction_mismatch,
            "k_mismatch": k_mismatch,
            "policy_decisions_matched": int(len(policy_join_check)),
        },
        "causality": {
            "feature_clock": "raw M1 single-pass ledgers; completed bars only",
            "outer_splits": "2024 <- answers available before 2024; 2025 <- before 2025; 2026 <- before 2026",
            "thresholds": "quantiles estimated from each outer split's prior-only training scores",
            "future_only_policies": [
                "ORACLE_REMOVE_SHORT_CHOP_LOSS_K1",
                "ORACLE_REMOVE_K1_HARD_STOP",
            ],
        },
        "primary_model": {
            "target": primary_target,
            "target_name": primary_target_name,
            "feature_set": PRIMARY_FEATURE_SET,
            "model": "median imputation + RobustScaler(10,90) + LogisticRegression C=0.1",
            "thresholds": threshold_records,
        },
        "baseline": {
            key: (
                int(baseline_pooled[key])
                if key in {"entries", "hard_stop_rows", "k1_stop_rows", "max_loss_streak", "max_stop_streak"}
                else float(baseline_pooled[key])
            )
            for key in (
                "entries", "units", "R", "pf_R", "dd_R", "hard_stop_rows",
                "k1_stop_rows", "max_loss_streak", "max_stop_streak",
            )
        },
        "same_m1_ambiguity": int(
            (
                analysis["same_m1_exit_stop_ambiguous"].eq(1)
                & analysis["W"].gt(0.0)
            ).sum()
        ),
    }
    (args.out_dir / "V10_REVERSAL_CHURN_VALIDATION.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    (args.out_dir / "V10_REVERSAL_CHURN_MODEL_SPEC.json").write_text(
        json.dumps(
            {
                "status": "shadow research only",
                "primary_target": primary_target,
                "primary_target_name": primary_target_name,
                "primary_feature_set": PRIMARY_FEATURE_SET,
                "features": FEATURE_SETS[PRIMARY_FEATURE_SET],
                "risk_quantiles": RISK_QUANTILES,
                "thresholds": threshold_records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(json.dumps(validation, indent=2))
    print("\nPRIMARY MODEL METRICS")
    metrics = pd.DataFrame(model_metrics_rows)
    print(
        metrics[
            metrics["target"].eq(primary_target_name)
            & metrics["feature_set"].eq(PRIMARY_FEATURE_SET)
        ][["eval_year", "model", "auc", "average_precision", "brier"]].to_string(index=False)
    )
    print("\nPOOLED POLICY FRONTIER")
    print(
        policy_frame[policy_frame["period"].eq("POOLED_2024_2026")][
            [
                "policy", "entries", "R", "pf_R", "dd_R", "hard_stop_rows",
                "k1_stop_rows", "hard_stop_recall_removed", "max_loss_streak",
                "max_stop_streak", "l6_positive_pnl_retention",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
