#!/usr/bin/env python3
from __future__ import annotations
import argparse, io, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

POINT=0.01

def met(rr):
    rr=pd.Series(rr).dropna().astype(float)
    p=rr[rr>0]; n=rr[rr<0]; eq=rr.cumsum()
    return dict(resolved=len(rr),wr=(len(p)/len(rr) if len(rr) else np.nan),total_R=float(rr.sum()),mean_R=float(rr.mean()) if len(rr) else np.nan,
                PF=(float(p.sum()/abs(n.sum())) if len(n) else np.inf),maxDD=(float((eq.cummax()-eq).max()) if len(eq) else np.nan),
                avg_win_R=(float(p.mean()) if len(p) else np.nan),avg_loss_R=(float(n.mean()) if len(n) else np.nan),
                payoff=(float(p.mean()/abs(n.mean())) if len(p) and len(n) else np.nan))

SOURCE_RANGES = {
    '2024': (43348274, 65173328),
    '2025H1': (65173328, 75912993),
    '2026JF': (86972434, 90428045),
}

def _read_source_range(source_m1, start_offset, end_offset):
    with open(source_m1,'rb') as f:
        f.seek(start_offset); raw=f.read(end_offset-start_offset)
    cols=['date','time','open','high','low','close','tickvol','vol','spread']
    x=pd.read_csv(io.StringIO(raw.decode('utf-8')),sep='\t',header=None,names=cols)
    return pd.DataFrame({
        'ts':pd.to_datetime(x.date+' '+x.time,format='%Y.%m.%d %H:%M:%S'),
        'spread_points':x.spread.astype(float),
    })

def load_spread(source_m1):
    frames=[_read_source_range(source_m1,*SOURCE_RANGES[b]) for b in ['2024','2025H1','2026JF']]
    return pd.concat(frames,ignore_index=True).drop_duplicates('ts').set_index('ts').sort_index()

def onepos_cost(df, spreads, rcol='R', exitcol='exit_ts', mult=1.0):
    z=df.copy(); z['entry_ts']=pd.to_datetime(z.entry_ts); z[exitcol]=pd.to_datetime(z[exitcol],errors='coerce')
    z['entry_spread']=z.entry_ts.map(spreads.spread_points)*POINT
    z['exit_spread']=z[exitcol].map(spreads.spread_points)*POINT
    z['spread_cost_price']=np.where(z.direction.eq('UP'),z.entry_spread,z.exit_spread)
    z['spread_cost_R']=mult*z.spread_cost_price/z.sl_dist
    z['R_net']=z[rcol]-z.spread_cost_R
    return z

