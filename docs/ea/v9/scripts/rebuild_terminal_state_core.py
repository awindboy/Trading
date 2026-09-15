#!/usr/bin/env python3
"""
Rebuild the 2026-09-16 V9 terminal-state core research from raw tester/price CSVs.

Research-only. Does not change V9 strategy authority.

Required files in --data-dir:
  V9_R0_events(1).csv
  V9_R0_trades(1).csv
  GOLD#_H4_202201030000_202608282000.csv
  GOLD#_H1_202201030100_202608282300.csv
  GOLD#_M30_202201030100_202608282330.csv
  GOLD#_M15_202201030100_202608282345.csv
  GOLD#_M5_202201030100_202608282355.csv

The script reproduces the literal-oracle correction and the main repeat-state
combination screen. It intentionally does not promote any threshold or strategy rule.
"""
from __future__ import annotations

import argparse
import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

EXPECTED = {
    "events": "V9_R0_events(1).csv",
    "trades": "V9_R0_trades(1).csv",
    "h4": "GOLD#_H4_202201030000_202608282000.csv",
    "h1": "GOLD#_H1_202201030100_202608282300.csv",
    "m30": "GOLD#_M30_202201030100_202608282330.csv",
    "m15": "GOLD#_M15_202201030100_202608282345.csv",
    "m5": "GOLD#_M5_202201030100_202608282355.csv",
}

def load_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t")

def prepare_tester(data_dir: Path):
    ev = pd.read_csv(data_dir / EXPECTED["events"])
    tr = pd.read_csv(data_dir / EXPECTED["trades"])

    ev["tick_time"] = pd.to_datetime(ev["tick_time"])
    for c in ["bid","ask","semantic_ref","atr180"]:
        if c in ev:
            ev[c] = pd.to_numeric(ev[c], errors="coerce")

    tr["entry_time"] = pd.to_datetime(tr["entry_time"])
    tr["exit_time"] = pd.to_datetime(tr["exit_time"])
    for c in ["semantic_entry","actual_entry","actual_exit","atr180","calc_profit"]:
        tr[c] = pd.to_numeric(tr[c], errors="coerce")
    return ev, tr

