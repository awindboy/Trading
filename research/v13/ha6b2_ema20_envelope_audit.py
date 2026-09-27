from __future__ import annotations
import sys, importlib.util, json, math, statistics
from pathlib import Path
from collections import defaultdict

P=Path('/mnt/data/v13_ha6b/ha6b1_ema50_context_audit.py')
spec=importlib.util.spec_from_file_location('ha6b1',P); m=importlib.util.module_from_spec(spec); sys.modules['ha6b1']=m; spec.loader.exec_module(m)
OUT=Path('/mnt/data/v13_ha6b')

def ema(values,period,seed='sma'):
    a=2/(period+1); out=[None]*len(values)
    if seed=='sma':
        e=sum(values[:period])/period; out[period-1]=e; start=period
    else:
        e=values[0]; out[0]=e; start=1
    for i in range(start,len(values)):
        e=a*values[i]+(1-a)*e; out[i]=e
    return out

def rate(rows,k): return sum(bool(r[k]) for r in rows)/len(rows) if rows else None

def med(vals):
    z=[v for v in vals if v is not None and math.isfinite(v)]; return statistics.median(z) if z else None

def summ(rows):
    return {'n':len(rows),'journeys':len({r['journey'] for r in rows}),'next_flip':rate(rows,'next_flip'),
            'flip_within_3':rate(rows,'flip_within_3'),'peak_already':rate(rows,'peak_already'),
            'remain_med':med([r['remaining_favorable_ranges'] for r in rows]),
            'giveback_med':med([r['giveback_ranges'] for r in rows])}

def rankmap(rows,key,n=5):
    z=sorted([r for r in rows if r.get(key) is not None and math.isfinite(r[key])],key=lambda r:r[key])
    return {id(r):min(n-1,i*n//len(z)) for i,r in enumerate(z)}

def qs(rows,key,n=5):
    q=rankmap(rows,key,n); return {str(i+1):summ([r for r in rows if q.get(id(r))==i]) for i in range(n)}

def cat(rows,key): return {str(v):summ([r for r in rows if r[key]==v]) for v in sorted({r[key] for r in rows},key=str)}

def overlap(rows,field,extras=(),min_each=5,include_hastoc=False,include_ema50=False):
    b=rankmap(rows,'h4_body_ratio',3); c=rankmap(rows,'h4_raw_close_normalized',3)
    h=rankmap(rows,'journey_hastoc10',3) if include_hastoc else None
    cells=defaultdict(list)
    for r in rows:
        key=(b[id(r)],c[id(r)],*(r[e] for e in extras))
        if include_hastoc:key=(*key,h.get(id(r)))
        if include_ema50:key=(*key,r['ema50_slope_aligned'],r['ema50_position_aligned'])
        cells[key].append(r)
    elig=[]
    for cell in cells.values():
        yes=[r for r in cell if r[field]]; no=[r for r in cell if not r[field]]
        if len(yes)>=min_each and len(no)>=min_each:elig.append((yes,no,min(len(yes),len(no))))
    w=sum(x[2] for x in elig)
    out={'cells':len(elig),'rows':sum(len(a)+len(b) for a,b,_ in elig),'total':len(rows),'min_each':min_each,
         'extras':list(extras),'hastoc_tertile':include_hastoc,'ema50_context':include_ema50}
    for t in ('next_flip','flip_within_3','peak_already'):
        out['not_beyond_minus_beyond_'+t]=sum(ww*(rate(no,t)-rate(yes,t)) for yes,no,ww in elig)/w if w else None
    return out

def main():
    h4,d,l=m.ha6a.build(); m.add_ema(h4,d)
    highs=[x.high for x in h4]; lows=[x.low for x in h4]
    eh=ema(highs,20,'sma'); el=ema(lows,20,'sma'); eh2=ema(highs,20,'first'); el2=ema(lows,20,'first')
    idx=[r['idx_h4'] for r in d]
    sens={'high_max_abs':max(abs(eh[i]-eh2[i]) for i in idx),'low_max_abs':max(abs(el[i]-el2[i]) for i in idx)}
    for r in d:
        i=r['idx_h4']; hc=(r['raw_open']+r['raw_high']+r['raw_low']+r['raw_close'])/4
        boundary=eh[i] if r['side']==1 else el[i]
        dist=r['side']*(hc-boundary)/boundary
        r['ema20_directional_boundary']=boundary; r['journey_ha_close_to_ema20_boundary_pct']=dist
        r['ema20_beyond_directional_boundary']=dist>0
    dm={r['signal']:r for r in d}; rows=[{**dm[x['signal']],**x} for x in l]
    assert len(rows)==4105
    out={'all':summ(rows),'seed_sensitivity':sens,'beyond':cat(rows,'ema20_beyond_directional_boundary'),
         'distance_quintiles':qs(rows,'journey_ha_close_to_ema20_boundary_pct'),
         'continuation':{'all':summ([r for r in rows if r['journey_bar']>1]),
                         'beyond':cat([r for r in rows if r['journey_bar']>1],'ema20_beyond_directional_boundary')}}
    out['overlap_h4']=overlap(rows,'ema20_beyond_directional_boundary',(),10)
    out['overlap_h4_delta_wick']=overlap(rows,'ema20_beyond_directional_boundary',('h4_delta_contract','h4_wick_present'),10)
    out['overlap_plus_h1_ha5']=overlap(rows,'ema20_beyond_directional_boundary',('h4_delta_contract','h4_wick_present','h1_path_state','progress_rejection_or_return'),5)
    out['overlap_plus_hastoc']=overlap(rows,'ema20_beyond_directional_boundary',('h4_delta_contract','h4_wick_present','h1_path_state','progress_rejection_or_return'),5,True,False)
    out['overlap_plus_all_prior']=overlap(rows,'ema20_beyond_directional_boundary',('h4_delta_contract','h4_wick_present','h1_path_state','progress_rejection_or_return'),5,True,True)
    opp=[r for r in rows if r['h1_opposed']]
    out['h1_opposed']={'all':summ(opp),'beyond':cat(opp,'ema20_beyond_directional_boundary'),
      'overlap_prior':overlap(opp,'ema20_beyond_directional_boundary',('h4_delta_contract','h4_wick_present','progress_rejection_or_return'),5,True,True)}
    out['year_side']={}
    for y in (2024,2025,2026):
      for s in (1,-1):
        z=[r for r in rows if r['year']==y and r['side']==s]; out['year_side'][f'{y}_{"L" if s==1 else "S"}']=cat(z,'ema20_beyond_directional_boundary')
    births=[r for r in rows if r['journey_bar']==1]
    out['birth']={'beyond':cat(births,'ema20_beyond_directional_boundary')}
    tails=[r for r in rows if r['journey_closed_bars']>=10]; assert len({r['journey'] for r in tails})==88
    weak=[r for r in tails if not r['ema20_beyond_directional_boundary']]
    out['long_tail']={'journeys':88,'warnings_journeys':len({r['journey'] for r in weak}),'warnings':len(weak),
      'not_next_flip':sum(not r['next_flip'] for r in weak),'next_flip':sum(r['next_flip'] for r in weak),
      'remaining_favorable_median':med([r['remaining_favorable_ranges'] for r in weak])}
    (OUT/'ha6b2_summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
