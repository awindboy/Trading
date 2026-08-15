# EA Design Decisions

## D-001 — GitHub as project memory

Status: ACTIVE

GitHub is the Single Source of Truth for long-term EA development.

ChatGPT conversation history is not authoritative.

## D-002 — Deterministic baseline first

Status: ACTIVE

The first EA must run without Gemini, Codex, OpenClaw, or other runtime AI dependencies.

## D-003 — MT5 is the primary backtest platform

Status: ACTIVE

Primary validation uses MT5 Strategy Tester, preferably Every tick based on real ticks.

## D-004 — Strategy correctness before profitability

Status: ACTIVE

Implementation parity with the intended rules is validated before optimization or profitability tuning.

## D-005 — Ground Truth V2 is not a prerequisite

Status: ACTIVE

The currently BLOCKED Ground Truth V2 pipeline is not required before baseline EA development.

## D-006 — Three-candle wave confirmation

Status: ACTIVE

Baseline EA의 market structure wave detector는 symmetric pivot detector를 사용하지 않는다.

Wave confirmation은 `MENTOR_RULE_CONTRACT.md`와
`mentor_engine/structure.py`의 3-candle rule을 사용한다.

- 3 consecutive bearish body closes confirm the preceding swing high.
- 3 consecutive bullish body closes confirm the preceding swing low.
- A doji belongs to neither direction and interrupts the sequence.
- Swing price is the highest/lowest wick of the completed leg.
- The swing becomes usable only after the third confirmation candle closes.

`ICTCockpitIndicator.mq5`의 pivot-length 방식은 visual/reference implementation으로만 사용한다.

Reason:

현재 deterministic Mentor research contract 및 Python baseline과 가장 직접적으로 일치하며,
future-side symmetric pivot confirmation dependency를 피할 수 있다.

## D-007 — Body close defines structure break

Status: ACTIVE

BOS / CHoCH는 structure level을 wick이 통과한 것만으로 확정하지 않는다.

```text
bullish break:
close > structure level

bearish break:
close < structure level
```

Wick-only breach는 structure state를 변경하지 않으며
liquidity module에서 sweep candidate로 평가한다.

Reason:

`AGENTS.md`의 external structure 및 CHoCH 계약과
현재 Mentor rule contract가 모두 body-close structure break를 요구한다.

## D-008 — Protected swing state over latest-pivot state

Status: ACTIVE

Baseline EA는 단순한 latest swing high / latest swing low를
external structure state로 사용하지 않는다.

각 timeframe은 명시적인:

```text
trend
protected swing
directional external extreme
active dealing range
```

를 유지한다.

현재 external structure 내부에서 형성되는 작은 swings는
기본적으로 internal structure로 취급한다.

Reason:

`AGENTS.md`는 H1/M30 protected structure와 내부 swing을 명확히 구분하며,
M1 또는 내부 swing break만으로 external reversal을 선언하는 것을 금지한다.

## D-009 — Structure information is time-causal

Status: ACTIVE

모든 swing과 structure event는
가격이 발생한 시점과 판단에 사용할 수 있게 된 시점을 분리한다.

Minimum metadata:

```text
occurred_at
available_at
```

나중에 external로 승격된 swing의 rank를
과거 시점부터 소급해서 사용할 수 없다.

Only closed-bar information may authorize structure decisions.

Reason:

Strategy Tester와 live EA 사이의 parity를 유지하고
look-ahead contamination을 방지하기 위함이다.

---
## D-010 — Conservative liquidity baseline

Status: ACTIVE

V1 EA는 가능한 많은 swing을 liquidity로 탐지하지 않는다.

Liquidity는 다른 시장 참여자가
그 level 바깥에 stop을 둘 행동적 / 구조적 이유가
deterministic하게 설명되는 경우에만 생성한다.

V1 eligible families:

```text
EXTERNAL_SWING
DEFENDED_RANGE_EDGE
STRUCTURAL_REACTION
```

Simple recent pivot alone is not tradable liquidity.

Reason:

현재 전략의 핵심은 liquidity quantity가 아니라
meaningful pre-existing stop pool과 그 sweep의 인과성을 보존하는 것이다.

---

## D-011 — External structure is primary liquidity

Status: ACTIVE

H1/M30에서 단순 최근 고점/저점을 external liquidity로 사용하지 않는다.

Market Structure engine이
external/protected 의미를 확정한 구조적 high/low를
가장 신뢰도 높은 liquidity family로 사용한다.

해당 swing의 external/protected 의미가 나중에 확정되면
liquidity availability도 그 확정 시점 이후부터 시작한다.

Reason:

최근 pivot을 무조건 liquidity로 승격하는 것을 막고,
Market Structure와 Liquidity의 causal hierarchy를 유지하기 위함이다.

---

## D-012 — Strict defended range for V1

Status: ACTIVE

V1 defended range liquidity는
기존 deterministic four-wave box protocol을 사용한다.

Required:

```text
four alternating confirmed waves
+
overlapping defended high wick regions
+
overlapping defended low wick regions
+
no valid body escape before range confirmation
```

한쪽 equal highs/equal lows만 존재하는 경우는
V1에서 독립적인 defended edge로 생성하지 않는다.

Reason:

Independent equal-high/equal-low detector는
price tolerance parameter를 새로 정의해야 한다.

