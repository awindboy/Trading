# EA Development Handoff

Last updated: 2026-08-19
Status: D-135A BUILD 1.91 PREPARED / CANCELED-PENDING LIFECYCLE REGRESSION HOTFIX PENDING LOCAL VALIDATION
Current phase: D-135A — preserve D-135 performance optimization and restore D-134 canceled-pending broker lifecycle
Execution safety: D-134 hedging same-direction add-ons + opposite-direction conflict block + scenario-scoped tickets/positions; D-135 changes indexing/reconciliation/log buffering only

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
-> selected SL protocol; if same-entry multi-Root, use outermost contributor invalidation
-> common pre-frozen objective price / nearest R>=1 TP

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

Phase 4C / Trigger Architecture
→ D-126 build 1.00 REAL-TICK CAUSAL SMOKE PASS
→ AUTHORIZED_SWEEP 11 / AUTHORIZED_SWEEP_POOL 20
→ all D-126 causal invariants PASS; implementation itself behaved as designed
→ D-126 Root-zone reintersection / strategic ownership layer is now HISTORICAL and SUPERSEDED BY D-127
→ D-127 separates M1 sweep detector from scenario sequence
→ M1_SWEEP_DETECTED has no Root/scenario/direction/child/quality gate
→ scenario uses first direction-compatible detected sweep after Root contact
→ Root-contact bar cannot satisfy sweep stage because intrabar order is unknown
→ no Root reintersection requirement
→ no latest-sweep replacement/reference layer
→ STRUCTURAL_REACTION creation remains disabled

Phase 5A M1 CHoCH
→ D-127 build 1.10 REAL-TICK LINEAR-PIPELINE SMOKE PASS
→ M1 STRUCTURE_PROTECTED_BREAK = M1_CHOCH_DETECTED exactly 154 / 154
→ LAST_OPPOSITE_OB baseline: 6 preplanned contacts -> 6 Sweep -> 2 CHoCH
→ FVG_ORIGIN_OB experiment enabled: 36 preplanned contacts -> 33 Sweep -> 18 scenario CHoCH branches
→ those 18 branches map to 9 distinct M1 CHoCH detector events / 10 Sweep→CHoCH bar pairs
→ original baseline scenario rows remain exact subset of experiment-on run
→ no Root-reintersection / sweep-family / sweep-time-reference / child nested trigger gate
→ accepted scenario CHoCH -> WAITING_FVG
→ D-127 validation build itself had FVG/order authorization disabled
→ FVG_ORIGIN_OB is now promoted by D-133 to baseline OB authority; 18 Root branches are still not automatically 18 trades

D-133 integrated execution validation
→ BUILD 1.70 / ROOT_OB_DISTAL_20 January real-tick run PASS
→ 18 finalized Root branches collapsed to 9 unique Entry opportunities
→ contributor merge clusters = 4
→ merged secondary Root branches = 9
→ same-entry ambiguity = 0
→ PENDING accepted = 3 / FILLED = 2 / CLOSED = 2
→ remaining execution NO_TRADE = 6, all old `EXPOSURE_ALREADY_ACCEPTED`
→ those six were complete same-direction opportunities: 2 while earlier pending existed, 4 while earlier filled position existed
→ D-133 same-entry merge / outermost Root SL / common-objective TP implementation PASS
→ profitability inference still NOT valid from two closed trades

D-134 same-direction add-on execution
→ USER APPROVED 2026-08-18
→ user account type = HEDGING
→ same-direction independent Entry/FVG scenarios may coexist as separate pending orders / positions
→ same Entry/FVG still uses D-133 contributor merge and one order
→ opposite-direction pending/position conflict = `OPPOSITE_DIRECTION_EXPOSURE_CONFLICT`
→ simultaneous new LONG+SHORT with no prior exposure = `AMBIGUOUS_SIMULTANEOUS_OPPOSITE_DIRECTION_AUTHORIZATION`
→ old `EXPOSURE_ALREADY_ACCEPTED` same-direction block removed
→ execution reconciliation refactored from one global managed scenario to per-scenario order ticket + POSITION_IDENTIFIER
→ partial-fill residual cancellation may touch only the same original order ticket
→ unresolved cancel-reject / partial-fill residual broker risk blocks all new orders via `EXECUTION_DIVERGENCE_LOCK`
→ non-hedging automated execution fails preflight with `HEDGING_ACCOUNT_REQUIRED_FOR_INDEPENDENT_SCENARIO_POSITIONS`
→ BUILD 1.80 prepared; compile + January real-tick validation pending

