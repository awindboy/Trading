#!/usr/bin/env python3
from pathlib import Path
import pandas as pd, numpy as np, zipfile, heapq, math, os, json, time
from numba import njit

POINTS={'GOLD#':0.01,'BTCUSD#':0.01,'USDJPY#':0.001}

def load_member(z, name, point):
    with z.open(name) as fh:
        x=pd.read_csv(fh, sep='\t')
    x.columns=[c.strip('<> ').lower() for c in x.columns]
    ts=pd.to_datetime(x['date'].astype(str)+' '+x['time'].astype(str), errors='raise')
    y=pd.DataFrame(index=ts)
    y.index.name='ts'
    for c in ['open','high','low','close']:
        y[c]=pd.to_numeric(x[c],errors='raise').to_numpy(float)
    y['tickvol']=pd.to_numeric(x.get('tickvol',0),errors='coerce').fillna(0).to_numpy(float)
    y['spread']=pd.to_numeric(x['spread'],errors='raise').to_numpy(float)
    y['spread_px']=y['spread']*point
    if y.index.has_duplicates: raise ValueError("dups")
    return y.sort_index()

def resample_ohlc(m1, rule):
    x=m1.resample(rule,label='left',closed='left').agg(
        open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),
        tickvol=('tickvol','sum'),spread_px=('spread_px','median'))
    return x.dropna(subset=['open','high','low','close'])

def atr_series(df,n=14):
    prev=df.close.shift(1)
    tr=pd.concat([(df.high-df.low),(df.high-prev).abs(),(df.low-prev).abs()],axis=1).max(axis=1)
    return tr.rolling(n,min_periods=n).mean()

def pivot_events(df,k,tfmin):
    h=df.high.to_numpy(float); l=df.low.to_numpy(float); idx=df.index
    rows=[]
    for i in range(k,len(df)-k):
        if h[i]>np.max(h[i-k:i]) and h[i]>=np.max(h[i+1:i+k+1]):
            rows.append((idx[i+k]+pd.Timedelta(minutes=tfmin),idx[i],'H',h[i]))
        if l[i]<np.min(l[i-k:i]) and l[i]<=np.min(l[i+1:i+k+1]):
            rows.append((idx[i+k]+pd.Timedelta(minutes=tfmin),idx[i],'L',l[i]))
    return pd.DataFrame(rows,columns=['available_at','pivot_at','type','price']).sort_values('available_at').reset_index(drop=True)

def dc_swing_events(df,k,tfmin):
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

def bos_owner_with_break(df,pe,tfmin):
    ends=(df.index+pd.Timedelta(minutes=tfmin)).to_numpy(dtype='datetime64[ns]')
    close=df.close.to_numpy(float)
    H=pe[pe.type=='H'].sort_values('available_at'); L=pe[pe.type=='L'].sort_values('available_at')
    ht=H.available_at.to_numpy(dtype='datetime64[ns]'); hp=H.price.to_numpy(float)
    lt=L.available_at.to_numpy(dtype='datetime64[ns]'); lp=L.price.to_numpy(float)
    owner=np.zeros(len(df),dtype=np.int8); changed=np.zeros(len(df),dtype=np.int8)
    hlev=np.full(len(df),np.nan); llev=np.full(len(df),np.nan);cur=0
    for i,t in enumerate(ends):
        ih=np.searchsorted(ht,t,side='right')-1; il=np.searchsorted(lt,t,side='right')-1
        if ih>=0:hlev[i]=hp[ih]
        if il>=0:llev[i]=lp[il]
        new=cur
        if ih>=0 and close[i]>hp[ih]:new=1
        if il>=0 and close[i]<lp[il]:new=-1
        if new!=cur:changed[i]=new;cur=new
        owner[i]=cur
    return ends,owner,changed,hlev,llev

def persistent_reactions(m1,events):
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

