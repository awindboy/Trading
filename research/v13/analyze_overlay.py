import pandas as pd, numpy as np, re, math
from pathlib import Path

START=pd.Timestamp('2024-01-01')
CUTOFF=pd.Timestamp('2026-08-28 20:00:00')

# ---------- SA1 actual tester ledger ----------
def parse_sa1(path):
    raw=pd.read_excel(path,sheet_name=0,header=None,dtype=object)
    deals=raw.loc[raw[4].isin(['in','out']),list(range(13))].copy()
    deals.columns=['time','deal','symbol','type','direction','volume','price','order','commission','swap','profit','balance','comment']
    deals['time']=pd.to_datetime(deals.time,format='%Y.%m.%d %H:%M:%S')
    for c in ['deal','volume','price','order','commission','swap','profit','balance']:
        deals[c]=pd.to_numeric(deals[c],errors='coerce')
    deals=deals.sort_values(['time','deal']).reset_index(drop=True)
    cre=re.compile(r'^V13SA1\|J(?P<journey>\d{6})\|C(?P<child>\d{2})\|(?P<side>[LS])$')
    opens=[]; completed=[]
    for r in deals.itertuples(index=False):
        if r.direction=='in':
            m=cre.match(str(r.comment).strip()) if pd.notna(r.comment) else None
            if m is None: continue
            side=1 if m.group('side')=='L' else -1
            opens.append(dict(journey=int(m.group('journey')),child=int(m.group('child')),side=side,
                              entry_time=r.time,entry_deal=int(r.deal),entry_price=float(r.price),volume=float(r.volume)))
        else:
            closing_side=1 if r.type=='sell' else -1 if r.type=='buy' else 0
            cand=[]
            for i,p in enumerate(opens):
                if p['side']==closing_side and math.isclose(p['volume'],float(r.volume),abs_tol=1e-12):
                    exp=p['side']*(float(r.price)-p['entry_price'])
                    cand.append((abs(exp-float(r.profit)),p['entry_time'],i,p))
            if not cand: continue
            err,_,i,p=min(cand,key=lambda x:(x[0],x[1],x[2]))
            opens.pop(i)
            completed.append({**p,'exit_time':r.time,'exit_deal':int(r.deal),'exit_price':float(r.price),'profit':float(r.profit)})
    d=pd.DataFrame(completed)
    return d[(d.entry_time>=START)&(d.exit_time<=CUTOFF)].copy()

def max_dd(pnl, times, tie=None):
    df=pd.DataFrame({'time':pd.to_datetime(times),'pnl':np.asarray(pnl,float)})
    if tie is not None: df['tie']=tie
    else: df['tie']=np.arange(len(df))
    df=df.sort_values(['time','tie'])
    eq=df.pnl.cumsum().to_numpy(); peak=np.maximum.accumulate(np.r_[0.,eq])
    return float((peak[1:]-eq).max()) if len(eq) else 0.0

def max_loss_streak(pnl,times,tie=None):
    df=pd.DataFrame({'time':pd.to_datetime(times),'pnl':np.asarray(pnl,float)})
    df['tie']=np.arange(len(df)) if tie is None else tie
    vals=df.sort_values(['time','tie']).pnl.to_numpy()
    cur=best=0
    for x in vals:
        if x<0: cur+=1; best=max(best,cur)
        else: cur=0
    return int(best)

def stats(df,pnl='profit',exit_time='exit_time',tie=None):
    v=df[pnl].astype(float).to_numpy(); w=v[v>0]; l=v[v<0]
    return dict(n=len(v),wins=int((v>0).sum()),losses=int((v<0).sum()),flats=int((v==0).sum()),
                wr=float((v>0).sum()/max(1,(v!=0).sum())),net=float(v.sum()),
                pf=float(w.sum()/-l.sum()) if len(l) and -l.sum()>0 else np.inf,
                avg_win=float(w.mean()) if len(w) else np.nan,avg_loss=float(l.mean()) if len(l) else np.nan,
                payoff=float(w.mean()/-l.mean()) if len(w) and len(l) else np.nan,
                dd=max_dd(v,df[exit_time],df[tie].to_numpy() if tie else None),
                streak=max_loss_streak(v,df[exit_time],df[tie].to_numpy() if tie else None))

sa=parse_sa1('/mnt/data/ReportTester-318585216.xlsx')
print('SA rows',len(sa),stats(sa,tie='exit_deal'))
print('SA yearly')
for y,g in sa.groupby(sa.entry_time.dt.year): print(y,stats(g,tie='exit_deal'))

# ---------- LTF clusters ----------
d=pd.read_csv('/mnt/data/v13_ltf_ml_runner_exit_diag.csv',parse_dates=['event_ts','ltfexit_time','flip_time'])
# infer event ATR and dollar pnl at 0.01 lot (= price move USD under 1 oz)
d['atr']=d['impulse']/d['impulse_atr']
d['pnl_usd_1u']=d['ltfexit_pnl_atr']*d['atr']
# cluster simultaneous same market opportunity. outcome should agree; score=max causal conviction across touched objects.
grp=['event_ts','h4_run_id','direction']
# sanity outcome spread within clusters
chk=d.groupby(grp).agg(pnl_min=('pnl_usd_1u','min'),pnl_max=('pnl_usd_1u','max'),exit_n=('ltfexit_time','nunique'),entry_n=('entry','nunique'))
print('cluster disagreements',((chk.pnl_max-chk.pnl_min).abs()>1e-7).sum(),(chk.exit_n>1).sum(),(chk.entry_n>1).sum())
cluster=d.groupby(grp,as_index=False).agg(
    year=('year','first'),entry=('entry','first'),exit_time=('ltfexit_time','first'),
    pnl_usd_1u=('pnl_usd_1u','first'),tail_score=('tail_score','max'),p_rebreak=('p_rebreak','max'),
    reaction_n=('reaction','nunique'),object_n=('family','size'),env_breach=('env_breach','max'),
    atr=('atr','first'),ltfexit_reason=('ltfexit_reason','first')
)
print('clusters',len(cluster),cluster.year.value_counts().sort_index().to_dict())

