import pandas as pd, numpy as np, warnings
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
# load M1
m=pd.read_csv(P/'GOLD#_M1_202201030100_202608282357(5).csv',sep='\t',usecols=['<DATE>','<TIME>','<OPEN>','<HIGH>','<LOW>','<CLOSE>'])
m['ts']=pd.to_datetime(m['<DATE>']+' '+m['<TIME>'],format='%Y.%m.%d %H:%M:%S'); m=m.rename(columns={'<OPEN>':'open','<HIGH>':'high','<LOW>':'low','<CLOSE>':'close'})
ts=m.ts.values.astype('datetime64[ns]'); o=m.open.values; h=m.high.values; l=m.low.values
outs=[]
for i,r in d.iterrows():
    direction=int(r.direction); imp=float(r.impulse); extreme=float(r.extreme); pull_ext=extreme-direction*float(r.depth)*imp
    j=np.searchsorted(ts,np.datetime64(r.event_ts),side='left'); k=np.searchsorted(ts,np.datetime64(r.flip_time),side='left')
    if j>=len(m) or k<=j: continue
    entry=float(o[j]); risk=(entry-pull_ext)*direction; reward=(extreme-entry)*direction
    if risk<=1e-8 or reward<=1e-8: continue
    outcome=None; exitp=None; exit_ts=None; amb=0
    for q in range(j,k):
        if direction==1:
            st=(l[q]<=pull_ext); tg=(h[q]>extreme)
        else:
            st=(h[q]>=pull_ext); tg=(l[q]<extreme)
        if st and tg:
            amb=1; outcome='STOP'; exitp=float(o[q]) if ((direction==1 and o[q]<pull_ext) or (direction==-1 and o[q]>pull_ext)) else pull_ext; exit_ts=pd.Timestamp(ts[q]); break
        if st:
            outcome='STOP'; exitp=float(o[q]) if ((direction==1 and o[q]<pull_ext) or (direction==-1 and o[q]>pull_ext)) else pull_ext; exit_ts=pd.Timestamp(ts[q]); break
        if tg:
            outcome='TARGET'; exitp=float(o[q]) if ((direction==1 and o[q]>extreme) or (direction==-1 and o[q]<extreme)) else extreme; exit_ts=pd.Timestamp(ts[q]); break
    if outcome is None:
        outcome='FLIP'; exitp=float(o[k]) if k<len(m) else float(m.close.iloc[-1]); exit_ts=pd.Timestamp(ts[k]) if k<len(m) else pd.Timestamp(r.flip_time)
    rr=(exitp-entry)*direction/risk
    outs.append({'idx':i,'m1_entry':entry,'stop':pull_ext,'target':extreme,'risk':risk,'target_R':reward/risk,'outcome':outcome,'R':rr,'amb':amb,'exit_ts_m1':exit_ts})
o=pd.DataFrame(outs).set_index('idx'); d=d.join(o,how='inner')
d.to_csv(P/'v13_ltf_structural_r_dataset.csv',index=False)
print('N',len(d)); print(d.groupby(['year','outcome']).size().unstack(fill_value=0));
for y,g in d.groupby('year'):
    print(y,'N',len(g),'R',g.R.sum(),'mean',g.R.mean(),'PF',g.loc[g.R>0,'R'].sum()/(-g.loc[g.R<0,'R'].sum()),'target', (g.outcome=='TARGET').mean(),'amb',g.amb.sum())
# features
cat=['reaction','family']; nums=['depth','depth_atr','impulse_atr','pullback_h','h4_run_age','prior_env','env_ratio','prior_success_n','env_available','env_breach','poi_width_atr','poi_age_h','pen_wick','pen_close','rej_atr','acc_atr','m15_body_atr','m15_range_atr','m15_close_loc','m15_opp_wick_atr','m15_tv_rel','m15_path_eff','m15_aligned_frac','m15_path_body_atr','depth_slope3','h1_align','h1_body_atr','h1_rng_atr','h4_ha_body_atr','h4_ha_rng_atr','h4_raw_close_vs_ha','target_R']
feats=nums+cat
pred=[]
for y in [2023,2024,2025,2026]:
 tr=d[(d.year<y)&(d.flip_time<pd.Timestamp(f'{y}-01-01'))].copy(); te=d[d.year==y].copy()
 # target-before-stop classifier; FLIP treated no-target
 pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('sc',RobustScaler(quantile_range=(10,90)))]),nums),('cat',OneHotEncoder(handle_unknown='ignore'),cat)])
 mdl=Pipeline([('pre',pre),('m',LogisticRegression(C=.5,max_iter=1500))]); yt=(tr.outcome=='TARGET').astype(int); yte=(te.outcome=='TARGET').astype(int); mdl.fit(tr[feats],yt); p=mdl.predict_proba(te[feats])[:,1]
 # direct R rank model shallow lgb
 z=pd.concat([tr[feats],te[feats]],ignore_index=True); z=pd.get_dummies(z,columns=cat,dtype=float).replace([np.inf,-np.inf],np.nan); z=z.fillna(z.iloc[:len(tr)].median(numeric_only=True)).fillna(0); Xtr=z.iloc[:len(tr)]; Xte=z.iloc[len(tr):]
 reg=lgb.LGBMRegressor(n_estimators=180,learning_rate=.03,num_leaves=7,max_depth=3,min_child_samples=40,reg_lambda=3,objective='huber',verbosity=-1,random_state=55); reg.fit(Xtr,tr.R.clip(tr.R.quantile(.01),tr.R.quantile(.99))); pr=reg.predict(Xte)
 q=te[['event_ts','year','h4_run_id','reaction','family','outcome','R','target_R','risk','impulse','impulse_atr','runner_pnl_atr','remaining_mfe_atr','extension_impulse']].copy(); q['p_target']=p; q['pred_R']=pr; q['pnl_atr_struct']=q.R*q.risk/(q.impulse/q.impulse_atr); pred.append(q)
 print('MODEL',y,'AUC target',roc_auc_score(yte,p),'R spearman',spearmanr(pr,te.R).statistic)
pred=pd.concat(pred); pred.to_csv(P/'v13_ltf_structural_r_oof.csv',index=False)
for y,g in pred.groupby('year'):
 print('\nYEAR',y)
 for sc in ['p_target','pred_R']:
  q=pd.qcut(g[sc].rank(method='first'),5,labels=False)
  for k in [0,4]:
   z=g[q==k]; pf=z.loc[z.R>0,'R'].sum()/(-z.loc[z.R<0,'R'].sum()) if (z.R<0).any() else np.inf
   print(sc,'Q',k+1,'N',len(z),'target',(z.outcome=='TARGET').mean(),'meanR',z.R.mean(),'PF',pf,'mfe',z.remaining_mfe_atr.mean())
