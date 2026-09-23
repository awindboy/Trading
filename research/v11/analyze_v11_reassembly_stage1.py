"""Stage-1 V11 reassembly: chronological sequential capital-funding diagnostic.

This script does not create a trading rule.  It asks whether the causal parts
already present in V10 can be reassembled into a funding clock rather than an
immediate-entry filter.  A FAST-k1 candidate may be funded immediately, kept
unfunded while its frozen Hard-SL guard remains alive, funded at a later causal
checkpoint, or left unfunded.  The campaign still exits on the frozen FAST
clock.

All reported tests are consumed-development evidence.  Models are fixed ridge
decompositions of three quantities for each action: action availability,
P(Hard-SL | funded), and E[R | funded, non-stop].  The script evaluates nested
feature views and a pre-declared stop-cost frontier without selecting a winner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


CHECKPOINTS = (0, 60, 120, 180)
STOP_COSTS = (0.0, 0.25, 0.50, 1.0, 2.0)
RIDGE_ALPHA = 25.0
MIN_TRAIN_ROWS = 40
RAW_FEATURES = (
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
)
ENGINEERED_FEATURES = (
    "e_log_stop", "e_fast_body", "e_ha_align", "e_ha_disagree",
    "e_ha_body_mean", "e_ha_body_disp", "e_adx", "e_di_mean",
    "e_di_disp", "e_ema", "e_ema_slope", "e_path_mean", "e_path_ratio",
    "e_flip_mean", "e_flip_accel", "e_align_mean", "e_align_disp",
    "e_transition_mean", "e_transition_disp", "e_streak_mean",
    "e_streak_disp", "e_body_sum_mean", "e_body_sum_disp",
    "e_body_eff_mean", "e_body_eff_disp", "e_body_rng_mean",
    "e_body_rng_disp", "e_opp_wick_mean", "e_opp_wick_disp",
    "e_trend_flow", "e_path_flow", "e_dir_flow", "e_ha_flow",
)
RANK_RAW = (
    "stop_dist_atr", "fast_body_rng", "std_body_rng", "slow_body_rng",
    "adx28_rel", "di14_signed", "ema8_21_signed", "path_eff4_rel",
    "path_eff12_rel", "flip8", "m15_body_rng", "m30_body_rng",
    "h1_body_rng",
)
RANK_FEATURES = tuple(f"rk_{name}" for name in RANK_RAW)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_event_decision(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values.astype(str).str.replace(".", "-", regex=False))


def sample_std3(a: pd.Series, b: pd.Series, c: pd.Series) -> pd.Series:
    mean = (a + b + c) / 3.0
    return np.sqrt(((a - mean) ** 2 + (b - mean) ** 2 + (c - mean) ** 2) / 2.0)


def build_v10_features(universe: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Reproduce the 38 raw, 33 engineered, and 13 prior-rank coordinates."""
    frame = universe.sort_values("decision").copy()
    for name in RAW_FEATURES:
        if name not in frame.columns:
            raise RuntimeError(f"missing V10 raw feature: {name}")

    x = frame
    x["e_log_stop"] = np.log1p(np.maximum(x["stop_dist_atr"], 0.0))
    x["e_fast_body"] = x["fast_body_rng"]
    x["e_ha_align"] = (x["std_align"] + x["slow_align"]) / 2.0
    x["e_ha_disagree"] = (x["std_align"] != x["slow_align"]).astype(float)
    x["e_ha_body_mean"] = x[["fast_body_rng", "std_body_rng", "slow_body_rng"]].mean(axis=1)
    x["e_ha_body_disp"] = sample_std3(x["fast_body_rng"], x["std_body_rng"], x["slow_body_rng"])
    x["e_adx"] = x["adx28_rel"]
    x["e_di_mean"] = (x["di14_signed"] + x["di28_signed"]) / 2.0
    x["e_di_disp"] = (x["di14_signed"] - x["di28_signed"]).abs()
    x["e_ema"] = x["ema8_21_signed"]
    x["e_ema_slope"] = x["ema8_slope"]
    x["e_path_mean"] = (x["path_eff4_rel"] + x["path_eff12_rel"]) / 2.0
    x["e_path_ratio"] = x["path_eff4_rel"] / (x["path_eff12_rel"].abs() + 1e-6)
    x["e_flip_mean"] = x[["flip4", "flip8", "flip12"]].mean(axis=1)
    x["e_flip_accel"] = x["flip4"] - x["flip12"]
    triples = {
        "align": ("m15_aligned", "m30_aligned", "h1_aligned"),
        "transition": ("m15_transition", "m30_transition", "h1_transition"),
        "streak": ("m15_streak", "m30_streak", "h1_streak"),
        "body_sum": ("m15_body_sum_atr", "m30_body_sum_atr", "h1_body_sum_atr"),
        "body_eff": ("m15_body_eff", "m30_body_eff", "h1_body_eff"),
        "body_rng": ("m15_body_rng", "m30_body_rng", "h1_body_rng"),
        "opp_wick": ("m15_opp_wick", "m30_opp_wick", "h1_opp_wick"),
    }
    for prefix, (a, b, c) in triples.items():
        x[f"e_{prefix}_mean"] = (x[a] + x[b] + x[c]) / 3.0
        x[f"e_{prefix}_disp"] = sample_std3(x[a], x[b], x[c])
    x["e_trend_flow"] = x["e_adx"] * x["e_body_rng_mean"]
    x["e_path_flow"] = x["e_path_mean"] * x["e_body_rng_mean"]
    x["e_dir_flow"] = x["e_di_mean"] * x["e_body_rng_mean"]
    x["e_ha_flow"] = x["e_ha_body_mean"] * x["e_body_rng_mean"]

    # Exact EA order: prior-only, stage/side-local, 360 observations, then push current.
    histories: dict[tuple[int, int, str], list[float]] = {}
    rank_values = {name: np.full(len(x), 0.5, dtype=float) for name in RANK_FEATURES}
    for pos, (_, row) in enumerate(x.iterrows()):
        stage = 1 if int(row["k"]) <= 1 else (2 if int(row["k"]) == 2 else 3)
        direction = int(row["dir"])
        for raw, rank in zip(RANK_RAW, RANK_FEATURES):
            key = (stage, direction, raw)
            history = histories.setdefault(key, [])
            value = float(row[raw])
            if len(history) >= 40:
                rank_values[rank][pos] = (sum(v <= value for v in history) + 0.5) / (len(history) + 1.0)
            history.append(value)
            if len(history) > 360:
                del history[0]
    for rank, values in rank_values.items():
        x[rank] = values
    features = list(RAW_FEATURES + ENGINEERED_FEATURES + RANK_FEATURES)
    return x, features


