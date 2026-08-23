#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,re,zipfile
from collections import defaultdict
from pathlib import Path

def kv(s:str):
    return {m.group(1):m.group(2) for m in re.finditer(r"(\w+)=([^ ]+)",s or "")}

def pct(n,d):
    return 100.0*n/d if d else float("nan")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("master_zip",type=Path)
    args=ap.parse_args()

    print("cell,fills,actual_plus1,actual_sl,actual_cens,actual_wr,shadow_plus1,shadow_sl,shadow_cens,shadow_wr,sl_to_plus1,rescue_pct_of_actual_sl,plus1_to_sl")
    with zipfile.ZipFile(args.master_zip) as master:
        nested=[n for n in master.namelist() if n.endswith(".zip") and not n.startswith("parity/")]
        for nested_name in nested:
            cell=nested_name.split("/",1)[0]
            with zipfile.ZipFile(io.BytesIO(master.read(nested_name))) as z:
                csvs=[n for n in z.namelist() if n.endswith(".csv")]
                if len(csvs)!=1:
                    raise RuntimeError(f"{cell}: expected one CSV")
                rows=list(csv.DictReader(io.StringIO(
                    z.read(csvs[0]).decode("utf-8-sig",errors="replace")
                )))

            pairs=[]
            by_dir=defaultdict(list)
            for r in rows:
                if r.get("event")!="D154M_PAIR_OUTCOME":
                    continue
                d=kv(r.get("detail",""))
                pairs.append(d)
                by_dir[d.get("direction","NA")].append(d)

            def summarize(ps):
                ap1=sum(p.get("actual_outcome")=="PLUS_1R" for p in ps)
                asl=sum(p.get("actual_outcome")=="SL_FIRST" for p in ps)
                ac=sum(p.get("actual_outcome")=="RIGHT_CENSORED" for p in ps)
                sp1=sum(p.get("shadow_outcome")=="PLUS_1R" for p in ps)
                ssl=sum(p.get("shadow_outcome")=="SL_FIRST" for p in ps)
                sc=sum(p.get("shadow_outcome")=="RIGHT_CENSORED" for p in ps)
                rescue=sum(p.get("pair_class")=="ACTUAL_SL_TO_SHADOW_PLUS_1R" for p in ps)
                bad=sum(p.get("pair_class")=="ACTUAL_PLUS_1R_TO_SHADOW_SL" for p in ps)
                return ap1,asl,ac,sp1,ssl,sc,rescue,bad

            ap1,asl,ac,sp1,ssl,sc,rescue,bad=summarize(pairs)
            print(
                f"{cell},{len(pairs)},{ap1},{asl},{ac},{pct(ap1,ap1+asl):.4f},"
                f"{sp1},{ssl},{sc},{pct(sp1,sp1+ssl):.4f},"
                f"{rescue},{pct(rescue,asl):.4f},{bad}"
            )
            for direction,ps in sorted(by_dir.items()):
                x=summarize(ps)
                print(
                    f"  {direction}: n={len(ps)} actual={x[0]}/{x[0]+x[1]} "
                    f"shadow={x[3]}/{x[3]+x[4]} SL->+1R={x[6]} +1R->SL={x[7]}"
                )

    print("\nInterpretation boundary:")
    print("- SL->+1R counts quote-side barrier flips, not a proposed trade rule.")
    print("- No fill, SL, +1R target, order, SP or EM is changed.")
    print("- Do not infer a zero-spread broker or optimized spread threshold.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
