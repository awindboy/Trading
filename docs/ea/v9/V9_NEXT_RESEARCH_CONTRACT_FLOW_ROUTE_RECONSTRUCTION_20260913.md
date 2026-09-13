# V9 Next Research Contract — Flow-Route Grammar Reconstruction

Date: `2026-09-13`
Status: `ACTIVE NEXT RESEARCH CONTRACT / SUPERSEDES STATE-ACTION AND SETUP-CENTRIC WORK`
Production authority: `NONE`
EA authority: `NONE`
Future-hidden: `2025-07 LOCKED`
Final reserve: `GOLD# 2021 UNTOUCHED`

## 1. Objective

Reconstruct the original V9 Grammar at the correct semantic scale:

```text
ORIGIN
-> DELIVERY / MOVEMENT
-> ARRIVAL
-> RESPONSE
-> RESOLUTION
-> NEXT DELIVERY / NEXT ROUTE
```

Do not spend the current phase optimizing trades.

The immediate goal is a compact, evidence-backed `FLOW_ROUTE` ledger that explains long contiguous price paths without degenerating into hourly alignment-state flips.

## 2. Historical research recovery boundary

The latest research audit established the following carry-forward boundary.

### Reuse

```text
Stage 1 Atlas research unit:
  FLOW LEG / DELIVERY PATH / ARRIVAL / NEXT STATE

Stage 2:
  exact code-owned FVG / OB / swing-liquidity geometry and lifecycle

Stage 3:
  arrival -> response -> next delivery as the correct structural question

Later hierarchy:
  H4/H1 nested topology, authority strength, uncertainty and transition buffers
  only as context observations
```

### Do not reuse as authority

```text
early 80-90% acceptance/rejection figures
last accepted probe before next state
future-selected last-event logic
H1 realign as continuation prediction
state-run boundary as FLOW_ROUTE boundary
```

The full checkpoint is:

`V9_FLOW_ROUTE_RESEARCH_RECOVERY_CHECKPOINT_20260913.md`

## 3. Workstream A0 — build the canonical chronological route-event stream first

Before assigning a single new FLOW_ID, construct one clean event stream from existing strict evidence plus authoritative price context.

Required existing sources:

```text
docs/ea/v9/results/market_flow_atlas/MARKET_FLOW_EVENT_LEDGER.csv
docs/ea/v9/results/market_flow_atlas/POI_INTERACTION_CLUSTER_STUDY_STRICT.csv
docs/ea/v9/results/market_flow_atlas/LIQUIDITY_DELIVERY_CLUSTER_STUDY_STRICT.csv
```

Use authoritative raw M1/H1/H4 only to attach price/context facts and to rebuild exact objects when needed. M1 wins any factual dispute.

Produce:

```text
FLOW_ROUTE_EVENT_STREAM.csv
```

Minimum fields:

```text
BLOCK
EVENT_TIME
EVENT_TYPE
EVENT_ID
EVENT_SIDE / DIRECTION
PRICE_LOW
PRICE_HIGH
OBJECT_IDS
OBJECT_FAMILY
SOURCE_TIMEFRAME
H4_CONTEXT
H1_CONTEXT
EXACT_SOURCE_STATUS
ANSWER_SHEET_NOTES
```

Do not use old `accepted_through_*`, `reversal_dominant_*`, favorable/adverse future-window measurements, or any later-outcome column to define the route itself.

## 4. Workstream A1 — Answer-sheet FLOW_ROUTE ledger

Use consumed answer-sheet periods first:

```text
2025-01..06
2026-01..02
```

Future-visible interpretation is allowed only for semantic discovery and must be clearly marked `ANSWER_SHEET`.

Create:

```text
ANSWER_SHEET_FLOW_ROUTE_LEDGER.csv
```

Minimum conceptual fields:

```text
FLOW_ID
BLOCK
FLOW_START
FLOW_END
DELIVERY_SIDE

ORIGIN
  exact reference ids
  time/price range
  answer-sheet semantic role

DESTINATION SET
  candidate landmark ids
  role hypotheses
  arrival/consumption status

ROUTE EVENTS
  departure
  same-side delivery evidence
  landmark arrival
  opposing/local response
  acceptance/rejection/balance/unresolved
  destination consumption
  route continuation
  route completion/reset/remap

CONTEXT OBSERVATIONS
  H4 authority/phase
  H1 local relation
  uncertainty

LOCAL_OBSERVATION_CHANGES_INSIDE_ROUTE
NEXT_FLOW_ID
ANSWER_SHEET_NOTES
```

The ledger must preserve exact object IDs and timestamps where code-owned objects exist.

## 5. Workstream A2 — starting segmentation hypothesis, explicitly not a rule

The first reconstruction pass should inspect whether coherent routes can be seen as:

```text
ORIGIN
-> repeated same-side delivery / progress toward meaningful landmarks
-> ARRIVAL
-> RESPONSE events, including possible opposite-side raids
-> RESOLUTION
-> either another delivery inside the same route
   or route completion/remap
```

Important:

- a same-side liquidity delivery is evidence of delivery/progress, not proof of a route;
- no fixed number of same-side deliveries defines a route;
- one opposite-side raid does not automatically create an opposing route;
- one H1/H4 label change does not automatically split a route;
- response semantics must be learned from many contiguous cases.

The first key research question is:

> When price produces an opposite-side raid/POI response inside an ongoing delivery path, what distinguishes ordinary response/repair from genuine completion of the old route and earning of a new route?

## 6. Workstream B — Compression criterion

