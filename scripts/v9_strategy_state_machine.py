#!/usr/bin/env python3
"""V9 live-safe Parent/Child strategy state machine over causal semantic runtime.

The semantic runtime owns market facts.  This layer owns pitch/Child lifecycle only.
It never selects a signal because of a later H1 outcome.

Default live-safe behavior is fail-closed:
- a precommitted M5 zone touch emits ENTRY_EXECUTION_REQUIRED; it is not a fill;
- material launch-anchor damage emits REVIEW_REQUIRED; it is not a stale-price exit;
- cross-lane overlap emits CROSS_LANE_CONFLICT_REVIEW; no hedge/netting rule is invented.

`--research-assume-zone-touch-fill` is consumed-data parity tooling only.  It does not
create production fill-price authority.
"""
from __future__ import annotations
import argparse,csv,json,math
from dataclasses import dataclass,asdict,field
from datetime import datetime
from pathlib import Path
from typing import Optional

from v9_semantic_runtime import (
    AUTHORITATIVE_SHA256, BLOCK_END, CompletedBar, MarketMachine, M1Row,
    RawM1Feed, SemanticEvent, fmt,
)
from v9_execution_state_machine import M5ObjectBook, M5Object

STRATEGY_RUNTIME_VERSION="v9-strategy-state-machine-5"
AUTHORIZATION_VERSION="v9-live-safe-continuous-context-2"

INTERRUPT_REL={"COUNTERFLOW","LOCAL_BALANCE"}

@dataclass
class Context:
    kind:str                 # ALIGNED or INTERRUPT
    block:str
    parent_id:str
    parent_side:str
    start:datetime
    initial_m15:str
    first_pitch_allowed:bool
    first_pitch_consumed:bool=False
    high:Optional[float]=None
    low:Optional[float]=None

@dataclass
class Child:
    child_id:str
    branch:str               # COUNTER / WITH_PARENT
    side:str
    parent_id:str
    parent_side:str
    authorized_at:datetime
    origin_boundary:float
    zone_id:str
    zone_low:float
    zone_high:float
    state:str="PENDING"     # PENDING/AWAITING_EXECUTION/OPEN/REVIEW_REQUIRED/REMAP_REQUIRED/EXIT_REQUESTED
    entry_trigger_at:Optional[datetime]=None
    fill_at:Optional[datetime]=None
    fill_price:Optional[float]=None
    journey_role:str="LOCAL_BRIDGE"
    launch_anchor:Optional[float]=None
    launch_anchor_at:Optional[datetime]=None
    launch_touch_at:Optional[datetime]=None
    launch_damage_at:Optional[datetime]=None
    launch_damage_reviewed:bool=False
    review_reason:Optional[str]=None
    terminal_at:Optional[datetime]=None
    terminal_reason:Optional[str]=None

@dataclass
class Event:
    seq:int; kind:str; known_at:datetime; block:str; branch:str
    child_id:Optional[str]=None; parent_id:Optional[str]=None; side:Optional[str]=None
    price_revealed_cutoff:Optional[datetime]=None; payload:dict=field(default_factory=dict)
    def row(self):
        d=asdict(self);d['known_at']=fmt(self.known_at);d['price_revealed_cutoff']=fmt(self.price_revealed_cutoff)
        d['payload']=json.dumps(self.payload,sort_keys=True,separators=(',',':'));return d

