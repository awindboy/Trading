\
#!/usr/bin/env python3
from pathlib import Path
import argparse, pandas as pd, numpy as np

def metric(g):
    p=g.loc[g.pnl>0,'pnl'].sum(); n=-g.loc[g.pnl<0,'pnl'].sum()
    return dict(trades=len(g),wins=int((g.pnl>0).sum()),losses=int((g.pnl<0).sum()),win_rate=float((g.pnl>0).mean()),pnl=float(g.pnl.sum()),pf=float(p/n) if n else np.inf)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--trades',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    t=pd.read_csv(a.trades); t['entry_dt']=pd.to_datetime(t.entry_time); t['exit_dt']=pd.to_datetime(t.exit_time); t['pnl']=t.calc_profit.astype(float); t['sl_dist_actual']=(t.actual_entry-t.structural_sl).abs(); t['hold_hours']=(t.exit_dt-t.entry_dt).dt.total_seconds()/3600
    rows=[]
    for y,g in t.groupby(t.entry_dt.dt.year): rows.append({'slice':'year','key':str(y),**metric(g)})
    for k,g in t.groupby('role'): rows.append({'slice':'role','key':k,**metric(g)})
    for k,g in t.groupby('direction'): rows.append({'slice':'direction','key':k,**metric(g)})
    for k,g in t.groupby('exit_reason'): rows.append({'slice':'exit_reason','key':k,**metric(g)})
    pd.DataFrame(rows).to_csv(out/'V9_R0_ACTUAL_TICK_SUMMARY.csv',index=False)
    print(metric(t))
if __name__=='__main__': main()
