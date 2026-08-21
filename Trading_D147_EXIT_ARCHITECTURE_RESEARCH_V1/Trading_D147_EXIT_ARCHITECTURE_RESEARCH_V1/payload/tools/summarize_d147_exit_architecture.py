#!/usr/bin/env python3
"""Summarize one D-147 unified ledger at closed-trade grain."""
from __future__ import annotations
import csv, re, statistics, sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

KV=re.compile(r"([A-Za-z0-9_]+)=(.*?)(?=\s+[A-Za-z0-9_]+=|$)")
DT_FMT="%Y.%m.%d %H:%M:%S"


def kv(s): return {k:v.strip() for k,v in KV.findall(s or "")}
def fnum(d,k,default=None):
    try: return float(d[k])
    except Exception: return default

def dt(s):
    try: return datetime.strptime(s,DT_FMT)
    except Exception: return None

def pct(n,d): return 0.0 if not d else 100.0*n/d

def read(path):
    start=None; fills={}; closes={}; directions={}; actions=Counter(); stop=None
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        for row in r:
            ev=(row.get("event") or "").strip(); d=kv(row.get("detail") or "")
            oid=(row.get("object_id") or "").strip(); sid=d.get("scenario_id",oid)
            if ev=="D147_EXIT_VARIANT_START": start=d
            elif ev=="D147_EXIT_VARIANT_STOP": stop=d
            elif ev=="PENDING_ORDER_ACCEPTED" and sid: directions[sid]=d.get("direction","UNKNOWN")
            elif ev=="POSITION_FILLED" and sid: fills[sid]=(d,row)
            elif ev=="POSITION_CLOSED" and sid: closes[sid]=(d,row)
            elif ev.startswith("D147_"): actions[ev]+=1
    return start,fills,closes,directions,actions,stop


def mean(xs): return None if not xs else statistics.mean(xs)
def fmt(x): return "NA" if x is None else f"{x:.4f}"


def main():
    if len(sys.argv)!=2:
        print("usage: summarize_d147_exit_architecture.py ledger.csv",file=sys.stderr); return 2
    path=Path(sys.argv[1]); start,fills,closes,directions,actions,stop=read(path)
    if start is None:
        print("D147 LEDGER INTEGRITY: FAIL")
        print("missing D147_EXIT_VARIANT_START")
        return 1
    mode=start.get("mode","UNKNOWN")
    records=[]
    missing_risk=[]
    for sid,(cd,crow) in closes.items():
        fd=fills.get(sid,({},{}))[0]
        risk=fnum(cd,"actual_fill_risk_money")
        if risk is None or risk<=0: risk=fnum(fd,"actual_fill_risk_money")
        net=fnum(cd,"realized_net_money")
        gross=fnum(cd,"exit_profit")
        if risk is None or risk<=0 or net is None:
            missing_risk.append(sid); continue
        exit_at=dt(cd.get("exit_at","")) or dt(crow.get("available_at","")) or dt(crow.get("observed_at",""))
        records.append({"sid":sid,"dir":directions.get(sid,"UNKNOWN"),"risk":risk,"net_money":net,
                        "net_r":net/risk,"gross_r":None if gross is None else gross/risk,"exit_at":exit_at})
    records.sort(key=lambda x:(x["exit_at"] or datetime.min,x["sid"]))
    unresolved=sorted(set(fills)-set(closes))
    netrs=[x["net_r"] for x in records]; wins=[x for x in netrs if x>0]; losses=[x for x in netrs if x<0]; bes=[x for x in netrs if x==0]
    grossrs=[x["gross_r"] for x in records if x["gross_r"] is not None]
    cum=0.0; peak=0.0; maxdd=0.0; streak=0; maxstreak=0
    for r in netrs:
        cum+=r; peak=max(peak,cum); maxdd=max(maxdd,peak-cum)
        if r<0: streak+=1; maxstreak=max(maxstreak,streak)
        else: streak=0
    pos=sorted((r for r in wins),reverse=True); pos_sum=sum(pos)
    top1=(pos[0]/pos_sum if pos and pos_sum>0 else None)
    top3=(sum(pos[:3])/pos_sum if pos and pos_sum>0 else None)
    print("D147 LEDGER INTEGRITY:", "PASS" if not missing_risk else "FAIL")
    print(f"file={path}")
    print(f"mode={mode}")
    print(f"fills={len(fills)} closes={len(closes)} analyzed_closed={len(records)} unresolved={len(unresolved)}")
    if missing_risk: print("missing_or_invalid_closed_trade_accounting=", ",".join(missing_risk[:10]))
    print(f"realized_net_win_rate={len(wins)}/{len(records)} ({pct(len(wins),len(records)):.2f}%) breakeven={len(bes)}")
    print(f"avg_winner_net_R={fmt(mean(wins))} avg_loser_net_R={fmt(mean(losses))}")
    print(f"net_expectancy_R_per_trade={fmt(mean(netrs))} total_net_R={fmt(sum(netrs) if netrs else None)}")
    print(f"gross_price_pnl_expectancy_R_per_trade={fmt(mean(grossrs))}")
    print(f"closed_trade_max_drawdown_R={maxdd:.4f} longest_loss_streak={maxstreak}")
    print(f"winner_R_share_top1={fmt(top1)} winner_R_share_top3={fmt(top3)}")
    for direction in ["LONG","SHORT","UNKNOWN"]:
        rr=[x["net_r"] for x in records if x["dir"]==direction]
        if rr:
            ww=sum(x>0 for x in rr)
            print(f"{direction}: n={len(rr)} win_rate={pct(ww,len(rr)):.2f}% expectancy_R={mean(rr):.4f}")
    print("actions:")
    for k in ["D147_TRAILING_SL_MOVED","D147_TRAILING_SL_REJECTED","D147_PARTIAL_CLOSE_ACCEPTED","D147_PARTIAL_CLOSE_REJECTED","D147_PARTIAL_INFEASIBLE"]:
        print(f"  {k}={actions[k]}")
    if stop:
        print("stop_counters:", " ".join(f"{k}={stop.get(k,'NA')}" for k in ["trailing_moves","partial_closes","action_rejections","partial_infeasible"]))
    if unresolved:
        print("unresolved_scenarios:", ",".join(unresolved[:20]))
    return 0 if not missing_risk else 1

if __name__=="__main__":
    raise SystemExit(main())
