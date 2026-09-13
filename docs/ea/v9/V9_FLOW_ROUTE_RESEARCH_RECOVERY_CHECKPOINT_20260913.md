# V9 Flow-Route Research Recovery Checkpoint

Date: `2026-09-13`
Status: `ACTIVE RESEARCH HANDOFF / HISTORICAL EVIDENCE RECOVERED / FIRST NEW FLOW_ROUTE LEDGER NOT YET BUILT`
GitHub HEAD reviewed: `3eca5a633b393269ecba2886055f663de1d22360`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Future-hidden: `2025-07 LOCKED`
Final reserve: `GOLD# 2021 UNTOUCHED`

## 1. Why this checkpoint exists

After the 2026-09-13 Grammar reset, the project asked a narrower question:

> Which parts of the older Market Flow Atlas were still studying the intended `movement -> arrival -> response -> next movement` process before H4/H1 alignment labels became the semantic center?

The answer is useful because the project does **not** need to restart from zero.

This checkpoint records what can be reused, what must remain discarded, and the exact next research step.

## 2. Earliest Atlas stages that were directionally correct

The research chronicle shows that the correct semantic scale was already present in the beginning of the Atlas.

### Stage 1 — continuous answer-sheet Atlas

Original form:

```text
reaction / arrival
-> price delivery
-> next reaction / arrival
-> price delivery
-> ...
```

Original research units:

```text
FLOW LEG
AUCTION CYCLE
BALANCE / RANGE STATE
DELIVERY PATH
NEXT STATE
```

This is directly compatible with the current Flow-Route authority.

### Stage 2 — exact object / arrival Atlas

The exact object engine preserved:

```text
FVG
OB candidate
H1/H4 swing-liquidity
object lifecycle
```

The enduring lesson was:

```text
object existence != object importance
```

This remains valid.

### Stage 3 — arrival / response research

The structural question was:

```text
arrival
-> response / acceptance / rejection
-> next delivery
```

That question remains useful.

What failed was not the question; some early quantitative labels reused part of the classification window inside the measured future outcome. Those percentages are not reusable as causal edge.

## 3. Later research pieces that remain useful only as context

The H4/H1 hierarchy did produce real descriptive information:

- nested timescales recur;
- H1 counterflow/balance often occurs inside slower directional authority;
- uncertainty/neutralization is real and should remain explicit;
- genuine H4 side changes commonly pass through interruption/weak/neutral buffers rather than clean instantaneous flips;
- difficult periods can contain more transition/neutralization without requiring a special month rule.

These facts can help interpret an active route.

They must **not** define route identity by themselves.

## 4. Historical evidence explicitly rejected from current route authority

Do not revive:

### A. Early 80-90% response/acceptance figures

Some reused classification-window movement in the later measured outcome window.
They may describe answer-sheet examples but are not clean forward edge.

### B. `last accepted probe before next state`

The event itself was chosen with knowledge of the next state. This is hindsight-selected and cannot be used causally.

### C. H1 realignment as movement continuation

`H1_REALIGN` is an observation generated after price has already moved enough to align the local H1 classification. It cannot be treated as proof that the next delivery continues.

### D. state-run boundaries as route boundaries

The current route model must be able to persist through local H1/H4 observation changes. A bar-state flip alone does not earn a new FLOW_ROUTE.

## 5. Existing assets approved for immediate reuse

Strict consumed event sources:

```text
docs/ea/v9/results/market_flow_atlas/MARKET_FLOW_EVENT_LEDGER.csv
docs/ea/v9/results/market_flow_atlas/POI_INTERACTION_CLUSTER_STUDY_STRICT.csv
docs/ea/v9/results/market_flow_atlas/LIQUIDITY_DELIVERY_CLUSTER_STUDY_STRICT.csv
```

Relevant scripts/code:

```text
scripts/v9_ict_object_engine.py
scripts/v9_market_flow_build_event_ledger.py
scripts/v9_market_flow_build_core.py        # context observations only
scripts/v9_market_flow_analyze_hierarchy.py # historical/context diagnostics only
```

Authoritative price source remains raw M1 with SHA256:

