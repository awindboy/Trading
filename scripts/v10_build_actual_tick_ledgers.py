#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,re,zipfile,math,json,statistics
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter,defaultdict
from xml.etree import ElementTree as ET

NS={'a':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
ENTRY_EVENTS={'ENTRY_FILL','ENTRY_REJECT','ENTRY_REJECT_SL_ALREADY_TOUCHED'}

def dt_event(s): return datetime.strptime(s,'%Y.%m.%d %H:%M:%S')
def dt_csv(s):
    # repo ledgers may use YYYY-MM-DD; raw events use dots
    for fmt in ('%Y-%m-%d %H:%M:%S','%Y.%m.%d %H:%M:%S'):
        try:return datetime.strptime(s,fmt)
        except:pass
    raise ValueError(s)

def read_events(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def read_xlsx_rows(path):
    with zipfile.ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall('a:si',NS):
                shared.append(''.join((t.text or '') for t in si.iter('{%s}t'%NS['a'])))
        sh=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows={}
        for row in sh.findall('.//a:sheetData/a:row',NS):
            d={}
            for c in row.findall('a:c',NS):
                ref=c.attrib['r']; col=re.match(r'([A-Z]+)',ref).group(1); typ=c.attrib.get('t'); v=c.find('a:v',NS)
                if v is None:continue
                raw=v.text
                if typ=='s': val=shared[int(raw)]
                elif typ=='inlineStr':
                    t=c.find('.//a:t',NS);val=t.text if t is not None else ''
                else:
                    try:
                        val=float(raw); val=int(val) if val.is_integer() else val
                    except:val=raw
                d[col]=val
            rows[int(row.attrib['r'])]=d
        return rows

def find_header(rows, predicate):
    for rn,d in rows.items():
        if predicate(d):return rn
    raise RuntimeError('header not found')

def parse_report(path):
    rows=read_xlsx_rows(path)
    # deals
    dh=find_header(rows,lambda d:d.get('A')=='시간' and d.get('E')=='방향' and d.get('K')=='수익')
    deals=[]
    for rn in sorted(k for k in rows if k>dh):
        d=rows[rn]
        if d.get('E') not in ('in','out'):continue
        deals.append({
            'row':rn,'time':str(d.get('A')),'deal':int(d.get('B')),'symbol':d.get('C'),'type':d.get('D'),'io':d.get('E'),
            'volume':float(d.get('F') or 0),'price':float(d.get('G') or 0),'order':int(d.get('H')) if d.get('H') is not None else None,
            'commission':float(d.get('I') or 0),'swap':float(d.get('J') or 0),'profit':float(d.get('K') or 0),
            'balance':float(d.get('L') or 0),'comment':d.get('M') or ''
        })
    # orders section starts at first '주문' label and header next row
    oh=find_header(rows,lambda d:d.get('A')=='진입 시간' and d.get('B')=='주문' and d.get('D')=='종류')
    orders=[]
    for rn in sorted(k for k in rows if k>oh and k<dh):
        d=rows[rn]
        if d.get('B') is None or d.get('D') not in ('buy','sell'):continue
        voltxt=str(d.get('E') or '')
        vm=re.match(r'([0-9.]+)',voltxt)
        orders.append({
            'row':rn,'time':str(d.get('A')),'order':int(d.get('B')),'symbol':d.get('C'),'type':d.get('D'),
            'volume':float(vm.group(1)) if vm else None,'price':float(d.get('G') or 0),'sl':float(d.get('H') or 0) if d.get('H') not in (None,'') else None,
            'tp':float(d.get('I') or 0) if d.get('I') not in (None,'') else None,'done_time':str(d.get('J') or ''),
            'state':d.get('L') or '','comment':d.get('M') or ''
        })
    return rows,deals,orders

def entry_effective_time(r):
    # ENTRY_FILL is logged on the first executable tick and can be 1-2 seconds
    # after the research decision clock.  The EA persists the exact signal clock
    # as effective_ts in detail.  Reject rows have no effective_ts and their
    # event time is the decision clock.
    m=re.search(r'\beffective_ts=(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\b',r.get('detail',''))
    return m.group(1) if m else r['time']

def infer_entry_events(events):
    entries=[r.copy() for r in events if r['event'] in ENTRY_EVENTS]
    assert len(entries)==1159, len(entries)
    for sid,r in enumerate(entries):
        r['signal_id']=sid
        r['effective_time']=entry_effective_time(r)
        if r['event']=='ENTRY_FILL':
            m=re.search(r'\bsignal=(\d+)\b',r.get('detail',''))
            if not m or int(m.group(1))!=sid:
                raise RuntimeError(f'signal sequence mismatch sid={sid} detail={r.get("detail")}')
    return entries

def flip_schedule(events):
    flips=[]
    for r in events:
        if r['event']!='FAST_HA_FLIP':continue
        m=re.match(r'(LONG|SHORT)\s*->\s*(LONG|SHORT)',r['detail'])
        if not m:continue
        flips.append({'time':dt_event(r['time']),'old':m.group(1),'new':m.group(2),'raw_time':r['time']})
    return flips

def first_exit_flip(entry_time,direction,flips):
    for f in flips:
        if f['time']>=entry_time and f['old']==direction:
            return f
    return None

def build_positions(events,deals,orders):
    entry_events=infer_entry_events(events)
    flips=flip_schedule(events)
    reject_times=Counter(dt_event(r['time']) for r in events if r['event']=='FAST_NHA_EXIT_REJECT')
    success_by_time=defaultdict(list)
    for r in events:
        if r['event']=='FAST_NHA_EXIT':
            m=re.search(r'ticket=(\d+)',r.get('detail',''))
            if m: success_by_time[dt_event(r['time'])].append(int(m.group(1)))

    # Entry deal/order maps by signal comment.
    entry_deal_by_sid={}
    ticket_by_sid={}
    for d in deals:
        if d['io']!='in':continue
        m=re.fullmatch(r'V10_(\d+)',d['comment'])
        if m:
            sid=int(m.group(1)); entry_deal_by_sid[sid]=d; ticket_by_sid[sid]=d['order']

    # Build filled position records.
    positions={}
    for e in entry_events:
        sid=e['signal_id']; units=round(float(e['volume'])/0.01) if float(e['volume']) else 0
        rec={
            'signal_id':sid,'decision_time':e['effective_time'],'entry_event_time':e['time'],'entry_status':e['event'],'entry_detail':e['detail'],
            'direction':e['direction'],'units':units,'requested_or_event_price':float(e['price'] or 0),
            'structural_sl':float(e['structural_sl'] or 0),'filled':e['event']=='ENTRY_FILL',
            'market_closed_entry_reject':e['event']=='ENTRY_REJECT',
            'sl_already_touched_reject':e['event']=='ENTRY_REJECT_SL_ALREADY_TOUCHED',
        }
        if rec['filled']:
            d=entry_deal_by_sid[sid]
            rec.update({'entry_time_actual':d['time'],'entry_price_actual':d['price'],'entry_ticket':d['order'],'entry_deal':d['deal']})
            f=first_exit_flip(dt_event(d['time']),e['direction'],flips)
            rec['intended_fast_nha_time']=f['raw_time'] if f else ''
            rec['intended_fast_nha_old_direction']=f['old'] if f else ''
            rec['intended_exit_reject_count_at_time']=(sum(reject_times[f['time']+timedelta(seconds=o)] for o in (0,1,2,3,4,5)) if f else 0)
        else:
            rec.update({'entry_time_actual':'','entry_price_actual':'','entry_ticket':'','entry_deal':'','intended_fast_nha_time':'','intended_fast_nha_old_direction':'','intended_exit_reject_count_at_time':0})
        positions[sid]=rec

    # Map exit deals to open positions. Use NHA ticket events when possible; SL price/comment otherwise;
    # fall back to predicted PnL distance.
    open_by_ticket={}
    for d in sorted(deals,key=lambda x:(dt_event(x['time']),x['deal'])):
        t=dt_event(d['time'])
        if d['io']=='in':
            m=re.fullmatch(r'V10_(\d+)',d['comment'])
            if m:
                sid=int(m.group(1)); open_by_ticket[d['order']]=sid
            continue
        close_dir='LONG' if d['type']=='sell' else 'SHORT'
        candidates=[]
        for ticket,sid in open_by_ticket.items():
            r=positions[sid]
            if r['direction']!=close_dir:continue
            if abs(float(r['units'])*0.01-d['volume'])>1e-9:continue
            candidates.append((ticket,sid))
        if not candidates:
            raise RuntimeError(f'No exit candidate for deal {d}')
        # exact successful NHA ticket set around this timestamp (events may log at second 0, deals at +1 sec)
        nha_tickets=set()
        for offs in (0,-1,1):
            nha_tickets.update(success_by_time.get(t+timedelta(seconds=offs),[]))
        if nha_tickets:
            narrowed=[x for x in candidates if x[0] in nha_tickets]
            if narrowed:candidates=narrowed
        # SL comment narrows by intended SL
        msl=re.search(r'\bsl\s+([0-9.]+)',d['comment'],re.I)
        if msl:
            slv=float(msl.group(1))
            narrowed=[x for x in candidates if abs(float(positions[x[1]]['structural_sl'])-slv)<=0.06]
            if narrowed:candidates=narrowed
        def pred(ticket_sid):
            ticket,sid=ticket_sid; r=positions[sid]; ep=float(r['entry_price_actual']); units=float(r['units'])
            # GOLD# tester: 0.01 lot ≈ $1 per $1 move
            pp=(d['price']-ep)*units if r['direction']=='LONG' else (ep-d['price'])*units
            return abs(pp-d['profit'])
        chosen=min(candidates,key=pred)
        ticket,sid=chosen; r=positions[sid]
        r.update({'exit_time_actual':d['time'],'exit_price_actual':d['price'],'exit_deal':d['deal'],'exit_order':d['order'],
                  'actual_pnl':d['profit'],'actual_swap':d['swap'],'exit_comment':d['comment'],
                  'exit_reason_actual':'STRUCTURAL_SL' if msl else 'FAST_NHA_OR_MANUAL'})
        del open_by_ticket[ticket]
    if open_by_ticket:
        raise RuntimeError(f'Unclosed positions: {open_by_ticket}')

    # defect flags and timing metrics
    for sid,r in positions.items():
        if not r['filled']:
            r.update({'exit_time_actual':'','exit_price_actual':'','exit_deal':'','exit_order':'','actual_pnl':'','actual_swap':'','exit_comment':'','exit_reason_actual':'',
                      'actual_holding_hours':'','exit_reject_affected':False,'unintended_hold_hours':'','actual_exit_after_intended_flip':False})
            continue
        et=dt_event(r['entry_time_actual']); xt=dt_event(r['exit_time_actual']); r['actual_holding_hours']=(xt-et).total_seconds()/3600
        if r['intended_fast_nha_time']:
            it=dt_event(r['intended_fast_nha_time'])
            after=xt>it+timedelta(seconds=2)
            # only call affected when an exit rejection existed at intended NHA and the position survived past it.
            affected=bool(r['intended_exit_reject_count_at_time']) and after
            r['exit_reject_affected']=affected
            r['actual_exit_after_intended_flip']=after
            r['unintended_hold_hours']=max(0,(xt-it).total_seconds()/3600) if affected else 0.0
        else:
            r['exit_reject_affected']=False;r['actual_exit_after_intended_flip']=False;r['unintended_hold_hours']=0.0
    return [positions[i] for i in range(1159)]

def write_csv(path,rows,fields):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--events',required=True);ap.add_argument('--report',required=True);ap.add_argument('--out-dir',required=True)
    args=ap.parse_args(); out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
    events=read_events(args.events); rows,deals,orders=parse_report(args.report); pos=build_positions(events,deals,orders)
    fields=['signal_id','decision_time','entry_event_time','entry_status','entry_detail','direction','units','requested_or_event_price','structural_sl','filled','market_closed_entry_reject','sl_already_touched_reject','entry_time_actual','entry_price_actual','entry_ticket','entry_deal','intended_fast_nha_time','intended_fast_nha_old_direction','intended_exit_reject_count_at_time','exit_time_actual','exit_price_actual','exit_deal','exit_order','actual_pnl','actual_swap','exit_comment','exit_reason_actual','actual_holding_hours','exit_reject_affected','actual_exit_after_intended_flip','unintended_hold_hours']
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_SIGNAL_EXECUTION_LEDGER_20260916.csv',pos,fields)
    rejects=[r for r in pos if not r['filled']]
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_ENTRY_REJECT_LEDGER_20260916.csv',rejects,fields)
    affected=[r for r in pos if r.get('exit_reject_affected')]
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_AFFECTED_LEDGER_20260916.csv',affected,fields)
    # raw normalized deals/orders
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_DEALS_LEDGER_20260916.csv',deals,['row','time','deal','symbol','type','io','volume','price','order','commission','swap','profit','balance','comment'])
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_ORDERS_LEDGER_20260916.csv',orders,['row','time','order','symbol','type','volume','price','sl','tp','done_time','state','comment'])
    # period/direction/execution summary
    summary=[]
    for period_name,pred in [('ALL',lambda r:True),('2025',lambda r:r['decision_time'].startswith('2025.')),('2026',lambda r:r['decision_time'].startswith('2026.'))]:
      for direction in ('ALL','LONG','SHORT'):
        subset=[r for r in pos if pred(r) and (direction=='ALL' or r['direction']==direction)]
        fills=[r for r in subset if r['filled']]
        pnl=sum(float(r['actual_pnl']) for r in fills)
        gp=sum(max(0,float(r['actual_pnl'])) for r in fills);gl=sum(min(0,float(r['actual_pnl'])) for r in fills)
        summary.append({'period':period_name,'direction':direction,'selected_signals':len(subset),'fills':len(fills),'entry_rejects':sum(r['market_closed_entry_reject'] for r in subset),
                        'sl_already_touched_rejects':sum(r['sl_already_touched_reject'] for r in subset),'units_filled':sum(r['units'] for r in fills),'pnl':round(pnl,2),'gross_profit':round(gp,2),'gross_loss':round(gl,2),'pf':round(gp/(-gl),6) if gl<0 else '',
                        'exit_reject_affected_positions':sum(bool(r.get('exit_reject_affected')) for r in fills),'unintended_hold_hours_sum':round(sum(float(r.get('unintended_hold_hours') or 0) for r in fills),4)})
    write_csv(out/'V10_BOUNDED_M3_ACTUAL_TICK_PERIOD_DIRECTION_SUMMARY_20260916.csv',summary,list(summary[0]))
    # validation json
    fills=[r for r in pos if r['filled']]; affected=[r for r in fills if r['exit_reject_affected']]
    val={
      'selected_signals':len(pos),'fills':len(fills),'entry_rejects':len([r for r in pos if r['market_closed_entry_reject']]),'sl_already_touched_rejects':len([r for r in pos if r['sl_already_touched_reject']]),
      'filled_pnl':round(sum(float(r['actual_pnl']) for r in fills),2),'filled_units':sum(r['units'] for r in fills),'affected_exit_reject_positions':len(affected),
      'distinct_exit_reject_timestamps':len(set(r['time'] for r in events if r['event']=='FAST_NHA_EXIT_REJECT')),
      'raw_exit_reject_events':sum(r['event']=='FAST_NHA_EXIT_REJECT' for r in events),
      'max_actual_holding_hours':max(float(r['actual_holding_hours']) for r in fills),
      'max_unintended_hold_hours':max(float(r['unintended_hold_hours']) for r in affected) if affected else 0,
      'sum_unintended_hold_hours_positionwise':round(sum(float(r['unintended_hold_hours']) for r in affected),4),
    }
    (out/'V10_BOUNDED_M3_ACTUAL_TICK_LEDGER_VALIDATION_20260916.json').write_text(json.dumps(val,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(val,indent=2))
if __name__=='__main__':main()
