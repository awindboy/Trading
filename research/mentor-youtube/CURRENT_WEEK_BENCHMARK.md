# Current Weekly Mentor Benchmark

## Active benchmark

- Period: 2025-06-16 through 2025-06-20
- Dataset: GOLD M1, reconstructed as H1/M30/M15/M5/M1 without future bars
- Output: `output/mentor_week_2025-06-16_20_current_rules_reverse_v4`
- Rule contract: `frozen_rule_contract_v4.json`
- Trade ledger: `current_rule_trades.csv`
- Candidate audit: `candidate_audit.jsonl`
- Causality audit: `causality_audit.json`

This V4 ledger is the active in-sample reference for the current mentor rules.
The older `mentor_week_2025-06-16_20_rule_reverse_engineering_v3` result is
retained only as a historical comparison and must not be used as the current
rule benchmark.

## Frozen result

- Trades: 11
- Wins / losses: 9 / 2
- Win rate: 81.82%
- Total: +28.896833R
- Profit factor: 15.4484
- Maximum drawdown: 1.00R
- Maximum concurrent risk: 3.00R

## Interpretation boundary

This is a reverse-engineered in-sample benchmark. It verifies that every
selected trade can be explained by the current rule contract; it does not prove
that the same performance will persist out of sample. Future implementations
must first reproduce this ledger semantically, then be evaluated on an unseen
week without changing the frozen rules.
