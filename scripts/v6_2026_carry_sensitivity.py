import sys, zipfile
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0,'/mnt/data')
import v6_003d_2026_independent_validator as v

ZIP=Path('/mnt/data/2026data.zip')
COLD=Path('/mnt/data/v6_2026_validation_work/all_triggers_routed.csv')
OUT=Path('/mnt/data/v6_2026_carry_sensitivity')
OUT.mkdir(exist_ok=True)

# End-2025 causal-state baselines. GOLD exact 2026 routing is reported separately;
# this fixed-baseline replay is a sensitivity for BTC/USDJPY where full historical raw arrays are not mounted.
BASE={
 'BTCUSD#': dict(n=213, scale=0.1842902383051549, accept_=0.015064475623302),
 'USDJPY#': dict(n=115, scale=0.1669464893021746, accept_=0.0185905340035986),
 'GOLD#': dict(n=168, scale=0.1583309712603747, accept_=0.0214266422590999),
}
qall=pd.read_csv(COLD,parse_dates=['sweep_time','trigger_time'])
allout=[]
with zipfile.ZipFile(ZIP) as z:
  names={n.split('_M1_')[0]:n for n in z.namelist() if n.lower().endswith('.csv')}
  for sym,q in qall.groupby('market',sort=False):
    q=q.sort_values('trigger_time').copy().reset_index(drop=True)
    b=BASE[sym]
    # Keep 2026-computable geometry values. For MENV-valid direct rows, compare to frozen end-2025
    # baseline rather than illegal Jan-1 reset. We intentionally do not claim exact rolling median here.
    eligible=q.m1_direct_transfer & q.geom & q.d1_atr.notna() & (q.d1_atr>0)
    q['menv_n_prior_carry']=np.where(eligible,b['n'],0)
    q['med_scale_carry']=np.where(eligible,b['scale'],np.nan)
    q['med_accept_carry']=np.where(eligible,b['accept_'],np.nan)
    q['menv_hh_carry']=eligible & (q.scale>b['scale']) & (q.acceptance>b['accept_'])
    q['h_auth']=q.m1_direct_transfer & q.geom & q.menv_hh_carry & (q.d24==q.dir)
    q['l1_auth']=q.m1_direct_transfer & (~q.h_auth) & (q.d14==q.dir) & (q.d24==q.dir)
    q['l2_auth']=q.m1_one_reneg & (q.d24==q.dir)
    q['module']=np.select([q.h_auth,q.l1_auth,q.l2_auth],['H','L1','L2'],default='NONE')
    m1=v.load_member(z,names[sym],v.POINTS[sym])
    s=v.simulate_routes(q,m1)
    allout.append(s)

A=pd.concat(allout,ignore_index=True)
A.to_csv(OUT/'all_triggers_carry_sensitivity.csv',index=False)
R=A[(A.module!='NONE') & A.accepted & A.prospective_fill_time.notna() & A.pnl_R.notna()].copy()
R=R.sort_values(['prospective_fill_time','market'])
R.to_csv(OUT/'accepted_resolved_carry_sensitivity.csv',index=False)

def metric(g):
    p=g[g.pnl_R>0]
    vals=g.sort_values('prospective_fill_time').pnl_R.tolist()
    return pd.Series({'N':len(g),'WR':(g.pnl_R>0).mean() if len(g) else np.nan,
                      'avg_positive_R':p.pnl_R.mean() if len(p) else np.nan,
                      'EV_R':g.pnl_R.mean() if len(g) else np.nan,'net_R':g.pnl_R.sum(),
                      'max_DD_R':v.max_dd(vals),'max_loss_streak':v.max_loss_streak(vals)})
for col,file in [('market','by_market.csv'),('module','by_module.csv'),('dir','by_direction.csv')]:
    R.groupby(col).apply(metric,include_groups=False).reset_index().to_csv(OUT/file,index=False)
R.groupby(['market','module']).apply(metric,include_groups=False).reset_index().to_csv(OUT/'by_market_module.csv',index=False)
L2=R[R.module=='L2'].copy();L2['age_bucket']=np.where(L2.d24_age>=24,'>=24','<24')
L2.groupby('age_bucket').apply(metric,include_groups=False).reset_index().to_csv(OUT/'l2_age_shadow.csv',index=False)
metric(R).to_frame('value').to_csv(OUT/'pooled.csv')

print('POOLED\n',metric(R))
print('\nBY MARKET\n',pd.read_csv(OUT/'by_market.csv').to_string(index=False))
print('\nBY MODULE\n',pd.read_csv(OUT/'by_module.csv').to_string(index=False))
print('\nBY MARKET MODULE\n',pd.read_csv(OUT/'by_market_module.csv').to_string(index=False))
print('\nL2 AGE\n',pd.read_csv(OUT/'l2_age_shadow.csv').to_string(index=False))
print('\nH EVENTS\n',R[R.module=='H'][['market','trigger_time','dir','outcome','pnl_R','d24_age','scale','acceptance']].to_string(index=False))
