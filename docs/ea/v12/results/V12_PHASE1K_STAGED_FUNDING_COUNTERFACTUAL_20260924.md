# V12 Phase 1K — Staged-funding counterfactual result

Status: **complete, reproducible, failed primary gate**  
Evidence: consumed development history through `2026-09-18 23:57`  
Trade/sizing authority: **none**

## Decision

The Phase 1J M15 mechanism is real as a path description, but it does **not**
improve V10 by gating its existing H4-spaced Children.

### Pooled test chronology

| Policy | Children retained | win-rate change | stops removed | stop/100 | tail retained | net R | equal-stop-budget R/unit |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 100.0% | — | — | 13.21 | 100.0% | +446.37 | 0.1831 |
| progression release | 97.7% | -0.03pp | 0.6% | 13.40 | 95.9% | +417.93 | 0.1690 |
| damage stop | 67.7% | -0.91pp | 21.1% | 15.54 | 77.9% | +318.39 | 0.1110 |
| progression or repair | 98.0% | -0.15pp | 0.6% | 13.36 | 95.9% | +414.80 | 0.1682 |
| first Child only | 47.6% | -3.81pp | 33.2% | 19.53 | 52.9% | +148.65 | 0.0412 |

`PROGRESSION_RELEASE` removes no repeat stopped units in any test fold. It
passes tail/frequency/raw-R gates but fails repeat-stop, all-stop, win-rate, and
equal-stop-budget gates.

## Why the promising Phase 1J contrast disappears

V10 adds Children at later H4 HA decisions. By then, two favorable M15 closes
have already occurred in nearly every run that will receive another Child,
including the runs that later stop. The event therefore retains `1,020/1,044`
test Children and is no longer selective at the capital decision moment.

The opposite rule is selective but indiscriminate. `DAMAGE_STOP` removes more
exposure than damage: funded exposure falls 32.3%, stops only 21.1%, and tail
capital 22.1%. Its normalized stop burden becomes worse.

## Consequence for V12 assembly

Do not use early M15 progression as a stale permission attached to the next H4
PHA. If the mechanism is developed further, the capital action must occur near
the event itself:

- first H4 Child remains the probe;
- an event-native M15 Child would be a new independent attempt with its own
  structural Hard SL;
- its purpose would be adding only when progression is currently demonstrated,
  not predicting the next H4 HA or rescuing the probe;
- existing later H4 Children cannot be silently replaced or backfilled.

That is a new Child architecture, not a parameter adjustment. It requires a new
contract and cannot reuse the failed fixed-k2 or complete-feature-stack funding
model under a new name.

## Reproducibility

Both six-file packs are byte-identical. All `58` V12 regression tests pass;
zero post-cutoff price rows were parsed.

GOLD# 2021 and post-cutoff chronology remain sealed.
