from __future__ import annotations
import importlib.util, sys, json, math, statistics, hashlib
from pathlib import Path
from collections import defaultdict

ROOT=Path('/mnt/data')
OUT=ROOT/'v13_ha6c'
H4_PATH=ROOT/'GOLD#_H4_202201030000_202608282000.csv'
HA6A=ROOT/'v13_ha6a/ha6a_hastoc_audit.py'
HA6B1=ROOT/'v13_ha6b/ha6b1_ema50_context_audit.py'

# Load frozen previous-stage reproductions.
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
ha6a=load_module('ha6a_for_ha6c',HA6A)
ha6b1=load_module('ha6b1_for_ha6c',HA6B1)


def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def med(vals):
    z=[v for v in vals if v is not None and math.isfinite(v)]
    return statistics.median(z) if z else None

def mean(vals):
    z=[v for v in vals if v is not None and math.isfinite(v)]
    return statistics.mean(z) if z else None

def rate(rows,key): return sum(bool(r[key]) for r in rows)/len(rows) if rows else None

def summary(rows):
    return {'n':len(rows),'journeys':len({r['journey'] for r in rows}),
            'next_flip':rate(rows,'next_flip'),'flip_within_3':rate(rows,'flip_within_3'),
            'peak_already':rate(rows,'peak_already'),
            'remain_range_med':med([r['remaining_favorable_ranges'] for r in rows]),
            'giveback_range_med':med([r['giveback_ranges'] for r in rows]),
            'remain_atr_med':med([r['remaining_favorable_atr14'] for r in rows]),
            'giveback_atr_med':med([r['giveback_atr14'] for r in rows])}

