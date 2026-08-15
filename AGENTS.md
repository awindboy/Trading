# 스승님식 수동 매매 절대 실행 계약

- 상태: `FROZEN / MANUAL-TRADING AUTHORITY`
- 제정일: `2026-08-01`
- 최근 개정: `2026-08-15` (`최초 진입을 CHoCH displacement FVG retest로 정정하고 widest-FVG 선택·FVG 기반 SL 규칙 추가`)
- 적용 범위: 수동 차트 분석, 블라인드 리플레이, 데모 매매 판단

## 1. 문서의 지위

이 문서는 사용자가 `스승님식으로 매매해`, `스승님 방식으로 차트를 봐`, `직접 매매해`라고 요청했을 때
내가 가장 먼저 적용해야 하는 수동 매매 실행 계약이다.

- 전략 근거는 이 폴더에 정리된 스승님의 21개 영상으로 제한한다.
- 일반 ICT/SMC 지식, 기존 EA, V32, 점수 모델, 역설계 결과는 거래를 허가할 수 없다.
- 과거 문서나 기존 관행과 충돌하면 이 문서의 **비매매 원칙과 원인 우선순위**를 따른다.
- 모호한 부분을 임의의 ICT 개념으로 채우지 않는다. 설명할 수 없으면 `비매매`다.
- 결과가 수익이어도 이 계약을 위반한 거래는 스승님식 성과에 포함하지 않는다.

스승님식 최초 진입의 기본 순서는 다음과 같다.

```text
목적 유동성
-> H1/M30 시장 지도
-> 스윙 근처의 사전 형성 HTF root OB
-> 같은 가격 사건을 설명하는 causal LTF OB refinement
-> refined OB 접촉
-> 사전에 존재하던 유동성 sweep
-> M1의 의미 있는 몸통 CHoCH
-> 같은 sweep-to-CHoCH causal leg의 fresh FVG
-> valid FVG 중 가장 넓은 FVG 선택
-> 선택된 FVG의 첫 retest
-> LONG은 FVG 상단 / SHORT은 FVG 하단 진입
-> FVG distal 바깥으로 FVG 폭의 20%를 둔 SL
-> 처음 동결한 목적 유동성 TP
```

이 순서에서 앞 단계가 없으면 뒷 단계는 아무리 선명해도 거래 근거가 아니다.

아래 `DELIVERY_FVG_REPLACEMENT` 대체 실행 경로는 기존 계약을 역사적으로 보존한다. 최초 포지션 기본형이 `INITIAL_CHOCH_FVG`로 정정되었으므로 **현재 V1에서는 RE-AUDIT REQUIRED / 주문 권한 비활성**이며, 별도 감사 전까지 새 주문에 사용하지 않는다.

기존 계약은 다음과 같다.

```text
동결된 owner / 방향 / objective / HTF-to-LTF OB lineage
-> 원래 OB 주문 미체결
-> 목적지 방향의 명확한 displacement와 구조 전달 재확인
-> displacement가 만든 fresh FVG와 causal OB
-> 기존 넓은 OB pending 취소
-> fresh FVG의 첫 되돌림
-> DELIVERY_FVG_REPLACEMENT 진입
-> displacement causal OB / protected swing / 원래 시나리오 무효화 바깥 SL
-> 처음 동결한 동일 objective TP
```

이 경로는 FVG가 새 시나리오를 만드는 것이 아니다. 이미 완성된 HTF 시나리오가 가격 전달로 확인됐을 때 **미체결 원주문의 실행 위치만 교체**한다.

## 2. 시간봉의 고정 역할

사용 시간봉은 `H1 / M30 / M15 / M5 / M1`이다. H4는 기본 매매 판단에서 사용하지 않는다.

| 역할 | 시간봉 | 해야 하는 일 | 해서는 안 되는 일 |
| --- | --- | --- | --- |
| Map | H1, M30 | 외부/내부 구조, 현재 파동, 목적 유동성, 의미 있는 스윙과 root OB를 정한다. | 최근 고저점을 무조건 외부 유동성으로 승격하지 않는다. |
| Refinement | M30, M15, M5 | 상위 OB와 같은 스윙 및 displacement를 설명하는 하위 OB를 찾는다. | 가격이 겹친다는 이유만으로 무관한 작은 OB를 연결하지 않는다. |
| Correction context | M5 | refined OB 안에서 진행되는 correction과 sweep 후보의 맥락을 확인한다. | M5 신호만으로 최초 포지션을 허가하지 않는다. |
| Trigger | M1 | OB 접촉 뒤 sweep, 의미 있는 CHoCH, execution zone을 확인한다. | POI가 정해지기 전에 M1에서 진입 후보부터 찾지 않는다. |

M1은 **시나리오를 만드는 시간봉이 아니라 이미 존재하는 시나리오의 반응을 확인하는 시간봉**이다.

## 3. 목적지와 시장 지도

### 3.1 목적 유동성을 먼저 정한다

진입 방향을 생각하기 전에 scenario scope와 그 scope가 설명할 수 있는 ordered objective family를 정한다. 최종 TP 하나는 아직 정하지 않으며, Entry와 hard SL이 확정된 뒤 pre-frozen family에서 planned R `>= 1`인 가장 가까운 scope-compatible candidate를 선택한다. 목적 후보군은 가까운 순서만으로 구성하지 않고 **외부 구조를 계속 전달하는 거래인지, 외부 범위 안에서 잠시 회전하는 거래인지**를 먼저 구분한다.

