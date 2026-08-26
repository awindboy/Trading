#!/usr/bin/env python3
"""V3-003D correction-completion / acceptance-persistence research.

Research-only. Discovery input must contain only GOLD# 2023-2025 M1 data.
Candidate A is imported unchanged from v3_003c_reload_state_acceptance_probe.py.
This script does NOT modify Candidate A. It compares separate follow-up variants.
"""
from __future__ import annotations
import argparse, importlib.util, math
from pathlib import Path
import numpy as np
import pandas as pd
try:
    from numba import njit
except Exception:
    def njit(fn): return fn


def load_c_module():
    p=Path(__file__).with_name('v3_003c_reload_state_acceptance_probe.py')
    if not p.exists():
        raise SystemExit(f'FAIL-CLOSED: missing Candidate A module: {p}')
    spec=importlib.util.spec_from_file_location('v3c',p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def build_m1_owner(m1):
    idx=m1.index.to_numpy(dtype='datetime64[ns]');h=m1.high.to_numpy(float);l=m1.low.to_numpy(float);cl=m1.close.to_numpy(float);n=len(m1)
    ctr=np.arange(2,n-2)
    hm=(h[ctr]>h[ctr-2])&(h[ctr]>h[ctr-1])&(h[ctr]>=h[ctr+1])&(h[ctr]>=h[ctr+2])
    lm=(l[ctr]<l[ctr-2])&(l[ctr]<l[ctr-1])&(l[ctr]<=l[ctr+1])&(l[ctr]<=l[ctr+2])
    hi=ctr[hm];li=ctr[lm]
    hav=idx[hi+2]+np.timedelta64(1,'m');lav=idx[li+2]+np.timedelta64(1,'m')
    hp=h[hi];lp=l[li];ends=idx+np.timedelta64(1,'m')
    ih=np.searchsorted(hav,ends,side='right')-1;il=np.searchsorted(lav,ends,side='right')-1
    hl=np.full(n,np.nan);ll=np.full(n,np.nan);ok=ih>=0;hl[ok]=hp[ih[ok]];ok=il>=0;ll[ok]=lp[il[ok]]
    @njit
    def ownbuild(close,hh,ll_):
        own=np.zeros(len(close),np.int8);chg=np.zeros(len(close),np.int8);cur=0
        for i in range(len(close)):
            new=cur
            if not np.isnan(hh[i]) and close[i]>hh[i]:new=1
            if not np.isnan(ll_[i]) and close[i]<ll_[i]:new=-1
            if new!=cur:chg[i]=new;cur=new
            own[i]=cur
        return own,chg
    own,chg=ownbuild(cl,hl,ll)
    return ends,own,chg


def add_micro_path(z,ends1,own1,chg1):
    clean=[];direct=[];counts=[]
    for r in z.itertuples(index=False):
        a=np.searchsorted(ends1,np.datetime64(r.sweep_time),side='right')
        b=np.searchsorted(ends1,np.datetime64(r.trigger_time),side='right')
        changes=chg1[a:b];ids=np.flatnonzero(changes!=0);ai=np.flatnonzero(changes==r.dir)
        pos=np.searchsorted(ends1,np.datetime64(r.trigger_time),side='right')-1
        agr=pos>=0 and own1[pos]==r.dir
        flip=bool(len(ai) and np.any(changes[ai[0]+1:]==-r.dir))
        clean.append(bool(agr and not flip));counts.append(len(ids))
        spos=np.searchsorted(ends1,np.datetime64(r.sweep_time),side='right')-1
        sow=own1[spos] if spos>=0 else 0
        direct.append(bool(sow==-r.dir and len(ids)==1 and changes[ids[0]]==r.dir))
    q=z.copy();q['m1_clean_path']=clean;q['m1_direct_transfer']=direct;q['m1_change_count']=counts
    return q


def build_reference(c,m1):
    bars={r:c.resample_ohlc(m1,r) for r in ['5min','15min','30min','60min']}
    for b in bars.values():b['atr14']=c.atr_series(b)
    piv={r:c.pivot_events(bars[r],2,{'5min':5,'15min':15,'30min':30,'60min':60}[r]) for r in bars}
    ends5,own5,chg5,hlev5,llev5=c.bos_owner_with_break(bars['5min'],piv['5min'],5)
    ends30,own30,_,_,_=c.bos_owner_with_break(bars['30min'],piv['30min'],30)
    ends60,own60,_,_,_=c.bos_owner_with_break(bars['60min'],piv['60min'],60)
    mw30=c.mentor_waves(bars['30min'],30)
    source=c.dc_swing_events(bars['15min'],2.0,15)
    rr=c.dedupe_enriched(c.persistent_reactions(m1,source),source)
    tr=c.build_triggers(rr,m1,bars['5min'],ends5,own5,chg5)
    ev=c.evaluate(tr,m1);ev['year']=ev.trigger_time.dt.year
    ev['m30_exp']=c.wave_expansion_at(ev.sweep_time,mw30)
    ev['m30_owner']=c.state_at(ev.sweep_time,ends30,own30);ev['h1_owner']=c.state_at(ev.sweep_time,ends60,own60)
    ev['delivery_state']=(ev.m30_exp>1.0)|((ev.m30_owner==ev.dir)&(ev.h1_owner==ev.dir))
    ev['broken_m5_level']=np.where(ev.dir.to_numpy()==1,hlev5[ev.trigger_m5_index.to_numpy(int)],llev5[ev.trigger_m5_index.to_numpy(int)])
    ev['penetration']=(ev.liq_price-ev.sweep_extreme)*ev.dir
    ev['acceptance_margin']=(ev.trigger_close-ev.broken_m5_level)*ev.dir
    ev['strong_acceptance']=ev.acceptance_margin>ev.penetration
    ev['mirror_win1']=c.mirror_eval(ev,m1)
    cand=ev[ev.delivery_state&ev.strong_acceptance].copy().reset_index(drop=True)
    return bars,piv,ends5,own5,chg5,cand,ev


def delayed_eval(events,entry_indices,b5,ends5,m1):
    mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);cl=m1.close.to_numpy(float);sp=m1.spread_px.to_numpy(float)
    rows=[]
    for j,(r,k) in enumerate(zip(events.itertuples(index=False),entry_indices)):
        if k is None or k<0 or k>=len(b5):continue
        t=pd.Timestamp(ends5[k]);ip=np.searchsorted(mt,np.datetime64(t),side='left')-1
        en=cl[ip]+sp[ip] if r.dir==1 else cl[ip];sl=r.sweep_extreme if r.dir==1 else r.sweep_extreme+sp[ip]
        risk=(en-sl) if r.dir==1 else (sl-en)
        if risk<=0:continue
        tp=en+r.dir*risk;w=-1
        for i in range(ip+1,len(mt)):
            if r.dir==1:ht=hi[i]>=tp;hs=lo[i]<=sl
            else:ah=hi[i]+sp[i];al=lo[i]+sp[i];ht=al<=tp;hs=ah>=sl
            if ht and hs:w=0;break
            if hs:w=0;break
            if ht:w=1;break
        rows.append((j,r.year,r.dir,t,risk,w))
    return pd.DataFrame(rows,columns=['base_index','year','dir','entry_time','risk','win1'])


