#!/usr/bin/env python3
from pathlib import Path
import argparse,json,math
import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import roc_auc_score,brier_score_loss
from v4_001_common import CausalWindowDataset,FEATURE_NAMES
from v4_001_model import CausalPatchPolicy


def move(batch,device):
    out={}
    for k,v in batch.items():
        if isinstance(v,dict):out[k]={a:b.to(device) for a,b in v.items()}
        elif torch.is_tensor(v):out[k]=v.to(device)
        else:out[k]=v
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--checkpoint',type=Path,required=True)
    ap.add_argument('--symbols',default='GOLD#,BTCUSD#,XAUEUR#,USDJPY#');ap.add_argument('--years',default='2025');ap.add_argument('--out',type=Path,required=True);ap.add_argument('--batch-size',type=int,default=256)
    args=ap.parse_args();ck=torch.load(args.checkpoint,map_location='cpu');cfg=ck['config'];symbols=args.symbols.split(',');years=list(map(int,args.years.split(',')));device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    ds=CausalWindowDataset(args.prepared,cfg,symbols,years=years);dl=DataLoader(ds,batch_size=args.batch_size,shuffle=False)
    model=CausalPatchPolicy(cfg,len(FEATURE_NAMES));model.load_state_dict(ck['model']);model.to(device).eval();rows=[];prev={s:0 for s in symbols};equity={s:0.0 for s in symbols};turn={s:0 for s in symbols}
    probs=[];ys=[];pred_mu=[];raw=[];spreads=[];times=[];targets=[]
    with torch.no_grad():
        for b in dl:
            bb=move(b,device);o=model(bb);p=torch.sigmoid(o['direction_logit'][:,0]).cpu().numpy();mu_norm=o['mu'][:,0].cpu().numpy();sigma1=b['sigma1m'].numpy();mu_raw=mu_norm*sigma1*np.sqrt(cfg['horizons_minutes'][0])
            probs.extend(p);ys.extend((b['y_norm'][:,0].numpy()>0).astype(int));pred_mu.extend(mu_raw);raw.extend(b['y_raw'][:,0].numpy());spreads.extend(b['spread_return'].numpy());times.extend(b['decision_ns'].numpy())
            # identify target from target mask index and dataset fixed symbol order
            ti=b['target_mask'].numpy().argmax(1);targets.extend([symbols[i] for i in ti])
    probs=np.asarray(probs);ys=np.asarray(ys);pred_mu=np.asarray(pred_mu);raw=np.asarray(raw);spreads=np.asarray(spreads);times=np.asarray(times);targets=np.asarray(targets)
    metrics={'n':int(len(ys)),'auc15':float(roc_auc_score(ys,probs)),'brier15':float(brier_score_loss(ys,probs)),'corr_mu_realized15':float(np.corrcoef(pred_mu,raw)[0,1])}
    # Development-only one-step controller, sequential within each target symbol.
    pol=[]
    for s in symbols:
        ix=np.where(targets==s)[0];ix=ix[np.argsort(times[ix])];p0=0;eq=0.;gross=0.;cost=0.;changes=0
        for i in ix:
            half=0.5*float(spreads[i]);q={a:a*float(pred_mu[i])-half*abs(a-p0) for a in (-1,0,1)};a=max(q,key=q.get)
            r=a*float(raw[i]);c=half*abs(a-p0);gross+=r;cost+=c;eq+=r-c;changes+=int(a!=p0);p0=a
        pol.append({'symbol':s,'n':int(len(ix)),'gross_logret':gross,'spread_cost':cost,'net_logret':eq,'exposure_changes':changes})
    metrics['policy']=pol;args.out.mkdir(parents=True,exist_ok=True);(args.out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8');print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
