# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-13`
Status: `ACTIVE / CONTINUOUS HIERARCHICAL MARKET-FLOW GRAMMAR`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed answer-sheet data: `2025-01 through 2025-06`, `2026-01 through 2026-02`
Consumed postmortem data: `2024-01 through 2024-12` (`tick-AI causal replay`; no longer OOS/future-hidden)
Future-hidden: `2025-07 LOCKED`
Untouched final reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Resume order

Always begin by checking latest GitHub `main` HEAD.

Read in this order:

1. `docs/ea/v9/AGENTS_V9.md`
2. `docs/ea/v9/HANDOFF_V9.md`
3. `docs/ea/v9/RESEARCH_STATE_V9.md`
4. `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
5. `docs/ea/v9/DECISIONS_V9_POSTJUNE_SIMPLIFICATION_AND_RUNTIME_ADDENDUM_20260910.md`
6. `docs/ea/v9/V9_MARKET_FLOW_ATLAS_AND_REVERSE_ENGINEERING_CONTRACT_20260911.md`
7. `docs/ea/v9/V9_MARKET_FLOW_GRAMMAR_CONTINUOUS_HIERARCHY_AUTHORITY_20260912.md`
8. `docs/ea/v9/V9_STRATEGY_EXTRACTION_DRAFT_PARENT_CHILD_FLOW_20260912.md`
9. `docs/ea/v9/V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`
10. `docs/ea/v9/V9_CAUSAL_STATE_MACHINE_IMPLEMENTATION_CHECKPOINT_20260912.md`
11. `docs/ea/v9/V9_AI_REVIEW_REMAP_PACKET_AND_SCHEDULER_PROTOCOL_20260912.md`
12. `docs/ea/v9/V9_AI_EXTERNAL_DECISION_AND_2024_TICK_VALIDATION_CHECKPOINT_20260912.md`
13. `docs/ea/v9/V9_2024_TICK_AI_TRADING_AND_LOSS_POSTMORTEM_CHECKPOINT_20260913.md`
14. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_GRAMMAR_LOSS_CONVERSION_20260913.md`
15. `docs/ea/v9/results/V9_MARKET_FLOW_ATLAS_MASTER_LEDGER_20260912.md`
16. `docs/ea/v9/results/V9_MARKET_FLOW_GRAMMAR_RESEARCH_CHRONICLE_20260912.md`
17. `docs/ea/v9/results/V9_DIFFICULT_MONTH_AND_AMBIGUITY_RESOLUTION_STUDY_20260912.md`
18. `docs/ea/v9/V9_CHART_NATIVE_ICT_OBJECT_AND_MTF_PIPELINE_20260910.md`
19. `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
20. `docs/ea/v9/V9_DISCRETIONARY_TRADING_PIPELINE_POSTJUNE_20260910.md`
21. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_POSTJUN_EXECUTION_RUNTIME_20260910.md` (historical; newer contract wins where conflicting)
22. current code/tool parity state.

If older postmortems/pipeline documents conflict with the current Market Flow Grammar authority, the current authority wins.

## Current research identity

Do not optimize individual trades now.

Research the continuous nested process:

```text
H4 MACRO AUTHORITY
-> H4 PHASE
-> H1 AUCTION
-> POI / LIQUIDITY LANDMARK
-> RESOLUTION
-> NEXT STATE
```

Current core labels:

```text
H4 AUTHORITY
STRONG DIRECTIONAL / WEAK DIRECTIONAL / NEUTRAL

H4 PHASE
MIGRATION / LOCAL_INTERRUPT / NEUTRAL

H1 ROLE
ALIGNED / H1_INTERRUPT

UNCERTAINTY
UNRESOLVED / AMBIGUOUS
```

Do not force uncertainty into a direction.

## Current evidence to remember

Strict final ledgers after in-period warmup:

- H1 nested interruption cycles: `145` in 2025 Jan-Jun, `41` in 2026 Jan-Feb.
- H1 realigns with the slower H4 side before H4 side change in roughly `76.6% / 78.0%` of consensus cycles. This is descriptive topology, not a trade win rate.
- H4 migration interruption episodes: `66 / 17` under strict final information-known boundaries.
- Actual directional side changes: `33 / 8`.
- Direct clean flips are uncommon; side changes usually travel through an interruption / neutralization buffer.
- 2025-05 is explained by weaker H4 authority, more interruption, and more real side change; do not create a May-specific exception.
- 2025 `AMBIGUOUS` episodes resolved 11 same-direction and 11 opposite-direction next migrations. Do not invent a tiebreaker.

## Critical boundary rule

The information-known timestamp is authoritative.

```text
2025 state/event known_at < 2025-07-01 00:00
2026 Jan-Feb state/event known_at < 2026-03-01 00:00
```

Do not use July as warmup.
Do not use Dec-2025 as warmup for Jan-2026.
Do not use the 2021 reserve.

A previous working ledger retained one June-source bar known exactly at July 1 00:00. The final scripts remove it. Do not reintroduce it.

## Object authority

Code owns exact candidate geometry / lifecycle for:

- FVG;
- OB candidate;
- swing/liquidity candidate.

AI may assign semantic roles, but object existence is not strategy importance.

Keep separate:

```text
GEOMETRIC LIFECYCLE
STRATEGIC / CAMPAIGN ROLE
```

POI / liquidity are landmarks inside the state process.

## Current research method

Use consumed data as answer-sheet research.
Full future-visible analysis is allowed only inside consumed periods.

Research sequence:

```text
continuous coverage
-> state transitions
-> difficult periods / counterexamples
-> robustness across alternate causal state views
-> landmark roles
-> route / destination semantics
-> Parent-continuity semantics
-> strategy extraction
-> causal sequential replay
```

Prefer compression over fit.

Do not explain every move with a different pattern.
Do not optimize one state definition for maximum historical accuracy.

## Strategy-extraction checkpoint — 2026-09-12

The first consumed-data strategy-extraction draft is now frozen for implementation testing.

Current descriptive hierarchy:

```text
ACTIVE-Parent H1 cycles: 171
  SAME_PARENT_REALIGN: 120
  PARENT_LOSS_FIRST:    51

first with-Parent M15 reauthorization (cycle-conditioned research): 94
live-safe first with-Parent runtime authorization: 95
strict fresh counter M15 reauthorization before H1 interrupt (cycle-conditioned research): 141
live-safe first Counter runtime authorization: 149

same-Parent post-realign routes:
  launch anchor no-touch:             63
  touch without M15 close damage:     26
  completed M15 close damage:         31
```

The raw-M1 dual-clock research prototype reproduced `718` frozen semantic events with zero missing events, zero timestamp mismatch, and zero anchor-price mismatch.

This is consumed-data reproducibility, not future edge.

`2025-07` remains locked.

## Causal state-machine implementation checkpoint — 2026-09-12

<!-- V9_CAUSAL_STATE_MACHINE_IMPL_20260912 -->

The deterministic consumed-data causal mechanics gate has passed.

Read:

`docs/ea/v9/V9_CAUSAL_STATE_MACHINE_IMPLEMENTATION_CHECKPOINT_20260912.md`

Key implementation facts:

```text
revealed consumed M1 rows: 229,861
future-hidden July-Dec rows revealed: 0
semantic events: 4,254
M5 OBJECT_KNOWN candidates: 27,899
live-safe first Counter authorizations: 149
live-safe first With-Parent authorizations: 95
split/resume parity: exact
external-action restart parity: exact
gate-driven mechanical replay: PASS
```

This is implementation causality, not future edge. Production authority and EA authority remain NONE.

`2025-07` remains LOCKED.

## What to research next

Do not open July and do not turn the 2024 postmortem into fixed filters.

2024 is now consumed postmortem data. The next research target is **Grammar-driven loss conversion while preserving large winners**.

Current order:

1. `ENTRY ARRIVAL / ACCEPTANCE`: paired chart study of fast/no-progress losses versus robust winners. Determine whether price actually accepts the Child side at the execution location; do not convert M5 consensus into a mandatory gate.
2. `DELIVERY / JOURNEY REVIEW`: compare +1R-or-more giveback losses with large winners after favorable liquidity/landmark delivery. Delivery is a review-context candidate, not TP/trailing authority.
3. `FRESH REAUTH / CAMPAIGN EXHAUSTION`: distinguish genuinely new auction/route information from repeated oscillation inside an exhausted Parent campaign; no retry count/cooldown.
4. compress branch-specific semantics for `COUNTER Local-Bridge` and `WITH_PARENT repair/continuation`.
5. freeze the causal chart-native attachment and AI model-role/prompt only after those paired studies.
6. if evidence supports new `ENTRY_CONTEXT_REVIEW` or `DELIVERY/PROGRESSION_REVIEW` events, implement them as research-only candidates and replay all consumed data.
7. freeze implementation/packet/chart/prompt/model-role versions and hashes.
8. only then explicitly decide again whether future-hidden `2025-07` can be unlocked.

The current future-hidden gate decision is `NOT SATISFIED`.

2024 must never again be cited as untouched/OOS validation after this postmortem.

## Do not do

Do not:

- open July or 2021;
- search for rare 90% setups as the research target;
- use early answer-sheet acceptance/rejection percentages as forward alpha;
- use the old hindsight-selected ~94% balance accepted-probe result as authority;
- force `AMBIGUOUS` into UP/DOWN;
- make session / MACD / Bollinger / PD-array / generic MSS / generic FVG chain mandatory;
- create fixed sweep counts, duration thresholds, cooldowns, retry caps, minimum-R, fixed no-chase, or trade/day quotas;
- optimize Entry/SL/TP before strategy extraction;
- let one Child result rewrite the Parent;
- rescue a stopped Child with future movement;
- change authority from one/two examples.

## Trading rules retained for downstream work

When trading research resumes:

- Parent and Child remain separate.
- Parent is not a direction veto.
- Hard SL is fixed before entry and never widened.
- Exact executable prices come from code/runtime, not visual guesswork.
- Parent-Journey may use `FIXED TP = NONE` if route/review conditions are known.
- Do not require minimum-R or fixed ATR/S targets.
- AI plans; runtime waits/guards.
- no hindsight backfill or rescue.

## 2026-09-12 AI external-decision validation checkpoint

<!-- V9_AI_EXTERNAL_DECISION_VALIDATED_20260912 -->

Validated on the unchanged frozen causal core:

```text
594 gate-driven segments
109 AI semantic requests
229,861 revealed consumed M1 rows
0 pending gates at end
combined mechanical-baseline ledger parity: exact
actual outage/stale-response safety: PASS
actual REMAP action path: PASS
2024 tick -> M1 OHLC/TICKVOL parity: 0 mismatches across 344,185 minutes
```

The validated v1 AI request is the deterministic causal **gate envelope**. It does not yet freeze the chart-native MAP attachment or the actual AI semantic decision instruction/model role. Because chart images remain primary AI semantic input under current tooling authority, synthetic EXIT decisions cannot authorize hidden strategy validation.

`2025-07` remains LOCKED.

## 2026-09-13 2024 tick-AI trading / loss postmortem checkpoint

<!-- V9_2024_LOSS_POSTMORTEM_20260913 -->

```text
2024 closed trades            305
2024 total R               +20.51R
2024 profit factor           1.118
2024 losses                   202
Hard SL                       153
AI loss exits                  49
fast/no-progress Hard SL       45
MFE>=1R then Hard SL           21
strategy runtime              v9-strategy-state-machine-5
consumed 594-gate parity      PASS / exact hashes
```

No new strategy threshold is authorized. The current research contract is `V9_NEXT_RESEARCH_CONTRACT_GRAMMAR_LOSS_CONVERSION_20260913.md`.

`2025-07` remains LOCKED; `2021` remains untouched.