# prior OOF cluster score distributions from hurdle OOF 2023-26. Need join event directions? OOF lacks direction in grouping enough event_ts+run.
oof=pd.read_csv('/mnt/data/v13_ltf_hurdle_oof.csv',parse_dates=['event_ts'])
oofc=oof.groupby(['event_ts','h4_run_id'],as_index=False).agg(year=('year','first'),tail_score=('tail_score','max'))

# weights using strictly previous outer-year OOF scores: q50/q75
policies={}
for y in [2024,2025,2026]:
    prior=oofc[oofc.year<y].tail_score.dropna().to_numpy()
    q50,q75=np.quantile(prior,[.5,.75])
    m=cluster.year.eq(y)
    s=cluster.loc[m,'tail_score'].to_numpy()
    policies.setdefault('1u_all',np.ones(len(cluster),int))
    # initialize globally after loop below separately
    print('year q',y,q50,q75,'prior n',len(prior),'score year median',np.median(s))

for name in ['1u_all','1_1_2','1_1_3','1_2_3','q50_1_q75_3','q75_1','q75_2','q75_3']:
    cluster[name]=0
for y in [2024,2025,2026]:
    prior=oofc[oofc.year<y].tail_score.dropna().to_numpy(); q50,q75=np.quantile(prior,[.5,.75]); m=cluster.year.eq(y); s=cluster.loc[m,'tail_score']
    cluster.loc[m,'1u_all']=1
    cluster.loc[m,'1_1_2']=np.where(s>=q75,2,1)
    cluster.loc[m,'1_1_3']=np.where(s>=q75,3,1)
    cluster.loc[m,'1_2_3']=np.where(s>=q75,3,np.where(s>=q50,2,1))
    cluster.loc[m,'q50_1_q75_3']=np.where(s>=q75,3,np.where(s>=q50,1,0))
    cluster.loc[m,'q75_1']=np.where(s>=q75,1,0)
    cluster.loc[m,'q75_2']=np.where(s>=q75,2,0)
    cluster.loc[m,'q75_3']=np.where(s>=q75,3,0)

# LTF standalone metrics
def metrics_policy(name):
    x=cluster[cluster[name]>0].copy(); x['profit']=x.pnl_usd_1u*x[name]; x['tie']=range(len(x));
    return stats(x,tie='tie'), {int(y):stats(g,tie='tie') for y,g in x.groupby('year')}
for p in ['1u_all','1_1_2','1_1_3','1_2_3','q50_1_q75_3','q75_1','q75_2','q75_3']:
    st,yr=metrics_policy(p); print('\nPOL',p,st); print('year',yr)

# combine SA1 base + overlays; treat each exit as realized balance event
def combine(name):
    l=cluster[cluster[name]>0].copy(); l['profit']=l.pnl_usd_1u*l[name]; l['source']='LTF'; l['tie']=np.arange(len(l))+10_000_000
    a=sa[['entry_time','exit_time','profit','exit_deal']].copy(); a['source']='SA1'; a['tie']=a.exit_deal
    # year attribution by entry/event year for reporting separately. combined yearly stats by source row's entry year.
    l['entry_time']=l.event_ts
    both=pd.concat([a[['entry_time','exit_time','profit','source','tie']],l[['entry_time','exit_time','profit','source','tie']]],ignore_index=True)
    return stats(both,tie='tie'), both

for p in ['1u_all','1_1_2','1_1_3','1_2_3','q50_1_q75_3','q75_1','q75_2','q75_3']:
    st,b=combine(p); print('\nCOMB',p,st)
    for y,g in b.groupby(b.entry_time.dt.year): print(' ',y,stats(g,tie='tie'))

# concurrent exposure units for SA1 + overlay policies (position count units; SA1 one unit each)
def max_concurrent(name):
    events=[]
    for r in sa.itertuples():
        events.append((r.entry_time,1,1,'SA1in')); events.append((r.exit_time,0,-1,'SA1out'))
    l=cluster[cluster[name]>0]
    for _,r in l.iterrows():
        u=int(r[name]); events.append((r.event_ts,1,u,'Lin')); events.append((r.exit_time,0,-u,'Lout'))
    # CLOSE before OPEN same timestamp: order key 0 exit,1 entry already encoded kind? use delta negative first
    events=sorted(events,key=lambda x:(x[0],0 if x[2]<0 else 1))
    cur=mx=0; tmx=None
    for t,_,delta,_ in events:
        cur+=delta
        if cur>mx: mx=cur;tmx=t
    return mx,tmx
for p in ['1u_all','1_1_2','1_1_3','1_2_3','q50_1_q75_3','q75_1','q75_2','q75_3']:
    print('CONCUR',p,max_concurrent(p))

cluster.to_csv('/mnt/data/v13_ltf_cluster_overlay_eval.csv',index=False)
