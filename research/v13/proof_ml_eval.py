import pandas as pd, numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
S=pd.read_csv('/mnt/data/v13_ltf_staged_proof.csv',parse_dates=['event_ts','exit_time_fb','rebreak_time','proof_add_time','flip_time'])
D=pd.read_csv('/mnt/data/v13_ltf_ml_dataset.csv',parse_dates=['event_ts','rebreak_time'])
key=['event_ts','h4_run_id','direction']
# target extreme tied to earliest rebreak per cluster
refs=[]
for k,g in D.groupby(key):
    q=g[g.rebreak_time.notna()].sort_values('rebreak_time')
    if len(q):
        r=q.iloc[0];refs.append((*k,r.rebreak_time,float(r.extreme)))
REF=pd.DataFrame(refs,columns=key+['ref_rebreak_time','ref_extreme'])
S=S.merge(REF,on=key,how='left')
# M15 proof bar context
m=pd.read_csv('/mnt/data/GOLD#_M15_202201030100_202608282345.csv',sep='\t');m['ts']=pd.to_datetime(m['<DATE>']+' '+m['<TIME>'],format='%Y.%m.%d %H:%M:%S');m=m.sort_values('ts').reset_index(drop=True);m['tv_med96']=m['<TICKVOL>'].rolling(96,min_periods=24).median();idx={t:i for i,t in enumerate(m.ts)}
vals=[]
for r in S.itertuples():
    if not r.proof_before_exit or pd.isna(r.proof_add_time): vals.append((np.nan,)*5);continue
    t=pd.Timestamp(r.proof_add_time)-pd.Timedelta(minutes=15); i=idx.get(t)
    if i is None: vals.append((np.nan,)*5);continue
    b=m.iloc[i];rng=max(float(b['<HIGH>'])-float(b['<LOW>']),1e-9);body=(float(b['<CLOSE>'])-float(b['<OPEN>']))*int(r.direction);cl=((float(b['<CLOSE>'])-float(b['<LOW>']))/rng if r.direction==1 else (float(b['<HIGH>'])-float(b['<CLOSE>']))/rng);tv=float(b['<TICKVOL>'])/float(b.tv_med96) if pd.notna(b.tv_med96) and b.tv_med96 else np.nan;over=(float(b['<CLOSE>'])-float(r.ref_extreme))*int(r.direction)/float(r.atr) if pd.notna(r.ref_extreme) else np.nan
    vals.append((body/float(r.atr),rng/float(r.atr),cl,tv,over))
