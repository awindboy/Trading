from __future__ import annotations
import argparse
import datetime as dt
from pathlib import Path
import zipfile

import mt5_batch_runner as runner
from mt5_batch_runner import TestCase, BatchError

CELLS=[
    ("GOLD23","GOLD","2023.01.01","2023.12.31"),
    ("GOLD24","GOLD","2024.01.01","2024.12.31"),
    ("SILVER25","SILVER","2025.01.01","2025.12.31"),
    ("CADJPY25","CADJPY","2025.01.01","2025.12.31"),
]

CASE=TestCase(
    "D154D_SOURCE_SUCCESSION_OOS",
    {
        "InpExitManagementMode":9,
        "InpV2D154EntrySurvivalAudit":True,
        "InpV2D154BConfirmationAudit":False,
        "InpV2D154CReaccelerationFvgAudit":False,
    },
    "OOS validation of D154A post-SL other-root vs root-created-after-failure source succession",
)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()

    cell_zips=[]
    for cell,symbol,date_from,date_to in CELLS:
        print("\n============================================================")
        print(f"D154D OOS CELL: {cell} {symbol} {date_from}..{date_to}")
        print("============================================================")
        runner.FIXED_SYMBOLS=(symbol,)
        runner.FIXED_FROM_DATE=date_from
        runner.FIXED_TO_DATE=date_to
        z=runner.run_fixed_2025_batch(
            f"D154D_SOURCE_SUCCESSION_OOS_{cell}",
            [CASE],
            symbols=(symbol,),
            dry_run=args.dry_run,
        )
        if z is not None:
            cell_zips.append((cell,Path(z)))

    if args.dry_run:
        print("\nD154D dry-run complete.")
        return

    desktop=runner.get_desktop_dir()
    stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    master=desktop/f"Trading_D154D_SOURCE_SUCCESSION_OOS_{stamp}.zip"
    with zipfile.ZipFile(master,"w",compression=zipfile.ZIP_DEFLATED) as out:
        for cell,zp in cell_zips:
            out.write(zp,f"{cell}/{zp.name}")
    print("\n============================================================")
    print("D154D OOS MASTER COMPLETE")
    print("ZIP:",master)
    print("Send this master ZIP to ChatGPT.")
    print("============================================================")

if __name__=="__main__":
    try:
        main()
    except BatchError as e:
        raise SystemExit(f"ERROR: {e}")
