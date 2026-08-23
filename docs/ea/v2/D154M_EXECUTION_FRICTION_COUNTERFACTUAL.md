# D-154M — Execution-Friction Entry-Side Quote Counterfactual

Status: RESEARCH / SHADOW-ONLY  
Date: 2026-08-23  
Target build: `2.11R0L11`

## Question

How many actual Fill->+1R failures are caused by the executable exit-side quote crossing, rather than failure of the Entry-side market-price path itself?

## Actual observation

D151 remains authoritative:

```text
LONG  +1R/SL barrier observation = BID
SHORT +1R/SL barrier observation = ASK
```

## Shadow counterfactual

Use the same quote side as Entry:

```text
LONG  = ASK
SHORT = BID
```

Freeze:
- actual Fill price;
- original normalized SL;
- initial `1R`;
- exact +1R price;
- actual tick stream.

This is **not** a synthetic zero-spread mid-price test. It is an `ENTRY_SIDE_QUOTE_BARRIER_RACE`.

## Primary output

For every actual Fill pair:

```text
actual outcome
shadow outcome
pair class
```

Key pair:

```text
ACTUAL_SL_TO_SHADOW_PLUS_1R
```

This quantifies actual SL-first cases whose Entry-side quote path reached +1R before reaching the same original SL.

## Integrity property

Under correct quote ordering:

```text
actual PLUS_1R -> shadow PLUS_1R
```

must hold. `ACTUAL_PLUS_1R_TO_SHADOW_SL` is treated as an integrity warning.

## Test panel

After GOLD/CADJPY Q1 OFF/ON parity:

```text
GOLD23
GOLD24
GOLD25
BTC25
SILVER25
CADJPY25
```

## Prohibited inference

D154M does not authorize:
- zero-spread assumptions;
- spread threshold filters;
- symbol exclusions;
- SL widening;
- +1R target changes;
- Entry changes;
- sizing/SP/EM changes.

If quote-side flips are large and monotonic with D154L cost scale, a later preregistered strategy/execution-design phase may be considered.
