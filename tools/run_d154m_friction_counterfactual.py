from __future__ import annotations
import csv
import datetime as dt
import io
import json
import os
import re
import zipfile
from pathlib import Path

STATE=Path("tools/.d154m_compile_state.json")
if not STATE.exists():
    raise SystemExit("ERROR: tools/.d154m_compile_state.json missing. Apply D154M package and verify compile first.")

state=json.loads(STATE.read_text(encoding="utf-8"))
os.environ["MT5_DATA_DIR"]=state["data_dir"]
os.environ["MT5_TERMINAL_EXE"]=state["terminal_exe"]

import mt5_batch_runner as runner
from mt5_batch_runner import TestCase, BatchError

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
    "InpV2D154KCrossScaleReactionAudit":False,
}

PARITY_SYMBOLS=("GOLD","CADJPY")
PARITY_CASES=[
    TestCase("D154M_OFF",{**BASE_SETTINGS,"InpV2D154MExecutionFrictionCounterfactualAudit":False},
             "D154M OFF parity control"),
    TestCase("D154M_ON",{**BASE_SETTINGS,"InpV2D154MExecutionFrictionCounterfactualAudit":True},
             "D154M same-entry-side quote shadow ON"),
]

CELLS=[
    ("GOLD23","GOLD","2023.01.01","2023.12.21"),
    ("GOLD24","GOLD","2024.01.01","2024.12.31"),
    ("GOLD25","GOLD","2025.01.01","2025.12.31"),
    ("BTC25","BTCUSD","2025.01.01","2025.12.31"),
    ("SILVER25","SILVER","2025.01.01","2025.12.31"),
    ("CADJPY25","CADJPY","2025.01.01","2025.12.31"),
]

FULL_CASE=TestCase(
    "D154M_COUNTERFACTUAL",
    {**BASE_SETTINGS,"InpV2D154MExecutionFrictionCounterfactualAudit":True},
    "Actual D151 executable-side barrier race vs entry-side quote counterfactual",
)

def rows_from_zip(zp:Path):
    out={}
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            if n.endswith(".csv"):
                out[n]=list(csv.DictReader(io.StringIO(z.read(n).decode("utf-8-sig",errors="replace"))))
    return out

def canonical(rows):
    out=[]
    for r in rows:
        if r.get("event","").startswith("D154M_"):
            continue
        d=dict(r)
        detail=d.get("detail","")
        detail=re.sub(r"csv_rows_written=\d+","csv_rows_written=<NORMALIZED>",detail)
        detail=re.sub(r"log_calls_suppressed=\d+","log_calls_suppressed=<NORMALIZED>",detail)
        d["detail"]=detail
        out.append(tuple(d.get(k,"") for k in
                         ("observed_at","event","timeframe","available_at","object_id","detail")))
    return out

def parity_check(zp:Path)->None:
    files=rows_from_zip(zp)
    for sym in PARITY_SYMBOLS:
        off=[(n,r) for n,r in files.items() if "__D154M_OFF__"+sym+"__" in n]
        on=[(n,r) for n,r in files.items() if "__D154M_ON__"+sym+"__" in n]
        if len(off)!=1 or len(on)!=1:
            raise BatchError(f"{sym}: parity CSV discovery failed OFF={len(off)} ON={len(on)}")
        _,offr=off[0]; _,onr=on[0]
        if any(r.get("event","").startswith("D154M_") for r in offr):
            raise BatchError(f"{sym}: D154M rows present in OFF run")
        a,b=canonical(offr),canonical(onr)
        if a!=b:
            msg=f"{sym}: D154M NON-INTERFERENCE PARITY FAIL OFF={len(a)} ON={len(b)}"
            for i,(x,y) in enumerate(zip(a,b)):
                if x!=y:
                    msg+=f" first_diff_index={i} OFF={x} ON={y}"
                    break
            raise BatchError(msg)

        events=[r.get("event","") for r in onr]
        starts=events.count("D154M_RESEARCH_START")
        stops=events.count("D154M_RESEARCH_STOP")
        fills=events.count("D154M_FILL_SNAPSHOT")
        pairs=events.count("D154M_PAIR_OUTCOME")
        if starts!=1 or stops!=1 or fills<=0 or pairs!=fills:
            raise BatchError(
                f"{sym}: D154M ON completeness fail start={starts} stop={stops} fills={fills} pairs={pairs}"
            )
        if "D154M_INTEGRITY_WARNING" in events:
            raise BatchError(f"{sym}: D154M integrity warning present in parity ON run")
        print(f"{sym}: D154M NON-INTERFERENCE PARITY PASS | canonical_rows={len(a)} | fills={fills} pairs={pairs}")

