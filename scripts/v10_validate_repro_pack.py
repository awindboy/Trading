#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,hashlib,json,math,re
from pathlib import Path

EXPECTED_RAW={
 'V10_BOUNDED_M3_ACTUAL_TICK_EVENTS_RAW_20260916.csv':'eea7f54a4f0a70aa3c3ea52b38163f95fe8f79de93cdf0ccf8d73cc8fcc91f69',
 'V10_BOUNDED_M3_ACTUAL_TICK_REPORT_RAW_20260916.xlsx':'83b3b5311b229ef9adb2754ac4475d174d3fb6d1337332b0a39738d6216be83c',
}
EXPECTED_ROWS={
 'V10_BOUNDED_M3_ACTUAL_TICK_SIGNAL_EXECUTION_LEDGER_20260916.csv':1159,
 'V10_BOUNDED_M3_ACTUAL_TICK_ENTRY_REJECT_LEDGER_20260916.csv':175,
 'V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_AFFECTED_LEDGER_20260916.csv':131,
 'V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_EVENT_LEDGER_20260916.csv':134,
 'V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_INCIDENT_LEDGER_20260916.csv':84,
 'V10_BOUNDED_M3_ACTUAL_TICK_PENDING_EXIT_DELAY_LEDGER_20260916.csv':131,
 'V10_BOUNDED_M3_ACTUAL_TICK_DEALS_LEDGER_20260916.csv':1968,
 'V10_BOUNDED_M3_ACTUAL_TICK_ORDERS_LEDGER_20260916.csv':1968,
 'V10_BOUNDED_M3_ACTUAL_TICK_EXPOSURE_PATH_LEDGER_20260916.csv':1968,
 'V10_BOUNDED_M3_ACTUAL_TICK_OVERLAP_EPISODE_LEDGER_20260916.csv':33,
 'V10_BOUNDED_M3_ACTUAL_TICK_SL_EXECUTION_LEDGER_20260916.csv':252,
 'V10_BOUNDED_M3_ACTUAL_TICK_PERIOD_DIRECTION_SUMMARY_20260916.csv':9,
 'V10_POST_HEAD_SELECTED_SIGNAL_FEATURE_LEDGER_20260916.csv':1159,
 'V10_BOUNDED_M3_ACTUAL_TICK_REFERENCE_PARITY_LEDGER_20260916.csv':1159,
 'V10_POST_HEAD_MODEL_REGEN_LEDGER_20260916.csv':1159,
}
REQUIRED_NONEMPTY=[
 'V10_BOUNDED_M3_ACTUAL_TICK_PARITY_SUMMARY_20260916.csv',
 'V10_POST_HEAD_REGEN_MODEL_COEFFICIENTS_20260916.csv',
 'V10_POST_HEAD_REGEN_SCORE_LEDGER_20260916.csv',
 'V10_POST_HEAD_REGEN_MODEL_METRICS_20260916.csv',
 'V10_K1_DANGER_REGEN_TAIL_SWEEP_20260916.csv',
 'V10_POST_HEAD_ORACLE_NONORACLE_ECONOMICS_REGEN_20260916.csv',
 'V10_POST_HEAD_NONORACLE_RUN_LENGTH_ECONOMICS_REGEN_20260916.csv',
 'V10_POST_HEAD_BOUNDED_FP_FN_DECOMPOSITION_REGEN_20260916.csv',
 'V10_POST_HEAD_BOUNDED_K1_SCALE_SCAN_REGEN_20260916.csv',
 'V10_POST_HEAD_MORPHOLOGY_MEDIANS_REGEN_20260916.csv',
 'V10_REPRODUCIBILITY_ARTIFACT_SHA256_20260916.csv',
]
REQUIRED_JSON=[
 'V10_BOUNDED_M3_ACTUAL_TICK_LEDGER_VALIDATION_20260916.json',
 'V10_BOUNDED_M3_ACTUAL_TICK_EXTENDED_VALIDATION_20260916.json',
 'V10_POST_HEAD_SELECTED_SIGNAL_FEATURE_LEDGER_20260916.validation.json',
 'V10_BOUNDED_M3_ACTUAL_TICK_PARITY_VALIDATION_20260916.json',
 'V10_POST_HEAD_REGEN_VALIDATION_20260916.json',
]
REQUIRED_DOCS=[
 'V10_REPRODUCIBILITY_LEDGER_AND_MODEL_REGEN_CHECKPOINT_20260916.md',
 'V10_DATA_AND_LEDGER_MANIFEST_20260916.md',
 'V10_REGENERATION_RESULTS_20260916.md',
]
FORBIDDEN_LIVE_FEATURES={'answer_final_run_len','answer_future_remaining_h4','final_run_len','natural_child_pnl_m1','R_child'}

