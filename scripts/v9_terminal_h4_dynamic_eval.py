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
OUT=Path('/mnt/data/v9_terminal_detector_20260915');P=OUT/'TERMINAL_H4_CHECKPOINT_DATASET.csv';ACC=Path('/mnt/data/v9_htf_exhaustion_20260914_fast/ARRIVALS_ACCEPTED.csv');H4=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv')
d=pd.read_csv(P,parse_dates=['ts','latest_child_ts']).replace([np.inf,-np.inf],np.nan); d=d[d.ha_same==1].copy()
acc=pd.read_csv(ACC,parse_dates=['entry_ts','challenge_ts','hybrid_exit_ts']);resolved=acc.groupby('route_id').challenge_ts.first().dropna().index;acc=acc[acc.route_id.isin(resolved)].copy();det=acc[acc.hybrid_status.isin(['SL','CHALLENGE_OPENS','NEXT_H4_LIQ'])&acc.hybrid_pnl.notna()].copy();route_year=acc.groupby('route_id').entry_ts.min().dt.year.to_dict();route_last=acc.groupby('route_id').entry_ts.max().to_dict();route_n=acc.groupby('route_id').size().to_dict()
# HA fast lookup
spec=importlib.util.spec_from_file_location('ha','/mnt/data/analyze_v9_terminal_ha_oracle.py');ha=importlib.util.module_from_spec(spec);spec.loader.exec_module(ha);h4=ha.build_h4_ha(H4);lookup={}
for s in ['UP','DOWN']:
 q=h4[h4.ha_side.eq(s)][['known_at','<CLOSE>']];lookup[s]=(q.known_at.to_numpy(dtype='datetime64[ns]'),q['<CLOSE>'].to_numpy(float))
def signal(at,direction):
 opp='DOWN' if direction=='UP' else 'UP';tt,pp=lookup[opp];j=np.searchsorted(tt,np.datetime64(at),side='right');return (pd.NaT,np.nan) if j>=len(tt) else (pd.Timestamp(tt[j]),float(pp[j]))
# features
cur=[c for c in d if c.startswith('h4c_') and not c.startswith(('h4c_birth_'))]
flow=[c for c in d if c.startswith(('h4c_birth_','same_arrivals_','era4_rejects_'))]
delta=[c for c in d if c.startswith('since_child_')]
child=[c for c in d if c.startswith('child_')]
state=[c for c in ['hours_since_child','bars_since_child','price_from_child_S','open_children','open_cont','h4_bar_body_S','h4_bar_range_S'] if c in d]
small=[c for c in ['h4c_distance_ratio','h4c_same_d1_S','h4c_same_nearest','since_child_h4liq_distance_ratio','since_child_h4liq_same_d1_S','since_child_h4liq_same_active_n','price_from_child_S','h4_bar_body_S','h4c_same_age1_h','child_anchor_mfe_S','child_anchor_peak_giveback_S','child_route_progress_S','child_current_sl_atr180','h4c_birth_opp_since_child','h4c_birth_same_since_child'] if c in d]
fams={'DYN_SMALL':small,'CURRENT_GEOM':cur,'GEOM_DELTA':list(dict.fromkeys(cur+delta+flow)),'FULL_NO_RANK':list(dict.fromkeys(cur+delta+flow+child+state)),'FULL_WITH_RANK':list(dict.fromkeys(cur+delta+flow+child+state+['latest_rank']))}
for k in fams:fams[k]=[c for c in fams[k] if d[c].notna().sum()>20 and d[c].nunique(dropna=True)>1]
def model(kind):
 if kind=='LOGIT':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('m',LogisticRegression(C=.12,max_iter=3000,solver='liblinear',class_weight='balanced',random_state=4))])
 if kind=='TREE2':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DecisionTreeClassifier(max_depth=2,min_samples_leaf=40,class_weight='balanced',random_state=4))])
 if kind=='TREE3':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DecisionTreeClassifier(max_depth=3,min_samples_leaf=30,class_weight='balanced',random_state=4))])
 if kind=='HGB':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',HistGradientBoostingClassifier(max_iter=140,learning_rate=.035,max_leaf_nodes=10,min_samples_leaf=35,l2_regularization=4,random_state=4))])
