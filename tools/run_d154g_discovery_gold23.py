from __future__ import annotations
import argparse,sys
import mt5_batch_runner as runner
from mt5_batch_runner import TestCase,BatchError

# Clean GOLD23 discovery window. 2023-12-22 is excluded because the broker's
# known market-closed pending-cancel fault dirties the ledger. Right-censoring
# at 2023-12-21 is preserved rather than imputed.
runner.FIXED_FROM_DATE="2023.01.01"
runner.FIXED_TO_DATE="2023.12.21"
CASE=TestCase(
    "D154G_HTF_ROOT_LINEAGE_DISCOVERY",
    {
        "InpExitManagementMode":9,
        "InpV2D154EntrySurvivalAudit":False,
        "InpV2D154BConfirmationAudit":False,
        "InpV2D154CReaccelerationFvgAudit":False,
        "InpV2D154FCausalLineageAudit":False,
        "InpV2D154GHTFRootLineageAudit":True,
    },
    "Discovery: stale prior same-TF map owner in actual-fill Root contributors",
)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--dry-run",action="store_true"); args=ap.parse_args()
    try:
        runner.run_fixed_2025_batch("D154G_HTF_ROOT_LINEAGE_DISCOVERY_GOLD23",[CASE],symbols=("GOLD",),dry_run=args.dry_run)
    except BatchError as e:
        print(f"\nERROR: {e}",file=sys.stderr); return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
