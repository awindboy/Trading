import pandas as pd, numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
E=pd.read_pickle('/mnt/data/scenario_events.pkl')
M1='/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv'
d=pd.read_csv(M1,sep='\t'); d.columns=[c.strip('<>').lower() for c in d.columns]; d['dt']=pd.to_datetime(d.date+' '+d.time,format='%Y.%m.%d %H:%M:%S'); d=d.set_index('dt')
for c in ['open','high','low','close','tickvol']: d[c]=pd.to_numeric(d[c])
m5=d[['open','high','low','close','tickvol']].resample('5min',label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last','tickvol':'sum'}).dropna()
# feature: 60m pre-path aligned to last-15m direction. all info <= source close.
rows=[]; valid=[]; anchors=[]
for j,r in E.iterrows():
 try: i=m5.index.get_loc(r.source_m5)
 except KeyError: valid.append(False); rows.append([np.nan]*18); anchors.append(0); continue
 if i<12: valid.append(False); rows.append([np.nan]*18); anchors.append(0); continue
 z=m5.iloc[i-12:i+1]
 c=z.close.to_numpy(); h=z.high.to_numpy(); l=z.low.to_numpy(); tv=z.tickvol.to_numpy()
 anchor=np.sign(c[-1]-c[-4]);
 if anchor==0: anchor=np.sign(c[-1]-z.open.iloc[-1])
 if anchor==0: anchor=1
 # aligned close trajectory from 60m ago, S-normalized (13 pts)
 path=anchor*(c-c[0])/r.S
 # shape summaries, all causal
 eff=abs(c[-1]-c[0])/(np.abs(np.diff(c)).sum()+1e-9)
 late=anchor*(c[-1]-c[-4])/r.S
 early=anchor*(c[-4]-c[0])/r.S
 rang=(h.max()-l.min())/r.S
 tvr=tv[-3:].mean()/(tv[:6].mean()+1e-9)
 rows.append(list(path)+[eff,late,early,rang,tvr]); valid.append(True); anchors.append(int(anchor))
X=np.array(rows,float); E['anchor15']=anchors; ok=np.array(valid)&np.all(np.isfinite(X),axis=1)
train=ok&(E.year.to_numpy()==2024)&(E.source_m5.to_numpy()<np.datetime64('2024-07-01'))
sc=StandardScaler(); Xt=sc.fit_transform(X[train]); km=KMeans(n_clusters=6,random_state=20260904,n_init=50).fit(Xt)
cl=np.full(len(E),-1); cl[ok]=km.predict(sc.transform(X[ok])); E['cluster']=cl
# describe clusters in raw feature mean
names=[]
print('cluster train counts',pd.Series(cl[train]).value_counts().sort_index().to_dict())
for k in range(6):
 z=X[train&(cl==k)]; mp=z.mean(axis=0); print('C',k,'N',len(z),'start->15m_before',round(mp[12-3],3),'final',round(mp[12],3),'eff',round(mp[13],3),'late',round(mp[14],3),'early',round(mp[15],3),'rangeS',round(mp[16],3),'tvRatio',round(mp[17],3))
# discovery action H1 based on resolved direction accuracy; fixed rule >=.55 follow <=.45 fade else none
rules={}; lab=E.first25_15.to_numpy(); anc=E.anchor15.to_numpy()
for k in range(6):
 m=train&(cl==k)&np.isin(lab,[-1,1]); n=m.sum(); acc=np.mean(lab[m]==anc[m]) if n else np.nan
 action='FOLLOW' if n>=20 and acc>=.55 else ('FADE' if n>=20 and acc<=.45 else 'NONE')
 rules[k]=(action,n,acc)
 print('rule C',k,'Nresolved',n,'follow_acc',round(acc,3) if n else None,'action',action)
# validation table
out=[]
periods={'2024H1':train,'2024H2':ok&(E.year.to_numpy()==2024)&(E.source_m5.to_numpy()>=np.datetime64('2024-07-01')),'2025':ok&(E.year.to_numpy()==2025),'2026':ok&(E.year.to_numpy()==2026)}
for k,(action,_,_) in rules.items():
 if action=='NONE': continue
 pred=anc if action=='FOLLOW' else -anc
 for pn,pm in periods.items():
  m=pm&(cl==k); res=m&np.isin(lab,[-1,1]); N=m.sum(); R=res.sum(); win=np.sum(lab[res]==pred[res]); loss=np.sum(lab[res]==-pred[res])
  out.append(dict(cluster=k,action=action,period=pn,N=N,resolved=R,dir_acc=win/R if R else np.nan,edge=(win-loss)/N if N else np.nan))
# combined selected policy: only action clusters
selected=np.array([rules.get(k,('NONE',0,0))[0]!='NONE' for k in cl])
pred=np.zeros(len(E),int)
for k,(action,_,_) in rules.items():
 if action=='FOLLOW': pred[cl==k]=anc[cl==k]
 elif action=='FADE': pred[cl==k]=-anc[cl==k]
for pn,pm in periods.items():
 m=pm&(pred!=0); res=m&np.isin(lab,[-1,1]); N=m.sum();R=res.sum();win=np.sum(lab[res]==pred[res]);loss=np.sum(lab[res]==-pred[res])
 out.append(dict(cluster='COMBINED',action='DISCOVERY_RULE',period=pn,N=N,resolved=R,dir_acc=win/R if R else np.nan,edge=(win-loss)/N if N else np.nan))
R=pd.DataFrame(out); R.to_csv('/mnt/data/scenario_cluster_results.csv',index=False); E[['year','source_m5','decision','p15','S','first25_15','anchor15','cluster']].to_csv('/mnt/data/scenario_cluster_assignments.csv',index=False)
print('\n',R.to_string(index=False))
