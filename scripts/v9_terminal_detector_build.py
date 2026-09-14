from __future__ import annotations
import importlib.util, hashlib
from pathlib import Path
import numpy as np, pandas as pd

BASE=Path('/mnt/data/v9_htf_exhaustion_20260914_fast')
OUT=Path('/mnt/data/v9_terminal_detector_20260915'); OUT.mkdir(exist_ok=True)
M1=Path('/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv')
H1=Path('/mnt/data/GOLD#_H1_202201030100_202608282300.csv')
H4=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv')
EXP='626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2'
assert hashlib.sha256(M1.read_bytes()).hexdigest()==EXP
spec=importlib.util.spec_from_file_location('jm','/mnt/data/v9_journey_end_20260914/v9_journey_end_model.py')
jm=importlib.util.module_from_spec(spec); spec.loader.exec_module(jm)

arr=pd.read_csv(BASE/'ARRIVALS.csv',parse_dates=['ts','next_ts'])
acc=pd.read_csv(BASE/'ARRIVALS_ACCEPTED.csv',parse_dates=['entry_ts','next_ts','challenge_ts','base_exit_ts','hybrid_exit_ts'])
h1o=pd.read_csv(BASE/'H1_SWING_OBJECTS.csv',parse_dates=['source_ts','known_at','raid_ts'])
h4o=pd.read_csv(BASE/'H4_SWING_OBJECTS.csv',parse_dates=['source_ts','known_at','raid_ts'])
# exclude the one unresolved terminal route because literal last child is censored
resolved_routes=acc.groupby('route_id').challenge_ts.first().dropna().index
acc=acc[acc.route_id.isin(resolved_routes)].copy().sort_values(['route_id','entry_ts']).reset_index(drop=True)
route_n=acc.groupby('route_id').size().rename('route_total_accepted')
acc=acc.join(route_n,on='route_id')
acc['last_child']=(acc.accepted_rank==acc.route_total_accepted).astype(int)

# Event frame compatible with existing causal feature builders.
ev=pd.DataFrame({
    'ts':acc.entry_ts,'route_id':acc.route_id,'primary':acc.direction,'ref':acc.entry,
    'atr180':acc.atr180,'atr14':acc.atr14,'entry_authorized':True,'sl_atr180':acc.sl_atr180,
}).reset_index(drop=True)

# H1 chart and ladder features are exactly the previous causal definitions.
h1f=jm.completed_h1_features(ev)
liq=jm.ladder_features(ev,h1o,h4o)

# Build M1 arrays for path stats.
m=pd.read_csv(M1,sep='\t',usecols=['<DATE>','<TIME>','<HIGH>','<LOW>','<CLOSE>'])
m['ts']=pd.to_datetime(m['<DATE>']+' '+m['<TIME>'])
mts=m.ts.to_numpy(dtype='datetime64[ns]'); hi=m['<HIGH>'].to_numpy(float); lo=m['<LOW>'].to_numpy(float); cl=m['<CLOSE>'].to_numpy(float)
arrs=arr.sort_values('ts')
route_start=arrs.groupby('route_id').first()[['ts','ref']].rename(columns={'ts':'route_start_ts','ref':'route_start_ref'})
first_acc=acc.groupby('route_id').first()[['entry_ts','entry']].rename(columns={'entry_ts':'first_acc_ts','entry':'first_acc_entry'})
anchor=acc[acc.accepted_rank==1][['route_id','entry_ts','entry','structural_sl','sl_dist','sl_atr180','hybrid_exit_ts','hybrid_exit_price','hybrid_pnl','hybrid_status']].rename(columns={
    'entry_ts':'anchor_entry_ts','entry':'anchor_entry','structural_sl':'anchor_sl','sl_dist':'anchor_sl_dist','sl_atr180':'anchor_sl_atr180','hybrid_exit_ts':'anchor_exit_ts','hybrid_exit_price':'anchor_exit_price','hybrid_pnl':'anchor_exit_pnl','hybrid_status':'anchor_exit_status'
}).set_index('route_id')

