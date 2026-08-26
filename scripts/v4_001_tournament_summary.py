#!/usr/bin/env python3
"""Pre-registered V4-001 claim-grade tournament summary.

R0 = frozen causal linear control.
R1 = supervised CausalPatchPolicy.
R2 = self-supervised MarketJEPA + frozen linear probe.

R3 Kronos and R4 MOMENT are transfer diagnostics only and can never promote a V4
candidate by themselves because their pretraining corpora are not clean V4 OOS data.
"""
from pathlib import Path
import argparse,json,statistics

LINEAR={
 'GOLD#':0.5097969644143469,
 'BTCUSD#':0.5026543919593831,
 'XAUEUR#':0.5106438502882269,
 'USDJPY#':0.5072127119502017,
}


def load_run(root:Path,name:str):
 v=json.loads((root/'stage_a_verdict.json').read_text(encoding='utf-8'))
 s=json.loads((root/'stage_a_summary.json').read_text(encoding='utf-8'))
 if s.get('diagnostic_non_authority'):
  raise SystemExit(f'FAIL-CLOSED: {name} is diagnostic/non-authority')
 lomo={sym:s['folds']['LOMO_FUTURE_2025_'+sym]['auc15'] for sym in LINEAR}
 deltas={s:lomo[s]-LINEAR[s] for s in LINEAR}
 return {'name':name,'verdict':v['verdict'],'primary_auc':s['folds']['TEMPORAL_2025_PRIMARY']['auc15'],
         'temporal_2024_auc':s['folds']['TEMPORAL_2024']['auc15'],'lomo_auc':lomo,'lomo_delta_vs_linear':deltas,
         'median_lomo_delta':float(statistics.median(deltas.values()))}


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--r1',type=Path,required=True);ap.add_argument('--r2',type=Path,required=True);ap.add_argument('--out',type=Path,default=Path('V4_001_TOURNAMENT_SUMMARY.json'));a=ap.parse_args()
 r1=load_run(a.r1,'R1_CausalPatchPolicy');r2=load_run(a.r2,'R2_MarketJEPA')
 passed=[x for x in [r1,r2] if x['verdict']=='PASS']
 if not passed:
  decision='NO_CLAIM_GRADE_PASS';selected=None;next_step='V4-001B and RL remain locked. Redesign only inside open development allocation.'
 else:
  # Pre-registered lexicographic selector: transfer improvement first, then primary future AUC.
  passed.sort(key=lambda x:(x['median_lomo_delta'],x['primary_auc']),reverse=True)
  selected=passed[0]['name'];decision='CLAIM_GRADE_STAGE_A_PASS';next_step='Freeze the selected representation before opening any external-market validation data.'
 out={'decision':decision,'selected':selected,'selection_rule':'PASS gate first; then higher median strict-LOMO AUC delta vs frozen R0; tie -> higher 2025 pooled AUC',
      'R0_linear_lomo':LINEAR,'R1':r1,'R2':r2,'R3_R4_authority':'TRANSFER_DIAGNOSTIC_ONLY','next_step':next_step}
 a.out.write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
