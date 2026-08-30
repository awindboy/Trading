# V8-B1 Causal Alignment Invalidation

Date: `2026-08-31`
Status: `INVALIDATED_BY_HTF_LOOKAHEAD / DO NOT DEPLOY`
Base GitHub HEAD audited: `0529c204a655e9cc281e1e6f35e5e7883bf4b427`
Production authority: `NONE`
Direction authority: `NONE`
V8-A status: `FROZEN / UNAFFECTED`
GOLD# 2021: `UNTOUCHED`

## 1. Executive verdict

The previously reported V8-B1 conditional-direction result is invalid.

The apparent 15m/30m/60m direction AUCs in the approximate `0.80-0.90` range were materially contaminated by a higher-timeframe alignment bug. M15/H1 bars were resampled as full completed bars and then selected by their **start timestamp** rather than by their **availability/close timestamp**.

At an event occurring inside an M15 or H1 bar, this exposed the future remainder of that bar to the direction model.

Therefore:

- do not implement or deploy the frozen V8-B1 model;
- do not use `config/v8_b1_direction_models.json` for inference;
- do not use the stale high V8-B1 AUCs as research evidence;
- do not open GOLD# 2021 on the basis of V8-B1;
- keep V8-A movement probability frozen because its feature path is independent and causal.

## 2. Exact bug

The leaky feature builder used the following pattern conceptually:

```python
z = m1.resample(rule, label="left", closed="left").agg(...)
tt = z.index.values
pp = np.searchsorted(tt, decision_times, "left") - 1
```

`z.index` is the **bar start time**.

For a decision at `10:25`:

```text
H1 selected start = 10:00
H1 selected interval = 10:00-11:00
information actually knowable at 10:25 = only 10:00-10:24 prefix
information accidentally used = full 10:00-10:59 bar
```

The same issue exists for M15 decisions that occur inside an M15 bar.

The correct completed-bar rule is:

```text
bar_start + timeframe_duration <= decision_time
```

Equivalently, selection must be based on availability/close time, not bar start time.

If a current partial H1/M15 bar is intentionally used, it must be reconstructed separately from the causal M1 prefix strictly before the decision timestamp. A later completed OHLC bar may never stand in for the partial state.

## 3. Leakage prevalence in the stale V8-B1 event population

Across 66,235 event rows:

```text
M5  leaky rows:      0 / 66,235   = 0.00%
M15 leaky rows: 44,897 / 66,235   = 67.78%
H1  leaky rows: 59,743 / 66,235   = 90.20%
```

For affected H1 rows, the selected completed H1 bar contained a median of roughly 30 future minutes and as much as 55 future minutes beyond the decision time.

Representative examples are stored in:

`ledgers/v8/V8_B1_HTF_LEAK_EXAMPLES.csv`

## 4. Re-audit design

The same V8-B formulation was rerun without changing the core model family merely to rescue the result.

Two causal alignments were tested.

### A. Completed-only

M5/M15/H1 technical features may use only bars satisfying:

```text
bar_start + duration <= decision_time
```

### B. Causal partial-current HTF

The current M15/H1 bar may be represented, but only by rebuilding its state from M1 rows strictly earlier than the decision time. ATR/RSI/EMA/MACD and rolling statistics are updated causally from that prefix.

This tests the legitimate trader-view objection that a trader can see the currently forming H1/M15 candle without granting access to its future completion.

The model remained the same regularized logistic family with the same signed core concept. V8-A movement probabilities remained frozen.

## 5. Corrected conditional direction AUC

### Completed-only

| Horizon | 2024 | 2025 | 2026 YTD |
|---|---:|---:|---:|
| 15m | 0.666 | 0.553 | 0.534 |
| 30m | 0.579 | 0.537 | 0.521 |
| 60m | 0.530 | 0.514 | 0.511 |

### Causal partial-current HTF

| Horizon | 2024 | 2025 | 2026 YTD |
|---|---:|---:|---:|
| 15m | 0.627 | 0.556 | 0.537 |
| 30m | 0.574 | 0.533 | 0.523 |
| 60m | 0.527 | 0.514 | 0.512 |