def economic_probe(df,m1,partial=0.25,runner_r=3.0):
    mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);sp=m1.spread_px.to_numpy(float)
    rows=[]
    for r in df.itertuples(index=False):
        ip=np.searchsorted(mt,np.datetime64(r.trigger_time),side='left')-1
        one=r.entry+r.dir*r.risk;target=r.entry+r.dir*runner_r*r.risk;stage=0;res=np.nan;runner=False
        for i in range(ip+1,len(mt)):
            if r.dir==1:
                if stage==0:
                    ht=hi[i]>=one;hs=lo[i]<=r.sl_exec
                    if ht and hs or hs:res=-1.0;break
                    if ht:stage=1;continue
                    continue
                ht=hi[i]>=target;hbe=lo[i]<=r.entry
            else:
                ah=hi[i]+sp[i];al=lo[i]+sp[i]
                if stage==0:
                    ht=al<=one;hs=ah>=r.sl_exec
                    if ht and hs or hs:res=-1.0;break
                    if ht:stage=1;continue
                    continue
                ht=al<=target;hbe=ah>=r.entry
            if ht and hbe or hbe:res=partial;break
            if ht:res=partial+(1-partial)*runner_r;runner=True;break
        rows.append((r.year,res,runner))
    return pd.DataFrame(rows,columns=['year','R','runner'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('data',type=Path);args=ap.parse_args()
    c=load_c_module();m1=c.load_gold(args.data)
    years=set(m1.index.year.unique())
    if not years.issubset({2023,2024,2025}):raise SystemExit(f'FAIL-CLOSED: V3-003D accepts discovery years 2023-2025 only, got {sorted(years)}')
    bars,piv,ends5,own5,chg5,cand,ev=build_reference(c,m1)
    ends1,own1,chg1=build_m1_owner(m1);cand=add_micro_path(cand,ends1,own1,chg1);ev=add_micro_path(ev,ends1,own1,chg1)
    print('CANDIDATE A');print(cand.groupby('year')[['win1','win1_costless','mirror_win1']].agg(['count','mean']).to_string())
    print('\nM1 CLEAN PATH — BROAD CONTROL');print(ev.groupby(['year','m1_clean_path']).win1.agg(['count','mean']).to_string())
    print('\nM1 CLEAN PATH — INSIDE CANDIDATE A');b=cand[cand.m1_clean_path].copy();print(b.groupby('year')[['win1','win1_costless','mirror_win1']].agg(['count','mean']).to_string())
    print('\nDIRECT M1 OWNERSHIP TRANSFER — INSIDE CANDIDATE A');d=cand[cand.m1_direct_transfer];print(d.groupby('year')[['win1','win1_costless','mirror_win1']].agg(['count','mean']).to_string())

    # Delayed confirmation variants: information arrives later, so Entry is moved later too.
    b5=bars['5min'];two=[];hold=[];reexp=[]
    pe5=piv['5min']
    for r in cand.itertuples(index=False):
        k=int(r.trigger_m5_index)+1;two.append(k if k<len(b5) and ((b5.close.iat[k]-r.broken_m5_level)*r.dir)>0 else None)
        typ='L' if r.dir==1 else 'H';q=pe5[(pe5.type==typ)&(pe5.available_at>r.trigger_time)].sort_values('available_at')
        kh=None;kr=None
        if len(q):
            p=q.iloc[0];tmp=np.searchsorted(ends5,np.datetime64(p.available_at),side='left')
            if ((float(p.price)-r.broken_m5_level)*r.dir)>0:
                kh=tmp;trigk=int(r.trigger_m5_index);ext=b5.high.iat[trigk] if r.dir==1 else b5.low.iat[trigk]
                for x in range(max(kh,trigk+1),len(b5)):
                    if own5[x]==-r.dir:break
                    if r.dir==1 and b5.low.iat[x]<r.sweep_extreme:break
                    if r.dir==-1 and b5.high.iat[x]>r.sweep_extreme:break
                    if (r.dir==1 and b5.close.iat[x]>ext) or (r.dir==-1 and b5.close.iat[x]<ext):kr=x;break
        hold.append(kh);reexp.append(kr)
    for name,arr in [('TWO_CLOSE',two),('STRUCTURAL_HOLD',hold),('REEXPANSION',reexp)]:
        q=delayed_eval(cand,arr,b5,ends5,m1);print('\nDELAYED',name);print(q.groupby('year').win1.agg(['count','mean']).to_string())

    # Separate economic-feasibility probe only; does not alter Entry authority.
    econ=economic_probe(b,m1,0.25,3.0)
    print('\nECONOMIC FEASIBILITY: M1-CLEAN SUBSET, +1R 25% / residual BE / 3R runner')
    for y,g in econ.groupby('year'):
        w=g[g.R>0];print(y,'n',len(g),'WR',float((g.R>0).mean()),'avgR',float(g.R.mean()),'avgWinner',float(w.R.mean()),'runnerRate',float(g.runner.mean()))

if __name__=='__main__':main()
