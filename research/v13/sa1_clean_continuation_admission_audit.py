from __future__ import annotations

import argparse, json, math, re
from pathlib import Path
import numpy as np
import pandas as pd

START = pd.Timestamp('2024-01-01 00:00:00')
CUTOFF = pd.Timestamp('2026-08-28 20:00:00')
COMMENT_RE = re.compile(r'^V13P\|J(?P<journey>\d{6})\|C(?P<child>\d{2})\|(?P<side>[LS])$')


def parse_mt5_report(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=0, header=None, dtype=object)
    deals = raw.loc[raw[4].isin(['in','out']), list(range(13))].copy()
    deals.columns = ['time','deal','symbol','type','direction','volume','price','order','commission','swap','profit','balance','comment']
    deals['time'] = pd.to_datetime(deals.time, format='%Y.%m.%d %H:%M:%S')
    for c in ['deal','volume','price','order','commission','swap','profit','balance']:
        deals[c] = pd.to_numeric(deals[c], errors='raise')
    deals = deals.sort_values(['time','deal']).reset_index(drop=True)
    open_positions=[]; completed=[]
    for row in deals.itertuples(index=False):
        if row.direction == 'in':
            m = COMMENT_RE.match(str(row.comment).strip())
            if m is None:
                continue
            side = 1 if m.group('side') == 'L' else -1
            open_positions.append({
                'journey':int(m.group('journey')), 'child':int(m.group('child')), 'side':side,
                'entry_time':row.time, 'entry_deal':int(row.deal), 'entry_price':float(row.price),
                'volume':float(row.volume), 'entry_comment':row.comment,
            })
            continue
        closing_side = 1 if row.type == 'sell' else -1 if row.type == 'buy' else 0
        candidates=[(i,p) for i,p in enumerate(open_positions)
                    if p['side']==closing_side and math.isclose(p['volume'],float(row.volume),abs_tol=1e-12)]
        if not candidates:
            raise RuntimeError(f'no matching open Child for exit deal {row.deal}')
        def score(item):
            i,p=item
            expected=p['side']*(float(row.price)-p['entry_price'])
            return abs(expected-float(row.profit)), p['entry_time'], i
        i,p=min(candidates,key=score)
        err=score((i,p))[0]
        if err > 0.011:
            raise RuntimeError(f'profit reconciliation error {err} on deal {row.deal}')
        open_positions.pop(i)
        completed.append({**p,'exit_time':row.time,'exit_deal':int(row.deal),'exit_price':float(row.price),
                          'profit':float(row.profit),'commission':float(row.commission),'swap':float(row.swap),
                          'match_error':err})
    if open_positions:
        raise RuntimeError(f'{len(open_positions)} unmatched open positions')
    out=pd.DataFrame(completed).sort_values(['entry_time','entry_deal']).reset_index(drop=True)
    return out


def load_h1(path: Path) -> pd.DataFrame:
    d=pd.read_csv(path,sep='\t')
    d['time']=pd.to_datetime(d['<DATE>']+' '+d['<TIME>'],format='%Y.%m.%d %H:%M:%S')
    for old,new in [('<OPEN>','open'),('<HIGH>','high'),('<LOW>','low'),('<CLOSE>','close')]:
        d[new]=pd.to_numeric(d[old],errors='raise')
    d=d.sort_values('time').reset_index(drop=True)
    ho=hc=None; color=0; colors=[]
    for r in d.itertuples(index=False):
        nhc=(r.open+r.high+r.low+r.close)/4.0
        nho=(r.open+r.close)/2.0 if ho is None else (ho+hc)/2.0
        ncolor=1 if nhc>nho else -1 if nhc<nho else color
        colors.append(ncolor); ho,hc,color=nho,nhc,ncolor
    d['ha_color']=colors
    d['h4']=d.time.dt.floor('4h')
    return d


def max_dd_exit_order(frame: pd.DataFrame) -> float:
    v=frame.sort_values(['exit_time','exit_deal']).profit.to_numpy(float)
    eq=np.cumsum(v); peaks=np.maximum.accumulate(np.r_[0.0,eq])
    return float((peaks[1:]-eq).max()) if len(eq) else 0.0


def max_loss_streak_exit_order(frame: pd.DataFrame) -> int:
    v=frame.sort_values(['exit_time','exit_deal']).profit.to_numpy(float)
    best=cur=0
    for x in v:
        if x<0: cur+=1; best=max(best,cur)
        else: cur=0
    return int(best)


def stats(frame: pd.DataFrame) -> dict:
    v=frame.profit.to_numpy(float)
    wins=int((v>0).sum()); losses=int((v<0).sum()); flats=int((v==0).sum())
    gw=float(v[v>0].sum()); gl=float(-v[v<0].sum())
    return {
        'n':int(len(v)), 'wins':wins, 'losses':losses, 'flats':flats,
        'win_rate_nonflat':wins/(wins+losses) if wins+losses else None,
        'net_usd':float(v.sum()), 'profit_factor':gw/gl if gl else None,
        'realized_max_dd_usd':max_dd_exit_order(frame),
        'max_consecutive_losses':max_loss_streak_exit_order(frame),
    }


