from __future__ import annotations
import importlib.util, json, math, statistics, hashlib, sys
from pathlib import Path
from collections import defaultdict

HA6A_PATH=Path('/mnt/data/v13_ha6a/ha6a_hastoc_audit.py')
OUT=Path('/mnt/data/v13_ha6b')

spec=importlib.util.spec_from_file_location('ha6a',HA6A_PATH)
ha6a=importlib.util.module_from_spec(spec); sys.modules['ha6a']=ha6a; spec.loader.exec_module(ha6a)


def ema_series(values, period=50, seed='sma'):
    alpha=2.0/(period+1.0)
    out=[None]*len(values)
    if seed=='sma':
        assert len(values)>=period
        e=sum(values[:period])/period
        out[period-1]=e
        start=period
    elif seed=='first':
        e=values[0]; out[0]=e; start=1
    else: raise ValueError(seed)
    for i in range(start,len(values)):
        e=alpha*values[i]+(1-alpha)*e
        out[i]=e
    return out


def rate(rows,key): return sum(bool(r[key]) for r in rows)/len(rows) if rows else None

def med(vals):
    z=[v for v in vals if v is not None and math.isfinite(v)]
    return statistics.median(z) if z else None

def summ(rows):
    return {'n':len(rows),'journeys':len({r['journey'] for r in rows}),
            'next_flip':rate(rows,'next_flip'),'flip_within_3':rate(rows,'flip_within_3'),
            'peak_already':rate(rows,'peak_already'),
            'remain_med':med([r['remaining_favorable_ranges'] for r in rows]),
            'giveback_med':med([r['giveback_ranges'] for r in rows])}

