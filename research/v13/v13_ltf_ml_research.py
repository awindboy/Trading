from __future__ import annotations
import pandas as pd, numpy as np, math, json, warnings
from pathlib import Path
from bisect import bisect_left, bisect_right, insort
from collections import defaultdict, deque
warnings.filterwarnings('ignore')
BASE=Path('/mnt/data')

def load(name):
    df=pd.read_csv(BASE/name, sep='\t')
    df['ts']=pd.to_datetime(df['<DATE>']+' '+df['<TIME>'], format='%Y.%m.%d %H:%M:%S')
    df=df.rename(columns={'<OPEN>':'open','<HIGH>':'high','<LOW>':'low','<CLOSE>':'close','<TICKVOL>':'tickvol','<SPREAD>':'spread'})
    return df[['ts','open','high','low','close','tickvol','spread']].copy()

def ha(df):
    hc=(df.open+df.high+df.low+df.close)/4.0
    ho=np.empty(len(df)); col=np.empty(len(df), dtype=np.int8)
    for i in range(len(df)):
        if i==0: ho[i]=(df.open.iloc[i]+df.close.iloc[i])/2
        else: ho[i]=(ho[i-1]+hc.iloc[i-1])/2
        d=hc.iloc[i]-ho[i]
        col[i]=1 if d>0 else (-1 if d<0 else (col[i-1] if i else 1))
    out=df.copy(); out['ha_open']=ho; out['ha_close']=hc.values; out['ha_color']=col
    out['ha_high']=np.maximum.reduce([out.high.values,ho,hc.values]); out['ha_low']=np.minimum.reduce([out.low.values,ho,hc.values])
    return out

def atr(df,n=180):
    pc=df.close.shift(1); tr=pd.concat([(df.high-df.low),(df.high-pc).abs(),(df.low-pc).abs()],axis=1).max(axis=1)
    return tr.rolling(n,min_periods=n).mean()

def pivots(df):
    h=df.high.values; l=df.low.values; n=len(df)
    hi=np.zeros(n,dtype=bool); lo=np.zeros(n,dtype=bool)
    for i in range(2,n-2):
        if h[i]>max(h[i-2],h[i-1]) and h[i]>=max(h[i+1],h[i+2]): hi[i]=1
        if l[i]<min(l[i-2],l[i-1]) and l[i]<=min(l[i+1],l[i+2]): lo[i]=1
    # known after second right bar completes; timestamps below are bar starts, add timeframe separately later
    return hi,lo

