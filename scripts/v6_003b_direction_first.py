import pandas as pd, numpy as np, sys, time
from pathlib import Path
from numba import njit
sys.path.insert(0,'/mnt/data')
from v6_core_repro import load_m1,resample_ohlc,pivot_events,bos_owner_with_break


def wilder(s,n): return s.ewm(alpha=1/n,adjust=False,min_periods=n).mean()

def tf_features(m1,rule,minutes):
    b=resample_ohlc(m1,rule)
    up=b.high.diff(); down=-b.low.diff()
    pdm=pd.Series(np.where((up>down)&(up>0),up,0.0),index=b.index)
    mdm=pd.Series(np.where((down>up)&(down>0),down,0.0),index=b.index)
    prev=b.close.shift(1)
    tr=pd.concat([(b.high-b.low),(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    atr=wilder(tr,14)
    pdi=100*wilder(pdm,14)/atr; mdi=100*wilder(mdm,14)/atr
    ema12=b.close.ewm(span=12,adjust=False,min_periods=12).mean()
    ema26=b.close.ewm(span=26,adjust=False,min_periods=26).mean()
    f=pd.DataFrame(index=b.index)
    f['dmi']=np.sign(pdi-mdi); f.loc[(pdi-mdi).isna(),'dmi']=np.nan
    f['macdline']=np.sign(ema12-ema26); f.loc[(ema12-ema26).isna(),'macdline']=np.nan
    if minutes==60:
        disp=b.close-b.close.shift(24);f['disp24']=np.sign(disp);f.loc[disp.isna(),'disp24']=np.nan
    f['available_at']=f.index+pd.Timedelta(minutes=minutes)
    pe=pivot_events(b,2,minutes);ends,own,_,_,_=bos_owner_with_break(b,pe,minutes)
    return f.reset_index(names='bar_open'),ends,own

def attach_priors(q,m1):
    h1,e1,o1=tf_features(m1,'60min',60)
    h4,_,_=tf_features(m1,'240min',240)
    m30=resample_ohlc(m1,'30min');p30=pivot_events(m30,2,30);e30,o30,_,_,_=bos_owner_with_break(m30,p30,30)
    z=q.sort_values('sweep_time').copy()
    h1=h1.rename(columns={'dmi':'dmi_h1','macdline':'macd_h1','disp24':'disp_h1_24','available_at':'h1_av'})
    h4=h4.rename(columns={'dmi':'dmi_h4','macdline':'macd_h4','available_at':'h4_av'})
    z=pd.merge_asof(z,h1[['h1_av','dmi_h1','macd_h1','disp_h1_24']].sort_values('h1_av'),left_on='sweep_time',right_on='h1_av',direction='backward',allow_exact_matches=True)
    z=pd.merge_asof(z.sort_values('sweep_time'),h4[['h4_av','dmi_h4','macd_h4']].sort_values('h4_av'),left_on='sweep_time',right_on='h4_av',direction='backward',allow_exact_matches=True)
    tt=z.sweep_time.to_numpy(dtype='datetime64[ns]')
    p=np.searchsorted(e1,tt,side='right')-1;s1=np.zeros(len(z),np.int8);ok=p>=0;s1[ok]=o1[p[ok]]
    p=np.searchsorted(e30,tt,side='right')-1;s30=np.zeros(len(z),np.int8);ok=p>=0;s30[ok]=o30[p[ok]]
    def consensus(a,b):
        a=np.nan_to_num(a,nan=0).astype(int);b=np.nan_to_num(b,nan=0).astype(int)
        return np.where((a==b)&(a!=0),a,0).astype(int)
    z['DP1_DMI_H1']=np.nan_to_num(z.dmi_h1,nan=0).astype(int)
    z['DP2_DMI_H1H4']=consensus(z.dmi_h1,z.dmi_h4)
    z['DP3_MACD_H1H4']=consensus(z.macd_h1,z.macd_h4)
    z['C1_DISP_H1_24']=np.nan_to_num(z.disp_h1_24,nan=0).astype(int)
    z['S1_STRUCT_H1M30']=np.where((s1==s30)&(s1!=0),s1,0).astype(int)
    return z

@njit
def parent_resolve(starts,dirs,entry,sl,risk,hi,lo,sp):
    n=len(starts);out=np.full(n,-1,np.int64)
    for a in range(n):
        tp=entry[a]+dirs[a]*risk[a]
        for i in range(starts[a]+1,len(hi)):
            if dirs[a]==1: ht=hi[i]>=tp;hs=lo[i]<=sl[a]
            else:
                ah=hi[i]+sp[i];al=lo[i]+sp[i];ht=al<=tp;hs=ah>=sl[a]
            if (ht and hs) or hs or ht: out[a]=i;break
    return out

@njit
def pending_fill(starts,ends,dirs,entry0,sl0,risk0,limit,hi,lo,sp):
    n=len(starts);fi=np.full(n,-1,np.int64)
    for a in range(n):
        for i in range(starts[a],min(ends[a]+1,len(hi))):
            if dirs[a]==1:
                terminal=(lo[i]<=sl0[a]) or (hi[i]>=entry0[a]+risk0[a]);fill=(lo[i]+sp[i])<=limit[a]
            else:
                terminal=(hi[i]+sp[i]>=sl0[a]) or (lo[i]+sp[i]<=entry0[a]-risk0[a]);fill=hi[i]>=limit[a]
            if terminal: break
            if fill: fi[a]=i;break
    return fi

@njit
def raw_and_h(fi,dirs,entry,sl,risk,hi,lo,sp):
    n=len(fi);h1=np.zeros(n,np.int8);h3=np.zeros(n,np.int8);h5=np.zeros(n,np.int8);oc=np.zeros(n,np.int8);ri=np.full(n,-1,np.int64)
    # oc 1 TP5, 2 BE after 3R, 3 SL, 4 censored
    for a in range(n):
        if fi[a]<0: continue
        hit3=False
        for i in range(fi[a],len(hi)):
            if dirs[a]==1:
                fav=hi[i]-entry[a];stop_orig=lo[i]<=sl[a];stop_be=lo[i]<=entry[a]
            else:
                ah=hi[i]+sp[i];al=lo[i]+sp[i];fav=entry[a]-al;stop_orig=ah>=sl[a];stop_be=ah>=entry[a]
            r=fav/risk[a]
            if not hit3:
                if stop_orig:
                    oc[a]=3;ri[a]=i;break
                if r>=1: h1[a]=1
                if r>=3:
                    h3[a]=1;hit3=True
                    if r>=5:
                        h5[a]=1;oc[a]=1;ri[a]=i;break
                    continue
            else:
                if stop_be:
                    oc[a]=2;ri[a]=i;break
                if r>=5:
                    h5[a]=1;oc[a]=1;ri[a]=i;break
        if fi[a]>=0 and oc[a]==0: oc[a]=4
    return h1,h3,h5,oc,ri

segments={
'GOLD22':('/mnt/data/GOLD22_repro_broad.csv',[Path('/mnt/data/v6_003a_raw/gold/GOLD#_M1_202201030100_202212302357.csv')],'GOLD',0.01),
'GOLD2325':('/mnt/data/GOLD2325_repro_broad.csv',sorted(Path('/mnt/data/v6_003a_raw/gold').glob('GOLD#_M1_202[3-5]*.csv')),'GOLD',0.01),
'BTCUSD':('/mnt/data/BTCUSD_repro_broad.csv',[Path('/mnt/data/v6_003a_raw/goldlike/BTCUSD#_M1_202301010000_202512310000.csv')],'BTCUSD',0.01),
'USDJPY':('/mnt/data/USDJPY_repro_broad.csv',[Path('/mnt/data/v6_003a_raw/goldlike/USDJPY#_M1_202301020901_202512310000.csv')],'USDJPY',0.001),
'XAUEUR':('/mnt/data/XAUEUR_repro_broad.csv',[Path('/mnt/data/v6_003a_raw/goldlike/XAUEUR#_M1_202301030101_202512302358.csv')],'XAUEUR',0.01),
}
frames=[]
for seg,(csv,paths,market,point) in segments.items():
    q=pd.read_csv(csv,parse_dates=['sweep_time','trigger_time']);q=q[q.d1_atr.notna()].copy();q['segment']=seg;q['market']=market
    m=load_m1(paths); mt=m.index.to_numpy(dtype='datetime64[ns]');sp=m.spread.to_numpy(float)*point
    ip=np.searchsorted(mt,q.trigger_time.to_numpy(dtype='datetime64[ns]'),side='left')-1;trigsp=sp[ip]
    q['entry_trigger']=np.where(q.dir.to_numpy()==1,q.trigger_close.to_numpy()+trigsp,q.trigger_close.to_numpy())
    q['sl_exec']=np.where(q.dir.to_numpy()==1,q.sweep_extreme.to_numpy(),q.sweep_extreme.to_numpy()+trigsp)
    chart=q.trigger_close.to_numpy()-q.dir.to_numpy()*0.5*np.abs(q.trigger_close.to_numpy()-q.broken_m5_level.to_numpy())
    q['limit_entry']=np.where(q.dir.to_numpy()==1,chart+trigsp,chart)
    q['planned_risk']=np.abs(q.limit_entry-q.sl_exec)
    q['improved']=np.where(q.dir.to_numpy()==1,q.limit_entry<q.entry_trigger,q.limit_entry>q.entry_trigger)
    q=q[np.isfinite(q.planned_risk)&(q.planned_risk>0)&q.improved].copy()
    q=attach_priors(q,m)
    starts=np.searchsorted(mt,q.trigger_time.to_numpy(dtype='datetime64[ns]'),side='left')-1
    entry0=q.entry_trigger.to_numpy(float);sl0=q.sl_exec.to_numpy(float);risk0=np.abs(entry0-sl0)
    pres=parent_resolve(starts,q.dir.to_numpy(np.int8),entry0,sl0,risk0,m.high.to_numpy(float),m.low.to_numpy(float),sp)
    ends=np.where(pres>=0,pres,len(mt)-1);pstarts=np.searchsorted(mt,q.trigger_time.to_numpy(dtype='datetime64[ns]'),side='right')
    fi=pending_fill(pstarts,ends,q.dir.to_numpy(np.int8),entry0,sl0,risk0,q.limit_entry.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),sp)
    h1,h3,h5,oc,ri=raw_and_h(fi,q.dir.to_numpy(np.int8),q.limit_entry.to_numpy(float),q.sl_exec.to_numpy(float),q.planned_risk.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),sp)
    q['fill_i']=fi;q['fill_time']=pd.to_datetime(np.where(fi>=0,mt[np.maximum(fi,0)],np.datetime64('NaT')))
    q['hit1']=h1;q['hit3']=h3;q['hit5']=h5
    q['outcome']=np.select([oc==1,oc==2,oc==3,oc==4],['TP5','BE','SL','CENSORED'],default='NOFILL');q.loc[fi<0,'outcome']='NOFILL'
    q['resolved_at']=pd.to_datetime(np.where(ri>=0,mt[np.maximum(ri,0)],np.datetime64('NaT')))
    frames.append(q)

A=pd.concat(frames,ignore_index=True).sort_values(['market','sweep_time']).reset_index(drop=True)
A.to_csv('/mnt/data/V6_003B_DIRECTION_FIRST_LEDGER.csv',index=False)
print('BROAD geometry-valid',len(A),'direct',int(A.m1_direct_transfer.sum()),'non-direct',int((~A.m1_direct_transfer).sum()))
priors=['DP1_DMI_H1','DP2_DMI_H1H4','DP3_MACD_H1H4','C1_DISP_H1_24','S1_STRUCT_H1M30']
rows=[];envrows=[];econrows=[]
for p in priors:
    avail=A[p]!=0;elig=A[avail & (A[p]==A.dir)].copy();opp=A[avail & (A[p]!=A.dir)].copy()
    f=elig[elig.fill_time.notna()].copy()
    print('\n',p,'avail',int(avail.sum()),'LONG',int((A[p]==1).sum()),'SHORT',int((A[p]==-1).sum()),'NEUT',int((A[p]==0).sum()),'confirmed',len(elig),'counter',len(opp),'fill',len(f))
    print(' raw hit',round(f.hit1.mean(),4),round(f.hit3.mean(),4),round(f.hit5.mean(),4),'directfill',int(f.m1_direct_transfer.sum()),'recovered_non_direct_fill',int((~f.m1_direct_transfer).sum()))
    # exposure-adjusted current H lifecycle on prior-confirmed fills
    accepted=[];blocked=[]
    ff=f.sort_values(['market','fill_time','trigger_time']).copy()
    for market,g in ff.groupby('market',sort=False):
        active=[]
        for idx,r in g.sort_values('fill_time').iterrows():
            t=r.fill_time
            active=[j for j in active if pd.isna(ff.loc[j,'resolved_at']) or ff.loc[j,'resolved_at']>t]
            if any(int(ff.loc[j,'dir'])==-int(r.dir) for j in active): blocked.append(idx)
            else: accepted.append(idx);active.append(idx)
    acc=ff.loc[accepted].copy() if accepted else ff.iloc[0:0].copy()
    acc['pnl_R']=np.select([acc.outcome.eq('TP5'),acc.outcome.eq('BE'),acc.outcome.eq('SL')],[4.5,0.75,-1.0],default=np.nan)
    pos=acc[acc.pnl_R>0]
    print(' accepted',len(acc),'blocked',len(blocked),'WR',round(float((acc.pnl_R>0).mean()),4) if len(acc) else np.nan,'avg+',round(float(pos.pnl_R.mean()),4) if len(pos) else np.nan,'EV',round(float(acc.pnl_R.mean()),4) if len(acc) else np.nan,'total',round(float(acc.pnl_R.sum()),2) if len(acc) else np.nan)
    for subset,name in [(f,'ALL'),(f[f.m1_direct_transfer],'DIRECT'),(f[~f.m1_direct_transfer],'RECOVERED_NON_DIRECT')]:
        rows.append({'prior':p,'subset':name,'availability':int(avail.sum()),'oppN':len(elig),'fillN':len(subset),'hit1':subset.hit1.mean() if len(subset) else np.nan,'hit3':subset.hit3.mean() if len(subset) else np.nan,'hit5':subset.hit5.mean() if len(subset) else np.nan})
    econrows.append({'prior':p,'confirmed_oppN':len(elig),'fillN':len(f),'acceptedN':len(acc),'blockedN':len(blocked),'WR':float((acc.pnl_R>0).mean()) if len(acc) else np.nan,'avg_positive_R':float(pos.pnl_R.mean()) if len(pos) else np.nan,'EV_R':float(acc.pnl_R.mean()) if len(acc) else np.nan,'total_R':float(acc.pnl_R.sum()) if len(acc) else np.nan,'TP5':int((acc.outcome=='TP5').sum()),'BE':int((acc.outcome=='BE').sum()),'SL':int((acc.outcome=='SL').sum())})
    for (m,y),g in elig.groupby(['market','year']):
        z=g[g.fill_time.notna()]
        envrows.append({'prior':p,'market':m,'year':int(y),'oppN':len(g),'fillN':len(z),'hit1':z.hit1.mean() if len(z) else np.nan,'hit3':z.hit3.mean() if len(z) else np.nan,'hit5':z.hit5.mean() if len(z) else np.nan,'non_direct_fillN':int((~z.m1_direct_transfer).sum())})

pd.DataFrame(rows).to_csv('/mnt/data/V6_003B_DIRECTION_FIRST_SUMMARY.csv',index=False)
pd.DataFrame(econrows).to_csv('/mnt/data/V6_003B_DIRECTION_FIRST_ECONOMICS.csv',index=False)
pd.DataFrame(envrows).to_csv('/mnt/data/V6_003B_DIRECTION_FIRST_BY_ENV.csv',index=False)
