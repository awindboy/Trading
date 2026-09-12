# V9 Development Handoff

Last updated: `2026-09-13`
Status: `ACTIVE / CONTINUOUS HIERARCHICAL MARKET-FLOW GRAMMAR`
Current phase: `CONTINUOUS GRAMMAR -> UNIFIED STATE-ACTION POLICY RESEARCH`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed: `2025-01 through 2025-06`, `2026-01 through 2026-02`
Consumed postmortem: `2024-01 through 2024-12`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
GitHub base HEAD for this handoff bundle: `ce9ab2651cf6112e36aebbf1fb549f7a5f3e7b8f`

## Why the project pivoted

The earlier research loop repeatedly became:

```text
trade result
-> local diagnosis
-> local rule change
-> another problem
```

This was too close to the historical V3-to-V9 overfit pattern.

The project therefore moved from setup optimization to **continuous market-flow reverse engineering**.

The main question is now:

> What small state grammar explains the continuous GOLD flow, including trends, repairs, ranges, uncertainty, and true transitions?

## Current grammar

```text
H4 MACRO AUTHORITY
  STRONG DIRECTIONAL
  WEAK DIRECTIONAL
  NEUTRAL / AMBIGUOUS

-> H4 PHASE
  MIGRATION
  LOCAL_INTERRUPT
  NEUTRAL

-> H1 AUCTION
  ALIGNED
  H1_INTERRUPT

-> LANDMARKS
  POI / FVG / OB / LIQUIDITY

-> RESOLUTION
  H1 REALIGN / H4 NEUTRALIZE / H4 SIDE CHANGE

-> NEXT STATE
```

This is a descriptive research grammar, not yet a trading strategy.

## Important findings

### Broad H4 topology

Strict final consumed-data ledger:

```text
H4 migration interruptions
2025 Jan-Jun: 66
2026 Jan-Feb: 17

actual H4 directional side changes
2025: 33
2026: 8
```

Migration normally alternates with local interruption.
Opposite-side control usually takes time and often passes through a neutral / ambiguous buffer.

### H1 recurring auction

```text
H1 interruption cycles
2025: 145
2026 Jan-Feb: 41
```

Consensus H1 realignment before H4 side change:

```text
2025: 76.6%
2026: 78.0%
```

Across 3 H4 views x 3 H1 views, the topology survives with different exact percentages.
The nested-timescale relationship is more important than any specific EMA/lookback implementation.

### Difficult 2025-05

May is transition-heavy rather than a special failure of the grammar.

Compared with other 2025 consumed months it had:

- less strong H4 authority;
- more weak H4 authority;
- more H4 local-interrupt time;
- more H4 neutral time;
- more actual side changes;
- slower H1-cycle resolution;
- lower H1 realignment.

Do not create a May-specific rule.

### Explicit uncertainty

`UNRESOLVED_SIDE` retains a directional majority but disputed local role.
`AMBIGUOUS` has no directional macro majority.

In 2025, 22 AMBIGUOUS episodes split exactly 11 / 11 between same-direction and opposite-direction next migration.
Therefore forcing ambiguity into a direction would invent information.

## Critical corrections

1. Some early high acceptance/rejection percentages reused classification-window movement; they are descriptive, not forward alpha.
2. The old ~94% `last accepted balance probe` result was hindsight-selected and is not authority.
3. Generic session, MSS, fresh-FVG, breaker/inversion, premium/discount, MACD/BB, fixed sweep-count studies did not add stable enough discrimination and are not active research directions.
4. Rare `repair + POI + support-response` 80-90% subsets are not the target.
5. Strict information-known boundary excludes the June-source bar known at `2025-07-01 00:00`.

## Current code / data bundle

New research scripts:

```text
scripts/v9_market_flow_build_core.py
scripts/v9_market_flow_analyze_hierarchy.py
scripts/v9_market_flow_research_tables.py
scripts/v9_market_flow_validate.py
scripts/README_MARKET_FLOW_ATLAS.md
```

They build and validate:

```text
CONTINUOUS_H4_FLOW_STATE_LEDGER.csv
CONTINUOUS_H4_FLOW_RUN_LEDGER.csv
CONTINUOUS_H1_NESTED_STATE_LEDGER.csv
HIERARCHICAL_FLOW_STATE_LEDGER.csv
H1_AUCTION_INTERRUPTION_LEDGER.csv
MIGRATION_INTERRUPTION_LEDGER.csv
DIRECTIONAL_TRANSITION_BUFFER_LEDGER.csv
H4_UNRESOLVED_RESOLUTION_LEDGER.csv
H4_AMBIGUOUS_RESOLUTION_LEDGER.csv
H4_H1_MONTHLY_STATE_STRESS_PROFILE.csv
```

Additional research tables include cross-view robustness, state confidence, difficult-month comparison, and ambiguity-resolution summaries.

