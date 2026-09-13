import pandas as pd, numpy as np, math, json
from pathlib import Path
import sys
sys.path.append('/mnt/data')
from scripts.v9_vector_topology import load,aggregate,pivots,attach_raids,events_from_objs,resolve

class SegTree:
    def __init__(self, highs, lows):
        self.n0=len(highs); n=1
        while n<self.n0: n*=2
        self.n=n
        self.mx=np.full(2*n,-np.inf,float); self.mn=np.full(2*n,np.inf,float)
        self.mx[n:n+self.n0]=highs; self.mn[n:n+self.n0]=lows
        for i in range(n-1,0,-1):
            self.mx[i]=max(self.mx[2*i],self.mx[2*i+1]); self.mn[i]=min(self.mn[2*i],self.mn[2*i+1])
    def first_high_ge(self,start,target):
        def rec(node,l,r):
            if r<=start or self.mx[node] < target: return None
            if node>=self.n: return l if l<self.n0 else None
            m=(l+r)//2
            x=rec(node*2,l,m)
            return x if x is not None else rec(node*2+1,m,r)
        return rec(1,0,self.n)
    def first_low_le(self,start,target):
        def rec(node,l,r):
            if r<=start or self.mn[node] > target: return None
            if node>=self.n: return l if l<self.n0 else None
            m=(l+r)//2
            x=rec(node*2,l,m)
            return x if x is not None else rec(node*2+1,m,r)
        return rec(1,0,self.n)

def block_build(df,start,end,name):
    bdf=df[(df.index>=start)&(df.index<end)].copy()
    h4=aggregate(bdf,4); h4objs=attach_raids(df,pivots(h4,'H4',4))
    ev=events_from_objs(df,h4objs,start,end); rr=resolve(ev)
    # Only opportunities with a next H4 event for topology-direction study; for trading allow final active arrival too.
    rr2=rr[rr.eligible].copy().reset_index(drop=True)
    # H1 structural objects from same block-internal reconstruction
    h1=aggregate(bdf,1); h1objs=attach_raids(df,pivots(h1,'H1',1))
    return bdf,h4,h4objs,ev,rr,rr2,h1,h1objs

def choose_h1_sl(h1objs, ts, direction, entry):
    # Must already be known and remain unraided strictly after entry minute; avoid same-minute invalidation ambiguity.
    active=h1objs[(h1objs.known_at<=ts) & (h1objs.raid_at.isna() | (h1objs.raid_at>ts))]
    if direction=='UP':
        c=active[(active.side=='DOWN') & (active.price<entry)]
        return float(c.price.max()) if len(c) else np.nan
    else:
        c=active[(active.side=='UP') & (active.price>entry)]
        return float(c.price.min()) if len(c) else np.nan

def prepare_opps(bdf,rr2,h1objs,block):
    out=[]
    for r in rr2.itertuples(index=False):
        ts=pd.Timestamp(r.ts); side=r.primary; entry=float(r.ref)
        row=bdf.loc[ts]
        if side=='UP':
            tp=float(r.nearest_bsl) if pd.notna(r.nearest_bsl) and float(r.nearest_bsl)>entry else np.nan
            gap=bool(float(row.open)>entry)
        else:
            tp=float(r.nearest_ssl) if pd.notna(r.nearest_ssl) and float(r.nearest_ssl)<entry else np.nan
            gap=bool(float(row.open)<entry)
        h1sl=choose_h1_sl(h1objs,ts,side,entry)
        out.append(dict(block=block,entry_ts=ts,direction=side,entry=entry,tp=tp,topology=r.topology,
                        d_same=r.d_same,d_opp=r.d_opp,resolution=r.resolution,next_side=r.next_side,dir_hit=r.hit,
                        h1_sl=h1sl,gap_cross=gap))
    return pd.DataFrame(out)