def replace_policy(ind, block_end):
    out=[]
    for block,g in ind.groupby('block'):
        cur=None; end=block_end[block]
        for rec in g.sort_values('entry_ts').to_dict('records'):
            t=rec['entry_ts']; skip=False
            if cur is not None:
                term=cur['exit_ts'] if pd.notna(cur['exit_ts']) else end
                if term<t:
                    out.append({**cur,'managed_status':cur['status'],'managed_exit_ts':term,'managed_R':cur['R'],'reason':'BASELINE_RESOLUTION'}); cur=None
                elif term==t:
                    out.append({**cur,'managed_status':cur['status'],'managed_exit_ts':term,'managed_R':cur['R'],'reason':'SAME_TIME_BASELINE_PRIORITY'}); cur=None; skip=True
            if skip: continue
            if cur is None: cur=rec.copy()
            else:
                sign=1 if cur['direction']=='UP' else -1; risk=abs(cur['entry']-cur['sl'])
                out.append({**cur,'managed_status':'REPLACED','managed_exit_ts':t,'managed_R':sign*(rec['entry']-cur['entry'])/risk,'reason':'NEW_ACTIVE_ARRIVAL'}); cur=rec.copy()
        if cur is not None:
            term=cur['exit_ts'] if pd.notna(cur['exit_ts']) else end
            out.append({**cur,'managed_status':cur['status'],'managed_exit_ts':term,'managed_R':cur['R'],'reason':'BASELINE_RESOLUTION'})
    return pd.DataFrame(out)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--results',type=Path,required=True); ap.add_argument('--source-m1',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    jour=pd.read_csv(a.results/'V9_JOURNEY_LEDGER_2024_2025H1_2026JF.csv'); one=pd.read_csv(a.results/'V9_JOURNEY_ONE_POSITION_LEDGER_2024_2025H1_2026JF.csv'); arr=pd.read_csv(a.results/'V9_ARRIVAL_LEDGER_2024_2025H1_2026JF.csv')
    for d in [jour,one]: d['entry_ts']=pd.to_datetime(d.entry_ts); d['exit_ts']=pd.to_datetime(d.exit_ts,errors='coerce')
    arr['ts']=pd.to_datetime(arr.ts)
    # H1 structural audit
    h=jour[(jour.universe=='CONTROL')&(jour.sl_arm=='H1_STRUCT')&(jour.policy=='CHALLENGE_EXIT')]
    audit=h.groupby('block').agg(opportunities=('entry_ts','size'),valid_sl=('sl',lambda x:x.notna().sum()),median_sl=('sl_dist','median'),mean_sl=('sl_dist','mean'),p10_sl=('sl_dist',lambda x:x.dropna().quantile(.1)),p90_sl=('sl_dist',lambda x:x.dropna().quantile(.9))).reset_index()
    audit.to_csv(a.out/'V9_H1_STRUCTURAL_SL_AUDIT.csv',index=False)
    # Challenge topology resolver
    rows=[]
    for idx,r in arr[arr.resolution=='CHALLENGE_OPENS'].iterrows():
        nxt=arr[(arr.block==r.block)&(arr.ts>r.ts)].sort_values('ts').head(1); outcome=(nxt.iloc[0].resolution if len(nxt) else None)
        if r.primary=='UP': d_old=(r.nearest_bsl-r.ref) if pd.notna(r.nearest_bsl) else np.nan; d_ch=(r.ref-r.nearest_ssl) if pd.notna(r.nearest_ssl) else np.nan
        else: d_old=(r.ref-r.nearest_ssl) if pd.notna(r.nearest_ssl) else np.nan; d_ch=(r.nearest_bsl-r.ref) if pd.notna(r.nearest_bsl) else np.nan
        if pd.isna(d_old) and pd.isna(d_ch): topo='BOTH_MISSING'
        elif pd.isna(d_old): topo='NO_OLD_TARGET'
        elif pd.isna(d_ch): topo='NO_CHALLENGER_TARGET'
        elif d_old<d_ch: topo='OLD_NEAREST'
        else: topo='CHALLENGER_NEAREST'
        pred='OLD_PRIMARY_WINS' if topo=='OLD_NEAREST' else ('CHALLENGER_EARNED' if topo=='CHALLENGER_NEAREST' else None)
        rows.append(dict(block=r.block,challenge_ts=r.ts,old_primary=r.primary,challenger=r.arrival_side,d_old=d_old,d_challenger=d_ch,challenge_topology=topo,outcome=outcome,prediction=pred,correct=(pred==outcome if pred else np.nan)))
    cr=pd.DataFrame(rows); cr.to_csv(a.out/'V9_CHALLENGE_TOPOLOGY_RESOLVER_LEDGER.csv',index=False)
    crs=[]
    for block,g in cr.groupby('block'):
        q=g[g.prediction.notna() & g.outcome.isin(['OLD_PRIMARY_WINS','CHALLENGER_EARNED'])]
        crs.append(dict(block=block,episodes=len(g),usable=len(q),accuracy=(q.correct.mean() if len(q) else np.nan)))
    q=cr[cr.prediction.notna() & cr.outcome.isin(['OLD_PRIMARY_WINS','CHALLENGER_EARNED'])]; crs.append(dict(block='COMBINED',episodes=len(cr),usable=len(q),accuracy=(q.correct.mean() if len(q) else np.nan)))
    pd.DataFrame(crs).to_csv(a.out/'V9_CHALLENGE_TOPOLOGY_RESOLVER_SUMMARY.csv',index=False)
    # fixed-entry challenge partial/full common cohort from one-position challenge-selected entries
    op=one[(one.universe=='CONTROL')&(one.sl_arm=='H1_STRUCT')&(one.policy=='CHALLENGE_EXIT')][['block','entry_ts']]
    c=jour[(jour.universe=='CONTROL')&(jour.sl_arm=='H1_STRUCT')&(jour.policy=='CHALLENGE_EXIT')][['block','entry_ts','R']].rename(columns={'R':'R_ch'})
    f=jour[(jour.universe=='CONTROL')&(jour.sl_arm=='H1_STRUCT')&(jour.policy=='FLIP_EXIT')][['block','entry_ts','R']].rename(columns={'R':'R_flip'})
    x=op.merge(c,on=['block','entry_ts']).merge(f,on=['block','entry_ts']); x=x[x.R_ch.notna()&x.R_flip.notna()]
    out=[]
    for frac in [1,.75,.5,.25,0]:
        for block,g in list(x.groupby('block'))+[('COMBINED',x)]:
            d=met(frac*g.R_ch+(1-frac)*g.R_flip); d.update(block=block,challenge_exit_fraction=frac,hold_to_flip_fraction=1-frac); out.append(d)
    pd.DataFrame(out).to_csv(a.out/'V9_CHALLENGE_ACTION_COMMON_COHORT.csv',index=False)
    # exposure overlap and concurrency
    ind=jour[(jour.universe=='CONTROL')&(jour.sl_arm=='H1_STRUCT')&(jour.policy=='CHALLENGE_EXIT')&(jour.status!='NO_VALID_SL')].copy().sort_values(['block','entry_ts'])
    bend={'2024':pd.Timestamp('2024-12-31 23:59:59'),'2025H1':pd.Timestamp('2025-06-30 23:59:59'),'2026JF':pd.Timestamp('2026-02-28 23:59:59')}
    ind['term_ts']=ind.apply(lambda r:r.exit_ts if pd.notna(r.exit_ts) else bend[r.block],axis=1)
    conc=[]
    for i,r in ind.iterrows(): conc.append(len(ind[(ind.block==r.block)&(ind.entry_ts<r.entry_ts)&(ind.term_ts>=r.entry_ts)]))
    ind['existing_children_at_entry']=conc; ind['concurrency_bucket']=ind.existing_children_at_entry.map(lambda n:str(n) if n<=2 else '3+')
    ind.to_csv(a.out/'V9_EXPOSURE_OVERLAP_LEDGER.csv',index=False)
    es=[]
    for block,g in ind.groupby('block'):
        ev=[]
        for _,r in g.iterrows(): ev += [(r.entry_ts,1),(r.term_ts+pd.Timedelta(nanoseconds=1),-1)]
        ev.sort(); cc=0; mx=0
        for _,d in ev: cc+=d; mx=max(mx,cc)
        es.append(dict(block=block,entries=len(g),max_concurrent=mx,pct_entry_while_child_open=float((g.existing_children_at_entry>0).mean()),median_existing=float(g.existing_children_at_entry.median()),p95_existing=float(g.existing_children_at_entry.quantile(.95))))
    pd.DataFrame(es).to_csv(a.out/'V9_EXPOSURE_OVERLAP_SUMMARY.csv',index=False)
    # replacement policy and policy summary
    rep=replace_policy(ind,bend); rep.to_csv(a.out/'V9_REPLACE_CHILD_LEDGER.csv',index=False)
    ps=[]
    onecore=one[(one.universe=='CONTROL')&(one.sl_arm=='H1_STRUCT')&(one.policy=='CHALLENGE_EXIT')].copy()
    for pname,df,col in [('ONE_POSITION',onecore,'R'),('REPLACE',rep,'managed_R'),('FULL_STACK',ind,'R')]:
        for block,g in list(df.groupby('block'))+[('COMBINED',df)]:
            d=met(g[col]); d.update(block=block,policy=pname,records=len(g)); ps.append(d)
    pd.DataFrame(ps).to_csv(a.out/'V9_EXPOSURE_POLICY_SUMMARY_GROSS.csv',index=False)
    # cost sensitivity
    spreads=load_spread(a.source_m1)
    cost=[]
    for pname,df,rcol,exitcol in [('ONE_POSITION',onecore,'R','exit_ts'),('REPLACE',rep,'managed_R','managed_exit_ts')]:
        for mult in [0,1,2,3]:
            z=onepos_cost(df,spreads,rcol,exitcol,mult)
            for block,g in list(z.groupby('block'))+[('COMBINED',z)]:
                d=met(g.R_net); d.update(block=block,policy=pname,observed_spread_multiple=mult,records=len(g)); cost.append(d)
    pd.DataFrame(cost).to_csv(a.out/'V9_COST_SENSITIVITY.csv',index=False)
    # monthly at 1x spread
    mon=[]
    for pname,df,rcol,exitcol in [('ONE_POSITION',onecore,'R','exit_ts'),('REPLACE',rep,'managed_R','managed_exit_ts')]:
        z=onepos_cost(df,spreads,rcol,exitcol,1); z['month']=z.entry_ts.dt.to_period('M').astype(str)
        for (block,month),g in z.groupby(['block','month']):
            d=met(g.R_net);d.update(block=block,month=month,policy=pname);mon.append(d)
    pd.DataFrame(mon).to_csv(a.out/'V9_COST_MONTHLY_1X_SPREAD.csv',index=False)
    # simple report
    report={'h1_structural_coverage':{'valid':int(audit.valid_sl.sum()),'opportunities':int(audit.opportunities.sum())},
            'challenge_topology_combined_accuracy':float(pd.DataFrame(crs).query("block=='COMBINED'").accuracy.iloc[0]),
            'replace_records':len(rep)}
    (a.out/'V9_POST_TOPOLOGY_STUDY_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__': main()
