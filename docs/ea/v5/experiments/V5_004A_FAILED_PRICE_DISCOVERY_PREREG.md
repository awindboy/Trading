# V5-004A — Failed Price Discovery / Re-entry Pre-registration

Status: `PRE-REGISTERED BEFORE V5-004A OUTCOME ANALYSIS`
Date: `2026-08-27`
Parent: `V5-003A cross-scale trendability continuation FAIL`
Strategy authority: `NONE`

## Success-first sources

Hypothesis source only:
- Raschke/Connors `Turtle Soup`: explicitly designed to trade failed breakout tests rather than breakout continuation.
- Peter Brandt: chart-pattern failure can contain more information than completion; confirmed bear/bull traps are tradable in his process.
- Toby Crabel: liquidity-run / spring behavior focuses on penetration followed by opposite response.
- Carol Osler: actual FX order clustering provides a microstructure basis for both reversal at technical levels and acceleration after crossing.

None of these sources authorize our implementation or expectancy.

## Population

Use causal rolling reference scales:

```text
60m / 240m / 1440m
```

At each scale, a boundary identity is:

```text
symbol
+ scale
+ direction
+ timestamp at which the rolling high/low boundary was established
+ boundary price
```

Use the **first breakout attempt per boundary identity**.

This replaces outcome-dependent frozen-range de-duplication:
a later newly established boundary is a new research object even if an old trend never returned to the old range.

## Break event

UP attempt:
```text
high_t > causal rolling high
```

DOWN attempt:
```text
low_t < causal rolling low
```

Current bar was not part of the boundary calculation.

## Re-entry event

After first break, find the first completed M1 close back inside the frozen boundary:

UP break:
```text
close < upper boundary
```

DOWN break:
```text
close > lower boundary
```

The breakout bar itself may be the re-entry bar if its completed close is already back inside.

A V5-004A failed-price-discovery event requires re-entry within its own reference scale `W` minutes.
Re-entry latency is still recorded continuously.

No penetration/dwell threshold is allowed.

## Outcome clock

All primary outcomes start at the **re-entry close**, not at the original boundary or breakout.

Failure direction:
```text
failure_direction = -break_direction
```

Record signed close return in failure direction after:
```text
15m / 60m / 240m
```

Also record MFE/MAE and censoring.

The movement from breakout extreme back to the boundary/re-entry close receives zero credit.

## Paired causal negative control

For the same boundary episode, use the last completed M1 close immediately before the breakout attempt as a paired
`PREBREAK_FADE` control.

At that time the boundary and fade direction were already causal.

Measure the same opposite-break direction outcomes from that pre-break close.

Primary paired question:

> Does waiting for actual breakout failure/re-entry improve future opposite-direction path versus simply fading the boundary before it breaks?

This control is paired within the same boundary episode and does not require choosing a profitable external placebo.

## Required reporting

Every:
- symbol;
- year;
- break direction;
- scale;
- re-entry-latency distribution.

Report:
- median/mean signed return;
- positive-return fraction;
- paired `REENTRY - PREBREAK_FADE` difference;
- MFE/MAE;
- right-censoring;
- block-bootstrap uncertainty.

## Recursive falsification

Before calling re-entry informative:

1. remove the already-consumed breakout-to-reentry move;
2. compare against paired pre-break fade;
3. check all market-years/directions/scales;
4. test whether result is only generic short-horizon mean reversion;
5. check whether a few extreme reversal events drive the mean;
6. keep M1 intrabar-order limitation explicit;
7. compare with V3's prior result that `sweep alone has almost no alpha`.

## Kill condition

Close V5-004A if:
- re-entry-close future return is not stably positive in failure direction; or
- paired improvement over pre-break fade is not stable; or
- the effect is carried by one market/year/scale.

No threshold rescue.

## If supported

Only then open V5-004B to study **which failure interactions are tradable** using continuous:
penetration, latency, approach character, effort/result proxy, and response geometry.

No V3 sweep/FVG/acceptance gates are inherited.
