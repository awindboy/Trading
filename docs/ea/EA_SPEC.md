# Mentor Baseline EA Specification

Status: DRAFT
Authority: `AGENTS.md`

## Rule Classification

- D — deterministic as currently specified
- H — heuristic threshold/definition must be chosen
- U — unresolved discretionary rule
- X — excluded from baseline

## 1. Timeframes

Map:
- H1
- M30

Refinement:
- M30
- M15
- M5

Correction context:
- M5

Trigger:
- M1

H4 is excluded from the baseline.

Only information available from closed bars may authorize a decision.

## 2. Market Structure

Status: PARTIALLY FROZEN

Primary authority:
- `AGENTS.md`

Primary implementation reference:
- `mentor_engine/structure.py`

Secondary references:
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`
- `mt5/legacy/MentorScenarioTraderEA.mq5`

`mt5/indicators/ICTCockpitIndicator.mq5`의 symmetric pivot detector는
현재 baseline의 structure authority로 사용하지 않는다.

### 2.1 Purpose

Market Structure 엔진의 목적은 차트의 모든 고점과 저점에 BOS/CHoCH를 붙이는 것이 아니다.

다음 상태를 deterministic하게 유지하는 것이 목적이다.

- 현재 map trend
- confirmed swing highs / lows
- external protected high / low
- internal swings
- active dealing range
- BOS
- CHoCH
- structure information availability time

H1/M30 구조가 시나리오 scope와 objective selection의 기반이 된다.

M15/M5 구조는 H1/M30 external structure 내부의 correction / refinement context로 사용한다.

M1 구조는 독립적인 외부 시나리오를 만들지 않고,
이미 사전에 준비된 HTF scenario의 reaction trigger를 확인하는 데 사용한다.

### 2.2 Candle Colour

Classification: D

각 확정봉은 다음과 같이 분류한다.

```text
close > open  -> bullish
close < open  -> bearish
close == open -> doji
```

Doji는 bullish 또는 bearish sequence 어느 쪽에도 포함되지 않는다.

따라서 doji가 발생하면 현재 3-candle wave confirmation sequence는 중단된다.

### 2.3 Wave Confirmation

Classification: D

Baseline EA는 symmetric pivot detector를 사용하지 않는다.

#### Swing High

이전 wave 이후 가격 상승 구간 뒤에
3개의 연속 bearish candle body가 확정되면 swing high 후보가 확정된다.

Swing High price는:

```text
이전 confirmed wave 이후
~
세 번째 bearish confirmation candle까지

구간 내 최고 wick high
```

이다.

#### Swing Low

이전 wave 이후 가격 하락 구간 뒤에
3개의 연속 bullish candle body가 확정되면 swing low 후보가 확정된다.

Swing Low price는:

```text
이전 confirmed wave 이후
~
세 번째 bullish confirmation candle까지

구간 내 최저 wick low
```

이다.

Wave는 swing price가 실제 발생한 시점과
그 wave를 알고 사용할 수 있게 된 시점을 별도로 기록한다.

Required fields:

```text
occurred_at
confirmed_at
available_at
price
side
timeframe
```

`available_at` 이전에는 해당 swing을 structure, liquidity 또는 entry 판단에 사용할 수 없다.

### 2.4 Initial Structure State

Classification: D

각 timeframe의 구조 엔진은 초기 상태에서:

```text
trend = NEUTRAL
protected_high = NONE
protected_low = NONE
external_high = NONE
external_low = NONE
```

으로 시작한다.

confirmed swing high / low는 수집할 수 있지만,
한쪽 구조가 body close로 파괴되기 전까지 directional external trend를 선언하지 않는다.

### 2.5 Initial BOS

Classification: D

Trend가 아직 NEUTRAL인 상태에서
가장 최근 사용 가능한 confirmed swing을 body close로 파괴하면 INITIAL_BOS가 발생한다.

#### Bullish INITIAL_BOS

```text
close > latest confirmed swing high
```

이면 bullish INITIAL_BOS다.

이때 최근 유효한 반대편 swing low가 새로운 protected low 후보가 된다.

#### Bearish INITIAL_BOS

```text
close < latest confirmed swing low
```

이면 bearish INITIAL_BOS다.

이때 최근 유효한 반대편 swing high가 새로운 protected high 후보가 된다.

Wick만 swing level을 통과하는 것은 INITIAL_BOS가 아니다.

### 2.6 Bullish External Structure State

Classification: D

Bullish external state에서는:

```text
trend = BULLISH
protected_low = current bullish structure invalidation swing
external_high = current bullish delivery extreme
```

를 유지한다.

#### Bullish BOS

현재 external high를 body close로 상향 돌파하면:

```text
close > external_high
```

bullish BOS가 발생한다.

BOS 후에도 external bullish direction은 유지된다.

새로운 opposite-side protected low는
해당 continuation leg 이전에 형성되어 있으며
현재 구조를 지키는 가장 최근의 causal confirmed swing low를 사용한다.

#### Bearish CHoCH

현재 protected low를 body close로 하향 돌파하면:

```text
close < protected_low
```

bearish CHoCH가 발생한다.

이 시점부터 기존 bullish external structure는 invalidated된다.

새 bearish state는
반대편 confirmed swing 구조를 이용해 새 protected high와 external low를 구성한다.

### 2.7 Bearish External Structure State

Classification: D

Bearish external state에서는:

```text
trend = BEARISH
protected_high = current bearish structure invalidation swing
external_low = current bearish delivery extreme
```

를 유지한다.

#### Bearish BOS

현재 external low를 body close로 하향 돌파하면:

```text
close < external_low
```

bearish BOS가 발생한다.

#### Bullish CHoCH

현재 protected high를 body close로 상향 돌파하면:

```text
close > protected_high
```

bullish CHoCH가 발생한다.

이 시점부터 기존 bearish external structure는 invalidated된다.

### 2.8 BOS vs CHoCH

Classification: D

BOS는 현재 external trend와 같은 방향으로 구조를 전달하는 break다.

CHoCH는 현재 external structure를 지키는 protected swing을
반대 방향 body close로 파괴하는 event다.

Example:

```text
Bullish state

external high break
-> bullish BOS

protected low break
-> bearish CHoCH
```

```text
Bearish state

external low break
-> bearish BOS

protected high break
-> bullish CHoCH
```

모든 opposite-direction lower-timeframe break를 CHoCH로 승격하지 않는다.

특히 M1 CHoCH만으로 H1/M30 external reversal을 선언하지 않는다.

### 2.9 Wick Breach

Classification: D

Structure break는 반드시 body close를 요구한다.

따라서:

```text
high > structure high
but
close <= structure high
```

또는

```text
low < structure low
but
close >= structure low
```

이면 structure break가 아니다.

이 event는 liquidity module에서 sweep candidate로 평가할 수 있지만
Market Structure state를 직접 변경하지 않는다.

### 2.10 Internal vs External Swing

Classification: D

모든 confirmed wave는 생성 시점에 자동으로 external swing이 되지 않는다.

#### External swing

현재 external trend의 구조를 실제로 정의하거나
현재 dealing range를 확장하는 swing만 external로 승격한다.

Bullish state에서는:

- protected low
- 현재 bullish delivery extreme / external high

가 external structure를 구성한다.

Bearish state에서는:

- protected high
- 현재 bearish delivery extreme / external low

가 external structure를 구성한다.

#### Internal swing

현재 external protected high/low 범위 안에서 발생하는
하위 swing은 기본적으로 internal로 유지한다.

Internal swing은:

- liquidity candidate
- correction context
- LTF refinement
- M1 trigger structure

에는 사용할 수 있지만,

그 자체로 H1/M30 external trend를 뒤집지 않는다.

### 2.11 External Swing Promotion

Classification: D

새 confirmed swing은 현재 trend 방향의 external range를 실제로 확장할 때만
directional external swing으로 승격할 수 있다.

#### Bullish state

새 swing high가 기존 external high보다 높고
현재 bullish range high를 확장할 경우
새 external high로 승격할 수 있다.

그 사이에 형성된 lower highs / higher lows는 기본적으로 internal structure다.

#### Bearish state

새 swing low가 기존 external low보다 낮고
현재 bearish range low를 확장할 경우
새 external low로 승격할 수 있다.

그 사이의 lower highs / higher lows는 기본적으로 internal structure다.

### 2.12 Protected Swing Lifecycle

Classification: D

Protected swing은 단순히 가장 최근 swing이 아니다.

현재 external structure가 유지되기 위해 지켜져야 하는 opposite-side causal swing이다.

#### Bullish state

```text
protected_low
```

가 존재한다.

Bullish continuation 중 형성되는 모든 새로운 swing low가
자동으로 protected low가 되지 않는다.

Continuation BOS와 그 leg의 causal relationship이 확인될 때
새로운 protected low로 갱신할 수 있다.

protected low body break 전까지 bullish external state는 유지된다.

#### Bearish state

```text
protected_high
```

가 존재한다.

모든 새로운 swing high가 자동으로 protected high가 되지 않는다.

Continuation BOS와 연결된 causal opposite swing만
새 protected high로 승격한다.

protected high body break 전까지 bearish external state는 유지된다.

### 2.13 Active Dealing Range

Classification: D

Active dealing range는 단순 최근 pivot high / low가 아니다.

H1/M30의 현재 external structure를 구성하는 protected extreme과
directional delivery extreme을 사용한다.

#### Bullish structure

```text
range_low  = protected_low
range_high = current external high
```

#### Bearish structure

```text
range_high = protected_high
range_low  = current external low
```

EQ:

```text
EQ = (range_high + range_low) / 2
```

Continuation setup에서는:

```text
long  -> discount
short -> premium
```

조건을 적용한다.

Premium / discount 자체는 entry signal이 아니다.

### 2.14 Timeframe Independence

Classification: D

각 timeframe은 독립적인 Structure State를 유지한다.

Required map states:

```text
H1
M30
M15
M5
M1
```

그러나 역할은 동일하지 않다.

```text
H1 / M30
-> external map authority

M15 / M5
-> internal correction / refinement context

