# 스승님식 Deterministic EA V1 전략 실행 계약

- 상태: `FROZEN / CURRENT V1 STRATEGY AUTHORITY`
- 제정일: `2026-08-01`
- 최근 개정: `2026-08-16` (`PD Array authority correction: context/reference only`)
- 적용 범위: deterministic EA, MT5 Strategy Tester, current V1 수동/블라인드 리플레이 검증

## 1. 문서의 지위

이 문서는 current deterministic Mentor EA V1의 최상위 전략 authority다.
수동 차트 분석과 블라인드 리플레이도 current V1을 검증할 때 이 계약을 따른다.

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

`DELIVERY_FVG_REPLACEMENT`, `DELIVERY_FVG_ADDON`, OB-only first entry 등
비활성 execution variant의 상세 계약은 Git history와 research 문서에만 보존한다.
Current V1 주문 권한에는 사용하지 않는다.

## 2. 시간봉의 고정 역할

| 역할 | 시간봉 | 권한 |
| --- | --- | --- |
| Long-horizon liquidity index | H4 | 오래된 ACTIVE external-swing liquidity만 압축 보존한다. |
| Active map | H1, M30 | 방향, external/internal structure, dealing range, reversal permission의 authority다. |
| Root/source candidate | H1, M30, M15 | current map과 causal displacement를 설명하는 Root 후보를 만들 수 있다. |
| Refinement / context | M30, M15, M5 | Root의 lower-TF causal child와 correction context를 확인한다. |
| Trigger | M1 | source reaction의 sweep, meaningful CHoCH, execution FVG를 확인한다. |

H4는 `LONG_HORIZON_LIQUIDITY_INDEX` 전용 frame이다.

H4는 다음 권한을 갖지 않는다.

```text
scenario direction
dealing range
reversal permission
Root/source
entry
```

H1/M30이 active trading map authority다.

M15는 active map authority는 아니지만
current H1/M30 causal context 안에서 Root candidate가 될 수 있다.

M1은 시나리오를 만드는 시간봉이 아니라
이미 존재하는 시나리오의 실행 반응을 확인하는 시간봉이다.

## 3. 목적지와 시장 지도

### 3.1 목적 유동성을 먼저 정한다

진입 방향을 생각하기 전에
현재 scenario scope가 설명할 수 있는
ordered objective family를 먼저 정한다.

V1 first-position active scenario scope는 두 개다.

```text
EXTERNAL_CONTINUATION
EXTERNAL_REVERSAL
```

`INTERNAL_ROTATION`은 현재 V1 first-position 주문 권한을 갖지 않는
research / historical classification으로만 유지한다.

PLAN 단계에서는 Entry와 SL geometry를 알기 전에
현재 causally-known 상태인 objective candidate를 freeze한다.

Candidate는 반드시:

```text
causally-known
unconsumed
trade direction ahead
scenario scope compatible
```

이어야 한다.

Objective family는 별도의:

```text
CURRENT_STRUCTURE
HISTORICAL_H1_FALLBACK
```

tier로 나누지 않는다.

또한 historical candidate를 임의로 최대 2개까지만 두는
candidate-count cap을 사용하지 않는다.

PLAN 시점에 현재 인과적으로 알고 있는
scope-compatible candidate 전체를
trade direction으로 가까운 순서대로 하나의 family에 freeze한다.

#### EXTERNAL_CONTINUATION

H1이 mature directional owner이면:

```text
현재 H1/M30 owner와 호환되는
trade-direction external liquidity
```

를 objective family로 사용한다.

Entry와 final external objective 사이의
internal liquidity는 최종 TP가 아니라
`INTERMEDIATE_DELIVERY`로 기록할 수 있다.

H1이 NEUTRAL / TRANSITION이고
M30이 temporary primary directional map이면:

```text
현재 M30 external liquidity
```

만 사용한다.

Old H1 dealing range 또는 old H1 objective를
자동 상속하지 않는다.

#### EXTERNAL_REVERSAL

Old H1 owner가 아직 active한 early reversal에서는:

```text
reversal direction의
mature opposite M30 external liquidity
```

를 current objective family로 사용한다.

Old H1 continuation objective나
old H1 historical liquidity를
반대 방향 TP 확장에 사용하지 않는다.

이후 old H1 owner가 invalidated되고
새 opposite mature H1 owner가 확정되면:

```text
new H1/M30 owner와 호환되는
new-direction external liquidity
```

를 새 scenario의 objective family로 사용한다.

#### Objective family freeze

PLAN 시점에 다음을 freeze한다.

```text
scenario_scope
owner / parent context
direction
objective_candidate_ids
candidate prices
candidate order
candidate availability
```

Entry와 hard SL이 확정된 뒤에는:

```text
새 liquidity candidate 추가
candidate 순서 변경
더 큰 R candidate 삽입
hindsight target 탐색
```

을 금지한다.

#### Final TP selection

Selected FVG Entry와 normalized strategy SL이 확정되면
freeze된 objective family를
trade direction으로 가까운 순서대로 검사한다.

각 candidate는:

1. 이미 consumed이면 건너뛴다.
2. current scope와 호환되지 않으면 건너뛴다.
3. reward가 0 이하이면 건너뛴다.
4. planned R `< 1`이면 final TP 자격에서는 제외한다.
5. planned R `< 1`인 valid liquidity는 필요하면 `INTERMEDIATE_DELIVERY`로 기록한다.
6. planned R `>= 1`인 최초 candidate를 final TP로 선택한다.

`planned R >= 1`은:

```text
objective-candidate eligibility
```

조건이다.

다음이 아니다.

```text
trade-wide immediate rejection filter
max-R optimizer
farthest-target selector
```

같은 family 안에서는
R이 더 크다는 이유로
더 먼 liquidity를 선택하지 않는다.

Frozen family 전체를 검사한 뒤에도
planned R `>= 1`인 candidate가 없으면:

```text
NO_TRADE
reason = NO_R_ELIGIBLE_OBJECTIVE
```

다.

#### Final TP freeze

Final TP는:

```text
objective family freeze
→ meaningful CHoCH
→ selected FVG
→ Entry
→ normalized strategy SL
→ objective eligibility evaluation
→ final TP freeze
→ pending order submission
```

순서로 정한다.

Final TP가 freeze된 뒤
pending fill 전에 해당 objective가 먼저 delivered되면:

```text
CANCELED_OBJECTIVE_DELIVERED
```

로 scenario와 pending order를 취소한다.

같은 scenario 안에서
다음 objective candidate로 자동 rollover하지 않는다.

TP는 selected structural liquidity의 actual price를 사용한다.

Swing liquidity는 actual wick high / low를 사용한다.

V1 baseline은:

```text
max-R TP extension
arbitrary farther target
spread-based TP extension
1-tick outward TP extension
```

을 사용하지 않는다.

LONG TP는 Bid-side,
SHORT TP는 Ask-side execution semantics를 따른다.

#### Long-horizon H4 liquidity extension

Current H1/M30 objective authority가 항상 우선한다.

PLAN 시점에:

```text
plan_reference_price
=
objective family freeze 시각까지 available한
가장 최근 closed M1 candle의 close
```

를 기록한다.

먼저 current H1/M30의:

```text
causally-known
unconsumed
direction-ahead
scope-compatible
```

primary candidate를 수집한다.

Primary candidate가 하나 이상이면:

LONG:
```text
primary_directional_horizon
=
가장 높은 primary candidate price
```

SHORT:
```text
primary_directional_horizon
=
가장 낮은 primary candidate price
```

다.

Primary candidate가 없으면:

```text
primary_directional_horizon
=
plan_reference_price
```

다.

그 뒤 다음 H4 liquidity만
동일 frozen ordered family의 바깥쪽 extension candidate로 추가할 수 있다.

```text
family = EXTERNAL_SWING
timeframe = H4
state = ACTIVE
```

LONG:

```text
H4 price > primary_directional_horizon
```

SHORT:

```text
H4 price < primary_directional_horizon
```

H4 extension은 다음 scope에서만 허용한다.

```text
EXTERNAL_CONTINUATION

EXTERNAL_REVERSAL
only after a new mature opposite H1 owner exists
```

다음 early reversal에는 H4 extension을 사용하지 않는다.

```text
old H1 owner still active
+
reversal permission OPEN
+
opposite M30-led early EXTERNAL_REVERSAL
```

이 경우 objective authority는
기존 규칙대로 opposite mature M30 external liquidity에 한정한다.

H4 candidate는 current H1/M30 horizon 안쪽 target을 대체하거나
더 큰 R을 만들기 위해 삽입되지 않는다.

PLAN freeze 후 Entry/SL이 알려지면
기존 nearest-first / `planned R >= 1` eligibility 규칙만 적용한다.

H4는 active direction/source/entry authority가 아니다.

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

```text
현재 mature HTF trend 우선
```

이다.

H1이 mature BULLISH / BEARISH이면
H1이 highest active directional owner다.

H1 trend가 유효하고
현재 H1 directional external extreme과
아직 interaction하지 않았다면:

```text
trade direction = H1 direction
```

만 first-position planning authority를 가진다.

예:

```text
H1 BULLISH
M30 BEARISH
H1 reversal reference high 미도달
```

이면 M30 bearish는:

```text
H1 bullish trend 내부 correction context
```

이며 그 사실만으로 SHORT lane을 만들지 않는다.

#### Reversal reference extreme

Mature bullish H1:

```text
현재 H1 owner flow의
가장 높은 valid structural external high
→ reversal-reference buy-side liquidity
```

Mature bearish H1:

```text
현재 H1 owner flow의
가장 낮은 valid structural external low
→ reversal-reference sell-side liquidity
```

Protected swing과 reversal reference는 역할이 다르다.

```text
Protected swing
→ current H1 trend invalidation boundary

Reversal reference extreme
→ opposite-direction reversal hypothesis permission boundary
```

#### Reference availability

Reference는 causal하게 available된 이후에만 사용할 수 있다.

새 reference가 current bar close에서 처음 available됐다면
그 bar의 더 이른 intrabar movement를
새 reference interaction으로 소급 사용하지 않는다.

#### Reference event precedence

동일 closed H1 bar에서
reference 관련 조건이 겹치면
다음 순서로 하나만 판정한다.

Bullish H1 reference high:

```text
1. close > reference_high
   → CONTINUATION_BODY_BREAK

2. high > reference_high
   AND close <= reference_high
   → SWEEP_REJECTION

3. high >= reference_high
   → TOUCH
```

Bearish H1 reference low:

```text
1. close < reference_low
   → CONTINUATION_BODY_BREAK

2. low < reference_low
   AND close >= reference_low
   → SWEEP_REJECTION

3. low <= reference_low
   → TOUCH
```

Continuation body-break가 성립한 bar에서
reversal permission을 잠깐 OPEN했다가
같은 close에서 다시 CLOSED하는
transient state를 만들지 않는다.

#### TOUCH

Bullish H1:

```text
high >= reversal_reference_high
→ OPEN_FOR_SHORT
```

Bearish H1:

```text
low <= reversal_reference_low
→ OPEN_FOR_LONG
```

단,
위 precedence에서 continuation body-break 또는 sweep/rejection이
먼저 성립하지 않은 경우에만 TOUCH로 분류한다.

TOUCH는:

```text
H1 trend reversal
entry signal
automatic counter-trend order
```

가 아니다.

단지 opposite LTF structure를
potential external-reversal evidence로 평가할 permission을 연다.

#### SWEEP / REJECTION

Bullish:

```text
high > reference_high
AND
close <= reference_high
→ SWEEP_REJECTION
→ OPEN_FOR_SHORT
```

Bearish:

```text
low < reference_low
AND
close >= reference_low
→ SWEEP_REJECTION
→ OPEN_FOR_LONG
```

Sweep/rejection은 reversal/liquidity context evidence지만
자동 order 또는 score를 만들지 않는다.

Actual reversal order에는 여전히:

```text
reversal permission OPEN
→ valid opposite map/context
→ valid opposite Root/source lineage
→ source contact
→ mature pre-existing sweep
→ meaningful M1 CHoCH
→ causal displacement FVG
→ first retest
```

전체 chain이 필요하다.

#### CONTINUATION BODY BREAK

Bullish:

```text
close > reference_high
```

Bearish:

```text
close < reference_low
```

이면 current trend 방향의 continuation BOS evidence다.

Result:

```text
old reversal permission CLOSED
old reversal watch terminated
normal BOS / protected-swing lifecycle
```

새 directional external extreme이 causal하게 available되면
그 extreme을 다음 reversal reference로 사용한다.

#### Opposite M30 before permission

H1 mature trend가 유지되고
reversal permission이 CLOSED라면
opposite M30/LTF trend는:

```text
HTF_INTERNAL_CORRECTION_CONTEXT
```

다.

독립적인 opposite first-position order scope가 아니다.

`INTERNAL_ROTATION`은 current V1 first-position scenario scope로 사용하지 않는다.

#### Opposite LTF after permission

HTF reversal-reference interaction으로
reversal permission이 OPEN된 뒤에는
opposite M30/LTF structure를
external-reversal hypothesis evidence로 평가할 수 있다.

단순 opposite M30 trend 하나만으로 order를 허가하지 않는다.

Required:

```text
1. reversal permission OPEN
2. deterministic opposite map/context
3. valid opposite Root/source lineage
4. complete base execution chain
```

H1 trend_state는 protected swing body-break 전까지
기존 BULLISH / BEARISH를 유지할 수 있다.

즉:

```text
trade hypothesis may reverse
before H1 trend label flips
```

이다.

#### H1 owner invalidation

H1 protected swing body-break:

```text
old H1 trend invalidated
→ H1 TRANSITION
```

이미 valid하게 freeze된 early EXTERNAL_REVERSAL scenario를
사후에 다른 scope로 다시 쓰지 않는다.

새 owner 아래의 새 해석은
새 scenario_id로 만든다.

#### H1 NEUTRAL / TRANSITION

H1에 mature directional owner가 없고
M30이 mature directional이면:

```text
highest_active_map = M30
scenario_scope = EXTERNAL_CONTINUATION
```

relative to M30로 처리한다.

M30 dealing range와
M30 external objective family를 사용한다.

Old H1 dealing range,
old H1 reversal reference,
old H1 objective family를
자동 상속하지 않는다.

M1은 HTF reversal permission 또는 map owner를
생성하거나 덮어쓰지 않는다.

### 3.3 dealing range와 premium/discount는 context로 기록한다

- H1/M30의 현재 external protected extreme과 directional extreme으로 active dealing range를 정하고 EQ 50%를 표시한다.
- Source/context의 현재 위치가 premium / discount 중 어디인지 기록한다.
- Premium/discount는 시장 위치를 설명하는 reference/context 정보이며, 그 자체로 scenario 또는 주문 권한을 만들지 않는다.
- `EXTERNAL_CONTINUATION` source/context가 통상적인 directional half와 반대쪽에 있더라도 그 사실 하나만으로 Root, source, scenario 또는 거래를 거부하지 않는다.
- Premium/discount는 standalone veto가 아니다. 다른 필수 causal chain이 유효하면 PD 위치만으로 `NO_TRADE`를 만들지 않는다.
- H1 mature trend와 반대인 M30/LTF structure는 reversal permission이 CLOSED인 동안 correction context로만 사용한다.
- `INTERNAL_ROTATION`은 current V1 first-position order scope가 아니다.
- HTF reversal-reference interaction으로 permission이 OPEN된 뒤에만 opposite LTF structure를 `EXTERNAL_REVERSAL` hypothesis로 평가한다.
- 실제 주문에는 Root, causal refinement, source contact, mature sweep, M1 CHoCH, causal FVG 등 나머지 필수 chain이 모두 필요하다.

