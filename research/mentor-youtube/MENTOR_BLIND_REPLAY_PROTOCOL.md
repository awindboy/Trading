# Mentor Q1 Blind Replay Protocol

## 목적

이 재생의 목적은 기존 EA가 만든 후보를 평가하는 것이 아니다. 21개 영상에서
확인한 스승님의 판단 절차만 사용해 GOLD 2025 Q1을 시간순으로 다시 읽고,
설명 가능한 거래와 비거래 결정을 독립적인 정답지로 만드는 것이다.

성과 수치는 스승님 본인의 실제 성과가 아니라, 영상만 학습한 분석자가 같은
절차를 결정론적으로 적용했을 때의 재현 성과다.

## 정보 경계

- 입력은 원본 M1 OHLC, tick volume, spread뿐이다.
- `mentor_engine`의 structure, liquidity, zone, sweep, scenario, candidate 출력은
  보지 않는다.
- 모든 시간봉은 M1 확정봉만 집계한다.
- 각 결정은 해당 시각까지 닫힌 캔들만 사용한다.
- 진입, SL, TP를 확정한 뒤에만 이후 캔들을 열어 결과를 판정한다.
- Q1 전체 결과를 본 뒤 거래를 추가하거나 삭제하지 않는다.
- replay 도구는 현재 `as_of` 패킷 하나만 공개한다. 현재 판단을 원장에
  기록하기 전에는 다음 패킷을 만들 수 없다.
- 완성 원장이 봉인되기 전에는 기존 알고리즘 출력과 대조하거나 경제 성과를
  계산하지 않는다.

## 무효 처리된 1차 시도

2026-07-17에 만든 full-day weekly sheet, future-excursion opportunity index와
zoom queue는 이 정보 경계를 위반했다. 해당 파일은
`output/mentor_blind_q1/_invalid_retrospective_locator/`로 격리했으며 정답 원장,
거래 수, 승률, 수익률 계산에 사용하지 않는다.

## 고정 판단 순서

1. H4/H1/M30에서 외부 구조, 내부 구조, 현재 가격 전달 방향을 문장으로 적는다.
2. 다음 목적 유동성을 하나 정하고, 다른 참가자의 손절이 왜 그곳에 모이는지 적는다.
3. 목적지 반대편의 출발 유동성과 스윙 고점·저점 부근의 fresh HTF OB를 찾는다.
4. HTF OB를 H1/M30/M15/M5로 내려가며 동일 스윙과 displacement를 설명하는 마지막 LTF OB로 최소 한 단계 이상 세분화한다.
5. 가격이 source context에 닿고 유동성을 관통한 뒤 회복할 때까지 기다린다.
6. M5는 correction 맥락을 확인하고 M1에서 live structure의 몸통 종가 CHoCH를 확인한다.
7. CHoCH displacement가 새로 만든 M1 FVG를 최초 entry zone으로 정한다. HTF/LTF
   OB refinement는 source와 구조적 SL 근거로 유지한다.
8. FVG 형성 봉이 닫힌 뒤 entry, SL, TP를 동결한다. 같은 봉 체결은 허용하지 않는다.
9. 체결 후에는 최초 SL 또는 TP만으로 결과를 판정한다.

## 시간 진행 방식

- **Map 단계**: H1 종가마다 H4/H1 구조와 목적지를 갱신한다. M30은 새로운 HTF OB를
  세분화하거나 H1 구조가 불명확할 때만 연다. 이 단계에서는 M1을 사람이 읽지 않는다.
- **대기 단계**: parent OB와 최소 하나의 causal LTF OB를 미리 선언한 뒤, 가격이
  해당 OB에 처음 닿는 시각까지 점프한다. 도구는 숨겨진 M1 OHLC를 오직 OB 접촉,
  objective 선도달, 구조 무효화 시각을 찾는 중립적 정지 조건으로만 사용한다.
- **Trigger 단계**: OB 접촉 이후에만 M5를 확인하고, 정밀한 sweep·CHoCH 판정이
  필요할 때 M1을 한 봉씩 공개한다. trigger episode가 거래 또는 비거래로 종결되면
  다시 H1 map 단계로 돌아간다.
- **Execution 단계**: 주문 동결 뒤 M1은 체결·SL·TP 순서 판정에만 사용한다. 이 데이터는
  새로운 방향이나 사후 entry 가격을 만드는 데 사용하지 않는다.

따라서 Q1 전체 M1을 처음부터 끝까지 눈으로 재생하지 않는다. 세밀한 관찰 비용은
미리 선언한 OB에 실제로 가격이 도달한 구간에만 지불한다.

## 거래 승인 계약

아래 항목을 모두 구체적인 가격과 시각으로 설명할 수 있어야 한다.

- `scope`: external continuation, internal rotation, external reversal 중 하나
- `map`: 외부/내부 구조와 활성 전달 방향
- `objective`: 목적 유동성과 참가자 손절 근거
- `sourceLiquidity`: 반대편 출발 유동성과 참가자 손절 근거
- `contextZone`: HTF parent OB와 causal LTF child OB의 시간봉, 생성 시각, 가격 범위, 동일 displacement 근거
- `sweep`: 관통한 가격과 회복 종가
- `choch`: 깨진 live structure 가격과 몸통 종가 확정 시각
- `entryZone`: CHoCH displacement가 만든 M1 FVG, execution OB, sweep extreme
- `entry`, `sl`, `tp`: 진입 전에 동결된 가격
- `invalidation`: 왜 SL에 닿으면 최초 시나리오가 틀린 것인지

`최근 고점`, `최근 저점`, `가까운 FVG`, `추세 같음`만으로 설명되는 항목이
하나라도 있으면 거래하지 않는다.

## 비거래 원장

거래가 없었던 날도 다음 중 하나로 이유를 남긴다.

- 목적 유동성을 하나로 정할 수 없음
- source liquidity에 참가자 손절 근거가 없음
- fresh HTF OB 또는 인과적인 LTF OB refinement가 없음
- source context 미도달
- sweep 없이 반응함
- CHoCH가 없거나 내부 잡음만 파괴함
- CHoCH-owned entry zone이 없음
- entry zone retest가 없음
- 목적지가 entry 전에 이미 전달됨
- 서로 반대인 시나리오가 동시에 살아 있음

## 별도 집계

- 기본형: sweep -> CHoCH -> CHoCH displacement M1 FVG -> retest
- 확인형: sweep -> CHoCH -> 별도 BOS -> BOS displacement M1 FVG -> retest

두 프로토콜은 같은 거래를 중복 집계하지 않고 결과를 별도로 표시한다. 기본
성과표는 영상에서 더 넓게 반복된 기본형을 사용한다.

최초 FVG 진입은 기본형에 포함한다. 기존 포지션의 TP 전달 중 FVG 되돌림
추가진입은 `DELIVERY_FVG_ADDON`으로 별도 집계하되, 동일 owner와 objective가
유지되고 새 causal displacement와 execution OB를 설명할 수 있어야 한다.

## 결과 보고

- 총 승인 시나리오, 미체결, 체결, 승/패, 승률, 합계 R, 평균 R, Profit Factor
- 월별 합계 R
- 거래별 map/context/trigger 시간봉, entry/SL/TP, holding time
- 각 손실의 `확률적 손실`, `논리 오류`, `실행 오류` 분류
- 모든 거래의 7문장 한국어 설명과 MTF 차트
- 포지션 표시는 entry/SL/TP 선이 아니라 반투명 포지션 박스로만 렌더링
