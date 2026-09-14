\
#!/usr/bin/env python3
from pathlib import Path
import argparse, math, pandas as pd, numpy as np

def run(events,trades,start_date,risk,start_balance):
    ev=pd.read_csv(events); ev['dt']=pd.to_datetime(ev.tick_time)
    tr=pd.read_csv(trades); tm=tr.set_index('child_id').to_dict('index')
    ent=ev[ev.event=='CHILD_ENTRY']
    allowed=None if not start_date else set(ent.loc[ent.dt>=pd.Timestamp(start_date),'child_id'].astype(int))
    rel=ev[ev.event.isin(['CHILD_ENTRY','CHILD_EXIT','CHILD_EXIT_RETRY_OK'])]
    if allowed is not None: rel=rel[rel.child_id.astype(int).isin(allowed)]
    bal=float(start_balance); op={}; maxb=bal; minb=bal; maxdd=0.; rows=[]
    for _,r in rel.iterrows():
        cid=int(r.child_id)
        if r.event=='CHILD_ENTRY':
            bid=float(r.bid); ask=float(r.ask); floating=sum(((bid-p['entry']) if p['dir']=='UP' else (p['entry']-ask))*p['units'] for p in op.values()); eq=bal+floating
            entry=float(r.actual_price); sl=float(r.structural_sl); r0=abs(entry-sl); units=max(1,math.floor((eq*risk+1e-12)/r0)); d='UP' if r.primary=='UP' else 'DOWN'; planned=r0*units
            op[cid]={'entry':entry,'dir':d,'units':units,'eq':eq,'planned':planned}; rows.append(dict(child_id=cid,event='entry',time=r.dt,balance=bal,equity=eq,volume=units*.01,planned_risk=planned,planned_risk_pct=planned/eq,n_open=len(op)))
        elif cid in op:
            p=op.pop(cid); pnl=float(tm[cid]['calc_profit'])*p['units']; bal+=pnl; maxb=max(maxb,bal); minb=min(minb,bal); maxdd=max(maxdd,(maxb-bal)/maxb); rows.append(dict(child_id=cid,event='exit',time=r.dt,balance=bal,equity=np.nan,volume=p['units']*.01,pnl=pnl,n_open=len(op)))
    return pd.DataFrame(rows),dict(end_balance=bal,max_balance=maxb,min_balance=minb,max_balance_dd=maxdd,open_count=len(op))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--events',required=True); ap.add_argument('--trades',required=True); ap.add_argument('--start-date'); ap.add_argument('--risk',type=float,required=True); ap.add_argument('--start-balance',type=float,default=1000); ap.add_argument('--out',required=True); a=ap.parse_args()
    led,s=run(a.events,a.trades,a.start_date,a.risk,a.start_balance); Path(a.out).parent.mkdir(parents=True,exist_ok=True); led.to_csv(a.out,index=False); print(s)
if __name__=='__main__': main()
