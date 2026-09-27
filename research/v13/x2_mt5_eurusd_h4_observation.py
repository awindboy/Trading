"""V13 X2 same-broker EURUSD# H4 observation, no trading action.

Run --export, then --build (future outcomes not loaded), then --evaluate.
The frozen source/timing/target contract is under docs/ea/v13/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ha8a_combination_model import fit_logistic, matrix, score
from x1_ecb_dollar_observation import bucket


ROOT = Path(__file__).resolve().parents[2]
H4 = ROOT / "data/GOLD#/GOLD#_H4_202201030000_202609230000.csv"
SOURCE = ROOT / "output/v13_ha8a_combination_20260928/decision_features.csv"
CHILD = ROOT / "output/v13_ha8a_combination_20260928/child_economics.csv"
OUT = ROOT / "output/v13_x2_mt5_eurusd_h4_20260928"
FX = OUT / "eurusd_hash_h4_mt5.csv"
EXPORT_MANIFEST = OUT / "export_manifest.json"
FEATURE = OUT / "journey_birth_features.csv"
FEATURE_MANIFEST = OUT / "feature_manifest.json"
EXPECTED_H4 = "b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf"
EXPECTED_SOURCE = "dc2a082cddd16359da8cb518cd535747297beecad521d40821034e0bf543be0d"
START = datetime(2022, 1, 1, tzinfo=timezone.utc)
STOP = datetime(2026, 8, 28, 20, tzinfo=timezone.utc)
FOLDS = [
    ("2024-H2", "2024-07-01", "2025-01-01"),
    ("2025-H1", "2025-01-01", "2025-07-01"),
    ("2025-H2", "2025-07-01", "2026-01-01"),
    ("2026-to-cutoff", "2026-01-01", "2026-09-01"),
]
BASE_NUMS = ["journey_bar", "h4_body_ratio", "h4_raw_close_normalized", "h1_trailing_opposed"]
BASE_CATS = ["side", "h4_delta_contract", "h4_wick_present", "h4_wick_reappeared", "h1_path_state"]
FX_NUMS = ["usd_h4_change1_norm", "usd_h4_change3_norm"]
MODELS = ("constant", "H4_H1", "plus_FX", "plus_alignment")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def export(terminal: str) -> None:
    if FX.exists():
        raise FileExistsError("X2 source already frozen; do not silently overwrite the FX export")
    if sha256(H4) != EXPECTED_H4:
        raise ValueError("GOLD# H4 source hash changed")
    import MetaTrader5 as mt5

    if not mt5.initialize(path=terminal, timeout=10000):
        raise RuntimeError(f"MT5 terminal connection failed: {mt5.last_error()}")
    try:
        gold = mt5.copy_rates_range("GOLD#", mt5.TIMEFRAME_H4, START, STOP)
        fx = mt5.copy_rates_range("EURUSD#", mt5.TIMEFRAME_H4, START, STOP)
        if gold is None or fx is None:
            raise RuntimeError(f"MT5 historical data unavailable: {mt5.last_error()}")
        terminal_build = mt5.terminal_info().build
    finally:
        mt5.shutdown()

    gold_api = pd.DataFrame(gold)
    fx_api = pd.DataFrame(fx)
    gold_csv = pd.read_csv(H4, sep="\t")
    gold_csv["time"] = pd.to_datetime(
        gold_csv["<DATE>"] + " " + gold_csv["<TIME>"],
        format="%Y.%m.%d %H:%M:%S",
    ).dt.as_unit("s").astype("int64")
    gold_csv = gold_csv[gold_csv.time <= int(STOP.timestamp())].reset_index(drop=True)
    if len(gold_api) != len(gold_csv) or not np.array_equal(gold_api.time, gold_csv.time):
        raise ValueError("MT5 GOLD# H4 timestamps differ from frozen source")
    for source_name, api_name in (("<OPEN>", "open"), ("<HIGH>", "high"),
                                  ("<LOW>", "low"), ("<CLOSE>", "close")):
        if not np.allclose(gold_csv[source_name], gold_api[api_name], rtol=0, atol=1e-8):
            raise ValueError(f"MT5 GOLD# H4 {api_name} differs from frozen source")
    if fx_api.time.duplicated().any() or not fx_api.time.is_monotonic_increasing:
        raise ValueError("EURUSD# H4 timestamp duplication/order failure")
    if not gold_api.time.isin(fx_api.time).all():
        raise ValueError("a GOLD# H4 timestamp lacks same-clock EURUSD# H4")
    if (fx_api[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("nonpositive EURUSD# OHLC")
    if ((fx_api.high < fx_api[["open", "close"]].max(axis=1)) |
            (fx_api.low > fx_api[["open", "close"]].min(axis=1)) |
            (fx_api.high < fx_api.low)).any():
        raise ValueError("invalid EURUSD# H4 OHLC geometry")
    OUT.mkdir(parents=True, exist_ok=True)
    fx_api["time"] = pd.to_datetime(fx_api.time, unit="s", utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
    fx_api.to_csv(FX, index=False)
    manifest = {
        "terminal_build": int(terminal_build), "symbol": "EURUSD#", "timeframe": "H4",
        "request_start_utc": START.isoformat(), "request_stop_utc": STOP.isoformat(),
        "gold_source_sha256": sha256(H4), "gold_api_rows": len(gold_api),
        "gold_exact_timestamp_ohlc_matches": len(gold_api),
        "fx_rows": len(fx_api), "fx_same_timestamp_gold_coverage": int(len(gold_api)),
        "fx_first_timestamp": fx_api.time.iloc[0], "fx_last_timestamp": fx_api.time.iloc[-1],
        "fx_csv_sha256": sha256(FX),
        "metatrader_history_api": "https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py",
    }
    EXPORT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def fx_rows():
    """Reveal only the next FX source row as gold decisions advance."""
    with FX.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not {"time", "close"}.issubset(reader.fieldnames or []):
            raise ValueError("FX H4 export schema mismatch")
        previous = None
        for row in reader:
            stamp = pd.Timestamp(row["time"])
            close = float(row["close"])
            if previous is not None and stamp <= previous:
                raise ValueError("FX H4 duplicate or nonchronological timestamp")
            if not math.isfinite(close) or close <= 0:
                raise ValueError("invalid FX H4 close")
            previous = stamp
            yield stamp, close


def build() -> None:
    export_manifest = json.loads(EXPORT_MANIFEST.read_text(encoding="utf-8"))
    if sha256(FX) != export_manifest["fx_csv_sha256"] or sha256(SOURCE) != EXPECTED_SOURCE:
        raise ValueError("FX export or HA-8A decision source changed")
    gold = pd.read_csv(SOURCE, parse_dates=["signal", "known_at"])
    if len(gold) != 4108 or gold.duplicated(["signal", "journey"]).any():
        raise ValueError("HA-8A source decision grain mismatch")
    if not gold.known_at.is_monotonic_increasing:
        raise ValueError("HA decision chronology mismatch")

    fx_iter = iter(fx_rows())
    pending = next(fx_iter, None)  # at most one future source row buffered, not used
    levels: list[float] = []
    latest = None
    rows = []
    for item in gold.itertuples(index=False):
        while pending is not None and pending[0] <= item.signal:
            level = -math.log(pending[1])
            one = three = math.nan
            if len(levels) >= 23:
                one = level - levels[-1]
                three = level - levels[-3]
                prior_one = [abs(levels[i] - levels[i - 1])
                             for i in range(len(levels) - 20, len(levels))]
                prior_three = [abs(levels[i] - levels[i - 3])
                               for i in range(len(levels) - 20, len(levels))]
                d1, d3 = statistics.median(prior_one), statistics.median(prior_three)
                one = one / d1 if d1 > 0 else math.nan
                three = three / d3 if d3 > 0 else math.nan
            latest = (pending[0], pending[1], one, three)
            levels.append(level)
            pending = next(fx_iter, None)
        if latest is None or latest[0] != item.signal:
            raise ValueError(f"missing exact same-H4 EURUSD# bar at {item.signal}")
        if item.known_at < item.signal + pd.Timedelta(hours=4):
            raise ValueError("external H4 bar not complete by decision known_at")
        rows.append({
            "signal": item.signal, "known_at": item.known_at, "journey": item.journey,
            "journey_bar": item.journey_bar, "side": item.side,
            "h4_body_ratio": item.h4_body_ratio,
            "h4_raw_close_normalized": item.h4_raw_close_normalized,
            "h1_trailing_opposed": item.h1_trailing_opposed,
            "h4_delta_contract": item.h4_delta_contract,
            "h4_wick_present": item.h4_wick_present,
            "h4_wick_reappeared": item.h4_wick_reappeared,
            "h1_path_state": item.h1_path_state,
            "fx_signal_bar": latest[0], "fx_close": latest[1],
            "usd_h4_change1_norm": latest[2], "usd_h4_change3_norm": latest[3],
            "side_x_usd_h4_change3": int(item.side) * latest[3],
        })
    feature = pd.DataFrame(rows)
    if feature[[*FX_NUMS, "side_x_usd_h4_change3"]].isna().any().any():
        raise ValueError("FX H4 normalized feature missing after 2022 warm-up")
    feature.to_csv(FEATURE, index=False)
    manifest = {
        "gold_h4_sha256": sha256(H4), "ha8a_feature_sha256": sha256(SOURCE),
        "fx_export_sha256": sha256(FX), "x2_feature_sha256": sha256(FEATURE),
        "decision_rows": len(feature), "birth_rows": int((feature.journey_bar == 1).sum()),
        "exact_fx_signal_bar_matches": int((feature.signal == feature.fx_signal_bar).sum()),
        "future_outcomes_loaded_during_build": False,
    }
    FEATURE_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def evaluate() -> None:
    manifest = json.loads(FEATURE_MANIFEST.read_text(encoding="utf-8"))
    if sha256(FEATURE) != manifest["x2_feature_sha256"] or sha256(FX) != manifest["fx_export_sha256"]:
        raise ValueError("FX source or feature ledger changed after freezing")
    features = pd.read_csv(FEATURE, parse_dates=["signal", "known_at"])
    child = pd.read_csv(CHILD, parse_dates=["signal"])
    if len(child) != 3858 or abs(child.baseline_pnl.sum() - 8147.11) >= 0.02:
        raise ValueError("Baseline-0 Child parity failed")
    grouped = child.groupby("journey").agg(
        journey_net=("baseline_pnl", "sum"), journey_len=("journey_len", "first"),
        child_count=("journey_bar", "count"),
    )
    starts = features.loc[features.journey_bar == 1].copy().set_index("journey")
    joined = starts.join(grouped, how="inner", validate="one_to_one")
    if len(joined) != 965 or abs(joined.journey_net.sum() - 8147.11) >= 0.02:
        raise ValueError("Baseline-0 Journey parity failed")
    joined["end_known_at"] = starts.loc[joined.index + 1, "known_at"].to_numpy()
    joined["journey_loss"] = (joined.journey_net < 0).astype(int)
    joined["prior_journey_loss"] = joined.journey_loss.shift(1).fillna(0).astype(bool)
    joined["year"] = joined.signal.dt.year
    joined = joined.reset_index().sort_values("signal")
    joined["fold"] = ""
    for name in MODELS:
        joined[name] = np.nan

    folds = {}
    for fold_name, start, end in FOLDS:
        test = joined[(joined.signal >= start) & (joined.signal < end)]
        if test.empty:
            raise ValueError("empty test block")
        train = joined[(joined.signal < start) & (joined.end_known_at < test.known_at.min())]
        if len(train) < 70:
            raise ValueError("insufficient causally closed training Journeys")
        joined.loc[test.index, "fold"] = fold_name
        y_train = train.journey_loss.to_numpy(dtype=float)
        y_test = test.journey_loss.to_numpy(dtype=float)
        joined.loc[test.index, "constant"] = float(y_train.mean())
        for name, nums in (
            ("H4_H1", BASE_NUMS),
            ("plus_FX", BASE_NUMS + FX_NUMS),
            ("plus_alignment", BASE_NUMS + FX_NUMS + ["side_x_usd_h4_change3"]),
        ):
            x_train, x_test = matrix(train, test, nums, BASE_CATS)
            beta = fit_logistic(x_train, y_train)
            joined.loc[test.index, name] = 1 / (1 + np.exp(-np.clip(x_test @ beta, -35, 35)))
        folds[fold_name] = {
            "train_n": int(len(train)), "test_n": int(len(test)),
            "scores": {m: score(y_test, joined.loc[test.index, m].to_numpy(dtype=float))
                       for m in MODELS},
        }

    oof = joined[joined.fold != ""].copy()
    y = oof.journey_loss.to_numpy(dtype=float)
    summary = {
        "status": "CONSUMED DEVELOPMENT / OBSERVATION ONLY / NO ACTION",
        "source_manifest": json.loads(EXPORT_MANIFEST.read_text(encoding="utf-8")),
        "feature_manifest": manifest,
        "parity": {"journeys": len(joined), "children": len(child),
                   "net_points": float(joined.journey_net.sum())},
        "oof": {"journeys": len(oof), "losses": int(y.sum()),
                "repeated_losses": int((oof.prior_journey_loss & oof.journey_loss.astype(bool)).sum()),
                "scores": {m: score(y, oof[m].to_numpy(dtype=float)) for m in MODELS},
                "high_predicted_loss_20pct": {m: bucket(oof, m) for m in MODELS[1:]}},
        "folds": folds,
        "year_side": {},
    }
    for (year, side), group in oof.groupby(["year", "side"]):
        label = f"{year}_{'LONG' if side == 1 else 'SHORT'}"
        gy = group.journey_loss.to_numpy(dtype=float)
        summary["year_side"][label] = {
            "n": len(group), "loss_rate": float(gy.mean()),
            "brier": {m: score(gy, group[m].to_numpy(dtype=float))["brier"] for m in MODELS},
        }
    oof.to_csv(OUT / "journey_oof_diagnostic.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "oof": {"journeys": summary["oof"]["journeys"], "losses": summary["oof"]["losses"],
                "scores": {m: {key: summary["oof"]["scores"][m][key]
                                for key in ("brier", "log_loss", "auc", "calibration_ece_10_fixed_bins")}
                           for m in MODELS},
                "high_predicted_loss_20pct": summary["oof"]["high_predicted_loss_20pct"]},
        "fold_brier": {k: {m: v["scores"][m]["brier"] for m in MODELS}
                       for k, v in folds.items()},
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--export", action="store_true")
    modes.add_argument("--build", action="store_true")
    modes.add_argument("--evaluate", action="store_true")
    parser.add_argument("--terminal", default=r"C:\Program Files\XM Global MT5\terminal64.exe")
    args = parser.parse_args()
    if args.export:
        export(args.terminal)
    elif args.build:
        build()
    else:
        evaluate()
