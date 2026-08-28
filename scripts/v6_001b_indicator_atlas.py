#!/usr/bin/env python3
"""V6-001B interpretable indicator atlas.

Research-only. No ML/AI. No threshold optimization.
Consumes:
  1) accepted GOLD# 2023-2025 M1 ZIP/directory;
  2) frozen broad-event path ledger with trigger_time, dir, path.

Outputs descriptive stability tables only. No trading-rule authority.
"""
from __future__ import annotations

import argparse
import json
import math
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

PATH_ORDINAL = {
    "L_CONTINUE": 0,
    "L_RECOVER": 1,
    "W_GIVEBACK": 2,
    "W_CONTINUE": 3,
}


def load_gold(path: Path) -> pd.DataFrame:
    frames = []
    if path.is_dir():
        sources = [(p.name, open(p, "rb")) for p in sorted(path.glob("*.csv"))]
        z = None
    else:
        z = zipfile.ZipFile(path)
        names = sorted(n for n in z.namelist() if n.lower().endswith(".csv"))
        sources = [(n, z.open(n)) for n in names]
    try:
        for _, fh in sources:
            x = pd.read_csv(fh, sep="\t")
            x.columns = [c.strip("<> ").lower() for c in x.columns]
            ts = pd.to_datetime(x["date"].astype(str) + " " + x["time"].astype(str), errors="raise")
            frames.append(pd.DataFrame({
                "open": pd.to_numeric(x["open"], errors="raise").to_numpy(float),
                "high": pd.to_numeric(x["high"], errors="raise").to_numpy(float),
                "low": pd.to_numeric(x["low"], errors="raise").to_numpy(float),
                "close": pd.to_numeric(x["close"], errors="raise").to_numpy(float),
                "tickvol": pd.to_numeric(x.get("tickvol", 0), errors="coerce").fillna(0).to_numpy(float),
            }, index=ts))
    finally:
        for _, fh in sources:
            try:
                fh.close()
            except Exception:
                pass
        if z is not None:
            z.close()
    m1 = pd.concat(frames).sort_index()
    if m1.index.has_duplicates:
        raise RuntimeError("duplicate M1 timestamps")
    return m1


def wilder(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def _aroon_up(arr: np.ndarray, n: int) -> float:
    pos = len(arr) - 1 - int(np.argmax(arr[::-1]))
    since = len(arr) - 1 - pos
    return 100.0 * (n - since) / n


def _aroon_down(arr: np.ndarray, n: int) -> float:
    pos = len(arr) - 1 - int(np.argmin(arr[::-1]))
    since = len(arr) - 1 - pos
    return 100.0 * (n - since) / n


def add_price_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # RSI(14)
    delta = out.close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    rs = wilder(gain, 14) / wilder(loss, 14).replace(0, np.nan)
    out["rsi14"] = 100 - 100 / (1 + rs)

    # DMI/ADX(14)
    up = out.high.diff()
    down = -out.low.diff()
    pdm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=out.index)
    mdm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=out.index)
    prev = out.close.shift(1)
    tr = pd.concat([(out.high - out.low), (out.high - prev).abs(), (out.low - prev).abs()], axis=1).max(axis=1)
    atr14 = wilder(tr, 14)
    pdi = 100 * wilder(pdm, 14) / atr14
    mdi = 100 * wilder(mdm, 14) / atr14
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    out["plus_di14"] = pdi
    out["minus_di14"] = mdi
    out["adx14"] = wilder(dx, 14)
    out["adx_d3"] = out.adx14 - out.adx14.shift(3)

    # Aroon(25)
    n = 25
    out["aroon_up25"] = out.high.rolling(n, min_periods=n).apply(lambda a: _aroon_up(a, n), raw=True)
    out["aroon_down25"] = out.low.rolling(n, min_periods=n).apply(lambda a: _aroon_down(a, n), raw=True)

    # Bollinger(20,2)
    ma = out.close.rolling(20, min_periods=20).mean()
    sd = out.close.rolling(20, min_periods=20).std(ddof=0)
    upper = ma + 2 * sd
    lower = ma - 2 * sd
    out["bb_pctb20"] = (out.close - lower) / (upper - lower).replace(0, np.nan)
    out["bb_width20"] = (upper - lower) / ma.abs().replace(0, np.nan)
    out["bb_width_ratio5"] = out.bb_width20 / out.bb_width20.shift(5)

    # MACD(12,26,9)
    ema12 = out.close.ewm(span=12, adjust=False, min_periods=12).mean()
    ema26 = out.close.ewm(span=26, adjust=False, min_periods=26).mean()
    macd = ema12 - ema26
    sig = macd.ewm(span=9, adjust=False, min_periods=9).mean()
    out["macd_hist"] = macd - sig
    out["macd_hist_d3"] = out.macd_hist - out.macd_hist.shift(3)

    # Stochastic/Williams %R(14)
    ll14 = out.low.rolling(14, min_periods=14).min()
    hh14 = out.high.rolling(14, min_periods=14).max()
    span14 = (hh14 - ll14).replace(0, np.nan)
    out["stoch_k14"] = 100 * (out.close - ll14) / span14
    out["willr14"] = -100 * (hh14 - out.close) / span14

    # ROC(12)
    out["roc12"] = 100 * (out.close / out.close.shift(12) - 1)

    # Donchian(20) location
    ll20 = out.low.rolling(20, min_periods=20).min()
    hh20 = out.high.rolling(20, min_periods=20).max()
    out["donch_pos20"] = (out.close - ll20) / (hh20 - ll20).replace(0, np.nan)

    # Keltner width: EMA20 +/- 2*ATR10
    atr10 = wilder(tr, 10)
    ema20 = out.close.ewm(span=20, adjust=False, min_periods=20).mean()
    out["kc_width20_10"] = 4 * atr10 / ema20.abs().replace(0, np.nan)

    # Choppiness(14)
    trsum = tr.rolling(14, min_periods=14).sum()
    rng = out.high.rolling(14, min_periods=14).max() - out.low.rolling(14, min_periods=14).min()
    out["chop14"] = 100 * np.log10(trsum / rng.replace(0, np.nan)) / np.log10(14)

    return out


