# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-13`
Status: `ACTIVE / ARRIVAL-DELIVERY GRAMMAR / TRADING EXTRACTION PREP`
Production authority: `NONE`
EA authority: `NONE`
Market authority: `GOLD# ONLY`
Consumed answer-sheet data: `2025-01 through 2025-06`, `2026-01 through 2026-02`
Consumed postmortem data: `2024-01 through 2024-12`
Future-hidden: `2025-07 LOCKED`
Untouched final reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 0. First rule on every resume

GitHub `awindboy/Trading` latest `main` HEAD is the Single Source of Truth.

Before any V9 research, read the current documents in this exact order:

1. `docs/ea/v9/AGENTS_V9.md`
2. `docs/ea/v9/V9_DOCUMENT_AUTHORITY_MAP_20260913.md`
3. `docs/ea/v9/HANDOFF_V9.md`
4. `docs/ea/v9/RESEARCH_STATE_V9.md`
5. `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
6. `docs/ea/v9/V9_ARRIVAL_DELIVERY_GRAMMAR_CORE_AUTHORITY_20260913.md`
7. `docs/ea/v9/V9_ARRIVAL_DELIVERY_GRAMMAR_AND_SIMPLE_BASELINE_CHECKPOINT_20260913.md`
8. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_ARRIVAL_DELIVERY_TRADING_REFINEMENT_20260913.md`
9. `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
10. `docs/ea/v9/V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`
11. current code/tool parity state.

Older FLOW_ROUTE reconstruction, state-action, scheduler, H1-native, COUNTER/WITH_PARENT, or postmortem documents are historical evidence unless explicitly retained by the authority map. They do not override the documents above.

## 1. Current V9 Grammar

The top-level market description is intentionally simple:

```text
MOVING
ARRIVAL
```

`MOVING` means price is between meaningful arrivals. Do not split MOVING into new market states because price accelerates, slows, pulls back, temporarily trends the other way, H1 interrupts, or H4/H1 labels change.

`ARRIVAL` is a factual event with attributes:

```text
SIDE
  UP
  DOWN
  OVERLAP / UNRESOLVED

ROLE
  H4 LIQUIDITY -> DELIVERY / PROGRESSION evidence
  H4 FVG / OB  -> RESPONSE / INTERACTION evidence
```

Arrival direction is an event attribute, not a new market state.

## 2. Slow semantic route status

The current compact semantic layer is:

```text
PRIMARY_ACTIVE(side)
        |
        | opposite H4 liquidity arrival
        v
CHALLENGED / UNRESOLVED
        |
        | next meaningful H4 liquidity arrival
        +-- old side        -> PRIMARY_CONTINUES
        +-- challenger side -> CHALLENGER_EARNED
```

Important interpretation:

- one opposite arrival does not automatically reverse the route;
- POI arrival does not automatically complete a route;
- `CHALLENGED` is explicit uncertainty, not a direction that must be guessed;
- no fixed event count, duration, R threshold, ATR threshold, cooldown, retry limit, or timeout is part of this semantic resolver;
- the consumed study seeded its initial primary from the first available H4-liquidity delivery in the research block. A production/live initialization contract is still unfrozen.

## 3. POI and liquidity roles are separate

Current evidence supports keeping both as arrivals while assigning different research roles:

```text
LIQUIDITY ARRIVAL
= what price actually delivered into / consumed
= primary progression evidence

