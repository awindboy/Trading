# V13 HA-6 / HA-7 research synthesis

Date: `2026-09-27`
Status: `CONSUMED DEVELOPMENT EVIDENCE / BASELINE 0 UNCHANGED`
GitHub SSOT base: `40f97352e47c66cd3b952f74532b1b71969e79fd`

## 1. Purpose

This document records the complete conceptual result of the HA-6 complementary
family program and the first HA-7 action experiment. It is intended to prevent
a future session from re-running dead ends, over-reading a pooled statistic, or
forgetting why a statistically plausible warning failed economically.

For exact formulas, denominators and local output fields, the individual stage
contracts and receipts remain authoritative.

## 2. The research question entering HA-6

After HA-5, V13 already knew that:

- H4 HA morphology contains persistence/transition information;
- ordered H1 opposition can warn before H4 color changes;
- causal raw-price swing rejection/return contributes real-price structure;
- all of these produce substantial false warnings in long persistent Journeys.

HA-6 therefore asked whether a *genuinely different information family* could
add stable transition information without simply stacking lagged transforms.

The families were tested one at a time:

```text
HA-6A  HASTOC / HA-derived momentum
HA-6B  moving-average raw-price context
HA-6C  ATR normalization
HA-6D  ADX/DMI trend strength
HA-6E  tick-volume participation
```

## 3. HA-6A — HASTOC10

### Mechanism

HASTOC maps the signed HA body into its own recent ten-bar signed-body history.
V13 used the paper-consistent orientation and then mirrored it by Journey side so
that larger `journey_hastoc10` means the current signed HA body sits nearer the
strong end of its recent history.

### Main result

A very strong pooled monotonic relation exists: weak HASTOC corresponds to more
near-term transition. Q1 next-H4 reversal is 35.8% versus 9.3% in Q5.

However, the raw 26.6-point gap is not independent. After H4 body/raw-close,
Delta/wick, H1 path and raw-swing state are held comparable, only a modest
residual remains, with incomplete overlap. HASTOC one-bar change is even more
redundant with Delta contraction.

### Why no action

Weak HASTOC occurs inside 84 of the 88 long Journeys. Across 337 weak-HASTOC
long-tail decisions, 261 do not reverse next H4 and median favorable movement
remaining is still about 1.05 trailing-H4 ranges.

**Use going forward:** candidate state feature, especially for conditional
near-term transition timing. Not a threshold, exit or second momentum vote.

## 4. HA-6B — moving averages

### EMA50

EMA50 raw close level/slope adds a slower time-scale reference. Opposition is
associated with higher transition probability, but after existing state matching
only ~3 pp next-H4 increment remains while a larger ~9 pp difference persists
over three H4 bars.

This is consistent with **regime context**, not a precise transition trigger.

### EMA20 high/low envelope

The directional EMA20 High/Low boundary describes whether HA has extended past
a local raw-price mean envelope. It remains directionally ordered in pooled and
year/side diagnostics, but support thins sharply after prior-state conditioning.

### Why no action

Both MA warnings repeatedly occur inside profitable long Journeys. EMA50 slope
opposition: 128/129 long-tail warnings do not flip next H4. EMA20 not-beyond:
190/191 do not flip next H4.

**Use going forward:** regime/extension features for a conditional model. Do
not stack EMA alignment rules onto Baseline 0.

## 5. HA-6C — ATR normalization

### Mechanism

Gold's price-unit volatility changes drastically from 2024 to 2026. A fixed
price-unit HA Delta, wick or EMA distance can therefore mean different things in
different eras. ATR14 was introduced as a denominator, never as a gate.

### Main result

ATR normalization removes most of the era drift in morphology/displacement.
For example, yearly median |HA Delta| varies 3.91x in raw price but only 1.10x in
ATR units.

Yet ATR-normalized variables remain strongly correlated with existing normalized
morphology. ATR level itself has little monotone next-H4 transition separation.
The existing trailing-20-H4 median-range outcome coordinate is already as stable
or slightly better for remaining excursion/giveback.

**Use going forward:** normalize price-distance features when needed; retain the
existing trailing-range outcome coordinate. Do not create an ATR regime filter.

## 6. HA-6D1 — ADX Wilder / DMI

### Mechanism

ADX was attractive because directionless trend strength is conceptually
different from instantaneous HA body geometry. DMI also offers directional
movement information from raw H4 highs/lows.

### Main result

ADX level is indeed weakly correlated with HA morphology, but its lifecycle
separation is modest and unstable across year/side. DMI direction has stronger
raw ordering but is highly correlated with the already-measured EMA trend
context. ADX falling is the most consistent raw warning, yet its incremental
next-H4 effect nearly disappears after the full prior state stack.

### Why branch stopped

ADX/DMI warnings heavily mark long Journeys with substantial favorable movement
remaining. Complexity would rise faster than explanatory value if SuperTrend
were simply added next. The HA-6D stop condition was therefore met.

