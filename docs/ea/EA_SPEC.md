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

Directional trend initialization에는
반대편 protected boundary까지 포함된 two-sided confirmed range가 필요하다.

즉 한쪽 confirmed swing만 존재하는 상태에서
그 swing을 body close로 돌파했다는 이유만으로
mature BULLISH / BEARISH external state를 만들지 않는다.

Required before INITIAL_BOS:

confirmed swing high
+
confirmed swing low

Both must be available before the INITIAL_BOS close.

### 2.5 Initial BOS

Classification: D

Trend가 NEUTRAL인 상태에서
먼저 양쪽 boundary가 모두 존재하는 confirmed two-sided range를 구성한다.

Required:

latest adjacent confirmed swing high
+
latest adjacent confirmed swing low

두 swing 모두 INITIAL_BOS close 전에 available해야 한다.

이 pair를:

neutral_range_high
neutral_range_low

로 사용한다.

#### Bullish INITIAL_BOS

close > neutral_range_high

이면 bullish INITIAL_BOS다.

Result:

trend = BULLISH
protected_low = neutral_range_low
external_high = bullish break / delivery extreme

#### Bearish INITIAL_BOS

close < neutral_range_low

이면 bearish INITIAL_BOS다.

Result:

trend = BEARISH
protected_high = neutral_range_high
external_low = bearish break / delivery extreme

Wick-only breach는 INITIAL_BOS가 아니다.

반대편 confirmed boundary가 아직 없다면:

NO INITIAL TREND

이다.

한쪽 swing break만으로
protected swing이 없는 directional state를 만들지 않는다.

### 2.6 Bullish External Structure State

Classification: D

Bullish external state에서는:

trend = BULLISH
protected_low = current bullish structure invalidation swing
external_high = current bullish delivery extreme

를 유지한다.

#### Bullish BOS

현재 bullish external high를 body close로 상향 돌파하면:

close > external_high

bullish BOS가 발생한다.

BOS 후에도 external bullish direction은 유지된다.

BOS가 돌파한 기존 external high를 `break_reference_high`로 freeze한다.

Causal correction window:

break_reference_high occurred
→ bullish BOS candle close

이 window 안에서:

candidate.side = LOW
candidate.occurred_at > break_reference_high.occurred_at
candidate.available_at <= BOS.available_at

을 만족하는 confirmed swing low만 causal correction candidate로 사용한다.

Candidate가 하나 이상이면:

causal_correction_low
=
가장 가격이 낮은 candidate

를 선택한다.

이 swing만 새 protected low로 승격할 수 있다.

Candidate가 하나도 없으면:

protected_low remains unchanged

이다.

단순 latest swing low 또는 BOS candle에 가장 가까운 swing low를 자동 protected low로 사용하지 않는다.

#### Bearish CHoCH

현재 protected low를 body close로 하향 돌파하면:

close < protected_low

bearish external CHoCH가 발생한다.

Result:

old bullish external owner = INVALIDATED
trend_state = TRANSITION

Wick-only breach는 external CHoCH가 아니다.

`TRANSITION`에서는 기존 bullish dealing range를 continuation authorization에 재사용하지 않는다.

완성된 new bearish external state는 새 two-sided structure와 body-close directional confirmation이 deterministic하게 성립한 뒤에만 확정한다.

### 2.7 Bearish External Structure State

Classification: D

Bearish external state에서는:

trend = BEARISH
protected_high = current bearish structure invalidation swing
external_low = current bearish delivery extreme

를 유지한다.

#### Bearish BOS

현재 bearish external low를 body close로 하향 돌파하면:

close < external_low

bearish BOS가 발생한다.

BOS 후에도 external bearish direction은 유지된다.

BOS가 돌파한 기존 external low를 `break_reference_low`로 freeze한다.

Causal correction window:

break_reference_low occurred
→ bearish BOS candle close

이 window 안에서:

candidate.side = HIGH
candidate.occurred_at > break_reference_low.occurred_at
candidate.available_at <= BOS.available_at

을 만족하는 confirmed swing high만 causal correction candidate로 사용한다.

Candidate가 하나 이상이면:

causal_correction_high
=
가장 가격이 높은 candidate

를 선택한다.

이 swing만 새 protected high로 승격할 수 있다.

Candidate가 하나도 없으면:

protected_high remains unchanged

이다.

단순 latest swing high 또는 BOS candle에 가장 가까운 swing high를 자동 protected high로 사용하지 않는다.

#### Bullish CHoCH

현재 protected high를 body close로 상향 돌파하면:

close > protected_high

bullish external CHoCH가 발생한다.

