from __future__ import annotations
import csv
import datetime as dt
import io
import json
import os
import re
import statistics
import zipfile
from pathlib import Path

import mt5_batch_runner as runner
from mt5_batch_runner import TestCase, BatchError

ULTRA_SYMBOLS=("GOLD#","BTCUSD#","SILVER#","CADJPY#")
PARITY_SYMBOLS=("GOLD#","CADJPY#")
STANDARD_NAME={"GOLD#":"GOLD","BTCUSD#":"BTCUSD","SILVER#":"SILVER","CADJPY#":"CADJPY"}

BASE_SETTINGS={
    "InpExitManagementMode":9,
    "InpEpisodeManagementMode":0,
    "InpV2D151CausalAudit":True,
    "InpV2D154EntrySurvivalAudit":False,
    "InpV2D154BConfirmationAudit":False,
    "InpV2D154CReaccelerationFvgAudit":False,
    "InpV2D154FCausalLineageAudit":False,
    "InpV2D154GHTFRootLineageAudit":False,
    "InpV2D154HHTFNestedReplayAudit":False,
    "InpV2D154JHTFDeliveryGeometryAudit":False,
}

PARITY_CASES=[
    TestCase(
        "D154UL_AUDITS_OFF",
        {
            **BASE_SETTINGS,
            "InpV2D154KCrossScaleReactionAudit":False,
            "InpV2D154MExecutionFrictionCounterfactualAudit":False,
        },
        "Ultra Low control: D154K/M both OFF",
    ),
    TestCase(
        "D154UL_AUDITS_ON",
        {
            **BASE_SETTINGS,
            "InpV2D154KCrossScaleReactionAudit":True,
            "InpV2D154MExecutionFrictionCounterfactualAudit":True,
        },
        "Ultra Low validation: D154K/M both ON",
    ),
]

FULL_CASE=TestCase(
    "D154UL_KM_ON",
    {
        **BASE_SETTINGS,
        "InpV2D154KCrossScaleReactionAudit":True,
        "InpV2D154MExecutionFrictionCounterfactualAudit":True,
    },
    "Ultra Low 2025 natural experiment against frozen Standard benchmark",
)

def kv(s:str)->dict[str,str]:
    return {m.group(1):m.group(2) for m in re.finditer(r"(\w+)=([^ ]+)",s or "")}

def rows_from_zip(zp:Path):
    out={}
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            if n.endswith(".csv"):
                out[n]=list(csv.DictReader(io.StringIO(
                    z.read(n).decode("utf-8-sig",errors="replace")
                )))
    return out

def canonical(rows):
    out=[]
    for r in rows:
        ev=r.get("event","")
        if ev.startswith("D154K_") or ev.startswith("D154M_"):
            continue
        d=dict(r)
        detail=d.get("detail","")
        detail=re.sub(r"csv_rows_written=\d+","csv_rows_written=<NORMALIZED>",detail)
        detail=re.sub(r"log_calls_suppressed=\d+","log_calls_suppressed=<NORMALIZED>",detail)
        d["detail"]=detail
        out.append(tuple(d.get(k,"") for k in
                         ("observed_at","event","timeframe","available_at","object_id","detail")))
    return out

