#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,re,json
from pathlib import Path
from datetime import datetime,timedelta
from collections import defaultdict

DT='%Y.%m.%d %H:%M:%S'

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(path,rows,fields=None):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0]) if rows else []
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def dt(s): return datetime.strptime(s,DT)
def b(v): return str(v).lower() in ('1','true','yes')
def fv(v,default=0.0):
    try:return float(v)
    except:return default

def build_reject_ledgers(events,signals,out):
    raw=[]
    per_time=defaultdict(list)
    seq=defaultdict(int)
    for i,r in enumerate(events):
        if r.get('event')!='FAST_NHA_EXIT_REJECT':continue
        t=r['time'];seq[t]+=1
        rec={'event_row_index':i,'time':t,'reject_seq_at_time':seq[t],'detail':r.get('detail',''),
             'direction':r.get('direction',''),'volume':fv(r.get('volume')),'units':round(fv(r.get('volume'))/0.01),
             'price':fv(r.get('price')),'structural_sl':fv(r.get('structural_sl'))}
        raw.append(rec);per_time[t].append(rec)
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_EVENT_LEDGER_20260916.csv',raw)

    # signals whose earned intended NHA matches the reject moment (allow seconds offset in logger)
    affected=[r for r in signals if b(r.get('exit_reject_affected'))]
    incidents=[]
    for t,rr in sorted(per_time.items(),key=lambda x:dt(x[0])):
        tt=dt(t)
        sigs=[]
        for s in affected:
            it=s.get('intended_fast_nha_time','')
            if it and abs((dt(it)-tt).total_seconds())<=6:
                sigs.append(s)
        incidents.append({
            'time':t,'reject_events':len(rr),'reject_units':sum(int(x['units']) for x in rr),
            'directions':'|'.join(sorted(set(x['direction'] for x in rr))),
            'affected_positions':len(sigs),'affected_units':sum(int(float(x['units'])) for x in sigs),
            'signal_ids':'|'.join(str(x['signal_id']) for x in sigs),
            'max_unintended_hold_hours':max([fv(x.get('unintended_hold_hours')) for x in sigs] or [0]),
            'sum_unintended_hold_hours':sum(fv(x.get('unintended_hold_hours')) for x in sigs),
        })
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_INCIDENT_LEDGER_20260916.csv',incidents)
    return raw,incidents

def build_exposure(deals,out):
    rows=sorted(deals,key=lambda r:(dt(r['time']),int(float(r['deal']))))
    long_lots=short_lots=0.0
    path=[]
    # intervals are state AFTER current deal until next deal
    overlap_eps=[];cur=None
    max_gross=0.0;max_gross_time=''
    overlap_seconds=0.0
    for i,r in enumerate(rows):
        v=fv(r['volume']);typ=r['type'];io=r['io']
        if io=='in':
            if typ=='buy':long_lots+=v
            else:short_lots+=v
        else:
            if typ=='sell':long_lots-=v
            else:short_lots-=v
        for name,val in [('long',long_lots),('short',short_lots)]:
            if abs(val)<1e-9:
                if name=='long':long_lots=0.0
                else:short_lots=0.0
        gross=long_lots+short_lots
        if gross>max_gross+1e-12:max_gross=gross;max_gross_time=r['time']
        next_time=dt(rows[i+1]['time']) if i+1<len(rows) else dt(r['time'])
        dur=max(0.0,(next_time-dt(r['time'])).total_seconds())
        overlap=(long_lots>1e-12 and short_lots>1e-12 and dur>0)
        if overlap: overlap_seconds+=dur
        path.append({
            'time':r['time'],'deal':r['deal'],'io':io,'type':typ,'volume':v,'price':r['price'],'profit':r.get('profit',''),
            'comment':r.get('comment',''),'long_lots_after':long_lots,'short_lots_after':short_lots,'gross_lots_after':gross,
            'long_units_after':round(long_lots/0.01,6),'short_units_after':round(short_lots/0.01,6),'gross_units_after':round(gross/0.01,6),
            'state_duration_to_next_deal_hours':dur/3600.0,'opposite_overlap_state':int(overlap)
        })
        if overlap:
            if cur is None:
                cur={'start_time':r['time'],'end_time':rows[i+1]['time'],'duration_hours':dur/3600.0,
                     'max_long_units':long_lots/0.01,'max_short_units':short_lots/0.01,'max_gross_units':gross/0.01,
                     'start_deal':r['deal'],'last_deal':r['deal']}
            else:
                cur['end_time']=rows[i+1]['time'];cur['duration_hours']+=dur/3600.0
                cur['max_long_units']=max(cur['max_long_units'],long_lots/0.01);cur['max_short_units']=max(cur['max_short_units'],short_lots/0.01);cur['max_gross_units']=max(cur['max_gross_units'],gross/0.01);cur['last_deal']=r['deal']
        elif cur is not None:
            overlap_eps.append(cur);cur=None
    if cur is not None:overlap_eps.append(cur)
    for j,e in enumerate(overlap_eps,1):e['episode_id']=j
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_EXPOSURE_PATH_LEDGER_20260916.csv',path)
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_OVERLAP_EPISODE_LEDGER_20260916.csv',overlap_eps,
              ['episode_id','start_time','end_time','duration_hours','max_long_units','max_short_units','max_gross_units','start_deal','last_deal'])
    return {'max_gross_units':max_gross/0.01,'max_gross_time':max_gross_time,'overlap_hours':overlap_seconds/3600.0,'overlap_episodes':len(overlap_eps)}

