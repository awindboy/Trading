import pandas as pd,numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
E=pd.read_csv('/mnt/data/scenario_events_with_htf.csv');E['source_m5']=pd.to_datetime(E.source_m5)
D=pd.read_pickle('/mnt/data/slow_m1.pkl');M5=D[['o','h','l','c','tv']].resample('5min',label='left',closed='left').agg(o=('o','first'),h=('h','max'),l=('l','min'),c=('c','last'),tv=('tv','sum')).dropna()
hi12=M5.h.shift(1).rolling(12).max();lo12=M5.l.shift(1).rolling(12).min();sma=M5.c.rolling(20).mean();sd=M5.c.rolling(20).std(ddof=0);up=sma+2*sd;dn=sma-2*sd
F=[];anc=[];valid=[]
for r in E.itertuples():
 try:i=M5.index.get_loc(r.source_m5)
 except: F.append([np.nan]*24);anc.append(0);valid.append(False);continue
 if i<12:F.append([np.nan]*24);anc.append(0);valid.append(False);continue
 z=M5.iloc[i-12:i+1];c=z.c.to_numpy();h=z.h.to_numpy();l=z.l.to_numpy();tv=z.tv.to_numpy();a=np.sign(c[-1]-c[-4]);
 if a==0:a=np.sign(c[-1]-z.o.iloc[-1]);
 if a==0:a=1
 path=a*(c-c[0])/r.S
 eff=abs(c[-1]-c[0])/(np.abs(np.diff(c)).sum()+1e-9);late=a*(c[-1]-c[-4])/r.S;early=a*(c[-4]-c[0])/r.S;rang=(h.max()-l.min())/r.S;tvr=tv[-3:].mean()/(tv[:6].mean()+1e-9)
 bd=1 if c[-1]>hi12.iloc[i] else (-1 if c[-1]<lo12.iloc[i] else 0); bb=1 if c[-1]>up.iloc[i] else(-1 if c[-1]<dn.iloc[i] else 0)
 # aligned categorical context: +1 same as anchor, -1 opposite, 0 none
 bdal=bd*a; bbal=bb*a
 hour=r.source_m5.hour+r.source_m5.minute/60;st=np.sin(2*np.pi*hour/24);ct=np.cos(2*np.pi*hour/24)
 vals=list(path)+[eff,late,early,rang,np.log1p(tvr),bdal,bbal,r.H1_rank if np.isfinite(r.H1_rank) else .5,r.H4_rank if np.isfinite(r.H4_rank) else .5,st,ct]
 F.append(vals);anc.append(int(a));valid.append(np.all(np.isfinite(vals)))
F=np.array(F);anc=np.array(anc);ok=np.array(valid);lab=E.first25_15.to_numpy();
train=ok&(E.year.to_numpy()==2024)&(E.source_m5.to_numpy()<np.datetime64('2024-07-01'))
sc=StandardScaler();km=KMeans(n_clusters=8,n_init=50,random_state=20260904).fit(sc.fit_transform(F[train]));cl=np.full(len(E),-1);cl[ok]=km.predict(sc.transform(F[ok]));
print('train cluster counts',pd.Series(cl[train]).value_counts().sort_index().to_dict())
rules={}
for k in range(8):
 m=train&(cl==k)&np.isin(lab,[-1,1]);n=m.sum();acc=np.mean(lab[m]==anc[m]) if n else np.nan;act='FOLLOW' if n>=20 and acc>=.55 else ('FADE' if n>=20 and acc<=.45 else 'NONE');rules[k]=(act,n,acc);print('C',k,'Nres',n,'followacc',round(acc,3) if n else None,'action',act)
periods={'2024H1':train,'2024H2':ok&(E.year.to_numpy()==2024)&(E.source_m5.to_numpy()>=np.datetime64('2024-07-01')),'2025':ok&(E.year.to_numpy()==2025),'2026':ok&(E.year.to_numpy()==2026)}
rows=[]
for k,(act,_,_) in rules.items():
 if act=='NONE':continue
 pred=anc if act=='FOLLOW' else -anc
 for pn,pm in periods.items():
  m=pm&(cl==k);res=m&np.isin(lab,[-1,1]);N=m.sum();R=res.sum();w=np.sum(lab[res]==pred[res]);l=np.sum(lab[res]==-pred[res]);rows.append((k,act,pn,N,R,w/R if R else np.nan,(w-l)/N if N else np.nan))
R=pd.DataFrame(rows,columns=['cluster','action','period','N','resolved','acc','edge']);print(R.to_string(index=False));R.to_csv('/mnt/data/context_cluster_results.csv',index=False)
# centroids raw summaries for selected clusters
for k,(act,_,_) in rules.items():
 if act=='NONE':continue
 m=train&(cl==k);q=F[m].mean(axis=0);print('DESC',k,act,'N',m.sum(),'finalpath',round(q[12],3),'eff',round(q[13],3),'late',round(q[14],3),'early',round(q[15],3),'range',round(q[16],3),'tvr_log',round(q[17],3),'bdal',round(q[18],3),'bbal',round(q[19],3),'H1rank',round(q[20],3),'H4rank',round(q[21],3))
E['ctx_cluster']=cl;E['anchor_ctx']=anc;E.to_csv('/mnt/data/context_cluster_assignments.csv',index=False)
