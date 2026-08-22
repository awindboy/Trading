import mt5_batch_runner as runner
from mt5_batch_runner import TestCase

runner.FIXED_SYMBOLS=("GOLD",)
runner.FIXED_FROM_DATE="2025.01.01"
runner.FIXED_TO_DATE="2025.03.31"

CASES=[
    TestCase(
        "D154B_OFF",
        {
            "InpExitManagementMode":9,
            "InpV2D154EntrySurvivalAudit":False,
            "InpV2D154BConfirmationAudit":False,
        },
        "V3E + D151; D154A/B shadow OFF",
    ),
    TestCase(
        "D154B_ON",
        {
            "InpExitManagementMode":9,
            "InpV2D154EntrySurvivalAudit":False,
            "InpV2D154BConfirmationAudit":True,
        },
        "D154B post-Fill confirmation shadow only",
    ),
]
if __name__=="__main__":
    runner.cli_main("D154B_PARITY_Q1_GOLD",CASES)
