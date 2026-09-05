from pathlib import Path
import pandas as pd, numpy as np

M1_PATH=Path('/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv')
EV_PATHS=[Path('/mnt/data/oldp0_events_2024.csv'),Path('/mnt/data/oldp0_events_2025.csv'),Path('/mnt/data/oldp0_events_2026.csv')]
SCALES=[0.125,0.25,0.50]
LOOKBACK_MIN=480


def load_m1():
    x=pd.read_csv(M1_PATH,sep='\t',usecols=['<DATE>','<TIME>','<HIGH>','<LOW>','<CLOSE>'])
    ts=pd.to_datetime(x['<DATE>'].astype(str)+' '+x['<TIME>'].astype(str),format='%Y.%m.%d %H:%M:%S')
    out=pd.DataFrame({'high':x['<HIGH>'].to_numpy(float),'low':x['<LOW>'].to_numpy(float),'close':x['<CLOSE>'].to_numpy(float)},index=ts)
    return out


def dc_state(prices, times, theta):
    if len(prices)<2 or not np.isfinite(theta) or theta<=0:
        return dict(mode=0,age=np.nan,progress=np.nan,extprog=np.nan,retrace=np.nan,n_events=0,last2='')
    mode=0
    hi=lo=float(prices[0]); hi_t=lo_t=times[0]
    confirm_p=float(prices[0]); confirm_t=times[0]
    events=[]
    extreme=float(prices[0]); extreme_t=times[0]
    for p,t in zip(prices[1:],times[1:]):
        p=float(p)
        if mode==0:
            if p>hi: hi=p; hi_t=t
            if p<lo: lo=p; lo_t=t
            # deterministic tie order: larger normalized excursion from opposite extreme; exact tie -> no event until next point
            up=p-lo>=theta
            dn=hi-p>=theta
            if up and not dn:
                mode=1; confirm_p=p; confirm_t=t; events.append((t,1,p,lo)); extreme=p; extreme_t=t
            elif dn and not up:
                mode=-1; confirm_p=p; confirm_t=t; events.append((t,-1,p,hi)); extreme=p; extreme_t=t
        elif mode==1:
            if p>extreme: extreme=p; extreme_t=t
            if extreme-p>=theta:
                mode=-1; confirm_p=p; confirm_t=t; events.append((t,-1,p,extreme)); extreme=p; extreme_t=t
        else:
            if p<extreme: extreme=p; extreme_t=t
            if p-extreme>=theta:
                mode=1; confirm_p=p; confirm_t=t; events.append((t,1,p,extreme)); extreme=p; extreme_t=t
    if mode==0:
        return dict(mode=0,age=np.nan,progress=np.nan,extprog=np.nan,retrace=np.nan,n_events=0,last2='')
    cur=float(prices[-1])
    age=(times[-1]-confirm_t)/np.timedelta64(1,'m')
    progress=mode*(cur-confirm_p)/theta
    extprog=mode*(extreme-confirm_p)/theta
    retrace=mode*(extreme-cur)/theta
    last2='|'.join(str(e[1]) for e in events[-2:])
    return dict(mode=mode,age=float(age),progress=float(progress),extprog=float(extprog),retrace=float(retrace),n_events=len(events),last2=last2)


def first_touch(m1idx,hi,lo,decision,origin,S,mult,horizon_min):
    a=np.searchsorted(m1idx,np.datetime64(decision),side='left')
    b=np.searchsorted(m1idx,np.datetime64(decision+pd.Timedelta(minutes=horizon_min)),side='left')
    up=origin+mult*S; dn=origin-mult*S
    for i in range(a,min(b,len(m1idx))):
        hu=hi[i]>=up; hd=lo[i]<=dn
        if hu and hd: return 2, i-a+1 # ambiguous
        if hu: return 1, i-a+1
        if hd: return -1, i-a+1
    return 0, np.nan


