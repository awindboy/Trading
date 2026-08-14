# MT5 Assets

## Current operational files

- `experts/TradeJournalExporterEA.mq5`: 수동 거래와 SL/TP 변경, 종료 이벤트를 일지로 내보내는 운영 EA
- `indicators/ICTCockpitIndicator.mq5`: MT5 표시용 ICT 지표
- `indicators/CleanChartTimeOverlay.mq5`: 차트 오버레이 정리 도구

## Research and legacy trading EAs

- `legacy/MentorCausalStateEA.mq5`
- `legacy/MentorScenarioTraderEA.mq5`
- `legacy/MentorSep2025ParityEA.mq5`

위 EA는 과거 자동매매·parity 연구 자산이며 현재 실거래 승인본이 아닙니다. 관련 `.set`, `.ex5`, compile log도 재현을 위해 보존합니다.

## Tester artifacts

`tester/`에는 Strategy Tester 설정과 보고서가 있습니다. 해당 결과를 현재 성과로 인용하기 전에 사용 EA, 설정 파일, 기간, symbol specification을 확인합니다.

설치 스크립트:

```powershell
npm run install-mt5-ea
npm run install-mt5-indicator
```
