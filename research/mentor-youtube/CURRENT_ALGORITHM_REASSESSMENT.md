# 스승님 원전 기준 현재 알고리즘 재검토

## 결론

현재 V32는 **사건을 빠짐없이 기록하고 재현하는 연구 원장**으로는 강하다. 그러나
스승님의 매매법을 구현한 거래 의사결정기로는 지나치게 복잡하고 일부 핵심 의미가
달라졌다.

문제는 코드를 몇 줄 더 고치면 해결되는 버그가 아니다. 우리가 다음 두 목표를 한
엔진 안에서 동일하게 취급한 것이 근본 원인이다.

1. 모든 가격 사건의 계보와 상태 전이를 완벽히 증명하는 것
2. 스승님이 실제로 반복하는 간단한 시나리오를 찾아 거래하는 것

V32는 1번을 정교하게 만들었지만, 그 정교함이 2번의 우위를 만들지는 못했다.

## 1. 현재 확인된 사실

### 의미론 검증 성과

`POI_SEMANTIC_V32_S0_S1_RESULT.md` 기준:

- Q1 physical POI touch: `3,530`
- reaction episode: `3,288`
- CHoCH: `680`
- distinct BOS: `292`
- entry POI proposal: `584`
- later retest/fill candidate: `559`
- route/global audit violation: `0`
- `entryAuthorized=false`, `performanceEvaluated=false`

즉 V32는 사건 누락, 순서 뒤바뀜, 재시작 불일치 같은 의미론 문제를 매우 잘 막는다.

### 경제 재생 결과

`V32_Q1_ECONOMIC_RESULT.md` 기준:

- Q1 fill route `500`건이 실제 physical signal `64`개로 축약됨
- fresh objective와 단일 geometry가 남은 physical signal: `23`개
- execution family: `20`개
- 결과: `13 SL`, `4 TP`, `3 target-before-entry`
- 승률: `23.53%`
- Profit Factor: `0.684`
- 순손익: `-4.102R`

따라서 "V32에 이미 많은 것이 구현됐다"는 말은 맞지만, 구현된 대부분은 **인과
원장의 무결성**이다. 수익성 있는 방향·목적지·zone 선택이 완성됐다는 뜻은 아니다.

## 2. 스승님 방식과 어긋난 지점

### 2.1 사건 체인이 목적이 됐다

현재 설계는 대체로 다음 완전 체인을 요구한다.

`POI touch -> sweep -> CHoCH -> 별도 BOS -> BOS-owned FVG/OB -> retest`

스승님의 보수적 사례에는 이 체인이 등장하지만 모든 거래의 필수 계약은 아니다.
여러 영상에서는 `sweep -> CHoCH -> 그 전환의 FVG`로 진입한다. 별도 BOS를
기다리는 동안 이미 목적지에 가까워지거나 되돌림이 끝날 수 있다.

경제 결과에서 `target delivered before entry`와 과도한 후보 감소가 나타난 이유 중
하나다. 별도 BOS 모델은 기본형의 필수 단계가 아니라 확인형 전략으로 분리해야 한다.

### 2.2 유동성을 구조 ID로는 관리했지만 참가자 행동을 충분히 보지 못했다

스승님의 유동성 판단은 "어디가 최근 swing인가"보다 "왜 많은 사람이 그 바깥에
손절을 두는가"에 가깝다. 반복 방어, 박스, 추세선, 외부 고저점, 명확한 지지/저항이
그 이유다.

V32의 ranked swing과 liquidity object는 시간적 무결성은 있지만, 이 행동 맥락을
충분히 표현하지 못한 채 많은 physical event를 만든다. 그래서 touch `3,530`건이
많다는 사실 자체가 좋은 시나리오가 많다는 뜻이 되지 않는다.

### 2.3 FVG/OB의 인과 귀속을 너무 좁게 만들었다

맥락 없는 FVG/OB를 배제한 방향은 맞다. 그러나 특정 owner break나 BOS가 직접
생성했다는 하나의 계보만 허용하면 스승님이 실제로 보는 다음 관계를 잃을 수 있다.

- 상위 시간봉에는 유동성만 보이고 하위 시간봉에 같은 지점의 OB가 보이는 경우
- HTF 되돌림 한 캔들 안에서 M15/M5 source zone이 드러나는 경우
- CHoCH displacement의 FVG가 진입이고, 별도 BOS는 없는 경우
- 외부 구조는 유지되지만 내부 반전만 거래하는 경우

필요한 것은 모든 zone의 단일 소유자를 증명하는 것이 아니라, `현재 목적지와 반대편
liquidity sweep을 설명하는 같은 가격 사건인가`를 확인하는 것이다.

