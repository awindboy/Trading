from __future__ import annotations

import argparse
import sys

import mt5_batch_runner as runner
from mt5_batch_runner import TestCase, BatchError


runner.FIXED_FROM_DATE = "2023.01.01"
runner.FIXED_TO_DATE = "2023.03.31"


CASES = [
    TestCase(
        "D154F_OFF",
        {
            "InpExitManagementMode": 9,
            "InpV2D154EntrySurvivalAudit": False,
            "InpV2D154BConfirmationAudit": False,
            "InpV2D154CReaccelerationFvgAudit": False,
            "InpV2D154FCausalLineageAudit": False,
        },
        "V3E reference + D151; D154F OFF",
    ),
    TestCase(
        "D154F_ON",
        {
            "InpExitManagementMode": 9,
            "InpV2D154EntrySurvivalAudit": False,
            "InpV2D154BConfirmationAudit": False,
            "InpV2D154CReaccelerationFvgAudit": False,
            "InpV2D154FCausalLineageAudit": True,
        },
        "D154F causal-lineage shadow ON",
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        runner.run_fixed_2025_batch(
            "D154F_PARITY_GOLD23_Q1",
            CASES,
            symbols=("GOLD",),
            dry_run=args.dry_run,
        )
    except BatchError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())