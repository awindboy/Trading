# V11 Wave Candle v0.5 MT5 checkpoint

Date: `2026-09-22`

Status: `IMPLEMENTED / COMPILED / DEPLOYED LOCALLY / OBSERVATION ONLY / NO TRADE AUTHORITY`

## Added

- selectable `FAST HA`, `STD HA`, `SLOW HA`, and ordinary `RAW OHLC` Wave Candle modes;
- formulas copied from the retained `V10HAOverlay.mq5` comparator;
- bullish/bearish hue, wick, open reference, path efficiency, and directional settlement now follow the selected candle coordinate system;
- the settlement-median line is removed;
- `InpShowOHCLLines` draws the selected candle's Open, High, Close, and Low as four horizontal lines.

FAST remains the default. The other modes are observation views and have no entry, exit, or model authority.

## Build receipt

- source: `mt5/indicators/V11WaveCandle.mq5`;
- source SHA-256: `d3890aec0c5434e0b30f2d851f93853c7fe032e29ac7498aff0948c999759820`;
- source size: `17,232` bytes;
- compiled EX5 size: `40,474` bytes;
- platform: XM Global MT5, terminal build `6182`;
- compiler result: `0 errors, 0 warnings`;
- deployed files: `V11WaveCandle.ex5`, compatibility alias `V11WaveCandle_v03.ex5`, and explicit current alias `V11WaveCandle_v05.ex5`.

## Verification boundary

- the v0.4 canvas contour was visually verified on a clean MT5 H4 chart;
- v0.5 compiled successfully and the four formulas were checked on a fixed three-bar numerical fixture, producing distinct FAST, STD, and SLOW recursions and exact RAW OHLC passthrough;
- the currently open MT5 chart also contains `V10HAOverlay`, so it is not suitable visual evidence for the v0.5 Wave Candle layer;
- no trading-performance claim follows from this implementation receipt.
