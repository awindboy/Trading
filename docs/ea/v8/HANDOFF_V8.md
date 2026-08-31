# V8 Development Handoff

Last updated: `2026-08-31`
GitHub base audited: `7cd9761f00e42e62aabcf8427c1a25fb8c71d235`
Current phase: `V8-B INTERNAL-ONLY DIRECTION / EXACT REBUILD + SEQUENTIAL POLICY`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## Current branch status

### V8-A

`FROZEN / RETAINED`

V8-A remains the 15m/30m/60m +/-10.0 movement-probability model and MT5 shadow indicator.

The B1 lookahead error did not affect V8-A.

A later exact Python reconstruction generated approximately `187,708` completed-M5 V8-A states over 2024-2026 with probability parity to the embedded MQL equations at roughly `1e-9` percentage-point scale.

### V8-B1

`INVALIDATED_BY_HTF_LOOKAHEAD / CLOSED`

Do not deploy old B1 coefficients.

### External B2

`DE-SCOPED / NOT ACTIVE`

The user explicitly chose to continue direction research from GOLD-internal information and V8-A rather than external/cross-market inputs.

`V8_B2_SOURCE_OF_MOVE_RESEARCH_CONTRACT.md` is historical only.

## Internal-only direction research completed after B1 correction

The project tested whether frozen V8-A could expose direction through better preprocessing rather than as a simple scalar.

Families tested included:

- full V8-A P15/P30/P60 trajectory;
- probability slope/acceleration/shape;
- price sequence + probability sequence;
- small temporal CNN;
- event-centered OHLC/MA/BB geometry;
- causal regime normalization of price and V8-A logit state;
- directional semivariance/body/wick/tick-activity decomposition;
- score fusion / two-score stacking;
- recent-year and rolling retraining controls;
- event-family conditioning;
- selective confidence tails;
- delayed 1/3/5/10-minute response experiments.

Typical pattern:

```text
2024 discovery: moderate AUC can be produced
2025 validation: weakens materially
2026 stress: tends toward ~0.5
```

No broad direction model is authorized.

## Important failed apparent edges

### Delayed-response illusion

Using the first 5 minutes after an event to predict the original event-C0 +/-10 race produced apparently strong continuation.

This was rejected because the first 5-minute move mechanically shortens one barrier and lengthens the other.

After resetting C0 at the delayed decision and defining a new symmetric +/-10 race, the large effect disappeared.

### Selective-tail illusion / reproducibility failure

A prior score artifact suggested 60m chosen-side hit rates above 70%.

It did not survive independent exact reconstruction using the current event ledger and explicit causal signed-activity equations.

Exact rebuild direction AUC:

```text
30m: 2025 ~0.533 / 2026 ~0.520
60m: 2025 ~0.516 / 2026 ~0.506
```

High chosen-side hit rates after adding V8-A were explained primarily by higher `move_rate`, while conditional direction accuracy stayed near 50%.

## Mandatory accounting

Always decompose:

```text
chosen_hit = movement selection + directional contribution
```

Report:

```text
move_rate
conditional_direction_accuracy
chosen_side_hit_rate
directional_excess = chosen_side_hit_rate - 0.5*move_rate
```

## Current best conclusion

```text
GOLD endogenous history -> near-term movement intensity: strong
GOLD endogenous history -> stable broad near-term sign: not demonstrated
```

V8-A remains useful even though V8-B has not yet found stable sign information.

## Immediate next work

1. finish exact `V8-A trajectory × factual event` conditioning on the frozen continuous probability series;
2. run the sequential `WAIT -> observe -> recenter -> update` policy with a new C0 at every decision;
3. keep all selection rules causal and independently reproducible;
4. test overlap, month, hour, event-family and direction concentration;
5. report directional excess, MAE/MFE and opposite-barrier path;
6. do not implement a direction MT5 companion until a candidate survives 2024 discovery -> 2025 validation -> 2026 stress;
7. keep GOLD# 2021 locked.

## Reading order next session

1. `docs/ea/v8/AGENTS_V8.md`
2. `docs/ea/v8/HANDOFF_V8.md`
3. `docs/ea/v8/V8_B_INTERNAL_DIRECTION_RESEARCH_20260831.md`
4. `docs/ea/v8/V8_B1_CAUSAL_ALIGNMENT_INVALIDATION.md`
5. `docs/ea/v8/V8_005_MOVEMENT_PROBABILITY_INDICATOR.md`
6. `docs/ea/v8/DECISIONS_V8.md`
7. `docs/ea/v8/RESEARCH_STATE_V8.md`
8. `docs/ea/v8/V8_RESEARCH_JOURNEY.md`

Always refresh GitHub HEAD before continuing.