## 4. HTF root OB

최초 포지션의 Root는 사전에 존재하는 `H1`, `M30`, 또는 `M15` causal OB여야 한다.

Root는 다음을 모두 설명해야 한다.

1. 의미 있는 external/protected 또는 structurally meaningful internal swing의 origin context에 있다.
2. 해당 origin window 안의 마지막 opposite candle이다.
3. 그 candle에서 시작한 same causal directional leg가 의미 있는 structure level을 body close로 전달했다.
4. 현재 scenario direction/objective와 causal하게 연결된다.
5. `strategy_state = ACTIVE`다.

Root strategy state는:

```text
ACTIVE
INVALIDATED
```

두 개만 사용한다.

Bullish Root:

```text
Root-own-timeframe close < Root.bottom
→ INVALIDATED
```

Bearish Root:

```text
Root-own-timeframe close > Root.top
→ INVALIDATED
```

Owner/causal structure invalidation도 Root를 invalidated한다.

다음은 Root invalidation이 아니다.

```text
touch
partial mitigation
wick-only distal penetration followed by recovery
N touches
age
```

따라서 `fully consumed`, `fresh/mitigated/consumed` 같은 별도 Root strategy state를 사용하지 않는다.

다음은 Root가 아니다.

- 화면에서 가장 가까운 반대색 캔들
- M1 반응을 보고 사후 선택한 HTF 캔들
- structure delivery를 만들지 않은 임의 candle
- FVG overlap만 있는 candle
- HTF FVG 자체
- 이미 `INVALIDATED`된 Root

HTF FVG는 delivery inefficiency evidence일 수 있지만
standalone Root/source authority를 갖지 않는다.

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

### 5.1 Root / final refined source invalidation

Root와 child는 strategy layer에서:

```text
ACTIVE
INVALIDATED
```

두 상태만 사용한다.

Touch나 partial mitigation은
audit information이며
그 자체로 source authority를 제거하지 않는다.

Bullish Root / child:

```text
source 자신의 timeframe에서
close < source.bottom
→ PRICE_INVALIDATED
```

Bearish Root / child:

```text
source 자신의 timeframe에서
close > source.top
→ PRICE_INVALIDATED
```

Strict inequality를 사용한다.

```text
close == distal
→ invalidation 아님
```

Wick-only distal penetration 후
source-own-timeframe close가 source 안으로 회복되면
source는 invalidated되지 않는다.

즉:

```text
wick through source distal + recovery
→ valid sweep/reaction context 가능

adverse body close through source distal
→ source invalidation
```

이다.

이 규칙 때문에
source distal을 넘는 liquidity-sweep wick과
source invalidation을 같은 wick 하나로 동시에 선언하지 않는다.

Parent Root invalidation은 descendant에 전파한다.

```text
parent invalidated
→ all descendants invalidated
```

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
- `INITIAL_CHOCH_FVG`의 3개 구성 M1 candle은 실제 시간상 연속된 M1 bar여야 한다.
- Required: `Candle2.open_time = Candle1.open_time + 60 seconds` AND `Candle3.open_time = Candle2.open_time + 60 seconds`.
- session close, weekend, trading halt 또는 missing-M1 interval을 사이에 둔 3-candle pattern은 current V1 execution FVG가 아니다.
- 즉 시장이 닫힌 동안 생긴 가격 공백 자체를 CHoCH displacement FVG로 해석하지 않는다.
- 이 continuity rule은 execution FVG에만 적용한다. Session boundary 자체가 market structure, Root, source, sweep scenario를 자동 reset하지 않는다.
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

### 비활성 research execution variants

다음 protocol은 current V1 first-position 주문 권한이 없다.

```text
DELIVERY_FVG_REPLACEMENT
DELIVERY_FVG_ADDON
OB-only first entry
FVG inversion entry
mandatory additional-BOS entry
```

이들의 과거 상세 계약은
Git history 및 legacy research 문서에 보존한다.

Current V1 engine은 이 variant들의:

```text
candidate
strategy state
pending order
position
risk slot
```

을 생성하지 않는다.

별도 재감사와 독립 protocol 승격 전까지
current baseline execution path에 포함하지 않는다.

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

V1 first-position strategy state는:

```text
PLANNED
WAITING_TRIGGER
PENDING
FILLED
CANCELED
NO_TRADE
```

를 사용한다.

Source contact, sweep, CHoCH, FVG selection은
별도 persistent strategy state를 늘리는 대신
event ID와 timestamp로 기록한다.

Meaningful CHoCH close에서 같은 EA decision cycle로:

```text
eligible fresh FVG snapshot
→ widest FVG freeze
→ Entry 계산
→ SL 계산
→ frozen objective family에서 Final TP 선택
→ execution preflight
→ pending 즉시 제출
```

한다.

LONG:

```text
BUY LIMIT at bullish FVG.top
```

SHORT:

```text
SELL LIMIT at bearish FVG.bottom
```

Pending order는:

```text
ORDER_TIME_GTC
```

를 사용한다.

다음은 time-only cancellation authority가 아니다.

```text
N bars
N minutes
session close
day change
next trading day
periodic H1/M15 re-approval missing
```

Fill 전 strategy cancellation authority는 세 종류뿐이다.

```text
1. final objective validity
2. required source-lineage validity
3. scenario-direction authority
```

구체적으로:

```text
final objective delivered before fill
→ CANCELED

final refined source / required parent Root invalidated
→ CANCELED

continuation owner invalidated
→ CANCELED

early-reversal permission terminated by current-trend continuation body-break
→ CANCELED
```

Selected FVG가 정상 pending으로 등록된 뒤:

```text
50% mitigation
partial mitigation
distal penetration
full traversal
body-close-through-FVG
```

를 별도 strategy cancellation condition으로 사용하지 않는다.

Entry가 FVG near-side boundary 자체이므로
정상적인 가격 진행에서는
deeper FVG traversal보다 pending activation/fill이 먼저 발생한다.

Broker rejection, StopsLevel, FreezeLevel,
server cancellation failure는
strategy invalidation이 아니라
execution result로 별도 기록한다.

Pending이 fill된 뒤에는
처음 freeze한 SL / TP가 실험 결과를 결정한다.

Fill 후 source / owner / M1 state 변화로
포지션을 임의 종료하지 않는다.

### Session / market-gap handling

Session close, daily pause, weekend 또는 scheduled market closure 자체는:

```text
scenario cancellation
pending cancellation
map reset
source reset
sweep reset
```

권한이 아니다.

따라서 causal validity가 살아 있다면
scenario state는 그대로 유지한다.

V1은 session close 직전이라는 이유만으로
pending을 미리 취소하지 않는다.

단, 이 규칙을 실제 server pending으로 구현하려면
symbol이 persistent GTC를 지원해야 한다.

Order submission preflight에서 반드시 확인한다.

```text
SYMBOL_EXPIRATION_MODE supports SYMBOL_EXPIRATION_GTC

AND

SYMBOL_ORDER_GTC_MODE == SYMBOL_ORDERS_GTC
```

둘 중 하나라도 만족하지 않으면:

```text
strategy signal = VALID
execution = EXECUTION_INFEASIBLE
→ NO ORDER
```

다.

Broker의 daily order deletion을
EA가 다음 session에 재생성하는 방식으로
baseline strategy를 우회 구현하지 않는다.

CHoCH/FVG decision cycle 시점에
현재 symbol의 trading session에서 주문 제출이 허용되지 않으면:

```text
EXECUTION_INFEASIBLE
→ NO ORDER
```

로 처리한다.

같은 execution chain을 저장해 두었다가
다음 session open에 늦게 제출하지 않는다.

No-quote interval에는
가격이 어떤 경로로 움직였는지 추정하지 않는다.

다만 session reopen 뒤 들어오는
첫 실제 broker quote와 이후 실제 tick은
정상 market information으로 처리한다.

이미 server에 accepted된 GTC pending이
reopen gap으로 activation되면:

```text
requested strategy entry
≠ necessarily actual fill price
```

일 수 있다.

Actual fill은 broker / MT5의:

```text
DEAL_PRICE
```

를 사용한다.

Limit order가 gap으로 strategy entry보다 유리한 가격에 fill되어도:

```text
selected FVG
strategy Entry
strategy SL
TP
lot size
planned R authorization
```

을 사후 재계산하지 않는다.

Strategy geometry와 actual execution result를 둘 다 기록한다.

Gap fill 또는 gap SL/TP execution은
정상적인 market execution event이며
그 사실만으로 `EXECUTION_DIVERGENCE`로 분류하지 않는다.

Open position이 session gap을 넘어가고
reopen 첫 quote가 SL 또는 TP trigger를 이미 넘어선 경우에도
requested SL/TP 가격으로 임의 체결을 재구성하지 않는다.

MT5 history의:

```text
DEAL_REASON_SL
DEAL_REASON_TP
DEAL_PRICE
```

를 actual execution source of truth로 사용한다.

Session gap을 이유로
killzone / day-of-week / session-time strategy filter를 새로 추가하지 않는다.

### Hierarchical bootstrap / historical compression

EA startup은 과거 모든 structure / OB / FVG / CHoCH를
현재까지 영구 보존하지 않는다.

Bootstrap order:

```text
1. H4 long-horizon liquidity index
2. H1 / M30 / M15 chronological root-discovery stream
3. current scenario-relevant ACTIVE Roots freeze
4. targeted M30 / M15 / M5 child refinement
5. current-source local M5 / M1 liquidity reconstruction
6. READY
```

H4:

```text
→ same causal structure detector를 streaming replay
→ ACTIVE H4 EXTERNAL_SWING liquidity만 장기 보존
```

H1/M30/M15 root-discovery stream:

```text
H1/M30
→ active map authority

M15
→ map authority 없음
→ current H1/M30 causal context 아래 Root detector 역할만 가능
```

Historical M15 object tree 전체를 보존하지 않는다.

