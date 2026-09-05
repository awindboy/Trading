from __future__ import annotations
import heapq, math
import numpy as np, pandas as pd
from pathlib import Path

POINT=0.01
DATA=Path('/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv')
OUT=Path('/mnt/data')

def load_gold(path):
    x=pd.read_csv(path,sep='\t')
    x.columns=[c.strip('<> ').lower() for c in x.columns]
    ts=pd.to_datetime(x['date'].astype(str)+' '+x['time'].astype(str),format='%Y.%m.%d %H:%M:%S')
    y=pd.DataFrame(index=ts); y.index.name='ts'
    for c in ['open','high','low','close']: y[c]=pd.to_numeric(x[c],errors='raise').to_numpy(float)
    y['tickvol']=pd.to_numeric(x['tickvol'],errors='coerce').fillna(0).to_numpy(float)
    y['spread']=pd.to_numeric(x['spread'],errors='raise').to_numpy(float)
    y['spread_px']=y['spread']*POINT
    return y

def resample_ohlc(m1,rule):
    x=m1.resample(rule,label='left',closed='left').agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),tickvol=('tickvol','sum'),spread_px=('spread_px','median'))
    return x.dropna(subset=['open','high','low','close'])

def atr_series(df,n=14):
    prev=df.close.shift(1)
    tr=pd.concat([(df.high-df.low),(df.high-prev).abs(),(df.low-prev).abs()],axis=1).max(axis=1)
    return tr.rolling(n,min_periods=n).mean()

def pivot_events(df,k,tfmin):
    h=df.high.to_numpy(float); l=df.low.to_numpy(float); idx=df.index; rows=[]
    for i in range(k,len(df)-k):
        if h[i]>np.max(h[i-k:i]) and h[i]>=np.max(h[i+1:i+k+1]): rows.append((idx[i+k]+pd.Timedelta(minutes=tfmin),idx[i],'H',h[i]))
        if l[i]<np.min(l[i-k:i]) and l[i]<=np.min(l[i+1:i+k+1]): rows.append((idx[i+k]+pd.Timedelta(minutes=tfmin),idx[i],'L',l[i]))
    return pd.DataFrame(rows,columns=['available_at','pivot_at','type','price']).sort_values('available_at').reset_index(drop=True)

def dc_swing_events(df,k,tfmin):
    atr=df.atr14.shift(1).to_numpy(float); hi=df.high.to_numpy(float); lo=df.low.to_numpy(float); cl=df.close.to_numpy(float); idx=df.index
    mode=0; high_p=-np.inf;high_i=None;low_p=np.inf;low_i=None;rows=[]
    for i in range(len(df)):
        a=atr[i]
        if not np.isfinite(a) or a<=0: continue
        if mode==0:
            if high_i is None: high_p=hi[i];high_i=i;low_p=lo[i];low_i=i;continue
            if hi[i]>high_p:high_p=hi[i];high_i=i
            if lo[i]<low_p:low_p=lo[i];low_i=i
            if high_p-cl[i]>=k*a and high_i<i:
                rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[high_i],'H',high_p));mode=-1;low_p=lo[i];low_i=i
            elif cl[i]-low_p>=k*a and low_i<i:
                rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[low_i],'L',low_p));mode=1;high_p=hi[i];high_i=i
        elif mode==1:
            if hi[i]>high_p:high_p=hi[i];high_i=i
            if high_p-cl[i]>=k*a and high_i<i:
                rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[high_i],'H',high_p));mode=-1;low_p=lo[i];low_i=i
        else:
            if lo[i]<low_p:low_p=lo[i];low_i=i
            if cl[i]-low_p>=k*a and low_i<i:
                rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[low_i],'L',low_p));mode=1;high_p=hi[i];high_i=i
    return pd.DataFrame(rows,columns=['available_at','pivot_at','type','price']).sort_values('available_at').reset_index(drop=True)

