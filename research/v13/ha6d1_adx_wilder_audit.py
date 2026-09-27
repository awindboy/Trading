from __future__ import annotations
import argparse, json, math, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

PERIOD=14

def sha256(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def read_h4(path: Path):
    d=pd.read_csv(path,sep='\t',encoding='utf-8-sig')
    d['signal']=pd.to_datetime(d['<DATE>']+' '+d['<TIME>'],format='%Y.%m.%d %H:%M:%S')
    for c in ['<OPEN>','<HIGH>','<LOW>','<CLOSE>']: d[c]=d[c].astype(float)
    return d

def smma(x: np.ndarray,n=14):
    out=np.full(len(x),np.nan,float)
    valid=np.where(np.isfinite(x))[0]
    if len(valid)<n:return out
    # Seed on first n consecutive valid values. The 2022->2024 warm-up makes seed choice immaterial at evaluation.
    for start in valid:
        end=start+n
        if end<=len(x) and np.all(np.isfinite(x[start:end])):
            out[end-1]=np.mean(x[start:end])
            for i in range(end,len(x)):
                if np.isfinite(x[i]): out[i]=(out[i-1]*(n-1)+x[i])/n
                else: out[i]=out[i-1]
            return out
    return out

def adx_wilder(h4: pd.DataFrame,n=14):
    hi=h4['<HIGH>'].to_numpy(float); lo=h4['<LOW>'].to_numpy(float); cl=h4['<CLOSE>'].to_numpy(float)
    up=np.full(len(h4),np.nan); dn=np.full(len(h4),np.nan); tr=np.full(len(h4),np.nan)
    for i in range(1,len(h4)):
        p=max(hi[i]-hi[i-1],0.0); m=max(lo[i-1]-lo[i],0.0)
        if p>m: m=0.0
        elif m>p: p=0.0
        else: p=m=0.0
        up[i]=p; dn[i]=m
        tr[i]=max(hi[i]-lo[i],abs(hi[i]-cl[i-1]),abs(lo[i]-cl[i-1]))
    atr=smma(tr,n); ps=smma(up,n); ns=smma(dn,n)
    pdi=np.where(atr>0,100*ps/atr,np.nan); ndi=np.where(atr>0,100*ns/atr,np.nan)
    denom=pdi+ndi
    dx=np.where(denom>0,100*np.abs(pdi-ndi)/denom,np.nan)
    adx=smma(dx,n)
    return pd.DataFrame({'signal':h4['signal'],'adx14_wilder':adx,'plus_di14':pdi,'minus_di14':ndi,'dx14':dx})

def eq_bins(s,k):
    good=s.notna()
    ranks=s[good].rank(method='first')
    bins=pd.Series(pd.NA,index=s.index,dtype='Int64')
    if len(ranks): bins.loc[good]=np.minimum(k-1,((ranks-1)*k/len(ranks)).astype(int)).astype(int)
    return bins

def rate(x):
    return float(np.mean(x.astype(float))) if len(x) else None

def med(x):
    z=pd.to_numeric(x,errors='coerce').dropna()
    return float(z.median()) if len(z) else None

def summarize(g):
    return {'decisions':int(len(g)),'journeys':int(g['journey'].nunique()),
            'next_flip':rate(g['next_flip']),'flip_within_3':rate(g['flip_within_3']),
            'peak_already':rate(g['peak_already']),
            'remaining_favorable_ranges_median':med(g['remaining_favorable_ranges']),
            'giveback_ranges_median':med(g['giveback_ranges'])}

def bin_summary(df,col,k=5):
    b=eq_bins(df[col],k); out={}
    for q in range(k): out[str(q+1)]=summarize(df[b==q])
    return out

def cat_summary(df,col):
    out={}
    for v,g in df.groupby(col,dropna=False): out[str(v)]=summarize(g)
    return out

def overlap_binary(df,field,base_cont,base_cat,min_each=10,bins=3):
    z=df.copy(); cellcols=[]
    for c in base_cont:
        bc='__b_'+c; z[bc]=eq_bins(z[c],bins); cellcols.append(bc)
    cellcols += list(base_cat)
    eligible=[]
    for _,g in z.groupby(cellcols,dropna=False,observed=True):
        a=g[g[field]==True]; b=g[g[field]==False]
        if len(a)>=min_each and len(b)>=min_each:
            eligible.append((a,b,min(len(a),len(b))))
    sw=sum(w for _,_,w in eligible)
    out={'eligible_cells':len(eligible),'decisions_in_eligible_cells':int(sum(len(a)+len(b) for a,b,_ in eligible)),
         'total_decisions':int(len(df)),'min_each':min_each,'continuous_bins':bins,
         'continuous_fields':base_cont,'categorical_fields':base_cat}
    for target in ['next_flip','flip_within_3','peak_already']:
        out[f'true_minus_false_{target}']=(sum(w*(rate(a[target])-rate(b[target])) for a,b,w in eligible)/sw if sw else None)
    return out

def overlap_extreme_quintiles(df,col,base_cont,base_cat,min_each=5,bins=3):
    z=df.copy(); z['__q']=eq_bins(z[col],5); cellcols=[]
    for c in base_cont:
        bc='__b_'+c; z[bc]=eq_bins(z[c],bins); cellcols.append(bc)
    cellcols += list(base_cat)
    eligible=[]
    for _,g in z.groupby(cellcols,dropna=False,observed=True):
        lo=g[g['__q']==0]; hi=g[g['__q']==4]
        if len(lo)>=min_each and len(hi)>=min_each: eligible.append((lo,hi,min(len(lo),len(hi))))
    sw=sum(w for _,_,w in eligible)
    out={'eligible_cells':len(eligible),'decisions_in_eligible_cells':int(sum(len(a)+len(b) for a,b,_ in eligible)),
         'total_decisions':int(len(df)),'min_each_extreme':min_each,'continuous_bins':bins,
         'continuous_fields':base_cont,'categorical_fields':base_cat}
    for target in ['next_flip','flip_within_3','peak_already']:
        out[f'q1_minus_q5_{target}']=(sum(w*(rate(lo[target])-rate(hi[target])) for lo,hi,w in eligible)/sw if sw else None)
    return out

def corr(df,a,b):
    z=df[[a,b]].apply(pd.to_numeric,errors='coerce').dropna()
    return float(z[a].corr(z[b])) if len(z)>2 else None

def main():
    p=argparse.ArgumentParser(); p.add_argument('--h4',type=Path,required=True); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    h4=read_h4(a.h4); adx=adx_wilder(h4,PERIOD)
    f=pd.read_csv(a.features,parse_dates=['signal','known_at']); y=pd.read_csv(a.labels,parse_dates=['signal'])
    assert len(f)==4108 and len(y)==4105
    # join only completed H4 values by the signal bar timestamp
    f=f.merge(adx,on='signal',how='left',validate='one_to_one')
    assert f['adx14_wilder'].notna().all()
    f['journey_di_margin']=f['side']*(f['plus_di14']-f['minus_di14'])
    f['di_state']=np.where(f['journey_di_margin']>0,'aligned',np.where(f['journey_di_margin']<0,'opposed','neutral'))
    f['di_aligned']=f['journey_di_margin']>0
    f['adx_change']=f['adx14_wilder'].diff()
    f['adx_rising']=f['adx_change']>0
    # The previous H4 is always chronologically prior even if Journey changes; ADX is market context, not Journey-local.
    rows=f.merge(y,on=['signal','journey'],how='inner',validate='one_to_one',suffixes=('','_label'))
    assert len(rows)==4105
    for c in ['next_flip','flip_within_3','peak_already']:
        if rows[c].dtype==object: rows[c]=rows[c].map({'True':True,'False':False})
        rows[c]=rows[c].astype(bool)
    for c in ['h4_delta_contract','h4_wick_present','h1_opposed','progress_rejection_or_return','ema50_slope_aligned','ema50_position_aligned','ema20_beyond_directional_boundary']:
        if rows[c].dtype==object: rows[c]=rows[c].map({'True':True,'False':False})
        rows[c]=rows[c].astype(bool)
    # Quintile labels frozen descriptively from full consumed population, never trade thresholds.
    rows['adx_quintile']=eq_bins(rows['adx14_wilder'],5)
    rows['di_margin_quintile']=eq_bins(rows['journey_di_margin'],5)
    rows['adx_change_quintile']=eq_bins(rows['adx_change'],5)
    rows['hastoc_quintile']=eq_bins(rows['journey_hastoc10'],5)
    rows['atr_delta_quintile']=eq_bins(rows['h4_abs_delta_atr14'],3)
    rows['atr_rawclose_quintile']=eq_bins(rows['journey_raw_close_minus_ha_close_atr14'],3)
    rows['adx_di_joint']=np.where(rows['di_aligned'],np.where(rows['adx_rising'],'DI_aligned_ADX_rising','DI_aligned_ADX_falling'),np.where(rows['adx_rising'],'DI_opposed_ADX_rising','DI_opposed_ADX_falling'))

    base_cont0=['h4_body_ratio','h4_raw_close_normalized']
    base_cat1=['h4_delta_contract','h4_wick_present']
    base_cat2=base_cat1+['h1_path_state','progress_rejection_or_return']
    base_cat3=base_cat2+['hastoc_quintile']
    base_cat4=base_cat3+['ema50_slope_aligned','ema50_position_aligned','ema20_beyond_directional_boundary']
    base_cont5=base_cont0+['h4_abs_delta_atr14','journey_raw_close_minus_ha_close_atr14']

    out={'all':summarize(rows),
         'adx_quintiles':bin_summary(rows,'adx14_wilder'),
         'di_alignment':cat_summary(rows,'di_state'),
         'adx_rising':cat_summary(rows,'adx_rising'),
         'adx_di_joint':cat_summary(rows,'adx_di_joint'),
         'di_margin_quintiles':bin_summary(rows,'journey_di_margin'),
         'adx_change_quintiles':bin_summary(rows,'adx_change'),
         'redundancy':{
             'corr_adx_body_ratio':corr(rows,'adx14_wilder','h4_body_ratio'),
             'corr_adx_abs_delta_atr14':corr(rows,'adx14_wilder','h4_abs_delta_atr14'),
             'corr_adx_hastoc':corr(rows,'adx14_wilder','journey_hastoc10'),
             'corr_di_margin_hastoc':corr(rows,'journey_di_margin','journey_hastoc10'),
             'corr_di_margin_ema50_slope_atr':corr(rows,'journey_di_margin','journey_ema50_slope_atr14'),
             'corr_di_margin_ema20_distance_atr':corr(rows,'journey_di_margin','journey_ha_close_to_ema20_boundary_atr14')},
         'overlap':{}}
    stages=[('h4_geometry',base_cont0,[]),('plus_delta_wick',base_cont0,base_cat1),('plus_h1_swing',base_cont0,base_cat2),('plus_hastoc',base_cont0,base_cat3),('plus_ma',base_cont0,base_cat4),('plus_atr_normalized',base_cont5,base_cat4)]
    for name,cont,cats in stages:
        out['overlap'][name]={
            'di_aligned':overlap_binary(rows,'di_aligned',cont,cats,10 if name in ('h4_geometry','plus_delta_wick') else 5),
            'adx_rising':overlap_binary(rows,'adx_rising',cont,cats,10 if name in ('h4_geometry','plus_delta_wick') else 5),
            'adx_q1_vs_q5':overlap_extreme_quintiles(rows,'adx14_wilder',cont,cats,5 if name in ('h4_geometry','plus_delta_wick') else 3)}

    # H1-opposition false-warning question.
    h1=rows[rows['h1_opposed']].copy(); assert len(h1)==1395
    out['h1_opposed']={'all':summarize(h1),'di_alignment':cat_summary(h1,'di_state'),'adx_rising':cat_summary(h1,'adx_rising'),'adx_quintiles':bin_summary(h1,'adx14_wilder'),
                       'joint':cat_summary(h1,'adx_di_joint'),
                       'full_stack_di_overlap':overlap_binary(h1,'di_aligned',base_cont5,base_cat4,3),
                       'full_stack_adx_rising_overlap':overlap_binary(h1,'adx_rising',base_cont5,base_cat4,3)}
    # Year/side and birth/continuation.
    out['year_side']={}
    for yr in [2024,2025,2026]:
        for side,label in [(1,'LONG'),(-1,'SHORT')]:
            g=rows[(rows.year==yr)&(rows.side==side)]
            out['year_side'][f'{yr}_{label}']={'all':summarize(g),'adx_quintiles':bin_summary(g,'adx14_wilder'),'di_alignment':cat_summary(g,'di_state'),'adx_rising':cat_summary(g,'adx_rising')}
    out['birth_continuation']={}
    for key,g in [('birth',rows[rows.journey_bar==1]),('continuation',rows[rows.journey_bar>1])]:
        out['birth_continuation'][key]={'all':summarize(g),'adx_quintiles':bin_summary(g,'adx14_wilder'),'di_alignment':cat_summary(g,'di_state'),'joint':cat_summary(g,'adx_di_joint')}
    # Long Journey tail preservation.
    tails=rows[rows['journey_closed_bars']>=10].copy(); assert tails['journey'].nunique()==88
    global_q=rows.set_index('signal')['adx_quintile']; tails['global_adx_q']=tails['signal'].map(global_q)
    events={
      'di_opposed':~tails['di_aligned'],
      'adx_falling':~tails['adx_rising'],
      'di_opposed_adx_falling':(~tails['di_aligned']) & (~tails['adx_rising']),
      'adx_lowest_global_quintile':tails['global_adx_q']==0,
      'h1_opposed_di_opposed':tails['h1_opposed'] & (~tails['di_aligned'])}
    out['long_journeys']={'journeys':88,'decisions':int(len(tails))}
    for name,mask in events.items():
        g=tails[mask]
        out['long_journeys'][name]={'journeys_with_event':int(g['journey'].nunique()),'event_decisions':int(len(g)),
            'event_not_next_flip':int((~g.next_flip).sum()),'event_next_flip':int(g.next_flip.sum()),
            'remaining_favorable_ranges_median':med(g['remaining_favorable_ranges'])}
    # useful numeric distributions, not thresholds
    out['distributions']={c:{'median':med(rows[c]),'q10':float(rows[c].quantile(.1)),'q90':float(rows[c].quantile(.9))} for c in ['adx14_wilder','journey_di_margin','adx_change']}

    feature_cols=list(f.columns)
    f.to_csv(a.output/'decision_features.csv',index=False)
    y.to_csv(a.output/'future_labels.csv',index=False)
    report={'status':'consumed-development-observation-only','authority_base':'40f97352e47c66cd3b952f74532b1b71969e79fd',
            'sources':{'h4_sha256':sha256(a.h4),'features_sha256':sha256(a.features),'labels_sha256':sha256(a.labels)},
            'formula':{'period':14,'family':'MetaQuotes/Welles Wilder ADX','warmup_start':str(h4.signal.iloc[0]),'mutually_exclusive_dm':True,'true_range':'max(high-low, abs(high-prev_close), abs(low-prev_close))'},
            'summary':out}
    (a.output/'summary.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
    print(json.dumps({'all':out['all'],'adx_quintiles':out['adx_quintiles'],'di_alignment':out['di_alignment'],'adx_rising':out['adx_rising'],'joint':out['adx_di_joint'],'h1_opposed':out['h1_opposed'],'long_journeys':out['long_journeys'],'overlap':out['overlap'],'redundancy':out['redundancy']},indent=2,default=str))
if __name__=='__main__': main()
