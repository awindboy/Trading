import pandas as pd, numpy as np
S=pd.read_csv('/mnt/data/v13_ltf_staged_proof.csv',parse_dates=['event_ts','exit_time_fb','proof_add_time'])
# H4 completed bar index map
h=pd.read_csv('/mnt/data/GOLD#_H4_202201030000_202608282000.csv',sep='\t');h['ts']=pd.to_datetime(h['<DATE>']+' '+h['<TIME>'],format='%Y.%m.%d %H:%M:%S');h['end']=h.ts+pd.Timedelta(hours=4);ends=h.end.values.astype('datetime64[ns]')
def hidx(ts):
 if pd.isna(ts):return -1
 return int(np.searchsorted(ends,np.datetime64(ts),side='right')-1)
S['proof_h4_idx']=[hidx(t) for t in S.proof_add_time]
S['exit_h4_idx']=[hidx(t) for t in S.exit_time_fb]
# causal feedback from prior proof trades only; exit_time < current proof time; latest 180 completed H4 indices.
proof=S[S.proof_before_exit].sort_values('proof_add_time').copy()
fb=[];count=[]
for r in proof.itertuples():
 prior=proof[(proof.exit_time_fb<r.proof_add_time)&(proof.exit_h4_idx>=r.proof_h4_idx-179)&(proof.exit_h4_idx<=r.proof_h4_idx)]
 fb.append(prior.proof_add_pnl_atr.mean() if len(prior) else np.nan);count.append(len(prior))
proof['fb180']=fb;proof['fb_n']=count;proof['upgrade_fb']=(proof.fb180>0).astype(int)
S=S.merge(proof[['event_ts','h4_run_id','direction','fb180','fb_n','upgrade_fb']],on=['event_ts','h4_run_id','direction'],how='left');S['upgrade_fb']=S.upgrade_fb.fillna(0).astype(int)
# metrics
def met(x):
 x=x.sort_values(['exit_time_fb','event_ts']);v=x.profit.values;w=v[v>0];l=v[v<0];eq=v.cumsum();pk=np.maximum.accumulate(np.r_[0,eq]);dd=(pk[1:]-eq).max();return len(v),v.sum(),w.sum()/-l.sum(),(v>0).sum()/max(1,(v!=0).sum()),dd
for k in [1,2]:
 S['profit']=S.pnl_usd_1u_fb+k*S.upgrade_fb*S.proof_add_pnl_1u
 print('\nFB k',k,'all',met(S))
 for y,g in S.groupby('year'):
  p=g[g.proof_before_exit];print(y,'all',met(g),'proof',len(p),'up',int(p.upgrade_fb.sum()),'rate',p.upgrade_fb.mean() if len(p) else 0,'fbmean',p.fb180.mean(),'fbnmed',p.fb_n.median())
# Compare proof-add incremental dollar by upgrade status/year
print('\nPROOF split')
for y,g in S[S.proof_before_exit].groupby('year'):
 for u,q in g.groupby('upgrade_fb'):
  v=q.proof_add_pnl_1u.values;w=v[v>0];l=v[v<0];print(y,u,len(q),'net',v.sum(),'PF',w.sum()/-l.sum(),'meanATR',q.proof_add_pnl_atr.mean())
S.to_csv('/mnt/data/v13_ltf_feedback180.csv',index=False)
