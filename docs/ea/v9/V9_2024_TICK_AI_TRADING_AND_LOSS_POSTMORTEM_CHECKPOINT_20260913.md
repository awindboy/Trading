# V9 2024 Tick-AI Trading + Loss Postmortem Checkpoint

Date: `2026-09-13`  
Status: `2024 CAUSAL REPLAY MEASURED / 2024 NOW CONSUMED POSTMORTEM DATA / NO NEW STRATEGY RULE AUTHORITY`  
Base GitHub HEAD: `55fca94794e00cdb3b83d410f3d71143f9beb171`  
Production authority: `NONE`  
EA authority: `NONE`  
Future-hidden: `2025-07 LOCKED`  
Untouched final reserve: `GOLD# 2021`

## 1. 이 문서의 의미

이 체크포인트는 2024 GOLD# 구간에서 기존 V9 Grammar를 미래를 보지 않고 순차 재생하고, 실제 BID/ASK tick으로 체결/손절을 재구성하며, AI 역할을 현재 ChatGPT가 당시 차트만 보고 수행한 결과를 기록한다.

중요한 데이터 분류 변경:

```text
2024 replay 자체는 결과를 보기 전에 causal하게 실행했다.
하지만 이제 2024 결과와 손실 거래를 상세 복기하여 다음 연구 방향에 사용한다.
따라서 2024는 이 시점부터 CONSUMED POSTMORTEM DATA다.
앞으로 2024를 untouched OOS / future-hidden validation이라고 다시 부르지 않는다.
```

`2025-07`은 열지 않았고 `2021`도 사용하지 않았다.

## 2. 실행 방식

- 2024 M1은 2024 block 내부에서만 warm-up했다.
- 각 시점에서 공개된 H4/H1/M15/M5와 object만 사용했다.
- AI review/remap 판단 후에만 이후 가격을 공개했다.
- 매수 체결은 실제 ASK, 매도 체결은 실제 BID를 사용했다.
- Hard SL은 진입 전 고정된 structural origin을 유지했고 절대 넓히지 않았다.
- long SL은 실제 BID, short SL은 실제 ASK의 최초 위반 tick으로 처리했다.
- historical spread는 포함했다.
- commission / swap / live network-broker latency는 포함하지 않았다.
- tick coverage gap 때문에 결과를 확정할 수 없는 5건은 censor 처리했다.

## 3. 2024 전체 성과

| 항목 | 결과 |
|---|---:|
| 실제 체결 | 310 |
| 결과 확정 가능 | 305 |
| tick gap censor | 5 |
| 이익 거래 | 103 |
| 손실 거래 | 202 |
| 승률 | 33.77% |
| 총손익 | +20.51R |
| 거래당 평균 | +0.067R |
| Profit Factor | 1.118 |
| 평균 이익 | +1.88R |
| 평균 손실 | -0.86R |
| 최대 trade-sequence drawdown | -30.73R |
| 최대 연속 손실 | 15회 |

분기별:

| Branch | 거래 | 승률 | 총 R | 거래당 평균 |
|---|---:|---:|---:|---:|
| 역추세 `COUNTER` | 256 | 35.94% | +12.26R | +0.048R |
| 추세추종 `WITH_PARENT` | 49 | 22.45% | +8.25R | +0.168R |

이 결과의 핵심은 높은 승률이 아니다. 소수의 큰 winner가 전체 expectancy를 만든다.

```text
상위 winner 1개 제거 후: +4.40R
상위 winner 3개 제거 후: -16.99R
상위 winner 5개 제거 후: -31.80R
```

따라서 fixed TP / 단순 trailing으로 큰 winner를 자르는 방향은 현재 evidence와 맞지 않는다.

## 4. 손실 전체 구조

202개 손실은 다음처럼 나뉜다.

| 손실 유형 | 건수 | 합계 R | 해석 |
|---|---:|---:|---|
| 1시간 이내 + MFE < 0.25R Hard SL | 45 | -46.61 | 거의 출발하지 못한 즉시 실패 |
| MFE < 0.25R이지만 1시간 초과 Hard SL | 23 | -23.65 | 방향 확장 없이 오래 버틴 실패 |
| MFE 0.25~1R 후 Hard SL | 64 | -66.68 | 일부 진행 후 확장 실패 |
| MFE >= 1R 후 Hard SL | 21 | -21.98 | 한때 성공했지만 전부 반납 |
| AI가 손실 중 조기청산 | 49 | -14.25 | review가 Hard SL보다 손실을 축소 |

