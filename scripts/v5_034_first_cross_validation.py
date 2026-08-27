#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib, math
from pathlib import Path
import numpy as np
import pandas as pd

RULE = "240min"

def load_m1(paths: list[Path]) -> pd.DataFrame:
    parts=[]
    for p in paths:
        d=pd.read_csv(p,sep="\t",usecols=["<DATE>","<TIME>","<OPEN>","<HIGH>","<LOW>","<CLOSE>","<SPREAD>"])
        idx=pd.to_datetime(d["<DATE>"].astype(str)+" "+d["<TIME>"].astype(str),format="%Y.%m.%d %H:%M:%S")
        parts.append(pd.DataFrame({
            "open":pd.to_numeric(d["<OPEN>"],errors="raise").to_numpy(float),
            "high":pd.to_numeric(d["<HIGH>"],errors="raise").to_numpy(float),
            "low":pd.to_numeric(d["<LOW>"],errors="raise").to_numpy(float),
            "close":pd.to_numeric(d["<CLOSE>"],errors="raise").to_numpy(float),
            "spread_points":pd.to_numeric(d["<SPREAD>"],errors="raise").to_numpy(float),
        },index=idx))
    q=pd.concat(parts).sort_index()
    if q.index.has_duplicates:
        q=q[~q.index.duplicated(keep="first")]
    if not q.index.is_monotonic_increasing:
        raise ValueError("M1 index not sorted")
    return q

def signal_bars(q: pd.DataFrame) -> pd.DataFrame:
    b=q.resample(RULE,closed="left",label="right").agg({
        "open":"first","high":"max","low":"min","close":"last","spread_points":"median"
    }).dropna()
    c=b.close
    b["fast"]=c.rolling(3).mean()-c.rolling(10).mean()
    b["slow"]=b.fast.rolling(16).mean()
    b["ema20"]=c.ewm(span=20,adjust=False,min_periods=20).mean()
    return b.dropna().copy()

def detect_setups(b: pd.DataFrame, point: float) -> list[dict]:
    ts=b.index.to_numpy(); h=b.high.to_numpy(); l=b.low.to_numpy()
    f=b.fast.to_numpy(); s=b.slow.to_numpy(); n=len(b)
    last_down=None; last_up=None; reg=0; ci=None; base=None
    seen=False; pull_i=None; used=False; out=[]
    for i in range(1,n-2):
        if s[i-1]>=0 and s[i]<0:
            last_down=i; reg=-1; ci=i
            base=np.max(h[last_up:i+1]) if last_up is not None else None
            seen=f[i]<0; pull_i=None; used=False; continue
        if s[i-1]<=0 and s[i]>0:
            last_up=i; reg=1; ci=i
            base=np.min(l[last_down:i+1]) if last_down is not None else None
            seen=f[i]>0; pull_i=None; used=False; continue
        if reg==1 and s[i]>0:
            if f[i]>0: seen=True
            if pull_i is None and seen and f[i-1]>=0 and f[i]<0: pull_i=i
        elif reg==-1 and s[i]<0:
            if f[i]<0: seen=True
            if pull_i is None and seen and f[i-1]<=0 and f[i]>0: pull_i=i
        if pull_i is None or used or base is None or i<pull_i+2:
            continue
        k=i-1; d=reg
        pivot=(l[k]<l[k-1] and l[k]<l[k+1]) if d==1 else (h[k]>h[k-1] and h[k]>h[k+1])
        if not pivot:
            continue
        used=True
        pext=l[k] if d==1 else h[k]
        if (d==1 and pext<=base) or (d==-1 and pext>=base):
            continue
        trigger=h[i]+point if d==1 else l[i]-point
        stop=pext-point if d==1 else pext+point
        if d*(trigger-stop)<=0:
            continue
        target=np.max(h[ci:pull_i]) if d==1 else np.min(l[ci:pull_i])
        expiry=ts[-1]
        for j in range(i+1,n):
            if (s[j]<=0 if d==1 else s[j]>=0):
                expiry=ts[j]; break
        out.append({
            "direction":int(d),"setup_i":int(i),"setup_end":pd.Timestamp(ts[i]),
            "pivot_i":int(k),"pull_i":int(pull_i),"trigger":float(trigger),"stop0":float(stop),
            "base_ext":float(base),"struct_target":float(target),"expiry":pd.Timestamp(expiry),
            "year":int(pd.Timestamp(ts[i]).year),
        })
    return out

def find_fill(q: pd.DataFrame, e: dict, point: float) -> dict:
    idx=q.index.to_numpy(); o=q.open.to_numpy(); h=q.high.to_numpy(); l=q.low.to_numpy()
    sp=q.spread_points.to_numpy()
    d=e["direction"]; tr=e["trigger"]; st=e["stop0"]; base=e["base_ext"]; target=e["struct_target"]
    start=np.searchsorted(idx,np.datetime64(e["setup_end"]),side="left")
    end=np.searchsorted(idx,np.datetime64(e["expiry"]),side="left")
    for j in range(start,min(end,len(idx))):
        invalid=(l[j]<=base if d==1 else h[j]>=base)
        hit=(h[j]>=tr if d==1 else l[j]<=tr)
        if invalid and hit:
            return {"fill_status":"ambiguous_prefill"}
        if invalid:
            return {"fill_status":"invalid_prefill"}
        if hit:
            entry=max(tr,o[j]) if d==1 else min(tr,o[j])
            if (l[j]<=st if d==1 else h[j]>=st):
                return {"fill_status":"ambiguous_fillstop","fill_ts":pd.Timestamp(idx[j])}
            risk=d*(entry-st)
            if risk<=0:
                return {"fill_status":"bad_risk"}
            target_r=d*(target-entry)/risk
            if target_r<=0:
                return {"fill_status":"no_target","fill_ts":pd.Timestamp(idx[j]),"entry":float(entry),"risk":float(risk),"target_r":float(target_r)}
            cost=2*sp[j]*point/risk
            return {
                "fill_status":"filled","fill_i":int(j),"fill_ts":pd.Timestamp(idx[j]),
                "entry":float(entry),"risk":float(risk),"target_r":float(target_r),"cost_r":float(cost)
            }
    return {"fill_status":"unfilled"}

