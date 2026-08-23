# D-154O Stage-A Candidate Universe Manifest

Status: `FROZEN BEFORE STAGE-A OUTCOMES`  
Date: `2026-08-24`  
Universe ID: `D154O_STAGE_A_UL32_20260824`  
Environment: `XM Ultra Low`  
Reference: `GOLD#`

## Purpose

Freeze the broad Stage-A market universe before any new-symbol 2025 strategy outcome is generated.

This manifest is a **candidate-universe freeze**, not the later Gold-like shortlist. No Stage-B authorization follows from inclusion here.

## Frozen screen window

```text
2026-08-17 00:00:00
through
2026-08-23 23:59:59
broker/server time
```

## Included universe — 32 symbols

### Forex / Standard Ultra Low / Majors — 15

```text
CADCHF#
CADJPY#
CHFJPY#
EURCAD#
EURCHF#
EURGBP#
EURJPY#
EURUSD#
GBPCAD#
GBPCHF#
GBPJPY#
GBPUSD#
USDCAD#
USDCHF#
USDJPY#
```

### Cryptocurrencies / Ultra Low — 8

```text
ADAUSD#
BCHUSD#
BTCUSD#
DOGEUSD#
ETHUSD#
SOLUSD#
XLMUSD#
XRPUSD#
```

### Derivatives / Spot Metals Ultra Low — 9

```text
GOLD#
SILVER#
XAUEUR#
XPDUSD#
XPTUSD#
GAUCNH#
GAUUSD#
XAUCNH#
XAUJPY#
```

## Explicitly excluded before outcomes

The initially considered US-stock cohort (`Nvidia`, `Nasdaq`, `Apple`, `Google`) is excluded from the primary D154O Stage-A universe because the broker's `Stocks/US` category does **not** have an Ultra Low classification.

This exclusion is based on execution-environment compatibility, not observed strategy performance, and was made before Stage-A or new-symbol 2025 outcomes.

## Governance

- Include all 32 symbols in the same fixed-week collection before interpreting relative execution metrics.
- `GOLD#` is the same-week reference.
- Stage-A chart metrics are proxies, not exact D154K strategy-derived variables.
- Do not generate or inspect new-symbol 2025 strategy WR/P&L before the later Gold-like shortlist and negative controls are frozen.
- Do not create a weighted `GoldLikeScore`.
- The later shortlist may only use Stage-A execution-scale metrics, their distributions, data quality, and asset/category context.
- Known prior GOLD#/BTCUSD#/SILVER#/CADJPY# evidence remains historical context and must not be used to retroactively tune a per-trade spread threshold.
