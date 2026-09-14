from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
OUT=Path('/mnt/data/v9_terminal_detector_20260915')
D=OUT/'TERMINAL_CHILD_DATASET.csv'; ACC=Path('/mnt/data/v9_htf_exhaustion_20260914_fast/ARRIVALS_ACCEPTED.csv'); H4=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv')
d=pd.read_csv(D,parse_dates=['ts']).replace([np.inf,-np.inf],np.nan)
acc=pd.read_csv(ACC,parse_dates=['entry_ts','challenge_ts','hybrid_exit_ts'])
resolved_routes=acc.groupby('route_id').challenge_ts.first().dropna().index
acc=acc[acc.route_id.isin(resolved_routes)].copy()
# deterministic economic ledger
det=acc[acc.hybrid_status.isin(['SL','CHALLENGE_OPENS','NEXT_H4_LIQ']) & acc.hybrid_pnl.notna()].copy()
route_start=acc.groupby('route_id').entry_ts.min(); route_year=route_start.dt.year.to_dict(); route_last=acc.groupby('route_id').entry_ts.max().to_dict(); route_n=acc.groupby('route_id').size().to_dict()
# HA helper
spec=importlib.util.spec_from_file_location('ha','/mnt/data/analyze_v9_terminal_ha_oracle.py');ha=importlib.util.module_from_spec(spec);spec.loader.exec_module(ha)
h4=ha.build_h4_ha(H4)
# Fast HA1 lookup arrays; first completed opposite-color H4 strictly after arm time.
ha_lookup={}
for side in ['UP','DOWN']:
    q=h4[h4.ha_side.eq(side)][['known_at','<CLOSE>']].copy()
    ha_lookup[side]=(q.known_at.to_numpy(dtype='datetime64[ns]'),q['<CLOSE>'].to_numpy(float))
def fast_signal(armed_at,direction):
    opp='DOWN' if direction=='UP' else 'UP'
    tt,pp=ha_lookup[opp]; j=np.searchsorted(tt,np.datetime64(armed_at),side='right')
    if j>=len(tt): return pd.NaT,np.nan
    return pd.Timestamp(tt[j]),float(pp[j])
# features
h4base=[c for c in d if c.startswith('h4liq_') or c.startswith('current_liq_')]
h4rel=[c for c in d if c.startswith(('dprev_h4liq_','dfirst_h4liq_','ratiofirst_h4liq_','relmedian_h4liq_','is_running_')) and ('h4liq_' in c or 'current_liq_' in c)]
h4flow=[c for c in d if c.startswith(('h4_birth_','h4_replenish_','h4_active_')) or c.startswith('current_liq_age_prior') or c.startswith('current_liq_age_vs') or c.startswith('current_liq_age_ratio')]
small=['h4liq_same_d1_S','h4liq_distance_ratio','h4liq_same_active_n','h4liq_opp_d1_S','relmedian_h4liq_same_d1_S','ratiofirst_h4liq_same_active_n','h4_replenish_net_since_first','h4_birth_balance_since_prev','h4_active_routeborn_balance','current_liq_age_prior_percentile']
small=[c for c in small if c in d]
h4all=list(dict.fromkeys(h4base+h4rel+h4flow))

def mk(kind):
 if kind=='SMALL_LOGIT': return small,Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('m',LogisticRegression(C=.12,max_iter=4000,solver='liblinear',class_weight='balanced',random_state=3))])
 if kind=='SMALL_HGB': return small,Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',HistGradientBoostingClassifier(max_iter=140,learning_rate=.035,max_leaf_nodes=10,min_samples_leaf=24,l2_regularization=4,random_state=3))])
 if kind=='H4ALL_HGB': return h4all,Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',HistGradientBoostingClassifier(max_iter=140,learning_rate=.035,max_leaf_nodes=10,min_samples_leaf=24,l2_regularization=4,random_state=3))])
 if kind=='H4BASE_LOGIT': return h4base,Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('m',LogisticRegression(C=.12,max_iter=4000,solver='liblinear',class_weight='balanced',random_state=3))])
 if kind=='H4ALL_TREE2': return h4all,Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DecisionTreeClassifier(max_depth=2,min_samples_leaf=25,class_weight='balanced',random_state=3))])
 raise KeyError(kind)

def empirical_pct(train,vals):
 a=np.sort(np.asarray(train,float)); v=np.asarray(vals,float); return np.searchsorted(a,v,side='right')/len(a)

