# V9 Next Research Contract — Sequential Live-Like Map / Trigger / Position Replay

Date: `2026-09-12`
Status: `ACTIVE IMPLEMENTATION GATE / STRATEGY-EXTRACTION DRAFT FROZEN / NO HIDDEN REPLAY YET`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## Current authority

Current active research authority:

`V9_MARKET_FLOW_GRAMMAR_CONTINUOUS_HIERARCHY_AUTHORITY_20260912.md`

Do not use sequential replay as the primary development loop yet.

## What must happen first

Continue Atlas research in this order:

```text
continuous hierarchy
-> route / destination semantics
-> Parent continuity / authority-loss semantics
-> exact landmark roles
-> frozen strategy-extraction draft
```

Only then ask:

> Can the extracted decision process be reproduced causally and sequentially without hindsight?

## Downstream replay requirements

When resumed:

- start from future-hidden causal prefix;
- freeze event/trigger before resolution;
- no backfill;
- preserve Parent/Child separation;
- Hard SL fixed before entry and never widened;
- preserve exact object lifecycle;
- AI only at authorized planning/review events;
- process quality separated from outcome;
- no hidden thresholds mined from consumed data;
- explicit handling of WEAK / UNRESOLVED / AMBIGUOUS states rather than forcing direction.

## Hidden-data gate

`2025-07` remains locked.
`2021` remains untouched.

Do not open either because the consumed-data grammar looks promising.

## 2026-09-12 activation update

The prerequisite first strategy-extraction draft is now frozen:

`V9_STRATEGY_EXTRACTION_DRAFT_PARENT_CHILD_FLOW_20260912.md`

The immediate runtime contract is now governed by:

`V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`

The next work is to implement and verify the frozen decision process on the consumed periods, not to open hidden data.

Required consumed replay gate:

```text
1. versioned dual-clock replay state;
2. deterministic M15/H1/H4 semantic event scheduler;
3. M15/M5 OBJECT_KNOWN_AT convention;
4. Child pending/fill/Hard-SL/review/remap event priority;
5. exact consumed-period parity through actual merged implementation;
6. frozen implementation commit and hashes.
```

Only after these pass may the project decide whether `2025-07` can be unlocked.

Until then:

```text
2025-07 = LOCKED
2021 = UNTOUCHED
```

