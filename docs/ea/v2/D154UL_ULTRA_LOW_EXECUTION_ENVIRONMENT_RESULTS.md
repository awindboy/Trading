# D-154UL — Ultra Low Execution-Environment Validation Results

Status: COMPLETE / NATURAL EXPERIMENT / NO STRATEGY CHANGE  
Date: 2026-08-24  
EA: `2.11R0L11 / D154M`  
Environment: XM Ultra Low (`#` symbols)

## Integrity

Ultra Low symbols:

```text
GOLD#
BTCUSD#
SILVER#
CADJPY#
```

GOLD# and CADJPY# Q1 D154K+D154M OFF/ON canonical parity passed.

All full-year 2025 runs:
- Every tick based on real ticks;
- same tested EX5;
- complete D154K snapshots and D154M pairs;
- zero D154K/D154M integrity warnings;
- zero execution divergence;
- zero pending-cancel rejection.

## Standard -> Ultra Low

```text
          fills       actual +1R survival       D154M shadow survival
GOLD      53 -> 55     56.6% -> 58.2%           58.5% -> 58.2%
BTCUSD   127 ->127     47.2% -> 48.8%           52.8% -> 51.2%
SILVER    46 -> 47     39.1% -> 38.3%           39.1% -> 38.3%
CADJPY   113 ->113     26.5% -> 30.1%           41.6% -> 38.9%
```

Actual survival change:

```text
GOLD     +1.58 pp
BTCUSD   +1.57 pp
SILVER   -0.83 pp
CADJPY   +3.54 pp
```

Ultra Low reduced friction but did not solve Entry survival.

## Relative spread scale

Median `spread / Root-contact->CHOCH reaction M1 TR`:

```text
GOLD      0.3417 -> 0.1620
BTCUSD    1.0147 -> 0.5411
SILVER    1.7011 -> 1.3025
CADJPY    2.1255 -> 1.6312
```

Median `spread / actual 1R`:

```text
GOLD      0.0281 -> 0.0141
BTCUSD    0.0632 -> 0.0323
SILVER    0.1471 -> 0.1084
CADJPY    0.1496 -> 0.1235
```

Median `spread / selected FVG width`:

```text
GOLD      0.4615 -> 0.2466
BTCUSD    1.0256 -> 0.5505
SILVER    2.0992 -> 1.5000
CADJPY    2.6875 -> 2.0563
```

## D154M effect

Actual SL-first -> entry-side quote +1R flips:

```text
GOLD       1 -> 0
BTCUSD     7 -> 3
SILVER     0 -> 0
CADJPY    17 ->10
```

Actual-vs-shadow survival gap:

```text
GOLD       1.89 pp -> 0.00 pp
BTCUSD     5.51 pp -> 2.36 pp
SILVER     0.00 pp -> 0.00 pp
CADJPY    15.04 pp -> 8.85 pp
```

Lower spread therefore reduced the exact post-Fill quote-side effect where that effect previously existed.

## Scenario-population overlap

Exact scenario-id overlap:

```text
GOLD      common 48 | Standard-only 5 | Ultra-only 7
BTCUSD    common126 | Standard-only 1 | Ultra-only 1
SILVER    common 43 | Standard-only 3 | Ultra-only 4
CADJPY    common112 | Standard-only 1 | Ultra-only 1
```

Across 329 common scenarios:

```text
SL_FIRST -> PLUS_1R = 7
PLUS_1R -> SL_FIRST = 0
```

This further supports execution friction as causal while confirming that lower spread alone is not sufficient.

## Decision

```text
D154K/L cost-scale mechanism                = FURTHER SUPPORTED
D154M post-Fill quote-side mechanism        = FURTHER SUPPORTED
Ultra Low reduces execution friction        = CONFIRMED
Ultra Low solves Entry-survival problem     = REJECT
per-trade spread threshold                  = NOT AUTHORIZED
baseline strategy change                    = NONE
```
