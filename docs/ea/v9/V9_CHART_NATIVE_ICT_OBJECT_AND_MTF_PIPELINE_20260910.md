# V9 Chart-Native ICT Object + MTF Pipeline

Date: `2026-09-12`
Status: `ACTIVE OBJECT-GEOMETRY METHODOLOGY / DOWNSTREAM CHART PIPELINE`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## Current phase note

The active research loop is **not** sequential chart-by-chart trade replay.

Current authority is:

`V9_MARKET_FLOW_GRAMMAR_CONTINUOUS_HIERARCHY_AUTHORITY_20260912.md`

This document remains authoritative for:

- exact candidate-object geometry;
- object provenance/lifecycle;
- later MAP/TRIGGER chart roles;
- separation of code geometry from AI semantic role.

Its old live-like trading sequence is downstream until strategy extraction.

## Deterministic object authority

Code creates exact candidates for:

```text
FVG
OB candidate
swing / liquidity candidate
```

Code owns:

```text
OBJECT_ID
source bars
born-at time
price coordinates
touch/fill/raid/mitigation/invalidation
geometric end
```

AI does not invent executable coordinates.

## FVG candidate

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

`BORN_AT` is C3 completion.
Use chronological M1 after birth for lifecycle timestamps.

## Swing/liquidity candidate

Current geometric candidate uses two left and two right bars.
It becomes known only after the second right bar completes.

Candidate geometry does not determine major/minor strategic importance.

## OB candidate

Current reproducible research candidate:

- completed bar closes through a confirmed swing candidate;
- last opposite-color candle before that break is source-candle candidate.

Store full wick/body/mean-threshold geometry and lifecycle.

This does not prove every candidate is strategically meaningful.

## Object lifecycle

Code owns geometric states.

Examples:

```text
FVG: ACTIVE / TOUCHED / FULLY_FILLED
LIQUIDITY: ACTIVE / RAIDED
OB: ACTIVE / MITIGATED / INVALIDATED
```

AI owns strategic role.

Current Atlas semantic roles to research later include:

```text
ORIGIN
TRANSIT
DELIVERY
CAMPAIGN-CHANGING
RETIRED
```

Keep:

```text
GEOMETRIC LIFECYCLE != STRATEGIC LIFECYCLE
```

## Current Atlas usage

During continuous-flow research, objects are landmarks inside:

```text
H4 AUTHORITY
-> H4 PHASE
-> H1 AUCTION
-> LANDMARK
-> RESOLUTION
```

Do not select an object merely because it exists or remains unfilled.
Do not require FVG + OB + sweep + BOS/MSS confluence.

## Later AI-facing charts

When strategy extraction and causal replay resume, retain exactly two default AI-facing roles:

### MAP

Default H1 chart with selected H4/H1 landmarks and active route.

### TRIGGER

M5 default, M15 if justified by execution scale.
Open only after the strategy-extraction policy authorizes LTF inspection.

Do not hunt unrelated LTF setups.

## Downstream live-like sequence

Deferred sequence:

```text
causal M1
-> exact object universe
-> MAP
-> AI semantic state / route
-> frozen wake event
-> TRIGGER if authorized
-> Child entry + Hard SL
-> runtime guard
-> review / exit / remap
```

Do not resume this loop until the Market Flow Atlas strategy-extraction gate passes.

## Permanent object rules

- exact geometry comes from code/runtime;
- AI may change semantic role but not stored geometry;
- consumed objects cannot remain geometrically active;
- object existence is not strategic importance;
- Child stop does not automatically invalidate Parent or HTF object;
- do not create a mandatory pattern chain.

## 2026-09-12 next chart-native gate after AI-envelope validation

<!-- V9_AI_EXTERNAL_DECISION_VALIDATED_20260912 -->

The causal gate envelope / scheduler mechanics are accepted. The remaining chart task is now concrete: freeze the review/remap `MAP` attachment so every AI semantic decision is bound to an exact causal prefix and render identity/hash.

Do not add extra discretionary charts or new indicator confirmations. The chart attachment must preserve the existing MAP/TRIGGER role separation and exact code-owned coordinates.
