#!/usr/bin/env python3
"""Summarize D-145 runner market-context audit without fitting thresholds."""
from __future__ import annotations
import csv, re, statistics, sys
from pathlib import Path

KV=re.compile(r'([A-Za-z0-9_]+)=([^\s]+)')

def kv(detail:str): return {k:v for k,v in KV.findall(detail)}
def num(d,k):
    try:
        v=d.get(k)
        if v is None or v=='NA': return None
        return float(v)
    except: return None

def med(rows,key):
    xs=[num(r,key) for r in rows]; xs=[x for x in xs if x is not None]
    return None if not xs else statistics.median(xs)

def read(path:Path):
    fills={}; ones={}; outcomes={}
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        for row in csv.reader(f):
            if len(row)<6: continue
            event=row[1]; detail=kv(row[5]); sid=detail.get('scenario_id',row[4] if len(row)>4 else '')
            if event=='EDGE_AUDIT_RUNNER_FILL_SNAPSHOT': fills[sid]=detail
            elif event=='EDGE_AUDIT_RUNNER_1R_SNAPSHOT': ones[sid]=detail
            elif event=='EDGE_AUDIT_RUNNER_OUTCOME': outcomes.setdefault(sid,{})[detail.get('target','?')]=detail.get('outcome','?')
    return fills,ones,outcomes

def pct(a,b): return 0.0 if not b else 100*a/b

def main():
    if len(sys.argv)!=2:
        print('Usage: summarize_runner_context_audit.py LEDGER.csv'); return 2
    fills,ones,outcomes=read(Path(sys.argv[1]))
    print(f'Fill snapshots: {len(fills):,}')
    print(f'First +1R snapshots: {len(ones):,}')
    for target in ('1R','2R','3R','STRUCTURAL_TP'):
        known=[o.get(target) for o in outcomes.values() if target in o]
        wins=sum(x=='REACHED_BEFORE_SL' for x in known)
        print(f'{target:13s}: {wins:4d}/{len(known):4d} = {pct(wins,len(known)):6.2f}%')

    for direction in ('LONG','SHORT'):
        ids=[sid for sid,d in fills.items() if d.get('direction')==direction]
        print(f'\n{direction}: fills={len(ids)}')
        for target in ('1R','2R','3R','STRUCTURAL_TP'):
            known=[outcomes.get(sid,{}).get(target) for sid in ids if target in outcomes.get(sid,{})]
            wins=sum(x=='REACHED_BEFORE_SL' for x in known)
            print(f'  {target:13s}: {wins:3d}/{len(known):3d} = {pct(wins,len(known)):6.2f}%')

    one_ids=[sid for sid,o in outcomes.items() if o.get('1R')=='REACHED_BEFORE_SL' and sid in fills]
    runner=[fills[sid] for sid in one_ids if outcomes.get(sid,{}).get('2R')=='REACHED_BEFORE_SL']
    exhaust=[fills[sid] for sid in one_ids if outcomes.get(sid,{}).get('2R')=='SL_FIRST']
    print(f'\nConditional on +1R: 2R+={len(runner)}, exhausted-before-2R={len(exhaust)}')
    fill_features=[
      'prefill_max_favorable_r','prefill_max_favorable_fvg_widths','prefill_max_adverse_r','fvg_to_fill_seconds',
      'fill_h1_range_progress','fill_h1_range_remaining_to_external_r','fill_m30_range_progress','fill_m30_range_remaining_to_external_r',
      'fill_m30_wave_progression','fill_m30_wave_net_directional_advance_norm','fill_m30_wave_leg_expansion_ratio','fill_m30_wave_protected_break_count',
      'fill_objective_room_r','fill_h1_map_owner_age_seconds','fill_m30_map_owner_age_seconds',
      'fill_h1_map_last_directional_bos_age_seconds','fill_m30_map_last_directional_bos_age_seconds'
    ]
    print('\nFill-background medians (descriptive only; no threshold selection):')
    for k in fill_features:
        a,b=med(exhaust,k),med(runner,k)
        if a is not None or b is not None: print(f'  {k:46s} exhaust={a!s:>12} 2R+={b!s:>12}')

    one_runner=[ones[sid] for sid in one_ids if sid in ones and outcomes.get(sid,{}).get('2R')=='REACHED_BEFORE_SL']
    one_exhaust=[ones[sid] for sid in one_ids if sid in ones and outcomes.get(sid,{}).get('2R')=='SL_FIRST']
    one_features=[
      'time_to_1r_seconds','one_r_speed_r_per_hour','max_adverse_before_1r_r',
      'm1_same_direction_events_since_fill','m1_opposite_direction_events_since_fill','m1_same_pb_since_fill','m1_opposite_pb_since_fill',
      'one_r_h1_range_progress','one_r_h1_range_remaining_to_external_r','one_r_m30_range_progress','one_r_m30_range_remaining_to_external_r',
      'one_r_m30_wave_progression','one_r_m30_wave_net_directional_advance_norm','one_r_m30_wave_leg_expansion_ratio','one_r_m30_wave_protected_break_count'
    ]
    print('\nFirst-+1R state medians (descriptive only; no threshold selection):')
    for k in one_features:
        a,b=med(one_exhaust,k),med(one_runner,k)
        if a is not None or b is not None: print(f'  {k:46s} exhaust={a!s:>12} 2R+={b!s:>12}')
    return 0

if __name__=='__main__': raise SystemExit(main())