POI ARRIVAL
= where price interacted / responded
= context for the journey
!= automatic continuation signal
!= automatic reversal signal
```

H4/H1 authority, phase, alignment, interrupt, realign, and similar labels remain context observations only. They cannot silently become route identity or entry authority.

## 4. Active destinations are dynamic

Do not model a route as one fixed origin-to-one-fixed-target path.

Current consumed research showed that the next same-side H4 liquidity destination is often created after the previous destination has already been consumed. Therefore:

```text
ACTIVE_DESTINATION_SET = dynamic
DESTINATION_CONSUMED != ROUTE_COMPLETE
NO CURRENT KNOWN SAME-SIDE TARGET != ROUTE_COMPLETE
```

New destinations may open while the same delivery journey remains alive.

## 5. Current structural evidence — research only

Consumed `2025H1 + 2026JF` research currently supports these descriptive facts:

- `PRIMARY_ACTIVE` H4-liquidity delivery was followed by another same-side H4-liquidity delivery in roughly `73%` of the studied active delivery-to-next-delivery windows;
- the result was similar across the two consumed blocks and both directions, but varied materially month to month;
- `CHALLENGER_EARNED` was followed by another same-side H4-liquidity delivery in roughly `82%` of the small consumed sample (`22` events);
- POI touch/orientation alone did not provide a stable continuation/reversal classifier;
- `CHALLENGED` POI structure did not reliably identify which side would resolve first;
- explicit `CHALLENGED / UNRESOLVED` materially reduced forced semantic disagreement in difficult periods.

These percentages are **not trade win rates** and are not live thresholds.

## 6. Simple trading baseline — checkpoint only

A deliberately primitive consumed-data baseline was used only to confirm that the simplified Grammar can be translated into trades at all.

Prototype family:

```text
state       = PRIMARY_ACTIVE
entry       = next H1 open after a causally confirmed active H4-liquidity delivery event
TP          = nearest causally known same-side H4 liquidity destination
Hard SL     = structural opposite H1 swing comparator
positioning = one-position comparator was tested separately
```

The exploratory H1-structural-SL one-position baseline produced approximately:

```text
resolved win rate: about 70%
net result: about +8R to +9R over the consumed study, depending on still-unfrozen execution/warm-up convention
max drawdown: about 4.4R in the tested comparator
```

The `CHALLENGER_EARNED` subset was stronger in the small sample, approximately `75-79%` resolved win rate and roughly `+5.6R to +6.6R` depending on convention.

Do not freeze these exact P&L numbers yet. The baseline reproduction script and execution convention must be versioned before exact performance receives authority.

The one-position comparator is not a hidden retry limit, trade quota, or final position policy.

## 7. Immediate next work

The next research phase is trading refinement **inside the simplified Grammar**, not another attempt to classify every market fluctuation.

Order:

```text
1. freeze a versioned reproduction script for the simple Entry/SL/TP baseline
2. freeze exact entry-price, object-known-at, target-selection, Hard-SL, spread/tick and intraminute conventions
3. compare PRIMARY_DELIVERY / PRIMARY_CONTINUES / CHALLENGER_EARNED as distinct causal entry contexts
4. study entry geometry during PRIMARY_ACTIVE, especially counter-move / POI-response structures
5. study structural Hard SL placement without widening after entry
6. study destination/journey handling and whether TP should remain nearest-known destination or become a managed journey
7. study existing-Child behavior when PRIMARY_ACTIVE becomes CHALLENGED; do not assume automatic exit
8. quantify payoff, loss containment, overlapping Child behavior, and route-level exposure on consumed data
9. freeze the simplest policy that survives counterexamples without hidden thresholds
10. only then implement/replay through the deterministic runtime and satisfy parity gates
11. only after all gates are explicitly satisfied may future-hidden `2025-07` be reconsidered
```

Do not optimize for a target win rate or minimum R.

## 8. Permanent causal and trading guardrails

Retain without exception:

- no future peek;
- no hindsight backfill;
- stopped Child is dead and never rescued by later price;
- Parent and Child remain separate;
- Hard SL is fixed before entry and never widened;
- code/runtime owns exact price, object geometry, known-at time, fill chronology and R arithmetic;
- AI/human research may interpret semantic role/context but cannot change code-owned geometry;
- no hidden minimum-R, cooldown, retry cap, fixed no-chase, fixed numeric TP, forced LONG/SHORT balance, trade/day quota, or duration threshold;
- do not change authority from one or two examples;
- explicit uncertainty is valid information;
- `PRICE_REVEALED_CUTOFF <= INFORMATION_KNOWN_AT` remains binding;
- accidental future reveal contaminates the interval; never backfill a trade into it.

## 9. Data boundary

```text
2024        = CONSUMED POSTMORTEM / RESEARCH DATA
2025-01..06 = CONSUMED ANSWER-SHEET DATA
2026-01..02 = CONSUMED ANSWER-SHEET DATA
2025-07     = FUTURE-HIDDEN LOCKED
2021        = UNTOUCHED FINAL RESERVE
```

Future-hidden gate: `NOT SATISFIED`.

## 10. What counts as progress now

Progress is no longer a more detailed state taxonomy.

Progress is:

- a causal, compact arrival/delivery representation that remains stable through local noise;
- explicit `CHALLENGED / UNRESOLVED` rather than forced direction;
- a reproducible baseline that shows whether the representation can support good attempts under uncertainty;
- Entry / Hard-SL / journey logic that contains losses without hindsight repair;
- a simple policy whose edge survives consumed counterexamples and implementation parity.
