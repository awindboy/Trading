# V9 Development Handoff

Last updated: `2026-09-13`
Status: `ACTIVE / FLOW-ROUTE GRAMMAR RECONSTRUCTION`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
GitHub HEAD at latest research handoff: `3eca5a633b393269ecba2886055f663de1d22360`

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

## What the latest research recovery established

The pre-drift Atlas already had the right research unit before the project centered H4/H1 state labels.

Reusable historical pieces:

```text
Stage 1  FLOW LEG / DELIVERY PATH / ARRIVAL / NEXT STATE
Stage 2  exact POI/FVG/OB/swing-liquidity geometry + lifecycle
Stage 3  arrival -> response -> next delivery as the structural question
Later     H4/H1 hierarchy + uncertainty as route context only
```

Existing strict event sources that should be reused immediately:

```text
docs/ea/v9/results/market_flow_atlas/MARKET_FLOW_EVENT_LEDGER.csv
docs/ea/v9/results/market_flow_atlas/POI_INTERACTION_CLUSTER_STUDY_STRICT.csv
docs/ea/v9/results/market_flow_atlas/LIQUIDITY_DELIVERY_CLUSTER_STUDY_STRICT.csv
```

The exact-object engine remains useful:

```text
scripts/v9_ict_object_engine.py
```

and authoritative M1 remains the final price/time authority.

Do not reuse as edge/labels:

```text
early 80-90% acceptance/rejection percentages
last accepted probe before next state
future-selected last event
H1 realign as continuation signal
state-run boundaries as route boundaries
```

No new FLOW_ROUTE count, route-duration threshold, or trading edge was frozen in the latest session. The research stopped immediately before constructing the first new route ledger.

## Immediate continuation point

The next session should **not** reproduce old H1-state counts and should **not** start with a trade.

Start with the strict chronological arrival stream for consumed `2025H1 + 2026JF`.

### Step 1 — build a clean route-event stream

Combine, in chronological order:

```text
LIQUIDITY_DELIVERY
POI_CLUSTER_TOUCH
exact H1/H4 object references
raw/authoritative price context
```

Carry H4/H1 labels only as side/context columns. Do not let them split routes.

Expected new research output:

```text
FLOW_ROUTE_EVENT_STREAM.csv
```

Minimum fields:

```text
BLOCK
EVENT_TIME
EVENT_TYPE
EVENT_ID
DIRECTION / SIDE
PRICE_LOW / PRICE_HIGH
OBJECT_IDS
OBJECT_FAMILY / TIMEFRAME where available
H4_CONTEXT
H1_CONTEXT
ANSWER_SHEET_NOTES
```

### Step 2 — reconstruct route legs answer-sheet first

Build:

```text
ANSWER_SHEET_FLOW_ROUTE_LEDGER.csv
```

Each route should attempt to preserve:

```text
FLOW_ID
FLOW_START / FLOW_END
DELIVERY_SIDE
ORIGIN reference(s)
ACTIVE_DESTINATION candidate(s)
ARRIVAL sequence
RESPONSE sequence
RESOLUTION
NEXT_FLOW_ID
LOCAL_OBSERVATION_CHANGES_INSIDE_ROUTE
UNRESOLVED flags
```

Use same-side liquidity deliveries as **candidate evidence** that one delivery path may still be active. This is not a rule and there is no fixed required count.

When an opposite-side liquidity raid or opposing POI arrival occurs inside an apparent route, do not immediately split the route. Record it as a response/counterflow candidate and ask whether subsequent arrival/response evidence actually completes/remaps the old route.

### Step 3 — quantify whether the route model is doing something nontrivial

Required audit:

```text
number of FLOW_ROUTE changes
vs
number of H1 relation flips
vs
number of H4 local-state changes
```

A useful route Grammar should contain multiple local observation changes inside some persistent routes. If route identity simply tracks H1/H4 flips, the reconstruction has failed.

### Step 4 — difficult-period test

After an initial vocabulary is usable, apply the same semantics to:

```text
2025-05 transition-heavy period
2026 Jan-Feb consumed block
```

Do not create month-specific labels.

### Step 5 — causalization only after answer-sheet vocabulary stabilizes

Then build a prefix-only route state with:

```text
KNOWN_ORIGIN
ACTIVE_DESTINATION_CANDIDATES
KNOWN_ARRIVALS
KNOWN_RESPONSES
ROUTE_STATUS
UNRESOLVED_QUESTIONS
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
```

No future-selected endpoint may enter the causal packet.

## Why the early Atlas is useful but not authoritative

The early Atlas used the right high-level question:

```text
reaction / arrival -> price delivery -> next reaction / arrival -> ...
```

but some early response/acceptance percentages were later found to reuse classification-window movement or future-selected event placement.

Therefore recover:

```text
the research unit
exact event geometry
the arrival/response/delivery question
```

but not:

```text
the contaminated predictive percentages
future-selected semantic labels
```

## What remains deliberately paused

Do not continue by default:

- direct H1-realign trading studies;
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

## Required first read in the next session

After the core authority, read:

`V9_FLOW_ROUTE_RESEARCH_RECOVERY_CHECKPOINT_20260913.md`

It records exactly which historical findings are safe to reuse and where the latest session stopped.
