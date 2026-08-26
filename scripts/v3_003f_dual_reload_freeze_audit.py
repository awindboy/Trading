#!/usr/bin/env python3
"""V3-003F frozen-candidate robustness/exposure audit from committed V3-003E ledgers.

Research only. Reads GOLD 2023-2025 discovery ledgers; does not read 2022 or 2021.
Candidate B uses H2 (direct-transfer, NOT H3/BOTH exclusion), the existing H +3R 25%
harvest control, primary Module L, and the pre-specified execution-compatible exposure
rule: same-direction coexistence allowed, opposite-direction coexistence blocked.
"""
from __future__ import annotations
import argparse, json, math, subprocess
from pathlib import Path
import numpy as np
import pandas as pd

BASE_HEAD = "fa8b4f447fa4990d3a26afd745d8743fe228d63a"
H_BLOB = "d1d652d4836f6859c5e0cfe7ced7580c0a77a46c"
L_BLOB = "daa3c35dd8cdec33356fc2dc07c07467cb799e19"
NATURAL_K=(1.5,2.0,2.5)
NATURAL_F=(0.25,0.50,0.75,1.00)


def _git(repo,*args):
    return subprocess.check_output(["git","-C",str(repo),*args],text=True).strip()


def _check_inputs(repo:Path,hp:Path,lp:Path):
    if not hp.exists() or not lp.exists():
        raise SystemExit(f"FAIL-CLOSED missing ledgers H={hp.exists()} L={lp.exists()}")
    # Exact immutable input identity; works both before and after the freeze-pack commit.
    if _git(repo,"hash-object",str(hp)) != H_BLOB:
        raise SystemExit("FAIL-CLOSED H ledger blob differs from V3-003E authority")
    if _git(repo,"hash-object",str(lp)) != L_BLOB:
        raise SystemExit("FAIL-CLOSED L ledger blob differs from V3-003E authority")


def _bool(s):
    if s.dtype==bool:return s
    return s.astype(str).str.lower().map({"true":True,"false":False})


def _metrics(df):
    a=pd.to_numeric(df.R).to_numpy(float); pos=a>1e-12
    return {
        "n":int(len(a)),
        "positive_rate":float(pos.mean()) if len(a) else math.nan,
        "avg_positive_R":float(a[pos].mean()) if pos.any() else math.nan,
        "expectancy_R":float(a.mean()) if len(a) else math.nan,
        "total_R":float(a.sum()),
    }


def _prepare(H,L):
    H=H.copy();L=L.copy()
    for c in ["source_k","fraction"]:H[c]=pd.to_numeric(H[c])
    for c in ["year","dir"]:H[c]=pd.to_numeric(H[c]).astype(int)
    H["direct_transfer"]=_bool(H.direct_transfer)
    H["both_branch"]=_bool(H.both_branch)
    H["owner_agree"]=_bool(H.owner_agree)
    for c in ["trigger_time","fill_time","resolved_at_h"]:H[c]=pd.to_datetime(H[c])
    H["H_primary_R"]=H.outcome.map({"TP5":5.0,"BE":0.0,"SL":-1.0})
    H["H_harvest_R"]=H.outcome.map({"TP5":4.5,"BE":0.75,"SL":-1.0})
    if H[["H_primary_R","H_harvest_R"]].isna().any().any():
        raise SystemExit("FAIL-CLOSED unsupported H outcome")

    for c in ["year","dir"]:L[c]=pd.to_numeric(L[c]).astype(int)
    for c in ["trigger_time","prior_trigger_time","res2_at"]:L[c]=pd.to_datetime(L[c])
    for c in ["checkpoint_hit","full1_hit","mirror_checkpoint_hit","res2_hit","L50_R"]:
        L[c]=pd.to_numeric(L[c],errors="raise")
    allowed={2023,2024,2025}
    if not set(H.year.unique()).issubset(allowed) or not set(L.year.unique()).issubset(allowed):
        raise SystemExit("FAIL-CLOSED non-discovery year present")
    return H,L


