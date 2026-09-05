import pandas as pd, numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, brier_score_loss

PATH='/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv'
d=pd.read_csv(PATH, sep='\t')
d.columns=[c.strip('<>').lower() for c in d.columns]
d['dt']=pd.to_datetime(d['date']+' '+d['time'], format='%Y.%m.%d %H:%M:%S')
d=d.set_index('dt').sort_index()
for c in ['open','high','low','close','tickvol','spread']:
    d[c]=pd.to_numeric(d[c],errors='coerce')
# basic minute quantities
ret=d['close'].diff().fillna(0.0)
rr=(d['high']-d['low']).fillna(0.0)
body=(d['close']-d['open']).abs().fillna(0.0)
absret=ret.abs()
rv=ret*ret

wins=[15,30,60,120,240,480,1440]
feat=pd.DataFrame(index=d.index)
for w in wins:
    feat[f'log_rv_{w}']=np.log1p(rv.rolling(w,min_periods=w).sum())
    feat[f'log_sumrange_{w}']=np.log1p(rr.rolling(w,min_periods=w).sum())
    feat[f'log_hl_{w}']=np.log1p(d['high'].rolling(w,min_periods=w).max()-d['low'].rolling(w,min_periods=w).min())
    feat[f'log_abs_{w}']=np.log1p(absret.rolling(w,min_periods=w).sum())
    feat[f'log_body_{w}']=np.log1p(body.rolling(w,min_periods=w).sum())
    feat[f'tickavg_{w}']=d['tickvol'].rolling(w,min_periods=w).mean()
# ratios / current state
feat['ret_15']=d['close'].diff(15)
feat['ret_60']=d['close'].diff(60)
feat['ret_240']=d['close'].diff(240)
feat['range_ratio_60_1440']=(d['high'].rolling(60,min_periods=60).max()-d['low'].rolling(60,min_periods=60).min())/(d['high'].rolling(1440,min_periods=1440).max()-d['low'].rolling(1440,min_periods=1440).min()+1e-9)
feat['rv_ratio_60_1440']=rv.rolling(60,min_periods=60).sum()/(rv.rolling(1440,min_periods=1440).sum()+1e-9)
feat['tick_ratio_60_1440']=d['tickvol'].rolling(60,min_periods=60).mean()/(d['tickvol'].rolling(1440,min_periods=1440).mean()+1e-9)
# time
hours=d.index.hour+d.index.minute/60
feat['sin_tod']=np.sin(2*np.pi*hours/24)
feat['cos_tod']=np.cos(2*np.pi*hours/24)

# H4 Wilder ATR14
h4=d[['open','high','low','close']].resample('4h',label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
prevclose=h4['close'].shift(1)
tr=pd.concat([(h4['high']-h4['low']),(h4['high']-prevclose).abs(),(h4['low']-prevclose).abs()],axis=1).max(axis=1)
# exact Wilder seeded at 14
atr=np.full(len(h4),np.nan)
trv=tr.to_numpy()
if len(trv)>=14:
    atr[13]=np.nanmean(trv[:14])
    for i in range(14,len(trv)):
        atr[i]=(atr[i-1]*13+trv[i])/14
h4['atr14']=atr

# map S for decision time: H4 block containing decision, use previous H4 row
h4_starts=h4.index.to_numpy(dtype='datetime64[ns]')
atrv=h4['atr14'].to_numpy()
def map_S(times):
    t=np.asarray(times,dtype='datetime64[ns]')
    # current h4 start = floor to 4h. find last h4 start <= current block start, then prev
    block=pd.DatetimeIndex(times).floor('4h').to_numpy(dtype='datetime64[ns]')
    pos=np.searchsorted(h4_starts,block,side='right')-1
    prev=pos-1
    out=np.full(len(t),np.nan)
    ok=(prev>=0)&(prev<len(atrv))
    out[ok]=atrv[prev[ok]]
    return out

# future excursion helper using forward rolling max/min on M1 after decision. decision t uses origin previous minute close; future starts t.
# We'll build decision frames by exact hour / 4h timestamps present as next minute boundary; origin is last M1 < decision.
all_idx=d.index
closev=d['close'].to_numpy(); hiv=d['high'].to_numpy(); lov=d['low'].to_numpy()

def build_decisions(freq, horizon_min, k):
    # decision times at regular grid, within data range, use searchsorted for origin/future positions
    start=all_idx.min().ceil(freq); end=all_idx.max().floor(freq)
    times=pd.date_range(start,end,freq=freq)
    arr=all_idx.to_numpy(dtype='datetime64[ns]')
    tarr=times.to_numpy(dtype='datetime64[ns]')
    p=np.searchsorted(arr,tarr,side='left') # first m1 >= decision
    origin=p-1
    # require previous minute reasonably close (<= 5m) and full future horizon with factual rows until time horizon (not row count)
    rows=[]
    S=map_S(times)
    for j,t in enumerate(times):
        if origin[j]<0 or p[j]>=len(d) or not np.isfinite(S[j]) or S[j]<=0: continue
        prevt=all_idx[origin[j]]
        if (t-prevt)>pd.Timedelta(minutes=5): continue
        tend=t+pd.Timedelta(minutes=horizon_min)
        q=np.searchsorted(arr,np.datetime64(tend),side='left')
        if q<=p[j]: continue
        # require end coverage near horizon end and at least 70% minute rows to avoid large gaps
        if all_idx[q-1] < tend-pd.Timedelta(minutes=5): continue
        if (q-p[j]) < int(horizon_min*0.7): continue
        origin_close=closev[origin[j]]
        mfe_up=np.nanmax(hiv[p[j]:q])-origin_close
        mfe_dn=origin_close-np.nanmin(lov[p[j]:q])
        y=max(mfe_up,mfe_dn)>=k*S[j]
        rows.append((t,origin[j],S[j],origin_close,int(y),mfe_up,mfe_dn))
    out=pd.DataFrame(rows,columns=['decision','origin_pos','S','origin_close','y','mfe_up','mfe_dn']).set_index('decision')
    # sample features at origin M1 row (strictly before decision)
    f=feat.iloc[out['origin_pos'].to_numpy()].copy(); f.index=out.index
    # normalize signed returns by S
    for c in ['ret_15','ret_60','ret_240']:
        f[c]=f[c]/out['S']
    out=pd.concat([out,f],axis=1).dropna()
    return out

specs=[('H1','1h',60,0.5),('H4','4h',240,1.0)]
for name,freq,h,k in specs:
    z=build_decisions(freq,h,k)
    cols=[c for c in z.columns if c not in ['origin_pos','S','origin_close','y','mfe_up','mfe_dn']]
    print('\n',name,'N',len(z),'base by year',z.groupby(z.index.year)['y'].agg(['count','mean']).to_dict('index'))
    for year in [2024,2025,2026]:
        tr=z[z.index.year<year]; te=z[z.index.year==year]
        if len(te)<100 or tr['y'].nunique()<2: continue
        model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,C=1.0))
        model.fit(tr[cols],tr['y'])
        p=model.predict_proba(te[cols])[:,1]
        auc=roc_auc_score(te['y'],p); bri=brier_score_loss(te['y'],p)
        # top decile / quartile actual rates
        q90=np.quantile(p,.9); q75=np.quantile(p,.75)
        print(year,'N',len(te),'base',te.y.mean(),'auc',auc,'brier',bri,'top25',te.loc[p>=q75,'y'].mean(),'top10',te.loc[p>=q90,'y'].mean(), 'pmean',p.mean())
