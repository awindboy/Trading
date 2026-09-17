import sys,json,time,warnings
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_pinball_loss
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
warnings.filterwarnings('ignore')
SEED=261017; OUT=Path('/mnt/data/v10_ml_advanced_r4');
stage=sys.argv[1]; direction=sys.argv[2]
df=pd.read_pickle(OUT/'ENRICHED.pkl'); FS=json.loads((OUT/'FEATURES.json').read_text()); g=df[(df.stage==stage)&(df.direction==direction)].copy()

def mk(fam,p):
 p=dict(p)
 if fam=='lgb':p.update(verbosity=-1,n_jobs=2,random_state=SEED);return LGBMRegressor(**p)
 if fam=='xgb':p.update(objective='reg:squarederror',verbosity=0,n_jobs=2,random_state=SEED);return XGBRegressor(**p)
 p.update(loss_function='RMSE',verbose=False,thread_count=2,random_seed=SEED,allow_writing_files=False);return CatBoostRegressor(**p)
basep={'lgb':dict(n_estimators=120,num_leaves=15,max_depth=4,learning_rate=.04,min_child_samples=60,reg_lambda=10,reg_alpha=.5),'xgb':dict(n_estimators=120,max_depth=3,learning_rate=.04,min_child_weight=15,reg_lambda=15,reg_alpha=.5,subsample=.85,colsample_bytree=.85),'cat':dict(iterations=120,depth=5,learning_rate=.04,l2_leaf_reg=15,random_strength=.2)}
grids={'lgb':[dict(n_estimators=140,num_leaves=7,max_depth=3,learning_rate=.04,min_child_samples=50,reg_lambda=10,reg_alpha=.5),dict(n_estimators=200,num_leaves=15,max_depth=4,learning_rate=.03,min_child_samples=80,reg_lambda=20,reg_alpha=1)],'xgb':[dict(n_estimators=140,max_depth=2,learning_rate=.04,min_child_weight=15,reg_lambda=15,reg_alpha=.5,subsample=.9,colsample_bytree=.9),dict(n_estimators=200,max_depth=3,learning_rate=.03,min_child_weight=25,reg_lambda=25,reg_alpha=1,subsample=.85,colsample_bytree=.85)],'cat':[dict(iterations=160,depth=4,learning_rate=.04,l2_leaf_reg=15,random_strength=.2),dict(iterations=220,depth=5,learning_rate=.03,l2_leaf_reg=25,random_strength=.3)]}
def sub(yr,rec):
 tr=g[g.year<yr].copy();va=g[g.year==yr].copy();w=None
 if rec=='roll730':tr=tr[tr.decision>=pd.Timestamp(f'{yr}-01-01')-pd.Timedelta(days=730)]
 elif rec in ('exp365','exp730'):
  hl=int(rec[3:]);age=(pd.Timestamp(f'{yr}-01-01')-tr.decision).dt.total_seconds()/86400;w=np.power(.5,age/hl).values
 return tr,va,w
def pred(fam,p,ff,tr,va,w=None):
 m=mk(fam,p);m.fit(tr[ff].fillna(0),tr.R,sample_weight=w);return m,m.predict(va[ff].fillna(0))
def sp(y,p):return float(spearmanr(y,p).statistic)
def cv(fam,p,ff,rec='expanding'):
 ss=[];ll=[]
 for yr in [2023,2024]:
  tr,va,w=sub(yr,rec);_,q=pred(fam,p,ff,tr,va,w);ss.append(sp(va.R,q));t=np.quantile(q,.75);ll.append(va.loc[q>=t,'R'].mean()-va.R.mean())
 return np.mean(ss),np.mean(ll)
def importance(m):
 if hasattr(m,'booster_'):a=m.booster_.feature_importance(importance_type='gain')
 else:a=np.asarray(m.feature_importances_)
 a=np.asarray(a,float);return a/(a.sum()+1e-12)
search=[];t0=time.time();A=[]
for fs in ['raw','eng','eng_rank']:
 for fam in ['lgb','xgb','cat']:
  s,l=cv(fam,basep[fam],FS[fs]);A.append((s,l,fam,fs));search.append([stage,direction,'family_preproc',fam,fs,'expanding',s,l,json.dumps(basep[fam])])
