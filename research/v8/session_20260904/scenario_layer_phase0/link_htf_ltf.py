import pandas as pd,numpy as np
E=pd.read_pickle('/mnt/data/scenario_events.pkl'); A=pd.read_csv('/mnt/data/scenario_cluster_assignments.csv');A['source_m5']=pd.to_datetime(A.source_m5);E=E.merge(A[['source_m5','cluster','anchor15']],on='source_m5');P=pd.read_csv('/mnt/data/htf_movement_preds.csv');P['decision']=pd.to_datetime(P.decision)
for tf in ['H1','H4']:
 q=P[P.tf==tf].copy().set_index('decision'); freq='1h' if tf=='H1' else '4h'; key=E.decision.dt.floor(freq); E[f'{tf}_p']=q.p_move.reindex(key).to_numpy();E[f'{tf}_rank']=q.rank_year.reindex(key).to_numpy()
print('Event HTF rank enrichment')
for y in [2024,2025,2026]:
 z=E[E.year==y]
 for tf in ['H1','H4']:
  r=z[f'{tf}_rank'].dropna();print(y,tf,'N',len(r),'meanrank',round(r.mean(),3),'top25%',round((r>=.75).mean(),3),'top10%',round((r>=.9).mean(),3))
# cluster4 rank
print('\ncluster4 vs rest H1')
for y in [2024,2025,2026]:
 z=E[E.year==y]
 for name,m in [('C4',z.cluster==4),('rest',z.cluster!=4)]:
  r=z.loc[m,'H1_rank'].dropna();print(y,name,'N',len(r),'mean',round(r.mean(),3),'top25',round((r>=.75).mean(),3))
# Does high H1 hour contain P0 event in its next hour? P0 decision mapped to same hour
print('\nH1 hour -> P0 occurrence same forecast hour')
for y in [2024,2025,2026]:
 h=P[(P.tf=='H1')&(P.year==y)].copy(); event_hours=set(E.loc[E.year==y,'decision'].dt.floor('1h'))
 h['has_p0']=h.decision.isin(event_hours); 
 for cut in [.5,.75,.9]:
  m=h.rank_year>=cut;print(y,'rank>=',cut,'Nh',m.sum(),'P0hour',round(h.loc[m,'has_p0'].mean(),3),'base',round(h.has_p0.mean(),3),'enrich',round(h.loc[m,'has_p0'].mean()/h.has_p0.mean(),2))
# C4 direction conditional H1 rank, pooled validation and periods
lab=E.first25_15.to_numpy();pred=E.anchor15.to_numpy();c4=E.cluster.to_numpy()==4
print('\nC4 direction by H1 rank')
for y in [2024,2025,2026]:
 for bucket,rm in [('top25',E.H1_rank.to_numpy()>=.75),('lower75',E.H1_rank.to_numpy()<.75)]:
  m=(E.year.to_numpy()==y)&c4&rm&np.isin(lab,[-1,1]);n=m.sum();print(y,bucket,'Nres',n,'acc',round(np.mean(lab[m]==pred[m]),3) if n else None)
E.to_csv('/mnt/data/scenario_events_with_htf.csv',index=False)
