from pathlib import Path
import numpy as np,pandas as pd
BASE=Path('/mnt/data/v9_htf_exhaustion_20260914_fast'); OUT=Path('/mnt/data/v9_terminal_detector_20260915'); H4P=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv')
acc=pd.read_csv(BASE/'ARRIVALS_ACCEPTED.csv',parse_dates=['entry_ts','challenge_ts','hybrid_exit_ts'])
arr=pd.read_csv(BASE/'ARRIVALS.csv',parse_dates=['ts'])
obj=pd.read_csv(BASE/'H4_SWING_OBJECTS.csv',parse_dates=['known_at','raid_ts'])
resolved=acc.groupby('route_id').challenge_ts.first().dropna().index
acc=acc[acc.route_id.isin(resolved)].copy().sort_values(['route_id','entry_ts'])
child_static=pd.read_csv(OUT/'TERMINAL_CHILD_DATASET.csv',parse_dates=['ts']).set_index(['route_id','accepted_rank'])
# H4 and causal ATR180
h=pd.read_csv(H4P,sep='\t');h['start']=pd.to_datetime(h['<DATE>']+' '+h['<TIME>']);h['known_at']=h.start+pd.Timedelta(hours=4)
for c in ['<OPEN>','<HIGH>','<LOW>','<CLOSE>']:h[c]=h[c].astype(float)
op=h['<OPEN>'].to_numpy(float);hi=h['<HIGH>'].to_numpy(float);lo=h['<LOW>'].to_numpy(float);cl=h['<CLOSE>'].to_numpy(float)
tr=np.empty(len(h));prev=np.nan
for i in range(len(h)):
 tr[i]=(hi[i]-lo[i]) if i==0 else max(hi[i]-lo[i],abs(hi[i]-cl[i-1]),abs(lo[i]-cl[i-1]))
atr=np.full(len(h),np.nan)
if len(h)>=180:
 atr[179]=tr[:180].mean()
 for i in range(180,len(h)):atr[i]=(atr[i-1]*179+tr[i])/180
h['atr180']=atr
hc=(op+hi+lo+cl)/4;hao=np.empty(len(h));hao[0]=(op[0]+cl[0])/2
for i in range(1,len(h)):hao[i]=(hao[i-1]+hc[i-1])/2
ha_side=np.where(hc>hao,'UP',np.where(hc<hao,'DOWN','DOJI'))
hk=h.known_at.to_numpy(dtype='datetime64[ns]')
# object numpy by side
O={}
for s in ['UP','DOWN']:
 q=obj[obj.side.eq(s)].copy(); known=q.known_at.to_numpy(dtype='datetime64[ns]'); raid=q.raid_ts.to_numpy(dtype='datetime64[ns]'); raid_num=raid.copy(); raid_num[np.isnat(raid_num)]=np.datetime64('2262-01-01'); O[s]=(known,raid_num,q.price.to_numpy(float))
