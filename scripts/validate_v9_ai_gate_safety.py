#!/usr/bin/env python3
"""Consumed integration checks for V9 AI outage/staleness/remap safety.

Synthetic outage/remap actions are interface tests only. They have no market-policy or
P/L authority. The validator never opens future-hidden ranges beyond the frozen manifest.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, shutil, sys
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from v9_runtime_state_v2 import V2Runner,load_index
from v9_ai_decision_protocol import (
    scheduler_disposition, build_ai_request, outage_record, validate_ai_response,
    RESPONSE_VERSION, ProtocolError,
)

EXPECTED_FIRST_AI_GATE='b0d82335f3929e41f25e7c95'
EXPECTED_FIRST_REMAP_GATE='33457bd70777a180dcc24aec'

def jd(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def at(g): return datetime.strptime(g['known_at'],'%Y-%m-%d %H:%M:%S')

def mechanical_non_ai_or_exit_ai(r,g,route):
    px=float(r.market.last_price.close if r.market.last_price else 0.0)
    if route=='EXECUTION_ADAPTER':
        k='ENTRY_FILL' if g['kind']=='ENTRY_EXECUTION_REQUIRED' else 'EXIT_FILL'
        return r.apply_action(k,child_id=g.get('child_id'),at=at(g),block=g['block'],price=px)
    if route=='DETERMINISTIC_FAIL_CLOSED':
        return r.apply_action('CONFLICT_DECISION',child_id=g.get('child_id'),at=at(g),block=g['block'],decision='SKIP_NEW_PITCH')
    return r.apply_action('REVIEW_DECISION',child_id=g.get('child_id'),at=at(g),block=g['block'],decision='EXIT')

def fresh(source,index,out):
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    return V2Runner(source,load_index(index),out,independent=False)

def first_ai_safety(source,index,out):
    r=fresh(source,index,out);seen=0
    while True:
        z=r.run_until_gate();seen+=1
        if z['status']!='GATE':raise RuntimeError('no AI gate found')
        g=z['gate'];disp=scheduler_disposition(r.state())
        if disp['route']=='AI_DECISION':break
        mechanical_non_ai_or_exit_ai(r,g,disp['route'])
    req=disp['request'];pre=r.state();d0=jd(pre)
    outage=outage_record(req,'synthetic service outage integration test');d1=jd(r.state())
    state_path=out/'state.json';r.save(state_path);rr=V2Runner.from_state(source,state_path);req2=build_ai_request(rr.state())
    changed=copy.deepcopy(rr.state());changed['action_log_sha256']='synthetic-changed-prefix';current=build_ai_request(changed)
    resp={'version':RESPONSE_VERSION,'request_id':req['request_id'],'request_fingerprint':req['request_fingerprint'],'gate_id':req['gate_id'],'decision':'EXIT'}
    rejected=False
    try:validate_ai_response(req,resp,current)
    except ProtocolError:rejected=True
    child=req['decision_context']['strategy']['child'] or {}
    return {'gates_seen':seen,'gate_id':g['gate_id'],'gate_kind':g['kind'],'expected_gate_id':EXPECTED_FIRST_AI_GATE,
            'outage_no_state_mutation':d0==d1,'restart_request_exact':req2==req,'stale_response_rejected':rejected,
            'outage_runtime_action':outage['runtime_action'],'outage_allow_new_risk':outage['allow_new_risk'],'outage_advance_semantic_replay':outage['advance_semantic_replay'],
            'hard_guard_origin_boundary':child.get('origin_boundary'),'hard_guard_state':child.get('state')}

def first_remap_path(source,index,out):
    r=fresh(source,index,out);seen=0
    while True:
        z=r.run_until_gate();seen+=1
        if z['status']!='GATE':raise RuntimeError('no REMAP gate found')
        g=z['gate'];disp=scheduler_disposition(r.state())
        if g['kind']=='REMAP_REQUIRED':break
        mechanical_non_ai_or_exit_ai(r,g,disp['route'])
    req=disp['request'];mp=req['decision_context']['market']['parent'];child=req['decision_context']['strategy']['child'];origin=child['origin_boundary']
    if not mp:raise RuntimeError('first REMAP gate has no causally earned current Parent')
    resp={'version':RESPONSE_VERSION,'request_id':req['request_id'],'request_fingerprint':req['request_fingerprint'],'gate_id':req['gate_id'],
          'decision':'REMAP','new_parent_id':mp['parent_id'],'new_parent_side':mp['side'],'journey_role':'WITH_NEW_PARENT_JOURNEY'}
    action=validate_ai_response(req,resp,req);kw={k:v for k,v in action.items() if k not in ('kind','child_id','at','block')}
    r.apply_action(action['kind'],child_id=action['child_id'],at=datetime.strptime(action['at'],'%Y-%m-%d %H:%M:%S'),block=action['block'],**kw)
    active=None
    for lane in (r.observer.counter,r.observer.with_parent):
        if lane.active and lane.active.child_id==child['child_id']:active=lane.active
    return {'gates_seen':seen,'gate_id':g['gate_id'],'expected_gate_id':EXPECTED_FIRST_REMAP_GATE,'old_parent_id':child['parent_id'],'new_parent':mp,
            'child_state_after':active.state if active else None,'origin_unchanged':bool(active and active.origin_boundary==origin),
            'journey_role':active.journey_role if active else None,'pending_gates_after':r.pending_gates}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--index',type=Path,required=True);ap.add_argument('--work-dir',type=Path,required=True);a=ap.parse_args()
    a.work_dir.mkdir(parents=True,exist_ok=True)
    outage=first_ai_safety(a.source,a.index,a.work_dir/'outage')
    remap=first_remap_path(a.source,a.index,a.work_dir/'remap')
    ok=(outage['gate_id']==EXPECTED_FIRST_AI_GATE and outage['outage_no_state_mutation'] and outage['restart_request_exact'] and outage['stale_response_rejected'] and outage['outage_runtime_action'] is None and not outage['outage_allow_new_risk'] and not outage['outage_advance_semantic_replay'] and outage['hard_guard_origin_boundary'] is not None and remap['gate_id']==EXPECTED_FIRST_REMAP_GATE and remap['child_state_after']=='OPEN' and remap['origin_unchanged'] and remap['journey_role']=='WITH_NEW_PARENT_JOURNEY' and not remap['pending_gates_after'])
    report={'status':'PASS' if ok else 'FAIL','scope':'consumed AI gate safety interface only; synthetic outage/remap have no strategy-performance authority','outage_staleness':outage,'remap_path':remap}
    p=a.work_dir/'V9_AI_GATE_SAFETY_INTEGRATION_20260912.json';p.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True))
    if not ok:raise SystemExit(2)
if __name__=='__main__':main()
