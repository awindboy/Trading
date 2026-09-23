# V11 Wave Candle v0.5.1 renderer-cache checkpoint

Date: `2026-09-22`

Status: `IMPLEMENTED / COMPILED / DEPLOYED LOCALLY / RUNTIME VISUAL RECHECK PENDING / OBSERVATION ONLY / NO TRADE AUTHORITY`

## Change

The v0.5 observation meaning is unchanged. Build v0.5.1 changes only rendering and data reuse:

- completed-M5 settlement densities are retained in a numeric cache;
- one chronological M5 read builds the retained cache instead of one `CopyRates` call per H4 slot;
- chart pan, zoom, and vertical-scale events call only the screen reprojection renderer;
- the bitmap canvas is preserved while its dimensions are unchanged, removing the normal `Destroy -> Create` blank interval;
- only cached H4 slots intersecting the visible horizontal viewport receive contour projection work;
- retained history defaults to 1,000 H4 slots and is configurable from 1 to 5,000;
- a newly completed M5 or changed H4 history rebuilds the numeric cache before repainting.

Completed historical observations still need screen reprojection after a chart-coordinate change because the contour width is expressed in H4 slot pixels. They do not need M5 rereads or KDE recomputation.

## Build receipt

- source: `mt5/indicators/V11WaveCandle.mq5`;
- source SHA-256: `cf41c6ebb9126f70789fc8aaf81a5a1198cffcbcfef454e95c5ce13e9997fe2f`;
- source size: `19,481` bytes;
- compiled EX5 SHA-256: `d483f792854c438bccaa7602d0c818e33cdde915d355bf7635589b8fd67da675`;
- compiled EX5 size: `42,014` bytes;
- platform: XM Global MT5, terminal build `6182`;
- compiler result: `0 errors, 0 warnings`;
- deployed files: `V11WaveCandle.ex5`, compatibility alias `V11WaveCandle_v03.ex5`, and explicit current alias `V11WaveCandle_v05.ex5`; all three installed binaries match the repository EX5 hash.

## Verification boundary

- static call-path audit confirms `CHARTEVENT_CHART_CHANGE` calls `RenderWaveCandles()` and does not call `CopyRates` or density calculation;
- the current Computer Use surface did not expose native MT5 windows, so an automated chart-navigation visual recheck was not possible in this session;
- the user's prior visual confirmation applies to v0.5 semantics, not yet to v0.5.1 renderer behavior;
- no trading-performance claim follows from this renderer checkpoint.