# birth-time arrays for searchsorted
B={s:np.sort(O[s][0]) for s in O}
# arrivals route index for rejected diagnostics
ARR={rid:g.sort_values('ts') for rid,g in arr.groupby('route_id')}
rows=[]
for rid,g in acc.groupby('route_id'):
 g=g.sort_values('entry_ts'); times=g.entry_ts.to_numpy(dtype='datetime64[ns]'); exits=g.hybrid_exit_ts.to_numpy(dtype='datetime64[ns]'); exits2=exits.copy();exits2[np.isnat(exits2)]=np.datetime64('2262-01-01')
 ranks=g.accepted_rank.to_numpy(int); prices=g.entry.to_numpy(float); direction=str(g.direction.iloc[0]); opp='DOWN' if direction=='UP' else 'UP'; sign=1 if direction=='UP' else -1; total=len(g); first=pd.Timestamp(g.entry_ts.iloc[0]); challenge=pd.Timestamp(g.challenge_ts.iloc[0])
 i0=np.searchsorted(hk,np.datetime64(first),side='right'); i1=np.searchsorted(hk,np.datetime64(challenge),side='left')
 if i1<=i0:continue
 ag=ARR.get(rid,pd.DataFrame())
 for j in range(i0,i1):
  if not np.isfinite(atr[j]):continue
  T=hk[j]; # child events at same T occur after H4 semantic close, so strict <
  k=np.searchsorted(times,T,side='left')-1
  if k<0:continue
  openmask=(times<T)&(exits2>T)
  if not np.any(openmask):continue
  rank=int(ranks[k]); childt=times[k]; childp=prices[k]; S=float(atr[j]); price=float(cl[j])
  z={'route_id':int(rid),'ts':pd.Timestamp(T),'route_year':first.year,'primary':direction,'latest_rank':rank,'route_total_accepted':total,'terminal_now':int(rank==total),'latest_child_ts':pd.Timestamp(childt),'latest_child_price':childp,'atr180':S,'price':price,'bars_since_child':j-np.searchsorted(hk,childt,side='right')+1,'hours_since_child':(T-childt)/np.timedelta64(1,'h'),'price_from_child_S':sign*(price-childp)/S,'open_children':int(openmask.sum()),'open_cont':int(np.sum(openmask & (g.role.to_numpy()=='CONTINUATION_CHILD'))),'ha_same':float(ha_side[j]==direction),'ha_opp':float(ha_side[j]==opp),'ha_doji':float(ha_side[j]=='DOJI'),'h4_bar_body_S':sign*(cl[j]-op[j])/S,'h4_bar_range_S':(hi[j]-lo[j])/S}
  # active geometry at semantic T; raid exactly T remains active before current row price.
  for nm,s in [('same',direction),('opp',opp)]:
   known,raid,px=O[s]; mask=(known<=T)&(raid>=T)
   if direction=='UP': dist=(px-price) if s=='UP' else (price-px)
   else: dist=(price-px) if s=='DOWN' else (px-price)
   mask &= dist>0; inds=np.flatnonzero(mask);z[f'h4c_{nm}_active_n']=len(inds)
   if len(inds):
    order=inds[np.argsort(dist[inds])[:3]]
   else:order=[]
   for kk in [1,2,3]:
    if len(order)>=kk:
     ii=order[kk-1];z[f'h4c_{nm}_d{kk}_S']=float(dist[ii]/S);z[f'h4c_{nm}_age{kk}_h']=float((T-known[ii])/np.timedelta64(1,'h'))
    else:z[f'h4c_{nm}_d{kk}_S']=np.nan;z[f'h4c_{nm}_age{kk}_h']=np.nan
  ds=z['h4c_same_d1_S'];do=z['h4c_opp_d1_S'];z['h4c_distance_ratio']=ds/do if np.isfinite(ds) and np.isfinite(do) and do>0 else np.nan;z['h4c_same_nearest']=float(np.isfinite(ds) and (not np.isfinite(do) or ds<do)) if (np.isfinite(ds) or np.isfinite(do)) else np.nan
  st=child_static.loc[(rid,rank)]
  for old,new in [('h4liq_same_d1_S','h4c_same_d1_S'),('h4liq_opp_d1_S','h4c_opp_d1_S'),('h4liq_distance_ratio','h4c_distance_ratio'),('h4liq_same_active_n','h4c_same_active_n'),('h4liq_opp_active_n','h4c_opp_active_n')]:z['since_child_'+old]=z[new]-st[old] if np.isfinite(z[new]) and pd.notna(st[old]) else np.nan
  # births since child and route start via searchsorted
  for lab,start in [('child',childt),('route',np.datetime64(first))]:
   for nm,s in [('same',direction),('opp',opp)]:
    a=B[s];z[f'h4c_birth_{nm}_since_{lab}']=int(np.searchsorted(a,T,side='right')-np.searchsorted(a,start,side='right'))
  if len(ag):
   qa=ag[(ag.ts>pd.Timestamp(childt))&(ag.ts<pd.Timestamp(T))&(ag.arrival_side==direction)]
   z['same_arrivals_since_child']=len(qa);z['era4_rejects_since_child']=int((qa.entry_reject_reason=='SL_ERA_GT_4').sum())
  else:z['same_arrivals_since_child']=z['era4_rejects_since_child']=0
  # static latest-child context
  for c in ['h4liq_same_d1_S','h4liq_opp_d1_S','h4liq_distance_ratio','h4liq_same_active_n','h4liq_opp_active_n','current_liq_age_median_h','anchor_mfe_S','anchor_peak_giveback_S','route_progress_S','accepted_progress_S','current_sl_atr180','h4_replenish_net_since_first','h4_active_routeborn_balance','relmedian_h4liq_same_d1_S','sl_progress_from_first_S']:
   if c in st:z['child_'+c]=st[c]
  rows.append(z)
out=pd.DataFrame(rows);out.to_csv(OUT/'TERMINAL_H4_CHECKPOINT_DATASET.csv',index=False)
print('rows',len(out),'routes',out.route_id.nunique(),'terminal rate',out.terminal_now.mean())
print(out.groupby('route_year').agg(n=('terminal_now','size'),routes=('route_id','nunique'),pos=('terminal_now','sum')).to_string())
print('HA same/opp/doji',out[['ha_same','ha_opp','ha_doji']].sum().to_dict())
