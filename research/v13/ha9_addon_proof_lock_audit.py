from __future__ import annotations

import argparse, json, math
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np

START = pd.Timestamp('2024-01-01 00:00:00')
CUTOFF = pd.Timestamp('2026-08-28 20:00:00')
EPS = 1e-9

@dataclass
class Journey:
    jid: int
    side: int
    start_idx: int
    end_idx: int | None = None


def load_bars(path: Path, tf: str) -> pd.DataFrame:
    d = pd.read_csv(path, sep='\t')
    d['time'] = pd.to_datetime(d['<DATE>'] + ' ' + d['<TIME>'], format='%Y.%m.%d %H:%M:%S')
    d = d.rename(columns={'<OPEN>':'open','<HIGH>':'high','<LOW>':'low','<CLOSE>':'close'})
    for c in ('open','high','low','close'):
        d[c] = pd.to_numeric(d[c], errors='raise')
    d = d.sort_values('time').reset_index(drop=True)
    if tf == 'M1':
        d['h4'] = d['time'].dt.floor('4h')
    return d


def build_h4_state(h4: pd.DataFrame) -> pd.DataFrame:
    ho = hc = None
    color = 0
    colors=[]; haos=[]; hacs=[]
    for r in h4.itertuples(index=False):
        nhc=(r.open+r.high+r.low+r.close)/4.0
        nho=(r.open+r.close)/2.0 if ho is None else (ho+hc)/2.0
        ncolor=1 if nhc>nho else -1 if nhc<nho else color
        haos.append(nho); hacs.append(nhc); colors.append(ncolor)
        ho,hc,color=nho,nhc,ncolor
    out=h4.copy(); out['ha_open']=haos; out['ha_close']=hacs; out['color']=colors
    return out


def build_children(h4: pd.DataFrame) -> pd.DataFrame:
    # Decision at completed H4 index i; execution price is next H4 raw open (i+1).
    rows=[]; jid=0; active_side=0; active_jid=0; child_no=0
    for i in range(len(h4)-1):
        r=h4.iloc[i]; prev=int(h4.iloc[i-1].color) if i else 0
        if r.time < START or r.time > CUTOFF:
            continue
        side=int(r.color)
        if side==0 or prev==0:
            continue
        if active_side==0:
            if side!=prev:
                jid+=1; active_jid=jid; active_side=side; child_no=1
                rows.append(dict(journey=jid, child=1, side=side, signal_idx=i,
                                 signal=r.time, entry_idx=i+1, entry=float(h4.iloc[i+1].open),
                                 signal_high=float(r.high), signal_low=float(r.low)))
            continue
        if side==active_side:
            if child_no < 10:
                child_no += 1
                rows.append(dict(journey=active_jid, child=child_no, side=side, signal_idx=i,
                                 signal=r.time, entry_idx=i+1, entry=float(h4.iloc[i+1].open),
                                 signal_high=float(r.high), signal_low=float(r.low)))
        else:
            # Opposite completed bar closes old Journey at this bar's following raw H4 open,
            # then itself starts next Journey Child #1 at the same execution price.
            exit_price=float(h4.iloc[i+1].open)
            for row in rows:
                if row['journey']==active_jid and 'baseline_exit' not in row:
                    row['baseline_exit']=exit_price; row['exit_signal_idx']=i
            jid+=1; active_jid=jid; active_side=side; child_no=1
            rows.append(dict(journey=jid, child=1, side=side, signal_idx=i,
                             signal=r.time, entry_idx=i+1, entry=float(h4.iloc[i+1].open),
                             signal_high=float(r.high), signal_low=float(r.low)))
    # only closed journey children participate in canonical economics
    closed=[r for r in rows if 'baseline_exit' in r]
    d=pd.DataFrame(closed)
    d['baseline_pnl']=d.side*(d.baseline_exit-d.entry)
    return d


def build_m1_groups(m1: pd.DataFrame):
    # Keep complete canonical action horizon; groups keyed by nominal H4 open.
    groups={k:g[['time','open','high','low','close']].reset_index(drop=True)
            for k,g in m1.groupby('h4', sort=False)}
    return groups