Phase 5B / D-128A causal M1 FVG
→ IMPLEMENTED in internal build 1.20 / local validation pending
→ M1_FVG_DETECTED is global detector-only geometry with strict M1 clock continuity
→ scenario eligibility = same direction + FVG available strictly after accepted Sweep + available by CHoCH + no pre-selection retest
→ Candle1 may precede Sweep; FVG must first become available after Sweep
→ unique widest selected after tick normalization
→ exact widest tie = AMBIGUOUS_EXECUTION_FVG / NO_TRADE
→ no candidate = NO_CAUSAL_FRESH_FVG / NO_TRADE
→ selected -> WAITING_EXECUTION_GEOMETRY
→ Entry / SL / Final TP / broker order path remain disabled
→ validate with both FVG_ORIGIN_OB=false and true before D-128B

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

M1 Sweep detector / scenario sequence
→ D-127 DETECT / SEQUENCE separation is current
→ detector uses causally-known liquidity + physical penetration/recovery only
→ scenario checks only Root-contact-before-Sweep and direction
→ Root-zone reintersection / family whitelist / child gate are not current strategy filters

M1 CHoCH detector / scenario sequence
→ existing M1 STRUCTURE_PROTECTED_BREAK is mirrored as M1_CHOCH_DETECTED
→ scenario checks only later-than-Sweep ordering and direction
→ no sweep-time protected-reference freeze or opposite-trend recheck

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
→ D-126 implementation validated but its strategic Root-reintersection ownership is superseded by D-127
→ D-127 linear detector/sequence trigger pipeline is current implementation target
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
→ HEDGING account required for automated execution
→ multiple independent same-direction PENDING/FILLED scenarios allowed
→ same FVG/Entry Roots remain one contributor-merged scenario
→ opposite-direction coexistence blocked
→ unresolved execution divergence blocks all new exposure

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
D-127 local validation
→ verify detector events are scenario-independent
→ verify sequence is strictly Root contact -> Sweep -> later CHoCH
→ inspect simplified funnel counts
→ then implement causal FVG stage
```

## D-127 Recognizer Comparison Checkpoint — 2026-08-16

Same build / same January fixture:

```text
                         LAST_OPPOSITE only   + FVG_ORIGIN experiment
