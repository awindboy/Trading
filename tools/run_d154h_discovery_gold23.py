from __future__ import annotations
import argparse,sys
import mt5_batch_runner as runner
from mt5_batch_runner import TestCase,BatchError

# Clean prefix: known 2023-12-22 broker market-closed cancel fault is excluded.
runner.FIXED_FROM_DATE="2023.01.01"
runner.FIXED_TO_DATE="2023.12.21"

CASE=TestCase(
    "D154H_HTF_NESTED_CAUSAL_REPLAY_DISCOVERY",
    {
        "InpExitManagementMode":9,
        "InpEpisodeManagementMode":0,
        "InpV2D151CausalAudit":True,
        "InpV2D154EntrySurvivalAudit":False,
        "InpV2D154BConfirmationAudit":False,
        "InpV2D154CReaccelerationFvgAudit":False,
        "InpV2D154FCausalLineageAudit":False,
        "InpV2D154GHTFRootLineageAudit":False,
        "InpV2D154HHTFNestedReplayAudit":True,
    },
    "Discovery census only: ordered H1/M30 structure events from PLAN to actual Fill",
)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--dry-run",action="store_true"); args=ap.parse_args()
    try:
        runner.run_fixed_2025_batch("D154H_HTF_NESTED_CAUSAL_REPLAY_DISCOVERY_GOLD23",[CASE],symbols=("GOLD",),dry_run=args.dry_run)
    except BatchError as e:
        print(f"\nERROR: {e}",file=sys.stderr); return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
