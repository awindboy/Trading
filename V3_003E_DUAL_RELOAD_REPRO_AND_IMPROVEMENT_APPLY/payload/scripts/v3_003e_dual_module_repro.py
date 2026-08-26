#!/usr/bin/env python3
from pathlib import Path
import argparse, importlib.util, math, sys, json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
OUT=Path('.')

def _load_local(name, filename):
    p=HERE/filename
    if not p.exists():
        raise SystemExit(f'FAIL-CLOSED: missing required helper: {p}')
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

c=_load_local('v3c','v3_003c_reload_state_acceptance_probe.py')
d=_load_local('v3d','v3_003d_correction_completion_probe.py')

def base_env(data_path):
    m1=c.load_gold(Path(data_path))
    years=set(m1.index.year.unique())
    if not years.issubset({2023,2024,2025}):
        raise SystemExit(f'FAIL-CLOSED: discovery replay accepts 2023-2025 only, got {sorted(years)}')
    bars={r:c.resample_ohlc(m1,r) for r in ['5min','15min','30min','60min']}
    for b in bars.values(): b['atr14']=c.atr_series(b)
    piv={r:c.pivot_events(bars[r],2,{'5min':5,'15min':15,'30min':30,'60min':60}[r]) for r in bars}
    ends5,own5,chg5,hlev5,llev5=c.bos_owner_with_break(bars['5min'],piv['5min'],5)
    ends30,own30,_,_,_=c.bos_owner_with_break(bars['30min'],piv['30min'],30)
    ends60,own60,_,_,_=c.bos_owner_with_break(bars['60min'],piv['60min'],60)
    mw30=c.mentor_waves(bars['30min'],30)
    ends1,own1,chg1=d.build_m1_owner(m1)
    t30=ends30; exp_grid=c.wave_expansion_at(pd.to_datetime(t30),mw30); h1_on30=c.state_at(pd.to_datetime(t30),ends60,own60)
    up=(exp_grid>1.0)|((own30==1)&(h1_on30==1)); dn=(exp_grid>1.0)|((own30==-1)&(h1_on30==-1))
    # trailing D1 ATR available only next day open
    d1=c.resample_ohlc(m1,'1D'); d1['atr14']=c.atr_series(d1)
    d1_av=(d1.index+pd.Timedelta(days=1)).to_numpy(dtype='datetime64[ns]'); d1v=d1.atr14.to_numpy(float)
    return locals()

def atr_at(times,av,vals):
    pos=np.searchsorted(av,np.asarray(times,dtype='datetime64[ns]'),side='right')-1
    out=np.full(len(pos),np.nan); ok=pos>=0; out[ok]=vals[pos[ok]]
    return out

def build_for_k(E,k):
    m1=E['m1']; bars=E['bars']
    src=c.dc_swing_events(bars['15min'],k,15)
    rr=c.dedupe_enriched(c.persistent_reactions(m1,src),src)
    tr=c.build_triggers(rr,m1,bars['5min'],E['ends5'],E['own5'],E['chg5'])
    ev=c.evaluate(tr,m1); ev['year']=ev.trigger_time.dt.year
    ev['source_k']=k
    ev['m30_exp']=c.wave_expansion_at(ev.sweep_time,E['mw30'])
    ev['m30_owner']=c.state_at(ev.sweep_time,E['ends30'],E['own30']); ev['h1_owner']=c.state_at(ev.sweep_time,E['ends60'],E['own60'])
    ev['delivery_state']=(ev.m30_exp>1.0)|((ev.m30_owner==ev.dir)&(ev.h1_owner==ev.dir))
    ev['broken_m5_level']=np.where(ev.dir.to_numpy()==1,E['hlev5'][ev.trigger_m5_index.to_numpy(int)],E['llev5'][ev.trigger_m5_index.to_numpy(int)])
    ev['penetration']=(ev.liq_price-ev.sweep_extreme)*ev.dir
    ev['acceptance_margin']=(ev.trigger_close-ev.broken_m5_level)*ev.dir
    ev['strong_acceptance']=ev.acceptance_margin>ev.penetration
    ev=d.add_micro_path(ev,E['ends1'],E['own1'],E['chg1'])
    ev['d1_atr']=atr_at(ev.trigger_time,E['d1_av'],E['d1v'])
    cand=ev[ev.delivery_state&ev.strong_acceptance].copy().reset_index(drop=True)
    return src,ev,cand

