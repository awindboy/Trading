from pathlib import Path
import numpy as np,pandas as pd, hashlib
BASE=Path('/mnt/data/v9_htf_exhaustion_20260914_fast'); OUT=Path('/mnt/data/v9_terminal_detector_20260915'); M1=Path('/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv'); H4P=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv')
acc=pd.read_csv(BASE/'ARRIVALS_ACCEPTED.csv',parse_dates=['entry_ts','challenge_ts','hybrid_exit_ts'])
arr=pd.read_csv(BASE/'ARRIVALS.csv',parse_dates=['ts'])
h4o=pd.read_csv(BASE/'H4_SWING_OBJECTS.csv',parse_dates=['known_at','raid_ts','source_ts'])
resolved=acc.groupby('route_id').challenge_ts.first().dropna().index
acc=acc[acc.route_id.isin(resolved)].copy().sort_values(['route_id','entry_ts'])
route_n=acc.groupby('route_id').size().to_dict(); route_first=acc.groupby('route_id').entry_ts.min().to_dict(); route_last=acc.groupby('route_id').entry_ts.max().to_dict(); route_ch=acc.groupby('route_id').challenge_ts.first().to_dict(); route_dir=acc.groupby('route_id').direction.first().to_dict()
child_static=pd.read_csv(OUT/'TERMINAL_CHILD_DATASET.csv',parse_dates=['ts']).set_index(['route_id','accepted_rank'])
# H4 + ATR180 + HA
h=pd.read_csv(H4P,sep='\t');h['start']=pd.to_datetime(h['<DATE>']+' '+h['<TIME>']);h['known_at']=h.start+pd.Timedelta(hours=4)
for c in ['<OPEN>','<HIGH>','<LOW>','<CLOSE>']:h[c]=h[c].astype(float)
tr=[];atr=[];prev=None;a=None
for r in h.itertuples():
 hi=float(getattr(r,'_3')) if False else None
# namedtuple column issue; use arrays
op=h['<OPEN>'].to_numpy(float);hi=h['<HIGH>'].to_numpy(float);lo=h['<LOW>'].to_numpy(float);cl=h['<CLOSE>'].to_numpy(float)
prev=None;a=None
for i in range(len(h)):
 x=(hi[i]-lo[i]) if prev is None else max(hi[i]-lo[i],abs(hi[i]-prev),abs(lo[i]-prev));tr.append(x)
 if a is None:
  if len(tr)>=180:a=float(np.mean(tr[-180:]))
 else:a=(a*179+x)/180
 atr.append(a if a is not None else np.nan);prev=cl[i]
