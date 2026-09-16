# V10 Regime / Reverse-Admission and Main-Clock Checkpoint

Date: `2026-09-17`  
Status: `CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY`  
Market: `GOLD# ONLY`  
Base GitHub HEAD at study start: `95536c3ef250f4eb217a6490b4e3b10f86dbc7d5`

## 1. Why this checkpoint exists

The bounded-m3 equity curve showed an important distinction:

```text
bad periods did not simply have "more losses"
good periods often had similar recurring gross loss
but large trend runs produced much more gross profit
```

A manual June-2025 review then exposed a second problem:

```text
old-direction FAST NHA
-> exit old campaign
-> the same HA color is immediately treated as new opposite PHA
-> enter opposite direction
-> loss
-> reverse again
-> loss
```

The new research question became:

> Should a FAST opposite HA be both an exit and an automatic reverse-entry authority?

Current evidence says no. `EXIT` and `REVERSE ADMISSION` are different decisions.

## 2. June vs October: loss did not disappear in the good month

Selected-entry cohort diagnostics:

| 2025 period | Gross profit | Gross loss | Net |
|---|---:|---:|---:|
| June | +543.29 | -1,088.42 | **-545.13** |
| October | **+3,553.17** | -879.52 | **+2,673.65** |

The difference is dominated by the right tail of profitable trend participation, not by the disappearance of losses.

This supports the interpretation:

```text
large trends -> pay for recurring false starts
few large trends -> recurring loss dominates the month
```

## 3. Exact NHA -> opposite k1 reversal diagnostic

Strict definition:

```text
old campaign natural FAST-NHA exit time
== new opposite run k1 decision time
```

### June 2025

```text
31 exact immediate reversals
6 wins / 25 losses
WR 19.4%
PF 0.612
PnL -211.94
```

### October 2025

```text
14 exact immediate reversals
6 wins / 8 losses
WR 42.9%
PF 1.805
PnL +347.23
```

Therefore a universal post-NHA waiting rule is also unsupported. Immediate reversal is bad in some regimes and valuable in others.

## 4. Flip-cluster evidence

June contained explicit alternating losing chains. The clearest example was approximately:

```text
2025-06-09 12:00 -> 2025-06-12 12:00
8 consecutive losing reversal campaigns
UP -> DOWN -> UP -> DOWN -> UP -> DOWN -> UP -> DOWN
combined about -295.77
```

Other losing flip chains also occurred during June.

The important semantic conclusion is:

```text
"old trend ended"
!=
"new opposite trend is now valid"
```

## 5. HA formula and LTF confirmation research

### Slower H4 HA as universal confirmation

STD/SLOW HA reduced some chop but delayed too much profitable trend participation. They are better treated as context than as universal reverse-entry gates.

### Close-heavy FAST `w4/a0.25`

A close-heavier FAST representation produced a small consumed-data improvement:

```text
PnL +15,065.51
PF ~1.57
units 2,277
June -508.53
October +2,673.65
```

It did not solve alternating-run chop by itself.

### LTF HA delivery

A simple M15/M30/H1 body-flow 2-of-3 agreement improved the total diagnostic result to roughly `+15.0k`, but the June alternating cluster often showed local LTF agreement in each new direction.

Interpretation:

> Local directional delivery can be real for a few hours even while the larger market is alternating between bursts.

Therefore direction confirmation and regime detection must be separated.

## 6. MA and ADX / DI studies

### EMA hard gate

`EMA8/21` direction gating:

```text
PnL ~+12,894
PF ~2.02
June -181.95
October +2,302.98
```

It improves trade quality but deletes too much trend right tail.

### ADX hard gate

An ADX28 strength gate:

```text
PnL ~+12,081
PF ~1.92
June -19.83
October +1,375.73
```

ADX is useful as a chop sensor but too destructive as a universal participation gate.

### DI hard gates

DI direction agreement showed useful information but also removed too much profitable participation when used globally.

## 7. Best current semantic use: conditional NEUTRAL

The strongest family did **not** use ADX as a hard entry filter.