def add_participation_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["rvol20"] = out.tickvol / out.tickvol.rolling(20, min_periods=20).median().replace(0, np.nan)
    typ = (out.high + out.low + out.close) / 3
    rm = typ * out.tickvol
    td = typ.diff()
    pos = rm.where(td > 0, 0.0).rolling(14, min_periods=14).sum()
    neg = rm.where(td < 0, 0.0).rolling(14, min_periods=14).sum()
    mr = pos / neg.replace(0, np.nan)
    out["mfi14"] = 100 - 100 / (1 + mr)
    mfm = ((out.close - out.low) - (out.high - out.close)) / (out.high - out.low).replace(0, np.nan)
    out["cmf20"] = (mfm * out.tickvol).rolling(20, min_periods=20).sum() / out.tickvol.rolling(20, min_periods=20).sum().replace(0, np.nan)
    sign = np.sign(out.close.diff()).fillna(0)
    obv = (sign * out.tickvol).cumsum()
    out["obv20_norm"] = (obv - obv.shift(20)) / out.tickvol.rolling(20, min_periods=20).sum().replace(0, np.nan)
    return out


def attach_tf(events: pd.DataFrame, m1: pd.DataFrame, rule: str, minutes: int, include_participation: bool) -> pd.DataFrame:
    bars = m1.resample(rule, label="left", closed="left").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), tickvol=("tickvol", "sum")
    ).dropna()
    x = add_price_indicators(bars)
    if include_participation:
        x = add_participation_indicators(x)
    cols = [
        "rsi14", "plus_di14", "minus_di14", "adx14", "adx_d3",
        "aroon_up25", "aroon_down25", "bb_pctb20", "bb_width20", "bb_width_ratio5",
        "macd_hist", "macd_hist_d3", "stoch_k14", "willr14", "roc12", "donch_pos20",
        "kc_width20_10", "chop14",
    ]
    if include_participation:
        cols += ["rvol20", "mfi14", "cmf20", "obv20_norm"]
    f = x[cols].copy()
    f["available_at"] = f.index + pd.Timedelta(minutes=minutes)
    e = pd.merge_asof(events.sort_values("trigger_time"), f.reset_index(drop=True).sort_values("available_at"),
                      left_on="trigger_time", right_on="available_at", direction="backward", allow_exact_matches=True)
    e["year"] = e.trigger_time.dt.year
    e["ordinal"] = e.path.map(PATH_ORDINAL)
    e["dmi_align"] = e.dir * (e.plus_di14 - e.minus_di14)
    e["aroon_align"] = e.dir * (e.aroon_up25 - e.aroon_down25)
    e["rsi_align"] = e.dir * (e.rsi14 - 50)
    e["bb_location_align"] = e.dir * (e.bb_pctb20 - 0.5)
    e["macd_align"] = e.dir * e.macd_hist
    e["macd_slope_align"] = e.dir * e.macd_hist_d3
    e["stoch_align"] = e.dir * (e.stoch_k14 - 50)
    e["willr_align"] = e.dir * (e.willr14 + 50)
    e["roc_align"] = e.dir * e.roc12
    e["donch_align"] = e.dir * (e.donch_pos20 - 0.5)
    if include_participation:
        e["mfi_align"] = e.dir * (e.mfi14 - 50)
        e["cmf_align"] = e.dir * e.cmf20
        e["obv_align"] = e.dir * e.obv20_norm
    return e


def rank_corr(x: pd.Series, y: pd.Series) -> float:
    q = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(q) < 3:
        return float("nan")
    return float(q.x.rank(method="average").corr(q.y.rank(method="average")))