def state_segment(t,direction,E):
    tgrid=E['t30']; arr=E['up'] if direction==1 else E['dn']
    pos=np.searchsorted(tgrid,np.datetime64(t),side='right')-1
    if pos<0 or not arr[pos]: return None
    s=pos
    while s>0 and arr[s-1]: s-=1
    e=pos+1
    while e<len(arr) and arr[e]: e+=1
    st=pd.Timestamp(tgrid[s]); en=pd.Timestamp(tgrid[e]) if e<len(arr) else pd.NaT
    return st,en

def add_episode(cand,E):
    q=cand.copy(); starts=[];ends=[];ids=[];active=[]
    for r in q.itertuples(index=False):
        seg=state_segment(r.trigger_time,r.dir,E)
        if seg is None: starts.append(pd.NaT);ends.append(pd.NaT);ids.append(None);active.append(False)
        else:
            st,en=seg;starts.append(st);ends.append(en);ids.append(f'{r.dir}:{st.isoformat()}');active.append(True)
    q['episode_start']=starts;q['episode_end']=ends;q['episode_id']=ids;q['state_active_trigger']=active
    return q

def module_l_candidates(E,byk):
    rows=[]
    for k,(src,ev,cand) in byk.items():
        ce=add_episode(cand,E)
        losers=ce[(ce.win1==0)&ce.state_active_trigger].copy()
        for r in losers.itertuples(index=False):
            end=r.episode_end if pd.notna(r.episode_end) else pd.Timestamp.max
            if pd.notna(r.episode_end) and r.resolved_at>=end: continue
            g=ev[(ev.dir==r.dir)&(ev.trigger_time>r.resolved_at)&(ev.trigger_time<end)].copy()
            if r.dir==1: g=g[g.liq_price<r.liq_price]
            else: g=g[g.liq_price>r.liq_price]
            if not len(g): continue
            x=g.sort_values('trigger_time').iloc[0]
            z=x.to_dict(); z.update({
                'prior_k':k,'prior_trigger_time':r.trigger_time,'prior_resolved_at':r.resolved_at,
                'prior_liq_price':r.liq_price,'prior_sl':r.sl_exec,'episode_id':r.episode_id,
            })
            rows.append(z)
    raw=pd.DataFrame(rows)
    if not len(raw): return raw,raw
    # physical requalification = same M5 trigger + direction. Use the most recent causal prior failure as predecessor.
    raw=raw.sort_values(['trigger_time','dir','prior_resolved_at','source_k'])
    out=[]
    for (tt,dr),g in raw.groupby(['trigger_time','dir'],sort=True):
        support=sorted(set(g.source_k.astype(float)))
        # most recent prior virtual failure; within ties prefer k=2 then nearer 2
        mx=g.prior_resolved_at.max(); gg=g[g.prior_resolved_at==mx].copy();gg['kdist']=(gg.source_k-2.0).abs();rep=gg.sort_values(['kdist','source_k']).iloc[0].to_dict()
        rep['support_k']='|'.join(map(lambda x:f'{x:g}',support)); rep['support_n']=len(support)
        out.append(rep)
    phys=pd.DataFrame(out).sort_values('trigger_time').reset_index(drop=True)
    return raw,phys