Result:

old bearish external owner = INVALIDATED
trend_state = TRANSITION

Wick-only breach는 external CHoCH가 아니다.

`TRANSITION`에서는 기존 bearish dealing range를 continuation authorization에 재사용하지 않는다.

완성된 new bullish external state는 새 two-sided structure와 body-close directional confirmation이 deterministic하게 성립한 뒤에만 확정한다.

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

Confirmed wave는 다음 role 중 하나를 가질 수 있다.

INTERNAL
EXTERNAL_EXTREME
CAUSAL_CORRECTION
PROTECTED

Wave가 confirmed되었다는 사실만으로
INTERNAL 이외의 role을 자동 획득하지 않는다.

`CAUSAL_CORRECTION`과 `PROTECTED` role은
Section 2.12의 BOS-time causal promotion으로만 획득한다.

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

현재 external structure를 실제로 유지시키고,
그 swing 이후의 directional leg가
기존 external boundary를 body close BOS로 돌파했기 때문에
보호 기준으로 승격된 opposite-side causal correction extreme이다.

#### Bullish state

현재:

protected_low

가 존재한다.

Bullish continuation 중 모든 새 swing low는
처음에는 INTERNAL이다.

Bullish BOS가 발생하면:

1. BOS가 돌파한 기존 external high를 `break_reference_high`로 freeze한다.
2. `break_reference_high.occurred_at` 이후부터 BOS close까지를 correction window로 정의한다.
3. BOS close 시점까지 이미 available한 confirmed swing low만 후보로 사용한다.
4. 그 후보 중 가장 낮은 price의 swing low를 `causal_correction_low`로 선택한다.
5. `causal_correction_low`가 존재하면 새 protected low로 승격한다.
6. 후보가 없으면 기존 protected low를 유지한다.

#### Bearish state

현재:

protected_high

가 존재한다.

Bearish continuation 중 모든 새 swing high는
처음에는 INTERNAL이다.

Bearish BOS가 발생하면:

1. BOS가 돌파한 기존 external low를 `break_reference_low`로 freeze한다.
2. `break_reference_low.occurred_at` 이후부터 BOS close까지를 correction window로 정의한다.
3. BOS close 시점까지 이미 available한 confirmed swing high만 후보로 사용한다.
4. 그 후보 중 가장 높은 price의 swing high를 `causal_correction_high`로 선택한다.
5. `causal_correction_high`가 존재하면 새 protected high로 승격한다.
6. 후보가 없으면 기존 protected high를 유지한다.

#### Availability / No Retroactive Promotion

BOS 전에 가격상 swing이 이미 발생했더라도
그 swing의 3-candle confirmation이 BOS close 이후에야 available되었다면
그 BOS의 causal correction candidate로 사용할 수 없다.

금지:

future confirmation
→ rewrite historical protected swing

Protected promotion은
BOS close 당시 알 수 있었던 정보만 사용한다.

#### External CHoCH

Bullish state:

close < protected_low
→ current bullish external state invalidated
→ TRANSITION

Bearish state:

close > protected_high
→ current bearish external state invalidated
→ TRANSITION

Wick-only breach는 external CHoCH가 아니다.

`TRANSITION` 상태에서는
old trend authority가 종료됐지만
반대편 mature external trend도 아직 완성됐다고 가정하지 않는다.

새 directional state는
valid two-sided structure와 body-close directional confirmation이
다시 확보된 뒤에만 mature BULLISH / BEARISH로 승격한다.

### 2.13 Active Dealing Range

Classification: D

Active dealing range는 단순 최근 pivot high / low가 아니다.

H1/M30의 현재 external structure를 구성하는 protected extreme과
directional delivery extreme을 사용한다.

`TRANSITION` 상태에서는
이전 trend의 dealing range를
새 continuation authorization에 재사용하지 않는다.

새 mature directional external state가 확정된 뒤
새 protected extreme과 directional external extreme으로
새 active dealing range를 구성한다.

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

### 2.19 Trend Engine State and Required Fields

Classification: D

Each timeframe maintains:

trend_state:
    NEUTRAL
    BULLISH
    BEARISH
    TRANSITION

confirmed_waves[]

external_high_id
external_low_id

protected_high_id
protected_low_id

break_reference_id

causal_correction_candidate_ids
causal_correction_extreme_id

last_bos_id
last_choch_id

range_high
range_low

Each confirmed wave records:

wave_id
side
price
occurred_at
confirmed_at
available_at

role:
    INTERNAL
    EXTERNAL_EXTREME
    CAUSAL_CORRECTION
    PROTECTED