def parity_check(zp:Path):
    files=rows_from_zip(zp)
    for sym in PARITY_SYMBOLS:
        off=[(n,r) for n,r in files.items() if "__D154UL_AUDITS_OFF__"+sym+"__" in n]
        on=[(n,r) for n,r in files.items() if "__D154UL_AUDITS_ON__"+sym+"__" in n]
        if len(off)!=1 or len(on)!=1:
            raise BatchError(f"{sym}: parity CSV discovery failed OFF={len(off)} ON={len(on)}")
        _,offr=off[0]; _,onr=on[0]
        if any((r.get("event","").startswith("D154K_") or
                r.get("event","").startswith("D154M_")) for r in offr):
            raise BatchError(f"{sym}: research rows present in OFF run")
        a,b=canonical(offr),canonical(onr)
        if a!=b:
            msg=f"{sym}: D154UL K+M NON-INTERFERENCE PARITY FAIL OFF={len(a)} ON={len(b)}"
            for i,(x,y) in enumerate(zip(a,b)):
                if x!=y:
                    msg+=f" first_diff_index={i} OFF={x} ON={y}"
                    break
            raise BatchError(msg)
        events=[r.get("event","") for r in onr]
        kfills=events.count("D154K_CROSS_SCALE_SNAPSHOT")
        mpairs=events.count("D154M_PAIR_OUTCOME")
        dfills=events.count("D151_FILL_SNAPSHOT")
        if kfills<=0 or kfills!=dfills or mpairs!=dfills:
            raise BatchError(
                f"{sym}: ON completeness fail D151 fills={dfills} K snapshots={kfills} M pairs={mpairs}"
            )
        if "D154K_INTEGRITY_WARNING" in events or "D154M_INTEGRITY_WARNING" in events:
            raise BatchError(f"{sym}: D154K/M integrity warning in parity ON run")
        print(f"{sym}: D154UL PARITY PASS | canonical={len(a)} fills={dfills} K={kfills} M={mpairs}")

def median(values):
    return statistics.median(values) if values else None

def analyze_rows(rows,symbol):
    ksnaps={}
    kout={}
    mpairs={}
    for r in rows:
        ev=r.get("event","")
        d=kv(r.get("detail",""))
        sid=d.get("scenario_id",r.get("object_id",""))
        if ev=="D154K_CROSS_SCALE_SNAPSHOT" and sid:
            ksnaps[sid]=d
        elif ev=="D154K_PRIMARY_OUTCOME" and sid:
            kout[sid]=d.get("outcome","")
        elif ev=="D154M_PAIR_OUTCOME" and sid:
            mpairs[sid]=d

    if not ksnaps or len(mpairs)!=len(ksnaps):
        raise BatchError(
            f"{symbol}: analysis completeness fail K snapshots={len(ksnaps)} M pairs={len(mpairs)}"
        )

    actual_plus=sum(p.get("actual_outcome")=="PLUS_1R" for p in mpairs.values())
    actual_sl=sum(p.get("actual_outcome")=="SL_FIRST" for p in mpairs.values())
    actual_cens=sum(p.get("actual_outcome")=="RIGHT_CENSORED" for p in mpairs.values())
    shadow_plus=sum(p.get("shadow_outcome")=="PLUS_1R" for p in mpairs.values())
    shadow_sl=sum(p.get("shadow_outcome")=="SL_FIRST" for p in mpairs.values())
    shadow_cens=sum(p.get("shadow_outcome")=="RIGHT_CENSORED" for p in mpairs.values())
    flips=sum(p.get("pair_class")=="ACTUAL_SL_TO_SHADOW_PLUS_1R" for p in mpairs.values())
    impossible=sum(p.get("pair_class")=="ACTUAL_PLUS_1R_TO_SHADOW_SL" for p in mpairs.values())
    if impossible:
        raise BatchError(f"{symbol}: impossible D154M pair count={impossible}")

    def nums(key):
        out=[]
        for d in ksnaps.values():
            try:
                v=float(d[key])
            except Exception:
                continue
            if v==v:
                out.append(v)
        return out

    resolved=actual_plus+actual_sl
    shadow_resolved=shadow_plus+shadow_sl
    return {
        "ultra_symbol":symbol,
        "standard_symbol":STANDARD_NAME[symbol],
        "fills":len(mpairs),
        "actual_plus1":actual_plus,
        "actual_sl_first":actual_sl,
        "actual_censored":actual_cens,
        "actual_survival": actual_plus/resolved if resolved else None,
        "shadow_plus1":shadow_plus,
        "shadow_sl_first":shadow_sl,
        "shadow_censored":shadow_cens,
        "shadow_survival": shadow_plus/shadow_resolved if shadow_resolved else None,
        "sl_to_shadow_plus1":flips,
        "rescue_of_actual_sl": flips/actual_sl if actual_sl else None,
        "median_spread_over_reaction_tr":median(nums("spread_over_reaction_tr")),
        "median_spread_over_risk":median(nums("spread_over_risk")),
        "median_spread_over_fvg":median(nums("spread_over_fvg")),
        "median_risk_over_reaction_tr":median(nums("risk_over_reaction_tr")),
    }

