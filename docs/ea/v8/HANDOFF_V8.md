# V8 Development Handoff

Last updated: `2026-08-31`
GitHub base audited: `93f8c829c4825b60942cfd5260da06b30baeacd4`
Current phase: `V8-B LOCAL / SEQUENTIAL DIRECTION TARGET RESEARCH`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## Current branch status

### V8-A

`FROZEN / RETAINED`

V8-A remains the 15m/30m/60m +/-10 movement-probability model and MT5 shadow indicator. Do not modify V8-A to rescue V8-B.

### V8-B history

Still authoritative:

- original B1 high AUC invalidated by M15/H1 lookahead;
- original-C0 delayed-response continuation invalidated by barrier-distance asymmetry;
- selective 70-90% direction-tail artifact rejected after exact independent rebuild;
- external/cross-market branch de-scoped by user decision.

## New research question

The active hypothesis is now narrower:

> V8-A succeeds because it predicts one local property only: whether a +/-10 move occurs within a fixed horizon. V8-B may also need an equally local target that predicts only short-horizon sign, rather than a broad eventual direction.

This hypothesis has now been tested through B30-B39 and the first fully recentered sequential experiment.

## B30 — Local endpoint direction

Targets:

```text
sign(close[t+H] - C0)
H = 15/30/60m
```

Later 5m/10m/15m versions were also tested.

Result:

```text
AUC generally ~0.50-0.52
```

Event-only training did not materially improve the result.

## B31 — Direction-only representation

Past GOLD state was restricted toward signed information:

- signed net displacement;
- path efficiency;
- up/down semivariance imbalance;
- bullish/bearish body imbalance;
- wick imbalance;
- rolling-range location;
- signed tick activity / price-impact proxies.

Endpoint sign and future excursion-dominance targets remained about chance to low-0.52 in 2024.

## B32/B33 — Independent up/down touch models

A V8-A-like formulation was tested:

```text
P(+10 touched within H)
P(-10 touched within H)
```

Representative 2024 30m:

```text
+10 touch AUC ~0.655
-10 touch AUC ~0.646
```

A mirrored symmetric model reached approximately:

```text
+10 AUC ~0.664
-10 AUC ~0.659
pure direction-skew AUC ~0.572
```

But temporal validation weakened:

```text
2025 direction ~0.547
2026 direction ~0.512
```

Interpretation: individual touch models relearn substantial movement-intensity information; stable sign information is much weaker.

## B34 — Exclusive local direction

Direction training was limited to clear one-sided outcomes:

```text
+10 only within H -> UP
-10 only within H -> DOWN
both/neither -> excluded from direction training
```

The prediction must still be applied back to all eligible events for operational evaluation.

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

This is the best weak clue so far, not direction authority.

## B35 — Micro barriers

15m local barriers:

```text
+/-1 -> near chance
+/-2 -> ~0.528 / 0.512 / 0.505
+/-3 -> ~0.553 / 0.518 / 0.506
```

for 2024/2025/2026.

Smaller barriers are not automatically more predictable. Do not barrier-mine.

## B36 — Ultra-local endpoint

5m/10m/15m future-close direction remained:

```text
AUC ~0.50-0.52
```

Merely shrinking horizon does not solve direction.

## B37/B38 — Direction-label weighting

Tested:

- V8-A P15 as sample weight;
- absolute future 15m net displacement as sample weight.

Neither improved temporal validation.

## B39 — Future local slope

The sign of a fitted future price slope was used instead of endpoint sign.

Result:

```text
AUC ~0.50-0.53
```

Endpoint noise was not the sole problem.

## Sequential WAIT/recenter result

Completed protocol:

```text
event
-> WAIT 1m / 3m / 5m
-> observe only causal new information
-> new C0 = delayed decision price
-> predict next 5m / 10m / 15m future-close sign
```

Result:

```text
AUC generally ~0.50-0.52
```

The first post-event response also did not become a robust continuation signal and often showed weak mean-reversion.

Therefore simple WAIT -> recenter -> endpoint confirmation is rejected.

## Immediate next experiment

Do not return to broad endpoint sign.

Test:

```text
event
-> WAIT fixed 1m / 3m / 5m
-> reset C0 at delayed decision
-> next 15m:
      +10 only = UP direction example
      -10 only = DOWN direction example
      both/neither = excluded from direction training
-> apply score back to all delayed eligible decisions
```

This combines the only weakly persistent local target with genuinely new causal post-event evidence.

## Mandatory checks if positive

1. timestamp / information-boundary audit;
2. full-population evaluation;
3. outcome-blind non-overlap;
4. 2024 discovery -> 2025 validation -> 2026 stress;
5. month/hour/event/direction breakdown;
6. weekly/monthly cluster bootstrap;
7. movement-rate vs directional-excess decomposition;
8. MAE/MFE and opposite-side path analysis.

## Current best conclusion

```text
V8-A movement probability: strong and frozen
broad t=0 direction: not demonstrated
local t=0 direction: weak at best
simple WAIT->recenter endpoint direction: failed
next candidate: WAIT->recenter->15m exclusive +/-10 direction
```

GOLD# 2021 remains locked.

## Reading order next session

1. `docs/ea/v8/AGENTS_V8.md`
2. `docs/ea/v8/HANDOFF_V8.md`
3. `docs/ea/v8/V8_B_LOCAL_DIRECTION_RESEARCH_20260831.md`
4. `docs/ea/v8/V8_B_INTERNAL_DIRECTION_RESEARCH_20260831.md`
5. `docs/ea/v8/V8_B1_CAUSAL_ALIGNMENT_INVALIDATION.md`
6. `docs/ea/v8/DECISIONS_V8.md`
7. `docs/ea/v8/RESEARCH_STATE_V8.md`
8. `docs/ea/v8/BACKLOG_V8.md`

Always refresh GitHub HEAD before continuing.