class Lane:
    def __init__(self,branch:str,book:M5ObjectBook,owner:'StrategyObserver'):
        self.branch=branch;self.book=book;self.owner=owner
        self.context:Optional[Context]=None
        self.active:Optional[Child]=None
        self.children:list[Child]=[];self.events:list[Event]=[];self.seq=0;self.child_seq=0
        self.parent_id:Optional[str]=None;self.parent_side:Optional[str]=None
        self.h1_relation:Optional[str]=None;self.m15_relation:Optional[str]=None
        self.first_auth_rows:list[dict]=[]

    def emit(self,kind,at,block,child:Optional[Child]=None,cutoff=None,**payload):
        self.seq+=1
        e=Event(self.seq,kind,at,block,self.branch,child.child_id if child else None,
                child.parent_id if child else payload.pop('parent_id',None),
                child.side if child else payload.pop('side',None),cutoff,payload)
        self.events.append(e);return e

    @staticmethod
    def relation(consensus:Optional[str],side:Optional[str])->str:
        if side not in ('UP','DOWN') or consensus is None:return 'NO_PARENT'
        if consensus==side:return 'ALIGNED'
        if consensus in ('UP','DOWN'):return 'COUNTERFLOW'
        if consensus=='BALANCE':return 'LOCAL_BALANCE'
        if consensus=='WARMUP':return 'WARMUP'
        return 'UNRESOLVED'

    @staticmethod
    def h1_core(relation:str)->str:
        """Trading-state compression: COUNTERFLOW and LOCAL_BALANCE are one H1 INTERRUPT.

        Atlas run segmentation may still distinguish the descriptive relations, but the
        Child lifecycle must not restart merely because H1 oscillates inside the same
        interruption.
        """
        if relation=='ALIGNED': return 'ALIGNED'
        if relation in INTERRUPT_REL: return 'INTERRUPT'
        if relation=='NO_PARENT': return 'NO_PARENT'
        if relation=='WARMUP': return 'WARMUP'
        return 'UNRESOLVED'

    def _effective(self,m:MarketMachine):
        if m.parent is None:return None,None,'NO_PARENT','NO_PARENT'
        pid,side=m.parent.parent_id,m.parent.side
        # H1 grammar intentionally compresses every non-directional H1 consensus
        # (BALANCE or AMBIGUOUS) into LOCAL_BALANCE while H4/Parent is directional.
        # M15 keeps AMBIGUOUS/other disagreement as UNRESOLVED.
        if m.latest_h1 is None:
            h1_raw='NO_PARENT'
        elif m.latest_h1.consensus==side:
            h1_raw='ALIGNED'
        elif m.latest_h1.consensus in ('UP','DOWN'):
            h1_raw='COUNTERFLOW'
        elif m.latest_h1.consensus=='WARMUP':
            h1_raw='WARMUP'
        else:
            h1_raw='LOCAL_BALANCE'
        m15=self.relation(m.latest_m15.consensus if m.latest_m15 else None,side)
        return pid,side,self.h1_core(h1_raw),m15

    def _start_context(self,kind,at,block,pid,side,m15):
        target='COUNTERFLOW' if kind=='ALIGNED' else 'ALIGNED'
        self.context=Context(kind,block,pid,side,at,m15,m15!=target)
        self.emit(f'{kind}_CONTEXT_STARTED',at,block,parent_id=pid,side=side,initial_m15=m15)

    def _end_context(self,at,block,reason):
        if self.context:
            self.emit(f'{self.context.kind}_CONTEXT_ENDED',at,block,parent_id=self.context.parent_id,
                      side=self.context.parent_side,reason=reason)
        self.context=None

    def _origin(self)->Optional[float]:
        c=self.context
        if c is None or c.high is None or c.low is None:return None
        if self.branch=='COUNTER':
            return c.high if c.parent_side=='UP' else c.low
        return c.low if c.parent_side=='UP' else c.high

    def _target_relation(self):return 'COUNTERFLOW' if self.branch=='COUNTER' else 'ALIGNED'

    def _context_authorizes(self)->bool:
        return self.context is not None and (
            (self.branch=='COUNTER' and self.context.kind=='ALIGNED') or
            (self.branch=='WITH_PARENT' and self.context.kind=='INTERRUPT')
        )

    def _archive(self,c:Child,state,at,reason,block,cutoff=None):
        c.state=state;c.terminal_at=at;c.terminal_reason=reason;self.children.append(c)
        self.emit(state,at,block,c,cutoff=cutoff,reason=reason);self.active=None

    def _authorize(self,at,block,pid,pside,last_price,cutoff,auth_class):
        ctx=self.context
        if ctx is None or ctx.parent_id!=pid:return
        origin=self._origin()
        side=pside if self.branch=='WITH_PARENT' else ('DOWN' if pside=='UP' else 'UP')
        self.emit('PITCH_AUTHORIZED',at,block,parent_id=pid,side=side,cutoff=cutoff,
                  auth_class=auth_class,context_start=fmt(ctx.start),origin_boundary=origin)
        if auth_class=='FIRST':
            self.first_auth_rows.append({'block':block,'parent_id':pid,'side':pside,'context_start':ctx.start,'signal_at':at})
        if self.active is not None:
            self.emit('PITCH_NOT_ARMED_ACTIVE_CHILD',at,block,parent_id=pid,side=side,cutoff=cutoff,active_child=self.active.child_id);return
        if origin is None or last_price is None or not math.isfinite(origin):
            self.emit('PITCH_NO_ORIGIN',at,block,parent_id=pid,side=side,cutoff=cutoff);return
        direction='BULL' if side=='UP' else 'BEAR'
        zone=self.book.latest_zone(direction,last_price,at)
        if zone is None:
            self.emit('PITCH_NO_GEOMETRY',at,block,parent_id=pid,side=side,cutoff=cutoff,origin=origin);return
        # Arm only after the complete same-known-at batch has been evaluated for both
        # lanes.  This prevents Python lane-call order from becoming a hidden portfolio
        # priority when opposite pitches are authorized simultaneously.
        self.owner.request_arm(self,at,block,pid,pside,side,float(origin),zone,cutoff,auth_class)

    def arm_intent(self,intent:dict):
        self.child_seq+=1;cid=f'{intent["block"]}-{self.branch[:3]}{self.child_seq:04d}'
        zone=intent['zone']
        child=Child(cid,self.branch,intent['side'],intent['parent_id'],intent['parent_side'],intent['at'],
                    intent['origin'],zone.object_id,zone.price_low,zone.price_high)
        self.active=child
        self.emit('CHILD_PENDING',intent['at'],intent['block'],child,cutoff=intent['cutoff'],
                  zone_id=zone.object_id,zone_low=zone.price_low,zone_high=zone.price_high,origin=intent['origin'])
        return child

    def process_batch(self,at:datetime,events:list[SemanticEvent],bars:list[CompletedBar],m:MarketMachine):
        pid,pside,h1,m15=self._effective(m)
        prev_pid,prev_h1,prev_m15=self.parent_id,self.h1_relation,self.m15_relation
        cutoff=m.price_revealed_cutoff
        h1bar=next((b for b in bars if b.minutes==60),None)
        m15bar=next((b for b in bars if b.minutes==15),None)
        parent_changed=(pid!=prev_pid)

        # Deterministic pre-fill invalidation / open remap when old Parent actually loses authority.
        lost=[e for e in events if e.kind=='PARENT_AUTHORITY_LOST']
        if self.active is not None and any(e.parent_id==self.active.parent_id for e in lost):
            c=self.active
            if c.state in ('PENDING','AWAITING_EXECUTION'):
                self._archive(c,'CHILD_CANCELLED',at,'PARENT_AUTHORITY_LOST_PREFILL',lost[0].block,cutoff)
            elif c.state in ('OPEN','REVIEW_REQUIRED'):
                c.state='REMAP_REQUIRED';c.review_reason='PARENT_AUTHORITY_LOST'
                self.emit('REMAP_REQUIRED',at,lost[0].block,c,cutoff=cutoff,reason='PARENT_AUTHORITY_LOST')

        if parent_changed:
            if self.context:self._end_context(at,self.context.block,'PARENT_CHANGED')
            self.parent_id,self.parent_side=pid,pside
            self.h1_relation,self.m15_relation=h1,m15
            if pid is not None:
                if h1=='ALIGNED':self._start_context('ALIGNED',at,m.parent.block,pid,pside,m15)
                elif h1=='INTERRUPT':self._start_context('INTERRUPT',at,m.parent.block,pid,pside,m15)
            # A relation under a newly earned Parent is a snapshot, not a fresh authorization.
            return

        # Actual H1 state transition; Atlas >2h run resets are intentionally ignored.
        if pid is not None and h1!=prev_h1:
            if self.context:self._end_context(at,self.context.block,'H1_RELATION_CHANGED')
            if h1=='ALIGNED':
                # With-Parent Child, including a Counter-origin Child explicitly remapped
                # into WITH_NEW_PARENT_JOURNEY, follows same-direction Parent-journey
                # semantics after the new Parent has been accepted. Historical branch
                # identity must not invert later H1/M15 damage logic.
                c=self.active
                remapped_parent_journey=(c is not None and c.journey_role=='WITH_NEW_PARENT_JOURNEY')
                if (self.branch=='WITH_PARENT' or remapped_parent_journey) and c is not None and c.parent_id==pid:
                    if c.state in ('PENDING','AWAITING_EXECUTION'):
                        self._archive(c,'CHILD_CANCELLED',at,'H1_REALIGN_PREFILL',m.parent.block,cutoff)
                    elif c.state=='OPEN' and h1bar is not None:
                        if c.journey_role!='WITH_NEW_PARENT_JOURNEY': c.journey_role='PARENT_JOURNEY'
                        c.launch_anchor=(h1bar.low if pside=='UP' else h1bar.high);c.launch_anchor_at=at
                        c.launch_touch_at=None;c.launch_damage_at=None;c.launch_damage_reviewed=False
                        self.emit('CHILD_PROMOTED_PARENT_JOURNEY',at,m.parent.block,c,cutoff=cutoff,anchor=c.launch_anchor)
                if self.branch=='COUNTER' and not remapped_parent_journey and c is not None and c.parent_id==pid:
                    if c.state in ('PENDING','AWAITING_EXECUTION'):
                        self._archive(c,'CHILD_CANCELLED',at,'H1_REALIGN_LOCAL_BRIDGE_TERMINAL_PREFILL',m.parent.block,cutoff)
                    elif c.state=='OPEN':
                        c.state='REVIEW_REQUIRED';c.review_reason='H1_REALIGN_LOCAL_BRIDGE_TERMINAL'
                        self.emit('REVIEW_REQUIRED',at,m.parent.block,c,cutoff=cutoff,reason=c.review_reason)
                self._start_context('ALIGNED',at,m.parent.block,pid,pside,m15)
            elif h1=='INTERRUPT':
                # Counter Local-Bridge gets the H1 interruption anchor. A Counter-origin
                # Child already remapped into the new Parent journey no longer uses the
                # old counter-bridge progression semantics.
                c=self.active
                remapped_parent_journey=(c is not None and c.journey_role=='WITH_NEW_PARENT_JOURNEY')
                if self.branch=='COUNTER' and not remapped_parent_journey and c is not None and c.parent_id==pid and h1bar is not None:
                    c.launch_anchor=(h1bar.high if pside=='UP' else h1bar.low);c.launch_anchor_at=at
                    c.launch_touch_at=None;c.launch_damage_at=None;c.launch_damage_reviewed=False
                    self.emit('H1_INTERRUPT_PROGRESS',at,m.parent.block,c,cutoff=cutoff,anchor=c.launch_anchor)
                self._start_context('INTERRUPT',at,m.parent.block,pid,pside,m15)

        # Fresh M15 transition after any same-time H1 context changes.  Strict start < signal.
        m15_changed=(pid is not None and m15bar is not None and m15!=prev_m15)
        if m15_changed and self._context_authorizes() and self.context.parent_id==pid and self.context.start<at:
            target=self._target_relation()
            if m15==target:
                if self.context.first_pitch_allowed and not self.context.first_pitch_consumed:
                    self.context.first_pitch_consumed=True
                    self._authorize(at,m.parent.block,pid,pside,m.last_price.close if m.last_price else None,cutoff,'FIRST')
                elif self.context.first_pitch_consumed and self.active is None:
                    self._authorize(at,m.parent.block,pid,pside,m.last_price.close if m.last_price else None,cutoff,'FRESH_REAUTH')
                elif not self.context.first_pitch_allowed and not self.context.first_pitch_consumed:
                    # Initial target state existed at context start.  The frozen draft did not authorize
                    # this class as an initial pitch; keep it explicit rather than silently expanding authority.
                    self.emit('INITIAL_TARGET_CONTEXT_REENTRY_REVIEW',at,m.parent.block,parent_id=pid,
                              side=pside,cutoff=cutoff,context_start=fmt(self.context.start),target=target)

        # M15 close damage is evaluated after same-time H1 anchor creation and authorization semantics.
        c=self.active
        if c is not None and c.launch_anchor is not None and m15bar is not None and c.state in ('PENDING','AWAITING_EXECUTION','OPEN') and c.launch_damage_at is None:
            same_parent_journey=(c.branch=='WITH_PARENT' or c.journey_role=='WITH_NEW_PARENT_JOURNEY')
            if same_parent_journey: damage=(m15bar.close<c.launch_anchor) if c.parent_side=='UP' else (m15bar.close>c.launch_anchor)
            else: damage=(m15bar.close>c.launch_anchor) if c.parent_side=='UP' else (m15bar.close<c.launch_anchor)
            if damage:
                c.launch_damage_at=at
                if c.state in ('PENDING','AWAITING_EXECUTION'):
                    self._archive(c,'CHILD_CANCELLED',at,'M15_CLOSE_BEYOND_LAUNCH_ANCHOR_PREFILL',m.parent.block,cutoff)
                else:
                    c.state='REVIEW_REQUIRED';c.review_reason='M15_CLOSE_BEYOND_LAUNCH_ANCHOR'
                    self.emit('MATERIAL_CHILD_DAMAGE',at,m.parent.block,c,cutoff=cutoff,anchor=c.launch_anchor,close=m15bar.close)
                    self.emit('REVIEW_REQUIRED',at,m.parent.block,c,cutoff=cutoff,reason=c.review_reason)

        self.parent_id,self.parent_side=pid,pside;self.h1_relation,self.m15_relation=h1,m15

    def on_price(self,row:M1Row,block:str,m:MarketMachine):
        # Context extrema use only actually revealed M1 after context start.
        if self.context is not None and row.ts>=self.context.start:
            self.context.high=row.high if self.context.high is None else max(self.context.high,row.high)
            self.context.low=row.low if self.context.low is None else min(self.context.low,row.low)
        c=self.active
        if c is None:return
        origin_break=(row.low<c.origin_boundary) if c.side=='UP' else (row.high>c.origin_boundary)
        zone_touch=(row.high>=c.zone_low and row.low<=c.zone_high)
        # Hard structural falsification has priority over discretionary review evidence
        # on the same revealed M1 row.  Do not call review for a Child that is already dead.
        if c.state in ('OPEN','REVIEW_REQUIRED','REMAP_REQUIRED','EXIT_REQUESTED') and origin_break:
            self._archive(c,'CHILD_DEAD',row.ts,'ORIGIN_INVALIDATED',block,row.ts);return
        # Launch-anchor M1 touch is review evidence, not automatic terminal authority.
        if c.state in ('OPEN','REVIEW_REQUIRED','REMAP_REQUIRED') and c.launch_anchor is not None and c.launch_touch_at is None:
            hit=(row.low<=c.launch_anchor) if c.side=='UP' else (row.high>=c.launch_anchor)
            if hit:
                c.launch_touch_at=row.ts;self.emit('LAUNCH_ANCHOR_TOUCHED',row.ts,block,c,cutoff=row.ts,anchor=c.launch_anchor)
        if c.state=='PENDING':
            if origin_break and zone_touch:
                self._archive(c,'CHILD_CANCELLED',row.ts,'INTRAMINUTE_ORIGIN_AND_ZONE_AMBIGUOUS',block,row.ts);return
            if origin_break:
                self._archive(c,'CHILD_CANCELLED',row.ts,'ORIGIN_INVALIDATED_PREFILL',block,row.ts);return
            if zone_touch:
                c.entry_trigger_at=row.ts
                if self.owner.research_assume_zone_touch_fill:
                    c.state='OPEN';c.fill_at=row.ts
                    self.emit('RESEARCH_ZONE_TOUCH_FILL',row.ts,block,c,cutoff=row.ts,fill_price_authority='NONE')
                else:
                    c.state='AWAITING_EXECUTION'
                    self.emit('ENTRY_EXECUTION_REQUIRED',row.ts,block,c,cutoff=row.ts,zone_id=c.zone_id)
                return
        elif c.state=='AWAITING_EXECUTION':
            if origin_break:self._archive(c,'CHILD_CANCELLED',row.ts,'ORIGIN_INVALIDATED_BEFORE_EXECUTION_REPORT',block,row.ts)

    def apply_execution_report(self,child_id:str,at:datetime,price:float,block:str,price_cutoff:Optional[datetime]=None):
        c=self.active
        if c is None or c.child_id!=child_id or c.state!='AWAITING_EXECUTION':
            raise RuntimeError('invalid entry execution report state')
        c.state='OPEN';c.fill_at=at;c.fill_price=float(price)
        self.emit('CHILD_FILLED',at,block,c,cutoff=price_cutoff,fill_price=price)

    def apply_entry_no_fill(self,child_id:str,at:datetime,block:str,price_cutoff:Optional[datetime]=None):
        """Broker/execution adapter reports that the touched zone did not fill.

        This does not invent a timeout or cancel rule.  The precommitted Child returns
        to PENDING and may request execution again only on a later revealed touch.
        """
        c=self.active
        if c is None or c.child_id!=child_id or c.state!='AWAITING_EXECUTION':
            raise RuntimeError('invalid no-fill report state')
        c.state='PENDING';c.entry_trigger_at=None
        self.emit('ENTRY_NOT_FILLED',at,block,c,cutoff=price_cutoff)

    def apply_entry_cancel(self,child_id:str,at:datetime,block:str,price_cutoff:Optional[datetime]=None):
        """Explicit external cancellation/rejection of an awaiting entry order."""
        c=self.active
        if c is None or c.child_id!=child_id or c.state not in ('PENDING','AWAITING_EXECUTION'):
            raise RuntimeError('invalid entry cancel state')
        self._archive(c,'CHILD_CANCELLED',at,'EXTERNAL_ENTRY_CANCEL',block,price_cutoff)

    def apply_review_decision(self,child_id:str,at:datetime,decision:str,block:str,price_cutoff:Optional[datetime]=None):
        """Apply an explicit external decision; this method contains no market policy.

        HOLD is allowed only for REVIEW_REQUIRED.  EXIT creates an execution request
        but does not invent a fill.  REMAP leaves the Child guarded while a new map is
        required.
        """
        c=self.active
        if c is None or c.child_id!=child_id:
            raise RuntimeError('unknown active Child for review decision')
        decision=decision.upper()
        if decision=='HOLD':
            if c.state!='REVIEW_REQUIRED': raise RuntimeError('HOLD requires REVIEW_REQUIRED')
            c.state='OPEN';c.review_reason=None;c.launch_damage_reviewed=True
            self.emit('REVIEW_HOLD',at,block,c,cutoff=price_cutoff)
            return
        if decision=='EXIT':
            if c.state not in ('REVIEW_REQUIRED','REMAP_REQUIRED','OPEN'):
                raise RuntimeError('EXIT requires an open/review/remap Child')
            c.state='EXIT_REQUESTED'
            self.emit('EXIT_EXECUTION_REQUIRED',at,block,c,cutoff=price_cutoff,reason=c.review_reason)
            return
        if decision=='REMAP':
            if c.state not in ('REVIEW_REQUIRED','OPEN','REMAP_REQUIRED'):
                raise RuntimeError('REMAP requires an open/review Child')
            c.state='REMAP_REQUIRED'
            self.emit('REMAP_REQUIRED',at,block,c,cutoff=price_cutoff,reason=c.review_reason or 'EXTERNAL_REMAP_DECISION')
            return
        raise RuntimeError(f'unsupported review decision {decision!r}')

    def apply_remap_result(self,child_id:str,at:datetime,block:str,*,
                           new_parent_id:Optional[str],new_parent_side:Optional[str],
                           journey_role:str,price_cutoff:Optional[datetime]=None):
        """Resume a surviving Child only after an explicit remap result.

        This is an interface, not an automatic handoff rule.  The caller must supply
        the remapped Parent identity/side and semantic journey role.
        """
        c=self.active
        if c is None or c.child_id!=child_id or c.state!='REMAP_REQUIRED':
            raise RuntimeError('invalid remap result state')
        c.parent_id=new_parent_id or c.parent_id
        if new_parent_side in ('UP','DOWN'): c.parent_side=new_parent_side
        c.journey_role=journey_role
        c.state='OPEN';c.review_reason=None
        self.emit('REMAP_ACCEPTED_CHILD_CONTINUES',at,block,c,cutoff=price_cutoff,
                  new_parent_id=new_parent_id,new_parent_side=new_parent_side,journey_role=journey_role)

    def apply_exit_execution(self,child_id:str,at:datetime,price:float,block:str,price_cutoff:Optional[datetime]=None):
        c=self.active
        if c is None or c.child_id!=child_id or c.state!='EXIT_REQUESTED':
            raise RuntimeError('invalid exit execution report state')
        c.fill_price=c.fill_price  # entry price remains unchanged; exit price is event payload only.
        self._archive(c,'CHILD_EXITED',at,'EXIT_EXECUTED',block,price_cutoff)
        self.events[-1].payload['exit_price']=float(price)

    def block_end(self,block:str,at:datetime):
        if self.active is not None:self._archive(self.active,'CENSORED_BLOCK_END',at,'BLOCK_END',block,at)
        if self.context:self._end_context(at,block,'BLOCK_END')
        self.parent_id=self.parent_side=self.h1_relation=self.m15_relation=None

