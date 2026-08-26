#!/usr/bin/env python3
from pathlib import Path
import argparse,json,random,math
import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import roc_auc_score
from v4_001_common import CausalWindowDataset,FEATURE_NAMES
from v4_001_model import CausalPatchPolicy,multitask_loss


def seed_all(s): random.seed(s);np.random.seed(s);torch.manual_seed(s)

def move(batch,device):
    out={}
    for k,v in batch.items():
        if isinstance(v,dict):out[k]={a:b.to(device) for a,b in v.items()}
        elif torch.is_tensor(v):out[k]=v.to(device)
        else:out[k]=v
    return out

def eval_epoch(model,dl,cfg,device):
    model.eval();losses=[];correct=[];probs=[];ys=[]
    with torch.no_grad():
        for b in dl:
            b=move(b,device);o=model(b);loss,_=multitask_loss(o,b,cfg);losses.append(float(loss))
            p=torch.sigmoid(o['direction_logit'][:,0]);y=(b['y_norm'][:,0]>0).float();probs.extend(p.cpu().tolist());ys.extend(y.cpu().tolist())
    y=np.asarray(ys);p=np.asarray(probs)
    auc=float(roc_auc_score(y,p)) if len(np.unique(y))==2 else float('nan')
    return float(np.mean(losses)) if losses else math.nan,float(auc)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--config',type=Path,default=Path('config/v4_001_baseline.json'))
    ap.add_argument('--symbols',default='GOLD#,BTCUSD#,XAUEUR#,USDJPY#');ap.add_argument('--train-years',default='2023,2024');ap.add_argument('--eval-years',default='2025')
    ap.add_argument('--seed',type=int,default=17);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--workers',type=int,default=0)
    ap.add_argument('--batch-size',type=int,default=None);ap.add_argument('--max-train-samples',type=int,default=None);ap.add_argument('--max-eval-samples',type=int,default=None)
    args=ap.parse_args();cfg=json.loads(args.config.read_text());symbols=args.symbols.split(',');trainy=list(map(int,args.train_years.split(',')));evaly=list(map(int,args.eval_years.split(',')))
    seed_all(args.seed);device=torch.device('cuda' if torch.cuda.is_available() else 'cpu');print('device',device)
    tr=CausalWindowDataset(args.prepared,cfg,symbols,years=trainy);ev=CausalWindowDataset(args.prepared,cfg,symbols,years=evaly)
    if args.max_train_samples and len(tr)>args.max_train_samples: tr.samples=tr.samples[:args.max_train_samples]
    if args.max_eval_samples and len(ev)>args.max_eval_samples: ev.samples=ev.samples[:args.max_eval_samples]
    bs=args.batch_size or cfg['training']['batch_size'];td=DataLoader(tr,batch_size=bs,shuffle=True,num_workers=args.workers,pin_memory=device.type=='cuda');ed=DataLoader(ev,batch_size=bs,shuffle=False,num_workers=args.workers)
    model=CausalPatchPolicy(cfg,len(FEATURE_NAMES)).to(device);print('params',sum(p.numel() for p in model.parameters()))
    opt=torch.optim.AdamW(model.parameters(),lr=cfg['optimizer']['lr'],weight_decay=cfg['optimizer']['weight_decay'])
    args.out.mkdir(parents=True,exist_ok=True);best=float('inf');pat=0;history=[]
    for epoch in range(1,cfg['training']['max_epochs']+1):
        model.train();ls=[]
        for b in td:
            b=move(b,device);opt.zero_grad(set_to_none=True);o=model(b);loss,_=multitask_loss(o,b,cfg);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),cfg['optimizer']['grad_clip']);opt.step();ls.append(float(loss.detach()))
        vl,auc=eval_epoch(model,ed,cfg,device);row={'epoch':epoch,'train_loss':float(np.mean(ls)),'eval_loss':vl,'eval_auc15':auc};history.append(row);print(row)
        if vl<best-1e-5:
            best=vl;pat=0;torch.save({'model':model.state_dict(),'config':cfg,'seed':args.seed,'row':row},args.out/'best.pt')
        else:
            pat+=1
            if pat>=cfg['training']['early_stop_patience']:break
    (args.out/'history.json').write_text(json.dumps(history,indent=2),encoding='utf-8');print('TRAIN PASS',args.out/'best.pt')
if __name__=='__main__':main()