def eval_l(E,q):
    m1=E['m1'];mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);sp=m1.spread_px.to_numpy(float);cl=m1.close.to_numpy(float)
    rows=[]
    for r in q.itertuples(index=False):
        d0=int(r.dir); en=float(r.entry); sl=float(r.sl_exec); risk=float(r.risk); d1=float(r.d1_atr)
        checkpoint=min(risk,0.5*d1) if np.isfinite(d1) and d1>0 else risk
        ip=np.searchsorted(mt,np.datetime64(r.trigger_time),side='left')-1
        out='CENSORED';hit1=0;cp=0;when=None;mfe=0.0;mae=0.0
        for i in range(ip+1,len(mt)):
            if d0==1:
                stop=lo[i]<=sl; fav=hi[i]-en; adv=en-lo[i]
            else:
                ah=hi[i]+sp[i]; al=lo[i]+sp[i]; stop=ah>=sl;fav=en-al;adv=ah-en
            mfe=max(mfe,fav);mae=max(mae,adv)
            # conservative: stop wins same-bar race
            if stop: out='SL';when=pd.Timestamp(mt[i]);break
            if not cp and fav>=checkpoint: cp=1;when=pd.Timestamp(mt[i]);out='CHECKPOINT';break
        # full 1R separately before original SL
        for i in range(ip+1,len(mt)):
            if d0==1: stop=lo[i]<=sl;fav=hi[i]-en
            else: stop=hi[i]+sp[i]>=sl;fav=en-(lo[i]+sp[i])
            if stop: break
            if fav>=risk: hit1=1;break
        # exact mirror same risk + checkpoint absolute distance
        md=-d0
        if md==1: men=cl[ip]+sp[ip];msl=men-risk
        else: men=cl[ip];msl=men+risk
        mcp=0
        for i in range(ip+1,len(mt)):
            if md==1: stop=lo[i]<=msl;fav=hi[i]-men
            else: stop=hi[i]+sp[i]>=msl;fav=men-(lo[i]+sp[i])
            if stop: break
            if fav>=checkpoint: mcp=1;break
        rows.append({**r._asdict(),'checkpoint_abs':checkpoint,'checkpoint_r':checkpoint/risk,'checkpoint_hit':cp,'full1_hit':hit1,'mirror_checkpoint_hit':mcp,'checkpoint_at':when,'path_mfe_abs':mfe,'path_mae_abs':mae})
    return pd.DataFrame(rows)

def fill_pullback(E,cand,fraction):
    m1=E['m1'];mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);sp=m1.spread_px.to_numpy(float)
    rows=[]
    clean=cand[cand.m1_clean_path==True].copy()
    for r in clean.itertuples(index=False):
        d0=int(r.dir)
        chart=float(r.trigger_close - d0*fraction*abs(r.trigger_close-r.broken_m5_level))
        trig_sp=(float(r.entry)-float(r.trigger_close)) if d0==1 else 0.0
        limit=chart+trig_sp if d0==1 else chart
        sl=float(r.sl_exec); risk=abs(limit-sl)
        if risk<=0: continue
        # must improve price vs trigger reference
        if (d0==1 and limit>=r.entry) or (d0==-1 and limit<=r.entry): continue
        st=np.searchsorted(mt,np.datetime64(r.trigger_time),side='right')
        end=np.searchsorted(mt,np.datetime64(r.resolved_at),side='right')
        fi=None
        for i in range(st,min(end,len(mt))):
            if d0==1:
                terminal=(lo[i]<=r.sl_exec) or (hi[i]>=r.entry+r.risk)
                fill=(lo[i]+sp[i])<=limit
            else:
                terminal=(hi[i]+sp[i]>=r.sl_exec) or (lo[i]+sp[i]<=r.entry-r.risk)
                fill=hi[i]>=limit
            # fail closed on same-bar order ambiguity: original terminal wins before pending fill
            if terminal: break
            if fill: fi=i; break
        if fi is None: continue
        hit3=False; outcome=None; resolved=None; mfe=0.0;mae=0.0
        for i in range(fi,len(mt)):
            if d0==1:
                adverse=(limit-lo[i]);fav=hi[i]-limit
                stop=(lo[i]<= (limit if hit3 else sl))
            else:
                askhi=hi[i]+sp[i]; asklo=lo[i]+sp[i]; adverse=askhi-limit;fav=limit-asklo
                stop=(askhi>= (limit if hit3 else sl))
            mfe=max(mfe,fav);mae=max(mae,adverse)
            # conservative stop first
            if stop:
                outcome='BE' if hit3 else 'SL';resolved=pd.Timestamp(mt[i]);break
            if fav>=5*risk:
                outcome='TP5';resolved=pd.Timestamp(mt[i]);break
            if (not hit3) and fav>=3*risk:
                hit3=True
        if outcome is None: outcome='CENSORED'
        d1=float(r.d1_atr); m30_atr=np.nan
        # M30 ATR available at trigger close
        b30=E['bars']['30min']; pos=b30.index.searchsorted(pd.Timestamp(r.trigger_time)-pd.Timedelta(microseconds=1),side='right')-1
        if pos>=0:m30_atr=float(b30.atr14.iloc[pos])
        rows.append({
            'source_k':float(r.source_k),'year':int(r.year),'dir':d0,'sweep_time':r.sweep_time,'trigger_time':r.trigger_time,
            'clean_m1':bool(r.m1_clean_path),'fraction':fraction,'broken_m5_level':r.broken_m5_level,'trigger_close':r.trigger_close,
            'limit_entry':limit,'sl_exec':sl,'risk':risk,'fill_time':pd.Timestamp(mt[fi]),'outcome':outcome,'resolved_at_h':resolved,
            'mfe_abs':mfe,'mae_abs':mae,'mfe_r':mfe/risk,'mae_r':mae/risk,'d1_atr':d1,'risk_d1':risk/d1 if d1>0 else np.nan,
            'm30_atr':m30_atr,'risk_m30':risk/m30_atr if m30_atr and m30_atr>0 else np.nan,
        })
    return pd.DataFrame(rows)

