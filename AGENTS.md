# 스승님식 수동 매매 절대 실행 계약

- 상태: `FROZEN / MANUAL-TRADING AUTHORITY`
- 제정일: `2026-08-01`
- 최근 개정: `2026-08-02` (`scenario scope별 목적 유동성 계약 및 외부추세 지속 중간 유동성 처리 추가`)
- 적용 범위: 수동 차트 분석, 블라인드 리플레이, 데모 매매 판단

## 1. 문서의 지위

이 문서는 사용자가 `스승님식으로 매매해`, `스승님 방식으로 차트를 봐`, `직접 매매해`라고 요청했을 때
내가 가장 먼저 적용해야 하는 수동 매매 실행 계약이다.

- 전략 근거는 이 폴더에 정리된 스승님의 21개 영상으로 제한한다.
- 일반 ICT/SMC 지식, 기존 EA, V32, 점수 모델, 역설계 결과는 거래를 허가할 수 없다.
- 과거 문서나 기존 관행과 충돌하면 이 문서의 **비매매 원칙과 원인 우선순위**를 따른다.
- 모호한 부분을 임의의 ICT 개념으로 채우지 않는다. 설명할 수 없으면 `비매매`다.
- 결과가 수익이어도 이 계약을 위반한 거래는 스승님식 성과에 포함하지 않는다.

스승님식 최초 진입의 기본 순서는 다음과 같다.

```text
목적 유동성
-> H1/M30 시장 지도
-> 스윙 근처의 사전 형성 HTF root OB
-> 같은 가격 사건을 설명하는 causal LTF OB refinement
-> refined OB 접촉
-> 사전에 존재하던 유동성 sweep
-> M1의 의미 있는 몸통 CHoCH
-> causal execution OB retest
-> 구조 무효화 바깥 SL
-> 처음 동결한 목적 유동성 TP
```

이 순서에서 앞 단계가 없으면 뒷 단계는 아무리 선명해도 거래 근거가 아니다.

단, 위 시나리오와 원래 목적지가 모두 동결됐지만 기다리던 OB 주문이 미체결된 채 가격이 목적지 방향으로 출발한 경우에는 다음 **대체 실행 경로**를 허용한다.

```text
동결된 owner / 방향 / objective / HTF-to-LTF OB lineage
-> 원래 OB 주문 미체결
-> 목적지 방향의 명확한 displacement와 구조 전달 재확인
-> displacement가 만든 fresh FVG와 causal OB
-> 기존 넓은 OB pending 취소
-> fresh FVG의 첫 되돌림
-> DELIVERY_FVG_REPLACEMENT 진입
-> displacement causal OB / protected swing / 원래 시나리오 무효화 바깥 SL
-> 처음 동결한 동일 objective TP
```

이 경로는 FVG가 새 시나리오를 만드는 것이 아니다. 이미 완성된 HTF 시나리오가 가격 전달로 확인됐을 때 **미체결 원주문의 실행 위치만 교체**한다.

## 2. 시간봉의 고정 역할

사용 시간봉은 `H1 / M30 / M15 / M5 / M1`이다. H4는 기본 매매 판단에서 사용하지 않는다.

| 역할 | 시간봉 | 해야 하는 일 | 해서는 안 되는 일 |
| --- | --- | --- | --- |
| Map | H1, M30 | 외부/내부 구조, 현재 파동, 목적 유동성, 의미 있는 스윙과 root OB를 정한다. | 최근 고저점을 무조건 외부 유동성으로 승격하지 않는다. |
| Refinement | M30, M15, M5 | 상위 OB와 같은 스윙 및 displacement를 설명하는 하위 OB를 찾는다. | 가격이 겹친다는 이유만으로 무관한 작은 OB를 연결하지 않는다. |
| Correction context | M5 | refined OB 안에서 진행되는 correction과 sweep 후보의 맥락을 확인한다. | M5 신호만으로 최초 포지션을 허가하지 않는다. |
| Trigger | M1 | OB 접촉 뒤 sweep, 의미 있는 CHoCH, execution zone을 확인한다. | POI가 정해지기 전에 M1에서 진입 후보부터 찾지 않는다. |

M1은 **시나리오를 만드는 시간봉이 아니라 이미 존재하는 시나리오의 반응을 확인하는 시간봉**이다.

## 3. 목적지와 시장 지도

### 3.1 목적 유동성을 먼저 정한다

진입 방향을 생각하기 전에 scenario scope와 그 scope가 설명할 수 있는 최종 목적 유동성을 하나 정한다. 목적지는 가까운 순서만으로 정하지 않고 **외부 구조를 계속 전달하는 거래인지, 외부 범위 안에서 잠시 회전하는 거래인지**를 먼저 구분한다.

