# V5-035B — Post-1R Structural Lock Availability Results

Status: `COMPLETED / SHADOW-ONLY / NEGATIVE AS SIMPLE RESCUE`
Date: `2026-08-27`
Preregistration SHA-256: `d51f6872297cb9b3fdb724fe7e4bed59d6b9b910e3b7c1c2a990bc3fc102201b`

## Question

After clear +1R survival, does the same 240m timeframe commonly provide a causal favorable pivot that could lock profit
before the current BE/adverse exit?

The audit did not apply the stop.

LONG:
- causal confirmed 3-bar pivot low formed after +1R;
- hypothetical stop = pivot low - 1 point;
- stop must be above Entry.

SHORT mirrors.

## Result

```text
clear +1R N                   223
positive structural lock      96 = 43.05%

first lock median             0.794R
max available lock median     1.616R
median time to first lock    19.9h
```

Key split:

```text
current EMA/slow runner trades
N                             123
lock available                 71 = 57.72%
max lock median               2.621R

current partial-BE trades
N                             100
lock available                 25 = 25.00%
max lock median               0.765R
```

## Interpretation

Same-240m structural trailing is much more available on trades that already become large runners than on the exact
partial-BE population that would need to be rescued.

Therefore:

```text
240m structural trailing
!= supported simple rescue for the WR/payoff conflict
```

This does not prove every structural trailing method fails.
It prohibits promoting this specific concept without a new preregistered reason.