def build_objects(df, minutes):
    # exact V9-style FVG + swing-break OB candidates; first fresh touch found by segment tree.
    n=len(df); o=df.open.values; h=df.high.values; l=df.low.values; c=df.close.values
    hi_p,lo_p=pivots(df)
    objects=[]
    for i in range(2,n):
        born=pd.Timestamp(df.ts.iloc[i])+pd.Timedelta(minutes=minutes)
        if h[i-2] < l[i]: objects.append({'family':'FVG','dir':1,'lo':float(h[i-2]),'hi':float(l[i]),'born':born,'src_i':i,'born_i':i+1})
        if l[i-2] > h[i]: objects.append({'family':'FVG','dir':-1,'lo':float(h[i]),'hi':float(l[i-2]),'born':born,'src_i':i,'born_i':i+1})
    # OB via sorted active confirmed pivot levels.
    active_hi=[]; active_lo=[]; last_bear=None; last_bull=None; seen=set(); pending=defaultdict(list)
    for i in np.flatnonzero(hi_p):
        if i+3<n: pending[i+3].append(('H',float(h[i])))
    for i in np.flatnonzero(lo_p):
        if i+3<n: pending[i+3].append(('L',float(l[i])))
    from bisect import insort, bisect_left, bisect_right
    for i in range(n):
        k=bisect_left(active_hi,float(c[i]))
        if k>0:
            if last_bear is not None:
                key=(1,last_bear)
                if key not in seen:
                    seen.add(key); born=pd.Timestamp(df.ts.iloc[i])+pd.Timedelta(minutes=minutes)
                    objects.append({'family':'OB','dir':1,'lo':float(l[last_bear]),'hi':float(h[last_bear]),'born':born,'src_i':last_bear,'born_i':i+1})
            del active_hi[:k]
        k=bisect_right(active_lo,float(c[i]))
        if k<len(active_lo):
            if last_bull is not None:
                key=(-1,last_bull)
                if key not in seen:
                    seen.add(key); born=pd.Timestamp(df.ts.iloc[i])+pd.Timedelta(minutes=minutes)
                    objects.append({'family':'OB','dir':-1,'lo':float(l[last_bull]),'hi':float(h[last_bull]),'born':born,'src_i':last_bull,'born_i':i+1})
            del active_lo[k:]
        if c[i]<o[i]: last_bear=i
        elif c[i]>o[i]: last_bull=i
        for typ,lev in pending.get(i,[]): insort(active_hi if typ=='H' else active_lo,lev)
    odf=pd.DataFrame(objects)
    if odf.empty: return odf,pd.DataFrame()
    # segment tree stores max(high), min(low). earliest overlap leaf after born_i.
    size=1
    while size<n: size*=2
    maxh=np.full(2*size,-np.inf); minl=np.full(2*size,np.inf)
    maxh[size:size+n]=h; minl[size:size+n]=l
    for x in range(size-1,0,-1):
        maxh[x]=max(maxh[2*x],maxh[2*x+1]); minl[x]=min(minl[2*x],minl[2*x+1])
    def first_overlap(start,loz,hiz):
        def rec(node,nl,nr):
            if nr<=start or maxh[node]<loz or minl[node]>hiz: return -1
            if nr-nl==1: return nl if nl<n and l[nl]<=hiz and h[nl]>=loz else -1
            mid=(nl+nr)//2; z=rec(node*2,nl,mid)
            return z if z>=0 else rec(node*2+1,mid,nr)
        return rec(1,0,size)
    events=[]
    for r in odf.itertuples(index=False):
        j=first_overlap(int(r.born_i),float(r.lo),float(r.hi))
        if j<0: continue
        width=max(float(r.hi-r.lo),1e-9)
        if int(r.dir)==1:
            reaction='REJECT' if c[j]>r.hi else ('ACCEPT' if c[j]<r.lo else 'INSIDE')
            pen_wick=(r.hi-l[j])/width; pen_close=(r.hi-c[j])/width; rej=max(0,c[j]-r.hi); acc=max(0,r.lo-c[j])
        else:
            reaction='REJECT' if c[j]<r.lo else ('ACCEPT' if c[j]>r.hi else 'INSIDE')
            pen_wick=(h[j]-r.lo)/width; pen_close=(c[j]-r.lo)/width; rej=max(0,r.lo-c[j]); acc=max(0,c[j]-r.hi)
        tt=pd.Timestamp(df.ts.iloc[j])+pd.Timedelta(minutes=minutes)
        events.append({'bar_i':j,'touch_ts':tt,'family':r.family,'obj_dir':int(r.dir),'obj_lo':r.lo,'obj_hi':r.hi,'obj_width':width,
                       'obj_age_h':(tt-r.born).total_seconds()/3600,'reaction':reaction,'pen_wick':pen_wick,'pen_close':pen_close,'rej_dist':rej,'acc_dist':acc})
    return odf,pd.DataFrame(events)

def build_h4_context(h4):
    h4=ha(h4); h4['atr180']=atr(h4,180)
    h4['end']=h4.ts+pd.Timedelta(hours=4)
    # color run id and age
    h4['run_id']=(h4.ha_color!=h4.ha_color.shift()).cumsum().astype(int)
    h4['run_age']=h4.groupby('run_id').cumcount()+1
    # future flip end and exit open
    flip_end=np.array([np.datetime64('NaT')]*len(h4),dtype='datetime64[ns]'); exit_px=np.full(len(h4),np.nan); run_end_i=np.full(len(h4),-1)
    for rid,g in h4.groupby('run_id'):
        idx=g.index.to_numpy(); last=idx[-1]
        if last+1 < len(h4):
            fe=h4.end.iloc[last+1] # opposite bar completion
            ep=h4.open.iloc[last+2] if last+2 < len(h4) else h4.close.iloc[last+1]
            flip_end[idx]=np.datetime64(fe); exit_px[idx]=ep; run_end_i[idx]=last+1
    h4['flip_end']=pd.to_datetime(flip_end); h4['exit_px']=exit_px; h4['run_end_i']=run_end_i
    # oriented HA geometry
    rng=(h4.ha_high-h4.ha_low).replace(0,np.nan)
    h4['ha_body_atr']=(h4.ha_close-h4.ha_open).abs()/h4.atr180
    h4['ha_rng_atr']=rng/h4.atr180
    h4['raw_close_vs_ha_oriented']=(h4.close-h4.ha_close)*h4.ha_color/h4.atr180
    return h4