def block_quality(frame: pd.DataFrame, sizes=(10,25,50,100)) -> dict:
    ordered=frame.sort_values(['exit_time','exit_deal']).profit.to_numpy(float)
    out={}
    for size in sizes:
        sums=[ordered[i:i+size].sum() for i in range(0,len(ordered),size) if len(ordered[i:i+size])==size]
        out[str(size)]={
            'blocks':len(sums),
            'positive_share':float(np.mean(np.array(sums)>0)) if sums else None,
            'median_usd':float(np.median(sums)) if sums else None,
        }
    return out


def trimmed_by_journey(frame: pd.DataFrame, ns=(1,3,5,10,20)) -> dict:
    j=frame.groupby('journey').profit.sum().sort_values(ascending=False)
    out={}
    for n in ns:
        remove=set(j.head(n).index)
        out[str(n)]=float(frame.loc[~frame.journey.isin(remove),'profit'].sum())
    return out


def add_gate(features: pd.DataFrame, h1: pd.DataFrame) -> pd.DataFrame:
    groups={t:g.ha_color.tolist() for t,g in h1.groupby('h4',sort=False)}
    f=features.copy()
    no_opp=[]; count=[]
    for t,side in zip(pd.to_datetime(f.signal),f.side.astype(int)):
        colors=groups.get(pd.Timestamp(t),[])
        count.append(len(colors))
        no_opp.append(bool(colors) and all(int(c)==int(side) for c in colors))
    f['signal_h4_h1_count']=count
    f['signal_h4_h1_no_opposition']=no_opp
    f['sa1_raw_close_accept']=f.t0_raw_close_pos.astype(float)>0.0
    f['sa1_no_opposite_wick']=~f.t0_wick_present.astype(bool)
    f['sa1_admit']=f.sa1_raw_close_accept & f.sa1_no_opposite_wick & f.signal_h4_h1_no_opposition
    return f


