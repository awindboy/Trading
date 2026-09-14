import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
ACC=Path('/mnt/data/v9_htf_exhaustion_20260914_fast/ARRIVALS_ACCEPTED.csv'); H4=Path('/mnt/data/GOLD#_H4_202201030000_202608282000.csv'); OUT=Path('/mnt/data/v9_terminal_detector_20260915')
acc=pd.read_csv(ACC,parse_dates=['entry_ts','challenge_ts','hybrid_exit_ts'])
det=acc[acc.hybrid_status.isin(['SL','CHALLENGE_OPENS','NEXT_H4_LIQ'])&acc.hybrid_pnl.notna()].copy()
last=acc.sort_values('entry_ts').groupby('route_id').tail(1).set_index('route_id')
spec=importlib.util.spec_from_file_location('ha','/mnt/data/analyze_v9_terminal_ha_oracle.py');ha=importlib.util.module_from_spec(spec);spec.loader.exec_module(ha); h4=ha.build_h4_ha(H4)
known=h4.known_at.to_numpy(dtype='datetime64[ns]')
def arm_after_bars(t,n):
 j=np.searchsorted(known,np.datetime64(t),side='right')
 k=j+n-1
 return pd.Timestamp(known[k]) if k<len(known) else pd.NaT
def sig(at,direction):return ha.signal_after(h4,at,direction,1)
def met(g,p='pnl'):
 x=g.sort_values('entry_ts')[p].to_numpy(float);pos=x[x>0].sum();neg=-x[x<0].sum();eq=np.cumsum(x);pk=np.maximum.accumulate(np.r_[0,eq]);return dict(N=len(x),PnL=x.sum(),PF=pos/neg if neg else np.inf,WR=(x>0).mean(),DD=(pk[1:]-eq).max(),P95=np.quantile(x,.95),Max=x.max())
rows=[]
# base
z=det.copy();z['pnl']=z.hybrid_pnl;rows.append({'delay_bars':-1,**met(z)})
# true last immediate n=0 uses arm at last child itself
for n in [0,1,2,3,4]:
 signals={}
 for rid,r in last.iterrows():
  at=r.entry_ts if n==0 else arm_after_bars(r.entry_ts,n)
  signals[rid]=sig(at,r.direction) if pd.notna(at) else (pd.NaT,np.nan)
 vals=[]
 for r in det.itertuples():
  st,px=signals.get(r.route_id,(pd.NaT,np.nan));use=pd.notna(st) and st>r.entry_ts and st<r.hybrid_exit_ts
  vals.append(((px-r.entry) if r.direction=='UP' else (r.entry-px)) if use else r.hybrid_pnl)
 z=det.copy();z['pnl']=vals;m=met(z);m['delay_bars']=n;rows.append(m)
out=pd.DataFrame(rows);out.to_csv(OUT/'TERMINAL_HA1_DELAY_ORACLE.csv',index=False);print(out.to_string(index=False))
