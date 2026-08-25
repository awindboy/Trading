#!/usr/bin/env python3
"""V3-003C GOLD reload-state × local-acceptance Level-A probe.

Research-only. 2023-2025 discovery data only. Do not use 2022/2021.

Reference family:
  M15 adaptive directional-change source (k=2 ATR)
  -> persistent liquidity until first consumption
  -> atomic same-M1 penetration + close recovery
  -> pre-sweep M5 owner opposite reaction direction
  -> first M5 owner transition back with reaction direction before sweep-extreme invalidation
  -> trigger-close Entry, sweep-extreme SL

Delivery state at sweep:
  M30 mentor-wave recent4/prior4 leg expansion > 1.0
  OR
  M30 and H1 causal BOS-owner states both agree with reaction direction.

Strong local acceptance:
  price accepted beyond the actually broken M5 structure level by more distance
  than the source-liquidity overshoot beyond the swept level.

No production strategy authority is implied.
"""
from __future__ import annotations

import argparse
import heapq
import math
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
try:
    from numba import njit
except Exception:  # pragma: no cover
    def njit(fn):
        return fn

POINT = 0.01


def load_gold(path: Path) -> pd.DataFrame:
    frames=[]
    if path.is_dir():
        names=sorted(path.glob('*.csv'))
        readers=[(p.name, open(p,'rb')) for p in names]
    else:
        z=zipfile.ZipFile(path)
        names=sorted([n for n in z.namelist() if n.lower().endswith('.csv')])
        readers=[(n,z.open(n)) for n in names]
    try:
        for name,fh in readers:
            x=pd.read_csv(fh,sep='\t')
            x.columns=[c.strip('<> ').lower() for c in x.columns]
            ts=pd.to_datetime(x['date'].astype(str)+' '+x['time'].astype(str),errors='raise')
            y=pd.DataFrame(index=ts)
            y.index.name='ts'
            for c in ['open','high','low','close']:
                y[c]=pd.to_numeric(x[c],errors='raise').to_numpy(float)
            y['tickvol']=pd.to_numeric(x.get('tickvol',0),errors='coerce').fillna(0).to_numpy(float)
            y['spread']=pd.to_numeric(x['spread'],errors='raise').to_numpy(float)
            y['spread_px']=y['spread']*POINT
            frames.append(y)
    finally:
        for _,fh in readers:
            try: fh.close()
            except Exception: pass
        if not path.is_dir(): z.close()
    m1=pd.concat(frames).sort_index()
    if m1.index.has_duplicates:
        raise RuntimeError('duplicate M1 timestamps')
    return m1


def resample_ohlc(m1: pd.DataFrame, rule: str) -> pd.DataFrame:
    x=m1.resample(rule,label='left',closed='left').agg(
        open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),
        tickvol=('tickvol','sum'),spread_px=('spread_px','median'))
    return x.dropna(subset=['open','high','low','close'])


def atr_series(df: pd.DataFrame,n: int=14) -> pd.Series:
    prev=df.close.shift(1)
    tr=pd.concat([(df.high-df.low),(df.high-prev).abs(),(df.low-prev).abs()],axis=1).max(axis=1)
    return tr.rolling(n,min_periods=n).mean()


def pivot_events(df: pd.DataFrame,k: int,tfmin: int) -> pd.DataFrame:
    h=df.high.to_numpy(float); l=df.low.to_numpy(float); idx=df.index
    rows=[]
    for i in range(k,len(df)-k):
        if h[i]>np.max(h[i-k:i]) and h[i]>=np.max(h[i+1:i+k+1]):
            rows.append((idx[i+k]+pd.Timedelta(minutes=tfmin),idx[i],'H',h[i]))
        if l[i]<np.min(l[i-k:i]) and l[i]<=np.min(l[i+1:i+k+1]):
            rows.append((idx[i+k]+pd.Timedelta(minutes=tfmin),idx[i],'L',l[i]))
    return pd.DataFrame(rows,columns=['available_at','pivot_at','type','price']).sort_values('available_at').reset_index(drop=True)


