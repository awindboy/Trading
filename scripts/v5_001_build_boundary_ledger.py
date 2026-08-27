from pathlib import Path
import pandas as pd, numpy as np, gc, json, hashlib

RAW={
'GOLD#':[Path('/mnt/data/v3research/GOLD#_M1_202301030100_202312292357.csv'),Path('/mnt/data/v3research/GOLD#_M1_202401020100_202412302358.csv'),Path('/mnt/data/v3research/GOLD#_M1_202501020800_202512302358.csv')],
'BTCUSD#':[Path('/mnt/data/goldlike/BTCUSD#_M1_202301010000_202512310000.csv')],
'XAUEUR#':[Path('/mnt/data/goldlike/XAUEUR#_M1_202301030101_202512302358.csv')],
'USDJPY#':[Path('/mnt/data/goldlike/USDJPY#_M1_202301020901_202512310000.csv')],
}
POINT={'GOLD#':0.01,'BTCUSD#':0.01,'XAUEUR#':0.01,'USDJPY#':0.001}
HORIZONS=[5,15,30,60,240]
REFS=[('PD_EXTREME_HIGH','high',1,'EXTREME'),('PD_EXTREME_LOW','low',-1,'EXTREME'),('PD_PLACEBO_Q75','q75',1,'PLACEBO'),('PD_PLACEBO_Q25','q25',-1,'PLACEBO')]

def load(paths):
    parts=[]
    for p in paths:
        d=pd.read_csv(p,sep='\t',usecols=['<DATE>','<TIME>','<OPEN>','<HIGH>','<LOW>','<CLOSE>','<TICKVOL>','<SPREAD>'])
        idx=pd.to_datetime(d['<DATE>'].astype(str)+' '+d['<TIME>'].astype(str),format='%Y.%m.%d %H:%M:%S')
        q=pd.DataFrame(index=pd.DatetimeIndex(idx))
        for a,b in [('open','<OPEN>'),('high','<HIGH>'),('low','<LOW>'),('close','<CLOSE>'),('tickvol','<TICKVOL>'),('spread_points','<SPREAD>')]:
            q[a]=pd.to_numeric(d[b],errors='coerce').to_numpy(float)
        parts.append(q)
    q=pd.concat(parts).sort_index();q=q[~q.index.duplicated(keep='first')]
    return q

def causal_features(q,point):
    lr=np.log(q.close/q.close.shift(1))
    out=pd.DataFrame(index=q.index)
    out['spread_return']=q.spread_points*point/q.close
    for m in [15,60,240,1440]:
        rr=lr.rolling(f'{m}min',min_periods=3)
        r=rr.sum().shift(1); rv=np.sqrt((lr*lr).rolling(f'{m}min',min_periods=3).sum()).shift(1)
        sa=lr.abs().rolling(f'{m}min',min_periods=3).sum().shift(1)
        out[f'ret_{m}']=r;out[f'rv_{m}']=rv;out[f'eff_{m}']=(r.abs()/sa.replace(0,np.nan)).clip(0,1)
    tvmean=q.tickvol.rolling('60min',min_periods=3).mean().shift(1);tvstd=q.tickvol.rolling('60min',min_periods=3).std().shift(1)
    out['tvmean60']=tvmean;out['tvstd60']=tvstd
    h60=q.high.rolling('60min',min_periods=3).max().shift(1);l60=q.low.rolling('60min',min_periods=3).min().shift(1)
    h240=q.high.rolling('240min',min_periods=3).max().shift(1);l240=q.low.rolling('240min',min_periods=3).min().shift(1)
    out['compression_60_240']=(h60-l60)/(h240-l240).replace(0,np.nan)
    return out