ROOT_CREATED                    19                    108
SCENARIO_PLANNED                13                     78
ROOT_CONTACT_BOUND               6                     36
SCENARIO_SWEEP_ACCEPTED          6                     33
SCENARIO_CHOCH_ACCEPTED          2                     18
distinct accepted CHoCH          2                      9
```

The experiment is additive:

```text
baseline Root identities preserved
baseline scenario rows preserved
generic structure/liquidity/Sweep/CHoCH/map detector streams unchanged
OB_RECOGNITION_MERGED = 34 for same-candle dual recognition
```

Current interpretation:

```text
FVG_ORIGIN_OB causal smoke = PASS
default-strategy promotion = NOT DECIDED
profitability = NOT TESTED
```

Carry both recognizer modes through causal FVG and execution validation before
promoting either interpretation on performance grounds.

## Integrated baseline checkpoint — build 1.50

Current code path now reaches the complete first-position baseline:

```text
Objective / Map
→ pre-existing HTF Root
→ Root contact
→ detected direction-compatible Sweep
→ later detected M1 CHoCH
→ causal fresh widest M1 FVG
→ FVG near-side Entry
→ outward-normalized 20% FVG-width SL
→ frozen objective family nearest-first planned-R>=1 TP
→ same-epoch authorization arbitration
→ Strategy Tester preflight + GTC pending
→ fill or causal pending cancellation
→ broker-history reconciliation
```

Important boundaries:

- live trading hard-blocked; tester orders only.
- no new hidden Sweep/CHoCH/FVG quality gate.
- any `>1` fully-authorized branch in one epoch is explicit `AMBIGUOUS_SIMULTANEOUS_AUTHORIZATION` until provenance-merge semantics are separately frozen.
- already accepted exposure blocks later first-position chains; blocked chains are not delayed.
- before fill only objective / Root / direction authority may cancel.
- after fill source/direction changes do not discretionary-close the position.
- startup with pre-existing symbol+magic exposure requires recovery instead of guessed provenance.

Next action is **one final local validation cycle**, not another implementation split: compile build 1.50, run January `FVG_ORIGIN_OB=false`, then identical `true`, and audit the entire funnel through orders/deals.

## Do Not Do Yet

- Do not optimize parameters.
- Do not add AI runtime dependencies.
- Do not implement FVG add-ons or Delivery FVG replacement until their post-correction contracts are re-audited.
- Do not implement CHoCH+BOS confirmation variant.
- Do not enable live trading.
- Do not treat legacy EA performance as current strategy performance.

## Implementation Checkpoint — D-127 Linear Trigger Pipeline

D-126 build `1.00` validation result:

```text
SCENARIO_PLANNED = 13
SCENARIO_ROOT_CONTACT_BOUND = 6
ROOT_CONTACT_WITHOUT_PREPLAN = 5
AUTHORIZED_SWEEP = 11
AUTHORIZED_SWEEP_POOL = 20
```

All 20 D-126 pool rows satisfied:

```text
pool.available_at < sweep_bar_open
root_intersection=true
same_contact_bar=false
strategy_source_kind=ROOT
child_required=false
```

D-126 is therefore a causal implementation PASS, but D-127 supersedes its
extra strategic Root-ownership filtering.

D-127 target:

```text
mt5/experts/MentorDeterministicV1EA.mq5
internal build = 1.10
phase = D127_LINEAR_TRIGGER_PIPELINE_CORE
```

Active pipeline:

```text
DETECT:
active causally-known liquidity
→ physical M1 penetration + same-bar recovery
→ M1_SWEEP_DETECTED

existing M1 structure detector
→ STRUCTURE_PROTECTED_BREAK
→ M1_CHOCH_DETECTED

SEQUENCE:
preplanned Root
→ Root contact
→ later direction-compatible M1_SWEEP_DETECTED
→ SCENARIO_SWEEP_ACCEPTED / WAITING_CHOCH
→ later same-direction M1_CHOCH_DETECTED
→ SCENARIO_CHOCH_ACCEPTED / WAITING_FVG
```

Explicitly removed:

```text
Root reintersection at Sweep
D-126 strategic family whitelist
latest sweep replacement
sweep-time opposite M1 trend requirement
sweep-time protected reference freeze
separate MEANINGFUL_CHOCH subtype
M5/child trigger gate
```

Still disabled:

```text
causal FVG selection
widest-FVG tie handling
Entry / SL / final TP
orders
```

D-127 smoke should verify:

```text
EA_START build=1.10 / D127_LINEAR_TRIGGER_PIPELINE_CORE
M1_SWEEP_DETECTED > 0
M1_CHOCH_DETECTED > 0
SCENARIO_SWEEP_ACCEPTED > 0
SCENARIO_CHOCH_ACCEPTED > 0 on the January fixture is expected but not hard-coded

for every SCENARIO_SWEEP_ACCEPTED:
root_contact_at <= sweep_bar_open
correct scenario direction side
root_reintersection=false
choch_reference_freeze=false

for every SCENARIO_CHOCH_ACCEPTED:
choch_bar_open > sweep_bar_open
direction matches scenario
state=WAITING_FVG
extra_reference_filter=false
fvg_search_enabled=false
order_authorization=false
```


## D-132 checkpoint — SL invalidation variants + contributor merge

Build 1.50 integrated January A/B real-tick validation is complete enough to move from implementation debugging to two explicit strategy-design experiments.

Observed funnel:

```text
FVG_ORIGIN_OB=false
19 Root -> 13 Plan -> 6 Contact -> 6 Sweep -> 2 CHoCH
-> 2 FVG selected -> 2 pending
-> 1 objective-before-fill cancel + 1 fill/SL close

