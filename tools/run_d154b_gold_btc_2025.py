from mt5_batch_runner import TestCase,cli_main

CASES=[
    TestCase(
        "D154B_CONFIRMATION_SHADOW",
        {
            "InpExitManagementMode":9,
            "InpV2D154EntrySurvivalAudit":False,
            "InpV2D154BConfirmationAudit":True,
        },
        "Transition-at-Fill -> first same-direction M1 INITIAL_BOS -> delayed executable shadow entry",
    ),
]
if __name__=="__main__":
    cli_main("D154B_CONFIRMATION_SHADOW",CASES)