M1
-> executable trigger structure
```

M1 state 변화는 H1/M30 structure state를 직접 덮어쓰지 않는다.

### 2.15 Closed-Bar Rule

Classification: D

Structure authorization은 확정봉 데이터만 사용한다.

현재 진행 중인 candle의:

```text
high
low
close
```

를 이용해 BOS, CHoCH 또는 wave confirmation을 미리 확정하지 않는다.

각 event는:

```text
occurred_at
available_at
```

을 별도로 보존한다.

EA가 event를 사용할 수 있는 최초 시각은 `available_at`이다.

### 2.16 Look-Ahead Prevention

Classification: D

다음 행위를 금지한다.

- future candles를 이용한 symmetric pivot confirmation을 baseline structure에 사용
- 이후 발생한 BOS를 보고 과거 swing의 rank를 과거 시점부터 external로 소급 적용
- unfinished HTF candle의 close를 structure break로 사용
- 향후 가격을 보고 protected swing을 재선택
- future session movement를 이용해 historical map을 다시 분류

Swing 또는 rank가 나중에 확정되더라도
그 정보의 effective time은 confirmation 이후다.

### 2.17 Session Gap Handling

Classification: H

`mentor_engine/structure.py`에는 market closure / gap이
physical displacement나 3-candle wave confirmation으로 잘못 처리되지 않도록
operational gap logic이 존재한다.

특히 기존 Python engine은:

- non-contiguous bars가 3-candle wave를 완성하지 못하게 함
- session gap 자체를 body break로 사용하지 않음
- M1의 긴 closure 뒤 execution structure 일부를 reset함

현재 이 동작은 sensible implementation safeguard이지만
`AGENTS.md`의 직접적인 전략 규칙은 아니다.

Baseline EA에 정확히 어떻게 적용할지는 별도 decision으로 확정한다.

Status:

```text
H — pending implementation decision
```

### 2.18 Warm-Up Requirement

Classification: H

Structure state는 테스트 시작 시점 이전의 과거 bars가 필요하다.

Warm-up의 목적은:

- active H1/M30 trend 복원
- protected swing 복원
- active dealing range 복원
- 아직 살아 있는 external liquidity context 복원

이다.

고정된 arbitrary bar count는 아직 확정하지 않는다.

Strategy Tester의 economic counting start보다 충분히 앞선 기간에서
structure state를 재구성해야 한다.

Exact warm-up requirement:

```text
TBD
```

### 2.19 Required Structure State

각 timeframe별 엔진은 최소 다음 상태를 노출한다.

```text
timeframe

trend:
    NEUTRAL
    BULLISH
    BEARISH

latest_confirmed_high
latest_confirmed_low

protected_high
protected_low

external_high
external_low

range_high
range_low
eq

confirmed_waves[]
structure_events[]
```

각 wave:

```text
id
side
price
occurred_at
confirmed_at
available_at
rank
rank_available_at
```

각 structure event:

```text
id
type:
    INITIAL_BOS
    BOS
    CHOCH

direction

broken_swing_id
broken_level

protected_swing_id
protected_level

occurred_at
available_at
```

### 2.20 Baseline Exclusions

Market Structure baseline에는 다음을 넣지 않는다.

```text
- symmetric pivot length optimization
- ATR-based swing quality score
- weighted swing ranking
- EMA trend bias
- H4 map
- fractal indicator dependency
- arbitrary BOS strength score
- AI-based swing selection
```

이들은 필요하면 별도 research variant로만 검토한다.

---


## 3. Liquidity

Status: PARTIALLY FROZEN

Primary authority:
- `AGENTS.md`

Primary implementation reference:
- `mentor_engine/liquidity.py`

Secondary references:
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`
- `research/mentor-youtube/MENTOR_MINIMAL_METHOD.md`

Legacy MQL5의 단순 recent-pivot liquidity logic은 baseline authority로 사용하지 않는다.

### 3.1 Purpose

Liquidity 엔진의 목적은 모든 swing high/low를 liquidity로 표시하는 것이 아니다.

Liquidity로 인정하려면:

```text
다른 시장 참여자가
그 가격 바깥에 stop을 둘
구조적 / 행동적 이유
```

가 있어야 한다.

따라서:

```text
confirmed swing != automatically tradable liquidity
```

이다.

V1은 모호한 유동성을 많이 탐지하는 것보다
신뢰할 수 있고 반복 가능한 liquidity pool을 적게 탐지하는 것을 우선한다.

### 3.2 V1 Eligible Liquidity Families

V1 baseline에서 허용하는 liquidity family는 다음 세 가지다.

```text
1. EXTERNAL_SWING
2. DEFENDED_RANGE_EDGE
3. STRUCTURAL_REACTION
```

다음은 V1에서 제외한다.

```text
TRENDLINE_CLUSTER
simple recent pivot
round number
session high/low by itself
arbitrary local high/low
```

이들은 향후 별도 research variant로 검토할 수 있다.

### 3.3 External Swing Liquidity

Classification: D

V1에서 가장 우선적으로 신뢰하는 liquidity다.

Market Structure 엔진에서 이미 external/protected 의미가 확정된
구조적 고점/저점을 사용한다.

단순히 H1/M30에서 최근에 보이는 고점/저점이라는 이유만으로
external liquidity가 되지 않는다.

Required conditions:

1. confirmed wave여야 한다.
2. Market Structure state에 의해 external/protected 의미가 확정되어야 한다.
3. 해당 의미가 확정된 시점 이전에는 liquidity로 사용할 수 없다.
4. 실제 outer wick extreme이 sweep/delivery reference level이다.

Examples:

```text
H1/M30 meaningful previous high
-> buy-side external liquidity

H1/M30 meaningful previous low
-> sell-side external liquidity
```

단, 해당 level은 현재 Market Structure engine에서
external/protected structure의 일부로 인정되어야 한다.

### 3.4 Defended Range Edge

Classification: D for V1 protocol

V1은 명확하게 위와 아래가 반복 방어된 박스형 range만 사용한다.

기본 형태:

```text
HIGH 1 -------- HIGH 2
   |              |
   |    RANGE     |
   |              |
LOW 1  -------- LOW 2
```

Required operational conditions:

1. four confirmed waves가 alternating sequence를 구성한다.
2. 두 high의 wick 영역이 서로 overlap한다.
3. 두 low의 wick 영역이 서로 overlap한다.
4. range가 완성되기 전 body close가 해당 defended box를 명확히 이탈하지 않는다.
5. 네 번째 wave가 confirmed되기 전에는 range-edge liquidity가 존재하지 않는다.

Alternating sequence examples:

```text
HIGH -> LOW -> HIGH -> LOW
```

또는:

```text
LOW -> HIGH -> LOW -> HIGH
```

High defended edge는 buy-side liquidity다.

Low defended edge는 sell-side liquidity다.

#### V1 restriction

다음처럼 한쪽에만 equal highs/equal lows가 존재하는 경우는
V1 baseline에서는 독립적인 defended edge로 승격하지 않는다.

```text
HIGH ---- HIGH
```

또는:

```text
LOW ----- LOW
```

이것은 의미 없는 패턴이라는 뜻이 아니다.

V1에서 임의의 price tolerance를 추가하지 않고
보수적인 deterministic baseline을 유지하기 위한 제한이다.

향후 별도 variant에서 independent equal-high/equal-low detector를 비교한다.

### 3.5 Structural Reaction Liquidity

Classification: D for V1 protocol

이미 구조적으로 의미가 확인된 causal OB에서 가격이 반응하고,
그 반응으로 confirmed swing이 형성되면
해당 swing 바깥에 새로운 stop liquidity가 생긴 것으로 본다.

직관:

```text
pre-existing meaningful OB
        |
        v
price touches OB
        |
        v
visible reaction
        |
        v
confirmed reaction swing
        |
        v
participants may place stops beyond that swing
```

#### Bullish reaction

Pre-existing bullish structural OB에서 반응하여
confirmed swing low가 형성되면:

```text
reaction low
-> sell-side liquidity
```

후보가 된다.

#### Bearish reaction

Pre-existing bearish structural OB에서 반응하여
confirmed swing high가 형성되면:

```text
reaction high
-> buy-side liquidity
```

후보가 된다.

Required conditions:

1. causal OB는 reaction 이전에 이미 존재해야 한다.
2. OB는 현재 zone/source rules에 의해 structurally owned 상태여야 한다.
3. price reaction은 해당 OB에 실제로 접촉해야 한다.
4. reaction 이후 opposite wave가 confirmed되어야 한다.
5. liquidity는 reaction wave confirmation 이후에만 사용할 수 있다.

#### V1 restriction

단순 FVG touch만으로 reaction liquidity를 생성하지 않는다.

단순 최근 swing이 OB 근처에 있다는 이유만으로도 생성하지 않는다.

정확한 OB 생성/ownership 규칙은 이후 `HTF Root OB` 및
`Causal LTF Refinement` specification에서 확정한다.

따라서 Structural Reaction Liquidity는
해당 zone engine이 causal OB를 확정할 수 있을 때 활성화된다.

### 3.6 Trendline Liquidity

Classification: X in V1

V1 baseline에서는 trendline liquidity를 사용하지 않는다.

Reason:

사람에게 명확해 보이는 trendline을
EA에서 동일하게 재현하는 deterministic definition이 현재 충분히 안정적이지 않다.

기존 Python의 3-wave line projection 방식은
유용한 research implementation이지만
현재 Mentor strategy authority 자체로 승격하지 않는다.

향후 별도 immutable research variant로 검증할 수 있다.

### 3.7 Liquidity Side

Classification: D

```text
HIGH-side pool
-> buy-side liquidity
-> stops / breakout interest above
-> sweep may support short reaction context

LOW-side pool
-> sell-side liquidity
-> stops / breakout interest below
-> sweep may support long reaction context
```

Liquidity object 자체는 trade direction을 결정하지 않는다.

Trade direction은:

```text
map
objective
source/context
swept liquidity side
```

를 함께 사용해 결정한다.

### 3.8 Liquidity Bounds

Classification: D

Liquidity는 필요할 경우 price zone으로 저장한다.

Required representation:

```text
bottom
top
```

Swing-based pool의 wick zone:

```text
HIGH swing:
bottom = max(open, close)
top    = high

LOW swing:
bottom = low
top    = min(open, close)
```

Defended range edge는
defending wick intervals의 overlap을 bounds로 사용할 수 있다.

하지만 physical sweep / delivery 판단의 outer reference는:

```text
HIGH pool -> top
LOW pool  -> bottom
```

이다.

### 3.9 Availability Time

Classification: D