**Use going forward:** ADX/DMI may remain optional model features, but there is
no justification for a deterministic ADX/DMI/SuperTrend action stack.

## 7. HA-6E — tick-volume participation

### Data semantics first

The supplied GOLD# H4 export has populated tick volume and zero real volume.
M1 tick-volume sums reproduce H4 tick volume exactly on all 7,199 bars. Tick
volume is therefore usable as *broker-feed activity*, not centralized traded
volume.

Absolute tick counts drift more than 2x by year and strongly by H4 start slot.
A causal same-slot trailing-20 median denominator removes most of that drift.

### Universal activity result

Low relative activity is associated with higher reversal probability in the
pooled sample, but H4 morphology matching nearly removes the effect. This is not
an independent universal volume signal.

### Important interaction

When H1 opposition is **persistent** through the H4 bar, high relative activity
has the opposite meaning: it is associated with *more* transition. Localized
opposed-H1 activity gives a strong Q1/Q5 separation, but is almost the same
information as whole-H4 relative activity (rho 0.973).

The semantically fixed boundary `relative_tick_volume20 > 1.0` means only
"above its own same-slot trailing median." It was not selected for profit.
Within persistent opposition it raised reversal hazard, but long-Journey false
warnings remained substantial.

**Use going forward:** a conditional interaction feature, not a universal
volume filter.

## 8. Why HA-7 tested Child admission instead of Journey exit

Every prior warning family had already shown severe false exits in long
Journeys. The least destructive action was therefore chosen:

- do not close existing positions;
- do not end the Journey;
- do not alter Child #1;
- on a continuation bar only, skip one add-on Child when persistent H1
  opposition coexists with above-baseline relative activity.

This directly tested whether the elevated transition hazard was economically
useful *without* destroying the existing trend tail.

## 9. HA-7 result and failure mechanism

The trigger skipped 89 Children.

```text
Baseline net: +8,147.11
Variant net:  +8,069.18
change:       -77.93
Baseline realized-Journey DD: 3,659.45
Variant:                      3,690.36
change:                       +30.91 worse
```

The skipped set contained more losers than winners (51 vs 38), but the winners
were larger; the skipped set was +77.93 points overall. In >=10-bar Journeys,
15 skipped Children alone contributed +341.09 points.

This is the key economic lesson:

> A feature can improve reversal *probability* and still be harmful as an action
> because the conditional payoff distribution is asymmetric.

V13 therefore rejects the action and explicitly forbids trying to rescue it by
threshold, Child-slot, side or year mining on the same consumed data.

## 10. What information survived HA-6 for later modeling

The following should be treated as **features with distinct or partially
distinct semantic roles**, not as independent votes:

| Family | Semantic role | Main caveat |
| --- | --- | --- |
| H4 HA morphology | immediate smoothed price geometry | internal variables overlap |
| ordered H1 path | intrabar transition path | many false warnings in long trends |
| causal raw swing | actual traded-price structure | limited coverage / overlap |
| HASTOC10 | signed HA body relative to recent history | much morphology redundancy |
| EMA50 | slower raw-price regime | lag + tail false warnings |
| EMA20 envelope | local extension | support thins after conditioning |
| ATR-normalized coordinates | cross-era scale | coordinate, not signal |
| ADX | directionless trend strength | weak/unstable transition separation |
| DMI | directional raw-price movement | heavily redundant with EMA context |
| relative tick activity | participation proxy | broker/feed dependent, morphology overlap |
| persistent H1 x activity | transition-intensity interaction | still false-warns tails |

## 11. The next research problem

The central V13 problem is no longer finding another warning. There are already
many warnings.

The problem is:

> Given a warning-rich state, can we estimate whether it is a genuine Journey
> transition or only temporary weakness inside a persistent high-payoff trend?

That is a multivariable conditional-state question and is the first point in
V13 where a simple interpretable model is scientifically justified.

## 12. HA-8A research boundary

HA-8A should estimate lifecycle state without changing trades.

Preferred first target:

`flip_within_3`

Reason: next-H4 is too timing-sensitive and many HA-6 effects were stronger over
2-3 H4 bars; Journey-end labels farther into the future risk blending timing and
magnitude. `flip_within_3` is already available causally as a future label and
matches the transition-horizon evidence accumulated in HA-6.

First model sequence:

```text
base rate
-> regularized logistic regression
-> shallow tree / small RF only if needed
```

Evaluation should emphasize:

- chronological OOF log loss / Brier score;
- calibration curve / reliability by fold;
- ROC/PR only as secondary discrimination measures;
- year/side stability;
- Journey age and child-slot diagnostics;
- performance specifically in >=10-bar Journeys;
- false-positive probability mass on high-payoff continuation tails;
- comparison with H1-only and HASTOC-only baselines.

No action threshold, sizing or exit is part of HA-8A.

## 13. Outstanding non-research task

The exact-window actual-tick Baseline-0 MT5 receipt remains pending under the
frozen tester protocol. Observation/model work may continue, but no production
or economic promotion should bypass that execution authority requirement.
