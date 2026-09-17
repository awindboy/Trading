from pathlib import Path
from bisect import bisect_left,bisect_right,insort
import numpy as np,pandas as pd
OUT=Path('/mnt/data/v10_ml_advanced_r4');OUT.mkdir(exist_ok=True)
df=pd.read_csv('/mnt/data/v10_ml_live/V10_LIVE_FULL_UNIVERSE_2022_2026.csv');df.decision=pd.to_datetime(df.decision);df['direction']=np.where(df.dir>0,'LONG','SHORT');df['stage']=np.where(df.k==1,'k1',np.where(df.k==2,'k2','k3p'));df=df.sort_values('decision').reset_index(drop=True);df['idx']=np.arange(len(df))
raw=['stop_dist_atr','fast_body_rng','fast_body_atr','std_align','std_body_rng','slow_align','slow_body_rng','adx28_rel','di14_signed','di28_signed','ema8_21_signed','ema8_slope','path_eff4_rel','path_eff12_rel','flip4','flip8','flip12','m15_aligned','m15_transition','m15_streak','m15_body_sum_atr','m15_body_eff','m15_body_rng','m15_opp_wick','m30_aligned','m30_transition','m30_streak','m30_body_sum_atr','m30_body_eff','m30_body_rng','m30_opp_wick','h1_aligned','h1_transition','h1_streak','h1_body_sum_atr','h1_body_eff','h1_body_rng','h1_opp_wick']
E=pd.DataFrame(index=df.index);E['log_stop']=np.log1p(df.stop_dist_atr.clip(lower=0));E['fast_body']=df.fast_body_rng;E['ha_align']=(df.std_align+df.slow_align)/2;E['ha_disagree']=(df.std_align!=df.slow_align).astype(float);E['ha_body_mean']=df[['fast_body_rng','std_body_rng','slow_body_rng']].mean(axis=1);E['ha_body_disp']=df[['fast_body_rng','std_body_rng','slow_body_rng']].std(axis=1).fillna(0);E['adx']=df.adx28_rel;E['di_mean']=df[['di14_signed','di28_signed']].mean(axis=1);E['di_disp']=(df.di14_signed-df.di28_signed).abs();E['ema']=df.ema8_21_signed;E['ema_slope']=df.ema8_slope;E['path_mean']=df[['path_eff4_rel','path_eff12_rel']].mean(axis=1);E['path_ratio']=df.path_eff4_rel/(df.path_eff12_rel.abs()+1e-6);E['flip_mean']=df[['flip4','flip8','flip12']].mean(axis=1);E['flip_accel']=df.flip4-df.flip12
for m,cc in {'align':['m15_aligned','m30_aligned','h1_aligned'],'transition':['m15_transition','m30_transition','h1_transition'],'streak':['m15_streak','m30_streak','h1_streak'],'body_sum':['m15_body_sum_atr','m30_body_sum_atr','h1_body_sum_atr'],'body_eff':['m15_body_eff','m30_body_eff','h1_body_eff'],'body_rng':['m15_body_rng','m30_body_rng','h1_body_rng'],'opp_wick':['m15_opp_wick','m30_opp_wick','h1_opp_wick']}.items():E[m+'_mean']=df[cc].mean(axis=1);E[m+'_disp']=df[cc].std(axis=1).fillna(0)
E['trend_flow']=E.adx*E.body_rng_mean;E['path_flow']=E.path_mean*E.body_rng_mean;E['dir_flow']=E.di_mean*E.body_rng_mean;E['ha_flow']=E.ha_body_mean*E.body_rng_mean
for c in E:df['e_'+c]=E[c]
eng=['e_'+c for c in E]
rankbase=['stop_dist_atr','fast_body_rng','std_body_rng','slow_body_rng','adx28_rel','di14_signed','ema8_21_signed','path_eff4_rel','path_eff12_rel','flip8','m15_body_rng','m30_body_rng','h1_body_rng']
def rp(v,w=360):
 v=np.asarray(v,float);o=np.full(len(v),.5);h=[]
 for i,x in enumerate(v):
  if len(h)>=40 and np.isfinite(x):o[i]=(bisect_right(h,float(x))+.5)/(len(h)+1)
  if np.isfinite(x):insort(h,float(x))
  j=i-w
  if j>=0 and np.isfinite(v[j]):
   k=bisect_left(h,float(v[j]));
   if k<len(h):h.pop(k)
 return o
for c in rankbase:
 col='rk_'+c
 for _,g in df.groupby(['stage','direction'],sort=False):df.loc[g.index,col]=rp(g[c].values)
ranks=['rk_'+c for c in rankbase]
df.to_pickle(OUT/'ENRICHED.pkl')
(OUT/'FEATURES.json').write_text(__import__('json').dumps({'raw':raw,'eng':eng,'eng_rank':eng+ranks},indent=2))
print(df.shape,len(raw),len(eng),len(eng+ranks))