Exact object geometry remains owned by existing V9 object tooling.

## Immediate next research

Do not add new generic indicators first.

### 1. Route/destination inside the normal cycle

Study:

```text
H4 authority
-> H1 interrupt
-> H1 realign
-> next delivery
-> next meaningful POI/liquidity
```

Goal: identify the natural sequence of transit versus campaign-changing landmarks.

### 2. Parent continuity ledger

Explicitly distinguish:

```text
SAME PARENT / NEXT H1 AUCTION
PARENT AUTHORITY LOST / AUCTION RESET
```

Use H4 authority erosion / neutralization, not one Child outcome or one MSS.

### 3. Exact landmark roles

Attach object IDs and roles:

```text
ORIGIN
TRANSIT
DELIVERY
CAMPAIGN-CHANGING
```

Do not infer coordinates visually.

### 4. Strategy extraction gate

Only when the flow grammar plus route/Parent semantics are compact and reproducible should the project write a strategy-extraction draft.

Then return to causal sequential replay.

## Things the next session must not do

- Do not reopen July.
- Do not touch 2021.
- Do not optimize a rare high-WR subset.
- Do not force unknown states into direction.
- Do not introduce a May-specific rule.
- Do not make indicators/session/ICT patterns mandatory confirmation.
- Do not create fixed event-count/time thresholds from the Atlas.
- Do not optimize Entry/SL/TP yet.
- Do not call answer-sheet statistics validation.
- Do not backfill trades.
- Do not let Child P/L define Parent authority.

## Downstream trading principles remain intact

When strategy extraction begins again:

- Parent/Child separation;
- Hard SL before entry, never widen;
- exact code/runtime coordinates;
- no minimum-R / fixed ATR-S stop/TP rule;
- no cooldown/retry cap/trade quota;
- runtime guards, AI plans/reviews;
- no hindsight rescue.

## 2026-09-12 first strategy-extraction checkpoint

This section is newer than earlier "Immediate next research" text in this file and supersedes it where they conflict.

Frozen consumed-data strategy draft:

`V9_STRATEGY_EXTRACTION_DRAFT_PARENT_CHILD_FLOW_20260912.md`

Active implementation gate:

`V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`

Key checkpoint:

```text
ACTIVE Parent H1 cycles: 171
same-Parent realign:      120
Parent-loss-first:         51

with-Parent M15 reauth:    94
strict pre-H1 counter reauth: 141

semantic runtime research parity:
718 events
missing 0
timestamp mismatch 0
anchor mismatch 0
```

The strategy draft preserves both with-Parent repair/journey participation and Counter-Parent Local-Bridge participation. Parent remains scale/context authority, not a direction veto.

Current next task is implementation/parity, not adding more setup filters.

`2025-07` remains locked; production authority and EA authority remain NONE.


## 2026-09-12 causal state-machine implementation checkpoint

<!-- V9_CAUSAL_STATE_MACHINE_IMPL_20260912 -->

The deterministic implementation gate described by the earlier dual-clock addendum has now passed on consumed data.

Primary checkpoint:

`V9_CAUSAL_STATE_MACHINE_IMPLEMENTATION_CHECKPOINT_20260912.md`

Frozen runtime scripts:

```text
scripts/v9_semantic_runtime.py
scripts/v9_execution_state_machine.py
scripts/v9_strategy_state_machine.py
scripts/v9_runtime_state_v2.py
scripts/validate_v9_causal_state_machine.py
```

Critical runtime distinction:

```text
141 Counter / 94 With-Parent
= cycle-conditioned research statistics

149 Counter / 95 With-Parent
= live-safe first-authorization runtime universe
```

Do not condition the live runtime on future H1-cycle membership.

The runtime now has:

- frozen consumed byte-range isolation tied to the authoritative source hash;
- full same-known-at information-batch barrier before strategy decisions;
- exact M5 `OBJECT_KNOWN_AT` geometry/lifecycle;
- versioned state-v2 checkpoint/resume;
- `run-until-gate -> action -> resume` flow;
- fail-closed execution/reporting for fills, exits, remaps, and cross-lane conflicts;
- deterministic Hard-SL / review / Parent-loss priority tests;
- exact split/restart parity.

Next work is the external AI review/remap packet, scheduler, and maximum-staleness/service-outage policy. Do not reopen setup mining.

`2025-07` remains LOCKED. `2021` remains UNTOUCHED. Production authority and EA authority remain NONE.

## 2026-09-12 validated AI external-decision mechanics

<!-- V9_AI_EXTERNAL_DECISION_VALIDATED_20260912 -->

The AI gate-envelope/scheduler mechanics passed the complete consumed 594-gate replay without changing the accepted gate-driven factual/action ledgers. Actual consumed outage/staleness and REMAP action paths also passed.

