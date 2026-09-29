import pandas as pd, numpy as np, re, math
from collections import defaultdict
START=pd.Timestamp('2024-01-01'); CUTOFF=pd.Timestamp('2026-08-28 20:00')
# Parse SA1
raw=pd.read_excel('/mnt/data/ReportTester-318585216.xlsx',sheet_name=0,header=None,dtype=object)
deals=raw.loc[raw[4].isin(['in','out']),list(range(13))].copy(); deals.columns=['time','deal','symbol','type','direction','volume','price','order','commission','swap','profit','balance','comment'];deals['time']=pd.to_datetime(deals.time,format='%Y.%m.%d %H:%M:%S')
for c in ['deal','volume','price','order','commission','swap','profit','balance']: deals[c]=pd.to_numeric(deals[c],errors='coerce')
cre=re.compile(r'^V13SA1\|J(?P<journey>\d{6})\|C(?P<child>\d{2})\|(?P<side>[LS])$'); opens=[]; comp=[]
for r in deals.sort_values(['time','deal']).itertuples(index=False):
  if r.direction=='in':
    m=cre.match(str(r.comment).strip()) if pd.notna(r.comment) else None
    if m: opens.append({'journey':int(m.group('journey')),'child':int(m.group('child')),'side':1 if m.group('side')=='L' else -1,'entry_time':r.time,'entry_price':float(r.price),'volume':float(r.volume),'entry_deal':int(r.deal)})
  else:
    cs=1 if r.type=='sell' else -1
    cand=[]
    for i,p in enumerate(opens):
      if p['side']==cs and math.isclose(p['volume'],float(r.volume),abs_tol=1e-12): cand.append((abs(p['side']*(float(r.price)-p['entry_price'])-float(r.profit)),p['entry_time'],i,p))
    if cand:
      _,_,i,p=min(cand,key=lambda x:(x[0],x[1],x[2]));opens.pop(i);comp.append({**p,'exit_time':r.time,'exit_price':float(r.price),'profit':float(r.profit),'exit_deal':int(r.deal)})
SA=pd.DataFrame(comp);SA=SA[(SA.entry_time>=START)&(SA.exit_time<=CUTOFF)].copy();SA['year']=SA.entry_time.dt.year
# clusters and predictions
C=pd.read_csv('/mnt/data/v13_ltf_first_breach_clusters.csv',parse_dates=['event_ts','exit_time_fb','flip_time'])
P=pd.read_csv('/mnt/data/v13_ltf_first_breach_ml_oof.csv',parse_dates=['event_ts','exit_time_fb'])
C=C[C.year>=2024].copy(); P=P[P.year>=2024].copy()
# merge HGB score into cluster by exact key
C=C.merge(P[['event_ts','h4_run_id','direction','hgb','pwin','ridge','hurdle_ev']],on=['event_ts','h4_run_id','direction'],how='left',validate='one_to_one')
# weights based on prior OOF distribution (from P full read)
Pall=pd.read_csv('/mnt/data/v13_ltf_first_breach_ml_oof.csv',parse_dates=['event_ts','exit_time_fb'])
for score in ['hgb','pwin','ridge','hurdle_ev']:
  for pol in ['1u','1_1_2','1_1_3']:
    C[f'{score}_{pol}']=1
  for y in [2024,2025,2026]:
    prior=Pall[Pall.year<y][score].dropna().values; q75=np.quantile(prior,.75); m=C.year.eq(y); high=C.loc[m,score]>=q75
    C.loc[m,f'{score}_1_1_2']=np.where(high,2,1); C.loc[m,f'{score}_1_1_3']=np.where(high,3,1)
    C.loc[m,f'{score}_high']=high.astype(int).values
# helper
def metrics(df,profit='profit',etime='exit_time',tie='tie'):
  x=df.sort_values([etime,tie]);v=x[profit].astype(float).values;w=v[v>0];l=v[v<0]; eq=np.cumsum(v); pk=np.maximum.accumulate(np.r_[0,eq]);dd=float((pk[1:]-eq).max()) if len(eq) else 0
  cur=best=0
  for z in v:
    if z<0:cur+=1;best=max(best,cur)
    else:cur=0
  return {'n':len(v),'wins':int((v>0).sum()),'losses':int((v<0).sum()),'flats':int((v==0).sum()),'wr':float((v>0).sum()/max(1,(v!=0).sum())),'net':float(v.sum()),'pf':float(w.sum()/-l.sum()),'avg_win':float(w.mean()),'avg_loss':float(l.mean()),'payoff':float(w.mean()/-l.mean()),'dd':dd,'streak':best}

