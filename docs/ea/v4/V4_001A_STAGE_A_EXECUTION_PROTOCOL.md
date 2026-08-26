# V4-001A — Leakage-Safe Stage-A Execution Protocol

Status: `FROZEN BEFORE OFFICIAL NEURAL OUTCOME`
Date: `2026-08-27`
Parent contract: `V4_001_AI_NATIVE_RESEARCH_CONTRACT.md`
Base model: `V4_001_CausalPatchPolicy`
Production authority: `NONE`

## 1. Why this addendum exists

The bootstrap model/config remains unchanged. Before the first authoritative neural run, code review found two
methodological problems in the low-level bootstrap trainer that must not be allowed into the Stage-A result:

1. the bootstrap trainer evaluated the outer year every epoch and selected the best checkpoint using that loss;
2. a same-calendar leave-one-market-out split can be overly permissive when correlated markets share the same
   future event interval.

These are evaluation-protocol defects, not strategy/model hypotheses. They were corrected before any official
V4-001A neural result.

A tiny CPU smoke run after the protocol was specified is explicitly `DIAGNOSTIC / NON-AUTHORITY` and may not be
used for model selection or Stage-A promotion.

## 2. Outer evaluation is never early-stopping data

Every training fold has three populations:

```text
FIT
INNER_VALIDATION
OUTER_EVALUATION
```

Only FIT changes weights.
Only INNER_VALIDATION selects the checkpoint/early stop.
OUTER_EVALUATION is scored only after the checkpoint for that seed is frozen.

Checkpoint criterion:

```text
lowest INNER_VALIDATION Gaussian return NLL
```

not outer AUC, outer P/L, or total multitask loss.

## 3. Chronological inner-validation split

Inside each training allocation:

```text
first 80% of training timestamps -> FIT side
last 20%                      -> INNER_VALIDATION side
```

A fixed seven-calendar-day purge is removed on both sides of the split boundary.

Reason:
- V4-001 H4 history is approximately seven days;
- the longest target is four hours;
- the purge prevents overlapping observation history around the checkpoint-selection boundary.

`80/20` and `7 days` are frozen engineering/research constants and were not selected from neural outcome.

## 4. Primary temporal folds

### Secondary temporal breadth

```text
FIT/INNER: 2023
OUTER:     2024
all four development markets
```

### Primary temporal fold

```text
FIT/INNER: 2023-2024
OUTER:     2025
all four development markets
```

The 2025 outer set is not used for checkpoint selection.

## 5. Primary leave-one-market-out folds are time-isolated

For each held-out market `S`:

```text
training targets/contexts:
    other 3 markets, 2023-2024

outer evaluation target:
    S, 2025

outer context available at decision time:
    all causally available development-market histories
```

The held-out market is not a training target **or training context**.

This is stricter than same-period domain holdout. It prevents training on contemporaneous future labels from
other highly correlated markets and then calling the same future interval an independent held-out-market test.

The four primary LOMO folds are:

```text
GOLD#
BTCUSD#
XAUEUR#
USDJPY#
```

all evaluated only in 2025 after training on the other three markets in 2023-2024.

## 6. Target-market balance during fitting

BTCUSD# has materially more 15-minute observations because it trades through periods when other markets are
closed. V4-001A does not interpret that mechanical observation count as strategic importance.

FIT uses inverse-target-frequency weighted sampling so each active training target has equal expected sample
share per epoch.

INNER_VALIDATION and OUTER_EVALUATION retain natural sample frequency.

This changes only optimizer sampling. It does not create or remove an evaluation opportunity.

## 7. Frozen seeds and aggregation

Run all three baseline seeds:

```text
17
29
43
```

No best-seed selection is allowed.

Primary fold prediction is the arithmetic mean of the three frozen-seed direction probabilities:

```text
p_ensemble = mean(p_seed17, p_seed29, p_seed43)
```

Per-seed metrics remain visible.

## 8. Hardware batch handling

Target effective batch:

```text
256
```

A smaller CUDA micro-batch is allowed only for memory/throughput reasons. Gradient accumulation preserves an
effective batch of approximately 256.

Changing micro-batch for hardware is not model/strategy tuning and must be recorded in the run manifest.

AMP may be used on CUDA and is recorded.

## 9. AUC uncertainty

The primary AUC confidence interval uses a weekly block bootstrap:

```text
1000 bootstrap repetitions
calendar-week blocks
all samples from a selected week move together
```

This preserves much more serial and cross-market dependence than an IID trade/sample bootstrap.

## 10. Frozen same-input linear control

The linear/logistic control uses the same 14 causal input channels and configured histories.

For every market/timeframe window, compute:

```text
last completed bar features
full-window mean
recent-half mean - older-half mean
log(1 + stream age)
```

For each timeframe concatenate:

```text
target-market summary
mean summary of allowed context markets
```

Across M1/M5/M30/H4 this produces 344 features with no symbol ID and no ICT/V3 labels.

Estimator:

```text
StandardScaler fit on training only
SGDClassifier(loss=log_loss)
alpha=1e-4
3 fixed passes
average=True
seed=17
```

This baseline is an AUC control, not the neural calibration reference.

## 11. Exact Stage-A PASS gate

All conditions must pass.

### A. Primary pooled temporal information

```text
TEMPORAL_2025_PRIMARY weekly-block AUC 95% CI lower bound > 0.500
```

### B. Primary temporal market breadth

```text
TEMPORAL_2025_PRIMARY per-target AUC > 0.500 in >= 3 of 4 markets
```

### C. Strict market transfer

```text
LOMO_FUTURE_2025 AUC > 0.500 in >= 3 of 4 held-out targets
```

### D. Added value over the frozen linear control

```text
neural strict-LOMO AUC > corresponding linear strict-LOMO AUC in >= 3 of 4 targets
```

### E. No gross probability miscalibration

```text
TEMPORAL_2025_PRIMARY ECE(10 equal-width bins) <= 0.05
```

### F. More than one favorable year

```text
TEMPORAL_2024 pooled AUC > 0.500
```

`PASS` requires A+B+C+D+E+F.

A failed Stage A keeps V4-001B and V4-002 locked. Do not use the external market vault to repair it.

## 12. Controller boundary

The Stage-A runner does not calculate or print the V4-001B trading controller result.

Reason:

```text
representation gate first
policy economics second
```

The bootstrap `v4_001_evaluate.py` remains useful as low-level development code, but its automatic policy output
is not Stage-A authority.

## 13. External data remain closed

Do not open:

```text
XAUJPY#
XAUCNH#
GAUCNH#
GAUUSD#
```

and do not inspect GOLD# 2021 during V4-001A.