class StrategyObserver:
    def __init__(self,research_assume_zone_touch_fill=False,independent_lanes=False):
        self.book=M5ObjectBook();self.research_assume_zone_touch_fill=research_assume_zone_touch_fill;self.independent_lanes=independent_lanes
        self.counter=Lane('COUNTER',self.book,self);self.with_parent=Lane('WITH_PARENT',self.book,self)
        self.batch_events:list[SemanticEvent]=[];self.batch_bars:list[CompletedBar]=[]
        self.object_creation_rows:list[dict]=[];self.arm_intents:list[dict]=[]
    def other_active(self,branch):
        if self.independent_lanes:return None
        other=self.with_parent if branch=='COUNTER' else self.counter
        return other.active
    def request_arm(self,lane,at,block,pid,pside,side,origin,zone,cutoff,auth_class):
        self.arm_intents.append({'lane':lane,'at':at,'block':block,'parent_id':pid,'parent_side':pside,'side':side,
                                 'origin':origin,'zone':zone,'cutoff':cutoff,'auth_class':auth_class})
    def _resolve_arm_intents(self,known_at):
        intents=[x for x in self.arm_intents if x['at']==known_at]
        self.arm_intents=[x for x in self.arm_intents if x['at']!=known_at]
        if not intents:return
        if self.independent_lanes:
            for x in intents:x['lane'].arm_intent(x)
            return
        # If two opposite pitches are born from the exact same information batch, arm
        # neither.  The event is surfaced rather than giving Counter/With-Parent hidden
        # code-order priority.  Both source signals remain consumed; no hindsight backfill.
        if len(intents)>1 and len({x['side'] for x in intents})>1:
            first=sorted(intents,key=lambda x:x['lane'].branch)[0]
            first['lane'].emit('CROSS_LANE_CONFLICT_REVIEW',known_at,first['block'],parent_id=first['parent_id'],side=first['side'],cutoff=first['cutoff'],
                               conflict_scope='SIMULTANEOUS_AUTHORIZATION',
                               candidates=[{'branch':x['lane'].branch,'side':x['side'],'origin':x['origin'],'zone_id':x['zone'].object_id} for x in sorted(intents,key=lambda y:y['lane'].branch)])
            return
        for x in intents:
            other=self.other_active(x['lane'].branch)
            if other is not None and other.state in ('PENDING','AWAITING_EXECUTION','OPEN','REVIEW_REQUIRED','REMAP_REQUIRED','EXIT_REQUESTED') and other.side!=x['side']:
                x['lane'].emit('CROSS_LANE_CONFLICT_REVIEW',x['at'],x['block'],parent_id=x['parent_id'],side=x['side'],cutoff=x['cutoff'],
                               conflict_scope='EXISTING_OPPOSITE_CHILD',other_child=other.child_id,other_side=other.side,zone_id=x['zone'].object_id,origin=x['origin'])
            else:
                x['lane'].arm_intent(x)
    def on_semantic_event(self,e,m):self.batch_events.append(e)
    def on_completed_bar(self,b,m):
        self.batch_bars.append(b)
        if b.minutes==5:
            for x in self.book.on_m5(b):
                z=_ser(x); z['event']='OBJECT_KNOWN'
                self.object_creation_rows.append(z)
    def on_information_batch_complete(self,known_at,m):
        ev=[e for e in self.batch_events if e.known_at==known_at];bars=[b for b in self.batch_bars if b.known_at==known_at]
        self.counter.process_batch(known_at,ev,bars,m);self.with_parent.process_batch(known_at,ev,bars,m)
        self._resolve_arm_intents(known_at)
        self.batch_events=[e for e in self.batch_events if e.known_at!=known_at];self.batch_bars=[b for b in self.batch_bars if b.known_at!=known_at]
    def on_price(self,row,block,m):
        self.book.on_price(row);self.counter.on_price(row,block,m);self.with_parent.on_price(row,block,m)
    def _lane_for_child(self,child_id:str):
        for lane in (self.counter,self.with_parent):
            if lane.active is not None and lane.active.child_id==child_id:return lane
        raise RuntimeError(f'active Child not found: {child_id}')
    def apply_entry_execution(self,child_id,at,price,block,price_cutoff=None):
        self._lane_for_child(child_id).apply_execution_report(child_id,at,price,block,price_cutoff)
    def apply_entry_no_fill(self,child_id,at,block,price_cutoff=None):
        self._lane_for_child(child_id).apply_entry_no_fill(child_id,at,block,price_cutoff)
    def apply_entry_cancel(self,child_id,at,block,price_cutoff=None):
        self._lane_for_child(child_id).apply_entry_cancel(child_id,at,block,price_cutoff)
    def apply_review_decision(self,child_id,at,decision,block,price_cutoff=None):
        self._lane_for_child(child_id).apply_review_decision(child_id,at,decision,block,price_cutoff)
    def apply_remap_result(self,child_id,at,block,price_cutoff=None,**kw):
        self._lane_for_child(child_id).apply_remap_result(child_id,at,block,price_cutoff=price_cutoff,**kw)
    def apply_exit_execution(self,child_id,at,price,block,price_cutoff=None):
        self._lane_for_child(child_id).apply_exit_execution(child_id,at,price,block,price_cutoff)
    def on_block_end(self,block,m):
        at=BLOCK_END[block];self.counter.block_end(block,at);self.with_parent.block_end(block,at)

