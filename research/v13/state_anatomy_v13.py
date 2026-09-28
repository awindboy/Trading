from __future__ import annotations
import pandas as pd, numpy as np, math, re, json
from pathlib import Path
from collections import defaultdict

DATA=Path.cwd()

def set_data_dir(path):
    global DATA
    DATA=Path(path)
START=pd.Timestamp('2024-01-01 00:00:00')
CUTOFF=pd.Timestamp('2026-08-28 20:00:00')
EPS=1e-9
COMMENT_RE=re.compile(r'^V13P\|J(?P<journey>\d{6})\|C(?P<child>\d{2})\|(?P<side>[LS])$')

def load_bars(name):
    d=pd.read_csv(DATA/name,sep='\t')
    d['time']=pd.to_datetime(d['<DATE>']+' '+d['<TIME>'],format='%Y.%m.%d %H:%M:%S')
    d=d.rename(columns={'<OPEN>':'open','<HIGH>':'high','<LOW>':'low','<CLOSE>':'close','<TICKVOL>':'tick_volume','<SPREAD>':'spread_points'})
    for c in ['open','high','low','close','tick_volume','spread_points']:
        if c in d: d[c]=pd.to_numeric(d[c],errors='raise')
    return d.sort_values('time').reset_index(drop=True)

def add_ha(d,prefix):
    ho=hc=None; prev_color=0; streak=0; out=[]
    for r in d.itertuples(index=False):
        nhc=(r.open+r.high+r.low+r.close)/4.0
        nho=(r.open+r.close)/2.0 if ho is None else (ho+hc)/2.0
        col=1 if nhc>nho else -1 if nhc<nho else prev_color
        hi=max(r.high,nho,nhc); lo=min(r.low,nho,nhc)
        streak=streak+1 if prev_color and col==prev_color else 1
        opp=(min(nho,nhc)-lo) if col==1 else (hi-max(nho,nhc))
        rng=hi-lo
        out.append((nho,nhc,col,streak,abs(nhc-nho),abs(nhc-nho)/rng if rng else 0,opp,hi,lo))
        ho,hc,prev_color=nho,nhc,col
    cols=[f'{prefix}_open',f'{prefix}_close',f'{prefix}_color',f'{prefix}_streak',f'{prefix}_abs_delta',f'{prefix}_body_ratio',f'{prefix}_opp_wick',f'{prefix}_high',f'{prefix}_low']
    return pd.concat([d,pd.DataFrame(out,columns=cols,index=d.index)],axis=1)

def parse_report():
    raw=pd.read_excel(DATA/'ReportTester-318585216.xlsx',sheet_name=0,header=None,dtype=object)
    rows=raw.loc[raw[4].isin(['in','out']),list(range(13))].copy()
    rows.columns=['time','deal','symbol','type','direction','volume','price','order','commission','swap','profit','balance','comment']
    rows['time']=pd.to_datetime(rows.time,format='%Y.%m.%d %H:%M:%S')
    for c in ['deal','volume','price','order','commission','swap','profit','balance']:
        rows[c]=pd.to_numeric(rows[c],errors='raise')
    rows=rows.sort_values(['time','deal']).reset_index(drop=True)
    opens=[]; done=[]
    for r in rows.itertuples(index=False):
        if r.direction=='in':
            m=COMMENT_RE.match(str(r.comment).strip())
            if not m: continue
            j=int(m.group('journey')); c=int(m.group('child')); side=1 if m.group('side')=='L' else -1
            opens.append(dict(journey=j,child=c,side=side,entry_time=r.time,entry_price=float(r.price),volume=float(r.volume),entry_deal=int(r.deal)))
        else:
            closing_side=1 if r.type=='sell' else -1 if r.type=='buy' else 0
            cand=[(i,p) for i,p in enumerate(opens) if p['side']==closing_side and math.isclose(p['volume'],float(r.volume),abs_tol=1e-12)]
            if not cand: raise RuntimeError(('no match',r.deal))
            def score(ip):
                i,p=ip; expected=p['side']*(float(r.price)-p['entry_price'])
                return (abs(expected-float(r.profit)),p['entry_time'],i)
            i,p=min(cand,key=score); opens.pop(i)
            done.append({**p,'exit_time':r.time,'exit_price':float(r.price),'profit':float(r.profit),'exit_deal':int(r.deal)})
    d=pd.DataFrame(done).sort_values(['entry_time','entry_deal']).reset_index(drop=True)
    d['hold_hours']=(d.exit_time-d.entry_time).dt.total_seconds()/3600
    return d

