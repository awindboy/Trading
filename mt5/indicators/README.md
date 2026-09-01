# MT5 Indicators

- `ICTCockpitIndicator.mq5`: ICT information display indicator.
- `CleanChartTimeOverlay.mq5`: chart timer/overlay object cleanup.
- `V8MovementProbabilityIndicator.mq5`: historical V8 movement-probability indicator.
- `V8MovementProbabilityA2ReliabilityIndicator.mq5`: V8-A2 absolute-$10 survival/reliability research indicator.
- `V8ANP15ContextIndicator.mq5`: **legacy M5-A-N research indicator** using the `1.50 * pre-decision M5 ATR14` target semantics.
- `V8SlowNP15ContextIndicator.mq5`: **active Slow-N research/shadow probe** using the Phase-0 `0.25 * previous-completed H4 ATR14` model.

## V8SlowNP15ContextIndicator

Status:

`RESEARCH PROBE / NO PRODUCTION AUTHORITY`

Attach to:

`GOLD# M5`

Displays in one `0-100` subwindow:

```text
Slow-N P15
H4 ATR14 causal percentile rank
MA20 distance / SlowTarget causal percentile rank
```

Default threshold:

`75%`

Changing `InpP15Threshold` changes both:

- the horizontal probability reference line;
- main-chart P15 candle markers.

Marker modes:

```text
SLOWN_MARK_LEVEL
= mark every completed M5 with P15 >= threshold

SLOWN_MARK_FRESH_CROSS
= mark only previous P15 < threshold and current P15 >= threshold
```

Main-chart arrows are **movement-probability markers only**. They are not SHORT arrows and do not estimate direction.

### Slow target alignment

```text
decision = completed source-M5 close

find H4 block containing decision
use ATR14 from immediately previous completed H4 bar
SlowTarget = 0.25 * that H4 ATR14
```

Example:

```text
source M5 = 11:55-12:00
decision = 12:00
current decision H4 block begins 12:00
ATR source = H4 bar that ended at 12:00
```

No partial current H4 candle is used.

### Embedded model

The indicator embeds the current Phase-0 86-feature multinomial-logistic survival probe.

Training de-overlap:

```text
m5_index % 5 == 0
```

This is not the final official Slow-N model. The embedded coefficients exist so the user can inspect chart states now and perform Python/MQL parity.

Reference values:

`docs/ea/v8/results/v8_slow_n_revalidation_20260902/slow_n_mql_parity_reference.csv`

Model pack:

`config/v8_a_n_slow_probe_20260902/models_h4_025_phase0_probe.json`

The legacy `V8ANP15ContextIndicator.mq5` remains intact for historical comparison.

`.ex5` and compile logs are local build outputs of their corresponding `.mq5` sources.
