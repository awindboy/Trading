from datetime import datetime
from types import SimpleNamespace
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from v9_strategy_state_machine import StrategyObserver,Child
from v9_execution_state_machine import M5Object
from v9_semantic_runtime import CompletedBar,M1Row,Parent
from v9_runtime_state_v2 import V2Runner

def t(s): return datetime.strptime(s,'%Y-%m-%d %H:%M:%S')

# 1. Same-known-at opposite arm intents: no lane receives hidden code-order priority.
o=StrategyObserver(independent_lanes=False)
z1=M5Object('ZC','2025H1','FVG','BEAR',t('2025-01-02 10:00:00'),t('2025-01-02 10:04:00'),t('2025-01-02 10:05:00'),100,101)
z2=M5Object('ZW','2025H1','FVG','BULL',t('2025-01-02 10:00:00'),t('2025-01-02 10:04:00'),t('2025-01-02 10:05:00'),99,100)
o.request_arm(o.counter,t('2025-01-02 10:15:00'),'2025H1','P1','UP','DOWN',105,z1,t('2025-01-02 10:14:00'),'FIRST')
o.request_arm(o.with_parent,t('2025-01-02 10:15:00'),'2025H1','P1','UP','UP',95,z2,t('2025-01-02 10:14:00'),'FIRST')
o._resolve_arm_intents(t('2025-01-02 10:15:00'))
assert o.counter.active is None and o.with_parent.active is None
all_events=o.counter.events+o.with_parent.events
assert sum(e.kind=='CROSS_LANE_CONFLICT_REVIEW' for e in all_events)==1
ce=next(e for e in all_events if e.kind=='CROSS_LANE_CONFLICT_REVIEW')
assert ce.payload['conflict_scope']=='SIMULTANEOUS_AUTHORIZATION'

# 2. One launch anchor can create material-damage review only once after HOLD.
o=StrategyObserver(independent_lanes=True);l=o.with_parent
c=Child('C1','WITH_PARENT','UP','P1','UP',t('2025-01-02 09:00:00'),95,'Z',96,97,state='OPEN',launch_anchor=101,launch_anchor_at=t('2025-01-02 10:00:00'))
l.active=c;l.parent_id='P1';l.parent_side='UP';l.h1_relation='ALIGNED';l.m15_relation='ALIGNED'
m=SimpleNamespace(parent=Parent('P1','2025H1','UP',t('2025-01-01 00:00:00')),latest_h1=SimpleNamespace(consensus='UP'),latest_m15=SimpleNamespace(consensus='UP'),price_revealed_cutoff=t('2025-01-02 10:14:00'),last_price=M1Row(t('2025-01-02 10:14:00'),100,100,100,100))
b1=CompletedBar('2025H1',15,t('2025-01-02 10:00:00'),t('2025-01-02 10:15:00'),t('2025-01-02 10:14:00'),102,103,99,100,15)
l.process_batch(t('2025-01-02 10:15:00'),[],[b1],m)
assert l.active.state=='REVIEW_REQUIRED' and l.active.launch_damage_at==t('2025-01-02 10:15:00')
assert [e.kind for e in l.events].count('REVIEW_REQUIRED')==1
l.apply_review_decision('C1',t('2025-01-02 10:15:00'),'HOLD','2025H1',t('2025-01-02 10:14:00'))
m.price_revealed_cutoff=t('2025-01-02 10:29:00');m.last_price=M1Row(t('2025-01-02 10:29:00'),99,99,99,99)
b2=CompletedBar('2025H1',15,t('2025-01-02 10:15:00'),t('2025-01-02 10:30:00'),t('2025-01-02 10:29:00'),100,101,98,99,15)
l.process_batch(t('2025-01-02 10:30:00'),[],[b2],m)
assert l.active.state=='OPEN'
assert [e.kind for e in l.events].count('REVIEW_REQUIRED')==1

# 3. Gate capture appends action-created gate behind an already pending gate.
r=V2Runner.__new__(V2Runner);r.pending_gates=[{'gate_id':'OLD'}];r.observer=StrategyObserver(independent_lanes=True)
r.market=SimpleNamespace(information_known_at=t('2025-01-02 11:00:00'),price_revealed_cutoff=t('2025-01-02 10:59:00'),parent=None,latest_h1=None,latest_m15=None)
r.observer.counter.emit('EXIT_EXECUTION_REQUIRED',t('2025-01-02 11:00:00'),'2025H1',parent_id='P1',side='UP',cutoff=t('2025-01-02 10:59:00'))
assert r._capture_gates() and len(r.pending_gates)==2 and r.pending_gates[1]['kind']=='EXIT_EXECUTION_REQUIRED'

print('PASS: 3 gate/runtime edge cases')
