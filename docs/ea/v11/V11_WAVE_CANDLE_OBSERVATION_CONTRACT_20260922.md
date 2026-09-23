# V11 Wave Candle v0.3 observation contract

Status: `FROZEN VISUAL SEMANTICS / OBSERVATION ONLY / NO TRADE AUTHORITY`

## Input and clock

- market: `GOLD#`;
- display timeframe: H4;
- internal timeframe: completed M5 bars inside each H4 slot;
- official replay source: verified raw M1 revealed chronologically, from which M5 and H4 are rebuilt;
- live MT5 display: broker H4/M5 history, using only completed M5 bars at the refresh time.

M1 remains the authority for exact Hard-SL/destination touch guards in any later trading replay. M5 is an internal measurement source, not an execution substitute or a mini-chart to display.

## Outer shell

V11 v0.3 inherits the V10 FAST H4 HA clock:

```text
HC_t = (O_t + H_t + L_t + 2*C_t) / 5
HO_t = 0.25*HO_(t-1) + 0.75*HC_(t-1)
HH_t = max(H_t, HO_t, HC_t)
HL_t = min(L_t, HO_t, HC_t)
```

`HC >= HO` is displayed with the PHA hue; otherwise the NHA hue. HA high-low remains a central wick. HA open is a short left tick and HA close is a short right tick. These marks are descriptive, not predictive.

## Internal coordinates

Let `c_i` be the ordered completed-M5 closes inside the H4 slot, `O` the raw H4 open, and `d` the FAST HA direction (`+1` PHA, `-1` NHA).

### Path efficiency

```text
E = abs(c_last - O) / sum(abs(p_i - p_(i-1)))
where p = [O, c_1, ..., c_last]
```

`E` is clamped to `[0,1]` for rendering. It scales the maximum half-width of the settlement contour to `0.15 + 0.25*E` of the H4 slot. A larger scale means more direct completed-M5 travel from the raw H4 open; it does not mean stronger future probability.

### Directional settlement

```text
S = count(d * (c_i - O) >= 0) / N
```

The contour tone becomes more saturated as `S` rises. It describes where completed M5 bars settled relative to the raw H4 open and current HA direction.

### Smoothed settlement-density contour

For price `y`, calculate an unnormalised Gaussian density from all completed M5 closes:

```text
h = max((H-L)/22, 0.28*stdev(c), 2*Point)
D(y) = mean(exp(-0.5*((y-c_i)/h)^2))
R(y) = D(y) / max_y(D(y))
```

Use 24 equal contour intervals, giving 25 price levels from raw H4 low to high. At each level, draw a symmetric half-width proportional to `R(y)` and the path-efficiency maximum scale. Connecting adjacent widths produces the Wave Candle contour.

A bulge means many completed M5 closes settled around that price. Multiple bulges mean a multi-centred settlement distribution. A long narrow section means price traversed that area without repeatedly settling there. This is not traded volume, tick volume, value area, support, resistance, or a destination.

### Settlement median

Draw the median completed-M5 close as a short horizontal line. It is a descriptive center, not a stop or target.

## Forming H4 rule

A forming H4 may be shown with a distinct shell style, but it may contain only M5 bars whose five-minute interval has completed. Its geometry can change at each newly completed M5 and must not be treated as final.

## MT5 rendering contract

- anchor every object in chart time and price, never screen pixels;
- render one transformed H4 candle; do not draw an M5 path, M5 candles, or an M5 occupancy histogram;
- approximate the smooth filled contour with two `OBJ_TRIANGLE` objects between each adjacent density level; use 24 intervals by default and allow `12..36`;
- use opaque chart-background blends because MT5 chart objects do not reliably preserve ARGB transparency;
- hide native candles by default and restore the user's chart colors on indicator removal;
- show 60 H4 slots by default, with a hard input cap of 200;
- rebuild only when a new M5 completes or H4 history changes;
- expose the numeric coordinates through object tooltips;
- attach only to H4; other chart periods display an instruction instead of a transformed candle.

## Prohibited interpretation

V0.3 defines no score, regime label, entry gate, retry rule, cooldown, sizing map, Hard SL, destination, or exit. Do not infer a hidden threshold from contour width, bulge count, tone, median, or counterflow fraction.

Any semantic change must receive a new version and checkpoint. Evidence observed under one version cannot be silently pooled with another.
