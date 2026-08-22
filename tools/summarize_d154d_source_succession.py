#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re,zipfile,tempfile
from collections import defaultdict
from pathlib import Path
from statistics import median

KV=re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")

def kv(s): return {m.group(1):m.group(2) for m in KV.finditer(s or "")}

def csv_paths(inputs):
    out=[]
    tempdirs=[]
    for raw in inputs:
        p=Path(raw)
        if p.is_dir():
            out+=sorted(p.rglob("*.csv"))
        elif p.suffix.lower()==".csv":
            out.append(p)
        elif p.suffix.lower()==".zip":
            td=Path(tempfile.mkdtemp(prefix="d154d_analyze_")); tempdirs.append(td)
            with zipfile.ZipFile(p) as z:z.extractall(td)
            # nested cell zips
            for nz in list(td.rglob("*.zip")):
                sub=nz.with_suffix("")
                sub.mkdir(exist_ok=True)
                with zipfile.ZipFile(nz) as z:z.extractall(sub)
            out+=sorted(td.rglob("*.csv"))
    return out

def read(p):
    with p.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def label(p,rows):
    for r in rows:
        if r.get("event")=="EA_START":
            x=kv(r.get("detail",""))
            sym=x.get("symbol","")
            if sym:
                # infer year from filename/batch path when possible
                s=str(p)
                for tag in ("GOLD23","GOLD24","SILVER25","CADJPY25"):
                    if tag in s:return tag
                return sym
    return p.stem

def pct(k,n): return "NA" if not n else f"{100*k/n:.1f}%"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("paths",nargs="+")
    a=ap.parse_args()

    all_unique=[]
    all_first=[]
    failure_summary=[]

    for p in csv_paths(a.paths):
        rows=read(p)
        if not any(r.get("event")=="D154A_SUCCESSOR_STAGE" for r in rows):
            continue
        cell=label(p,rows)

        prim={}
        fill_at={}
        failures={}
        terminals={}
        succ=[]

        for idx,r in enumerate(rows):
            e=r.get("event",""); x=kv(r.get("detail",""))
            sid=x.get("scenario_id") or r.get("object_id","")
            if e=="D154A_PRIMARY_OUTCOME" and sid:
                prim[sid]=x.get("outcome","")
            elif e=="D154A_FILL_OWNERSHIP" and sid:
                try:fill_at[sid]=int(x.get("fill_at_s","0"))
                except:fill_at[sid]=0
            elif e=="D154A_SL_FAILURE_STATE" and sid:
                failures[sid]=x
            elif e=="D154A_RECOVERY_TERMINAL" and sid:
                terminals[sid]=x
            elif e=="D154A_SUCCESSOR_STAGE" and x.get("stage")=="FILL":
                succ.append((idx,x))

        failure_summary.append((
            cell,len(failures),
            sum(x.get("map_support_same_at_sl")=="true" for x in failures.values()),
            sum((terminals.get(sid,{}) or {}).get("outcome")=="RECOVERED_PLUS_1R_BEFORE_MAP_LOSS" for sid in failures),
            sum((terminals.get(sid,{}) or {}).get("outcome")=="MAP_SUPPORT_LOST_AFTER_SL" for sid in failures),
        ))

        # Unique actual successor candidates, globally deduped within cell.
        seen=set()
        for idx,x in succ:
            cand=x.get("candidate_scenario_id","")
            if not cand or cand in seen: continue
            seen.add(cand)
            direction="LONG" if ":LONG:" in cand else ("SHORT" if ":SHORT:" in cand else "NA")
            all_unique.append({
                "cell":cell,"candidate":cand,"direction":direction,
                "new_root":x.get("root_new_after_failure")=="true",
                "outcome":prim.get(cand,"UNKNOWN"),
                "root_tf":x.get("candidate_root_tf","NA"),
            })

        # Operational first successor fill per failed scenario.
        by_orig={}
        for idx,x in succ:
            orig=x.get("scenario_id",""); cand=x.get("candidate_scenario_id","")
            if not orig or not cand: continue
            ct=fill_at.get(cand,10**18)
            key=(ct,idx)
            if orig not in by_orig or key<by_orig[orig][0]:
                by_orig[orig]=(key,x)
        for orig,(key,x) in by_orig.items():
            cand=x.get("candidate_scenario_id","")
            fat=int(failures.get(orig,{}).get("failure_at_s","0") or 0)
            ct=fill_at.get(cand,0)
            direction="LONG" if ":LONG:" in cand else ("SHORT" if ":SHORT:" in cand else "NA")
            all_first.append({
                "cell":cell,"orig":orig,"candidate":cand,"direction":direction,
                "new_root":x.get("root_new_after_failure")=="true",
                "outcome":prim.get(cand,"UNKNOWN"),
                "delay_h":(ct-fat)/3600 if ct and fat else None,
                "original_terminal":terminals.get(orig,{}).get("outcome","UNKNOWN"),
            })

    print("== FAILURE POPULATION ==")
    print(f"{'cell':12s} {'SL-first':>8s} {'map-same':>9s} {'recover':>8s} {'map-loss':>8s}")
    for row in failure_summary:
        print(f"{row[0]:12s} {row[1]:8d} {row[2]:9d} {row[3]:8d} {row[4]:8d}")

    def summarize(records,title):
        print(f"\n== {title} ==")
        groups=defaultdict(list)
        for r in records:
            cls="NEW_ROOT_AFTER_FAILURE" if r["new_root"] else "OTHER_EXISTING_ROOT"
            groups[(r["cell"],cls)].append(r)
            groups[("POOLED",cls)].append(r)
        print(f"{'cell/class':38s} {'n':>5s} {'+1R':>5s} {'SL':>5s} {'rate':>8s}")
        for (cell,cls),rs in sorted(groups.items()):
            plus=sum(r["outcome"]=="PLUS_1R" for r in rs)
            sl=sum(r["outcome"]=="SL_FIRST" for r in rs)
            print(f"{(cell+'|'+cls):38s} {len(rs):5d} {plus:5d} {sl:5d} {pct(plus,plus+sl):>8s}")

    summarize(all_unique,"UNIQUE ACTUAL SUCCESSOR FILLS")
    summarize(all_first,"FIRST SUCCESSOR FILL PER FAILED SCENARIO")

    print("\n== DIRECTION CHECK: UNIQUE CANDIDATES ==")
    groups=defaultdict(list)
    for r in all_unique:
        cls="NEW" if r["new_root"] else "EXISTING"
        groups[(r["cell"],r["direction"],cls)].append(r)
    for k,rs in sorted(groups.items()):
        plus=sum(r["outcome"]=="PLUS_1R" for r in rs)
        sl=sum(r["outcome"]=="SL_FIRST" for r in rs)
        print(f"{'|'.join(k):30s} n={len(rs):3d} +1R={plus:3d} SL={sl:3d} rate={pct(plus,plus+sl)}")

    print("\n== DECISION BOUNDARY ==")
    print("- Discovery reference GOLD25/BTC25 is NOT included in these OOS runs.")
    print("- Existing-other-Root succession is not promoted if it remains near baseline ~50%.")
    print("- NEW_ROOT_AFTER_FAILURE needs non-trivial independent samples and direction consistency.")
    print("- A 4/4 discovery result is not enough; a reversal/collapse in OOS rejects it.")
    print("- Same-Root retry remains lifecycle-constrained and is not inferred from zero observations.")
    print("- This is source-succession evidence only; no re-entry, sizing, SL, or EM authority.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