- PLAN은 임의의 TP 하나를 미리 확정하는 것이 아니라 동일 owner 경로의 순서가 고정된 `objective family`를 Entry/SL geometry가 알려지기 전에 동결한다.
- PLAN 시점에 `scenario_scope`, `owner`, `direction`, `objective_candidate_ids`, 각 candidate의 가격/종류/순서를 고정한다.
- Entry와 hard SL이 확정된 뒤에는 새로운 liquidity candidate를 추가하거나 후보 순서를 바꿀 수 없다.
- `EXTERNAL_CONTINUATION` family는 현재 H1/M30 외부 방향의 미소진 H1/M30 external liquidity로 구성한다.
- `INTERNAL_ROTATION` family는 외부 구조가 바뀌었다고 확대하지 않고, 현재 dealing range 안의 의미 있는 M15 이상 internal liquidity로 구성한다.
- `EXTERNAL_REVERSAL`은 반대 방향 M1 CHoCH만으로 선언하지 않는다. Mature H1 owner가 유지되는 동안에는 Section 3.2.2의 reversal-reference external extreme interaction으로 반대 방향 reversal permission이 먼저 열려야 한다. Permission이 열린 뒤 deterministic한 opposite M30/LTF structure와 valid opposite Root/source lineage가 형성되면 H1 trend label이 아직 기존 방향이어도 early `EXTERNAL_REVERSAL` scenario를 만들 수 있다. H1 protected swing body-break와 새 mature H1 owner 확인은 early reversal의 선행조건이 아니다.
- `EXTERNAL_CONTINUATION`의 entry와 external objective 사이에 있는 내부 유동성은 최종 external TP 후보가 아니라 `INTERMEDIATE_DELIVERY`로 기록한다.
- Entry와 hard SL이 확정되면 frozen objective family를 방향상 가까운 순서대로 검사한다.
- 아직 미소진이고 scenario scope와 호환되며 planned R `>= 1`인 최초 candidate를 최종 TP로 선택한다.
- planned R `< 1`인 valid liquidity는 삭제하지 않고 `INTERMEDIATE_DELIVERY`로 기록하며 final TP 자격만 제외한다.
- `planned R >= 1`은 거래 전체를 즉시 거부하는 필터나 최대 RR을 찾는 최적화 규칙이 아니라 `objective candidate eligibility` 조건이다.
- R이 더 크다는 이유만으로 더 먼 candidate를 선택하지 않는다. 같은 candidate tier에서는 가장 가까운 R-eligible liquidity가 우선한다.
- `INTERNAL_ROTATION`에서도 가장 가까운 internal liquidity가 planned R `< 1`이라는 이유만으로 시나리오를 즉시 종료하지 않는다. frozen internal family 안에서 가장 가까운 R-eligible mature M15+ internal liquidity를 찾는다.
- `INTERNAL_ROTATION`은 1R을 만들기 위해 external liquidity를 TP로 승격하지 않는다.
- `INTERMEDIATE_DELIVERY`가 CHoCH 또는 delivery displacement 과정에서 소진돼도, selected objective·owner·source lineage가 그대로라면 그것만으로 pending order를 취소하거나 TP를 재지정하지 않는다.
- 목적 유동성은 다른 참여자가 실제로 손절을 둘 만한 스윙, 반복 방어된 range edge, reaction trap 등이어야 한다.
- 단순 최근 pivot, 라운드 넘버, 이미 소진된 고저점은 목적 유동성이 아니다.
- 비교할 수 없는 owner 경로의 목적지가 여러 개 남으면 하나의 family로 섞지 않고 별도 scenario lane으로 유지한다.
- External scenario의 PLAN packet은 current-structure family 바깥 방향의 causally-known 미소진 H1 external liquidity 중 방향상 가장 가까운 최대 `2개`를 비활성 fallback tier로 함께 동결할 수 있다.
- Historical H1 fallback은 H1-owned `EXTERNAL_CONTINUATION` 또는 old owner가 무효화되고 새 mature H1 owner가 확정된 이후의 HTF-confirmed `EXTERNAL_REVERSAL`에서만 사용할 수 있다. Old H1 owner가 아직 active한 상태에서 reversal permission을 기반으로 생성된 early LTF-led `EXTERNAL_REVERSAL`, M30-primary `EXTERNAL_CONTINUATION`, `INTERNAL_ROTATION`에서는 사용하지 않는다.
- Historical H1 fallback도 Entry/SL geometry가 알려지기 전에 candidate와 순서가 동결되어 있어야 한다. Entry/SL을 본 뒤 새 fallback liquidity를 탐색해서 추가하지 않는다.
- Current-structure tier에 planned R `>=1`인 valid candidate가 하나라도 있으면 historical fallback tier를 사용하지 않는다.
- Current-structure candidate가 없거나, 모두 소진됐거나, 모두 planned R `<1`인 경우에만 pre-frozen historical H1 fallback tier를 평가한다.
- Fallback tier에서도 planned R `>=1`인 가장 가까운 candidate를 선택한다. 가장 큰 R을 주는 candidate를 선택하지 않는다.
- 허용된 current/fallback frozen family 전체에 R-eligible candidate가 하나도 없을 때만 `NO TRADE / NO_R_ELIGIBLE_OBJECTIVE`로 처리한다.
- 처음 선택한 목적지가 멀수록 좋은 거래라고 판단하지 않는다. 큰 R은 올바른 원인과 가까운 구조 무효화에서 나오는 결과이지, TP를 임의의 먼 유동성으로 밀어서 만드는 수치가 아니다.
- Final TP는 selected FVG Entry와 Section 9 규칙의 hard SL이 확정된 뒤, pending order 제출 전에 동결한다.
- Final TP가 동결된 뒤 주문 체결 전에 해당 objective가 먼저 소진되면 기존 시나리오와 pending order를 취소한다. 같은 scenario 안에서 다음 family member로 TP를 자동 rollover하지 않는다.

TP는 해당 유동성의 실제 wick 가격에 둔다. 스윕 가능성을 무시하고 유동성보다 더 멀리 TP를 밀지 않는다.

### 3.2 외부와 내부를 혼동하지 않는다

- H1/M30 protected swing과 dealing range를 먼저 표시한다.
- 그 범위 안의 M15/M5 저점과 고점은 우선 내부 구조로 취급한다.
- 내부 저점 sweep만으로 H1 외부 반전을 선언하지 않는다.
- 외부 구조가 남아 있는데 M1 CHoCH가 발생해도 그것은 우선 내부 반응이다.

`내부 유동성 -> M1 CHoCH`를 `외부 반전`으로 승격하는 것은 금지한다.

### 3.2.1 H1/M30 추세는 causal protected swing으로 판정한다

3-candle wave는 추세 자체가 아니라 swing 후보를 확정하는 detector다.

확정된 모든 wave를 외부 구조로 승격하지 않는다.

각 map timeframe은 먼저:

trend = NEUTRAL

에서 시작하며, 상승/하락의 양쪽 confirmed swing이 모두 존재하는 two-sided range가 만들어지기 전에는 directional external trend를 선언하지 않는다.

Bullish initial structure:

confirmed swing high + confirmed swing low
→ swing high를 body close로 상향 돌파
→ bullish external state
→ 반대편 confirmed swing low가 최초 protected low

Bearish initial structure:

confirmed swing high + confirmed swing low
→ swing low를 body close로 하향 돌파
→ bearish external state
→ 반대편 confirmed swing high가 최초 protected high

Wick-only breach는 trend initialization 또는 trend reversal이 아니다.

Protected swing은 단순 latest opposite swing이 아니다.

Bullish continuation BOS가 발생할 때:

1. 돌파 대상이었던 기존 external high의 발생 이후부터 BOS close까지를 correction window로 잡는다.
2. 그 window 안에서 BOS close 시점까지 이미 confirmed / available인 swing low만 후보로 사용한다.
3. 후보 중 가장 낮은 confirmed swing low를 해당 BOS를 만든 `causal correction low`로 본다.
4. 그 causal correction low만 새 protected low로 승격할 수 있다.
5. 해당 후보가 없으면 기존 protected low를 유지한다.

Bearish continuation BOS는 대칭적으로:

1. 기존 external low 이후부터 BOS close까지의 correction window를 사용한다.
2. 이미 confirmed / available인 swing high만 후보로 사용한다.
3. 후보 중 가장 높은 confirmed swing high를 `causal correction high`로 본다.
4. 그 swing만 새 protected high로 승격할 수 있다.
5. 후보가 없으면 기존 protected high를 유지한다.

즉:

최근 swing
≠ 자동 protected swing

이며:

external BOS를 실제로 만든 correction extreme
= protected swing candidate

다.

BOS 시점에 아직 confirmed되지 않은 과거 swing을
나중에 확인됐다는 이유로 과거 protected swing으로 소급 승격하지 않는다.

Bullish external trend는:

close < current protected low

가 발생할 때만 외부 상승 구조가 무효화된다.

Bearish external trend는:

close > current protected high

가 발생할 때만 외부 하락 구조가 무효화된다.

Protected swing을 wick으로만 관통하고 종가가 다시 구조 안에서 마감되면
external trend는 뒤집히지 않으며 liquidity sweep 후보로만 본다.

Protected swing body-break가 발생하면 기존 external trend는 즉시 invalidated된다.

다만 반대편 mature external structure의 protected boundary가 아직 완성되지 않았다면
곧바로 완성된 반대 trend를 만들어내지 않고 `TRANSITION` 상태로 둔다.

새 반대 external trend는
다시 valid two-sided structure와 body-close directional confirmation이 확보된 뒤
mature directional state로 승격한다.

현재 protected swing / directional external extreme / BOS에 의해 승격된 causal correction swing이 아닌
나머지 confirmed waves는 기본적으로 INTERNAL로 유지한다.

External / internal 판정에는:

ATR threshold
minimum point distance
minimum retracement percentage
minimum bar count

같은 추가 크기 threshold를 사용하지 않는다.

Wave의 크기가 아니라
현재 external structure 안에서 맡는 causal role로 external 여부를 결정한다.

### 3.2.2 HTF trend-follow bias와 reversal permission

H1과 M30의 structure state는 독립적으로 유지하지만
매매 방향 authority는 동등하게 취급하지 않는다.

기본 원칙:

현재 mature HTF trend를 우선한다.

H1이 mature BULLISH / BEARISH라면
H1이 가장 높은 directional owner다.

H1 trend가 유효하고
현재 H1 directional external extreme과 아직 interaction하지 않았다면:

trade direction = H1 direction

만 first-position planning authority를 가진다.

예:

H1 BULLISH
M30 BEARISH
H1 reversal reference high 미도달

