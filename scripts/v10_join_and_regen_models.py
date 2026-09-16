#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,json,math,statistics,re
from pathlib import Path
from datetime import datetime


def read_csv(p):
 with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def norm_time(s):return s.replace('.','-')
def execution_signal_time(e):
 m=re.search(r'\beffective_ts=(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\b',e.get('entry_detail',''))
 return m.group(1) if m else e.get('decision_time','')
def fnum(x,default=0.0):
 try:return float(x)
 except:return default

def write_csv(path,rows,fields=None):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if fields is None:fields=list(rows[0]) if rows else []
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def percentile(vals,q):
 if not vals:return float('nan')
 a=sorted(vals);x=(len(a)-1)*q;lo=int(math.floor(x));hi=int(math.ceil(x))
 if lo==hi:return a[lo]
 return a[lo]*(hi-x)+a[hi]*(x-lo)

def auc(y,s):
 pairs=sorted(zip(s,y),key=lambda z:z[0]);n1=sum(y);n0=len(y)-n1
 if not n1 or not n0:return float('nan')
 rank_sum=0.0;i=0
 while i<len(pairs):
  j=i+1
  while j<len(pairs) and pairs[j][0]==pairs[i][0]:j+=1
  avg=(i+1+j)/2.0
  rank_sum+=avg*sum(pairs[k][1] for k in range(i,j));i=j
 return (rank_sum-n1*(n1+1)/2)/(n1*n0)

def fit_logistic(rows,features,label,l2=0.05,lr=0.08,iters=5000):
 # deterministic standardized batch gradient descent
 X=[];y=[]
 for r in rows:
  vals=[];ok=True
  for c in features:
   try:v=float(r[c]);
   except:ok=False;break
   if not math.isfinite(v):ok=False;break
   vals.append(v)
  if ok:X.append(vals);y.append(int(float(r[label])))
 if not X:raise ValueError('no training rows')
 p=len(features);means=[sum(x[j] for x in X)/len(X) for j in range(p)]
 stds=[]
 for j in range(p):
  v=sum((x[j]-means[j])**2 for x in X)/len(X);stds.append(math.sqrt(v) if v>1e-12 else 1.0)
 Z=[[(x[j]-means[j])/stds[j] for j in range(p)] for x in X]
 base=min(max(sum(y)/len(y),1e-6),1-1e-6);b=math.log(base/(1-base));w=[0.0]*p
 for it in range(iters):
  gb=0.0;gw=[0.0]*p
  for z,yy in zip(Z,y):
   a=b+sum(wj*zj for wj,zj in zip(w,z));a=max(-35,min(35,a));pr=1/(1+math.exp(-a));e=pr-yy;gb+=e
   for j in range(p):gw[j]+=e*z[j]
  n=len(Z);gb/=n
  maxg=abs(gb);neww=[]
  for j in range(p):
   g=gw[j]/n+l2*w[j];maxg=max(maxg,abs(g));neww.append(w[j]-lr*g)
  b-=lr*gb;w=neww
  if maxg<1e-7:break
 return {'features':features,'mean':means,'std':stds,'coef':w,'intercept':b,'train_n':len(y),'train_positive':sum(y),'iterations':it+1,'l2':l2}

def predict(model,row):
 a=model['intercept']
 for c,m,s,w in zip(model['features'],model['mean'],model['std'],model['coef']):a+=w*(float(row[c])-m)/s
 a=max(-35,min(35,a));return 1/(1+math.exp(-a))

def fold_id(ts):
 t=datetime.strptime(norm_time(ts),'%Y-%m-%d %H:%M:%S')
 if datetime(2025,7,1)<=t<datetime(2026,1,1):return '2025H2'
 if datetime(2026,1,1)<=t<datetime(2027,1,1):return '2026'
 return ''