def prepare_h4(data_dir: Path, ev: pd.DataFrame) -> pd.DataFrame:
    h4 = load_tsv(data_dir / EXPECTED["h4"]).copy()
    h4["bar_start"] = pd.to_datetime(h4["<DATE>"]+" "+h4["<TIME>"], format="%Y.%m.%d %H:%M:%S")
    h4 = h4.rename(columns={"<OPEN>":"open","<HIGH>":"high","<LOW>":"low","<CLOSE>":"close"})
    for c in ["open","high","low","close"]:
        h4[c] = pd.to_numeric(h4[c], errors="coerce")
    h4 = h4.sort_values("bar_start").reset_index(drop=True)
    h4["nominal_end"] = h4.bar_start + pd.Timedelta(hours=4)

    fin = ev[ev.event.eq("H4_FINALIZED")][["tick_time","bid","ask"]].drop_duplicates("tick_time").sort_values("tick_time")
    m = pd.merge_asof(
        h4[["nominal_end"]].reset_index().sort_values("nominal_end"),
        fin.rename(columns={"tick_time":"known_at"}).sort_values("known_at"),
        left_on="nominal_end", right_on="known_at", direction="forward"
    ).sort_values("index")
    h4["known_at"] = m["known_at"].to_numpy()
    h4["known_bid"] = m["bid"].to_numpy()
    h4["known_ask"] = m["ask"].to_numpy()

    # Standard HA.
    h4["ha_close"] = (h4.open+h4.high+h4.low+h4.close)/4.0
    ho = np.empty(len(h4), dtype=float)
    ho[0] = (h4.loc[0,"open"]+h4.loc[0,"close"])/2.0
    hc = h4.ha_close.to_numpy(float)
    for i in range(1,len(h4)):
        ho[i] = (ho[i-1]+hc[i-1])/2.0
    h4["ha_open"] = ho
    h4["ha_side"] = np.where(h4.ha_close>h4.ha_open,"UP",np.where(h4.ha_close<h4.ha_open,"DOWN","FLAT"))
    h4["prev_ha_side"] = pd.Series(h4.ha_side).shift(1)
    h4["ha1_up_to_down"] = h4.ha_side.eq("DOWN") & h4.prev_ha_side.eq("UP")
    h4["ha1_down_to_up"] = h4.ha_side.eq("UP") & h4.prev_ha_side.eq("DOWN")
    h4["ha_high"] = np.maximum.reduce([h4.high.to_numpy(float), h4.ha_open.to_numpy(float), h4.ha_close.to_numpy(float)])
    h4["ha_low"] = np.minimum.reduce([h4.low.to_numpy(float), h4.ha_open.to_numpy(float), h4.ha_close.to_numpy(float)])

    # Wilder ATR180.
    pc = h4.close.shift(1)
    trng = pd.concat([
        h4.high-h4.low,
        (h4.high-pc).abs(),
        (h4.low-pc).abs()
    ], axis=1).max(axis=1)
    h4["atr180_calc"] = trng.ewm(alpha=1/180, adjust=False, min_periods=180).mean()

    # Reproducible transformed HA / Pressure coordinates used in the state screen.
    O=h4.open.to_numpy(float); H=h4.high.to_numpy(float); L=h4.low.to_numpy(float); C=h4.close.to_numpy(float)
    ATR=h4.atr180_calc.to_numpy(float)

    hc2=(O+H+L+4*C)/7.0
    ho2=np.empty(len(h4)); ho2[0]=(O[0]+C[0])/2
    for i in range(1,len(h4)):
        ho2[i]=0.5*ho2[i-1]+0.5*hc2[i-1]
    h4["closeha_body"]=(hc2-ho2)/ATR

    rng=np.maximum(H-L,1e-12)
    loc=(C-(H+L)/2)/(rng/2)
    size=rng/ATR
    pc2=loc*np.tanh(0.5*size)
    po=np.full(len(h4),np.nan)
    finite=np.flatnonzero(np.isfinite(pc2))
    if len(finite):
        j0=finite[0]; po[j0]=pc2[j0]
        for i in range(j0+1,len(h4)):
            if np.isfinite(pc2[i-1]) and np.isfinite(po[i-1]):
                po[i]=0.75*po[i-1]+0.25*pc2[i-1]
    pbody=pc2-po
    h4["pressure_flow2"]=pd.Series(pbody).rolling(2,min_periods=2).sum().to_numpy()

    # Donchian location.
    hi20=h4.high.rolling(20,min_periods=20).max()
    lo20=h4.low.rolling(20,min_periods=20).min()
    h4["donchian_pos20"]=(h4.close-lo20)/(hi20-lo20)
    return h4

def prepare_ltf(path: Path) -> pd.DataFrame:
    df=load_tsv(path).copy()
    df["ts"]=pd.to_datetime(df["<DATE>"]+" "+df["<TIME>"],format="%Y.%m.%d %H:%M:%S")
    df=df.rename(columns={"<OPEN>":"open","<HIGH>":"high","<LOW>":"low","<CLOSE>":"close"})
    for c in ["open","high","low","close"]:
        df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df.sort_values("ts").reset_index(drop=True)
    df["ha_close"]=(df.open+df.high+df.low+df.close)/4.0
    ho=np.empty(len(df));ho[0]=(df.loc[0,"open"]+df.loc[0,"close"])/2
    hc=df.ha_close.to_numpy(float)
    for i in range(1,len(df)):
        ho[i]=(ho[i-1]+hc[i-1])/2
    df["ha_open"]=ho
    df["ha_body"]=df.ha_close-df.ha_open
    return df

