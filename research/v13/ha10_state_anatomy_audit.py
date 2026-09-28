from __future__ import annotations
import sys, math, json, re, argparse
from pathlib import Path
from collections import deque, defaultdict, Counter
import numpy as np, pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
sys.path.insert(0,str(Path(__file__).resolve().parent))
import research.v13.state_anatomy_v13 as sav
from research.v13.state_anatomy_v13 import *

# ---------- causal H4 swing state, following frozen HA-5 convention ----------
def add_h4_pivots(h4: pd.DataFrame) -> pd.DataFrame:
    last_hi = last_lo = None  # (price, origin_idx, confirm_idx)
    prev_close = None
    prev_used_hi_origin = prev_used_lo_origin = None
    five=deque(maxlen=5)
    rows=[]
    def interaction(bar, level, orient, previous_used_origin):
        if level is None: return 'no_level'
        price, origin_idx, conf_idx = level
        extreme = bar.high if orient==1 else bar.low
        exceeded = orient*(extreme-price) > EPS
        close_beyond = orient*(bar.close-price) > EPS
        same = origin_idx == previous_used_origin
        previous_beyond = same and prev_close is not None and orient*(prev_close-price)>EPS
        if previous_beyond and not close_beyond: return 'return_inside'
        if close_beyond and previous_beyond: return 'held_close_beyond'
        if close_beyond: return 'fresh_close_beyond'
        if exceeded: return 'probe_rejected'
        return 'no_break'
    for i,r in enumerate(h4.itertuples(index=False)):
        hi_before=last_hi; lo_before=last_lo
        hi_state=interaction(r,hi_before,1,prev_used_hi_origin)
        lo_state=interaction(r,lo_before,-1,prev_used_lo_origin)
        prev_used_hi_origin = hi_before[1] if hi_before else None
        prev_used_lo_origin = lo_before[1] if lo_before else None
        prev_close=float(r.close)
        five.append((i,float(r.high),float(r.low)))
        if len(five)==5:
            cand=five[2]; others=[five[j] for j in (0,1,3,4)]
            if all(cand[1] > o[1] for o in others): last_hi=(cand[1],cand[0],i)
            if all(cand[2] < o[2] for o in others): last_lo=(cand[2],cand[0],i)
        rows.append({
            'pivot_high_before':hi_before[0] if hi_before else np.nan,
            'pivot_low_before':lo_before[0] if lo_before else np.nan,
            'pivot_high_after':last_hi[0] if last_hi else np.nan,
            'pivot_low_after':last_lo[0] if last_lo else np.nan,
            'pivot_high_age_after':i-last_hi[2] if last_hi else np.nan,
            'pivot_low_age_after':i-last_lo[2] if last_lo else np.nan,
            'high_state_before':hi_state,'low_state_before':lo_state,
        })
    return pd.concat([h4,pd.DataFrame(rows,index=h4.index)],axis=1)

class Window:
    def __init__(self, frame:pd.DataFrame):
        self.df=frame
        self.times=frame.time.to_numpy('datetime64[ns]')
        self.ns=self.times.astype('int64')
        self.open=frame.open.to_numpy(float); self.high=frame.high.to_numpy(float); self.low=frame.low.to_numpy(float); self.close=frame.close.to_numpy(float)
        self.tick=frame.tick_volume.to_numpy(float) if 'tick_volume' in frame else None
        self.rel=frame.rel_activity.to_numpy(float) if 'rel_activity' in frame else None
    def bounds(self,start,end):
        a=int(np.searchsorted(self.ns,np.datetime64(pd.Timestamp(start),'ns').astype('int64'),'left'))
        b=int(np.searchsorted(self.ns,np.datetime64(pd.Timestamp(end),'ns').astype('int64'),'left'))
        return a,b
    def slice(self,start,end):
        a,b=self.bounds(start,end); return a,b

# Full-bar post-entry path: only bars whose start >= ceil(entry to TF) and close <= checkpoint.
def ceil_time(t:pd.Timestamp, minutes:int):
    base=t.floor(f'{minutes}min')
    return base if t==base else base+pd.Timedelta(minutes=minutes)

def record_counts(values, favor=True):
    count=0; best=None
    for x in values:
        if best is None or (x>best if favor else x<best):
            count+=1; best=x
    return count