V1에서는 parameter sensitivity를 줄이고
가장 보수적이고 설명 가능한 defended-range definition부터 검증한다.

향후 별도 immutable variant에서
independent equal highs/lows를 비교할 수 있다.

---

## D-013 — Structural OB reaction can create liquidity

Status: ACTIVE

이미 존재하며 structurally owned 상태인 causal OB에서
가격이 실제 반응하고 confirmed reaction swing이 만들어지면
그 swing 바깥을 새로운 liquidity로 사용할 수 있다.

```text
bullish OB reaction
-> confirmed reaction low
-> sell-side liquidity

bearish OB reaction
-> confirmed reaction high
-> buy-side liquidity
```

Reaction OB는 swing reaction 이전에 이미 존재해야 한다.

Liquidity는 reaction wave가 confirmed된 이후에만 active하다.

FVG touch alone does not create V1 reaction liquidity.

Reason:

이 규칙은 시장 참여자가 이미 확인된 지지/저항 반응을 보고 진입하고,
그 reaction swing 바깥에 stop을 둘 수 있다는 행동적 이유를 보존한다.

---

## D-014 — Trendline liquidity excluded from V1

Status: ACTIVE

Trendline-based liquidity는 V1 baseline에서 제외한다.

기존 Python의 3-wave projected-line detector는
research reference로만 유지한다.

Reason:

사람에게 명확한 trendline과
현재 deterministic projection algorithm 사이의 의미적 parity가 충분히 검증되지 않았다.

Core EA baseline에서는
더 명확한 external structure / defended range / structural reaction liquidity를 우선한다.

향후 trendline liquidity는 별도 research variant로 추가할 수 있다.

---

## D-015 — Liquidity is consumed once

Status: ACTIVE

Eligible liquidity pool은 다음 중 하나가 발생하면 consumed된다.

```text
wick penetration + close recovery
-> SWEEP

body close beyond outer level
-> BODY_DELIVERY
```

Consumed pool은 같은 structural reason으로 재사용하지 않는다.

새 거래에서 동일 가격대를 다시 liquidity로 사용하려면
새로운 causal liquidity object가 형성되어야 한다.

Reason:

이미 stop pool이 실제로 거래된 뒤에도
동일 liquidity가 무한히 존재한다고 가정하는 것을 방지한다.

---

## D-016 — Same-bar liquidity self-sweep is forbidden

Status: ACTIVE

현재 bar close에서 처음 확정된 liquidity object를
동일 bar의 intrabar high/low가 이미 sweep한 것으로 처리하지 않는다.

Liquidity는 `available_at` 이후의 causal processing step부터 active하다.

Reason:

Historical replay에서 미래 정보를 이용한
self-referential liquidity/sweep event를 방지하기 위함이다.

---

## D-017 — Root OB requires meaningful swing ownership

Status: ACTIVE

V1 HTF Root OB는 단순 latest opposite candle이 아니다.

Root candidate는:

```text
meaningful external/protected swing
or
structurally meaningful internal swing
```

의 origin causal window에 속해야 한다.

그 window 안에서 subsequent directional leg가 시작되기 전
마지막 opposite candle을 Root candidate로 사용한다.

Reason:

구조 전달 직전 우연히 존재한 pause candle을
실제 scenario source로 잘못 승격하는 것을 방지하기 위함이다.

---

## D-018 — Structure delivery is V1 displacement proof

Status: ACTIVE

V1은 Root OB confirmation을 위해
별도의 ATR/body-size/FVG-size threshold를 사용하지 않는다.

Root candidate 이후 same causal directional leg가
meaningful structure level을 body close로 돌파한 사실을
minimum displacement proof로 사용한다.

```text
meaningful structure body-break
= minimum V1 displacement proof
```

Wick breach는 충분하지 않다.

Reason:

임의 threshold parameter를 줄이면서도
실제 directional delivery가 발생했다는 객관적인 증거를 유지하기 위함이다.

---

## D-019 — V1 initial Root uses causal LAST_OPPOSITE_OB lineage

Status: ACTIVE

V1 first-position Root source는
`LAST_OPPOSITE_OB` 계열을 사용한다.

하지만 모든 last-opposite detector 결과를 사용하지 않는다.

Required filters:

```text
meaningful swing ownership
same causal leg
opposite candle direction
meaningful structure body-break
scenario/objective direction alignment
freshness
```

`FVG_ORIGIN_OB`는 V1 initial Root source 권한을 갖지 않는다.

HTF FVG 자체도 Root source가 아니다.

향후 FVG-origin Root 방식은
별도 immutable research variant로 비교할 수 있다.

---

## D-020 — Root freshness uses structural state, not arbitrary expiry

Status: ACTIVE

Root OB는:

```text
fully consumed
or
causal structure invalidated
```

될 때 first-position source 권한을 잃는다.

단순 touch만으로 즉시 폐기하지 않는다.

V1에서는 다음을 사용하지 않는다.

```text
N-touch expiry
N-bar expiry
ATR age decay
quality score
```

Reason:

Root의 생존 여부를 임의 score가 아니라
실제 price interaction과 causal structure state로 판단하기 위함이다.

---

## D-021 — Root bounds remain full candle until causal refinement

