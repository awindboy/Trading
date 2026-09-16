import pandas as pd, numpy as np, math, json, os, warnings
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import HistGradientBoostingClassifier
warnings.filterwarnings('ignore')
def cli():
 import argparse
 ap=argparse.ArgumentParser(description='Build causal V10 full-universe features and train/export live ML models.')
 ap.add_argument('--m1',required=True);ap.add_argument('--m15',required=True);ap.add_argument('--m30',required=True);ap.add_argument('--h1',required=True);ap.add_argument('--h4',required=True);ap.add_argument('--out-dir',required=True)
 return ap.parse_args()
ARGS=cli()
files={k:Path(getattr(ARGS,k)) for k in ('m1','m15','m30','h1','h4')}
OUTDIR=Path(ARGS.out_dir);OUTDIR.mkdir(parents=True,exist_ok=True)

def read(p):
 d=pd.read_csv(p,sep='\t')
 d['time']=pd.to_datetime(d['<DATE>']+' '+d['<TIME>'],format='%Y.%m.%d %H:%M:%S')
 return d.rename(columns={'<OPEN>':'o','<HIGH>':'h','<LOW>':'l','<CLOSE>':'c'})[['time','o','h','l','c']]

def ha(df,w,alpha):
 o=df.o.to_numpy(); h=df.h.to_numpy(); l=df.l.to_numpy(); c=df.c.to_numpy(); n=len(df)
 hc=(o+h+l+w*c)/(3+w); ho=np.empty(n); ho[0]=(o[0]+c[0])/2
 for i in range(1,n): ho[i]=alpha*ho[i-1]+(1-alpha)*hc[i-1]
 hh=np.maximum.reduce([h,ho,hc]); ll=np.minimum.reduce([l,ho,hc]); dr=np.where(hc>=ho,1,-1)
 out=df.copy();out['ha_open']=ho;out['ha_close']=hc;out['ha_high']=hh;out['ha_low']=ll;out['ha_dir']=dr;out['ha_body']=hc-ho
 return out

def atr_wilder(df,n=180):
 prev=df.c.shift(); tr=pd.concat([(df.h-df.l),(df.h-prev).abs(),(df.l-prev).abs()],axis=1).max(axis=1)
 arr=tr.to_numpy(); out=np.full(len(arr),np.nan)
 if len(arr)>=n:
  a=np.nanmean(arr[:n]); out[n-1]=a
  for i in range(n,len(arr)): a=(a*(n-1)+arr[i])/n;out[i]=a
 return out

def ema(x,n): return pd.Series(x).ewm(span=n,adjust=False).mean().to_numpy()

def adx_di(df,n):
 h,l,c=df.h.to_numpy(),df.l.to_numpy(),df.c.to_numpy(); N=len(df)
 tr=np.zeros(N); pdm=np.zeros(N); mdm=np.zeros(N)
 tr[0]=h[0]-l[0]
 for i in range(1,N):
  tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])); up=h[i]-h[i-1]; dn=l[i-1]-l[i]
  pdm[i]=up if up>dn and up>0 else 0; mdm[i]=dn if dn>up and dn>0 else 0
 atr=np.full(N,np.nan); sp=np.full(N,np.nan); sm=np.full(N,np.nan)
 if N>n:
  atr[n]=tr[1:n+1].sum();sp[n]=pdm[1:n+1].sum();sm[n]=mdm[1:n+1].sum()
  for i in range(n+1,N):
   atr[i]=atr[i-1]-atr[i-1]/n+tr[i];sp[i]=sp[i-1]-sp[i-1]/n+pdm[i];sm[i]=sm[i-1]-sm[i-1]/n+mdm[i]
 pdi=100*sp/np.where(atr==0,np.nan,atr); mdi=100*sm/np.where(atr==0,np.nan,atr); dx=100*np.abs(pdi-mdi)/np.where((pdi+mdi)==0,np.nan,pdi+mdi)
 adx=np.full(N,np.nan)
 start=2*n
 if N>start:
  adx[start]=np.nanmean(dx[n+1:start+1])
  for i in range(start+1,N): adx[i]=(adx[i-1]*(n-1)+dx[i])/n
 return adx,pdi,mdi

def runmeta(d):
 n=len(d);k=np.zeros(n,int);L=np.zeros(n,int);rid=np.zeros(n,int);s=0;r=0
 while s<n:
  e=s+1
  while e<n and d[e]==d[s]:e+=1
  r+=1; ln=e-s;k[s:e]=np.arange(1,ln+1);L[s:e]=ln;rid[s:e]=r;s=e
 return k,L,rid

