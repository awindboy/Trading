# EA Development Handoff

Last updated: 2026-08-16
Status: V1 AUTHORITY CORRECTION IN PROGRESS
Current phase: Post-contact LTF child sequencing correction before Phase 4C continuation

## Goal

AI/Gemini/Codex runtime dependency 없이 MT5 Strategy Tester와 향후 실거래 환경에서 독립적으로 실행 가능한 deterministic Mentor EA baseline을 만든다.

## Strategy Authority

최상위 전략 권한은 루트 `AGENTS.md`다.

과거 Python 엔진, legacy EA, Ground Truth, TradingView 전략은 구현 참고자료일 뿐 거래 권한을 갖지 않는다.

## Current Direction

기존 Ground Truth V2는 BLOCKED 상태이며 EA 개발의 선행조건이 아니다.

현재 우선순위:

1. AGENTS.md 규칙을 deterministic specification으로 변환
2. 기존 Python/MQL5 구현과 매핑
3. 최소 baseline EA 구현
4. MT5 Strategy Tester에서 구현 정확성 검증
5. 이후 수익성 평가

## Baseline Scenario

Objective
-> H1/M30 market structure
-> pre-existing eligible / unconsumed HTF root OB
-> actual HTF root OB contact
-> post-contact lower-TF reaction
-> newly formed causal LTF child OB / refinement
-> valid liquidity sweep under the re-audited post-contact timing contract
-> meaningful M1 body-close CHoCH
-> causal fresh FVG in the same sweep-to-CHoCH displacement
-> widest valid FVG
-> first FVG retest
-> LONG: FVG top / SHORT: FVG bottom entry
-> FVG distal ± 20% FVG-width strategy SL
-> frozen objective TP

## Primary References

