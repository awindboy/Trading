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

Status: ACTIVE / FROZEN

V1 first-position Root uses the `LAST_OPPOSITE_OB` family
only after all causal filters pass:

```text
meaningful swing ownership
same causal leg
valid opposite candle
meaningful structure body-break
scenario/objective direction alignment
strategy_state = ACTIVE
```

`FVG_ORIGIN_OB` and HTF FVG-only source authority are excluded.

No separate Root freshness score/state exists.

---

## D-020 — Root validity uses ACTIVE / INVALIDATED only

Status: ACTIVE / FROZEN
Supersedes the old full-consumption lifecycle wording.

Bullish Root:

```text
own-TF close < bottom
→ INVALIDATED
```

Bearish Root:

```text
own-TF close > top
→ INVALIDATED
```

Owner/causal-structure invalidation also invalidates the Root.

Touch, partial mitigation, and wick-only distal penetration
are audit facts and do not create additional Root strategy states.

No N-touch/N-bar/age/quality expiry is used.

---

## D-021 — Root bounds remain full candle as source context

Status: ACTIVE / SOURCE-REFINEMENT WORDING SUPERSEDED BY D-124

HTF Root OB의 initial bounds는 origin candle의 전체 wick range다.

```text
bottom = low
top = high
```

Root 단계에서 body-only 또는 50% geometry로 축소하지 않는다.

Root는 full-candle bounds를 가진 strategy source/context로 유지한다. Optional post-contact child가 보여도 Root source bounds를 strategy authority로 대체하지 않는다.

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

Status: SUPERSEDED IN TEMPORAL OWNERSHIP BY D-122

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

Status: ACTIVE FOR NON-DISTANCE PRINCIPLE / TEMPORAL LINEAGE SUPERSEDED BY D-122

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

Status: SUPERSEDED BY D-124 FOR CURRENT V1 STRATEGY AUTHORITY

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

Status: SUPERSEDED BY D-124

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

Status: SUPERSEDED BY D-122 / D-124 FOR STRATEGY AUTHORITY

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

Status: HISTORICAL CHILD-LINEAGE RULE / ROOT INVALIDATION PRINCIPLE RETAINED

```text
parent invalidated
→ descendants invalidated
```

Child strategy validity uses the same exact rule as D-090:

```text
own-TF adverse body-close through distal
or
parent/owner invalidation
```

There is no independent `final child full consumption` strategy state.

If an old child is invalidated while the Root remains ACTIVE,
a later newly formed causal child may become a new lineage object.

The invalidated child is never revived.

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

Status: SUPERSEDED BY ROOT-CONTACT AUTHORITY UNDER D-122 / D-124

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

## D-031 — First-position sweep liquidity must pre-exist the relevant Root-reaction sweep event

Status: REQUIRES ROOT-BASED TIMING RE-AUDIT UNDER D-124

현재 first-position trigger에 사용할 liquidity pool의 정확한 freeze anchor는 corrected Phase 4C에서 Root contact/reaction 기준으로 재감사한다.

Child availability는 이 timing anchor가 아니다.

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

## D-032 — Same-bar Root contact and sweep require causal-order re-audit

Status: RESOLVED FOR CURRENT CLOSED-BAR BASELINE BY D-126 / TICK-ORDER VARIANT OPEN

HTF Root contact와 pre-existing eligible liquidity sweep이 동일 M1 candle에서 함께 관찰될 수 있다. D-126 current closed-bar baseline은 OHLC만으로 `contact → sweep` intrabar ordering을 증명할 수 없으므로 **동일 Root-contact bar의 strategic sweep authorization을 fail-closed로 금지**한다. Tick-order evidence를 별도로 구현하는 future variant에서만 재검토할 수 있다.

Child의 존재 여부는 이 판단에 영향을 주지 않는다.

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

## D-033 — Trigger-authorizing sweep must belong to the Root reaction context

Status: SUPERSEDED IN SOURCE OWNERSHIP BY D-124 / TIMING RE-AUDIT REQUIRED

V1 first-position의 authorized sweep은 specific HTF Root reaction context에 귀속되어야 한다.

Old `final refined source` intersection requirement is superseded because optional child never becomes strategy source.

Root를 과거에 touch한 뒤 전혀 별개의 가격 사건에서 발생한 sweep을 원래 setup에 사후 연결하지 않는다.

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

## D-037 — Pre-Root-contact sweep cannot be reused

Status: ACTIVE / ROOT-BASED UNDER D-124

Qualifying HTF Root contact 이전에 완료된 liquidity sweep을
현재 first-position trigger chain의 sweep으로 재사용하지 않는다.

Required causal order:

```text
Root contact
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

## D-042 — CHoCH waiting uses causal invalidation, not timeout

Status: ACTIVE / FROZEN

The active pre-CHoCH chain ends when:

```text
final source INVALIDATED
required Root/parent owner INVALIDATED
final objective delivered
scenario direction authority revoked
```

`final child full consumption` is not an independent strategy state.

Source/child validity is defined by D-090.

No N-bar/N-minute timeout is used.

---

## D-043 — M1 CHoCH confirms execution but does not create HTF reversal permission

Status: ACTIVE / FROZEN

M1 meaningful CHoCH alone cannot:

```text
open HTF reversal permission
flip H1 trend_state
create EXTERNAL_REVERSAL from nothing
```

However, when HTF reversal permission is already OPEN
from the active H1 reversal-reference interaction,
a valid opposite M1 CHoCH may confirm execution
for an early EXTERNAL_REVERSAL scenario.

Thus:

```text
M1 CHoCH alone
→ no HTF reversal authority

