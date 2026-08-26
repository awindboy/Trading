#!/usr/bin/env python3
"""Frozen V4-001A pooled linear/logistic control.

Uses the same causal 14-channel prepared streams but compresses each configured history into:
last bar, full-window mean, recent-half minus older-half mean, and stream age.
For each timeframe the target summary and mean of allowed context-market summaries are concatenated.
No symbol ID or technical-analysis labels are used.

Primary strict LOMO folds exclude the held-out symbol entirely from training contexts and use
other markets 2023-2024 -> held-out target 2025.
"""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

SYMS=['GOLD#','BTCUSD#','XAUEUR#','USDJPY#'];F=14
CACHE={}

def safe(s):return s.replace('#','_HASH')

def load(root,cfg):
 M={}
 for s in SYMS:
  d=root/safe(s);M[s]={'t':np.load(d/'decision_ns.npy',mmap_mode='r'),'y':np.load(d/'future_normret.npy',mmap_mode='r')[:,0],'streams':{}}
  for tf in cfg['timeframes']:
   M[s]['streams'][tf]=(np.load(d/f'{tf}_x.npy',mmap_mode='r'),np.load(d/f'{tf}_available_ns.npy',mmap_mode='r'),np.load(d/f'{tf}_valid.npy',mmap_mode='r'))
 return M

def summarize(m,tf,times,cfg):
 x,av,v=m['streams'][tf];L=int(cfg['timeframes'][tf]['history']);end=np.searchsorted(av,times,side='right').astype(np.int64);li=np.maximum(end-1,0)
 last=np.asarray(x[li],dtype=np.float32).copy();has=end>0;last[~has]=0;age=np.where(has,np.maximum(0,(times-av[li])/60e9),1e6).astype(np.float32)
 key=(id(x),tf)
 if key not in CACHE:
  xv=np.asarray(x,dtype=np.float32)*np.asarray(v,dtype=np.float32)[:,None]
  CACHE[key]=(np.vstack([np.zeros((1,F),np.float64),np.cumsum(xv,dtype=np.float64,axis=0)]),np.r_[0,np.cumsum(np.asarray(v,dtype=np.int64))])
 cs,cc=CACHE[key]
 start=np.maximum(0,end-L);mean=((cs[end]-cs[start])/(cc[end]-cc[start]).clip(min=1)[:,None]).astype(np.float32)
 half=max(1,L//2);mid=np.maximum(start,end-half)
 recent=((cs[end]-cs[mid])/(cc[end]-cc[mid]).clip(min=1)[:,None]).astype(np.float32)
 older=((cs[mid]-cs[start])/(cc[mid]-cc[start]).clip(min=1)[:,None]).astype(np.float32)
 return np.concatenate([last,mean,recent-older,np.log1p(age)[:,None]],1)

def make_X(M,cfg,target,contexts,years):
 t=np.asarray(M[target]['t'],dtype=np.int64);yr=pd.to_datetime(t).year.to_numpy();keep=np.isin(yr,years);t=t[keep];y=(np.asarray(M[target]['y'])[keep]>0).astype(np.uint8);blocks=[]
 for tf in cfg['timeframes']:
  tar=summarize(M[target],tf,t,cfg);ctxs=[s for s in contexts if s!=target]
  ctx=np.mean(np.stack([summarize(M[s],tf,t,cfg) for s in ctxs]),0).astype(np.float32) if ctxs else np.zeros_like(tar)
  blocks.extend([tar,ctx])
 return np.concatenate(blocks,1).astype(np.float32),y

def fit_auc(Xtr,ytr,Xe,ye):
 sc=StandardScaler();a=sc.fit_transform(Xtr);b=sc.transform(Xe)
 m=SGDClassifier(loss='log_loss',alpha=1e-4,max_iter=3,tol=None,random_state=17,average=True,n_jobs=-1)
 m.fit(a,ytr);return float(roc_auc_score(ye,m.decision_function(b)))

def pooled(M,cfg,train_targets,train_context,train_years,eval_targets,eval_context,eval_years):
 tx=[];ty=[]
 for s in train_targets:
  x,y=make_X(M,cfg,s,train_context,train_years);tx.append(x);ty.append(y)
 ex=[];ey=[]
 for s in eval_targets:
  x,y=make_X(M,cfg,s,eval_context,eval_years);ex.append(x);ey.append(y)
 Xtr=np.concatenate(tx);ytr=np.concatenate(ty);Xe=np.concatenate(ex);ye=np.concatenate(ey)
 return {'n_train':int(len(ytr)),'n_eval':int(len(ye)),'auc15':fit_auc(Xtr,ytr,Xe,ye),'feature_dim':int(Xtr.shape[1])}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--config',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 cfg=json.loads(args.config.read_text());M=load(args.prepared,cfg);res={}
 res['TEMPORAL_2024']=pooled(M,cfg,SYMS,SYMS,[2023],SYMS,SYMS,[2024]);print('TEMPORAL_2024',res['TEMPORAL_2024'],flush=True)
 res['TEMPORAL_2025_PRIMARY']=pooled(M,cfg,SYMS,SYMS,[2023,2024],SYMS,SYMS,[2025]);print('TEMPORAL_2025_PRIMARY',res['TEMPORAL_2025_PRIMARY'],flush=True)
 for hold in SYMS:
  tr=[s for s in SYMS if s!=hold]
  name='LOMO_FUTURE_2025_'+hold;res[name]=pooled(M,cfg,tr,tr,[2023,2024],[hold],SYMS,[2025]);print(name,res[name],flush=True)
 out={'status':'FROZEN_LINEAR_CONTROL','definition':'target/context last + window mean + recent-half-minus-older-half + age; StandardScaler(train only); averaged 3-pass SGD logistic alpha=1e-4 seed17','folds':res}
 args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(out,indent=2),encoding='utf-8');print('LINEAR BASELINE COMPLETE',args.out)
if __name__=='__main__':main()
