# V8 Development Handoff

Last updated: `2026-09-02`
Current phase: `V8-A-N-SLOW / DOWNSTREAM REVALIDATION IN PROGRESS`
Production authority: `NONE`
Market: `GOLD#`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`
Base Git HEAD for this update: `cfb286b1947ccb77e5e907caa9e96b26af314654`

## 1. Current problem definition

Legacy M5-A-N:

```text
barrier = 1.50 * causal pre-decision M5 ATR14
```

is retained only as historical M5-volatility-relative movement research.

Active intended probability contract:

```text
decision = completed M5 close timestamp

H4 block = block containing decision
scale = Wilder ATR14 from the immediately previous completed H4 bar
T = 0.25 * scale
T stays fixed for the whole H4 decision block

P15 = P(reach +/-T within 15m)
P30 = P(reach +/-T within 30m)
P60 = P(reach +/-T within 60m)
```

The H4 choice remains provisional but is the current primary balance candidate.

## 2. Probability probe — corrected current numbers

A horizon-eligibility mismatch was found during independent reconstruction. After restoring the correct requirement that the full future label window is available, the original Slow-N probe was reproduced closely.

### Phase-0

| Year | Eval N | AUC15 | P15>=75 N | P15>=75 actual | fresh75 N | fresh75 actual |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 67,954 | .81394 | 3,399 | 82.61% | 653 | 78.10% |
| 2025 | 67,582 | .76483 | 2,230 | 81.21% | 535 | 78.50% |
| 2026 | 44,605 | .77681 | 1,262 | 80.43% | 321 | 76.01% |

### Phase-2 robustness model

| Year | Eval N | AUC15 | P15>=75 N | P15>=75 actual | fresh75 N | fresh75 actual |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 67,954 | .81507 | 3,341 | 83.30% | 733 | 80.22% |
| 2025 | 67,582 | .76485 | 2,185 | 80.87% | 579 | 76.34% |
| 2026 | 44,605 | .77583 | 1,161 | 81.14% | 292 | 78.08% |

Fresh75 identity sensitivity:

```text
Phase-0 N1509
Phase-2 N1604
intersection N1133
Jaccard 57.22%
```

Interpretation: probability ranking/calibration is fairly stable at aggregate level, but exact fresh-cross membership is model-realization sensitive. Use cross-phase robustness as a downstream gate.

## 3. Downstream transfer — failures

| Method | Current Slow-N result | Decision |
|---|---|---|
| Legacy deterministic 7-voter | P0 51.73 / 54.08 / 50.00%; P2 49.17 / 56.79 / 49.83% | FAIL |
| M5 Stoch standalone | P0 47.96 / 51.99 / 54.46%; P2 46.25 / 53.79 / 51.92% | FAIL |
| Market-question equal panel | 50.94 / 53.51 / 48.41% | FAIL |
| Immediate pressure | 49.69 / 51.80 / 47.45% | FAIL |
| Oscillator transition | 50.00 / 52.18 / 51.59% | FAIL |
| M15 structure | 50.94 / 53.51 / 54.14% | FAIL |
| H1 structure | 48.27 / 52.75 / 53.18% | FAIL |
| H4 structure | 51.10 / 52.37 / 52.87% | FAIL |
| HTF regime | 52.04 / 49.72 / 54.14% | FAIL |
| Volatility transition | 50.63 / 54.08 / 50.00% | FAIL |
| Location/liquidity | 49.06 / 52.18 / 50.00% | FAIL |
| M1 tape proxy | 50.16 / 53.51 / 50.32% | FAIL |
| M1 recent direction | 48.90 / 51.99 / 50.00% | FAIL |
| M1 pressure | 51.10 / 53.32 / 53.18% | FAIL |
| M1 Stoch standalone | 51.10 / 47.63 / 51.59% | FAIL |
| M1 EMA3/8 | 51.89 / 52.94 / 48.41% | FAIL |
| Old asymmetric MTF state | UP 36.36 / 50.00 / 63.64% | FAIL / relation reversal |
| BB-A | DOWN 50.00 / 55.56 / 58.33% | FAIL |
| BB-C | DOWN 57.14 / 61.90 / 33.33% | FAIL / 2026 reversal |
| BB-D | UP 52.94 / 52.63 / 54.17% | FAIL |
| Generic raw-tick panel on overlap only | 50.86 / 52.32 / 52.17%, pooled 51.67% | FAIL |

Do not continue threshold/weight search on these failures.

## 4. Positive candidate — BB-B

Definition is frozen from legacy research, not redesigned on Slow-N:

```text
prior residence = MID
trigger closes OUT_U
abs normalized SMA-gap path = AWAY
predict UP
```

Primary n=5:

```text
Phase-0:
2024 N34 58.82
2025 N17 76.47
2026 N13 69.23
ALL N64 65.63%