def path_metrics(win:Window, entry_time, end_time, side, entry, scale, tf_minutes:int):
    st=ceil_time(pd.Timestamp(entry_time),tf_minutes)
    en=pd.Timestamp(end_time)
    a,b=win.bounds(st,en)  # bars starting < end; ensure complete below
    # Only bars whose close is <= end. Since b excludes starts >= end, all starts are < end; drop last if incomplete.
    if b>a and pd.Timestamp(win.times[b-1])+pd.Timedelta(minutes=tf_minutes) > en:
        b-=1
    if b<=a:
        return {f'n_{tf_minutes}m':0}
    hi=win.high[a:b]; lo=win.low[a:b]; cl=win.close[a:b]
    directional_close=side*(cl-entry)
    path=np.r_[0.0,directional_close]
    travel=float(np.abs(np.diff(path)).sum())
    progress=float(directional_close[-1])
    mfe=float(np.max(hi)-entry) if side==1 else float(entry-np.min(lo))
    mae=float(entry-np.min(lo)) if side==1 else float(np.max(hi)-entry)
    signs=np.sign(directional_close)
    nonzero=signs[signs!=0]
    crossings=int(np.sum(nonzero[1:]!=nonzero[:-1])) if len(nonzero)>1 else 0
    favorable_ext = hi if side==1 else -lo
    adverse_ext = -lo if side==1 else hi
    fav_records=record_counts(favorable_ext,True)
    adv_records=record_counts(adverse_ext,True)
    runmax=np.maximum.accumulate(directional_close)
    giveback=float(np.max(runmax-directional_close)) if len(directional_close) else np.nan
    # first adverse then recovery to >=0 close
    adverse_idx=np.flatnonzero(directional_close<0)
    recovery=False; recovery_bar=np.nan
    if len(adverse_idx):
        later=np.flatnonzero(directional_close[adverse_idx[0]+1:]>=0)
        if len(later): recovery=True; recovery_bar=int(adverse_idx[0]+1+later[0]+1)
    rel=np.nan
    if win.rel is not None:
        vals=win.rel[a:b]; rel=float(np.nanmean(vals)) if np.isfinite(vals).any() else np.nan
    aligned_frac=float(np.mean(directional_close>0))
    close_seq=''.join('A' if x>0 else 'O' if x<0 else 'F' for x in directional_close)
    return {
        f'n_{tf_minutes}m':int(b-a),
        f'{tf_minutes}m_progress_n':progress/scale if scale else np.nan,
        f'{tf_minutes}m_mfe_n':mfe/scale if scale else np.nan,
        f'{tf_minutes}m_mae_n':mae/scale if scale else np.nan,
        f'{tf_minutes}m_efficiency':progress/travel if travel>0 else 0.0,
        f'{tf_minutes}m_crossings':crossings,
        f'{tf_minutes}m_fav_records':fav_records,
        f'{tf_minutes}m_adv_records':adv_records,
        f'{tf_minutes}m_giveback_n':giveback/scale if scale else np.nan,
        f'{tf_minutes}m_recovered_after_adverse':recovery,
        f'{tf_minutes}m_recovery_bar':recovery_bar,
        f'{tf_minutes}m_rel_activity':rel,
        f'{tf_minutes}m_aligned_frac':aligned_frac,
        f'{tf_minutes}m_close_seq':close_seq,
    }

def m1_path_metrics(win:Window, entry_time,end_time,side,entry,scale,target):
    # Include the entry minute only if entry is exactly on minute boundary; otherwise start next full minute.
    st=ceil_time(pd.Timestamp(entry_time),1); en=pd.Timestamp(end_time)
    a,b=win.bounds(st,en)
    if b<=a: return {'n_m1':0}
    hi=win.high[a:b]; lo=win.low[a:b]; cl=win.close[a:b]
    d=side*(cl-entry); path=np.r_[0.0,d]; travel=float(np.abs(np.diff(path)).sum())
    progress=float(d[-1]); mfe=float(np.max(hi)-entry) if side==1 else float(entry-np.min(lo)); mae=float(entry-np.min(lo)) if side==1 else float(np.max(hi)-entry)
    signs=np.sign(d); nz=signs[signs!=0]; crossings=int(np.sum(nz[1:]!=nz[:-1])) if len(nz)>1 else 0
    favorable_ext=hi if side==1 else -lo; adverse_ext=-lo if side==1 else hi
    fav_records=record_counts(favorable_ext,True); adv_records=record_counts(adverse_ext,True)
    first_dir=int(np.sign(d[0])) if len(d) else 0
    target_hits=np.flatnonzero(hi>target+EPS) if side==1 else np.flatnonzero(lo<target-EPS)
    target_close=np.flatnonzero(cl>target+EPS) if side==1 else np.flatnonzero(cl<target-EPS)
    init_dist=side*(target-entry)
    best_to_target = mfe/init_dist if init_dist>EPS else np.nan
    return {
      'n_m1':int(b-a),'m1_progress_n':progress/scale if scale else np.nan,'m1_mfe_n':mfe/scale if scale else np.nan,'m1_mae_n':mae/scale if scale else np.nan,
      'm1_efficiency':progress/travel if travel>0 else 0.0,'m1_crossings':crossings,'m1_fav_records':fav_records,'m1_adv_records':adv_records,'m1_first_close_dir':first_dir,
      'm1_target_hit':bool(len(target_hits)),'m1_target_close_accept':bool(len(target_close)),'m1_target_hit_bar':int(target_hits[0]+1) if len(target_hits) else np.nan,
      'm1_target_close_bar':int(target_close[0]+1) if len(target_close) else np.nan,'m1_target_approach_ratio':best_to_target,
    }

