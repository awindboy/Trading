#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, pickle, sys, hashlib
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_VERSION = 'v9-2024-loss-postmortem-1'

# state.pkl was produced by the interactive 2024 runner whose observer class lived in __main__.
# A shell class is sufficient for read-only postmortem inspection.
class TickAwareObserver:
    pass


def dt(s):
    if not s: return None
    return datetime.fromisoformat(s)


def sha256(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()


def read_csv(path):
    with path.open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))


def fnum(x, default=None):
    if x in (None,''): return default
    return float(x)


def bval(x):
    return str(x).lower()=='true'


def latest(seq, times, t):
    i=bisect_right(times,t)-1
    return seq[i] if i>=0 else None


def objdict(x):
    return vars(x) if hasattr(x,'__dict__') else x


def side_support(consensus, side):
    return consensus == side


def load_minute_quotes(path):
    q={}
    with path.open(newline='',encoding='ascii') as f:
        r=csv.DictReader(f,delimiter='\t')
        for z in r:
            t=datetime.strptime(z['minute'],'%Y.%m.%d %H:%M')
            q[t]={k:float(z[k]) for k in ['bid_open','bid_high','bid_low','bid_close','ask_open','ask_high','ask_low','ask_close']}
    return q


def quote_exit_r(q, side, entry, risk):
    if q is None or not risk: return None
    px=q['bid_open'] if side=='UP' else q['ask_open']
    pnl=(px-entry) if side=='UP' else (entry-px)
    return pnl/risk


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--trades',required=True)
    ap.add_argument('--state',required=True)
    ap.add_argument('--minute-quotes',required=True)
    ap.add_argument('--out-dir',required=True)
    args=ap.parse_args()
    trades_p=Path(args.trades); state_p=Path(args.state); quotes_p=Path(args.minute_quotes); out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)

    # Make class visible as __main__.TickAwareObserver for pickle.
    import __main__
    __main__.TickAwareObserver=TickAwareObserver
    with state_p.open('rb') as f: st=pickle.load(f)
    m=st['market']; o=m.observer
    rows=read_csv(trades_p)
    quotes=load_minute_quotes(quotes_p)

    h4_times=[x.known_at for x in m.h4_states]
    h1_times=[x['known_at'] for x in m.h1_states]
    m15_times=[x.known_at for x in m.m15_states]
    m5_times=[x.known_at for x in m.m5_states]

    # Child and authorization maps.
    child_map={}
    auth_events=[]
    for lane in (o.counter,o.with_parent):
        for c in lane.children: child_map[c.child_id]=c
        for e in lane.events:
            if e.kind=='PITCH_AUTHORIZED': auth_events.append(e)
    auth_by_key=defaultdict(list)
    for e in auth_events:
        auth_by_key[(e.branch,e.parent_id,e.side,e.known_at)].append(e)

    # Pre-existing swing liquidity candidates.
    swings=[x for x in o.book.objects if x.family=='SWING' and x.end_reason=='RAIDED' and x.ended_at is not None]

    enriched=[]
    for z in rows:
        rec=dict(z)
        cid=z['child_id']; c=child_map.get(cid)
        entry=dt(z['entry_at']); exit_at=dt(z['exit_at']); auth_at=dt(z['authorized_at'])
        branch=z['branch']; side=z['side']; parent_id=z['parent_id_at_entry']
        entry_price=fnum(z['entry_price']); risk=fnum(z['initial_risk']); mfe_r=fnum(z['mfe_r'],0.0); mae_r=fnum(z['mae_r'],0.0); rr=fnum(z['realized_r'])
        cens=bval(z['censored'])
        dur_min=(exit_at-entry).total_seconds()/60 if entry and exit_at else None

        ae=(auth_by_key.get((branch,parent_id,side,auth_at)) or [None])[0]
        auth_class=ae.payload.get('auth_class') if ae else ''

        hs=latest(m.h4_states,h4_times,entry) if entry else None
        h1=latest(m.h1_states,h1_times,entry) if entry else None
        m15=latest(m.m15_states,m15_times,entry) if entry else None
        m5=latest(m.m5_states,m5_times,entry) if entry else None
        h1d=objdict(h1) if h1 else {}; h4d=objdict(hs) if hs else {}; m15d=objdict(m15) if m15 else {}; m5d=objdict(m5) if m5 else {}

        # Favorable liquidity delivery = a swing that is causally known before its raid, on the profitable side of entry,
        # and raided while the trade is alive. The swing may become known after entry; it must be known before delivery. This is descriptive postmortem evidence, not TP authority.
        fd=[]
        if entry and exit_at:
            want='HIGH' if side=='UP' else 'LOW'
            for sw in swings:
                if sw.direction!=want: continue
                if sw.object_known_at>=sw.ended_at or not (entry < sw.ended_at <= exit_at): continue
                p=sw.price_high if want=='HIGH' else sw.price_low
                if side=='UP' and p<=entry_price: continue
                if side=='DOWN' and p>=entry_price: continue
                fd.append(sw)
            fd.sort(key=lambda x:x.ended_at)
        first_fd=fd[0] if fd else None

        # First completed M15 state after first favorable delivery that no longer supports Child side.
        ns=None; ns_r=None
        if first_fd:
            start=bisect_right(m15_times,first_fd.ended_at-timedelta(microseconds=1))
            for x in m.m15_states[start:]:
                if exit_at and x.known_at>exit_at: break
                if x.consensus != side:
                    ns=x; q=quotes.get(x.known_at.replace(second=0,microsecond=0)); ns_r=quote_exit_r(q,side,entry_price,risk); break

        loss_class=''
        if not cens and rr is not None and rr<0:
            if z['terminal_reason']=='HARD_SL':
                if mfe_r>=1.0: loss_class='PROFITABLE_1R_PLUS_THEN_HARD_SL'
                elif dur_min is not None and dur_min<=60 and mfe_r<0.25: loss_class='FAST_NO_PROGRESS_HARD_SL'
                elif mfe_r<0.25: loss_class='NO_PROGRESS_HARD_SL'
                else: loss_class='PARTIAL_PROGRESS_HARD_SL'
            elif z['terminal_reason']=='AI_EXIT': loss_class='AI_EARLY_LOSS_EXIT'
            else: loss_class='OTHER_LOSS'

        rec.update({
            'auth_class':auth_class,
            'duration_minutes': '' if dur_min is None else f'{dur_min:.6f}',
            'loss_class':loss_class,
            'h4_flow_at_entry':h4d.get('flow_state',''),
            'h4_macro_at_entry':h4d.get('macro_state_majority',''),
            'h4_macro_agree_n':h4d.get('macro_agree_n',''),
            'h4_role_at_entry':h4d.get('role_state_majority',''),
            'h4_role_agree_n':h4d.get('role_agree_n',''),
            'h1_consensus_at_entry':h1d.get('consensus',''),
            'h1_agree_n':h1d.get('agree_n',''),
            'h1_relation_at_entry':h1d.get('h1_vs_h4_relation',''),
            'm15_consensus_at_entry':m15d.get('consensus',''),
            'm15_agree_n':m15d.get('agree_n',''),
            'm15_supports_child':str(bool(m15 and side_support(m15.consensus,side))),
            'm5_consensus_at_entry':m5d.get('consensus',''),
            'm5_agree_n':m5d.get('agree_n',''),
            'm5_supports_child':str(bool(m5 and side_support(m5.consensus,side))),
            'favorable_liquidity_delivery_count':len(fd),
            'first_favorable_delivery_at': first_fd.ended_at.isoformat(sep=' ') if first_fd else '',
            'first_favorable_delivery_object': first_fd.object_id if first_fd else '',
            'first_post_delivery_m15_nonsupport_at': ns.known_at.isoformat(sep=' ') if ns else '',
            'first_post_delivery_m15_nonsupport_consensus': ns.consensus if ns else '',
            'counterfactual_r_at_first_post_delivery_m15_nonsupport': '' if ns_r is None else f'{ns_r:.9f}',
        })
        enriched.append(rec)

    # Normalize typed helper view.
    def num(r,k): return fnum(r.get(k))
    closed=[r for r in enriched if not bval(r['censored']) and r.get('exit_at')]
    losses=[r for r in closed if num(r,'realized_r')<0]
    wins=[r for r in closed if num(r,'realized_r')>0]
    hard=[r for r in losses if r['terminal_reason']=='HARD_SL']
    ai_loss=[r for r in losses if r['terminal_reason']=='AI_EXIT']
    fast=[r for r in hard if num(r,'duration_minutes')<=60 and num(r,'mfe_r')<0.25]
    give=[r for r in hard if num(r,'mfe_r')>=1.0]

    def stats(rs):
        vals=[num(r,'realized_r') for r in rs if num(r,'realized_r') is not None]
        return {'n':len(rs),'sum_r':sum(vals),'avg_r':sum(vals)/len(vals) if vals else None,'wins':sum(v>0 for v in vals),'losses':sum(v<0 for v in vals)}

    # Branch summaries, M5 support, auth class, monthly and parent.
    by_branch={b:stats([r for r in closed if r['branch']==b]) for b in ['COUNTER','WITH_PARENT']}
    hard_by_branch={b:stats([r for r in hard if r['branch']==b]) for b in ['COUNTER','WITH_PARENT']}
    fast_by_branch={b:stats([r for r in fast if r['branch']==b]) for b in ['COUNTER','WITH_PARENT']}
    give_by_branch={b:stats([r for r in give if r['branch']==b]) for b in ['COUNTER','WITH_PARENT']}

    m5_support={}
    for b in ['COUNTER','WITH_PARENT']:
        m5_support[b]={}
        for flag in ['True','False']:
            rs=[r for r in closed if r['branch']==b and r['m5_supports_child']==flag]
            s=stats(rs); s['hard_sl']=sum(r['terminal_reason']=='HARD_SL' for r in rs); s['hard_sl_rate']=s['hard_sl']/len(rs) if rs else None
            m5_support[b][flag]=s

    auth_summary={}
    for a in sorted(set(r['auth_class'] for r in closed)):
        auth_summary[a]=stats([r for r in closed if r['auth_class']==a])
        auth_summary[a]['by_branch']={b:stats([r for r in closed if r['auth_class']==a and r['branch']==b]) for b in ['COUNTER','WITH_PARENT']}

    monthly={}
    for r in closed:
        mo=r['entry_at'][:7]
        monthly.setdefault(mo,[]).append(r)
    monthly={k:{**stats(v),'hard_sl':sum(r['terminal_reason']=='HARD_SL' for r in v)} for k,v in sorted(monthly.items())}

    parents=defaultdict(list)
    for r in closed: parents[r['parent_id_at_entry']].append(r)
    parent_summary=[]
    for pid,rs in parents.items():
        s=stats(rs); s.update({'parent_id':pid,'hard_sl':sum(r['terminal_reason']=='HARD_SL' for r in rs),'fresh_reauth':sum(r['auth_class']=='FRESH_REAUTH' for r in rs)})
        parent_summary.append(s)
    parent_summary.sort(key=lambda x:x['sum_r'])

    # Delivery / post-delivery review evidence in 1R+ givebacks.
    give_delivery=[r for r in give if int(r['favorable_liquidity_delivery_count'])>0]
    give_ns=[r for r in give_delivery if r['first_post_delivery_m15_nonsupport_at']]
    give_ns_prof=[r for r in give_ns if fnum(r['counterfactual_r_at_first_post_delivery_m15_nonsupport'],-999)>0]
    cf_sum=sum(fnum(r['counterfactual_r_at_first_post_delivery_m15_nonsupport']) for r in give_ns_prof)
    final_sum=sum(num(r,'realized_r') for r in give_ns_prof)

    # Similar conditions in winners to show why it cannot be an automatic exit rule.
    win_delivery=[r for r in wins if int(r['favorable_liquidity_delivery_count'])>0]
    win_ns=[r for r in win_delivery if r['first_post_delivery_m15_nonsupport_at']]

    # Top-winner dependence.
    win_sorted=sorted([num(r,'realized_r') for r in wins],reverse=True)
    total_r=sum(num(r,'realized_r') for r in closed)
    remove_top={str(n):total_r-sum(win_sorted[:n]) for n in [1,3,5,10] if len(win_sorted)>=n}

    # Fast loss characteristics.
    fast_h4_3of3=sum(int(r['h4_macro_agree_n'] or 0)==3 for r in fast)
    fast_m5_support=Counter(r['m5_supports_child'] for r in fast)
    fast_m15_support=Counter(r['m15_supports_child'] for r in fast)

    loss_class_summary={}
    for c in sorted(set(r['loss_class'] for r in losses)):
        loss_class_summary[c]=stats([r for r in losses if r['loss_class']==c])
        loss_class_summary[c]['by_branch']={b:stats([r for r in losses if r['loss_class']==c and r['branch']==b]) for b in ['COUNTER','WITH_PARENT']}

    # Remap decisions from saved decisions file, if adjacent file exists.
    decisions_p=trades_p.parent/'ai_decisions.json'; remaps=[]
    if decisions_p.exists():
        dec=json.loads(decisions_p.read_text(encoding='utf-8'))
        remaps=[x for x in dec if x.get('decision')=='REMAP']

    summary={
      'version':SCRIPT_VERSION,
      'source_identity':{
        'trades_sha256':sha256(trades_p),'state_sha256':sha256(state_p),'minute_quotes_sha256':sha256(quotes_p),
      },
      'scope':'2024 is now CONSUMED POSTMORTEM DATA; statistics are research evidence, not future-hidden validation or production authority.',
      'all_closed':stats(closed),'wins':stats(wins),'losses':stats(losses),'hard_sl_losses':stats(hard),'ai_early_loss_exits':stats(ai_loss),
      'loss_classes':loss_class_summary,
      'branches':by_branch,'hard_sl_by_branch':hard_by_branch,'fast_no_progress_by_branch':fast_by_branch,'one_r_plus_giveback_by_branch':give_by_branch,
      'fast_no_progress':{
        **stats(fast),'definition':'HARD_SL within 60 minutes of fill and MFE < 0.25R (postmortem stratification only; not a live threshold)',
        'h4_macro_3of3':fast_h4_3of3,'m5_support_counts':dict(fast_m5_support),'m15_support_counts':dict(fast_m15_support),
      },
      'one_r_plus_then_hard_sl':{
        **stats(give),'definition':'HARD_SL after MFE >= 1R (postmortem stratification only; never a live TP/trailing threshold)',
        'two_r_plus':sum(num(r,'mfe_r')>=2 for r in hard),'three_r_plus':sum(num(r,'mfe_r')>=3 for r in hard),
        'favorable_liquidity_delivery':len(give_delivery),'post_delivery_m15_nonsupport':len(give_ns),'still_profitable_at_first_nonsupport':len(give_ns_prof),
        'counterfactual_subset_final_sum_r':final_sum,'counterfactual_subset_exit_at_nonsupport_sum_r':cf_sum,'counterfactual_difference_r':cf_sum-final_sum,
        'counterfactual_warning':'Descriptive hindsight comparison only. It does not authorize delivery->exit or M15 non-support->exit.'
      },
      'winner_same_event_warning':{
        'winners':len(wins),'winners_with_favorable_liquidity_delivery':len(win_delivery),'winners_with_post_delivery_m15_nonsupport':len(win_ns),
        'interpretation':'The same delivery + M15 wobble appears in many winners, so it cannot be promoted to an automatic exit rule.'
      },
      'm5_support_at_entry':m5_support,'authorization_class':auth_summary,'monthly':monthly,'worst_parents':parent_summary[:12],
      'top_winner_dependence':{'top_realized_r':win_sorted[:10],'total_r':total_r,'total_r_after_removing_top_winners':remove_top},
      'remap_decisions':remaps,
      'research_conclusions':[
        'Primary loss-conversion opportunity is not wider SL or fixed TP; it is better causal interpretation before/around entry and after meaningful delivery.',
        'Fast no-progress losses are mostly an entry-arrival/acceptance problem: H4 can be strong while the local price response at the execution location is not accepting the Child side.',
        'Counter losses include both bridge-never-opened failures and successful local bridges that completed meaningful delivery before later giving everything back.',
        'With-Parent losses more often indicate premature continuation entry while the H1/M15 repair is not actually finished.',
        'Fresh reauthorization underperformed first authorization in aggregate, but profitable months contain large reauthorization winners; do not add retry limits. Research new-auction versus exhausted-campaign semantics instead.',
        'Favorable liquidity delivery is a candidate AI review event, not TP authority. The AI must distinguish continued acceptance/expansion from Parent-side re-acceptance.',
      ],
      'next_research_contract':[
        'ENTRY ARRIVAL/ACCEPTANCE: compare fast no-progress losses against robust winners at the same causal chart inputs; study whether price accepts/rejects the M5 execution location without converting M5 consensus into a mandatory filter.',
        'DELIVERY/JOURNEY REVIEW: compare 1R+ giveback losses against large winners after favorable liquidity/landmark delivery; identify chart-native semantics of expansion versus role-completion, without fixed R/TP/trailing rules.',
        'REAUTH/CAMPAIGN EXHAUSTION: distinguish genuinely new auction information from repeated oscillation inside an exhausted Parent campaign; no retry counts/cooldowns.',
        'BRANCH-SPECIFIC SEMANTICS: Counter asks whether local bridge actually opened / completed; With-Parent asks whether repair truly ended and Parent-side acceptance re-emerged.',
        'Only after those studies, freeze any new ENTRY_REVIEW or PROGRESSION_REVIEW AI scheduler event and rerun all consumed data. Do not open 2025-07 yet.',
      ],
    }

    # Write full enriched and loss-only ledgers.
    fieldnames=list(enriched[0].keys())
    for name,data in [('V9_2024_ALL_TRADES_ENRICHED_20260913.csv',enriched),('V9_2024_LOSS_POSTMORTEM_LEDGER_20260913.csv',losses)]:
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fieldnames); w.writeheader(); w.writerows(data)
    (out/'V9_2024_LOSS_POSTMORTEM_SUMMARY_20260913.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