Liquidity는 그 존재 이유가 causal하게 확정된 이후에만 사용할 수 있다.

Examples:

```text
external swing
-> external/protected rank availability 이후

defended range
-> required fourth wave confirmation 이후

structural reaction
-> reaction wave confirmation 이후
```

Required metadata:

```text
occurred_at
available_at
source_reason
source_id
```

나중에 확인된 liquidity를
과거 시점부터 존재했던 것처럼 사용할 수 없다.

### 3.10 Physical Sweep

Classification: D

Physical sweep은:

```text
pre-existing eligible liquidity
+
wick penetration
+
body close recovery
```

로 정의한다.

#### HIGH-side sweep

```text
high > pool.top
AND
close <= pool.top
```

#### LOW-side sweep

```text
low < pool.bottom
AND
close >= pool.bottom
```

Sweep은 liquidity event이지
그 자체로 entry trigger가 아니다.

다음 조건을 대신하지 않는다.

```text
valid map
valid objective
valid source/context
source contact
M1 CHoCH
valid execution zone
```

### 3.11 Body Delivery

Classification: D

Price가 liquidity outer level을 body close로 통과하면
wick sweep이 아니라 directional delivery로 처리한다.

HIGH-side:

```text
close > pool.top
```

LOW-side:

```text
close < pool.bottom
```

해당 pool은 consumed 처리한다.

### 3.12 Pool Consumption

Classification: D

Liquidity pool은 physical sweep 또는 body delivery가 발생하면 consumed된다.

```text
sweep
-> consumed

body delivery
-> consumed
```

Consumed pool은 동일한 structural reason으로 다시 사용할 수 없다.

새 liquidity를 사용하려면
새로운 causal structural reason이 형성되어야 한다.

### 3.13 Same-Bar Self-Sweep Prevention

Classification: D

현재 bar close에서 처음 available해진 liquidity를
같은 bar의 intrabar high/low가 이미 sweep한 것으로 처리하지 않는다.

즉:

```text
pool.available_at == current_bar_close
```

이면 해당 bar 내부 움직임으로 그 pool의 sweep을 선언할 수 없다.

Pool은 다음 causal processing step부터 active하다.

이 규칙은 self-referential event와 look-ahead를 방지한다.

### 3.14 Source Liquidity vs Objective Liquidity

Classification: D

동일한 LiquidityPool object model을 사용할 수 있지만
scenario 내 역할은 분리한다.

#### Source liquidity

Setup이 시작되기 전에 sweep되어야 할 liquidity.

```text
LONG scenario
-> LOW-side source liquidity

SHORT scenario
-> HIGH-side source liquidity
```

Source liquidity는 pre-existing이어야 한다.

#### Objective liquidity

가격이 전달될 목표 liquidity.

Objective는 단순 nearest pivot으로 선택하지 않는다.

Scenario scope와 frozen objective rules에 따라 선택한다.

정확한 objective-selection algorithm은
`Objective / TP` section에서 확정한다.

### 3.15 V1 Liquidity Priority

동시에 여러 liquidity candidate가 존재할 경우
V1은 단순히 가장 가까운 level을 자동 선택하지 않는다.

개념적 신뢰도 우선순위는:

```text
1. meaningful external/protected structure
2. clearly defended range edge
3. structurally-owned OB reaction liquidity
```

이다.

단, 이것을 weighted score로 구현하지 않는다.

실제 source/objective selection은
scenario scope와 causal ownership rule을 이용해 결정한다.

### 3.16 Explicit V1 Exclusions

다음은 V1 baseline liquidity source로 사용하지 않는다.

```text
trendline cluster
simple recent pivot
arbitrary local high/low
round number
session high/low by itself
ATR-based liquidity quality score
weighted maturity score
age-decay score
nearest-pivot fallback
AI-selected liquidity
```

이들은 필요하면 baseline 완성 후
독립된 research variant로 비교한다.

### 3.17 Required Liquidity Object

Minimum state:

```text
id

family:
    EXTERNAL_SWING
    DEFENDED_RANGE_EDGE
    STRUCTURAL_REACTION

side:
    HIGH
    LOW

bottom
top

source_id
source_reason

occurred_at
available_at

consumed
consumed_at
consumption_type:
    NONE
    SWEEP
    BODY_DELIVERY
```

### 3.18 Remaining Dependencies

Liquidity semantics는 V1 기준으로 대부분 확정하지만,
`STRUCTURAL_REACTION`의 실제 활성화는
zone engine의 다음 규칙이 확정되어야 완성된다.

```text
HTF Root OB
Causal LTF Refinement
OB ownership
OB validity / invalidation
```

따라서 Liquidity section status는 현재:

```text
PARTIALLY FROZEN
```

으로 유지한다.

---


## 4. HTF Root OB

Status: FROZEN FOR V1

Primary authority:
- `AGENTS.md`

Primary implementation reference:
- `mentor_engine/zones.py`

Secondary reference:
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`

Legacy MQL5의 단순 lookback-based last-opposite detector는
root-source authority로 사용하지 않는다.

### 4.1 Purpose

HTF Root OB는 최초 포지션 시나리오의
사전에 존재하는 causal source다.

다음 정의는 사용하지 않는다.

```text
bullish move 전 아무 마지막 bearish candle
bearish move 전 아무 마지막 bullish candle
```

V1 Root OB는 다음 causal chain을 설명해야 한다.

```text
meaningful HTF swing
        ↓
opposite candle in swing-origin region
        ↓
directional leg
        ↓
meaningful structure body-break
        ↓
confirmed causal Root OB
```

즉 Root OB는 candle pattern이 아니라
structure-owned source object다.

### 4.2 Allowed Root Timeframes

Classification: D

최초 position의 Root OB 허용 timeframe:

```text
H1
M30
M15
```

M5와 M1은 최초 Root owner가 될 수 없다.

```text
H1/M30/M15
-> root/source

M30/M15/M5
-> causal refinement 가능

M1
-> trigger/execution
```

동일 scenario에서 무조건 가장 높은 timeframe의 OB를 선택하지 않는다.

현재 structure owner와 displacement를
직접 설명하는 causal Root를 선택한다.

### 4.3 Direction

Classification: D

Bullish Root OB:

```text
meaningful low/swing-origin region
+
bearish candle
+
subsequent bullish structure delivery
```

Bearish Root OB:

```text
meaningful high/swing-origin region
+
bullish candle
+
subsequent bearish structure delivery
```

Doji는 opposite candle로 사용하지 않는다.

### 4.4 Meaningful Swing Context

Classification: D for V1 protocol

Root OB candidate는 의미 있는 swing formation에 속해야 한다.

Eligible swing context:

```text
external/protected swing
or
structurally meaningful internal swing
```

단순 micro pivot은 Root context가 아니다.

Root candidate는 해당 swing의 origin window 안에서 찾는다.

V1에서 `swing-origin window`는:

```text
confirmed meaningful swing을 형성한 causal wave leg의
실제 reversal/origin region
```

을 뜻한다.

구현 시 Market Structure engine의 confirmed wave ownership을 사용하며,
structure delivery와 무관한 이전 wave까지 검색 범위를 확장하지 않는다.

### 4.5 Root Candle Selection

Classification: D for V1 protocol

V1 Root candle은:

```text
meaningful swing-origin window 안에 존재하면서
subsequent causal directional leg가 시작되기 전의
last opposite candle
```

이다.

즉:

```text
last opposite candle anywhere
```

가 아니라:

```text
last opposite candle
within the meaningful swing-origin causal window
```

이다.

이 규칙은 기존 `mentor_engine/zones.py`의
deterministic last-opposite 탐색 원리를 재사용하되,
meaningful swing ownership constraint를 추가한다.

### 4.6 Same Causal Leg Requirement

Classification: D

Root candle과 linked structure event는
같은 directional causal leg에 속해야 한다.

금지:

```text
과거 unrelated bearish candle
        ↓
몇 개 wave 경과
        ↓
현재 bullish BOS
        ↓
과거 candle을 bullish Root로 연결
```

허용:

```text
meaningful swing origin
        ↓
root candle
        ↓
same directional leg
        ↓
structure delivery
```

Market closure/session gap을 가로질러
이전 session candle을 새 displacement의 Root로 연결하지 않는다.

### 4.7 Structure Delivery Confirmation

Classification: D

Root candidate가 실제 Root OB로 승격되려면
그 이후 directional leg가 의미 있는 structure level을
몸통 종가로 돌파해야 한다.

Bullish:

```text
close > meaningful protected/owned high
```

Bearish:

```text
close < meaningful protected/owned low
```

Wick-only breach는 Root confirmation용 structure delivery가 아니다.

Linked event는 현재 Market Structure engine이 생성하는
valid BOS/CHoCH 계열 event여야 한다.

### 4.8 Displacement Proof

Classification: D for V1 protocol

V1은 별도의:

```text
ATR multiplier
minimum candle-body percentage
minimum consecutive candle count
minimum FVG size
```

를 displacement 필수 조건으로 추가하지 않는다.

Minimum displacement proof는:

```text
Root candidate에서 시작한 directional leg가
meaningful structure level을 body close로 실제 전달했다
```

는 사실이다.

즉:

```text
meaningful structure delivery
= V1 minimum displacement proof
```

FVG는 추가 delivery evidence일 수 있으나 필수 조건이 아니다.

### 4.9 FVG Relationship

Classification: D

HTF FVG는 최초 position의 standalone Root source가 될 수 없다.

```text
FVG only
-> no Root authority
```

FVG가 존재하더라도 causal Root OB가 없으면
최초 scenario를 승인하지 않는다.

반대로 valid Root OB가 structure delivery를 만들었다면
FVG가 없다는 이유만으로 Root를 폐기하지 않는다.

V1:

```text
causal OB + meaningful structure delivery
-> Root candidate/confirmation