2024 tick execution-source audit passed exact M1 OHLC/TICKVOL parity across `344,185` covered minutes.

This does **not** freeze the real discretionary AI semantic path: chart-native MAP attachment + actual AI review instruction/model-role contract remain the next gate. Future-hidden July remains locked.

## 2026-09-13 2024 tick-AI trading / loss postmortem handoff

<!-- V9_2024_LOSS_POSTMORTEM_20260913 -->

2024 GOLD# was replayed causally with historical BID/ASK tick execution and manual chart-native AI decisions. The measured checkpoint was `305` closed trades, `+20.51R`, `33.77%` win rate, and `PF 1.118`.

Because 2024 outcomes have now been opened and used for postmortem research, **2024 is CONSUMED POSTMORTEM DATA from this checkpoint forward**. Do not cite it again as untouched/OOS/future-hidden validation.

Loss decomposition showed:

```text
202 losses total
153 Hard SL
49 AI loss exits
45 fast/no-progress Hard SL (<=60m and MFE<0.25R, postmortem bucket only)
21 Hard SL after MFE>=1R
```

The most important gap is not a new fixed exit rule. `152 / 153` Hard-SL trades ended before an AI semantic review could act. Current research therefore moves to Grammar-driven loss conversion:

```text
ENTRY ARRIVAL / ACCEPTANCE
-> DELIVERY / JOURNEY REVIEW
-> FRESH REAUTH / CAMPAIGN EXHAUSTION
-> branch-specific semantic compression
-> chart-native input + AI model-role freeze
-> consumed causal replay
```

No `M5` mandatory filter, fixed-R management, delivery TP, retry cap, cooldown, or Parent-specific trade cap is authorized.

2024 replay also exposed a runtime REMAP bug. `v9-strategy-state-machine-5` makes `WITH_NEW_PARENT_JOURNEY` use same-direction new-Parent journey damage orientation while preserving the original structural origin. The v5 consumed `2025H1 + 2026JF` 594-gate replay remains byte-identical to the accepted gate-driven ledgers.

Read next:

- `V9_2024_TICK_AI_TRADING_AND_LOSS_POSTMORTEM_CHECKPOINT_20260913.md`
- `V9_NEXT_RESEARCH_CONTRACT_GRAMMAR_LOSS_CONVERSION_20260913.md`

`2025-07` remains LOCKED. `GOLD# 2021` remains untouched.

## 2026-09-13 event-driven AI scheduler handoff update

<!-- V9_EVENT_DRIVEN_AI_SCHEDULER_20260913 -->

Read `V9_EVENT_DRIVEN_AI_ENTRY_AND_POSITION_REVIEW_CHECKPOINT_20260913.md` and `V9_NEXT_RESEARCH_CONTRACT_AI_TRADE_DESIGN_AND_EVENT_SCHEDULER_20260913.md` before resuming research.

Key decisions:

- exploratory ML direction/sentinel track is retired;
- every deterministic entry candidate should receive chart-native AI trade-design review in the next research harness;
- while OPEN, deterministic review events wake AI rather than directly changing the position;
- candidate wake reasons are integer-R progression, first favorable delivery, first post-delivery M15 non-support, and existing structural review/remap;
- 2024 feasibility: 798 minute-batched management calls, 21/21 1R+ giveback losses reached, 0/45 fast/no-progress losses reached post-entry;
- fixed TP / automatic event exits were counterproductive because they cut the long-tail winners;
- Hard SL remains independent and never widened;
- same-batch reasons must be coalesced and pending-request supersession must preserve exact-staleness authority;
- `2025-07` remains LOCKED and `2021` remains untouched.

## 2026-09-13 continuous Grammar -> unified state-action policy handoff

<!-- V9_CONTINUOUS_STATE_ACTION_POLICY_PIVOT_20260913 -->

This section supersedes older immediate-next-work text where it conflicts.

Current phase:

```text
CONTINUOUS GRAMMAR
-> STATE / TRANSITION / ROUTE / POSITION POLICY
-> H1-NATIVE EXECUTION COMPARISON
-> CAUSAL POLICY REPLAY
```

The separate branch supplied important preliminary evidence that the continuous Grammar can remain compact while the first strategy extraction used only a narrow subset of it. Preserve the reported `9-state / 8-transition` result, H1 route-event density, and `WITH_PARENT FIRST` proxy as preliminary evidence only; reproduce them from current `main` before freezing counts.

Do not continue optimizing the existing 45 fast-loss / 21 giveback candidate universe as the top-level research loop. Those studies remain useful counterexamples and scheduler evidence.

Retain all accepted dual-clock, object, Hard-SL, external-action, request-fingerprint, and restart-safety mechanics.

`2025-07` stays LOCKED. `2021` stays UNTOUCHED.