### 2.4 objective를 너무 일찍, 너무 멀리 고정했다

스승님은 시나리오를 세우면 SL/TP까지 인내하라고 하지만, TP의 등급은 확인된 구조의
등급에 맞춘다. 외부 전체 반전이 확인되지 않으면 내부 유동성까지만 보기도 하고,
첫 시나리오가 SL로 끝난 뒤 반대 추세가 확인되면 새로운 가까운 TP로 재설계한다.

따라서 owner 확정 시 먼 HTF objective를 무조건 동결하는 방식은 다음 문제를 만든다.

- 내부 반응인데 외부 목적지를 선택해 낮은 실현 가능성을 감수함
- 진입 체인이 완성되는 동안 objective가 먼저 소진됨
- 새로운 반대 시나리오가 생겨도 과거 목적지의 의미를 과도하게 보존함

objective는 **시나리오 생성 시점에 현재 확인된 구조 등급으로 선택**하고, 체결 뒤에는
고정한다. 시나리오가 SL로 종료되면 다음 시나리오는 새 objective를 가진다.

### 2.5 competing scenario 판정이 실제 판단보다 상태 수를 늘렸다

반대 구조를 무시하지 않는 취지는 맞다. 그러나 모든 비교 불가능성을 별도 state와
veto로 확장하면 거래 기회는 줄어도 방향 선택은 좋아지지 않는다.

스승님 방식의 충돌 판정은 더 단순하다.

- 외부 구조의 방향
- 현재 거래하려는 내부/외부 시나리오의 등급
- 출발 liquidity sweep 여부
- LTF 추세 전환 여부
- 목적지까지 먼저 만나는 반대 zone

이 다섯 요소로 방향을 설명할 수 없으면 대기한다. 수십 개의 품질 점수나 challenger
state가 우위를 대신하게 해서는 안 된다.

## 3. 유지할 것

V32를 폐기할 이유는 없다. 다음 기반은 그대로 재사용 가치가 높다.

- M1 공통 시계와 확정 캔들 집계
- 사건 발생 시각과 관측 가능 시각 분리
- look-ahead 방지
- swing, zone, touch, sweep의 영구 ID
- fresh/mitigated/consumed 상태 기록
- 동일 physical signal 중복 제거
- restart/replay 결정성
- spread와 실제 주문 geometry 계산
- 거래 근거와 결과 귀속 원장

이것들은 **연구 인프라**다. 매매법의 조건으로 전부 노출하지 않는다.

## 4. 제거하거나 분리할 것

### 기본 매매법에서 제거

- 고정 HTF owner
- 별도 BOS의 무조건 필수화
- BOS가 직접 만든 zone만 허용하는 단일 ownership
- 먼 HTF objective 조기 동결
- 모든 challenger가 해소될 때까지 기다리는 복잡한 veto
- 점수 합산과 품질 임계값
- 최대 R, RR fallback, 시간 종료

### 별도 변형으로 분리

- CHoCH 뒤 continuation BOS까지 기다리는 확인형
- FVG inversion 즉시 진입형
- OB-only 정밀 entry
- 부분 익절/본절 관리
- MTF 확인을 생략하는 sniper형

기본형과 변형을 한 엔진의 토글 조합으로 섞지 않는다. 각각 독립된 거래 모델로
기록해야 손익 차이를 해석할 수 있다.

## 5. 교체할 최소 시나리오 엔진

### 5.1 입력 객체

엔진이 거래 판단에 직접 사용하는 객체는 다섯 종류면 충분하다.

1. `structure_leg`: 외부/내부, 방향, protected high/low
2. `liquidity_pool`: 가격 범위, 손절이 모인 행동 근거, 등급, active/consumed
3. `context_zone`: FVG/OB 유형, fresh 상태, liquidity와의 가격 관계
4. `reversal_event`: sweep, CHoCH, optional BOS
5. `trade_scenario`: direction, source liquidity, entry zone, SL, objective

V32의 세부 event는 감사 원장에 남기되 거래 엔진은 이 다섯 객체의 설명 가능한
관계만 본다.

### 5.2 적응형 시간봉 탐색

고정 H1 anchor에서 아래로 내려가는 방식 대신 하나의 가격 사건을 중심으로 탐색한다.

1. H1/M30에서 외부 구조와 목적지 후보를 본다.
2. 출발 liquidity 주변의 원인 zone이 불명확하면 M30 -> M15 -> M5로 내려간다.
3. 여러 zone이 난립하면 반대로 한 단계 올려 공통 원인을 찾는다.
4. 같은 sweep과 displacement를 설명하는 가장 선명한 시간봉을 context frame으로 둔다.
5. M5/M1에서 전환을 확인하되, 작은 시간봉 노이즈가 상위 context를 바꾸게 하지 않는다.

