# V5-038A — Williams Commercial COT Population Qualification

Status: `CLOSED BEFORE PRICE OUTCOME`
Date recorded: `2026-08-28`
Authority: `V5 historical source/data evidence only`
Production authority: `NONE`

## Source-faithful definition

Use CFTC Legacy Futures Only Gold contract `088691`.

```text
Commercial Net = Commercial Long - Commercial Short
COT Index = percentile position of current Commercial Net
            within prior 156 weekly reports
bullish extreme >= 80
bearish extreme <= 20
```

This replaced an earlier exploratory Commercial-price-divergence scratch that was not the exact Williams COT Index definition.

## 2023 population qualification

Only two source-defined extreme reports qualified in 2023, both bullish/long extremes.
The preregistered minimum population was N>=12.

```text
qualifying reports = 2
required minimum   = 12
```

Representative qualifying values from the 156-week recomputation were approximately:

```text
2023-10-03  COT Index ~80.7
2023-10-10  COT Index ~89.1
```

## Decision

```text
SOURCE-DEFINED POPULATION INSUFFICIENT
CLOSED BEFORE GOLD PRICE OUTCOME
```

No 80->75 relaxation, rolling-window change, extra-year expansion, Managed-Money substitution, or seasonality rescue was allowed.