def partial_h4(m1:Window, h4:pd.DataFrame, signal_idx:int, nominal_start, checkpoint, side, scale):
    a,b=m1.bounds(nominal_start,checkpoint)
    if b<=a: return {}
    o=float(h4.iloc[signal_idx+1].open); hi=float(np.max(m1.high[a:b])); lo=float(np.min(m1.low[a:b])); cl=float(m1.close[b-1])
    prev=h4.iloc[signal_idx]
    ho=(float(prev.h4ha_open)+float(prev.h4ha_close))/2.0
    hc=(o+hi+lo+cl)/4.0
    hh=max(hi,ho,hc); hl=min(lo,ho,hc); hr=hh-hl
    side_delta=side*(hc-ho)
    opp_wick=(min(ho,hc)-hl) if side==1 else (hh-max(ho,hc))
    raw_rng=hi-lo
    # side-oriented HASTOC strength using last 9 completed d + partial current d
    d_hist=(h4.h4ha_open-h4.h4ha_close).iloc[max(0,signal_idx-8):signal_idx+1].to_numpy(float)
    d_cur=ho-hc
    if len(d_hist)>=9:
        w=np.r_[d_hist[-9:],d_cur]; span=float(w.max()-w.min()); raw=100*(d_cur-w.min())/span if span else np.nan
        hs=(100-raw) if side==1 else raw
    else: hs=np.nan
    return {
      'ph4_side_delta_n':side_delta/scale if scale else np.nan,
      'ph4_body_ratio':abs(hc-ho)/hr if hr else 0.0,
      'ph4_opp_wick_n':opp_wick/scale if scale else np.nan,
      'ph4_raw_progress_n':side*(cl-o)/scale if scale else np.nan,
      'ph4_raw_close_pos':side*(cl-hc)/raw_rng if raw_rng else 0.0,
      'ph4_hastoc_strength':hs,
    }

def proof_time(m1:Window,row):
    a,b=m1.bounds(pd.Timestamp(row.entry_time).floor('min'), pd.Timestamp(row.nominal_entry)+pd.Timedelta(hours=4))
    if b<=a: return pd.NaT
    hits=np.flatnonzero(m1.high[a:b]>row.signal_high+EPS) if row.side==1 else np.flatnonzero(m1.low[a:b]<row.signal_low-EPS)
    return pd.Timestamp(m1.times[a+int(hits[0])]) if len(hits) else pd.NaT