Current scenario와 관계가 끝난 historical object는
다음 active working-set에서 제거할 수 있다.

다만 아래 중 하나가 reference하면 RAM에서 제거할 수 없다.

```text
current neutral-range construction
current protected/external structure
open BOS correction window
ACTIVE liquidity
ACTIVE Root/child/source
active scenario
active CHoCH reference
H4 ACTIVE liquidity index
```

Consumed / invalidated / unreferenced object는:

```text
append-only audit storage에 기록
→ in-memory working set에서 eviction 가능
```

이다.

Audit log 자체를 전부 RAM에 보존할 필요는 없다.

Bootstrap 완료 뒤:

```text
execution_epoch_start
```

를 freeze한다.

다음 first-position execution event는 모두
`execution_epoch_start` 이후 새 event여야 한다.

```text
source contact
authorized sweep
meaningful M1 CHoCH
execution FVG
```

Pre-start CHoCH/FVG/pending hypothesis는 runtime order authority가 아니다.

Startup 첫 observable price가 이미 final source 내부라면:

```text
STARTED_INSIDE_SOURCE
```

만 기록한다.

새 contact를 소급 생성하지 않는다.

```text
exit source
→ later re-entry
→ new source contact
```

가 필요하다.

### Closed-bar multi-timeframe processing order

동일 timestamp에 여러 timeframe candle이 close되면:

```text
H4
→ H1
→ M30
→ M15
→ M5
→ M1
→ scenario/order authorization
```

순서로 처리한다.

각 timeframe close 내부에서는:

```text
1. pre-existing object invalidation / consumption update
2. structure-state update
3. newly confirmed object availability
4. dependent authorization
```

순서를 사용한다.

이 순서는 look-ahead를 추가하는 것이 아니라
동일 available timestamp의 deterministic tie-breaker다.

### First-position concurrency / exposure

Current V1은 risk-slot arbitration을 사용하지 않는다.

한 symbol + EA magic 기준:

```text
max one live scenario per direction

max one accepted first-position exposure:
PENDING + FILLED <= 1
```

Reversal permission이 CLOSED이면
active-map direction scenario만 first-position authority를 가진다.

Reversal permission이 OPEN된 뒤에는
opposite `EXTERNAL_REVERSAL` watch scenario가 존재할 수 있다.

하지만 하나의 scenario가 broker에 accepted된 pending을 가지거나
position이 fill되면
다른 scenario는 새 first-position order를 제출할 수 없다.

Blocked trigger chain을 exposure 종료 뒤 늦게 제출하지 않는다.
새 order에는 새 execution chain이 필요하다.

동일 processing epoch에서
서로 반대 방향의 first-position order가 동시에 완성되면:

```text
NO_TRADE
reason = AMBIGUOUS_SIMULTANEOUS_AUTHORIZATION
```

로 처리한다.

점수나 임의 direction priority를 만들지 않는다.

### SL

`INITIAL_CHOCH_FVG` strategy SL:

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

Strategy SL은 `SYMBOL_TRADE_TICK_SIZE`에 맞춰
risk를 줄이지 않는 방향으로만 normalize한다.

Broker:

```text
Bid / Ask
StopsLevel
FreezeLevel
trade mode
margin
```

제약은 strategy geometry를 바꾸지 않는다.

Frozen geometry가 실행 불가능하면:

```text
EXECUTION_INFEASIBLE
→ NO ORDER
```

다.

### V1 parity volume

Strategy correctness / parity baseline은:

```text
sizing_mode = MINIMUM_VOLUME_PARITY
order_volume = SYMBOL_VOLUME_MIN
```

을 사용한다.

Volume은:

```text
SYMBOL_VOLUME_MIN
SYMBOL_VOLUME_MAX
SYMBOL_VOLUME_STEP
```

를 검증한다.

Minimum volume 자체가 margin/request constraint를 통과하지 못하면:

```text
EXECUTION_INFEASIBLE
→ NO ORDER
```

다.

V1 parity 단계에서는 arbitrary risk-percent parameter를 추가하지 않는다.

성과의 전략 비교 단위는 우선 R이다.

Account-risk-percent sizing은
implementation parity 완료 뒤 별도 execution/risk policy로 검토한다.

### TP

- Objective family는 PLAN 단계에서 Entry/SL geometry를 알기 전에 freeze한다.
- Active V1 first-position scope는 `EXTERNAL_CONTINUATION`과 `EXTERNAL_REVERSAL` 두 개다.
- Candidate는 causally-known, unconsumed, direction-ahead, scope-compatible liquidity만 포함한다.
- 별도의 current/historical fallback tier를 만들지 않는다.
- Candidate 수에 arbitrary maximum cap을 두지 않는다.
- Candidate order는 trade direction으로 가까운 순서로 freeze한다.
- Entry와 normalized strategy SL이 확정되면 가까운 순서대로 planned R을 계산한다.
- planned R `<1` candidate는 final TP 자격에서 제외하고 필요하면 `INTERMEDIATE_DELIVERY`로 기록한다.
- planned R `>=1`인 최초 candidate를 final TP로 선택한다.
- 더 큰 R을 만들기 위해 candidate를 추가하거나 순서를 변경하거나 더 먼 TP를 선택하지 않는다.
- Frozen family 전체에 R-eligible candidate가 없으면 `NO_TRADE / NO_R_ELIGIBLE_OBJECTIVE`다.
- Final TP freeze 후 fill 전에 objective가 delivered되면 scenario와 pending을 취소한다.
- 같은 scenario에서 next objective로 rollover하지 않는다.
- V1 TP는 selected structural liquidity의 actual price를 사용한다.
- LONG TP는 Bid-side, SHORT TP는 Ask-side execution semantics를 따른다.

