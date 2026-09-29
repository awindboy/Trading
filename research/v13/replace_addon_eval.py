import pandas as pd, numpy as np, re, math
# parse SA1 quickly from saved integrated? redo
raw=pd.read_excel('/mnt/data/ReportTester-318585216.xlsx',sheet_name=0,header=None,dtype=object);deals=raw.loc[raw[4].isin(['in','out']),list(range(13))].copy();deals.columns=['time','deal','symbol','type','direction','volume','price','order','commission','swap','profit','balance','comment'];deals['time']=pd.to_datetime(deals.time,format='%Y.%m.%d %H:%M:%S')
for c in ['deal','volume','price','order','commission','swap','profit','balance']:deals[c]=pd.to_numeric(deals[c],errors='coerce')
cre=re.compile(r'^V13SA1\|J(?P<journey>\d{6})\|C(?P<child>\d{2})\|(?P<side>[LS])$');op=[];co=[]
for r in deals.sort_values(['time','deal']).itertuples(index=False):
 if r.direction=='in':
  m=cre.match(str(r.comment).strip()) if pd.notna(r.comment) else None
  if m:op.append({'journey':int(m.group('journey')),'child':int(m.group('child')),'side':1 if m.group('side')=='L' else -1,'entry_time':r.time,'entry_price':float(r.price),'volume':float(r.volume),'entry_deal':int(r.deal)})
 else:
  cs=1 if r.type=='sell' else -1;c=[]
  for i,p in enumerate(op):
   if p['side']==cs and abs(p['volume']-float(r.volume))<1e-12:c.append((abs(p['side']*(float(r.price)-p['entry_price'])-float(r.profit)),p['entry_time'],i,p))
  if c:
   _,_,i,p=min(c,key=lambda x:(x[0],x[1],x[2]));op.pop(i);co.append({**p,'exit_time':r.time,'profit':float(r.profit),'exit_deal':int(r.deal)})
SA=pd.DataFrame(co);SA=SA[(SA.entry_time>=pd.Timestamp('2024-01-01'))&(SA.exit_time<=pd.Timestamp('2026-08-28 20:00'))].copy();C1=SA[SA.child==1].copy();ADD=SA[SA.child>=2].copy()
S=pd.read_csv('/mnt/data/v13_ltf_staged_proof.csv',parse_dates=['event_ts','exit_time_fb','proof_add_time']);S=S[S.year>=2024].copy()
def met(df):
 x=df.sort_values(['exit_time','tie']);v=x.profit.values;w=v[v>0];l=v[v<0];eq=v.cumsum();pk=np.maximum.accumulate(np.r_[0,eq]);dd=(pk[1:]-eq).max();cur=best=0
 for z in v:
  if z<0:cur+=1;best=max(best,cur)
  else:cur=0
 return {'n':len(v),'w':int((v>0).sum()),'l':int((v<0).sum()),'wr':(v>0).sum()/max(1,(v!=0).sum()),'net':v.sum(),'pf':w.sum()/-l.sum(),'avgW':w.mean(),'avgL':l.mean(),'payoff':w.mean()/-l.mean(),'dd':dd,'streak':best}
def build(k):
 a=C1[['entry_time','exit_time','profit','exit_deal']].copy();a['tie']=a.exit_deal;a['src']='C1'
 l=S.copy();l['profit']=l.pnl_usd_1u_fb+k*l.proof_add_pnl_1u;l['entry_time']=l.event_ts;l['exit_time']=l.exit_time_fb;l['tie']=np.arange(len(l))+10_000_000;l['src']='LTF'
 return pd.concat([a[['entry_time','exit_time','profit','tie','src']],l[['entry_time','exit_time','profit','tie','src']]],ignore_index=True)
print('C1',met(C1.assign(tie=C1.exit_deal)),'ADD',met(ADD.assign(tie=ADD.exit_deal)))
for k in [0,1,2]:
 b=build(k);print('\nREPL K',k,met(b));b['year']=b.entry_time.dt.year
 for y,g in b.groupby('year'):print(y,met(g))
 x=b.sort_values(['exit_time','tie']).profit.values
 print('blocks', {n:(np.mean(np.array([x[i:i+n].sum() for i in range(0,len(x),n) if len(x[i:i+n])==n])>0),np.median([x[i:i+n].sum() for i in range(0,len(x),n) if len(x[i:i+n])==n])) for n in [10,25,50,100]})
 # concurrency C1 + base + proof units
 ev=[]
 for r in C1.itertuples():ev += [(r.entry_time,1),(r.exit_time,-1)]
 for r in S.itertuples():
  ev += [(r.event_ts,1),(r.exit_time_fb,-1)]
  if k and r.proof_before_exit:ev += [(r.proof_add_time,k),(r.exit_time_fb,-k)]
 ev.sort(key=lambda z:(z[0],0 if z[1]<0 else 1));cur=mx=0;tm=None
 for t,d in ev:
  cur+=d
  if cur>mx:mx=cur;tm=t
 print('concur',mx,tm)
