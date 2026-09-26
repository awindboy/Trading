"""Directly retrain frozen V10 R4/R5 heads with causal weekly feature blocks.

Phase 1T is consumed-development diagnostics only.  It rebuilds the V10 causal
opportunity universe from raw M1, appends the already-frozen Phase-1S weekly
coordinates inside the original head-specific models, and recomputes the R4 ->
R5 -> R7G chain chronologically.  No result has action authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import shutil
import sys
from bisect import bisect_left, bisect_right, insort
from datetime import datetime
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "research" / "v10"))

import catboost
import lightgbm
import numpy as np
import pandas as pd
import sklearn
import xgboost
from catboost import CatBoostClassifier, CatBoostRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.metrics import log_loss, roc_auc_score
from xgboost import XGBClassifier, XGBRegressor

from build_v10_causal_m1_universe_r3 import UniverseBuilder
from build_v12_phase0 import PrefixAudit, iter_m1_prefix, parse_cutoff
from build_v12_phase1d import build_clusters, load_calendar
from build_v12_phase1s import CLOCK_FEATURES, EVENT_FEATURES, PRICE_FEATURES, build_features


VERSION = "v12-phase1t-v10-direct-feature-retrain-v1"
PREFIX = "V12_PHASE1T_"
SEED = 261017

RAW_FEATURES = [
    "stop_dist_atr", "fast_body_rng", "fast_body_atr", "std_align",
    "std_body_rng", "slow_align", "slow_body_rng", "adx28_rel",
    "di14_signed", "di28_signed", "ema8_21_signed", "ema8_slope",
    "path_eff4_rel", "path_eff12_rel", "flip4", "flip8", "flip12",
    "m15_aligned", "m15_transition", "m15_streak", "m15_body_sum_atr",
    "m15_body_eff", "m15_body_rng", "m15_opp_wick", "m30_aligned",
    "m30_transition", "m30_streak", "m30_body_sum_atr", "m30_body_eff",
    "m30_body_rng", "m30_opp_wick", "h1_aligned", "h1_transition",
    "h1_streak", "h1_body_sum_atr", "h1_body_eff", "h1_body_rng",
    "h1_opp_wick",
]
RANK_RAW = [
    "stop_dist_atr", "fast_body_rng", "std_body_rng", "slow_body_rng",
    "adx28_rel", "di14_signed", "ema8_21_signed", "path_eff4_rel",
    "path_eff12_rel", "flip8", "m15_body_rng", "m30_body_rng", "h1_body_rng",
]
HEAD_FEATURES = {
    "V10_CONTROL": {"r4": [], "r5_stop": [], "r5_r": []},
    "V10_WEEK_CLOCK": {"r4": CLOCK_FEATURES, "r5_stop": CLOCK_FEATURES, "r5_r": CLOCK_FEATURES},
    "V10_WEEK_PRICE": {"r4": PRICE_FEATURES, "r5_stop": PRICE_FEATURES, "r5_r": PRICE_FEATURES},
    "V10_WEEK_PRICE_EVENT": {
        "r4": PRICE_FEATURES + EVENT_FEATURES,
        "r5_stop": PRICE_FEATURES + EVENT_FEATURES,
        "r5_r": PRICE_FEATURES + EVENT_FEATURES,
    },
    # Post-primary explanatory ablations.  These cannot repair or redefine the
    # frozen all-head primary result.
    "V10_WEEK_PRICE_R4_ONLY": {"r4": PRICE_FEATURES, "r5_stop": [], "r5_r": []},
    "V10_WEEK_PRICE_STOP_ONLY": {"r4": [], "r5_stop": PRICE_FEATURES, "r5_r": []},
    "V10_WEEK_PRICE_R5_BOTH": {"r4": [], "r5_stop": PRICE_FEATURES, "r5_r": PRICE_FEATURES},
    "V10_WEEK_PRICE_EVENT_STOP_ONLY": {
        "r4": [], "r5_stop": PRICE_FEATURES + EVENT_FEATURES, "r5_r": [],
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual.lower() != expected.lower():
        raise ValueError(f"{label} SHA256 mismatch: {actual}; expected {expected}")


def safe_output(path: Path, replace: bool) -> None:
    resolved = path.resolve()
    output_root = (Path(__file__).resolve().parents[2] / "output").resolve()
    if output_root not in resolved.parents:
        raise ValueError(f"output must be a child of {output_root}: {resolved}")
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output is not empty: {path}")
        for child in path.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def save_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g",
                 date_format="%Y-%m-%d %H:%M:%S")


def save_json(value: object, path: Path) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8")


def build_universe(m1_path: Path, cutoff: datetime) -> tuple[pd.DataFrame, PrefixAudit]:
    audit = PrefixAudit()
    builder = UniverseBuilder()
    for row in iter_m1_prefix(m1_path, cutoff, audit=audit):
        builder.push_m1(row.timestamp, row.open, row.high, row.low, row.close)
    frame = builder.frame()
    frame["decision"] = pd.to_datetime(frame["decision"])
    frame["entry_time"] = pd.to_datetime(frame["entry_time"])
    frame["exit_time"] = pd.to_datetime(frame["exit_time"])
    frame["label_available_at"] = pd.to_datetime(frame["label_available_at"])
    frame["direction"] = np.where(frame["dir"].astype(int) > 0, "LONG", "SHORT")
    frame["stage"] = np.where(frame["k"].eq(1), "k1", np.where(frame["k"].eq(2), "k2", "k3p"))
    frame = frame.sort_values("decision").reset_index(drop=True)
    frame["opportunity_index"] = np.arange(len(frame), dtype=int)
    return frame, audit


def rank_past(values: Iterable[float], window: int = 360) -> np.ndarray:
    values = np.asarray(list(values), dtype=float)
    output = np.full(len(values), 0.5, dtype=float)
    history: list[float] = []
    for index, value in enumerate(values):
        if len(history) >= 40 and np.isfinite(value):
            output[index] = (bisect_right(history, float(value)) + 0.5) / (len(history) + 1.0)
        if np.isfinite(value):
            insort(history, float(value))
        expired = index - window
        if expired >= 0 and np.isfinite(values[expired]):
            position = bisect_left(history, float(values[expired]))
            if position < len(history):
                history.pop(position)
    return output


def add_v10_features(universe: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    frame = universe.copy()
    engineered = pd.DataFrame(index=frame.index)
    engineered["log_stop"] = np.log1p(frame["stop_dist_atr"].clip(lower=0))
    engineered["fast_body"] = frame["fast_body_rng"]
    engineered["ha_align"] = (frame["std_align"] + frame["slow_align"]) / 2.0
    engineered["ha_disagree"] = (frame["std_align"] != frame["slow_align"]).astype(float)
    engineered["ha_body_mean"] = frame[["fast_body_rng", "std_body_rng", "slow_body_rng"]].mean(axis=1)
    engineered["ha_body_disp"] = frame[["fast_body_rng", "std_body_rng", "slow_body_rng"]].std(axis=1).fillna(0)
    engineered["adx"] = frame["adx28_rel"]
    engineered["di_mean"] = frame[["di14_signed", "di28_signed"]].mean(axis=1)
    engineered["di_disp"] = (frame["di14_signed"] - frame["di28_signed"]).abs()
    engineered["ema"] = frame["ema8_21_signed"]
    engineered["ema_slope"] = frame["ema8_slope"]
    engineered["path_mean"] = frame[["path_eff4_rel", "path_eff12_rel"]].mean(axis=1)
    engineered["path_ratio"] = frame["path_eff4_rel"] / (frame["path_eff12_rel"].abs() + 1e-6)
    engineered["flip_mean"] = frame[["flip4", "flip8", "flip12"]].mean(axis=1)
    engineered["flip_accel"] = frame["flip4"] - frame["flip12"]
    groups = {
        "align": ["m15_aligned", "m30_aligned", "h1_aligned"],
        "transition": ["m15_transition", "m30_transition", "h1_transition"],
        "streak": ["m15_streak", "m30_streak", "h1_streak"],
        "body_sum": ["m15_body_sum_atr", "m30_body_sum_atr", "h1_body_sum_atr"],
        "body_eff": ["m15_body_eff", "m30_body_eff", "h1_body_eff"],
        "body_rng": ["m15_body_rng", "m30_body_rng", "h1_body_rng"],
        "opp_wick": ["m15_opp_wick", "m30_opp_wick", "h1_opp_wick"],
    }
    for name, columns in groups.items():
        engineered[f"{name}_mean"] = frame[columns].mean(axis=1)
        engineered[f"{name}_disp"] = frame[columns].std(axis=1).fillna(0)
    engineered["trend_flow"] = engineered["adx"] * engineered["body_rng_mean"]
    engineered["path_flow"] = engineered["path_mean"] * engineered["body_rng_mean"]
    engineered["dir_flow"] = engineered["di_mean"] * engineered["body_rng_mean"]
    engineered["ha_flow"] = engineered["ha_body_mean"] * engineered["body_rng_mean"]
    engineered.columns = [f"e_{name}" for name in engineered.columns]
    frame = pd.concat([frame, engineered], axis=1)
    for source in RANK_RAW:
        column = f"rk_{source}"
        frame[column] = 0.5
        for _, indices in frame.groupby(["stage", "direction"], sort=False).groups.items():
            ordered = frame.loc[indices].sort_values("decision")
            frame.loc[ordered.index, column] = rank_past(ordered[source].to_numpy())
    feature_registry = RAW_FEATURES + list(engineered.columns) + [f"rk_{name}" for name in RANK_RAW]
    if len(feature_registry) != 84:
        raise AssertionError(f"expected 84 V10 features, got {len(feature_registry)}")
    return frame, feature_registry


def training_slice(frame: pd.DataFrame, eval_year: int, recency: str,
                   *, non_stop: bool = False) -> tuple[pd.DataFrame, np.ndarray | None]:
    train = frame.loc[frame["year"].astype(int) < eval_year].copy()
    if non_stop:
        train = train.loc[train["stop_hit"].eq(0)].copy()
    weights: np.ndarray | None = None
    boundary = pd.Timestamp(f"{eval_year}-01-01")
    if recency == "roll730":
        train = train.loc[train["decision"] >= boundary - pd.Timedelta(days=730)].copy()
    elif recency in {"exp365", "exp730"}:
        half_life = int(recency[3:])
        age = (boundary - train["decision"]).dt.total_seconds() / 86400.0
        weights = np.power(0.5, age.to_numpy() / half_life)
    elif recency != "expanding":
        raise ValueError(f"unknown recency: {recency}")
    return train, weights


def matrix(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    return frame[features].replace([np.inf, -np.inf], np.nan).fillna(0.0)


def make_model(family: str, params: dict, task: str):
    params = dict(params)
    if family == "lgb":
        params.update(verbosity=-1, n_jobs=2, random_state=SEED)
        return LGBMClassifier(**params) if task == "cls" else LGBMRegressor(**params)
    if family == "xgb":
        params.update(verbosity=0, n_jobs=2, random_state=SEED)
        if task == "cls":
            return XGBClassifier(objective="binary:logistic", eval_metric="logloss", **params)
        return XGBRegressor(objective="reg:squarederror", **params)
    if family == "cat":
        params.update(verbose=False, thread_count=2, random_seed=SEED, allow_writing_files=False)
        if task == "cls":
            return CatBoostClassifier(loss_function="Logloss", **params)
        return CatBoostRegressor(loss_function="RMSE", **params)
    raise ValueError(f"unknown family: {family}")


def fit_variant(frame: pd.DataFrame, specs: dict, variant: str) -> pd.DataFrame:
    added = HEAD_FEATURES[variant]
    rows: list[pd.DataFrame] = []
    for stage in ("k1", "k2", "k3p"):
        for direction in ("LONG", "SHORT"):
            key = f"{stage}_{direction}"
            spec = specs[key]
            local = frame.loc[(frame["stage"] == stage) & (frame["direction"] == direction)].copy()
            for year in (2023, 2024, 2025, 2026):
                test = local.loc[local["year"].astype(int) == year].copy()
                if test.empty:
                    continue
                r4 = spec["r4"]
                r4_features = list(dict.fromkeys(r4["features"] + added["r4"]))
                train, sample_weight = training_slice(local, year, r4["recency"])
                alpha = 0.1 if spec["score_source"] == "q10" else 0.5
                qparams = dict(r4["qpar"])
                qparams.update(objective="quantile", alpha=alpha, verbosity=-1,
                               n_jobs=2, random_state=SEED)
                r4_model = LGBMRegressor(**qparams)
                r4_model.fit(matrix(train, r4_features), train["R"], sample_weight=sample_weight)
                score = r4_model.predict(matrix(test, r4_features))

                stop_spec = spec["r5_stop"]
                stop_features = list(dict.fromkeys(stop_spec["features"] + added["r5_stop"]))
                stop_train, stop_weight = training_slice(local, year, stop_spec["recency"])
                stop_model = make_model(stop_spec["family"], stop_spec["params"], "cls")
                stop_model.fit(matrix(stop_train, stop_features), stop_train["stop_hit"],
                               sample_weight=stop_weight)
                p_stop = stop_model.predict_proba(matrix(test, stop_features))[:, 1]

                r_spec = spec["r5_r"]
                r_features = list(dict.fromkeys(r_spec["features"] + added["r5_r"]))
                r_train, r_weight = training_slice(local, year, r_spec["recency"], non_stop=True)
                r_model = make_model(r_spec["family"], r_spec["params"], "reg")
                r_model.fit(matrix(r_train, r_features), r_train["R"], sample_weight=r_weight)
                mu = r_model.predict(matrix(test, r_features))

                result = test[[
                    "signal_id", "decision", "entry_time", "exit_time", "year", "dir", "direction",
                    "stage", "k", "rid", "L", "R", "pnl", "stop_hit", "opportunity_index",
                ]].copy()
                result["variant"] = variant
                result["score"] = score
                result["p_stop"] = p_stop
                result["mu_nonstop"] = mu
                result["EV"] = -p_stop + (1.0 - p_stop) * mu
                result["r4_feature_count"] = len(r4_features)
                result["r5_stop_feature_count"] = len(stop_features)
                result["r5_r_feature_count"] = len(r_features)
                rows.append(result)
    output = pd.concat(rows, ignore_index=True).sort_values("decision").reset_index(drop=True)
    return output


def assign_r4_actions(scored: pd.DataFrame) -> pd.DataFrame:
    frame = scored.copy()
    frame["quarter"] = frame["decision"].dt.to_period("Q")
    references: dict[tuple[str, str, pd.Period], tuple[float, float, int]] = {}
    for (stage, direction, quarter), group in frame.groupby(["stage", "direction", "quarter"]):
        values = group["score"].to_numpy(dtype=float)
        references[(stage, direction, quarter)] = (
            float(np.quantile(values, 0.50)), float(np.quantile(values, 0.75)), len(values)
        )
    q50: list[float] = []
    q75: list[float] = []
    ref_n: list[int] = []
    weights: list[int] = []
    for row in frame.itertuples():
        ref = references.get((row.stage, row.direction, row.quarter - 1))
        if ref is None:
            q50.append(math.nan); q75.append(math.nan); ref_n.append(0); weights.append(0)
            continue
        median, upper, count = ref
        q50.append(median); q75.append(upper); ref_n.append(count)
        weights.append(0 if row.score < median else (1 if row.score < upper else 3))
    frame["q50"] = q50
    frame["q75"] = q75
    frame["threshold_reference_n"] = ref_n
    frame["r4_weight"] = weights
    return frame.drop(columns=["quarter"])


def feedback_and_r7g(frame: pd.DataFrame, h4_window: int = 180) -> pd.DataFrame:
    output = frame.sort_values("decision").copy().reset_index(drop=True)
    # Every opportunity corresponds to one completed H4 decision slot after the
    # V10 warmup, so opportunity_index distance is the H4-index distance.
    eligible: list[tuple[int, pd.Timestamp, float]] = []
    feedback: list[float] = []
    weights: list[int] = []
    for row in output.itertuples():
        known = [realized for index, exit_time, realized in eligible
                 if index >= row.opportunity_index - h4_window and exit_time < row.decision]
        value = float(np.mean(known)) if known else math.nan
        feedback.append(value)
        weight = int(row.r4_weight)
        if weight == 1 and row.EV > 0.0 and math.isfinite(value) and value > 0.0:
            weight = 3
        weights.append(weight)
        if int(row.r4_weight) == 1 and row.EV > 0.0:
            eligible.append((int(row.opportunity_index), pd.Timestamp(row.exit_time), float(row.R)))
    output["feedback_R"] = feedback
    output["r7g_weight"] = weights
    return output


def load_mt5_events(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["decision_dt"] = pd.to_datetime(frame["decision"], format="%Y.%m.%d %H:%M")
    frame["direction"] = frame["dir"].map({"LONG": "LONG", "SHORT": "SHORT"})
    frame["stage"] = np.where(frame["k"].astype(int).eq(1), "k1",
                               np.where(frame["k"].astype(int).eq(2), "k2", "k3p"))
    return frame


def parity(control: pd.DataFrame, mt5: pd.DataFrame, start: pd.Timestamp,
           end: pd.Timestamp) -> tuple[pd.DataFrame, dict]:
    left = control.loc[(control["decision"] >= start) & (control["decision"] <= end)].copy()
    right = mt5.loc[(mt5["decision_dt"] >= start) & (mt5["decision_dt"] <= end)].copy()
    joined = left.merge(
        right[["decision_dt", "direction", "score", "q50", "q75", "r4_weight",
               "p_stop", "mu_nonstop", "EV", "feedback_R", "r7g_weight"]],
        left_on=["decision", "direction"], right_on=["decision_dt", "direction"],
        suffixes=("_refit", "_mt5"), how="outer", indicator=True, validate="one_to_one",
    )
    for name in ("score", "q50", "q75", "p_stop", "mu_nonstop", "EV", "feedback_R"):
        joined[f"{name}_abs_error"] = (
            pd.to_numeric(joined[f"{name}_refit"], errors="coerce")
            - pd.to_numeric(joined[f"{name}_mt5"], errors="coerce")
        ).abs()
    common = joined["_merge"].eq("both")
    r4_match = joined["r4_weight_refit"].eq(joined["r4_weight_mt5"]) & common
    ev_sign_match = (
        (pd.to_numeric(joined["EV_refit"], errors="coerce") > 0)
        == (pd.to_numeric(joined["EV_mt5"], errors="coerce") > 0)
    ) & common
    r7_match = joined["r7g_weight_refit"].eq(joined["r7g_weight_mt5"]) & common
    joined["r4_action_match"] = r4_match
    joined["r5_ev_sign_match"] = ev_sign_match
    joined["r7g_weight_match"] = r7_match
    summary = {
        "refit_rows": int(len(left)), "mt5_rows": int(len(right)),
        "joined_rows": int(common.sum()), "left_only": int((joined["_merge"] == "left_only").sum()),
        "right_only": int((joined["_merge"] == "right_only").sum()),
        "r4_action_matches": int(r4_match.sum()), "r4_action_match_rate": float(r4_match.sum() / max(1, common.sum())),
        "r5_ev_sign_matches": int(ev_sign_match.sum()), "r5_ev_sign_match_rate": float(ev_sign_match.sum() / max(1, common.sum())),
        "r7g_weight_matches": int(r7_match.sum()), "r7g_weight_match_rate": float(r7_match.sum() / max(1, common.sum())),
        "score_max_abs_error": float(joined.loc[common, "score_abs_error"].max()),
        "ev_max_abs_error": float(joined.loc[common, "EV_abs_error"].max()),
        "feedback_max_abs_error": float(joined.loc[common, "feedback_R_abs_error"].max()),
    }
    return joined, summary


def maximum_stop_streak(frame: pd.DataFrame) -> int:
    maximum = current = 0
    for value in frame.sort_values("decision")["stop_hit"].astype(int):
        current = current + 1 if value else 0
        maximum = max(maximum, current)
    return maximum


def score_policy(frame: pd.DataFrame, scope: str) -> dict:
    selected = frame.loc[frame["r7g_weight"] > 0].copy()
    weights = selected["r7g_weight"].astype(float)
    weighted_r = selected["R"].astype(float) * weights
    stopped = selected["stop_hit"].astype(int).eq(1)
    stopped_units = float(weights[stopped].sum())
    funded_units = float(weights.sum())
    equity = weighted_r.cumsum()
    drawdown = float((equity.cummax() - equity).max()) if len(equity) else 0.0
    return {
        "scope": scope,
        "children": int(len(selected)),
        "funded_units": funded_units,
        "stopped_children": int(stopped.sum()),
        "stopped_units": stopped_units,
        "stopped_units_per_100": 100.0 * stopped_units / funded_units if funded_units else math.nan,
        "win_rate": float((selected["R"] > 0).mean()) if len(selected) else math.nan,
        "net_R": float(weighted_r.sum()),
        "R_per_unit": float(weighted_r.sum() / funded_units) if funded_units else math.nan,
        "drawdown_R": drawdown,
        "right_tail_ge5_R": float(weighted_r[selected["R"] >= 5.0].sum()),
        "max_stop_streak": maximum_stop_streak(selected),
    }


def safe_auc(y: pd.Series, score: pd.Series) -> float:
    if len(y) == 0 or y.nunique() < 2:
        return math.nan
    return float(roc_auc_score(y.astype(int), score.astype(float)))


def safe_logloss(y: pd.Series, score: pd.Series) -> float:
    if len(y) == 0 or y.nunique() < 2:
        return math.nan
    return float(log_loss(y.astype(int), np.clip(score.astype(float), 1e-9, 1 - 1e-9)))


def safe_spearman(y: pd.Series, score: pd.Series) -> float:
    return float(pd.Series(y).corr(pd.Series(score), method="spearman"))


def model_metrics(frame: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for (variant, year), group in frame.groupby(["variant", "year"]):
        rows.extend([
            {"variant": variant, "year": int(year), "head": "R4_SCORE", "metric": "spearman_R",
             "value": safe_spearman(group["R"], group["score"]), "rows": len(group)},
            {"variant": variant, "year": int(year), "head": "R5_STOP", "metric": "auc",
             "value": safe_auc(group["stop_hit"], group["p_stop"]), "rows": len(group)},
            {"variant": variant, "year": int(year), "head": "R5_STOP", "metric": "log_loss",
             "value": safe_logloss(group["stop_hit"], group["p_stop"]), "rows": len(group)},
        ])
        non_stop = group.loc[group["stop_hit"].eq(0)]
        rows.append({"variant": variant, "year": int(year), "head": "R5_CONDITIONAL_R",
                     "metric": "spearman_R", "value": safe_spearman(non_stop["R"], non_stop["mu_nonstop"]),
                     "rows": len(non_stop)})
    return rows


def capital_tables(scored: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp):
    active = scored.loc[(scored["decision"] >= start) & (scored["decision"] <= end)].copy()
    pooled: list[dict] = []
    years: list[dict] = []
    sides: list[dict] = []
    for variant, group in active.groupby("variant", sort=False):
        pooled.append({"variant": variant, **score_policy(group, "POOLED")})
        for year, part in group.groupby("year"):
            years.append({"variant": variant, **score_policy(part, str(int(year)))})
        for side, part in group.groupby("direction"):
            sides.append({"variant": variant, **score_policy(part, side)})
    return pd.DataFrame(pooled), pd.DataFrame(years), pd.DataFrame(sides)


def gates(pooled: pd.DataFrame, years: pd.DataFrame, sides: pd.DataFrame,
          contract: dict, parity_summary: dict) -> pd.DataFrame:
    base = pooled.set_index("variant").loc["V10_CONTROL"]
    primary = pooled.set_index("variant").loc[contract["primary_variant"]]
    rules = contract["primary_gates"]
    stopped_improvement = 1.0 - primary["stopped_units_per_100"] / base["stopped_units_per_100"]
    equal_stop_r = primary["net_R"] * base["stopped_units"] / primary["stopped_units"]
    year_base = years.loc[years["variant"] == "V10_CONTROL"].set_index("scope")
    year_primary = years.loc[years["variant"] == contract["primary_variant"]].set_index("scope")
    negative_years = int((year_primary["net_R"] - year_base["net_R"] < 0).sum())
    side_base = sides.loc[sides["variant"] == "V10_CONTROL"].set_index("scope")
    side_primary = sides.loc[sides["variant"] == contract["primary_variant"]].set_index("scope")
    values = [
        ("CONTROL_R4_PARITY", parity_summary["r4_action_match_rate"], contract["control_parity"]["r4_action_match_required"], ">="),
        ("CONTROL_R5_EV_SIGN_PARITY", parity_summary["r5_ev_sign_match_rate"], contract["control_parity"]["r5_ev_sign_match_required"], ">="),
        ("CONTROL_R7G_PARITY", parity_summary["r7g_weight_match_rate"], contract["control_parity"]["r7g_weight_match_required"], ">="),
        ("CHILD_RETENTION", primary["children"] / base["children"], rules["child_retention_min"], ">="),
        ("NET_R_RETENTION", primary["net_R"] / base["net_R"], rules["net_r_retention_min"], ">="),
        ("TAIL_RETENTION", primary["right_tail_ge5_R"] / base["right_tail_ge5_R"], rules["right_tail_ge5_r_retention_min"], ">="),
        ("STOPPED_UNITS_PER100_IMPROVEMENT", stopped_improvement, rules["stopped_units_per_100_improvement_min"], ">="),
        ("EQUAL_STOP_BUDGET_R_RATIO", equal_stop_r / base["net_R"], rules["equal_stopped_unit_budget_r_ratio_min"], ">="),
        ("MAX_STOP_STREAK_NONWORSE", float(primary["max_stop_streak"] <= base["max_stop_streak"]), 1.0, ">="),
        ("BOTH_SIDES_STOP_DENSITY_NONWORSE", float((side_primary["stopped_units_per_100"] <= side_base["stopped_units_per_100"]).all()), 1.0, ">="),
        ("NEGATIVE_YEAR_DELTAS", float(negative_years), float(rules["maximum_negative_annual_deltas"]), "<="),
    ]
    return pd.DataFrame([
        {"gate": name, "actual": float(actual), "required": float(required), "operator": operator,
         "passed": bool(actual >= required if operator == ">=" else actual <= required)}
        for name, actual, required, operator in values
    ])


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1t_contract.json")
    parser.add_argument("--model-specs", type=Path, default=repo / "research/v12/v12_phase1t_v10_frozen_model_specs.json")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--calendar", type=Path, default=Path.home() / "AppData/Roaming/MetaQuotes/Terminal/Common/Files/V12_PHASE1E_MQL5_CALENDAR_SNAPSHOT.csv")
    parser.add_argument("--calendar-overrides", type=Path, default=repo / "research/v12/v12_calendar_time_overrides.json")
    parser.add_argument("--mt5-events", type=Path, default=Path.home() / "Downloads/V10_R7G_full_embedded_ml_events.csv")
    parser.add_argument("--v10-child-ledger", type=Path, default=repo / "output/v11_reassembly_stage3_20260923/V11_REASSEMBLY_STAGE3_CHILD_LEDGER.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1t_v10_direct_feature_retrain_20260926_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != VERSION:
        raise ValueError("contract version mismatch")
    sources = contract["source_hashes"]
    for path, key, label in (
        (args.m1, "raw_m1_full_sha256", "raw M1"),
        (args.calendar, "calendar_snapshot_sha256", "calendar"),
        (args.calendar_overrides, "calendar_time_overrides_sha256", "calendar overrides"),
        (args.model_specs, "frozen_model_specs_sha256", "frozen V10 model specs"),
        (args.mt5_events, "mt5_event_ledger_sha256", "MT5 event ledger"),
        (args.v10_child_ledger, "v10_child_ledger_sha256", "V10 Child ledger"),
    ):
        verify(path, sources[key], label)
    safe_output(args.output, args.replace)

    cutoff = parse_cutoff(contract["cutoff"])
    universe, audit = build_universe(args.m1, cutoff)
    universe, registry = add_v10_features(universe)
    calendar, calendar_quality = load_calendar(args.calendar, cutoff, args.calendar_overrides)
    clusters = build_clusters(calendar)
    decisions = universe[["signal_id", "decision", "direction", "dir"]].rename(
        columns={"decision": "decision_time"}
    )
    weekly, weekly_audit = build_features(args.m1, decisions, clusters, cutoff)
    weekly = weekly.rename(columns={"decision_time": "decision"})
    joined = universe.merge(weekly, on=["signal_id", "decision", "direction"], how="inner", validate="one_to_one")
    if len(joined) != len(universe):
        raise ValueError(f"weekly feature coverage mismatch: {len(joined)} != {len(universe)}")
    specs = json.loads(args.model_specs.read_text(encoding="utf-8"))

    variants: list[pd.DataFrame] = []
    for variant in contract["feature_variants"]:
        scored = fit_variant(joined, specs, variant)
        scored = assign_r4_actions(scored)
        scored = feedback_and_r7g(scored)
        variants.append(scored)
    all_scored = pd.concat(variants, ignore_index=True)

    start = pd.Timestamp(contract["economic_window"]["start_inclusive"])
    end = pd.Timestamp(contract["economic_window"]["end_inclusive"])
    mt5 = load_mt5_events(args.mt5_events)
    parity_ledger, parity_summary = parity(
        all_scored.loc[all_scored["variant"] == "V10_CONTROL"], mt5, start, end
    )
    pooled, years, sides = capital_tables(all_scored, start, end)
    gate_table = gates(pooled, years, sides, contract, parity_summary)
    metrics = pd.DataFrame(model_metrics(all_scored.loc[all_scored["year"] >= 2024]))

    inventory = []
    for variant, heads in HEAD_FEATURES.items():
        for head, added in heads.items():
            for order, feature in enumerate(added):
                inventory.append({"variant": variant, "head": head, "order": order, "feature": feature})
    quality = {
        "contract_version": VERSION,
        "raw_m1_prefix_rows": audit.parsed_price_rows,
        "raw_m1_prefix_sha256": audit.prefix_sha256,
        "first_unrevealed_timestamp": audit.first_unrevealed_timestamp.isoformat() if audit.first_unrevealed_timestamp else None,
        "weekly_prefix_rows": weekly_audit.parsed_price_rows,
        "weekly_prefix_sha256": weekly_audit.prefix_sha256,
        "universe_rows": len(universe),
        "universe_first_decision": universe["decision"].min().isoformat(),
        "universe_last_decision": universe["decision"].max().isoformat(),
        "weekly_feature_rows": len(weekly),
        "strict_weekly_snapshots": int((pd.to_datetime(weekly["snapshot_last_m1_time"]) < weekly["decision"]).sum()),
        "v10_feature_count": len(registry),
        "calendar": calendar_quality,
        "versions": {
            "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__, "lightgbm": lightgbm.__version__,
            "xgboost": xgboost.__version__, "catboost": catboost.__version__,
        },
    }
    control_failed = gate_table.loc[
        gate_table["gate"].str.startswith("CONTROL_") & ~gate_table["passed"]
    ]
    summary = {
        "contract_version": VERSION,
        "status": "COMPLETE_DIAGNOSTIC" if control_failed.empty else "CONTROL_PARITY_FAILED",
        "parity": parity_summary,
        "primary_variant": contract["primary_variant"],
        "primary_gates_passed": int(gate_table["passed"].sum()),
        "primary_gates_total": int(len(gate_table)),
        "all_gates_pass": bool(gate_table["passed"].all()),
        "pooled": pooled.to_dict(orient="records"),
        "evidence": contract["evidence"],
    }

    save_csv(all_scored, args.output / f"{PREFIX}EVENT_LEDGER.csv")
    save_csv(parity_ledger, args.output / f"{PREFIX}CONTROL_PARITY.csv")
    save_csv(pd.DataFrame([parity_summary]), args.output / f"{PREFIX}CONTROL_PARITY_SUMMARY.csv")
    save_csv(metrics, args.output / f"{PREFIX}MODEL_METRICS.csv")
    save_csv(pooled, args.output / f"{PREFIX}POLICY_SCORECARDS.csv")
    save_csv(years, args.output / f"{PREFIX}YEAR_SCORECARDS.csv")
    save_csv(sides, args.output / f"{PREFIX}SIDE_SCORECARDS.csv")
    save_csv(gate_table, args.output / f"{PREFIX}GATES.csv")
    save_csv(pd.DataFrame(inventory), args.output / f"{PREFIX}FEATURE_INVENTORY.csv")
    save_json(quality, args.output / f"{PREFIX}DATA_QUALITY.json")
    save_json(summary, args.output / f"{PREFIX}SUMMARY.json")
    manifest = {
        path.name: sha256_file(path)
        for path in sorted(args.output.iterdir()) if path.is_file()
    }
    save_json(manifest, args.output / f"{PREFIX}RELEASE_MANIFEST.json")
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