def sha(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rows(p:Path):
 with p.open(encoding='utf-8-sig',newline='') as f:
  r=csv.reader(f);next(r,None);return sum(1 for _ in r)
def read_json(p:Path):return json.loads(p.read_text(encoding='utf-8-sig'))
def close(a,b,tol=0.02):return math.isfinite(float(a)) and abs(float(a)-float(b))<=tol

def norm_time(s): return str(s).replace('.', '-')
def effective_from_detail(r):
 m=re.search(r'\beffective_ts=(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\b',r.get('entry_detail',''))
 return m.group(1) if m else r.get('decision_time','')

def main():
 ap=argparse.ArgumentParser(description='Validate the V10 reproducibility ledger/model-regeneration pack after application.')
 ap.add_argument('repo')
 ap.add_argument('--structural-only',action='store_true',help='Skip exact economics checks; intended only for package application smoke tests on a mock repo.')
 args=ap.parse_args();repo=Path(args.repo).resolve();results=repo/'docs/ea/v10/results';raw=results/'raw'
 problems=[];facts={'repo':str(repo),'raw_sha256':{},'row_counts':{}}

 # Raw evidence identity.
 for name,h in EXPECTED_RAW.items():
  p=raw/name
  if not p.exists():problems.append(f'missing raw evidence: {p}')
  else:
   got=sha(p);facts['raw_sha256'][name]=got
   if got!=h:problems.append(f'raw hash mismatch: {name}: {got} != {h}')

 # Fixed-row artifacts.
 for name,n in EXPECTED_ROWS.items():
  p=results/name
  if not p.exists():problems.append(f'missing result: {p}');continue
  got=rows(p);facts['row_counts'][name]=got
  if got!=n:problems.append(f'row count mismatch {name}: {got} != {n}')

 # Generated artifacts that must not be empty.
 for name in REQUIRED_NONEMPTY:
  p=results/name
  if not p.exists():problems.append(f'missing generated result: {p}');continue
  got=rows(p);facts['row_counts'][name]=got
  if got<=0:problems.append(f'empty generated result: {name}')

 for name in REQUIRED_JSON:
  p=results/name
  if not p.exists():problems.append(f'missing validation receipt: {p}')
  else:
   try:read_json(p)
   except Exception as e:problems.append(f'invalid JSON {name}: {e}')

 for name in REQUIRED_DOCS:
  p=repo/'docs/ea/v10'/name
  if not p.exists():problems.append(f'missing document: {p}')

 # Validate the precomputed execution facts.
 p=results/'V10_BOUNDED_M3_ACTUAL_TICK_LEDGER_VALIDATION_20260916.json'
 if p.exists():
  j=read_json(p);exp={'selected_signals':1159,'fills':984,'entry_rejects':174,'sl_already_touched_rejects':1,'affected_exit_reject_positions':131,'distinct_exit_reject_timestamps':84,'raw_exit_reject_events':134,'filled_units':1966}
  for k,v in exp.items():
   if int(j.get(k,-999))!=v:problems.append(f'execution validation mismatch {k}: {j.get(k)} != {v}')
  if not close(j.get('filled_pnl',float('nan')),16220.67):problems.append(f'filled_pnl mismatch: {j.get("filled_pnl")} != 16220.67')

 p=results/'V10_BOUNDED_M3_ACTUAL_TICK_EXTENDED_VALIDATION_20260916.json'
 if p.exists():
  j=read_json(p);exp={'exit_reject_events':134,'exit_reject_incidents':84,'pending_exit_affected_positions':131,'structural_sl_positions':252,'overlap_episodes':33}
  for k,v in exp.items():
   if int(j.get(k,-999))!=v:problems.append(f'extended validation mismatch {k}: {j.get(k)} != {v}')
  if not close(j.get('max_gross_units',float('nan')),16.0,1e-9):problems.append('max_gross_units must equal 16')
  if not close(j.get('overlap_hours',float('nan')),311.0125,1e-6):problems.append('overlap_hours must equal 311.0125')

 # Causal feature receipt and source identities.
 p=results/'V10_POST_HEAD_SELECTED_SIGNAL_FEATURE_LEDGER_20260916.validation.json'
 if p.exists():
  j=read_json(p)
  if int(j.get('rows',-1))!=1159:problems.append('feature receipt rows must equal 1159')
  if int(j.get('direction_mismatch',-1))!=0:problems.append('feature receipt direction_mismatch must equal 0')
  if set(j.get('answer_sheet_columns',[]))!={'answer_final_run_len','answer_future_remaining_h4'}:problems.append('unexpected answer-sheet column declaration')
  source_hashes={
   'events':'eea7f54a4f0a70aa3c3ea52b38163f95fe8f79de93cdf0ccf8d73cc8fcc91f69',
   'm15':'245902105a2c36a627768f979584984944aabc9e62dfa3cfc9acb3198544c269',
   'm30':'8a3124d0f67ec6f8729b495011899cd4ca4fb5fd723dce7998f09614a12a1022',
   'h1':'c1d9f63f8af4d7dddd9e20e6eb124dc71de51015384b9c61a772d5981c7be52c',
   'h4':'5e12fa91f974c0f15e340ea8116bd9168fc6821e6309592cee1a7e197675de09'}
  for k,v in source_hashes.items():
   if j.get('hashes',{}).get(k)!=v:problems.append(f'feature source hash mismatch: {k}')

 # Decision-clock parity: research decision/effective_ts is distinct from actual fill/event time.
 bp=results/'V10_BOUNDED_M3_ENTRY_LEDGER_2025_2026.csv'; ep=results/'V10_BOUNDED_M3_ACTUAL_TICK_SIGNAL_EXECUTION_LEDGER_20260916.csv'; fp=results/'V10_POST_HEAD_SELECTED_SIGNAL_FEATURE_LEDGER_20260916.csv'
 if bp.exists() and ep.exists() and fp.exists():
  with bp.open(encoding='utf-8-sig',newline='') as f: br=[r for r in csv.DictReader(f) if float(r.get('W') or 0)>0]
  with ep.open(encoding='utf-8-sig',newline='') as f: er=list(csv.DictReader(f))
  with fp.open(encoding='utf-8-sig',newline='') as f: fr=list(csv.DictReader(f))
  if len(br)==len(er)==len(fr)==1159:
   shifted=0;max_shift=0.0
   from datetime import datetime
   def pdt(x): return datetime.strptime(norm_time(x),'%Y-%m-%d %H:%M:%S')
   for sid,(b0,e0,f0) in enumerate(zip(br,er,fr)):
    bt=norm_time(b0['decision_ts']); eff=norm_time(effective_from_detail(e0)); ft=norm_time(f0['decision_time'])
    if bt!=eff: problems.append(f'effective decision mismatch sid={sid}: {bt} != {eff}'); break
    if bt!=norm_time(e0['decision_time']): problems.append(f'execution canonical decision mismatch sid={sid}: {bt} != {e0["decision_time"]}'); break
    if bt!=ft: problems.append(f'feature canonical decision mismatch sid={sid}: {bt} != {f0["decision_time"]}'); break
    evt=e0.get('entry_event_time','')
    if evt:
     d=(pdt(evt)-pdt(bt)).total_seconds()
     if d<0: problems.append(f'entry event precedes decision sid={sid}: {d}s'); break
     if d>0: shifted+=1;max_shift=max(max_shift,d)
   facts['decision_clock']={'shifted_event_rows':shifted,'max_event_lag_seconds':max_shift}

 # Model coefficients must explicitly identify the selected population and cannot leak answer/outcome fields.
 cp=results/'V10_POST_HEAD_REGEN_MODEL_COEFFICIENTS_20260916.csv'
 if cp.exists():
  with cp.open(encoding='utf-8-sig',newline='') as f: cr=list(csv.DictReader(f))
  if not cr:problems.append('empty coefficient ledger')
  for r in cr:
   if r.get('population')!='BOUNDED_M3_SELECTED':problems.append('coefficient population must be BOUNDED_M3_SELECTED');break
   if r.get('feature') in FORBIDDEN_LIVE_FEATURES:problems.append(f'forbidden live feature in model: {r.get("feature")}');break

 # Full validation ties to the real GitHub bounded ledger rather than a structural mock.
 if not args.structural_only:
  bp=results/'V10_BOUNDED_M3_ENTRY_LEDGER_2025_2026.csv'
  if not bp.exists():problems.append('missing original bounded-m3 source ledger')
  else:
   with bp.open(encoding='utf-8-sig',newline='') as f: br=[r for r in csv.DictReader(f) if float(r.get('W') or 0)>0]
   if len(br)!=1159:problems.append(f'original selected bounded rows {len(br)} != 1159')
   units=sum(float(r['W']) for r in br);pnl=sum(float(r['natural_child_pnl_m1'])*float(r['W']) for r in br);rr=sum(float(r['R_child'])*float(r['W']) for r in br)
   facts['bounded_reference']={'rows':len(br),'units':units,'pnl':pnl,'R':rr}
   if not close(units,2313,1e-9):problems.append(f'bounded units mismatch: {units} != 2313')
   if not close(pnl,14827.57):problems.append(f'bounded PnL mismatch: {pnl} != 14827.57')
   if not close(rr,388.8765423128,1e-6):problems.append(f'bounded R mismatch: {rr}')
  pp=results/'V10_BOUNDED_M3_ACTUAL_TICK_PARITY_VALIDATION_20260916.json'
  if pp.exists():
   j=read_json(pp);checks={
    'rows':1159,'entry_reject_rows':175,'clean_fill_rows':853,'contaminated_fill_rows':131}
   for k,v in checks.items():
    if int(j.get(k,-1))!=v:problems.append(f'parity mismatch {k}: {j.get(k)} != {v}')
   numeric={'selected_reference_pnl':14827.57,'filled_reference_pnl':13495.44,'filled_actual_pnl':16220.67,'entry_reject_reference_pnl':1332.13,'clean_reference_pnl':11618.07,'clean_actual_pnl':11478.19,'contaminated_reference_pnl':1877.37,'contaminated_actual_pnl':4742.48}
   for k,v in numeric.items():
    if not close(j.get(k,float('nan')),v,0.08):problems.append(f'parity economics mismatch {k}: {j.get(k)} != ~{v}')

 bad=repo/'.v10_update_backup_20260916'
 if bad.exists():problems.append('obsolete in-repo backup directory still exists: .v10_update_backup_20260916')
 result={'ok':not problems,'structural_only':args.structural_only,'problems':problems,'facts':facts}
 print(json.dumps(result,ensure_ascii=False,indent=2))
 raise SystemExit(0 if not problems else 2)
if __name__=='__main__':main()
