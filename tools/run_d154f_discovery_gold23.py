import mt5_batch_runner as runner
from mt5_batch_runner import TestCase

runner.FIXED_SYMBOLS=("GOLD",)
runner.FIXED_FROM_DATE="2023.01.01"
runner.FIXED_TO_DATE="2023.12.31"

CASES=[
    TestCase(
        "D154F_CAUSAL_LINEAGE_DISCOVERY",
        {
            "InpExitManagementMode":9,
            "InpV2D154EntrySurvivalAudit":False,
            "InpV2D154BConfirmationAudit":False,
            "InpV2D154CReaccelerationFvgAudit":False,
            "InpV2D154FCausalLineageAudit":True,
        },
        "Discovery only: sequence-only vs same-reaction lineage on GOLD 2023",
    ),
]

if __name__=="__main__":
    runner.cli_main("D154F_CAUSAL_LINEAGE_DISCOVERY_GOLD23",CASES)
