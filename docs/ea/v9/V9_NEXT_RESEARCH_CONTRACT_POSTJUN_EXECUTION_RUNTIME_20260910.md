# V9 Next Research Contract — Sequential Live-Like Map / Trigger / Position Replay

Date: `2026-09-10`
Status: `ACTIVE NEXT V9 CONTRACT / CONSUMED-DATA SEQUENTIAL RESEARCH`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`
Consumed data: `2025-01 through 2025-06`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`

## Purpose

Answer:

> Can the V9 AI operate a coherent ICT-assisted H1/H4 market map through time, wait for selected POIs, manage LTF triggers, manage open positions, and remap only when new objective facts justify it — as if trading live?

This phase validates the research process, not profitability.

Do not optimize API cadence, broker integration, or LTF patterns first.

## Required architecture

Use:

```text
v9_causal_m1
-> v9_ict_object_engine
-> MAP
-> AI map ledger
-> frozen event
-> v9_replay_event_runner
-> updated objects
-> TRIGGER when authorized
-> frozen trigger
-> Child
-> Hard SL / HTF review event
-> HOLD / EXIT / REMAP
```

## Episode selection

Use consumed January-June only.

Choose starting cutoffs before inspecting their continuation for the active pass.
Include different market conditions rather than selecting only clean trend examples.

Start each new episode FLAT unless the episode was explicitly designed as a continuation test from a previously frozen state.

## Initial map call

At the initial cutoff:

1. build exact H4/H1 candidate objects;
2. render MAP;
3. select only strategically meaningful object IDs;
4. state LONG and SHORT scenarios;
5. state `WAIT` or a prepared pitch;
6. freeze the first event that can trigger another discretionary call.

Persist the map ledger.

## Object management test

Through the episode verify that:

- FVG rectangles end at exact full fill;
- liquidity rays end at exact raid;
- OB mitigation/invalidation is tracked exactly;
- strategic roles are updated separately;
- an object is not silently moved or deleted;
- newly important objects have exact provenance before receiving authority;
- old geometrically active objects may be marked strategically stale with an explicit reason.

## Waiting test

A selected POI is a place to observe, not automatic entry.

Advance to the first frozen event without exposing intermediate price to AI.

`NO TRADE` is correct when:

- the selected POI never arrives before the route resolves elsewhere;
- the POI is consumed before a frozen trigger;
- the expected LTF response never confirms;
- a better pitch does not form.

Do not chase or backfill.

## Trigger test

When HTF context authorizes LTF:

- render TRIGGER chart;
- select an objective LTF reference from already-revealed data;
- freeze the trigger before further reveal;
- runtime advances to trigger or cancellation event.

Do not optimize a universal trigger family in this phase.

Record why the trigger has authority inside the HTF thesis.

## Position-management test

At fill:

- freeze Entry;
- freeze Hard SL;
- record Child thesis;
- record Parent route;
- record major review/destination objects.

Runtime guards Hard SL and mapped events.

At each authorized review:

```text
HOLD
EXIT
REMAP
```

Do not exit from ordinary P/L changes or small LTF reactions.
Do not widen Hard SL.

## Map-continuity test

Every AI call receives the prior map ledger plus the new event.

Require explicit `MAP_CHANGES`.

Look for failures such as:

- blank-slate story rewrite;
- unexplained POI disappearance;
- object geometry drift;
- direction flip from small noise;
- repeated LTF hunting when no HTF pitch exists;
- keeping consumed liquidity as an active destination;
- treating Child stop as automatic Parent death;
- immediate same-side retry with no new objective fact.

## AI-call discipline

During this research, the runtime should approximate eventual live operation.

Call AI for:

- initial planning;
- selected POI/liquidity event requiring interpretation;
- frozen LTF confirmation event requiring discretionary decision;
- major HTF review/remap event;
- explicitly scheduled research audit when testing map persistence.

Do not call on every H1/M15/M5 close.

## Evidence to record

For each episode keep:

```text
starting cutoff
candidate engine version
MAP / TRIGGER images
map ledger versions
selected object IDs
geometric state changes
AI call reasons
frozen runtime events
trade/no-trade decisions
Entry / Hard SL
review / destination events
HOLD / EXIT / REMAP
R / S / MFE / MAE / hold time
process review
```

## Pass criteria

Pass this phase only when repeated consumed-data episodes show that:

1. the candidate engine reproduces exact object geometry/lifecycle;
2. AI can select a small, explainable subset from the candidate universe;
3. the market map remains materially coherent through sequential events;
4. object state changes are explicit and temporally correct;
5. AI waits rather than manufacturing trades;
6. LTF triggers are frozen before price resolves them;
7. Child entries and Hard SLs are causally reproducible;
8. open positions are managed from the mapped HTF route rather than every local fluctuation;
9. remaps follow objective new facts;
10. losses and no-trade episodes do not cause ad-hoc threshold/rule additions;
11. the same recognizable process works across different consumed market conditions;
12. July remains unopened and 2021 untouched.

Do not require a specific win rate from consumed development data to pass this process phase.

## After pass

Then:

1. freeze object-engine version and AI map schema;
2. freeze MAP/TRIGGER visual contract;
3. study LTF trigger families more systematically;
4. define live AI-call scheduling and maximum-staleness behavior;
5. integrate MT5 chart capture / API inputs;
6. build deterministic order/runtime parity;
7. run July contamination preflight;
8. begin fresh July replay from FLAT.
