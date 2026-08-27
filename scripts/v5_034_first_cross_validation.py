#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd

RULE = '240min'
CANDIDATE = 'V5_FIRST_CROSS_240M_HALF_EMA_RUNNER'
REQUIRED_YEARS = (2023, 2024, 2025)
REQUIRED_MONTHS = tuple(range(1, 13))
VALIDATION_MARKETS = ('XAUJPY#', 'XAUCNH#', 'GAUCNH#', 'GAUUSD#')
BOOTSTRAP_REPS = 100_000
BOOTSTRAP_SEED = 5034

REQ_COLS = ['<DATE>','<TIME>','<OPEN>','<HIGH>','<LOW>','<CLOSE>','<SPREAD>']

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def _read_one(path: Path) -> pd.DataFrame:
    d=pd.read_csv(path,sep='\t',usecols=REQ_COLS)
    idx=pd.to_datetime(d['<DATE>'].astype(str)+' '+d['<TIME>'].astype(str),format='%Y.%m.%d %H:%M:%S',errors='raise')
    q=pd.DataFrame({
        'open':pd.to_numeric(d['<OPEN>'],errors='raise').to_numpy(float),
        'high':pd.to_numeric(d['<HIGH>'],errors='raise').to_numpy(float),
        'low':pd.to_numeric(d['<LOW>'],errors='raise').to_numpy(float),
        'close':pd.to_numeric(d['<CLOSE>'],errors='raise').to_numpy(float),
        'spread_points':pd.to_numeric(d['<SPREAD>'],errors='raise').to_numpy(float),
    },index=idx)
    return q

def audit_and_load_m1(paths: list[Path], point: float) -> tuple[pd.DataFrame, dict]:
    if not paths:
        raise SystemExit('FAIL-CLOSED no input files supplied')
    if not (math.isfinite(point) and point>0):
        raise SystemExit(f'FAIL-CLOSED invalid point {point!r}')
    parts=[]; file_audits=[]
    for p in paths:
        if not p.exists(): raise SystemExit(f'FAIL-CLOSED missing {p}')
        q=_read_one(p)
        if q.empty: raise SystemExit(f'FAIL-CLOSED empty input file {p}')
        vals=q[['open','high','low','close','spread_points']].to_numpy(float)
        if not np.isfinite(vals).all(): raise SystemExit(f'FAIL-CLOSED non-finite numeric value in {p}')
        if q.index.has_duplicates: raise SystemExit(f'FAIL-CLOSED duplicate timestamp in {p}')
        if not q.index.is_monotonic_increasing: raise SystemExit(f'FAIL-CLOSED unsorted timestamp in {p}')
        if bool(((q.index.second != 0) | (q.index.microsecond != 0)).any()):
            raise SystemExit(f'FAIL-CLOSED non-M1-aligned timestamp in {p}')
        bad_ohlc=(q.high < q[['open','close','low']].max(axis=1)) | (q.low > q[['open','close','high']].min(axis=1))
        if bool(bad_ohlc.any()): raise SystemExit(f'FAIL-CLOSED invalid OHLC geometry in {p}')
        if bool((q.spread_points<0).any()): raise SystemExit(f'FAIL-CLOSED negative spread in {p}')
        y=q.index.year
        file_audits.append({
            'path':str(p), 'sha256':sha256_file(p), 'rows':int(len(q)),
            'first_ts':q.index[0].isoformat(), 'last_ts':q.index[-1].isoformat(),
            'years':{str(int(yy)):int((y==yy).sum()) for yy in sorted(set(y))},
            'spread_points_median':float(q.spread_points.median()),
            'spread_points_min':float(q.spread_points.min()),
            'spread_points_max':float(q.spread_points.max()),
            'zero_spread_rows':int((q.spread_points==0).sum()),
        })
        parts.append(q)
    q=pd.concat(parts)
    if q.index.has_duplicates: raise SystemExit('FAIL-CLOSED duplicate timestamp across input files')
    if not q.index.is_monotonic_increasing: raise SystemExit('FAIL-CLOSED input file order is not chronological')
    present=sorted(set(int(x) for x in q.index.year))
    expected_years=list(REQUIRED_YEARS)
    if present != expected_years:
        missing=[y for y in REQUIRED_YEARS if y not in present]
        extra=[y for y in present if y not in REQUIRED_YEARS]
        raise SystemExit(f'FAIL-CLOSED validation years must be exactly {expected_years}; missing={missing} extra={extra}')
    months_by_year={}
    for y in REQUIRED_YEARS:
        counts=q.loc[q.index.year==y].groupby(q.loc[q.index.year==y].index.month).size()
        months_by_year[str(y)]={str(m):int(counts.get(m,0)) for m in REQUIRED_MONTHS}
        missing_months=[m for m in REQUIRED_MONTHS if counts.get(m,0)==0]
        if missing_months:
            raise SystemExit(f'FAIL-CLOSED missing calendar months for {y}: {missing_months}')
    audit={
        'point':float(point), 'files':file_audits, 'rows_total':int(len(q)),
        'first_ts':q.index[0].isoformat(), 'last_ts':q.index[-1].isoformat(),
        'present_years':present, 'rows_by_year_month':months_by_year,
    }
    return q,audit

