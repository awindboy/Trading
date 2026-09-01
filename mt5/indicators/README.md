# MT5 Indicators

- `ICTCockpitIndicator.mq5`: ICT information display indicator.
- `CleanChartTimeOverlay.mq5`: chart timer/overlay object cleanup.
- `V8MovementProbabilityIndicator.mq5`: historical V8 movement-probability indicator.
- `V8MovementProbabilityA2ReliabilityIndicator.mq5`: V8-A2 absolute-$10 survival/reliability research indicator.
- `V8ANP15ContextIndicator.mq5`: **legacy M5-A-N research indicator** using the `1.50 * pre-decision M5 ATR14` target semantics.

## Important V8-A-N status — 2026-09-02

`V8ANP15ContextIndicator.mq5` is retained for historical/shadow comparison only.

It must **not** be treated as the implementation of the active `V8-A-N-SLOW` research line because it answers:

```text
P(reach +/-1.50 * M5 ATR within 15m)
```

where the target changes every completed M5 bar.

The active replacement research is testing a slowly updated higher-timeframe scale, currently led by:

```text
T = 0.25 * previous-completed H4 ATR14
T fixed through the next H4 block
```

A Slow-N MT5 indicator should only be created after the slow target/model contract is frozen and Python/MQL parity references exist.

`.ex5` and compile logs are local build outputs of their corresponding `.mq5` sources.
