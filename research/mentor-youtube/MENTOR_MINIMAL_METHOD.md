# 스승님 매매법 최소 규칙

## 1. 한 문장 정의

현재 가격이 향하는 **다음 유동성**을 시장 구조로 정하고, 반대편의 의미 있는
유동성이 **FVG/OB 맥락 구간에서 sweep**된 뒤 작은 시간봉의 **추세 전환**을
확인하여, 그 전환 displacement가 만든 **FVG 되돌림**에 진입하는 방법이다.

이 문서에서 FVG, OB, CHoCH는 서로 독립된 신호가 아니다. 하나의 가격 이동
시나리오를 설명하는 역할만 가진다.

## 2. 핵심 개념은 여섯 개뿐이다

### 2.1 시장 구조

시장 구조의 목적은 차트에 BOS와 CHoCH를 많이 붙이는 것이 아니라 두 가지를
결정하는 것이다.

1. 지금 가격이 어느 쪽 유동성을 향하는가?
2. 현재 움직임은 외부 추세인가, 그 안의 내부 되돌림인가?

외부 고저점의 파괴는 큰 방향 변화의 근거가 되고, 내부 고저점은 되돌림이나
중간 유동성이 될 수 있다. 몸통 종가 돌파와 후속 움직임을 확인하며, 꼬리만
관통한 경우는 sweep 가능성을 먼저 본다.

근거: 1편 `03:14-04:42`, 10편 `05:24-07:45`, 13편 `20:28-22:49`,
21편 `10:57-12:45`.

### 2.2 유동성

유동성은 최근 pivot이라는 이유만으로 생기지 않는다. 다른 트레이더가 그 가격
바깥에 손절을 둘 **행동 이유**가 있어야 한다.

신뢰할 만한 후보는 다음과 같다.

- 여러 번 방어된 고점/저점 또는 지지/저항
- 횡보 박스의 상단/하단과 equal highs/lows
- 추세선이나 명확한 패턴의 바깥
- 오래 유지된 외부 swing high/low
- 큰 움직임 직전의 눈에 띄는 고저점
- 세션 고저점은 보조 후보지만 핵심 필수 조건은 아님

판단 질문은 하나다.

> 내가 이 방향의 일반 트레이더라면 손절을 어디에 둘 것인가?

근거: 4편 `03:46-07:44`, 11편 `02:27-06:18`, 16편 `06:49-07:56`,
21편 `02:01-04:15`.

### 2.3 Sweep

가격이 위 유동성을 관통하고 다시 아래로 회복하면 buy-side sweep 후보,
아래 유동성을 관통하고 다시 위로 회복하면 sell-side sweep 후보다.

그러나 sweep만으로 진입하지 않는다. 해당 유동성이 의미 있었고, 가격이
반응할 FVG/OB 맥락에 있었으며, 이후 작은 시간봉 추세가 실제로 바뀌어야 한다.

근거: 1편 `03:14-03:51`, 3편 `08:34-10:35`, 13편 `07:28-11:27`.

### 2.4 FVG

FVG는 세 캔들 중 첫 번째와 세 번째 꼬리 사이에 남은 불균형이다. 이 구간은
큰 주문이 빠르게 가격을 이동시키며 충분히 체결되지 못한 흔적으로 해석한다.

FVG의 존재만으로는 거래하지 않는다. 다음 둘 중 하나의 역할이 있어야 한다.

- 의미 있는 유동성 sweep이 일어날 상위/중간 시간봉 맥락 구간
- 작은 시간봉 추세 전환이 만든 실제 entry 구간

근거: 3편 `08:34-13:26`, 12편 `02:01-07:47`, 16편 `00:07-07:56`.

### 2.5 OB

영상에는 두 정의가 함께 쓰인다.

- 움직임 직전의 마지막 반대색 캔들
- FVG를 완전히 채우는 첫 캔들 또는 그 경계

따라서 연구 단계에서는 두 정의를 별도 유형으로 기록한다. 어느 하나를 스승님의
유일한 정의라고 임의 확정하지 않는다. 이미 완전히 채워지고 가격 전달이 끝난
zone은 재사용하지 않는다.

근거: 5편 `01:57-04:11`, 7편 `01:37-02:54`, 12편 `05:31-06:46`.

### 2.6 시간봉 역할

시간봉은 고정 조합이 아니라 역할로 선택한다.

