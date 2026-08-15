# 스승님식 수동 매매 절대 실행 계약

> **LEGACY / SUPERSEDED NOTICE**
>
> 이 문서는 과거 OB-first-entry manual-trading snapshot이다.
> 현재 deterministic Mentor EA V1 및 current V1 수동 판단의 authority는
> repository root `AGENTS.md`와 `docs/ea/EA_SPEC.md`다.
>
> 이 문서의 causal-execution-OB first entry,
> old SL geometry,
> INTERNAL_ROTATION order scope,
> stale-pending / periodic re-approval 규칙은
> current V1 주문 권한으로 사용하지 않는다.
>
> Historical research record로만 보존한다.

- 상태: `LEGACY / SUPERSEDED FOR CURRENT V1`
- 제정일: `2026-08-01`
- 적용 범위: 수동 차트 분석, 블라인드 리플레이, 데모 매매 판단

## 1. 문서의 지위

이 문서는 사용자가 `스승님식으로 매매해`, `스승님 방식으로 차트를 봐`, `직접 매매해`라고 요청했을 때
내가 가장 먼저 적용해야 하는 수동 매매 실행 계약이다.

- 전략 근거는 이 폴더에 정리된 스승님의 21개 영상으로 제한한다.
- 일반 ICT/SMC 지식, 기존 EA, V32, 점수 모델, 역설계 결과는 거래를 허가할 수 없다.
- 과거 문서나 기존 관행과 충돌하면 이 문서의 **비매매 원칙과 원인 우선순위**를 따른다.
- 모호한 부분을 임의의 ICT 개념으로 채우지 않는다. 설명할 수 없으면 `비매매`다.
- 결과가 수익이어도 이 계약을 위반한 거래는 스승님식 성과에 포함하지 않는다.

스승님식 매매의 필수 순서는 다음과 같다.

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

진입 방향을 생각하기 전에 현재 가격이 전달될 가능성이 있는 기존 유동성을 하나 정한다.

- 외부 추세 지속은 다음 외부 유동성을 목표로 한다.
- 내부회전은 외부 구조가 바뀌었다고 확대하지 않고, 처음 만나는 내부 유동성까지만 목표로 한다.
- 목적 유동성은 다른 참여자가 실제로 손절을 둘 만한 스윙, 반복 방어된 range edge, reaction trap 등이어야 한다.
- 단순 최근 pivot, 라운드 넘버, 이미 소진된 고저점은 목적 유동성이 아니다.
- 비교할 수 없는 목적지가 여러 개 남으면 하나를 임의로 선택하지 않고 기다린다.

TP는 해당 유동성의 실제 wick 가격에 둔다. 스윕 가능성을 무시하고 유동성보다 더 멀리 TP를 밀지 않는다.

### 3.2 외부와 내부를 혼동하지 않는다

- H1/M30 protected swing과 dealing range를 먼저 표시한다.
- 그 범위 안의 M15/M5 저점과 고점은 우선 내부 구조로 취급한다.
- 내부 저점 sweep만으로 H1 외부 반전을 선언하지 않는다.
- 외부 구조가 남아 있는데 M1 CHoCH가 발생해도 그것은 우선 내부 반응이다.

`내부 유동성 -> M1 CHoCH`를 `외부 반전`으로 승격하는 것은 금지한다.

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

### 의미 있는 CHoCH

- wick 돌파가 아니라 몸통 종가 돌파여야 한다.
- 하락 중 long이라면 실제 correction을 지배하던 반응 고점을 깨야 한다.
- 상승 중 short이라면 실제 correction을 지배하던 반응 저점을 깨야 한다.
- 한두 캔들의 미세 pivot이나 같은 방향의 내부 흔들림은 CHoCH가 아니다.
- M1 CHoCH가 선명해도 HTF root OB와 refinement가 없으면 진입하지 않는다.

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
- 기존 포지션 없이 delivery FVG만 추격하는 변형
- FVG inversion 진입

### 추가진입

기존 최초 포지션이 이미 동결된 TP 방향으로 전달 중이고, 강한 displacement가 새 FVG를 만든 경우의 첫 retest만 추가진입 후보가 될 수 있다. 기본 OB-refinement 방식의 재현성이 확인되기 전까지 추가진입은 비활성으로 둔다.

## 8. Entry, SL, TP

### Entry

- 최초 진입은 final causal execution OB의 방향별 proximal boundary를 기본으로 한다.
- 이미 지나간 첫 retest에 사후 진입하지 않는다.
- 가격이 POI에서 출발했다면 놓친 거래로 기록하고 추격하지 않는다.

### SL

SL은 단순 M1 sweep extreme 하나로 정하지 않는다.

