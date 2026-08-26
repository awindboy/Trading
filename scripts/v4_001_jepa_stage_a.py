#!/usr/bin/env python3
"""V4-001 R2 MarketJEPA claim-grade Stage-A runner.

Protocol:
- same frozen development allocation and strict folds as R1;
- self-supervised pretraining uses only the training allocation;
- chronological inner validation + 7-day purge; outer data is untouched;
- pretraining predicts the target market's causal latent state 15 minutes later;
- encoder is frozen before a *linear* direction probe is trained;
- seeds 17/29/43 are ensembled; no seed selection;
- strict future-isolated LOMO excludes the held-out market from pretraining context and targets.

The purpose is to test whether self-supervised financial dynamics pretraining improves
transferable representation skill, not to tune trading P/L.
"""
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, math, platform, random, sys
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader, Subset, WeightedRandomSampler, TensorDataset
from sklearn.metrics import roc_auc_score, brier_score_loss

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from v4_001_common import CausalWindowDataset, FEATURE_NAMES
from v4_001_jepa_model import MarketJEPA, CausalPatchEncoder
from v4_001_stage_a import (
    ALL_SYMBOLS, PURGE_DAYS, INNER_VAL_FRACTION,
    verify_prepared_identity, seed_all, move, chronological_inner_split,
    fold_specs, summary_metrics, sha256_file,
)


def contiguous_cap(ds, indices, cap_per_target_year):
    if not cap_per_target_year: return list(indices)
    groups={}
    for i in indices:
        s=ds.samples[i]; key=(s[0], pd.Timestamp(int(s[2])).year); groups.setdefault(key,[]).append(i)
    out=[]
    for key,ix in sorted(groups.items()):
        ix=sorted(ix,key=lambda i:int(ds.samples[i][2]))
        out.extend(ix[:cap_per_target_year])
    return sorted(out,key=lambda i:int(ds.samples[i][2]))


def load_json(p:Path): return json.loads(p.read_text(encoding='utf-8'))


class FutureStatePairDataset(Dataset):
    """Pairs a causal decision state at t with the same target state at t+h.

    Both indices must belong to the already-selected partition, preventing pairs from
    crossing fit/inner-val/purge boundaries.
    """
    def __init__(self, base:CausalWindowDataset, indices:list[int], horizon_minutes:int=15):
        self.base=base; self.h=int(pd.Timedelta(minutes=horizon_minutes).value)
        allowed=set(indices)
        lookup={(base.samples[i][0], int(base.samples[i][2])):i for i in indices}
        pairs=[]
        for i in indices:
            s=base.samples[i]; key=(s[0], int(s[2])+self.h)
            j=lookup.get(key)
            if j is not None and j in allowed: pairs.append((i,j))
        self.pairs=pairs
    def __len__(self): return len(self.pairs)
    def __getitem__(self,k):
        i,j=self.pairs[k]
        return {'context':self.base[i],'future':self.base[j]}
    def target(self,k): return self.base.samples[self.pairs[k][0]][0]


def pair_sampler(ds:FutureStatePairDataset,seed:int):
    counts={}
    for k in range(len(ds)): counts[ds.target(k)]=counts.get(ds.target(k),0)+1
    w=torch.tensor([1.0/counts[ds.target(k)] for k in range(len(ds))],dtype=torch.double)
    g=torch.Generator();g.manual_seed(seed)
    return WeightedRandomSampler(w,num_samples=len(ds),replacement=True,generator=g),counts


def pair_loader(ds,batch,workers,sampler=None):
    return DataLoader(ds,batch_size=batch,sampler=sampler,shuffle=False,num_workers=workers,
                      pin_memory=torch.cuda.is_available(),persistent_workers=(workers>0))


def eval_jepa(model,dl,device):
    model.eval();tot=0.;n=0;parts={'pred':0.,'var':0.,'cov':0.}
    with torch.no_grad():
        for b in dl:
            c=move(b['context'],device);f=move(b['future'],device)
            loss,d=model(c,f);bs=c['target_mask'].shape[0]
            tot += float(loss.cpu())*bs;n+=bs
            for k in parts:parts[k]+=d[k]*bs
    out={'loss':tot/max(n,1),'n':n}
    out.update({k:parts[k]/max(n,1) for k in parts})
    return out


