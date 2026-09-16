# V10 Handoff

Date: `2026-09-16`
Status: `ACTIVE HA-PRIMARY SHADOW RESEARCH`

<!-- V10_POST_HEAD_HANDOFF_20260916_START -->
## Current priority override — post-HEAD / actual-tick gate

The earlier handoff remains historical context, but the current resume path is:

1. confirm latest GitHub `main`;
2. follow `AGENTS_V10.md`;
3. read `V10_POST_HEAD_RESEARCH_CHECKPOINT_20260916.md`;
4. read `V10_BOUNDED_M3_ACTUAL_TICK_VALIDATION_20260916.md`;
5. follow `V10_NEXT_RESEARCH_CONTRACT_EXECUTION_FIDELITY_AND_DANGER_REGEN_20260916.md`.

Current research thesis:

```text
Opportunity != Safety

k1:
Opportunity Head + extreme Danger Head
-> participate or abstain

k2:
Persistence Head
-> confirm / stop adding

k3+:
marginal Child economics

FAST NHA:
campaign exit
```

Current exact executable benchmark remains bounded `m=3`. The post-HEAD shock-veto result is not yet reproducible enough to embed.

The first actual-tick bounded-m3 test produced raw `+$16,220.67 / PF 1.6866`, but that headline is contaminated by non-persistent market-closed FAST-NHA exits and must not be treated as validated strategy performance.

Execution-fidelity repair comes before additional model tuning.
<!-- V10_POST_HEAD_HANDOFF_20260916_END -->

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

<!-- V10_REPRO_LEDGER_HANDOFF_20260916_START -->
## Reproducibility handoff — row-level evidence is now available

The current V10 handoff now has a complete row-level research spine for the existing bounded-m3 control:

```text
1,159 selected signals
-> exact entry fill/reject state
-> normalized MT5 order/deal rows
-> failed FAST-NHA exit incidents
-> actual exit and exposure path
-> M1-reference parity
-> causal M15/M30/H1/H4 selected-signal state
-> deterministic model-regeneration artifacts
```

Use `V10_DATA_AND_LEDGER_MANIFEST_20260916.md` as the data-lineage index.

Important distinction:

```text
old session-recorded shock-veto result
= historical consumed evidence

new _REGEN models
= reproducible selection-conditioned candidates
```

Do not describe the latter as recovery of the former.

Before another model scan, run:

```text
python scripts/v10_validate_repro_pack.py .
```

Execution fidelity still comes first. A repaired actual-tick control must preserve immutable `EXIT_PENDING` and must be compared to the new row-level parity ledger before any strategy conclusion is drawn.
<!-- V10_REPRO_LEDGER_HANDOFF_20260916_END -->

<!-- V10_DECISION_CLOCK_HOTFIX_HANDOFF_20260916_START -->
## Decision-clock hotfix

The reproducibility pack distinguishes the signal clock from the actual tick clock.

Read `V10_SIGNAL_DECISION_CLOCK_HOTFIX_20260916.md` before using the row-level execution or feature ledgers.

For filled rows, the EA may log the entry event one or two seconds after the H4 decision boundary. The exact intended clock is already persisted as `effective_ts`; that value must match the baseline `decision_ts` exactly. Actual event/fill time remains separate execution evidence.
<!-- V10_DECISION_CLOCK_HOTFIX_HANDOFF_20260916_END -->
