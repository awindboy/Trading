#!/usr/bin/env python3
"""
V8 N2 normalized-N1 deterministic raw-tick voter probe.

No model fitting. No threshold search. No 2021 access.
Population must match exact resolved N1 ledger:
2024=797, 2025=814, 2026=538.

The probe fetches only PRE-decision MT5 ticks and creates five deterministic
direction voters from raw bid/ask-derived midquote paths. It also computes
the same voters on a fixed -10 minute shifted placebo endpoint.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import timezone, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

EXPECTED = {2024:797, 2025:814, 2026:538}
WINDOWS = [5,15,30,60,180,300]
EPS = 1e-12
PLACEBO_SHIFT_SEC = 600
PROBE_VERSION = "2026-09-01-v3-sparse-tick-aware"

def parse_args():
    ap=argparse.ArgumentParser()
    ap.add_argument("--resolved-ledger", required=True)
    ap.add_argument("--symbol", default="GOLD#")
    ap.add_argument("--server-tz", required=True,
                    help="IANA timezone used by ledger/MT5 server timestamps, e.g. Europe/Helsinki")
    ap.add_argument("--out", default="V8_N2_NORMALIZED_TICK_VOTER_RESULTS")
    ap.add_argument("--terminal-path", default=None)
    return ap.parse_args()

def server_to_utc(ts: pd.Timestamp, tz_name: str):
    if ts.tzinfo is not None:
        return ts.tz_convert("UTC").to_pydatetime()
    local=ts.to_pydatetime().replace(tzinfo=ZoneInfo(tz_name))
    return local.astimezone(timezone.utc)

def safe_div(a,b):
    return float(a/b) if np.isfinite(a) and np.isfinite(b) and abs(b)>EPS else 0.0

def last_run_score(signs):
    if len(signs)==0: return 0.0
    s=signs[-1]
    run=1
    for q in signs[-2::-1]:
        if q==s: run+=1
        else: break
    return float(s*run/len(signs))

def extract_window(ticks: pd.DataFrame, end_ms: int, sec: int, prefix: str):
    start_ms=end_ms-sec*1000
    z=ticks[(ticks.time_msc>=start_ms)&(ticks.time_msc<end_ms)]
    p=f"{prefix}{sec}_"
    keys=["n","net","moveimb","magimb","clv","eff","lastrun",
          "tickrate","spreadmean","spreaddelta"]
    if len(z)<2:
        return {p+k:np.nan for k in keys}
    bid=z.bid.to_numpy(float); ask=z.ask.to_numpy(float)
    mid=(bid+ask)*0.5
    spread=ask-bid
    dm=np.diff(mid)
    nz=dm[np.abs(dm)>EPS]
    signs=np.sign(nz)
    up=float(np.sum(nz>EPS)); dn=float(np.sum(nz<-EPS))
    pm=float(np.sum(nz[nz>EPS])); nm=float(np.sum(-nz[nz<-EPS]))
    path=float(np.sum(np.abs(dm)))
    hi=float(np.max(mid)); lo=float(np.min(mid))
    return {
        p+"n":float(len(z)),
        p+"net":float(mid[-1]-mid[0]),
        p+"moveimb":safe_div(up-dn,up+dn),
        p+"magimb":safe_div(pm-nm,pm+nm),
        p+"clv":safe_div((mid[-1]-lo)-(hi-mid[-1]),hi-lo),
        p+"eff":safe_div(float(mid[-1]-mid[0]),path),
        p+"lastrun":last_run_score(signs),
        p+"tickrate":float(len(z)/sec),
        p+"spreadmean":float(np.mean(spread)),
        p+"spreaddelta":float(spread[-1]-spread[0]),
    }

def extract_all(ticks,end_ms,prefix):
    out={}
    for w in WINDOWS:
        out.update(extract_window(ticks,end_ms,w,prefix))
    return out

def vote_available(*xs, min_active=2):
    """Directional majority over available windows.
    - A window is unavailable only when it has <2 valid ticks.
    - Require at least two available windows.
    - A 1:1 tie with exactly two windows => abstain (NaN).
    - Zero-valued directional metric counts SHORT, consistently with v2.
    """
    vals=np.array(xs,dtype=float)
    vals=vals[np.isfinite(vals)]
    if len(vals)<min_active:
        return np.nan
    longs=int(np.sum(vals>0))
    shorts=int(len(vals)-longs)
    if longs==shorts:
        return np.nan
    return int(longs>shorts)

def make_votes(row,prefix):
    return {
        prefix+"vote_NET": vote_available(row[prefix+"15_net"],row[prefix+"60_net"],row[prefix+"300_net"]),
        prefix+"vote_MOVE": vote_available(row[prefix+"5_moveimb"],row[prefix+"15_moveimb"],row[prefix+"60_moveimb"]),
        prefix+"vote_MAG": vote_available(row[prefix+"15_magimb"],row[prefix+"60_magimb"],row[prefix+"300_magimb"]),
        prefix+"vote_CLV": vote_available(row[prefix+"15_clv"],row[prefix+"60_clv"],row[prefix+"300_clv"]),
        prefix+"vote_RUN": vote_available(row[prefix+"5_lastrun"],row[prefix+"15_lastrun"],row[prefix+"60_lastrun"]),
    }

def panel_vote(row, vote_cols, min_active=3):
    vals=pd.to_numeric(row[vote_cols],errors="coerce").to_numpy(float)
    vals=vals[np.isfinite(vals)]
    if len(vals)<min_active:
        return np.nan
    longs=int(np.sum(vals>0.5))
    shorts=int(len(vals)-longs)
    if longs==shorts:
        return np.nan
    return int(longs>shorts)

def n2r1_control(df):
    votes=(
        (df.H4_signedvol3>=0.119909).astype(int)+
        (df.H4_roc1>=-0.075533).astype(int)+
        (df.M1_240_moveimb<=0.042017).astype(int)+
        (df.M1_5_range_atr>=2.661190).astype(int)+
        (df.p60>=0.987684).astype(int)+
        (df.H4_bb_width_atr<=3.514138).astype(int)+
        (df.M15_body_atr<=0.272129).astype(int)
    )
    return (votes>=5).astype(int)

def main():
    args=parse_args()
    print(f"PROBE_VERSION={PROBE_VERSION}")
    out=Path(args.out).resolve()
    out.mkdir(parents=True,exist_ok=True)

    led=pd.read_csv(args.resolved_ledger)
    req=["decision","year","label_up","H4_signedvol3","H4_roc1","M1_240_moveimb",
         "M1_5_range_atr","p60","H4_bb_width_atr","M15_body_atr"]
    missing=[c for c in req if c not in led.columns]
    if missing: raise SystemExit(f"Missing ledger columns: {missing}")
    led["decision"]=pd.to_datetime(led["decision"])
    counts=led.groupby("year").size().to_dict()
    if counts!=EXPECTED:
        raise SystemExit(f"FAIL-CLOSED population mismatch: got {counts}, expected {EXPECTED}")
    led=led.sort_values("decision").reset_index(drop=True)
    led["n2r1_pred_up"]=n2r1_control(led)

    try:
        import MetaTrader5 as mt5
    except ImportError:
        raise SystemExit("Install MetaTrader5: python -m pip install MetaTrader5 pandas numpy")

    ok=mt5.initialize(args.terminal_path) if args.terminal_path else mt5.initialize()
    if not ok:
        raise SystemExit(f"MetaTrader5.initialize failed: {mt5.last_error()}")
    if not mt5.symbol_select(args.symbol,True):
        raise SystemExit(f"Could not select symbol {args.symbol!r}: {mt5.last_error()}")

    rows=[]; quality=[]
    fetch_back=PLACEBO_SHIFT_SEC+max(WINDOWS)+5
    try:
        for i,r in enumerate(led.itertuples(index=False),1):
            dec_utc=server_to_utc(pd.Timestamp(r.decision),args.server_tz)
            start=dec_utc-timedelta(seconds=fetch_back)
            end=dec_utc
            arr=mt5.copy_ticks_range(args.symbol,start,end,mt5.COPY_TICKS_ALL)
            if arr is None:
                arr=[]
            z=pd.DataFrame(arr)
            q={"decision":r.decision,"year":int(r.year),"ticks":len(z),
               "bad_bid":0,"bad_ask":0,"crossed":0,
               "at_decision":0,"after_decision":0,"timestamp_decrease":0}
            if len(z):
                needed=["time_msc","bid","ask"]
                miss=[c for c in needed if c not in z.columns]
                if miss: raise RuntimeError(f"MT5 ticks missing {miss}")
                z=z[needed].copy()
                q["bad_bid"]=int((~np.isfinite(z.bid)|(z.bid<=0)).sum())
                q["bad_ask"]=int((~np.isfinite(z.ask)|(z.ask<=0)).sum())
                q["crossed"]=int((z.ask<z.bid).sum())
                q["timestamp_decrease"]=int((np.diff(z.time_msc.to_numpy(np.int64))<0).sum())
                dec_ms=int(round(dec_utc.timestamp()*1000))
                q["at_decision"]=int((z.time_msc==dec_ms).sum())
                q["after_decision"]=int((z.time_msc>dec_ms).sum())
                z=z[(z.bid>0)&(z.ask>0)&(z.ask>=z.bid)&(z.time_msc<dec_ms)]
                z=z.sort_values("time_msc",kind="mergesort").reset_index(drop=True)
            quality.append(q)

            base={"decision":r.decision,"year":int(r.year),"label_up":int(r.label_up),
                  "n2r1_pred_up":int(r.n2r1_pred_up)}
            if len(z)>=2:
                dec_ms=int(round(dec_utc.timestamp()*1000))
                base.update(extract_all(z,dec_ms,"a"))
                base.update(extract_all(z,dec_ms-PLACEBO_SHIFT_SEC*1000,"p"))
                base.update(make_votes(base,"a"))
                base.update(make_votes(base,"p"))
            rows.append(base)
            if i%100==0 or i==len(led):
                print(f"{i}/{len(led)}")
    finally:
        mt5.shutdown()

    qdf=pd.DataFrame(quality)
    qdf.to_csv(out/"tick_quality.csv",index=False)
    # MT5 copy_ticks_range is endpoint-inclusive. Ticks exactly at the
    # decision millisecond are recorded as at_decision, excluded from
    # all features by time_msc < dec_ms, and are NOT a quality failure.
    # Any tick strictly after the decision remains fail-closed.
    critical=(qdf[["bad_bid","bad_ask","crossed","after_decision","timestamp_decrease"]].sum().sum()>0)
    if critical:
        (out/"STATUS.txt").write_text("FAIL_CLOSED_DATA_QUALITY\n",encoding="utf-8")
        raise SystemExit("FAIL-CLOSED tick quality issue. See tick_quality.csv")

    df=pd.DataFrame(rows)
    voteA=["avote_NET","avote_MOVE","avote_MAG","avote_CLV","avote_RUN"]
    voteP=["pvote_NET","pvote_MOVE","pvote_MAG","pvote_CLV","pvote_RUN"]

    # Persist raw extraction BEFORE any coverage gate so a failed run is diagnosable.
    df.to_csv(out/"raw_tick_features.csv",index=False)

    # Sparse-aware panel: individual voters may abstain when their required
    # windows do not contain enough quote changes. The panel needs >=3 active
    # voters and a strict majority.
    df["aligned_active_voters"]=df[voteA].notna().sum(axis=1)
    df["placebo_active_voters"]=df[voteP].notna().sum(axis=1)
    df["tick_pred_up"]=df.apply(lambda r: panel_vote(r,voteA,min_active=3),axis=1)
    df["placebo_pred_up"]=df.apply(lambda r: panel_vote(r,voteP,min_active=3),axis=1)

    aligned_ok=df["tick_pred_up"].notna()
    placebo_ok=df["placebo_pred_up"].notna()
    joint_ok=aligned_ok & placebo_ok

    # Detailed outcome-blind coverage diagnostics.
    cov_rows=[]
    for year in ["ALL",2024,2025,2026]:
        g=df if year=="ALL" else df[df.year==year]
        a=g["tick_pred_up"].notna()
        p=g["placebo_pred_up"].notna()
        j=a&p
        cov_rows.append({
            "year":year,"N":len(g),
            "aligned_panel_coverage":float(a.mean()),
            "placebo_panel_coverage":float(p.mean()),
            "joint_panel_coverage":float(j.mean()),
            "aligned_mean_active_voters":float(g.aligned_active_voters.mean()),
            "placebo_mean_active_voters":float(g.placebo_active_voters.mean()),
        })
    coverage_df=pd.DataFrame(cov_rows)
    for c in voteA+voteP:
        coverage_df[c+"_availability"]=[
            float(df[c].notna().mean()),
            float(df.loc[df.year==2024,c].notna().mean()),
            float(df.loc[df.year==2025,c].notna().mean()),
            float(df.loc[df.year==2026,c].notna().mean()),
        ]
    coverage_df.to_csv(out/"coverage_summary.csv",index=False)

    # Primary aligned analysis uses every event with a valid aligned panel.
    # Placebo comparison uses the fair joint-covered intersection only.
    primary=df[aligned_ok].copy()
    primary["tick_pred_up"]=primary["tick_pred_up"].astype(int)
    primary["tick_correct"]=(primary.tick_pred_up==primary.label_up).astype(int)
    primary["n2r1_correct"]=(primary.n2r1_pred_up==primary.label_up).astype(int)
    primary["tick_n2_agree"]=(primary.tick_pred_up==primary.n2r1_pred_up).astype(int)
    primary.to_csv(out/"tick_voter_ledger.csv",index=False)

    joint=df[joint_ok].copy()
    joint["tick_pred_up"]=joint["tick_pred_up"].astype(int)
    joint["placebo_pred_up"]=joint["placebo_pred_up"].astype(int)
    joint["aligned_correct"]=(joint.tick_pred_up==joint.label_up).astype(int)
    joint["placebo_correct"]=(joint.placebo_pred_up==joint.label_up).astype(int)
    joint.to_csv(out/"aligned_placebo_joint_ledger.csv",index=False)

    aligned_cov=float(aligned_ok.mean())
    joint_cov=float(joint_ok.mean())

    # Predeclared quality gate: aligned evidence must cover >=90% of N1;
    # placebo comparison must jointly cover >=80%. Unlike v2, sparse 5-second
    # windows may abstain instead of deleting the whole event.
    if aligned_cov < 0.90 or joint_cov < 0.80:
        (out/"STATUS.txt").write_text(
            f"FAIL_CLOSED_TICK_COVERAGE\naligned={aligned_cov:.6f}\njoint_placebo={joint_cov:.6f}\n",
            encoding="utf-8")
        print(coverage_df.to_string(index=False))
        raise SystemExit(
            f"FAIL-CLOSED sparse-aware coverage: aligned={aligned_cov:.2%}, "
            f"joint placebo={joint_cov:.2%}. See coverage_summary.csv and raw_tick_features.csv")

    yr=[]
    for year,g in primary.groupby("year"):
        j=joint[joint.year==year]
        row={"year":int(year),"N_aligned":len(g),"N_joint_placebo":len(j),
             "aligned_coverage":len(g)/len(df[df.year==year]),
             "joint_placebo_coverage":len(j)/len(df[df.year==year]),
             "tick_accuracy":g.tick_correct.mean(),
             "shifted_placebo_accuracy":j.placebo_correct.mean() if len(j) else np.nan,
             "aligned_accuracy_on_joint":j.aligned_correct.mean() if len(j) else np.nan,
             "n2r1_accuracy":g.n2r1_correct.mean(),
             "tick_long_rate":g.tick_pred_up.mean(),
             "placebo_long_rate":j.placebo_pred_up.mean() if len(j) else np.nan,
             "tick_n2_agree_rate":g.tick_n2_agree.mean()}
        for c in voteA:
            ok=g[c].notna()
            row[c+"_N"]=int(ok.sum())
            row[c+"_accuracy"]=(
                (g.loc[ok,c].astype(int)==g.loc[ok,"label_up"].astype(int)).mean()
                if ok.sum() else np.nan)
        yr.append(row)
    ydf=pd.DataFrame(yr)
    ydf.to_csv(out/"year_summary.csv",index=False)

    inter=[]
    for year,g in primary.groupby("year"):
        for agree in [0,1]:
            gg=g[g.tick_n2_agree==agree]
            if len(gg):
                inter.append({"year":int(year),"relation":"AGREE" if agree else "DISAGREE",
                              "N":len(gg),"n2r1_accuracy":gg.n2r1_correct.mean(),
                              "tick_accuracy":gg.tick_correct.mean()})
    pd.DataFrame(inter).to_csv(out/"n2r1_tick_interaction.csv",index=False)

    primary[voteA].corr().to_csv(out/"aligned_vote_correlation.csv")

    summary={"population_counts":counts,
             "aligned_coverage_N":int(aligned_ok.sum()),
             "aligned_coverage":float(aligned_ok.mean()),
             "joint_placebo_coverage_N":int(joint_ok.sum()),
             "joint_placebo_coverage":float(joint_ok.mean()),
             "placebo_shift_sec":PLACEBO_SHIFT_SEC,
             "year_summary":ydf.to_dict(orient="records")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    (out/"PROBE_VERSION.txt").write_text(PROBE_VERSION+"\n",encoding="utf-8")
    (out/"STATUS.txt").write_text("COMPLETE_DEVELOPMENT_EVIDENCE_ONLY\n",encoding="utf-8")
    print(ydf.to_string(index=False))
    print(f"Results: {out}")

if __name__=="__main__":
    main()