def conservative_stop_fill(side:int, lock:float, row) -> float:
    # Gap-aware: if the bar opens beyond the virtual stop, fill at open; otherwise at stop.
    if side==1:
        return float(row.open) if row.open < lock else lock
    return float(row.open) if row.open > lock else lock


def evaluate_variant(children: pd.DataFrame, h4: pd.DataFrame, m1_groups: dict, use_timeout: bool=True) -> pd.DataFrame:
    out=[]
    h4_times=h4.time.to_list()
    for r in children.itertuples(index=False):
        base=float(r.baseline_pnl)
        exit_price=float(r.baseline_exit)
        reason='HA_EXIT'
        proven=False
        proof_time=None
        lock=None
        variant_exit=exit_price
        if int(r.child)>=2:
            proof_h4=h4_times[int(r.entry_idx)]
            proof_rows=m1_groups.get(proof_h4)
            target=float(r.signal_high if r.side==1 else r.signal_low)
            entry=float(r.entry)
            if proof_rows is None or proof_rows.empty:
                raise RuntimeError(f'missing M1 proof H4 {proof_h4}')
            proof_pos=None
            for j,bar in enumerate(proof_rows.itertuples(index=False)):
                if (r.side==1 and bar.high > target+EPS) or (r.side==-1 and bar.low < target-EPS):
                    proven=True; proof_pos=j; proof_time=bar.time
                    lock=max(entry,target) if r.side==1 else min(entry,target)
                    break
            if proven:
                # lock becomes active from the next M1, never inside the proof M1 itself.
                hit=False
                for hi in range(int(r.entry_idx), int(r.exit_signal_idx)+1):
                    key=h4_times[hi]
                    g=m1_groups.get(key)
                    if g is None: continue
                    for bar in g.itertuples(index=False):
                        if bar.time <= proof_time: continue
                        if (r.side==1 and bar.low <= lock+EPS) or (r.side==-1 and bar.high >= lock-EPS):
                            variant_exit=conservative_stop_fill(int(r.side), float(lock), bar)
                            reason='BREAKOUT_LOCK'
                            hit=True
                            break
                    if hit: break
            elif use_timeout:
                # exactly one H4 proof window; close at the next H4 raw open. If the Journey
                # flips on that completed proof bar, this is the same price as the HA exit.
                timeout_idx=int(r.entry_idx)+1
                timeout_price=float(h4.iloc[timeout_idx].open) if timeout_idx < len(h4) else exit_price
                baseline_exit_idx=int(r.exit_signal_idx)+1
                if timeout_idx <= baseline_exit_idx:
                    variant_exit=timeout_price
                    reason='PROOF_TIMEOUT'
        vpnl=int(r.side)*(variant_exit-float(r.entry))
        out.append({**r._asdict(), 'variant_exit':variant_exit,'variant_pnl':vpnl,
                    'exit_reason':reason,'proven':proven,'proof_time':proof_time,'lock_level':lock})
    return pd.DataFrame(out)


def max_dd(values):
    eq=np.cumsum(np.asarray(values,dtype=float)); peaks=np.maximum.accumulate(np.r_[0.0,eq])
    dd=peaks[1:]-eq
    return float(dd.max()) if len(dd) else 0.0


def max_loss_streak(values):
    best=cur=0
    for v in values:
        if v<0: cur+=1; best=max(best,cur)
        else: cur=0
    return int(best)


def stats(df, col):
    v=df[col].to_numpy(float); wins=int((v>0).sum()); losses=int((v<0).sum()); flats=int((v==0).sum())
    gw=float(v[v>0].sum()); gl=float(-v[v<0].sum())
    return dict(n=len(v),wins=wins,losses=losses,flats=flats,
                win_rate_nonflat=wins/(wins+losses) if wins+losses else None,
                net_points=float(v.sum()),profit_factor=gw/gl if gl else None,
                max_trade_sequence_dd=max_dd(v),max_consecutive_losses=max_loss_streak(v))


