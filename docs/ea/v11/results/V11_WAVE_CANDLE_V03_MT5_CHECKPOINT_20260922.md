# V11 Wave Candle v0.3 MT5 checkpoint

Date: `2026-09-22`

Status: `IMPLEMENTED AND COMPILED / USER RUNTIME RECHECK REQUIRED / NO TRADE AUTHORITY`

## Representation

- completed M5 closes are converted into a Gaussian-smoothed price density;
- density becomes the symmetric left/right width of one H4 contour;
- path efficiency scales the contour's maximum width;
- directional settlement controls contour tone;
- FAST HA direction controls hue, while HA high/low and open/close remain as a wick and compact ticks;
- the settlement median remains a short horizontal line;
- no M5 candle, ordered path, or occupancy histogram is displayed.

## MT5 implementation

MT5 has no arbitrary filled curve object. V0.3 approximates the smooth contour with 24 price steps and two filled `OBJ_TRIANGLE` objects between each adjacent pair. This preserves time/price anchoring under zoom and scroll.

- source: `mt5/indicators/V11WaveCandle.mq5`;
- source SHA-256: `bfd55ea3054b8c1399cf1572c23e04c038db671827bf6b60cf026991d4f1e6ff`;
- platform: XM Global MT5, terminal build `6182`;
- compiler result: `0 errors, 0 warnings`;
- local terminal artifacts: `MQL5/Indicators/V11WaveCandle.ex5` and explicit reload alias `V11WaveCandle_v03.ex5`, 23,438 bytes each;
- default scope: 60 H4 bars, 24 contour steps, maximum 200 bars and 36 steps.

MT5-style design preview: ignored `output/v11_wave_candle_mt5_20260922/V11_WAVE_CANDLE_V03_MT5_PREVIEW.png`.

The preview is not a running MT5 screenshot and not performance evidence. Runtime object load, visual seams, and refresh latency still require inspection after the indicator is reattached.

## Runtime loading incident

The user's chart retained three `V11WaveCandle 1.000` instances and one `1.200` instance. Those releases shared the same chart-object prefix, so legacy instances could erase and repaint the newer output. Build `1.300` uses a versioned prefix and a timer that removes legacy-prefix objects. The explicit `V11WaveCandle_v03` alias exists so the current binary can be selected unambiguously from Navigator.