def mentor_waves(df,tfmin):
    col=np.sign(df.close.to_numpy(float)-df.open.to_numpy(float)).astype(int); hi=df.high.to_numpy(float);lo=df.low.to_numpy(float);idx=df.index
    rows=[];last_side=0;leg_start=0;recent=[]
    for i,c in enumerate(col):
        recent.append(c)
        if len(recent)>3:recent.pop(0)
        if len(recent)<3 or 0 in recent or not(recent[0]==recent[1]==recent[2]):continue
        side=1 if c==-1 else -1
        if side==last_side:continue
        if side==1:
            ex=leg_start+int(np.argmax(hi[leg_start:i+1]));typ='H';price=hi[ex]
        else:
            ex=leg_start+int(np.argmin(lo[leg_start:i+1]));typ='L';price=lo[ex]
        rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[ex],typ,float(price)));last_side=side;leg_start=ex
    return pd.DataFrame(rows,columns=['available_at','pivot_at','type','price'])

def bos_owner_with_break(df,pe,tfmin):
    ends=(df.index+pd.Timedelta(minutes=tfmin)).to_numpy(dtype='datetime64[ns]');close=df.close.to_numpy(float)
    H=pe[pe.type=='H'].sort_values('available_at');L=pe[pe.type=='L'].sort_values('available_at')
    ht=H.available_at.to_numpy(dtype='datetime64[ns]');hp=H.price.to_numpy(float);lt=L.available_at.to_numpy(dtype='datetime64[ns]');lp=L.price.to_numpy(float)
    owner=np.zeros(len(df),dtype=np.int8);changed=np.zeros(len(df),dtype=np.int8);hlev=np.full(len(df),np.nan);llev=np.full(len(df),np.nan);cur=0
    for i,t in enumerate(ends):
        ih=np.searchsorted(ht,t,side='right')-1;il=np.searchsorted(lt,t,side='right')-1
        if ih>=0:hlev[i]=hp[ih]
        if il>=0:llev[i]=lp[il]
        new=cur
        if ih>=0 and close[i]>hp[ih]:new=1
        if il>=0 and close[i]<lp[il]:new=-1
        if new!=cur:changed[i]=new;cur=new
        owner[i]=cur
    return ends,owner,changed,hlev,llev

def state_at(times,ends,vals):
    pos=np.searchsorted(ends,np.asarray(times,dtype='datetime64[ns]'),side='right')-1
    out=np.zeros(len(pos),dtype=vals.dtype);ok=pos>=0;out[ok]=vals[pos[ok]]
    return out

def wave_expansion_at(times,waves,n=12,leg_group=4):
    wt=waves.available_at.to_numpy(dtype='datetime64[ns]');pr=waves.price.to_numpy(float);out=np.full(len(times),np.nan)
    for j,t in enumerate(np.asarray(times,dtype='datetime64[ns]')):
        pos=np.searchsorted(wt,t,side='right')
        if pos<n:continue
        pp=pr[pos-n:pos]
        recent=np.mean([abs(pp[i]-pp[i-1]) for i in range(n-leg_group,n)])
        prior=np.mean([abs(pp[i]-pp[i-1]) for i in range(n-2*leg_group,n-leg_group)])
        if prior>0:out[j]=recent/prior
    return out

def persistent_reactions(m1,events):
    ev=events.sort_values('available_at').reset_index(drop=True);et=ev.available_at.to_numpy(dtype='datetime64[ns]');typ=ev.type.to_numpy();pr=ev.price.to_numpy(float);pv=ev.pivot_at.to_numpy(dtype='datetime64[ns]')
    hheap=[];lheap=[];ep=0;rows=[];idx=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);cl=m1.close.to_numpy(float)
    for i,t in enumerate(idx):
        while ep<len(ev) and et[ep]<=t:
            if typ[ep]=='H':heapq.heappush(hheap,(pr[ep],ep))
            else:heapq.heappush(lheap,(-pr[ep],ep))
            ep+=1
        while hheap and hheap[0][0]<hi[i]:
            p,eid=heapq.heappop(hheap)
            if cl[i]<p:rows.append((pd.Timestamp(t),-1,p,pd.Timestamp(pv[eid]),eid))
        while lheap and -lheap[0][0]>lo[i]:
            np_,eid=heapq.heappop(lheap);p=-np_
            if cl[i]>p:rows.append((pd.Timestamp(t),1,p,pd.Timestamp(pv[eid]),eid))
    return pd.DataFrame(rows,columns=['sweep_time','dir','liq_price','pivot_at','liq_id'])