FVG
-> optional delivery evidence
```

### 4.10 Root OB Family

Classification: D for V1 protocol

V1 최초 Root source는:

```text
LAST_OPPOSITE_OB lineage
```

를 사용한다.

단, 기존 detector의 모든 LAST_OPPOSITE_OB를 인정하는 것이 아니라
다음 filter를 모두 통과해야 한다.

```text
meaningful swing ownership
same causal leg
valid opposite candle
meaningful structure body-break
scenario direction alignment
freshness
```

`FVG_ORIGIN_OB`는 V1 최초 Root source로 사용하지 않는다.

향후 별도 immutable research variant로 비교할 수 있다.

### 4.11 Root Bounds

Classification: D for V1

Root OB의 initial HTF bounds는
origin candle의 전체 wick range를 사용한다.

```text
bottom = candle.low
top    = candle.high
```

V1 Root 단계에서:

```text
body-only
open-to-low
open-to-high
50% OB
```

등으로 임의 축소하지 않는다.

Root 자체의 source precision은
causal LTF refinement가 담당한다.

최초 포지션의 실제 entry / SL geometry는
후속 M1 CHoCH displacement FVG 규칙이 담당한다.

### 4.12 Occurrence and Availability

Classification: D

Root candle 자체의 발생 시점과
Root라는 의미가 확정되는 시점을 분리한다.

```text
occurred_at
= origin candle time

available_at
= linked meaningful structure event confirmation time
```

Structure delivery가 확인되기 전에
해당 candle을 이미 Root OB였던 것처럼 사용할 수 없다.

이 규칙은 historical replay에서 look-ahead를 방지한다.

### 4.13 Scenario Direction Alignment

Classification: D

Root OB는 frozen scenario direction과 objective를 설명해야 한다.

예:

```text
scenario:
bullish continuation

objective:
upper external liquidity
```

이면 bullish Root OB만 해당 scenario source 후보가 된다.

반대 방향 OB가 기술적으로 valid하더라도
현재 scenario의 Root로 사용하지 않는다.

### 4.14 Freshness and Lifecycle

Classification: D

Root OB는 scenario planning 시점에 active해야 한다.

Minimum lifecycle state:

```text
FRESH
TOUCHED
PARTIALLY_MITIGATED
CONSUMED
STRUCTURALLY_INVALIDATED
```

단순 첫 touch만으로 Root를 폐기하지 않는다.

임의의:

```text
touch_count >= N
age >= N bars
ATR decay
quality decay
```

규칙은 V1에 넣지 않는다.

### 4.15 Full Consumption

Classification: D

Bullish Root:

```text
price fully delivers through Root distal
```

즉 Root 전체가 완전히 관통되면 consumed 처리한다.

Bearish Root도 반대로 동일하다.

기존 zone lifecycle infrastructure를 재사용할 수 있으나,
Root lifecycle과 FVG partial-fill semantics를 혼동하지 않는다.

Consumed Root는 신규 first-position source로 재사용하지 않는다.

### 4.16 Structural Invalidation

Classification: D

Root가 속한 causal structure premise가 무효화되면
Root 자체도 source authority를 잃는다.

즉 candle zone이 물리적으로 남아 있더라도:

```text
owner invalidated
scenario scope invalidated
causal structure invalidated
```

이면 Root는 active source가 아니다.

정확한 invalidation event는
Market Structure / Scenario Scope state와 연결한다.

### 4.17 Multiple Root Candidates

Classification: D principle

여러 candidate가 있을 때 다음 기준으로 임의 선택하지 않는다.

```text
가장 좁은 OB
현재가에 가장 가까운 OB
가장 큰 RR을 만드는 OB
가장 최근 OB
```

Nested causal relation이 명확하면 parent-child lineage로 유지한다.

비교할 수 없는 서로 다른 Root candidate가
동일 scenario ownership을 주장하고
deterministic하게 causal owner를 선택할 수 없다면:

```text
NO TRADE / AMBIGUOUS ROOT
```

로 처리한다.

### 4.18 Explicit V1 Exclusions

Root source selection에서 사용하지 않는다.

```text
simple latest opposite candle
nearest opposite candle
FVG overlap alone
HTF FVG as source
M1 reaction-based retrospective HTF selection
ATR displacement score
body-size score
touch-count score
age-decay score
RR-based Root selection
AI-selected Root
```

### 4.19 Required Root Object

Minimum state:

```text
id

timeframe:
    H1
    M30
    M15

direction:
    LONG
    SHORT

origin_index
occurred_at
available_at

bottom
top

origin_wave_id
meaningful_swing_id
linked_structure_event_id

scenario_owner_id
objective_family_id

state:
    FRESH
    TOUCHED
    PARTIALLY_MITIGATED
    CONSUMED
    STRUCTURALLY_INVALIDATED

first_touch_at
consumed_at
invalidated_at
```

Implementation에서 모든 field가 즉시 필요하지 않더라도
causal ownership과 replay 검증에 필요한 식별자를 보존한다.

### 4.20 V1 Root Protocol Summary

LONG:

```text
bullish scenario/objective frozen
        ↓
meaningful HTF low/swing context
        ↓
swing-origin causal window
        ↓
last bearish candle inside that window
        ↓
same bullish directional leg
        ↓
meaningful high body-close break
        ↓
Root available
        ↓
Root still fresh / structurally valid
        ↓
search causal LTF child
```

SHORT:

```text
bearish scenario/objective frozen
        ↓
meaningful HTF high/swing context
        ↓
swing-origin causal window
        ↓
last bullish candle inside that window
        ↓
same bearish directional leg
        ↓
meaningful low body-close break
        ↓
Root available
        ↓
Root still fresh / structurally valid
        ↓
search causal LTF child
```

---


## 5. Causal LTF OB Refinement

Status: FROZEN FOR V1

Primary authority:
- `AGENTS.md`

Primary implementation reference:
- `mentor_engine/planner.py`
- `mentor_engine/zones.py`

Secondary reference:
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`

### 5.1 Purpose

HTF Root OB가 확정됐다고 해서
그 넓은 Root candle 전체를 바로 precision execution source로 사용하지 않는다.

Refinement의 목적은:

```text
상위 timeframe에서 본 동일한 원인 사건을
더 낮은 timeframe에서 causal하게 다시 확인
```

하는 것이다.

예:

```text
H1 Root
→ M30 causal child
→ M15 causal child
→ M5 causal child
```

각 child는 단순히 parent 내부에 있는 작은 OB가 아니라
같은 price event와 같은 displacement를 설명해야 한다.

### 5.2 Minimum One Child Requirement

Classification: D

최초 position baseline은
최소 하나의 valid lower-timeframe causal child를 요구한다.

```text
HTF Root only
→ no first-position authorization
```

예:

```text
H1 Root
→ no valid M30/M15/M5 child
→ NO TRADE
```

또는:

```text
M30 Root
→ valid M15 child
→ refinement requirement satisfied
```

Root 전체를 바로 M1 trigger source로 사용하는 것은
V1 baseline protocol이 아니다.

### 5.3 Allowed Refinement Timeframes

Classification: D

Root timeframes:

```text
H1
M30
M15
```

Refinement timeframes:

```text
M30
M15
M5
```

Child는 반드시 parent보다 더 낮은 timeframe이어야 한다.

Examples:

```text
H1
→ M30
→ M15
→ M5
```

```text
H1
→ M15
```

```text
M30
→ M15
→ M5
```

모든 중간 timeframe에 child가 반드시 존재할 필요는 없다.

M1은 HTF-to-LTF source refinement에 포함하지 않는다.

M1은 이후:

```text
sweep
CHoCH
CHoCH displacement FVG
entry execution
```

를 담당한다.

### 5.4 Same Direction

Classification: D

Child OB는 parent와 동일 방향이어야 한다.

```text
bullish parent
→ bullish child only

bearish parent
→ bearish child only
```

반대 방향 lower-TF OB는 correction structure일 수 있으나
parent source refinement로 사용하지 않는다.

### 5.5 Recursive Causal OB Logic

Classification: D for V1

Child OB도 Root OB와 같은 causal logic을 축소 적용한다.

Valid child는:

```text
lower-TF meaningful swing-origin context
+
last opposite candle inside that origin window
+
same causal lower-TF directional leg
+
meaningful lower-TF structure body-break
```

을 모두 만족해야 한다.

즉:

```text
parent 안에 있는 작은 반대색 candle
```

이라는 이유만으로 child가 되지 않는다.

Bullish child example:

```text
meaningful lower-TF low
        ↓
last bearish candle in origin window
        ↓
bullish displacement
        ↓
meaningful lower-TF high body-break
```

Bearish child는 반대다.

### 5.6 Same Price Event

Classification: D

Parent와 child는 같은 가격 사건을 설명해야 한다.

Child origin은 parent의 causal swing-origin window 안에 있어야 한다.

Required time relation:

```text
parent origin
<= child origin
<= child structure confirmation
<= parent linked structure confirmation
```

Parent의 structure delivery가 완전히 끝난 뒤
나중에 생긴 lower-TF OB는
기존 parent의 refinement로 연결하지 않는다.

그것은 별도의 continuation source 후보일 수 있다.

### 5.7 Same Displacement Ownership

Classification: D

Price overlap만으로 parent-child 관계를 만들지 않는다.

Child의 structure delivery는
parent displacement가 진행 중인 동일 directional delivery chain에 속해야 한다.

즉:

```text
same direction
+
same causal origin window
+
same directional delivery chain
```

을 만족해야 한다.

금지:

```text
parent 안에 가격이 겹치는 unrelated M5 OB
→ child 승격
```

### 5.8 Price Containment

Classification: D-compatible

가장 명확한 refinement는:

```text
parent.bottom <= child.bottom
AND
child.top <= parent.top
```

이다.

Full containment를 우선적으로 인정한다.

그러나 multi-timeframe aggregation 차이 때문에
같은 causal event의 lower-TF child가 parent 경계를 일부 벗어날 수 있다.

이 경우 고정 point / ATR tolerance를 사용하지 않는다.

### 5.9 Event-Defined Immediate Adjacency

Classification: D for V1 protocol

Parent boundary를 일부 벗어난 child는
다음 causal 조건이 모두 성립할 때만 허용한다.

```text
same parent swing-origin lower-TF bar sequence
+
same directional displacement
+
same structure-delivery ownership
+
child structure confirmation inside parent event window
```

즉:

```text
가격이 3포인트 이내라서
ATR의 0.2배 이내라서
```

같은 거리 기반 adjacency는 사용하지 않는다.

V1에서 adjacency는 가격 거리가 아니라
event lineage로 정의한다.

### 5.10 Child Structure Delivery Requirement

Classification: D

Child도 자체 lower-timeframe structure delivery를 만들어야 한다.

Valid bullish child:

```text
lower-TF origin
→ bullish directional leg
→ meaningful lower-TF high body-close break
```

Valid bearish child:

