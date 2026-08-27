# V5-002 through V5-025 — Success-First Research Synthesis

Status: `FROZEN RESEARCH HISTORY`
Date: `2026-08-27`
Strategy authority: `NONE`

Purpose: prevent a later session from repeating already-consumed discovery or selectively remembering only favorable intermediate results.

## Boundary / breakout mechanism cycle

### V5-002 — balance-generated breakout

Result:
- continuous balance/contraction descriptors did not stably explain breakout direction;
- pre-event expansion/trendiness was more stable for **future movement intensity** than for direction;
- confirmation tended to describe an already-realized move rather than create remaining directional payoff.

Classification:

```text
DIRECTIONAL MECHANISM NOT SUPPORTED
INTENSITY INFORMATION DESCRIPTIVELY SUPPORTED
```

Do not reopen by choosing the best range length or contraction threshold.

### V5-003 — cross-scale trendability

Higher-timeframe directional efficiency did not reliably convert lower-timeframe breakout into remaining directional continuation.

Classification: `FAILED`.

### V5-004 / V5-005 — failed price discovery / breakout retest

These branches did not produce a promoted strategy candidate under the frozen success-first gates.

Do not reuse them as a reason to introduce a generic `breakout/retest` Entry.

## Raschke Holy Grail cycle

The important lesson was the separation of:
- Entry survival;
- structural target geometry;
- winner continuation.

Selected pooled Level-A results from the local research ledger:

| Experiment | N | WR | Avg positive net R | EV |
| --- | ---: | ---: | ---: | ---: |
| V5-006A initial Holy Grail | 723 | 59.61% | 0.642R | -0.035R |
| V5-006B broader lifecycle | 9,037 | 53.67% | 0.751R | -0.096R |
| V5-006C runner | 9,037 | 51.61% | 0.846R | -0.065R |
| V5-014A EMA runner | 9,037 | 44.58% | 1.018R | -0.064R |
| V5-016A target-lock runner | 9,037 | 53.14% | 0.807R | -0.071R |
| V5-019A +1R conversion | 9,035 | 50.15% | 0.974R | -0.055R |
| V5-020A source-correct prior-swing target | 7,922 | 54.19% | 0.497R | -0.064R |
| V5-020A source-correct +1R conversion | 7,921 | 51.58% | 0.990R | -0.006R |
| V5-023A source-correct target-lock | 7,922 | 52.75% | 0.609R | -0.019R |

Repeated structure:

```text
high Entry survival
<-> small structural winner

or

larger winner
<-> WR loss
```

This trade-off is why the project did not promote the Holy Grail family.

### V5-012 survival diagnostic

With the original Holy Grail structural risk, +1R was reached before -1R slightly more than 50% at every tested scale:

```text
15m   50.72%
30m   51.43%
60m   51.62%
120m  51.72%
```

This was useful mechanism evidence, not a profitable strategy.

### V5-020 source correction

Research returned to the Street Smarts wording and corrected the Entry trigger from the EMA-touch bar to the **previous completed signal bar high/low**.

The correction improved hit rate but compressed the prior-swing R multiple; it did not solve expectancy.

### V5-021 published re-entry

Source-corrected re-entry attempts:

```text
N                    1,637
WR                   50.64%
avg positive net R   0.969R
EV                  -0.026R
```

No promotion.

### V5-022 structural asymmetry

Applying the previously frozen `target_R > 1` economic condition to source-corrected Holy Grail did not rescue the family:

```text
structural objective subset:
N 1,630 / WR 37.67% / avg positive 1.555R / EV -0.123R

+1R conversion on same subset:
N 1,630 / WR 48.59% / avg positive 0.966R / EV -0.103R
```

No threshold rescue.

## Other success-first setups

### Turtle Soup / failure tests

V5-007/V5-009 did not meet the project joint WR/payoff/EV target. Preserve as negative setup-family evidence.

### Anti

V5-010A pooled 4-bar lifecycle:

```text
N 17,376
WR 41.21%
avg positive net R 0.826R
EV -0.101R
```

No promotion.

### Momentum Pinball

V5-018A:

```text
N 656
WR 17.38%
avg positive net R 4.444R
EV -0.121R
```

The payoff tail was large but the realized win rate was far below the project requirement.

### 80-20

V5-024 showed extreme R multiples caused by very tight failure-test risk geometry, but:

```text
5-point version:
WR 12.69%
median recorded spread cost ~0.53R

15-point version:
WR 13.96%
median recorded spread cost ~0.36R
```

It violates the final WR target and is execution-fragile. Do not infer edge from large mean winner/EV alone.

### Failed Holy Grail forecast

V5-025 tested Raschke's statement that a Holy Grail that fails to hold the EMA can have opposite-direction forecasting value.

Under the frozen causal clock, failure confirmation did not add stable remaining opposite-direction information versus the paired fill-time fade control.

Classification: `FAILED`.

## Regression conclusion

After these failures, do not conclude that technical analysis is impossible.

The correct regression was:

```text
Do successful technical traders have a setup whose
Entry + structural invalidation + lifecycle
jointly satisfy our required payoff geometry?
```

That led to the 3/10 `First Cross` research line.