def is_train_for(fold,ts):
 t=datetime.strptime(norm_time(ts),'%Y-%m-%d %H:%M:%S')
 if fold=='2025H2':return datetime(2025,1,1)<=t<datetime(2025,7,1)
 if fold=='2026':return datetime(2025,1,1)<=t<datetime(2026,1,1)
 return False

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--features',required=True);ap.add_argument('--execution',required=True);ap.add_argument('--out-dir',required=True)
 args=ap.parse_args();out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
 base_all=read_csv(args.baseline);base=[r for r in base_all if fnum(r.get('W'))>0]
 feat=read_csv(args.features);exe=read_csv(args.execution)
 if not(len(base)==len(feat)==len(exe)==1159):raise SystemExit(f'row count mismatch base={len(base)} feat={len(feat)} exe={len(exe)}')
 merged=[]
 for sid,(b,f,e) in enumerate(zip(base,feat,exe)):
  # hard parity checks
  if int(f['signal_id'])!=sid or int(e['signal_id'])!=sid:raise SystemExit('signal id mismatch')
  bt=norm_time(b['decision_ts']); et=norm_time(execution_signal_time(e)); ft=norm_time(f['decision_time'])
  if bt!=et:
   raise SystemExit(f'signal-clock mismatch sid {sid}: baseline={b["decision_ts"]} effective={execution_signal_time(e)} event={e.get("entry_event_time",e.get("decision_time",""))}')
  # A pre-hotfix feature ledger used the event-log timestamp.  It is safe only
  # when it equals the execution event timestamp; the features themselves use
  # completed M15/M30/H1/H4 bars and the merged research clock remains baseline.
  event_t=norm_time(e.get('entry_event_time',e.get('decision_time','')))
  if ft not in (bt,event_t):
   raise SystemExit(f'feature-clock mismatch sid {sid}: baseline={b["decision_ts"]} feature={f["decision_time"]} event={e.get("entry_event_time",e.get("decision_time",""))}')
  bd='LONG' if b['direction']=='UP' else 'SHORT'
  if bd!=f['direction'] or bd!=e['direction']:raise SystemExit(f'direction mismatch sid {sid}')
  if abs(fnum(b['W'])-fnum(f['units']))>1e-9:raise SystemExit(f'unit mismatch sid {sid}')
  if int(float(b['run_seq']))!=int(float(f['h4_fast_run_k'])) or int(float(b['final_run_len']))!=int(float(f['answer_final_run_len'])):
   raise SystemExit(f'run metadata mismatch sid {sid}')
  r={'signal_id':sid};r.update(b)
  for k,v in f.items():
   if k not in r:r[k]=v
  for k,v in e.items():
   if k not in r:r['actual_'+k if k not in ('signal_id',) else k]=v
  last=int(float(b['run_seq']))==int(float(b['final_run_len']));rr=fnum(b['R_child'])
  r['label_current_is_last_fast']=int(last);r['label_severe_loss']=int(rr<=-0.5);r['label_nha_shock']=int(last and rr<=-0.5)
  r['label_next_same_fast']=int(int(float(b['run_seq']))<int(float(b['final_run_len'])))
  r['label_third_fast_exists']=int(int(float(b['final_run_len']))>=3)
  r['reference_weighted_pnl']=fnum(b['natural_child_pnl_m1'])*fnum(b['W']);r['reference_weighted_r']=rr*fnum(b['W'])
  merged.append(r)
 write_csv(out/'V10_POST_HEAD_MODEL_REGEN_LEDGER_20260916.csv',merged)
 # reproducible candidate heads. These are NEW regeneration candidates, not claimed to equal lost session model.
 danger_features=['h1_risk_m1','h4_fast_body_to_range_signed',
  'm15_aligned_fraction','m15_transition_rate','m15_current_signed_streak','m15_body_to_range_mean_signed','m15_opposing_wick_share_mean',
  'm30_aligned_fraction','m30_transition_rate','m30_current_signed_streak','m30_body_to_range_mean_signed','m30_opposing_wick_share_mean',
  'h1_aligned_fraction','h1_transition_rate','h1_current_signed_streak','h1_body_to_range_mean_signed','h1_opposing_wick_share_mean']
 persist_features=['P_M','P_W','P_SUPPORT','h1_risk_m1','h4_fast_body_to_range_signed',
  'm15_aligned_fraction','m15_current_signed_streak','m15_body_to_range_mean_signed','m15_opposing_wick_share_mean',
  'm30_aligned_fraction','m30_current_signed_streak','m30_body_to_range_mean_signed','m30_opposing_wick_share_mean',
  'h1_aligned_fraction','h1_current_signed_streak','h1_body_to_range_mean_signed','h1_opposing_wick_share_mean']
 heads=[('K1_NHA_SHOCK_REGEN',1,'label_nha_shock',danger_features),('K2_PERSISTENCE_REGEN',2,'label_next_same_fast',persist_features)]
 coef_rows=[];score_rows=[];metric_rows=[]
 for head,stage,label,features in heads:
  stage_rows=[r for r in merged if int(float(r['run_seq']))==stage]
  for fold in ('2025H2','2026'):
   train=[r for r in stage_rows if is_train_for(fold,r['decision_ts'])]
   test=[r for r in stage_rows if fold_id(r['decision_ts'])==fold]
   if not train or not test:continue
   model=fit_logistic(train,features,label)
   train_scores=[predict(model,r) for r in train];test_scores=[predict(model,r) for r in test];ys=[int(r[label]) for r in test]
   qs={q:percentile(train_scores,q) for q in (0.75,0.80,0.85,0.875,0.90,0.925,0.95,0.975)}
   for c,m,s,w in zip(features,model['mean'],model['std'],model['coef']):coef_rows.append({'population':'BOUNDED_M3_SELECTED','head':head,'fold':fold,'feature':c,'train_mean':m,'train_std':s,'coefficient':w,'intercept':model['intercept'],'train_n':model['train_n'],'train_positive':model['train_positive'],'l2':model['l2'],'iterations':model['iterations']})
   for r,sc in zip(test,test_scores):
    rank=sum(v<=sc for v in train_scores)/len(train_scores)
    score_rows.append({'population':'BOUNDED_M3_SELECTED','head':head,'fold':fold,'signal_id':r['signal_id'],'decision_ts':r['decision_ts'],'run_seq':r['run_seq'],'final_run_len':r['final_run_len'],'label':r[label],'score':sc,'prior_percentile_rank':rank,'top10_prior':int(sc>=qs[0.90]),'top5_prior':int(sc>=qs[0.95]),'W':r['W'],'reference_weighted_pnl':r['reference_weighted_pnl'],'reference_weighted_r':r['reference_weighted_r']})
   metric_rows.append({'population':'BOUNDED_M3_SELECTED','head':head,'fold':fold,'train_n':len(train),'eval_n':len(test),'eval_positive':sum(ys),'eval_prevalence':sum(ys)/len(ys),'auc':auc(ys,test_scores),'train_q90':qs[0.90],'train_q95':qs[0.95]})
 write_csv(out/'V10_POST_HEAD_REGEN_MODEL_COEFFICIENTS_20260916.csv',coef_rows)
 write_csv(out/'V10_POST_HEAD_REGEN_SCORE_LEDGER_20260916.csv',score_rows)
 write_csv(out/'V10_POST_HEAD_REGEN_MODEL_METRICS_20260916.csv',metric_rows)
 # danger tail sweep on k1 head. Candidate is full bounded reference in each eval period minus vetoed weighted pnl.
 tail_rows=[];k1scores=[r for r in score_rows if r['head']=='K1_NHA_SHOCK_REGEN']
 for fold in ('2025H2','2026'):
  period=[r for r in merged if fold_id(r['decision_ts'])==fold]
  base_pnl=sum(float(r['reference_weighted_pnl']) for r in period)
  srows=[r for r in k1scores if r['fold']==fold]
  for tail in (0.025,0.05,0.075,0.10,0.125,0.15,0.20,0.25):
   veto=[r for r in srows if float(r['prior_percentile_rank'])>=1-tail]
   removed=sum(float(r['reference_weighted_pnl']) for r in veto);removed_r=sum(float(r['reference_weighted_r']) for r in veto)
   tail_rows.append({'population':'BOUNDED_M3_SELECTED','fold':fold,'tail_fraction':tail,'veto_events':len(veto),'veto_units':sum(float(r['W']) for r in veto),'removed_reference_pnl':removed,'removed_reference_r':removed_r,'candidate_pnl_after_veto':base_pnl-removed,'delta_vs_base':-removed,'nha_shock_labels':sum(int(r['label']) for r in veto)})
 write_csv(out/'V10_K1_DANGER_REGEN_TAIL_SWEEP_20260916.csv',tail_rows)
 # summary json
 summary={'merged_rows':len(merged),'heads':metric_rows,'danger_features':danger_features,'persistence_features':persist_features,'population':'BOUNDED_M3_SELECTED','important_note':'These are selection-conditioned reproducible regeneration candidates on the bounded-m3 selected population. They are NOT asserted to reproduce the lost post-HEAD fitted coefficients or full ALL1-universe models.'}
 (out/'V10_POST_HEAD_REGEN_VALIDATION_20260916.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
