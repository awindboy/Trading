import pandas as pd,numpy as np
E=pd.read_pickle('/mnt/data/scenario_events.pkl')
D=pd.read_pickle('/mnt/data/slow_m1.pkl')
M5=D[['o','h','l','c','tv']].resample('5min',label='left',closed='left').agg(o=('o','first'),h=('h','max'),l=('l','min'),c=('c','last'),tv=('tv','sum')).dropna()
# context at every m5
hi12=M5.h.shift(1).rolling(12).max();lo12=M5.l.shift(1).rolling(12).min();sma=M5.c.rolling(20).mean();sd=M5.c.rolling(20).std(ddof=0);up=sma+2*sd;dn=sma-2*sd;ad=(M5.c-sma).abs()
# future label function from confirmation time and origin confirm close
idx=D.index.to_numpy(dtype='datetime64[ns]'); H=D.h.to_numpy();L=D.l.to_numpy()
def firstlabel(t,origin,S,horizon=.25,mins=15):
 p=np.searchsorted(idx,np.datetime64(t),'left');q=np.searchsorted(idx,np.datetime64(t+pd.Timedelta(minutes=mins)),'left');U=origin+horizon*S;Dn=origin-horizon*S
 for i in range(p,q):
  u=H[i]>=U;d=L[i]<=Dn
  if u and d:return 99
  if u:return 1
  if d:return -1
 return 0
rows=[]
for r in E.itertuples():
 s=r.source_m5; nxt=s+pd.Timedelta(minutes=5); conf=s+pd.Timedelta(minutes=10)
 if nxt not in M5.index: continue
 # require contiguous next bar: confirmation uses bar at nxt
 c0=M5.at[s,'c'];o0=M5.at[s,'o'];c1=M5.at[nxt,'c'];
 H0=hi12.at[s];L0=lo12.at[s];bd=1 if c0>H0 else (-1 if c0<L0 else 0);bodyS=abs(c0-o0)/r.S
 bb0=1 if c0>up.at[s] else (-1 if c0<dn.at[s] else 0);bb1=1 if c1>up.at[nxt] else (-1 if c1<dn.at[nxt] else 0)
 # source sweep reversal dir
 sw=0
 if M5.at[s,'h']>H0+.03*r.S and c0<=H0: sw=-1
 elif M5.at[s,'l']<L0-.03*r.S and c0>=L0: sw=1
 # canonical sequences
 defs=[]
 if bd!=0 and bodyS>=.15:
  accept=(bd==1 and c1>H0) or (bd==-1 and c1<L0)
  fail=(bd==1 and c1<=H0) or (bd==-1 and c1>=L0)
  if accept:defs.append(('D1_BREAKOUT_ACCEPT',bd))
  if fail:defs.append(('D2_BREAKOUT_FAIL_FADE',-bd))
 if bb0!=0 and (ad.at[s]>ad.shift(1).at[s]) and (ad.shift(1).at[s]>ad.shift(2).at[s]):
  persist=(bb1==bb0) and (ad.at[nxt]>ad.at[s])
  fail=(bb1==0) # simple reentry into bands
  if persist:defs.append(('D3_BB_PERSIST',bb0))
  if fail:defs.append(('D4_BB_REENTRY_FADE',-bb0))
 if sw!=0:
  # confirmation: next close continues away from swept side vs source close
  cont=(sw==1 and c1>=c0) or (sw==-1 and c1<=c0)
  if cont:defs.append(('D5_SWEEP_RECLAIM_CONFIRM',sw))
 # residence escape, same residence as prior script
 prev=M5.c.loc[:s].iloc[-7:-1].to_numpy(); R=H0-L0
 if len(prev)==6 and R>0 and bd!=0:
  res=((bd==1 and (prev>=L0+.75*R).sum()>=4) or (bd==-1 and (prev<=L0+.25*R).sum()>=4))
  hold=((bd==1 and c1>H0) or (bd==-1 and c1<L0))
  if res and hold:defs.append(('D6_RESIDENCE_ACCEPT',bd))
 lab15=firstlabel(conf,c1,r.S,.25,15);lab30=firstlabel(conf,c1,r.S,.25,30)
 for name,pd_ in defs:rows.append((r.year,s,conf,name,pd_,r.S,c1,lab15,lab30))
R=pd.DataFrame(rows,columns=['year','source','confirm','scenario','pred','S','origin','lab15','lab30'])
R.to_csv('/mnt/data/delayed_scenario_events.csv',index=False)
for name,z in R.groupby('scenario'):
 print('\n',name)
 for y in [2024,2025,2026]:
  q=z[z.year==y]; lab=q.lab15.to_numpy();p=q.pred.to_numpy();res=np.isin(lab,[-1,1]);
  if len(q):print(y,'N',len(q),'move',round(res.mean(),3),'acc',round(np.mean(lab[res]==p[res]),3) if res.sum() else None,'edge',round((np.sum(lab==p)-np.sum(lab==-p))/len(q),3))