A candidate Grammar is good only if it reduces many bars/events to a smaller number of coherent routes.

Required checks:

- number/duration of FLOW_ROUTE legs;
- number of H1 alignment flips inside the same route;
- number of H4 local observation changes inside the same route;
- route continuity across ordinary counterflow;
- number of landmark arrivals/responses inside each route;
- difficult-period behavior;
- explicit unresolved segments.

Produce:

```text
OBSERVATION_FLIP_VS_ROUTE_CHANGE_AUDIT.csv
```

Do not force a route split merely to improve retrospective neatness.

## 7. Workstream C — Arrival / response semantics

Research a minimal reusable response vocabulary.

Candidate concepts, not frozen labels:

```text
TRANSIT ARRIVAL
TERMINAL / CAMPAIGN-CHANGING ARRIVAL
LOCAL RESPONSE / REPAIR
REJECTION
ACCEPTANCE / CONSUMPTION
BALANCE / ABSORPTION
ROUTE CONTINUATION
ROUTE COMPLETE
OPPOSING ROUTE EARNED
UNRESOLVED
```

The purpose is not to classify every chart perfectly. Prefer explicit unresolved cases to one-off explanations.

Maintain:

```text
FLOW_ROUTE_VOCABULARY.md
UNRESOLVED_FLOW_ROUTE_CASES.csv
```

Every proposed semantic distinction must survive multiple consumed examples before promotion.

## 8. Workstream D — Counterexamples and difficult periods

The same route language must be tested on:

- strong directional periods;
- repeated repairs;
- balances/ranges;
- transition-heavy periods, especially consumed `2025-05`;
- genuine side changes;
- ambiguous/unresolved segments;
- consumed `2026 Jan-Feb` as a second block.

A valid Grammar should explain difficult periods as different route/resolution behavior, not by month-specific exceptions.

## 9. Workstream E — Separate observations from route semantics

At every research case, explicitly record:

```text
LOCAL OBSERVATIONS
H4/H1 labels
```

separately from:

```text
FLOW_ROUTE IDENTITY / STATUS
```

Measure how often H1/H4 observation flips occur without a route change.

This is a primary test of whether the research has escaped bar-by-bar state classification.

## 10. Workstream F — Causal FLOW_ROUTE contract

Only after answer-sheet semantics stabilize, build a prefix-only version.

At each decision/event time, causal state may contain only information already revealed:

```text
CAUSAL_FLOW_ID / hypothesis id
KNOWN_ORIGIN
ACTIVE_DESTINATION_CANDIDATES
KNOWN_ARRIVALS
KNOWN_RESPONSES
ROUTE_STATUS
UNRESOLVED QUESTIONS
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
OBJECT_LEDGER_HASH
PREFIX_HASH
```

Never populate causal state with the answer-sheet endpoint before it becomes knowable.

A future-selected 'true destination' may be used only as an evaluation label, never as live input.

## 11. Workstream G — AI semantic packet

Only after the causal route facts are reproducible should an AI packet be frozen.

AI questions should focus on route semantics:

```text
What flow is active?
What origin still has authority?
Which landmarks are plausible destinations?
Is the current arrival transit, terminal, or unresolved?
What did the response change?
Did the prior route continue, complete, or remap?
What new route is earned, if any?
```

Do not ask AI merely to infer H1/H4 alignment that code already knows.

## 12. Workstream H — Trading extraction after Grammar gate

Only after route reconstruction passes should the project extract trading actions.

Then compare, on the same causal route representation:

```text
MECHANICAL policy
AI discretionary policy
HUMAN + Grammar visualization research
```

This comparison is explicitly deferred. Do not conclude now that AI, mechanical trading, or human discretion is superior.

Old COUNTER/WITH_PARENT, H1-native, and state-action variants may be used as historical baselines only.

## 13. Output gate before trading research resumes

Required outputs:

1. `FLOW_ROUTE_EVENT_STREAM.csv`;
2. `ANSWER_SHEET_FLOW_ROUTE_LEDGER.csv` for consumed answer-sheet periods;
3. `FLOW_ROUTE_VOCABULARY.md`;
4. `OBSERVATION_FLIP_VS_ROUTE_CHANGE_AUDIT.csv`;
5. `UNRESOLVED_FLOW_ROUTE_CASES.csv`;
6. difficult-period counterexample report;
7. causal FLOW_ROUTE reconstruction protocol;
8. prefix-only causal replay parity;
9. versioned route packet/render identity if AI is used.

Only after these are accepted may strategy extraction restart.

## 14. What is explicitly banned in the current phase

Do not:

- run another `H1_REALIGN -> trade` optimization;
- infer route continuation from H1 realignment alone;
- use the old nine-state table as the core Grammar;
- optimize state-action P/L;
- remove M15/M5 or declare H1-native superior without a later controlled comparison;
- optimize entry/SL/TP from the old candidate universe;
- restart ML direction/scheduler work;
- turn an arrival into automatic entry/exit;
- define a route by a fixed duration, fixed R, fixed retracement, fixed event count, or fixed number of liquidity deliveries;
- use old future-window columns as route inputs;
- open `2025-07` or `2021`.

## 15. Data order

Preferred research order:

```text
2025H1 + 2026JF consumed answer-sheet
-> FLOW_ROUTE semantics
-> causal route contract
-> 2024 consumed replay as execution/counterexample research
-> policy extraction/comparison
-> freeze
-> explicit future-hidden gate decision
```

Future-hidden gate remains `NOT SATISFIED`.
