# EA Development Documentation

이 디렉터리는 `Trading` 저장소의 deterministic MT5 EA baseline 개발 상태를 장기간 유지하기 위한 영속 문서 계층이다.

대화 기록이나 특정 AI 세션의 기억이 아니라, 이 저장소의 최신 문서를 프로젝트 상태의 기준으로 사용한다.

## Authority Order

1. `AGENTS.md`
   - 현재 전략 규칙의 최상위 authority
   - 모든 EA 구현은 이 문서를 우선한다.

2. `docs/ea/EA_SPEC.md`
   - `AGENTS.md`의 전략 규칙을 deterministic EA가 실행 가능한 형태로 변환한 구현 명세

3. `docs/ea/DECISIONS.md`
   - 구현 과정에서 확정한 중요한 설계 결정과 그 이유

4. `docs/ea/HANDOFF.md`
   - 현재 개발 단계, 완료 항목, 알려진 문제, 다음 작업

5. `docs/ea/TEST_RESULTS.md`
   - MT5 Strategy Tester 및 회귀 검증 결과

6. `docs/ea/BACKLOG.md`
   - 향후 연구, 구현, 검증 항목

문서 간 충돌이 발생하면 위 순서대로 상위 authority를 따른다.

과거 Python 엔진, legacy EA, TradingView 전략, Ground Truth 산출물은 구현 참고자료일 뿐 `AGENTS.md`보다 높은 거래 권한을 갖지 않는다.

## Current Development Goal

현재 목표는 AI 이미지 분석, Gemini, Codex, OpenClaw 등의 runtime dependency 없이 MT5 Strategy Tester와 향후 실거래 환경에서 독립적으로 실행 가능한 deterministic EA baseline을 만드는 것이다.

기존 Ground Truth V2는 현재 BLOCKED 상태이므로, 이를 완성하는 것을 EA 개발의 선행조건으로 두지 않는다.

개발은 다음 두 단계를 분리한다.

1. 전략 구현 정확성 검증
2. 수익성 평가 및 최적화

먼저 의도한 매매 규칙을 정확히 실행하는 EA를 만든 뒤 성과를 평가한다.

## Baseline Development Principle

처음부터 모든 ICT/SMC 경우를 구현하지 않는다.

기본 시나리오는 다음 최소 체인부터 시작한다.

```text
Market Structure
-> Liquidity / Objective
-> Root / Causal LTF Source
-> Source Contact
-> Sweep
-> Meaningful M1 CHoCH
-> Causal CHoCH Displacement FVG
-> Widest FVG
-> FVG Near-Side Limit Entry
-> FVG Distal ± 20% Width SL
-> Frozen Objective / TP
```

H4 is used only as a long-horizon external-liquidity index.
It is not active map/source/entry authority.

FVG add-on, mandatory extra BOS, quality scoring, complex challenger states, arbitrary RR fallback 등의 추가 규칙은 baseline에 포함하지 않는다.

## Primary Reference Areas

EA 개발 시 우선 참고하는 파일과 폴더는 다음과 같다.

### Strategy Authority

- `AGENTS.md`

### Mentor Research

- `research/mentor-youtube/MENTOR_MINIMAL_METHOD.md`
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`
- `research/mentor-youtube/CURRENT_ALGORITHM_REASSESSMENT.md`
- `research/mentor-youtube/EA_TEST_PROTOCOL.md`

### Existing Deterministic Python Implementation

- `mentor_engine/structure.py`
- `mentor_engine/liquidity.py`
- `mentor_engine/zones.py`
- `mentor_engine/execution.py`
- `mentor_engine/planner.py`
- `mentor_engine/engine.py`

### Existing MQL5 References

- `mt5/indicators/ICTCockpitIndicator.mq5`
- `mt5/legacy/MentorScenarioTraderEA.mq5`
- `mt5/legacy/MentorSep2025ParityEA.mq5`
- `mt5/tester/`

## Lower-Priority / Deferred Areas

다음 영역은 EA-only deterministic baseline 개발의 핵심 경로에서 우선 제외한다.

- `mentor_context_pack/`
- Gemini / Codex replay pipeline
- OpenClaw 관련 설정
- Ground Truth V2 생성 파이프라인
- `mentor_rule_engine/`
- `archive/`
- TradingView 전략 코드

필요할 경우 비교 자료로만 사용한다.

## Working Process

장기 개발에서는 다음 흐름을 따른다.

```text
ChatGPT
-> 전략 분석 / 설계 / 코드 리뷰
-> 필요한 변경사항 제안

User local environment
-> 파일 생성 및 수정
-> MetaEditor compile
-> MT5 Strategy Tester
-> 실제 로컬 검증

GitHub
-> 최신 코드와 문서 저장
-> 프로젝트의 Single Source of Truth
```

중요한 설계 결정은 `DECISIONS.md`, 개발 상태 변경은 `HANDOFF.md`, 백테스트 결과는 `TEST_RESULTS.md`에 기록한다.

코드만 변경하고 상태 문서를 방치하지 않는다.

## Core Working Rule

> ChatGPT 대화는 작업 공간이고, GitHub가 프로젝트의 기억이다.
