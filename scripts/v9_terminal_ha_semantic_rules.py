from pathlib import Path
import numpy as np,pandas as pd
OUT=Path('/mnt/data/v9_terminal_detector_20260915');D=OUT/'TERMINAL_H4_CHECKPOINT_DATASET.csv';ACC=Path('/mnt/data/v9_htf_exhaustion_20260914_fast/ARRIVALS_ACCEPTED.csv')
ev=pd.read_csv(D,parse_dates=['ts']);ev=ev[ev.ha_opp==1].copy();acc=pd.read_csv(ACC,parse_dates=['entry_ts','challenge_ts','hybrid_exit_ts']);resolved=acc.groupby('route_id').challenge_ts.first().dropna().index;acc=acc[acc.route_id.isin(resolved)].copy();det=acc[acc.hybrid_status.isin(['SL','CHALLENGE_OPENS','NEXT_H4_LIQ'])&acc.hybrid_pnl.notna()].copy();ry=acc.groupby('route_id').entry_ts.min().dt.year.to_dict();last=acc.groupby('route_id').entry_ts.max().to_dict()
rules={
 'ANY_HA':lambda x:np.ones(len(x),bool),
 'OPPOSITE_NEAREST':lambda x:(x.h4c_same_nearest==0).to_numpy(bool),
 'NO_SAME_TARGET':lambda x:x.h4c_same_d1_S.isna().to_numpy(bool),
 'OPP_NEAREST_OR_NO_SAME':lambda x:((x.h4c_same_nearest==0)|x.h4c_same_d1_S.isna()).to_numpy(bool),
 'RATIO_WORSENED':lambda x:(x.since_child_h4liq_distance_ratio>0).fillna(False).to_numpy(bool),
 'OPP_NEAREST_AND_RATIO_WORSENED':lambda x:((x.h4c_same_nearest==0)&(x.since_child_h4liq_distance_ratio>0)).fillna(False).to_numpy(bool),
 'SAME_DISTANCE_WIDENED':lambda x:(x.since_child_h4liq_same_d1_S>0).fillna(False).to_numpy(bool),
 'OPP_NEAREST_AND_SAME_WIDENED':lambda x:((x.h4c_same_nearest==0)&(x.since_child_h4liq_same_d1_S>0)).fillna(False).to_numpy(bool),
}
def met(g):
 x=g.sort_values('entry_ts').pnl.to_numpy(float);pos=x[x>0].sum();neg=-x[x<0].sum();eq=np.cumsum(x);pk=np.maximum.accumulate(np.r_[0,eq]);return {'PnL':x.sum(),'PF':pos/neg if neg else np.inf,'WR':(x>0).mean(),'DD':(pk[1:]-eq).max(),'P95':np.quantile(x,.95),'Max':x.max(),'N':len(x)}
rows=[]
for yr in [2022,2023,2024,2025,2026]:
 routes=[r for r,y in ry.items() if y==yr];base=det[det.route_id.isin(routes)].copy();base['pnl']=base.hybrid_pnl;base_pnl=base.pnl.sum()
 for name,fn in rules.items():
  ee=ev[ev.route_id.isin(routes)].sort_values('ts').copy();mask=fn(ee);ee=ee[mask];chosen=ee.groupby('route_id').first().reset_index();emap={r.route_id:r for r in chosen.itertuples()};vals=[];chg=[]
  for r in base.itertuples():
   e=emap.get(r.route_id);use=e is not None and e.ts>r.entry_ts and e.ts<r.hybrid_exit_ts
   vals.append(((e.price-r.entry) if r.direction=='UP' else (r.entry-e.price)) if use else r.hybrid_pnl);chg.append(use)
  g=base.copy();g['pnl']=vals;m=met(g);m.update(year=yr,rule=name,delta=m['PnL']-base_pnl,event_routes=len(chosen),early=sum(r.ts<last[r.route_id] for r in chosen.itertuples()),changed=sum(chg));rows.append(m)
out=pd.DataFrame(rows);out.to_csv(OUT/'TERMINAL_HA_SEMANTIC_RULES.csv',index=False);print(out.groupby('rule').agg(PnL=('PnL','sum'),delta=('delta','sum'),min_delta=('delta','min'),PFmean=('PF','mean'),DDmax=('DD','max'),events=('event_routes','sum'),early=('early','sum'),changed=('changed','sum')).sort_values('delta',ascending=False).to_string());print('\nBY YEAR');print(out.sort_values(['year','delta'],ascending=[True,False])[['year','rule','PnL','delta','PF','DD','event_routes','early','changed']].to_string(index=False))