def overlay(pol):
  o=C.copy();o['units']=o[pol];o['profit']=o.pnl_usd_1u_fb*o.units;o['entry_time']=o.event_ts;o['exit_time']=o.exit_time_fb;o['tie']=np.arange(len(o))+10_000_000;return o

def combined(pol):
  o=overlay(pol);a=SA[['entry_time','exit_time','profit','exit_deal','year']].copy();a['tie']=a.exit_deal;a['src']='SA1';o['src']='LTF';o['year']=o.entry_time.dt.year
  return pd.concat([a[['entry_time','exit_time','profit','tie','src','year']],o[['entry_time','exit_time','profit','tie','src','year']]],ignore_index=True)
# evaluate base and HGB upgrade
print('SA',metrics(SA.assign(tie=SA.exit_deal)))
for pol in ['hgb_1u','hgb_1_1_2','hgb_1_1_3']:
  o=overlay(pol);b=combined(pol)
  print('\nOVER',pol,metrics(o));
  for y,g in o.groupby('year'):print(' year',y,metrics(g))
  print('COMB',metrics(b));
  for y,g in b.groupby('year'):print(' cyear',y,metrics(g))
# concurrency close-before-open
def concurrency(pol):
  ev=[]
  for r in SA.itertuples(): ev.extend([(r.entry_time,1,1,'SA1'),(r.exit_time,0,-1,'SA1')])
  o=overlay(pol)
  for r in o.itertuples(): ev.extend([(r.entry_time,1,int(r.units),'LTF'),(r.exit_time,0,-int(r.units),'LTF')])
  ev.sort(key=lambda z:(z[0],0 if z[2]<0 else 1))
  cur=0;mx=0;tm=None; path=[]
  for t,_,d,s in ev:
    cur+=d;path.append((t,cur));
    if cur>mx:mx=cur;tm=t
  return mx,tm
for pol in ['hgb_1u','hgb_1_1_2','hgb_1_1_3']:
 print('CONCUR',pol,concurrency(pol))
# high bucket diagnostics + permutation same counts by year
rng=np.random.default_rng(13)
for y,g in C.groupby('year'):
 high=g.hgb_high.astype(bool); obs=g.loc[high,'pnl_usd_1u_fb'].sum(); n=high.sum(); vals=g.pnl_usd_1u_fb.values
 draws=np.array([rng.choice(vals,size=n,replace=False).sum() for _ in range(10000)])
 print('HIGH',y,'n',n,'obs_sum',obs,'rest_sum',g.loc[~high,'pnl_usd_1u_fb'].sum(),'obsmean',g.loc[high,'pnl_usd_1u_fb'].mean(),'restmean',g.loc[~high,'pnl_usd_1u_fb'].mean(),'pct_ge',np.mean(draws>=obs),'random_mean',draws.mean(),'95',np.quantile(draws,[.025,.975]).tolist())
# top-run trim overlay base and combined approximate by overlay run contributions; for standalone exact
for pol in ['hgb_1u','hgb_1_1_2','hgb_1_1_3']:
 o=overlay(pol);rg=o.groupby('h4_run_id').profit.sum().sort_values(ascending=False);print('TRIM',pol,'net',o.profit.sum(),{n:o.loc[~o.h4_run_id.isin(rg.head(n).index),'profit'].sum() for n in [1,3,5,10,20]})
# blocks combined
def blocks(df):
 x=df.sort_values(['exit_time','tie']).profit.values;out={}
 for n in [10,25,50,100]:
  ss=[x[i:i+n].sum() for i in range(0,len(x),n) if len(x[i:i+n])==n];out[n]=(len(ss),float(np.mean(np.array(ss)>0)),float(np.median(ss)))
 return out
for pol in ['hgb_1u','hgb_1_1_2','hgb_1_1_3']:
 print('BLOCKS',pol,blocks(combined(pol)))
C.to_csv('/mnt/data/v13_ltf_integrated_eval.csv',index=False)
