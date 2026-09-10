# V9 Chart-Native ICT Object + MTF Pipeline

Date: `2026-09-10`
Status: `ACTIVE V9 RESEARCH METHODOLOGY AUTHORITY`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`
Consumed development data: `2025-01 through 2025-06`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`

## Purpose

Use deterministic code for exact ICT candidate geometry and lifecycle.
Use AI for strategic selection and multi-timeframe interpretation.

Do not make code decide which detected object matters.
Do not let AI invent executable coordinates from visual impression.

Use:

```text
CAUSAL M1
-> H4/H1 OBJECT CANDIDATE UNIVERSE
-> MAP CHART
-> AI SELECTS IMPORTANT POI / LIQUIDITY / ROUTE
-> WAIT
-> SELECTED POI EVENT
-> TRIGGER CHART
-> AI SELECTS / FREEZES LTF TRIGGER
-> CHILD ENTRY + HARD SL
-> HTF JOURNEY
-> REVIEW / SL / DESTINATION EVENT
-> MAP + POSITION UPDATE
```

## Deterministic candidate objects

### FVG candidate

Use completed three-candle geometry.

Bullish:

```text
C1.high < C3.low
FVG = [C1.high, C3.low]
```

Bearish:

```text
C1.low > C3.high
FVG = [C3.high, C1.low]
```

Record:

```text
OBJECT_ID
TIMEFRAME
SOURCE C1 / C2 / C3
BORN_AT = C3 completion
PRICE_LOW / PRICE_HIGH
FIRST_TOUCH_AT
FULL_FILL_AT
GEOMETRIC_STATE
GEOMETRIC_END_AT
```

Use exact M1 chronology for touch/full-fill timestamps after the HTF object is born.

FVG rectangle starts at `BORN_AT`.
Stop the rectangle at `FULL_FILL_AT`.

### Swing / liquidity candidate

Mechanical swing detection creates a candidate reference only.

Current research engine uses a `2-left / 2-right` geometric pivot.
This is not strategic major/minor authority.

A swing is known only after the second right bar completes.

Create:

```text
BSL candidate from confirmed swing high
SSL candidate from confirmed swing low
```

Record exact source price, `BORN_AT`, and exact M1 `RAID_AT`.

Liquidity ray ends at `RAID_AT`.

### OB candidate

Current research candidate definition:

1. a completed bar closes through a previously confirmed swing candidate;
2. find the last opposite-color candle before that break;
3. store that candle as the candidate OB source.

Record:

```text
SOURCE CANDLE
FULL WICK RANGE
BODY RANGE
MEAN THRESHOLD
BREAK_REFERENCE_ID
BREAK_BAR
BORN_AT = break-bar completion
FIRST_MITIGATION_AT
DISTAL_INVALIDATION_AT
GEOMETRIC_STATE
GEOMETRIC_END_AT
```

This definition creates a reproducible OB candidate universe.
It does not claim that every candidate is a meaningful ICT order block.
AI selects strategic importance.

## Two independent lifecycle layers

Keep geometric lifecycle and strategic lifecycle separate.

Code owns geometric lifecycle.

Examples:

```text
FVG: ACTIVE -> TOUCHED -> FULLY_FILLED
LIQUIDITY: ACTIVE -> RAIDED
OB: ACTIVE -> MITIGATED -> INVALIDATED
```

AI owns strategic lifecycle.

Examples:

```text
SELECTED
SECONDARY
TRANSIT
STALE
RETIRED
DESTINATION
REVIEW
```

A geometrically active object can be strategically stale.
A Child stop does not automatically invalidate the HTF object.
A filled FVG or raided liquidity object must not continue as an active geometric object.

## AI object selection

AI reads the large chart first.

Select only a small subset of candidate objects that matter to the current map.

Judge:

- current major directional legs;
- dealing range / balance / compression;
- location inside the larger move;
- which candidate object launched or interrupted meaningful displacement;
- whether the object's original campaign already delivered its route;
- whether it has already produced meaningful mitigation/reaction;
- external liquidity and open route;
- strongest opposite scenario.

