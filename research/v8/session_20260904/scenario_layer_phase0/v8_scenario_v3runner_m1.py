import pandas as pd,numpy as np
D=pd.read_pickle('/mnt/data/slow_m1.pkl');idx=D.index.to_numpy(dtype='datetime64[ns]');H=D.h.to_numpy();L=D.l.to_numpy();C=D.c.to_numpy()
mods=[]
# endogenous late ignition, exclude 15:30 server slot
cl=pd.read_csv('/mnt/data/scenario_cluster_assignments.csv',parse_dates=['source_m5','decision']);cl=cl[(cl.cluster==4)&~((cl.source_m5.dt.hour==15)&(cl.source_m5.dt.minute==30))].copy();
mods.append(pd.DataFrame({'module':'LATE_IGNITION_ENDO','year':cl.year,'source':cl.source_m5,'decision':cl.decision,'S':cl.S,'dir':cl.anchor15}))
# BB persistence + HTF owner alignment
bb=pd.read_csv('/mnt/data/delayed_scenario_v3state.csv',parse_dates=['source','confirm']);bb=bb[(bb.scenario=='D3_BB_PERSIST')&bb.owners_align_pred].copy();mods.append(pd.DataFrame({'module':'BB_PERSIST_HTF','year':bb.year,'source':bb.source,'decision':bb.confirm,'S':bb.S,'dir':bb.pred}))
# major scheduled macro 2024
ma=pd.read_csv('/mnt/data/major_macro_p0_2024_events.csv',parse_dates=['source_m5','decision']);mods.append(pd.DataFrame({'module':'MACRO_MAJOR_2024','year':2024,'source':ma.source_m5,'decision':ma.decision,'S':ma.S,'dir':ma.anchor15}))
E=pd.concat(mods,ignore_index=True)

def replay(r):
 t=pd.Timestamp(r.decision); p=np.searchsorted(idx,np.datetime64(t),'left'); en=C[p-1];R=.25*r.S
 init_end=np.searchsorted(idx,np.datetime64(t+pd.Timedelta(minutes=15)),'left')
 hit=None;hi_i=None
 for i in range(p,min(init_end,len(idx))):
  if r.dir==1: win=H[i]>=en+R; loss=L[i]<=en-R
  else: win=L[i]<=en-R; loss=H[i]>=en+R
  if win and loss: hit='SL';hi_i=i;break
  if loss:hit='SL';hi_i=i;break
  if win:hit='CP';hi_i=i;break
 if hit=='SL': return dict(outcome='SL',pnlR=-1.0,cp=0,runner2=0,dur_min=(pd.Timestamp(idx[hi_i])-t).total_seconds()/60)
 if hit is None:
  # close at 15m last completed minute
  j=max(p,min(init_end,len(idx))-1); rr=r.dir*(C[j]-en)/R
  return dict(outcome='TIMEOUT15',pnlR=rr,cp=0,runner2=0,dur_min=15.0)
 # checkpoint: 50% realized at +1R, residual BE / +2R, total horizon 60m from entry
 run_end=np.searchsorted(idx,np.datetime64(t+pd.Timedelta(minutes=60)),'left')
 # same bar after CP is ambiguous for residual BE vs runner; pessimistic: if same bar contains BE after CP we BE. OHLC cannot order, so start next M1; CP itself locked +0.5R
 for i in range(hi_i+1,min(run_end,len(idx))):
  if r.dir==1: tp=H[i]>=en+2*R; be=L[i]<=en
  else: tp=L[i]<=en-2*R; be=H[i]>=en
  if tp and be: return dict(outcome='CP_BE_AMBIG',pnlR=.5,cp=1,runner2=0,dur_min=(pd.Timestamp(idx[i])-t).total_seconds()/60)
  if be:return dict(outcome='CP_BE',pnlR=.5,cp=1,runner2=0,dur_min=(pd.Timestamp(idx[i])-t).total_seconds()/60)
  if tp:return dict(outcome='RUNNER2',pnlR=1.5,cp=1,runner2=1,dur_min=(pd.Timestamp(idx[i])-t).total_seconds()/60)
 j=max(hi_i,min(run_end,len(idx))-1); residual=r.dir*(C[j]-en)/R; residual=max(0,min(2,residual));return dict(outcome='RUN_TIMEOUT60',pnlR=.5+.5*residual,cp=1,runner2=0,dur_min=60.0)
R=[]
for r in E.itertuples(index=False):R.append({**r._asdict(),**replay(r)})
out=pd.DataFrame(R);out.to_csv('/mnt/data/v8_scenario_v3runner_m1.csv',index=False)
for mod,g0 in out.groupby('module'):
 print('\nMOD',mod)
 for y,g in g0.groupby('year'):
  pos=g[g.pnlR>0];neg=g[g.pnlR<0]
  print(y,'N',len(g),'meanR',round(g.pnlR.mean(),3),'WR+',round((g.pnlR>0).mean(),3),'avg+',round(pos.pnlR.mean(),3) if len(pos) else None,'PF',round(pos.pnlR.sum()/(-neg.pnlR.sum()),3) if len(neg) else None,'CP',g.cp.sum(),'R2',g.runner2.sum(),'R2|CP',round(g.runner2.sum()/g.cp.sum(),3) if g.cp.sum() else None)
# union frequency by source event; priority macro > BB > late
print('\nUNION SOURCE COUNTS (available modules)')
for y,g in out.groupby('year'):
 print(y,'rows',len(g),'unique_source',g.source.nunique())
 print(pd.crosstab(g.source,g.module).astype(bool).sum().to_dict())
