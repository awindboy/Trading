# V8-B Local Direction Target Research

Date: `2026-08-31`
Status: `ACTIVE RESEARCH NARRATIVE / NO DIRECTION AUTHORITY`
V8-A: `FROZEN`
Market: `GOLD#`
External inputs: `NONE`
GOLD# 2021: `LOCKED`

## 1. Motivation

The research tested the hypothesis that earlier direction tasks were too broad. V8-A succeeds by asking one narrow question: whether +/-10 is reached within a fixed horizon. V8-B was therefore reformulated around short, explicitly directional targets.

## 2. B30 — Local endpoint direction

Targets:

```text
sign(close[t+H] - C0)
H = 15/30/60m
```

Later 5m/10m/15m variants were also tested.

Result: AUC generally about `0.50-0.52`. Event-only training did not materially improve it.

## 3. B31 — Direction-only representation

Past state was restricted to signed information:

- signed displacement;
- path efficiency;
- up/down semivariance imbalance;
- bullish/bearish body imbalance;
- wick imbalance;
- range location;
- signed tick-activity / price-impact proxies.

Endpoint sign and future excursion-dominance remained near chance to low-0.52 in 2024.

## 4. B32 — Independent +10 / -10 touch models

Instead of one first-hit label:

```text
P(+10 touched within H)
P(-10 touched within H)
```

Representative 2024 30m:

```text
+10 touch AUC ~0.655
-10 touch AUC ~0.646
```

The directional contrast was much weaker, implying shared movement-intensity information.

## 5. B33 — Mirrored symmetric model

A shared model was trained with vertically mirrored states:

```text
P(up|X)=f(X)
P(down|X)=f(mirror(X))
```

Representative 2024 30m:

```text
UP AUC ~0.664
DOWN AUC ~0.659
direction-skew AUC ~0.572
```

Later direction weakened to about `0.547` in 2025 and `0.512` in 2026.

## 6. B34 — Exclusive local direction

Training direction only on clear one-sided outcomes:

```text
+10 only within H -> UP
-10 only within H -> DOWN
both/neither -> excluded from direction training
```

The 15m horizon was strongest:

```text
2024 ~0.603
2025 ~0.556
2026 ~0.535
```

30m/60m were weaker.

A simple recent-15m direction-efficiency baseline was approximately:

```text
2024 ~0.639
2025 ~0.577
2026 ~0.531
```

This is a weak clue, not an edge claim.

## 7. B35 — Micro barriers

15m direction with small barriers:

```text
+/-1 -> near chance
+/-2 -> ~0.528 / 0.512 / 0.505
+/-3 -> ~0.553 / 0.518 / 0.506
```

for 2024/2025/2026. Smaller is not automatically more predictable; do not barrier-mine.

## 8. B36 — Ultra-local endpoint

Next 5m/10m/15m future-close sign remained about `0.50-0.52` AUC. Shrinking the horizon alone did not solve direction.

## 9. B37 — V8-A attention weighting

V8-A P15 was used as a sample weight rather than a direction feature. Chronological validation did not improve.

## 10. B38 — Magnitude-weighted direction

Binary future-close sign was weighted by absolute future 15m net displacement to emphasize clearer direction examples. Validation again did not improve.

## 11. B39 — Future local slope

The target became the sign of a fitted future price slope instead of endpoint sign. AUC remained about `0.50-0.53`.

## 12. Sequential WAIT / recenter test

Protocol:

```text
event at t0
WAIT 1m / 3m / 5m
observe only causal new GOLD data
new C0 = price at delayed decision
predict next 5m / 10m / 15m future-close sign
```

This removes the earlier original-C0 barrier-distance illusion.

Result:

```text
AUC generally ~0.50-0.52
```

The first response direction also failed to become a robust continuation confirmation and often showed weak mean-reversion.

Therefore simple WAIT followed by endpoint prediction is rejected.

## 13. Current next formulation

The only weakly persistent target was 15m exclusive direction, so the next experiment combines it with new causal post-event evidence:

```text
event
-> WAIT fixed 1m / 3m / 5m
-> new C0
-> next 15m:
   +10 only -> UP training example
   -10 only -> DOWN training example
   both/neither -> excluded from direction training
-> score all delayed eligible decisions
```

Primary controls:

- t=0 15m exclusive-direction model;
- simple recent-15m direction-efficiency baseline;
- frozen V8-A kept separate until genuine sign contribution is measured.

## 14. If positive, mandatory regression

Immediately test:

- information-boundary audit;
- same-M1 dual-touch ambiguity;
- label-boundary purge;
- full-population evaluation;
- outcome-blind non-overlap;
- 2024 discovery -> 2025 validation -> 2026 stress;
- month/hour/event/direction concentration;
- weekly/monthly block bootstrap;
- directional excess;
- MAE/MFE and opposite-side path.

## 15. Current conclusion

Target localization was worth testing but did not reveal a strong hidden sign edge by itself.

Current evidence:

```text
movement intensity: strongly learnable
static local sign: weak
15m exclusive one-side direction: weak but above chance in all three years
simple WAIT->recenter endpoint confirmation: failed
next justified test: WAIT->recenter->15m exclusive direction
```

No V8-B MT5 direction implementation is authorized.
