# V9 Next Research Contract — HTF Market Map

Date: `2026-09-10`
Status: `ACTIVE NEXT V9 CONTRACT / CONSUMED-DATA RESEARCH`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`
Consumed data: `2025-01 through 2025-06`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`

## Purpose

Answer:

> Can AI repeatedly build a useful multi-day H1/H4 market map, select meaningful POIs and routes, and produce HTF-scale trade ideas before LTF execution is optimized?

Do not optimize runtime first.
Do not optimize LTF entry first.

## Workstream A — chart packet

Build a standard chart input.

Include:

- H1 multi-day chart;
- H4 broader chart when needed;
- exact current price;
- S;
- time labels;
- no future candles beyond cutoff.

Use the same visual scale across repeated tests where practical.

## Workstream B — semantic market map

At each research cutoff require:

```text
MAJOR_LEGS
MAJOR_HIGHS_LOWS
MAJOR_POIS
EXTERNAL_LIQUIDITY_CANDIDATES
RANGE_OR_COMPRESSION
LONG_SCENARIO
SHORT_SCENARIO
PREFERRED_PITCH_OR_WAIT
```

Keep the explanation short.

## Workstream C — repeated-run stability

Run the same cutoff multiple times independently.

Compare:

- selected major legs;
- selected POIs;
- selected liquidity;
- scenario direction;
- Child invalidation scale;
- destination hierarchy.

Do not require pixel-identical annotations.
Require materially similar market meaning.

## Workstream D — consumed-data replay

Use January-June.

Repeat:

```text
map
-> plan
-> reveal
-> review
-> revise method
-> test another consumed episode
```

Include winners, losses, ranges, false breakouts, and failed trends.

Do not select only clean examples.

## Workstream E — scale

Measure:

- intended route points;
- intended route S;
- Hard SL points;
- SL/S;
- MFE S;
- realized S;
- R;
- holding time.

Do not fit fixed S or R thresholds.

## Workstream F — SL and exit

Study:

- which HTF structure invalidates the Child;
- when LTF structure has enough authority to be Hard SL;
- when a major POI is consumed;
- when destination is exit versus review;
- when progression failure justifies exit.

Do not add fixed BE, partial, trail, or MFE-giveback rules.

## Workstream G — LTF execution later

Do not optimize M15/M5 trigger families until A-F are stable.

Then test whether LTF improves entry without changing the HTF thesis.

## Pass criteria

Pass this phase when:

1. the chart packet is reproducible;
2. AI repeatedly identifies materially similar large structure;
3. selected POIs and routes are explainable before outcomes;
4. bad examples expose clear reasoning failures;
5. Child SL scale is coherent with the trade thesis;
6. winner management operates at HTF scale;
7. the method produces a recognizable strategy identity across periods;
8. no hidden numeric threshold is fitted to January-June;
9. July remains unopened;
10. 2021 remains untouched.

## After pass

Then:

1. freeze the market-map protocol;
2. define the minimal AI schema;
3. research LTF execution;
4. build deterministic execution runtime;
5. freeze order and scheduler semantics;
6. run consumed-data parity;
7. perform July contamination preflight;
8. start fresh July replay from FLAT.

Do not call this production validation.