Hard SL 153건 평균은 `-1.039R`, 손실 상태에서 AI EXIT한 49건 평균은 `-0.291R`이다.

가장 중요한 사실:

```text
153 Hard SL 중 152건은 AI semantic review를 받기 전에 종료됐다.
```

따라서 현재 최대 개선 여지는 exit 선택보다 **진입 전/진입 직후의 Grammar 해석**에 있다.

## 5. 바로 죽는 거래 — Entry arrival / acceptance gap

Hard SL 중:

```text
1시간 안에 SL: 77건
MFE < 0.25R: 68건
두 조건 동시: 45건
```

45건의 중앙 생존 시간은 약 `18.61분`, 중앙 MFE는 약 `0.077R`이다.

그런데 45건 중:

```text
H4 macro 3/3 agreement: 37
M15가 Child 방향 지지: 36
M5가 Child 방향 지지: 22
M5가 Child 방향 비지지: 23
```

즉 “H4가 약해서 손실”이라고 단순화할 수 없다. 대부분은 큰 방향과 M15 authorization이 이미 존재한다.

전체 2024에서도 M5 상태는 강한 descriptive 차이를 보였다.

| Branch | M5가 Child 지지 | 거래 | Hard SL | Hard SL률 | 총 R |
|---|---|---:|---:|---:|---:|
| COUNTER | Yes | 181 | 78 | 43.1% | +14.15R |
| COUNTER | No | 75 | 48 | 64.0% | -1.89R |
| WITH_PARENT | Yes | 31 | 15 | 48.4% | +21.09R |
| WITH_PARENT | No | 18 | 12 | 66.7% | -12.84R |

하지만 이것은 `M5 반대 -> 진입 금지` authority가 아니다.

현재 Grammar에서 M5는 주로 실행 위치/geometry다. 이번 손실 복기는 다음 semantic gap을 제기한다.

> 가격이 M5 execution location에 도착했다는 사실과, 그 위치에서 실제로 Child 방향을 **받아들이는 것(acceptance)** 은 다르다.

다음 연구는 M5 consensus threshold가 아니라 **arrival -> reaction -> acceptance/rejection**을 chart-native AI가 causal하게 읽을 수 있는지를 검증해야 한다.

### 대표 사례

- `2024OOS-COU0003`: H4/H1 DOWN 속 counter long. M15은 UP이었지만 진입 시 M5는 DOWN. MFE `+0.26R`, 최종 `-1.02R`.
- `2024OOS-WIT0010`: Parent UP continuation long. M15/M5는 UP이었지만 H1 repair가 실제로 끝나지 않은 상태에서 체결. MFE `0R`, 약 31분 후 `-1.01R`.
- `2024OOS-WIT0064`: H4 DOWN 3/3인데 continuation short가 진입 당시 M15/M5 UP. MFE `+0.15R`, 약 5분 후 `-1.03R`.

증거 차트는 bundle `evidence/`에 포함한다.

## 6. 역추세 COUNTER 손실 복기

COUNTER Hard SL:

```text
126건 / -130.10R
1시간 이내 SL: 60건
MFE < 0.25R: 56건
MFE >= 1R 후 SL: 17건
```

반복적으로 두 종류가 존재했다.

### A. Local-Bridge가 실제로 열리지 않은 경우

M15 counter transition은 나왔지만 가격이 execution location에서 counter side를 받아들이지 않고 곧바로 Parent 방향으로 다시 흡수된다.

연구 질문:

> “fresh M15 counter transition”이 실제 local bridge의 시작인가, 아니면 강한 Parent migration 안의 짧은 흔들림인가?

### B. Local-Bridge는 성공했지만 역할 종료를 너무 늦게 읽은 경우

17건은 이미 +1R 이상 갔다가 Hard SL로 끝났다.

