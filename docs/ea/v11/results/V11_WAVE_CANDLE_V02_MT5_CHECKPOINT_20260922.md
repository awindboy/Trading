# V11 Wave Candle v0.2 MT5 checkpoint

Date: `2026-09-22`

Status: `SUPERSEDED BY V0.3 / DESIGN HISTORY ONLY / NO TRADE AUTHORITY`

V0.2 corrected the raw-LTF-path mistake but used a rigid rectangular Q25-Q75 settlement zone. V0.3 replaces it with the requested smooth settlement-density contour.

## Correction from v0.1

- removed the visible ordered-M5 path;
- removed the M5-close occupancy histogram;
- M5 now remains an internal measurement source only;
- retained one H4 candle whose width, tone, settlement zone, and median carry the compressed dimensions;
- replaced ARGB transparency with opaque colors blended against the chart background because MT5 chart objects did not render the translucent bodies reliably.

## Artifact

- source: `mt5/indicators/V11WaveCandle.mq5`;
- source SHA-256: `a801c3a444a5a14be7222eac0cfc46247f1845b4aefbc0ec935ae68e685ecc8e`;
- platform: XM Global MT5, terminal build `6182`;
- compiler result: `0 errors, 0 warnings`;
- local terminal artifact: `MQL5/Indicators/V11WaveCandle.ex5`, 22,250 bytes.

## Current visual mapping

- outer wick/body: FAST H4 HA;
- body width: completed-M5 path efficiency;
- body tone: directional settlement fraction;
- inner vertical zone: completed-M5 close Q25-Q75;
- short horizontal line: completed-M5 close median.

MT5-style design preview: ignored `output/v11_wave_candle_mt5_20260922/V11_WAVE_CANDLE_V02_MT5_PREVIEW.png`.

The preview is not a running MT5 screenshot and not performance evidence. The attached indicator must be removed and reattached, or the MT5 Navigator refreshed, before evaluating v0.2 runtime rendering.