HTF permission
+ valid opposite context/source
+ M1 CHoCH
→ early reversal execution confirmation allowed
```

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
Root contact
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

Broker Bid/Ask, tick-grid, StopsLevel, FreezeLevel,
GTC and execution-feasibility handling are frozen by
D-060 through D-065, D-099 through D-101, and EA_SPEC Section 11.

Those constraints never redefine the 20% strategy SL geometry.

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

Status: RESEARCH-ONLY / INACTIVE IN V1

기존 `DELIVERY_FVG_REPLACEMENT`와 `DELIVERY_FVG_ADDON` 계약은
과거 OB-first-entry baseline을 전제로 작성된 부분이 있다.

최초 포지션 기본형이 `INITIAL_CHOCH_FVG`로 정정되었으므로
두 후속 execution protocol의 시작 조건과 SL 계약은
별도 감사 전까지 V1 주문 권한을 비활성으로 둔다.

기존 문서 내용은 역사/연구 기록으로 보존하며
재감사 전 임의로 새 baseline에 맞춰 재작성하지 않는다.

---

## D-055 — FVG becomes available only after Candle3 closes

Status: ACTIVE

A three-candle FVG becomes usable only after Candle3 is fully closed.

FVG.available_at = Candle3 close

An in-progress Candle3 cannot create an execution candidate.

---

## D-056 — Initial FVG candidate set freezes at meaningful CHoCH close

Status: ACTIVE / FROZEN

At meaningful CHoCH close,
freeze all causal same-direction FVGs that:

```text
are already available
belong to the authorized sweep-to-CHoCH leg
have no PRE_SELECTION_RETEST
```

The exact pre-selection freshness rule is D-088.

Select the widest eligible FVG.

FVGs formed after CHoCH close cannot enter this candidate set.

---

## D-057 — Pre-selection overlap makes an FVG ineligible

Status: ACTIVE / FROZEN
Consolidated with D-088.

Starting from the next causal bar after FVG availability,
any FVG overlap before meaningful CHoCH close is:

```text
PRE_SELECTION_RETEST
→ candidate excluded
```

No 50%, partial-fill, distal, or generic consumption threshold is used.

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

Status: CONSOLIDATED INTO D-063

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

---

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

## D-068 — Nearest R-eligible candidate wins in the single frozen family

Status: ACTIVE / FROZEN

V1 has one frozen ordered objective family.

Scan nearest-first in trade direction.

The first valid candidate with:

```text
planned R >= 1
```

becomes Final TP.

No candidate tier, max-R selection, or farthest-target optimization is used.

---

## D-069 — Scenario scope outranks R

Status: ACTIVE / FROZEN

Current V1 active first-position scopes:

```text
EXTERNAL_CONTINUATION
EXTERNAL_REVERSAL
```

R이 크더라도
현재 scenario scope가 설명할 수 없는 liquidity를
TP로 사용하지 않는다.

`INTERNAL_ROTATION`은 current V1 first-position order scope가 아니다.

---

## D-070 — Historical H1 fallback is pre-frozen and restricted to H1-owned external scenarios

Status: SUPERSEDED BY D-092

An eligible H1-owned external scenario may freeze
up to the nearest two causally-known unconsumed H1 external liquidity candidates
outside the current-structure family
as an inactive historical fallback tier at PLAN time.

Allowed:

H1-owned EXTERNAL_CONTINUATION

HTF-confirmed EXTERNAL_REVERSAL
under a new mature H1 owner

Forbidden:

early LTF-led EXTERNAL_REVERSAL
while the old H1 owner is still active

M30-primary EXTERNAL_CONTINUATION

INTERNAL_ROTATION

Fallback candidate ID / price / order
must be frozen before Entry / SL geometry is known.

If the current-structure tier contains
any valid planned R >= 1 candidate,
historical fallback is not used.

Historical reconstruction depth itself
remains a separate warm-up infrastructure decision.

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

---

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

---

## D-079 — H1 is the parent owner only while H1 is mature directional

Status: ACTIVE / FROZEN

H1 BULLISH / BEARISH:
→ H1 is parent external owner and highest active map.

H1 NEUTRAL / TRANSITION:
→ H1 has no directional owner authority.

If H1 is non-directional and M30 is mature directional:
→ M30 may become temporary highest active directional map.

---

## D-080 — Opposite M30 under mature H1 is correction context by default

Status: ACTIVE / FROZEN

When H1 is mature directional,
an opposite mature M30 structure does not automatically create
an opposite first-position trading lane.

Before HTF reversal permission opens:

H1 direction
→ default first-position trade authority

opposite M30 direction
→ HTF internal correction context

H1 BULLISH + M30 BEARISH
does not by itself authorize SHORT.

H1 BEARISH + M30 BULLISH
does not by itself authorize LONG.

---

## D-081 — H1 owner invalidation terminates old-owner-dependent scenarios

Status: ACTIVE / FROZEN

H1 protected-swing body break:

old H1 owner = INVALIDATED
H1 = TRANSITION

The old H1 EXTERNAL_CONTINUATION scenario
cannot remain authorized under the invalidated owner.

Any opposite M30 structure that existed before reversal permission
does not retroactively become an old-owner INTERNAL_ROTATION trade.

An already-frozen early EXTERNAL_REVERSAL scenario
that was validly created after HTF reversal permission opened
is not retrospectively renamed or rewritten merely because
the H1 trend_state later enters TRANSITION.

Its own frozen causal lifecycle determines whether it survives.

New interpretations under the changed map
require a new scenario_id.

---

## D-082 — M30 may be the temporary primary map while H1 is non-directional

Status: ACTIVE / FROZEN

If H1 is NEUTRAL or TRANSITION and M30 is mature directional:

M30 = temporary highest active map
scope = EXTERNAL_CONTINUATION relative to M30

Use M30 dealing range and M30 external objective family.

Old H1 objective/range state is not inherited by this M30-primary scenario.

Any H4 long-horizon extension must satisfy D-105 and the current V1
H4 objective-extension contract; it is not an old-H1 fallback.

If H1 later becomes mature directional, the old M30-primary scenario is not silently inherited by H1.

---

## D-083 — External reversal permission opens at the active HTF directional extreme

Status: ACTIVE / FROZEN

Mature bullish H1:

current flow highest valid external high
→ reversal-reference BSL

Mature bearish H1:

current flow lowest valid external low
→ reversal-reference SSL

Price reaching that extreme opens
opposite-direction reversal permission.

Bullish:
high >= reference high
→ OPEN_FOR_SHORT

Bearish:
low <= reference low
→ OPEN_FOR_LONG

This does not flip H1 trend or authorize an order.

It only allows opposite LTF structure
to be evaluated as an external-reversal hypothesis.

---

## D-084 — V1 does not run ordinary opposing H1/M30 first-position lanes in parallel

Status: ACTIVE / FROZEN

The previous rule allowing:

H1-direction EXTERNAL_CONTINUATION
+
opposite M30 INTERNAL_ROTATION

as ordinary parallel first-position lanes is removed.

While reversal_permission = CLOSED:

only the mature H1 direction has first-position trade authority.

Opposite M30 remains correction context.

After reversal_permission = OPEN:

an opposite EXTERNAL_REVERSAL hypothesis may be created,
but it must satisfy its own complete causal chain.

This is a context-gated reversal exception,
not blind simultaneous hedging.

---

## D-085 — Reversal reference is the current trend-flow extreme, not the latest swing

Status: ACTIVE / FROZEN

Bullish:
highest valid structural external high of current H1 owner flow.

Bearish:
lowest valid structural external low of current H1 owner flow.

Lower highs do not replace a higher bullish reference.
Higher lows do not replace a lower bearish reference.

Protected swing:
→ trend invalidation

Reversal reference:
→ reversal-hypothesis permission

---

## D-086 — Touch, sweep, and continuation break are distinct extreme events

Status: ACTIVE / FROZEN

TOUCH:
price reaches reference
→ reversal permission opens

SWEEP_REJECTION:
wick penetrates reference and closes back inside
→ reversal/liquidity context evidence
→ no automatic order

CONTINUATION_BODY_BREAK:
body close beyond reference in current trend direction
→ terminate old reference watch
→ normal BOS lifecycle
→ future new causal extreme becomes next reference

No event alone bypasses the base execution chain.

---

## D-087 — Early external reversal may precede H1 trend-label flip

Status: ACTIVE / FROZEN

After HTF reversal permission opens,
opposite M30/LTF structure may support an EXTERNAL_REVERSAL scenario
while H1 trend_state still carries the old mature direction.

This is allowed only because
permission originated from the old trend's major external extreme.

Actual order still requires the frozen:
Root/source → contact → sweep → M1 CHoCH → FVG → entry chain.

---

## D-088 — Pre-selection FVG touch removes first-retest freshness

Status: ACTIVE / FROZEN

Starting from the next causal bar after FVG availability,
if price overlaps the FVG before meaningful CHoCH close:

PRE_SELECTION_RETEST
→ candidate excluded

No 50% or partial-fill threshold is used.

---

## D-089 — Selected FVG order is submitted in the CHoCH decision cycle

Status: ACTIVE / FROZEN

At meaningful CHoCH close:

eligible FVG snapshot
→ widest FVG freeze
→ Entry / SL / TP
→ preflight
→ pending submission

occur in the same EA decision cycle.

No strategic arming or periodic reapproval delay exists.

---

## D-090 — Source validity uses adverse body close through distal

Status: ACTIVE / FROZEN

Bullish Root / child:

own-timeframe close < bottom
→ invalidated

Bearish Root / child:

own-timeframe close > top
→ invalidated

Wick-only distal penetration does not invalidate the source.

Touch / partial mitigation are audit facts, not strategy states.

---

## D-091 — Strategy state is smaller than the audit ledger

Status: ACTIVE / FROZEN

Persistent first-position strategy state:

PLANNED
WAITING_TRIGGER
PENDING
FILLED
CANCELED
NO_TRADE

Source contact, sweep, CHoCH, FVG selection,
touch and mitigation details remain event-ledger fields
rather than separate strategy branches.

---

## D-092 — V1 uses one ordered objective family with no historical fallback tier

Status: ACTIVE / FROZEN

At PLAN time freeze all currently known:

causally-valid
unconsumed
scope-compatible
direction-ahead

objective candidates in nearest-first order.

Do not create:

CURRENT_STRUCTURE tier
HISTORICAL_H1_FALLBACK tier
maximum-two-candidate cap

After Entry / SL:
the first candidate with planned R >= 1 becomes Final TP.

---

## D-093 — INTERNAL_ROTATION is research-only in current V1 first-position authorization

Status: ACTIVE / FROZEN

Ordinary opposite-M30 structure under mature H1
is correction context.

Counter-HTF first-position permission requires
HTF reversal permission
and is classified as EXTERNAL_REVERSAL.

Therefore INTERNAL_ROTATION is not
an active V1 first-position scenario_scope.

---

## D-094 — Only one pre-CHoCH sweep/reference is active per scenario

Status: ACTIVE / FROZEN

A newer valid authorized sweep before CHoCH
replaces the active sweep/reference.

Older sweeps remain in the audit ledger
but do not create concurrent live strategy trigger chains.

---

## D-095 — Pending cancellation uses three causal survival authorities

Status: ACTIVE / FROZEN

Before fill:

final objective validity
required HTF Root validity
scenario-direction authority

are the only strategy-level survival authorities.

Under D-124, optional child validity is not part of pending survival authority.

Selected-FVG mitigation,
M1 trigger-state drift,
undefined source episodes,
periodic reapproval,
and elapsed time
do not add independent cancellation branches.

---

## D-096 — Disabled variants and Ground Truth orchestration are not baseline authority

Status: ACTIVE / FROZEN

Current deterministic V1 does not instantiate:

DELIVERY_FVG_REPLACEMENT
DELIVERY_FVG_ADDON
OB-only first entry
GT V2 / Gemini runtime states
API latency states
AI risk-slot arbitration

Historical contracts remain research history only.

## D-097 — Session boundaries do not reset or cancel V1 strategy state

Status: ACTIVE / FROZEN

Daily pause, session close, weekend,
or scheduled market closure alone does not:

cancel a scenario
cancel a valid pending
reset market structure
reset source lineage
reset active sweep/reference

V1 adds no session-time expiry.

---

## D-098 — An execution FVG must use clock-contiguous M1 bars

Status: ACTIVE / FROZEN

`INITIAL_CHOCH_FVG` requires:

Candle2.open_time
= Candle1.open_time + 60 seconds

AND

Candle3.open_time
= Candle2.open_time + 60 seconds

Otherwise:

SESSION_OR_DATA_GAP_FVG
→ candidate excluded

A market-closed price discontinuity is not
treated as CHoCH displacement FVG.

This continuity gate applies to the execution FVG,
not as a global market-structure reset.

---

## D-099 — Persistent GTC support is an execution prerequisite

Status: ACTIVE / FROZEN

Because V1 has no time/session pending expiration,
the symbol must support:

SYMBOL_EXPIRATION_GTC

and:

SYMBOL_ORDER_GTC_MODE == SYMBOL_ORDERS_GTC

before a first-position pending order is submitted.

If the broker/symbol uses daily pending deletion:

strategy signal may remain VALID
execution = EXECUTION_INFEASIBLE
→ NO ORDER

V1 does not recreate a broker-deleted pending
at the next session.

---

## D-100 — Gap fills use actual broker execution without strategy re-optimization

Status: ACTIVE / FROZEN

A server-accepted GTC limit order may activate
on the first available quote after a session gap.

Requested strategy Entry remains the frozen
strategy geometry.

Actual execution uses the broker deal price.

After a gap fill do not recalculate:

selected FVG
Entry authority
SL
TP
lot
planned-R authorization

Gap SL/TP execution likewise uses actual MT5
deal reason and deal price.

Normal market-gap execution is not automatically
EXECUTION_DIVERGENCE and remains in economic results.

---

## D-101 — A signal that cannot be submitted in its decision cycle is not delayed to the next session

Status: ACTIVE / FROZEN

If trading-session restrictions prevent
order submission in the CHoCH/FVG decision cycle:

EXECUTION_INFEASIBLE
→ NO ORDER

The EA does not queue the old signal
and place it after the market reopens.

A future order requires a new valid execution chain.


## D-102 — H4 is a long-horizon liquidity index, not an active trading map

Status: ACTIVE / FROZEN

H4 is permitted in V1 only as:

LONG_HORIZON_LIQUIDITY_INDEX

It may identify and maintain
ACTIVE H4 external-swing liquidity.

H4 does not authorize:

scenario direction
dealing range
reversal permission
Root/source
entry

H1/M30 remain the active trading map.

---

## D-103 — Historical bootstrap retains active meaning, not complete historical trees

Status: ACTIVE / FROZEN

Historical bars may be replayed,
but V1 does not permanently retain every historical:

swing
OB
FVG
CHoCH
trigger chain
source lineage

Only state that can still affect the current decision is retained.

---

## D-104 — Long-horizon H4 liquidity is restricted to EXTERNAL_SWING in V1

Status: ACTIVE / FROZEN

The V1 long-horizon archive stores only
H4 protected/external swing highs and lows.

It does not bootstrap H4:

FVG
OB
internal pivot archive
defended-range liquidity
structural-reaction liquidity

This keeps the historical memory minimal and explainable.

---

## D-105 — H4 objective candidates only extend beyond the current H1/M30 horizon

Status: ACTIVE / FROZEN

Current H1/M30 objective authority always comes first.

At PLAN:

```text
plan_reference_price
=
latest closed M1 close available at family freeze
```

Primary horizon:

```text
LONG  = highest current H1/M30 primary candidate
SHORT = lowest current H1/M30 primary candidate
```

If no primary candidate exists:

```text
primary_directional_horizon = plan_reference_price
```

H4 candidate representation:

```text
family = EXTERNAL_SWING
timeframe = H4
state = ACTIVE
```

It must lie beyond the primary horizon.

Allowed:

```text
EXTERNAL_CONTINUATION
EXTERNAL_REVERSAL after new opposite mature H1 owner
```

Forbidden:

```text
early EXTERNAL_REVERSAL while old H1 owner remains active
```

H4 never replaces an inside-horizon H1/M30 objective.

---

## D-106 — Lower-timeframe bootstrap is targeted to the current active Root/source

Status: ACTIVE / FROZEN

M30/M15/M5 historical reconstruction is not global.

After the current H1/M30 active map is reconstructed,
lower-TF replay is limited to causal windows needed
to resolve currently relevant ACTIVE Root/source lineage.

Old unrelated lower-TF zone trees are not retained.

---

## D-107 — Pre-start execution triggers are never carried into runtime orders

Status: ACTIVE / FROZEN

Warm-up may identify current market state and
pre-existing eligible liquidity.

But pre-start:

source-contact execution episode
sweep authorization
M1 CHoCH
execution FVG
pending hypothesis

cannot authorize a new runtime first-position order.

A new execution chain begins after execution_epoch_start.

---

## D-108 — Startup inside an eligible Root requires exit and later re-entry

Status: ACTIVE / ROOT-BASED UNDER D-124

If startup begins with current price already inside
the eligible HTF Root:

STARTED_INSIDE_ROOT

is recorded.

No retroactive contact is created.

A new first-position trigger chain requires:

exit
→ later re-entry
→ new Root contact

---

## D-109 — Bootstrap uses a compressed working set

Status: ACTIVE / FROZEN

Historical bars may be replayed without retaining
every historical object in active memory.

Keep an object in RAM only while referenced by:

current structure
open correction window
ACTIVE liquidity
ACTIVE Root/source
active scenario/CHoCH reference
H4 ACTIVE liquidity index

Resolved unreferenced objects may be written to
append-only audit storage and evicted from RAM.

---

## D-110 — V1 parity sizing uses broker minimum volume

Status: ACTIVE / FROZEN

Initial Strategy Tester implementation correctness uses:

sizing_mode = MINIMUM_VOLUME_PARITY
order_volume = SYMBOL_VOLUME_MIN

Volume min/max/step and margin/request feasibility must pass.

No arbitrary risk-percent input is part of V1 parity.

Performance comparison is primarily R-based until
a separate risk-sizing policy is approved.

---

## D-111 — V1 has one accepted first-position exposure per symbol and magic

Status: HISTORICAL / SUPERSEDED BY D-134

Per symbol + magic:

max one scenario per direction
max one accepted PENDING/FILLED exposure

An opposite EXTERNAL_REVERSAL watch scenario is allowed
only after reversal permission opens.

Once one order is accepted,
other first-position chains cannot submit until exposure is terminal.

Blocked old chains are not delayed/reused.

Simultaneous opposite authorization with no existing exposure:

NO_TRADE
reason = AMBIGUOUS_SIMULTANEOUS_AUTHORIZATION

---

## D-112 — Execution failure terminates that execution chain

Status: ACTIVE / FROZEN

If a valid strategy signal cannot be submitted in its decision cycle:

EXECUTION_INFEASIBLE
or
server REJECTED

then:

scenario_state = NO_TRADE

for that execution chain.

Do not retry the old signal on later ticks or sessions.

A future order requires a new causal execution chain.

---

## D-113 — Same-timestamp bar processing is higher timeframe first

Status: ACTIVE / FROZEN

When multiple closed bars become available at the same timestamp:

H4
→ H1
→ M30
→ M15
→ M5
→ M1
→ scenario/order authorization

Within each timeframe:

existing-object invalidation/consumption
→ structure update
→ new object availability
→ dependent authorization

This is a deterministic tie-breaker for simultaneously available information.

---

## D-114 — Broker transaction callback order is not execution causality

Status: ACTIVE / FROZEN

Do not rely on OnTradeTransaction callback arrival order.

Reconcile using:

request_id
order ticket
deal ticket
position ticket
current order/position state
broker history

Execution handlers must be idempotent.

---

## D-115 — Bootstrap discovers Roots before targeted refinement

Status: SUPERSEDED IN REFINEMENT TIMING BY D-122

Bootstrap order:

H4 index
→ H1/M30/M15 chronological Root-discovery stream
→ retain current relevant ACTIVE Roots
→ targeted M30/M15/M5 causal refinement
→ current-source local liquidity reconstruction
→ READY

M15 may detect Root candidates under H1/M30 causal context
without becoming an active map authority.

This removes circular dependency between
"known active Root" and lower-TF reconstruction.

---

## D-116 — Directional owner identity is the INITIAL_BOS event identity

Status: ACTIVE / IMPLEMENTATION-FROZEN

For H1/M30 deterministic owner bookkeeping:

```text
NEUTRAL / TRANSITION
→ INITIAL_BOS
→ mature directional owner
```

sets:

```text
owner_id = INITIAL_BOS structure event ID
owner_started_at = INITIAL_BOS available_at
```

Continuation BOS remains inside the same owner flow
and does not create a new owner ID.

Protected-swing body break:

```text
old owner invalidated
→ owner_id cleared
→ TRANSITION
```

A new mature direction receives a new owner ID only
after the next valid two-sided INITIAL_BOS.

Reason:

The frozen strategy refers to the "current H1/M30 owner flow".
Using INITIAL_BOS as the stable owner identity prevents
every continuation BOS from being misclassified as a new map owner.

---

## D-117 — Permission origin is preserved separately from the moving current reversal reference

Status: ACTIVE / IMPLEMENTATION-FROZEN

The current H1 reversal reference may move outward
when a new valid structural external extreme becomes causally available.

If reversal permission was already opened by an earlier:

```text
TOUCH
or
SWEEP_REJECTION
```

the causal event that opened that permission remains recorded as:

```text
permission_reference_id
permission_reference_price
permission_opened_at
permission_event_type
```

until the permission is closed.

The current map reference and the historical permission-opening reference
are separate audit identities.

This does not create a second trading authority or a score.

Permission still closes under the frozen:

```text
continuation body break
or
H1 owner invalidation/change
```

contract.

Reason:

Do not rewrite the causal origin of an already-open permission
when the current owner later publishes a farther external extreme.

---

## D-118 — Owner-compatible final objective primary liquidity uses current external-horizon `EXTERNAL_SWING`

Status: ACTIVE / IMPLEMENTATION-FROZEN

The frozen objective contract requires:

```text
current H1/M30 owner-compatible external liquidity
```

and separately states that internal liquidity between Entry and the final
external target must not be promoted to final external TP.

Phase 4B operationalizes that contract as follows.

Primary final-objective liquidity family:

```text
EXTERNAL_SWING
```

only.

H1-owned continuation:

```text
eligible TF = H1 or M30
```

but the candidate must be at or beyond the current H1 directional external boundary.

LONG:

```text
candidate.price >= current H1 external_high
```

SHORT:

```text
candidate.price <= current H1 external_low
```

M30-primary continuation and early reversal:

```text
eligible TF = M30
```

and the candidate must be at or beyond the current M30 directional external boundary.

This prevents an M30 external pool that is still internal to the active H1
directional horizon from being misclassified as a final H1 external objective.

`DEFENDED_RANGE_EDGE` and `STRUCTURAL_REACTION` remain valid liquidity families
for their frozen liquidity roles, but are not promoted into this final
external-objective primary family merely because they are direction-ahead.

H4 extension remains separately governed by the frozen:

```text
family = EXTERNAL_SWING
timeframe = H4
beyond primary_directional_horizon
```

contract.

No ATR, point-distance, RR, nearest-pivot, or score threshold is introduced.

Reason:

Use structural external ownership, not price proximity, to distinguish
final external objective candidates from internal delivery liquidity.

---

## D-119 — First-position liquidity eligibility uses a runtime M1 physical-consumption overlay

Status: IMPLEMENTATION CONCEPT RETAINED / ROOT-CONTACT ANCHOR REQUIRES D-124 RE-AUDIT

Phase 2 keeps its own-timeframe liquidity detector and audit events.

Phase 4C additionally requires first-position authorization to know whether a
cross-timeframe liquidity pool has already been physically swept or body-delivered
on a closed M1 bar before the relevant Root-reaction eligibility freeze.

Therefore runtime strategy eligibility maintains a separate overlay:

```text
liquidity_id
consumed_at
consumption_type:
    SWEEP
    BODY_DELIVERY
