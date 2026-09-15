# V9 Research Instructions — Current Authority

<!-- V10_TRANSITION_NOTICE_START -->
> **V9 ACTIVE RESEARCH GENERATION CLOSED — 2026-09-16**
> V9 prototype semantics and evidence remain preserved as historical controls.
> Active HA-primary research has moved to V10.
> Read `docs/ea/v9/V9_RESEARCH_CLOSURE_AND_V10_TRANSITION_20260916.md`, then resume from `docs/ea/v10/AGENTS_V10.md`.
> The V9 resume order below remains the correct order only when auditing or reproducing V9 history.
<!-- V10_TRANSITION_NOTICE_END -->


Last synchronized: `2026-09-16`
Status: `CLOSED RESEARCH GENERATION / PROTOTYPE FROZEN HISTORICAL CONTROL / V10 ACTIVE`
Production authority: `NONE`
EA authority: `RESEARCH / DEMO ONLY`
Market authority: `GOLD# ONLY`
Base GitHub HEAD before this update packet: `f57e10c670666dd763152e6302d0952f9a7a2f5d`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
2026-09-16 ALL_TO_CHALLENGE event ledger SHA256: `f6b9189ed80afe6fa4f606dc06eff98beeef85b241429a2499d1532524c61293`
2026-09-16 ALL_TO_CHALLENGE trade ledger SHA256: `ef0cab9a00e67b1b02a12541c0e496dd619a4e9e76ec1401021ac965ad840dad`

## 0. Resume order

GitHub `awindboy/Trading` latest `main` HEAD remains the Single Source of Truth.

Read in this order:

1. `docs/ea/v9/AGENTS_V9.md`
2. `docs/ea/v9/V9_DOCUMENT_AUTHORITY_MAP_20260913.md`
3. `docs/ea/v9/HANDOFF_V9.md`
4. `docs/ea/v9/RESEARCH_STATE_V9.md`
5. `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
6. `docs/ea/v9/V9_PROTOTYPE_AUTHORITY_20260914.md`
7. `docs/ea/v9/V9_MT5_ACTUAL_TICK_VALIDATION_20260914.md`
8. `docs/ea/v9/V9_MONEY_MANAGEMENT_STUDY_20260914.md`
9. `docs/ea/v9/V9_ACTUAL_TICK_EXECUTION_AND_ERA_SCALE_ADDENDUM_20260914.md`
10. `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
11. `docs/ea/v9/V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`
12. `docs/ea/v9/V9_TERMINAL_STAGE_HEIKIN_ASHI_RESEARCH_CHECKPOINT_20260915.md`
13. `docs/ea/v9/V9_TERMINAL_STAGE_CAUSAL_COMBINATION_RESEARCH_CHECKPOINT_20260915.md`
14. `docs/ea/v9/V9_ALL_TO_CHALLENGE_ACTUAL_TICK_LEDGER_REBUILD_20260916.md`
15. `docs/ea/v9/V9_TERMINAL_STATE_TABLE_RESEARCH_CHECKPOINT_20260916.md`
16. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_TERMINAL_STATE_TABLE_STABILITY_20260916.md`
17. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_ORACLE_LEDGER_REPLICATION_20260915.md` — supporting predecessor; item 16 controls where the current state-table work is more specific.
18. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_TERMINAL_STAGE_CAUSAL_DETECTION_20260915.md` — historical predecessor.
19. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_FORWARD_DEMO_20260914.md`
20. current EA/runtime/code state.

Older one-active-Child, hidden-gate, fixed-GOLD-SL, M1-only ambiguity, and pre-ERA4 documents remain historical evidence only when they conflict with current prototype authority.

## 1. Current prototype authority remains unchanged

```text
H1/H4 swing liquidity: causal 2-left / 2-right
H4 liquidity raid: tick-native Bid chronology
Grammar: PRIMARY_ACTIVE / CHALLENGED
Entry: immediate eligible PRIMARY_ACTIVE Arrival
Hard SL: nearest active causal opposite H1 swing liquidity
ERA_SCALE: previous completed H4 Wilder ATR180
ERA_RISK: abs(entry - structural SL) / ERA_SCALE
Eligibility: ERA_RISK <= 4

First accepted Child in active route = ANCHOR_CHILD
  -> own structural SL
  -> hold same-side H4-liquidity Arrivals
  -> exit at CHALLENGE_OPENS

Later accepted Child in same route = CONTINUATION_CHILD
  -> own structural SL
  -> exit at first subsequent H4-liquidity Arrival

No fixed TP.
No SHORT ban.
No Child-count cap.
No day/session/hour filter.
No duration timeout.
```

