# V8-002 — 10P First-Hit Numerical Pilot Results

Date: `2026-08-31`
Status: `DEVELOPMENT DIAGNOSTIC / NO STRATEGY AUTHORITY`

## 1. Label census

Initial V8 anchor population:

```text
total anchors                 59,438
UP_FIRST                      30,320
DOWN_FIRST                    29,089
AMBIGUOUS_SAME_M1                 29
UNRESOLVED                         0
UP rate among resolved        51.04%
```

First-hit elapsed-time quantiles:

```text
10%      23 min
25%      76 min
50%     257 min
75%     665 min
90%   1,413 min
95%   2,235 min
99%   5,235 min
```

The label therefore avoids an arbitrary terminal-close horizon while still resolving almost all events on an
intraday / short multi-day path.

## 2. 2024 representation selection

Same compact multi-TF temporal CNN; one seed.

| Input | ROC AUC | Balanced accuracy | Accuracy |
| --- | ---: | ---: | ---: |
| OHLC only | 0.504 | 0.499 | 0.489 |
| OHLC + indicator history | 0.519 | 0.521 | 0.509 |
| OHLC + indicator history + d1 | 0.519 | 0.531 | 0.525 |

Indicator history improves the 2024 information diagnostic relative to OHLC-only.

The delta variant is only marginally better than raw indicator history in AUC, but improves balanced
classification accuracy in this pilot.

## 3. Frozen IND + d1 temporal diagnostics

After the 2024 selection comparison, the indicator+d1 contract was kept fixed.

| Evaluation | ROC AUC | Balanced accuracy | Accuracy | Log loss |
| --- | ---: | ---: | ---: | ---: |
| 2024 | 0.519 | 0.531 | 0.525 | 0.726 |
| 2025 | 0.509 | 0.511 | 0.503 | 0.782 |
| 2026 YTD | 0.509 | 0.502 | 0.492 | 0.737 |

Interpretation:

- the small 2024 information lift does not strengthen in 2025/2026;
- ranking information remains only slightly above chance;
- probability calibration is poor: log loss is worse than the constant-prior baseline in later periods;
- this pooled classifier is not a robust direction model.

## 4. Label base-rate movement

UP_FIRST rate:

```text
2022  49.49%
2023  49.33%
2024  55.40%
2025  52.32%
2026  47.38%
```

This is a material regime shift in the target distribution itself.

## 5. Event-family ablation

No threshold/filter was selected. Every preregistered anchor family was tested separately with the same
10p target and indicator+d1 input.

### M5 SMA20 contact

```text
2024 AUC 0.506
2025 AUC 0.512
2026 AUC 0.508
```

Small but weakly stable ranking information; not enough for a trading claim.

### M5 upper BB20 contact

```text
2024 AUC 0.518
2025 AUC 0.497
2026 AUC 0.490
```

Fails temporal stability.

### M5 lower BB20 contact

```text
2024 AUC 0.491
2025 AUC 0.487
2026 AUC 0.491
```

No useful direction information.

### H1 Double-B

```text
2024 N409  AUC 0.546
2025 N400  AUC 0.561
2026 N248  AUC 0.458
```

The attractive 2024/2025 values reverse in 2026 and the population is small. No promotion.

## 6. H4/D1 broader-context ablation

Outcome-blind context extension:

```text
D1 40 completed bars
H4 60 completed bars
+ existing H1/M15/M5/M1
```

2024 same-eligible-population result:

```text
4TF AUC 0.498
6TF AUC 0.508
```

But balanced accuracy remains ~0.50 and log loss worsens materially.

Conclusion: merely adding longer timeframes is not yet a demonstrated solution.

## 7. Current decision

Retain:

- event-close-centered coordinate system;
- fixed +/-10 GOLD-price-unit first-hit target;
- exact numerical historical sequences;
- historical indicator series;
- explicit indicator d1 channels;
- visual input de-scoped from the base path.

Reject as current strategy candidate:

- pooled global 10p direction classifier;
- simple per-event-family rescue;
- adding H4/D1 alone as a rescue.

## 8. Next research question

The remaining representation gap is objective structural context, not another indicator threshold.

Next V8 experiment should add factual, causal structure without semantic labels, e.g.:

- prior-day OHLC levels;
- current-day open/high-so-far/low-so-far;
- sequences of causally confirmed swing highs/lows with age and event-relative distance;
- prior Double-B/event history;
- later, exact session/KTR levels only after broker-server mapping is frozen.

The target and evaluation protocol should remain unchanged during this next representation ablation.
