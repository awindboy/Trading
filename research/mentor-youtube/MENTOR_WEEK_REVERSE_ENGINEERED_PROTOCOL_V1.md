# Mentor Weekly Scenario Protocol V1

> **폐기된 실행 기준:** 이 버전은 HTF source OB와 M1 entry zone을 분리하지 못하고
> M1 causal OB retest를 기본 진입으로 고정했다. 영상 2·3·11·13편에서 반복되는
> `CHoCH displacement FVG retest`와 충돌하므로 블라인드 성과 검증에 사용하지 않는다.
> 현재 실행 기준은 `MENTOR_WEEK_REVERSE_ENGINEERED_PROTOCOL_V2.md`다.

## 목적과 적용 범위

이 문서는 2025-04-07~11 GOLD 전체 경로를 H1, M15, M5, M1 순서로 다시 읽어
추출한 동결 규칙이다. 개별 거래의 손익을 설명하기 위해 조건을 붙이는 문서가 아니다.
다음 블라인드 주간에서도 같은 구조라면 같은 방향, 같은 POI 종류, 같은 SL/TP 원칙을
사용하기 위한 결정 계약이다.

스승님 영상에서 확인한 개념과 이번 주에서 필요성이 드러난 실행 규칙을 구분한다.

- `MENTOR`: 영상에서 반복적으로 확인된 판단 흐름
- `OPERATIONAL`: 동일 판단을 매번 재현하기 위해 이번 연구에서 고정한 실행 규칙
- `UNCERTAIN`: 아직 영상 또는 블라인드 표본으로 확정하지 못한 부분

## 1. 시나리오는 목적지부터 시작한다

1. `MENTOR` H1에서 현재 전달 방향과 다음에 공격할 외부 유동성을 먼저 정한다.
2. `OPERATIONAL` 외부 유동성은 단순 최근 고저점이 아니라 다음 중 하나여야 한다.
   - H1/M15에서 명확히 방어된 스윙 고점 또는 저점
   - 같은 가격대에서 두 번 이상 반응한 고점 또는 저점
   - 이전 전달 파동이 출발하거나 멈춘 경계
3. TP는 선택한 유동성의 실제 가격에 둔다. 유동성 바깥으로 임의 offset을 두지 않는다.
4. 목적지가 먼저 소진되면 기존 시나리오와 미체결 주문은 종료한다. 더 먼 목표를
   기존 OB에 다시 붙이지 않는다.

## 2. H1 map의 지속과 전환

1. `MENTOR` H1은 방향과 premium/discount 맥락을 정하고 M15/M5는 원인을 세분화한다.
2. `OPERATIONAL` H1 map은 반대 방향의 작은 CHoCH만으로 바뀌지 않는다.
3. 현재 map은 다음 두 조건이 함께 발생할 때까지 유지한다.
   - 반대편 외부 유동성이 sweep 또는 명확히 도달됨
   - 이후 H1 몸통이 현재 map의 protected swing을 반대로 돌파함
4. 외부 유동성 도달 후 M15만 반대로 전환됐지만 H1 protected swing이 유지되면
   `INTERNAL_ROTATION`이다. 이 경우 TP는 첫 내부 유동성까지만 허용한다.
5. H1 protected swing까지 몸통으로 깨고 반대 방향 retest가 실패해야
   `EXTERNAL_REVERSAL`로 승격한다.
6. 반대 방향 이동이 objective를 이미 소진한 뒤 원래 H1 방향으로 reclaim되면
   반대 시나리오는 즉시 끝낸다. 소진된 objective 아래나 위로 TP를 연장하지 않는다.

이 규칙은 추세를 틀리게 읽은 손실과 올바른 추세 안에서 발생한 정상 손실을 분리한다.
map이 유지된 상태에서 유효한 POI와 trigger를 거친 손절만 `MARKET_UNCERTAINTY`로
분류할 수 있다.

## 3. 최초 진입: HTF OB 반응

1. `MENTOR` H1 또는 M30의 의미 있는 스윙 부근에서 전달을 만든 마지막 반대색
   캔들을 parent OB로 잡는다.
2. 같은 전달 파동 안에서 M15, M5, M1 순서로 내려가며 parent OB를 구성한 마지막
   인과적 OB를 찾는다.
3. 단순 가격 중첩은 refinement가 아니다. child OB는 parent와 같은 displacement가
   같은 구조를 돌파한 원인을 설명해야 한다.
4. 가격이 미리 정한 refined OB에 도달하기 전에는 M1 trigger를 찾지 않는다.
5. 도달 후 다음 순서를 모두 요구한다.
   - 진입 반대편에 사전 형성된 M1 유동성
   - 그 유동성의 wick sweep과 종가 복귀
   - 별도 캔들의 map 방향 몸통 CHoCH
   - CHoCH displacement를 만든 causal M1 OB의 첫 retest
6. 진입가는 마지막 causal OB의 proximal boundary다.
7. M1 sweep extreme은 trigger 무효화점일 뿐 자동 SL이 아니다.

## 4. 출발한 추세를 따라가는 진입: Delivery FVG

기존 규칙은 원래 OB가 retest되기 전에 objective가 도달하면 시나리오를 끝내기만 했다.
이번 주에는 이 때문에 연속 전달 구간 대부분이 비매매로 남았다. 다음 규칙은 기존 OB를
재사용하는 편법이 아니라, 새 displacement가 만든 별도 continuation 시나리오다.

