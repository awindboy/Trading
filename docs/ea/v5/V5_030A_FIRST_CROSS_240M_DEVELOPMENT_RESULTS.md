# V5-030A — First Cross 240m Development Results

Status: `DEVELOPMENT PASS / VALIDATION REQUIRED`
Date: `2026-08-27`
Production authority: `NONE`

## Frozen strategy

Setup lineage:

```text
Linda Raschke 3/10 First Cross concept
-> 240m completed bars
-> first slow-line zero regime change
-> first fast-line pullback through zero while slow remains on trend side
-> causal first 3-bar price pivot confirming higher-low / lower-high structure
-> stop-entry beyond completed pivot-confirmation bar
-> structural stop beyond pivot extreme
```

Management:

```text
initial stop = -1R
if +1R is reached first:
    realize 50% at +1R
    runner stop -> entry
    runner remains open until:
        first completed 240m close across EMA20 against position
        OR 3/10 slow line crosses zero against position
    hard BE runner stop remains active
```

No target-room filter, session filter, direction filter, volatility filter, daily filter or market-specific exception is part of this candidate.

## Development population

```text
GOLD#    2023-2025
BTCUSD#  2023-2025
XAUEUR#  2023-2025
USDJPY#  2023-2025
```

Level-A M1 replay uses conservative ambiguity exclusion and a recorded round-trip spread proxy.

## Primary result

```text
resolved trades          406
net-positive WR           53.94%
avg positive net R       +1.197R
spread-adjusted EV       +0.148R/trade
total net R              +60.11R
avg recorded spread cost  0.095R/trade
```

This is the first V5 development result to satisfy, simultaneously:

```text
WR > 50%
avg positive net R > 1R
spread-adjusted EV > 0
```

without forcing the whole position to exit at 1R.

## Year stability

| Year | N | WR | Avg positive net R | EV |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 138 | 55.07% | 1.379R | +0.271R |
| 2024 | 131 | 56.49% | 1.048R | +0.116R |
| 2025 | 137 | 50.36% | 1.155R | +0.055R |

Every pooled development year is positive.

## Market stability

| Market | N | WR | Avg positive net R | EV |
| --- | ---: | ---: | ---: | ---: |
| BTCUSD# | 136 | 54.41% | 1.276R | +0.174R |
| GOLD# | 93 | 61.29% | 0.951R | +0.183R |
| XAUEUR# | 86 | 51.16% | 1.616R | +0.307R |
| USDJPY# | 91 | 48.35% | 0.962R | -0.077R |

Three of four development markets have positive EV. USDJPY# is the principal negative market and must not be removed from the frozen candidate.

## Dependence checks

All leave-one-market-out pooled EVs remain positive:

```text
exclude BTCUSD#  +0.135R
exclude GOLD#    +0.138R
exclude XAUEUR#  +0.105R
exclude USDJPY#  +0.213R
```

All leave-one-year-out pooled EVs remain positive:

```text
exclude 2023  +0.085R
exclude 2024  +0.163R
exclude 2025  +0.195R
```

The result is therefore not carried by one development market or one development year.

Market x year x direction is less uniform:

```text
24 groups
positive EV     15 / 24
WR >= 50%       16 / 24
```

This is a reason to validate, not a reason to add filters.

## Uncertainty

Weekly-cluster bootstrap, 347 symbol-week clusters:

```text
EV 95% interval              [-0.018R, +0.336R]
WR 95% interval              [49.13%, 58.90%]
avg positive R 95% interval  [0.964R, 1.477R]
```

The point estimate passes the project development target, but the bootstrap lower bounds do not establish a final claim.

## Consumed temporal diagnostic

GOLD# 2022 was already consumed by V3 and is not pristine.

Unchanged V5-030A diagnostic:

```text
N                    34
WR                   50.0%
avg positive net R   +1.029R
EV                   -0.011R
```

This is approximately flat and does not validate the strategy. It also does not authorize retuning.

## Cost boundary

Current `net R` subtracts the frozen Level-A round-trip recorded spread proxy.

It does **not** yet establish:
- broker commission parity;
- slippage;
- exact tick order sequencing;
- live spread-at-order/fill divergence.

Therefore `full-cost expectancy` is not yet proven.

## Frozen interpretation

Classification:

```text
DEVELOPMENT PASS / VALIDATION REQUIRED
```

Do not:
- add an USDJPY veto;
- add a 2025 filter;
- tune ATR/ADX/EMA thresholds;
- change 240m because another timeframe looks better later;
- use GOLD# 2022 to repair the candidate.

Next authority is `V5_034A_EXTERNAL_VALIDATION_CONTRACT.md`.