이면:

M30 bearish
= H1 bullish trend 내부 correction context

이며
그 사실만으로 SHORT trading lane을 만들지 않는다.

M30 opposite structure는 correction의 진행 정도와
향후 HTF-direction continuation 재개를 판단하는 context로 유지한다.

#### Reversal reference extreme

Mature bullish H1 owner:

현재 owner 흐름이 만들어낸
가장 높은 valid structural external high
= reversal-reference buy-side liquidity

Mature bearish H1 owner:

현재 owner 흐름이 만들어낸
가장 낮은 valid structural external low
= reversal-reference sell-side liquidity

Protected swing:
→ current H1 trend invalidation boundary

Reversal reference extreme:
→ opposite-direction reversal hypothesis permission boundary

#### Reversal permission

Bullish H1:

bar.high >= reversal_reference_high
→ SHORT reversal permission OPEN

Bearish H1:

bar.low <= reversal_reference_low
→ LONG reversal permission OPEN

Reference가 available된 이후의 movement만 interaction으로 인정한다.

External extreme interaction은:

H1 trend reversal
entry signal
automatic counter-trend trade

가 아니다.

그 event는 단지:

반대 방향 LTF structure를
평범한 correction이 아니라
potential external-reversal evidence로 평가할 permission

을 연다.

#### Sweep / rejection

Bullish extreme:

high > reference_high
AND
close <= reference_high

Bearish extreme:

low < reference_low
AND
close >= reference_low

이면 external liquidity sweep/rejection interaction으로 기록한다.

이 event는 reversal context를 강화하지만
점수나 자동 주문을 만들지 않는다.

Actual reversal order에는 여전히:

valid opposite scenario
→ Root/source lineage
→ source contact
→ mature pre-existing sweep
→ meaningful M1 CHoCH
→ causal displacement FVG
→ first retest

전체 chain이 필요하다.

#### Body-close continuation

Bullish:

close > reference_high

Bearish:

close < reference_low

이면 기존 trend 방향의 structure delivery/BOS로 처리한다.

old reference reversal permission
→ CLOSED

standard continuation BOS / protected-swing update
→ 실행

새 external extreme이 causal하게 확정되면
그 extreme을 다음 reversal reference로 사용한다.

#### Opposite M30 before reversal permission

H1 mature trend가 유지되는 동안
reversal permission이 CLOSED라면
opposite mature M30은 거래 가능한 역추세 owner가 아니다.

기존의:

H1 continuation lane
+
opposite M30 INTERNAL_ROTATION trading lane

병렬 first-position planning은 V1에서 사용하지 않는다.

M30 opposite trend는 correction context로만 추적한다.

#### Opposite LTF after reversal permission

HTF external extreme interaction으로
reversal permission이 OPEN된 뒤에는
opposite-direction M30/LTF structure를
external reversal hypothesis의 evidence로 사용할 수 있다.

단순 M30 opposite trend 하나만으로 order를 허가하지 않는다.

최소:

1. reversal permission OPEN
2. opposite-direction map/context가 deterministic하게 설명 가능
3. opposite Root/source lineage 존재
4. 기존 base execution chain 완료

가 필요하다.

H1 trend_state는 protected swing이 body-close로 깨지기 전까지
기존 BULLISH / BEARISH를 유지할 수 있다.

즉:

trade hypothesis may reverse before H1 trend label flips.

#### H1 owner invalidation

H1 protected swing body-break:

old H1 trend invalidated
→ H1 TRANSITION

이미 frozen된 early reversal scenario를
사후에 다른 scope로 다시 쓰지 않는다.

새 H1 owner 아래의 후속 scenario는
새 scenario_id로 생성한다.

#### H1 NEUTRAL / TRANSITION

H1에 mature directional owner가 없으면
mature M30을 temporary highest active map으로 사용할 수 있다.

M30 direction
→ M30-primary EXTERNAL_CONTINUATION

M30 dealing range와 M30 external objective family를 사용한다.

Old H1 dealing range와 historical H1 fallback을 자동 상속하지 않는다.

M1은 HTF reversal permission 또는 map owner를 생성하거나 덮어쓰지 않는다.

### 3.3 dealing range 위치를 진입 권한에 포함한다

- H1/M30의 현재 external protected high와 low로 active dealing range를 정하고 EQ 50%를 표시한다.
- `EXTERNAL_CONTINUATION` long은 discount에서만, short은 premium에서만 준비한다.
- continuation 방향의 POI가 반대 절반에 있으면 OB가 선명해도 정보로만 남기고 주문 권한을 부여하지 않는다.
- H1 mature trend가 유효하고 reversal permission이 CLOSED인 동안, 반대 방향 M30/LTF 구조는 기본적으로 HTF 내부 correction context다. V1은 이 상태에서 독립적인 역추세 first-position `INTERNAL_ROTATION` 주문을 허가하지 않는다.
- HTF reversal-reference extreme interaction으로 reversal permission이 OPEN된 뒤에만 opposite LTF structure를 external-reversal hypothesis의 context로 승격해 평가할 수 있다.
- premium/discount 위치는 단독 진입 신호가 아니다. 올바른 위치에 있더라도 root OB, causal refinement, mature sweep, M1 trigger가 모두 필요하다.

## 4. HTF root OB

최초 포지션의 원인은 사전에 존재하는 `H1`, `M30`, 또는 `M15` root OB여야 한다.

root OB는 다음을 모두 설명해야 한다.

1. 의미 있는 스윙 고점 또는 저점 부근에 있다.
2. 그 위치에서 실제 displacement가 출발했다.
3. 그 displacement가 의미 있는 구조 전달이나 몸통 돌파를 만들었다.
4. 아직 완전히 소비되거나 구조적으로 무효화되지 않았다.
5. 현재 목적 유동성 방향과 연결되는 이유를 말로 설명할 수 있다.

다음은 root OB가 아니다.

- 화면에서 가장 가까운 반대색 캔들
- M1 반응을 보고 사후에 선택한 HTF 캔들
- 구조 전달을 만들지 않은 임의의 캔들 묶음
- 단순히 FVG와 겹치는 캔들
- 이미 여러 번 완전히 체결된 OB
- HTF FVG 자체

HTF FVG는 가격 전달의 비효율을 보여줄 수 있지만 **최초 포지션의 root source가 될 수 없다.**

## 5. causal LTF OB refinement

HTF root OB를 찾았다고 바로 M1으로 내려가지 않는다. 최소 하나의 causal child OB가 필요하다.

refinement는 H1/M30/M15/M5를 내려가며 찾되 다음을 모두 만족해야 한다.

1. 부모 OB와 같은 방향이다.
2. 부모 OB 안에 있거나, 부모 스윙의 바로 인접한 하위 구조다.
3. 부모와 같은 가격 사건 및 같은 displacement를 설명한다.
4. 형성 시각이 부모 파동의 원인 구간과 일치한다.
5. 하위 OB의 displacement가 실제 하위 구조 전달을 만들었다.
6. 부모와 자식의 연결을 차트에 함께 표시할 수 있다.

가격만 겹치거나 나중에 우연히 생긴 하위 OB는 refinement가 아니다.

유효한 refinement가 확인되면 마지막 causal child OB는 최초 포지션의 source/context와 무효화 맥락을 정밀화한다. 최초 포지션의 실제 entry와 기본 SL geometry는 제7~8장의 CHoCH displacement FVG 규칙이 담당한다.

하위 OB가 여러 개로 갈라지고 어느 것이 원인인지 비교할 수 없으면 가장 좁은 것을 임의로 선택하지 않는다. 더 높은 child OB를 유지하거나 비매매한다.

## 6. M1 trigger 허용 조건

다음 항목이 모두 사전에 완료되기 전에는 M1 trigger를 찾지 않는다.

- 목적 유동성 동결
- map 방향과 scenario scope 동결
- HTF root OB 동결
- causal LTF refinement 경로 동결
- source/refined OB 무효화 가격 동결
- 가격이 refined OB에 실제 접촉

접촉 뒤의 기본 trigger chain은 다음과 같다.

