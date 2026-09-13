#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np, json, hashlib
from pathlib import Path

M1=Path('/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv')
H4=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv')
TRADES=Path('/mnt/data/era_runtime_chunk/FULL_2022_202608_MULTI_CHILD_TRADES.csv')
ARRIVALS=Path('/mnt/data/era_runtime_chunk/FULL_2022_202608_MULTI_CHILD_ARRIVALS.csv')
OUT=Path('/mnt/data/V9_20260914_ERA4_MULTICHILD_SHORT_DIAGNOSTIC/results'); OUT.mkdir(parents=True,exist_ok=True)

def pf(a):
    a=np.asarray(a,float); pos=a[a>0].sum(); neg=-a[a<0].sum(); return pos/neg if neg else np.inf

def metr(g,col='price_pnl',amb_wc=False):
    g=g.sort_values('entry_ts'); vals=[]
    for _,r in g.iterrows():
        if r.status in ('SL','CHALLENGE_OPENS') and pd.notna(r[col]): vals.append(float(r[col]))
        elif amb_wc and r.status=='AMBIGUOUS': vals.append(-float(r.sl_dist))
    a=np.asarray(vals,float); eq=np.cumsum(a) if len(a) else np.array([]); peak=np.maximum.accumulate(np.r_[0,eq]) if len(a) else np.array([0.]); dd=float((peak[1:]-eq).max()) if len(a) else 0.
    return {'entries':len(g),'resolved_or_wc':len(a),'pnl':float(a.sum()) if len(a) else 0.,'PF':float(pf(a)) if len(a) else np.nan,'WR':float((a>0).mean()) if len(a) else np.nan,'maxDD':dd,'avg_win':float(a[a>0].mean()) if (a>0).any() else np.nan,'avg_loss':float(a[a<0].mean()) if (a<0).any() else np.nan}

tr=pd.read_csv(TRADES,parse_dates=['entry_ts','exit_ts'])
tr['year']=tr.entry_ts.dt.year
tr['price_pnl']=np.where(tr.direction.eq('UP'),tr.exit_price-tr.entry,tr.entry-tr.exit_price)
tr.loc[~tr.status.isin(['SL','CHALLENGE_OPENS']),'price_pnl']=np.nan

# Spread proxy mapping: chart prices treated as Bid-like research reference, as in previous packet.
sp=pd.read_csv(M1,sep='\t',usecols=['<DATE>','<TIME>','<SPREAD>'],dtype={'<DATE>':'string','<TIME>':'string','<SPREAD>':'float64'})
sp['ts']=pd.to_datetime(sp['<DATE>']+' '+sp['<TIME>'])
spmap=pd.Series(sp['<SPREAD>'].to_numpy(),index=sp.ts).to_dict()
tr['entry_spread_price']=tr.entry_ts.map(lambda x:spmap.get(x,np.nan))*0.01
tr['exit_spread_price']=tr.exit_ts.map(lambda x:spmap.get(x,np.nan) if pd.notna(x) else np.nan)*0.01
tr['spread_cost']=np.where(tr.direction.eq('UP'),tr.entry_spread_price,tr.exit_spread_price)
for k in range(4): tr[f'net_spread_{k}x']=tr.price_pnl-k*tr.spread_cost

# Arrival route/order + next H4-liquidity outcome.
ar=pd.read_csv(ARRIVALS,parse_dates=['ts']).sort_values('ts').reset_index(drop=True)
route=0; order=0; rids=[]; orders=[]
for _,r in ar.iterrows():
    if r.resolution in ('SEED','CHALLENGER_EARNED','OLD_PRIMARY_WINS'):
        route+=1; order=0
    if bool(r.eligible): order+=1; orders.append(order)
    else: orders.append(np.nan)
    rids.append(route)
ar['route_id']=rids; ar['child_order']=orders
ar['next_resolution']=ar.resolution.shift(-1); ar['next_ts']=ar.ts.shift(-1); ar['continued_next']=ar.next_resolution.eq('PRIMARY_CONTINUES')
start=ar[ar.resolution.isin(['SEED','CHALLENGER_EARNED','OLD_PRIMARY_WINS'])][['route_id','ts','ref','primary']].rename(columns={'ts':'route_start_ts','ref':'route_start_ref','primary':'route_side'})
ctx=ar[ar.eligible==True][['ts','route_id','child_order','next_resolution','next_ts','continued_next']].rename(columns={'ts':'entry_ts'})
tr=tr.merge(ctx,on='entry_ts',how='left').merge(start,on='route_id',how='left')
tr['route_progress_price']=np.where(tr.direction.eq('UP'),tr.entry-tr.route_start_ref,tr.route_start_ref-tr.entry)
tr['route_progress_atr180']=tr.route_progress_price/tr.atr180
tr['order_band']=pd.cut(tr.child_order,[0,1,2,3,999],labels=['1','2','3','4+'])