def score(method,tr,te):
 if method=='MECH_CUR_D1':
  a=tr.h4c_same_d1_S.copy();b=te.h4c_same_d1_S.copy();mx=np.nanquantile(a,.99);return a.fillna(mx*1.5).to_numpy(float),b.fillna(mx*1.5).to_numpy(float)
 fam,kind=method.split('__');cs=fams[fam];m=model(kind);m.fit(tr[cs],tr.terminal_now.astype(int));return m.predict_proba(tr[cs])[:,1],m.predict_proba(te[cs])[:,1]
methods=['MECH_CUR_D1','DYN_SMALL__LOGIT','DYN_SMALL__HGB','GEOM_DELTA__LOGIT','GEOM_DELTA__HGB','FULL_NO_RANK__LOGIT','FULL_NO_RANK__TREE2','FULL_NO_RANK__HGB','FULL_WITH_RANK__LOGIT']
# classification metrics
rows=[];score_cache={}
for yr in [2023,2024,2025,2026]:
 tr=d[d.route_year<yr];te=d[d.route_year==yr]
 for method in methods:
  trs,tes=score(method,tr,te);score_cache[(yr,method)]=(tr.index,trs,te.index,tes)
  if yr>=2024:
   rows.append(dict(year=yr,method=method,auc=roc_auc_score(te.terminal_now,tes),ap=average_precision_score(te.terminal_now,tes)))
met=pd.DataFrame(rows);met.to_csv(OUT/'TERMINAL_H4_DYNAMIC_MODEL_METRICS.csv',index=False);print('CLASSIFICATION');print(met.groupby('method').agg(mean_auc=('auc','mean'),min_auc=('auc','min'),mean_ap=('ap','mean')).sort_values('mean_auc',ascending=False).to_string())
# economic helpers
def pm(g,pcol='pnl'):
 x=g.sort_values('entry_ts')[pcol].to_numpy(float);pos=x[x>0].sum();neg=-x[x<0].sum();eq=np.cumsum(x);pk=np.maximum.accumulate(np.r_[0,eq]);return dict(N=len(x),PnL=x.sum(),PF=pos/neg if neg else np.inf,WR=(x>0).mean(),DD=(pk[1:]-eq).max(),P95=np.quantile(x,.95),Max=x.max(),Top10=np.sort(x)[-10:].sum() if len(x)>=10 else x[x>0].sum())
def sim(yr,sm,thr):
 routes=[r for r,y in route_year.items() if y==yr];dd=d[d.route_id.isin(routes)].copy();dd['score']=dd.index.map(sm);arm={};sig={}
 for rid,g in dd.sort_values('ts').groupby('route_id'):
  hit=g[g.score>=thr]
  if len(hit):
   rr=hit.iloc[0];arm[rid]=rr.ts;sig[rid]=signal(rr.ts,rr.primary)
  else:arm[rid]=pd.NaT;sig[rid]=(pd.NaT,np.nan)
 econ=det[det.route_id.isin(routes)].copy();vals=[];chg=[]
 for r in econ.itertuples():
  st,px=sig.get(r.route_id,(pd.NaT,np.nan));use=pd.notna(st) and st>r.entry_ts and st<r.hybrid_exit_ts
  vals.append(((px-r.entry) if r.direction=='UP' else (r.entry-px)) if use else r.hybrid_pnl);chg.append(use)
 econ['pnl']=vals;econ['changed']=chg;m=pm(econ);m['routes']=len(routes);m['armed_routes']=sum(pd.notna(arm.get(r,pd.NaT)) for r in routes);m['arm_rate']=m['armed_routes']/len(routes) if routes else np.nan;m['arm_before_last']=sum(pd.notna(arm.get(r,pd.NaT)) and arm.get(r,pd.NaT)<route_last[r] for r in routes);m['ha_before_last']=sum(pd.notna(sig.get(r,(pd.NaT,np.nan))[0]) and sig.get(r,(pd.NaT,np.nan))[0]<route_last[r] for r in routes);m['changed']=int(np.sum(chg));return m,econ
