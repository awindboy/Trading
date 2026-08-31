# V8-B Internal Direction Research — Post-B1 Causal Rebuild

Date: `2026-08-31`
Status: `CURRENT INTERNAL DIRECTION RESEARCH NARRATIVE`
V8-A: `FROZEN`
Direction authority: `NONE`
External inputs: `DE-SCOPED`
GOLD# 2021: `LOCKED`

## 1. Research objective

The user observed the V8-A movement-probability indicator in MT5 and judged that the probability state looked potentially useful for deciding when to perform deeper chart analysis.

The active question became:

> Can frozen V8-A movement information be transformed or combined with causal GOLD-internal context to predict the sign of the next meaningful move?

The research deliberately kept V8-A unchanged.

## 2. Starting correction: V8-B1 invalidation

The first apparently strong same-horizon direction model was invalidated before MT5 deployment.

Its M15/H1 features selected `label=left` resampled bars by bar-start timestamp rather than availability time.

For intrabar decisions, the final full M15/H1 bar therefore included future observations.

Permanent rule:

```text
completed HTF available iff
bar_start + timeframe_duration <= decision_time
```

After correction, broad direction performance collapsed toward chance.

This is the first major V8-B false-positive case.

## 3. External source-of-move proposal was de-scoped

A cross-market direction branch was considered after the B1 failure.

The user rejected it as the active direction path and requested continued research using:

- GOLD internal information;
- frozen V8-A;
- better preprocessing / modeling.

The project therefore returned to internal-only research.

## 4. V8-A trajectory as a direction representation

V8-A was not treated merely as three scalar inputs.

For event decisions, the research constructed probability-state variables including:

```text
P15 / P30 / P60
5m / 15m / 30m / 60m lags
slopes
accelerations
rolling mean / dispersion
P30-P15
P60-P30
relative horizon shape
hazard-like shape
```

The hypothesis was that `how movement probability is forming` could contain more information than its absolute level.

It did not provide stable broad OOS direction skill.

## 5. Price sequence + V8-A probability sequence

A direct sequence study compared:

```text
price sequence only
V8-A probability sequence only
joint price + V8-A sequence
```

A representative 2024 30m discovery result was approximately:

```text
price-only  ~0.69 AUC
V8-A-only   ~0.66
joint       ~0.68
```

The joint representation did not beat price-only.

When carried through chronological later years, the 2024 direction skill weakened materially and approached the mid-0.5 range.

A small temporal CNN was also tested. It did not demonstrate stable incremental V8-A value.

Conclusion:

> A nonlinear temporal model cannot be assumed to discover a missing directional relation merely because V8-A is a strong movement model.

## 6. Event-centered geometry

Because return sequences can discard the spatial structure a trader sees, the price branch was re-expressed around the current decision close:

```text
C0 = 0
OHLC / MA / BB geometry relative to C0
```

and aligned with the V8-A probability trajectory.

This representation also failed to produce stable later-year direction information.

## 7. Regime canonicalization

A material distribution shift exists:

- GOLD volatility rose strongly into 2025/2026;
- raw V8-A probability distributions also shifted upward.

The direction branch therefore tested causal regime normalization:

- price scaled by local causal volatility;
- V8-A transformed by logit;
- trailing causal z-scores;
- probability changes rather than absolute probability.

Some 2024 60m variants modestly improved AUC, but the frozen relationship failed in 2025.

Conclusion:

> scale shift alone does not explain the missing direction edge.

## 8. Directional-energy decomposition

V8-A is strong partly because it measures directionless market energy.

The research therefore decomposed internal M1 activity into signed components:

- up/down semivariance;
- bullish/bearish candle-body energy;
- upper/lower wick pressure;
- signed path efficiency;
- tick-activity imbalance / price-impact proxies.

The intended factorization was:

```text
V8-A = how much movement energy exists
signed activity = which side recently carries that energy
```

Again, 2024 could show moderate AUC, but 2025/2026 validation weakened substantially.

## 9. Score fusion and stacking

To test whether raw joint feature spaces were simply overfitting, V8-A state and signed-activity state were each compressed to low-dimensional direction scores.

Tests included:

- equal-weight score fusion;
- two-score logistic stacking.

A small 2025 ranking improvement in one 30m stack was within paired weekly bootstrap uncertainty and did not improve proper all-event log loss reliably.

Conclusion:

> high-dimensional feature interaction was not the only reason the joint models failed.

## 10. Training-population controls

Another possible explanation was that event-only mover samples were too small.

Direction learning was expanded to all completed M5 mover states, while factual events remained the evaluation anchors.

This greatly increased training examples but did not solve later-year direction stability.

Recent-year / rolling retraining controls also failed to restore a robust broad edge.

## 11. Sequential-response false positive

An event-after-response formulation initially looked strong.

For example, after waiting several minutes, the sign of the first response often matched which original event-C0 +/-10 barrier was eventually hit.

This was rejected.

Reason:

If the price already moves +5 after the event:

```text
original +10 barrier is now only +5 away
original -10 barrier is now -15 away
```

The target is no longer symmetric.

Correct delayed-decision rule:

```text
new C0 = current price at delayed decision
new barriers = new C0 +/-10.0
```

After recentering, the apparent 70%+ continuation effect largely disappeared.

This is the second major V8-B false-positive case.

## 12. Selective confidence tails

Because a broad classifier may be weak while rare extreme states contain information, selective direction-confidence tails were tested.

A first artifact appeared to produce very high later-year conditional direction accuracy and chosen-side hit rates.

Further review found two issues:

1. absolute direction-score cutoffs were not comparable across annually refit models;
2. the old score artifact was not preserved with sufficient model/equation provenance for independent reproduction.

Causal rolling-percentile selection reduced the apparent effect materially.

## 13. Exact independent B28 rebuild

The selective-direction idea was then rebuilt independently from scratch using:

- the current factual event ledger;
- explicit causal M1 signed-activity equations;
- full chronological training and purge rules;
- frozen V8-A probabilities;
- causal rolling selection;
- outcome-blind non-overlap;
- week/month cluster bootstrap.

Representative exact direction AUC:

```text
30m: 2025 ~0.533 / 2026 ~0.520
60m: 2025 ~0.516 / 2026 ~0.506
```

The earlier 70-90% direction-tail evidence did not reproduce.

It is rejected as direction authority.

This is the third important false-positive/reproducibility correction.

## 14. Why chosen-side hit can still look high

In high V8-A states, `move_rate` can be very high.

A direction model with approximately random sign can therefore appear to have a high chosen-side hit rate.

Example logic:

```text
move_rate = 90%
random side accuracy = 50%
expected chosen-side hit = 45%
```

Therefore all future direction studies must report:

```text
move_rate
conditional direction accuracy
chosen-side hit
directional excess
```

with:

```text
directional excess =
chosen-side hit - 0.5 * move_rate
```

The exact rebuild showed that V8-A can strongly improve movement selection while conditional direction remains near 50%.

## 15. Event-side semantics under V8-A

Nonparametric checks asked whether V8-A changes the meaning of existing events:

- upper BB continuation/reversal;
- lower BB continuation/reversal;
- MA20 contact side;
- Double-B side.

No stable rule emerged in which higher V8-A probability consistently made these simple event directions substantially more predictable across later years.

This blocks a simple rule such as:

```text
high V8-A + upper BB => continuation
```

## 16. Exact continuous V8-A research series

For the remaining internal research, the frozen MQL V8-A equations were independently reproduced on all completed M5 states across 2024-2026.

Approximately `187,708` M5 decision points were generated.

This provides a causal continuous series for:

```text
current P15/P30/P60
past probability state
slopes / acceleration
event-time probability trajectory
sequential WAIT state
```

The reconstruction matched the embedded V8-A equations at effectively floating-point tolerance (~1e-9 percentage-point scale in the audit).

## 17. Current evidence hierarchy

Strongest retained evidence:

```text
V8-A movement intensity = strong
```

Not retained:

```text
broad autonomous direction = not demonstrated
V8-A raw probability as direction feature = not demonstrated
V8-A trajectory + price sequence = not stable
directional-energy + V8-A = not stable
selective 70-90% direction tail = not reproducible
simple event-side conditioned by high V8-A = not stable
```

## 18. Remaining internal-only research

The remaining high-value questions are narrower.

### A. Exact V8-A trajectory × event interaction

Using the exact continuous V8-A series, complete the causal matrix for states such as:

```text
high and rising
high and falling
low but rapidly rising
extreme and flattening
```

Cross only with factual, outcome-blind event information.

Do not tune a threshold after seeing direction outcomes.

### B. Sequential WAIT -> recenter -> update

This is now more plausible than forcing a one-shot direction prediction at event time.

Protocol:

```text
event
-> V8-A identifies a high-attention state
-> direction uncertain => WAIT
-> observe only new causal GOLD evidence
-> at fixed delay, reset C0 to current price
-> define a new symmetric +/-10.0 race
-> update direction / WAIT again
```

Every delay must use a new C0.

### C. Path quality, not only side

If a direction candidate appears, inspect:

- MAE before chosen-side hit;
- MFE;
- opposite-side excursion;
- first-hit ordering;
- time to hit;
- cost/execution implications.

### D. Prospective human labels if machine direction stays weak

If exact internal retrospective direction remains near chance, stop endless feature mining.

The V8-A MT5 indicator can instead support prospective logging of:

```text
event
V8-A state
human LONG/SHORT/WAIT/SKIP
human reasoning tags if desired
actual path/outcome
```

The next learnable problem may be which human decisions are worth trusting, rather than directly predicting market sign from the same endogenous history.

## 19. Promotion gate

No V8-B direction MT5 extension until a candidate:

1. is strictly causal;
2. has complete model/feature provenance;
3. is independently reproducible;
4. survives 2024 discovery -> 2025 validation -> 2026 stress;
5. survives outcome-blind non-overlap;
6. improves proper full-population metrics;
7. has positive directional excess, not merely high movement rate;
8. survives month/hour/event/direction concentration checks.

## 20. Reserve

GOLD# 2021 remains untouched.

The current direction evidence is not strong enough to justify consuming it.
