# V9 Decision Authority — Continuous Market-Flow Grammar First

Date: `2026-09-12`
Status: `ACTIVE V9 DECISION AUTHORITY`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## Current decision

Continue the Market Flow Atlas phase.

Do not return to trade-by-trade optimization yet.
Do not search for a rare high-win-rate setup as the research target.

Current order:

```text
continuous hierarchical grammar
-> route / destination semantics
-> Parent continuity / authority-loss semantics
-> strategy extraction draft
-> causal sequential replay
-> live runtime design
-> future-hidden replay
```

## Current market representation

Use the smallest current hierarchy:

```text
H4 AUTHORITY
  STRONG DIRECTIONAL / WEAK DIRECTIONAL / NEUTRAL

H4 PHASE
  MIGRATION / LOCAL_INTERRUPT / NEUTRAL

H1 AUCTION
  ALIGNED / H1_INTERRUPT

UNCERTAINTY
  UNRESOLVED / AMBIGUOUS

LANDMARKS
  exact POI / FVG / OB / liquidity objects
```

Do not create a new strategy branch for every descriptive subtype.

## Why confidence is explicit

When the three causal H4 state views agree strongly, H1 interruptions usually behave differently from interruptions under weak/disputed H4 authority.

Therefore:

> lack of consensus is information.

Do not add a tiebreaker indicator merely to eliminate WEAK / UNRESOLVED / AMBIGUOUS states.

## Object decision

Code owns exact object geometry and lifecycle.

AI may later assign strategic roles such as:

```text
ORIGIN
TRANSIT
DELIVERY
CAMPAIGN-CHANGING
RETIRED
```

Object existence does not imply strategic importance.

## Difficult-period decision

2025-05 is not a special regime that requires its own rule.
It is represented by more weak H4 authority, more interruption, more neutralization/side-change activity, and slower nested-auction resolution.

Do not create month-specific exceptions.

## Ambiguity decision

Keep `AMBIGUOUS` as a first-class state.

2025 consumed ambiguous episodes split 11 / 11 between same-direction and opposite-direction next migration.

Do not force a directional answer where the current representation has none.

## Research boundary decision

Use information-known time, not source-bar date, as the strict boundary.

```text
2025 known_at < 2025-07-01 00:00
2026 Jan-Feb known_at < 2026-03-01 00:00
```

No July warmup.
No Dec-2025 warmup for Jan-2026.
No 2021.

## Retired active research directions

Do not continue stacking:

- session label alone;
- generic London/NY sweep-reclaim-body-break;
- generic MSS;
- generic fresh-FVG confirmation;
- breaker/inversion automatic role flip;
- premium/discount alone;
- MACD/Bollinger confirmation;
- fixed sweep counts;
- rare repair-resumption subsets;
- fixed duration/event-count rules.

If one of these is ever reopened, it must add new explanatory power to the continuous grammar, not merely fit a few examples.

## Research-quality decision

Prefer:

```text
many hours / many cycles explained by few states
```

over:

```text
few historical examples with very high conditional percentages
```

Always preserve counterexamples and explicit unresolved remainder.

## Retained absolute trading rules for downstream work

When trading research resumes:

- Parent/Child separation remains mandatory.
- Parent is not a direction veto.
- Hard SL is fixed before entry and never widened.
- exact Entry/SL/TP/review coordinates come from code/runtime.
- no fixed minimum-R rule.
- no fixed ATR/S stop or TP rule.
- no cooldown.
- no retry cap.
- no fixed no-chase rule.
- no forced LONG/SHORT balance.
- no fixed minimum trades/day.
- no mandatory ICT pattern chain.
- Child outcome does not automatically validate/invalidate Parent.
- no hindsight rescue/backfill.
- winner participation remains important when the journey stays coherent.

## 2026-09-12 strategy-extraction decision update

This is the newer decision sequence and supersedes earlier "Current order" text where they conflict.

The continuous hierarchy and Parent/route semantics are sufficiently stable for a first strategy-extraction freeze.

Current order is now:

```text
continuous hierarchy / route semantics
-> first strategy-extraction draft FROZEN
-> dual-clock runtime implementation
-> M15/M5 information-known object timing
-> consumed-period sequential replay through actual implementation
-> freeze implementation version + hashes
-> decide whether future-hidden replay gate is satisfied
```

Do not return to trade-by-trade rule mining during this implementation phase.

Retain:

- with-Parent repair / continuation Child branch;
- Counter-Parent Local-Bridge Child branch;
- Parent/Child separation;
- Parent is not a direction veto;
- structural origin falsification before risk;
- M5 as execution geometry rather than direction authority;
- H1 launch anchor as journey/bridge review structure;
- completed M15 close beyond launch anchor as material Child-damage evidence, not automatic Parent death;
- delivery and counter landmarks as progression/review context, not automatic TP/exit;
- fresh objective reauthorization may create a new independent Child; stopped Child is never rescued.

`2025-07` remains locked.


## 2026-09-12 causal implementation decision update

<!-- V9_CAUSAL_STATE_MACHINE_IMPL_20260912 -->

The deterministic consumed-data implementation mechanics gate is accepted.

Retain these implementation decisions:

- strategy-time H1 role is `ALIGNED` versus `INTERRUPT`; internal `COUNTERFLOW <-> LOCAL_BALANCE` changes do not restart Child context;
- Atlas `>2h` gap segmentation is research bookkeeping, not a trade timeout or Child invalidation;
- full same-known-at information batches complete before strategy authorization is resolved;
- semantic gate time is not execution-price authority;
- zone touch requires execution reporting rather than invented fill;
- completed M15 launch-anchor damage creates review authority, not an automatic stale-price exit;
- Hard-SL / structural origin has deterministic priority over discretionary review;
- Parent loss cancels pre-fill Child or requires remap of an alive paid Child; it does not fabricate a Child result;
- cross-lane hedge/netting/replacement is not frozen and therefore remains fail-closed review;
- simultaneous opposite authorization receives no code-order priority;
- live-safe first authorization counts are `149 Counter / 95 With-Parent`; `141 / 94` remain cycle-conditioned research statistics only;
- hidden-safe normal runtime uses the frozen consumed byte-range manifest and does not discover hidden ranges by scanning the strategy source.

Current order:

```text
accepted deterministic causal mechanics
-> freeze AI review/remap packet
-> freeze scheduler + max-staleness/service-outage behavior
-> consumed causal external-decision dry-run
-> freeze implementation/packet/scheduler commit + hashes
-> explicit future-hidden gate decision
```

`2025-07` remains LOCKED.

## 2026-09-12 validated AI external-decision decision update

<!-- V9_AI_EXTERNAL_DECISION_VALIDATED_20260912 -->

Retain:

- `REVIEW_REQUIRED` / `REMAP_REQUIRED` are the only AI semantic gates in the current runtime;
- entry/exit fill reports remain execution-adapter authority;
- cross-lane conflict remains deterministic fail-closed `SKIP_NEW_PITCH`;
- AI response staleness is exact causal-structure mismatch, not an elapsed-minute threshold;
- AI outage creates no implicit HOLD/EXIT/REMAP and no new risk;
- the Hard-SL structural origin remains authoritative during review/remap/outage;
- 2024 tick data is execution validation only and cannot retune strategy grammar.

The packet/scheduler mechanics gate has passed. Future-hidden replay is still blocked until chart-native AI semantic input and the actual AI review instruction/model-role contract are frozen and consumed-tested.

## 2026-09-13 2024 loss-postmortem decision update

<!-- V9_2024_LOSS_POSTMORTEM_20260913 -->

Decision:

```text
2024 causal replay result = useful research checkpoint
2024 future validation status = RETIRED / now consumed
new strategy rule authority = NONE
v9-strategy-state-machine-5 REMAP bugfix = ACCEPTED after exact consumed parity
2025-07 = LOCKED
2021 = UNTOUCHED
```

Do not promote the following descriptive 2024 differences into mechanical rules:

- M5 side agreement;
- +1R/+2R/+3R buckets;
- favorable liquidity delivery;
- post-delivery M15 non-support;
- FIRST versus FRESH_REAUTH aggregate P/L;
- repeated losses inside one Parent.

The active research decision is to improve **Grammar interpretation**, not add thresholds. Study entry acceptance, delivery meaning, and campaign exhaustion using paired loss/winner charts and causal state/object context. Only after compact semantics are supported may any new AI scheduler gate be proposed and consumed-tested.

## 2026-09-13 event-driven AI entry / position-review decision update

<!-- V9_EVENT_DRIVEN_AI_SCHEDULER_20260913 -->

Decision:

```text
exploratory ML direction/scheduler track = RETIRED
deterministic strategy authorization       = candidate generation for next research
entry candidate                            = AI trade-design review required in research harness
management events                          = AI wake reasons only
automatic event action                     = NONE
Hard SL                                    = unchanged / independent / never widened
2025-07                                    = LOCKED
2021                                       = UNTOUCHED
```

Consumed 2024 feasibility supports simple deterministic scheduling without ML. Candidate review reasons are positive integer-R first crossings, first favorable liquidity delivery, first post-delivery M15 non-support, plus the existing structural REVIEW/REMAP reasons.

Do not interpret R milestones as minimum-R, TP, BE, or trailing authority. Do not interpret delivery or M15 non-support as automatic exit. Counterfactuals show those automatic rules cut more winner value than they save.

The exact entry action schema, chart packet, prompt/model role, event-packet version, and pending-request supersession mechanics remain unfrozen and require consumed causal testing.

## 2026-09-13 continuous Grammar state-action policy decision update

<!-- V9_CONTINUOUS_STATE_ACTION_POLICY_PIVOT_20260913 -->

Decision:

```text
active top-level research frame = CONTINUOUS STATE-ACTION POLICY
setup-centric COUNTER/WITH_PARENT optimization = SUBORDINATE / BASELINE
event-driven R/delivery scheduler = DOWNSTREAM INFRASTRUCTURE / REVIEW CANDIDATE
H1-native execution = HIGH-PRIORITY COMPARISON HYPOTHESIS
M15/M5 deletion = NOT AUTHORIZED
ML = RETIRED FROM ACTIVE PATH
2025-07 = LOCKED
2021 = UNTOUCHED
```

The separate research branch suggests that the Grammar may be compact enough to support a unified policy and that lower-timeframe reauthorization may fragment larger H1 theses. These are research motivations, not automatic rules.

The project must first reproduce the branch evidence on current `main`, then build a causal `State + Transition + Route + Position -> Action` ledger over consumed 2025H1 + 2026JF.

Do not convert state base rates into deterministic direction, do not impose one-trade-per-H1-cycle, and do not remove M15/M5 before controlled H1-native A/B/C comparison.

