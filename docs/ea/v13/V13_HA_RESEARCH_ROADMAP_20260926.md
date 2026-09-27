# V13 Heikin-Ashi research roadmap

Original roadmap date: `2026-09-26`
Current synchronization: `2026-09-28`
Status: `HA-0..HA-8 CONSUMED / HA-9 ACTION CANDIDATE ACTIVE`

## 1. Objective amendment

The original roadmap began by prioritizing preservation of large right-tail
Journeys when testing warnings/filters. The current objective has been clarified.
See `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`.

Current first-order objective:

> reduce ordinary losing Children and persistent downward stretches enough that
> the typical trade stream becomes more consistently upward.

Right-tail damage remains reported, but is no longer an automatic rejection
criterion.

## 2. Common protocol

Every stage/action must:

- use causal completed information only;
- preserve the frozen Baseline-0 comparator;
- use full 2024-01-01..2026-08-28 consumed history for primary development
  comparisons;
- keep year/side diagnostics visible without mining exceptions;
- preserve Journey and Child grain separately;
- keep decision/action inputs separate from future outcomes;
- avoid hidden thresholds, side balancing, cooldowns or hindsight recovery;
- report both traditional economics and ordinary-stream quality.

Current ordinary-stream quality metrics:

```text
loss count/share
non-flat win rate
max consecutive losses
chronological trade-stream drawdown
10/25/50/100-trade block positive share and median P/L
year stability
Top-N profitable-Journey-trimmed P/L
```

## 3. Consumed roadmap stages

### HA-0..HA-2 — standard HA measurement/lifecycle
Completed. Established morphology, lag and giveback anatomy.

### HA-3 — alternate HA representations
Completed. No representation promoted.

### HA-4 — multi-timeframe standard HA
Completed. H1 ordered path informative; D1 weak.

### HA-5 — causal raw structure
Completed. Useful description, insufficient action selector.

### HA-6 — complementary families
Completed HASTOC, MA, ATR normalization, ADX/DMI and tick participation studies.
No single family earned an action rule.

### HA-7 — first action
Completed and rejected: persistent-H1-opposition + high relative activity Child
veto. Historical right-tail damage remains part of that receipt, but current
objective interpretation is superseded by the 2026-09-28 objective update.

### HA-8 — state/economic modeling
Completed first combination model and external X1/X2 observations. More complex
feature/model stacking did not produce the desired loss-frequency step change.

## 4. HA-9 — runtime proof/lock action

Current active stage.

Instead of predicting whether an add-on will fail, allow the Child to enter and
require actual raw price to prove continuation during one H4. If proved, protect
the achieved breakout level; if not proved, close the Child at the H4 boundary.

This is the first consumed-data action showing a large shift in ordinary trade
quality:

```text
losses 2,427 -> 1,685
non-flat win rate 37.08% -> 56.07%
trade-sequence DD 3,756.99 -> 1,283.65
max loss streak 25 -> 14
```

## 5. Next roadmap gate

Before HA-10 or any new indicator/model branch:

1. compile HA-9 EA;
2. actual-tick canonical-window test;
3. event parity versus causal research ledger;
4. explain execution deltas;
5. if mechanism survives, analyze remaining losses and only then decide whether
   sizing/capital or another structural action deserves study.

Do not optimize proof duration/offsets on the same consumed data as the next
step.