def signal_bars(q: pd.DataFrame) -> pd.DataFrame:
    b=q.resample(RULE,closed='left',label='right').agg({'open':'first','high':'max','low':'min','close':'last','spread_points':'median'}).dropna()
    c=b.close
    b['fast']=c.rolling(3).mean()-c.rolling(10).mean()
    b['slow']=b.fast.rolling(16).mean()
    b['ema20']=c.ewm(span=20,adjust=False,min_periods=20).mean()
    return b.dropna().copy()

def detect_setups(b: pd.DataFrame, point: float) -> list[dict]:
    ts=b.index.to_numpy();h=b.high.to_numpy();l=b.low.to_numpy();f=b.fast.to_numpy();s=b.slow.to_numpy();n=len(b)
    last_down=None;last_up=None;reg=0;ci=None;base=None;seen=False;pull_i=None;used=False;out=[]
    for i in range(1,n-2):
        if s[i-1]>=0 and s[i]<0:
            last_down=i;reg=-1;ci=i;base=np.max(h[last_up:i+1]) if last_up is not None else None
            seen=f[i]<0;pull_i=None;used=False;continue
        if s[i-1]<=0 and s[i]>0:
            last_up=i;reg=1;ci=i;base=np.min(l[last_down:i+1]) if last_down is not None else None
            seen=f[i]>0;pull_i=None;used=False;continue
        if reg==1 and s[i]>0:
            if f[i]>0: seen=True
            if pull_i is None and seen and f[i-1]>=0 and f[i]<0: pull_i=i
        elif reg==-1 and s[i]<0:
            if f[i]<0: seen=True
            if pull_i is None and seen and f[i-1]<=0 and f[i]>0: pull_i=i
        if pull_i is None or used or base is None or i<pull_i+2: continue
        k=i-1;d=reg
        pivot=(l[k]<l[k-1] and l[k]<l[k+1]) if d==1 else (h[k]>h[k-1] and h[k]>h[k+1])
        if not pivot: continue
        used=True;pext=l[k] if d==1 else h[k]
        if (d==1 and pext<=base) or (d==-1 and pext>=base): continue
        trigger=h[i]+point if d==1 else l[i]-point
        stop=pext-point if d==1 else pext+point
        if d*(trigger-stop)<=0: continue
        target=np.max(h[ci:pull_i]) if d==1 else np.min(l[ci:pull_i])
        expiry=ts[-1]
        for j in range(i+1,n):
            if (s[j]<=0 if d==1 else s[j]>=0): expiry=ts[j];break
        out.append({'direction':int(d),'setup_i':int(i),'setup_end':pd.Timestamp(ts[i]),'pivot_i':int(k),'pull_i':int(pull_i),'trigger':float(trigger),'stop0':float(stop),'base_ext':float(base),'struct_target':float(target),'expiry':pd.Timestamp(expiry),'year':int(pd.Timestamp(ts[i]).year)})
    return out

