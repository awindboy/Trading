# V13 results

Status: `HA-4C/D INTEGRATED OBSERVATION COMPLETE / EXACT-WINDOW OFFICIAL ECONOMIC RECEIPT STILL PENDING`

Store only compact, source-backed result receipts here.

## Current receipts

- `V13_EXECUTION_13002_TEST_RECEIPT_20260926.md` — compilation and synthetic
  execution-recovery tests; not economic evidence.
- `V13_BASELINE0_EXTENDED_ACTUAL_TICK_DIAGNOSTIC_20260926.md` — user's extended
  GOLD# real-tick report, structural parity through the canonical cutoff, and
  explicit protocol mismatches. Diagnostic only.
- `V13_HA0_MEASUREMENT_RECEIPT_20260927.md` — causal standard-HA source/ledger
  parity and Journey/Child structural counts.
- `V13_HA1_MORPHOLOGY_PERSISTENCE_RECEIPT_20260927.md` — body, wick and
  contraction transition associations; no rule.
- `V13_HA2_LIFECYCLE_GIVEBACK_RECEIPT_20260927.md` — raw M1 extreme-to-flip
  lag and giveback anatomy; no exit rule.
- `V13_HA3_REPRESENTATION_COMPARISON_RECEIPT_20260927.md` — STD, FAST-R25 and
  pre/post-EMA2 descriptive comparison; no representation promoted.
- `V13_HA4_D1_STANDARD_HA_RECEIPT_20260927.md` — last completed D1 standard
  HA context at H4 decisions; no alignment gate.
- `V13_HA4_H1_STANDARD_HA_RECEIPT_20260927.md` — completed H1 warning,
  false-warning and H4 raw-close redundancy checks; no exit rule.
- `V13_HA4C_D_INTEGRATED_STATE_RECEIPT_20260927.md` — same-Standard-Journey
  HA morphology, ordered H1 path, FAST/D1 and PRE/POST EMA wick comparisons;
  this supplement is required context before interpreting HA-3/4 as complete
  HA-state research. No action rule.

Generated CSV ledgers and summary JSON are local under
`output/v13_ha3_20260927/` and are not Git authority. The reproducible source
is `research/v13/ha_representation_audit.py`.

HA-4's separately generated D1/H1 decision-feature, future-label and summary
files are local under `output/v13_ha4_d1_20260927/` and
`output/v13_ha4_h1_20260927/`. Its source is
`research/v13/ha4_mtf_audit.py`.

HA-4C/D's regenerated H1/D1 and integrated ledgers are local under
`output/v13_ha4c_*_20260927/`. Reproduce with `ha4_mtf_audit.py` and
`research/v13/ha_integrated_state_audit.py`; local ledgers are not Git
authority.

## Official Baseline-0 receipt still required

Expected file:

`V13_BASELINE0_MT5_ACTUAL_TICK_RESULT_20260926.md`

It should come from a run matching the frozen protocol exactly, including:

```text
GOLD#
H4
Every tick based on real ticks
2024-01-01 .. 2026-08-28
10,000 USD
1:100 leverage unless the authority is explicitly revised
hedging mode
current execution revision
```

Identify EA revision/hash, tester build/broker, raw report filename/hash, and the
metrics required by `../V13_MQL5_BACKTEST_PROTOCOL_20260926.md`.

Large XLSX/HTML/CSV tester exports stay outside Git unless explicitly promoted.
