from mt5_batch_runner import TestCase,cli_main

CASES=[
    TestCase(
        "D154C_REACCELERATION_FVG_SHADOW",
        {
            "InpExitManagementMode":9,
            "InpV2D154EntrySurvivalAudit":False,
            "InpV2D154BConfirmationAudit":False,
            "InpV2D154CReaccelerationFvgAudit":True,
        },
        "Transition Fill -> first same-dir INITIAL_BOS -> first post-confirmation same-dir FVG -> first retest shadow",
    ),
]
if __name__=="__main__":
    cli_main("D154C_REACCELERATION_FVG_SHADOW",CASES)
