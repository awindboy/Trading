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

## 2026-09-12 strategy-extraction freeze checkpoint

This checkpoint supersedes older "Current research task" / "gate to strategy extraction" text above where they conflict.

The first strategy-extraction draft is frozen in:

`V9_STRATEGY_EXTRACTION_DRAFT_PARENT_CHILD_FLOW_20260912.md`

The current implementation gate is:

`V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`

The market remains represented continuously rather than as a rare accepted-setup funnel.

```text
171 active-Parent H1 cycles
  120 same-Parent realign
   51 Parent-loss-first

120 same-Parent routes
   63 H1 launch-anchor no-touch
   26 touch without completed M15 close damage
   31 completed M15 close damage
```

Counter-Parent flow is retained as a first-class Child branch:

```text
141 strict fresh M15 counter transitions before H1 interrupt
17  already-counter at aligned-run start
13  no counter condition in that aligned run
```

This does not predict Parent reversal. It maps a Counter Local-Bridge branch inside the slower Parent context.

The raw-M1 dual-clock prototype reproduced 718 strategy semantic events exactly on consumed data.

Current research state:

```text
STRATEGY EXTRACTION DRAFT = FROZEN FOR IMPLEMENTATION TEST
DUAL-CLOCK RUNTIME = REQUIRED NEXT
FUTURE-HIDDEN JULY = LOCKED
PRODUCTION / EA AUTHORITY = NONE
```


## 2026-09-12 causal state-machine implementation accepted

<!-- V9_CAUSAL_STATE_MACHINE_IMPL_20260912 -->

The frozen strategy-extraction draft has been reproduced as a resumable raw-M1 causal state machine on consumed periods.

Acceptance summary:

```text
revealed consumed rows: 229,861
future-hidden rows revealed: 0
semantic events: 4,254
M5 object-known candidates: 27,899
first Counter runtime authorizations: 149
first With-Parent runtime authorizations: 95
split/resume exact parity: PASS
external-action restart exact parity: PASS
gate-driven mechanical replay: PASS
```

The live-safe authorization universe is intentionally larger than the older cycle-conditioned `141 / 94` research counts. Future H1 resolution is not available to the runtime and is not used to select signals.

Current state:

```text
MARKET-FLOW GRAMMAR = FROZEN FIRST DRAFT
STRATEGY EXTRACTION = FROZEN FIRST DRAFT
DETERMINISTIC CAUSAL MECHANICS = ACCEPTED ON CONSUMED DATA
AI REVIEW/REMAP PACKET + SCHEDULER = NEXT GATE
FUTURE-HIDDEN JULY = LOCKED
PRODUCTION / EA AUTHORITY = NONE
```

Remaining unresolved issues are explicitly listed in `V9_CAUSAL_STATE_MACHINE_IMPLEMENTATION_CHECKPOINT_20260912.md`; do not mine hidden thresholds to remove them.
