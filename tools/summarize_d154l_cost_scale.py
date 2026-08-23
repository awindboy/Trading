#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,re,statistics,zipfile
from pathlib import Path

def kv(s:str):
    return {m.group(1):m.group(2) for m in re.finditer(r"(\w+)=([^ ]+)",s or "")}

def med(xs):
    return statistics.median(xs) if xs else float("nan")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("master_zip",type=Path)
    args=ap.parse_args()

    print("cell,fills,wins,wr,median_spread_over_reaction_tr,median_spread_over_risk,median_spread_over_fvg,median_risk_over_reaction_tr")
    with zipfile.ZipFile(args.master_zip) as master:
        for nested_name in master.namelist():
            if not nested_name.endswith(".zip"):
                continue
            cell=nested_name.split("/",1)[0]
            with zipfile.ZipFile(io.BytesIO(master.read(nested_name))) as z:
                csvs=[n for n in z.namelist() if n.endswith(".csv")]
                if len(csvs)!=1:
                    raise RuntimeError(f"{cell}: expected one CSV")
                rows=list(csv.DictReader(io.StringIO(z.read(csvs[0]).decode("utf-8-sig",errors="replace"))))

            snaps={}
            outs={}
            for r in rows:
                d=kv(r.get("detail",""))
                sid=d.get("scenario_id",r.get("object_id",""))
                if r.get("event")=="D154K_CROSS_SCALE_SNAPSHOT" and sid:
                    snaps[sid]=d
                elif r.get("event")=="D154K_PRIMARY_OUTCOME" and sid:
                    outs[sid]=d.get("outcome","RIGHT_CENSORED")
            resolved=[s for s in snaps if outs.get(s) in ("PLUS_1R","SL_FIRST")]
            wins=sum(outs[s]=="PLUS_1R" for s in resolved)
            def vals(key):
                out=[]
                for s in resolved:
                    try:
                        out.append(float(snaps[s][key]))
                    except Exception:
                        pass
                return out
            print(
                f"{cell},{len(resolved)},{wins},{wins/len(resolved) if resolved else float('nan'):.6f},"
                f"{med(vals('spread_over_reaction_tr')):.8f},"
                f"{med(vals('spread_over_risk')):.8f},"
                f"{med(vals('spread_over_fvg')):.8f},"
                f"{med(vals('risk_over_reaction_tr')):.8f}"
            )
    print("\nFrozen interpretation: compare direction/ranking only. Do not fit a threshold from these cells.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
