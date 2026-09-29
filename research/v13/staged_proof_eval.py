import pandas as pd, numpy as np
D=pd.read_csv('/mnt/data/v13_ltf_ml_dataset.csv',parse_dates=['event_ts','rebreak_time','flip_time'])
C=pd.read_csv('/mnt/data/v13_ltf_first_breach_clusters.csv',parse_dates=['event_ts','exit_time_fb','flip_time'])
# Aggregate earliest rebreak and market proof refs per cluster
key=['event_ts','h4_run_id','direction']
R=D.groupby(key,as_index=False).agg(rebreak_time=('rebreak_time','min'),rebreak_any=('rebreak','max'),atr=('impulse',lambda x: np.nan))
# own atr already in C; drop bogus
R=R.drop(columns=['atr'])
C=C.merge(R,on=key,how='left',validate='one_to_one')
# load M15 opens
m=pd.read_csv('/mnt/data/GOLD#_M15_202201030100_202608282345.csv',sep='\t')
m['ts']=pd.to_datetime(m['<DATE>']+' '+m['<TIME>'],format='%Y.%m.%d %H:%M:%S'); m=m.sort_values('ts'); mts=m.ts.values.astype('datetime64[ns]'); mo=m['<OPEN>'].astype(float).values
# entry after proof: first M15 bar whose start >= rebreak_time
add=[]
for r in C.itertuples():
  if pd.isna(r.rebreak_time) or pd.Timestamp(r.rebreak_time)>=pd.Timestamp(r.exit_time_fb):
    add.append((np.nan,pd.NaT,0.0,False));continue
  j=np.searchsorted(mts,np.datetime64(r.rebreak_time),side='left')
  if j>=len(m) or pd.Timestamp(m.ts.iloc[j])>=pd.Timestamp(r.exit_time_fb):
    add.append((np.nan,pd.NaT,0.0,False));continue
  px=float(mo[j]); pnl=int(r.direction)*(float(r.exit_px_fb)-px); add.append((px,pd.Timestamp(m.ts.iloc[j]),pnl,True))
C['proof_add_entry']=[x[0] for x in add];C['proof_add_time']=[x[1] for x in add];C['proof_add_pnl_1u']=[x[2] for x in add];C['proof_before_exit']=[x[3] for x in add]
C['proof_latency_h']=(pd.to_datetime(C.proof_add_time)-C.event_ts).dt.total_seconds()/3600
C['proof_add_pnl_atr']=C.proof_add_pnl_1u/C.atr
for y,g in C[C.year>=2024].groupby('year'):
 p=g[g.proof_before_exit];v=p.proof_add_pnl_1u.values;w=v[v>0];l=v[v<0]
 print('PROOF',y,'n',len(p),'rate',len(p)/len(g),'net',v.sum(),'PF',w.sum()/-l.sum(),'WR',(v>0).sum()/max(1,(v!=0).sum()),'avgW',w.mean(),'avgL',l.mean(),'latmed',p.proof_latency_h.median())
# staged total = base one unit + k proof add units
for k in [0,1,2]:
 print('\nK',k)
 allx=[]
 for y,g in C[C.year>=2024].groupby('year'):
  g=g.copy();g['profit']=g.pnl_usd_1u_fb+k*g.proof_add_pnl_1u;v=g.profit.values;w=v[v>0];l=v[v<0]
  z=g.sort_values(['exit_time_fb','event_ts']);eq=z.profit.cumsum().values;pk=np.maximum.accumulate(np.r_[0,eq]);dd=(pk[1:]-eq).max()
  print(y,'n',len(g),'net',v.sum(),'PF',w.sum()/-l.sum(),'WR',(v>0).sum()/max(1,(v!=0).sum()),'DD',dd,'avgW',w.mean(),'avgL',l.mean())
  allx.append(g)
 z=pd.concat(allx).sort_values(['exit_time_fb','event_ts']);v=z.profit.values;w=v[v>0];l=v[v<0];eq=np.cumsum(v);pk=np.maximum.accumulate(np.r_[0,eq]);dd=(pk[1:]-eq).max();print('ALL net',v.sum(),'PF',w.sum()/-l.sum(),'WR',(v>0).sum()/max(1,(v!=0).sum()),'DD',dd)
C.to_csv('/mnt/data/v13_ltf_staged_proof.csv',index=False)
