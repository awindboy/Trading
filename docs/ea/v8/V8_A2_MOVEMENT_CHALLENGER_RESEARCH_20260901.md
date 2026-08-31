# V8-A2 Movement Probability Challenger Research — 2026-09-01

Status: `RESEARCH COMPLETE / CHALLENGER RETAINED / NOT PROMOTED`

Authority:
- current V8-A remains `FROZEN / CONTROL / MT5 SHADOW AUTHORITY`;
- V8-A2 does not replace the current V8-A model pack or indicator;
- GOLD# 2021 remains untouched reserve;
- 2022-2026 are consumed/open-development evidence.

## 1. Research question

Can the direction-free V8-A movement model be made materially more accurate and more trustworthy in future regimes, with special attention to overfit-resistant validation and a possible 90% high-confidence operating zone?

The target remains unchanged:

```text
C0 = causal completed decision price
barrier = +/-10 GOLD price units
H = 15m / 30m / 60m
movement = either barrier reached within H
```

No direction target is introduced.

## 2. Data and population

Primary M1 source:

```text
GOLD#_M1_202201030100_202608282357.csv
SHA256 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
```

Factual V8 event census rebuilt from source data:

```text
66,277 unique event decisions
66,235 modelable after historical-feature availability
```

Outer chronological evaluation population:

```text
2024 N=14,294
2025 N=13,958
2026 N=9,352 through 2026-08-28
```

## 3. Validation policy

Primary validation remains chronological future-year evaluation:

```text
2024 <- past only
2025 <- past only
2026 <- past only
```

Inner validation uses blocked chronological folds. Random K-fold is not authority.

All label-resolution boundaries are purged. For the multi-horizon survival challenger the strict rule is:

```text
training row eligible only if decision + 60m <= evaluation cutoff
```

This is required even when reading the 15m or 30m output from the survival model.

An audit during research found that an early exploratory survival/stack implementation had used the requested output horizon rather than the full 60m survival-label boundary. That exploratory stack/selective output is not authority. The strict model pack and reported survival results below were regenerated with the full 60m purge.

## 4. Frozen V8-A control reproduction

AUC:

| H | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| 15m | 0.85656 | 0.87146 | 0.81772 |
| 30m | 0.84184 | 0.85261 | 0.79766 |
| 60m | 0.80676 | 0.83161 | 0.78685 |

The control remains strong enough that improvement must be judged against it, not against a naive classifier.

## 5. Explicit barrier-difficulty / regime representation

Thirty-three direction-free features were added to the original 53-feature movement representation. They express fixed-barrier difficulty and relative movement regime, including forms such as:

```text
10 / rolling high-low
10 / realized-volatility scale
rolling range / 10
volatility scale / 10
activity rate
path-to-range
short/long range, volatility and activity ratios
```

AUC:

| H | Year | V8-A control | Regime logit |
|---|---:|---:|---:|
| 15m | 2024 | 0.85656 | 0.86276 |
| 15m | 2025 | 0.87146 | 0.87422 |
| 15m | 2026 | 0.81772 | 0.81873 |
| 30m | 2024 | 0.84184 | 0.84712 |
| 30m | 2025 | 0.85261 | 0.85664 |
| 30m | 2026 | 0.79766 | 0.79955 |
| 60m | 2024 | 0.80676 | 0.81310 |
| 60m | 2025 | 0.83161 | 0.83813 |
| 60m | 2026 | 0.78685 | 0.79276 |

Ranking AUC improved in all 9 year/horizon cells. Probability calibration did not improve uniformly, so these features are a representation improvement clue, not automatic deployment authority.

## 6. Multi-horizon survival challenger

Instead of fitting three unrelated binary models, V8-A2 models first-hit time as four classes:

```text
0: +/-10 hit within 15m
1: first hit during 15-30m
2: first hit during 30-60m
3: no hit by 60m
```

Outputs are structurally nested:

```text
P15 = P(class 0)
P30 = P(class 0 or 1)
P60 = P(class 0 or 1 or 2)
```

The reproducible research pack uses:

```text
86 inputs = original 53 + regime 33
StandardScaler
multinomial regularized logistic regression
C = 0.5
strict 60m purge
```

Audited research-pack AUC:

| H | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| 15m | 0.86601 | 0.87362 | 0.81902 |
| 30m | 0.85008 | 0.85654 | 0.79990 |
| 60m | 0.81298 | 0.83842 | 0.79252 |

The survival challenger also beats the frozen control in all 9 cells, but the absolute improvement is modest. It is retained as a research challenger, not promoted to MT5 authority.