def dc_swing_events(df: pd.DataFrame,k: float,tfmin: int) -> pd.DataFrame:
    atr=df.atr14.shift(1).to_numpy(float)
    hi=df.high.to_numpy(float); lo=df.low.to_numpy(float); cl=df.close.to_numpy(float); idx=df.index
    mode=0; high_p=-np.inf; high_i=None; low_p=np.inf; low_i=None; rows=[]
    for i in range(len(df)):
        a=atr[i]
        if not np.isfinite(a) or a<=0: continue
        if mode==0:
            if high_i is None:
                high_p=hi[i];high_i=i;low_p=lo[i];low_i=i;continue
            if hi[i]>high_p: high_p=hi[i];high_i=i
            if lo[i]<low_p: low_p=lo[i];low_i=i
            if high_p-cl[i]>=k*a and high_i<i:
                rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[high_i],'H',high_p));mode=-1;low_p=lo[i];low_i=i
            elif cl[i]-low_p>=k*a and low_i<i:
                rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[low_i],'L',low_p));mode=1;high_p=hi[i];high_i=i
        elif mode==1:
            if hi[i]>high_p: high_p=hi[i];high_i=i
            if high_p-cl[i]>=k*a and high_i<i:
                rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[high_i],'H',high_p));mode=-1;low_p=lo[i];low_i=i
        else:
            if lo[i]<low_p: low_p=lo[i];low_i=i
            if cl[i]-low_p>=k*a and low_i<i:
                rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[low_i],'L',low_p));mode=1;high_p=hi[i];high_i=i
    return pd.DataFrame(rows,columns=['available_at','pivot_at','type','price']).sort_values('available_at').reset_index(drop=True)


def mentor_waves(df: pd.DataFrame,tfmin: int) -> pd.DataFrame:
    col=np.sign(df.close.to_numpy(float)-df.open.to_numpy(float)).astype(int)
    hi=df.high.to_numpy(float);lo=df.low.to_numpy(float);idx=df.index
    rows=[];last_side=0;leg_start=0;recent=[]
    for i,c in enumerate(col):
        recent.append(c)
        if len(recent)>3: recent.pop(0)
        if len(recent)<3 or 0 in recent or not(recent[0]==recent[1]==recent[2]): continue
        side=1 if c==-1 else -1
        if side==last_side: continue
        if side==1:
            off=int(np.argmax(hi[leg_start:i+1])); ex=leg_start+off; typ='H'; price=hi[ex]
        else:
            off=int(np.argmin(lo[leg_start:i+1])); ex=leg_start+off; typ='L'; price=lo[ex]
        rows.append((idx[i]+pd.Timedelta(minutes=tfmin),idx[ex],typ,float(price)))
        last_side=side;leg_start=ex
    return pd.DataFrame(rows,columns=['available_at','pivot_at','type','price'])


def bos_owner_with_break(df: pd.DataFrame,pe: pd.DataFrame,tfmin: int):
    ends=(df.index+pd.Timedelta(minutes=tfmin)).to_numpy(dtype='datetime64[ns]')
    close=df.close.to_numpy(float)
    H=pe[pe.type=='H'].sort_values('available_at');L=pe[pe.type=='L'].sort_values('available_at')
    ht=H.available_at.to_numpy(dtype='datetime64[ns]');hp=H.price.to_numpy(float)
    lt=L.available_at.to_numpy(dtype='datetime64[ns]');lp=L.price.to_numpy(float)
    owner=np.zeros(len(df),dtype=np.int8);changed=np.zeros(len(df),dtype=np.int8)
    hlev=np.full(len(df),np.nan);llev=np.full(len(df),np.nan);cur=0
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
    out=np.zeros(len(pos),dtype=np.int8);ok=pos>=0;out[ok]=vals[pos[ok]]
    return out


def wave_expansion_at(times,waves,n=12,leg_group=4):
    wt=waves.available_at.to_numpy(dtype='datetime64[ns]');pr=waves.price.to_numpy(float)
    out=np.full(len(times),np.nan)
    for j,t in enumerate(np.asarray(times,dtype='datetime64[ns]')):
        pos=np.searchsorted(wt,t,side='right')
        if pos<n:continue
        pp=pr[pos-n:pos]
        recent=np.mean([abs(pp[i]-pp[i-1]) for i in range(n-leg_group,n)])
        prior=np.mean([abs(pp[i]-pp[i-1]) for i in range(n-2*leg_group,n-leg_group)])
        if prior>0:out[j]=recent/prior
    return out


