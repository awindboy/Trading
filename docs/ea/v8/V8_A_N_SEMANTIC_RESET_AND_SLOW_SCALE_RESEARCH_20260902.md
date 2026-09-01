# V8-A-N Semantic Reset and Slow-Scale Movement Research — 2026-09-02

Status: `DEVELOPMENT RESEARCH / ACTIVE REPLACEMENT CANDIDATE / NOT FROZEN`
Market: `GOLD#`
Base Git HEAD (original semantic-reset study): `7344f8c3918a89e3fc6d30f1df64d90d567ecda5`
Current update base Git HEAD: `cfb286b1947ccb77e5e907caa9e96b26af314654`
Primary M1 source: `GOLD#_M1_202201030100_202608282357.csv`
Source SHA256 authority: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Reserve: `GOLD# 2021 LOCKED / UNTOUCHED`

## 1. Why this research was reopened

The original V8-A-N study correctly showed that a fixed $10 target has radically different volatility-relative difficulty across 2022-2026. It then defined:

```text
barrier = k * causal pre-decision M5 ATR14
```

That solved one statistical problem: ATR-multiple movement base rates were stable.

However, during MT5 visualization design a strategy-semantics problem became explicit:

```text
M5 ATR changes every completed M5 bar
=> the predicted barrier changes every five minutes
=> P15 no longer always asks about the same practical size of opportunity
```

The user's intended A-N role was different:

> ATR should correct broad era/regime differences in what counts as a meaningful movement, not continuously resize the target because the immediately preceding M5 volatility changed.

Therefore the old M5-A-N research is not “wrong math”; it answers the different question of volatility-relative excursion. The active strategy line now requires a slower volatility scale.

## 2. Research question

Find a causal slow scale that satisfies all of the following as well as possible:

1. adjusts the meaningful-move distance across large regime/era changes;
2. does not change the target every M5;
3. remains responsive enough to avoid stale D1-style lag;
4. makes P15 interpretable as the probability of a practically meaningful near-term move;
5. is mechanically causal and easy to reproduce in MT5;
6. is selected without LONG/SHORT outcomes or trade P/L.

## 3. Candidate scales tested

Simple interpretable scale anchors were used:

```text
legacy: 1.50 * M5 ATR14
H1:     0.50 * previous-completed H1 ATR14
H4:     0.25 * previous-completed H4 ATR14
D1:     0.10 * previous-completed D1 ATR14
fixed:  10 price units control
```

The H1/H4/D1 fractions are semantic/design anchors, not P/L-optimized thresholds. H4 0.25 was attractive because in the current 2026 regime its median target is approximately 10 price units while automatically scaling lower in earlier regimes.

## 4. Target-size and base-rate result

### M5 1.50ATR

| Year | Median target | 15m hit rate |
|---|---:|---:|
| 2022 | 1.74 | 34.54% |
| 2023 | 1.54 | 34.55% |
| 2024 | 2.23 | 34.71% |
| 2025 | 4.08 | 34.65% |
| 2026 | 8.03 | 33.56% |

Statistically stable, but target changes every M5.

### H1 0.50ATR

| Year | Median target | 15m hit rate |
|---|---:|---:|
| 2022 | 2.27 | 23.04% |
| 2023 | 2.06 | 22.99% |
| 2024 | 2.95 | 23.14% |
| 2025 | 5.04 | 23.13% |
| 2026 | 10.00 | 21.79% |

### H4 0.25ATR

| Year | Median target | 15m hit rate |
|---|---:|---:|
| 2022 | 2.33 | 22.07% |
| 2023 | 2.14 | 21.72% |
| 2024 | 3.03 | 22.02% |
| 2025 | 5.07 | 22.75% |
| 2026 | 10.09 | 20.68% |

### D1 0.10ATR

| Year | Median target | 15m hit rate |
|---|---:|---:|
| 2022 | 2.50 | 19.82% |
| 2023 | 2.37 | 18.27% |
| 2024 | 3.31 | 19.13% |
| 2025 | 5.21 | 22.37% |
| 2026 | 11.37 | 18.66% |

## 5. Target update stability

| Target | Change rate per M5 transition | Median absolute change when it changes |
|---|---:|---:|
| M5 1.50ATR | 100.00% | 2.10% |
| H1 0.50ATR | 8.34% | 2.48% |
| H4 0.25ATR | 2.18% | 2.51% |
| D1 0.10ATR | 0.36% | 1.93% |

This is the central semantic difference. H4 permits the market scale to evolve while holding the actual target constant through an approximately four-hour block.

## 6. Why H4 currently leads

H4 is **not** the top model on every numerical metric.

- H1 produced slightly stronger annual fresh75 precision in the lightweight probe.
- D1 produced higher AUC in that probe.
- D1, however, showed material quarter-level target-difficulty lag in 2026.
- M5 has the cleanest annual base-rate stability but violates the intended target semantics by updating every five minutes.

H4 is retained because it gives the best current balance of:

```text
slow enough not to chase M5 noise
fast enough not to become D1-stale
current target near the desired ~10p scale
stable 2022-2026 15m target difficulty
simple causal block semantics
```

This is a structural choice to formalize, not a final freeze.

## 7. Lightweight P15 survival probe

To test whether the slow target remains modelable, an A2-style 86-feature survival probe was run.

Probe methodology:

- target family changed according to each candidate scale;
- four first-hit-time classes retained;
- strict historical chronology retained conceptually;
- outcome-blind every-5th-M5 (~25-minute) training de-overlap used for speed;
- full modelable M5 evaluation states scored;
- 2024 / 2025 / 2026 evaluated chronologically;
- this is not the final official model pack.

### Model metrics