def metric(df: pd.DataFrame) -> dict:
    d=df.sort_values(["policy_exit_time","child_id"])
    x=d.policy_pnl.to_numpy(float)
    pos=x[x>0].sum(); neg=-x[x<0].sum()
    eq=np.cumsum(x); peak=np.maximum.accumulate(np.r_[0,eq])[:-1]
    dd=np.max(peak-eq) if len(eq) else 0
    return {
        "N":len(d),"PnL":float(x.sum()),"PF":float(pos/neg if neg>0 else np.inf),
        "WR":float((x>0).mean()),"DD":float(dd),
        "P90":float(np.quantile(x,0.90)),"P95":float(np.quantile(x,0.95)),"Max":float(x.max())
    }

def build_routes(ev: pd.DataFrame, tr: pd.DataFrame, h4: pd.DataFrame):
    ch = ev[(ev.event.eq("H4_LIQ_ARRIVAL")) & ev.resolution.eq("CHALLENGE_OPENS")]
    chmap=ch.groupby("route_id").tick_time.min()
    rows=[]
    for rid,g in tr.groupby("route_id"):
        if rid not in chmap.index: continue
        rows.append({
            "route_id":int(rid),"direction":g.direction.iloc[0],
            "first_entry":g.entry_time.min(),"last_entry":g.entry_time.max(),
            "challenge_ts":chmap.loc[rid]
        })
    routes=pd.DataFrame(rows)
    last_known=h4.known_at.dropna().max()
    routes=routes[routes.challenge_ts<=last_known].copy()
    return routes

def oracle_ledger(tr, routes, h4):
    answer=[]
    for r in routes.itertuples(index=False):
        opp="DOWN" if r.direction=="UP" else "UP"
        c=h4[h4.known_at.notna() & h4.ha_side.eq(opp) &
             (h4.known_at>r.last_entry) & (h4.known_at<r.challenge_ts)]
        if len(c):
            z=c.iloc[0]
            px=float(z.known_bid if r.direction=="UP" else z.known_ask)
            answer.append({
                "route_id":r.route_id,"oracle_ts":z.known_at,"oracle_ha_idx":int(z.name),
                "oracle_exec_ref":px,
                "oracle_is_transition_ha1":bool(
                    (r.direction=="UP" and z.ha1_up_to_down) or
                    (r.direction=="DOWN" and z.ha1_down_to_up))
            })
    ans=pd.DataFrame(answer)
    amap=ans.set_index("route_id").to_dict("index")
    led=tr[tr.route_id.isin(routes.route_id)].copy()
    out_t=[];out_px=[];out_p=[];chg=[]
    for x in led.itertuples(index=False):
        a=amap.get(x.route_id)
        use=a is not None and x.entry_time<a["oracle_ts"]<x.exit_time
        if use:
            px=a["oracle_exec_ref"]
            pnl=(px-x.actual_entry) if x.direction=="UP" else (x.actual_entry-px)
            out_t.append(a["oracle_ts"]);out_px.append(px);out_p.append(pnl);chg.append(True)
        else:
            out_t.append(x.exit_time);out_px.append(x.actual_exit);out_p.append(x.calc_profit);chg.append(False)
    led["policy_exit_time"]=out_t
    led["policy_exit_price"]=out_px
    led["policy_pnl"]=out_p
    led["policy_changed"]=chg
    return ans,led

