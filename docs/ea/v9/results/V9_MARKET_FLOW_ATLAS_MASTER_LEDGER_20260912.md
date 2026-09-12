# V9 Market Flow Atlas — Master Ledger

Date: `2026-09-12`
Status: `AUTHORITATIVE CONSUMED-DATA RESEARCH SNAPSHOT / NOT STRATEGY PERFORMANCE`
GitHub base HEAD: `b7ad4da10383699a38434a163a5e8e72db15b5d5`

## 1. Scope

Consumed answer-sheet data only:

```text
2025-01 through 2025-06
2026-01 through 2026-02
```

Locked / untouched:

```text
2025-07 LOCKED
GOLD# 2021 untouched reserve
```

Strict information-known boundary:

```text
2025 known_at < 2025-07-01 00:00
2026 Jan-Feb known_at < 2026-03-01 00:00
```

No July warmup.
No Dec-2025 warmup for Jan-2026.

## 2. Purpose of this ledger

This snapshot exists so a later session can:

- reproduce the current grammar;
- compare new research against the same consumed baseline;
- audit boundary leakage;
- inspect every H4/H1 state and transition;
- attach exact object landmarks;
- identify where a claimed new rule helps or merely overfits;
- recover the research state without relying on chat memory.

## 3. Core state representation

```text
H4 MACRO AUTHORITY
  STRONG / WEAK / NEUTRAL

H4 PHASE
  MIGRATION / LOCAL_INTERRUPT / NEUTRAL

H1 ROLE
  ALIGNED / H1_INTERRUPT

UNCERTAINTY
  UNRESOLVED / AMBIGUOUS
```

Objects are landmarks, not the state machine itself.

## 4. Strict ledger counts

### H4

```text
completed research H4 bars after warmup
2025: 703
2026 Jan-Feb: 188
```

Exact H4 role majority coverage:

```text
2025: 83.9%
2026: 85.1%
```

Macro-state majority coverage:

```text
2025: 95.4%
2026: 98.4%
```

### H1 hierarchy

Valid H4-known H1 hours:

```text
2025: 2687
2026: 714
```

Within directional H4 authority:

```text
2025
H1 ALIGNED:   69.9%
H1 INTERRUPT: 30.1%

2026
H1 ALIGNED:   72.2%
H1 INTERRUPT: 27.8%
```

### H1 nested cycles

```text
2025: 145
2026: 41
```

Consensus realignment before H4 side change:

```text
2025: 76.6%
2026: 78.0%
```

### H4 interruption / transition

```text
H4 migration interruptions
2025: 66
2026: 17

actual directional side changes
2025: 33
2026: 8
```

## 5. State-definition robustness

Nested-cycle topology was checked across:

```text
3 causal H4 state views
x
3 causal H1 state views
```

Realignment range:

```text
2025: 71.5% to 91.2%, mean 82.3%
2026: 76.9% to 89.6%, mean 83.4%
```

Do not interpret the maximum as the preferred model.
The purpose is to show that the topology survives reasonable representation changes.

## 6. Compression result

Most valid H1 time can be described by only a few hierarchy combinations.

Cumulative coverage of the top three hierarchical combinations:

```text
2025: 68.4%
2026: 72.3%
```

Top five:

```text
2025: 84.6%
2026: 87.0%
```

Do not force the remainder into special rules.

## 7. Chronological master event ledger

`MARKET_FLOW_EVENT_LEDGER.csv` contains `2487` events:

```text
1128 POI cluster touches
651 liquidity delivery clusters
336 H4 state-run starts
186 H1 interruption starts
186 H1 interruption resolutions
```

Each event is ordered chronologically and carries the latest known state context where available.

This is the main comparison ledger for later semantic role research.

## 8. Exact landmark snapshots

Strict snapshots:

```text
POI_INTERACTION_CLUSTER_STUDY_STRICT.csv
LIQUIDITY_DELIVERY_CLUSTER_STUDY_STRICT.csv
```

POI snapshot rows: `1128`
Liquidity delivery clusters: `651`

These preserve exact object IDs and geometry from the existing object research pipeline.

Do not treat old `accepted_through` descriptive fields as current strategy authority.
They remain historical columns in the source evidence only.