## 7. Cross-validation result and the 90% lesson

Blocked chronological development folds sometimes produced 15m AUC above 0.90. For example, before the 2024 outer year the regime-logit blocked-CV mean was about 0.9045 and the best fold was about 0.9370.

The actual future 2024 AUC was only 0.8628 for the same regime representation.

Therefore:

```text
CV AUC >= 0.90
!=
future-year AUC >= 0.90
```

CV is an architecture-selection and fragility diagnostic. It cannot convert already-consumed development history into untouched evidence.

## 8. Why raw accuracy is the wrong 90% objective

Observed movement base rates changed dramatically:

| H | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| 15m | 1.16% | 8.05% | 29.45% |
| 30m | 3.21% | 16.77% | 48.61% |
| 60m | 8.43% | 30.88% | 70.00% |

A classifier can report very high raw accuracy in low-prevalence years by mostly predicting NO MOVE. The meaningful 90% objective is therefore selective precision/accuracy with explicit coverage and future-period stability.

Strict survival selective-frontier evidence did not show a regime-invariant 90% MOVE rule. One notable case was 60m in 2026, where the threshold derived from the top 1% of the historical training-score distribution produced approximately:

```text
future coverage 29.17%
MOVE precision 94.87%
```

The same type of 90% MOVE rule was not stable across 2024/2025. High NO-MOVE precision in early years is largely aided by the very low movement base rate.

Conclusion: 90% high-confidence operation remains a valid research objective, but is not current authority.

## 9. Nonlinear and excursion challengers

A fixed shallow HistGradientBoosting classifier did not consistently beat the logistic control. Future-excursion quantile/distribution modeling also failed later-year consistency.

These are not retained as default V8-A2 paths.

## 10. Tick incremental test

The 2023Q4-2024 tick dataset was revisited using only direction-free movement features. Exact tick-vs-M1 movement-label parity was 100% on the aligned population.

Representative 2024 15m AUC:

```text
long-history M1 control   ~0.8578
Q4-only M1                ~0.8082
tick-only                 ~0.7197
M1 + tick                 ~0.7158
history M1 + tick meta    ~0.7237
```

Signless tick activity did not add stable incremental movement information to the long-history M1 model. Do not reopen tick feature mining for V8-A2 without a materially new information source.

## 11. Conformal / abstention diagnostic

A chronological class-conditional split-conformal diagnostic did not preserve nominal 90% future coverage under market drift. Future set coverage was materially below 90% in multiple year/horizon cells.

Conformal wrapping does not solve nonstationarity by itself. It remains a diagnostic, not a reliability guarantee.

## 12. Monthly causal adaptation

A 15m causal monthly study compared the annual regime model with expanding monthly refit, trailing-12-month refit, 180-day Platt calibration and 180-day prior-odds shift.

Key results:

```text
2024 annual regime:       AUC .86276 / Brier .01123
2024 180d calibration:    AUC .84292 / Brier .01093

2025 annual regime:       AUC .87422 / Brier .06911
2025 trailing-12m:        AUC .87205 / Brier .05991

2026 annual regime:       AUC .81873 / Brier .14698
2026 trailing-12m:        AUC .81977 / Brier .14508
```

Adaptation can improve calibration in later regimes, but it is not an AUC breakthrough and can reduce ranking quality. Automatic online refitting is not authorized.

## 13. Final research conclusion

Current V8-A is already a strong and useful movement-ranking control. The V8-A2 study found real but modest improvements from:

```text
explicit barrier-difficulty / regime representation
+
multi-horizon first-hit-time formulation
```

It did not demonstrate a robust future-year AUC >=0.90 model.

The largest practical risk is not sudden disappearance of all ranking skill; it is probability calibration/base-rate drift as the meaning of a fixed $10 move changes with the GOLD regime.

Therefore the current operational philosophy is:

```text
keep frozen V8-A
use it primarily as a relative movement-state signal
log prospectively
monitor AUC + calibration + score-decile ordering
research recalibration separately
fail closed if ranking ordering materially collapses
```

## 14. Promotion gate for any future A2

Do not replace V8-A unless a frozen A2 challenger demonstrates all of:

1. strict causal reconstruction and label-boundary audit;
2. repeated future-block improvement over V8-A, not just CV improvement;
3. Brier/log-loss and calibration that are at least defensible, not AUC-only improvement;
4. stable score-decile ordering;
5. selective 90% claims reported together with coverage;
6. prospective shadow evidence after architecture freeze;
7. Python/MQL parity before any MT5 authority change.

No current V8-A2 model passes that promotion gate.
