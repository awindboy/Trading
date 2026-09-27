from __future__ import annotations
import csv, math, statistics, json, hashlib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

H4=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv')
H1=Path('/mnt/data/GOLD#_H1_202201030100_202608282300.csv')
START=datetime(2024,1,1)
LAST_EXECUTION_OPEN=datetime(2026,8,28,20)

@dataclass
class Bar:
    time: datetime; open: float; high: float; low: float; close: float

def stamp(r): return datetime.strptime(r['<DATE>']+' '+r['<TIME>'],'%Y.%m.%d %H:%M:%S')
def read(path):
    z=[]
    with path.open(newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f,delimiter='\t'):
            z.append(Bar(stamp(r),*(float(r[k]) for k in ('<OPEN>','<HIGH>','<LOW>','<CLOSE>'))))
    assert all(a.time<b.time for a,b in zip(z,z[1:])); return z
class HA:
    def __init__(self): self.o=self.c=None; self.color=0; self.streak=0
    def update(self,b):
        hc=(b.open+b.high+b.low+b.close)/4
        ho=(b.open+b.close)/2 if self.o is None else (self.o+self.c)/2
        hh=max(b.high,ho,hc); hl=min(b.low,ho,hc)
        old=self.color; color=1 if hc>ho else -1 if hc<ho else old
        self.streak=self.streak+1 if old and color==old else 1
        self.o,self.c,self.color=ho,hc,color
        up=hh-max(ho,hc); low=min(ho,hc)-hl; rg=hh-hl
        return {'ha_open':ho,'ha_close':hc,'ha_high':hh,'ha_low':hl,'color':color,'prior_color':old,
                'delta':hc-ho,'abs_delta':abs(hc-ho),'body_ratio':abs(hc-ho)/rg if rg else 0.0,
                'opposite_wick':low if color==1 else up,'streak':self.streak}

def paper_self_test():
    vals=[
      (66.45,66.45),(66.45,66.445),(66.4475,66.45),(66.44875,66.44),(66.44438,66.5),
      (66.47219,66.51),(66.49109,66.51),(66.50055,66.78),(66.64027,66.79),(66.71514,66.70313),
      (66.70913,66.70375),(66.70644,66.7325)]
    d=[o-c for o,c in vals]; got=[]
    for i in range(9,len(d)):
        w=d[i-9:i+1]; got.append(100*(d[i]-min(w))/(max(w)-min(w)))
    exp=[100.000,97.725,86.938]
    assert all(abs(x-y)<.003 for x,y in zip(got,exp)),got
    return [round(x,3) for x in got]

def interaction(b, level, direction, prior_close, prior_origin):
    if level is None: return 'no_level'
    price, origin = level
    extreme=(b.high>price) if direction==1 else (b.low<price)
    cb=(b.close>price) if direction==1 else (b.close<price)
    pb=False
    if prior_close is not None and prior_origin==origin:
        pb=(prior_close>price) if direction==1 else (prior_close<price)
    if cb: return 'held_close_beyond' if pb else 'fresh_close_beyond'
    if pb: return 'return_inside'
    if extreme: return 'probe_rejected'
    return 'no_break'