def extract_features(df,h4,h1,m1,m5,m15,m30):
    h4_idx={t:i for i,t in enumerate(h4.time)}
    h1_by_start=h1.set_index('time')
    rows=[]
    for r in df.itertuples(index=False):
        sigi=int(r.signal_idx); sig=h4.iloc[sigi]; scale=float(sig.median_range20) if pd.notna(sig.median_range20) and sig.median_range20>0 else float(sig.raw_range)
        side=int(r.side); target=float(r.signal_high if side==1 else r.signal_low)
        lag=(pd.Timestamp(r.entry_time)-pd.Timestamp(r.nominal_entry)).total_seconds()
        progress_state = sig.high_state_before if side==1 else sig.low_state_before
        adverse_state = sig.low_state_before if side==1 else sig.high_state_before
        active_progress = sig.pivot_high_after if side==1 else sig.pivot_low_after
        active_adverse = sig.pivot_low_after if side==1 else sig.pivot_high_after
        hastoc_strength = (100-float(sig.hastoc10)) if side==1 and pd.notna(sig.hastoc10) else (float(sig.hastoc10) if pd.notna(sig.hastoc10) else np.nan)
        out={
          'journey':int(r.journey),'child':int(r.child),'side':side,'signal':pd.Timestamp(r.signal),'entry_time':pd.Timestamp(r.entry_time),'exit_time':pd.Timestamp(r.exit_time),
          'profit':float(r.profit),'hold_hours':float(r.hold_hours),'entry_price':float(r.entry_price),'target':target,'nominal_entry':pd.Timestamp(r.nominal_entry),
          'year':pd.Timestamp(r.signal).year,'quarter':str(pd.Timestamp(r.signal).to_period('Q')),'entry_lagged':lag>0,'entry_lag_sec':lag,
          't0_range_norm20':float(sig.range_norm20),'t0_delta_norm20':float(sig.delta_norm20),'t0_body_ratio':float(sig.h4ha_body_ratio),
          't0_delta_contract':bool(sig.delta_contract),'t0_wick_present':bool(sig.wick_present),'t0_wick_reappeared':bool(sig.wick_reappeared),
          't0_raw_close_pos':float(sig.raw_close_pos),'t0_streak':int(sig.h4ha_streak),'t0_hastoc_strength':hastoc_strength,
          't0_progress_state':progress_state,'t0_adverse_state':adverse_state,
          't0_progress_level_dist_n': side*(float(active_progress)-float(r.entry_price))/scale if pd.notna(active_progress) else np.nan,
          't0_adverse_level_dist_n': -side*(float(active_adverse)-float(r.entry_price))/scale if pd.notna(active_adverse) else np.nan,
        }
        pt=proof_time(m1,r); out['proof_time']=pt; out['proof_minutes']=(pt-pd.Timestamp(r.entry_time)).total_seconds()/60 if pd.notna(pt) else np.nan
        # resolution path up to actual exit, capped at proof H4 end to keep the same initial-action horizon.
        anatomy_end=min(pd.Timestamp(r.exit_time),pd.Timestamp(r.nominal_entry)+pd.Timedelta(hours=4))
        out.update(m1_path_metrics(m1,r.entry_time,anatomy_end,side,float(r.entry_price),scale,target))
        out.update(path_metrics(m5,r.entry_time,anatomy_end,side,float(r.entry_price),scale,5))
        out.update(path_metrics(m15,r.entry_time,anatomy_end,side,float(r.entry_price),scale,15))
        out.update(path_metrics(m30,r.entry_time,anatomy_end,side,float(r.entry_price),scale,30))
        # valid H1 completions after actual entry, inside proof H4 and known by exit.
        h1_starts=h1[(h1.time>=pd.Timestamp(r.nominal_entry))&(h1.time<pd.Timestamp(r.nominal_entry)+pd.Timedelta(hours=4))]
        valid=[]
        for hh in h1_starts.itertuples(index=False):
            cp=pd.Timestamp(hh.time)+pd.Timedelta(hours=1)
            if cp>pd.Timestamp(r.entry_time) and cp<=pd.Timestamp(r.exit_time): valid.append((hh,cp))
        seq=[]
        for k,(hh,cp) in enumerate(valid[:4],start=1):
            aligned=int(hh.h1ha_color)==side; seq.append('A' if aligned else 'O')
            out[f't{k}_clock']=cp
            out[f't{k}_h1_aligned']=aligned
            out[f't{k}_h1_side_delta_n']=side*(float(hh.h1ha_close)-float(hh.h1ha_open))/scale
            out[f't{k}_h1_body_ratio']=float(hh.h1ha_body_ratio)
            advwick=(float(hh.h1ha_opp_wick)/scale) if int(hh.h1ha_color)==side else np.nan
            out[f't{k}_h1_opp_wick_n']=advwick
            out[f't{k}_h1_rel_activity']=float(hh.rel_activity20) if pd.notna(hh.rel_activity20) else np.nan
            out[f't{k}_h1_raw_progress_n']=side*(float(hh.close)-float(r.entry_price))/scale
            ph=partial_h4(m1,h4,sigi,r.nominal_entry,cp,side,scale)
            for key,val in ph.items(): out[f't{k}_{key}']=val
            # post-entry path up to checkpoint
            for src,name,mins in [(m5,'m5',5),(m15,'m15',15),(m30,'m30',30)]:
                pm=path_metrics(src,r.entry_time,cp,side,float(r.entry_price),scale,mins)
                for key,val in pm.items(): out[f't{k}_{key}']=val
            mm=m1_path_metrics(m1,r.entry_time,cp,side,float(r.entry_price),scale,target)
            for key,val in mm.items(): out[f't{k}_{key}']=val
            # known active H4 pivot progression by checkpoint
            a,b=m1.bounds(r.nominal_entry,cp)
            if b>a:
                hi=float(np.max(m1.high[a:b])); lo=float(np.min(m1.low[a:b])); cl=float(m1.close[b-1])
                if pd.notna(active_progress):
                    pbreak = hi>active_progress+EPS if side==1 else lo<active_progress-EPS
                    pclose = cl>active_progress+EPS if side==1 else cl<active_progress-EPS
                else: pbreak=pclose=False
                if pd.notna(active_adverse):
                    abreak = lo<active_adverse-EPS if side==1 else hi>active_adverse+EPS
                    aclose = cl<active_adverse-EPS if side==1 else cl>active_adverse+EPS
                else: abreak=aclose=False
                out[f't{k}_progress_swing_probe']=bool(pbreak); out[f't{k}_progress_swing_close']=bool(pclose)
                out[f't{k}_adverse_swing_probe']=bool(abreak); out[f't{k}_adverse_swing_close']=bool(aclose)
        out['h1_observed_count']=len(valid); out['h1_seq']=''.join(seq)
        rows.append(out)
    return pd.DataFrame(rows)

