#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

HEAD='da0bf0592f1d5d447f224803182dec57fcf5d8b7'
M1_SHA='626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2'


def sha256(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def metrics(df, pnl_col='pnl', sort_col='entry_ts'):
    g=df.sort_values(sort_col)
    x=g[pnl_col].astype(float).to_numpy()
    pos=x[x>0].sum(); neg=-x[x<0].sum()
    eq=np.cumsum(x); peak=np.maximum.accumulate(np.r_[0.0,eq])
    dd=float((peak[1:]-eq).max()) if len(x) else 0.0
    return {
        'N':int(len(x)), 'PnL':float(x.sum()), 'PF':float(pos/neg) if neg else float('inf'),
        'WR':float((x>0).mean()) if len(x) else float('nan'), 'Avg':float(x.mean()) if len(x) else float('nan'),
        'AvgWin':float(x[x>0].mean()) if (x>0).any() else float('nan'),
        'AvgLoss':float(x[x<0].mean()) if (x<0).any() else float('nan'),
        'DD':dd, 'Max':float(x.max()) if len(x) else float('nan'), 'Min':float(x.min()) if len(x) else float('nan')
    }


def build_h4_ha(h4_path: Path):
    h4=pd.read_csv(h4_path, sep='\t')
    h4['start']=pd.to_datetime(h4['<DATE>']+' '+h4['<TIME>'])
    for c in ['<OPEN>','<HIGH>','<LOW>','<CLOSE>']:
        h4[c]=h4[c].astype(float)
    h4['ha_close']=(h4['<OPEN>']+h4['<HIGH>']+h4['<LOW>']+h4['<CLOSE>'])/4.0
    hao=np.empty(len(h4),float)
    hao[0]=(h4.loc[0,'<OPEN>']+h4.loc[0,'<CLOSE>'])/2.0
    for i in range(1,len(h4)):
        hao[i]=(hao[i-1]+h4.loc[i-1,'ha_close'])/2.0
    h4['ha_open']=hao
    h4['ha_side']=np.where(h4.ha_close>h4.ha_open,'UP',np.where(h4.ha_close<h4.ha_open,'DOWN','DOJI'))
    h4['known_at']=h4['start']+pd.Timedelta(hours=4)
    return h4


def signal_after(h4, armed_at, direction, n):
    opp='DOWN' if direction=='UP' else 'UP'; run=0
    for _,r in h4[h4.known_at>armed_at].iterrows():
        if r.ha_side==opp:
            run += 1
            if run>=n:
                return r.known_at, float(r['<CLOSE>'])
        else:
            run=0
    return pd.NaT, np.nan


def apply_policy(df, sigs, n, scope):
    out=df.copy(); vals=[]
    for _,r in out.iterrows():
        st,px=sigs[n][int(r.route_id)]
        in_scope=(scope=='ALL_OPEN') or (scope=='ANCHOR_ONLY' and r.role=='ANCHOR_CHILD')
        use=bool(in_scope and pd.notna(st) and st>r.entry_ts and st<r.hybrid_exit_ts)
        if use:
            pnl=(px-r.entry) if r.direction=='UP' else (r.entry-px)
            vals.append((st,px,pnl,f'TERMINAL_HA{n}',True))
        else:
            vals.append((r.hybrid_exit_ts,r.hybrid_exit_price,r.hybrid_pnl,r.hybrid_status,False))
    z=pd.DataFrame(vals,index=out.index,columns=['exit_ts','exit_price','pnl','status','changed'])
    for c in z.columns: out[c]=z[c]
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--arrivals',required=True)
    ap.add_argument('--h4',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    arr_path=Path(a.arrivals); h4_path=Path(a.h4); od=Path(a.out); od.mkdir(parents=True,exist_ok=True)
    ar=pd.read_csv(arr_path,parse_dates=['entry_ts','next_ts','challenge_ts','base_exit_ts','hybrid_exit_ts'])
    det=ar[ar.hybrid_status.isin(['SL','CHALLENGE_OPENS','NEXT_H4_LIQ']) & ar.hybrid_pnl.notna()].copy()
    h4=build_h4_ha(h4_path)
    last=ar.sort_values('entry_ts').groupby('route_id').tail(1)[['route_id','entry_ts','accepted_rank','direction']].copy()
    last=last.rename(columns={'entry_ts':'terminal_oracle_armed_at','accepted_rank':'route_total_accepted'})
    last_map=last.set_index('route_id')
    sigs={1:{},2:{}}
    for route,row in last_map.iterrows():
        for n in [1,2]: sigs[n][int(route)]=signal_after(h4,row.terminal_oracle_armed_at,row.direction,n)
    policies={'BASE':det.copy()}
    policies['BASE']['exit_ts']=policies['BASE'].hybrid_exit_ts; policies['BASE']['exit_price']=policies['BASE'].hybrid_exit_price
    policies['BASE']['pnl']=policies['BASE'].hybrid_pnl; policies['BASE']['status']=policies['BASE'].hybrid_status; policies['BASE']['changed']=False
    for n in [1,2]:
        policies[f'ANCHOR_ONLY_HA{n}']=apply_policy(det,sigs,n,'ANCHOR_ONLY')
        policies[f'ALL_OPEN_HA{n}']=apply_policy(det,sigs,n,'ALL_OPEN')

    # Per-trade ledger.
    led=det[['route_id','accepted_rank','role','entry_ts','direction','entry','structural_sl','atr180','hybrid_status','hybrid_exit_ts','hybrid_exit_price','hybrid_pnl']].copy()
    led=led.merge(last,on=['route_id','direction'],how='left')
    for n in [1,2]:
        sm=pd.DataFrame([(r,)+sigs[n][int(r)] for r in last.route_id],columns=['route_id',f'HA{n}_signal_ts',f'HA{n}_signal_close'])
        led=led.merge(sm,on='route_id',how='left')
    for name,d in policies.items():
        k=name.lower()
        led[f'{k}_exit_ts']=d.exit_ts.values; led[f'{k}_exit_price']=d.exit_price.values; led[f'{k}_pnl']=d.pnl.values; led[f'{k}_status']=d.status.values; led[f'{k}_changed']=d.changed.values
    led.to_csv(od/'TERMINAL_HA_ORACLE_TRADE_LEDGER.csv',index=False)

    # Main summaries.
    rows=[]
    for name,d in policies.items():
        m=metrics(d); m['policy']=name; m['changed']=int(d.changed.sum()); rows.append(m)
    pd.DataFrame(rows).to_csv(od/'TERMINAL_HA_ORACLE_SUMMARY.csv',index=False)

    for dim in ['year','direction','role']:
        rows=[]
        for name,d0 in policies.items():
            d=d0.copy()
            if dim=='year': d['year']=d.entry_ts.dt.year
            for val,g in d.groupby(dim):
                m=metrics(g); m.update(policy=name,**{dim:val},changed=int(g.changed.sum())); rows.append(m)
        pd.DataFrame(rows).to_csv(od/f'TERMINAL_HA_ORACLE_BY_{dim.upper()}.csv',index=False)

    # Journey-level summaries based on full accepted Child count, using all deterministic resolved Children.
    rc=ar.groupby('route_id').size().rename('accepted_count')
    journey_tables=[]
    for name,d0 in policies.items():
        d=d0.merge(rc,on='route_id',how='left')
        j=d.groupby('route_id').agg(journey_start=('entry_ts','min'),direction=('direction','first'),accepted_count=('accepted_count','first'),resolved_children=('pnl','size'),journey_pnl=('pnl','sum')).reset_index()
        j['journey_type']=np.where(j.accepted_count.eq(1),'SINGLE','MULTI')
        j['year']=j.journey_start.dt.year; j['policy']=name
        j['child_bucket']=np.where(j.accepted_count>=4,'4+',j.accepted_count.astype(str))
        journey_tables.append(j)
    journeys=pd.concat(journey_tables,ignore_index=True); journeys.to_csv(od/'TERMINAL_HA_ORACLE_JOURNEY_LEDGER.csv',index=False)

    rows=[]
    for (name,typ),g in journeys.groupby(['policy','journey_type']):
        gg=g.rename(columns={'journey_start':'entry_ts','journey_pnl':'pnl'}); m=metrics(gg); m.update(policy=name,journey_type=typ); rows.append(m)
    pd.DataFrame(rows).to_csv(od/'TERMINAL_HA_ORACLE_BY_JOURNEY_TYPE.csv',index=False)
    rows=[]
    for (name,b),g in journeys.groupby(['policy','child_bucket']):
        gg=g.rename(columns={'journey_start':'entry_ts','journey_pnl':'pnl'}); m=metrics(gg); m.update(policy=name,child_bucket=b); rows.append(m)
    pd.DataFrame(rows).to_csv(od/'TERMINAL_HA_ORACLE_BY_CHILD_COUNT.csv',index=False)

    manifest={
      'source_main_head':HEAD,
      'arrivals_accepted_sha256':sha256(arr_path),
      'h4_sha256':sha256(h4_path),
      'authoritative_m1_sha256':M1_SHA,
      'status':'CONSUMED-DATA HINDSIGHT ORACLE / UPPER BOUND ONLY / NOT STRATEGY AUTHORITY',
      'base_population':'1139 deterministic role-based resolved Children from 1250 accepted Children',
      'terminal_oracle':'true last accepted Child in each route, known only with hindsight',
      'HA1':'after oracle arm time, first completed opposite-color H4 Heikin-Ashi candle; close at that source H4 close if before existing role exit',
      'HA2':'after oracle arm time, second consecutive completed opposite-color H4 Heikin-Ashi candle; same exit convention',
      'ALL_OPEN':'HA event closes every still-open deterministic Child in the route; existing role exit wins if earlier',
      'ANCHOR_ONLY':'same HA event only replaces Anchor exit; Continuation remains current NEXT_H4_LIQ/SL policy',
      'hard_sl':'existing role-based structural SL/base exit remains authoritative whenever earlier than HA close',
      'execution_caveat':'gross M1/H4 close-price screening; HA-close execution has not been revalidated with MT5 actual ticks/Bid-Ask',
      'no_authority_change':True
    }
    (od/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(pd.read_csv(od/'TERMINAL_HA_ORACLE_SUMMARY.csv').to_string(index=False))

if __name__=='__main__': main()
