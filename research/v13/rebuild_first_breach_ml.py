import pandas as pd, numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler,OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score,brier_score_loss
from scipy.stats import spearmanr

D=pd.read_csv('/mnt/data/v13_ltf_ml_dataset.csv',parse_dates=['event_ts','flip_time','rebreak_time'])
# Cluster same interaction time into one actual opportunity.
key=['event_ts','h4_run_id','direction']
# market state aggregate; object-specific reaction features aggregate in causal ways
reaction_rank={'REJECT':0,'INSIDE':1,'ACCEPT':2}
D['reaction_rank']=D.reaction.map(reaction_rank)
D['has_fvg']=(D.family=='FVG').astype(int);D['has_ob']=(D.family=='OB').astype(int)
D['is_reject']=(D.reaction=='REJECT').astype(int);D['is_inside']=(D.reaction=='INSIDE').astype(int);D['is_accept']=(D.reaction=='ACCEPT').astype(int)
# Most market/path variables can differ if multiple M30 episodes point to same interaction; aggregate min/mean/max to preserve full known state.
base_first=['year','entry','exit_px','flip_time']
mean_cols=['depth','depth_atr','impulse_atr','pullback_h','h4_run_age','prior_env','env_ratio','prior_success_n','env_available','env_breach',
           'm15_tv_rel','m15_path_eff','m15_aligned_frac','m15_path_body_atr','depth_slope3','h1_align','h1_body_atr','h1_rng_atr','h4_ha_body_atr','h4_ha_rng_atr','h4_raw_close_vs_ha']
obj_mean=['poi_width_atr','poi_age_h','pen_wick','pen_close','rej_atr','acc_atr','m15_body_atr','m15_range_atr','m15_close_loc','m15_opp_wick_atr']
agg={c:'first' for c in base_first}
for c in mean_cols: agg[c]='mean'
for c in obj_mean: agg[c]='mean'
agg.update({'has_fvg':'max','has_ob':'max','is_reject':'max','is_inside':'max','is_accept':'max','reaction_rank':'max','family':'size'})
C=D.groupby(key,as_index=False).agg(agg).rename(columns={'family':'object_n'})
# for breach state at an event, any underlying episode breach counts; override mean with max
mx=D.groupby(key,as_index=False).agg(env_breach_any=('env_breach','max'),env_ratio_max=('env_ratio','max'),depth_max=('depth','max'),depth_atr_max=('depth_atr','max'))
C=C.merge(mx,on=key,how='left')
# Need known H4 ATR at entry: infer from any source row impulse/impulse_atr, cluster median
D['atr']=D.impulse/D.impulse_atr
atr=D.groupby(key,as_index=False).atr.median()
C=C.merge(atr,on=key,how='left')

# First FUTURE cluster in same run with any env_breach. Exit at breach-cluster entry (next M15 open), else H4 flip exit price.
C=C.sort_values(['h4_run_id','event_ts']).reset_index(drop=True)
exit_time=[];exit_px=[];reason=[]
for rid,g in C.groupby('h4_run_id',sort=False):
    idx=g.index.to_numpy(); times=g.event_ts.to_numpy(); breach=g.env_breach_any.to_numpy().astype(bool)
    for pos,ix in enumerate(idx):
        later=np.flatnonzero(breach[pos+1:])
        if len(later):
            j=pos+1+int(later[0]); jx=idx[j]
            exit_time.append((ix,pd.Timestamp(C.at[jx,'event_ts']),float(C.at[jx,'entry']),'ENV_BREACH'))
        else:
            exit_time.append((ix,pd.Timestamp(C.at[ix,'flip_time']),float(C.at[ix,'exit_px']),'H4_FLIP'))
# assign
emap={ix:(t,p,r) for ix,t,p,r in exit_time}
C['exit_time_fb']=[emap[i][0] for i in C.index]; C['exit_px_fb']=[emap[i][1] for i in C.index]; C['exit_reason_fb']=[emap[i][2] for i in C.index]
C['pnl_usd_1u_fb']=C.direction*(C.exit_px_fb-C.entry)
C['pnl_atr_fb']=C.pnl_usd_1u_fb/C.atr
C['positive_fb']=(C.pnl_atr_fb>0).astype(int)
print('clusters',len(C),C.year.value_counts().sort_index().to_dict())
for y,g in C[C.year>=2024].groupby('year'):
    v=g.pnl_usd_1u_fb.values; w=v[v>0];l=v[v<0]
    print('BASE',y,len(v),'net$',v.sum(),'PF',w.sum()/-l.sum(),'WR',(v>0).sum()/(v!=0).sum(),'avgW',w.mean(),'avgL',l.mean(),'meanATR',g.pnl_atr_fb.mean(),'exit',g.exit_reason_fb.value_counts().to_dict())

# ML feature packet
cat=[] # use binary cluster reaction/family representation; avoids object category ambiguity
nums=['depth','depth_atr','depth_max','depth_atr_max','impulse_atr','pullback_h','h4_run_age','prior_env','env_ratio','env_ratio_max','prior_success_n','env_available','env_breach','env_breach_any',
      'poi_width_atr','poi_age_h','pen_wick','pen_close','rej_atr','acc_atr','m15_body_atr','m15_range_atr','m15_close_loc','m15_opp_wick_atr',
      'm15_tv_rel','m15_path_eff','m15_aligned_frac','m15_path_body_atr','depth_slope3','h1_align','h1_body_atr','h1_rng_atr','h4_ha_body_atr','h4_ha_rng_atr','h4_raw_close_vs_ha',
      'has_fvg','has_ob','is_reject','is_inside','is_accept','object_n']
pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('sc',RobustScaler(quantile_range=(10,90)))]),nums)])
# Generate outer OOF 2023-26; labels must resolve before test-year boundary for train.
preds=[]; mets=[]
for y in [2023,2024,2025,2026]:
    train=C[(C.year<y)&(C.exit_time_fb<pd.Timestamp(f'{y}-01-01'))].copy(); test=C[C.year==y].copy()
    if len(train)<100: continue
    # p positive
    clf=Pipeline([('pre',pre),('m',LogisticRegression(C=.5,max_iter=2000))]); clf.fit(train[nums],train.positive_fb); p=clf.predict_proba(test[nums])[:,1]
    # direct robust-ish linear expected ATR pnl
    reg=Pipeline([('pre',pre),('m',Ridge(alpha=10.0))]); reg.fit(train[nums],train.pnl_atr_fb); pred_lin=reg.predict(test[nums])
    # nonlinear fixed shallow hist gradient boosting; median impute separately encoded by same pre produces sparse? use custom numeric impute only no scaling
    Xtr=train[nums].replace([np.inf,-np.inf],np.nan); Xte=test[nums].replace([np.inf,-np.inf],np.nan)
    med=Xtr.median(); Xtr=Xtr.fillna(med);Xte=Xte.fillna(med)
    h=HistGradientBoostingRegressor(max_iter=150,learning_rate=.04,max_leaf_nodes=15,min_samples_leaf=40,l2_regularization=2.0,loss='squared_error',random_state=13)
    h.fit(Xtr,train.pnl_atr_fb); pred_h=h.predict(Xte)
    # hurdle: logistic p + conditional linear magnitude heads (positive / loss) using Ridge
    pos=train[train.pnl_atr_fb>0]; neg=train[train.pnl_atr_fb<0]
    rpos=Pipeline([('pre',pre),('m',Ridge(alpha=10.0))]); rneg=Pipeline([('pre',pre),('m',Ridge(alpha=10.0))])
    rpos.fit(pos[nums],pos.pnl_atr_fb); rneg.fit(neg[nums],-neg.pnl_atr_fb)
    pw=np.clip(rpos.predict(test[nums]),0,None); pl=np.clip(rneg.predict(test[nums]),0,None)
    ev=p*pw-(1-p)*pl
    for model,pr in [('PWIN',p),('RIDGE',pred_lin),('HGB',pred_h),('HURDLE_EV',ev)]:
        if model=='PWIN': sp=spearmanr(pr,test.pnl_atr_fb).statistic
        else: sp=spearmanr(pr,test.pnl_atr_fb).statistic
        mets.append((y,model,len(test),roc_auc_score(test.positive_fb,p) if model=='PWIN' else np.nan,sp))
    z=test[['event_ts','h4_run_id','direction','year','entry','exit_time_fb','pnl_usd_1u_fb','pnl_atr_fb','positive_fb','atr']].copy()
    z['pwin']=p;z['ridge']=pred_lin;z['hgb']=pred_h;z['hurdle_ev']=ev
    preds.append(z)
P=pd.concat(preds,ignore_index=True)
print('\nMETRICS')
for m in mets: print(m)
# Sizing based solely on strictly prior OOF score quantiles. Compare all base 1u + upgrades q75, and 1/2/3.
for score in ['pwin','ridge','hgb','hurdle_ev']:
  print('\nSCORE',score)
  for pol in ['1_1_2','1_1_3','1_2_3','0_1_3']:
    allparts=[]
    for y in [2024,2025,2026]:
        tr=P[P.year<y][score].dropna().values; te=P[P.year==y].copy(); q50,q75=np.quantile(tr,[.5,.75]); s=te[score]
        if pol=='1_1_2': te['u']=np.where(s>=q75,2,1)
        elif pol=='1_1_3': te['u']=np.where(s>=q75,3,1)
        elif pol=='1_2_3': te['u']=np.where(s>=q75,3,np.where(s>=q50,2,1))
        else: te['u']=np.where(s>=q75,3,np.where(s>=q50,1,0))
        te['profit']=te.pnl_usd_1u_fb*te.u; allparts.append(te)
    Z=pd.concat(allparts); v=Z.profit.values; w=v[v>0];l=v[v<0]
    # realized DD exit order
    zz=Z.sort_values(['exit_time_fb','event_ts']); eq=zz.profit.cumsum().values; peak=np.maximum.accumulate(np.r_[0.,eq]);dd=(peak[1:]-eq).max()
    print(pol,'all n',len(Z),'active',(Z.u>0).sum(),'units',Z.u.sum(),'net',v.sum(),'PF',w.sum()/-l.sum(),'DD',dd)
    for y,g in Z.groupby('year'):
       v=g.profit.values;w=v[v>0];l=v[v<0]
       print(' ',y,'n',len(g),'active',(g.u>0).sum(),'units',g.u.sum(),'net',v.sum(),'PF',w.sum()/-l.sum(),'WR',(v>0).sum()/max(1,(v!=0).sum()))

C.to_csv('/mnt/data/v13_ltf_first_breach_clusters.csv',index=False)
P.to_csv('/mnt/data/v13_ltf_first_breach_ml_oof.csv',index=False)