def train_jepa(base_cfg,jepa_cfg,train_ds,fit_idx,val_idx,seed,out,batch,effective_batch,workers,max_epochs_override=None,min_pairs_fit=1000,min_pairs_val=200):
    seed_all(seed);device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    fit_pair=FutureStatePairDataset(train_ds,fit_idx,int(jepa_cfg['pretrain_horizon_minutes']))
    val_pair=FutureStatePairDataset(train_ds,val_idx,int(jepa_cfg['pretrain_horizon_minutes']))
    if len(fit_pair)<min_pairs_fit or len(val_pair)<min_pairs_val: raise RuntimeError(f'too few JEPA causal pairs fit={len(fit_pair)} val={len(val_pair)}')
    sampler,counts=pair_sampler(fit_pair,seed)
    fit_dl=pair_loader(fit_pair,batch,workers,sampler);val_dl=pair_loader(val_pair,batch,workers)
    model=MarketJEPA(base_cfg,jepa_cfg,len(FEATURE_NAMES)).to(device)
    opt=torch.optim.AdamW(model.parameters(),lr=float(jepa_cfg['optimizer']['lr']),weight_decay=float(jepa_cfg['optimizer']['weight_decay']))
    accum=max(1,math.ceil(effective_batch/batch));amp=device.type=='cuda';scaler=torch.amp.GradScaler('cuda',enabled=amp)
    best=math.inf;pat=0;hist=[];out.mkdir(parents=True,exist_ok=True)
    maxep=int(max_epochs_override or jepa_cfg['training']['pretrain_max_epochs']);patlim=int(jepa_cfg['training']['pretrain_patience'])
    for ep in range(1,maxep+1):
        model.train();opt.zero_grad(set_to_none=True);vals=[]
        for bi,b in enumerate(fit_dl,1):
            c=move(b['context'],device);f=move(b['future'],device)
            with torch.amp.autocast(device_type=device.type,enabled=amp):
                loss,_=model(c,f);sl=loss/accum
            scaler.scale(sl).backward();vals.append(float(loss.detach().cpu()))
            if bi%accum==0 or bi==len(fit_dl):
                scaler.unscale_(opt);torch.nn.utils.clip_grad_norm_(model.parameters(),float(jepa_cfg['optimizer']['grad_clip']))
                scaler.step(opt);scaler.update();opt.zero_grad(set_to_none=True)
        vv=eval_jepa(model,val_dl,device)
        row={'epoch':ep,'fit_loss':float(np.mean(vals)),'inner_val':vv};hist.append(row);print('JEPA',seed,row,flush=True)
        if vv['loss']<best-1e-5:
            best=vv['loss'];pat=0
            torch.save({'encoder':model.encoder.state_dict(),'predictor':model.predictor.state_dict(),'base_cfg':base_cfg,'jepa_cfg':jepa_cfg,'seed':seed,'row':row},out/'jepa_best.pt')
        else:
            pat+=1
            if pat>=patlim:break
    (out/'jepa_history.json').write_text(json.dumps(hist,indent=2),encoding='utf-8')
    (out/'jepa_meta.json').write_text(json.dumps({'seed':seed,'device':str(device),'fit_pairs':len(fit_pair),'val_pairs':len(val_pair),'balanced_counts':counts,
        'micro_batch':batch,'effective_batch':effective_batch,'amp':amp,'trainable_parameters':sum(p.numel() for p in model.parameters())},indent=2),encoding='utf-8')
    return out/'jepa_best.pt'


def base_loader(ds,indices,batch,workers):
    return DataLoader(Subset(ds,indices),batch_size=batch,shuffle=False,num_workers=workers,
                      pin_memory=torch.cuda.is_available(),persistent_workers=(workers>0))


