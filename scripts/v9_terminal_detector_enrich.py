from pathlib import Path
import numpy as np,pandas as pd
P=Path('/mnt/data/v9_terminal_detector_20260915/TERMINAL_CHILD_DATASET.csv')
O=Path('/mnt/data/v9_htf_exhaustion_20260914_fast/H4_SWING_OBJECTS.csv')
A=Path('/mnt/data/v9_htf_exhaustion_20260914_fast/ARRIVALS_ACCEPTED.csv')
d=pd.read_csv(P,parse_dates=['ts'])
o=pd.read_csv(O,parse_dates=['known_at','raid_ts','source_ts'])
acc=pd.read_csv(A,parse_dates=['entry_ts'])
first=d.groupby('route_id').first()[['ts']].rename(columns={'ts':'first_child_ts'})
rows=[]
for r in d.itertuples():
    t=pd.Timestamp(r.ts); ft=first.loc[r.route_id,'first_child_ts']; side=r.primary; opp='DOWN' if side=='UP' else 'UP'
    prev=d[(d.route_id==r.route_id)&(d.ts<t)].ts.max()
    if pd.isna(prev): prev=ft
    # born means object became causally known by this point
    same=o[o.side.eq(side)]; op=o[o.side.eq(opp)]
    born_same_prev=((same.known_at>prev)&(same.known_at<=t)).sum()
    born_opp_prev=((op.known_at>prev)&(op.known_at<=t)).sum()
    born_same_first=((same.known_at>ft)&(same.known_at<=t)).sum()
    born_opp_first=((op.known_at>ft)&(op.known_at<=t)).sum()
    raid_same_first=((same.raid_ts>=ft)&(same.raid_ts<=t)).sum()
    raid_same_prev=((same.raid_ts>prev)&(same.raid_ts<=t)).sum()
    active_same=same[(same.known_at<=t)&(same.raid_ts.isna()| (same.raid_ts>t))]
    active_opp=op[(op.known_at<=t)&(op.raid_ts.isna()| (op.raid_ts>t))]
    # route-born currently active ladder
    as_new=active_same[active_same.known_at>ft]
    ao_new=active_opp[active_opp.known_at>ft]
    as_old=active_same[active_same.known_at<=ft]
    ao_old=active_opp[active_opp.known_at<=ft]
    cur=o[(o.raid_ts==t)&(o.side==side)]
    cur_age=((t-cur.known_at).dt.total_seconds()/3600) if len(cur) else pd.Series(dtype=float)
    # previously consumed same-side objects in this route, causal history
    prevraid=same[(same.raid_ts>=ft)&(same.raid_ts<t)].copy()
    prev_age=(prevraid.raid_ts-prevraid.known_at).dt.total_seconds()/3600 if len(prevraid) else pd.Series(dtype=float)
    z={
      'h4_birth_same_since_prev':float(born_same_prev),'h4_birth_opp_since_prev':float(born_opp_prev),
      'h4_birth_balance_since_prev':float(born_same_prev-born_opp_prev),
      'h4_birth_ratio_since_prev':(born_same_prev+0.5)/(born_opp_prev+0.5),
      'h4_birth_same_since_first':float(born_same_first),'h4_birth_opp_since_first':float(born_opp_first),
      'h4_birth_balance_since_first':float(born_same_first-born_opp_first),
      'h4_birth_ratio_since_first':(born_same_first+0.5)/(born_opp_first+0.5),
      'h4_raid_same_since_prev':float(raid_same_prev),'h4_raid_same_since_first':float(raid_same_first),
      'h4_replenish_net_since_first':float(born_same_first-raid_same_first),
      'h4_replenish_ratio_since_first':(born_same_first+0.5)/(raid_same_first+0.5),
      'h4_active_same_routeborn_n':float(len(as_new)),'h4_active_opp_routeborn_n':float(len(ao_new)),
      'h4_active_same_preroute_n':float(len(as_old)),'h4_active_opp_preroute_n':float(len(ao_old)),
      'h4_active_routeborn_balance':float(len(as_new)-len(ao_new)),
      'h4_active_routeborn_ratio':(len(as_new)+0.5)/(len(ao_new)+0.5),
      'current_liq_age_vs_prior_median':float(cur_age.median()-prev_age.median()) if len(cur_age) and len(prev_age) else np.nan,
      'current_liq_age_ratio_prior_median':float(cur_age.median()/prev_age.median()) if len(cur_age) and len(prev_age) and prev_age.median()>0 else np.nan,
      'current_liq_age_prior_percentile':float((np.sum(prev_age<cur_age.median())+0.5*np.sum(prev_age==cur_age.median()))/len(prev_age)) if len(cur_age) and len(prev_age) else np.nan,
    }
    # nearest remaining same/opp object born during route vs before route
    def nearest_origin(active):
        if len(active)==0:return np.nan
        if side=='UP': dist=np.where(active.side.eq('UP'),active.price-r.ref,r.ref-active.price)
        else: dist=np.where(active.side.eq('DOWN'),r.ref-active.price,active.price-r.ref)
        j=np.nanargmin(dist)
        return float(active.iloc[j].known_at>ft)
    z['h4_nearest_same_routeborn']=nearest_origin(active_same)
    # for opp function distance formula based opp side
    if len(active_opp):
        if side=='UP': dist=r.ref-active_opp.price.to_numpy(float)
        else: dist=active_opp.price.to_numpy(float)-r.ref
        j=int(np.nanargmin(dist)); z['h4_nearest_opp_routeborn']=float(active_opp.iloc[j].known_at>ft)
    else:z['h4_nearest_opp_routeborn']=np.nan
    rows.append(z)