A.sort(key=lambda x:(-x[0],-x[1]));_,_,fam,fs=A[0];ff=FS[fs];B=[]
for p in grids[fam]:
 s,l=cv(fam,p,ff);B.append((s,l,p));search.append([stage,direction,'hparam',fam,fs,'expanding',s,l,json.dumps(p)])
B.sort(key=lambda x:(-x[0],-x[1]));_,_,p=B[0];C=[]
for rec in ['expanding','roll730','exp365','exp730']:
 s,l=cv(fam,p,ff,rec);C.append((s,l,rec));search.append([stage,direction,'recency',fam,fs,rec,s,l,json.dumps(p)])
C.sort(key=lambda x:(-x[0],-x[1]));_,_,rec=C[0]
ii=[]
for yr in [2023,2024]:tr,va,w=sub(yr,rec);m,q=pred(fam,p,ff,tr,va,w);ii.append(importance(m))
order=np.argsort(-np.mean(ii,axis=0));ranked=[ff[i] for i in order];K=[]
for k in sorted(set([8,16,min(24,len(ff)),len(ff)])):
 f2=ranked[:k];s,l=cv(fam,p,f2,rec);K.append((s,l,k,f2));search.append([stage,direction,'prune',fam,f'top{k}',rec,s,l,json.dumps(p)])
best=max(x[0] for x in K);ok=[x for x in K if x[0]>=best-.005];ok.sort(key=lambda x:(x[2],-x[0]));s,l,k,f2=ok[0]
selected=dict(stage=stage,direction=direction,family=fam,preprocess=fs,recency=rec,params=p,features=f2,tune=s,lift=l,prune=f'top{k} within .005 best {best:.4f}')
pd.DataFrame(search,columns=['stage','direction','phase','family','preprocess','recency','score','lift','params']).to_csv(OUT/f'SEARCH_{stage}_{direction}.csv',index=False)
(OUT/f'SELECTED_{stage}_{direction}.json').write_text(json.dumps(selected,indent=2))
# quantile tune and OOS
qps=[dict(n_estimators=160,num_leaves=7,max_depth=3,learning_rate=.04,min_child_samples=50,reg_lambda=10),dict(n_estimators=220,num_leaves=15,max_depth=4,learning_rate=.03,min_child_samples=80,reg_lambda=20)]
def qp(par,a,tr,va,w=None):
 z=dict(par);z.update(objective='quantile',alpha=a,verbosity=-1,n_jobs=2,random_state=SEED);m=LGBMRegressor(**z);m.fit(tr[f2].fillna(0),tr.R,sample_weight=w);return m.predict(va[f2].fillna(0))
Q=[]
for par in qps:
 loss=[]
 for yr in [2023,2024]:
  tr,va,w=sub(yr,rec);scale=max(np.median(np.abs(tr.R-np.median(tr.R))),.1)
  for a in [.1,.5,.9]:loss.append(mean_pinball_loss(va.R,qp(par,a,tr,va,w),alpha=a)/scale)
 Q.append((np.mean(loss),par))
Q.sort(key=lambda x:x[0]);qpar=Q[0][1];oos=[];qm=[]
for yr in [2024,2025,2026]:
 tr,va,w=sub(yr,rec);_,mu=pred(fam,p,f2,tr,va,w);qs={a:qp(qpar,a,tr,va,w) for a in [.1,.5,.9]}
 for j,i in enumerate(va.index):oos.append([i,yr,stage,direction,mu[j],qs[.1][j],qs[.5][j],qs[.9][j],va.loc[i,'R'],va.loc[i,'pnl'],va.loc[i,'rid'],va.loc[i,'L'],va.loc[i,'decision']])
 for a in [.1,.5,.9]:qm.append([stage,direction,yr,a,np.mean(va.R.values<=qs[a]),mean_pinball_loss(va.R,qs[a],alpha=a),len(va)])
pd.DataFrame(oos,columns=['idx','year','stage','direction','mean','q10','q50','q90','R','pnl','rid','L','decision']).to_csv(OUT/f'OOS_{stage}_{direction}.csv',index=False)
pd.DataFrame(qm,columns=['stage','direction','year','alpha','coverage','pinball','n']).to_csv(OUT/f'QUANT_{stage}_{direction}.csv',index=False)
print(json.dumps({'stage':stage,'direction':direction,'family':fam,'preprocess':fs,'recency':rec,'nfeat':len(f2),'tune':s,'runtime':time.time()-t0}))