FVG_ORIGIN_OB=true
108 Root -> 78 Plan -> 36 Contact -> 33 Sweep -> 18 CHoCH
-> 18 FVG selected -> 14 execution NO_TRADE + 4 pending
-> 2 objective-before-fill cancel + 2 fill/close
```

Important interpretation:

- Build 1.50's causal execution chain behaved consistently in the observed branches.
- `FVG_ORIGIN_OB=true` creates many more Root explanations, but several Root branches converge on the exact same downstream FVG / Entry / SL / objective / TP.
- Those duplicate-provenance branches were previously rejected only because D-129 treated any same-epoch branch count `>1` as ambiguity.
- Existing FVG SL is structurally very tight in this sample; therefore planned-R values can become extremely large because the risk denominator is tiny.

User-confirmed mentor principle:

```text
SL = scenario invalidation point
```

D-132 therefore introduces three isolated SL modes while leaving Entry and frozen objective-family mechanics unchanged:

```text
V1_SL_FVG_DISTAL_20   (control)
LONG  = FVG.bottom - 0.20 * FVG.width
SHORT = FVG.top    + 0.20 * FVG.width

V1_SL_SWEEP_EXTREME
LONG  = accepted D-127 Sweep bar low
SHORT = accepted D-127 Sweep bar high

V1_SL_ROOT_OB_DISTAL_20
Root.width = Root.top - Root.bottom
LONG  = Root.bottom - 0.20 * Root.width
SHORT = Root.top    + 0.20 * Root.width
```

All SL prices are normalized outward to `SYMBOL_TRADE_TICK_SIZE`. No ATR/fixed-distance padding is added. Final objective eligibility is recalculated after each SL choice because planned R changes with the risk distance.

Duplicate-provenance contributor merge is also added. Same-epoch fully authorized branches merge only when every executable identity field is identical:

```text
direction
selected_fvg_id
Entry tick
normalized SL tick
final_objective_liquidity_id
TP tick
```

When identical:

```text
multiple Root branches
-> one frozen execution opportunity
-> one implementation master ledger
-> N frozen contributor Root/scenario IDs
-> exactly one broker pending order
```

The implementation master is not a strategically preferred Root. If any executable identity field differs, the existing fail-closed result remains:

```text
AMBIGUOUS_SIMULTANEOUS_AUTHORIZATION
```

Pending survival for a merged opportunity:

```text
common objective remains valid
AND
at least one frozen contributor retains:
    ACTIVE Root
    + valid existing continuation/reversal direction authority
```

If every contributor becomes invalid before fill:

```text
CANCELED_ALL_CONTRIBUTORS_INVALID
```

No contributor may be attached after authorization freeze. On fill, secondary contributor scenario ownership is released and the master position is governed only by frozen server SL/TP; this prevents `MERGED_CONTRIBUTOR` state from blocking later independent scenarios on those Roots.

Target code identity:

```text
mt5/experts/MentorDeterministicV1EA.mq5
internal build = 1.60
phase = D132_SL_VARIANTS_CONTRIBUTOR_MERGE
live execution = hard-blocked
```

Required local validation matrix on the same January real-tick fixture:

```text
1. FVG_ORIGIN_OB=false / V1_SL_FVG_DISTAL_20
2. FVG_ORIGIN_OB=true  / V1_SL_FVG_DISTAL_20
3. FVG_ORIGIN_OB=false / V1_SL_SWEEP_EXTREME
4. FVG_ORIGIN_OB=true  / V1_SL_SWEEP_EXTREME
5. FVG_ORIGIN_OB=false / V1_SL_ROOT_OB_DISTAL_20
6. FVG_ORIGIN_OB=true  / V1_SL_ROOT_OB_DISTAL_20

InpEnableContributorMerge=true for all six runs
```

Validate implementation invariants before profitability:

```text
D-127 upstream detector/sequence counts unchanged within the same recognizer mode
SWEEP_EXTREME uses exactly the accepted Sweep bar extreme
ROOT_OB_DISTAL_20 uses the scenario-frozen Root bounds
outward tick normalization is correct
objective R-eligibility is recomputed from selected SL
identical execution branches merge exactly once
different execution identities remain fail-closed
no new contributor attaches after freeze
merged pending survives while >=1 contributor is alive
merged pending cancels when all contributors are invalid
secondary contributor ownership is released on fill/terminal resolution
historical D-132 one-exposure invariant (SUPERSEDED BY D-134)
```

Profitability/optimization is still out of scope until these invariants pass.

## D-133 checkpoint — FVG-origin OB baseline + same-entry Root contributor scenario

User authority decision on 2026-08-18:

```text
FVG_ORIGIN_OB = accepted baseline OB definition
same FVG / same Entry from multiple Roots = one scenario
```

D-132 January evidence immediately before this decision:

```text
FVG_ORIGIN_OB=true / ROOT_OB_DISTAL_20 / merge=true
108 Root -> 78 Plan -> 36 Contact -> 33 Sweep -> 18 CHoCH -> 18 FVG-selected branches
3 pending / 2 filled / 2 closed / 1 objective-before-fill cancel / divergence 0