def dedupe_enriched(r,pe):
    rows=[]
    if len(r)==0:
        return pd.DataFrame(columns=['sweep_time','dir','liq_price','liq_pivot_at','liq_available_at','liq_id','n_levels'])
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
        if mi>=len(mt) or mt[mi]!=np.datetime64(r.sweep_time): continue
        ext=float(lo[mi] if r.dir==1 else hi[mi])
        bi=np.searchsorted(ends5,np.datetime64(r.sweep_time),side='right')
        pre=own5[bi-1] if bi>0 else 0
        if pre!=-r.dir: continue
        for k in range(bi,len(b5)):
            bs=b5.index[k]; et=bs+pd.Timedelta(minutes=5)
            a=np.searchsorted(mt,np.datetime64(r.sweep_time),side='right') if k==bi else np.searchsorted(mt,np.datetime64(bs),side='left')
            b=np.searchsorted(mt,np.datetime64(et),side='left')
            plo=lo[a:b].min() if a<b else np.inf; phi=hi[a:b].max() if a<b else -np.inf
            if (r.dir==1 and plo<ext) or (r.dir==-1 and phi>ext): break
            if chg5[k]==r.dir:
                rows.append((r.sweep_time,r.dir,r.liq_price,r.liq_pivot_at,r.liq_available_at,r.liq_id,r.n_levels,ext,pd.Timestamp(ends5[k]),float(b5.close.iat[k]),pre,k))
                break
    return pd.DataFrame(rows,columns=['sweep_time','dir','liq_price','liq_pivot_at','liq_available_at','liq_id','n_levels','sweep_extreme','trigger_time','trigger_close','pre_m5_owner','trigger_m5_index'])

def state_at_scalar(t, ends, vals, default=0):
    p=np.searchsorted(ends,np.datetime64(t),side='right')-1
    return vals[p] if p>=0 else default

def attach_m1_path(tr, ends1, own1, chg1):
    ct=ends1[chg1!=0]
    cv=chg1[chg1!=0]
    paths=[]; startowners=[]; direct=[]; one=[]
    for r in tr.itertuples(index=False):
        start=state_at_scalar(r.sweep_time, ends1, own1)
        a=np.searchsorted(ct,np.datetime64(r.sweep_time),side='right')  # changes after sweep_time
        b=np.searchsorted(ct,np.datetime64(r.trigger_time),side='right') # through trigger
        seq=cv[a:b].tolist()
        startowners.append(int(start)); paths.append(','.join(map(str,seq)))
        direct.append(start==-r.dir and seq==[r.dir] and state_at_scalar(r.trigger_time, ends1, own1)==r.dir)
        one.append(start==-r.dir and seq==[r.dir,-r.dir,r.dir] and state_at_scalar(r.trigger_time, ends1, own1)==r.dir)
    out=tr.copy()
    out['m1_owner_at_sweep']=startowners;out['m1_path']=paths;out['m1_direct_transfer']=direct;out['m1_one_reneg']=one
    return out


def sign_arr(x):
    out=np.sign(x).astype(float)
    return out

def feature_grids(m1):
    h1=resample_ohlc(m1,'60min')
    h1e=(h1.index+pd.Timedelta(hours=1)).to_numpy(dtype='datetime64[ns]')
    c=h1.close
    d14=np.sign(c-c.shift(14)).fillna(0).to_numpy(np.int8)
    d24=np.sign(c-c.shift(24)).fillna(0).to_numpy(np.int8)
    age=np.zeros(len(h1),dtype=np.int32)
    prev=0; a=0
    for i,d in enumerate(d24):
        if d==0: a=0
        elif d==prev: a+=1
        else: a=1
        age[i]=a; prev=int(d)
    d1=resample_ohlc(m1,'1D')
    d1['atr14']=atr_series(d1,14)
    d1e=(d1.index+pd.Timedelta(days=1)).to_numpy(dtype='datetime64[ns]')
    atr=d1.atr14.to_numpy(float)
    return h1e,d14,d24,age,d1e,atr

def lookup_grid(times, ends, vals, default=0):
    tt=np.asarray(times,dtype='datetime64[ns]')
    p=np.searchsorted(ends,tt,side='right')-1
    if np.issubdtype(np.asarray(vals).dtype, np.floating):
        out=np.full(len(tt),np.nan,dtype=float)
    else:
        out=np.full(len(tt),default,dtype=np.asarray(vals).dtype)
    ok=p>=0
    out[ok]=np.asarray(vals)[p[ok]]
    return out

