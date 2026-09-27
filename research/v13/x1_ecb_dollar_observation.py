"""V13 X1: daily ECB EUR/USD proxy at HA Journey birth, observation only.

Run --build first. The build phase never loads future Journey outcomes.
Run --evaluate only after inspecting the saved feature/source manifest.
See docs/ea/v13/V13_X1_ECB_DOLLAR_OBSERVATION_CONTRACT_20260928.md.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from ha8a_combination_model import fit_logistic, matrix, score


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "output/v13_ha8a_combination_20260928/decision_features.csv"
CHILD = ROOT / "output/v13_ha8a_combination_20260928/child_economics.csv"
GOLD_H4 = ROOT / "data/GOLD#/GOLD#_H4_202201030000_202609230000.csv"
OUT = ROOT / "output/v13_x1_ecb_dollar_20260928"
RAW = OUT / "ecb_exr_d_usd_eur_sp00_a.csv"
FEATURE = OUT / "journey_birth_features.csv"
MANIFEST = OUT / "feature_manifest.json"
API = (
    "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
    "?startPeriod=2022-01-01&endPeriod=2026-08-28&format=csvdata"
)
EXPECTED_SOURCE_HASH = "dc2a082cddd16359da8cb518cd535747297beecad521d40821034e0bf543be0d"
EXPECTED_H4_HASH = "b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf"
FOLDS = [
    ("2024-H2", "2024-07-01", "2025-01-01"),
    ("2025-H1", "2025-01-01", "2025-07-01"),
    ("2025-H2", "2025-07-01", "2026-01-01"),
    ("2026-to-cutoff", "2026-01-01", "2026-09-01"),
]
BASE_NUMS = ["journey_bar", "h4_body_ratio", "h4_raw_close_normalized", "h1_trailing_opposed"]
BASE_CATS = ["side", "h4_delta_contract", "h4_wick_present", "h4_wick_reappeared", "h1_path_state"]
EXTERNAL_NUMS = ["usd_change1_norm", "usd_change5_norm"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def get_raw() -> None:
    if RAW.exists():
        return
    OUT.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(API, headers={"User-Agent": "V13-X1-research/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read()
    if not body.startswith(b"KEY,FREQ,CURRENCY"):
        raise ValueError("ECB response is not the expected CSV series")
    RAW.write_bytes(body)


def source_rows():
    with RAW.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not {"KEY", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS"}.issubset(reader.fieldnames or []):
            raise ValueError("ECB CSV schema mismatch")
        previous = None
        for row in reader:
            if row["KEY"] != "EXR.D.USD.EUR.SP00.A":
                raise ValueError("wrong ECB series")
            observed = date.fromisoformat(row["TIME_PERIOD"])
            value = float(row["OBS_VALUE"])
            if previous is not None and observed <= previous:
                raise ValueError("ECB duplicate or nonchronological observation")
            if not math.isfinite(value) or value <= 0:
                raise ValueError("invalid ECB exchange rate")
            previous = observed
            yield observed, value, row["OBS_STATUS"]


def build() -> None:
    get_raw()
    if sha256(SOURCE) != EXPECTED_SOURCE_HASH or sha256(GOLD_H4) != EXPECTED_H4_HASH:
        raise ValueError("V13 gold source/feature hash changed; re-audit authority before X1")
    gold = pd.read_csv(SOURCE, parse_dates=["signal", "known_at"])
    if gold.duplicated(["signal", "journey"]).any() or len(gold) != 4108:
        raise ValueError("HA-8A source grain/coverage mismatch")
    if not gold.known_at.is_monotonic_increasing:
        raise ValueError("GOLD decision timestamps not chronological")

    iterator = iter(source_rows())
    pending = next(iterator, None)  # one external record may be buffered, never used early
    prior_levels: list[float] = []
    latest = None
    rows = []
    for item in gold.itertuples(index=False):
        safe_date = item.known_at.date() - timedelta(days=2)
        while pending is not None and pending[0] <= safe_date:
            observed, eurusd, status = pending
            level = -math.log(eurusd)
            one = five = math.nan
            if len(prior_levels) >= 25:
                one = level - prior_levels[-1]
                five = level - prior_levels[-5]
                prior_one = [abs(prior_levels[i] - prior_levels[i - 1])
                             for i in range(len(prior_levels) - 20, len(prior_levels))]
                prior_five = [abs(prior_levels[i] - prior_levels[i - 5])
                              for i in range(len(prior_levels) - 20, len(prior_levels))]
                d1, d5 = statistics.median(prior_one), statistics.median(prior_five)
                one = one / d1 if d1 > 0 else math.nan
                five = five / d5 if d5 > 0 else math.nan
            latest = (observed, eurusd, status, one, five)
            prior_levels.append(level)
            pending = next(iterator, None)
        if latest is None or latest[0] > safe_date:
            raise ValueError("missing causally available ECB observation")
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
            "ecb_observation_date": latest[0].isoformat(),
            "ecb_age_broker_calendar_days": (item.known_at.date() - latest[0]).days,
            "ecb_eurusd": latest[1], "ecb_obs_status": latest[2],
            "usd_change1_norm": latest[3], "usd_change5_norm": latest[4],
        })
    feature = pd.DataFrame(rows)
    if feature[EXTERNAL_NUMS].isna().any().any():
        raise ValueError("missing ECB normalized feature after 2022 warm-up")
    if feature.ecb_age_broker_calendar_days.min() < 2:
        raise ValueError("ECB publication lag violated")
    feature.to_csv(FEATURE, index=False)
    manifest = {
        "source_url": API,
        "raw_ecb_sha256": sha256(RAW),
        "gold_h4_sha256": sha256(GOLD_H4),
        "ha8a_decision_features_sha256": sha256(SOURCE),
        "x1_feature_sha256": sha256(FEATURE),
        "feature_rows": len(feature),
        "journey_birth_rows": int((feature.journey_bar == 1).sum()),
        "ecb_min_date_used": feature.ecb_observation_date.min(),
        "ecb_max_date_used": feature.ecb_observation_date.max(),
        "ecb_distinct_dates_used": int(feature.ecb_observation_date.nunique()),
        "ecb_age_days": {"min": int(feature.ecb_age_broker_calendar_days.min()),
                         "median": float(feature.ecb_age_broker_calendar_days.median()),
                         "max": int(feature.ecb_age_broker_calendar_days.max()),
                         "over_5_rows": int((feature.ecb_age_broker_calendar_days > 5).sum())},
        "statuses_used": feature.ecb_obs_status.value_counts().to_dict(),
        "publication_lag": "ECB observation date <= broker known_at date minus 2 calendar days",
        "future_outcomes_loaded_during_build": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def bucket(frame: pd.DataFrame, column: str) -> dict:
    ordered = frame.sort_values([column, "signal"], ascending=[False, True])
    high = ordered.head(int(math.ceil(0.2 * len(ordered))))
    losses = frame.journey_loss
    repeat = frame.prior_journey_loss & losses
    high_repeat = high.prior_journey_loss & high.journey_loss
    positive = high.loc[high.journey_net > 0, "journey_net"]
    negative = high.loc[high.journey_net < 0, "journey_net"]
    long = high.loc[high.journey_len >= 10]
    return {
        "eligible": int(len(frame)), "high_risk_n": int(len(high)),
        "losses_all": int(losses.sum()), "losses_high": int(high.journey_loss.sum()),
        "repeat_losses_all": int(repeat.sum()), "repeat_losses_high": int(high_repeat.sum()),
        "winners_high": int((high.journey_net > 0).sum()),
        "gross_winners_high": float(positive.sum()),
        "gross_losers_high": float(negative.sum()),
        "net_high": float(high.journey_net.sum()),
        "long_journeys_high": int(len(long)),
        "long_journey_net_high": float(long.journey_net.sum()),
        "profitable_long_journeys_high": int((long.journey_net > 0).sum()),
        "top_5_winners_high": [float(v) for v in positive.nlargest(5)],
    }


def evaluate() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(FEATURE) != manifest["x1_feature_sha256"] or sha256(RAW) != manifest["raw_ecb_sha256"]:
        raise ValueError("X1 source or causal feature ledger changed")
    features = pd.read_csv(FEATURE, parse_dates=["signal", "known_at"])
    child = pd.read_csv(CHILD, parse_dates=["signal"])
    if len(child) != 3858 or abs(child.baseline_pnl.sum() - 8147.11) >= 0.02:
        raise ValueError("Baseline-0 structural parity failed")
    grouped = child.groupby("journey").agg(
        journey_net=("baseline_pnl", "sum"), journey_len=("journey_len", "first"),
        child_count=("journey_bar", "count"),
    )
    starts = features.loc[features.journey_bar == 1].copy().set_index("journey")
    joined = starts.join(grouped, how="inner", validate="one_to_one")
    if len(joined) != 965 or abs(joined.journey_net.sum() - 8147.11) >= 0.02:
        raise ValueError("closed-Journey count/points parity failed")
    joined["end_known_at"] = starts.loc[joined.index + 1, "known_at"].to_numpy()
    joined["journey_loss"] = (joined.journey_net < 0).astype(int)
    prior = joined.journey_loss.shift(1)
    joined["prior_journey_loss"] = prior.fillna(0).astype(bool)
    joined["year"] = joined.signal.dt.year
    joined = joined.reset_index().sort_values("signal")
    joined["fold"] = ""
    for name in ("constant", "H4_H1", "plus_ECB"):
        joined[name] = np.nan

    fold_scores = {}
    for fold_name, start, end in FOLDS:
        test = joined[(joined.signal >= start) & (joined.signal < end)]
        if test.empty:
            raise ValueError("empty test block")
        train = joined[(joined.signal < start) & (joined.end_known_at < test.known_at.min())]
        if len(train) < 70:
            raise ValueError(f"insufficient causally closed training Journeys for {fold_name}")
        joined.loc[test.index, "fold"] = fold_name
        y_train = train.journey_loss.to_numpy(dtype=float)
        y_test = test.journey_loss.to_numpy(dtype=float)
        joined.loc[test.index, "constant"] = float(y_train.mean())
        for name, nums in (("H4_H1", BASE_NUMS),
                           ("plus_ECB", BASE_NUMS + EXTERNAL_NUMS)):
            x_train, x_test = matrix(train, test, nums, BASE_CATS)
            beta = fit_logistic(x_train, y_train)
            joined.loc[test.index, name] = 1 / (1 + np.exp(-np.clip(x_test @ beta, -35, 35)))
        fold_scores[fold_name] = {
            "train_n": int(len(train)), "test_n": int(len(test)),
            "event_rate": float(y_test.mean()),
            "scores": {m: score(y_test, test_predictions(joined, test.index, m))
                       for m in ("constant", "H4_H1", "plus_ECB")},
        }

    oof = joined[joined.fold != ""].copy()
    y = oof.journey_loss.to_numpy(dtype=float)
    models = ("constant", "H4_H1", "plus_ECB")
    summary = {
        "status": "CONSUMED DEVELOPMENT / OBSERVATION ONLY / NO STRATEGY ACTION",
        "manifest": manifest,
        "structural_parity": {"journeys": len(joined), "children": len(child),
                              "net_points": float(joined.journey_net.sum())},
        "oof": {"journeys": len(oof), "losses": int(y.sum()),
                "repeated_loss_journeys": int((oof.prior_journey_loss & oof.journey_loss.astype(bool)).sum()),
                "scores": {m: score(y, oof[m].to_numpy(dtype=float)) for m in models},
                "high_predicted_loss_20pct": {m: bucket(oof, m) for m in ("H4_H1", "plus_ECB")}},
        "folds": fold_scores,
        "year_side": {},
    }
    for (year, side), group in oof.groupby(["year", "side"]):
        label = f"{year}_{'LONG' if side == 1 else 'SHORT'}"
        gy = group.journey_loss.to_numpy(dtype=float)
        summary["year_side"][label] = {
            "n": len(group), "loss_rate": float(gy.mean()),
            "h4_h1_brier": score(gy, group.H4_H1.to_numpy(dtype=float))["brier"],
            "plus_ecb_brier": score(gy, group.plus_ECB.to_numpy(dtype=float))["brier"],
        }
    oof.to_csv(OUT / "journey_oof_diagnostic.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"oof": summary["oof"], "folds": {
        k: {"train_n": v["train_n"], "test_n": v["test_n"], "brier": {
            m: v["scores"][m]["brier"] for m in models}}
        for k, v in fold_scores.items()}}, indent=2))


def test_predictions(frame: pd.DataFrame, index: pd.Index, name: str) -> np.ndarray:
    return frame.loc[index, name].to_numpy(dtype=float)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    build() if args.build else evaluate()