def find_fill(q: pd.DataFrame,e:dict,point:float)->dict:
    idx=q.index.to_numpy();o=q.open.to_numpy();h=q.high.to_numpy();l=q.low.to_numpy();sp=q.spread_points.to_numpy()
    d=e['direction'];tr=e['trigger'];st=e['stop0'];base=e['base_ext'];target=e['struct_target']
    start=np.searchsorted(idx,np.datetime64(e['setup_end']),side='left');end=np.searchsorted(idx,np.datetime64(e['expiry']),side='left')
    for j in range(start,min(end,len(idx))):
        invalid=(l[j]<=base if d==1 else h[j]>=base);hit=(h[j]>=tr if d==1 else l[j]<=tr)
        if invalid and hit:return {'fill_status':'ambiguous_prefill'}
        if invalid:return {'fill_status':'invalid_prefill'}
        if hit:
            entry=max(tr,o[j]) if d==1 else min(tr,o[j])
            if (l[j]<=st if d==1 else h[j]>=st):return {'fill_status':'ambiguous_fillstop','fill_ts':pd.Timestamp(idx[j])}
            risk=d*(entry-st)
            if risk<=0:return {'fill_status':'bad_risk'}
            target_r=d*(target-entry)/risk
            if target_r<=0:return {'fill_status':'no_target','fill_ts':pd.Timestamp(idx[j]),'entry':float(entry),'risk':float(risk),'target_r':float(target_r)}
            cost=2*sp[j]*point/risk
            return {'fill_status':'filled','fill_i':int(j),'fill_ts':pd.Timestamp(idx[j]),'entry':float(entry),'risk':float(risk),'target_r':float(target_r),'cost_r':float(cost)}
    return {'fill_status':'unfilled'}

