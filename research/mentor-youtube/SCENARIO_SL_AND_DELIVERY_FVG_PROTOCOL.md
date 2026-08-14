# Scenario SL And Delivery FVG Protocol

## 목적

이 문서는 주간 수동 재생과 이후 EA에서 공통으로 사용할 두 가지 실행 원칙을
고정한다.

1. M1 trigger가 깨지는 가격과 전체 시나리오가 틀리는 가격을 구분한다.
2. 최초 OB 되돌림이 오지 않은 채 목적지 방향으로 가격 전달이 시작되면,
   강한 displacement가 남긴 FVG 되돌림을 두 번째 실행 경로로 사용한다.

## 1. 두 단계 무효화

### Trigger invalidation

M1 sweep, CHoCH, entry OB/FVG가 더 이상 같은 trigger chain을 설명하지 못하는
가격이다. 다음 용도로만 사용한다.

- 미체결 pending 주문 취소
- 해당 trigger chain 폐기
- 새로운 sweep과 CHoCH가 필요한지 판정

Trigger invalidation만으로 전체 map과 objective가 틀렸다고 단정하지 않는다.
따라서 M1 sweep extreme 하나를 자동으로 포지션 SL로 사용하지 않는다.

### Scenario invalidation

진입 전에 정한 방향과 objective로 가격이 전달된다는 가정이 구조적으로 틀렸다고
판정할 수 있는 가격이다. 다음 세 요소를 모두 확인한다.

- source HTF OB를 세분화한 마지막 causal LTF OB의 distal
- 그 OB가 소유하거나 방어한 source/refinement swing의 protected extreme
- 가격이 넘으면 원래 owner와 objective를 유지할 수 없는 map structure level

실제 hard SL은 이 중 **현재 시나리오가 정상적으로 허용하는 가격 경로를 모두
벗어난 가장 먼 경계** 바깥에 둔다. buffer는 broker stops level, 현재 spread,
1 tick 중 최댓값을 사용한다.

하위 OB가 parent와 같은 원인을 명확히 설명하면 HTF OB 전체 폭까지 SL을 넓히지
않는다. 반대로 하위 OB가 단순 중첩일 뿐 source swing을 소유하지 않으면 이를
근거로 SL을 줄이지 않는다.

### 주문 전 필수 기록

각 주문은 다음 네 가격을 별도로 기록한다.

- `trigger_extreme`: sweep 또는 CHoCH chain의 극값
- `entry_zone_distal`: 실제 진입 OB/FVG의 distal
- `scenario_invalidation`: owner와 objective가 틀리는 구조 가격
- `hard_sl`: scenario invalidation 바깥의 실제 주문 가격

`hard_sl`이 예상 sweep, source OB, protected swing 안쪽에 있으면 주문을 만들지
않는다. SL이 너무 멀어 손익비가 나빠지는 경우에도 SL을 억지로 줄이지 않고
진입 가격을 더 정밀화하거나 거래를 포기한다.

## 2. Delivery FVG continuation

### 사용 목적

미리 선택한 OB까지 가격이 되돌아오지 않고 objective 방향으로 강한 displacement가
출발한 경우, 놓친 가격을 추격하지 않고 그 displacement가 만든 FVG의 첫 되돌림을
기다린다. 이미 같은 시나리오의 포지션이 있다면 동일한 구조를 추가진입 기회로
사용할 수 있다.

이 경로는 standalone FVG 매매가 아니다. 기존에 동결된 map owner, 방향,
objective가 먼저 있어야 한다.

### 활성 조건

다음 조건을 모두 만족해야 한다.

1. H1/M30 map의 owner와 objective가 아직 유효하다.
2. 원래 source/refined OB 주문이 미체결이거나, 기존 포지션이 objective 방향으로
   전달 중이다.
3. M5 또는 M1에서 objective 방향의 몸통 확장과 명확한 FVG가 함께 생긴다.
4. displacement가 실제 protected swing을 돌파하거나 기존 방향의 delivery를
   재확인한다.
5. FVG가 생성된 뒤의 첫 되돌림만 사용한다. 이미 완전 체결됐거나 몸통 종가로
   반대편을 관통한 FVG는 재사용하지 않는다.
6. FVG와 displacement를 만든 causal OB 및 protected swing을 설명할 수 있다.

### 진입과 취소

- 진입 후보는 FVG proximal boundary의 첫 retest다.
- proximal touch 뒤 반응 확인이 필요한 맥락이면 M1에서 reclaim/CHoCH를 확인하고
  causal OB retest로 더 정밀화한다.
- 가격이 objective에 먼저 도달하면 주문을 취소한다.
- FVG가 반대 방향 몸통 종가로 무효화되거나 causal OB/protected swing이 깨지면
  주문을 취소한다.
- 원래 넓은 OB pending이 남아 있다면 delivery가 확인되는 순간 이를 취소하고
  FVG continuation 주문으로 교체한다. 두 주문을 동시에 대기시키지 않는다.

### SL과 TP

- SL은 FVG distal에 두지 않는다.
- FVG를 만든 causal displacement OB의 distal, protected swing, scenario
  invalidation 중 정상 되돌림 경로를 모두 벗어난 가격 바깥에 둔다.
- TP는 최초 시나리오에서 동결한 동일 objective를 유지한다.
- 추가진입을 이유로 더 먼 TP로 바꾸지 않는다.

## 3. 최초 진입과 추가진입의 구분

- `DELIVERY_FVG_REPLACEMENT`: 원래 OB 주문이 미체결인 상태에서 FVG retest가
  최초 체결 기회가 된 경우
- `DELIVERY_FVG_ADDON`: 기존 포지션이 살아 있고 동일 objective를 향한 별도
  displacement와 FVG retest가 생긴 경우

두 주문은 같은 방향과 TP를 공유하지만 서로 다른 entry chain과 SL을 가진다.
성과는 ticket 단위 R뿐 아니라 scenario 전체의 합산 위험과 합산 R도 함께 기록한다.
추가진입은 손실 복구나 가격 추격이 아니라 새 displacement와 새 FVG의 첫 retest가
있을 때만 허용한다.

## 4. 주간 재생 감사 기준

각 손실과 미체결 주문을 다음 순서로 다시 본다.

1. hard SL이 scenario invalidation보다 안쪽이었는가?
2. M1 trigger 실패를 HTF scenario 실패로 잘못 해석했는가?
3. 원래 OB 미체결 뒤 유효한 delivery FVG replacement가 있었는가?
4. 기존 포지션 전달 중 유효한 delivery FVG add-on이 있었는가?
5. FVG가 단독 신호였거나 이미 소비된 구간을 재사용했는가?

사후 차트를 보고 SL과 entry를 이동해 기존 거래 결과를 바꾸지는 않는다. 교정된
규칙은 다음 blind replay부터 적용하고, 이전 주간은 규칙 결함을 보여주는 감사
표본으로 유지한다.