Core invariants:

1. Three-candle wave != external trend.
2. Initial trend requires a two-sided confirmed range.
3. Mature directional trend must have an opposite protected swing.
4. Latest swing alone never becomes protected.
5. Protected promotion requires external directional BOS.
6. Bullish BOS selects the lowest available confirmed low in its causal correction window.
7. Bearish BOS selects the highest available confirmed high in its causal correction window.
8. No retroactive protected-swing rewrite.
9. Internal break cannot flip H1/M30 external trend.
10. External trend invalidation requires body close through the current protected swing.
11. Wick-only protected breach is not trend reversal.
12. External/internal promotion uses structural role, not ATR/point/percentage thresholds.

### 2.20 H1/M30 Map Ownership and Scenario Scope

Status: FROZEN FOR V1
Classification: D

#### 2.20.1 Directional Owner Eligibility

Only mature BULLISH / BEARISH structure states may act as directional map owners.

NEUTRAL and TRANSITION are non-directional.

#### 2.20.2 Owner Hierarchy

if H1 is directional:
    parent_owner_tf = H1
    highest_active_map = H1

if H1 is NEUTRAL or TRANSITION
and M30 is directional:
    parent_owner_tf = NONE
    highest_active_map = M30

if neither H1 nor M30 is directional:
    NO DIRECTIONAL SCENARIO

#### 2.20.3 H1 EXTERNAL_CONTINUATION

Required:

H1 = mature BULLISH / BEARISH
scenario.direction = H1.direction
H1 owner valid

Scope:
EXTERNAL_CONTINUATION

Active map:
H1

M30 may be SAME_DIRECTION, OPPOSITE_DIRECTION, NEUTRAL, or TRANSITION.

M30 opposite state alone does not invalidate the H1 continuation lane.

Use:
H1 dealing range
H1 continuation premium/discount gate
external objective family

#### 2.20.4 M30 INTERNAL_ROTATION under mature H1

Required:

H1 = mature directional
M30 = mature directional
M30.direction != H1.direction
scenario.direction = M30.direction
H1 owner still valid

Scope:
INTERNAL_ROTATION

Parent owner:
H1

Active nested map:
M30

Restrictions:
objective family = mature M15+ internal liquidity inside H1 parent range
historical H1 fallback = FORBIDDEN
external H1 target expansion = FORBIDDEN
new mandatory premium/discount gate = NONE

Root/source lineage must align with M30 scenario direction.

#### 2.20.5 Temporary M30 Primary Map

If:
H1 = NEUTRAL or TRANSITION
M30 = mature directional

then M30 becomes the temporary highest active directional map.

Scope:
EXTERNAL_CONTINUATION relative to M30.

Use:
M30 dealing range
M30 continuation premium/discount gate
M30 external objective family

Forbidden:
historical H1 fallback
automatic inheritance of old H1 range
automatic inheritance into a future H1 owner

When H1 later becomes mature directional:
existing M30-primary scenario
→ MAP_REEVALUATION_REQUIRED

No silent owner promotion.

#### 2.20.6 H1 Owner Invalidation

If H1 protected swing is body-broken:

old H1 owner = INVALIDATED
H1 = TRANSITION

All scenarios whose scope depends on that parent H1 owner require cancellation / map reevaluation.

This includes:
H1 EXTERNAL_CONTINUATION
M30 INTERNAL_ROTATION nested under that H1 owner

The old H1 dealing range cannot authorize new continuation setups.

#### 2.20.7 H1 EXTERNAL_REVERSAL Phase

When H1 was previously mature in direction OLD,
entered TRANSITION through protected-swing body break,
and later matures in direction NEW where NEW != OLD:

create new H1 owner_id
owner_phase = REVERSAL

H1-direction external scenarios created while owner_phase = REVERSAL use:
scenario_scope = EXTERNAL_REVERSAL

After the first same-direction H1 continuation BOS under the new owner:
owner_phase = ESTABLISHED

Future new scenarios then use:
scenario_scope = EXTERNAL_CONTINUATION

Existing frozen scenarios are not relabeled retroactively.

#### 2.20.8 H1 Re-establishment in Same Direction

If H1 enters TRANSITION but later matures again in the same direction as the previous H1 owner:

new owner_id is created
owner_phase = ESTABLISHED
scope = EXTERNAL_CONTINUATION

It is not EXTERNAL_REVERSAL.

#### 2.20.9 Parallel Structural Lanes

When:
H1 = mature directional
M30 = mature opposite directional

the engine may maintain two independent planning lanes:

Lane A:
H1 direction
EXTERNAL_CONTINUATION