def verify_full(zp:Path):
    files=rows_from_zip(zp)
    summaries={}
    for sym in ULTRA_SYMBOLS:
        matches=[r for n,r in files.items() if "__D154UL_KM_ON__"+sym+"__" in n]
        if len(matches)!=1:
            raise BatchError(f"{sym}: full CSV discovery failed count={len(matches)}")
        rows=matches[0]
        events=[r.get("event","") for r in rows]
        if events.count("D154K_RESEARCH_START")!=1 or events.count("D154K_RESEARCH_STOP")!=1:
            raise BatchError(f"{sym}: D154K start/stop missing")
        if events.count("D154M_RESEARCH_START")!=1 or events.count("D154M_RESEARCH_STOP")!=1:
            raise BatchError(f"{sym}: D154M start/stop missing")
        if "D154K_INTEGRITY_WARNING" in events or "D154M_INTEGRITY_WARNING" in events:
            raise BatchError(f"{sym}: D154K/M integrity warning")
        if "EXECUTION_DIVERGENCE" in events or "PENDING_CANCEL_REJECTED" in events:
            raise BatchError(f"{sym}: execution integrity failure")
        summaries[sym]=analyze_rows(rows,sym)
        s=summaries[sym]
        print(
            f"{sym}: PASS | fills={s['fills']} actual={s['actual_plus1']}/"
            f"{s['actual_plus1']+s['actual_sl_first']} "
            f"shadow={s['shadow_plus1']}/{s['shadow_plus1']+s['shadow_sl_first']} "
            f"SL->shadow+1R={s['sl_to_shadow_plus1']}"
        )
    return summaries

def compare_to_standard(summaries,benchmark):
    rows=[]
    for ultra in ULTRA_SYMBOLS:
        u=summaries[ultra]
        std=benchmark["symbols"][u["standard_symbol"]]
        row={
            "symbol":u["standard_symbol"],
            "ultra_symbol":ultra,
            "standard_fills":std["fills"],
            "ultra_fills":u["fills"],
            "fill_delta":u["fills"]-std["fills"],
            "standard_actual_survival":std["actual_survival"],
            "ultra_actual_survival":u["actual_survival"],
            "actual_survival_delta_pp":(
                (u["actual_survival"]-std["actual_survival"])*100
                if u["actual_survival"] is not None else None
            ),
            "standard_shadow_survival":std["shadow_survival"],
            "ultra_shadow_survival":u["shadow_survival"],
            "shadow_survival_delta_pp":(
                (u["shadow_survival"]-std["shadow_survival"])*100
                if u["shadow_survival"] is not None else None
            ),
            "standard_sl_to_shadow_plus1":std["sl_to_shadow_plus1"],
            "ultra_sl_to_shadow_plus1":u["sl_to_shadow_plus1"],
            "standard_spread_over_reaction_tr":std["median_spread_over_reaction_tr"],
            "ultra_spread_over_reaction_tr":u["median_spread_over_reaction_tr"],
            "spread_over_reaction_tr_ratio":(
                u["median_spread_over_reaction_tr"]/std["median_spread_over_reaction_tr"]
                if u["median_spread_over_reaction_tr"] is not None else None
            ),
            "standard_spread_over_risk":std["median_spread_over_risk"],
            "ultra_spread_over_risk":u["median_spread_over_risk"],
            "standard_spread_over_fvg":std["median_spread_over_fvg"],
            "ultra_spread_over_fvg":u["median_spread_over_fvg"],
        }
        rows.append(row)
    return rows

def write_comparison_csv(path:Path,rows):
    keys=list(rows[0].keys())
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

