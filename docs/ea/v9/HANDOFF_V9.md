# V9 Development Handoff

Last updated: `2026-09-13`
Status: `ACTIVE / FLOW-ROUTE GRAMMAR RECONSTRUCTION`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Current correction

V9 originally pivoted away from setup mining because the market appeared to repeat a continuous process:

```text
movement / delivery
-> arrival
-> response
-> next movement / delivery
-> next arrival
-> ...
```

Later research accidentally over-promoted the supporting H4/H1 state labels into the Grammar itself and began testing ideas such as:

```text
H4 STRONG + H1 REALIGN -> trade
state + transition -> action
```

That is now explicitly corrected.

`H1_REALIGN` means that price has already moved enough for an H1 relation label to align again. It is not, by itself, a forecast of the next leg. Bar-by-bar alignment changes do not equal FLOW_ROUTE changes.

## Current model

Primary semantic sequence:

```text
ORIGIN
-> ACTIVE DELIVERY
-> LANDMARK ARRIVAL
-> RESPONSE
-> RESOLUTION
-> NEXT DELIVERY or ROUTE COMPLETE
-> NEXT ROUTE
```

Supporting observations:

```text
H4 authority / phase
H1 aligned / interrupt / unresolved
exact POI / liquidity / object lifecycle
```

Supporting observations help interpret the route. They do not define route identity by themselves.

## Current immediate work

Build a new FLOW_ROUTE research ledger on consumed data.

Minimum conceptual fields:

```text
FLOW_ID
BLOCK
START / END
FLOW_SIDE
ORIGIN
ORIGIN_ROLE
ACTIVE_DESTINATION_CANDIDATES
ARRIVAL_EVENTS
RESPONSE_EVENTS
ROUTE_STATUS
RESOLUTION
NEXT_FLOW_ID

CONTEXT_OBSERVATIONS
  H4 authority / phase
  H1 local relation
  uncertainty

EXACT_OBJECT_REFERENCES
ANSWER_SHEET vs CAUSAL label status
```

The ledger should compress long contiguous price action into meaningful flow legs. If it flips every hour merely because H1 alignment flips, the model has failed the intended Grammar definition.

## Research stages

### Stage 1 — answer-sheet flow reconstruction

Use consumed `2025H1 + 2026JF` to discover compact flow-route semantics.
Full future-visible interpretation is allowed only as answer-sheet research and must be labeled as such.

### Stage 2 — counterexamples / difficult periods

Test whether the same route language explains trend, repair, balance, uncertainty, and transition periods without month-specific exceptions.

### Stage 3 — causalization

Build prefix-only route state that knows only what has actually been revealed.
Separate:

```text
ANSWER_SHEET_ROUTE_ROLE
CAUSALLY_KNOWN_ROUTE_ROLE
```

No future-selected destination or 'last event before next state' may leak into causal decisions.

### Stage 4 — policy extraction later

Only after the route grammar is causal and compact should the project compare:

```text
mechanical policy
AI discretionary policy
human + Grammar visualization research
```

Do not compare them yet using H1 realign or old setup-candidate universes and call that a test of the Grammar.

## What is deliberately paused

Do not continue by default:

- direct H1-realgin trading studies;
- H1-native strategy optimization;
- state-action policy table construction;
- COUNTER/WITH_PARENT candidate optimization;
- AI entry filtering of the old candidate set;
- R-milestone scheduler optimization;
- ML scheduler/direction work.

Historical results remain useful as evidence that these abstractions were insufficient.

## Permanent guardrails

- no future peek / hindsight backfill;
- Hard SL fixed before entry and never widened once trading extraction resumes;
- stopped Child is dead;
- Parent/Child separation retained;
- code owns exact geometry and execution facts;
- AI may own semantic roles only from causal context;
- no hidden thresholds, min-R, cooldown, retry cap, fixed no-chase, fixed TP, or trade quotas;
- explicit unresolved states are valid;
- `2025-07` stays locked and `2021` stays untouched.

## Next session start point

Do not start from a trade.
Start from a continuous price segment and ask:

```text
What flow is active?
Where did it originate?
What is it delivering toward?
What did it arrive at?
What response occurred?
Did the route continue, resolve, or remap?
```

That is the current V9 research task.
