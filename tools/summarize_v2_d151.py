from __future__ import annotations

import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

KV_RE = re.compile(r'([A-Za-z0-9_]+)=("[^"]*"|\S+)')
FLOORS = [0.25,0.50,0.75,1.00,1.25,1.50]


def kv(detail):
    if not isinstance(detail,str):
        return {}
    out={}
    for m in KV_RE.finditer(detail):
        out[m.group(1)] = m.group(2).strip('"')
    return out


def f(d,k,default=float('nan')):
    try: return float(d.get(k,''))
    except Exception: return default


def b(d,k):
    return str(d.get(k,'')).lower()=='true'


def scenario_id_from_detail(detail):
    return kv(detail).get('scenario_id','')


def trade_metrics(rs):
    if not rs:
        return None
    wins=[x for x in rs if x>0]
    losses=[x for x in rs if x<=0]
    equity=0.0; peak=0.0; maxdd=0.0; streak=0; maxstreak=0
    for x in rs:
        equity+=x; peak=max(peak,equity); maxdd=max(maxdd,peak-equity)
        if x<=0: streak+=1; maxstreak=max(maxstreak,streak)
        else: streak=0
    return {
        'n':len(rs),'wins':len(wins),'wr':len(wins)/len(rs),
        'avgw':sum(wins)/len(wins) if wins else math.nan,
        'avgl':sum(losses)/len(losses) if losses else math.nan,
        'exp':sum(rs)/len(rs),'total':sum(rs),'dd':maxdd,'streak':maxstreak,
        'ge1':sum(x>=1.0 for x in rs),'ge1_rate':sum(x>=1.0 for x in rs)/len(rs),
        'all_ge1':all(x>=1.0 for x in rs),
    }


def print_metrics(m):
    if not m:
        print('no closed-trade metrics')
        return
    print(f"closed={m['n']} wins={m['wins']} WR={100*m['wr']:.2f}%")
    print(f"avg_winner={m['avgw']:+.3f}R avg_loser={m['avgl']:+.3f}R expectancy={m['exp']:+.3f}R total={m['total']:+.3f}R")
    print(f"max_closed_trade_DD={m['dd']:.3f}R longest_nonpositive_streak={m['streak']}")
    print(f"final_net_R>=+1R: {m['ge1']}/{m['n']} = {100*m['ge1_rate']:.2f}%  all_ge_1R={str(m['all_ge1']).lower()}")
    print(f"gap_to_70pct_WR={max(0.0,70.0-100*m['wr']):.2f} percentage points")


