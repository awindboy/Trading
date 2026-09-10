# V9 Development Handoff

Last updated: `2026-09-10`
Status: `ACTIVE / CHART-NATIVE HTF MARKET-MAP RESEARCH`
Current phase: `HTF MAP DISCOVERY -> CONSUMED-DATA REPLAY -> LTF EXECUTION RESEARCH`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed: `2025-01 through 2025-06`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Why the phase changed

V3 failed to identify important market structure reliably with mechanical swing/liquidity/ICT rules.

V9 improved discretionary reasoning but often worked at too small a scale.

The repeated problem was:

```text
large Parent idea
-> local structure search
-> local stop
-> local target
-> repeated small decisions
```

Strategy changes had limited effect because the market map remained too local.

Use AI for the part that V3 could not encode well:

```text
which structure actually matters?
```

## Current strategy direction

Use:

```text
multi-day H1/H4 map
-> major POI
-> external liquidity / route
-> scenario
-> wait
-> LTF execution later
-> HTF-aligned Hard SL
-> multi-hour Parent-Journey
```

The intended winner is a meaningful market leg.
Do not design V9 as a small H1 bridge system.

## Current research priority

Study market mapping before entry optimization.

Test:

- major-leg recognition;
- major POI selection;
- external-liquidity selection;
- range/compression recognition;
- LONG/SHORT scenario construction;
- Child falsification scale;
- destination hierarchy;
- winner capture in S;
- repeated-run AI map stability.

Use 2025 January-June only.

## Immediate tasks

1. Build a standardized H1/H4 chart packet.
2. Replay consumed periods with large-map analysis.
3. Record the map before inspecting the continuation of each research episode.
4. Compare good and failed map decisions.
5. Repeat the same cutoffs and test AI selection stability.
6. Study SL authority at HTF Child scale.
7. Study destination and HOLD/EXIT/REMAP at major HTF structures.
8. Study LTF entry only after the HTF process becomes stable.
9. Formalize runtime only after the market-analysis method is mature.

Do not open July.

## Deferred work

Defer:

- universal deterministic structure registry;
- deterministic major/minor swing classification;
- detailed pending-order runtime;
- AI-call scheduler parity;
- LTF trigger optimization.

Retain useful execution principles from those documents for later implementation.

## Permanent rules

Set Hard SL before entry.
Never widen it.
Keep Parent and Child separate.
Do not rescue stopped trades.
Evaluate both directions.
Do not invent fixed R, ATR, cooldown, retry, or side-balance rules.
Let large winners travel.
