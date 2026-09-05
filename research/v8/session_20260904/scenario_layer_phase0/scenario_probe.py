import pandas as pd, numpy as np
M1='/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv'
EV='/mnt/data/fresh648_events.csv'
d=pd.read_csv(M1,sep='\t'); d.columns=[c.strip('<>').lower() for c in d.columns]
d['dt']=pd.to_datetime(d['date']+' '+d['time'],format='%Y.%m.%d %H:%M:%S'); d=d.set_index('dt')
for c in ['open','high','low','close','tickvol']: d[c]=pd.to_numeric(d[c])
# M5
m5=d[['open','high','low','close','tickvol']].resample('5min',label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last','tickvol':'sum'}).dropna()
m5=m5[m5.index.year==2024].copy()
# indicators
sma=m5['close'].rolling(20).mean(); sd=m5['close'].rolling(20).std(ddof=0); up=sma+2*sd; lo=sma-2*sd
prior_hi12=m5['high'].shift(1).rolling(12).max(); prior_lo12=m5['low'].shift(1).rolling(12).min()
prior_hi36=m5['high'].shift(1).rolling(36).max(); prior_lo36=m5['low'].shift(1).rolling(36).min()
range12=prior_hi12-prior_lo12
body=(m5['close']-m5['open']).abs()
# event S map
ev=pd.read_csv(EV); ev['source_m5']=pd.to_datetime(ev['source_m5']); ev=ev.set_index('source_m5')
# map S to m5 by event only, for baseline approximate use H4 ATR recreated via M1
h4=d[['open','high','low','close']].resample('4h',label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
pc=h4.close.shift(1); tr=pd.concat([(h4.high-h4.low),(h4.high-pc).abs(),(h4.low-pc).abs()],axis=1).max(axis=1)
atr=np.full(len(h4),np.nan); trv=tr.to_numpy(); atr[13]=np.nanmean(trv[:14])
for i in range(14,len(trv)): atr[i]=(atr[i-1]*13+trv[i])/14
h4['atr']=atr
# decision source m5 +5m. S = previous H4 before decision block
h4idx=h4.index.to_numpy(dtype='datetime64[ns]'); av=h4.atr.to_numpy()
dec=(m5.index+pd.Timedelta(minutes=5)); block=dec.floor('4h').to_numpy(dtype='datetime64[ns]'); pos=np.searchsorted(h4idx,block,side='right')-1; prev=pos-1
S=np.full(len(m5),np.nan); ok=(prev>=0)&(prev<len(av)); S[ok]=av[prev[ok]]; m5['S']=S
# scenarios
m5['outside_upper']=m5.close>up; m5['outside_lower']=m5.close<lo
m5['outside_any']=m5.outside_upper|m5.outside_lower
m5['breakout_1h']=(m5.close>prior_hi12)|(m5.close<prior_lo12)
m5['breakout_3h']=(m5.close>prior_hi36)|(m5.close<prior_lo36)
m5['sweep_reclaim_1h']=((m5.high>prior_hi12)&(m5.close<=prior_hi12))|((m5.low<prior_lo12)&(m5.close>=prior_lo12))
m5['displacement_010S']=(body/m5.S)>=0.10
m5['displacement_015S']=(body/m5.S)>=0.15
m5['dist_sma_gt_015S']=((m5.close-sma).abs()/m5.S)>=0.15
m5['range1h_gt_050S']=(range12/m5.S)>=0.50
m5['range1h_lt_025S']=(range12/m5.S)<=0.25
# 'compression release': prior 1h compact then current close breakout prior range isn't possible if using same prior; combine low range and current wick/close breakout
m5['compression_breakout']=m5.range1h_lt_025S & m5.breakout_1h
# expanding away: outside any + abs SMA gap increasing 3 consecutive bars
absdist=(m5.close-sma).abs()/m5.S
m5['bb_away3']=m5.outside_any & (absdist>absdist.shift(1)) & (absdist.shift(1)>absdist.shift(2))
# fresh membership
m5['fresh']=m5.index.isin(ev.index)
print('baseline bars',len(m5),'fresh',m5.fresh.sum())
cols=['outside_any','outside_upper','outside_lower','breakout_1h','breakout_3h','sweep_reclaim_1h','displacement_010S','displacement_015S','dist_sma_gt_015S','range1h_gt_050S','range1h_lt_025S','compression_breakout','bb_away3']
for c in cols:
    a=m5.loc[m5.fresh,c].mean(); b=m5.loc[~m5.fresh,c].mean(); enr=a/b if b>0 else np.nan
    print(c, 'fresh',round(a,4),'base',round(b,4),'enrich',round(enr,2),'Nfresh',int(m5.loc[m5.fresh,c].sum()))
# p15 conditional within fresh
joined=ev[['p15','direction']].join(m5[cols+['S']],how='left')
print('\nWithin fresh p15 mean by scenario:')
for c in cols:
    if joined[c].sum()>=5:
        print(c,int(joined[c].sum()),round(joined.loc[joined[c],'p15'].mean(),4),round(joined.loc[~joined[c],'p15'].mean(),4))