def dedupe_enriched(r,pe):
    rows=[]
    for (t,d),g in r.groupby(['sweep_time','dir'],sort=True):
        rep=g.loc[g.liq_price.idxmax()] if d==1 else g.loc[g.liq_price.idxmin()];src=pe.iloc[int(rep.liq_id)]
        rows.append((t,d,float(rep.liq_price),pd.Timestamp(rep.pivot_at),pd.Timestamp(src.available_at),int(rep.liq_id),len(g)))
    return pd.DataFrame(rows,columns=['sweep_time','dir','liq_price','liq_pivot_at','liq_available_at','liq_id','n_levels'])

def build_triggers(reactions,m1,b5,ends5,own5,chg5):
    mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);rows=[]
    for r in reactions.itertuples(index=False):
        mi=np.searchsorted(mt,np.datetime64(r.sweep_time));ext=float(lo[mi] if r.dir==1 else hi[mi])
        bi=np.searchsorted(ends5,np.datetime64(r.sweep_time),side='right');pre=own5[bi-1] if bi>0 else 0
        if pre!=-r.dir:continue
        for k in range(bi,len(b5)):
            bs=b5.index[k];et=bs+pd.Timedelta(minutes=5)
            a=np.searchsorted(mt,np.datetime64(r.sweep_time),side='right') if k==bi else np.searchsorted(mt,np.datetime64(bs),side='left'); b=np.searchsorted(mt,np.datetime64(et),side='left')
            plo=lo[a:b].min() if a<b else np.inf;phi=hi[a:b].max() if a<b else -np.inf
            if (r.dir==1 and plo<ext) or (r.dir==-1 and phi>ext):break
            if chg5[k]==r.dir:
                rows.append((r.sweep_time,r.dir,r.liq_price,r.liq_pivot_at,r.liq_available_at,r.liq_id,r.n_levels,ext,pd.Timestamp(ends5[k]),float(b5.close.iat[k]),pre,k));break
    return pd.DataFrame(rows,columns=['sweep_time','dir','liq_price','liq_pivot_at','liq_available_at','liq_id','n_levels','sweep_extreme','trigger_time','trigger_close','pre_m5_owner','trigger_m5_index'])

def first_touch(m1, start, origin, S, d, fav, adv, horizon_min):
    # chart-side descriptive, no execution spread. direction d: +1 long/-1 short
    idx=m1.index; a=idx.searchsorted(pd.Timestamp(start),side='left'); b=idx.searchsorted(pd.Timestamp(start)+pd.Timedelta(minutes=horizon_min),side='left')
    g=m1.iloc[a:b]
    if len(g)==0:return np.nan,np.nan
    up=origin+d*fav*S; dn=origin-d*adv*S
    # for d=+1 favorable uses high >= up, adverse low <= dn; reversed for d=-1
    for j,r in g.iterrows():
        if d==1:
            hf=r.high>=up; ha=r.low<=dn
        else:
            hf=r.low<=up; ha=r.high>=dn
        if hf and ha:return 0.0,(j-pd.Timestamp(start)).total_seconds()/60 # ambiguous pessimistic
        if ha:return 0.0,(j-pd.Timestamp(start)).total_seconds()/60
        if hf:return 1.0,(j-pd.Timestamp(start)).total_seconds()/60
    return np.nan,np.nan