def build(sym,paths):
    q=load(paths);f=causal_features(q,POINT[sym])
    times=q.index.view('i8');op=q.open.to_numpy();hi=q.high.to_numpy();lo=q.low.to_numpy();cl=q.close.to_numpy();tv=q.tickvol.to_numpy()
    day_key=q.index.normalize()
    g=q.groupby(day_key)
    daily=g.agg(high=('high','max'),low=('low','min'),close=('close','last'),open=('open','first'))
    daily['bar_count']=g.size()
    first=g.apply(lambda x:x.index[0]);last=g.apply(lambda x:x.index[-1])
    daily['span_minutes']=(last.values-first.values)/np.timedelta64(1,'m')
    daily['range']=daily.high-daily.low;daily['q75']=daily.low+.75*daily['range'];daily['q25']=daily.low+.25*daily['range']
    prev=daily.shift(1)
    rows=[];days=list(daily.index)
    for di in range(1,len(days)):
        d=days[di]; pr=prev.loc[d]
        rng=float(pr['range'])
        if not np.isfinite(rng) or rng<=0: continue
        t0=pd.Timestamp(d).value;t1=(pd.Timestamp(d)+pd.Timedelta(days=1)).value
        i0=int(np.searchsorted(times,t0,'left'));i1=int(np.searchsorted(times,t1,'left'))
        if i0>=i1: continue
        sub_idx=np.arange(i0,i1)
        pclose=np.empty(i1-i0);pclose[0]=cl[i0-1] if i0>0 else np.nan;pclose[1:]=cl[i0:i1-1]
        for ref,col,direction,role in REFS:
            b=float(pr[col])
            if direction==1: mask=(pclose<b)&(hi[i0:i1]>=b)
            else: mask=(pclose>b)&(lo[i0:i1]<=b)
            hit=np.flatnonzero(mask)
            if not len(hit): continue
            j=i0+int(hit[0]);ts=pd.Timestamp(times[j]);fr=f.iloc[j]
            row={'symbol':sym,'year':ts.year,'event_ts':ts.isoformat(),'day':str(pd.Timestamp(d).date()),'reference':ref,'reference_role':role,'direction':direction,
                 'boundary':b,'prev_day_high':float(pr['high']),'prev_day_low':float(pr['low']),'prev_day_range':rng,'prev_day_bar_count':int(pr['bar_count']),'prev_day_span_minutes':float(pr['span_minutes']),
                 'event_open':op[j],'event_high':hi[j],'event_low':lo[j],'event_close':cl[j],'prev_close':pclose[j-i0],
                 'gap_through':bool((direction==1 and op[j]>b) or (direction==-1 and op[j]<b)),
                 'event_close_rel':direction*(cl[j]-b)/rng,'event_penetration':((hi[j]-b) if direction==1 else (b-lo[j]))/rng,
                 'event_inside_excursion':((b-lo[j]) if direction==1 else (hi[j]-b))/rng,'tod_minute':ts.hour*60+ts.minute,'dow':ts.dayofweek,
                 'spread_return':float(fr['spread_return']) if np.isfinite(fr['spread_return']) else np.nan,'tickvol':tv[j],
                 'tickvol_z60':(tv[j]-fr['tvmean60'])/fr['tvstd60'] if np.isfinite(fr['tvstd60']) and fr['tvstd60']>0 else np.nan,
                 'compression_60_240':float(fr['compression_60_240']) if np.isfinite(fr['compression_60_240']) else np.nan}
            for m in [15,60,240,1440]:
                row[f'pre_ret_{m}_signed']=direction*fr[f'ret_{m}'] if np.isfinite(fr[f'ret_{m}']) else np.nan
                row[f'pre_rv_{m}']=fr[f'rv_{m}'] if np.isfinite(fr[f'rv_{m}']) else np.nan
                row[f'pre_eff_{m}']=fr[f'eff_{m}'] if np.isfinite(fr[f'eff_{m}']) else np.nan
            for m in [15,60,240]:
                target=times[j]-m*60_000_000_000
                k=int(np.searchsorted(times,target,'right')-1)
                row[f'dist_{m}_ago_signed']=direction*(b-cl[k])/rng if k>=0 else np.nan
            tvm=fr['tvmean60']
            row['effort_result_proxy_60']=row['pre_ret_60_signed']/np.sqrt(tvm) if np.isfinite(tvm) and tvm>0 and np.isfinite(row['pre_ret_60_signed']) else np.nan
            for h in HORIZONS:
                end=times[j]+h*60_000_000_000;k1=int(np.searchsorted(times,end,'right'))
                sl=slice(j,k1);cseg=cl[sl];hseg=hi[sl];lseg=lo[sl];tseg=times[sl]
                if len(cseg)==0: continue
                row[f'res_{h}']=direction*(cseg[-1]-b)/rng
                row[f'ret_{h}']=direction*np.log(cseg[-1]/op[j])
                if direction==1:
                    row[f'ext_{h}']=(hseg.max()-b)/rng;row[f'inside_{h}']=(b-lseg.min())/rng;beyond=cseg>b;re=cseg<b
                else:
                    row[f'ext_{h}']=(b-lseg.min())/rng;row[f'inside_{h}']=(hseg.max()-b)/rng;beyond=cseg<b;re=cseg>b
                row[f'beyond_frac_{h}']=float(np.mean(beyond))
                rr=np.flatnonzero(re);row[f'reentry_min_{h}']=float((tseg[rr[0]]-times[j])/60_000_000_000) if len(rr) else np.nan
                if len(cseg)>1:
                    lrs=np.diff(np.log(cseg));den=np.abs(lrs).sum();row[f'dir_eff_{h}']=direction*lrs.sum()/den if den>0 else np.nan;row[f'rv_post_{h}']=float(np.sqrt(np.square(lrs).sum()))
                    row[f'max_gap_{h}']=float(np.diff(tseg).max()/60_000_000_000)
                else:
                    row[f'dir_eff_{h}']=np.nan;row[f'rv_post_{h}']=np.nan;row[f'max_gap_{h}']=np.nan
                row[f'bars_{h}']=len(cseg);row[f'complete_{h}']=bool(tseg[-1]>=end-60_000_000_000)
            rows.append(row)
    out=pd.DataFrame(rows)
    print(sym,len(out),out.reference.value_counts().to_dict(),flush=True)
    return out

allx=[]
for s,p in RAW.items():
    allx.append(build(s,p));gc.collect()
ledger=pd.concat(allx,ignore_index=True)
out=Path('/mnt/data/v5_001_boundary_ledger.csv.gz');ledger.to_csv(out,index=False,compression='gzip')
meta={'rows':len(ledger),'columns':len(ledger.columns),'symbols':ledger.symbol.value_counts().to_dict(),'references':ledger.reference.value_counts().to_dict(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
Path('/mnt/data/v5_001_boundary_ledger_meta.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps(meta,indent=2),flush=True)