def attach_route_state(tr,m1,ends5,hlev5,llev5):
    q=tr.copy()
    h1e,d14,d24,age,d1e,d1atr=feature_grids(m1)
    q['d14']=lookup_grid(q.trigger_time,h1e,d14)
    q['d24']=lookup_grid(q.trigger_time,h1e,d24)
    q['d24_age']=lookup_grid(q.trigger_time,h1e,age)
    q['d1_atr']=lookup_grid(q.trigger_time,d1e,d1atr)
    q['broken_m5_level']=np.where(q.dir.to_numpy()==1,hlev5[q.trigger_m5_index.to_numpy(int)],llev5[q.trigger_m5_index.to_numpy(int)])
    mt=m1.index.to_numpy(dtype='datetime64[ns]'); sp=m1.spread_px.to_numpy(float); cl=m1.close.to_numpy(float)
    ip=np.searchsorted(mt,q.trigger_time.to_numpy(dtype='datetime64[ns]'),side='left')-1
    q['trigger_spread']=np.where(ip>=0,sp[np.maximum(ip,0)],np.nan)
    q['parent_entry']=np.where(q.dir.to_numpy()==1,q.trigger_close.to_numpy()+q.trigger_spread.to_numpy(),q.trigger_close.to_numpy())
    q['parent_sl']=np.where(q.dir.to_numpy()==1,q.sweep_extreme.to_numpy(),q.sweep_extreme.to_numpy()+q.trigger_spread.to_numpy())
    q['parent_risk']=np.abs(q.parent_entry-q.parent_sl)
    chart=q.trigger_close.to_numpy()-q.dir.to_numpy()*0.5*np.abs(q.trigger_close.to_numpy()-q.broken_m5_level.to_numpy())
    q['limit_entry']=np.where(q.dir.to_numpy()==1,chart+q.trigger_spread.to_numpy(),chart)
    q['planned_sl']=q.parent_sl
    q['planned_risk']=np.abs(q.limit_entry-q.planned_sl)
    q['improved']=np.where(q.dir.to_numpy()==1,q.limit_entry<q.parent_entry,q.limit_entry>q.parent_entry)
    q['geom']=(q.parent_risk>1e-12)&(q.planned_risk>1e-12)&q.improved&np.isfinite(q.broken_m5_level)
    q['scale']=np.nan;q['acceptance']=np.nan;q['menv_n_prior']=0;q['med_scale']=np.nan;q['med_accept']=np.nan;q['menv_hh']=False
    hist_s=[];hist_a=[]
    # rows already chronological by trigger
    for ix,r in q.sort_values('trigger_time').iterrows():
        if bool(r.m1_direct_transfer) and bool(r.geom) and np.isfinite(r.d1_atr) and r.d1_atr>0:
            scale=float(r.planned_risk/r.d1_atr)
            acc=float(((r.trigger_close-r.broken_m5_level)*r.dir)/r.d1_atr)
            n=len(hist_s)
            q.at[ix,'scale']=scale;q.at[ix,'acceptance']=acc;q.at[ix,'menv_n_prior']=n
            if n>=20:
                ms=float(np.median(hist_s));ma=float(np.median(hist_a))
                q.at[ix,'med_scale']=ms;q.at[ix,'med_accept']=ma
                q.at[ix,'menv_hh']=(scale>ms and acc>ma)
            hist_s.append(scale);hist_a.append(acc)
    q['h_auth']=q.m1_direct_transfer&q.geom&(q.menv_n_prior>=20)&q.menv_hh&(q.d24==q.dir)
    q['l1_auth']=q.m1_direct_transfer&(~q.h_auth)&(q.d14==q.dir)&(q.d24==q.dir)
    q['l2_auth']=q.m1_one_reneg&(q.d24==q.dir)
    q['module']=np.select([q.h_auth,q.l1_auth,q.l2_auth],['H','L1','L2'],default='NONE')
    return q.sort_values('trigger_time').reset_index(drop=True)

