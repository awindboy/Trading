from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
P=Path('/mnt/data/v9_terminal_detector_20260915/TERMINAL_CHILD_DATASET.csv'); OUT=P.parent
d=pd.read_csv(P,parse_dates=['ts']); d=d.replace([np.inf,-np.inf],np.nan)
# feature sets
h4base=[c for c in d if c.startswith('h4liq_') or c.startswith('current_liq_')]
h4rel=[c for c in d if c.startswith(('dprev_h4liq_','dfirst_h4liq_','ratiofirst_h4liq_','relmedian_h4liq_','is_running_')) and ('h4liq_' in c or 'current_liq_' in c)]
h4flow=[c for c in d if c.startswith(('h4_birth_','h4_replenish_','h4_active_')) or c.startswith('current_liq_age_prior') or c.startswith('current_liq_age_vs') or c.startswith('current_liq_age_ratio')]
h1liq=[c for c in d if c.startswith('h1liq_') or c.startswith(('dprev_h1liq_','dfirst_h1liq_'))]
journey=[c for c in ['primary_is_up','route_age_h','accepted_age_h','route_progress_S','accepted_progress_S','route_arrival_count','route_same_arrival_count','hours_since_prev_arrival','hours_since_prev_child','price_since_prev_child_S','current_sl_atr180','open_children_after','open_cont_after','closed_children_count','closed_cont_count','anchor_alive','anchor_age_h','anchor_unreal_S','anchor_unreal_R','anchor_realized_S','anchor_mfe_S','anchor_mae_S','anchor_peak_giveback_S','closed_cont_cum_pnl_S','closed_cont_mean_pnl_S','closed_cont_win_rate','last_cont_pnl_S','sl_progress_from_first_S','sl_change_prev_S'] if c in d]
journey_noclock=[c for c in journey if c not in ['route_age_h','accepted_age_h','route_arrival_count','route_same_arrival_count','anchor_age_h','closed_children_count','closed_cont_count']]
htf=[c for c in d if (c.startswith('h1_') and not c.startswith('h1liq_')) or c.startswith('h4_') or c=='atr14_atr180']
htf=[c for c in htf if not any(f'_l{i}' in c for i in range(1,25)) and not c.startswith(('h4_birth_','h4_replenish_','h4_active_'))]
small=['h4liq_same_d1_S','h4liq_distance_ratio','h4liq_same_active_n','h4liq_opp_d1_S','relmedian_h4liq_same_d1_S','ratiofirst_h4liq_same_active_n','h4_replenish_net_since_first','h4_birth_balance_since_prev','h4_active_routeborn_balance','current_liq_age_prior_percentile']
small=[c for c in small if c in d]
fams={
 'SMALL_GEOM':small,
 'H4_BASE':h4base,
 'H4_FLOW':list(dict.fromkeys(h4base+h4flow)),
 'H4_ROUTE_REL':list(dict.fromkeys(h4base+h4rel)),
 'H4_ALL':list(dict.fromkeys(h4base+h4rel+h4flow)),
 'H4_H1LIQ_ALL':list(dict.fromkeys(h4base+h4rel+h4flow+h1liq)),
 'COMBINED_NOCLOCK':list(dict.fromkeys(h4base+h4rel+h4flow+h1liq+journey_noclock+htf)),
 'COMBINED_FULL':list(dict.fromkeys(h4base+h4rel+h4flow+h1liq+journey+htf+['accepted_rank_raw'])),
}
for k in fams:fams[k]=[c for c in fams[k] if d[c].notna().sum()>10 and d[c].nunique(dropna=True)>1]

def model(kind):
 if kind=='LOGIT':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('m',LogisticRegression(C=.12,max_iter=4000,solver='liblinear',class_weight='balanced',random_state=2))])
 if kind=='TREE2':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DecisionTreeClassifier(max_depth=2,min_samples_leaf=25,class_weight='balanced',random_state=2))])
 if kind=='TREE3':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DecisionTreeClassifier(max_depth=3,min_samples_leaf=20,class_weight='balanced',random_state=2))])
 if kind=='HGB':return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',HistGradientBoostingClassifier(max_iter=140,learning_rate=.035,max_leaf_nodes=10,min_samples_leaf=24,l2_regularization=4,random_state=2))])

def route_metrics(g,s):
 x=g[['route_id','accepted_rank','last_child']].copy();x['s']=s
 pair=[];mx=[];pct=[]
 for _,q in x.groupby('route_id'):
  last=q[q.last_child==1]
  if len(last)!=1:continue
  sl=last.s.iloc[0]; prev=q[q.last_child==0].s.to_numpy(float); vals=q.s.to_numpy(float)
  if len(prev):
   pair+=np.where(sl>prev,1,np.where(sl==prev,.5,0)).tolist();mx.append(float(sl>=np.max(prev)))
  pct.append((np.sum(vals<sl)+.5*np.sum(vals==sl))/len(vals))
 return np.mean(pair) if pair else np.nan,np.mean(mx) if mx else np.nan,np.mean(pct)
rows=[];pred=[]
for year in [2024,2025,2026]:
 tr=d[d.year<year];te=d[d.year==year];yt=tr.last_child.astype(int);yv=te.last_child.astype(int)
 for fam,cs in fams.items():
  kinds=['LOGIT','TREE2','TREE3'] + (['HGB'] if fam in ['SMALL_GEOM','H4_ALL'] else [])
  for kind in kinds:
   m=model(kind);m.fit(tr[cs],yt);p=m.predict_proba(te[cs])[:,1]
   auc=roc_auc_score(yv,p);ap=average_precision_score(yv,p); pair,mx,pct=route_metrics(te,p)
   rows.append(dict(year=year,family=fam,model=kind,n_features=len(cs),auc=auc,ap=ap,pair_auc=pair,last_max=mx,last_pct=pct))
   for j,(idx,r) in enumerate(te.iterrows()):pred.append(dict(idx=idx,year=year,route_id=int(r.route_id),accepted_rank=int(r.accepted_rank),last_child=int(r.last_child),family=fam,model=kind,score=float(p[j])))
met=pd.DataFrame(rows);pred=pd.DataFrame(pred);met.to_csv(OUT/'TERMINAL_MODEL_METRICS_ENRICHED.csv',index=False);pred.to_csv(OUT/'TERMINAL_MODEL_PRED_ENRICHED.csv',index=False)
agg=met.groupby(['family','model']).agg(mean_auc=('auc','mean'),min_auc=('auc','min'),mean_ap=('ap','mean'),mean_pair=('pair_auc','mean'),mean_lastmax=('last_max','mean'),mean_lastpct=('last_pct','mean')).reset_index().sort_values(['mean_auc','min_auc'],ascending=False)
agg.to_csv(OUT/'TERMINAL_MODEL_RANKING_ENRICHED.csv',index=False)
print(agg.head(30).to_string(index=False))