| 역할 | 질문 | 예시 |
| --- | --- | --- |
| 지도 프레임 | 가격이 큰 구조에서 어디를 향하는가? | H1, M30 |
| HTF source 프레임 | 나중에 가격이 돌아왔을 때 반응을 관찰할 사전 형성·미소진 OB는 어디인가? | H1, M30, M15 |
| post-contact refinement 프레임 | HTF OB 접촉 이후 반응에서 새로 생긴 causal child OB는 무엇인가? | M30, M15, M5 |
| trigger 프레임 | post-contact child 맥락이 준비된 뒤 sweep과 추세 전환이 어디서 확인되는가? | M5, M1 |

주로 H1의 스윙 고점·저점 부근에서 **사전에 형성되어 있고 아직 미소진된 HTF OB**를 먼저 찾는다.
그 다음 lower timeframe에서 과거 OB를 미리 세분화하지 않고, 가격이 나중에 그 HTF OB에 실제로 도달할 때까지 기다린다.
HTF OB 접촉 이후에만 M30/M15/M5 반응을 관찰하며, 그 반응에서 새로 형성되고 자체 lower-TF 구조 전달로 확인되는 OB를 causal child로 인정한다.

따라서 다음은 current child refinement가 아니다.

- HTF Root 접촉 전에 이미 존재한 lower-TF OB
- HTF Root를 처음 만들었던 과거 displacement를 단순히 작은 시간봉으로 분해해 찾은 OB
- 단순히 가격이 가까이 있거나 겹친 unrelated lower-TF OB

Post-contact child가 parent OB 안에 있거나 일부 경계가 벗어나더라도, **동일한 post-contact reaction을 설명하는 causal relation**이 먼저 성립해야 한다.
최소 한 단계 이상의 post-contact child가 확인되지 않으면 정밀 진입 시나리오를 만들지 않는다.
이때 child는 최초 포지션의 source/context lineage를 정밀화하고, 실제 entry/SL geometry는 CHoCH displacement FVG 규칙이 담당한다.

근거: 9편 `03:01-03:38`, 13편 `16:46-18:33`, 16편 `02:20-03:32`,
20편 `06:01-07:32`.

## 3. 표준 시나리오 절차

### 단계 1. 목적지부터 찾는다

외부 시장 구조와 현재 활성 추세를 보고 다음으로 가져갈 가능성이 있는 반대편
유동성을 하나 정한다.

- long 시나리오: 다음 credible buy-side liquidity
- short 시나리오: 다음 credible sell-side liquidity
- 외부 구조 전체 반전이 확인되지 않았다면 먼 외부 목표 대신 가까운 내부 목표

목적지를 설명할 수 없으면 FVG/OB가 보여도 시나리오를 만들지 않는다.

### 단계 2. 사전 형성 HTF Root OB를 찾는다

목적지 반대편에서 가격이 나중에 반응할 수 있는 의미 있는 위치를 찾고, 주로 H1의
스윙 고점·저점 부근에서 **사전 형성·미소진 HTF OB**를 먼저 확인한다.

이 단계에서 중요한 것은:

- OB가 의미 있는 구조 전달을 만든 원인 위치인가
- 아직 first-reaction source로 볼 수 있는가
- 현재 map/objective와 연결되는가

이다.

이 시점에는 M30/M15/M5의 과거 lower-TF OB를 current child로 미리 동결하지 않는다.
HTF FVG는 전달 과정의 비효율을 설명할 수 있지만 단독 source POI로 사용하지 않는다.

### 단계 3. 가격이 HTF Root OB에 오기를 기다린다

가격이 사전에 정한 HTF Root OB에 도달하기 전에는 current setup의 LTF child를 사후 탐색하거나 M1 trigger를 찾지 않는다.

재생 연구에서도:

```text
H1/M30 map + objective + HTF Root를 먼저 동결
→ HTF Root 최초 qualifying contact까지 진행
→ contact 이후 lower-TF chart를 순차 관찰
```

한다.

HTF Root 접촉 전에 이미 존재했던 lower-TF OB를 접촉 이후 child였던 것처럼 소급 연결하지 않는다.

### 단계 4. HTF Root 접촉 이후 causal LTF child를 찾는다

가격이 HTF Root에 실제로 도달한 뒤 M30/M15/M5에서 **그 접촉에 대한 반응으로 새로 형성되는 OB**를 찾는다.

Valid child는:

- Root contact 이후 형성된다.
- 그 post-contact reaction에서 발생한다.
- 자체 lower-TF displacement와 의미 있는 구조 전달로 확인된다.
- causal confirmation 이후에만 사용할 수 있다.

