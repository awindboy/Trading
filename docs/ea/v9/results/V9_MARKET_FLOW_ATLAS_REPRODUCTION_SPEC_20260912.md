# V9 Market Flow Atlas — Reproduction Spec

Date: `2026-09-12`
Status: `REPRODUCTION / PARITY SPEC`

## Source files used by the hierarchy scripts

```text
H4
GOLD#_H4_202201030000_202608282000.csv
SHA256 5e12fa91f974c0f15e340ea8116bd9168fc6821e6309592cee1a7e197675de09

H1
GOLD#_H1_202201030100_202608282300.csv
SHA256 c1d9f63f8af4d7dddd9e20e6eb124dc71de51015384b9c61a772d5981c7be52c

Authoritative M1
GOLD#_M1_202201030100_202608282357(5).csv
SHA256 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
```

H4/H1 exports are acceleration inputs for this answer-sheet hierarchy study.
The existing causal protocol still makes M1 the final price/timestamp authority when disputes matter.

## Strict consumed boundaries

```text
2025 research information-known time < 2025-07-01 00:00
2026 Jan-Feb information-known time < 2026-03-01 00:00
```

Do not use:

- 2025-07 as warmup;
- 2025-12 as warmup for Jan-2026;
- 2021.

## Core build

```bash
python scripts/v9_market_flow_build_core.py \
  --h4 'GOLD#_H4_202201030000_202608282000.csv' \
  --h1 'GOLD#_H1_202201030100_202608282300.csv' \
  --output-dir ./tmp_v9_market_flow
```

Expected core build headline:

```text
H4 state rows: 1003
H4 runs: 336
H1 nested rows: 3837
```

The row counts include in-period warmup rows where appropriate.

## Hierarchy analysis

```bash
python scripts/v9_market_flow_analyze_hierarchy.py \
  --core-dir ./tmp_v9_market_flow \
  --output-dir ./tmp_v9_market_flow
```

Expected strict headline:

```text
H1 cycles: 186
H4 interruptions: 83
Directional side changes: 41
UNRESOLVED episodes: 85
AMBIGUOUS episodes: 25
```

Block parity:

```text
H1 cycles
2025: 145
2026: 41

H4 migration interruptions
2025: 66
2026: 17

Directional side changes
2025: 33
2026: 8
```

## Research tables

```bash
python scripts/v9_market_flow_research_tables.py \
  --dir ./tmp_v9_market_flow
```

This generates:

- monthly cycle stability;
- H4 state-confidence studies;
- hierarchical time-share/compression;
- transition anatomy;
- difficult-month comparison;
- ambiguity/unresolved summaries;
- 3x3 H4/H1 cross-view topology robustness.

Expected cross-view H1 realignment range:

```text
2025: 0.7153 to 0.9118, mean ~0.8225
2026: 0.7692 to 0.8955, mean ~0.8342
```

Do not optimize to the highest member of that range.
The range exists to test topology robustness.

## Chronological event ledger

The event ledger additionally requires the strict POI/liquidity cluster sources produced by the existing object-research pipeline.

```bash
python scripts/v9_market_flow_build_event_ledger.py \
  --dir ./tmp_v9_market_flow \
  --poi POI_INTERACTION_CLUSTER_STUDY.csv \
  --liquidity LIQUIDITY_DELIVERY_CLUSTER_STUDY.csv
```

Current expected strict snapshot:

```text
MARKET_FLOW_EVENT_LEDGER rows: 2487
POI clusters: 1128
liquidity delivery clusters: 651
```

## Validation

```bash
python scripts/v9_market_flow_validate.py \
  --dir ./tmp_v9_market_flow
```

Expected:

```text
PASS: required files/columns
PASS: strict consumed-data information-known boundaries
PASS: headline ledger parity
```

## Interpretation warning

These scripts reproduce **descriptive consumed-data market-flow research**.

They do not reproduce:

- a trading strategy;
- trade entries;
- realized WR/R;
- future-hidden validation.

Do not convert the output percentages directly into live execution rules.