def main():
    print('load')
    m1=load_gold(DATA)
    # research range 2024-2026 only for bridge execution, retain earlier bars for causal warmup
    bars={r:resample_ohlc(m1,r) for r in ['5min','15min','30min','60min']}
    for b in bars.values():b['atr14']=atr_series(b)
    piv={r:pivot_events(bars[r],2,{'5min':5,'15min':15,'30min':30,'60min':60}[r]) for r in bars}
    ends5,own5,chg5,hlev5,llev5=bos_owner_with_break(bars['5min'],piv['5min'],5)
    ends30,own30,chg30,_,_=bos_owner_with_break(bars['30min'],piv['30min'],30)
    ends60,own60,chg60,_,_=bos_owner_with_break(bars['60min'],piv['60min'],60)
    mw30=mentor_waves(bars['30min'],30)
    print('source/reactions')
    src=dc_swing_events(bars['15min'],2.0,15)
    rr=dedupe_enriched(persistent_reactions(m1,src),src)
    tr=build_triggers(rr,m1,bars['5min'],ends5,own5,chg5)
    tr['m30_exp']=wave_expansion_at(tr.sweep_time,mw30)
    tr['m30_owner']=state_at(tr.sweep_time,ends30,own30);tr['h1_owner']=state_at(tr.sweep_time,ends60,own60)
    tr['delivery_state']=(tr.m30_exp>1.0)|((tr.m30_owner==tr.dir)&(tr.h1_owner==tr.dir))
    ii=tr.trigger_m5_index.to_numpy(int)
    tr['broken_m5_level']=np.where(tr.dir.to_numpy()==1,hlev5[ii],llev5[ii])
    tr['penetration']=(tr.liq_price-tr.sweep_extreme)*tr.dir
    tr['acceptance_margin']=(tr.trigger_close-tr.broken_m5_level)*tr.dir
    tr['strong_acceptance']=tr.acceptance_margin>tr.penetration
    tr['strict_A']=tr.delivery_state & tr.strong_acceptance
    tr=tr[(tr.trigger_time>=pd.Timestamp('2024-01-01')) & (tr.trigger_time<pd.Timestamp('2026-09-01'))].copy()
    tr.to_csv(OUT/'v3_bridge_triggers.csv',index=False)
    print('triggers',len(tr),'strict',int(tr.strict_A.sum()),tr.groupby(tr.trigger_time.dt.year).size().to_dict())

    ev=pd.concat([pd.read_csv(OUT/f'oldp0_events_{y}.csv') for y in [2024,2025,2026]],ignore_index=True)
    for c in ['source_m5','decision']:ev[c]=pd.to_datetime(ev[c])
    # attach V3 current state at P15 decision
    ev['m30_exp']=wave_expansion_at(ev.decision,mw30)
    ev['m30_owner']=state_at(ev.decision,ends30,own30);ev['h1_owner']=state_at(ev.decision,ends60,own60)
    ev['m5_owner']=state_at(ev.decision,ends5,own5);ev['m5_changed']=state_at(ev.decision,ends5,chg5)
    # event-body dir
    b5=bars['5min']; pos=b5.index.get_indexer(ev.source_m5)
    ev['body_dir']=np.sign(b5.close.to_numpy()[pos]-b5.open.to_numpy()[pos]).astype(int)
    # local candidate direction: source-bar M5 owner change if any, else current owner
    ev['local_dir']=np.where(ev.m5_changed!=0,ev.m5_changed,ev.m5_owner).astype(int)
    ev['delivery_local']=(ev.m30_exp>1.0)|((ev.m30_owner==ev.local_dir)&(ev.h1_owner==ev.local_dir))
    # find nearest prior/next trigger and scenario flags
    tt=tr.trigger_time.to_numpy(dtype='datetime64[ns]')
    for i,r in ev.iterrows():
        t=np.datetime64(r.decision)
        p=np.searchsorted(tt,t,side='right')-1
        n=p+1
        if p>=0:
            pr=tr.iloc[p]; age=(r.decision-pr.trigger_time).total_seconds()/60
            if age<=60:
                for c in ['dir','delivery_state','strong_acceptance','strict_A','trigger_time','sweep_time']:
                    ev.at[i,'prior_'+c]=pr[c]
                ev.at[i,'prior_age_min']=age
        if n<len(tr):
            nr=tr.iloc[n]; lead=(nr.trigger_time-r.decision).total_seconds()/60
            if lead<=30:
                for c in ['dir','delivery_state','strong_acceptance','strict_A','trigger_time','sweep_time']:
                    ev.at[i,'next_'+c]=nr[c]
                ev.at[i,'next_lead_min']=lead
    # descriptive first-touch from P15 decision for selected directions
    outs=[]
    for r in ev.itertuples(index=False):
        d=int(r.local_dir) if int(r.local_dir)!=0 else int(r.body_dir or 1)
        w25,t25=first_touch(m1,r.decision,r.origin_close,r.S,d,.25,.25,15)
        w50,t50=first_touch(m1,r.decision,r.origin_close,r.S,d,.50,.40,30)
        outs.append((w25,t25,w50,t50))
    a=np.array(outs,float);ev[['local_win25','local_t25','local_win50_40','local_t50_40']]=a
    ev.to_csv(OUT/'v3_v8_bridge_events.csv',index=False)

if __name__=='__main__':main()
