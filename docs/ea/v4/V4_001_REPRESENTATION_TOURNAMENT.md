# V4-001 Representation Tournament Contract

Status: `PRE-REGISTERED DEVELOPMENT CONTRACT / BEFORE CLAIM-GRADE NEURAL OUTCOME`
Date: `2026-08-27`
Production authority: `NONE`
Parent: `V4_001_AI_NATIVE_RESEARCH_CONTRACT.md`

## 1. Why this supersedes a one-model test

V4 was opened because hand-authored state machines repeatedly failed temporal or cross-market generalization.
The same mistake must not be repeated at the model-family level by treating one locally designed Transformer as
"AI" and then tuning it until it works.

V4-001 therefore compares distinct representation-learning priors under the same development governance.
The first question remains information skill, not trading P/L.

## 2. Tournament tracks

### R0 — frozen causal linear control

Authority: `CLAIM-GRADE CONTROL`

The already-frozen 344-feature pooled logistic baseline is the minimum learned control. Strict future-isolated
LOMO AUC15 values were recorded before claim-grade neural results:

```text
GOLD#    0.5097969644
BTCUSD#  0.5026543920
XAUEUR#  0.5106438503
USDJPY#  0.5072127120
```

### R1 — supervised `V4_001_CausalPatchPolicy`

Authority: `CLAIM-GRADE CONTENDER`

Frozen topology from `V4_001_BASE_MODEL_SPEC.md`. It learns directly from 15/60/240-minute return-distribution
labels. Official execution follows `V4_001A_STAGE_A_EXECUTION_PROTOCOL.md`.

### R2 — self-supervised `V4_001_MarketJEPA` + frozen linear probe

Authority: `CLAIM-GRADE CONTENDER`

R2 preserves the same causal patch-encoder information set and roughly the same representation capacity as R1,
but changes the learning problem:

```text
causal state at t
-> encoder z_t
-> predictor
-> latent state of the same target market at t+15m
```

Pretraining is self-supervised inside the training allocation only. After pretraining:

```text
encoder frozen
-> one linear direction probe
-> same Stage-A outer folds
```

The anti-collapse term is an explicit project implementation inspired by the SIGReg/isotropy family of ideas.
It is not claimed to reproduce external Fin-JEPA byte-for-byte or to reproduce its daily-equity architecture.

Strict LOMO rule is stronger than ordinary domain holdout:

```text
other 3 markets 2023-2024 only
held-out market absent from self-supervised context and targets
-> held-out market 2025 outer evaluation
```

### R3 — Kronos-mini zero-shot K-line forecast

Authority: `TRANSFER DIAGNOSTIC ONLY`

Pinned upstream code commit:

```text
shiyu-coder/Kronos
67b630e67f6a18c9e9be918d9b4337c960db1e9a
```

Pinned model family:

```text
NeoQuasar/Kronos-mini
NeoQuasar/Kronos-Tokenizer-2k
```

Kronos is finance-specific and useful as an external prior, but its exact pretraining temporal coverage is not
sufficiently documented for our broker 2023-2025 period to be treated as pristine OOS. R3 can inform later
architecture/pretraining choices but cannot by itself unlock V4-001B or external validation.

### R4 — MOMENT-1-small frozen embedding probe

Authority: `TRANSFER DIAGNOSTIC ONLY`

Reference upstream commit:

```text
moment-timeseries-foundation-model/moment
38f7310ad594100747ca2a8357e9c7ca7d323e0e
```

Model:

```text
AutonLab/MOMENT-1-small
```

R4 tests whether generic time-series pretraining transfers to our broker-return sequence. Its pretraining corpus is
external to V4, so the result is diagnostic rather than pristine V4 evidence.

## 3. Common claim-grade allocation

Open development lab only:

```text
GOLD#    2023-2025
BTCUSD#  2023-2025
XAUEUR#  2023-2025
USDJPY#  2023-2025
```

External-market validation remains closed:

```text
XAUJPY# / XAUCNH# / GAUCNH# / GAUUSD# 2023-2025
```

GOLD# 2021 remains untouched.

## 4. Claim-grade Stage-A gate

R1 and R2 use the same gate. All must pass:

1. 2025 pooled 15m AUC weekly-block-bootstrap 95% lower bound > 0.5;
2. 2025 per-market AUC > 0.5 in at least 3/4 markets;
3. strict future-isolated LOMO AUC > 0.5 in at least 3/4 markets;
4. strict LOMO AUC beats frozen R0 in at least 3/4 markets;
5. 2025 ECE10 <= 0.05;
6. secondary temporal 2024 pooled AUC > 0.5.

No P/L threshold participates in Stage A.

## 5. Pre-registered claim-grade model selection

If neither R1 nor R2 passes:

```text
NO_CLAIM_GRADE_PASS
V4-001B locked
V4-002 RL locked
external validation closed
```

If exactly one passes, that representation becomes the sole candidate for the next freeze decision.

If both pass, use the following lexicographic selection rule, frozen before results:

1. higher median strict-LOMO AUC improvement over R0 across four held-out markets;
2. if tied, higher pooled `train 2023-2024 -> 2025` AUC.

Do not use R3/R4 to override this selector.

## 6. External-model contamination rule

A pretrained model whose training corpus may contain the same asset/time period is not pristine OOS evidence even
if our local fine-tuning/probe split is chronological. Therefore:

- R3/R4 results are labeled transfer diagnostics;
- they may motivate a new from-scratch/domain-pretraining experiment inside the open development lab;
- they cannot open the V4 validation vault;
- they cannot authorize V4-001B economics or RL by themselves.

## 7. Compute boundary

Official R1/R2 runs require CUDA-enabled PyTorch. CPU-only runs are smoke/diagnostic only.
Hardware-driven micro-batch reduction is permitted if effective batch size remains frozen.
Workers, pinned-memory settings and AMP implementation are execution parameters, not strategy/model-selection axes.

## 8. Required result artifacts

For R1 and R2 upload:

```text
V4_001_R1_RESULT_BUNDLE.zip
V4_001_R2_RESULT_BUNDLE.zip
V4_001_TOURNAMENT_SUMMARY.json
```

Checkpoint binaries are not required for routine review; their SHA-256 hashes must be preserved in the bundles.

R3/R4 JSON outputs are optional during the first claim-grade run and should be uploaded separately if executed.
