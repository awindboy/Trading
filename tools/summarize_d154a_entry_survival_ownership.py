#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, re
from collections import defaultdict
from pathlib import Path

KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")

def parse_detail(detail):
    return {m.group(1): m.group(2) for m in KV_RE.finditer(detail or "")}

def truth(v):
    return (v or "").lower() == "true"

def read_ledger(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def discover_csvs(items):
    out=[]
    for item in items:
        p=Path(item)
        if p.is_dir(): out.extend(sorted(p.rglob("*.csv")))
        elif p.suffix.lower()==".csv": out.append(p)
    seen=set(); uniq=[]
    for p in out:
        rp=p.resolve()
        if rp not in seen:
            seen.add(rp); uniq.append(p)
    return uniq

def pct(n,d):
    return "NA" if d==0 else f"{100*n/d:.1f}%"

def market_from_rows(rows,fallback):
    for r in rows:
        if r.get("event")=="EA_START":
            d=parse_detail(r.get("detail",""))
            if d.get("symbol"): return d["symbol"]
    return fallback

def first_owner_path(fill,outcome):
    fill_s=int(fill.get("fill_at_s","0") or 0)
    term_s=int(outcome.get("terminal_at_s","0") or 0)
    same=int(outcome.get("first_same_initial_at_s","0") or 0)
    opp=int(outcome.get("first_opposite_initial_at_s","0") or 0)
    cand=[]
    if same>0 and same<=term_s: cand.append((same,"SAME_DIR_INITIAL_BOS"))
    if opp>0 and opp<=term_s: cand.append((opp,"OPPOSITE_DIR_INITIAL_BOS"))
    if not cand: return "NO_INITIAL_BOS_BEFORE_PRIMARY_TERMINAL"
    cand.sort()
    when,label=cand[0]
    return label+("_BEFORE_FILL" if when<=fill_s else "_AFTER_FILL")

def summarize_group(records,key_fn,title):
    groups=defaultdict(list)
    for r in records: groups[str(key_fn(r))].append(r)
    print(f"\n== {title} ==")
    print(f"{'group':42s} {'n':>5s} {'+1R':>5s} {'SL':>5s} {'cens':>5s} {'+1R rate resolved':>18s}")
    for k in sorted(groups):
        rs=groups[k]
        plus=sum(x["outcome"]=="PLUS_1R" for x in rs)
        sl=sum(x["outcome"]=="SL_FIRST" for x in rs)
        cens=sum(x["outcome"].startswith("RIGHT_CENSORED") for x in rs)
        print(f"{k:42s} {len(rs):5d} {plus:5d} {sl:5d} {cens:5d} {pct(plus,plus+sl):>18s}")

def main():
    ap=argparse.ArgumentParser(description="Summarize D-154A M1 ownership completion and post-SL source succession.")
    ap.add_argument("paths",nargs="+",help="D154A ledger CSV(s) or directories")
    args=ap.parse_args()
    files=discover_csvs(args.paths)
    if not files: raise SystemExit("No CSV ledgers found.")

    records=[]; recovery_records=[]; errors=[]
    for path in files:
        rows=read_ledger(path)
        if not any(r.get("event","").startswith("D154A_") for r in rows): continue
        market=market_from_rows(rows,path.stem)
        fills={}; outcomes={}; recoveries={}
        d151_fills=set(); d151_plus=set(); d151_sl=set()
        for row in rows:
            event=row.get("event",""); d=parse_detail(row.get("detail",""))
            sid=d.get("scenario_id") or row.get("object_id","")
            if event=="D154A_FILL_OWNERSHIP" and sid:
                if sid in fills: errors.append(f"{market}: duplicate D154A fill {sid}")
                fills[sid]=d
            elif event=="D154A_PRIMARY_OUTCOME" and sid:
                if sid in outcomes: errors.append(f"{market}: duplicate D154A primary outcome {sid}")
                outcomes[sid]=d
            elif event=="D154A_RECOVERY_TERMINAL" and sid:
                if sid in recoveries: errors.append(f"{market}: duplicate D154A recovery terminal {sid}")
                recoveries[sid]=d
            elif event=="D151_FILL_SNAPSHOT" and sid: d151_fills.add(sid)
            elif event=="D151_PLUS_1R" and sid: d151_plus.add(sid)
            elif event=="D151_PRE1_FAILURE" and sid: d151_sl.add(sid)

        if d151_fills!=set(fills):
            if d151_fills-set(fills): errors.append(f"{market}: D154A missing {len(d151_fills-set(fills))} D151 fills")
            if set(fills)-d151_fills: errors.append(f"{market}: D154A has {len(set(fills)-d151_fills)} fills not in D151")

        for sid,fill in fills.items():
            out=outcomes.get(sid)
            if out is None:
                errors.append(f"{market}: missing D154A outcome {sid}"); continue
            outcome=out.get("outcome","UNKNOWN")
            if sid in d151_plus and outcome!="PLUS_1R": errors.append(f"{market}: D151 +1R but D154={outcome} {sid}")
            if sid in d151_sl and outcome!="SL_FIRST": errors.append(f"{market}: D151 SL-first but D154={outcome} {sid}")
            rec={
                "market":market,"scenario_id":sid,
                "direction":fill.get("direction",out.get("direction","NA")),
                "root_tf":fill.get("root_tf","NA"),
                "ownership":fill.get("m1_ownership_class","UNKNOWN"),
                "outcome":outcome,
                "first_owner_path":first_owner_path(fill,out),
                "same_initial_before_fill":truth(fill.get("same_initial_before_fill")),
                "opposite_initial_before_fill":truth(fill.get("opposite_initial_before_fill")),
                "same_bos_before_fill":truth(fill.get("same_bos_before_fill")),
                "opposite_pb_before_fill":truth(fill.get("opposite_pb_after_same_owner_before_fill")),
                "late_arm_at_fill":truth(fill.get("late_arm_at_fill")),
            }
            records.append(rec)
            if outcome=="SL_FIRST" and sid in recoveries:
                rr=dict(recoveries[sid]); rr.update({"market":market,"scenario_id":sid,"direction":rec["direction"],"root_tf":rec["root_tf"]})
                recovery_records.append(rr)

    print("D154A EVENT INTEGRITY:","PASS" if not errors else "FAIL")
    if errors:
        for e in errors[:30]: print(" -",e)
        return 2
    if not records:
        print("No D154A filled-trade records found."); return 1

    print(f"\nResolved/observed filled records: {len(records)}")
    late=sum(r["late_arm_at_fill"] for r in records)
    print(f"Late D154A tracker arms at Fill: {late}/{len(records)}")
    if late: print("WARNING: pre-Fill ownership-event coverage is incomplete for late-armed fills.")

    summarize_group(records,lambda r:r["market"],"Market")
    summarize_group(records,lambda r:f'{r["market"]}|{r["direction"]}',"Market x direction")
    summarize_group(records,lambda r:r["ownership"],"M1 ownership class at actual Fill")
    summarize_group(records,lambda r:f'{r["market"]}|{r["ownership"]}',"Market x M1 ownership at Fill")
    summarize_group(records,lambda r:r["first_owner_path"],"First M1 INITIAL_BOS after scenario CHoCH")
    summarize_group(records,lambda r:r["root_tf"],"Root timeframe")

    print("\n== Pre-Fill structural facts ==")
    facts=[
        ("same INITIAL_BOS before Fill","same_initial_before_fill"),
        ("opposite INITIAL_BOS before Fill","opposite_initial_before_fill"),
        ("same-direction BOS before Fill","same_bos_before_fill"),
        ("opposite PB after same owner before Fill","opposite_pb_before_fill"),
    ]
    for label,key in facts:
        for name,rs in (("YES",[r for r in records if r[key]]),("NO",[r for r in records if not r[key]])):
            plus=sum(r["outcome"]=="PLUS_1R" for r in rs); sl=sum(r["outcome"]=="SL_FIRST" for r in rs)
            print(f"{label:44s} {name:3s}: n={len(rs):4d} resolved={plus+sl:4d} +1R={plus:4d} SL={sl:4d} rate={pct(plus,plus+sl)}")

    print("\n== SL-first recovery / source succession ==")
    if not recovery_records:
        print("No D154A recovery-terminal rows.")
    else:
        def iv(d,k): return int(d.get(k,"0") or 0)
        for market in sorted(set(r["market"] for r in recovery_records)):
            for outcome in sorted(set(r.get("outcome","UNKNOWN") for r in recovery_records)):
                rs=[r for r in recovery_records if r["market"]==market and r.get("outcome")==outcome]
                if not rs: continue
                n=len(rs)
                metrics={
                    "same_root_fvg>0":sum(iv(r,"same_root_fvg")>0 for r in rs),
                    "same_root_fill>0":sum(iv(r,"same_root_fill")>0 for r in rs),
                    "other_root_fvg>0":sum(iv(r,"other_root_fvg")>0 for r in rs),
                    "other_root_fill>0":sum(iv(r,"other_root_fill")>0 for r in rs),
                    "new_root_after_failure_fvg>0":sum(iv(r,"new_root_after_failure_fvg")>0 for r in rs),
                    "new_root_after_failure_fill>0":sum(iv(r,"new_root_after_failure_fill")>0 for r in rs),
                }
                print(f"\n{market} | {outcome} | n={n}")
                for k,v in metrics.items(): print(f"  {k:34s} {v:4d}/{n:<4d} {pct(v,n)}")

    print("\n== Interpretation boundary ==")
    print("- No pooled threshold optimization is performed.")
    print("- Post-Fill M1 events cannot be backfilled into original Entry authorization.")
    print("- A useful post-Fill owner-completion relation only justifies a later D154B delayed-entry shadow test.")
    print("- New-Root succession counts only events before D151 recovery/map-support terminal.")
    print("- Relations that reverse across GOLD/BTC or LONG/SHORT are not universal promotion candidates.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
