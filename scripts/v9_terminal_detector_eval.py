from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer, MissingIndicator
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import HistGradientBoostingClassifier

P=Path('/mnt/data/v9_terminal_detector_20260915/TERMINAL_CHILD_DATASET.csv')
OUT=P.parent
d=pd.read_csv(P,parse_dates=['ts','challenge_ts','hybrid_exit_ts'])

def cols_start(prefixes): return [c for c in d.columns if any(c.startswith(p) for p in prefixes)]
meta=set(['ts','route_id','accepted_rank','route_total_accepted','role','primary','ref','atr180','atr14','sl_atr180','last_child','challenge_ts','hybrid_status','hybrid_exit_ts','hybrid_exit_price','hybrid_pnl','year','route_last_rank_pct_diag'])
h4geom=[c for c in d if c.startswith('h4liq_') or c.startswith('current_liq_')]
h1geom=[c for c in d if c.startswith('h1liq_')]
dh4=[c for c in d if c.startswith('dprev_h4liq_') or c.startswith('dfirst_h4liq_')]
dh1=[c for c in d if c.startswith('dprev_h1liq_') or c.startswith('dfirst_h1liq_')]
htf=[c for c in d if (c.startswith('h1_') and not c.startswith('h1liq_')) or c.startswith('h4_') or c=='atr14_atr180']
# use compact summaries only, not raw h1_path/body 24 lags
htf=[c for c in htf if not any(x in c for x in ['_l1','_l2','_l3','_l4','_l5','_l6','_l7','_l8','_l9','_l10','_l11','_l12','_l13','_l14','_l15','_l16','_l17','_l18','_l19','_l20','_l21','_l22','_l23','_l24'])]
journey=[c for c in [
 'primary_is_up','route_age_h','accepted_age_h','route_progress_S','accepted_progress_S','route_arrival_count','route_same_arrival_count','hours_since_prev_arrival','hours_since_prev_child','price_since_prev_child_S','current_sl_atr180','open_children_after','open_cont_after','closed_children_count','closed_cont_count','anchor_alive','anchor_age_h','anchor_unreal_S','anchor_unreal_R','anchor_realized_S','anchor_sl_atr180','anchor_mfe_S','anchor_mae_S','anchor_peak_giveback_S','closed_cont_cum_pnl_S','closed_cont_mean_pnl_S','closed_cont_win_rate','last_cont_pnl_S'] if c in d]
journey_count=journey+['accepted_rank_raw']
other_delta=[c for c in d if c.startswith('dprev_') or c.startswith('dfirst_')]
# remove duplicates
families={
 'H4_GEOM':h4geom,
 'H4_GEOM_DELTA':list(dict.fromkeys(h4geom+dh4)),
 'H4_H1_LIQ':list(dict.fromkeys(h4geom+h1geom+dh4+dh1)),
 'JOURNEY_NO_COUNT':journey,
 'HTF_COMPACT':htf,
 'COMBINED_NO_COUNT':list(dict.fromkeys(h4geom+h1geom+dh4+dh1+journey+htf+other_delta)),
 'COMBINED_WITH_COUNT':list(dict.fromkeys(h4geom+h1geom+dh4+dh1+journey_count+htf+other_delta)),
}
# remove constant/allnan
for k,cs in list(families.items()):
    families[k]=[c for c in cs if c in d and d[c].notna().sum()>5 and d[c].nunique(dropna=True)>1]

class WeightedLogit:
    pass

def make_model(kind):
    if kind=='LOGIT':
        return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('m',LogisticRegression(C=.15,max_iter=4000,solver='liblinear',class_weight='balanced',random_state=1))])
    if kind=='TREE2':
        return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DecisionTreeClassifier(max_depth=2,min_samples_leaf=25,class_weight='balanced',random_state=1))])
    if kind=='TREE3':
        return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DecisionTreeClassifier(max_depth=3,min_samples_leaf=20,class_weight='balanced',random_state=1))])
    if kind=='HGB':
        return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',HistGradientBoostingClassifier(max_iter=160,learning_rate=.035,max_leaf_nodes=10,min_samples_leaf=25,l2_regularization=3.0,random_state=1))])

def route_metrics(g,score):
    z=g[['route_id','accepted_rank','last_child']].copy(); z['score']=score
    maxok=[]; pct=[]; pair=[]
    for rid,q in z.groupby('route_id'):
        q=q.sort_values('accepted_rank'); last=q[q.last_child==1]
        if len(last)!=1: continue
        s=float(last.score.iloc[0]); prev=q[q.last_child==0].score.to_numpy(float)
        if len(prev)==0:
            maxok.append(1.0); pct.append(1.0); continue
        maxok.append(float(s>=np.nanmax(prev)))
        pair.extend((s>prev).astype(float).tolist()); pair.extend((s==prev).astype(float).tolist()) # temp corrected below
        # percentile among route, ties averaged
        vals=q.score.to_numpy(float); pct.append((np.sum(vals<s)+0.5*np.sum(vals==s))/len(vals))
    # recompute pairwise with ties=.5 correctly
    pair=[]
    for rid,q in z.groupby('route_id'):
        last=q[q.last_child==1]
        if len(last)!=1: continue
        s=float(last.score.iloc[0]); prev=q[q.last_child==0].score.to_numpy(float)
        if len(prev): pair.extend(np.where(s>prev,1.0,np.where(s==prev,.5,0.0)).tolist())
    return {'last_is_route_max':np.mean(maxok) if maxok else np.nan,'last_route_percentile':np.mean(pct) if pct else np.nan,'within_route_pair_auc':np.mean(pair) if pair else np.nan}

