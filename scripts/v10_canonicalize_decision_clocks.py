#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,json,re
from pathlib import Path
from datetime import datetime

EFF_RE=re.compile(r'\beffective_ts=(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\b')

def read_csv(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(p,rows,fields):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    with tmp.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    tmp.replace(p)
def norm(s):return str(s).replace('.','-')
def dots(s):return str(s).replace('-','.')
def pdt(s):return datetime.strptime(norm(s),'%Y-%m-%d %H:%M:%S')
def effective(e):
    m=EFF_RE.search(e.get('entry_detail',''))
    return m.group(1) if m else e.get('decision_time','')

def main():
    ap=argparse.ArgumentParser(description='Canonicalize V10 selected-signal decision clocks without conflating them with actual tick/fill times.')
    ap.add_argument('--baseline',required=True);ap.add_argument('--execution',required=True);ap.add_argument('--features',required=True)
    args=ap.parse_args()
    allb=read_csv(args.baseline);base=[r for r in allb if float(r.get('W') or 0)>0]
    exe=read_csv(args.execution);feat=read_csv(args.features)
    if not(len(base)==len(exe)==len(feat)==1159):raise SystemExit(f'row count mismatch base={len(base)} execution={len(exe)} features={len(feat)}')
    shifted=[]
    for sid,(b,e,f) in enumerate(zip(base,exe,feat)):
        if int(e['signal_id'])!=sid or int(f['signal_id'])!=sid:raise SystemExit(f'signal_id mismatch sid={sid}')
        canon=b['decision_ts']; eff=effective(e)
        if norm(canon)!=norm(eff):raise SystemExit(f'effective clock mismatch sid={sid}: baseline={canon} effective={eff}')
        old_event=e.get('entry_event_time') or e.get('decision_time','')
        if not old_event:raise SystemExit(f'missing execution event time sid={sid}')
        old_ft=f.get('decision_time','')
        # A pre-hotfix feature ledger used the logger event time.  It must match either
        # that event time or the canonical decision time; anything else is not repaired.
        if norm(old_ft) not in (norm(old_event),norm(canon)):
            raise SystemExit(f'feature clock mismatch sid={sid}: feature={old_ft} event={old_event} baseline={canon}')
        if f.get('h4_source_end') and pdt(f['h4_source_end'])>pdt(canon):
            raise SystemExit(f'feature uses H4 source after canonical decision sid={sid}: {f["h4_source_end"]} > {canon}')
        lag=(pdt(old_event)-pdt(canon)).total_seconds()
        if lag<0:raise SystemExit(f'event precedes decision sid={sid}: {lag}s')
        if lag>0:shifted.append((sid,lag,canon,old_event))
        e['entry_event_time']=old_event
        e['decision_time']=dots(canon)
        f['decision_time']=dots(canon)
    efields=list(exe[0].keys())
    if 'entry_event_time' not in efields:
        i=efields.index('decision_time')+1;efields.insert(i,'entry_event_time')
    write_csv(args.execution,exe,efields)
    write_csv(args.features,feat,list(feat[0].keys()))

    fv=Path(args.features).with_suffix('.validation.json')
    if fv.exists():
        j=json.loads(fv.read_text(encoding='utf-8-sig'))
        j['decision_clock']='baseline decision_ts / EA effective_ts (canonical); logger/fill tick is separate'
        j['canonicalized_event_lag_rows']=len(shifted)
        j['max_event_lag_seconds']=max([x[1] for x in shifted] or [0])
        fv.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    ev=Path(args.execution).parent/'V10_BOUNDED_M3_ACTUAL_TICK_LEDGER_VALIDATION_20260916.json'
    if ev.exists():
        j=json.loads(ev.read_text(encoding='utf-8-sig'))
        j['decision_clock']='baseline decision_ts / EA effective_ts (canonical); entry_event_time and entry_time_actual preserve execution chronology'
        j['entry_event_lag_rows']=len(shifted)
        j['max_entry_event_lag_seconds']=max([x[1] for x in shifted] or [0])
        ev.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'rows':1159,'canonicalized_event_lag_rows':len(shifted),'max_event_lag_seconds':max([x[1] for x in shifted] or [0]),'first_shifted':shifted[:5]},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