# base/oracle cohort
base={};oracle={}
for yr in [2023,2024,2025,2026]:
 routes=[r for r,y in route_year.items() if y==yr];g=det[det.route_id.isin(routes)].copy();g['pnl']=g.hybrid_pnl;base[yr]=pm(g)
 vals=[]
 for r in g.itertuples():
  st,px=signal(route_last[r.route_id],r.direction);use=pd.notna(st) and st>r.entry_ts and st<r.hybrid_exit_ts;vals.append(((px-r.entry) if r.direction=='UP' else (r.entry-px)) if use else r.hybrid_pnl)
 g['pnl']=vals;oracle[yr]=pm(g)
qs=[.50,.70,.80,.90,.95];fixed=[]
for yr in [2023,2024,2025,2026]:
 for method in methods:
  tri,trs,tei,tes=score_cache[(yr,method)];sm=dict(zip(tei,tes))
  for q in qs:
   thr=float(np.quantile(trs,q));m,_=sim(yr,sm,thr);m.update(year=yr,method=method,q=q,threshold=thr,delta=m['PnL']-base[yr]['PnL']);fixed.append(m)
fixed=pd.DataFrame(fixed);fixed.to_csv(OUT/'TERMINAL_H4_DYNAMIC_FIXED_GRID.csv',index=False)
# nested prior-year q selection
nest=[]
for yr in [2024,2025,2026]:
 val=yr-1
 for method in methods:
  vf=fixed[(fixed.year==val)&(fixed.method==method)].sort_values(['delta','q'],ascending=[False,False]);q=float(vf.iloc[0].q);tri,trs,tei,tes=score_cache[(yr,method)];sm=dict(zip(tei,tes));thr=float(np.quantile(trs,q));m,_=sim(yr,sm,thr);delta=m['PnL']-base[yr]['PnL'];od=oracle[yr]['PnL']-base[yr]['PnL'];m.update(year=yr,method=method,selected_q=q,val_delta=float(vf.iloc[0].delta),base_pnl=base[yr]['PnL'],oracle_pnl=oracle[yr]['PnL'],delta=delta,oracle_recovery=delta/od if od else np.nan);nest.append(m)
nest=pd.DataFrame(nest);nest.to_csv(OUT/'TERMINAL_H4_DYNAMIC_NESTED_FORWARD.csv',index=False)
agg=nest.groupby('method').agg(PnL=('PnL','sum'),base=('base_pnl','sum'),oracle=('oracle_pnl','sum'),delta=('delta','sum'),min_year_delta=('delta','min'),recovery=('oracle_recovery','mean'),armed=('armed_routes','sum'),early=('arm_before_last','sum'),ha_before_last=('ha_before_last','sum'),DDmax=('DD','max')).reset_index();agg['pooled_recovery']=agg.delta/(agg.oracle-agg.base);agg=agg.sort_values(['delta','min_year_delta'],ascending=False);agg.to_csv(OUT/'TERMINAL_H4_DYNAMIC_NESTED_SUMMARY.csv',index=False)
print('\nECONOMIC NESTED');print(agg.to_string(index=False));print('\nBY YEAR');print(nest.sort_values(['year','delta'],ascending=[True,False])[['year','method','selected_q','PnL','base_pnl','delta','oracle_pnl','oracle_recovery','armed_routes','arm_before_last','ha_before_last','DD','P95','Max']].to_string(index=False))
