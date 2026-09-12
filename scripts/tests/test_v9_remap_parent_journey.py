from datetime import datetime
from types import SimpleNamespace
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from v9_strategy_state_machine import StrategyObserver, Child
from v9_semantic_runtime import CompletedBar, M1Row, Parent, SemanticEvent


def t(s): return datetime.strptime(s,'%Y-%m-%d %H:%M:%S')

def market(parent_side='DOWN', h1='DOWN', m15='DOWN', cutoff='2025-01-02 10:14:00'):
    return SimpleNamespace(
        parent=Parent('P2','2025H1',parent_side,t('2025-01-02 08:00:00')),
        latest_h1=SimpleNamespace(consensus=h1),
        latest_m15=SimpleNamespace(consensus=m15),
        price_revealed_cutoff=t(cutoff),
        last_price=M1Row(t(cutoff),99,100,98,99),
    )

def remapped_child():
    return Child(
        'C1','COUNTER','DOWN','P2','DOWN',t('2025-01-02 09:00:00'),105.0,
        'Z1',101,102,state='OPEN',journey_role='WITH_NEW_PARENT_JOURNEY',
        launch_anchor=100.0,launch_anchor_at=t('2025-01-02 10:00:00')
    )

# 1. A Counter-origin Child remapped into a DOWN Parent journey must NOT treat
# favorable DOWN continuation below the launch anchor as damage.
o=StrategyObserver(independent_lanes=True); l=o.counter; l.active=remapped_child()
l.parent_id='P2'; l.parent_side='DOWN'; l.h1_relation='ALIGNED'; l.m15_relation='ALIGNED'
b=CompletedBar('2025H1',15,t('2025-01-02 10:00:00'),t('2025-01-02 10:15:00'),t('2025-01-02 10:14:00'),100,101,98,99,15)
l.process_batch(t('2025-01-02 10:15:00'),[],[b],market(),)
assert l.active is not None and l.active.state=='OPEN'
assert not any(e.kind in ('MATERIAL_CHILD_DAMAGE','REVIEW_REQUIRED') for e in l.events)

# 2. The same remapped DOWN journey must treat a completed M15 close ABOVE the
# launch anchor as material damage, i.e. same-direction Parent-journey semantics.
o=StrategyObserver(independent_lanes=True); l=o.counter; l.active=remapped_child()
l.parent_id='P2'; l.parent_side='DOWN'; l.h1_relation='ALIGNED'; l.m15_relation='ALIGNED'
b=CompletedBar('2025H1',15,t('2025-01-02 10:00:00'),t('2025-01-02 10:15:00'),t('2025-01-02 10:14:00'),99,102,98,101,15)
l.process_batch(t('2025-01-02 10:15:00'),[],[b],market(),)
assert l.active is not None and l.active.state=='REVIEW_REQUIRED'
assert [e.kind for e in l.events][-2:]==['MATERIAL_CHILD_DAMAGE','REVIEW_REQUIRED']

# 3. Parent-loss events must use their causal event block, not infer a block from
# the authorization year. This is behaviorally identical for frozen 2025/2026 blocks
# and makes the state machine portable to an OOS block.
o=StrategyObserver(independent_lanes=True); l=o.counter
c=Child('C2','COUNTER','DOWN','P1','UP',t('2024-02-01 09:00:00'),105,'Z2',101,102,state='OPEN')
l.active=c;l.parent_id='P1';l.parent_side='UP';l.h1_relation='ALIGNED';l.m15_relation='COUNTERFLOW'
ev=SemanticEvent(1,'PARENT_AUTHORITY_LOST',t('2024-02-01 12:00:00'),t('2024-02-01 11:59:00'),'2024OOS',parent_id='P1',parent_side='UP')
m=SimpleNamespace(parent=None,latest_h1=None,latest_m15=None,price_revealed_cutoff=t('2024-02-01 11:59:00'),last_price=M1Row(t('2024-02-01 11:59:00'),1,1,1,1))
l.process_batch(t('2024-02-01 12:00:00'),[ev],[],m)
assert l.events[0].kind=='REMAP_REQUIRED' and l.events[0].block=='2024OOS'

print('PASS: 3 remapped-parent-journey portability cases')