@njit
def sim_l_routes(start_idx, dirs, entry, sl, risk, hi, lo, sp, opn, maxbars=240):
    n=len(start_idx)
    pnl=np.full(n,np.nan); oc=np.zeros(n,np.int8); ri=np.full(n,-1,np.int64)
    # oc 1 TP, 2 SL, 3 TIME, 4 CENSORED
    for a in range(n):
        s=start_idx[a]
        if s<0 or s>=len(hi) or risk[a]<=0:
            oc[a]=4; continue
        end=min(s+maxbars, len(hi))
        done=False
        tp=entry[a]+dirs[a]*risk[a]
        for i in range(s,end):
            if dirs[a]==1:
                ht=hi[i]>=tp; hs=lo[i]<=sl[a]
            else:
                ah=hi[i]+sp[i]; al=lo[i]+sp[i]
                ht=al<=tp; hs=ah>=sl[a]
            if ht and hs:
                pnl[a]=-1.0;oc[a]=2;ri[a]=i;done=True;break
            if hs:
                pnl[a]=-1.0;oc[a]=2;ri[a]=i;done=True;break
            if ht:
                pnl[a]=1.0;oc[a]=1;ri[a]=i;done=True;break
        if done: continue
        cap=s+maxbars
        if cap < len(hi):
            if dirs[a]==1:
                ex=opn[cap]
                pnl[a]=(ex-entry[a])/risk[a]
            else:
                ex=opn[cap]+sp[cap]
                pnl[a]=(entry[a]-ex)/risk[a]
            oc[a]=3;ri[a]=cap
        else:
            oc[a]=4
    return pnl,oc,ri

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
        last=ends[a]
        if last<0: last=len(hi)-1
        for i in range(starts[a],min(last+1,len(hi))):
            if dirs[a]==1:
                terminal=(lo[i]<=sl0[a]) or (hi[i]>=entry0[a]+risk0[a]);fill=(lo[i]+sp[i])<=limit[a]
            else:
                terminal=(hi[i]+sp[i]>=sl0[a]) or (lo[i]+sp[i]<=entry0[a]-risk0[a]);fill=hi[i]>=limit[a]
            if terminal: break
            if fill: fi[a]=i;break
    return fi

@njit
def sim_h_from_fill(fi,dirs,entry,sl,risk,hi,lo,sp):
    n=len(fi); pnl=np.full(n,np.nan);oc=np.zeros(n,np.int8);ri=np.full(n,-1,np.int64)
    # oc 1 TP5, 2 BE3, 3 SL, 4 CENSORED, 0 NOFILL
    for a in range(n):
        if fi[a]<0: continue
        hit3=False
        for i in range(fi[a],len(hi)):
            if dirs[a]==1:
                fav=hi[i]-entry[a]; stop_orig=lo[i]<=sl[a]; stop_be=lo[i]<=entry[a]
            else:
                ah=hi[i]+sp[i];al=lo[i]+sp[i]; fav=entry[a]-al; stop_orig=ah>=sl[a]; stop_be=ah>=entry[a]
            rr=fav/risk[a]
            if not hit3:
                if stop_orig:
                    pnl[a]=-1.0;oc[a]=3;ri[a]=i;break
                if rr>=3:
                    hit3=True
                    if rr>=5:
                        pnl[a]=4.5;oc[a]=1;ri[a]=i;break
                    continue
            else:
                if stop_be:
                    pnl[a]=0.75;oc[a]=2;ri[a]=i;break
                if rr>=5:
                    pnl[a]=4.5;oc[a]=1;ri[a]=i;break
        if oc[a]==0:
            oc[a]=4
    return pnl,oc,ri

