# V6-003B/C — Direction-First Indicator Authority Results

Status: `CLOSED AS CONVENTIONAL-INDICATOR AUTHORITY / SIMPLE PRICE-STATE SIGNAL REMAINS RESEARCH-ONLY`
Date: `2026-08-29`
Base GitHub HEAD: `982839b0a1ea166fc534272f2024a72cedfb8326`
Production authority: `NONE`
GOLD 2021: `UNTOUCHED`

## 1. Why this child was necessary

The first V6-003A pass still asked too much of the old event direction:

```text
local event says LONG/SHORT
-> prior aligned or opposed?
```

That did not fully test the intended architecture.

V6-003B/C corrected the causal order:

```text
completed HTF indicator state
-> prior declares LONG / SHORT / NEUTRAL before the sweep event finalizes direction
-> matching liquidity sweep/recovery + M5 transition confirms timing/geometry
-> Entry/SL remain structural
```

The first B test also removed `m1_direct_transfer` as eligibility authority to see whether a true direction layer could recover opportunities that V3 microstructure had excluded.

## 2. Direction-first opportunity universe

Frozen V3 local reaction substrate before the `m1_direct_transfer` filter:

```text
M15 persistent DC liquidity
-> atomic same-M1 sweep/recovery
-> pre-sweep M5 owner opposite reaction
-> sweep extreme intact
-> first completed M5 owner transition
```

After causal D1 availability and valid 50% pullback geometry:

```text
1391 broad opportunities
620 direct-transfer
771 non-direct
```

The prior is sampled at `sweep_time` from completed bars only.

## 3. Frozen prior families

V6-003B:

- `DP1_DMI_H1`: H1 Wilder DMI(14) sign.
- `DP2_DMI_H1H4`: H1/H4 DMI(14) consensus.
- `DP3_MACD_H1H4`: sign of EMA12-EMA26 on completed H1/H4, consensus.
- `C1_DISP_H1_24`: simple H1 24-bar signed displacement control.
- `S1_STRUCT_H1M30`: H1/M30 BOS-owner consensus control.

V6-003C conventional falsification atlas:

- `AR25_H1H4`: Aroon(25) H1/H4 consensus.
- `VI14_H1H4`: Vortex(14) H1/H4 consensus.
- `RSI14_H1H4`: Wilder RSI(14) above/below 50, H1/H4 consensus.

No parameter search, no ADX threshold, no score/weighted vote, no volatility scaling.

## 4. First genuine direction-first test — can prior replace direct M1 transfer?

The answer is **no** under the current H lifecycle.

| Prior | Confirmed broad opp | Accepted | WR | Avg positive R | EV R | Total R |
|---|---:|---:|---:|---:|---:|---:|
| H1 DMI14 | 479 | 444 | 21.85% | 2.992 | -0.128 | -56.75 |
| H1/H4 DMI14 | 355 | 336 | 21.73% | 3.113 | -0.106 | -35.75 |
| H1/H4 MACD | 392 | 364 | 23.63% | 3.148 | -0.020 | -7.25 |
| H1 DISP24 control | 500 | 460 | 23.48% | 3.146 | -0.027 | -12.25 |
| H1/M30 structure | 286 | 269 | 22.68% | 3.332 | -0.018 | -4.75 |

The recovered non-direct opportunities are generally weaker than the retained direct-transfer opportunities.

Example MACD:

```text
DIRECT fills:       146 / +1R 50.68% / +3R 26.71% / +5R 17.12%
RECOVERED NONDIRECT 223 / +1R 44.39% / +3R 21.97% / +5R 13.90%
```

Therefore:

> Direction authority does not make the local direct-transfer information disposable.

The hypothesis `indicator direction -> broad local timing is enough` is closed.

## 5. Direction-first with direct local confirmation

Keeping the frozen direct-transfer timing/quality condition changes the result materially.

Current event-direction-only direct control:

```text
620 opp
586 fills
560 accepted
WR 23.75%
avg positive 2.977R
EV -0.055R
total -31.0R
```

Selected direction-first direct results:

| Prior | Accepted | WR | Avg positive R | EV R | Total R |
|---|---:|---:|---:|---:|---:|
| H1 DMI | 190 | 24.74% | 3.064 | +0.005 | +1.00 |
| H1/H4 DMI | 139 | 21.58% | 3.125 | -0.110 | -15.25 |
| H1/H4 MACD | 146 | 26.71% | 3.154 | +0.110 | +16.00 |
| H1 DISP24 | 209 | 26.79% | 3.228 | +0.133 | +27.75 |
| H1/M30 structure | 113 | 24.78% | 3.295 | +0.064 | +7.25 |

This proves a causal direction-first layer can separate some useful local events from the negative unconditional direct population.

But MACD is not independent of the simpler price control:

```text
MACD vs DISP24 exact direction agreement on MACD-available direct events: 86.34%
Discordant fills where event matches MACD: +5R 11.54%
Discordant fills where event matches DISP24: +5R 22.58%
```

