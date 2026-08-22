#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from collections import defaultdict
from pathlib import Path
from statistics import median

KV=re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")

def d(s): return {m.group(1):m.group(2) for m in KV.finditer(s or "")}
def f(x):
    try:return float(x)
    except:return None
def pct(k,n): return "NA" if not n else f"{100*k/n:.1f}%"

def read(p):
    with p.open("r",encoding="utf-8-sig",newline="") as h:
        return list(csv.DictReader(h))

def discover(xs):
    out=[]
    for x in xs:
        p=Path(x)
        if p.is_dir(): out += sorted(p.rglob("*.csv"))
        elif p.suffix.lower()==".csv": out.append(p)
    return out

def market(rows,fallback):
    for r in rows:
        if r.get("event")=="EA_START":
            x=d(r.get("detail",""))
            if x.get("symbol"): return x["symbol"]
    return fallback

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("paths",nargs="+")
    a=ap.parse_args()

    rec=[]; errors=[]
    for p in discover(a.paths):
        rows=read(p)
        if not any(r.get("event","").startswith("D154C_") for r in rows):
            continue
        m=market(rows,p.stem)
        fills={}; initial={}; fvg={}; infeas={}; sf={}; pre={}; prim_after={}; term={}; amb={}
        for r in rows:
            e=r.get("event",""); x=d(r.get("detail",""))
            sid=x.get("scenario_id") or r.get("object_id","")
            if not sid: continue
            if e=="D154C_TRANSITION_FILL": fills[sid]=x
            elif e=="D154C_FIRST_INITIAL_BOS": initial[sid]=x
            elif e=="D154C_FVG_SELECTED": fvg[sid]=x
            elif e=="D154C_FVG_INFEASIBLE": infeas[sid]=x
            elif e=="D154C_RETEST_FILL": sf[sid]=x
            elif e=="D154C_PREENTRY_TERMINAL": pre[sid]=x
            elif e=="D154C_PRIMARY_REFERENCE_AFTER_SHADOW_FILL": prim_after[sid]=x
            elif e=="D154C_SHADOW_TERMINAL": term[sid]=x
            elif e=="D154C_RETEST_AMBIGUOUS": amb[sid]=x

        for sid,fi in fills.items():
            ini=initial.get(sid,{})
            relation=ini.get("relation","NONE")
            fg=fvg.get(sid)
            inf=infeas.get(sid)
            sh=sf.get(sid)
            te=term.get(sid)
            pr=pre.get(sid) or prim_after.get(sid)
            if not pr:
                errors.append(f"{m}: missing primary reference {sid}")
            if sh and not te:
                errors.append(f"{m}: shadow fill without terminal {sid}")
            if te and not sh:
                errors.append(f"{m}: shadow terminal without fill {sid}")
            primary=(pr or {}).get("primary_outcome","UNKNOWN")
            rec.append({
                "market":m,"sid":sid,"direction":fi.get("direction","NA"),
                "relation":relation,"primary":primary,
                "fvg":bool(fg),"infeasible":bool(inf),"shadow_fill":bool(sh),
                "ambiguous":sid in amb,"shadow":(te or {}).get("outcome",""),
                "entry_r":f((fg or {}).get("entry_r_from_original")),
                "pullback_r":f((fg or {}).get("pullback_from_confirmation_r")),
                "struct_tp_r":f((fg or {}).get("structural_tp_r")),
                "fvg_retest_min":f((sh or {}).get("minutes_fvg_to_retest")),
            })

    print("D154C EVENT INTEGRITY:","PASS" if not errors else "FAIL")
    for e in errors[:30]: print(" -",e)
    if errors:return 2
    if not rec:
        print("No D154C records found.")
        return 1

    def table(key,title,filter_fn=lambda r: True):
        groups=defaultdict(list)
        for r in rec:
            if filter_fn(r): groups[key(r)].append(r)
        print(f"\n== {title} ==")
        print(f"{'group':36s} {'n':>5s} {'primary+1':>9s} {'rate':>9s}")
        for k,rs in sorted(groups.items()):
            resolved=[r for r in rs if r["primary"] in ("PLUS_1R","SL_FIRST")]
            ok=sum(r["primary"]=="PLUS_1R" for r in resolved)
            print(f"{k:36s} {len(rs):5d} {ok:9d} {pct(ok,len(resolved)):>9s}")

    print(f"\nTransition-at-Fill population: {len(rec)}")
    table(lambda r:r["market"],"Primary survival by market")
    table(lambda r:f'{r["market"]}|{r["direction"]}',"Primary survival by market x direction")
    table(lambda r:r["relation"],"Primary survival by first INITIAL_BOS")

    same=[r for r in rec if r["relation"]=="SAME_DIR"]
    print("\n== Same-direction confirmation source availability ==")
    for m in sorted(set(r["market"] for r in same)):
        rs=[r for r in same if r["market"]==m]
        print(
            f"{m}: same_confirm={len(rs)} "
            f"first_fvg_feasible={sum(r['fvg'] for r in rs)} "
            f"first_fvg_infeasible={sum(r['infeasible'] for r in rs)} "
            f"retest_fills={sum(r['shadow_fill'] for r in rs)} "
            f"ambiguous={sum(r['ambiguous'] for r in rs)}"
        )

    fills=[r for r in rec if r["shadow_fill"]]
    print("\n== D154C shadow Fill -> +1R vs original SL ==")
    print(f"{'group':32s} {'fills':>6s} {'+1R':>5s} {'SL':>5s} {'cens':>5s} {'survival':>9s}")
    groups=defaultdict(list)
    for r in fills: groups[r["market"]].append(r)
    for r in fills: groups[f'{r["market"]}|{r["direction"]}'].append(r)
    for k,rs in sorted(groups.items()):
        plus=sum(r["shadow"]=="PLUS_1R" for r in rs)
        sl=sum(r["shadow"]=="ORIGINAL_SL" for r in rs)
        ce=sum(r["shadow"]=="RIGHT_CENSORED" for r in rs)
        print(f"{k:32s} {len(rs):6d} {plus:5d} {sl:5d} {ce:5d} {pct(plus,plus+sl):>9s}")

    print("\n== Pairwise baseline vs D154C among actual shadow fills ==")
    cells=defaultdict(int)
    for r in fills:
        cells[(r["primary"],r["shadow"])]+=1
    for k,v in sorted(cells.items()):
        print(f"{k[0]:>10s} -> {k[1]:<14s}: {v}")

    vals=[r for r in rec if r["fvg"]]
    if vals:
        print("\n== Geometry of feasible first post-confirmation FVG ==")
        for m in sorted(set(r["market"] for r in vals)):
            rs=[r for r in vals if r["market"]==m]
            def med(field):
                x=[r[field] for r in rs if r[field] is not None]
                return "NA" if not x else f"{median(x):.3f}"
            print(
                f"{m}: n={len(rs)} "
                f"median_entry_original_R={med('entry_r')} "
                f"median_pullback_recovered_R={med('pullback_r')} "
                f"median_structural_TP_R={med('struct_tp_r')}"
            )

    print("\n== Interpretation boundaries ==")
    print("- First same-direction INITIAL_BOS is a state confirmation, not an Entry.")
    print("- D154C freezes the first same-direction FVG whose middle/displacement candle begins after confirmation.")
    print("- Entry is only the first executable retest of that FVG proximal edge.")
    print("- Original normalized SL and frozen structural TP are unchanged.")
    print("- If primary +1R/SL happens before retest, no delayed shadow Entry is backfilled.")
    print("- Post-SL re-entry and second-FVG retries are excluded.")
    print("- Cross-market/direction reversal rejects universal promotion; no threshold rescue.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
