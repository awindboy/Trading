import pandas as pd, numpy as np
from datetime import datetime
from pathlib import Path
SAFE='/mnt/data/GOLD_M1_SAFE_TO_20250630.tsv'

def load():
    df=pd.read_csv(SAFE,sep='\t',usecols=['<DATE>','<TIME>','<OPEN>','<HIGH>','<LOW>','<CLOSE>'])
    df['ts']=pd.to_datetime(df['<DATE>']+' '+df['<TIME>'],format='%Y.%m.%d %H:%M:%S')
    return df[['ts','<OPEN>','<HIGH>','<LOW>','<CLOSE>']].rename(columns={'<OPEN>':'open','<HIGH>':'high','<LOW>':'low','<CLOSE>':'close'}).set_index('ts')

def aggregate(df,hours):
    g=df.resample(f'{hours}h',origin='start_day',label='left',closed='left')
    x=g.agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),n=('close','size')).dropna().reset_index()
    x['known_at']=x.ts+pd.Timedelta(hours=hours)
    return x

def pivots(bars,tf,hours):
    out=[]
    for i in range(2,len(bars)-2):
        b=bars.iloc[i]; left=bars.iloc[i-2:i]; right=bars.iloc[i+1:i+3]
        known=right.iloc[-1].ts+pd.Timedelta(hours=hours)
        if b.high > left.high.max() and b.high >= right.high.max():
            out.append([f'{tf}_BSL_{b.ts:%Y%m%d_%H%M}','UP',float(b.high),b.ts,known,pd.NaT])
        if b.low < left.low.min() and b.low <= right.low.min():
            out.append([f'{tf}_SSL_{b.ts:%Y%m%d_%H%M}','DOWN',float(b.low),b.ts,known,pd.NaT])
    return pd.DataFrame(out,columns=['id','side','price','source','known_at','raid_at'])

def attach_raids(df,objs):
    times=df.index.values.astype('datetime64[ns]')
    highs=df.high.to_numpy(); lows=df.low.to_numpy()
    raid=[]
    for r in objs.itertuples(index=False):
        k=np.datetime64(r.known_at.to_datetime64())
        i=int(np.searchsorted(times,k,side='left'))
        if i>=len(times): raid.append(pd.NaT); continue
        if r.side=='UP':
            a=np.flatnonzero(highs[i:] > r.price)
        else:
            a=np.flatnonzero(lows[i:] < r.price)
        raid.append(pd.Timestamp(times[i+int(a[0])]) if len(a) else pd.NaT)
    o=objs.copy(); o['raid_at']=raid; return o

def events_from_objs(df,objs,start,end):
    o=objs[(objs.raid_at.notna()) & (objs.raid_at>=start) & (objs.raid_at<end)].copy()
    events=[]
    for t,g in o.groupby('raid_at',sort=True):
        up=g[g.side=='UP']; dn=g[g.side=='DOWN']
        if len(up) and len(dn): side='OVERLAP'; ref=np.nan
        elif len(up): side='UP'; ref=up.price.max()
        else: side='DOWN'; ref=dn.price.min()
        # active after this event, historical objects allowed; born by t, raid strictly after t or NaT
        act=objs[(objs.known_at<=t) & (objs.raid_at.isna() | (objs.raid_at>t))]
        bsl=act[act.side=='UP'].price.min() if any(act.side=='UP') else np.nan
        ssl=act[act.side=='DOWN'].price.max() if any(act.side=='DOWN') else np.nan
        row=df.loc[t]
        events.append(dict(ts=t,side=side,ref=ref,nearest_bsl=bsl,nearest_ssl=ssl,
                           up_ids=';'.join(up.id),dn_ids=';'.join(dn.id),m1_open=row.open,m1_high=row.high,m1_low=row.low,m1_close=row.close))
    return pd.DataFrame(events)

