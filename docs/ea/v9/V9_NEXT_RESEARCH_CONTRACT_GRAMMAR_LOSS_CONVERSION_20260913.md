# V9 Next Research Contract — Grammar-Driven Loss Conversion

Date: `2026-09-13`  
Status: `ACTIVE NEXT RESEARCH CONTRACT / NO NEW TRADE RULE AUTHORITY YET`  
Base GitHub HEAD: `55fca94794e00cdb3b83d410f3d71143f9beb171`  
Market: `GOLD# ONLY`  
Production authority: `NONE`  
EA authority: `NONE`  
2024: `CONSUMED POSTMORTEM DATA`  
Future-hidden: `2025-07 LOCKED`  
Final reserve: `GOLD# 2021 UNTOUCHED`

## 1. 연구 목표

다음 연구의 목표는 winner를 더 빨리 자르는 것이 아니다.

> 기존 Market-Flow Grammar를 바탕으로 **손실이 되기 전에 시장이 실제로 제공한 causal information을 더 잘 해석**하여, 불필요한 Child를 줄이고 이미 성공한 Child가 역할 종료 후 전부 반납하는 경우를 줄이는 것이다.

성공 기준은 단순 2024 P/L 최대화가 아니다.

```text
compact semantic explanation
+ branch 간 재사용 가능성
+ difficult-period coverage
+ large-winner preservation
+ hidden threshold 없음
+ causal chart input으로 재현 가능
```

이어야 한다.

## 2. 절대 guardrails

이번 연구에서 금지:

- `M5 반대면 진입 금지` 같은 mandatory filter;
- +1R/+2R/+3R 고정 BE/TP/trailing;
- delivery가 나오면 자동 청산;
- M15이 반대로 바뀌면 자동 청산;
- N번 손절 / N번 재진입 후 중지;
- cooldown / retry cap / fixed no-chase;
- 2024에 맞춘 month/Parent-specific rule;
- stopped Child를 이후 가격으로 rescue;
- 한두 사례로 Grammar authority 수정;
- `2025-07` 또는 `2021` 열기.

2024의 R bucket은 **postmortem stratification**일 뿐 live rule이 아니다.

## 3. Workstream A — Entry Arrival / Acceptance

### 문제

현재 execution flow는 대체로:

```text
M15 authorization
-> M5 execution geometry
-> zone touch
-> fill
```

이다.

2024에서 45개 거래가 1시간 이내, MFE 0.25R 미만 상태로 Hard SL됐다. 그중 37개는 H4 macro 3/3이었다.

따라서 다음 질문을 연구한다.

> 가격이 미리 정한 execution location에 도착했을 때, 시장은 실제로 Child side를 받아들이고 있는가?

### 연구 방법

- 45 `FAST_NO_PROGRESS_HARD_SL` 전체를 review한다.
- 같은 branch / comparable Parent-H1 context의 robust winner를 짝지어 비교한다.
- chart에는 causal 시점의 H4/H1/M15/M5, exact zone, origin, nearby liquidity/object를 표시한다.
- AI는 다음을 narrative semantic으로 구분한다.
  - `ARRIVAL_WITH_ACCEPTANCE`
  - `ARRIVAL_WITH_REJECTION`
  - `ARRIVAL_STILL_INSIDE_REPAIR`
  - `UNRESOLVED`
- label은 연구 vocabulary다. 바로 entry rule이 아니다.

### 확인할 핵심

COUNTER:

> counter M15 transition이 실제 local bridge 개시인지, Parent acceleration 속 흔들림인지?

WITH_PARENT:

> Parent-side M15 reauthorization이 실제 repair 종료인지, repair 내부의 일시적 Parent-side 흔들림인지?

### Gate 후보

`ENTRY_CONTEXT_REVIEW`는 **research candidate only**다.

새 gate를 runtime authority로 넣기 전에 paired case study와 consumed replay가 먼저다.

## 4. Workstream B — Delivery / Journey Review

### 문제

21개 Hard SL은 이미 +1R 이상 진행했다. 14개는 trade가 살아 있는 동안 causally known favorable swing/liquidity delivery를 완료했다.

그러나 같은 delivery와 이후 M15 wobble은 large winner에서도 흔하다.

### 연구 질문

> delivery 이후 이 Child는 더 큰 journey로 확장되고 있는가, 아니면 현재 branch가 맡았던 역할을 이미 완료하고 Parent/반대 auction이 다시 가격을 받아들이는가?

### 비교 집단

반드시 양쪽을 함께 본다.

```text
A. +1R 이상 진행 후 Hard SL 21건
B. 큰 winner / long-tail winner
```

특히:

- `COU0307`: +3.60R까지 갔다가 -1.02R
- `COU0330`: +10.72R MFE, +7.80R realized

처럼 delivery 후 구조가 달라지는 pair를 우선 비교한다.

### 분석 vocabulary 후보

- `DELIVERY_CONTINUES_ACCEPTANCE`
- `DELIVERY_ROLE_COMPLETE`
- `PARENT_SIDE_REACCEPTANCE`
- `NEW_DESTINATION_OPENED`
- `UNRESOLVED`

이 역시 연구 label이며 자동 exit rule이 아니다.

### Scheduler 후보