# M1 path excursions.
m=pd.read_csv(M1,sep='\t',usecols=['<DATE>','<TIME>','<HIGH>','<LOW>','<CLOSE>'],dtype={'<DATE>':'string','<TIME>':'string'})
m['ts']=pd.to_datetime(m['<DATE>']+' '+m['<TIME>'])
ts=m.ts.values.astype('datetime64[ns]'); hi=m['<HIGH>'].to_numpy(float); lo=m['<LOW>'].to_numpy(float); cl=m['<CLOSE>'].to_numpy(float)
mfe=[]; mae=[]; hold=[]
for r in tr.itertuples():
    st=np.searchsorted(ts,np.datetime64(r.entry_ts),'left')
    et=ts[-1] if pd.isna(r.exit_ts) else np.datetime64(r.exit_ts)
    en=np.searchsorted(ts,et,'right')
    if r.direction=='UP': mf=hi[st:en].max()-r.entry; ma=r.entry-lo[st:en].min()
    else: mf=r.entry-lo[st:en].min(); ma=hi[st:en].max()-r.entry
    mfe.append(mf); mae.append(ma); hold.append((pd.Timestamp(et)-r.entry_ts).total_seconds()/3600)
tr['MFE']=mfe; tr['MAE']=mae; tr['hold_h']=hold; tr['MFE_ATR180']=tr.MFE/tr.atr180; tr['MAE_ATR180']=tr.MAE/tr.atr180

# Early path, capped by actual child resolution.
for hrs in (1,4,12,24):
    fav=[]; adv=[]; ret=[]
    for r in tr.itertuples():
        st=np.searchsorted(ts,np.datetime64(r.entry_ts),'left')
        et=np.datetime64(r.entry_ts+pd.Timedelta(hours=hrs))
        if pd.notna(r.exit_ts): et=min(et,np.datetime64(r.exit_ts))
        en=np.searchsorted(ts,et,'right')
        if r.direction=='UP': f=hi[st:en].max()-r.entry; a=r.entry-lo[st:en].min(); rr=cl[en-1]-r.entry
        else: f=r.entry-lo[st:en].min(); a=hi[st:en].max()-r.entry; rr=r.entry-cl[en-1]
        fav.append(f/r.atr180); adv.append(a/r.atr180); ret.append(rr/r.atr180)
    tr[f'fav_{hrs}h_S']=fav; tr[f'adv_{hrs}h_S']=adv; tr[f'ret_{hrs}h_S']=ret

# Performance by year/direction.
rows=[]
for period,g0 in list(tr.groupby('year'))+[('ALL',tr)]:
    for side,g in list(g0.groupby('direction'))+[('ALL',g0)]:
        d=metr(g); dw=metr(g,amb_wc=True)
        d1=metr(g.assign(price_pnl=g.net_spread_1x))
        rows.append({'period':str(period),'direction':side,**d,'spread1_pnl':d1['pnl'],'spread1_PF':d1['PF'],'spread1_DD':d1['maxDD'],'amb_wc_pnl':dw['pnl'],'amb_wc_PF':dw['PF'],'amb_wc_DD':dw['maxDD']})
pd.DataFrame(rows).to_csv(OUT/'ERA4_PERFORMANCE_BY_YEAR_DIRECTION.csv',index=False)

# Spread sensitivity total.
rows=[]
for k in range(4):
    g=tr.copy(); g['price_pnl']=g[f'net_spread_{k}x']; d=metr(g)
    rows.append({'spread_multiple':k,**d})
pd.DataFrame(rows).to_csv(OUT/'ERA4_SPREAD_SENSITIVITY.csv',index=False)

# Monthly performance.
rows=[]
for mo,g in tr.groupby(tr.entry_ts.dt.to_period('M').astype(str)):
    d=metr(g); g1=g.copy(); g1['price_pnl']=g1.net_spread_1x; d1=metr(g1)
    rows.append({'month':mo,**d,'spread1_pnl':d1['pnl'],'spread1_PF':d1['PF']})
pd.DataFrame(rows).to_csv(OUT/'ERA4_MONTHLY_PERFORMANCE.csv',index=False)

# Child-order diagnostic.
rows=[]
for period,g0 in list(tr.groupby('year'))+[('ALL',tr)]:
    for side,g1 in g0.groupby('direction'):
        for ob,g in g1.groupby('order_band',observed=False):
            d=metr(g); rows.append({'period':str(period),'direction':side,'child_order_band':str(ob),**d,'median_route_progress_S':g.route_progress_atr180.median(),'median_sl_S':g.sl_atr180.median(),'median_MFE_S':g.MFE_ATR180.median(),'median_MAE_S':g.MAE_ATR180.median()})
