# V4 AI-Native Trading Research Contract

Status: `PAUSED / PRESERVED RESEARCH AUTHORITY`
Date: `2026-08-27`
Parent negative authority: `V3-003G Candidate B 2022 independent validation FAIL`
Production authority: `NONE`

## 1. Purpose

V4 is a separate research line for learned market representation and learned/sequential trading policy.
It exists because V3 repeatedly showed that hand-authored chart states and direction rules can fit a development
regime while failing temporal or cross-market generalization.

V4 does **not** mean that ML/RL is assumed to work. It means that the project now tests whether useful state
representation can be learned from a broader causal information set before another human-authored strategy
state machine is created.

## 2. Startup authority

On every V4 session:

1. check the latest GitHub commit;
2. read root `AGENTS.md`;
3. read root `docs/ea/HANDOFF.md`;
4. read this file;
5. read `HANDOFF_V4.md`;
6. read `RESEARCH_STATE_V4.md`;
7. read `V4_001_AI_NATIVE_RESEARCH_CONTRACT.md`;
8. read `V4_001_BASE_MODEL_SPEC.md`;
9. read `V4_001_REPRESENTATION_TOURNAMENT.md`;
10. read `V4_001A_STAGE_A_EXECUTION_PROTOCOL.md`;
11. read `V4_LITERATURE_LEDGER.md`;
12. read `BACKLOG_V4.md`;
13. inspect the exact current V4 code/config/model manifest before changing architecture.

If chat memory conflicts with GitHub, GitHub wins.

V1 remains a frozen deterministic control. V2 remains paused/preserved. V3 remains preserved negative and
mechanism-research authority. V4 must not rewrite their historical results.

## 3. Core V4 research principles

### 3.1 Representation first

Do not start with PPO/SAC/actor-critic simply because V4 is AI-native.

Required order:

```text
causal raw sequence
-> learned representation
-> out-of-sample information-skill test
-> simple cost-aware controller
-> only then sequential RL if justified
```

If the learned representation cannot demonstrate useful OOS information, RL is not authorized as a rescue.
Expand the information set or change the research problem instead.

### 3.2 Causality is stricter, not looser

All model inputs must satisfy:

```text
available_at <= decision_time
```

Rules:
- only completed bars may enter a decision window;
- resampled bars become available at their close, not their open timestamp;
- causal rolling normalization only;
- no full-sample scaler fit;
- no future-aware imputation;
- missing/stale cross-market context must be explicit to the model;
- target labels may use the future, features may not;
- train/validation/test transforms must be frozen before evaluation.

### 3.3 Minimal human technical-analysis priors

V4-001 inputs do not include hard-coded ICT/SMC strategy labels such as:

```text
sweep
FVG quality
BOS owner
BOTH branch
Candidate A
Module H / L
session veto
```

Those may later be supplied as optional ablation channels, never as assumed privileged truth.

Permitted base transforms are market-invariance transforms rather than strategy rules:
- log return;
- body/range/wick geometry;
- tick volume;
- spread;
- causal volatility normalization;
- timestamp/session availability;
- multi-resolution causal aggregation.

### 3.4 Market actions do not create alpha

For the initial research scale, the agent is assumed too small to move market prices materially.
Therefore long/flat/short counterfactual next-period rewards can be evaluated from the same exogenous path.
V4-001 exploits this full-information property instead of introducing unnecessary offline-RL extrapolation.

### 3.5 Costs from the first economic policy test

Representation diagnostics may use raw future returns, but any trading-policy claim must include the recorded
spread model from the first run.

Commission/slippage/swap and exact-tick fill semantics remain later execution layers. A Level-A positive result
is not production authority.

### 3.6 Discovery and validation remain separate

No model architecture, horizon, history length, action rule, cost treatment, normalization, loss weighting,
or threshold may be changed because a validation-vault result was poor.

If a validation result causes redesign, that data becomes consumed and the new model requires a new untouched
validation allocation.

### 3.7 Black-box success is not enough

Record at minimum:
- code commit / file hashes;
- data hashes;
- exact split;
- random seed;
- config;
- parameter count;
- training history;
- fold metrics;
- calibration;
- turnover and cost burden;
- market/year contribution;
- drawdown and loss streak;
- baseline comparisons.

A single favorable seed or one favorable market is not evidence.

## 4. V4 dataset governance

### Development laboratory — OPEN

```text
GOLD#    2023-2025
BTCUSD#  2023-2025
XAUEUR#  2023-2025
USDJPY#  2023-2025
```

These data are development only. They have already been viewed during V3/cross-market research and cannot
serve as final independent validation.

### Cross-market validation vault — UNOPENED FOR V4

Frozen from the prior V2 outcome-blind GOLD-like cohort:

```text
XAUJPY#  2023-2025
XAUCNH#  2023-2025
GAUCNH#  2023-2025
GAUUSD#  2023-2025
```

Do not request/open these for V4 until a V4 candidate and validation contract are frozen.

### Temporal final confirmation — UNTOUCHED

```text
GOLD# 2021
```

Keep untouched until explicitly authorized.

### Consumed / non-pristine

```text
GOLD# 2022 = consumed V3 validation
```

It may later be used for diagnostic or training purposes only after an explicit decision. It is not a pristine
V4 validation vault.

## 5. Promotion ladder

```text
V4-001A representation skill
-> V4-001B simple cost-aware policy
-> frozen external-market validation
-> exact tick / costs
-> V4-002 sequential RL only if additional sequential control is still needed
-> MT5 reproduction
-> controlled EA/inference integration
```

Skipping directly to a live RL agent is forbidden.

## 6. Final strategy objective remains unchanged

Any eventual V4 strategy still targets:
- realized trade win rate >= 50%;
- average winner meaningfully > 1R;
- clearly positive cost-adjusted expectancy;
- acceptable drawdown and loss streak;
- multi-period and multi-market robustness;
- no unresolved execution divergence.

V4 may use different intermediate metrics during representation learning, but it does not lower the final
strategy standard.

## 7. Current phase

```text
V4-001 REPRESENTATION TOURNAMENT / CLAIM-GRADE CUDA RUN NEXT
```

No model has trading authority. No MT5 EA modification is authorized.

## V4-001 Representation Tournament authority — 2026-08-27

Read before current model work:

```text
V4_001_REPRESENTATION_TOURNAMENT.md
V4_001A_STAGE_A_EXECUTION_PROTOCOL.md
V4_LITERATURE_LEDGER.md
```

Current claim-grade tracks:

```text
R0 causal linear control                    FROZEN
R1 V4_001_CausalPatchPolicy supervised      CLAIM-GRADE CONTENDER
R2 V4_001_MarketJEPA + linear probe         CLAIM-GRADE CONTENDER
```

External-pretrained tracks:

```text
R3 Kronos-mini                              TRANSFER DIAGNOSTIC ONLY
R4 MOMENT-1-small                           TRANSFER DIAGNOSTIC ONLY
```

R3/R4 may never override a failed R1/R2 Stage-A gate. Before opening a new major V4 representation, foundation-model, RL or agent architecture, update `V4_LITERATURE_LEDGER.md` from current web/literature/maintained-open-source evidence first.


## V5 disposition — 2026-08-27
V4 is paused after the success-first mechanism pivot. It is not invalidated.
Do not run R1/R2 as the active priority unless V5 explicitly re-opens the tournament.
Prepared data, code, frozen protocols and negative/positive findings remain preserved.
