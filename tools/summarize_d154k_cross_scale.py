#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,re,statistics,zipfile
from pathlib import Path

METRICS=[
    "reaction_mean_tr","reaction_efficiency","reaction_net_over_tr","reaction_path_over_tr",
    "reaction_range_over_tr","reaction_favorable_over_tr","reaction_adverse_over_tr",
    "risk_over_reaction_tr","fvg_over_reaction_tr","root_over_reaction_tr",
    "plan_span_over_reaction_tr","plan_remaining_over_reaction_tr",
    "spread_over_reaction_tr","spread_over_risk","spread_over_fvg",
    "slippage_over_reaction_tr","slippage_over_risk",
    "pullback_choch_to_fill_over_tr","pullback_choch_to_fill_over_risk",
    "risk_over_price","reaction_tr_over_price","plan_span_over_price",
]

def kv(s):
    return {m.group(1):m.group(2) for m in re.finditer(r"(\w+)=([^ ]+)",s or "")}

def get_full_csvs(master:Path):
    with zipfile.ZipFile(master) as z:
        nested=[n for n in z.namelist() if n.startswith("cross_scale/") and n.endswith(".zip")]
        if len(nested)!=1:
            raise RuntimeError(f"expected one cross_scale ZIP, found {len(nested)}")
        payload=z.read(nested[0])
    out=[]
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for n in z.namelist():
            if n.endswith(".csv"):
                out.append((n,list(csv.DictReader(io.StringIO(z.read(n).decode("utf-8-sig",errors="replace"))))))
    return out

def med(xs):
    return statistics.median(xs) if xs else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("master_zip",type=Path)
    args=ap.parse_args()
    for name,rows in get_full_csvs(args.master_zip):
        sym="GOLD" if "__GOLD__" in name else ("CADJPY" if "__CADJPY__" in name else name)
        snap={}
        outcome={}
        for r in rows:
            d=kv(r.get("detail",""))
            sid=d.get("scenario_id",r.get("object_id",""))
            if r.get("event")=="D154K_CROSS_SCALE_SNAPSHOT" and sid:
                snap[sid]=d
            elif r.get("event")=="D154K_PRIMARY_OUTCOME" and sid:
                outcome[sid]=d.get("outcome","RIGHT_CENSORED")
        resolved=[s for s in snap if outcome.get(s) in ("PLUS_1R","SL_FIRST")]
        print(f"\n[{sym}] snapshots={len(snap)} resolved={len(resolved)} wins={sum(outcome.get(s)=='PLUS_1R' for s in resolved)}")
        for metric in METRICS:
            vals={}
            for grp in ("ALL","PLUS_1R","SL_FIRST"):
                xs=[]
                for sid in resolved:
                    if grp!="ALL" and outcome.get(sid)!=grp:
                        continue
                    try:
                        x=float(snap[sid].get(metric,"nan"))
                        if x==x:
                            xs.append(x)
                    except Exception:
                        pass
                vals[grp]=med(xs)
            if vals["ALL"] is not None:
                print(f"{metric:34s} all={vals['ALL']:.6g} win={vals['PLUS_1R']} loss={vals['SL_FIRST']}")
    print("\nDescriptive only: no thresholds or symbol-specific gates are fitted.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
