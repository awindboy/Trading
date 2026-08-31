# V8 Development Handoff

Last updated: `2026-09-01`
Current phase: `V8-A FROZEN + V8-A2 CHALLENGER RECORDED + V8-C ENTRY/EXIT RESEARCH`
Production authority: `NONE`
Research EA authority: `V8MAMTFStochResearchEA R0.4` for frozen LONG validation
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Branch status

### V8-A

`FROZEN / RETAINED / CURRENT MOVEMENT CONTROL`

Contract:

```text
+/-10 movement
15m / 30m / 60m
53 causal M1 features
2024 <- 2022-23
2025 <- 2022-24
2026 <- 2022-25
```

Do not change the current indicator or coefficient pack.

### V8-A2

`RESEARCH COMPLETE / CHALLENGER RETAINED / NOT PROMOTED`

The A2 tournament found modest, repeatable improvement from:

```text
53 original movement features
+ 33 barrier-difficulty/regime features
+ unified 15/30/60 first-hit-time survival formulation
```

Strict 60m-purged research-pack AUC:

```text
          2024     2025     2026
15m     0.8660   0.8736   0.8190
30m     0.8501   0.8565   0.7999
60m     0.8130   0.8384   0.7925
```

Frozen control:

```text
          2024     2025     2026
15m     0.8566   0.8715   0.8177
30m     0.8418   0.8526   0.7977
60m     0.8068   0.8316   0.7868
```

No future-year AUC >=0.90 authority was demonstrated.

Important audit: an early exploratory survival/stack run used an insufficient horizon-specific purge for a label that contains 60m information. Those exploratory stack/selective outputs are not authority. The retained survival pack was regenerated using `decision+60m <= cutoff` for every output horizon.

Barrier/regime logistic also improved AUC in all nine cells, but probability calibration did not improve uniformly.

Shallow HGB, future-excursion distribution and signless tick features are not retained as default A2 paths.

### V8-B

`PAUSED / NEGATIVE-RESULT AUTHORITY`

Broad learned direction remains weak or unstable after strict causal reconstruction. Do not resume equivalent feature/model mining under a new name.

### V8-C LONG

`PROVISIONAL FROZEN / MT5 REAL-TICK VERIFIED ON OPEN DEVELOPMENT EVIDENCE`

Frozen entry:

```text
M5 SMA20 contact-start
P15 > prior-288 same-model-year Q75
raw Stoch K14 > D3
completed M15 3-bar up
completed H1 3-bar down
=> LONG next M5 open
SL/TP +/-10
one position
```

Accepted R0.4:

```text
2024 N152 WR59.87% +29.26R
2025 N165 WR61.21% +37.35R
2026 N139 WR58.99% +25.24R
pooled N456 WR60.09% +91.85R
expectancy +0.201R/trade
PF ~1.49
```

Current 1R full exit is entry-edge validation only.

### V8-C-S1 SHORT

`RESEARCH ONLY / M1 PROXY`

```text
P15 > prior-288 Q75
K < D
previous M5 entirely below SMA20
event closes below SMA20 after contact-start
trailing 288 M5 net displacement < 0
=> SHORT
```

M1 proxy:

```text
2024 N41 WR58.54%
2025 N51 WR54.90%
2026 N48 WR62.50%
pooled N140 WR58.57% +24R
```

No MT5 authority yet.

## 2. A2 validation findings that must carry forward

### 2.1 CV is not future evidence

Blocked chronological folds could exceed 0.90 AUC while the actual next-year outer score remained around 0.86. Random K-fold is prohibited as authority.

### 2.2 90% must include coverage

Raw accuracy is misleading because movement prevalence changed sharply:

```text
15m: 1.16% -> 8.05% -> 29.45%
30m: 3.21% -> 16.77% -> 48.61%
60m: 8.43% -> 30.88% -> 70.00%
```

Any 90% claim must report precision/selective accuracy, coverage and year-by-year stability.

### 2.3 Tick data did not improve A2

2023Q4->2024 direction-free tick features failed to add incremental movement AUC to the long-history M1 control. Do not reopen tick feature mining without new information.

### 2.4 Conformal is not a drift cure

A chronological class-conditional conformal diagnostic failed to retain nominal 90% future coverage. Do not use conformal as a reliability guarantee under nonstationarity.

### 2.5 Monthly adaptation helps calibration more than ranking

15m trailing-12m / 180d calibration diagnostics improved Brier in 2025/26 but did not create a major AUC jump. Automatic online refit is not authorized.

## 3. Practical V8-A reliability interpretation

Current evidence supports using V8-A primarily as a relative movement-state/ranking signal. The principal live risk is calibration/base-rate drift as the meaning of a fixed $10 move changes.

Prospective monitoring should record:

```text
P15/P30/P60
resolved movement outcomes
AUC
Brier/calibration
score-decile hit rates
high-vs-low score ordering
recent 30/60/90d stability
```

Do not retrain reactively because a short window is poor.

## 4. Files from the A2 study

Primary report:

`docs/ea/v8/V8_A2_MOVEMENT_CHALLENGER_RESEARCH_20260901.md`

Audited result tables:

`docs/ea/v8/results/v8_a2_20260901/`

Research-only model manifest:

`config/v8_a2_survival_challenger_manifest.json`

The existing frozen V8-A model/indicator remains the only V8-A MT5 authority.

## 5. Immediate next tasks

1. Keep V8-A frozen.
2. Add prospective movement-probability reliability logging before any A2 promotion decision.
3. Do not chase 0.90 by architecture/threshold mining.
4. If A2 research resumes, start from the audited 86-feature regime representation and strict 60m-purged survival formulation.
5. Preserve V8-C LONG semantics.
6. Continue SHORT/exit work separately when desired.
7. Keep 2021 locked.

## 6. Reading order next session

1. `docs/ea/v8/AGENTS_V8.md`
2. `docs/ea/v8/HANDOFF_V8.md`
3. `docs/ea/v8/V8_A2_MOVEMENT_CHALLENGER_RESEARCH_20260901.md`
4. `docs/ea/v8/V8_C_ENTRY_ARCHITECTURE_MT5_VALIDATION_20260901.md`
5. `docs/ea/v8/DECISIONS_V8_A2_ADDENDUM_20260901.md`
6. `docs/ea/v8/DECISIONS_V8_ADDENDUM_20260901.md`
7. `docs/ea/v8/RESEARCH_STATE_V8.md`
8. `docs/ea/v8/BACKLOG_V8.md`

Always refresh GitHub HEAD before continuing.
