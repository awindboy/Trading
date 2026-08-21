from __future__ import annotations
import re,sys
import pandas as pd

def kv(s):
    if pd.isna(s): return {}
    return dict(re.findall(r'([A-Za-z0-9_]+)=([^\\s]+)',str(s)))

def num(x):
    try:return float(x)
    except:return None

def main(path):
    d=pd.read_csv(path)
    starts=d[d.event=='EA_START']
    print('EA_START',len(starts))
    if len(starts): print(starts.iloc[-1].detail)
    closes=[]
    for _,r in d[d.event=='D151_ACTUAL_CLOSE'].iterrows():
        z=kv(r.detail); v=num(z.get('actual_net_r'))
        if v is not None: closes.append(v)
    if closes:
        s=pd.Series(closes)
        w=s[s>0]; l=s[s<=0]
        print(f'closed={len(s)} WR={(s>0).mean():.2%} R>=1={(s>=1).mean():.2%} avg_win={w.mean() if len(w) else float("nan"):.3f} avg_loss={l.mean() if len(l) else float("nan"):.3f} expectancy={s.mean():.3f} total={s.sum():.3f}')
    for ev in ['D152_SP_KNOWN_DEFAULT_FULL_CLOSE','D152_SP_BANK_ACCEPTED','D152_SP_BANK_ALREADY_SATISFIED','D152_SP_BANK_INFEASIBLE','D152_SP_PLUS2_STATE']:
        print(ev, int((d.event==ev).sum()))
    if (d.event=='D152_SP_PLUS2_STATE').any():
        reasons=[]
        for x in d.loc[d.event=='D152_SP_PLUS2_STATE','detail']:
            reasons.append(kv(x).get('reason','NA'))
        print(pd.Series(reasons).value_counts().to_string())
if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit('usage: summarize_v2_d152_sp.py <ledger.csv>')
    main(sys.argv[1])