1. `MENTOR` 기존 H1 map과 다음 objective가 먼저 존재해야 한다.
2. `OPERATIONAL` map 방향 M15 displacement가 이전 objective를 몸통으로 돌파하고
   다음 objective로 acceptance를 보이면 새로운 전달 파동을 선언한다.
3. 그 displacement가 만든 M15 FVG 중 구조 돌파에 직접 포함된 FVG만 후보로 삼는다.
4. M15 FVG는 M5에서 같은 displacement의 세부 FVG/OB로 refinement할 수 있다.
5. 첫 retest에서 M1 반대편 유동성 sweep과 map 방향 CHoCH가 나오면 진입한다.
6. 원래 깊은 OB pending은 새 전달 파동이 확정되는 순간 취소한다. 두 주문을 동시에
   기다리지 않는다.
7. 이 진입은 `DELIVERY_FVG_REPLACEMENT`로 기록한다. 이미 같은 objective를 향한
   포지션이 있다면 `DELIVERY_FVG_ADDON`으로 구분한다.

## 5. 여러 되돌림 구간과 재시도

1. 같은 M15 displacement 안에 서로 떨어진 FVG가 둘 이상이면 얕은 구간과 깊은
   구간을 별도 POI로 보존한다.
2. 얕은 FVG의 손절만으로 H1 map을 폐기하지 않는다.
3. 더 깊은 FVG가 아직 fresh이고 scenario protected swing이 유지되며, 그 구간에서
   새로운 M1 sweep과 CHoCH가 완성되면 같은 objective로 새 거래를 허용한다.
4. 이전 trigger를 재사용하지 않는다. POI마다 sweep, CHoCH, causal entry OB가 새로
   형성돼야 한다.
5. 한 시점에는 하나의 포지션만 허용한다. 첫 포지션이 손절되거나 종료된 뒤 다음
   causal POI를 사용한다.
6. 첫 손절과 두 번째 큰 익절은 하나의 방향 가설에 대한 두 개의 독립 실행으로 기록한다.
   두 번째 거래를 첫 손실의 복구 주문으로 취급하지 않는다.

## 6. SL

### HTF OB 반응

- long: causal entry OB distal, refined source protected low, map protected low 중 가장 낮은
  시나리오 무효화점 아래
- short: causal entry OB distal, refined source protected high, map protected high 중 가장 높은
  시나리오 무효화점 위

### Delivery FVG

- FVG 경계 자체가 아니라 FVG를 만든 causal OB와 correction protected swing 바깥
- 정상적인 되돌림이 통과할 수 있는 M1 sweep extreme에는 SL을 두지 않음

buffer는 현재 spread, broker stops level, 1 tick 중 최댓값만 사용한다. SL이 멀어
손익비가 낮아지는 경우에도 구조를 좁혀서 맞추지 않는다. 진입을 포기하거나 더 정밀한
causal child를 기다린다.

## 7. TP와 시나리오 갱신

1. TP는 진입 전에 동결한 가장 가까운 미소진 목적 유동성의 실제 가격이다.
2. TP 도달 전에는 더 먼 유동성으로 이동하지 않는다.
3. TP 도달 후 가격이 그 수준을 몸통으로 받아들이고 새 displacement를 만들면
   기존 거래와 별개의 continuation 시나리오를 만든다.
4. wick sweep 후 level 안쪽으로 복귀하면 objective는 소진된 것으로 처리하고
   우선 내부 rotation 가능성을 관찰한다.
5. 최대 R, RR fallback, 시간 청산은 사용하지 않는다.

## 8. 거래하지 않는 경우

- H1 방향과 objective를 사전에 설명할 수 없음
- parent OB 또는 구조 돌파를 만든 delivery FVG가 없음
- 가격이 POI에 오기 전에 M1 trigger를 찾음
- POI 접촉은 있었지만 사전 유동성 sweep이 없음
- sweep과 CHoCH가 같은 한 캔들의 단순 wick/body 움직임임
- objective가 이미 소진됐는데 기존 POI에 더 먼 TP를 붙임
- 강한 H1 map 반대 거래인데 외부 objective sweep과 M15 rotation조차 없음
- 반대 objective가 소진되고 원래 방향 reclaim가 발생했는데 이전 반대 map을 계속 사용함
- SL이 M1 sweep extreme만으로 정해지고 scenario invalidation을 포함하지 못함

## 9. 손실 분류

손실을 보고 규칙을 바꾸지 않는다. 아래 조건을 모두 만족한 손실만 시장 불확실성으로
받아들인다.

1. 진입 전에 H1 map과 objective가 동결됨
2. 허용된 parent OB 또는 delivery FVG만 사용함
3. causal refinement와 M1 sweep, CHoCH, retest가 순서대로 존재함
4. SL이 scenario invalidation 바깥에 있음
5. TP가 미소진 실제 유동성에 있음
6. 경쟁 반대 시나리오가 규칙상 우세하지 않았음

하나라도 빠지면 `MARKET_UNCERTAINTY`가 아니라 규칙 위반 또는 아직 정의되지 않은
지식의 빈공간이다.

## 10. 블라인드 주간 동결 항목

다음 주간을 보기 전에 아래 항목을 변경하지 않는다.

- map 전환 조건
- OB reaction과 delivery FVG의 구분
- 여러 FVG 재시도 조건
- M1 sweep/CHoCH/retest 순서
- scenario invalidation SL
- 실제 liquidity 가격 TP
- objective 도달 후 새 시나리오 생성 규칙

다음 블라인드 주간에서 같은 구조가 같은 판단으로 이어지는지 먼저 확인한다. 수익률을
보고 조건을 추가하거나 제거하지 않는다.
