# V9 Development Handoff

Last updated: `2026-09-13`
Status: `ACTIVE / ARRIVAL-DELIVERY GRAMMAR / TRADING EXTRACTION PREP`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
GitHub HEAD used for this document update: `ad8bc8efc47cd9478e1b7f7e8d5bfbba398218ce`

## Current correction

The latest consumed research simplified V9 again.

The project no longer tries to represent every acceleration, pullback, H1 interrupt, realignment, temporary countertrend, or H4/H1 state change as a new market state.

The top-level visual Grammar is now:

```text
MOVING
ARRIVAL
```

Movement may contain large pullbacks or temporary counter-delivery without forcing a new state.

## Current arrival roles

Arrival is factual and carries attributes rather than creating many states:

```text
SIDE
  UP / DOWN / OVERLAP-UNRESOLVED

ROLE
  H4 LIQUIDITY -> DELIVERY / PROGRESSION
  H4 FVG / OB  -> RESPONSE / INTERACTION
```

The central empirical correction is that POI touch itself is not a reliable continuation/reversal classifier. POI is where interaction occurs. H4 liquidity consumption is the cleaner evidence for destination progression.

## Current slow semantic resolver

```text
PRIMARY_ACTIVE(side)
        |
        | opposite H4 LIQ arrival
        v
CHALLENGED / UNRESOLVED
        |
        | next H4 LIQ
        +-- old side        -> PRIMARY_CONTINUES
        +-- challenger side -> CHALLENGER_EARNED
```

No numeric count, timeout, ATR threshold, R threshold, cooldown, or retry rule is attached to this resolver.

`CHALLENGED` is explicit uncertainty. Do not force a direction merely to cover every hour of price history.

## Why this simplification survived consumed review

Using consumed `2025H1 + 2026JF` strict event evidence:

- H4 arrivals compressed to a small factual event vocabulary instead of many H1/H4 state changes;
- active H4-liquidity delivery was followed by another same-side H4-liquidity delivery in roughly `73%` of active delivery-to-next-delivery windows;
- the result was similar across the two consumed blocks and both directions, though not uniform by month;
- after `CHALLENGER_EARNED`, another same-side H4-liquidity delivery occurred in roughly `82%` of the small `22`-event consumed sample;
- POI-only arrival did not provide a stable direction classifier;
- POI structure inside `CHALLENGED` did not reliably determine the winner;
- treating `CHALLENGED` as unresolved materially reduced forced disagreement in difficult manual route periods.

These are semantic/descriptive research results, not trade win rates.

## Destination-set correction

The current route should not be modeled as one fixed target.

The H4 swing-liquidity candidate geometry was reconstructed against the strict ledger with `220/220` H4 liquidity object IDs reproduced in the consumed study.

Within same-primary continuation pairs:

- about half of the next actually consumed same-side H4 liquidity targets were already known at the previous delivery;
- about half were born only after that previous delivery;
- there were many cases where no known same-side H4 liquidity target remained immediately after a delivery, yet the same route later continued after new liquidity formed.

Therefore:

```text
ACTIVE_DESTINATION_SET is dynamic.
DESTINATION_CONSUMED != ROUTE_COMPLETE.
NO KNOWN NEXT TARGET != ROUTE_COMPLETE.
```

## Simple Entry / SL / TP baseline

A deliberately primitive trading translation was tested only to answer whether this simplified Grammar can support a viable trade process before deeper refinement.

Prototype:

```text
state       PRIMARY_ACTIVE
entry       next H1 open after a causal active H4-liquidity delivery event
TP          nearest causally known same-side H4 liquidity
Hard SL     opposite H1 structural swing comparator
position    one-position comparator examined separately
```

The interactive research session produced an H1-structural-SL one-position result around `70%` resolved wins and approximately `+8R` on the consumed sample with roughly `4.4R` maximum drawdown. A nearby independent reconstruction under still-unfrozen warm-up/execution conventions produced a similar resolved win rate and roughly `+9R`.

The `CHALLENGER_EARNED` subset was stronger in the small sample, around `75-79%` resolved wins and roughly `+5.6R to +6.6R` depending on convention.

These exact P&L figures are **not frozen strategy authority**. The discrepancy is evidence that the reproduction script and execution convention must be versioned before performance numbers receive authority.

Important qualitative baseline result:

- signal-H1-extreme SL was usually too tight and suffered normal journey noise;
- H4 structural SL was usually too wide and converted high win rate into weak R efficiency;
- H1 structural swing SL was the best simple balance in this preliminary comparison.

No minimum-R filter was introduced.

## Immediate continuation point

Do not return to market-state proliferation.

Next work:

1. freeze a reproducible baseline script and exact execution conventions;
2. keep `CHALLENGED` as `UNRESOLVED / NO-EDGE` for new-entry research unless consumed evidence earns something better;
3. study entry geometry only inside `PRIMARY_ACTIVE`;
4. compare entry contexts `PRIMARY_DELIVERY`, `PRIMARY_CONTINUES`, and `CHALLENGER_EARNED`;
5. refine Hard SL structurally without widening after entry;
6. study journey/TP management around dynamic destinations;
7. audit overlapping/repeated Child attempts without inventing retry limits;
8. study what an already-open Child should do when the semantic route becomes challenged;
9. replay the simplest surviving policy on consumed data through deterministic runtime mechanics;
10. satisfy implementation/parity gates before any future-hidden replay.

## Permanent guardrails

- GitHub latest `main` HEAD is SSOT;
- no future peek or hindsight backfill;
- stopped Child is dead;
- Hard SL fixed before entry and never widened;
- Parent/Child remain separate;
- no hidden minimum-R, cooldown, retry cap, fixed no-chase, fixed numeric TP, forced LONG/SHORT balance, duration threshold, or trade quota;
- code/runtime owns exact geometry, known-at time, fills and arithmetic;
- explicit uncertainty is valid;
- 2025-07 remains locked;
- 2021 remains untouched.
