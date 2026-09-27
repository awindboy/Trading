from pathlib import Path
import pandas as pd, numpy as np, json, math, hashlib

H4=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv')
M1=Path('/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv')
FEATURES=Path('/mnt/data/v13_ha6d1/decision_features.csv')
LABELS=Path('/mnt/data/v13_ha6d1/future_labels.csv')
OUT=Path('/mnt/data/v13_ha6e')
OUT.mkdir(exist_ok=True)

START=pd.Timestamp('2024-01-01 00:00:00')
END=pd.Timestamp('2026-08-28 20:00:00')

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def rate(s):
    return float(np.mean(s.astype(float))) if len(s) else None

def med(s):
    x=pd.Series(s).dropna()
    return float(x.median()) if len(x) else None

def summary(g):
    return {
        'n':int(len(g)),
        'next_flip':rate(g.next_flip) if len(g) else None,
        'flip_within_3':rate(g.flip_within_3) if len(g) else None,
        'peak_already':rate(g.peak_already) if len(g) else None,
        'remaining_favorable_ranges_median':med(g.remaining_favorable_ranges),
        'giveback_ranges_median':med(g.giveback_ranges),
        'relative_tick_volume20_median':med(g.relative_tick_volume20),
    }

def add_quantile_bins(df, col, q, prefix):
    # deterministic rank-based equal-count display bins; ties broken by row order only for display.
    valid=df[col].notna()
    ranks=df.loc[valid,col].rank(method='first')
    bins=pd.qcut(ranks,q,labels=False)+1
    out=pd.Series(pd.NA,index=df.index,dtype='Int64')
    out.loc[valid]=bins.astype('int64')
    df[prefix]=out
    return df

def overlap_tail_contrast(df, group_cols, min_each=8):
    # Q1-vs-Q5 only, within exact categorical cells; weighted by min(n1,n5).
    d=df[df['vol_q'].isin([1,5])].copy()
    cells=[]
    for keys,g in d.groupby(group_cols,dropna=False):
        a=g[g.vol_q==1]; b=g[g.vol_q==5]
        if len(a)>=min_each and len(b)>=min_each:
            w=min(len(a),len(b))
            cells.append((w, rate(a.next_flip)-rate(b.next_flip), rate(a.flip_within_3)-rate(b.flip_within_3), len(a),len(b)))
    if not cells:
        return {'cells':0,'comparable_rows':0,'q1_rows':0,'q5_rows':0,'weighted_next_flip_diff_q1_minus_q5':None,'weighted_flip3_diff_q1_minus_q5':None}
    W=sum(x[0] for x in cells)
    return {
        'cells':len(cells),
        'comparable_rows':int(sum(x[3]+x[4] for x in cells)),
        'q1_rows':int(sum(x[3] for x in cells)),
        'q5_rows':int(sum(x[4] for x in cells)),
        'weighted_next_flip_diff_q1_minus_q5':float(sum(x[0]*x[1] for x in cells)/W),
        'weighted_flip3_diff_q1_minus_q5':float(sum(x[0]*x[2] for x in cells)/W),
    }

# H4 history + feature construction
h4=pd.read_csv(H4,sep='\t')
h4['signal']=pd.to_datetime(h4['<DATE>']+' '+h4['<TIME>'])
h4=h4.sort_values('signal').reset_index(drop=True)
h4['slot']=h4.signal.dt.hour
h4['year']=h4.signal.dt.year
h4['same_slot_median20']=h4.groupby('slot')['<TICKVOL>'].transform(lambda s:s.shift(1).rolling(20,min_periods=20).median())
h4['relative_tick_volume20']=h4['<TICKVOL>']/h4['same_slot_median20']
h4['log_relative_tick_volume20']=np.log(h4['relative_tick_volume20'])

# M1->H4 exact tick-volume aggregation quality check
parts=[]
for ch in pd.read_csv(M1,sep='\t',chunksize=300000):
    dt=pd.to_datetime(ch['<DATE>']+' '+ch['<TIME>'])
    bucket=dt.dt.floor('4h')
    t=pd.DataFrame({'bucket':bucket,'tv':ch['<TICKVOL>'].astype('int64'),'vol':ch['<VOL>'].astype('int64')})
    parts.append(t.groupby('bucket').agg(m1_tickvol=('tv','sum'),m1_rows=('tv','size'),m1_realvol=('vol','sum')))
m1agg=pd.concat(parts).groupby(level=0).sum()
parity=h4.set_index('signal').join(m1agg,how='left')
parity['tickvol_diff']=parity['<TICKVOL>']-parity['m1_tickvol']

