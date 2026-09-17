import json,time,warnings
from pathlib import Path
from bisect import bisect_left,bisect_right,insort
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_pinball_loss
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
warnings.filterwarnings('ignore')
SEED=261017; OUT=Path('/mnt/data/v10_ml_advanced_r4');OUT.mkdir(exist_ok=True)
df=pd.read_csv('/mnt/data/v10_ml_live/V10_LIVE_FULL_UNIVERSE_2022_2026.csv');df.decision=pd.to_datetime(df.decision);df['direction']=np.where(df.dir>0,'LONG','SHORT');df['stage']=np.where(df.k==1,'k1',np.where(df.k==2,'k2','k3p'));df=df.sort_values('decision').reset_index(drop=True);df['idx']=np.arange(len(df))
raw=['stop_dist_atr','fast_body_rng','fast_body_atr','std_align','std_body_rng','slow_align','slow_body_rng','adx28_rel','di14_signed','di28_signed','ema8_21_signed','ema8_slope','path_eff4_rel','path_eff12_rel','flip4','flip8','flip12','m15_aligned','m15_transition','m15_streak','m15_body_sum_atr','m15_body_eff','m15_body_rng','m15_opp_wick','m30_aligned','m30_transition','m30_streak','m30_body_sum_atr','m30_body_eff','m30_body_rng','m30_opp_wick','h1_aligned','h1_transition','h1_streak','h1_body_sum_atr','h1_body_eff','h1_body_rng','h1_opp_wick']
E=pd.DataFrame(index=df.index);E['log_stop']=np.log1p(df.stop_dist_atr.clip(lower=0));E['fast_body']=df.fast_body_rng;E['ha_align']=(df.std_align+df.slow_align)/2;E['ha_disagree']=(df.std_align!=df.slow_align).astype(float);E['ha_body_mean']=df[['fast_body_rng','std_body_rng','slow_body_rng']].mean(axis=1);E['ha_body_disp']=df[['fast_body_rng','std_body_rng','slow_body_rng']].std(axis=1).fillna(0);E['adx']=df.adx28_rel;E['di_mean']=df[['di14_signed','di28_signed']].mean(axis=1);E['di_disp']=(df.di14_signed-df.di28_signed).abs();E['ema']=df.ema8_21_signed;E['ema_slope']=df.ema8_slope;E['path_mean']=df[['path_eff4_rel','path_eff12_rel']].mean(axis=1);E['path_ratio']=df.path_eff4_rel/(df.path_eff12_rel.abs()+1e-6);E['flip_mean']=df[['flip4','flip8','flip12']].mean(axis=1);E['flip_accel']=df.flip4-df.flip12
for m,cc in {'align':['m15_aligned','m30_aligned','h1_aligned'],'transition':['m15_transition','m30_transition','h1_transition'],'streak':['m15_streak','m30_streak','h1_streak'],'body_sum':['m15_body_sum_atr','m30_body_sum_atr','h1_body_sum_atr'],'body_eff':['m15_body_eff','m30_body_eff','h1_body_eff'],'body_rng':['m15_body_rng','m30_body_rng','h1_body_rng'],'opp_wick':['m15_opp_wick','m30_opp_wick','h1_opp_wick']}.items():E[m+'_mean']=df[cc].mean(axis=1);E[m+'_disp']=df[cc].std(axis=1).fillna(0)
E['trend_flow']=E.adx*E.body_rng_mean;E['path_flow']=E.path_mean*E.body_rng_mean;E['dir_flow']=E.di_mean*E.body_rng_mean;E['ha_flow']=E.ha_body_mean*E.body_rng_mean
for c in E:df['e_'+c]=E[c]
eng=['e_'+c for c in E]
rankbase=['stop_dist_atr','fast_body_rng','std_body_rng','slow_body_rng','adx28_rel','di14_signed','ema8_21_signed','path_eff4_rel','path_eff12_rel','flip8','m15_body_rng','m30_body_rng','h1_body_rng']
def rankpast(v,w=360):
 v=np.asarray(v,float);o=np.full(len(v),.5);h=[]
 for i,x in enumerate(v):
  if len(h)>=40 and np.isfinite(x):o[i]=(bisect_right(h,float(x))+.5)/(len(h)+1)
  if np.isfinite(x):insort(h,float(x))
  j=i-w
  if j>=0 and np.isfinite(v[j]):
   k=bisect_left(h,float(v[j]));
   if k<len(h):h.pop(k)
 return o
for c in rankbase:
 col='rk_'+c
 for _,g in df.groupby(['stage','direction'],sort=False):df.loc[g.index,col]=rankpast(g[c].values)
