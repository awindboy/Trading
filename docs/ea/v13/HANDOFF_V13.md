# V13 handoff

Last synchronized: `2026-09-28`
Status: `BASELINE 0 FROZEN / HA-7 REJECTED / HA-8A FIRST COMBINATION MODEL DIAGNOSTIC COMPLETE / NO ACTION`
Market: `GOLD# ONLY`
GitHub SSOT base checked for this update: `53457bf5a38b0da0b77da094b6ea0223bc238fab`

## Resume point

V13 has completed the HA representation/observation program through HA-6 and
performed exactly one HA-7 action experiment. **Baseline 0 has not changed.**
The first deterministic action candidate failed because it removed economically
important continuation-tail Children despite elevated reversal probability.

HA-8A's first causal combination model diagnostic is now complete. The next
scientific step, if pursued, is a separately frozen **economic lifecycle
target** that tests repeated losing Journeys and right-tail preservation. It
is not another indicator threshold sweep or an EA modification.

The first HA-8A receipt is
`results/V13_HA8A_COMBINATION_MODEL_RECEIPT_20260928.md`. In 3,338
chronological OOF decisions, H4+H1 already captured most three-H4 flip
information (Brier `0.22608`); the best expanded combination reached only
`0.22530`. Its highest-risk 471 add-on Children had 287 losses but still
contributed `+513.61` idealized points, with profitable long-Journey false
warnings. **No model, score, filter, exit or sizing rule was promoted.**

## Frozen Baseline 0

```text
completed standard H4 HA only
same-color run = Journey
Child #1 on qualifying flip, then one Child per completed same-color H4
maximum 10 successful Children
first opposite completed H4 = close all
same event then starts opposite Journey after close-all
1 fixed unit per Child
no SL / no TP / no filters / no ML action
```

Canonical window: `2024-01-01 .. 2026-08-28 available GOLD# history`.

Structural sanity remains:

```text
closed Journeys: 965
closed Children: 3,858
gross net points: +8,147.11
Journey PF: 1.2597
Child PF: 1.2000
```

The extended actual-tick MT5 run remains diagnostic only because it extends
beyond the frozen cutoff and used 1:500 rather than 1:100 leverage. Exact-window
official economic receipt is still pending.

## What HA-0..HA-5 established

- HA morphology is richer than color, but body/Delta/wicks are overlapping
  geometry rather than independent votes.
- Standard HA captures long persistence at the cost of delayed reversal
  confirmation and giveback.
- D1 standard HA adds little next-H4 distinction.
- H1 opposition is informative but not safe: 735/1,395 ending-H1-opposed
  decisions did not flip next H4, and all 88 long Journeys contained an H1
  opposition warning.
- Ordered H1 path matters: repair differs from persistent/unrepaired opposition,
  but pooled effects shrink after H4 morphology matching.
- Causal raw swing rejection/return helps describe some transition states but
  has limited coverage and major long-Journey false warnings.

## HA-6A — HASTOC10

Formula parity was checked against the published HASTOC sample using:

```text
D_t = HA_OPEN_t - HA_CLOSE_t
HASTOC10 = 100 * (D_t - min(D[t-9:t])) / (max(D[t-9:t]) - min(...))
```

Journey-oriented HASTOC quintiles showed strong pooled ordering:

```text
Q1 weakest  next flip 35.8%   flip<=3 66.4%   remaining favorable 0.63 ranges
Q5 strongest next flip  9.3%   flip<=3 44.6%   remaining favorable 0.95 ranges
```

But after H4 morphology, Delta/wick, H1 and HA-5 matching, the independent
separation shrank materially. Weak HASTOC appeared in 84/88 long Journeys; 261
of 337 weak-tail decisions did not reverse next H4. Retain as a state feature,
not an exit.

## HA-6B — moving-average context

### EMA50 raw-close level/slope

```text
slope opposed: 1,360 decisions, 29.71% next flip
slope aligned: 2,745 decisions, 20.36%
position opposed: 1,451 decisions, 26.95%
position aligned: 2,654 decisions, 21.55%
```

After prior-state matching, residual next-H4 separation was only about 3 pp,
while the 3-H4 horizon retained about 9 pp. EMA50 is slower regime context.
Long-tail warning: slope opposition appeared in 37/88 long Journeys; 128/129
warnings did not flip next H4 and 3.44 ranges of favorable movement remained at
the median.

### EMA20 High/Low envelope

```text
not beyond directional boundary: 27.56% next flip / 62.09% within 3
beyond boundary:                 20.23% / 52.00%
```

After the full prior state stack the supported comparison was only 1,020/4,105
decisions. In long Journeys, not-beyond occurred in 62/88 Journeys and 190/191
warnings did not flip next H4. No EMA gate/exit.

## HA-6C — ATR normalization

ATR14 was used as a coordinate only. Median H4 ATR14 rose from `11.99` in 2024
to `41.01` in 2026. Raw price-unit HA/EMA measures therefore drift strongly.
ATR normalization reduced yearly median drift, e.g.:

```text
|HA Delta| raw max/min 3.91x -> ATR-normalized 1.10x
|raw Close - HA Close| 3.86x -> 1.03x
|HA Close - EMA50| 3.89x -> 1.23x
```

