from pathlib import Path
import importlib.util
import numpy as np,pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score,average_precision_score
OUT=Path('/mnt/data/v9_terminal_detector_20260915');P=OUT/'TERMINAL_H4_CHECKPOINT_DATASET.csv';ACC=Path('/mnt/data/v9_htf_exhaustion_20260914_fast/ARRIVALS_ACCEPTED.csv')
d=pd.read_csv(P,parse_dates=['ts','latest_child_ts']).replace([np.inf,-np.inf],np.nan);d=d[d.ha_opp==1].copy()
acc=pd.read_csv(ACC,parse_dates=['entry_ts','challenge_ts','hybrid_exit_ts']);resolved=acc.groupby('route_id').challenge_ts.first().dropna().index;acc=acc[acc.route_id.isin(resolved)].copy();det=acc[acc.hybrid_status.isin(['SL','CHALLENGE_OPENS','NEXT_H4_LIQ'])&acc.hybrid_pnl.notna()].copy();route_year=acc.groupby('route_id').entry_ts.min().dt.year.to_dict();route_last=acc.groupby('route_id').entry_ts.max().to_dict()
cur=[c for c in d if c.startswith('h4c_') and not c.startswith('h4c_birth_')];flow=[c for c in d if c.startswith(('h4c_birth_','same_arrivals_','era4_rejects_'))];delta=[c for c in d if c.startswith('since_child_')];child=[c for c in d if c.startswith('child_')];state=[c for c in ['hours_since_child','bars_since_child','price_from_child_S','open_children','open_cont','h4_bar_body_S','h4_bar_range_S'] if c in d]
small=[c for c in ['h4c_distance_ratio','h4c_same_d1_S','h4c_same_nearest','since_child_h4liq_distance_ratio','since_child_h4liq_same_d1_S','since_child_h4liq_same_active_n','price_from_child_S','h4_bar_body_S','h4_bar_range_S','h4c_same_age1_h','child_anchor_mfe_S','child_anchor_peak_giveback_S','child_route_progress_S','child_current_sl_atr180','h4c_birth_opp_since_child','h4c_birth_same_since_child','hours_since_child'] if c in d]
fams={'SMALL':small,'GEOM':cur,'GEOM_DELTA':list(dict.fromkeys(cur+delta+flow)),'FULL':list(dict.fromkeys(cur+delta+flow+child+state))}
for k in fams:fams[k]=[c for c in fams[k] if d[c].notna().sum()>10 and d[c].nunique(dropna=True)>1]
def mk(kind):
 if kind=='LOGIT':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('m',LogisticRegression(C=.12,max_iter=3000,solver='liblinear',class_weight='balanced',random_state=5))])
 if kind=='TREE2':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DecisionTreeClassifier(max_depth=2,min_samples_leaf=25,class_weight='balanced',random_state=5))])
 if kind=='TREE3':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DecisionTreeClassifier(max_depth=3,min_samples_leaf=20,class_weight='balanced',random_state=5))])
 if kind=='HGB':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',HistGradientBoostingClassifier(max_iter=140,learning_rate=.035,max_leaf_nodes=10,min_samples_leaf=25,l2_regularization=4,random_state=5))])
def score(method,tr,te):
 if method=='MECH_D1':
  a=tr.h4c_same_d1_S.copy();b=te.h4c_same_d1_S.copy();mx=np.nanquantile(a,.99);return a.fillna(mx*1.5).to_numpy(float),b.fillna(mx*1.5).to_numpy(float)
 if method=='MECH_RATIO':
  a=tr.h4c_distance_ratio.copy();b=te.h4c_distance_ratio.copy();med=a.median();return a.fillna(med).to_numpy(float),b.fillna(med).to_numpy(float)
 if method=='MECH_RATIO_DELTA':
  a=tr.since_child_h4liq_distance_ratio.copy();b=te.since_child_h4liq_distance_ratio.copy();med=a.median();return a.fillna(med).to_numpy(float),b.fillna(med).to_numpy(float)
 if method=='MECH_PRICE_RETRACE':
  a=-tr.price_from_child_S.copy();b=-te.price_from_child_S.copy();med=a.median();return a.fillna(med).to_numpy(float),b.fillna(med).to_numpy(float)
 fam,kind=method.split('__');cs=fams[fam];m=mk(kind);m.fit(tr[cs],tr.terminal_now.astype(int));return m.predict_proba(tr[cs])[:,1],m.predict_proba(te[cs])[:,1]
methods=['MECH_RATIO','MECH_RATIO_DELTA','MECH_PRICE_RETRACE','MECH_D1','SMALL__LOGIT','SMALL__TREE2','SMALL__HGB','GEOM_DELTA__LOGIT','GEOM_DELTA__HGB','FULL__LOGIT','FULL__TREE2','FULL__HGB']
# classification + score caches
cache={};mets=[]
for yr in [2023,2024,2025,2026]:
 tr=d[d.route_year<yr];te=d[d.route_year==yr]
 for method in methods:
  trs,tes=score(method,tr,te);cache[(yr,method)]=(tr.index,trs,te.index,tes)
  if yr>=2024:mets.append({'year':yr,'method':method,'auc':roc_auc_score(te.terminal_now,tes),'ap':average_precision_score(te.terminal_now,tes),'base_rate':te.terminal_now.mean(),'n':len(te)})