- PLAN은 임의의 TP 하나가 아니라 동일 owner 경로의 순서가 고정된 `objective family`를 동결한다.
- `EXTERNAL_CONTINUATION` family는 현재 H1/M30 외부 방향의 미소진 H1/M30 external liquidity로만 구성한다.
- `INTERNAL_ROTATION` family는 외부 구조가 바뀌었다고 확대하지 않고, 현재 dealing range 안의 의미 있는 M15 이상 internal liquidity로만 구성한다.
- `EXTERNAL_REVERSAL`은 반대 방향 M1 CHoCH만으로 선언하지 않는다. H1/M30 protected swing의 몸통 파괴와 새 방향 owner가 확인된 뒤에만 새 방향 external liquidity를 목표로 한다.
- `EXTERNAL_CONTINUATION`의 entry와 external objective 사이에 있는 내부 유동성은 최종 TP가 아니라 `INTERMEDIATE_DELIVERY`로 사전에 기록한다.
- `INTERMEDIATE_DELIVERY`가 CHoCH 또는 delivery displacement 과정에서 소진돼도, 외부 objective·owner·source lineage가 그대로라면 그것만으로 pending order를 취소하거나 TP를 재지정하지 않는다.
- 반대로 `INTERNAL_ROTATION`의 첫 internal objective가 entry 전에 소진되면 시나리오는 끝난다. 더 먼 internal/external liquidity로 TP를 갈아 끼우지 않는다.
- 목적 유동성은 다른 참여자가 실제로 손절을 둘 만한 스윙, 반복 방어된 range edge, reaction trap 등이어야 한다.
- 단순 최근 pivot, 라운드 넘버, 이미 소진된 고저점은 목적 유동성이 아니다.
- 비교할 수 없는 owner 경로의 목적지가 여러 개 남으면 하나의 family로 섞지 않고 별도 scenario lane으로 유지한다.
- PLAN packet은 현재 구조의 미소진 H1/M30 objective를 주 경로로 보존하고, `2023-12-01` 이후의 먼 과거 미소진 H1 liquidity 중 현재가에서 방향상 가장 가까운 최대 `2개`만 비활성 fallback으로 함께 동결할 수 있다. 오래된 M30 이하는 fallback이 될 수 없다.
- 장기 H1 fallback은 Entry와 hard SL이 확정된 뒤 현재 구조 objective가 없거나 모두 planned R `1` 미만인 경우에만 활성화한다. 현재 objective가 하나라도 planned R `>=1`이면 장기 H1 후보를 TP로 선택하지 않는다.
- Entry와 hard SL이 확정된 시점에 family 순서대로 검사하여 아직 미소진이고 planned R `>=1`인 최초 수준을 최종 TP로 선택한다. 그 앞 수준은 `INTERMEDIATE_DELIVERY`다.
- `INTERNAL_ROTATION`에서는 진입가와 먼 유동성 사이의 더 가까운 성숙한 internal liquidity를 건너뛰지 않는다.
- `EXTERNAL_CONTINUATION`에서는 더 가까운 내부 유동성을 숨기지 않고 중간 전달 지점으로 기록하되, 그것을 이유로 사전에 동결한 external objective를 내부 TP로 축소하지 않는다.
- 처음 선택한 목적지가 멀수록 좋은 거래라고 판단하지 않는다. 큰 R은 올바른 원인과 가까운 구조 무효화에서 나오는 결과이지, TP를 먼 유동성으로 밀어서 만드는 수치가 아니다.
- 주문 전 최종 objective가 먼저 소진되거나 더 가까운 opposing liquidity가 새 owner로 확정되면 기존 시나리오와 pending order를 취소하고 map부터 다시 작성한다.

TP는 해당 유동성의 실제 wick 가격에 둔다. 스윕 가능성을 무시하고 유동성보다 더 멀리 TP를 밀지 않는다.

### 3.2 외부와 내부를 혼동하지 않는다

- H1/M30 protected swing과 dealing range를 먼저 표시한다.
- 그 범위 안의 M15/M5 저점과 고점은 우선 내부 구조로 취급한다.
- 내부 저점 sweep만으로 H1 외부 반전을 선언하지 않는다.
- 외부 구조가 남아 있는데 M1 CHoCH가 발생해도 그것은 우선 내부 반응이다.

`내부 유동성 -> M1 CHoCH`를 `외부 반전`으로 승격하는 것은 금지한다.

### 3.3 dealing range 위치를 진입 권한에 포함한다

- H1/M30의 현재 external protected high와 low로 active dealing range를 정하고 EQ 50%를 표시한다.
- `EXTERNAL_CONTINUATION` long은 discount에서만, short은 premium에서만 준비한다.
- continuation 방향의 POI가 반대 절반에 있으면 OB가 선명해도 정보로만 남기고 주문 권한을 부여하지 않는다.
- `INTERNAL_ROTATION`은 range의 반대편 외부 유동성까지 확대하지 않고 현재 range 안의 첫 내부 objective에서 끝낸다.
- premium/discount 위치는 단독 진입 신호가 아니다. 올바른 위치에 있더라도 root OB, causal refinement, mature sweep, M1 trigger가 모두 필요하다.

## 4. HTF root OB

최초 포지션의 원인은 사전에 존재하는 `H1`, `M30`, 또는 `M15` root OB여야 한다.

root OB는 다음을 모두 설명해야 한다.

1. 의미 있는 스윙 고점 또는 저점 부근에 있다.
2. 그 위치에서 실제 displacement가 출발했다.
3. 그 displacement가 의미 있는 구조 전달이나 몸통 돌파를 만들었다.
4. 아직 완전히 소비되거나 구조적으로 무효화되지 않았다.
5. 현재 목적 유동성 방향과 연결되는 이유를 말로 설명할 수 있다.

다음은 root OB가 아니다.

- 화면에서 가장 가까운 반대색 캔들
- M1 반응을 보고 사후에 선택한 HTF 캔들
- 구조 전달을 만들지 않은 임의의 캔들 묶음
- 단순히 FVG와 겹치는 캔들
- 이미 여러 번 완전히 체결된 OB
- HTF FVG 자체

HTF FVG는 가격 전달의 비효율을 보여줄 수 있지만 **최초 포지션의 root source가 될 수 없다.**

## 5. causal LTF OB refinement

HTF root OB를 찾았다고 바로 M1으로 내려가지 않는다. 최소 하나의 causal child OB가 필요하다.

refinement는 H1/M30/M15/M5를 내려가며 찾되 다음을 모두 만족해야 한다.

1. 부모 OB와 같은 방향이다.
2. 부모 OB 안에 있거나, 부모 스윙의 바로 인접한 하위 구조다.
3. 부모와 같은 가격 사건 및 같은 displacement를 설명한다.
4. 형성 시각이 부모 파동의 원인 구간과 일치한다.
5. 하위 OB의 displacement가 실제 하위 구조 전달을 만들었다.
6. 부모와 자식의 연결을 차트에 함께 표시할 수 있다.

가격만 겹치거나 나중에 우연히 생긴 하위 OB는 refinement가 아니다.

