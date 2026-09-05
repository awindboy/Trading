import pandas as pd, numpy as np
P='/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv'
x=pd.read_csv(P,sep='\t');x.columns=[c.strip('<> ').lower() for c in x.columns]
ts=pd.to_datetime(x.date.astype(str)+' '+x.time.astype(str),format='%Y.%m.%d %H:%M:%S');m=pd.DataFrame({'high':x.high.values,'low':x.low.values},index=ts)
e=pd.read_csv('/mnt/data/v3_v8_bridge_events.csv',parse_dates=['decision'])

def test(g,fav,adv,h):
    out=[]
    for r in g.itertuples():
        d=int(r.m5_changed); o=float(r.origin_close); S=float(r.S); st=r.decision
        a=m.index.searchsorted(st,'left');b=m.index.searchsorted(st+pd.Timedelta(minutes=h),'left')
        res=np.nan
        for z in m.iloc[a:b].itertuples():
            if d>0: win=z.high>=o+fav*S; lose=z.low<=o-adv*S
            else: win=z.low<=o-fav*S; lose=z.high>=o+adv*S
            if win and lose:res=0;break
            if lose:res=0;break
            if win:res=1;break
        out.append(res)
    a=np.array(out,float); q=np.isfinite(a)
    return int(q.sum()), float(np.nanmean(a)) if q.any() else np.nan, int(np.nansum(a)), len(a)-int(q.sum())

rows=[]
for y in [2024,2025,2026]:
    gy=e[(e.year==y)&(e.m5_changed!=0)]
    for label,mask in [('M5_CHANGE',np.ones(len(gy),bool)),('M5_CHANGE_DELIVERY',gy.delivery_local==True),('M5_CHANGE_NO_DELIVERY',gy.delivery_local!=True)]:
        q=gy[mask]
        for fav,adv,h in [(.25,.25,15),(.5,.4,30),(.75,.4,60),(1.0,.4,60),(1.5,.5,90)]:
            n,wr,w,c=test(q,fav,adv,h)
            rows.append((y,label,len(q),fav,adv,h,n,wr,w,c))
r=pd.DataFrame(rows,columns=['year','scenario','events','favS','advS','horizon','completed','wr','wins','unresolved'])
r.to_csv('/mnt/data/v3_v8_m1_ladder.csv',index=False)
print(r.to_string(index=False))