def encode_indices(base_cfg,checkpoint,ds,indices,batch,workers):
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu');ck=torch.load(checkpoint,map_location='cpu')
    enc=CausalPatchEncoder(base_cfg,len(FEATURE_NAMES));enc.load_state_dict(ck['encoder']);enc.to(device);enc.eval()
    dl=base_loader(ds,indices,batch,workers);zs=[];ys=[];ts=[];tis=[]
    with torch.no_grad():
        for b in dl:
            bb=move(b,device)
            with torch.amp.autocast(device_type=device.type,enabled=(device.type=='cuda')):z=enc(bb)
            zs.append(z.float().cpu().numpy());ys.append((b['y_norm'][:,0].numpy()>0).astype(np.float32));ts.append(b['decision_ns'].numpy());tis.append(b['target_mask'].numpy().argmax(1).astype(np.int16))
    return np.concatenate(zs),np.concatenate(ys),np.concatenate(ts),np.concatenate(tis)


class Probe(nn.Module):
    def __init__(self,d):super().__init__();self.linear=nn.Linear(d,1)
    def forward(self,x):return self.linear(x).squeeze(-1)


def train_probe(zf,yf,tif,zv,yv,seed,out,jepa_cfg):
    seed_all(seed);device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    counts={int(i):int((tif==i).sum()) for i in np.unique(tif)}
    weights=np.asarray([1.0/counts[int(i)] for i in tif],np.float64)
    td=TensorDataset(torch.from_numpy(zf.astype(np.float32)),torch.from_numpy(yf.astype(np.float32)))
    g=torch.Generator();g.manual_seed(seed);sampler=WeightedRandomSampler(torch.from_numpy(weights),num_samples=len(weights),replacement=True,generator=g)
    dl=DataLoader(td,batch_size=1024,sampler=sampler);zv_t=torch.from_numpy(zv.astype(np.float32));yv_t=torch.from_numpy(yv.astype(np.float32))
    model=Probe(zf.shape[1]).to(device);opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4)
    best=math.inf;pat=0;hist=[];maxep=int(jepa_cfg['training']['probe_max_epochs']);patlim=int(jepa_cfg['training']['probe_patience'])
    for ep in range(1,maxep+1):
        model.train();ls=[]
        for x,y in dl:
            x=x.to(device);y=y.to(device);logit=model(x);loss=torch.nn.functional.binary_cross_entropy_with_logits(logit,y)
            opt.zero_grad(set_to_none=True);loss.backward();opt.step();ls.append(float(loss.detach().cpu()))
        model.eval()
        with torch.no_grad():
            logit=model(zv_t.to(device));vl=float(torch.nn.functional.binary_cross_entropy_with_logits(logit,yv_t.to(device)).cpu())
            pv=torch.sigmoid(logit).cpu().numpy();auc=float(roc_auc_score(yv,pv))
        row={'epoch':ep,'fit_bce':float(np.mean(ls)),'inner_val_bce':vl,'inner_val_auc':auc};hist.append(row);print('PROBE',seed,row,flush=True)
        if vl<best-1e-6:
            best=vl;pat=0;torch.save({'probe':model.state_dict(),'seed':seed,'row':row},out/'probe_best.pt')
        else:
            pat+=1
            if pat>=patlim:break
    (out/'probe_history.json').write_text(json.dumps(hist,indent=2),encoding='utf-8')
    return out/'probe_best.pt'


