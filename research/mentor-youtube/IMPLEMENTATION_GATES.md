# Mentor Engine Implementation Gates

이 문서는 수익률을 보고 나중에 붙이는 필터가 아니라, 구현이 스승님의 판단
순서를 거꾸로 만들지 못하게 막는 불변 조건이다. 아래 조건을 하나라도 위반한
빌드는 Q1 결과와 관계없이 폐기한다.

1. **목적지 우선**: 방향과 TP는 source liquidity sweep 전에 확정돼야 한다.
2. **지도 구조 소유권**: map timeframe은 source timeframe과 시간 간격이 가깝거나
   단순히 가장 높다는 이유로 선택하지 않는다. source 반대편에서 처음 만나는 완전한
   objective를 실제로 만든 timeframe과 그 구조 사건이 시나리오를 소유한다.
3. **OB 우선 source**: 최초 주문은 스윙 고점·저점 부근에서 미리 선택된 HTF OB가
   있어야만 활성화된다. HTF FVG 단독 touch는 source 또는 최초 진입 권한이 아니다.
4. **인과적 refinement**: 최소 하나의 하위 OB가 필요하다. 하위 OB는 상위 OB와
   겹치거나 동일한 상위 스윙의 바로 인접한 하위 구조이고, 같은 displacement를
   설명할 때만 진입 구간과 SL 기준을 위임받는다.
5. **LTF 역할 제한**: M1 CHoCH는 방향을 만들지 않는다. M5의 외부 trend와 내부
   correction leg를 분리하고, pre-sweep M5 correction이 source에서 끝났음을 확인할
   때만 이미 존재하는 시나리오의 trigger가 된다.
6. **경로 충돌 금지**: source가 활성 반대 delivery zone 안에 있으면 계획을 만들지
   않는다. 내부 회전 TP는 유동성과 반대 FVG 중 먼저 만나는 목적지를 사용한다.
7. **고정 목적지**: trigger 뒤 더 유리해 보이는 TP로 교체하지 않는다. objective가
   먼저 소진되면 주문하지 않는다.
8. **시나리오 무효화 바깥 SL**: M1 sweep extreme은 trigger 폐기 기준이지 자동
   포지션 SL이 아니다. SL은 마지막 causal LTF OB, 그 OB가 소유한 protected swing,
   map owner와 objective가 틀리는 structure level 중 시나리오가 허용하는 경로를
   모두 벗어난 곳에 둔다. 인과적 refinement가 증명된 경우에만 HTF parent zone
   전체 폭을 손절로 강제하지 않는다.
9. **충돌 시 대기**: 서로 다른 owner 또는 objective가 같은 trigger를 주장하면 가장
   최근 context를 고르지 않고 주문을 보류한다.
10. **전 계보 기록**: 모든 주문은 plan, map structure, objective, source pool,
   parent/refinement zone, sweep, CHoCH, entry zone ID를 원장에 남긴다.
11. **회귀 금지**: `Q1_SCENARIO_REVIEW_FIXTURES.json`의 `NO_TRADE` 시각에 같은 방향
    주문이 다시 생기면 통합 검증은 실패한다.
12. **Delivery FVG 실행**: 최초 OB 주문이 미체결인 채 objective 방향 displacement가
    출발하면 첫 FVG retest를 `DELIVERY_FVG_REPLACEMENT`로 허용한다. 기존 포지션이
    있으면 별도 chain의 `DELIVERY_FVG_ADDON`으로 허용한다. 둘 다 기존 owner와
    objective, 구조를 재확인한 displacement, causal OB/protected swing이 있어야
    하며 standalone FVG는 주문 권한이 없다.

## 완료 조건

- 정적·synthetic 검사가 위 12개 계약을 확인한다.
- Q1 replay 결과에 plan funnel과 거절 이유가 공개된다.
- 경제 목표 미달을 임의 점수나 ATR 필터로 가리지 않는다.
- 코드가 위 계약을 통과해도 수익성이 입증되기 전에는 자동매매 EA로 승인하지 않는다.