h['atr180']=atr
hc=(op+hi+lo+cl)/4;hao=np.empty(len(h));hao[0]=(op[0]+cl[0])/2
for i in range(1,len(h)):hao[i]=(hao[i-1]+hc[i-1])/2
h['ha_close']=hc;h['ha_open']=hao;h['ha_side']=np.where(hc>hao,'UP',np.where(hc<hao,'DOWN','DOJI'))
# M1 for exact post-child MFE/MAE and current open mark not needed
m=pd.read_csv(M1,sep='\t',usecols=['<DATE>','<TIME>','<HIGH>','<LOW>']);m['ts']=pd.to_datetime(m['<DATE>']+' '+m['<TIME>']);mts=m.ts.to_numpy(dtype='datetime64[ns]');mhi=m['<HIGH>'].to_numpy(float);mlo=m['<LOW>'].to_numpy(float)
# object arrays by side
objs={s:h4o[h4o.side.eq(s)].copy() for s in ['UP','DOWN']}
rows=[]
for rid,g in acc.groupby('route_id'):
 direction=route_dir[rid];opp='DOWN' if direction=='UP' else 'UP';ft=route_first[rid];ct=route_ch[rid];Sroute=None
 # H4 close checkpoints strictly after first accepted and before challenge
 hs=h[(h.known_at>ft)&(h.known_at<ct)&h.atr180.notna()]
 if len(hs)==0: continue
 children=g.sort_values('entry_ts')
 for hr in hs.itertuples():
  T=pd.Timestamp(hr.known_at)
  prior=children[children.entry_ts<T]
  if len(prior)==0: continue
  lc=prior.iloc[-1]; rank=int(lc.accepted_rank); S=float(hr.atr180); price=float(getattr(hr,'_5')) if False else float(h.loc[hr.Index,'<CLOSE>'])
  # require at least one deterministic/open child exposure at T (including ambiguous/open as actual base status if exit NaT)
  entered=children[children.entry_ts<T]
  open_now=entered[entered.hybrid_exit_ts.isna() | (entered.hybrid_exit_ts>T)]
  if len(open_now)==0: continue
  sideobj=objs[direction];oppobj=objs[opp]
  # At semantic H4 close T, raids exactly at T price row are not yet exposed, so >=T remains active.
  same=sideobj[(sideobj.known_at<=T)&(sideobj.raid_ts.isna() | (sideobj.raid_ts>=T))].copy()
  opx=oppobj[(oppobj.known_at<=T)&(oppobj.raid_ts.isna() | (oppobj.raid_ts>=T))].copy()
  if direction=='UP':same['dist']=same.price-price;same=same[same.dist>0];opx['dist']=price-opx.price;opx=opx[opx.dist>0]
  else:same['dist']=price-same.price;same=same[same.dist>0];opx['dist']=opx.price-price;opx=opx[opx.dist>0]
  same=same.sort_values('dist');opx=opx.sort_values('dist')
  z={'route_id':rid,'ts':T,'route_year':ft.year,'primary':direction,'latest_rank':rank,'route_total_accepted':route_n[rid],'terminal_now':int(rank==route_n[rid]),'latest_child_ts':lc.entry_ts,'latest_child_price':lc.entry,'atr180':S,'price':price,'bars_since_child':int(np.searchsorted(h.known_at.to_numpy(dtype='datetime64[ns]'),np.datetime64(T))-np.searchsorted(h.known_at.to_numpy(dtype='datetime64[ns]'),np.datetime64(lc.entry_ts),side='right')+1),'hours_since_child':(T-lc.entry_ts).total_seconds()/3600,'price_from_child_S':(price-lc.entry)/S*(1 if direction=='UP' else -1),'open_children':len(open_now),'open_cont':int((open_now.role=='CONTINUATION_CHILD').sum()),'ha_same':float(h.loc[hr.Index,'ha_side']==direction),'ha_opp':float(h.loc[hr.Index,'ha_side']==opp),'ha_doji':float(h.loc[hr.Index,'ha_side']=='DOJI')}
  for nm,q in [('same',same),('opp',opx)]:
   z[f'h4c_{nm}_active_n']=len(q)
   for k in [1,2,3]:
    if len(q)>=k:
     rr=q.iloc[k-1];z[f'h4c_{nm}_d{k}_S']=rr.dist/S;z[f'h4c_{nm}_age{k}_h']=(T-rr.known_at).total_seconds()/3600
    else:z[f'h4c_{nm}_d{k}_S']=np.nan;z[f'h4c_{nm}_age{k}_h']=np.nan
  ds=z['h4c_same_d1_S'];do=z['h4c_opp_d1_S'];z['h4c_distance_ratio']=ds/do if np.isfinite(ds) and np.isfinite(do) and do>0 else np.nan;z['h4c_same_nearest']=float(np.isfinite(ds) and (not np.isfinite(do) or ds<do)) if (np.isfinite(ds) or np.isfinite(do)) else np.nan
  # changes vs latest accepted child's post-arrival geometry
  st=child_static.loc[(rid,rank)]
  for c0,c1 in [('h4liq_same_d1_S','h4c_same_d1_S'),('h4liq_opp_d1_S','h4c_opp_d1_S'),('h4liq_distance_ratio','h4c_distance_ratio'),('h4liq_same_active_n','h4c_same_active_n'),('h4liq_opp_active_n','h4c_opp_active_n')]:
   z['since_child_'+c0]=z[c1]-st[c0] if np.isfinite(z[c1]) and pd.notna(st[c0]) else np.nan
  # liquidity births after latest child / after first child, causal at T
  for label,start in [('child',lc.entry_ts),('route',ft)]:
   z[f'h4c_birth_same_since_{label}']=int(((sideobj.known_at>start)&(sideobj.known_at<=T)).sum())
   z[f'h4c_birth_opp_since_{label}']=int(((oppobj.known_at>start)&(oppobj.known_at<=T)).sum())
  # same-side arrivals after latest accepted child but before T, including rejected ones
  qa=arr[(arr.route_id==rid)&(arr.ts>lc.entry_ts)&(arr.ts<T)&(arr.arrival_side==direction)]
  z['same_arrivals_since_child']=len(qa);z['rejected_same_arrivals_since_child']=int((qa.entry_authorized==False).sum());z['era4_rejects_since_child']=int((qa.entry_reject_reason=='SL_ERA_GT_4').sum())
  # path since child through rows strictly before T (semantic close includes bar close but price path already known in completed H4; M1 rows <T are safe)
  i0=np.searchsorted(mts,np.datetime64(lc.entry_ts),'left');i1=np.searchsorted(mts,np.datetime64(T),'left');sign=1 if direction=='UP' else -1
  if i1>i0:
   if direction=='UP':peak=np.max(mhi[i0:i1]);trough=np.min(mlo[i0:i1]);mfe=(peak-lc.entry)/S;mae=(lc.entry-trough)/S
   else:trough=np.min(mlo[i0:i1]);peak=np.max(mhi[i0:i1]);mfe=(lc.entry-trough)/S;mae=(peak-lc.entry)/S
   z['child_mfe_S']=mfe;z['child_mae_S']=mae;z['child_giveback_S']=mfe-z['price_from_child_S']
  else:z['child_mfe_S']=z['child_mae_S']=z['child_giveback_S']=np.nan
  # static latest-child context copied causally; exclude future cols later
  for c in ['h4liq_same_d1_S','h4liq_opp_d1_S','h4liq_distance_ratio','h4liq_same_active_n','h4liq_opp_active_n','current_liq_age_median_h','anchor_mfe_S','anchor_peak_giveback_S','route_progress_S','accepted_progress_S','current_sl_atr180','h4_replenish_net_since_first','h4_active_routeborn_balance','relmedian_h4liq_same_d1_S']:
   if c in st:z['child_'+c]=st[c]
  rows.append(z)
out=pd.DataFrame(rows);out.to_csv(OUT/'TERMINAL_H4_CHECKPOINT_DATASET.csv',index=False)
print('rows',len(out),'routes',out.route_id.nunique(),'terminal rate',out.terminal_now.mean())
print(out.groupby('route_year').agg(n=('terminal_now','size'),routes=('route_id','nunique'),pos=('terminal_now','sum')).to_string())
print('same-color rows',int(out.ha_same.sum()),'opp-color rows',int(out.ha_opp.sum()))