def assert_unique(frame: pd.DataFrame, keys: list[str], name: str) -> None:
    duplicates = int(frame.duplicated(keys).sum())
    if duplicates:
        raise RuntimeError(f"{name} has {duplicates} duplicate keys at {keys}")


def load_inputs(
    universe_path: Path,
    episodes_path: Path,
    events_path: Path,
    selection_path: Path,
    registry_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    universe = pd.read_csv(universe_path)
    episodes = pd.read_csv(episodes_path)
    events = pd.read_csv(events_path)
    selection = pd.read_csv(selection_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    universe["decision"] = pd.to_datetime(universe["decision"])
    episodes["decision"] = pd.to_datetime(episodes["decision"])
    events["decision"] = normalize_event_decision(events["decision"])
    selection["decision"] = pd.to_datetime(selection["decision"])
    assert_unique(universe, ["decision", "k"], "universe")
    assert_unique(episodes, ["decision", "k"], "episodes")
    assert_unique(events, ["decision", "k"], "events")
    assert_unique(selection, ["decision", "k"], "selection")

    featured, v10_features = build_v10_features(universe)
    if v10_features != list(registry["features"]):
        raise RuntimeError("reconstructed V10 feature order does not match FEATURE_REGISTRY")
    k1 = featured[featured["k"].eq(1)].copy()
    k1["label_available_at"] = pd.to_datetime(k1["label_available_at"])
    data = episodes.merge(
        k1[["decision", "k", "dir", "year", "label_available_at"] + v10_features],
        on=["decision", "k", "dir", "year"],
        how="left",
        validate="one_to_one",
    )
    if len(data) != len(episodes) or data[v10_features].isna().all(axis=1).any():
        raise RuntimeError("episode-to-V10 feature join lost coverage")

    event_columns = [
        "decision", "k", "event", "score", "q50", "q75", "r4_weight",
        "p_stop", "mu_nonstop", "EV", "feedback_R", "r7g_weight",
    ]
    data = data.merge(events[event_columns], on=["decision", "k"], how="left", validate="one_to_one")
    data["selected_r7g"] = data["r7g_weight"].gt(0) & data["event"].ne("SHADOW_WARMUP")

    expected = selection[(selection["k"].eq(1)) & (selection["selected_r7g"].eq(1))]
    expected_keys = set(zip(expected["decision"], expected["k"]))
    actual = data[data["selected_r7g"]]
    actual_keys = set(zip(actual["decision"], actual["k"]))
    if expected_keys != actual_keys:
        raise RuntimeError(
            "selected R7G parity failed: "
            f"expected={len(expected_keys)} actual={len(actual_keys)} "
            f"missing={len(expected_keys-actual_keys)} extra={len(actual_keys-expected_keys)}"
        )

    invariant_rows: list[dict[str, object]] = []
    for minute in (60, 120, 180):
        valid = data[f"b{minute}_valid"].eq(1)
        failures = int((valid & data[f"b{minute}_R"].isna()).sum())
        guard_conflict = int((valid & data[f"b{minute}_guard_touched_before_entry"].eq(1)).sum())
        stop_domain = int((valid & ~data[f"b{minute}_stop_hit"].isin([0, 1])).sum())
        if failures or guard_conflict or stop_domain:
            raise RuntimeError(f"checkpoint {minute} invariant failed")
        invariant_rows.append({
            "checkpoint": minute,
            "available": int(data[f"b{minute}_available"].eq(1).sum()),
            "valid": int(valid.sum()),
            "guard_failed": int(data[f"b{minute}_guard_touched_before_entry"].eq(1).sum()),
            "valid_missing_R": failures,
            "valid_guard_conflict": guard_conflict,
            "valid_stop_domain_failure": stop_domain,
        })

    quality = {
        "grain": "one FAST k1 Child per decision timestamp",
        "row_counts": {
            "universe_all_k": int(len(universe)),
            "universe_k1": int(len(k1)),
            "episodes": int(len(episodes)),
            "events": int(len(events)),
            "joined_k1": int(len(data)),
            "selected_r7g": int(data["selected_r7g"].sum()),
            "selection_expected": int(len(expected)),
        },
        "join_coverage": float(data[v10_features[0]].notna().mean()),
        "selected_key_parity": len(expected_keys) == len(actual_keys) == len(expected_keys & actual_keys),
        "checkpoint_invariants": invariant_rows,
        "feature_registry_match": True,
        "event_head_coverage_by_year": {
            str(int(year)): int(group["p_stop"].notna().sum())
            for year, group in data.groupby("year", sort=True)
        },
        "causal_process_contract": {
            "allowed_at_decision": [
                "causal_context", "prior_nha_explanation", "same_h4_consumed",
                "same_h1_consumed", "h4_route_open", "h1_route_open",
                "completed decision-H4 Wave coordinates", "prev_run_len",
            ],
            "explicitly_forbidden": [
                "immediate_nha", "next_run_length", "one_bar_triplet_rotation",
                "short_run_triplet_rotation", "pair_net_progress",
                "journey_net_progress", "route_still_open_after_nha",
                "nha_explanation", "L", "run_end_decision", "R", "stop_hit",
            ],
        },
    }
    return data.sort_values("decision").reset_index(drop=True), actual.copy(), quality


def process_feature_columns(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str], dict[int, list[str]]]:
    frame = data.copy()
    atr = (frame["entry"] - frame["stop"]).abs() / frame["stop_dist_atr"].replace(0, np.nan)
    direction = frame["dir"].astype(float)
    # Only coordinates known at the k1 decision are allowed here.  In the source
    # event ledger, immediate_nha, next_run_length, triplet labels, current
    # nha_explanation, and the post-run progress fields are explicit outcomes.
    static_numeric = [
        "same_h4_consumed", "same_h1_consumed", "h4_route_open", "h1_route_open",
        "nha_wave_efficiency", "nha_wave_settlement", "nha_wave_dispersion_atr",
        "nha_wave_favorable_mass", "nha_wave_entropy", "nha_fraction_beyond_prev_open",
        "nha_fraction_beyond_prev_close", "nha_close_beyond_prev_open_atr",
        "nha_density_median_beyond_prev_open_atr", "nha_body_atr", "nha_raw_return_atr",
        "nha_range_atr", "prev_run_len",
    ]
    for column in static_numeric:
        frame[f"proc_{column}"] = pd.to_numeric(frame[column], errors="coerce")
    frame["proc_nha_density_peak_rel"] = direction * (frame["nha_wave_density_peak"] - frame["entry"]) / atr
    frame["proc_nha_density_median_rel"] = direction * (frame["nha_wave_density_median"] - frame["entry"]) / atr
    process_base = [f"proc_{column}" for column in static_numeric] + [
        "proc_nha_density_peak_rel", "proc_nha_density_median_rel"
    ]

    category_columns: list[str] = []
    for source in ("causal_context", "prior_nha_explanation"):
        values = sorted(v for v in frame[source].dropna().astype(str).unique())
        for value in values:
            safe = "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower()
            column = f"proc_{source}_{safe}"
            frame[column] = frame[source].astype(str).eq(value).astype(float)
            category_columns.append(column)
    process_base.extend(category_columns)

    by_state: dict[int, list[str]] = {0: list(process_base)}
    prior_eff = frame["nha_wave_efficiency"]
    prior_settlement = frame["nha_wave_settlement"]
    prior_dispersion = frame["nha_wave_dispersion_atr"]
    prior_mass = frame["nha_wave_favorable_mass"]
    prior_entropy = frame["nha_wave_entropy"]
    prior_peak = frame["nha_wave_density_peak"]
    prior_median = frame["nha_wave_density_median"]
    accumulated = list(process_base)
    for minute in (60, 120, 180):
        key = f"b{minute}"
        columns: list[str] = []
        raw_names = (
            "available", "prefix_return_atr", "close_beyond_nha_close_atr",
            "fraction_beyond_nha_close", "wave_efficiency", "wave_settlement",
            "wave_dispersion_atr", "wave_favorable_mass", "wave_entropy",
        )
        for name in raw_names:
            column = f"proc_{key}_{name}"
            frame[column] = pd.to_numeric(frame[f"{key}_{name}"], errors="coerce")
            columns.append(column)
        frame[f"proc_{key}_density_peak_rel"] = direction * (frame[f"{key}_wave_density_peak"] - frame["entry"]) / atr
        frame[f"proc_{key}_density_median_rel"] = direction * (frame[f"{key}_wave_density_median"] - frame["entry"]) / atr
        frame[f"proc_{key}_efficiency_delta"] = frame[f"{key}_wave_efficiency"] - prior_eff
        frame[f"proc_{key}_settlement_delta"] = frame[f"{key}_wave_settlement"] - prior_settlement
        frame[f"proc_{key}_dispersion_delta"] = frame[f"{key}_wave_dispersion_atr"] - prior_dispersion
        frame[f"proc_{key}_mass_delta"] = frame[f"{key}_wave_favorable_mass"] - prior_mass
        frame[f"proc_{key}_entropy_delta"] = frame[f"{key}_wave_entropy"] - prior_entropy
        frame[f"proc_{key}_density_peak_delta_atr"] = direction * (frame[f"{key}_wave_density_peak"] - prior_peak) / atr
        frame[f"proc_{key}_density_median_delta_atr"] = direction * (frame[f"{key}_wave_density_median"] - prior_median) / atr
        columns.extend([
            f"proc_{key}_density_peak_rel", f"proc_{key}_density_median_rel",
            f"proc_{key}_efficiency_delta", f"proc_{key}_settlement_delta",
            f"proc_{key}_dispersion_delta", f"proc_{key}_mass_delta",
            f"proc_{key}_entropy_delta", f"proc_{key}_density_peak_delta_atr",
            f"proc_{key}_density_median_delta_atr",
        ])
        accumulated.extend(columns)
        by_state[minute] = list(accumulated)
        prior_eff = frame[f"{key}_wave_efficiency"]
        prior_settlement = frame[f"{key}_wave_settlement"]
        prior_dispersion = frame[f"{key}_wave_dispersion_atr"]
        prior_mass = frame[f"{key}_wave_favorable_mass"]
        prior_entropy = frame[f"{key}_wave_entropy"]
        prior_peak = frame[f"{key}_wave_density_peak"]
        prior_median = frame[f"{key}_wave_density_median"]
    return frame, process_base, by_state


@dataclass
class Ridge:
    alpha: float = RIDGE_ALPHA
    median: np.ndarray | None = None
    mean: np.ndarray | None = None
    scale: np.ndarray | None = None
    beta: np.ndarray | None = None

    def fit(self, x: pd.DataFrame, y: pd.Series) -> "Ridge":
        values = x.to_numpy(dtype=float)
        target = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float)
        keep = np.isfinite(target)
        values = values[keep]
        target = target[keep]
        if len(target) < MIN_TRAIN_ROWS:
            raise RuntimeError(f"insufficient training rows: {len(target)}")
        self.median = np.nanmedian(values, axis=0)
        self.median = np.where(np.isfinite(self.median), self.median, 0.0)
        values = np.where(np.isfinite(values), values, self.median)
        self.mean = values.mean(axis=0)
        self.scale = values.std(axis=0)
        self.scale = np.where(self.scale > 1e-9, self.scale, 1.0)
        z = (values - self.mean) / self.scale
        design = np.column_stack([np.ones(len(z)), z])
        penalty = np.eye(design.shape[1]) * self.alpha
        penalty[0, 0] = 0.0
        self.beta = np.linalg.solve(design.T @ design + penalty, design.T @ target)
        return self

    def predict(self, x: pd.DataFrame) -> np.ndarray:
        if self.beta is None or self.median is None or self.mean is None or self.scale is None:
            raise RuntimeError("model not fitted")
        values = x.to_numpy(dtype=float)
        values = np.where(np.isfinite(values), values, self.median)
        z = (values - self.mean) / self.scale
        return np.column_stack([np.ones(len(z)), z]) @ self.beta


