from __future__ import annotations
import argparse,datetime as dt
from pathlib import Path
import zipfile
import mt5_batch_runner as runner
from mt5_batch_runner import TestCase,BatchError

# PRE-REGISTERED validation panel. Do not run until GOLD23 discovery is reviewed.
CELLS=[
    ("GOLD24","GOLD","2024.01.01","2024.12.31"),
    ("GOLD25","GOLD","2025.01.01","2025.12.31"),
    ("BTC25","BTCUSD","2025.01.01","2025.12.31"),
    ("SILVER25","SILVER","2025.01.01","2025.12.31"),
    ("CADJPY25","CADJPY","2025.01.01","2025.12.31"),
]
CASE=TestCase(
    "D154G_HTF_ROOT_LINEAGE_VALIDATION",
    {
        "InpExitManagementMode":9,
        "InpV2D154EntrySurvivalAudit":False,
        "InpV2D154BConfirmationAudit":False,
        "InpV2D154CReaccelerationFvgAudit":False,
        "InpV2D154FCausalLineageAudit":False,
        "InpV2D154GHTFRootLineageAudit":True,
    },
    "Pre-registered OOS validation; stale definition frozen before validation",
)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dry-run",action="store_true"); args=ap.parse_args()
    cell_zips=[]
    for cell,symbol,date_from,date_to in CELLS:
        print("\n============================================================")
        print(f"D154G VALIDATION CELL: {cell} {symbol} {date_from}..{date_to}")
        print("============================================================")
        # Stable runner's allow-list is intentionally narrow; explicit symbols are
        # still passed, and this wrapper temporarily admits only the current cell.
        runner.FIXED_SYMBOLS=(symbol,)
        runner.FIXED_FROM_DATE=date_from; runner.FIXED_TO_DATE=date_to
        z=runner.run_fixed_2025_batch(f"D154G_HTF_ROOT_LINEAGE_VALIDATION_{cell}",[CASE],symbols=(symbol,),dry_run=args.dry_run)
        if z is not None: cell_zips.append((cell,Path(z)))
    if args.dry_run:
        print("\nD154G validation dry-run complete."); return
    desktop=runner.get_desktop_dir(); stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    master=desktop/f"Trading_D154G_HTF_ROOT_LINEAGE_VALIDATION_{stamp}.zip"
    with zipfile.ZipFile(master,"w",compression=zipfile.ZIP_DEFLATED) as out:
        for cell,zp in cell_zips: out.write(zp,f"{cell}/{zp.name}")
    print("\nD154G VALIDATION MASTER COMPLETE\nZIP:",master,"\nSend this ZIP to ChatGPT.")
if __name__=="__main__":
    try: main()
    except BatchError as e: raise SystemExit(f"ERROR: {e}")