def adverse_time_arrays(b: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    long_mask=(b.close<b.ema20)|(b.slow<=0)
    short_mask=(b.close>b.ema20)|(b.slow>=0)
    return (b.index[long_mask].to_numpy(dtype="datetime64[ns]"),
            b.index[short_mask].to_numpy(dtype="datetime64[ns]"))

def manage_candidate(q:pd.DataFrame,adv_long:np.ndarray,adv_short:np.ndarray,fill:dict,e:dict)->dict:
    if fill.get('fill_status')!='filled':return {'candidate_status':'not_eligible','gross_r':np.nan,'net_r':np.nan}
    idx=q.index.to_numpy();o=q.open.to_numpy();h=q.high.to_numpy();l=q.low.to_numpy();d=e['direction'];entry=float(fill['entry']);risk=float(fill['risk']);stop=float(e['stop0']);cost=float(fill['cost_r']);one=entry+d*risk;start=int(fill['fill_i'])
    adv=adv_long if d==1 else adv_short
    partial=False;next_adv=None
    for j in range(start,len(idx)):
        ts=pd.Timestamp(idx[j])
        # Contract parity: a completed 240m adverse signal is executable at this M1 open.
        # The hard BE stop remains active intrabar, therefore open-time adverse exit has priority
        # over the same M1 bar's later high/low BE observation.
        if partial and next_adv is not None and ts>=next_adv:
            runner_r=d*(o[j]-entry)/risk;gross=0.5+0.5*runner_r
            return {'candidate_status':'ema_slow','gross_r':float(gross),'net_r':float(gross-cost),'end_ts':ts}
        astop=entry if partial else stop
        hit_stop=(l[j]<=astop if d==1 else h[j]>=astop)
        hit_1=(h[j]>=one if d==1 else l[j]<=one) if not partial else False
        if not partial:
            if hit_stop and hit_1:return {'candidate_status':'ambiguous_pre1','gross_r':np.nan,'net_r':np.nan,'end_ts':ts}
            if hit_stop:return {'candidate_status':'loss','gross_r':-1.0,'net_r':-1.0-cost,'end_ts':ts}
            if hit_1:
                partial=True
                pos=np.searchsorted(adv,np.datetime64(ts),side='right')
                next_adv=pd.Timestamp(adv[pos]) if pos<len(adv) else None
                if (l[j]<=entry if d==1 else h[j]>=entry):return {'candidate_status':'ambiguous_partial','gross_r':np.nan,'net_r':np.nan,'end_ts':ts}
        elif hit_stop:
            return {'candidate_status':'partial_be','gross_r':0.5,'net_r':0.5-cost,'end_ts':ts}
    return {'candidate_status':'censored','gross_r':np.nan,'net_r':np.nan}

def metrics(df:pd.DataFrame)->dict:
    r=df[df.net_r.notna()].copy();pos=r[r.net_r>0]
    return {'n':int(len(r)),'wr':float((r.net_r>0).mean()) if len(r) else None,'avg_positive_net_r':float(pos.net_r.mean()) if len(pos) else None,'ev_net_r':float(r.net_r.mean()) if len(r) else None,'total_net_r':float(r.net_r.sum()) if len(r) else None,'avg_cost_r':float(r.cost_r.mean()) if len(r) else None}

def weekly_block_bootstrap(rr:pd.DataFrame)->dict:
    x=rr.copy();iso=x.fill_ts.dt.isocalendar();x['cluster']=x.symbol.astype(str)+'|'+iso.year.astype(str)+'-'+iso.week.astype(str)
    stats=[]
    for _,g in x.groupby('cluster',sort=True):
        z=g.net_r.to_numpy(float);p=z[z>0];stats.append((len(z),z.sum(),(z>0).sum(),p.sum(),len(p)))
    a=np.asarray(stats,float);n=len(a);rng=np.random.default_rng(BOOTSTRAP_SEED)
    ev=[];wr=[];ap=[];batch=5000
    for start in range(0,BOOTSTRAP_REPS,batch):
        m=min(batch,BOOTSTRAP_REPS-start);ids=rng.integers(0,n,size=(m,n));s=a[ids].sum(axis=1)
        ev.append(s[:,1]/s[:,0]);wr.append(s[:,2]/s[:,0]);ap.append(np.divide(s[:,3],s[:,4],out=np.full(m,np.nan),where=s[:,4]>0))
    def ci(parts):
        z=np.concatenate(parts);q=np.nanquantile(z,[0.025,0.975]);return [float(q[0]),float(q[1])]
    return {'cluster_definition':'symbol x ISO calendar week of fill_ts','clusters':int(n),'reps':BOOTSTRAP_REPS,'seed':BOOTSTRAP_SEED,'ev_95':ci(ev),'wr_95':ci(wr),'avg_positive_net_r_95':ci(ap)}

def evaluate_gates(summary:dict)->dict:
    p=summary['pooled']
    A=bool(p['n'] and p['wr']>=0.50 and p['avg_positive_net_r'] is not None and p['avg_positive_net_r']>1.0 and p['ev_net_r'] is not None and p['ev_net_r']>0)
    market_status={};positive_adequate=0
    for sym,m in summary['markets'].items():
        ov=m['overall'];n=ov['n'];ev=ov['ev_net_r']
        if n<40: st='INSUFFICIENT'
        elif ev is not None and ev>0: st='POSITIVE';positive_adequate+=1
        else: st='NONPOSITIVE'
        market_status[sym]=st
    B=positive_adequate>=3
    C=all(str(y) in summary['pooled_years'] and summary['pooled_years'][str(y)]['ev_net_r'] is not None and summary['pooled_years'][str(y)]['ev_net_r']>0 for y in REQUIRED_YEARS)
    D=all(v['ev_net_r'] is not None and v['ev_net_r']>0 for v in summary['leave_one_market_out'].values())
    E=summary['bootstrap']['ev_95'][0]>0
    if A and B and C and D and E: verdict='PASS'
    elif A and B and C and D and not E: verdict='INCONCLUSIVE_UNCERTAINTY'
    else: verdict='FAIL'
    return {'A_pooled_economics':A,'B_market_breadth':B,'C_temporal_breadth':C,'D_concentration':D,'E_uncertainty':E,'F_market_sample_status':market_status,'positive_adequate_markets':int(positive_adequate),'verdict':verdict}

def validate_data_map(dm:dict)->None:
    actual=set(dm)
    expected=set(VALIDATION_MARKETS)
    if actual != expected:
        missing=sorted(expected-actual); extra=sorted(actual-expected)
        raise SystemExit(f'FAIL-CLOSED validation market panel mismatch; missing={missing} extra={extra}')
    for sym in VALIDATION_MARKETS:
        spec=dm[sym]
        if 'point' not in spec or 'files' not in spec:
            raise SystemExit(f'FAIL-CLOSED incomplete data-map spec for {sym}')
        paths=[Path(x) for x in spec['files']]
        if not paths:
            raise SystemExit(f'FAIL-CLOSED no input files for {sym}')
        stem=sym.replace('#','').lower()
        for path in paths:
            if stem not in path.name.lower():
                raise SystemExit(f'FAIL-CLOSED filename does not identify {sym}: {path.name}')

def build_preflight(dm:dict)->dict:
    validate_data_map(dm)
    audit={'candidate':CANDIDATE,'required_years':list(REQUIRED_YEARS),'validation_markets':list(VALIDATION_MARKETS),'markets':{}}
    for sym,spec in dm.items():
        point=float(spec['point']);paths=[Path(x) for x in spec['files']]
        _,a=audit_and_load_m1(paths,point);audit['markets'][sym]=a
    return audit

def verify_expected_hashes(dm:dict, expected:dict)->None:
    validate_data_map(dm)
    if expected.get('candidate')!=CANDIDATE or expected.get('required_years')!=list(REQUIRED_YEARS) or expected.get('validation_markets')!=list(VALIDATION_MARKETS):
        raise SystemExit('FAIL-CLOSED expected audit contract mismatch')
    if set(expected.get('markets',{}))!=set(dm):
        raise SystemExit('FAIL-CLOSED expected audit market set mismatch')
    for sym,spec in dm.items():
        exp=expected['markets'][sym]; point=float(spec['point']); paths=[Path(x) for x in spec['files']]
        if float(exp['point'])!=point: raise SystemExit(f'FAIL-CLOSED point changed for {sym}')
        exp_files=exp['files']
        if len(exp_files)!=len(paths): raise SystemExit(f'FAIL-CLOSED file count changed for {sym}')
        for p,ef in zip(paths,exp_files):
            if str(p)!=ef['path']: raise SystemExit(f'FAIL-CLOSED file path/order changed for {sym}')
            if not p.exists(): raise SystemExit(f'FAIL-CLOSED missing {p}')
            if sha256_file(p)!=ef['sha256']: raise SystemExit(f'FAIL-CLOSED raw SHA-256 changed for {p}')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-map',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--preflight-only',action='store_true');ap.add_argument('--expected-audit',type=Path)
    args=ap.parse_args();dm=json.loads(args.data_map.read_text(encoding='utf-8'));validate_data_map(dm);args.out_dir.mkdir(parents=True,exist_ok=True)
    audit_path=args.out_dir/'V5_034_INPUT_AUDIT.json'
    if args.preflight_only:
        audit=build_preflight(dm);audit_text=json.dumps(audit,indent=2,sort_keys=True);audit_path.write_text(audit_text,encoding='utf-8')
        print('input_audit',audit_path,'sha256',hashlib.sha256(audit_text.encode()).hexdigest(),flush=True);return
    if args.expected_audit is None:
        raise SystemExit('FAIL-CLOSED full validation requires --expected-audit from a completed preflight-only run')
    expected=json.loads(args.expected_audit.read_text(encoding='utf-8'));verify_expected_hashes(dm,expected)
    audit_text=json.dumps(expected,indent=2,sort_keys=True);audit_sha=hashlib.sha256(audit_text.encode()).hexdigest()
    all_ledgers=[];summary={'candidate':CANDIDATE,'markets':{},'input_audit_sha256':audit_sha}
    for sym,spec in dm.items():
        point=float(spec['point']);paths=[Path(x) for x in spec['files']];q,a=audit_and_load_m1(paths,point)
        if a!=expected['markets'][sym]: raise SystemExit(f'FAIL-CLOSED audited content changed for {sym}')
        b=signal_bars(q);adv_long,adv_short=adverse_time_arrays(b);rows=[]
        for e in detect_setups(b,point):
            f=find_fill(q,e,point);c=manage_candidate(q,adv_long,adv_short,f,e);rows.append({**e,**f,**c,'symbol':sym})
        out=pd.DataFrame(rows);path=args.out_dir/f"{sym.replace('#','')}_V5_034_LEDGER.csv";out.to_csv(path,index=False);all_ledgers.append(out);rr=out[out.net_r.notna()].copy()
        summary['markets'][sym]={'overall':metrics(out),'years':{str(int(y)):metrics(g) for y,g in rr.groupby('year')},'directions':{str(int(d)):metrics(g) for d,g in rr.groupby('direction')},'ledger_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        print(sym,summary['markets'][sym]['overall'],flush=True)
    pooled=pd.concat(all_ledgers,ignore_index=True);rr=pooled[pooled.net_r.notna()].copy();summary['pooled']=metrics(pooled);summary['pooled_years']={str(int(y)):metrics(g) for y,g in rr.groupby('year')};summary['leave_one_market_out']={sym:metrics(rr[rr.symbol!=sym]) for sym in dm};summary['bootstrap']=weekly_block_bootstrap(rr);summary['gates']=evaluate_gates(summary)
    sp=args.out_dir/'V5_034_VALIDATION_SUMMARY.json';sp.write_text(json.dumps(summary,indent=2),encoding='utf-8');print('summary',sp,flush=True);print('verdict',summary['gates']['verdict'],flush=True)
if __name__=='__main__':main()
