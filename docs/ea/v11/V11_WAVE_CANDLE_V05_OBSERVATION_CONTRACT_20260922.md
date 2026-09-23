# V11 Wave Candle v0.5 observation contract

Status: `FROZEN VISUAL SEMANTICS / OBSERVATION ONLY / NO TRADE AUTHORITY`

## Input and clock

- market: `GOLD#`;
- display timeframe: H4;
- internal timeframe: completed M5 bars inside each H4 slot;
- official replay source: verified raw M1 revealed chronologically, from which M5 and H4 are rebuilt;
- live MT5 display: broker H4/M5 history, using only completed M5 bars at refresh time.

M1 remains authoritative for exact Hard-SL or destination touch guards. M5 is an internal measurement source, not an execution substitute or an LTF chart to display.

## Selectable outer candle

`InpCandleMode` selects one of four H4 coordinate systems:

```text
FAST HA: HC=(O+H+L+2C)/5, HO_t=.25*HO_(t-1)+.75*HC_(t-1)
STD  HA: HC=(O+H+L+C)/4,  HO_t=.50*HO_(t-1)+.50*HC_(t-1)
SLOW HA: HC=(O+H+L+2C)/5, HO_t=.75*HO_(t-1)+.25*HC_(t-1)
RAW OHLC: selected O/H/L/C equals the ordinary H4 candle
```

For each HA mode, selected high is `max(raw H, selected O, selected C)` and selected low is `min(raw L, selected O, selected C)`. FAST HA remains the default and the V10 campaign comparator. The other modes are selectable observation views, not strategy authorities.

The selected candle's `C >= O` state supplies the bullish hue; otherwise it supplies the bearish hue. Its high-low is the central wick, with compact open and close ticks.

## Internal coordinates

For completed M5 closes `c_i`, selected candle open `O*`, and selected candle direction `d`:

```text
E = abs(c_last - O*) / sum(abs(p_i - p_(i-1)))
p = [O*, c_1, ..., c_last]

S = count(d * (c_i - O*) >= 0) / N
```

`E` only scales maximum display width. `S` only changes fill intensity. Neither has predictive or trade authority.

At 49 default price levels across raw H4 low-high:

```text
h = max((H-L)/48, 0.10*stdev(c), 2*Point)
D(y) = mean(exp(-0.5*((y-c_i)/h)^2))
R(y) = (D(y) / max_y(D(y)))^1.35
```

The symmetric half-width is `R(y)` times `0.46 * H4-slot-pixels * (0.72 + 0.28*E)`, with a one-pixel floor. The left and right profiles form one filled antialiased canvas polygon.

A bulge means repeated completed-M5 settlement around that price. Multiple bulges mean a multi-centred distribution. A narrow passage means traversal with little repeated settlement. This is not traded volume, tick volume, value area, support, resistance, a destination, or a next-HA forecast.

## Selected-candle OHCL lines

The former completed-M5 median line is removed. When `InpShowOHCLLines=true`, draw four short horizontal lines at the selected candle's exact:

```text
Open
High
Close
Low
```

Thus FAST, STD, SLOW, and RAW modes produce their own corresponding four levels. These lines describe the selected coordinate system; they are not stops, targets, support, or resistance.

## Forming H4 rule

A forming H4 uses only M5 bars whose five-minute intervals have completed. Its contour and selected O/H/C/L levels may change as allowed by the selected candle definition and are not final.

## MT5 rendering contract

- use one transparent `CCanvas` bitmap-label layer;
- normalize horizontal width to the visible H4 slot for zoom readability;
- use 48 contour intervals by default and allow `24..96`;
- never draw the ordered M5 path, M5 candles, or a raw occupancy histogram;
- hide native candles by default and restore their colors on indicator removal;
- retain 1,000 H4 slots by default, configurable from 1 to 5,000;
- rebuild numeric M5/KDE state on a newly completed M5 or changed H4 history;
- reuse the persistent canvas and cached numeric state for chart zoom/resize/scroll reprojection;
- attach only to H4;
- use a clean chart without `V10HAOverlay`, which can conceal the Wave Candle.

## Prohibited interpretation

V0.5 defines no score, regime label, entry gate, retry rule, cooldown, sizing map, Hard SL, destination, or exit. Mode selection is not permission to choose the best-looking history after the fact in a formal test.

Evidence observed under v0.1-v0.4 cannot be silently pooled with v0.5. Any further semantic change requires a new version and checkpoint.
