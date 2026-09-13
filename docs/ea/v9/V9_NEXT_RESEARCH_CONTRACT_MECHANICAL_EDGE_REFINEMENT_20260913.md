# V9 Next Research Contract — Mechanical Edge Refinement

Date: `2026-09-13`
Status: `ACTIVE NEXT CONTRACT`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `2021`
Base GitHub HEAD: `4707ac6993a9288afdbff6ae127074bbcd11d3a7`

## 1. Objective

Build the strongest **simple mechanical V9** that can be justified on consumed data while preserving the simplified Arrival/Delivery Grammar.

The project must not obtain a pretty result by:

- adding many entry filters;
- optimizing an LTF trigger;
- shrinking the opportunity set to a tiny subset;
- using AI to select visually attractive trades;
- repairing failed Children with hindsight.

## 2. Frozen research convention

For this contract:

```text
ENTRY TIMING
= immediate at the causal meaningful Arrival / Delivery event
  after the factual Grammar update authorizes the Child

LTF
= chronology / execution data only
!= required trigger source

AI
= deferred
```

Exact tick/M1 executable-price convention still requires versioned implementation freeze, but no additional M1/M5/M15 pattern may be required for entry.

## 3. A0 — exact-arrival baseline

Build a versioned mechanical ledger with, at minimum:

```text
EVENT_ID
BLOCK
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
ARRIVAL_FIRST_TOUCH_AT
ARRIVAL_SIDE
ARRIVAL_ROLE
OBJECT_IDS

PRIMARY_STATUS_BEFORE
PRIMARY_SIDE_BEFORE
PRIMARY_STATUS_AFTER
PRIMARY_SIDE_AFTER

ENTRY_AUTHORIZED
ENTRY_AT
ENTRY_PRICE_REFERENCE
```

Requirements:

- H4 liquidity exact first touch must come from revealed M1/tick chronology;
- no H1-close convenience delay in the primary baseline;
- same-time semantic and price-event priority must be deterministic;
- ambiguous intraminute fill ordering must be labeled, not invented.

Deliverable:

`MECHANICAL_IMMEDIATE_ENTRY_BASELINE_LEDGER.csv`

## 4. A1 — opportunity-universe preservation

At every refinement stage report:

```text
raw opportunity count
participated count
participation rate
resolved / censored count
LONG / SHORT count
```

A result that improves only because opportunity count collapses must be flagged.

Do not introduce:

- minimum R;
- minimum distance;
- cooldown;
- retry cap;
- max entries per route;
- duration threshold;
- fixed no-chase;
- forced direction balance;
- trade/day quota.

## 5. A2 — Hard-SL study

Keep the immediate entry fixed.

Compare only structurally causal invalidation references that exist at entry, such as:

```text
H1 structural swing
response origin
relevant OB distal
delivery-leg structural invalidation
other versioned objective structural reference
```

For each candidate report:

```text
eligibility / coverage
win rate
total R
mean R
profit factor
max drawdown
SL price-distance distribution
SL percentage-distance distribution
TP/journey distance distribution
MAE / MFE where causally computable
period stability
direction stability
```

Hard SL rules:

- fixed before entry;
- never widened;
- stopped Child is dead;
- no future structure may become the original SL retroactively.

Do not select a winner from one period only.

## 6. A3 — destination / TP / journey study

Entry remains fixed.

Study, without requiring a currently visible fixed TP:

```text
nearest-known same-side H4 liquidity
dynamic destination rollover
arrival-to-arrival harvesting
meaningful-arrival review
new destination birth after entry
journey continuation after destination consumption
```

Separate:

```text
DESTINATION EXISTENCE
from
ROUTE / JOURNEY SURVIVAL
```

Required report:

```text
resolved win rate
total R
PF
DD
winner distribution
loss distribution
time-in-trade
TP / realized-journey distance distribution
cases entered with no current forward destination
```

Do not create a fixed numeric TP merely for convenience.

## 7. A4 — repeated Child / exposure mechanics

Do not assume either:

```text
OPEN EVERY DELIVERY
```

or:

```text
ONE POSITION ONLY
```

as authority.

Research mechanically defensible repeated opportunities.

For every additional Child candidate record:

```text
existing Child state
same/opposite side
new Arrival / Delivery facts
whether a distinct structural invalidation exists
combined route-level risk
individual Child Hard SL
result
```

The study may test exposure accounting and distinct-thesis mechanics but may not invent a retry cap.

## 8. A5 — continuation / challenge factual study

Factual variables may be tested for descriptive separation of:

```text
PRIMARY CONTINUATION
vs
CHALLENGE / FLIP
```

Possible factual inputs include:

- active same-side/opposite liquidity geometry;
- distance to known liquidity;
- object age;
- newly born liquidity;
- recent delivery sequence;
- cluster composition;
- POI interaction history;
- destination rollover facts.

Rules:

- test single-variable / simple effects before multivariate rules;
- check 2024, 2025H1 and 2026JF separately;
- check UP/DOWN separately;
- check month stability;
- preserve counterexamples;
- do not create a high-complexity direction classifier merely to improve accuracy a few percentage points.

This work is subordinate to total trading expectancy.

## 9. A6 — cross-period mechanical comparison

The candidate mechanical policy must be compared across:

```text
2024 consumed postmortem
2025 Jan-Jun consumed answer-sheet
2026 Jan-Feb consumed answer-sheet
```

Report both pooled and separate results.

A policy is not robust merely because pooled R is positive.

Identify whether improvement comes from:

```text
direction edge
SL efficiency
winner harvesting
exposure mechanics
or opportunity deletion
```

## 10. A7 — freeze the simplest policy

Prefer the least complex policy that retains broad evidence.

The freeze packet must contain:

```text
exact event clock
entry convention
Hard-SL convention
journey / TP convention
Child / exposure convention
all object known-at rules
all execution assumptions
source hashes
reproduction command
ledger hash
summary hash
```

No AI and no LTF trigger dependency in this freeze.

## 11. A8 — deterministic runtime parity

Only after the mechanical policy is frozen:

- implement through dual-clock runtime;
- verify exact consumed replay;
- verify restart parity;
- verify object/known-at parity;
- verify Hard-SL chronology;
- verify destination chronology;
- verify intraminute ambiguity handling.

Do not unlock future-hidden data from an analysis notebook alone.

## 12. A9 — hidden gate

`2025-07` remains locked until every mechanical and runtime gate is explicitly satisfied.

`2021` remains untouched final reserve.

## 13. A10 — AI study, deferred

AI may be reconsidered only after the mechanical policy is strong and frozen.

The test must be:

```text
FROZEN MECHANICAL BASELINE
vs
SAME BASELINE + AI
```

not:

```text
weak mechanical process
vs
AI-created strategy
```

AI must add stable incremental value across held-out comparisons and must not improve metrics merely by rejecting most trades.

Failure to add value means AI is omitted.

## 14. A11 — optional LTF entry study, deferred further

Only if a mature mechanical strategy already exists may a later project ask whether an LTF execution refinement adds value.

The comparator must remain the exact-arrival immediate-entry policy.

Any proposed LTF trigger must:

- be preregistered;
- preserve causal chronology;
- be tested on held-out data;
- improve net expectancy / execution quality after participation loss;
- survive period and direction splits.

Otherwise immediate entry remains authoritative.

## 15. Completion criterion

This contract is complete when the project can state, with reproducible consumed evidence:

> V9's mechanical edge is carried by the Arrival/Delivery Grammar, bounded-risk structural invalidation, and journey harvesting rather than by LTF trigger optimization or AI selection.
