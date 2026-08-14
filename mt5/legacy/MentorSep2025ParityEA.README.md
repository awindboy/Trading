# MentorSep2025ParityEA

This EA is a Strategy Tester calibration bridge for the official September
2025 GOLD blind ledger. It is intentionally separate from the autonomous
strategy.

It verifies three execution facts before the manual decision layer is ported:

1. the declared root and child ranges existed before the decision;
2. MT5 can place the frozen entry, structural SL and liquidity TP using the
   broker's Bid/Ask and stop rules;
3. actual fill and close timestamps can be compared with the blind ledger.

The embedded reference decisions **must not be interpreted as signal
generation**. They are test fixtures. The autonomous implementation is only
complete when the rule engine emits the same decisions without reading this
fixture table.

## Tester

- Expert: `MentorSep2025ParityEA`
- Symbol: the XM GOLD symbol used by the source dataset
- Period: `M1`
- Model: `Every tick based on real ticks`
- Date: `2025-08-01` through `2025-10-01`
- Inputs: `MentorSep2025ParityEA.GOLD.M1.2025-09.set`
- Live execution: hard blocked by `MQL_TESTER`

The EA writes `MQL5/Files/trading_journal/mentor_sep2025_parity_v2.csv`.