def build():
    h4=read(H4); h1=read(H1)
    # Full H4 standard HA and HASTOC warmup
    hs=HA(); hf=[]; dh=[]
    for b in h4:
        f=hs.update(b); d=f['ha_open']-f['ha_close']; dh.append(d)
        hv=width=None
        if len(dh)>=10:
            w=dh[-10:]; width=max(w)-min(w)
            hv=100*(d-min(w))/width if width else None
        hf.append({**f,'hastoc10':hv,'hastoc_width':width})
    # Full H1 standard HA; map by time for efficient slices
    h1s=HA(); h1f=[]
    for b in h1:
        f=h1s.update(b); h1f.append((b.time,f))
    h1_times=[t for t,_ in h1f]
    import bisect

    decisions=[]; active=None; jid=0; jbar=0
    five=[]; last_hi=last_lo=None; prior_close=None; prev_hi_origin=prev_lo_origin=None
    for i,(b,nxt) in enumerate(zip(h4,h4[1:])):
        f=hf[i]; side=f['color']
        # HA5 states against levels already known before this bar.
        pl=last_hi if side==1 else last_lo; al=last_lo if side==1 else last_hi
        por=prev_hi_origin if side==1 else prev_lo_origin; aor=prev_lo_origin if side==1 else prev_hi_origin
        ps=interaction(b,pl,side,prior_close,por); ads=interaction(b,al,-side,prior_close,aor)

        if b.time>=START and nxt.time<=LAST_EXECUTION_OPEN:
            if active is not None and side!=active: active=None
            if active is None and f['prior_color']!=0 and side!=f['prior_color']:
                jid+=1; active=side; jbar=0
            if active is not None:
                jbar+=1
                lo=bisect.bisect_left(h1_times,b.time); hi=bisect.bisect_left(h1_times,nxt.time)
                inside=[v for _,v in h1f[lo:hi]]
                opposed=[x['color']!=side for x in inside]
                trailing=0
                for x in reversed(opposed):
                    if not x: break
                    trailing+=1
                path=('no_opposition' if not any(opposed) else 'repaired' if not opposed[-1]
                      else 'persistent_opposition' if all(opposed) else 'unrepaired_mixed')
                rawrg=b.high-b.low
                prev=decisions[-1] if decisions and decisions[-1]['journey']==jid else None
                jh=None if f['hastoc10'] is None else (100-f['hastoc10'] if side==1 else f['hastoc10'])
                decisions.append({
                    'idx_h4':i,'signal':b.time,'known_at':nxt.time,'journey':jid,'side':side,'journey_bar':jbar,'year':b.time.year,
                    'raw_open':b.open,'raw_high':b.high,'raw_low':b.low,'raw_close':b.close,'execution_raw_open':nxt.open,
                    'h4_body_ratio':f['body_ratio'],'h4_abs_delta':f['abs_delta'],
                    'h4_raw_close_normalized':side*(b.close-f['ha_close'])/rawrg if rawrg else 0.0,
                    'h4_delta_contract': prev is not None and f['abs_delta']<prev['h4_abs_delta'],
                    'h4_wick_present':f['opposite_wick']>1e-9,
                    'h1_path_state':path,'h1_opposed':trailing>0,'h1_trailing_opposed':trailing,
                    'progress_state':ps,'adverse_state':ads,'progress_rejection_or_return':ps in ('probe_rejected','return_inside'),
                    'hastoc10':f['hastoc10'],'journey_hastoc10':jh,
                    'journey_hastoc_change':None if prev is None or jh is None or prev['journey_hastoc10'] is None else jh-prev['journey_hastoc10'],
                    'hastoc_width':f['hastoc_width']})
        # Continuity markers reflect the active level used for this bar.
        prev_hi_origin=last_hi[1] if last_hi else None; prev_lo_origin=last_lo[1] if last_lo else None
        prior_close=b.close
        five.append(b)
        if len(five)>5: five.pop(0)
        if len(five)==5:
            c=five[2]; oth=[five[j] for j in (0,1,3,4)]
            if all(c.high>x.high for x in oth): last_hi=(c.high,c.time)
            if all(c.low<x.low for x in oth): last_lo=(c.low,c.time)
    assert len(decisions)==4108, len(decisions)
    assert len({r['journey'] for r in decisions})==966
    byj=defaultdict(list)
    for n,r in enumerate(decisions): byj[r['journey']].append(n)
    assert sum(min(10,len(byj[j])) for j in range(1,966))==3858

    # HA4C-style future labels using raw H4 extrema (HA5 established M1/H4 OHLC parity).
    labels=[]
    for i,r in enumerate(decisions):
        if i+3>=len(decisions): continue
        ids=byj[r['journey']]; end=ids[-1]
        if end+1>=len(decisions): continue
        stop=end+1
        future=decisions[i+1:stop+1]
        extreme=max(x['raw_high'] for x in future) if r['side']==1 else min(x['raw_low'] for x in future)
        entry=r['execution_raw_open']; exitp=decisions[stop]['execution_raw_open']
        favorable=max(0.0,r['side']*(extreme-entry)); giveback=r['side']*(extreme-exitp)
        # Future-defined "final peak already past": use completed raw history before current execution open vs final Journey extreme.
        jstart=ids[0]; hist=decisions[jstart:i+1]
        past=max(x['raw_high'] for x in hist) if r['side']==1 else min(x['raw_low'] for x in hist)
        peak_already=(past>=extreme) if r['side']==1 else (past<=extreme)
        scale=None
        # Scale uses last 20 source H4 bars, not last 20 active decisions.
        src_i=r['idx_h4']
        if src_i>=19:
            ranges=[h4[k].high-h4[k].low for k in range(src_i-19,src_i+1)]
            scale=statistics.median(ranges)
        labels.append({'signal':r['signal'],'journey':r['journey'],'next_flip':decisions[i+1]['side']!=r['side'],
                       'flip_within_3':any(decisions[k]['side']!=r['side'] for k in range(i+1,i+4)),
                       'peak_already':peak_already,'journey_closed_bars':len(ids),
                       'remaining_favorable_ranges':favorable/scale if scale else None,
                       'giveback_ranges':giveback/scale if scale else None})
    assert len(labels)==4105, len(labels)
    return h4,decisions,labels