def permutation_test(addons: pd.DataFrame, selected: pd.DataFrame, draws=3000, seed=13) -> dict:
    # Preserve year/side/Child-ordinal selected counts. This is a descriptive selection sanity check.
    rng=np.random.default_rng(seed)
    strata_cols=['year','side','child']
    target=selected.groupby(strata_cols).size().to_dict()
    groups={k:g.index.to_numpy() for k,g in addons.groupby(strata_cols)}
    obs_loss=int((selected.profit<0).sum()); obs_win=int((selected.profit>0).sum()); obs_net=float(selected.profit.sum())
    samples=[]
    for _ in range(draws):
        idx=[]
        for k,n in target.items():
            pool=groups[k]
            idx.extend(rng.choice(pool,size=n,replace=False).tolist())
        g=addons.loc[idx]
        samples.append((int((g.profit<0).sum()),int((g.profit>0).sum()),float(g.profit.sum())))
    a=np.asarray(samples,float)
    return {
        'draws':draws,
        'strata':'year + side + child ordinal',
        'observed':{'losses':obs_loss,'wins':obs_win,'net_usd':obs_net},
        'random_mean':{'losses':float(a[:,0].mean()),'wins':float(a[:,1].mean()),'net_usd':float(a[:,2].mean())},
        'random_percentile':{
            'losses_le_observed':float(np.mean(a[:,0]<=obs_loss)),
            'wins_ge_observed':float(np.mean(a[:,1]>=obs_win)),
            'net_ge_observed':float(np.mean(a[:,2]>=obs_net)),
        },
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--h1',type=Path,required=True)
    p.add_argument('--state-features',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    actual=parse_mt5_report(a.report)
    canonical=actual.loc[(actual.entry_time>=START)&(actual.exit_time<=CUTOFF)].copy()
    canonical['year']=canonical.entry_time.dt.year
    assert len(canonical)==3858, len(canonical)
    assert int((canonical.profit>0).sum())==2118
    assert int((canonical.profit<0).sum())==1734

    h1=load_h1(a.h1)
    features=pd.read_csv(a.state_features)
    features['signal']=pd.to_datetime(features.signal)
    features=add_gate(features,h1)
    assert len(features)==2893
    gatekeys=set(map(tuple,features.loc[features.sa1_admit,['journey','child']].to_numpy()))
    canonical['sa1_admit']=(canonical.child==1)|canonical.apply(lambda r:(r.journey,r.child) in gatekeys,axis=1)
    selected=canonical.loc[canonical.sa1_admit].copy()
    addons=canonical.loc[canonical.child>=2].copy()
    gated=selected.loc[selected.child>=2].copy()
    c1=canonical.loc[canonical.child==1].copy()

    # Attach gate components to add-ons for interaction diagnostics.
    comp=features[['journey','child','year','side','t0_raw_close_pos','t0_wick_present','t0_delta_contract',
                   'signal_h4_h1_no_opposition','sa1_raw_close_accept','sa1_no_opposite_wick','sa1_admit']]
    addon_diag=addons.merge(comp,on=['journey','child','side'],how='left',validate='one_to_one',suffixes=('','_feature'))
    if addon_diag.sa1_admit.isna().any(): raise RuntimeError('missing feature join')

    rw=addon_diag.loc[addon_diag.sa1_raw_close_accept & addon_diag.sa1_no_opposite_wick]
    rw_h1=rw.groupby('signal_h4_h1_no_opposition').apply(lambda g:pd.Series(stats(g)),include_groups=False).to_dict(orient='index')
    inside_gate=addon_diag.loc[addon_diag.sa1_admit]
    delta_split=inside_gate.groupby('t0_delta_contract').apply(lambda g:pd.Series(stats(g)),include_groups=False).to_dict(orient='index')

    summary={
        'status':'CONSUMED DEVELOPMENT / SA-1 ACTION CANDIDATE / ACTUAL-TICK STRATEGY TESTER VALIDATION PENDING',
        'base_head':'652dcd070206f04a51eb5a7451a253393b60ee03',
        'window':'2024-01-01 through 2026-08-28 20:00 canonical cutoff',
        'definition':{
            'child1':'unchanged and always admitted',
            'addons':'admit only when raw close is favorable versus signal-H4 HA close, opposite H4 HA wick is absent, and every observed completed H1 HA inside the signal H4 is Journey-aligned',
            'management':'after admission, keep HA-9 proof / one-H4 timeout / breakout-lock unchanged',
            'numbering':'a rejected signal does not consume a successful Child number; later same-color H4 may be another opportunity until 10 successful entries',
        },
        'actual_tick':{
            'ha9_all':stats(canonical),
            'sa1_all':stats(selected),
            'child1_unchanged':stats(c1),
            'ha9_addons':stats(addons),
            'sa1_addons':stats(gated),
            'loss_reduction_all_count':int((canonical.profit<0).sum()-(selected.profit<0).sum()),
            'loss_reduction_all_pct':float(((canonical.profit<0).sum()-(selected.profit<0).sum())/(canonical.profit<0).sum()),
            'addon_loss_reduction_count':int((addons.profit<0).sum()-(gated.profit<0).sum()),
            'addon_loss_reduction_pct':float(((addons.profit<0).sum()-(gated.profit<0).sum())/(addons.profit<0).sum()),
            'net_retention_all':float(selected.profit.sum()/canonical.profit.sum()),
            'net_retention_addons':float(gated.profit.sum()/addons.profit.sum()),
            'block_quality':{'ha9':block_quality(canonical),'sa1':block_quality(selected)},
            'top_profitable_journey_removed':{'ha9':trimmed_by_journey(canonical),'sa1':trimmed_by_journey(selected)},
        },
        'sa1_addon_year':{}, 'sa1_addon_side':{},
        'interaction':{
            'raw_close_plus_no_wick':stats(rw),
            'raw_close_plus_no_wick_by_h1_no_opposition':rw_h1,
            'inside_sa1_by_delta_contraction':delta_split,
        },
        'permutation':permutation_test(addons,gated),
        'limitations':[
            'SA-1 was discovered on consumed 2024-2026 development history; this receipt is not independent out-of-sample proof.',
            'Actual-tick report economics are available, but the supplied journal did not contain the V13HAProofLockMax10EA / V13P proof-lock event stream, so exact HA-9 event-reason parity remains unresolved.',
            'This audit filters the already reconstructed actual Child ledger. Official SA-1 economics require a fresh Every tick based on real ticks tester run of the SA-1 EA.',
        ],
    }
    for y,g in gated.groupby(gated.entry_time.dt.year): summary['sa1_addon_year'][str(int(y))]=stats(g)
    for s,g in gated.groupby('side'): summary['sa1_addon_side']['LONG' if s==1 else 'SHORT']=stats(g)

    features.to_csv(a.output/'sa1_gate_feature_ledger.csv',index=False)
    addon_diag.to_csv(a.output/'sa1_addon_diagnostic_ledger.csv',index=False)
    selected.to_csv(a.output/'sa1_selected_actual_children.csv',index=False)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2,default=str),encoding='utf-8')
    print(json.dumps({
        'ha9_all':summary['actual_tick']['ha9_all'],
        'sa1_all':summary['actual_tick']['sa1_all'],
        'ha9_addons':summary['actual_tick']['ha9_addons'],
        'sa1_addons':summary['actual_tick']['sa1_addons'],
        'permutation':summary['permutation'],
    },indent=2))

if __name__=='__main__': main()