def simulate_routes(q,m1):
    out=q.copy()
    mt=m1.index.to_numpy(dtype='datetime64[ns]')
    hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);sp=m1.spread_px.to_numpy(float);opn=m1.open.to_numpy(float)
    out['prospective_fill_time']=pd.NaT
    out['pnl_R']=np.nan;out['outcome']='NO_TRADE';out['resolved_at']=pd.NaT
    # L
    mask=out.module.isin(['L1','L2'])
    if mask.any():
        z=out.loc[mask]
        s=np.searchsorted(mt,z.trigger_time.to_numpy(dtype='datetime64[ns]'),side='left')
        pnl,oc,ri=sim_l_routes(s,z.dir.to_numpy(np.int8),z.parent_entry.to_numpy(float),z.parent_sl.to_numpy(float),
                               z.parent_risk.to_numpy(float),hi,lo,sp,opn,240)
        idx=z.index
        out.loc[idx,'prospective_fill_time']=z.trigger_time.to_numpy()
        out.loc[idx,'pnl_R']=pnl
        labels=np.select([oc==1,oc==2,oc==3,oc==4],['TP1','SL','TIME','CENSORED'],default='?')
        out.loc[idx,'outcome']=labels
        rr=pd.to_datetime(np.where(ri>=0,mt[np.maximum(ri,0)],np.datetime64('NaT')))
        out.loc[idx,'resolved_at']=rr.to_numpy()
    # H
    mask=out.module.eq('H')
    if mask.any():
        z=out.loc[mask]
        starts0=np.searchsorted(mt,z.trigger_time.to_numpy(dtype='datetime64[ns]'),side='left')-1
        pres=parent_resolve(starts0,z.dir.to_numpy(np.int8),z.parent_entry.to_numpy(float),z.parent_sl.to_numpy(float),
                            z.parent_risk.to_numpy(float),hi,lo,sp)
        ends=np.where(pres>=0,pres,len(mt)-1)
        pstarts=np.searchsorted(mt,z.trigger_time.to_numpy(dtype='datetime64[ns]'),side='right')
        fi=pending_fill(pstarts,ends,z.dir.to_numpy(np.int8),z.parent_entry.to_numpy(float),z.parent_sl.to_numpy(float),
                        z.parent_risk.to_numpy(float),z.limit_entry.to_numpy(float),hi,lo,sp)
        pnl,oc,ri=sim_h_from_fill(fi,z.dir.to_numpy(np.int8),z.limit_entry.to_numpy(float),z.planned_sl.to_numpy(float),
                                  z.planned_risk.to_numpy(float),hi,lo,sp)
        idx=z.index
        ft=pd.to_datetime(np.where(fi>=0,mt[np.maximum(fi,0)],np.datetime64('NaT')))
        out.loc[idx,'prospective_fill_time']=ft.to_numpy()
        out.loc[idx,'pnl_R']=pnl
        labels=np.select([fi<0,(fi>=0)&(oc==1),(fi>=0)&(oc==2),(fi>=0)&(oc==3),(fi>=0)&(oc==4)],
                         ['NOFILL','TP5','BE3','SL','CENSORED'],default='?')
        out.loc[idx,'outcome']=labels
        rr=pd.to_datetime(np.where(ri>=0,mt[np.maximum(ri,0)],np.datetime64('NaT')))
        out.loc[idx,'resolved_at']=rr.to_numpy()
    # exposure acceptance across actual prospective fills
    out['accepted']=False;out['exposure_blocked']=False
    cands=out[out.module!='NONE'].copy()
    cands=cands[cands.prospective_fill_time.notna()].copy()
    cands['prio']=np.where(cands.module.eq('H'),0,1)
    cands=cands.sort_values(['prospective_fill_time','prio','trigger_time'])
    active=[] # (idx,dir,resolved_at)
    for ix,r in cands.iterrows():
        t=r.prospective_fill_time
        newact=[]
        for j,d,res in active:
            if pd.isna(res) or res>t:
                newact.append((j,d,res))
        active=newact
        if any(d==-int(r.dir) for j,d,res in active):
            out.at[ix,'exposure_blocked']=True
        else:
            out.at[ix,'accepted']=True
            active.append((ix,int(r.dir),r.resolved_at))
    return out

def process_market(z,name):
    sym=name.split('_M1_')[0]; point=POINTS[sym]
    m1=load_member(z,name,point)
    # audit
    bad_ohlc=((m1.high < m1[['open','close','low']].max(axis=1)) | (m1.low > m1[['open','close','high']].min(axis=1))).sum()
    prof={
        'market':sym,'rows':len(m1),'start':m1.index.min(),'end':m1.index.max(),
        'trading_days':m1.index.normalize().nunique(),'dup':m1.index.duplicated().sum(),
        'nonmonotonic':int((np.diff(m1.index.view('i8'))<=0).sum()),'ohlc_errors':int(bad_ohlc),
        'zero_spread':int((m1.spread<=0).sum()),'spread_points_median':float(m1.spread.median()),
        'spread_points_p95':float(m1.spread.quantile(.95)),'spread_px_median':float(m1.spread_px.median())
    }
    bars={r:resample_ohlc(m1,r) for r in ['1min','5min','15min']}
    bars['15min']['atr14']=atr_series(bars['15min'])
    piv5=pivot_events(bars['5min'],2,5)
    ends5,own5,chg5,hlev5,llev5=bos_owner_with_break(bars['5min'],piv5,5)
    piv1=pivot_events(bars['1min'],2,1)
    ends1,own1,chg1,_,_=bos_owner_with_break(bars['1min'],piv1,1)
    source=dc_swing_events(bars['15min'],2.0,15)
    rr=dedupe_enriched(persistent_reactions(m1,source),source)
    tr=build_triggers(rr,m1,bars['5min'],ends5,own5,chg5)
    tr=attach_m1_path(tr,ends1,own1,chg1)
    q=attach_route_state(tr,m1,ends5,hlev5,llev5)
    q.insert(0,'market',sym)
    s=simulate_routes(q,m1)
    return m1,prof,s


