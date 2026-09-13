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

## Latest recovery result — where the useful old research actually was

The research-history audit found that the project had the correct semantic scale at the beginning of the Market Flow Atlas:

```text
Stage 1
  FLOW LEG
  DELIVERY PATH
  ARRIVAL
  NEXT STATE

Stage 2
  exact code-owned object geometry/lifecycle

Stage 3
  arrival -> response -> next delivery
```

The later H4/H1 hierarchy remains useful because it showed nested timescales, uncertainty, and transition buffers, but it must be treated as **route context**, not as the route itself.

Historical evidence safe to reuse immediately:

- chronological exact POI cluster touches;
- chronological H1/H4 liquidity deliveries/raids;
- object IDs, prices, source timeframes and lifecycle;
- H4/H1 context labels as descriptive columns;
- uncertainty/neutralization and side-change-buffer evidence as contextual interpretation.

Historical evidence explicitly unsafe as causal/predictive authority:

- early 80-90% response/acceptance figures that reused part of the classification window;
- `last accepted probe before next state` and related future-selected events;
- state-run boundaries as automatic flow boundaries;
- H1 realignment as next-leg prediction.

## Existing data assets to start from

```text
docs/ea/v9/results/market_flow_atlas/MARKET_FLOW_EVENT_LEDGER.csv
docs/ea/v9/results/market_flow_atlas/POI_INTERACTION_CLUSTER_STUDY_STRICT.csv
docs/ea/v9/results/market_flow_atlas/LIQUIDITY_DELIVERY_CLUSTER_STUDY_STRICT.csv
```

Relevant exact-object code:

```text
scripts/v9_ict_object_engine.py
```

The strict event ledger currently contains historical POI/liquidity/state events, but **no new FLOW_ROUTE identity has yet been frozen**.

## Primary unknowns

The project must still learn:

1. how to identify a meaningful origin without hindsight;
2. how to represent one or more active destination candidates;
3. what distinguishes transit arrival from terminal/campaign-changing arrival;
4. what response/acceptance/rejection means in a compact cross-period way;
5. when a route remains the same despite H1/H4 local observation changes;
6. when the old route is complete and a genuinely new route is earned;
7. which route semantics can be known causally rather than only from the answer sheet.

## Immediate research hypothesis to investigate — not authority

Start from the chronological landmark sequence.

A plausible route may appear as:

```text
origin
-> one or more same-side deliveries toward meaningful liquidity/POI
-> arrival
-> local/opposite response events may occur
-> old route either survives and delivers again
   or is genuinely resolved/remapped
```

This is only a reconstruction hypothesis.

Do not create rules such as:

```text
N same-side raids = one route
one opposite raid = route reversal
H1 realign = route continues
```

The research question is precisely which opposite-side/local events are merely responses inside the same route and which observations actually earn a new route.

## Active outputs to build next

```text
FLOW_ROUTE_EVENT_STREAM.csv
ANSWER_SHEET_FLOW_ROUTE_LEDGER.csv
FLOW_ROUTE_VOCABULARY.md
OBSERVATION_FLIP_VS_ROUTE_CHANGE_AUDIT.csv
UNRESOLVED_FLOW_ROUTE_CASES.csv
```

No new route-count or trading-performance result was completed before the latest session ended.

## Success criteria for the next ledger

- long contiguous periods are covered;
- the number of route changes is materially smaller than bar-by-bar alignment flips;
- each route has an interpretable origin/destination story;
- arrival/response/resolution vocabulary remains compact across consumed periods;
- difficult periods produce more unresolved/transition routes rather than requiring special exceptions;
- local H1/H4 observation flips can occur inside one persistent route;
- causal replay can eventually preserve an active route without seeing the future.

## Explicitly not current research

- optimizing H1 realign entries;
- proving H1-native is superior;
- optimizing nine discrete states;
- building a state-specific LONG/SHORT table;
- further ML direction/scheduler work;
- reopening old setup mining;
- comparing AI vs mechanical vs human trading before the route representation is frozen.

## Data classification

```text
2024         consumed postmortem/research
2025 Jan-Jun consumed answer-sheet
2026 Jan-Feb consumed answer-sheet
2025-07      future-hidden LOCKED
2021         untouched final reserve
```

Future-hidden gate: `NOT SATISFIED`.
