#!/usr/bin/env python3
"""Consumed-data gate-by-gate dry-run through frozen V9 AI packet/scheduler.

Synthetic decisions are interface-contract test data only and have no P/L authority.
The action policy intentionally mirrors the previously accepted mechanical harness so
core ledger hashes and gate counts can be compared without changing market policy.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from v9_runtime_state_v2 import V2Runner, load_index
from v9_ai_decision_protocol import build_ai_request, validate_ai_response, route_gate, deterministic_gate_action, RESPONSE_VERSION

EXPECTED_GATES={'CROSS_LANE_CONFLICT_REVIEW':162,'ENTRY_EXECUTION_REQUIRED':213,'EXIT_EXECUTION_REQUIRED':109,'REMAP_REQUIRED':28,'REVIEW_REQUIRED':81}
EXPECTED_GATE_DRIVEN_HASHES={
 'revealed_consumed.tsv':'ddc7e6d8a280a0e14258dbfe5e891caf816d85f42bf60d87db4b1855b640334a',
 'semantic_events.jsonl':'6844da62c01f70f609f305040712f174fa1f432164d13f5e6109ad4a296e1506',
 'counter_events.jsonl':'e6a26ef44acac1078d9dd496f591ffc1c17896b264d4e07adb7ebb28d63e9932',
 'with_parent_events.jsonl':'6bdf8152a12b2c5342f8ff7aa04c1b7d46c57a437279ca83f52e2b681991bff2',
 'object_known.jsonl':'ffaae63cc13a3a981ab587b22b36c2e882bc2bb086f766dff537f8fd0b98d326',
 'external_actions.jsonl':'236809d1566033419600528bb131d9ba3de81779dbc0150b560ff855311ce218',
}

def sha(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def clean(p:Path):
 if p.exists():shutil.rmtree(p)
 p.mkdir(parents=True)

def synthetic_ai_response(req:dict)->dict:
 # Contract test only. Mirrors old mechanical harness: both review/remap semantic gates exit.
 return {'version':RESPONSE_VERSION,'request_id':req['request_id'],'request_fingerprint':req['request_fingerprint'],'gate_id':req['gate_id'],'decision':'EXIT'}

def apply_action(r:V2Runner,a:dict):
 at=datetime.strptime(a['at'],'%Y-%m-%d %H:%M:%S');kw={k:v for k,v in a.items() if k not in ('kind','child_id','at','block')}
 return r.apply_action(a['kind'],child_id=a.get('child_id'),at=at,block=a['block'],**kw)

def runner_state_for_packet(r:V2Runner)->dict:
 # state() drains factual logs and binds packet fingerprint to exact prefix hashes.
 return r.state()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--index',type=Path,required=True);ap.add_argument('--work-dir',type=Path,required=True);a=ap.parse_args()
 clean(a.work_dir);state_path=a.work_dir/'state.json';r=V2Runner(a.source,load_index(a.index),a.work_dir,independent=False)
 gates=Counter();routes=Counter();ai_requests=0;request_restart_exact=True;segments=0;restart_points={1,25,100,250,500}
 while True:
  z=r.run_until_gate();segments+=1
  if z['status']=='END_OF_CONSUMED':break
  g=z['gate'];gates[g['kind']]+=1
  route=route_gate(g);routes[route]+=1
  if route=='EXECUTION_ADAPTER':
   px=float(r.market.last_price.close if r.market.last_price else 0.0)
   if g['kind']=='ENTRY_EXECUTION_REQUIRED':act={'kind':'ENTRY_FILL','child_id':g.get('child_id'),'at':g['known_at'],'block':g['block'],'price':px}
   else:act={'kind':'EXIT_FILL','child_id':g.get('child_id'),'at':g['known_at'],'block':g['block'],'price':px}
  elif route=='DETERMINISTIC_FAIL_CLOSED':
   act=deterministic_gate_action(g)
  else:
   st=runner_state_for_packet(r);req=build_ai_request(st);ai_requests+=1
   if segments in restart_points:
    r.save(state_path);r=V2Runner.from_state(a.source,state_path);req2=build_ai_request(r.state());request_restart_exact &= (req2==req);req=req2
   resp=synthetic_ai_response(req);cur=build_ai_request(r.state());act=validate_ai_response(req,resp,cur)
  apply_action(r,act)
  if segments in restart_points and route!='AI_DECISION':
   r.save(state_path);r=V2Runner.from_state(a.source,state_path)
 r.save(state_path)
 hashes={n:sha(a.work_dir/n) for n in EXPECTED_GATE_DRIVEN_HASHES}
 report={'status':'PASS','scope':'packet/scheduler/external-decision contract mechanics only; synthetic decisions have no strategy-performance authority',
         'segments':segments,'gates':dict(gates),'routes':dict(routes),'ai_requests':ai_requests,'request_restart_exact':request_restart_exact,
         'revealed_rows':r.revealed_rows,'pending_gates':r.pending_gates,'ledger_hashes':hashes,'expected_gate_driven_hashes':EXPECTED_GATE_DRIVEN_HASHES,
         'gate_counts_match':dict(gates)==EXPECTED_GATES,'ledger_hashes_match':hashes==EXPECTED_GATE_DRIVEN_HASHES}
 if not (segments==594 and dict(gates)==EXPECTED_GATES and ai_requests==109 and request_restart_exact and r.revealed_rows==229861 and not r.pending_gates and hashes==EXPECTED_GATE_DRIVEN_HASHES):
  report['status']='FAIL'
 out=a.work_dir/'V9_AI_PACKET_SCHEDULER_CONSUMED_DRY_RUN_20260912.json';out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
 if report['status']!='PASS':raise SystemExit(2)
if __name__=='__main__':main()
