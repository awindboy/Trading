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