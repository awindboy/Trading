#!/usr/bin/env python3
"""V9 causal Child/order state-machine implementation harness.

This module sits on top of v9_semantic_runtime.  It consumes only causal runtime
state transitions, completed M5 object geometry, and revealed M1 price rows.

Important authority boundaries:
- structural origin boundaries are semantic falsification guards, not a claim about
  final broker/tick Hard-SL fill price;
- M5 object geometry supplies precommitted location, not direction authority;
- material H1/M15 damage produces a deterministic REVIEW/REMAP state; it is not
  silently converted into a stale-bar execution price;
- same-M1 origin-breach + zone-touch ambiguity fails closed.

The harness can run WITH_PARENT and COUNTER lanes independently.  Combined portfolio
conflict policy remains an explicit implementation gate rather than an invented rule.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import heapq
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from v9_semantic_runtime import (
    AUTHORITATIVE_SHA256, BLOCK_END, CompletedBar, MarketMachine, M1Row,
    RawM1Feed, SemanticEvent, fmt,
)

EXECUTION_VERSION = "v9-child-execution-harness-1"
OBJECT_ENGINE_VERSION = "v9-m5-object-known-at-1"


@dataclass
class M5Object:
    object_id: str
    block: str
    family: str
    direction: str
    source_start: datetime
    source_last_m1_at: datetime
    object_known_at: datetime
    price_low: float
    price_high: float
    active: bool = True
    ended_at: Optional[datetime] = None
    end_reason: Optional[str] = None
    sequence: int = 0


class M5ObjectBook:
    """Incremental exact M5 candidate geometry + M1 lifecycle."""
    def __init__(self) -> None:
        self.block: Optional[str] = None
        self.bars: list[CompletedBar] = []
        self.objects: list[M5Object] = []
        self.by_id: dict[str, M5Object] = {}
        self.seq = 0
        self.high_sw_heap: list[tuple[float,int,str]] = []
        self.low_sw_heap: list[tuple[float,int,str]] = []
        self.swing_seq = 0
        self.last_red: Optional[CompletedBar] = None
        self.last_green: Optional[CompletedBar] = None
        self.seen_ob_source: set[tuple[str,datetime]] = set()
        # lifecycle heaps; lazy stale entries are fine
        self.bull_fvg_fill: list[tuple[float,int,str]] = []      # max by low via -price
        self.bear_fvg_fill: list[tuple[float,int,str]] = []      # min high
        self.bull_ob_inval: list[tuple[float,int,str]] = []      # max low via -price
        self.bear_ob_inval: list[tuple[float,int,str]] = []      # min high
        self.swing_high_raid: list[tuple[float,int,str]] = []    # min high
        self.swing_low_raid: list[tuple[float,int,str]] = []     # max low via -price

    def reset(self, block: str) -> None:
        # Preserve archived objects across consumed blocks; reset only block-local
        # geometry/lifecycle indices.
        self.block = block
        self.bars = []
        self.high_sw_heap = []; self.low_sw_heap = []; self.swing_seq = 0
        self.last_red = None; self.last_green = None; self.seen_ob_source = set()
        self.bull_fvg_fill = []; self.bear_fvg_fill = []
        self.bull_ob_inval = []; self.bear_ob_inval = []
        self.swing_high_raid = []; self.swing_low_raid = []

    def _add(self, family: str, direction: str, source: datetime,
             source_last: datetime, known: datetime, lo: float, hi: float,
             suffix: str) -> M5Object:
        self.seq += 1
        oid=f"M5_{family}_{direction}_{source:%Y%m%d_%H%M}_{suffix}"
        o=M5Object(oid,self.block or "",family,direction,source,source_last,known,float(lo),float(hi),sequence=self.seq)
        self.objects.append(o);self.by_id[oid]=o
        if family=="FVG" and direction=="BULL": heapq.heappush(self.bull_fvg_fill,(-o.price_low,o.sequence,oid))
        elif family=="FVG" and direction=="BEAR": heapq.heappush(self.bear_fvg_fill,(o.price_high,o.sequence,oid))
        elif family=="OB" and direction=="BULL": heapq.heappush(self.bull_ob_inval,(-o.price_low,o.sequence,oid))
        elif family=="OB" and direction=="BEAR": heapq.heappush(self.bear_ob_inval,(o.price_high,o.sequence,oid))
        elif family=="SWING" and direction=="HIGH": heapq.heappush(self.swing_high_raid,(o.price_high,o.sequence,oid))
        elif family=="SWING" and direction=="LOW": heapq.heappush(self.swing_low_raid,(-o.price_low,o.sequence,oid))
        return o

    def _end(self, oid: str, at: datetime, reason: str) -> None:
        o=self.by_id.get(oid)
        if o is not None and o.active:
            o.active=False;o.ended_at=at;o.end_reason=reason

    def on_m5(self,b:CompletedBar)->list[M5Object]:
        if self.block!=b.block:self.reset(b.block)
        created=[]
        self.bars.append(b)
        n=len(self.bars)
        # Swing pivot at i-2 becomes known now (two right bars complete).
        if n>=5:
            a,b1,p,r1,r2=self.bars[-5:]
            if p.high>max(a.high,b1.high) and p.high>=max(r1.high,r2.high):
                o=self._add("SWING","HIGH",p.start,r2.price_revealed_cutoff,r2.known_at,p.high,p.high,"PIVOT");created.append(o)
                self.swing_seq+=1;heapq.heappush(self.high_sw_heap,(p.high,self.swing_seq,o.object_id))
            if p.low<min(a.low,b1.low) and p.low<=min(r1.low,r2.low):
                o=self._add("SWING","LOW",p.start,r2.price_revealed_cutoff,r2.known_at,p.low,p.low,"PIVOT");created.append(o)
                self.swing_seq+=1;heapq.heappush(self.low_sw_heap,(-p.low,self.swing_seq,o.object_id))
        # FVG C1/C3.
        if n>=3:
            c1,_,c3=self.bars[-3:]
            if c1.high<c3.low:
                created.append(self._add("FVG","BULL",c3.start,c3.price_revealed_cutoff,c3.known_at,c1.high,c3.low,"C3"))
            if c1.low>c3.high:
                created.append(self._add("FVG","BEAR",c3.start,c3.price_revealed_cutoff,c3.known_at,c3.high,c1.low,"C3"))
        # OB first break of already-confirmed swings.  Objects known exactly now are
        # not eligible as break references until a later completed M5 bar.
        broken_hi=[]
        while self.high_sw_heap and self.high_sw_heap[0][0] < b.close:
            _,_,oid=heapq.heappop(self.high_sw_heap);sw=self.by_id[oid]
            if sw.object_known_at < b.known_at: broken_hi.append(sw)
            else:
                heapq.heappush(self.high_sw_heap,(sw.price_high,sw.sequence,oid));break
        if broken_hi and self.last_red is not None:
            key=("BULL",self.last_red.start)
            if key not in self.seen_ob_source:
                self.seen_ob_source.add(key)
                created.append(self._add("OB","BULL",self.last_red.start,b.price_revealed_cutoff,b.known_at,
                                         self.last_red.low,self.last_red.high,f"VIA_{b.start:%Y%m%d_%H%M}"))
        broken_lo=[]
        while self.low_sw_heap and -self.low_sw_heap[0][0] > b.close:
            _,_,oid=heapq.heappop(self.low_sw_heap);sw=self.by_id[oid]
            if sw.object_known_at < b.known_at: broken_lo.append(sw)
            else:
                heapq.heappush(self.low_sw_heap,(-sw.price_low,sw.sequence,oid));break
        if broken_lo and self.last_green is not None:
            key=("BEAR",self.last_green.start)
            if key not in self.seen_ob_source:
                self.seen_ob_source.add(key)
                created.append(self._add("OB","BEAR",self.last_green.start,b.price_revealed_cutoff,b.known_at,
                                         self.last_green.low,self.last_green.high,f"VIA_{b.start:%Y%m%d_%H%M}"))
        if b.close<b.open:self.last_red=b
        if b.close>b.open:self.last_green=b
        return created

    def on_price(self,row:M1Row)->None:
        # FVG full fill.
        while self.bull_fvg_fill and -self.bull_fvg_fill[0][0] >= row.low:
            _,_,oid=heapq.heappop(self.bull_fvg_fill);o=self.by_id[oid]
            if o.active and row.ts>=o.object_known_at:self._end(oid,row.ts,"FULLY_FILLED")
        while self.bear_fvg_fill and self.bear_fvg_fill[0][0] <= row.high:
            _,_,oid=heapq.heappop(self.bear_fvg_fill);o=self.by_id[oid]
            if o.active and row.ts>=o.object_known_at:self._end(oid,row.ts,"FULLY_FILLED")
        # OB distal invalidation (strict beyond distal edge).
        while self.bull_ob_inval and -self.bull_ob_inval[0][0] > row.low:
            _,_,oid=heapq.heappop(self.bull_ob_inval);o=self.by_id[oid]
            if o.active and row.ts>=o.object_known_at:self._end(oid,row.ts,"DISTAL_INVALIDATED")
        while self.bear_ob_inval and self.bear_ob_inval[0][0] < row.high:
            _,_,oid=heapq.heappop(self.bear_ob_inval);o=self.by_id[oid]
            if o.active and row.ts>=o.object_known_at:self._end(oid,row.ts,"DISTAL_INVALIDATED")
        # Swing/liquidity raid.
        while self.swing_high_raid and self.swing_high_raid[0][0] < row.high:
            _,_,oid=heapq.heappop(self.swing_high_raid);o=self.by_id[oid]
            if o.active and row.ts>=o.object_known_at:self._end(oid,row.ts,"RAIDED")
        while self.swing_low_raid and -self.swing_low_raid[0][0] > row.low:
            _,_,oid=heapq.heappop(self.swing_low_raid);o=self.by_id[oid]
            if o.active and row.ts>=o.object_known_at:self._end(oid,row.ts,"RAIDED")

    def latest_zone(self, direction:str, price:float, known_at:datetime)->Optional[M5Object]:
        # Research selection: latest known intact FVG/OB entirely behind current price;
        # OB wins same-known-time family tie (lexicographic family descending).
        candidates=[]
        for o in reversed(self.objects):
            if o.block!=self.block or not o.active or o.object_known_at>known_at or o.family not in ("FVG","OB") or o.direction!=direction:continue
            if direction=="BULL" and not (o.price_high<price):continue
            if direction=="BEAR" and not (o.price_low>price):continue
            candidates.append(o)
        if not candidates:return None
        return max(candidates,key=lambda o:(o.object_known_at,o.family,o.sequence))


@dataclass
class Child:
    child_id:str
    branch:str
    side:str
    parent_id:str
    parent_side:str
    authorized_at:datetime
    origin_boundary:float
    zone_id:str
    zone_low:float
    zone_high:float
    state:str="PENDING"
    fill_at:Optional[datetime]=None
    h1_cycle_id:Optional[str]=None
    launch_anchor:Optional[float]=None
    launch_anchor_at:Optional[datetime]=None
    journey_role:str="LOCAL_BRIDGE"
    terminal_reason:Optional[str]=None
    terminal_at:Optional[datetime]=None


@dataclass
class ExecEvent:
    sequence:int
    kind:str
    at:datetime
    block:str
    branch:str
    child_id:Optional[str]=None
    parent_id:Optional[str]=None
    side:Optional[str]=None
    payload:dict=field(default_factory=dict)
    def row(self):
        d=asdict(self);d['at']=fmt(self.at);d['payload']=json.dumps(self.payload,sort_keys=True,separators=(',',':'));return d


class ExecutionLane:
    """One independent research lane: WITH_PARENT or COUNTER."""
    def __init__(self,branch:str,book:M5ObjectBook):
        if branch not in ("WITH_PARENT","COUNTER"):raise ValueError(branch)
        self.branch=branch;self.book=book;self.active:Optional[Child]=None;self.seq=0;self.child_seq=0
        self.events:list[ExecEvent]=[];self.children:list[Child]=[]
        self.h1_aligned_start:Optional[datetime]=None;self.h1_aligned_parent:Optional[str]=None
        self.h1_aligned_side:Optional[str]=None;self.h1_aligned_initial_m15:Optional[str]=None
        self.h1_aligned_eligible=False;self.aligned_high=None;self.aligned_low=None
        self.interrupt_start:Optional[datetime]=None;self.interrupt_parent:Optional[str]=None;self.interrupt_side:Optional[str]=None
        self.interrupt_high=None;self.interrupt_low=None;self.current_cycle_id:Optional[str]=None
        self.last_m15_relation:Optional[str]=None

    def emit(self,kind,at,block,child:Optional[Child]=None,**payload):
        self.seq+=1;e=ExecEvent(self.seq,kind,at,block,self.branch,child.child_id if child else None,
                               child.parent_id if child else payload.pop('parent_id',None),child.side if child else payload.pop('side',None),payload)
        self.events.append(e);return e

    def _finish_child(self,child:Child,state:str,at:datetime,reason:str,block:str):
        child.state=state;child.terminal_at=at;child.terminal_reason=reason;self.children.append(child)
        self.emit(state,at,block,child,reason=reason)
        self.active=None

    def _authorize(self,at:datetime,block:str,parent_id:str,parent_side:str,origin:Optional[float],last_price:Optional[float],cycle_id:Optional[str]=None):
        if self.active is not None:return
        if origin is None or last_price is None or not math.isfinite(origin):
            self.emit("PITCH_NO_ORIGIN",at,block,parent_id=parent_id,side=parent_side);return
        side=parent_side if self.branch=="WITH_PARENT" else ("DOWN" if parent_side=="UP" else "UP")
        direction="BULL" if side=="UP" else "BEAR"
        zone=self.book.latest_zone(direction,last_price,at)
        self.child_seq+=1;cid=f"{block}-{self.branch[:3]}{self.child_seq:04d}"
        if zone is None:
            self.emit("PITCH_NO_GEOMETRY",at,block,parent_id=parent_id,side=side,origin=origin,cycle_id=cycle_id);return
        child=Child(cid,self.branch,side,parent_id,parent_side,at,float(origin),zone.object_id,zone.price_low,zone.price_high,h1_cycle_id=cycle_id)
        self.active=child;self.emit("CHILD_PENDING",at,block,child,origin=origin,zone_id=zone.object_id,zone_low=zone.price_low,zone_high=zone.price_high,cycle_id=cycle_id)

    def on_semantic(self,e:SemanticEvent,m:MarketMachine):
        # Track natural H1 run boundaries independent of later cycle outcome.
        if e.kind=="H1_RUN_STARTED":
            if e.relation=="ALIGNED" and e.parent_id is not None:
                self.h1_aligned_start=e.known_at;self.h1_aligned_parent=e.parent_id;self.h1_aligned_side=e.parent_side
                self.h1_aligned_initial_m15=m.current_m15_relation
                self.h1_aligned_eligible=(m.current_m15_relation!="COUNTERFLOW")
                self.aligned_high=self.aligned_low=None
            elif e.relation!="ALIGNED":
                # End initial aligned authorization window; existing Child may continue.
                self.h1_aligned_start=None;self.h1_aligned_parent=None;self.h1_aligned_side=None;self.h1_aligned_eligible=False
        elif e.kind=="H1_INTERRUPT_START":
            self.interrupt_start=e.known_at;self.interrupt_parent=e.parent_id;self.interrupt_side=e.parent_side;self.current_cycle_id=e.h1_cycle_id
            self.interrupt_high=self.interrupt_low=None
            if self.branch=="COUNTER" and self.active is not None and self.active.parent_id==e.parent_id:
                self.active.h1_cycle_id=e.h1_cycle_id;self.active.launch_anchor=e.anchor_price;self.active.launch_anchor_at=e.known_at
                self.emit("H1_INTERRUPT_PROGRESS",e.known_at,e.block,self.active,anchor=e.anchor_price)
        elif e.kind=="H1_REALIGN":
            if self.branch=="WITH_PARENT" and self.active is not None and self.active.parent_id==e.parent_id:
                if self.active.state=="PENDING":
                    self._finish_child(self.active,"CHILD_CANCELLED",e.known_at,"H1_REALIGN_BEFORE_FILL",e.block)
                elif self.active.state=="OPEN":
                    self.active.journey_role="PARENT_JOURNEY";self.active.launch_anchor=e.anchor_price;self.active.launch_anchor_at=e.known_at
                    self.emit("CHILD_PROMOTED_PARENT_JOURNEY",e.known_at,e.block,self.active,anchor=e.anchor_price)
            if self.branch=="COUNTER" and self.active is not None and self.active.parent_id==e.parent_id:
                # Local-Bridge terminal.  Do not invent stale execution; require immediate remap/review.
                if self.active.state=="PENDING":self._finish_child(self.active,"CHILD_CANCELLED",e.known_at,"H1_REALIGN_LOCAL_BRIDGE_TERMINAL",e.block)
                elif self.active.state=="OPEN":
                    self.active.state="REMAP_REQUIRED";self.emit("REMAP_REQUIRED",e.known_at,e.block,self.active,reason="H1_REALIGN_LOCAL_BRIDGE_TERMINAL")
        elif e.kind=="PARENT_AUTHORITY_LOST":
            if self.active is not None and self.active.parent_id==e.parent_id:
                if self.active.state=="PENDING":self._finish_child(self.active,"CHILD_CANCELLED",e.known_at,"PARENT_AUTHORITY_LOST_BEFORE_FILL",e.block)
                elif self.active.state in ("OPEN","REMAP_REQUIRED"):
                    self.active.state="REMAP_REQUIRED";self.emit("REMAP_REQUIRED",e.known_at,e.block,self.active,reason="PARENT_AUTHORITY_LOST")
        elif e.kind=="PARENT_EARNED":
            if self.branch=="COUNTER" and self.active is not None and self.active.state=="REMAP_REQUIRED":
                if e.parent_side==self.active.side:
                    self.active.parent_id=e.parent_id or self.active.parent_id;self.active.parent_side=e.parent_side or self.active.parent_side;self.active.journey_role="WITH_NEW_PARENT_JOURNEY"
                    self.active.state="OPEN";self.emit("COUNTER_HANDOFF_NEW_PARENT",e.known_at,e.block,self.active,new_parent=e.parent_id)
                else:
                    self.emit("UNRESOLVED_REMAP_SAME_SIDE_REEARN",e.known_at,e.block,self.active,new_parent=e.parent_id)
        elif e.kind=="M15_RELATION_CHANGED":
            self.last_m15_relation=e.relation
            # Equal-time H1 start/interrupt is excluded by strict > start authority.
            if self.branch=="COUNTER":
                can_initial=(self.active is None and m.current_h1_relation=="ALIGNED" and self.h1_aligned_start is not None and
                             e.parent_id==self.h1_aligned_parent and e.known_at>self.h1_aligned_start and self.h1_aligned_eligible)
                can_reauth=(self.active is None and e.parent_id is not None and e.relation=="COUNTERFLOW" and self.current_cycle_id is not None)
                if e.relation=="COUNTERFLOW" and (can_initial or can_reauth):
                    origin=None
                    if can_initial:
                        origin=self.aligned_high if e.parent_side=="UP" else self.aligned_low
                    else:
                        # After a stopped/damaged Counter Child during H1 interrupt, a fresh pitch uses the
                        # current post-stop/interruption excursion; for impl1 use current interruption extreme.
                        origin=self.interrupt_high if e.parent_side=="UP" else self.interrupt_low
                    self._authorize(e.known_at,e.block,e.parent_id or "",e.parent_side or "",origin,m.last_price.close if m.last_price else None,self.current_cycle_id)
                    if can_initial:self.h1_aligned_eligible=False
            else:
                if (e.relation=="ALIGNED" and self.active is None and e.parent_id is not None and
                    m.current_h1_relation in ("COUNTERFLOW","LOCAL_BALANCE") and self.interrupt_start is not None and
                    e.known_at>self.interrupt_start and e.parent_id==self.interrupt_parent):
                    origin=self.interrupt_low if e.parent_side=="UP" else self.interrupt_high
                    self._authorize(e.known_at,e.block,e.parent_id,e.parent_side or "",origin,m.last_price.close if m.last_price else None,self.current_cycle_id)
        # relationship snapshots update initial aligned-run eligibility at the exact run start.
        elif e.kind=="M15_RELATION_SNAPSHOT":
            self.last_m15_relation=e.relation

    def on_m15_bar(self,b:CompletedBar,m:MarketMachine):
        # At H1 aligned-run start include M15 state known at the exact same timestamp in initial snapshot.
        if self.h1_aligned_start==b.known_at and self.h1_aligned_parent==(m.parent.parent_id if m.parent else None):
            self.h1_aligned_initial_m15=m.current_m15_relation
            self.h1_aligned_eligible=(m.current_m15_relation!="COUNTERFLOW")
        c=self.active
        if c is None or c.launch_anchor is None or c.state not in ("PENDING","OPEN"):return
        damage=False
        if c.branch=="WITH_PARENT": damage=(b.close<c.launch_anchor) if c.parent_side=="UP" else (b.close>c.launch_anchor)
        else: damage=(b.close>c.launch_anchor) if c.parent_side=="UP" else (b.close<c.launch_anchor)
        if damage:
            if c.state=="PENDING":self._finish_child(c,"CHILD_CANCELLED",b.known_at,"M15_CLOSE_BEYOND_LAUNCH_ANCHOR_PREFILL",b.block)
            else:
                c.state="REMAP_REQUIRED";self.emit("MATERIAL_CHILD_DAMAGE",b.known_at,b.block,c,anchor=c.launch_anchor,close=b.close)

    def on_price(self,row:M1Row,block:str,m:MarketMachine):
        # Maintain causal origin extrema from the relevant H1 context.
        if self.h1_aligned_start is not None and row.ts>=self.h1_aligned_start and self.h1_aligned_parent is not None:
            self.aligned_high=row.high if self.aligned_high is None else max(self.aligned_high,row.high)
            self.aligned_low=row.low if self.aligned_low is None else min(self.aligned_low,row.low)
        if self.interrupt_start is not None and row.ts>=self.interrupt_start and self.interrupt_parent is not None:
            self.interrupt_high=row.high if self.interrupt_high is None else max(self.interrupt_high,row.high)
            self.interrupt_low=row.low if self.interrupt_low is None else min(self.interrupt_low,row.low)
        c=self.active
        if c is None or c.state not in ("PENDING","OPEN","REMAP_REQUIRED"):return
        origin_break=(row.low<c.origin_boundary) if c.side=="UP" else (row.high>c.origin_boundary)
        zone_touch=row.high>=c.zone_low and row.low<=c.zone_high
        if c.state=="PENDING":
            if origin_break and zone_touch:
                self._finish_child(c,"CHILD_CANCELLED",row.ts,"INTRAMINUTE_ORIGIN_AND_ZONE_AMBIGUOUS",block);return
            if origin_break:
                self._finish_child(c,"CHILD_CANCELLED",row.ts,"ORIGIN_INVALIDATED_PREFILL",block);return
            if zone_touch:
                c.state="OPEN";c.fill_at=row.ts;self.emit("CHILD_FILLED",row.ts,block,c,zone_id=c.zone_id);return
        elif c.state in ("OPEN","REMAP_REQUIRED") and origin_break:
            self._finish_child(c,"CHILD_DEAD",row.ts,"ORIGIN_INVALIDATED",block)

    def block_end(self,block:str):
        if self.active is not None:
            self._finish_child(self.active,"CENSORED_BLOCK_END",BLOCK_END[block],"BLOCK_END",block)
        self.h1_aligned_start=self.h1_aligned_parent=self.h1_aligned_side=None;self.h1_aligned_eligible=False
        self.interrupt_start=self.interrupt_parent=self.interrupt_side=None;self.current_cycle_id=None
        self.aligned_high=self.aligned_low=self.interrupt_high=self.interrupt_low=None


class ExecutionObserver:
    def __init__(self):
        self.book=M5ObjectBook();self.with_parent=ExecutionLane("WITH_PARENT",self.book);self.counter=ExecutionLane("COUNTER",self.book)
    def on_semantic_event(self,e,m):
        self.with_parent.on_semantic(e,m);self.counter.on_semantic(e,m)
    def on_completed_bar(self,b,m):
        if b.minutes==5:self.book.on_m5(b)
        elif b.minutes==15:
            self.with_parent.on_m15_bar(b,m);self.counter.on_m15_bar(b,m)
    def on_price(self,row,block,m):
        self.book.on_price(row);self.with_parent.on_price(row,block,m);self.counter.on_price(row,block,m)
    def on_block_end(self,block,m):
        self.with_parent.block_end(block);self.counter.block_end(block)


def write_csv(path:Path,rows:list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:path.write_text('',encoding='utf-8');return
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def child_row(c:Child):
    d=asdict(c)
    for k,v in list(d.items()):
        if isinstance(v,datetime):d[k]=fmt(v)
    return d

def object_row(o:M5Object):
    d=asdict(o)
    for k,v in list(d.items()):
        if isinstance(v,datetime):d[k]=fmt(v)
    return d


def replay(source:Path,out:Path)->dict:
    obs=ExecutionObserver();m=MarketMachine(observer=obs);RawM1Feed(source).replay(m);out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'m5_objects.csv',[object_row(o) for o in obs.book.objects])
    write_csv(out/'with_parent_exec_events.csv',[e.row() for e in obs.with_parent.events]);write_csv(out/'counter_exec_events.csv',[e.row() for e in obs.counter.events])
    write_csv(out/'with_parent_children.csv',[child_row(c) for c in obs.with_parent.children]);write_csv(out/'counter_children.csv',[child_row(c) for c in obs.counter.children])
    summary={'execution_version':EXECUTION_VERSION,'object_engine_version':OBJECT_ENGINE_VERSION,'source_sha256':AUTHORITATIVE_SHA256,
             'm5_object_counts':{},'with_parent_event_counts':{},'counter_event_counts':{},
             'with_parent_children':len(obs.with_parent.children),'counter_children':len(obs.counter.children)}
    for o in obs.book.objects:summary['m5_object_counts'][o.family]=summary['m5_object_counts'].get(o.family,0)+1
    for e in obs.with_parent.events:summary['with_parent_event_counts'][e.kind]=summary['with_parent_event_counts'].get(e.kind,0)+1
    for e in obs.counter.events:summary['counter_event_counts'][e.kind]=summary['counter_event_counts'].get(e.kind,0)+1
    (out/'execution_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8');return summary


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);a=p.parse_args(argv)
    print(json.dumps(replay(a.source,a.out_dir),indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
