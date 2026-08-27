# V5-008A — Holy Grail 3-10 Momentum Confirmation / Runner Routing Pre-registration

Status: `PRE-REGISTERED BEFORE V5-008A OUTCOME ANALYSIS`
Date: `2026-08-27`
Parent: `V5-006B/C Holy Grail reproduction`
Strategy authority: `NONE`

## Why this study

V5-006B produced the first repeated success-first mechanism in the project:
- target-first win rate around 55-60% across 15/30/60/120m;
- broad market/year/direction stability;
- but median target payoff <1R and spread-adjusted expectancy was negative.

V5-006C preserved half at the prior swing target and ran half using a frozen EMA20-close exit. It improved payoff but
did not robustly satisfy the project target.

Before abandoning Holy Grail, return to Raschke's own description rather than inventing filters:
- the 2004 Active Trader interview says the best Grail setups have confirmation from the 3-10 oscillator making new
  momentum highs/lows;
- the same interview says 3-10 divergence can mark the end of a run;
- Street Smarts explicitly says the target retest can either fail for a small profit or start a new continuation leg,
  and suggests taking part at the old swing and tightening the balance if continuation is expected.

V5-008A tests whether this missing published momentum information separates those two outcomes.

## Base population and execution

Reuse V5-006B exactly:
- signal timeframes: 15 / 30 / 60 / 120m;
- ADX(14)>30 and rising;
- frozen V5 direction operationalization;
- first EMA20 pullback;
- V5-006B order lifecycle;
- structural stop and prior swing target;
- M1 execution and one-spread Level-A cost.

Do not retune ADX, EMA, timeframe, entry, stop, target, or pending lifecycle.

Reuse the V5-006C runner exit exactly:
- after target, runner stop is moved to entry;
- runner exits at the first completed signal-timeframe close across EMA20 against the trade;
- same-minute target/BE ambiguity is pessimistic.

The only new information is the published 3-10 oscillator.

## 3-10 oscillator

On each completed signal-timeframe bar:

```text
osc = SMA(close,3) - SMA(close,10)
signal = SMA(osc,16)
```

No exponential moving averages.

Only completed signal bars can be used.

## M1 — Pre-pullback momentum confirmation

The frozen prior-swing target has an origin bar: the completed signal bar between `arm_end` and `setup_end` on which
the target high/low was established.

For LONG:
```text
pre_momentum_confirmed =
    osc_at_target_origin > osc_at_arm
    AND
    osc_at_target_origin >= max(osc on completed bars from arm through target-origin)
```

For SHORT reverse the inequalities.

If the target origin is the arm bar itself, confirmation is `UNRESOLVED`, not TRUE.

This is a cycle-local, no-new-lookback operationalization of Raschke's statement that the move should create a new
momentum high/low before the first pullback.

Primary M1 question:
Does the confirmed subset improve:
- target-first WR;
- target-R distribution;
- cost-adjusted expectancy;
- runner potential;
without one market/year carrying the effect?

M1 is a descriptive mechanism test first. It does not authorize dropping unconfirmed trades unless the full promotion
gate is met.

## M2 — Momentum persistence at the prior-swing retest

For target-hit trades only, at the exact M1 target-hit timestamp use the **last completed signal bar available strictly
before that timestamp**.

Compare its 3-10 oscillator with the oscillator at the original target-origin bar.

LONG:
```text
target_momentum_persistent =
    latest_completed_osc_before_target > osc_at_target_origin
```

SHORT:
```text
target_momentum_persistent =
    latest_completed_osc_before_target < osc_at_target_origin
```

No threshold and no use of the incomplete signal bar containing the target hit.

Interpretation:
- TRUE = momentum has already exceeded the old swing's momentum reading before price completes the retest;
- FALSE = no new momentum extreme / possible divergence;
- missing history = UNRESOLVED.

## Frozen routed exit

For every V5-006B resolved trade:

LOSS:
```text
-1R minus frozen one-spread cost
```

TARGET HIT + M2 FALSE/UNRESOLVED:
```text
exit 100% at frozen prior-swing target
```

TARGET HIT + M2 TRUE:
```text
exit 50% at target
move remaining 50% stop to entry
exit runner with frozen V5-006C EMA20-close rule
```

No partial fraction tuning. The 50/50 split is inherited from V5-006C and matches the published suggestion to take part
at the old swing and tighten the balance.

## Recursive falsification

Before promotion:
1. Compare M2 TRUE vs FALSE within every symbol/year/direction/timeframe.
2. Verify momentum persistence predicts **post-target runner return**, not merely identifies trades that already moved.
3. Target-hit movement receives no extra credit; runner starts at target.
4. Control for target_R and trade duration so M2 is not only a geometry proxy.
5. Remove the strongest market/year and repeat.
6. Report all four timeframes.
7. Compare against the frozen V5-006B target-only and V5-006C unconditional-runner controls.

## Promotion gate

A routed Holy Grail candidate is `SUCCESSFUL DEVELOPMENT CANDIDATE` only if one timeframe, without hidden market
selection, satisfies all:

- realized final positive-trade rate >=50% pooled and in >=18/24 market-year-direction groups with adequate N;
- average realized winner >1.0R;
- pooled cost-adjusted expectancy >0;
- median market-year-direction cost-adjusted expectancy >0;
- positive cost-adjusted expectancy in >=18/24 adequate-N groups;
- improvement over BOTH V5-006B and V5-006C at the same timeframe;
- no single market/year is necessary for the pooled result;
- neighboring timeframe does not show a material sign reversal.

If M1/M2 do not pass, close them. Do not invent oscillator thresholds.
