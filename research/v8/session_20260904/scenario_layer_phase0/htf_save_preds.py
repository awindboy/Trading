exec(open('/mnt/data/htf_probe.py').read().split("specs=[")[0])
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
outs=[]
for name,freq,h,k in [('H1','1h',60,.5),('H4','4h',240,1.0)]:
 z=build_decisions(freq,h,k); cols=[c for c in z.columns if c not in ['origin_pos','S','origin_close','y','mfe_up','mfe_dn']]
 for year in [2024,2025,2026]:
  tr=z[z.index.year<year];te=z[z.index.year==year].copy()
  if len(te)<100:continue
  md=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,C=1.0));md.fit(tr[cols],tr.y);p=md.predict_proba(te[cols])[:,1]
  te['p_move']=p;te['tf']=name;te['year']=year;te['rank_year']=pd.Series(p,index=te.index).rank(pct=True).to_numpy();outs.append(te.reset_index())
out=pd.concat(outs,ignore_index=True);out.to_csv('/mnt/data/htf_movement_preds.csv',index=False);print(out.groupby(['tf','year']).agg(N=('y','size'),base=('y','mean'),p90=('p_move',lambda x:np.quantile(x,.9))).round(4))
