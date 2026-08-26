#!/usr/bin/env python3
"""Apply the frozen V4-001A information-skill gate to an official Stage-A run."""
from pathlib import Path
import argparse,json

LINEAR={
 'GOLD#':0.5097969644143469,
 'BTCUSD#':0.5026543919593831,
 'XAUEUR#':0.5106438502882269,
 'USDJPY#':0.5072127119502017,
}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage-a',type=Path,required=True);ap.add_argument('--out',type=Path,default=None);args=ap.parse_args()
 q=json.loads((args.stage_a/'stage_a_summary.json').read_text())
 if q.get('diagnostic_non_authority'):
  raise SystemExit('FAIL-CLOSED: diagnostic/non-authority run cannot receive a Stage-A verdict')
 f=q['folds'];p=f['TEMPORAL_2025_PRIMARY'];s=f['TEMPORAL_2024']
 lomo={sym:f['LOMO_FUTURE_2025_'+sym] for sym in LINEAR}
 checks={}
 checks['primary_weekly_block_auc_ci_lower_gt_0_5']=p['weekly_block_auc95'][0]>0.5
 checks['primary_2025_target_breadth_3of4']=sum(v['auc15']>0.5 for v in p['by_target'].values())>=3
 checks['strict_lomo_positive_3of4']=sum(v['auc15']>0.5 for v in lomo.values())>=3
 checks['strict_lomo_beats_linear_3of4']=sum(lomo[sym]['auc15']>LINEAR[sym] for sym in LINEAR)>=3
 checks['primary_ece10_le_0_05']=p['ece10']<=0.05
 checks['secondary_temporal_2024_auc_gt_0_5']=s['auc15']>0.5
 verdict='PASS' if all(checks.values()) else 'FAIL'
 out={'verdict':verdict,'checks':checks,'linear_lomo_reference':LINEAR,'primary_temporal_2025':p,'secondary_temporal_2024':s,
      'strict_lomo':{k:{'neural_auc':lomo[k]['auc15'],'linear_auc':LINEAR[k],'delta':lomo[k]['auc15']-LINEAR[k]} for k in LINEAR},
      'next_authority':'V4-001B may be opened only after PASS' if verdict=='PASS' else 'V4-001B/RL remain locked; redesign only inside development data'}
 path=args.out or (args.stage_a/'stage_a_verdict.json');path.write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
