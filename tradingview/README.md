# TradingView ICT Scripts

## Current indicator

- `ict_cockpit_indicator.pine`: Pine v6 정보 표시용 ICT 지표

이 지표는 사용자의 판단을 돕기 위해 OB, FVG, 구조, 유동성 정보를 표시합니다. 자동 setup, 방향 추천, 주문 권한으로 사용하지 않습니다.

## Other scripts

- `ict_cockpit_strategy.pine`: 과거 단순화 전략 연구
- `ict_zone_reaction_archive.pine`: 과거 FVG/OB 반응 영역 보관 표시

strategy 결과는 현재 수동 매매 계약이나 Mentor AI Replay V4의 성과가 아닙니다.

## Static check

```powershell
python scripts\check_pine_static.py tradingview\ict_cockpit_indicator.pine
```

정적 검사는 Pine 문법의 일부만 확인합니다. 최종 검증은 TradingView Pine Editor의 v6 compile과 실제 차트 이동·시간봉 전환으로 수행합니다.
