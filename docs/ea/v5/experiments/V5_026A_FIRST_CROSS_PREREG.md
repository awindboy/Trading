# V5-026A First Cross Source-Reproduction Pre-registration
Status: FROZEN BEFORE OUTCOME ANALYSIS
Date: 2026-08-27

Sources: Linda Raschke Professional Trading Techniques / 3-10 oscillator materials.

Population: GOLD#, BTCUSD#, XAUEUR#, USDJPY# 2023-2025.
Signal timeframes: 15m, 30m, 60m, 120m, 1D. All reported.

Oscillator:
fast = SMA3(close) - SMA10(close)
slow = SMA16(fast)
Long regime starts on first slow cross from <=0 to >0; short reverse.
First Cross setup is the FIRST subsequent fast cross through zero opposite the slow regime while slow remains on its trend side.

Price/structure confirmation:
- Long pullback bar low must remain strictly above the reversal-regime low established since the prior slow-down regime through the slow-up cross.
- Short pullback bar high must remain strictly below the reversal-regime high established since the prior slow-up regime through the slow-down cross.
- At completion of the pullback bar, place a stop-entry one symbol point beyond that completed bar's high (long) / low (short).
- Initial stop one point beyond the pullback bar's opposite extreme.
- Cancel if slow crosses back through zero before fill or the reversal-regime extreme is invalidated.
- No stale-time threshold.

Execution: M1 first touch. If entry and stop can occur in same M1 bar after trigger and order is ambiguous, mark ambiguous and exclude from claim-grade metrics.
Round-trip spread proxy = 2 * entry-bar spread_points * point / initial risk. XAUEUR missing/zero spread remains caveated.

Frozen management families (both source-grounded, neither selected post hoc):
A. STRUCTURAL_RETEST: target = prior impulse extreme made between slow zero cross and pullback bar. Only if target lies beyond entry. Full position exits there or at initial stop.
B. EMA20_TREND: no fixed profit target; initial structural stop remains until favorable MFE >=1R, then stop is moved to breakeven. Exit at first signal-timeframe completed close across EMA20 against position, executed at next M1 open; hard stop always active. Max holding until slow line crosses zero against position, also next M1 open.

Primary final-project metrics: realized WR >50%, average positive net R >1.0R, positive cost-adjusted EV, market/year/direction stability. No threshold tuning.
