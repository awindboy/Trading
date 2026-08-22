#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,math,re,zipfile
from collections import defaultdict,Counter
from pathlib import Path

def kv(detail:str):
    out={}
    for tok in detail.split():
        if "=" in tok:
            k,v=tok.split("=",1); out[k]=v
    return out

def read_csv_bytes(data:bytes):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))

def process_zip_bytes(data:bytes,label:str,results:list):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        nested=[n for n in z.namelist() if n.lower().endswith(".zip")]
        if nested:
            for n in nested: process_zip_bytes(z.read(n),f"{label}/{n}",results)
            return
        manifests={}
        for n in z.namelist():
            if n.endswith("batch_manifest.json"):
                try: manifests[n]=json.loads(z.read(n).decode("utf-8"))
                except Exception: pass
        csvs=[n for n in z.namelist() if n.lower().endswith(".csv")]
        for n in csvs:
            clean=True; integrity_note="NO_MANIFEST"
            for m in manifests.values():
                for run in m.get("runs",[]):
                    if run.get("csv")==Path(n).name or run.get("csv")==n:
                        integ=run.get("integrity",{}); clean=bool(integ.get("profitability_evidence_clean",False)); integrity_note=str(integ)
            results.append((f"{label}/{n}",read_csv_bytes(z.read(n)),clean,integrity_note))

def load_inputs(paths):
    out=[]
    for p in paths:
        if p.suffix.lower()==".csv": out.append((str(p),read_csv_bytes(p.read_bytes()),True,"DIRECT_CSV"))
        elif p.suffix.lower()==".zip": process_zip_bytes(p.read_bytes(),p.name,out)
    return out

def rate(rows):
    wins=sum(1 for x in rows if x["outcome"]=="PLUS_1R"); losses=sum(1 for x in rows if x["outcome"]=="SL_FIRST")
    n=wins+losses; return n,wins,losses,(wins/n if n else float("nan"))

def fisher_two_sided(a,b,c,d):
    # table [[a,b],[c,d]]; fixed margins, exact two-sided by probability <= observed.
    r1=a+b; r2=c+d; c1=a+c; n=r1+r2
    if n==0: return float("nan")
    den=math.comb(n,r1)
    def p(x): return math.comb(c1,x)*math.comb(n-c1,r1-x)/den
    lo=max(0,r1-(n-c1)); hi=min(r1,c1); po=p(a)
    return min(1.0,sum(p(x) for x in range(lo,hi+1) if p(x)<=po+1e-15))

def pct(x): return "NA" if math.isnan(x) else f"{100*x:.1f}%"

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("paths",nargs="+",type=Path); args=ap.parse_args()
    datasets=load_inputs(args.paths)
    all_out=[]; contributor_classes=Counter(); integrity_bad=[]
    for label,rows,clean,note in datasets:
        if not clean:
            integrity_bad.append(label); continue
        outcomes=[]
        for r in rows:
            if r.get("event")=="D154G_CONTRIBUTOR_LINEAGE":
                contributor_classes[kv(r.get("detail","" )).get("lineage_class","MISSING")]+=1
            if r.get("event")!="D154G_PRIMARY_OUTCOME": continue
            x=kv(r.get("detail","")); outcome=x.get("outcome","")
            outcomes.append({
                "cell":label,"scenario":x.get("scenario_id",r.get("object_id","")),"direction":x.get("direction",""),"outcome":outcome,
                "stale":x.get("stale_prior_owner_present","false")=="true","class":x.get("fill_lineage_class",""),
                "missing":int(x.get("snapshot_missing_count","0") or 0),"contributors":int(x.get("contributor_count","0") or 0),
                "prior_same":int(x.get("prior_same_tf_same_dir_count","0") or 0),"prior_opp":int(x.get("prior_same_tf_opposite_dir_count","0") or 0),
                "bridge":int(x.get("m30_to_h1_bridge_count","0") or 0),
            })
        all_out.extend(outcomes)
        resolved=[x for x in outcomes if x["outcome"] in ("PLUS_1R","SL_FIRST")]
        n,w,l,rr=rate(resolved)
        print(f"CELL {label}: outcomes={len(outcomes)} resolved={n} +1R={w} SL={l} survival={pct(rr)} censored={sum(x['outcome']=='RIGHT_CENSORED' for x in outcomes)}")
    if integrity_bad:
        print("\nDIRTY CELLS EXCLUDED FROM INFERENCE:")
        for x in integrity_bad: print(" -",x)
    resolved=[x for x in all_out if x["outcome"] in ("PLUS_1R","SL_FIRST") and x["missing"]==0]
    stale=[x for x in resolved if x["stale"]]; clean=[x for x in resolved if not x["stale"]]
    ns,ws,ls,rs=rate(stale); nc,wc,lc,rc=rate(clean)
    print("\nPRIMARY PRE-REGISTERED COMPARISON")
    print(f"HAS_PRIOR_SAME_TF_OWNER: n={ns} +1R={ws} SL={ls} survival={pct(rs)}")
    print(f"NO_PRIOR_SAME_TF_OWNER:  n={nc} +1R={wc} SL={lc} survival={pct(rc)}")
    if ns and nc:
        print(f"Fisher two-sided p={fisher_two_sided(ws,ls,wc,lc):.6g}")
    print("\nBY DIRECTION")
    for d in ("LONG","SHORT"):
        for key,val in (("STALE",True),("NO_STALE",False)):
            r=[x for x in resolved if x["direction"]==d and x["stale"]==val]; n,w,l,rr=rate(r)
            print(f"{d:5s} {key:8s}: n={n} +1R={w} SL={l} survival={pct(rr)}")
    print("\nFILL LINEAGE CLASSES")
    for cls in sorted(set(x["class"] for x in resolved)):
        r=[x for x in resolved if x["class"]==cls]; n,w,l,rr=rate(r); print(f"{cls}: n={n} +1R={w} SL={l} survival={pct(rr)}")
    print("\nSINGLE VS MERGED (descriptive only)")
    for name,pred in (("SINGLE",lambda x:x["contributors"]<=1),("MERGED",lambda x:x["contributors"]>1)):
        r=[x for x in resolved if pred(x)]; n,w,l,rr=rate(r); print(f"{name}: n={n} +1R={w} SL={l} survival={pct(rr)}")
    print("\nCONTRIBUTOR LINEAGE COUNTS (descriptive; contributors are NOT independent trades)")
    for k,v in contributor_classes.most_common(): print(f"{k}: {v}")
    print("\nINTERPRETATION GUARD")
    print("- Primary exposure is presence of a prior owner on the same PLAN map timeframe, not Root age.")
    print("- M30_TO_H1_PROMOTION is explicitly not stale.")
    print("- RIGHT_CENSORED is never imputed.")
    print("- Contributor rows are descriptive only; fill is the independent outcome unit.")
    print("- Discovery thresholds, source-TF exceptions, and market-specific rescue rules are prohibited.")
    return 0
if __name__=="__main__": raise SystemExit(main())
