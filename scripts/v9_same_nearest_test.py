from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd, numpy as np, heapq, math

SRC=Path('/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv')
FMT='%Y.%m.%d %H:%M:%S'

def load_safe(start, end):
    rows=[]
    with SRC.open('r',encoding='utf-8-sig') as f:
        f.readline()
        for line in f:
            p=line.rstrip('\n').split('\t')
            if len(p)<6: continue
            ts=datetime.strptime(p[0]+' '+p[1],FMT)
            if ts < start: continue
            if ts >= end: break
            rows.append((ts,float(p[2]),float(p[3]),float(p[4]),float(p[5])))
    return pd.DataFrame(rows,columns=['ts','open','high','low','close']).set_index('ts')

def aggregate(df, hours):
    freq=f'{hours}h'
    # timestamps aligned to midnight
    g=df.resample(freq, origin='start_day', label='left', closed='left')
    bars=g.agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),n=('close','size')).dropna()
    bars['start']=bars.index
    bars['known_at']=bars.index + pd.Timedelta(hours=hours)
    return bars.reset_index(drop=True)

def pivots(bars, tf):
    out=[]
    mins=240 if tf=='H4' else 60
    for i in range(2,len(bars)-2):
        b=bars.iloc[i]; left=bars.iloc[i-2:i]; right=bars.iloc[i+1:i+3]
        known=right.iloc[-1]['start']+pd.Timedelta(minutes=mins)
        if b['high'] > left['high'].max() and b['high'] >= right['high'].max():
            out.append(dict(id=f'{tf}_BSL_{b.start:%Y%m%d_%H%M}', side='UP', price=float(b.high), source=b.start.to_pydatetime(), known_at=known.to_pydatetime()))
        if b['low'] < left['low'].min() and b['low'] <= right['low'].min():
            out.append(dict(id=f'{tf}_SSL_{b.start:%Y%m%d_%H%M}', side='DOWN', price=float(b.low), source=b.start.to_pydatetime(), known_at=known.to_pydatetime()))
    return sorted(out,key=lambda x:(x['known_at'],x['id']))

def build_arrivals(df, objs):
    births={}
    for o in objs: births.setdefault(o['known_at'],[]).append(o)
    # heaps store active levels
    bsl=[]; ssl=[]
    active={}
    events=[]
    for ts,row in df.iterrows():
        t=ts.to_pydatetime()
        for o in births.get(t,[]):
            active[o['id']]=o
            if o['side']=='UP': heapq.heappush(bsl,(o['price'],o['id']))
            else: heapq.heappush(ssl,(-o['price'],o['id']))
        ra_up=[]; ra_dn=[]
        H=float(row.high); L=float(row.low)
        # lazy + pop all crossed
        while bsl:
            price,oid=bsl[0]
            if oid not in active:
                heapq.heappop(bsl); continue
            if price < H:
                heapq.heappop(bsl); ra_up.append(active.pop(oid))
            else: break
        while ssl:
            nprice,oid=ssl[0]; price=-nprice
            if oid not in active:
                heapq.heappop(ssl); continue
            if price > L:
                heapq.heappop(ssl); ra_dn.append(active.pop(oid))
            else: break
        if not ra_up and not ra_dn: continue
        if ra_up and ra_dn:
            side='OVERLAP'; ref=np.nan
        elif ra_up:
            side='UP'; ref=max(o['price'] for o in ra_up)
        else:
            side='DOWN'; ref=min(o['price'] for o in ra_dn)
        # snapshot nearest active levels post-raid
        def clean_bsl():
            while bsl and bsl[0][1] not in active: heapq.heappop(bsl)
        def clean_ssl():
            while ssl and ssl[0][1] not in active: heapq.heappop(ssl)
        clean_bsl(); clean_ssl()
        nearest_bsl=bsl[0][0] if bsl else np.nan
        nearest_ssl=-ssl[0][0] if ssl else np.nan
        events.append(dict(ts=t,side=side,ref=ref,up_ids=';'.join(o['id'] for o in ra_up),dn_ids=';'.join(o['id'] for o in ra_dn),nearest_bsl=nearest_bsl,nearest_ssl=nearest_ssl, m1_open=float(row.open),m1_high=H,m1_low=L,m1_close=float(row.close)))
    return pd.DataFrame(events)

