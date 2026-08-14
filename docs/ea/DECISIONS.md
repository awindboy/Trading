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

SL과 entry precision은
후속 causal LTF refinement가 담당한다.

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
