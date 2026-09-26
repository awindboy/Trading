# EA strategy research documentation

Last synchronized: `2026-09-27`

## Active research

V13 is the only active strategy-research generation.

```text
repository AGENTS.md
-> docs/ea/v13/AGENTS_V13.md
-> V13_DOCUMENT_AUTHORITY_MAP_20260926.md
-> HANDOFF_V13.md
-> RESEARCH_STATE_V13.md
-> V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md
-> V13_HA_RESEARCH_ROADMAP_20260926.md
-> V13_HA3_REPRESENTATION_COMPARISON_CONTRACT_20260927.md
-> V13_HA4_MTF_OBSERVATION_CONTRACT_20260927.md
-> V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md
-> V13_EXECUTION_RECOVERY_20260926.md
-> V13_MQL5_BACKTEST_PROTOCOL_20260926.md
-> results/
```

V13 is a clean rebuild from a minimal H4 standard-Heikin-Ashi strategy. The
HA-0..HA-4 observation receipts are under `results/`. HA-4 studied completed
D1 and H1 standard HA separately without changing the Baseline-0 EA. The next
stage is HA-5 raw-price structure, observation-only.

Baseline 0 remains one contiguous same-color H4 HA Journey with one fixed-size
Child after every completed same-color bar, capped at ten successful Children,
and full Journey exit/reversal on the first completed opposite-color H4 HA.
There is no SL or TP.

## Canonical comparison period

`2024-01-01 through 2026-08-28`

Partial windows are diagnostic only.

## Current HA research program

The active roadmap proceeds one layer at a time:

```text
standard-HA measurement ledger
-> HA morphology
-> HA lifecycle / lag / giveback
-> HA smoothing variants
-> multi-timeframe standard HA
-> raw-price structure complement
-> single external complements (HASTOC / EMA / ATR / ADX-SuperTrend / volume)
-> one-action-rule experiments
-> ML only after the representation is understood
```

External sources are registered with evidence class and caveats. MQL5
community/Market material is used to generate hypotheses, not to establish edge.

## Historical generations

- V12: frozen immediate predecessor and historical evidence;
- V11: frozen predecessor;
- V10: frozen HA/ML predecessor;
- V9 and earlier: historical evidence only.

Historical documents cannot override V13 authority.
