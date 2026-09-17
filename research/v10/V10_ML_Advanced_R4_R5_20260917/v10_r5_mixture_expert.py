import sys,json,warnings
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from lightgbm import LGBMRegressor,LGBMClassifier
from xgboost import XGBRegressor,XGBClassifier
from catboost import CatBoostRegressor,CatBoostClassifier
warnings.filterwarnings('ignore')
SEED=261017;OUT=Path('/mnt/data/v10_ml_advanced_r5');OUT.mkdir(exist_ok=True);BASE=Path('/mnt/data/v10_ml_advanced_r4')
stage=sys.argv[1];direction=sys.argv[2]
df=pd.read_pickle(BASE/'ENRICHED.pkl');FS=json.loads((BASE/'FEATURES.json').read_text());g=df[(df.stage==stage)&(df.direction==direction)].copy()
base={'lgb':dict(n_estimators=120,num_leaves=15,max_depth=4,learning_rate=.04,min_child_samples=60,reg_lambda=10,reg_alpha=.5),'xgb':dict(n_estimators=120,max_depth=3,learning_rate=.04,min_child_weight=15,reg_lambda=15,reg_alpha=.5,subsample=.85,colsample_bytree=.85),'cat':dict(iterations=120,depth=5,learning_rate=.04,l2_leaf_reg=15,random_strength=.2)}
grids={'lgb':[dict(n_estimators=140,num_leaves=7,max_depth=3,learning_rate=.04,min_child_samples=50,reg_lambda=10,reg_alpha=.5),dict(n_estimators=200,num_leaves=15,max_depth=4,learning_rate=.03,min_child_samples=80,reg_lambda=20,reg_alpha=1)],'xgb':[dict(n_estimators=140,max_depth=2,learning_rate=.04,min_child_weight=15,reg_lambda=15,reg_alpha=.5,subsample=.9,colsample_bytree=.9),dict(n_estimators=200,max_depth=3,learning_rate=.03,min_child_weight=25,reg_lambda=25,reg_alpha=1,subsample=.85,colsample_bytree=.85)],'cat':[dict(iterations=160,depth=4,learning_rate=.04,l2_leaf_reg=15,random_strength=.2),dict(iterations=220,depth=5,learning_rate=.03,l2_leaf_reg=25,random_strength=.3)]}
def mk(fam,p,task):
 p=dict(p)
 if fam=='lgb':p.update(verbosity=-1,n_jobs=2,random_state=SEED);return LGBMClassifier(**p) if task=='cls' else LGBMRegressor(**p)
 if fam=='xgb':
  p.update(verbosity=0,n_jobs=2,random_state=SEED);return XGBClassifier(objective='binary:logistic',eval_metric='logloss',**p) if task=='cls' else XGBRegressor(objective='reg:squarederror',**p)
 p.update(verbose=False,thread_count=2,random_seed=SEED,allow_writing_files=False);return CatBoostClassifier(loss_function='Logloss',**p) if task=='cls' else CatBoostRegressor(loss_function='RMSE',**p)
def sub(data,yr,rec):
 tr=data[data.year<yr].copy();va=data[data.year==yr].copy();w=None
 if rec=='roll730':tr=tr[tr.decision>=pd.Timestamp(f'{yr}-01-01')-pd.Timedelta(days=730)]
 elif rec in ('exp365','exp730'):
  hl=int(rec[3:]);age=(pd.Timestamp(f'{yr}-01-01')-tr.decision).dt.total_seconds()/86400;w=np.power(.5,age/hl).values
 return tr,va,w
def fitpred(data,fam,p,ff,task,label,yr,rec):
 tr,va,w=sub(data,yr,rec);m=mk(fam,p,task);m.fit(tr[ff].fillna(0),tr[label],sample_weight=w);pr=m.predict_proba(va[ff].fillna(0))[:,1] if task=='cls' else m.predict(va[ff].fillna(0));return m,va,pr
def metric(y,p,task):return roc_auc_score(y,p) if task=='cls' else float(spearmanr(y,p).statistic)
def cv(data,fam,p,ff,task,label,rec='expanding'):
 v=[]
 for yr in [2023,2024]:_,va,pr=fitpred(data,fam,p,ff,task,label,yr,rec);v.append(metric(va[label],pr,task))
 return np.mean(v)
def imp(m):
 if hasattr(m,'booster_'):a=m.booster_.feature_importance(importance_type='gain')
 else:a=np.asarray(m.feature_importances_)
 a=np.asarray(a,float);return a/(a.sum()+1e-12)