reason
```

Physical M1 geometry uses the frozen one-tick rules.

This overlay is used to:

```text
prevent pre-contact sweep reuse
exclude already physically consumed pools from contact-time eligible snapshots
exclude already consumed liquidity from future objective eligibility
```

It does **not** retrospectively rewrite the Phase 2 global audit event history.

Contact-time pool maturity remains:

```text
pool.available_at < source_contact_bar_open
```

and no age/ATR/quality score is introduced.

Reason:

A first-position sweep authorization is an M1 causal event. Waiting for a
higher-timeframe pool's own bar to close could leave a physically consumed pool
temporarily eligible and allow an old M1 sweep to be reused.

---

## D-120 — Structural Reaction requires post-contact M1 proof of the reaction extreme

Status: REQUIRES ROOT-BASED OWNERSHIP/TIMING RE-AUDIT UNDER D-124

A Phase 4C `STRUCTURAL_REACTION` pool requires:

```text
scenario-owned HTF Root
actual Root contact
compatible confirmed reaction wave on source timeframe
reaction confirmation after contact
```

A source-timeframe wave's `occurred_at` is the source bar's open timestamp.
The exact wick extreme may have formed later inside that bar.

Therefore, when the source-timeframe occurrence bar overlaps the contact time,
Phase 4C proves the reaction causally on M1:

```text
M1 available_at >= source_contact_at
M1 bar belongs to / intersects the relevant Root reaction geometry
M1 high/low equals the confirmed source-TF reaction extreme
```

Price equality uses only half a broker tick as a floating representation guard:

```text
abs(M1 extreme - source-TF extreme) <= 0.5 tick
```

This is not a trading-distance tolerance, quality filter, ATR threshold, or
adjacency rule.

Only after this proof and later reaction-wave confirmation is the
`STRUCTURAL_REACTION` pool made available.

The current scenario cannot use that newly created reaction pool for its same
first position because the scenario's eligible sweep-liquidity set was frozen
at the earlier source-contact bar.

Reason:

Do not label a source-TF reaction as post-contact merely because its wave was
confirmed after contact when its actual price extreme may have occurred before
contact.

---

## D-121 — Premium / discount is context-only and never a standalone veto

Status: ACTIVE / AUTHORITY-CORRECTION

The active H1/M30 dealing range and EQ remain deterministic map information.

For every candidate/scenario, the engine may record whether the source/context
is currently in premium or discount.

However:

```text
premium / discount
!= scenario authority
!= entry authority
!= standalone rejection authority
```

In particular, an `EXTERNAL_CONTINUATION` source on the opposite half of EQ
must not be rejected for that reason alone.

The source must still belong to the active map and satisfy the complete frozen
causal chain:

```text
objective
→ map/direction authority
→ pre-existing eligible Root
→ qualifying Root contact
→ mature Root-reaction sweep
→ meaningful M1 CHoCH
→ causal FVG
→ execution geometry
```

Reason:

The Mentor method uses PD Array as location/context reference. The previous V1
wording and implementation promoted it into a hard continuation veto, which
gave PD more authority than intended.

---

## D-122 — HTF Root contact precedes any causal LTF child observation

Status: ACTIVE / TEMPORAL AUTHORITY-CORRECTION; CHILD REQUIREMENT SUPERSEDED BY D-124

Current V1 separates the **formation of the HTF Root** from the **later formation of its LTF child**.

Required causal order:

```text
pre-existing eligible / unconsumed HTF Root
→ price later actually contacts that Root
→ lower-timeframe reaction begins after contact
→ M1 Root-reaction evaluation may proceed without any child
→ if a new LTF child OB later forms, it may be recorded only after its own causal structure delivery confirms it
→ that child remains optional audit/context information
```

Any optional current child observation must therefore satisfy:

```text
child.available_at > qualifying_root_contact_at
```

and must be attributable to the post-contact reaction.

The following are **not** valid current child refinement:

```text
an LTF OB that already existed before the HTF Root contact
an LTF OB found by decomposing the original displacement that created the Root
price-overlap-only historical nesting
retrospective selection of a Root after seeing the later M1 reaction
```

The HTF Root must be identified before the later reaction and must still be eligible for the intended first reaction. The term `unconsumed` is a Root-watch eligibility requirement; this decision does not invent an N-touch, age, percentage-mitigation, ATR, or score rule, and does not redefine ordinary wick/touch facts as body-close invalidation.

This decision supersedes the **temporal-order / ownership portions** of:

```text
D-023
D-024
D-025
D-026
D-027
D-030
D-032
D-033
D-115
```

and requires a timing re-audit before relying on the existing implementation details of:

```text
D-031
D-119
D-120
```

Those older decisions remain in this log as historical design records. Their non-conflicting principles — no distance/score selection, causal availability, parent invalidation propagation, physical sweep geometry, and no look-ahead — remain valid.

The old implementation concept:

```text
Root creation
→ historical child discovery inside the Root-forming displacement
→ child frozen
→ later refined-child contact
```

is no longer current strategy authority.

Reason:

The intended Mentor workflow is to keep valid, unconsumed HTF OBs on watch and wait for price to reach the HTF OB before evaluating its later reaction. If a lower-timeframe child is recorded, it must belong to that later reaction. Treating an older lower-timeframe candle from the Root's original displacement as a future post-contact child reverses causal order. D-124 further clarifies that child observation is optional and cannot gate the Root setup.

Implementation consequence:

Phase 3B refinement, Phase 4B scenario planning, and Phase 4C contact/sweep logic that depended on pre-contact child freeze or mandatory child authority must be reworked and revalidated before those phases can be considered strategy-parity PASS. Earlier test counts remain historical facts for the old implementation, not evidence of corrected V1 opportunity frequency.

---

## D-123 — D122A isolates physical Root-contact / post-contact-child causality from downstream strategy authorization

Status: ACTIVE / BASELINE CAUSAL PASS 2026-08-16 / REINTERPRETED BY D-124

D-122 changed temporal ordering enough that D122A isolated Root watch/contact and post-contact child observation before Phase 4B/4C were reattached. The 2026-08-16 baseline test passed that temporal-causality purpose. D-124 now clarifies that the child observation proven by this test is optional audit evidence rather than a required strategy gate.

The D122A implementation therefore remains useful as a causal validation fixture, not as proof that a child is required.

### Root watch eligibility

Root strategy state remains exactly:

```text
ACTIVE
INVALIDATED
```

D122A does **not** add a new Root strategy state such as `MITIGATED` or `CONSUMED`.

For the isolated D122A causality test only, bootstrap uses a conservative fail-closed first-reaction watch guard: a Root is not armed as a fresh Root watch if a fully closed M1 bar, causally after `Root.available_at`, has already intersected the Root wick range.

```text
closed M1 intersection after Root.available_at
→ not eligible for a new first-reaction Root watch
→ Root strategy_state itself remains ACTIVE unless the existing invalidation rule fires
```

This is an execution-watch eligibility distinction, not a rewrite of D-090 body-close invalidation. It is **not yet promoted into a general strategy definition of partial/full OB consumption**; that semantic remains outside D122A. The guard exists so the post-contact-child test does not knowingly treat an already revisited historical Root as a fresh first-reaction fixture.
No N-touch, mitigation percentage, age, ATR, point-distance, or quality score is introduced.

If startup begins inside an otherwise eligible Root, D122A does not synthesize a historical contact. It requires:

```text
exit Root
→ later closed-M1 re-entry
→ new runtime Root-contact observation
```

### Runtime Root-contact observation

A newly available runtime Root is registered only after the complete same-timestamp MTF processing group has finished.
This prevents price movement that occurred before Root availability from being reused as a same-timestamp self-contact.

D122A records a physical contact only from a newly closed M1 bar after both:

```text
Root.available_at
Root-watch registration time
```

and after `execution_epoch_start` when runtime execution has begun.

The D122A event is:

```text
ROOT_CONTACT_OBSERVED
```

and is intentionally logged with:

```text
strategy_authority = false
map_objective_qualification = DEFERRED_PHASE4B
```

because Phase 4B must later decide whether the watched Root has full map / direction / objective authority.
D122A validates temporal causality, not final trade authorization.

### Post-contact child causality

At Root contact, D122A snapshots the causally known M30/M15 structure state and reconstructs M5 **structure-only** context through the contact timestamp. That M5 reconstruction may establish prior structure context but may not publish any historical child/source authority.
Only subsequently closed M30/M15/M5 bars may advance that Root's private reaction state for child authorization.

A candidate child fails closed unless its causal evidence is strictly after the current parent anchor.
For the first child the anchor is the Root contact; for a deeper child it is the direct parent's `available_at`.

Required:

```text
structure_event.available_at > causal_anchor
break_bar.open_time >= causal_anchor
meaningful_reaction_wave.available_at > causal_anchor
meaningful_reaction_wave.occurred_at >= causal_anchor
child_origin_bar.open_time >= causal_anchor
```

A lower-TF bar that opened before the anchor is not used to prove a post-anchor child because OHLC alone cannot establish the intrabar ordering.

The existing deterministic OB recognizers remain separate:

```text
LAST_OPPOSITE_OB            → always enabled baseline recognizer
FVG_ORIGIN_OB               → only when the existing experiment toggle is true
```

If both recognize the same physical child candle, geometry is deduplicated and the recognition reasons are merged.
Distinct physical child candidates remain distinct; no score or RR selection is added.

Full containment is preferred. If the post-contact meaningful reaction wave itself intersects the current parent source, the existing event-defined adjacency principle may admit a boundary-crossing child without any fixed point/ATR tolerance.

### Child invalidation

D-028 remains active:

```text
child invalidated while Root remains ACTIVE
→ invalidated child is not revived
→ lineage rolls back to the nearest still-active parent
→ a later newly formed post-contact child may be discovered
```

Root invalidation still invalidates the whole descendant lineage.

### Explicitly disabled downstream authority

D122A intentionally does not run the superseded Phase 4B/4C authorization path.
Until the unresolved Section 6 timing questions are frozen, the following are disabled as strategy-authorizing runtime paths:

```text
SCENARIO_PLANNED
old final-source SOURCE_CONTACT
eligible sweep snapshot freeze
AUTHORIZED_SWEEP
STRUCTURAL_REACTION strategy ownership
meaningful M1 CHoCH
entry / order submission
```

The Phase-2 physical liquidity detector and sweep/body-delivery audit geometry remain intact.

Reason:

The corrected Root-contact → child order must first be proven independently. Reattaching objective, sweep, CHoCH, and order logic in the same change would mix a known authority correction with still-unresolved timing choices and make failures impossible to attribute cleanly.

### 2026-08-16 D122A baseline result

```text
repository commit = 5693058733b63089ad7e612281ce58a7623c73e3
internal build = 0.80
fvg_origin_ob_experiment = false
event rows = 7067
ROOT_WATCH_CREATED = 21
ROOT_CONTACT_OBSERVED = 11
CHILD_CREATED = 1
SCENARIO_PLANNED = 0
old Phase4C SOURCE_CONTACT = 0
AUTHORIZED_SWEEP = 0
orders/deals = 0
```

Observed child causality:

```text
03:45 Root contact
→ 03:55 child origin
→ 04:00 meaningful M5 reaction low
→ 04:15 wave available
→ 04:45 M5 INITIAL_BOS bar
→ 04:50 child available
```

All 11 Root contacts occurred after Root availability and the execution epoch. Historical pre-contact child authorization was zero. Structure, liquidity, map/reversal, and Root detector events were exactly row-identical to the prior `fvg_origin_ob_experiment=false` control run.

Under D-124 this result is interpreted as:

```text
11 Root-contact contexts remained valid candidates for downstream Root-based evaluation
1 optional post-contact child happened to be observed
10 missing children are NOT trade rejections
```

---

## D-124 — HTF Root is the sole OB strategy source; post-contact child is audit-only optional context

Status: ACTIVE / CURRENT V1 AUTHORITY-CORRECTION

Current V1 first-position baseline no longer requires a causal LTF child OB.

Required OB/source path:

```text
pre-existing eligible HTF Root
→ actual HTF Root contact
→ Root-reaction sweep
→ meaningful M1 CHoCH
→ causal M1 FVG
→ widest valid FVG first retest
```

A post-contact LTF child may still be observed, but only as audit/context information.

```text
no child
→ Root setup continues

