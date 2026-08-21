#!/usr/bin/env python3
"""Summarize and integrity-check one D-149 SP/EM V2 unified event ledger."""
from __future__ import annotations
import csv
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

KV = re.compile(r"([A-Za-z0-9_]+)=(.*?)(?=\s+[A-Za-z0-9_]+=|$)")
DT_FMT = "%Y.%m.%d %H:%M:%S"

def kv(s: str) -> dict[str,str]: return {k:v.strip() for k,v in KV.findall(s or "")}
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
    data = {
        "starts":[], "stops":[], "ea_stops":[], "plans":{}, "fills":{}, "closes":{},
        "sp_state":{}, "sp_v2_close":defaultdict(list), "sp_v2_be":defaultdict(list),
        "em_block":defaultdict(list), "em_v2_real1":defaultdict(list), "em_v2_failure":defaultdict(list),
        "quarantine_enter":[], "quarantine_release":[],
        "shadow_arm":defaultdict(list), "shadow_fill":defaultdict(list), "shadow_terminal":defaultdict(list),
        "events":Counter(), "rows":[],
    }
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        for row in r:
            ev=(row.get("event") or "").strip(); d=kv(row.get("detail") or "")
            oid=(row.get("object_id") or "").strip(); sid=d.get("scenario_id",oid)
            data["events"][ev]+=1; data["rows"].append((ev,d,row,sid))
            if ev=="D149_RESEARCH_START": data["starts"].append(d)
            elif ev=="D149_RESEARCH_STOP": data["stops"].append(d)
            elif ev=="EA_STOP": data["ea_stops"].append(d)
            elif ev=="SCENARIO_PLANNED" and sid: data["plans"][sid]=d
            elif ev=="POSITION_FILLED" and sid: data["fills"][sid]=(d,row)
            elif ev=="POSITION_CLOSED" and sid: data["closes"][sid]=(d,row)
            elif ev=="D149_SP_STATE_FROZEN" and sid: data["sp_state"][sid]=d
            elif ev.startswith("D149_SP_V2_CLOSE_") and sid: data["sp_v2_close"][sid].append((ev,d,row))
            elif ev.startswith("D149_SP_V2_COST_BE_") and sid: data["sp_v2_be"][sid].append((ev,d,row))
            elif ev=="D149_EM_BLOCKED" and sid: data["em_block"][sid].append(d)
            elif ev=="D149_EM_V2_REAL_PLUS_1R" and sid: data["em_v2_real1"][sid].append((d,row))
            elif ev=="D149_EM_V2_ENTRY_FAILURE" and sid: data["em_v2_failure"][sid].append((d,row))
            elif ev=="D149_EM_V2_QUARANTINE_ENTERED": data["quarantine_enter"].append((d,row))
            elif ev=="D149_EM_V2_QUARANTINE_RELEASED": data["quarantine_release"].append((d,row))
            elif ev=="D149_EM_V2_SHADOW_ARMED" and sid: data["shadow_arm"][sid].append((d,row))
            elif ev=="D149_EM_V2_SHADOW_FILLED" and sid: data["shadow_fill"][sid].append((d,row))
            elif ev in {"D149_EM_V2_SHADOW_PLUS_1R","D149_EM_V2_SHADOW_SL","D149_EM_V2_SHADOW_CANCELED","D149_EM_V2_SHADOW_CENSORED","D149_EM_V2_SHADOW_SUPERSEDED"} and sid:
                data["shadow_terminal"][sid].append((ev,d,row))
    return data

def build_records(data):
    records=[]; bad=[]
    for sid,(cd,crow) in data["closes"].items():
        fd=data["fills"].get(sid,({},{}))[0]
        risk=fnum(cd,"actual_fill_risk_money") or fnum(fd,"actual_fill_risk_money")
        net=fnum(cd,"realized_net_money"); gross=fnum(cd,"exit_profit")
        if risk is None or risk<=0 or net is None:
            bad.append(sid); continue
        p=data["plans"].get(sid,{})
        exit_at=dt(cd.get("exit_at","")) or dt(crow.get("available_at","")) or dt(crow.get("observed_at",""))
        records.append({
            "sid":sid,"scope":p.get("scope","UNKNOWN"),"dir":p.get("direction","UNKNOWN"),
            "net_r":net/risk,"gross_r":None if gross is None else gross/risk,"exit_at":exit_at,
            "sp":data["sp_state"].get(sid,{}).get("state","NONE"),
            "one_r":sid in data["em_v2_real1"], "entry_failure":sid in data["em_v2_failure"],
        })
    records.sort(key=lambda x:(x["exit_at"] or datetime.min,x["sid"]))
    return records,bad