def verify_cell(zp:Path,cell:str,symbol:str)->None:
    files=rows_from_zip(zp)
    if len(files)!=1:
        raise BatchError(f"{cell}: expected exactly one CSV, found {len(files)}")
    _,rows=next(iter(files.items()))
    events=[r.get("event","") for r in rows]
    if events.count("D154M_RESEARCH_START")!=1 or events.count("D154M_RESEARCH_STOP")!=1:
        raise BatchError(f"{cell}: D154M start/stop missing")
    fills=events.count("D154M_FILL_SNAPSHOT")
    pairs=events.count("D154M_PAIR_OUTCOME")
    actual=events.count("D154M_ACTUAL_OUTCOME")
    if fills<=0 or pairs!=fills or actual>fills:
        raise BatchError(f"{cell}: D154M completeness fail fills={fills} pairs={pairs} actual_rows={actual}")
    if "D154M_INTEGRITY_WARNING" in events:
        raise BatchError(f"{cell}: D154M integrity warning present")
    if "EXECUTION_DIVERGENCE" in events or "PENDING_CANCEL_REJECTED" in events:
        raise BatchError(f"{cell}: execution integrity failure")
    print(f"{cell}: PASS | {symbol} fills={fills} pairs={pairs}")

def main():
    # Q1 dual-symbol non-interference parity first.
    runner.FIXED_SYMBOLS=PARITY_SYMBOLS
    runner.FIXED_FROM_DATE="2025.01.01"
    runner.FIXED_TO_DATE="2025.03.31"
    parity=runner.run_fixed_2025_batch(
        "D154M_PARITY_GOLD_CADJPY25_Q1",
        PARITY_CASES,
        symbols=PARITY_SYMBOLS,
        dry_run=False,
    )
    if parity is None:
        raise BatchError("parity batch returned no ZIP")
    parity=Path(parity)
    parity_check(parity)

    outputs=[]
    for cell,symbol,date_from,date_to in CELLS:
        print("\n============================================================")
        print(f"D154M CELL {cell}: {symbol} {date_from}..{date_to}")
        print("============================================================")
        runner.FIXED_SYMBOLS=(symbol,)
        runner.FIXED_FROM_DATE=date_from
        runner.FIXED_TO_DATE=date_to
        z=runner.run_fixed_2025_batch(
            f"D154M_{cell}",
            [FULL_CASE],
            symbols=(symbol,),
            dry_run=False,
        )
        if z is None:
            raise BatchError(f"{cell}: no ZIP returned")
        z=Path(z)
        verify_cell(z,cell,symbol)
        outputs.append((cell,z))

    desktop=runner.get_desktop_dir()
    stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    master=desktop/f"Trading_D154M_EXECUTION_FRICTION_COUNTERFACTUAL_{stamp}.zip"
    with zipfile.ZipFile(master,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.write(parity,"parity/"+parity.name)
        for cell,p in outputs:
            z.write(p,f"{cell}/{p.name}")

    print("\nD154M EXECUTION-FRICTION COUNTERFACTUAL COMPLETE")
    print("MASTER ZIP:",master)
    print("Send this ZIP to ChatGPT.")

if __name__=="__main__":
    try:
        main()
    except BatchError as e:
        raise SystemExit(f"ERROR: {e}")
