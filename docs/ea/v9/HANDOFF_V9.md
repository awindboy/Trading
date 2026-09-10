# V9 Development Handoff

Last updated: `2026-09-10`
Status: `ACTIVE / SEQUENTIAL MAP-TRIGGER-POSITION RESEARCH`
Current phase: `ICT OBJECT ENGINE -> AI HTF MAP -> EVENT-DRIVEN TRIGGER -> LIVE-LIKE CONSUMED REPLAY`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed: `2025-01 through 2025-06`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Current direction

V3 showed that mechanically detected ICT objects are not automatically meaningful market structure.
Earlier V9 showed that free-form AI analysis can drift to structures that are too local or geometrically inconsistent.

Current solution:

```text
code = exact candidate geometry / lifecycle
AI = strategic selection / MTF interpretation
runtime = causal event monitoring
```

Use:

```text
multi-day H1/H4 map
-> mechanical FVG / OB / liquidity candidates
-> AI-selected major POI / route
-> wait
-> selected HTF event
-> M5/M15 trigger chart
-> Child
-> HTF journey
-> review / remap
```

## Current tooling

Active V9 research tools:

- `scripts/v9_causal_m1.py`
  - verified fail-closed M1 reveal and H4/H1/M15/M5 snapshots;
- `scripts/v9_ict_object_engine.py`
  - exact H4/H1 ICT candidate object geometry and lifecycle;
- `scripts/v9_chart_native_packet.py`
  - standardized two-chart `MAP + TRIGGER` renderer from selected object IDs;
- `scripts/v9_replay_event_runner.py`
  - advance to first frozen price/bar-confirmation event without showing intermediate market action to AI;
- `scripts/v9_hard_stop_guard.py`
  - independent Hard SL touch guard on already-revealed M1.

Current object engine is a research candidate engine, not a proven ICT classifier.

## Current evidence

Read:

`results/V9_ICT_OBJECT_ENGINE_AND_MTF_TRIGGER_CALIBRATION_20260910.md`

Key evidence:

- freehand POI boxes were replaced by exact mechanical candidate objects;
- FVG and liquidity lifecycle can be terminated at exact M1 fill/raid times;
- multiple POI touches correctly produced `NO TRADE` when the frozen trigger did not occur;
- a later H4 OB + M5 sweep/MSS Child lost `-1R`;
- Child failure did not automatically invalidate the larger HTF object;
- geometric presence and strategic freshness must remain separate.

These are consumed-data development findings, not validation.

## Immediate next research

Do not optimize another trigger pattern yet.

Run complete consumed-data episodes like live discretionary trading.

For each episode:

1. preselect starting cutoff without looking ahead;
2. start FLAT;
3. build exact object universe;
4. AI creates MAP and selects POI/liquidity/route;
5. persist map ledger;
6. runtime advances only to frozen event;
7. update geometric lifecycle;
8. open TRIGGER chart only when authorized;
9. freeze trigger before advancing;
10. if filled, freeze Child + Hard SL + HTF route;
11. runtime guards SL and review events;
12. at review decide `HOLD / EXIT / REMAP`;
13. continue until the episode is naturally resolved/remapped.

Evaluate whether AI can keep one coherent market map through time rather than winning one trade.

## What to score

- selected-object consistency;
- correct object creation/end handling;
- map continuity;
- unexplained object disappearance or geometry drift;
- appropriate `WAIT / NO TRADE` behavior;
- trigger discipline;
- Child/Parent separation;
- Hard SL authority;
- HTF journey management;
- unnecessary AI-call frequency;
- process quality before outcome.

## Deferred

Defer:

- production API architecture;
- MT5 screenshot capture integration;
- final AI-call scheduler cadence;
- final order simulator / broker fill semantics;
- LTF trigger optimization;
- July future-hidden replay.

The sequential research should approximate the future live process so these can be formalized after the analysis method stabilizes.