features=pd.read_csv(FEATURES)
labels=pd.read_csv(LABELS)
features['signal']=pd.to_datetime(features.signal)
labels['signal']=pd.to_datetime(labels.signal)
vol=h4[['signal','<TICKVOL>','<VOL>','<SPREAD>','slot','same_slot_median20','relative_tick_volume20','log_relative_tick_volume20']]
f=features.merge(vol,on='signal',how='left',validate='one_to_one')
assert len(f)==4108 and f.relative_tick_volume20.notna().all()
joined=f.merge(labels,on=['signal','journey'],how='inner',validate='one_to_one',suffixes=('','_label'))
assert len(joined)==4105
# safe booleans after CSV read
for c in ['next_flip','flip_within_3','peak_already','h4_delta_contract','h4_wick_present','h1_opposed','progress_rejection_or_return','ema50_slope_aligned','ema20_beyond_directional_boundary','di_aligned','adx_rising']:
    if joined[c].dtype==object:
        joined[c]=joined[c].map({'True':True,'False':False,True:True,False:False})

# Display quantiles
joined=add_quantile_bins(joined,'relative_tick_volume20',5,'vol_q')
# controls with global rank bins
for c,n,p in [('h4_body_ratio',3,'body_t'),('h4_abs_delta_atr14',3,'delta_t'),('journey_hastoc10',3,'hastoc_t'),('adx14_wilder',3,'adx_t')]:
    joined=add_quantile_bins(joined,c,n,p)

# Data quality and normalized stability
canon=h4[(h4.signal>=START)&(h4.signal<=END)].copy()
quality={
    'source_sha256':{'h4':digest(H4),'m1':digest(M1),'features':digest(FEATURES),'labels':digest(LABELS)},
    'h4_rows':int(len(h4)),
    'h4_timestamp_duplicates':int(h4.signal.duplicated().sum()),
    'h4_tickvol_zero_rows':int((h4['<TICKVOL>']==0).sum()),
    'h4_realvol_nonzero_rows':int((h4['<VOL>']!=0).sum()),
    'm1_h4_tickvol_exact_rows':int((parity.tickvol_diff==0).sum()),
    'm1_h4_rows_compared':int(parity.m1_tickvol.notna().sum()),
    'm1_realvol_nonzero_aggregates':int((parity.m1_realvol.fillna(0)!=0).sum()),
    'year_raw_tickvol_median':{str(k):float(v) for k,v in canon.groupby(canon.signal.dt.year)['<TICKVOL>'].median().items()},
    'year_relative_tickvol_median':{str(k):float(v) for k,v in canon.groupby(canon.signal.dt.year)['relative_tick_volume20'].median().items()},
    'slot_raw_tickvol_median':{str(k):float(v) for k,v in canon.groupby('slot')['<TICKVOL>'].median().items()},
    'slot_relative_tickvol_median':{str(k):float(v) for k,v in canon.groupby('slot')['relative_tick_volume20'].median().items()},
    'raw_year_median_max_min_ratio':float(canon.groupby(canon.signal.dt.year)['<TICKVOL>'].median().max()/canon.groupby(canon.signal.dt.year)['<TICKVOL>'].median().min()),
    'relative_year_median_max_min_ratio':float(canon.groupby(canon.signal.dt.year)['relative_tick_volume20'].median().max()/canon.groupby(canon.signal.dt.year)['relative_tick_volume20'].median().min()),
    'raw_slot_median_max_min_ratio':float(canon.groupby('slot')['<TICKVOL>'].median().max()/canon.groupby('slot')['<TICKVOL>'].median().min()),
    'relative_slot_median_max_min_ratio':float(canon.groupby('slot')['relative_tick_volume20'].median().max()/canon.groupby('slot')['relative_tick_volume20'].median().min()),
    'm1_rows_per_h4_quantiles':{str(k):float(v) for k,v in parity.m1_rows.quantile([0,.01,.05,.5,.95,.99,1]).items()},
}

out={'status':'consumed-development-observation-only','quality':quality,'all':summary(joined),'volume_quintiles':{}}
for q,g in joined.groupby('vol_q'):
    out['volume_quintiles'][str(int(q))]=summary(g)

# Year x side stability, global quintiles
ys={}
for (year,side),g in joined.groupby(['year','side']):
    q1=g[g.vol_q==1];q5=g[g.vol_q==5]
    ys[f"{year}_{'LONG' if side==1 else 'SHORT'}"]={
        'n':int(len(g)),'q1_n':int(len(q1)),'q5_n':int(len(q5)),
        'q1_next_flip':rate(q1.next_flip) if len(q1) else None,
        'q5_next_flip':rate(q5.next_flip) if len(q5) else None,
        'q1_minus_q5_next_flip':(rate(q1.next_flip)-rate(q5.next_flip)) if len(q1) and len(q5) else None,
        'q1_flip3':rate(q1.flip_within_3) if len(q1) else None,
        'q5_flip3':rate(q5.flip_within_3) if len(q5) else None,
    }
out['year_side']=ys

