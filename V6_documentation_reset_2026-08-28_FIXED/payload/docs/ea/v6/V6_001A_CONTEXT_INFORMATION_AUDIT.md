# V6-001A — Same-Capacity Cross-Market Context Information Audit

Status: `QUEUED / PRE-REGISTERED CHILD / NOT CURRENT GENERATION GATE`  
Date: `2026-08-28`  
Production authority: `NONE`  
Parent: `V6-001 CONTEXT-MEASUREMENT HYPOTHESIS REGISTRY`

## 0. Scope correction

This contract is preserved because late V5 produced a specific cross-market clue with an unresolved capacity confound.

V6-001A is one `Family B — cross-market / relative state` child.

It is NOT:

- the definition of V6;
- a required gate before every other indicator/context family;
- proof of strategy if passed;
- proof that all hidden/context hypotheses fail if rejected.

A fail closes only the exact XAUEUR/USDJPY formulation below.

No replacement-market shopping is allowed inside this child.

## 1. Question

Late V5 scratch suggested synchronized `XAUEUR# + USDJPY#` state improved event-conditioned path discrimination in both 2024 and 2025.

But the context model had approximately three times the input channels.

V6-001A asks:

> Does real synchronized cross-market context provide incremental information beyond a same-capacity input that contains no new market information?

This is a capacity-confound cleanup of consumed hypothesis-generation evidence.

## 2. Population

Exact V3-003C `BROAD CONTROL`.

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

BTCUSD# is excluded from this child because the frozen hypothesis concerns gold/currency decomposition, not broad risk appetite.

No new external data source is introduced.

## 4. Causal alignment

For every GOLD event timestamp:

- use only completed GOLD and context bars available no later than the event;
- preserve alignment staleness information;
- do not forward-fill future context;
- fail closed if required history is unavailable.

Use the same M1/M5/M30/H4 event-history boundaries across all arms.

## 5. Arms

### A — GOLD-only descriptive reference

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

- match the ~30-channel dimensionality of the real-context arm;
- add zero new market information.

### C — real synchronized context — PRIMARY TEST

```text
[GOLD block, XAUEUR block, USDJPY block]
```

Use exactly the same model family, random kernels/features, seeds, regularization-search policy, timeframe aggregation, and evaluation splits as Arm B.

## 6. Outcome

Primary child outcome:

```text
W_CONTINUE (+1 -> +2 before 0)
vs
L_CONTINUE (-1 -> -2 before 0)
```

Reason:

- removes the most obvious giveback/recovery ambiguity;
- late V5 showed binary +1R-vs-SL mixes different path types;
- this is a continuation-strength information audit, not an Entry filter.

Secondary diagnostic:

```text
L_CONTINUE
L_RECOVER
W_GIVEBACK
W_CONTINUE
```

Do not change the primary outcome after results.

## 7. Frozen chronology

```text
F1 train 2023       -> eval 2024
F2 train 2023-2024  -> eval 2025
```

No random CV as claim-grade evidence.

## 8. Model discipline

Use the exact recovered/frozen late-V5 raw-convolution + Ridge diagnostic if it can be recovered and audited.

Before execution record:

- exact script SHA;
- input tensor SHA or source identities;
- kernel count/features;
- seeds;
- Ridge alpha grid;
- timeframe aggregation rule.

If the prior implementation cannot be exactly reproduced, rebuild ONE fixed implementation before opening outcomes.

Do not compare implementations and select the best.

Individual timeframe results are diagnostic only. Do not select a best timeframe.

## 9. Primary falsification

The exact cross-market claim is supported only if Arm C beats Arm B in the same direction in BOTH chronological evaluation years.

Minimum condition:

```text
AUC_C_2024 > AUC_B_2024
AND
AUC_C_2025 > AUC_B_2025
```

Also report paired prediction uncertainty using calendar-month cluster resampling or another frozen time-cluster method.

### `CONTEXT_INFORMATION_SUPPORTED`

Requires:

- real context beats GOLDx3 in both years;
- pooled/time-cluster evidence is directionally consistent;
- no alignment leakage;
- result is not explained by a tiny number of events.

Interpretation:

```text
XAUEUR/USDJPY formulation contains incremental information
under this child design
```

This is not strategy authority.

### `CAPACITY_ARTIFACT_OR_NO_INCREMENTAL_CONTEXT`

If GOLDx3 matches/exceeds real context in either chronological year:

```text
close XAUEUR/USDJPY incremental-information claim
under this formulation
```

Do not search replacement context-market combinations inside V6-001A.

This result does NOT close independently preregistered V6 measurement families.

### `INCONCLUSIVE_SMALL_SAMPLE`

If point estimates improve both years but uncertainty is too wide.

Do not increase model complexity just to sharpen the result.

## 10. Additional controls

Only if primary C>B holds in both years may the same frozen implementation run:

- one-bar/one-period stale context;
- within-day time-shift context;
- direction/mirror diagnostics where meaningful.

Do not run several controls first and choose the favorable definition.

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

## 12. Return to parent registry

After classification, freeze the result and return to:

```text
V6-001 CONTEXT-MEASUREMENT HYPOTHESIS REGISTRY
```

If supported:
- mark Family B / exact XAUEUR+USDJPY formulation as information-supported;
- only later may a separate child ask whether it explains residual chronology or conditions a stage-specific policy.

If failed:
- close the exact formulation;
- do not market-shop inside the child;
- continue only with independently preregistered parent-registry hypotheses.

If inconclusive:
- record small-sample uncertainty;
- do not escalate complexity simply to force a decision.