ATR level itself did not provide a useful monotone transition selector. Existing
trailing-20-H4 range normalization remains at least as stable for lifecycle
outcomes. No ATR filter/SL/TP/sizing authority.

## HA-6D1 — ADX Wilder 14

- ADX strength is genuinely different from instantaneous HA morphology but only
  weakly separates lifecycle state and is unstable by year/side.
- DMI direction looks stronger raw but correlates heavily with EMA50/EMA20
  context (`+0.862` / `+0.908`).
- ADX falling is directionally consistent raw but its independent next-H4
  increment falls to nearly zero after the full prior-state stack.
- Long Journeys are heavily falsely marked: ADX falling occurs 355 times in 71
  long Journeys, with 336 not flipping next H4 and 3.38 ranges median favorable
  movement still remaining.

HA-6D stop condition met. SuperTrend was not tested and is not judged.

## HA-6E — tick-volume participation

Data semantics/quality:

```text
7,199 H4 rows
0 duplicate H4 timestamps
0 zero tick-volume H4 rows
real volume nonzero rows: 0
M1 summed tick volume -> H4 tick volume: 7,199/7,199 exact
```

Absolute H4 tick-volume median drifted `25,022 -> 37,382 -> 56,328.5` from
2024 to 2026, so absolute tick count is unusable cross-era. The fixed research
coordinate is:

`relative_tick_volume20 = current H4 tick volume / median(previous 20 same-H4-slot tick volumes)`

Its overall Q1-to-Q5 next-H4 flip gradient was `28.5% -> 19.7%`, but matching
H4 morphology reduced the difference to about `0.65 pp`; universal volume
filtering is therefore rejected.

The important interaction was `persistent_opposition`: high participation was
associated with more transition. In the localized H1-participation audit:

```text
persistent Q1: n=44, next flip 36.4%, flip<=3 56.8%, remaining favorable 0.85
persistent Q5: n=44, next flip 65.9%, flip<=3 88.6%, remaining favorable 0.43
```

But localized H1 activity and whole-H4 relative activity had rho `0.973`, so do
not count them as two signals. Long-Journey false warnings remained.

## HA-7 — first action experiment: REJECTED

Frozen action:

```text
on original Journey bar 2..10 only:
  if h1_path_state == persistent_opposition
  and relative_tick_volume20 > 1.0:
      skip only that bar's add-on Child
keep existing Children and Journey open
never veto Child #1
never backfill a skipped Child
```

`1.0` was semantic (above own same-slot trailing median), not optimized.

Result:

```text
Baseline: 3,858 Children, +8,147.11 points, realized-Journey DD 3,659.45
Variant:  3,769 Children, +8,069.18 points, realized-Journey DD 3,690.36
Skipped: 89 Children
Net change: -77.93 points
DD change: +30.91 points (worse)
```

The skipped set had 38 winners / 51 losers but still contributed +77.93 points.
Inside >=10-bar Journeys, 15 skipped Children contributed **+341.09 points**
(11 winners / 4 losers). The action directly damaged the right tail. Do not
tune the threshold, add side/year exceptions, invent a late-Child cap, or turn
the same state into an exit.

## Central inference after HA-7

V13 repeatedly observes states with elevated reversal hazard, yet deterministic
rules fail because continuation tails dominate payoff. The missing problem is
conditional discrimination of *true transition* versus *temporary weakness*.

That is now the purpose of HA-8A.

## Immediate next work after the first HA-8A diagnostic

The first frozen `flip_within_3` contract and chronological model ladder are
complete; do not rerun/tune them to rescue a trade filter. Its target was:

`opposite H4 HA occurs within next 3 completed H4 bars`

For a distinct next target, freeze the decision timestamp, label and economic
failure definition *before* fitting. Reuse causal features already measured.
Simple base-rate/logistic baselines remain the first comparison; use a shallow
nonlinear model only if a stable residual justifies it. In particular, compare
actual losing-Journey/repeated-loss separation with false alarms in the
profitable long-Journey tail. Do not call consumed-data OOF independent
validation.

The roadmap allowed this complexity ladder, but the first diagnostic stopped
at the constant and regularized logistic baselines (no tree was run):

1. base rate;
2. regularized logistic regression;
3. shallow tree / small Random Forest only if justified.

Validation:

- chronological walk-forward/out-of-fold only on consumed 2024-2026 history;
- no random train/test split as the primary evidence;
- no in-sample prediction presented as strategy result;
- report calibration/discrimination by year, side, Journey age and long-tail
  exposure;
- compare against simple baselines such as H1 path alone and HASTOC alone;
- no trading threshold/action mapping from the first HA-8A diagnostic;
- untouched future data remains necessary for promotion.

## Do not resume with

- SuperTrend just because it was next to ADX in an external product;
- RSI/MACD/another indicator stack without a distinct information mechanism;
- threshold search over HASTOC/EMA/ATR/ADX/volume;
- side/year special cases mined from consumed data;
- a new exit or Child veto from the first HA-8A flip score without a distinct
  economic-lifecycle contract and validation;
- production/EA modification from the rejected HA-7 experiment.
