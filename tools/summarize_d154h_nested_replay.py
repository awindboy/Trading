#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re,tempfile,zipfile
from pathlib import Path
from collections import defaultdict,Counter

KV=re.compile(r"(?:^|\s)([A-Za-z0-9_]+)=([^\s]*)")
def kv(s:str): return {m.group(1):m.group(2) for m in KV.finditer(s or "")}

def find_csv(p:Path):
    if p.suffix.lower()==".csv": return p,None
    if p.suffix.lower()==".zip":
        td=tempfile.TemporaryDirectory(); z=zipfile.ZipFile(p); z.extractall(td.name)
        cs=list(Path(td.name).rglob("*.csv"))
        if len(cs)!=1: raise SystemExit(f"expected one CSV in discovery ZIP, found {len(cs)}")
        return cs[0],td
    raise SystemExit("input must be CSV or ZIP")

def load(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("input",type=Path); args=ap.parse_args()
    cp,tmp=find_csv(args.input); rows=load(cp)
    ev=[]; stages=defaultdict(lambda:defaultdict(list)); fills={}; outcomes={}
    starts=sum(r.get("event")=="D154H_RESEARCH_START" for r in rows); stops=sum(r.get("event")=="D154H_RESEARCH_STOP" for r in rows)
    warnings=[r for r in rows if r.get("event")=="D154H_INTEGRITY_WARNING"]
    for r in rows:
        e=r.get("event",""); d=kv(r.get("detail",""))
        if e=="D154H_HTF_EVENT":
            try: seq=int(d.get("seq","-1"))
            except: continue
            ev.append((seq,d))
        elif e=="D154H_STAGE_SNAPSHOT":
            sid=d.get("scenario_id",r.get("object_id","")); stage=d.get("stage","")
            if sid and stage: stages[sid][stage].append(d)
        elif e=="D154H_FILL_REPLAY_ANCHOR":
            sid=d.get("scenario_id",r.get("object_id","")); fills[sid]=d
        elif e=="D154H_PRIMARY_OUTCOME":
            sid=d.get("scenario_id",r.get("object_id","")); outcomes[sid]=d.get("outcome","")
    ev.sort(key=lambda x:x[0])
    seqs=[x[0] for x in ev]
    monotonic=(seqs==sorted(seqs) and len(seqs)==len(set(seqs)) and (not seqs or seqs==list(range(seqs[0],seqs[-1]+1))))
    print(f"D154H integrity: start={starts} stop={stops} htf_events={len(ev)} fills={len(fills)} outcomes={len(outcomes)} warnings={len(warnings)} seq_monotonic={monotonic}")
    missing_out=[s for s in fills if s not in outcomes]
    print(f"missing_outcomes={len(missing_out)}")

    def stage_seq(sid,stage):
        a=stages.get(sid,{}).get(stage,[])
        if not a:return None
        try:return int(a[-1].get("seq_at_stage","-1"))
        except:return None
    def event_token(d): return f"{d.get('event_tf','?')}:{d.get('event_type','?')}:{d.get('event_direction','?')}"
    signature_stats=Counter(); signature_out=defaultdict(Counter); interval_counts=defaultdict(Counter)
    missing_plan=0
    for master,f in fills.items():
        contrib=f.get("contributor_scenario_ids",master).split("|") if f.get("contributor_scenario_ids",master) else [master]
        fill_seq=int(f.get("event_seq_at_fill","-1"))
        out=outcomes.get(master,"MISSING")
        fill_signatures=[]
        for sid in contrib:
            ps=stage_seq(sid,"PLAN")
            if ps is None:
                missing_plan+=1; continue
            cs=stage_seq(sid,"ROOT_CONTACT")
            ss=stage_seq(sid,"SWEEP")
            hs=stage_seq(sid,"CHOCH")
            pend=stage_seq(master,"PENDING")
            bounds=[("PLAN_CONTACT",ps,cs),("CONTACT_SWEEP",cs,ss),("SWEEP_CHOCH",ss,hs),("CHOCH_PENDING",hs,pend),("PENDING_FILL",pend,fill_seq)]
            toks=[]
            for seq,d in ev:
                if seq>ps and seq<=fill_seq: toks.append(event_token(d))
            sig=" > ".join(toks) if toks else "NO_HTF_EVENT_PLAN_TO_FILL"
            fill_signatures.append(sig)
            for name,a,b in bounds:
                if a is None or b is None: continue
                n=sum(1 for seq,_ in ev if seq>a and seq<=b)
                interval_counts[name][n]+=1
        master_sig=" || ".join(fill_signatures) if fill_signatures else "MISSING_CONTRIBUTOR_REPLAY"
        signature_stats[master_sig]+=1; signature_out[master_sig][out]+=1
    print(f"missing_contributor_plan_anchors={missing_plan}")
    print("\nTop exact fill-level replay signatures (descriptive only):")
    for sig,n in signature_stats.most_common(15):
        c=signature_out[sig]
        print(f"n={n:3d} +1R={c['PLUS_1R']:3d} SL={c['SL_FIRST']:3d} cens={c['RIGHT_CENSORED']:3d} :: {sig}")
    print("\nInterval HTF-event count distributions (contributor paths; descriptive):")
    for name,c in interval_counts.items():
        print(name,dict(sorted(c.items())))
    print("\nNo sequence is promoted by this summarizer. Freeze any candidate mechanism in a later phase before validation.")
    return 0
if __name__=="__main__": raise SystemExit(main())
