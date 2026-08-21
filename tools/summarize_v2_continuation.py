#!/usr/bin/env python3
from __future__ import annotations
import csv, re, sys
from pathlib import Path

KV=re.compile(r'([A-Za-z0-9_]+)=([^ ]+)')

def kv(s): return dict(KV.findall(s or ''))

def main(path):
    rows=list(csv.DictReader(open(path,'r',encoding='utf-8-sig',newline='')))
    starts=[r for r in rows if r.get('event')=='EA_START']
    errs=[]
    if len(starts)!=1: errs.append(f'EA_START count={len(starts)}')
    if starts:
        d=kv(starts[0].get('detail',''))
        if d.get('build')!='2.00R0L0': errs.append(f"build={d.get('build')}")
        if d.get('phase')!='V2_CONTINUATION_ONLY_BOOTSTRAP': errs.append(f"phase={d.get('phase')}")
    rev_plan=rev_fill=rev_close=0
    fills=closes=div=cancelrej=0
    for r in rows:
        e=r.get('event',''); det=r.get('detail','') or ''
        isrev=('scope=EXTERNAL_REVERSAL' in det or 'scenario_scope=EXTERNAL_REVERSAL' in det or ':EXTERNAL_REVERSAL:' in (r.get('object_id','') or ''))
        if e=='SCENARIO_PLANNED' and isrev: rev_plan+=1
        if e=='POSITION_FILLED':
            fills+=1
            if isrev: rev_fill+=1
        if e=='POSITION_CLOSED':
            closes+=1
            if isrev: rev_close+=1
        if e=='EXECUTION_DIVERGENCE': div+=1
        if e in ('PENDING_CANCEL_REJECTED','EXECUTION_CANCEL_REJECTED'): cancelrej+=1
    unresolved=max(0,fills-closes)
    if rev_plan or rev_fill or rev_close:
        errs.append(f'reversal strategy events plan={rev_plan} fill={rev_fill} close={rev_close}')
    status='PASS' if not errs else 'FAIL'
    print(f'V2 CONTINUATION-ONLY INTEGRITY: {status}')
    print(f'file={path}')
    print(f'fills={fills} closes={closes} unresolved={unresolved} execution_divergence={div} cancel_rejected={cancelrej}')
    print(f'reversal_plans={rev_plan} reversal_fills={rev_fill} reversal_closes={rev_close}')
    for e in errs: print('ERROR:',e)
    return 0 if not errs else 1

if __name__=='__main__':
    if len(sys.argv)!=2:
        print('usage: summarize_v2_continuation.py <ledger.csv>'); raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1])))