Do not select an object merely because it exists or remains partially unfilled.
Do not require a mandatory FVG + OB + sweep + BOS chain.

## Two-chart packet

The AI-facing research packet has exactly two chart roles.

### MAP chart

Default:

```text
H1 main chart
+ selected H4/H1 ICT objects
+ major liquidity
+ major route / entry / SL / review levels when relevant
```

Show enough history for the active multi-day structure.
Use roughly 7-15 trading days as a display default, not a trade filter.
H4 calculations and clean debug charts may exist behind the tooling, but do not add a third AI-facing chart by default.

Annotations must be short.
Do not cover the price structure with large explanation boxes.

### TRIGGER chart

Open only after a selected HTF POI or liquidity event makes LTF inspection relevant.

Default research timeframe: `M5`.
Use M15 instead when the active trigger structure is clearly M15-scale.

Show:

- active HTF POI boundary;
- local liquidity candidate(s);
- sweep/raid event when relevant;
- local structural reference selected before entry;
- trigger confirmation;
- Entry and Hard SL after frozen.

LTF does not create an unrelated Parent thesis.

If no HTF POI is actionable, mark trigger state `INACTIVE`; do not hunt for a setup.

## Map ledger

Do not rebuild the market story from scratch on every AI call.

Persist:

```text
MAP_VERSION
ASOF
MAJOR_LEGS
SELECTED_OBJECT_IDS
OBJECT_STRATEGIC_ROLES
LONG_SCENARIO
SHORT_SCENARIO
PREFERRED_PITCH / WAIT
ACTIVE_WAIT_EVENT
CHILD_STATE
POSITION_STATE
REVIEW_ROUTE
MAP_CHANGES_SINCE_PRIOR_CALL
```

Coordinates come from object IDs or frozen runtime levels.
AI may change role/state with new evidence but must not silently move the underlying object geometry.

## Sequential live-like research process

### 1. Initial planning

Start FLAT at a preselected consumed-data cutoff.
Build causal H1/H4 candidates.
Render MAP.
AI selects important objects, both scenarios, and `WAIT` or a prepared pitch.
Freeze the map ledger before revealing more price.

### 2. Waiting

Runtime advances M1 chronologically to the first frozen event.
Do not show every intermediate H1/M15 bar to the AI.

Typical events:

```text
SELECTED_POI_TOUCH
SELECTED_POI_FULL_FILL / INVALIDATION
SELECTED_LIQUIDITY_RAID
PRECOMMITTED_BAR_CONFIRMATION
REMAP_EVENT
```

### 3. Trigger management

At an authorized HTF event, render updated MAP + TRIGGER.

AI decides:

```text
NO ENTRY
WAIT FOR FROZEN LTF CONDITION
ENTER / ARM CHILD
REMAP
```

If waiting for a trigger, freeze the exact objective condition before advancing.

### 4. Position start

Before risk is paid record:

```text
SIDE
ATTEMPT_THESIS
ENTRY / ENTRY_TRIGGER
HARD_SL
WHY HARD_SL INVALIDATES THIS CHILD
PARENT_ROUTE
DESTINATION / REVIEW_STRUCTURE_IDS
```

Never widen Hard SL.

### 5. Open-position management

Runtime continuously guards Hard SL and selected mechanical review/destination events.

Do not call AI on every M5/M15/H1 candle.

At an authorized discretionary review, render MAP + TRIGGER/resolution chart and decide:

```text
HOLD
EXIT
REMAP
```

Treat small LTF reactions as transit unless they materially damage the mapped thesis.

### 6. Child resolution

Stop the Child at Hard SL or authorized exit/destination.

Do not use later movement to rescue a stopped Child.
Parent may survive.

Any new attempt requires:

```text
WHAT OBJECTIVE FACT CHANGED?
IS THIS A GOOD PITCH?
```

## Research goal now

The next research question is not whether one ICT setup wins.

Test whether the full process can be operated like live discretionary trading:

```text
map
-> object selection
-> wait
-> lifecycle update
-> trigger management
-> position management
-> remap
```

while preserving causal integrity and a coherent market story through time.

Do not optimize trigger thresholds yet.
Do not open July yet.