def _ser(d):
    z=asdict(d)
    for k,v in list(z.items()):
        if isinstance(v,datetime):z[k]=fmt(v)
    return z

def write(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:path.write_text('',encoding='utf-8');return
    with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def replay(source:Path,out:Path,research_fill=False,independent=False):
    o=StrategyObserver(research_fill,independent);m=MarketMachine(observer=o);RawM1Feed(source).replay(m);out.mkdir(parents=True,exist_ok=True)
    write(out/'counter_events.csv',[e.row() for e in o.counter.events]);write(out/'with_parent_events.csv',[e.row() for e in o.with_parent.events])
    write(out/'counter_children.csv',[_ser(c) for c in o.counter.children]);write(out/'with_parent_children.csv',[_ser(c) for c in o.with_parent.children])
    write(out/'m5_objects.csv',[_ser(x) for x in o.book.objects])
    def authrows(l):
        return [{k:(fmt(v) if isinstance(v,datetime) else v) for k,v in x.items()} for x in l.first_auth_rows]
    write(out/'counter_first_authorizations.csv',authrows(o.counter));write(out/'with_parent_first_authorizations.csv',authrows(o.with_parent))
    sm={'strategy_runtime_version':STRATEGY_RUNTIME_VERSION,'authorization_version':AUTHORIZATION_VERSION,'source_sha256':AUTHORITATIVE_SHA256,
        'mode':{'research_assume_zone_touch_fill':research_fill,'independent_lanes':independent},
        'counter_first_authorizations':len(o.counter.first_auth_rows),'with_parent_first_authorizations':len(o.with_parent.first_auth_rows),
        'counter_event_counts':{},'with_parent_event_counts':{},'m5_object_counts':{}}
    for e in o.counter.events:sm['counter_event_counts'][e.kind]=sm['counter_event_counts'].get(e.kind,0)+1
    for e in o.with_parent.events:sm['with_parent_event_counts'][e.kind]=sm['with_parent_event_counts'].get(e.kind,0)+1
    for x in o.book.objects:sm['m5_object_counts'][x.family]=sm['m5_object_counts'].get(x.family,0)+1
    (out/'summary.json').write_text(json.dumps(sm,indent=2,sort_keys=True)+'\n',encoding='utf-8');return sm

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True)
    p.add_argument('--research-assume-zone-touch-fill',action='store_true');p.add_argument('--independent-lanes',action='store_true');a=p.parse_args()
    print(json.dumps(replay(a.source,a.out_dir,a.research_assume_zone_touch_fill,a.independent_lanes),indent=2,sort_keys=True))
if __name__=='__main__':main()
