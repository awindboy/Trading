# V4 Research State

Status: `ACTIVE`
Phase: `V4-001A CAUSAL PATCH REPRESENTATION BASELINE`
Date: `2026-08-27`

## Current research question

Can a compact learned representation of causal multi-resolution, multi-market broker data extract stable
out-of-sample predictive information that was not recoverable from the hand-authored V3 state variables?

The first question is information, not profit optimization.

## Current classification

```text
V1 deterministic EA                     FROZEN CONTROL
V2 continuation/SP/execution line       PAUSED / PRESERVED
V3 raw-event deterministic line         PAUSED / NEGATIVE AUTHORITY
V3 Candidate B                          FAILED INDEPENDENT VALIDATION
V4 AI-native research                   ACTIVE

V4-001 causal dataset                   PREPARED BY CODE / BUILD NEXT
V4-001 learned representation           ACTIVE NEXT
V4-001 cost-aware controller            LOCKED UNTIL REPRESENTATION TEST
V4-002 sequential RL                    DEFERRED
external-market V4 validation           CLOSED
GOLD# 2021 temporal confirmation        UNTOUCHED
production AI inference                 NOT AUTHORIZED
```

## What V4-001 is deliberately testing

It tests whether the model can learn latent market state without receiving the V3 strategy ontology as truth.

Base information:
- OHLC geometry;
- tick volume;
- spread;
- causal volatility scale;
- market availability/staleness;
- time of week/day;
- multiple causal bar resolutions;
- simultaneous context markets.

Not in the first feature set:
- Candidate A;
- H/L membership;
- sweep/BOS/FVG gates;
- discretionary mentor labels;
- outcomes from 2022/2021.

## Development data

```text
GOLD#    2023-2025
BTCUSD#  2023-2025
XAUEUR#  2023-2025
USDJPY#  2023-2025
```

These data may be used for architecture research, ablation and internal cross-validation only.

## Validation data

Cross-market V4 validation remains unopened:

```text
XAUJPY# / XAUCNH# / GAUCNH# / GAUUSD# 2023-2025
```

GOLD# 2021 remains final untouched temporal confirmation.

## No-authority list

No current result authorizes:
- V4 live or paper trading;
- MT5 Entry/SL/TP/sizing changes;
- black-box inference inside the EA;
- external validation-data inspection;
- leverage/risk sizing;
- RL training as a rescue for absent predictive information.
