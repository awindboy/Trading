#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from pathlib import Path

def load(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def canonical(rows):
    out=[]
    for r in rows:
        if r.get("event","").startswith("D154H_"): continue
        x=dict(r)
        d=x.get("detail","")
        d=re.sub(r"csv_rows_written=\d+","csv_rows_written=<NORMALIZED>",d)
        x["detail"]=d
        out.append(tuple(x.get(k,"") for k in ("observed_at","event","timeframe","available_at","object_id","detail")))
    return out

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("off",type=Path); ap.add_argument("on",type=Path); args=ap.parse_args()
    a,b=load(args.off),load(args.on); ca,cb=canonical(a),canonical(b)
    hon=sum(1 for r in b if r.get("event","").startswith("D154H_")); hoff=sum(1 for r in a if r.get("event","").startswith("D154H_"))
    if hoff:
        print(f"D154H NON-INTERFERENCE PARITY: FAIL | OFF D154H rows={hoff}"); return 2
    if ca!=cb:
        print(f"D154H NON-INTERFERENCE PARITY: FAIL | canonical OFF={len(ca)} ON={len(cb)}")
        for i,(x,y) in enumerate(zip(ca,cb)):
            if x!=y:
                print("first_diff_index=",i); print("OFF",x); print("ON ",y); break
        if len(ca)!=len(cb): print("canonical length differs")
        return 2
    print(f"D154H NON-INTERFERENCE PARITY: PASS | canonical_rows={len(ca)} | d154h_on_rows={hon}")
    return 0
if __name__=="__main__": raise SystemExit(main())