# ---------- matching ----------
def match_groups(A,B,continuous,exact=('quarter','side','child','entry_lagged')):
    pairs=[]
    # global SD from pooled data for cost normalization; robust fallback
    pooled=pd.concat([A,B],ignore_index=True)
    scales={c:float(pooled[c].std()) if pd.notna(pooled[c].std()) and pooled[c].std()>1e-12 else 1.0 for c in continuous}
    keys=sorted(set(map(tuple,A[list(exact)].astype(str).to_numpy())).intersection(set(map(tuple,B[list(exact)].astype(str).to_numpy()))))
    for key in keys:
        maskA=np.ones(len(A),dtype=bool); maskB=np.ones(len(B),dtype=bool)
        for c,v in zip(exact,key):
            maskA &= A[c].astype(str).to_numpy()==v; maskB &= B[c].astype(str).to_numpy()==v
        aa=A.loc[maskA]; bb=B.loc[maskB]
        if aa.empty or bb.empty: continue
        XA=aa[list(continuous)].astype(float).to_numpy(); XB=bb[list(continuous)].astype(float).to_numpy()
        # impute within stratum by pooled median, then global fallback 0
        for j,c in enumerate(continuous):
            vals=np.r_[XA[:,j],XB[:,j]]; med=np.nanmedian(vals)
            if not np.isfinite(med): med=0.0
            XA[:,j]=np.where(np.isfinite(XA[:,j]),XA[:,j],med); XB[:,j]=np.where(np.isfinite(XB[:,j]),XB[:,j],med)
            XA[:,j]/=scales[c]; XB[:,j]/=scales[c]
        cost=((XA[:,None,:]-XB[None,:,:])**2).sum(axis=2)
        ia,ib=linear_sum_assignment(cost)
        for x,y in zip(ia,ib): pairs.append((aa.index[x],bb.index[y],float(cost[x,y])))
    return pd.DataFrame(pairs,columns=['a_idx','b_idx','cost'])

def smd(a,b):
    a=np.asarray(pd.Series(a).dropna(),float); b=np.asarray(pd.Series(b).dropna(),float)
    if len(a)<2 or len(b)<2:return np.nan
    den=np.sqrt((a.var(ddof=1)+b.var(ddof=1))/2)
    return (a.mean()-b.mean())/den if den>0 else 0.0

def bootstrap_diff(A,B,feature,func=np.nanmean,draws=500,seed=13):
    # Frozen matched sample, resample Journey clusters independently in each arm.
    rng=np.random.default_rng(seed)
    aj=A[['journey',feature]].dropna(); bj=B[['journey',feature]].dropna()
    idsA=aj.journey.unique(); idsB=bj.journey.unique()
    if not len(idsA) or not len(idsB): return (np.nan,np.nan,np.nan)
    obs=float(func(aj[feature].to_numpy(float))-func(bj[feature].to_numpy(float)))
    vals=[]
    ga={j:g[feature].to_numpy(float) for j,g in aj.groupby('journey')}; gb={j:g[feature].to_numpy(float) for j,g in bj.groupby('journey')}
    for _ in range(draws):
        sa=rng.choice(idsA,size=len(idsA),replace=True); sb=rng.choice(idsB,size=len(idsB),replace=True)
        va=np.concatenate([ga[j] for j in sa]); vb=np.concatenate([gb[j] for j in sb]); vals.append(float(func(va)-func(vb)))
    lo,hi=np.quantile(vals,[.025,.975])
    return obs,float(lo),float(hi)

def bool_boot(A,B,feature):
    return bootstrap_diff(A.assign(**{feature:A[feature].astype(float)}),B.assign(**{feature:B[feature].astype(float)}),feature,np.nanmean)

def common_seq(df,col,minn=20):
    vc=df[col].fillna('missing').value_counts(); return vc[vc>=minn].to_dict()