one child
→ log child; Root remains strategy source

multiple children / ambiguous children
→ log what is causally knowable; do not choose a best child; Root remains strategy source

child invalidated while Root ACTIVE
→ audit fact only; Root setup continues
```

The child has no authority over:

```text
scenario authorization
trade veto
strategy-source replacement
Entry
SL
TP
pending cancellation
Root invalidation
sweep eligibility
CHoCH authorization
```

Actual first-position execution geometry remains the already-frozen M1-FVG contract:

```text
LONG Entry = selected bullish FVG.top
LONG SL    = selected FVG.bottom - 0.20 * FVG.width

SHORT Entry = selected bearish FVG.bottom
SHORT SL    = selected FVG.top + 0.20 * FVG.width
```

Therefore a narrower child does not tighten the baseline stop and is not needed for entry precision.

D-122 temporal causality remains active for any optional child observation:

```text
Root contact must precede child formation/availability
pre-contact historical LTF OB may not be relabeled as a post-contact child
```

D-124 supersedes current-strategy authority portions of:

```text
D-025 deepest-child final-source rule
D-026 mandatory-child rule
D-027 mandatory child-lineage freeze before M1
D-028 descendant strategy-authority consequence, except Root invalidation itself
D-030 refined-source contact gate
all later rules that require a child before sweep / CHoCH / Entry
```

Reason:

The baseline already performs its decisive execution filtering later through Root reaction, valid sweep, meaningful M1 CHoCH, and causal FVG first-retest geometry. Requiring an additional child OB at the source layer removes Root reactions before those intended confirmation stages and grants the child more authority than the strategy needs.

---

## D-125 — Corrected Phase 4B freezes each Root scenario and objective family before Root contact

Status: ACTIVE / PHASE 4B VALIDATED — 2026-08-16

D-124 establishes the HTF Root as the sole OB strategy source. Corrected Phase 4B therefore prepares strategy state around the **physical Root itself**, not around any child/refinement lineage.

Required order for a Root contact to belong to a strategy scenario:

```text
causally known active H1/M30 map
+
causally known objective family
+
pre-existing ACTIVE HTF Root
→ Root-specific PLAN frozen
→ objective family frozen
→ later qualifying Root contact
```

Required strict timing:

```text
scenario.frozen_at < qualifying_root_contact_at
```

A PLAN created at the same timestamp as the contact is not accepted for that contact. It is canceled fail-closed rather than surviving as a retrospective scenario.

### Independent physical Root candidates

Each distinct physical Root is evaluated independently.

```text
Root A under map X
Root B under map X
→ two independent Root candidates
```

The engine must not collapse them into one shared-context ambiguity veto.

Forbidden:

```text
multiple valid Roots in same map
→ AMBIGUOUS_ROOT_LINEAGE
→ reject all
```

Also forbidden:

```text
choose nearest Root
choose latest Root
choose narrowest Root
score Roots
choose highest RR Root
```

A Root receives a PLAN only if that Root itself is compatible with the current frozen map/direction/scope and has at least one valid objective-family candidate under the existing objective rules.

### Map / scope qualification

Corrected Phase 4B reuses the already-frozen map authority:

```text
mature H1 + reversal permission CLOSED
→ H1 EXTERNAL_CONTINUATION
→ Root direction must match H1

