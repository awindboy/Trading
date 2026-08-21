from mt5_batch_runner import TestCase, cli_main

# D-152 isolated SP comparison.
# The stable runner automatically executes every case on:
#   GOLD   2025.01.01 -> 2025.12.31
#   BTCUSD 2025.01.01 -> 2025.12.31
# with M1 / Every tick based on real ticks / EM OFF / D151 audit ON.
#
# Current V2 enum identities:
#   4 = SMART_PARTIAL_V2 parent control
#   5 = V3A KNOWN_DEFAULT_CLOSE
#   6 = V3B PROFIT_BANK
#   7 = V3C BANK_3R_LOCK
#   8 = V3D STRUCTURAL_BANK
#   9 = V3E BANK_2R_LOCK_ONE

CASES = [
    TestCase(
        "CTRL_SP_V2",
        {"InpExitManagementMode": 4},
        "Parent control: SP V2 +2R cost-adjusted BE",
    ),
    TestCase(
        "V3A_KNOWN_DEFAULT_CLOSE",
        {"InpExitManagementMode": 5},
        "Known-range DEFAULT full close at +1R; STRONG unchanged",
    ),
    TestCase(
        "V3B_PROFIT_BANK",
        {"InpExitManagementMode": 6},
        "+2R minimum realized-profit bank, residual original SL/structural TP",
    ),
    TestCase(
        "V3C_BANK_3R_LOCK",
        {"InpExitManagementMode": 7},
        "+2R small bank then +3R meaningful +1R fallback bank",
    ),
    TestCase(
        "V3D_STRUCTURAL_BANK",
        {"InpExitManagementMode": 8},
        "+2R bank size selected from causal current-M30 room",
    ),
    TestCase(
        "V3E_BANK_2R_LOCK_ONE",
        {"InpExitManagementMode": 9},
        "+2R aggressive realized bank targeting >=+1.05R original-SL fallback",
    ),
]

if __name__ == "__main__":
    cli_main("D152_SP_V3", CASES)
