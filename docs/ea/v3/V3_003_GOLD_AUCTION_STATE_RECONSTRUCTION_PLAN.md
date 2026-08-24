# V3-003 — GOLD Auction-State Reconstruction Plan

Status: `ACTIVE NEXT PHASE`
Date: `2026-08-25`
Market: `GOLD# ONLY`
Discovery: `2023-2025`
Validation vault: `2022 — CLOSED`
2021: `UNTOUCHED`

## 1. Research pivot

The next V3 phase stops treating one pattern as if it should trade every GOLD regime.

The working market model is:

```text
COMPRESSION
-> EXPANSION
-> RELOAD / PULLBACK
-> EXHAUSTION / FAILED AUCTION
-> transition to a new state
```

The goal is not to label these states after seeing the outcome.

The goal is to construct **causal state descriptors** from information available at each
bar and test whether strategy behavior differs materially by state.

## 2. Why this is more fundamental

Repeated micro-optimization did not resolve:
- quarter instability;
- continuation vs reversal ambiguity;
- 2023/2024/2025 direction-model instability;
- winner/loser feature-classification failure.

Therefore the next question is one architectural level higher:

> Is the same reaction pattern being traded in fundamentally different market states?

If yes, Entry tuning cannot solve the problem.

## 3. State descriptors

Begin with continuous causal descriptors, not hard thresholds.

### Direction / progress

```text
multi-horizon directional return
directional efficiency
swing progression
distance/progress toward active structural objective
recent structure refresh
```

### Compression / expansion

```text
short/long realized range ratio
short/long true-range ratio
bar overlap / range overlap
range expansion rate
directional displacement per unit volatility
```

### Liquidity / reaction state

```text
active unswept intermediate liquidity
distance to nearby liquidity
recent liquidity consumption count
same-state internal sweep ordinal
atomic rejection event
local acceptance / structure transition
```

### Exhaustion / failed auction

```text
objective proximity / objective delivery
expansion maturity
progress deceleration
repeated failed breakout / failed acceptance
opposite-side acceptance
HTF structure age / refresh
```

### Execution suitability

```text
spread / local range
spread / proposed risk
risk / local volatility
```

Execution remains a separate dimension, not a substitute for market state.

## 4. State-discovery methods

Allowed research methods:

```text
rolling normalized descriptors
change-point detection
unsupervised clustering
hidden-state models
simple interpretable decision trees
state-transition matrices
```

Use ML to discover repeatable state structure, not to maximize trade-level outcome labels.

Any state model must be reproducible causally:
- trailing-only normalization;
- no full-sample future normalization;
- no future bars in state assignment;
- stable semantics across years.

## 5. Strategy modules

Do not require one Entry family to trade every state.

### A. EXPANSION / RELOAD CONTINUATION

Candidate logic:

```text
known destination / active delivery
-> intermediate opposite-side liquidity reaction
-> local acceptance back with delivery
-> continuation Entry
```

The current selective-continuation evidence belongs here.

### B. COMPRESSION BREAKOUT

Candidate logic:

```text
causal compression
-> destination-compatible expansion
-> acceptance outside compression
-> first valid pullback / continuation
```

Prior naive range-breakout controls were weak.

Therefore this module must add market-state and destination semantics, not merely another
lookback breakout threshold.

### C. EXHAUSTION / FAILED-AUCTION REVERSAL

Candidate logic:

```text
mature expansion
-> objective delivery / near-delivery
-> failure to continue
-> opposite acceptance
-> reversal Entry
```

Do not authorize reversal merely because a sweep and opposite structure break occurred.

Reversal must be a **late-auction state**, not the mirror image of continuation.

## 6. Outcome framework

Do not reduce all research to `+1R before SL`.

For every candidate, record:

```text
MFE path
MAE path
time to MFE
time to adverse excursion
+1R/+2R/+3R/+5R barriers
objective delivery
premise invalidation
realized exit architecture result
```

The project target remains:

```text
realized WR >= 50%
average winner meaningfully > 1R
positive cost-adjusted expectancy
```

but the research engine should preserve the full path.

## 7. Naive controls are mandatory

Every complex module must beat a simpler causal control.

Examples:

```text
trend + generic pullback
trend + generic BOS
compression + generic breakout
mean-reversion from volatility extension
matched random state/time/risk control
mirror direction
```

If the complex module does not materially beat its naive control, the added concepts do not
receive authority.

## 8. Escalation rule

Research must move upward when natural variants stop improving.

```text
L1 — implementation detail
    FVG selector, swing prominence, Entry depth

if natural variants plateau/fail:

L2 — architecture
    source scale, trigger role, continuation/reversal module

if architecture families plateau/fail:

L3 — fundamental assumption
    is sweep causal?
    is direction predictable?
    is one fixed strategy valid across GOLD regimes?
```

Do not spend dozens of experiments at L1 after L2/L3 failure is already indicated.

## 9. GOLD-first rule

Current V3 scope is:

```text
GOLD FIRST
```

Do not move the active research line to cross-market generalization merely because the
current GOLD pattern is incomplete.

Cross-market validation is deferred until one of the following:

1. GOLD has a materially coherent candidate architecture worth validating elsewhere; or
2. GOLD research reaches a documented structural ceiling and the user explicitly approves a
   market-universe pivot.

The previously prepared cross-market exporter remains deferred.

## 10. Validation governance

```text
2023-2025
    discovery / state reconstruction / strategy design

2022
    final V3 validation vault
    do not inspect during state discovery

2021
    untouched
```

Do not open 2022 to settle uncertainty that can still be resolved inside the discovery lab.

## 11. Immediate next work

```text
1. Build causal GOLD state descriptor table for every M1/M5 decision point.
2. Reconstruct state sequences through 2023/2024/2025.
3. Compare state composition of known strong vs weak periods without creating quarter gates.
4. Test whether selective continuation concentrates in EXPANSION/RELOAD states.
5. Build the first genuine EXHAUSTION-reversal module.
6. Build the first destination-aware COMPRESSION-breakout module.
7. Compare each module against naive controls.
8. Only then combine modules into a GOLD portfolio.
```

No production strategy change is authorized.
