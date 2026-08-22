import mt5_batch_runner as runner
from mt5_batch_runner import TestCase

runner.FIXED_SYMBOLS=("GOLD",)
runner.FIXED_FROM_DATE="2025.01.01"
runner.FIXED_TO_DATE="2025.03.31"

CASES=[
    TestCase(
        "D154C_OFF",
        {
            "InpExitManagementMode":9,
            "InpV2D154EntrySurvivalAudit":False,
            "InpV2D154BConfirmationAudit":False,
            "InpV2D154CReaccelerationFvgAudit":False,
        },
        "V3E + D151; D154A/B/C shadow OFF",
    ),
    TestCase(
        "D154C_ON",
        {
            "InpExitManagementMode":9,
            "InpV2D154EntrySurvivalAudit":False,
            "InpV2D154BConfirmationAudit":False,
            "InpV2D154CReaccelerationFvgAudit":True,
        },
        "D154C first post-confirmation same-dir FVG retest shadow",
    ),
]
if __name__=="__main__":
    runner.cli_main("D154C_PARITY_Q1_GOLD",CASES)