```text
lower-TF origin
→ bearish directional leg
→ meaningful lower-TF low body-close break
```

Wick-only break는 child confirmation이 아니다.

Structure delivery가 없는 lower-TF opposite candle은
refinement source가 아니다.

### 5.11 Child Availability

Classification: D

Child candle의 발생 시점과
causal child로 사용할 수 있게 된 시점을 분리한다.

```text
occurred_at
= child origin candle time

available_at
= child linked structure delivery confirmation
```

Child는 `available_at` 이전에
refined source로 사용할 수 없다.

### 5.12 Refinement Is Not Forced to M5

Classification: D

Refinement는 가능한 가장 낮은 timeframe까지
무조건 내려가는 과정이 아니다.

목적은:

```text
lowest timeframe
```

이 아니라:

```text
deepest unambiguous causal child
```

이다.

Example:

```text
H1 Root
→ M30 valid
→ M15 valid
→ M5 ambiguous
```

이면 final refined source:

```text
M15
```

이다.

M5의 가장 좁은 candidate를 임의 선택하지 않는다.

### 5.13 Ambiguity Handling

Classification: D

동일 parent 안에 비교 불가능한 child candidates가 여러 개 존재하고
causal ownership을 deterministic하게 구분할 수 없으면:

```text
nearest child
narrowest child
newest child
best RR child
```

기준으로 선택하지 않는다.

#### Case A — 이미 상위 child가 확정된 경우

```text
H1
→ M30 valid
→ M15 ambiguous
```

이면:

```text
M30을 final refined source로 유지
```

한다.

#### Case B — 첫 child 단계부터 ambiguous

```text
H1 Root
→ M30/M15 child를 하나도 확정할 수 없음
```

이면:

```text
NO TRADE
```

이다.

이유:

V1은 최소 하나의 causal lower-TF child를 요구한다.

### 5.14 Final Refined Source

Classification: D

Ambiguity 없이 causal lineage가 유지되는
가장 깊은 child가 final refined source다.

Final child는:

price contact zone
trigger-location authority
source/context invalidation reference

를 담당한다.

최초 포지션의 실제 entry와 기본 SL geometry는
후속 M1 CHoCH displacement FVG 규칙이 담당한다.

단:

더 좁아서 선택

하는 것이 아니라:

같은 원인이 더 낮은 TF에서도 명확해서 선택

하는 것이다.

### 5.15 Lineage Freeze Before M1

Classification: D

Final causal child와 parent-child lineage는
M1 trigger 관찰 전에 확정되어야 한다.

Required order:

```text
objective frozen
→ map frozen
→ HTF Root frozen
→ causal refinement lineage frozen
→ final refined source frozen
→ source contact
→ liquidity sweep
→ M1 CHoCH
```

금지:

```text
M1 CHoCH 발견
→ 그 반응에 잘 맞는 M5 OB 선택
→ 그 M5 OB와 겹치는 M15/H1 OB를 사후 연결
```

이는 retrospective fitting으로 취급한다.

### 5.16 Source Contact

Classification: D concept

Final refined source는 M1 trigger를 보기 전에 존재한다.

Price가 final child bounds와 실제로 교차하면
source contact event를 기록할 수 있다.

```text
bar.high >= child.bottom
AND
bar.low <= child.top
```

단, source contact 자체는 trade trigger가 아니다.

Source contact 이후에만
해당 scenario의 M1 sweep / CHoCH search를 활성화한다.

Source Contact의 세부 event contract는
다음 `Source Contact + Mature Sweep` 단계에서 확정한다.

### 5.17 Child Lifecycle

Classification: D

Child state는 최소:

```text
FRESH
TOUCHED
PARTIALLY_MITIGATED
CONSUMED
STRUCTURALLY_INVALIDATED
```

를 유지한다.

단순 touch만으로 child를 즉시 invalid 처리하지 않는다.

V1에서는:

```text
N-touch expiry
N-bar expiry
age score
quality score
```

를 사용하지 않는다.

### 5.18 Parent Invalidation Propagation

Classification: D

Ownership은 상위에서 하위로 흐른다.

```text
Parent Root invalidated
→ all descendants invalidated
```

상위 owner가 사라지면
lower-TF child가 차트상 untouched여도
source authority를 잃는다.

### 5.19 Child Consumption

Classification: D

Final child가 완전히 소비되면
그 child를 사용하는 execution lane은 종료된다.

```text
final child consumed
→ current lane invalid
```

다만 child consumption이
항상 HTF Root 자체의 구조적 invalidation을 뜻하는 것은 아니다.

Root가 살아 있다면
향후 새로운 causal child가 형성될 가능성은 있다.

하지만 같은 consumed child를
재사용해서 새 M1 trigger를 기다리지는 않는다.

### 5.20 Parent-Child Identity

Classification: D

각 child는 자신의 direct parent를 명시적으로 기록한다.

Required lineage example:

```text
H1 Root ID
→ M30 Child ID
→ M15 Child ID
→ M5 Child ID
```

중간 timeframe을 건너뛰는 경우:

```text
H1 Root ID
→ M15 Child ID
```

도 허용한다.

각 child는 최소:

```text
parent_zone_id
root_zone_id
linked_structure_event_id
origin_wave_id
```

를 보존한다.

### 5.21 Distance Is Not Authority

Classification: D

Distance는 후보 탐색 최적화에 사용할 수 있으나
causal child authorization에는 사용할 수 없다.

```text
distance
-> enumeration optimization only

causal lineage
-> authorization
```

현재 `planner.py`의 nearest-family 탐색 성격은
후보 enumeration으로만 참고한다.

다음은 child 권한을 부여하지 않는다.

```text
closest lower-TF OB
smallest lower-TF OB
best RR lower-TF OB
```

### 5.22 Required Refinement Object

Minimum lineage state:

```text
root_zone_id

path:
    [root, child1, child2, ...]

final_child_id

for each child:
    id
    timeframe
    direction
    parent_zone_id
    root_zone_id

    origin_wave_id
    linked_structure_event_id

    occurred_at
    available_at

    bottom
    top

    containment_type:
        CONTAINED
        EVENT_ADJACENT

    state:
        FRESH
        TOUCHED
        PARTIALLY_MITIGATED
        CONSUMED
        STRUCTURALLY_INVALIDATED
```

### 5.23 Explicit V1 Exclusions

Causal refinement에서 사용하지 않는다.

```text
price overlap alone
nearest-zone selection
narrowest-zone selection
RR-based refinement
fixed point adjacency tolerance
ATR adjacency tolerance
force refinement to M5
M1 retrospective refinement
AI-selected child
weighted child quality score
```

### 5.24 V1 Refinement Protocol Summary

LONG:

```text
valid bullish HTF Root
        ↓
project Root causal origin event to lower TF
        ↓
find meaningful lower-TF origin
        ↓
last bearish candle inside child origin window
        ↓
bullish child displacement
        ↓
meaningful lower-TF body-break
        ↓
verify same event / same displacement / time causality
        ↓
link as child
        ↓
repeat on lower TF while unambiguous
        ↓
freeze deepest unambiguous child
        ↓
wait for source contact
```

SHORT는 반대다.

---


## 6. Source Contact + Mature Sweep

Status: FROZEN FOR V1

Primary authority:
- `AGENTS.md`

Primary implementation reference:
- `mentor_engine/liquidity.py`

Secondary references:
- `research/mentor-youtube/MENTOR_MINIMAL_METHOD.md`
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`

### 6.1 Purpose

이 단계의 목적은 전역적으로 탐지된 모든 liquidity sweep 중
현재 frozen scenario와 final refined source에 실제로 연결되는 sweep만
M1 trigger chain에 사용할 수 있도록 제한하는 것이다.

Liquidity detector와 trade authorization은 분리한다.

```text
GLOBAL LIQUIDITY DETECTION
        ↓
scenario-specific authorization
        ↓
