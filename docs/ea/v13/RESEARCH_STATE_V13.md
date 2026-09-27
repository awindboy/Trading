# V13 research state

Last synchronized: `2026-09-28`
Status: `BASELINE 0 FROZEN / HA-7 REJECTED / HA-8A FIRST DIAGNOSTIC COMPLETE / X1-X2 DOLLAR PROXIES NEGATIVE / NO ACTION`
Market authority: `GOLD# ONLY`
GitHub SSOT base checked for this update: `53457bf5a38b0da0b77da094b6ea0223bc238fab`

## 1. Active generation and strategy skeleton

V13 remains a reset generation. V12 and earlier strategies are historical
context only and do not silently re-enter V13.

```text
completed standard H4 HA
-> same-color Journey
-> one Child per completed same-color bar
-> max 10 successful Children
-> first opposite completed H4 closes all
-> same event then starts opposite Journey
-> fixed 1 unit per Child
```

No Hard SL, TP, trailing, break-even, partial close, session/news/volatility
filter, MA/oscillator gate, CRT, liquidity rule, Wave rule or ML action is part
of Baseline 0.

## 2. Frozen comparison window and causal timing

Primary window: `2024-01-01 through 2026-08-28 available GOLD# history`.
2022 history is warm-up/state only. Decisions use only completed bars and become
known at the next executable print. Future labels are stored separately.

## 3. Baseline structural/economic sanity

Idealized next-H4-open reconstruction:

```text
closed Journeys: 965
closed Children: 3,858
gross net points: +8,147.11
Journey PF: 1.2597
Child PF: 1.2000
```

Closed-Journey Child distribution remains:

```text
1:187, 2:202, 3:139, 4:113, 5:79,
6:59, 7:40, 8:33, 9:25, 10:88
```

The existing extended real-tick MT5 run confirms structure through the canonical
prefix but is not the official economic receipt because it extends through
2026-09-26 and uses 1:500 leverage. The exact-window 1:100 receipt remains
pending.

## 4. Research evidence — HA-0 through HA-5

### HA-0/1 — standard HA ledger and morphology

The standard-HA decision ledger is causally reproducible. HA body strength,
Delta magnitude, opposite-wick presence/reappearance and contraction describe
persistence/weakening, but they are overlapping geometry rather than independent
signals.

### HA-2 — lifecycle lag and giveback

Standard HA's smoothing benefit has a cost:

```text
median raw favorable extreme -> opposite HA exit lag: 7.35 hours
median raw favorable extreme -> HA exit giveback: 21.41 GOLD price
```

This is a lifecycle description, not an exit threshold.

### HA-3 — alternate HA representations

FAST-R25 increases switching and reduces lag/giveback; PRE-EMA2 slows switching
and increases lag/giveback. PRE-EMA2 and POST-EMA2 had identical open/close/color
chronology under the tested linear formulas while wick morphology differed.
No alternate representation was promoted.

### HA-4 — D1/H1 context and integrated state

D1 opposition adds little next-H4 distinction. H1 is more informative but unsafe:

```text
last-H1 opposed decisions: 1,395
next-H4 flips: 660
not next-H4 flip: 735
```

Ordered H1 paths separate repaired from ending opposition, but pooled effects
shrink inside comparable H4 morphology. Every one of the 88 >=10-bar Journeys
contained at least one H1 opposition warning.

### HA-5 — causal raw-price swing probe

M1 chronological reconstruction confirmed H4 OHLC parity and enforced 2-left /
2-right causal swing confirmation. `return_inside` and rejection states raise
transition hazard in some contexts, but coverage is limited and effects shrink
inside H4 morphology. In long Journeys these states frequently fire without an
immediate reversal. No swing rule promoted.

## 5. HA-6A — HASTOC / HA-derived momentum

Formula reproduced against the published sample before outcome inspection.
Journey-normalized HASTOC10 pooled ordering:

| HASTOC state | Next-H4 flip | Flip within 3 | Peak already | Median remaining favorable |
| --- | ---: | ---: | ---: | ---: |
| Q1 weakest | 35.8% | 66.4% | 48.8% | 0.63 ranges |
| Q2 | 27.8% | 60.3% | 40.6% | 0.76 |
| Q3 | 23.8% | 57.2% | 38.5% | 0.77 |
| Q4 | 20.7% | 53.7% | 36.2% | 0.81 |
| Q5 strongest | 9.3% | 44.6% | 27.6% | 0.95 |

Raw Q1-Q5 next-flip gap is +26.6 pp and has the same sign across all six
year×side slices. However:

```text
within H4 body/raw-close geometry: +9.1 pp
+ Delta contraction / wick:        +3.4 pp
+ ordered H1 path:                 +2.7 pp on supported extreme cells
+ HA-5 state:                      +4.9 pp on only 811/4,105 rows
```

Weak HASTOC occurs repeatedly in long Journeys: Q1 appears in 84/88; 261/337
such tail decisions do not flip next H4. HASTOC survives as a candidate model
feature, not an action rule.

## 6. HA-6B — moving-average context

### HA-6B1 EMA50

Raw next-H4 rates:

```text
slope opposed 29.71% vs aligned 20.36%
position opposed 26.95% vs aligned 21.55%
```

After H4 morphology + H1 + HA-5 + HASTOC matching, next-H4 increment is only
~3 pp while three-H4 increment remains ~9 pp. EMA50 is best interpreted as a
slower regime context.

Tail counterexample: slope opposition appears in 37/88 long Journeys and 128/
129 warnings do not flip next H4; median 3.44 favorable ranges remain.

### HA-6B2 EMA20 high/low envelope

```text
not beyond directional boundary: 27.56% next-H4 / 62.09% <=3
beyond boundary:                 20.23% / 52.00%
```

After the complete prior stack only 1,020/4,105 rows support a matched
comparison. In long Journeys, not-beyond appears 191 times across 62/88
Journeys; 190/191 are not next-H4 flips and 3.88 favorable ranges remain.
No EMA action authority.

## 7. HA-6C — ATR normalization

Completed-H4 ATR14 is used as a coordinate only. GOLD volatility changes
materially across the sample:

| Year | median ATR14 | median raw H4 range |
| --- | ---: | ---: |
| 2024 | 11.99 | 10.26 |
| 2025 | 20.27 | 18.98 |
| 2026 | 41.01 | 38.78 |

Normalization reduces price-unit drift:

```text
|HA Delta| raw yearly max/min 3.91x -> ATR 1.10x
|raw Close - HA Close| 3.86x -> 1.03x
|HA Close - EMA50| 3.89x -> 1.23x
|EMA50 slope| 3.82x -> 1.23x
```

ATR level quintiles show little monotone next-H4 separation. Existing trailing-
20-H4 median-range outcome normalization is at least as stable as ATR14 for
remaining excursion/giveback. No ATR signal or risk-rule authority.

## 8. HA-6D1 — ADX Wilder / DMI

ADX14 quintiles only weakly separate next-H4 flip (`26.1%` Q1 vs `21.3%` Q5)
and sign reverses in some year/side slices. ADX is not just HA morphology, but
its predictive ordering is weak.

DMI alignment is stronger raw:

```text
Journey-aligned: 21.7% next flip / 54.5% <=3
Journey-opposed: 27.3% / 60.7%
```

Yet Journey DI margin correlates `+0.862` with ATR-normalized EMA50 slope and
`+0.908` with EMA20 boundary distance. ADX falling is directionally consistent
raw but its increment falls to approximately zero after the complete prior
state stack.

Long-Journey false warnings are decisive: ADX falling marks 355 decisions in
71/88 long Journeys; 336 do not flip next H4 and median 3.38 favorable ranges
remain. HA-6D stop condition met. SuperTrend not tested.

## 9. HA-6E — tick-volume participation

### Data quality and semantics

