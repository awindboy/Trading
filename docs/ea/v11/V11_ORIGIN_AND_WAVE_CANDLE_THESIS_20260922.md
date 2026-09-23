# How V11 and the Wave Candle were born

## 1. What V10 taught us

V10 became viable only after the strategy moved away from ordinary candles and used the H4 Heikin-Ashi state as its main participation clock. That change did not make HA a market truth. It provided a simple, low-noise representation that helped the strategy remain in persistent movement instead of trying to predict an exact reversal price.

The same simplicity also became the limitation. One H4 HA candle compresses four hours of trading into a synthetic open, high, low, close, and color. Very different intrabar journeys can finish as nearly identical HA candles.

## 2. Why V11 was not another filter

V10 explored regime labels, next-HA prediction, lower-timeframe feature expansion, progression and damage/repair rules, MA-band filters, and alternative Hard-SL ideas. Those studies produced useful negative evidence but did not establish a robust oracle or a stable rule that removed losses without also threatening the large persistent runs.

The next step therefore was not to add another score to the same compressed H4 input. It was to ask whether the observation surface itself was hiding information that mattered.

## 3. The representation insight

An H4 candle is the final envelope of many smaller movements. Its OHLC says where price opened, reached, and finished, but not:

- the order in which those prices were visited;
- where M5 closes repeatedly settled;
- whether favorable progress was direct or repeatedly surrendered;
- whether the H4 body came from efficient travel or large two-way churn.

These are not predictions and they do not assign a causal story to the market. They are additional coordinates of the process that produced the H4 result.

## 4. Why it is called Wave Candle

The user named it **Wave Candle** because one large wave—the H4 candle—should carry information extracted from the smaller M5 waves that formed it. Like HA, it is a transformed chart. Unlike HA alone, it does not discard all information about the journey inside the higher-timeframe bar.

The first visual prototype misunderstood that idea and drew the M5 path directly inside each H4 slot. That was rejected: it merely added a raw LTF chart as another dimension. Wave Candle's defining operation must be **compression**. The M5 sequence stays hidden and changes the H4 candle's contour, scale, and color tone instead.

V0.2 therefore kept the familiar FAST H4 HA shell and compressed M5 information into width, tone, a Q25-Q75 settlement zone, and median. It established the correct compression boundary but retained a rigid rectangular visual grammar.

V0.3 makes the candle itself wave-like. It smooths the complete M5-close price distribution and maps local density to the candle's left/right width. Dense settlement prices bulge; sparse prices narrow. The maximum scale still carries path efficiency, the tone carries directional settlement, and the median remains explicit. No raw M5 path or candle is shown.

V0.4 replaced visually collapsed chart triangles with one antialiased MT5 canvas contour. V0.5 then made the outer coordinate system selectable—FAST HA, STD HA, SLOW HA, or ordinary H4 OHLC—and replaced the median mark with the selected candle's O/H/C/L lines. FAST remains the default comparator; the alternatives are observation views, not retrospective permission to choose whichever history looks best.

## 5. What makes this V11

V11 is the research generation built around this representation change:

```text
V10: H4 FAST HA state is the principal observable

V11: selectable H4 shell, FAST HA by default
     + causal M5 process and settlement dimensions
     = Wave Candle
```

V10 R7G remains the frozen comparator. V11 begins with no claim of better performance. Its first obligation is to prove that the new representation is causal, reproducible, readable in MT5, and capable of supporting a pre-registered experiment without silently becoming another hindsight filter.

## 7. The transition insight

The first broad Wave and liquidity studies clarified that the fundamental change cannot be another admission filter on the same V10 action. The action itself must change. A completed NHA can terminate or interrupt the current Child without proving that an opposite journey has begun.

V11 therefore inserts a neutral bridge between interruption and new risk. During that bridge, the Wave Candle is asked whether prospective movement is becoming efficient directional business or is still rotational settlement inside the old journey. The possible outputs are old-direction resumption, independently authorized opposite participation, or continued neutrality. This state separation—not prediction of the next HA color—is the strategic reason to retain Wave Candle research.
