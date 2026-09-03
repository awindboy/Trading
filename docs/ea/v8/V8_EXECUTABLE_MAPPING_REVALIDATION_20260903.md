# V8 Executable Mapping Revalidation — 2026-09-03

Status: `OPEN-DEVELOPMENT REVALIDATION / NO PRODUCTION AUTHORITY`
Market: `GOLD# ONLY`
Open evidence: `2024-2026` within the already-consumed GOLD# 2022-2026 development set
Untouched reserve: `GOLD# 2021`
Source Git HEAD verified before this documentation update: `636524efc0335b1569405cfed420e84549a0c4b9`
Raw M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Current working downstream ledger authority: `retention_competing075_ledger(1).csv`

## 1. Purpose

Recent V8 research accumulated several strong-looking statistical results, especially movement onset, structural retention and winner continuation. This revalidation forces one practical reporting rule:

> When a quantity has good AUC / hit-rate / structural separation, report what happens when that information is mapped into an executable trading rule.

Statistical discrimination and trading profitability are therefore reported together. AUC alone is not trading edge.

## 2. P0/P2 correction

`P0` and `P2` are alternate deterministic **training-sample de-overlap realizations**. They are not execution phases that restrict inference/trading to one M5 residue.

The trained Slow-N model is applied across the full modelable M5 population. Current P0 fresh75 events are distributed across all `m5_index % 5` residues.

Therefore the existing P0 replay did **not** trade only one-fifth of M5 decisions.

P2 remains a robustness realization. Do not opportunistically merge P0 and P2 into one account.

## 3. Current P0 event funnel

Using the current revalidated P0 full-M5 inference population:

| Stage | 2024 | 2025 | 2026 | Total |
| --- | ---: | ---: | ---: | ---: |
| P0 fresh75 | 653 | 535 | 321 | **1,509** |
| actual +/-0.25S touch within 15m | 510 | 420 | 244 | **1,174** |
| <=15m M1-close reveal | 426 | 361 | 211 | **998** |
| 25% pullback fill diagnostic | 390 | 318 | 193 | **901** |
| full ACCEPTANCE | 279 | 236 | 153 | **668** |

Key rates:

- fresh75 -> actual +/-0.25S touch within 15m: `77.8%`.
- reveal -> 25% pullback fill: `90.3%`.
- 25% pullback fill -> full ACCEPTANCE: `74.1%`.

ACCEPTANCE remains:

```text
fresh75
-> <=15m +/-0.25S M1-close reveal
-> >=25% pullback
-> origin retained
-> M1-close reclaim
```

Among the 668 ACCEPTANCE events, 316 (`47.3%`) had pullback and reclaim inside the same M1 bar. These events must not simply be dropped. Same-M1 ambiguity remains an M1 replay limitation and ultimately requires real-tick MT5 confirmation.

## 4. Blind pullback and direct reclaim economics

### 4.1 Blind 25% pullback, symmetric +/-0.25S

Diagnostic policy:

```text
reveal
-> 25% pullback fill
-> TP +0.25S from entry
-> SL -0.25S from entry
```

Without spread:

- N `901`
- WR `50.06%`
- mean R approximately `+0.001R`
- PF approximately `1.002`

With causal M1 spread treatment:

| Year | N | WR | Avg R | PF |
| --- | ---: | ---: | ---: | ---: |
| 2024 | 390 | 43.3% | -0.133R | 0.765 |
| 2025 | 318 | 51.6% | +0.031R | 1.065 |
| 2026 | 193 | 51.8% | +0.036R | 1.075 |
| **Total** | **901** | **48.1%** | **-0.039R** | **0.925** |

Verdict: the high pullback/acceptance transition rate is real, but blind pullback is not a robust symmetric directional trade.

### 4.2 Trade the ACCEPTANCE reclaim itself

Diagnostic policy:

```text
25% pullback entry
-> TP = original +/-0.25S reveal/reclaim level
-> SL = origin
```

With spread:

| Year | N | Economic WR | Avg R | PF |
| --- | ---: | ---: | ---: | ---: |
| 2024 | 390 | 63.1% | -0.021R | 0.820 |
| 2025 | 318 | 73.0% | +0.067R | 2.218 |
| 2026 | 193 | 68.9% | +0.062R | 2.008 |
| **Total** | **901** | **67.8%** | **+0.028R** | **1.339** |

