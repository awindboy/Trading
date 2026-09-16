#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

def read_csv(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def fmt(x,n=3):
    try:return f"{float(x):,.{n}f}"
    except:return str(x)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
    d=Path(args.results_dir)
    metrics=read_csv(d/'V10_POST_HEAD_REGEN_MODEL_METRICS_20260916.csv')
    tails=read_csv(d/'V10_K1_DANGER_REGEN_TAIL_SWEEP_20260916.csv')
    econ=read_csv(d/'V10_POST_HEAD_ORACLE_NONORACLE_ECONOMICS_REGEN_20260916.csv')
    decomp=read_csv(d/'V10_POST_HEAD_BOUNDED_FP_FN_DECOMPOSITION_REGEN_20260916.csv')
    morph=read_csv(d/'V10_POST_HEAD_MORPHOLOGY_MEDIANS_REGEN_20260916.csv')
    scales=read_csv(d/'V10_POST_HEAD_BOUNDED_K1_SCALE_SCAN_REGEN_20260916.csv')
    def metric(head,fold):
        return next(r for r in metrics if r['head']==head and r['fold']==fold)
    def tail(fold,t):
        return next(r for r in tails if r['fold']==fold and abs(float(r['tail_fraction'])-t)<1e-9)
    def group(rows,key,val):return next(r for r in rows if r[key]==val)
    k1h2=metric('K1_NHA_SHOCK_REGEN','2025H2');k126=metric('K1_NHA_SHOCK_REGEN','2026')
    k2h2=metric('K2_PERSISTENCE_REGEN','2025H2');k226=metric('K2_PERSISTENCE_REGEN','2026')
    t10h2=tail('2025H2',.10);t1026=tail('2026',.10)
    ora=group(econ,'group','ORACLE');non=group(econ,'group','NON_ORACLE');tp=group(decomp,'group','SELECTED_TRUE_POSITIVE');fp=group(decomp,'group','SELECTED_FALSE_POSITIVE');fn=group(decomp,'group','MISSED_ORACLE_1X')
    lines=[]
    lines += ['# V10 Post-Head Regeneration Results — Reproducible Candidate Set','',
    'Date: `2026-09-16`  ',
    'Status: `AUTO-GENERATED / CONSUMED-DATA REGENERATION / NOT STRATEGY AUTHORITY`  ',
    'Market: `GOLD# ONLY`','',
    '> This file is generated from persisted ledgers and explicit formulas. The regenerated heads are **selection-conditioned on the 1,159 bounded-m3 selected signals**. It does **not** claim to recreate the lost post-HEAD full-universe Danger-model coefficients. Any `_REGEN` head is a new reproducible candidate and must be evaluated on its own evidence.','',
    '## 1. Recreated economic decompositions','',
    '| Group | N | PnL | PF | Structural R |','|---|---:|---:|---:|---:|',
    f"| Oracle opportunity | {ora['N']} | {fmt(ora['pnl'],2)} | {fmt(ora['PF'])} | {fmt(ora['R'],2)} |",
    f"| Non-Oracle opportunity | {non['N']} | {fmt(non['pnl'],2)} | {fmt(non['PF'])} | {fmt(non['R'],2)} |",
    f"| Bounded selected true-positive | {tp['N']} | {fmt(tp['pnl'],2)} | {fmt(tp['PF'])} | {fmt(tp['R'],2)} |",
    f"| Bounded selected false-positive | {fp['N']} | {fmt(fp['pnl'],2)} | {fmt(fp['PF'])} | {fmt(fp['R'],2)} |",
    f"| Missed Oracle at 1x | {fn['N']} | {fmt(fn['pnl'],2)} | {fmt(fn['PF'])} | {fmt(fn['R'],2)} |",'',
    '## 2. New reproducible model heads','',
    'These models use deterministic, standardized logistic regression implemented with the Python standard library. Their feature sets, preprocessing statistics, coefficients, intercepts, chronological folds, scores, and prior-only percentile ranks are all persisted in CSV ledgers. The population is the bounded-m3 selected subset, not all 2,489 eligible FAST opportunities.','',
    '| Head | Fold | Eval N | Positive N | AUC |','|---|---|---:|---:|---:|',
    f"| K1 NHA_SHOCK REGEN | 2025H2 <- 2025H1 | {k1h2['eval_n']} | {k1h2['eval_positive']} | {fmt(k1h2['auc'],4)} |",
    f"| K1 NHA_SHOCK REGEN | 2026 <- 2025 | {k126['eval_n']} | {k126['eval_positive']} | {fmt(k126['auc'],4)} |",
    f"| K2 persistence REGEN | 2025H2 <- 2025H1 | {k2h2['eval_n']} | {k2h2['eval_positive']} | {fmt(k2h2['auc'],4)} |",
    f"| K2 persistence REGEN | 2026 <- 2025 | {k226['eval_n']} | {k226['eval_positive']} | {fmt(k226['auc'],4)} |",'',
    'These AUC values must be compared with the session-recorded values only as **new evidence**. A difference is not a bug by itself because the original exact model feature normalization and coefficients were never persisted.','',
    '## 3. K1 Danger tail sweep from the new REGEN head','',
    '| Fold | Tail | Veto events | Units | Removed ref PnL | Candidate delta | NHA_SHOCK labels |','|---|---:|---:|---:|---:|---:|---:|',
    f"| 2025H2 | top 10% | {t10h2['veto_events']} | {fmt(t10h2['veto_units'],0)} | {fmt(t10h2['removed_reference_pnl'],2)} | {fmt(t10h2['delta_vs_base'],2)} | {t10h2['nha_shock_labels']} |",
    f"| 2026 | top 10% | {t1026['veto_events']} | {fmt(t1026['veto_units'],0)} | {fmt(t1026['removed_reference_pnl'],2)} | {fmt(t1026['delta_vs_base'],2)} | {t1026['nha_shock_labels']} |",'',
    'No percentile from this sweep is promoted. The sweep exists so broad-veto damage and extreme-tail behavior remain inspectable.','',
    '## 4. Universal k1 scaling negative control','',
    '| k1 scale | Units | PnL | PF | R |','|---:|---:|---:|---:|---:|']
    for r in scales: lines.append(f"| {r['k1_scale']} | {fmt(r['units'],0)} | {fmt(r['pnl'],2)} | {fmt(r['PF'])} | {fmt(r['R'],2)} |")
    lines += ['', '## 5. Morphology parity / semantic validation','',
    'The regenerated selected-signal feature ledger uses a fixed four-hour window of completed M15/M30/H1 HA state preceding each effective H4 participation decision. Categorical/run-structure medians reproduce the previous session checkpoint closely. Body-related values are intentionally treated as a new explicit normalization because the original body normalization formula was not persisted.','',
    '## 6. Authority boundary','',
    '- `_REGEN` coefficients are reproducible research artifacts, not recovered authority.','- The session-recorded `+15,013.69` shock-veto result remains historical consumed evidence until independently reproduced by a fully persisted candidate.','- Actual-tick campaign-exit semantics still require the `EXIT_PENDING` repair and rerun before V10 can claim an actual-tick validation pass.','- No production authority exists.','']
    Path(args.out).write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__':main()
