# V5-006C — Holy Grail Partial-Target + EMA20 Runner Pre-registration

Status: PRE-REGISTERED BEFORE RUNNER OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-006B entry/initial-target mechanism

V5-006B has a reproducible >50% probability of reaching the published recent-swing retest before the structural stop
on most market/year/direction groups, but target payoff is often below 1R and Level-A costs erase expectancy.

This phase tests the published idea of taking partial profit at the recent extreme and retaining a runner.

## Frozen exit architecture

Loser:
- structural stop before recent-swing target = -1R gross.

Winner:
1. Exit exactly 50% at the published recent-swing target.
2. On the remaining 50%, immediately move the structural stop to the original entry trigger (0R gross).
3. Hold the runner until the first completed signal-timeframe bar closes through EMA20 against the trade:
   - LONG runner exit: close < EMA20
   - SHORT runner exit: close > EMA20
4. If breakeven is touched before that bar-close exit, runner exits at 0R.
5. Ambiguous same-M1 target/BE ordering is pessimistic: runner = 0R.

Gross winner R:
0.5 * target_R + 0.5 * runner_R

Level-A net R:
gross composite R - frozen one-spread cost_R.

No 1R breakeven trigger, ATR trail, chandelier, or optimized partial fraction.
50/50 is frozen as the literal midpoint interpretation of 'exit part and trail the balance'.

## Required result

Every symbol/year/direction/timeframe.

Promotion requires:
- realized win rate remains >=50% across at least 18/24 adequate groups at the same timeframe;
- average realized winner >1.0R;
- pooled AND median market-year-direction cost-adjusted expectancy >0;
- no single market/year carries the result;
- neighboring timeframes do not materially reverse.

Failure closes the runner implementation; do not optimize the partial percentage or EMA length.
