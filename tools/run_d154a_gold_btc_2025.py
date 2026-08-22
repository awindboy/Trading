from mt5_batch_runner import TestCase,cli_main
CASES=[
    TestCase(
        "D154A_OWNERSHIP_AUDIT",
        {"InpExitManagementMode":9,"InpV2D154EntrySurvivalAudit":True},
        "M1 CHoCH transition -> owner completion and post-SL Root succession shadow audit",
    ),
]
if __name__=="__main__":
    cli_main("D154A_ENTRY_SURVIVAL",CASES)
