# EA Development Documentation

이 디렉터리는 `Trading` 저장소의 deterministic MT5 EA 개발·검증·전략 연구 상태를 장기간 유지하기 위한 영속 문서 계층이다.

대화 기록이나 특정 AI 세션의 기억이 아니라, 이 저장소의 최신 문서를 프로젝트 상태의 기준으로 사용한다.

Last reviewed for current research state: 2026-08-20.

## Authority Order

1. `AGENTS.md`
   - 현재 baseline 전략 규칙의 최상위 authority
   - 모든 EA 구현은 이 문서를 우선한다.

2. `docs/ea/EA_SPEC.md`
   - `AGENTS.md`의 전략 규칙을 deterministic EA가 실행 가능한 형태로 변환한 구현 명세

3. `docs/ea/DECISIONS.md`
   - 구현·검증·연구 과정에서 확정한 중요한 결정과 그 이유

4. `docs/ea/HANDOFF.md`
   - 현재 개발 단계, 완료 항목, 알려진 문제, 다음 작업

5. `docs/ea/TEST_RESULTS.md`
   - MT5 Strategy Tester, 회귀 검증, direct research/OOS 결과

6. `docs/ea/REGIME_RESEARCH_2023_2025.md`
   - 2023–2025 Development regime 연구의 전체 실험 ledger, 실패 가설, freeze, direct validation, 2022 first OOS evidence

7. `docs/ea/STRATEGY_RESEARCH_STATE.md`
   - 현재 전략 robustness 연구 상태의 압축 요약

8. `docs/ea/BACKLOG.md`
   - 향후 연구, 구현, 검증 항목

문서 간 충돌이 발생하면 위 순서대로 상위 authority를 따른다.

**중요:** `REGIME_RESEARCH_2023_2025.md`와 `STRATEGY_RESEARCH_STATE.md`에 기록된 연구 결과는 `AGENTS.md` 또는 `EA_SPEC.md`보다 높은 거래 권한을 갖지 않는다. Research V1이 OOS PASS했다고 해서 자동으로 baseline 규칙이 바뀌지 않는다.

과거 Python 엔진, legacy EA, TradingView 전략, Ground Truth 산출물은 구현 참고자료일 뿐 `AGENTS.md`보다 높은 거래 권한을 갖지 않는다.

## Current Development State

Deterministic execution baseline 구축은 대부분 완료되었고, 현재 핵심 작업은 **strategy robustness research**다.

현재 control:

```text
Mentor deterministic V1
build = 1.91
SL = ROOT_OB_DISTAL_20
```

현재 baseline execution chain:

```text
Objective liquidity
-> H1/M30 map
-> pre-existing eligible HTF Root OB
-> Root-specific PLAN / frozen objective family
-> actual Root contact
-> direction-compatible M1 Sweep
-> later M1 protected-break CHoCH
-> causal fresh M1 FVG
-> unique widest eligible FVG
-> FVG first-retest Entry
-> contributor-merged SL/objective geometry
-> hedging-account same-direction execution
-> pending/fill/cancel/close reconciliation
```

Current baseline properties:

```text
LAST_OPPOSITE_OB + FVG_ORIGIN_OB = Root recognizers
post-contact child OB = optional audit/context only
PD Array = context/reference only
same-direction independent add-ons = allowed on hedging accounts
opposite-direction coexistence = blocked
H4 = long-horizon external-liquidity index only
```

## Current Regime Research State

Research protocol:

```text
2023–2025 = Development / Research
2022      = first sealed OOS — completed / PASS
2021      = preferred final untouched confirmation
```

Frozen research state:

`M30_CLEAN_PERSISTENT_EXPANDING`

```text
scope = EXTERNAL_CONTINUATION
snapshot = scenario PLAN freeze
latest 12 confirmed M30 waves
progression >= 2/3
M30 PROTECTED_BREAK in same 12-wave span <= 1
leg_expansion_ratio > 1.0
```

The frozen model passed the pre-registered 2022 OOS contract, but remains an **OOS-supported research model**, not current baseline authority.

Next research gate:

```text
2021 untouched direct A/B/C confirmation
-> explicit promotion / no-promotion decision
```

Do not alter the frozen formula after viewing 2022 and still call the changed model V1. Any such change is V2 and needs a new untouched confirmation set.

## Research Harness

The standalone research EA family provides direct comparison modes:

```text
V1_REGIME_BASELINE_NO_GATE
V1_REGIME_PARENT_CLEAN_PERSISTENT
V1_REGIME_V1_CLEAN_PERSISTENT_EXPANDING
```

Long-run logging:

```text
RESEARCH_COMPACT = ordinary multi-year research
FULL_AUDIT       = diagnostic replay when a discrepancy must be traced
```

Logging mode has no strategy authority.

## Primary Reference Areas

### Strategy Authority

- `AGENTS.md`
- `docs/ea/EA_SPEC.md`
- `docs/ea/DECISIONS.md`

### Current Status / Evidence

- `docs/ea/HANDOFF.md`
- `docs/ea/TEST_RESULTS.md`
- `docs/ea/REGIME_RESEARCH_2023_2025.md`
- `docs/ea/STRATEGY_RESEARCH_STATE.md`
- `docs/ea/BACKLOG.md`

### Mentor Research

- `research/mentor-youtube/MENTOR_MINIMAL_METHOD.md`
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`
- `research/mentor-youtube/CURRENT_ALGORITHM_REASSESSMENT.md`
- `research/mentor-youtube/EA_TEST_PROTOCOL.md`

### Existing Deterministic Python Reference

- `mentor_engine/structure.py`
- `mentor_engine/liquidity.py`
- `mentor_engine/zones.py`
- `mentor_engine/execution.py`
- `mentor_engine/planner.py`
- `mentor_engine/engine.py`

### Current MQL5 / Historical References

- `mt5/experts/MentorDeterministicV1EA.mq5`
- `mt5/experts/MentorDeterministicV1EA_RegimeResearchV1.mq5`
- `mt5/indicators/ICTCockpitIndicator.mq5`
- `mt5/legacy/`
- `mt5/tester/`

## Lower-Priority / Deferred Areas

다음 영역은 현재 EA strategy robustness 연구의 기본 출발점으로 사용하지 않는다.

- `mentor_context_pack/`
- Gemini / Codex replay pipeline
- OpenClaw 관련 설정
- Ground Truth V2 생성 파이프라인
- `mentor_rule_engine/`
- `archive/`
- TradingView 전략 코드

필요한 특정 구현을 비교할 때만 참고한다.

## Working Process

장기 개발에서는 다음 흐름을 따른다.

```text
ChatGPT
-> 최신 GitHub authority / handoff 복구
-> 전략 분석 / 설계 / 코드 리뷰 / 백테스트 분석
-> complete replacement 파일 제공

User local environment
-> repo-relative 파일 덮어쓰기
-> MetaEditor compile
-> MT5 Strategy Tester
-> 결과 CSV 전달
-> GitHub push

GitHub
-> 최신 코드와 문서 저장
-> 프로젝트의 Single Source of Truth
```

중요한 설계·연구 결정은 `DECISIONS.md`, 개발 상태 변경은 `HANDOFF.md`, 백테스트 결과는 `TEST_RESULTS.md`, regime 실험 전체 이력은 `REGIME_RESEARCH_2023_2025.md`에 기록한다.

코드만 변경하고 상태 문서를 방치하지 않는다.

## Core Working Rule

> ChatGPT 대화는 작업 공간이고, GitHub가 프로젝트의 기억이다.