### 체결 후

- 최초 SL 또는 TP가 결과를 판정한다.
- 공포, 수익 보호 욕구, 중간 M1 반대 신호로 임의 청산하지 않는다.
- 시간 만료, 본절 이동, 부분 익절은 별도 승인 전까지 사용하지 않는다.

## 9. 즉시 비매매 조건

다음 중 하나라도 해당하면 current V1 first-position order를 만들지 않는다.

1. 현재 directional map 또는 trade-direction authority를 결정할 수 없다.
2. Active dealing range를 deterministic하게 결정할 수 없다.
3. Scenario scope와 ordered objective family를 결정할 수 없다.
4. Frozen objective family 전체에 planned R `>=1`인 valid candidate가 없다.
5. 의미 있는 HTF Root OB가 없다.
6. Valid causal lower-timeframe child를 최소 하나 찾지 못했다.
7. Parent-child가 같은 causal event / displacement를 설명하지 못한다.
8. Final refined source가 아직 contact되지 않았다.
9. Required sweep liquidity가 source-contact bar 이전부터 available하지 않았다.
10. Direction-compatible mature liquidity sweep이 없다.
11. Authorized sweep 시점에 valid opposite M1 correction protected swing이 없다.
12. Meaningful M1 CHoCH가 없다.
13. Meaningful CHoCH는 있지만 같은 sweep-to-CHoCH causal leg에 fresh valid FVG가 없다.
14. Widest valid FVG를 deterministic하게 하나 선택할 수 없다.
15. Selected FVG의 Entry / SL / TP geometry가 계산되지 않는다.
16. Frozen strategy geometry가 broker execution preflight를 통과하지 못한다.

비활성 research variant의 조건 충족 여부는
current V1 no-trade branch에 포함하지 않는다.

## 10. 블라인드 재생 규율

1. H1/M30에서 current map, scenario scope, ordered objective family와 Root context를 먼저 결정한다.
2. M30/M15/M5에서 causal refinement를 확인한다.
3. 가격이 final source에 도달하기 전에는 current scenario의 M1 trigger를 탐색하지 않는다.
4. Source contact 뒤에만 eligible pre-existing liquidity sweep과 M1 CHoCH를 본다.
5. PLAN에서 objective candidate family와 order를 먼저 freeze한다. Final TP 하나는 Entry/SL이 알려진 뒤 frozen family에서 선택한다.
6. 지나간 entry/retest를 사후 주문으로 복원하지 않는다.
7. 주문 전에 causal IDs, Entry, SL, TP, volume과 execution preflight를 기록한다.
8. 결과를 본 뒤 Root/liquidity/CHoCH/FVG/SL/TP를 다시 그리지 않는다.
9. 미래 데이터가 노출된 replay session은 protocol result에서 제외한다.
10. `PLANNED / WAITING_TRIGGER` 상태에서 가격이 source와 멀리 있고 causal invalidation도 없다면 동일 분석을 불필요하게 반복하지 않는다.
11. 사전에 선언된 structural/objective/source event에서만 replay를 정지한다.
12. 비활성 Delivery-FVG/OB-only/add-on variant는 current V1 blind-replay 판단에 사용하지 않는다.

## 11. 주문 전 필수 증거

주문 전에 최소 다음을 deterministic ledger에 기록한다.

```text
scenario_id
scenario_scope
scenario_direction
active_map_tf
owner / parent context

plan_reference_price
primary_directional_horizon
frozen ordered objective family
each candidate:
    liquidity_id
    family
    timeframe
    price
    order_index

selected final objective
selected final objective planned_R

Root ID / timeframe / bounds
final child ID / timeframe / bounds
parent-child lineage
source invalidation boundary

source_contact_at
active_sweep_event_id
active_choch_reference_swing_id
meaningful CHoCH event ID

eligible FVG IDs / widths
selected FVG ID / bounds / width

strategy Entry
raw SL
normalized SL
TP

sizing_mode
order_volume
EA magic number

Bid / Ask / spread
StopsLevel / FreezeLevel
GTC capability
execution preflight result
order-send retcode / broker ticket
strategy terminal reason if no order
```

Historical inactive variant state는 current V1 필수 증거가 아니다.

## 12. 성과 분류

### Strategy-valid trade

주문 전에 current V1의 필수 causal chain과
Entry / SL / TP geometry가 모두 freeze된 거래다.

### Protocol violation

다음은 PnL과 무관하게
current V1 strategy performance에서 제외한다.