FVG_ORIGIN_OB=false / ROOT_OB_DISTAL_20 / merge=true
19 Root -> 13 Plan -> 6 Contact -> 6 Sweep -> 2 CHoCH -> 2 FVG-selected branches
2 pending / 1 filled / 1 closed / 1 objective-before-fill cancel / divergence 0
```

Implementation interpretation:

- Generic M1 Sweep / CHoCH / FVG detector streams remained unchanged between recognizer modes in the tested fixture.
- FVG-origin recognition therefore expands Root provenance rather than rewriting downstream detector facts.
- Root-derived stops showed that same-entry Roots can have different SL values, so D-132's `same SL + same TP` merge identity conflicts with the user's scenario interpretation.

D-133 code target:

```text
build = 1.70
phase = D133_FVG_OB_BASELINE_SAME_ENTRY_ROOT_MERGE

removed inputs:
InpEnableFvgOriginObExperiment
InpEnableContributorMerge

always active:
LAST_OPPOSITE_OB + FVG_ORIGIN_OB
same-entry Root contributor merge
```

Execution-stage order:

```text
FVG selected per Root branch
→ derive common Entry + each contributor's candidate SL
→ same direction + selected_fvg_id + Entry tick identity
→ merge contributors
→ LONG: lowest contributor SL / SHORT: highest contributor SL
→ TP from objective-price intersection frozen by all contributors
→ nearest common reward_ticks >= risk_ticks
→ one pending order
```

True ambiguity remains only when distinct FVG/Entry opportunities complete in the same epoch.

D-133 local validation used the same January real-tick fixture with:

```text
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
```

Expected regression targets from the previous `FVG_ORIGIN_OB=true` Root-SL run:

```text
ROOT_CREATED = 108
SCENARIO_PLANNED = 78
SCENARIO_ROOT_CONTACT_BOUND = 36
SCENARIO_SWEEP_ACCEPTED = 33
SCENARIO_CHOCH_ACCEPTED = 18
SCENARIO_FVG_SELECTED = 18
```

Those upstream branch counts should remain unchanged. Downstream execution counts are expected to change because same-entry Root clusters now collapse into scenario-level opportunities.

D-133 validation checks (PASS on uploaded January run):

```text
EA_START build=1.70 / D133_FVG_OB_BASELINE_SAME_ENTRY_ROOT_MERGE
no FVG-origin experiment toggle in inputs
same-entry clusters emit EXECUTION_OPPORTUNITY_MERGED
SL/TP equality is NOT required for merge
ROOT_OB merged LONG SL = minimum contributor Root SL
ROOT_OB merged SHORT SL = maximum contributor Root SL
FINAL_OBJECTIVE_SELECTED uses common frozen objective price
no common R>=1 price -> NO_COMMON_R_ELIGIBLE_OBJECTIVE
only different FVG/Entry opportunities use AMBIGUOUS_SIMULTANEOUS_AUTHORIZATION
D-133 one-exposure result was historical and is SUPERSEDED BY D-134
pending survives while >=1 contributor authority remains
all contributors invalid -> CANCELED_ALL_CONTRIBUTORS_INVALID
execution divergence = 0 expected
```

D-133 implementation invariants passed on the uploaded January run; profitability judgment remains deferred because the closed-trade sample is too small.

## D-134 Immediate Validation Plan

Run the same January real-tick fixture used for D-133 with:

```text
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
account mode = HEDGING
```

Validate before any profitability comparison:

```text
1. D-127/D-128 upstream detector and scenario counts remain unchanged.
2. 18 Root execution branches still collapse to the same 9 unique Entry opportunities.
3. D-133 same-entry contributor clusters and merged SL/TP geometry remain unchanged.
4. old EXPOSURE_ALREADY_ACCEPTED = 0.
5. the six previously blocked same-direction opportunities are now eligible for independent submission.
6. same-direction pending orders coexist without one being canceled as another scenario's residual.
7. same-direction filled positions have distinct POSITION_IDENTIFIER values and independent SL/TP lifecycle.
8. objective / contributor invalidation cancels only the owning scenario's pending ticket.
9. opposite-direction conflict remains fail-closed.
10. no unrelated same-direction pending is ever canceled as residual volume.
11. any unresolved cancel-reject / residual broker risk activates `EXECUTION_DIVERGENCE_LOCK`.
12. execution divergence = 0 in the normal January fixture.
```

Expected January diagnostic signal, if no unrelated broker preflight constraint intervenes:

```text
same_direction_addon_authorized ≈ 6
opposite_direction_exposure_blocked = 0
```

Do not treat an exact order/fill count as a frozen expectation until the run is inspected, because newly allowed pending/positions can change later execution state and objective-delivery timing.


## D-134 Full-Year 2025 Validation Checkpoint — 2026-08-19

Focused durable test record: `docs/ea/TEST_RESULTS_D134_2025_D135_PERF.md`


Uploaded ledger:

```text
mentor_v1_structure_events(20260818-064307).csv
SHA-256 = 28ab4a4e6c2477989fb2d4b2768006e89c7b396d4508de8d464d41ca3edbc0e4
period = 2025-01-01 ~ 2025-12-31
model = Every tick based on real ticks
build = 1.80
phase = D134_HEDGING_SAME_DIRECTION_ADDON_EXECUTION
SL = ROOT_OB_DISTAL_20
rows ≈ 234,275
reported tester runtime ≈ 9 hours
```

Functional execution result:

```text
unique Entry opportunities = 79
execution geometry ready = 74
pending accepted = 73
filled = 58
closed = 58
TP = 14
SL = 44
pending canceled before fill = 15
order reject = 0
cancel reject = 0
execution divergence = 0
opposite-direction exposure conflict = 1
```

Approximate research-performance summary from the event ledger, using the same provisional GOLD 0.01-lot gross-PnL convention used in analysis and excluding commission/swap:

```text
win rate ≈ 24.1%
gross PnL ≈ +265.64 USD
profit factor ≈ 1.315
realized total ≈ +8.68R
expectancy ≈ +0.15R / filled trade
max closed-trade R drawdown ≈ -21.44R
```

Important research observations, not yet strategy changes:

```text
EXTERNAL_CONTINUATION: 51 fills / 14 TP / about +15.94R
EXTERNAL_REVERSAL:      7 fills / 0 TP / about -7.26R