Status: ACTIVE

HTF Root OB의 initial bounds는 origin candle의 전체 wick range다.

```text
bottom = low
top = high
```

Root 단계에서 body-only 또는 50% geometry로 축소하지 않는다.

Root 자체의 source precision은
후속 causal LTF refinement가 담당한다.

최초 포지션의 실제 entry / SL geometry는
후속 CHoCH displacement FVG 규칙이 담당한다.

Reason:

HTF Root detection과 execution refinement의 역할을 분리하고,
Root 단계에서 임의로 RR을 개선하는 것을 방지하기 위함이다.

---

## D-022 — Ambiguous incomparable Roots do not get score-selected

Status: ACTIVE

동일 scenario에 비교 불가능한 Root candidate가 여러 개 남을 경우
다음 기준으로 하나를 임의 선택하지 않는다.

```text
nearest
narrowest
newest
highest RR
weighted quality score
```

Nested causal relation이 명확하면 lineage로 유지한다.

Causal owner를 deterministic하게 결정할 수 없다면:

```text
NO TRADE / AMBIGUOUS ROOT
```

로 처리한다.

Reason:

수익률 최적화를 위해 사후적으로 좋은 OB를 선택하는 것을 막고
baseline의 설명 가능성과 causal parity를 유지하기 위함이다.

---
## D-023 — Causal child repeats Root logic on lower timeframe

Status: ACTIVE

V1 lower-timeframe child OB는
parent 내부의 단순 small opposite candle이 아니다.

각 child는 다음 causal logic을 만족해야 한다.

```text
meaningful lower-TF swing origin
+
last opposite candle in that origin window
+
same causal lower-TF directional leg
+
meaningful lower-TF structure body-break
```

Reason:

HTF Root와 lower-TF refinement가
서로 다른 OB 철학을 사용하지 않게 하고,
작은 candle을 임의로 precision source로 승격하는 것을 방지하기 위함이다.

---

## D-024 — Refinement authority follows event lineage, not distance

Status: ACTIVE

Parent-child refinement는
가격 근접도보다 event lineage를 우선한다.

Full containment는 직접 허용한다.

Parent boundary를 일부 벗어난 child는
고정 point/ATR tolerance로 허용하지 않는다.

대신:

```text
same swing-origin lower-TF sequence
same displacement ownership
same structure-delivery chain
valid parent-child time relation
```

을 모두 만족할 때만 `EVENT_ADJACENT` child로 인정한다.

Reason:

multi-timeframe aggregation 차이는 허용하되,
임의 tolerance parameter로 unrelated zone을 연결하지 않기 위함이다.

---

## D-025 — Refinement stops at deepest unambiguous child

Status: ACTIVE

V1은 무조건 M5까지 refinement하지 않는다.

```text
deepest unambiguous causal child
```

를 final refined source로 사용한다.

예:

```text
H1 → M30 → M15 valid
M5 ambiguous
```

이면 M15를 final child로 유지한다.

M5에서 가장 좁거나 RR이 좋은 candidate를 선택하지 않는다.

Reason:

Refinement의 목적은 SL 최소화가 아니라
causal certainty를 유지한 precision source identification이기 때문이다.

---

## D-026 — At least one lower-timeframe child is mandatory

Status: ACTIVE

최초-position V1 baseline은
HTF Root 아래 최소 하나의 valid causal child를 요구한다.

```text
Root only
→ NO TRADE
```

첫 refinement 단계부터 child ownership이 ambiguous하고
하나도 deterministic하게 확정할 수 없으면 거래하지 않는다.

Reason:

현재 Mentor baseline은
HTF source를 lower timeframe에서 causal하게 정밀화한 뒤
M1 trigger를 확인하는 protocol이기 때문이다.

---

## D-027 — Refinement lineage is frozen before M1 trigger

Status: ACTIVE

Final refined source와 전체 parent-child lineage는
source contact 및 M1 sweep/CHoCH를 보기 전에 확정한다.

금지:

```text
M1 reaction observed
→ matching M5 OB selected retrospectively
→ M15/H1 parent fitted afterward
```

Reason:

Historical replay에서 사후맞춤을 막고
live execution과 동일한 information order를 유지하기 위함이다.

---

## D-028 — Parent invalidation propagates downward

Status: ACTIVE

Causal ownership은 parent에서 child로 흐른다.

```text
parent invalidated
→ descendants invalidated
```

Final child가 완전히 consumed되면
그 child를 사용하는 current execution lane은 종료한다.

그러나 child consumption만으로
항상 HTF Root 전체를 구조적으로 invalid 처리하지는 않는다.

Root가 여전히 유효하다면
새로운 causal child가 별도 chain으로 형성될 수 있다.

Reason:

Root ownership과 execution precision zone lifecycle을
동일한 상태로 뭉개지 않기 위함이다.

---

## D-029 — Distance may enumerate but may not authorize refinement

Status: ACTIVE

Nearest-zone, narrowest-zone, RR-based 기준은
causal child authorization에 사용하지 않는다.

거리 기반 탐색은 계산량을 줄이기 위한
candidate enumeration 단계에서만 사용할 수 있다.

Final authorization은:

```text
same event
same displacement
same causal ownership
```

으로 결정한다.

Reason:

과거 `planner.py`의 후보 탐색 편의를
전략적 거래 권한으로 오해하지 않기 위함이다.

---
## D-030 — Source contact gates M1 trigger observation

Status: ACTIVE

Final refined source와 price가 실제로 교차하기 전에는
현재 scenario의 M1 trigger chain을 활성화하지 않는다.

```text
source contact
→ sweep search enabled
```

Source contact 자체는 entry signal이 아니다.

Reason:

HTF/LTF source가 실제로 반응할 위치에 도달하기 전에
M1의 unrelated noise/sweeps/CHoCH를 거래 근거로 사용하는 것을 방지하기 위함이다.

---

## D-031 — First-position sweep liquidity must pre-exist source contact

Status: ACTIVE

현재 first-position trigger에 사용할 liquidity pool은
source-contact bar가 시작되기 전에 이미 available해야 한다.

```text
liquidity.available_at
<
source_contact_bar_open
```

추가 N-bar/N-minute maturity threshold는 두지 않는다.

Maturity는:

```text
eligible structural family
+
causal pre-existence
+
unconsumed state
```

로 정의한다.

Reason:

현재 source reaction이 만든 새 고저점을
같은 setup의 원인 liquidity로 사후 재사용하는 것을 방지하면서
임의 age parameter도 피하기 위함이다.

---

## D-032 — Same-bar source contact and sweep are allowed

Status: ACTIVE

Final refined source contact와
pre-existing eligible liquidity sweep이
동일 M1 candle에서 발생하는 것은 허용한다.

```text
same-bar contact + sweep
→ allowed
```

단:

```text
same-bar liquidity creation + sweep
→ forbidden
```

이다.

Reason:

실전에서 source 진입과 liquidity raid가
한 candle의 동일 reaction으로 발생할 수 있기 때문이다.

---

## D-033 — Trigger-authorizing sweep must occur at the refined source

Status: ACTIVE

V1 first-position의 authorized sweep bar는
final refined source와 실제로 교차해야 한다.

```text
sweep bar intersects final source
```

Source를 과거에 touch한 뒤
가격이 source와 멀어진 곳에서 발생한 sweep을
원래 setup에 연결하지 않는다.

Reason:

`몇 bar 이내`, `몇 point 이내` 같은 임의 reaction-window parameter 없이
source-sweep causality를 보수적으로 유지하기 위함이다.

---

## D-034 — V1 sweep requires same-bar penetration and recovery

Status: ACTIVE

HIGH-side liquidity:

```text
high >= top + one_tick
AND
close <= top
```

LOW-side liquidity:

```text
low <= bottom - one_tick
AND
close >= bottom
```

을 V1 physical sweep으로 정의한다.

Body close beyond liquidity는
`BODY_DELIVERY`이며 sweep이 아니다.

Multi-bar reclaim은 V1 baseline에서 제외한다.

Reason:

Sweep event를 closed-bar basis에서 명확하고 재현 가능하게 만들고
복잡한 intrabar/multi-bar reclaim state machine을 초기 baseline에 도입하지 않기 위함이다.

---

## D-035 — Sweep penetration uses symbol tick, not arbitrary strength threshold

Status: ACTIVE

Liquidity outer boundary를 넘어가는 최소 유효 penetration은:

```text
one valid symbol tick
```

이다.

다음은 사용하지 않는다.

```text
ATR multiplier
fixed arbitrary point threshold
percentage threshold
sweep strength score
```

Reason:

실제 가격 최소 단위를 사용하면서
근거 없는 sweep-quality parameter를 추가하지 않기 위함이다.

---

## D-036 — Multiple eligible pools may authorize one sweep event

Status: ACTIVE

하나의 candle이 여러 eligible pre-existing liquidity pools를
동시에 sweep하면 모두 event ledger에 기록한다.

현재 scenario의 sweep condition은:

```text
at least one
direction-compatible
eligible
pre-existing
pool
```

이 valid sweep되면 충족한다.

Best-pool score 또는 strongest-pool selection은 사용하지 않는다.

Reason:

하나의 physical liquidity raid가
여러 structural pool을 동시에 소비할 수 있으며,
사후적으로 “가장 좋은” 하나를 골라 성과를 최적화하지 않기 위함이다.

---

## D-037 — Pre-contact sweep cannot be reused

Status: ACTIVE

Final refined source 접촉 이전에 완료된 liquidity sweep을
현재 first-position trigger chain의 sweep으로 재사용하지 않는다.

Required causal order:

```text
source contact
→ authorized sweep
→ M1 CHoCH
```

Reason:

이전의 unrelated sweep을 현재 source reaction에 사후 연결하는 것을 방지하고
manual replay와 live EA의 information order를 동일하게 유지하기 위함이다.

---
## D-038 — Meaningful M1 CHoCH breaks the correction's protected swing

Status: ACTIVE

V1 CHoCH reference는
sweep 뒤 가장 가까운 임의 pivot이 아니다.

LONG:

```text
bearish M1 correction
→ protected HIGH
→ bullish body-close break
```

SHORT:

```text
bullish M1 correction
→ protected LOW
→ bearish body-close break
```

을 요구한다.

Reason:

작은 M1 noise break를 execution reversal로 승격하지 않고
source로 들어오던 correction의 실제 protected structure가
무너졌음을 확인하기 위함이다.