def journey_trim(df, col, n):
    j=df.groupby('journey')[col].sum().sort_values(ascending=False)
    remove=set(j.head(n).index)
    return float(df.loc[~df.journey.isin(remove),col].sum())


def block_positive_share(df,col,size):
    v=df.sort_values(['signal','journey','child'])[col].to_numpy(float)
    sums=[v[i:i+size].sum() for i in range(0,len(v),size) if len(v[i:i+size])==size]
    return dict(block_size=size,n_blocks=len(sums),positive_share=float(np.mean(np.array(sums)>0)),median_points=float(np.median(sums)))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--h4',type=Path,required=True); p.add_argument('--m1',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    h4=build_h4_state(load_bars(a.h4,'H4'))
    m1=load_bars(a.m1,'M1')
    children=build_children(h4)
    assert children.journey.nunique()==965, children.journey.nunique()
    assert len(children)==3858, len(children)
    assert abs(children.baseline_pnl.sum()-8147.11)<0.02, children.baseline_pnl.sum()
    groups=build_m1_groups(m1)
    lock_only=evaluate_variant(children,h4,groups,use_timeout=False)
    v=evaluate_variant(children,h4,groups,use_timeout=True)
    # New candidate intentionally leaves Child #1 unchanged; verify.
    assert np.allclose(v.loc[v.child==1,'variant_pnl'],v.loc[v.child==1,'baseline_pnl'])
    summary={
      'status':'CONSUMED DEVELOPMENT / BREAKTHROUGH ACTION CANDIDATE / MT5 VALIDATION PENDING',
      'window':'2024-01-01 through 2026-08-28 available GOLD# history',
      'baseline':stats(v,'baseline_pnl'), 'breakout_lock_only':stats(lock_only,'variant_pnl'), 'proof_lock_timeout':stats(v,'variant_pnl'),
      'loss_reduction_count':int((v.baseline_pnl<0).sum()-(v.variant_pnl<0).sum()),
      'loss_reduction_pct':float(((v.baseline_pnl<0).sum()-(v.variant_pnl<0).sum())/(v.baseline_pnl<0).sum()),
      'year':{}, 'exit_reasons':v.exit_reason.value_counts().to_dict(), 'lock_only_exit_reasons':lock_only.exit_reason.value_counts().to_dict(),
      'top_profitable_journey_removed':{}, 'trade_blocks':{}
    }
    v['year']=pd.to_datetime(v.signal).dt.year
    for y,g in v.groupby('year'):
      lo=lock_only.loc[lock_only.signal.isin(g.signal)]
      summary['year'][str(int(y))]={'baseline':stats(g,'baseline_pnl'),'lock_only':stats(lo,'variant_pnl'),'variant':stats(g,'variant_pnl')}
    for n in (1,3,5,10,20):
      summary['top_profitable_journey_removed'][str(n)]={'baseline':journey_trim(v,'baseline_pnl',n),'variant':journey_trim(v,'variant_pnl',n)}
    for size in (10,25,50,100):
      summary['trade_blocks'][str(size)]={'baseline':block_positive_share(v,'baseline_pnl',size),'variant':block_positive_share(v,'variant_pnl',size)}
    # Monthly smoothness is descriptive; it does not create a calendar filter.
    monthly=[]
    for month,g in v.groupby(pd.to_datetime(v.signal).dt.to_period('M')):
      monthly.append({'month':str(month),'baseline_points':float(g.baseline_pnl.sum()),'variant_points':float(g.variant_pnl.sum())})
    summary['monthly']={'months':len(monthly),'baseline_positive_months':sum(x['baseline_points']>0 for x in monthly),'variant_positive_months':sum(x['variant_points']>0 for x in monthly),'baseline_worst_month':min(x['baseline_points'] for x in monthly),'variant_worst_month':min(x['variant_points'] for x in monthly),'rows':monthly}
    v.to_csv(a.output/'child_ledger.csv',index=False)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2,default=str),encoding='utf-8')
    print(json.dumps(summary,indent=2,default=str))

if __name__=='__main__': main()