def persistent_reactions(m1: pd.DataFrame,events: pd.DataFrame) -> pd.DataFrame:
    ev=events.sort_values('available_at').reset_index(drop=True)
    et=ev.available_at.to_numpy(dtype='datetime64[ns]');typ=ev.type.to_numpy();pr=ev.price.to_numpy(float);pv=ev.pivot_at.to_numpy(dtype='datetime64[ns]')
    hheap=[];lheap=[];ep=0;rows=[]
    idx=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);cl=m1.close.to_numpy(float)
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


def dedupe_enriched(r: pd.DataFrame,pe: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for (t,d),g in r.groupby(['sweep_time','dir'],sort=True):
        rep=g.loc[g.liq_price.idxmax()] if d==1 else g.loc[g.liq_price.idxmin()]
        src=pe.iloc[int(rep.liq_id)]
        rows.append((t,d,float(rep.liq_price),pd.Timestamp(rep.pivot_at),pd.Timestamp(src.available_at),int(rep.liq_id),len(g)))
    return pd.DataFrame(rows,columns=['sweep_time','dir','liq_price','liq_pivot_at','liq_available_at','liq_id','n_levels'])


def build_triggers(reactions,m1,b5,ends5,own5,chg5):
    mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float)
    rows=[]
    for r in reactions.itertuples(index=False):
        mi=np.searchsorted(mt,np.datetime64(r.sweep_time))
        ext=float(lo[mi] if r.dir==1 else hi[mi])
        bi=np.searchsorted(ends5,np.datetime64(r.sweep_time),side='right');pre=own5[bi-1] if bi>0 else 0
        if pre!=-r.dir:continue
        for k in range(bi,len(b5)):
            bs=b5.index[k];et=bs+pd.Timedelta(minutes=5)
            a=np.searchsorted(mt,np.datetime64(r.sweep_time),side='right') if k==bi else np.searchsorted(mt,np.datetime64(bs),side='left')
            b=np.searchsorted(mt,np.datetime64(et),side='left')
            plo=lo[a:b].min() if a<b else np.inf;phi=hi[a:b].max() if a<b else -np.inf
            if (r.dir==1 and plo<ext) or (r.dir==-1 and phi>ext):break
            if chg5[k]==r.dir:
                rows.append((r.sweep_time,r.dir,r.liq_price,r.liq_pivot_at,r.liq_available_at,r.liq_id,r.n_levels,ext,pd.Timestamp(ends5[k]),float(b5.close.iat[k]),pre,k))
                break
    return pd.DataFrame(rows,columns=['sweep_time','dir','liq_price','liq_pivot_at','liq_available_at','liq_id','n_levels','sweep_extreme','trigger_time','trigger_close','pre_m5_owner','trigger_m5_index'])


@njit
def barrier_eval(starts,dirs,entry,sl,risk,hi,lo,sp):
    n=len(starts);win=np.full(n,-1,np.int8);resolved=np.full(n,-1,np.int64);mfe=np.zeros(n);mae=np.zeros(n)
    for a in range(n):
        tp=entry[a]+dirs[a]*risk[a]
        for i in range(starts[a]+1,len(hi)):
            if dirs[a]==1:
                ht=hi[i]>=tp;hs=lo[i]<=sl[a];fav=(hi[i]-entry[a])/risk[a];adv=(entry[a]-lo[i])/risk[a]
            else:
                ah=hi[i]+sp[i];al=lo[i]+sp[i];ht=al<=tp;hs=ah>=sl[a];fav=(entry[a]-al)/risk[a];adv=(ah-entry[a])/risk[a]
            if fav>mfe[a]:mfe[a]=fav
            if adv>mae[a]:mae[a]=adv
            if ht and hs:win[a]=0;resolved[a]=i;break
            if hs:win[a]=0;resolved[a]=i;break
            if ht:win[a]=1;resolved[a]=i;break
    return win,resolved,mfe,mae


