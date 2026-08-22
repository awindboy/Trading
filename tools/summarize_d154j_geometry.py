#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,re,statistics,zipfile
from pathlib import Path
from collections import defaultdict

def kv(s:str): return {m.group(1):m.group(2) for m in re.finditer(r'(\w+)=([^ ]+)',s or '')}
def f(x):
    try:return float(x)
    except:return None

def med(xs):
    xs=[x for x in xs if x is not None]
    return statistics.median(xs) if xs else None

def q(xs,p):
    xs=sorted(x for x in xs if x is not None)
    if not xs:return None
    k=(len(xs)-1)*p; a=int(k); b=min(a+1,len(xs)-1); t=k-a
    return xs[a]*(1-t)+xs[b]*t

def fmt(xs):
    xs=[x for x in xs if x is not None]
    if not xs:return 'NA'
    return f'n={len(xs)} med={med(xs):.3f} q25={q(xs,.25):.3f} q75={q(xs,.75):.3f}'

def nested_geometry_zip(master:Path):
    with zipfile.ZipFile(master) as z:
        ns=[n for n in z.namelist() if n.startswith('geometry/') and n.endswith('.zip')]
        if len(ns)!=1: raise RuntimeError(f'expected one geometry nested ZIP, found {len(ns)}')
        return z.read(ns[0])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('master_zip',type=Path); a=ap.parse_args()
    blob=nested_geometry_zip(a.master_zip)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        csvs=[n for n in z.namelist() if n.endswith('.csv')]
        for name in csvs:
            sym='GOLD' if '__GOLD__' in name else ('CADJPY' if '__CADJPY__' in name else name)
            rows=list(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig',errors='replace'))))
            stages=defaultdict(dict); outcomes={}
            for r in rows:
                e=r.get('event',''); d=kv(r.get('detail',''))
                if e=='D154J_GEOMETRY_STAGE': stages[d.get('scenario_id','')][d.get('stage','')]=d
                elif e=='D154J_PRIMARY_OUTCOME': outcomes[d.get('scenario_id','')]=d.get('outcome','')
            print(f'\n[{sym}] fills={len(outcomes)} plus1={sum(v=="PLUS_1R" for v in outcomes.values())} sl={sum(v=="SL_FIRST" for v in outcomes.values())} censor={sum(v=="RIGHT_CENSORED" for v in outcomes.values())}')
            for stage in ('PLAN','ROOT_CONTACT','FIRST_POST_CONTACT_SAME_DIR_BOS','SWEEP','CHOCH','PENDING','FILL'):
                allv=[]; wins=[]; losses=[]
                for sid,sd in stages.items():
                    if stage not in sd: continue
                    d=sd[stage]
                    if d.get('plan_geometry_available')!='true': continue
                    v=f(d.get('plan_progress'))
                    allv.append(v)
                    if outcomes.get(sid)=='PLUS_1R': wins.append(v)
                    elif outcomes.get(sid)=='SL_FIRST': losses.append(v)
                if allv: print(f'  {stage:34s} progress all[{fmt(allv)}] win[{fmt(wins)}] loss[{fmt(losses)}]')
            # Path deltas on frozen PLAN-map geometry when both endpoints are available.
            for a0,a1,label in [('ROOT_CONTACT','CHOCH','contact->choch'),('ROOT_CONTACT','FILL','contact->fill')]:
                vals=[]; wins=[]; losses=[]
                for sid,sd in stages.items():
                    if a0 not in sd or a1 not in sd: continue
                    x,y=sd[a0],sd[a1]
                    if x.get('plan_geometry_available')!='true' or y.get('plan_geometry_available')!='true': continue
                    v=f(y.get('plan_progress')); u=f(x.get('plan_progress'))
                    if v is None or u is None: continue
                    d=v-u; vals.append(d)
                    if outcomes.get(sid)=='PLUS_1R': wins.append(d)
                    elif outcomes.get(sid)=='SL_FIRST': losses.append(d)
                print(f'  {label:34s} delta all[{fmt(vals)}] win[{fmt(wins)}] loss[{fmt(losses)}]')
            rem=[]; remr=[]; wrem=[]; lrem=[]
            for sid,sd in stages.items():
                if 'FILL' not in sd: continue
                d=sd['FILL']
                if d.get('plan_geometry_available')=='true':
                    v=f(d.get('plan_remaining_fraction')); rem.append(v)
                    if outcomes.get(sid)=='PLUS_1R': wrem.append(v)
                    elif outcomes.get(sid)=='SL_FIRST': lrem.append(v)
                    if d.get('risk_available')=='true': remr.append(f(d.get('plan_remaining_r')))
            print(f'  FILL remaining_fraction           all[{fmt(rem)}] win[{fmt(wrem)}] loss[{fmt(lrem)}]')
            print(f'  FILL remaining_R                  all[{fmt(remr)}]')
    print('\nDescriptive contrast only. No threshold optimization or market-specific rule is performed.')
    return 0
if __name__=='__main__': raise SystemExit(main())
