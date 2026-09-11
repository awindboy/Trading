# V9 Development Handoff

Last updated: `2026-09-11`
Status: `ACTIVE / MARKET-FLOW ATLAS + REVERSE ENGINEERING`
Current phase: `ANSWER-SHEET FLOW STUDY -> MINIMAL GRAMMAR -> STRATEGY EXTRACTION`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed: `2025-01 through 2025-06`, `2026-01 through 2026-02`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Why the phase changed

The project repeatedly fell into:

```text
trade fails
-> diagnose one issue
-> add/refine one rule
-> new failure
-> refine again
```

That loop risks reproducing the V3-to-V9 overfit pattern before the underlying market grammar is understood.

Jan-Feb research also showed:

- H1 opportunity objects are frequent;
- higher frequency alone did not improve results;
- better LTF execution geometry alone did not solve pitch quality;
- one-object-at-a-time tuning moved the bottleneck without solving strategy identity.

Therefore pause trade-by-trade optimization.

## Current direction

Use consumed data as an answer sheet.

Study:

```text
arrival / reaction
-> delivery
-> next arrival / reaction
-> delivery
-> ...
```

Include trends, ranges, compression, repair, false breaks, liquidity sweeps, shakeout-like moves, POI failures, acceptance through old structure, and ambiguous transitions.

## Current analytical architecture

```text
RAW / H4 / H1 CHART
+ EXACT ICT OBJECT LEDGER
+ OPTIONAL INDICATOR / VOLATILITY LENSES
-> CONTINUOUS FLOW ATLAS
-> REPEATED RELATIONSHIPS
-> MINIMAL MARKET-FLOW GRAMMAR
```

Existing object tools remain useful for exact provenance.
AI decides semantic relationships and whether a lens is actually useful.

MACD, Bollinger Bands, MA, ATR/volatility, momentum, and session context are permitted as research lenses.
They are not automatic signals.

## Current tooling retained

- `scripts/v9_causal_m1.py`
- `scripts/v9_ict_object_engine.py`
- `scripts/v9_chart_native_packet.py`
- `scripts/v9_replay_event_runner.py`
- `scripts/v9_hard_stop_guard.py`

Causal/event tools are retained for downstream testing.
Current atlas research may inspect full future on consumed data only.

## Immediate next research

Build the Market Flow Atlas across:

- `2025-01 through 2025-06`;
- `2026-01 through 2026-02`.

For each contiguous period:

1. map H4/H1 flow;
2. identify reaction/arrival events;
3. identify directional legs and range states;
4. attach exact FVG/OB/liquidity objects;
5. measure distance, duration, S, volatility;
6. test useful analytical lenses;
7. record destination and state transition;
8. cluster repeated relationships;
9. retain counterexamples;
10. simplify rather than add exceptions.

## Outputs

```text
FLOW_LEG_LEDGER.csv
FLOW_STATE_LEDGER.csv
FLOW_ARCHETYPE_CATALOG.md
LENS_EVIDENCE_LEDGER.csv
ATLAS_CHARTS/
```

Do not optimize P/L in this phase.

## Downstream

After a compact grammar is stable:

1. extract what is knowable in real time;
2. define the tradable subset;
3. map H4 Parent / H1 auction roles;
4. define LTF execution and Hard SL;
5. resume causal sequential replay;
6. design live AI-call / MT5 runtime;
7. only then consider future-hidden replay.

Do not open July.