```text
refined OB 접촉
-> 그 맥락 안에 사전 형성된 유동성 관통
-> 가격 회복
-> 진행 중 M1 추세의 의미 있는 live swing을 몸통 종가로 돌파
-> 같은 sweep-to-CHoCH causal leg의 fresh same-direction FVG 확인
-> valid FVG 중 가장 넓은 FVG 선택
-> 선택된 FVG의 이후 첫 retest
```

### sweep 대상 유동성의 성숙도

- sweep 대상 고저점은 **최종 sweep excursion이 시작되기 전에 이미 존재**해야 한다.
- 그 고저점에서 최소 한 번의 완결된 반응이 나와 live swing 또는 실제 stop pool로 확인돼야 한다.
- 현재 reaction leg가 방금 만든 고저점을 같은 leg 안에서 즉시 `BSL/SSL sweep 완료`로 선언하지 않는다.
- reaction 중 생긴 고저점은 가격이 충분히 이탈해 구조가 확정된 뒤, 별도의 후속 접근이 그것을 관통하고 회복할 때만 sweep 근거가 될 수 있다.
- 하나의 진행 중 wick이 고점을 만들고 다시 밀렸다는 이유만으로 `final sweep`이라 부르지 않는다.

### 의미 있는 CHoCH

- wick 돌파가 아니라 몸통 종가 돌파여야 한다.
- 하락 중 long이라면 실제 correction을 지배하던 반응 고점을 깨야 한다.
- 상승 중 short이라면 실제 correction을 지배하던 반응 저점을 깨야 한다.
- 한두 캔들의 미세 pivot이나 같은 방향의 내부 흔들림은 CHoCH가 아니다.
- M1 CHoCH가 선명해도 HTF root OB와 refinement가 없으면 진입하지 않는다.
- M1 CHoCH가 M5 correction을 지배하던 swing을 깨지 못했다면 HTF delivery 전환으로 승격하지 않는다.
- M5가 명확히 반대 방향으로 전달 중인데 M1에서만 짧은 반등 CHoCH가 발생하면 우선 내부 correction으로 분류한다.

## 7. FVG의 제한된 역할

FVG를 보았다는 이유로 최초 시나리오를 만들지 않는다.

### 최초 포지션 기본형

- HTF-to-LTF OB lineage는 source/context authority다.
- 의미 있는 M1 CHoCH 자체는 protected/live swing의 몸통 종가 돌파로 성립한다.
- 다만 최초 포지션을 실제로 허가하려면 authorized sweep에서 CHoCH까지 이어지는 동일 causal leg 안에 fresh same-direction 3-candle FVG가 최소 하나 있어야 한다.
- CHoCH가 있어도 causal FVG가 없으면 structure event만 기록하고 `NO ENTRY`다.
- valid FVG가 여러 개면 `width = top - bottom`이 가장 큰 FVG를 선택한다.
- symbol tick 기준으로 최대 폭이 정확히 같은 FVG가 둘 이상이면 임의 선택하지 않고 `NO TRADE`다.
- selected FVG와 meaningful CHoCH가 모두 확정된 이후 가격이 그 FVG에 처음 닿는 것을 first retest로 사용한다.
- first retest의 가격 교차는 `bar.high >= FVG.bottom AND bar.low <= FVG.top`으로 판정하며, authorization 이전에 이미 지나간 touch를 사후 retest로 복원하지 않는다.
- CHoCH FVG가 선명하더라도 누락된 root OB 또는 refinement를 대신할 수 없다.

3-candle FVG는 다음처럼 정의한다.

```text
Bullish:
Candle3.low > Candle1.high
bottom = Candle1.high
top = Candle3.low

Bearish:
Candle3.high < Candle1.low
bottom = Candle3.high
top = Candle1.low
```

### 별도 연구형

다음은 기본 스승님식 최초 진입에 섞지 않는다.

- causal execution OB만을 최초 entry zone으로 쓰는 변형
- HTF FVG를 source로 쓰는 변형
- 동결된 HTF owner·objective·OB lineage 없이 delivery FVG만 추격하는 변형
- FVG inversion 진입

### 미체결 원주문의 Delivery FVG 대체 진입

> **현재 V1 상태: RE-AUDIT REQUIRED / 주문 권한 비활성.** 아래 내용은 기존 계약을 역사적으로 보존한다. 최초 `INITIAL_CHOCH_FVG` baseline과의 연결 조건 및 SL 계약은 별도 감사 전까지 새 V1 주문에 사용하지 않는다.

기다리던 refined OB 주문이 체결되지 않고 가격이 목적지 방향으로 출발했다면 시장가로 추격하지 않는다. 다음 조건을 모두 만족할 때만 `DELIVERY_FVG_REPLACEMENT`를 허용한다.

1. 원래 H1/M30 owner, 방향, scenario scope, objective가 변하지 않았다.
2. 원래 HTF root OB와 causal child OB lineage가 주문 전에 이미 동결돼 있었다.
3. 원래 OB 주문은 아직 체결되지 않았고, 해당 source가 무효화되지 않았다.
4. M5 또는 M1의 목적지 방향 displacement가 protected swing을 몸통으로 돌파하거나 기존 delivery를 명확히 재확인했다.
5. 그 displacement가 fresh FVG를 만들었고, 해당 displacement의 causal OB와 protected swing을 식별할 수 있다.
6. 진입은 그 FVG의 **첫 되돌림**만 사용한다. 이미 여러 번 접촉했거나 몸통으로 무효화된 FVG는 사용하지 않는다.
7. entry와 objective 사이에 더 가까운 미소진 liquidity가 새로 생기지 않았다.

- 기존의 깊은 OB pending은 delivery가 확인되는 즉시 취소한다. 원주문과 대체 주문을 동시에 남기지 않는다.
- 기본 entry는 fresh FVG의 방향별 proximal boundary다. FVG 안의 causal M1 OB가 같은 displacement를 명확히 설명하면 그 OB의 첫 retest로 정밀화할 수 있다.
- SL은 fresh FVG distal 하나가 아니라 displacement causal OB distal, trigger protected swing, 원래 final child 무효화 중 정상 되돌림을 모두 벗어나는 가장 보수적인 경계 바깥에 둔다.
- 주문 생성 시점의 `max(actual spread, broker stops level, 1 tick)` buffer를 그 구조 경계 바깥에 더한다. FVG distal은 entry zone의 상태와 through-delivery를 판정하는 정보이지 hard SL의 단독 권한이 아니다.
- 체결 시점 spread가 동결 buffer보다 커졌다면 SL을 사후로 넓히지 않고 주문을 취소한다.
- TP는 처음 동결한 동일 objective다. FVG 진입으로 바뀌었다는 이유로 목표를 더 멀리 연장하지 않는다.
- 첫 retest 전에 objective가 소진되거나 owner가 바뀌거나 FVG/causal OB/protected swing이 무효화되면 주문을 취소한다.
- 첫 되돌림 없이 목적지까지 직행하면 `MISSED - NO DELIVERY RETEST`로 기록하고 보내준다.

### 기존 포지션의 Delivery FVG 추가진입

기존 최초 포지션이 이미 동결된 TP 방향으로 전달 중이고 진입가를 넘어 유리하게 진행된 뒤, 새 구조 전달과 fresh FVG가 만들어진 경우의 첫 retest만 `DELIVERY_FVG_ADDON` 후보가 될 수 있다. 추가진입도 새 displacement·fresh FVG·causal OB·protected swing이 전부 확인돼야 하며, 동일 physical FVG/retest는 하나의 execution chain만 만든다. 각 addon은 독립 `1R`이고 최초 포지션과 같은 objective family를 사용한다.

기본 HTF-to-LTF OB 진입과 Delivery FVG replacement의 재현성이 독립적으로 확인되기 전까지 `DELIVERY_FVG_ADDON` 주문 권한은 비활성으로 둔다. 비활성 상태에서는 후보를 탐색하거나 API 심사를 요청하거나 위험 슬롯을 점유하지 않는다.

## 8. Entry, SL, TP