## 9. Core ledger file roles

### `CONTINUOUS_H4_FLOW_STATE_LEDGER.csv`

One row per research H4 bar.
Contains three causal H4 views, majority state, agreement count, flow state, known-at time.

### `CONTINUOUS_H4_FLOW_RUN_LEDGER.csv`

Consecutive H4 flow states collapsed into runs.
Useful for migration/interruption/neutral transition topology.

### `CONTINUOUS_H1_NESTED_STATE_LEDGER.csv`

H1 state views plus latest causally known H4 state.
Defines H1 alignment/counterflow/local-balance relation.

### `HIERARCHICAL_FLOW_STATE_LEDGER.csv`

H1-resolution joined hierarchy:

```text
H4 phase
H4 confidence
H1 core role
```

### `H1_AUCTION_INTERRUPTION_LEDGER.csv`

Every detected nested H1 interruption cycle and eventual resolution.

### `MIGRATION_INTERRUPTION_LEDGER.csv`

Every H4 migration interruption and whether it resumed, neutralized, or reached opposite side before neutralization.

### `DIRECTIONAL_TRANSITION_BUFFER_LEDGER.csv`

Every detected directional migration side change and its intermediate buffer.

### `H4_UNRESOLVED_RESOLUTION_LEDGER.csv`

Tracks disputed-role directional states to their resolution.

### `H4_AMBIGUOUS_RESOLUTION_LEDGER.csv`

Tracks no-directional-majority episodes to the next migration.

### `H4_H1_MONTHLY_STATE_STRESS_PROFILE.csv`

Monthly state composition and transition difficulty.
Use this instead of inventing month-specific regimes.

## 10. Important research evidence tables

```text
H4_H1_CROSS_VIEW_NESTED_CYCLE_ROBUSTNESS.csv
H1_CYCLE_STATE_CONFIDENCE_STUDY.csv
H1_CYCLE_STATE_CONFIDENCE_MONTHLY.csv
H1_AUCTION_MONTHLY_STABILITY.csv
HIERARCHICAL_FLOW_STATE_TIME_SHARE.csv
HIERARCHICAL_STATE_COMPRESSION_COVERAGE.csv
DIRECTIONAL_TRANSITION_ANATOMY.csv
DIFFICULT_MONTH_2025_05_COMPARISON.csv
H4_UNRESOLVED_RESOLUTION_SUMMARY.csv
H4_AMBIGUOUS_RESOLUTION_SUMMARY.csv
BALANCE_PROBE_CAUSAL_AUDIT.csv
```

`BALANCE_PROBE_CAUSAL_AUDIT.csv` is retained specifically as correction evidence showing why the earlier hindsight-selected balance result was rejected.

## 11. Reproduction scripts

```text
scripts/v9_market_flow_build_core.py
scripts/v9_market_flow_analyze_hierarchy.py
scripts/v9_market_flow_research_tables.py
scripts/v9_market_flow_build_event_ledger.py
scripts/v9_market_flow_validate.py
```

Read:

`scripts/README_MARKET_FLOW_ATLAS.md`

Run the validator after rebuilding.

## 12. Current conclusions

The current evidence supports a continuous nested interpretation:

```text
slower H4 authority
contains
repeated faster H1 interruptions

while H4 authority remains coherent:
H1 often realigns

as H4 authority erodes:
interruptions persist
-> neutralization / ambiguity rises
-> new migration eventually earns control
```

POI/liquidity objects are exact landmarks inside this process.

## 13. What this ledger does NOT prove

It does not prove:

- realized trading expectancy;
- causal entry edge;
- live win rate;
- optimal SL/TP;
- optimal state parameters;
- a deterministic market law.

All current percentages are consumed-data descriptive research.

## 14. Next comparison baseline

Any future proposed market-flow concept should be compared against this ledger and asked:

1. Does it explain previously ambiguous/remainder flow?
2. Does it reduce complexity rather than add branches?
3. Does it survive alternate causal state views?
4. Does it improve route/Parent semantics, not merely classify a rare subset?
5. Does it preserve the locked-data boundary?

If not, do not promote it.