So MACD is downgraded rather than promoted.

## 6. Conventional indicator atlas

Direction-first direct economics:

| Prior | Accepted | WR | Avg positive R | EV R | Total R |
|---|---:|---:|---:|---:|---:|
| Aroon25 H1/H4 | 135 | 24.44% | 2.795 | -0.072 | -9.75 |
| Vortex14 H1/H4 | 104 | 26.92% | 3.027 | +0.084 | +8.75 |
| RSI14 H1/H4 | 117 | 29.06% | 2.956 | +0.150 | +17.50 |
| MACD H1/H4 | 146 | 26.71% | 3.154 | +0.110 | +16.00 |
| DISP24 simple control | 209 | 26.79% | 3.228 | +0.133 | +27.75 |

Aroon fails outright. Vortex is weak. RSI is the strongest conventional indicator result.

RSI also separates aligned from opposed local events:

```text
RSI aligned DIRECT: 117 accepted / EV +0.150R
RSI opposed DIRECT: 331 accepted / EV -0.122R
```

This is real directional separation on the consumed panel.

## 7. Recursive falsification of RSI

The required simpler control was frozen *after* the RSI result solely to test whether the indicator transformation itself mattered:

```text
C2 DISP14_H1H4
H1 sign(close - close[-14])
H4 sign(close - close[-14])
consensus else NEUTRAL
```

This preserves RSI's period count and H1/H4 consensus architecture while removing Wilder gain/loss transformation.

Result:

```text
RSI14 vs DISP14 H1/H4 direction agreement on jointly available direct events = 99.18%
```

Direct direction-first economics:

```text
RSI14 consensus:
117 accepted
WR 29.06%
avg+ 2.956R
EV +0.150R
total +17.50R

simple DISP14 consensus:
90 accepted
WR 30.00%
avg+ 3.250R
EV +0.275R
total +24.75R
```

Broad confirmation also favors the simpler control:

```text
RSI14 broad accepted 288 / EV +0.049R
DISP14 broad accepted 229 / EV +0.067R
```

Only three jointly available direct events disagree between RSI14 and DISP14 in a way that assigns the event to one side.

Therefore:

> The observed RSI directional effect is almost completely explained by simple multi-horizon signed price displacement.

Do not call RSI an independent indicator edge.

## 8. Breadth and statistical caution

DISP14 direction-first direct is promising as a *price-state* research clue but not a robust strategy:

```text
90 accepted
8 / 13 market-years positive EV
5 / 13 negative EV
several cells contain only 2-6 trades
```

Stratified market-year x direction permutation diagnostics for aligned-minus-opposed direct events:

```text
RSI14:
+1R p ~0.254
+3R p ~0.141
+5R p ~0.239
raw lifecycle R p ~0.167

DISP14:
+1R p ~0.243
+3R p ~0.172
+5R p ~0.133
raw lifecycle R p ~0.115
```

These are descriptive falsification diagnostics, not promotion tests. They do not support a strong independent claim.

## 9. Scientific conclusion

The corrected V6-003 direction research now establishes:

1. A prior can genuinely be placed before local event direction and used to decide LONG/SHORT/NEUTRAL.
2. Removing direct local-transfer information because a prior now owns direction adds too much noise.
3. With direct local confirmation retained, several trend-direction priors separate better from worse events.
4. DMI, MACD, Aroon, Vortex and RSI do not demonstrate an independent edge over simpler price displacement.
5. The strongest surviving clue is not a conventional indicator. It is **multi-horizon directional price persistence**.
6. That clue is still consumed-panel, thin, and not recurrent enough for strategy authority.

So the conventional-indicator direction-authority thesis is closed in its current form.

This does **not** restore local structure as sole direction authority. It instead redirects the next research question toward a simpler causal directional-state mechanism.

## 10. Next research direction

Do not run more conventional indicator windows/thresholds.

The next child should preregister a *directional state/mechanism* rather than another named indicator:

```text
multi-horizon directional persistence
+ explicit continuation-vs-reversal regime meaning
-> prior LONG / SHORT / NEUTRAL
-> direct local structure only for timing/geometry
```

It must explain why persistence should continue or fail, rather than just select another displacement horizon.

Possible mechanism questions for the next pre-outcome contract:
- whether the directional move is broad/persistent across horizons versus one impulsive leg;
- whether current volatility expansion represents continuation or rebound/reversal risk;
- whether prior direction survives local counter-move and reasserts causally;
- whether a prior can recover opportunities without replacing direct local information with noise.

Do not tune DISP14/24 on the consumed panel.

GOLD 2021 remains untouched.

## 11. Restrictions after this child

- no DMI/MACD/RSI/Aroon/Vortex period or threshold rescue;
- no RSI 70/30 rescue in the same consumed panel;
- no displacement-window tournament;
- no dropping direct-transfer merely to increase N;
- no indicator-only Entry;
- no production EA change;
- no GOLD 2021;
- no claim that `DISP14 aligned` is a strategy.
