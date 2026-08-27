#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, json, hashlib
import numpy as np
import pandas as pd

SCALES=(60,240,1440)
HORIZONS=(5,15,30,60,240)

def read_mt5(paths):
    parts=[]
    for path in paths:
        d=pd.read_csv(path,sep="\t",usecols=["<DATE>","<TIME>","<OPEN>","<HIGH>","<LOW>","<CLOSE>","<TICKVOL>","<SPREAD>"])
        idx=pd.to_datetime(d["<DATE>"].astype(str)+" "+d["<TIME>"].astype(str),format="%Y.%m.%d %H:%M:%S")
        q=pd.DataFrame(index=pd.DatetimeIndex(idx))
        for name,col in [("open","<OPEN>"),("high","<HIGH>"),("low","<LOW>"),("close","<CLOSE>"),
                         ("tickvol","<TICKVOL>"),("spread_points","<SPREAD>")]:
            q[name]=pd.to_numeric(d[col],errors="raise").to_numpy(float)
        parts.append(q)
    q=pd.concat(parts).sort_index()
    if q.index.has_duplicates:
        raise ValueError("duplicate timestamps")
    return q

def descriptor(q,t,scale,direction):
    a=t-pd.Timedelta(minutes=scale)
    b=t-pd.Timedelta(minutes=2*scale)
    cur=q.loc[(q.index>=a)&(q.index<t)]
    prv=q.loc[(q.index>=b)&(q.index<a)]
    if len(cur)<3 or len(prv)<3:return None
    hi=float(cur.high.max());lo=float(cur.low.min());rng=hi-lo
    phi=float(prv.high.max());plo=float(prv.low.min());prng=phi-plo
    if not np.isfinite(rng) or rng<=0 or not np.isfinite(prng) or prng<=0:return None
    lr=np.log(cur.close/cur.close.shift(1)).dropna()
    plr=np.log(prv.close/prv.close.shift(1)).dropna()
    den=float(lr.abs().sum())
    eff=abs(float(lr.sum()))/den if den>0 else np.nan
    rv=float(np.sqrt(np.square(lr.to_numpy()).sum())) if len(lr) else np.nan
    prv_rv=float(np.sqrt(np.square(plr.to_numpy()).sum())) if len(plr) else np.nan
    mid=(hi+lo)/2
    side=np.sign(cur.close.to_numpy()-mid)
    cross=int(np.sum(side[1:]*side[:-1]<0)) if len(side)>1 else 0
    cross_density=cross/max(1,len(side)-1)
    if direction==1:
        boundary=hi; created=cur.high.idxmax()
    else:
        boundary=lo; created=cur.low.idxmin()
    return {
        "high":hi,"low":lo,"range":rng,"boundary":boundary,
        "directional_efficiency":eff,
        "contraction_ratio":rng/prng,
        "rv_ratio":rv/prv_rv if np.isfinite(prv_rv) and prv_rv>0 else np.nan,
        "mid_cross_density":cross_density,
        "boundary_age_min":(t-created).total_seconds()/60,
        "activity_ratio":float(cur.tickvol.sum())/float(prv.tickvol.sum()) if float(prv.tickvol.sum())>0 else np.nan,
        "window_bars":int(len(cur)),"previous_window_bars":int(len(prv))
    }

def path_arrays(q,t,boundary,direction,rng,h):
    end=t+pd.Timedelta(minutes=h)
    w=q.loc[(q.index>=t)&(q.index<=end)]
    if len(w)==0:return {}
    c=w.close.to_numpy();hi=w.high.to_numpy();lo=w.low.to_numpy()
    if direction==1:
        ext=(hi.max()-boundary)/rng;inside=(boundary-lo.min())/rng;beyond=c>boundary;re=c<boundary
    else:
        ext=(boundary-lo.min())/rng;inside=(hi.max()-boundary)/rng;beyond=c<boundary;re=c>boundary
    rr=np.flatnonzero(re)
    re_min=(w.index[rr[0]]-t).total_seconds()/60 if len(rr) else np.nan
    lr=np.diff(np.log(c)) if len(c)>1 else np.array([])
    den=np.abs(lr).sum()
    return {
        f"res_{h}":direction*(float(c[-1])-boundary)/rng,
        f"ext_{h}":float(ext),f"inside_{h}":float(inside),f"beyond_frac_{h}":float(np.mean(beyond)),
        f"reentry_min_{h}":float(re_min) if np.isfinite(re_min) else np.nan,
        f"dir_eff_{h}":direction*float(lr.sum())/float(den) if len(lr) and den>0 else np.nan,
        f"rv_post_{h}":float(np.sqrt(np.square(lr).sum())) if len(lr) else np.nan,
        f"bars_{h}":int(len(w)),f"complete_{h}":bool(w.index[-1]>=end-pd.Timedelta(minutes=1))
    }

