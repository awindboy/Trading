# 실시간 및 데모 운용 절차

## 1. 역할 분리

- MT5 collector: bars, ticks, spread, symbol specification 수집
- neutral renderer: 같은 as-of의 H1/M30/M15/M5/M1 raw chart 생성
- AI judgment: map, objective, root, refinement, trigger, 주문 또는 비매매 판단
- deterministic validator: schema, state transition, spread, stops level, risk, 중복 주문 검증
- demo executor: 검증된 주문만 MT5 데모 계좌로 전달

AI가 수량을 임의 계산하거나 검증기를 우회해 `order_send`를 호출해서는 안 된다.

## 2. 이벤트 기반 호출

1. 새 H1 종가: map, objective, source freshness 재검토
2. scenario 없음: 다음 H1까지 대기
3. root/child 동결: 가격이 child 접근 범위에 들어올 때까지 M1 호출 금지
4. child 접근/접촉: M5와 M1 packet 생성, M1 종가마다 반응 검토
5. ORDER_FROZEN: 결정론적 주문 검사 후 데모 전송
6. pending 중 새 H1/M15 종가: 반드시 AI 재승인
7. 체결 후: 최초 SL/TP만 기계적으로 관리하고 AI 임의청산 금지

접근 범위는 거래 허가 규칙이 아니다. collector가 고정된 child 가격으로 차트 확대 시점을 알리는 운영 최적화일 뿐이다.

## 3. 호출 packet

매 호출에는 다음만 포함한다.

- 실행 모드와 동일한 UTC `as_of`
- H1/M30 map 이미지
- 필요한 경우 M15/M5 refinement 이미지
- POI 접근 뒤에만 M1 이미지
- `state/current_state.json`
- 직전 상태 이후의 M1 bars와 현재 bid/ask/spread
- tick size, volume min/step/max, broker stops level
- 직전 20개 append-only decision event

전체 대화 기록이나 대상 기간의 이후 성과는 매번 다시 넣지 않는다.

## 4. 상태 전이

```text
FLAT
-> PREPARED
-> ARMED
-> TRIGGERED
-> PENDING
-> FILLED
-> CLOSED
```

어느 단계에서도 `CANCELED`, `MISSED`, `DATA_ERROR`로 종결될 수 있다. 과거 상태를 덮어쓰지 말고 append-only event를 추가한 뒤 current state를 갱신한다.

## 5. 승인 경계

- 기본 계좌: 데모
- 기본 sizing: 최소 lot 또는 별도 고정 위험 모듈
- 동시 노출: pending 또는 position 하나
- 필수 필드 누락: 주문 차단
- schema 위반 또는 state hash 불일치: 주문 차단
- 데이터 지연, symbol 불일치, as-of 불일치: 주문 차단
- live 전환: 별도 사용자 승인 없이는 금지