def build_sl(signals,out):
    rows=[]
    for r in signals:
        if r.get('exit_reason_actual')!='STRUCTURAL_SL':continue
        units=int(float(r['units']));entry=fv(r['entry_price_actual']);sl=fv(r['structural_sl']);exitp=fv(r['exit_price_actual']);pnl=fv(r['actual_pnl'])
        risk=abs(entry-sl);risk_dollars=risk*units
        ar=pnl/risk_dollars if risk_dollars>0 else ''
        direction=r['direction']
        adverse=(sl-exitp) if direction=='LONG' else (exitp-sl)
        adverse=max(0.0,adverse)
        rows.append({
            'signal_id':r['signal_id'],'direction':direction,'units':units,'entry_time':r['entry_time_actual'],'entry_price':entry,
            'structural_sl':sl,'exit_time':r['exit_time_actual'],'exit_price':exitp,'actual_pnl':pnl,
            'intended_risk_price':risk,'intended_risk_dollars':risk_dollars,'actual_r':ar,
            'adverse_slippage_price':adverse,'adverse_slippage_r':(adverse/risk if risk>0 else ''),
            'excess_loss_beyond_1r':max(0.0,-1.0-float(ar)) if ar!='' else '',
            'exit_comment':r.get('exit_comment','')
        })
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_SL_EXECUTION_LEDGER_20260916.csv',rows)
    return rows

def build_pending(signals,out):
    rows=[]
    for r in signals:
        if not b(r.get('exit_reject_affected')):continue
        rows.append({
            'signal_id':r['signal_id'],'direction':r['direction'],'units':r['units'],'entry_time_actual':r['entry_time_actual'],
            'intended_fast_nha_time':r['intended_fast_nha_time'],'actual_exit_time':r['exit_time_actual'],'unintended_hold_hours':r['unintended_hold_hours'],
            'entry_price_actual':r['entry_price_actual'],'structural_sl':r['structural_sl'],'exit_price_actual':r['exit_price_actual'],'actual_pnl':r['actual_pnl'],
            'exit_reason_actual':r['exit_reason_actual'],'exit_comment':r['exit_comment']
        })
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_PENDING_EXIT_DELAY_LEDGER_20260916.csv',rows)
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--events',required=True);ap.add_argument('--signal-ledger',required=True);ap.add_argument('--deals-ledger',required=True);ap.add_argument('--out-dir',required=True);args=ap.parse_args()
    out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
    events=read_csv(args.events);signals=read_csv(args.signal_ledger);deals=read_csv(args.deals_ledger)
    raw,inc=build_reject_ledgers(events,signals,out);exp=build_exposure(deals,out);sl=build_sl(signals,out);pend=build_pending(signals,out)
    summary={'exit_reject_events':len(raw),'exit_reject_incidents':len(inc),'pending_exit_affected_positions':len(pend),'structural_sl_positions':len(sl),**exp}
    (out/'V10_BOUNDED_M3_ACTUAL_TICK_EXTENDED_VALIDATION_20260916.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