The 2024 15m result is a development-period anomaly with only about 100 prior training movers and does not remain remotely comparable in 2025/2026. It is not a promoted sub-branch.

The previous high AUC result is therefore not recoverable by legitimately using a causal current partial HTF bar.

## 6. Outcome-blind non-overlap re-audit

Events were also reduced outcome-blind by accepting an event and then suppressing subsequent anchors for H minutes.

### Completed-only non-overlap AUC

| Horizon | 2024 | 2025 | 2026 YTD |
|---|---:|---:|---:|
| 15m | 0.651 | 0.556 | 0.531 |
| 30m | 0.588 | 0.520 | 0.518 |
| 60m | 0.512 | 0.512 | 0.514 |

### Causal partial-current HTF non-overlap AUC

| Horizon | 2024 | 2025 | 2026 YTD |
|---|---:|---:|---:|
| 15m | 0.594 | 0.557 | 0.530 |
| 30m | 0.583 | 0.511 | 0.521 |
| 60m | 0.525 | 0.516 | 0.517 |

The prior claim that V8-B1 remained strong after overlap correction is invalid because that robustness audit inherited the same leaky HTF features.

## 7. Full-population joint-probability re-audit

The central future-selection objection was retested on **all events**, not only events that later moved.

Frozen V8-A supplies:

```text
p_H = P(any +/-10 move within H)
```

Corrected V8-B supplies candidate conditional side:

```text
q_H = P(UP | move within H)
```

and:

```text
P(NO MOVE) = 1-p_H
P(DOWN)    = p_H * (1-q_H)
P(UP)      = p_H * q_H
```

The corrected V8-B does **not** consistently improve log loss over the same frozen V8-A with a simple prior or 50/50 side allocation.

For example, completed-only `prior logloss - V8-B logloss` is:

```text
15m: 2024 +0.00056 / 2025 -0.00094 / 2026 -0.00107
30m: 2024 +0.00038 / 2025 -0.00173 / 2026 -0.00186
60m: 2024 -0.00040 / 2025 -0.00254 / 2026 -0.00187
```

Positive means V8-B helped; negative means it hurt. Later years are mostly negative.

Therefore the stale claim that conditional direction adds genuine full-population information is withdrawn.

## 8. Event-family result after correction

No M5 event family retains the previously reported strong and stable side AUC.

Typical corrected 30m causal-partial values are approximately:

```text
M5 MA20:       2024 0.519 / 2025 0.504 / 2026 0.529
M5 upper BB:   2024 0.493 / 2025 0.507 / 2026 0.514
M5 lower BB:   2024 0.599 / 2025 0.499 / 2026 0.489
H1 Double-B:   2024 0.509 / 2025 0.542 / 2026 0.539
```

No family is promoted.

## 9. Why V8-A remains valid

This invalidation is specific to the V8-B higher-timeframe direction feature builder.

The frozen V8-A portable model:

- derives its 53-feature state from backward-looking M1 windows;
- selects the last M1 strictly before the completed-M5 decision;
- does not substitute future-completed M15/H1 OHLC for current state;
- already has independent Python-to-MQL formula parity checks.

Therefore V8-B1 invalidation does **not** invalidate the V8-A movement probability branch.

V8-A remains frozen.

## 10. Research lesson

The failure is methodologically valuable.

The high stale direction AUC looked plausible because the leaked H1 full bar encoded exactly the future short-horizon directional movement the target asked about. Several later robustness tests then reused the same contaminated feature table, so they were not independent leakage tests.

The correct regression question is not only:

> Is this feature timestamp before the decision?

It is:

> Was every value inside this feature actually available by the decision timestamp?

For resampled bars, start-time alignment is insufficient.

## 11. Disposition

```text
V8-A movement probability       FROZEN / RETAINED
V8-B1 leaky positive result     INVALIDATED
V8-B1 coefficient manifest      DO NOT DEPLOY
V8-B1 MT5 direction extension   CANCELLED
GOLD# 2021                      UNTOUCHED
```

Next branch:

`V8-B2 SOURCE-OF-MOVE / CROSS-MARKET CAUSAL DIRECTION`

Read `V8_B2_SOURCE_OF_MOVE_RESEARCH_CONTRACT.md` before opening any new direction outcome.
