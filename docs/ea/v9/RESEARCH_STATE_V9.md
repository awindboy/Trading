# V9 Research State

Date: `2026-09-10`
Status: `ACTIVE / HTF MARKET-MAP RESEARCH`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed development data: `2025-01 through 2025-06`
Future-hidden candidate: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Current problem

V9 often understood local price action but mapped the market at too small a scale.

This produced:

- local stop authority inside large Parent ideas;
- local targets inside large directional legs;
- same-auction churn;
- repeated AI attention to small structures;
- weak strategy identity across sessions.

The current problem is market representation and scale.

## Current hypothesis

AI can read chart-native H1/H4 structure better than a deterministic swing/liquidity engine.

Use AI to select the meaningful structure.
Use code to execute the selected structure exactly.

Research this sequence:

```text
large H1/H4 structure
-> major POI / external liquidity
-> scenario
-> wait
-> Child entry
-> HTF-aligned Hard SL
-> large route
```

## Evidence status

2025 January-June is consumed development evidence.

Use it for:

- retrospective structure study;
- causal sub-replay from chosen cutoffs;
- matched-pair research;
- AI stability tests;
- failure taxonomy.

Do not call these results validation.

Do not use July.
Do not use 2021.

## What AI should learn to do

AI should identify:

- major legs;
- meaningful swing highs/lows;
- major POIs;
- external liquidity candidates;
- range and compression;
- displacement and failed displacement;
- consumed structure;
- open route;
- opposite scenario;
- Child invalidation structure;
- major destination/review structure.

AI should ignore most local structures until the large map makes them relevant.

## What code should do

Code should:

- render causal multi-timeframe charts;
- store selected coordinates;
- calculate exact geometry;
- monitor entry/SL/review events;
- measure R, S, MFE, MAE, hold time.

Do not ask code to decide which mechanical swing is strategically important.

## SL research

Keep Hard SL.

Study which structure actually kills the current Child.

Compare:

- LTF execution anchor;
- H1 pullback structure;
- broader H1 Child structure;
- Parent failure structure.

Do not select the winner after seeing the outcome.
Do not widen after entry.

## Journey research

Measure:

- captured points;
- captured S;
- MFE in S;
- MFE in R;
- holding time;
- distance to major destination;
- giveback before exit.

Do not turn `1S`, `2S`, or `3S` into fixed targets.

A strategy claiming HTF trend capture should produce meaningful S-scale winners.

## Current gate

Do not freeze a production strategy yet.

Pass the next phase when:

1. the chart packet is stable;
2. repeated AI runs produce materially similar large maps;
3. major POIs and routes are explainable before outcomes;
4. failure examples are understood without threshold mining;
5. SL scale matches the Child thesis;
6. large-winner management is defined at HTF scale;
7. LTF entry can be added without changing the market thesis.

Only then design the final deterministic runtime and open a new future-hidden period.
