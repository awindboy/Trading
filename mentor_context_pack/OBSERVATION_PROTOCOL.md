# 시각적 차트 이해 절차

## 1. 입력을 이해하는 방식

판단 입력은 미래가 가려진 raw candlestick 이미지다. 코드는 M1 OHLC를 시간봉별로 집계하고 차트를 그리는 역할만 한다. OB, 유동성, 방향, trigger와 거래 허가는 모델이 이미지에서 직접 비교한다.

모델은 차트를 수치 공식으로 분류하지 않는다. 캔들 배열을 하나의 장면으로 보고 다음 관계를 비교한다.

```text
가격이 어디서 출발했는가
-> 무엇을 몸통으로 전달했는가
-> 그 원인 캔들이 의미 있는 스윙에 있는가
-> 같은 사건이 하위 시간봉에서 어떻게 세분화되는가
-> 가격이 돌아왔을 때 실제 반응 구조가 생겼는가
```

## 2. 매 호출의 관찰 순서

### A. 화면 무결성

- 모든 패널의 symbol과 `as_of`가 동일한지 확인한다.
- H1/M30/M15/M5/M1 마지막 캔들이 같은 공통 M1 시계를 넘지 않는지 확인한다.
- 가격축, 시간축, wick과 body가 판독 가능한지 확인한다.
- 자동 OB/FVG/유동성 라벨이나 이후 거래 결과가 가려져 있는지 확인한다.
- 하나라도 실패하면 `DATA_ERROR`이고 판단하지 않는다.

### B. H1/M30 map

- 가장 최근 캔들보다 먼저 현재 외부 파동의 protected high/low와 active dealing range를 본다.
- 현재 가격이 external continuation인지, range 내부 rotation인지, 외부 반전 후보인지 구분한다.
- 다른 참여자의 stop이 실제로 쌓였다고 설명할 수 있는 첫 미소진 유동성을 objective로 고른다.
- 목적지가 여러 개로 비교 불가능하면 scenario를 만들지 않는다.

### C. root 원인 선택

- 의미 있는 H1/M30/M15 swing 부근에서 실제 displacement가 시작된 반대색 캔들을 찾는다.
- 이후 body delivery가 구조를 전달했는지 확인한다.
- 단순 최근 반대색 캔들, HTF FVG 자체, 이미 소비된 구간은 제외한다.
- root의 시간·상단·하단·distal과 invalidation을 기록한다.

### D. causal refinement

- M30, M15, M5 순서로 같은 시간·가격 사건을 확대한다.
- 부모 안에 있다는 이유만으로 child로 선택하지 않는다.
- 부모와 같은 displacement를 시작했고 하위 구조 전달을 만든 OB만 child다.
- 여러 child가 분리되어 비교 불가능하면 좁은 것을 임의 선택하지 않는다.

### E. 대기와 확대

- refined OB가 멀면 M1을 읽지 않고 H1/M15 확정 때 map만 재승인한다.
- 가격이 child에 접근하거나 접촉하면 M5 correction을 먼저 확인한다.
- 그 뒤에만 M1을 한 봉씩 읽는다.

### F. M1 반응 판단

- sweep 대상은 현재 excursion 전에 이미 존재하고 반응이 완결된 유동성이어야 한다.
- wick 관통 후 회복과 correction을 지배한 live swing의 body break를 구분한다.
- micro pivot break를 CHoCH로 승격하지 않는다.
- CHoCH displacement의 causal execution OB와 첫 retest를 확인한다.

### G. 주문 전 반증

거래 이유보다 먼저 다음 반증을 확인한다.

- wrong premium/discount half
- 더 가까운 미소진 liquidity
- source 또는 child body invalidation
- objective 선도달
- stale pending과 map 미재승인
- M5 correction과 충돌하는 M1 micro signal
- 진입 접근이 zone과 invalidation을 동시에 관통
- spread와 broker stops level 바깥 SL을 설명할 수 없음

하나라도 해당하면 ORDER가 아니다.

## 3. 이미지와 상태의 역할 분리

- 이미지는 현재 구조를 다시 판단하는 근거다.
- `current_state.json`은 과거에 동결한 objective와 source를 이어받는 외부 기억이다.
- 상태에 기록돼 있다는 이유만으로 현재 차트와 충돌하는 source를 유지하지 않는다.
- 이미지에 새 구조가 보인다는 이유만으로 과거 objective를 조용히 바꾸지 않는다. 기존 상태를 `CANCEL`한 뒤 새 scenario를 만든다.

## 4. 불확실성 처리

시각적 판단은 확률적이므로 모호한 root, child, liquidity를 억지로 수치화하지 않는다. `confidence`는 거래 허가 점수가 아니라 관찰 품질 표시다. 필수 인과관계가 모호하면 confidence와 관계없이 비매매다.

