# Mentor Weekly Scenario Protocol V2

## 0. 이 문서가 고정하는 것

이 규칙은 2025-04-07~11 GOLD 전체 경로와 스승님 영상 2·3·11·13편을 함께
대조해 만든 실행 계약이다. 개별 손실을 피하기 위한 필터가 아니다. 다음
블라인드 주간에서도 같은 구조라면 같은 map, source, entry, SL, TP를 선택한다.

핵심 분리는 다음과 같다.

- **H1/M30 OB**: 가격이 반응할 원인 위치와 큰 시나리오
- **M15/M5 refinement**: 동일 스윙 안에서 source와 무효화 범위를 좁힘
- **M1 sweep/CHoCH**: 실제 전환 확인
- **M1 FVG**: 주문을 둘 실행 가격
- **외부 유동성**: 사전에 동결할 TP

## 1. Map과 목적지

1. H1 외부 구조로 활성 전달 방향을 하나 정한다. M30/M15는 H1 map 안의 내부
   조정과 source 위치를 설명할 뿐, 작은 CHoCH 하나로 H1 방향을 바꾸지 않는다.
2. H1 map은 반대편 외부 유동성이 먼저 소진되고, H1 protected swing이 반대
   방향 몸통 종가로 깨질 때만 외부 반전으로 바뀐다.
3. 외부 반전이 확인되지 않은 반대 이동은 `INTERNAL_ROTATION`이며, 목표도
   처음 만나는 내부 유동성까지만 허용한다.
4. TP는 진입 전에 존재한 가장 가까운 미소진 목적 유동성의 실제 가격이다.
   반복 방어 고저점, range edge, equal high/low, 오래 유지된 외부 swing처럼
   다른 참가자의 손절이 모일 이유가 있어야 한다.
5. objective가 없거나 이미 소진됐으면 주문하지 않는다. 더 먼 목표를 사후에
   붙이거나 RR로 대체하지 않는다.

## 2. 최초 반응 source

1. 최초 반응 시나리오는 H1 또는 M30의 의미 있는 swing 부근 fresh OB에서
   시작한다. HTF FVG 단독 접촉은 source가 아니다.
2. parent OB는 의미 있는 유동성 사건 뒤 protected swing을 몸통으로 깬
   displacement 직전의 마지막 반대색 캔들이다.
3. H1→M30→M15→M5 순서로 같은 swing과 displacement를 설명하는 child OB를
   찾는다. 단순 가격 중첩은 refinement가 아니다.
4. 서로 떨어진 child가 경쟁하면 가장 작은 zone을 임의 선택하지 않는다.
   하나의 lineage가 확인될 때만 좁히고, 아니면 마지막으로 유일했던 부모
   시간봉을 source로 유지한다.
5. map, objective, parent/child OB, source invalidation을 가격 도달 전에 동결한다.
   source에 오기 전 M1 신호는 거래하지 않는다.

## 3. M1 trigger와 최초 entry

1. source 접촉 뒤 M5는 correction 맥락만 확인하고 trigger는 M1에서만 판정한다.
2. 진입 반대편에 사전에 형성된 실제 M1 유동성이 필요하다. source 첫 반응이
   새로운 reaction high/low를 만들었다면, 이후 재접촉에서 그 수준이 sweep될
   때까지 같은 source를 유지할 수 있다.
3. wick이 그 유동성을 관통하고 종가가 안쪽으로 회복해야 sweep이다.
4. sweep 뒤 별도 M1 봉이 반대 파동의 live protected swing을 몸통 종가로 깨야
   CHoCH다. sweep과 CHoCH를 같은 봉의 단순 움직임으로 합치지 않는다.
5. CHoCH displacement가 만든 첫 fresh 3-candle wick FVG를 entry zone으로
   동결한다. FVG 형성 봉이 닫힌 뒤의 retest만 체결 가능하다.
6. long entry는 bullish FVG의 위쪽 proximal boundary, short entry는 bearish
   FVG의 아래쪽 proximal boundary다.
7. CHoCH displacement에 FVG가 없으면 기본형 거래도 없다. 기존 source OB
   경계로 주문을 되돌리지 않는다.

## 4. 연속 전달과 여러 FVG

1. 활성 H1 map 방향 displacement가 이전 objective를 몸통으로 돌파하고 다음
   objective가 이미 존재하면 새 continuation delivery가 시작된다.
2. 이때 기존의 깊은 source OB를 기다리지 않는다. 구조 돌파 displacement가
   만든 M1 FVG retest를 최초 체결이면 `DELIVERY_FVG_REPLACEMENT`, 기존 포지션이
   있으면 `DELIVERY_FVG_ADDON`으로 기록한다.