pd.DataFrame(rows).to_csv(OUT/'CHILD_ORDER_DIAGNOSTIC.csv',index=False)

# Next H4 liquidity continuation and stop before it.
rows=[]
for side,g in tr.groupby('direction'):
    for cont,h in g.groupby('continued_next'):
        r=h[h.status.isin(['SL','CHALLENGE_OPENS'])]
        rows.append({'direction':side,'next_primary_continues':bool(cont),'entries':len(h),'next_event_share':len(h)/len(g),'SL_share_all_entries':(h.status=='SL').mean(),'resolved_price_pnl':r.price_pnl.sum(),'resolved_PF':pf(r.price_pnl.dropna())})
pd.DataFrame(rows).to_csv(OUT/'NEXT_LIQUIDITY_CONTINUATION_DIAGNOSTIC.csv',index=False)

# Early path diagnostic by direction/year + overall.
rows=[]
for period,g0 in list(tr.groupby('year'))+[('ALL',tr)]:
  for side,g in g0.groupby('direction'):
    row={'period':str(period),'direction':side,'entries':len(g)}
    for hrs in (1,4,12,24):
        row[f'mean_ret_{hrs}h_S']=g[f'ret_{hrs}h_S'].mean(); row[f'median_ret_{hrs}h_S']=g[f'ret_{hrs}h_S'].median(); row[f'median_fav_{hrs}h_S']=g[f'fav_{hrs}h_S'].median(); row[f'median_adv_{hrs}h_S']=g[f'adv_{hrs}h_S'].median()
    rows.append(row)
pd.DataFrame(rows).to_csv(OUT/'EARLY_PATH_DIAGNOSTIC.csv',index=False)

# Challenge capture: max favorable move vs common challenge giveback.
ch=tr[tr.status=='CHALLENGE_OPENS'].copy(); ch['final_S']=ch.price_pnl/ch.atr180; ch['giveback_S']=(ch.MFE-ch.price_pnl)/ch.atr180
rows=[]
for period,g0 in list(ch.groupby('year'))+[('ALL',ch)]:
  for side,g in g0.groupby('direction'):
    rows.append({'period':str(period),'direction':side,'n':len(g),'median_MFE_S':g.MFE_ATR180.median(),'median_giveback_S':g.giveback_S.median(),'median_final_S':g.final_S.median(),'mean_final_S':g.final_S.mean(),'positive_exit_share':(g.price_pnl>0).mean()})
pd.DataFrame(rows).to_csv(OUT/'CHALLENGE_CAPTURE_DIAGNOSTIC.csv',index=False)

# Route-progress descriptive bands (not authority).
bins=[-np.inf,.5,1,2,3,4,6,np.inf]; labels=['<=0.5','0.5-1','1-2','2-3','3-4','4-6','>6']
tr['route_progress_band']=pd.cut(tr.route_progress_atr180,bins=bins,labels=labels)
rows=[]
for side,g0 in tr.groupby('direction'):
  for b,g in g0.groupby('route_progress_band',observed=False):
    d=metr(g); rows.append({'direction':side,'route_progress_band':str(b),**d,'median_child_order':g.child_order.median()})
pd.DataFrame(rows).to_csv(OUT/'ROUTE_PROGRESS_DIAGNOSTIC.csv',index=False)

# Exact runtime trade ledger enriched for inspectability.
tr.to_csv(OUT/'ERA4_TRADES_ENRICHED.csv',index=False)

# Summary JSON.
summary={
 'runtime_policy':'MULTI_CHILD_ERA4',
 'era_scale':'previous-completed H4 Wilder ATR180',
 'eligibility':'valid causal H1 structural SL and SL_distance/ATR180 <= 4.0',
 'entries':int(len(tr)),
 'resolved':int(tr.status.isin(['SL','CHALLENGE_OPENS']).sum()),
 'ambiguous':int((tr.status=='AMBIGUOUS').sum()),
 'gross':metr(tr),
 'ambiguous_worst':metr(tr,amb_wc=True),
 'direction':{s:metr(g) for s,g in tr.groupby('direction')},
 'positive_months':int((pd.read_csv(OUT/'ERA4_MONTHLY_PERFORMANCE.csv').pnl>0).sum()),
 'months':int(len(pd.read_csv(OUT/'ERA4_MONTHLY_PERFORMANCE.csv'))),
}
(OUT/'ERA4_SHORT_PATH_REPORT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