- Root 누락
- causal refinement 누락
- source contact 이전 trigger-first 진입
- immature liquidity sweep 사용
- arbitrary micro pivot CHoCH
- causal FVG 없는 CHoCH entry
- widest-FVG rule 위반
- wrong FVG boundary entry
- 20% FVG SL rule 위반
- premium/discount를 standalone authorization 또는 veto로 사용
- wrong scenario direction authority
- objective-family hindsight modification
- farther-R target optimization
- post-selection TP rollover
- fill 전 objective delivery를 무시
- invalidated source/owner를 사용해 pending 유지

### Execution divergence

Strategy가 이미 CANCELED 상태인데
broker cancellation failure 등으로
실제 order가 fill된 경우:

```text
EXECUTION_DIVERGENCE
```

로 기록한다.

이것은 strategy-valid trade도
strategy protocol violation trade도 아니며
execution infrastructure failure로 별도 집계한다.

## 13. 최근 실패의 재발 방지

다음 실패 유형은 current V1 regression에서 반드시 차단한다.

- internal swing을 external liquidity로 잘못 승격
- HTF Root 없이 M1 trigger로 빈칸을 채움
- HTF FVG를 standalone source로 사용
- parent-child causal relation 없이 단순 overlap으로 refinement
- source contact 이전 M1 trigger-first 판단
- reaction 중 방금 생긴 high/low를 same setup의 mature liquidity로 사용
- premium/discount를 standalone gate로 사용
- M1 micro CHoCH를 HTF direction authority처럼 사용
- widest-FVG rule 위반
- selected FVG 20% SL geometry 변경
- frozen objective family를 Entry/SL 확인 뒤 변경
- fill 전에 objective가 delivered됐는데 pending 유지
- Root/final source가 body-close invalidated됐는데 pending 유지
- reversal permission이 continuation body-break로 종료됐는데 early-reversal pending 유지

단순 시간 경과,
periodic re-approval timestamp 누락,
비활성 Delivery-FVG protocol 상태는
current V1 regression reason으로 사용하지 않는다.

## 14. 주문 직전 최종 선언

주문 전에 다음 질문에 모두 답할 수 있어야 한다.

```text
현재 scenario_scope는 ________ 이다.
현재 trade-direction authority는 ________ 이다.
reversal permission이 필요한 경우 그 origin event는 ________ 이다.

active dealing range는 ________ ~ ________ 이다.
EQ는 ________ 이다.
현재 위치는 premium / discount 중 ________ 이다.

PLAN에서 freeze한 ordered objective family는 ________ 이다.
candidate 순서는 ________ 이다.
Final TP는 ________ 이다.
Final TP planned R은 ________ R이다.
이 candidate가 가장 가까운 R-eligible candidate인 이유는 ________ 이다.

Root는 ________ TF의 ________ 영역이다.
Final causal child는 ________ TF의 ________ 영역이다.
두 zone이 같은 causal event인 이유는 ________ 이다.
Source invalidation boundary는 ________ 이다.

가격은 ________ 시각에 final source를 contact했다.
Required liquidity ________ 은 ________ 시각부터 available했다.
Authorized sweep은 ________ 시각의 ________ event다.

M1 CHoCH reference는 ________ 이다.
Meaningful CHoCH event는 ________ 이다.

Eligible causal FVG는 ________ 이다.
Selected widest FVG는 ________ 이다.

Entry는 ________ 이다.
FVG width는 ________ 이다.
Raw SL은 ________ 이다.
Normalized strategy SL은 ________ 이다.
TP는 ________ 이다.

Order submission 시 Bid / Ask / spread는 ________ 이다.
StopsLevel / FreezeLevel은 ________ 이다.
Execution preflight 결과는 ________ 이다.
```

한 항목이라도 current V1 authority 기준으로 결정할 수 없으면
주문하지 않는다.

## 15. 한 문장 원칙

> M1 trigger로 거래의 원인을 찾지 않는다. 먼저 HTF swing OB와 causal LTF OB refinement로 시나리오를 완성하고, M1은 그 시나리오가 실제로 반응했는지만 확인한다.

## 16. Legacy regression records

과거 regression 사례의 구체적인:

```text
execution-OB Entry
old SL geometry
INTERNAL_ROTATION trade scope
periodic H1/M15 pending re-approval
legacy objective price
```

는 current V1 strategy authority가 아니다.

Historical evidence는 Git history와 research 문서에 보존한다.

새 V1 regression fixture는
현재 `AGENTS.md`와 `docs/ea/EA_SPEC.md`의 frozen contract로 다시 생성한다.

최소 regression class:

```text
wrong external/internal classification
missing Root
missing causal child
immature liquidity used as sweep
premium/discount used as standalone authorization/veto
missing meaningful CHoCH
missing causal FVG
wrong widest FVG
wrong FVG entry boundary
wrong 20% FVG SL
objective delivered before fill
source invalidated before fill
owner/direction authority revoked before fill
```

## 17. Ground Truth / AI pipeline status

Ground Truth V2,
Gemini replay,
API latency,
AI risk-slot orchestration은
current deterministic EA V1 strategy authority가 아니다.

현재 상태:

```text
BLOCKED
OUT_OF_BASELINE_PATH
```

EA V1은 AI runtime 없이
MT5 Strategy Tester와 향후 live MT5 환경에서
독립 실행되어야 한다.

Historical Ground Truth / Gemini execution contracts는
Git history 및 관련 research documents에 보존한다.
