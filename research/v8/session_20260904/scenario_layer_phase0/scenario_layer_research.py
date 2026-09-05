import pandas as pd, numpy as np, os
from collections import defaultdict
M1='/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv'
# Load M1 once
D=pd.read_csv(M1,sep='\t'); D.columns=[c.strip('<>').lower() for c in D.columns]
D['dt']=pd.to_datetime(D['date']+' '+D['time'],format='%Y.%m.%d %H:%M:%S'); D=D.set_index('dt').sort_index()
for c in ['open','high','low','close','tickvol']: D[c]=pd.to_numeric(D[c],errors='coerce')
M5=D[['open','high','low','close','tickvol']].resample('5min',label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last','tickvol':'sum'}).dropna()
# Context arrays, all causal at source close
hi12=M5.high.shift(1).rolling(12).max(); lo12=M5.low.shift(1).rolling(12).min(); r12=hi12-lo12
hi36=M5.high.shift(1).rolling(36).max(); lo36=M5.low.shift(1).rolling(36).min()
sma20=M5.close.rolling(20).mean(); sd20=M5.close.rolling(20).std(ddof=0); bbup=sma20+2*sd20; bblo=sma20-2*sd20
absdist=(M5.close-sma20).abs()
# prev-bar breakout boundary
prev_break_dir=np.where(M5.close.shift(1)>hi12.shift(1),1,np.where(M5.close.shift(1)<lo12.shift(1),-1,0))
# H1 completed bars/context
H1=D[['open','high','low','close']].resample('1h',label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
# event populations: 2024 exact old P0 648 + sequential same-algorithm proxies 2025/26
parts=[]
for y in [2024,2025,2026]:
 p=f'/mnt/data/oldp0_events_{y}.csv'
 z=pd.read_csv(p); z['source_m5']=pd.to_datetime(z['source_m5']); z['decision']=pd.to_datetime(z['decision']); z['population']='P0R_lbfgs' if y>2024 else 'oldP0_648'
 parts.append(z)
E=pd.concat(parts,ignore_index=True)
# Map context by source_m5
def at(series,times): return series.reindex(pd.DatetimeIndex(times)).to_numpy()
E['o']=at(M5.open,E.source_m5); E['h']=at(M5.high,E.source_m5); E['l']=at(M5.low,E.source_m5); E['c']=at(M5.close,E.source_m5)
E['hi12']=at(hi12,E.source_m5); E['lo12']=at(lo12,E.source_m5); E['r12']=E.hi12-E.lo12
E['hi36']=at(hi36,E.source_m5); E['lo36']=at(lo36,E.source_m5)
E['sma20']=at(sma20,E.source_m5); E['bbup']=at(bbup,E.source_m5); E['bblo']=at(bblo,E.source_m5); E['absdist0']=np.abs(E.c-E.sma20)
E['absdist1']=at(absdist.shift(1),E.source_m5); E['absdist2']=at(absdist.shift(2),E.source_m5)
E['prev_break_dir']=at(pd.Series(prev_break_dir,index=M5.index),E.source_m5)
# local bar prior values
for k in range(1,8):
 for fld in ['open','high','low','close']:
  E[f'{fld}{k}']=at(M5[fld].shift(k),E.source_m5)
# basic dirs
body=E.c-E.o; bodydir=np.sign(body).astype(int)
breakdir=np.where(E.c>E.hi12,1,np.where(E.c<E.lo12,-1,0))
break3dir=np.where(E.c>E.hi36,1,np.where(E.c<E.lo36,-1,0))
bbdir=np.where(E.c>E.bbup,1,np.where(E.c<E.bblo,-1,0))
E['body_dir']=bodydir; E['break_dir']=breakdir; E['break3_dir']=break3dir; E['bb_dir']=bbdir
E['bodyS']=np.abs(body)/E.S
# Scenarios and prescribed direction. No outcome used in definitions.
scenarios={}
# 1 breakout displacement follow
mask=(breakdir!=0)&(E.bodyS>=.15)&(bodydir==breakdir)
scenarios['S1_BREAKOUT_DISP_FOLLOW']=(mask,breakdir)
# 2 sweep reclaim fade, overshoot >= .03S
up_sweep=(E.h>E.hi12+.03*E.S)&(E.c<=E.hi12)
dn_sweep=(E.l<E.lo12-.03*E.S)&(E.c>=E.lo12)
sweepdir=np.where(dn_sweep,1,np.where(up_sweep,-1,0)) # trade reversal direction
scenarios['S2_SWEEP_RECLAIM_FADE']=((sweepdir!=0),sweepdir)
# 3 failed prior close breakout -> current reentry, fade previous breakout
prev_hi=E.hi12 # current boundary similar enough; use previous source's fixed prior boundary reconstructed below from shifted hi12
prev_hi_b=at(hi12.shift(1),E.source_m5); prev_lo_b=at(lo12.shift(1),E.source_m5)
prevbd=E.prev_break_dir.astype(int)
reentry=((prevbd==1)&(E.c<=prev_hi_b))|((prevbd==-1)&(E.c>=prev_lo_b))
fdir=-prevbd
scenarios['S3_FAILED_BREAKOUT_FADE']=(reentry&(prevbd!=0),fdir)
# 4 residence escape: 4/6 previous closes in outer quartile of CURRENT prior 1h range, then breakout
prevcl=np.vstack([E[f'close{k}'].to_numpy() for k in range(1,7)]).T
upper_cut=E.lo12+.75*E.r12; lower_cut=E.lo12+.25*E.r12
upres=(prevcl>=upper_cut.to_numpy()[:,None]).sum(axis=1)>=4
dnres=(prevcl<=lower_cut.to_numpy()[:,None]).sum(axis=1)>=4
resmask=((breakdir==1)&upres)|((breakdir==-1)&dnres)
scenarios['S4_RESIDENCE_ESCAPE_FOLLOW']=(resmask,breakdir)
# 5 compression release: prior 1h range <= .35S + displacement breakout
comp=(E.r12/E.S)<=.35
scenarios['S5_COMPRESSION_RELEASE_FOLLOW']=(comp&(breakdir!=0)&(E.bodyS>=.15)&(bodydir==breakdir),breakdir)
# 6 BB away 3 follow
away=(E.absdist0>E.absdist1)&(E.absdist1>E.absdist2)
scenarios['S6_BB_AWAY3_FOLLOW']=(away&(bbdir!=0),bbdir)
# 7 pullback-resume after 30m impulse
# past six bars excluding source; identify directional impulse from close6 to max/min of prior 5 bars; shallow retrace within last two then source resumes across prev high/low
c6=E.close6.to_numpy(); prior_high=np.nanmax(np.vstack([E[f'high{k}'].to_numpy() for k in range(1,6)]).T,axis=1); prior_low=np.nanmin(np.vstack([E[f'low{k}'].to_numpy() for k in range(1,6)]).T,axis=1)
imp_up=(prior_high-c6)>=.30*E.S; imp_dn=(c6-prior_low)>=.30*E.S
last2low=np.nanmin(np.vstack([E.low1,E.low2]).T,axis=1); last2high=np.nanmax(np.vstack([E.high1,E.high2]).T,axis=1)
retr_up=(prior_high-last2low>=.08*E.S)&(prior_high-last2low<=.30*E.S)
retr_dn=(last2high-prior_low>=.08*E.S)&(last2high-prior_low<=.30*E.S)
resume_up=imp_up&retr_up&(bodydir==1)&(E.bodyS>=.10)&(E.c>E.high1)
resume_dn=imp_dn&retr_dn&(bodydir==-1)&(E.bodyS>=.10)&(E.c<E.low1)
prdir=np.where(resume_up,1,np.where(resume_dn,-1,0))
scenarios['S7_IMPULSE_PULLBACK_RESUME']=(prdir!=0,prdir)
# 8 H1 impulse aligned M5 continuation after one-bar counter/pause
# Map previous completed H1 to source bar: source belongs H1 block; use prior H1
h1start=E.source_m5.dt.floor('1h'); h1pos=H1.index.searchsorted(h1start)-1
validh=(h1pos>=0)&(h1pos<len(H1)); h1o=np.full(len(E),np.nan);h1c=np.full(len(E),np.nan)
h1o[validh]=H1.open.to_numpy()[h1pos[validh]]; h1c[validh]=H1.close.to_numpy()[h1pos[validh]]
h1dir=np.sign(h1c-h1o).astype(float); h1body=np.abs(h1c-h1o)/E.S
pause=np.sign(E.close1-E.open1)
h1resume=(h1body>=.30)&(h1dir!=0)&(bodydir==h1dir)&(E.bodyS>=.10)&((pause==-h1dir)|(np.abs(E.close1-E.open1)/E.S<.05))
scenarios['S8_H1_IMPULSE_M5_RESUME']=(h1resume,h1dir)
# Future first-touch labels from decision: +/- .25S within 15m and 30m. M1 source close is origin.
arr=D.index.to_numpy(dtype='datetime64[ns]'); hiv=D.high.to_numpy(); lov=D.low.to_numpy(); closev=D.close.to_numpy()
def label_first(horizon,k=.25):
 labs=np.zeros(len(E),dtype=np.int8); elapsed=np.full(len(E),np.nan)
 for j,r in enumerate(E.itertuples()):
  p=np.searchsorted(arr,np.datetime64(r.decision),side='left'); q=np.searchsorted(arr,np.datetime64(r.decision+pd.Timedelta(minutes=horizon)),side='left')
  u=r.origin_close+k*r.S; dn=r.origin_close-k*r.S
  for i in range(p,q):
   U=hiv[i]>=u; Dn=lov[i]<=dn
   if U and Dn: labs[j]=99; elapsed[j]=(pd.Timestamp(arr[i])-r.decision).total_seconds()/60; break
   if U: labs[j]=1; elapsed[j]=(pd.Timestamp(arr[i])-r.decision).total_seconds()/60; break
   if Dn: labs[j]=-1; elapsed[j]=(pd.Timestamp(arr[i])-r.decision).total_seconds()/60; break
 return labs,elapsed
E['first25_15'],E['hitmin15']=label_first(15,.25); E['first25_30'],E['hitmin30']=label_first(30,.25)
# Outcome summary
out=[]
def summarize(name,mask,pdir,label='first25_15'):
 mask=np.asarray(mask)&np.isfinite(pdir)&(np.asarray(pdir)!=0)
 for period,pmask in [('2024H1',(E.year==2024)&(E.source_m5<'2024-07-01')),('2024H2',(E.year==2024)&(E.source_m5>='2024-07-01')),('2024',(E.year==2024)),('2025',(E.year==2025)),('2026',(E.year==2026))]:
  zmask=mask&pmask.to_numpy(); z=E.loc[zmask]; pdv=np.asarray(pdir)[zmask]; lab=z[label].to_numpy()
  resolved=np.isin(lab,[-1,1]); win=lab==pdv; loss=(lab==-pdv)
  N=len(z); R=resolved.sum();
  out.append(dict(scenario=name,period=period,N=N,coverage=N/max(1,pmask.sum()),resolved=R,move_rate=R/max(1,N),dir_acc=(win[resolved].mean() if R else np.nan),all_win_rate=win.mean() if N else np.nan,all_loss_rate=loss.mean() if N else np.nan,edge_score=((win.sum()-loss.sum())/N if N else np.nan)))
for name,(mask,pdir) in scenarios.items(): summarize(name,mask,pdir)
R=pd.DataFrame(out); R.to_csv('/mnt/data/scenario_handcoded_results.csv',index=False)
E.to_pickle('/mnt/data/scenario_events.pkl')
print('POP',E.groupby('year').size().to_dict())
print('\n2024/25/26 handcoded summary')
print(R[R.period.isin(['2024','2025','2026'])].pivot(index='scenario',columns='period',values=['N','dir_acc','edge_score']).round(3).to_string())
# scenario overlap / no-scenario coverage
for y in [2024,2025,2026]:
 mm=np.zeros((len(E),len(scenarios)),bool)
 for j,(name,(m,d)) in enumerate(scenarios.items()): mm[:,j]=np.asarray(m)&(np.asarray(d)!=0)
 yy=E.year.to_numpy()==y
 print('year',y,'any scenario',mm[yy].any(axis=1).mean(),'median count',np.median(mm[yy].sum(axis=1)),'none',np.sum(~mm[yy].any(axis=1)))
