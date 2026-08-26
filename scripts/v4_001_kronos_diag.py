#!/usr/bin/env python3
"""R3 Kronos-mini zero-shot transfer diagnostic.

NON-CLAIM-GRADE by design: Kronos' exact pretraining temporal coverage is not known
well enough for our 2023-2025 broker data to be treated as pristine OOS.  This runner
asks only whether a finance-native pretrained K-line model contains useful transferable
signal on the same broker environment.
"""
from pathlib import Path
import argparse,json,math,random,sys
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from v4_001_common import load_symbol,resample_bars


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--data-map',type=Path,required=True);ap.add_argument('--vendor-kronos',type=Path,required=True);ap.add_argument('--diag-config',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 cfg=json.loads(a.diag_config.read_text(encoding='utf-8'))['kronos'];dm=json.loads(a.data_map.read_text(encoding='utf-8'))
 if not a.vendor_kronos.exists():raise SystemExit('Kronos vendor directory missing; run tools/install_external_models.ps1')
 sys.path.insert(0,str(a.vendor_kronos.resolve()))
 try: from model import Kronos,KronosTokenizer,KronosPredictor
 except Exception as e: raise SystemExit(f'Kronos import failed: {e}')
 random.seed(17);np.random.seed(17);torch.manual_seed(17)
 if torch.cuda.is_available():torch.cuda.manual_seed_all(17)
 device='cuda:0' if torch.cuda.is_available() else 'cpu'
 tokenizer=KronosTokenizer.from_pretrained(cfg['tokenizer']);model=Kronos.from_pretrained(cfg['model'])
 predictor=KronosPredictor(model,tokenizer,device=device,max_context=2048)
 out={'authority':'TRANSFER_DIAGNOSTIC_ONLY','device':device,'config':cfg,'by_symbol':{}}
 all_y=[];all_s=[]
 for sym,spec in dm.items():
  raw=load_symbol([Path(x) for x in spec['files']]);bars=resample_bars(raw,'15min');op=pd.Series(raw.open.to_numpy(float),index=raw.index)
  candidates=[]
  for t in bars.index[(bars.index.year==int(cfg['year']))]:
   if t not in op.index or t+pd.Timedelta(minutes=15) not in op.index:continue
   pos=bars.index.searchsorted(t,side='left')
   if pos<int(cfg['lookback_bars']):continue
   candidates.append((t,pos))
  cap=int(cfg['max_decisions_per_symbol'])
  if len(candidates)>cap:
   take=np.unique(np.linspace(0,len(candidates)-1,cap).round().astype(int));candidates=[candidates[i] for i in take]
  ys=[];scores=[];errors=0
  for k,(t,pos) in enumerate(candidates,1):
   q=bars.iloc[pos-int(cfg['lookback_bars']):pos]
   x_df=q[['open','high','low','close']].reset_index(drop=True);x_ts=pd.Series(q.index);y_ts=pd.Series([t])
   try:
    pred=predictor.predict(df=x_df,x_timestamp=x_ts,y_timestamp=y_ts,pred_len=1,T=float(cfg['temperature']),top_p=float(cfg['top_p']),sample_count=int(cfg['sample_count']))
    pc=float(pred['close'].iloc[-1]);entry=float(op.loc[t]);future=float(op.loc[t+pd.Timedelta(minutes=15)])
    scores.append(math.log(max(pc,1e-12)/max(entry,1e-12)));ys.append(int(future>entry))
   except Exception as e:
    errors+=1
    if errors<=3: print(sym,'prediction error',repr(e),flush=True)
   if k%250==0:print(sym,k,'/',len(candidates),flush=True)
  auc=float(roc_auc_score(ys,scores)) if len(set(ys))==2 else math.nan
  out['by_symbol'][sym]={'n':len(ys),'errors':errors,'auc15_direction':auc,'positive_rate':float(np.mean(ys)) if ys else math.nan}
  all_y.extend(ys);all_s.extend(scores);print(sym,out['by_symbol'][sym],flush=True)
 out['pooled_auc15_direction']=float(roc_auc_score(all_y,all_s)) if len(set(all_y))==2 else math.nan
 a.out.write_text(json.dumps(out,indent=2),encoding='utf-8');print('KRONOS DIAGNOSTIC',a.out.resolve())
if __name__=='__main__':main()
