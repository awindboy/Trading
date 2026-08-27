# V5-026 through V5-033 — First Cross Research Synthesis

Status: `FROZEN DISCOVERY HISTORY`
Date: `2026-08-27`

## Source concept

Raschke's 3/10 First Cross is not treated as an oscillator cross signal by itself.

Source interpretation:

```text
slow 3/10 trend line crosses zero
-> trend is beginning to reverse
-> first fast-line pullback through zero
-> price should confirm first higher low / lower high
-> price triggers Entry
```

The source explicitly describes the oscillator as an initial condition and price as the trigger.

## V5-026A — broad source reproduction

15m / 30m / 60m / 120m / 1D were all reported.

Structural-retest pooled result:

```text
N        10,480
WR       45.29%
avg win  1.052R
EV      -0.231R
```

120m was the strongest common intraday scale but still only:

```text
N 647 / WR 49.92% / avg win 1.214R / EV +0.048R
```

Daily was too sparse (`N=50`) for evidence.

## V5-027A — causal price-pivot confirmation

A first causal 3-bar pivot higher-low/lower-high confirmation was added because the source says price must trigger the pattern.

Common intraday scales still failed.

Daily structural-retest result looked strong but was tiny:

```text
N 57 / WR 64.91% / avg win 1.142R / EV +0.377R
```

Do not treat this small daily sample as proof.

## V5-027B — pre-registered higher-timeframe bridge

The natural 240m and 480m bridge scales were frozen before outcomes.

Structural objective:

```text
240m: N 342 / WR 53.22% / avg positive 1.296R / EV +0.203R
480m: N 197 / WR 49.24% / avg positive 1.297R / EV +0.116R
```

240m therefore became discovery-selected and was frozen for exact M1 replay.

## V5-028A — exact M1 replay

Conservative ambiguity handling + recorded spread materially changed the apparent candidate:

```text
N                    398
WR                   46.73%
avg positive net R   1.354R
EV                  +0.048R
```

This failed the >=50% WR target.

Important lesson:

```text
coarse-bar strategy result != executable M1 result
```

## V5-029A — half at +1R, runner only to structural objective

```text
N                    390
WR                   55.90%
avg positive net R   0.796R
EV                  -0.030R
```

It restored win rate by manufacturing too many small winners. Rejected.

## V5-030A — half at +1R + EMA20/slow runner

This retained the exact V5-028A setup, Entry and structural stop.

The only management change was:
- 50% at +1R;
- runner to BE;
- remaining 50% held until 240m EMA20 close failure or 3/10 slow zero reversal.

Result:

```text
N                    406
WR                   53.94%
avg positive net R   1.197R
EV                  +0.148R
```

This is the first V5 development result satisfying the three central development economics simultaneously.

Read `V5_030A_FIRST_CROSS_240M_DEVELOPMENT_RESULTS.md`.

## V5-031A — daily 3/10 context

The daily alignment filter reduced the sample and did not improve temporal stability:

```text
N                    188
WR                   51.60%
avg positive net R   1.242R
EV                  +0.118R

2025 EV             -0.195R
```

Rejected. Do not add daily context to V5-030A.

## V5-032A — volatility adequacy

Source-grounded causal condition:

```text
current 240m ATR14
>
median(previous 20 completed ATR14)
```

Development subset:

```text
N                    155
WR                   61.29%
avg positive net R   0.993R
EV                  +0.212R
```

It failed its own frozen gate:
- required N >=240;
- avg positive net R had to remain >1R;
- USDJPY remained negative;
- GOLD# 2022 consumed diagnostic EV was -0.087R.

Rejected. No ATR threshold rescue.

## V5-033A — source-corrected Holy Grail runner

This was pre-registered as another source-grounded check, but it is **administratively closed without promotion**.

Reason:
V5-030A had already passed development economics. Continuing to search another Holy Grail lifecycle before independent validation would violate the success-first anti-mining discipline.

Do not run V5-033A as a rescue before V5-030A validation.

## Frozen conclusion

The active candidate is **not** “First Cross plus whichever filter looks best.”

It is exactly:

```text
V5-030A
240m First Cross
+ causal 3-bar price pivot
+ structural stop
+ 50% at +1R
+ runner BE
+ EMA20 / slow-line runner exit
```

All later development filters are rejected.

Next step: independent external-market validation only.