ranks=['rk_'+c for c in rankbase];FS={'raw':raw,'eng':eng,'eng_rank':eng+ranks}

def mk(fam,p):
 p=dict(p)
 if fam=='lgb':p.update(verbosity=-1,n_jobs=2,random_state=SEED);return LGBMRegressor(**p)
 if fam=='xgb':p.update(objective='reg:squarederror',verbosity=0,n_jobs=2,random_state=SEED);return XGBRegressor(**p)
 p.update(loss_function='RMSE',verbose=False,thread_count=2,random_seed=SEED,allow_writing_files=False);return CatBoostRegressor(**p)
basep={'lgb':dict(n_estimators=120,num_leaves=15,max_depth=4,learning_rate=.04,min_child_samples=60,reg_lambda=10,reg_alpha=.5),'xgb':dict(n_estimators=120,max_depth=3,learning_rate=.04,min_child_weight=15,reg_lambda=15,reg_alpha=.5,subsample=.85,colsample_bytree=.85),'cat':dict(iterations=120,depth=5,learning_rate=.04,l2_leaf_reg=15,random_strength=.2)}
grids={'lgb':[dict(n_estimators=140,num_leaves=7,max_depth=3,learning_rate=.04,min_child_samples=50,reg_lambda=10,reg_alpha=.5),dict(n_estimators=200,num_leaves=15,max_depth=4,learning_rate=.03,min_child_samples=80,reg_lambda=20,reg_alpha=1)],'xgb':[dict(n_estimators=140,max_depth=2,learning_rate=.04,min_child_weight=15,reg_lambda=15,reg_alpha=.5,subsample=.9,colsample_bytree=.9),dict(n_estimators=200,max_depth=3,learning_rate=.03,min_child_weight=25,reg_lambda=25,reg_alpha=1,subsample=.85,colsample_bytree=.85)],'cat':[dict(iterations=160,depth=4,learning_rate=.04,l2_leaf_reg=15,random_strength=.2),dict(iterations=220,depth=5,learning_rate=.03,l2_leaf_reg=25,random_strength=.3)]}
def sub(g,yr,rec):
 tr=g[g.year<yr].copy();va=g[g.year==yr].copy();w=None
 if rec=='roll730':tr=tr[tr.decision>=pd.Timestamp(f'{yr}-01-01')-pd.Timedelta(days=730)]
 elif rec in ('exp365','exp730'):
  hl=int(rec[3:]);age=(pd.Timestamp(f'{yr}-01-01')-tr.decision).dt.total_seconds()/86400;w=np.power(.5,age/hl).values
 return tr,va,w
def pred(fam,p,ff,tr,va,w=None):
 m=mk(fam,p);m.fit(tr[ff].fillna(0),tr.R,sample_weight=w);return m,m.predict(va[ff].fillna(0))
def sp(y,p):return float(spearmanr(y,p).statistic)
def cv(g,fam,p,ff,rec='expanding'):
 ss=[];ll=[]
 for yr in [2023,2024]:
  tr,va,w=sub(g,yr,rec);_,q=pred(fam,p,ff,tr,va,w);ss.append(sp(va.R,q));t=np.quantile(q,.75);ll.append(va.loc[q>=t,'R'].mean()-va.R.mean())
 return np.mean(ss),np.mean(ll)
def importance(m):
 if hasattr(m,'booster_'):a=m.booster_.feature_importance(importance_type='gain')
 else:a=np.asarray(m.feature_importances_)
 a=np.asarray(a,float);return a/(a.sum()+1e-12)
