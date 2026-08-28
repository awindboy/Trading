# V6 Failure Map — What Must Not Be Repeated

Status: `ACTIVE CONSTRAINT MAP`
Date: `2026-08-28`

## V3 — hand-authored state overgeneralization

### What worked in discovery

- GOLD 2023-2025 produced encouraging event/state relationships.
- Candidate B achieved an unusually attractive development profile under the then-frozen architecture.
- Entry survival and winner continuation could be decomposed meaningfully.
- D145 found a strong +1R survivor continuation relationship inside V3 populations.

### What failed

- GOLD 2022 frozen validation broke Candidate B.
- other-market Entry survival was materially weaker.
- mirror relationships sometimes rivaled or exceeded the intended direction.
- hand-crafted trade-level ML in early V3 did not generalize reliably.
- D145 M30 continuation relation later failed transfer to First Cross in V5.

### V6 lesson

Do not assume a human-readable state has invariant meaning across time/markets.
Do not fix a validation reversal by adding another threshold.

## V4 — generic AI no-learning

### What V4 tried

- causal multi-resolution raw sequences;
- compact Transformer-style models;
- generic 15m/60m/240m next-return targets;
- representation / pretrained-model directions;
- leakage-aware temporal splits.

### Practical result

The user ran multiple learning attempts and did not obtain meaningful learning.
Current GitHub documents may understate this by leaving some CUDA runs as pending; for V6 planning, the user's later correction is authoritative about the practical stop reason.

### V6 lesson

Do not repeat:

```text
all market times
-> generic next-return label
-> bigger/newer model
```

A modern model is not evidence of a learnable problem.

## V5 — mechanism/payoff search narrowed the target

### What V5 established

- First Cross could raise hit rate and retain positive EV but not average positive >=2R.
- partial-fraction tuning could not solve the joint objective.
- structural-lock and source-native continuation states did not rescue the needed population.
- D145 M30 state was measurable cross-architecture but its edge did not transfer.
- real yield was carefully causal but empirically wrong-direction in 2023.
- source-faithful Williams COT extremes were too sparse for the frozen 2023 test.

### Late V5 transition back to AI

Event-conditioned raw GOLD state was tested on the V3 broad population.
The core result remained unstable chronologically:

```text
2024 weak/reversed
2025 better
pooled near chance
```

Refining the label into robust path endpoints did not eliminate the reversal.

Cross-market context then produced a small same-direction improvement across 2024 and 2025, but capacity confounding remained unresolved.

### V6 lesson

The unresolved problem is not `find another setup`.
It is:

```text
when does the same event mean something different,
and is the missing state observable causally?
```

## Do-not-repeat checklist

Before proposing a new V6 experiment, ask:

- Is this just a new threshold on a consumed V3/V5 variable?
- Is this just another generic return-prediction model like V4?
- Am I selecting a timeframe/model after seeing outcomes?
- Am I adding channels without a same-capacity placebo?
- Am I calling a chronological reversal random noise without measuring uncertainty?
- Am I mixing Entry survival and winner continuation?
- Am I using a consumed validation year to tune?
- Am I treating a tail-driven mean as representative performance?
- Am I solving poor payoff by forcing a fixed TP?
- Am I moving away from GOLD merely because another market/source looks easier?

If yes, stop and redesign the research question.