### Entry

- 최초 진입 execution model은 `INITIAL_CHOCH_FVG`다.
- LONG은 selected bullish FVG의 상단(`top`)에 Buy Limit을 둔다.
- SHORT은 selected bearish FVG의 하단(`bottom`)에 Sell Limit을 둔다.
- selected FVG와 meaningful CHoCH가 모두 확정된 이후 첫 retest만 사용하며, 이미 지나간 접촉에 사후 진입하지 않는다.
- CHoCH가 있어도 같은 sweep-to-CHoCH causal leg에 valid fresh FVG가 없으면 최초 포지션은 만들지 않는다.
- selected FVG first retest 없이 가격이 출발하면 시장가로 추격하지 않는다.
- `DELIVERY_FVG_REPLACEMENT`는 제7장에 기존 기록을 보존하지만 현재 V1에서는 재감사 전 주문 권한이 없다.

### 체결 전 pending order 생명주기

주문 상태는 다음 순서로만 진행한다.

```text
PREPARED: objective / map / root / child 동결
-> ARMED: refined OB 실제 접촉
-> CHOCH_CONFIRMED: mature sweep + meaningful M1 CHoCH
-> TRIGGERED: causal FVG 확인 + widest valid FVG 확정
-> PENDING: selected FVG first retest 주문 대기
-> FILLED 또는 CANCELED
```

- `PENDING`은 무기한 유효하지 않다. 새로운 H1 또는 M15 확정봉이 생길 때마다 owner, scope, objective, source freshness, trigger protected swing을 다시 승인한다.
- 주문 생성 뒤 한 번이라도 H1/M15 map이 달라졌는데 재승인 기록이 없으면 체결하지 않는다.
- objective 선도달, root/child 몸통 무효화, trigger protected swing 파괴, POI 완전 소비, opposing owner 확정 중 하나가 발생하면 즉시 `CANCELED`다.
- trigger 뒤 가격이 entry zone을 떠나 새로운 HTF leg를 만든 경우, 과거 M1 trigger를 다음 세션까지 재사용하지 않는다. 새로운 진입에는 새로운 sweep부터 CHoCH displacement FVG까지 전 체인이 필요하다.
- entry와 SL을 같은 접근 displacement가 함께 관통하면 정상 retest가 아니라 `through-delivery`로 분류한다. historical tick이 별도의 진입-반응 순서를 증명하지 못하면 유효한 스승님식 체결로 승인하지 않는다.
- 주문 체결 시점의 시나리오를 주문 생성 시점의 설명만으로 정당화하지 않는다. **마지막 재승인 시각**을 원장에 반드시 기록한다.

### SL

`INITIAL_CHOCH_FVG` 최초 진입의 전략 SL은 selected FVG geometry로 정한다.

```text
width = FVG.top - FVG.bottom
buffer = width * 0.20
```

LONG:

```text
SL = FVG.bottom - buffer
```

SHORT:

```text
SL = FVG.top + buffer
```

- 전략 SL은 symbol tick size에 맞게 가격 단위만 normalize한다.
- broker spread / stops level / Bid-Ask 체결 제약을 전략 SL과 정확히 어떻게 연결할지는 execution infrastructure 단계에서 별도로 확정한다. 이 미결정을 이유로 전략 SL 공식을 임의 변경하지 않는다.
- buffer 때문에 risk가 커지면 lot을 줄인다.

`DELIVERY_FVG_REPLACEMENT`와 `DELIVERY_FVG_ADDON`의 SL 계약은 현재 최초 진입 규칙과 별개이며, 재감사/승격 전까지 새 V1 주문에 사용하지 않는다.

### TP

- PLAN 단계에서 Entry/SL geometry를 알기 전에 동일 owner와 scenario scope의 ordered objective family를 동결한다.
- Entry와 hard SL이 확정된 뒤 pre-frozen family를 방향상 가까운 순서대로 검사한다.
- 아직 미소진이고 scope-compatible하며 planned R `>= 1`인 최초 candidate를 final TP로 선택한다.
- planned R `< 1`인 valid liquidity는 삭제하지 않고 `INTERMEDIATE_DELIVERY`로 기록하며 final TP 자격만 제외한다.
- planned R은 objective-candidate eligibility에만 사용한다. 더 큰 R을 만들기 위해 TP를 새로 찾거나 candidate 순서를 바꾸거나 SL을 줄이지 않는다.
- 같은 tier에서는 R이 더 큰 candidate가 아니라 가장 가까운 R-eligible candidate를 선택한다.
- EXTERNAL_CONTINUATION의 current tier는 현재 owner 방향의 미소진 H1/M30 external liquidity다. 그 사이의 internal liquidity는 `INTERMEDIATE_DELIVERY`로 기록한다.
- INTERNAL_ROTATION의 current tier는 active dealing range 안의 mature M15+ internal liquidity다. 가장 가까운 internal liquidity가 `<1R`이면 intermediate로 남기고 다음 internal candidate를 평가한다. External liquidity로 scope를 확장하지 않는다.
- EXTERNAL_REVERSAL은 H1/M30 protected swing body break와 새 owner 확인 뒤 새 방향 external objective family를 사용한다. M1 반전만으로 이 계약을 사용할 수 없다.
- External scenario에서 current tier에 R-eligible candidate가 없을 때만 PLAN 단계에서 pre-frozen된 historical H1 fallback tier를 평가한다.
- Final TP가 선택된 뒤에는 같은 scenario에서 다음 objective로 rollover하지 않는다.
- Final TP가 fill 전에 delivered되면 scenario와 pending order를 취소한다.
- V1 strategy TP는 selected liquidity의 actual structural price를 사용한다. Swing liquidity는 actual wick price를 사용한다.
- 유동성보다 더 멀리 임의 buffer를 두거나 RR을 높이기 위해 TP를 이동하지 않는다.
- V1 baseline에서 spread/1-tick inward TP front-run을 사용하지 않는다. 필요하면 향후 별도 immutable execution-optimization variant로 비교한다.
- LONG TP는 Bid-side, SHORT TP는 Ask-side broker execution semantics를 따른다.

### 체결 후

- 최초 SL 또는 TP가 결과를 판정한다.
- 공포, 수익 보호 욕구, 중간 M1 반대 신호로 임의 청산하지 않는다.
- 시간 만료, 본절 이동, 부분 익절은 별도 승인 전까지 사용하지 않는다.

## 9. 즉시 비매매 조건

다음 중 하나라도 해당하면 거래하지 않는다.

1. 목적 유동성이 명확하지 않다.
2. Final TP로 선택된 objective가 pending fill 전에 이미 소진됐다.
3. H1/M30에서 외부와 내부 구조를 구분하지 못했다.
4. 의미 있는 swing 근처의 HTF root OB가 없다.
5. source가 HTF FVG뿐이다.
6. causal child OB를 최소 하나 찾지 못했다.
7. parent-child가 가격만 겹치고 같은 displacement를 설명하지 못한다.
8. 가격이 refined OB에 아직 도달하지 않았고, 유효한 `DELIVERY_FVG_REPLACEMENT` 계약도 완성되지 않았다.
9. OB 접촉 전에 M1 trigger부터 찾았다.
10. sweep 대상 유동성이 사전에 존재하지 않았다.
11. CHoCH가 의미 있는 live swing이 아니라 micro pivot만 돌파했다.
11a. 의미 있는 CHoCH는 있지만 같은 sweep-to-CHoCH causal leg에 valid fresh FVG가 없다.
12. selected FVG의 first retest가 이미 지나갔다.
13. selected FVG와 FVG 폭 20% buffer 기반 전략 SL을 설명할 수 없다.
14. TP를 정확한 유동성 가격으로 설명할 수 없다.
15. 필수 구조를 차트에 표시할 수 없다.
16. continuation long이 active range의 premium에 있거나 continuation short이 discount에 있다.
17. INTERNAL_ROTATION에서 selected TP보다 가까운 mature internal liquidity를 candidate family에서 누락했거나, planned R `>=1`인 더 가까운 candidate를 건너뛰었거나, planned R `<1`인 가까운 liquidity를 `INTERMEDIATE_DELIVERY`로 기록하지 않았다. EXTERNAL_CONTINUATION에서는 entry와 selected external TP 사이의 internal liquidity를 `INTERMEDIATE_DELIVERY`로 기록하지 않으면 비매매다.
18. sweep 대상 고저점이 현재 reaction leg에서 방금 생겼고 아직 완결된 반응으로 성숙하지 않았다.
19. pending order 뒤 새 H1/M15 확정봉이 생겼지만 마지막 재승인 기록이 없다.
20. M5는 반대 방향 correction을 유지하는데 M1 micro CHoCH만으로 전환을 선언했다.
21. entry 접근 displacement가 selected FVG entry와 전략 SL을 동시에 관통한다.
22. broker spread/stops-level 때문에 전략 SL을 그대로 제출할 수 없는 상태인데, execution-infrastructure 정책이 확정되지 않은 채 SL을 임의 변경하거나 주문을 강행한다.

