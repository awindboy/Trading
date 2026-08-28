import pandas as pd, numpy as np, sys
from pathlib import Path
sys.path.insert(0,'/mnt/data')
from v6_core_repro import load_m1,resample_ohlc

def wilder(s,n): return s.ewm(alpha=1/n,adjust=False,min_periods=n).mean()

def tf_ind(m1,rule,minutes):
    b=resample_ohlc(m1,rule)
    # RSI14 Wilder
    d=b.close.diff();g=d.clip(lower=0);l=(-d).clip(lower=0)
    rs=wilder(g,14)/wilder(l,14).replace(0,np.nan);rsi=100-100/(1+rs)
    rsi_dir=np.sign(rsi-50);rsi_dir[rsi.isna()]=np.nan
    # Aroon25 based on time since highest high / lowest low in last 25 bars
    n=25
    def aup(a):
        # most recent highest high gets since=0
        rev=a[::-1]; since=int(np.argmax(rev)); return 100*(n-since)/n
    def adn(a):
        rev=a[::-1]; since=int(np.argmin(rev)); return 100*(n-since)/n
    au=b.high.rolling(n,min_periods=n).apply(aup,raw=True);ad=b.low.rolling(n,min_periods=n).apply(adn,raw=True)
    ar=np.sign(au-ad);ar[(au-ad).isna()]=np.nan
    # Vortex14
    prevc=b.close.shift(1);tr=pd.concat([(b.high-b.low),(b.high-prevc).abs(),(b.low-prevc).abs()],axis=1).max(axis=1)
    vmp=(b.high-b.low.shift(1)).abs();vmm=(b.low-b.high.shift(1)).abs()
    vi_p=vmp.rolling(14,min_periods=14).sum()/tr.rolling(14,min_periods=14).sum().replace(0,np.nan)
    vi_m=vmm.rolling(14,min_periods=14).sum()/tr.rolling(14,min_periods=14).sum().replace(0,np.nan)
    vi=np.sign(vi_p-vi_m);vi[(vi_p-vi_m).isna()]=np.nan
    f=pd.DataFrame({'available_at':b.index+pd.Timedelta(minutes=minutes),'aroon':ar,'vortex':vi,'rsi':rsi_dir})
    return f.reset_index(drop=True)

def attach_consensus(q,m1):
    h1=tf_ind(m1,'60min',60).rename(columns={'available_at':'h1av','aroon':'ar1','vortex':'vi1','rsi':'rsi1'})
    h4=tf_ind(m1,'240min',240).rename(columns={'available_at':'h4av','aroon':'ar4','vortex':'vi4','rsi':'rsi4'})
    z=q.sort_values('sweep_time').copy()
    z=pd.merge_asof(z,h1.sort_values('h1av'),left_on='sweep_time',right_on='h1av',direction='backward',allow_exact_matches=True)
    z=pd.merge_asof(z.sort_values('sweep_time'),h4.sort_values('h4av'),left_on='sweep_time',right_on='h4av',direction='backward',allow_exact_matches=True)
    def con(a,b):
        a=np.nan_to_num(a,nan=0).astype(int);b=np.nan_to_num(b,nan=0).astype(int);return np.where((a==b)&(a!=0),a,0)
    z['AR25_H1H4']=con(z.ar1,z.ar4);z['VI14_H1H4']=con(z.vi1,z.vi4);z['RSI14_H1H4']=con(z.rsi1,z.rsi4)
    return z

segments={
'GOLD22':([Path('/mnt/data/v6_003a_raw/gold/GOLD#_M1_202201030100_202212302357.csv')]),
'GOLD2325':(sorted(Path('/mnt/data/v6_003a_raw/gold').glob('GOLD#_M1_202[3-5]*.csv'))),
'BTCUSD':([Path('/mnt/data/v6_003a_raw/goldlike/BTCUSD#_M1_202301010000_202512310000.csv')]),
'USDJPY':([Path('/mnt/data/v6_003a_raw/goldlike/USDJPY#_M1_202301020901_202512310000.csv')]),
'XAUEUR':([Path('/mnt/data/v6_003a_raw/goldlike/XAUEUR#_M1_202301030101_202512302358.csv')]),
}
A=pd.read_csv('/mnt/data/V6_003B_DIRECTION_FIRST_LEDGER.csv',parse_dates=['sweep_time','trigger_time','fill_time','resolved_at'])
out=[]
for seg,paths in segments.items():
    q=A[A.segment==seg].copy();m=load_m1(paths);out.append(attach_consensus(q,m))
