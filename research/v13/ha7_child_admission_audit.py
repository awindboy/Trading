from pathlib import Path
import pandas as pd, numpy as np, json, hashlib

FEATURES=Path('/mnt/data/v13_ha6e/decision_features_h1_participation.csv')
OUT=Path('/mnt/data/v13_ha6e')

def pf(vals):
    vals=np.asarray(vals,dtype=float); gp=vals[vals>0].sum(); gl=-vals[vals<0].sum()
    return float(gp/gl) if gl>0 else None

def max_dd_from_realized(journey_pnl):
    eq=np.r_[0.0,np.cumsum(np.asarray(journey_pnl,dtype=float))]
    peak=np.maximum.accumulate(eq); dd=peak-eq
    return float(dd.max()), int(dd.argmax())

def summ(vals):
    vals=np.asarray(vals,dtype=float)
    return {'n':int(len(vals)),'net':float(vals.sum()),'gross_profit':float(vals[vals>0].sum()),
            'gross_loss':float(vals[vals<0].sum()),'pf':pf(vals),
            'wins':int((vals>0).sum()),'losses':int((vals<0).sum()),'zeros':int((vals==0).sum()),
            'median':float(np.median(vals)) if len(vals) else None}

f=pd.read_csv(FEATURES)
f['signal']=pd.to_datetime(f.signal); f=f.sort_values(['journey','journey_bar']).reset_index(drop=True)
for c in ['h1_opposed']:
    if c in f and f[c].dtype==object:f[c]=f[c].map({'True':True,'False':False,True:True,False:False})
journey_ids=sorted(f.journey.unique())
assert journey_ids[0]==1 and journey_ids[-1]==966
# first execution price of each journey; closes prior journey at same event
first=f.groupby('journey',sort=True).first(numeric_only=False)
closed_ids=journey_ids[:-1]
rows=[]
for jid in closed_ids:
    g=f[f.journey==jid].sort_values('journey_bar')
    exit_price=float(first.loc[jid+1,'execution_raw_open'])
    jlen=len(g)
    side=int(g.side.iloc[0]); assert (g.side==side).all()
    for _,r in g[g.journey_bar<=10].iterrows():
        entry=float(r.execution_raw_open)
        pnl=side*(exit_price-entry)
        trigger=(int(r.journey_bar)>=2 and r.h1_path_state=='persistent_opposition' and float(r.relative_tick_volume20)>1.0)
        rows.append({
            'journey':int(jid),'journey_len':int(jlen),'side':side,'signal':r.signal,'year':int(r.year),
            'journey_bar':int(r.journey_bar),'entry':entry,'exit':exit_price,'baseline_pnl':pnl,
            'veto':bool(trigger),'variant_pnl':0.0 if trigger else pnl,
            'relative_tick_volume20':float(r.relative_tick_volume20),'h1_path_state':r.h1_path_state,
        })
child=pd.DataFrame(rows)
assert len(child)==3858, len(child)
baseline_net=child.baseline_pnl.sum()
# parity tolerance cents-ish on data representation
assert abs(baseline_net-8147.11)<0.02, baseline_net

# Journey aggregates
j=child.groupby('journey').agg(baseline_pnl=('baseline_pnl','sum'),variant_pnl=('variant_pnl','sum'),journey_len=('journey_len','first'),side=('side','first')).reset_index()
base_dd,_=max_dd_from_realized(j.baseline_pnl)
var_dd,_=max_dd_from_realized(j.variant_pnl)

veto=child[child.veto].copy()
report={
 'status':'consumed-development-idealized-structural-action-test-only',
 'baseline_parity':{
  'closed_journeys':int(j.journey.nunique()),'closed_children':int(len(child)),'net_points':float(baseline_net),
  'child_pf':pf(child.baseline_pnl),'journey_pf':pf(j.baseline_pnl),'realized_journey_max_dd_points':base_dd},
 'variant':{
  'admitted_children':int((~child.veto).sum()),'skipped_children':int(child.veto.sum()),
  'net_points':float(child.variant_pnl.sum()),'net_change_points':float(child.variant_pnl.sum()-baseline_net),
  'child_pf':pf(child[~child.veto].baseline_pnl),'journey_pf':pf(j.variant_pnl),
  'realized_journey_max_dd_points':var_dd,'dd_change_points':float(var_dd-base_dd)},
 'skipped':summ(veto.baseline_pnl),
 'skipped_by_year_side':{},'skipped_by_child_slot':{},'skipped_by_journey_len':{},
 'long_journeys':{},'concentration':{}
}
for (y,s),g in veto.groupby(['year','side']):
    report['skipped_by_year_side'][f"{y}_{'LONG' if s==1 else 'SHORT'}"]=summ(g.baseline_pnl)
for b,g in veto.groupby('journey_bar'):
    report['skipped_by_child_slot'][str(int(b))]=summ(g.baseline_pnl)
# grouped lengths compact exact
for l,g in veto.groupby('journey_len'):
    report['skipped_by_journey_len'][str(int(l))]=summ(g.baseline_pnl)
long=child[child.journey_len>=10]
longv=veto[veto.journey_len>=10]
report['long_journeys']={
    'baseline_children':int(len(long)),'baseline_net':float(long.baseline_pnl.sum()),
    'skipped_children':int(len(longv)),'skipped_journeys':int(longv.journey.nunique()),
    'skipped_net':float(longv.baseline_pnl.sum()),
    'variant_long_net':float(long.baseline_pnl.sum()-longv.baseline_pnl.sum()),
    'skipped':summ(longv.baseline_pnl)
}
# winner/loser concentration of economic change by journey. Positive benefit = -skipped pnl
benefit=veto.groupby('journey').baseline_pnl.sum().mul(-1).sort_values(ascending=False)
positive=benefit[benefit>0]; total_pos=positive.sum()
report['concentration']={
    'vetoed_journeys':int(veto.journey.nunique()),
    'journeys_with_positive_variant_contribution':int((benefit>0).sum()),
    'journeys_with_negative_variant_contribution':int((benefit<0).sum()),
    'top1_positive_share':float(positive.iloc[:1].sum()/total_pos) if total_pos>0 else None,
    'top5_positive_share':float(positive.iloc[:5].sum()/total_pos) if total_pos>0 else None,
    'top10_positive_share':float(positive.iloc[:10].sum()/total_pos) if total_pos>0 else None,
    'largest_positive_journey_benefits':{str(int(k)):float(v) for k,v in positive.head(10).items()},
    'largest_negative_journey_benefits':{str(int(k)):float(v) for k,v in benefit.sort_values().head(10).items()}
}
# annual/side full variant effect
report['full_by_year_side']={}
for (y,s),g in child.groupby(['year','side']):
 report['full_by_year_side'][f"{y}_{'LONG' if s==1 else 'SHORT'}"]={
  'baseline':summ(g.baseline_pnl),'variant':summ(g.loc[~g.veto,'baseline_pnl']),
  'skipped_n':int(g.veto.sum()),'net_change':float(-g.loc[g.veto,'baseline_pnl'].sum())}

child.to_csv(OUT/'ha7_child_ledger.csv',index=False)
j.to_csv(OUT/'ha7_journey_economics.csv',index=False)
with open(OUT/'ha7_summary.json','w') as fp:json.dump(report,fp,indent=2)
print(json.dumps(report,indent=2))