유효한 refinement가 확인되면 마지막 causal child OB가 정밀 진입과 SL geometry를 담당한다. 이때만 넓은 HTF OB 전체가 아니라 하위 OB로 SL 폭을 줄일 수 있다.

하위 OB가 여러 개로 갈라지고 어느 것이 원인인지 비교할 수 없으면 가장 좁은 것을 임의로 선택하지 않는다. 더 높은 child OB를 유지하거나 비매매한다.

## 6. M1 trigger 허용 조건

다음 항목이 모두 사전에 완료되기 전에는 M1 trigger를 찾지 않는다.

- 목적 유동성 동결
- map 방향과 scenario scope 동결
- HTF root OB 동결
- causal LTF refinement 경로 동결
- source/refined OB 무효화 가격 동결
- 가격이 refined OB에 실제 접촉

접촉 뒤의 기본 trigger chain은 다음과 같다.

```text
refined OB 접촉
-> 그 맥락 안에 사전 형성된 유동성 관통
-> 가격 회복
-> 진행 중 M1 추세의 의미 있는 live swing을 몸통 종가로 돌파
-> CHoCH displacement가 만든 causal execution OB
-> 이후 첫 retest
```

### sweep 대상 유동성의 성숙도

- sweep 대상 고저점은 **최종 sweep excursion이 시작되기 전에 이미 존재**해야 한다.
- 그 고저점에서 최소 한 번의 완결된 반응이 나와 live swing 또는 실제 stop pool로 확인돼야 한다.
- 현재 reaction leg가 방금 만든 고저점을 같은 leg 안에서 즉시 `BSL/SSL sweep 완료`로 선언하지 않는다.
- reaction 중 생긴 고저점은 가격이 충분히 이탈해 구조가 확정된 뒤, 별도의 후속 접근이 그것을 관통하고 회복할 때만 sweep 근거가 될 수 있다.
- 하나의 진행 중 wick이 고점을 만들고 다시 밀렸다는 이유만으로 `final sweep`이라 부르지 않는다.

### 의미 있는 CHoCH

- wick 돌파가 아니라 몸통 종가 돌파여야 한다.
- 하락 중 long이라면 실제 correction을 지배하던 반응 고점을 깨야 한다.
- 상승 중 short이라면 실제 correction을 지배하던 반응 저점을 깨야 한다.
- 한두 캔들의 미세 pivot이나 같은 방향의 내부 흔들림은 CHoCH가 아니다.
- M1 CHoCH가 선명해도 HTF root OB와 refinement가 없으면 진입하지 않는다.
- M1 CHoCH가 M5 correction을 지배하던 swing을 깨지 못했다면 HTF delivery 전환으로 승격하지 않는다.
- M5가 명확히 반대 방향으로 전달 중인데 M1에서만 짧은 반등 CHoCH가 발생하면 우선 내부 correction으로 분류한다.

## 7. FVG의 제한된 역할

FVG를 보았다는 이유로 최초 시나리오를 만들지 않는다.

### 최초 포지션 기본형

- source와 SL 근거는 HTF-to-LTF OB lineage다.
- M1 CHoCH FVG는 displacement 확인 정보다.
- 기본 최초 진입은 마지막 causal execution OB의 retest다.
- CHoCH FVG가 선명하더라도 누락된 root OB 또는 refinement를 대신할 수 없다.

### 별도 연구형

다음은 기본 스승님식 최초 진입에 섞지 않는다.

- CHoCH FVG 자체를 최초 entry zone으로 쓰는 변형
- HTF FVG를 source로 쓰는 변형
- 동결된 HTF owner·objective·OB lineage 없이 delivery FVG만 추격하는 변형
- FVG inversion 진입

### 미체결 원주문의 Delivery FVG 대체 진입

기다리던 refined OB 주문이 체결되지 않고 가격이 목적지 방향으로 출발했다면 시장가로 추격하지 않는다. 다음 조건을 모두 만족할 때만 `DELIVERY_FVG_REPLACEMENT`를 허용한다.

1. 원래 H1/M30 owner, 방향, scenario scope, objective가 변하지 않았다.
2. 원래 HTF root OB와 causal child OB lineage가 주문 전에 이미 동결돼 있었다.
3. 원래 OB 주문은 아직 체결되지 않았고, 해당 source가 무효화되지 않았다.
4. M5 또는 M1의 목적지 방향 displacement가 protected swing을 몸통으로 돌파하거나 기존 delivery를 명확히 재확인했다.
5. 그 displacement가 fresh FVG를 만들었고, 해당 displacement의 causal OB와 protected swing을 식별할 수 있다.
6. 진입은 그 FVG의 **첫 되돌림**만 사용한다. 이미 여러 번 접촉했거나 몸통으로 무효화된 FVG는 사용하지 않는다.
7. entry와 objective 사이에 더 가까운 미소진 liquidity가 새로 생기지 않았다.

- 기존의 깊은 OB pending은 delivery가 확인되는 즉시 취소한다. 원주문과 대체 주문을 동시에 남기지 않는다.
- 기본 entry는 fresh FVG의 방향별 proximal boundary다. FVG 안의 causal M1 OB가 같은 displacement를 명확히 설명하면 그 OB의 첫 retest로 정밀화할 수 있다.
- SL은 fresh FVG distal 하나가 아니라 displacement causal OB distal, trigger protected swing, 원래 final child 무효화 중 정상 되돌림을 모두 벗어나는 가장 보수적인 경계 바깥에 둔다.
- 주문 생성 시점의 `max(actual spread, broker stops level, 1 tick)` buffer를 그 구조 경계 바깥에 더한다. FVG distal은 entry zone의 상태와 through-delivery를 판정하는 정보이지 hard SL의 단독 권한이 아니다.
- 체결 시점 spread가 동결 buffer보다 커졌다면 SL을 사후로 넓히지 않고 주문을 취소한다.
- TP는 처음 동결한 동일 objective다. FVG 진입으로 바뀌었다는 이유로 목표를 더 멀리 연장하지 않는다.
- 첫 retest 전에 objective가 소진되거나 owner가 바뀌거나 FVG/causal OB/protected swing이 무효화되면 주문을 취소한다.
- 첫 되돌림 없이 목적지까지 직행하면 `MISSED - NO DELIVERY RETEST`로 기록하고 보내준다.

