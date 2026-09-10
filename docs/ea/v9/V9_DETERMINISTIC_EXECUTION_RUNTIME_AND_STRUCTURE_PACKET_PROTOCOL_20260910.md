# V9 Deterministic Execution Runtime and Structure Packet Protocol

Date: `2026-09-10`
Status: `DEFERRED IMPLEMENTATION REFERENCE`
Market: `GOLD# ONLY`

## Current status

Do not treat this document as the active research gate.

First mature the chart-native HTF market-map method.

The earlier plan to make a deterministic structure registry choose major market structure is deferred.

## Retain for later implementation

Runtime should later handle:

- causal data ingestion;
- chart construction;
- exact coordinates after AI selection;
- Entry/SL/R/S arithmetic;
- order state;
- Hard SL guards;
- destination/review touch detection;
- timestamps;
- MFE/MAE;
- journal state.

Runtime should not decide that a mechanically detected swing is strategically important.

## Structure authority

AI may select major semantic structures from the chart.

After selection, store:

```text
STRUCTURE_ID
SOURCE_TIMEFRAME
SOURCE_TIMESTAMPS
LOWER_PRICE
UPPER_PRICE
AI_ROLE
```

Use exact stored coordinates for execution.

Do not let AI silently move an armed SL/TP/review level after entry.

## Liquidity language

OHLC does not prove resting order-book liquidity.

Use `liquidity candidate` for prior highs/lows and other price draws inferred from chart structure.

## Future work

Return to deterministic runtime implementation after:

1. HTF mapping method is stable;
2. POI selection is stable enough;
3. SL authority is understood;
4. destination/review logic is understood;
5. LTF execution research is complete.