COUNTER는 Parent reversal을 맞히는 전략이 아니라 local bridge participation이므로, **bridge가 의미 있는 destination을 전달한 뒤에도 계속 같은 Child를 Parent reversal처럼 들고 있는지**를 연구해야 한다.

## 7. 추세추종 WITH_PARENT 손실 복기

WITH_PARENT Hard SL:

```text
27건 / -28.82R
1시간 이내 SL: 17건
MFE < 0.25R: 12건
MFE >= 1R 후 SL: 4건
```

주요 gap은 Parent 방향 자체보다 **repair 종료 시점**이다.

현재 authorization:

```text
H1 INTERRUPT
-> fresh M15 Parent-side reauthorization
-> M5 execution location
```

손실 사례에서는 이 sequence가 존재해도 실제 price acceptance가 아직 repair 내부에 남아 있는 경우가 있었다.

연구 질문:

> “M15이 Parent 방향으로 다시 바뀌었다”와 “H1/M15 repair가 실제로 끝나 Parent 방향 가격수용이 다시 시작됐다”를 어떻게 구분할 것인가?

Hard SL을 넓히는 것은 답이 아니다. 손절된 Child는 그대로 죽는다.

## 8. +1R 이상 갔다가 Hard SL — loss conversion의 직접 후보

Hard SL 153건 중:

```text
MFE >= 1R 후 SL: 21건
MFE >= 2R 후 SL: 10건
MFE >= 3R 후 SL: 5건
```

21건 중 branch:

```text
COUNTER: 17
WITH_PARENT: 4
```

causally known M5 swing/liquidity가 profitable side에 생기거나 이미 존재했고, trade가 살아 있는 동안 실제 raid/delivery된 사례:

```text
14 / 21
```

그 14건 중 delivery 이후 completed M15가 Child side를 더 이상 지지하지 않는 상태가 나온 사례가 `10건`, 그 첫 시점에도 실제 호가 기준 수익권인 사례가 `9건`이었다.

그 9건의 **사후 비교**:

```text
실제 최종 합계:                 -9.21R
첫 post-delivery M15 non-support 시점 즉시청산 가정: +4.43R
차이:                           +13.63R
```

이 비교는 연구 중요도를 보여줄 뿐, exit rule authority가 아니다.

왜냐하면 winner에서도 같은 현상이 흔하다.

```text
전체 winner: 103
favorable liquidity delivery가 있었던 winner: 101
delivery 후 M15 non-support도 있었던 winner: 80
```

따라서 금지:

```text
delivery -> 자동 TP
+1R / +2R -> 자동 BE/trailing
post-delivery M15 non-support -> 자동 EXIT
```

다음 AI가 읽어야 하는 것은 **delivery 발생 여부 자체가 아니라 delivery 이후 시장의 acceptance**다.

### 비교 사례

- `2024OOS-COU0307`: counter short, MFE `+3.60R`, 여러 favorable delivery 후 Parent-side re-acceptance가 진행됐지만 AI gate 없이 `-1.02R` Hard SL.
- `2024OOS-COU0330`: counter short, MFE `+10.72R`, delivery와 M15 wobble이 있었지만 더 낮은 가격대에서 counter-side acceptance가 계속되어 최종 `+7.80R`.

이 두 사례를 구분하지 못하는 단순 trailing rule은 V9의 large-tail edge를 훼손한다.

## 9. Fresh reauthorization / campaign exhaustion

authorization class 결과:

| Authorization | 거래 | 승 | 패 | 총 R |
|---|---:|---:|---:|---:|
| FIRST | 203 | 70 | 133 | +38.24R |
| FRESH_REAUTH | 102 | 33 | 69 | -17.74R |

분기별 FRESH_REAUTH:

```text
COUNTER: -8.94R
WITH_PARENT: -8.80R
```

하지만 이를 retry-limit으로 바꾸지 않는다. profitable periods에도 큰 reauthorization winner가 존재한다.

질문은 횟수가 아니라:

> fresh transition이 실제 **새 auction/route의 시작**인가, 아니면 destination이 이미 소진된 campaign 안에서 반복되는 oscillation인가?

이다.

## 10. 10월 stress와 Parent MP098

