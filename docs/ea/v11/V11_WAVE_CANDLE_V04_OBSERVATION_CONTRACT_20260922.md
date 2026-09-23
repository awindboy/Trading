# V11 Wave Candle v0.4 observation contract

Status: `FROZEN VISUAL SEMANTICS / OBSERVATION ONLY / NO TRADE AUTHORITY`

## Input and clock

- market: `GOLD#`;
- display timeframe: H4;
- internal timeframe: completed M5 bars inside each H4 slot;
- official replay source: verified raw M1 revealed chronologically, from which M5 and H4 are rebuilt;
- live MT5 display: broker H4/M5 history, using only completed M5 bars at the refresh time.

M1 remains the authority for exact Hard-SL or destination touch guards in any later trading replay. M5 is an internal measurement source, not an execution substitute or an LTF chart to display.

## Outer shell

V0.4 retains the V10 FAST H4 HA clock:

```text
HC_t = (O_t + H_t + L_t + 2*C_t) / 5
HO_t = 0.25*HO_(t-1) + 0.75*HC_(t-1)
HH_t = max(H_t, HO_t, HC_t)
HL_t = min(L_t, HO_t, HC_t)
```

`HC >= HO` supplies the PHA hue; otherwise the NHA hue. HA high-low remains a central wick. HA open and close remain compact left/right ticks.

## Internal coordinates

For the completed M5 closes `c_i` inside an H4 slot, raw H4 open `O`, and FAST HA direction `d`:

```text
E = abs(c_last - O) / sum(abs(p_i - p_(i-1)))
p = [O, c_1, ..., c_last]

S = count(d * (c_i - O) >= 0) / N
```

`E` is path efficiency and only scales maximum display width. `S` is directional settlement and only changes fill intensity. Neither has predictive or trade authority.

### Canvas KDE contour

At 49 default price levels across raw H4 low-high:

```text
h = max((H-L)/48, 0.10*stdev(c), 2*Point)
D(y) = mean(exp(-0.5*((y-c_i)/h)^2))
R(y) = (D(y) / max_y(D(y)))^1.35
```

The symmetric half-width is `R(y)` times `0.46 * H4-slot-pixels * (0.72 + 0.28*E)`, with a one-pixel floor. The left and right profiles form one filled polygon with an antialiased edge. A bulge means repeated completed-M5 settlement around that price; multiple bulges mean a multi-centred distribution; a narrow passage means traversal with little repeated settlement.

This is not traded volume, tick volume, value area, support, resistance, a destination, or a next-HA forecast.

The median completed-M5 close remains a short horizontal descriptive mark.

## Forming H4 rule

A forming H4 uses only M5 bars whose five-minute intervals have completed. Its contour may change on each newly completed M5 and is not final.

## MT5 rendering contract

- use one transparent `CCanvas` bitmap-label layer, not thousands of `OBJ_TRIANGLE` chart objects;
- map price vertically and keep contour width proportional to the current H4 screen slot, so the distribution remains readable under zoom;
- use 48 contour intervals by default and allow `24..96`;
- render one transformed H4 candle; never draw the ordered M5 path, M5 candles, or a raw occupancy histogram;
- hide native candles by default and restore their colors on indicator removal;
- show 60 H4 slots by default, capped at 200;
- rebuild on a newly completed M5, changed H4 history, or chart zoom/resize/scroll;
- attach only to H4;
- use a clean chart without `V10HAOverlay`; a co-mounted V10 HA body can visually conceal the Wave Candle even though the canvas is valid.

## Prohibited interpretation

V0.4 defines no score, regime label, entry gate, retry rule, cooldown, sizing map, Hard SL, destination, or exit. Do not infer a hidden threshold from contour width, bulge count, tone, median, or counterflow fraction.

Evidence observed under v0.1-v0.3 cannot be silently pooled with v0.4. Any further semantic change requires a new version and checkpoint.