def main():
    m1=load_m1(); idx=m1.index.to_numpy(dtype='datetime64[ns]'); cl=m1.close.to_numpy(float); hi=m1.high.to_numpy(float); lo=m1.low.to_numpy(float)
    ev=pd.concat([pd.read_csv(p) for p in EV_PATHS],ignore_index=True)
    ev['decision']=pd.to_datetime(ev.decision); ev['source_m5']=pd.to_datetime(ev.source_m5)
    rows=[]
    for r in ev.itertuples(index=False):
        dec=pd.Timestamp(r.decision); S=float(r.S); origin=float(r.origin_close)
        end=np.searchsorted(idx,np.datetime64(dec),side='left') # legal info strictly before decision
        start=np.searchsorted(idx,np.datetime64(dec-pd.Timedelta(minutes=LOOKBACK_MIN)),side='left')
        prices=cl[start:end]; times=idx[start:end]
        z={'year':int(r.year),'source_m5':r.source_m5,'decision':dec,'p15':float(r.p15),'S':S,'origin_close':origin}
        for s in SCALES:
            st=dc_state(prices,times,s*S); tag=str(s).replace('.','p')
            for k,v in st.items(): z[f'dc{tag}_{k}']=v
        modes=[z['dc0p125_mode'],z['dc0p25_mode'],z['dc0p5_mode']]
        z['align3']=int(modes[0]!=0 and modes[0]==modes[1]==modes[2])
        z['align3_dir']=modes[0] if z['align3'] else 0
        z['align_fast']=int(modes[0]!=0 and modes[0]==modes[1])
        z['align_fast_dir']=modes[0] if z['align_fast'] else 0
        z['small_counter_large']=int(modes[1]!=0 and modes[1]==modes[2] and modes[0]==-modes[2])
        z['large_dir']=modes[2]
        z['small_dir']=modes[0]
        z['small_recent']=int(np.isfinite(z['dc0p125_age']) and z['dc0p125_age']<=15)
        z['med_recent']=int(np.isfinite(z['dc0p25_age']) and z['dc0p25_age']<=30)
        for mult,hor,name in [(0.25,15,'ft25_15'),(0.50,30,'ft50_30')]:
            lab,t=first_touch(idx,hi,lo,dec,origin,S,mult,hor); z[name]=lab; z[name+'_bar']=t
        rows.append(z)
    out=pd.DataFrame(rows)
    # existing module membership from current M1 scenario controls
    scen=pd.read_csv('/mnt/data/v8_scenario_v3runner_m1.csv')
    scen['decision']=pd.to_datetime(scen.decision)
    modset=set(scen.decision)
    out['existing_module']=out.decision.isin(modset).astype(int)
    out.to_csv('/mnt/data/dc_glass_ceiling_events.csv',index=False)

    # summary tables
    periods=[]
    for y in [2024,2025,2026]:
        periods.append((str(y),out.year.eq(y)))
    periods += [('2024H1',(out.year.eq(2024)&(out.decision<'2024-07-01'))),('2024H2',(out.year.eq(2024)&(out.decision>='2024-07-01')))]
    rec=[]
    def add(name,mask,pdir_col,target='ft25_15'):
        for per,pm in periods:
            g=out[mask & pm & out[target].isin([-1,1])]
            if len(g):
                pred=g[pdir_col].to_numpy(int); yy=g[target].to_numpy(int)
                rec.append({'state':name,'period':per,'target':target,'n':len(g),'coverage_all':(mask&pm).sum()/max(1,pm.sum()),'acc':(pred==yy).mean(),'move_target_n':len(g)})
    for s in SCALES:
        tag=str(s).replace('.','p'); add(f'dc_{s}_state',out[f'dc{tag}_mode']!=0,f'dc{tag}_mode')
    add('align_fast',out.align_fast.eq(1),'align_fast_dir')
    add('align3',out.align3.eq(1),'align3_dir')
    add('small_counter_large_follow_small',out.small_counter_large.eq(1),'small_dir')
    add('small_counter_large_follow_large',out.small_counter_large.eq(1),'large_dir')
    add('align3_nonexisting',out.align3.eq(1)&out.existing_module.eq(0),'align3_dir')
    add('align3_existing',out.align3.eq(1)&out.existing_module.eq(1),'align3_dir')
    summ=pd.DataFrame(rec); summ.to_csv('/mnt/data/dc_glass_ceiling_summary.csv',index=False)

    # overshoot bins by scale and periods
    bins=[-np.inf,0.5,1,2,np.inf]; labels=['<0.5','0.5-1','1-2','>=2']
    ores=[]
    for s in SCALES:
        tag=str(s).replace('.','p'); col=f'dc{tag}_extprog'; mode=f'dc{tag}_mode'
        binned=pd.cut(out[col],bins=bins,labels=labels,right=False)
        for lab in labels:
            for per,pm in periods:
                mask=pm & binned.eq(lab) & out.ft25_15.isin([-1,1]) & out[mode].ne(0)
                g=out[mask]
                if len(g): ores.append({'scale':s,'bin':lab,'period':per,'n':len(g),'acc':(g[mode].to_numpy(int)==g.ft25_15.to_numpy(int)).mean(),'mean_extprog':g[col].mean()})
    pd.DataFrame(ores).to_csv('/mnt/data/dc_overshoot_decay.csv',index=False)

    # transition/frequency raw stats
    fre=[]
    for per,pm in periods:
        g=out[pm]
        fre.append({'period':per,'N':len(g),'align_fast_n':int(g.align_fast.sum()),'align_fast_rate':g.align_fast.mean(),'align3_n':int(g.align3.sum()),'align3_rate':g.align3.mean(),'counter_n':int(g.small_counter_large.sum()),'counter_rate':g.small_counter_large.mean(),'existing_module_n':int(g.existing_module.sum()),'existing_module_rate':g.existing_module.mean()})
    pd.DataFrame(fre).to_csv('/mnt/data/dc_frequency.csv',index=False)
    print(summ.to_string(index=False))
    print('\nFREQ\n',pd.DataFrame(fre).to_string(index=False))

if __name__=='__main__': main()
