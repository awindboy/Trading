# V10 Handoff

Date: `2026-09-16`
Status: `ACTIVE HA-PRIMARY SHADOW RESEARCH`

## Resume first

1. Confirm latest GitHub `main` HEAD.
2. Read `AGENTS_V10.md`.
3. Read `V10_DOCUMENT_AUTHORITY_MAP_20260916.md`.
4. Read V9 closure / transition.
5. Read `RESEARCH_STATE_V10.md`.
6. Read `V10_HA_PRIMARY_RESEARCH_CHECKPOINT_20260916.md`.
7. Read `V10_NEXT_RESEARCH_CONTRACT_ORACLE_PARTICIPATION_20260916.md`.
8. Inspect `results/` ledgers.

## Current generation thesis

V10 is not a V9 terminal-exit tweak.

The working hypothesis is:

```text
HA should own participation timing.
Grammar should become context.
H1 liquidity should retain structural invalidation / risk.
STD / SLOW / LTF HA should describe maturity and delivery.
```

## Current FAST / STD / SLOW roles

```text
FAST w2/a0.25
-> execution / run clock

STD w1/a0.50
-> strongest current early-run representation
-> directional support

SLOW w2/a0.75
-> broader maturity context
-> not supported as delayed exit authority
```

## Current best answer sheet

```text
k = current FAST same-color HA index
L = final FAST same-color run length

TRUE EARLY THIRD:
3*k <= L
```

`L` is answer-sheet-only.

## Current best practical research direction

Do not simply increase size every three HA bars.

Current evidence favors:

```text
P_RUNWAY
* P_WIN
* P_STD_SUPPORT
```

followed by bounded exposure.

The current bounded diagnostic captures about 80% of true early-third Oracle bars but has only about 39% precision. False positives are the primary research problem.

## Important negative results

- PURE HA participation without state filtering increases raw PnL but reduces quality.
- delaying exit until SLOW HA confirmation is poor;
- BASE / SLOW confirmation generally gives back too much;
- Grammar-confirmed delayed exit can generate very large right-tail gains but uses extreme exposure and is highly concentrated;
- adding every MTF HA feature worsens generalization;
- high AUC on very long runway labels does not automatically produce best economics;
- fixed bar-count pyramiding does not replicate the Oracle well.

## Current execution caveat

V10 hypothetical H1 stops are screened with M1 first-touch, not V10 actual-tick execution.

Do not describe V10 as actual-tick validated.

## Most important files

- `results/V10_FAST_CHILD_ORACLE_STATE_LEDGER_2025_2026.csv`
- `results/V10_BOUNDED_M3_ENTRY_LEDGER_2025_2026.csv`
- `results/V10_BOUNDED_M3_RUN_LEVEL_LEDGER_2025_2026.csv`
- `results/V10_RUNWAY_MULTIPLE_SCAN_20260916.csv`
- `results/V10_SIZING_COMPARISON_20260916.csv`
