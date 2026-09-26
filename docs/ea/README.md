# EA strategy research documentation

Last synchronized: `2026-09-26`

## Active research

V13 is the only active strategy-research generation.

```text
repository AGENTS.md
-> docs/ea/v13/AGENTS_V13.md
-> V13_DOCUMENT_AUTHORITY_MAP_20260926.md
-> HANDOFF_V13.md
-> RESEARCH_STATE_V13.md
-> V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md
-> V13_MQL5_BACKTEST_PROTOCOL_20260926.md
```

V13 is a clean rebuild from a minimal H4 standard-Heikin-Ashi strategy. It does
not inherit CRT, ML, Wave, liquidity, session, news, or multi-indicator gates.

The current frozen baseline is one contiguous same-color H4 HA Journey with one
new fixed-size Child after each completed same-color bar, capped at 10 Children,
and full Journey exit/reversal on the first completed opposite-color H4 HA.
There is no SL or TP in Baseline 0.

## Canonical comparison period

Current V13 strategy comparisons use the entire available window:

`2024-01-01 through 2026-08-28`

Partial windows are diagnostic only.

## Historical generations

- V12: frozen immediate predecessor and historical evidence;
- V11: frozen predecessor;
- V10: frozen HA/ML predecessor;
- V9 and earlier: historical evidence only.

Historical documents cannot override V13 authority.