@dataclass
class ActionModel:
    valid: Ridge
    stop: Ridge
    mu: Ridge

    def predict(self, x: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        p_valid = np.clip(self.valid.predict(x), 0.0, 1.0)
        p_stop = np.clip(self.stop.predict(x), 0.0, 1.0)
        mu = self.mu.predict(x)
        ev = p_valid * (-p_stop + (1.0 - p_stop) * mu)
        return p_valid, p_stop, mu, ev


def action_columns(action: int) -> tuple[pd.Series | str, str, str]:
    if action == 0:
        return "__always_valid__", "stop_hit", "R"
    return f"b{action}_valid", f"b{action}_stop_hit", f"b{action}_R"


def fit_action_model(train: pd.DataFrame, columns: list[str], action: int) -> ActionModel:
    valid_column, stop_column, r_column = action_columns(action)
    if valid_column == "__always_valid__":
        valid = pd.Series(1.0, index=train.index)
    else:
        valid = pd.to_numeric(train[valid_column], errors="coerce").fillna(0.0)
    valid_model = Ridge().fit(train[columns], valid)
    funded = train[valid.eq(1)].copy()
    stop = pd.to_numeric(funded[stop_column], errors="coerce")
    stop_model = Ridge().fit(funded[columns], stop)
    non_stop = funded[stop.eq(0)].copy()
    mu_model = Ridge().fit(non_stop[columns], pd.to_numeric(non_stop[r_column], errors="coerce"))
    return ActionModel(valid_model, stop_model, mu_model)


def state_reachable(frame: pd.DataFrame, state: int) -> pd.Series:
    if state == 0:
        return pd.Series(True, index=frame.index)
    return frame[f"b{state}_valid"].eq(1)


def build_models(
    train: pd.DataFrame,
    columns_by_state: dict[int, list[str]],
) -> dict[tuple[int, int], ActionModel]:
    models: dict[tuple[int, int], ActionModel] = {}
    for state in CHECKPOINTS:
        state_train = train[state_reachable(train, state)].copy()
        for action in CHECKPOINTS:
            if action < state:
                continue
            models[(state, action)] = fit_action_model(state_train, columns_by_state[state], action)
    return models


def predict_state_actions(
    models: dict[tuple[int, int], ActionModel],
    frame: pd.DataFrame,
    state: int,
    columns: list[str],
) -> dict[int, dict[str, np.ndarray]]:
    output: dict[int, dict[str, np.ndarray]] = {}
    for action in CHECKPOINTS:
        if action < state:
            continue
        p_valid, p_stop, mu, ev = models[(state, action)].predict(frame[columns])
        output[action] = {
            "p_valid": p_valid,
            "p_stop": p_stop,
            "mu": mu,
            "ev": ev,
            "stop_burden": p_valid * p_stop,
        }
    return output


def next_checkpoint(state: int) -> int | None:
    idx = CHECKPOINTS.index(state)
    return CHECKPOINTS[idx + 1] if idx + 1 < len(CHECKPOINTS) else None


def run_policy(
    test: pd.DataFrame,
    predictions: dict[int, dict[int, dict[str, np.ndarray]]],
    stop_cost: float,
    view: str,
    test_year: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    test = test.reset_index(drop=True)
    for i, row in test.iterrows():
        state = 0
        trace: list[str] = []
        funded_action: int | None = None
        terminal_reason = "UNRESOLVED"
        while state is not None:
            if state > 0:
                available = row.get(f"b{state}_available", 0)
                valid = row.get(f"b{state}_valid", np.nan)
                guard = row.get(f"b{state}_guard_touched_before_entry", np.nan)
                if available != 1:
                    trace.append(f"{state}:NO_OBSERVATION")
                    state = next_checkpoint(state)
                    continue
                if valid != 1:
                    terminal_reason = "GUARD_DIED" if guard == 1 else "ACTION_UNAVAILABLE"
                    trace.append(f"{state}:{terminal_reason}")
                    break
            state_predictions = predictions[state]
            available_actions = [a for a in CHECKPOINTS if a >= state]
            utilities = {
                action: float(state_predictions[action]["ev"][i])
                - stop_cost * float(state_predictions[action]["stop_burden"][i])
                for action in available_actions
            }
            best = max(available_actions, key=lambda action: (utilities[action], -action))
            if utilities[best] <= 0.0:
                terminal_reason = "MODEL_SKIP"
                trace.append(f"{state}:SKIP")
                break
            if best == state:
                funded_action = state
                terminal_reason = "FUNDED"
                trace.append(f"{state}:FUND")
                break
            trace.append(f"{state}:WAIT_FOR_{best}")
            state = next_checkpoint(state)

        result = {
            "view": view,
            "test_year": test_year,
            "stop_cost": stop_cost,
            "decision": row["decision"],
            "signal_id": row["signal_id"],
            "dir": int(row["dir"]),
            "L": int(row["L"]),
            "r7g_weight": float(row["r7g_weight"]),
            "funded_action": "SKIP" if funded_action is None else f"FUND_{funded_action}",
            "terminal_reason": terminal_reason,
            "trace": "|".join(trace),
            "traded": int(funded_action is not None),
            "entry_time_policy": pd.NaT,
            "R_policy": 0.0,
            "stop_policy": 0,
        }
        if funded_action is not None:
            if funded_action == 0:
                result["entry_time_policy"] = row["entry_time"]
                result["R_policy"] = float(row["R"])
                result["stop_policy"] = int(row["stop_hit"])
            else:
                result["entry_time_policy"] = row[f"b{funded_action}_entry_time"]
                result["R_policy"] = float(row[f"b{funded_action}_R"])
                result["stop_policy"] = int(row[f"b{funded_action}_stop_hit"])
        rows.append(result)
    return pd.DataFrame(rows)


def equity_path(values: Iterable[float], risk_fraction: float) -> tuple[float, float]:
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in values:
        equity *= max(1e-12, 1.0 + risk_fraction * float(value))
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, 1.0 - equity / peak)
    return float(equity), float(max_drawdown)


def equal_drawdown_risk(values: np.ndarray, target_drawdown: float) -> float:
    low, high = 0.0, 0.10
    if equity_path(values, high)[1] < target_drawdown:
        return math.nan
    for _ in range(100):
        middle = (low + high) / 2.0
        if equity_path(values, middle)[1] < target_drawdown:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def max_stop_streak(values: Iterable[int]) -> int:
    best = current = 0
    for value in values:
        current = current + 1 if int(value) == 1 else 0
        best = max(best, current)
    return best


def summarize_policy(ledger: pd.DataFrame, selected: pd.DataFrame, policy: str, scope: str) -> dict[str, object]:
    traded = ledger[ledger["traded"].eq(1)].copy()
    traded["entry_time_policy"] = pd.to_datetime(traded["entry_time_policy"])
    traded = traded.sort_values("entry_time_policy")
    weighted = traded["R_policy"] * traded["r7g_weight"]
    positive_tail = traded.loc[traded["L"].ge(6), "R_policy"].clip(lower=0) * traded.loc[traded["L"].ge(6), "r7g_weight"]
    baseline_tail = selected.loc[selected["L"].ge(6), "R"].clip(lower=0) * selected.loc[selected["L"].ge(6), "r7g_weight"]
    ending, drawdown = equity_path(weighted.to_numpy(dtype=float), 0.01)
    positives = weighted[weighted > 0].sort_values(ascending=False)
    top10_share = float(positives.head(10).sum() / positives.sum()) if positives.sum() > 0 else math.nan
    return {
        "scope": scope,
        "policy": policy,
        "candidates": int(len(selected)),
        "trades": int(len(traded)),
        "trade_retention": float(len(traded) / len(selected)) if len(selected) else math.nan,
        "hard_sl": int(traded["stop_policy"].sum()),
        "hard_sl_rate": float(traded["stop_policy"].mean()) if len(traded) else math.nan,
        "wins": int(traded["R_policy"].gt(0).sum()),
        "win_rate": float(traded["R_policy"].gt(0).mean()) if len(traded) else math.nan,
        "structural_R": float(traded["R_policy"].sum()),
        "r7g_weighted_R": float(weighted.sum()),
        "max_stop_streak": max_stop_streak(traded["stop_policy"]),
        "ending_equity_1pct": ending,
        "max_drawdown_1pct": drawdown,
        "L6_positive_weighted_R_retention": float(positive_tail.sum() / baseline_tail.sum()) if baseline_tail.sum() > 0 else math.nan,
        "top10_positive_weighted_R_share": top10_share,
    }


def baseline_ledger(selected: pd.DataFrame, action: int, scope: str) -> pd.DataFrame:
    rows = []
    for _, row in selected.iterrows():
        if action == 0:
            valid = True
            entry_time = row["entry_time"]
            r_value = row["R"]
            stop = row["stop_hit"]
        else:
            valid = row[f"b{action}_valid"] == 1
            entry_time = row[f"b{action}_entry_time"] if valid else pd.NaT
            r_value = row[f"b{action}_R"] if valid else 0.0
            stop = row[f"b{action}_stop_hit"] if valid else 0
        rows.append({
            "view": "BASELINE",
            "test_year": int(row["year"]),
            "stop_cost": math.nan,
            "decision": row["decision"],
            "signal_id": row["signal_id"],
            "dir": int(row["dir"]),
            "L": int(row["L"]),
            "r7g_weight": float(row["r7g_weight"]),
            "funded_action": "SKIP" if not valid else f"FUND_{action}",
            "terminal_reason": "BASELINE",
            "trace": scope,
            "traded": int(valid),
            "entry_time_policy": entry_time,
            "R_policy": float(r_value),
            "stop_policy": int(stop),
        })
    return pd.DataFrame(rows)


def prediction_diagnostics(
    test: pd.DataFrame,
    predictions: dict[int, dict[int, dict[str, np.ndarray]]],
    view: str,
    test_year: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for state in CHECKPOINTS:
        reachable = state_reachable(test, state).to_numpy(dtype=bool)
        for action in CHECKPOINTS:
            if action < state:
                continue
            valid_col, stop_col, r_col = action_columns(action)
            actual_valid = np.ones(len(test)) if valid_col == "__always_valid__" else pd.to_numeric(test[valid_col], errors="coerce").fillna(0).to_numpy()
            actual_stop = pd.to_numeric(test[stop_col], errors="coerce").fillna(0).to_numpy()
            actual_r = pd.to_numeric(test[r_col], errors="coerce").fillna(0).to_numpy()
            actual_ev = np.where(actual_valid == 1, actual_r, 0.0)
            pred = predictions[state][action]
            mask = reachable
            if mask.sum() == 0:
                continue
            pearson = np.corrcoef(pred["ev"][mask], actual_ev[mask])[0, 1] if np.std(pred["ev"][mask]) > 0 and np.std(actual_ev[mask]) > 0 else math.nan
            rows.append({
                "view": view,
                "test_year": test_year,
                "state": state,
                "action": action,
                "rows": int(mask.sum()),
                "actual_valid_rate": float(actual_valid[mask].mean()),
                "predicted_valid_mean": float(pred["p_valid"][mask].mean()),
                "actual_stop_burden": float((actual_valid[mask] * actual_stop[mask]).mean()),
                "predicted_stop_burden": float(pred["stop_burden"][mask].mean()),
                "actual_action_R_mean": float(actual_ev[mask].mean()),
                "predicted_action_EV_mean": float(pred["ev"][mask].mean()),
                "action_EV_pearson": float(pearson),
            })
    return rows


def add_equal_drawdown(summary: pd.DataFrame, ledgers: dict[str, pd.DataFrame]) -> pd.DataFrame:
    output = summary.copy()
    output["equal_drawdown_risk_fraction"] = math.nan
    output["equal_drawdown_ending_equity"] = math.nan
    for scope in output["scope"].unique():
        baseline_row = output[(output["scope"].eq(scope)) & (output["policy"].eq("IMMEDIATE"))]
        if baseline_row.empty:
            continue
        target = float(baseline_row.iloc[0]["max_drawdown_1pct"])
        for idx, row in output[output["scope"].eq(scope)].iterrows():
            ledger = ledgers[f"{scope}|{row['policy']}"]
            traded = ledger[ledger["traded"].eq(1)].copy()
            traded["entry_time_policy"] = pd.to_datetime(traded["entry_time_policy"])
            traded = traded.sort_values("entry_time_policy")
            values = (traded["R_policy"] * traded["r7g_weight"]).to_numpy(dtype=float)
            risk = equal_drawdown_risk(values, target)
            ending = equity_path(values, risk)[0] if np.isfinite(risk) else math.nan
            output.loc[idx, "equal_drawdown_risk_fraction"] = risk
            output.loc[idx, "equal_drawdown_ending_equity"] = ending
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--selection-ledger", type=Path, required=True)
    parser.add_argument("--feature-registry", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    data, selected_raw, quality = load_inputs(
        args.universe, args.episodes, args.events, args.selection_ledger, args.feature_registry
    )
    data, _, process_by_state = process_feature_columns(data)
    selected_keys = set(zip(selected_raw["decision"], selected_raw["k"]))
    selected = data[[key in selected_keys for key in zip(data["decision"], data["k"])]].copy()
    selected = selected[selected["selected_r7g"]].copy()

    base_features = list(RAW_FEATURES + ENGINEERED_FEATURES + RANK_FEATURES)
    head_features = ["score", "p_stop", "mu_nonstop", "EV", "feedback_R"]
    data["feedback_R_available"] = data["feedback_R"].notna().astype(float)
    selected["feedback_R_available"] = selected["feedback_R"].notna().astype(float)
    head_features.append("feedback_R_available")
    views = {
        "V10_84": {state: list(base_features) for state in CHECKPOINTS},
        "V10_84_PROCESS": {state: list(base_features) + process_by_state[state] for state in CHECKPOINTS},
        "V10_84_PROCESS_HEADS": {state: list(base_features) + process_by_state[state] + head_features for state in CHECKPOINTS},
    }

    all_ledgers: list[pd.DataFrame] = []
    diagnostic_rows: list[dict[str, object]] = []
    model_audit: list[dict[str, object]] = []
    for view, columns_by_state in views.items():
        for test_year in (2024, 2025, 2026):
            if view.endswith("HEADS") and test_year == 2024:
                continue
            test = selected[selected["year"].eq(test_year)].copy().reset_index(drop=True)
            if test.empty:
                continue
            test_cutoff = pd.Timestamp(test["decision"].min())
            train = data[
                data["year"].lt(test_year)
                & data["label_available_at"].lt(test_cutoff)
            ].copy()
            if view.endswith("HEADS"):
                train = train[train["p_stop"].notna()].copy()
            models = build_models(train, columns_by_state)
            predictions = {
                state: predict_state_actions(models, test, state, columns_by_state[state])
                for state in CHECKPOINTS
            }
            diagnostic_rows.extend(prediction_diagnostics(test, predictions, view, test_year))
            model_audit.append({
                "view": view,
                "test_year": test_year,
                "train_start": int(train["year"].min()),
                "train_end": int(train["year"].max()),
                "test_cutoff": str(test_cutoff),
                "train_rows": int(len(train)),
                "test_selected_rows": int(len(test)),
                "feature_count_state0": len(columns_by_state[0]),
                "feature_count_state180": len(columns_by_state[180]),
                "ridge_alpha": RIDGE_ALPHA,
            })
            for stop_cost in STOP_COSTS:
                all_ledgers.append(run_policy(test, predictions, stop_cost, view, test_year))

    policy_ledger = pd.concat(all_ledgers, ignore_index=True)
    summaries: list[dict[str, object]] = []
    ledgers: dict[str, pd.DataFrame] = {}
    scopes = {
        "2024_2026": selected[selected["year"].isin([2024, 2025, 2026])].copy(),
        "2025_2026": selected[selected["year"].isin([2025, 2026])].copy(),
    }
    for scope, scoped_selected in scopes.items():
        years = set(scoped_selected["year"].astype(int))
        for action, name in ((0, "IMMEDIATE"), (60, "WAIT_60_ALL"), (120, "WAIT_120_ALL"), (180, "WAIT_180_ALL")):
            ledger = baseline_ledger(scoped_selected, action, scope)
            ledgers[f"{scope}|{name}"] = ledger
            summaries.append(summarize_policy(ledger, scoped_selected, name, scope))
        for (view, stop_cost), group in policy_ledger[
            policy_ledger["test_year"].isin(years)
        ].groupby(["view", "stop_cost"], sort=True):
            if view.endswith("HEADS") and 2024 in years:
                continue
            name = f"{view}_SC{stop_cost:.2f}"
            ledger = group.copy()
            ledgers[f"{scope}|{name}"] = ledger
            summaries.append(summarize_policy(ledger, scoped_selected, name, scope))
    summary = add_equal_drawdown(pd.DataFrame(summaries), ledgers)

    baseline_by_scope = summary[summary["policy"].eq("IMMEDIATE")].set_index("scope")
    summary["hard_sl_reduction"] = summary.apply(
        lambda row: 1.0 - row["hard_sl"] / baseline_by_scope.loc[row["scope"], "hard_sl"], axis=1
    )
    summary["weighted_R_retention"] = summary.apply(
        lambda row: row["r7g_weighted_R"] / baseline_by_scope.loc[row["scope"], "r7g_weighted_R"], axis=1
    )

    slices: list[dict[str, object]] = []
    for scope, scoped_selected in scopes.items():
        for policy in summary.loc[summary["scope"].eq(scope), "policy"]:
            ledger = ledgers[f"{scope}|{policy}"]
            for year, candidate_group in scoped_selected.groupby("year", sort=True):
                group = ledger[ledger["test_year"].eq(int(year))]
                row = summarize_policy(group, candidate_group, policy, f"YEAR_{int(year)}")
                row["parent_scope"] = scope
                slices.append(row)
            for direction, candidate_group in scoped_selected.groupby("dir", sort=True):
                group = ledger[ledger["dir"].eq(int(direction))]
                label = "LONG" if int(direction) > 0 else "SHORT"
                row = summarize_policy(group, candidate_group, policy, f"SIDE_{label}")
                row["parent_scope"] = scope
                slices.append(row)

    action_counts = (
        policy_ledger.groupby(["view", "stop_cost", "test_year", "funded_action", "terminal_reason"], dropna=False)
        .size().reset_index(name="rows")
    )
    outputs = {
        "policy_summary": args.out_dir / "V11_REASSEMBLY_STAGE1_POLICY_SUMMARY.csv",
        "policy_slices": args.out_dir / "V11_REASSEMBLY_STAGE1_POLICY_SLICES.csv",
        "policy_ledger": args.out_dir / "V11_REASSEMBLY_STAGE1_POLICY_LEDGER.csv",
        "action_counts": args.out_dir / "V11_REASSEMBLY_STAGE1_ACTION_COUNTS.csv",
        "prediction_diagnostics": args.out_dir / "V11_REASSEMBLY_STAGE1_PREDICTION_DIAGNOSTICS.csv",
        "model_audit": args.out_dir / "V11_REASSEMBLY_STAGE1_MODEL_AUDIT.csv",
        "data_quality": args.out_dir / "V11_REASSEMBLY_STAGE1_DATA_QUALITY.json",
    }
    summary.to_csv(outputs["policy_summary"], index=False)
    pd.DataFrame(slices).to_csv(outputs["policy_slices"], index=False)
    policy_ledger.to_csv(outputs["policy_ledger"], index=False)
    action_counts.to_csv(outputs["action_counts"], index=False)
    pd.DataFrame(diagnostic_rows).to_csv(outputs["prediction_diagnostics"], index=False)
    pd.DataFrame(model_audit).to_csv(outputs["model_audit"], index=False)
    outputs["data_quality"].write_text(json.dumps(quality, indent=2), encoding="utf-8")

    manifest = {
        "status": "CONSUMED_DEVELOPMENT_STAGE1_ONLY",
        "authority": "NO TRADE, WAIT, MODEL, SIZING, OR PRODUCTION AUTHORITY",
        "question": "Can V10 components select sequential capital-funding actions out of chronological sample?",
        "model": {
            "family": "fixed ridge decomposition",
            "ridge_alpha": RIDGE_ALPHA,
            "stop_cost_frontier": list(STOP_COSTS),
            "checkpoints": list(CHECKPOINTS),
            "selection": "no winning stop cost or feature view is promoted",
        },
        "input_sha256": {
            "universe": sha256_file(args.universe),
            "episodes": sha256_file(args.episodes),
            "events": sha256_file(args.events),
            "selection_ledger": sha256_file(args.selection_ledger),
            "feature_registry": sha256_file(args.feature_registry),
        },
        "output_sha256": {key: sha256_file(path) for key, path in outputs.items()},
    }
    manifest_path = args.out_dir / "V11_REASSEMBLY_STAGE1_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nPOLICY SUMMARY")
    print(summary.sort_values(["scope", "hard_sl", "r7g_weighted_R"], ascending=[True, True, False]).to_string(index=False))


if __name__ == "__main__":
    main()
