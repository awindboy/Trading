# V13 results

Status: `BASELINE STRUCTURAL PARITY CONFIRMED / EXACT-WINDOW OFFICIAL ECONOMIC RECEIPT STILL PENDING`

Store only compact, source-backed result receipts here.

## Current receipts

- `V13_EXECUTION_13002_TEST_RECEIPT_20260926.md` — compilation and synthetic
  execution-recovery tests; not economic evidence.
- `V13_BASELINE0_EXTENDED_ACTUAL_TICK_DIAGNOSTIC_20260926.md` — user's extended
  GOLD# real-tick report, structural parity through the canonical cutoff, and
  explicit protocol mismatches. Diagnostic only.

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
