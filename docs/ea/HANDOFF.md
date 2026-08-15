# EA Development Handoff

Last updated: 2026-08-16
Status: V1 SPECIFICATION FROZEN
Current phase: Phase 2 Liquidity / Sweep core implementation

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


## Implementation Checkpoint — Phase 2 Liquidity/Sweep Core

Phase 1.1 structure/bootstrap verification is complete.

Verified from the short real-tick smoke run:

```text
duplicate structure event        = 0
future available_at              = 0
MTF tie-order violation          = 0
same-side consecutive wave       = 0
INITIAL_BOS opposite ref missing = 0
body-close break violation       = 0
protected break transition error = 0
```

One logging-only defect was found:

```text
InpLogBootstrapEvents=false
but bootstrap PROTECTED_BREAK STRUCTURE_STATE rows were still emitted
```

Phase 2 fixes this without changing strategy calculation.

Current code status:

- Phase: `LIQUIDITY_CORE`
- Internal build: `0.20`
- MQL property version: `1.00`
- Orders: intentionally disabled
- Phase 2 compile: PENDING LOCAL METAEDITOR
- Phase 2 liquidity smoke test: NOT STARTED

Implemented in Phase 2:

### EXTERNAL_SWING

- confirmed WAVE only
- protected/external structural promotion required
- synthetic delivery extreme itself cannot create liquidity
- wick interval stored as `bottom/top`
- rank/promotion time becomes liquidity `available_at`
- H4 uses the same family with `timeframe=H4`
- H4 remains long-horizon liquidity memory only

### H4 LONG_HORIZON_LIQUIDITY_INDEX

- H4 creates only `EXTERNAL_SWING`
- H4 `DEFENDED_RANGE_EDGE` is explicitly blocked
- consumed H4 pools are removed from the active index
- H4 index grants no map/source/entry authority

### DEFENDED_RANGE_EDGE

- four confirmed alternating waves
- HIGH/HIGH wick intervals must overlap
- LOW/LOW wick intervals must overlap
- body close must remain inside the defended box through fourth-wave confirmation
- both HIGH and LOW edge pools become available only at fourth-wave confirmation
- independent equal-high/equal-low detection is not added
- H4 defended-range generation is disabled

### Physical sweep / body delivery

HIGH pool sweep:

```text
high penetrates pool.top by at least one tick
AND
close <= pool.top
```

LOW pool sweep:

```text
low penetrates pool.bottom by at least one tick
AND
close >= pool.bottom
```

Body delivery has precedence:

```text
HIGH: close > pool.top
LOW : close < pool.bottom
```

A sweep or body delivery consumes the pool once.

### Same-bar self-sweep prevention

Liquidity consumption is processed before
new structure/liquidity publication on each closed bar.

Additionally:

```text
pool.available_at >= current_bar.available_at
```

cannot be consumed by that bar.

### Active-memory compression

Consumed pools are removed from the in-memory active array
after their audit event is written.

### STRUCTURAL_REACTION

The family/type remains part of the V1 object model.

Actual creation is intentionally dormant in Phase 2 because the frozen rule requires:

```text
pre-existing causal OB
+
structural ownership
+
actual OB touch
+
confirmed reaction wave
```

Root/source ownership is attached in the next implementation layer.
No FVG-only or arbitrary reaction substitute is introduced.

Not implemented yet:

- causal Root OB discovery
- Root/source ownership registry
- STRUCTURAL_REACTION activation
- targeted M30/M15/M5 child refinement
- source contact / source lifecycle
- scenario-specific mature sweep authorization
- meaningful M1 CHoCH binding
- execution FVG selection
- objective / TP selection
- pending order submission / cancellation
- `OnTradeTransaction` reconciliation

## Next Task

1. Compile Phase 2 in MetaEditor and preserve the complete compile result.
2. Run the Phase 2 liquidity smoke test with `Every tick based on real ticks`.
3. Audit the generated `mentor_v1_phase2_events.csv` for:
   - EXTERNAL_SWING causal promotion
   - H4 external-only invariant
   - four-wave defended-range causality
   - one-tick sweep
   - body-delivery precedence
   - same-bar self-sweep prevention
   - single-consumption invariant
4. After Phase 2 passes, implement Root OB + causal child/source ownership.
5. Activate `STRUCTURAL_REACTION` only after that ownership layer exists.


## Do Not Do Yet

- Do not optimize parameters.
- Do not add AI runtime dependencies.
- Do not implement FVG add-ons or Delivery FVG replacement until their post-correction contracts are re-audited.
- Do not implement CHoCH+BOS confirmation variant.
- Do not enable live trading.
- Do not treat legacy EA performance as current strategy performance.