# INVALIDATION NOTICE — 2026-08-31

**Status: `INVALIDATED_BY_HTF_LOOKAHEAD / DO NOT USE AS POSITIVE EVIDENCE`**

The original V8-B1 result below is preserved for research history, but its high conditional-direction AUC is not valid. The M15/H1 feature builder selected full resampled bars by bar-start time, exposing future portions of the current HTF bar.

Authoritative correction:

`V8_B1_CAUSAL_ALIGNMENT_INVALIDATION.md`

Corrected strictly causal 30m AUC is only about `0.579 / 0.537 / 0.521` (completed-only) across 2024/2025/2026, and the full-population joint proper score does not improve reliably in later years.

Do not deploy `config/v8_b1_direction_models.json`.

---

# V8-B Direction Probability — Conditional Same-Horizon Research Results

Date: `2026-08-31`
Status at time of original run: `SUPERSEDED / LEAKY RESULT — SEE INVALIDATION NOTICE ABOVE`
Market: `GOLD#`
V8-A movement model: `FROZEN`
Untouched reserve: `GOLD# 2021` — `LOCKED`

## 1. Why V8-B was reopened

The earlier V8 direction path asked an unconditional question:

```text
from event close C0,
which barrier is reached first eventually:
C0 + 10.0 or C0 - 10.0 ?
```

Across many preprocessing/model variants this remained weak and unstable.

V8-A then demonstrated a materially different fact: near-term movement probability over fixed 15m/30m/60m horizons is strongly predictable.

This motivated a new formulation rather than another feature/architecture rescue.

## 2. Frozen V8-A contract

V8-A is not modified by V8-B.

For each horizon `H in {15m,30m,60m}`:

```text
p_H(X) = P(either +10.0 or -10.0 is reached within H | causal state X)
```

The existing 53-feature continuous-M5 walk-forward logistic movement model remains frozen.

Historical display/training policy remains:

```text
2024 <- model trained through 2023
2025 <- model trained through 2024
2026 <- model trained through 2025
```

For 2022H2-2023 V8-B training rows, cross-fitted movement scores were generated using the same frozen V8-A feature/model family with a six-month warm-up and quarterly expanding refits. This was done only to prevent in-sample movement-label leakage into V8-B feature tests.

## 3. Corrected V8-B formulation

V8-B does not try to predict the old eventual first-hit side.

Instead, at the same fixed horizon as V8-A, define:

```text
M_H = a +/-10.0 barrier is reached within H
S_H = UP or DOWN first, conditional on M_H
```

V8-B estimates:

```text
q_H(X) = P(UP first | M_H = 1, causal state X)
```

The modular joint probabilities are then:

```text
P(UP within H)   = p_H * q_H
P(DOWN within H) = p_H * (1 - q_H)
P(NO 10p move)   = 1 - p_H
```

This is a two-part / hurdle-style decomposition. The movement marginal stays exactly under V8-A authority.

Same-M1 cases where both +10 and -10 are touched on the first hit minute are direction-ambiguous and excluded from the conditional side target.

## 4. First hypothesis was falsified: V8-A probability is not a useful direction feature

The initial idea was to feed `P15/P30/P60` directly into a direction model or use them as continuous gates.

That did **not** improve conditional direction prediction.

Representative 30m AUC:

| Model | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| signed causal core | **0.888** | **0.860** | **0.823** |
| core + V8-A probabilities | 0.870 | 0.857 | 0.824 |
| continuous gated interactions | 0.878 | 0.807 | 0.812 |
| movement probabilities + event only | 0.564 | 0.545 | 0.538 |

Representative 60m AUC:

| Model | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| signed causal core | **0.859** | **0.838** | **0.795** |
| core + V8-A probabilities | 0.844 | 0.836 | 0.797 |
| continuous gated interactions | 0.838 | 0.805 | 0.787 |
| movement probabilities + event only | 0.536 | 0.510 | 0.534 |

Conclusion:

> V8-A movement probability should not be promoted as an additional raw direction feature. Its useful role is to supply the movement marginal in the final joint probability decomposition.

## 5. What did predict conditional direction

The strongest simple input family was signed causal market progression rather than movement magnitude.

The frozen development core uses variables such as:

- signed 30/60/120/240/480-minute net progression;
- close location inside recent causal ranges;
- signed path-efficiency and body-bias measures;
- M5/M15/H1 normalized returns over several lags;
- M15/H1 Bollinger location;
- M15/H1 RSI-centered state;
- normalized MACD-histogram state;
- factual event flags.

No hard TREND/RANGE/BREAKOUT label is supplied.

The strongest individual variable was recent H1 progression. For 30m movers, `H1 3-bar return` alone had AUC:

```text
2024  0.798
2025  0.745
2026  0.681
```

The full core improved this materially to approximately:

```text
2024  0.895
2025  0.869
2026  0.823
```

Therefore V8-B is not merely a repackaged H1-momentum rule, although broad H1/M15 directional context is the dominant mechanism.

## 6. Conditional direction results using all causally eligible prior movers

Regularized logistic side model, no V8-A probabilities as direct inputs:

| Horizon | 2024 AUC | 2025 AUC | 2026 AUC |
|---|---:|---:|---:|
| 15m | 0.846 | 0.866 | 0.838 |
| 30m | **0.895** | **0.869** | **0.823** |
| 60m | 0.863 | 0.842 | 0.795 |

These AUCs are conditional on an actual within-horizon +/-10 move. They are not by themselves executable trade hit rates. Joint all-event evaluation is required and is reported below.

## 7. Non-overlap robustness

To avoid counting many event anchors from one underlying move as independent evidence, evaluation was repeated on an outcome-blind population that accepts an event and then accepts no new event for the next `H` minutes.

Conditional side AUC:

| Horizon | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| 15m | 0.831 | 0.858 | 0.838 |
| 30m | **0.894** | **0.869** | **0.822** |
| 60m | 0.829 | 0.846 | 0.801 |

Week-block bootstrap 95% AUC intervals:

| Horizon | 2024 | 2025 | 2026 |
|---|---|---|---|
| 15m | 0.770–0.881 | 0.821–0.892 | 0.811–0.874 |
| 30m | **0.856–0.927** | **0.850–0.889** | **0.793–0.851** |
| 60m | 0.786–0.868 | 0.822–0.870 | 0.775–0.831 |

The result therefore survives removal of overlapping event windows.

## 8. Event-family falsification

This is not a universal event-direction model.

### M5 event families

The side model remained strong for:

- M5 SMA20 contact-start;
- M5 upper-BB contact-start;
- M5 lower-BB contact-start.

For 30m, family AUCs were approximately:

```text
M5 MA20:      0.922 / 0.863 / 0.842
M5 upper-BB:  0.898 / 0.894 / 0.836
M5 lower-BB:  0.933 / 0.887 / 0.829
```

### H1 Double-B

Double-B failed decisively as a V8-B directional family:

```text
30m AUC: 0.475 / 0.481 / 0.484
60m AUC: 0.474 / 0.496 / 0.490
```

Decision:

> H1 Double-B may retain V8-A movement probability, but current evidence does not authorize a V8-B directional probability at Double-B anchors.

This is consistent with earlier V7/V8 evidence that Double-B is an attention event, not a stable direction rule.

## 9. Leakage / shortcut audits

Several regressions were performed because the initial conditional AUC was unexpectedly high.

### 9.1 Same-M1 ambiguity

Cases where both +/-10 barriers were reached in the first hit M1 were excluded from side training/evaluation.

### 9.2 Completed-bar boundary

All signed features use information available before the forecast interval. M1 features stop at the last completed M1 before the event decision. M5/M15/H1 features use completed bars only.

### 9.3 Feature ablation

30m AUC:

| Feature family | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| full signed core | 0.888 | 0.860 | 0.823 |
| remove shortest M1/M5-sensitive group | 0.885 | 0.847 | 0.807 |
| M15/H1 only | 0.824 | 0.793 | 0.760 |
| M5 only | 0.578 | 0.532 | 0.518 |

The result therefore does not depend on one final event candle or one M5 shortcut. Broader M15/H1 progression carries a large part of the signal.

### 9.4 Permutation negative control

For the 30m task, permuting training side labels returned evaluation AUC around chance on average rather than reproducing the real model result.

This argues against a mechanical feature/target indexing bug as the explanation for the observed AUC.

## 10. Important regression: highest movement state does not improve side predictability

The original gating intuition was that very high V8-A movement probability might make direction easier.

The opposite tendency appeared.

For 30m actual movers, side-model AUC by within-year V8-A movement-probability quintile:

### 2025

```text
Q1  0.890
Q2  0.874
Q3  0.879
Q4  0.859
Q5  0.803
```

### 2026

```text
Q1  0.876
Q2  0.859
Q3  0.846
Q4  0.809
Q5  0.725
```

Interpretation:

> Extreme movement intensity makes a 10p move more likely, but the side of that move becomes less structurally predictable from endogenous chart context.

This explains why direct V8-A gating/interaction terms did not improve q_H.

## 11. Joint all-event validation

Conditional mover AUC can be misleading if the model only looks good after selecting future movers.

Therefore q_H was applied to **all** evaluation events and combined with the frozen V8-A probability.

The resulting three classes are:

```text
NO 10p move within H
DOWN first within H
UP first within H
```