Instead:

```text
FAST NHA
-> exit old campaign

if regime is normal/trendable
-> new FAST direction remains usable

if regime is chop-risk
-> NEUTRAL
-> wait for independent new-direction organization
```

Candidate regime coordinates included:

```text
ADX28 relative weakness
H4 path efficiency
recent H4 flip activity
```

Candidate directional confirmation coordinates included:

```text
EMA direction
DI direction
modified HA phase
M15/M30/H1 HA delivery
```

No absolute ADX value, efficiency threshold, cooldown, or waiting-bar count is promoted.

## 8. Consumed-data conditional-NEUTRAL diagnostics

Best scan result:

```text
regime:
ADX28 weak
AND
4-H4 path efficiency weak

NEUTRAL release:
DI14 agreement
OR
EMA8/21 agreement

PnL +17,900.26
PF 1.853
units 1,906
2025 +8,211.63
2026 +9,688.63
June -316.49
October +2,685.72
```

This is a **selection-biased consumed-data upper bound**, not a strategy candidate ready for promotion.

A more conservative 12-H4 efficiency representation produced:

```text
PnL +17,574.46
PF 1.786
units 2,029
2025 +7,961.81
2026 +9,612.65
June -224.49
October +2,828.57
L>=6 positive gross-profit retention ~96.6%
```

A stronger confirmation variant requiring `DI28 AND EMA8/21` produced:

```text
PnL +17,378.25
PF 1.850
June -100.09
October +2,882.87
```

Again, these are post-hoc consumed-data scans.

## 9. Current state interpretation

The useful decomposition is now:

```text
Layer 1: REGIME
Is a new reversal direction trustworthy at all?

Layer 2: DIRECTION
If it is trustworthy, which direction is organized?
```

Roles suggested by evidence:

```text
FAST H4 HA        -> campaign clock / old-campaign exit
ADX               -> trend-strength / regime sensor
H4 efficiency     -> directional persistence vs alternating path
recent flips      -> churn context
EMA               -> medium-horizon directional axis
DI                -> directional pressure
M15/M30/H1 HA     -> local delivery
STD/SLOW HA       -> broader phase / maturity context
```

## 10. H4 vs H1 main clock

The same mechanical HA structure was also tested with the main clock moved from H4 to H1.

Local H4 reconstruction:

```text
2,491 entries
PnL +10,168.07
PF 1.375
DD ~2,153
+270.5R
```

H1 FAST main:

```text
9,477 entries
PnL +2,031
PF 1.036
DD ~2,547
+29.4R
max concurrent 24
```

H1 first-PHA only:

```text
2,954 entries
PnL +554
PF 1.029
-20.2R
```

Slower H1 representations improved the H1 result but did not match H4 quality:

```text
H1 STD   +9,241 / PF 1.147
H1 SLOW  +5,533 / PF 1.069
H1 w4/a0.25  -917 / PF 0.984
```

A future-only H1 early-third Oracle remained extremely strong (`~+34,373 / PF 10.65`), proving H1 contains trend information; the problem is causal signal-to-noise.

Current project direction:

```text
H4 remains the main campaign clock.
H1/M30/M15 remain internal delivery / regime / confirmation layers.
```

## 11. What is supported vs not supported

Supported as a research direction:

```text
EXIT != REVERSE ADMISSION
LONG / NEUTRAL / SHORT is more natural than forced LONG / SHORT
regime and direction should be modeled separately
H4 remains the main clock
```

Not promoted:

```text
ADX28
4-H4 or 12-H4 efficiency
EMA8/21
DI14 / DI28
any percentile or absolute threshold
any fixed wait / cooldown
any single scanned indicator combination
```

## 12. Result artifact

See:

`results/V10_REGIME_REVERSE_ADMISSION_SUMMARY_20260917.csv`

This summary persists the major session-recorded consumed-data diagnostics. The reverse/regime study does not yet have the same row-level reproducibility spine as the later HA-risk study; do not overstate precision beyond the persisted summary.
