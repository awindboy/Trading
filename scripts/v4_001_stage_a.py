#!/usr/bin/env python3
"""V4-001A authoritative Stage-A runner.

Key protections compared with the bootstrap low-level trainer:
- outer evaluation data is NEVER used for early stopping;
- inner validation is chronological with a 7-day purge;
- primary leave-one-market-out folds are also future-isolated (train other markets 2023-24 -> held-out market 2025);
- three frozen seeds are ensembled; no lucky-seed selection;
- Stage A reports information skill only; it does not run the economic controller.

The model architecture/config is unchanged from V4_001_CausalPatchPolicy.
"""
from __future__ import annotations
from pathlib import Path
import argparse, copy, json, math, random, sys, time, hashlib, platform
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Subset, WeightedRandomSampler
from sklearn.metrics import roc_auc_score, brier_score_loss

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from v4_001_common import CausalWindowDataset, FEATURE_NAMES
from v4_001_model import CausalPatchPolicy, multitask_loss

ALL_SYMBOLS=['GOLD#','BTCUSD#','XAUEUR#','USDJPY#']
PURGE_DAYS=7
INNER_VAL_FRACTION=0.20
BOOTSTRAP_REPS=1000


def sha256_file(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def verify_prepared_identity(prepared_root:Path, config_path:Path):
    auth_path=HERE.parent/'docs/ea/v4/V4_001A_PREPARED_DATA_MANIFEST.json'
    prep_path=prepared_root/'prepared_manifest.json'
    if not auth_path.exists():
        raise SystemExit(f'FAIL-CLOSED missing authority data manifest: {auth_path}')
    if not prep_path.exists():
        raise SystemExit(f'FAIL-CLOSED missing prepared manifest: {prep_path}')
    auth=json.loads(auth_path.read_text(encoding='utf-8')); prep=json.loads(prep_path.read_text(encoding='utf-8'))
    if sha256_file(config_path)!=auth['config_sha256']:
        raise SystemExit('FAIL-CLOSED config SHA-256 differs from frozen V4-001A authority')
    errors=[]
    for sym,exp in auth['symbols'].items():
        got=prep.get('symbols',{}).get(sym)
        if not got: errors.append(f'{sym}: missing prepared symbol'); continue
        for k in ['point','rows_m1']:
            if got.get(k)!=exp.get(k): errors.append(f'{sym}: {k} expected {exp.get(k)} got {got.get(k)}')
        if got.get('decisions',{}).get('rows')!=exp.get('decisions',{}).get('rows'):
            errors.append(f"{sym}: decision rows expected {exp['decisions']['rows']} got {got.get('decisions',{}).get('rows')}")
        for tf,e in exp['streams'].items():
            g=got.get('streams',{}).get(tf,{})
            for k in ['rows','valid','feature_dim']:
                if g.get(k)!=e.get(k): errors.append(f'{sym}/{tf}: {k} expected {e.get(k)} got {g.get(k)}')
    exp_hash={s:sorted(x['sha256'] for x in auth['raw_files'] if x['symbol']==s) for s in auth['symbols']}
    got_hash={s:sorted(x['sha256'] for x in prep.get('raw_files',[]) if x['symbol']==s) for s in auth['symbols']}
    for s in exp_hash:
        if exp_hash[s]!=got_hash[s]: errors.append(f'{s}: raw-file SHA-256 set differs')
    if errors: raise SystemExit('FAIL-CLOSED prepared-data identity mismatch:\n- '+'\n- '.join(errors))
    return {'authority_manifest':str(auth_path),'prepared_manifest':str(prep_path),'raw_hashes_match':True,'counts_match':True,'config_hash_match':True}


def seed_all(seed:int):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def move(batch,device):
    out={}
    for k,v in batch.items():
        if isinstance(v,dict): out[k]={a:b.to(device,non_blocking=True) for a,b in v.items()}
        elif torch.is_tensor(v): out[k]=v.to(device,non_blocking=True)
        else: out[k]=v
    return out


def target_of(sample): return sample[0]
def time_of(sample): return int(sample[2])


def chronological_inner_split(ds:CausalWindowDataset):
    unique_t=np.array(sorted({time_of(s) for s in ds.samples}),dtype=np.int64)
    if len(unique_t)<100:
        raise RuntimeError('too few training timestamps for inner split')
    cut=int(unique_t[min(len(unique_t)-1,max(1,int((1-INNER_VAL_FRACTION)*len(unique_t))))])
    purge=int(pd.Timedelta(days=PURGE_DAYS).value)
    fit=[i for i,s in enumerate(ds.samples) if time_of(s)<=cut-purge]
    val=[i for i,s in enumerate(ds.samples) if time_of(s)>=cut+purge]
    if not fit or not val: raise RuntimeError('inner split empty')
    return fit,val,cut


def stratified_cap(ds, indices, cap_per_target_year:int|None, seed:int):
    if not cap_per_target_year: return list(indices)
    g={}
    for i in indices:
        s=ds.samples[i]; key=(target_of(s),pd.Timestamp(time_of(s)).year);g.setdefault(key,[]).append(i)
    rng=np.random.default_rng(seed);out=[]
    for key,ix in sorted(g.items()):
        if len(ix)>cap_per_target_year:
            ix=np.asarray(ix); ix=rng.choice(ix,size=cap_per_target_year,replace=False).tolist()
        out.extend(ix)
    return sorted(out,key=lambda i:time_of(ds.samples[i]))


def balanced_sampler(ds, indices, seed):
    counts={}
    for i in indices: counts[target_of(ds.samples[i])]=counts.get(target_of(ds.samples[i]),0)+1
    w=torch.tensor([1.0/counts[target_of(ds.samples[i])] for i in indices],dtype=torch.double)
    gen=torch.Generator();gen.manual_seed(seed)
    return WeightedRandomSampler(w,num_samples=len(indices),replacement=True,generator=gen),counts


def eval_loader(model,dl,cfg,device):
    model.eval(); probs=[];ys=[];times=[];targets=[];mus=[];raw=[]; nll_sum=0.; n=0
    with torch.no_grad():
        for b in dl:
            bb=move(b,device);o=model(bb)
            y=bb['y_norm'].float();scale=torch.exp(o['logscale']).clamp_min(1e-4)
            per=(0.5*((y-o['mu'])/scale)**2+o['logscale']).mean(1)
            nll_sum += float(per.sum().cpu()); n+=len(per)
            p=torch.sigmoid(o['direction_logit'][:,0]).cpu().numpy()
            probs.append(p);ys.append((b['y_norm'][:,0].numpy()>0).astype(np.uint8))
            times.append(b['decision_ns'].numpy())
            ti=b['target_mask'].numpy().argmax(1);targets.append(ti.astype(np.int8))
            mus.append(o['mu'][:,0].cpu().numpy());raw.append(b['y_raw'][:,0].numpy())
    p=np.concatenate(probs);y=np.concatenate(ys);t=np.concatenate(times);ti=np.concatenate(targets);mu=np.concatenate(mus);r=np.concatenate(raw)
    auc=float(roc_auc_score(y,p)) if len(np.unique(y))==2 else math.nan
    return {'nll':nll_sum/max(n,1),'auc':auc,'p':p,'y':y,'t':t,'target_idx':ti,'mu_norm':mu,'raw':r}


def make_loader(ds,indices,batch,workers,shuffle=False,sampler=None):
    return DataLoader(Subset(ds,indices),batch_size=batch,shuffle=(shuffle and sampler is None),sampler=sampler,
                      num_workers=workers,pin_memory=torch.cuda.is_available(),persistent_workers=(workers>0))


def train_one(cfg,train_ds,fit_idx,val_idx,seed,out,batch_size,effective_batch,workers,max_epochs):
    seed_all(seed);device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    sampler,counts=balanced_sampler(train_ds,fit_idx,seed)
    fit_dl=make_loader(train_ds,fit_idx,batch_size,workers,sampler=sampler)
    val_dl=make_loader(train_ds,val_idx,batch_size,workers)
    model=CausalPatchPolicy(cfg,len(FEATURE_NAMES)).to(device)
    opt=torch.optim.AdamW(model.parameters(),lr=cfg['optimizer']['lr'],weight_decay=cfg['optimizer']['weight_decay'])
    accum=max(1,math.ceil(effective_batch/batch_size))
    amp=(device.type=='cuda'); scaler=torch.amp.GradScaler('cuda',enabled=amp)
    best=math.inf;pat=0;history=[];out.mkdir(parents=True,exist_ok=True)
    for epoch in range(1,max_epochs+1):
        model.train();opt.zero_grad(set_to_none=True);ls=[];steps=0
        for bi,b in enumerate(fit_dl,1):
            bb=move(b,device)
            with torch.amp.autocast(device_type=device.type,enabled=amp):
                o=model(bb);loss,_=multitask_loss(o,bb,cfg);scaled_loss=loss/accum
            scaler.scale(scaled_loss).backward();ls.append(float(loss.detach().cpu()))
            if bi%accum==0 or bi==len(fit_dl):
                scaler.unscale_(opt);torch.nn.utils.clip_grad_norm_(model.parameters(),cfg['optimizer']['grad_clip'])
                scaler.step(opt);scaler.update();opt.zero_grad(set_to_none=True);steps+=1
        vv=eval_loader(model,val_dl,cfg,device)
        row={'epoch':epoch,'fit_loss':float(np.mean(ls)),'inner_val_nll':vv['nll'],'inner_val_auc15':vv['auc'],'optimizer_steps':steps}
        history.append(row);print('seed',seed,row,flush=True)
        if vv['nll']<best-1e-5:
            best=vv['nll'];pat=0;torch.save({'model':model.state_dict(),'config':cfg,'seed':seed,'row':row},out/'best.pt')
        else:
            pat+=1
            if pat>=cfg['training']['early_stop_patience']: break
    (out/'history.json').write_text(json.dumps(history,indent=2),encoding='utf-8')
    (out/'train_meta.json').write_text(json.dumps({'seed':seed,'device':str(device),'fit_n':len(fit_idx),'inner_val_n':len(val_idx),
        'balanced_target_counts':counts,'micro_batch':batch_size,'effective_batch':effective_batch,'amp':amp,'parameter_count':sum(p.numel() for p in model.parameters())},indent=2),encoding='utf-8')
    return out/'best.pt'


def eval_checkpoint(cfg,checkpoint,eval_ds,eval_idx,batch_size,workers):
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu');ck=torch.load(checkpoint,map_location='cpu')
    model=CausalPatchPolicy(cfg,len(FEATURE_NAMES));model.load_state_dict(ck['model']);model.to(device)
    dl=make_loader(eval_ds,eval_idx,batch_size,workers)
    return eval_loader(model,dl,cfg,device)


def ece(y,p,bins=10):
    edges=np.linspace(0,1,bins+1);z=0.
    for i in range(bins):
        m=(p>=edges[i])&(p<(edges[i+1] if i<bins-1 else edges[i+1]+1e-12))
        if m.any(): z+=m.mean()*abs(p[m].mean()-y[m].mean())
    return float(z)


def weekly_bootstrap_auc(y,p,t,reps=BOOTSTRAP_REPS,seed=90210):
    dt=pd.to_datetime(t);week=np.asarray(dt.to_period('W-MON').astype(str));u=np.unique(week);groups={w:np.where(week==w)[0] for w in u}
    rng=np.random.default_rng(seed);vals=[]
    for _ in range(reps):
        draw=rng.choice(u,size=len(u),replace=True);ix=np.concatenate([groups[w] for w in draw])
        if len(np.unique(y[ix]))==2: vals.append(roc_auc_score(y[ix],p[ix]))
    return [float(np.quantile(vals,.025)),float(np.quantile(vals,.975))] if vals else [math.nan,math.nan]


def summary_metrics(y,p,t,target_idx,symbols):
    out={'n':int(len(y)),'auc15':float(roc_auc_score(y,p)),'brier15':float(brier_score_loss(y,p)),'ece10':ece(y,p),
         'weekly_block_auc95':weekly_bootstrap_auc(y,p,t),'by_target':{}}
    for i,s in enumerate(symbols):
        m=target_idx==i
        if m.any(): out['by_target'][s]={'n':int(m.sum()),'auc15':float(roc_auc_score(y[m],p[m])),'brier15':float(brier_score_loss(y[m],p[m]))}
    return out


def fold_specs():
    fs=[
      {'name':'TEMPORAL_2024','train_context':ALL_SYMBOLS,'train_targets':ALL_SYMBOLS,'train_years':[2023],
       'eval_context':ALL_SYMBOLS,'eval_targets':ALL_SYMBOLS,'eval_years':[2024]},
      {'name':'TEMPORAL_2025_PRIMARY','train_context':ALL_SYMBOLS,'train_targets':ALL_SYMBOLS,'train_years':[2023,2024],
       'eval_context':ALL_SYMBOLS,'eval_targets':ALL_SYMBOLS,'eval_years':[2025]},
    ]
    for hold in ALL_SYMBOLS:
        train=[s for s in ALL_SYMBOLS if s!=hold]
        fs.append({'name':'LOMO_FUTURE_2025_'+hold,'train_context':train,'train_targets':train,'train_years':[2023,2024],
                   'eval_context':ALL_SYMBOLS,'eval_targets':[hold],'eval_years':[2025]})
    return fs


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--config',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--batch-size',type=int,default=64);ap.add_argument('--effective-batch-size',type=int,default=256);ap.add_argument('--workers',type=int,default=0)
    ap.add_argument('--seeds',default='17,29,43');ap.add_argument('--fold',default='ALL');ap.add_argument('--max-epochs',type=int,default=None)
    ap.add_argument('--bootstrap-reps',type=int,default=1000);ap.add_argument('--diagnostic-cap-fit-per-target-year',type=int,default=None);ap.add_argument('--diagnostic-cap-val-per-target-year',type=int,default=None);ap.add_argument('--diagnostic-cap-eval-per-target-year',type=int,default=None)
    args=ap.parse_args();
    global BOOTSTRAP_REPS; BOOTSTRAP_REPS=args.bootstrap_reps
    cfg=json.loads(args.config.read_text());seeds=[int(x) for x in args.seeds.split(',')];max_epochs=args.max_epochs or cfg['training']['max_epochs']
    data_verification=verify_prepared_identity(args.prepared,args.config)
    args.out.mkdir(parents=True,exist_ok=True);allres={}
    prep_manifest=args.prepared/'prepared_manifest.json'
    run_manifest={
      'status':'DIAGNOSTIC' if (args.max_epochs is not None or args.seeds!=','.join(map(str,cfg['training']['seeds'])) or args.fold!='ALL' or args.bootstrap_reps!=1000 or any(x is not None for x in [args.diagnostic_cap_fit_per_target_year,args.diagnostic_cap_val_per_target_year,args.diagnostic_cap_eval_per_target_year])) else 'OFFICIAL_STAGE_A',
      'config_path':str(args.config),'config_sha256':sha256_file(args.config),
      'prepared_manifest_sha256':sha256_file(prep_manifest) if prep_manifest.exists() else None,
      'stage_a_script_sha256':sha256_file(Path(__file__)),
      'common_sha256':sha256_file(HERE/'v4_001_common.py'),'model_sha256':sha256_file(HERE/'v4_001_model.py'),
      'python':platform.python_version(),'torch':torch.__version__,'cuda_available':torch.cuda.is_available(),
      'cuda_device':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
      'inner_val_fraction':INNER_VAL_FRACTION,'purge_days':PURGE_DAYS,'bootstrap_reps':BOOTSTRAP_REPS,
      'seed_aggregation':'arithmetic_mean_probability','market_balanced_fit_sampler':True,
      'folds':fold_specs(),'data_verification':data_verification,
    }
    (args.out/'run_manifest.json').write_text(json.dumps(run_manifest,indent=2),encoding='utf-8')
    selected=[f for f in fold_specs() if args.fold=='ALL' or f['name']==args.fold]
    if not selected: raise SystemExit('unknown fold')
    diagnostic=any(x is not None for x in [args.diagnostic_cap_fit_per_target_year,args.diagnostic_cap_val_per_target_year,args.diagnostic_cap_eval_per_target_year]) or max_epochs!=cfg['training']['max_epochs'] or seeds!=cfg['training']['seeds'] or args.fold!='ALL' or args.bootstrap_reps!=1000
    for f in selected:
        print('\nFOLD',f['name'],flush=True)
        tr=CausalWindowDataset(args.prepared,cfg,f['train_context'],target_symbols=f['train_targets'],years=f['train_years'])
        fit,val,cut=chronological_inner_split(tr)
        fit=stratified_cap(tr,fit,args.diagnostic_cap_fit_per_target_year,111)
        val=stratified_cap(tr,val,args.diagnostic_cap_val_per_target_year,222)
        ev=CausalWindowDataset(args.prepared,cfg,f['eval_context'],target_symbols=f['eval_targets'],years=f['eval_years'])
        eidx=list(range(len(ev)));eidx=stratified_cap(ev,eidx,args.diagnostic_cap_eval_per_target_year,333)
        foldout=args.out/f['name'];foldout.mkdir(parents=True,exist_ok=True)
        seed_preds=[];base=None
        for seed in seeds:
            ck=train_one(cfg,tr,fit,val,seed,foldout/f'seed_{seed}',args.batch_size,args.effective_batch_size,args.workers,max_epochs)
            pr=eval_checkpoint(cfg,ck,ev,eidx,args.batch_size,args.workers)
            np.savez_compressed(foldout/f'seed_{seed}'/'outer_predictions.npz',p=pr['p'],y=pr['y'],t=pr['t'],target_idx=pr['target_idx'],mu_norm=pr['mu_norm'],raw=pr['raw'])
            seed_preds.append(pr['p']);
            if base is None: base=pr
            sm=summary_metrics(pr['y'],pr['p'],pr['t'],pr['target_idx'],f['eval_context']);(foldout/f'seed_{seed}'/'outer_metrics.json').write_text(json.dumps(sm,indent=2))
        ens=np.mean(np.stack(seed_preds),axis=0)
        sm=summary_metrics(base['y'],ens,base['t'],base['target_idx'],f['eval_context'])
        sm.update({'fold':f['name'],'seeds':seeds,'inner_cutoff':str(pd.Timestamp(cut)),'purge_days':PURGE_DAYS,'fit_n':len(fit),'inner_val_n':len(val),'outer_n':len(eidx),'diagnostic_non_authority':diagnostic})
        (foldout/'ensemble_metrics.json').write_text(json.dumps(sm,indent=2));allres[f['name']]=sm;print('ENSEMBLE',json.dumps(sm,indent=2),flush=True)
    (args.out/'stage_a_summary.json').write_text(json.dumps({'diagnostic_non_authority':diagnostic,'folds':allres},indent=2))
    print('STAGE-A RUN COMPLETE diagnostic_non_authority=',diagnostic)

if __name__=='__main__': main()