@njit
def costless_eval(starts,dirs,entry,sl,risk,hi,lo):
    n=len(starts);win=np.full(n,-1,np.int8)
    for a in range(n):
        tp=entry[a]+dirs[a]*risk[a]
        for i in range(starts[a]+1,len(hi)):
            if dirs[a]==1:ht=hi[i]>=tp;hs=lo[i]<=sl[a]
            else:ht=lo[i]<=tp;hs=hi[i]>=sl[a]
            if ht and hs:win[a]=0;break
            if hs:win[a]=0;break
            if ht:win[a]=1;break
    return win


def evaluate(tr,m1):
    mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);cl=m1.close.to_numpy(float);sp=m1.spread_px.to_numpy(float)
    starts=np.searchsorted(mt,tr.trigger_time.to_numpy(dtype='datetime64[ns]'),side='left')-1
    entries=[];sls=[];risks=[]
    for r,ip in zip(tr.itertuples(index=False),starts):
        if r.dir==1:en=cl[ip]+sp[ip];sl=r.sweep_extreme
        else:en=cl[ip];sl=r.sweep_extreme+sp[ip]
        entries.append(en);sls.append(sl);risks.append(abs(en-sl))
    x=tr.copy();x['entry']=entries;x['sl_exec']=sls;x['risk']=risks
    good=x.risk>0;x=x[good].reset_index(drop=True);starts=starts[good.to_numpy()]
    w,ri,mfe,mae=barrier_eval(starts,x.dir.to_numpy(np.int8),x.entry.to_numpy(float),x.sl_exec.to_numpy(float),x.risk.to_numpy(float),hi,lo,sp)
    x['win1']=w;x['resolved_i']=ri;x['resolved_at']=pd.to_datetime(np.where(ri>=0,mt[np.maximum(ri,0)],np.datetime64('NaT')));x['mfe_r']=mfe;x['mae_r']=mae
    # exact no-spread counterfactual uses trigger chart close and sweep extreme.
    en0=x.trigger_close.to_numpy(float);sl0=x.sweep_extreme.to_numpy(float);r0=np.abs(en0-sl0)
    x['win1_costless']=costless_eval(starts,x.dir.to_numpy(np.int8),en0,sl0,r0,hi,lo)
    return x


def mirror_eval(df,m1):
    mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);cl=m1.close.to_numpy(float);sp=m1.spread_px.to_numpy(float)
    out=[]
    for r in df.itertuples(index=False):
        d=-r.dir;ip=np.searchsorted(mt,np.datetime64(r.trigger_time),side='left')-1;risk=r.risk
        if d==1:en=cl[ip]+sp[ip];sl=en-risk;tp=en+risk
        else:en=cl[ip];sl=en+risk;tp=en-risk
        z=0
        for i in range(ip+1,len(hi)):
            if d==1:ht=hi[i]>=tp;hs=lo[i]<=sl
            else:ah=hi[i]+sp[i];al=lo[i]+sp[i];ht=al<=tp;hs=ah>=sl
            if ht and hs:z=0;break
            if hs:z=0;break
            if ht:z=1;break
        out.append(z)
    return np.asarray(out,dtype=np.int8)


def first_delivery_loss(trigger,d,t30,up,dn,active):
    if not active:return pd.Timestamp(trigger)
    vals=up if d==1 else dn;pos=np.searchsorted(t30,np.datetime64(trigger),side='right');ix=np.flatnonzero(~vals[pos:])
    return pd.Timestamp(t30[pos+ix[0]]) if len(ix) else pd.NaT


def first_local_opp(trigger,d,ends5,own5):
    pos=np.searchsorted(ends5,np.datetime64(trigger),side='right');ix=np.flatnonzero(own5[pos:]==-d)
    return pd.Timestamp(ends5[pos+ix[0]]) if len(ix) else pd.NaT


def first_tp_after(start,d,tp,m1):
    mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);sp=m1.spread_px.to_numpy(float)
    p=np.searchsorted(mt,np.datetime64(start),side='right')
    if d==1:ix=np.flatnonzero(hi[p:]>=tp)
    else:ix=np.flatnonzero(lo[p:]+sp[p:]<=tp)
    return pd.Timestamp(mt[p+ix[0]]) if len(ix) else pd.NaT