def resolve_trade_series(bdf,opps,sl_kind,sl_dist=None):
    times=bdf.index.to_numpy(); highs=bdf.high.to_numpy(float); lows=bdf.low.to_numpy(float)
    seg=SegTree(highs,lows)
    rec=[]
    for o in opps.itertuples(index=False):
        entry=o.entry; side=o.direction; tp=o.tp
        if sl_kind=='H1_STRUCT': sl=o.h1_sl
        else: sl=entry-sl_dist if side=='UP' else entry+sl_dist
        if pd.isna(sl) or (side=='UP' and not sl<entry) or (side=='DOWN' and not sl>entry):
            rec.append({**o._asdict(),'sl_arm':sl_kind if sl_dist is None else f'FIXED_{sl_dist:g}','sl':sl,'sl_dist':np.nan,'tp_dist':abs(tp-entry) if pd.notna(tp) else np.nan,'status':'NO_VALID_SL','exit_ts':pd.NaT,'R':np.nan})
            continue
        risk=abs(entry-sl)
        if risk<=0:
            rec.append({**o._asdict(),'sl_arm':sl_kind,'sl':sl,'sl_dist':risk,'tp_dist':abs(tp-entry) if pd.notna(tp) else np.nan,'status':'NO_VALID_SL','exit_ts':pd.NaT,'R':np.nan}); continue
        i=int(np.searchsorted(times,np.datetime64(o.entry_ts.to_datetime64()),side='left'))
        if side=='UP':
            isl=seg.first_low_le(i,sl)
            itp=seg.first_high_ge(i,tp) if pd.notna(tp) else None
        else:
            isl=seg.first_high_ge(i,sl)
            itp=seg.first_low_le(i,tp) if pd.notna(tp) else None
        status='OPEN_CENSORED'; exit_i=None; R=np.nan
        if isl is None and itp is None:
            pass
        elif isl is not None and itp is not None and isl==itp:
            status='INTRAMINUTE_AMBIGUOUS'; exit_i=isl
        elif itp is not None and (isl is None or itp<isl):
            status='TP'; exit_i=itp; R=abs(tp-entry)/risk
        elif isl is not None and (itp is None or isl<itp):
            status='SL'; exit_i=isl; R=-1.0
        exit_ts=pd.Timestamp(times[exit_i]) if exit_i is not None else pd.NaT
        rec.append({**o._asdict(),'sl_arm':sl_kind if sl_dist is None else f'FIXED_{sl_dist:g}','sl':sl,'sl_dist':risk,'tp_dist':abs(tp-entry) if pd.notna(tp) else np.nan,'status':status,'exit_ts':exit_ts,'R':R})
    return pd.DataFrame(rec)

def maxdd(rs):
    if len(rs)==0: return np.nan
    eq=np.cumsum(rs); peak=np.maximum.accumulate(np.r_[0,eq]); vals=np.r_[0,eq]; return float(np.max(peak-vals))

def stats(df):
    eligible=df[df.status!='NO_VALID_SL']
    resolved=eligible[eligible.status.isin(['TP','SL'])]
    wins=resolved[resolved.status=='TP']; losses=resolved[resolved.status=='SL']
    pos=wins.R.sum(); neg=-losses.R.sum()
    return dict(opportunities=len(df),eligible=len(eligible),resolved=len(resolved),wins=len(wins),losses=len(losses),
                wr=(len(wins)/len(resolved) if len(resolved) else np.nan),total_R=float(resolved.R.sum()) if len(resolved) else np.nan,
                mean_R=float(resolved.R.mean()) if len(resolved) else np.nan,pf=(float(pos/neg) if neg>0 else np.inf),max_dd=maxdd(resolved.R.to_numpy()),
                avg_win_R=float(wins.R.mean()) if len(wins) else np.nan,median_win_R=float(wins.R.median()) if len(wins) else np.nan,
                avg_sl=float(eligible.sl_dist.mean()) if len(eligible) else np.nan,median_sl=float(eligible.sl_dist.median()) if len(eligible) else np.nan,
                avg_tp=float(eligible.tp_dist.mean()) if eligible.tp_dist.notna().any() else np.nan,median_tp=float(eligible.tp_dist.median()) if eligible.tp_dist.notna().any() else np.nan,
                ambiguous=int((eligible.status=='INTRAMINUTE_AMBIGUOUS').sum()),censored=int((eligible.status=='OPEN_CENSORED').sum()),
                no_valid_sl=int((df.status=='NO_VALID_SL').sum()),gap_cross=int(eligible.gap_cross.sum()))

def one_position(df):
    d=df.sort_values('entry_ts').copy(); keep=[]; busy_until=None
    for i,r in d.iterrows():
        if busy_until is not None and r.entry_ts<=busy_until:
            continue
        keep.append(i)
        if pd.notna(r.exit_ts): busy_until=r.exit_ts
        else: busy_until=pd.Timestamp.max.tz_localize(None)
    return d.loc[keep].copy()

def split_stats(df):
    rows=[]
    for key,g in df.groupby('direction'):
        s=stats(g); s['split']='direction'; s['key']=key; rows.append(s)
    tmp=df.copy(); tmp['month']=tmp.entry_ts.dt.strftime('%Y-%m'); tmp['quarter']=tmp.entry_ts.dt.to_period('Q').astype(str)
    for col in ['month','quarter']:
        for key,g in tmp.groupby(col):
            s=stats(g); s['split']=col; s['key']=key; rows.append(s)
    return pd.DataFrame(rows)