AUTHORIZED SWEEP
```

`liquidity.py`가 sweep event를 만들었다는 사실만으로
현재 거래 setup의 sweep condition이 충족되는 것은 아니다.

### 6.2 Required Precondition

Classification: D

Source Contact / Sweep 단계에 들어오기 전에
다음이 모두 frozen 상태여야 한다.

```text
objective
scenario scope
map owner
HTF Root OB
causal refinement lineage
final refined source
source invalidation geometry
```

이 중 하나라도 없으면
M1 sweep authorization을 시작하지 않는다.

### 6.3 Source Contact

Classification: D for V1

Final refined source와 closed bar range가
실제로 최초 교차하면 source contact로 기록한다.

Condition:

```text
bar.high >= source.bottom
AND
bar.low <= source.top
```

단:

```text
bar.available_at > source.available_at
```

인 causal bar만 contact 후보가 된다.

Source가 final refined source로 확정되기 전에
과거에 이미 지나간 가격 움직임을
사후적으로 source contact라고 소급하지 않는다.

### 6.4 Source Contact Is a Gate, Not a Signal

Classification: D

Source contact는:

```text
entry
sweep
CHoCH
```

가 아니다.

Source contact의 의미는:

```text
이제부터 현재 scenario의 M1 trigger chain을 관찰할 수 있다.
```

뿐이다.

따라서 V1은 refined OB touch만으로
첫 position limit/market entry를 실행하지 않는다.

Required chain remains:

source contact
→ mature liquidity sweep
→ meaningful M1 CHoCH
→ same sweep-to-CHoCH causal leg의 fresh same-direction FVG
→ widest valid FVG selection
→ first retest
→ entry

### 6.5 Trigger Search Activation

Classification: D

Source contact 이전:

```text
trigger_search_enabled = false
```

Source contact 이후:

```text
sweep_search_enabled = true
```

단, CHoCH authorization은
valid sweep이 확정된 이후에만 활성화한다.

```text
source contact
→ sweep confirmed
→ CHoCH search enabled
```

Source contact 이전에 발생한 M1 sweep/CHoCH를
현재 scenario에 끌어와 사용하지 않는다.

### 6.6 Direction-Compatible Sweep

Classification: D

LONG scenario:

```text
required sweep side = LOW
```

즉 sell-side liquidity sweep이 필요하다.

SHORT scenario:

```text
required sweep side = HIGH
```

즉 buy-side liquidity sweep이 필요하다.

반대 side liquidity sweep은
현재 first-position trigger chain authorization이 아니다.

### 6.7 Eligible Sweep Liquidity Families

Classification: D

V1 trigger-authorizing sweep에는
현재 Liquidity V1에서 허용한 family만 사용한다.

```text
EXTERNAL_SWING
DEFENDED_RANGE_EDGE
STRUCTURAL_REACTION
```

V1에서 제외:

```text
TRENDLINE_CLUSTER
simple recent pivot
arbitrary local high/low
session high/low by itself
round number
```

Detector 또는 legacy code가 해당 event를 생성해도
V1 trade authorization에는 사용하지 않는다.

### 6.8 Mature Liquidity Definition

Classification: D for V1

V1에서 maturity는 arbitrary age가 아니라
causal pre-existence와 structural eligibility로 정의한다.

Required:

```text
eligible liquidity family
+
liquidity already available before source-contact bar begins
+
not already consumed
```

현재 first-position trigger에 사용할 liquidity는:

```text
liquidity.available_at
<
source_contact_bar_open
```

이어야 한다.

즉 source contact candle이 진행되는 동안 처음 확정된 liquidity는
같은 first-position trigger의 required pool이 될 수 없다.

### 6.9 No Arbitrary Liquidity Age Threshold

Classification: D

V1은 다음을 사용하지 않는다.

```text
minimum 2 bars old
minimum 3 bars old
minimum N minutes old
ATR-distance maturity
age score
maturity score
```

이유:

Liquidity family 자체가 이미 구조적으로 의미 있는 stop pool만
보수적으로 허용하기 때문이다.

V1 maturity의 핵심은:

```text
pre-existing
+
eligible
+
unconsumed
```

이다.

### 6.10 Pre-Contact Sweep Is Not Reused

Classification: D

Final refined source가 실제 접촉되기 전에
완료된 sweep은 현재 first-position trigger chain에 사용하지 않는다.

금지:

```text
old sweep
→ later source contact
→ old sweep reused
→ CHoCH
```

Required order:

```text
source contact
→ authorized sweep
→ CHoCH
```

이 규칙은 unrelated earlier liquidity event를
사후적으로 current source에 연결하는 것을 방지한다.

### 6.11 Same-Bar Contact + Sweep

Classification: D

Source contact와 liquidity sweep이
같은 closed M1 bar에서 발생하는 것은 허용한다.

Example LONG:

```text
M1 bar enters bullish refined source
+
same bar wicks below pre-existing sell-side liquidity
+
same bar closes back above liquidity boundary
```

이면:

```text
source contact
+
authorized sell-side sweep
```

을 동시에 기록할 수 있다.

단:

```text
liquidity itself must pre-exist the source-contact bar
```

여야 한다.

즉:

```text
same-bar contact + sweep
→ allowed

same-bar liquidity creation + sweep
→ forbidden
```

이다.

### 6.12 Sweep Must Occur at the Final Refined Source

Classification: D for V1

V1 trigger-authorizing sweep bar는
final refined source와 실제로 교차해야 한다.

```text
sweep_bar.high >= source.bottom
AND
sweep_bar.low <= source.top
```

즉 source를 과거에 한 번 touch한 뒤
가격이 source와 멀어진 곳에서 나중에 발생한 sweep을
원래 setup의 trigger로 연결하지 않는다.

V1에서는:

```text
sweep bar intersects final refined source
```

를 required causal condition으로 사용한다.

### 6.13 Sweep Extreme May Extend Beyond Source

Classification: D

Sweep bar가 final source와 교차해야 하지만
sweep extreme 자체가 source bounds 안에 있을 필요는 없다.

LONG example:

```text
bullish refined source
        ↓
price enters source
        ↓
wick extends below source distal
        ↓
pre-existing sell-side liquidity swept
        ↓
close recovers
```

은 유효할 수 있다.

즉 source는 reaction context이고
liquidity sweep extreme은 source 바깥까지 확장될 수 있다.

### 6.14 Physical Sweep Condition

Classification: D

Sweep은 pre-existing eligible liquidity의 outer boundary를
실제로 최소 one valid tick 이상 관통하고
같은 closed bar에서 recovery해야 한다.

#### HIGH-side liquidity

```text
bar.high >= pool.top + one_tick
AND
bar.close <= pool.top
```

#### LOW-side liquidity

```text
bar.low <= pool.bottom - one_tick
AND
bar.close >= pool.bottom
```

여기서 `one_tick`은
해당 symbol의 실제 valid tick size를 사용한다.

별도 ATR 또는 percentage penetration threshold는 사용하지 않는다.

### 6.15 Same-Bar Recovery Only

Classification: D for V1

V1 physical sweep은:

```text
penetration
+
recovery
```

가 같은 closed bar 안에서 완료되어야 한다.

Example excluded from V1:

```text
bar 1:
liquidity 아래 body close

bar 2:
다시 위로 reclaim
```

이것은 V1 sweep으로 취급하지 않는다.

Multi-bar reclaim은 향후 별도 immutable research variant로 검토할 수 있다.

### 6.16 Body Delivery Is Not Sweep

Classification: D

Liquidity outer edge를 body close로 directional하게 통과하면
sweep이 아니라 BODY_DELIVERY다.

HIGH-side:

```text
close > pool.top
→ BODY_DELIVERY
```

LOW-side:

```text
close < pool.bottom
→ BODY_DELIVERY
```

해당 pool은 consumed되며
현재 trigger chain의 required sweep으로 사용할 수 없다.

### 6.17 One-Tick Minimum Penetration

Classification: D

Sweep penetration은 실제 symbol tick size 기준으로
최소 한 tick 이상 outer boundary를 넘어야 한다.

단순 equality:

```text
high == pool.top
low == pool.bottom
```

은 sweep이 아니다.

V1은 다음을 사용하지 않는다.

```text
ATR penetration multiplier
fixed arbitrary point penetration
percentage penetration
sweep strength score
```

### 6.18 Source-Generated Liquidity Cannot Trigger the Same First Position

Classification: D

현재 final refined source 접촉 이후
그 reaction 자체가 새 swing/liquidity를 만들 수 있다.

하지만 그 새 liquidity를
동일 first-position trigger의 required pre-existing liquidity로 사용할 수 없다.

금지:

```text
source contact
→ reaction low/high generated
→ that new liquidity declared mature
→ same setup sweep
```

현재 setup의 required pool은
source-contact bar 이전부터 이미 available해야 한다.

새 reaction liquidity는
향후 별도 scenario / continuation context에서 사용할 수 있다.

### 6.19 Multiple Pools Swept by One Bar

Classification: D

하나의 sweep bar가 여러 eligible pre-existing pools를
동시에 관통하고 recovery할 수 있다.

예:

```text
structural reaction liquidity
+
defended range edge
+
external swing
```

이 동일 wick에 의해 sweep될 수 있다.

이 경우:

```text
모든 consumed eligible pool을 event ledger에 기록
```

한다.

Scenario authorization은:

```text
direction-compatible
eligible
pre-existing
unconsumed
pool
at least one swept
```

이면 충족한다.

Best-pool score를 만들지 않는다.

### 6.20 Sweep Availability

Classification: D

Sweep은 해당 candle이 close된 뒤에만 확정된다.

```text
sweep.occurred_at
= sweep bar time

sweep.available_at
= sweep bar close
```

진행 중 candle의 wick만 보고
미리 sweep을 확정하지 않는다.

### 6.21 CHoCH Search Activation

Classification: D

Valid authorized sweep이 closed-bar 기준으로 확정된 이후:

```text
trigger_search_enabled = true
```

가 된다.

이 시점부터 current scenario와 연결된
meaningful M1 CHoCH를 찾는다.

Sweep이 확정되기 전에
향후 CHoCH event를 사후적으로 연결하지 않는다.

같은 bar가 sweep과 CHoCH를 동시에 수행할 수 있는지는
다음 `M1 Meaningful CHoCH` specification에서 별도로 결정한다.

### 6.22 Scenario-Specific Sweep State

각 scenario는 최소 다음 state를 보존한다.

```text
scenario_id

final_source_id

source_contacted
source_contact_at
source_contact_bar

eligible_pool_ids_at_contact

authorized_sweep_ids
sweep_confirmed_at

sweep_search_enabled
trigger_search_enabled
```

이 state는 audit 시 다음을 설명할 수 있어야 한다.

```text
어떤 source에 닿았는가?
어떤 liquidity가 그 전에 이미 존재했는가?
어떤 pool이 sweep됐는가?
왜 그 sweep이 현재 scenario에 허용됐는가?
언제부터 CHoCH를 찾기 시작했는가?
```

### 6.23 Global Detection vs Scenario Authorization

Classification: D

기존 liquidity detector는
전역 liquidity/sweep event discovery 용도로 사용할 수 있다.

그러나 V1 trade authority는 별도 filter를 통과해야 한다.

```text
GLOBAL SWEEP EVENT
        ↓
V1 family eligible?
        ↓
correct side?
        ↓
available before source contact?
        ↓
unconsumed before sweep?
        ↓
sweep bar intersects final source?
        ↓
same-bar penetration + recovery?
        ↓
attached to frozen scenario?
        ↓
AUTHORIZED SWEEP
```

Distance, quality score, nearest-pool rule은
authorization에 사용하지 않는다.

### 6.24 Explicit V1 Exclusions

다음을 first-position sweep authorization에 사용하지 않는다.

```text
pre-contact sweep reuse
same-bar liquidity creation + sweep
micro-pivot sweep
trendline liquidity sweep
multi-bar reclaim sweep
body-delivery-as-sweep
ATR penetration filter
liquidity age threshold
sweep quality score
nearest-pool fallback
AI-selected sweep
source-distant later sweep
```

### 6.25 V1 Source Contact + Sweep Summary

LONG:

```text
bullish final refined source frozen
        ↓
eligible pre-existing sell-side liquidity snapshot
        ↓
price intersects final source
        ↓
same bar or later source-intersecting bar
penetrates eligible LOW pool by >= 1 tick
        ↓
same bar closes back at/above pool boundary
        ↓
pool consumed as SWEEP
        ↓
scenario authorized_sweep recorded
        ↓
M1 CHoCH search enabled
```

SHORT:

```text
bearish final refined source frozen
        ↓
eligible pre-existing buy-side liquidity snapshot
        ↓
price intersects final source
        ↓
same bar or later source-intersecting bar
penetrates eligible HIGH pool by >= 1 tick
        ↓
