import mt5_batch_runner as runner
from mt5_batch_runner import TestCase

runner.FIXED_SYMBOLS=("GOLD",)
runner.FIXED_FROM_DATE="2023.01.01"
runner.FIXED_TO_DATE="2023.03.31"

CASES=[
    TestCase(
        "D154F_OFF",
        {
            "InpExitManagementMode":9,
            "InpV2D154EntrySurvivalAudit":False,
            "InpV2D154BConfirmationAudit":False,
            "InpV2D154CReaccelerationFvgAudit":False,
            "InpV2D154FCausalLineageAudit":False,
        },
        "V3E reference + D151; D154F OFF",
    ),
    TestCase(
        "D154F_ON",
        {
            "InpExitManagementMode":9,
            "InpV2D154EntrySurvivalAudit":False,
            "InpV2D154BConfirmationAudit":False,
            "InpV2D154CReaccelerationFvgAudit":False,
            "InpV2D154FCausalLineageAudit":True,
        },
        "D154F causal-lineage shadow ON",
    ),
]

if __name__=="__main__":
    runner.cli_main("D154F_PARITY_GOLD23_Q1",CASES)
