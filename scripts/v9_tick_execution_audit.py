#!/usr/bin/env python3
from __future__ import annotations
import argparse, zipfile, json, time, os, hashlib
from collections import Counter
from pathlib import Path


def key_m1_line(raw: bytes):
    # DATE<TAB>TIME... => YYYYMMDDHHMM integer for minute key
    # fixed date/time width in source files
    y=int(raw[0:4]); mo=int(raw[5:7]); d=int(raw[8:10]); h=int(raw[11:13]); mi=int(raw[14:16])
    return (((y*100+mo)*100+d)*100+h)*100+mi

def tick_stamp_ms(raw: bytes):
    # YYYY.MM.DD\tHH:MM:SS.mmm
    y=int(raw[0:4]); mo=int(raw[5:7]); d=int(raw[8:10]); h=int(raw[11:13]); mi=int(raw[14:16]); s=int(raw[17:19]); ms=int(raw[20:23])
    # ordinal-lite: datetime conversion avoided; lexicographic date integer insufficient for gap across day.
    # Use stdlib datetime only once per tick would be slow, so convert with civil-to-days algorithm.
    y0=y - (1 if mo <= 2 else 0)
    era=(y0 if y0>=0 else y0-399)//400
    yoe=y0-era*400
    mp=mo + (-3 if mo>2 else 9)
    doy=(153*mp+2)//5+d-1
    doe=yoe*365+yoe//4-yoe//100+doy
    days=era*146097+doe-719468
    return (((days*24+h)*60+mi)*60+s)*1000+ms

def q_from_counter(c:Counter, q:float):
    n=sum(c.values())
    if not n:return None
    target=max(1,int((n-1)*q)+1)
    acc=0
    for k in sorted(c):
        acc+=c[k]
        if acc>=target:return k
    return max(c)