Compared with using the same frozen V8-A probability but assigning direction only by historical prior / 50:50, V8-B reduced multiclass log loss consistently.

### 30m joint log loss

| Year | V8-A + V8-B | V8-A + prior side | V8-A + 50/50 |
|---|---:|---:|---:|
| 2024 | **0.126** | 0.135 | 0.134 |
| 2025 | **0.406** | 0.439 | 0.440 |
| 2026 | **0.789** | 0.875 | 0.874 |

### 60m joint log loss

| Year | V8-A + V8-B | V8-A + prior side | V8-A + 50/50 |
|---|---:|---:|---:|
| 2024 | **0.272** | 0.292 | 0.291 |
| 2025 | **0.611** | 0.668 | 0.669 |
| 2026 | **0.878** | 0.979 | 0.979 |

Thus the high conditional AUC is not merely a future-mover-selection illusion; it contributes predictive information when mapped back to the full event population.

## 12. Joint directional hit-rate diagnostics

These are **diagnostics, not trading thresholds**.

For 30m, among events whose predicted probability of the chosen side was at least 0.50:

```text
2024: N=10,   actual chosen-side hit within 30m = 20.0%  (too small / unstable)
2025: N=389,  actual chosen-side hit within 30m = 70.4%
2026: N=2364, actual chosen-side hit within 30m = 65.5%
```

For 60m at the same predicted joint threshold:

```text
2024: N=78,   57.7%
2025: N=1054, 73.7%
2026: N=4406, 67.9%
```

The 2024 30m tail demonstrates why no hard trade threshold is authorized: absolute calibration and opportunity frequency change dramatically with the movement regime.

## 13. Direct three-class comparison

A direct multinomial model that is allowed to re-learn the entire movement+direction distribution achieved slightly lower multiclass log loss than the frozen decomposition.

Example 30m:

```text
2024 direct 0.111 vs decomposition 0.126
2025 direct 0.387 vs decomposition 0.406
2026 direct 0.770 vs decomposition 0.789
```

This is recorded rather than hidden.

It is **not adopted** for V8-B because the user explicitly froze V8-A. Re-learning the movement marginal inside V8-B would blur attribution and violate the modular freeze contract.

## 14. Current V8-B1 development candidate

V8-B1 is frozen at the research-contract level as:

```text
V8-A:
  p15 / p30 / p60 movement probabilities
  unchanged

V8-B:
  regularized logistic conditional-side model
  signed causal multi-horizon context
  no direct V8-A probability features

Joint:
  up_H   = p_H * q_H
  down_H = p_H * (1 - q_H)
  no_H   = 1 - p_H
```

Event support:

```text
M5 SMA20 contact-start       supported for V8-B development
M5 upper-BB contact-start    supported for V8-B development
M5 lower-BB contact-start    supported for V8-B development
H1 Double-B                  movement-only; direction NOT supported
```

All three horizons remain development outputs, but 30m/60m have the strongest sample support. The 15m early-period mover population is materially smaller and should be treated more cautiously despite positive later results.

## 15. What this does not prove

V8-B does not yet prove:

- profitable executable trades;
- a final LONG/SHORT threshold;
- stop/target expectancy after spread and slippage;
- live broker-feed parity;
- independence from all possible execution effects;
- final performance on the untouched GOLD# 2021 reserve.

No autonomous trade authority is granted.

## 16. Next required step

Before opening GOLD# 2021:

1. freeze exact V8-B feature equations and model coefficients for the current development candidate;
2. implement V8-B as a shadow-only extension beside frozen V8-A;
3. show `P(move)`, conditional `P(UP|move)` and joint UP/DOWN probabilities separately so semantics cannot be confused;
4. prove Python/MQL formula parity;
5. keep Double-B direction blank/unsupported;
6. prospectively log every supported M5 event;
7. do not set a trading threshold from retrospective tails.

Historical note from the invalidated run: this proposed next step is cancelled. GOLD# 2021 remains locked; see the invalidation notice above.

## 17. Frozen research artifacts

Model coefficient manifest:

`config/v8_b1_direction_models.json`

Evidence ledgers:

- `ledgers/v8/V8_B1_JOINT_METRICS.csv`
- `ledgers/v8/V8_B1_NONOVERLAP_BOOTSTRAP.csv`
- `ledgers/v8/V8_B1_EVENT_FAMILY_ROBUSTNESS.csv`
- `ledgers/v8/V8_B1_MOVEMENT_QUINTILE_SIDE_AUC.csv`

The model manifest SHA256 at creation was:

`0bde9d6940a0f21e1b7bbe8692c68e0eb0c1b8f83d18da40dd75ce7e1068f6d7`