same-direction add-ons: 20 fills / about +4.20R
max simultaneous filled positions: 4
max accepted exposure observed: 5
```

The full-year run therefore validates D-134 multi-position lifecycle much more broadly than January, but does **not** constitute profitability approval. Reversal weakness and correlated same-direction portfolio exposure remain research items after implementation performance is fixed.

### Performance defect discovered

The full-year run required about 9 hours while January-scale runs had generally completed in under roughly one minute. Progress repeatedly stalled and then jumped.

Static review identified cumulative scans of historical objective/scenario/Root-reaction/execution ledgers plus per-row CSV flushes. The defect is classified:

```text
strategy correctness issue = NO EVIDENCE
execution divergence = 0 in observed run
implementation scalability defect = YES
priority = fix before multi-year testing
```

## D-135 Prepared Build

Target:

```text
build = 1.90
phase = D135_PERFORMANCE_WORKING_SET_OPTIMIZATION
strategy_semantics = D134_UNCHANGED
default CSV = mentor_v1_d135_events.csv
```

Implemented performance changes:

```text
1. frozen objective consumption is propagated on the liquidity-consumption event;
   no objective×scenario polling on every scenario refresh.
2. scenario authority signature no longer concatenates every historical Root tracker;
   Root-reaction state uses a monotonic change version.