---

## D-039 — CHoCH reference is frozen at the authorized sweep

Status: ACTIVE

Authorized sweep 시점에
현재 M1 correction structure의 protected swing을 snapshot한다.

Required:

```text
reference.available_at
<= sweep_bar_open
```

Sweep 이후 price action을 보고
더 쉬운 pivot으로 reference를 변경하지 않는다.

Protected reference가 없으면
해당 sweep chain은 first-position trigger를 authorize할 수 없다.

Reason:

CHoCH level의 retrospective fitting을 방지하기 위함이다.

---

## D-040 — M1 CHoCH requires body-close break

Status: ACTIVE

LONG:

```text
close > frozen protected HIGH
```

SHORT:

```text
close < frozen protected LOW
```

만 CHoCH로 인정한다.

Wick-only breach와 equality는 CHoCH가 아니다.

별도 ATR/N-point break-strength threshold는 사용하지 않는다.

Reason:

기존 structure contract와 일치시키면서
추가 임의 parameter 없이 structural delivery를 확인하기 위함이다.

---

## D-041 — Same-bar sweep and CHoCH are excluded from V1 baseline

Status: ACTIVE

V1은:

```text
choch_bar.index > sweep_bar.index
```

를 요구한다.

동일 M1 candle에서 sweep과 protected-swing body break가
모두 관측되어도 baseline first-position CHoCH로 사용하지 않는다.

Reason:

OHLC만으로 동일 candle 내부의
`sweep → recovery → CHoCH` 순서를 증명할 수 없기 때문이다.

향후 MT5 real-tick ordering을 이용한
별도 immutable variant에서 검토한다.

---

## D-042 — CHoCH waiting uses causal invalidation, not fixed timeout

Status: ACTIVE

Sweep 이후 CHoCH까지
고정 N-bar/N-minute timeout을 두지 않는다.

현재 trigger chain은 다음 causal event로 종료된다.

```text
final source invalidation
Root/parent owner invalidation
objective delivery before entry
final child full consumption
map owner invalidation
```

Reason:

근거 없는 시간 parameter를 추가하지 않고
scenario 자체의 원인이 사라질 때 setup을 종료하기 위함이다.

---

## D-043 — M1 CHoCH is execution confirmation, not HTF reversal authority

Status: ACTIVE

M1 meaningful CHoCH는
현재 frozen scenario의 실행 방향을 확인할 뿐이다.

M1 CHoCH만으로 H1/M30 external owner 또는 trend를
반전시키지 않는다.

External reversal은 별도의
H1/M30 protected structure body break와
new-direction owner confirmation이 필요하다.

Reason:

internal reaction과 external structural reversal을
혼동하지 않기 위함이다.

---

## D-044 — FVG and additional BOS are not mandatory CHoCH gates

Status: SUPERSEDED IN PART — 2026-08-15

Historical decision:

```text
authorized sweep
→ meaningful body-close CHoCH
→ causal execution OB
```

를 V1 first-position baseline으로 두고,
CHoCH FVG를 optional evidence로 취급했다.

Correction:

- FVG는 **CHoCH structure event 자체를 정의하기 위한 필수 조건은 아니다.**
- 그러나 V1 **first-position execution authorization**에는
  같은 sweep-to-CHoCH causal leg의 valid fresh same-direction FVG가 필요하다.
- additional BOS는 여전히 V1 baseline 필수 조건이 아니다.
- causal execution OB retest는 더 이상 V1 base first-position entry가 아니다.

Superseded by D-046 ~ D-053.

---

## D-045 — INITIAL_BOS cannot substitute for meaningful CHoCH

Status: ACTIVE

M1 directional correction structure가 아직 확립되지 않아
protected swing이 없는 상태에서 발생하는 `INITIAL_BOS`는
V1 first-position CHoCH를 대체하지 않는다.

```text
no protected correction swing
→ no meaningful CHoCH authority
```

Reason:

아무 첫 structure break를
sweep-confirmed reversal로 과대평가하지 않기 위함이다.

---

## D-046 — Initial mentor-style entry uses CHoCH displacement FVG, not OB retest

Status: ACTIVE

V1 최초 포지션의 기본 execution zone은
meaningful M1 CHoCH를 전달한 directional displacement가 생성한
fresh FVG다.

```text
source contact
→ mature sweep
→ meaningful M1 CHoCH
→ causal CHoCH displacement FVG
→ FVG retest
→ entry
```

Causal M1 OB는 displacement origin/lineage를 설명할 수 있으나
최초 포지션의 기본 entry price authority가 아니다.

Reason:

스승님의 실제 진입 설명을 재확인하면서
기존 `causal execution OB retest = base entry` 해석이
원전 매매법과 다르다는 점을 수정했다.

---

## D-047 — FVG is not required to define CHoCH, but is required for base entry

Status: ACTIVE

Meaningful M1 CHoCH 자체는
frozen protected swing의 body-close break로 정의한다.

그러나 first-position order authorization에는
그 CHoCH directional displacement가 생성한
valid causal FVG가 추가로 필요하다.

```text
CHoCH exists + no valid causal FVG
→ structure event exists
→ no base first-position order
```

---

## D-048 — Initial execution uses the standard causal three-candle FVG

