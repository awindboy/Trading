# Mentor System Execution Contract

## 목적

이 문서는 신호를 더 많이 만드는 필터가 아니다. 유효한 시나리오를 사람의
조급함, 복구 심리, 임의 재해석으로 망가뜨리지 못하게 하는 실행 경계다.

활성 시간봉은 `H1 / M30 / M15 / M5 / M1`이다. H1이 최상위 지도 프레임이며
H4는 방향, PD, 목적지, source owner 판단에 사용하지 않는다.

## 연구 단계

- 현재 빌드는 `paper/Strategy Tester only`다.
- 수량은 symbol 최소 lot으로 고정한다.
- 실거래 주문 전송은 코드에서 차단한다.
- 실시간 forward test가 필요하면 실제 자금이 아닌 데모 계좌만 사용한다.
- 자체 과거 재생은 월·분기 전체를 한 번에 최적화하지 않고, 미래를 가린 월요일부터
  금요일까지의 1주 단위로 수행한다. 한 주가 끝나기 전에는 규칙을 수정하지 않는다.
- 승률이나 순이익이 아니라 먼저 모든 거래의 map/source/trigger/SL/TP 계보가
  설명 가능한지 검증한다.

## 주문 생성 계약

다음 항목이 모두 존재해야 주문 후보가 된다.

1. frozen objective와 그 목적지를 소유하는 map structure
2. 목적지 반대편의 participant-stop liquidity
3. swing-owned HTF `LAST_OPPOSITE_OB`
4. 같은 displacement 안에서 형성된 최소 한 단계의 LTF child OB
5. source OB 접촉 뒤 발생한 liquidity sweep
6. M5 correction 안에서 발생한 M1 liquidity sweep
7. M1 body-close CHoCH
8. M1 CHoCH displacement의 `LAST_OPPOSITE_OB`
9. 해당 M1 OB retest entry
10. sweep extreme과 entry OB distal 바깥의 SL
11. scenario scope와 같은 등급의 TP

HTF FVG, FVG 첫봉 OB, 최근 pivot, trendline 반응 하나만으로는 첫 주문을
만들 수 없다.

## 실행 상태

```text
PLANNED
-> SOURCE_TOUCHED
-> SWEPT
-> CHOCH_CONFIRMED
-> ORDER_PENDING
-> FILLED
-> TP | SL
```

- 각 상태는 뒤로 돌아가지 않는다.
- 한 시점에는 하나의 `ORDER_PENDING` 또는 `FILLED`만 허용한다.
- 같은 map owner, source, sweep, CHoCH, entry OB로 만든 주문은 물리적으로
  하나의 chain이다.
- 같은 chain은 취소·손절 뒤 다시 주문할 수 없다.
- 새 주문은 source부터 entry OB까지 전 체인이 새로 만들어져야 한다.

## 취소와 무효화

체결 전 다음 중 하나가 발생하면 주문을 취소하고 chain을 종료한다.

- objective 선도달
- source 또는 entry OB body-close 무효화
- source/entry zone 완전 소비
- map protected structure body-close 파괴
- 기존 pending/position과 시간 중첩

체결 후에는 최초 SL 또는 TP만 결과로 사용한다. 수동 청산, SL 축소, TP 이동,
손실 복구 주문은 연구 결과에 포함하지 않는다.

## 승인 경계

1. 최근 기록으로 만든 규칙이 synthetic 검사에서 통과
2. 사용하지 않은 과거 구간에서 paper replay
3. 최소 표본 수를 확보한 뒤 비용 포함 양의 기대값 확인
4. 별도 OOS 구간에서도 규칙을 바꾸지 않고 통과
5. 그 이후에만 별도 live 빌드를 만든다

현재 `MentorScenarioTraderEA.mq5`는 live 빌드가 아니다.
