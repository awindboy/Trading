# V4-001 — AI-Native Representation-to-Policy Research Contract

Status: `PRE-REGISTERED DEVELOPMENT CONTRACT`
Date: `2026-08-27`
Model family: `V4_001_CausalPatchPolicy`
Production authority: `NONE`

## 1. Research purpose

V4-001 tests a narrower and more falsifiable claim than "RL can trade".

Primary claim under test:

> A learned causal representation of multi-resolution and cross-market broker data contains stable predictive
> information about near-future return distributions that is not captured by simple same-input baselines.

Only if this claim survives internal OOS diagnostics is a simple economic controller tested.
Only if the controller survives a separately frozen external-market validation is sequential RL considered.

## 2. Why the first model is not RL

At the intended account scale, actions are assumed not to alter the historical market path.
For a given time interval, the price path therefore permits evaluating the counterfactual P/L of long, flat and
short exposures from the same data.

Using PPO/SAC immediately would add:
- behavior-policy dependence;
- credit assignment;
- value extrapolation;
- policy instability;
- more hyperparameters;

before proving that the observation contains predictive information.

V4-001 instead uses a learned predictive state plus a deterministic one-step cost-aware controller as the
minimum AI-native control.

## 3. Data roles

### Open development lab

```text
GOLD#    2023-2025
BTCUSD#  2023-2025
XAUEUR#  2023-2025
USDJPY#  2023-2025
```

All architecture and hyperparameter work in V4-001A/B occurs here.

### Unopened cross-market validation vault

```text
XAUJPY#
XAUCNH#
GAUCNH#
GAUUSD#
2023-2025
```

This set was selected by the prior V2 outcome-blind market screen, not by V4 performance.
Do not open it before a candidate is frozen.

### Final temporal confirmation

```text
GOLD# 2021
```

Untouched.

### Consumed data

```text
GOLD# 2022
```

Consumed by V3 Candidate-B validation. It is not a pristine V4 validation set.

## 4. Decision epoch and information boundary

Base decision interval:

```text
15 minutes
```

At decision time `t`:
- target execution price is the target market M1 open at `t` in Level-A research;
- observation may include only bars whose close/availability time is `<= t`;
- the M1 bar starting at `t` is **not** an input to the decision at `t`;
- future labels begin at `t`.

Bar streams:

```text
M1   history 256 completed bars
M5   history 192 completed bars
M30  history 96 completed bars
H4   history 42 completed bars
```

These lengths are architecture constants for V4-001, not P/L-selected thresholds.
They provide roughly 4h / 16h / 48h / 7d context while keeping the first model small enough for an 8GB-class GPU.

## 5. Base feature family

Per completed bar:

```text
normalized log return
normalized candle body
normalized high-low range
normalized upper wick
normalized lower wick
close location in bar
log tick volume z-score (causal EWM)
spread / price
spread / causal volatility
log gap since previous observed bar
time-of-day sin/cos
day-of-week sin/cos
```

Normalization is causal. No global fit over future data is allowed.

No V3 strategy-state label is included in the base model.

## 6. Model targets

Primary horizons:

```text
15m
60m
240m
```

For each horizon, predict:
- normalized future log-return mean;
- normalized future return scale;
- direction probability;
- normalized absolute return.

The multi-task targets force the representation to learn both direction and state-dependent movement scale.

## 7. Internal evaluation design

Required diagnostics include both:

### Temporal

```text
train 2023 -> evaluate 2024
train 2023-2024 -> evaluate 2025
```

2024/2025 remain development diagnostics, not pristine final validation.

### Leave-one-market-out

For each of:

```text
GOLD# / BTCUSD# / XAUEUR# / USDJPY#
```

train on the other development markets and evaluate the held-out target market using shared symbol-agnostic
encoders. No learned symbol ID is allowed in the base architecture.

## 8. Required controls

The learned model is compared against:
- chance / constant probability;
- same-input linear/logistic baseline;
- simple trailing momentum and mean-reversion controls for economic tests;
- target-only version of the same neural encoder;
- cross-market-context version.

A neural model does not receive credit merely for beating a V3 technical rule.

## 9. Stage-A progression gate

All of the following are required before V4-001B:

1. pooled held-out 15m direction AUC bootstrap interval excludes 0.5 on the positive side;
2. primary 15m AUC is >0.5 in at least 3 of 4 leave-one-market-out targets;
3. the neural model beats the same-input linear baseline in at least 3 of 4 held-out targets;
4. predicted probabilities are not grossly uncalibrated;
5. the gain is not explained by one market/year only.

This is an information-skill gate, not a final trading-strategy promotion gate.

If it fails, do not tune on the external validation vault and do not start RL.

## 10. V4-001B economic controller

Only after Stage-A pass.

State:

```text
learned latent state z_t
predicted 15m mean return
current exposure p_t in {-1,0,+1}
current recorded spread
```

Action:

```text
a_t in {-1,0,+1}
```

Expected one-step utility control:

```text
Q(a_t) = a_t * predicted_return_15m
         - half_spread_return_t * abs(a_t - p_t)
```

Choose `argmax_a Q(a)`.

This creates a natural no-trade state when the expected edge is not large enough to pay the current exposure
transition cost. No confidence threshold is tuned in the first controller.

Realized Level-A interval reward uses the same exposure and recorded spread cost accounting.

## 11. V4-001B reporting

Report:
- number of exposure changes;
- fraction of time long/flat/short;
- turnover;
- gross and spread-adjusted return;
- episode win rate;
- average positive/negative episode;
- expectancy;
- maximum drawdown;
- maximum negative streak;
- year / target-market contribution;
- sensitivity to removing cross-market context.

The project final >=50% WR and >1R winner objective remains binding before strategy promotion, but failure of a
minimal V4-001 controller is diagnostic rather than permission to manipulate the metric with arbitrary exits.

## 12. RL authorization rule

V4-002 sequential RL may be opened only if at least one of these is true after V4-001:

1. representation skill is robust and the simple controller is profitable, but position lifecycle/risk control
   is clearly the remaining bottleneck; or
2. full-information multi-step dynamic-programming diagnostics show material value beyond the one-step controller.

If representation skill is absent, RL is not authorized as a rescue.

## 13. No-production boundary

No result in V4-001 changes an EA Entry, SL, TP, sizing rule or live inference path.
Exact tick, full costs, MT5 parity and deployment design remain later gates.
