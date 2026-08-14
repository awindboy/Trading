# Mentor Week Reverse-Engineered Protocol V3

## 목적과 증거 경계

이 규칙은 `2025-06-16~20 GOLD`의 전체 경로를 본 뒤 역설계했다. 기존 6개 거래만
설명한 것이 아니라, 해당 주간의 M30/M15 원인 OB 접촉 23개를 진입·대기·거절·
무효화 중 하나로 종결했다.

이 주간의 `+27.31R`, 7승 5패는 **in-sample 반사실 결과**다. 수익성을 증명하지
않으며, 아래 규칙을 수정하지 않고 다른 미사용 주간에 적용한 결과만 검증 자료가 된다.

## 1. 부모 시나리오

1. H1에서 외부 방향, protected high/low, dealing range를 정한다.
2. 실제 몸통 구조 돌파를 만든 마지막 반대색 M30/M15 캔들을 원인 OB로 정한다.
3. HTF FVG는 전달 과정의 정보일 뿐 부모 source가 아니다.
4. 외부 지속의 목적지는 방향상 가장 가까운 미소진 외부 유동성이다.
5. 내부 회전의 목적지는 기존 외부 구조를 넘지 않는 첫 반대 유동성이다.
6. 부모는 OB distal 바깥 몸통 수용 또는 목적지 선도달 전까지 유지된다.

## 2. M1 실행 시도

부모 source를 접촉한 뒤 다음 순서를 모두 요구한다.

1. 접촉 전에 존재했거나 source 반응으로 명확히 형성된 유동성
2. wick 관통과 같은 캔들의 종가 복귀
3. 별도 캔들의 live protected level 몸통 CHoCH
4. CHoCH displacement가 만든 FVG
5. FVG가 없을 때만 CHoCH의 causal OB
6. 확정 이후의 retest

진입은 FVG 또는 OB proximal boundary에 둔다. 실행 SL은 `sweep extreme`과
`CHoCH execution OB distal` 중 더 먼 곳 바깥에 당시 spread를 더한다.

## 3. 부모와 실행을 분리한다

- 실행 SL은 해당 M1 시도가 틀렸다는 뜻이다.
- 실행 SL만으로 M30/M15 부모 source와 목적지를 삭제하지 않는다.
- 부모가 살아 있다면 새로운 sweep부터 시작한 독립 체인으로 재무장한다.
- 같은 sweep이나 같은 CHoCH/FVG를 두 번 주문하는 것은 금지한다.
- 부모 무효화 뒤에는 같은 방향 재진입을 금지하고 H1 map부터 다시 작성한다.

이 분리가 없어서 기존 replay는 6월 16일, 18일의 첫 손절 뒤 큰 후속 수익을 놓쳤다.

## 4. 목적지 규칙

- 유동성 가격 자체가 TP다. 유동성 너머에 buffer를 두지 않는다.
- 더 큰 R을 만들기 위해 가까운 미소진 유동성을 건너뛰지 않는다.
- 6월 17일 10:59 short는 `3373.10`이 아니라 `3381.70`이 정답이었다.
- 6월 17일 15:31 내부 long은 `3400.31`이 아니라 첫 반대 유동성 `3391.76`에서
  종료해야 했다.
- 목적지가 먼저 소진되면 같은 주문의 더 먼 TP를 사후 선택하지 않는다.

## 5. 시장 불확실성의 정의

다음이 모두 맞았는데 실행 SL이 난 경우만 `MARKET_UNCERTAINTY`다.

- H1 map
- 원인 M30/M15 OB
- source 접촉
- 독립 sweep
- 별도 CHoCH
- causal FVG/OB와 이후 retest
- execution geometry SL
- 가장 가까운 미소진 objective

6월 20일 long 두 건은 이 조건을 충족한 뒤 부모 M15 OB까지 무효화됐다. 이 손실은
추세를 사후에 바꿔 설명하지 않는다. 반대로 이전 6월 17일 손실 두 건은 가까운
유동성을 건너뛴 TP 오류였으므로 시장 불확실성으로 분류하지 않는다.

## 6. 다음 블라인드 주간의 동결 조건

- H1/M30/M15 map은 M1 trigger를 보기 전에 기록한다.
- source 접촉 전에는 M1 trigger 후보를 찾지 않는다.
- 주문 시 entry, execution SL, parent invalidation, objective를 동시에 동결한다.
- 실행 SL 뒤 부모 상태만 재평가하고 결과에 따라 규칙을 변경하지 않는다.
- 주간 종료 후에만 승률, R, 누락 체인과 의미 오류를 감사한다.

## 산출물

- `output/mentor_week_2025-06-16_20_rule_reverse_engineering_v3/weekly_path_audit.jsonl`
- `output/mentor_week_2025-06-16_20_rule_reverse_engineering_v3/counterfactual_trades.csv`
- `output/mentor_week_2025-06-16_20_rule_reverse_engineering_v3/frozen_rule_contract_v3.json`
- `output/mentor_week_2025-06-16_20_rule_reverse_engineering_v3/TRADE_REVIEW.html`
