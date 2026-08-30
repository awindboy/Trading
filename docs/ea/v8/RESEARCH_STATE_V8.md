# V8 Research State

Status: `ACTIVE / V8-A FROZEN + V8-B1 INVALIDATED + V8-B2 PREFLIGHT`
Date: `2026-08-31`
Current phase: `V8-B2 SOURCE-OF-MOVE CAUSAL DIRECTION`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`

## Branch map

### V8-A — Movement probability

`FROZEN / POSITIVE OPEN-DEVELOPMENT EVIDENCE`

Target:

```text
P(price reaches completed-M5 close +/-10.0 within H)
H in {15,30,60}
```

Portable MT5 event-subset AUC remains recorded as approximately:

```text
15m: 0.865 / 0.873 / 0.815
30m: 0.844 / 0.851 / 0.796
60m: 0.807 / 0.829 / 0.781
```

V8-A is direction-free and unaffected by the B1 invalidation.

### V8-B1 — Conditional endogenous direction

`INVALIDATED_BY_HTF_LOOKAHEAD / CLOSED`

The previously committed high direction AUC used future-completed M15/H1 bars for many intrabar decisions.

Leak prevalence:

```text
M15 67.78%
H1  90.20%
```

After strict causal realignment:

```text
completed-only 30m AUC: 0.579 / 0.537 / 0.521
completed-only 60m AUC: 0.530 / 0.514 / 0.511
```

A causal current-partial M15/H1 reconstruction also fails to restore the edge.

The B1 coefficient artifact is historical invalidated evidence only and must not be deployed.

### V8-B2 — Source-of-move causal direction

`PRE-REGISTERED / RAW EXTERNAL DATA NOT CURRENTLY MOUNTED`

Purpose:

Test whether a compact external context tied to a specific failure mechanism adds directional information beyond corrected GOLD-only input while V8-A remains frozen.

Initial sources:

- USDJPY# — primary USD/rate-pressure proxy;
- XAUEUR# — primary cross-gold / USD-translation separator;
- BTCUSD# — negative-control risk/sentiment context.

Full contract:

`V8_B2_SOURCE_OF_MOVE_RESEARCH_CONTRACT.md`

## Causal-alignment authority

For every V8 branch:

```text
completed bar is observable only if
bar_start + timeframe_duration <= decision_time
```

A current partial HTF bar may be used only when reconstructed from lower-timeframe observations available before the decision.

Bar-start timestamp alone is never sufficient proof of availability.

## Validation reserve

```text
GOLD# 2021 = UNTOUCHED / LOCKED
```

No V8-B result currently authorizes opening it.

## Current required documents

- `V8_B1_CAUSAL_ALIGNMENT_INVALIDATION.md`
- `V8_B2_SOURCE_OF_MOVE_RESEARCH_CONTRACT.md`
- `V8_005_MOVEMENT_PROBABILITY_INDICATOR.md`
- `V8_RESEARCH_JOURNEY.md`
- `DECISIONS_V8.md`
- `HANDOFF_V8.md`
