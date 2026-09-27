# V13 HA-6B2 EMA20 High/Low envelope observation contract

Date: `2026-09-27`
Status: `FROZEN AFTER HA-6B1 / BEFORE HA-6B2 MEASUREMENT / OBSERVATION ONLY`

## Why this follow-up exists

HA-6B1 found that raw-close EMA50 slope/position carries modest slower-horizon
context after prior HA/H1/raw-swing/HASTOC state, but is unsafe as an exit and
frequently opposes long right-tail Journeys. The same MQL5 source also uses a
20-period EMA on raw H4 High and Low as short-term boundaries. HA-6B2 isolates
that second mechanism rather than importing the combined source strategy.

## Fixed source semantics

From MQL5 Article 20851:

```text
EMA20_HIGH = iMA(symbol,H4,20,0,MODE_EMA,PRICE_HIGH)
EMA20_LOW  = iMA(symbol,H4,20,0,MODE_EMA,PRICE_LOW)
```

For an active Standard-H4 Journey:

```text
LONG  directional boundary = EMA20_HIGH
SHORT directional boundary = EMA20_LOW
beyond = HA_CLOSE > EMA20_HIGH (LONG)
         HA_CLOSE < EMA20_LOW  (SHORT)
```

Record the side-normalized percent distance from completed HA Close to the
relevant boundary. No numerical distance threshold is allowed. EMA20 is seeded
with the SMA of the first 20 raw H4 values; report sensitivity to first-value
seeding across the evaluation window.

## Question

Does HA Close extending beyond a causal raw-price EMA20 extreme envelope add
local continuation/transition information beyond H4 morphology, ordered H1,
HA-5 raw swing, HA-6A HASTOC and HA-6B1 EMA50 context?

## Comparisons

- overall and continuation-only beyond/not-beyond state;
- equal-count quintiles of side-normalized boundary distance;
- next-H4 flip, three-H4 flip, peak-already-past, remaining excursion/giveback;
- overlap within H4 body/raw-close, Delta/wick, H1 path, HA-5 state, HASTOC and
  finally EMA50 slope/position context where support remains;
- year/side and Journey birth/continuation diagnostics;
- >=10-bar Journey warning/tail accounting.

## Exclusions

No EMA20 period grid, no EMA50+EMA20 combined trade rule, no crossover event,
no entry/exit/SL/TP/sizing/Child change, and no MT5 economic claim.