mature H1 + reversal permission OPEN
+ mature opposite M30 matching permission
→ M30-led EXTERNAL_REVERSAL

H1 not mature
+ mature M30
→ M30-primary EXTERNAL_CONTINUATION
```

The Root must belong to the active map range. Premium/discount remains context-only and cannot veto the Root.

### Objective family

Objective-family construction keeps the frozen V1 contract:

```text
causally known
unconsumed
trade-direction ahead
scope compatible
nearest-first ordered family
```

H1-led continuation may use current H1/M30 primary external liquidity.
M30-primary continuation and early reversal use M30 primary external liquidity.
Eligible H4 liquidity remains extension-only under the existing H4 rules.

`planned R >= 1` is **not** evaluated at Phase 4B because Entry/SL do not exist yet. Final TP eligibility remains deferred until M1 FVG Entry/SL geometry exists.

### No retrospective plan

A physical Root contact without an already-valid pre-contact PLAN remains a valid physical Root-contact audit event, but that contact cannot later be backfilled into a strategy scenario.

```text
Root contact
+
no PLAN frozen strictly before contact
→ ROOT_CONTACT_WITHOUT_PREPLAN
→ no retrospective scenario for that contact
```

If a pre-contact PLAN is canceled because its map owner or reversal authority becomes invalid **before contact**, the still-ACTIVE and still-uncontacted Root may later receive a new PLAN only if a new valid map/objective context becomes causally available before its eventual contact.

### Root remains the source

For every Phase 4B PLAN:

```text
strategy_source_id = Root.id
strategy_source_kind = ROOT
child_required = false
```

Optional children remain D-124 audit/context only and cannot create, replace, select, cancel, or veto the PLAN.

### Phase 4C remains disabled

This decision does **not** resolve `EA_SPEC` Section 6.6.

Build D-125 may maintain the D-119 M1 physical-consumption overlay so an already consumed liquidity pool is not newly frozen into a later objective family, but it must not authorize a strategic sweep.

After Root contact, a successfully preplanned scenario enters:

```text
WAITING_SWEEP
```

not `WAITING_TRIGGER`.

The following remain disabled until corrected Phase 4C freezes Root-reaction sweep ownership:

```text
eligible sweep-pool snapshot
AUTHORIZED_SWEEP
STRUCTURAL_REACTION strategy ownership
meaningful M1 CHoCH authorization
FVG / order execution
```

Reason:

Phase 4B can be corrected deterministically from the already-frozen Objective → Map → Root → Contact order without inventing the unresolved sweep-freeze contract. Keeping Phase 4C disabled isolates this correction and prevents another timing rule from being guessed.

### 2026-08-16 validation result

Build `0.90 / D125_ROOT_PRECONTACT_SCENARIO_OBJECTIVE_CORE` passed the corrected
Phase 4B causal smoke on the January 2025 fixture.

```text
SCENARIO_PLANNED = 13
OBJECTIVE_CANDIDATE_FROZEN = 91
SCENARIO_ROOT_CONTACT_BOUND = 6
ROOT_CONTACT_WITHOUT_PREPLAN = 5

