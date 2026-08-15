# EA Development Handoff

Last updated: 2026-08-15
Status: V1 SPECIFICATION FROZEN
Current phase: Minimum MQL5 baseline implementation

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


## Implementation Checkpoint — Phase 1.1 Structure/Bootstrap Core

`mt5/experts/MentorDeterministicV1EA.mq5` implementation is active.

Local compile result for Phase 1 / build 0.10:

```text
0 errors
1 warning
482 ms
cpu='AVX2 + FMA3'
```

The exact warning text was not preserved in the repository.

Post-compile authority review found implementation defects before tester validation:

1. Market-structure waves incorrectly required clock-contiguous bars across session gaps.
   - FIXED in Phase 1.1.
   - Frozen clock-continuity requirement belongs only to M1 execution-FVG qualification.

2. INITIAL_BOS / BOS could leave the new directional external delivery extreme unset.
   - FIXED in Phase 1.1.
   - Bullish break now creates/maintains the bullish delivery extreme.
   - Bearish break is symmetric.

3. If bootstrap completed while the market was closed, the final already-processed bar could be processed again at reopen.
   - FIXED with explicit runtime cursor pending-state semantics.

4. Historical closed-bar `available_at` was tied to next-bar open across a gap.
   - FIXED to timeframe-slot close availability.
   - No synthetic price path is created.

5. Bootstrap event logging could become excessively large.
   - Strategy calculation is unchanged.
   - Detailed bootstrap event output is now optional and OFF by default.
   - Runtime events and bootstrap final snapshots remain available.

Current code status:

- Phase: `STRUCTURE_ONLY`
- Internal build: `0.11`
- MQL property version: `1.00`
- Orders: intentionally disabled
- Phase 1 / build 0.10 MetaEditor compile: `0 errors / 1 warning`
- Phase 1.1 recompile: REQUIRED
- Strategy Tester structure smoke test: NOT YET PASSED

Implemented:

- H4 / H1 / M30 / M15 historical structure bootstrap backbone
- H4 → H1 → M30 → M15 chronological bootstrap tie order
- runtime H4 → H1 → M30 → M15 → M5 → M1 closed-bar scheduler
- causal 3-candle wave confirmation
- doji interruption
- session gaps do NOT reset structure or invalidate the 3-bar wave sequence by clock discontinuity
- body-close INITIAL_BOS / BOS
- directional delivery extreme after INITIAL_BOS / BOS
- protected-swing body-close break → TRANSITION
- compact structure working state instead of full historical wave tree
- execution epoch boundary logging
- duplicate-safe reopen cursor
- CSV structural/event logging

Not implemented yet:

- H4 long-horizon liquidity index objects
- liquidity families / sweep engine
- Root OB detection
- causal LTF child refinement
- source contact / source lifecycle
- M1 meaningful CHoCH scenario authorization
- execution FVG selection
- objective / TP selection
- broker order submission / cancellation / OnTradeTransaction reconciliation

## Next Task

1. Recompile Phase 1.1 and require `0 errors`; if any warning remains, preserve the exact warning line.
2. Run a short `Every tick based on real ticks` Strategy Tester structure smoke test.
3. Inspect bootstrap final state plus runtime `WAVE_CONFIRMED`, `INITIAL_BOS`, `BOS`, and `PROTECTED_BREAK` ordering.
4. Only after the structure smoke test passes, implement H4 long-horizon liquidity index + V1 liquidity/sweep layer.
5. Continue Root/source → M1 execution → broker order layers, then run full parity before profitability optimization.

## Do Not Do Yet

- Do not optimize parameters.
- Do not add AI runtime dependencies.
- Do not implement FVG add-ons or Delivery FVG replacement until their post-correction contracts are re-audited.
- Do not implement CHoCH+BOS confirmation variant.
- Do not enable live trading.
- Do not treat legacy EA performance as current strategy performance.