posrows=[]
for r in acc.itertuples():
    t=pd.Timestamp(r.entry_ts); S=float(r.atr180); sign=1.0 if r.direction=='UP' else -1.0
    rs=route_start.loc[r.route_id]; fa=first_acc.loc[r.route_id]; a=anchor.loc[r.route_id]
    rr=arrs[(arrs.route_id==r.route_id)&(arrs.ts<=t)].sort_values('ts')
    # Accepted children up through current decision point.
    ach=acc[(acc.route_id==r.route_id)&(acc.entry_ts<=t)].sort_values('entry_ts')
    prior=ach[ach.entry_ts<t]
    # Open state just after current accepted Child; exits at current timestamp from older Child are already resolved.
    route_all=acc[acc.route_id==r.route_id]
    entered=route_all[route_all.entry_ts<=t]
    open_after=entered[entered.hybrid_exit_ts.isna() | (entered.hybrid_exit_ts>t)]
    closed_before=entered[entered.hybrid_exit_ts.notna() & (entered.hybrid_exit_ts<=t) & entered.hybrid_pnl.notna()]
    z={
      'primary_is_up':1.0 if r.direction=='UP' else 0.0,
      'accepted_rank_raw':float(r.accepted_rank),
      'route_age_h':(t-rs.route_start_ts).total_seconds()/3600,
      'accepted_age_h':(t-fa.first_acc_ts).total_seconds()/3600,
      'route_progress_S':sign*(r.entry-rs.route_start_ref)/S,
      'accepted_progress_S':sign*(r.entry-fa.first_acc_entry)/S,
      'route_arrival_count':float(len(rr)),
      'route_same_arrival_count':float((rr.arrival_side==r.direction).sum()),
      'hours_since_prev_arrival':(t-rr.ts.iloc[-2]).total_seconds()/3600 if len(rr)>=2 else np.nan,
      'hours_since_prev_child':(t-prior.entry_ts.iloc[-1]).total_seconds()/3600 if len(prior) else np.nan,
      'price_since_prev_child_S':sign*(r.entry-prior.entry.iloc[-1])/S if len(prior) else np.nan,
      'current_sl_atr180':r.sl_atr180,
      'open_children_after':float(len(open_after)),
      'open_cont_after':float((open_after.role=='CONTINUATION_CHILD').sum()),
      'closed_children_count':float(len(closed_before)),
      'closed_cont_count':float((closed_before.role=='CONTINUATION_CHILD').sum()),
    }
    # anchor state at decision time (no future use)
    anchor_alive=bool(pd.isna(a.anchor_exit_ts) or a.anchor_exit_ts>t)
    z['anchor_alive']=float(anchor_alive)
    z['anchor_age_h']=(t-a.anchor_entry_ts).total_seconds()/3600
    if anchor_alive:
        z['anchor_unreal_S']=sign*(r.entry-a.anchor_entry)/S
        z['anchor_unreal_R']=sign*(r.entry-a.anchor_entry)/a.anchor_sl_dist if a.anchor_sl_dist>0 else np.nan
    else:
        z['anchor_unreal_S']=np.nan; z['anchor_unreal_R']=np.nan
    z['anchor_realized_S']=sign*(a.anchor_exit_price-a.anchor_entry)/S if (not anchor_alive and pd.notna(a.anchor_exit_price)) else np.nan
    z['anchor_sl_atr180']=a.anchor_sl_atr180
    i0=np.searchsorted(mts,np.datetime64(a.anchor_entry_ts),'left'); i1=np.searchsorted(mts,np.datetime64(t),'left')
    if i1>i0:
        if r.direction=='UP':
            peak=max(np.max(hi[i0:i1]),r.entry); trough=min(np.min(lo[i0:i1]),r.entry)
            mfe=(peak-a.anchor_entry)/S; mae=(a.anchor_entry-trough)/S
        else:
            trough=min(np.min(lo[i0:i1]),r.entry); peak=max(np.max(hi[i0:i1]),r.entry)
            mfe=(a.anchor_entry-trough)/S; mae=(peak-a.anchor_entry)/S
        z['anchor_mfe_S']=mfe; z['anchor_mae_S']=mae
        cur=sign*(r.entry-a.anchor_entry)/S
        z['anchor_peak_giveback_S']=mfe-cur
    else:
        z['anchor_mfe_S']=z['anchor_mae_S']=z['anchor_peak_giveback_S']=np.nan
    # realized previous Child economics known now
    cc=closed_before[closed_before.role=='CONTINUATION_CHILD'].sort_values('hybrid_exit_ts')
    if len(cc):
        vals=(cc.hybrid_pnl/cc.atr180).to_numpy(float)
        z['closed_cont_cum_pnl_S']=float(vals.sum()); z['closed_cont_mean_pnl_S']=float(vals.mean()); z['closed_cont_win_rate']=float((vals>0).mean()); z['last_cont_pnl_S']=float(vals[-1])
    else:
        z['closed_cont_cum_pnl_S']=0.0; z['closed_cont_mean_pnl_S']=np.nan; z['closed_cont_win_rate']=np.nan; z['last_cont_pnl_S']=np.nan
    posrows.append(z)
pos=pd.DataFrame(posrows)

