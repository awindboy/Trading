#!/usr/bin/env python3
from __future__ import annotations
import argparse, io, json, heapq, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

SOURCE_SHA256="626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
START_OFFSET=86972434
END_OFFSET=90428045
BLOCK="2026JF"

def sha256(path: Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def load_block(path: Path):
    if sha256(path)!=SOURCE_SHA256:
        raise RuntimeError("authoritative M1 SHA256 mismatch")
    with path.open("rb") as f:
        f.seek(START_OFFSET); raw=f.read(END_OFFSET-START_OFFSET)
    cols=['date','time','open','high','low','close','tickvol','vol','spread']
    x=pd.read_csv(io.StringIO(raw.decode("utf-8")),sep="\t",header=None,names=cols)
    return pd.DataFrame({
        "ts":pd.to_datetime(x.date+" "+x.time,format="%Y.%m.%d %H:%M:%S"),
        "open":x.open.astype(float),"high":x.high.astype(float),
        "low":x.low.astype(float),"close":x.close.astype(float)
    })

def aggregate(df,hours):
    d=df.copy()
    d["bucket"]=d.ts.dt.floor(f"{hours}h")
    return d.groupby("bucket",sort=True).agg(
        open=("open","first"),high=("high","max"),low=("low","min"),
        close=("close","last"),last_ts=("ts","last")).reset_index()

def build_objects(df,hours):
    bars=aggregate(df,hours)
    objs=[]
    tf=f"H{hours}"
    for i in range(2,len(bars)-2):
        b=bars.iloc[i]; L=bars.iloc[i-2:i]; R=bars.iloc[i+1:i+3]
        known=pd.Timestamp(R.iloc[-1].bucket)+pd.Timedelta(hours=hours)
        if b.high>L.high.max() and b.high>=R.high.max():
            objs.append(dict(id=f"{tf}_BSL_{pd.Timestamp(b.bucket):%Y%m%d_%H%M}",side="UP",price=float(b.high),source=b.bucket,known_at=known))
        if b.low<L.low.min() and b.low<=R.low.min():
            objs.append(dict(id=f"{tf}_SSL_{pd.Timestamp(b.bucket):%Y%m%d_%H%M}",side="DOWN",price=float(b.low),source=b.bucket,known_at=known))
    o=pd.DataFrame(objs).sort_values(["known_at","id"]).reset_index(drop=True)
    o["raid_at"]=pd.NaT
    birth_order=list(o.sort_values(["known_at","id"]).index)
    bp=0
    active=set(); up=[]; dn=[]
    for r in df.itertuples(index=False):
        # Activate every object whose scheduled information time is now known.
        # This handles market gaps without synthesizing missing M1 rows.
        while bp < len(birth_order) and o.loc[birth_order[bp],"known_at"] <= r.ts:
            j=birth_order[bp]; bp += 1
            active.add(j)
            if o.loc[j,"side"]=="UP": heapq.heappush(up,(o.loc[j,"price"],j))
            else: heapq.heappush(dn,(-o.loc[j,"price"],j))
        while up:
            p,j=up[0]
            if j not in active: heapq.heappop(up); continue
            if p < r.high:
                heapq.heappop(up); active.remove(j); o.loc[j,"raid_at"]=r.ts
            else: break
        while dn:
            np_,j=dn[0]; p=-np_
            if j not in active: heapq.heappop(dn); continue
            if p > r.low:
                heapq.heappop(dn); active.remove(j); o.loc[j,"raid_at"]=r.ts
            else: break
    return bars,o

def event_stream(df,h4):
    rows=[]
    for ts,g in h4[h4.raid_at.notna()].groupby("raid_at",sort=True):
        if g.side.nunique()!=1: continue
        side=g.side.iloc[0]; ref=float(g.price.max() if side=="UP" else g.price.min())
        active=h4[(h4.known_at<=ts)&(h4.raid_at.isna() | (h4.raid_at>ts))]
        b=active[(active.side=="UP")&(active.price>ref)]
        s=active[(active.side=="DOWN")&(active.price<ref)]
        nb=float(b.price.min()) if len(b) else np.nan
        ns=float(s.price.max()) if len(s) else np.nan
        m=df[df.ts==ts].iloc[0]
        rows.append(dict(ts=ts,arrival_side=side,ref=ref,nearest_bsl=nb,nearest_ssl=ns,
                         m1_open=m.open,m1_high=m.high,m1_low=m.low,m1_close=m.close))
    ev=pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    state=None; primary=None; challenger=None; out=[]
    for idx,r in ev.iterrows():
        before=state; eligible=False
        if state is None:
            state="ACTIVE"; primary=r.arrival_side; res="SEED"
        elif state=="ACTIVE":
            if r.arrival_side==primary: res="PRIMARY_CONTINUES"; eligible=True
            else: state="CHALLENGED"; challenger=r.arrival_side; res="CHALLENGE_OPENS"
        else:
            if r.arrival_side==primary: state="ACTIVE"; challenger=None; res="OLD_PRIMARY_WINS"; eligible=True
            else: primary=challenger; state="ACTIVE"; challenger=None; res="CHALLENGER_EARNED"; eligible=True
        ds=do=np.nan; topo=np.nan
        if eligible:
            if primary=="UP":
                ds=r.nearest_bsl-r.ref if pd.notna(r.nearest_bsl) else np.nan
                do=r.ref-r.nearest_ssl if pd.notna(r.nearest_ssl) else np.nan
            else:
                ds=r.ref-r.nearest_ssl if pd.notna(r.nearest_ssl) else np.nan
                do=r.nearest_bsl-r.ref if pd.notna(r.nearest_bsl) else np.nan
            if pd.isna(ds) and pd.isna(do): topo="BOTH_TARGETS_MISSING"
            elif pd.isna(ds): topo="NO_SAME_TARGET"
            elif pd.isna(do): topo="NO_OPPOSITE_TARGET"
            elif ds<do: topo="SAME_NEAREST"
            else: topo="OPPOSITE_NEAREST"
        out.append({**r.to_dict(),"idx":idx,"before":before,"after":state,"primary":primary,
                    "resolution":res,"eligible":eligible,"topology":topo,"d_same":ds,"d_opp":do})
    x=pd.DataFrame(out)
    x["next_side"]=x.arrival_side.shift(-1)
    x["hit"]=np.where(x.eligible & x.next_side.notna(),x.next_side==x.primary,np.nan)
    x["block"]=BLOCK
    return x

def h1_sl(h1,ts,direction,entry):
    a=h1[(h1.known_at<=ts)&(h1.raid_at.isna() | (h1.raid_at>ts))]
    if direction=="UP":
        q=a[(a.side=="DOWN")&(a.price<entry)]
        return float(q.price.max()) if len(q) else np.nan
    q=a[(a.side=="UP")&(a.price>entry)]
    return float(q.price.min()) if len(q) else np.nan

def semantic_exit(ev,ts,direction):
    f=ev[(ev.ts>ts)&(ev.before=="ACTIVE")&(ev.after=="CHALLENGED")&(ev.arrival_side!=direction)]
    if len(f):
        r=f.iloc[0]; return r.ts,float(r.ref)
    return None,None

def resolve(df,ev,row):
    if pd.isna(row.sl): return "NO_VALID_SL",pd.NaT,np.nan
    xt,xp=semantic_exit(ev,row.entry_ts,row.direction)
    end=xt if xt is not None else df.ts.max()
    d=df[(df.ts>=row.entry_ts)&(df.ts<=end)]
    mask=d.low<=row.sl if row.direction=="UP" else d.high>=row.sl
    if mask.any():
        st=d.loc[mask,"ts"].iloc[0]
        if xt is not None and st==xt: return "AMBIGUOUS",st,np.nan
        if xt is None or st<xt: return "SL",st,-1.0
    if xt is None: return "OPEN_CENSORED",pd.NaT,np.nan
    sign=1 if row.direction=="UP" else -1
    return "CHALLENGE_OPENS",xt,sign*(xp-row.entry)/abs(row.entry-row.sl)

def one_position(x):
    keep=[]; until=None
    for i,r in x.sort_values("entry_ts").iterrows():
        term=r.exit_ts if pd.notna(r.exit_ts) else pd.Timestamp("2026-02-27 23:57:00")
        if until is None or r.entry_ts>until:
            keep.append(i); until=term
    return x.loc[keep].sort_values("entry_ts")

def metrics(x):
    rr=x.R.dropna(); p=rr[rr>0]; n=rr[rr<0]; cum=rr.cumsum(); dd=cum.cummax()-cum
    return dict(n=len(x),resolved=len(rr),wins=len(p),losses=len(n),wr=len(p)/len(rr) if len(rr) else None,
                total_R=float(rr.sum()),mean_R=float(rr.mean()) if len(rr) else None,
                PF=float(p.sum()/abs(n.sum())) if len(n) else None,maxDD=float(dd.max()) if len(rr) else None,
                avg_win_R=float(p.mean()) if len(p) else None,avg_loss_R=float(n.mean()) if len(n) else None)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--m1",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    df=load_block(a.m1)
    _,h4=build_objects(df,4); _,h1=build_objects(df,1); ev=event_stream(df,h4)
    trades=[]
    for _,r in ev[ev.eligible].iterrows():
        for universe in ("CONTROL","SAME_NEAREST"):
            if universe=="SAME_NEAREST" and r.topology!="SAME_NEAREST": continue
            sl=h1_sl(h1,r.ts,r.primary,float(r.ref))
            rec=dict(block=BLOCK,universe=universe,entry_ts=r.ts,direction=r.primary,entry=float(r.ref),
                     topology=r.topology,d_same=r.d_same,d_opp=r.d_opp,sl=sl,sl_dist=abs(float(r.ref)-sl) if pd.notna(sl) else np.nan)
            row=pd.Series(rec); st,xt,R=resolve(df,ev,row)
            rec.update(policy="CHALLENGE_EXIT",status=st,exit_ts=xt,R=R)
            trades.append(rec)
    t=pd.DataFrame(trades)
    summary=[]
    for u,g in t.groupby("universe"):
        op=one_position(g)
        m=metrics(op); m.update(universe=u,position_mode="ONE_POSITION")
        summary.append(m)
    ev.to_csv(a.out/"V9_ARRIVAL_LEDGER_2026JF.csv",index=False)
    h4.to_csv(a.out/"V9_H4_LIQUIDITY_OBJECTS_2026JF.csv",index=False)
    h1.to_csv(a.out/"V9_H1_LIQUIDITY_OBJECTS_2026JF.csv",index=False)
    t.to_csv(a.out/"V9_H1_STRUCT_CHALLENGE_2026JF.csv",index=False)
    pd.DataFrame(summary).to_csv(a.out/"V9_H1_STRUCT_CHALLENGE_2026JF_SUMMARY.csv",index=False)
    lab=ev[ev.eligible & ev.hit.notna()]
    sn=lab[lab.topology=="SAME_NEAREST"]; ns=lab[lab.topology!="SAME_NEAREST"]
    report={"same_nearest":{"n":len(sn),"hits":int(sn.hit.sum()),"rate":float(sn.hit.mean())},
            "not_same":{"n":len(ns),"hits":int(ns.hit.sum()),"rate":float(ns.hit.mean())},
            "summary":summary}
    (a.out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