시간봉 선택 결과는 `H1이라서 선택`이 아니라 `이 liquidity와 zone 관계를 유일하게
설명해서 선택`이라고 기록한다.

### 5.3 유동성 등급

단순 pivot rank 대신 행동 근거를 기록한다.

- `EXTERNAL`: 현재 외부 range의 고저점
- `DEFENDED`: 두 번 이상 의미 있게 방어된 고저점
- `RANGE_EDGE`: 눈에 보이는 횡보 상단/하단
- `TRENDLINE_CLUSTER`: 다수 접점이 있는 추세선 바깥 손절
- `INTERNAL`: 외부 구조 안의 중간 swing
- `SESSION`: 이전 세션/일 고저점, 보조 등급

여러 근거가 같은 가격대에 겹치면 하나의 liquidity pool로 묶되, 단순히 근접했다는
이유만으로 합치지 않는다.

### 5.4 진입 계약

기본형 계약은 다음과 같다.

```text
목적 liquidity가 현재 구조와 일치
AND 출발 liquidity에 손절 집중 이유가 존재
AND fresh context FVG/OB가 같은 가격 사건에 존재
AND 가격이 출발 liquidity를 sweep하고 회복
AND M5 또는 M1에서 live structure CHoCH
AND 같은 sweep-to-CHoCH causal leg에 fresh same-direction FVG 존재
AND valid FVG 중 가장 넓은 FVG 선택
AND meaningful CHoCH와 selected FVG 확정 이후 first retest
```

- LONG entry는 selected bullish FVG의 상단이다.
- SHORT entry는 selected bearish FVG의 하단이다.
- meaningful CHoCH가 있어도 같은 causal leg에 valid FVG가 없으면 최초 포지션은 없다.
- 별도 BOS는 필수가 아니다. 확인형 모델에서만 추가한다.

### 5.5 SL/TP 계약

- `width = selected FVG top - bottom`
- long SL: `FVG bottom - 0.20 * width`
- short SL: `FVG top + 0.20 * width`
- broker spread / stops-level / Bid-Ask와 전략 SL의 결합 방식은 execution infrastructure에서 별도 확정
- TP: 현재 시나리오 등급과 같은 등급의 다음 liquidity
- 체결 전 objective가 소비되면 주문 취소
- 체결 후에는 SL/TP로 판정
- 첫 시나리오 종료 뒤 새 구조는 새 scenario ID와 새 objective를 가짐

## 6. 다음 연구에서 먼저 답할 질문

다음 단계는 기능을 더 붙이는 것이 아니라 원전의 모호성을 최소 실험으로 분리하는 것이다.

1. 기본형 `CHoCH-FVG entry`와 확인형 `CHoCH+BOS entry` 중 어느 쪽이 expectancy가 높은가?
2. widest-FVG first-retest와 FVG 폭 20% SL 규칙이 표본 전체에서 원전 의도대로 재현되는가?
3. 행동 근거가 있는 liquidity만 남기면 단순 pivot liquidity 대비 방향 정확도가 나아지는가?
4. 내부 시나리오 TP를 내부 liquidity로 제한하면 승률과 평균 R이 어떻게 바뀌는가?
5. adaptive timeframe 선택이 고정 H1/M30 source보다 같은 가격 사건을 더 잘 설명하는가?

이 다섯 질문은 작은 토글 튜닝이 아니라 서로 다른 핵심 가설이다. 각 실험은 신호 발생
당시 차트를 재구성해 이유를 전수 확인해야 한다.

## 7. 개발 판단

현재 V3 EA에 V32 조건을 더 붙이는 방향은 중단해야 한다. 올바른 순서는 다음과 같다.

1. V32 원장을 read-only 연구 기반으로 동결한다.
2. 위 최소 시나리오 엔진을 Python에서 먼저 같은 Q1 데이터에 재생한다.
3. 모든 거래를 사람이 읽을 수 있는 7문장 시나리오로 출력한다.
4. 결과와 무관하게 표본 전체에서 원전 규칙을 지켰는지 먼저 검토한다.
5. 규칙 parity가 확인된 뒤에만 MT5 EA로 이식한다.

승률 50%는 규칙을 정확히 구현했다고 자동 달성되는 값이 아니다. 다만 지금처럼
23.53%의 결과를 만든 복잡한 체인을 계속 확장하는 것보다, 스승님의 실제 핵심을
독립 모델로 재현하고 틀린 방향·목표·유동성을 직접 분류하는 것이 이론적으로 맞는
다음 단계다.
