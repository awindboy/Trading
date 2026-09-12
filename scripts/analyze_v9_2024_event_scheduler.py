#!/usr/bin/env python3
"""2024 consumed-data feasibility study for deterministic AI wake events.

Research only. Events created here are AI review triggers, never automatic
entry/exit/BE/trailing/TP authority.

Inputs:
  --trades      enriched 2024 trade ledger from the 2024 postmortem bundle
  --decisions   2024 AI decision log
  --m1          2024 authoritative BID M1 subset
  --out-dir     output directory

R-event eligibility/count uses tick-derived MFE_R already frozen in the trade
ledger. M1 is used only to obtain minute-level proxy timestamps for batching and
latency diagnostics; for short positions the exact favorable execution quote is
ASK and can occur later inside that minute. No execution result is recomputed
from this proxy.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

VERSION='v9-event-driven-ai-scheduler-feasibility-1'

def load_m1(path: Path) -> pd.DataFrame:
    d=pd.read_csv(path,sep='\t',usecols=['<DATE>','<TIME>','<HIGH>','<LOW>'])
    d['dt']=pd.to_datetime(d['<DATE>']+' '+d['<TIME>'],format='%Y.%m.%d %H:%M:%S')
    return d[['dt','<HIGH>','<LOW>']].sort_values('dt').reset_index(drop=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--trades',required=True)
    ap.add_argument('--decisions',required=True)
    ap.add_argument('--m1',required=True)
    ap.add_argument('--out-dir',required=True)
    a=ap.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)

    tr=pd.read_csv(a.trades)
    tr=tr[(~tr.censored.astype(bool)) & tr.exit_at.notna()].copy()
    tr['entry_dt']=pd.to_datetime(tr.entry_at,format='mixed')
    tr['exit_dt']=pd.to_datetime(tr.exit_at,format='mixed')
    tr['giveback']=(tr.terminal_reason=='HARD_SL')&(tr.mfe_r>=1)
    tr['winner']=tr.realized_r>0
    tr['hard_sl']=tr.terminal_reason=='HARD_SL'
    tr['r_event_count']=np.floor(tr.mfe_r.clip(lower=0)).astype(int)
    m1=load_m1(Path(a.m1))

    # M1 proxy times for each positive integer-R first crossing. Eligibility is
    # determined by exact tick-derived MFE_R, not by the proxy M1 price.
    rrows=[]
    for _,r in tr[tr.mfe_r>=1].iterrows():
        seg=m1[(m1.dt>=r.entry_dt.floor('min'))&(m1.dt<=r.exit_dt.floor('min'))]
        for k in range(1,int(np.floor(r.mfe_r+1e-12))+1):
            thr=r.entry_price+k*r.initial_risk if r.side=='UP' else r.entry_price-k*r.initial_risk
            hit=seg[seg['<HIGH>']>=thr] if r.side=='UP' else seg[seg['<LOW>']<=thr]
            t=hit.dt.iloc[0] if len(hit) else pd.NaT
            rrows.append({'child_id':r.child_id,'k':k,'threshold':thr,'proxy_at':t})
    rp=pd.DataFrame(rrows)
    rp.to_csv(out/'V9_2024_R_MILESTONE_M1_PROXY_20260913.csv',index=False)

    decisions=json.load(open(a.decisions,encoding='utf-8'))
    review_by={}
    for z in decisions:
        cid=z.get('child_id')
        if cid and z.get('kind') in ('REVIEW_REQUIRED','REMAP_REQUIRED'):
            review_by.setdefault(cid,[]).append(pd.Timestamp(z['at']))

    events=[]
    for _,r in tr.iterrows():
        for t in review_by.get(r.child_id,[]):
            events.append({'child_id':r.child_id,'at':t,'event':'EXISTING_STRUCTURAL_REVIEW','source':'exact_gate'})
        if pd.notna(r.first_favorable_delivery_at):
            events.append({'child_id':r.child_id,'at':pd.Timestamp(r.first_favorable_delivery_at),'event':'FIRST_FAVORABLE_DELIVERY','source':'object_engine'})
        if pd.notna(r.first_post_delivery_m15_nonsupport_at):
            events.append({'child_id':r.child_id,'at':pd.Timestamp(r.first_post_delivery_m15_nonsupport_at),'event':'POST_DELIVERY_M15_NONSUPPORT','source':'completed_M15'})
    for _,z in rp.iterrows():
        if pd.notna(z.proxy_at):
            events.append({'child_id':z.child_id,'at':pd.Timestamp(z.proxy_at),'event':f'R_MILESTONE_{int(z.k)}','source':'M1_proxy_time_tick_MFE_eligibility'})
    ev=pd.DataFrame(events)
    ev['at']=pd.to_datetime(ev['at'],format='mixed')
    ev['minute']=ev['at'].dt.floor('min')
    ev.to_csv(out/'V9_2024_EVENT_SCHEDULER_EVENT_LEDGER_20260913.csv',index=False)

    scenarios={
      'CURRENT_EXISTING_ONLY':['EXISTING_STRUCTURAL_REVIEW'],
      'R_MILESTONES_ONLY':['R_MILESTONE_'],
      'FIRST_DELIVERY_ONLY':['FIRST_FAVORABLE_DELIVERY'],
      'POST_DELIVERY_M15_NONSUPPORT_ONLY':['POST_DELIVERY_M15_NONSUPPORT'],
      'PROPOSED_MINIMAL':['EXISTING_STRUCTURAL_REVIEW','R_MILESTONE_','FIRST_FAVORABLE_DELIVERY','POST_DELIVERY_M15_NONSUPPORT'],
    }
    rows=[]
    for name,fams in scenarios.items():
        def match(s): return any(s==f or (f.endswith('_') and s.startswith(f)) for f in fams)
        e=ev[ev.event.map(match)]
        b=e.groupby(['child_id','minute']).agg(reasons=('event',lambda x:'|'.join(sorted(set(x))))).reset_index()
        called=set(b.child_id); give=tr[tr.giveback]; wins=tr[tr.winner]; hard=tr[tr.hard_sl]
        rows.append({
          'scenario':name,'raw_event_reasons':len(e),'batched_management_calls':len(b),'called_trades':len(called),
          'giveback_1Rplus_hardsl_total':len(give),'giveback_trades_with_review_opportunity':int(give.child_id.isin(called).sum()),
          'giveback_coverage':float(give.child_id.isin(called).mean()),'winner_trades_called':int(wins.child_id.isin(called).sum()),
          'hard_sl_trades_called':int(hard.child_id.isin(called).sum()),'entry_ai_calls_if_every_filled_entry':len(tr),
          'total_calls_including_entry':len(b)+len(tr),'calls_per_252day_proxy':(len(b)+len(tr))/252,
        })
    sc=pd.DataFrame(rows); sc.to_csv(out/'V9_2024_EVENT_SCHEDULER_SCENARIOS_20260913.csv',index=False)

    fam=[]
    for label,pred in [
      ('EXISTING_STRUCTURAL_REVIEW',lambda s:s=='EXISTING_STRUCTURAL_REVIEW'),
      ('R_MILESTONE_ALL',lambda s:s.startswith('R_MILESTONE_')),
      ('FIRST_FAVORABLE_DELIVERY',lambda s:s=='FIRST_FAVORABLE_DELIVERY'),
      ('POST_DELIVERY_M15_NONSUPPORT',lambda s:s=='POST_DELIVERY_M15_NONSUPPORT')]:
        e=ev[ev.event.map(pred)]; b=e.groupby(['child_id','minute']).size().reset_index(); called=set(b.child_id)
        fam.append({'family':label,'events':len(e),'batched_calls':len(b),'trades_called':len(called),
                    'giveback_coverage_n':int(tr[tr.giveback].child_id.isin(called).sum()),
                    'giveback_coverage_rate':float(tr[tr.giveback].child_id.isin(called).mean()),
                    'winner_trades_called':int(tr[tr.winner].child_id.isin(called).sum())})
    pd.DataFrame(fam).to_csv(out/'V9_2024_EVENT_FAMILY_COVERAGE_20260913.csv',index=False)

    proposed=ev.groupby(['child_id','minute']).agg(reasons=('event',lambda x:'|'.join(sorted(set(x))))).reset_index()
    cc=proposed.groupby('child_id').size().rename('management_calls').reset_index()
    top=tr.sort_values('realized_r',ascending=False).head(20).merge(cc,on='child_id',how='left')
    top.to_csv(out/'V9_2024_EVENT_SCHEDULER_TOP_WINNERS_20260913.csv',index=False)
    give=tr[tr.giveback].merge(cc,on='child_id',how='left')
    first=proposed.sort_values('minute').groupby('child_id').first().reset_index()[['child_id','minute','reasons']]
    first=first.rename(columns={'minute':'first_sched_review_at','reasons':'first_sched_reasons'})
    give=give.merge(first,on='child_id',how='left')
    give['minutes_first_review_to_exit']=(give.exit_dt-give.first_sched_review_at).dt.total_seconds()/60
    give.to_csv(out/'V9_2024_EVENT_SCHEDULER_GIVEBACKS_20260913.csv',index=False)

    # Demonstrate why events are wakeups rather than automatic actions.
    base=float(tr.realized_r.sum()); fixed={}
    for k in (1,2,3):
        hit=tr.mfe_r>=k; cf=np.where(hit,k,tr.realized_r)
        fixed[f'{k}R']={'hit_trades':int(hit.sum()),'counterfactual_total_r':float(cf.sum()),'delta_vs_actual':float(cf.sum()-base)}
    cfr=pd.to_numeric(tr.counterfactual_r_at_first_post_delivery_m15_nonsupport,errors='coerce'); mask=cfr.notna()
    winmask=mask & (tr.realized_r>0); lossmask=mask & (tr.realized_r<0)
    auto={'actual_total_r':base,'fixed_tp_counterfactuals':fixed,
      'post_delivery_m15_nonsupport_auto_exit':{
       'event_trades':int(mask.sum()),'actual_sum_r_on_event_trades':float(tr.loc[mask,'realized_r'].sum()),
       'auto_exit_counterfactual_sum_r':float(cfr[mask].sum()),'delta':float(cfr[mask].sum()-tr.loc[mask,'realized_r'].sum()),
       'winner_event_trades':int(winmask.sum()),'winner_actual_sum_r':float(tr.loc[winmask,'realized_r'].sum()),
       'winner_auto_exit_counterfactual_sum_r':float(cfr[winmask].sum()),
       'loss_event_trades':int(lossmask.sum()),'loss_actual_sum_r':float(tr.loc[lossmask,'realized_r'].sum()),
       'loss_auto_exit_counterfactual_sum_r':float(cfr[lossmask].sum())}}
    (out/'V9_2024_EVENT_SCHEDULER_AUTO_EXIT_COUNTERFACTUALS_20260913.json').write_text(json.dumps(auto,indent=2),encoding='utf-8')

    fast=(tr.hard_sl)&(tr.mfe_r<0.25)&(pd.to_numeric(tr.duration_minutes,errors='coerce')<=60)
    called=set(proposed.child_id)
    summary={'version':VERSION,'scope':'2024 consumed postmortem; scheduler feasibility only; no new trade action authority',
      'closed_trades':len(tr),'fast_no_progress_hard_sl':int(fast.sum()),'fast_no_progress_with_management_event':int(tr.loc[fast,'child_id'].isin(called).sum()),
      'giveback_1Rplus_hardsl':int(tr.giveback.sum()),'r_milestone_reasons':int(tr.r_event_count.sum()),
      'all_favorable_liquidity_deliveries':int(tr.favorable_liquidity_delivery_count.sum()),
      'proposed_minimal_batched_management_calls':int(sc.loc[sc.scenario=='PROPOSED_MINIMAL','batched_management_calls'].iloc[0]),
      'proposed_total_including_filled_entry_lower_bound':int(sc.loc[sc.scenario=='PROPOSED_MINIMAL','total_calls_including_entry'].iloc[0]),
      'proposed_calls_per_252day_proxy':float(sc.loc[sc.scenario=='PROPOSED_MINIMAL','calls_per_252day_proxy'].iloc[0]),
      'giveback_first_review_lead_minutes':give.minutes_first_review_to_exit.describe().to_dict(),
      'notes':['filled-entry count is a lower bound for future candidate-level entry AI calls','same-child same-minute reasons are coalesced','an in-flight AI request should coalesce later non-Hard-SL reasons rather than spawn parallel calls','Hard SL remains independent']}
    (out/'V9_2024_EVENT_SCHEDULER_SUMMARY_20260913.json').write_text(json.dumps(summary,indent=2,default=float),encoding='utf-8')
    print(json.dumps(summary,indent=2,default=float))

if __name__=='__main__': main()