def build_swings(h4, ev):
    rows=[]
    for i in range(2,len(h4)-2):
        if h4.loc[i,"high"]>h4.loc[i-2:i-1,"high"].max() and h4.loc[i,"high"]>h4.loc[i+1:i+2,"high"].max():
            rows.append((i,"BSL",float(h4.loc[i,"high"]),h4.loc[i+2,"known_at"]))
        if h4.loc[i,"low"]<h4.loc[i-2:i-1,"low"].min() and h4.loc[i,"low"]<h4.loc[i+1:i+2,"low"].min():
            rows.append((i,"SSL",float(h4.loc[i,"low"]),h4.loc[i+2,"known_at"]))
    sw=pd.DataFrame(rows,columns=["center_idx","type","level","known_at"])
    sw=sw[sw.known_at.notna()].copy()
    sw["level_key"]=sw.level.round(2)
    sw["consumed_at"]=pd.NaT
    arr=ev[ev.event.eq("H4_LIQ_ARRIVAL")][["tick_time","semantic_ref","arrival_side"]].copy()
    arr["semantic_ref"]=pd.to_numeric(arr.semantic_ref,errors="coerce")
    for a in arr.sort_values("tick_time").itertuples(index=False):
        typ="BSL" if a.arrival_side=="UP" else "SSL" if a.arrival_side=="DOWN" else None
        if typ is None or not np.isfinite(a.semantic_ref): continue
        key=round(float(a.semantic_ref),2)
        m=sw.type.eq(typ)&sw.level_key.eq(key)&(sw.known_at<=a.tick_time)&sw.consumed_at.isna()
        if m.any(): sw.loc[m,"consumed_at"]=a.tick_time
    return sw

def liq_at(sw, ts, direction, price, atr):
    a=sw[(sw.known_at<=ts)&(sw.consumed_at.isna()|(sw.consumed_at>ts))]
    same="BSL" if direction=="UP" else "SSL"
    opp="SSL" if direction=="UP" else "BSL"
    out={}
    for nm,typ in [("same",same),("opp",opp)]:
        z=a[a.type.eq(typ)].copy()
        if direction=="UP":
            dist=(z.level-price) if typ=="BSL" else (price-z.level)
        else:
            dist=(price-z.level) if typ=="SSL" else (z.level-price)
        z=z.assign(dist=dist); z=z[z.dist>0]
        out[nm+"_active_n"]=len(z)
        out[nm+"_d1_S"]=float(z.dist.min()/atr) if len(z) and atr>0 else np.nan
    ds=out["same_d1_S"];do=out["opp_d1_S"]
    out["distance_ratio"]=ds/do if np.isfinite(ds) and np.isfinite(do) and do>0 else np.nan
    return out

def ltf_eff(df,start,end,direction):
    w=df[(df.ts>=start)&(df.ts<end)]
    if len(w)<3: return np.nan
    s=1 if direction=="UP" else -1
    x=w.close.to_numpy(float); path=np.abs(np.diff(x)).sum()
    return float((-s*(x[-1]-x[0]))/path) if path>0 else np.nan

