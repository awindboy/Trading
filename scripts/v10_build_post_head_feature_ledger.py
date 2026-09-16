#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,hashlib,json,math,re
from pathlib import Path
from datetime import datetime,timedelta
from bisect import bisect_right

EXPECTED_HASHES={
 'm15':'245902105a2c36a627768f979584984944aabc9e62dfa3cfc9acb3198544c269',
 'm30':'8a3124d0f67ec6f8729b495011899cd4ca4fb5fd723dce7998f09614a12a1022',
 'h1':'c1d9f63f8af4d7dddd9e20e6eb124dc71de51015384b9c61a772d5981c7be52c',
 'h4':'5e12fa91f974c0f15e340ea8116bd9168fc6821e6309592cee1a7e197675de09',
 'events':'eea7f54a4f0a70aa3c3ea52b38163f95fe8f79de93cdf0ccf8d73cc8fcc91f69',
}
ENTRY_EVENTS={'ENTRY_FILL','ENTRY_REJECT','ENTRY_REJECT_SL_ALREADY_TOUCHED'}

def sha256(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def parse_dt(date,time): return datetime.strptime(date+' '+time,'%Y.%m.%d %H:%M:%S')
def read_bars(path):
 out=[]
 with open(path,encoding='utf-8-sig',newline='') as f:
  rd=csv.DictReader(f,delimiter='\t')
  for r in rd:
   out.append({'time':parse_dt(r['<DATE>'],r['<TIME>']),'o':float(r['<OPEN>']),'h':float(r['<HIGH>']),'l':float(r['<LOW>']),'c':float(r['<CLOSE>'])})
 return out

def heikin(bars,w=1.0,alpha=0.5):
 # HC=(O+H+L+w*C)/(3+w); HO_t=alpha*HO_prev+(1-alpha)*HC_prev
 out=[];prev_ho=None;prev_hc=None
 for i,b in enumerate(bars):
  hc=(b['o']+b['h']+b['l']+w*b['c'])/(3.0+w)
  if i==0:ho=(b['o']+b['c'])/2.0
  else:ho=alpha*prev_ho+(1-alpha)*prev_hc
  hh=max(b['h'],ho,hc);ll=min(b['l'],ho,hc)
  d=1 if hc>=ho else -1
  out.append({**b,'ha_open':ho,'ha_close':hc,'ha_high':hh,'ha_low':ll,'ha_dir':d,'ha_body':hc-ho})
  prev_ho,prev_hc=ho,hc
 return out

def wilder_atr(bars,n=180):
 tr=[]
 for i,b in enumerate(bars):
  if i==0:t=b['h']-b['l']
  else:
   pc=bars[i-1]['c'];t=max(b['h']-b['l'],abs(b['h']-pc),abs(b['l']-pc))
  tr.append(t)
 out=[None]*len(bars)
 if len(bars)>=n:
  a=sum(tr[:n])/n;out[n-1]=a
  for i in range(n,len(bars)):
   a=(a*(n-1)+tr[i])/n;out[i]=a
 return out

def run_meta(dirs):
 k=[0]*len(dirs);L=[0]*len(dirs);rid=[0]*len(dirs)
 s=0;run=0
 while s<len(dirs):
  e=s+1
  while e<len(dirs) and dirs[e]==dirs[s]:e+=1
  run+=1;ln=e-s
  for i in range(s,e):k[i]=i-s+1;L[i]=ln;rid[i]=run
  s=e
 return k,L,rid

def window_features(seq,primary_dir):
 if not seq:return {k:'' for k in feature_names('x')}
 signs=[primary_dir*x['ha_dir'] for x in seq] # + aligned, - opposed
 # runs in signed alignment
 runs=[];st=0
 for i in range(1,len(signs)+1):
  if i==len(signs) or signs[i]!=signs[st]:
   runs.append((signs[st],i-st));st=i
 same=[ln for sg,ln in runs if sg>0];opp=[ln for sg,ln in runs if sg<0]
 trans=sum(signs[i]!=signs[i-1] for i in range(1,len(signs)))
 signed_bodies=[];signed_body_range=[];oppwick=[];noopp=[]
 for x in seq:
  body=primary_dir*(x['ha_close']-x['ha_open']);signed_bodies.append(body)
  rng=max(x['ha_high']-x['ha_low'],1e-12);signed_body_range.append(body/rng)
  if primary_dir>0: wick=max(0,min(x['ha_open'],x['ha_close'])-x['ha_low'])
  else: wick=max(0,x['ha_high']-max(x['ha_open'],x['ha_close']))
  sh=wick/rng;oppwick.append(sh);noopp.append(sh<=1e-10)
 absbody=sum(abs(x) for x in signed_bodies)
 last=signs[-1];cur=0
 for s in reversed(signs):
  if s==last:cur+=1
  else:break
 cur_signed=cur if last>0 else -cur
 return {
  'count':len(seq),'aligned_fraction':sum(s>0 for s in signs)/len(signs),'transition_rate':trans/max(1,len(signs)-1),
  'mean_same_run_len':sum(same)/len(same) if same else 0.0,'mean_opp_run_len':sum(opp)/len(opp) if opp else 0.0,
  'max_same_run_len':max(same) if same else 0,'max_opp_run_len':max(opp) if opp else 0,
  'length_advantage':(max(same) if same else 0)-(max(opp) if opp else 0),'current_signed_streak':cur_signed,
  'body_sum_signed':sum(signed_bodies),'body_mean_signed':sum(signed_bodies)/len(signed_bodies),'body_flow_eff':sum(signed_bodies)/(absbody if absbody else 1.0),
  'body_to_range_mean_signed':sum(signed_body_range)/len(signed_body_range),'opposing_wick_share_mean':sum(oppwick)/len(oppwick),
  'no_opposing_wick_fraction':sum(noopp)/len(noopp)
 }

def feature_names(prefix):
 names=['count','aligned_fraction','transition_rate','mean_same_run_len','mean_opp_run_len','max_same_run_len','max_opp_run_len','length_advantage','current_signed_streak','body_sum_signed','body_mean_signed','body_flow_eff','body_to_range_mean_signed','opposing_wick_share_mean','no_opposing_wick_fraction']
 return [prefix+'_'+x for x in names]

def prefixed(prefix,d):return {prefix+'_'+k:v for k,v in d.items()}

def read_events(path):
 with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def entry_effective_time(r):
 m=re.search(r'\beffective_ts=(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\b',r.get('detail',''))
 return m.group(1) if m else r['time']

def main():
 ap=argparse.ArgumentParser();
 ap.add_argument('--events',required=True);ap.add_argument('--m15',required=True);ap.add_argument('--m30',required=True);ap.add_argument('--h1',required=True);ap.add_argument('--h4',required=True);ap.add_argument('--out',required=True);ap.add_argument('--skip-hash-check',action='store_true')
 args=ap.parse_args()
 paths={k:Path(getattr(args,k)) for k in ('events','m15','m30','h1','h4')}
 if not args.skip_hash_check:
  bad=[]
  for k,p in paths.items():
   got=sha256(p); exp=EXPECTED_HASHES[k]
   if got!=exp:bad.append((k,got,exp))
  if bad:raise SystemExit('SHA256 mismatch: '+repr(bad))
 events=read_events(paths['events']);entries=[r for r in events if r['event'] in ENTRY_EVENTS]
 if len(entries)!=1159:raise SystemExit(f'expected 1159 entry events, got {len(entries)}')
 for i,r in enumerate(entries):r['signal_id']=i
 # bars and HA
 raw_h4=read_bars(paths['h4']);h4=heikin(raw_h4,w=2,alpha=0.25);atr=wilder_atr(raw_h4,180);k,L,rid=run_meta([x['ha_dir'] for x in h4])
 for i,x in enumerate(h4):x.update({'end':x['time']+timedelta(hours=4),'run_k':k[i],'run_L':L[i],'run_id_ha':rid[i],'atr180':atr[i]})
 h4_ends=[x['end'] for x in h4]
 tf={
  'm15':heikin(read_bars(paths['m15']),w=2,alpha=0.25),
  'm30':heikin(read_bars(paths['m30']),w=2,alpha=0.25),
  'h1':heikin(read_bars(paths['h1']),w=1,alpha=0.5),
 }
 # index by open time for fast slicing
 tf_times={name:[x['time'] for x in seq] for name,seq in tf.items()}
 rows=[];mismatch=[]
 for e in entries:
  effective_time=entry_effective_time(e)
  t=datetime.strptime(effective_time,'%Y.%m.%d %H:%M:%S')
  hi=bisect_right(h4_ends,t)-1
  if hi<0:raise SystemExit('no completed H4 for '+effective_time)
  hb=h4[hi]; pdir=1 if e['direction']=='LONG' else -1
  if hb['ha_dir']!=pdir:mismatch.append((e['signal_id'],effective_time,e['direction'],hb['time'].isoformat(),hb['ha_dir']))
  rec={
   'signal_id':e['signal_id'],'decision_time':effective_time,'entry_event':e['event'],'direction':e['direction'],'units':round(float(e['volume'])/0.01) if float(e['volume']) else 0,
   'event_price':float(e['price'] or 0),'structural_sl':float(e['structural_sl'] or 0),
   'h4_source_open':hb['time'].strftime('%Y-%m-%d %H:%M:%S'),'h4_source_end':hb['end'].strftime('%Y-%m-%d %H:%M:%S'),
   'h4_fast_dir':'LONG' if hb['ha_dir']>0 else 'SHORT','h4_fast_run_k':hb['run_k'],'answer_final_run_len':hb['run_L'],'answer_future_remaining_h4':hb['run_L']-hb['run_k'],
   'h4_fast_body_signed':pdir*hb['ha_body'],'h4_fast_body_to_range_signed':pdir*hb['ha_body']/max(hb['ha_high']-hb['ha_low'],1e-12),
   'era_scale_prev_h4_atr180':atr[hi-1] if hi-1>=0 and atr[hi-1] is not None else '',
  }
  if rec['era_scale_prev_h4_atr180']!='':rec['era_risk_event_price']=abs(rec['event_price']-rec['structural_sl'])/rec['era_scale_prev_h4_atr180']
  else:rec['era_risk_event_price']=''
  for name,seq in tf.items():
   times=tf_times[name];a=bisect_right(times,hb['time']-timedelta(microseconds=1));b=bisect_right(times,hb['end']-timedelta(microseconds=1));win=seq[a:b]
   rec.update(prefixed(name,window_features(win,pdir)))
  rows.append(rec)
 if mismatch:
  # Any mismatch is serious; write details in message and fail rather than silently creating wrong research data.
  raise SystemExit(f'H4 FAST direction mismatch count={len(mismatch)} first={mismatch[:5]}')
 fields=list(rows[0].keys())
 out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 meta={'rows':len(rows),'direction_mismatch':len(mismatch),'feature_columns':len(fields),'answer_sheet_columns':['answer_final_run_len','answer_future_remaining_h4'],'hashes':{k:sha256(p) for k,p in paths.items()}}
 out.with_suffix('.validation.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
