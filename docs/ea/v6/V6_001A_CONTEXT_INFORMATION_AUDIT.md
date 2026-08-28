# V6-001A — Same-Capacity Cross-Market Context Information Audit

Status: `ACTIVE / PRE-REGISTERED FROM V5 HANDOFF`
Date: `2026-08-28`
Production authority: `NONE`

## 1. Question

Late V5 scratch suggested synchronized `XAUEUR# + USDJPY#` state improved event-conditioned path discrimination in both 2024 and 2025.

But the context model had approximately three times the input channels.

V6-001A asks:

> Does real synchronized cross-market context provide incremental information beyond a same-capacity input that contains no new market information?

## 2. Population

Exact V3-003C BROAD CONTROL.

Required parity before outcome evaluation:

```text
2023 84
2024 86
2025 67
```

Do not apply Candidate-A/V3 gates.

## 3. Markets

Primary GOLD anchor:

```text
GOLD#
```

Real context:

```text
XAUEUR#
USDJPY#
```

BTCUSD# is excluded from V6-001A because the immediate hypothesis is decomposition of gold/currency state, not broad risk appetite.

No new external data source is introduced.

## 4. Causal alignment

For every GOLD event timestamp:
- use only completed GOLD and context bars available no later than the event;
- preserve alignment staleness information;
- do not forward-fill future context;
- fail closed if required history is unavailable.

Use the same M1/M5/M30/H4 event-history boundaries across all arms.

## 5. Arms

### A — GOLD-only diagnostic

Existing GOLD raw context block.
Approximate channel count: 10 per timeframe.

### B — GOLDx3 same-capacity placebo — PRIMARY CONTROL

Concatenate the exact GOLD block three times:

```text
[GOLD block, GOLD block, GOLD block]
```

No noise injection.
No transformed duplicate.
No independent random feature.

Purpose:
- match the 30-channel dimensionality of the real-context arm;
- add zero new market information.

### C — real synchronized context — PRIMARY TEST

```text
[GOLD block, XAUEUR block, USDJPY block]
```

Use exactly the same model family, random kernels/features, seeds, regularization search policy, timeframe aggregation, and evaluation splits as Arm B.

## 6. Outcomes

Primary V6-001A outcome is the robust path-endpoint task inherited from late V5:

```text
W_CONTINUE (+1 -> +2 before 0)
vs
L_CONTINUE (-1 -> -2 before 0)
```

Reason:
- it removes the most obvious giveback/recovery ambiguity;
- late V5 already showed that binary +1R-vs-SL alone mixed different path types;
- this is a continuation-strength information audit, not an Entry filter.

Secondary diagnostic:
- ordinal path strength over `L_CONTINUE, L_RECOVER, W_GIVEBACK, W_CONTINUE`.

Do not switch primary outcome after results.

## 7. Chronological folds

Frozen:

```text
F1 train 2023       -> eval 2024
F2 train 2023-2024  -> eval 2025
```

No random CV as claim-grade evidence.

## 8. Model discipline

Use the exact recovered/frozen late-V5 raw-convolution + Ridge diagnostic implementation if its code can be recovered and audited.

Before execution, record:
- exact script SHA;
- input tensor SHA or source data identities;
- kernel count/features;
- seeds;
- Ridge alpha grid;
- timeframe aggregation rule.

If the prior implementation cannot be reproduced exactly, rebuild ONE fixed implementation before opening outcomes. Do not compare several implementations and pick the best.

Individual timeframe results are diagnostic only.
Do not promote M30 or another timeframe because it looks strongest in one year.

## 9. Primary falsification

The real-context claim is supported only if Arm C beats Arm B in the same direction in BOTH chronological evaluation years.

Minimum directional condition:

```text
AUC_C_2024 > AUC_B_2024
AND
AUC_C_2025 > AUC_B_2025
```

Also report paired prediction uncertainty using calendar-month cluster resampling or another preregistered time-cluster method.

Classification:

### `CONTEXT_INFORMATION_SUPPORTED`

Requires:
- real context beats GOLDx3 in both years;
- pooled/time-cluster evidence is directionally consistent;
- no obvious alignment leakage;
- improvement is not explained by a tiny number of events.

This is information evidence only, not a strategy pass.

### `CAPACITY_ARTIFACT_OR_NO_INCREMENTAL_CONTEXT`

If GOLDx3 matches/exceeds real context in either chronological year, close the claim that XAUEUR/USDJPY adds stable incremental information under this formulation.

Do not search alternative context-market combinations in the same phase.

### `INCONCLUSIVE_SMALL_SAMPLE`

If point estimates improve in both years but uncertainty is too wide to distinguish C from B.

Do not escalate model complexity merely to sharpen the result.

## 10. Additional controls after primary classification

Only if the primary C>B direction holds in both years may the same frozen implementation run:

- one-bar / one-period stale-context control;
- within-day time-shift control;
- direction/mirror diagnostics where mechanically meaningful.

Do not run these first and choose the most favorable control definition.

## 11. What V6-001A does NOT authorize

- no trading filter;
- no probability threshold;
- no position sizing;
- no Entry change;
- no exit change;
- no online adaptation;
- no Transformer/JEPA escalation;
- no extra market selection;
- no GOLD 2022 tuning;
- no GOLD# 2021 inspection.

## 12. Next-stage branching

If context information is supported:

```text
V6-001B
-> determine whether remaining chronological weakness is
   hidden-context insufficiency vs genuine concept drift
-> only then consider conservative causal adaptation
```

If context information is not supported:

```text
close this hidden-context formulation
-> return to event/problem formulation
-> do not replace XAUEUR/USDJPY with a market shopping exercise
```
