#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from collections import defaultdict
from pathlib import Path
from statistics import median

KV=re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")

def detail(s):
    return {m.group(1):m.group(2) for m in KV.finditer(s or "")}

def read(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def discover(items):
    out=[]
    for x in items:
        p=Path(x)
        if p.is_dir(): out.extend(sorted(p.rglob("*.csv")))
        elif p.suffix.lower()==".csv": out.append(p)
    return out

def market(rows,fallback):
    for r in rows:
        if r.get("event")=="EA_START":
            d=detail(r.get("detail",""))
            if d.get("symbol"): return d["symbol"]
    return fallback

def pct(k,n):
    return "NA" if not n else f"{100*k/n:.1f}%"

def fnum(x,default=0.0):
    try:return float(x)
    except:return default

def main():
    ap=argparse.ArgumentParser(description="Analyze D-154B delayed confirmation shadow.")
    ap.add_argument("paths",nargs="+")
    a=ap.parse_args()

    files=discover(a.paths)
    records=[]; errors=[]
    for p in files:
        rows=read(p)
        if not any(r.get("event","").startswith("D154B_") for r in rows):
            continue
        m=market(rows,p.stem)
        fills={}; first={}; armed={}; infeasible={}; primary={}; terminal={}
        for r in rows:
            e=r.get("event",""); d=detail(r.get("detail",""))
            sid=d.get("scenario_id") or r.get("object_id","")
            if not sid: continue
            if e=="D154B_TRANSITION_FILL": fills[sid]=d
            elif e=="D154B_FIRST_INITIAL_BOS": first[sid]=d
            elif e=="D154B_CANDIDATE_ARMED": armed[sid]=d
            elif e=="D154B_CANDIDATE_INFEASIBLE": infeasible[sid]=d
            elif e=="D154B_PRIMARY_REFERENCE": primary[sid]=d
            elif e=="D154B_SHADOW_TERMINAL": terminal[sid]=d

        for sid,f in fills.items():
            if sid not in primary:
                errors.append(f"{m}: missing primary reference {sid}")
                continue
            pr=primary[sid]
            fi=first.get(sid,{})
            relation=fi.get("relation","NONE")
            ar=armed.get(sid)
            inf=infeasible.get(sid)
            te=terminal.get(sid)
            if ar and not te:
                errors.append(f"{m}: armed candidate missing shadow terminal {sid}")
            if te and not ar:
                errors.append(f"{m}: shadow terminal without armed candidate {sid}")
            records.append({
                "market":m,"sid":sid,"direction":f.get("direction","NA"),
                "primary":pr.get("primary_outcome","UNKNOWN"),
                "relation":relation,
                "armed":ar is not None,
                "infeasible":inf.get("reason","") if inf else "",
                "shadow":te.get("outcome","") if te else "",
                "confirm_r":fnum(ar.get("confirmation_r_from_original")) if ar else None,
                "struct_tp_r":fnum(ar.get("structural_tp_r")) if ar else None,
                "spread":fnum(ar.get("spread")) if ar else None,
                "minutes":fnum(fi.get("minutes_after_fill")) if fi else None,
                "mfe":fnum(te.get("shadow_mfe_r")) if te else None,
                "mae":fnum(te.get("shadow_mae_r")) if te else None,
                "map_loss":(te.get("map_support_lost")=="true") if te else False,
            })

    print("D154B EVENT INTEGRITY:","PASS" if not errors else "FAIL")
    for e in errors[:30]: print(" -",e)
    if errors: return 2
    if not records:
        print("No D154B transition-fill records found.")
        return 1

    def summarize(groups,title,outcome_field="primary",positive="PLUS_1R"):
        print(f"\n== {title} ==")
        print(f"{'group':42s} {'n':>5s} {'success':>8s} {'rate':>9s}")
        for k,rs in sorted(groups.items()):
            resolved=[r for r in rs if r[outcome_field] in ("PLUS_1R","SL_FIRST","ORIGINAL_SL")]
            ok=sum(r[outcome_field]==positive for r in resolved)
            print(f"{k:42s} {len(rs):5d} {ok:8d} {pct(ok,len(resolved)):>9s}")

    by_market=defaultdict(list)
    by_md=defaultdict(list)
    by_rel=defaultdict(list)
    by_mrel=defaultdict(list)
    for r in records:
        by_market[r["market"]].append(r)
        by_md[f'{r["market"]}|{r["direction"]}'].append(r)
        by_rel[r["relation"]].append(r)
        by_mrel[f'{r["market"]}|{r["relation"]}'].append(r)

    print(f"\nTransition-at-Fill population: {len(records)}")
    summarize(by_market,"Original primary survival by market")
    summarize(by_md,"Original primary survival by market x direction")
    summarize(by_rel,"Original primary survival by first post-Fill INITIAL_BOS")
    summarize(by_mrel,"Original primary survival by market x first confirmation")

    candidates=[r for r in records if r["armed"]]
    print("\n== Same-direction confirmation candidate geometry ==")
    print(f"armed={len(candidates)} | infeasible_same_confirmation={sum(bool(r['infeasible']) for r in records if r['relation']=='SAME_DIR')}")
    for m in sorted(set(r["market"] for r in candidates)):
        rs=[r for r in candidates if r["market"]==m]
        print(
            f"{m}: n={len(rs)} "
            f"median_confirmation_original_R={median(r['confirm_r'] for r in rs):.3f} "
            f"median_structural_TP_R={median(r['struct_tp_r'] for r in rs):.3f} "
            f"median_minutes_after_fill={median(r['minutes'] for r in rs):.1f}"
        )

    shadow_groups=defaultdict(list)
    shadow_md=defaultdict(list)
    for r in candidates:
        shadow_groups[r["market"]].append(r)
        shadow_md[f'{r["market"]}|{r["direction"]}'].append(r)

    print("\n== Delayed confirmation shadow: +1R from NEW executable entry vs ORIGINAL SL ==")
    print(f"{'group':32s} {'n':>5s} {'+1R':>5s} {'SL':>5s} {'cens':>5s} {'survival':>9s}")
    for groups in (shadow_groups,shadow_md):
        for k,rs in sorted(groups.items()):
            plus=sum(r["shadow"]=="PLUS_1R" for r in rs)
            sl=sum(r["shadow"]=="ORIGINAL_SL" for r in rs)
            ce=sum(r["shadow"]=="RIGHT_CENSORED" for r in rs)
            print(f"{k:32s} {len(rs):5d} {plus:5d} {sl:5d} {ce:5d} {pct(plus,plus+sl):>9s}")
        print()

    print("== Retention / trade-off ==")
    total_primary_wins=sum(r["primary"]=="PLUS_1R" for r in records)
    same_primary=[r for r in records if r["relation"]=="SAME_DIR"]
    opp_primary=[r for r in records if r["relation"]=="OPPOSITE_DIR"]
    none_primary=[r for r in records if r["relation"]=="NONE"]
    print(f"transition primary winners total: {total_primary_wins}/{len(records)}")
    print(f"same-dir first confirmation: {sum(r['primary']=='PLUS_1R' for r in same_primary)}/{len(same_primary)} original +1R")
    print(f"opposite-dir first confirmation: {sum(r['primary']=='PLUS_1R' for r in opp_primary)}/{len(opp_primary)} original +1R (would be rejected by a direction gate)")
    print(f"no confirmation before primary terminal: {sum(r['primary']=='PLUS_1R' for r in none_primary)}/{len(none_primary)} original +1R")
    if candidates:
        print(f"armed candidates whose NEW shadow also reached +1R: {sum(r['shadow']=='PLUS_1R' for r in candidates)}/{len(candidates)}")

    print("\n== Causal interpretation boundary ==")
    print("- This is a delayed-entry shadow test, not a strategy rule.")
    print("- Candidate entry is the first executable tick after causal same-direction INITIAL_BOS close.")
    print("- Stop is the original normalized SL; +1R is recomputed from the later entry.")
    print("- Structural TP must still provide >=1R from the later entry; no threshold optimization is performed.")
    print("- Confirmation direction is correlated with favorable/adverse price progress, so success is not automatically proof of an independent structure edge.")
    print("- Promotion requires relation consistency outside GOLD25/BTC25 and a later real-execution variant with costs.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