# Completed H4 low-dimensional state, known only when bar closes.
h4=pd.read_csv(H4,sep='\t')
h4['ts']=pd.to_datetime(h4['<DATE>']+' '+h4['<TIME>']); h4['known_at']=h4.ts+pd.Timedelta(hours=4)
for c in ['<OPEN>','<HIGH>','<LOW>','<CLOSE>']: h4[c]=h4[c].astype(float)
hknown=h4.known_at.to_numpy(dtype='datetime64[ns]'); hop=h4['<OPEN>'].to_numpy(float); hhi=h4['<HIGH>'].to_numpy(float); hlo=h4['<LOW>'].to_numpy(float); hcl=h4['<CLOSE>'].to_numpy(float)
h4rows=[]
for r in acc.itertuples():
    t=np.datetime64(r.entry_ts); j=np.searchsorted(hknown,t,side='right')-1; S=float(r.atr180); sign=1 if r.direction=='UP' else -1
    z={}
    for w in [1,2,3,6,12]:
        aidx=j-w+1; b=j+1
        if aidx<0 or j<0:
            for nm in ['net','range','rv','eff','mean_range','body_mean']:
                z[f'h4_{nm}_{w}b']=np.nan
        else:
            c=hcl[aidx:b]; hh=hhi[aidx:b]; ll=hlo[aidx:b]; oo=hop[aidx:b]
            dif=np.diff(c); den=np.sum(np.abs(dif))
            z[f'h4_net_{w}b']=sign*(c[-1]-c[0])/S if w>1 else sign*(c[-1]-oo[-1])/S
            z[f'h4_range_{w}b']=(np.max(hh)-np.min(ll))/S
            z[f'h4_rv_{w}b']=np.sqrt(np.sum(dif*dif))/S if len(dif) else 0.0
            z[f'h4_eff_{w}b']=abs(c[-1]-c[0])/den if den>0 else (1.0 if w==1 else 0.0)
            z[f'h4_mean_range_{w}b']=np.mean(hh-ll)/S
            z[f'h4_body_mean_{w}b']=np.mean(sign*(c-oo))/S
    h4rows.append(z)
h4f=pd.DataFrame(h4rows)

meta=acc[['entry_ts','route_id','accepted_rank','route_total_accepted','role','direction','entry','atr180','atr14','sl_atr180','last_child','challenge_ts','hybrid_status','hybrid_exit_ts','hybrid_exit_price','hybrid_pnl']].rename(columns={'entry_ts':'ts','direction':'primary','entry':'ref'}).reset_index(drop=True)
d=pd.concat([meta,h1f.reset_index(drop=True),h4f.reset_index(drop=True),liq.reset_index(drop=True),pos.reset_index(drop=True)],axis=1)
d['year']=d.ts.dt.year

# Geometry transforms, no fitted thresholds.
for prefix in ['h4liq','h1liq']:
    s1=d[f'{prefix}_same_d1_S']; s2=d[f'{prefix}_same_d2_S']; s3=d[f'{prefix}_same_d3_S']; o1=d[f'{prefix}_opp_d1_S']; o2=d[f'{prefix}_opp_d2_S']; o3=d[f'{prefix}_opp_d3_S']
    d[f'{prefix}_same_missing1']=s1.isna().astype(float); d[f'{prefix}_same_missing2']=s2.isna().astype(float); d[f'{prefix}_same_missing3']=s3.isna().astype(float)
    d[f'{prefix}_opp_missing1']=o1.isna().astype(float)
    d[f'{prefix}_same_gap12_S']=s2-s1; d[f'{prefix}_same_gap23_S']=s3-s2
    d[f'{prefix}_opp_gap12_S']=o2-o1; d[f'{prefix}_opp_gap23_S']=o3-o2
    d[f'{prefix}_nearest_margin_S']=o1-s1
    d[f'{prefix}_active_balance']=d[f'{prefix}_same_active_n']-d[f'{prefix}_opp_active_n']
    d[f'{prefix}_active_ratio']=(d[f'{prefix}_same_active_n']+1)/(d[f'{prefix}_opp_active_n']+1)

# Within-route changes from previous and first accepted Child, computed only from current/past features.
delta_cols=[
 'h4liq_same_d1_S','h4liq_same_d2_S','h4liq_same_d3_S','h4liq_opp_d1_S','h4liq_distance_ratio','h4liq_same_active_n','h4liq_opp_active_n',
 'h1liq_same_d1_S','h1liq_opp_d1_S','h1liq_distance_ratio',
 'current_liq_age_median_h','current_liq_age_max_h','route_progress_S','accepted_progress_S','anchor_mfe_S','anchor_peak_giveback_S','atr14_atr180',
 'h1_eff_6h','h1_eff_24h','h1_range_24h','h1_rv_24h','h4_eff_3b','h4_range_3b','h4_rv_3b'
]
for c in delta_cols:
    if c not in d: continue
    d[f'dprev_{c}']=d.groupby('route_id')[c].diff()
    first=d.groupby('route_id')[c].transform('first')
    d[f'dfirst_{c}']=d[c]-first

# terminal geometry summaries with interpretable continuous transforms only.
d['h4liq_log_distance_ratio']=np.log(d.h4liq_distance_ratio.replace(0,np.nan))
d['h1liq_log_distance_ratio']=np.log(d.h1liq_distance_ratio.replace(0,np.nan))
d['route_last_rank_pct_diag']=d.accepted_rank/d.route_total_accepted # DIAGNOSTIC/FUTURE! never model feature

d.to_csv(OUT/'TERMINAL_CHILD_DATASET.csv',index=False)
print('rows',len(d),'routes',d.route_id.nunique(),'positive',d.last_child.sum(),'rate',d.last_child.mean())
print('years',d.groupby('year').agg(n=('last_child','size'),routes=('route_id','nunique'),pos=('last_child','sum')).to_dict('index'))
print('saved',OUT/'TERMINAL_CHILD_DATASET.csv')
