import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler,OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss
D=pd.read_csv('/mnt/data/v13_ltf_structural_r_dataset.csv',parse_dates=['event_ts','flip_time'])
D['yt']=(D.outcome=='TARGET').astype(int)
cat=['reaction','family']
shape=['depth','pullback_h','h4_run_age','env_ratio','prior_success_n','env_available','env_breach','pen_wick','pen_close','m15_close_loc','m15_path_eff','m15_aligned_frac','depth_slope3','h1_align','target_R']
atr=['depth_atr','impulse_atr','poi_width_atr','rej_atr','acc_atr','m15_body_atr','m15_range_atr','m15_opp_wick_atr','m15_path_body_atr','h1_body_atr','h1_rng_atr','h4_ha_body_atr','h4_ha_rng_atr','h4_raw_close_vs_ha']
sets={'TARGET_R_ONLY':['target_R'],'SHAPE':shape,'SHAPE_ATR':shape+atr}
for y in [2024,2025,2026]:
 tr=D[(D.year<y)&(D.flip_time<pd.Timestamp(f'{y}-01-01'))]; te=D[D.year==y]
 print('\nYEAR',y,'train',len(tr),'test',len(te))
 for name,nums in sets.items():
  cats=[] if name=='TARGET_R_ONLY' else cat
  pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('sc',RobustScaler(quantile_range=(10,90)))]),nums),('cat',OneHotEncoder(handle_unknown='ignore'),cats)])
  m=Pipeline([('pre',pre),('m',LogisticRegression(C=.5,max_iter=1500))]); m.fit(tr[nums+cats],tr.yt); p=m.predict_proba(te[nums+cats])[:,1]
  print(name,'AUC',round(roc_auc_score(te.yt,p),4),'Brier',round(brier_score_loss(te.yt,p),4))
