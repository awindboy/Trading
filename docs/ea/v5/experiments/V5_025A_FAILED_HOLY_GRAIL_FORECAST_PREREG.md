# V5-025A — Failed Holy Grail Forecast Diagnostic Pre-registration

Status: `PRE-REGISTERED BEFORE OUTCOME ANALYSIS`
Date: `2026-08-27`
Strategy authority: `NONE`

## Source basis

Linda Bradford Raschke stated in an Active Trader interview that a failed Holy Grail buy trade — one that
"fails to hold the moving average" — can have forecasting value to the downside and should stop the trader
from continuing to buy pullbacks. This is treated as a hypothesis source, not as evidence of expectancy.

## Population

Use only the source-corrected V5-020A Holy Grail first-attempt fills:
- original ADX/EMA setup population unchanged;
- previous completed signal-bar high/low trigger;
- actual fill timestamp/risk already frozen in V5-020A;
- 15m / 30m / 60m / 120m signal timeframes;
- GOLD#, BTCUSD#, XAUEUR#, USDJPY# 2023-2025.

## Failure-state definition

For an original LONG:
- after fill, wait for a completed signal-timeframe bar to close strictly below its causal EMA20.

For an original SHORT:
- after fill, wait for a completed signal-timeframe bar to close strictly above its causal EMA20.

A failed-Grail forecast event is recorded only if this EMA failure occurs BEFORE:
1. the original trade first reaches +1.0R MFE; and
2. the original structural -1.0R stop is touched.

The completed failure bar itself is observation only.

Forecast clock starts at the first available M1 open strictly after the failure-bar close.

No immediate stop-and-reverse assumption is made.

## Primary forecast outcomes

Failure direction = opposite the original Holy Grail direction.

From the causal forecast start, record signed log return in failure direction after:
- 1 signal bar;
- 3 signal bars;
- 6 signal bars.

Also record continuous MFE/MAE over the 6-bar horizon.

Normalize MFE/MAE by the original Holy Grail risk only as a descriptive scale; do not treat it as the future
failure-trade stop.

## Paired negative control

For every failed-Grail event, compare the same horizons from the source-corrected Holy Grail fill in the opposite
direction.

Primary question:

> Does waiting for an actual failure-to-hold-EMA observation add opposite-direction forecasting information beyond
> simply fading the original Grail fill?

This paired control prevents the ordinary pullback itself from being mislabeled as failure information.

## Required reporting

Every:
- symbol;
- year;
- original direction;
- signal timeframe.

Report:
- event count;
- median/mean signed return;
- positive-return fraction;
- paired failure-start minus fill-start forecast difference;
- MFE/MAE;
- sign stability.

## Recursive falsification

Before promotion:
- separate information observed at failure from movement already consumed before failure;
- compare with paired fill-time fade;
- check if effect is only generic mean reversion;
- check all markets/years/directions/timeframes;
- revisit V3 result that sweep/failure geometry alone often had no stable alpha.

## Gate to V5-025B

A trade-design phase may open only if:
1. 3-bar opposite signed return is positive in at least 18/24 symbol-year-direction groups for at least one
   pre-registered timeframe;
2. the paired improvement over fill-time fade has the same sign in at least 18/24 groups;
3. 1-bar and 6-bar horizons do not materially reverse the relationship;
4. no one market/year is required.

If no timeframe passes, close the hypothesis without threshold rescue.
