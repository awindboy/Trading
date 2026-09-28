from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

EPS=1e-9
START=pd.Timestamp('2024-01-01 00:00:00')
CUTOFF=pd.Timestamp('2026-08-28 20:00:00')

def load(path:Path,tf:str):
 d=pd.read_csv(path,sep='\t');d['time']=pd.to_datetime(d['<DATE>']+' '+d['<TIME>'],format='%Y.%m.%d %H:%M:%S')
 d=d.rename(columns={'<OPEN>':'open','<HIGH>':'high','<LOW>':'low','<CLOSE>':'close'})
 for c in ['open','high','low','close']:d[c]=pd.to_numeric(d[c],errors='raise')
 d=d.sort_values('time').reset_index(drop=True)
 if tf=='M1': d['h4']=d.time.dt.floor('4h')
 if tf=='H1': d['h4']=d.time.dt.floor('4h')
 return d

def add_ha(d:pd.DataFrame,prefix='ha'):
 ho=hc=None;color=0;arr=[]
 for r in d.itertuples(index=False):
  nhc=(r.open+r.high+r.low+r.close)/4.0
  nho=(r.open+r.close)/2.0 if ho is None else (ho+hc)/2.0
  nc=1 if nhc>nho else -1 if nhc<nho else color
  hh=max(r.high,nho,nhc);ll=min(r.low,nho,nhc)
  upper=hh-max(nho,nhc); lower=min(nho,nhc)-ll
  opp=lower if nc==1 else upper
  arr.append((nho,nhc,nc,opp))
  ho,hc,color=nho,nhc,nc
 out=d.copy();out[[prefix+'_open',prefix+'_close',prefix+'_color',prefix+'_opp_wick']]=pd.DataFrame(arr,index=out.index)
 return out

def gate_map(h4,h1):
 h1_groups={t:g.h1_color.astype(int).tolist() for t,g in h1.groupby('h4',sort=False)}
 out={}
 for r in h4.itertuples(index=False):
  side=int(r.h4_color); cols=h1_groups.get(r.time,[])
  raw_accept=side*(r.close-r.h4_close)>EPS
  no_wick=float(r.h4_opp_wick)<=EPS
  h1_no_opp=bool(cols) and all(int(c)==side for c in cols)
  out[r.time]=(raw_accept and no_wick and h1_no_opp,raw_accept,no_wick,h1_no_opp,len(cols))
 return out

def build_children(h4,gate=None):
 rows=[];jid=0;active=0;active_jid=0;success=0
 for i in range(len(h4)-1):
  r=h4.iloc[i]; prev=int(h4.iloc[i-1].h4_color) if i else 0
  if r.time<START or r.time>CUTOFF: continue
  side=int(r.h4_color)
  if side==0 or prev==0: continue
  if active==0:
   if side!=prev:
    jid+=1;active_jid=jid;active=side;success=1
    rows.append(dict(journey=jid,child=1,side=side,signal_idx=i,signal=r.time,entry_idx=i+1,entry=float(h4.iloc[i+1].open),signal_high=float(r.high),signal_low=float(r.low),admitted=True))
   continue
  if side==active:
   if success<10:
    admitted=True if gate is None else bool(gate[r.time][0])
    if admitted:
     success+=1
     rows.append(dict(journey=active_jid,child=success,side=side,signal_idx=i,signal=r.time,entry_idx=i+1,entry=float(h4.iloc[i+1].open),signal_high=float(r.high),signal_low=float(r.low),admitted=True))
   continue
  exit_price=float(h4.iloc[i+1].open)
  for row in rows:
   if row['journey']==active_jid and 'baseline_exit' not in row:
    row['baseline_exit']=exit_price;row['exit_signal_idx']=i
  jid+=1;active_jid=jid;active=side;success=1
  rows.append(dict(journey=jid,child=1,side=side,signal_idx=i,signal=r.time,entry_idx=i+1,entry=float(h4.iloc[i+1].open),signal_high=float(r.high),signal_low=float(r.low),admitted=True))
 d=pd.DataFrame([r for r in rows if 'baseline_exit' in r])
 d['baseline_pnl']=d.side*(d.baseline_exit-d.entry)
 return d

