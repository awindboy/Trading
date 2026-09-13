#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, math
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

TSFMT='%Y.%m.%d %H:%M:%S'
OUTFMT='%Y-%m-%d %H:%M:%S'
RUNTIME_VERSION='v9-arrival-delivery-multichild-era-runtime-1'
ERA_ATR_N=180
MAX_SL_ERA=4.0

@dataclass
class Bar:
    start:str; hours:int; open:float; high:float; low:float; close:float; last_ts:str

@dataclass
class Obj:
    id:str; tf:str; side:str; price:float; source:str; known_at:str

class TFState:
    def __init__(self,hours:int):
        self.hours=hours; self.current=None; self.recent=[]; self.active={}
        self.prev_close=None; self.tr_values=[]; self.atr180=None; self.finalized_count=0
    def bucket(self,ts:datetime):
        h=(ts.hour//self.hours)*self.hours
        return ts.replace(hour=h,minute=0,second=0,microsecond=0)
    def due_before(self,ts:datetime):
        if not self.current: return False
        st=datetime.strptime(self.current['start'],OUTFMT)
        return ts>=st+timedelta(hours=self.hours) and self.bucket(ts)!=st
    def finalize(self):
        b=self.current; self.current=None
        # Causal true-range / Wilder ATR180 on finalized H4 only.
        if self.hours==4:
            h=float(b['high']); l=float(b['low']); c=float(b['close'])
            tr=(h-l) if self.prev_close is None else max(h-l,abs(h-self.prev_close),abs(l-self.prev_close))
            self.tr_values.append(float(tr)); self.finalized_count+=1
            if self.atr180 is None and len(self.tr_values)>=ERA_ATR_N:
                self.atr180=sum(self.tr_values[-ERA_ATR_N:])/ERA_ATR_N
            elif self.atr180 is not None:
                self.atr180=(self.atr180*(ERA_ATR_N-1)+tr)/ERA_ATR_N
            self.prev_close=c
            if len(self.tr_values)>ERA_ATR_N: self.tr_values=self.tr_values[-ERA_ATR_N:]
        self.recent.append(b)
        if len(self.recent)>5: self.recent=self.recent[-5:]
        born=[]
        if len(self.recent)>=5:
            a=self.recent[-5:]
            c=a[2]; L=a[:2]; R=a[3:]
            known=datetime.strptime(a[-1]['start'],OUTFMT)+timedelta(hours=self.hours)
            tf=f'H{self.hours}'
            src=datetime.strptime(c['start'],OUTFMT)
            if c['high']>max(x['high'] for x in L) and c['high']>=max(x['high'] for x in R):
                oid=f'{tf}_BSL_{src:%Y%m%d_%H%M}'
                o={'id':oid,'tf':tf,'side':'UP','price':float(c['high']),'source':c['start'],'known_at':known.strftime(OUTFMT)}
                self.active[oid]=o; born.append(o)
            if c['low']<min(x['low'] for x in L) and c['low']<=min(x['low'] for x in R):
                oid=f'{tf}_SSL_{src:%Y%m%d_%H%M}'
                o={'id':oid,'tf':tf,'side':'DOWN','price':float(c['low']),'source':c['start'],'known_at':known.strftime(OUTFMT)}
                self.active[oid]=o; born.append(o)
        return born
    def update(self,ts:datetime,o,h,l,c):
        st=self.bucket(ts)
        if self.current is None:
            self.current={'start':st.strftime(OUTFMT),'hours':self.hours,'open':o,'high':h,'low':l,'close':c,'last_ts':ts.strftime(OUTFMT)}
        else:
            curst=datetime.strptime(self.current['start'],OUTFMT)
            if st!=curst:
                raise RuntimeError('bar must be finalized before new bucket')
            self.current['high']=max(self.current['high'],h); self.current['low']=min(self.current['low'],l); self.current['close']=c; self.current['last_ts']=ts.strftime(OUTFMT)
    def raid(self,ts:datetime,h:float,l:float):
        hit=[]
        for oid,o in list(self.active.items()):
            if (o['side']=='UP' and o['price']<h) or (o['side']=='DOWN' and o['price']>l):
                hit.append(o); del self.active[oid]
        return hit
    def to_state(self): return {'hours':self.hours,'current':self.current,'recent':self.recent,'active':self.active,'prev_close':self.prev_close,'tr_values':self.tr_values,'atr180':self.atr180,'finalized_count':self.finalized_count}
    @classmethod
    def from_state(cls,d):
        x=cls(d['hours']); x.current=d['current']; x.recent=d['recent']; x.active=d['active']; x.prev_close=d.get('prev_close'); x.tr_values=d.get('tr_values',[]); x.atr180=d.get('atr180'); x.finalized_count=d.get('finalized_count',0); return x

class Runtime:
    def __init__(self,block,policy='ONE_POSITION'):
        self.block=block; self.policy=policy
        self.h1=TFState(1); self.h4=TFState(4)
        self.state=None; self.primary=None
        self.children=[]
        self.price_revealed_cutoff=None; self.information_known_at=None
        self.arrivals=[]; self.trades=[]; self.objects=[]; self.rejections=[]
        self.row_index=0; self.last_exit_same_row=False
    def finalize_due(self,ts):
        born=[]
        # deterministic H1 then H4, but all due semantic info is known before row OHLC
        for tf in [self.h1,self.h4]:
            if tf.due_before(ts):
                born.extend(tf.finalize())
        if born:
            # information time can be earlier than current row around gaps
            self.information_known_at=max(o['known_at'] for o in born)
            self.objects.extend(born)
    def choose_sl(self,side,entry):
        vals=[]
        for o in self.h1.active.values():
            p=o['price']
            if side=='UP' and o['side']=='DOWN' and p<entry: vals.append(p)
            if side=='DOWN' and o['side']=='UP' and p>entry: vals.append(p)
        if not vals: return None
        return max(vals) if side=='UP' else min(vals)
    def close_child_obj(self,ch,ts,price,status):
        risk=abs(ch['entry']-ch['sl']); sign=1 if ch['direction']=='UP' else -1
        R=sign*(price-ch['entry'])/risk if status!='SL' else -1.0
        rec={**ch,'status':status,'exit_ts':ts.strftime(OUTFMT),'exit_price':price,'R':R}
        self.trades.append(rec)

    def process_row(self,ts,o,h,l,c,spread):
        self.last_exit_same_row=False
        self.finalize_due(ts)
        # Begin/update current bars only after due semantics are emitted.
        self.h1.update(ts,o,h,l,c); self.h4.update(ts,o,h,l,c)
        # reveal current price
        self.price_revealed_cutoff=ts.strftime(OUTFMT); self.information_known_at=ts.strftime(OUTFMT)
        h1hits=self.h1.raid(ts,h,l); h4hits=self.h4.raid(ts,h,l)
        # build arrival after all same-row H4 raids are known
        event=None
        if h4hits:
            sides={x['side'] for x in h4hits}
            if len(sides)==1:
                side=next(iter(sides)); ref=max(x['price'] for x in h4hits) if side=='UP' else min(x['price'] for x in h4hits)
                ups=[x['price'] for x in self.h4.active.values() if x['side']=='UP' and x['price']>ref]
                dns=[x['price'] for x in self.h4.active.values() if x['side']=='DOWN' and x['price']<ref]
                nb=min(ups) if ups else None; ns=max(dns) if dns else None
                before=self.state; eligible=False
                if self.state is None:
                    self.state='ACTIVE'; self.primary=side; res='SEED'
                elif self.state=='ACTIVE':
                    if side==self.primary:
                        res='PRIMARY_CONTINUES'; eligible=True
                    else:
                        self.state='CHALLENGED'; res='CHALLENGE_OPENS'
                else:
                    if side==self.primary:
                        self.state='ACTIVE'; res='OLD_PRIMARY_WINS'; eligible=True
                    else:
                        self.primary=side; self.state='ACTIVE'; res='CHALLENGER_EARNED'; eligible=True
                ds=do=None; topo=None
                if eligible:
                    if self.primary=='UP':
                        ds=(nb-ref) if nb is not None else None; do=(ref-ns) if ns is not None else None
                    else:
                        ds=(ref-ns) if ns is not None else None; do=(nb-ref) if nb is not None else None
                    if ds is None and do is None: topo='BOTH_TARGETS_MISSING'
                    elif ds is None: topo='NO_SAME_TARGET'
                    elif do is None: topo='NO_OPPOSITE_TARGET'
                    elif ds<do: topo='SAME_NEAREST'
                    else: topo='OPPOSITE_NEAREST'
                event={'block':self.block,'ts':ts.strftime(OUTFMT),'arrival_side':side,'ref':ref,'before':before,'after':self.state,'primary':self.primary,'resolution':res,'eligible':eligible,'topology':topo,'d_same':ds,'d_opp':do,'nearest_bsl':nb,'nearest_ssl':ns}
                self.arrivals.append(event)
        # Every Child owns its own fixed H1 structural SL.
        # A CHALLENGE_OPENS event is a common semantic exit boundary, but
        # same-M1 SL+challenge ambiguity is evaluated independently per Child.
        survivors=[]
        if self.children:
            challenge_event=(event is not None and event['resolution']=='CHALLENGE_OPENS')
            for ch in self.children:
                sl=ch['sl']; slhit=(l<=sl) if ch['direction']=='UP' else (h>=sl)
                challenge=(challenge_event and event['arrival_side']!=ch['direction'])
                if slhit and challenge:
                    self.trades.append({**ch,'status':'AMBIGUOUS','exit_ts':ts.strftime(OUTFMT),'exit_price':None,'R':None})
                elif slhit:
                    self.close_child_obj(ch,ts,sl,'SL')
                elif challenge:
                    self.close_child_obj(ch,ts,event['ref'],'CHALLENGE_OPENS')
                else:
                    survivors.append(ch)
            self.children=survivors
        # Every mechanically eligible PRIMARY_ACTIVE Arrival may open a new independent Child.
        # No aggregate child-count/risk cap is introduced here.
        if event is not None and event['eligible']:
            entry=event['ref']; side=event['primary']; sl=self.choose_sl(side,entry)
            atr180=self.h4.atr180
            reason=None; ratio=None; dist=None
            if sl is None or not ((side=='UP' and sl<entry) or (side=='DOWN' and sl>entry)):
                reason='NO_VALID_H1_STRUCT_SL'
            else:
                dist=abs(entry-sl)
                if atr180 is None or not (atr180>0):
                    reason='ATR180_WARMUP'
                else:
                    ratio=dist/atr180
                    if ratio>MAX_SL_ERA:
                        reason='SL_ERA_GT_4'
            event['structural_sl']=sl; event['sl_dist']=dist; event['atr180']=atr180; event['sl_atr180']=ratio; event['entry_authorized']=(reason is None); event['entry_reject_reason']=reason
            if reason is None:
                self.children.append({'block':self.block,'entry_ts':ts.strftime(OUTFMT),'direction':side,'entry':entry,'sl':sl,'sl_dist':dist,'atr180':atr180,'sl_atr180':ratio,'topology':event['topology'],'d_same':event['d_same'],'d_opp':event['d_opp'],'policy':'MULTI_CHILD_ERA4'})
            else:
                self.rejections.append({'block':self.block,'entry_ts':ts.strftime(OUTFMT),'direction':side,'entry':entry,'sl':sl,'sl_dist':dist,'atr180':atr180,'sl_atr180':ratio,'reason':reason})
        self.row_index+=1
    def finish(self,last_ts):
        for ch in self.children:
            self.trades.append({**ch,'status':'OPEN_CENSORED','exit_ts':None,'exit_price':None,'R':None})
        self.children=[]
    def state_dict(self):
        return {'version':RUNTIME_VERSION,'block':self.block,'policy':self.policy,'h1':self.h1.to_state(),'h4':self.h4.to_state(),'state':self.state,'primary':self.primary,'children':self.children,'price_revealed_cutoff':self.price_revealed_cutoff,'information_known_at':self.information_known_at,'arrivals':self.arrivals,'trades':self.trades,'objects':self.objects,'rejections':self.rejections,'row_index':self.row_index}
    @classmethod
    def from_state(cls,d):
        x=cls(d['block'],d['policy']); x.h1=TFState.from_state(d['h1']); x.h4=TFState.from_state(d['h4']); x.state=d['state']; x.primary=d['primary']; x.children=d.get('children',[]); x.price_revealed_cutoff=d['price_revealed_cutoff']; x.information_known_at=d['information_known_at']; x.arrivals=d['arrivals']; x.trades=d['trades']; x.objects=d['objects']; x.rejections=d.get('rejections',[]); x.row_index=d['row_index']; return x

def file_sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def load_rows(path,start_offset=None,end_offset=None,expected_sha256=None):
    if expected_sha256 and file_sha256(path)!=expected_sha256:
        raise RuntimeError('source SHA256 mismatch')
    if start_offset is not None or end_offset is not None:
        if start_offset is None or end_offset is None: raise RuntimeError('both offsets required')
        with open(path,'rb') as f:
            f.seek(start_offset); raw=f.read(end_offset-start_offset)
        text=raw.decode('utf-8')
        rd=csv.reader(text.splitlines(),delimiter='\t')
        for r in rd:
            if len(r)<9: continue
            ts=datetime.strptime(r[0]+' '+r[1],TSFMT)
            yield ts,float(r[2]),float(r[3]),float(r[4]),float(r[5]),float(r[8])
    else:
        with open(path,newline='',encoding='utf-8-sig') as f:
            rd=csv.DictReader(f,delimiter='\t')
            for r in rd:
                ts=datetime.strptime(r['<DATE>']+' '+r['<TIME>'],TSFMT)
                yield ts,float(r['<OPEN>']),float(r['<HIGH>']),float(r['<LOW>']),float(r['<CLOSE>']),float(r['<SPREAD>'])

def write_csv(path,rows):
    if not rows:
        Path(path).write_text('',encoding='utf-8'); return
    fields=[]
    seen=set()
    for row in rows:
        for k in row.keys():
            if k not in seen:
                seen.add(k); fields.append(k)
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def run(path,block,policy,outdir,split=None,state_in=None,state_out=None,finish=True,start_offset=None,end_offset=None,expected_sha256=None):
    rows=list(load_rows(path,start_offset,end_offset,expected_sha256))
    rt=Runtime(block,policy) if state_in is None else Runtime.from_state(json.loads(Path(state_in).read_text()))
    start=rt.row_index
    stop=len(rows) if split is None else min(split,len(rows))
    for row in rows[start:stop]: rt.process_row(*row)
    if finish and stop==len(rows): rt.finish(rows[-1][0])
    od=Path(outdir); od.mkdir(parents=True,exist_ok=True)
    write_csv(od/f'{block}_{policy}_ARRIVALS.csv',rt.arrivals)
    write_csv(od/f'{block}_{policy}_TRADES.csv',rt.trades)
    write_csv(od/f'{block}_{policy}_OBJECTS.csv',rt.objects)
    write_csv(od/f'{block}_{policy}_REJECTIONS.csv',rt.rejections)
    if state_out: Path(state_out).write_text(json.dumps(rt.state_dict(),separators=(',',':')))
    return rt

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--m1',required=True); ap.add_argument('--start-offset',type=int); ap.add_argument('--end-offset',type=int); ap.add_argument('--expected-sha256'); ap.add_argument('--block',required=True); ap.add_argument('--policy',choices=['MULTI_CHILD'],default='MULTI_CHILD'); ap.add_argument('--out',required=True); ap.add_argument('--split',type=int); ap.add_argument('--state-in'); ap.add_argument('--state-out'); ap.add_argument('--no-finish',action='store_true')
    a=ap.parse_args(); run(a.m1,a.block,a.policy,a.out,a.split,a.state_in,a.state_out,not a.no_finish,a.start_offset,a.end_offset,a.expected_sha256)
if __name__=='__main__': main()