def main():
    df=load()
    blocks=[]; topo=[]
    specs=[(pd.Timestamp('2024-01-01'),pd.Timestamp('2025-01-01'),'2024'),(pd.Timestamp('2025-01-01'),pd.Timestamp('2025-07-01'),'2025H1')]
    for start,end,name in specs:
        bdf,h4,h4objs,ev,rr,rr2,h1,h1objs=block_build(df,start,end,name)
        opp=prepare_opps(bdf,rr2,h1objs,name); blocks.append((name,bdf,opp))
        lab=rr[rr.eligible & rr.hit.notna()].copy(); lab['block']=name; topo.append(lab)
        print(name,'opps',len(opp),'SN',sum(opp.topology=='SAME_NEAREST'),'H1SL available',opp.h1_sl.notna().sum(),'gap',opp.gap_cross.sum())
    topodf=pd.concat(topo,ignore_index=True)
    print('\nTOPOLOGY')
    for name,g in topodf.groupby('block'):
        for typ,gg in [('ALL',g),('SAME_NEAREST',g[g.topology=='SAME_NEAREST']),('NOT_SAME',g[g.topology!='SAME_NEAREST'])]:
            print(name,typ,len(gg),int(gg.hit.sum()),gg.hit.mean())
    all_trade=[]; summaries=[]; splits=[]
    arms=[('H1_STRUCT',None)]+[('FIXED',x) for x in [10,15,20,25,30,40,50]]
    for name,bdf,oppall in blocks:
        for universe,opps in [('CONTROL',oppall),('SAME_NEAREST',oppall[oppall.topology=='SAME_NEAREST'].copy())]:
            for kind,dist in arms:
                tr=resolve_trade_series(bdf,opps,kind,dist); tr['universe']=universe; tr['block']=name
                all_trade.append(tr)
                s=stats(tr); s.update(block=name,universe=universe,sl_arm=tr.sl_arm.iloc[0] if len(tr) else (kind if dist is None else f'FIXED_{dist:g}'),position_mode='INDEPENDENT'); summaries.append(s)
                sp=split_stats(tr); sp['block']=name; sp['universe']=universe; sp['sl_arm']=s['sl_arm']; sp['position_mode']='INDEPENDENT'; splits.append(sp)
                op=one_position(tr); so=stats(op); so.update(block=name,universe=universe,sl_arm=s['sl_arm'],position_mode='ONE_POSITION'); summaries.append(so)
    trades=pd.concat(all_trade,ignore_index=True); summary=pd.DataFrame(summaries); split=pd.concat(splits,ignore_index=True)
    # combined 2024+2025H1 independent by simply concatenating outcomes of each block arm/universe
    comb=[]
    for (univ,arm),g in trades.groupby(['universe','sl_arm']):
        s=stats(g); s.update(block='COMBINED',universe=univ,sl_arm=arm,position_mode='INDEPENDENT'); comb.append(s)
    summary=pd.concat([summary,pd.DataFrame(comb)],ignore_index=True)
    topodf.to_csv('/mnt/data/V9_2024_2025H1_TOPOLOGY_LEDGER.csv',index=False)
    trades.to_csv('/mnt/data/V9_2024_2025H1_TRADE_LEDGER.csv',index=False)
    summary.to_csv('/mnt/data/V9_2024_2025H1_SL_SUMMARY.csv',index=False)
    split.to_csv('/mnt/data/V9_2024_2025H1_SPLITS.csv',index=False)
    print('\nSUMMARY independent SAME')
    print(summary[(summary.position_mode=='INDEPENDENT')&(summary.universe=='SAME_NEAREST')][['block','sl_arm','opportunities','eligible','resolved','wins','losses','wr','total_R','mean_R','pf','max_dd','avg_win_R','median_sl','median_tp','ambiguous','censored','no_valid_sl','gap_cross']].to_string(index=False))
    print('\nSUMMARY independent CONTROL')
    print(summary[(summary.position_mode=='INDEPENDENT')&(summary.universe=='CONTROL')][['block','sl_arm','opportunities','eligible','resolved','wins','losses','wr','total_R','mean_R','pf','max_dd','avg_win_R','median_sl','median_tp','ambiguous','censored','no_valid_sl','gap_cross']].to_string(index=False))
    print('\nONE POSITION SAME')
    print(summary[(summary.position_mode=='ONE_POSITION')&(summary.universe=='SAME_NEAREST')][['block','sl_arm','opportunities','eligible','resolved','wins','losses','wr','total_R','mean_R','pf','max_dd','ambiguous','censored']].to_string(index=False))
if __name__=='__main__': main()
