#!/usr/bin/env python3
"""V3-003F raw-M1 closeout audit for interrupted H tests and mentor-wave semantic cross-check.

Depends on the committed V3-003C/D/E replay scripts in the repository.
Accepts discovery GOLD 2023-2025 only. Never reads 2022/2021.
"""
from __future__ import annotations
import argparse, importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent

def _load(name,fn):
    p=HERE/fn
    if not p.exists(): raise SystemExit(f"FAIL-CLOSED missing {p}")
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

e=_load("v3e","v3_003e_dual_module_repro.py")


def _enrich_source(E,src,source_name):
    c=e.c
    rr=c.dedupe_enriched(c.persistent_reactions(E['m1'],src),src)
    tr=c.build_triggers(rr,E['m1'],E['bars']['5min'],E['ends5'],E['own5'],E['chg5'])
    ev=c.evaluate(tr,E['m1']);ev['year']=ev.trigger_time.dt.year;ev['source_k']=2.0
    ev['m30_exp']=c.wave_expansion_at(ev.sweep_time,E['mw30'])
    ev['m30_owner']=c.state_at(ev.sweep_time,E['ends30'],E['own30']);ev['h1_owner']=c.state_at(ev.sweep_time,E['ends60'],E['own60'])
    ev['owner_agree']=(ev.m30_owner==ev.dir)&(ev.h1_owner==ev.dir)
    ev['delivery_state']=(ev.m30_exp>1.0)|ev.owner_agree
    ev['broken_m5_level']=np.where(ev.dir.to_numpy()==1,E['hlev5'][ev.trigger_m5_index.to_numpy(int)],E['llev5'][ev.trigger_m5_index.to_numpy(int)])
    ev['penetration']=(ev.liq_price-ev.sweep_extreme)*ev.dir
    ev['acceptance_margin']=(ev.trigger_close-ev.broken_m5_level)*ev.dir
    ev['strong_acceptance']=ev.acceptance_margin>ev.penetration
    ev=e.d.add_micro_path(ev,E['ends1'],E['own1'],E['chg1'])
    ev['d1_atr']=e.atr_at(ev.trigger_time,E['d1_av'],E['d1v'])
    ev['source_name']=source_name
    return ev,ev[ev.delivery_state&ev.strong_acceptance].copy().reset_index(drop=True)


def _h2(E,cand):
    q=e.fill_pullback(E,cand,0.5)
    meta=cand[['trigger_time','dir','liq_price','m30_exp','m30_owner','h1_owner','owner_agree','m1_direct_transfer']].copy()
    q=q.merge(meta,on=['trigger_time','dir'],how='left')
    q['direct_transfer']=q.m1_direct_transfer.astype(bool)
    q['both_branch']=(q.m30_exp>1)&q.owner_agree.astype(bool)
    q['base_R']=q.outcome.map({'TP5':5.0,'BE':0.0,'SL':-1.0})
    return q


def _body(E,r,tf):
    m=E['m1'];mt=m.index.to_numpy(dtype='datetime64[ns]');hi=m.high.to_numpy(float);lo=m.low.to_numpy(float);cl=m.close.to_numpy(float);sp=m.spread_px.to_numpy(float)
    d=int(r.dir);en=float(r.limit_entry);sl=float(r.sl_exec);risk=float(r.risk);liq=float(r.liq_price)
    fi=np.searchsorted(mt,np.datetime64(r.fill_time),side='left');hit3=False
    m5last={}
    if tf=='M5':
        for end in E['bars']['5min'].index+pd.Timedelta(minutes=5):
            i=np.searchsorted(mt,np.datetime64(end),side='left')-1
            if i>=0 and pd.Timestamp(mt[i])>=end-pd.Timedelta(minutes=5):m5last[i]=end
    for i in range(fi,len(mt)):
        if d==1: stop=lo[i]<=(en if hit3 else sl);fav=hi[i]-en
        else: stop=hi[i]+sp[i]>=(en if hit3 else sl);fav=en-(lo[i]+sp[i])
        if stop:return ('BE' if hit3 else 'SL',pd.Timestamp(mt[i]),0.0 if hit3 else -1.0,False)
        if fav>=5*risk:return ('TP5',pd.Timestamp(mt[i]),5.0,False)
        if not hit3 and fav>=3*risk:hit3=True
        check=(tf=='M1') or (tf=='M5' and i in m5last)
        if check:
            breach=(cl[i]<liq) if d==1 else (cl[i]>liq)
            if breach:
                px=cl[i] if d==1 else cl[i]+sp[i];rr=(px-en)*d/risk
                t=(pd.Timestamp(mt[i])+pd.Timedelta(minutes=1)) if tf=='M1' else pd.Timestamp(m5last[i])
                return (f'BODY_{tf}',t,rr,True)
    return ('CENSORED',pd.NaT,np.nan,False)


