from pathlib import Path
import numpy as np,pandas as pd, importlib.util
OUT=Path('/mnt/data/v9_terminal_detector_20260915');D=OUT/'TERMINAL_CHILD_DATASET.csv';ACC=Path('/mnt/data/v9_htf_exhaustion_20260914_fast/ARRIVALS_ACCEPTED.csv');H4=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv')
d=pd.read_csv(D,parse_dates=['ts']).sort_values(['route_id','ts']).copy();acc=pd.read_csv(ACC,parse_dates=['entry_ts','challenge_ts','hybrid_exit_ts']);resolved=acc.groupby('route_id').challenge_ts.first().dropna().index;acc=acc[acc.route_id.isin(resolved)].copy();det=acc[acc.hybrid_status.isin(['SL','CHALLENGE_OPENS','NEXT_H4_LIQ'])&acc.hybrid_pnl.notna()].copy();ry=acc.groupby('route_id').entry_ts.min().dt.year.to_dict();last=acc.groupby('route_id').entry_ts.max().to_dict()
# prior extrema flags, first child false
for c,mode,nm in [('h4liq_same_active_n','min','same_count_new_min'),('h4liq_same_d1_S','max','same_d1_new_max'),('h4liq_distance_ratio','max','ratio_new_max'),('h4liq_opp_d1_S','min','opp_d1_new_min')]:
 vals=[]
 for rid,g in d.groupby('route_id',sort=False):
  a=g[c].to_numpy(float)
  for i,v in enumerate(a):
   if i==0 or not np.isfinite(v):vals.append(False);continue
   p=a[:i];p=p[np.isfinite(p)]
   vals.append(bool(len(p) and (v<np.min(p) if mode=='min' else v>np.max(p))))
 d[nm]=vals
rules={
 'COUNT_NEW_MIN':d.same_count_new_min,
 'D1_NEW_MAX':d.same_d1_new_max,
 'RATIO_NEW_MAX':d.ratio_new_max,
 'COUNTMIN_AND_D1MAX':d.same_count_new_min & d.same_d1_new_max,
 'COUNTMIN_AND_RATIOMAX':d.same_count_new_min & d.ratio_new_max,
 'D1MAX_AND_RATIOMAX':d.same_d1_new_max & d.ratio_new_max,
 'THREE_EXTREMA':d.same_count_new_min & d.same_d1_new_max & d.ratio_new_max,
 'OPP_CLOSER_AND_D1MAX':d.opp_d1_new_min & d.same_d1_new_max,
}
# HA fast
spec=importlib.util.spec_from_file_location('ha','/mnt/data/analyze_v9_terminal_ha_oracle.py');ha=importlib.util.module_from_spec(spec);spec.loader.exec_module(ha);h4=ha.build_h4_ha(H4);look={}
for s in ['UP','DOWN']:
 q=h4[h4.ha_side.eq(s)][['known_at','<CLOSE>']];look[s]=(q.known_at.to_numpy(dtype='datetime64[ns]'),q['<CLOSE>'].to_numpy(float))
def sig(t,side):
 opp='DOWN' if side=='UP' else 'UP';tt,pp=look[opp];j=np.searchsorted(tt,np.datetime64(t),side='right');return (pd.NaT,np.nan) if j>=len(tt) else (pd.Timestamp(tt[j]),float(pp[j]))
def met(g):
 x=g.sort_values('entry_ts').pnl.to_numpy(float);pos=x[x>0].sum();neg=-x[x<0].sum();eq=np.cumsum(x);pk=np.maximum.accumulate(np.r_[0,eq]);return x.sum(),pos/neg if neg else np.inf,(pk[1:]-eq).max()
rows=[]
for name,mask in rules.items():
 dd=d[mask].copy();
 # classification precision of flagged child
 precision=dd.last_child.mean() if len(dd) else np.nan
 for yr in [2022,2023,2024,2025,2026]:
  routes=[r for r,y in ry.items() if y==yr];base=det[det.route_id.isin(routes)].copy();base['pnl']=base.hybrid_pnl;basep=base.pnl.sum();cand=dd[dd.route_id.isin(routes)].sort_values('ts').groupby('route_id').first().reset_index();signals={r.route_id:sig(r.ts,r.primary) for r in cand.itertuples()};vals=[]
  for r in base.itertuples():
   st,px=signals.get(r.route_id,(pd.NaT,np.nan));use=pd.notna(st) and st>r.entry_ts and st<r.hybrid_exit_ts;vals.append(((px-r.entry) if r.direction=='UP' else (r.entry-px)) if use else r.hybrid_pnl)
  g=base.copy();g['pnl']=vals;p,pf,ddv=met(g);rows.append({'year':yr,'rule':name,'PnL':p,'delta':p-basep,'PF':pf,'DD':ddv,'flagged_children':len(dd[dd.route_id.isin(routes)]),'armed_routes':len(cand),'early':sum(r.ts<last[r.route_id] for r in cand.itertuples()),'flag_precision_all':precision})
out=pd.DataFrame(rows);out.to_csv(OUT/'TERMINAL_ROUTE_EXTREMA_RULES.csv',index=False);print(out.groupby('rule').agg(delta=('delta','sum'),min_delta=('delta','min'),PFmean=('PF','mean'),DDmax=('DD','max'),armed=('armed_routes','sum'),early=('early','sum'),precision=('flag_precision_all','first')).sort_values('delta',ascending=False).to_string());print('\nBY YEAR');print(out.sort_values(['year','delta'],ascending=[True,False]).to_string(index=False))
