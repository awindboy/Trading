# EA Development Handoff

Last updated: 2026-08-16
Status: D-125 CORRECTED PHASE 4B PASS / D-126 PHASE 4C IMPLEMENTED, LOCAL VALIDATION PENDING
Current phase: Root-specific strategic sweep ownership; Phase 5A CHoCH remains disabled

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
→ D-125 build 0.90 REAL-TICK CAUSAL SMOKE PASS
→ SCENARIO_PLANNED 13 / OBJECTIVE_CANDIDATE_FROZEN 91
→ physical Root contact 11
→ strictly preplanned Root contact bound 6
→ contact without prior PLAN 5; retrospective planning 0
→ plan_frozen_at >= root_contact_at violations 0
→ AMBIGUOUS_ROOT_LINEAGE 0 / PREPLAN_SOURCE_CONTACT 0
→ Root remains strategy source; child has no role
→ profitability NOT evaluated

Phase 4C Root-Reaction Strategic Sweep
→ D-126 build 1.00 IMPLEMENTED / LOCAL COMPILE + REAL-TICK VALIDATION PENDING
→ per-M1-open causal eligible-pool snapshot
→ only EXTERNAL_SWING / DEFENDED_RANGE_EDGE
→ LONG LOW-side / SHORT HIGH-side
→ pool.available_at < sweep_bar.open required
→ Root-contact bar excluded in closed-bar baseline
→ sweep M1 bar must intersect owning Root zone
→ multiple pools retained; no best/latest pool selection
→ multiple sweep episodes retained for later Phase 5A linkage
→ STRUCTURAL_REACTION creation disabled
→ meaningful CHoCH / FVG / orders disabled

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
→ D-126 operational contract FROZEN
→ snapshot at each candidate M1 bar open from pre-group causal state
→ Root-contact bar excluded; same-bar ordering not provable from OHLC
→ sweep bar must intersect owning Root zone
→ child is not part of ownership

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
→ required HTF Root validity
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
→ D122A temporal causality validated
→ D-124 Root-primary / optional-child semantics validated
→ D-125 corrected Phase 4B validated
→ D-126 corrected Phase 4C external/defended Root-reaction sweep ownership frozen
→ STRUCTURAL_REACTION remains separate re-audit

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


## Historical Checkpoint — D-125 Corrected Phase 4B (VALIDATED)

D-124 build `0.81` passed the Root-primary / optional-child audit:

```text
ROOT_CONTACT_OBSERVED = 11
ROOT_CONTEXT_READY = 11
optional child observations = 2
strategy-source children = 0
```

Corrected Phase 4B is now prepared as:

```text
mt5/experts/MentorDeterministicV1EA.mq5
internal build = 0.90
phase = D125_ROOT_PRECONTACT_SCENARIO_OBJECTIVE_CORE
property version = 1.00
```

D-125 implementation boundary:

```text
each physical ACTIVE Root = independent scenario candidate
current H1/M30 map / direction / scope qualification
ordered objective family freeze
scenario.frozen_at < Root contact required
Root remains strategy source
optional child remains audit-only
multiple same-map Roots are not collapsed into an ambiguity veto
D-119 M1 consumption overlay may exclude already consumed future objective candidates

Root contact with valid preplan
→ SCENARIO_ROOT_CONTACT_BOUND
→ state = WAITING_SWEEP

Root contact without strictly earlier preplan
→ ROOT_CONTACT_WITHOUT_PREPLAN
→ no retrospective scenario
```

Explicitly disabled in D-125 at that time:

```text
corrected Phase 4C eligible sweep-pool freeze
AUTHORIZED_SWEEP
STRUCTURAL_REACTION strategy ownership
M1 CHoCH authorization
FVG / order submission
```

Required local validation:

```text
1. MetaEditor compile
2. Every tick based on real ticks
3. InpEnableFvgOriginObExperiment = false
4. same January fixture first
5. audit event CSV
```

D-125 PASS requires at minimum:

```text
SCENARIO_PLANNED > 0 on the long sample

every SCENARIO_PLANNED:
    strategy_source_kind = ROOT
    child_required = false
    root_contact_at = NA at freeze

AMBIGUOUS_ROOT_LINEAGE = 0

every SCENARIO_ROOT_CONTACT_BOUND:
    plan_frozen_at < root_contact_at
    root_zone_id == strategy_source_id
    state = WAITING_SWEEP

ROOT_CONTACT_WITHOUT_PREPLAN may be > 0
→ this is not itself a defect
→ it means no valid map/objective PLAN existed strictly before that contact

old Phase4C SOURCE_CONTACT = 0
AUTHORIZED_SWEEP = 0
STRUCTURAL_REACTION strategy authorization = 0
orders/deals = 0
```

After D-125 passes:

```text
Corrected Phase 4C
→ freeze Root-reaction sweep ownership under EA_SPEC 6.6
→ then Phase 5A M1 meaningful CHoCH
```

## Do Not Do Yet

- Do not optimize parameters.
- Do not add AI runtime dependencies.
- Do not implement FVG add-ons or Delivery FVG replacement until their post-correction contracts are re-audited.
- Do not implement CHoCH+BOS confirmation variant.
- Do not enable live trading.
- Do not treat legacy EA performance as current strategy performance.

## Implementation Checkpoint — D-126 Corrected Phase 4C

D-125 validation on build `0.90` produced:

```text
SCENARIO_PLANNED = 13
SCENARIO_ROOT_CONTACT_BOUND = 6
ROOT_CONTACT_WITHOUT_PREPLAN = 5
OBJECTIVE_CANDIDATE_FROZEN = 91
AMBIGUOUS_ROOT_LINEAGE = 0
PREPLAN_SOURCE_CONTACT = 0
```

Corrected Phase 4B is PASS within scope.

D-126 code target:

```text
mt5/experts/MentorDeterministicV1EA.mq5
internal build = 1.00
phase = D126_ROOT_REACTION_SWEEP_CORE
```

D-126 active authority:

```text
preplanned Root contact
→ WAITING_SWEEP

for each later candidate M1 bar:
state carried into close-timestamp group
→ snapshot mature direction-compatible EXTERNAL_SWING / DEFENDED_RANGE_EDGE
→ require pool.available_at < M1 bar open
→ complete M1 bar
→ require physical same-bar sweep
→ require M1 bar intersects Root zone
→ AUTHORIZED_SWEEP_POOL(s)
→ scenario-specific AUTHORIZED_SWEEP episode
→ WAITING_TRIGGER
```

Fail-closed boundaries:

```text
same Root-contact M1 bar = not strategically authorized
STRUCTURAL_REACTION = disabled
child = no role
ATR / point / age / score = none
best/latest sweep selection = none
```

Still disabled:

```text
meaningful M1 CHoCH authorization
sweep→CHoCH episode selection
execution FVG
orders
```

D-126 causal smoke must verify:

```text
AUTHORIZED_SWEEP > 0 on a sufficiently long fixture
every authorized pool available_at < sweep_bar_open
every sweep_bar_open >= root_contact_at
same_contact_bar=false
root_intersection=true
strategy_source_kind=ROOT
child_required=false
family in {EXTERNAL_SWING, DEFENDED_RANGE_EDGE}
direction side compatible
STRUCTURAL_REACTION_CREATED=0
orders/deals=0
```
