# V6-003D 2026 Holdout Validation — WORKING RESULTS

This package is deliberately NOT a GitHub documentation update.
It is a working validation bundle to be incorporated into the project documents
together with the pending MT5 parity work and the preceding Gold-family validation.

## Scope

Input:
- GOLD# 2026-01-02 through 2026-08-28
- BTCUSD# 2026-01-01 through 2026-08-29
- USDJPY# 2026-01-02 through 2026-08-28

Frozen architecture:
- H = DIRECT + D24 aligned + MENV HH, 50% pullback, 25% at +3R, residual BE, +5R
- L1 = DIRECT + D14=D24=dir, H-priority exclusion, +1R / 240 active-M1 cap
- L2 = ONE_RENEG + D24 aligned, +1R / 240 active-M1 cap

No threshold, symbol, lifecycle, or outcome-based rescue was introduced.

## Data quality

All three 2026 M1 files passed structural checks:
no duplicate timestamps, no time reversals, no OHLC consistency errors, no zero spread.

The markets are substantially more independent than the Gold-cross family:
H1 return correlation:
- GOLD vs BTCUSD: +0.292
- GOLD vs USDJPY: -0.222
- BTCUSD vs USDJPY: -0.092

D1 return correlation:
- GOLD vs BTCUSD: +0.331
- GOLD vs USDJPY: -0.279
- BTCUSD vs USDJPY: -0.134

## Carry-state issue

A Jan-1 cold reset is not causally correct for markets already observed through 2025,
because MENV uses ALL PRIOR same-market eligible DIRECT geometry.

Therefore:
- cold-reset outputs are retained only as a diagnostic;
- GOLD 2026 was separately checked with continuous historical carry and gives the same
  accepted trade result shown here: N10, WR60.0%, EV +0.0689R, net +0.6890R;
- BTCUSD/USDJPY results use end-2025 causal MENV baseline carry sensitivity.
  Full historical raw arrays were not mounted for an exact rolling-median replay.
- A USDJPY baseline sensitivity grid keeps pooled EV between about -0.059R and -0.011R,
  so the combined-strategy conclusion is not dependent on one precise terminal median.

## Carry-aware primary working result

Pooled descriptive:
- N = 42
- WR = 45.24%
- average positive = 1.013R
- EV = -0.034R/trade
- net = -1.432R
- sequence max DD = 4.769R

By market:
- BTCUSD#: N13, WR30.77%, EV -0.347R, net -4.505R
- GOLD#: N10, WR60.00%, EV +0.069R, net +0.689R
- USDJPY#: N19, WR47.37%, EV +0.125R, net +2.384R

By module:
- H: N8, WR25.00%, avg positive 2.625R, EV -0.094R, net -0.750R
- L1: N15, WR26.67%, avg positive 0.771R, EV -0.443R, net -6.644R
- L2: N19, WR68.42%, avg positive 0.839R, EV +0.314R, net +5.961R

H includes a USDJPY TP5 (+4.5R) and a BE-after-3R (+0.75R), so the H payoff mechanism
is not absent. It is simply not proven profitable in this holdout.

L2 D24-age shadow:
- age <24: N15, WR66.67%, EV +0.297R
- age >=24: N4, WR75.00%, EV +0.378R

The age relation remains directionally consistent but is still too small to promote
to a gate. Do not tune 24.

## Research decision

COMBINED FROZEN ARCHITECTURE: EXTERNAL/TEMPORAL VALIDATION FAIL
MODULE L2: REPLICATED / KEEP FROZEN
MODULE L1: FAILED TO REPLICATE ON 2026 FACTOR-DIVERSE HOLDOUT
MODULE H: PAYOFF FUNCTION OBSERVED, EDGE NOT VALIDATED

No post-hoc threshold rescue is authorized.
The current combined V6-003D control should remain frozen as a research comparison
control, not be promoted as a validated final strategy.

Full commission/slippage and H swap are still absent, so the economic conclusion
cannot improve after full costs without new evidence.

## Input hash

2026data.zip SHA256:
11083838b4a6521d21f3e7cbbcd14c2c365a4752636d731314abea2068c0ba0a