| Variant | Year | AUC15 | Base15 | P15>=75 hit | fresh75 N | fresh75 hit |
|---|---:|---:|---:|---:|---:|---:|
| FIXED10 | 2024 | .8790 | 1.04% | 40.00% N5 | 4 | 50.00% |
| FIXED10 | 2025 | .8692 | 7.33% | 72.11% N190 | 64 | 75.00% |
| FIXED10 | 2026 | .8273 | 28.78% | 86.04% N4707 | 610 | 71.31% |
| M5 1.50ATR | 2024 | .6996 | 35.41% | 80.10% | 685 | 81.75% |
| M5 1.50ATR | 2025 | .6720 | 35.18% | 79.30% | 477 | 81.76% |
| M5 1.50ATR | 2026 | .6713 | 34.14% | 81.79% | 413 | 80.39% |
| H1 0.50ATR | 2024 | .8019 | 23.82% | 82.82% | 604 | 79.97% |
| H1 0.50ATR | 2025 | .7546 | 23.81% | 82.19% | 454 | 82.38% |
| H1 0.50ATR | 2026 | .7579 | 22.34% | 80.99% | 275 | 79.27% |
| H4 0.25ATR | 2024 | .8142 | 22.64% | 82.73% | 648 | 78.55% |
| H4 0.25ATR | 2025 | .7650 | 23.40% | 81.46% | 531 | 78.53% |
| H4 0.25ATR | 2026 | .7770 | 21.18% | 80.58% | 323 | 76.47% |
| D1 0.10ATR | 2024 | .8306 | 19.66% | 83.52% | 537 | 76.16% |
| D1 0.10ATR | 2025 | .7984 | 22.97% | 84.25% | 511 | 80.82% |
| D1 0.10ATR | 2026 | .8203 | 19.05% | 85.93% | 310 | 77.10% |

## 8. Quarterly caveat

Annual summaries are not enough.

H4 fresh75 examples:

```text
2025Q3 ~71.32%
2026Q2 ~69.75%
```

D1 base-rate drift in 2026 was more severe:

```text
2026Q1 25.92%
2026Q2 14.43%
2026Q3 15.93%
```

Therefore H4 is promising, not solved.

## 9. Training phase sensitivity

The H4 probe's 25-minute training de-overlap phase was shifted from the original phase to offset 2.

Fresh75 hit on the alternate phase:

```text
2024 80.35%
2025 76.04%
2026 77.32%
```

The broad result persists. This reduces concern that the probe is an accident of one five-minute sampling phase, but does not replace a formal model rebuild.

## 10. Current research decision

Retain as provisional primary candidate:

```text
T(t) = 0.25 * ATR14_H4(previous completed H4 bar)
T fixed through the next H4 block
```

Do not yet call this the frozen new N1.

Before freeze:

1. formal causal HTF construction/unit audit;
2. full model rebuild or explicit de-overlap architecture decision;
3. calibration/quarter/month stress;
4. target-distance/block-clustering diagnostics;
5. movement-only fresh75 profile.

## 11. Consequence for prior research

The old M5-A-N downstream research cannot be inherited numerically.

Changing the movement scale changes:

- which M5 decisions become fresh75 events;
- target distance at each event;
- which side first reaches the movement barrier;
- interaction with M1/tick/chart states;
- execution/risk scale.

Therefore N2, M1, raw tick, Bollinger and N3 must be rerun on the new population.

Their old methods and frozen hypotheses are valuable precisely because they can now be tested without first redesigning them on the new population.

## 12. Reserve discipline

2022-2026 are consumed development evidence. No claim that Slow-N creates a new independent holdout.

`GOLD# 2021` remains locked until target, N1, direction and execution architecture are sufficiently frozen.

## 13. Rebuild correction — horizon eligibility

During downstream restart, the Slow-N label pipeline was independently reconstructed from the raw M1 source.

An initial ~0.2-0.3 percentage-point annual base-rate mismatch was traced to label-window eligibility rather than H4 target construction.

After requiring the complete future label horizon to exist and restoring the intended decision-time alignment, the lightweight H4 probe was reproduced closely.

Corrected Phase-0 model-evaluation metrics:

```text
2024 AUC15 .813936 / fresh75 N653 / actual 78.10%
2025 AUC15 .764832 / fresh75 N535 / actual 78.50%
2026 AUC15 .776809 / fresh75 N321 / actual 76.01%
```

This supersedes tiny count/metric differences in the first exploratory report. The semantic H4 target conclusion is unchanged.

## 14. Probability-model realization sensitivity

A second outcome-blind de-overlap phase was trained without using downstream direction/P&L.

```text
Phase-2 fresh75
2024 N733 / 80.22%
2025 N579 / 76.34%
2026 N292 / 78.08%
```

Aggregate discrimination remains similar, but exact fresh75 event identity is less stable:

```text
Phase-0 events 1509
Phase-2 events 1604
intersection 1133
union 1980
Jaccard 57.22%
```

Research consequence:

> downstream direction evidence must be robust to reasonable probability-model realizations, not only to calendar years.

This is now an additional development gate.

## 15. Phase-0 MT5 shadow implementation

A research-only indicator is now permitted before final model freeze because its purpose is manual chart inspection and Python/MQL parity work, not strategy authority.

File:

`mt5/indicators/V8SlowNP15ContextIndicator.mq5`

It embeds the Phase-0 probe model and uses the exact Slow-N target alignment:

```text
source M5 closes at decision
decision determines current H4 block
use ATR14 from immediately previous completed H4 bar
T = 0.25 * ATR14
```

The indicator is explicitly labeled `PROBE / NO PRODUCTION AUTHORITY`.

The final official Slow-N model, when frozen, must replace this probe pack rather than silently inheriting it.

