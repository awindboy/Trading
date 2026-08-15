# EA Development Handoff

Last updated: 2026-08-16
Status: V1 SPECIFICATION FROZEN
Current phase: Phase 3B causal LTF OB refinement implementation

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
-> pre-existing HTF root OB
-> causal LTF OB refinement
-> refined OB touch
-> pre-existing liquidity sweep
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

## Current Status

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

Source contact
→ REQUIRED before trigger search

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
→ COMPLETE

EA_SPEC status
→ FROZEN FOR V1 IMPLEMENTATION

Source lifecycle
→ ACTIVE / INVALIDATED only
→ no independent full-consumption state

H4 extension
→ EXTERNAL_SWING + timeframe H4
→ beyond H1/M30 horizon only
→ forbidden for old-H1 early EXTERNAL_REVERSAL

Bootstrap Root discovery
→ H1/M30/M15 chronological stream
→ targeted child refinement afterward

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


## Implementation Checkpoint — Phase 3B Causal LTF OB Refinement

Phase 3A Root core smoke test is complete.

Verified Phase 3A runtime:

```text
ROOT_CREATED      = 2
ROOT_INVALIDATED  = 3
ROOT_REJECTED     = 16

Root causal-rule violations = 0
Phase 1 structure regression = 0
Phase 2 liquidity regression = 0
```

Full bootstrap + runtime Root lifecycle:

```text
created = 272
price invalidated = 161
structure invalidated = 110
active at stop = 1

161 + 110 + 1 = 272
```

Known Root coverage limitation:

```text
Independent completeness enumeration for every
"structurally meaningful internal swing" Root context
is not yet audited/complete.

Therefore the full Root-spec backlog item stays open.
```

Phase 3B code status:

- Phase: `REFINEMENT_CORE`
- Internal build: `0.40`
- MQL property version: `1.00`
- Orders: intentionally disabled
- Scenario authority: intentionally disabled
- Source contact: not yet active
- Phase 3B compile: PENDING LOCAL METAEDITOR
- Phase 3B short smoke: NO_CHILD path PASS / child path NOT COVERED

Short smoke result:

```text
REFINEMENT_FROZEN = 4
NO_CHILD = 4
CHILD_CREATED = 0
REFINEMENT_READY = 0

NO_CHILD causal path = PASS
child creation path = NOT COVERED
Phase 3B final status = COVERAGE INCOMPLETE
```

No frozen rule is relaxed based only on missing short-window child coverage.

Implemented in Phase 3B:

### Targeted refinement only

Historical bootstrap does not build a global M5 source tree.

Order:

```text
H1/M30/M15 Root discovery
→ retain current ACTIVE Roots
→ targeted lower-TF reconstruction only for those Roots
```

Runtime Root refinement is also queued until every
same-`available_at` timeframe close has been processed:

```text
H4
→ H1
→ M30
→ M15
→ M5
→ M1
→ refinement freeze
```

This prevents a higher-TF Root close from reading
same-timestamp lower-TF information before the frozen scheduler order permits it.

### Allowed child timeframes

```text
M30
M15
M5
```

A child must be lower than its direct parent.

M1 is never used for source refinement.

### Recursive causal child logic

Each child must independently satisfy:

```text
meaningful lower-TF swing-origin context
+
last opposite candle in child origin window
+
same direction as parent
+
lower-TF body-close structure delivery
+
causal timing inside parent event
```

### Time causality

Required:

```text
parent origin
<= child origin
<= child structure confirmation
<= parent linked structure confirmation
```

Child origin must also belong to the parent causal swing-origin window.

### Containment

Preferred:

```text
CONTAINED

parent.bottom <= child.bottom
AND
child.top <= parent.top
```

If not fully contained, Phase 3B allows only:

```text
EVENT_ADJACENT
```

defined by parent-event time lineage and same directional delivery.

No fixed-point, ATR, percentage, or RR adjacency tolerance is used.

### Ambiguity

For each lower timeframe, child candidates are causally deduplicated.

If multiple comparable-authority candidates remain:

First child stage:

```text
AMBIGUOUS_FIRST
→ no final child
→ no first-position source authority
```

After a higher child already exists:

```text
STOPPED_AMBIGUOUS
→ keep the already selected higher child
→ do not choose nearest/narrowest/newest candidate
```

### Deepest unambiguous child

If exactly one valid child is found:

```text
select child
→ use it as direct parent
→ continue to the next allowed lower timeframe
```

Final child is the deepest unambiguous causal child.

Refinement is not forced to M5.

### Snapshot validity vs ambiguity

Ambiguity is determined at the Root/refinement freeze time.

A child that was one of multiple causal candidates at freeze time
cannot later disappear by invalidation and retrospectively
make the older ambiguous decision unambiguous.

Current snapshot validity is evaluated only after
the causal candidate set has been frozen.

### Child strategy lifecycle

```text
ACTIVE
INVALIDATED
```

only.

Bullish child:

```text
child-own-TF close < child.bottom
→ PRICE_INVALIDATED
```

Bearish child:

```text
child-own-TF close > child.top
→ PRICE_INVALIDATED
```

Parent invalidation propagates to all descendants.

### Lineage identity

Each retained child stores:

```text
parent_zone_id
root_zone_id
origin_wave_id
linked_structure_event_id
containment_type
occurred_at
available_at
```

### Scenario authority

Even a valid final refined child remains:

```text
scenario_owner_id = UNBOUND
scenario_authority = false
```

until map/objective/scenario binding is implemented.

### STRUCTURAL_REACTION

Still intentionally dormant in Phase 3B.

Reason:

```text
Root/child ownership is now established,
but safe structural-reaction creation also needs
refined-source reaction/contact replay.

No shortcut is introduced merely because a child exists.
```

Activation is deferred to the source-reaction/contact checkpoint.

Not implemented yet:

- full Root completeness audit for structurally meaningful internal-swing contexts
- scenario direction/objective binding
- source contact
- scenario-specific mature sweep authorization
- STRUCTURAL_REACTION creation
- meaningful M1 CHoCH binding
- execution FVG
- Entry / SL / TP
- pending order execution/cancellation
- OnTradeTransaction reconciliation

## Next Task

1. Keep Phase 3B build 0.40 unchanged.
2. Run extended real-tick coverage: `2025-01-06 ~ 2025-02-01`.
3. Require at least one `CHILD_CREATED` before final Phase 3B PASS.
4. If the extended run still produces zero children, add candidate-rejection diagnostics before changing any causal rule.
5. Do not begin scenario/source-contact implementation until child creation lineage is actually log-verified.

## Do Not Do Yet

- Do not optimize parameters.
- Do not add AI runtime dependencies.
- Do not implement FVG add-ons or Delivery FVG replacement until their post-correction contracts are re-audited.
- Do not implement CHoCH+BOS confirmation variant.
- Do not enable live trading.
- Do not treat legacy EA performance as current strategy performance.