2024-10:

```text
39 trades
7 wins / 32 losses
26 Hard SL
-20.67R
```

하나의 Parent `2024OOS-MP098` 안에서:

```text
19 trades
15 Hard SL
11 FRESH_REAUTH
-10.06R
```

이 결과는 `N회 손실 후 중지`를 정당화하지 않는다.

연구할 것은 **Parent campaign coherence / auction exhaustion**이다. 같은 Parent 아래서 fresh objective transition이 계속 나오더라도, route가 실제 새로운 destination을 열고 있는지 아니면 양방향 churn으로 변했는지 구분해야 한다.

## 11. REMAP runtime 버그 수정

2024 causal replay에서 실제 REMAP 2건을 다루며 구현 버그가 드러났다.

기존:

```text
COUNTER Child
-> opposite new Parent와 Child 방향 일치
-> journey_role = WITH_NEW_PARENT_JOURNEY
-> 그러나 내부 damage orientation은 계속 COUNTER branch 규칙 사용
```

수정:

```text
WITH_NEW_PARENT_JOURNEY
-> original structural origin은 그대로 유지
-> 새 same-direction Parent journey 기준으로 launch/damage semantics 적용
```

현재 runtime:

```text
STRATEGY_RUNTIME_VERSION = v9-strategy-state-machine-5
SHA256 = 5728c013f5c650a8e21c607112c1391b4ce1254234199380df08ac0042f91436
```

이 변경은 전략 rule 추가가 아니라 기존 authority 구현 버그 수정이다.

수정 후 기존 consumed `2025H1 + 2026JF` 전체 replay:

```text
segments                  594
AI semantic requests      109
revealed M1           229,861
pending gates               0
gate counts             EXACT
revealed ledger         EXACT
semantic ledger         EXACT
Counter ledger          EXACT
With-Parent ledger      EXACT
object ledger           EXACT
external actions        EXACT
status                   PASS
```

## 12. 이번 복기로 새로 알게 된 것

### 확정 가능한 연구 결론

1. V9의 2024 edge는 승률형이 아니라 **large-winner tail participation**형이다.
2. 현재 가장 큰 손실 gap은 AI exit quality보다 **AI가 entry/early-life를 semantic하게 검토하지 않는 구조**다.
3. 빠른 SL은 H4 weakness 하나로 설명되지 않는다. 강한 Parent에서도 execution location의 local acceptance가 실패한다.
4. COUNTER는 `bridge never opened`와 `bridge delivered but role ended`를 분리해서 이해해야 한다.
5. WITH_PARENT는 Parent 방향 예측보다 `repair really ended`를 더 잘 읽어야 한다.
6. liquidity delivery는 매우 중요한 진행 정보지만 자동 TP가 아니다.
7. FIRST vs FRESH_REAUTH 차이는 campaign-exhaustion 연구를 요구하지만 retry cap을 정당화하지 않는다.

### 아직 authority가 아닌 것

- M5 consensus filter
- +1R/+2R/+3R management threshold
- delivery TP
- delivery 후 M15 change 자동 exit
- retry count/cooldown
- Parent별 trade cap
- fixed no-chase

## 13. 현재 데이터 분류

```text
2024-01..12 = CONSUMED POSTMORTEM DATA
2025-01..06 = CONSUMED ANSWER-SHEET DATA
2026-01..02 = CONSUMED ANSWER-SHEET DATA
2025-07     = FUTURE-HIDDEN LOCKED
GOLD# 2021  = UNTOUCHED FINAL RESERVE
```

2024를 다시 OOS라고 부르지 않는다.

## 14. 다음 연구

다음 exact contract는:

`V9_NEXT_RESEARCH_CONTRACT_GRAMMAR_LOSS_CONVERSION_20260913.md`

핵심 순서:

```text
ENTRY ARRIVAL / ACCEPTANCE
-> DELIVERY / JOURNEY REVIEW
-> FRESH REAUTH / CAMPAIGN EXHAUSTION
-> branch-specific semantic comparison
-> chart-native AI input + model-role freeze
-> consumed causal replay
-> only then future-hidden gate decision
```

`2025-07`은 계속 잠근다.