### 기존 포지션의 Delivery FVG 추가진입

기존 최초 포지션이 이미 동결된 TP 방향으로 전달 중이고 진입가를 넘어 유리하게 진행된 뒤, 새 구조 전달과 fresh FVG가 만들어진 경우의 첫 retest만 `DELIVERY_FVG_ADDON` 후보가 될 수 있다. 추가진입도 새 displacement·fresh FVG·causal OB·protected swing이 전부 확인돼야 하며, 동일 physical FVG/retest는 하나의 execution chain만 만든다. 각 addon은 독립 `1R`이고 최초 포지션과 같은 objective family를 사용한다.

기본 HTF-to-LTF OB 진입과 Delivery FVG replacement의 재현성이 독립적으로 확인되기 전까지 `DELIVERY_FVG_ADDON` 주문 권한은 비활성으로 둔다. 비활성 상태에서는 후보를 탐색하거나 API 심사를 요청하거나 위험 슬롯을 점유하지 않는다.

## 8. Entry, SL, TP

### Entry

- 최초 진입은 final causal execution OB의 방향별 proximal boundary를 기본으로 한다.
- 이미 지나간 첫 retest에 사후 진입하지 않는다.
- 가격이 POI에서 출발했다면 시장가로 추격하지 않는다. 원래 시나리오가 유지되고 목적지 방향 displacement가 새 fresh FVG를 만든 경우에만 제7장의 `DELIVERY_FVG_REPLACEMENT`를 검토한다.

### 체결 전 pending order 생명주기

주문 상태는 다음 순서로만 진행한다.

```text
PREPARED: objective / map / root / child 동결
-> ARMED: refined OB 실제 접촉
-> TRIGGERED: mature sweep + M1 CHoCH + execution OB 확정
-> PENDING: 이후 retest 주문 대기
-> FILLED 또는 CANCELED
```

- `PENDING`은 무기한 유효하지 않다. 새로운 H1 또는 M15 확정봉이 생길 때마다 owner, scope, objective, source freshness, trigger protected swing을 다시 승인한다.
- 주문 생성 뒤 한 번이라도 H1/M15 map이 달라졌는데 재승인 기록이 없으면 체결하지 않는다.
- objective 선도달, root/child 몸통 무효화, trigger protected swing 파괴, POI 완전 소비, opposing owner 확정 중 하나가 발생하면 즉시 `CANCELED`다.
- trigger 뒤 가격이 entry zone을 떠나 새로운 HTF leg를 만든 경우, 과거 M1 trigger를 다음 세션까지 재사용하지 않는다. 새로운 진입에는 새로운 sweep부터 execution OB까지 전 체인이 필요하다.
- entry와 trigger invalidation 또는 SL을 같은 접근 displacement가 함께 관통하면 정상 retest가 아니라 `through-delivery`로 분류한다. historical tick이 별도의 진입-반응 순서를 증명하지 못하면 유효한 스승님식 체결로 승인하지 않는다.
- 주문 체결 시점의 시나리오를 주문 생성 시점의 설명만으로 정당화하지 않는다. **마지막 재승인 시각**을 원장에 반드시 기록한다.

### SL

SL은 단순 M1 sweep extreme 하나로 정하지 않는다.

`HTF_OB_REACTION` 최초 진입에는 다음 구조를 적용한다.

- final causal child OB의 distal
- 해당 OB를 방어하는 protected swing
- 유효한 sweep extreme
- 현재 시나리오를 실제로 무효화하는 구조 가격

위 가격 중 정상적인 되돌림 경로를 모두 벗어나는 가장 보수적인 경계 바깥에 SL을 둔다. 유효한 child refinement가 같은 부모 원인을 증명할 때만 HTF OB 전체가 아닌 child 구조를 시나리오 무효화로 사용할 수 있다.

`DELIVERY_FVG_REPLACEMENT`에는 제7장의 causal structural invalidation을 적용한다. delivery causal OB, trigger protected swing, 원래 final child 무효화 중 가장 보수적인 경계를 hard SL 계산에 포함한다. FVG distal은 단독 hard SL 근거가 아니다. `DELIVERY_FVG_ADDON`은 별도 승격 전까지 주문 권한이 없다.

- hard SL buffer는 `actual spread`, `broker stops level`, `1 tick` 중 최댓값보다 작을 수 없다.
- long SL은 chart의 Bid 기준 하단 체결을, short SL은 Ask 기준 상단 체결을 반영한다. 특히 short는 chart high에 spread를 더하지 않은 SL을 금지한다.
- sweep extreme 자체에 SL을 붙이지 않는다. 먼저 final sweep이 확정된 뒤 그 extreme 바깥에 execution buffer를 둔다.
- buffer 때문에 risk가 커지면 lot을 줄인다. 계획 R을 키우려고 SL을 spread 안쪽이나 micro pivot 바로 바깥으로 당기지 않는다.

SL이 너무 멀어 손익비가 나쁘다면 SL을 M1 pivot으로 억지로 줄이지 않는다. 더 정밀한 causal refinement를 찾거나 거래하지 않는다.

### TP

