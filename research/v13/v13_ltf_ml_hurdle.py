import pandas as pd, numpy as np, warnings, json
warnings.filterwarnings('ignore')
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler,OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
import lightgbm as lgb
P=Path('/mnt/data')
d=pd.read_csv(P/'v13_ltf_ml_dataset.csv',parse_dates=['event_ts','flip_time','rebreak_time','episode_start'])
d['atrv']=d.impulse/d.impulse_atr.replace(0,np.nan)
d['target_gain_atr']=((d.extreme-d.entry)*d.direction)/d.atrv
d['tp_or_flip_atr']=np.where(d.rebreak.eq(1),d.target_gain_atr,d.runner_pnl_atr)
d['tail_beyond_atr']=d.extension_impulse*d.impulse_atr
# Post-rebreak eventual H4-flip P/L from old extreme (for potential add-on at proof)
d['post_rebreak_flip_atr']=((d.exit_px-d.extreme)*d.direction)/d.atrv
cat=['reaction','family']
nums=['depth','depth_atr','impulse_atr','pullback_h','h4_run_age','prior_env','env_ratio','prior_success_n','env_available','env_breach',
      'poi_width_atr','poi_age_h','pen_wick','pen_close','rej_atr','acc_atr','m15_body_atr','m15_range_atr','m15_close_loc','m15_opp_wick_atr',
      'm15_tv_rel','m15_path_eff','m15_aligned_frac','m15_path_body_atr','depth_slope3','h1_align','h1_body_atr','h1_rng_atr','h4_ha_body_atr','h4_ha_rng_atr','h4_raw_close_vs_ha']
feats=nums+cat

def encode(train,test):
    z=pd.concat([train[feats],test[feats]],ignore_index=True)
    z=pd.get_dummies(z,columns=cat,dtype=float).replace([np.inf,-np.inf],np.nan)
    med=z.iloc[:len(train)].median(numeric_only=True); z=z.fillna(med).fillna(0)
    return z.iloc[:len(train)],z.iloc[len(train):]

def pmodel(train,test):
    pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('sc',RobustScaler(quantile_range=(10,90)))]),nums),('cat',OneHotEncoder(handle_unknown='ignore'),cat)])
    m=Pipeline([('pre',pre),('m',LogisticRegression(C=.5,max_iter=1500))]); m.fit(train[feats],train.rebreak)
    return m.predict_proba(test[feats])[:,1],m

pred=[]; metrics=[]
for y in [2023,2024,2025,2026]:
    tr=d[(d.year<y)&(d.flip_time<pd.Timestamp(f'{y}-01-01'))].copy(); te=d[d.year==y].copy()
    p,_=pmodel(tr,te); Xtr,Xte=encode(tr,te)
    # failure conditional expected pnl: only non-rebreak rows. Robust linear and shallow lgb, use ridge for stability.
    fail=tr[tr.rebreak==0]; Xf,_=encode(fail,te)
    ridge=Ridge(alpha=10.0); ridge.fit(Xf,fail.runner_pnl_atr.clip(fail.runner_pnl_atr.quantile(.01),fail.runner_pnl_atr.quantile(.99))); failpred=ridge.predict(Xte)
    # tail beyond old extreme, conditional on rebreak. log1p stabilizes long tail.
    suc=tr[tr.rebreak==1]; Xs,_=encode(suc,te)
    tail=lgb.LGBMRegressor(n_estimators=160,learning_rate=.03,num_leaves=7,max_depth=3,min_child_samples=35,reg_lambda=3,objective='huber',verbosity=-1,random_state=41)
    tail.fit(Xs,np.log1p(suc.tail_beyond_atr.clip(0,suc.tail_beyond_atr.quantile(.99))))
    tailpred=np.expm1(tail.predict(Xte)).clip(0)
    ev=p*te.target_gain_atr.values+(1-p)*failpred
    tailscore=p*tailpred
    z=te[['event_ts','year','h4_run_id','direction','reaction','family','rebreak','target_gain_atr','tp_or_flip_atr','runner_pnl_atr','remaining_mfe_atr','tail_beyond_atr','post_rebreak_flip_atr']].copy()
    z['p_rebreak']=p; z['pred_fail']=failpred; z['repair_ev']=ev; z['pred_tail_cond']=tailpred; z['tail_score']=tailscore
    pred.append(z)
    metrics.append({'year':y,'auc':roc_auc_score(te.rebreak,p),'repair_ev_spearman':spearmanr(ev,te.tp_or_flip_atr).statistic,
                    'tail_score_spearman_all':spearmanr(tailscore,te.tail_beyond_atr).statistic,
                    'tail_cond_spearman_success':spearmanr(tailpred[te.rebreak.values==1],te.loc[te.rebreak==1,'tail_beyond_atr']).statistic,
                    'n':len(te)})
