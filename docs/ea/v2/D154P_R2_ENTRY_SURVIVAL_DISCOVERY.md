# D-154P R2 — Entry Survival Discovery Freeze / 2024 Validation

Status: `2025 DISCOVERY FROZEN / 2024 UNSEEN VALIDATION NEXT`  
Date: `2026-08-24`  
Strategy authority: `NONE`  
2021: `KEEP UNTOUCHED`

## Primary discovery population

Complete-history, execution-clean, low-friction markets:

```text
GOLD#      55 fills
BTCUSD#   127 fills
XAUEUR#    58 fills
USDJPY#    94 fills
TOTAL     334 fills
```

2025 is discovery only.

## R2 correction to the earlier session hypothesis

The previously discovered `13:00 <= actual Fill < 15:00` effect remains statistically
interesting, but it is **not a pre-Fill setup-authorization variable**.

Observed in 2025:

```text
actual Fill 13:00-15:00
28 fills
23/28 = 82.1% Fill->+1R

FVG/PENDING authorization 13:00-15:00
36 fills
19/36 = 52.8% Fill->+1R
```

Therefore the effect belongs to **retest/execution-time regime**, not setup formation.

A future strategy implementation would require a session-aware virtual/conditional pending
architecture. Do not pretend that the future Fill time was knowable when the FVG was authorized.

The 2024 run will validate this relation descriptively only.

## H-ESCAPE — primary actionable pre-Fill hypothesis

Define causal Root width:

```text
W = root_top - root_bottom
```

Define planned-entry directional escape distance:

```text
LONG:
g = (planned_entry - root_top) / W

SHORT:
g = (root_bottom - planned_entry) / W
```

Frozen discovery band:

```text
ROOT_ESCAPE_BAND := 0 < g <= 0.5
```

Interpretation:

```text
g <= 0
    Entry has not cleanly escaped the causal Root.

0 < g <= 0.5
    displacement has cleared the Root,
    but Entry remains close to the causal origin.

g > 0.5
    Entry is increasingly extended away from the causal Root.
```

This is fully known when the selected FVG / planned Entry is frozen.

### 2025 result

```text
ROOT_ESCAPE_BAND
62 fills
42/62 = 67.7% Fill->+1R
37/62 = 59.7% realized winners
+0.360R/trade expectancy
1.225R average winner
PF 1.97
+22.30R total

all other geometries
272 fills
125/272 = 46.0% Fill->+1R
41.5% realized winners
-0.054R/trade expectancy
PF 0.91
```

Per market:

```text
             fills   +1R survival   realized WR   expectancy
GOLD#           10       80.0%         80.0%       +0.801R
BTCUSD#         24       62.5%         54.2%       +0.301R
XAUEUR#          8       75.0%         62.5%       +0.153R
USDJPY#         20       65.0%         55.0%       +0.293R
```

The sample is still discovery-sized, especially XAUEUR#.

### Robustness inside 2025

The relation did not depend on one market:

```text
leave one market out
-> among five natural Root-relative bands
   INSIDE / 0-.5W / .5-1W / 1-2W / >2W
-> the other three markets selected 0-.5W every time

held-out survival:
GOLD#      80.0%
BTCUSD#    62.5%
XAUEUR#    75.0%
USDJPY#    65.0%
```

Market+direction-stratified logistic OR was about `2.51` in favor of the band.

A market+direction-stratified permutation scan over the five natural geometry bands gave
an approximate scan-adjusted `p ~= 0.009`.

Quarter stability:

```text
Q1  55.6%
Q2  70.6%
Q3  65.2%
Q4  76.9%
```

The relation also remained positive for:
- LONG and SHORT;
- H1 and M30 active map;
- H1/M30/M15 Root source;
- merged and non-merged execution contributors.

## Execution-suitability interaction

The same ROOT_ESCAPE_BAND did **not** rescue the valid high-friction controls:

```text
SILVER# + EURUSD# + ETHUSD#

band:
13 / 32 = 40.6% survival

outside:
72 / 181 = 39.8% survival
```

Median exact execution friction inside the same band:

```text
low-friction primary markets:
spread/reactionTR ~= 0.38
spread/risk       ~= 0.031
spread/FVG        ~= 0.51

high-friction controls:
spread/reactionTR ~= 0.94
spread/risk       ~= 0.060
spread/FVG        ~= 1.25
```

Working causal model:

```text
market-level execution suitability
        x
trade-level causal Entry geometry
        ->
Entry edge survival
```

This is not a per-trade spread threshold.

## Geometric interpretation

The current SL is Root-distal based. As Entry moves farther beyond the Root:

```text
risk distance grows
+
remaining objective room shrinks
+
the selected FVG becomes a later continuation entry
```

The 0-.5W band is therefore interpreted as:

> `escape without extension`

There is enough displacement to leave the Root, but the Entry has not consumed too much
of the causal move.

This is a more specific hypothesis than the older `Root/FVG gap <= 1W` screen.