def mirror_h(E,q):
    # Same fill timestamp and same risk, reverse direction. 5R vs SL; no synthetic pending-order mirror.
    m1=E['m1'];mt=m1.index.to_numpy(dtype='datetime64[ns]');hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);sp=m1.spread_px.to_numpy(float);cl=m1.close.to_numpy(float)
    out=[]
    for r in q.itertuples(index=False):
        md=-int(r.dir); ip=np.searchsorted(mt,np.datetime64(r.fill_time),side='left')
        # at physical fill timestamp use chart close just before/at M1 bar open approximation; preserve risk only
        j=max(0,ip-1)
        if md==1: en=cl[j]+sp[j]; sl=en-r.risk
        else: en=cl[j]; sl=en+r.risk
        hit=0
        for i in range(ip,len(mt)):
            if md==1: stop=lo[i]<=sl;fav=hi[i]-en
            else: stop=hi[i]+sp[i]>=sl;fav=en-(lo[i]+sp[i])
            if stop:break
            if fav>=5*r.risk:hit=1;break
        out.append(hit)
    return np.asarray(out,dtype=int)

def summarize_h(q):
    if not len(q): return pd.DataFrame()
    z=q.copy();z['pnl_r']=np.select([z.outcome.eq('TP5'),z.outcome.eq('SL')],[5.0,-1.0],default=0.0)
    return z.groupby('year').agg(n=('outcome','size'),tp5=('outcome',lambda x:(x=='TP5').sum()),sl=('outcome',lambda x:(x=='SL').sum()),be=('outcome',lambda x:(x=='BE').sum()),ev=('pnl_r','mean')).reset_index()


def add_l_protected_runner(E,L,partial=0.5):
    """At high-precision checkpoint realize partial, residual BE, residual target 2R."""
    m1=E['m1']; idx=m1.index.to_numpy(dtype='datetime64[ns]')
    hi=m1.high.to_numpy(float); lo=m1.low.to_numpy(float); spr=m1.spread_px.to_numpy(float)
    q=L.copy(); hits=[]; ats=[]; terms=[]; pnls=[]
    for r in q.itertuples(index=False):
        if not int(r.checkpoint_hit):
            hits.append(0); ats.append(pd.NaT); terms.append('NO_CHECKPOINT'); pnls.append(-1.0); continue
        d0=int(r.dir); en=float(r.entry); risk=float(r.risk); tp=en+d0*2*risk
        start=np.searchsorted(idx,np.datetime64(r.checkpoint_at),side='left')
        hit=0; at=pd.NaT; term='CENSORED'
        for i in range(start+1,len(idx)):
            if d0==1:
                ht=hi[i]>=tp; hbe=lo[i]<=en
            else:
                ah=hi[i]+spr[i]; al=lo[i]+spr[i]
                ht=al<=tp; hbe=ah>=en
            if ht and hbe:
                hit=0;at=pd.Timestamp(idx[i]);term='BE_SAMEBAR';break
            if hbe:
                hit=0;at=pd.Timestamp(idx[i]);term='BE';break
            if ht:
                hit=1;at=pd.Timestamp(idx[i]);term='TP2';break
        cp=float(r.checkpoint_r)
        pnl=partial*cp+(1-partial)*(2.0 if hit else 0.0)
        hits.append(hit); ats.append(at); terms.append(term); pnls.append(pnl)
    q['res2_hit']=hits;q['res2_at']=ats;q['res2_term']=terms
    q['L50_R']=pnls
    return q

