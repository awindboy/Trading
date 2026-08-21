#!/usr/bin/env python3
"""Summarize one D-149 SP/EM unified event ledger."""
from __future__ import annotations
import csv
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

KV=re.compile(r"([A-Za-z0-9_]+)=(.*?)(?=\s+[A-Za-z0-9_]+=|$)")
DT_FMT="%Y.%m.%d %H:%M:%S"

def kv(s): return {k:v.strip() for k,v in KV.findall(s or "")}
def fnum(d,k,default=None):
    try: return float(d[k])
    except Exception: return default
def dt(v):
    try: return datetime.strptime(v,DT_FMT)
    except Exception: return None
def pct(n,d): return 0.0 if not d else 100.0*n/d
def mean(xs): return None if not xs else statistics.mean(xs)
def fmt(x,digits=4): return "NA" if x is None else f"{x:.{digits}f}"

def read(path: Path):
    data={
        "starts":[],"stops":[],"ea_stops":[],"plans":{},"fills":{},"closes":{},
        "sp_state":{},"sp_partial":defaultdict(list),"sp_be":defaultdict(list),
        "em_block":defaultdict(list),"em_auth":defaultdict(list),"em_result":defaultdict(list),
        "events":Counter(),
    }
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        for row in r:
            ev=(row.get("event") or "").strip(); d=kv(row.get("detail") or "")
            oid=(row.get("object_id") or "").strip(); sid=d.get("scenario_id",oid)
            data["events"][ev]+=1
            if ev=="D149_RESEARCH_START": data["starts"].append(d)
            elif ev=="D149_RESEARCH_STOP": data["stops"].append(d)
            elif ev=="EA_STOP": data["ea_stops"].append(d)
            elif ev=="SCENARIO_PLANNED" and sid: data["plans"][sid]=d
            elif ev=="POSITION_FILLED" and sid: data["fills"][sid]=(d,row)
            elif ev=="POSITION_CLOSED" and sid: data["closes"][sid]=(d,row)
            elif ev=="D149_SP_STATE_FROZEN" and sid: data["sp_state"][sid]=d
            elif ev.startswith("D149_SP_PARTIAL_") and sid: data["sp_partial"][sid].append((ev,d))
            elif ev.startswith("D149_SP_BE_") and sid: data["sp_be"][sid].append((ev,d))
            elif ev=="D149_EM_BLOCKED" and sid: data["em_block"][sid].append(d)
            elif ev=="D149_EM_AUTHORIZED" and sid: data["em_auth"][sid].append(d)
            elif ev in {"D149_EM_RESULT","D149_EM_RESULT_SKIPPED"} and sid: data["em_result"][sid].append((ev,d))
    return data

def build_records(data):
    records=[]; bad=[]
    for sid,(cd,crow) in data["closes"].items():
        fd=data["fills"].get(sid,({},{}))[0]
        risk=fnum(cd,"actual_fill_risk_money") or fnum(fd,"actual_fill_risk_money")
        net=fnum(cd,"realized_net_money")
        gross=fnum(cd,"exit_profit")
        if risk is None or risk<=0 or net is None:
            bad.append(sid); continue
        p=data["plans"].get(sid,{})
        exit_at=dt(cd.get("exit_at","")) or dt(crow.get("available_at","")) or dt(crow.get("observed_at",""))
        records.append({
            "sid":sid,"scope":p.get("scope","UNKNOWN"),"dir":p.get("direction","UNKNOWN"),
            "net_r":net/risk,"gross_r":None if gross is None else gross/risk,"exit_at":exit_at,
            "sp":data["sp_state"].get(sid,{}).get("state","NONE"),
        })
    records.sort(key=lambda x:(x["exit_at"] or datetime.min,x["sid"]))
    return records,bad

def metrics(rows):
    rs=[x["net_r"] for x in rows]
    wins=[r for r in rs if r>0]; losses=[r for r in rs if r<0]; bes=[r for r in rs if r==0]
    cum=peak=maxdd=0.0; streak=maxstreak=0
    for r in rs:
        cum+=r; peak=max(peak,cum); maxdd=max(maxdd,peak-cum)
        if r<=0:
            streak+=1; maxstreak=max(maxstreak,streak)
        else: streak=0
    pos=sorted(wins,reverse=True); ps=sum(pos)
    return {
        "n":len(rs),"wins":len(wins),"bes":len(bes),"wr":pct(len(wins),len(rs)),
        "avgw":mean(wins),"avgl":mean(losses),"exp":mean(rs),"total":sum(rs) if rs else None,
        "dd":maxdd,"streak":maxstreak,"top1":None if not pos or ps<=0 else pos[0]/ps,
        "top3":None if not pos or ps<=0 else sum(pos[:3])/ps,
    }