# H1 opposed subset
h1=joined[joined.h1_opposed==True]
out['h1_opposed']={'all':summary(h1),'quintiles':{str(int(q)):summary(g) for q,g in h1.groupby('vol_q')}}
# path states
out['h1_path_states']={}
for state,g in joined.groupby('h1_path_state'):
    out['h1_path_states'][str(state)]={'all':summary(g),'q1':summary(g[g.vol_q==1]),'q5':summary(g[g.vol_q==5])}

# progressive overlap controls
control_sets={
    'morphology':['body_t','delta_t','h4_delta_contract','h4_wick_present'],
    'morphology_h1_raw':['body_t','delta_t','h4_delta_contract','h4_wick_present','h1_path_state','progress_rejection_or_return'],
    'plus_hastoc_ma':['body_t','delta_t','h4_delta_contract','h4_wick_present','h1_path_state','progress_rejection_or_return','hastoc_t','ema50_slope_aligned','ema20_beyond_directional_boundary'],
    'plus_adx_dmi':['body_t','delta_t','h4_delta_contract','h4_wick_present','h1_path_state','progress_rejection_or_return','hastoc_t','ema50_slope_aligned','ema20_beyond_directional_boundary','adx_t','di_aligned','adx_rising'],
}
out['overlap_controls']={k:overlap_tail_contrast(joined,v,min_each=5) for k,v in control_sets.items()}
out['h1_opposed_overlap_controls']={k:overlap_tail_contrast(h1,v,min_each=4) for k,v in control_sets.items()}

# correlations to existing continuous price-derived states
corr_cols=['relative_tick_volume20','h4_body_ratio','h4_abs_delta_atr14','journey_raw_close_minus_ha_close_atr14','journey_hastoc10','journey_ema50_slope_atr14','journey_ha_close_to_ema20_boundary_atr14','adx14_wilder','journey_di_margin','atr14']
out['spearman']=joined[corr_cols].corr(method='spearman').loc['relative_tick_volume20'].drop('relative_tick_volume20').to_dict()

# Long journey exposure. Report both low/high participation tails to avoid post-hoc warning direction selection.
tails=joined[joined.journey_closed_bars>=10]
assert tails.journey.nunique()==88
lj={'journeys':88,'decisions':int(len(tails))}
for q in [1,5]:
    g=tails[tails.vol_q==q]
    gh=g[g.h1_opposed==True]
    lj[f'q{q}']={
        'journeys_with_event':int(g.journey.nunique()),'event_decisions':int(len(g)),
        'event_not_next_flip':int((~g.next_flip).sum()),
        'event_next_flip':int(g.next_flip.sum()),
        'remaining_favorable_ranges_median':med(g.remaining_favorable_ranges),
        'h1_opposed_event_decisions':int(len(gh)),
        'h1_opposed_not_next_flip':int((~gh.next_flip).sum()),
        'h1_opposed_remaining_favorable_ranges_median':med(gh.remaining_favorable_ranges),
    }
out['long_journeys']=lj

# Partial/short H4 coverage diagnostics from M1 counts joined to canonical decision signal
rowcov=parity[['m1_rows']].reset_index().rename(columns={'index':'signal'})
joined_cov=joined.merge(rowcov,on='signal',how='left')
out['coverage_sensitivity']={}
for minimum in [1,180,230,239]:
    g=joined_cov[joined_cov.m1_rows>=minimum]
    q1=g[g.vol_q==1];q5=g[g.vol_q==5]
    out['coverage_sensitivity'][f'm1_rows_ge_{minimum}']={
        'n':int(len(g)),'q1_n':int(len(q1)),'q5_n':int(len(q5)),
        'q1_minus_q5_next_flip':(rate(q1.next_flip)-rate(q5.next_flip)) if len(q1) and len(q5) else None,
        'q1_minus_q5_flip3':(rate(q1.flip_within_3)-rate(q5.flip_within_3)) if len(q1) and len(q5) else None,
    }

# write feature ledger (no future labels) and labels separately
feature_cols=list(f.columns)+['vol_q'] if 'vol_q' in f.columns else list(f.columns)
# need vol_q from joined mapping back to feature rows
qmap=joined[['signal','journey','vol_q']]
fout=f.merge(qmap,on=['signal','journey'],how='left')
fout.to_csv(OUT/'decision_features.csv',index=False)
labels.to_csv(OUT/'future_labels.csv',index=False)
with open(OUT/'summary.json','w') as fp: json.dump(out,fp,indent=2)
print(json.dumps({
    'quality':quality,
    'volume_quintiles':out['volume_quintiles'],
    'overlap_controls':out['overlap_controls'],
    'h1_opposed':out['h1_opposed']['quintiles'],
    'long_journeys':out['long_journeys'],
    'spearman':out['spearman']
},indent=2))
