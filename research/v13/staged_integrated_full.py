import pandas as pd, numpy as np, re, math
# reuse SA parse from previous integrated script by exec limited? copy lightweight
START=pd.Timestamp('2024-01-01');CUTOFF=pd.Timestamp('2026-08-28 20:00')
raw=pd.read_excel('/mnt/data/ReportTester-318585216.xlsx',sheet_name=0,header=None,dtype=object);deals=raw.loc[raw[4].isin(['in','out']),list(range(13))].copy();deals.columns=['time','deal','symbol','type','direction','volume','price','order','commission','swap','profit','balance','comment'];deals['time']=pd.to_datetime(deals.time,format='%Y.%m.%d %H:%M:%S')
for c in ['deal','volume','price','order','commission','swap','profit','balance']:deals[c]=pd.to_numeric(deals[c],errors='coerce')
cre=re.compile(r'^V13SA1\|J(?P<journey>\d{6})\|C(?P<child>\d{2})\|(?P<side>[LS])$');op=[];co=[]
for r in deals.sort_values(['time','deal']).itertuples(index=False):
 if r.direction=='in':
  m=cre.match(str(r.comment).strip()) if pd.notna(r.comment) else None
  if m:op.append({'journey':int(m.group('journey')),'child':int(m.group('child')),'side':1 if m.group('side')=='L' else -1,'entry_time':r.time,'entry_price':float(r.price),'volume':float(r.volume),'entry_deal':int(r.deal)})
 else:
  cs=1 if r.type=='sell' else -1; cand=[]
  for i,p in enumerate(op):
   if p['side']==cs and abs(p['volume']-float(r.volume))<1e-12:cand.append((abs(p['side']*(float(r.price)-p['entry_price'])-float(r.profit)),p['entry_time'],i,p))
  if cand:
   _,_,i,p=min(cand,key=lambda x:(x[0],x[1],x[2]));op.pop(i);co.append({**p,'exit_time':r.time,'profit':float(r.profit),'exit_deal':int(r.deal)})
SA=pd.DataFrame(co);SA=SA[(SA.entry_time>=START)&(SA.exit_time<=CUTOFF)].copy();SA['year']=SA.entry_time.dt.year
S=pd.read_csv('/mnt/data/v13_ltf_staged_proof.csv',parse_dates=['event_ts','exit_time_fb','proof_add_time']);S=S[(S.year>=2024)&(S.event_ts<=CUTOFF)].copy()

def met(df):
 x=df.sort_values(['exit_time','tie']);v=x.profit.values;w=v[v>0];l=v[v<0];eq=v.cumsum();pk=np.maximum.accumulate(np.r_[0,eq]);dd=(pk[1:]-eq).max() if len(v) else 0;cur=best=0
 for z in v:
  if z<0:cur+=1;best=max(best,cur)
  else:cur=0
 return dict(n=len(v),w=int((v>0).sum()),l=int((v<0).sum()),f=int((v==0).sum()),wr=(v>0).sum()/max(1,(v!=0).sum()),net=v.sum(),pf=w.sum()/-l.sum(),avgW=w.mean(),avgL=l.mean(),payoff=w.mean()/-l.mean(),dd=dd,streak=best)

def opp(k):
 x=S.copy();x['profit']=x.pnl_usd_1u_fb+k*x.proof_add_pnl_1u;x['entry_time']=x.event_ts;x['exit_time']=x.exit_time_fb;x['tie']=np.arange(len(x))+10_000_000;x['run']=x.h4_run_id;return x

def comb(k):
 l=opp(k);a=SA.copy();a['tie']=a.exit_deal;a['src']='SA1';l['src']='LTF';a['run']=-a.journey # separate IDs
 return pd.concat([a[['entry_time','exit_time','profit','tie','src','run']],l[['entry_time','exit_time','profit','tie','src','run']]],ignore_index=True)
for k in [0,1,2]:
 print('\nK',k,'overlay',met(opp(k)),'combined',met(comb(k)))
 for y,g in opp(k).groupby('year'):print(' oy',y,met(g))
 b=comb(k);b['year']=b.entry_time.dt.year
 for y,g in b.groupby('year'):print(' cy',y,met(g))
 # blocks combined
 x=b.sort_values(['exit_time','tie']).profit.values
 print(' blocks',end=' ')
 for n in [10,25,50,100]:
  q=[x[i:i+n].sum() for i in range(0,len(x),n) if len(x[i:i+n])==n];print(n,(np.mean(np.array(q)>0),np.median(q)),end='; ')
 print()
 # overlay top H4 run trim
 l=opp(k);rg=l.groupby('run').profit.sum().sort_values(ascending=False);print(' trim',{n:l.loc[~l.run.isin(rg.head(n).index),'profit'].sum() for n in [1,3,5,10,20]})
# Ticket-level for k=1: base and proof add as separate logical children
base=S[['event_ts','exit_time_fb','pnl_usd_1u_fb','h4_run_id']].copy();base.columns=['entry_time','exit_time','profit','run'];base['tie']=np.arange(len(base))+10_000_000;base['kind']='LTF_BASE'
pa=S[S.proof_before_exit][['proof_add_time','exit_time_fb','proof_add_pnl_1u','h4_run_id']].copy();pa.columns=['entry_time','exit_time','profit','run'];pa['tie']=np.arange(len(pa))+20_000_000;pa['kind']='LTF_PROOF'
a=SA[['entry_time','exit_time','profit','exit_deal','journey']].copy();a['tie']=a.exit_deal;a['run']=-a.journey;a['kind']='SA1';tickets=pd.concat([a[['entry_time','exit_time','profit','tie','run','kind']],base,pa],ignore_index=True);print('\nTICKET K1 all',met(tickets));print(tickets.groupby('kind').apply(lambda g:pd.Series(met(g)),include_groups=False))
# concurrency for k=0,1,2, treating proof add k units
for k in [0,1,2]:
 ev=[]
 for r in SA.itertuples():ev += [(r.entry_time,1),(r.exit_time,-1)]
 for r in S.itertuples():
  ev += [(r.event_ts,1),(r.exit_time_fb,-1)]
  if k and r.proof_before_exit:ev += [(r.proof_add_time,k),(r.exit_time_fb,-k)]
 ev.sort(key=lambda z:(z[0],0 if z[1]<0 else 1));cur=mx=0;tm=None
 for t,d in ev:
  cur+=d
  if cur>mx:mx=cur;tm=t
 print('CONCUR K',k,mx,tm)
# preperiod 2022-23 standalone staged stress
ALL=pd.read_csv('/mnt/data/v13_ltf_staged_proof.csv',parse_dates=['event_ts','exit_time_fb','proof_add_time'])
for k in [0,1,2]:
 print('PRE K',k)
 for y,g in ALL[ALL.year.isin([2022,2023])].groupby('year'):
  x=g.copy();x['profit']=x.pnl_usd_1u_fb+k*x.proof_add_pnl_1u;x['entry_time']=x.event_ts;x['exit_time']=x.exit_time_fb;x['tie']=range(len(x));print(y,met(x))
