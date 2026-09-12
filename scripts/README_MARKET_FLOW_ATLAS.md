# V9 Market Flow Atlas Research Scripts

These scripts reproduce the current **continuous hierarchical market-flow grammar** from consumed GOLD# data.

They are research tooling, not trading-strategy authority.

## Required order

### 1. Build causal descriptive H4/H1 states

```bash
python scripts/v9_market_flow_build_core.py \
  --h4 '/path/to/GOLD#_H4_202201030000_202608282000.csv' \
  --h1 '/path/to/GOLD#_H1_202201030100_202608282300.csv' \
  --output-dir /tmp/v9_market_flow
```

### 2. Build hierarchy / transition ledgers

```bash
python scripts/v9_market_flow_analyze_hierarchy.py \
  --core-dir /tmp/v9_market_flow \
  --output-dir /tmp/v9_market_flow
```

### 3. Build research summaries / robustness tables

```bash
python scripts/v9_market_flow_research_tables.py \
  --dir /tmp/v9_market_flow
```

### 4. Build chronological landmark event ledger

Requires the upstream exact object-cluster research tables generated from the existing object engine/pipeline.

```bash
python scripts/v9_market_flow_build_event_ledger.py \
  --dir /tmp/v9_market_flow \
  --poi /path/to/POI_INTERACTION_CLUSTER_STUDY.csv \
  --liquidity /path/to/LIQUIDITY_DELIVERY_CLUSTER_STUDY.csv
```

### 5. Validate

```bash
python scripts/v9_market_flow_validate.py \
  --dir /tmp/v9_market_flow
```

## Boundary rule

The information-known timestamp is authoritative.

```text
2025 state/event known_at < 2025-07-01 00:00
2026 Jan-Feb state/event known_at < 2026-03-01 00:00
```

Do not:

- use 2025-07 as warmup;
- use Dec-2025 as warmup for Jan-2026;
- use the 2021 reserve.

## State methodology

The implementation intentionally uses multiple causal views.

H4:

```text
state_A
state_B
state_C
```

H1:

```text
state_ema20
state_net_mid
state_ema_stack
```

2-of-3 consensus is used to reduce dependence on one exact representation.

Disagreement is preserved as:

```text
WEAK
UNRESOLVED_UP / DOWN
AMBIGUOUS
```

Do not add another indicator just to remove disagreement.

## Core semantic hierarchy

```text
H4 AUTHORITY
-> H4 PHASE
-> H1 AUCTION
-> EXACT LANDMARKS
-> RESOLUTION
-> NEXT STATE
```

Object geometry remains owned by the existing deterministic V9 object tooling.

## Interpretation warning

The output is consumed-data Atlas research.

Do not interpret:

- H1 realignment percentage as trade WR;
- state transitions as entry signals;
- high conditional subsets as validated edge;
- exact lookbacks as optimized strategy parameters.

Read the current authority and research chronicle before modifying these scripts.
