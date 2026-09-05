import pandas as pd, numpy as np, pickle
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
m5=pd.read_pickle('/mnt/data/slow_m5.pkl'); X=np.load('/mnt/data/slow_feats.npy'); mi=np.arange(len(m5))
valid_feat=np.all(np.isfinite(X),axis=1)&np.isfinite(m5['T'].to_numpy())
valid_train=valid_feat & m5.eligible60.to_numpy() & (m5['class'].to_numpy()>=0)
yall=m5['class'].to_numpy()
rows=[]
for year in [2024,2025,2026]:
    tr=valid_train & (m5.decision.to_numpy()<np.datetime64(f'{year}-01-01')) & ((mi%5)==0)
    sc=StandardScaler(); xt=sc.fit_transform(X[tr]); y=yall[tr]
    lr=LogisticRegression(C=0.4,solver='newton-cholesky',max_iter=100).fit(xt,y)
    ym=(m5.decision.dt.year.to_numpy()==year)
    scoremask=valid_feat & ym
    p=np.full(len(m5),np.nan); inds=np.where(scoremask)[0]; p[inds]=lr.predict_proba(sc.transform(X[inds]))[:,0]
    prev=np.r_[np.nan,p[:-1]]
    fresh=valid_train & ym & (p>=.75) & (prev<.75)
    ids=np.where(fresh)[0]
    print(year,'train',tr.sum(),'fresh',len(ids),'hit',np.mean(yall[ids]==0),'meanp',np.nanmean(p[ids]))
    for i in ids:
        rows.append(dict(year=year,source_m5=m5.index[i],decision=m5.decision.iloc[i],p15=p[i],S=m5['T'].iloc[i]/.25,origin_close=m5.c.iloc[i],cls=int(yall[i])))
out=pd.DataFrame(rows); out.to_csv('/mnt/data/oldp0_events_all.csv',index=False)
print(out.groupby('year').size())
