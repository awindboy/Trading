# V11 Wave Candle v0.1 MT5 checkpoint

Date: `2026-09-22`

Status: `SUPERSEDED AND REJECTED / DESIGN HISTORY ONLY / NO TRADE AUTHORITY`

V0.1 drew the ordered M5 path and settlement profile directly inside each H4 slot. Runtime inspection showed that this was an LTF mini-chart overlay, not the intended compressed Wave Candle representation. It was replaced by v0.2.

## Artifact

- source: `mt5/indicators/V11WaveCandle.mq5`;
- source SHA-256: `1bfec8dcb8ebbdc99d98a54a6618dea7b2c3cc1d991765592e139b22f3dacaa8`;
- platform: XM Global MT5, terminal build `6182`;
- compiler: MetaEditor X64 Regular;
- result: `0 errors, 0 warnings`;
- local terminal artifact: `MQL5/Indicators/V11WaveCandle.ex5`, 23,018 bytes.

The `.ex5` and compile log are local build outputs and are not committed.

## Visual-development evidence

- source: verified GOLD# raw M1 ending `2026-09-18 23:57`;
- source SHA-256: `ebb15194e782c1265fb9eabef2b5324f9909d15b3dd9a70bf2717c5700b61817`;
- displayed design sample: 20 completed H4 bars from `2026-09-15 12:00` through `2026-09-18 16:00`;
- construction: one chronological raw-M1 pass into completed M5 and H4 bars;
- MT5-style preview: ignored `output/v11_wave_candle_mt5_20260922/V11_WAVE_CANDLE_MT5_PREVIEW.png`.

The preview is a visual mock using the indicator's fixed time/price mapping. It is not a screenshot of a running MT5 chart and not performance evidence.

## Remaining checks

- attach to a live/historical GOLD# H4 chart;
- inspect layering at several zoom levels and chart proportions;
- verify hover text and forming-H4 updates;
- compare a fixed sample of Python and MQL numeric coordinates;
- observe object count and redraw latency over a long session.