def main():
    pkg_dir=Path(__file__).resolve().parents[1] / "Trading_D154UL_ULTRA_LOW_EXECUTION_VALIDATION"
    # If installed to repo tools, benchmark is copied to tools/ as well.
    candidates=[
        Path("tools/d154ul_standard_2025_benchmark.json"),
        Path("standard_2025_benchmark.json"),
        pkg_dir/"standard_2025_benchmark.json",
    ]
    bench_path=next((p for p in candidates if p.exists()),None)
    if bench_path is None:
        raise BatchError("D154UL Standard benchmark JSON not found")
    benchmark=json.loads(bench_path.read_text(encoding="utf-8"))

    ctx=runner.discover_mt5()
    print("D154UL MT5 data dir:",ctx.data_dir)
    print("D154UL EX5:",ctx.expert_ex5)
    print("IMPORTANT: terminal must currently be logged into the Ultra Low account.")

    # Q1 parity. This also naturally triggers first history synchronization
    # for GOLD# and CADJPY# if their local tick cache is absent.
    runner.FIXED_SYMBOLS=PARITY_SYMBOLS
    runner.FIXED_FROM_DATE="2025.01.01"
    runner.FIXED_TO_DATE="2025.03.31"
    parity=runner.run_fixed_2025_batch(
        "D154UL_PARITY_GOLD_CADJPY_Q1",
        PARITY_CASES,
        symbols=PARITY_SYMBOLS,
        dry_run=False,
    )
    if parity is None:
        raise BatchError("D154UL parity returned no ZIP")
    parity=Path(parity)
    parity_check(parity)

    # Full same-year natural experiment.
    runner.FIXED_SYMBOLS=ULTRA_SYMBOLS
    runner.FIXED_FROM_DATE="2025.01.01"
    runner.FIXED_TO_DATE="2025.12.31"
    full=runner.run_fixed_2025_batch(
        "D154UL_ULTRA_LOW_2025",
        [FULL_CASE],
        symbols=ULTRA_SYMBOLS,
        dry_run=False,
    )
    if full is None:
        raise BatchError("D154UL full batch returned no ZIP")
    full=Path(full)
    summaries=verify_full(full)
    comparison=compare_to_standard(summaries,benchmark)

    temp=full.parent/"d154ul_comparison"
    temp.mkdir(parents=True,exist_ok=True)
    (temp/"ultra_low_summary.json").write_text(
        json.dumps(summaries,indent=2,ensure_ascii=False),encoding="utf-8"
    )
    (temp/"standard_benchmark.json").write_text(
        json.dumps(benchmark,indent=2,ensure_ascii=False),encoding="utf-8"
    )
    (temp/"standard_vs_ultra_low.json").write_text(
        json.dumps(comparison,indent=2,ensure_ascii=False),encoding="utf-8"
    )
    write_comparison_csv(temp/"standard_vs_ultra_low.csv",comparison)

    print("\nSTANDARD -> ULTRA LOW COMPARISON")
    for r in comparison:
        print(
            f"{r['symbol']}: spread/TR {r['standard_spread_over_reaction_tr']:.4f}"
            f" -> {r['ultra_spread_over_reaction_tr']:.4f} | "
            f"actual WR {100*r['standard_actual_survival']:.2f}%"
            f" -> {100*r['ultra_actual_survival']:.2f}% | "
            f"M flips {r['standard_sl_to_shadow_plus1']}"
            f" -> {r['ultra_sl_to_shadow_plus1']}"
        )

    desktop=runner.get_desktop_dir()
    stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    master=desktop/f"Trading_D154UL_ULTRA_LOW_2025_{stamp}.zip"
    with zipfile.ZipFile(master,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.write(parity,"parity/"+parity.name)
        z.write(full,"full/"+full.name)
        for p in temp.iterdir():
            if p.is_file():
                z.write(p,"comparison/"+p.name)

    print("\nD154UL ULTRA LOW VALIDATION COMPLETE")
    print("MASTER ZIP:",master)
    print("Send this ZIP to ChatGPT.")

if __name__=="__main__":
    try:
        main()
    except BatchError as e:
        raise SystemExit(f"ERROR: {e}")