def score_method(method,train,test):
 if method=='MECH_D1':
  tr=train.h4liq_same_d1_S.copy(); te=test.h4liq_same_d1_S.copy(); mx=np.nanquantile(tr,.99); tr=tr.fillna(mx*1.5); te=te.fillna(mx*1.5); return tr.to_numpy(float),te.to_numpy(float)
 if method=='MECH4':
  specs=[('h4liq_same_d1_S',1,'HIGHMISS'),('h4liq_distance_ratio',1,'MED'),('h4liq_same_active_n',-1,'MED'),('h4_replenish_net_since_first',-1,'MED')]
  trs=[];tes=[]
  for c,sg,miss in specs:
   a=train[c].astype(float).copy(); b=test[c].astype(float).copy()
   if miss=='HIGHMISS':
    mx=np.nanquantile(a,.99); a=a.fillna(mx*1.5); b=b.fillna(mx*1.5)
   else:
    med=a.median();a=a.fillna(med);b=b.fillna(med)
   aa=sg*a.to_numpy(float);bb=sg*b.to_numpy(float)
   trs.append(empirical_pct(aa,aa));tes.append(empirical_pct(aa,bb))
  return np.mean(trs,axis=0),np.mean(tes,axis=0)
 cs,m=mk(method);m.fit(train[cs],train.last_child.astype(int));return m.predict_proba(train[cs])[:,1],m.predict_proba(test[cs])[:,1]

def metrics_pnl(g,pcol='pnl'):
 x=g.sort_values('entry_ts')[pcol].to_numpy(float);pos=x[x>0].sum();neg=-x[x<0].sum();eq=np.cumsum(x);pk=np.maximum.accumulate(np.r_[0,eq]);dd=(pk[1:]-eq).max() if len(x) else 0
 return dict(N=len(x),PnL=x.sum(),PF=pos/neg if neg else np.inf,WR=(x>0).mean() if len(x) else np.nan,DD=dd,P95=np.quantile(x,.95) if len(x) else np.nan,Max=x.max() if len(x) else np.nan,Top10=np.sort(x)[-10:].sum() if len(x)>=10 else x[x>0].sum())

def simulate(year,score_map,threshold,policy='HA1'):
 # route start year defines evaluation cohort
 routes=[r for r,y in route_year.items() if y==year]
 dd=d[d.route_id.isin(routes)].copy();dd['score']=dd.index.map(score_map)
 arm={};sig={};arm_rank={}
 for rid,g in dd.sort_values('ts').groupby('route_id'):
  hit=g[g.score>=threshold]
  if len(hit):
   row=hit.iloc[0]; at=row.ts; ar=int(row.accepted_rank); direction=row.primary
   st,px=fast_signal(at,direction)
   arm[rid]=at;arm_rank[rid]=ar;sig[rid]=(st,px)
  else:
   arm[rid]=pd.NaT;arm_rank[rid]=np.nan;sig[rid]=(pd.NaT,np.nan)
 econ=det[det.route_id.isin(routes)].copy(); vals=[]; changed=[]
 for r in econ.itertuples():
  st,px=sig.get(r.route_id,(pd.NaT,np.nan));use=pd.notna(st) and st>r.entry_ts and st<r.hybrid_exit_ts
  if use:
   pnl=(px-r.entry) if r.direction=='UP' else (r.entry-px); vals.append(pnl);changed.append(True)
  else: vals.append(r.hybrid_pnl);changed.append(False)
 econ['pnl']=vals;econ['changed']=changed
 m=metrics_pnl(econ)
 # route diagnostics
 nroute=len(routes);armed=sum(pd.notna(arm[r]) for r in routes)
 arm_last=sum(pd.notna(arm[r]) and arm_rank[r]==route_n[r] for r in routes)
 arm_early=sum(pd.notna(arm[r]) and arm_rank[r]<route_n[r] for r in routes)
 ha_before_last=sum(pd.notna(sig[r][0]) and sig[r][0]<route_last[r] for r in routes)
 m.update(routes=nroute,armed_routes=armed,arm_rate=armed/nroute if nroute else np.nan,arm_exact_last=arm_last,arm_early=arm_early,ha_before_true_last=ha_before_last,changed=int(econ.changed.sum()))
 return m,econ,arm,sig

methods=['MECH_D1','MECH4','H4BASE_LOGIT','SMALL_LOGIT','SMALL_HGB','H4ALL_TREE2','H4ALL_HGB']
qs=[.50,.70,.80,.90,.95]
# cache year-model scores: model train uses all years before target/validation year.
score_cache={}
for yr in [2023,2024,2025,2026]:
 tr=d[d.year<yr];te=d[d.route_id.map(route_year).eq(yr)] # score all rows in routes that start yr, including possible cross-year children
 for method in methods:
  trs,tes=score_method(method,tr,te);score_cache[(yr,method)]=(tr.index,trs,te.index,tes)

