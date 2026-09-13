#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np
from pathlib import Path

M1=Path('/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv')
TRADES=Path('/mnt/data/era_runtime_chunk/FULL_2022_202608_MULTI_CHILD_TRADES.csv')
ARRIVALS=Path('/mnt/data/era_runtime_chunk/FULL_2022_202608_MULTI_CHILD_ARRIVALS.csv')
OUT=Path('/mnt/data/V9_20260914_ERA4_MULTICHILD_SHORT_DIAGNOSTIC/results'); OUT.mkdir(parents=True,exist_ok=True)

def metric(g,pnl_col,amb_col=None):
    vals=[]
    for r in g.sort_values('entry_ts').itertuples():
        v=getattr(r,pnl_col)
        if pd.notna(v): vals.append(float(v))
        elif amb_col and getattr(r,'hybrid_status')=='AMBIGUOUS': vals.append(-float(r.sl_dist))
    a=np.asarray(vals,float); pos=a[a>0].sum(); neg=-a[a<0].sum(); eq=np.cumsum(a); peak=np.maximum.accumulate(np.r_[0,eq]) if len(a) else np.array([0.]); dd=float((peak[1:]-eq).max()) if len(a) else 0.
    return {'entries':len(g),'n':len(a),'pnl':float(a.sum()),'PF':float(pos/neg) if neg else np.inf,'WR':float((a>0).mean()) if len(a) else np.nan,'DD':dd}

tr=pd.read_csv(TRADES,parse_dates=['entry_ts','exit_ts'])
ar=pd.read_csv(ARRIVALS,parse_dates=['ts']).sort_values('ts').reset_index(drop=True)
# Grammar route id.
route=0; order=0; ids=[]; orders=[]
for _,r in ar.iterrows():
    if r.resolution in ('SEED','CHALLENGER_EARNED','OLD_PRIMARY_WINS'): route+=1; order=0
    if bool(r.eligible): order+=1; orders.append(order)
    else: orders.append(np.nan)
    ids.append(route)
ar['route_id']=ids; ar['candidate_order']=orders
ar['next_ts']=ar.ts.shift(-1); ar['next_ref']=ar.ref.shift(-1)
ctx=ar[ar.eligible==True][['ts','route_id','candidate_order','next_ts','next_ref']].rename(columns={'ts':'entry_ts'})
tr=tr.merge(ctx,on='entry_ts',how='left')
# First actually accepted Child in each route is ANCHOR; later accepted Children are CONTINUATION.
tr['accepted_rank']=tr.groupby('route_id')['entry_ts'].rank(method='first').astype(int)
tr['role']=np.where(tr.accepted_rank.eq(1),'ANCHOR_CHILD','CONTINUATION_CHILD')

m=pd.read_csv(M1,sep='\t',usecols=['<DATE>','<TIME>','<HIGH>','<LOW>','<SPREAD>'],dtype={'<DATE>':'string','<TIME>':'string'})
m['ts']=pd.to_datetime(m['<DATE>']+' '+m['<TIME>']); ts=m.ts.values.astype('datetime64[ns]'); hi=m['<HIGH>'].to_numpy(float); lo=m['<LOW>'].to_numpy(float)
spmap=pd.Series(m['<SPREAD>'].to_numpy(float),index=m.ts).to_dict()

# Local continuation Child: own lifecycle ends at first subsequent H4-liquidity Arrival, unless own SL happened earlier; same-minute is ambiguous.
local=[]
for r in tr.itertuples():
    if r.role=='ANCHOR_CHILD':
        pnl=(r.exit_price-r.entry) if r.direction=='UP' else (r.entry-r.exit_price) if pd.notna(r.exit_price) else np.nan
        if r.status not in ('SL','CHALLENGE_OPENS'): pnl=np.nan
        local.append((r.entry_ts,r.status,r.exit_ts,r.exit_price,pnl))
        continue
    if pd.isna(r.next_ts): local.append((r.entry_ts,'OPEN_CENSORED',pd.NaT,np.nan,np.nan)); continue
    st=np.searchsorted(ts,np.datetime64(r.entry_ts),'left'); ev=np.searchsorted(ts,np.datetime64(r.next_ts),'left')
    if r.direction=='UP':
        hits=np.where(lo[st:ev] <= r.sl)[0]; same=(ev<len(ts) and ts[ev]==np.datetime64(r.next_ts) and lo[ev]<=r.sl)
    else:
        hits=np.where(hi[st:ev] >= r.sl)[0]; same=(ev<len(ts) and ts[ev]==np.datetime64(r.next_ts) and hi[ev]>=r.sl)
    if len(hits):
        xt=pd.Timestamp(ts[st+hits[0]]); pnl=-float(r.sl_dist); local.append((r.entry_ts,'SL',xt,r.sl,pnl))
    elif same:
        local.append((r.entry_ts,'AMBIGUOUS',r.next_ts,np.nan,np.nan))
    else:
        pnl=(r.next_ref-r.entry) if r.direction=='UP' else (r.entry-r.next_ref); local.append((r.entry_ts,'NEXT_H4_LIQ',r.next_ts,r.next_ref,pnl))
loc=pd.DataFrame(local,columns=['entry_ts','hybrid_status','hybrid_exit_ts','hybrid_exit_price','hybrid_pnl'])
tr=tr.merge(loc,on='entry_ts',how='left'); tr['hybrid_exit_ts']=pd.to_datetime(tr.hybrid_exit_ts,errors='coerce')
tr['entry_spread_price']=tr.entry_ts.map(lambda x:spmap.get(x,np.nan))*0.01; tr['exit_spread_price']=tr.hybrid_exit_ts.map(lambda x:spmap.get(x,np.nan) if pd.notna(x) else np.nan)*0.01
tr['spread_cost']=np.where(tr.direction.eq('UP'),tr.entry_spread_price,tr.exit_spread_price)
for k in (0,1,2,3): tr[f'net_{k}x']=tr.hybrid_pnl-k*tr.spread_cost
tr.to_csv(OUT/'ROLE_BASED_CHILD_LEDGER.csv',index=False)

rows=[]
for period,g0 in list(tr.groupby(tr.entry_ts.dt.year))+[('ALL',tr)]:
  for side,g in list(g0.groupby('direction'))+[('ALL',g0)]:
    row={'period':str(period),'direction':side}
    for k in (0,1,3):
        d=metric(g,f'net_{k}x'); row.update({f'{k}x_{kk}':vv for kk,vv in d.items()})
    wc=metric(g,'hybrid_pnl',amb_col='yes'); row.update({f'amb_wc_{kk}':vv for kk,vv in wc.items()})
    rows.append(row)
pd.DataFrame(rows).to_csv(OUT/'ROLE_BASED_MANAGEMENT_SUMMARY.csv',index=False)

# Maximum concurrency (exit before entry when timestamps equal).
ev=[]
for r in tr.itertuples():
    if pd.isna(r.hybrid_exit_ts): continue
    ev.append((r.entry_ts,1)); ev.append((r.hybrid_exit_ts,-1))
cur=mx=0
for _,d in sorted(ev,key=lambda z:(z[0],z[1])): cur+=d; mx=max(mx,cur)
Path(OUT/'ROLE_BASED_MAX_CONCURRENCY.txt').write_text(str(mx)+'\n')
print('max_concurrency',mx)
print(pd.read_csv(OUT/'ROLE_BASED_MANAGEMENT_SUMMARY.csv').query("period=='ALL'").to_string(index=False))
