import pandas as pd,numpy as np,importlib.util
spec=importlib.util.spec_from_file_location('b','/mnt/data/v3_v8_bridge.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
m1=b.load_gold(b.DATA);m5=b.resample_ohlc(m1,'5min');m30=b.resample_ohlc(m1,'30min');h1=b.resample_ohlc(m1,'60min')
for z in [m5,m30,h1]:z['atr14']=b.atr_series(z)
p5=b.pivot_events(m5,2,5);p30=b.pivot_events(m30,2,30);p60=b.pivot_events(h1,2,60)
e5,o5,c5,_,_=b.bos_owner_with_break(m5,p5,5);e30,o30,c30,_,_=b.bos_owner_with_break(m30,p30,30);e60,o60,c60,_,_=b.bos_owner_with_break(h1,p60,60)
ev=pd.concat([pd.read_csv(f'/mnt/data/oldp0_events_{y}.csv') for y in [2024,2025,2026]],ignore_index=True);ev['source_m5']=pd.to_datetime(ev.source_m5);ev['decision']=pd.to_datetime(ev.decision)
pos=m5.index.get_indexer(ev.source_m5);ev['m5_owner']=o5[pos];ev['m5_changed']=c5[pos];ev['pre_m5_owner']=np.where(pos>0,o5[np.maximum(pos-1,0)],0)
ev['m30_owner']=b.state_at(ev.decision,e30,o30);ev['h1_owner']=b.state_at(ev.decision,e60,o60)
ev['htf_dir']=np.where((ev.m30_owner==ev.h1_owner)&(ev.m30_owner!=0),ev.m30_owner,0).astype(int)
# mutually exclusive semantic states
state=[];pred=[]
for r in ev.itertuples():
 d=int(r.htf_dir); pre=int(r.pre_m5_owner); cur=int(r.m5_owner); ch=int(r.m5_changed)
 if d!=0 and pre==-d and ch==d:
  s='S1_RELOAD_TRANSFER'; p=d
 elif d!=0 and cur==d and ch==0:
  s='S2_ALIGNED_CONTINUATION'; p=d
 elif d!=0 and ch==-d:
  s='S3_COUNTER_TRANSFER'; p=-d # local event direction, not auto fade
 elif d!=0 and cur==-d and ch==0:
  s='S4_CORRECTION_ACTIVE'; p=d # hypothesis: HTF resume, diagnostic only
 elif d==0 and ch!=0:
  s='S5_LOCAL_TRANSFER_NO_HTF'; p=ch
 elif d==0 and cur!=0:
  s='S6_LOCAL_OWNER_NO_HTF'; p=cur
 else:
  s='S7_UNRESOLVED'; p=0
 state.append(s);pred.append(p)
ev['state']=state;ev['pred']=pred
# outcomes quote-free M1 from decision
idx=m1.index.to_numpy(dtype='datetime64[ns]');H=m1.high.to_numpy();L=m1.low.to_numpy()
def ft(r,fav,adv,mins):
 if r.pred==0:return np.nan
 p=np.searchsorted(idx,np.datetime64(r.decision),'left');q=np.searchsorted(idx,np.datetime64(r.decision+pd.Timedelta(minutes=mins)),'left');U=r.origin_close+r.pred*fav*r.S;A=r.origin_close-r.pred*adv*r.S
 for i in range(p,q):
  if r.pred>0:w=H[i]>=U;l=L[i]<=A
  else:w=L[i]<=U;l=H[i]>=A
  if w and l:return 0.0
  if l:return 0.0
  if w:return 1.0
 return np.nan
for spec2,name in [((.25,.25,15),'w25'),((.5,.4,30),'w50'),((.75,.4,60),'w75')]: ev[name]=[ft(r,*spec2) for r in ev.itertuples()]
ev.to_csv('/mnt/data/v8_v3_state_transition_events.csv',index=False)
for y,g in ev.groupby('year'):
 print('\nYEAR',y,'N',len(g))
 for s,q in g.groupby('state'):
  print(s,'N',len(q),'w25',q.w25.mean(),'n25',q.w25.notna().sum(),'w50',q.w50.mean(),'n50',q.w50.notna().sum(),'w75',q.w75.mean(),'n75',q.w75.notna().sum())