met=pd.DataFrame(mets);met.to_csv(OUT/'TERMINAL_HA_EVENT_MODEL_METRICS.csv',index=False);print('CLASS');print(met.groupby('method').agg(mean_auc=('auc','mean'),min_auc=('auc','min'),mean_ap=('ap','mean')).sort_values('mean_auc',ascending=False).to_string())
# econ helpers
def pm(g,p='pnl'):
 x=g.sort_values('entry_ts')[p].to_numpy(float);pos=x[x>0].sum();neg=-x[x<0].sum();eq=np.cumsum(x);pk=np.maximum.accumulate(np.r_[0,eq]);return {'PnL':x.sum(),'PF':pos/neg if neg else np.inf,'WR':(x>0).mean(),'DD':(pk[1:]-eq).max(),'P95':np.quantile(x,.95),'Max':x.max(),'N':len(x)}
def sim(yr,sm,thr):
 routes=[r for r,y in route_year.items() if y==yr];events=d[d.route_id.isin(routes)].copy();events['score']=events.index.map(sm);chosen={}
 for rid,g in events.sort_values('ts').groupby('route_id'):
  hit=g[g.score>=thr]; chosen[rid]=hit.iloc[0] if len(hit) else None
 econ=det[det.route_id.isin(routes)].copy();vals=[];chg=[]
 for r in econ.itertuples():
  ev=chosen.get(r.route_id);use=ev is not None and ev.ts>r.entry_ts and ev.ts<r.hybrid_exit_ts
  if use:
   px=float(ev.price);vals.append((px-r.entry) if r.direction=='UP' else (r.entry-px));chg.append(True)
  else:vals.append(r.hybrid_pnl);chg.append(False)
 econ['pnl']=vals;econ['changed']=chg;m=pm(econ);m['routes']=len(routes);m['event_routes']=sum(v is not None for v in chosen.values());m['event_before_last']=sum(v is not None and v.ts<route_last[r] for r,v in chosen.items());m['changed']=sum(chg);return m
base={};oracle={}
# oracle event gate = first opposite HA event after true last child among dynamic event rows, should approximate terminal oracle HA1 but may omit routes no open checkpoint.
for yr in [2023,2024,2025,2026]:
 routes=[r for r,y in route_year.items() if y==yr];g=det[det.route_id.isin(routes)].copy();g['pnl']=g.hybrid_pnl;base[yr]=pm(g)
 evs=d[(d.route_id.isin(routes)) & (d.ts>d.route_id.map(route_last))].sort_values('ts').groupby('route_id').first().reset_index();emap={r.route_id:r for r in evs.itertuples()};vals=[]
 for r in g.itertuples():
  ev=emap.get(r.route_id);use=ev is not None and ev.ts>r.entry_ts and ev.ts<r.hybrid_exit_ts
  vals.append(((ev.price-r.entry) if r.direction=='UP' else (r.entry-ev.price)) if use else r.hybrid_pnl)
 g['pnl']=vals;oracle[yr]=pm(g)
qs=[.5,.7,.8,.9,.95];fixed=[]
for yr in [2023,2024,2025,2026]:
 for method in methods:
  tri,trs,tei,tes=cache[(yr,method)];sm=dict(zip(tei,tes))
  for q in qs:
   thr=float(np.quantile(trs,q));m=sim(yr,sm,thr);m.update(year=yr,method=method,q=q,delta=m['PnL']-base[yr]['PnL']);fixed.append(m)
fixed=pd.DataFrame(fixed);fixed.to_csv(OUT/'TERMINAL_HA_EVENT_FIXED_GRID.csv',index=False)
nest=[]
for yr in [2024,2025,2026]:
 val=yr-1
 for method in methods:
  vf=fixed[(fixed.year==val)&(fixed.method==method)].sort_values(['delta','q'],ascending=[False,False]);q=float(vf.iloc[0].q);tri,trs,tei,tes=cache[(yr,method)];sm=dict(zip(tei,tes));thr=float(np.quantile(trs,q));m=sim(yr,sm,thr);delta=m['PnL']-base[yr]['PnL'];od=oracle[yr]['PnL']-base[yr]['PnL'];m.update(year=yr,method=method,selected_q=q,val_delta=float(vf.iloc[0].delta),base_pnl=base[yr]['PnL'],oracle_pnl=oracle[yr]['PnL'],delta=delta,oracle_recovery=delta/od if od else np.nan);nest.append(m)
nest=pd.DataFrame(nest);nest.to_csv(OUT/'TERMINAL_HA_EVENT_NESTED_FORWARD.csv',index=False);agg=nest.groupby('method').agg(PnL=('PnL','sum'),base=('base_pnl','sum'),oracle=('oracle_pnl','sum'),delta=('delta','sum'),min_year_delta=('delta','min'),armed=('event_routes','sum'),early=('event_before_last','sum'),DDmax=('DD','max')).reset_index();agg['pooled_recovery']=agg.delta/(agg.oracle-agg.base);agg=agg.sort_values(['delta','min_year_delta'],ascending=False);agg.to_csv(OUT/'TERMINAL_HA_EVENT_NESTED_SUMMARY.csv',index=False);print('\nECON');print(agg.to_string(index=False));print('\nBY YEAR');print(nest.sort_values(['year','delta'],ascending=[True,False])[['year','method','selected_q','PnL','base_pnl','delta','oracle_pnl','oracle_recovery','event_routes','event_before_last','DD','P95','Max']].to_string(index=False))