- 진입 전에 동결한 동일한 objective family를 사용하며, Entry·SL 확정 시 그 family에 결정론적 선택 규칙을 적용해 TP 하나를 확정한다.
- 유동성보다 더 멀리 임의 buffer를 두지 않는다.
- RR fallback, 최대 R 제한, 최소 R을 맞추기 위한 TP 이동을 사용하지 않는다.
- TP가 지나치게 멀다고 느껴지면 목적 유동성과 scenario scope를 다시 검토한다.
- EXTERNAL_CONTINUATION TP는 H1/M30 외부 방향의 다음 미소진 external liquidity다. 그 사이의 internal liquidity는 주문 전에 중간 전달 지점으로 기록하되 TP로 대체하지 않는다.
- INTERNAL_ROTATION TP는 현재 dealing range 안의 첫 미소진 내부 유동성이다. H1 external body break가 없으면 그 너머 external liquidity까지 목표를 확장하지 않는다.
- EXTERNAL_REVERSAL TP는 H1/M30 protected swing의 몸통 파괴와 새 owner 확인 뒤 선택한 새 방향 external liquidity다. M1 반전만으로 이 계약을 사용할 수 없다.
- 목표 wick을 정확히 맞히는 대신 체결 안정성을 위해 front-run할 경우, 주문 전에 선언하고 actual spread 또는 1 tick 안쪽 범위로만 제한한다. 유동성 바깥으로 TP를 더 멀리 두는 것은 금지한다.

### 체결 후

- 최초 SL 또는 TP가 결과를 판정한다.
- 공포, 수익 보호 욕구, 중간 M1 반대 신호로 임의 청산하지 않는다.
- 시간 만료, 본절 이동, 부분 익절은 별도 승인 전까지 사용하지 않는다.

## 9. 즉시 비매매 조건

다음 중 하나라도 해당하면 거래하지 않는다.

1. 목적 유동성이 명확하지 않다.
2. 목적지가 이미 소진됐다.
3. H1/M30에서 외부와 내부 구조를 구분하지 못했다.
4. 의미 있는 swing 근처의 HTF root OB가 없다.
5. source가 HTF FVG뿐이다.
6. causal child OB를 최소 하나 찾지 못했다.
7. parent-child가 가격만 겹치고 같은 displacement를 설명하지 못한다.
8. 가격이 refined OB에 아직 도달하지 않았고, 유효한 `DELIVERY_FVG_REPLACEMENT` 계약도 완성되지 않았다.
9. OB 접촉 전에 M1 trigger부터 찾았다.
10. sweep 대상 유동성이 사전에 존재하지 않았다.
11. CHoCH가 의미 있는 live swing이 아니라 micro pivot만 돌파했다.
12. 진입 retest가 이미 지나갔다.
13. 구조 무효화 바깥 SL을 설명할 수 없다.
14. TP를 정확한 유동성 가격으로 설명할 수 없다.
15. 필수 구조를 차트에 표시할 수 없다.
16. continuation long이 active range의 premium에 있거나 continuation short이 discount에 있다.
17. INTERNAL_ROTATION에서 entry와 objective 사이의 더 가까운 성숙한 internal liquidity를 건너뛰었거나, EXTERNAL_CONTINUATION에서 중간 internal liquidity를 원장에 기록하지 않았다.
18. sweep 대상 고저점이 현재 reaction leg에서 방금 생겼고 아직 완결된 반응으로 성숙하지 않았다.
19. pending order 뒤 새 H1/M15 확정봉이 생겼지만 마지막 재승인 기록이 없다.
20. M5는 반대 방향 correction을 유지하는데 M1 micro CHoCH만으로 전환을 선언했다.
21. entry 접근 displacement가 zone과 invalidation을 동시에 관통한다.
22. short의 Ask spread 또는 long/short의 broker stops level을 반영한 hard SL을 계산하지 않았다.

`FVG가 보임`, `M1이 강하게 움직임`, `곧 반전할 것 같음`, `최근 고저점 sweep`은 누락된 조건을 보충하지 못한다.

## 10. 블라인드 재생 규율

1. H1/M30에서 map, objective, root OB를 먼저 동결한다.
2. M30/M15/M5에서 refinement 경로를 차트에 표시한다.
3. 가격이 refined OB에 접근하기 전에는 M1을 보지 않는다.
4. root OB 접근 뒤에는 M15/M5로 refinement와 correction을 확인하고, refined OB 실제 접촉 뒤에만 M1을 한 봉씩 확인한다.
5. **사건 기반 판단 게이트:** map을 만들 때 `root OB 접근 경계 / refined OB 접근 경계 / objective / source 무효화 / protected swing 몸통 돌파` 가격을 먼저 동결한다. 그 뒤에는 이 중 가장 먼저 발생하는 사건까지 빠르게 재생할 수 있으며, 사건에서 멈춘 뒤 `주문 동결 / 대기 / 비매매`를 기록하기 전에는 더 진행하지 않는다.
6. 지나간 진입을 사후 주문으로 복원하지 않는다.
7. 주문 전에 entry, SL, TP와 모든 원인 ID를 기록한다.
8. 거래 결과를 본 뒤 OB, liquidity, CHoCH, SL, TP를 다시 그리지 않는다.
9. 재생 제어 오류로 미래 데이터가 보이면 해당 세션을 즉시 폐기한다.
10. 코드, 지표, 기존 후보 원장, 이후 가격은 매매 판단에 사용하지 않는다.
11. 원래 OB가 미체결된 채 delivery가 출발하면 시장가로 따라가지 않는다. 기존 pending을 취소하고, 목적지 방향 displacement가 만든 fresh FVG의 첫 되돌림이 실제로 생길 때만 대체 주문을 준비한다.
12. `DELIVERY_FVG_REPLACEMENT`를 준비할 때도 해당 FVG가 나타난 시점까지의 데이터만 보고 owner·objective 유지, 구조 전달, causal OB, protected swing을 다시 동결한다.
13. 재생을 빨리 넘겨 후보를 뒤늦게 발견한 것은 시장의 `미체결`이나 정상적인 `놓친 거래`가 아니라 **분석자 재생 절차 실패**다. 해당 거래일은 블라인드 성과 통계에서 제외하고 새 미사용 기간으로 다시 검증한다.
14. 넓은 시간 구간의 OHLC를 한꺼번에 출력하거나 이후 봉을 먼저 열어 본 뒤 과거 시점의 판단을 복원하는 행위를 금지한다. 단, 사전에 동결한 사건 가격 중 하나에 도달할 때까지만 재생기가 자동 탐색하는 것은 허용한다. 이때 사건 이전의 이후 차트는 판단자에게 노출하지 않는다.
15. `PREPARED` 상태에서 가격이 root OB와 충분히 떨어져 있고 동결된 무효화 사건도 없다면 H1 봉마다 같은 분석을 반복하지 않는다. root OB 접근 시 M15/M5로 전환하고, refined OB 실제 접촉 뒤에만 M1을 한 봉씩 진행한다.
16. 빠른 재생 중 정지 조건은 사전에 가격으로 선언한 사건에 한정한다. 재생 결과를 본 뒤 더 유리한 POI나 정지 가격을 소급해서 추가할 수 없다.

