# V11 Wave Candle v0.4 MT5 checkpoint

Date: `2026-09-22`

Status: `IMPLEMENTED / COMPILED / MT5 RUNTIME VISUALLY VERIFIED / NO TRADE AUTHORITY`

## Root cause of the v0.3 display failure

V0.3 did create its chart objects: runtime diagnostics showed `1152/1152` and `2880/2880` successful filled triangles with zero creation errors. The failure was representational:

- low-density triangle segments collapsed to approximately `1..3` horizontal pixels at the active MT5 zoom;
- thousands of separate triangles looked like the same thin vertical HA marks instead of one smooth settlement surface;
- a chart that also retained `V10HAOverlay` visually concealed the new same-hue layer.

The problem was not `InpShowWaveContour`; the persisted value was `true`.

## V0.4 implementation

- source: `mt5/indicators/V11WaveCandle.mq5`;
- source SHA-256: `cd2cb5dff387930e7c48d0ffbbefba36ecb57fe4519c66aab643d89aec3de982`;
- source size: `19,662` bytes;
- compiled EX5 size: `41,414` bytes;
- platform: XM Global MT5, terminal build `6182`;
- compiler result: `0 errors, 0 warnings`;
- renderer: one transparent `CCanvas` polygon layer with antialiased outlines;
- default scope: 60 H4 slots and 48 KDE contour intervals.

Runtime diagnostics on the clean V11 chart reported:

```text
slots=60
visible_profiles=60
nonzero_center_pixels=60
canvas=3283x1443
ChartScreenShot ok=1, error=0
```

The full-width MT5 screenshot visibly shows single- and multi-bulge settlement contours. The screenshot is retained locally under ignored output as `output/v11_wave_candle_mt5_20260922/V11_WAVE_CANDLE_V04_MT5_RUNTIME.png`; it is visual/runtime evidence only, not trading-performance evidence.

## Operational note

Use V11 on a clean H4 chart. A second chart containing `V10HAOverlay` continued to show rectangular V10 HA bodies over the same price area; that is overlay interference, not a v0.4 canvas failure.
