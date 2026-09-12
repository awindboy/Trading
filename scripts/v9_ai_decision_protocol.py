#!/usr/bin/env python3
"""V9 AI review/remap packet + scheduler contract.

This layer does not invent market policy. It binds AI decisions to the exact first
pending semantic gate and exact causal state fingerprint. No elapsed-minute market
threshold is used for staleness. Service outage is fail-stop: no implicit HOLD/EXIT/
REMAP and no new risk; the precommitted Hard-SL remains external/runtime authority.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any, Optional

REQUEST_VERSION='v9-ai-review-remap-request-1'
RESPONSE_VERSION='v9-ai-review-remap-response-1'
SCHEDULER_VERSION='v9-ai-call-scheduler-1'
STALENESS_VERSION='v9-structural-staleness-1'
OUTAGE_VERSION='v9-ai-outage-fail-stop-1'

AI_GATES={'REVIEW_REQUIRED','REMAP_REQUIRED'}
EXECUTION_GATES={'ENTRY_EXECUTION_REQUIRED','EXIT_EXECUTION_REQUIRED'}
DETERMINISTIC_GATES={'CROSS_LANE_CONFLICT_REVIEW'}

class ProtocolError(RuntimeError): pass

def canonical_bytes(x:Any)->bytes:
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')

def digest(x:Any)->str:return hashlib.sha256(canonical_bytes(x)).hexdigest()

def route_gate(gate:dict)->str:
    k=gate.get('kind')
    if k in AI_GATES:return 'AI_DECISION'
    if k in EXECUTION_GATES:return 'EXECUTION_ADAPTER'
    if k in DETERMINISTIC_GATES:return 'DETERMINISTIC_FAIL_CLOSED'
    raise ProtocolError(f'unsupported gate kind {k!r}')

def deterministic_gate_action(gate:dict)->dict:
    if gate.get('kind')!='CROSS_LANE_CONFLICT_REVIEW':
        raise ProtocolError('no deterministic action for this gate')
    return {'kind':'CONFLICT_DECISION','child_id':gate.get('child_id'),'at':gate['known_at'],'block':gate['block'],'decision':'SKIP_NEW_PITCH'}

def _active_lane_snapshot(state:dict,gate:dict)->dict:
    strat=state.get('strategy') or {}
    candidates=[]
    for key in ('counter','with_parent'):
        lane=strat.get(key) or {}
        c=lane.get('active')
        if c and (gate.get('child_id') is None or c.get('child_id')==gate.get('child_id')):
            candidates.append((key,lane))
    if gate.get('child_id'):
        exact=[x for x in candidates if (x[1].get('active') or {}).get('child_id')==gate['child_id']]
        if len(exact)!=1:raise ProtocolError(f'active child snapshot not uniquely found for {gate["child_id"]}')
        key,lane=exact[0]
    else:
        key,lane=(None,{})
    return {'lane_key':key,'context':lane.get('context'),'active_child':lane.get('active')}

def _decision_basis(state:dict,gate:dict)->dict:
    if not state.get('pending_gates') or state['pending_gates'][0].get('gate_id')!=gate.get('gate_id'):
        raise ProtocolError('AI packet can only bind to the first pending gate')
    market=state.get('market') or {}; lane=_active_lane_snapshot(state,gate)
    child=lane.get('active_child') or {}
    return {
      'protocol_versions':{
        'request':REQUEST_VERSION,'scheduler':SCHEDULER_VERSION,'staleness':STALENESS_VERSION,'outage':OUTAGE_VERSION,
        'runtime_state':state.get('version'),'runner':state.get('runner_version'),'strategy_runtime':state.get('strategy_runtime_version'),'authorization':state.get('authorization_version'),
      },
      'causal_prefix':{
        'source_sha256':state.get('source_sha256'),'source_basename':state.get('source_basename'),'range_index':state.get('range_index'),'resume_offset':state.get('resume_offset'),
        'revealed_rows':state.get('revealed_rows'),'revealed_sha256':state.get('revealed_sha256'),'semantic_log_sha256':state.get('semantic_log_sha256'),
        'counter_log_sha256':state.get('counter_log_sha256'),'with_parent_log_sha256':state.get('with_parent_log_sha256'),'object_log_sha256':state.get('object_log_sha256'),'action_log_sha256':state.get('action_log_sha256'),
        'price_revealed_cutoff':state.get('price_revealed_cutoff'),'information_known_at':state.get('information_known_at'),
      },
      'gate':gate,
      'market':{
        'parent':market.get('parent'),'latest_h4':market.get('latest_h4'),'latest_h1':market.get('latest_h1'),'latest_m15':market.get('latest_m15'),'latest_m5':market.get('latest_m5'),
        'current_h1_relation':market.get('current_h1_relation'),'current_m15_relation':market.get('current_m15_relation'),'last_price':market.get('last_price'),
      },
      'strategy':{
        'branch':gate.get('branch'),'lane_key':lane.get('lane_key'),'context':lane.get('context'),'child':lane.get('active_child'),
        'hard_guard':{'origin_boundary':child.get('origin_boundary'),'side':child.get('side'),'state':child.get('state'),'guard_remains_authoritative':bool(child)},
        'execution_zone':{'zone_id':child.get('zone_id'),'zone_low':child.get('zone_low'),'zone_high':child.get('zone_high')},
        'journey_review':{'journey_role':child.get('journey_role'),'launch_anchor':child.get('launch_anchor'),'launch_anchor_at':child.get('launch_anchor_at'),'launch_touch_at':child.get('launch_touch_at'),'launch_damage_at':child.get('launch_damage_at'),'review_reason':child.get('review_reason')},
      },
    }

def response_contract(gate_kind:str)->dict:
    if gate_kind=='REVIEW_REQUIRED':
        return {'decision':['HOLD','EXIT','REMAP'],'remap_fields':'not accepted at REVIEW_REQUIRED; REMAP creates a new REMAP_REQUIRED gate'}
    if gate_kind=='REMAP_REQUIRED':
        return {'decision':['EXIT','REMAP'],'REMAP_requires':['new_parent_id','new_parent_side','journey_role'],'new_parent_side':['UP','DOWN']}
    raise ProtocolError('response contract requested for non-AI gate')

def build_ai_request(state:dict)->dict:
    gates=state.get('pending_gates') or []
    if not gates:raise ProtocolError('no pending gate')
    gate=gates[0]
    if route_gate(gate)!='AI_DECISION':raise ProtocolError(f'first gate {gate.get("kind")} is not an AI gate')
    basis=_decision_basis(state,gate);fp=digest(basis)
    request_id=hashlib.sha256((REQUEST_VERSION+'|'+gate['gate_id']+'|'+fp).encode()).hexdigest()[:32]
    return {
      'version':REQUEST_VERSION,'scheduler_version':SCHEDULER_VERSION,'request_id':request_id,'request_fingerprint':fp,'gate_id':gate['gate_id'],'gate_kind':gate['kind'],
      'known_at':gate['known_at'],'price_revealed_cutoff':gate.get('price_revealed_cutoff'),'information_known_at':gate.get('information_known_at'),
      'decision_context':basis,'response_contract':response_contract(gate['kind']),
      'staleness_policy':{
        'version':STALENESS_VERSION,'mode':'STRUCTURAL_EXACT','elapsed_market_time_threshold':None,
        'valid_iff':['same first pending gate_id','same request_fingerprint','same causal-prefix hashes/clocks','same Child/Parent/context snapshot'],
        'on_mismatch':'REJECT_RESPONSE_AND_REBUILD_REQUEST',
      },
      'service_outage_policy':{
        'version':OUTAGE_VERSION,'mode':'FAIL_STOP_GUARDED','implicit_market_decision':None,'allow_new_risk':False,'advance_semantic_replay_while_unresolved':False,
        'hard_sl':'PRECOMMITTED_HARD_SL_REMAINS_EXTERNAL/RUNTIME_AUTHORITY','note':'No timeout, cooldown, forced exit, or implicit hold is invented.'
      },
    }

def scheduler_disposition(state:dict)->dict:
    gates=state.get('pending_gates') or []
    if not gates:return {'scheduler_version':SCHEDULER_VERSION,'route':'NO_GATE'}
    g=gates[0];route=route_gate(g)
    z={'scheduler_version':SCHEDULER_VERSION,'route':route,'gate_id':g.get('gate_id'),'gate_kind':g.get('kind')}
    if route=='AI_DECISION':z['request']=build_ai_request(state)
    elif route=='DETERMINISTIC_FAIL_CLOSED':z['action']=deterministic_gate_action(g)
    return z

def outage_record(request:dict,error:Optional[str]=None)->dict:
    return {'version':OUTAGE_VERSION,'request_id':request['request_id'],'request_fingerprint':request['request_fingerprint'],'gate_id':request['gate_id'],
            'result':'FAIL_STOP_GUARDED','runtime_action':None,'allow_new_risk':False,'advance_semantic_replay':False,
            'hard_sl':'REMAINS_AUTHORITATIVE','error':error}

def validate_ai_response(request:dict,response:dict,current_request:Optional[dict]=None)->dict:
    if request.get('version')!=REQUEST_VERSION:raise ProtocolError('unsupported request version')
    if response.get('version')!=RESPONSE_VERSION:raise ProtocolError('unsupported response version')
    for k in ('request_id','request_fingerprint','gate_id'):
        if response.get(k)!=request.get(k):raise ProtocolError(f'response {k} does not match request')
    if current_request is not None:
        if current_request.get('request_id')!=request.get('request_id') or current_request.get('request_fingerprint')!=request.get('request_fingerprint') or current_request.get('gate_id')!=request.get('gate_id'):
            raise ProtocolError('stale AI response: current causal state/gate no longer matches request')
    decision=str(response.get('decision','')).upper(); kind=request['gate_kind']
    allowed=response_contract(kind)['decision']
    if decision not in allowed:raise ProtocolError(f'decision {decision!r} not allowed for {kind}')
    base={'child_id':request['decision_context']['gate'].get('child_id'),'at':request['known_at'],'block':request['decision_context']['gate']['block']}
    if kind=='REVIEW_REQUIRED':
        return {'kind':'REVIEW_DECISION',**base,'decision':decision}
    if kind=='REMAP_REQUIRED':
        if decision=='EXIT':return {'kind':'REVIEW_DECISION',**base,'decision':'EXIT'}
        np=response.get('new_parent_id');ns=response.get('new_parent_side');jr=response.get('journey_role')
        if not np or ns not in ('UP','DOWN') or not jr:raise ProtocolError('REMAP response requires new_parent_id, new_parent_side UP/DOWN, and journey_role')
        return {'kind':'REMAP_RESULT',**base,'new_parent_id':np,'new_parent_side':ns,'journey_role':jr}
    raise ProtocolError('unreachable AI gate')

def _load(path:Path):return json.loads(path.read_text(encoding='utf-8'))
def _write(path:Path,obj:dict):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True)
    x=sp.add_parser('packet');x.add_argument('--state',type=Path,required=True);x.add_argument('--out',type=Path,required=True)
    x=sp.add_parser('validate-response');x.add_argument('--state',type=Path,required=True);x.add_argument('--request',type=Path,required=True);x.add_argument('--response',type=Path,required=True);x.add_argument('--out-action',type=Path,required=True)
    x=sp.add_parser('outage');x.add_argument('--request',type=Path,required=True);x.add_argument('--out',type=Path,required=True);x.add_argument('--error')
    a=p.parse_args()
    if a.cmd=='packet':_write(a.out,scheduler_disposition(_load(a.state)))
    elif a.cmd=='validate-response':
        st=_load(a.state);cur=build_ai_request(st);_write(a.out_action,validate_ai_response(_load(a.request),_load(a.response),cur))
    elif a.cmd=='outage':_write(a.out,outage_record(_load(a.request),a.error))
if __name__=='__main__':main()
