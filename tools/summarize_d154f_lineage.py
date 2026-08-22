#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re,tempfile,zipfile,json
from collections import defaultdict
from pathlib import Path
from statistics import median

KV=re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")

def kv(s): return {m.group(1):m.group(2) for m in KV.finditer(s or "")}
def pct(k,n): return "NA" if not n else f"{100*k/n:.1f}%"
def num(x):
    try:return float(x)
    except:return None

def expand(inputs):
    roots=[]
    for raw in inputs:
        p=Path(raw)
        if p.is_dir():
            roots.append(p)
        elif p.suffix.lower()==".zip":
            td=Path(tempfile.mkdtemp(prefix="d154f_"))
            with zipfile.ZipFile(p) as z:z.extractall(td)
            # validation master contains nested cell ZIPs
            for nz in list(td.rglob("*.zip")):
                sub=nz.with_suffix("")
                sub.mkdir(exist_ok=True)
                with zipfile.ZipFile(nz) as z:z.extractall(sub)
            roots.append(td)
        elif p.suffix.lower()==".csv":
            roots.append(p.parent)
    return roots

def read_csv(p):
    with p.open("r",encoding="utf-8-sig",newline="") as h:
        return list(csv.DictReader(h))

def cell_name(p,rows):
    s=str(p)
    for tag in ("GOLD23","GOLD24","GOLD25","BTC25","SILVER25","CADJPY25"):
        if tag in s:return tag
    for r in rows:
        if r.get("event")=="EA_START":
            x=kv(r.get("detail",""))
            sym=x.get("symbol")
            if sym:return sym
    return p.stem

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("paths",nargs="+")
    a=ap.parse_args()

    roots=expand(a.paths)
    csvs=[]
    manifests=[]
    for root in roots:
        csvs += list(root.rglob("*.csv"))
        manifests += list(root.rglob("batch_manifest.json"))

    dirty=set()
    for mp in manifests:
        m=json.loads(mp.read_text(encoding="utf-8"))
        bid=m.get("batch_id","")
        cell=None
        for tag in ("GOLD23","GOLD24","GOLD25","BTC25","SILVER25","CADJPY25"):
            if tag in bid: cell=tag
        for run in m.get("runs",[]):
            integ=run.get("integrity",{})
            if cell and not integ.get("profitability_evidence_clean",False):
                dirty.add(cell)

    records=[]
    integrity_errors=[]

    for p in csvs:
        rows=read_csv(p)
        if not any(r.get("event","").startswith("D154F_") for r in rows):
            continue
        cell=cell_name(p,rows)
        root={}; sweep={}; choch={}; fvg={}; fill={}; outcome={}
        for r in rows:
            e=r.get("event",""); x=kv(r.get("detail",""))
            sid=x.get("scenario_id") or r.get("object_id","")
            if not sid: continue
            if e=="D154F_ROOT_CONTACT": root[sid]=x
            elif e=="D154F_SWEEP_ACCEPTED": sweep[sid]=x
            elif e=="D154F_CHOCH_LINEAGE": choch[sid]=x
            elif e=="D154F_FVG_LINEAGE": fvg[sid]=x
            elif e=="D154F_LINEAGE_FILL":
                if sid in fill: integrity_errors.append(f"{cell}: duplicate fill {sid}")
                fill[sid]=x
            elif e=="D154F_PRIMARY_OUTCOME":
                if sid in outcome: integrity_errors.append(f"{cell}: duplicate outcome {sid}")
                outcome[sid]=x

        for sid,fi in fill.items():
            if sid not in root: integrity_errors.append(f"{cell}: fill without root {sid}")
            if sid not in sweep: integrity_errors.append(f"{cell}: fill without sweep {sid}")
            if sid not in choch: integrity_errors.append(f"{cell}: fill without choch {sid}")
            if sid not in fvg: integrity_errors.append(f"{cell}: fill without fvg {sid}")
            if sid not in outcome: integrity_errors.append(f"{cell}: fill without primary outcome {sid}")

            sw=sweep.get(sid,{})
            ch=choch.get(sid,{})
            fg=fvg.get(sid,{})
            ou=outcome.get(sid,{})
            records.append({
                "cell":cell,
                "clean":cell not in dirty,
                "sid":sid,
                "direction":fi.get("direction","NA"),
                "source_tf":fi.get("source_tf","NA"),
                "lineage":fi.get("lineage_class",ch.get("lineage_class","UNKNOWN")),
                "sweep_state":fi.get("sweep_pre_state_class",sw.get("sweep_pre_state_class","UNKNOWN")),
                "outcome":ou.get("outcome","UNKNOWN"),
                "matched":int(float(fi.get("sweep_matched_count","0") or 0)),
                "multi":fi.get("multi_pool_identity","false")=="true",
                "c1_pre":fi.get("fvg_c1_before_sweep_bar","false")=="true",
                "c1_sweep":fi.get("fvg_c1_is_sweep_bar","false")=="true",
                "contact_events":int(float(fi.get("contact_to_sweep_structure_events","0") or 0)),
                "intermediate_events":int(float(fi.get("intermediate_structure_events_after_sweep","0") or 0)),
                "owner_changed":fi.get("owner_or_trend_changed_contact_to_sweep","false")=="true",
                "min_age":num(sw.get("min_pool_age_s")),
                "max_age":num(sw.get("max_pool_age_s")),
            })

    print("D154F EVENT INTEGRITY:","PASS" if not integrity_errors else "FAIL")
    for e in integrity_errors[:30]: print(" -",e)
    print("Dirty cells excluded from inference:",", ".join(sorted(dirty)) if dirty else "NONE")
    if integrity_errors:return 2
    if not records:
        print("No D154F filled records found.")
        return 1

    clean=[r for r in records if r["clean"] and r["outcome"] in ("PLUS_1R","SL_FIRST")]
    print("Clean resolved fills:",len(clean))

    def group(title,keyfn,subset=None):
        rs=clean if subset is None else subset
        groups=defaultdict(list)
        for r in rs: groups[keyfn(r)].append(r)
        print(f"\n== {title} ==")
        print(f"{'group':42s} {'n':>5s} {'+1R':>5s} {'SL':>5s} {'rate':>9s}")
        for k,g in sorted(groups.items(),key=lambda x:str(x[0])):
            plus=sum(r["outcome"]=="PLUS_1R" for r in g)
            sl=sum(r["outcome"]=="SL_FIRST" for r in g)
            print(f"{str(k):42s} {len(g):5d} {plus:5d} {sl:5d} {pct(plus,plus+sl):>9s}")

    group("PRIMARY: CHOCH LINEAGE CLASS",lambda r:r["lineage"])
    group("PRIMARY BY DIRECTION",lambda r:f'{r["direction"]}|{r["lineage"]}')
    group("SOURCE TF x LINEAGE",lambda r:f'{r["source_tf"]}|{r["lineage"]}')
    group("SWEEP-TIME M1 STATE",lambda r:r["sweep_state"])
    group("SWEEP IDENTITY MULTIPLICITY",lambda r:"MULTI_POOL" if r["multi"] else "SINGLE_POOL")
    group("FVG CANDLE1 RELATION",lambda r:"C1_PRE_SWEEP" if r["c1_pre"] else ("C1_IS_SWEEP_BAR" if r["c1_sweep"] else "C1_AFTER_SWEEP"))

    direct=[r for r in clean if r["lineage"]=="DIRECT_FROZEN_BREAK"]
    non=[r for r in clean if r["lineage"]!="DIRECT_FROZEN_BREAK"]
    print("\n== PRE-REGISTERED DISCOVERY CONTRAST ==")
    for name,rs in (("DIRECT_FROZEN_BREAK",direct),("ALL_NON_DIRECT",non)):
        plus=sum(r["outcome"]=="PLUS_1R" for r in rs)
        sl=sum(r["outcome"]=="SL_FIRST" for r in rs)
        print(f"{name:24s} n={len(rs):4d} +1R={plus:4d} SL={sl:4d} rate={pct(plus,plus+sl)}")

    print("\n== DESCRIPTIVE PATH COMPLEXITY (NO THRESHOLD PROMOTION) ==")
    for name,rs in (("DIRECT",direct),("NON_DIRECT",non)):
        if not rs: continue
        ce=[r["contact_events"] for r in rs]
        ie=[r["intermediate_events"] for r in rs]
        ma=[r["matched"] for r in rs]
        ages=[r["max_age"] for r in rs if r["max_age"] is not None]
        print(
            f"{name:10s} n={len(rs):4d} "
            f"median_contact_to_sweep_structure_events={median(ce):.1f} "
            f"median_intermediate_events_after_sweep={median(ie):.1f} "
            f"median_matched_sweep_pools={median(ma):.1f} "
            f"median_oldest_pool_age_min={('NA' if not ages else f'{median(ages)/60:.1f}')}"
        )

    print("\n== DECISION BOUNDARY ==")
    print("- Discovery hypothesis is fixed before GOLD23: DIRECT_FROZEN_BREAK should have higher Fill->+1R survival than non-direct lineage.")
    print("- Do not optimize event-count, pool-age, FVG timing, or matched-pool thresholds on GOLD23.")
    print("- Only if the structural relationship is meaningful should the unchanged definition be tested on GOLD24/GOLD25 and BTC/SILVER/CADJPY 2025.")
    print("- If validation reverses, reject SAME_REACTION_LINEAGE as a universal Entry rule; do not rescue with thresholds.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