def rate(rows,k): return sum(bool(r[k]) for r in rows)/len(rows) if rows else None
def med(vals):
    z=[v for v in vals if v is not None and math.isfinite(v)]
    return statistics.median(z) if z else None
def summ(rows):
    return {'n':len(rows),'journeys':len({r['journey'] for r in rows}),'next_flip':rate(rows,'next_flip'),
            'flip_within_3':rate(rows,'flip_within_3'),'peak_already':rate(rows,'peak_already'),
            'remain_med':med([r['remaining_favorable_ranges'] for r in rows]),'giveback_med':med([r['giveback_ranges'] for r in rows])}
def rankmap(rows,key,n=5):
    z=sorted([r for r in rows if r[key] is not None],key=lambda r:r[key]); return {id(r):min(n-1,i*n//len(z)) for i,r in enumerate(z)}
def qs(rows,key,n=5):
    m=rankmap(rows,key,n); return {str(q+1):summ([r for r in rows if m.get(id(r))==q]) for q in range(n)}
def pearson(rows,a,b):
    z=[(r[a],r[b]) for r in rows if r[a] is not None and r[b] is not None]
    mx=statistics.mean(x for x,y in z); my=statistics.mean(y for x,y in z)
    num=sum((x-mx)*(y-my) for x,y in z); den=(sum((x-mx)**2 for x,y in z)*sum((y-my)**2 for x,y in z))**.5
    return num/den if den else None

def overlap_extremes(rows,key,extras=(),min_each=10):
    q=rankmap(rows,key,5); b=rankmap(rows,'h4_body_ratio',3); c=rankmap(rows,'h4_raw_close_normalized',3)
    cells=defaultdict(list)
    for r in rows:
        if id(r) in q: cells[(b[id(r)],c[id(r)],*(r[e] for e in extras))].append(r)
    elig=[]
    for cell in cells.values():
        lo=[r for r in cell if q[id(r)]==0]; hi=[r for r in cell if q[id(r)]==4]
        if len(lo)>=min_each and len(hi)>=min_each: elig.append((lo,hi,min(len(lo),len(hi))))
    w=sum(x[2] for x in elig)
    out={'cells':len(elig),'rows':sum(len(a)+len(b) for a,b,_ in elig),'total':len(rows),'min_each':min_each,'extras':list(extras)}
    for target in ('next_flip','flip_within_3','peak_already'):
        out['q1_minus_q5_'+target]=sum(ww*(rate(a,target)-rate(b,target)) for a,b,ww in elig)/w if w else None
    return out

def analyze(decisions,labels):
    d={r['signal']:r for r in decisions}; rows=[{**d[l['signal']],**l} for l in labels]
    # Receipt parity gates.
    pc={k:sum(r['h1_path_state']==k for r in rows) for k in sorted({r['h1_path_state'] for r in rows})}
    assert pc['no_opposition']==1637,pc
    assert pc['repaired']==1073,pc
    assert pc['persistent_opposition']+pc['unrepaired_mixed']==1395,pc
    opp=[r for r in rows if r['h1_opposed']]; assert len(opp)==1395
    flag=[r for r in opp if r['progress_rejection_or_return']]
    assert len(flag)==235,(len(flag),pc)
    assert sum(r['next_flip'] for r in flag)==138,sum(r['next_flip'] for r in flag)

    out={'paper_self_test':paper_self_test(),'all':summ(rows),'path_counts':pc,'hastoc_missing':sum(r['journey_hastoc10'] is None for r in rows),
         'hastoc_quintiles':qs(rows,'journey_hastoc10'),'change_quintiles':qs([r for r in rows if r['journey_hastoc_change'] is not None],'journey_hastoc_change'),
         'corr_hastoc_body_ratio':pearson(rows,'journey_hastoc10','h4_body_ratio'),
         'corr_hastoc_abs_delta':pearson(rows,'journey_hastoc10','h4_abs_delta')}
    out['overlap_h4_geometry']=overlap_extremes(rows,'journey_hastoc10')
    out['overlap_h4_delta_wick']=overlap_extremes(rows,'journey_hastoc10',('h4_delta_contract','h4_wick_present'))
    out['overlap_plus_h1']=overlap_extremes(rows,'journey_hastoc10',('h4_delta_contract','h4_wick_present','h1_path_state'),5)
    out['overlap_plus_h1_ha5']=overlap_extremes(rows,'journey_hastoc10',('h4_delta_contract','h4_wick_present','h1_path_state','progress_rejection_or_return'),5)
    out['continuation_quintiles']=qs([r for r in rows if r['journey_bar']>1],'journey_hastoc10')
    out['year_side']={}
    for y in (2024,2025,2026):
      for s in (1,-1): out['year_side'][f'{y}_{"L" if s==1 else "S"}']=qs([r for r in rows if r['year']==y and r['side']==s],'journey_hastoc10')
    # Long Journey tail using lowest relative-HASTOC quintile as diagnostic display only.
    q=rankmap(rows,'journey_hastoc10',5); tails=[r for r in rows if r['journey_closed_bars']>=10]; weak=[r for r in tails if q.get(id(r))==0]
    out['long_tail']={'journeys':len({r['journey'] for r in tails}),'q1_journeys':len({r['journey'] for r in weak}),'q1_n':len(weak),
                      'q1_next_flip':sum(r['next_flip'] for r in weak),'q1_not_next_flip':sum(not r['next_flip'] for r in weak),
                      'q1_remain_med':med([r['remaining_favorable_ranges'] for r in weak])}
    # H1-opposed only: HASTOC quintiles and HA5 flag cross context.
    out['h1_opposed_hastoc_quintiles']=qs(opp,'journey_hastoc10')
    out['h1_opposed_ha5_cross']={}
    qm=rankmap(opp,'journey_hastoc10',5)
    for qv in range(5):
        for f in (False,True):
            z=[r for r in opp if qm.get(id(r))==qv and r['progress_rejection_or_return']==f]
            out['h1_opposed_ha5_cross'][f'q{qv+1}_ha5_{int(f)}']=summ(z)
    return out,rows

if __name__=='__main__':
    h4,d,l=build(); out,rows=analyze(d,l)
    Path('/mnt/data/v13_ha6a').mkdir(exist_ok=True)
    Path('/mnt/data/v13_ha6a/summary.json').write_text(json.dumps(out,indent=2,default=str),encoding='utf-8')
    print(json.dumps(out,indent=2,default=str))