def window_feat(seq,pdir,scale):
 if len(seq)==0:return None
 signs=pdir*seq.ha_dir.to_numpy(); trans=np.sum(signs[1:]!=signs[:-1]) if len(signs)>1 else 0
 runs=[];s=0
 for i in range(1,len(signs)+1):
  if i==len(signs) or signs[i]!=signs[s]:runs.append((signs[s],i-s));s=i
 same=[z for sg,z in runs if sg>0];opp=[z for sg,z in runs if sg<0]
 body=pdir*(seq.ha_close-seq.ha_open).to_numpy(); rng=np.maximum((seq.ha_high-seq.ha_low).to_numpy(),1e-9)
 btr=body/rng; eff=body.sum()/max(np.abs(body).sum(),1e-9)
 wick=np.where(pdir>0,np.maximum(0,np.minimum(seq.ha_open.to_numpy(),seq.ha_close.to_numpy())-seq.ha_low.to_numpy()),np.maximum(0,seq.ha_high.to_numpy()-np.maximum(seq.ha_open.to_numpy(),seq.ha_close.to_numpy())))/rng
 last=signs[-1];cur=0
 for z in signs[::-1]:
  if z==last:cur+=1
  else:break
 return {
 'aligned':np.mean(signs>0),'transition':trans/max(1,len(signs)-1),'same_mean':np.mean(same) if same else 0,'opp_mean':np.mean(opp) if opp else 0,
 'same_max':max(same) if same else 0,'opp_max':max(opp) if opp else 0,'len_adv':(max(same) if same else 0)-(max(opp) if opp else 0),
 'streak':cur if last>0 else -cur,'body_sum_atr':body.sum()/max(scale,1e-9),'body_mean_atr':body.mean()/max(scale,1e-9),'body_eff':eff,
 'body_rng':np.mean(btr),'opp_wick':np.mean(wick),'no_opp_wick':np.mean(wick<1e-10)}

print('loading')
m1=read(files['m1']);h4raw=read(files['h4']); h4f=ha(h4raw,2,.25); h4s=ha(h4raw,1,.5); h4slow=ha(h4raw,2,.75)
ltf={'m15':ha(read(files['m15']),2,.25),'m30':ha(read(files['m30']),2,.25),'h1':ha(read(files['h1']),1,.5)}
atr180=atr_wilder(h4raw,180);k,L,rid=runmeta(h4f.ha_dir.to_numpy()); h4f['k']=k;h4f['L']=L;h4f['rid']=rid;h4f['end']=h4f.time+pd.Timedelta(hours=4)
adx14,pdi14,mdi14=adx_di(h4raw,14);adx28,pdi28,mdi28=adx_di(h4raw,28)
ema8=ema(h4raw.c,8);ema21=ema(h4raw.c,21)
# rolling prior medians (shifted) of ADX
adx28med=pd.Series(adx28).rolling(180,min_periods=60).median().shift(1).to_numpy()
# path efficiencies
c=h4raw.c.to_numpy(); pe={}
for w in (4,12):
 a=np.full(len(c),np.nan)
 for i in range(w-1,len(c)):
  den=np.sum(np.abs(np.diff(c[i-w+1:i+1])));a[i]=abs(c[i]-c[i-w+1])/den if den>1e-12 else 0
 pe[w]=a
pe4med=pd.Series(pe[4]).rolling(180,min_periods=60).median().shift(1).to_numpy();pe12med=pd.Series(pe[12]).rolling(180,min_periods=60).median().shift(1).to_numpy()
# flip rates
fd=h4f.ha_dir.to_numpy(); flip={}
for w in (4,8,12):
 a=np.full(len(fd),np.nan)
 for i in range(w-1,len(fd)):a[i]=np.mean(fd[i-w+2:i+1]!=fd[i-w+1:i])
 flip[w]=a