def metrics(rows):
    rs=[x["net_r"] for x in rows]; wins=[r for r in rs if r>0]; losses=[r for r in rs if r<0]; bes=[r for r in rs if r==0]
    cum=peak=maxdd=0.0; streak=maxstreak=0
    for r in rs:
        cum+=r; peak=max(peak,cum); maxdd=max(maxdd,peak-cum)
        if r<=0: streak+=1; maxstreak=max(maxstreak,streak)
        else: streak=0
    pos=sorted(wins,reverse=True); ps=sum(pos)
    return {"n":len(rs),"wins":len(wins),"bes":len(bes),"wr":pct(len(wins),len(rs)),"avgw":mean(wins),"avgl":mean(losses),
            "exp":mean(rs),"total":sum(rs) if rs else None,"dd":maxdd,"streak":maxstreak,
            "top1":None if not pos or ps<=0 else pos[0]/ps,"top3":None if not pos or ps<=0 else sum(pos[:3])/ps}

def print_metrics(label,rows):
    m=metrics(rows)
    print(f"{label}: n={m['n']} wins={m['wins']} WR={m['wr']:.2f}% BE={m['bes']} "
          f"avg_win_R={fmt(m['avgw'])} avg_loss_R={fmt(m['avgl'])} expectancy_R={fmt(m['exp'])} "
          f"total_R={fmt(m['total'])} max_DD_R={m['dd']:.4f} longest_nonpositive_streak={m['streak']} "
          f"top1_winner_share={fmt(m['top1'])} top3_winner_share={fmt(m['top3'])}")

def integrity(data, records):
    errors=[]
    if len(data["starts"])!=1: errors.append(f"D149_RESEARCH_START count={len(data['starts'])}")
    if len(data["stops"])>1: errors.append(f"D149_RESEARCH_STOP count={len(data['stops'])}")
    start=data["starts"][0] if data["starts"] else {}
    if start.get("build") not in {None,"1.96R1L12"}: errors.append(f"unexpected D149 build={start.get('build')}")
    unresolved=set(data["fills"])-set(data["closes"])
    if unresolved: errors.append(f"unresolved filled positions={len(unresolved)}")
    blocked=set(data["em_block"])
    overlap=blocked & set(data["fills"])
    if overlap: errors.append(f"EM-blocked scenarios later filled={len(overlap)}")
    if set(data["em_v2_real1"]) & set(data["em_v2_failure"]):
        errors.append(f"same real scenario classified +1R and genuine failure={len(set(data['em_v2_real1']) & set(data['em_v2_failure']))}")
    for sid,arms in data["shadow_arm"].items():
        if len(arms)!=1: errors.append(f"shadow {sid} arm count={len(arms)}")
        terms=data["shadow_terminal"].get(sid,[])
        if len(terms)!=1: errors.append(f"shadow {sid} terminal count={len(terms)}")
        fills=data["shadow_fill"].get(sid,[])
        if len(fills)>1: errors.append(f"shadow {sid} fill count={len(fills)}")
        if terms and terms[0][0] in {"D149_EM_V2_SHADOW_PLUS_1R","D149_EM_V2_SHADOW_SL"} and len(fills)!=1:
            errors.append(f"shadow {sid} price terminal without exactly one shadow fill")
    orphan_term=set(data["shadow_terminal"])-set(data["shadow_arm"])
    if orphan_term: errors.append(f"shadow terminals without arm={len(orphan_term)}")
    if len(data["quarantine_release"])>len(data["quarantine_enter"]):
        errors.append("quarantine releases exceed entries")
    # SP V2 is continuation-only: no V2 action should belong to a known reversal plan.
    for sid in set(data["sp_v2_close"])|set(data["sp_v2_be"]):
        if data["plans"].get(sid,{}).get("scope")=="EXTERNAL_REVERSAL":
            errors.append(f"SP V2 action on reversal scenario={sid}")
    return errors, unresolved