def superiority(a: pd.Series, b: pd.Series) -> float:
    av = a.dropna().to_numpy(float)
    bv = b.dropna().to_numpy(float)
    if len(av) == 0 or len(bv) == 0:
        return float("nan")
    gt = (av[:, None] > bv[None, :]).sum()
    eq = (av[:, None] == bv[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(av) * len(bv)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("gold", type=Path)
    ap.add_argument("ledger", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    m1 = load_gold(args.gold)
    ev = pd.read_csv(args.ledger, parse_dates=["trigger_time", "sweep_time"])
    required = {"event_id", "trigger_time", "dir", "path"}
    missing = required - set(ev.columns)
    if missing:
        raise RuntimeError(f"ledger missing columns: {sorted(missing)}")
    if set(ev.path.unique()) - set(PATH_ORDINAL):
        raise RuntimeError("unexpected path labels")

    expected = {2023: 84, 2024: 86, 2025: 67}
    observed = ev.groupby(ev.trigger_time.dt.year).size().to_dict()
    if observed != expected:
        raise RuntimeError(f"event parity fail: {observed} != {expected}")

    tf_frames = {
        "H1": attach_tf(ev, m1, "1h", 60, include_participation=True),
        "H4": attach_tf(ev, m1, "4h", 240, include_participation=False),
    }
    base_features = [
        "dmi_align", "adx14", "adx_d3", "aroon_align", "rsi_align",
        "bb_location_align", "bb_width20", "bb_width_ratio5",
        "macd_align", "macd_slope_align", "stoch_align", "willr_align", "roc_align", "donch_align",
        "kc_width20_10", "chop14",
    ]
    h1_extra = ["rvol20", "mfi_align", "cmf_align", "obv_align"]

    ordinal_rows = []
    stage_rows = []
    contrasts = {
        "ENTRY_SURVIVAL": (["W_CONTINUE", "W_GIVEBACK"], ["L_RECOVER", "L_CONTINUE"]),
        "WINNER_CONTINUATION": (["W_CONTINUE"], ["W_GIVEBACK"]),
        "LOSS_RECOVERY": (["L_RECOVER"], ["L_CONTINUE"]),
    }

    for tf, e in tf_frames.items():
        feats = base_features + (h1_extra if tf == "H1" else [])
        for f in feats:
            for y, g in e.groupby("year"):
                ordinal_rows.append({
                    "tf": tf,
                    "feature": f,
                    "year": int(y),
                    "n": int(g[f].notna().sum()),
                    "rho_ordinal": rank_corr(g[f], g.ordinal),
                    "median_L_CONTINUE": float(g.loc[g.path == "L_CONTINUE", f].median()),
                    "median_L_RECOVER": float(g.loc[g.path == "L_RECOVER", f].median()),
                    "median_W_GIVEBACK": float(g.loc[g.path == "W_GIVEBACK", f].median()),
                    "median_W_CONTINUE": float(g.loc[g.path == "W_CONTINUE", f].median()),
                })
            for cname, (hi_paths, lo_paths) in contrasts.items():
                for (y, d), g in e.groupby(["year", "dir"]):
                    hi = g.loc[g.path.isin(hi_paths), f]
                    lo = g.loc[g.path.isin(lo_paths), f]
                    stage_rows.append({
                        "tf": tf,
                        "feature": f,
                        "contrast": cname,
                        "year": int(y),
                        "dir": int(d),
                        "n_hi": int(hi.notna().sum()),
                        "n_lo": int(lo.notna().sum()),
                        "median_hi": float(hi.median()),
                        "median_lo": float(lo.median()),
                        "p_hi_gt_lo": superiority(hi, lo),
                    })

    ordinal = pd.DataFrame(ordinal_rows)
    stage = pd.DataFrame(stage_rows)
    ordinal.to_csv(args.out / "indicator_ordinal_by_year.csv", index=False)
    stage.to_csv(args.out / "indicator_stage_by_year_direction.csv", index=False)

    # Strict descriptive stability: all six year x direction cells on same side of 0.5.
    stable = []
    for (tf, f, c), g in stage.groupby(["tf", "feature", "contrast"]):
        q = g.dropna(subset=["p_hi_gt_lo"])
        if len(q) != 6:
            continue
        vals = q.p_hi_gt_lo.to_numpy(float)
        if np.all(vals > 0.5) or np.all(vals < 0.5):
            stable.append({
                "tf": tf,
                "feature": f,
                "contrast": c,
                "sign": "HIGHER" if np.all(vals > 0.5) else "LOWER",
                "min_probability": float(vals.min()),
                "max_probability": float(vals.max()),
                "mean_abs_deviation_from_half": float(np.mean(np.abs(vals - 0.5))),
            })
    summary = {
        "status": "EXPLORATORY_ONLY_NO_TRADING_AUTHORITY",
        "event_counts": expected,
        "stable_six_cell_relations": stable,
        "note": "Do not select thresholds or promote filters from this atlas. Any follow-up requires a separate frozen child contract.",
    }
    (args.out / "indicator_atlas_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