`FVG가 보임`, `M1이 강하게 움직임`, `곧 반전할 것 같음`, `최근 고저점 sweep`은 누락된 조건을 보충하지 못한다.

## 10. 블라인드 재생 규율

1. H1/M30에서 map, scenario scope, ordered objective family, root OB를 먼저 동결한다. Final TP 하나는 Entry와 hard SL이 확정된 뒤 pre-frozen family에서 선택한다.
2. M30/M15/M5에서 refinement 경로를 차트에 표시한다.
3. 가격이 refined OB에 접근하기 전에는 M1을 보지 않는다.
4. root OB 접근 뒤에는 M15/M5로 refinement와 correction을 확인하고, refined OB 실제 접촉 뒤에만 M1을 한 봉씩 확인한다.
5. **사건 기반 판단 게이트:** map을 만들 때 `root OB 접근 경계 / refined OB 접근 경계 / pre-frozen objective candidate levels / source 무효화 / protected swing 몸통 돌파`를 먼저 동결한다. Final TP가 선택되기 전에는 objective-family candidate의 소진 여부를 사건으로 추적하고, Final TP가 선택된 뒤에는 selected objective의 delivery가 cancellation authority를 가진다. 사건에서 멈춘 뒤 `주문 동결 / 대기 / 비매매`를 기록하기 전에는 더 진행하지 않는다.
6. 지나간 진입을 사후 주문으로 복원하지 않는다.
7. 주문 전에 entry, SL, TP와 모든 원인 ID를 기록한다.
8. 거래 결과를 본 뒤 OB, liquidity, CHoCH, SL, TP를 다시 그리지 않는다.
9. 재생 제어 오류로 미래 데이터가 보이면 해당 세션을 즉시 폐기한다.
10. 코드, 지표, 기존 후보 원장, 이후 가격은 매매 판단에 사용하지 않는다.
11. `[RE-AUDIT REQUIRED / 현재 V1 비활성]` 기존 Delivery FVG replacement 절차에서는 원주문 미체결 뒤 시장가로 따라가지 않고 후속 fresh FVG의 첫 되돌림만 검토했다. 이 절차는 별도 재감사 전까지 새 V1 주문에 사용하지 않는다.
12. `DELIVERY_FVG_REPLACEMENT`를 준비할 때도 해당 FVG가 나타난 시점까지의 데이터만 보고 owner·objective 유지, 구조 전달, causal OB, protected swing을 다시 동결한다.
13. 재생을 빨리 넘겨 후보를 뒤늦게 발견한 것은 시장의 `미체결`이나 정상적인 `놓친 거래`가 아니라 **분석자 재생 절차 실패**다. 해당 거래일은 블라인드 성과 통계에서 제외하고 새 미사용 기간으로 다시 검증한다.
14. 넓은 시간 구간의 OHLC를 한꺼번에 출력하거나 이후 봉을 먼저 열어 본 뒤 과거 시점의 판단을 복원하는 행위를 금지한다. 단, 사전에 동결한 사건 가격 중 하나에 도달할 때까지만 재생기가 자동 탐색하는 것은 허용한다. 이때 사건 이전의 이후 차트는 판단자에게 노출하지 않는다.
15. `PREPARED` 상태에서 가격이 root OB와 충분히 떨어져 있고 동결된 무효화 사건도 없다면 H1 봉마다 같은 분석을 반복하지 않는다. root OB 접근 시 M15/M5로 전환하고, refined OB 실제 접촉 뒤에만 M1을 한 봉씩 진행한다.
16. 빠른 재생 중 정지 조건은 사전에 가격으로 선언한 사건에 한정한다. 재생 결과를 본 뒤 더 유리한 POI나 정지 가격을 소급해서 추가할 수 없다.

## 11. 주문 전 필수 증거

아래 항목을 차트와 원장에 모두 남기기 전에는 주문하지 않는다.

- map TF와 scenario scope
- active dealing range, EQ, 현재 premium/discount 위치
- PLAN에서 pre-frozen된 ordered objective family의 candidate ID / 가격 / 종류 / tier / 순서
- 각 objective candidate의 consumed 여부, planned R, eligibility, role
- planned R `<1`이라 final TP에서 제외된 더 가까운 liquidity의 `INTERMEDIATE_DELIVERY` 기록
- selected final objective의 ID / 정확한 가격 / planned R / 선택 시각
- 같은 tier의 더 가까운 R-eligible liquidity를 건너뛰지 않았다는 증거
- HTF root OB의 시간, 상단, 하단
- refinement 경로와 각 child OB의 시간, 상단, 하단
- parent-child가 같은 displacement인 이유
- refined OB 접촉 시각
- sweep 대상 유동성, 그 유동성이 성숙한 시각, final sweep extreme
- M1 CHoCH가 돌파한 live swing
- 같은 sweep-to-CHoCH displacement 안의 valid FVG와 각 width
- selected widest FVG의 형성 시각, 상단, 하단, width, first retest 여부
- entry, FVG distal, 20% width buffer, actual spread, broker stops level, hard SL
- TP와 해당 유동성의 출처 및 scenario scope와의 일치
- pending order의 마지막 H1/M15 재승인 시각
- execution model이 `INITIAL_CHOCH_FVG`, `DELIVERY_FVG_REPLACEMENT`, `DELIVERY_FVG_ADDON` 중 무엇인지
- `DELIVERY_FVG_REPLACEMENT` 관련 기존 증거 계약은 역사적으로 보존하되 현재 V1에서는 재감사 전 비활성

차트에서 이 연결을 사용자가 한눈에 확인할 수 없다면 내가 원인을 제대로 선택하지 못한 것으로 간주한다.

## 12. 성과 분류

### 스승님식 유효 거래

모든 필수 증거가 주문 전에 동결된 거래만 해당한다. 이런 거래의 SL은 결과가 아니라 `시장 불확실성`으로 분류할 수 있다.

### 프로토콜 위반 거래

다음은 PnL과 무관하게 스승님식 성과에서 제외한다.

- root OB 누락
- causal refinement 누락
- 내부 유동성을 외부 유동성으로 승격
- HTF FVG를 standalone source로 사용
- M1 trigger-first 진입
- micro CHoCH 진입
- causal FVG가 없는 CHoCH만으로 만든 최초 진입
- widest-FVG 규칙을 무시하고 임의 FVG를 선택한 최초 진입
- FVG 20% external-buffer 전략 SL을 임의 변경한 최초 진입
- stale pending order 체결
- 성숙하지 않은 reaction 고저점을 sweep으로 사용
- premium continuation long 또는 discount continuation short
- INTERNAL_ROTATION 목표를 외부 유동성까지 확대
- actual Bid/Ask spread 안쪽 SL
- 사후 선택한 entry/SL/TP
- 필수 차트 증거 누락
- 동결된 HTF 시나리오 없이 fresh FVG만 보고 만든 `DELIVERY_FVG_REPLACEMENT`
- 기존 OB pending과 Delivery FVG 대체 주문을 동시에 유지한 거래
- 두 번째 이후 FVG 접촉을 첫 retest로 소급한 거래