def _trade_candidates(h,L):
    return pd.concat([
        pd.DataFrame({
            "start":h.fill_time,"end":h.resolved_at_h,"year":h.year,"module":"H",
            "dir":h.dir,"R":h.H_harvest_R,
            "source_id":"H:"+h.trigger_time.astype(str),
        }),
        pd.DataFrame({
            "start":L.trigger_time,"end":L.res2_at,"year":L.year,"module":"L",
            "dir":L.dir,"R":L.L50_R,
            "source_id":"L:"+L.trigger_time.astype(str),
        })
    ],ignore_index=True).sort_values(["start","module","source_id"]).reset_index(drop=True)


def _apply_policy(df,policy):
    accepted=[]; blocked=[]
    for _,tr in df.iterrows():
        # end<=new start is treated as resolved before the new entry.
        active=[a for a in accepted if pd.Timestamp(a["end"])>pd.Timestamp(tr.start)]
        if policy=="ALL_INDEPENDENT": ok=True
        elif policy=="SERIAL_ONE_POSITION": ok=(len(active)==0)
        elif policy=="OPPOSITE_DIRECTION_BLOCK":
            ok=not any(int(a["dir"])==-int(tr.dir) for a in active)
        else: raise ValueError(policy)
        (accepted if ok else blocked).append(tr.to_dict())
    return pd.DataFrame(accepted),pd.DataFrame(blocked)