## 11. 주문 전 필수 증거

아래 항목을 차트와 원장에 모두 남기기 전에는 주문하지 않는다.

- map TF와 scenario scope
- active dealing range, EQ, 현재 premium/discount 위치
- 정확한 목적 유동성 가격
- entry와 objective 사이의 더 가까운 competing liquidity 검토 결과
- HTF root OB의 시간, 상단, 하단
- refinement 경로와 각 child OB의 시간, 상단, 하단
- parent-child가 같은 displacement인 이유
- refined OB 접촉 시각
- sweep 대상 유동성, 그 유동성이 성숙한 시각, final sweep extreme
- M1 CHoCH가 돌파한 live swing
- final execution OB
- entry, child distal, protected swing, scenario invalidation, actual spread, broker stops level, hard SL
- TP와 해당 유동성의 출처 및 scenario scope와의 일치
- pending order의 마지막 H1/M15 재승인 시각
- execution model이 `HTF_OB_REACTION`, `DELIVERY_FVG_REPLACEMENT`, `DELIVERY_FVG_ADDON` 중 무엇인지
- 대체 진입이라면 원래 OB 주문의 가격·취소 시각, delivery가 돌파한 protected swing, fresh FVG의 형성 시각·범위·첫 retest 여부, delivery causal OB distal과 protected swing으로 계산한 local hard SL, 원래 final child distal이 hard SL에서 제외됐다는 기록

차트에서 이 연결을 사용자가 한눈에 확인할 수 없다면 내가 원인을 제대로 선택하지 못한 것으로 간주한다.

## 12. 성과 분류

### 스승님식 유효 거래

모든 필수 증거가 주문 전에 동결된 거래만 해당한다. 이런 거래의 SL은 결과가 아니라 `시장 불확실성`으로 분류할 수 있다.

### 프로토콜 위반 거래

다음은 PnL과 무관하게 스승님식 성과에서 제외한다.

- root OB 누락
- causal refinement 누락
- 내부 유동성을 외부 유동성으로 승격
- HTF FVG를 standalone source로 사용
- M1 trigger-first 진입
- micro CHoCH 진입
- stale pending order 체결
- 성숙하지 않은 reaction 고저점을 sweep으로 사용
- premium continuation long 또는 discount continuation short
- INTERNAL_ROTATION 목표를 외부 유동성까지 확대
- actual Bid/Ask spread 안쪽 SL
- 사후 선택한 entry/SL/TP
- 필수 차트 증거 누락
- 동결된 HTF 시나리오 없이 fresh FVG만 보고 만든 `DELIVERY_FVG_REPLACEMENT`
- 기존 OB pending과 Delivery FVG 대체 주문을 동시에 유지한 거래
- 두 번째 이후 FVG 접촉을 첫 retest로 소급한 거래

TP에 도달한 프로토콜 위반 거래도 성공 사례가 아니다. SL에 도달한 유효 거래도 규칙을 사후 변경할 근거가 아니다.

## 13. 최근 실패의 재발 방지

다음 행동은 이미 성과 급락을 만든 실패로 확인됐으며 반복하지 않는다.

- 3359 내부 저점을 H1 외부 SSL로 잘못 승격하고 M1 FVG long을 만든 행동
- 명확한 HTF OB 없이 M1 CHoCH로 시나리오의 빈칸을 채운 행동
- M15 FVG를 HTF root source처럼 사용한 행동
- 스승님 영상에 없는 일반적인 `range breakdown/acceptance` 해석으로 거래를 허가한 행동
- POI 접근을 빠른 재생으로 지나친 뒤 중간 가격에서 새 근거를 만든 행동
- parent OB와 child OB를 차트에 표시하지 못한 상태에서 주문을 계속한 행동
- 손실 뒤 규칙을 즉석에서 바꾸고 같은 주의 결과에 다시 적용한 행동
- 2025-08-19 long처럼 M1 trigger 후 13시간 동안 map을 재승인하지 않고 오래된 pending order를 bearish displacement에 체결한 행동
- 2025-08-21 첫 long처럼 H1 dealing range premium에서 이미 대부분 전달된 bullish leg의 continuation을 추격한 행동
- 2025-08-21 short처럼 reaction 중 방금 생긴 3347.48 고점을 final BSL sweep으로 조기 확정하고 실제 3347.99 sweep 전에 진입한 행동
- short SL을 chart high에만 맞추고 Ask spread를 누락한 행동
- INTERNAL_ROTATION인데 더 가까운 3325.03 SSL을 건너뛰고 3313.89 external SSL까지 TP를 확대한 행동

## 14. 주문 직전 최종 선언

주문 전 다음 문장을 빈칸 없이 답해야 한다.

