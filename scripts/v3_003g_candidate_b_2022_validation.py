#!/usr/bin/env python3
"""V3-003G one-time GOLD# 2022 validation replay for frozen Candidate B.

This script is a reproducibility companion to:
    docs/ea/v3/V3_003G_CANDIDATE_B_2022_VALIDATION_RESULTS.md

It imports the already-committed V3-003E replay engine so Candidate-A/H/L
semantics are not re-invented. The only intentional difference from V3-003E
base_env is dataset governance: this script accepts exactly year 2022.

Frozen Candidate B:
- Candidate-A M15 adaptive DC k=2
- H2 direct-transfer, 50% pullback
- H +3R 25% harvest / residual BE / +5R
- primary L protected-runner
- same-direction coexistence allowed
- opposite-direction coexistence blocked

No 2022 result is allowed to change these rules.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent


def _load_local(name: str, filename: str):
    p = HERE / filename
    if not p.exists():
        raise SystemExit(f"FAIL-CLOSED missing committed helper: {p}")
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


e = _load_local("v3e", "v3_003e_dual_module_repro.py")
c = e.c
d = e.d


def base_env_2022(data_path: Path):
    m1 = c.load_gold(data_path)
    years = set(m1.index.year.unique())
    if years != {2022}:
        raise SystemExit(f"FAIL-CLOSED validation requires exactly 2022, got {sorted(years)}")

    bars = {r: c.resample_ohlc(m1, r) for r in ["5min", "15min", "30min", "60min"]}
    for b in bars.values():
        b["atr14"] = c.atr_series(b)

    piv = {
        r: c.pivot_events(bars[r], 2, {"5min": 5, "15min": 15, "30min": 30, "60min": 60}[r])
        for r in bars
    }

    ends5, own5, chg5, hlev5, llev5 = c.bos_owner_with_break(bars["5min"], piv["5min"], 5)
    ends30, own30, _, _, _ = c.bos_owner_with_break(bars["30min"], piv["30min"], 30)
    ends60, own60, _, _, _ = c.bos_owner_with_break(bars["60min"], piv["60min"], 60)
    mw30 = c.mentor_waves(bars["30min"], 30)
    ends1, own1, chg1 = d.build_m1_owner(m1)

    t30 = ends30
    exp_grid = c.wave_expansion_at(pd.to_datetime(t30), mw30)
    h1_on30 = c.state_at(pd.to_datetime(t30), ends60, own60)
    up = (exp_grid > 1.0) | ((own30 == 1) & (h1_on30 == 1))
    dn = (exp_grid > 1.0) | ((own30 == -1) & (h1_on30 == -1))

    d1 = c.resample_ohlc(m1, "1D")
    d1["atr14"] = c.atr_series(d1)
    d1_av = (d1.index + pd.Timedelta(days=1)).to_numpy(dtype="datetime64[ns]")
    d1v = d1.atr14.to_numpy(float)

    return locals()


def build_for_k_2022(E, k: float):
    m1 = E["m1"]
    bars = E["bars"]
    src = c.dc_swing_events(bars["15min"], k, 15)
    rr = c.dedupe_enriched(c.persistent_reactions(m1, src), src)
    tr = c.build_triggers(rr, m1, bars["5min"], E["ends5"], E["own5"], E["chg5"])
    ev = c.evaluate(tr, m1)
    ev["year"] = ev.trigger_time.dt.year
    ev["source_k"] = k
    ev["m30_exp"] = c.wave_expansion_at(ev.sweep_time, E["mw30"])
    ev["m30_owner"] = c.state_at(ev.sweep_time, E["ends30"], E["own30"])
    ev["h1_owner"] = c.state_at(ev.sweep_time, E["ends60"], E["own60"])
    ev["owner_agree"] = (ev.m30_owner == ev.dir) & (ev.h1_owner == ev.dir)
    ev["delivery_state"] = (ev.m30_exp > 1.0) | ev.owner_agree
    ev["broken_m5_level"] = np.where(
        ev.dir.to_numpy() == 1,
        E["hlev5"][ev.trigger_m5_index.to_numpy(int)],
        E["llev5"][ev.trigger_m5_index.to_numpy(int)],
    )
    ev["penetration"] = (ev.liq_price - ev.sweep_extreme) * ev.dir
    ev["acceptance_margin"] = (ev.trigger_close - ev.broken_m5_level) * ev.dir
    ev["strong_acceptance"] = ev.acceptance_margin > ev.penetration
    ev = d.add_micro_path(ev, E["ends1"], E["own1"], E["chg1"])
    ev["d1_atr"] = e.atr_at(ev.trigger_time, E["d1_av"], E["d1v"])
    cand = ev[ev.delivery_state & ev.strong_acceptance].copy().reset_index(drop=True)
    return src, ev, cand


def state_segment_2022(t, direction, E):
    arr = E["up"] if direction == 1 else E["dn"]
    t30 = E["t30"]
    pos = np.searchsorted(t30, np.datetime64(t), side="right") - 1
    if pos < 0 or not arr[pos]:
        return None
    s = pos
    while s > 0 and arr[s - 1]:
        s -= 1
    ee = pos + 1
    while ee < len(arr) and arr[ee]:
        ee += 1
    st = pd.Timestamp(t30[s])
    en = pd.Timestamp(t30[ee]) if ee < len(arr) else pd.NaT
    return st, en


def add_episode_2022(cand, E):
    q = cand.copy()
    starts, ends, ids, active = [], [], [], []
    for r in q.itertuples(index=False):
        seg = state_segment_2022(r.trigger_time, r.dir, E)
        if seg is None:
            starts.append(pd.NaT)
            ends.append(pd.NaT)
            ids.append(None)
            active.append(False)
        else:
            st, en = seg
            starts.append(st)
            ends.append(en)
            ids.append(f"{r.dir}:{st.isoformat()}")
            active.append(True)
    q["episode_start"] = starts
    q["episode_end"] = ends
    q["episode_id"] = ids
    q["state_active_trigger"] = active
    return q


def module_l_candidates_2022(E, byk):
    rows = []
    for k, (_, ev, cand) in byk.items():
        ce = add_episode_2022(cand, E)
        losers = ce[(ce.win1 == 0) & ce.state_active_trigger].copy()
        for r in losers.itertuples(index=False):
            end = r.episode_end if pd.notna(r.episode_end) else pd.Timestamp.max
            if pd.notna(r.episode_end) and r.resolved_at >= end:
                continue
            g = ev[
                (ev.dir == r.dir)
                & (ev.trigger_time > r.resolved_at)
                & (ev.trigger_time < end)
            ].copy()
            g = g[g.liq_price < r.liq_price] if r.dir == 1 else g[g.liq_price > r.liq_price]
            if not len(g):
                continue
            x = g.sort_values("trigger_time").iloc[0]
            z = x.to_dict()
            z.update(
                {
                    "prior_k": k,
                    "prior_trigger_time": r.trigger_time,
                    "prior_resolved_at": r.resolved_at,
                    "prior_liq_price": r.liq_price,
                    "prior_sl": r.sl_exec,
                    "episode_id": r.episode_id,
                }
            )
            rows.append(z)

    raw = pd.DataFrame(rows)
    if not len(raw):
        return raw, raw

    raw = raw.sort_values(["trigger_time", "dir", "prior_resolved_at", "source_k"])
    out = []
    for (_, _), g in raw.groupby(["trigger_time", "dir"], sort=True):
        support = sorted(set(g.source_k.astype(float)))
        mx = g.prior_resolved_at.max()
        gg = g[g.prior_resolved_at == mx].copy()
        gg["kdist"] = (gg.source_k - 2.0).abs()
        rep = gg.sort_values(["kdist", "source_k"]).iloc[0].to_dict()
        rep["support_k"] = "|".join(f"{x:g}" for x in support)
        rep["support_n"] = len(support)
        out.append(rep)
    phys = pd.DataFrame(out).sort_values("trigger_time").reset_index(drop=True)
    return raw, phys


def l_trade_end(L: pd.DataFrame) -> pd.Series:
    end = pd.to_datetime(L.res2_at)
    return end.where(L.checkpoint_hit.astype(bool), pd.to_datetime(L.checkpoint_at))


def build_candidate_b_trades(H2: pd.DataFrame, L: pd.DataFrame):
    h = pd.DataFrame(
        {
            "start": pd.to_datetime(H2.fill_time),
            "end": pd.to_datetime(H2.resolved_at_h),
            "year": H2.year.astype(int),
            "module": "H",
            "dir": H2.dir.astype(int),
            "R": H2.H_harvest_R.astype(float),
            "source_id": "H:" + H2.trigger_time.astype(str),
            "outcome": H2.outcome.astype(str),
            "trigger_time": pd.to_datetime(H2.trigger_time),
        }
    )

    if len(L):
        l = pd.DataFrame(
            {
                "start": pd.to_datetime(L.trigger_time),
                "end": l_trade_end(L),
                "year": L.year.astype(int),
                "module": "L",
                "dir": L.dir.astype(int),
                "R": L.L50_R.astype(float),
                "source_id": "L:" + L.trigger_time.astype(str),
                "outcome": np.where(L.checkpoint_hit.astype(bool), L.res2_term.astype(str), "SL"),
                "trigger_time": pd.to_datetime(L.trigger_time),
            }
        )
    else:
        l = pd.DataFrame(columns=h.columns)

    return (
        pd.concat([h, l], ignore_index=True)
        .sort_values(["start", "module", "source_id"])
        .reset_index(drop=True)
    )


def apply_opposite_block(df: pd.DataFrame):
    accepted, blocked = [], []
    for _, tr in df.iterrows():
        active = [a for a in accepted if pd.Timestamp(a["end"]) > pd.Timestamp(tr.start)]
        ok = not any(int(a["dir"]) == -int(tr.dir) for a in active)
        (accepted if ok else blocked).append(tr.to_dict())
    return pd.DataFrame(accepted), pd.DataFrame(blocked)


def metrics(df: pd.DataFrame):
    a = pd.to_numeric(df.R).to_numpy(float)
    pos = a > 1e-12
    eq = peak = dd = 0.0
    streak = mx = 0
    for x in a:
        if x < -1e-12:
            streak += 1
            mx = max(mx, streak)
        else:
            streak = 0
        eq += x
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    return {
        "n": int(len(a)),
        "positive_n": int(pos.sum()),
        "positive_rate": float(pos.mean()) if len(a) else math.nan,
        "avg_positive_R": float(a[pos].mean()) if pos.any() else math.nan,
        "expectancy_R": float(a.mean()) if len(a) else math.nan,
        "total_R": float(a.sum()),
        "max_negative_streak": int(mx),
        "max_sequence_drawdown_R": float(dd),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", type=Path, help="GOLD# 2022 M1 CSV or ZIP")
    ap.add_argument("--out", type=Path, default=Path("v3_003g_2022_validation_out"))
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    E = base_env_2022(args.data)
    byk = {k: build_for_k_2022(E, k) for k in [1.5, 2.0, 2.5]}
    cand = byk[2.0][2]

    H_all = e.fill_pullback(E, cand, 0.5)
    meta = cand[
        ["sweep_time", "trigger_time", "dir", "m30_exp", "m30_owner", "h1_owner", "m1_direct_transfer"]
    ].copy()
    H = H_all.merge(meta, on=["sweep_time", "trigger_time", "dir"], how="left")
    H["direct_transfer"] = H.m1_direct_transfer.astype(bool)
    H["owner_agree"] = (H.m30_owner == H.dir) & (H.h1_owner == H.dir)
    H["both_branch"] = (H.m30_exp > 1.0) & H.owner_agree
    H["H_primary_R"] = H.outcome.map({"TP5": 5.0, "BE": 0.0, "SL": -1.0})
    H["H_harvest_R"] = H.outcome.map({"TP5": 4.5, "BE": 0.75, "SL": -1.0})
    H2 = H[H.direct_transfer].copy().reset_index(drop=True)
    H2["mirror5"] = e.mirror_h(E, H2)

    lraw, lphys = module_l_candidates_2022(E, byk)
    if len(lphys):
        L = e.eval_l(E, lphys)
        L = e.add_l_protected_runner(E, L, partial=0.5)
    else:
        L = lphys.copy()

    trades = build_candidate_b_trades(H2, L)
    accepted, blocked = apply_opposite_block(trades)

    # Link L back to actual H2 parent triggers.
    h_triggers = set(pd.to_datetime(H2.trigger_time))
    if len(L):
        L["linked_to_actual_H2"] = pd.to_datetime(L.prior_trigger_time).isin(h_triggers)

    cand.to_csv(out / "candidate_a.csv", index=False)
    H2.to_csv(out / "h2.csv", index=False)
    L.to_csv(out / "module_l.csv", index=False)
    accepted.to_csv(out / "candidate_b_accepted.csv", index=False)
    blocked.to_csv(out / "candidate_b_blocked.csv", index=False)

    result = metrics(accepted)
    result["candidate_A_n"] = int(len(cand))
    result["candidate_A_win1"] = int((cand.win1 == 1).sum())
    result["candidate_A_wr1"] = float((cand.win1 == 1).mean())
    result["H2_n"] = int(len(H2))
    result["H2_tp5"] = int((H2.outcome == "TP5").sum())
    result["H2_sl"] = int((H2.outcome == "SL").sum())
    result["H2_be"] = int((H2.outcome == "BE").sum())
    result["H2_primary_ev_R"] = float(H2.H_primary_R.mean()) if len(H2) else math.nan
    result["H2_harvest_ev_R"] = float(H2.H_harvest_R.mean()) if len(H2) else math.nan
    result["H2_mirror_tp5"] = int(H2.mirror5.sum()) if len(H2) else 0
    result["H3_shadow_both_n"] = int(H2.both_branch.sum()) if len(H2) else 0
    result["H3_shadow_both_tp5"] = int((H2.both_branch & H2.outcome.eq("TP5")).sum()) if len(H2) else 0
    result["L_n"] = int(len(L))
    result["L_checkpoint_hits"] = int(L.checkpoint_hit.sum()) if len(L) else 0
    result["L_full1_hits"] = int(L.full1_hit.sum()) if len(L) else 0
    result["L_res2_hits"] = int(L.res2_hit.sum()) if len(L) else 0
    result["L_mirror_checkpoint_hits"] = int(L.mirror_checkpoint_hit.sum()) if len(L) else 0
    result["L_mean_R"] = float(L.L50_R.mean()) if len(L) else math.nan
    result["blocked_n"] = int(len(blocked))
    result["classification"] = (
        "PASS"
        if result["positive_rate"] >= 0.50
        and result["avg_positive_R"] > 1.0
        and result["expectancy_R"] > 0
        else "FAIL"
    )

    (out / "manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
