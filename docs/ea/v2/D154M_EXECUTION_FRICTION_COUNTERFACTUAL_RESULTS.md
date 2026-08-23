# D-154M — Execution-Friction Counterfactual Results

Status: COMPLETE / SHADOW-ONLY / NO STRATEGY CHANGE  
Date: 2026-08-23  
Build: `2.11R0L11`

## Integrity

GOLD25 and CADJPY25 Q1 OFF/ON canonical non-interference parity passed.

Full research panel used one EX5 SHA:

```text
b0756412c0ce03274c5b366cf18924f4e5206a33ff31b2058631c80c3e90a0ce
```

All full cells had:
- `D154M_FILL_SNAPSHOT == D154M_PAIR_OUTCOME`;
- zero `D154M_INTEGRITY_WARNING`;
- zero `ACTUAL_PLUS_1R_TO_SHADOW_SL`;
- zero execution divergence;
- zero pending-cancel rejection.

GOLD23 retained one right-censored Fill in both actual and shadow.

## Counterfactual

Actual D151 barrier quote:

```text
LONG  = BID
SHORT = ASK
```

D154M shadow:

```text
LONG  = ASK
SHORT = BID
```

Same actual Fill, same original SL, same exact +1R barrier.

This is an `ENTRY_SIDE_QUOTE_BARRIER_RACE`, not a synthetic zero-spread price.

## Results

```text
cell       actual survival   shadow survival   SL->shadow +1R   rescue of actual SL
GOLD23     34/65 = 52.3%     39/65 = 60.0%     5 / 31           16.1%
GOLD24     24/52 = 46.2%     25/52 = 48.1%     1 / 28            3.6%
GOLD25     30/53 = 56.6%     31/53 = 58.5%     1 / 23            4.3%
BTC25      60/127= 47.2%     67/127= 52.8%     7 / 67           10.4%
SILVER25   18/46 = 39.1%     18/46 = 39.1%     0 / 28            0.0%
CADJPY25   30/113= 26.5%     47/113= 41.6%    17 / 83           20.5%
```

2025 percentage-point improvement:

```text
GOLD      +1.9 pp
BTC       +5.5 pp
SILVER    +0.0 pp
CADJPY   +15.0 pp
```

## Direction split

```text
GOLD25
LONG   60.0% -> 62.9%   1 flip
SHORT  50.0% -> 50.0%   0 flips

BTC25
LONG   44.3% -> 54.1%   6 flips
SHORT  50.0% -> 51.5%   1 flip

SILVER25
LONG   40.0% -> 40.0%   0 flips
SHORT  37.5% -> 37.5%   0 flips

CADJPY25
LONG   20.8% -> 37.5%   8 flips
SHORT  30.8% -> 44.6%   9 flips
```

CADJPY therefore is not a LONG-only quote artifact.

## Interpretation

D154M establishes a real causal pathway:

> For a meaningful subset of actual SL-first trades, the Entry-side quote reaches the same +1R barrier before reaching the same original SL even though the executable exit-side quote produces SL-first.

This effect is large in CADJPY and material in BTC.

However it is **not a universal explanation** of D154L:
- SILVER has high relative spread but zero D154M flips;
- GOLD23 has moderate relative spread but five flips;
- therefore market-level cost scale cannot be reduced to post-Fill barrier-side disadvantage alone.

After D154M, 2025 shadow survival becomes:

```text
GOLD      58.5%
BTC       52.8%
CADJPY    41.6%
SILVER    39.1%
```

The original strict D154L market ordering is no longer preserved after only this friction component is removed.

## Decision

```text
D154L cross-market cost-scale mechanism        = RETAIN
D154M post-fill quote-side causal effect       = SUPPORTED / PARTIAL
post-fill quote-side effect as universal cause = REJECT
per-trade spread threshold                     = NOT AUTHORIZED
baseline strategy change                       = NONE
```

The remaining execution hypothesis is pre-Fill quote-side timing/depth while a pending order waits for its executable quote.