Phase-2:
2024 N34 64.71
2025 N18 66.67
2026 N11 63.64
ALL N63 65.08%
```

Window robustness:

```text
Phase-0 n3: 55.56 / 70.00 / 57.14
Phase-0 n5: 58.82 / 76.47 / 69.23
Phase-0 n8: 66.67 / 71.43 / 62.50

Phase-2 n3: 55.17 / 61.54 / 58.33
Phase-2 n5: 64.71 / 66.67 / 63.64
Phase-2 n8: 71.43 / 60.00 / 71.43
```

All 18 year x phase x window cells are above 50%.

Status: `STRONG DEVELOPMENT CANDIDATE / NOT VALIDATED / SMALL SAMPLE`.

## 5. Positive hypothesis — Stoch/M1/tick re-synchronization

Current raw tick data cover only the intersection between new Slow-N events and the old tick-instrumented N1 ledger.

Resolved overlap rows: `N418`.

Predefined aligned tick state `0001` following M5 Stoch D:

```text
2024 N18 61.11%
2025 N20 70.00%
2026 N7  71.43%
ALL  N45 66.67%
```

Shifted -10m placebo `0001`:

```text
ALL N40 45.00%
```

Nested M1 observations:

```text
+ M1 recent counter-move                       N26 65.38%
+ M1 Stoch aligned with M5 D                   N14 85.71%
+ M1 Stoch opposite ~3m earlier -> now aligned N10 90.00%
```

Status: `PROMISING MECHANISM / INSUFFICIENT COVERAGE`.

Do not quote 85-90% as an edge. The correct next test is full raw-tick extraction for all new N1 decisions.

## 6. Reproducibility finding

Legacy M1 confirmed-structure state could not be reproduced exactly from the retained documentation/package. A new reconstruction reached only ~85% state-label parity.

Treat this as an instrumentation/reproducibility defect.

Do not use old `M1 structure == N2-R1` percentages as Slow-N evidence until:

1. original generator is recovered, or
2. a new explicit state definition is frozen and treated as a new experiment.

## 7. MT5 research indicator

New file:

`mt5/indicators/V8SlowNP15ContextIndicator.mq5`

Purpose:

- Phase-0 Slow-N P15 line, 0-100;
- user-set P15 threshold horizontal line;
- main-chart arrows when P15 meets the selected level/fresh-cross condition;
- H4 ATR14 causal percentile rank, 0-100;
- `abs(M5 close-SMA20) / SlowTarget` causal percentile rank, 0-100.

Critical target alignment:

```text
source M5 11:55 -> decision 12:00
decision belongs to H4 block starting 12:00
use ATR14 from H4 bar that ended at 12:00
T = 0.25 * that ATR
```

No partial current H4 is used.

The embedded Phase-0 model is **research-only** because the official full Slow-N model architecture is not yet frozen.

## 8. Next work

1. full new-N1 raw tick extraction using V4 wall-clock alignment;
2. aligned vs -10m placebo;
3. exact old `0001` transfer test on full population;
4. M1 Stoch alignment/transition on full population;
5. native Slow-N Path Clearance;
6. BB-B x temporal-transition interaction;
7. recover/freeze M1 structure generator;
8. multiplicity and near-miss audits;
9. freeze direction only after these tests;
10. exits/economics remain closed;
11. 2021 remains locked.

## 9. Files

Read next:

1. `V8_A_N_SLOW_DOWNSTREAM_REVALIDATION_RESULT_20260902.md`
2. `V8_A_N_SEMANTIC_RESET_AND_SLOW_SCALE_RESEARCH_20260902.md`
3. `V8_A_N_LEGACY_DOWNSTREAM_REVALIDATION_MAP_20260902.md`
4. `DECISIONS_V8_SLOW_N_RESET_ADDENDUM_20260902.md`