Lane B:
M30 direction
INTERNAL_ROTATION

They must never share:
scenario_id
objective family
Root/source lineage
sweep
CHoCH
selected FVG
pending-order identity

This authorizes parallel analysis/planning only.

Whether opposite order-ready lanes may simultaneously place live pending orders is a separate V1 execution/risk decision.

#### 2.20.10 Scenario Scope Is Frozen

Once a scenario PLAN is frozen:

scenario_scope
parent_owner_id
active_map_tf
scenario_direction
objective family

do not change category in place.

If owner hierarchy changes materially:

old scenario
→ cancel / reevaluate

new map
→ new scenario_id

No hindsight scope promotion.

#### 2.20.11 Required Map State

scenario_id
scenario_scope
scenario_direction

parent_owner_tf
parent_owner_id
parent_owner_direction

active_map_tf
active_map_owner_id
active_map_direction

h1_trend_state
h1_owner_id
h1_owner_phase

m30_trend_state
m30_owner_id

parent_range_high
parent_range_low

active_range_high
active_range_low

premium_discount_gate_required
premium_discount_gate_result

created_at
map_invalidated_at
map_invalidation_reason

### 2.21 Required Structure State

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

### 2.22 Baseline Exclusions

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

FVG는 Candle 3가 완전히 close된 이후에만 available하다.

FVG.available_at = Candle3 close

진행 중인 Candle3를 이용해
FVG candidate를 미리 생성하거나 주문을 authorize하지 않는다.

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

``` text
Candidate eligibility는 meaningful CHoCH candle close 시점에 판정한다.

해당 시점까지 candidate FVG는 반드시:

1. 이미 available 상태여야 한다.
2. meaningful CHoCH와 같은 방향이어야 한다.
3. 같은 authorized sweep-to-CHoCH causal leg에 속해야 한다.
4. 형성 이후 아직 retest되지 않았어야 한다.
5. 아직 consumed / invalidated되지 않았어야 한다.

FVG가 available된 뒤
meaningful CHoCH candle close 전에 가격이 해당 FVG를 다시 접촉했다면:

FVG available
→ pre-authorization retest
→ candidate 제외

로 처리한다.

이미 지나간 retest를
CHoCH 확정 뒤 사후 entry로 복원하지 않는다.
```

### 8.4 Multiple FVG Selection and Freeze

Classification: D

Meaningful CHoCH를 만든 M1 candle이 close되는 순간
현재 first-position execution candidate set을 freeze한다.

candidate_freeze_at = CHoCH candle close

이 시점에 Section 8.3의 eligibility를 만족하는
valid FVG만 snapshot한다.

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

CHoCH candle close 이후 새로 형성되는 FVG는
현재 `INITIAL_CHOCH_FVG` candidate set에 추가하지 않는다.

이미 freeze된 selected FVG를
이후 생성된 더 넓은 FVG로 교체하지 않는다.

CHoCH close 시점에 eligible FVG가 하나도 없으면:

NO BASE FIRST-POSITION ENTRY

다.

### 8.5 First Retest

Classification: D

Selected FVG는 meaningful CHoCH candle close에서 freeze된다.

그 이후 selected FVG의 direction-specific entry boundary에
처음 다시 도달하는 것을 first authorized retest로 정의한다.

LONG:

price reaches selected bullish FVG.top

SHORT:

price reaches selected bearish FVG.bottom

실제 baseline execution은
해당 boundary에 pending limit order를 미리 제출하는 방식이다.

따라서 first authorized retest와
pending order activation/fill은
MT5의 실제 Bid/Ask execution semantics에 따라 기록한다.

FVG 생성 이후 CHoCH/order authorization 전에 이미 발생한 touch는
first authorized retest가 아니다.

그 FVG는 Section 8.3에 따라
candidate에서 제외되어야 한다.

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

MT5 baseline order type:

LONG:
BUY_LIMIT at selected bullish FVG.top

SHORT:
SELL_LIMIT at selected bearish FVG.bottom

V1 baseline은 strategy entry에
spread offset을 추가하지 않는다.

향후 optimization 단계에서:

spread-aware pending-price adjustment

를 별도 execution variant로 비교할 수 있다.

해당 variant는 baseline strategy geometry를
사후 변경하지 않는다.

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

candidate_freeze_at

excluded_pre_retested_fvg_ids
excluded_consumed_fvg_ids

selected_fvg_frozen_at

strategy_entry_price
normalized_entry_price

pending_created_at

bid_at_authorization
ask_at_authorization
spread_at_authorization

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

실제 주문 가격은 symbol의:

SYMBOL_TRADE_TICK_SIZE

에 맞는 valid trade-price grid를 사용한다.

Digits 또는 SYMBOL_POINT만으로
실제 executable price increment를 가정하지 않는다.

Entry FVG boundary는 OHLC 기반 가격이므로
원칙적으로 tick grid 위에 있어야 한다.

floating-point 표현 오차 제거를 넘어
entry의 경제적 가격 자체를 이동해야만 valid tick이 된다면:

EXECUTION_PRICE_NOT_REPRESENTABLE
→ NO TRADE

로 처리한다.

20% FVG-width SL 계산값이 tick grid 사이에 위치하면
전략 SL을 좁히지 않는 방향으로 normalize한다.

LONG:

raw_SL = FVG.bottom - 0.20 * FVG.width
normalized_SL =
greatest valid tick price <= raw_SL

SHORT:

raw_SL = FVG.top + 0.20 * FVG.width
normalized_SL =
smallest valid tick price >= raw_SL

즉 tick normalization은
원래 전략 stop distance를 유지하거나
최소 tick만큼 더 넓힐 수는 있지만
절대로 더 좁히지 않는다.

Broker execution constraint 때문에
FVG selection, entry boundary 또는
20% FVG-width strategy SL을 임의 변경하지 않는다.

해당 frozen geometry가 broker constraint를 만족하지 못하면
Section 11의 `EXECUTION_INFEASIBLE` 규칙을 적용한다.

## 10. Objective / TP

Status: FROZEN FOR V1

### 10.1 Purpose

Classification: D

V1의 Objective는 원하는 RR을 만들기 위해 임의로 선택하는 가격이 아니다.

현재 scenario scope와 owner가 설명할 수 있는
실제 structural liquidity candidate를 먼저 구성하고,
Entry / SL geometry가 확정된 뒤
그 pre-frozen family 안에서 final TP 자격을 판정한다.

`planned R >= 1`은:

objective-candidate eligibility filter

다.

다음이 아니다.

trade-wide immediate rejection filter
maximum-R optimizer
permission to invent a farther TP
permission to tighten SL

### 10.2 Scenario Scopes

Classification: D

허용 scope:

EXTERNAL_CONTINUATION
INTERNAL_ROTATION
EXTERNAL_REVERSAL

Scenario scope가 objective candidate universe를 결정한다.

R이 크다는 이유로 scope 밖 liquidity를 final TP로 승격하지 않는다.

### 10.3 Objective Family Freeze

Classification: D

PLAN 단계에서 Entry / SL geometry를 알기 전에 다음을 freeze한다.

scenario_id
scenario_scope
owner_id
direction

objective_candidate_ids
objective_candidate_prices
objective_candidate_types
objective_candidate_order
objective_candidate_available_at

objective_family_frozen_at

Entry / SL 확정 뒤 금지:

add new liquidity candidate
change candidate order
insert better-R candidate
search hindsight target

### 10.4 EXTERNAL_CONTINUATION Family

Classification: D

Current owner direction의 미소진 H1/M30 external liquidity를
current-structure objective family로 사용한다.

Entry와 external objective 사이의 internal liquidity는:

INTERMEDIATE_DELIVERY

로 기록하며 final external TP candidate로 승격하지 않는다.

### 10.5 INTERNAL_ROTATION Family

Classification: D

현재 active dealing range 안에서
trade direction에 존재하는
meaningful mature M15+ internal liquidity만 family에 포함한다.

External liquidity는
1R을 만들기 위한 INTERNAL_ROTATION TP fallback으로 사용하지 않는다.

가장 가까운 internal liquidity가 1R 미만이어도
즉시 scenario를 종료하지 않는다.

Frozen internal family에서
가장 가까운 R-eligible mature internal liquidity를 찾는다.

### 10.6 EXTERNAL_REVERSAL Family

Classification: D

EXTERNAL_REVERSAL은:

H1/M30 protected structure body break
+
new-direction owner confirmation

이후에만 생성한다.

그 뒤 새 owner direction의
미소진 H1/M30 external liquidity를 family로 사용한다.

M1 CHoCH만으로 external reversal objective family를 만들지 않는다.

### 10.7 Planned-R Geometry

Classification: D

Objective eligibility 계산은 frozen strategy geometry를 사용한다.

LONG:

risk = Entry - normalized_SL
reward(candidate) = candidate_price - Entry
planned_R = reward / risk

SHORT:

risk = normalized_SL - Entry
reward(candidate) = Entry - candidate_price
planned_R = reward / risk

Required:

risk > 0
reward > 0