def rankmap(rows,key,n=5):
    z=sorted([r for r in rows if r.get(key) is not None and math.isfinite(r[key])],key=lambda r:r[key])
    return {id(r):min(n-1,i*n//len(z)) for i,r in enumerate(z)}

def qs(rows,key,n=5):
    m=rankmap(rows,key,n)
    return {str(q+1):summ([r for r in rows if m.get(id(r))==q]) for q in range(n)}

def cat(rows,key):
    return {str(v):summ([r for r in rows if r[key]==v]) for v in sorted({r[key] for r in rows},key=str)}

def hastoc_bins(rows,n=3): return rankmap(rows,'journey_hastoc10',n)

def overlap_binary(rows, field, extras=(), bin_count=3, min_each=10, include_hastoc=False):
    body=rankmap(rows,'h4_body_ratio',bin_count); rawc=rankmap(rows,'h4_raw_close_normalized',bin_count)
    hb=hastoc_bins(rows,3) if include_hastoc else None
    cells=defaultdict(list)
    for r in rows:
        if id(r) not in body or id(r) not in rawc: continue
        key=(body[id(r)],rawc[id(r)],*(r[e] for e in extras))
        if include_hastoc: key=(*key,hb.get(id(r)))
        cells[key].append(r)
    elig=[]
    for cell in cells.values():
        yes=[r for r in cell if r[field] is True]; no=[r for r in cell if r[field] is False]
        if len(yes)>=min_each and len(no)>=min_each: elig.append((yes,no,min(len(yes),len(no))))
    w=sum(x[2] for x in elig)
    out={'cells':len(elig),'rows':sum(len(a)+len(b) for a,b,_ in elig),'total':len(rows),
         'min_each':min_each,'extras':list(extras),'include_hastoc_tertile':include_hastoc}
    for target in ('next_flip','flip_within_3','peak_already'):
        # opposed/false minus aligned/true: positive means non-alignment is more transition-like
        out['false_minus_true_'+target]=(sum(ww*(rate(no,target)-rate(yes,target)) for yes,no,ww in elig)/w if w else None)
    return out

def add_ema(h4,decisions):
    closes=[b.close for b in h4]
    e=ema_series(closes,50,'sma'); ef=ema_series(closes,50,'first')
    eval_idx=[r['idx_h4'] for r in decisions]
    diffs=[abs(e[i]-ef[i]) for i in eval_idx if e[i] is not None]
    seed={'max_abs_difference_eval':max(diffs),'median_abs_difference_eval':statistics.median(diffs)}
    for r in decisions:
        i=r['idx_h4']; cur=e[i]; prev=e[i-1]
        assert cur is not None and prev is not None
        ha_close=(r['raw_open']+r['raw_high']+r['raw_low']+r['raw_close'])/4.0
        slope=(cur-prev)/prev
        pos=(ha_close-cur)/cur
        js=r['side']*slope; jp=r['side']*pos
        eps=1e-15
        r['ema50']=cur; r['ema50_prev']=prev
        r['journey_ema50_slope_pct']=js
        r['journey_ha_close_to_ema50_pct']=jp
        r['ema50_slope_aligned']=True if js>eps else False if js<-eps else None
        r['ema50_position_aligned']=True if jp>eps else False if jp<-eps else None
        if r['ema50_slope_aligned'] is None or r['ema50_position_aligned'] is None: ctx='neutral'
        elif r['ema50_slope_aligned'] and r['ema50_position_aligned']: ctx='both_aligned'
        elif r['ema50_slope_aligned']: ctx='slope_only'
        elif r['ema50_position_aligned']: ctx='position_only'
        else: ctx='neither'
        r['ema50_context']=ctx
    return seed

def analyze(h4,decisions,labels):
    seed=add_ema(h4,decisions)
    dm={r['signal']:r for r in decisions}; rows=[{**dm[l['signal']],**l} for l in labels]
    assert len(rows)==4105
    # Upstream parity.
    pc={k:sum(r['h1_path_state']==k for r in rows) for k in sorted({r['h1_path_state'] for r in rows})}
    assert pc['no_opposition']==1637 and pc['repaired']==1073
    assert pc['persistent_opposition']+pc['unrepaired_mixed']==1395
    opp=[r for r in rows if r['h1_opposed']]; assert len(opp)==1395
    hf=[r for r in opp if r['progress_rejection_or_return']]; assert len(hf)==235 and sum(r['next_flip'] for r in hf)==138

    out={'all':summ(rows),'seed_sensitivity':seed,'context':cat(rows,'ema50_context'),
         'slope_aligned':cat(rows,'ema50_slope_aligned'),'position_aligned':cat(rows,'ema50_position_aligned'),
         'slope_quintiles':qs(rows,'journey_ema50_slope_pct'),
         'position_quintiles':qs(rows,'journey_ha_close_to_ema50_pct')}

    for f in ('ema50_slope_aligned','ema50_position_aligned'):
        out[f+'_overlap_h4']=overlap_binary(rows,f)
        out[f+'_overlap_h4_delta_wick']=overlap_binary(rows,f,('h4_delta_contract','h4_wick_present'))
        out[f+'_overlap_plus_h1']=overlap_binary(rows,f,('h4_delta_contract','h4_wick_present','h1_path_state'),min_each=5)
        out[f+'_overlap_plus_h1_ha5']=overlap_binary(rows,f,('h4_delta_contract','h4_wick_present','h1_path_state','progress_rejection_or_return'),min_each=5)
        out[f+'_overlap_plus_prior_all']=overlap_binary(rows,f,('h4_delta_contract','h4_wick_present','h1_path_state','progress_rejection_or_return'),min_each=5,include_hastoc=True)

    out['h1_opposed']={'all':summ(opp),'context':cat(opp,'ema50_context'),
                       'slope_aligned':cat(opp,'ema50_slope_aligned'),
                       'position_aligned':cat(opp,'ema50_position_aligned'),
                       'slope_quintiles':qs(opp,'journey_ema50_slope_pct'),
                       'position_quintiles':qs(opp,'journey_ha_close_to_ema50_pct')}
    # Within H1-opposed, test EMA context after H4 morphology and HA5, with HASTOC context last.
    for f in ('ema50_slope_aligned','ema50_position_aligned'):
        out['h1_opposed'][f+'_overlap_h4_ha5']=overlap_binary(opp,f,('h4_delta_contract','h4_wick_present','progress_rejection_or_return'),min_each=5)
        out['h1_opposed'][f+'_overlap_prior_all']=overlap_binary(opp,f,('h4_delta_contract','h4_wick_present','progress_rejection_or_return'),min_each=5,include_hastoc=True)

    out['year_side']={}
    for y in (2024,2025,2026):
        for s in (1,-1):
            z=[r for r in rows if r['year']==y and r['side']==s]
            out['year_side'][f'{y}_{"L" if s==1 else "S"}']={'slope':cat(z,'ema50_slope_aligned'),'position':cat(z,'ema50_position_aligned'),'context':cat(z,'ema50_context')}
    out['birth_continuation']={}
    for birth in (True,False):
        z=[r for r in rows if (r['journey_bar']==1)==birth]
        out['birth_continuation']['birth' if birth else 'continuation']={'all':summ(z),'context':cat(z,'ema50_context')}

    tails=[r for r in rows if r['journey_closed_bars']>=10]
    assert len({r['journey'] for r in tails})==88
    out['long_tail']={'journeys':88,'decisions':len(tails)}
    for f in ('ema50_slope_aligned','ema50_position_aligned'):
        warn=[r for r in tails if r[f] is False]
        out['long_tail'][f+'_opposed']={'journeys_with_warning':len({r['journey'] for r in warn}),
          'warnings':len(warn),'not_next_flip':sum(not r['next_flip'] for r in warn),'next_flip':sum(r['next_flip'] for r in warn),
          'remaining_favorable_median':med([r['remaining_favorable_ranges'] for r in warn])}
    bad=[r for r in tails if r['ema50_context']=='neither']
    out['long_tail']['neither']={'journeys_with_warning':len({r['journey'] for r in bad}),'warnings':len(bad),
      'not_next_flip':sum(not r['next_flip'] for r in bad),'next_flip':sum(r['next_flip'] for r in bad),
      'remaining_favorable_median':med([r['remaining_favorable_ranges'] for r in bad])}
    return out,rows

if __name__=='__main__':
    h4,d,l=ha6a.build(); out,rows=analyze(h4,d,l)
    OUT.mkdir(exist_ok=True)
    (OUT/'summary.json').write_text(json.dumps(out,indent=2,default=str),encoding='utf-8')
    print(json.dumps(out,indent=2,default=str))
