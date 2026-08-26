#!/usr/bin/env python3
"""R4 MOMENT-1-small frozen-embedding transfer diagnostic.

This is deliberately non-claim-grade.  The external foundation model was pretrained on
Timeseries-PILE, so its embedding skill is useful as a transfer benchmark but does not
constitute pristine V4 OOS evidence.
"""
from pathlib import Path
import argparse,json,sys
import numpy as np
import torch
from torch.utils.data import DataLoader,Subset
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import roc_auc_score

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from v4_001_common import CausalWindowDataset

ALL=['GOLD#','BTCUSD#','XAUEUR#','USDJPY#']


def cap_indices(ds,cap):
 g={}
 for i,s in enumerate(ds.samples):g.setdefault((s[0],__import__('pandas').Timestamp(int(s[2])).year),[]).append(i)
 out=[]
 for _,ix in sorted(g.items()):
  if len(ix)>cap:
   take=np.unique(np.linspace(0,len(ix)-1,cap).round().astype(int));ix=[ix[j] for j in take]
  out.extend(ix)
 return sorted(out)


def encode(model,ds,indices,batch,workers,device):
 dl=DataLoader(Subset(ds,indices),batch_size=batch,shuffle=False,num_workers=workers,pin_memory=(device.type=='cuda'))
 Z=[];Y=[]
 with torch.no_grad():
  for b in dl:
   x=b['streams']['M1'].float();mask=b['masks']['M1'].bool();tm=b['target_mask'].bool();B,M,L,F=x.shape;mi=tm.long().argmax(1);ar=torch.arange(B)
   # Same causal M1 history as R1/R2; use normalized log return channel only.
   seq=x[ar,mi,:,0];msk=mask[ar,mi,:]
   pad=512-L
   if pad<0:seq=seq[:,-512:];msk=msk[:,-512:]
   elif pad>0:
    seq=torch.nn.functional.pad(seq,(pad,0));msk=torch.nn.functional.pad(msk,(pad,0),value=False)
   seq=seq.unsqueeze(1).to(device);msk=msk.to(device)
   out=model(x_enc=seq,input_mask=msk);emb=out.embeddings
   if emb.ndim==3:z=emb.mean(1)
   elif emb.ndim==2:z=emb
   else:raise RuntimeError(f'unexpected MOMENT embedding shape {tuple(emb.shape)}')
   Z.append(z.float().cpu().numpy());Y.append((b['y_norm'][:,0].numpy()>0).astype(np.uint8))
 return np.concatenate(Z),np.concatenate(Y)


def run_fold(model,prepared,base_cfg,train_targets,train_years,eval_targets,eval_years,cap,batch,workers,device):
 tr=CausalWindowDataset(prepared,base_cfg,train_targets,target_symbols=train_targets,years=train_years);ev=CausalWindowDataset(prepared,base_cfg,eval_targets,target_symbols=eval_targets,years=eval_years)
 ti=cap_indices(tr,cap);ei=cap_indices(ev,cap);zt,yt=encode(model,tr,ti,batch,workers,device);ze,ye=encode(model,ev,ei,batch,workers,device)
 clf=SGDClassifier(loss='log_loss',alpha=1e-4,max_iter=20,tol=1e-4,random_state=17,class_weight='balanced',average=True);clf.fit(zt,yt);p=clf.predict_proba(ze)[:,1]
 return {'n_train':len(yt),'n_eval':len(ye),'auc15':float(roc_auc_score(ye,p))}


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--base-config',type=Path,required=True);ap.add_argument('--diag-config',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--batch-size',type=int,default=32);ap.add_argument('--workers',type=int,default=0);a=ap.parse_args()
 from momentfm import MOMENTPipeline
 cfg=json.loads(a.diag_config.read_text(encoding='utf-8'))['moment'];base=json.loads(a.base_config.read_text(encoding='utf-8'));device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
 model=MOMENTPipeline.from_pretrained(cfg['model'],model_kwargs={'task_name':'embedding'});model.init();model.to(device);model.eval()
 cap=int(cfg['max_samples_per_symbol_year']);res={'authority':'TRANSFER_DIAGNOSTIC_ONLY','device':str(device),'model':cfg['model'],'cap_per_symbol_year':cap,'folds':{}}
 res['folds']['TEMPORAL_2025']=run_fold(model,a.prepared,base,ALL,[2023,2024],ALL,[2025],cap,a.batch_size,a.workers,device)
 for hold in ALL:
  train=[x for x in ALL if x!=hold];res['folds']['LOMO_FUTURE_2025_'+hold]=run_fold(model,a.prepared,base,train,[2023,2024],[hold],[2025],cap,a.batch_size,a.workers,device);print(hold,res['folds']['LOMO_FUTURE_2025_'+hold],flush=True)
 a.out.write_text(json.dumps(res,indent=2),encoding='utf-8');print('MOMENT DIAGNOSTIC',a.out.resolve())
if __name__=='__main__':main()
