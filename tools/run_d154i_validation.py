from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import zipfile

import mt5_batch_runner as runner
from mt5_batch_runner import TestCase, BatchError


# Frozen validation panel. No market-specific changes.
CELLS = [
    ("GOLD24", "GOLD", "2024.01.01", "2024.12.31"),
    ("GOLD25", "GOLD", "2025.01.01", "2025.12.31"),
    ("BTC25", "BTCUSD", "2025.01.01", "2025.12.31"),
    ("SILVER25", "SILVER", "2025.01.01", "2025.12.31"),
    ("CADJPY25", "CADJPY", "2025.01.01", "2025.12.31"),
]

CASE = TestCase(
    "D154I_POST_CONTACT_HTF_DELIVERY_VALIDATION",
    {
        "InpExitManagementMode": 9,
        "InpEpisodeManagementMode": 0,
        "InpV2D151CausalAudit": True,
        "InpV2D154EntrySurvivalAudit": False,
        "InpV2D154BConfirmationAudit": False,
        "InpV2D154CReaccelerationFvgAudit": False,
        "InpV2D154FCausalLineageAudit": False,
        "InpV2D154GHTFRootLineageAudit": False,
        "InpV2D154HHTFNestedReplayAudit": True,
    },
    "Frozen OOS validation of post-Root-contact same-direction H1/M30 BOS before accepted CHoCH",
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cell_zips: list[tuple[str, Path]] = []

    for cell, symbol, date_from, date_to in CELLS:
        print("\n============================================================")
        print(f"D154I VALIDATION CELL: {cell} {symbol} {date_from}..{date_to}")
        print("============================================================")

        runner.FIXED_SYMBOLS = (symbol,)
        runner.FIXED_FROM_DATE = date_from
        runner.FIXED_TO_DATE = date_to

        z = runner.run_fixed_2025_batch(
            f"D154I_POST_CONTACT_HTF_DELIVERY_VALIDATION_{cell}",
            [CASE],
            symbols=(symbol,),
            dry_run=args.dry_run,
        )
        if z is not None:
            cell_zips.append((cell, Path(z)))

    if args.dry_run:
        print("\nD154I validation dry-run complete.")
        return

    desktop = runner.get_desktop_dir()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    master = desktop / f"Trading_D154I_POST_CONTACT_HTF_DELIVERY_VALIDATION_{stamp}.zip"

    with zipfile.ZipFile(master, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for cell, zp in cell_zips:
            out.write(zp, f"{cell}/{zp.name}")

    print("\nD154I VALIDATION MASTER COMPLETE")
    print("ZIP:", master)
    print("Send this ZIP to ChatGPT.")


if __name__ == "__main__":
    try:
        main()
    except BatchError as e:
        raise SystemExit(f"ERROR: {e}")
