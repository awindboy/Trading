import sys,json,warnings
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
warnings.filterwarnings('ignore')
SEED=261017;OUT=Path('/mnt/data/v10_ml_advanced_r4');stage=sys.argv[1];direction=sys.argv[2];head=sys.argv[3];label='next_same' if head=='survival' else 'severe'
df=pd.read_pickle(OUT/'ENRICHED.pkl');FS=json.loads((OUT/'FEATURES.json').read_text());g=df[(df.stage==stage)&(df.direction==direction)].copy()
def mk(fam,p):
 p=dict(p)
 if fam=='lgb':p.update(verbosity=-1,n_jobs=2,random_state=SEED);return LGBMClassifier(**p)
 if fam=='xgb':p.update(objective='binary:logistic',eval_metric='logloss',verbosity=0,n_jobs=2,random_state=SEED);return XGBClassifier(**p)
 p.update(loss_function='Logloss',verbose=False,thread_count=2,random_seed=SEED,allow_writing_files=False);return CatBoostClassifier(**p)
base={'lgb':dict(n_estimators=120,num_leaves=15,max_depth=4,learning_rate=.04,min_child_samples=60,reg_lambda=10,reg_alpha=.5),'xgb':dict(n_estimators=120,max_depth=3,learning_rate=.04,min_child_weight=15,reg_lambda=15,reg_alpha=.5,subsample=.85,colsample_bytree=.85),'cat':dict(iterations=120,depth=5,learning_rate=.04,l2_leaf_reg=15,random_strength=.2)}
grids={'lgb':[dict(n_estimators=140,num_leaves=7,max_depth=3,learning_rate=.04,min_child_samples=50,reg_lambda=10,reg_alpha=.5),dict(n_estimators=200,num_leaves=15,max_depth=4,learning_rate=.03,min_child_samples=80,reg_lambda=20,reg_alpha=1)],'xgb':[dict(n_estimators=140,max_depth=2,learning_rate=.04,min_child_weight=15,reg_lambda=15,reg_alpha=.5,subsample=.9,colsample_bytree=.9),dict(n_estimators=200,max_depth=3,learning_rate=.03,min_child_weight=25,reg_lambda=25,reg_alpha=1,subsample=.85,colsample_bytree=.85)],'cat':[dict(iterations=160,depth=4,learning_rate=.04,l2_leaf_reg=15,random_strength=.2),dict(iterations=220,depth=5,learning_rate=.03,l2_leaf_reg=25,random_strength=.3)]}
def sub(yr,rec):
 tr=g[g.year<yr].copy();va=g[g.year==yr].copy();w=None
 if rec=='roll730':tr=tr[tr.decision>=pd.Timestamp(f'{yr}-01-01')-pd.Timedelta(days=730)]
 elif rec in ('exp365','exp730'):
  hl=int(rec[3:]);age=(pd.Timestamp(f'{yr}-01-01')-tr.decision).dt.total_seconds()/86400;w=np.power(.5,age/hl).values
 return tr,va,w
def pred(fam,p,ff,tr,va,w=None):
 m=mk(fam,p);m.fit(tr[ff].fillna(0),tr[label],sample_weight=w);return m,m.predict_proba(va[ff].fillna(0))[:,1]
def auc(y,p):return roc_auc_score(y,p) if len(np.unique(y))>1 else np.nan
def cv(fam,p,ff,rec='expanding'):
 aa=[]
 for yr in [2023,2024]:tr,va,w=sub(yr,rec);_,q=pred(fam,p,ff,tr,va,w);aa.append(auc(va[label],q))
 return np.mean(aa)
def imp(m):
 if hasattr(m,'booster_'):a=m.booster_.feature_importance(importance_type='gain')
 else:a=np.asarray(m.feature_importances_)
 a=np.asarray(a,float);return a/(a.sum()+1e-12)
search=[];A=[]
for fs in ['raw','eng','eng_rank']:
 for fam in ['lgb','xgb','cat']:
  s=cv(fam,base[fam],FS[fs]);A.append((s,fam,fs));search.append([head,stage,direction,'family',fam,fs,'expanding',s,json.dumps(base[fam])])
A.sort(reverse=True);_,fam,fs=A[0];ff=FS[fs];B=[]
for p in grids[fam]:s=cv(fam,p,ff);B.append((s,p));search.append([head,stage,direction,'hparam',fam,fs,'expanding',s,json.dumps(p)])
B.sort(key=lambda x:-x[0]);_,p=B[0];C=[]
for rec in ['expanding','roll730','exp365','exp730']:
 s=cv(fam,p,ff,rec);C.append((s,rec));search.append([head,stage,direction,'recency',fam,fs,rec,s,json.dumps(p)])
C.sort(reverse=True);_,rec=C[0]
# compactness all vs top16
im=[]
for yr in [2023,2024]:tr,va,w=sub(yr,rec);m,q=pred(fam,p,ff,tr,va,w);im.append(imp(m))
ranked=[ff[i] for i in np.argsort(-np.mean(im,axis=0))];opts=[]
for k in sorted(set([16,len(ff)])):
 f2=ranked[:k];s=cv(fam,p,f2,rec);opts.append((s,k,f2));search.append([head,stage,direction,'prune',fam,f'top{k}',rec,s,json.dumps(p)])
best=max(x[0] for x in opts);ok=[x for x in opts if x[0]>=best-.005];ok.sort(key=lambda x:x[1]);s,k,f2=ok[0]
sel=dict(head=head,stage=stage,direction=direction,label=label,family=fam,preprocess=fs,recency=rec,params=p,features=f2,tune_auc=s)
(OUT/f'CLS_SELECTED_{head}_{stage}_{direction}.json').write_text(json.dumps(sel,indent=2));pd.DataFrame(search,columns=['head','stage','direction','phase','family','preprocess','recency','score','params']).to_csv(OUT/f'CLS_SEARCH_{head}_{stage}_{direction}.csv',index=False)
rows=[]
for yr in [2023,2024,2025,2026]:
 tr,va,w=sub(yr,rec);_,q=pred(fam,p,f2,tr,va,w)
 for idx,pr in zip(va.index,q):rows.append([idx,yr,head,stage,direction,pr,va.loc[idx,label],va.loc[idx,'decision']])
pd.DataFrame(rows,columns=['idx','year','head','stage','direction','pred','actual','decision']).to_csv(OUT/f'CLS_OOS_{head}_{stage}_{direction}.csv',index=False)
print(json.dumps({'head':head,'stage':stage,'direction':direction,'family':fam,'preprocess':fs,'recency':rec,'nfeat':len(f2),'tune_auc':s}))
