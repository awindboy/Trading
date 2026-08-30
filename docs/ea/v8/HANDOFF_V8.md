# V8 Development Handoff

Last updated: `2026-08-31`
GitHub state at start of this update: `25c4f912cb3c83aa96ef640088702cc0e33d7f49`
Current phase: `V8-005A MOVEMENT PROBABILITY SHADOW INDICATOR`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`
Market: `GOLD# only`
Untouched reserve: `GOLD# 2021`

## Current research conclusion

V8 has separated two prediction problems that must not be conflated.

### Direction

Historical GOLD OHLC/indicator context has not produced stable useful `+10 / -10 first-hit` direction information. Extensive preprocessing/model/event/overlap/rolling/meta-label diagnostics remained near chance or reversed across later development periods.

Do not resume direction-model threshold mining without a materially new information source or preregistered causal hypothesis.

### Movement intensity

Near-term barrier-crossing probability is strongly learnable from causal recent range/realized-volatility structure.

Portable continuous-M5 logistic event-subset AUC:

```text
15m: 2024 0.865 / 2025 0.873 / 2026 0.815
30m: 2024 0.844 / 2025 0.851 / 2026 0.796
60m: 2024 0.807 / 2025 0.829 / 2026 0.781
```

These are open-development results, not final untouched validation.

## Current implementation

Primary artifact:

`mt5/indicators/V8MovementProbabilityIndicator.mq5`

Behavior:

- attach to GOLD# M5;
- separate subwindow shows continuous 15m/30m/60m probability lines;
- main chart shows factual event triangles;
- event-family colors configurable in indicator Properties;
- marker tooltips show probabilities known at event decision time;
- no trading or directional output;
- no value on the forming M5 candle;
- historical model selection is walk-forward by year.

Implementation/provenance:

`docs/ea/v8/V8_005_MOVEMENT_PROBABILITY_INDICATOR.md`

Full research narrative:

`docs/ea/v8/V8_RESEARCH_JOURNEY.md`

## Critical model contract

Target barrier is fixed:

```text
+/- 10.0 GOLD price units
```

Do not change the MT5 input to another barrier without retraining.

Historical model policy:

```text
2024 <- train 2022-2023
2025 <- train 2022-2024
2026 <- train 2022-2025
```

Before 2024: no plotted probability.
After 2026: disabled by default until retrained/validated.

## Event authority

Current markers:

- M5 SMA20 contact episode start;
- M5 BB20 upper contact episode start;
- M5 BB20 lower contact episode start;
- H1 Double-B confirmation using BB20/2 CLOSE and BB4/4 OPEN.

Event markers are factual attention anchors, not LONG/SHORT labels.

## Critical parity result

Python research equations vs embedded MQL equations were recomputed on 30 sampled M5 timestamps spanning 2024-2026.

```text
max absolute feature difference      2.22e-12
max absolute probability difference  5.39e-14
```

This validates formula translation only. Actual MetaEditor compile and broker-history runtime parity are still required.

## Immediate next task

The user compiles the indicator in the actual Windows/MT5 environment.

Then verify:

1. compile success;
2. M1/M5/H1 broker history availability;
3. historical probability lines load;
4. triangle/event timing visually matches expected source candles;
5. Python/MT5 probability parity on selected timestamps if feed matches;
6. no order/trade side effects.

After successful runtime parity, begin prospective shadow logging. Do not optimize a discretionary trade threshold retrospectively from selected examples.

## Prospectively logged question

The immediate practical research question is:

> Does human discretionary directional/trade performance improve materially as movement probability rises?

Required prospective fields:

- event timestamp/type;
- 15m/30m/60m probabilities;
- human LONG/SHORT/WAIT/SKIP decision;
- actual entry/SL/TP if traded;
- realized result;
- ignored events must also remain in the ledger.

## Reading order next session

1. `docs/ea/v8/AGENTS_V8.md`
2. `docs/ea/v8/HANDOFF_V8.md`
3. `docs/ea/v8/V8_RESEARCH_JOURNEY.md`
4. `docs/ea/v8/V8_005_MOVEMENT_PROBABILITY_INDICATOR.md`
5. `docs/ea/v8/DECISIONS_V8.md`
6. `docs/ea/v8/RESEARCH_STATE_V8.md`
7. `mt5/indicators/V8MovementProbabilityIndicator.mq5`

Always refresh GitHub HEAD before further implementation.
