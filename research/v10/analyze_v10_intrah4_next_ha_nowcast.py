"""Causal intrabar nowcast of the next FAST H4 HA direction.

This is a consumed-data research diagnostic, not strategy authority.

The experiment is deliberately narrower than the earlier next-HA studies:

* the target H4 bar has already started;
* every feature uses only raw M1 rows strictly before a fixed +60/+120/+180
  minute checkpoint;
* the target is whether that forming H4 finishes in the existing campaign
  direction (PHA) or opposite to it (NHA);
* H4 FAST HA open and the volatility scale are frozen from completed prior H4
  bars;
* models are fit on earlier years only, and labels must have become available
  before the outer-year boundary;
* the only model action comparator is a predeclared prior-score q90 warning.

The economic simulation closes only the newly entered Child at the checkpoint
M1 open.  It does not exit older campaign Children and does not change the
campaign clock.  A Child whose Hard SL was touched before the checkpoint is
dead and cannot be rescued.
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
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler


EXPECTED_M1_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
CHECKPOINT_MINUTES = (60, 120, 180)
TEST_YEARS = (2024, 2025, 2026)

FEATURES = [
    "ha_margin_atr",
    "prefix_return_atr",
    "prefix_range_atr",
    "favorable_excursion_atr",
    "adverse_excursion_atr",
    "close_location_aligned",
    "directional_path_efficiency",
    "retrace_from_favorable_atr",
    "ret_15_atr",
    "ret_30_atr",
    "ret_60_atr",
    "m5_aligned_fraction",
    "m5_transition_rate",
    "m5_signed_streak",
    "m5_body_efficiency",
    "prefix_coverage",
]


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
    return frame[["ts", "h4_start", "open", "high", "low", "close"]]


def build_h4_state(m1: pd.DataFrame) -> pd.DataFrame:
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

    fast_close = (h4["open"] + h4["high"] + h4["low"] + 2.0 * h4["close"]) / 5.0
    fast_open = np.full(len(h4), np.nan, dtype=float)
    if len(h4):
        fast_open[0] = 0.5 * (float(h4.iloc[0]["open"]) + float(h4.iloc[0]["close"]))
        for i in range(1, len(h4)):
            fast_open[i] = 0.25 * fast_open[i - 1] + 0.75 * float(fast_close.iloc[i - 1])
    h4["fast_ha_open"] = fast_open
    h4["fast_ha_close"] = fast_close
    h4["fast_dir"] = np.where(h4["fast_ha_close"] >= h4["fast_ha_open"], 1, -1)
    h4["causal_scale"] = h4["atr180"].shift(1)
    return h4


def signed_streak(signs: np.ndarray) -> float:
    if len(signs) == 0:
        return np.nan
    last = signs[-1]
    length = 1
    for value in signs[-2::-1]:
        if value != last:
            break
        length += 1
    return float(last * length)


def late_return(prefix: pd.DataFrame, end: pd.Timestamp, minutes: int) -> float:
    start = end - pd.Timedelta(minutes=minutes)
    tail = prefix[prefix["ts"] >= start]
    if tail.empty:
        return np.nan
    return float(prefix.iloc[-1]["close"] - tail.iloc[0]["open"])


def generic_prefix_rows(
    m1: pd.DataFrame,
    h4: pd.DataFrame,
    decisions: set[pd.Timestamp],
) -> pd.DataFrame:
    state = h4.set_index("h4_start")
    exact_open = m1.set_index("ts")["open"]
    rows: list[dict[str, object]] = []
    for start, group in m1[m1["h4_start"].isin(decisions)].groupby("h4_start", sort=True):
        if start not in state.index:
            continue
        state_row = state.loc[start]
        scale = float(state_row["causal_scale"])
        if not np.isfinite(scale) or scale <= 0.0:
            continue
        group = group.sort_values("ts")
        for minutes in CHECKPOINT_MINUTES:
            checkpoint = start + pd.Timedelta(minutes=minutes)
            prefix = group[group["ts"] < checkpoint]
            if prefix.empty:
                continue
            o = float(prefix.iloc[0]["open"])
            h = float(prefix["high"].max())
            l = float(prefix["low"].min())
            c = float(prefix.iloc[-1]["close"])
            fast_close_prefix = (o + h + l + 2.0 * c) / 5.0
            changes = np.diff(np.r_[o, prefix["close"].to_numpy(dtype=float)])
            path_length = float(np.abs(changes).sum())
            close_location = 0.0 if h <= l else 2.0 * (c - l) / (h - l) - 1.0

            m5_key = ((prefix["ts"] - start).dt.total_seconds() // 300).astype(int)
            m5 = (
                prefix.assign(m5_key=m5_key)
                .groupby("m5_key", sort=True)
                .agg(open=("open", "first"), close=("close", "last"))
            )
            bodies = (m5["close"] - m5["open"]).to_numpy(dtype=float)
            signs = np.where(bodies >= 0.0, 1.0, -1.0)
            transitions = (
                float(np.mean(signs[1:] != signs[:-1])) if len(signs) > 1 else 0.0
            )
            body_abs = float(np.abs(bodies).sum())
            body_eff = float(bodies.sum() / body_abs) if body_abs > 1e-12 else 0.0

            exit_open = np.nan
            if checkpoint in exact_open.index:
                value = exact_open.loc[checkpoint]
                if isinstance(value, pd.Series):
                    raise ValueError(f"duplicate M1 checkpoint timestamp: {checkpoint}")
                exit_open = float(value)

            rows.append(
                {
                    "decision": start,
                    "checkpoint_min": minutes,
                    "checkpoint_time": checkpoint,
                    "prefix_rows": int(len(prefix)),
                    "prefix_coverage": float(len(prefix) / minutes),
                    "prefix_open": o,
                    "prefix_high": h,
                    "prefix_low": l,
                    "prefix_close": c,
                    "fast_ha_open": float(state_row["fast_ha_open"]),
                    "fast_ha_close_prefix": fast_close_prefix,
                    "causal_scale": scale,
                    "close_location_raw": close_location,
                    "path_length": path_length,
                    "ret_15_raw": late_return(prefix, checkpoint, 15),
                    "ret_30_raw": late_return(prefix, checkpoint, 30),
                    "ret_60_raw": late_return(prefix, checkpoint, 60),
                    "m5_up_fraction": float(np.mean(signs > 0.0)),
                    "m5_transition_rate": transitions,
                    "m5_streak_raw": signed_streak(signs),
                    "m5_body_eff_raw": body_eff,
                    "checkpoint_open": exit_open,
                    "final_fast_dir": int(state_row["fast_dir"]),
                }
            )
    return pd.DataFrame(rows)


def add_directional_features(prefix: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "signal_id",
        "decision",
        "entry_time",
        "year",
        "dir",
        "k",
        "rid",
        "entry",
        "stop",
        "exit_time",
        "exit_reason",
        "stop_hit",
        "R",
        "pnl",
        "L",
        "next_same",
        "label_available_at",
    ]
    frame = universe[columns].merge(prefix, on="decision", how="inner", validate="one_to_many")
    direction = frame["dir"].astype(float)
    scale = frame["causal_scale"].astype(float)
    frame["ha_margin_atr"] = direction * (
        frame["fast_ha_close_prefix"] - frame["fast_ha_open"]
    ) / scale
    frame["prefix_return_atr"] = direction * (
        frame["prefix_close"] - frame["prefix_open"]
    ) / scale
    frame["prefix_range_atr"] = (frame["prefix_high"] - frame["prefix_low"]) / scale
    frame["favorable_excursion_atr"] = np.where(
        direction > 0,
        frame["prefix_high"] - frame["prefix_open"],
        frame["prefix_open"] - frame["prefix_low"],
    ) / scale
    frame["adverse_excursion_atr"] = np.where(
        direction > 0,
        frame["prefix_open"] - frame["prefix_low"],
        frame["prefix_high"] - frame["prefix_open"],
    ) / scale
    frame["close_location_aligned"] = direction * frame["close_location_raw"]
    frame["directional_path_efficiency"] = direction * (
        frame["prefix_close"] - frame["prefix_open"]
    ) / frame["path_length"].clip(lower=1e-9)
    frame["retrace_from_favorable_atr"] = np.where(
        direction > 0,
        frame["prefix_high"] - frame["prefix_close"],
        frame["prefix_close"] - frame["prefix_low"],
    ) / scale
    for minutes in (15, 30, 60):
        frame[f"ret_{minutes}_atr"] = direction * frame[f"ret_{minutes}_raw"] / scale
    frame["m5_aligned_fraction"] = np.where(
        direction > 0,
        frame["m5_up_fraction"],
        1.0 - frame["m5_up_fraction"],
    )
    frame["m5_signed_streak"] = direction * frame["m5_streak_raw"]
    frame["m5_body_efficiency"] = direction * frame["m5_body_eff_raw"]
    frame["nha"] = 1 - frame["next_same"].astype(int)
    frame["final_same_rebuilt"] = (frame["final_fast_dir"] == frame["dir"]).astype(int)
    return frame


def load_selected_events(path: Path, universe: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    events = pd.read_csv(path)
    events["decision"] = pd.to_datetime(events["decision"], format="%Y.%m.%d %H:%M")
    active = events[(events["decision"] >= pd.Timestamp("2024-10-01")) & (events["r7g_weight"] > 0)].copy()
    active["dir_event"] = active["dir"].map({"LONG": 1, "SHORT": -1}).astype(int)
    available = set(universe["decision"])
    matched = active[active["decision"].isin(available)].copy()
    audit = {
        "event_rows": int(len(events)),
        "post_2024q4_positive_weight_rows": int(len(active)),
        "matched_resolved_universe_rows": int(len(matched)),
        "unmatched_rows": int(len(active) - len(matched)),
    }
    return matched[["decision", "dir_event", "k", "r7g_weight", "event"]], audit


def model_pipeline(feature_columns: list[str]) -> Pipeline:
    transformer = ColumnTransformer(
        [("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", RobustScaler(quantile_range=(10, 90)))]), feature_columns)],
        remainder="drop",
    )
    return Pipeline(
        [
            ("prep", transformer),
            ("model", LogisticRegression(C=1.0, max_iter=2000, random_state=20260921)),
        ]
    )


def safe_auc(y: pd.Series, score: np.ndarray) -> float:
    return float(roc_auc_score(y, score)) if y.nunique() > 1 else np.nan


def score_outer_years(
    all_rows: pd.DataFrame,
    selected: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scored_parts: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    for checkpoint in CHECKPOINT_MINUTES:
        checkpoint_all = all_rows[all_rows["checkpoint_min"] == checkpoint].copy()
        checkpoint_selected = selected[selected["checkpoint_min"] == checkpoint].copy()
        for year in TEST_YEARS:
            boundary = pd.Timestamp(f"{year}-01-01")
            train = checkpoint_all[
                (checkpoint_all["decision"] < boundary)
                & (checkpoint_all["label_available_at"] < boundary)
            ].copy()
            test = checkpoint_selected[checkpoint_selected["year"] == year].copy()
            if train.empty or test.empty or train["nha"].nunique() < 2:
                continue
            model = model_pipeline(FEATURES)
            model.fit(train[FEATURES], train["nha"])
            train_score = model.predict_proba(train[FEATURES])[:, 1]
            test_score = model.predict_proba(test[FEATURES])[:, 1]
            threshold = float(np.quantile(train_score, 0.90))
            test["p_nha"] = test_score
            test["prior_score_q90"] = threshold
            test["warn_q90"] = (test["p_nha"] >= threshold).astype(int)
            test["warn_p50"] = (test["p_nha"] >= 0.50).astype(int)
            test["provisional_nha"] = (test["ha_margin_atr"] < 0.0).astype(int)
            scored_parts.append(test)

            y = test["nha"].astype(int)
            for name, score, warning in [
                ("PROVISIONAL_HA_MARGIN", -test["ha_margin_atr"].to_numpy(), test["provisional_nha"]),
                ("COMPACT_PATH_MODEL_P50", test_score, test["warn_p50"]),
                ("COMPACT_PATH_MODEL_PRIOR_Q90", test_score, test["warn_q90"]),
            ]:
                warning = np.asarray(warning, dtype=int)
                tp = int(((warning == 1) & (y.to_numpy() == 1)).sum())
                fp = int(((warning == 1) & (y.to_numpy() == 0)).sum())
                fn = int(((warning == 0) & (y.to_numpy() == 1)).sum())
                metric_rows.append(
                    {
                        "checkpoint_min": checkpoint,
                        "year": year,
                        "method": name,
                        "n": int(len(test)),
                        "nha_rate": float(y.mean()),
                        "roc_auc": safe_auc(y, np.asarray(score, dtype=float)),
                        "average_precision": float(average_precision_score(y, score)),
                        "warnings": int(warning.sum()),
                        "precision": float(tp / max(1, tp + fp)),
                        "recall": float(tp / max(1, tp + fn)),
                        "prior_q90": threshold if "Q90" in name else np.nan,
                    }
                )
    scored = pd.concat(scored_parts, ignore_index=True)
    return scored, pd.DataFrame(metric_rows)


def add_execution_state(scored: pd.DataFrame, m1: pd.DataFrame) -> pd.DataFrame:
    frame = scored.copy()
    frame["entry_time"] = pd.to_datetime(frame["entry_time"])
    frame["exit_time"] = pd.to_datetime(frame["exit_time"])
    frame["checkpoint_time"] = pd.to_datetime(frame["checkpoint_time"])
    frame["alive_at_checkpoint"] = (
        (frame["entry_time"] < frame["checkpoint_time"])
        & (frame["exit_time"] >= frame["checkpoint_time"])
        & frame["checkpoint_open"].notna()
    )
    risk = (frame["entry"] - frame["stop"]).abs()
    frame["early_exit_R"] = frame["dir"] * (
        frame["checkpoint_open"] - frame["entry"]
    ) / risk.clip(lower=1e-9)
    return frame


def pooled_classification(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for checkpoint, group in scored.groupby("checkpoint_min", sort=True):
        y = group["nha"].astype(int)
        definitions = [
            (
                "PROVISIONAL_HA_MARGIN",
                -group["ha_margin_atr"].to_numpy(dtype=float),
                group["provisional_nha"].to_numpy(dtype=int),
            ),
            (
                "COMPACT_PATH_MODEL_P50",
                group["p_nha"].to_numpy(dtype=float),
                group["warn_p50"].to_numpy(dtype=int),
            ),
            (
                "COMPACT_PATH_MODEL_PRIOR_Q90",
                group["p_nha"].to_numpy(dtype=float),
                group["warn_q90"].to_numpy(dtype=int),
            ),
        ]
        for method, score, warning in definitions:
            tp = int(((warning == 1) & (y.to_numpy() == 1)).sum())
            fp = int(((warning == 1) & (y.to_numpy() == 0)).sum())
            fn = int(((warning == 0) & (y.to_numpy() == 1)).sum())
            rows.append(
                {
                    "checkpoint_min": int(checkpoint),
                    "method": method,
                    "n": int(len(group)),
                    "nha_rate": float(y.mean()),
                    "roc_auc": safe_auc(y, score),
                    "average_precision": float(average_precision_score(y, score)),
                    "warnings": int(warning.sum()),
                    "precision": float(tp / max(1, tp + fp)),
                    "recall": float(tp / max(1, tp + fn)),
                }
            )
    return pd.DataFrame(rows)


def q90_decomposition(scored: pd.DataFrame) -> pd.DataFrame:
    frame = scored[(scored["warn_q90"] == 1) & scored["alive_at_checkpoint"]].copy()
    frame["delta_weighted_R"] = (
        frame["early_exit_R"] - frame["R"]
    ) * frame["r7g_weight"]
    return (
        frame.groupby(["checkpoint_min", "year", "nha", "stop_hit"], dropna=False)
        .agg(
            children=("decision", "size"),
            baseline_weighted_R=("R", lambda s: float((s * frame.loc[s.index, "r7g_weight"]).sum())),
            early_exit_weighted_R=(
                "early_exit_R",
                lambda s: float((s * frame.loc[s.index, "r7g_weight"]).sum()),
            ),
            delta_weighted_R=("delta_weighted_R", "sum"),
        )
        .reset_index()
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


def policy_row(base: pd.DataFrame, name: str, trigger: pd.Series) -> dict[str, object]:
    frame = base.sort_values("decision").copy()
    executed = trigger.astype(bool) & frame["alive_at_checkpoint"].astype(bool)
    frame["policy_R"] = np.where(executed, frame["early_exit_R"], frame["R"])
    frame["policy_stop"] = frame["stop_hit"].astype(bool) & ~executed
    weight = frame["r7g_weight"].astype(float)
    baseline_weighted_r = float((frame["R"] * weight).sum())
    policy_weighted_r = float((frame["policy_R"] * weight).sum())
    baseline_positive = float((frame["R"].clip(lower=0.0) * weight).sum())
    policy_on_baseline_winners = float(
        (frame.loc[frame["R"] > 0.0, "policy_R"].clip(lower=0.0) * weight[frame["R"] > 0.0]).sum()
    )
    tail_mask = (frame["L"] >= 6) & (frame["R"] > 0.0)
    baseline_tail = float((frame.loc[tail_mask, "R"] * weight[tail_mask]).sum())
    retained_tail = float(
        (frame.loc[tail_mask, "policy_R"].clip(lower=0.0) * weight[tail_mask]).sum()
    )
    return {
        "policy": name,
        "children": int(len(frame)),
        "warnings": int(trigger.astype(bool).sum()),
        "executed_early_exits": int(executed.sum()),
        "true_nha_exits": int((executed & (frame["nha"] == 1)).sum()),
        "false_pha_exits": int((executed & (frame["nha"] == 0)).sum()),
        "baseline_hard_stops": int(frame["stop_hit"].sum()),
        "policy_hard_stops": int(frame["policy_stop"].sum()),
        "hard_stops_prevented": int((frame["stop_hit"].astype(bool) & executed).sum()),
        "baseline_max_stop_streak": max_true_streak(frame["stop_hit"]),
        "policy_max_stop_streak": max_true_streak(frame["policy_stop"]),
        "baseline_weighted_R": baseline_weighted_r,
        "policy_weighted_R": policy_weighted_r,
        "delta_weighted_R": policy_weighted_r - baseline_weighted_r,
        "positive_R_retention": policy_on_baseline_winners / baseline_positive if baseline_positive > 0 else np.nan,
        "L6plus_positive_R_retention": retained_tail / baseline_tail if baseline_tail > 0 else np.nan,
    }


def simulate_policies(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for checkpoint in CHECKPOINT_MINUTES:
        base = scored[scored["checkpoint_min"] == checkpoint].copy()
        rows.append(policy_row(base, f"PROVISIONAL_NHA_{checkpoint}M", base["provisional_nha"] == 1))
        rows.append(policy_row(base, f"MODEL_PRIOR_Q90_{checkpoint}M", base["warn_q90"] == 1))
        rows.append(policy_row(base, f"ORACLE_NHA_{checkpoint}M", base["nha"] == 1))

    ordered = scored.sort_values(["decision", "checkpoint_min"]).copy()
    selected_rows: list[pd.Series] = []
    for _, group in ordered.groupby("decision", sort=True):
        chosen = None
        for _, candidate in group.iterrows():
            if bool(candidate["warn_q90"]) and bool(candidate["alive_at_checkpoint"]):
                chosen = candidate
                break
        if chosen is None:
            chosen = group.iloc[0].copy()
            chosen["warn_q90"] = 0
            chosen["alive_at_checkpoint"] = False
        selected_rows.append(chosen)
    sequential = pd.DataFrame(selected_rows)
    rows.append(
        policy_row(
            sequential,
            "MODEL_PRIOR_Q90_EARLIEST_60_120_180",
            sequential["warn_q90"] == 1,
        )
    )
    return pd.DataFrame(rows)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    m1 = load_m1(args.m1)
    universe = pd.read_csv(
        args.universe,
        parse_dates=["decision", "entry_time", "exit_time", "label_available_at"],
    )
    h4 = build_h4_state(m1)
    prefix = generic_prefix_rows(m1, h4, set(universe["decision"]))
    all_rows = add_directional_features(prefix, universe)

    parity_mismatches = int((all_rows["next_same"] != all_rows["final_same_rebuilt"]).sum())
    if parity_mismatches:
        raise ValueError(f"rebuilt next-HA parity mismatches: {parity_mismatches}")

    selected_events, event_audit = load_selected_events(args.events, universe)
    selected = all_rows.merge(
        selected_events,
        on="decision",
        how="inner",
        suffixes=("", "_event"),
        validate="many_to_one",
    )
    direction_mismatches = int((selected["dir"] != selected["dir_event"]).sum())
    k_mismatches = int((selected["k_event"] != selected["k"]).sum())
    if direction_mismatches or k_mismatches:
        raise ValueError(
            f"selected-event parity failed: dir={direction_mismatches}, k={k_mismatches}"
        )

    scored, classification = score_outer_years(all_rows, selected)
    scored = add_execution_state(scored, m1)
    classification_pooled = pooled_classification(scored)
    decomposition = q90_decomposition(scored)
    policies = simulate_policies(scored)

    prefix_path = args.out_dir / "V10_INTRAH4_NOWCAST_PREFIX_LEDGER.csv"
    score_path = args.out_dir / "V10_INTRAH4_NOWCAST_SCORED_SELECTED.csv"
    class_path = args.out_dir / "V10_INTRAH4_NOWCAST_CLASSIFICATION.csv"
    class_pooled_path = args.out_dir / "V10_INTRAH4_NOWCAST_CLASSIFICATION_POOLED.csv"
    policy_path = args.out_dir / "V10_INTRAH4_NOWCAST_POLICY.csv"
    decomposition_path = args.out_dir / "V10_INTRAH4_NOWCAST_Q90_DECOMPOSITION.csv"
    all_rows.to_csv(prefix_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    scored.to_csv(score_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    classification.to_csv(class_path, index=False)
    classification_pooled.to_csv(class_pooled_path, index=False)
    policies.to_csv(policy_path, index=False)
    decomposition.to_csv(decomposition_path, index=False)

    manifest = {
        "status": "CONSUMED_DATA_DIAGNOSTIC_ONLY",
        "source_m1": str(args.m1.resolve()),
        "source_m1_sha256": sha256_file(args.m1),
        "source_universe": str(args.universe.resolve()),
        "source_universe_sha256": sha256_file(args.universe),
        "source_events": str(args.events.resolve()),
        "source_events_sha256": sha256_file(args.events),
        "checkpoints_minutes": list(CHECKPOINT_MINUTES),
        "feature_columns": FEATURES,
        "model": "RobustScaler(10,90) + LogisticRegression(C=1.0)",
        "outer_years": list(TEST_YEARS),
        "training_rule": "decision and label_available_at both strictly before outer-year boundary",
        "warning_rule": "p_nha >= q90 of the fitted model's prior-training score distribution",
        "economic_action": "close newest Child only at exact checkpoint M1 open if still alive",
        "universe_rows": int(len(universe)),
        "prefix_rows": int(len(all_rows)),
        "selected_children": int(selected["decision"].nunique()),
        "scored_selected_rows": int(len(scored)),
        "next_ha_parity_mismatches": parity_mismatches,
        "selected_direction_mismatches": direction_mismatches,
        "selected_k_mismatches": k_mismatches,
        "event_audit": event_audit,
        "outputs": [
            str(prefix_path),
            str(score_path),
            str(class_path),
            str(class_pooled_path),
            str(policy_path),
            str(decomposition_path),
        ],
    }
    manifest_path = args.out_dir / "V10_INTRAH4_NOWCAST_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nCLASSIFICATION")
    print(classification.to_string(index=False))
    print("\nCLASSIFICATION_POOLED")
    print(classification_pooled.to_string(index=False))
    print("\nPOLICIES")
    print(policies.to_string(index=False))


if __name__ == "__main__":
    main()
