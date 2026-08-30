# V8 Development Handoff

Last updated: `2026-08-31`
GitHub base for this research cycle: `91060e20ee6e84df58ef4b17573824643d147088`
Current phase: `V8-B1 CONDITIONAL DIRECTION PROBABILITY / DEVELOPMENT FREEZE`
Production authority: `NONE`
EA authority: `NONE`
Direction trade authority: `NONE`
Market: `GOLD# only`
Untouched reserve: `GOLD# 2021`

## Current branch split

### V8-A — movement probability

`FROZEN`

Do not change:

- +/-10.0 GOLD price-unit movement barrier;
- 15m/30m/60m horizons;
- 53-feature causal movement representation;
- portable walk-forward logistic model family;
- historical model policy;
- MT5 probability semantics.

Primary artifact remains:

`mt5/indicators/V8MovementProbabilityIndicator.mq5`

V8-A estimates only whether a 10p move occurs within H. It remains direction-free.

### V8-B — direction probability

`POSITIVE OPEN-DEVELOPMENT EVIDENCE / NOT YET IMPLEMENTED IN MT5`

The old eventual +/-10 first-hit classifier is not reopened.

New formulation:

```text
p_H = V8-A P(any +/-10 move within H)
q_H = V8-B P(UP first | a move occurs within H)

P(UP within H)   = p_H * q_H
P(DOWN within H) = p_H * (1-q_H)
P(NO MOVE)       = 1-p_H
```

## Main research result

The original hypothesis that V8-A probability should be fed directly into the direction model was falsified.

Signed causal context without V8-A probabilities produced the best conditional side model.

All-prior-mover conditional AUC:

```text
15m: 2024 0.846 / 2025 0.866 / 2026 0.838
30m: 2024 0.895 / 2025 0.869 / 2026 0.823
60m: 2024 0.863 / 2025 0.842 / 2026 0.795
```

Outcome-blind non-overlap AUC:

```text
15m: 0.831 / 0.858 / 0.838
30m: 0.894 / 0.869 / 0.822
60m: 0.829 / 0.846 / 0.801
```

Week-block bootstrap intervals remain far above 0.5.

## Event-family boundary

Directional support currently survives for:

- M5 SMA20 contact-start;
- M5 BB20 upper contact-start;
- M5 BB20 lower contact-start.

H1 Double-B directional prediction failed:

```text
30m AUC ~0.475 / 0.481 / 0.484
60m AUC ~0.474 / 0.496 / 0.490
```

Therefore Double-B remains V8-A movement-only.

## Mechanism discovered

Recent H1 progression is the strongest single directional variable, but it does not explain all performance.

Example 30m mover AUC:

```text
H1 3-bar return alone: 0.798 / 0.745 / 0.681
full signed core:       0.895 / 0.869 / 0.823
```

M15/H1 context remains informative after removing shortest M1/M5-sensitive features. M5-only context is near chance.

## Important counter-result

Higher V8-A movement probability does not make side easier to predict.

At the highest movement-probability quintile, conditional side AUC falls materially, especially in 2026.

Therefore V8-A is not used as a direction gate/feature in V8-B1. It is used only to convert conditional side probability into joint UP/DOWN probability.

## Full-population validation

The high conditional AUC was checked against the future-selection objection by scoring every event as:

```text
NO MOVE / DOWN / UP
```

V8-A + V8-B consistently improved multiclass log loss versus the same frozen V8-A with historical-prior or 50:50 direction.

30m joint log loss:

```text
2024 0.126 vs 0.135 prior
2025 0.406 vs 0.439 prior
2026 0.789 vs 0.875 prior
```

60m:

```text
2024 0.272 vs 0.292
2025 0.611 vs 0.668
2026 0.878 vs 0.979
```

## Current research artifact

Read first:

`docs/ea/v8/V8_B_DIRECTION_PROBABILITY_RESULTS.md`

Frozen coefficient artifact:

`config/v8_b1_direction_models.json`

Then:

1. `docs/ea/v8/AGENTS_V8.md`
2. `docs/ea/v8/DECISIONS_V8.md`
3. `docs/ea/v8/RESEARCH_STATE_V8.md`
4. `docs/ea/v8/V8_RESEARCH_JOURNEY.md`
5. `docs/ea/v8/V8_005_MOVEMENT_PROBABILITY_INDICATOR.md`

## Immediate next task

Freeze the exact V8-B signed-feature equations and fit current walk-forward coefficients without changing the research contract.

Then implement a shadow-only MT5 extension that displays separately:

```text
V8-A P(move)
V8-B P(UP | move)
joint P(UP)
joint P(DOWN)
```

Double-B direction must remain blank/unsupported.

After Python/MQL parity and runtime audit, decide whether the V8-B candidate is mature enough to consume GOLD# 2021.

Do not open GOLD# 2021 before that freeze.
