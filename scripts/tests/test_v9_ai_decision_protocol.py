import copy, json, pytest
from v9_ai_decision_protocol import *

def state(kind='REVIEW_REQUIRED'):
    gate={'gate_id':'g1','kind':kind,'known_at':'2025-01-17 14:30:00','price_revealed_cutoff':'2025-01-17 14:29:00','information_known_at':'2025-01-17 14:30:00','block':'2025H1','branch':'WITH_PARENT','child_id':'C1','parent_id':'P1','side':'UP','payload':{'reason':'X'}}
    child={'child_id':'C1','state':'REVIEW_REQUIRED' if kind=='REVIEW_REQUIRED' else 'REMAP_REQUIRED','side':'UP','origin_boundary':2600.0,'zone_id':'Z1','zone_low':2610.0,'zone_high':2612.0,'journey_role':'PARENT_JOURNEY','launch_anchor':2620.0,'launch_anchor_at':'2025-01-17 14:00:00','launch_touch_at':None,'launch_damage_at':'2025-01-17 14:30:00','review_reason':'X'}
    return {'version':2,'runner_version':'r3','strategy_runtime_version':'s1','authorization_version':'a1','source_basename':'m1.csv','source_sha256':'src','range_index':0,'resume_offset':123,'revealed_rows':10,'revealed_sha256':'rv','semantic_log_sha256':'sl','counter_log_sha256':'cl','with_parent_log_sha256':'wl','object_log_sha256':'ol','action_log_sha256':'al','price_revealed_cutoff':'2025-01-17 14:29:00','information_known_at':'2025-01-17 14:30:00','pending_gates':[gate],
            'market':{'parent':{'parent_id':'P1','side':'UP'},'latest_h4':{'side':'UP'},'latest_h1':{'consensus':'DOWN'},'latest_m15':{'consensus':'UP'},'latest_m5':{'consensus':'UP'},'current_h1_relation':'INTERRUPT','current_m15_relation':'WITH_PARENT','last_price':{'ts':'2025-01-17 14:29:00','close':2615.0}},
            'strategy':{'counter':{'active':None,'context':None},'with_parent':{'active':child,'context':{'kind':'INTERRUPT','parent_id':'P1'}}}}

def response(req,decision='EXIT',**kw):
    return {'version':RESPONSE_VERSION,'request_id':req['request_id'],'request_fingerprint':req['request_fingerprint'],'gate_id':req['gate_id'],'decision':decision,**kw}

def test_scheduler_routes():
    s=state();assert scheduler_disposition(s)['route']=='AI_DECISION'
    for k,r in [('ENTRY_EXECUTION_REQUIRED','EXECUTION_ADAPTER'),('EXIT_EXECUTION_REQUIRED','EXECUTION_ADAPTER'),('CROSS_LANE_CONFLICT_REVIEW','DETERMINISTIC_FAIL_CLOSED')]:
        q=state();q['pending_gates'][0]['kind']=k;assert scheduler_disposition(q)['route']==r

def test_packet_deterministic():
    s=state();a=build_ai_request(s);b=build_ai_request(copy.deepcopy(s));assert a==b

def test_fingerprint_changes_on_prefix_or_child_change():
    s=state();a=build_ai_request(s);s['revealed_sha256']='changed';b=build_ai_request(s);assert a['request_fingerprint']!=b['request_fingerprint']
    s=state();a=build_ai_request(s);s['strategy']['with_parent']['active']['launch_anchor']=999;assert a['request_fingerprint']!=build_ai_request(s)['request_fingerprint']

def test_review_response_maps_strictly():
    s=state();req=build_ai_request(s);a=validate_ai_response(req,response(req,'HOLD'),build_ai_request(s));assert a['kind']=='REVIEW_DECISION' and a['decision']=='HOLD'
    assert validate_ai_response(req,response(req,'REMAP'),build_ai_request(s))['decision']=='REMAP'

def test_remap_response_requires_fields():
    s=state('REMAP_REQUIRED');req=build_ai_request(s)
    with pytest.raises(ProtocolError):validate_ai_response(req,response(req,'REMAP'),build_ai_request(s))
    a=validate_ai_response(req,response(req,'REMAP',new_parent_id='P2',new_parent_side='DOWN',journey_role='PARENT_JOURNEY'),build_ai_request(s));assert a['kind']=='REMAP_RESULT'

def test_stale_response_rejected():
    s=state();req=build_ai_request(s);resp=response(req,'EXIT');s['action_log_sha256']='new';cur=build_ai_request(s)
    with pytest.raises(ProtocolError):validate_ai_response(req,resp,cur)

def test_outage_is_not_market_decision():
    req=build_ai_request(state());o=outage_record(req,'service down');assert o['runtime_action'] is None and not o['allow_new_risk'] and not o['advance_semantic_replay'] and o['hard_sl']=='REMAINS_AUTHORITATIVE'

def test_cross_lane_only_skip():
    q=state();q['pending_gates'][0]['kind']='CROSS_LANE_CONFLICT_REVIEW';a=deterministic_gate_action(q['pending_gates'][0]);assert a['decision']=='SKIP_NEW_PITCH'
