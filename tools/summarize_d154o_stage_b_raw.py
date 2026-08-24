from __future__ import annotations
import argparse, csv, io, json, math, re, statistics, zipfile
from collections import Counter
from pathlib import Path

SYMBOLS=("GOLD#","XAUJPY#","XAUCNH#","BTCUSD#","XAUEUR#","GAUCNH#","GAUUSD#","USDJPY#",
         "GBPUSD#","SILVER#","EURUSD#","ETHUSD#")

def kv(s):
    return {m.group(1):m.group(2) for m in re.finditer(r"(\w+)=([^ ]+)",s or "")}
def num(d,k):
    try:
        x=float(d[k]); return x if math.isfinite(x) else None
    except Exception:
        return None
def med(xs):
    xs=[x for x in xs if x is not None and math.isfinite(x)]
    return statistics.median(xs) if xs else None

def load(zp):
    out={}
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            if n.endswith(".csv") and not n.startswith("repro/"):
                m=re.search(r"__([^_]+#)__2025\.csv$",n)
                if m:
                    out[m.group(1)]=list(csv.DictReader(io.StringIO(z.read(n).decode("utf-8-sig",errors="replace"))))
    return out

def analyze(sym,rows):
    ev=Counter(r.get("event","") for r in rows)
    fills={}; ks={}; pairs={}
    divergence=False
    for r in rows:
        d=kv(r.get("detail","")); sid=d.get("scenario_id",r.get("object_id",""))
        if r.get("event")=="D151_FILL_SNAPSHOT": fills[sid]=d
        elif r.get("event")=="D154K_CROSS_SCALE_SNAPSHOT": ks[sid]=d
        elif r.get("event")=="D154M_PAIR_OUTCOME": pairs[sid]=d
        if r.get("event")=="PENDING_CANCEL_REJECTED" or d.get("divergence")=="true":
            divergence=True
    if len(fills)!=len(ks) or len(fills)!=len(pairs):
        raise SystemExit(f"{sym}: D151/K/M mismatch {len(fills)}/{len(ks)}/{len(pairs)}")
    plus=sum(x.get("actual_outcome")=="PLUS_1R" for x in pairs.values())
    sl=sum(x.get("actual_outcome")=="SL_FIRST" for x in pairs.values())
    cens=sum(x.get("actual_outcome")=="RIGHT_CENSORED" for x in pairs.values())
    shp=sum(x.get("shadow_outcome")=="PLUS_1R" for x in pairs.values())
    shs=sum(x.get("shadow_outcome")=="SL_FIRST" for x in pairs.values())
    flips=sum(x.get("pair_class")=="ACTUAL_SL_TO_SHADOW_PLUS_1R" for x in pairs.values())
    dirs={sid:d.get("direction") for sid,d in fills.items()}
    def ds(direction):
        pp=[pairs[s] for s in pairs if dirs.get(s)==direction]
        a=sum(x.get("actual_outcome")=="PLUS_1R" for x in pp)
        b=sum(x.get("actual_outcome")=="SL_FIRST" for x in pp)
        return len(pp), a/(a+b) if a+b else None
    lf,lsv=ds("LONG"); sf,ssv=ds("SHORT")
    def vals(k): return [num(d,k) for d in ks.values()]
    return {
        "symbol":sym,"execution_valid":not divergence,"fills":len(fills),
        "plus1":plus,"sl_first":sl,"right_censored":cens,
        "survival":plus/(plus+sl) if plus+sl else None,
        "long_fills":lf,"long_survival":lsv,"short_fills":sf,"short_survival":ssv,
        "spread_over_reaction_tr":med(vals("spread_over_reaction_tr")),
        "spread_over_risk":med(vals("spread_over_risk")),
        "spread_over_selected_fvg":med(vals("spread_over_fvg")),
        "shadow_survival":shp/(shp+shs) if shp+shs else None,
        "sl_to_shadow_plus1":flips,
        "pending_cancel_rejected":ev["PENDING_CANCEL_REJECTED"],
        "partial_close_rejected":ev["D149_SP_V2_CLOSE_REJECTED"]+ev["D149_SP_PARTIAL_REJECTED"],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("zip")
    ap.add_argument("--out",default="D154O_STAGE_B_POSTPROCESS")
    a=ap.parse_args()
    rows=load(Path(a.zip))
    missing=[s for s in SYMBOLS if s not in rows]
    if missing: raise SystemExit("missing symbols: "+", ".join(missing))
    result=[analyze(s,rows[s]) for s in SYMBOLS]
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    (out/"summary.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    with (out/"summary.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]))
        w.writeheader(); w.writerows(result)
    for r in result:
        status="VALID" if r["execution_valid"] else "EXECUTION_INVALID"
        surv="NA" if r["survival"] is None else f"{100*r['survival']:.1f}%"
        print(f"{r['symbol']:10s} {status:17s} fills={r['fills']:3d} survival={surv:>6s}")
if __name__=="__main__":
    main()
