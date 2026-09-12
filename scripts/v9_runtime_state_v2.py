#!/usr/bin/env python3
"""Versioned resumable V9 dual-clock causal strategy runtime.

This runner never uses future OHLC to decide current semantic/order state.
It persists exact market/strategy accumulators plus source byte offset and current
incomplete timeframe buckets.  Consumed research blocks are indexed by timestamps
only; hidden interval OHLC is never decoded by the strategy runtime.

State-v2 is an implementation gate, not production/EA authority.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, os, tempfile
from collections import deque
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from v9_semantic_runtime import (
    AUTHORITATIVE_SHA256, EXPECTED_HEADER, BLOCKS, BLOCK_END, TF_PRIORITY,
    Bucket, BucketSet, CompletedBar, EMA, H4Calculator, H4State, H1Cycle,
    LTFCalculator, LTFState, M1Row, MarketMachine, Parent, RuntimeErrorV9,
    SemanticEvent, fast_ts, fmt, sha256_file,
)
from v9_execution_state_machine import M5Object, M5ObjectBook
from v9_strategy_state_machine import (
    AUTHORIZATION_VERSION, STRATEGY_RUNTIME_VERSION, Child, Context, Event,
    Lane, StrategyObserver,
)

STATE_VERSION=2
RUNNER_VERSION='v9-resumable-dual-clock-runner-3'
SOURCE_INDEX_VERSION='v9-consumed-byte-range-index-1'
FROZEN_CONSUMED_RANGES=[
    {'block':'2025H1','start':'2025-01-01 00:00:00','end':'2025-07-01 00:00:00','start_offset':65173328,'end_offset':75912993},
    {'block':'2026JF','start':'2026-01-01 00:00:00','end':'2026-03-01 00:00:00','start_offset':86972434,'end_offset':90428045},
]



def dt(x): return None if x in (None,'') else datetime.strptime(x,'%Y-%m-%d %H:%M:%S')
def dts(x): return fmt(x) if isinstance(x,datetime) else x

def atomic_write(path:Path,obj:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:
            json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def append_jsonl(path:Path,rows:list[dict]):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8',newline='\n') as f:
        for r in rows:f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')

def file_sha_if_exists(p:Path)->Optional[str]: return sha256_file(p) if p.exists() else None

# ---------------- frozen consumed source ranges ----------------
def validate_source_index(source:Path,index:dict)->dict:
    actual=sha256_file(source)
    if actual.lower()!=AUTHORITATIVE_SHA256.lower():
        raise RuntimeErrorV9(f'source SHA mismatch expected={AUTHORITATIVE_SHA256} actual={actual}')
    if index.get('version')!=SOURCE_INDEX_VERSION:
        raise RuntimeErrorV9('unsupported consumed source-range index version')
    if index.get('source_sha256')!=actual or int(index.get('source_size',-1))!=source.stat().st_size:
        raise RuntimeErrorV9('consumed source-range manifest does not match authoritative source identity')
    if index.get('ranges')!=FROZEN_CONSUMED_RANGES:
        raise RuntimeErrorV9('consumed source-range manifest differs from frozen authority; refusing to scan or infer hidden ranges')
    return index

# Research provisioning helper only. The causal runtime itself must consume the frozen
# manifest above and must not discover ranges by scanning through future-hidden data.
def build_source_index(source:Path)->dict:
    actual=sha256_file(source)
    if actual.lower()!=AUTHORITATIVE_SHA256.lower():
        raise RuntimeErrorV9(f'source SHA mismatch expected={AUTHORITATIVE_SHA256} actual={actual}')
    targets=[]
    for name,start,end in BLOCKS:
        targets += [(name,'start',start),(name,'end',end)]
    targets=sorted(targets,key=lambda x:x[2])
    found={}
    with source.open('rb') as f:
        header=f.readline().decode('utf-8-sig').rstrip('\r\n').split('\t')
        if header!=EXPECTED_HEADER: raise RuntimeErrorV9('unexpected source header')
        while targets:
            pos=f.tell(); raw=f.readline()
            if not raw:break
            # Timestamp fields only. OHLC bytes are neither decoded nor exposed here.
            h=raw.split(b'\t',2)
            if len(h)<3: raise RuntimeErrorV9('malformed source row while indexing')
            ts=fast_ts(h[0].decode('ascii'),h[1].decode('ascii'))
            while targets and ts>=targets[0][2]:
                name,which,target=targets.pop(0);found[(name,which)]=pos
            if not targets: break
    if targets: raise RuntimeErrorV9(f'could not locate source range targets: {targets}')
    ranges=[]
    for name,start,end in BLOCKS:
        ranges.append({'block':name,'start':fmt(start),'end':fmt(end),
                       'start_offset':found[(name,'start')],'end_offset':found[(name,'end')]})
    return {'version':SOURCE_INDEX_VERSION,'source_basename':source.name,'source_sha256':actual,
            'source_size':source.stat().st_size,'ranges':ranges}

# ---------------- serializers ----------------
def ser_bar(x):
    if x is None:return None
    z=asdict(x)
    for k,v in list(z.items()):
        if isinstance(v,datetime):z[k]=fmt(v)
    return z

def deser_bucket(z):
    if z is None:return None
    return Bucket(z['block'],int(z['minutes']),dt(z['start']),float(z['open']),float(z['high']),float(z['low']),float(z['close']),dt(z['last_ts']),int(z['observed_rows']))

def deser_completed(z):
    if z is None:return None
    return CompletedBar(z['block'],int(z['minutes']),dt(z['start']),dt(z['known_at']),dt(z['price_revealed_cutoff']),float(z['open']),float(z['high']),float(z['low']),float(z['close']),int(z['observed_rows']))

def ser_ema(e:EMA):return {'value':e.value,'count':e.count}
def load_ema(e:EMA,z):e.value=z['value'];e.count=int(z['count'])

def ser_h4calc(c:H4Calculator):
    return {'block':c.block,'count':c.count,'ema20':ser_ema(c.ema20),'ema50':ser_ema(c.ema50),
            'closes':list(c.closes),'highs':list(c.highs),'lows':list(c.lows),'e20':list(c.e20),'e50':list(c.e50)}
def load_h4calc(z):
    c=H4Calculator();c.block=z['block'];c.count=int(z['count']);load_ema(c.ema20,z['ema20']);load_ema(c.ema50,z['ema50'])
    c.closes=deque(z['closes'],maxlen=21);c.highs=deque(z['highs'],maxlen=20);c.lows=deque(z['lows'],maxlen=20);c.e20=deque(z['e20'],maxlen=5);c.e50=deque(z['e50'],maxlen=6);return c

def ser_ltfcalc(c:LTFCalculator):
    return {'timeframe':c.timeframe,'warmup':c.warmup,'block':c.block,'count':c.count,'ema20':ser_ema(c.ema20),'ema50':ser_ema(c.ema50),
            'closes':list(c.closes),'highs':list(c.highs),'lows':list(c.lows),'e20':list(c.e20)}
def load_ltfcalc(z):
    c=LTFCalculator(z['timeframe'],int(z['warmup']));c.block=z['block'];c.count=int(z['count']);load_ema(c.ema20,z['ema20']);load_ema(c.ema50,z['ema50'])
    c.closes=deque(z['closes'],maxlen=9);c.highs=deque(z['highs'],maxlen=8);c.lows=deque(z['lows'],maxlen=8);c.e20=deque(z['e20'],maxlen=4);return c

def ser_dc(x):
    if x is None:return None
    z=asdict(x)
    for k,v in list(z.items()):
        if isinstance(v,datetime):z[k]=fmt(v)
    return z

def load_h4state(z): return None if z is None else H4State(**{**z,'start':dt(z['start']),'known_at':dt(z['known_at']),'price_revealed_cutoff':dt(z['price_revealed_cutoff'])})
def load_ltfstate(z): return None if z is None else LTFState(**{**z,'start':dt(z['start']),'known_at':dt(z['known_at']),'price_revealed_cutoff':dt(z['price_revealed_cutoff'])})

def ser_market(m:MarketMachine):
    return {
      'h4_calc':ser_h4calc(m.h4_calc),'h1_calc':ser_ltfcalc(m.h1_calc),'m15_calc':ser_ltfcalc(m.m15_calc),'m5_calc':ser_ltfcalc(m.m5_calc),
      'latest_h4':ser_dc(m.latest_h4),'latest_h1':ser_dc(m.latest_h1),'latest_m15':ser_dc(m.latest_m15),'latest_m5':ser_dc(m.latest_m5),
      'parent':ser_dc(m.parent),'parent_counter':m.parent_counter,'cycle_counter':m.cycle_counter,'active_cycle':ser_dc(m.active_cycle),
      'h1_run_side':m.h1_run_side,'h1_run_relation':m.h1_run_relation,'h1_run_last_at':fmt(m.h1_run_last_at),
      'current_h1_relation':m.current_h1_relation,'current_m15_relation':m.current_m15_relation,'m15_parent_id':m.m15_parent_id,
      'semantic_seq':m.seq,'price_revealed_cutoff':fmt(m.price_revealed_cutoff),'information_known_at':fmt(m.information_known_at),'last_price':ser_dc(m.last_price),
    }
def load_market(z,observer):
    m=MarketMachine(observer=observer);m.h4_calc=load_h4calc(z['h4_calc']);m.h1_calc=load_ltfcalc(z['h1_calc']);m.m15_calc=load_ltfcalc(z['m15_calc']);m.m5_calc=load_ltfcalc(z['m5_calc'])
    m.latest_h4=load_h4state(z['latest_h4']);m.latest_h1=load_ltfstate(z['latest_h1']);m.latest_m15=load_ltfstate(z['latest_m15']);m.latest_m5=load_ltfstate(z['latest_m5'])
    if z['parent']:
        q=z['parent'];m.parent=Parent(q['parent_id'],q['block'],q['side'],dt(q['start']))
    m.parent_counter={k:int(v) for k,v in z['parent_counter'].items()};m.cycle_counter={k:int(v) for k,v in z['cycle_counter'].items()}
    if z['active_cycle']:
        q=z['active_cycle'];m.active_cycle=H1Cycle(q['cycle_id'],q['block'],q['side'],dt(q['start']),q['parent_id'])
    m.h1_run_side=z['h1_run_side'];m.h1_run_relation=z['h1_run_relation'];m.h1_run_last_at=dt(z['h1_run_last_at'])
    m.current_h1_relation=z['current_h1_relation'];m.current_m15_relation=z['current_m15_relation'];m.m15_parent_id=z['m15_parent_id'];m.seq=int(z['semantic_seq'])
    m.price_revealed_cutoff=dt(z['price_revealed_cutoff']);m.information_known_at=dt(z['information_known_at'])
    if z['last_price']:
        q=z['last_price'];m.last_price=M1Row(dt(q['ts']),float(q['open']),float(q['high']),float(q['low']),float(q['close']))
    # Histories are append-only ledgers outside the checkpoint; calculations do not depend on them.
    m.events=[];m.h4_states=[];m.h1_states=[];m.m15_states=[];m.m5_states=[];m.cycles=[];m.parents=[]
    return m

def ser_object(o:M5Object):
    z=asdict(o)
    for k,v in list(z.items()):
        if isinstance(v,datetime):z[k]=fmt(v)
    return z
def load_object(z):
    for k in ['source_start','source_last_m1_at','object_known_at','ended_at']:
        z[k]=dt(z.get(k))
    return M5Object(**z)

def ser_book(b:M5ObjectBook):
    # A swing can be geometrically RAIDED (inactive for liquidity lifecycle) yet still
    # remain in the OB break-reference heap until a later completed M5 close breaks it.
    # Preserve every active object plus every object still referenced by those heaps.
    required_ids={o.object_id for o in b.objects if o.active and o.block==b.block}
    required_ids.update(x[2] for x in b.high_sw_heap); required_ids.update(x[2] for x in b.low_sw_heap)
    retained=[ser_object(o) for o in b.objects if o.object_id in required_ids]
    return {'block':b.block,'bars':[ser_bar(x) for x in b.bars[-5:]],'retained_objects':retained,'seq':b.seq,'swing_seq':b.swing_seq,
            'high_sw_heap':[list(x) for x in b.high_sw_heap],'low_sw_heap':[list(x) for x in b.low_sw_heap],
            'last_red':ser_bar(b.last_red),'last_green':ser_bar(b.last_green),
            'seen_ob_source':[[a,fmt(t)] for a,t in sorted(b.seen_ob_source,key=lambda x:(x[0],x[1]))]}
def load_book(z):
    b=M5ObjectBook();b.block=z['block'];b.bars=[deser_completed(x) for x in z['bars']];b.seq=int(z['seq']);b.swing_seq=int(z['swing_seq'])
    b.objects=[load_object(dict(x)) for x in z['retained_objects']];b.by_id={x.object_id:x for x in b.objects}
    b.high_sw_heap=[tuple(x) for x in z['high_sw_heap']];b.low_sw_heap=[tuple(x) for x in z['low_sw_heap']]
    b.last_red=deser_completed(z['last_red']);b.last_green=deser_completed(z['last_green']);b.seen_ob_source={(a,dt(t)) for a,t in z['seen_ob_source']}
    # Rebuild lifecycle heaps from active objects.  OB-break heaps remain exact from state above.
    b.bull_fvg_fill=[];b.bear_fvg_fill=[];b.bull_ob_inval=[];b.bear_ob_inval=[];b.swing_high_raid=[];b.swing_low_raid=[]
    import heapq
    for o in b.objects:
        if o.family=='FVG' and o.direction=='BULL':heapq.heappush(b.bull_fvg_fill,(-o.price_low,o.sequence,o.object_id))
        elif o.family=='FVG' and o.direction=='BEAR':heapq.heappush(b.bear_fvg_fill,(o.price_high,o.sequence,o.object_id))
        elif o.family=='OB' and o.direction=='BULL':heapq.heappush(b.bull_ob_inval,(-o.price_low,o.sequence,o.object_id))
        elif o.family=='OB' and o.direction=='BEAR':heapq.heappush(b.bear_ob_inval,(o.price_high,o.sequence,o.object_id))
        elif o.family=='SWING' and o.direction=='HIGH':heapq.heappush(b.swing_high_raid,(o.price_high,o.sequence,o.object_id))
        elif o.family=='SWING' and o.direction=='LOW':heapq.heappush(b.swing_low_raid,(-o.price_low,o.sequence,o.object_id))
    return b

def ser_context(c):return ser_dc(c)
def load_context(z):
    if z is None:return None
    return Context(z['kind'],z['block'],z['parent_id'],z['parent_side'],dt(z['start']),z['initial_m15'],bool(z['first_pitch_allowed']),bool(z['first_pitch_consumed']),z['high'],z['low'])
def ser_child(c):return ser_dc(c)
def load_child(z):
    if z is None:return None
    for k in ['authorized_at','entry_trigger_at','fill_at','launch_anchor_at','launch_touch_at','launch_damage_at','terminal_at']:
        z[k]=dt(z.get(k))
    return Child(**z)

def ser_lane(l:Lane):
    return {'branch':l.branch,'context':ser_context(l.context),'active':ser_child(l.active),'seq':l.seq,'child_seq':l.child_seq,
            'parent_id':l.parent_id,'parent_side':l.parent_side,'h1_relation':l.h1_relation,'m15_relation':l.m15_relation}
def load_lane(l:Lane,z):
    l.context=load_context(z['context']);l.active=load_child(dict(z['active'])) if z['active'] else None;l.seq=int(z['seq']);l.child_seq=int(z['child_seq'])
    l.parent_id=z['parent_id'];l.parent_side=z['parent_side'];l.h1_relation=z['h1_relation'];l.m15_relation=z['m15_relation'];l.children=[];l.events=[];l.first_auth_rows=[]

def ser_observer(o:StrategyObserver):
    if o.batch_events or o.batch_bars or getattr(o,'arm_intents',[]): raise RuntimeErrorV9('checkpoint attempted inside incomplete information batch')
    return {'research_assume_zone_touch_fill':o.research_assume_zone_touch_fill,'independent_lanes':o.independent_lanes,'book':ser_book(o.book),
            'counter':ser_lane(o.counter),'with_parent':ser_lane(o.with_parent)}
def load_observer(z):
    o=StrategyObserver(bool(z['research_assume_zone_touch_fill']),bool(z['independent_lanes']));o.book=load_book(z['book'])
    o.counter.book=o.book;o.with_parent.book=o.book;load_lane(o.counter,z['counter']);load_lane(o.with_parent,z['with_parent']);o.object_creation_rows=[];o.batch_events=[];o.batch_bars=[];o.arm_intents=[];return o

def ser_buckets(bs:BucketSet):return {str(k):ser_bar(v) for k,v in bs.current.items()}
def load_buckets(z):
    b=BucketSet();b.current={int(k):deser_bucket(v) for k,v in z.items()};return b

# ---------------- runner ----------------
class V2Runner:
    def __init__(self,source:Path,index:dict,work:Path,*,research_fill=False,independent=False):
        self.source=source;self.index=validate_source_index(source,index);self.work=work;self.work.mkdir(parents=True,exist_ok=True)
        self.observer=StrategyObserver(research_fill,independent);self.market=MarketMachine(observer=self.observer);self.buckets=BucketSet()
        self.range_i=0;self.active_block=None;self.resume_offset=int(index['ranges'][0]['start_offset']);self.last_source_ts=None;self.revealed_rows=0
        self.revealed=self.work/'revealed_consumed.tsv';self.semantic_log=self.work/'semantic_events.jsonl';self.counter_log=self.work/'counter_events.jsonl';self.with_log=self.work/'with_parent_events.jsonl';self.object_log=self.work/'object_known.jsonl';self.action_log=self.work/'external_actions.jsonl';self.request_packet=self.work/'pending_request.json'
        self.pending_gates=[]
        if not self.revealed.exists():
            with source.open('rb') as f: header=f.readline()
            self.revealed.write_bytes(header)
        self._log_mark=(0,0,0,0)

    @classmethod
    def from_state(cls,source:Path,state_path:Path):
        z=json.loads(state_path.read_text(encoding='utf-8')); idx=validate_source_index(source,z['source_index']);work=state_path.parent
        if z['version']!=STATE_VERSION:raise RuntimeErrorV9('unsupported state version')
        actual=sha256_file(source)
        if actual!=z['source_sha256'] or source.stat().st_size!=z['source_size']:raise RuntimeErrorV9('source identity changed')
        r=cls.__new__(cls);r.source=source;r.index=idx;r.work=work;r.observer=load_observer(z['strategy']);r.market=load_market(z['market'],r.observer);r.buckets=load_buckets(z['buckets'])
        r.range_i=int(z['range_index']);r.active_block=z['active_block'];r.resume_offset=int(z['resume_offset']);r.last_source_ts=dt(z['last_source_ts']);r.revealed_rows=int(z['revealed_rows'])
        r.revealed=work/'revealed_consumed.tsv';r.semantic_log=work/'semantic_events.jsonl';r.counter_log=work/'counter_events.jsonl';r.with_log=work/'with_parent_events.jsonl';r.object_log=work/'object_known.jsonl';r.action_log=work/'external_actions.jsonl';r.request_packet=work/'pending_request.json';r._log_mark=(0,0,0,0)
        r.pending_gates=list(z.get('pending_gates',[]))
        if file_sha_if_exists(r.revealed)!=z['revealed_sha256']:raise RuntimeErrorV9('revealed consumed file changed')
        for key,path in [('semantic_log_sha256',r.semantic_log),('counter_log_sha256',r.counter_log),('with_parent_log_sha256',r.with_log),('object_log_sha256',r.object_log),('action_log_sha256',r.action_log)]:
            if z.get(key)!=file_sha_if_exists(path):raise RuntimeErrorV9(f'{path.name} changed')
        return r

    @staticmethod
    def _process_due(m:MarketMachine,due:list[CompletedBar]):
        i=0
        while i<len(due):
            known=due[i].known_at;j=i
            while j<len(due) and due[j].known_at==known:m.process_bar(due[j]);j+=1
            if m.observer and hasattr(m.observer,'on_information_batch_complete'):m.observer.on_information_batch_complete(known,m)
            i=j

    def _drain_logs(self):
        append_jsonl(self.semantic_log,[e.row() for e in self.market.events]);self.market.events=[]
        append_jsonl(self.counter_log,[e.row() for e in self.observer.counter.events]);self.observer.counter.events=[]
        append_jsonl(self.with_log,[e.row() for e in self.observer.with_parent.events]);self.observer.with_parent.events=[]
        append_jsonl(self.object_log,self.observer.object_creation_rows);self.observer.object_creation_rows=[]

    def _finish_range(self):
        if self.active_block is None:return
        self._process_due(self.market,self.buckets.flush_block(self.active_block));self.market.finish_block(self.active_block)
        self.active_block=None;self.range_i+=1
        if self.range_i<len(self.index['ranges']):self.resume_offset=int(self.index['ranges'][self.range_i]['start_offset'])

    def run_to(self,cutoff:datetime):
        # cutoff must belong to an allowed block.
        target_i=None
        for i,q in enumerate(self.index['ranges']):
            if dt(q['start'])<=cutoff<dt(q['end']):target_i=i;break
        if target_i is None:raise RuntimeErrorV9('cutoff is outside consumed allowed ranges')
        if target_i<self.range_i:raise RuntimeErrorV9('cutoff precedes current runtime range')
        idxmap={v:i for i,v in enumerate(EXPECTED_HEADER)};found=False
        with self.source.open('rb') as f, self.revealed.open('ab') as rv:
            while self.range_i<len(self.index['ranges']):
                q=self.index['ranges'][self.range_i];block=q['block'];end_off=int(q['end_offset'])
                if self.active_block is None:self.active_block=block
                f.seek(self.resume_offset)
                while f.tell()<end_off:
                    pos=f.tell();raw=f.readline()
                    if not raw:raise RuntimeErrorV9('unexpected EOF inside consumed range')
                    h=raw.split(b'\t',2);ts=fast_ts(h[0].decode('ascii'),h[1].decode('ascii'))
                    if self.last_source_ts is not None and ts<=self.last_source_ts:raise RuntimeErrorV9('source chronology moved backward')
                    if self.range_i==target_i and ts>cutoff:
                        self.resume_offset=pos;self._drain_logs();return False
                    self._process_due(self.market,self.buckets.due_before_row(ts,block))
                    p=raw.decode('ascii').rstrip('\r\n').split('\t');row=M1Row(ts,float(p[idxmap['<OPEN>']]),float(p[idxmap['<HIGH>']]),float(p[idxmap['<LOW>']]),float(p[idxmap['<CLOSE>']]))
                    self.market.process_price(row,block);self.buckets.add_row(block,row);rv.write(raw);self.revealed_rows+=1;self.last_source_ts=ts;self.resume_offset=f.tell()
                    if self.range_i==target_i and ts==cutoff:
                        found=True;self._drain_logs();return True
                self._finish_range();self._drain_logs()
                if self.range_i>target_i:break
        if not found:raise RuntimeErrorV9('exact cutoff row not found in allowed range')
        return found

    def run_all(self):
        # use last actual row before each strict range end by processing until end_offset.
        idxmap={v:i for i,v in enumerate(EXPECTED_HEADER)}
        with self.source.open('rb') as f,self.revealed.open('ab') as rv:
            while self.range_i<len(self.index['ranges']):
                q=self.index['ranges'][self.range_i];block=q['block'];end_off=int(q['end_offset']);self.active_block=self.active_block or block;f.seek(self.resume_offset)
                while f.tell()<end_off:
                    raw=f.readline();h=raw.split(b'\t',2);ts=fast_ts(h[0].decode('ascii'),h[1].decode('ascii'))
                    self._process_due(self.market,self.buckets.due_before_row(ts,block));p=raw.decode('ascii').rstrip('\r\n').split('\t');row=M1Row(ts,float(p[idxmap['<OPEN>']]),float(p[idxmap['<HIGH>']]),float(p[idxmap['<LOW>']]),float(p[idxmap['<CLOSE>']]))
                    self.market.process_price(row,block);self.buckets.add_row(block,row);rv.write(raw);self.revealed_rows+=1;self.last_source_ts=ts;self.resume_offset=f.tell()
                self._finish_range();self._drain_logs()
        return True

    GATE_KINDS={
        'ENTRY_EXECUTION_REQUIRED',
        'REVIEW_REQUIRED',
        'REMAP_REQUIRED',
        'EXIT_EXECUTION_REQUIRED',
        'CROSS_LANE_CONFLICT_REVIEW',
    }
    GATE_PRIORITY={
        'EXIT_EXECUTION_REQUIRED':0,
        'REMAP_REQUIRED':1,
        'REVIEW_REQUIRED':2,
        'ENTRY_EXECUTION_REQUIRED':3,
        'CROSS_LANE_CONFLICT_REVIEW':4,
    }

    @staticmethod
    def _allowed_actions(kind:str)->list[dict]:
        if kind=='ENTRY_EXECUTION_REQUIRED':
            return [
                {'kind':'ENTRY_FILL','requires':['child_id','at','block','price']},
                {'kind':'ENTRY_NO_FILL','requires':['child_id','at','block']},
                {'kind':'ENTRY_CANCEL','requires':['child_id','at','block']},
            ]
        if kind=='REVIEW_REQUIRED':
            return [{'kind':'REVIEW_DECISION','requires':['child_id','at','block','decision'],'decision':['HOLD','EXIT','REMAP']}]
        if kind=='REMAP_REQUIRED':
            return [
                {'kind':'REMAP_RESULT','requires':['child_id','at','block','new_parent_id','new_parent_side','journey_role']},
                {'kind':'REVIEW_DECISION','requires':['child_id','at','block','decision'],'decision':['EXIT']},
            ]
        if kind=='EXIT_EXECUTION_REQUIRED':
            return [{'kind':'EXIT_FILL','requires':['child_id','at','block','price']}]
        if kind=='CROSS_LANE_CONFLICT_REVIEW':
            return [{'kind':'CONFLICT_DECISION','requires':['at','block','decision'],'decision':['SKIP_NEW_PITCH']}]
        return []

    def _gate_from_event(self,e)->dict:
        raw={
            'kind':e.kind,'known_at':fmt(e.known_at),'price_revealed_cutoff':fmt(e.price_revealed_cutoff),
            'block':e.block,'branch':e.branch,'child_id':e.child_id,'parent_id':e.parent_id,'side':e.side,
            'event_sequence':e.seq,'payload':e.payload,
        }
        ident=json.dumps(raw,sort_keys=True,separators=(',',':')).encode('utf-8')
        raw['gate_id']=hashlib.sha256(ident).hexdigest()[:24]
        raw['information_known_at']=fmt(self.market.information_known_at)
        raw['allowed_actions']=self._allowed_actions(e.kind)
        raw['market_snapshot']={
            'parent_id':self.market.parent.parent_id if self.market.parent else None,
            'parent_side':self.market.parent.side if self.market.parent else None,
            'h1_consensus':self.market.latest_h1.consensus if self.market.latest_h1 else None,
            'm15_consensus':self.market.latest_m15.consensus if self.market.latest_m15 else None,
            'last_revealed_m1':fmt(self.market.price_revealed_cutoff),
        }
        return raw

    def _capture_gates(self)->bool:
        events=[]
        for lane in (self.observer.counter,self.observer.with_parent):
            events.extend(e for e in lane.events if e.kind in self.GATE_KINDS)
        if events:
            # A normal run stops at the earliest gate immediately.  During an external
            # action, however, another same-batch gate may already be pending and the
            # action may emit a new gate (REVIEW EXIT -> EXIT execution).  Append new
            # packets without dropping the existing queue.
            events.sort(key=lambda e:(e.known_at,self.GATE_PRIORITY.get(e.kind,99),e.branch,e.seq))
            existing={g['gate_id'] for g in self.pending_gates}
            for e in events:
                g=self._gate_from_event(e)
                if g['gate_id'] not in existing:
                    self.pending_gates.append(g);existing.add(g['gate_id'])
        return bool(self.pending_gates)

    def next_gate(self)->Optional[dict]:
        return self.pending_gates[0] if self.pending_gates else None

    def run_until_gate(self)->dict:
        """Advance causally until the first external-action gate or consumed-data end.

        Semantic gates are detected after the full same-known-at information batch and
        before the next M1 OHLC is decoded.  Price-trigger gates are detected after that
        M1 row is revealed.  No future-hidden range is scanned; only frozen consumed
        byte ranges are sought directly.
        """
        if self.pending_gates:
            return {'status':'GATE','gate':self.pending_gates[0]}
        idxmap={v:i for i,v in enumerate(EXPECTED_HEADER)}
        with self.source.open('rb') as f,self.revealed.open('ab') as rv:
            while self.range_i<len(self.index['ranges']):
                q=self.index['ranges'][self.range_i];block=q['block'];end_off=int(q['end_offset'])
                self.active_block=self.active_block or block;f.seek(self.resume_offset)
                while f.tell()<end_off:
                    pos=f.tell();raw=f.readline()
                    if not raw: raise RuntimeErrorV9('unexpected EOF inside consumed range')
                    h=raw.split(b'\t',2);ts=fast_ts(h[0].decode('ascii'),h[1].decode('ascii'))
                    if self.last_source_ts is not None and ts<=self.last_source_ts:
                        raise RuntimeErrorV9('source chronology moved backward')
                    self._process_due(self.market,self.buckets.due_before_row(ts,block))
                    # Stop before decoding/revealing current-row OHLC if a completed-bar
                    # semantic batch created an external-action gate.
                    if self._capture_gates():
                        self.resume_offset=pos;self._drain_logs()
                        return {'status':'GATE','gate':self.pending_gates[0]}
                    p=raw.decode('ascii').rstrip('\r\n').split('\t')
                    row=M1Row(ts,float(p[idxmap['<OPEN>']]),float(p[idxmap['<HIGH>']]),float(p[idxmap['<LOW>']]),float(p[idxmap['<CLOSE>']]))
                    self.market.process_price(row,block);self.buckets.add_row(block,row);rv.write(raw)
                    self.revealed_rows+=1;self.last_source_ts=ts;self.resume_offset=f.tell()
                    if self._capture_gates():
                        self._drain_logs();return {'status':'GATE','gate':self.pending_gates[0]}
                self._finish_range()
                if self._capture_gates():
                    self._drain_logs();return {'status':'GATE','gate':self.pending_gates[0]}
                self._drain_logs()
        return {'status':'END_OF_CONSUMED','gate':None}

    def _validate_external_action_time(self,at:datetime):
        floor=self.market.price_revealed_cutoff
        ceil=self.market.information_known_at
        if floor is None or ceil is None: raise RuntimeErrorV9('runtime has no revealed market clock')
        if at<floor or at>ceil:
            raise RuntimeErrorV9(f'external action time must satisfy PRICE_REVEALED_CUTOFF <= at <= INFORMATION_KNOWN_AT; got {fmt(at)} vs {fmt(floor)}..{fmt(ceil)}')

    def apply_action(self,kind:str,*,child_id:Optional[str],at:datetime,block:str,**kw):
        if not self.pending_gates:
            raise RuntimeErrorV9('no pending external-action gate')
        gate=self.pending_gates[0];kind=kind.upper()
        allowed={x['kind'] for x in gate.get('allowed_actions',[])}
        if kind not in allowed:
            raise RuntimeErrorV9(f'action {kind} is not allowed for gate {gate["kind"]}; allowed={sorted(allowed)}')
        if block!=gate['block']:
            raise RuntimeErrorV9(f'action block {block} does not match gate block {gate["block"]}')
        gat=dt(gate['known_at'])
        if at!=gat:
            raise RuntimeErrorV9(f'action time must equal frozen gate known_at {gate["known_at"]}; got {fmt(at)}')
        if gate.get('child_id') and child_id!=gate['child_id']:
            raise RuntimeErrorV9(f'action child_id {child_id} does not match gate child {gate["child_id"]}')
        self._validate_external_action_time(at);cutoff=self.market.price_revealed_cutoff
        popped=self.pending_gates.pop(0)
        try:
            if kind=='ENTRY_FILL':
                self.observer.apply_entry_execution(child_id,at,float(kw['price']),block,cutoff)
            elif kind=='ENTRY_NO_FILL':
                self.observer.apply_entry_no_fill(child_id,at,block,cutoff)
            elif kind=='ENTRY_CANCEL':
                self.observer.apply_entry_cancel(child_id,at,block,cutoff)
            elif kind=='REVIEW_DECISION':
                decision=str(kw['decision']).upper()
                if gate['kind']=='REMAP_REQUIRED' and decision!='EXIT':
                    raise RuntimeErrorV9('REMAP_REQUIRED gate permits REVIEW_DECISION only with EXIT')
                self.observer.apply_review_decision(child_id,at,decision,block,cutoff)
            elif kind=='REMAP_RESULT':
                self.observer.apply_remap_result(child_id,at,block,price_cutoff=cutoff,new_parent_id=kw.get('new_parent_id'),new_parent_side=kw.get('new_parent_side'),journey_role=str(kw['journey_role']))
            elif kind=='EXIT_FILL':
                self.observer.apply_exit_execution(child_id,at,float(kw['price']),block,cutoff)
            elif kind=='CONFLICT_DECISION':
                decision=str(kw.get('decision','')).upper()
                if decision!='SKIP_NEW_PITCH':
                    raise RuntimeErrorV9('current fail-closed cross-lane authority supports only explicit SKIP_NEW_PITCH; other portfolio policies remain unresolved')
            else:
                raise RuntimeErrorV9(f'unsupported external action {kind}')
        except Exception:
            self.pending_gates.insert(0,popped)
            raise
        # An action may itself create the next gate (e.g. REVIEW EXIT -> EXIT execution).
        self._capture_gates()
        rec={'kind':kind,'gate_id':gate['gate_id'],'gate_kind':gate['kind'],'at':fmt(at),'price_revealed_cutoff':fmt(cutoff),'information_known_at':fmt(self.market.information_known_at),'block':block,'child_id':child_id,'payload':kw}
        append_jsonl(self.action_log,[rec]);self._drain_logs();return rec

    def state(self)->dict:
        self._drain_logs()
        return {'version':STATE_VERSION,'runner_version':RUNNER_VERSION,'semantic_runtime_version':'v9-semantic-runtime-1','strategy_runtime_version':STRATEGY_RUNTIME_VERSION,'authorization_version':AUTHORIZATION_VERSION,
                'source_basename':self.source.name,'source_sha256':self.index['source_sha256'],'source_size':self.index['source_size'],'source_index':self.index,
                'range_index':self.range_i,'active_block':self.active_block,'resume_offset':self.resume_offset,'last_source_ts':fmt(self.last_source_ts),'revealed_rows':self.revealed_rows,
                'revealed_sha256':file_sha_if_exists(self.revealed),'semantic_log_sha256':file_sha_if_exists(self.semantic_log),'counter_log_sha256':file_sha_if_exists(self.counter_log),'with_parent_log_sha256':file_sha_if_exists(self.with_log),'object_log_sha256':file_sha_if_exists(self.object_log),'action_log_sha256':file_sha_if_exists(self.action_log),
                'price_revealed_cutoff':fmt(self.market.price_revealed_cutoff),'information_known_at':fmt(self.market.information_known_at),
                'buckets':ser_buckets(self.buckets),'market':ser_market(self.market),'strategy':ser_observer(self.observer),
                'pending_gates':self.pending_gates,
                'future_hidden_2025_07':'LOCKED / OHLC not decoded by allowed-range replay'}

    def _write_request_packet(self):
        if self.pending_gates:
            atomic_write(self.request_packet,{'version':1,'runner_version':RUNNER_VERSION,'gates':self.pending_gates})
        elif self.request_packet.exists():
            self.request_packet.unlink()

    def save(self,state_path:Path):
        atomic_write(state_path,self.state());self._write_request_packet()


def cmd_index(a):
    if not a.research_provisioning_only:
        raise RuntimeErrorV9('range discovery is research provisioning only; normal runtime must use the frozen manifest')
    z=build_source_index(a.source);
    if z['ranges']!=FROZEN_CONSUMED_RANGES:
        raise RuntimeErrorV9('provisioned ranges differ from frozen consumed manifest')
    atomic_write(a.output,z);print(json.dumps(z,indent=2))
def load_index(p):return json.loads(p.read_text(encoding='utf-8'))
def cmd_init(a):
    work=a.state.parent;idx=load_index(a.index);r=V2Runner(a.source,idx,work,research_fill=a.research_assume_zone_touch_fill,independent=a.independent_lanes);r.run_to(a.cutoff);r.save(a.state);print(json.dumps({'ok':True,'state':str(a.state),'cutoff':fmt(r.market.price_revealed_cutoff),'known_at':fmt(r.market.information_known_at)},indent=2))
def cmd_advance(a):
    r=V2Runner.from_state(a.source,a.state);r.run_to(a.cutoff);r.save(a.state);print(json.dumps({'ok':True,'cutoff':fmt(r.market.price_revealed_cutoff),'known_at':fmt(r.market.information_known_at)},indent=2))
def cmd_run_all(a):
    idx=load_index(a.index);r=V2Runner(a.source,idx,a.state.parent,research_fill=a.research_assume_zone_touch_fill,independent=a.independent_lanes);r.run_all();r.save(a.state);print(json.dumps({'ok':True,'state':str(a.state),'range_index':r.range_i,'cutoff':fmt(r.market.price_revealed_cutoff)},indent=2))
def cmd_finish(a):
    r=V2Runner.from_state(a.source,a.state);r.run_all();r.save(a.state);print(json.dumps({'ok':True,'state':str(a.state),'range_index':r.range_i,'cutoff':fmt(r.market.price_revealed_cutoff)},indent=2))
def cmd_run_until_gate(a):
    if a.state.exists():
        r=V2Runner.from_state(a.source,a.state)
    else:
        if a.index is None: raise RuntimeErrorV9('--index is required when starting a new gate-driven runtime')
        r=V2Runner(a.source,load_index(a.index),a.state.parent,research_fill=a.research_assume_zone_touch_fill,independent=a.independent_lanes)
    result=r.run_until_gate();r.save(a.state)
    print(json.dumps({'ok':True,'state':str(a.state),**result,'cutoff':fmt(r.market.price_revealed_cutoff),'known_at':fmt(r.market.information_known_at)},indent=2,sort_keys=True))
def cmd_action(a):
    r=V2Runner.from_state(a.source,a.state);kw={}
    if a.kind in ('ENTRY_FILL','EXIT_FILL'):
        if a.price is None: raise RuntimeErrorV9(f'{a.kind} requires --price')
        kw['price']=a.price
    if a.kind=='REVIEW_DECISION':
        if a.decision is None: raise RuntimeErrorV9('REVIEW_DECISION requires --decision')
        kw['decision']=a.decision
    if a.kind=='CONFLICT_DECISION':
        if a.conflict_decision is None: raise RuntimeErrorV9('CONFLICT_DECISION requires --conflict-decision')
        kw['decision']=a.conflict_decision
    if a.kind=='REMAP_RESULT':
        if not a.journey_role: raise RuntimeErrorV9('REMAP_RESULT requires --journey-role')
        kw.update(new_parent_id=a.new_parent_id,new_parent_side=a.new_parent_side,journey_role=a.journey_role)
    rec=r.apply_action(a.kind,child_id=a.child_id,at=a.at,block=a.block,**kw);r.save(a.state);print(json.dumps({'action':rec,'next_gate':r.next_gate()},indent=2,sort_keys=True))

def cmd_audit(a):
    z=json.loads(a.state.read_text());print(json.dumps({'version':z['version'],'runner_version':z['runner_version'],'source_sha256':z['source_sha256'],'range_index':z['range_index'],'active_block':z['active_block'],'resume_offset':z['resume_offset'],'price_revealed_cutoff':z['price_revealed_cutoff'],'information_known_at':z['information_known_at'],'revealed_rows':z['revealed_rows'],'revealed_sha256_ok':file_sha_if_exists(a.state.parent/'revealed_consumed.tsv')==z['revealed_sha256'],'pending_gate':(z.get('pending_gates') or [None])[0]},indent=2))

def main():
    p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True)
    x=sp.add_parser('index');x.add_argument('--source',type=Path,required=True);x.add_argument('--output',type=Path,required=True);x.add_argument('--research-provisioning-only',action='store_true');x.set_defaults(fn=cmd_index)
    def common(x):
        x.add_argument('--source',type=Path,required=True);x.add_argument('--state',type=Path,required=True)
    x=sp.add_parser('init');common(x);x.add_argument('--index',type=Path,required=True);x.add_argument('--cutoff',type=lambda s:datetime.strptime(s,'%Y-%m-%d %H:%M:%S'),required=True);x.add_argument('--research-assume-zone-touch-fill',action='store_true');x.add_argument('--independent-lanes',action='store_true');x.set_defaults(fn=cmd_init)
    x=sp.add_parser('advance');common(x);x.add_argument('--cutoff',type=lambda s:datetime.strptime(s,'%Y-%m-%d %H:%M:%S'),required=True);x.set_defaults(fn=cmd_advance)
    x=sp.add_parser('run-all');common(x);x.add_argument('--index',type=Path,required=True);x.add_argument('--research-assume-zone-touch-fill',action='store_true');x.add_argument('--independent-lanes',action='store_true');x.set_defaults(fn=cmd_run_all)
    x=sp.add_parser('finish');common(x);x.set_defaults(fn=cmd_finish)
    x=sp.add_parser('run-until-gate');common(x);x.add_argument('--index',type=Path);x.add_argument('--research-assume-zone-touch-fill',action='store_true');x.add_argument('--independent-lanes',action='store_true');x.set_defaults(fn=cmd_run_until_gate)
    x=sp.add_parser('action');common(x);x.add_argument('--kind',choices=['ENTRY_FILL','ENTRY_NO_FILL','ENTRY_CANCEL','REVIEW_DECISION','REMAP_RESULT','EXIT_FILL','CONFLICT_DECISION'],required=True);x.add_argument('--child-id');x.add_argument('--at',type=lambda s:datetime.strptime(s,'%Y-%m-%d %H:%M:%S'),required=True);x.add_argument('--block',required=True);x.add_argument('--price',type=float);x.add_argument('--decision',choices=['HOLD','EXIT','REMAP']);x.add_argument('--conflict-decision',choices=['SKIP_NEW_PITCH']);x.add_argument('--new-parent-id');x.add_argument('--new-parent-side',choices=['UP','DOWN']);x.add_argument('--journey-role');x.set_defaults(fn=cmd_action)
    x=sp.add_parser('audit');x.add_argument('--state',type=Path,required=True);x.set_defaults(fn=cmd_audit)
    a=p.parse_args();a.fn(a)
if __name__=='__main__':main()