- `AGENTS.md`
- `research/mentor-youtube/MENTOR_MINIMAL_METHOD.md`
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`
- `research/mentor-youtube/CURRENT_ALGORITHM_REASSESSMENT.md`
- `research/mentor-youtube/EA_TEST_PROTOCOL.md`
- `mentor_engine/`
- `mt5/indicators/ICTCockpitIndicator.mq5`
- `mt5/legacy/MentorScenarioTraderEA.mq5`
- `mt5/legacy/MentorSep2025ParityEA.mq5`

## Critical Authority Correction — Post-Contact LTF Child

The intended causal order is now explicitly frozen as:

```text
pre-existing / unconsumed HTF Root
→ actual HTF Root contact
→ post-contact lower-TF reaction
→ newly formed / confirmed causal child OB
→ post-contact refinement lineage
→ execution-trigger chain
```

The previous implementation searched the Root-forming historical displacement for lower-TF children before price returned to the Root. That temporal ownership is incorrect.

Consequences:

- `PREPLAN_SOURCE_CONTACT` is not a valid strategy rejection merely because HTF Root contact preceded child discovery; Root contact is supposed to start child discovery.
- Phase 3B child/refinement PASS, Phase 4B scenario-planning PASS, and Phase 4C final-source-contact ownership are superseded as strategy-parity evidence and require reimplementation/retest.
- Phase 1.1 structure, Phase 2 liquidity detector, Phase 3A HTF Root detection/lifecycle, and Phase 4A H1/M30 map/reversal logic are not invalidated by this sequencing correction in their independent scopes.
- Do not proceed to Phase 5A until corrected post-contact child ownership and downstream sweep timing are frozen and tested.

## Current Status

Phase 4B Scenario / Objective Family
→ HISTORICAL TEST PASS FOR OLD PRE-CONTACT-CHILD IMPLEMENTATION ONLY
→ STRATEGY-PARITY STATUS SUPERSEDED BY D-122
→ SCENARIO_PLANNED 2 and related counts remain audit history
→ `PREPLAN_SOURCE_CONTACT` rejection semantics are obsolete under corrected ordering
→ objective-family logic itself remains subject to normal regression after scenario-layer rework
→ profitability NOT evaluated

Phase 4A H1/M30 map / reversal permission
→ REAL-TICK EXTENDED TEST PASS
→ owner hierarchy PASS
→ reversal-reference precedence PASS
→ same-bar self-interaction 0
→ permission-origin rewrite 0
→ Phase 1~3B regression PASS

Phase 3B causal LTF refinement
→ SUPERSEDED AS STRATEGY-PARITY TEST BY D-122
→ old CHILD_CREATED 7 / READY 7 were historical children from the Root-forming displacement
→ corrected child must form only after actual HTF Root contact
→ reimplementation and new real-tick validation REQUIRED
→ profitability NOT evaluated

Phase 3A HTF Root OB core
→ IMPLEMENTED
→ uploaded event CSV causal audit PASS within implemented scope
→ Root lifecycle balance PASS
→ session-gap rejection PASS
→ scenario authority remained disabled
→ profitability NOT evaluated

Phase 2 liquidity/sweep
→ IMPLEMENTED
→ uploaded event CSV audit PASS
→ EXTERNAL_SWING / SWEEP / BODY_DELIVERY causal checks PASS
→ H4 external-only invariant PASS
→ Phase 1.1 structure regression PASS
→ profitability NOT evaluated

Phase 1.1 structure/bootstrap
→ IMPLEMENTED
→ Strategy Tester smoke PASS
→ causal log audit PASS
→ profitability NOT evaluated

Phase 1.1 verified runtime
→ GOLD / XMGlobal-MT5 12
→ 2025-01-06 ~ 2025-01-08
→ Every tick based on real ticks
→ 476,672 ticks / 2,758 M1 bars
→ orders/deals 0
→ runtime fatal error 0

Three-candle wave detector
→ FROZEN
→ swing candidate only

Initial trend initialization
→ FROZEN
→ two-sided confirmed range required

Protected swing selection
→ FROZEN
→ BOS-producing causal correction extreme
→ NOT latest opposite swing

External trend invalidation
→ body close through current protected swing

Post-external-CHoCH state
→ TRANSITION
→ no immediate fabricated opposite mature trend

H1/M30 trade-direction authority
→ trend-follow first / FROZEN

Reversal reference
→ bullish H1: current-flow highest valid external high
→ bearish H1: current-flow lowest valid external low

Reversal reference event precedence
→ continuation body break
→ sweep/rejection
→ touch

Opposite M30 while permission CLOSED
→ correction context only

Active V1 first-position scenario scopes
→ EXTERNAL_CONTINUATION
→ EXTERNAL_REVERSAL

Premium / discount (PD Array)
→ CONTEXT / REFERENCE ONLY
→ no standalone scenario authorization or rejection

INTERNAL_ROTATION
→ research-only
→ no current V1 first-position authority

Early EXTERNAL_REVERSAL
→ allowed after HTF reversal permission
→ may occur before H1 trend label flips

Objective family
→ one frozen nearest-first ordered family
→ no historical fallback tier
→ no arbitrary candidate cap

Minimum objective eligibility
→ planned R >= 1

Final TP
→ nearest scope-compatible R-eligible candidate

Post-selection TP rollover
→ FORBIDDEN

Root / child strategy state
→ ACTIVE / INVALIDATED

Source price invalidation
→ adverse body close through distal
→ evaluated on source's own timeframe

Wick through source distal
→ may remain valid sweep context
→ not automatic source invalidation

Minimum one causal lower-TF child
→ REQUIRED
→ must form / become available AFTER qualifying HTF Root contact

HTF Root contact
→ REQUIRED
→ starts lower-TF child discovery

Post-contact child lineage
→ REQUIRED before current setup can authorize M1 execution trigger search

Mature sweep
→ pre-existing eligible liquidity
→ same-bar penetration + recovery
→ one-tick minimum

Active pre-CHoCH sweep/reference
→ one per scenario
→ newer valid sweep replaces active reference

Meaningful M1 CHoCH
→ body-close break of frozen correction protected swing

Same-bar sweep + CHoCH
→ EXCLUDED in V1

INITIAL_CHOCH_FVG
→ FROZEN core entry model

FVG availability
→ Candle3 close

Pre-selection FVG retest
→ candidate excluded

FVG selection
→ widest eligible FVG at CHoCH close

Entry
→ LONG BUY_LIMIT at FVG.top
→ SHORT SELL_LIMIT at FVG.bottom

Strategy SL
→ LONG FVG.bottom - 20% width
→ SHORT FVG.top + 20% width

Pending submission
→ same CHoCH decision cycle after Entry / SL / TP

Pending lifetime
→ ORDER_TIME_GTC

Post-registration FVG mitigation
→ no separate cancellation branch

Pending strategy survival authority
→ final objective validity
→ required source-lineage validity
→ scenario-direction authority

Time-based cancellation
→ NONE

Periodic H1/M15 pending reapproval
→ REMOVED

Bid/Ask execution semantics
→ FROZEN

StopsLevel infeasibility
→ execution failure / NO ORDER
→ strategy geometry not repaired

FreezeLevel cancellation failure
→ execution divergence tracking

Delivery FVG replacement/add-on
→ research-only / inactive

Ground Truth V2 / Gemini runtime state
→ outside deterministic EA baseline

Session boundary
→ no strategy reset / no time-based cancellation

M1 execution FVG session continuity
→ Candle1 / Candle2 / Candle3 must be clock-contiguous M1 bars
→ market-closed gap cannot create INITIAL_CHOCH_FVG

Persistent pending across session
→ requires SYMBOL_EXPIRATION_GTC support
→ requires SYMBOL_ORDER_GTC_MODE == SYMBOL_ORDERS_GTC

Broker daily pending deletion
→ EXECUTION_INFEASIBLE
→ no next-session order recreation

Signal generated while trade session disallows submission
→ EXECUTION_INFEASIBLE / NO ORDER
→ no delayed next-session submission

Gap pending fill
→ actual MT5 DEAL_PRICE
→ strategy geometry remains frozen

Gap SL / TP
→ actual DEAL_REASON + DEAL_PRICE
→ MARKET_GAP_EXECUTION
→ not automatically execution divergence

Session / killzone time filter
→ NOT ADDED

Historical-memory philosophy
→ retain active meaning, not complete historical object trees

H4 role
→ LONG_HORIZON_LIQUIDITY_INDEX only
→ no active direction/source/entry authority

H4 retained archive
→ ACTIVE H4 EXTERNAL_SWING liquidity only

H1/M30 bootstrap
→ reconstruct current active map
→ retain current-owner relevant state only

M30/M15/M5 bootstrap
→ targeted reconstruction for current ACTIVE Root/source only

M1 bootstrap
→ no historical trigger-tree carry-in
→ current-source ACTIVE local liquidity may be reconstructed

Objective family
→ H1/M30 primary authority first
→ H4 candidate allowed only beyond current H1/M30 directional horizon
→ still one frozen nearest-first family

Execution epoch
→ pre-start CHoCH/FVG/sweep chain cannot authorize runtime order

Startup inside source
→ require exit + later re-entry

Final authority consistency audit
→ PREVIOUS AUDIT SUPERSEDED IN REFINEMENT/CONTACT ORDER BY D-122

EA_SPEC status
→ AUTHORITY-CORRECTED; POST-CONTACT CHILD / SWEEP TIMING REIMPLEMENTATION REQUIRED

Source lifecycle
→ ACTIVE / INVALIDATED only
→ no independent full-consumption state

H4 extension
→ EXTERNAL_SWING + timeframe H4
→ beyond H1/M30 horizon only
→ forbidden for old-H1 early EXTERNAL_REVERSAL

Bootstrap Root discovery
→ H1/M30/M15 chronological stream
→ retain current eligible HTF Roots
→ do NOT decompose the Root-forming historical displacement into current children
→ runtime child discovery begins only after qualifying Root contact

Active-memory policy
→ compressed working set
→ resolved history may be file-backed audit only

V1 parity volume
→ MINIMUM_VOLUME_PARITY
→ SYMBOL_VOLUME_MIN

Managed exposure
→ max one accepted PENDING/FILLED first-position exposure per symbol+magic

Execution infeasible/rejected
→ NO_TRADE terminal for that chain
→ no delayed retry

Same-timestamp MTF order
→ H4 → H1 → M30 → M15 → M5 → M1 → authorization

Broker transaction reconciliation
→ ticket/history based
→ callback arrival order not trusted


## Implementation Checkpoint — D-122 Post-Contact Child Correction

The Phase 4C code currently in `MentorDeterministicV1EA.mq5` was built on the old temporal assumption:

```text
Root
→ historical child refinement
→ final refined source frozen
→ source contact
```

Current authority is:

```text
pre-existing eligible HTF Root
→ actual HTF Root contact
→ post-contact LTF reaction
→ newly formed causal child
→ post-contact refinement lineage
```

Therefore:

```text
Phase 3B corrected refinement = NOT IMPLEMENTED
Phase 4B corrected scenario planning = NOT IMPLEMENTED
Phase 4C corrected contact/sweep ownership = NOT IMPLEMENTED
Phase 5A = BLOCKED until the corrected sequence passes
```

The previously implemented physical liquidity/sweep detector and one-tick penetration/recovery geometry are not discarded, but their strategy-authorization timing relative to the new child must be re-audited before reuse.

The uploaded True/False OB experiment tests remain useful only for diagnosing the old implementation behavior. They do not establish current strategy opportunity frequency because both runs used pre-contact child discovery.

Immediate next work:

```text
1. rewrite refinement state machine so HTF Root contact opens child discovery
2. ensure child.available_at > qualifying_root_contact_at
3. remove historical Root-forming-displacement child authorization
4. replace PREPLAN_SOURCE_CONTACT rejection semantics
5. re-audit when eligible sweep-liquidity is frozen relative to the new child
6. rerun Phase 3B / 4B / 4C real-tick validation
7. only then resume Phase 5A
```

## Do Not Do Yet

- Do not optimize parameters.
- Do not add AI runtime dependencies.
- Do not implement FVG add-ons or Delivery FVG replacement until their post-correction contracts are re-audited.
- Do not implement CHoCH+BOS confirmation variant.
- Do not enable live trading.
- Do not treat legacy EA performance as current strategy performance.