AMBIGUOUS_ROOT_LINEAGE = 0
PREPLAN_SOURCE_CONTACT = 0
old Phase4C SOURCE_CONTACT = 0
old AUTHORIZED_SWEEP = 0
STRUCTURAL_REACTION strategy authorization = 0
```

All six bound contacts satisfied:

```text
plan_frozen_at < root_contact_at
strategy_source_kind = ROOT
child_required = false
state after contact = WAITING_SWEEP
```

The five physical contacts without a prior valid PLAN were not retrospectively
backfilled. Seven planned Roots never contacted before later Root invalidation;
all seven plans were canceled by the existing Root-invalidated survival rule.

Upstream structure, liquidity, map/reversal, Root detector, Root-watch/contact,
and optional-child audit outputs remained causally consistent with D-124.

Therefore corrected Phase 4B is strategy-parity PASS within its isolated scope.

---

## D-126 — Corrected Phase 4C uses per-M1-open causal pool snapshots and Root-zone intersection

Status: VALIDATED HISTORICAL IMPLEMENTATION — 2026-08-16 / STRATEGIC OWNERSHIP SUPERSEDED BY D-127

D-125 proves that a Root-specific map/objective PLAN can exist strictly before
physical Root contact. D-126 freezes the remaining baseline strategic-sweep
ownership rule without reintroducing child authority or arbitrary distance/age
parameters.

### Why the snapshot is not frozen at Root contact

A Root-contact-time pool snapshot is too early.

Current authority explicitly allows a liquidity object that forms **after**
Root contact to become eligible later if it becomes causally mature and a
separate subsequent approach sweeps it.

Therefore the strategy does not persist one immutable contact-time pool set.

Instead, for every M1 bar that could become a sweep excursion:

```text
M1 bar open
→ snapshot pools already causally known before that open
→ let the M1 bar complete
→ evaluate penetration + same-bar recovery
```

This is a causal **per-bar** snapshot, not a future-looking dynamic search after
the wick is known.

### Same-timestamp processing safety

The snapshot is taken from state carried **into** the close-timestamp processing
group, before H4/H1/M30/M15/M5 events that become available at the M1 bar's
close are applied.

Required pool maturity in build D-126:

```text
pool.available_at < sweep_bar.open_time
```

Strict `<` is a conservative closed-bar ordering rule. A pool that only becomes
available at the exact M1 open timestamp is not used in that bar's completed
excursion.

### Root-contact bar

The current closed-bar implementation does not authorize the Root-contact M1
bar itself as the strategic sweep.

Reason:

```text
Root contact is known at that M1 bar close
OHLC does not prove intrabar contact-before-sweep ordering
```

So a scenario first enters sweep eligibility on the next/later M1 bar. This is a
fail-closed implementation decision, not a claim that tick-level same-bar
ordering could never be valid.

### Eligible families and direction

D-126 strategic sweep families are:

```text
EXTERNAL_SWING
DEFENDED_RANGE_EDGE
```

`STRUCTURAL_REACTION` remains disabled until its Root-based creation/ownership
contract is independently re-frozen.

Direction:

```text
LONG  → LOW-side pool
SHORT → HIGH-side pool
```

Already strategy-consumed pools are excluded.

No:

```text
N-bar age
ATR distance
point distance
quality score
latest/nearest pool selection
```

is added.

### Root-reaction spatial ownership

A direction-compatible physical sweep is strategy-owned by a Root scenario only
when the **sweep M1 bar itself intersects that scenario's Root zone**:

```text
bar.high >= Root.bottom
AND
bar.low <= Root.top
```

This operationalizes the mentor evidence that valid liquidity/sweep belongs to
the source/zone reaction context while avoiding an arbitrary distance
threshold.

A distant future sweep that does not trade through the Root zone cannot be
attached merely because it happened after Root contact.

### Multiple pools / multiple episodes

One M1 bar may sweep several mature eligible pools.

```text
one scenario
+ one M1 sweep bar
+ N distinct swept pools
→ one AUTHORIZED_SWEEP episode
→ N AUTHORIZED_SWEEP_POOL identities retained
```

No best pool is selected.

Later valid sweep episodes before scenario cancellation are also retained.
D-126 does not replace an earlier episode with a later one.

Which retained sweep episode becomes the causal predecessor of a meaningful M1
CHoCH remains Phase 5A authority.

### D-126 state transition

```text
PLANNED
→ qualifying Root contact
→ WAITING_SWEEP
→ first/any authorized Root-reaction sweep
→ WAITING_TRIGGER
```

`WAITING_TRIGGER` means only that at least one authorized sweep episode exists.
Meaningful M1 CHoCH search is still disabled in D-126.

### Explicit boundary

D-126 does not:

```text
create STRUCTURAL_REACTION liquidity
authorize M1 CHoCH
select a causal sweep episode for CHoCH
select/build execution FVG
submit/cancel orders
```

Optional child observations remain audit/context only and are absent from every
sweep key.

Reason:

This is the narrowest deterministic rule consistent with the current authority
and casebook evidence (`SOURCE_LIQUIDITY_SWEEP`, `LIQUIDITY_NEAR_ZONE`,
`M1_SWEEP`, `SWEEP_BEFORE_TRIGGER`) while preserving no-lookahead.

### 2026-08-16 D-126 validation result

Build `1.00 / D126_ROOT_REACTION_SWEEP_CORE` passed its isolated causal smoke:

```text
SCENARIO_PLANNED = 13
SCENARIO_ROOT_CONTACT_BOUND = 6
ROOT_CONTACT_WITHOUT_PREPLAN = 5
AUTHORIZED_SWEEP = 11
AUTHORIZED_SWEEP_POOL = 20
```

All 20 authorized pool rows satisfied the D-126 implementation contract:

```text
pool.available_at < sweep_bar_open
root_intersection = true
same_contact_bar = false
strategy_source_kind = ROOT
child_required = false
```

and:

```text
AUTHORIZED_SWEEP_REPLACED = 0
STRUCTURAL_REACTION_CREATED = 0
old SOURCE_CONTACT = 0
orders/deals = 0
```

This proves D-126 was implemented as designed. It does **not** prove that
Root-zone reintersection and the extra sweep-ownership layer belong in the
minimal baseline. D-127 supersedes those strategic filters while preserving the
D-126 run as historical evidence.

---

## D-127 — Separate DETECT / SEQUENCE / EXECUTE; use a linear Root → Sweep → CHoCH pipeline

Status: ACTIVE / VALIDATED — 2026-08-16

The current baseline had accumulated nested filters inside stages that were
already downstream of several higher-timeframe filters.

Observed shape:

```text
Map
→ Root
→ Contact
→ Sweep(extra Root ownership / family / intersection filters)
→ CHoCH(extra sweep-time trend / protected-reference filters)
→ FVG
```

This is rejected for the minimal baseline.

The current architecture is instead:

```text
DETECT
→ liquidity / M1 sweep / M1 CHoCH / FVG facts

SEQUENCE
→ Map
→ Root
→ Contact
→ Sweep
→ CHoCH
→ FVG

EXECUTE
→ FVG selection
→ Entry / SL / TP
→ order lifecycle
```

### Detector authority

A detector answers only:

```text
"did this structure exist?"
```

It does not know whether the current Root scenario is tradable.

#### M1 sweep

At each M1 bar open, snapshot currently active liquidity already causally known
at that open. Then apply the existing physical penetration + same-bar recovery
geometry.

Detector event:

```text
M1_SWEEP_DETECTED
```

No detector-side:

```text
Root intersection
scenario ownership
direction gate
child gate
ATR / point / N-bar / quality score
strategy family whitelist
```

is added.

The pre-open causality rule remains because it prevents look-ahead; it is not a
quality filter.

#### M1 CHoCH

The existing M1 structure detector remains the CHoCH authority.

```text
M1 STRUCTURE_PROTECTED_BREAK
→ M1_CHOCH_DETECTED
```

The scenario must not rebuild a second CHoCH definition at sweep time.

Therefore D-127 rejects the unpushed strict-D127 draft rule that required:

```text
opposite M1 trend at sweep
+
protected swing frozen at sweep
+
later break of that frozen snapshot
```

That draft was never repository authority.

`INITIAL_BOS` remains a different detector event. If that taxonomy is later
revised, it must be done in the structure detector itself rather than by adding
scenario exceptions.

### Sequence authority

A Root-specific preplanned scenario uses simple stage order.

LONG:

```text
Root contact
→ later LOW-side M1_SWEEP_DETECTED
→ later bullish M1_CHOCH_DETECTED
→ WAITING_FVG
```

SHORT is symmetric.

The scenario layer checks only:

```text
time ordering
direction compatibility
existing scenario lifecycle validity
```

It does not re-score the structures.

The Root-contact bar cannot simultaneously satisfy the Sweep stage, and the
same M1 bar cannot simultaneously satisfy Sweep and CHoCH, because closed OHLC
cannot prove the required intrabar order. These are sequence-causality rules,
not additional structure-quality filters.

The first direction-compatible detected sweep after Root contact satisfies the
Sweep stage. Later sweep detections remain detector/audit facts and do not
replace the stage or create a new CHoCH reference.

### Explicitly removed from current baseline

```text
sweep bar must re-intersect Root
D-126 Root-owned sweep episode selection
D-126 strategy family whitelist at Sweep stage
latest sweep replacement
sweep-time opposite M1 trend requirement
sweep-time protected swing freeze
separate MEANINGFUL_CHOCH structure subtype
mandatory M5 confirmation
child-based trigger authority
```

### Meaning of "meaningful CHoCH"

The phrase remains descriptive only:

```text
generic detected M1 CHoCH
+
correct Root → Contact → Sweep scenario sequence
=
CHoCH meaningful to this scenario
```

There is no second detector hidden inside that label.

### Boundary

D-127 stops at:

```text
SCENARIO_CHOCH_ACCEPTED
→ WAITING_FVG
```

FVG selection, Entry, SL, final TP selection, and order submission remain
disabled until this simplified funnel is locally validated.

Reason:

The baseline already filters context through objective/map/Root/contact. Sweep
and CHoCH should contribute one additional structural fact each, not each carry
another multi-condition strategy gate. This preserves explainability and lets
later FVG/Entry logic perform its intended downstream filtering.

### 2026-08-16 validation and OB-recognizer experiment comparison

Build `1.10 / D127_LINEAR_TRIGGER_PIPELINE_CORE` passed the January causal smoke.

Baseline recognizer:

```text
InpEnableFvgOriginObExperiment = false