Status: ACTIVE

Bullish FVG:

```text
Candle3.low > Candle1.high

bottom = Candle1.high
top = Candle3.low
width = top - bottom
```

Bearish FVG:

```text
Candle3.high < Candle1.low

bottom = Candle3.high
top = Candle1.low
width = top - bottom
```

Initial execution FVG는 authorized sweep 이후 형성되고,
meaningful CHoCH와 같은 방향이며,
동일 sweep-to-CHoCH causal M1 leg에 속해야 한다.

FVG가 CHoCH candle 자체를 반드시 포함할 필요는 없다.

---

## D-049 — Initial FVG entry uses the near-side boundary

Status: ACTIVE

LONG:

```text
entry = bullish FVG top
```

SHORT:

```text
entry = bearish FVG bottom
```

FVG midpoint/50%/CE와 execution-OB retest는
V1 base first-position entry에 사용하지 않는다.

Reason:

사용자가 스승님식 execution rule을 명시적으로 확정했다.

---

## D-050 — Initial FVG stop uses 20% external width buffer

Status: ACTIVE

```text
width = top - bottom
buffer = 0.20 * width
```

LONG:

```text
SL = bottom - buffer
```

SHORT:

```text
SL = top + buffer
```

즉 SL은 FVG distal boundary 바깥으로
FVG 전체 폭의 20%만큼 추가 여유를 둔다.

Broker spread / stops-level / Bid-Ask 제약과
전략 SL을 연결하는 방식은 execution infrastructure 단계에서 별도 확정한다.
그 전에는 위 전략 SL 공식을 임의 변경하지 않는다.

Reason:

사용자가 EA V1의 deterministic FVG-based SL geometry로 확정했다.

---

## D-051 — Executable CHoCH displacement requires a causal FVG

Status: ACTIVE

Meaningful M1 CHoCH 자체는 body-close structure event로 유효할 수 있다.

그러나 authorized sweep에서 CHoCH까지 이어지는
same-direction causal leg가 fresh FVG를 하나도 만들지 않았다면
V1 first-position executable displacement로 승인하지 않는다.

```text
meaningful CHoCH + no causal FVG
→ NO BASE ENTRY
```

별도의 ATR/body-size/consecutive-candle displacement score는 추가하지 않는다.

Reason:

천천히 진행된 structure break와
실제 imbalance를 남긴 directional displacement를 구분하면서
근거 없는 strength threshold를 추가하지 않기 위함이다.

---

## D-052 — Select the widest FVG in the CHoCH displacement

Status: ACTIVE

동일 authorized sweep → meaningful CHoCH causal leg 안에
valid FVG가 여러 개 존재하면:

```text
selected_FVG = argmax(top - bottom)
```

을 사용한다.

다음 기준은 사용하지 않는다.

```text
nearest
latest
first
source proximity
best RR
```

Symbol tick normalization 이후 최대 폭이 정확히 같은 FVG가
둘 이상 남으면:

```text
AMBIGUOUS_EXECUTION_FVG
→ NO TRADE
```

로 처리한다.

---

## D-053 — First touch of the selected FVG is the retest

Status: ACTIVE

Selected FVG와 meaningful CHoCH가 모두 available된 이후,
가격이 selected FVG와 처음 교차하는 것을
first retest로 정의한다.

```text
bar.high >= FVG.bottom
AND
bar.low <= FVG.top
```

FVG 생성 candle의 과거 intrabar movement나
order authorization 이전에 이미 지나간 touch를
사후 retest로 복원하지 않는다.

같은 first-position execution chain에서
두 번째 이후 touch를 재사용하지 않는다.

---

## D-054 — Delivery FVG replacement/add-on require re-audit after base-entry correction

Status: ACTIVE

기존 `DELIVERY_FVG_REPLACEMENT`와 `DELIVERY_FVG_ADDON` 계약은
과거 OB-first-entry baseline을 전제로 작성된 부분이 있다.

최초 포지션 기본형이 `INITIAL_CHOCH_FVG`로 정정되었으므로
두 후속 execution protocol의 시작 조건과 SL 계약은
별도 감사 전까지 V1 주문 권한을 비활성으로 둔다.

기존 문서 내용은 역사/연구 기록으로 보존하며
재감사 전 임의로 새 baseline에 맞춰 재작성하지 않는다.

## D-055 — FVG becomes available only after Candle3 closes

Status: ACTIVE

A three-candle FVG becomes usable only after Candle3 is fully closed.

FVG.available_at = Candle3 close

An in-progress Candle3 cannot create an execution candidate.

---

## D-056 — Initial FVG candidate set freezes at meaningful CHoCH close

Status: ACTIVE

Meaningful M1 CHoCH를 만든 candle이 close되는 순간
현재 first-position candidate set을 freeze한다.

Eligible candidate는 그 시점까지:

already available
same causal sweep-to-CHoCH leg
same direction
not previously retested
not consumed / invalidated

이어야 한다.

그 시점의 valid FVG 중 가장 넓은 FVG를 선택한다.

CHoCH close 이후 형성되는 FVG는
현재 candidate set에 추가하지 않으며
selected FVG를 교체하지 않는다.

---

## D-057 — Pre-authorization FVG retest makes the FVG ineligible

Status: ACTIVE