def build_ha1_states(ev,tr,routes,h4,m15,m30,sw,oracle_ans):
    omap=oracle_ans.set_index("route_id").oracle_ts.to_dict()
    base_route=tr[tr.route_id.isin(routes.route_id)].groupby("route_id").calc_profit.sum().to_dict()
    rows=[]
    for r in routes.itertuples(index=False):
        idx = h4.index[h4.ha1_up_to_down] if r.direction=="UP" else h4.index[h4.ha1_down_to_up]
        idx=[i for i in idx if pd.notna(h4.loc[i,"known_at"]) and h4.loc[i,"known_at"]>r.first_entry and h4.loc[i,"known_at"]<r.challenge_ts]
        prev_idx=None
        rg=tr[tr.route_id.eq(r.route_id)].sort_values("entry_time")
        for i in idx:
            ts=h4.loc[i,"known_at"]; atr=float(h4.loc[i,"atr180_calc"])
            if not np.isfinite(atr) or atr<=0: continue
            sign=1 if r.direction=="UP" else -1
            px_exec=float(h4.loc[i,"known_bid"] if r.direction=="UP" else h4.loc[i,"known_ask"])
            px=float(h4.loc[i,"close"])

            # PHA.
            j=i-1
            while j>=0 and h4.loc[j,"ha_side"]==r.direction: j-=1
            ps=j+1
            pha=h4.loc[ps:i-1]
            if pha.empty: continue
            pha_hi=float(pha.ha_high.max()); pha_lo=float(pha.ha_low.min()); pha_range=pha_hi-pha_lo

            # Position damage.
            openp=rg[(rg.entry_time<ts)&(rg.exit_time>ts)].copy()
            if len(openp):
                upnl=np.where(openp.direction.eq("UP"), px_exec-openp.actual_entry, openp.actual_entry-px_exec)
                loss=np.maximum(0,-upnl)
                lossatr=loss/openp.atr180.to_numpy(float)
                max_loss=float(np.nanmax(lossatr)); total_loss=float(np.nansum(lossatr))
            else:
                max_loss=total_loss=np.nan

            # CycleMin.
            cycle=np.nan
            if prev_idx is not None:
                prevpx=float(h4.loc[prev_idx,"close"])
                seg=h4.loc[prev_idx+1:i]
                if r.direction=="UP":
                    extpx=float(seg.high.max())
                    ext=max(0,extpx-prevpx)/atr; gb=max(0,extpx-px)/atr
                else:
                    extpx=float(seg.low.min())
                    ext=max(0,prevpx-extpx)/atr; gb=max(0,px-extpx)/atr
                cycle=min(ext,gb)

            # Liquidity now / latest Child / previous HA.
            cur=liq_at(sw,ts,r.direction,px,atr)
            lc=rg[rg.entry_time<ts].iloc[-1]
            child=liq_at(sw,lc.entry_time,r.direction,float(lc.semantic_entry),float(lc.atr180))

            # Label.
            ots=omap.get(r.route_id,pd.NaT)
            if pd.isna(ots): label="NO_ORACLE"
            elif ts<ots: label="EARLY"
            elif ts==ots: label="EXACT"
            else: label="LATE"

            # Route delta if exiting all survivors here.
            cand=0.0
            for t in rg.itertuples(index=False):
                if t.entry_time<ts<t.exit_time:
                    p=(px_exec-t.actual_entry) if t.direction=="UP" else (t.actual_entry-px_exec)
                    cand+=p
                else:
                    cand+=t.calc_profit
            route_delta=cand-base_route[r.route_id]

            close_pen=((pha_hi-float(h4.loc[i,"ha_close"]))/pha_range if r.direction=="UP"
                       else (float(h4.loc[i,"ha_close"])-pha_lo)/pha_range) if pha_range>0 else np.nan
            body_sum=abs(float(h4.loc[i,"ha_close"]-h4.loc[i,"ha_open"]))/pha_range if pha_range>0 else np.nan
            raw_range=(float(h4.loc[i,"ha_high"])-float(h4.loc[i,"ha_low"]))/pha_range if pha_range>0 else np.nan

            pressure=-sign*float(h4.loc[i,"pressure_flow2"])
            closeha=-sign*float(h4.loc[i,"closeha_body"])
            resilient=pressure*cycle/(1+cycle) if np.isfinite(cycle) else np.nan

            row={
                "route_id":r.route_id,"entry_year":r.first_entry.year,"direction":r.direction,
                "ha_idx":i,"decision_ts":ts,"decision_px":px_exec,"challenge_ts":r.challenge_ts,
                "state_label":label,"route_delta_if_exit":route_delta,
                "cycle_min":cycle,"resilient_pressure":resilient,
                "pressure_opp_flow2":pressure,"closeha_opp_body":closeha,
                "max_loss_entry_atr":max_loss,"total_loss_entry_atr":total_loss,
                "nha_close_penetration":close_pen,"nha_body_sum_over_pha_range":body_sum,
                "nha_range_over_pha_range":raw_range,
                "m15_raw_opp_eff_cum":ltf_eff(m15,h4.loc[i,"bar_start"],h4.loc[i,"bar_start"]+pd.Timedelta(hours=4),r.direction),
                "m30_raw_opp_eff_cum":ltf_eff(m30,h4.loc[i,"bar_start"],h4.loc[i,"bar_start"]+pd.Timedelta(hours=4),r.direction),
                "donchian_primary":float(h4.loc[i,"donchian_pos20"]) if r.direction=="UP" else 1-float(h4.loc[i,"donchian_pos20"]),
                "ha_opp_body_strength_S":-sign*float(h4.loc[i,"ha_close"]-h4.loc[i,"ha_open"])/atr,
                "liq_same_active_n":cur["same_active_n"],"liq_opp_active_n":cur["opp_active_n"],
                "liq_same_d1_S":cur["same_d1_S"],"liq_opp_d1_S":cur["opp_d1_S"],
                "liq_distance_ratio":cur["distance_ratio"],
                "liq_since_child_opp_d1_S":cur["opp_d1_S"]-child["opp_d1_S"] if np.isfinite(cur["opp_d1_S"]) and np.isfinite(child["opp_d1_S"]) else np.nan,
                "liq_since_child_distance_ratio":cur["distance_ratio"]-child["distance_ratio"] if np.isfinite(cur["distance_ratio"]) and np.isfinite(child["distance_ratio"]) else np.nan,
            }
            rows.append(row)
            prev_idx=i
    df=pd.DataFrame(rows).sort_values(["route_id","decision_ts"])
    for c in ["liq_same_active_n","liq_opp_active_n","liq_same_d1_S","liq_opp_d1_S","liq_distance_ratio"]:
        df["prevha_"+c+"_delta"]=df.groupby("route_id")[c].diff()
    return df

