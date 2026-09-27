"""Frozen HA-8A observation ladder; see the 2026-09-28 contract.

Run --build-features first. Only --evaluate loads future labels. This is a
consumed-history model diagnostic, not a Baseline-0 action or MT5 backtest.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
H4 = ROOT / "data/GOLD#/GOLD#_H4_202201030000_202609230000.csv"
HA4 = ROOT / "output/v13_ha4c_integrated_20260927/decision_features.csv"
HA5 = ROOT / "output/v13_ha5_raw_swing_20260927/decision_features.csv"
LABELS = ROOT / "output/v13_ha4c_integrated_20260927/future_labels.csv"
OUT = ROOT / "output/v13_ha8a_combination_20260928"
FEATURE_FILE = OUT / "decision_features.csv"
STOP = datetime(2026, 8, 28, 20)

SWING_STATES = (
    "no_level", "no_break", "probe_rejected", "return_inside",
    "fresh_close_beyond", "held_close_beyond",
)
CATEGORIES = {
    "side": ("-1", "1"),
    "h4_delta_contract": ("False", "True"),
    "h4_wick_present": ("False", "True"),
    "h4_wick_reappeared": ("False", "True"),
    "h1_path_state": (
        "no_opposition", "repaired", "unrepaired_mixed", "persistent_opposition"
    ),
    "progress_state": SWING_STATES,
    "adverse_state": SWING_STATES,
    "ema50_slope_opposed": ("False", "True"),
    "ema50_position_opposed": ("False", "True"),
}
SPECS = {
    "H1_only": (["h1_trailing_opposed"], ["h1_path_state"]),
    "HASTOC_only": (["journey_hastoc10"], []),
    "H4_H1": (
        ["journey_bar", "h4_body_ratio", "h4_raw_close_normalized", "h1_trailing_opposed"],
        ["side", "h4_delta_contract", "h4_wick_present", "h4_wick_reappeared", "h1_path_state"],
    ),
    "plus_HASTOC": (["journey_hastoc10"], []),
    "plus_activity": (["log_relative_tick_volume20", "persistent_x_log_activity"], []),
    "plus_raw_swing": (
        ["progress_close_distance_ranges", "adverse_close_distance_ranges"],
        ["progress_state", "adverse_state"],
    ),
    "plus_EMA50": ([], ["ema50_slope_opposed", "ema50_position_opposed"]),
}
FOLDS = [
    ("2024-H2", "2024-07-01", "2025-01-01"),
    ("2025-H1", "2025-01-01", "2025-07-01"),
    ("2025-H2", "2025-07-01", "2026-01-01"),
    ("2026-to-cutoff", "2026-01-01", "2026-09-01"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_h4_prefix() -> dict[str, dict]:
    """Streaming prefix; no later bar is held while a bar feature is formed."""
    slots: dict[int, deque[int]] = defaultdict(lambda: deque(maxlen=20))
    delta10: deque[float] = deque(maxlen=10)
    ema_seed: list[float] = []
    ema = None
    prev_ha_o = prev_ha_c = prev_ema = None
    prior_color = 0
    result = {}
    with H4.open(newline="", encoding="utf-8-sig") as stream:
        for idx, row in enumerate(csv.DictReader(stream, delimiter="\t")):
            signal = datetime.strptime(row["<DATE>"] + " " + row["<TIME>"], "%Y.%m.%d %H:%M:%S")
            if signal > STOP:
                break
            o, hi, lo, close = (float(row[k]) for k in ("<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"))
            tv = int(row["<TICKVOL>"])
            if tv <= 0:
                raise ValueError(f"nonpositive H4 tick volume: {signal}")
            slot_prior = slots[signal.hour]
            relative = tv / float(np.median(slot_prior)) if len(slot_prior) == 20 else math.nan
            ha_c = (o + hi + lo + close) / 4.0
            ha_o = (o + close) / 2.0 if prev_ha_o is None else (prev_ha_o + prev_ha_c) / 2.0
            color = 1 if ha_c > ha_o else -1 if ha_c < ha_o else prior_color
            delta10.append(ha_o - ha_c)
            if len(delta10) == 10 and max(delta10) > min(delta10):
                hastoc = 100.0 * (delta10[-1] - min(delta10)) / (max(delta10) - min(delta10))
                journey_hastoc = 100.0 - hastoc if color == 1 else hastoc
            else:
                journey_hastoc = math.nan
            if len(ema_seed) < 50:
                ema_seed.append(close)
                if len(ema_seed) == 50:
                    ema = sum(ema_seed) / 50.0
            else:
                ema = (2.0 / 51.0) * close + (49.0 / 51.0) * ema
            slope = color * (ema - prev_ema) if ema is not None and prev_ema is not None else math.nan
            position = color * (ha_c - ema) if ema is not None else math.nan
            key = signal.strftime("%Y-%m-%d %H:%M:%S")
            if key in result:
                raise ValueError(f"duplicate H4 timestamp: {key}")
            result[key] = {
                "signal": key, "h4_idx": idx, "raw_h4_open": o, "ha_color_rebuilt": color,
                "journey_hastoc10": journey_hastoc,
                "relative_tick_volume20": relative,
                "log_relative_tick_volume20": math.log(relative) if math.isfinite(relative) else math.nan,
                "ema50_slope_opposed": slope < -1e-15 if math.isfinite(slope) else None,
                "ema50_position_opposed": position < -1e-15 if math.isfinite(position) else None,
            }
            prev_ha_o, prev_ha_c, prior_color, prev_ema = ha_o, ha_c, color, ema
            slot_prior.append(tv)
    return result


def build_features() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    h4 = build_h4_prefix()
    h4_by_idx = {row["h4_idx"]: row for row in h4.values()}
    ha4 = pd.read_csv(HA4, parse_dates=["signal", "known_at"])
    ha5 = pd.read_csv(HA5, parse_dates=["signal", "known_at"])
    if len(ha4) != 4108 or len(ha5) != 4108:
        raise ValueError("upstream feature-ledger count changed")
    swing_cols = [
        "signal", "journey", "raw_open", "raw_high", "raw_low", "raw_close",
        "progress_state", "adverse_state", "progress_close_distance_ranges",
        "adverse_close_distance_ranges",
    ]
    d = ha4.merge(ha5[swing_cols], on=["signal", "journey"], how="left", validate="one_to_one")
    if d["progress_state"].isna().any() or len(d) != 4108:
        raise ValueError("HA-4C / HA-5 join failed")
    records = []
    for r in d.itertuples(index=False):
        key = r.signal.strftime("%Y-%m-%d %H:%M:%S")
        known = r.known_at.strftime("%Y-%m-%d %H:%M:%S")
        current = h4.get(key)
        next_bar = h4_by_idx.get(current["h4_idx"] + 1) if current is not None else None
        next_next_bar = h4_by_idx.get(current["h4_idx"] + 2) if current is not None else None
        next_start = next_bar["signal"] if next_bar is not None else None
        next_next_start = next_next_bar["signal"] if next_next_bar is not None else None
        if (current is None or next_bar is None or current["ha_color_rebuilt"] != int(r.side)
                or known < next_start or (next_next_start is not None and known >= next_next_start)):
            raise ValueError(
                f"H4 feature/side/next-open parity failed at {key}: "
                f"known_at={known}, rebuilt_color={None if current is None else current['ha_color_rebuilt']}, "
                f"ledger_side={r.side}, next_bar_start={next_start}"
            )
        item = r._asdict()
        item.update(current)
        item["execution_raw_open"] = next_bar["raw_h4_open"]
        item["persistent_x_log_activity"] = (
            current["log_relative_tick_volume20"]
            if r.h1_path_state == "persistent_opposition" else 0.0
        )
        records.append(item)
    f = pd.DataFrame.from_records(records).sort_values("signal")
    if f["relative_tick_volume20"].isna().any() or f["journey_hastoc10"].isna().any():
        raise ValueError("warm-up features missing")
    f.to_csv(FEATURE_FILE, index=False)
    manifest = {
        "status": "features-built-without-future-labels",
        "rows": len(f), "first_signal": str(f.signal.min()), "last_signal": str(f.signal.max()),
        "last_h4_prefix_bar": max(h4),
        "sha256": {str(path.relative_to(ROOT)): sha256(path) for path in (H4, HA4, HA5)},
        "feature_ledger_sha256": sha256(FEATURE_FILE),
    }
    (OUT / "feature_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def matrix(train: pd.DataFrame, test: pd.DataFrame, nums: list[str], cats: list[str]) -> tuple[np.ndarray, np.ndarray]:
    def encode(d: pd.DataFrame, med: dict, scales: dict) -> np.ndarray:
        cols = [np.ones(len(d), dtype=float)]
        for name in nums:
            v = pd.to_numeric(d[name], errors="coerce").to_numpy(dtype=float)
            v = np.where(np.isfinite(v), v, med[name])
            cols.append((v - med[name]) / scales[name])
        for name in cats:
            values = d[name].astype(str).to_numpy()
            for category in CATEGORIES[name][1:]:
                cols.append((values == category).astype(float))
        return np.column_stack(cols)

    med, scales = {}, {}
    for name in nums:
        v = pd.to_numeric(train[name], errors="coerce").to_numpy(dtype=float)
        finite = v[np.isfinite(v)]
        med[name] = float(np.median(finite)) if len(finite) else 0.0
        filled = np.where(np.isfinite(v), v, med[name])
        scales[name] = max(float(np.std(filled)), 1e-9)
    return encode(train, med, scales), encode(test, med, scales)


def fit_logistic(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Deterministic Newton solution to sum-logloss + 0.5*||beta_nonintercept||^2."""
    beta = np.zeros(x.shape[1])
    p0 = float(np.clip(y.mean(), 1e-6, 1 - 1e-6))
    beta[0] = math.log(p0 / (1 - p0))
    penalty = np.ones(x.shape[1]); penalty[0] = 0.0
    for _ in range(60):
        p = 1 / (1 + np.exp(-np.clip(x @ beta, -35, 35)))
        grad = x.T @ (p - y) + penalty * beta
        weights = np.maximum(p * (1 - p), 1e-12)
        hess = x.T @ (x * weights[:, None]) + np.diag(penalty)
        step = np.linalg.solve(hess, grad)
        beta -= step
        if np.max(np.abs(step)) < 1e-9:
            break
    else:
        raise RuntimeError("logistic solver did not converge")
    if not np.isfinite(beta).all():
        raise RuntimeError("nonfinite logistic coefficients")
    return beta