The supplied GOLD# feed has real volume zero; only tick volume is populated.
Tick volume is treated as broker-feed activity, not centralized traded volume.

```text
H4 rows: 7,199
duplicate timestamps: 0
zero tick-volume H4 rows: 0
nonzero real-volume H4 rows: 0
M1 summed tick volume -> H4 parity: 7,199/7,199 exact
```

Absolute median H4 tick volume drifts:

```text
2024 25,022
2025 37,382
2026 56,328.5
```

The frozen coordinate therefore normalizes by the previous 20 bars of the same
H4 start slot. This cuts year-median max/min to 1.048x and slot-median max/min
to 1.017x.

### HA-6E1 full-H4 relative activity

```text
Q1 next flip 28.5% / <=3 61.3% / rem fav 0.61
Q5 next flip 19.7% / <=3 52.1% / rem fav 0.93
```

But H4 morphology matching reduces the next-H4 Q1-Q5 difference to ~0.65 pp.
Universal low/high volume filters are not justified.

### HA-6E2 persistent H1 opposition interaction

The H1 path reconstruction matches the existing ledger on all 4,108 decisions.
Only `persistent_opposition` shows a strong participation interaction:

```text
Q1 n=44 next flip 36.4% <=3 56.8% peak already 47.7% rem fav 0.85
Q5 n=44 next flip 65.9% <=3 88.6% peak already 84.1% rem fav 0.43
```

Journey-cluster bootstrap Q5-Q1:

```text
next-H4: +29.5 pp, approx 95% interval +7.8..+50.3 pp
<=3 H4:  +31.8 pp, approx +14.1..+48.9 pp
```

However H1-opposition-localized activity and whole-H4 relative activity have
rho `0.973`; they are not separate votes. Long-tail false warnings remain.

## 10. HA-7 — first action experiment

Frozen Child-admission action:

```text
continuation bar with original journey_bar 2..10
AND persistent H1 opposition
AND relative_tick_volume20 > 1.0
=> suppress only this bar's add-on Child
```

No threshold sweep. Existing positions/Journey unchanged, Child1 never vetoed,
no backfill.

### Result

| Metric | Baseline | Variant | Change |
| --- | ---: | ---: | ---: |
| Children | 3,858 | 3,769 | -89 |
| Net points | +8,147.11 | +8,069.18 | **-77.93** |
| Child PF | 1.19995 | 1.20182 | +0.00187 |
| Journey PF | 1.25972 | 1.26232 | +0.00260 |
| realized-Journey max DD | 3,659.45 | 3,690.36 | **+30.91 worse** |

Skipped set:

```text
38 winners / 51 losers
net contribution +77.93 points
gross +841.61 / -763.68
```

The action loses because the minority winners are larger. Right-tail damage is
especially important:

```text
15 skipped Children in 15 >=10-bar Journeys
11 winners / 4 losers
original net contribution +341.09 points
```

Result: **REJECTED / NO EA CHANGE**. Do not tune the semantic 1.0 boundary,
search Child-slot cutoffs, add side/year exceptions, or convert the state into
an exit.

## 11. Cross-stage conclusion

The research has now repeatedly shown that transition probability and economic
action value are different objects. Weakness states can raise near-term reversal
hazard while continuation tails still dominate P/L. This explains why simple
filters repeatedly fail despite visually and statistically meaningful warning
states.

The next scientific question is conditional:

> Can a causal combination of the already measured state variables distinguish
> genuine H4 Journey transition from temporary weakness while preserving the
> large continuation tail?

## 12. HA-8A first model diagnostic and next boundary

HA-8A is a **state-model evaluation**, not a strategy change. Its first
combination-model ladder is complete as consumed-development evidence; see
`results/V13_HA8A_COMBINATION_MODEL_RECEIPT_20260928.md` for exact results.