def percentile(train_vals,test_vals):
    a=np.asarray(train_vals,float); a=a[np.isfinite(a)]
    if len(a)==0: return np.full(len(test_vals),np.nan)
    a=np.sort(a)
    v=np.asarray(test_vals,float); v=np.where(np.isfinite(v),v,np.nanmedian(a))
    return np.searchsorted(a,v,side="right")/len(a)

def score_state(train,target,spec):
    p=[]
    for c,ori in spec.items():
        a=ori*train[c].to_numpy(float)
        if np.isfinite(a).sum()<10: continue
        p.append(percentile(a,ori*target[c].to_numpy(float)))
    return np.nanmean(p,axis=0) if p else np.full(len(target),np.nan)

def combo_screen(states: pd.DataFrame, tr_common: pd.DataFrame, oracle_led: pd.DataFrame, outdir: Path):
    specs={
        "SAME_PARTICIPATION_LOSS":{
            "prevha_liq_same_active_n_delta":-1,
            "prevha_liq_same_d1_S_delta":1,
        },
        "OPP_PRESSURE_GAIN":{
            "prevha_liq_opp_active_n_delta":1,
            "prevha_liq_opp_d1_S_delta":-1,
        },
        "CYCLE_MIN":{"cycle_min":1},
        "RESILIENT_PRESSURE":{"resilient_pressure":1},
        "DELIVERY":{
            "pressure_opp_flow2":1,"m15_raw_opp_eff_cum":1,
            "m30_raw_opp_eff_cum":1,"closeha_opp_body":1,
            "ha_opp_body_strength_S":1,
        },
        "POSITION_DAMAGE":{"max_loss_entry_atr":1,"total_loss_entry_atr":1},
        "PHA_NHA":{"nha_close_penetration":1,"nha_body_sum_over_pha_range":1,"nha_range_over_pha_range":1},
        "OLD_BEST3":{"liq_since_child_opp_d1_S":-1,"donchian_primary":-1,"ha_opp_body_strength_S":1},
    }
    names=list(specs)
    qgrid=[.5,.6,.7,.8,.9,.95,.975]
    rows=[]

    base_by_year=tr_common.groupby(tr_common.entry_time.dt.year).calc_profit.sum().to_dict()
    # Oracle improvement denominator by year.
    oyear=oracle_led.groupby(oracle_led.entry_time.dt.year).policy_pnl.sum().to_dict()

    scored={}
    for yr in [2025,2026]:
        train=states[(states.entry_year<yr)&states.cycle_min.notna()].copy()
        test=states[(states.entry_year==yr)&states.cycle_min.notna()].copy()
        for n,spec in specs.items():
            train[n]=score_state(train,train,spec)
            test[n]=score_state(train,test,spec)
        scored[yr]=(train,test)

    for k in range(1,5):
        for combo in itertools.combinations(names,k):
            for yr in [2025,2026]:
                train,test=scored[yr]
                train=train.copy();test=test.copy()
                train["score"]=train[list(combo)].mean(axis=1)
                test["score"]=test[list(combo)].mean(axis=1)
                best=None
                for q in qgrid:
                    thr=float(train.score.quantile(q))
                    sel=train[train.score>=thr].sort_values(["route_id","decision_ts"]).groupby("route_id",as_index=False).first()
                    delta=float(sel.route_delta_if_exit.sum())
                    if best is None or (delta,q)>(best[0],best[1]): best=(delta,q,thr)
                _,q,thr=best
                sel=test[test.score>=thr].sort_values(["route_id","decision_ts"]).groupby("route_id",as_index=False).first()
                delta=float(sel.route_delta_if_exit.sum())
                cnt=sel.state_label.value_counts().to_dict()
                denom=oyear.get(yr,np.nan)-base_by_year.get(yr,np.nan)
                rows.append({
                    "year":yr,"combo":"+".join(combo),"q_prior":q,"signals":len(sel),
                    "delta":delta,"recovery":delta/denom if denom else np.nan,
                    "EXACT":cnt.get("EXACT",0),"EARLY":cnt.get("EARLY",0),
                    "LATE":cnt.get("LATE",0),"FALSE":cnt.get("NO_ORACLE",0)
                })
    res=pd.DataFrame(rows)
    res.to_csv(outdir/"REPEAT_STATE_COMBINATION_WALKFORWARD_BY_YEAR.csv",index=False)
    sm=res.groupby("combo").agg(
        total_delta=("delta","sum"),min_year_delta=("delta","min"),
        mean_recovery=("recovery","mean"),EXACT=("EXACT","sum"),
        EARLY=("EARLY","sum"),LATE=("LATE","sum"),FALSE=("FALSE","sum"),
        signals=("signals","sum")).reset_index()
    sm.to_csv(outdir/"REPEAT_STATE_COMBINATION_SUMMARY.csv",index=False)
    return res,sm

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    args=ap.parse_args()
    args.out_dir.mkdir(parents=True,exist_ok=True)

    ev,tr=prepare_tester(args.data_dir)
    h4=prepare_h4(args.data_dir,ev)
    m15=prepare_ltf(args.data_dir/EXPECTED["m15"])
    m30=prepare_ltf(args.data_dir/EXPECTED["m30"])

    routes=build_routes(ev,tr,h4)
    common=tr[tr.route_id.isin(routes.route_id)].copy()
    common["policy_exit_time"]=common.exit_time
    common["policy_pnl"]=common.calc_profit

    ans,oled=oracle_ledger(common,routes,h4)
    sw=build_swings(h4,ev)
    states=build_ha1_states(ev,common,routes,h4,m15,m30,sw,ans)

    common.to_csv(args.out_dir/"BASE_COMMON_693_TRADES.csv",index=False)
    ans.to_csv(args.out_dir/"ORACLE_LITERAL_ANSWER_SHEET.csv",index=False)
    oled.to_csv(args.out_dir/"ORACLE_LITERAL_COMMON_TRADES.csv",index=False)
    states.to_csv(args.out_dir/"HA1_STATE_EVENTS.csv",index=False)

    combo,summary=combo_screen(states,common,oled,args.out_dir)

    b=metric(common)
    o=metric(oled)
    print("Common routes:",routes.route_id.nunique())
    print("Common Children:",len(common))
    print("Literal Oracle routes:",len(ans))
    print("BASE",b)
    print("ORACLE",o)
    print("\nTop repeat-state combinations by pooled delta:")
    print(summary.sort_values("total_delta",ascending=False).head(10).to_string(index=False))

if __name__=="__main__":
    main()