def score(y: np.ndarray, p: np.ndarray) -> dict:
    p = np.clip(p, 1e-12, 1 - 1e-12)
    n_pos = int(y.sum()); n_neg = len(y) - n_pos
    if n_pos and n_neg:
        ranks = pd.Series(p).rank(method="average").to_numpy()
        auc = float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))
    else:
        auc = None
    calibration = []
    ece = 0.0
    for b in range(10):
        lower, upper = b / 10, (b + 1) / 10
        mask = (p >= lower) & ((p < upper) if b < 9 else (p <= upper))
        if mask.any():
            expected, observed = float(p[mask].mean()), float(y[mask].mean())
            calibration.append({"bin": f"{lower:.1f}-{upper:.1f}", "n": int(mask.sum()),
                                "predicted": expected, "observed": observed})
            ece += float(mask.mean()) * abs(expected - observed)
    return {
        "n": int(len(y)), "event_rate": float(y.mean()),
        "mean_prediction": float(p.mean()),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(np.mean(-y * np.log(p) - (1 - y) * np.log(1 - p))),
        "auc": auc, "calibration_ece_10_fixed_bins": ece,
        "calibration_bins": calibration,
    }


def economics(f: pd.DataFrame) -> pd.DataFrame:
    f = f.sort_values(["journey", "journey_bar"])
    first = f.groupby("journey", sort=True).first()
    rows = []
    for jid in sorted(f.journey.unique())[:-1]:
        g = f[f.journey == jid]
        exit_open = float(first.loc[jid + 1, "execution_raw_open"])
        for r in g[g.journey_bar <= 10].itertuples(index=False):
            rows.append({
                "signal": r.signal, "journey": int(jid), "journey_bar": int(r.journey_bar),
                "journey_len": len(g), "side": int(r.side),
                "entry": float(r.execution_raw_open), "exit": exit_open,
                "baseline_pnl": int(r.side) * (exit_open - float(r.execution_raw_open)),
            })
    child = pd.DataFrame(rows)
    if len(child) != 3858 or abs(child.baseline_pnl.sum() - 8147.11) >= 0.02:
        raise ValueError(f"Baseline-0 structural parity failed: {len(child)}, {child.baseline_pnl.sum()}")
    return child