`626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

The old strict event ledger currently combines:

```text
POI_CLUSTER_TOUCH
LIQUIDITY_DELIVERY
H4_STATE_START
H1_INTERRUPT_START
H1_INTERRUPT_RESOLUTION
```

For new route reconstruction, POI/liquidity facts should be treated as primary arrival evidence. H4/H1 events are context observations only.

## 6. Important caveat on old strict CSV columns

The old strict POI/liquidity files contain future-window research columns such as variants of:

```text
accepted_through_4h_2close
reversal_dominant_24h
favorable_points
adverse_points
continuation_points
```

These may be inspected only as historical answer-sheet diagnostics **after** route semantics are defined.

They must not be used to choose an origin, destination, arrival role, response label, route boundary, or causal action.

## 7. What was actually completed in the latest recovery session

Completed:

1. latest `main` and new Flow-Route authority re-read;
2. old Atlas pivot, master ledger, research chronicle and reproduction spec reviewed;
3. early Stage 1-3 research identified as the last clearly correct semantic direction;
4. exact strict POI/liquidity/event assets identified for reuse;
5. exact object engine and historical event-builder inspected;
6. the new research start point was fixed at the chronological liquidity/POI arrival sequence.

Not completed:

```text
no new FLOW_ID ledger
no new route count
no frozen route-duration statistic
no new response-vocabulary count
no new trading result
no new causal route detector
```

Do not invent these numbers in the next session.

## 8. Exact next task

The next session should begin by constructing:

```text
FLOW_ROUTE_EVENT_STREAM.csv
```

from the strict POI/liquidity sources plus authoritative price/context.

Then construct:

```text
ANSWER_SHEET_FLOW_ROUTE_LEDGER.csv
```

over `2025H1 + 2026JF`.

The first reconstruction should inspect the event chronology with this conceptual lens:

```text
ORIGIN
-> ACTIVE DELIVERY / same-side progress
-> LANDMARK ARRIVAL
-> RESPONSE, which may include opposite-side liquidity work
-> RESOLUTION
-> same route continues OR old route completes/remaps
```

This is a lens, not a deterministic rule.

## 9. First research question to answer

The highest-value immediate question is:

> During an apparent active delivery path, when price performs an opposite-side liquidity raid or arrives at an opposing POI, what distinguishes an ordinary local response/repair that remains inside the same FLOW_ROUTE from a genuine terminal/campaign-changing response that completes the old route and earns a new one?

This question is closer to the original Grammar than asking whether the next H1 candle realigns.

Study many contiguous cases before proposing a distinction.

## 10. Starting route-segmentation discipline

Allowed as evidence:

- same-side liquidity deliveries and meaningful POI progress;
- exact landmark arrival/consumption;
- opposing-side raids/responses;
- repeated progress toward or away from active destination hypotheses;
- uncertainty/neutralization as contextual evidence;
- later answer-sheet route completion when labeling the retrospective ledger.

Not allowed as a route rule:

```text
fixed number of deliveries
fixed number of opposite raids
fixed time duration
fixed R or ATR distance
H1 realign
one H4/H1 state flip
one POI touch
```

## 11. Required route-compression audit

Once the first route ledger exists, build:

```text
OBSERVATION_FLIP_VS_ROUTE_CHANGE_AUDIT.csv
```

At minimum report per route:

```text
route duration
number of landmark events
number of H1 relation changes
number of H4 local-state changes
number of same-side liquidity deliveries
number of opposite-side/local response events
resolution type
```

Success requires examples where one FLOW_ROUTE survives several local H1/H4 observation changes. Otherwise the model has merely renamed the old state machine.

## 12. Difficult-period test

Do not optimize only on clean trends.

After a provisional vocabulary is usable, deliberately inspect:

```text
2025-05
2026 Jan-Feb
```

The same terms must explain strong delivery, repair, balance, ambiguity, neutralization and genuine route reversal without month-specific labels.

## 13. Causalization comes after semantic recovery

Only when answer-sheet route roles are compact enough should the project define causal state:

```text
CAUSAL_FLOW_ID / hypothesis
KNOWN_ORIGIN
ACTIVE_DESTINATION_CANDIDATES
KNOWN_ARRIVALS
KNOWN_RESPONSES
ROUTE_STATUS
UNRESOLVED_QUESTIONS
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
OBJECT_LEDGER_HASH
PREFIX_HASH
```

A retrospective answer-sheet endpoint may never appear in the causal packet before it becomes knowable.

## 14. Trading and AI status

Do not resume policy optimization yet.

The open question `mechanical vs AI vs human+Grammar` remains deferred until all three can receive the same frozen causal FLOW_ROUTE representation.

AI's eventual useful role, if any, is semantic:

```text
transit vs terminal arrival
response meaning
route continuation/completion
new destination/route earned
```

not H1/H4 alignment detection.

## 15. Data lock

No change:

```text
2025-07 = LOCKED
2021    = UNTOUCHED
```

Future-hidden gate remains `NOT SATISFIED`.