def build_ideal_children(h4):
    rows=[]; jid=0; active_side=0; active_jid=0; child_no=0
    for i in range(len(h4)-1):
        r=h4.iloc[i]; prev=int(h4.iloc[i-1].h4ha_color) if i else 0
        if r.time<START or r.time>CUTOFF: continue
        side=int(r.h4ha_color)
        if side==0 or prev==0: continue
        if active_side==0:
            if side!=prev:
                jid+=1; active_jid=jid; active_side=side; child_no=1
                rows.append(dict(journey=jid,child=1,side=side,signal_idx=i,signal=r.time,entry_h4_idx=i+1,nominal_entry=h4.iloc[i+1].time,signal_high=float(r.high),signal_low=float(r.low)))
            continue
        if side==active_side:
            if child_no<10:
                child_no+=1
                rows.append(dict(journey=active_jid,child=child_no,side=side,signal_idx=i,signal=r.time,entry_h4_idx=i+1,nominal_entry=h4.iloc[i+1].time,signal_high=float(r.high),signal_low=float(r.low)))
        else:
            exit_nom=h4.iloc[i+1].time
            for rr in rows:
                if rr['journey']==active_jid and 'baseline_exit_nominal' not in rr:
                    rr['baseline_exit_nominal']=exit_nom
            jid+=1; active_jid=jid; active_side=side; child_no=1
            rows.append(dict(journey=jid,child=1,side=side,signal_idx=i,signal=r.time,entry_h4_idx=i+1,nominal_entry=h4.iloc[i+1].time,signal_high=float(r.high),signal_low=float(r.low)))
    return pd.DataFrame([r for r in rows if 'baseline_exit_nominal' in r])

def add_h4_features(h4):
    h4=add_ha(h4,'h4ha')
    h4['raw_range']=h4.high-h4.low
    h4['median_range20']=h4.raw_range.shift(1).rolling(20,min_periods=20).median()
    h4['range_norm20']=h4.raw_range/h4.median_range20
    h4['delta_norm20']=h4.h4ha_abs_delta/h4.median_range20
    h4['delta_contract']=h4.h4ha_abs_delta < h4.h4ha_abs_delta.shift(1)
    h4['wick_present']=h4.h4ha_opp_wick>EPS
    h4['wick_reappeared']=(h4.h4ha_opp_wick.shift(1)<=EPS)&(h4.h4ha_opp_wick>EPS)
    h4['raw_close_pos'] = np.where(h4.raw_range>0, h4.h4ha_color*(h4.close-h4.h4ha_close)/h4.raw_range,0.0)
    d=h4.h4ha_open-h4.h4ha_close
    hs=[]
    for i in range(len(h4)):
        if i<9: hs.append(np.nan); continue
        w=d.iloc[i-9:i+1]; span=float(w.max()-w.min())
        hs.append(100*(float(d.iloc[i])-float(w.min()))/span if span else np.nan)
    h4['hastoc10']=hs
    return h4

def add_h1_features(h1):
    h1=add_ha(h1,'h1ha')
    h1['hour']=h1.time.dt.hour
    h1['same_hour_med20']=h1.groupby('hour').tick_volume.transform(lambda s:s.shift(1).rolling(20,min_periods=20).median())
    h1['rel_activity20']=h1.tick_volume/h1.same_hour_med20
    return h1

if __name__=='__main__':
    h4=add_h4_features(load_bars('GOLD#_H4_202201030000_202608282000.csv'))
    actual=parse_report(); ideal=build_ideal_children(h4)
    canon=actual[(actual.entry_time>=START)&(actual.exit_time<=CUTOFF)].copy()
    j=canon.merge(ideal,on=['journey','child','side'],how='left',validate='one_to_one',indicator=True)
    print('actual',len(actual),'canonical',len(canon),'ideal',len(ideal),'joined both',(j._merge=='both').sum())
    print('canonical wins/loss/flat', (canon.profit>0).sum(),(canon.profit<0).sum(),(canon.profit==0).sum(), canon.profit.sum())
    add=j[j.child>=2]
    print('addons',len(add),'wins/loss', (add.profit>0).sum(),(add.profit<0).sum())
    for name,m in [('w<=1',(add.profit>0)&(add.hold_hours<=1)),('w1-4',(add.profit>0)&(add.hold_hours>1)&(add.hold_hours<4)),('loss4-8',(add.profit<0)&(add.hold_hours>=4)&(add.hold_hours<8)),('>=8',(add.hold_hours>=8))]:
        g=add[m]; print(name,len(g),'net',g.profit.sum(),'median h',g.hold_hours.median())
