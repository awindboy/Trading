# V9 Development Handoff

Last updated: `2026-09-12`
Status: `ACTIVE / CONTINUOUS HIERARCHICAL MARKET-FLOW GRAMMAR`
Current phase: `ANSWER-SHEET FLOW GRAMMAR -> ROUTE/PARENT SEMANTICS -> STRATEGY EXTRACTION`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed: `2025-01 through 2025-06`, `2026-01 through 2026-02`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
GitHub base HEAD for this handoff bundle: `b7ad4da10383699a38434a163a5e8e72db15b5d5`

## Why the project pivoted

The earlier research loop repeatedly became:

```text
trade result
-> local diagnosis
-> local rule change
-> another problem
```

This was too close to the historical V3-to-V9 overfit pattern.

The project therefore moved from setup optimization to **continuous market-flow reverse engineering**.

The main question is now:

> What small state grammar explains the continuous GOLD flow, including trends, repairs, ranges, uncertainty, and true transitions?

## Current grammar

```text
H4 MACRO AUTHORITY
  STRONG DIRECTIONAL
  WEAK DIRECTIONAL
  NEUTRAL / AMBIGUOUS

-> H4 PHASE
  MIGRATION
  LOCAL_INTERRUPT
  NEUTRAL

-> H1 AUCTION
  ALIGNED
  H1_INTERRUPT

-> LANDMARKS
  POI / FVG / OB / LIQUIDITY

-> RESOLUTION
  H1 REALIGN / H4 NEUTRALIZE / H4 SIDE CHANGE

-> NEXT STATE
```

This is a descriptive research grammar, not yet a trading strategy.

## Important findings

### Broad H4 topology

Strict final consumed-data ledger:

```text
H4 migration interruptions
2025 Jan-Jun: 66
2026 Jan-Feb: 17

actual H4 directional side changes
2025: 33
2026: 8
```

Migration normally alternates with local interruption.
Opposite-side control usually takes time and often passes through a neutral / ambiguous buffer.

### H1 recurring auction

```text
H1 interruption cycles
2025: 145
2026 Jan-Feb: 41
```

Consensus H1 realignment before H4 side change:

```text
2025: 76.6%
2026: 78.0%
```

Across 3 H4 views x 3 H1 views, the topology survives with different exact percentages.
The nested-timescale relationship is more important than any specific EMA/lookback implementation.

### Difficult 2025-05

May is transition-heavy rather than a special failure of the grammar.

Compared with other 2025 consumed months it had:

- less strong H4 authority;
- more weak H4 authority;
- more H4 local-interrupt time;
- more H4 neutral time;
- more actual side changes;
- slower H1-cycle resolution;
- lower H1 realignment.

Do not create a May-specific rule.

### Explicit uncertainty

`UNRESOLVED_SIDE` retains a directional majority but disputed local role.
`AMBIGUOUS` has no directional macro majority.

In 2025, 22 AMBIGUOUS episodes split exactly 11 / 11 between same-direction and opposite-direction next migration.
Therefore forcing ambiguity into a direction would invent information.

## Critical corrections

1. Some early high acceptance/rejection percentages reused classification-window movement; they are descriptive, not forward alpha.
2. The old ~94% `last accepted balance probe` result was hindsight-selected and is not authority.
3. Generic session, MSS, fresh-FVG, breaker/inversion, premium/discount, MACD/BB, fixed sweep-count studies did not add stable enough discrimination and are not active research directions.
4. Rare `repair + POI + support-response` 80-90% subsets are not the target.
5. Strict information-known boundary excludes the June-source bar known at `2025-07-01 00:00`.

## Current code / data bundle

New research scripts:

```text
scripts/v9_market_flow_build_core.py
scripts/v9_market_flow_analyze_hierarchy.py
scripts/v9_market_flow_research_tables.py
scripts/v9_market_flow_validate.py
scripts/README_MARKET_FLOW_ATLAS.md
```

They build and validate:

```text
CONTINUOUS_H4_FLOW_STATE_LEDGER.csv
CONTINUOUS_H4_FLOW_RUN_LEDGER.csv
CONTINUOUS_H1_NESTED_STATE_LEDGER.csv
HIERARCHICAL_FLOW_STATE_LEDGER.csv
H1_AUCTION_INTERRUPTION_LEDGER.csv
MIGRATION_INTERRUPTION_LEDGER.csv
DIRECTIONAL_TRANSITION_BUFFER_LEDGER.csv
H4_UNRESOLVED_RESOLUTION_LEDGER.csv
H4_AMBIGUOUS_RESOLUTION_LEDGER.csv
H4_H1_MONTHLY_STATE_STRESS_PROFILE.csv
```

Additional research tables include cross-view robustness, state confidence, difficult-month comparison, and ambiguity-resolution summaries.

Exact object geometry remains owned by existing V9 object tooling.

## Immediate next research

Do not add new generic indicators first.

### 1. Route/destination inside the normal cycle

Study:

```text
H4 authority
-> H1 interrupt
-> H1 realign
-> next delivery
-> next meaningful POI/liquidity
```

Goal: identify the natural sequence of transit versus campaign-changing landmarks.

### 2. Parent continuity ledger

Explicitly distinguish:

```text
SAME PARENT / NEXT H1 AUCTION
PARENT AUTHORITY LOST / AUCTION RESET
```

Use H4 authority erosion / neutralization, not one Child outcome or one MSS.

### 3. Exact landmark roles

Attach object IDs and roles:

```text
ORIGIN
TRANSIT
DELIVERY
CAMPAIGN-CHANGING
```

Do not infer coordinates visually.

### 4. Strategy extraction gate

Only when the flow grammar plus route/Parent semantics are compact and reproducible should the project write a strategy-extraction draft.

Then return to causal sequential replay.

## Things the next session must not do

- Do not reopen July.
- Do not touch 2021.
- Do not optimize a rare high-WR subset.
- Do not force unknown states into direction.
- Do not introduce a May-specific rule.
- Do not make indicators/session/ICT patterns mandatory confirmation.
- Do not create fixed event-count/time thresholds from the Atlas.
- Do not optimize Entry/SL/TP yet.
- Do not call answer-sheet statistics validation.
- Do not backfill trades.
- Do not let Child P/L define Parent authority.

## Downstream trading principles remain intact

When strategy extraction begins again:

- Parent/Child separation;
- Hard SL before entry, never widen;
- exact code/runtime coordinates;
- no minimum-R / fixed ATR-S stop/TP rule;
- no cooldown/retry cap/trade quota;
- runtime guards, AI plans/reviews;
- no hindsight rescue.
