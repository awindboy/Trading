# V9 Research State

Date: `2026-09-13`
Status: `ACTIVE / FLOW-ROUTE GRAMMAR RECONSTRUCTION`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`

## Current research thesis

The valuable V9 hypothesis is not that H4/H1 alignment predicts the next candle.

It is that price can be usefully compressed as repeated routes:

```text
ORIGIN
-> MOVEMENT / DELIVERY
-> ARRIVAL
-> RESPONSE
-> RESOLUTION
-> NEXT MOVEMENT / ROUTE
```

The current task is to determine whether that route language can be made compact, reproducible, and causal.

## What has been corrected

Recent research showed that directly trading:

```text
STRONG Parent + H1 REALIGN
```

can perform very differently across periods even when the larger H4 context remains similar.
This does **not** by itself refute the original flow Grammar. It shows that `H1_REALIGN` was being used as if it were the Grammar's movement-continuation event when it is actually a local observation produced after price has already moved.

Likewise, the prior `State + Transition + Route + Position -> Action` pivot remains useful as a historical attempt, but it over-weighted discrete H4/H1 state labels. It is no longer the active top-level model.

## Current semantic hierarchy

### Core Grammar

```text
FLOW_ROUTE / FLOW_LEG
  ORIGIN
  ACTIVE DELIVERY
  ARRIVAL
  RESPONSE
  RESOLUTION
  NEXT ROUTE
```

### Context observations

```text
H4 authority / phase
H1 aligned / interrupt / unresolved
landmark/object lifecycle
uncertainty
```

Context observations may change inside one persistent flow.

## Primary unknowns

The project must still learn:

1. how to identify a meaningful origin without hindsight;
2. how to represent one or more active destination candidates;
3. what distinguishes transit arrival from terminal/campaign-changing arrival;
4. what response/acceptance/rejection means in a compact cross-period way;
5. when a route remains the same despite H1/H4 local observation changes;
6. when the old route is complete and a genuinely new route is earned;
7. which route semantics can be known causally rather than only from the answer sheet.

## Current evidence status

Retain as historical evidence:

- H4/H1 nested topology exists and is useful context;
- uncertainty/neutralization should remain explicit;
- direct clean H4 flips are uncommon;
- code-owned landmarks are plentiful and object existence is not strategic importance;
- old COUNTER/WITH_PARENT and scheduler studies demonstrate that event names do not determine actions;
- aggressive fixed TP/exit rules can destroy long-tail winners.

Do not promote these into the core route definition.

## Active output to build

`FLOW_ROUTE_LEDGER` and a causal counterpart.

Success means:

- long contiguous periods are covered;
- the number of route changes is materially smaller than bar-by-bar alignment flips;
- each route has an interpretable origin/destination story;
- arrival/response/resolution vocabulary remains compact across consumed periods;
- difficult periods produce more unresolved/transition routes rather than requiring special exceptions;
- causal replay can preserve an active route without seeing the future.

## Explicitly not current research

- optimizing H1 realign entries;
- proving H1-native is superior;
- optimizing nine discrete states;
- building a state-specific LONG/SHORT table;
- further ML direction/scheduler work;
- reopening old setup mining.

## Data classification

```text
2024        consumed postmortem/research
2025 Jan-Jun consumed answer-sheet
2026 Jan-Feb consumed answer-sheet
2025-07     future-hidden LOCKED
2021        untouched final reserve
```

Future-hidden gate: `NOT SATISFIED`.