Z=pd.concat(out,ignore_index=True).sort_values(['market','sweep_time']).reset_index(drop=True)
Z.to_csv('/mnt/data/V6_003C_CONVENTIONAL_DIRECTION_LEDGER.csv',index=False)

# generic exposure economics

def econ(q):
    f=q[q.fill_time.notna()].sort_values(['market','fill_time','trigger_time']).copy();accepted=[]
    for market,g in f.groupby('market',sort=False):
        active=[]
        for idx,r in g.sort_values('fill_time').iterrows():
            t=r.fill_time;active=[j for j in active if pd.isna(f.loc[j,'resolved_at']) or f.loc[j,'resolved_at']>t]
            if not any(int(f.loc[j,'dir'])==-int(r.dir) for j in active):accepted.append(idx);active.append(idx)
    acc=f.loc[accepted].copy() if accepted else f.iloc[:0].copy();acc['pnl']=np.select([acc.outcome.eq('TP5'),acc.outcome.eq('BE'),acc.outcome.eq('SL')],[4.5,.75,-1.],default=np.nan)
    pos=acc[acc.pnl>0]
    return len(q),len(f),len(acc),float((acc.pnl>0).mean()) if len(acc) else np.nan,float(pos.pnl.mean()) if len(pos) else np.nan,float(acc.pnl.mean()) if len(acc) else np.nan,float(acc.pnl.sum()) if len(acc) else np.nan,acc

priors=['AR25_H1H4','VI14_H1H4','RSI14_H1H4','DP3_MACD_H1H4','C1_DISP_H1_24']
rows=[];env=[]
for p in priors:
    for agreement in ['ALIGNED','OPPOSED']:
        b=Z[(Z[p]!=0)&((Z[p]==Z.dir) if agreement=='ALIGNED' else (Z[p]==-Z.dir))]
        for flag,name in [(None,'ALL'),(True,'DIRECT'),(False,'NON_DIRECT')]:
            q=b if flag is None else b[b.m1_direct_transfer==flag]
            opp,fill,acc,wr,avgp,ev,total,aa=econ(q)
            f=q[q.fill_time.notna()]
            rows.append({'prior':p,'agreement':agreement,'subset':name,'availability':int((Z[p]!=0).sum()),'oppN':opp,'fillN':fill,'acceptedN':acc,'hit1':f.hit1.mean() if fill else np.nan,'hit3':f.hit3.mean() if fill else np.nan,'hit5':f.hit5.mean() if fill else np.nan,'WR':wr,'avg_pos':avgp,'EV':ev,'totalR':total})
    # env for aligned direct
    q=Z[(Z[p]!=0)&(Z[p]==Z.dir)&Z.m1_direct_transfer]
    for (m,y),g in q.groupby(['market','year']):
        f=g[g.fill_time.notna()]
        env.append({'prior':p,'market':m,'year':int(y),'oppN':len(g),'fillN':len(f),'hit1':f.hit1.mean() if len(f) else np.nan,'hit3':f.hit3.mean() if len(f) else np.nan,'hit5':f.hit5.mean() if len(f) else np.nan})
R=pd.DataFrame(rows);R.to_csv('/mnt/data/V6_003C_CONVENTIONAL_DIRECTION_SUMMARY.csv',index=False)
E=pd.DataFrame(env);E.to_csv('/mnt/data/V6_003C_CONVENTIONAL_DIRECTION_BY_ENV.csv',index=False)
print(R.to_string(index=False))

# direct aligned comparisons and discordance vs displacement
for p in ['AR25_H1H4','VI14_H1H4','RSI14_H1H4']:
    d=Z[Z.m1_direct_transfer & (Z[p]!=0)].copy(); both=d[d.C1_DISP_H1_24!=0]
    print('\n',p,'availability direct',len(d),'agreement with DISP',round((both[p]==both.C1_DISP_H1_24).mean(),4),'Nboth',len(both))
    x=both[both[p]!=both.C1_DISP_H1_24]
    for who,col in [('IND',p),('DISP','C1_DISP_H1_24')]:
        q=x[x[col]==x.dir];f=q[q.fill_time.notna()]
        print(' discord',who,'opp',len(q),'fill',len(f),'h1',round(f.hit1.mean(),3) if len(f) else None,'h3',round(f.hit3.mean(),3) if len(f) else None,'h5',round(f.hit5.mean(),3) if len(f) else None)