## H-ROOT-NEAR — demoted secondary geometry

Older discovery:

```text
FVG/Root interval gap <= 1 Root width
```

pooled positively, but did not preserve direction in every market; BTCUSD# did not improve.
Keep it descriptive in 2024, but H-ESCAPE is the primary pre-Fill geometry hypothesis.

## H-COMPACT — continuous discovery descriptor

`reaction_range_over_tr` was lower for PLUS_1R than SL_FIRST in all four primary markets.

Within-market quartiles:

```text
Q1  55.6%
Q2  55.3%
Q3  49.4%
Q4  40.0%
```

However its independent effect weakens after controlling for H-ESCAPE.
Validate it as a continuous descriptor only. Do not freeze a cutoff.

## H-DECISIVE-SWEEP — instrumentation candidate, not a rule

Shorter Root-contact -> sweep time was favorable in three of four markets and in
same-day observations. Wall-clock seconds are contaminated by session gaps.

If the relation survives 2024 descriptively, add shadow-only active-M1-bar counts before
any strategy use. No seconds threshold is authorized.

## H-SESSION — execution-time regime

Frozen descriptive relation:

```text
13:00 <= actual Fill broker/server time < 15:00
```

2025 primary markets:

```text
28 fills
82.1% Fill->+1R
75.0% realized WR
+0.647R/trade expectancy
```

It was positive in all four full-year low-friction markets and both directions.

But:
- authorization time in the same window was not predictive;
- valid high-friction controls did not show the relation.

Therefore any later strategy variant must simulate/implement session-restricted pending
execution without look-ahead.

## Orthogonality of H-ESCAPE and H-SESSION

2025:

```text
neither                   108 / 250 = 43.2%
H-ESCAPE only              36 / 56  = 64.3%
H-SESSION only             17 / 22  = 77.3%
both                         6 / 6   = 100.0%  [tiny]
```

In a market+direction fixed-effects model, both signals remained independently positive.

Do not promote the six-trade interaction.

## FVG-selector architecture hypothesis

Current frozen selection chooses the widest eligible same-causal-leg FVG.

Among extended (`g > 0.5`) SL_FIRST trades:

```text
77 / 97
```

had more than one eligible FVG.

Current logs do not contain the geometry/outcome of every unselected candidate, so no claim
can yet be made that a nearer candidate would have been better.

If H-ESCAPE validates in 2024, the next highest-value shadow audit is:

```text
current widest eligible FVG
vs
nearest causally eligible FVG satisfying Root-relative geometry

same scenario
same Root
same causal leg
shadow only
```

The purpose is to determine whether good setups should be rejected when the widest FVG is
extended, or whether the EA is sometimes selecting the wrong FVG.

## Decision counterfactuals — discovery only

Unchanged actual trade outcomes, no new backtest:

```text
GOLD# all trades
WR            56.4%
avg winner     1.323R
expectancy    +0.291R
net           +15.99R
PF             1.64
```

Non-GOLD (`BTCUSD# / XAUEUR# / USDJPY#`) only in H-ESCAPE:

```text
52 trades
survival       65.4%
realized WR    55.8%
avg winner      1.217R
expectancy     +0.275R
net            +14.29R
PF              1.68
```

`GOLD# all + non-GOLD H-ESCAPE`:

```text
107 trades
realized WR    56.1%
avg winner      1.272R
expectancy     +0.283R
net            +30.28R
PF              1.66
```

`GOLD# all + non-GOLD (H-ESCAPE OR H-SESSION)`:

```text
124 trades
realized WR    59.7%
avg winner      1.264R
expectancy     +0.358R
net            +44.44R
PF              1.91
```

These are discovery counterfactuals only. They define the decision question for 2024;
they are not strategy evidence.

## 2024 validation contract

Run unchanged strategy:

```text
XM Ultra Low
GOLD#
BTCUSD#
XAUEUR#
USDJPY#

2024-01-01 .. 2024-12-31
Every tick based on real ticks
V3E mode 9
EM OFF
D151 ON
D154K ON
D154M ON
```

Freeze before viewing 2024:

```text
PRIMARY:
H-ESCAPE = 0 < directional planned-entry Root gap / Root width <= 0.5

DESCRIPTIVE:
H-SESSION = actual Fill 13:00-15:00 server time
H-ROOT-NEAR = Root/FVG interval gap <= 1W
H-COMPACT = continuous reaction_range_over_tr

PAYOFF SEPARATE:
structural objective room >=3R
```

Do not move any boundary after 2024 is seen.

Primary decision:

```text
If H-ESCAPE reproduces across non-GOLD markets and remains economically positive:
    non-GOLD participation remains viable.

If H-ESCAPE fails outside GOLD:
    do not invent another 2025-derived geometry cutoff;
    move the final universe decision toward GOLD / GOLD-family only.

If H-SESSION also reproduces:
    design a shadow-only session-restricted pending execution audit before any live gate.
```

2021 stays untouched.