def groups_m1(m1):return {k:g[['time','open','high','low','close']].reset_index(drop=True) for k,g in m1.groupby('h4',sort=False)}
def fill(side,lock,row):return float(row.open) if (side==1 and row.open<lock) or (side==-1 and row.open>lock) else lock

def eval_ha9(children,h4,m1g):
 ht=h4.time.to_list();out=[]
 for r in children.itertuples(index=False):
  ex=float(r.baseline_exit);reason='HA_EXIT';proven=False;pt=None;lock=None
  if int(r.child)>=2:
   key=ht[int(r.entry_idx)];g=m1g.get(key);target=float(r.signal_high if r.side==1 else r.signal_low)
   if g is None or g.empty:raise RuntimeError(f'missing M1 {key}')
   pos=None
   for j,b in enumerate(g.itertuples(index=False)):
    if (r.side==1 and b.high>target+EPS) or (r.side==-1 and b.low<target-EPS):proven=True;pos=j;pt=b.time;lock=max(float(r.entry),target) if r.side==1 else min(float(r.entry),target);break
   if proven:
    hit=False
    for hi in range(int(r.entry_idx),int(r.exit_signal_idx)+1):
     gg=m1g.get(ht[hi]);
     if gg is None:continue
     for b in gg.itertuples(index=False):
      if b.time<=pt:continue
      if (r.side==1 and b.low<=lock+EPS) or (r.side==-1 and b.high>=lock-EPS):ex=fill(int(r.side),lock,b);reason='BREAKOUT_LOCK';hit=True;break
     if hit:break
   else:
    ti=int(r.entry_idx)+1; bi=int(r.exit_signal_idx)+1
    if ti<=bi:ex=float(h4.iloc[ti].open);reason='PROOF_TIMEOUT'
  pnl=int(r.side)*(ex-float(r.entry));out.append({**r._asdict(),'variant_exit':ex,'variant_pnl':pnl,'reason':reason,'proven':proven,'proof_time':pt,'lock':lock})
 return pd.DataFrame(out)

def stats(df):
 v=df.variant_pnl.to_numpy(float);w=int((v>0).sum());l=int((v<0).sum());f=int((v==0).sum());gw=v[v>0].sum();gl=-v[v<0].sum();eq=np.cumsum(v);pk=np.maximum.accumulate(np.r_[0,eq]);dd=(pk[1:]-eq).max() if len(eq) else 0;best=cur=0
 for x in v:
  if x<0:cur+=1;best=max(best,cur)
  else:cur=0
 return {'n':len(v),'wins':w,'losses':l,'flats':f,'wr_nonflat':w/(w+l) if w+l else None,'net':float(v.sum()),'pf':float(gw/gl) if gl else None,'dd':float(dd),'max_loss_streak':best,'journeys':int(df.journey.nunique())}

def main():
 p=argparse.ArgumentParser();p.add_argument('--h4',type=Path,required=True);p.add_argument('--h1',type=Path,required=True);p.add_argument('--m1',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 h4=add_ha(load(a.h4,'H4'),'h4');h1=add_ha(load(a.h1,'H1'),'h1');m1=load(a.m1,'M1');gate=gate_map(h4,h1);m1g=groups_m1(m1)
 base=eval_ha9(build_children(h4,None),h4,m1g);sa1=eval_ha9(build_children(h4,gate),h4,m1g)
 summary={'status':'CONSUMED DEVELOPMENT / IDEALIZED M1 REPLAY','ha9':stats(base),'sa1':stats(sa1),'loss_reduction_pct':((base.variant_pnl<0).sum()-(sa1.variant_pnl<0).sum())/(base.variant_pnl<0).sum(),'net_retention':sa1.variant_pnl.sum()/base.variant_pnl.sum(),'year':{}}
 for y in [2024,2025,2026]:
  summary['year'][str(y)]={'ha9':stats(base[pd.to_datetime(base.signal).dt.year==y]),'sa1':stats(sa1[pd.to_datetime(sa1.signal).dt.year==y])}
 base.to_csv(a.output/'ha9_idealized_child_ledger.csv',index=False);sa1.to_csv(a.output/'sa1_idealized_child_ledger.csv',index=False);(a.output/'idealized_summary.json').write_text(json.dumps(summary,indent=2,default=str),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