def _plus2(E,r):
    m=E['m1'];mt=m.index.to_numpy(dtype='datetime64[ns]');hi=m.high.to_numpy(float);lo=m.low.to_numpy(float);sp=m.spread_px.to_numpy(float)
    d=int(r.dir);en=float(r.limit_entry);sl=float(r.sl_exec);risk=float(r.risk);fi=np.searchsorted(mt,np.datetime64(r.fill_time),side='left')
    hit2=hit3=False
    for i in range(fi,len(mt)):
        if d==1:stop=lo[i]<=(en if hit3 else sl);fav=hi[i]-en
        else:stop=hi[i]+sp[i]>=(en if hit3 else sl);fav=en-(lo[i]+sp[i])
        if stop:
            if hit2:return ('BE' if hit3 else 'SL_AFTER_2',pd.Timestamp(mt[i]),1.0+(0.0 if hit3 else -0.5),hit2,hit3)
            return ('SL',pd.Timestamp(mt[i]),-1.0,False,False)
        if fav>=5*risk:return ('TP5',pd.Timestamp(mt[i]),3.5,True,True)
        if fav>=2*risk:hit2=True
        if fav>=3*risk:hit3=True
    return ('CENSORED',pd.NaT,np.nan,hit2,hit3)


def _mentor_l(E,ev,cand):
    ce=e.add_episode(cand,E);rows=[]
    for r in ce[(ce.win1==0)&ce.state_active_trigger].itertuples(index=False):
        end=r.episode_end if pd.notna(r.episode_end) else pd.Timestamp.max
        if pd.notna(r.episode_end) and r.resolved_at>=end:continue
        g=ev[(ev.dir==r.dir)&(ev.trigger_time>r.resolved_at)&(ev.trigger_time<end)].copy()
        g=g[g.liq_price<r.liq_price] if r.dir==1 else g[g.liq_price>r.liq_price]
        if not len(g):continue
        x=g.sort_values('trigger_time').iloc[0].to_dict();x.update({'prior_trigger_time':r.trigger_time,'prior_resolved_at':r.resolved_at,'prior_liq_price':r.liq_price,'prior_sl':r.sl_exec,'episode_id':r.episode_id,'support_k':'MENTOR','support_n':1,'prior_k':np.nan,'kdist':np.nan})
        rows.append(x)
    if not rows:return pd.DataFrame()
    q=pd.DataFrame(rows).sort_values(['trigger_time','dir','prior_resolved_at']).drop_duplicates(['trigger_time','dir'],keep='last')
    L=e.eval_l(E,q.reset_index(drop=True));return e.add_l_protected_runner(E,L,partial=0.5)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('data',type=Path);ap.add_argument('--out',type=Path,default=Path('v3_003f_raw_closeout_out'));args=ap.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    E=e.base_env(args.data);years=set(E['m1'].index.year.unique())
    if not years.issubset({2023,2024,2025}):raise SystemExit(f'FAIL-CLOSED discovery years only, got {years}')
    byk={k:e.build_for_k(E,k) for k in [1.5,2.0,2.5]}
    assert byk[2.0][2].groupby('year').size().to_dict()=={2023:40,2024:29,2025:27}
    H=_h2(E,byk[2.0][2]);H=H[H.direct_transfer].reset_index(drop=True);assert len(H)==44
    rows=[]
    for r in H.itertuples(index=False):
        m1=_body(E,r,'M1');m5=_body(E,r,'M5');p2=_plus2(E,r)
        rows.append({**r._asdict(),'m1_body_terminal':m1[0],'m1_body_time':m1[1],'m1_body_R':m1[2],'m1_body_used':m1[3],'m5_body_terminal':m5[0],'m5_body_time':m5[1],'m5_body_R':m5[2],'m5_body_used':m5[3],'plus2_terminal':p2[0],'plus2_time':p2[1],'plus2_R':p2[2],'plus2_hit2':p2[3],'plus2_hit3':p2[4]})
    close=pd.DataFrame(rows);close.to_csv(out/'h_interrupted_experiment_detail.csv',index=False)

    src=e.c.mentor_waves(E['bars']['15min'],15);mev,mcand=_enrich_source(E,src,'MENTOR_WAVE')
    MH=_h2(E,mcand);MH['branch']=np.select([MH.both_branch,(MH.m30_exp>1)&(~MH.owner_agree.astype(bool)),(MH.m30_exp<=1)&MH.owner_agree.astype(bool)],['BOTH','EXP_ONLY','OWNER_ONLY'],default='NEITHER');MH.to_csv(out/'mentor_h_crosscheck.csv',index=False)
    ML=_mentor_l(E,mev,mcand);ML.to_csv(out/'mentor_l_crosscheck.csv',index=False)

    print('PARITY PASS H2',len(H),int((H.outcome=='TP5').sum()),int((H.outcome=='SL').sum()),int((H.outcome=='BE').sum()))
    print('M1 body EV',float(close.m1_body_R.mean()),'used',int(close.m1_body_used.sum()))
    print('M5 body EV',float(close.m5_body_R.mean()),'used',int(close.m5_body_used.sum()))
    print('+2 half EV',float(close.plus2_R.mean()),'positive',float((close.plus2_R>0).mean()))
    print('mentor H direct/non-direct',int(MH.direct_transfer.sum()),int((~MH.direct_transfer).sum()))
    print('mentor L',len(ML))

if __name__=='__main__':main()
