# Mentor Protocol Implementation Status

> **LEGACY IMPLEMENTATION SNAPSHOT — 2026-07-30**
>
> 이 문서는 당시 OB-first-entry 연구 엔진 상태 기록이다.
> Current V1 strategy / implementation authority는:
>
> - `AGENTS.md`
> - `docs/ea/EA_SPEC.md`
> - `docs/ea/HANDOFF.md`
>
> 이 문서의 OB-only first-position,
> sweep-based SL,
> legacy planner state를
> current V1 계약으로 사용하지 않는다.

## Current Boundary - 2026-07-30

- Strategy source: `MENTOR_RULE_CONTRACT.md`
- Execution boundary: `SYSTEM_EXECUTION_CONTRACT.md`
- Recent evidence audit: `RECENT_EXECUTION_AUDIT_2026-07-23_28.md`
- Python research engine: `mentor_engine/`
- MT5 research port: `mt5/legacy/MentorScenarioTraderEA.mq5`

The old 16-trade Q1 result under `GOLD_2025_Q1_FINAL` is a legacy diagnostic.
It included first-position FVG execution and independently simulated orders, so
it is not the current baseline and must not be used as profitability evidence.

## Implemented In The Current Baseline

- closed-M1 clock and H1/M30/M15/M5/M1 aggregation
- H1 maximum map timeframe; H4 is excluded from active decisions
- OB-only first-position source and CHoCH entry family
- at least one causal HTF-to-LTF OB refinement
- M5 correction context and M1-only sweep/body-close CHoCH sequence
- SL beyond the sweep extreme and causal entry OB
- one active pending order or position
- duplicate causal-chain rejection
- fixed objective with no RR fallback or time exit
- Strategy Tester-only MT5 order permission

Standalone HTF FVG sources, FVG first entries, FVG-origin OB entries, and
in-position FVG add-ons are disabled in the baseline.

## Latest Integration Replay

Output:
`output/mentor_engine/GOLD_2025_Q1_EXECUTION_CONTRACT_20260730/`

- eligible liquidity sweeps: 1,111
- destination plans: 673
- activated scenarios: 8
- candidate orders: 0
- all 8 activated scenarios ended as `PARENT_SOURCE_INVALIDATED`

This is not an economic result. It proves that the current planner-to-trigger
handoff still fails to reproduce the mentor's executable reaction sequence.
The correct next task is to compare these eight source episodes against raw
as-of charts and repair source ownership/trigger handoff. It is not acceptable
to restore FVG entries or loosen thresholds merely to create trades.

## Approval State

- unit tests: passed
- MT5 compile: 0 errors, 0 warnings
- Casebook chart-replay parity: unavailable
- positive expectancy: not demonstrated
- live trading: blocked

No live EA is approved. A separate live build requires replayable mentor cases,
an unused paper period with positive expectancy, and a frozen-rule OOS pass.
