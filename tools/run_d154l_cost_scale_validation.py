from __future__ import annotations
import csv, io, zipfile, datetime as dt
from pathlib import Path
import mt5_batch_runner as runner
from mt5_batch_runner import TestCase, BatchError

CELLS=[
    # Historical context only: previous GOLD23 discovery window.
    ("GOLD23_CONTEXT","GOLD","2023.01.01","2023.12.21"),
    # Frozen validation cells for the D154K cost-scale hypothesis.
    ("GOLD24_VALIDATION","GOLD","2024.01.01","2024.12.31"),
    ("BTC25_VALIDATION","BTCUSD","2025.01.01","2025.12.31"),
    ("SILVER25_VALIDATION","SILVER","2025.01.01","2025.12.31"),
]

CASE=TestCase(
    "D154L_COST_SCALE",
    {
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
        "InpV2D154KCrossScaleReactionAudit":True,
    },
    "Frozen transfer validation of execution cost relative to causal M1 reaction scale",
)

def verify_zip(zp:Path,cell:str,symbol:str)->None:
    with zipfile.ZipFile(zp) as z:
        csvs=[n for n in z.namelist() if n.endswith(".csv")]
        if len(csvs)!=1:
            raise BatchError(f"{cell}: expected 1 CSV, found {len(csvs)}")
        rows=list(csv.DictReader(io.StringIO(z.read(csvs[0]).decode("utf-8-sig",errors="replace"))))
    events=[r.get("event","") for r in rows]
    if "D154K_RESEARCH_START" not in events or "D154K_RESEARCH_STOP" not in events:
        raise BatchError(f"{cell}: D154K start/stop missing")
    snaps=sum(e=="D154K_CROSS_SCALE_SNAPSHOT" for e in events)
    outs=sum(e=="D154K_PRIMARY_OUTCOME" for e in events)
    fills=sum(e=="D151_FILL_SNAPSHOT" for e in events)
    if snaps<=0 or snaps!=outs or snaps!=fills:
        raise BatchError(f"{cell}: D154K completeness fail fills={fills} snapshots={snaps} outcomes={outs}")
    if "EXECUTION_DIVERGENCE" in events or "PENDING_CANCEL_REJECTED" in events:
        raise BatchError(f"{cell}: execution integrity failure")
    print(f"{cell}: PASS | {symbol} fills={fills} D154K_snapshots={snaps}")

def main():
    outputs=[]
    for cell,symbol,date_from,date_to in CELLS:
        print("\n============================================================")
        print(f"D154L CELL {cell}: {symbol} {date_from}..{date_to}")
        print("============================================================")
        runner.FIXED_SYMBOLS=(symbol,)
        runner.FIXED_FROM_DATE=date_from
        runner.FIXED_TO_DATE=date_to
        z=runner.run_fixed_2025_batch(
            f"D154L_{cell}",
            [CASE],
            symbols=(symbol,),
            dry_run=False,
        )
        if z is None:
            raise BatchError(f"{cell}: no ZIP returned")
        z=Path(z)
        verify_zip(z,cell,symbol)
        outputs.append((cell,z))

    desktop=runner.get_desktop_dir()
    stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    master=desktop/f"Trading_D154L_COST_SCALE_TRANSFER_VALIDATION_{stamp}.zip"
    with zipfile.ZipFile(master,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for cell,p in outputs:
            z.write(p,f"{cell}/{p.name}")
    print("\nD154L COST-SCALE TRANSFER VALIDATION COMPLETE")
    print("MASTER ZIP:",master)
    print("Send this ZIP to ChatGPT.")

if __name__=="__main__":
    try:
        main()
    except BatchError as e:
        raise SystemExit(f"ERROR: {e}")
