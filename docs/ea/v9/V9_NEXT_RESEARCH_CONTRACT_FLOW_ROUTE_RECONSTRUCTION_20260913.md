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

## 2. Workstream A — Answer-sheet FLOW_ROUTE ledger

Use consumed answer-sheet periods first:

```text
2025-01..06
2026-01..02
```

Future-visible interpretation is allowed only for semantic discovery and must be clearly marked `ANSWER_SHEET`.

Create at least:

```text
FLOW_ID
BLOCK
FLOW_START
FLOW_END
FLOW_SIDE / DELIVERY_SIDE

ORIGIN
  object/reference ids
  time/price range
  semantic role

DESTINATION SET
  candidate landmark ids
  role hypotheses
  arrival/consumption status

ROUTE EVENTS
  departure
  landmark arrival
  response
  acceptance/rejection/unresolved
  destination consumption
  route continuation
  route completion/reset

CONTEXT OBSERVATIONS
  H4 authority/phase
  H1 local relation
  uncertainty

NEXT_FLOW_ID
ANSWER_SHEET_NOTES
```

The ledger must preserve exact object IDs and timestamps where code-owned objects exist.

## 3. Workstream B — Compression criterion

A candidate Grammar is good only if it reduces many bars/events to a smaller number of coherent routes.

Required checks:

- number/duration of FLOW_ROUTE legs;
- number of H1 alignment flips inside the same route;
- number of H4 local observation changes inside the same route;
- route continuity across ordinary counterflow;
- difficult-period behavior;
- explicit unresolved segments.

Do not force a route split merely to improve retrospective neatness.

## 4. Workstream C — Arrival / response semantics

Research a minimal reusable response vocabulary.

Candidate concepts, not frozen labels:

```text
TRANSIT ARRIVAL
TERMINAL / CAMPAIGN-CHANGING ARRIVAL
REJECTION
ACCEPTANCE / CONSUMPTION
BALANCE / ABSORPTION
ROUTE CONTINUATION
ROUTE COMPLETE
OPPOSING ROUTE EARNED
UNRESOLVED
```

The purpose is not to classify every chart perfectly. Prefer explicit unresolved cases to one-off explanations.

## 5. Workstream D — Counterexamples and difficult periods

The same route language must be tested on:

- strong directional periods;
- repeated repairs;
- balances/ranges;
- transition-heavy periods such as the already-consumed difficult month evidence;
- genuine side changes;
- ambiguous/unresolved segments.

A valid Grammar should explain difficult periods as different route/resolution behavior, not by month-specific exceptions.

## 6. Workstream E — Separate observations from route semantics

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

## 7. Workstream F — Causal FLOW_ROUTE contract

After answer-sheet semantics stabilize, build a prefix-only version.

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

## 8. Workstream G — AI semantic packet

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

## 9. Workstream H — Trading extraction after Grammar gate

Only after route reconstruction passes should the project extract trading actions.

Then compare, on the same causal route representation:

```text
MECHANICAL policy
AI discretionary policy
HUMAN + Grammar visualization research
```

This comparison is explicitly deferred. Do not conclude now that AI, mechanical trading, or human discretion is superior.

Old COUNTER/WITH_PARENT, H1-native, and state-action variants may be used as historical baselines only.

## 10. Output gate before trading research resumes

Required outputs:

1. `FLOW_ROUTE_LEDGER` for consumed answer-sheet periods;
2. compact origin/destination/arrival/response/resolution vocabulary;
3. difficult-period counterexample report;
4. observation-flip vs route-change audit;
5. explicit unresolved-route inventory;
6. causal FLOW_ROUTE reconstruction protocol;
7. prefix-only causal replay parity;
8. versioned route packet/render identity if AI is used.

Only after these are accepted may strategy extraction restart.

## 11. What is explicitly banned in the current phase

Do not:

- run another `H1_REALIGN -> trade` optimization;
- infer route continuation from H1 realignment alone;
- use the old nine-state table as the core Grammar;
- optimize state-action P/L;
- remove M15/M5 or declare H1-native superior without a later controlled comparison;
- optimize entry/SL/TP from the old candidate universe;
- restart ML direction/scheduler work;
- turn an arrival into automatic entry/exit;
- define a route by a fixed duration, fixed R, fixed retracement, or fixed event count;
- open `2025-07` or `2021`.

## 12. Data order

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