SCENARIO_PLANNED = 13
SCENARIO_ROOT_CONTACT_BOUND = 6
SCENARIO_SWEEP_ACCEPTED = 6
SCENARIO_CHOCH_ACCEPTED = 2
distinct accepted M1 CHoCH events = 2
```

Experiment enabled:

```text
InpEnableFvgOriginObExperiment = true

ROOT_CREATED = 108
  LAST_OPPOSITE_OB = 19
  FVG_ORIGIN_OB = 89

SCENARIO_PLANNED = 78
SCENARIO_ROOT_CONTACT_BOUND = 36
SCENARIO_SWEEP_ACCEPTED = 33
SCENARIO_CHOCH_ACCEPTED = 18
distinct accepted M1 CHoCH events = 9
```

The experiment is additive rather than substitutive:

```text
all baseline ROOT_CREATED identities remain present
all baseline SCENARIO_PLANNED rows remain present
all baseline ROOT_CONTACT_BOUND rows remain present
all baseline SCENARIO_SWEEP_ACCEPTED rows remain present
all baseline SCENARIO_CHOCH_ACCEPTED rows remain present
```

Generic structure, liquidity, Sweep detector, CHoCH detector, and map streams are
row-identical between the two runs.

Same physical origin candles recognized by both OB definitions are merged:

```text
OB_RECOGNITION_MERGED = 34
```

This confirms implementation causality but does not promote the experimental
recognizer to default authority.

Current freeze:

```text
LAST_OPPOSITE_OB = default baseline recognizer
FVG_ORIGIN_OB = immutable research experiment
```

Reason:

```text
the experiment materially expands candidate coverage
but 18 scenario CHoCH branches collapse to only 9 distinct M1 CHoCH events
and downstream FVG / Entry / exposure arbitration / profitability are not yet tested
```

Do not select the recognizer variant by raw branch count. Carry both variants
through the same FVG/execution pipeline and compare completed deterministic
setups first.


---

## D-128A — FVG is an independent detector fact; scenario freezes only the causal fresh widest set

Status: ACTIVE / IMPLEMENTED / VALIDATION DEFERRED TO INTEGRATED BUILD 1.50

D-127 established the architecture:

```text
DETECT -> SEQUENCE -> EXECUTE
```

D-128A applies the same separation to M1 FVG instead of placing another compound
filter inside `WAITING_FVG`.

### Detector

Global M1 FVG geometry is scenario-independent:

```text
Bullish: Candle3.low > Candle1.high
Bearish: Candle3.high < Candle1.low
```

The three bars must be clock-contiguous M1 bars. Candle3 close is the FVG
`available_at`. A price void spanning a missing/session interval is rejected as
`SESSION_OR_DATA_GAP_FVG`.

### Scenario causal boundary

At `SCENARIO_CHOCH_ACCEPTED`, the candidate set is frozen from detector facts that
satisfy only:

```text
direction == scenario.direction
FVG.available_at > accepted Sweep close
FVG.available_at <= accepted CHoCH close
no post-formation/pre-selection retest
```

`Candle1 >= Sweep` is deliberately **not** required. A valid causal pattern may
use a pre-Sweep Candle1, the Sweep/reversal as Candle2, and confirm the FVG only
when Candle3 closes afterward.

Same-Sweep-close FVG availability is fail-closed because closed M1 OHLC cannot
prove Sweep-before-FVG ordering inside that bar.

No minimum width, ATR/body/displacement score, Root re-touch, child confirmation,
or extra candle-colour sequence is added.

### Freshness

Formation Candle3 is not its own retest. Every later completed M1 bar up to and
including a later CHoCH bar is checked for:

```text
bar.high >= FVG.bottom
AND
bar.low <= FVG.top
```

Any such touch before selection excludes that candidate as `PRE_SELECTION_RETEST`.

### Selection

Eligible bounds are normalized to the symbol tick grid. Width is compared in
integer tick units. The unique maximum width wins. Exact max-width tie:

```text
AMBIGUOUS_EXECUTION_FVG -> NO_TRADE
```

No eligible candidate:

```text
NO_CAUSAL_FRESH_FVG -> NO_TRADE
```

Unique widest candidate:

```text
SCENARIO_FVG_SELECTED
-> WAITING_EXECUTION_GEOMETRY
```

### Isolation boundary

Build `1.20` intentionally does not calculate or submit:

```text
Entry
SL
Final TP
broker preflight
pending order
fill/cancel/reconciliation
```

Reason: FVG causality/freshness/widest selection must pass independently before
execution geometry is attached. This also preserves the project's rule that a
stage contributes one concept rather than hiding another multi-filter pipeline.


---

## D-128B — Selected FVG deterministically fixes Entry/SL and frozen-family TP

Status: ACTIVE / IMPLEMENTED IN BUILD 1.50 / LOCAL VALIDATION PENDING

After `SCENARIO_FVG_SELECTED`, no new strategy detector is introduced. Geometry is direct:

```text
LONG Entry  = bullish FVG.top
LONG raw SL = FVG.bottom - 0.20 * FVG.width
LONG normalized SL = greatest valid symbol tick <= raw SL

SHORT Entry  = bearish FVG.bottom
SHORT raw SL = FVG.top + 0.20 * FVG.width
SHORT normalized SL = smallest valid symbol tick >= raw SL
```

The PLAN-time objective family is then scanned in its frozen nearest-first order. Consumed/nonpositive-reward candidates are skipped; planned R `<1` remains intermediate; the first planned R `>=1` becomes Final TP. No max-R optimization or objective reordering is allowed.
Eligibility uses integer symbol-tick distances for the `1R` boundary (`reward_ticks >= risk_ticks`), avoiding any floating epsilon that could silently admit a mathematically sub-1R objective. `planned_r` is reported from those tick counts.

---

## D-129 — Fully-authorized same-epoch multi-Root branches fail closed until provenance merge is specified

Status: HISTORICAL / SUPERSEDED BY D-132 AND D-133

V1 already freezes one accepted first-position exposure per symbol+magic and forbids arbitrary risk-slot scoring. D-127/FVG-origin testing demonstrated that several Root branches can converge on the same CHoCH.

Current baseline therefore uses:

```text
fully_authorized_branch_count == 1
→ execution may proceed

fully_authorized_branch_count > 1
→ all branches NO_TRADE
→ AMBIGUOUS_SIMULTANEOUS_AUTHORIZATION
```

This applies to same-direction as well as opposite-direction branches. It is not an extra Sweep/CHoCH/FVG quality filter; it is a one-exposure execution collision rule after complete strategy authorization.

Forbidden tie-breaks:

```text
array order
nearest/latest Root
widest/narrowest Root
best RR
quality score
manual visual preference
```

A future contributor/provenance merge may be researched separately, but it must define which Root(s) own pending survival after the merge before it can replace this fail-closed baseline.

---

## D-130 — Build 1.50 submits frozen geometry only in Strategy Tester

Status: ACTIVE / IMPLEMENTED / LOCAL VALIDATION PENDING

After exactly one fully-authorized branch survives arbitration, execution preflight checks symbol trade mode, limit/SL/TP support, tick grid, StopsLevel, minimum-volume parity, persistent GTC capability, current trade session, and `OrderCheck`.

```text
sizing = SYMBOL_VOLUME_MIN
order = BUY_LIMIT / SELL_LIMIT
time = ORDER_TIME_GTC
filling = ORDER_FILLING_RETURN
```

No broker constraint may move Entry, tighten/widen the strategy SL, replace the selected FVG, or replace TP. Failure is terminal `EXECUTION_INFEASIBLE` or `ORDER_REJECTED`; the old signal is never delayed/retried.

To enforce “same decision cycle” without an arbitrary age threshold, pending submission additionally requires `current M1 open == CHoCH bar open + 60 sec`. Closed-bar catch-up of older signals is therefore fail-closed rather than submitted late.

Live execution remains hard-blocked; `OrderSend` authorization requires Strategy Tester environment.

---

## D-131 — Pending lifecycle uses only frozen objective, Root, and direction authority before fill

Status: ACTIVE / IMPLEMENTED / LOCAL VALIDATION PENDING

Pending survival authority remains exactly:

```text
final objective not delivered
required HTF Root remains valid
scenario direction authority remains valid
```

Objective delivery is checked using the frozen liquidity state and live side-specific quote (`LONG: Bid`, `SHORT: Ask`). Root/direction invalidation is inherited from the existing closed-bar scenario cancellation logic.

On cancellation the strategy state becomes `CANCELED` first, then the EA requests `TRADE_ACTION_REMOVE`. Freeze/server rejection does not revive strategy validity; a later fill after failed cancellation is `EXECUTION_DIVERGENCE`.

After valid fill, source/owner/M1 changes no longer cancel the position. Broker/server SL/TP and actual deal history determine the economic result. `OnTradeTransaction` is only a reconciliation trigger; callback arrival order is not treated as strategy causality.

Startup with an already-existing symbol+magic pending/position enters `INIT_EXECUTION_RECOVERY_REQUIRED` rather than guessing prior scenario provenance.

Partial fill is treated as an execution-state exception, not a second strategy signal. If
a position is present while a residual pending from the same first-position order remains,
the position keeps its frozen server SL/TP and the residual receives one cancel request.
Residual survival/cancel rejection is `EXECUTION_DIVERGENCE`; the exposure lock remains
held and no invented retry/re-entry path is created.

---

## D-132 — SL invalidation variants + duplicate-provenance contributor merge

Status: SL VARIANTS RETAINED / STRICT EXECUTION-IDENTITY MERGE SUPERSEDED BY D-133 — 2026-08-18

Build 1.50 January A/B validation showed that the deterministic execution chain itself was behaving causally in the observed branches, but exposed two strategy-design issues:

1. `FVG_DISTAL_20` often produces a very small GOLD risk distance because the stop scales only with M1 FVG width.
2. With `FVG_ORIGIN_OB=true`, several independent Root branches can converge on the exact same downstream FVG / Entry / SL / objective / TP, yet D-129 rejected every branch solely because the same authorization epoch contained more than one branch.

The user confirmed the mentor's governing rule:

```text
SL = point where the scenario is invalidated
```

D-132 therefore freezes three isolated SL protocols:

```text
A. V1_SL_FVG_DISTAL_20 (control)
LONG  = FVG.bottom - 0.20 * FVG.width
SHORT = FVG.top    + 0.20 * FVG.width