def risk_bucket(child: pd.DataFrame, name: str) -> dict:
    z = child[child.journey_bar.between(2, 10) & child[name].notna()].copy()
    z = z.sort_values([name, "signal"], ascending=[False, True])
    high = z.head(int(math.ceil(0.20 * len(z))))
    positive = high.loc[high.baseline_pnl > 0, "baseline_pnl"].sort_values(ascending=False)
    quintiles = []
    for q, positions in enumerate(np.array_split(np.arange(len(z)), 5), start=1):
        group = z.iloc[positions]
        quintiles.append({
            "risk_rank": q, "n": len(group),
            "mean_predicted_flip3": float(group[name].mean()),
            "actual_flip3": float(group.flip_within_3.astype(float).mean()),
            "losses": int((group.baseline_pnl < 0).sum()),
            "winners": int((group.baseline_pnl > 0).sum()),
            "gross_winning_points": float(group.loc[group.baseline_pnl > 0, "baseline_pnl"].sum()),
            "gross_losing_points": float(group.loc[group.baseline_pnl < 0, "baseline_pnl"].sum()),
            "net_points": float(group.baseline_pnl.sum()),
            "long_journey_children": int((group.journey_len >= 10).sum()),
        })
    return {
        "eligible_n": len(z), "highest_risk_20pct_n": len(high),
        "eligible_losses": int((z.baseline_pnl < 0).sum()),
        "eligible_winners": int((z.baseline_pnl > 0).sum()),
        "eligible_net_points": float(z.baseline_pnl.sum()),
        "high_bucket_mean_predicted_flip3": float(high[name].mean()),
        "high_bucket_actual_flip3": float(high.flip_within_3.astype(float).mean()),
        "losses": int((high.baseline_pnl < 0).sum()),
        "winners": int((high.baseline_pnl > 0).sum()),
        "zeros": int((high.baseline_pnl == 0).sum()),
        "gross_winning_points": float(high.loc[high.baseline_pnl > 0, "baseline_pnl"].sum()),
        "gross_losing_points": float(high.loc[high.baseline_pnl < 0, "baseline_pnl"].sum()),
        "net_points": float(high.baseline_pnl.sum()),
        "top5_winner_points": float(positive.head(5).sum()),
        "long_journey_children": int((high.journey_len >= 10).sum()),
        "long_journey_net_points": float(high.loc[high.journey_len >= 10, "baseline_pnl"].sum()),
        "long_journey_flip3_false_alarms": int(((high.journey_len >= 10) & (~high.flip_within_3)).sum()),
        "descriptive_risk_quintiles_high_to_low": quintiles,
    }


