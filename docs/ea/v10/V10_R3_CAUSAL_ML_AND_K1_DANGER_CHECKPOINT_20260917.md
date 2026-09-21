# V10 R3 Causal ML and K1 Danger Checkpoint

Date: `2026-09-17`  
Status: `CONSUMED-DATA SHADOW RESEARCH / NO STRATEGY OR EA PROMOTION`

## 1. What changed

This checkpoint replaces the earlier one-size-fits-all ML question with a narrower, purpose-specific one:

```text
R2 opportunity model
-> already selected a Child

R3 danger model
-> only asks whether a newly selected k1 Child belongs to an extreme STOP-risk tail
```

The research did **not** promote a universal regime gate, a general negative-R classifier, a new direction model, or a production threshold.

The current future-facing result is one shadow hypothesis:

```text
population
= R2-selected k1 Children only

preprocessing
= RobustScaler, training quantiles 10%-90%

model
= logistic regression, C=0.5

reference
= calibrated chronological OOF q97.5

hypothetical action
= abstain from that k1 Child only
```

It has no trade authority.

## 2. Causal data contract

Official raw source:

```text
GOLD#_M1_202201030100_202608282357.csv
SHA256 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
1,648,545 chronological M1 rows
```

R3 reconstructs M15, M30, H1, and H4 directly from a single chronological M1 stream. A higher-timeframe bar becomes visible only when a later M1 row proves that the interval has ended. The builder never preloads future higher-timeframe files and filters backward by cutoff.

Resulting causal universe:

```text
6,770 Child decisions
2,139 resolved FAST runs

2022  1,320
2023  1,488
2024  1,496
2025  1,486
2026    980
```

Future answer-sheet fields are attached only after the FAST run and Child outcome resolve. `label_available_at` is persisted, and rows whose answer crosses an outer-year boundary are purged from training.

Parity against the committed R2 2024-2026 ledger:

```text
3,962 / 3,962 decisions matched
0 missing / 0 extra
0 direction mismatches
0 k mismatches
entry exact
stop, feature, PnL and R parity within floating precision
```

There are 31 same-M1 NHA/SL ambiguities in the full 2022-2026 universe and 20 in 2024-2026. Exact tick order is unknowable from OHLC. The primary ledger uses the conservative stop outcome and persists the decision-open NHA alternative. The selected shadow result is unchanged under that alternative because none of its vetoed rows is one of the seven selected ambiguous positions.

## 3. Purpose-specific representation

The K1 STOP head does not receive every available column. Its 21 causal inputs are a deliberate fusion of:

```text
R2 opportunity / severe / stop / shock probabilities and score
Child stop distance and FAST / STD body geometry
ADX, path efficiency and HA flip context
previous-run length and recent short-run morphology
DI / EMA direction-relative state
M15 / M30 / H1 coherence summaries
```

The model tournament separately tested:

- standard scaling + logistic regression;
- robust scaling + logistic regression;
- quantile-knot spline transformation + logistic regression;
- shallow histogram gradient boosting;
- multiple regularization strengths and run-weighting modes.

Model selection used expanding chronological folds. Probability calibration used only out-of-fold predictions. Decision references came only from prior calibrated OOF scores.

This follows the practical implications of official scikit-learn guidance on chronological splits, probability calibration, nonlinear spline preprocessing, and native nonlinear tree models:

- <https://scikit-learn.org/1.0/modules/generated/sklearn.model_selection.TimeSeriesSplit.html>
- <https://scikit-learn.org/1.7/modules/calibration.html>
- <https://scikit-learn.org/dev/auto_examples/linear_model/plot_polynomial_interpolation.html>
- <https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html>

## 4. Important negative results

### 4.1 Broad regime classification did not solve the trading problem

The first R3 `trendable3` REGIME target produced outer-year AUC around random:

```text
2024  0.490
2025  0.499
2026  0.467
```

Its layered policies worsened economics. ADX / path-efficiency context remains useful instrumentation, but this target is rejected as an admission model.

### 4.2 Generic negative-R classification was the wrong target

The selection-conditioned negative-R head produced AUC only about `0.50-0.54`. The STOP head produced about `0.73-0.76` for the broad selected population and `0.68-0.73` for the narrower K1 population. “Any negative outcome” is too heterogeneous; actual structural STOP is the cleaner purpose-specific event.

### 4.3 Generic log-loss optimization was not enough

When all consumed data were available, generic chronological log-loss selected robust logistic `C=0.02`. Fixed outer-year economics showed that this setting did not preserve improvement across 2024-2026.

Therefore:

```text
best average probability fit
!=
best extreme-tail action model
```

The future shadow member is selected from the fixed specifications that improved structural R in every outer year, then checked with run-block bootstrap. This is still post-hoc consumed-data selection and is not independent validation.

### 4.4 More features were not automatically better, but context interaction mattered

Fixed Robust `C=0.5` feature ablation:

| Feature family | Pooled R | PF_R | DD_R |
| --- | ---: | ---: | ---: |
| Full purpose-specific 21 | `553.83` | `1.4813` | `45.41` |
| Compact hybrid 12 | `550.80` | `1.4759` | `46.41` |
| R2 meta only 6 | `546.53` | `1.4777` | `46.41` |
| R2 comparator | `532.16` | `1.4525` | `52.41` |
| Geometry only 15 | `527.76` | `1.4597` | `46.41` |

The useful result is not “21 is better because it is larger.” Opportunity-state and causal geometry complement each other; geometry alone did not improve R.

## 5. Consumed outer walk-forward result

Primary future shadow hypothesis: `ROBUST_C05`.

| Period | R2 R | Shadow R | Delta R |
| --- | ---: | ---: | ---: |
| 2024 | `199.12` | `214.46` | `+15.34` |
| 2025 | `208.66` | `213.11` | `+4.45` |
| 2026 through Aug 28 | `124.38` | `126.26` | `+1.87` |
| Pooled | `532.16` | `553.83` | `+21.67` |

Pooled comparison:

| Metric | R2 comparator | ROBUST_C05 shadow |
| --- | ---: | ---: |
| Entries | `1,573` | `1,556` |
| Units | `3,067` | `3,040` |
| Raw PnL | `12,788.52` | `12,901.12` |
| PF | `1.4368` | `1.4425` |
| Structural R | `532.16` | `553.83` |
| PF_R | `1.4525` | `1.4813` |
| DD_R | `52.41` | `45.41` |
| Oracle recall | `70.99%` | `70.19%` |
| L6+ positive-child retention | `43.350%` | `43.313%` |

The gate removed only 17 of 1,573 selected positions:

```text
16 losing positions
1 winning position
14 structural STOPs
27 risk units removed
delta +112.60 raw PnL
delta +21.67R
```

Run-block bootstrap, 20,000 draws:

```text
pooled observed delta        +21.67R
pooled 95% interval      [ +6.03R, +38.74R ]
P(delta R > 0)                 99.70%
```

The 2025 and 2026 lower quantiles are exactly zero, not strictly positive, and their probability of positive delta is lower than 2024. This is encouraging development evidence, not proof of durable edge.

## 6. Why the tuned headline is not the future action model

The per-era tuned q97.5 diagnostic produced:

```text
+555.85R
PF_R 1.4842
DD_R 45.41
```

That is `+23.69R` over R2 and slightly higher than fixed Robust `C=0.5`. It switches hyperparameters/model family by era and was selected after the full scan. The simpler fixed robust model gives up about `2.02R` of consumed-data result while removing a large degree of freedom. It is therefore the only action-bearing future **shadow** candidate.

Shallow HistGB and its union with Robust reduced realized DD further, but their run-block bootstrap lower bounds crossed zero. They remain diagnostic-only disagreement channels.

## 7. EA and policy parity incident

The committed R2 research ledger applies conditional-NEUTRAL admission per Child. The current R2 EA latches `g_run_admitted=true` for the remainder of a FAST run. This changes six 2024-2026 Child actions.

```text
research-ledger policy
!=
current EA run-latched policy
```

No R3 model should be integrated into the EA until that semantic choice is resolved and Python/MQL action parity is exact.

## 8. Authority decision

```text
ROBUST_C05
= primary future shadow hypothesis
!= strategy authority
!= EA authority
!= production readiness
!= independent validation
```

All 2022-2026 rows are consumed development evidence. `GOLD# 2021` remains untouched final temporal reserve.

No current V10 threshold, model, policy, or EA is promoted.

## 9. Reproducibility

Code:

- `research/v10/build_v10_causal_m1_universe_r3.py`
- `research/v10/tune_v10_r3_models.py`
- `research/v10/probe_v10_r3_meta_danger.py`
- `research/v10/validate_v10_r3_k1stop_candidate.py`
- `research/v10/compare_v10_r3_k1stop_specs.py`
- `research/v10/validate_v10_r3_stable_union.py`
- `research/v10/ablate_v10_r3_k1stop_features.py`
- `research/v10/train_v10_r3_k1stop_future_shadow.py`
- `research/v10/publish_v10_r3_k1stop_results.py`

Compact receipts:

`results/r3_k1stop_20260917/`

The large causal universe, per-event score ledgers, bootstrap draws, and joblib shadow bundle are regenerated under ignored `output/v10_r3/` and are intentionally not presented as repository-scale authority artifacts.

R3 publication validation passes:

```text
17 published artifact hashes checked
11 script / environment-contract hashes checked
future shadow bundle reloaded
primary member and 21-feature contract checked
0 R3 publication problems
```

The predecessor repository-wide V10 pack and its validator were removed during the 2026-09-21 cleanup because they mixed obsolete bounded-m3 artifacts, a historical clock mismatch, and duplicate backup files. They remain available in Git history. This checkpoint proves only the compact raw-M1/R3 lineage and receipts; it does not revive the removed predecessor pack.