def resolve(events):
    rec=[]; state=None; primary=None; challenger=None
    directional_idxs=[i for i,r in events.iterrows() if r.side in ('UP','DOWN')]
    next_dir={directional_idxs[j]: (events.loc[directional_idxs[j+1],'side'] if j+1<len(directional_idxs) else None) for j in range(len(directional_idxs))}
    seed_done=False
    for i,r in events.iterrows():
        before=state; pbefore=primary
        eligible=False; resolution=None
        if r.side=='OVERLAP':
            # leave semantic state unchanged; event itself unresolved
            after=state; pafter=primary
        elif state is None:
            state='ACTIVE'; primary=r.side; challenger=None; after=state;pafter=primary; resolution='SEED'
        elif state=='ACTIVE':
            if r.side==primary:
                state='ACTIVE'; resolution='PRIMARY_CONTINUES'; eligible=True
            else:
                state='CHALLENGED'; challenger=r.side; resolution='CHALLENGE_OPENS'
            after=state;pafter=primary
        else: # challenged
            if r.side==primary:
                state='ACTIVE'; challenger=None; resolution='OLD_PRIMARY_WINS'; eligible=True
            else:
                primary=r.side; state='ACTIVE'; challenger=None; resolution='CHALLENGER_EARNED'; eligible=True
            after=state;pafter=primary
        topo='NA'; ds=do=np.nan
        if eligible and r.side in ('UP','DOWN'):
            # primary equals current arrival side after active resolution
            ref=float(r.ref)
            if primary=='UP':
                if not pd.isna(r.nearest_bsl): ds=float(r.nearest_bsl)-ref
                if not pd.isna(r.nearest_ssl): do=ref-float(r.nearest_ssl)
            else:
                if not pd.isna(r.nearest_ssl): ds=ref-float(r.nearest_ssl)
                if not pd.isna(r.nearest_bsl): do=float(r.nearest_bsl)-ref
            # only valid forward distances
            if not pd.isna(ds) and ds<0: ds=np.nan
            if not pd.isna(do) and do<0: do=np.nan
            if not pd.isna(ds) and not pd.isna(do): topo='SAME_NEAREST' if ds<do else 'OPPOSITE_NEAREST'
            elif pd.isna(ds) and pd.isna(do): topo='BOTH_MISSING'
            elif pd.isna(ds): topo='NO_SAME_TARGET'
            else: topo='NO_OPPOSITE_TARGET'
        nside=next_dir.get(i)
        hit=(nside==primary) if (eligible and nside is not None) else None
        rec.append(dict(idx=i,ts=r.ts,arrival_side=r.side,ref=r.ref,before=before,after=after,primary=primary,resolution=resolution,eligible=eligible,topology=topo,d_same=ds,d_opp=do,next_side=nside,hit=hit,nearest_bsl=r.nearest_bsl,nearest_ssl=r.nearest_ssl))
    return pd.DataFrame(rec)

def run_block(df, start, end, name):
    bdf=df[(df.index>=start)&(df.index<end)]
    h4=aggregate(bdf,4)
    objs=pivots(h4,'H4')
    ev=build_arrivals(bdf,objs)
    rr=resolve(ev)
    elig=rr[(rr.eligible)&(rr.hit.notna())]
    sn=elig[elig.topology=='SAME_NEAREST']
    print('\n',name,'M1',len(bdf),'H4bars',len(h4),'objs',len(objs),'events',len(ev),'dir',sum(ev.side!='OVERLAP'),'overlap',sum(ev.side=='OVERLAP'))
    print('eligible',len(elig),'hits',int(elig.hit.sum()),float(elig.hit.mean()) if len(elig) else None)
    print(elig.topology.value_counts(dropna=False).to_dict())
    print('SN',len(sn),int(sn.hit.sum()),float(sn.hit.mean()) if len(sn) else None)
    comp=elig[elig.topology!='SAME_NEAREST']
    print('notSN',len(comp),int(comp.hit.sum()),float(comp.hit.mean()) if len(comp) else None)
    print('resolutions',rr.resolution.value_counts(dropna=False).to_dict())
    return bdf,h4,objs,ev,rr

if __name__=='__main__':
    df=load_safe(datetime(2024,1,1),datetime(2025,7,1))
    a=run_block(df,datetime(2024,1,1),datetime(2025,1,1),'2024')
    b=run_block(df,datetime(2025,1,1),datetime(2025,7,1),'2025H1')
    # save temp
    b[-1].to_csv('/mnt/data/rr_2025h1.csv',index=False)
