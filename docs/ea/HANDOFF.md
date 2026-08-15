# EA Development Handoff

Last updated: 2026-08-15
Status: PRE-IMPLEMENTATION
Current phase: Rule formalization

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

Protected swing availability
→ BOS-close information only
→ no retroactive promotion

External trend invalidation
→ body close through current protected swing

Post-external-CHoCH state
→ TRANSITION
→ no immediate fabricated opposite mature trend

External/internal wave promotion
→ structural role based
→ no ATR/point/percentage threshold

INITIAL_CHOCH_FVG core entry
→ FROZEN

FVG availability
→ FROZEN
→ Candle3 close

Candidate snapshot / widest-FVG freeze
→ FROZEN
→ meaningful M1 CHoCH candle close

Post-CHoCH FVG inclusion
→ FORBIDDEN

Pre-authorization FVG retest
→ candidate excluded

Baseline pending entry
→ LONG BUY_LIMIT at FVG.top
→ SHORT SELL_LIMIT at FVG.bottom

Spread-adjusted entry
→ NOT BASELINE
→ future optimization variant

Strategy SL
→ LONG: FVG.bottom - 20% width
→ SHORT: FVG.top + 20% width

Tick normalization
→ entry: preserve strategy boundary
→ LONG SL: outward/down
→ SHORT SL: outward/up

Bid/Ask execution semantics
→ FROZEN

StopsLevel violation
→ EXECUTION_INFEASIBLE / NO ORDER

FreezeLevel cancellation failure
→ EXECUTION_DIVERGENCE tracking

Pending MT5 lifetime
→ ORDER_TIME_GTC

Causal pending cancellation
→ FROZEN

Time-based strategy cancellation
→ NONE / FROZEN

Pending survival authority
→ causal state only

Objective candidate family
→ FROZEN before Entry/SL geometry

Minimum objective eligibility
→ planned R >= 1

planned R role
→ objective-candidate filter
→ NOT max-R optimization

Final TP selection
→ nearest scope-compatible R-eligible candidate

Historical H1 fallback
→ external scenarios only
→ pre-frozen maximum 2 candidates

Post-selection TP rollover
→ FORBIDDEN

Baseline TP price
→ exact selected structural liquidity

## Next Task

Create the first EA rule mapping for:

1. Validate the frozen trend-state semantics visually and during implementation parity testing.
2. Return to H1/M30 map-owner + scenario-scope assignment using the frozen trend engine.
3. Resolve selected-FVG exact invalidation / consumption.
4. Resolve final refined-source exact invalidation.
5. Resolve session-gap handling.
6. Resolve warm-up/state reconstruction.
7. Run final AGENTS / EA_SPEC / DECISIONS consistency audit.
8. Freeze deterministic V1 specification.
9. Implement minimum MQL5 EA.
10. Validate implementation parity before profitability optimization.

Each rule must be classified as:

- D: already deterministic
- H: deterministic after an explicit heuristic is chosen
- U: unresolved / discretionary and requires a design decision

## Do Not Do Yet

- Do not optimize parameters.
- Do not add AI runtime dependencies.
- Do not implement FVG add-ons or Delivery FVG replacement until their post-correction contracts are re-audited.
- Do not implement CHoCH+BOS confirmation variant.
- Do not enable live trading.
- Do not treat legacy EA performance as current strategy performance.