def manage_candidate(q: pd.DataFrame, b: pd.DataFrame, fill: dict, e: dict) -> dict:
    if fill.get("fill_status")!="filled":
        return {"candidate_status":"not_eligible","gross_r":np.nan,"net_r":np.nan}
    idx=q.index.to_numpy(); o=q.open.to_numpy(); h=q.high.to_numpy(); l=q.low.to_numpy()
    d=e["direction"]; entry=float(fill["entry"]); risk=float(fill["risk"])
    stop=float(e["stop0"]); cost=float(fill["cost_r"]); one=entry+d*risk
    start=int(fill["fill_i"])
    # Completed adverse 240m states. A bar labeled T represents [T-240m,T), so it is available at T.
    bb=b.loc[b.index>fill["fill_ts"]]
    adverse_times=[]
    for bt,br in bb.iterrows():
        adverse=(br.close<br.ema20 or br.slow<=0) if d==1 else (br.close>br.ema20 or br.slow>=0)
        if adverse:
            adverse_times.append(pd.Timestamp(bt))
    partial=False; next_adv=None
    for j in range(start,len(idx)):
        ts=pd.Timestamp(idx[j])
        astop=entry if partial else stop
        hit_stop=(l[j]<=astop if d==1 else h[j]>=astop)
        hit_1=(h[j]>=one if d==1 else l[j]<=one) if not partial else False
        if not partial:
            if hit_stop and hit_1:
                return {"candidate_status":"ambiguous_pre1","gross_r":np.nan,"net_r":np.nan,"end_ts":ts}
            if hit_stop:
                return {"candidate_status":"loss","gross_r":-1.0,"net_r":-1.0-cost,"end_ts":ts}
            if hit_1:
                partial=True
                next_adv=next((x for x in adverse_times if x>ts),None)
                # M1 cannot order +1R touch and return to entry inside the same minute.
                if (l[j]<=entry if d==1 else h[j]>=entry):
                    return {"candidate_status":"ambiguous_partial","gross_r":np.nan,"net_r":np.nan,"end_ts":ts}
        else:
            if hit_stop:
                return {"candidate_status":"partial_be","gross_r":0.5,"net_r":0.5-cost,"end_ts":ts}
            if next_adv is not None and ts>=next_adv:
                runner_r=d*(o[j]-entry)/risk
                gross=0.5+0.5*runner_r
                return {"candidate_status":"ema_slow","gross_r":float(gross),"net_r":float(gross-cost),"end_ts":ts}
    return {"candidate_status":"censored","gross_r":np.nan,"net_r":np.nan}

def metrics(df: pd.DataFrame) -> dict:
    r=df[df.net_r.notna()].copy()
    pos=r[r.net_r>0]
    return {
        "n":int(len(r)),
        "wr":float((r.net_r>0).mean()) if len(r) else None,
        "avg_positive_net_r":float(pos.net_r.mean()) if len(pos) else None,
        "ev_net_r":float(r.net_r.mean()) if len(r) else None,
        "total_net_r":float(r.net_r.sum()) if len(r) else None,
        "avg_cost_r":float(r.cost_r.mean()) if len(r) else None,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-map",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    args=ap.parse_args()
    dm=json.loads(args.data_map.read_text(encoding="utf-8"))
    args.out_dir.mkdir(parents=True,exist_ok=True)
    all_ledgers=[]
    summary={"candidate":"V5_030A_FIRST_CROSS_240M_HALF_EMA_RUNNER","markets":{}}
    for symbol,spec in dm.items():
        point=float(spec["point"]); paths=[Path(x) for x in spec["files"]]
        for p in paths:
            if not p.exists(): raise SystemExit(f"FAIL-CLOSED missing {p}")
        q=load_m1(paths); b=signal_bars(q)
        rows=[]
        for e in detect_setups(b,point):
            f=find_fill(q,e,point)
            c=manage_candidate(q,b,f,e)
            row={**e,**f,**c,"symbol":symbol}
            rows.append(row)
        out=pd.DataFrame(rows)
        path=args.out_dir/f"{symbol.replace('#','')}_V5_034_LEDGER.csv"
        out.to_csv(path,index=False)
        all_ledgers.append(out)
        rr=out[out.net_r.notna()].copy()
        summary["markets"][symbol]={
            "overall":metrics(out),
            "years":{str(int(y)):metrics(g) for y,g in rr.groupby("year")},
            "directions":{str(int(d)):metrics(g) for d,g in rr.groupby("direction")},
            "ledger_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        print(symbol,summary["markets"][symbol]["overall"],flush=True)
    pooled=pd.concat(all_ledgers,ignore_index=True)
    rr=pooled[pooled.net_r.notna()].copy()
    summary["pooled"]=metrics(pooled)
    summary["pooled_years"]={str(int(y)):metrics(g) for y,g in rr.groupby("year")}
    # leave-one-market-out
    summary["leave_one_market_out"]={}
    for symbol in dm:
        summary["leave_one_market_out"][symbol]=metrics(rr[rr.symbol!=symbol])
    sumpath=args.out_dir/"V5_034_VALIDATION_SUMMARY.json"
    sumpath.write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("summary",sumpath,flush=True)

if __name__=="__main__":
    main()
