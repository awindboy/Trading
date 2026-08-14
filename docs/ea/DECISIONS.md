# EA Design Decisions

## D-001 — GitHub as project memory

Status: ACTIVE

GitHub is the Single Source of Truth for long-term EA development.

ChatGPT conversation history is not authoritative.

## D-002 — Deterministic baseline first

Status: ACTIVE

The first EA must run without Gemini, Codex, OpenClaw, or other runtime AI dependencies.

## D-003 — MT5 is the primary backtest platform

Status: ACTIVE

Primary validation uses MT5 Strategy Tester, preferably Every tick based on real ticks.

## D-004 — Strategy correctness before profitability

Status: ACTIVE

Implementation parity with the intended rules is validated before optimization or profitability tuning.

## D-005 — Ground Truth V2 is not a prerequisite

Status: ACTIVE

The currently BLOCKED Ground Truth V2 pipeline is not required before baseline EA development.