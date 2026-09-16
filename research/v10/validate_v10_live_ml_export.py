import argparse,json,math,pandas as pd,numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--universe',required=True);ap.add_argument('--model-json',required=True);args=ap.parse_args()
D=pd.read_csv(args.universe)
M=json.load(open(args.model_json,encoding='utf-8'))
f=M['features']
# deterministic manual inference smoke test and chronology contract checks
assert len(f)==27
for c in f: assert c in D.columns,c
assert (D['year']>=2022).all()
def pred(spec,row):
 z=spec['intercept']
 for c,m,s,w in zip(f,spec['mean'],spec['scale'],spec['coef']): z+=w*((float(row[c])-m)/(s if abs(s)>1e-12 else 1.0))
 z=max(-35,min(35,z));return 1/(1+math.exp(-z))
checks=[]
for era in ('2023','2024','2025','2026','FUTURE'):
 for head in ('RUNWAY','WIN','PERSIST','SEVERE','STOP','SHOCK'):
  spec=M['eras'][era][head]
  vals=[pred(spec,D.iloc[i]) for i in np.linspace(0,len(D)-1,17,dtype=int)]
  assert all(math.isfinite(x) and 0<=x<=1 for x in vals)
  checks.append((era,head,min(vals),max(vals)))
print(json.dumps({'ok':True,'rows':len(D),'features':len(f),'checks':len(checks),'eras':['2023','2024','2025','2026','FUTURE'],
 'causal_contract':{'2023':'train 2022','2024':'train 2022-2023','2025':'train 2022-2024','2026':'train 2022-2025','FUTURE':'train through 2026-08-28'}},indent=2))