TP에 도달한 프로토콜 위반 거래도 성공 사례가 아니다. SL에 도달한 유효 거래도 규칙을 사후 변경할 근거가 아니다.

## 13. 최근 실패의 재발 방지

다음 행동은 이미 성과 급락을 만든 실패로 확인됐으며 반복하지 않는다.

- 3359 내부 저점을 H1 외부 SSL로 잘못 승격하고 M1 FVG long을 만든 행동
- 명확한 HTF OB 없이 M1 CHoCH로 시나리오의 빈칸을 채운 행동
- M15 FVG를 HTF root source처럼 사용한 행동
- 스승님 영상에 없는 일반적인 `range breakdown/acceptance` 해석으로 거래를 허가한 행동
- POI 접근을 빠른 재생으로 지나친 뒤 중간 가격에서 새 근거를 만든 행동
- parent OB와 child OB를 차트에 표시하지 못한 상태에서 주문을 계속한 행동
- 손실 뒤 규칙을 즉석에서 바꾸고 같은 주의 결과에 다시 적용한 행동
- 2025-08-19 long처럼 M1 trigger 후 13시간 동안 map을 재승인하지 않고 오래된 pending order를 bearish displacement에 체결한 행동
- 2025-08-21 첫 long처럼 H1 dealing range premium에서 이미 대부분 전달된 bullish leg의 continuation을 추격한 행동
- 2025-08-21 short처럼 reaction 중 방금 생긴 3347.48 고점을 final BSL sweep으로 조기 확정하고 실제 3347.99 sweep 전에 진입한 행동
- short SL을 chart high에만 맞추고 Ask spread를 누락한 행동
- INTERNAL_ROTATION인데 더 가까운 3325.03 SSL을 건너뛰고 3313.89 external SSL까지 TP를 확대한 행동

## 14. 주문 직전 최종 선언

주문 전 다음 문장을 빈칸 없이 답해야 한다.

```text
PLAN에서 동결한 objective family는 ________ 이며 candidate 순서는 ________ 이다.
H1/M30 map과 scenario scope는 ________ 이다.
active dealing range는 ________ ~ ________, EQ는 ________, 현재 위치는 premium / discount 중 ________ 이다.
Final TP보다 가까운 liquidity candidate는 ________ 이며, 각각의 planned R / role은 ________ 이다.
Final TP로 ________ 을 선택했으며 planned R은 ________ R이고, 이것이 같은 tier에서 가장 가까운 R-eligible candidate인 이유는 ________ 이다.
root OB는 ________ TF의 ________ 가격 영역이다.
그 OB의 causal child는 ________ TF의 ________ 가격 영역이다.
두 OB가 같은 원인인 이유는 ________ 이다.
가격은 ________ 시각에 refined OB를 접촉했다.
유동성 ________ 은 ________ 시각에 성숙했고, ________ 시각에 final sweep됐다.
M1은 ________ live swing을 몸통으로 돌파했다.
같은 sweep-to-CHoCH displacement의 valid FVG는 ________ 이며, widest selected FVG는 ________ 이다.
selected FVG의 first retest는 ________ 이다.
Entry는 ________, FVG width는 ________, 20% SL buffer는 ________, hard SL은 ________, TP는 ________ 이다.
actual spread는 ________, broker stops level은 ________ 이다.
SL이 FVG 규칙에 맞는 이유는 ________ 이다.
TP가 scenario scope와 일치하는 structural liquidity이고 objective-family selection rule을 만족하는 이유는 ________ 이다.
pending order의 마지막 H1/M15 재승인 시각은 ________ 이다.
execution model은 INITIAL_CHOCH_FVG / DELIVERY_FVG_REPLACEMENT / DELIVERY_FVG_ADDON 중 ________ 이다.
DELIVERY_FVG_REPLACEMENT는 현재 V1에서 비활성이며, 재감사 전에는 N/A로 기록한다.
```

한 항목이라도 답할 수 없으면 주문하지 않는다.

## 15. 한 문장 원칙

> M1 trigger로 거래의 원인을 찾지 않는다. 먼저 HTF swing OB와 causal LTF OB refinement로 시나리오를 완성하고, M1은 그 시나리오가 실제로 반응했는지만 확인한다.

## 16. 2025-08-18~22 실패 회귀 검사

> 이 절의 과거 entry/SL 숫자 또는 sweep-based SL 문구는 당시 프로토콜의 legacy 기록이다. 현재 최초 진입의 entry/SL pass/fail은 제7~8장의 `INITIAL_CHOCH_FVG` 규칙으로 다시 계산한다. liquidity maturity, map, scenario scope 관련 회귀 목적은 그대로 유지한다.

다음 주간 매매를 시작하기 전에 아래 세 사례가 현재 규칙으로 반드시 거절되거나 올바른 시점까지 대기되는지 확인한다.

### 회귀 A: stale pending long

- trigger 뒤 13시간이 지나고 H1/M15 map이 달라졌는데도 주문이 남아 있으면 실패다.
- bearish displacement가 entry와 SL을 같은 접근에서 관통하면 유효 retest로 처리해서는 안 된다.
- 기대 결과: `CANCELED - MAP_NOT_REAUTHORIZED` 또는 `CANCELED - SOURCE_EPISODE_ENDED`.

### 회귀 B: premium continuation long

- H1 range `3311.35~3351.95`, EQ `3331.65`에서 `3341.62` long을 continuation으로 승인하면 실패다.
- M5 correction이 하락인데 M1 bullish micro CHoCH만으로 H1 continuation을 선언하면 실패다.
- 기대 결과: `NO_TRADE - WRONG_PD_HALF` 및 `NO_TRADE - M1_INTERNAL_ONLY`.

### 회귀 C: premature short before final sweep

- reaction 중 새로 생긴 `3347.48`을 즉시 final BSL sweep으로 인정하면 실패다.
- `3347.99` 후속 sweep과 그 뒤 body CHoCH가 나오기 전에는 short를 허가하지 않는다.
- short SL은 final sweep extreme과 Ask spread 바깥이어야 한다.
- scenario가 INTERNAL_ROTATION이면 첫 TP는 `3325.03` 계열이며 `3313.89`로 확대하지 않는다.
- 기대 결과: 최초 short는 `WAIT - LIQUIDITY_NOT_MATURE`; final sweep 뒤 새 chain만 별도 승인 가능.

이 세 회귀 중 하나라도 통과하지 못하면 새로운 주간 블라인드 매매를 시작하지 않는다.

## 17. 2025-08-25~29 목적 유동성 회귀 검사

> 이 절의 과거 execution OB entry/SL 숫자와 당시 단일 objective 선택 결과는 legacy 기록이다. 현재 최초 진입의 Entry/SL은 제7~8장의 `INITIAL_CHOCH_FVG` 규칙으로 재산출하고, final TP도 현재의 pre-frozen objective family + planned R `>=1` eligibility + nearest-eligible selection 규칙으로 다시 판정한다. 아래 사례의 핵심 회귀 목적은 `EXTERNAL_CONTINUATION`과 `INTERNAL_ROTATION`의 scope를 혼동하지 않는 것이며, 과거에 적힌 특정 TP 숫자가 새 geometry에서도 자동으로 current authority가 되는 것은 아니다.

scenario scope와 TP 종류를 혼동하지 않기 위해 다음 세 사례를 고정 회귀로 사용한다.

### 회귀 D: external continuation을 내부 TP로 축소하지 않기

- 2025-08-27 long은 H1/M30 외부 상승 구조와 같은 방향의 `EXTERNAL_CONTINUATION`이다.
- `3384.41` 내부 BSL은 `INTERMEDIATE_DELIVERY`이며 최종 TP가 아니다.
- 당시 동결할 external objective는 `3394.14` BSL 계열이다.
- 기대 결과: entry `3376.72`, SL `3372.70`, external TP `3394.14`; 내부 BSL 도달만으로 청산하지 않는다.

### 회귀 E: external continuation의 중간 유동성 선도달

