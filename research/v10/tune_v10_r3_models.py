"""Nested chronological V10 R3 model/preprocessing tournament.

R3 keeps the V10 semantic layers separate:

* REGIME: is the newly forming FAST run trendable rather than short/choppy?
* DIRECTION: is the current FAST direction likely to persist one more H4 bar?
* RUNWAY: is the current Child still in the future early-third answer sheet?
* SEVERE: is the admitted Child exposed to a severe structural-R outcome?

Each head owns a compact feature family and independently selects preprocessing,
model family, regularisation and run weighting using expanding half-year folds.
Outer 2024/2025/2026 results are strictly walk-forward: rows whose label resolves
on or after the evaluation boundary are purged from training.

The script is research-only.  It writes all selection scores, per-event scores,
policy actions and validation receipts; no threshold or model is promoted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, SplineTransformer, StandardScaler


RANDOM_STATE = 20260917


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tune and evaluate V10 R3 causal ML heads.")
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--r2-ledger", type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


REGIME_FEATURES = [
    "adx28_rel",
    "adx28_delta3_rel",
    "path_eff4_rel",
    "path_eff12_rel",
    "path_eff4_delta",
    "flip4",
    "flip8",
    "flip12",
    "prev_run_len",
    "prev4_run_mean",
    "prev4_run_std",
    "prev4_short_rate",
]

DIRECTION_FEATURES = [
    "fast_body_rng",
    "fast_body_delta",
    "std_align",
    "std_body_rng",
    "slow_align",
    "slow_body_rng",
    "di14_signed",
    "ema8_21_signed",
    "ema8_slope",
    "ltf_align_mean",
    "ltf_align_std",
    "direction_vote",
    "m15_body_rng",
    "m30_body_rng",
    "h1_body_rng",
]

RUNWAY_FEATURES = [
    "k",
    "stop_dist_atr",
    "fast_body_rng",
    "fast_body_delta",
    "std_align",
    "std_body_rng",
    "slow_align",
    "adx28_rel",
    "path_eff4_rel",
    "path_eff12_rel",
    "flip8",
    "prev_run_len",
    "prev4_short_rate",
    "di14_signed",
    "ema8_21_signed",
    "ltf_align_mean",
    "ltf_align_std",
    "direction_vote",
]

SEVERE_FEATURES = [
    "k",
    "stop_dist_atr",
    "fast_body_rng",
    "fast_body_delta",
    "std_align",
    "std_body_rng",
    "slow_align",
    "slow_body_rng",
    "adx28_rel",
    "adx28_delta3_rel",
    "path_eff4_rel",
    "path_eff12_rel",
    "flip8",
    "prev_run_len",
    "prev4_short_rate",
    "di14_signed",
    "ema8_21_signed",
    "ltf_align_mean",
    "direction_vote",
]

BINARY_FEATURES = {"std_align", "slow_align"}


@dataclass(frozen=True)
class Head:
    name: str
    target: str
    features: tuple[str, ...]
    population: str


HEADS = [
    Head("REGIME", "trendable3", tuple(REGIME_FEATURES), "K1"),
    Head("DIRECTION", "next_same", tuple(DIRECTION_FEATURES), "ALL"),
    Head("RUNWAY", "early3", tuple(RUNWAY_FEATURES), "ALL"),
    Head("SEVERE", "severe", tuple(SEVERE_FEATURES), "UNAMBIGUOUS"),
]


@dataclass(frozen=True)
class ModelSpec:
    family: str
    weight_mode: str
    C: float | None = None
    n_knots: int | None = None
    learning_rate: float | None = None
    max_iter: int | None = None
    max_leaf_nodes: int | None = None
    min_samples_leaf: int | None = None
    l2_regularization: float | None = None

    @property
    def spec_id(self) -> str:
        values = [self.family, self.weight_mode]
        for key, value in asdict(self).items():
            if key in {"family", "weight_mode"} or value is None:
                continue
            values.append(f"{key}={value}")
        return "|".join(values)


def candidate_specs(head: Head) -> list[ModelSpec]:
    specs: list[ModelSpec] = []
    for weight in ("decision", "run_sqrt"):
        for c_value in (0.02, 0.1, 0.5, 2.0):
            specs.append(ModelSpec("standard_logit", weight, C=c_value))
        for c_value in (0.02, 0.1, 0.5):
            specs.append(ModelSpec("robust_logit", weight, C=c_value))
        for knots in (3, 4):
            for c_value in (0.02, 0.1):
                specs.append(ModelSpec("spline_logit", weight, C=c_value, n_knots=knots))
        for config in (
            (0.03, 240, 7, 40, 1.0),
            (0.05, 180, 7, 70, 3.0),
            (0.03, 240, 15, 70, 5.0),
            (0.05, 180, 15, 110, 8.0),
        ):
            specs.append(
                ModelSpec(
                    "histgb",
                    weight,
                    learning_rate=config[0],
                    max_iter=config[1],
                    max_leaf_nodes=config[2],
                    min_samples_leaf=config[3],
                    l2_regularization=config[4],
                )
            )
    if head.name in {"REGIME", "RUNWAY"}:
        # Purpose-specific objective: give long-run opportunity and severe loss
        # examples more influence without changing the causal feature vector.
        specs.extend(
            [
                ModelSpec("robust_logit", "tail_utility", C=0.1),
                ModelSpec("spline_logit", "tail_utility", C=0.1, n_knots=3),
                ModelSpec(
                    "histgb",
                    "tail_utility",
                    learning_rate=0.03,
                    max_iter=240,
                    max_leaf_nodes=7,
                    min_samples_leaf=70,
                    l2_regularization=3.0,
                ),
            ]
        )
    return specs


def population_mask(frame: pd.DataFrame, head: Head) -> pd.Series:
    if head.population == "K1":
        return frame["k"].eq(1)
    if head.population == "UNAMBIGUOUS":
        return frame["same_m1_exit_stop_ambiguous"].eq(0)
    return pd.Series(True, index=frame.index)


def sample_weights(frame: pd.DataFrame, target: str, mode: str) -> np.ndarray:
    weights = np.ones(len(frame), dtype=float)
    if mode in {"run_sqrt", "tail_utility"}:
        counts = frame.groupby("rid")["rid"].transform("size").to_numpy(dtype=float)
        weights /= np.sqrt(np.maximum(counts, 1.0))
    if mode == "tail_utility":
        labels = frame[target].to_numpy(dtype=int)
        long_tail = 1.0 + np.minimum(frame["L"].to_numpy(dtype=float), 12.0) / 12.0
        loss_tail = 1.0 + np.minimum(np.maximum(-frame["R"].to_numpy(dtype=float), 0.0), 1.0)
        weights *= np.where(labels == 1, long_tail, loss_tail)
    return weights / max(float(np.mean(weights)), 1e-12)


def build_model(spec: ModelSpec, features: tuple[str, ...]) -> Pipeline:
    if spec.family == "standard_logit":
        prep = StandardScaler()
        model = LogisticRegression(C=float(spec.C), max_iter=5000, random_state=RANDOM_STATE)
    elif spec.family == "robust_logit":
        prep = RobustScaler(quantile_range=(10.0, 90.0))
        model = LogisticRegression(C=float(spec.C), max_iter=5000, random_state=RANDOM_STATE)
    elif spec.family == "spline_logit":
        continuous = [x for x in features if x not in BINARY_FEATURES]
        binary = [x for x in features if x in BINARY_FEATURES]
        prep = ColumnTransformer(
            [
                (
                    "smooth",
                    SplineTransformer(
                        n_knots=int(spec.n_knots),
                        degree=2,
                        knots="quantile",
                        extrapolation="constant",
                        include_bias=False,
                    ),
                    continuous,
                ),
                ("binary", "passthrough", binary),
            ],
            remainder="drop",
            verbose_feature_names_out=False,
        )
        model = LogisticRegression(C=float(spec.C), max_iter=5000, random_state=RANDOM_STATE)
    elif spec.family == "histgb":
        prep = "passthrough"
        model = HistGradientBoostingClassifier(
            loss="log_loss",
            learning_rate=float(spec.learning_rate),
            max_iter=int(spec.max_iter),
            max_leaf_nodes=int(spec.max_leaf_nodes),
            min_samples_leaf=int(spec.min_samples_leaf),
            l2_regularization=float(spec.l2_regularization),
            early_stopping=False,
            random_state=RANDOM_STATE,
        )
    else:
        raise ValueError(spec.family)
    return Pipeline([("prep", prep), ("model", model)])


def fit_model(model: Pipeline, frame: pd.DataFrame, head: Head, spec: ModelSpec) -> Pipeline:
    weights = sample_weights(frame, head.target, spec.weight_mode)
    model.fit(
        frame[list(head.features)],
        frame[head.target].astype(int),
        model__sample_weight=weights,
    )
    return model


def half_year_boundaries(frame: pd.DataFrame) -> list[pd.Timestamp]:
    start_year = int(frame["decision"].dt.year.min())
    end = frame["decision"].max()
    boundaries: list[pd.Timestamp] = []
    for year in range(start_year, int(end.year) + 1):
        for month in (1, 7):
            value = pd.Timestamp(year=year, month=month, day=1)
            if value <= end:
                boundaries.append(value)
    return sorted(boundaries)


def inner_folds(
    frame: pd.DataFrame,
    head: Head,
    max_folds: int = 4,
    min_train: int = 180,
    min_valid: int = 80,
) -> list[tuple[pd.Index, pd.Index, str]]:
    boundaries = half_year_boundaries(frame)
    folds: list[tuple[pd.Index, pd.Index, str]] = []
    mask_head = population_mask(frame, head)
    for pos in range(1, len(boundaries)):
        start = boundaries[pos]
        end = boundaries[pos + 1] if pos + 1 < len(boundaries) else frame["decision"].max() + pd.Timedelta(seconds=1)
        train_mask = (
            (frame["decision"] < start)
            & (frame["label_available_at"] < start)
            & mask_head
        )
        valid_mask = (
            (frame["decision"] >= start)
            & (frame["decision"] < end)
            & mask_head
        )
        train_idx = frame.index[train_mask]
        valid_idx = frame.index[valid_mask]
        if len(train_idx) < min_train or len(valid_idx) < min_valid:
            continue
        if frame.loc[train_idx, head.target].nunique() < 2 or frame.loc[valid_idx, head.target].nunique() < 2:
            continue
        folds.append((train_idx, valid_idx, f"{start:%YH}{1 if start.month == 1 else 2}"))
    return folds[-max_folds:]


def safe_metrics(y: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    probability = np.clip(np.asarray(probability, dtype=float), 1e-6, 1.0 - 1e-6)
    y = np.asarray(y, dtype=int)
    return {
        "auc": float(roc_auc_score(y, probability)) if len(np.unique(y)) > 1 else float("nan"),
        "logloss": float(log_loss(y, probability, labels=[0, 1])),
        "brier": float(brier_score_loss(y, probability)),
    }


def expected_calibration_error(y: np.ndarray, probability: np.ndarray, bins: int = 10) -> float:
    work = pd.DataFrame({"y": y, "p": probability})
    try:
        work["bin"] = pd.qcut(work["p"], q=min(bins, work["p"].nunique()), duplicates="drop")
    except ValueError:
        return float("nan")
    total = len(work)
    return float(
        sum(len(group) / total * abs(group["y"].mean() - group["p"].mean()) for _, group in work.groupby("bin", observed=True))
    )


def evaluate_spec(
    frame: pd.DataFrame,
    head: Head,
    spec: ModelSpec,
    folds: list[tuple[pd.Index, pd.Index, str]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    all_y: list[np.ndarray] = []
    all_p: list[np.ndarray] = []
    fold_rows: list[dict[str, object]] = []
    for train_idx, valid_idx, fold_name in folds:
        train = frame.loc[train_idx]
        valid = frame.loc[valid_idx]
        model = fit_model(build_model(spec, head.features), train, head, spec)
        probability = model.predict_proba(valid[list(head.features)])[:, 1]
        metrics = safe_metrics(valid[head.target].to_numpy(), probability)
        fold_rows.append(
            {
                "head": head.name,
                "spec_id": spec.spec_id,
                "fold": fold_name,
                "train_n": len(train),
                "valid_n": len(valid),
                **metrics,
            }
        )
        all_y.append(valid[head.target].to_numpy(dtype=int))
        all_p.append(probability)
    metrics = safe_metrics(np.concatenate(all_y), np.concatenate(all_p))
    return {
        "head": head.name,
        "spec_id": spec.spec_id,
        "family": spec.family,
        "weight_mode": spec.weight_mode,
        "folds": len(folds),
        "eval_n": int(sum(len(x) for x in all_y)),
        **metrics,
    }, fold_rows


@dataclass
class Platt:
    slope: float = 1.0
    intercept: float = 0.0

    def apply(self, probability: np.ndarray) -> np.ndarray:
        p = np.clip(np.asarray(probability, dtype=float), 1e-6, 1.0 - 1e-6)
        logits = np.log(p / (1.0 - p))
        z = np.clip(self.slope * logits + self.intercept, -35.0, 35.0)
        return 1.0 / (1.0 + np.exp(-z))


def fit_platt(y: np.ndarray, probability: np.ndarray) -> Platt:
    p = np.clip(np.asarray(probability, dtype=float), 1e-6, 1.0 - 1e-6)
    logits = np.log(p / (1.0 - p)).reshape(-1, 1)
    model = LogisticRegression(C=1000.0, max_iter=5000, random_state=RANDOM_STATE)
    model.fit(logits, np.asarray(y, dtype=int))
    return Platt(float(model.coef_[0, 0]), float(model.intercept_[0]))


def selected_oof_and_test(
    frame: pd.DataFrame,
    outer_train: pd.DataFrame,
    outer_test: pd.DataFrame,
    head: Head,
    spec: ModelSpec,
    folds: list[tuple[pd.Index, pd.Index, str]],
) -> tuple[pd.Series, np.ndarray, Pipeline, Platt]:
    raw_oof = pd.Series(np.nan, index=outer_train.index, dtype=float)
    target_oof_idx: list[int] = []
    target_oof_y: list[int] = []
    target_oof_p: list[float] = []
    for train_idx, valid_idx, _ in folds:
        train = frame.loc[train_idx]
        valid_all = frame.loc[valid_idx.min() : valid_idx.max()]
        # Keep the exact chronological validation window, including rows outside
        # the head's fitting population, so every semantic head can score the
        # same policy rows without training on them.
        start = frame.loc[valid_idx, "decision"].min()
        end = frame.loc[valid_idx, "decision"].max()
        valid_all = outer_train[(outer_train["decision"] >= start) & (outer_train["decision"] <= end)]
        model = fit_model(build_model(spec, head.features), train, head, spec)
        prediction = model.predict_proba(valid_all[list(head.features)])[:, 1]
        raw_oof.loc[valid_all.index] = prediction
        target_valid = valid_all[population_mask(valid_all, head)]
        if len(target_valid):
            target_prediction = raw_oof.loc[target_valid.index].to_numpy(dtype=float)
            target_oof_idx.extend(target_valid.index.tolist())
            target_oof_y.extend(target_valid[head.target].astype(int).tolist())
            target_oof_p.extend(target_prediction.tolist())
    platt = fit_platt(np.asarray(target_oof_y), np.asarray(target_oof_p))
    calibrated_oof = pd.Series(np.nan, index=raw_oof.index, dtype=float)
    available = raw_oof.notna()
    calibrated_oof.loc[available] = platt.apply(raw_oof.loc[available].to_numpy())

    train_population = outer_train[population_mask(outer_train, head)]
    final_model = fit_model(build_model(spec, head.features), train_population, head, spec)
    raw_test = final_model.predict_proba(outer_test[list(head.features)])[:, 1]
    return calibrated_oof, platt.apply(raw_test), final_model, platt


def tier_weights(score: np.ndarray, q50: float, q75: float) -> np.ndarray:
    score = np.asarray(score, dtype=float)
    return np.where(score < q50, 0.0, np.where(score < q75, 1.0, 3.0))


def neutral_weights(
    frame: pd.DataFrame,
    tier: np.ndarray,
    admission_score: np.ndarray,
    admission_q50: float,
) -> np.ndarray:
    result = np.zeros(len(frame), dtype=float)
    work = frame[["rid", "k", "decision"]].copy()
    work["position"] = np.arange(len(frame))
    work["tier"] = tier
    work["admission"] = admission_score
    for _, group in work.sort_values(["rid", "k", "decision"]).groupby("rid", sort=False):
        admitted = False
        for row in group.itertuples(index=False):
            if not admitted and row.admission >= admission_q50:
                admitted = True
            if admitted:
                result[int(row.position)] = float(row.tier)
    return result


def apply_campaign_cap(frame: pd.DataFrame, desired: np.ndarray, cap: float) -> np.ndarray:
    allocated = np.zeros(len(frame), dtype=float)
    work = frame[["rid", "entry_time", "exit_time"]].copy()
    work["position"] = np.arange(len(frame))
    work["desired"] = desired
    for _, group in work.sort_values(["rid", "entry_time"]).groupby("rid", sort=False):
        live: list[tuple[pd.Timestamp, float]] = []
        for row in group.itertuples(index=False):
            live = [(end, units) for end, units in live if end > row.entry_time]
            committed = sum(units for _, units in live)
            units = max(0.0, min(float(row.desired), cap - committed))
            allocated[int(row.position)] = units
            if units > 0.0:
                live.append((row.exit_time, units))
    return allocated


def max_committed(frame: pd.DataFrame, units: np.ndarray) -> float:
    events: list[tuple[pd.Timestamp, int, float]] = []
    for row, value in zip(frame.itertuples(index=False), units):
        if value <= 0.0:
            continue
        events.append((row.entry_time, 1, float(value)))
        events.append((row.exit_time, 0, -float(value)))
    current = maximum = 0.0
    for _, _, delta in sorted(events, key=lambda x: (x[0], x[1])):  # exits before entries
        current += delta
        maximum = max(maximum, current)
    return maximum


def drawdown(values: pd.Series, times: pd.Series) -> float:
    order = pd.DataFrame(
        {
            "value": np.asarray(values, dtype=float),
            "time": np.asarray(times),
        }
    ).sort_values("time")
    curve = order["value"].cumsum().to_numpy(dtype=float)
    if not len(curve):
        return 0.0
    peaks = np.maximum.accumulate(np.concatenate([[0.0], curve]))[1:]
    return float(np.max(peaks - curve))


def policy_metrics(frame: pd.DataFrame, units: np.ndarray, policy: str, year: str) -> dict[str, object]:
    selected = units > 0.0
    weighted_pnl = units * frame["pnl"].to_numpy(dtype=float)
    weighted_r = units * frame["R"].to_numpy(dtype=float)
    gross_profit = float(weighted_pnl[weighted_pnl > 0.0].sum())
    gross_loss = float(weighted_pnl[weighted_pnl < 0.0].sum())
    gross_r_profit = float(weighted_r[weighted_r > 0.0].sum())
    gross_r_loss = float(weighted_r[weighted_r < 0.0].sum())
    positives = np.sort(weighted_pnl[weighted_pnl > 0.0])[::-1]
    true_oracle = frame["early3"].eq(1).to_numpy()
    selected_positive_l6 = selected & frame["L"].ge(6).to_numpy() & frame["pnl"].gt(0).to_numpy()
    all_positive_l6 = frame["L"].ge(6).to_numpy() & frame["pnl"].gt(0).to_numpy()
    return {
        "year": year,
        "policy": policy,
        "rows": len(frame),
        "entries": int(selected.sum()),
        "units": float(units.sum()),
        "pnl": float(weighted_pnl.sum()),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pf": gross_profit / -gross_loss if gross_loss < 0.0 else float("inf"),
        "R": float(weighted_r.sum()),
        "pf_R": gross_r_profit / -gross_r_loss if gross_r_loss < 0.0 else float("inf"),
        "dd_pnl": drawdown(pd.Series(weighted_pnl), frame["exit_time"]),
        "dd_R": drawdown(pd.Series(weighted_r), frame["exit_time"]),
        "oracle_recall": float((selected & true_oracle).sum() / max(true_oracle.sum(), 1)),
        "oracle_precision": float(true_oracle[selected].mean()) if selected.any() else float("nan"),
        "weighted_position_hours": float((units * frame["position_hours"].to_numpy(dtype=float)).sum()),
        "max_single_units": float(units.max()) if len(units) else 0.0,
        "max_committed_units": max_committed(frame, units),
        "top1_winner_share": float(positives[:1].sum() / positives.sum()) if positives.sum() > 0 else float("nan"),
        "top5_winner_share": float(positives[:5].sum() / positives.sum()) if positives.sum() > 0 else float("nan"),
        "top10_winner_share": float(positives[:10].sum() / positives.sum()) if positives.sum() > 0 else float("nan"),
        "l6_positive_child_retention": float(frame.loc[selected_positive_l6, "pnl"].sum() / frame.loc[all_positive_l6, "pnl"].sum()) if frame.loc[all_positive_l6, "pnl"].sum() > 0 else float("nan"),
        "ambiguous_selected": int((selected & frame["same_m1_exit_stop_ambiguous"].eq(1).to_numpy()).sum()),
    }


def right_tail_rows(frame: pd.DataFrame, units: np.ndarray, policy: str, year: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    buckets = [(1, 2, "L1-2"), (3, 5, "L3-5"), (6, 8, "L6-8"), (9, 11, "L9-11"), (12, 10**9, "L12+")]
    for lower, upper, name in buckets:
        mask = frame["L"].between(lower, upper).to_numpy()
        selected = mask & (units > 0.0)
        result.append(
            {
                "year": year,
                "policy": policy,
                "run_length_bucket": name,
                "population_rows": int(mask.sum()),
                "selected_rows": int(selected.sum()),
                "units": float(units[mask].sum()),
                "pnl": float((units[mask] * frame.loc[mask, "pnl"].to_numpy(dtype=float)).sum()),
                "R": float((units[mask] * frame.loc[mask, "R"].to_numpy(dtype=float)).sum()),
            }
        )
    return result


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(
        args.universe,
        parse_dates=["decision", "entry_time", "exit_time", "run_end_decision", "label_available_at"],
    ).sort_values("decision").reset_index(drop=True)
    required = sorted({x for head in HEADS for x in head.features} | {head.target for head in HEADS})
    missing = [x for x in required if x not in frame.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    if frame[required].isna().any().any():
        raise ValueError("model inputs or targets contain missing values")

    r2_weights: dict[pd.Timestamp, float] = {}
    if args.r2_ledger:
        r2 = pd.read_csv(args.r2_ledger, parse_dates=["decision"])
        r2_weights = dict(zip(r2["decision"], r2["W"].astype(float)))

    selection_rows: list[dict[str, object]] = []
    fold_rows: list[dict[str, object]] = []
    head_metric_rows: list[dict[str, object]] = []
    score_ledgers: list[pd.DataFrame] = []
    policy_rows: list[dict[str, object]] = []
    right_tail: list[dict[str, object]] = []
    model_bundle: dict[str, object] = {"heads": {}, "source_sha256": sha256_file(args.universe)}

    for outer_year in (2024, 2025, 2026):
        boundary = pd.Timestamp(year=outer_year, month=1, day=1)
        outer_train = frame[
            (frame["decision"] < boundary) & (frame["label_available_at"] < boundary)
        ].copy()
        outer_test = frame[frame["year"].eq(outer_year)].copy()
        model_bundle["heads"][str(outer_year)] = {}
        oof_probabilities: dict[str, pd.Series] = {}
        test_probabilities: dict[str, np.ndarray] = {}

        for head in HEADS:
            folds = inner_folds(outer_train, head)
            if len(folds) < 2:
                raise RuntimeError(f"insufficient inner folds for {outer_year} {head.name}")
            head_candidates: list[dict[str, object]] = []
            for spec in candidate_specs(head):
                aggregate, details = evaluate_spec(frame, head, spec, folds)
                aggregate["outer_year"] = outer_year
                head_candidates.append(aggregate)
                fold_rows.extend({**row, "outer_year": outer_year} for row in details)
            ranked = sorted(
                head_candidates,
                key=lambda row: (row["logloss"], row["brier"], -row["auc"]),
            )
            selected = ranked[0]
            for row in head_candidates:
                row["selected"] = int(row["spec_id"] == selected["spec_id"])
                selection_rows.append(row)
            selected_spec = next(spec for spec in candidate_specs(head) if spec.spec_id == selected["spec_id"])
            oof, test_probability, final_model, platt = selected_oof_and_test(
                frame, outer_train, outer_test, head, selected_spec, folds
            )
            oof_probabilities[head.name] = oof
            test_probabilities[head.name] = test_probability
            test_population = outer_test[population_mask(outer_test, head)]
            test_indices = np.flatnonzero(population_mask(outer_test, head).to_numpy())
            metrics = safe_metrics(
                test_population[head.target].to_numpy(dtype=int),
                test_probability[test_indices],
            )
            metrics["ece10"] = expected_calibration_error(
                test_population[head.target].to_numpy(dtype=int),
                test_probability[test_indices],
            )
            head_metric_rows.append(
                {
                    "outer_year": outer_year,
                    "head": head.name,
                    "target": head.target,
                    "population": head.population,
                    "features": len(head.features),
                    "train_n": int(population_mask(outer_train, head).sum()),
                    "test_n": len(test_population),
                    "selected_spec": selected_spec.spec_id,
                    "platt_slope": platt.slope,
                    "platt_intercept": platt.intercept,
                    **metrics,
                }
            )
            model_bundle["heads"][str(outer_year)][head.name] = {
                "features": list(head.features),
                "target": head.target,
                "population": head.population,
                "spec": asdict(selected_spec),
                "platt": asdict(platt),
                "model": final_model,
            }

        oof_common = outer_train.index
        for values in oof_probabilities.values():
            oof_common = oof_common.intersection(values.index[values.notna()])
        if len(oof_common) < 300:
            raise RuntimeError(f"too few common OOF rows for {outer_year}: {len(oof_common)}")
        oof_k = outer_train.loc[oof_common, "k"].to_numpy(dtype=int)
        oof_regime = oof_probabilities["REGIME"].loc[oof_common].to_numpy()
        oof_direction = oof_probabilities["DIRECTION"].loc[oof_common].to_numpy()
        oof_runway = oof_probabilities["RUNWAY"].loc[oof_common].to_numpy()
        oof_severe = oof_probabilities["SEVERE"].loc[oof_common].to_numpy()
        oof_runway_persist = oof_runway * np.where(oof_k >= 2, oof_direction, 1.0)
        oof_layered = oof_runway * oof_direction * (1.0 - oof_severe)
        oof_admission = oof_regime * oof_direction * (1.0 - oof_severe)
        thresholds = {
            "runway_persist_q50": float(np.quantile(oof_runway_persist, 0.50)),
            "runway_persist_q75": float(np.quantile(oof_runway_persist, 0.75)),
            "layered_q50": float(np.quantile(oof_layered, 0.50)),
            "layered_q75": float(np.quantile(oof_layered, 0.75)),
            "admission_q50": float(
                np.quantile(oof_admission[outer_train.loc[oof_common, "k"].eq(1).to_numpy()], 0.50)
            ),
        }
        model_bundle["heads"][str(outer_year)]["thresholds"] = thresholds

        test_k = outer_test["k"].to_numpy(dtype=int)
        test_runway_persist = test_probabilities["RUNWAY"] * np.where(
            test_k >= 2, test_probabilities["DIRECTION"], 1.0
        )
        test_layered = (
            test_probabilities["RUNWAY"]
            * test_probabilities["DIRECTION"]
            * (1.0 - test_probabilities["SEVERE"])
        )
        test_admission = (
            test_probabilities["REGIME"]
            * test_probabilities["DIRECTION"]
            * (1.0 - test_probabilities["SEVERE"])
        )
        rp_tier = tier_weights(
            test_runway_persist,
            thresholds["runway_persist_q50"],
            thresholds["runway_persist_q75"],
        )
        layered_tier = tier_weights(
            test_layered, thresholds["layered_q50"], thresholds["layered_q75"]
        )
        policies = {
            "R3_RUNWAY_PERSIST": rp_tier,
            "R3_LAYERED": layered_tier,
            "R3_LAYERED_NEUTRAL": neutral_weights(
                outer_test,
                layered_tier,
                test_admission,
                thresholds["admission_q50"],
            ),
        }
        if r2_weights:
            policies["R2_DEFAULT"] = outer_test["decision"].map(r2_weights).fillna(0.0).to_numpy(dtype=float)

        score = outer_test[
            [
                "signal_id", "decision", "entry_time", "exit_time", "year", "dir",
                "rid", "k", "L", "early3", "pnl", "R", "position_hours",
                "same_m1_exit_stop_ambiguous",
            ]
        ].copy()
        for name, values in test_probabilities.items():
            score[f"p_{name.lower()}"] = values
        score["score_runway_persist"] = test_runway_persist
        score["score_layered"] = test_layered
        score["score_admission"] = test_admission
        for key, value in thresholds.items():
            score[key] = value
        for name, desired in list(policies.items()):
            score[f"W_{name}"] = desired
            capped = apply_campaign_cap(outer_test, desired, 8.0)
            policies[f"{name}_CAP8"] = capped
            score[f"W_{name}_CAP8"] = capped
        score_ledgers.append(score)

        for name, units in policies.items():
            policy_rows.append(policy_metrics(outer_test, units, name, str(outer_year)))
            right_tail.extend(right_tail_rows(outer_test, units, name, str(outer_year)))

    score_ledger = pd.concat(score_ledgers, ignore_index=True).sort_values("decision")
    for column in [x for x in score_ledger.columns if x.startswith("W_")]:
        policy = column[2:]
        units = score_ledger[column].to_numpy(dtype=float)
        policy_rows.append(policy_metrics(score_ledger, units, policy, "POOLED_2024_2026"))
        right_tail.extend(right_tail_rows(score_ledger, units, policy, "POOLED_2024_2026"))

    selection = pd.DataFrame(selection_rows).sort_values(
        ["outer_year", "head", "selected", "logloss"], ascending=[True, True, False, True]
    )
    fold_detail = pd.DataFrame(fold_rows).sort_values(["outer_year", "head", "spec_id", "fold"])
    head_metrics = pd.DataFrame(head_metric_rows).sort_values(["outer_year", "head"])
    policy_summary = pd.DataFrame(policy_rows).sort_values(["year", "policy"])
    right_tail_summary = pd.DataFrame(right_tail).sort_values(["year", "policy", "run_length_bucket"])

    outputs = {
        "selection": args.out_dir / "V10_R3_MODEL_SELECTION.csv",
        "folds": args.out_dir / "V10_R3_MODEL_SELECTION_FOLDS.csv",
        "head_metrics": args.out_dir / "V10_R3_HEAD_METRICS.csv",
        "scores": args.out_dir / "V10_R3_SCORE_POLICY_LEDGER_2024_2026.csv",
        "policies": args.out_dir / "V10_R3_POLICY_SUMMARY.csv",
        "right_tail": args.out_dir / "V10_R3_RIGHT_TAIL_SUMMARY.csv",
        "bundle": args.out_dir / "V10_R3_MODEL_BUNDLE.joblib",
    }
    selection.to_csv(outputs["selection"], index=False)
    fold_detail.to_csv(outputs["folds"], index=False)
    head_metrics.to_csv(outputs["head_metrics"], index=False)
    score_ledger.to_csv(outputs["scores"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    policy_summary.to_csv(outputs["policies"], index=False)
    right_tail_summary.to_csv(outputs["right_tail"], index=False)
    joblib.dump(model_bundle, outputs["bundle"])

    validation = {
        "ok": True,
        "source": str(args.universe),
        "source_sha256": sha256_file(args.universe),
        "rows": len(frame),
        "outer_years": [2024, 2025, 2026],
        "label_crossing_rows_purged": {
            str(year): int(
                ((frame["decision"] < pd.Timestamp(year=year, month=1, day=1)) & (frame["label_available_at"] >= pd.Timestamp(year=year, month=1, day=1))).sum()
            )
            for year in (2024, 2025, 2026)
        },
        "ambiguous_same_m1_rows": int(frame["same_m1_exit_stop_ambiguous"].sum()),
        "head_feature_counts": {head.name: len(head.features) for head in HEADS},
        "selection_objective": "minimum expanding-fold log loss; Brier then AUC tie-break",
        "calibration": "Platt sigmoid fit only on expanding-fold OOF predictions",
        "threshold_clock": "q50/q75 and admission q50 from prior-only calibrated OOF scores",
        "outputs": {key: str(value) for key, value in outputs.items()},
        "output_sha256": {
            key: sha256_file(value) for key, value in outputs.items() if key != "bundle"
        },
        "authority": "CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY",
    }
    validation_path = args.out_dir / "V10_R3_VALIDATION.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(head_metrics.to_string(index=False))
    print("\nPOOLED POLICIES")
    print(policy_summary[policy_summary["year"] == "POOLED_2024_2026"].to_string(index=False))
    print(f"\nvalidation={validation_path}")


if __name__ == "__main__":
    main()
