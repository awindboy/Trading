#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,math,statistics
from pathlib import Path

def read(p):
 with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def f(x):
 try:return float(x)
 except:return 0.0
def wr(rows,pnlcol):return sum(f(r[pnlcol])>0 for r in rows)/len(rows) if rows else 0
def agg(rows,pnlcol='natural_child_pnl_m1',weightcol=None,rcol='R_child'):
 vals=[];rs=[];units=0
 for r in rows:
  w=f(r[weightcol]) if weightcol else 1.0;p=f(r[pnlcol])*w;rr=f(r[rcol])*w
  vals.append(p);rs.append(rr);units+=w
 gp=sum(max(0,x) for x in vals);gl=sum(min(0,x) for x in vals)
 return {'N':len(rows),'units':units,'pnl':sum(vals),'gross_profit':gp,'gross_loss':gl,'PF':gp/(-gl) if gl<0 else '', 'WR':sum(x>0 for x in vals)/len(vals) if vals else '', 'R':sum(rs),'avg_pnl':sum(vals)/len(vals) if vals else ''}
def write(path,rows):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8-sig',newline='') as g:
  w=csv.DictWriter(g,fieldnames=list(rows[0]) if rows else []);w.writeheader();w.writerows(rows)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--merged',required=True);ap.add_argument('--out-dir',required=True);args=ap.parse_args();out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
 allrows=read(args.baseline);selected=[r for r in allrows if f(r.get('W'))>0];merged=read(args.merged)
 # Oracle/non-oracle 1-unit economics across all eligible opportunities
 econ=[]
 for name,pred in [('ORACLE',lambda r:r.get('oracle_early_third','').lower()=='true'),('NON_ORACLE',lambda r:r.get('oracle_early_third','').lower()!='true'),('ALL1',lambda r:True)]:
  a=agg([r for r in allrows if pred(r)]);a={'group':name,**a};econ.append(a)
 write(out/'V10_POST_HEAD_ORACLE_NONORACLE_ECONOMICS_REGEN_20260916.csv',econ)
 # non-oracle final run-length bins
 bins=[('L1_2',lambda L:L<=2),('L3_5',lambda L:3<=L<=5),('L6_8',lambda L:6<=L<=8),('L9_11',lambda L:9<=L<=11),('L12_PLUS',lambda L:L>=12)]
 rr=[]
 non=[r for r in allrows if r.get('oracle_early_third','').lower()!='true']
 for name,pred in bins:
  a=agg([r for r in non if pred(int(float(r['final_run_len'])))]);rr.append({'run_len_bin':name,**a})
 write(out/'V10_POST_HEAD_NONORACLE_RUN_LENGTH_ECONOMICS_REGEN_20260916.csv',rr)
 # selected TP/FP/FN decomposition
 s_tp=[r for r in selected if r.get('oracle_early_third','').lower()=='true'];s_fp=[r for r in selected if r.get('oracle_early_third','').lower()!='true']
 # FN is oracle opportunity with W=0
 fn=[r for r in allrows if r.get('oracle_early_third','').lower()=='true' and f(r.get('W'))==0]
 decomp=[]
 for name,rows,weighted in [('SELECTED_TRUE_POSITIVE',s_tp,True),('SELECTED_FALSE_POSITIVE',s_fp,True),('MISSED_ORACLE_1X',fn,False)]:
  a=agg(rows,weightcol='W' if weighted else None);decomp.append({'group':name,**a})
 write(out/'V10_POST_HEAD_BOUNDED_FP_FN_DECOMPOSITION_REGEN_20260916.csv',decomp)
 # k1 universal scaling scan on selected bounded entries only
 scale_rows=[]
 for scale in (1.0,0.75,0.5,0.25,0.0):
  pnl=rrr=units=0.0;gp=gl=0.0
  for r in selected:
   w=f(r['W']);
   if int(float(r['run_seq']))==1:w*=scale
   p=f(r['natural_child_pnl_m1'])*w;rv=f(r['R_child'])*w
   pnl+=p;rrr+=rv;units+=w;gp+=max(0,p);gl+=min(0,p)
  scale_rows.append({'k1_scale':scale,'units':units,'pnl':pnl,'PF':gp/(-gl) if gl<0 else '', 'R':rrr})
 write(out/'V10_POST_HEAD_BOUNDED_K1_SCALE_SCAN_REGEN_20260916.csv',scale_rows)
 # morphology medians from selected feature ledger: exact formulas now persisted.
 mrows=[]
 specs=[('K1_STOP',1,lambda L:L==1),('K1_SURVIVE',1,lambda L:L>1),('K2_STOP',2,lambda L:L==2),('K2_SURVIVE',2,lambda L:L>2)]
 cols=['h1_aligned_fraction','h1_transition_rate','h1_mean_opp_run_len','h1_current_signed_streak','h1_body_to_range_mean_signed','h1_opposing_wick_share_mean',
       'm30_aligned_fraction','m30_transition_rate','m30_mean_same_run_len','m30_mean_opp_run_len','m30_current_signed_streak','m30_body_to_range_mean_signed','m30_opposing_wick_share_mean',
       'm15_aligned_fraction','m15_transition_rate','m15_mean_same_run_len','m15_mean_opp_run_len','m15_current_signed_streak','m15_body_to_range_mean_signed','m15_opposing_wick_share_mean']
 for group,stage,pred in specs:
  sub=[r for r in merged if int(float(r['run_seq']))==stage and pred(int(float(r['final_run_len'])))]
  for c in cols:
   vals=[f(r[c]) for r in sub];mrows.append({'group':group,'stage':stage,'N':len(sub),'feature':c,'median':statistics.median(vals) if vals else '', 'mean':sum(vals)/len(vals) if vals else ''})
 write(out/'V10_POST_HEAD_MORPHOLOGY_MEDIANS_REGEN_20260916.csv',mrows)
 print('generated',len(econ),len(rr),len(decomp),len(scale_rows),len(mrows))
if __name__=='__main__':main()