def map_latest_completed_h4(times,h4):
    ends=h4.end.values.astype('datetime64[ns]')
    arr=np.asarray(times,dtype='datetime64[ns]')
    return np.searchsorted(ends,arr,side='right')-1

def main():
    h4=load('GOLD#_H4_202201030000_202608282000.csv'); m30=load('GOLD#_M30_202201030100_202608282330.csv'); m15=load('GOLD#_M15_202201030100_202608282345.csv'); h1=load('GOLD#_H1_202201030100_202608282300.csv')
    h4=build_h4_context(h4)
    print('building objects...',flush=True)
    cache=BASE/'v13_m15_fresh_poi_events.csv'
    if cache.exists():
        ev15=pd.read_csv(cache,parse_dates=['touch_ts'])
    else:
        _,ev15=build_objects(m15,15); ev15.to_csv(cache,index=False)
    print('M15 touch events',len(ev15),flush=True)
    # H1 HA context
    h1h=ha(h1); h1h['end']=h1h.ts+pd.Timedelta(hours=1); h1h['atr_h4_proxy']=np.nan
    # M15 rolling/path helper
    m15['end']=m15.ts+pd.Timedelta(minutes=15)
    m15['body']=m15.close-m15.open; m15['range']=m15.high-m15.low
    m15['clv']=np.where(m15['range']>0,(2*m15.close-m15.high-m15.low)/m15['range'],0)
    m15['tv_med96']=m15.tickvol.rolling(96,min_periods=24).median()
    m15['tv_rel']=m15.tickvol/m15.tv_med96.replace(0,np.nan)
    # M30 pivots and pullback episodes -- chronological, array-based.
    hi_p,lo_p=pivots(m30); m30['end']=m30.ts+pd.Timedelta(minutes=30)
    piv=[]
    for i in np.flatnonzero(hi_p):
        if i+2<len(m30): piv.append(('H',i,pd.Timestamp(m30.ts.iloc[i]),pd.Timestamp(m30.ts.iloc[i+2])+pd.Timedelta(minutes=30),float(m30.high.iloc[i])))
    for i in np.flatnonzero(lo_p):
        if i+2<len(m30): piv.append(('L',i,pd.Timestamp(m30.ts.iloc[i]),pd.Timestamp(m30.ts.iloc[i+2])+pd.Timedelta(minutes=30),float(m30.low.iloc[i])))
    piv.sort(key=lambda x:x[3])
    ev15=ev15.sort_values('touch_ts').reset_index(drop=True)
    h4idx=map_latest_completed_h4(ev15.touch_ts.values,h4); ev15['h4_i']=h4idx; ev15=ev15[h4idx>=0].reset_index(drop=True)
    evtimes=ev15.touch_ts.values.astype('datetime64[ns]')
    # arrays
    m15_ts=m15.ts.values.astype('datetime64[ns]'); m15_end=m15.end.values.astype('datetime64[ns]')
    mo=m15.open.values; mh=m15.high.values; ml=m15.low.values; mc=m15.close.values
    run_start={int(rid):g.ts.iloc[0] for rid,g in h4.groupby('run_id')}
    records=[]; last_low=None; last_high=None
    for typ,pi,ptime,known,price in piv:
        anchor=last_low if typ=='H' else last_high
        direction=1 if typ=='H' else -1
        # update current pivot AFTER making episode, so opposite anchor is strictly earlier known pivot
        if anchor is not None:
            atype,api,aptime,aknown,aprice=anchor
            origin=float(aprice); extreme=float(price); imp=(extreme-origin)*direction
            if imp>0:
                start=known; hi4=map_latest_completed_h4([start],h4)[0]
                if hi4>=0 and np.isfinite(h4.atr180.iloc[hi4]) and int(h4.ha_color.iloc[hi4])==direction:
                    flip=h4.flip_end.iloc[hi4]
                    if pd.notna(flip) and flip>start:
                        rid=int(h4.run_id.iloc[hi4])
                        if ptime>=run_start[rid]:
                            # M15 range start..flip
                            si=np.searchsorted(m15_end,np.datetime64(start),side='left'); fi=np.searchsorted(m15_end,np.datetime64(flip),side='left')
                            if fi>si:
                                if direction==1:
                                    z=np.flatnonzero(mh[si:fi+1]>extreme)
                                else: z=np.flatnonzero(ml[si:fi+1]<extreme)
                                rebreak_i=(si+int(z[0])) if len(z) else None
                                rebreak_time=pd.Timestamp(m15_end[rebreak_i]) if rebreak_i is not None else None
                                cutoff=min(flip,rebreak_time) if rebreak_time is not None else flip
                                left=np.searchsorted(evtimes,np.datetime64(start),side='left'); right=np.searchsorted(evtimes,np.datetime64(cutoff),side='left')
                                chosen=None
                                for ei in range(left,right):
                                    er=ev15.iloc[ei]
                                    if int(er.obj_dir)==direction:
                                        chosen=er; break
                                if chosen is not None:
                                    e=chosen; et=pd.Timestamp(e.touch_ts); bi=int(e.bar_i); hi4e=int(e.h4_i); atrv=float(h4.atr180.iloc[hi4e])
                                    if hi4e>=0 and int(h4.ha_color.iloc[hi4e])==direction and np.isfinite(atrv) and atrv>0:
                                        ps=np.searchsorted(m15_ts,np.datetime64(ptime),side='left'); pe=bi
                                        if pe>=ps:
                                            if direction==1: pull_ext=float(np.min(ml[ps:pe+1])); depth=(extreme-pull_ext)/imp
                                            else: pull_ext=float(np.max(mh[ps:pe+1])); depth=(pull_ext-extreme)/imp
                                            f0=np.searchsorted(m15_end,np.datetime64(et),side='right'); f1=np.searchsorted(m15_end,np.datetime64(flip),side='right')
                                            if f1>f0:
                                                fh=mh[f0:f1]; fl=ml[f0:f1]
                                                if direction==1:
                                                    reb=bool(np.any(fh>extreme)); maxfav=float(np.max(fh)-mc[bi]); maxadv=float(mc[bi]-np.min(fl)); beyond=max(0.0,float(np.max(fh)-extreme))/imp
                                                else:
                                                    reb=bool(np.any(fl<extreme)); maxfav=float(mc[bi]-np.min(fl)); maxadv=float(np.max(fh)-mc[bi]); beyond=max(0.0,float(extreme-np.min(fl)))/imp
                                                entry_i=bi+1
                                                if entry_i<len(m15) and pd.Timestamp(m15.ts.iloc[entry_i])<flip:
                                                    entry=float(mo[entry_i]); exit_px=float(h4.exit_px.iloc[hi4e]) if np.isfinite(h4.exit_px.iloc[hi4e]) else float(mc[f1-1]); pnl=(exit_px-entry)*direction
                                                    br=m15.iloc[bi]; rng=max(float(br['range']),1e-9); body=(float(br.close)-float(br.open))*direction
                                                    close_loc=((float(br.close)-float(br.low))/rng if direction==1 else (float(br.high)-float(br.close))/rng)
                                                    opp_wick=((min(float(br.open),float(br.close))-float(br.low))/atrv if direction==1 else (float(br.high)-max(float(br.open),float(br.close)))/atrv)
                                                    p0=np.searchsorted(m15_end,np.datetime64(start),side='right'); p1=np.searchsorted(m15_end,np.datetime64(et),side='right')
                                                    if p1>p0:
                                                        po=mo[p0:p1]; ph=mh[p0:p1]; pl=ml[p0:p1]; pc=mc[p0:p1]
                                                        orient=(pc-po)*direction; path_sum=float(np.sum(ph-pl)); disp=float((pc[-1]-po[0])*direction); eff=disp/path_sum if path_sum>0 else 0; aligned_frac=float(np.mean(orient>0))
                                                        if direction==1: dd=(extreme-np.minimum.accumulate(pl))/imp
                                                        else: dd=(np.maximum.accumulate(ph)-extreme)/imp
                                                        depth_slope=float(dd[-1]-dd[max(0,len(dd)-3)]) if len(dd)>1 else 0
                                                        h1i=np.searchsorted(h1h.end.values.astype('datetime64[ns]'),np.datetime64(et),side='right')-1
                                                        if h1i>=0:
                                                            h1_align=int(h1h.ha_color.iloc[h1i])*direction; h1_body=((h1h.ha_close.iloc[h1i]-h1h.ha_open.iloc[h1i])*direction)/atrv; h1_rng=(h1h.high.iloc[h1i]-h1h.low.iloc[h1i])/atrv
                                                        else: h1_align=h1_body=h1_rng=np.nan
                                                        records.append({'event_ts':et,'year':et.year,'direction':direction,'h4_run_id':rid,'h4_run_age':int(h4.run_age.iloc[hi4e]),
                                                            'reaction':e.reaction,'family':e.family,'depth':depth,'depth_atr':abs(extreme-pull_ext)/atrv,'impulse_atr':imp/atrv,'pullback_h':(et-start).total_seconds()/3600,
                                                            'poi_width_atr':float(e.obj_width)/atrv,'poi_age_h':float(e.obj_age_h),'pen_wick':float(e.pen_wick),'pen_close':float(e.pen_close),'rej_atr':float(e.rej_dist)/atrv,'acc_atr':float(e.acc_dist)/atrv,
                                                            'm15_body_atr':body/atrv,'m15_range_atr':rng/atrv,'m15_close_loc':close_loc,'m15_opp_wick_atr':opp_wick,'m15_tv_rel':float(br.tv_rel) if np.isfinite(br.tv_rel) else np.nan,
                                                            'm15_path_eff':eff,'m15_aligned_frac':aligned_frac,'m15_path_body_atr':float(np.sum(orient))/atrv,'depth_slope3':depth_slope,
                                                            'h1_align':h1_align,'h1_body_atr':h1_body,'h1_rng_atr':h1_rng,'h4_ha_body_atr':float(h4.ha_body_atr.iloc[hi4e]),'h4_ha_rng_atr':float(h4.ha_rng_atr.iloc[hi4e]),'h4_raw_close_vs_ha':float(h4.raw_close_vs_ha_oriented.iloc[hi4e]),
                                                            'rebreak':int(reb),'remaining_mfe_atr':maxfav/atrv,'remaining_mae_atr':maxadv/atrv,'extension_impulse':beyond,'runner_pnl':pnl,'runner_pnl_atr':pnl/atrv,
                                                            'flip_time':flip,'entry':entry,'exit_px':exit_px,'impulse':imp,'origin':origin,'extreme':extreme,
                                                            'episode_start':start,'rebreak_time':rebreak_time,
                                                            'survived_depth': (float((extreme-np.min(ml[ps:rebreak_i+1]))/imp) if (rebreak_i is not None and direction==1) else (float((np.max(mh[ps:rebreak_i+1])-extreme)/imp) if rebreak_i is not None else np.nan))})
        if typ=='H': last_high=(typ,pi,ptime,known,price)
        else: last_low=(typ,pi,ptime,known,price)
    d=pd.DataFrame(records).sort_values('event_ts').reset_index(drop=True)
    # Resolution-safe prior successful correction envelope.
    d['prior_env']=np.nan; d['env_ratio']=np.nan; d['prior_success_n']=0; d['env_available']=0; d['env_breach']=0
    d['rebreak_time']=pd.to_datetime(d['rebreak_time'])
    for rid,g in d.groupby('h4_run_id'):
        idxs=g.sort_values('event_ts').index.tolist()
        for ix in idxs:
            t=d.at[ix,'event_ts']
            prev=d.loc[idxs]
            prev=prev[(prev.index!=ix)&prev.rebreak_time.notna()&(prev.rebreak_time<t)&prev.survived_depth.notna()]
            if len(prev):
                env=float(prev.survived_depth.max()); d.at[ix,'prior_env']=env; d.at[ix,'env_ratio']=float(d.at[ix,'depth'])/env if env>1e-12 else np.nan
                d.at[ix,'prior_success_n']=len(prev); d.at[ix,'env_available']=1; d.at[ix,'env_breach']=int(float(d.at[ix,'depth'])>env)
    d.to_csv(BASE/'v13_ltf_ml_dataset.csv',index=False)
    print('dataset',len(d),d.year.value_counts().sort_index().to_dict(),flush=True)
    print('rebreak',d.groupby('year').rebreak.mean().to_dict(), 'pnl',d.groupby('year').runner_pnl_atr.mean().to_dict(),flush=True)
    # model; exclude env features primary due above conservative note until resolution-safe rebuild
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import RobustScaler,OneHotEncoder
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.metrics import roc_auc_score,log_loss,brier_score_loss
    from scipy.stats import spearmanr
    import lightgbm as lgb
    cat=['reaction','family']
    base_loc=['depth','depth_atr','impulse_atr','pullback_h','h4_run_age','prior_env','env_ratio','prior_success_n','env_available','env_breach']
    react=['poi_width_atr','poi_age_h','pen_wick','pen_close','rej_atr','acc_atr','m15_body_atr','m15_range_atr','m15_close_loc','m15_opp_wick_atr']
    path=['m15_tv_rel','m15_path_eff','m15_aligned_frac','m15_path_body_atr','depth_slope3','h1_align','h1_body_atr','h1_rng_atr','h4_ha_body_atr','h4_ha_rng_atr','h4_raw_close_vs_ha']
    groups={'LOC':base_loc,'LOC_REACT':base_loc+react,'FULL':base_loc+react+path}
    rows=[]; pred_all=[]
    for testy in [2024,2025,2026]:
        train=d[(d.year<testy)&(d.flip_time<pd.Timestamp(f'{testy}-01-01'))].copy(); test=d[d.year==testy].copy()
        if len(train)<100 or len(test)<30: continue
        for gname,nums in groups.items():
            feats=nums+cat
            Xtr=train[feats]; Xte=test[feats]; ytr=train.rebreak; yte=test.rebreak
            pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('sc',RobustScaler(quantile_range=(10,90)))]),nums),('cat',OneHotEncoder(handle_unknown='ignore'),cat)])
            logit=Pipeline([('pre',pre),('m',LogisticRegression(C=.5,max_iter=1000,class_weight=None))]); logit.fit(Xtr,ytr); p=logit.predict_proba(Xte)[:,1]
            rows.append({'year':testy,'group':gname,'model':'ROBUST_LOGIT','auc':roc_auc_score(yte,p),'brier':brier_score_loss(yte,p),'logloss':log_loss(yte,p),'n':len(test)})
            if gname=='FULL':
                pred_all.append(test[['event_ts','year','h4_run_id','runner_pnl_atr','remaining_mfe_atr','extension_impulse','rebreak']].assign(model='ROBUST_LOGIT',p_rebreak=p))
            # fixed lightgbm with native one-hot via pandas dummies after impute
            Xall=pd.concat([train[feats],test[feats]],ignore_index=True)
            Xall=pd.get_dummies(Xall,columns=cat,dtype=float)
            Xall=Xall.replace([np.inf,-np.inf],np.nan)
            meds=Xall.iloc[:len(train)].median(numeric_only=True); Xall=Xall.fillna(meds).fillna(0)
            Xtr2=Xall.iloc[:len(train)]; Xte2=Xall.iloc[len(train):]
            clf=lgb.LGBMClassifier(n_estimators=180,learning_rate=.03,num_leaves=7,max_depth=3,min_child_samples=40,subsample=.85,colsample_bytree=.85,reg_lambda=2,verbosity=-1,random_state=7)
            clf.fit(Xtr2,ytr); p2=clf.predict_proba(Xte2)[:,1]
            rows.append({'year':testy,'group':gname,'model':'LGBM_SHALLOW','auc':roc_auc_score(yte,p2),'brier':brier_score_loss(yte,p2),'logloss':log_loss(yte,p2),'n':len(test)})
            if gname=='FULL':
                pred_all.append(test[['event_ts','year','h4_run_id','runner_pnl_atr','remaining_mfe_atr','extension_impulse','rebreak']].assign(model='LGBM_SHALLOW',p_rebreak=p2))
                # economic regression head on runner_pnl_atr and MFE; same fixed features
                reg=lgb.LGBMRegressor(n_estimators=180,learning_rate=.03,num_leaves=7,max_depth=3,min_child_samples=40,subsample=.85,colsample_bytree=.85,reg_lambda=2,objective='huber',verbosity=-1,random_state=9)
                reg.fit(Xtr2,train.runner_pnl_atr.clip(train.runner_pnl_atr.quantile(.01),train.runner_pnl_atr.quantile(.99)))
                pr=reg.predict(Xte2); sp=spearmanr(pr,test.runner_pnl_atr).statistic
                rows.append({'year':testy,'group':gname,'model':'LGBM_PNL_REG','auc':np.nan,'brier':np.nan,'logloss':np.nan,'n':len(test),'spearman':sp})
                pa=test[['event_ts','year','h4_run_id','runner_pnl_atr','remaining_mfe_atr','extension_impulse','rebreak']].copy(); pa['model']='LGBM_PNL_REG'; pa['score']=pr; pred_all.append(pa)
                reg2=lgb.LGBMRegressor(n_estimators=180,learning_rate=.03,num_leaves=7,max_depth=3,min_child_samples=40,subsample=.85,colsample_bytree=.85,reg_lambda=2,objective='huber',verbosity=-1,random_state=11)
                reg2.fit(Xtr2,train.remaining_mfe_atr.clip(0,train.remaining_mfe_atr.quantile(.99)))
                pm=reg2.predict(Xte2); sp2=spearmanr(pm,test.remaining_mfe_atr).statistic
                rows.append({'year':testy,'group':gname,'model':'LGBM_MFE_REG','auc':np.nan,'brier':np.nan,'logloss':np.nan,'n':len(test),'spearman':sp2})
                pb=test[['event_ts','year','h4_run_id','runner_pnl_atr','remaining_mfe_atr','extension_impulse','rebreak']].copy(); pb['model']='LGBM_MFE_REG'; pb['score']=pm; pred_all.append(pb)
    metrics=pd.DataFrame(rows); metrics.to_csv(BASE/'v13_ltf_ml_metrics.csv',index=False)
    preds=pd.concat(pred_all,ignore_index=True); preds.to_csv(BASE/'v13_ltf_ml_oof_predictions.csv',index=False)
    print('\nMETRICS'); print(metrics.to_string(index=False),flush=True)
    # ranking diagnostics for FULL models by test-year quintile independently (diagnostic only, not causal threshold action)
    outs=[]
    for (y,m),g in preds.groupby(['year','model']):
        scorecol='p_rebreak' if 'p_rebreak' in g.columns and g.p_rebreak.notna().any() and m!='LGBM_PNL_REG' and m!='LGBM_MFE_REG' else 'score'
        s=g[scorecol]
        if s.nunique()<5: continue
        q=pd.qcut(s.rank(method='first'),5,labels=False)
        for qi in range(5):
            z=g[q==qi]
            outs.append({'year':y,'model':m,'q':qi+1,'n':len(z),'rebreak':z.rebreak.mean(),'mean_pnl_atr':z.runner_pnl_atr.mean(),'median_pnl_atr':z.runner_pnl_atr.median(),'mean_mfe_atr':z.remaining_mfe_atr.mean(),'median_mfe_atr':z.remaining_mfe_atr.median(),'mean_ext_imp':z.extension_impulse.mean()})
    rank=pd.DataFrame(outs); rank.to_csv(BASE/'v13_ltf_ml_rank.csv',index=False)
    print('\nRANK TOP/BOT'); print(rank[rank.q.isin([1,5])].to_string(index=False),flush=True)
    # feature importance full LGBM final train through 2025, evaluate 2026; retrain to inspect
    train=d[(d.year<2026)&(d.flip_time<pd.Timestamp('2026-01-01'))]; feats=groups['FULL']+cat; X=pd.get_dummies(train[feats],columns=cat,dtype=float).replace([np.inf,-np.inf],np.nan); X=X.fillna(X.median(numeric_only=True)).fillna(0)
    clf=lgb.LGBMClassifier(n_estimators=180,learning_rate=.03,num_leaves=7,max_depth=3,min_child_samples=40,subsample=.85,colsample_bytree=.85,reg_lambda=2,verbosity=-1,random_state=7); clf.fit(X,train.rebreak)
    imp=pd.DataFrame({'feature':X.columns,'importance':clf.feature_importances_}).sort_values('importance',ascending=False); imp.to_csv(BASE/'v13_ltf_ml_feature_importance.csv',index=False)
    print('\nTOP FEATURES'); print(imp.head(20).to_string(index=False),flush=True)
    print(json.dumps({'dataset_n':len(d),'years':d.year.value_counts().sort_index().to_dict()},default=int))
if __name__=='__main__': main()