same bar closes back at/below pool boundary
        ↓
pool consumed as SWEEP
        ↓
scenario authorized_sweep recorded
        ↓
M1 CHoCH search enabled
```

---


## 7. M1 Meaningful CHoCH

Status: FROZEN FOR V1

Primary authority:
- `AGENTS.md`

Primary implementation reference:
- `mentor_engine/structure.py`

Secondary references:
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`
- `research/mentor-youtube/MENTOR_MINIMAL_METHOD.md`

### 7.1 Purpose

M1 CHoCH의 역할은 새로운 HTF scenario를 만드는 것이 아니다.

이미 사전에 frozen된:

```text
objective
map owner
HTF Root
causal LTF lineage
final refined source
```

가 실제 source reaction에서 실행 가능한 방향으로 반응하고 있는지를
M1 structure로 확인하는 것이다.

따라서:

```text
M1 CHoCH
= execution confirmation
```

이며:

```text
M1 CHoCH
≠ HTF directional authority
```

이다.

### 7.2 Required Causal Order

Classification: D

V1 first-position trigger는 다음 순서를 요구한다.

final source frozen
→ source contact
→ authorized mature liquidity sweep
→ meaningful M1 CHoCH
→ same sweep-to-CHoCH causal leg의 fresh same-direction FVG
→ widest valid FVG selection
→ first retest
→ entry

앞 단계가 없으면
뒤 단계의 M1 structure event 또는 execution event가 아무리 선명해도
현재 scenario의 trade authority가 아니다.

### 7.3 Meaningful CHoCH Reference

Classification: D

Meaningful CHoCH는 최근 아무 pivot을 깨는 사건이 아니다.

CHoCH reference는:

```text
final source로 들어오던 M1 correction을
실제로 지배하던 protected swing
```

이어야 한다.

LONG scenario:

```text
bearish M1 correction
→ current protected HIGH
→ bullish body-close break
```

SHORT scenario:

```text
bullish M1 correction
→ current protected LOW
→ bearish body-close break
```

을 요구한다.

### 7.4 Arbitrary Pivot Is Not CHoCH Authority

Classification: D

다음 기준으로 CHoCH reference를 선택하지 않는다.

```text
nearest pivot
latest tiny pivot
smallest swing
best RR swing
visually convenient swing
```

CHoCH reference는 global M1 structure detector가
현재 correction trend에서 실제 protected structure로 관리하던 swing이어야 한다.

### 7.5 Reference Freeze at Authorized Sweep

Classification: D

Authorized sweep이 확정될 때
현재 M1 correction structure의 protected swing을 snapshot한다.

LONG:

```text
M1 trend before sweep = bearish
reference = current protected HIGH
```

SHORT:

```text
M1 trend before sweep = bullish
reference = current protected LOW
```

이 reference를:

```text
choch_reference_swing
```

으로 freeze한다.

### 7.6 Reference Must Pre-Exist Sweep

Classification: D

CHoCH reference swing은 sweep event보다 먼저
이미 확정되어 있어야 한다.

Required:

```text
reference.available_at
<= sweep_bar_open
```

Sweep candle 또는 이후 price action을 보고
새로운 쉬운 pivot을 reference로 사후 선택하지 않는다.

### 7.7 No Protected Reference Means No Trigger

Classification: D for V1

Authorized sweep 시점에
scenario 방향과 반대되는 M1 correction trend 및
그 trend의 protected swing이 존재하지 않으면:

```text
NO CHOCH AUTHORIZATION
```

이다.

예 LONG:

```text
source contact
→ sell-side sweep
→ M1 bearish correction protected HIGH 없음
```

이면 해당 sweep chain으로 거래하지 않는다.

최근 임의 pivot 또는 `INITIAL_BOS`를
CHoCH reference의 fallback으로 사용하지 않는다.

### 7.8 Direction Compatibility

Classification: D

LONG scenario:

```text
authorized sell-side sweep
→ bullish M1 CHoCH only
```

SHORT scenario:

```text
authorized buy-side sweep
→ bearish M1 CHoCH only
```

반대 방향 CHoCH는
현재 frozen scenario의 execution confirmation이 아니다.

### 7.9 Body-Close Break

Classification: Authority / Frozen

Meaningful CHoCH는 body close로
frozen reference level을 실제 돌파해야 한다.

LONG:

```text
M1 close > reference_high
```

SHORT:

```text
M1 close < reference_low
```

다음은 CHoCH가 아니다.

```text
wick-only breach
close == reference level
```

### 7.10 No Arbitrary Break-Strength Threshold

Classification: D

Body close break가 성립하면
별도의 임의 break-strength threshold를 추가하지 않는다.

사용하지 않는다.

```text
ATR displacement threshold
N-point close buffer
percentage break filter
CHoCH strength score
```

Symbol price/tick normalization은 적용하지만
추가 trading threshold로 사용하지 않는다.

### 7.11 Same-Bar Sweep + CHoCH Is Excluded in V1

Classification: D for causal replay

V1에서는 authorized sweep과 CHoCH가
동일 M1 candle에서 확정되는 것을 first-position trigger로 사용하지 않는다.

Required:

```text
choch_bar.index > sweep_bar.index
```

이유:

OHLC bar만으로 동일 candle 내부에서:

```text
liquidity sweep
→ recovery
→ protected swing break
```

순서가 실제로 발생했는지 확인할 수 없기 때문이다.

Same-bar sweep + CHoCH는
향후 MT5 real-tick ordering을 사용하는
별도 immutable research variant에서 검토한다.

### 7.12 CHoCH Bar Need Not Intersect Source

Classification: D

Authorized sweep bar는 V1에서
final refined source와 교차해야 한다.

하지만 이후 CHoCH bar까지
source와 교차할 필요는 없다.

유효 causal relation:

```text
authorized sweep at source
→ later body-close break of frozen protected swing
```

이다.

강한 reaction displacement가 source를 빠르게 벗어난 뒤
CHoCH를 만드는 것을 허용한다.

### 7.13 No Fixed CHoCH Timeout

Classification: D

Sweep 이후 CHoCH까지:

```text
N bars
N minutes
```

같은 고정 timeout을 두지 않는다.

대신 실제 causal invalidation event로
trigger chain을 종료한다.

### 7.14 Trigger-Chain Invalidation Before CHoCH

Classification: D

CHoCH가 확정되기 전에 다음 중 하나가 발생하면
현재 trigger chain은 종료된다.

```text
final refined source structurally invalidated
HTF Root / parent owner invalidated
frozen objective delivered before entry
final child fully consumed
scenario map owner invalidated
```

시간 경과만으로 자동 폐기하지 않는다.

### 7.15 Multiple Authorized Sweeps Before CHoCH

Classification: D

CHoCH 전에 새로운 direction-compatible authorized sweep이
같은 valid source에서 발생할 수 있다.

각 sweep은 독립 trigger chain으로 기록한다.

```text
trigger_chain_A
trigger_chain_B
```

새 sweep B가 발생하면
B 시점의 valid M1 correction protected swing을
새 reference로 snapshot할 수 있다.

이는 새로운 physical sweep event가 발생했기 때문에
retrospective fitting이 아니다.

과거 chain A의 기록은 삭제하지 않는다.

Execution authorization에는
현재 유효한 latest trigger chain을 사용한다.

### 7.16 M5 Correction Context

Classification: Authority-compatible

M5는:

```text
correction context / ownership
```

을 담당한다.

M1은:

```text
execution confirmation
```

을 담당한다.

M5는 현재 M1 trigger가
final source로 들어오는 expected correction/reaction에 속하는지
context를 제공할 수 있다.

그러나 V1은 다음을 추가 요구하지 않는다.

```text
M5 CHoCH mandatory
M5 BOS mandatory
M5 candle-colour confirmation
```

M5 단독 event는 first-position order를 authorize하지 않는다.

### 7.17 M1 CHoCH Does Not Change HTF Owner

Classification: Authority / Frozen

M1 meaningful CHoCH는
현재 frozen scenario scope 안에서만 의미가 있다.

예:

```text
INTERNAL_ROTATION LONG
+
bullish M1 CHoCH
```

는:

```text
internal bullish execution reaction confirmed
```

을 의미할 뿐이다.

이것만으로 H1/M30 external structure를
bullish reversal로 변경하지 않는다.

External reversal은 별도로:

```text
H1/M30 protected swing body break
+
new-direction owner confirmation
```

이 필요하다.

### 7.18 CHoCH Validity vs Executable Displacement

Classification: D

Structure event 자체의 meaningful CHoCH validity는:

body close through frozen protected swing

으로 결정한다.

따라서 FVG가 없더라도
meaningful M1 CHoCH structure event 자체는 존재할 수 있다.

그러나 V1 first-position execution authorization에는
추가로 다음이 필요하다.

authorized sweep
+
meaningful M1 CHoCH
+
same sweep-to-CHoCH causal leg 안의
fresh same-direction 3-candle FVG

즉:

meaningful CHoCH + no causal FVG
→ valid CHoCH structure event
→ NO BASE ENTRY

V1은 executable displacement를 판정하기 위해
별도의:

ATR displacement threshold
minimum body size
minimum consecutive directional candle count
displacement quality score

를 추가하지 않는다.

현재 V1에서:

meaningful CHoCH
+
same causal leg의 fresh FVG

를 first-position executable displacement의 최소 증거로 사용한다.

### 7.19 CHoCH Displacement FVG Is Required for Base Entry

Classification: D for V1 first-position execution

FVG는 meaningful CHoCH structure event 자체를 정의하기 위한
필수 조건이 아니다.

그러나 V1 최초 포지션을 실제로 authorize하려면
해당 CHoCH directional displacement가 만든
valid causal FVG가 최소 하나 필요하다.

Initial execution FVG는 반드시:

1. authorized sweep 이후의 causal reaction leg에 속한다.
2. meaningful CHoCH와 같은 방향이다.
3. sweep → CHoCH를 만든 동일 M1 directional leg에 속한다.
4. 주문 authorization 시점에 이미 확정되어 있다.

FVG가 CHoCH candle 자체를 반드시 포함할 필요는 없다.

CHoCH 이전에 같은 sweep-to-CHoCH causal displacement 안에서
형성된 FVG도 candidate가 될 수 있다.

HTF/LTF OB lineage가 누락된 상태에서
FVG만으로 새로운 first-position scenario를 만들지는 않는다.

