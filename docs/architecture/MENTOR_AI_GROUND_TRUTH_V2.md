# Mentor AI Ground Truth V2

## Authority

`AGENTS.md`가 유일한 전략 정본이다. 활성 계약인 `PLAN`,
`TRIGGER_WATCH`, `DELIVERY_REVIEW/ADDON`은
`scripts/build_mentor_api_contracts.py`가 이 정본에서 생성한다.

## Evidence Flow

```text
raw M1 since 2023-12-01
-> H1/M30/M15/M5 permanent event ledger
-> lossless family packets with exact role OHLC
-> continuous stateful chronological replay
-> independently repeated semantic audit
-> shuffled counterfactual audit
-> four-checkpoint daily no-trade MTF audit
-> trigger-role and risk-slot audit
-> frozen Ground Truth
-> Gemini replay comparison
```

정답 역할이 최초 판단 가능 패킷에 없으면 `MODEL_MISS`가 아니라
`ENGINE_CANDIDATE_MISS`다. 이 값이 하나라도 있으면 정답지를 동결하지
않는다. 같은 physical family는 accepted PLAN이 terminal event에 도달하기
전까지 새 snapshot으로 중복 승인할 수 없다.

## Scenario And Risk Books

- `ownerEpoch`: 외부 owner 생명주기
- `scenarioSlots`: 독립 watch/pending lane
- `orders`: idempotent client ID 주문 원장
- `positions`: 체결 원장
- `executionChains`: 동일 physical FVG/retest 중복 방지
- PREPARED/watch lane은 위험 슬롯을 사용하지 않는다.
- PENDING+FILLED만 최대 3개이며 반대 방향 동시 위험은 금지한다.

## Objective Family

PLAN은 같은 owner 경로의 순서화된 objective family를 동결한다. 현재
H1/M30 목적지는 삭제하지 않는다. 먼 과거 유동성은 H1만 최대 2개를
fallback 증거로 보존하며, 실행 가능한 현재 목적지가 하나도 없을 때만
검토한다. Entry와 SL이 확정된 뒤 `plannedR >= 1`인 최초 미소진 목적지를
선택하고 TP는 그 유동성의 실제 wick 가격에 둔다.

## Completion Gates

1. 계약 생성과 legacy 문구 검사
2. scripted replay/live/multi-lane/latency 검사
3. Ground Truth 역할 coverage 100%
4. 연속 chronological, 독립 재심사, shuffled counterfactual 감사 일치
5. 일별 06/12/18/24 UTC no-trade 차트 감사에서 누락 family 0건
6. trigger packet 역할, 미래 데이터, 주문 전 동결, 3-risk-slot 검사
7. frozen Ground Truth에 대한 Gemini 차이 귀속
8. live shadow parity와 broker reconciliation

## Current Status

- 기존 경로 `output/ground_truth_v2_june2026_v451`은 무효다.
- 기존 2건 합계 `+0.1293013556R`은 동적 objective 수명주기가 누락된
  결과이므로 Gemini parity 기준으로 사용할 수 없다.
- 2026년 6월은 월초부터 owner/objective 상태를 유지하는 연속 원장을
  다시 생성하고 있다.
- 새 원장과 모든 독립 감사가 끝나기 전 상태는
  `BLOCKED_DYNAMIC_OBJECTIVE_LIFECYCLE`다.
- 실제 Gemini 재현성, live-shadow parity, MT5 DEMO 체결은 아직 승인되지
  않았다.

코드 회귀 통과, 이미지 생성, 일부 기간 재생만으로 정답지 완료나 수익성을
주장하지 않는다.
