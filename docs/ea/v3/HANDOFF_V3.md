# V3 Development Handoff

Last updated: `2026-08-24`
Repository base before V3 bootstrap: `0e7b1d5b39de1126394e88f85abf87cde167fc84`
Current phase: `V3-001 RAW DATA LAB BOOTSTRAP`
V1: `FROZEN`
V2: `PAUSED / PRESERVED CONTROL`
2021: `KEEP UNTOUCHED`

## Startup order

On every V3 session:

1. Check latest GitHub commit.
2. Read root `AGENTS.md`.
3. Read `docs/ea/v3/AGENTS_V3.md`.
4. Read root `docs/ea/HANDOFF.md`.
5. Read this file.
6. Read `RESEARCH_STATE_V3.md`.
7. Read `V3_RAW_DATA_LAB_PROTOCOL.md`.
8. Read `BACKLOG_V3.md`.
9. Inspect the latest V3 experiment/result documents and code.

If chat conflicts with GitHub, GitHub wins.

## Why V3 exists

V2 successfully separated execution, Entry survival, winner continuation and exit
architecture, but current deterministic Entry generation remains sparse and unstable.

Recent GOLD frequency:

```text
2024: 52 fills
2025: 55 fills
```

FULL_AUDIT showed the scarcity is not simply lack of market activity:

```text
2025 GOLD#
804 PLAN
466 Root contact
363 Sweep accepted
165 current CHOCH
68 distinct execution geometries
55 Fill
```

The current chain therefore compresses a much larger reaction population.

V3 does not assume this compression is correct.

## D155 lesson carried into V3

D155 found a semantic tension:

- mentor research describes small-timeframe `live structure` transition and allows
  a role for M5/M1;
- current deterministic V2 is M1-only and scenario CHOCH depends on the inherited
  global protected-structure detector;
- the three-opposite-colour-candle wave detector is an operational formalization,
  not something V3 must preserve.

This does not authorize a replacement trigger by itself.

It motivates rebuilding the opportunity universe from raw market data instead of
studying only V2 fills.

## Active data allocation

```text
GOLD# 2023-2025
    V3 discovery/development

2022
    validation vault

2021
    untouched
```

Initial discovery starts with M1 bars.

Tick data is requested only after candidate hypotheses survive fast replay.

## Immediate task

User provides:

```text
GOLD# M1 CSV
2023-01-01 through 2025-12-31
broker/server timestamps
OHLC + tick volume + real volume + spread
```

Preferred: one CSV per year or one continuous CSV, compressed in ZIP.

Do not upload internal HCC/TKC binaries as the primary exchange format unless
explicitly requested. Export broker data to CSV first.

After upload:

1. verify date coverage and row ordering;
2. identify broker-server timezone/session discontinuities;
3. verify spread field and symbol precision;
4. rebuild M5/M15/M30/H1/H4 from M1;
5. build candidate swing/liquidity/sweep/zone/trigger universe;
6. produce the first opportunity-density census;
7. only then begin strategy-family experiments.

## V2 disposition

Do not delete V2.

V2 remains the reference for:
- deterministic causal infrastructure;
- execution behavior;
- D151/D154 instrumentation;
- SP/V3E exit work;
- prior negative results;
- comparison against any eventual V3 candidate.

Do not continue D154P/D155 filter mining while V3-001 is active unless explicitly
reopened.

## Result-document rule

Every major V3 experiment gets its own immutable result document.

Phase changes update this HANDOFF.

Important V3 architectural decisions append to root `docs/ea/DECISIONS.md`.
