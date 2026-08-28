import pandas as pd,numpy as np,sys
from pathlib import Path
sys.path.insert(0,'/mnt/data')
from v6_core_repro import load_m1,resample_ohlc

def tf(m,rule,minu):
 b=resample_ohlc(m,rule);d=b.close-b.close.shift(14);s=np.sign(d);s[d.isna()]=np.nan
 return pd.DataFrame({'av':b.index+pd.Timedelta(minutes=minu),'s':s})
def attach(q,m):
 a=tf(m,'60min',60).rename(columns={'av':'a1','s':'s1'});b=tf(m,'240min',240).rename(columns={'av':'a4','s':'s4'});z=q.sort_values('sweep_time').copy()
 z=pd.merge_asof(z,a.sort_values('a1'),left_on='sweep_time',right_on='a1',direction='backward',allow_exact_matches=True);z=pd.merge_asof(z.sort_values('sweep_time'),b.sort_values('a4'),left_on='sweep_time',right_on='a4',direction='backward',allow_exact_matches=True)
 x=np.nan_to_num(z.s1,nan=0).astype(int);y=np.nan_to_num(z.s4,nan=0).astype(int);z['C2_DISP14_H1H4']=np.where((x==y)&(x!=0),x,0);return z
segments={'GOLD22':[Path('/mnt/data/v6_003a_raw/gold/GOLD#_M1_202201030100_202212302357.csv')],'GOLD2325':sorted(Path('/mnt/data/v6_003a_raw/gold').glob('GOLD#_M1_202[3-5]*.csv')),'BTCUSD':[Path('/mnt/data/v6_003a_raw/goldlike/BTCUSD#_M1_202301010000_202512310000.csv')],'USDJPY':[Path('/mnt/data/v6_003a_raw/goldlike/USDJPY#_M1_202301020901_202512310000.csv')],'XAUEUR':[Path('/mnt/data/v6_003a_raw/goldlike/XAUEUR#_M1_202301030101_202512302358.csv')]}
A=pd.read_csv('/mnt/data/V6_003C_CONVENTIONAL_DIRECTION_LEDGER.csv',parse_dates=['sweep_time','trigger_time','fill_time','resolved_at']);o=[]
for seg,paths in segments.items():o.append(attach(A[A.segment==seg].copy(),load_m1(paths)))
Z=pd.concat(o,ignore_index=True).sort_values(['market','sweep_time']).reset_index(drop=True);Z.to_csv('/mnt/data/V6_003C_RSI_CONTROL_LEDGER.csv',index=False)

def econ(q):
 f=q[q.fill_time.notna()].sort_values(['market','fill_time','trigger_time']).copy();acc=[]
 for market,g in f.groupby('market',sort=False):
  active=[]
  for idx,r in g.sort_values('fill_time').iterrows():
   t=r.fill_time;active=[j for j in active if pd.isna(f.loc[j,'resolved_at']) or f.loc[j,'resolved_at']>t]
   if not any(int(f.loc[j,'dir'])==-int(r.dir) for j in active):acc.append(idx);active.append(idx)
 a=f.loc[acc].copy();a['pnl']=np.select([a.outcome.eq('TP5'),a.outcome.eq('BE'),a.outcome.eq('SL')],[4.5,.75,-1.],default=np.nan);p=a[a.pnl>0]
 return len(q),len(f),len(a),(a.pnl>0).mean(),p.pnl.mean() if len(p) else np.nan,a.pnl.mean(),a.pnl.sum()
for p in ['RSI14_H1H4','C2_DISP14_H1H4']:
 print('\n',p,'availability',(Z[p]!=0).sum())
 for ag in ['ALIGNED','OPPOSED']:
  b=Z[(Z[p]!=0)&((Z[p]==Z.dir) if ag=='ALIGNED' else (Z[p]==-Z.dir))]
  for flag,name in [(None,'ALL'),(True,'DIRECT'),(False,'NON_DIRECT')]:
   q=b if flag is None else b[b.m1_direct_transfer==flag];print(ag,name,econ(q))
 # direct env
 q=Z[(Z[p]!=0)&(Z[p]==Z.dir)&Z.m1_direct_transfer]
 print('ENV aligned direct')
 for (m,y),g in q.groupby(['market','year']):
  f=g[g.fill_time.notna()];print(m,y,len(f),round(f.hit1.mean(),3),round(f.hit3.mean(),3),round(f.hit5.mean(),3))
# agreement/discordant direct
D=Z[Z.m1_direct_transfer & (Z.RSI14_H1H4!=0)&(Z.C2_DISP14_H1H4!=0)]
print('\nagreement RSI C2',len(D),(D.RSI14_H1H4==D.C2_DISP14_H1H4).mean())
X=D[D.RSI14_H1H4!=D.C2_DISP14_H1H4]
for name,p in [('RSI','RSI14_H1H4'),('C2','C2_DISP14_H1H4')]:
 q=X[X[p]==X.dir];f=q[q.fill_time.notna()];print(name,'discord match',len(q),len(f),f.hit1.mean() if len(f) else None,f.hit3.mean() if len(f) else None,f.hit5.mean() if len(f) else None)