Final TP eligibility:

planned_R >= 1.0

`normalized_SL`은 Section 9의
outward tick-normalized 20% FVG-width strategy SL이다.

Baseline planned-R eligibility 계산에는:

commission
swap
future slippage
spread-aware TP offset

을 섞지 않는다.

이들은 execution/economic reporting에서 별도로 기록한다.

### 10.8 Candidate Selection

Classification: D

Selected FVG, Entry, normalized strategy SL이 확정된 뒤
frozen objective family를 방향상 가까운 순서대로 검사한다.

각 candidate:

1. 이미 consumed이면 제외한다.
2. scenario scope와 호환되지 않으면 제외한다.
3. planned R을 계산한다.
4. planned R < 1이면 final TP 자격을 제외하고 `INTERMEDIATE_DELIVERY`로 기록한다.
5. planned R >= 1인 최초 candidate를 `FINAL_TP`로 선택한다.
6. 첫 eligible candidate를 선택하면 current tier 검색을 종료한다.

금지:

max-R candidate selection
farthest candidate selection
RR-based candidate reordering

### 10.9 Historical H1 Fallback Tier

Classification: D for strategy / H for warm-up depth

External scenario는 PLAN 단계에서
current-structure family 바깥 방향의
causally-known 미소진 H1 external liquidity 중
가장 가까운 최대 2개를 inactive fallback tier로 freeze할 수 있다.

Allowed:

EXTERNAL_CONTINUATION
EXTERNAL_REVERSAL

Forbidden:

INTERNAL_ROTATION

Fallback candidate도 Entry / SL을 알기 전에
ID / price / order가 freeze되어야 한다.

Selection precedence:

Tier 1 = CURRENT_STRUCTURE
Tier 2 = HISTORICAL_H1_FALLBACK

Current tier에 valid planned R >= 1 candidate가 하나라도 있으면
fallback을 사용하지 않는다.

Current tier에서 final TP를 찾지 못했을 때만
fallback tier를 같은 nearest-first / >=1R 규칙으로 검사한다.

Fallback에서 더 큰 R을 이유로
더 먼 candidate를 선택하지 않는다.

Historical data를 어디까지 복원해야 하는지는
Section 2.18 warm-up requirement에서 별도로 결정한다.

Permanent strategy rule에 특정 calendar start date를 사용하지 않는다.

### 10.10 No Eligible Objective

Classification: D

다음을 모두 평가한 뒤에도:

allowed current frozen family
+
applicable pre-frozen fallback family

planned R >= 1인 valid candidate가 없으면:

NO TRADE
reason = NO_R_ELIGIBLE_OBJECTIVE

로 처리한다.

첫 번째 1R 미만 liquidity 하나만 보고
scenario를 즉시 폐기하지 않는다.

### 10.11 Intermediate Delivery

Classification: D

Valid liquidity가 planned R < 1이라는 이유로
시장 지도에서 삭제되지 않는다.

해당 candidate는:

INTERMEDIATE_DELIVERY

로 기록한다.

EXTERNAL_CONTINUATION에서는
selected external objective·owner·source lineage가 유지되는 한
intermediate delivery 자체만으로
pending을 취소하거나 TP를 축소하지 않는다.

INTERNAL_ROTATION에서도
selected final objective가 아닌
더 가까운 <1R internal liquidity의 delivery 자체만으로
final TP를 자동 교체하지 않는다.

### 10.12 Final TP Freeze Timing

Classification: D

Final TP selection은:

meaningful CHoCH close
→ widest valid FVG freeze
→ Entry freeze
→ normalized strategy SL freeze
→ objective eligibility evaluation
→ final TP freeze
→ pending order submission

순서다.

Required:

objective_family_frozen_at
<
entry_sl_geometry_known_at

final_objective_selected_at
<= pending_created_at

### 10.13 No Post-Selection Rollover

Classification: D

Final TP가 선택된 뒤
같은 scenario 안에서 다음 objective candidate로
자동 rollover하지 않는다.

Final objective가 pending fill 전에 delivered되면:

CANCELED_OBJECTIVE_DELIVERED

로 scenario와 pending order를 취소한다.

새 objective가 필요하면
map / scenario를 다시 평가한다.

### 10.14 TP Price

Classification: D

Final TP는 selected liquidity의
actual structural price를 사용한다.

Swing liquidity:

actual wick high / low

를 사용한다.

금지:

move TP farther to improve R
move TP because another candidate has higher R
automatic max-R extension

### 10.15 TP Execution Semantics

Classification: D

V1 baseline은 exact selected-liquidity TP를 사용한다.