def select(data,task,label):
 search=[];A=[]
 for fs in ['raw','eng','eng_rank']:
  for fam in ['lgb','xgb','cat']:
   s=cv(data,fam,base[fam],FS[fs],task,label);A.append((s,fam,fs));search.append(['family',fam,fs,'expanding',s,json.dumps(base[fam])])
 A.sort(reverse=True);_,fam,fs=A[0];ff=FS[fs];B=[]
 for p in grids[fam]:s=cv(data,fam,p,ff,task,label);B.append((s,p));search.append(['hparam',fam,fs,'expanding',s,json.dumps(p)])
 B.sort(key=lambda x:-x[0]);_,p=B[0];C=[]
 for rec in ['expanding','roll730','exp365','exp730']:
  s=cv(data,fam,p,ff,task,label,rec);C.append((s,rec));search.append(['recency',fam,fs,rec,s,json.dumps(p)])
 C.sort(reverse=True);_,rec=C[0]
 ii=[]
 for yr in [2023,2024]:m,va,pr=fitpred(data,fam,p,ff,task,label,yr,rec);ii.append(imp(m))
 ranked=[ff[i] for i in np.argsort(-np.mean(ii,axis=0))];O=[]
 for k in sorted(set([16,len(ff)])):
  f2=ranked[:k];s=cv(data,fam,p,f2,task,label,rec);O.append((s,k,f2));search.append(['prune',fam,f'top{k}',rec,s,json.dumps(p)])
 best=max(x[0] for x in O);ok=[x for x in O if x[0]>=best-.005];ok.sort(key=lambda x:x[1]);s,k,f2=ok[0]
 return dict(family=fam,preprocess=fs,params=p,recency=rec,features=f2,tune=s),search
stop_sel,search_stop=select(g,'cls','stop_hit')
cond=g[g.stop_hit==0].copy();r_sel,search_r=select(cond,'reg','R')
# OOS 2024-26 predictions; conditional R model predicts all rows using training on non-stop only
rows=[]
for yr in [2024,2025,2026]:
 # stop
 tr,va,w=sub(g,yr,stop_sel['recency']);m=mk(stop_sel['family'],stop_sel['params'],'cls');m.fit(tr[stop_sel['features']].fillna(0),tr.stop_hit,sample_weight=w);ps=m.predict_proba(va[stop_sel['features']].fillna(0))[:,1]
 # conditional R
 trc=cond[cond.year<yr].copy();wc=None
 if r_sel['recency']=='roll730':trc=trc[trc.decision>=pd.Timestamp(f'{yr}-01-01')-pd.Timedelta(days=730)]
 elif r_sel['recency'] in ('exp365','exp730'):
  hl=int(r_sel['recency'][3:]);age=(pd.Timestamp(f'{yr}-01-01')-trc.decision).dt.total_seconds()/86400;wc=np.power(.5,age/hl).values
 mr=mk(r_sel['family'],r_sel['params'],'reg');mr.fit(trc[r_sel['features']].fillna(0),trc.R,sample_weight=wc);mu=mr.predict(va[r_sel['features']].fillna(0))
 ev=-ps+(1-ps)*mu
 for j,i in enumerate(va.index):rows.append([i,yr,stage,direction,ps[j],mu[j],ev[j],va.loc[i,'R'],va.loc[i,'pnl'],va.loc[i,'rid'],va.loc[i,'L'],va.loc[i,'decision']])
pd.DataFrame(rows,columns=['idx','year','stage','direction','p_stop','mu_nonstop','EV','R','pnl','rid','L','decision']).to_csv(OUT/f'MIX_OOS_{stage}_{direction}.csv',index=False)
sel={'stage':stage,'direction':direction,'stop':stop_sel,'conditional_R':r_sel};(OUT/f'MIX_SELECTED_{stage}_{direction}.json').write_text(json.dumps(sel,indent=2));pd.DataFrame(search_stop,columns=['phase','family','preprocess','recency','score','params']).to_csv(OUT/f'MIX_SEARCH_STOP_{stage}_{direction}.csv',index=False);pd.DataFrame(search_r,columns=['phase','family','preprocess','recency','score','params']).to_csv(OUT/f'MIX_SEARCH_R_{stage}_{direction}.csv',index=False)
print(json.dumps({'stage':stage,'direction':direction,'stop_auc':stop_sel['tune'],'stop_model':stop_sel['family']+'/'+stop_sel['preprocess']+'/'+stop_sel['recency'],'cond_rho':r_sel['tune'],'r_model':r_sel['family']+'/'+r_sel['preprocess']+'/'+r_sel['recency']}))