search=[];selected=[];t0=time.time()
for st in ['k1','k2','k3p']:
 for d in ['LONG','SHORT']:
  g=df[(df.stage==st)&(df.direction==d)];A=[]
  for fs in ['raw','eng','eng_rank']:
   for fam in ['lgb','xgb','cat']:
    s,l=cv(g,fam,basep[fam],FS[fs]);A.append((s,l,fam,fs));search.append([st,d,'family_preproc',fam,fs,'expanding',s,l,json.dumps(basep[fam])])
  A.sort(key=lambda x:(-x[0],-x[1]));_,_,fam,fs=A[0];ff=FS[fs];B=[]
  for p in grids[fam]:
   s,l=cv(g,fam,p,ff);B.append((s,l,p));search.append([st,d,'hparam',fam,fs,'expanding',s,l,json.dumps(p)])
  B.sort(key=lambda x:(-x[0],-x[1]));_,_,p=B[0];C=[]
  for rec in ['expanding','roll730','exp365','exp730']:
   s,l=cv(g,fam,p,ff,rec);C.append((s,l,rec));search.append([st,d,'recency',fam,fs,rec,s,l,json.dumps(p)])
  C.sort(key=lambda x:(-x[0],-x[1]));_,_,rec=C[0]
  ii=[]
  for yr in [2023,2024]:tr,va,w=sub(g,yr,rec);m,q=pred(fam,p,ff,tr,va,w);ii.append(importance(m))
  order=np.argsort(-np.mean(ii,axis=0));ranked=[ff[i] for i in order];K=[]
  for k in sorted(set([8,16,min(24,len(ff)),len(ff)])):
   f2=ranked[:k];s,l=cv(g,fam,p,f2,rec);K.append((s,l,k,f2));search.append([st,d,'prune',fam,f'top{k}',rec,s,l,json.dumps(p)])
  best=max(x[0] for x in K);ok=[x for x in K if x[0]>=best-.005];ok.sort(key=lambda x:(x[2],-x[0]));s,l,k,f2=ok[0];selected.append(dict(stage=st,direction=d,family=fam,preprocess=fs,recency=rec,params=p,features=f2,tune=s,lift=l));print(st,d,fam,fs,rec,k,round(s,3),flush=True)
pd.DataFrame(search,columns=['stage','direction','phase','family','preprocess','recency','score','lift','params']).to_csv(OUT/'MODEL_SEARCH.csv',index=False);(OUT/'SELECTED.json').write_text(json.dumps(selected,indent=2))
# Quantile heads: use small LGBM config selected by 2023/24 pinball
qps=[dict(n_estimators=160,num_leaves=7,max_depth=3,learning_rate=.04,min_child_samples=50,reg_lambda=10),dict(n_estimators=220,num_leaves=15,max_depth=4,learning_rate=.03,min_child_samples=80,reg_lambda=20)]
def qp(p,a,ff,tr,va,w=None):
 z=dict(p);z.update(objective='quantile',alpha=a,verbosity=-1,n_jobs=2,random_state=SEED);m=LGBMRegressor(**z);m.fit(tr[ff].fillna(0),tr.R,sample_weight=w);return m.predict(va[ff].fillna(0))
oos=[];qm=[]
for s in selected:
 g=df[(df.stage==s['stage'])&(df.direction==s['direction'])];Q=[]
 for p in qps:
  loss=[]
  for yr in [2023,2024]:
   tr,va,w=sub(g,yr,s['recency']);scale=max(np.median(np.abs(tr.R-np.median(tr.R))),.1)
   for a in [.1,.5,.9]:loss.append(mean_pinball_loss(va.R,qp(p,a,s['features'],tr,va,w),alpha=a)/scale)
  Q.append((np.mean(loss),p))
 Q.sort(key=lambda x:x[0]);qpar=Q[0][1]
 for yr in [2024,2025,2026]:
  tr,va,w=sub(g,yr,s['recency']);_,mu=pred(s['family'],s['params'],s['features'],tr,va,w);qs={a:qp(qpar,a,s['features'],tr,va,w) for a in [.1,.5,.9]}
  for j,i in enumerate(va.index):oos.append([i,yr,s['stage'],s['direction'],mu[j],qs[.1][j],qs[.5][j],qs[.9][j],va.loc[i,'R'],va.loc[i,'pnl'],va.loc[i,'rid'],va.loc[i,'L'],va.loc[i,'decision']])
  for a in [.1,.5,.9]:qm.append([s['stage'],s['direction'],yr,a,np.mean(va.R.values<=qs[a]),mean_pinball_loss(va.R,qs[a],alpha=a),len(va)])
oos=pd.DataFrame(oos,columns=['idx','year','stage','direction','mean','q10','q50','q90','R','pnl','rid','L','decision']);oos.to_csv(OUT/'OOS_DISTRIBUTIONS.csv',index=False);pd.DataFrame(qm,columns=['stage','direction','year','alpha','coverage','pinball','n']).to_csv(OUT/'QUANTILE_METRICS.csv',index=False)
# choose mean/q10/q50/q90 ranking from 2024 OOS only
choices=[]
for st in ['k1','k2','k3p']:
 for d in ['LONG','SHORT']:
  z=oos[(oos.stage==st)&(oos.direction==d)&(oos.year==2024)];A=[]
  for c in ['mean','q10','q50','q90']:
   r=sp(z.R,z[c]);t=np.quantile(z[c],.75);lift=z.loc[z[c]>=t,'R'].mean()-z.R.mean();A.append((r,lift,c))
  A.sort(key=lambda x:(-x[0],-x[1]));choices.append([st,d,A[0][2],A[0][0],A[0][1]])