In 3,338 chronological OOF decisions, H4+H1 Brier/AUC were `0.22608/0.6667`.
Adding HASTOC, relative tick participation, causal raw swing and EMA50 only
reached best Brier `0.22530` and best AUC `0.6718`, with inconsistent fold
gains. The activity model's 471 highest-risk OOF add-on Children had 287
losses and 184 winners but **net +513.61 idealized price points**. Its 66
long-Journey false warnings contributed +2,471.13. This model does not
separate economically bad Children from valuable temporary weakness, and no
score/action threshold is authorized.

The next question, if pursued, is a separately frozen economic-lifecycle
target emphasizing repeated losing Journeys versus large continuation wins.
Do not alter the first HA-8A label or refit on this consumed outcome to claim
an untouched result.

First evaluated label:

`flip_within_3 = opposite standard-H4 HA appears within the next 3 completed H4 bars`

Feature families are limited to causal variables already justified for study:

- standard H4 morphology / Delta / wick / streak;
- ordered H1 path;
- HA-5 raw-swing interaction;
- HASTOC10;
- EMA50/EMA20 context;
- ATR-normalized morphology/context;
- ADX/DMI;
- normalized tick participation and the persistent-H1 interaction.

Validation requirements:

1. freeze feature and target contract first;
2. use chronological walk-forward/out-of-fold predictions on consumed history;
3. compare constant/base-rate and simple single-family baselines;
4. fit regularized logistic regression first;
5. add only a shallow nonlinear model if residual structure justifies it;
6. report calibration, discrimination and error decomposition by year, side,
   Journey age and long-Journey/tail status;
7. keep model predictions observation-only in HA-8A;
8. require untouched future data and later action contract before production.

## 13. Outstanding execution item

The exact-window official Baseline-0 MT5 actual-tick receipt remains required.
It does not block HA-8A observation/model research, but no economic promotion
should bypass it.

## 14. X1 external ECB dollar-proxy observation

X1 froze an economic target at Journey birth: whether the complete Baseline-0
Journey loses, with repeat-loss and right-tail diagnostics. Its only new
information family was the official daily ECB EUR/USD reference rate, allowed
only after a conservative two-broker-calendar-day publication lag. The source
was registered before outcome evaluation. This is a bilateral, daily proxy,
**not** DXY or intraday H4 dollar data.

Across 777 chronological OOF closed Journeys, 590 lost and 441 were repeat
losses. Adding ECB to H4/H1 worsened Brier `0.18706 -> 0.18888`, worsening
each of four test blocks. The highest predicted-loss 20% contained 120/156
losses versus 122/156 for H4/H1 alone; repeat losses fell from 89 to 85.
The ECB bucket contained +3,739.80 idealized net price points, including
10 >=10-bar winning Journeys worth +6,710.82. **Negative proxy result; no
filter/model/action promotion.** Read the X1 contract and result receipt for
source/timing limits. A true intraday external-data study would need a new
contract; X1 is not evidence that all dollar information lacks value.

## 15. X2 same-broker EURUSD# H4 external observation

The XM MT5 API returned 7,199 GOLD# H4 bars exactly matching the frozen
GOLD# CSV in timestamps and OHLC, plus 7,253 EURUSD# H4 bars covering every
GOLD# timestamp. X2 causally joined the same **completed** H4 FX bar at all
4,108 decisions, then tested a one-/three-bar normalized bilateral dollar
proxy and a separately staged side interaction at Journey birth. Its target,
OOF blocks and economics were the same as X1, but the data were truly H4.

On 777 chronological OOF Journeys, H4/H1 Brier `0.18706` worsened to
`0.18810` with FX and `0.18865` with the interaction; **all four** folds
worsened. The top predicted-loss 156 had 121 losses and 92 repeat losses
with FX (versus 122 and 89 baseline), but was net **+1,376.87** idealized
points and included 11 profitable >=10-bar Journeys worth +3,593.00.
The interaction lowered the loss count to 120 and flagged even more tail.
**Negative observation; no action.** Read the X2 contract/receipt. A
broker symbol named `USDX-DEC26` displayed old history despite a 2026-09-10
start_time after the cutoff, so it was rejected as a historical source.