rows=[]; preds=[]
for year in [2024,2025,2026]:
    tr=d[d.year<year].copy(); te=d[d.year==year].copy()
    ytr=tr.last_child.to_numpy(int); yte=te.last_child.to_numpy(int)
    # route-balanced weights + class balancing approximately via model class_weight where supported. HGB sample weights manually class adjusted.
    routew=1/tr.groupby('route_id').route_id.transform('size').to_numpy(float)
    classw=np.where(ytr==1,1/max((ytr==1).sum(),1),1/max((ytr==0).sum(),1))
    classw=classw/np.mean(classw)
    rbw=routew/np.mean(routew)
    for fam,cs in families.items():
      for kind in ['LOGIT','TREE2','TREE3','HGB']:
        m=make_model(kind)
        fitkw={}
        # compare standard and route-balanced only for logit/HGB via nested loop
        for weight_mode in ['ROW','ROUTE_BAL']:
            m=make_model(kind)
            sw=None
            if weight_mode=='ROUTE_BAL':
                sw=rbw*classw if kind=='HGB' else rbw
            try:
                if sw is None: m.fit(tr[cs],ytr)
                else:
                    # Pipeline routes sample_weight to final estimator
                    m.fit(tr[cs],ytr,**({'m__sample_weight':sw}))
                p=m.predict_proba(te[cs])[:,1]
            except Exception as e:
                continue
            auc=roc_auc_score(yte,p); ap=average_precision_score(yte,p); br=brier_score_loss(yte,p)
            rm=route_metrics(te,p)
            rows.append({'year':year,'family':fam,'model':kind,'weight':weight_mode,'n_features':len(cs),'auc':auc,'ap':ap,'brier':br,**rm})
            for i,idx in enumerate(te.index): preds.append({'idx':idx,'year':year,'route_id':int(te.loc[idx,'route_id']),'accepted_rank':int(te.loc[idx,'accepted_rank']),'last_child':int(te.loc[idx,'last_child']),'family':fam,'model':kind,'weight':weight_mode,'score':float(p[i])})

# Mechanical single variables, orientation frozen from training.
mech=['h4liq_same_d1_S','h4liq_distance_ratio','h4liq_nearest_margin_S','h4liq_same_active_n','h4liq_opp_d1_S','h4liq_same_age1_h','current_liq_age_median_h','dprev_h4liq_same_d1_S','dfirst_h4liq_same_d1_S']
for year in [2024,2025,2026]:
  tr=d[d.year<year]; te=d[d.year==year]; ytr=tr.last_child.astype(int); yte=te.last_child.astype(int)
  for c in mech:
    if c not in d: continue
    # semantic missing handling for same target: missing = large distance; else median
    trv=tr[c].astype(float).copy(); tev=te[c].astype(float).copy()
    if c=='h4liq_same_d1_S':
        mx=np.nanquantile(trv,.99) if trv.notna().any() else 1.0
        trv=trv.fillna(mx*1.5); tev=tev.fillna(mx*1.5)
    else:
        med=trv.median(); trv=trv.fillna(med); tev=tev.fillna(med)
    if trv.nunique()<2: continue
    a=roc_auc_score(ytr,trv)
    sign=1 if a>=.5 else -1
    s=sign*tev.to_numpy(float)
    auc=roc_auc_score(yte,s); ap=average_precision_score(yte,s)
    rm=route_metrics(te,s)
    rows.append({'year':year,'family':'MECH_SINGLE','model':c,'weight':'ROW','n_features':1,'auc':auc,'ap':ap,'brier':np.nan,**rm,'train_orientation':sign})
    for i,idx in enumerate(te.index): preds.append({'idx':idx,'year':year,'route_id':int(te.loc[idx,'route_id']),'accepted_rank':int(te.loc[idx,'accepted_rank']),'last_child':int(te.loc[idx,'last_child']),'family':'MECH_SINGLE','model':c,'weight':'ROW','score':float(s[i])})

met=pd.DataFrame(rows); pred=pd.DataFrame(preds)
met.to_csv(OUT/'TERMINAL_MODEL_METRICS.csv',index=False); pred.to_csv(OUT/'TERMINAL_MODEL_PREDICTIONS.csv',index=False)
# aggregate robustness ranking
agg=met.groupby(['family','model','weight']).agg(mean_auc=('auc','mean'),min_auc=('auc','min'),mean_ap=('ap','mean'),mean_lastmax=('last_is_route_max','mean'),mean_routepct=('last_route_percentile','mean'),mean_pairauc=('within_route_pair_auc','mean'),years=('year','nunique')).reset_index()
agg=agg[agg.years==3].sort_values(['mean_auc','min_auc'],ascending=False)
agg.to_csv(OUT/'TERMINAL_MODEL_RANKING.csv',index=False)
print(agg.head(25).to_string(index=False))
