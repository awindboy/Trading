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
-> causal execution OB retest
-> structural SL
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

No new EA baseline has been implemented yet.

The next task is not MQL5 coding.
The next task is to map AGENTS.md requirements into deterministic rules and compare them with existing implementations.

## Next Task

Create the first EA rule mapping for:

1. Market Structure
2. Liquidity
3. HTF Root OB
4. Causal LTF Refinement
5. Sweep
6. M1 CHoCH
7. Entry
8. SL
9. Objective / TP

Each rule must be classified as:

- D: already deterministic
- H: deterministic after an explicit heuristic is chosen
- U: unresolved / discretionary and requires a design decision

## Do Not Do Yet

- Do not optimize parameters.
- Do not add AI runtime dependencies.
- Do not implement FVG add-ons.
- Do not implement CHoCH+BOS confirmation variant.
- Do not enable live trading.
- Do not treat legacy EA performance as current strategy performance.