```text
목적 유동성은 ________ 이다.
H1/M30 map과 scenario scope는 ________ 이다.
active dealing range는 ________ ~ ________, EQ는 ________, 현재 위치는 premium / discount 중 ________ 이다.
entry와 objective 사이의 더 가까운 미소진 liquidity는 ________ 이며, 이를 건너뛰지 않는 이유는 ________ 이다.
root OB는 ________ TF의 ________ 가격 영역이다.
그 OB의 causal child는 ________ TF의 ________ 가격 영역이다.
두 OB가 같은 원인인 이유는 ________ 이다.
가격은 ________ 시각에 refined OB를 접촉했다.
유동성 ________ 은 ________ 시각에 성숙했고, ________ 시각에 final sweep됐다.
M1은 ________ live swing을 몸통으로 돌파했다.
final execution OB는 ________ 이다.
Entry는 ________, hard SL은 ________, TP는 ________ 이다.
actual spread는 ________, broker stops level은 ________, SL buffer는 ________ 이다.
SL이 시나리오를 무효화하는 이유는 ________ 이다.
TP가 목적 유동성인 이유는 ________ 이다.
pending order의 마지막 H1/M15 재승인 시각은 ________ 이다.
execution model은 HTF_OB_REACTION / DELIVERY_FVG_REPLACEMENT / DELIVERY_FVG_ADDON 중 ________ 이다.
대체 진입이라면 원래 OB 주문 취소 시각은 ________, delivery가 돌파한 protected swing은 ________, fresh FVG와 첫 retest는 ________, delivery-local SL 근거는 ________ 이며 원래 final child distal은 hard SL 계산에서 제외됐다.
```

한 항목이라도 답할 수 없으면 주문하지 않는다.

## 15. 한 문장 원칙

> M1 trigger로 거래의 원인을 찾지 않는다. 먼저 HTF swing OB와 causal LTF OB refinement로 시나리오를 완성하고, M1은 그 시나리오가 실제로 반응했는지만 확인한다.

## 16. 2025-08-18~22 실패 회귀 검사

다음 주간 매매를 시작하기 전에 아래 세 사례가 현재 규칙으로 반드시 거절되거나 올바른 시점까지 대기되는지 확인한다.

### 회귀 A: stale pending long

- trigger 뒤 13시간이 지나고 H1/M15 map이 달라졌는데도 주문이 남아 있으면 실패다.
- bearish displacement가 entry와 SL을 같은 접근에서 관통하면 유효 retest로 처리해서는 안 된다.
- 기대 결과: `CANCELED - MAP_NOT_REAUTHORIZED` 또는 `CANCELED - SOURCE_EPISODE_ENDED`.

### 회귀 B: premium continuation long

- H1 range `3311.35~3351.95`, EQ `3331.65`에서 `3341.62` long을 continuation으로 승인하면 실패다.
- M5 correction이 하락인데 M1 bullish micro CHoCH만으로 H1 continuation을 선언하면 실패다.
- 기대 결과: `NO_TRADE - WRONG_PD_HALF` 및 `NO_TRADE - M1_INTERNAL_ONLY`.

### 회귀 C: premature short before final sweep

- reaction 중 새로 생긴 `3347.48`을 즉시 final BSL sweep으로 인정하면 실패다.
- `3347.99` 후속 sweep과 그 뒤 body CHoCH가 나오기 전에는 short를 허가하지 않는다.
- short SL은 final sweep extreme과 Ask spread 바깥이어야 한다.
- scenario가 INTERNAL_ROTATION이면 첫 TP는 `3325.03` 계열이며 `3313.89`로 확대하지 않는다.
- 기대 결과: 최초 short는 `WAIT - LIQUIDITY_NOT_MATURE`; final sweep 뒤 새 chain만 별도 승인 가능.

이 세 회귀 중 하나라도 통과하지 못하면 새로운 주간 블라인드 매매를 시작하지 않는다.

## 17. 2025-08-25~29 목적 유동성 회귀 검사

scenario scope와 TP 종류를 혼동하지 않기 위해 다음 세 사례를 고정 회귀로 사용한다.

### 회귀 D: external continuation을 내부 TP로 축소하지 않기

- 2025-08-27 long은 H1/M30 외부 상승 구조와 같은 방향의 `EXTERNAL_CONTINUATION`이다.
- `3384.41` 내부 BSL은 `INTERMEDIATE_DELIVERY`이며 최종 TP가 아니다.
- 당시 동결할 external objective는 `3394.14` BSL 계열이다.
- 기대 결과: entry `3376.72`, SL `3372.70`, external TP `3394.14`; 내부 BSL 도달만으로 청산하지 않는다.

### 회귀 E: external continuation의 중간 유동성 선도달

- 2025-08-29 낮 long은 H1/M30 상승 delivery가 유지된 `EXTERNAL_CONTINUATION` 후보다.
- `3408.72`, `3411.16` 계열 내부 BSL은 중간 전달 지점이며, 사전에 동결한 external objective `3422.95`를 대체하지 않는다.
- owner·root/child lineage·pending 재승인이 유지되는 동안 내부 BSL 소진만으로 주문을 취소하면 실패다.
- 기대 결과: 기존 execution OB 주문이 Ask 기준 `3407.29`에 체결되면 구조 SL 바깥과 external TP `3422.95`로 판정한다.

### 회귀 F: internal rotation을 외부 TP로 확대하지 않기

- 2025-08-29 저녁 short은 H1/M30 외부 상승 구조 안의 `INTERNAL_ROTATION`이다.
- 첫 internal SSL `3442.45`가 올바른 최종 objective이며 external SSL `3404.22`로 확대하지 않는다.
- 올바른 M1 execution OB retest 전에 `3442.45`가 소진되면 주문은 취소다.
- 기대 결과: `CANCELED - INTERNAL_OBJECTIVE_REACHED_BEFORE_ENTRY`; 외부 TP를 적용해 19:34에 체결시키고 SL로 만드는 것은 scope 위반이다.

회귀 D~F는 모든 거래의 TP를 외부 또는 내부로 일괄 통일하지 않고, 주문 전에 동결한 scenario scope가 TP 종류를 결정하는지 확인한다.

