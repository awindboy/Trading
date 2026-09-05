import pandas as pd, numpy as np, importlib.util
spec=importlib.util.spec_from_file_location('b','/mnt/data/v3_v8_bridge.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
m1=b.load_gold(b.DATA)
b30=b.resample_ohlc(m1,'30min'); b60=b.resample_ohlc(m1,'60min')
for z in [b30,b60]: z['atr14']=b.atr_series(z)
p30=b.pivot_events(b30,2,30); p60=b.pivot_events(b60,2,60)
e30,o30,c30,_,_=b.bos_owner_with_break(b30,p30,30); e60,o60,c60,_,_=b.bos_owner_with_break(b60,p60,60)
mw=b.mentor_waves(b30,30)
x=pd.read_csv('/mnt/data/delayed_scenario_events.csv',parse_dates=['source','confirm'])
x['m30_exp']=b.wave_expansion_at(x.confirm,mw)
x['m30_owner']=b.state_at(x.confirm,e30,o30);x['h1_owner']=b.state_at(x.confirm,e60,o60)
x['delivery_pred']=(x.m30_exp>1)|((x.m30_owner==x.pred)&(x.h1_owner==x.pred))
x['owners_align_pred']=(x.m30_owner==x.pred)&(x.h1_owner==x.pred)
x.to_csv('/mnt/data/delayed_scenario_v3state.csv',index=False)
for sc,g0 in x.groupby('scenario'):
 print('\nSCEN',sc)
 for y,g in g0.groupby('year'):
   print(' year',y,'all',len(g),end=' ')
   for label,mask in [('DEL',g.delivery_pred),('NO',~g.delivery_pred),('ALIGN',g.owners_align_pred),('EXP',g.m30_exp>1)]:
     q=g[mask]; q15=q[q.lab15!=0];q30=q[q.lab30!=0]
     a15=(q15.pred==q15.lab15).mean() if len(q15) else np.nan;a30=(q30.pred==q30.lab30).mean() if len(q30) else np.nan
     print(f'{label}:N{len(q)}/a15={a15:.3f}/a30={a30:.3f}',end=' ')
   print()