def main():
    if len(sys.argv)!=2:
        print("usage: summarize_d149_sp_em_v2.py ledger.csv",file=sys.stderr); return 2
    path=Path(sys.argv[1]); data=read(path); records,bad=build_records(data)
    errors,unresolved=integrity(data,records)
    if bad: errors.append(f"closed trades missing risk/net accounting={len(bad)}")
    start=data["starts"][0] if data["starts"] else {}
    exit_mode=start.get("exit_mode","UNKNOWN"); em_mode=start.get("em_mode","UNKNOWN")

    print("D149 V2 LEDGER INTEGRITY:","PASS" if not errors else "FAIL")
    print(f"file={path}")
    print(f"build={start.get('build','UNKNOWN')} exit_mode={exit_mode} em_mode={em_mode}")
    print(f"fills={len(data['fills'])} closes={len(data['closes'])} unresolved={len(unresolved)} blocked_scenarios={len(data['em_block'])}")
    if data["ea_stops"]:
        es=data["ea_stops"][-1]
        print(f"execution_divergences={es.get('execution_divergences','NA')} cancel_rejected={es.get('cancel_rejected','NA')}")
    for e in errors: print("ERROR:",e)

    print_metrics("ALL",records)
    cont=[x for x in records if x["scope"]=="EXTERNAL_CONTINUATION"]
    rev=[x for x in records if x["scope"]=="EXTERNAL_REVERSAL"]
    if cont: print_metrics("CONTINUATION",cont)
    if rev: print_metrics("REVERSAL",rev)
    for d in ["LONG","SHORT"]:
        rr=[x for x in cont if x["dir"]==d]
        if rr: print_metrics(f"CONT_{d}",rr)

    if exit_mode=="SMART_PARTIAL_V2" or data["sp_v2_close"] or data["sp_v2_be"]:
        print("SP_V2:")
        cont_states=Counter(data["sp_state"].get(x["sid"],{}).get("state","NONE") for x in cont if x["sid"] in data["sp_state"])
        for k,v in sorted(cont_states.items()): print(f"  continuation_state_{k}={v}")
        actions=Counter()
        for rows in data["sp_v2_close"].values():
            for ev,d,_ in rows:
                if ev=="D149_SP_V2_CLOSE_ACCEPTED": actions[d.get("action","UNKNOWN")]+=1
        for k,v in sorted(actions.items()): print(f"  close_{k}={v}")
        print(f"  close_rejected={data['events']['D149_SP_V2_CLOSE_REJECTED']} strong_partial_infeasible={data['events']['D149_SP_V2_STRONG_PARTIAL_INFEASIBLE']}")
        print(f"  cost_be_moved={data['events']['D149_SP_V2_COST_BE_MOVED']} cost_be_rejected={data['events']['D149_SP_V2_COST_BE_REJECTED']} cost_be_already_protected={data['events']['D149_SP_V2_COST_BE_ALREADY_PROTECTED']}")
        for state in ["STRONG_RUNNER","DEFAULT"]:
            rr=[x for x in cont if x["sp"]==state]
            if rr: print_metrics(f"SP_V2_CONT_{state}",rr)

    if em_mode=="ENTRY_SURVIVAL_QUARANTINE_V2" or data["em_v2_real1"] or data["em_v2_failure"] or data["shadow_arm"]:
        print("EM_V2:")
        reasons=Counter(d.get("reason","UNKNOWN") for rows in data["em_block"].values() for d in rows)
        for k,v in sorted(reasons.items()): print(f"  blocked_{k}={v}")
        print(f"  real_plus_1r={data['events']['D149_EM_V2_REAL_PLUS_1R']} genuine_entry_failures={data['events']['D149_EM_V2_ENTRY_FAILURE']}")
        print(f"  quarantine_entered={data['events']['D149_EM_V2_QUARANTINE_ENTERED']} quarantine_released={data['events']['D149_EM_V2_QUARANTINE_RELEASED']}")
        print(f"  shadow_armed={data['events']['D149_EM_V2_SHADOW_ARMED']} shadow_filled={data['events']['D149_EM_V2_SHADOW_FILLED']} shadow_plus_1r={data['events']['D149_EM_V2_SHADOW_PLUS_1R']} shadow_sl={data['events']['D149_EM_V2_SHADOW_SL']} shadow_canceled={data['events']['D149_EM_V2_SHADOW_CANCELED']} shadow_censored={data['events']['D149_EM_V2_SHADOW_CENSORED']}")
        if data["stops"]:
            s=data["stops"][-1]
            keys=["em_v2_entry_failures","em_v2_one_r_successes","em_v2_quarantine_entries","em_v2_quarantine_releases","em_v2_blocks_quarantine","em_v2_blocks_no_refresh","em_v2_shadow_armed","em_v2_shadow_filled","em_v2_shadow_success","em_v2_shadow_failure","em_v2_shadow_canceled","em_v2_shadow_censored","em_v2_quarantine_active_at_stop","em_v2_global_failures_at_stop"]
            print("  stop_counters="+" ".join(f"{k}={s.get(k,'NA')}" for k in keys))

    if unresolved: print("unresolved_scenarios="+",".join(sorted(unresolved)[:20]))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