ch=pd.DataFrame(choices,columns=['stage','direction','source','spearman2024','lift2024']);ch.to_csv(OUT/'SCORE_SOURCE.csv',index=False);cm={(r.stage,r.direction):r.source for _,r in ch.iterrows()}
# stage-dir, prior-year OOS percentile mapping
rows=[]
for yr in [2025,2026]:
 for st in ['k1','k2','k3p']:
  for d in ['LONG','SHORT']:
   src=cm[(st,d)];pr=oos[(oos.year==yr-1)&(oos.stage==st)&(oos.direction==d)];cu=oos[(oos.year==yr)&(oos.stage==st)&(oos.direction==d)];a,b=np.quantile(pr[src],[.5,.75])
   for _,r in cu.iterrows():w=0 if r[src]<a else (1 if r[src]<b else 3);rows.append({**r.to_dict(),'source':src,'score':r[src],'q50_prior':a,'q75_prior':b,'w':w})
pol=pd.DataFrame(rows).sort_values('decision');pol.to_csv(OUT/'POLICY_LEDGER.csv',index=False)
def met(z):
 z=z[z.w>0];wp=z.pnl*z.w;wr=z.R*z.w;gp=wp[wp>0].sum();gl=-wp[wp<0].sum();cum=wr.cumsum();return dict(events=len(z),units=z.w.sum(),pnl=wp.sum(),R=wr.sum(),pf=gp/gl if gl else np.inf,wr=(wp>0).mean(),ddR=(cum.cummax()-cum).max())
S=[]
for n,z in [('ALL',pol),('2025',pol[pol.year==2025]),('2026',pol[pol.year==2026]),('LONG',pol[pol.direction=='LONG']),('SHORT',pol[pol.direction=='SHORT']),('k1',pol[pol.stage=='k1']),('k2',pol[pol.stage=='k2']),('k3p',pol[pol.stage=='k3p'])]:S.append({'scope':n,**met(z)})
su=pd.DataFrame(S);su.to_csv(OUT/'POLICY_SUMMARY.csv',index=False)
# run buckets, concentration
se=pol[pol.w>0].copy();se['wp']=se.pnl*se.w;se['wR']=se.R*se.w;se['bucket']=pd.cut(se.L,[0,2,5,8,11,999],labels=['L1-2','L3-5','L6-8','L9-11','L12+']);pd.DataFrame([{'bucket':str(b),**met(g)} for b,g in se.groupby('bucket',observed=True)]).to_csv(OUT/'RUN_BUCKETS.csv',index=False);runs=se.groupby(['year','rid'],as_index=False).agg(pnl=('wp','sum'),R=('wR','sum'));pos=runs[runs.pnl>0].sort_values('pnl',ascending=False);tot=se.wp.sum();pd.DataFrame([{'top_n':n,'pnl':pos.head(n).pnl.sum(),'share':pos.head(n).pnl.sum()/tot} for n in [1,5,10]]).to_csv(OUT/'RIGHT_TAIL.csv',index=False)
# final OOS mean metrics
M=[]
for s in selected:
 for yr in [2025,2026]:
  z=oos[(oos.stage==s['stage'])&(oos.direction==s['direction'])&(oos.year==yr)];M.append([s['stage'],s['direction'],yr,sp(z.R,z['mean']),s['family'],s['preprocess'],s['recency'],len(s['features'])])
pd.DataFrame(M,columns=['stage','direction','year','spearman','family','preprocess','recency','nfeat']).to_csv(OUT/'OOS_METRICS.csv',index=False)
md=['# V10 Advanced ML R4',f'Runtime: {time.time()-t0:.1f}s','', 'All model-family/preprocessing/hyperparameter/recency/feature-count choices were selected only on 2023-2024 walk-forward validation. 2025-2026 are sequential OOS.','', '## Policy',su.to_markdown(index=False),'','## Ranking source selected from 2024 OOS',ch.to_markdown(index=False),'','## Experts']+[f"- {x['stage']} {x['direction']}: {x['family']} / {x['preprocess']} / {x['recency']} / {len(x['features'])} features / tune rho {x['tune']:.3f}" for x in selected]
(OUT/'SUMMARY.md').write_text('\n'.join(md))
print('\nDONE',round(time.time()-t0,1));print(su.to_string(index=False));print('\nSOURCES\n',ch.to_string(index=False))
