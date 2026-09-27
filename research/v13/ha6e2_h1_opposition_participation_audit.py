from pathlib import Path
import pandas as pd, numpy as np, json, hashlib

H1=Path('/mnt/data/GOLD#_H1_202201030100_202608282300.csv')
BASE_FEATURES=Path('/mnt/data/v13_ha6e/decision_features.csv')
LABELS=Path('/mnt/data/v13_ha6e/future_labels.csv')
OUT=Path('/mnt/data/v13_ha6e')

def rate(s):
    return float(pd.Series(s).astype(float).mean()) if len(s) else None

def med(s):
    x=pd.Series(s).dropna(); return float(x.median()) if len(x) else None

def add_q(df,col,q,name):
    out=pd.Series(pd.NA,index=df.index,dtype='Int64')
    valid=df[col].notna()
    if valid.sum():
        r=df.loc[valid,col].rank(method='first')
        out.loc[valid]=(pd.qcut(r,q,labels=False)+1).astype('int64')
    df[name]=out
    return df

def summarize(g):
    return {
        'n':int(len(g)),
        'next_flip':rate(g.next_flip) if len(g) else None,
        'flip_within_3':rate(g.flip_within_3) if len(g) else None,
        'peak_already':rate(g.peak_already) if len(g) else None,
        'remaining_favorable_ranges_median':med(g.remaining_favorable_ranges),
        'giveback_ranges_median':med(g.giveback_ranges),
        'opposed_h1_activity_median':med(g.opposed_h1_activity),
        'h4_relative_tick_volume_median':med(g.relative_tick_volume20),
    }

# H1 standard HA + same-hour relative tick volume
h1=pd.read_csv(H1,sep='\t')
h1['time']=pd.to_datetime(h1['<DATE>']+' '+h1['<TIME>'])
h1=h1.sort_values('time').reset_index(drop=True)
ha_open=[];ha_close=[];ha_color=[]
prev_o=None;prev_c=None;color=0
for r in h1.itertuples(index=False):
    o=float(getattr(r,'_2')) if False else None
# use explicit arrays because angle-bracket column names are awkward
for i,row in h1.iterrows():
    o,h,l,c=[float(row[k]) for k in ['<OPEN>','<HIGH>','<LOW>','<CLOSE>']]
    hc=(o+h+l+c)/4.0
    ho=(o+c)/2.0 if prev_o is None else (prev_o+prev_c)/2.0
    if hc>ho: color=1
    elif hc<ho: color=-1
    ha_open.append(ho);ha_close.append(hc);ha_color.append(color)
    prev_o,prev_c=ho,hc
h1['ha_open']=ha_open;h1['ha_close']=ha_close;h1['ha_color']=ha_color
h1['hour']=h1.time.dt.hour
h1['same_hour_median20']=h1.groupby('hour')['<TICKVOL>'].transform(lambda s:s.shift(1).rolling(20,min_periods=20).median())
h1['h1_relative_tick_volume20']=h1['<TICKVOL>']/h1['same_hour_median20']
h1_by_time=h1.set_index('time')

f=pd.read_csv(BASE_FEATURES)
f['signal']=pd.to_datetime(f.signal)
# Map existing bools if strings
for c in ['h1_opposed','progress_rejection_or_return','h4_delta_contract','h4_wick_present','ema50_slope_aligned','ema20_beyond_directional_boundary','di_aligned','adx_rising']:
    if c in f and f[c].dtype==object:
        f[c]=f[c].map({'True':True,'False':False,True:True,False:False})

records=[]; mismatches=[]
for r in f.itertuples(index=False):
    start=r.signal; end=start+pd.Timedelta(hours=4); side=int(r.side)
    inside=h1[(h1.time>=start)&(h1.time<end)]
    opp=(inside.ha_color.to_numpy()!=side)
    path=''.join('1' if x else '0' for x in opp)
    if len(opp)==0:
        state='missing'
        trailing=0
    else:
        trailing=0
        for x in opp[::-1]:
            if not x: break
            trailing+=1
        state=('no_opposition' if not opp.any() else 'repaired' if not opp[-1] else 'persistent_opposition' if opp.all() else 'unrepaired_mixed')
    if state!=r.h1_path_state:
        mismatches.append((start,state,r.h1_path_state,path,len(inside)))
    rel=inside.h1_relative_tick_volume20.to_numpy(dtype=float)
    opposed_vals=rel[opp] if len(rel) else np.array([])
    aligned_vals=rel[~opp] if len(rel) else np.array([])
    trail_vals=rel[-trailing:] if trailing>0 else np.array([])
    records.append({
        'signal':start,'journey':int(r.journey),'h1_rebuilt_path':path,'h1_bars_rebuilt':int(len(inside)),
        'h1_path_state_rebuilt':state,'h1_trailing_opposed_rebuilt':int(trailing),
        'h1_total_activity_mean':float(np.nanmean(rel)) if len(rel) else np.nan,
        'opposed_h1_activity':float(np.nanmean(opposed_vals)) if len(opposed_vals) else np.nan,
        'aligned_h1_activity':float(np.nanmean(aligned_vals)) if len(aligned_vals) else np.nan,
        'trailing_opposed_activity':float(np.nanmean(trail_vals)) if len(trail_vals) else np.nan,
        'opposed_h1_bars':int(opp.sum()) if len(opp) else 0,
    })