B. V1_SL_SWEEP_EXTREME
LONG  = accepted D-127 Sweep bar low
SHORT = accepted D-127 Sweep bar high

C. V1_SL_ROOT_OB_DISTAL_20
LONG  = Root.bottom - 0.20 * Root.width
SHORT = Root.top    + 0.20 * Root.width
```

All are outward-normalized to the symbol tick grid. No ATR/fixed-distance padding is introduced. The frozen objective family itself is not rebuilt, but final objective eligibility is recomputed after the selected SL because `planned R` changes with risk.

D-132 also replaces D-129's blanket same-epoch branch-count rejection with a strict duplicate-provenance test. Branches merge only when direction, selected FVG identity, Entry tick, normalized SL tick, final objective liquidity identity, and TP tick are all identical. Otherwise `AMBIGUOUS_SIMULTANEOUS_AUTHORIZATION` remains fail-closed.

The merge freezes contributor scenario IDs and Root IDs at authorization. No later contributor may be attached. A merged pending survives while the common objective is valid and at least one frozen contributor retains its ACTIVE Root plus existing continuation/reversal direction authority. All contributors invalid before fill causes `CANCELED_ALL_CONTRIBUTORS_INVALID`.

The first branch may be used as the implementation master ledger only. It is not a strategic winner. On master fill or terminal pre-fill resolution, secondary contributor scenario ownership is released so resolved contributor rows cannot permanently block future Root reuse.

Reason:

The observed ambiguity was frequently not a conflict between different trades, but several causal histories arriving at one identical executable order. D-132 removes only that duplicate provenance without inventing Root ranking. At the same time, the SL variants test two explicit invalidation interpretations without silently mixing them into one optimized rule.

---

## D-133 — FVG-origin OB is baseline; same FVG/Entry Roots are one scenario

Status: ACTIVE / USER APPROVED — 2026-08-18

The user made two strategy-authority decisions after D-132 real-tick comparison:

```text
1. FVG-origin Candle1 OB is accepted as a normal OB definition.
2. If multiple Roots arrive at the same trade Entry, they are one scenario.
```

Operationally, `same trade Entry` is frozen as:

```text
same direction
same selected_fvg_id
same Entry tick
```

This supersedes D-132's requirement that normalized SL and TP must also already be identical before contributor merge.

### Recognizer authority

`LAST_OPPOSITE_OB` and `FVG_ORIGIN_OB` are both always-enabled baseline Root recognizers. The old `InpEnableFvgOriginObExperiment` input is removed. Same physical candles are deduplicated and recognition reasons are merged.

### Merge before TP

Old D-132 order:

```text
Root branch
→ branch SL
→ branch TP
→ compare full execution identity
→ maybe merge
```

D-133 order:

```text
Root branches
→ same selected FVG / Entry?
→ merge contributor scenario
→ choose one merged SL
→ choose one merged TP
→ one execution opportunity
```

This is necessary because Root-based SL makes different valid Roots produce different stop prices even when they describe the same entry opportunity.

### Merged SL authority

Each contributor calculates the stop implied by the selected SL model, then the merged scenario uses the stop that preserves all contributor invalidation space:

```text
LONG  = minimum contributor normalized SL
SHORT = maximum contributor normalized SL
```

Under `ROOT_OB_DISTAL_20`, this corresponds to the outermost/deepest contributing Root stop. The rule is symmetric and does not rank Roots by quality.

### Objective authority after merge

A merged scenario cannot take one arbitrary Root's objective family and cannot union new targets after Entry. Final TP is selected from the **intersection of objective price ticks already frozen by every contributor plan**.

After merged SL:

```text
common frozen objective prices
→ nearest-first in trade direction
→ first reward_ticks >= risk_ticks
```

No common R-eligible price:

```text
NO_COMMON_R_ELIGIBLE_OBJECTIVE
→ NO_TRADE
```

A liquidity ID used for ledger reconciliation may be selected deterministically among same-price representatives; the objective price is the strategic authority.

### Ambiguity

Different Root IDs no longer create ambiguity by themselves.

Fail closed only when the same execution epoch contains distinct completed entry opportunities:

```text
different direction
or different selected_fvg_id
or different Entry tick
→ AMBIGUOUS_SIMULTANEOUS_AUTHORIZATION
```

### D-132 evidence motivating the decision

January build 1.60 with `FVG_ORIGIN_OB=true / ROOT_OB_DISTAL_20` showed same-entry Root clusters whose stop prices differed solely because each Root carried its own geometry. Example `2025-01-15 18:23`:

```text
same Entry = 2681.33
same TP candidate = 2697.90
5 Root branches
Root-derived normalized SLs = 2667.64 / 2666.04 / 2668.58 / 2666.04 / 2668.74
```

D-132 treated the cluster as ambiguity. D-133 treats it as one scenario and would use `2666.04` as the merged LONG Root-OB stop before recalculating TP eligibility.

Build target:

```text
internal build = 1.70
phase = D133_FVG_OB_BASELINE_SAME_ENTRY_ROOT_MERGE
```

---

## D-134 — Same-direction independent add-on scenarios are allowed on hedging accounts

Status: ACTIVE / USER APPROVED — 2026-08-18

The user explicitly removed the one-position/one-exposure restriction for same-direction trades.

Reasoning:

A later signal that independently completes:

```text
new Root
→ Root contact
→ liquidity sweep
→ M1 CHoCH
→ causal FVG
→ Entry / SL / TP
```

while an earlier same-direction position is alive is not merely duplicate exposure. It can represent a new pullback/re-entry into the same larger trend.

### Directional exposure rule

Allowed:

```text
existing LONG pending/position + new LONG scenario
existing SHORT pending/position + new SHORT scenario
```

Blocked:

```text
existing LONG pending/position + new SHORT scenario
existing SHORT pending/position + new LONG scenario
```

Blocked opposite-direction reason:

```text
OPPOSITE_DIRECTION_EXPOSURE_CONFLICT
```

The old signal is not delayed and submitted after the conflicting exposure terminates.

### Same Entry versus add-on Entry

D-133 remains authoritative for duplicate provenance:

```text
same direction
+ same selected_fvg_id
+ same Entry tick
→ contributor merge
→ one order
```

D-134 adds:

```text
same direction
+ different selected_fvg_id or Entry tick
→ independent add-on scenario
→ separate order/position allowed
```

No add-on modifies an earlier scenario's Entry, SL, TP, volume, or exit lifecycle.

### Simultaneous opposite-direction authorization

If both directions become fully authorized in the same processing epoch and no managed exposure existed before that epoch:

```text
AMBIGUOUS_SIMULTANEOUS_OPPOSITE_DIRECTION_AUTHORIZATION
→ fail closed
```

This prevents submission order / array order from becoming an implicit direction selector.

If one direction was already exposed before the epoch, only same-direction add-ons may proceed; opposite-direction opportunities are blocked.

### Hedging account is required

The user confirmed the intended account is a hedging account.

Build 1.80 therefore requires:

```text
ACCOUNT_MARGIN_MODE_RETAIL_HEDGING
```

for automated execution.

A netting account cannot preserve independent scenario SL/TP lifecycle and is:

```text
EXECUTION_INFEASIBLE
reason = HEDGING_ACCOUNT_REQUIRED_FOR_INDEPENDENT_SCENARIO_POSITIONS
```

No synthetic per-scenario accounting is used to pretend one net position is several independent trades.

### Scenario-scoped execution reconciliation

D-131/D-133's single global managed-order assumption is superseded for active execution.

Each accepted scenario is reconciled by its own:

```text
broker_order_ticket
entry deal
DEAL_POSITION_ID / POSITION_IDENTIFIER
exit deal
```

A partial fill may leave residual volume only on that scenario's original order ticket. The EA may cancel that exact residual order once.

D-134 does not weaken the existing execution-divergence safety lock. If a cancel-rejected order, partial-fill residual, or divergent position remains live, new orders in **either direction** are blocked with:

```text
EXECUTION_DIVERGENCE_LOCK
```

until the broker-side risk is no longer live.

Forbidden:

```text
find any symbol+magic pending
→ treat it as residual of whichever scenario just filled
```

because another same-direction pending may be a legitimate independent add-on.

### Evidence motivating the change

D-133 January real-tick validation with `ROOT_OB_DISTAL_20` produced:

```text
18 finalized Root branches
→ 9 unique Entry opportunities
→ 4 contributor-merge clusters
→ 0 same-entry ambiguity
→ 6 otherwise-valid opportunities blocked only by EXPOSURE_ALREADY_ACCEPTED
```

Those six consisted of two signals while an earlier pending existed and four signals while an earlier same-direction position was filled.

D-134 removes only that execution-policy bottleneck. Upstream detector/scenario rules remain unchanged.
