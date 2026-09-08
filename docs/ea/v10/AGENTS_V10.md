# V10 Gemini V9-Style Replay

Status: `ACTIVE EXPERIMENT / GEMINI ANALYSIS PARITY`
Market: `GOLD# ONLY`
Replay period: `2025-01-02 08:00 through 2025-01-31 23:57`
Production authority: `NONE`
EA authority: `NONE`

## Purpose

V10 asks one narrow question:

> Given only causally available GOLD# chart history, can Gemini make market reads and discretionary trade decisions that are meaningfully comparable to the current V9 process?

V10 is not a new strategy and does not replace V9. It is an isolated model-capability experiment.

## Separation from V9

- Do not modify V9 documents, journals, decisions, or replay state.
- Do not give Gemini any V9 January 2025 decisions, outcomes, checkpoints, or summaries.
- Do not import an open V9 position or V9 replay ledger.
- Store all generated artifacts under `output/v10_gemini_jan2025/`.
- Do not commit or push V10 work unless the user later asks.

## Evidence boundary

- Gemini may receive historical context that was available before the current cutoff.
- No row, bar, chart, prompt, or state after the current cutoff may be included.
- The only decision period is January 2025.
- `GOLD# 2021` remains untouched.
- Results are descriptive model-behavior evidence, not performance validation.

## Active files

- Behavior contract: `docs/ea/v10/V10_GEMINI_BEHAVIOR_CONTRACT.md`
- Runner: `scripts/v10_gemini_jan2025.py`
- Tests: `tests/test_v10_gemini_jan2025.py`

## Required Gemini decision

At every cutoff Gemini must return:

```text
Parent Journey
active memories
current child route
falsification anchor and genuine restoration behavior
first destination or OPEN ROUTE
TRADE / NO TRADE / NOT YET
if already in a trade: HOLD / EXIT
uncertainties
next review cadence
```

No broker order, EA execution, position sizing, spread model, or live-risk system is in scope.