def evaluate() -> None:
    if not FEATURE_FILE.exists():
        raise FileNotFoundError("run --build-features before --evaluate")
    f = pd.read_csv(FEATURE_FILE, parse_dates=["signal", "known_at"])
    manifest = json.loads((OUT / "feature_manifest.json").read_text(encoding="utf-8"))
    if sha256(FEATURE_FILE) != manifest["feature_ledger_sha256"]:
        raise ValueError("feature ledger changed after label boundary")
    labels = pd.read_csv(LABELS, parse_dates=["signal"])
    d = f.merge(labels, on=["signal", "journey"], how="inner", validate="one_to_one")
    if len(d) != 4105 or labels[["signal", "journey"]].duplicated().any():
        raise ValueError("future-label parity failed")
    d = d.sort_values("known_at").reset_index(drop=True)
    y_all = d.flip_within_3.astype(int).to_numpy()
    pred = d[["signal", "known_at", "journey", "journey_bar", "side", "year", "flip_within_3", "journey_closed_bars"]].copy()
    pred["fold"] = ""
    for name in ("constant", *SPECS):
        pred[name] = np.nan
    cumulative_nums: list[str] = []
    cumulative_cats: list[str] = []
    model_features = {}
    for name in SPECS:
        ns, cs = SPECS[name]
        if name in ("H1_only", "HASTOC_only"):
            model_features[name] = (list(ns), list(cs))
            continue
        if name == "H4_H1":
            cumulative_nums = list(ns)
            cumulative_cats = list(cs)
        else:
            cumulative_nums += ns
            cumulative_cats += cs
        model_features[name] = (list(cumulative_nums), list(cumulative_cats))
    folds = {}
    for fold_name, start, end in FOLDS:
        test_idx = np.flatnonzero(((d.known_at >= start) & (d.known_at < end)).to_numpy())
        if not len(test_idx):
            raise ValueError(f"empty test fold {fold_name}")
        first_test_h4 = int(d.loc[test_idx[0], "h4_idx"])
        train_idx = np.flatnonzero(((d.known_at < start) & (d.h4_idx + 4 <= first_test_h4)).to_numpy())
        if len(train_idx) < 500:
            raise ValueError(f"too little chronological training data: {fold_name}")
        train, test = d.iloc[train_idx], d.iloc[test_idx]
        y_train, y_test = y_all[train_idx], y_all[test_idx]
        pred.loc[test_idx, "fold"] = fold_name
        pred.loc[test_idx, "constant"] = y_train.mean()
        for name, (nums, cats) in model_features.items():
            x_train, x_test = matrix(train, test, nums, cats)
            beta = fit_logistic(x_train, y_train)
            pred.loc[test_idx, name] = 1 / (1 + np.exp(-np.clip(x_test @ beta, -35, 35)))
        folds[fold_name] = {
            "train_n": len(train), "test_n": len(test),
            "purged_before_test_n": int(((d.known_at < start) & (d.h4_idx + 4 > first_test_h4)).sum()),
            "train_last_known_at": str(train.known_at.max()),
            "test_first_known_at": str(test.known_at.min()),
            "scores": {name: score(y_test, pred.loc[test_idx, name].to_numpy(dtype=float))
                       for name in ("constant", *SPECS)},
        }
    oof = pred[pred.fold != ""].copy()
    ys = oof.flip_within_3.astype(int).to_numpy()
    pooled = {name: score(ys, oof[name].to_numpy(dtype=float)) for name in ("constant", *SPECS)}
    child = economics(f)
    child = child.merge(oof[["signal", "journey", "fold", "flip_within_3", *SPECS]],
                        on=["signal", "journey"], how="left", validate="one_to_one")
    for name in ("H4_H1", "plus_HASTOC", "plus_activity", "plus_raw_swing", "plus_EMA50"):
        if child[name].notna().sum() < 2000:
            raise ValueError("OOF Child coverage unexpectedly low")
    result = {
        "status": "consumed-development-chronological-oof-observation-only",
        "not_official_mt5_economics": True,
        "source_sha256": {"features": sha256(FEATURE_FILE), "labels": sha256(LABELS)},
        "n_decisions": len(d), "n_oof_decisions": len(oof),
        "baseline_parity": {"closed_journeys": int(child.journey.nunique()),
                             "closed_children": len(child), "net_points": float(child.baseline_pnl.sum())},
        "folds": folds, "pooled_scores": pooled,
        "risk_bucket_addon_child": {name: risk_bucket(child, name) for name in
                                    ("H4_H1", "plus_HASTOC", "plus_activity", "plus_raw_swing", "plus_EMA50")},
        "by_year_side": {}, "by_journey_age": {},
    }
    for (year, side), g in oof.groupby(["year", "side"]):
        yy = g.flip_within_3.astype(int).to_numpy()
        result["by_year_side"][f"{year}_{'long' if side == 1 else 'short'}"] = {
            name: score(yy, g[name].to_numpy(dtype=float))
            for name in ("constant", "H4_H1", "plus_activity", "plus_raw_swing", "plus_EMA50")
        }
    oof["age_group"] = pd.cut(oof.journey_bar, bins=[0, 1, 3, 9, math.inf], labels=["1", "2-3", "4-9", "10+"])
    for age, g in oof.groupby("age_group", observed=True):
        yy = g.flip_within_3.astype(int).to_numpy()
        result["by_journey_age"][str(age)] = {
            name: score(yy, g[name].to_numpy(dtype=float))
            for name in ("constant", "H4_H1", "plus_activity", "plus_raw_swing", "plus_EMA50")
        }
    pred.to_csv(OUT / "oof_predictions.csv", index=False)
    child.to_csv(OUT / "child_economics.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({
        "n_oof": len(oof), "baseline": result["baseline_parity"],
        "pooled_brier_auc": {name: [round(value["brier"], 5), round(value["auc"], 4)]
                             for name, value in pooled.items()},
        "top20_addon_net": {name: round(value["net_points"], 2)
                            for name, value in result["risk_bucket_addon_child"].items()},
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build-features", action="store_true")
    group.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    if args.build_features:
        build_features()
    else:
        evaluate()
