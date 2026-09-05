import pandas as pd, numpy as np, importlib.util
spec=importlib.util.spec_from_file_location('b','/mnt/data/v3_v8_bridge.py'); b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
m1=b.load_gold(b.DATA)
# causal multi-TF states
bars={r:b.resample_ohlc(m1,r) for r in ['5min','30min','60min']}
for z in bars.values(): z['atr14']=b.atr_series(z)
p5=b.pivot_events(bars['5min'],2,5); p30=b.pivot_events(bars['30min'],2,30); p60=b.pivot_events(bars['60min'],2,60)
e5,o5,c5,h5,l5=b.bos_owner_with_break(bars['5min'],p5,5)
e30,o30,c30,_,_=b.bos_owner_with_break(bars['30min'],p30,30)
e60,o60,c60,_,_=b.bos_owner_with_break(bars['60min'],p60,60)
# helper at scalar time
def state_scalar(t, ends, vals):
    p=np.searchsorted(ends,np.datetime64(t),side='right')-1
    return int(vals[p]) if p>=0 else 0
# future M1 labels from confirmation close, not event-source close
D=pd.read_pickle('/mnt/data/slow_m1.pkl'); idx=D.index.to_numpy(dtype='datetime64[ns]'); H=D.h.to_numpy(float); L=D.l.to_numpy(float); C=D.c.to_numpy(float)
def close_before(t):
    p=np.searchsorted(idx,np.datetime64(t),side='left')-1
    return C[p] if p>=0 else np.nan
def first_touch(t, origin,S,tp,sl,mins):
    p=np.searchsorted(idx,np.datetime64(t),'left');q=np.searchsorted(idx,np.datetime64(t+pd.Timedelta(minutes=mins)),'left')
    up=origin+tp*S; dn=origin-sl*S
    # symmetric direction label relative to predicted direction handled outside; return signed first absolute barrier only if tp==sl; for asym use pnl label externally
    for i in range(p,min(q,len(idx))):
        u=H[i]>=up; d=L[i]<=dn
        if u and d:return 99
        if u:return 1
        if d:return -1
    return 0
# event pool
allE=pd.concat([pd.read_csv(f'/mnt/data/oldp0_events_{y}.csv',parse_dates=['source_m5','decision']) for y in [2024,2025,2026]],ignore_index=True)
rows=[]
for r in allE.itertuples(index=False):
    t=pd.Timestamp(r.decision)
    m30=state_scalar(t,e30,o30); h1=state_scalar(t,e60,o60)
    if m30==0 or h1==0 or m30!=h1: continue
    d=m30
    loc=state_scalar(t,e5,o5)
    # two V3-semantic state machines, mutually defined by local state at P15 decision
    mode='RELOAD_WAIT' if loc!=d else 'FAILED_WAIT'
    target=d if mode=='RELOAD_WAIT' else -d
    conf=None
    # only next 3 completed M5 bars = 15m post-P15 scenario window
    for k in [5,10,15]:
        tt=t+pd.Timedelta(minutes=k)
        # HTF delivery must still be intact at confirmation
        m30k=state_scalar(tt,e30,o30); h1k=state_scalar(tt,e60,o60)
        if not (m30k==d and h1k==d):
            break
        ch=state_scalar(tt,e5,c5)
        if ch==target:
            conf=tt; break
    if conf is None: continue
    origin=close_before(conf)
    # simple symmetric short-distance label
    lab25=first_touch(conf,origin,r.S,.25,.25,15)
    # directional asymmetric outcome flags for predicted target direction; conservative ambiguous=0
    def pred_out(tp,sl,mins):
        p=np.searchsorted(idx,np.datetime64(conf),'left');q=np.searchsorted(idx,np.datetime64(conf+pd.Timedelta(minutes=mins)),'left')
        U=origin+target*tp*r.S; A=origin-target*sl*r.S
        for i in range(p,min(q,len(idx))):
            if target==1: win=H[i]>=U; lose=L[i]<=A
            else: win=L[i]<=U; lose=H[i]>=A
            if win and lose:return 99
            if lose:return -1
            if win:return 1
        return 0
    rows.append(dict(year=r.year,source_m5=r.source_m5,p15_decision=t,confirm=conf,S=r.S,p15=r.p15,htf_dir=d,local_at_p15=loc,scenario=('S_RELOAD_ACCEPT' if mode=='RELOAD_WAIT' else 'S_FAILED_AUCTION_LOCAL_FLIP'),pred=target,origin=origin,lab25=lab25,o50=pred_out(.50,.40,30),o75=pred_out(.75,.40,45)))
out=pd.DataFrame(rows);out.to_csv('/mnt/data/v8_postp15_v3_state_machine_events.csv',index=False)
print('total',len(out))
for sc,g0 in out.groupby('scenario'):
 print('\n',sc)
 for y,g in g0.groupby('year'):
  q=g[np.isin(g.lab25,[-1,1])]; a=(q.lab25==q.pred).mean() if len(q) else np.nan
  for col in ['o50','o75']:
   z=g[g[col].isin([-1,1])]; wr=(z[col]==1).mean() if len(z) else np.nan
   print(y,'N',len(g),'25res',len(q),'w25',round(a,4),'% '+col+' n/wr',len(z),round(wr,4) if len(z) else None,end='; ')
  print()
# Coverage among all P15 events: unique confirmation modules
print('\ncoverage by year')
for y in [2024,2025,2026]:
 n=(allE.year==y).sum(); ny=(out.year==y).sum(); print(y,ny,'/',n,ny/n)
