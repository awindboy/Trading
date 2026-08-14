# Mentor One-Week Replay Decision Protocol

## 목적

이 문서는 `2025-01-06 00:00 UTC`부터 `2025-01-10 23:59 UTC`까지 GOLD를
미래 봉 없이 수동 재생할 때 사용할 고정 판단 절차다. 기존 EA, V32 후보,
자동 zone 탐색 결과는 보지 않는다. 스승님 영상 21편에서 반복 확인된 흐름만
사용한다.

## 매 시점의 판단 순서

1. H1/M30에서 외부 구조와 현재 가격 전달 방향을 먼저 정한다.
2. 다음 목적지는 다른 참가자의 손절이 설명되는 유동성으로 정한다.
   오래된 외부 고저점, 여러 번 방어된 고저점, 횡보 경계, 반응 뒤 생긴
   trap만 인정한다. 단순 최근 pivot은 목적지가 아니다.
3. 목적지 반대편에서 가격을 다시 전달시킬 수 있는 **스윙 소유 OB**를 찾는다.
   HTF FVG는 이동의 비효율을 설명할 뿐 최초 진입 source로 쓰지 않는다.
4. H1 OB를 M30/M15/M5로 내려가 같은 스윙과 displacement를 설명하는 하위
   OB를 찾는다. 가격만 겹치는 별개 OB는 refinement가 아니다.
5. 이 시점에 map, 목적지, parent OB, refined OB, 무효화 가격을 먼저 동결한다.
   가격이 refined OB에 도달하기 전에는 M1을 열지 않는다.
6. OB 도달 뒤에는 그 자리에서 새로 형성됐거나 사전에 존재하던 의미 있는
   유동성의 sweep을 확인한다. OB 접촉 자체는 진입 신호가 아니다.
7. M5는 correction 맥락만 확인하고 실제 trigger는 M1에서 판정한다. 진행 중 반대
   파동의 live swing을 몸통 종가로 돌파하는 CHoCH가 필요하며, 꼬리 돌파나 작은
   캔들 한두 개는 전환으로 보지 않는다.
8. 기본 재생은 CHoCH displacement가 새로 만든 M1 FVG의 이후 retest에 진입한다.
   HTF/LTF OB refinement는 source와 SL 근거이며 entry limit 가격이 아니다.
   원래 HTF OB 반응 주문을 놓친 뒤 목적지 방향 displacement가 출발하면 그
   움직임이 만든 첫 M1 FVG retest를 `DELIVERY_FVG_REPLACEMENT`로 사용한다.
   기존 포지션이 있으면 별도 chain의 `DELIVERY_FVG_ADDON`으로 기록한다.
9. M1 sweep extreme은 trigger 무효화일 뿐 자동 SL이 아니다. SL은 causal LTF OB,
   source/refinement protected swing, map owner가 틀리는 구조 가격 중 시나리오가
   정상적으로 허용하는 경로를 모두 벗어난 곳에 둔다. 세부 규칙은
   `SCENARIO_SL_AND_DELIVERY_FVG_PROTOCOL.md`를 따른다.
10. TP는 처음 정한 목적 유동성에 둔다. 최대 R, RR fallback, 시간 청산은 없다.

## 시나리오 유형

### `HTF_OB_REACTION`

- 주로 H1 스윙 고점/저점 부근의 fresh OB에서 시작한다.
- M30/M15/M5의 동일 스윙 OB로 세분화한다.
- 진입 계약: `OB 접촉 -> M5 correction 맥락 -> M1 sweep -> M1 CHoCH
  -> CHoCH displacement M1 FVG -> 이후 retest`.
- 이번 주간 재생의 기본형이다.

### `OLD_SWING_FVG_REVERSAL`

- 오래 유지된 외부 고점/저점의 큰 유동성이 먼저 sweep된 경우다.
- M1에서 추세가 실제로 전환되고 그 과정에 FVG가 생긴 경우에만 FVG retest를
  사용한다.
- 일반 OB 반응과 섞지 않고 별도 집계한다.

### `REACTION_TRAP_FVG_REVERSAL`

- 방향과 목적지가 먼저 정해졌지만 HTF zone에 반응 유동성이 없으면 기다린다.
- zone 반응으로 다른 참가자의 손절이 모일 고저점이 만들어지고, 그 trap을
  sweep한 뒤 M5 구조가 전환될 때만 사용한다.
- 진입은 전환 displacement가 만든 M5 FVG retest다. 이는 영상 16편의 별도
  실행 사례이며 일반 OB refinement 진입과 구분해 집계한다.

### `DELIVERY_FVG_ADDON`

- 최초 포지션이 이미 목적지를 향해 전달 중일 때 생긴 FVG 되돌림 추가진입이다.
- 기존 owner와 objective가 유효하고, 새 displacement가 구조 전달을 재확인하며,
  causal OB/protected swing을 설명할 수 있을 때 사용한다.
- 원래 OB 주문이 미체결이었다면 추가진입이 아니라
  `DELIVERY_FVG_REPLACEMENT`라는 최초 체결 경로로 기록한다.
- standalone FVG 매매와 구분하며
  `SCENARIO_SL_AND_DELIVERY_FVG_PROTOCOL.md`의 활성·취소·SL 규칙을 따른다.

## 명시적 비매매 조건

- 목적 유동성을 사전에 설명할 수 없음.
- source가 HTF FVG뿐이고 구조를 소유한 OB가 없음.
- parent와 causal child OB 계보를 설명할 수 없음.
- OB에 왔지만 sweep할 실제 유동성이 아직 형성되지 않음.
- sweep 뒤 M1 CHoCH가 없음.
- 내부 소음 구간에서 외부 전환으로 확대 해석해야만 성립함.
- 진입 전에 목적지가 먼저 소진됨.
- 이미 완전히 소비된 OB를 재사용해야만 성립함.

## 사후 변경 금지

각 주문은 결정 순간 entry, SL, TP, 시나리오 설명을 동결한다. 결과를 본 뒤
OB 경계, sweep, CHoCH, 목표를 다시 그리지 않는다. 손실은 `확률적 손실`,
`map 오류`, `OB 계보 오류`, `유동성 오류`, `trigger 오류`, `실행 오류` 중
하나로 귀속한다.
