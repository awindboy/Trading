import pandas as pd, numpy as np
M1='/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv'; EV='/mnt/data/fresh648_events.csv'
d=pd.read_csv(M1,sep='\t'); d.columns=[c.strip('<>').lower() for c in d.columns]
d['dt']=pd.to_datetime(d['date']+' '+d['time'],format='%Y.%m.%d %H:%M:%S'); d=d.set_index('dt').sort_index()
for c in ['open','high','low','close']: d[c]=pd.to_numeric(d[c])
m5=d[['open','high','low','close']].resample('5min',label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna(); m5=m5[m5.index.year==2024].copy()
ev=pd.read_csv(EV); ev['decision']=pd.to_datetime(ev['decision']); ev['source_m5']=pd.to_datetime(ev['source_m5'])
# M5 context
sma=m5.close.rolling(20).mean(); sd=m5.close.rolling(20).std(ddof=0); up=sma+2*sd; lo=sma-2*sd
hi12=m5.high.shift(1).rolling(12).max(); lo12=m5.low.shift(1).rolling(12).min(); hi36=m5.high.shift(1).rolling(36).max(); lo36=m5.low.shift(1).rolling(36).min()
ctx=pd.DataFrame(index=m5.index)
ctx['break1_dir']=np.where(m5.close>hi12,1,np.where(m5.close<lo12,-1,0))
ctx['break3_dir']=np.where(m5.close>hi36,1,np.where(m5.close<lo36,-1,0))
ctx['bb_dir']=np.where(m5.close>up,1,np.where(m5.close<lo,-1,0))
ctx['body_dir']=np.sign(m5.close-m5.open).astype(int)
ctx['sweep_dir']=np.where((m5.low<lo12)&(m5.close>=lo12),1,np.where((m5.high>hi12)&(m5.close<=hi12),-1,0))
# future first touch ±.25S in 15m using M1, ambiguous if both in same M1
idx=d.index.to_numpy(dtype='datetime64[ns]'); hi=d.high.to_numpy(); low=d.low.to_numpy()
labels=[]
for r in ev.itertuples():
    t=r.decision; p=np.searchsorted(idx,np.datetime64(t),side='left'); q=np.searchsorted(idx,np.datetime64(t+pd.Timedelta(minutes=15)),side='left')
    upbar=r.origin_close+0.25*r.S; dnbar=r.origin_close-0.25*r.S
    lab=0; hit_time=None
    for i in range(p,q):
        u=hi[i]>=upbar; dn=low[i]<=dnbar
        if u and dn: lab=99; hit_time=d.index[i]; break
        if u: lab=1; hit_time=d.index[i]; break
        if dn: lab=-1; hit_time=d.index[i]; break
    labels.append(lab)
ev['first25']=labels
ev=ev.join(ctx,on='source_m5')
print('label counts',ev.first25.value_counts().to_dict())
for c in ['break1_dir','break3_dir','bb_dir','body_dir','sweep_dir']:
    z=ev[(ev[c]!=0)&(ev.first25.isin([-1,1]))]
    if len(z): print(c,'N',len(z),'acc',round((z[c]==z.first25).mean(),4),'coverage',round(len(z)/len(ev),3))
# combos: breakout + body aligned; BB + body aligned; breakout 3h + BB same direction
pairs=[('break1_body', (ev.break1_dir!=0)&(ev.break1_dir==ev.body_dir), 'break1_dir'),
       ('break3_body', (ev.break3_dir!=0)&(ev.break3_dir==ev.body_dir), 'break3_dir'),
       ('bb_body',(ev.bb_dir!=0)&(ev.bb_dir==ev.body_dir),'bb_dir'),
       ('break3_bb',(ev.break3_dir!=0)&(ev.break3_dir==ev.bb_dir),'break3_dir'),
       ('break1_bb',(ev.break1_dir!=0)&(ev.break1_dir==ev.bb_dir),'break1_dir')]
for name,mask,dc in pairs:
    z=ev[mask & ev.first25.isin([-1,1])]
    print(name,'N',len(z),'acc',round((z[dc]==z.first25).mean(),4) if len(z) else None)