def rankmap(rows,key,n=5):
    z=sorted([r for r in rows if r.get(key) is not None and math.isfinite(r[key])],key=lambda r:r[key])
    return {id(r):min(n-1,i*n//len(z)) for i,r in enumerate(z)}

def quantile_outcomes(rows,key,n=5):
    q=rankmap(rows,key,n)
    return {str(i+1):summary([r for r in rows if q.get(id(r))==i]) for i in range(n)}

def fixed_cutpoints(rows,key,n=5):
    vals=sorted(r[key] for r in rows if r.get(key) is not None and math.isfinite(r[key]))
    # nearest-rank boundaries between equal-count bins, deterministic.
    return [vals[(i*len(vals))//n] for i in range(1,n)]

def apply_cutpoints(rows,key,cuts):
    out={str(i+1):[] for i in range(len(cuts)+1)}
    for r in rows:
        v=r.get(key)
        if v is None or not math.isfinite(v): continue
        b=0
        while b<len(cuts) and v>=cuts[b]: b+=1
        out[str(b+1)].append(r)
    return {k:summary(v) for k,v in out.items()}

def year_side_fixed(rows,key,cuts):
    out={}
    for y in (2024,2025,2026):
        for side in (1,-1):
            z=[r for r in rows if r['year']==y and r['side']==side]
            out[f'{y}_{"LONG" if side==1 else "SHORT"}']=apply_cutpoints(z,key,cuts)
    return out

def tr_series(h4):
    out=[None]*len(h4)
    for i,b in enumerate(h4):
        if i==0: out[i]=b.high-b.low
        else: out[i]=max(b.high,h4[i-1].close)-min(b.low,h4[i-1].close)
    return out

def rolling_mean(vals,n=14):
    out=[None]*len(vals); s=0.0
    for i,v in enumerate(vals):
        s+=v
        if i>=n: s-=vals[i-n]
        if i>=n-1: out[i]=s/n
    return out

def add_ema20(h4,decisions):
    # Same frozen HA-6B2 semantics: SMA-seeded EMA20 on raw highs/lows.
    def ema(vals,p):
        a=2/(p+1); out=[None]*len(vals); e=sum(vals[:p])/p; out[p-1]=e
        for i in range(p,len(vals)):
            e=a*vals[i]+(1-a)*e; out[i]=e
        return out
    eh=ema([b.high for b in h4],20); el=ema([b.low for b in h4],20)
    for r in decisions:
        i=r['idx_h4']; hc=(r['raw_open']+r['raw_high']+r['raw_low']+r['raw_close'])/4.0
        bound=eh[i] if r['side']==1 else el[i]
        r['ema20_directional_boundary']=bound
        r['journey_ha_close_to_ema20_boundary_pct']=r['side']*(hc-bound)/bound
        r['ema20_beyond_directional_boundary']=r['journey_ha_close_to_ema20_boundary_pct']>0


def build_rows():
    h4,decisions,labels=ha6a.build()
    # Add HA6B frozen EMA50 and EMA20 context.
    ha6b1.add_ema(h4,decisions); add_ema20(h4,decisions)
    tr=tr_series(h4); atr=rolling_mean(tr,14)
    # For raw feature reconstruction we need standard HA OHLC/opposite wick at each H4 source index.
    hs=ha6a.HA(); haf=[]
    for b in h4: haf.append(hs.update(b))

    dm={r['signal']:r for r in decisions}
    lm={r['signal']:r for r in labels}
    rows=[]; features=[]; future=[]
    for r in decisions:
        i=r['idx_h4']; a=atr[i]
        assert a is not None and a>0
        f=haf[i]; side=r['side']; hc=f['ha_close']; raw_range=r['raw_high']-r['raw_low']
        # decision feature fields only
        feat=dict(r)
        feat.update({
          'atr14':a,'atr14_lag1':atr[i-1],
          'atr14_pct_close':a/r['raw_close'],
          'h4_abs_delta_price':f['abs_delta'],
          'h4_abs_delta_atr14':f['abs_delta']/a,
          'h4_opposite_wick_price':f['opposite_wick'],
          'h4_opposite_wick_atr14':f['opposite_wick']/a,
          'raw_h4_range_price':raw_range,
          'raw_h4_range_atr14':raw_range/a,
          'journey_raw_close_minus_ha_close_price':side*(r['raw_close']-hc),
          'journey_raw_close_minus_ha_close_atr14':side*(r['raw_close']-hc)/a,
          'journey_ema50_slope_price':side*(r['ema50']-r['ema50_prev']),
          'journey_ema50_slope_atr14':side*(r['ema50']-r['ema50_prev'])/a,
          'journey_ha_close_to_ema50_price':side*(hc-r['ema50']),
          'journey_ha_close_to_ema50_atr14':side*(hc-r['ema50'])/a,
          'journey_ha_close_to_ema20_boundary_price':side*(hc-r['ema20_directional_boundary']),
          'journey_ha_close_to_ema20_boundary_atr14':side*(hc-r['ema20_directional_boundary'])/a,
        })
        features.append(feat)
        lab=lm.get(r['signal'])
        if lab is None: continue
        # Reconstruct raw favorable/giveback numerators from the already-fixed Journey and exits.
        ids=[j for j,x in enumerate(decisions) if x['journey']==r['journey']]
        end=ids[-1]; stop=end+1
        assert stop < len(decisions)
        pos=decisions.index(r)
        fut=decisions[pos+1:stop+1]
        extreme=max(x['raw_high'] for x in fut) if side==1 else min(x['raw_low'] for x in fut)
        favorable=max(0.0,side*(extreme-r['execution_raw_open']))
        giveback=side*(extreme-decisions[stop]['execution_raw_open'])
        lab2=dict(lab)
        lab2.update({'remaining_favorable_price':favorable,'giveback_price':giveback,
                     'remaining_favorable_atr14':favorable/a,'giveback_atr14':giveback/a})
        future.append(lab2)
        rows.append({**feat,**lab2})
    assert len(features)==4108 and len(rows)==len(future)==4105
    # Frozen parity checks from prior receipts.
    assert len({r['journey'] for r in features})==966
    assert sum(min(10,sum(x['journey']==j for x in features)) for j in range(1,966))==3858
    assert sum(r['h1_opposed'] for r in rows)==1395
    flag=[r for r in rows if r['h1_opposed'] and r['progress_rejection_or_return']]
    assert len(flag)==235 and sum(r['next_flip'] for r in flag)==138
    return h4,features,future,rows


def year_medians(rows,keys):
    out={}
    for y in (2024,2025,2026):
        z=[r for r in rows if r['year']==y]
        out[str(y)]={k:med([r[k] for r in z]) for k in keys}
    return out

def max_min_ratio(year_dict,key,absolute=False):
    vals=[]
    for y,v in year_dict.items():
        x=v[key]
        if x is None: continue
        vals.append(abs(x) if absolute else x)
    vals=[x for x in vals if x>0]
    return max(vals)/min(vals) if vals else None

def side_year_outcomes(rows):
    out={}
    for y in (2024,2025,2026):
      for side in (1,-1):
        z=[r for r in rows if r['year']==y and r['side']==side]
        out[f'{y}_{"LONG" if side==1 else "SHORT"}']={
          'n':len(z),
          'remaining_price_med':med([r['remaining_favorable_price'] for r in z]),
          'remaining_range_med':med([r['remaining_favorable_ranges'] for r in z]),
          'remaining_atr_med':med([r['remaining_favorable_atr14'] for r in z]),
          'giveback_price_med':med([r['giveback_price'] for r in z]),
          'giveback_range_med':med([r['giveback_ranges'] for r in z]),
          'giveback_atr_med':med([r['giveback_atr14'] for r in z]),
        }
    return out

def gradient_spread(block):
    vals=[]
    for cell in block.values():
        q1=cell.get('1',{}).get('next_flip'); q5=cell.get('5',{}).get('next_flip')
        if q1 is not None and q5 is not None: vals.append(q1-q5)
    return {'values':vals,'mean':mean(vals),'min':min(vals) if vals else None,'max':max(vals) if vals else None,
            'range':max(vals)-min(vals) if vals else None}

def analyze(rows):
    primary_pairs={
      'ha_delta':('h4_abs_delta_price','h4_abs_delta_atr14'),
      'opposite_wick':('h4_opposite_wick_price','h4_opposite_wick_atr14'),
      'raw_close_minus_ha':('journey_raw_close_minus_ha_close_price','journey_raw_close_minus_ha_close_atr14'),
      'ema50_distance':('journey_ha_close_to_ema50_price','journey_ha_close_to_ema50_atr14'),
      'ema50_slope':('journey_ema50_slope_price','journey_ema50_slope_atr14'),
      'ema20_distance':('journey_ha_close_to_ema20_boundary_price','journey_ha_close_to_ema20_boundary_atr14'),
    }
    keys=[k for p in primary_pairs.values() for k in p]
    ym=year_medians(rows,keys+['atr14','atr14_pct_close','raw_h4_range_price','raw_h4_range_atr14'])
    out={'all':summary(rows),'year_medians':ym,'scale_drift':{},'features':{}}
    for name,(rawk,normk) in primary_pairs.items():
        # magnitude drift uses absolute per-year medians for signed measures.
        raw_abs={y:med([abs(r[rawk]) for r in rows if r['year']==int(y)]) for y in ('2024','2025','2026')}
        norm_abs={y:med([abs(r[normk]) for r in rows if r['year']==int(y)]) for y in ('2024','2025','2026')}
        rr=max(raw_abs.values())/min(raw_abs.values()) if min(raw_abs.values())>0 else None
        nr=max(norm_abs.values())/min(norm_abs.values()) if min(norm_abs.values())>0 else None
        raw_cuts=fixed_cutpoints(rows,rawk); norm_cuts=fixed_cutpoints(rows,normk)
        raw_ys=year_side_fixed(rows,rawk,raw_cuts); norm_ys=year_side_fixed(rows,normk,norm_cuts)
        out['scale_drift'][name]={'raw_abs_median_by_year':raw_abs,'atr_abs_median_by_year':norm_abs,
                                  'raw_max_min_ratio':rr,'atr_max_min_ratio':nr,
                                  'ratio_reduction':(rr-nr) if rr is not None and nr is not None else None}
        out['features'][name]={
          'raw_full_quintiles':quantile_outcomes(rows,rawk),
          'atr_full_quintiles':quantile_outcomes(rows,normk),
          'raw_fixed_fullwindow_cut_year_side':raw_ys,
          'atr_fixed_fullwindow_cut_year_side':norm_ys,
          'raw_year_side_gradient_spread':gradient_spread(raw_ys),
          'atr_year_side_gradient_spread':gradient_spread(norm_ys),
        }
    out['outcomes_year_side']=side_year_outcomes(rows)
    # Aggregate year-level normalization stability for future label magnitudes.
    outcome_year={}
    for y in (2024,2025,2026):
        z=[r for r in rows if r['year']==y]
        outcome_year[str(y)]={
          'remain_price':med([r['remaining_favorable_price'] for r in z]),
          'remain_range':med([r['remaining_favorable_ranges'] for r in z]),
          'remain_atr':med([r['remaining_favorable_atr14'] for r in z]),
          'giveback_price':med([r['giveback_price'] for r in z]),
          'giveback_range':med([r['giveback_ranges'] for r in z]),
          'giveback_atr':med([r['giveback_atr14'] for r in z]),
        }
    out['outcomes_by_year']=outcome_year
    # ATR regime diagnostics only: no action interpretation.
    out['atr14_quintiles_diagnostic']=quantile_outcomes(rows,'atr14')
    out['atr14_pct_close_quintiles_diagnostic']=quantile_outcomes(rows,'atr14_pct_close')
    # Tail remains explicit.
    tails=[r for r in rows if r['journey_closed_bars']>=10]
    assert len({r['journey'] for r in tails})==88
    out['long_journeys']={'journeys':88,'decisions':len(tails),
      'remaining_atr_median':med([r['remaining_favorable_atr14'] for r in tails]),
      'remaining_range_median':med([r['remaining_favorable_ranges'] for r in tails]),
      'giveback_atr_median':med([r['giveback_atr14'] for r in tails]),
      'giveback_range_median':med([r['giveback_ranges'] for r in tails])}
    # Lagged denominator sensitivity on raw dimensions (same numerator).
    sens=[]
    for r in rows:
        lag=r['atr14_lag1']
        if lag is None: continue
        sens.append((r['h4_abs_delta_price']/r['atr14'],r['h4_abs_delta_price']/lag,
                     r['raw_h4_range_price']/r['atr14'],r['raw_h4_range_price']/lag))
    out['lagged_atr_sensitivity']={
      'ha_delta_median_abs_difference':med([abs(a-b) for a,b,_,_ in sens]),
      'range_median_abs_difference':med([abs(c-d) for _,_,c,d in sens]),
    }
    return out


def write_csv(path,rows):
    import csv
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

if __name__=='__main__':
    h4,features,future,rows=build_rows(); out=analyze(rows)
    OUT.mkdir(exist_ok=True)
    write_csv(OUT/'decision_features.csv',features)
    write_csv(OUT/'future_labels.csv',future)
    payload={'status':'consumed-development-observation-only',
             'authority_base':'40f97352e47c66cd3b952f74532b1b71969e79fd',
             'sources':{'h4_sha256':sha256(H4_PATH)},'summary':out}
    (OUT/'summary.json').write_text(json.dumps(payload,indent=2,default=str),encoding='utf-8')
    print(json.dumps(out,indent=2,default=str))