new=pd.DataFrame(rows)
d=pd.concat([d,new],axis=1)
# Causal route-relative transforms for key level features: ratio/current-vs-first and running extrema.
keys=['h4liq_same_active_n','h4liq_opp_active_n','h4liq_same_d1_S','h4liq_opp_d1_S','h4liq_distance_ratio','h4liq_same_age1_h','h4liq_opp_age1_h','current_liq_age_median_h','current_liq_age_max_h']
for c in keys:
    firstv=d.groupby('route_id')[c].transform('first')
    d[f'ratiofirst_{c}']=(d[c]+1e-6)/(firstv+1e-6)
    # expanding prior median including current is causal; useful as route-relative scale.
    med=[]; maxv=[]; minv=[]
    for rid,g in d.groupby('route_id',sort=False):
        vals=g[c].to_numpy(float)
        for i,v in enumerate(vals):
            past=vals[:i+1]; finite=past[np.isfinite(past)]
            med.append(np.nanmedian(finite) if len(finite) else np.nan)
            maxv.append(np.nanmax(finite) if len(finite) else np.nan)
            minv.append(np.nanmin(finite) if len(finite) else np.nan)
    # groupby order matches dataframe because sorted by route in build
    med=np.asarray(med);maxv=np.asarray(maxv);minv=np.asarray(minv)
    d[f'relmedian_{c}']=d[c]/med
    d[f'is_running_max_{c}']=np.where(np.isfinite(d[c]),(d[c]>=maxv).astype(float),np.nan)
    d[f'is_running_min_{c}']=np.where(np.isfinite(d[c]),(d[c]<=minv).astype(float),np.nan)
# H1 structural SL progression from first/current previous accepted child
# structural SL absolute recovered from ref +/- sl distance using direction.
sign=np.where(d.primary.eq('UP'),1.0,-1.0)
d['structural_sl_price']=d.ref-sign*d.sl_atr180*d.atr180
firstsl=d.groupby('route_id').structural_sl_price.transform('first')
d['sl_progress_from_first_S']=sign*(d.structural_sl_price-firstsl)/d.atr180
d['sl_change_prev_S']=d.groupby('route_id').structural_sl_price.diff()*sign/d.atr180

d.to_csv(P,index=False)
print('enriched',d.shape)
print(d[[c for c in d if c.startswith('h4_birth_')][:6]+['h4_replenish_net_since_first','current_liq_age_prior_percentile']].describe().to_string())