Average winner is only about `+0.162R`.

Verdict: `pullback -> reclaim` is a genuine state transition, but the payoff is too small to satisfy the final V8 objective by itself.

## 5. Routine Base control

Frozen Base:

```text
ACCEPTANCE
-> next executable M1 open
-> TP +0.25S
-> SL -0.25S
```

| Year | N | WR | Avg R | PF(R) |
| --- | ---: | ---: | ---: | ---: |
| 2024 | 279 | 44.8% | -0.104R | 0.812 |
| 2025 | 236 | 52.5% | +0.051R | 1.107 |
| 2026 | 153 | about 49% | -0.014R | 0.973 |
| **Total** | **668** | **48.5%** | **-0.029R** | **0.944** |

The realistic chronological account replay attributed about `-$31.85` to Base.

This is an entry/economic-mapping failure of the routine Base. It does not invalidate movement onset, structural retention or winner continuation as separate phenomena.

## 6. Structural retention: strong phenomenon, unproven direct entry selector

### 6.1 Ex-post structural outcome versus Base

Descriptive only; future structural outcome is not known at entry.

| Future 15m structural outcome | N | Base WR | Approx Avg R |
| --- | ---: | ---: | ---: |
| retained | 224 | **86.2%** | **+0.727R** |
| not retained | 444 | **29.5%** | **-0.410R** |

Using actual 15m M1-close integrity:

- close-intact N `277`: Base WR about `84.1%`.
- close-broken N `391`: Base WR about `23.3%`.

Therefore future structural survival is economically highly relevant. The problem is causal identification early enough to trade it.

### 6.2 micro3 AUC versus actual Base selection

`micro3 = prog1 + run_accept + prog3` remains a causal acceptance-time structural-retention ranking prior.

Current later-year retention AUC is approximately:

- 2025: `0.729`
- 2026: `0.735`

But a high micro3/retention-ranking subset used as direct Base permission did not create a profitable selector:

| Year | Selected N | Base WR | Avg R | PF |
| --- | ---: | ---: | ---: | ---: |
| 2025 | 50 | 44.0% | -0.120R | 0.786 |
| 2026 | 40 | 45.0% | -0.100R | 0.818 |
| **Combined** | **90** | **44.4%** | **-0.111R** | **0.800** |

A structural-stop mapping also remained negative:

- 2025 N50, WR 44.0%, mean about `-0.070R`, average winner about `+1.11R`.
- 2026 N40, WR 42.5%, mean about `-0.081R`, average winner about `+1.16R`.

Verdict:

```text
micro3 = useful structural-retention predictor
micro3 != proven direction/economic entry selector
```

## 7. Simple close-break exit mapping

Causal diagnostic:

```text
hold frozen Base
-> if M1 close breaches acceptance pullback extreme
-> exit at next M1 open
```

Across 668 Base events:

- WR about `38.5%`
- mean about `-0.043R`
- PF about `0.900`
- average loss improved from roughly `-0.997R` to `-0.694R`

Loss severity improves, but expectancy is worse than frozen Base.

Verdict: close damage is a valid hazard state, but `CLOSE_BROKEN -> unconditional immediate exit` is not validated.

## 8. Early realized progress: strong target AUC, unstable standalone trade

Among t10 close-intact events, realized MFE by 10m strongly ranks whether the event becomes the frozen t15 High-Q state.

| Year | t10 close-intact N | eventual t15 High-Q | AUC |
| --- | ---: | ---: | ---: |
| 2024 | 129 | 28 | 0.931 |
| 2025 | 125 | 22 | 0.964 |
| 2026 | 71 | 11 | 0.947 |

A diagnostic standalone policy using approximately `MFE10 >= 0.370S` plus close integrity and entering around t10 produced:

| Year | N | WR | Avg R | PF |
| --- | ---: | ---: | ---: | ---: |
| 2024 | 41 | 56.1% | +0.102R | 1.575 |
| 2025 | 34 | 41.2% | -0.019R | 0.909 |
| 2026 | 16 | 62.5% | +0.485R | 3.321 |
| **Total** | **91** | **51.6%** | **+0.124R** | **1.643** |

