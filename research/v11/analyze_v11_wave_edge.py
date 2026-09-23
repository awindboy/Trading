"""Test whether frozen Wave Candle coordinates add useful V10 R7G information.

This is a consumed-data representation diagnostic.  It compares two fixed
observation points without granting any trade authority:

1. the fully completed H4 Wave immediately before an R7G Child decision;
2. the forming H4 Wave at exactly +60 minutes, using completed M5 closes only.

For each observation point one fixed logistic model uses only the outer H4/HA
shell, and a second fixed model adds the Wave coordinates.  Outer-year tests
train only on earlier decisions whose labels were already available.  Fixed
q80/q90 score tails are economic diagnostics, not proposed thresholds.
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler


EXPECTED_M1_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
ACTIVE_START = pd.Timestamp("2024-10-01 00:00:00")
TEST_YEARS = (2025, 2026)
QUANTILES = (0.80, 0.90)

WAVE_FEATURES = [
    "wave_efficiency",
    "wave_settlement_child",
    "wave_dispersion_atr",
    "wave_close_density_ratio",
    "wave_peak_gap_atr",
    "wave_density_favorable_mass",
    "wave_entropy",
]

EVOLUTION_FEATURES = [
    "evo_efficiency_delta",
    "evo_settlement_delta",
    "evo_favorable_mass_delta",
    "evo_centroid_shift_atr",
]

COMPLETED_BASE = [
    "k",
    "r7g_weight",
    "outer_ha_body_aligned_atr",
    "outer_range_atr",
    "outer_close_location_aligned",
]

FORMING_BASE = [
    "k",
    "r7g_weight",
    "ha_margin_atr",
    "prefix_return_atr",
    "prefix_range_atr",
]

DANGER_ORIENTATION = {
    "wave_efficiency": -1.0,
    "wave_settlement_child": -1.0,
    "wave_dispersion_atr": 1.0,
    "wave_close_density_ratio": -1.0,
    "wave_peak_gap_atr": 1.0,
    "wave_density_favorable_mass": -1.0,
    "wave_entropy": 1.0,
    "evo_efficiency_delta": -1.0,
    "evo_settlement_delta": -1.0,
    "evo_favorable_mass_delta": -1.0,
    "evo_centroid_shift_atr": -1.0,
}


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_m1(path: Path) -> pd.DataFrame:
    source_hash = sha256_file(path)
    if source_hash.lower() != EXPECTED_M1_SHA256:
        raise ValueError(f"M1 SHA256 mismatch: {source_hash}")
    frame = pd.read_csv(
        path,
        sep="\t",
        usecols=["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"],
    )
    frame["ts"] = pd.to_datetime(
        frame["<DATE>"].astype(str) + " " + frame["<TIME>"].astype(str),
        format="%Y.%m.%d %H:%M:%S",
    )
    if not frame["ts"].is_monotonic_increasing or frame["ts"].duplicated().any():
        raise ValueError("M1 timestamps are not strictly chronological")
    frame = frame.rename(
        columns={"<OPEN>": "open", "<HIGH>": "high", "<LOW>": "low", "<CLOSE>": "close"}
    )
    frame["h4_start"] = frame["ts"].dt.floor("4h")
    frame["m5_start"] = frame["ts"].dt.floor("5min")
    return frame[["ts", "h4_start", "m5_start", "open", "high", "low", "close"]]


def build_market_state(m1: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    h4 = (
        m1.groupby("h4_start", sort=True)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            m1_rows=("ts", "size"),
        )
        .reset_index()
    )
    previous_close = h4["close"].shift(1)
    true_range = pd.concat(
        [
            h4["high"] - h4["low"],
            (h4["high"] - previous_close).abs(),
            (h4["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = np.full(len(h4), np.nan, dtype=float)
    if len(h4) >= 180:
        atr[179] = float(true_range.iloc[:180].mean())
        for i in range(180, len(h4)):
            atr[i] = (atr[i - 1] * 179.0 + float(true_range.iloc[i])) / 180.0
    h4["atr180"] = atr
    h4["causal_scale"] = h4["atr180"].shift(1)

    fast_close = (h4["open"] + h4["high"] + h4["low"] + 2.0 * h4["close"]) / 5.0
    fast_open = np.full(len(h4), np.nan, dtype=float)
    if len(h4):
        fast_open[0] = 0.5 * (float(h4.iloc[0]["open"]) + float(h4.iloc[0]["close"]))
        for i in range(1, len(h4)):
            fast_open[i] = 0.25 * fast_open[i - 1] + 0.75 * float(fast_close.iloc[i - 1])
    h4["fast_ha_open"] = fast_open
    h4["fast_ha_close"] = fast_close
    h4["fast_dir"] = np.where(fast_close >= fast_open, 1, -1)

    m5 = (
        m1.groupby("m5_start", sort=True)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            rows=("ts", "size"),
        )
        .reset_index()
    )
    m5["h4_start"] = m5["m5_start"].dt.floor("4h")
    return h4, m5


def wave_coordinates(
    closes: np.ndarray,
    raw_low: float,
    raw_high: float,
    ha_open: float,
    ha_close: float,
    scale: float,
    child_direction: int,
) -> dict[str, float]:
    if len(closes) == 0 or not np.isfinite(scale) or scale <= 0.0 or raw_high <= raw_low:
        return {name: np.nan for name in WAVE_FEATURES}

    path = float(np.abs(np.diff(np.r_[ha_open, closes])).sum())
    efficiency = abs(float(closes[-1]) - ha_open) / path if path > 1e-12 else 0.0
    settlement = float(np.mean(child_direction * (closes - ha_open) >= 0.0))
    dispersion = float(np.std(closes, ddof=0) / scale)

    steps = 48
    prices = np.linspace(raw_low, raw_high, steps + 1)
    span = raw_high - raw_low
    bandwidth = max(span / 48.0, float(np.std(closes, ddof=0)) * 0.10, 0.02)
    z = (prices[:, None] - closes[None, :]) / bandwidth
    density = np.exp(-0.5 * z * z).mean(axis=1)
    max_density = float(density.max())
    ratio = density / max_density if max_density > 0.0 else np.zeros_like(density)
    close_density = float(np.interp(ha_close, prices, ratio, left=ratio[0], right=ratio[-1]))
    peak_price = float(prices[int(np.argmax(density))])
    peak_gap = child_direction * (ha_close - peak_price) / scale
    density_sum = float(density.sum())
    favorable = child_direction * (prices - ha_open) >= 0.0
    favorable_mass = float(density[favorable].sum() / density_sum) if density_sum > 0.0 else np.nan
    probability = density / density_sum if density_sum > 0.0 else np.zeros_like(density)
    positive = probability[probability > 0.0]
    entropy = float(-(positive * np.log(positive)).sum() / np.log(len(prices)))

    return {
        "wave_efficiency": efficiency,
        "wave_settlement_child": settlement,
        "wave_dispersion_atr": dispersion,
        "wave_close_density_ratio": close_density,
        "wave_peak_gap_atr": peak_gap,
        "wave_density_favorable_mass": favorable_mass,
        "wave_entropy": entropy,
    }


def load_selected_children(universe_path: Path, events_path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    universe = pd.read_csv(
        universe_path,
        parse_dates=["decision", "entry_time", "exit_time", "label_available_at"],
    )
    events = pd.read_csv(events_path)
    events["decision"] = pd.to_datetime(events["decision"], format="%Y.%m.%d %H:%M")
    events = events[(events["decision"] >= ACTIVE_START) & (events["r7g_weight"] > 0)].copy()
    if events["decision"].duplicated().any():
        raise ValueError("duplicate positive-weight event decisions")
    events["dir_event"] = events["dir"].map({"LONG": 1, "SHORT": -1}).astype(int)
    selected = universe.merge(
        events[["decision", "dir_event", "k", "r7g_weight", "event"]],
        on="decision",
        how="inner",
        suffixes=("", "_event"),
        validate="one_to_one",
    )
    direction_mismatch = int((selected["dir"] != selected["dir_event"]).sum())
    k_mismatch = int((selected["k"] != selected["k_event"]).sum())
    if direction_mismatch or k_mismatch:
        raise ValueError(f"selected parity failed: direction={direction_mismatch}, k={k_mismatch}")
    audit = {
        "universe_rows": int(len(universe)),
        "positive_events_after_active_start": int(len(events)),
        "matched_resolved_children": int(len(selected)),
        "unmatched_events": int(len(events) - len(selected)),
        "direction_mismatches": direction_mismatch,
        "k_mismatches": k_mismatch,
    }
    return selected, audit


def completed_wave_rows(
    selected: pd.DataFrame,
    h4: pd.DataFrame,
    m5: pd.DataFrame,
) -> pd.DataFrame:
    h4_state = h4.set_index("h4_start")
    closes_by_h4 = {
        key: group.sort_values("m5_start")["close"].to_numpy(dtype=float)
        for key, group in m5.groupby("h4_start", sort=True)
    }
    rows: list[dict[str, object]] = []
    for child in selected.itertuples(index=False):
        wave_start = child.decision - pd.Timedelta(hours=4)
        if wave_start not in h4_state.index or wave_start not in closes_by_h4:
            continue
        state = h4_state.loc[wave_start]
        scale = float(state["causal_scale"])
        if not np.isfinite(scale) or scale <= 0.0:
            continue
        closes = closes_by_h4[wave_start]
        span = float(state["high"] - state["low"])
        close_location = 0.0 if span <= 0.0 else 2.0 * (float(state["fast_ha_close"]) - float(state["low"])) / span - 1.0
        row = {
            "signal_id": child.signal_id,
            "decision": child.decision,
            "year": child.year,
            "dir": child.dir,
            "k": child.k,
            "rid": child.rid,
            "r7g_weight": child.r7g_weight,
            "entry": child.entry,
            "stop": child.stop,
            "entry_time": child.entry_time,
            "exit_time": child.exit_time,
            "label_available_at": child.label_available_at,
            "stop_hit": child.stop_hit,
            "R": child.R,
            "pnl": child.pnl,
            "L": child.L,
            "wave_start": wave_start,
            "m5_count": int(len(closes)),
            "outer_ha_body_aligned_atr": child.dir * (float(state["fast_ha_close"]) - float(state["fast_ha_open"])) / scale,
            "outer_range_atr": span / scale,
            "outer_close_location_aligned": child.dir * close_location,
        }
        row.update(
            wave_coordinates(
                closes,
                float(state["low"]),
                float(state["high"]),
                float(state["fast_ha_open"]),
                float(state["fast_ha_close"]),
                scale,
                int(child.dir),
            )
        )
        rows.append(row)
    return pd.DataFrame(rows)


def forming_wave_rows(
    selected: pd.DataFrame,
    h4: pd.DataFrame,
    m1: pd.DataFrame,
    m5: pd.DataFrame,
) -> pd.DataFrame:
    h4_state = h4.set_index("h4_start")
    m1_groups = {key: group.sort_values("ts") for key, group in m1.groupby("h4_start", sort=True)}
    m5_groups = {key: group.sort_values("m5_start") for key, group in m5.groupby("h4_start", sort=True)}
    exact_open = m1.set_index("ts")["open"]
    rows: list[dict[str, object]] = []
    for child in selected.itertuples(index=False):
        start = child.decision
        checkpoint = start + pd.Timedelta(minutes=60)
        if start not in h4_state.index or start not in m1_groups or start not in m5_groups:
            continue
        if checkpoint not in exact_open.index:
            continue
        state = h4_state.loc[start]
        scale = float(state["causal_scale"])
        if not np.isfinite(scale) or scale <= 0.0:
            continue
        prefix_m1 = m1_groups[start]
        prefix_m1 = prefix_m1[prefix_m1["ts"] < checkpoint]
        prefix_m5 = m5_groups[start]
        prefix_m5 = prefix_m5[prefix_m5["m5_start"] < checkpoint]
        if prefix_m1.empty or prefix_m5.empty:
            continue
        o = float(prefix_m1.iloc[0]["open"])
        h = float(prefix_m1["high"].max())
        l = float(prefix_m1["low"].min())
        c = float(prefix_m1.iloc[-1]["close"])
        fast_open = float(state["fast_ha_open"])
        fast_close = (o + h + l + 2.0 * c) / 5.0
        closes = prefix_m5["close"].to_numpy(dtype=float)
        risk = abs(float(child.entry) - float(child.stop))
        checkpoint_open = float(exact_open.loc[checkpoint])
        alive = bool(child.entry_time < checkpoint and child.exit_time >= checkpoint)
        row = {
            "signal_id": child.signal_id,
            "decision": child.decision,
            "year": child.year,
            "dir": child.dir,
            "k": child.k,
            "rid": child.rid,
            "r7g_weight": child.r7g_weight,
            "entry": child.entry,
            "stop": child.stop,
            "entry_time": child.entry_time,
            "exit_time": child.exit_time,
            "label_available_at": child.label_available_at,
            "stop_hit": child.stop_hit,
            "R": child.R,
            "pnl": child.pnl,
            "L": child.L,
            "checkpoint_time": checkpoint,
            "checkpoint_open": checkpoint_open,
            "alive_at_checkpoint": alive,
            "early_exit_R": child.dir * (checkpoint_open - float(child.entry)) / max(risk, 1e-12),
            "m5_count": int(len(closes)),
            "ha_margin_atr": child.dir * (fast_close - fast_open) / scale,
            "prefix_return_atr": child.dir * (c - o) / scale,
            "prefix_range_atr": (h - l) / scale,
        }
        wave60 = wave_coordinates(closes, l, h, fast_open, fast_close, scale, int(child.dir))
        row.update(wave60)

        checkpoint30 = start + pd.Timedelta(minutes=30)
        prefix30_m1 = prefix_m1[prefix_m1["ts"] < checkpoint30]
        prefix30_m5 = prefix_m5[prefix_m5["m5_start"] < checkpoint30]
        if (
            not prefix30_m1.empty
            and not prefix30_m5.empty
            and len(closes) > len(prefix30_m5)
        ):
            o30 = float(prefix30_m1.iloc[0]["open"])
            h30 = float(prefix30_m1["high"].max())
            l30 = float(prefix30_m1["low"].min())
            c30 = float(prefix30_m1.iloc[-1]["close"])
            fast_close30 = (o30 + h30 + l30 + 2.0 * c30) / 5.0
            closes30 = prefix30_m5["close"].to_numpy(dtype=float)
            wave30 = wave_coordinates(
                closes30, l30, h30, fast_open, fast_close30, scale, int(child.dir)
            )
            row["evo_efficiency_delta"] = wave60["wave_efficiency"] - wave30["wave_efficiency"]
            row["evo_settlement_delta"] = wave60["wave_settlement_child"] - wave30["wave_settlement_child"]
            row["evo_favorable_mass_delta"] = (
                wave60["wave_density_favorable_mass"] - wave30["wave_density_favorable_mass"]
            )
            row["evo_centroid_shift_atr"] = int(child.dir) * (
                float(np.mean(closes[len(closes30) :])) - float(np.mean(closes30))
            ) / scale
        else:
            for feature in EVOLUTION_FEATURES:
                row[feature] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def model_pipeline(features: list[str]) -> Pipeline:
    prep = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scale", RobustScaler(quantile_range=(10, 90))),
                    ]
                ),
                features,
            )
        ],
        remainder="drop",
    )
    return Pipeline(
        [
            ("prep", prep),
            ("model", LogisticRegression(C=1.0, max_iter=2000, random_state=20260922)),
        ]
    )


def safe_auc(y: pd.Series, score: np.ndarray) -> float:
    return float(roc_auc_score(y, score)) if y.nunique() > 1 else np.nan


def score_outer_years(
    frame: pd.DataFrame,
    stage: str,
    base_features: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scored_parts: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    threshold_rows: list[dict[str, object]] = []
    augmented_features = base_features + WAVE_FEATURES
    for year in TEST_YEARS:
        boundary = pd.Timestamp(f"{year}-01-01")
        train = frame[(frame["decision"] < boundary) & (frame["label_available_at"] < boundary)].copy()
        test = frame[frame["year"] == year].copy()
        if stage == "FORMING_60M":
            train = train[train["alive_at_checkpoint"]].copy()
            test = test[test["alive_at_checkpoint"]].copy()
        if train.empty or test.empty or train["stop_hit"].nunique() < 2:
            continue
        scored = test.copy()
        model_definitions = [
            ("OUTER_ONLY", base_features),
            ("OUTER_PLUS_WAVE", augmented_features),
        ]
        if stage == "FORMING_60M":
            model_definitions.append(
                ("OUTER_PLUS_WAVE_EVOLUTION", augmented_features + EVOLUTION_FEATURES)
            )
        for model_name, features in model_definitions:
            model = model_pipeline(features)
            model.fit(train[features], train["stop_hit"].astype(int))
            train_score = model.predict_proba(train[features])[:, 1]
            test_score = model.predict_proba(test[features])[:, 1]
            scored[f"score_{model_name.lower()}"] = test_score
            y = test["stop_hit"].astype(int)
            metric_rows.append(
                {
                    "stage": stage,
                    "test_year": year,
                    "model": model_name,
                    "train_n": int(len(train)),
                    "test_n": int(len(test)),
                    "test_stops": int(y.sum()),
                    "stop_rate": float(y.mean()),
                    "roc_auc": safe_auc(y, test_score),
                    "average_precision": float(average_precision_score(y, test_score)),
                    "brier": float(brier_score_loss(y, test_score)),
                }
            )
            policy_model = (
                "OUTER_PLUS_WAVE_EVOLUTION" if stage == "FORMING_60M" else "OUTER_PLUS_WAVE"
            )
            if model_name == policy_model:
                for quantile in QUANTILES:
                    threshold_rows.append(
                        {
                            "stage": stage,
                            "test_year": year,
                            "quantile": quantile,
                            "threshold": float(np.quantile(train_score, quantile)),
                            "score_column": f"score_{model_name.lower()}",
                        }
                    )
        scored_parts.append(scored)
    return (
        pd.concat(scored_parts, ignore_index=True),
        pd.DataFrame(metric_rows),
        pd.DataFrame(threshold_rows),
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


def economic_policy_rows(
    full_frame: pd.DataFrame,
    scored: pd.DataFrame,
    thresholds: pd.DataFrame,
    stage: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for threshold_row in thresholds.itertuples(index=False):
        year = int(threshold_row.test_year)
        base = full_frame[full_frame["year"] == year].copy()
        score_column = str(threshold_row.score_column)
        score_map = scored[scored["year"] == year].set_index("signal_id")[score_column]
        base["score"] = base["signal_id"].map(score_map)
        action = base["score"].ge(float(threshold_row.threshold))
        if stage == "FORMING_60M":
            action &= base["alive_at_checkpoint"].fillna(False)
            policy_r = np.where(action, base["early_exit_R"], base["R"])
        else:
            policy_r = np.where(action, 0.0, base["R"])
        base["policy_R"] = policy_r
        base["policy_stop"] = base["stop_hit"].astype(bool) & ~action
        weight = base["r7g_weight"].astype(float)
        baseline_r = float((base["R"] * weight).sum())
        policy_weighted_r = float((base["policy_R"] * weight).sum())
        positive = base["R"] > 0.0
        tail = positive & (base["L"] >= 6)
        baseline_positive = float((base.loc[positive, "R"] * weight[positive]).sum())
        kept_positive = float((base.loc[positive, "policy_R"].clip(lower=0.0) * weight[positive]).sum())
        baseline_tail = float((base.loc[tail, "R"] * weight[tail]).sum())
        kept_tail = float((base.loc[tail, "policy_R"].clip(lower=0.0) * weight[tail]).sum())
        rows.append(
            {
                "stage": stage,
                "test_year": year,
                "quantile": float(threshold_row.quantile),
                "children": int(len(base)),
                "actions": int(action.sum()),
                "baseline_stops": int(base["stop_hit"].sum()),
                "policy_stops": int(base["policy_stop"].sum()),
                "stops_prevented": int((base["stop_hit"].astype(bool) & action).sum()),
                "baseline_max_stop_streak": max_true_streak(base.sort_values("decision")["stop_hit"]),
                "policy_max_stop_streak": max_true_streak(base.sort_values("decision")["policy_stop"]),
                "baseline_weighted_R": baseline_r,
                "policy_weighted_R": policy_weighted_r,
                "delta_weighted_R": policy_weighted_r - baseline_r,
                "positive_R_retention": kept_positive / baseline_positive if baseline_positive > 0.0 else np.nan,
                "L6plus_positive_R_retention": kept_tail / baseline_tail if baseline_tail > 0.0 else np.nan,
            }
        )
    return pd.DataFrame(rows)


def forming_policy_population(selected: pd.DataFrame, forming: pd.DataFrame) -> pd.DataFrame:
    """Keep every selected Child; missing +60m observations simply cannot act."""
    base_columns = [
        "signal_id",
        "decision",
        "year",
        "dir",
        "k",
        "rid",
        "r7g_weight",
        "entry",
        "stop",
        "entry_time",
        "exit_time",
        "label_available_at",
        "stop_hit",
        "R",
        "pnl",
        "L",
    ]
    observation = forming[["signal_id", "alive_at_checkpoint", "early_exit_R"]].copy()
    population = selected[base_columns].merge(
        observation, on="signal_id", how="left", validate="one_to_one"
    )
    population["alive_at_checkpoint"] = population["alive_at_checkpoint"].fillna(False)
    return population


def univariate_rows(frame: pd.DataFrame, stage: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    eligible = frame.copy()
    if stage == "FORMING_60M":
        eligible = eligible[eligible["alive_at_checkpoint"]].copy()
    features = WAVE_FEATURES + (EVOLUTION_FEATURES if stage == "FORMING_60M" else [])
    for period, subset in [("POOLED", eligible)]:
        for feature in features:
            clean = subset[[feature, "stop_hit"]].dropna()
            score = DANGER_ORIENTATION[feature] * clean[feature].to_numpy(dtype=float)
            rows.append(
                {
                    "stage": stage,
                    "period": period,
                    "direction": "ALL",
                    "feature": feature,
                    "danger_orientation": DANGER_ORIENTATION[feature],
                    "n": int(len(clean)),
                    "stops": int(clean["stop_hit"].sum()),
                    "roc_auc": safe_auc(clean["stop_hit"].astype(int), score),
                }
            )
    for (year, direction), subset in eligible.groupby(["year", "dir"], sort=True):
        for feature in features:
            clean = subset[[feature, "stop_hit"]].dropna()
            score = DANGER_ORIENTATION[feature] * clean[feature].to_numpy(dtype=float)
            rows.append(
                {
                    "stage": stage,
                    "period": str(int(year)),
                    "direction": "LONG" if int(direction) > 0 else "SHORT",
                    "feature": feature,
                    "danger_orientation": DANGER_ORIENTATION[feature],
                    "n": int(len(clean)),
                    "stops": int(clean["stop_hit"].sum()),
                    "roc_auc": safe_auc(clean["stop_hit"].astype(int), score),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    m1 = load_m1(args.m1)
    h4, m5 = build_market_state(m1)
    selected, selection_audit = load_selected_children(args.universe, args.events)

    completed = completed_wave_rows(selected, h4, m5)
    forming = forming_wave_rows(selected, h4, m1, m5)
    completed_scored, completed_metrics, completed_thresholds = score_outer_years(
        completed, "COMPLETED_PRE_ENTRY", COMPLETED_BASE
    )
    forming_scored, forming_metrics, forming_thresholds = score_outer_years(
        forming, "FORMING_60M", FORMING_BASE
    )

    model_metrics = pd.concat([completed_metrics, forming_metrics], ignore_index=True)
    thresholds = pd.concat([completed_thresholds, forming_thresholds], ignore_index=True)
    policies = pd.concat(
        [
            economic_policy_rows(completed, completed_scored, completed_thresholds, "COMPLETED_PRE_ENTRY"),
            economic_policy_rows(
                forming_policy_population(selected, forming),
                forming_scored,
                forming_thresholds,
                "FORMING_60M",
            ),
        ],
        ignore_index=True,
    )
    univariate = pd.concat(
        [
            univariate_rows(completed, "COMPLETED_PRE_ENTRY"),
            univariate_rows(forming, "FORMING_60M"),
        ],
        ignore_index=True,
    )

    outputs = {
        "completed_ledger": args.out_dir / "V11_COMPLETED_WAVE_LEDGER.csv",
        "forming_ledger": args.out_dir / "V11_FORMING_60M_WAVE_LEDGER.csv",
        "model_metrics": args.out_dir / "V11_WAVE_MODEL_COMPARISON.csv",
        "thresholds": args.out_dir / "V11_WAVE_PRIOR_THRESHOLDS.csv",
        "policies": args.out_dir / "V11_WAVE_POLICY_DIAGNOSTIC.csv",
        "univariate": args.out_dir / "V11_WAVE_UNIVARIATE_AUDIT.csv",
    }
    completed.to_csv(outputs["completed_ledger"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    forming.to_csv(outputs["forming_ledger"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    model_metrics.to_csv(outputs["model_metrics"], index=False)
    thresholds.to_csv(outputs["thresholds"], index=False)
    policies.to_csv(outputs["policies"], index=False)
    univariate.to_csv(outputs["univariate"], index=False)

    manifest = {
        "status": "CONSUMED_DATA_REPRESENTATION_DIAGNOSTIC_ONLY",
        "authority": "NO TRADE OR PRODUCTION AUTHORITY",
        "source_m1": str(args.m1.resolve()),
        "source_m1_sha256": sha256_file(args.m1),
        "source_universe": str(args.universe.resolve()),
        "source_universe_sha256": sha256_file(args.universe),
        "source_events": str(args.events.resolve()),
        "source_events_sha256": sha256_file(args.events),
        "selection_audit": selection_audit,
        "completed_rows": int(len(completed)),
        "forming_rows": int(len(forming)),
        "forming_alive_rows": int(forming["alive_at_checkpoint"].sum()),
        "test_years": list(TEST_YEARS),
        "fixed_quantiles": list(QUANTILES),
        "completed_base_features": COMPLETED_BASE,
        "forming_base_features": FORMING_BASE,
        "wave_features": WAVE_FEATURES,
        "evolution_features": EVOLUTION_FEATURES,
        "model": "RobustScaler(10,90) + LogisticRegression(C=1.0)",
        "training_rule": "decision and label_available_at strictly before test-year boundary",
        "outputs": {name: str(path.resolve()) for name, path in outputs.items()},
        "output_sha256": {name: sha256_file(path) for name, path in outputs.items()},
    }
    manifest_path = args.out_dir / "V11_WAVE_EDGE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps(manifest, indent=2))
    print("\nMODEL COMPARISON")
    print(model_metrics.to_string(index=False))
    print("\nPOLICY DIAGNOSTIC")
    print(policies.to_string(index=False))
    print("\nPOOLED UNIVARIATE")
    print(univariate[univariate["period"] == "POOLED"].to_string(index=False))


if __name__ == "__main__":
    main()