def main(path):
    df=pd.read_csv(path)
    if list(df.columns)[:6] != ['observed_at','event','timeframe','available_at','object_id','detail']:
        raise SystemExit('unexpected ledger columns')

    starts=df[df.event.eq('EA_START')]
    failures=[]
    if len(starts)!=1:
        failures.append(f'EA_START count={len(starts)} (D151 requires one tester run per ledger)')
    start=kv(starts.iloc[0].detail) if len(starts) else {}
    build=start.get('build','')
    if build and build!='2.01R0L1':
        failures.append(f'unexpected build={build}, expected 2.01R0L1')

    # hard V2 scope integrity
    reversal_plans=int(df.event.eq('SCENARIO_PLANNED').mul(df.detail.astype(str).str.contains('scope=EXTERNAL_REVERSAL',na=False)).sum())
    reversal_fills=int(df.event.eq('POSITION_FILLED').mul(df.detail.astype(str).str.contains('scenario:EXTERNAL_REVERSAL',na=False)).sum())
    reversal_closes=int(df.event.eq('POSITION_CLOSED').mul(df.detail.astype(str).str.contains('scenario:EXTERNAL_REVERSAL',na=False)).sum())
    div=int(df.event.eq('EXECUTION_DIVERGENCE').sum())
    cancel_rej=int(df.event.eq('PENDING_CANCEL_REJECTED').sum())
    if reversal_plans or reversal_fills or reversal_closes:
        failures.append(f'reversal authority leak plans/fills/closes={reversal_plans}/{reversal_fills}/{reversal_closes}')
    if div: failures.append(f'execution_divergence={div}')
    if cancel_rej: failures.append(f'cancel_rejected={cancel_rej}')

    # Economic R from actual aggregate closes. Prefer D151 event, which already uses actual fill-risk money.
    close_rows=df[df.event.eq('D151_ACTUAL_CLOSE')]
    rs=[]; close_by_id={}
    if len(close_rows):
        for _,r in close_rows.iterrows():
            d=kv(r.detail); sid=d.get('scenario_id',''); x=f(d,'actual_net_r')
            if sid and math.isfinite(x):
                close_by_id[sid]=x; rs.append(x)
    else:
        for _,r in df[df.event.eq('POSITION_CLOSED')].iterrows():
            d=kv(r.detail); risk=f(d,'actual_fill_risk_money'); net=f(d,'realized_net_money')
            if risk>0 and math.isfinite(net):
                x=net/risk; rs.append(x); close_by_id[d.get('scenario_id','')]=x

    print('=== D151 V2 INTEGRITY ===')
    print(f"symbol={start.get('symbol','NA')} build={build or 'NA'} phase={start.get('phase','NA')}")
    print(f"reversal_plans={reversal_plans} reversal_fills={reversal_fills} reversal_closes={reversal_closes}")
    print(f"execution_divergence={div} cancel_rejected={cancel_rej}")
    print('D151 V2 LEDGER INTEGRITY:', 'PASS' if not failures else 'FAIL')
    for x in failures: print(' -',x)

    print('\n=== STRETCH TARGET SCORECARD ===')
    print_metrics(trade_metrics(rs))

    fills={scenario_id_from_detail(x) for x in df.loc[df.event.eq('D151_FILL_SNAPSHOT'),'detail']}
    one={scenario_id_from_detail(x) for x in df.loc[df.event.eq('D151_PLUS_1R'),'detail']}
    two={scenario_id_from_detail(x) for x in df.loc[df.event.eq('D151_PLUS_2R'),'detail']}
    fills.discard(''); one.discard(''); two.discard('')
    print('\n=== STAGE FUNNEL ===')
    print(f"D151 fills={len(fills)} +1R={len(one)} ({100*len(one)/len(fills):.2f}% if fills else 0) +2R={len(two)}")
    if one: print(f"P(+2R | +1R)={100*len(two & one)/len(one):.2f}%")

    # Runner state at +1R.
    one_state={}
    for _,r in df[df.event.eq('D151_PLUS_1R')].iterrows():
        d=kv(r.detail); one_state[d.get('scenario_id','')]=d.get('runner_state','UNKNOWN')
    print('\n=== +1R RUNNER DISCRIMINATION ===')
    for state in sorted(set(one_state.values())):
        ids={sid for sid,s in one_state.items() if sid and s==state}
        hit=len(ids & two)
        print(f"{state}: n={len(ids)} +2R={hit} rate={100*hit/len(ids):.2f}%" if ids else f"{state}: n=0")

    # Pre-1R failures and shadow taxonomy.
    pre_fail=[]
    for _,r in df[df.event.eq('D151_PRE1_FAILURE')].iterrows(): pre_fail.append(kv(r.detail))
    terminals=[]
    for _,r in df[df.event.eq('D151_PRE1_SHADOW_TERMINAL')].iterrows(): terminals.append(kv(r.detail))
    print('\n=== PRE-1R FAILURE TAXONOMY ===')
    print(f"SL-first failures={len(pre_fail)}")
    if pre_fail:
        print('map_support_same_at_sl=',sum(b(x,'map_support_same_at_sl') for x in pre_fail),'/',len(pre_fail))
        print('root_alive_at_sl=',sum(b(x,'root_alive_at_sl') for x in pre_fail),'/',len(pre_fail))
        print('frozen_owner_alive_at_sl=',sum(b(x,'frozen_owner_alive_at_sl') for x in pre_fail),'/',len(pre_fail))
    tc=Counter(x.get('outcome','UNKNOWN') for x in terminals)
    for k,v in sorted(tc.items()): print(f"{k}: {v}")

    # +2R giveback in actual economics.
    print('\n=== +2R ACTUAL GIVEBACK ===')
    post2_actual=[close_by_id[sid] for sid in two if sid in close_by_id]
    if post2_actual:
        small=sum(x<1.0 for x in post2_actual)
        print(f"closed +2R cohort={len(post2_actual)} final_net_R<1R={small}/{len(post2_actual)}")
        print(f"median_final_net_R={pd.Series(post2_actual).median():+.3f}R mean={sum(post2_actual)/len(post2_actual):+.3f}R")
    else: print('no closed +2R cohort')

    # Post2 price-path milestone retracement frontier.
    milestone=defaultdict(dict)
    for _,r in df[df.event.eq('D151_POST2_MILESTONE')].iterrows():
        d=kv(r.detail); sid=d.get('scenario_id',''); ms=d.get('milestone','')
        if sid and ms: milestone[ms][sid]=f(d,'min_r_since_plus2')
    print('\n=== POST-+2R RETRACEMENT FRONTIER ===')
    for ms in ['PLUS_3R','PLUS_4R','PLUS_5R']:
        vals=[x for x in milestone.get(ms,{}).values() if math.isfinite(x)]
        if not vals:
            print(f"{ms}: n=0")
            continue
        s=pd.Series(vals)
        print(f"{ms}: n={len(vals)} min-before milestone median={s.median():.3f}R min={s.min():.3f}R")
        safe=[]
        for floor in FLOORS:
            n=sum(v>floor+1e-10 for v in vals)
            safe.append(f"{floor:.2f}R:{n}/{len(vals)}")
        print('  floor not touched before milestone ->',' '.join(safe))

    postterm=[kv(x) for x in df.loc[df.event.eq('D151_POST2_TERMINAL'),'detail']]
    print('\npost2 terminals:',dict(Counter(x.get('outcome','UNKNOWN') for x in postterm)))

    if failures:
        return 2
    return 0


if __name__=='__main__':
    if len(sys.argv)!=2:
        print('usage: summarize_v2_d151.py <ledger.csv>')
        raise SystemExit(1)
    raise SystemExit(main(Path(sys.argv[1])))
