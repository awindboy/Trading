import pandas as pd,numpy as np,importlib.util
spec=importlib.util.spec_from_file_location('b','/mnt/data/v3_v8_bridge.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
m1=b.load_gold(b.DATA);m5=b.resample_ohlc(m1,'5min');m30=b.resample_ohlc(m1,'30min');h1=b.resample_ohlc(m1,'60min')
for z in [m5,m30,h1]:z['atr14']=b.atr_series(z)
p5=b.pivot_events(m5,2,5);p30=b.pivot_events(m30,2,30);p60=b.pivot_events(h1,2,60)
e5,o5,c5,hl5,ll5=b.bos_owner_with_break(m5,p5,5);e30,o30,c30,_,_=b.bos_owner_with_break(m30,p30,30);e60,o60,c60,_,_=b.bos_owner_with_break(h1,p60,60)
mw=b.mentor_waves(m30,30)
x=pd.read_csv('/mnt/data/delayed_scenario_events.csv',parse_dates=['source','confirm'])
x['m30_exp']=b.wave_expansion_at(x.confirm,mw);x['m30_owner']=b.state_at(x.confirm,e30,o30);x['h1_owner']=b.state_at(x.confirm,e60,o60);x['m5_owner']=b.state_at(x.confirm,e5,o5);x['m5_changed']=b.state_at(x.confirm,e5,c5)
# pred is follow for continuation scenarios; for fade scenarios original direction = -pred
x['orig_dir']=np.where(x.scenario.isin(['D2_BREAKOUT_FAIL_FADE','D4_BB_REENTRY_FADE']),-x.pred,x.pred)
x['orig_owners_align']=(x.m30_owner==x.orig_dir)&(x.h1_owner==x.orig_dir)
x['orig_delivery']=(x.m30_exp>1)|x.orig_owners_align
x['opposite_accept']=(x.m5_owner==x.pred)
x['opposite_change']=(x.m5_changed==x.pred)
x.to_csv('/mnt/data/delayed_scenario_v3full.csv',index=False)
for sc in ['D2_BREAKOUT_FAIL_FADE','D4_BB_REENTRY_FADE']:
 print('\n',sc)
 for y,g in x[x.scenario==sc].groupby('year'):
  print('YEAR',y,'all',len(g))
  masks={'orig_delivery':g.orig_delivery,'orig_align':g.orig_owners_align,'opp_owner':g.opposite_accept,'opp_change':g.opposite_change,
         'origDel+oppOwner':g.orig_delivery&g.opposite_accept,'origAlign+oppOwner':g.orig_owners_align&g.opposite_accept,
         'origDel+oppChange':g.orig_delivery&g.opposite_change}
  for nm,m in masks.items():
   q=g[m];r=q[q.lab15!=0];r30=q[q.lab30!=0]
   a=(r.pred==r.lab15).mean() if len(r) else np.nan;a30=(r30.pred==r30.lab30).mean() if len(r30) else np.nan
   print(nm,'N',len(q),'a15',round(a,3) if np.isfinite(a) else None,'a30',round(a30,3) if np.isfinite(a30) else None)
