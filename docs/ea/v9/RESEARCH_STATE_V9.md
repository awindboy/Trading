# V9 Research State

Date: `2026-09-12`
Status: `ACTIVE / CONTINUOUS HIERARCHICAL MARKET-FLOW GRAMMAR`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed answer-sheet data: `2025-01 through 2025-06`, `2026-01 through 2026-02`
Future-hidden candidate: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Current problem

The research no longer asks:

```text
Which setup has the highest historical win rate?
```

It asks:

```text
Which compact hierarchy explains the continuous market flow,
and which later parts of that hierarchy can eventually be converted into causal trading decisions?
```

## Current market-flow grammar

```text
H4 AUTHORITY
  strong directional
  weak directional
  neutral / ambiguous

-> H4 PHASE
  migration
  local interrupt
  neutral

-> H1 AUCTION
  aligned
  interrupt

-> EXACT LANDMARKS
  POI / FVG / OB / liquidity

-> RESOLUTION
  realign
  neutralize
  side change

-> NEXT STATE
```

## Current strict ledger headline

After in-period warmup and information-known boundary enforcement:

```text
H4 completed research bars after warmup
2025: 703
2026 Jan-Feb: 188

H1 interruption cycles
2025: 145
2026: 41

H4 migration interruption episodes
2025: 66
2026: 17

actual directional side changes
2025: 33
2026: 8
```

H1 interruption realignment before H4 side change:

```text
2025: 76.6%
2026: 78.0%
```

This is descriptive topology, not realized trade performance.

## Robustness

The nested H1 auction was recomputed across:

```text
3 H4 state views x 3 H1 state views
```

Realignment range:

```text
2025: 71.5% to 91.2%
2026: 76.9% to 89.6%
```

The exact number changes; the topology remains.

## Difficult-month result

2025-05 had:

- lower strong H4 authority;
- more weak directional authority;
- more H4 local-interrupt time;
- more H4 neutral time;
- more side changes;
- slower H1-cycle resolution.

Therefore the difficult month is already represented by the grammar as **authority stress / transition density**.
No special month filter is authorized.

## Ambiguity result

Keep:

```text
UNRESOLVED_UP / DOWN
AMBIGUOUS
```

Do not force them away.

In 2025, AMBIGUOUS episodes with a prior side split exactly 11 same / 11 opposite next migrations.
This is evidence that an explicit unknown state is necessary.

## Current data-boundary rule

```text
2025 known_at < 2025-07-01 00:00
2026 Jan-Feb known_at < 2026-03-01 00:00
```

Do not use July as warmup.
Do not use Dec-2025 as warmup for Jan-2026.
Do not use 2021.

## Retired / de-prioritized active research directions

Do not spend more current Atlas effort on:

- session labels alone;
- generic London/NY sweep-reclaim-body-break;
- generic MSS;
- fresh FVG confirmation;
- breaker / inversion auto-flip;
- premium/discount alone;
- MACD / Bollinger confirmation;
- fixed double-sweep count;
- rare 80-90% repair-resumption subsets;
- event-count or duration thresholds.

These may remain descriptive vocabulary but are not current discriminators.

## Critical corrections in the record

- Early acceptance/rejection figures partly overlapped classification and outcome windows; do not cite them as forward edge.
- The ~94% last-accepted-balance-probe result was hindsight-selected; do not use it.
- Final strict ledgers remove the June-source / July-known boundary row.

## Current research task

Next:

1. map route/destination after `H1_INTERRUPT -> REALIGN`;
2. distinguish transit landmark from campaign-changing landmark;
3. build explicit `SAME PARENT / NEXT AUCTION` versus `PARENT AUTHORITY LOST / RESET` ledger;
4. attach exact object IDs to origin/transit/delivery/campaign-changing roles;
5. continue testing compactness and difficult-period coverage;
6. when stable, freeze a strategy-extraction draft.

Do not optimize Entry / SL / TP yet.

## Current gate to strategy extraction

Do not leave Atlas phase until:

- the hierarchy explains long contiguous periods without month-specific exceptions;
- explicit ambiguity is retained rather than hidden;
- route/destination semantics are compact;
- Parent continuity vs reset is defined without Child-outcome hindsight;
- exact landmarks map to object IDs / lifecycle;
- the same process can be restated using only information that will later be available causally.

Then:

```text
FLOW GRAMMAR
-> STRATEGY EXTRACTION DRAFT
-> CAUSAL SEQUENTIAL REPLAY
-> LIVE RUNTIME
-> FUTURE-HIDDEN REPLAY
```
