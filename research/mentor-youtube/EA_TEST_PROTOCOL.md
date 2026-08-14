# MentorScenarioTraderEA 첫 테스트

현재 EA는 수동 1주 원장을 코드로 이식한 첫 연구 baseline이다. 수익성을 승인한 버전이 아니다.

## Strategy Tester 설정

1. `Ctrl+R`로 Strategy Tester를 연다.
2. Expert Advisor에서 `MentorScenarioTraderEA`를 선택한다.
3. Symbol은 XM의 실제 GOLD 심볼을 선택한다. 브로커에 따라 `GOLD`, `GOLDm`, `XAUUSD` 중 Market Watch에 있는 이름을 사용한다.
4. Period는 `M1`로 설정한다.
5. Model은 `Every tick based on real ticks`로 설정한다.
6. Date는 `2024.12.01 00:00`부터 `2025.01.11 00:00`까지로 설정한다. 12월은 HTF warm-up이고, EA 내부 `InpTradeFrom/InpTradeTo`가 실제 거래 집계를 1월 6~10일로 제한한다.
7. Inputs에서 `MentorScenarioTraderEA.GOLD.M1.2025-W02.set`을 불러온다.
8. Visual mode는 첫 실행에서 켜지 않아도 된다. 완료 후 Experts/Journal 로그에서 `SCENARIO_ARMED`, `ORDER_SENT`, `ORDER_REJECTED`, `SCENARIO_CANCELLED`를 확인한다.

## 확인할 값

첫 실행에서 수익률보다 먼저 다음을 기록한다.

- 거래 횟수와 주문 발생 시각
- owner timeframe: H4/H1/M30
- refinement timeframe: M15/M5
- sweep과 CHoCH 이후에만 주문됐는지
- SL이 parent OB가 아닌 entry zone과 sweep extreme 바깥에 있는지
- TP가 고정 objective인지
- objective 선도달·source-TF 무효화 취소가 작동했는지
- `ORDER_REJECTED`의 retcode와 설명

## 결과 파일

테스트 결과 HTML/CSV와 Journal의 거래 목록을 보존한다. 같은 기간을 다시 돌릴 때는 결과를 덮어쓰지 말고 파일명에 `mentor-v1-week2`를 붙인다.

첫 비교 기준은 수동 원장의 11건과 숫자가 같은지가 아니다. 같은 날짜의 신호가 같은 owner·source·sweep·CHoCH·objective를 갖는지부터 비교한다. 차이가 있으면 승률을 높이기 전에 사건 귀속부터 수정한다.