# fixed-q results on 2024-26 + validation 2023
rows=[]
for yr in [2023,2024,2025,2026]:
 for method in methods:
  tri,trs,tei,tes=score_cache[(yr,method)]; sm=dict(zip(tei,tes))
  for q in qs:
   threshold=float(np.quantile(trs,q));m,*_=simulate(yr,sm,threshold);m.update(year=yr,method=method,q=q,threshold=threshold);rows.append(m)
fixed=pd.DataFrame(rows);fixed.to_csv(OUT/'TERMINAL_HA1_FIXED_ARMING_GRID.csv',index=False)

# nested choice: each test year's q selected solely from previous year's fixed-q sequential PnL delta vs BASE.
# BASE by route-year
base_by={}
for yr in [2023,2024,2025,2026]:
 routes=[r for r,y in route_year.items() if y==yr];g=det[det.route_id.isin(routes)].copy();g['pnl']=g.hybrid_pnl;base_by[yr]=metrics_pnl(g)
# oracle by applying true-last HA1 to same cohorts for recovered fraction
oracle_by={}
for yr in [2023,2024,2025,2026]:
 routes=[r for r,y in route_year.items() if y==yr];g=det[det.route_id.isin(routes)].copy(); vals=[]
 for r in g.itertuples():
  at=route_last[r.route_id]; st,px=fast_signal(at,r.direction); use=pd.notna(st) and st>r.entry_ts and st<r.hybrid_exit_ts
  vals.append(((px-r.entry) if r.direction=='UP' else (r.entry-px)) if use else r.hybrid_pnl)
 g['pnl']=vals;oracle_by[yr]=metrics_pnl(g)

nested=[];ledgers=[]
for yr in [2024,2025,2026]:
 valyr=yr-1
 for method in methods:
  vf=fixed[(fixed.year==valyr)&(fixed.method==method)].copy();vf['delta']=vf.PnL-base_by[valyr]['PnL']
  # tie -> more selective q
  best=vf.sort_values(['delta','q'],ascending=[False,False]).iloc[0];q=float(best.q)
  tri,trs,tei,tes=score_cache[(yr,method)];threshold=float(np.quantile(trs,q));sm=dict(zip(tei,tes))
  m,econ,arm,sig=simulate(yr,sm,threshold);base=base_by[yr];ora=oracle_by[yr];delta=m['PnL']-base['PnL'];oden=ora['PnL']-base['PnL'];rec=delta/oden if oden!=0 else np.nan
  m.update(year=yr,method=method,selected_q=q,val_year=valyr,val_delta=float(best.delta),base_pnl=base['PnL'],oracle_pnl=ora['PnL'],delta=delta,oracle_recovery=rec)
  nested.append(m)
  econ['year_eval']=yr;econ['method']=method;econ['selected_q']=q;ledgers.append(econ)
nest=pd.DataFrame(nested);nest.to_csv(OUT/'TERMINAL_HA1_NESTED_FORWARD.csv',index=False);pd.concat(ledgers).to_csv(OUT/'TERMINAL_HA1_NESTED_TRADE_LEDGER.csv',index=False)
agg=nest.groupby('method').agg(PnL=('PnL','sum'),base=('base_pnl','sum'),oracle=('oracle_pnl','sum'),delta=('delta','sum'),mean_recovery=('oracle_recovery','mean'),min_year_delta=('delta','min'),PF_mean=('PF','mean'),DD_max=('DD','max'),armed=('armed_routes','sum'),early=('arm_early','sum'),ha_before_last=('ha_before_true_last','sum'),changed=('changed','sum')).reset_index()
agg['pooled_recovery']=agg.delta/(agg.oracle-agg.base)
agg=agg.sort_values(['delta','min_year_delta'],ascending=False);agg.to_csv(OUT/'TERMINAL_HA1_NESTED_SUMMARY.csv',index=False)
print('\nNESTED SUMMARY 2024-2026')
print(agg.to_string(index=False))
print('\nBY YEAR TOP')
print(nest.sort_values(['year','delta'],ascending=[True,False])[['year','method','selected_q','PnL','base_pnl','delta','oracle_pnl','oracle_recovery','armed_routes','arm_early','ha_before_true_last','DD','P95','Max']].to_string(index=False))