def enrich_h_reference(byk,H_all):
    """Reference k=2, 50% pullback, with H-specific eligibility metadata."""
    ref=H_all[(H_all.source_k==2.0)&(H_all.fraction==0.5)].copy()
    cand=byk[2.0][2]
    meta=cand[['sweep_time','trigger_time','dir','m30_exp','m30_owner','h1_owner','m1_direct_transfer']].copy()
    ref=ref.merge(meta,on=['sweep_time','trigger_time','dir'],how='left')
    ref['direct_transfer']=ref.m1_direct_transfer.astype(bool)
    ref['owner_agree']=(ref.m30_owner==ref.dir)&(ref.h1_owner==ref.dir)
    ref['both_branch']=(ref.m30_exp>1.0)&ref.owner_agree
    ref['base_R']=ref.outcome.map({'TP5':5.0,'BE':0.0,'SL':-1.0}).astype(float)
    # +3R 25% harvest: TP5=4.5R, BE after hit3=0.75R, SL=-1R.
    ref['H3_25_R']=ref.outcome.map({'TP5':4.5,'BE':0.75,'SL':-1.0}).astype(float)
    ref['H_direct']=ref.direct_transfer
    ref['H_primary_shadow']=ref.direct_transfer & (~ref.both_branch)
    return ref

def build_combined_ledger(H,L,h_col='base_R'):
    """Descriptive episode ledger: independently-authorized H; add L only after actual H loss."""
    rows=[]; matched=set()
    h=H[H.H_primary_shadow].copy().sort_values('fill_time')
    for _,r in h.iterrows():
        pnl=float(r[h_col]); lmatch=L[
            (pd.to_datetime(L.prior_trigger_time)==pd.Timestamp(r.trigger_time)) &
            (L.dir==r.dir)
        ]
        l_ids=[]; l_pnl=0.0
        if pnl<0 and len(lmatch):
            for li,lr in lmatch.iterrows():
                l_pnl += float(lr.L50_R); matched.add(li); l_ids.append(str(li))
            pnl += l_pnl
        rows.append({
            'time':pd.Timestamp(r.fill_time),'year':int(r.year),'kind':'H_episode',
            'h_trigger_time':r.trigger_time,'h_outcome':r.outcome,'h_R':float(r[h_col]),
            'l_recovery_count':len(l_ids),'l_recovery_R':l_pnl,'episode_R':pnl
        })
    for li,lr in L.iterrows():
        if li in matched: continue
        rows.append({
            'time':pd.Timestamp(lr.trigger_time),'year':int(lr.year),'kind':'L_standalone',
            'h_trigger_time':pd.NaT,'h_outcome':'','h_R':0.0,
            'l_recovery_count':1,'l_recovery_R':float(lr.L50_R),'episode_R':float(lr.L50_R)
        })
    return pd.DataFrame(rows).sort_values('time').reset_index(drop=True)

def metrics(df,col='episode_R'):
    a=df[col].to_numpy(float); pos=a>1e-12; neg=a<-1e-12
    eq=peak=dd=0.0; streak=mx=0
    for x in a:
        if x<0: streak+=1;mx=max(mx,streak)
        else: streak=0
        eq+=x;peak=max(peak,eq);dd=max(dd,peak-eq)
    return {
        'n':len(a),'positive_rate':float(pos.mean()),'negative_rate':float(neg.mean()),
        'avg_positive_R':float(a[pos].mean()) if pos.any() else math.nan,
        'expectancy_R':float(a.mean()),'total_R':float(a.sum()),
        'max_negative_streak':int(mx),'max_drawdown_R':float(dd)
    }


