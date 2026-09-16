#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,json,math,re
from pathlib import Path

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(path,rows,fields=None):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0]) if rows else []
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def f(v,d=0.0):
    try:return float(v)
    except:return d
def b(v):return str(v).lower() in ('true','1','yes')
def norm(s):return str(s).replace('.','-')
def execution_signal_time(e):
    m=re.search(r'\beffective_ts=(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\b',e.get('entry_detail',''))
    return m.group(1) if m else e.get('decision_time','')

def agg(rows,pnlcol,refpnlcol=None):
    vals=[f(r.get(pnlcol)) for r in rows if str(r.get(pnlcol,''))!='']
    gp=sum(max(0,x) for x in vals);gl=sum(min(0,x) for x in vals)
    out={'N':len(rows),'pnl':sum(vals),'gross_profit':gp,'gross_loss':gl,'PF':gp/(-gl) if gl<0 else '', 'wins':sum(x>0 for x in vals),'losses':sum(x<0 for x in vals)}
    if refpnlcol:
        refs=[f(r.get(refpnlcol)) for r in rows];out['reference_pnl']=sum(refs);out['delta_vs_reference']=out['pnl']-out['reference_pnl']
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--execution',required=True);ap.add_argument('--out-dir',required=True);args=ap.parse_args();out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
    allbase=read_csv(args.baseline);base=[r for r in allbase if f(r.get('W'))>0];exe=read_csv(args.execution)
    if len(base)!=1159 or len(exe)!=1159:raise SystemExit(f'expected 1159 selected rows, got base={len(base)} exe={len(exe)}')
    rows=[]
    for sid,(r,e) in enumerate(zip(base,exe)):
        if int(e['signal_id'])!=sid:raise SystemExit(f'signal id mismatch {sid}')
        et=execution_signal_time(e)
        if norm(r['decision_ts'])!=norm(et):raise SystemExit(f'signal-clock mismatch sid={sid}: baseline={r["decision_ts"]} effective={et} event={e.get("entry_event_time", e.get("decision_time",""))}')
        d='LONG' if r['direction']=='UP' else 'SHORT'
        if d!=e['direction']:raise SystemExit(f'direction mismatch sid={sid}')
        w=f(r['W']);ref_pnl=f(r['natural_child_pnl_m1'])*w;ref_r=f(r['R_child'])*w
        filled=b(e['filled']);affected=b(e.get('exit_reject_affected'))
        if not filled:
            cls='ENTRY_REJECT_SL_ALREADY_TOUCHED' if b(e.get('sl_already_touched_reject')) else 'ENTRY_REJECT_MARKET_CLOSED'
        else: cls='FILLED_EXIT_REJECT_AFFECTED' if affected else 'FILLED_CLEAN'
        actual_pnl=f(e['actual_pnl']) if filled else ''
        risk_dist=abs(f(e.get('entry_price_actual'))-f(e.get('structural_sl'))) if filled else ''
        risk_dollars=(risk_dist*int(f(e.get('units')))) if filled else ''
        actual_r=(f(actual_pnl)/risk_dollars) if filled and risk_dollars and risk_dollars>0 else ''
        o={
            'signal_id':sid,'decision_ts':r['decision_ts'],'year':r['entry_year'],'run_id':r['run_id'],'direction':r['direction'],'direction_exec':d,
            'run_seq':r['run_seq'],'final_run_len':r['final_run_len'],'W':r['W'],'oracle_early_third':r['oracle_early_third'],
            'P_M':r.get('P_M',''),'P_W':r.get('P_W',''),'P_SUPPORT':r.get('P_SUPPORT',''),'SCORE':r.get('SCORE',''),'BIN':r.get('BIN',''),
            'reference_entry_px':r['entry_px'],'reference_structural_sl':r['h1_sl_m1'],'reference_h1_risk':r['h1_risk_m1'],'reference_natural_exit_time':r['natural_exit_time_m1'],
            'reference_child_pnl_1x':r['natural_child_pnl_m1'],'reference_R_1x':r['R_child'],'reference_weighted_pnl':ref_pnl,'reference_weighted_R':ref_r,
            'execution_class':cls,'filled':int(filled),'entry_time_actual':e.get('entry_time_actual',''),'entry_price_actual':e.get('entry_price_actual',''),
            'structural_sl_actual_payload':e.get('structural_sl',''),'intended_fast_nha_time':e.get('intended_fast_nha_time',''),'exit_time_actual':e.get('exit_time_actual',''),
            'exit_price_actual':e.get('exit_price_actual',''),'exit_reason_actual':e.get('exit_reason_actual',''),'actual_pnl':actual_pnl,'actual_R_vs_tick_entry_structural_risk':actual_r,
            'pnl_delta_vs_m1_reference':(f(actual_pnl)-ref_pnl) if filled else '', 'R_delta_vs_m1_reference':(f(actual_r)-ref_r) if filled and actual_r!='' else '',
            'unintended_hold_hours':e.get('unintended_hold_hours',''),'exit_comment':e.get('exit_comment','')
        }
        rows.append(o)
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_REFERENCE_PARITY_LEDGER_20260916.csv',rows)

    summary=[]
    def add(dim,val,sub):
        fills=[r for r in sub if r['filled']==1]
        a=agg(fills,'actual_pnl','reference_weighted_pnl') if fills else {'N':0,'pnl':0,'gross_profit':0,'gross_loss':0,'PF':'','wins':0,'losses':0,'reference_pnl':0,'delta_vs_reference':0}
        summary.append({'dimension':dim,'value':val,'selected_signals':len(sub),'fills':len(fills),'units_selected':sum(f(r['W']) for r in sub),'units_filled':sum(f(r['W']) for r in fills),
                        'reference_pnl_all_selected':sum(f(r['reference_weighted_pnl']) for r in sub),'reference_R_all_selected':sum(f(r['reference_weighted_R']) for r in sub),
                        'reference_pnl_filled':a['reference_pnl'],'actual_pnl_filled':a['pnl'],'actual_vs_ref_delta_filled':a['delta_vs_reference'],'actual_PF_filled':a['PF'],
                        'clean_fills':sum(r['execution_class']=='FILLED_CLEAN' for r in sub),'exit_reject_affected_fills':sum(r['execution_class']=='FILLED_EXIT_REJECT_AFFECTED' for r in sub),
                        'market_closed_entry_rejects':sum(r['execution_class']=='ENTRY_REJECT_MARKET_CLOSED' for r in sub),'sl_touched_entry_rejects':sum(r['execution_class']=='ENTRY_REJECT_SL_ALREADY_TOUCHED' for r in sub)})
    add('ALL','ALL',rows)
    for y in sorted(set(r['year'] for r in rows)):add('YEAR',y,[r for r in rows if r['year']==y])
    for d in ('UP','DOWN'):add('DIRECTION',d,[r for r in rows if r['direction']==d])
    for w in ('1.0','3.0'):
        add('WEIGHT',w,[r for r in rows if abs(f(r['W'])-float(w))<1e-9])
    for o in ('True','False'):add('ORACLE',o,[r for r in rows if str(r['oracle_early_third'])==o])
    for c in sorted(set(r['execution_class'] for r in rows)):add('EXECUTION_CLASS',c,[r for r in rows if r['execution_class']==c])
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_PARITY_SUMMARY_20260916.csv',summary)

    # exact reference subsets needed by the narrative
    entry_rej=[r for r in rows if not r['filled']]
    clean=[r for r in rows if r['execution_class']=='FILLED_CLEAN']
    contaminated=[r for r in rows if r['execution_class']=='FILLED_EXIT_REJECT_AFFECTED']
    validation={
        'rows':len(rows),'entry_reject_rows':len(entry_rej),'clean_fill_rows':len(clean),'contaminated_fill_rows':len(contaminated),
        'selected_reference_pnl':sum(f(r['reference_weighted_pnl']) for r in rows),'selected_reference_r':sum(f(r['reference_weighted_R']) for r in rows),
        'filled_reference_pnl':sum(f(r['reference_weighted_pnl']) for r in rows if r['filled']),'filled_actual_pnl':sum(f(r['actual_pnl']) for r in rows if r['filled']),
        'entry_reject_reference_pnl':sum(f(r['reference_weighted_pnl']) for r in entry_rej),'entry_reject_reference_r':sum(f(r['reference_weighted_R']) for r in entry_rej),
        'clean_reference_pnl':sum(f(r['reference_weighted_pnl']) for r in clean),'clean_actual_pnl':sum(f(r['actual_pnl']) for r in clean),
        'contaminated_reference_pnl':sum(f(r['reference_weighted_pnl']) for r in contaminated),'contaminated_actual_pnl':sum(f(r['actual_pnl']) for r in contaminated),
    }
    (out/'V10_BOUNDED_M3_ACTUAL_TICK_PARITY_VALIDATION_20260916.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(validation,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