def _overlaps(H2,L):
    rows=[]
    for _,h in H2.iterrows():
        for _,l in L.iterrows():
            if pd.Timestamp(h.fill_time)<pd.Timestamp(l.res2_at) and pd.Timestamp(l.trigger_time)<pd.Timestamp(h.resolved_at_h):
                rows.append({
                    "kind":"H_L","h_trigger":h.trigger_time,"h_fill":h.fill_time,"h_end":h.resolved_at_h,
                    "h_dir":int(h.dir),"h_outcome":h.outcome,"l_trigger":l.trigger_time,"l_end":l.res2_at,
                    "l_dir":int(l.dir),"same_direction":int(h.dir)==int(l.dir),
                })
    hs=H2.sort_values("fill_time").reset_index(drop=True)
    for i,a in hs.iterrows():
        for j in range(i+1,len(hs)):
            b=hs.iloc[j]
            if pd.Timestamp(b.fill_time)>=pd.Timestamp(a.resolved_at_h): break
            rows.append({
                "kind":"H_H","h_trigger":a.trigger_time,"h_fill":a.fill_time,"h_end":a.resolved_at_h,
                "h_dir":int(a.dir),"h_outcome":a.outcome,"l_trigger":b.trigger_time,"l_end":b.resolved_at_h,
                "l_dir":int(b.dir),"same_direction":int(a.dir)==int(b.dir),
            })
    return pd.DataFrame(rows)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--out",type=Path,default=Path("v3_003f_freeze_out"))
    args=ap.parse_args();repo=args.repo.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    led=repo/"docs/ea/v3/ledgers";hp=led/"V3_003E_MODULE_H_ALL_VARIANTS_ENRICHED.csv";lp=led/"V3_003E_MODULE_L_PHYSICAL_LEDGER.csv"
    _check_inputs(repo,hp,lp)
    H,L=_prepare(pd.read_csv(hp),pd.read_csv(lp))
    H2=H[H.direct_transfer].copy()

    ref=H2[np.isclose(H2.source_k,2.0)&np.isclose(H2.fraction,0.5)].copy()
    assert len(ref)==44
    assert int((ref.outcome=="TP5").sum())==14
    assert int((ref.outcome=="SL").sum())==27
    assert int((ref.outcome=="BE").sum())==3
    assert len(L)==11 and int(L.checkpoint_hit.sum())==11 and int(L.full1_hit.sum())==10
    assert int(L.mirror_checkpoint_hit.sum())==1 and int(L.res2_hit.sum())==7

    # Reference policy comparison.
    basecand=_trade_candidates(ref,L)
    policies=[]
    for p in ["ALL_INDEPENDENT","SERIAL_ONE_POSITION","OPPOSITE_DIRECTION_BLOCK"]:
        q,b=_apply_policy(basecand,p);m=_metrics(q);policies.append({"policy":p,**m,"blocked_n":len(b)})
    pd.DataFrame(policies).to_csv(out/"exposure_policy_comparison.csv",index=False)

    # Frozen Candidate-B reference and natural surface under the pre-specified contract.
    surface=[];annual=[];loo=[]
    for k in NATURAL_K:
        for f in NATURAL_F:
            h=H2[np.isclose(H2.source_k,k)&np.isclose(H2.fraction,f)].copy()
            q,b=_apply_policy(_trade_candidates(h,L),"OPPOSITE_DIRECTION_BLOCK")
            surface.append({"source_k":k,"fraction":f,**_metrics(q),"blocked_n":len(b)})
            for y,g in q.groupby("year"):
                annual.append({"source_k":k,"fraction":f,"year":int(y),**_metrics(g)})
            for omit in [2023,2024,2025]:
                loo.append({"source_k":k,"fraction":f,"omitted_year":omit,**_metrics(q[q.year!=omit])})
            if k==2.0 and f==0.5:
                q.to_csv(out/"candidate_b_reference_trade_basket.csv",index=False)
                b.to_csv(out/"candidate_b_reference_blocked_entries.csv",index=False)
    surf=pd.DataFrame(surface);ann=pd.DataFrame(annual);lo=pd.DataFrame(loo)
    surf.to_csv(out/"candidate_b_natural_surface.csv",index=False)
    ann.to_csv(out/"candidate_b_natural_surface_by_year.csv",index=False)
    lo.to_csv(out/"candidate_b_leave_one_year_out.csv",index=False)

    ov=_overlaps(ref,L);ov.to_csv(out/"reference_exposure_overlaps.csv",index=False)

    # H branch audit: H3 is deliberately shadow-only.
    branch=ref.copy()
    branch["branch"]=np.select([
        branch.both_branch,
        (branch.m30_exp>1)&(~branch.owner_agree.astype(bool)),
        (branch.m30_exp<=1)&branch.owner_agree.astype(bool),
    ],["BOTH","EXP_ONLY","OWNER_ONLY"],default="NEITHER")
    bsum=branch.groupby(["year","branch"]).agg(
        n=("outcome","size"),tp5=("outcome",lambda s:int((s=="TP5").sum())),
        sl=("outcome",lambda s:int((s=="SL").sum())),be=("outcome",lambda s:int((s=="BE").sum())),
        primary_ev_R=("H_primary_R","mean")
    ).reset_index()
    bsum.to_csv(out/"adaptive_h2_branch_summary.csv",index=False)

    refq,_=_apply_policy(basecand,"OPPOSITE_DIRECTION_BLOCK")
    manifest={
        "base_head_when_frozen":BASE_HEAD,
        "input_blobs":{"H":H_BLOB,"L":L_BLOB},
        "parity":{"H2_n":44,"H2_tp5":14,"H2_sl":27,"H2_be":3,"L_n":11,"L_res2":7},
        "candidate_b_reference":_metrics(refq),
        "candidate_b_blocked_n":int(len(basecand)-len(refq)),
        "exposure_rule":"same-direction coexistence allowed; opposite-direction coexistence blocked",
        "H3_BOTH_used":False,
        "validation_2022":"CLOSED",
        "2021":"UNTOUCHED",
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("PARITY PASS")
    print(json.dumps(manifest,indent=2))
    print("\nNatural surface")
    print(surf.to_string(index=False))

if __name__=="__main__":main()
