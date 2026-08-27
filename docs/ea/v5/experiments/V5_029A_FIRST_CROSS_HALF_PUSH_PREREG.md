# V5-029A First Cross — Half Off and Push Runner
Status: FROZEN BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent setup: exact V5-028A First Cross 240m candidate; entry/stop/population unchanged.

Source basis: Raschke Professional Trading Techniques states that when managing trades, a good rule is to take half off and “push” the other half; profitable trades should be followed with protective stops and large favorable trades should not be closed without reason.

Frozen management:
- Initial risk = structural V5-028A stop.
- No full-position 1R exit.
- When price first reaches +1.0R before initial stop, exit exactly 50% at +1R and move the remaining 50% stop to entry (breakeven).
- Runner objective = the same prior impulse structural extreme frozen at entry.
- If structural objective lies <= +1R, exit the whole position at that structural objective; do not manufacture a farther target.
- If runner returns to entry after +1R partial, total gross outcome = +0.5R.
- If runner reaches structural objective after +1R partial, gross outcome = 0.5*1R + 0.5*targetR.
- If initial stop occurs before +1R, gross outcome = -1R.
- Conservative same-M1 ambiguity exclusion.
- Round-trip spread proxy applied to the whole original unit exactly once.

No setup filtering, no target-room threshold, no timeframe change, no parameter search.
Final metrics: realized net-positive WR >=50%, avg positive net R meaningfully >1R, positive cost-adjusted EV, market/year stability.
