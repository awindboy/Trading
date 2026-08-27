# V5-035A — First Cross Payoff-Capacity Audit Results

Status: `COMPLETED / SHADOW-ONLY / NO STRATEGY AUTHORITY`
Date: `2026-08-27`
Population: GOLD#, BTCUSD#, XAUEUR#, USDJPY# 2023-2025
Candidate reference: `V5_FIRST_CROSS_240M_HALF_EMA_RUNNER`
Preregistration SHA-256: `70b32c1995b52905d011b1ddbe6bd673f550b3ce24bd5be4226acecb19a4068b`

## Final economic objective

The old V5 development gate is no longer sufficient for promotion.

```text
realized positive-trade rate >= 50%
average positive NET R       >= 2.0R
cost-adjusted EV             > 0
```

`2R` is an evaluation criterion, not a fixed take-profit authorization.

## Current V5-030A distribution

```text
resolved N             406
positive N             219
WR                     53.94%
mean positive net R    1.1968R
positive median        0.580R
positive 75th pct      1.140R
positive 90th pct      2.092R
positive 95th pct      3.498R
```

Only `10.96%` of positive trades realized >=2R net.
Only `5.91%` of all resolved trades realized >=2R net.

Positive-R concentration:

```text
top 1% of positive trades   14.9% of positive R
top 5%                      33.7%
top 10%                     45.6%
top 20%                     59.2%
```

The mean winner is already materially tail-supported.

## Raw structural-regime excursion capacity

Shadow population: 409 eligible filled trades.

Observation window:

```text
actual fill
-> initial structural stop
OR
-> frozen slow-regime reversal
```

No EMA20 exit, +1R partial, or BE was applied.

Conservative M1 MFE:

```text
median MFE              0.864R
mean MFE                2.342R
75th percentile         2.273R
90th percentile         5.602R

reach >=1R             46.45%
reach >=2R             28.85%
reach >=3R             18.09%
reach >=4R             12.96%
```

The >=2R raw excursion rate was broad:

```text
BTCUSD#  29.71%
GOLD#    25.81%
USDJPY#  29.35%
XAUEUR#  30.23%

2023     28.78%
2024     28.24%
2025     29.50%

SHORT    26.92%
LONG     30.85%
```

## Post-1R continuation under current runner lifecycle

Clear +1R population: `223`.

```text
median continuation MFE   1.845R
mean continuation MFE     3.402R

reach >=2R               45.29%
reach >=3R               27.80%
reach >=4R               18.83%
```

Current partial-BE trades:

```text
N                         100
reached >=2R before BE     28
reached >=3R before BE     11
reached >=4R before BE      5
```

Therefore the current ~1.20R mean positive result is not explained by absence of 2R+ favorable excursion.

## Partial-fraction feasibility check

After the preregistered shadow audit, the complete one-dimensional family was checked algebraically:

```text
at +1R realize fraction f
remaining 1-f uses the SAME current BE + EMA/slow runner
```

No new exit signal or threshold was introduced.

Endpoints:

```text
f = 0.00
WR              29.56%
avg positive     2.755R
EV              +0.293R

f = 0.50  current
WR              53.94%
avg positive     1.197R
EV              +0.148R
```

Across all `f`:

```text
maximum avg positive while WR >=50%  ~= 1.515R
maximum WR while avg positive >=2R   ~= 39.66%
```

Therefore partial-size tuning alone cannot satisfy the new joint objective.

## Classification

```text
REAL 2R+ EXCURSION CAPACITY EXISTS

BUT

THE CURRENT PARTIAL/BE/RUNNER FAMILY CANNOT JOINTLY DELIVER
WR >=50% AND AVG POSITIVE NET >=2R
```

Do not select a new partial fraction from this development population.
