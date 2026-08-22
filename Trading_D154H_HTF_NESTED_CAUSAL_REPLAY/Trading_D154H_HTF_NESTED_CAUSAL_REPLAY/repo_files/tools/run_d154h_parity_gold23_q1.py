from __future__ import annotations
import argparse,sys
import mt5_batch_runner as runner
from mt5_batch_runner import TestCase,BatchError

runner.FIXED_FROM_DATE="2023.01.01"
runner.FIXED_TO_DATE="2023.03.31"

COMMON={
    "InpExitManagementMode":9,
    "InpEpisodeManagementMode":0,
    "InpV2D151CausalAudit":True,
    "InpV2D154EntrySurvivalAudit":False,
    "InpV2D154BConfirmationAudit":False,
    "InpV2D154CReaccelerationFvgAudit":False,
    "InpV2D154FCausalLineageAudit":False,
    "InpV2D154GHTFRootLineageAudit":False,
}
CASES=[
    TestCase("D154H_OFF",{**COMMON,"InpV2D154HHTFNestedReplayAudit":False},"V3E + D151; D154H OFF"),
    TestCase("D154H_ON",{**COMMON,"InpV2D154HHTFNestedReplayAudit":True},"D154H HTF nested causal replay ON"),
]

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--dry-run",action="store_true"); args=ap.parse_args()
    try:
        runner.run_fixed_2025_batch("D154H_PARITY_GOLD23_Q1",CASES,symbols=("GOLD",),dry_run=args.dry_run)
    except BatchError as e:
        print(f"\nERROR: {e}",file=sys.stderr); return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
