# V12 Phase-0 causal event-universe receipt

Date: `2026-09-23`

Status: `PHASE-0 NUMERIC UNIVERSE COMPLETE / NO ENTRY OR PERFORMANCE AUTHORITY`

## What was built

The repository now has a dependency-free causal pipeline that:

1. reads raw `GOLD#` M1 only in chronological order through the frozen cutoff;
2. reconstructs M5, M15, M30, H1, H4, D1, and W1 on the broker's exported
   clock without filling missing minutes;
3. registers every consecutive W1 and D1 pair as C1/C2;
4. assigns the frozen seven-way C2 interaction state using point-rounded strict
   breaches and equality-as-touch;
5. records first M1 extreme breaches and preserves unresolved same-M1 order;
6. emits decision-only JSONL, a rich numeric ledger, a blind-review pack, quality
   diagnostics, and hashes; and
7. validates every parent ID, schema record, summary total, and output hash.

No trigger, Child, entry, outcome, R, or P/L was created in this phase.

## Input and parity evidence

- full local M1 file SHA-256:
  `fd6b1c886519b544b00dfdcf0ee390970e29c54bb3bf7530c3bd1ef52aa47250`;
- causal prefix through `2026-09-18 23:57` SHA-256:
  `04e074ca77f449f02ac65a0b11f8efcb06254272be1a99b7273db8876ec4c939`;
- revealed M1 rows: `1,669,073`, from `2022-01-03 01:00` through the cutoff;
- post-cutoff price rows parsed: `0`;
- the first `101,405,198` bytes exactly match the previously trusted M1 file,
  SHA-256 `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`;
- duplicate timestamps, non-monotonic timestamps, invalid OHLC rows, and off-grid
  price rows: all `0`.

The raw-M1 reconstruction matched all supplied MT5 exports exactly in bar count,
OHLC, tick volume, and volume:

| Timeframe | Completed bars | Exact parity |
|---|---:|---|
| M5 | 334,145 | yes |
| M15 | 111,387 | yes |
| M30 | 55,696 | yes |
| H1 | 27,864 | yes |
| H4 | 7,288 | yes |
| D1 | 1,216 | yes |
| W1 | 245 | yes |

This establishes the broker bucket rules, including W1 Sunday 00:00, but does
not establish UTC conversion. Timestamps remain offset-free MT5 broker labels.

## Event universe

| Lane | C1/C2 records | Directional hypotheses | Same-M1 ambiguous order |
|---|---:|---:|---:|
| D1 -> H1 | 1,215 | 914 | 1 |
| W1 -> H4 | 244 | 191 | 0 |
| Total | 1,459 | 1,105 | 1 |

The blind pack has `634` deterministic, outcome-free records stratified by lane,
year, and interaction state. It is a review input, not a completed discretionary
label audit.

## Reproducibility

Two independent builds were run into separate output directories. All ten output
files were byte-identical. Key hashes:

- decision JSONL:
  `4b5fe2b76d8ba6faca26b062b8caac0aa8d56bcf5e08066b8d11c7375550a33a`;
- rich parent-event CSV:
  `ded52cdc2b195a69dca300c1c0b38dca79cb0eb0ddd8e4f009a0b1589042fbf0`;
- primary output manifest:
  `d9c616f5ad65423c29b08e14c45f6f9c870cb49d95f527852db1de0b4580c20c`.

Large files remain under ignored `output/`. The compact release manifest is
`research/v12/v12_phase0_release_manifest.json`.

## Authority boundary and next gate

Phase 0 proves that V12's parent population is causal, exhaustive, numerically
defined, and reproducible. It does not show that CRT has an edge or performs
better than V10.

Phase 1 must freeze one mechanical C3 trigger definition at a time, both
structural Hard-SL variants, midpoint/opposite-extreme outcomes, ambiguity and
cost policies, then report full lane/side/year/era scorecards. V10 comparison is
not allowed until the V12 baseline uses a fixed matched evidence window and
exposure accounting.