### 7.20 Additional BOS Is Not Mandatory

Classification: Authority / Frozen

V1 baseline은:

authorized sweep
→ meaningful M1 CHoCH
→ causal displacement FVG
→ FVG retest
→ entry

를 사용한다.

다음은 별도 research variant로 유지한다.

authorized sweep
→ CHoCH
→ additional BOS
→ BOS displacement FVG
→ entry

따라서 second BOS가 없다는 이유만으로
valid V1 CHoCH 또는 valid initial CHoCH-FVG execution을 거부하지 않는다.


### 7.21 INITIAL_BOS Cannot Substitute for CHoCH

Classification: D for V1

현재 `structure.py`에서 trend가 아직 확립되지 않았을 때
생성되는:

```text
INITIAL_BOS
```

는 first-position meaningful CHoCH를 대체할 수 없다.

M1 correction이 directional protected structure를
아직 확립하지 못했다면:

```text
trigger not mature
```

로 취급한다.

### 7.22 Session Discontinuity

Classification: D-compatible

M1 session discontinuity/opening gap 자체를
old protected swing CHoCH로 사용하지 않는다.

큰 session gap 이후:

```text
reset/rebuild M1 execution structure
→ require new protected correction swing
→ require new causal trigger chain
```

을 따른다.

세부 session-gap handling은
Market Structure 최종 통합 감사에서 다시 확인한다.

### 7.23 Global Detection vs Scenario Authorization

Classification: D

기존 `mentor_engine/structure.py`는
global M1 structure event detector로 재사용할 수 있다.

Trade authorization은 별도 scenario layer에서 수행한다.

Required filter:

```text
event.timeframe == M1
event.event_type == CHOCH
event.direction == scenario.direction
event.index > authorized_sweep.index
event.broken_swing_id == frozen_choch_reference_swing_id
scenario still valid
```

즉 global CHoCH event가 존재한다는 사실만으로
trade authority가 생기지 않는다.

### 7.24 Required CHoCH Object

Minimum state:

```text
choch_event_id
scenario_id
trigger_chain_id

direction

source_id
sweep_event_id

reference_swing_id
reference_swing_level
reference_swing_available_at

choch_bar_index
occurred_at
available_at
close_price

break_type = BODY_CLOSE
```

Audit fields:

```text
m1_trend_before
reference_side
reference_rank
source_contact_at
sweep_confirmed_at
```

### 7.25 Explicit V1 Exclusions

다음을 meaningful M1 CHoCH authorization에 사용하지 않는다.

```text
arbitrary recent pivot
nearest pivot
wick-only break
equality break
INITIAL_BOS fallback
same-bar sweep + CHoCH
ATR break threshold
CHoCH quality score
FVG as a requirement to define the CHoCH structure event itself
mandatory second BOS
M5-only trigger
M1 CHoCH as HTF reversal authority
AI-selected CHoCH reference
```

### 7.26 V1 LONG Protocol

```text
LONG scenario frozen
        ↓
bullish final refined source
        ↓
source contact
        ↓
authorized sell-side sweep
        ↓
at sweep:
    M1 correction trend = bearish
    current protected HIGH exists
    protected HIGH already available
        ↓
freeze protected HIGH as CHoCH reference
        ↓
wait for later closed M1 bar
        ↓
M1 close > frozen protected HIGH
        ↓
bullish meaningful CHoCH
        ↓
collect fresh bullish FVGs
belonging to the same sweep-to-CHoCH causal leg
        ↓
if none:
    NO BASE ENTRY
        ↓
if one or more:
    select widest valid FVG
        ↓
wait for first authorized retest
```

### 7.27 V1 SHORT Protocol

```text
SHORT scenario frozen
        ↓
bearish final refined source
        ↓
source contact
        ↓
authorized buy-side sweep
        ↓
at sweep:
    M1 correction trend = bullish
    current protected LOW exists
    protected LOW already available
        ↓
freeze protected LOW as CHoCH reference
        ↓
wait for later closed M1 bar
        ↓
M1 close < frozen protected LOW
        ↓
bearish meaningful CHoCH
        ↓
collect fresh bearish FVGs
belonging to the same sweep-to-CHoCH causal leg
        ↓
if none:
    NO BASE ENTRY
        ↓
if one or more:
    select widest valid FVG
        ↓
wait for first authorized retest
```

---


## 8. CHoCH Displacement FVG + Entry

Status: FROZEN FOR V1 CORE ENTRY RULES

Primary authority:
- `AGENTS.md`

Secondary references:
- `research/mentor-youtube/MENTOR_RULE_CONTRACT.md`
- `research/mentor-youtube/MENTOR_MINIMAL_METHOD.md`

### 8.1 Purpose

V1 최초 포지션의 actual execution zone은
causal M1 execution OB가 아니라
meaningful M1 CHoCH를 전달한 directional displacement의 FVG다.

HTF Root OB와 causal LTF refinement는
scenario source/context authority로 계속 필요하다.

즉:

HTF/LTF OB lineage
≠ actual first-position entry zone

CHoCH displacement FVG
= actual first-position execution zone

### 8.2 Three-Candle FVG Definition

Classification: D

Bullish FVG:

Candle3.low > Candle1.high

Bounds:

bottom = Candle1.high
top = Candle3.low
width = top - bottom

Bearish FVG:

Candle3.high < Candle1.low

Bounds:

bottom = Candle3.high
top = Candle1.low
width = top - bottom

Required:

width > 0

FVG는 Candle 3가 close된 이후에만 available하다.

### 8.3 Causal Execution-FVG Qualification

Classification: D for V1

Initial execution FVG candidate는 반드시:

authorized sweep
→ meaningful CHoCH

를 만든 동일 causal M1 directional leg에 속해야 한다.

LONG:

authorized sell-side sweep
→ bullish causal leg
→ bullish FVG
→ bullish meaningful CHoCH

SHORT:

authorized buy-side sweep
→ bearish causal leg
→ bearish FVG
→ bearish meaningful CHoCH

을 요구한다.

Sweep 이전의 unrelated FVG 또는
CHoCH 이후 별도 delivery leg에서 새로 생긴 FVG를
현재 `INITIAL_CHOCH_FVG` 후보로 사용하지 않는다.

Meaningful CHoCH가 있어도
valid causal FVG가 하나도 없으면:

NO BASE FIRST-POSITION ENTRY

다.

### 8.4 Multiple FVG Selection

Classification: D

같은 authorized sweep → meaningful CHoCH causal displacement 안에
valid FVG가 여러 개 존재하면:

selected_FVG =
argmax(FVG.top - FVG.bottom)

을 사용한다.

즉 가장 가격 폭이 넓은 FVG를 선택한다.

다음 기준은 사용하지 않는다.

nearest FVG
latest FVG
first FVG
closest-to-source FVG
best-RR FVG

Symbol tick normalization 이후에도
최대 width가 정확히 같은 FVG가 둘 이상이면:

AMBIGUOUS_EXECUTION_FVG
→ NO TRADE

로 처리한다.

### 8.5 Retest

Classification: D

Selected FVG와 meaningful CHoCH가 모두 available된 이후
가격이 selected FVG와 처음 교차하면
first retest로 정의한다.

Intersection:

bar.high >= FVG.bottom
AND
bar.low <= FVG.top

FVG 생성 candle 내부의 과거 movement 또는
CHoCH/order authorization 전에 이미 지나간 touch를
사후 retest로 복원하지 않는다.

같은 first-position execution chain에서
두 번째 이후 touch는 재사용하지 않는다.

### 8.6 Entry Price

Classification: D

LONG:

entry = selected bullish FVG.top

SHORT:

entry = selected bearish FVG.bottom

즉 가격이 되돌아올 때 먼저 닿는
FVG near-side boundary에 limit entry를 둔다.

V1 base first-position에서는 사용하지 않는다.

FVG midpoint
50% / CE
causal execution OB retest
market chase
RR-optimized internal FVG price

### 8.7 Required Entry State

Minimum state:

selected_fvg_id
direction

fvg_bottom
fvg_top
fvg_width

fvg_available_at
choch_available_at

candidate_fvg_ids
candidate_fvg_widths

first_retest_at
entry_price

execution_model = INITIAL_CHOCH_FVG

## 9. Stop Loss

Status: FROZEN FOR V1 STRATEGY GEOMETRY

V1 `INITIAL_CHOCH_FVG` first-position SL은
selected FVG의 geometry로 결정한다.

FVG width:

width = FVG.top - FVG.bottom

SL buffer:

buffer = width * 0.20

LONG:

entry = FVG.top
SL = FVG.bottom - buffer

SHORT:

entry = FVG.bottom
SL = FVG.top + buffer

즉:

LONG
→ bullish FVG lower/distal boundary 아래로
  FVG 폭의 20% 추가

SHORT
→ bearish FVG upper/distal boundary 위로
  FVG 폭의 20% 추가

를 사용한다.

다음은 V1 base first-position SL 가격을 대체하지 않는다.

sweep extreme
execution OB distal
final child OB distal
arbitrary M1 pivot
ATR stop
fixed point stop

이 구조 정보들은 scenario/source lifecycle 또는
audit reference로 보존할 수 있지만
`INITIAL_CHOCH_FVG`의 전략 SL 가격 자체를 변경하지 않는다.

실제 주문 가격은 symbol의 valid tick size에 맞게 normalize한다.

Broker spread / stops level / Bid-Ask execution constraint를
이 전략 SL과 정확히 어떻게 연결할지는
execution-infrastructure 단계에서 별도로 확정한다.

그 결정 전까지 broker constraint를 이유로
위 전략 SL 공식을 임의 변경하지 않는다.

## 10. Objective / TP

Scenario scopes:
- EXTERNAL_CONTINUATION
- INTERNAL_ROTATION
- EXTERNAL_REVERSAL

TP must follow the frozen objective family defined before entry.

Exact deterministic objective selection:
TBD.

## 11. Pending Order Cancellation

Current contract includes:
- source invalidation
- objective delivery before fill
- entry zone consumption / invalidation
- new opposing owner where applicable

Exact state machine:
TBD.

## 12. Explicitly Excluded From Baseline

- AI judgment
- weighted quality scoring
- arbitrary RR fallback
- maximum-R target replacement
- arbitrary time exits
- mandatory extra BOS after CHoCH
- FVG add-on
- discretionary partial profit
- live trading