3. 한 번의 중단 없는 displacement 안에서 같은 execution OB가 만든 연속 FVG는
   여러 거래가 아니라 하나의 family다. 아직 체결되지 않은 동안 같은 impulse가
   더 진행되며 새 FVG를 만들면, entry candidate를 현재 가격에 더 가까운
   proximal FVG로 갱신한다. 한 번 체결된 뒤에는 바꾸지 않는다.
4. 가격이 되돌아 protected correction swing을 만든 뒤 다시 map 방향으로
   displacement하면 새 execution OB와 새 FVG가 생긴다. 이것은 같은 objective를
   향하더라도 독립 family이므로 새 진입 또는 추가진입이 가능하다.
5. 앞선 family의 손절만으로 H1 map과 objective를 폐기하지 않는다. source
   invalidation과 map protected swing이 살아 있고 새 correction→displacement
   chain이 완성되면 같은 objective로 다시 시도한다.
6. 각 독립 family는 1R로 기록한다. 기존 포지션 보유 중의 add-on도 별도 1R이며
   총 open risk를 합산 보고한다. 임의 횟수 상한 대신 새 protected correction
   swing과 새 displacement가 없는 중복 gap 주문을 금지한다.
7. continuation FVG도 standalone 신호가 아니다. 활성 map, 다음 objective,
   objective를 돌파한 causal displacement, execution OB가 모두 필요하다.

## 5. SL

1. 최초 OB 반응 FVG의 SL은 CHoCH displacement를 시작한 M1 execution OB distal,
   sweep extreme, 마지막 인과적 M15/M5 refined source OB distal 중 더 먼
   구조 바깥에 둔다.
2. continuation FVG의 SL은 해당 delivery displacement의 M1 execution OB distal,
   correction protected swing, 그 delivery를 소유한 마지막 M15/M5 causal OB
   distal 중 더 먼 구조 바깥에 둔다.
3. M1 sweep extreme만 기계적으로 SL로 사용하지 않는다. 반대로 H1 parent OB
   전체 폭을 항상 강제하지도 않는다.
4. buffer는 현재 spread, broker stops level, 1 tick 중 최댓값만 사용한다.
5. SL까지의 거리가 커도 구조를 손익비에 맞춰 좁히지 않는다. 거래 크기를 줄인다.

## 6. TP와 주문 취소

1. TP는 동결한 objective의 정확한 가격이다. 유동성 너머 offset, 최대 R,
   RR fallback, 시간 청산은 없다.
2. 진입 전에 objective가 먼저 도달하면 주문과 source episode를 종료한다.
3. source OB가 몸통으로 무효화되거나 entry FVG와 execution OB가 주문 체결 전에
   완전히 무효화되면 취소한다.
4. 체결 뒤에는 최초 SL 또는 TP로만 결과를 판정한다.

## 7. 비매매

- H1 map과 목적지를 사전에 한 문장으로 설명할 수 없음
- 참가자의 손절이 설명되는 objective가 없음
- HTF source가 FVG뿐이고 swing-owned OB가 없음
- parent와 child OB가 같은 가격 사건이라는 인과 계보가 없음
- source 도달 전 M1 CHoCH를 끼워 맞춤
- source 접촉 뒤 sweep 또는 별도 CHoCH가 없음
- CHoCH displacement에 fresh M1 FVG가 없음
- objective가 entry 전에 소진됨
- 외부 map 반대 거래를 내부 rotation으로 제한하지 못함

## 8. 손실 분류

다음 항목이 모두 사전에 충족된 손실만 `MARKET_UNCERTAINTY`다.

1. H1 map과 objective가 진입 전에 동결됨
2. source OB와 refinement lineage가 가격 도달 전에 존재함
3. source 접촉, sweep, 별도 M1 CHoCH 순서가 지켜짐
4. entry가 CHoCH displacement M1 FVG의 이후 retest임
5. SL이 execution OB/sweep 구조 바깥임
6. TP가 미소진 실제 유동성 가격임

하나라도 빠지면 시장의 불확실성이 아니라 규칙 위반 또는 아직 정의되지 않은
지식의 빈 공간이다.

## 9. 블라인드 동결 항목

- H1 map 전환 조건
- external continuation과 internal rotation의 분리
- OB source와 FVG entry의 역할 분리
- M1 sweep → 별도 CHoCH → FVG → retest 순서
- 같은 impulse의 proximal FVG 갱신과 새 correction 뒤 독립 FVG의 구분
- execution OB와 refined source OB를 함께 보호하는 SL
- 정확한 liquidity TP
- objective 선도달 취소

블라인드 주간 중 손익을 보고 위 규칙을 추가·삭제하지 않는다.