def sha256(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def load_m1(path:Path):
    m={}
    with path.open('rb') as f:
        header=f.readline().rstrip(b'\r\n')
        for raw in f:
            if raw[:4] < b'2024': continue
            if raw[:4] > b'2024': break
            p=raw.rstrip(b'\r\n').split(b'\t')
            k=key_m1_line(raw)
            m[k]=(float(p[2]),float(p[3]),float(p[4]),float(p[5]),int(p[6]))
    return header.decode(),m

def scan_member(z:zipfile.ZipFile,name:str,m1:dict,overall_spread:Counter):
    t0=time.perf_counter(); ticks=bid_updates=ask_updates=0; backward=duplicates=0
    spread=Counter(); last_bid=last_ask=None; last_ms=None; gap_max_ms=0; gap_gt_1s=gap_gt_5s=gap_gt_30s=gap_gt_60s=0
    minute=None; cur=None; m1_missing_for_tick=0; mismatch=[]; minute_count=0
    order=Counter(); first_key=last_key=None

    def finish_minute(k,x):
        nonlocal m1_missing_for_tick, minute_count
        if k is None:return
        minute_count+=1
        ref=m1.get(k)
        if ref is None:
            m1_missing_for_tick+=1; return
        agg=(x['o'],x['h'],x['l'],x['c'],x['n'])
        if agg!=ref and len(mismatch)<20:mismatch.append({'minute':k,'m1':ref,'tick':agg})
        elif agg!=ref:mismatch.append(None)
        if x['n']>0 and x['h']!=x['l']:
            if x['t_high']<x['t_low']:order['HIGH_BEFORE_LOW']+=1
            elif x['t_low']<x['t_high']:order['LOW_BEFORE_HIGH']+=1
            else:order['SAME_TICK']+=1
        elif x['n']>0:order['FLAT']+=1

    with z.open(name) as f:
        header=f.readline().rstrip(b'\r\n').decode()
        for raw in f:
            if not raw.strip():continue
            ticks+=1
            p=raw.rstrip(b'\r\n').split(b'\t')
            k=key_m1_line(raw)
            first_key = k if first_key is None else first_key; last_key=k
            ms=tick_stamp_ms(raw)
            if last_ms is not None:
                if ms<last_ms:backward+=1
                elif ms==last_ms:duplicates+=1
                gap=ms-last_ms
                if gap>gap_max_ms:gap_max_ms=gap
                if gap>1000:gap_gt_1s+=1
                if gap>5000:gap_gt_5s+=1
                if gap>30000:gap_gt_30s+=1
                if gap>60000:gap_gt_60s+=1
            last_ms=ms
            bid=None; ask=None
            if len(p)>2 and p[2]:
                bid=float(p[2]); last_bid=bid; bid_updates+=1
            if len(p)>3 and p[3]:
                ask=float(p[3]); last_ask=ask; ask_updates+=1
            if last_bid is not None and last_ask is not None:
                cents=int(round((last_ask-last_bid)*100))
                spread[cents]+=1;overall_spread[cents]+=1
            if bid is None:continue
            if minute!=k:
                finish_minute(minute,cur)
                minute=k;cur={'o':bid,'h':bid,'l':bid,'c':bid,'n':1,'t_high':ms,'t_low':ms}
            else:
                if bid>cur['h']:cur['h']=bid;cur['t_high']=ms
                if bid<cur['l']:cur['l']=bid;cur['t_low']=ms
                cur['c']=bid;cur['n']+=1
        finish_minute(minute,cur)
    # exact mismatch count including entries beyond stored samples
    mismatch_count=sum(1 for x in mismatch if x is not None) + sum(1 for x in mismatch if x is None)
    # m1 minutes within member's observed first/last tick range that had no bid update
    m1_in_range=sum(1 for k in m1 if first_key<=k<=last_key)
    missing_tick_m1=m1_in_range-minute_count
    secs=time.perf_counter()-t0
    return {
      'member':name,'header':header,'ticks':ticks,'bid_updates':bid_updates,'ask_updates':ask_updates,
      'minute_bars_from_bid':minute_count,'first_minute':first_key,'last_minute':last_key,
      'm1_rows_in_observed_range':m1_in_range,'m1_missing_tick_minute':missing_tick_m1,
      'tick_minute_missing_m1':m1_missing_for_tick,'ohlc_tickvol_mismatch':mismatch_count,
      'mismatch_samples':[x for x in mismatch if x is not None][:5],
      'tick_timestamp_backward':backward,'tick_timestamp_duplicates':duplicates,
      'gap_max_ms':gap_max_ms,'gap_gt_1s':gap_gt_1s,'gap_gt_5s':gap_gt_5s,'gap_gt_30s':gap_gt_30s,'gap_gt_60s':gap_gt_60s,
      'spread_usd':{
        'events':sum(spread.values()),'p50':q_from_counter(spread,.50)/100 if spread else None,'p90':q_from_counter(spread,.90)/100 if spread else None,
        'p95':q_from_counter(spread,.95)/100 if spread else None,'p99':q_from_counter(spread,.99)/100 if spread else None,
        'max':max(spread)/100 if spread else None,
      },
      'intraminute_final_extrema_order':dict(order),
      'scan_seconds':secs,
      'uncompressed_bytes':z.getinfo(name).file_size,
      'throughput_uncompressed_MB_s':z.getinfo(name).file_size/(1024*1024)/secs if secs else None,
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tick-zip',type=Path,required=True);ap.add_argument('--m1',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    header,m1=load_m1(a.m1)
    overall_spread=Counter();months=[];t0=time.perf_counter()
    with zipfile.ZipFile(a.tick_zip) as z:
        names=sorted(n for n in z.namelist() if n.startswith('GOLD#_2024') and n.endswith('.csv'))
        for n in names:
            r=scan_member(z,n,m1,overall_spread);months.append(r);print(n, 'ticks',r['ticks'],'mins',r['minute_bars_from_bid'],'mis',r['ohlc_tickvol_mismatch'],'sec',round(r['scan_seconds'],1),flush=True)
    total_secs=time.perf_counter()-t0
    order=Counter();
    for r in months:order.update(r['intraminute_final_extrema_order'])
    report={
      'status':'PASS' if all(r['ohlc_tickvol_mismatch']==0 and r['tick_minute_missing_m1']==0 and r['m1_missing_tick_minute']==0 and r['tick_timestamp_backward']==0 for r in months) else 'CHECK',
      'scope':'2024 tick-vs-authoritative-M1 execution/tooling validation only; not strategy edge authority',
      'm1_basename':a.m1.name,'m1_sha256':sha256(a.m1),'m1_2024_rows':len(m1),'tick_zip_basename':a.tick_zip.name,'tick_zip_sha256':sha256(a.tick_zip),
      'months':months,
      'totals':{
        'tick_files':len(months),'ticks':sum(r['ticks'] for r in months),'bid_updates':sum(r['bid_updates'] for r in months),'ask_updates':sum(r['ask_updates'] for r in months),
        'minute_bars_from_bid':sum(r['minute_bars_from_bid'] for r in months),'ohlc_tickvol_mismatch':sum(r['ohlc_tickvol_mismatch'] for r in months),
        'm1_missing_tick_minute':sum(r['m1_missing_tick_minute'] for r in months),'tick_minute_missing_m1':sum(r['tick_minute_missing_m1'] for r in months),
        'tick_timestamp_backward':sum(r['tick_timestamp_backward'] for r in months),'tick_timestamp_duplicates':sum(r['tick_timestamp_duplicates'] for r in months),
        'intraminute_final_extrema_order':dict(order),
        'spread_usd':{
          'events':sum(overall_spread.values()),'p50':q_from_counter(overall_spread,.50)/100,'p90':q_from_counter(overall_spread,.90)/100,
          'p95':q_from_counter(overall_spread,.95)/100,'p99':q_from_counter(overall_spread,.99)/100,'max':max(overall_spread)/100,
        },
        'scan_seconds':total_secs,'uncompressed_tick_GB':sum(r['uncompressed_bytes'] for r in months)/(1024**3),
        'throughput_uncompressed_MB_s':sum(r['uncompressed_bytes'] for r in months)/(1024*1024)/total_secs,
      },
      'interpretation':[
        'Authoritative M1 OPEN/HIGH/LOW/CLOSE/TICKVOL is audited against non-empty BID tick updates.',
        'Spread diagnostics use forward-filled latest BID/ASK state and are descriptive execution-environment evidence, not a trading threshold.',
        'Final-high versus final-low order demonstrates tick data can resolve intraminute ordering that M1 OHLC alone cannot.',
      ]
    }
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report['totals'],indent=2,sort_keys=True));print('status',report['status'],'out',a.out)
if __name__=='__main__':main()
