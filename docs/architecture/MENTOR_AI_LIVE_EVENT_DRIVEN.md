# Mentor AI Live Event-Driven Boundary

## Common Clock

Replay와 live는 모두 `V4Runner.advance_closed_m1_bar()`를 호출합니다.

```text
closed M1
-> position/addon update
-> permanent candidate ledger refresh
-> every scenario lane advance
-> PLAN scheduling
-> cursor commit
```

가격이 POI에서 멀리 있는 동안에는 모델 호출이 없습니다. PLAN이 동결된 lane은
objective, source invalidation, child touch 같은 로컬 가격 사건까지만 진행합니다.

## Latency

- API 응답 전에 첫 retest가 지나가면 `MISSED_API_LATENCY`
- broker 승인 전에 지나가면 `MISSED_ORDER_LATENCY`
- M1 안에서 순서를 알 수 없으면 `LATENCY_INTRABAR_AMBIGUOUS`
- entry와 SL을 같은 최초 접근이 관통하면 `THROUGH_DELIVERY`

과거 봉을 소급해 체결하지 않습니다.

## Broker Boundary

Live shadow는 MT5 pending/position을 읽어 로컬 client ID와 reconciliation합니다.
알 수 없는 Mentor 주문, 중복 ID, 전송됐다고 기록됐지만 사라진 주문은 fail-closed입니다.

현재 DEMO 주문 전송은 비활성입니다. shadow 사건 parity와 broker reconciliation 승인을
별도 동결하기 전에는 `--enable-demo-orders`도 거절됩니다. 실계좌는 승인 대상이 아닙니다.