def print_metrics(label,rows):
    m=metrics(rows)
    print(f"{label}: n={m['n']} wins={m['wins']} WR={m['wr']:.2f}% BE={m['bes']} "
          f"avg_win_R={fmt(m['avgw'])} avg_loss_R={fmt(m['avgl'])} expectancy_R={fmt(m['exp'])} "
          f"total_R={fmt(m['total'])} max_DD_R={m['dd']:.4f} longest_nonpositive_streak={m['streak']} "
          f"top1_winner_share={fmt(m['top1'])} top3_winner_share={fmt(m['top3'])}")

def main():
    if len(sys.argv)!=2:
        print("usage: summarize_d149_sp_em.py ledger.csv",file=sys.stderr); return 2
    path=Path(sys.argv[1]); data=read(path); errors=[]
    if len(data["starts"])!=1: errors.append(f"D149_RESEARCH_START count={len(data['starts'])}")
    if len(data["stops"])>1: errors.append(f"D149_RESEARCH_STOP count={len(data['stops'])}")
    records,bad=build_records(data)
    if bad: errors.append(f"closed trades missing risk/net accounting={len(bad)}")
    blocked=set(data["em_block"])
    if blocked & set(data["fills"]): errors.append(f"EM-blocked scenarios later filled={len(blocked & set(data['fills']))}")
    unresolved=set(data["fills"])-set(data["closes"])

    start=data["starts"][0] if data["starts"] else {}
    exit_mode=start.get("exit_mode","UNKNOWN"); em_mode=start.get("em_mode","UNKNOWN")
    print("D149 LEDGER INTEGRITY:","PASS" if not errors else "FAIL")
    print(f"file={path}")
    print(f"exit_mode={exit_mode} em_mode={em_mode}")
    print(f"fills={len(data['fills'])} closes={len(data['closes'])} unresolved={len(unresolved)} blocked_scenarios={len(blocked)}")
    for e in errors: print("ERROR:",e)
    if data["ea_stops"]:
        es=data["ea_stops"][-1]
        print(f"execution_divergences={es.get('execution_divergences','NA')} cancel_rejected={es.get('cancel_rejected','NA')}")

    print_metrics("ALL",records)
    cont=[x for x in records if x["scope"]=="EXTERNAL_CONTINUATION"]
    rev=[x for x in records if x["scope"]=="EXTERNAL_REVERSAL"]
    if cont: print_metrics("CONTINUATION",cont)
    if rev: print_metrics("REVERSAL",rev)
    for d in ["LONG","SHORT"]:
        rr=[x for x in cont if x["dir"]==d]
        if rr: print_metrics(f"CONT_{d}",rr)

    if exit_mode=="SMART_PARTIAL" or data["sp_state"]:
        print("SP:")
        states=Counter(x.get("state","UNKNOWN") for x in data["sp_state"].values())
        for k,v in states.items(): print(f"  state_{k}={v}")
        print(f"  partial_accepted={data['events']['D149_SP_PARTIAL_ACCEPTED']} partial_rejected={data['events']['D149_SP_PARTIAL_REJECTED']} partial_infeasible={data['events']['D149_SP_PARTIAL_INFEASIBLE']}")
        print(f"  be_moved={data['events']['D149_SP_BE_MOVED']} be_rejected={data['events']['D149_SP_BE_REJECTED']} be_already_protected={data['events']['D149_SP_BE_ALREADY_PROTECTED']}")
        for state in ["STRONG_RUNNER","DEFAULT"]:
            rr=[x for x in records if x["sp"]==state]
            if rr: print_metrics(f"SP_{state}",rr)

    if em_mode=="CAUSAL_EPISODE_V1" or blocked or data["em_result"]:
        print("EM:")
        reasons=Counter(d.get("reason","UNKNOWN") for rows in data["em_block"].values() for d in rows)
        for k,v in reasons.items(): print(f"  blocked_{k}={v}")
        print(f"  authorized={data['events']['D149_EM_AUTHORIZED']} refresh_events={data['events']['D149_EM_STRUCTURE_REFRESH']} results={data['events']['D149_EM_RESULT']} result_skipped={data['events']['D149_EM_RESULT_SKIPPED']}")
        if data["stops"]:
            s=data["stops"][-1]
            keys=["em_blocks_concurrent","em_blocks_no_refresh","em_blocks_hard_lock","em_refresh_retries","em_episode_wins","em_episode_losses","em_hard_locks"]
            print("  stop_counters="+" ".join(f"{k}={s.get(k,'NA')}" for k in keys))

    if unresolved: print("unresolved_scenarios="+",".join(sorted(unresolved)[:20]))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