pd.DataFrame(metrics).to_csv(P/'v13_ltf_hurdle_metrics.csv',index=False)
pred=pd.concat(pred,ignore_index=True); pred.to_csv(P/'v13_ltf_hurdle_oof.csv',index=False)
print(pd.DataFrame(metrics).to_string(index=False))
# diagnostic quintiles by each score
out=[]
for y,g in pred.groupby('year'):
 for sc in ['p_rebreak','repair_ev','tail_score']:
  q=pd.qcut(g[sc].rank(method='first'),5,labels=False)
  for k in range(5):
   z=g[q==k]
   out.append({'year':y,'score':sc,'q':k+1,'n':len(z),'rebreak':z.rebreak.mean(),'tpflip_mean':z.tp_or_flip_atr.mean(),'tpflip_med':z.tp_or_flip_atr.median(),
               'runner_mean':z.runner_pnl_atr.mean(),'tail_mean':z.tail_beyond_atr.mean(),'tail_med':z.tail_beyond_atr.median(),'mfe_mean':z.remaining_mfe_atr.mean(),
               'post_rebreak_flip_mean':z.loc[z.rebreak==1,'post_rebreak_flip_atr'].mean()})
r=pd.DataFrame(out); r.to_csv(P/'v13_ltf_hurdle_rank.csv',index=False)
print('\nTOP/BOTTOM QUINTILES')
print(r[r.q.isin([1,5])].to_string(index=False))
# causal policy thresholds: derive q50/q75 from prior-year OOF scores only; for 2024 use 2023 pseudo OOF by model trained 2022.
# Build score references for preceding years with one-step expanding model, same hurdle function simplified recursively.
def fit_predict(tr,te):
    p,_=pmodel(tr,te); Xtr,Xte=encode(tr,te)
    fail=tr[tr.rebreak==0]; Xf,_=encode(fail,te); ridge=Ridge(alpha=10.0); ridge.fit(Xf,fail.runner_pnl_atr.clip(fail.runner_pnl_atr.quantile(.01),fail.runner_pnl_atr.quantile(.99))); fp=ridge.predict(Xte)
    suc=tr[tr.rebreak==1]; Xs,_=encode(suc,te); tail=lgb.LGBMRegressor(n_estimators=160,learning_rate=.03,num_leaves=7,max_depth=3,min_child_samples=35,reg_lambda=3,objective='huber',verbosity=-1,random_state=41); tail.fit(Xs,np.log1p(suc.tail_beyond_atr.clip(0,suc.tail_beyond_atr.quantile(.99)))); tp=np.expm1(tail.predict(Xte)).clip(0)
    return pd.DataFrame({'repair_ev':p*te.target_gain_atr.values+(1-p)*fp,'tail_score':p*tp},index=te.index)
refs=[]
for yy in [2023,2024,2025]:
 tr=d[(d.year<yy)&(d.flip_time<pd.Timestamp(f'{yy}-01-01'))]; te=d[d.year==yy]
 if len(tr)>100 and len(te):
  s=fit_predict(tr,te); s['year']=yy; refs.append(s)
refs=pd.concat(refs)
pol=[]
for y in [2024,2025,2026]:
 g=pred[pred.year==y].copy(); prior=refs[refs.year<y]
 for sc in ['repair_ev','tail_score']:
  q50=prior[sc].quantile(.5); q75=prior[sc].quantile(.75)
  # 0/1/3 on structural TP-or-flip outcome
  w013=np.where(g[sc]>=q75,3,np.where(g[sc]>=q50,1,0))
  # 1/3 broad participation
  w13=np.where(g[sc]>=q75,3,1)
  for name,w in [('013',w013),('13',w13)]:
   pnl=g.tp_or_flip_atr.values*w
   pol.append({'year':y,'score':sc,'policy':name,'n_active':int((w>0).sum()),'units':int(w.sum()),'net_Rproxy':pnl.sum(),'mean_per_unit':pnl.sum()/w.sum() if w.sum() else np.nan,
               'base_1unit':g.tp_or_flip_atr.sum(),'top3_n':int((w==3).sum())})
policy=pd.DataFrame(pol); policy.to_csv(P/'v13_ltf_hurdle_policy.csv',index=False)
print('\nPOLICY')
print(policy.to_string(index=False))