def select_episodes(q,scale,direction,rolling_high,rolling_low):
    hi=q.high.to_numpy();lo=q.low.to_numpy();cl=q.close.to_numpy()
    H=rolling_high.to_numpy();L=rolling_low.to_numpy()
    valid=np.isfinite(H)&np.isfinite(L)&(H>L)
    cand=np.flatnonzero(valid & ((hi>H) if direction==1 else (lo<L)))
    out=[]
    pos=0
    n=len(q)
    while pos<len(cand):
        j=int(cand[pos])
        frozen_hi=float(H[j]);frozen_lo=float(L[j])
        out.append(j)
        # Re-arm at the first completed close inside the frozen range.
        inside=np.flatnonzero((cl[j:]>=frozen_lo)&(cl[j:]<=frozen_hi))
        rearm=j+int(inside[0]) if len(inside) else n
        # next candidate must be strictly after the re-arm close
        pos=int(np.searchsorted(cand,rearm+1,side="left"))
    return out

def build(symbol,point,paths):
    q=read_mt5(paths)
    rows=[]
    # All rolling boundaries exclude the current M1 bar via closed='left'.
    for scale in SCALES:
        H=q.high.rolling(f"{scale}min",closed="left",min_periods=3).max()
        L=q.low.rolling(f"{scale}min",closed="left",min_periods=3).min()
        up=set(select_episodes(q,scale,1,H,L))
        dn=set(select_episodes(q,scale,-1,H,L))
        event_idx=sorted(up|dn)
        for j in event_idx:
            t=q.index[j];bar=q.iloc[j]
            directions=[]
            if j in up:directions.append(1)
            if j in dn:directions.append(-1)
            dual=len(directions)==2
            for direction in directions:
                d=descriptor(q,t,scale,direction)
                if d is None:continue
                row={"symbol":symbol,"event_ts":t.isoformat(),"year":t.year,"direction":direction,"scale_min":scale,
                     "boundary":d["boundary"],"range_low":d["low"],"range_high":d["high"],"range_width":d["range"],
                     "directional_efficiency":d["directional_efficiency"],"contraction_ratio":d["contraction_ratio"],
                     "rv_ratio":d["rv_ratio"],"mid_cross_density":d["mid_cross_density"],
                     "boundary_age_min":d["boundary_age_min"],"activity_ratio":d["activity_ratio"],
                     "window_bars":d["window_bars"],"previous_window_bars":d["previous_window_bars"],
                     "spread_return":bar.spread_points*point/bar.close,"dual_break":dual}
                for h in HORIZONS:
                    row.update(path_arrays(q,t,d["boundary"],direction,d["range"],h))
                rows.append(row)
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-map",type=Path,required=True,help="JSON {symbol:{point,files:[...]}}")
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    dm=json.loads(args.data_map.read_text(encoding="utf-8"))
    allx=[]
    for symbol,spec in dm.items():
        paths=[Path(x) for x in spec["files"]]
        for p in paths:
            if not p.exists():raise SystemExit(f"FAIL-CLOSED missing {p}")
        z=build(symbol,float(spec["point"]),paths);allx.append(z)
        print(symbol,len(z),flush=True)
    out=pd.concat(allx,ignore_index=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(args.out,index=False,compression="gzip" if str(args.out).endswith(".gz") else None)
    sha=hashlib.sha256(args.out.read_bytes()).hexdigest()
    print("ROWS",len(out),"SHA256",sha,flush=True)

if __name__=="__main__":
    main()
