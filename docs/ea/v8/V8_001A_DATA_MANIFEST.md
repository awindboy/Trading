# V8-001A Data Manifest

Status: `OPEN DEVELOPMENT SOURCE / STILL AUTHORITATIVE FOR CURRENT V8 DATA LINEAGE`
Date recorded: `2026-08-30`
Last reviewed: `2026-08-31`

## Source

```text
filename: GOLD#_M1_202201030100_202608282357.csv
sha256: 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
bytes: 101405198
data_rows: 1648545
first_timestamp: 2022-01-03 01:00:00
last_timestamp: 2026-08-28 23:57:00
```

Expected columns:

```text
<DATE>
<TIME>
<OPEN>
<HIGH>
<LOW>
<CLOSE>
<TICKVOL>
<VOL>
<SPREAD>
```

## V8 role

This file remains the open development source used by the current V8 representation, direction-falsification and movement-probability research.

All years contained in it are treated as consumed/open for final-claim purposes because prior/current project research has already inspected these periods.

It may support chronological development diagnostics but cannot become a pristine V8 holdout.

## Important chronological rule added during V8-003

For labels that resolve after the decision timestamp, chronological evaluation must purge a training event if the event's label-resolution time crosses the next evaluation boundary.

A decision occurring before an evaluation year is not sufficient by itself to make the sample eligible for training.

## Untouched temporal reserve

```text
GOLD# 2021
```

The 2021 reserve is not present in this manifest and remains unopened.

Do not open it merely because the project is currently in phase name `V8-005A`. The reserve stays locked until a **claim-grade candidate and evaluation protocol are frozen**, not simply until a phase number is reached.

## Repository policy

The raw CSV is intentionally not committed to Git by the current update package.

Small reproducibility artifacts such as model parity references may be committed under `ledgers/v8/`.