Available FVG가 meaningful CHoCH close 전에
이미 retest / fill / consumption을 겪었다면
현재 first-position candidate에서 제외한다.

과거 retest를 authorization 이후
사후 entry로 복원하지 않는다.

---

## D-058 — Baseline entry is an exact FVG-boundary pending limit

Status: ACTIVE

LONG:
BUY_LIMIT at bullish FVG.top

SHORT:
SELL_LIMIT at bearish FVG.bottom

V1 baseline은 strategy entry에 spread offset을 적용하지 않는다.

Spread-aware pending-price adjustment는
향후 별도 optimization variant로 비교한다.

---

## D-059 — V1 has no time-based pending cancellation

Status: ACTIVE / FROZEN

V1 pending order는
시간 경과만으로 취소하지 않는다.

사용하지 않는다.

N-bar timeout
N-minute timeout
session-close timeout
day-change timeout
next-day automatic cancellation
arbitrary pending-age limit

Pending order의 생존 여부는
elapsed time이 아니라
scenario의 causal validity로 결정한다.

따라서:

time_based_strategy_cancellation = NONE

MT5 pending order는:

ORDER_TIME_GTC

를 사용한다.

Pending cancellation authority는
EA_SPEC Section 11.9의 causal invalidation events에만 있다.

Reason:

이미 objective, Root/owner, source,
trigger structure, selected FVG 등
시나리오의 실제 원인이 명시적으로 관리되고 있으므로
단순 시간 경과를 별도의 무효화 이유로 추가할 근거가 없다.

---

## D-060 — Tick size defines executable price granularity

Status: ACTIVE

MT5 executable price는
SYMBOL_TRADE_TICK_SIZE를 기준으로 검증한다.

Entry boundary는 floating-point cleanup을 넘어
경제적 가격을 이동해서 맞추지 않는다.

20% FVG-width SL은 stop을 좁히지 않는 방향으로 normalize한다.

LONG:
greatest valid tick <= raw SL

SHORT:
smallest valid tick >= raw SL

---

## D-061 — Broker minimum-distance constraints do not redefine strategy geometry

Status: ACTIVE

Frozen entry / SL / TP가
SYMBOL_TRADE_STOPS_LEVEL 등 broker constraint를 만족하지 못하면:

EXECUTION_INFEASIBLE
→ NO ORDER

로 처리한다.

Entry, selected FVG, 20% strategy SL 또는 objective를
broker constraint 통과 목적으로 임의 변경하지 않는다.

---

## D-062 — Bid / Ask execution semantics are explicit

Status: ACTIVE

BUY_LIMIT:
Ask-side execution semantics

SELL_LIMIT:
Bid-side execution semantics

LONG SL:
Bid-side execution

SHORT SL:
Ask-side execution

Execution-sensitive event에서
Bid와 Ask를 모두 기록한다.

---

## D-063 — Pending orders use GTC and causal cancellation only

Status: ACTIVE / FROZEN

V1은 time-based strategy cancellation을 사용하지 않는다.

따라서 MT5 pending order는:

ORDER_TIME_GTC

를 사용한다.

Broker expiration time을 두지 않는다.

Scenario의 causal state가 살아 있는 동안
pending order를 유지한다.

EA_SPEC Section 11.9의
causal cancellation event가 발생하면
EA가 pending order 삭제를 요청한다.

Reason:

MT5 order lifetime과
strategy invalidation을 분리하고,
시간 경과 자체가 전략 근거를 무효화하지 않도록 하기 위함이다.

---

## D-064 — Broker cancellation failure is execution divergence

Status: ACTIVE

Strategy cancellation 뒤
FreezeLevel/server restriction 때문에
pending order 삭제가 실패하면:

strategy = CANCELED
execution = CANCEL_REJECTED_BY_BROKER

로 기록한다.

그 주문이 이후 체결되면:

EXECUTION_DIVERGENCE

로 분류하고
strategy-parity performance에서 제외한다.

---

## D-065 — Execution layer fails instead of silently repairing strategy geometry

Status: ACTIVE

OrderSend 전에
tick grid, Bid/Ask legality, StopsLevel,
trade mode, volume, margin/request feasibility를 검증한다.

Frozen strategy geometry가 실행 불가능하면:

EXECUTION_INFEASIBLE

로 종료한다.

Execution layer는:

selected FVG
entry boundary
20% FVG-width SL
objective

를 자동 수정하지 않는다.

## D-066 — 1R is objective-candidate eligibility

Status: ACTIVE / FROZEN

V1에서 planned R >= 1은
trade 전체를 첫 가까운 liquidity에서 즉시 거부하는 조건이 아니다.

Scenario scope에 의해 사전에 frozen된 liquidity candidate 중
final TP 자격을 판정하는 minimum-delivery 조건이다.

planned R < 1인 valid liquidity는
INTERMEDIATE_DELIVERY로 유지한다.

Reason:

현재 전략은 directional delivery를 거래하므로
너무 가까운 liquidity를 final trend objective로 사용하지 않되,
그 liquidity 하나 때문에 전체 POI/scenario를 즉시 폐기하지 않기 위함이다.

---

## D-067 — Objective family freezes before Entry/SL geometry

Status: ACTIVE / FROZEN