## 18. Ground Truth V2 및 자동 판단 실행 계약

이 절은 앞 절의 전략 의미를 바꾸지 않고, 정답지·Gemini replay·live shadow가 같은 사건과 위험 상태를 다루도록 실행 경계를 고정한다.

### 18.1 후보와 objective family

- 거래 후보는 raw M1 확정봉에서 집계한 H1/M30/M15/M5 사건 원장으로만 만든다. oracle, move index, 결과가 보이는 미래 구간은 후보 발견에 사용할 수 없다.
- root 후보는 모든 `마지막 반대색 원인 캔들 -> displacement -> 몸통 구조 전달` episode를 형성 시점부터 소비·무효화 시점까지 영구 ID로 보존한다.
- liquidity 후보는 H1/M30의 external swing·반복 방어·range edge·reaction trap과 M15 이상 internal liquidity를 형성 시점부터 소진 시점까지 추적한다. 단순 2-bar pivot은 모델이 검토할 원시 후보일 뿐 자동으로 목적 유동성이 되지 않는다.
- 후보 수나 prompt 크기 때문에 family를 삭제하지 않는다. 결정론적 paging을 사용하고, page별 입력 family ID와 응답 family ID의 집합이 정확히 일치해야 한다.
- PLAN은 같은 owner·scope·lineage의 순서가 고정된 objective family를 동결한다. 모델은 family 구성원의 가격이나 순서를 다시 쓰지 않는다.
- objective family의 장기 이력 구간에는 현재가에서 방향상 가장 가까운 미소진 H1 liquidity를 최대 `2개`만 포함한다. 장기 M30 이하 후보는 포함하지 않으며, 현재 구조 objective가 주문 기하상 적격이면 장기 후보는 비활성 상태를 유지한다.
- 정답 거래의 최초 판단 가능 시각 packet에 root·child·objective family 역할 ID가 하나라도 없으면 `MODEL_MISS`가 아니라 `ENGINE_CANDIDATE_MISS`다.

### 18.2 다중 scenario lane과 위험 슬롯

- 전역 상태는 `ownerEpoch`, 독립 `scenarioLanes`, `orders`, `positions`, `executionChains`로 나눈다.
- PREPARED·TRIGGER_WATCH lane은 위험 슬롯을 사용하지 않는다. `PENDING + FILLED`의 합계만 최대 `3`이며 각 주문은 독립 `1R`이다.
- 슬롯은 주문 생성 시각 순으로 배정한다. 같은 시각이면 root TF `H1 > M30 > M15`, source 인식 시각, signal ID 순으로 정한다.
- 열린 pending 또는 position과 반대 방향의 새 주문은 금지한다. 반대 watch lane은 유지할 수 있지만 차단되어 지나간 첫 retest를 나중에 복원하지 않는다.
- 같은 physical FVG·첫 retest는 하나의 execution ID만 가진다. 서로 다른 lineage가 동일 execution을 주장하고 하나로 해소되지 않으면 `UNRESOLVED_LINEAGE`다.
- SL 이후에도 source·owner·objective family가 유효하면 family 자체를 retire하지 않는다. 새 sweep부터 execution zone까지 완전한 새 execution chain만 재진입할 수 있다.
- TP 또는 최종 objective 소진 뒤에는 그 family를 종료한다.

### 18.3 API 지연과 체결 순서

- API 요청 중 새로 확정된 M1 봉과 broker tick은 순서대로 버퍼링한다.
- 모델 응답과 로컬 승인 전에 첫 retest가 지나가면 `MISSED_API_LATENCY`, broker 주문 승인 전에 지나가면 `MISSED_ORDER_LATENCY`다. 사후 체결은 금지한다.
- historical M1만 있어 응답 분의 touch 순서를 판별할 수 없으면 `LATENCY_INTRABAR_AMBIGUOUS`로 제외한다.
- 최초 접근 봉이 Entry와 SL을 함께 관통하면 `THROUGH_DELIVERY`다. 체결 후 후속 봉에서 SL·TP가 동시에 닿으면 보수적으로 SL 우선이다.
- FVG 주문 생성 때 동결한 buffer보다 fill 시점 actual spread가 커지면 주문을 취소하고 SL을 사후 수정하지 않는다.

### 18.4 replay·live 일치와 운영 승인

- replay와 live는 같은 `advance_closed_m1_bar()` 순서로 후보 갱신, 모든 lane 진행, position 진행, PLAN scheduling, slot arbitration을 수행한다.
- live archive의 M1 gap은 MT5에서 backfill한다. 복구할 수 없는 gap이 있으면 API 판단과 주문을 모두 중지한다.
- 모든 주문은 idempotent client ID를 사용하며 재시작 때 in-flight request, lane, pending, position, objective family, latency 상태를 content hash로 복원한다.
- MT5 pending·position과 로컬 원장을 reconciliation하지 못하면 새 주문을 만들지 않는다.
- live shadow가 replay와 동일 사건 원장을 만든 뒤에만 DEMO 최소 lot 주문을 허용한다. 실계좌 주문은 별도 위험 비율과 운영 승인 전까지 비활성이다.

### 18.5 Ground Truth 완료 조건

- Ground Truth는 chronological 감사, 순서를 섞은 반증 감사, no-trade 구간 감사를 모두 통과해야 한다.
- 각 거래는 최초 판단 가능 시각의 역할 ID, objective family, execution chain, 주문 전 증거, 종료 결과를 append-only 원장에 남긴다.
- 모든 accepted 거래의 역할 ID가 당시 Gemini packet에 존재하는지 100% 검사한다.
- 정답지의 결과가 좋다는 이유로 거래를 채택하지 않고, 결과가 나쁘다는 이유로 룰을 만족한 거래를 삭제하지 않는다.
- render 수·파일 수·후보 수만으로 정답지 완료를 선언하지 않는다. 실제 의미 감사와 주문 생명주기 증거가 모두 있어야 한다.
