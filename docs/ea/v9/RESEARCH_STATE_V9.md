# V9 Research State

Date: `2026-09-10`
Status: `ACTIVE / SEQUENTIAL CHART-NATIVE MTF REPLAY`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed development data: `2025-01 through 2025-06`
Future-hidden candidate: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Problem now

The project has moved past the first proof that AI can draw a plausible large H1/H4 map.

The unresolved problem is continuity:

> Can AI maintain and trade one coherent market map as price evolves, while code maintains exact ICT object geometry and lifecycle?

Do not evaluate this only from isolated screenshots or one winning trade.

## Current architecture

Use:

```text
verified causal M1
-> deterministic H4/H1 ICT candidate universe
-> AI selects strategic objects
-> MAP ledger
-> frozen wait event
-> runtime advance
-> MAP update
-> TRIGGER chart when authorized
-> frozen LTF trigger
-> Child entry + Hard SL
-> event-driven position management
-> HOLD / EXIT / REMAP
```

## Candidate-object hypothesis

Mechanical ICT geometry is useful as a candidate universe.

Current candidates:

- FVG from exact three-candle gaps;
- swing/liquidity candidates from reproducible geometric pivots;
- OB candidates from a reproducible swing-break/source-candle rule.

These definitions provide reproducible coordinates.
They do not provide strategic importance.

AI must reject most candidates.

## Lifecycle hypothesis

Separate:

```text
GEOMETRIC LIFECYCLE
STRATEGIC / CAMPAIGN LIFECYCLE
```

Code handles fill/raid/mitigation/invalidation.
AI handles selected/secondary/transit/stale/retired/destination/review roles.

A geometrically active object can be strategically stale.
A Child failure does not automatically end the Parent or HTF object.

## Current chart contract

AI-facing packet has two chart roles:

```text
MAP
TRIGGER
```

MAP is the H1 multi-day market view with selected H4/H1 objects overlaid.
TRIGGER is M5 by default and appears only when LTF inspection is authorized by the HTF map.

Do not add a third chart to compensate for weak interpretation.
Code may retain debug/parity charts separately.

## Current research task

Run multiple complete sequential episodes across consumed January-June.

Each episode must preserve prior state.
Do not restart interpretation at every event.

Test:

- map creation;
- POI/liquidity selection;
- waiting;
- object creation and consumption through time;
- trigger activation/cancellation;
- position creation;
- HTF review management;
- Parent/Child continuity;
- remapping after objective change;
- no-trade and missed-move behavior.

Include losses, failed triggers, ranges, trends, false breaks, and no-fill cases.

## Measurement

Record:

- object IDs and roles;
- object born/end timestamps;
- map changes;
- AI-call reason;
- trigger state;
- Entry / Hard SL;
- route/review object IDs;
- points, R, S;
- MFE/MAE;
- holding time;
- process-quality review.

Do not fit fixed thresholds to these measurements.

## Current gate

Do not open July until the sequential process shows all of the following:

- exact object geometry is reproducible;
- object lifecycle updates do not silently rewrite history;
- AI retains materially coherent maps between events;
- selected POIs and liquidity remain explainable before outcomes;
- AI can wait without manufacturing LTF trades;
- trigger plans are frozen before subsequent price;
- Child stops are handled without rescue;
- position reviews operate at HTF scale;
- remaps are tied to objective new facts;
- strategy identity remains recognizable across different consumed episodes;
- no hidden numeric threshold was mined from January-June.

After that, freeze the analysis protocol, then design live API/MT5 calling semantics and runtime parity before July.
