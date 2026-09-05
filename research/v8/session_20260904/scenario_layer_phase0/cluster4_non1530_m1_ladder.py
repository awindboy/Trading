import pandas as pd,numpy as np
D=pd.read_pickle('/mnt/data/slow_m1.pkl');idx=D.index.to_numpy(dtype='datetime64[ns]');H=D.h.to_numpy();L=D.l.to_numpy();C=D.c.to_numpy()
x=pd.read_csv('/mnt/data/scenario_cluster_assignments.csv',parse_dates=['decision','source_m5']);q=x[(x.cluster==4)&~((x.source_m5.dt.hour==15)&(x.source_m5.dt.minute==30))].copy()
def out(r,tp,sl,mins):
 p=np.searchsorted(idx,np.datetime64(r.decision),'left');end=np.searchsorted(idx,np.datetime64(r.decision+pd.Timedelta(minutes=mins)),'left');en=r.origin_close if hasattr(r,'origin_close') else C[p-1]
 for i in range(p,min(end,len(idx))):
  if r.anchor15==1:win=H[i]>=en+tp*r.S;lose=L[i]<=en-sl*r.S
  else:win=L[i]<=en-tp*r.S;lose=H[i]>=en+sl*r.S
  if win and lose:return 99
  if lose:return -1
  if win:return 1
 return 0
for tp,sl,mins in [(.25,.25,15),(.5,.4,30),(.75,.4,45)]:
 print('\n',tp,sl)
 for y,g in q.groupby('year'):
  a=np.array([out(r,tp,sl,mins) for r in g.itertuples(index=False)]);z=a[np.isin(a,[-1,1])]
  print(y,'N',len(g),'resolved',len(z),'WR',round((z==1).mean(),3) if len(z) else None,'meanS',round(np.where(z==1,tp,-sl).mean(),3) if len(z) else None)