Terminal-stage / Heikin-Ashi research is **shadow research only** and does not replace current prototype exits.

## 2. Research comparator and literal oracle

A user-requested ALL_TO_CHALLENGE rerun is now retained as a separate terminal-research comparator:

```text
unlimited accepted Children
each Child keeps own structural Hard SL
surviving Children remain open
CHALLENGED -> close all survivors together
```

This comparator is not prototype authority.

Raw uploaded tester:

```text
700 closed Children / +6,973.87 / PF 1.533 / DD 1,700.62
```

Comparable H4-covered cohort:

```text
693 Children / 191 routes
BASE +7,210.31 / PF 1.5655 / DD 1,700.62
```

Correct literal terminal answer sheet:

```text
TRUE LAST ACCEPTED CHILD
-> first completed opposite-color H4 HA after that Child
-> close every still-open Child at H4_FINALIZED executable quote
```

Current literal oracle:

```text
157 Oracle routes
ORACLE +19,827.81 / PF 3.6176 / DD 856.81
BASE -> ORACLE improvement +12,617.50
```

The earlier `156` transition-HA1 oracle is superseded for current research because one route's final Child occurs inside an already-opposite NHA episode.

## 3. Primary evaluation rule

Every candidate must compare identical BASE / candidate / ORACLE cohorts.

```text
ORACLE_IMPROVEMENT_RECOVERY
= (candidate PnL - BASE PnL)
  / (ORACLE PnL - BASE PnL)
```

Always report:

- EXACT / total Oracle;
- EARLY / total Oracle;
- LATE / total Oracle;
- MISS / total Oracle;
- FALSE_NO_ORACLE;
- route/Child oracle regret;
- PF/DD and right-tail preservation.

AUC and raw BASE delta are secondary.

## 4. Current repeat-HA state representation

Current strongest **research representation hypothesis**:

```text
primary same-side participation loss
+ opposite structural pressure gain
+ survived-reversal cycle maturity
+ strong current reversal delivery
```

Best stable discrimination pair:

```text
SAME_PARTICIPATION_LOSS + RESILIENT_PRESSURE
2025 AUC 0.768
2026 AUC 0.730
mean 0.749
```

Best observed consumed-data economic combination:

```text
SAME_PARTICIPATION_LOSS
+ OPP_PRESSURE_GAIN
+ CYCLE_MIN
+ RESILIENT_PRESSURE
```

2025-2026:

```text
BASE +5,307.95
CANDIDATE +9,528.95
ORACLE +16,476.18

BASE delta +4,221.00
Oracle recovery 37.79%
PF 2.103
DD 1,529.50

EXACT 23 / 99
EARLY 8
LATE 5
MISS 63
FALSE 1
```

This is **not authority** and must not be described as validated future performance.

## 5. Mandatory overfit caveat

The combination above was discovered by screening consumed data.

When the combination itself is selected from prior history only:

```text
2025 <- choose using 2024
2026 <- choose using 2024-2025
```

result:

```text
PnL +6,064.84
BASE delta +756.89
Oracle recovery 6.78%
PF 1.642
DD 2,344.84
```

Therefore the current task is representation stability / regret decomposition, not rule promotion.

## 6. Current research objective

Follow:

`V9_NEXT_RESEARCH_CONTRACT_TERMINAL_STATE_TABLE_STABILITY_20260916.md`

Main tasks:

1. explain repeat-state EARLY/LATE/MISS economic regret;
2. test stability of the state representation without combination-selection hindsight;
3. separately solve FIRST-HA1 routes where CycleMin is unavailable;
4. do not return to broad generic-indicator mining;
5. only move toward EA terminal logic after fixed causal semantics survive actual-tick and forward evidence.

## 7. Data governance and guardrails

All supplied GOLD# periods are research-consumable and therefore consumed.

This does not permit hindsight repair.

- `TRUE LAST CHILD` is answer-sheet information only;
- never use future route count, later price, future challenge, final PnL, or oracle timestamp as causal inputs;
- stopped Child stays dead;
- Hard SL remains fixed before entry and never widens;
- Parent/route and Child remain separate;
- no fitted Nth-Child, fixed duration, forced direction balance, cooldown, retry, or hidden min-R rules;
- actual-tick chronology remains higher authority for execution questions;
- no terminal candidate changes strategy authority until separate causal, actual-tick, and forward evidence earns it.