def resolve(events):
    rec=[]; state=None; primary=None; challenger=None
    diridx=[i for i,r in events.iterrows() if r.side in ('UP','DOWN')]
    nextside={diridx[j]:(events.loc[diridx[j+1],'side'] if j+1<len(diridx) else None) for j in range(len(diridx))}
    for i,r in events.iterrows():
        before=state; pbefore=primary; eligible=False; res=None
        if r.side=='OVERLAP':
            after=state
        elif state is None:
            state='ACTIVE'; primary=r.side; res='SEED'; after=state
        elif state=='ACTIVE':
            if r.side==primary:
                res='PRIMARY_CONTINUES'; eligible=True
            else:
                state='CHALLENGED'; challenger=r.side; res='CHALLENGE_OPENS'
            after=state
        else:
            if r.side==primary:
                state='ACTIVE'; challenger=None; res='OLD_PRIMARY_WINS'; eligible=True
            else:
                primary=r.side; state='ACTIVE'; challenger=None; res='CHALLENGER_EARNED'; eligible=True
            after=state
        ds=do=np.nan; topo='NA'
        if eligible:
            ref=float(r.ref)
            if primary=='UP':
                if pd.notna(r.nearest_bsl): ds=float(r.nearest_bsl)-ref
                if pd.notna(r.nearest_ssl): do=ref-float(r.nearest_ssl)
            else:
                if pd.notna(r.nearest_ssl): ds=ref-float(r.nearest_ssl)
                if pd.notna(r.nearest_bsl): do=float(r.nearest_bsl)-ref
            if pd.notna(ds) and ds<0: ds=np.nan
            if pd.notna(do) and do<0: do=np.nan
            if pd.notna(ds) and pd.notna(do): topo='SAME_NEAREST' if ds<do else 'OPPOSITE_NEAREST'
            elif pd.isna(ds) and pd.isna(do): topo='BOTH_MISSING'
            elif pd.isna(ds): topo='NO_SAME_TARGET'
            else: topo='NO_OPPOSITE_TARGET'
        ns=nextside.get(i); hit=(ns==primary) if eligible and ns is not None else None
        rec.append(dict(idx=i,ts=r.ts,arrival_side=r.side,ref=r.ref,before=before,after=after,primary=primary,resolution=res,eligible=eligible,topology=topo,d_same=ds,d_opp=do,next_side=ns,hit=hit,nearest_bsl=r.nearest_bsl,nearest_ssl=r.nearest_ssl,
                        m1_open=r.m1_open,m1_high=r.m1_high,m1_low=r.m1_low,m1_close=r.m1_close))
    return pd.DataFrame(rec)

if __name__=='__main__':
    df=load(); print('m1',len(df),df.index.min(),df.index.max())
    h4=aggregate(df,4); objs=attach_raids(df,pivots(h4,'H4',4)); print('h4',len(h4),'objs',len(objs),'raided',objs.raid_at.notna().sum())
    for start,end,name in [(pd.Timestamp('2024-01-01'),pd.Timestamp('2025-01-01'),'2024'),(pd.Timestamp('2025-01-01'),pd.Timestamp('2025-07-01'),'2025H1')]:
        ev=events_from_objs(df,objs,start,end); rr=resolve(ev); elig=rr[rr.eligible & rr.hit.notna()]; sn=elig[elig.topology=='SAME_NEAREST']; notsn=elig[elig.topology!='SAME_NEAREST']
        print('\n',name,'events',len(ev),'overlap',(ev.side=='OVERLAP').sum(),'eligible',len(elig),int(elig.hit.sum()),elig.hit.mean())
        print(elig.topology.value_counts().to_dict())
        print('SN',len(sn),int(sn.hit.sum()),sn.hit.mean(),'not',len(notsn),int(notsn.hit.sum()),notsn.hit.mean())
        print(rr.resolution.value_counts(dropna=False).to_dict())
        rr.to_csv(f'/mnt/data/{name}_topology_rr.csv',index=False)
    objs.to_csv('/mnt/data/h4_liq_objs_safe.csv',index=False)