여러 child가 생겼지만 어느 것이 같은 반응의 원인인지 구분할 수 없으면 가장 좁은 것을 임의 선택하지 않는다.

### 단계 5. 작은 시간봉 전환을 확인한다

Post-contact child lineage가 causal하게 준비된 뒤 M5/M1에서 기존 추세의 live swing을 반대 방향 몸통 종가로 깨고, 후속 가격이 그 방향으로 전달되는지 확인한다. 이 변화가 CHoCH다.

별도 BOS는 전환 신뢰도를 높이는 확인이지만 영상 전체의 필수 조건은 아니다.
기본 실행 구역은 CHoCH displacement가 새로 만든 M1 FVG다. 여기서 HTF Root와 post-contact child refinement는 진입 주문 자체가 아니라 가격이 반응할 원인 위치와 causal lineage를 설명한다.
의미 있는 CHoCH가 있어도 같은 sweep-to-CHoCH leg에 fresh FVG가 없으면 구조 전환만 기록하고 최초 포지션은 진입하지 않는다.

- 기본형: pre-existing HTF OB -> HTF OB contact -> post-contact causal LTF child -> sweep -> M1 CHoCH
  -> CHoCH displacement FVG -> FVG retest
- 확인형: pre-existing HTF OB -> HTF OB contact -> post-contact causal LTF child -> sweep -> M1 CHoCH
  -> 별도 BOS -> BOS displacement FVG -> FVG retest
- OB 정밀형: 전환 FVG 없이 OB만 재접촉하는 사례는 기본형과 섞지 않고 별도 연구 원장으로만 남긴다.

이 correction은 post-contact child 형성 뒤 **별도 child retest가 반드시 필요한지**를 새로 확정하지 않는다. 영상 근거가 없는 세부 순서를 임의 추가하지 않는다.

### 단계 6. 되돌림에 진입한다

기본 최초 진입은 M1 CHoCH displacement 안의 valid fresh FVG 중 **가격 폭이 가장
넓은 FVG**를 선택하고, selected FVG와 meaningful CHoCH가 모두 확정된 이후의 첫
retest를 사용한다. LONG은 bullish FVG의 상단, SHORT은 bearish FVG의 하단에 주문을
둔다. 동일한 최대 폭 FVG가 둘 이상이면 임의 선택하지 않고 거래하지 않는다.

선택된 FVG의 `width = top - bottom`으로 정의한다. LONG SL은
`bottom - 0.20 * width`, SHORT SL은 `top + 0.20 * width`로 둔다.

FVG는 standalone source가 아니다. `DELIVERY_FVG_REPLACEMENT`와
`DELIVERY_FVG_ADDON`은 최초 `INITIAL_CHOCH_FVG` 기본형과 별도의 후속 execution
protocol이다. 최초 진입 기본형이 정정되었으므로 두 protocol의 시작 조건과 SL 계약은
별도 재감사 전까지 V1 주문 권한을 비활성으로 유지한다.

### 단계 7. 틀릴 가격과 맞을 가격을 정한다

**SL**

- selected FVG의 `width = top - bottom`
- long: `SL = bottom - 0.20 * width`
- short: `SL = top + 0.20 * width`
- symbol tick size에 맞게 가격 단위만 normalize
- broker spread / stops level / Bid-Ask 제약을 전략 SL과 연결하는 방식은 execution
  infrastructure 단계에서 별도로 확정하며, 그 전에는 전략 SL 공식을 임의 변경하지 않음

**TP**

- 시나리오가 겨냥한 다음 유동성
- 외부 반전이 확인되지 않은 내부 시나리오는 내부 유동성
- 목적지까지 중간 장애물이 크면 일부 청산은 가능하지만 핵심 필수 규칙은 아님
- RR fallback, 최대 R, 임의 시간 만료는 사용하지 않음

근거: 1편 `08:44-09:14`, 3편 `12:59-15:42`, 13편 `18:21-18:44`,
17편 `02:09-09:03`.

### 단계 8. 결과를 받아들이고 다음 시나리오를 새로 만든다

체결 뒤에는 처음 정의한 SL/TP가 기본 판정이다. 같은 시나리오가 살아 있는 동안
가격이 느리다는 이유만으로 방향을 계속 바꾸지 않는다.

SL이 나면 다음을 구분한다.

- **확률적 손실**: 진입 당시 구조, liquidity, sweep, trigger가 모두 유효했으나
  시장이 반대로 전달됨
