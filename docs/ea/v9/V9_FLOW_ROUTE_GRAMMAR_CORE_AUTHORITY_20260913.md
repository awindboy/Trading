# V9 Flow-Route Market Grammar — Core Authority

Date: `2026-09-13`
Status: `ACTIVE SEMANTIC RESEARCH AUTHORITY`
Production authority: `NONE`
EA authority: `NONE`
Market authority: `GOLD# ONLY`

## 1. Definition

V9 Grammar is a model of **continuous price flow**, not a classifier of H1/H4 candle alignment.

Canonical form:

```text
ORIGIN
-> ACTIVE MOVEMENT / DELIVERY
-> LANDMARK ARRIVAL
-> RESPONSE
-> RESOLUTION
-> NEXT DELIVERY or ROUTE COMPLETE / RESET
-> NEXT ROUTE
```

The central research unit is a `FLOW_ROUTE` (or `FLOW_LEG`).

A useful Grammar should compress many candles into a smaller number of persistent, meaningful routes.

## 2. Why this correction is necessary

The Atlas originally changed the research unit from `TRADE` to:

```text
FLOW LEG
AUCTION CYCLE
DELIVERY PATH
NEXT STATE
```

Later work discovered robust H4/H1 nested relationships. Those relationships are useful, but they were subsequently over-promoted into the semantic center of the Grammar.

This created an invalid shortcut:

```text
H1 interrupt
-> H1 realign
-> assume movement continuation
```

`H1_REALIGN` is retrospective with respect to the movement that produced the realignment. It can be a useful observation inside a route, but it is not itself proof of the next route or the next delivery.

## 3. Core semantic objects

### FLOW_ROUTE

A persistent price-delivery story linking an origin to one or more meaningful destinations.

### ORIGIN

The causally interpretable structure/area from which the current delivery is considered to have been earned.
An answer-sheet origin may be identified retrospectively during research, but causal authority requires a separately frozen rule for when that origin became knowable.

### ACTIVE DELIVERY

Price is progressing within the same route toward an active destination hypothesis.
Local opposite candles or H1 interruption do not automatically terminate the route.

### DESTINATION

A meaningful landmark/area that organizes the current delivery hypothesis.
Multiple destination candidates may coexist until evidence resolves their roles.

### ARRIVAL

Price reaches or consumes a meaningful landmark relevant to the active route.
Arrival is an event, not an automatic reversal or exit.

### RESPONSE

Price behavior after arrival that may support continuation, rejection, balance, absorption, or unresolved status.
The exact compact response vocabulary is an active research task.

### RESOLUTION

The market has supplied enough information to classify the prior arrival/response as one of:

```text
ROUTE_CONTINUES
DESTINATION_CONSUMED / NEW_DESTINATION_OPENS
ROUTE_COMPLETE / RESET
OPPOSING_ROUTE_EARNED
UNRESOLVED
```

These labels are conceptual authority; exact causal detection is not yet frozen.

## 4. Context observations

The following remain valuable but subordinate:

```text
H4 macro side / authority strength
H4 phase
H1 aligned / interrupt / unresolved
local balance / counterflow observations
```

They describe the environment in which the route unfolds.

They must not create a new FLOW_ROUTE by themselves.

Examples:

```text
same FLOW_ROUTE
  H1 ALIGNED
  -> H1 INTERRUPT
  -> H1 REALIGNS
  -> H1 INTERRUPT again
```

is allowed if origin/destination/route semantics remain intact.

Conversely, a genuine new route may begin before a slow completed-bar label cleanly flips, provided the route change is earned by causal arrival/response/resolution evidence.

## 5. Exact landmarks and strategic roles

Code owns exact geometry/lifecycle.

Research/AI may assign route roles such as:

```text
ORIGIN
TRANSIT
DESTINATION
ARRIVAL
RESPONSE_REFERENCE
CAMPAIGN_CHANGING
STALE / RETIRED
UNRESOLVED
```

Never infer exact execution geometry from a visual freehand box.

Do not equate:

```text
object exists
```

with:

```text
object matters to the active FLOW_ROUTE
```

## 6. Flow identity and route changes

A FLOW_ROUTE should be persistent enough to survive ordinary local noise.

The model fails if route identity flips merely because one H1/H4 relationship label flips.

A new route should require meaningful resolution of the previous origin/destination story.

Research must therefore distinguish:

```text
LOCAL OBSERVATION CHANGE
vs
FLOW_ROUTE CHANGE
```

This distinction is now mandatory.

## 7. What counts as Grammar quality

Do not evaluate Grammar quality by:

- next-hour H1 state persistence;
- H1 realign win rate;
- a state-specific P/L table;
- number of profitable setups extracted;
- how often H4/H1 labels agree.

Evaluate it by:

- contiguous coverage of price flow;
- compression into meaningful legs/routes;
- stability of route identity through local noise;
- meaningful linkage of origin -> destination -> arrival -> response -> next route;
- cross-period semantic reuse;
- explicit unresolved remainder;
- eventual causal reconstructability.

## 8. AI, code, and human roles

### Code

Owns:

- chronological reveal;
- bar construction;
- H4/H1 observations;
- object geometry/lifecycle;
- exact prices/timestamps;
- causal hashes;
- execution guards.

### AI research role

Potentially owns semantic questions that are difficult to reduce mechanically without overfit:

```text
Which exact landmarks organize the active route?
Is this arrival transit or terminal/campaign-changing?
What does the response imply about the old route?
Has the destination been consumed?
Did a new destination/route open?
Is the correct state genuinely unresolved?
```

AI is **not** needed to determine whether H1 candles are aligned.

### Human discretionary comparison

A Grammar visualization for a human may be researched later, but only after the causal FLOW_ROUTE representation is stable. Human/AI/mechanical comparison before that point tests different subjective setups, not the same Grammar policy.

## 9. Trading extraction is downstream

Do not yet assign:

```text
H1_REALIGN -> ENTER
ARRIVAL -> EXIT
ROUTE_CONTINUES -> automatic add
```

Trading policy comes only after the route model is sufficiently stable and causal.

At that later stage, compare mechanical/AI/human policy using the **same frozen route information**.

## 10. Permanent prohibitions

Do not:

- redefine the Grammar as an alignment state machine;
- count every H1 state flip as a new route;
- use future-selected destinations in causal replay;
- use 'last event before next move' hindsight labels as causal inputs;
- create one pattern/rule per example;
- add hidden thresholds to force route resolution;
- remove ambiguity merely to increase trade count;
- open 2025-07 or 2021 before the gate.