def max_dd(vals):
    eq=0.0; peak=0.0; dd=0.0
    for v in vals:
        eq+=float(v); peak=max(peak,eq); dd=max(dd,peak-eq)
    return dd

def max_loss_streak(vals):
    cur=best=0
    for v in vals:
        if v<0: cur+=1; best=max(best,cur)
        else: cur=0
    return best

def metric(g):
    p=g[g.pnl_R>0]
    return pd.Series({
        'N':len(g),
        'WR':float((g.pnl_R>0).mean()) if len(g) else np.nan,
        'avg_positive_R':float(p.pnl_R.mean()) if len(p) else np.nan,
        'EV_R':float(g.pnl_R.mean()) if len(g) else np.nan,
        'net_R':float(g.pnl_R.sum()) if len(g) else 0.0
    })

def main():
    import argparse
    ap=argparse.ArgumentParser(description="V6-003D frozen 2026 independent-factor offline validator")
    ap.add_argument("input_zip", type=Path)
    ap.add_argument("--out", type=Path, default=Path("v6_validation_out"))
    args=ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.input_zip) as z:
        names=sorted([n for n in z.namelist() if n.lower().endswith(".csv")])
        allres={}; profiles=[]
        for name in names:
            sym=name.split("_M1_")[0]
            if sym not in POINTS:
                raise RuntimeError(f"Unknown point mapping for {sym}; add it explicitly before running.")
            m,prof,s=process_market(z,name)
            profiles.append(prof); allres[sym]=(m,s)
            print(sym, "triggers",len(s),"routes",int((s.module!="NONE").sum()),"accepted",int(s.accepted.sum()))
    prof_df=pd.DataFrame(profiles)
    all_s=pd.concat([s for _,s in allres.values()],ignore_index=True)
    route=all_s[all_s.module!="NONE"].copy()
    acc=route[route.accepted & route.prospective_fill_time.notna()].copy()
    res=acc[acc.pnl_R.notna()].copy()

    rows=[]
    for sym,(m,s) in allres.items():
        fills=s[(s.module!="NONE") & s.prospective_fill_time.notna()]
        aa=fills[fills.accepted]; rr=aa[aa.pnl_R.notna()].sort_values("prospective_fill_time"); pp=rr[rr.pnl_R>0]
        elig=s[s.m1_direct_transfer & s.geom & s.d1_atr.notna()]
        sv=elig[elig.menv_n_prior>=20]
        rows.append({
            "market":sym,"triggers":len(s),"direct":int(s.m1_direct_transfer.sum()),"one_reneg":int(s.m1_one_reneg.sum()),
            "menv_eligible":len(elig),"menv_state_valid":len(sv),"menv_HH":int(sv.menv_hh.sum()),
            "H_auth":int(s.h_auth.sum()),"H_fills":int((s.module.eq("H") & s.prospective_fill_time.notna()).sum()),
            "L1_auth":int(s.l1_auth.sum()),"L2_auth":int(s.l2_auth.sum()),"accepted_fills":len(aa),
            "resolved":len(rr),"censored":int(aa.pnl_R.isna().sum()),
            "WR":float((rr.pnl_R>0).mean()) if len(rr) else np.nan,
            "avg_positive_R":float(pp.pnl_R.mean()) if len(pp) else np.nan,
            "EV_R":float(rr.pnl_R.mean()) if len(rr) else np.nan,"net_R":float(rr.pnl_R.sum()),
            "max_DD_R":max_dd(rr.pnl_R.tolist()),"max_loss_streak":max_loss_streak(rr.pnl_R.tolist())
        })
    pd.DataFrame(rows).to_csv(args.out/"market_summary.csv",index=False)
    prof_df.to_csv(args.out/"data_quality.csv",index=False)
    all_s.sort_values(["market","trigger_time"]).to_csv(args.out/"all_triggers_routed.csv",index=False)
    res.sort_values(["prospective_fill_time","market"]).to_csv(args.out/"accepted_resolved_trades.csv",index=False)
    res.groupby("module").apply(metric,include_groups=False).reset_index().to_csv(args.out/"module_summary.csv",index=False)
    l2=res[res.module=="L2"].copy()
    l2["age_bucket"]=np.where(l2.d24_age>=24,">=24","<24")
    l2.groupby("age_bucket").apply(metric,include_groups=False).reset_index().to_csv(args.out/"l2_age_shadow.csv",index=False)
    print("POOLED")
    print(metric(res).to_string())

if __name__ == "__main__":
    main()
