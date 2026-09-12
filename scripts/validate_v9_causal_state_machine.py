#!/usr/bin/env python3
"""Regression validator for the frozen V9 causal state-machine implementation checkpoint.

This validator never scans future-hidden source ranges in strategy mode. It uses the
frozen consumed byte-range manifest and checks deterministic hashes/counts plus resume
and gate/action mechanics. Synthetic gate actions are interface tests only; they have
no P/L or strategy-performance authority.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from v9_runtime_state_v2 import V2Runner,load_index,AUTHORITATIVE_SHA256

EXPECTED_CODE={
 'v9_semantic_runtime.py':'92f8ab602ca81dff881cb78ee4084664c0c8847fa1948f998bee81158c408c2d',
 'v9_execution_state_machine.py':'8a5430bcecdaad36f47bf63be60fd9f069ed31565037fb025ea4b07fb300fd09',
 'v9_strategy_state_machine.py':'3f7bd38cc17f30409a330b7b357a03685fbf3c05473cc00c9ca536f34136070e',
 'v9_runtime_state_v2.py':'45086e53d34d0c9f247b746ebfbece7ca7e75a453dd888ec1064538527a441cb',
}
EXPECTED_FULL_HASHES={
 'revealed_consumed.tsv':'ddc7e6d8a280a0e14258dbfe5e891caf816d85f42bf60d87db4b1855b640334a',
 'semantic_events.jsonl':'6844da62c01f70f609f305040712f174fa1f432164d13f5e6109ad4a296e1506',
 'counter_events.jsonl':'1925b55c1e3ec196fbe81fd9056b67d72a210023340b767fe7859a41384f95b8',
 'with_parent_events.jsonl':'19141ebaaca7620c9c34001f854951cc5cf35f925e7b1c683ca5c70161d58427',
 'object_known.jsonl':'ffaae63cc13a3a981ab587b22b36c2e882bc2bb086f766dff537f8fd0b98d326',
}
EXPECTED_GATE_COUNTS={'CROSS_LANE_CONFLICT_REVIEW':162,'ENTRY_EXECUTION_REQUIRED':213,'EXIT_EXECUTION_REQUIRED':109,'REMAP_REQUIRED':28,'REVIEW_REQUIRED':81}

def sha(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()

def clean(p):
 if p.exists():shutil.rmtree(p)
 p.mkdir(parents=True)

def counts(path):
 c=Counter();first=0
 for line in path.read_text(encoding='utf-8').splitlines():
  x=json.loads(line);c[x['kind']]+=1
  if x['kind']=='PITCH_AUTHORIZED' and json.loads(x['payload']).get('auth_class')=='FIRST':first+=1
 return c,first

def full_run(source,index,out):
 clean(out);r=V2Runner(source,index,out,independent=True);r.run_all();r.save(out/'state.json');return r

def split_run(source,index,out):
 clean(out);st=out/'state.json';r=V2Runner(source,index,out,independent=True)
 for s in ['2025-03-05 12:34:00','2025-06-30 23:57:00','2026-02-12 12:34:00']:
  r.run_to(datetime.strptime(s,'%Y-%m-%d %H:%M:%S'));r.save(st);r=V2Runner.from_state(source,st)
 r.run_all();r.save(st);return r

def mechanical_action(r,g):
 price=float(r.market.last_price.close if r.market.last_price else 0.0);at=datetime.strptime(g['known_at'],'%Y-%m-%d %H:%M:%S')
 k=g['kind'];child=g.get('child_id');block=g['block']
 if k=='ENTRY_EXECUTION_REQUIRED': return 'ENTRY_FILL',child,at,block,{'price':price}
 if k in ('REVIEW_REQUIRED','REMAP_REQUIRED'): return 'REVIEW_DECISION',child,at,block,{'decision':'EXIT'}
 if k=='EXIT_EXECUTION_REQUIRED': return 'EXIT_FILL',child,at,block,{'price':price}
 if k=='CROSS_LANE_CONFLICT_REVIEW': return 'CONFLICT_DECISION',child,at,block,{'decision':'SKIP_NEW_PITCH'}
 raise RuntimeError(k)

def deep_gate(source,index,out):
 clean(out);st=out/'state.json';r=V2Runner(source,index,out,independent=False);gate_counts=Counter();segments=0;restarts={1,25,100,250,500}
 first_sem=None
 while True:
  if segments in restarts:r.save(st);r=V2Runner.from_state(source,st)
  z=r.run_until_gate();segments+=1
  if z['status']=='END_OF_CONSUMED':break
  g=z['gate'];gate_counts[g['kind']]+=1
  if g['known_at']!=g['price_revealed_cutoff'] and first_sem is None:first_sem=g
  ak,ch,at,block,kw=mechanical_action(r,g);r.apply_action(ak,child_id=ch,at=at,block=block,**kw)
 r.save(st)
 return {'segments':segments,'gates':dict(gate_counts),'first_semantic_gate':first_sem,'revealed_rows':r.revealed_rows,'range_index':r.range_i,'pending_gates':r.pending_gates}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--index',type=Path,required=True);ap.add_argument('--work-dir',type=Path,required=True);ap.add_argument('--deep-gate',action='store_true');a=ap.parse_args()
 idx=load_index(a.index);a.work_dir.mkdir(parents=True,exist_ok=True)
 code={n:sha(HERE/n) for n in EXPECTED_CODE}
 if code!=EXPECTED_CODE:raise SystemExit(f'CODE HASH MISMATCH\nexpected={EXPECTED_CODE}\nactual={code}')
 full=a.work_dir/'full';split=a.work_dir/'split';r=full_run(a.source,idx,full)
 hashes={n:sha(full/n) for n in EXPECTED_FULL_HASHES}
 if hashes!=EXPECTED_FULL_HASHES:raise SystemExit(f'FULL HASH MISMATCH\nexpected={EXPECTED_FULL_HASHES}\nactual={hashes}')
 sc=sum(1 for _ in (full/'semantic_events.jsonl').open());assert sc==4254,sc
 obj=Counter(json.loads(x)['family'] for x in (full/'object_known.jsonl').read_text().splitlines());assert obj==Counter({'SWING':12408,'FVG':10163,'OB':5328}),obj
 cc,cf=counts(full/'counter_events.jsonl');wc,wf=counts(full/'with_parent_events.jsonl');assert cf==149 and wf==95,(cf,wf)
 split_run(a.source,idx,split)
 for n in EXPECTED_FULL_HASHES:assert sha(full/n)==sha(split/n),n
 report={'status':'PASS','source_sha256':AUTHORITATIVE_SHA256,'future_hidden_2025_07':'LOCKED','code_sha256':code,'full_hashes':hashes,'revealed_rows':r.revealed_rows,'semantic_events':sc,'m5_objects':dict(obj),'first_authorizations':{'COUNTER':cf,'WITH_PARENT':wf},'split_resume_parity':True}
 if a.deep_gate:
  dg=deep_gate(a.source,idx,a.work_dir/'deep_gate');assert dg['segments']==594,dg['segments'];assert dg['gates']==EXPECTED_GATE_COUNTS,dg['gates'];assert dg['revealed_rows']==229861 and dg['range_index']==2 and not dg['pending_gates'];assert dg['first_semantic_gate']['price_revealed_cutoff']<dg['first_semantic_gate']['known_at'];report['deep_gate']=dg
 out=a.work_dir/'V9_RUNTIME_ACCEPTANCE_REPORT.json';out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
