import mt5_batch_runner as runner
from mt5_batch_runner import TestCase

runner.FIXED_SYMBOLS=("GOLD",)
runner.FIXED_FROM_DATE="2025.01.01"
runner.FIXED_TO_DATE="2025.03.31"

CASES=[
    TestCase("D154A_OFF",{"InpExitManagementMode":9,"InpV2D154EntrySurvivalAudit":False},"Parity control: V3E + D151 ON + D154A OFF"),
    TestCase("D154A_ON",{"InpExitManagementMode":9,"InpV2D154EntrySurvivalAudit":True},"Shadow ownership/succession audit only"),
]
if __name__=="__main__":
    runner.cli_main("D154A_PARITY_Q1_GOLD",CASES)
