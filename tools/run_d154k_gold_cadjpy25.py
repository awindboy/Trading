from __future__ import annotations
import csv, io, re, zipfile, datetime as dt
from pathlib import Path
import mt5_batch_runner as runner
from mt5_batch_runner import TestCase, BatchError

SYMBOLS=("GOLD","CADJPY")
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
    TestCase("D154K_OFF",{**BASE_SETTINGS,"InpV2D154KCrossScaleReactionAudit":False},"D154K OFF parity control"),
    TestCase("D154K_ON",{**BASE_SETTINGS,"InpV2D154KCrossScaleReactionAudit":True},"D154K shadow ON"),
]
FULL_CASES=[
    TestCase("D154K_CROSS_SCALE",{**BASE_SETTINGS,"InpV2D154KCrossScaleReactionAudit":True},
             "GOLD25 vs CADJPY25 Root-reaction/local-noise scale contrast"),
]

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
        if r.get("event","").startswith("D154K_"):
            continue
        d=dict(r)
        d["detail"]=re.sub(r"csv_rows_written=\d+","csv_rows_written=<NORMALIZED>",d.get("detail",""))
        out.append(tuple(d.get(k,"") for k in ("observed_at","event","timeframe","available_at","object_id","detail")))
    return out

def parity_check(zp:Path):
    files=rows_from_zip(zp)
    for sym in SYMBOLS:
        off=[(n,r) for n,r in files.items() if "__D154K_OFF__"+sym+"__" in n]
        on=[(n,r) for n,r in files.items() if "__D154K_ON__"+sym+"__" in n]
        if len(off)!=1 or len(on)!=1:
            raise BatchError(f"{sym}: parity CSV discovery failed OFF={len(off)} ON={len(on)}")
        _,offr=off[0]; _,onr=on[0]
        if any(r.get("event","").startswith("D154K_") for r in offr):
            raise BatchError(f"{sym}: D154K rows present in OFF run")
        a,b=canonical(offr),canonical(onr)
        if a!=b:
            msg=f"{sym}: D154K NON-INTERFERENCE PARITY FAIL OFF={len(a)} ON={len(b)}"
            for i,(x,y) in enumerate(zip(a,b)):
                if x!=y:
                    msg+=f" first_diff_index={i} OFF={x} ON={y}"
                    break
            raise BatchError(msg)
        on_rows=sum(r.get("event","").startswith("D154K_") for r in onr)
        if on_rows<=0:
            raise BatchError(f"{sym}: D154K_ON_EMITTED_ZERO_ROWS; tester is not running the expected compact-logger build")
        print(f"{sym}: D154K NON-INTERFERENCE PARITY PASS | canonical_rows={len(a)} | d154k_on_rows={on_rows}")

def main():
    runner.FIXED_SYMBOLS=SYMBOLS
    runner.FIXED_FROM_DATE="2025.01.01"
    runner.FIXED_TO_DATE="2025.03.31"
    parity=runner.run_fixed_2025_batch("D154K_PARITY_GOLD_CADJPY25_Q1",PARITY_CASES,symbols=SYMBOLS,dry_run=False)
    if parity is None:
        raise BatchError("parity batch returned no ZIP")
    parity=Path(parity)
    parity_check(parity)

    runner.FIXED_SYMBOLS=SYMBOLS
    runner.FIXED_FROM_DATE="2025.01.01"
    runner.FIXED_TO_DATE="2025.12.31"
    full=runner.run_fixed_2025_batch("D154K_CROSS_SCALE_GOLD_CADJPY25",FULL_CASES,symbols=SYMBOLS,dry_run=False)
    if full is None:
        raise BatchError("full cross-scale batch returned no ZIP")
    full=Path(full)

    desktop=runner.get_desktop_dir()
    stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    master=desktop/f"Trading_D154K_GOLD_CADJPY25_{stamp}.zip"
    with zipfile.ZipFile(master,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.write(parity,"parity/"+parity.name)
        z.write(full,"cross_scale/"+full.name)
    print("\nD154K GOLD25 + CADJPY25 COMPLETE")
    print("MASTER ZIP:",master)
    print("Send this ZIP to ChatGPT.")

if __name__=="__main__":
    try:
        main()
    except BatchError as e:
        raise SystemExit(f"ERROR: {e}")