def main():
    ap=argparse.ArgumentParser(description='V3-003E dual reload reproducibility replay (2023-2025 only)')
    ap.add_argument('data', type=Path, help='GOLD# M1 CSV directory or ZIP containing discovery years 2023-2025')
    ap.add_argument('--out', type=Path, default=Path('v3_003e_repro_out'))
    args=ap.parse_args()
    global OUT
    OUT=args.out.resolve(); OUT.mkdir(parents=True,exist_ok=True)

    E=base_env(args.data); byk={}
    for k in [1.5,2.0,2.5]:
        byk[k]=build_for_k(E,k)
        _,ev,cand=byk[k]
        print('Candidate',k,cand.groupby('year').win1.agg(['count','mean']).to_dict('index'))

    ref=byk[2.0][2]
    assert ref.groupby('year').size().to_dict()=={2023:40,2024:29,2025:27}, 'Candidate-A parity failed'
    print('REFERENCE CANDIDATE-A PARITY PASS')

    lraw,lphys=module_l_candidates(E,byk)
    L=eval_l(E,lphys)
    L=add_l_protected_runner(E,L,partial=0.5)
    lraw.to_csv(OUT/'module_l_raw_multiscale_matches.csv',index=False)
    L.to_csv(OUT/'module_l_physical_ledger.csv',index=False)
    assert len(L)==11 and int(L.checkpoint_hit.sum())==11 and int(L.full1_hit.sum())==10 and int(L.mirror_checkpoint_hit.sum())==1
    print('MODULE L PARITY PASS:',len(L),'trades, checkpoint',int(L.checkpoint_hit.sum()),'full1',int(L.full1_hit.sum()),'mirror',int(L.mirror_checkpoint_hit.sum()))
    print('MODULE L L50 mean R',float(L.L50_R.mean()),'residual2',int(L.res2_hit.sum()))

    halls=[]
    for k in [1.5,2.0,2.5]:
        cand=byk[k][2]
        for f in [0.25,0.5,0.75,1.0]:
            q=fill_pullback(E,cand,f);q['mirror5']=mirror_h(E,q) if len(q) else []
            q.to_csv(OUT/f'module_h_k{k:g}_f{f:g}.csv',index=False); halls.append(q)
    Hall=pd.concat(halls,ignore_index=True)
    Hall.to_csv(OUT/'module_h_all_variants.csv',index=False)

    # Enrich the entire natural source/pullback panel with H-stage eligibility metadata.
    enriched=[]
    for k in [1.5,2.0,2.5]:
        meta=byk[k][2][['sweep_time','trigger_time','dir','m30_exp','m30_owner','h1_owner','m1_direct_transfer']].copy()
        q=Hall[Hall.source_k==k].merge(meta,on=['sweep_time','trigger_time','dir'],how='left')
        q['direct_transfer']=q.m1_direct_transfer.astype(bool)
        q['owner_agree']=(q.m30_owner==q.dir)&(q.h1_owner==q.dir)
        q['both_branch']=(q.m30_exp>1.0)&q.owner_agree
        enriched.append(q)
    HallE=pd.concat(enriched,ignore_index=True)
    HallE.to_csv(OUT/'module_h_all_variants_enriched.csv',index=False)
    assert int(((~HallE.direct_transfer)&HallE.outcome.eq('TP5')).sum())==0, 'non-direct TP5 appeared in natural panel'
    assert int((HallE.direct_transfer&HallE.both_branch&HallE.outcome.eq('TP5')).sum())==0, 'BOTH TP5 appeared in natural panel'
    print('MODULE H PANEL: non-direct TP5=0; direct+BOTH TP5=0 across k=1.5/2/2.5 and 25/50/75/100% pullbacks')

    Href=enrich_h_reference(byk,Hall)
    Href.to_csv(OUT/'module_h_reference_enriched.csv',index=False)
    base=Href
    assert len(base)==48
    assert int((base.outcome=='TP5').sum())==14 and int((base.outcome=='SL').sum())==31 and int((base.outcome=='BE').sum())==3
    Hdirect=base[base.H_direct]
    assert len(Hdirect)==44 and int((Hdirect.outcome=='TP5').sum())==14 and int((Hdirect.outcome=='SL').sum())==27
    Hprimary=base[base.H_primary_shadow]
    assert len(Hprimary)==40 and int((Hprimary.outcome=='TP5').sum())==14 and int((Hprimary.outcome=='SL').sum())==23 and int((Hprimary.outcome=='BE').sum())==3
    print('MODULE H BASE PARITY PASS: 48 / 14 TP5 / 31 SL / 3 BE')
    print('MODULE H DIRECT:',len(Hdirect),'EV',float(Hdirect.base_R.mean()))
    print('MODULE H DIRECT & NOT-BOTH SHADOW:',len(Hprimary),'EV',float(Hprimary.base_R.mean()))

    # H->L links and descriptive combined ledgers
    links=[]
    for _,r in Hprimary.iterrows():
        if float(r.base_R)>=0: continue
        g=L[(pd.to_datetime(L.prior_trigger_time)==pd.Timestamp(r.trigger_time))&(L.dir==r.dir)]
        for _,lr in g.iterrows():
            links.append({
                'year':int(r.year),'h_trigger_time':r.trigger_time,'h_fill_time':r.fill_time,
                'h_outcome':r.outcome,'h_R':float(r.base_R),
                'l_trigger_time':lr.trigger_time,'l_checkpoint_r':float(lr.checkpoint_r),
                'l_res2_hit':int(lr.res2_hit),'l_R':float(lr.L50_R),
                'episode_R':float(r.base_R+lr.L50_R)
            })
    links=pd.DataFrame(links)
    links.to_csv(OUT/'h_to_l_recovery_links.csv',index=False)
    print('H->L links',len(links),'net-positive',int((links.episode_R>0).sum()) if len(links) else 0)

    comb=build_combined_ledger(Href,L,'base_R')
    comb_harvest=build_combined_ledger(Href,L,'H3_25_R')
    comb.to_csv(OUT/'combined_episode_base.csv',index=False)
    comb_harvest.to_csv(OUT/'combined_episode_harvest.csv',index=False)
    print('COMBINED BASE',metrics(comb))
    print('COMBINED HARVEST',metrics(comb_harvest))

    manifest={
        'candidate_A_counts':ref.groupby('year').size().to_dict(),
        'module_L':{'n':len(L),'checkpoint_hits':int(L.checkpoint_hit.sum()),'full1_hits':int(L.full1_hit.sum()),
                    'mirror_checkpoint_hits':int(L.mirror_checkpoint_hit.sum()),'L50_mean_R':float(L.L50_R.mean()),
                    'residual2_hits':int(L.res2_hit.sum())},
        'module_H_base':{'n':len(base),'tp5':int((base.outcome=='TP5').sum()),'sl':int((base.outcome=='SL').sum()),
                         'be':int((base.outcome=='BE').sum()),'ev_R':float(base.base_R.mean())},
        'module_H_direct':{'n':len(Hdirect),'tp5':int((Hdirect.outcome=='TP5').sum()),'sl':int((Hdirect.outcome=='SL').sum()),
                           'be':int((Hdirect.outcome=='BE').sum()),'ev_R':float(Hdirect.base_R.mean())},
        'module_H_direct_notboth_shadow':{'n':len(Hprimary),'tp5':int((Hprimary.outcome=='TP5').sum()),
                                         'sl':int((Hprimary.outcome=='SL').sum()),'be':int((Hprimary.outcome=='BE').sum()),
                                         'ev_R':float(Hprimary.base_R.mean())},
        'h_to_l_links':len(links),
        'combined_base':metrics(comb),
        'combined_harvest':metrics(comb_harvest),
    }
    (OUT/'repro_manifest.json').write_text(json.dumps(manifest,indent=2,default=str),encoding='utf-8')
    print('OUTPUT',OUT)

if __name__=='__main__':
    main()