Scenario PLAN 단계에서
objective candidate family와 candidate order를 freeze한다.

Entry / SL 확정 뒤에는
새 liquidity candidate를 추가하거나
better-R candidate를 삽입하지 않는다.

Final TP 하나는 Entry / SL geometry가 알려진 뒤
pre-frozen family에서 선택한다.

Reason:

planned R 계산에는 Entry와 SL이 필요하지만,
그 정보를 본 뒤 TP 후보 자체를 새로 찾으면
hindsight RR optimization이 되기 때문이다.

---

## D-068 — Nearest R-eligible candidate wins

Status: ACTIVE / FROZEN

같은 candidate tier에서는
planned R >= 1인 candidate 중
trade direction으로 가장 가까운 valid liquidity를 final TP로 선택한다.

더 큰 R을 제공한다는 이유만으로
더 먼 candidate를 선택하지 않는다.

---

## D-069 — Scenario scope outranks R

Status: ACTIVE / FROZEN

R이 크더라도 scenario scope 밖 liquidity를 TP로 사용하지 않는다.

INTERNAL_ROTATION:
mature M15+ internal liquidity only.

EXTERNAL_CONTINUATION / EXTERNAL_REVERSAL:
external objective family.

INTERNAL_ROTATION은
1R을 만들기 위해 external H1 liquidity로 확장하지 않는다.

---

## D-070 — Historical H1 fallback is pre-frozen and external-only

Status: ACTIVE / FROZEN FOR STRATEGY

External scenario는 current-structure family 바깥 방향의
가장 가까운 causally-known 미소진 H1 external liquidity
최대 2개를 PLAN 시점에 inactive fallback으로 freeze할 수 있다.

Fallback은:

EXTERNAL_CONTINUATION
EXTERNAL_REVERSAL

에서만 허용한다.

INTERNAL_ROTATION에서는 금지한다.

Current-structure tier에 R-eligible candidate가 있으면
fallback을 사용하지 않는다.

Historical reconstruction depth 자체는
warm-up infrastructure decision으로 분리한다.

---

## D-071 — No post-selection objective rollover

Status: ACTIVE / FROZEN

Final TP가 pending submission 전에 선택된 뒤에는
같은 scenario에서 다음 family member로 자동 교체하지 않는다.

Selected objective가 fill 전에 delivered되면:

CANCELED_OBJECTIVE_DELIVERED

이다.

새 objective는 새 map/scenario evaluation을 요구한다.

---

## D-072 — Exact structural liquidity is baseline TP

Status: ACTIVE / FROZEN

V1 strategy TP는 selected liquidity의
actual structural price를 사용한다.

Swing liquidity는 actual wick price를 사용한다.

Baseline에서 spread/1-tick TP front-run을 사용하지 않는다.

LONG TP는 Bid-side,
SHORT TP는 Ask-side execution semantics를 따른다.

Front-run은 향후 별도 immutable execution optimization variant로만 검토한다.

## D-073 — Three-candle waves are swing candidates, not trend states

Status: ACTIVE / FROZEN

The three-candle detector confirms wave highs/lows only.

Confirmed wave creation does not automatically create:

external swing
protected swing
directional trend

Reason:

Internal waves must coexist inside an external trend without flipping the external map.

---

## D-074 — Initial external trend requires a two-sided confirmed range

Status: ACTIVE / FROZEN

Before INITIAL_BOS, both a confirmed swing high and confirmed swing low must already be available.

Bullish initialization:

body close above range high
→ BULLISH
→ opposite range low becomes protected low

Bearish initialization:

body close below range low
→ BEARISH
→ opposite range high becomes protected high

A directional state without a valid opposite protected boundary is forbidden.

---

## D-075 — Protected swing is the BOS-producing correction extreme

Status: ACTIVE / FROZEN

The protected swing is not the latest opposite swing.

At bullish BOS:

correction window
= broken external high occurrence → BOS close

eligible lows
= confirmed / available lows inside that window

new protected low
= lowest eligible low

At bearish BOS:

correction window
= broken external low occurrence → BOS close

eligible highs
= confirmed / available highs inside that window

new protected high
= highest eligible high

If no eligible correction swing exists, retain the previous protected swing.

---

## D-076 — Protected promotion uses only BOS-time available information

Status: ACTIVE / FROZEN

A swing whose price occurred before BOS but whose confirmation becomes available only after BOS cannot retroactively become the protected swing for that BOS.

Reason:

Prevent look-ahead and historical structure rewriting.

---

## D-077 — External trend invalidation enters TRANSITION before a new mature opposite state

Status: ACTIVE / FROZEN

Body-close break of the current protected swing immediately invalidates the old external trend.

However, V1 does not fabricate a complete opposite mature trend when the new opposite protected boundary is not yet deterministic.

State:

old directional trend
→ protected body break
→ TRANSITION

New BULLISH / BEARISH state requires a valid new two-sided structure and body-close directional confirmation.

---

## D-078 — External/internal importance is structural-role based, not size-threshold based

Status: ACTIVE / FROZEN

V1 does not use ATR, minimum points, percentage retracement, or minimum bar-count thresholds to decide whether a confirmed wave is external.

External role comes from:

directional external boundary
protected causal correction role
BOS/CHoCH structure relationship

All other confirmed waves remain internal by default.