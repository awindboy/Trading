# D-154G HTF Root Birth Lineage — Results

Status: `COMPLETE / NO STRATEGY PROMOTION`  
Date: `2026-08-22`

## Primary preregistered question

Does an actual Fill become weaker when at least one same-entry contributor Root was born while the same later PLAN-map timeframe already had a different mature owner?

`M30 -> later H1 promotion` was explicitly excluded from stale classification.

## Discovery — GOLD23 clean prefix

Window: `2023-01-01 .. 2023-12-21`. Execution integrity clean.

```text
actual fills                         = 66
resolved                             = 65
PLUS_1R                              = 34
SL_FIRST                             = 31
RIGHT_CENSORED                       = 1
contributor Roots                    = 142
SAME_PLAN_TF_OWNER_AT_BIRTH          = 142 / 142
HAS_PRIOR_SAME_TF_OWNER fills        = 0 / 66
```

The primary stale-owner exposure had zero coverage. It therefore cannot explain Entry survival in this population.

## Validation panel

Clean runs:

```text
GOLD24    52 fills
GOLD25    53
BTCUSD25 127
SILVER25  46
CADJPY25 113
total    391
```

`HAS_PRIOR_SAME_TF_OWNER = 0 / 391`. Combined with discovery, zero of 457 actual fills exhibited the preregistered exposure.

## Exploratory same-owner refresh proxy

GOLD23 ledger reconstruction suggested that a new same-owner active-map BOS between contributor PLAN and master pending submission was associated with weak survival:

```text
GOLD23 refresh      1/9  = 11.1%
GOLD23 no refresh  33/56 = 58.9%
```

The frozen validation definition did not generalize:

```text
validation refresh      6/19  = 31.6%
validation no refresh 156/372 = 41.9%
```

GOLD24 and CADJPY25 reversed the relationship. Coverage was only 19/391. No cancel-on-refresh rule is authorized.

Simple static H1/M30 alignment also failed to generalize and is not promoted.

## Decision

- Reject prior-owner Root reuse as the current Entry-survival explanation: zero observed coverage.
- Reject same-owner pre-entry BOS refresh as a universal veto.
- Do not rescue with Root age, source TF, direction, market-specific exceptions, or scores.
- Move upstream from scalar/static HTF labels to ordered nested H1/M30 state-transition replay.
- Baseline strategy semantics remain unchanged.