def probe_predict(path,z):
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu');ck=torch.load(path,map_location='cpu');m=Probe(z.shape[1]);m.load_state_dict(ck['probe']);m.to(device);m.eval()
    outs=[]
    with torch.no_grad():
        for i in range(0,len(z),8192):outs.append(torch.sigmoid(m(torch.from_numpy(z[i:i+8192].astype(np.float32)).to(device))).cpu().numpy())
    return np.concatenate(outs)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--base-config',type=Path,required=True);ap.add_argument('--jepa-config',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--pretrain-batch-size',type=int,default=24);ap.add_argument('--encode-batch-size',type=int,default=64);ap.add_argument('--workers',type=int,default=0);ap.add_argument('--fold',default='ALL');ap.add_argument('--seeds',default='17,29,43')
    ap.add_argument('--diagnostic-cap-per-target-year',type=int,default=None);ap.add_argument('--diagnostic-pretrain-epochs',type=int,default=None)
    args=ap.parse_args();base_cfg=load_json(args.base_config);jc=load_json(args.jepa_config);seeds=[int(x) for x in args.seeds.split(',')]
    # Reuse the exact prepared-data identity authority used by R1.
    verification=verify_prepared_identity(args.prepared,args.base_config)
    official=(args.fold=='ALL' and seeds==jc['training']['seeds'] and args.diagnostic_cap_per_target_year is None and args.diagnostic_pretrain_epochs is None)
    args.out.mkdir(parents=True,exist_ok=True)
    run={'status':'OFFICIAL_STAGE_A' if official else 'DIAGNOSTIC','model':'V4_001_MarketJEPA','base_config_sha256':sha256_file(args.base_config),'jepa_config_sha256':sha256_file(args.jepa_config),
         'script_sha256':sha256_file(Path(__file__)),'model_script_sha256':sha256_file(HERE/'v4_001_jepa_model.py'),'torch':torch.__version__,'cuda_available':torch.cuda.is_available(),'cuda_device':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
         'pretraining_data_rule':'training allocation only; no outer data','probe':'frozen encoder + linear logistic head','data_verification':verification,'folds':fold_specs()}
    (args.out/'run_manifest.json').write_text(json.dumps(run,indent=2),encoding='utf-8')
    selected=[f for f in fold_specs() if args.fold=='ALL' or f['name']==args.fold]
    if not selected:raise SystemExit('unknown fold')
    allres={}
    for f in selected:
        print('\nJEPA FOLD',f['name'],flush=True)
        tr=CausalWindowDataset(args.prepared,base_cfg,f['train_context'],target_symbols=f['train_targets'],years=f['train_years'])
        fit,val,cut=chronological_inner_split(tr)
        fit=contiguous_cap(tr,fit,args.diagnostic_cap_per_target_year);val=contiguous_cap(tr,val,args.diagnostic_cap_per_target_year)
        ev=CausalWindowDataset(args.prepared,base_cfg,f['eval_context'],target_symbols=f['eval_targets'],years=f['eval_years']);eidx=list(range(len(ev)));eidx=contiguous_cap(ev,eidx,args.diagnostic_cap_per_target_year)
        fo=args.out/f['name'];fo.mkdir(parents=True,exist_ok=True);preds=[];base=None
        for seed in seeds:
            so=fo/f'seed_{seed}';ck=train_jepa(base_cfg,jc,tr,fit,val,seed,so,args.pretrain_batch_size,int(jc['training']['effective_batch_size']),args.workers,max_epochs_override=args.diagnostic_pretrain_epochs,min_pairs_fit=(10 if not official else 1000),min_pairs_val=(10 if not official else 200))
            zf,yf,tf,tif=encode_indices(base_cfg,ck,tr,fit,args.encode_batch_size,args.workers)
            zv,yv,tv,tiv=encode_indices(base_cfg,ck,tr,val,args.encode_batch_size,args.workers)
            ze,ye,te,tie=encode_indices(base_cfg,ck,ev,eidx,args.encode_batch_size,args.workers)
            pp=train_probe(zf,yf,tif,zv,yv,seed,so,jc);p=probe_predict(pp,ze);preds.append(p)
            sm=summary_metrics(ye,p,te,tie,f['eval_context']);(so/'outer_metrics.json').write_text(json.dumps(sm,indent=2),encoding='utf-8')
            if base is None:base=(ye,te,tie)
            # Do not retain huge latent matrices after the probe; checkpoints are enough for reproducibility.
            del zf,zv,ze
        ens=np.mean(np.stack(preds),axis=0);ye,te,tie=base;sm=summary_metrics(ye,ens,te,tie,f['eval_context'])
        sm.update({'fold':f['name'],'seeds':seeds,'inner_cutoff':str(pd.Timestamp(cut)),'fit_n':len(fit),'inner_val_n':len(val),'outer_n':len(eidx),'diagnostic_non_authority':not official})
        (fo/'ensemble_metrics.json').write_text(json.dumps(sm,indent=2),encoding='utf-8');allres[f['name']]=sm;print('JEPA ENSEMBLE',json.dumps(sm,indent=2),flush=True)
    (args.out/'stage_a_summary.json').write_text(json.dumps({'diagnostic_non_authority':not official,'folds':allres},indent=2),encoding='utf-8')
    print('JEPA STAGE-A COMPLETE official=',official)

if __name__=='__main__':main()