- 2025-08-29 낮 long은 H1/M30 상승 delivery가 유지된 `EXTERNAL_CONTINUATION` 후보다.
- `3408.72`, `3411.16` 계열 내부 BSL은 중간 전달 지점이며, 사전에 동결한 external objective `3422.95`를 대체하지 않는다.
- owner·root/child lineage·pending 재승인이 유지되는 동안 내부 BSL 소진만으로 주문을 취소하면 실패다.
- 기대 결과: 기존 execution OB 주문이 Ask 기준 `3407.29`에 체결되면 구조 SL 바깥과 external TP `3422.95`로 판정한다.

### 회귀 F: internal rotation을 외부 TP로 확대하지 않기

- 2025-08-29 저녁 short은 H1/M30 외부 상승 구조 안의 `INTERNAL_ROTATION`이다.
- 첫 internal SSL `3442.45`가 올바른 최종 objective이며 external SSL `3404.22`로 확대하지 않는다.
- 올바른 M1 execution OB retest 전에 `3442.45`가 소진되면 주문은 취소다.
- 기대 결과: `CANCELED - INTERNAL_OBJECTIVE_REACHED_BEFORE_ENTRY`; 외부 TP를 적용해 19:34에 체결시키고 SL로 만드는 것은 scope 위반이다.

회귀 D~F는 모든 거래의 TP를 외부 또는 내부로 일괄 통일하지 않고, 주문 전에 동결한 scenario scope가 TP 종류를 결정하는지 확인한다.

## 18. Ground Truth V2 및 자동 판단 실행 계약

이 절은 앞 절의 전략 의미를 바꾸지 않고, 정답지·Gemini replay·live shadow가 같은 사건과 위험 상태를 다루도록 실행 경계를 고정한다.

### 18.1 후보와 objective family

- 거래 후보는 raw M1 확정봉에서 집계한 H1/M30/M15/M5 사건 원장으로만 만든다. oracle, move index, 결과가 보이는 미래 구간은 후보 발견에 사용할 수 없다.
- root 후보는 모든 `마지막 반대색 원인 캔들 -> displacement -> 몸통 구조 전달` episode를 형성 시점부터 소비·무효화 시점까지 영구 ID로 보존한다.
- liquidity 후보는 H1/M30의 external swing·반복 방어·range edge·reaction trap과 M15 이상 internal liquidity를 형성 시점부터 소진 시점까지 추적한다. 단순 2-bar pivot은 모델이 검토할 원시 후보일 뿐 자동으로 목적 유동성이 되지 않는다.
- 후보 수나 prompt 크기 때문에 family를 삭제하지 않는다. 결정론적 paging을 사용하고, page별 입력 family ID와 응답 family ID의 집합이 정확히 일치해야 한다.
- PLAN은 같은 owner·scope·lineage의 순서가 고정된 objective family를 동결한다. 모델은 family 구성원의 가격이나 순서를 다시 쓰지 않는다.
- Final TP는 Entry와 normalized strategy SL이 확정된 뒤 pre-frozen family에서 planned R `>=1`인 가장 가까운 scope-compatible candidate를 선택한다. Entry/SL 확인 뒤 새 candidate를 추가하거나 더 큰 R을 위해 candidate 순서를 바꾸지 않는다.
- objective family의 장기 이력 구간에는 현재가에서 방향상 가장 가까운 미소진 H1 liquidity를 최대 `2개`만 포함한다. 장기 M30 이하 후보는 포함하지 않으며, 현재 구조 objective가 주문 기하상 적격이면 장기 후보는 비활성 상태를 유지한다.
- objective family의 historical fallback tier에는 current-structure family 바깥 방향의 causally-known 미소진 H1 external liquidity를 방향상 가장 가까운 순서로 최대 `2개`만 포함한다. 장기 M30 이하 후보는 포함하지 않는다. 이 tier는 EXTERNAL_CONTINUATION / EXTERNAL_REVERSAL에서만 허용하며, current-structure tier에 planned R `>=1`인 valid candidate가 있으면 비활성 상태를 유지한다.
- 정답 거래의 최초 판단 가능 시각 packet에 root·child·objective family 역할 ID가 하나라도 없으면 `MODEL_MISS`가 아니라 `ENGINE_CANDIDATE_MISS`다.

### 18.2 다중 scenario lane과 위험 슬롯

- 전역 상태는 `ownerEpoch`, 독립 `scenarioLanes`, `orders`, `positions`, `executionChains`로 나눈다.
- PREPARED·TRIGGER_WATCH lane은 위험 슬롯을 사용하지 않는다. `PENDING + FILLED`의 합계만 최대 `3`이며 각 주문은 독립 `1R`이다.
- 슬롯은 주문 생성 시각 순으로 배정한다. 같은 시각이면 root TF `H1 > M30 > M15`, source 인식 시각, signal ID 순으로 정한다.
- 열린 pending 또는 position과 반대 방향의 새 주문은 금지한다. 반대 watch lane은 유지할 수 있지만 차단되어 지나간 첫 retest를 나중에 복원하지 않는다.
- 같은 physical FVG·첫 retest는 하나의 execution ID만 가진다. 서로 다른 lineage가 동일 execution을 주장하고 하나로 해소되지 않으면 `UNRESOLVED_LINEAGE`다.
- SL 이후에도 source·owner·objective family가 유효하면 family 자체를 retire하지 않는다. 새 sweep부터 CHoCH displacement FVG까지 완전한 새 execution chain만 재진입할 수 있다.
- TP 또는 최종 objective 소진 뒤에는 그 family를 종료한다.

### 18.3 API 지연과 체결 순서

- API 요청 중 새로 확정된 M1 봉과 broker tick은 순서대로 버퍼링한다.
- 모델 응답과 로컬 승인 전에 첫 retest가 지나가면 `MISSED_API_LATENCY`, broker 주문 승인 전에 지나가면 `MISSED_ORDER_LATENCY`다. 사후 체결은 금지한다.
- historical M1만 있어 응답 분의 touch 순서를 판별할 수 없으면 `LATENCY_INTRABAR_AMBIGUOUS`로 제외한다.
- 최초 접근 봉이 Entry와 SL을 함께 관통하면 `THROUGH_DELIVERY`다. 체결 후 후속 봉에서 SL·TP가 동시에 닿으면 보수적으로 SL 우선이다.
- FVG 주문 생성 때 동결한 buffer보다 fill 시점 actual spread가 커지면 주문을 취소하고 SL을 사후 수정하지 않는다.

### 18.4 replay·live 일치와 운영 승인

- replay와 live는 같은 `advance_closed_m1_bar()` 순서로 후보 갱신, 모든 lane 진행, position 진행, PLAN scheduling, slot arbitration을 수행한다.
- live archive의 M1 gap은 MT5에서 backfill한다. 복구할 수 없는 gap이 있으면 API 판단과 주문을 모두 중지한다.
- 모든 주문은 idempotent client ID를 사용하며 재시작 때 in-flight request, lane, pending, position, objective family, latency 상태를 content hash로 복원한다.
- MT5 pending·position과 로컬 원장을 reconciliation하지 못하면 새 주문을 만들지 않는다.
- live shadow가 replay와 동일 사건 원장을 만든 뒤에만 DEMO 최소 lot 주문을 허용한다. 실계좌 주문은 별도 위험 비율과 운영 승인 전까지 비활성이다.

### 18.5 Ground Truth 완료 조건

- Ground Truth는 chronological 감사, 순서를 섞은 반증 감사, no-trade 구간 감사를 모두 통과해야 한다.
- 각 거래는 최초 판단 가능 시각의 역할 ID, objective family, execution chain, 주문 전 증거, 종료 결과를 append-only 원장에 남긴다.
- 모든 accepted 거래의 역할 ID가 당시 Gemini packet에 존재하는지 100% 검사한다.
- 정답지의 결과가 좋다는 이유로 거래를 채택하지 않고, 결과가 나쁘다는 이유로 룰을 만족한 거래를 삭제하지 않는다.
- render 수·파일 수·후보 수만으로 정답지 완료를 선언하지 않는다. 실제 의미 감사와 주문 생명주기 증거가 모두 있어야 한다.