3. CancelInvalidScenarioPlans runs only when scenario authority signature changes.
4. Root-contact M1 processing uses WAITING Root indices only.
5. optional child audit uses READY Root indices only.
6. Sweep processing uses WAITING_SWEEP indices only.
7. CHoCH/FVG retention uses WAITING_CHOCH indices only.
8. same-cycle execution authorization uses WAITING_EXECUTION_GEOMETRY indices only.
9. broker reconciliation uses active pending/filled scenario indices only.
10. ordinary ticks do not HistorySelect for an exact pending order / hedging position that is still live.
11. final objective uses a direct frozen-candidate index rather than a whole objective-ledger scan on every tick.
12. active liquidity caches strategy-consumed membership for O(1) M1-overlay checks.
13. CSV flush is batched at 256 rows, with critical execution events and deinit still flushed.
```

### Immediate validation sequence

Do **not** run another full year first.

Run the January real-tick fixture with:

```text
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
hedging account
```

Compare D-135 against the already validated D-134 January baseline.

Required parity:

```text
ROOT_CREATED = 108
SCENARIO_PLANNED = 78
SCENARIO_ROOT_CONTACT_BOUND = 36
SCENARIO_SWEEP_ACCEPTED = 33
SCENARIO_CHOCH_ACCEPTED = 18
SCENARIO_FVG_SELECTED = 18
unique Entry opportunities = 9
same-entry merge clusters = 4
pending accepted = 9
filled = 7
closed = 7
objective-before-fill cancel = 2
exposure-policy NO_TRADE = 0
execution divergence = 0
```

Also compare every unique opportunity's:

```text
selected FVG
Entry
merged SL
Final TP
pending/cancel/fill/close outcome
```

Measure wall-clock runtime. If semantic parity passes and runtime is materially reduced, D-135 becomes the working baseline for longer/multi-year tests. If any strategy/execution result differs, treat D-135 as failed regardless of speed.


## D-135 Full-Year Regression Result + D-135A Hotfix — 2026-08-19

D-135 full-year runtime:

```text
D-134 build 1.80 ≈ 9 hours
D-135 build 1.90 ≈ 6 minutes 10 seconds
speedup ≈ 87.6x
```

The performance objective therefore passed strongly. Long-run strategy geometry also remained stable, but broker pending lifecycle parity did not fully pass.

Observed full-year difference versus D-134:

```text
execution geometry ready: 74 -> 74
filled:                  58 -> 58
closed:                  58 -> 58
pending accepted:        73 -> 72
pending cancel:          15 -> 12
opposite conflict:        1 -> 2
```

Root / Sweep / CHoCH / FVG / Entry / SL / TP remained equivalent for the completed geometry opportunities. The actionable defect was that `strategy_state=CANCELED` scenarios with a still-live broker pending could be removed from the active execution working set before the broker cancel request.

Primary regression fixture:

```text
2025-06-13 02:56 LONG pending
Entry 3388.90 / SL 3330.80 / TP 3499.90
order_ticket = 48

2025-06-16 10:00 Root invalidated
D-134: PENDING_CANCEL_ACCEPTED
D-135: no pending cancel

2025-06-18 17:16 valid SHORT geometry
Entry 3397.25 / SL 3404.81 / TP 3319.20
D-134: independent SHORT order allowed
D-135: blocked by surviving opposite LONG pending
```

Secondary fixture:

```text
2025-11-26 LONG pending
Entry = 4138.03
Root invalidated at 16:30
D-135 omitted broker cancellation after strategy cancellation
```

D-135A build 1.91 changes only `ReconcileScenarioExecution()` working-set retention:

```text
CANCELED + live original pending
-> remain active
-> ManageIntegratedExecution requests exact-ticket cancellation
-> reconcile until broker terminal
-> then remove from active execution set
```

### Immediate validation

Because January does not exercise the discovered bug, the next validation should include at least the June regression window containing `2025-06-13 ~ 2025-06-18`.

Required evidence:

```text
1. build=1.91 / D135A_CANCELED_PENDING_LIFECYCLE_HOTFIX
2. June order ticket corresponding to Entry 3388.90 receives PENDING_CANCEL_ACCEPTED after Root invalidation.
3. June 18 SHORT is no longer falsely blocked by the orphan LONG pending.
4. no new execution divergence.
5. runtime remains close to D-135 performance characteristics.
```

After the focused June regression passes, rerun the full 2025 year and require D-134 execution lifecycle parity with D-135-class runtime.