- **논리 오류**: 의미 없는 liquidity, 이미 소진된 zone, 외부/내부 혼동, 전환 전 진입,
  잘못된 목표나 SL
- **실행 오류**: spread, slippage, 잘못된 주문 가격, 중복 체결

SL로 시나리오가 끝난 뒤 반대 구조가 새로 완성되면 기존 objective를 고집하지 않고
새 방향·새 SL·새 TP로 재설계한다.

근거: 8편 `00:43`, 15편 `14:26-16:00`, 18편 `00:17-14:50`.

## 4. 거래 체크리스트

아래 일곱 질문에 모두 답할 수 있어야 한다.

1. 현재 외부 구조와 활성 추세는 무엇인가?
2. 이 시나리오의 목적 유동성은 어디이며 왜 손절이 모였는가?
3. 반대편 출발 유동성은 어디이며 왜 의미 있는가?
4. 사전에 정한 HTF swing OB는 무엇이고, 실제 contact 이후 어떤 causal LTF child가 새로 형성됐는가?
5. 유동성 sweep과 작은 시간봉 CHoCH가 실제로 발생했는가?
6. entry FVG는 post-contact child 맥락에서 CHoCH를 만든 M1 displacement에 속하며, valid FVG 중 가장 넓고 meaningful CHoCH 확정 이후의 first retest를 사용하고 있는가?
7. SL, TP, 그리고 틀렸다고 판정할 이유를 진입 전에 설명할 수 있는가?

한 질문이라도 `그냥 최근 고점`, `그냥 FVG`, `그냥 추세 같음`이라면 거래하지 않는다.

## 5. 핵심과 옵션의 경계

### 핵심 규칙

- 외부/내부 시장 구조 구분
- 참가자 손절 위치로 설명되는 유동성
- 사전 형성·미소진 HTF swing OB
- HTF Root 실제 contact 이후 새로 형성되는 causal LTF child refinement
- adaptive MTF 역할 분담
- sweep 뒤 LTF 추세 전환
- CHoCH displacement의 widest valid FVG first-retest entry
- 후속 FVG replacement/add-on은 별도 재감사 전 비활성
- FVG distal 바깥 20% width SL, 다음 유동성 TP

### 옵션 또는 별도 모델

- 별도 continuation BOS까지 기다리는 확인형 entry
- PD 50% premium/discount
- 세션 고저점과 kill zone
- 반대색 캔들 세 개를 한 파동으로 보는 경험 규칙
- FVG inversion 몸통 종가 즉시 진입
- 부분 익절과 본절 이동
- MTF 확인을 생략한 sniper entry

### 이 연구에서 제외할 것

- 스승님 영상에 없는 복잡한 ICT 명칭과 패턴 조합
- FVG/OB/CHoCH/BOS 개수를 늘린 점수제
- 고정 H1/M30/M15/M5/M1 앵커 강제
- 최근 pivot만으로 만든 BSL/SSL
- RR fallback, 최대 R 제한, 임의 보유 시간 종료
- 손실 뒤 결과에 맞춰 규칙을 바꾸는 사후 합리화

## 6. 아직 규칙으로 확정하지 않은 모호성

다음은 영상만으로 단일 정답을 확정할 수 없다. 구현자가 임의 결론을 내리지 않고
각 후보를 독립적으로 재생해야 한다.

1. OB를 마지막 반대색 캔들로 볼지, FVG fill candle로 볼지
2. 내부 시나리오와 외부 시나리오의 최소 구분 기준
3. delivery 정체 시 본절 이동을 규칙화할 수 있는지
4. 부분 청산이 전체 기대값을 개선하는지
5. post-contact child가 형성·확정된 뒤 별도의 child retest가 execution trigger 전에 반드시 필요한지

이 항목들은 필터 튜닝 문제가 아니라 매매 모델의 서로 다른 변형 또는 아직 미확정된 세부 계약이다.

## 7. 수익성에 대한 정직한 경계

영상은 이 방법이 높은 손익비로 손실을 보완한다고 주장하고, 매매일지 영상에는
짧은 기간의 높은 승률과 수익이 제시된다. 그러나 선택된 영상 사례와 자기 보고만으로
장기 수익성을 증명할 수는 없다.

따라서 이 문서는 **스승님의 방법을 정확히 재현하기 위한 이론 계약**이다. 수익성은
이 계약을 바꾸지 않은 상태에서 충분한 표본과 미사용 기간으로 별도 검증해야 한다.