`PROGRESSION_REVIEW` / `DELIVERY_REVIEW`는 research candidate only.

유동성 raid 하나만으로 호출하는 것이 아니라, chart-native semantic context를 정의한 뒤 scheduler contract를 freeze한다.

## 5. Workstream C — Fresh Reauthorization / Campaign Exhaustion

2024 aggregate:

```text
FIRST        203 trades / +38.24R
FRESH_REAUTH 102 trades / -17.74R
```

이 차이를 보고 retry limit을 만들지 않는다.

연구 질문:

> fresh objective transition이 실제 새 auction/route의 시작인가, 아니면 이미 delivery가 반복되고 destination이 소진된 Parent campaign 내부의 oscillation인가?

### 필수 비교

- profitable reauthorization campaigns;
- 2024-10 `MP098` 같은 churn-heavy campaign;
- COUNTER와 WITH_PARENT를 별도 분석;
- exact route/destination landmark sequence;
- Parent authority/coherence 변화;
- ambiguity/neutralization을 숨기지 않는다.

횟수/시간을 threshold로 바꾸지 않는다.

## 6. Workstream D — Branch-specific semantics

### COUNTER Local-Bridge

분리해야 하는 질문:

```text
1. bridge가 실제 열렸는가?
2. bridge가 의미 있는 destination을 전달했는가?
3. 전달 후에도 counter-side acceptance가 계속 확장되는가?
4. 아니면 Parent side가 다시 가격을 받아들이는가?
```

COUNTER Child는 Parent reversal prediction이 아니다.

### WITH_PARENT repair/continuation

분리해야 하는 질문:

```text
1. H1/M15 repair가 실제 끝났는가?
2. Parent-side price acceptance가 execution location에서 재개됐는가?
3. 단순 reauthorization인가, 실제 next auction launch인가?
```

Parent direction이 맞았다는 이유로 stopped Child를 rescue하지 않는다.

## 7. Chart-native AI input 연구

현재 AI gate-envelope은 REVIEW/REMAP mechanics만 freeze되어 있다.

다음 chart contract는 최소 다음을 같은 causal fingerprint에 묶어야 한다.

```text
H4 authority / phase / agreement
H1 auction role
M15 local transition
M5 execution geometry + current local flow
Parent id/side + Child branch/side
structural origin / launch anchor
exact active/consumed liquidity landmarks
route/destination history available so far
current price cutoff / information-known timestamp
```

미래 bar, later Child outcome, hindsight label은 입력에 절대 포함하지 않는다.

## 8. AI model-role 연구

현재 연구 단계에서는 외부 AI API가 필요하지 않다. ChatGPT가 causal chart를 보고 동일 role을 수행한다.

다음 model-role contract는 최소 다음 원칙을 가져야 한다.

- Child 질문과 Parent story를 분리한다.
- direction oracle처럼 행동하지 않는다.
- uncertainty를 `UNRESOLVED`로 허용한다.
- fixed threshold를 만들어내지 않는다.
- stopped Child를 rescue하지 않는다.
- large winner participation을 기본적으로 보존한다.

연구 단계의 candidate questions:

```text
ENTRY: 이 location에서 Child side acceptance가 실제 존재하는가?
PROGRESSION: delivery 이후 current Child role이 계속 살아 있는가?
REAUTH: 이것은 genuinely new auction인가, exhausted campaign oscillation인가?
```

실제 runtime action schema는 evidence가 쌓인 뒤 별도로 freeze한다.

## 9. 연구 순서

```text
1. 2024 loss/winner enriched ledger = DONE
2. Entry arrival/acceptance paired chart study
3. Delivery/giveback vs large-winner paired study
4. Fresh reauth / campaign-exhaustion study
5. branch-specific semantic vocabulary compression
6. chart-native causal attachment freeze
7. AI model-role / prompt freeze
8. 필요하다면 research-only candidate gate 구현
9. 2024 + 2025H1 + 2026JF consumed causal replay
10. difficult-period / counterexample review
11. implementation + packet + chart + prompt hashes freeze
12. future-hidden gate decision 재평가
```

## 10. Future-hidden gate

현재 결정:

```text
2025-07 FUTURE-HIDDEN GATE = NOT SATISFIED
```

이유:

- 2024 postmortem이 새로운 semantic gaps를 드러냈다.
- entry acceptance / delivery meaning / reauth exhaustion에 대한 chart-native AI contract가 아직 freeze되지 않았다.
- 2024는 이제 consumed이므로 future validation 역할을 하지 않는다.

`2021`은 untouched final reserve로 유지한다.

## 11. 이 연구가 끝났다고 판단하는 조건

다음 조건이 모두 필요하다.

- 손실과 winner를 같은 compact vocabulary로 설명할 수 있다.
- 10월 같은 stress period도 month-specific rule 없이 설명된다.
- large winner를 잘라내지 않는다.
- M5/유동성/R/retry count를 threshold로 숨기지 않는다.
- causal chart만으로 label을 재현할 수 있다.
- runtime gate가 필요하다면 exact event authority와 action schema가 freeze된다.
- consumed replay에서 implementation parity가 유지된다.

그 뒤에만 `2025-07` unlock 여부를 다시 결정한다.