def summarize_match(A,B,pairs,labelA,labelB,features):
    aa=A.loc[pairs.a_idx].copy(); bb=B.loc[pairs.b_idx].copy(); aa.index=range(len(aa)); bb.index=range(len(bb))
    out={'pairs':len(pairs),'A':labelA,'B':labelB,'features':{}}
    for f in features:
        if f not in aa or f not in bb: continue
        if pd.api.types.is_bool_dtype(aa[f]) or pd.api.types.is_bool_dtype(bb[f]):
            obs,lo,hi=bool_boot(aa,bb,f); out['features'][f]={'A_rate':float(aa[f].mean()),'B_rate':float(bb[f].mean()),'diff':obs,'ci95':[lo,hi]}
        elif pd.api.types.is_numeric_dtype(aa[f]) and pd.api.types.is_numeric_dtype(bb[f]):
            obs,lo,hi=bootstrap_diff(aa,bb,f,np.nanmean); out['features'][f]={'A_mean':float(aa[f].mean()),'B_mean':float(bb[f].mean()),'diff':obs,'ci95':[lo,hi],'smd':smd(aa[f],bb[f])}
    return out,aa,bb

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data-dir',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    sav.set_data_dir(args.data_dir)
    print('loading...')
    h4=add_h4_pivots(add_h4_features(load_bars('GOLD#_H4_202201030000_202608282000.csv')))
    h1=add_h1_features(load_bars('GOLD#_H1_202201030100_202608282300.csv'))
    # LTF activity normalized by same clock slot prior 20 occurrences (causal)
    frames={}
    for tf,name,mins in [('m1','GOLD#_M1_202201030100_202608282357(5).csv',1),('m5','GOLD#_M5_202201030100_202608282355.csv',5),('m15','GOLD#_M15_202201030100_202608282345.csv',15),('m30','GOLD#_M30_202201030100_202608282330.csv',30)]:
        d=load_bars(name)
        if tf!='m1':
            d['slot']=d.time.dt.hour*(60//mins)+d.time.dt.minute//mins
            d['slot_med20']=d.groupby('slot').tick_volume.transform(lambda s:s.shift(1).rolling(20,min_periods=20).median())
            d['rel_activity']=d.tick_volume/d.slot_med20
        frames[tf]=d
    actual=parse_report(); ideal=build_ideal_children(h4)
    canon=actual[(actual.entry_time>=START)&(actual.exit_time<=CUTOFF)].copy().merge(ideal,on=['journey','child','side'],how='left',validate='one_to_one')
    add=canon[canon.child>=2].copy()
    print('extracting',len(add))
    feat=extract_features(add,h4,h1,Window(frames['m1']),Window(frames['m5']),Window(frames['m15']),Window(frames['m30']))
    feat['label']=np.select([
      (feat.profit>0)&(feat.hold_hours<=1),
      (feat.profit>0)&(feat.hold_hours>1)&(feat.hold_hours<4),
      (feat.profit<0)&(feat.hold_hours>=4)&(feat.hold_hours<8),
      feat.hold_hours>=8],['W_LE1','W_1_4','L_4_8','SURV_8P'],default='OTHER')
    outdir=args.output; outdir.mkdir(parents=True,exist_ok=True)
    feat.to_csv(outdir/'state_anatomy_features.csv',index=False)
    print(feat.label.value_counts())
    # matching sets
    B=feat[feat.label=='L_4_8'].copy(); A1=feat[feat.label=='W_LE1'].copy(); A2=feat[feat.label=='W_1_4'].copy()
    match_cov=['t0_range_norm20','t0_delta_norm20','t0_body_ratio','t0_raw_close_pos']
    p1=match_groups(A1,B,match_cov); p2=match_groups(A2,B,match_cov)
    print('pairs A1/B',len(p1),'A2/B',len(p2))
    # T0 contrasts
    t0f=['t0_delta_norm20','t0_body_ratio','t0_delta_contract','t0_wick_present','t0_wick_reappeared','t0_raw_close_pos','t0_streak','t0_hastoc_strength','entry_lag_sec']
    s1,a1m,b1m=summarize_match(A1,B,p1,'W_LE1','L_4_8',t0f)
    s2,a2m,b2m=summarize_match(A2,B,p2,'W_1_4','L_4_8',t0f)
    # checkpoint contrasts A2 vs B for T1..T3 where both observed. Freeze matched pairs then require feature availability in both arms.
    dyn={}
    for k in (1,2,3):
        f=[f't{k}_h1_aligned',f't{k}_h1_side_delta_n',f't{k}_h1_raw_progress_n',f't{k}_h1_rel_activity',
           f't{k}_ph4_side_delta_n',f't{k}_ph4_body_ratio',f't{k}_ph4_opp_wick_n',f't{k}_ph4_raw_progress_n',f't{k}_ph4_hastoc_strength',
           f't{k}_m1_progress_n',f't{k}_m1_mfe_n',f't{k}_m1_mae_n',f't{k}_m1_efficiency',f't{k}_m1_crossings',f't{k}_m1_fav_records',f't{k}_m1_adv_records',
           f't{k}_5m_progress_n',f't{k}_5m_efficiency',f't{k}_5m_crossings',f't{k}_5m_fav_records',f't{k}_5m_adv_records',f't{k}_5m_rel_activity',f't{k}_5m_aligned_frac',
           f't{k}_progress_swing_probe',f't{k}_progress_swing_close',f't{k}_adverse_swing_probe',f't{k}_adverse_swing_close']
        # pairwise availability on checkpoint clock
        aa=A2.loc[p2.a_idx]; bb=B.loc[p2.b_idx]
        valid=np.array([(f't{k}_clock' in aa.columns and pd.notna(x) and pd.notna(y)) for x,y in zip(aa.get(f't{k}_clock',pd.Series(index=aa.index)),bb.get(f't{k}_clock',pd.Series(index=bb.index)))])
        pp=p2.loc[valid].copy()
        ss,_,_=summarize_match(A2,B,pp,f'W_1_4_T{k}',f'L_4_8_T{k}',f)
        dyn[f'T{k}']=ss
        print('T',k,'pairs',len(pp))
    # Quick-winner anatomy at actual resolution vs matched loss at same elapsed timestamp: compute path features for loss dynamically at winner elapsed time.
    # Reuse frozen pair mapping. Generate compact comparison on M1/M5 metrics at winner resolution time.
    quick_rows=[]
    wm1=Window(frames['m1']); wm5=Window(frames['m5'])
    # lookup raw merged rows for B
    raw_by_key={(int(r.journey),int(r.child)):r for r in add.itertuples(index=False)}
    for _,pr in p1.iterrows():
        wa=A1.loc[pr.a_idx]; lb=B.loc[pr.b_idx]
        elapsed=pd.Timestamp(wa.exit_time)-pd.Timestamp(wa.entry_time)
        lend=min(pd.Timestamp(lb.entry_time)+elapsed,pd.Timestamp(lb.exit_time),pd.Timestamp(lb.nominal_entry)+pd.Timedelta(hours=4))
        # derive scale from loss t0 signal
        br=raw_by_key[(int(lb.journey),int(lb.child))]; sig=h4.iloc[int(br.signal_idx)]; scale=float(sig.median_range20) if pd.notna(sig.median_range20) and sig.median_range20>0 else float(sig.raw_range)
        lm=m1_path_metrics(wm1,lb.entry_time,lend,int(lb.side),float(lb.entry_price),scale,float(lb.target))
        l5=path_metrics(wm5,lb.entry_time,lend,int(lb.side),float(lb.entry_price),scale,5)
        rec={'w_idx':pr.a_idx,'l_idx':pr.b_idx,'elapsed_min':elapsed.total_seconds()/60}
        for f in ['m1_progress_n','m1_mfe_n','m1_mae_n','m1_efficiency','m1_crossings','m1_fav_records','m1_adv_records','m1_target_approach_ratio']:
            rec['W_'+f]=wa.get(f,np.nan); rec['L_'+f]=lm.get(f,np.nan)
        for f in ['5m_progress_n','5m_efficiency','5m_crossings','5m_fav_records','5m_adv_records','5m_rel_activity','5m_aligned_frac']:
            rec['W_'+f]=wa.get(f,np.nan); rec['L_'+f]=l5.get(f,np.nan)
        quick_rows.append(rec)
    q=pd.DataFrame(quick_rows)
    qsummary={}
    for base in ['m1_progress_n','m1_mfe_n','m1_mae_n','m1_efficiency','m1_crossings','m1_fav_records','m1_adv_records','m1_target_approach_ratio','5m_progress_n','5m_efficiency','5m_crossings','5m_fav_records','5m_adv_records','5m_rel_activity','5m_aligned_frac']:
        x=q['W_'+base]; y=q['L_'+base]; valid=x.notna()&y.notna();
        if valid.sum():
            qsummary[base]={'n':int(valid.sum()),'W_mean':float(x[valid].mean()),'L_mean':float(y[valid].mean()),'diff':float((x[valid]-y[valid]).mean()),'median_pair_diff':float((x[valid]-y[valid]).median()),'smd':smd(x[valid],y[valid])}
    # Sequence tables in matched A2/B at T1/T2/T3 available: h1 sequence prefixes
    seq={}
    for k in (1,2,3):
        pp=p2.copy(); aa=A2.loc[pp.a_idx].copy(); bb=B.loc[pp.b_idx].copy()
        # sequence from observed H1 seq prefix k; only rows with >=k H1 checkpoints
        va=aa.h1_observed_count>=k; vb=bb.h1_observed_count>=k; v=va.to_numpy()&vb.to_numpy(); aa=aa.loc[v];bb=bb.loc[v]
        seq[f'T{k}']={'pairs':len(aa),'W':common_seq(aa.h1_seq.str[:k],None) if False else aa.h1_seq.str[:k].value_counts().to_dict(),'L':bb.h1_seq.str[:k].value_counts().to_dict()}
    # Year consistency of selected strongest dynamic raw metrics at T1 for A2/B matched sample
    year={}
    aa=A2.loc[p2.a_idx].copy(); bb=B.loc[p2.b_idx].copy(); aa['pairid']=range(len(aa)); bb['pairid']=range(len(bb))
    for yr in (2024,2025,2026):
        # because exact quarter matching, paired signals same year by construction
        v=(aa.year.to_numpy()==yr)&(bb.year.to_numpy()==yr)&aa.t1_clock.notna().to_numpy()&bb.t1_clock.notna().to_numpy()
        ag=aa.loc[v]; bg=bb.loc[v]
        year[str(yr)]={'pairs':len(ag)}
        for f in ['t1_ph4_side_delta_n','t1_m1_progress_n','t1_m1_efficiency','t1_m1_mae_n','t1_5m_aligned_frac','t1_h1_aligned']:
            if f in ag:
                if ag[f].dtype==bool: year[str(yr)][f]=float(ag[f].mean()-bg[f].mean())
                else: year[str(yr)][f]=float(ag[f].mean()-bg[f].mean())
    # Exploratory archetype clustering at T1 among A2+B matched observations, excluding proof/target variables and labels from fit.
    aa=A2.loc[p2.a_idx].copy(); bb=B.loc[p2.b_idx].copy(); aa['outcome']='W_1_4'; bb['outcome']='L_4_8'; pool=pd.concat([aa,bb],ignore_index=True)
    pool=pool[pool.t1_clock.notna()].copy()
    cfeatures=['t1_ph4_side_delta_n','t1_ph4_body_ratio','t1_ph4_opp_wick_n','t1_ph4_hastoc_strength','t1_h1_side_delta_n','t1_h1_raw_progress_n','t1_h1_rel_activity','t1_m1_progress_n','t1_m1_mfe_n','t1_m1_mae_n','t1_m1_efficiency','t1_m1_crossings','t1_5m_rel_activity','t1_5m_aligned_frac']
    X=pool[cfeatures].astype(float).copy()
    X=X.fillna(X.median())
    Z=StandardScaler().fit_transform(X)
    clusters={}
    for k in (2,3,4):
        km=KMeans(n_clusters=k,random_state=13,n_init=30).fit(Z); lab=km.labels_; sil=float(silhouette_score(Z,lab))
        temp=pool[['outcome','year','side','journey']].copy(); temp['cluster']=lab
        cs=[]
        for c,g in temp.groupby('cluster'):
            cs.append({'cluster':int(c),'n':len(g),'win_rate':float((g.outcome=='W_1_4').mean()),'journeys':int(g.journey.nunique()),'years':g.groupby('year').size().to_dict(),'sides':g.groupby('side').size().to_dict()})
        clusters[str(k)]={'silhouette':sil,'clusters':cs}
    result={
      'status':'CONSUMED DEVELOPMENT / STATE-ANATOMY OBSERVATION / NO ACTION AUTHORITY',
      'head_note':'GitHub main 652dcd0; HA-9 unchanged; action tests intentionally deferred.',
      'population':feat.label.value_counts().to_dict(),
      'proof_by_label':feat.groupby('label').proof_time.apply(lambda s:float(s.notna().mean())).to_dict(),
      'match':{'W_LE1_vs_L_4_8':s1,'W_1_4_vs_L_4_8':s2,'dynamic_W_1_4_vs_L_4_8':dyn},
      'quick_resolution_path':qsummary,
      'h1_sequences':seq,'year_consistency':year,'archetype_clustering_T1':clusters,
    }
    (outdir/'state_anatomy_summary.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    q.to_csv(outdir/'quick_resolution_pairs.csv',index=False)
    p1.to_csv(outdir/'match_WLE1_L48.csv',index=False);p2.to_csv(outdir/'match_W14_L48.csv',index=False)
    print(json.dumps({'population':result['population'],'proof':result['proof_by_label'],'pairs1':len(p1),'pairs2':len(p2),'T':{k:v['pairs'] for k,v in dyn.items()},'cluster':clusters},indent=2,default=str))

if __name__=='__main__': main()