Verdict: AUC is strong for the future-state target, but the simple t10 standalone execution rule is not year-stable because 2025 is negative. Do not promote it.

## 9. High-Q runner remains the strongest executable component

Frozen runner control:

```text
ACCEPTANCE + 15m
M1-close structure intact
MFE15 >= 0.555S
-> next executable M1 open
-> TP +0.75S
-> SL -0.40S
-> current control horizon 60m
```

P0 fixed-0.01 diagnostic:

| Year | N | WR | Avg stop-R |
| --- | ---: | ---: | ---: |
| 2024 | 28 | 42.86% | +0.071R |
| 2025 | 22 | 59.09% | +0.481R |
| 2026 | 11 | 45.45% | +0.450R |
| **Total** | **61** | **49.18%** | **about +0.287R** |

Aggregate:

- PF roughly `1.68-1.71` depending on dollar/R normalization.
- average winner roughly `+1.4R`.
- positive mean R in each year.
- N only `61`.
- aggregate WR remains below the user's >=50% final condition.

P2 robustness of the same semantic runner family:

- N `70`
- WR about `51.4%`
- mean about `+0.214R`
- PF about `1.53-1.56`
- average winner > `1R`.

P0/P2 are robustness realizations, not trades to merge.

## 10. Realistic chronological account replay decomposition

Frozen P0 account probe:

- starting balance `$1,000`
- routine Base 0.01 lot
- High-Q runner risk budget <=2% floating equity, 0.01 minimum/step
- leverage 1:1000
- causal M1 spread model
- overlapping positions allowed

| Component | Result |
| --- | ---: |
| Base P/L | **-$31.85** |
| Runner P/L | **+$250.21** |
| Combined ending balance | **$1,218.36** |
| Combined net | **+$218.36 / +21.84%** |
| Floating-equity MDD | **-21.85%** |
| Max concurrent positions | **2** |

The combined wrapper made money because runner gains more than offset the negative Base.

Runner-only 60m control was previously superior to paying on every ACCEPTANCE:

- ending balance about `$1,220.89`
- net about `+$220.89`
- floating MDD about `-9.86%`

This supports treating ACCEPTANCE as a causal observation state rather than automatically paying 0.01 lot merely to obtain information.

## 11. Mandatory AUC-to-trade reporting rule

From this point forward, any V8 report that cites AUC or another discrimination statistic for a state intended to influence trading must also state, when an executable mapping has been tested:

- exact target semantics;
- information availability time;
- executable action rule;
- N;
- WR;
- mean R / expectancy;
- PF;
- average winner and loser when meaningful;
- year breakdown;
- whether the result is descriptive, shadow-only, diagnostic, challenger, or frozen control.

If no executable mapping has been tested, explicitly state:

`NO EXECUTABLE TRADING RESULT YET`

Do not imply profitability from AUC alone.

## 12. Current synthesis

Supported mechanisms:

1. **Movement onset/opportunity is learnable.** P15 fresh75 materially enriches near-term +/-0.25S movement episodes.
2. **Structural survival/damage is learnable.** Retention and close-integrity states are real and economically associated with outcomes, but current acceptance-time ranking is not a proven direct Base permission rule.
3. **Winner continuation after realized progress is learnable.** The t15 High-Q runner is the strongest positive executable component so far.

Unresolved strategy problem:

```text
How should capital/exposure be mapped through
fresh75 -> reveal -> pullback -> acceptance -> early path -> runner-grade progress
without paying negative expectancy on every acceptance,
while preserving enough trade frequency and achieving
WR >=50%, average winner >1R, and positive cost-adjusted expectancy?
```

This is the active GOLD-only bottleneck.

## 13. Hard scope guardrails

- GOLD# only until the user explicitly declares GOLD complete or reopens another market.
- Do not touch GOLD# 2021.
- Do not reopen external-market/source-of-move work while GOLD-only freeze is active.
- Do not convert P15, retention AUC, micro3 or MFE AUC into direction permission without executable validation.
- Do not flatten all winners to 1R merely to satisfy WR.
- Keep Base as control when testing new action/exposure mapping.
- Prefer shadow-only first for new mappings.