assert not mismatches, mismatches[:10]
rfeat=pd.DataFrame(records)
assert len(rfeat)==4108
f2=f.merge(rfeat,on=['signal','journey'],how='left',validate='one_to_one')
labels=pd.read_csv(LABELS); labels['signal']=pd.to_datetime(labels.signal)
d=f2.merge(labels,on=['signal','journey'],how='inner',validate='one_to_one')
assert len(d)==4105
for c in ['next_flip','flip_within_3','peak_already']:
    if d[c].dtype==object: d[c]=d[c].map({'True':True,'False':False,True:True,False:False})

# q within each predeclared path population, not global, because activity distribution differs by path composition
out={'status':'consumed-development-observation-only','parity':{
    'h1_path_mismatches':0,'decisions_checked':4108,
    'h1_bars_per_h4_counts':{str(int(k)):int(v) for k,v in rfeat.h1_bars_rebuilt.value_counts().sort_index().items()},
    'opposed_feature_coverage':int(d.opposed_h1_activity.notna().sum())
},'paths':{},'all_opposed':{}}

op=d[d.opposed_h1_activity.notna()].copy()
op=add_q(op,'opposed_h1_activity',5,'oppact_q')
out['all_opposed']['all']=summarize(op)
out['all_opposed']['quintiles']={str(int(q)):summarize(g) for q,g in op.groupby('oppact_q')}
out['all_opposed']['spearman_vs_h4_relative_tick_volume']=float(op[['opposed_h1_activity','relative_tick_volume20']].corr(method='spearman').iloc[0,1])

for state in ['repaired','unrepaired_mixed','persistent_opposition']:
    g=d[d.h1_path_state==state].copy()
    g=add_q(g,'opposed_h1_activity',5,'oppact_q')
    out['paths'][state]={
        'all':summarize(g),
        'quintiles':{str(int(q)):summarize(x) for q,x in g.groupby('oppact_q')},
        'year_side':{}
    }
    for (y,s),x in g.groupby(['year','side']):
        q1=x[x.oppact_q==1];q5=x[x.oppact_q==5]
        out['paths'][state]['year_side'][f"{y}_{'LONG' if s==1 else 'SHORT'}"]={
            'n':int(len(x)),'q1_n':int(len(q1)),'q5_n':int(len(q5)),
            'q1_next_flip':rate(q1.next_flip) if len(q1) else None,
            'q5_next_flip':rate(q5.next_flip) if len(q5) else None,
            'q5_minus_q1_next_flip':(rate(q5.next_flip)-rate(q1.next_flip)) if len(q1) and len(q5) else None
        }

# persistent opposition: morphology overlap with within-subset tertiles
p=d[d.h1_path_state=='persistent_opposition'].copy()
p=add_q(p,'opposed_h1_activity',5,'oppact_q')
for col,name in [('h4_body_ratio','body_t'),('h4_abs_delta_atr14','delta_t'),('journey_hastoc10','hastoc_t')]:
    p=add_q(p,col,3,name)
out['persistent_overlap']={}
for grouping in [['body_t'],['delta_t'],['body_t','delta_t'],['body_t','delta_t','progress_rejection_or_return']]:
    label='+'.join(grouping); cells=[]
    for keys,x in p[p.oppact_q.isin([1,5])].groupby(grouping,dropna=False):
        a=x[x.oppact_q==1];b=x[x.oppact_q==5]
        if len(a)>=3 and len(b)>=3:
            w=min(len(a),len(b)); cells.append((w,len(a),len(b),rate(b.next_flip)-rate(a.next_flip),rate(b.flip_within_3)-rate(a.flip_within_3)))
    W=sum(z[0] for z in cells)
    out['persistent_overlap'][label]={
        'cells':len(cells),'comparable_rows':int(sum(z[1]+z[2] for z in cells)),
        'weighted_q5_minus_q1_next_flip':float(sum(z[0]*z[3] for z in cells)/W) if W else None,
        'weighted_q5_minus_q1_flip3':float(sum(z[0]*z[4] for z in cells)/W) if W else None,
    }

# Long journeys in each path; report both extremes, no warning selection
out['long_journeys']={}
for state in ['repaired','unrepaired_mixed','persistent_opposition']:
    g=d[(d.h1_path_state==state)&(d.journey_closed_bars>=10)].copy()
    if len(g): g=add_q(g,'opposed_h1_activity',5,'local_q')
    stateout={'decisions':int(len(g)),'journeys':int(g.journey.nunique())}
    for q in [1,5]:
        x=g[g.local_q==q] if len(g) else g
        stateout[f'q{q}']={'n':int(len(x)),'journeys':int(x.journey.nunique()),'next_flip':rate(x.next_flip) if len(x) else None,
                           'not_next_flip':int((~x.next_flip.astype(bool)).sum()) if len(x) else 0,
                           'remaining_favorable_ranges_median':med(x.remaining_favorable_ranges)}
    out['long_journeys'][state]=stateout

# save ledgers separately
f2.to_csv(OUT/'decision_features_h1_participation.csv',index=False)
labels.to_csv(OUT/'future_labels_h1_participation.csv',index=False)
with open(OUT/'summary_h1_participation.json','w') as fp: json.dump(out,fp,indent=2)
print(json.dumps(out,indent=2))