S[['proof_body_atr','proof_range_atr','proof_close_loc','proof_tv_rel','proof_overshoot_atr']]=vals
S['proof_gain_atr']=S.direction*(S.proof_add_entry-S.entry)/S.atr
S['proof_positive']=(S.proof_add_pnl_atr>0).astype(int)
P0=S[S.proof_before_exit].copy()
nums=['depth','depth_atr','depth_max','depth_atr_max','impulse_atr','pullback_h','h4_run_age','prior_env','env_ratio','env_ratio_max','prior_success_n','env_available','env_breach','env_breach_any','poi_width_atr','poi_age_h','pen_wick','pen_close','rej_atr','acc_atr','m15_body_atr','m15_range_atr','m15_close_loc','m15_opp_wick_atr','m15_tv_rel','m15_path_eff','m15_aligned_frac','m15_path_body_atr','depth_slope3','h1_align','h1_body_atr','h1_rng_atr','h4_ha_body_atr','h4_ha_rng_atr','h4_raw_close_vs_ha','has_fvg','has_ob','is_reject','is_inside','is_accept','object_n','proof_latency_h','proof_gain_atr','proof_body_atr','proof_range_atr','proof_close_loc','proof_tv_rel','proof_overshoot_atr']
pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('sc',RobustScaler(quantile_range=(10,90)))]),nums)])
preds=[]
for y in [2023,2024,2025,2026]:
    tr=P0[(P0.year<y)&(P0.exit_time_fb<pd.Timestamp(f'{y}-01-01'))].copy();te=P0[P0.year==y].copy()
    if len(tr)<100: continue
    clf=Pipeline([('pre',pre),('m',LogisticRegression(C=.5,max_iter=2000))]);clf.fit(tr[nums],tr.proof_positive);p=clf.predict_proba(te[nums])[:,1]
    # HGB expected normalized add pnl
    Xtr=tr[nums].replace([np.inf,-np.inf],np.nan);Xte=te[nums].replace([np.inf,-np.inf],np.nan);med=Xtr.median();Xtr=Xtr.fillna(med);Xte=Xte.fillna(med)
    h=HistGradientBoostingRegressor(max_iter=150,learning_rate=.04,max_leaf_nodes=15,min_samples_leaf=30,l2_regularization=2.0,random_state=13);h.fit(Xtr,tr.proof_add_pnl_atr);ph=h.predict(Xte)
    rr=Pipeline([('pre',pre),('m',Ridge(alpha=10))]);rr.fit(tr[nums],tr.proof_add_pnl_atr);pr=rr.predict(te[nums])
    print('YEAR',y,'n',len(te),'auc',roc_auc_score(te.proof_positive,p),'sp_p',spearmanr(p,te.proof_add_pnl_atr).statistic,'sp_hgb',spearmanr(ph,te.proof_add_pnl_atr).statistic,'sp_ridge',spearmanr(pr,te.proof_add_pnl_atr).statistic)
    z=te[key+['year','proof_add_pnl_1u','proof_add_pnl_atr','proof_add_time','exit_time_fb']].copy();z['pwin_proof']=p;z['hgb_proof']=ph;z['ridge_proof']=pr;preds.append(z)
P=pd.concat(preds,ignore_index=True)
# Evaluate staged baseline K1: base unit + 1 proof unit, and ML extra +1/+2 on prior q75 proof score.
base=S[S.year>=2024].copy()
for score in ['pwin_proof','hgb_proof','ridge_proof']:
    M=base.merge(P[key+[score]],on=key,how='left')
    for extra in [1,2]:
      M['extra_units']=0
      for y in [2024,2025,2026]:
        prior=P[P.year<y][score].dropna().values;q=np.quantile(prior,.75);mask=(M.year==y)&M.proof_before_exit&(M[score]>=q);M.loc[mask,'extra_units']=extra
      M['profit']=M.pnl_usd_1u_fb+M.proof_add_pnl_1u+M.extra_units*M.proof_add_pnl_1u
      z=M.sort_values(['exit_time_fb','event_ts']);v=z.profit.values;w=v[v>0];l=v[v<0];eq=np.cumsum(v);pk=np.maximum.accumulate(np.r_[0,eq]);dd=(pk[1:]-eq).max()
      print('\nPOL',score,'extra',extra,'net',v.sum(),'PF',w.sum()/-l.sum(),'DD',dd,'upgrades',(M.extra_units>0).sum())
      for y,g in M.groupby('year'):
        v=g.profit.values;w=v[v>0];l=v[v<0];print(y,'net',v.sum(),'PF',w.sum()/-l.sum(),'up',(g.extra_units>0).sum())
      # random selection sanity within proofed candidates same upgrade counts per year
      rng=np.random.default_rng(27);obs_inc=float((M.extra_units*M.proof_add_pnl_1u).sum());draw=[]
      for _ in range(5000):
        inc=0
        for y,g in M[M.proof_before_exit].groupby('year'):
          n=int((g.extra_units>0).sum()); vals=g.proof_add_pnl_1u.values
          if n: inc += extra*rng.choice(vals,n,replace=False).sum()
        draw.append(inc)
      draw=np.array(draw);print('increment',obs_inc,'random mean',draw.mean(),'p>=obs',np.mean(draw>=obs_inc),'95',np.quantile(draw,[.025,.975]))
P.to_csv('/mnt/data/v13_ltf_proof_ml_oof.csv',index=False);S.to_csv('/mnt/data/v13_ltf_proof_features.csv',index=False)
