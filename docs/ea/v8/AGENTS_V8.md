# V8 Research Instructions

Status: `ACTIVE`
Generation: `V8`
Active branches:
- `V8-A MOVEMENT PROBABILITY` — FROZEN
- `V8-B LOCAL / SEQUENTIAL DIRECTION` — ACTIVE RESEARCH / NO AUTHORITY
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Current thesis

V8-A retains strong open-development evidence for short-horizon movement intensity. V8-B remains separate and must not convert movement probability into LONG/SHORT authority.

The active V8-B question is now narrow:

> Can direction become learnable when V8-B is trained only on a local short-horizon sign target, analogous to V8-A's localized movement target?

## 2. V8-A remains frozen

Do not change:

```text
C0 = completed M5 decision close
barrier = +/-10 GOLD price units
H = 15m / 30m / 60m
53-feature causal M1 movement representation
walk-forward historical model policy
```

## 3. Internal-only direction

External/cross-market data are de-scoped unless explicitly reopened.

V8-B may use only causal GOLD information plus frozen V8-A state.

## 4. Permanent causality rules

Completed resampled bars are available only when:

```text
bar_start + timeframe_duration <= decision_time
```

Current partial HTF inputs must be rebuilt from already-observed lower-timeframe data.

Outcome windows crossing an evaluation boundary must be purged from training.

## 5. Invalidated evidence

Do not revive:

- original B1 high-AUC HTF model;
- selective 70-90% tail artifact that failed exact reconstruction;
- delayed-response results using original event C0 after observing new price.

## 6. Local-target findings

Tested and not stable:

- 5/10/15/30/60m future-close sign;
- future local slope;
- excursion dominance;
- +/-1/2/3 micro barriers;
- V8-A-weighted direction loss;
- future-magnitude-weighted direction loss;
- simple WAIT 1/3/5m -> recenter -> endpoint sign.

The only weakly persistent local clue is 15m exclusive direction:

```text
+10 only -> UP
-10 only -> DOWN
both/neither -> not direction-training rows
```

Approximate AUC:

```text
2024 0.603
2025 0.556
2026 0.535
```

This is research evidence only.

## 7. Recenter every delayed decision

For sequential studies:

```text
WAIT
-> new decision time
-> new C0 = current causal price
-> define all future targets from new C0
```

Never measure delayed direction against the old event C0.

## 8. Directional accounting

Always separate movement filtering from sign information.

Report:

```text
move_rate
conditional_direction_accuracy
chosen_side_hit_rate
directional_excess
```

where:

```text
directional_excess = chosen_side_hit_rate - 0.5 * move_rate
```

## 9. Current next experiment

```text
event
-> WAIT 1/3/5m
-> reset C0
-> next 15m exclusive direction:
   +10 only = UP
   -10 only = DOWN
   both/neither excluded from direction training
-> evaluate prediction on all delayed eligible decisions
```

If positive, immediately run 2024->2025->2026 temporal validation, non-overlap, cluster bootstrap, concentration, MAE/MFE and opposite-side path checks.

## 10. Deployment gate

No MT5 direction companion until a candidate is strictly causal, fully reproducible, survives later-year validation, and shows genuine directional excess rather than movement selection.

## 11. Reserve

`GOLD# 2021 = LOCKED / UNTOUCHED`
