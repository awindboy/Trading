from datetime import datetime
from types import SimpleNamespace
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from v9_strategy_state_machine import StrategyObserver,Child
from v9_semantic_runtime import M1Row,Parent,SemanticEvent

def t(s):return datetime.strptime(s,'%Y-%m-%d %H:%M:%S')
def child(state='PENDING',side='UP'):
 return Child('T-C1','WITH_PARENT',side,'P1','UP',t('2025-01-02 10:00:00'),100.0,'Z1',99.0,101.0,state=state,launch_anchor=101.0,launch_anchor_at=t('2025-01-02 11:00:00'))

def kinds(l):return [e.kind for e in l.events]

# 1 pending origin+zone same M1 => fail closed, no entry request.
o=StrategyObserver(independent_lanes=True);l=o.with_parent;l.active=child('PENDING','UP')
l.on_price(M1Row(t('2025-01-02 10:01:00'),100,102,99,101),'2025H1',SimpleNamespace())
assert l.active is None and kinds(l)==['CHILD_CANCELLED']
assert l.events[-1].payload['reason']=='INTRAMINUTE_ORIGIN_AND_ZONE_AMBIGUOUS'

# 2 Hard SL/origin has priority over launch-anchor review on same M1.
o=StrategyObserver(independent_lanes=True);l=o.with_parent;l.active=child('OPEN','UP')
l.on_price(M1Row(t('2025-01-02 11:01:00'),102,103,99,100),'2025H1',SimpleNamespace())
assert l.active is None and kinds(l)==['CHILD_DEAD'],kinds(l)

# 3 Zone touch alone requires execution report and does not auto fill.
o=StrategyObserver(independent_lanes=True);l=o.with_parent;c=child('PENDING','UP');c.origin_boundary=95;c.zone_low=99;c.zone_high=101;l.active=c
l.on_price(M1Row(t('2025-01-02 10:01:00'),102,102,100,100.5),'2025H1',SimpleNamespace())
assert l.active.state=='AWAITING_EXECUTION' and kinds(l)==['ENTRY_EXECUTION_REQUIRED']

# 4 EXIT review decision only requests execution; Hard SL remains guarded before report.
l.apply_review_decision(c.child_id,t('2025-01-02 10:01:00'),'EXIT','2025H1',t('2025-01-02 10:01:00')) if False else None
# use OPEN/REVIEW Child instead
o=StrategyObserver(independent_lanes=True);l=o.with_parent;c=child('REVIEW_REQUIRED','UP');c.origin_boundary=100;l.active=c
l.apply_review_decision(c.child_id,t('2025-01-02 11:00:00'),'EXIT','2025H1',t('2025-01-02 10:59:00'))
assert l.active.state=='EXIT_REQUESTED' and kinds(l)==['EXIT_EXECUTION_REQUIRED']
l.on_price(M1Row(t('2025-01-02 11:01:00'),101,102,99,100),'2025H1',SimpleNamespace())
assert l.active is None and kinds(l)[-1]=='CHILD_DEAD'

# 5 Parent authority loss cancels pending before any later price event.
o=StrategyObserver(independent_lanes=True);l=o.with_parent;c=child('PENDING','UP');l.active=c;l.parent_id='P1';l.parent_side='UP';l.h1_relation='INTERRUPT';l.m15_relation='COUNTERFLOW'
new_parent=Parent('P2','2025H1','DOWN',t('2025-01-02 12:00:00'))
m=SimpleNamespace(parent=new_parent,latest_h1=SimpleNamespace(consensus='DOWN'),latest_m15=SimpleNamespace(consensus='DOWN'),price_revealed_cutoff=t('2025-01-02 11:59:00'),last_price=M1Row(t('2025-01-02 11:59:00'),1,1,1,1))
ev=SemanticEvent(1,'PARENT_AUTHORITY_LOST',t('2025-01-02 12:00:00'),t('2025-01-02 11:59:00'),'2025H1',parent_id='P1',parent_side='UP')
l.process_batch(t('2025-01-02 12:00:00'),[ev],[],m)
assert l.active is None and l.events[0].kind=='CHILD_CANCELLED' and l.events[0].payload['reason']=='PARENT_AUTHORITY_LOST_PREFILL'

# 6 Parent authority loss on OPEN does not invent exit; it enters REMAP_REQUIRED and remains SL-guarded.
o=StrategyObserver(independent_lanes=True);l=o.counter;c=Child('T-C2','COUNTER','DOWN','P1','UP',t('2025-01-02 10:00:00'),105.0,'Z2',100,102,state='OPEN');l.active=c;l.parent_id='P1';l.parent_side='UP';l.h1_relation='ALIGNED';l.m15_relation='COUNTERFLOW'
l.process_batch(t('2025-01-02 12:00:00'),[ev],[],m)
assert l.active is not None and l.active.state=='REMAP_REQUIRED' and l.events[0].kind=='REMAP_REQUIRED'
l.on_price(M1Row(t('2025-01-02 12:01:00'),104,106,103,105),'2025H1',SimpleNamespace())
assert l.active is None and l.events[-1].kind=='CHILD_DEAD'
print('PASS: 6 deterministic priority cases')
