# V9 Market Flow Atlas + Reverse-Engineering Contract

Date: `2026-09-12`
Status: `ACTIVE CONTRACT / CONTINUOUS HIERARCHICAL MARKET-FLOW RESEARCH`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

Consumed answer-sheet data:

- `2025-01 through 2025-06`
- `2026-01 through 2026-02`

Locked / untouched:

- `2025-07 LOCKED`
- `GOLD# 2021 untouched reserve`

## Purpose

Use consumed data as an answer sheet to understand the continuous price process before extracting trading rules.

The research target is not a final deterministic law and not a rare high-probability setup.

Target:

```text
many hours / many cycles
-> few reusable state relationships
-> explicit ambiguous remainder
```

Current companion authority:

`V9_MARKET_FLOW_GRAMMAR_CONTINUOUS_HIERARCHY_AUTHORITY_20260912.md`

## Research mode

Full future-visible analysis is permitted only on consumed development data.

This is noncausal answer-sheet research.

Therefore:

- do not call results validation;
- do not report descriptive flow percentages as strategy WR/expectancy;
- do not backfill trades;
- do not open July;
- do not use 2021;
- preserve exact timestamps / object IDs / lifecycle;
- make all causal-vs-answer-sheet distinctions explicit.

## Strict boundary rule

Information-known time is authoritative:

```text
2025 known_at < 2025-07-01 00:00
2026 Jan-Feb known_at < 2026-03-01 00:00
```

A source bar dated June 30 but only known at July 1 is outside the consumed research boundary.

## Primary research unit

The primary unit is not a trade.

Use:

```text
H4 MACRO AUTHORITY
H4 PHASE
H1 AUCTION CYCLE
LANDMARK ARRIVAL
DELIVERY PATH
NEUTRALIZATION / RESET
NEXT STATE
```

Ranges, balance, uncertainty, false breaks, sweeps, repairs, and transitions remain first-class market behavior.

## Current hierarchical grammar

### H4 authority

```text
STRONG DIRECTIONAL
WEAK DIRECTIONAL
NEUTRAL / AMBIGUOUS
```

### H4 phase

```text
MIGRATION
LOCAL_INTERRUPT
NEUTRAL
```

### H1 role

```text
ALIGNED
H1_INTERRUPT
```

### Uncertainty

```text
UNRESOLVED_SIDE
AMBIGUOUS
```

Do not eliminate uncertainty by adding more indicators.

## Analysis lenses

### Exact deterministic objects

Continue using code for exact:

- FVG;
- OB candidate;
- swing/liquidity candidate;
- birth/touch/fill/raid/mitigation/invalidation.

These are factual landmarks, not automatic signals.

### State / auction lenses

Study:

- directional authority agreement;
- migration versus local interruption;
- H1 alignment versus H1 interruption;
- authority erosion;
- neutralization;
- route continuation;
- state reset.

### Optional lenses

Generic indicators/patterns may only be reopened if they add stable explanatory power to the continuous grammar.

Current de-prioritized lenses include:

- MACD;
- Bollinger Bands;
- session label alone;
- generic MSS;
- generic fresh-FVG confirmation;
- breaker/inversion auto-flip;
- premium/discount alone;
- fixed sweep counts.

Do not keep testing them by default.

## Describe before explaining

For every continuous segment first record:

```text
current larger authority
current H4 phase
current H1 role
where price arrived
what object/liquidity was consumed
what state changed
where price delivered next
```

Only then propose semantic roles.

Do not invent a special explanation for every leg.

## Robustness method

A useful grammar should survive alternate reasonable causal state views.

Current state research intentionally uses multiple H4 and H1 representations and consensus.

Do not optimize a single lookback for maximum historical accuracy.

Preserve:

```text
STRONG
WEAK
UNRESOLVED
AMBIGUOUS
```

as legitimate outputs.

## Difficult-period method

When one month performs differently, first ask:

```text
Did the grammar fail?
or
did the market spend more time in weak / interrupted / transition states?
```

2025-05 supports the second interpretation.

Do not create month-specific exceptions without strong repeated evidence.

## Atlas outputs

Current core outputs:

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

Research tables include:

```text
H4_H1_CROSS_VIEW_NESTED_CYCLE_ROBUSTNESS.csv
H1_CYCLE_STATE_CONFIDENCE_MONTHLY.csv
HIERARCHICAL_STATE_COMPRESSION_COVERAGE.csv
DIFFICULT_MONTH_2025_05_COMPARISON.csv
H4_UNRESOLVED_RESOLUTION_SUMMARY.csv
H4_AMBIGUOUS_RESOLUTION_SUMMARY.csv
DIRECTIONAL_TRANSITION_ANATOMY.csv
```

## Current research order

```text
CONTINUOUS HIERARCHY
-> ROUTE / DESTINATION SEMANTICS
-> PARENT CONTINUITY / AUTHORITY LOSS
-> EXACT LANDMARK ROLE MAPPING
-> STRATEGY EXTRACTION DRAFT
-> CAUSAL SEQUENTIAL REPLAY
-> LIVE RUNTIME DESIGN
-> FUTURE-HIDDEN REPLAY
```

## Strategy extraction comes later

After the grammar is stable ask:

```text
Which state is knowable in real time?
Which H1 interruption is a tradable Child opportunity?
Which landmark is an objective Child invalidation?
Which delivery is realistic to capture?
When does Parent authority survive Child resolution?
When has Parent authority actually reset?
```

Only then define trading policy.

## Anti-overfit

Do not create:

- one rule per chart example;
- rare-subset optimization;
- month-specific filters;
- ambiguity tiebreakers;
- fixed event counts;
- fixed timeouts;
- fixed retracement depth;
- fixed trade-frequency targets;
- mandatory pattern chains;
- hindsight-only labels;
- special exceptions that rescue failed cases.

## Exit criteria for Atlas phase

Do not return to strategy-performance optimization until:

1. long contiguous consumed periods are represented by the hierarchy;
2. difficult months are explained without special exceptions;
3. ambiguity remains explicit rather than hidden;
4. route/destination semantics are compact;
5. Parent continuity versus reset is defined independently of Child P/L;
6. exact landmarks map to object IDs/lifecycle;
7. the grammar can be translated into causal real-time inputs;
8. a strategy-extraction draft is frozen before hidden replay.