# times for LTF slicing
ltimes={x:d.time.to_numpy(dtype='datetime64[ns]') for x,d in ltf.items()}
# M1 arrays for entry/outcomes
m1t=m1.time.to_numpy(dtype='datetime64[ns]'); m1o=m1.o.to_numpy();m1h=m1.h.to_numpy();m1l=m1.l.to_numpy()
rows=[]
print('building opportunities',len(h4f))
for i in range(181,len(h4f)-1):
 t=h4f.end.iloc[i]; year=t.year
 if year<2022 or year>2026:continue
 pdir=int(h4f.ha_dir.iloc[i]); stop=float(h4s.ha_low.iloc[i-1] if pdir>0 else h4s.ha_high.iloc[i-1])
 # first M1 at or after decision, bounded to 4h to avoid weekend huge delayed fills
 j=np.searchsorted(m1t,np.datetime64(t),'left')
 if j>=len(m1t):continue
 entry_t=pd.Timestamp(m1t[j]);
 if entry_t-t>pd.Timedelta(hours=4):continue
 entry=float(m1o[j])
 if (pdir>0 and stop>=entry) or (pdir<0 and stop<=entry):continue
 # natural exit at end of first opposite FAST bar after i
 e=i+1
 while e<len(h4f) and h4f.ha_dir.iloc[e]==pdir:e+=1
 if e>=len(h4f):continue
 exit_t=h4f.end.iloc[e]; j2=np.searchsorted(m1t,np.datetime64(exit_t),'left')
 if j2>=len(m1t):continue
 # scan stop [entry minute, exit)
 seg_h=m1h[j:j2+1];seg_l=m1l[j:j2+1]
 hit_idx=np.where(seg_l<=stop)[0] if pdir>0 else np.where(seg_h>=stop)[0]
 if len(hit_idx):
  ex=stop; actual_exit_t=pd.Timestamp(m1t[j+hit_idx[0]]);stop_hit=1
 else:
  ex=float(m1o[j2]);actual_exit_t=pd.Timestamp(m1t[j2]);stop_hit=0
 pnl=pdir*(ex-entry); risk=abs(entry-stop); R=pnl/risk
 scale=float(atr180[i-1]) if np.isfinite(atr180[i-1]) else np.nan
 if not np.isfinite(scale) or scale<=0:continue
 rec={'decision':t,'year':year,'dir':pdir,'k':int(k[i]),'L':int(L[i]),'rid':int(rid[i]),'entry':entry,'stop':stop,'stop_dist_atr':risk/scale,'pnl':pnl,'R':R,'stop_hit':stop_hit,
      'early3':int(3*k[i]<=L[i]),'next_same':int(k[i]<L[i]),'win':int(R>0),'severe':int(R<=-.5),'shock':int(k[i]==L[i] and R<=-.5),
      'fast_body_rng':pdir*(h4f.ha_close.iloc[i]-h4f.ha_open.iloc[i])/max(h4f.ha_high.iloc[i]-h4f.ha_low.iloc[i],1e-9),
      'fast_body_atr':pdir*h4f.ha_body.iloc[i]/scale,
      'std_align':int(h4s.ha_dir.iloc[i]==pdir),'std_body_rng':pdir*h4s.ha_body.iloc[i]/max(h4s.ha_high.iloc[i]-h4s.ha_low.iloc[i],1e-9),
      'slow_align':int(h4slow.ha_dir.iloc[i]==pdir),'slow_body_rng':pdir*h4slow.ha_body.iloc[i]/max(h4slow.ha_high.iloc[i]-h4slow.ha_low.iloc[i],1e-9),
      'adx14':adx14[i] if np.isfinite(adx14[i]) else 0,'adx28_rel':adx28[i]/adx28med[i] if np.isfinite(adx28med[i]) and adx28med[i]>0 else 1,
      'di14_signed':pdir*(pdi14[i]-mdi14[i])/100 if np.isfinite(pdi14[i]) else 0,'di28_signed':pdir*(pdi28[i]-mdi28[i])/100 if np.isfinite(pdi28[i]) else 0,
      'ema8_21_signed':pdir*(ema8[i]-ema21[i])/scale,'ema8_slope':pdir*(ema8[i]-ema8[i-1])/scale,
      'path_eff4_rel':pe[4][i]/pe4med[i] if np.isfinite(pe4med[i]) and pe4med[i]>0 else 1,'path_eff12_rel':pe[12][i]/pe12med[i] if np.isfinite(pe12med[i]) and pe12med[i]>0 else 1,
      'flip4':flip[4][i],'flip8':flip[8][i],'flip12':flip[12][i]}
 # LTF window current H4 interval [open,end); all bars completed by end; use opens within interval
 start=h4f.time.iloc[i];end=h4f.end.iloc[i]
 for name,d in ltf.items():
  a=np.searchsorted(ltimes[name],np.datetime64(start),'left');b=np.searchsorted(ltimes[name],np.datetime64(end),'left')
  wf=window_feat(d.iloc[a:b],pdir,scale)
  if wf is None: break
  for z,v in wf.items():rec[f'{name}_{z}']=v
 else:rows.append(rec)
D=pd.DataFrame(rows).sort_values('decision').reset_index(drop=True)
outdir=OUTDIR
D.to_csv(outdir/'V10_LIVE_FULL_UNIVERSE_2022_2026.csv',index=False)
print('rows',len(D),D.year.value_counts().sort_index().to_dict())
print('full causal universe written to',outdir/'V10_LIVE_FULL_UNIVERSE_2022_2026.csv')
