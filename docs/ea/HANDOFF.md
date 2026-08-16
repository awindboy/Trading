# EA Development Handoff

Last updated: 2026-08-16
Status: D-124 ROOT-PRIMARY / OPTIONAL-CHILD AUDIT PASS
Current phase: Corrected Phase 4B/4C Root-based scenario and sweep reattachment

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
-> valid Root-reaction liquidity sweep under the re-audited timing contract
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

## Critical Authority Correction — Root Is Primary; Child Is Optional Audit

Current required causal order is:

```text
pre-existing / unconsumed HTF Root
→ actual HTF Root contact
→ valid Root-reaction sweep
→ meaningful M1 CHoCH
→ causal M1 FVG
→ FVG first-retest execution
```

Post-contact LTF child OB is not in the required chain. If one is observed, D-122 still requires it to form/become available after Root contact, but D-124 gives it audit/context authority only.

Consequences:

- No child, multiple children, child ambiguity, or optional-child invalidation does not reject an otherwise valid Root setup.
- The HTF Root remains the strategy source; child never replaces it.
- Entry and SL remain the selected M1 FVG geometry.
- `PREPLAN_SOURCE_CONTACT` and old final-refined-source ownership are obsolete strategy concepts.
- Historical Phase 3B/4B/4C results that depended on mandatory child authority remain audit history only.
- Phase 1.1 structure, Phase 2 physical liquidity detector, Phase 3A Root detector/lifecycle, and Phase 4A map/reversal logic remain valid within their independent scopes.

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
→ OLD PRE-CONTACT IMPLEMENTATION SUPERSEDED BY D-122
→ D122A build 0.80 compiled and ran in Strategy Tester
→ baseline causal validation PASS: Root watch 21 / Root contact 11 / post-contact child 1
→ historical pre-contact child authorization = 0
→ D-124 build 0.81 validation PASS: Root contact 11 / ROOT_CONTEXT_READY 11 / optional child observations 2
→ children_created_strategy_sources = 0; every ready context retained strategy_source_kind=ROOT
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

HTF Root strategy state
→ ACTIVE / INVALIDATED

Root price invalidation
→ adverse body close through Root distal
→ evaluated on Root own timeframe

Wick through Root distal
→ may remain valid sweep/reaction context
→ not automatic Root invalidation

Minimum lower-TF child requirement
→ NONE
→ optional child may be observed only AFTER qualifying HTF Root contact

HTF Root contact
→ REQUIRED
→ activates Root reaction evaluation and optional child audit

Post-contact child observation
→ OPTIONAL audit/context only
→ never required before M1 execution trigger search

Physical sweep geometry
→ same-bar penetration + recovery
→ one-tick minimum
→ Phase 2 audit detector remains valid

Strategic sweep authorization timing
→ REQUIRES D-122 RE-AUDIT
→ DISABLED in D122A
→ exact Root-reaction liquidity-freeze anchor remains unresolved; child is not part of that decision

Active pre-CHoCH sweep/reference
→ old Phase 4C ownership semantics SUPERSEDED pending timing re-audit

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
→ no historical child reconstruction for current setup
→ lower-TF structure may supply causally known state at Root contact
→ optional child audit begins only from future post-contact bars; no strategy authority

M1 bootstrap
→ no historical trigger-tree carry-in
→ current-source ACTIVE local liquidity may be reconstructed

Objective family
→ H1/M30 primary authority first
→ H4 candidate allowed only beyond current H1/M30 directional horizon
→ still one frozen nearest-first family

Execution epoch
→ pre-start CHoCH/FVG/sweep chain cannot authorize runtime order

Startup inside eligible Root
→ no pre-start contact fabrication
→ require Root exit + later closed-M1 re-entry before runtime contact observation

Final authority consistency audit
→ PREVIOUS AUDIT SUPERSEDED IN REFINEMENT/CONTACT ORDER BY D-122

EA_SPEC status
→ AUTHORITY-CORRECTED
→ D122A temporal child-observation implementation validated; D-124 Root-primary semantics prepared
→ Root-based sweep timing / Phase 4B-4C authorization reimplementation still required

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
→ optional runtime child audit begins only after qualifying Root contact

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


## Implementation Checkpoint — D-124 Root-Primary / Optional-Child Consolidation

D122A build `0.80` proved the corrected temporal fact that a logged child can be formed only after actual HTF Root contact.

The 2026-08-16 real-tick test produced:

```text
ROOT_WATCH_CREATED = 21
ROOT_CONTACT_OBSERVED = 11
post-contact child observed = 1
historical pre-contact child authorization = 0
```

D-124 changes the interpretation of those events:

```text
11 Root contacts = 11 Root-level reaction contexts before later strategy filters
1 child = one optional audit observation
missing child = not a rejection
```

Current consolidation target:

```text
mt5/experts/MentorDeterministicV1EA.mq5
internal build = 0.81
phase = D124_ROOT_PRIMARY_OPTIONAL_CHILD_AUDIT_CORE
property version = 1.00
```

Build `0.81` validation boundary:

```text
HTF Root remains strategy source after contact
ROOT_CONTEXT_READY at qualifying Root contact
optional child observations may be logged
optional children are not added as strategy-source objects
child absence / multiplicity / invalidation cannot veto Root context
Entry / SL / TP remain M1-FVG authority
scenario / strategic sweep / CHoCH / order authorization remain disabled for this isolated smoke
```

Expected baseline smoke characteristics for the same January sample:

```text
ROOT_CONTACT_OBSERVED ≈ prior D122A physical-contact count
ROOT_CONTEXT_READY = ROOT_CONTACT_OBSERVED for qualifying runtime contacts
OPTIONAL_CHILD_OBSERVED may be 0..N and does not change Root readiness
children_created_strategy_sources = 0
SCENARIO_PLANNED = 0
old Phase4C SOURCE_CONTACT = 0
AUTHORIZED_SWEEP = 0
orders/deals = 0
```

After build `0.81` compiles and this isolated smoke passes, the next implementation is:

```text
Corrected Phase 4B
→ qualify pre-contact HTF Root against current map / direction / objective
→ keep each distinct valid physical Root as an independent candidate; do not restore arbitrary multi-Root rejection

Corrected Phase 4C
→ attach strategic liquidity/sweep ownership directly to the Root reaction context
→ child identity must not be a required key or gate

then Phase 5A
→ M1 meaningful CHoCH
```

Actual first-position execution remains:

```text
M1 CHoCH causal FVG
→ widest valid FVG
→ first retest
→ FVG Entry
→ FVG distal ± 20% width SL
→ frozen objective TP
```

## Do Not Do Yet

- Do not optimize parameters.
- Do not add AI runtime dependencies.
- Do not implement FVG add-ons or Delivery FVG replacement until their post-correction contracts are re-audited.
- Do not implement CHoCH+BOS confirmation variant.
- Do not enable live trading.
- Do not treat legacy EA performance as current strategy performance.