# V9 Discretionary Trading Pipeline — Sequential Map + Trigger

Date: `2026-09-12`
Status: `DEFERRED / DOWNSTREAM STRATEGY-EXECUTION PIPELINE`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## Current phase

Do not use this pipeline as the current strategy-development loop.

Current work is governed by:

`V9_MARKET_FLOW_GRAMMAR_CONTINUOUS_HIERARCHY_AUTHORITY_20260912.md`

Resume this pipeline only after a strategy-extraction draft is frozen.

## Expected upstream strategy state when resumed

The future MAP should inherit:

```text
H4 MACRO AUTHORITY
H4 PHASE
H1 AUCTION ROLE
PARENT CONTINUITY / RESET STATE
SELECTED LANDMARK ROLES
ROUTE / DESTINATION SEMANTICS
```

It must not revert to selecting one FVG/OB and sleeping until price touches it.

## Deferred causal sequence

```text
revealed causal M1
-> exact H4/H1 object universe
-> state / Parent map
-> frozen runtime wake event
-> LTF trigger only when authorized
-> Child entry + fixed Hard SL
-> runtime guard
-> state/route review
-> HOLD / EXIT / REMAP
```

## Permanent downstream rules

- start from revealed chronological prefix;
- do not preload future for active decisions;
- code owns object geometry/lifecycle;
- AI owns semantic role;
- exact executable price comes from code/runtime;
- Hard SL fixed before entry, never widen;
- Parent and Child remain separate;
- Child loss does not automatically kill Parent;
- Child win does not prove Parent;
- no hindsight rescue/backfill;
- no minimum-R;
- no fixed ATR/S stop or TP;
- no retry cap / cooldown / fixed no-chase / trade quota;
- no mandatory pattern chain;
- runtime guards ordinary price action; AI is called only at planned events.

## Resume gate

Do not reactivate this pipeline until the Atlas provides:

1. stable hierarchical market grammar;
2. compact route/destination semantics;
3. explicit Parent-continuity versus reset semantics;
4. exact landmark-role mapping;
5. frozen strategy-extraction draft that says what is knowable before risk is paid.

## 2026-09-12 upstream checkpoint

A first strategy-extraction draft now exists:

`V9_STRATEGY_EXTRACTION_DRAFT_PARENT_CHILD_FLOW_20260912.md`

Do not reactivate discretionary/live use yet.

The remaining resume gate is implementation/parity under:

`V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`

The runtime must reproduce the consumed-data decision process causally before this downstream pipeline becomes active.


## 2026-09-12 causal runtime checkpoint

<!-- V9_CAUSAL_STATE_MACHINE_IMPL_20260912 -->

The deterministic causal state-machine mechanics gate has passed on consumed data.

This downstream discretionary pipeline is still not live/production authority. Its next activation dependency is narrower now:

```text
accepted deterministic runtime
-> freeze AI review/remap packet + scheduler + staleness/outage behavior
-> consumed causal external-decision dry-run
-> explicit future-hidden gate decision
```

When this pipeline resumes, use `run-until-gate` and deterministic request packets. Do not bypass an execution/review/remap gate by reading ahead or filling from stale completed-bar prices.

`2025-07` remains LOCKED.
