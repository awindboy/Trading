import pandas as pd,numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
E=pd.read_pickle('/mnt/data/scenario_events.pkl'); A=pd.read_csv('/mnt/data/scenario_cluster_assignments.csv'); A['source_m5']=pd.to_datetime(A.source_m5)
E=E.merge(A[['source_m5','cluster','anchor15']],on='source_m5',suffixes=('','_a'))
# reconstruct compact causal shape features from existing columns
# use earlier source context columns stored in E
anchor=E.anchor15.to_numpy(); S=E.S.to_numpy()
# aligned early: close3 - close12? E has only close1..close7 in scenario_events; need M5 for 12
M1='/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv'; d=pd.read_csv(M1,sep='\t');d.columns=[c.strip('<>').lower() for c in d.columns];d['dt']=pd.to_datetime(d.date+' '+d.time,format='%Y.%m.%d %H:%M:%S');d=d.set_index('dt')
for c in ['open','high','low','close','tickvol']:d[c]=pd.to_numeric(d[c])
m5=d[['open','high','low','close','tickvol']].resample('5min',label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last','tickvol':'sum'}).dropna()
F=[]
for r in E.itertuples():
 i=m5.index.get_loc(r.source_m5); z=m5.iloc[i-12:i+1]; c=z.close.to_numpy();h=z.high.to_numpy();l=z.low.to_numpy();tv=z.tickvol.to_numpy(); a=r.anchor15
 eff=abs(c[-1]-c[0])/(np.abs(np.diff(c)).sum()+1e-9)
 late=a*(c[-1]-c[-4])/r.S; early=a*(c[-4]-c[0])/r.S; rang=(h.max()-l.min())/r.S; tvr=tv[-3:].mean()/(tv[:6].mean()+1e-9); source_body=abs(z.close.iloc[-1]-z.open.iloc[-1])/r.S
 F.append([early,late,rang,tvr,eff,source_body])
F=np.array(F); names=['early45S','late15S','range60S','tick_ratio_late_early','eff60','source_bodyS']
train=(E.year.to_numpy()==2024)&(E.source_m5.to_numpy()<np.datetime64('2024-07-01')); y=(E.cluster.to_numpy()==4).astype(int)
clf=DecisionTreeClassifier(max_depth=3,min_samples_leaf=8,class_weight='balanced',random_state=1).fit(F[train],y[train])
print(export_text(clf,feature_names=names))
pred=clf.predict(F).astype(bool)
# purity to cluster4 and outcome perf
lab=E.first25_15.to_numpy(); direction=E.anchor15.to_numpy();
for pn,pm in [('2024H1',train),('2024H2',(E.year==2024).to_numpy()&(E.source_m5.to_numpy()>=np.datetime64('2024-07-01'))),('2025',(E.year==2025).to_numpy()),('2026',(E.year==2026).to_numpy())]:
 m=pm&pred; res=m&np.isin(lab,[-1,1]); n=m.sum();r=res.sum();acc=np.mean(lab[res]==direction[res]) if r else np.nan; pure=np.mean(E.cluster.to_numpy()[m]==4) if n else np.nan
 print(pn,'N',n,'resolved',r,'follow_acc',round(acc,4),'cluster4_purity',round(pure,3),'coverage',round(n/pm.sum(),3))
# Save features/pred
out=E[['year','source_m5','decision','p15','S','first25_15']].copy();out['anchor15']=direction;out['late_ignition_tree']=pred
for j,n in enumerate(names):out[n]=F[:,j]
out.to_csv('/mnt/data/late_ignition_tree.csv',index=False)
