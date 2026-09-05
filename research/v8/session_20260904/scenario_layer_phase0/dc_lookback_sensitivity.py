import pandas as pd, numpy as np
from pathlib import Path
from dc_glass_ceiling_audit import load_m1, dc_state
m1=load_m1(); idx=m1.index.to_numpy(dtype='datetime64[ns]'); cl=m1.close.to_numpy(float)
ev=pd.concat([pd.read_csv(f'/mnt/data/oldp0_events_{y}.csv') for y in [2024,2025,2026]],ignore_index=True); ev.decision=pd.to_datetime(ev.decision)
# outcomes from audit
base=pd.read_csv('/mnt/data/dc_glass_ceiling_events.csv'); base.decision=pd.to_datetime(base.decision)
out=[]
for lb in [240,480,960]:
 rows=[]
 for r in ev.itertuples(index=False):
  dec=pd.Timestamp(r.decision); end=np.searchsorted(idx,np.datetime64(dec),'left'); start=np.searchsorted(idx,np.datetime64(dec-pd.Timedelta(minutes=lb)),'left'); prices=cl[start:end]; times=idx[start:end]
  z={'decision':dec,'year':r.year}
  for s in [.125,.25,.5]:
   st=dc_state(prices,times,s*r.S); z[f'm{s}']=st['mode']
  z['align3']=int(z['m0.125']!=0 and z['m0.125']==z['m0.25']==z['m0.5']); z['dir']=z['m0.125'] if z['align3'] else 0
  rows.append(z)
 d=pd.DataFrame(rows).merge(base[['decision','ft25_15']],on='decision')
 for y in [2024,2025,2026]:
  q=d[(d.year==y)&(d.align3==1)&d.ft25_15.isin([-1,1])]
  out.append({'lookback':lb,'year':y,'align3_n_all':int(d[(d.year==y)].align3.sum()),'hit_n':len(q),'acc':(q.dir==q.ft25_15).mean() if len(q) else np.nan})
 d.to_csv(f'/mnt/data/dc_lb_{lb}.csv',index=False)
# agreement with 480
D={lb:pd.read_csv(f'/mnt/data/dc_lb_{lb}.csv') for lb in [240,480,960]}
for d in D.values(): d.decision=pd.to_datetime(d.decision)
for lb in [240,960]:
 m=D[480].merge(D[lb],on=['decision','year'],suffixes=('_480',f'_{lb}'))
 for y in [2024,2025,2026]:
  q=m[m.year==y]
  out.append({'lookback':f'agree480_{lb}','year':y,'align3_n_all':len(q),'hit_n':int((q.align3_480==q[f'align3_{lb}']).sum()),'acc':(q.dir_480==q[f'dir_{lb}']).mean()})
res=pd.DataFrame(out); res.to_csv('/mnt/data/dc_lookback_sensitivity.csv',index=False); print(res.to_string(index=False))