- final causal child OB의 distal
- 해당 OB를 방어하는 protected swing
- 유효한 sweep extreme
- 현재 시나리오를 실제로 무효화하는 구조 가격

위 가격 중 정상적인 되돌림 경로를 모두 벗어나는 가장 보수적인 경계 바깥에 SL을 둔다. 유효한 child refinement가 같은 부모 원인을 증명할 때만 HTF OB 전체가 아닌 child 구조를 시나리오 무효화로 사용할 수 있다.

SL이 너무 멀어 손익비가 나쁘다면 SL을 M1 pivot으로 억지로 줄이지 않는다. 더 정밀한 causal refinement를 찾거나 거래하지 않는다.

### TP

- 진입 전에 정한 동일한 목적 유동성을 사용한다.
- 유동성보다 더 멀리 임의 buffer를 두지 않는다.
- RR fallback, 최대 R 제한, 최소 R을 맞추기 위한 TP 이동을 사용하지 않는다.
- TP가 지나치게 멀다고 느껴지면 목적 유동성과 scenario scope를 다시 검토한다.

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
8. 가격이 refined OB에 아직 도달하지 않았다.
9. OB 접촉 전에 M1 trigger부터 찾았다.
10. sweep 대상 유동성이 사전에 존재하지 않았다.
11. CHoCH가 의미 있는 live swing이 아니라 micro pivot만 돌파했다.
12. 진입 retest가 이미 지나갔다.
13. 구조 무효화 바깥 SL을 설명할 수 없다.
14. TP를 정확한 유동성 가격으로 설명할 수 없다.
15. 필수 구조를 차트에 표시할 수 없다.

`FVG가 보임`, `M1이 강하게 움직임`, `곧 반전할 것 같음`, `최근 고저점 sweep`은 누락된 조건을 보충하지 못한다.

## 10. 블라인드 재생 규율

1. H1/M30에서 map, objective, root OB를 먼저 동결한다.
2. M30/M15/M5에서 refinement 경로를 차트에 표시한다.
3. 가격이 refined OB에 접근하기 전에는 M1을 보지 않는다.
4. POI 접근 뒤에는 재생 속도를 낮추고 M1을 한 봉씩 확인한다.
5. 빠른 재생으로 trigger를 지나쳤다면 `놓친 거래`로 기록한다.
6. 지나간 진입을 사후 주문으로 복원하지 않는다.
7. 주문 전에 entry, SL, TP와 모든 원인 ID를 기록한다.
8. 거래 결과를 본 뒤 OB, liquidity, CHoCH, SL, TP를 다시 그리지 않는다.
9. 재생 제어 오류로 미래 데이터가 보이면 해당 세션을 즉시 폐기한다.
10. 코드, 지표, 기존 후보 원장, 이후 가격은 매매 판단에 사용하지 않는다.

## 11. 주문 전 필수 증거

아래 항목을 차트와 원장에 모두 남기기 전에는 주문하지 않는다.

- map TF와 scenario scope
- 정확한 목적 유동성 가격
- HTF root OB의 시간, 상단, 하단
- refinement 경로와 각 child OB의 시간, 상단, 하단
- parent-child가 같은 displacement인 이유
- refined OB 접촉 시각
- sweep 대상 유동성과 sweep extreme
- M1 CHoCH가 돌파한 live swing
- final execution OB
- entry, child distal, protected swing, scenario invalidation, hard SL
- TP와 해당 유동성의 출처

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
- 사후 선택한 entry/SL/TP
- 필수 차트 증거 누락

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

## 14. 주문 직전 최종 선언

주문 전 다음 문장을 빈칸 없이 답해야 한다.

```text
목적 유동성은 ________ 이다.
H1/M30 map과 scenario scope는 ________ 이다.
root OB는 ________ TF의 ________ 가격 영역이다.
그 OB의 causal child는 ________ TF의 ________ 가격 영역이다.
두 OB가 같은 원인인 이유는 ________ 이다.
가격은 ________ 시각에 refined OB를 접촉했다.
사전 유동성 ________ 을 sweep했다.
M1은 ________ live swing을 몸통으로 돌파했다.
final execution OB는 ________ 이다.
Entry는 ________, hard SL은 ________, TP는 ________ 이다.
SL이 시나리오를 무효화하는 이유는 ________ 이다.
TP가 목적 유동성인 이유는 ________ 이다.
```

한 항목이라도 답할 수 없으면 주문하지 않는다.

## 15. 한 문장 원칙

> M1 trigger로 거래의 원인을 찾지 않는다. 먼저 HTF swing OB와 causal LTF OB refinement로 시나리오를 완성하고, M1은 그 시나리오가 실제로 반응했는지만 확인한다.