def main():
    ap=argparse.ArgumentParser();ap.add_argument('data',type=Path);ap.add_argument('--sensitivity',action='store_true');args=ap.parse_args()
    m1=load_gold(args.data)
    print('DATA',len(m1),m1.index.min(),m1.index.max())
    bars={r:resample_ohlc(m1,r) for r in ['5min','15min','30min','60min']}
    for b in bars.values():b['atr14']=atr_series(b)

    piv={r:pivot_events(bars[r],2,{'5min':5,'15min':15,'30min':30,'60min':60}[r]) for r in bars}
    ends5,own5,chg5,hlev5,llev5=bos_owner_with_break(bars['5min'],piv['5min'],5)
    ends30,own30,_,_,_=bos_owner_with_break(bars['30min'],piv['30min'],30)
    ends60,own60,_,_,_=bos_owner_with_break(bars['60min'],piv['60min'],60)
    mw30=mentor_waves(bars['30min'],30)

    # Main reference source: M15 DC k=2.0. Natural-scale sensitivity printed below.
    source=dc_swing_events(bars['15min'],2.0,15)
    rr=dedupe_enriched(persistent_reactions(m1,source),source)
    tr=build_triggers(rr,m1,bars['5min'],ends5,own5,chg5)
    ev=evaluate(tr,m1)
    ev['year']=ev.trigger_time.dt.year
    ev['m30_exp']=wave_expansion_at(ev.sweep_time,mw30)
    ev['m30_owner']=state_at(ev.sweep_time,ends30,own30);ev['h1_owner']=state_at(ev.sweep_time,ends60,own60)
    ev['owner_agree']=(ev.m30_owner==ev.dir)&(ev.h1_owner==ev.dir)
    ev['delivery_state']=(ev.m30_exp>1.0)|ev.owner_agree
    # Broken level is the exact M5 level held by the owner detector on the trigger bar.
    ev['broken_m5_level']=np.where(ev.dir.to_numpy()==1,hlev5[ev.trigger_m5_index.to_numpy(int)],llev5[ev.trigger_m5_index.to_numpy(int)])
    ev['penetration']=(ev.liq_price-ev.sweep_extreme)*ev.dir
    ev['acceptance_margin']=(ev.trigger_close-ev.broken_m5_level)*ev.dir
    ev['strong_acceptance']=ev.acceptance_margin>ev.penetration
    ev['mirror_win1']=mirror_eval(ev,m1)

    print('\nBASE')
    print(ev.groupby('year').win1.agg(['count','mean']).to_string())
    print('\n2x2 DELIVERY_STATE x STRONG_ACCEPTANCE')
    print(ev.groupby(['year','delivery_state','strong_acceptance'])[['win1','mirror_win1']].agg(['count','mean']).to_string())
    cand=ev[ev.delivery_state&ev.strong_acceptance].copy()
    print('\nREFERENCE CANDIDATE')
    print(cand.groupby('year')[['win1','win1_costless','mirror_win1']].agg(['count','mean']).to_string())
    print('\nDIRECTION')
    print(cand.groupby(['year','dir']).win1.agg(['count','mean']).to_string())
    cand['quarter']=cand.trigger_time.dt.to_period('Q').astype(str)
    print('\nQUARTER (DESCRIPTIVE ONLY; NO QUARTER GATES)')
    print(cand.groupby('quarter').win1.agg(['count','mean']).to_string())

    # Dynamic delivery-state lifecycle on M30 completed-bar grid.
    t30=ends30;exp_grid=wave_expansion_at(pd.to_datetime(t30),mw30);h1_on30=state_at(pd.to_datetime(t30),ends60,own60)
    up=(exp_grid>1.0)|((own30==1)&(h1_on30==1));dn=(exp_grid>1.0)|((own30==-1)&(h1_on30==-1))
    def delivery_at(times,dirs):
        out=np.zeros(len(times),dtype=bool)
        for i,(t,d) in enumerate(zip(np.asarray(times,dtype='datetime64[ns]'),dirs)):
            pos=np.searchsorted(t30,t,side='right')-1
            if pos>=0:out[i]=(up if d==1 else dn)[pos]
        return out
    cand['delivery_at_trigger']=delivery_at(cand.trigger_time,cand.dir)
    cand['delivery_at_resolution']=delivery_at(cand.resolved_at,cand.dir)
    cand['local_invalidated_at']=[first_local_opp(t,d,ends5,own5) for t,d in zip(cand.trigger_time,cand.dir)]
    cand['delivery_lost_at']=[first_delivery_loss(t,d,t30,up,dn,a) for t,d,a in zip(cand.trigger_time,cand.dir,cand.delivery_at_trigger)]
    cand['local_pre_resolution']=cand.local_invalidated_at.notna()&(cand.local_invalidated_at<=cand.resolved_at)
    cand['delivery_pre_resolution']=cand.delivery_lost_at.notna()&(cand.delivery_lost_at<=cand.resolved_at)
    losers=cand[cand.win1==0].copy()
    cls=[]
    for r in losers.itertuples(index=False):
        if not r.delivery_at_trigger:c='STATE_STALE_AT_TRIGGER'
        else:
            dl=pd.notna(r.delivery_lost_at) and r.delivery_lost_at<=r.resolved_at
            li=pd.notna(r.local_invalidated_at) and r.local_invalidated_at<=r.resolved_at
            if dl:c='LOCAL_FAIL_THEN_STATE_LOSS_PRE_SL' if li and r.local_invalidated_at<r.delivery_lost_at else 'STATE_LOSS_PRE_SL'
            elif li:c='LOCAL_TRIGGER_FAIL_STATE_ALIVE_AT_SL'
            else:c='SL_WITH_LOCAL_AND_STATE_ALIVE'
        cls.append(c)
    losers['failure_class']=cls
    print('\nLOSER LIFECYCLE TAXONOMY')
    print(losers.groupby(['year','failure_class']).size().to_string())

    # Post-SL: original +1R recovery before dynamic delivery-state loss, for taxonomy only.
    rec=[];term=[]
    for r in losers.itertuples(index=False):
        tp=r.entry+r.dir*r.risk
        rr=first_tp_after(r.resolved_at,r.dir,tp,m1)
        dl=first_delivery_loss(r.resolved_at,r.dir,t30,up,dn,bool(r.delivery_at_resolution))
        rec.append(rr)
        term.append('RECOVER_1R_BEFORE_STATE_LOSS' if pd.notna(rr) and (pd.isna(dl) or rr<dl) else 'STATE_LOSS_BEFORE_1R_RECOVERY')
    losers['post_sl_recovery_at']=rec;losers['post_sl_terminal']=term
    print('\nPOST-SL TAXONOMY')
    print(losers.groupby(['year','post_sl_terminal']).size().to_string())

    if args.sensitivity:
        print('\nSOURCE-SCALE SENSITIVITY (same state + acceptance semantics)')
        rows=[]
        for tf,mins in [('15min',15),('30min',30)]:
            for k in ([1.5,2.0,2.5] if tf=='15min' else [1.5,2.0]):
                src=dc_swing_events(bars[tf],k,mins);q=dedupe_enriched(persistent_reactions(m1,src),src)
                z=evaluate(build_triggers(q,m1,bars['5min'],ends5,own5,chg5),m1);z['year']=z.trigger_time.dt.year
                z['m30_exp']=wave_expansion_at(z.sweep_time,mw30);z['m30_owner']=state_at(z.sweep_time,ends30,own30);z['h1_owner']=state_at(z.sweep_time,ends60,own60)
                z['delivery_state']=(z.m30_exp>1.0)|((z.m30_owner==z.dir)&(z.h1_owner==z.dir))
                z['broken']=np.where(z.dir.to_numpy()==1,hlev5[z.trigger_m5_index.to_numpy(int)],llev5[z.trigger_m5_index.to_numpy(int)])
                z['strong']=((z.trigger_close-z.broken)*z.dir)>((z.liq_price-z.sweep_extreme)*z.dir)
                for y in [2023,2024,2025]:
                    g=z[(z.year==y)&z.delivery_state&z.strong]
                    rows.append((tf,k,y,len(g),g.win1.mean() if len(g) else np.nan))
        print(pd.DataFrame(rows,columns=['source_tf','k','year','n','wr']).to_string(index=False))
    else:
        print('\nSOURCE-SCALE SENSITIVITY: skipped (pass --sensitivity for the slower robustness sweep)')


if __name__=='__main__':
    main()
