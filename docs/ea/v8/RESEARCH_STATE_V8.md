# V8 Research State

Status: `ACTIVE / V8-A FROZEN + INTERNAL V8-B RESEARCH`
Date: `2026-08-31`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`

## V8-A — Movement probability

`FROZEN / POSITIVE OPEN-DEVELOPMENT EVIDENCE`

The portable 53-feature M1-derived model remains the active movement-intensity component.

It estimates:

```text
P(reach C0 +/-10.0 within 15m/30m/60m)
```

It is not a LONG/SHORT or trade-win probability.

## V8-B1

`INVALIDATED_BY_HTF_LOOKAHEAD / CLOSED`

The previously high conditional direction AUC cannot be used.

Strictly causal realignment reduced the broad direction result toward chance in later development years.

## External source-of-move branch

`DE-SCOPED / HISTORICAL PROPOSAL`

External/cross-market research is not the active branch after the user chose to continue with GOLD-internal information plus frozen V8-A.

## Internal V8-B research

`ACTIVE RESEARCH / NO DIRECTION AUTHORITY`

Research performed after B1 invalidation:

- V8-A probability snapshot and trajectory;
- probability slopes/acceleration/hazard shape;
- price + probability joint sequences;
- TCN joint-sequence model;
- event-centered causal geometry;
- causal volatility/probability regime canonicalization;
- directional semivariance/body/wick/activity features;
- V8-A + directional-activity interaction;
- score fusion and stacking;
- all-M5 direction training controls;
- recent-year / rolling retraining controls;
- event-family diagnostics;
- selective confidence tails;
- exact independent rebuild;
- delayed-event posterior diagnostics with mandatory recenter correction.

## Current result

No tested internal representation has demonstrated a stable broad direction edge across 2024 -> 2025 -> 2026.

Promising 2024 results repeatedly weakened in 2025 and approached chance in 2026.

The independently reconstructed selective direction model produced approximately:

```text
30m AUC: 2025 0.533 / 2026 0.520
60m AUC: 2025 0.516 / 2026 0.506
```

Adding V8-A can materially increase the probability that a 10p move occurs, but this must not be confused with direction skill.

## Directional-excess rule

Use:

```text
directional_excess =
chosen_side_hit_rate - 0.5 * move_rate
```

as a mandatory companion metric.

High `chosen_side_hit_rate` with near-zero directional excess is movement filtering, not direction edge.

## Exact V8-A trajectory infrastructure

An exact continuous completed-M5 V8-A probability series was independently reconstructed for 2024-2026.

This enables causal tests of:

- current probability;
- 5/15/30/60-minute probability history;
- probability slope and acceleration;
- event interaction;
- sequential posterior state.

The final exact trajectory/event matrix is still the immediate unfinished internal diagnostic.

## Remaining active hypothesis

The most credible remaining internal-only formulation is not a forced one-shot LONG/SHORT classifier.

It is:

```text
event
-> V8-A says attention/movement state
-> WAIT when direction evidence is weak
-> observe new causal GOLD evidence
-> recenter C0 at the new decision
-> update/enter only if direction evidence appears
```

## Reserve

`GOLD# 2021 = LOCKED / UNTOUCHED`

No current direction candidate justifies consuming it.
