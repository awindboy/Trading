#!/usr/bin/env python3
"""Build a chronological Atlas event ledger from state and exact-landmark ledgers."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def in_scope(block: str, t: pd.Timestamp) -> bool:
    if block == "2025H1":
        return pd.Timestamp("2025-01-01") <= t < pd.Timestamp("2025-07-01")
    if block == "2026JF":
        return pd.Timestamp("2026-01-01") <= t < pd.Timestamp("2026-03-01")
    return False


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--dir",required=True)
    ap.add_argument("--poi",required=True)
    ap.add_argument("--liquidity",required=True)
    args=ap.parse_args()
    root=Path(args.dir)

    h1=pd.read_csv(root/'CONTINUOUS_H1_NESTED_STATE_LEDGER.csv',parse_dates=['known_at'])
    runs=pd.read_csv(root/'CONTINUOUS_H4_FLOW_RUN_LEDGER.csv',parse_dates=['start'])
    cycles=pd.read_csv(root/'H1_AUCTION_INTERRUPTION_LEDGER.csv',parse_dates=['start','resolution'])
    poi=pd.read_csv(args.poi,parse_dates=['touch_hour'])
    liq=pd.read_csv(args.liquidity,parse_dates=['event_time'])

    # Strict landmark snapshots for reproducibility.
    poi=poi[[in_scope(b,t) for b,t in zip(poi.block,poi.touch_hour)]].copy()
    liq=liq[[in_scope(b,t) for b,t in zip(liq.block,liq.event_time)]].copy()
    poi.to_csv(root/'POI_INTERACTION_CLUSTER_STUDY_STRICT.csv',index=False)
    liq.to_csv(root/'LIQUIDITY_DELIVERY_CLUSTER_STUDY_STRICT.csv',index=False)

    rows=[]
    # Helper to attach latest known H1/H4 state at event time.
    def state_at(block,t):
        z=h1[(h1.block==block)&(h1.known_at<=t)].sort_values('known_at')
        if z.empty:
            return (None,None,None,None)
        r=z.iloc[-1]
        return (r.get('macro_state_majority'),r.get('flow_state'),r.get('h1_vs_h4_relation'),r.get('h1_state_consensus'))

    for _,r in runs.iterrows():
        t=pd.Timestamp(r.start)
        if not in_scope(r.block,t): continue
        H,F,R,L=state_at(r.block,t)
        rows.append(dict(block=r.block,event_time=t,event_type='H4_STATE_START',event_id='',direction='',price_low=np.nan,price_high=np.nan,object_ids='',h4_macro=H,h4_flow_state=r.state,h1_relation=R,h1_state=L,detail=f"hours={r.hours}"))

    for _,r in cycles.iterrows():
        for et,t,detail in [
            ('H1_INTERRUPT_START',pd.Timestamp(r.start),f"h4_side={r.h4_side}; path={r.path}"),
            ('H1_INTERRUPT_RESOLUTION',pd.Timestamp(r.resolution),f"outcome={r.outcome}; bars={r.h1_bars_to_resolution}"),
        ]:
            if not in_scope(r.block,t): continue
            H,F,R,L=state_at(r.block,t)
            rows.append(dict(block=r.block,event_time=t,event_type=et,event_id=r.h1_cycle_id,direction=r.h4_side,price_low=np.nan,price_high=np.nan,object_ids='',h4_macro=H,h4_flow_state=F,h1_relation=R,h1_state=L,detail=detail))

    for _,r in poi.iterrows():
        t=pd.Timestamp(r.touch_hour); H,F,R,L=state_at(r.block,t)
        rows.append(dict(block=r.block,event_time=t,event_type='POI_CLUSTER_TOUCH',event_id=r.cluster_id,direction=r.direction,price_low=r.price_low,price_high=r.price_high,object_ids=r.object_ids,h4_macro=H,h4_flow_state=F,h1_relation=R,h1_state=L,detail=f"families={r.families}; timeframes={r.timeframes}; objects={r.object_count}"))

    for _,r in liq.iterrows():
        t=pd.Timestamp(r.event_time); H,F,R,L=state_at(r.block,t)
        rows.append(dict(block=r.block,event_time=t,event_type='LIQUIDITY_DELIVERY',event_id=r.cluster_id,direction=r.direction,price_low=r.price_min,price_high=r.price_max,object_ids=r.object_ids,h4_macro=H,h4_flow_state=F,h1_relation=R,h1_state=L,detail=f"objects={r.object_count}; H4_present={r.H4_object_present}"))

    out=pd.DataFrame(rows).sort_values(['block','event_time','event_type','event_id']).reset_index(drop=True)
    out.to_csv(root/'MARKET_FLOW_EVENT_LEDGER.csv',index=False)
    print(f"events={len(out)}, poi={len(poi)}, liquidity={len(liq)}")

if __name__=='__main__':
    main()