LONG TP:
Bid-side execution

SHORT TP:
Ask-side execution

Spread 또는 1-tick inward TP front-run은
baseline strategy에 포함하지 않는다.

필요하면 향후 별도 immutable
execution-optimization variant로 비교한다.

### 10.16 Required Objective State

각 scenario는 최소 다음을 기록한다.

scenario_scope
owner_id
direction

objective_family_frozen_at

objective_candidates[]:
    id
    liquidity_id
    liquidity_type
    price
    available_at
    family_tier
    order_index
    consumed
    consumed_at
    planned_R
    eligibility
    role

family_tier:
    CURRENT_STRUCTURE
    HISTORICAL_H1_FALLBACK

eligibility:
    SCOPE_INELIGIBLE
    CONSUMED
    BELOW_1R
    ELIGIBLE

role:
    FINAL_TP
    INTERMEDIATE_DELIVERY
    UNUSED_FUTURE

final_objective_id
final_objective_price
final_objective_selected_at

## 11. Pending Order Lifecycle + MT5 Execution Constraints

Status: PARTIALLY FROZEN FOR V1

### 11.1 Strategy vs Execution State

Classification: D

Strategy validity와 broker execution feasibility를 분리한다.

예:

valid strategy signal
+
broker constraint violation

은:

strategy_signal = VALID
execution_state = EXECUTION_INFEASIBLE

로 기록한다.

Broker constraint 때문에
전략 geometry를 사후 변경하지 않는다.

### 11.2 Bid / Ask Semantics

Classification: D

MT5 pending execution은 side-specific market price를 사용한다.

BUY_LIMIT:

Ask-side execution / activation semantics

SELL_LIMIT:

Bid-side execution / activation semantics

Protective stop:

LONG SL
→ Bid-side execution

SHORT SL
→ Ask-side execution

따라서 execution-sensitive event에서는
Bid와 Ask를 모두 기록한다.

### 11.3 StopsLevel

Classification: D

Order authorization 시:

SYMBOL_TRADE_STOPS_LEVEL
SYMBOL_POINT

를 읽어 broker minimum distance를 price unit으로 계산한다.

Pending entry legality:

BUY_LIMIT:

Ask - entry
>= broker minimum distance

SELL_LIMIT:

entry - Bid
>= broker minimum distance

Attached SL / TP도
broker가 요구하는 applicable minimum-distance constraint를 만족해야 한다.

만약 frozen strategy geometry가
broker minimum-distance constraint를 만족하지 못하면:

EXECUTION_INFEASIBLE
→ NO ORDER

이다.

금지:

move FVG entry
widen strategy SL only to satisfy broker
replace selected FVG
change frozen objective

Strategy validity와 broker feasibility는
ledger에서 별도로 기록한다.

### 11.4 FreezeLevel

Classification: D

EA는:

SYMBOL_TRADE_FREEZE_LEVEL

을 읽고 기록한다.

Strategy cancellation event가 발생하면
strategy state는 즉시:

CANCELED

가 된다.

그 뒤 EA는 실제 MT5 pending order 삭제를 요청한다.

Broker freeze restriction 또는 server constraint 때문에
삭제가 거부되면:

strategy_state = CANCELED
execution_state = CANCEL_REJECTED_BY_BROKER

로 기록한다.

그 broker order가 이후 실제 체결되면:

EXECUTION_DIVERGENCE

로 분류한다.

이 체결은 strategy-parity performance에서 제외하고
execution-infrastructure failure로 별도 집계한다.

### 11.5 Pending Order Lifetime

Classification: D / Frozen for V1

V1은 time-based strategy cancellation을 사용하지 않는다.

time_based_strategy_cancellation = NONE

Pending order는 단순히 시간이 오래 지났다는 이유로
취소하지 않는다.

다음은 cancellation authority가 아니다.

N bars elapsed
N minutes elapsed
session close
calendar day change
next trading day
arbitrary age threshold

Scenario의 causal state가 살아 있는 동안
pending order는 계속 유지한다.

MT5 pending order는:

ORDER_TIME_GTC

를 사용한다.

Broker-side expiration을
strategy cancellation 대신 사용하지 않는다.

주문은 Section 11.9의
causal cancellation condition이 발생할 때만
EA가 직접 삭제 요청한다.

### 11.6 Pending Filling Policy

Classification: D for V1 infrastructure

Pending order request는 baseline에서:

ORDER_FILLING_RETURN

을 사용한다.

단, broker/server가 해당 symbol에서
다른 filling policy를 강제하는 경우
symbol capability를 먼저 확인한다.

