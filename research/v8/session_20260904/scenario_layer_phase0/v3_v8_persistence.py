import pandas as pd, numpy as np
# load bridge and M1/M5 helper data by importing prior script module functions
import importlib.util
spec=importlib.util.spec_from_file_location('b','/mnt/data/v3_v8_bridge.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
m1=b.load_gold(b.DATA); m5=b.resample_ohlc(m1,'5min');m5['atr14']=b.atr_series(m5)
p=b.pivot_events(m5,2,5); ends,owner,chg,hlev,llev=b.bos_owner_with_break(m5,p,5)
ev=pd.read_csv('/mnt/data/v3_v8_bridge_events.csv',parse_dates=['source_m5','decision'])
rows=[]
for r in ev.itertuples(index=False):
    if int(r.m5_changed)==0: continue
    k=m5.index.get_indexer([r.source_m5])[0]
    if k<0 or k+1>=len(m5): continue
    d=int(r.m5_changed); level=hlev[k] if d>0 else llev[k]
    if not np.isfinite(level): continue
    src_close=float(m5.close.iloc[k]); nxt_close=float(m5.close.iloc[k+1]); confirm=m5.index[k+1]+pd.Timedelta(minutes=5)
    src_margin=d*(src_close-level); nxt_margin=d*(nxt_close-level)
    persist_owner=(owner[k+1]==d)
    persist_close=(nxt_margin>0)
    persist=persist_owner and persist_close
    expand=persist and (nxt_margin>src_margin)
    # quote-free origin = next M5 close (last legal M1 close at confirm)
    origin=nxt_close
    rows.append(dict(year=r.year,source=r.source_m5,confirm=confirm,dir=d,S=r.S,origin=origin,p15=r.p15,
                     delivery=bool(r.delivery_local),src_margin=src_margin,nxt_margin=nxt_margin,
                     persist_owner=persist_owner,persist_close=persist_close,persist=persist,margin_expand=expand))
out=pd.DataFrame(rows);out.to_csv('/mnt/data/v3_v8_persistence_events.csv',index=False)
# outcome descriptive
idx=m1.index
def run(q,fav,adv,h):
    z=[]
    for r in q.itertuples():
        a=idx.searchsorted(r.confirm,'left');e=idx.searchsorted(r.confirm+pd.Timedelta(minutes=h),'left');res=np.nan
        for x in m1.iloc[a:e].itertuples():
            if r.dir>0: win=x.high>=r.origin+fav*r.S; lose=x.low<=r.origin-adv*r.S
            else: win=x.low<=r.origin-fav*r.S; lose=x.high>=r.origin+adv*r.S
            if win and lose:res=0;break
            if lose:res=0;break
            if win:res=1;break
        z.append(res)
    a=np.array(z,float);ok=np.isfinite(a);return ok.sum(),np.nanmean(a) if ok.any() else np.nan
for y,g in out.groupby('year'):
 print('\nYEAR',y,'base',len(g))
 for nm,mask in [('persist',g.persist),('persist_delivery',g.persist & g.delivery),('expand',g.margin_expand),('expand_delivery',g.margin_expand & g.delivery),('fail',~g.persist)]:
   q=g[mask]
   vals=[]
   for spec2 in [(.25,.25,15),(.5,.4,30),(.75,.4,60)]: vals.append(run(q,*spec2))
   print(nm,'N',len(q),vals)
