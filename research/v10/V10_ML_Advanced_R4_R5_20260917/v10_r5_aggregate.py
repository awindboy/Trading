from pathlib import Path
import pandas as pd, numpy as np, glob, json
from scipy.stats import spearmanr
P=Path('/mnt/data/v10_ml_advanced_r5')
o=pd.concat([pd.read_csv(f,parse_dates=['decision']) for f in glob.glob(str(P/'MIX_OOS_*.csv'))],ignore_index=True);o['neg_pstop']=-o.p_stop;o.to_csv(P/'MIX_OOS_ALL.csv',index=False)
def sp(y,p):return float(spearmanr(y,p).statistic)
choices=[]
for st in ['k1','k2','k3p']:
 for d in ['LONG','SHORT']:
  z=o[(o.stage==st)&(o.direction==d)&(o.year==2024)];A=[]
  for c in ['EV','mu_nonstop','neg_pstop']:
   r=sp(z.R,z[c]);q=np.quantile(z[c],.75);lift=z.loc[z[c]>=q,'R'].mean()-z.R.mean();A.append((r,lift,c))
  A.sort(key=lambda x:(-x[0],-x[1]));choices.append([st,d,A[0][2],A[0][0],A[0][1],';'.join(f'{c}:{r:.3f}/{l:.3f}' for r,l,c in A)])
ch=pd.DataFrame(choices,columns=['stage','direction','source','spearman2024','lift2024','all']);ch.to_csv(P/'MIX_SCORE_SOURCE.csv',index=False);cm={(r.stage,r.direction):r.source for _,r in ch.iterrows()}
rows=[]
for yr in [2025,2026]:
 for st in ['k1','k2','k3p']:
  for d in ['LONG','SHORT']:
   src=cm[(st,d)];pr=o[(o.year==yr-1)&(o.stage==st)&(o.direction==d)];cu=o[(o.year==yr)&(o.stage==st)&(o.direction==d)];q50,q75=np.quantile(pr[src],[.5,.75])
   for _,r in cu.iterrows():
    w=0 if r[src]<q50 else (1 if r[src]<q75 else 3);x=r.to_dict();x.update(source=src,score=r[src],q50_prior=q50,q75_prior=q75,w=w);rows.append(x)
pol=pd.DataFrame(rows).sort_values('decision');pol.to_csv(P/'MIX_POLICY_LEDGER.csv',index=False)
def met(z):
 z=z[z.w>0].copy();wp=z.pnl*z.w;wr=z.R*z.w;gp=wp[wp>0].sum();gl=-wp[wp<0].sum();cum=wr.cumsum();return dict(events=len(z),units=z.w.sum(),pnl=wp.sum(),R=wr.sum(),pf=gp/gl if gl else np.inf,wr=(wp>0).mean(),ddR=(cum.cummax()-cum).max())
S=[]
for n,z in [('ALL',pol),('2025',pol[pol.year==2025]),('2026',pol[pol.year==2026]),('LONG',pol[pol.direction=='LONG']),('SHORT',pol[pol.direction=='SHORT']),('k1',pol[pol.stage=='k1']),('k2',pol[pol.stage=='k2']),('k3p',pol[pol.stage=='k3p'])]:S.append({'scope':n,**met(z)})
su=pd.DataFrame(S);su.to_csv(P/'MIX_POLICY_SUMMARY.csv',index=False)
# OOS metrics each source
m=[]
for st in ['k1','k2','k3p']:
 for d in ['LONG','SHORT']:
  for yr in [2025,2026]:
   z=o[(o.stage==st)&(o.direction==d)&(o.year==yr)]
   for c in ['EV','mu_nonstop','neg_pstop']:m.append([st,d,yr,c,sp(z.R,z[c])])
pd.DataFrame(m,columns=['stage','direction','year','source','spearman']).to_csv(P/'MIX_OOS_METRICS.csv',index=False)
# run buckets/right tail
se=pol[pol.w>0].copy();se['wp']=se.pnl*se.w;se['wR']=se.R*se.w;se['bucket']=pd.cut(se.L,[0,2,5,8,11,999],labels=['L1-2','L3-5','L6-8','L9-11','L12+']);rb=pd.DataFrame([{'bucket':str(b),**met(g)} for b,g in se.groupby('bucket',observed=True)]);rb.to_csv(P/'MIX_RUN_BUCKETS.csv',index=False);runs=se.groupby(['year','rid'],as_index=False).agg(pnl=('wp','sum'));pos=runs[runs.pnl>0].sort_values('pnl',ascending=False);tot=se.wp.sum();rt=pd.DataFrame([{'top_n':n,'pnl':pos.head(n).pnl.sum(),'share':pos.head(n).pnl.sum()/tot} for n in [1,5,10]]);rt.to_csv(P/'MIX_RIGHT_TAIL.csv',index=False)
print('CHOICES\n',ch.to_string(index=False));print('\nSUMMARY\n',su.to_string(index=False));print('\nRUN\n',rb.to_string(index=False));print('\nRIGHT\n',rt.to_string(index=False))