Trade request 결과는 반드시
trade-server retcode까지 확인한다.

Local function return만으로
주문이 server에 정상 수락되었다고 판정하지 않는다.

Record:

order_send_result
trade_server_retcode
broker_order_ticket
rejection_reason

Server rejection이면:

strategy signal may remain VALID
execution = REJECTED

로 기록한다.

### 11.7 Preflight Validation

Classification: D

OrderSend 전에
OrderCheck-equivalent preflight와
symbol-property validation을 수행한다.

최소 검사:

trade mode permits requested direction
pending order type supported
entry on valid tick grid
SL on valid tick grid
TP on valid tick grid
entry respects StopsLevel
SL / TP respect applicable broker distance
volume respects min / max / step
margin / request check acceptable

실패:

EXECUTION_INFEASIBLE
→ NO ORDER

Strategy signal은 research ledger에 남긴다.

### 11.8 No Automatic Strategy-Price Repair

Classification: D

Execution layer가 자동 변경해서는 안 되는 항목:

selected FVG
FVG entry boundary
20% FVG-width strategy SL
frozen objective / TP

허용되는 자동 변환:

floating-point cleanup
Section 9의 directional tick normalization
기존 risk-sizing contract에 따른 valid lot-step normalization

Frozen strategy geometry가
broker에 합법적으로 제출될 수 없다면:

EXECUTION_INFEASIBLE
→ NO ORDER

이다.

### 11.9 Causal Pending Cancellation

Classification: D

V1 pending order cancellation은
아래 causal invalidation event만 사용한다.

Time-only cancellation은 사용하지 않는다.

다음 중 applicable condition이 발생하면
pending strategy order를 취소한다.

frozen objective delivered before fill
HTF Root / parent owner invalidated
final refined source invalidated
trigger protected structure invalidated
selected FVG invalidated / consumed before valid fill
opposing owner confirmed where applicable
source episode terminated where applicable

Event 발생 즉시:

strategy_state = CANCELED

로 변경하고
MT5 pending order 삭제를 요청한다.

이미 지나간 retest/fill을
사후 복원하지 않는다.

### 11.10 No Time-Based Cancellation

Classification: D / Frozen for V1

V1에서는 시간 경과 자체를
pending order invalidation reason으로 사용하지 않는다.

금지:

N-bar timeout
N-minute timeout
session-close timeout
day-change timeout
next-day automatic cancellation
age-decay cancellation

Pending order의 생존 여부는
elapsed time이 아니라
현재 scenario의 causal validity로 결정한다.

유지 조건:

objective still valid
Root / owner still valid
final refined source still valid
trigger protected structure still valid
selected FVG still valid
no opposing owner confirmation
source episode still valid

위 조건이 유지되면
주문이 오래 대기했더라도 pending을 유지한다.

반대로 시간이 거의 지나지 않았더라도
Section 11.9의 causal invalidation event가 발생하면
즉시 취소한다.

따라서:

time_based_strategy_cancellation = NONE
MT5_pending_lifetime = ORDER_TIME_GTC
cancellation_authority = CAUSAL_EVENTS_ONLY

### 11.11 Execution State Machine

PREPARED
→ ARMED
→ SWEEP_CONFIRMED
→ CHOCH_CONFIRMED

at CHOCH candle close:
    snapshot already-available causal FVGs
    exclude pre-retested / consumed FVGs
    select widest
    ignore all future FVGs

→ FVG_SELECTED

execution preflight:
    tick-grid validation
    Bid/Ask legality
    StopsLevel
    trade mode
    volume
    margin / request validation

if infeasible:
    → EXECUTION_INFEASIBLE
    → NO ORDER

if feasible:
    → PENDING
    → MT5 limit order

then:

valid activation / fill
→ FILLED

or:

causal strategy cancellation
→ CANCELED
→ request MT5 pending deletion

if broker refuses deletion and order later fills:
→ EXECUTION_DIVERGENCE

Elapsed time alone never transitions PENDING to CANCELED in V1.

### 11.12 Required Execution Ledger

Minimum fields:

symbol_tick_size
symbol_point
symbol_digits
symbol_stops_level
symbol_freeze_level

strategy_entry_price
normalized_entry_price

raw_strategy_sl
normalized_sl

bid_at_authorization
ask_at_authorization
spread_at_authorization

order_type
order_time_type
order_filling_type

preflight_result
order_send_retcode
broker_order_ticket

pending_created_at

first_retest_at
fill_at
fill_price

strategy_cancel_at
strategy_cancel_reason
broker_cancel_result

execution_status
execution_divergence_reason

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

