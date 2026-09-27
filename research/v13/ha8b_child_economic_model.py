"""V13 HA-8B frozen Child-marginal economic model, observation only.

Run --build-features before --evaluate. The first phase streams known state
without opening any future-label table; the second constructs terminal labels
and chronological OOF diagnostics. See the HA-8B contract before changing this.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import log_loss, mean_absolute_error, mean_squared_error, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "output/v13_ha8a_combination_20260928/decision_features.csv"
SOURCE_MANIFEST = ROOT / "output/v13_ha8a_combination_20260928/feature_manifest.json"
H4 = ROOT / "data/GOLD#/GOLD#_H4_202201030000_202609230000.csv"
OUT = ROOT / "output/v13_ha8b_child_economic_20260928"
FEATURES = OUT / "decision_features.csv"
MANIFEST = OUT / "feature_manifest.json"
FOLDS = (
    ("2024-H2", "2024-07-01", "2025-01-01"),
    ("2025-H1", "2025-01-01", "2025-07-01"),
    ("2025-H2", "2025-07-01", "2026-01-01"),
    ("2026-cutoff", "2026-01-01", "2026-09-01"),
)

BASE_NUM = ("journey_bar", "h4_body_ratio", "h4_raw_close_normalized", "h1_trailing_opposed")
BASE_CAT = ("side", "h4_delta_contract", "h4_wick_present", "h4_wick_reappeared", "h1_path_state")
POSITION_NUM = ("live_avg_pnl_ranges", "last_journey_avg_pnl_ranges", "log1p_prior_loss_streak", "has_prior_journey")
CONTEXT_NUM = (
    "journey_hastoc10", "log_relative_tick_volume20", "persistent_x_log_activity",
    "progress_close_distance_ranges", "adverse_close_distance_ranges",
)
CONTEXT_CAT = ("progress_state", "adverse_state", "ema50_slope_opposed", "ema50_position_opposed")
SPECS = {
    "h4_h1": (BASE_NUM, BASE_CAT),
    "plus_position": (BASE_NUM + POSITION_NUM, BASE_CAT),
    "plus_context": (BASE_NUM + POSITION_NUM + CONTEXT_NUM, BASE_CAT + CONTEXT_CAT),
}
FAMILIES = ("linear", "shallow")
MODELS = ("stage_mean", *(f"{family}_{spec}" for family in FAMILIES for spec in SPECS))
FIELDS = (
    "signal", "known_at", "journey", "journey_bar", "side", "range20", "audit_execution_open",
    *BASE_NUM[1:], *BASE_CAT[1:], *POSITION_NUM, *CONTEXT_NUM, *CONTEXT_CAT,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def h4_stamp(row: dict[str, str]) -> datetime:
    return datetime.strptime(row["<DATE>"] + " " + row["<TIME>"], "%Y.%m.%d %H:%M:%S")


def preceding_range_at_signal(h4_reader: csv.DictReader, ranges: deque[float], signal: datetime) -> float:
    """Advance raw H4 only through this signal; never inspect a later bar."""
    for bar in h4_reader:
        current = h4_stamp(bar)
        if current > signal:
            raise ValueError(f"missing H4 signal bar {signal}; next is {current}")
        scale = float(np.median(ranges)) if len(ranges) == 20 else math.nan
        hi, lo = float(bar["<HIGH>"]), float(bar["<LOW>"])
        if hi <= lo:
            raise ValueError(f"invalid H4 range at {current}")
        ranges.append(hi - lo)
        if current == signal:
            if not math.isfinite(scale) or scale <= 0:
                raise ValueError(f"missing causal prior-20 H4 scale at {signal}")
            return scale
    raise ValueError(f"H4 ended before feature signal {signal}")


def build_features() -> None:
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if sha256(SOURCE) != source_manifest["feature_ledger_sha256"]:
        raise ValueError("HA-8A frozen feature source has changed")
    if sha256(H4) != source_manifest["sha256"][str(H4.relative_to(ROOT))]:
        raise ValueError("H4 source has changed since HA-8A feature construction")
    OUT.mkdir(parents=True, exist_ok=True)

    ranges: deque[float] = deque(maxlen=20)
    active_journey = None
    active_side = 0
    entries: list[float] = []
    last_journey_avg_pnl = 0.0
    loss_streak = 0
    prior_available = False
    closed_journeys = 0
    closed_children = 0
    closed_net = 0.0
    n = 0
    last_signal = last_known = None
    last_bar_no = 0
    with H4.open(newline="", encoding="utf-8-sig") as h4_stream, SOURCE.open(newline="", encoding="utf-8") as src, FEATURES.open("w", newline="", encoding="utf-8") as dst:
        h4_reader = csv.DictReader(h4_stream, delimiter="\t")
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=FIELDS)
        writer.writeheader()
        for row in reader:
            signal, known = stamp(row["signal"]), stamp(row["known_at"])
            if (last_signal is not None and signal <= last_signal) or (last_known is not None and known <= last_known):
                raise ValueError("source ledger is not strictly chronological")
            if known < signal + pd.Timedelta(hours=4):
                raise ValueError("H4 feature known before completed signal bar")
            scale = preceding_range_at_signal(h4_reader, ranges, signal)
            price = float(row["execution_raw_open"])
            if not math.isfinite(price) or price <= 0:
                raise ValueError("invalid decision-time execution price")
            journey, side, bar_no = int(row["journey"]), int(row["side"]), int(row["journey_bar"])
            if active_journey != journey:
                if active_journey is not None:
                    if journey != active_journey + 1 or side != -active_side or bar_no != 1:
                        raise ValueError("Journey transition parity failed")
                    pnl = sum(active_side * (price - entry) for entry in entries)
                    last_journey_avg_pnl = (pnl / len(entries)) if entries else 0.0
                    loss_streak = loss_streak + 1 if pnl < 0 else 0
                    closed_net += pnl
                    closed_children += len(entries)
                    closed_journeys += 1
                    prior_available = True
                else:
                    if journey != 1 or bar_no != 1:
                        raise ValueError("first Journey parity failed")
                active_journey, active_side, entries = journey, side, []
            elif side != active_side or bar_no != last_bar_no + 1:
                raise ValueError("same-color Journey bar/side continuity failed")
            live = sum(side * (price - entry) for entry in entries) / len(entries) if entries else 0.0
            item = {
                "signal": row["signal"], "known_at": row["known_at"], "journey": journey,
                "journey_bar": bar_no, "side": side, "range20": scale,
                "audit_execution_open": price,
                "live_avg_pnl_ranges": live / scale,
                "last_journey_avg_pnl_ranges": last_journey_avg_pnl / scale if prior_available else 0.0,
                "log1p_prior_loss_streak": math.log1p(loss_streak),
                "has_prior_journey": int(prior_available),
            }
            item.update({name: row[name] for name in (*BASE_NUM[1:], *BASE_CAT[1:], *CONTEXT_NUM, *CONTEXT_CAT)})
            writer.writerow(item)
            if bar_no <= 10:
                entries.append(price)
            n += 1
            last_signal, last_known = signal, known
            last_bar_no = bar_no
    if (n, closed_journeys, closed_children) != (4108, 965, 3858) or abs(closed_net - 8147.11) >= 0.02:
        raise ValueError(f"Baseline structural parity failed: {(n, closed_journeys, closed_children, closed_net)}")
    manifest = {
        "status": "causal-feature-ledger-frozen-before-current-journey-labels",
        "source_head": "29e0073e57553d8fe1fd14b843daf09164a7a248",
        "source_sha256": sha256(SOURCE), "h4_sha256": sha256(H4),
        "features_sha256": sha256(FEATURES), "decision_rows": n,
        "closed_journeys_observed_at_later_flip": closed_journeys,
        "closed_children_observed_at_later_flip": closed_children,
        "closed_child_net_points": round(closed_net, 8),
        "last_signal": str(last_signal), "last_known_at": str(last_known),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def make_labels(features: pd.DataFrame) -> pd.DataFrame:
    journeys = list(features.groupby("journey", sort=True))
    if len(journeys) != 966 or [j for j, _ in journeys] != list(range(1, 967)):
        raise ValueError("unexpected Journey sequence")
    result = []
    previous_total = None
    for (jid, group), (next_jid, next_group) in zip(journeys, journeys[1:]):
        if next_jid != jid + 1:
            raise ValueError("nonconsecutive Journey")
        exit_row = next_group.iloc[0]
        eligible = group[group.journey_bar <= 10]
        if len(eligible) != min(len(group), 10):
            raise ValueError("Child slot parity failed")
        child_pnls = group.side.iloc[0] * (float(exit_row.audit_execution_open) - eligible.audit_execution_open)
        journey_total = float(child_pnls.sum())
        for row, pnl in zip(eligible.itertuples(index=False), child_pnls, strict=True):
            result.append({
                "signal": row.signal, "known_at": row.known_at, "journey": jid,
                "exit_known_at": exit_row.known_at, "journey_len": len(group),
                "journey_total_points": journey_total,
                "repeat_losing_journey": int(previous_total is not None and previous_total < 0 and journey_total < 0),
                "tail_journey": int(len(group) >= 10),
                "child_pnl_points": float(pnl), "child_pnl_ranges": float(pnl / row.range20),
                "child_loss": int(pnl < 0), "child_win": int(pnl > 0),
            })
        previous_total = journey_total
    label = pd.DataFrame(result)
    if len(label) != 3858 or label.journey.nunique() != 965 or abs(label.child_pnl_points.sum() - 8147.11) >= 0.02:
        raise ValueError("terminal-label economic parity failed")
    return label


def prep(train: pd.DataFrame, test: pd.DataFrame, nums: tuple[str, ...], cats: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    numeric = make_pipeline(SimpleImputer(strategy="median"), StandardScaler())
    categorical = make_pipeline(SimpleImputer(strategy="most_frequent"), OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    transform = ColumnTransformer((("num", numeric, list(nums)), ("cat", categorical, list(cats))), sparse_threshold=0)
    def frame(rows: pd.DataFrame) -> pd.DataFrame:
        data = rows[list(nums + cats)].copy()
        for name in nums:
            data[name] = pd.to_numeric(data[name], errors="coerce")
        for name in cats:
            data[name] = data[name].astype("string").fillna("missing").astype(str)
        return data
    x_train = transform.fit_transform(frame(train))
    x_test = transform.transform(frame(test))
    if not np.isfinite(x_train).all() or not np.isfinite(x_test).all():
        raise ValueError("nonfinite transformed feature")
    return x_train, x_test


def fit_hurdle(train: pd.DataFrame, test: pd.DataFrame, family: str, spec: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x_train, x_test = prep(train, test, *SPECS[spec])
    y = train.child_pnl_ranges.to_numpy(dtype=float)
    if (y > 0).sum() < 60 or (y < 0).sum() < 60:
        raise ValueError("insufficient wins/losses for conditional magnitude heads")
    if family == "linear":
        loss = LogisticRegression(C=1.0, max_iter=1000)
        positive = Ridge(alpha=20.0)
        negative = Ridge(alpha=20.0)
    elif family == "shallow":
        opts = dict(max_leaf_nodes=7, max_iter=100, learning_rate=0.05,
                    min_samples_leaf=60, l2_regularization=10.0,
                    early_stopping=False, random_state=13)
        loss = HistGradientBoostingClassifier(**opts)
        positive = HistGradientBoostingRegressor(**opts)
        negative = HistGradientBoostingRegressor(**opts)
    else:
        raise ValueError(family)
    loss.fit(x_train, (y < 0).astype(int))
    positive.fit(x_train[y > 0], y[y > 0])
    negative.fit(x_train[y < 0], -y[y < 0])
    p_loss = np.clip(loss.predict_proba(x_test)[:, 1], 1e-6, 1 - 1e-6)
    mu_pos = np.maximum(positive.predict(x_test), 0.0)
    mu_neg = np.maximum(negative.predict(x_test), 0.0)
    return p_loss, mu_pos, mu_neg


def stage_mean(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    predictions = np.zeros((len(test), 3))
    for stage in (1, 2):
        tr = train[train.journey_bar.eq(1) if stage == 1 else train.journey_bar.gt(1)]
        idx = (test.journey_bar.eq(1) if stage == 1 else test.journey_bar.gt(1)).to_numpy()
        values = tr.child_pnl_ranges.to_numpy(dtype=float)
        predictions[idx] = (float((values < 0).mean()), float(values[values > 0].mean()), float(-values[values < 0].mean()))
    return predictions[:, 0], predictions[:, 1], predictions[:, 2]


def binary_scores(y: np.ndarray, p: np.ndarray) -> dict:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {"n": len(y), "rate": float(y.mean()), "predicted_rate": float(p.mean()),
            "brier": float(np.mean((p-y)**2)), "log_loss": float(log_loss(y, p, labels=[0, 1])),
            "auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None}


def model_scores(rows: pd.DataFrame, name: str) -> dict:
    actual = rows.child_pnl_ranges.to_numpy(dtype=float)
    estimated = rows[f"ev_{name}"].to_numpy(dtype=float)
    return {
        "loss": binary_scores(rows.child_loss.to_numpy(dtype=int), rows[f"p_loss_{name}"].to_numpy(dtype=float)),
        "ev_n": len(rows), "ev_actual_mean": float(actual.mean()),
        "ev_predicted_mean": float(estimated.mean()),
        "ev_mae": float(mean_absolute_error(actual, estimated)),
        "ev_rmse": float(mean_squared_error(actual, estimated)**0.5),
        "ev_bias": float((estimated - actual).mean()),
    }


def bucket(rows: pd.DataFrame, name: str, top10: set[int]) -> dict:
    z = rows.sort_values([f"ev_{name}", "signal"], ascending=[True, True])
    low = z.head(math.ceil(len(z) / 5))
    def digest(part: pd.DataFrame) -> dict:
        tail = part[part.tail_journey == 1]
        largest = part[part.journey.isin(top10)]
        journey_points = part.groupby("journey").child_pnl_points.sum().sort_values()
        return {
            "n": len(part), "journeys": int(part.journey.nunique()),
            "losses": int(part.child_loss.sum()), "wins": int(part.child_win.sum()),
            "flats": int(len(part) - part.child_loss.sum() - part.child_win.sum()),
            "gross_win_points": float(part.loc[part.child_pnl_points > 0, "child_pnl_points"].sum()),
            "gross_loss_points": float(part.loc[part.child_pnl_points < 0, "child_pnl_points"].sum()),
            "net_points": float(part.child_pnl_points.sum()),
            "mean_actual_ranges": float(part.child_pnl_ranges.mean()),
            "mean_predicted_ranges": float(part[f"ev_{name}"].mean()),
            "tail_children": len(tail), "tail_net_points": float(tail.child_pnl_points.sum()),
            "tail_winning_children": int(tail.child_win.sum()),
            "top10_winning_journey_children": len(largest),
            "top10_winning_journey_net_points": float(largest.child_pnl_points.sum()),
            "worst5_journey_points": float(journey_points.head(5).sum()),
            "best5_journey_points": float(journey_points.tail(5).sum()),
            "repeat_losing_journeys": int(part.loc[part.journey_bar == 1, "repeat_losing_journey"].sum()),
        }
    quintiles = [digest(z.iloc[positions]) for positions in np.array_split(np.arange(len(z)), 5)]
    total_losses = int(z.child_loss.sum())
    total_repeat = int(z.loc[z.journey_bar == 1, "repeat_losing_journey"].sum())
    result = {"eligible": digest(z), "lowest_20pct": digest(low), "low_loss_capture": float(low.child_loss.sum()/total_losses),
              "low_repeat_loss_capture": float(low.loc[low.journey_bar == 1, "repeat_losing_journey"].sum()/total_repeat) if total_repeat else None,
              "descriptive_quintiles_low_to_high": quintiles}
    clustered = low.groupby("journey").agg(points=("child_pnl_points", "sum"), children=("child_pnl_points", "size"))
    values = clustered[["points", "children"]].to_numpy(dtype=float)
    rng = np.random.default_rng(13)
    draws = rng.integers(0, len(values), size=(1000, len(values)))
    resampled = values[draws].sum(axis=1)
    means = resampled[:, 0] / resampled[:, 1]
    result["low_mean_points_per_child_journey_bootstrap_95pct_descriptive"] = [float(x) for x in np.quantile(means, [0.025, 0.975])]
    return result


def evaluate() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(FEATURES) != manifest["features_sha256"]:
        raise ValueError("frozen HA-8B feature ledger hash changed")
    f = pd.read_csv(FEATURES, parse_dates=["signal", "known_at"])
    if len(f) != manifest["decision_rows"] or f[["signal", "journey"]].duplicated().any():
        raise ValueError("feature ledger coverage/uniqueness failure")
    labels = make_labels(f)
    labels.to_csv(OUT / "future_child_labels.csv", index=False)
    d = f.merge(labels, on=["signal", "known_at", "journey"], how="inner", validate="one_to_one")
    if len(d) != 3858 or d.child_pnl_ranges.isna().any():
        raise ValueError("Child feature/label join failure")
    d = d.sort_values(["known_at", "journey_bar"]).reset_index(drop=True)
    pred = d[["signal", "known_at", "journey", "journey_bar", "side", "range20",
              "child_pnl_ranges", "child_pnl_points", "child_loss", "child_win", "tail_journey",
              "repeat_losing_journey", "journey_total_points", "exit_known_at"]].copy()
    pred["fold"] = ""
    for name in MODELS:
        for field in ("p_loss", "mu_pos", "mu_neg", "ev"):
            pred[f"{field}_{name}"] = np.nan
    for family in FAMILIES:
        pred[f"p_tail_{family}"] = np.nan
    folds = {}
    for fold_name, start, end in FOLDS:
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        train_idx = np.flatnonzero((d.exit_known_at < start).to_numpy())
        test_idx = np.flatnonzero(((d.known_at >= start) & (d.known_at < end)).to_numpy())
        train, test = d.iloc[train_idx], d.iloc[test_idx]
        if train.journey.nunique() < 150 or test.journey.nunique() < 100:
            raise ValueError(f"inadequate chronological Journey coverage in {fold_name}")
        if train.journey.max() >= test.journey.min() or train.exit_known_at.max() >= test.known_at.min():
            raise ValueError("Journey/label-time leak across fold")
        pred.loc[test_idx, "fold"] = fold_name
        for name in MODELS:
            if name == "stage_mean":
                p_loss, mu_pos, mu_neg = stage_mean(train, test)
            else:
                family, spec = name.split("_", 1)
                p_loss, mu_pos, mu_neg = fit_hurdle(train, test, family, spec)
            pred.loc[test_idx, f"p_loss_{name}"] = p_loss
            pred.loc[test_idx, f"mu_pos_{name}"] = mu_pos
            pred.loc[test_idx, f"mu_neg_{name}"] = mu_neg
            pred.loc[test_idx, f"ev_{name}"] = (1 - p_loss) * mu_pos - p_loss * mu_neg
        for family in FAMILIES:
            x_train, x_test = prep(train, test, *SPECS["plus_context"])
            if family == "linear":
                model = LogisticRegression(C=1.0, max_iter=1000)
            else:
                model = HistGradientBoostingClassifier(max_leaf_nodes=7, max_iter=100, learning_rate=0.05,
                    min_samples_leaf=60, l2_regularization=10.0, early_stopping=False, random_state=13)
            model.fit(x_train, train.tail_journey.to_numpy(dtype=int))
            pred.loc[test_idx, f"p_tail_{family}"] = model.predict_proba(x_test)[:, 1]
        block = pred.iloc[test_idx]
        folds[fold_name] = {
            "train_journeys": int(train.journey.nunique()), "train_children": len(train),
            "test_journeys": int(test.journey.nunique()), "test_children": len(test),
            "train_last_exit_known_at": str(train.exit_known_at.max()),
            "test_first_known_at": str(test.known_at.min()),
            "excluded_earlier_unclosed_children": int(((d.known_at < start) & (d.exit_known_at >= start)).sum()),
            "scores": {name: model_scores(block, name) for name in MODELS},
        }
    oof = pred[pred.fold != ""].copy()
    if oof.empty or oof[[f"ev_{name}" for name in MODELS]].isna().any().any():
        raise ValueError("missing OOF predictions")
    top10 = set(labels[["journey", "journey_total_points"]].drop_duplicates().nlargest(10, "journey_total_points").journey.astype(int))
    result = {
        "status": "consumed-development-chronological-oof-observation-only",
        "official_mt5_economics": False, "feature_sha256": sha256(FEATURES),
        "label_sha256": sha256(OUT / "future_child_labels.csv"),
        "baseline_parity": {"closed_journeys": int(labels.journey.nunique()), "children": len(labels),
                            "net_price_points": float(labels.child_pnl_points.sum())},
        "oof_journeys": int(oof.journey.nunique()), "oof_children": len(oof),
        "folds": folds,
        "pooled_scores": {name: model_scores(oof, name) for name in MODELS},
        "tail_guardrail": {family: binary_scores(oof.tail_journey.to_numpy(dtype=int), oof[f"p_tail_{family}"].to_numpy(dtype=float)) for family in FAMILIES},
        "top10_winning_journey_ids_diagnostic_only": sorted(top10),
        "birth_buckets": {name: bucket(oof[oof.journey_bar == 1], name, top10) for name in MODELS},
        "addon_buckets": {name: bucket(oof[oof.journey_bar > 1], name, top10) for name in MODELS},
        "fold_stage_buckets": {}, "by_year_side": {}, "by_stage": {},
    }
    for fold_name, _, _ in FOLDS:
        block = oof[oof.fold == fold_name]
        result["fold_stage_buckets"][fold_name] = {
            stage: {name: bucket(group, name, top10) for name in MODELS if name != "stage_mean"}
            for stage, group in (("birth", block[block.journey_bar == 1]),
                                 ("addon", block[block.journey_bar > 1]))
        }
    for (year, side), group in oof.groupby([oof.known_at.dt.year, "side"]):
        result["by_year_side"][f"{year}_{'long' if side == 1 else 'short'}"] = {
            name: model_scores(group, name) for name in MODELS
        }
    for stage, group in (("birth", oof[oof.journey_bar == 1]), ("addon", oof[oof.journey_bar > 1])):
        result["by_stage"][stage] = {name: model_scores(group, name) for name in MODELS}
        result["by_stage"][stage]["tail_guardrail"] = {
            family: binary_scores(group.tail_journey.to_numpy(dtype=int), group[f"p_tail_{family}"].to_numpy(dtype=float))
            for family in FAMILIES
        }
    pred.to_csv(OUT / "oof_predictions.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({
        "baseline_parity": result["baseline_parity"], "oof_journeys": result["oof_journeys"],
        "oof_children": result["oof_children"],
        "pooled_loss_brier": {name: round(result["pooled_scores"][name]["loss"]["brier"], 5) for name in MODELS},
        "pooled_ev_mae": {name: round(result["pooled_scores"][name]["ev_mae"], 5) for name in MODELS},
        "lowest_birth_net_points": {name: round(result["birth_buckets"][name]["lowest_20pct"]["net_points"], 2) for name in MODELS},
        "lowest_addon_net_points": {name: round(result["addon_buckets"][name]["lowest_20pct"]["net_points"], 2) for name in MODELS},
    }, indent=2))


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
