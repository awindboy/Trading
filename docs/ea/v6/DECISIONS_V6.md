# V6 Decisions

Status: `ACTIVE DECISION LEDGER`
Date: `2026-08-29`

Older V6 decision documents and result files remain historical evidence. The entries below record the active post-`8f9c6e3` research decisions from the role-conditioned phase.

## D048 — use active-market time for horizon research

Wall-clock holding time is invalid across weekends/session closures. L/H horizon studies use active M1 bars.

## D049 — direction accuracy must be base-rate aware

Raw LONG/SHORT accuracy can be distorted by market endpoint drift. Compare against market-year directional base rate before claiming side failure.

## D050 — first-M1-flip use of `m1_direct_transfer` is look-ahead

`m1_direct_transfer` is only fully known at the later M5 trigger. Any first-M1-flip result conditioned on future absence of additional flips is invalid and discarded.

## D051 — physical horizon outranks chart-TF label

Equal 24-bar lookbacks on M30/H1/H4 represent different physical durations. H evidence is interpreted as approximately 24 active-hour displacement, not “H1 is best.”

## D052 — L and H require different horizon state

L short-horizon resumption requires shorter and longer persistence to be synchronized; H large destination can tolerate shorter-horizon disagreement when D24 direction and MENV destination are valid.

## D053 — H destination remains MENV HIGH_HIGH

MENV direction ownership is rejected. MENV retains destination authority only. Non-HH, mixed-quadrant and stronger-HH score variants did not improve robust economics.

## D054 — L1 research control

L1 is DIRECT + D14=D24=local, H-authorized parent excluded, market Entry, sweep-extreme SL, +1R or 4 active-hour cap.

## D055 — ONE_RENEG is a second causal M1 path family

The exact `event -> opposite -> event` ownership sequence before M5 trigger is distinct from clean direct transfer. Multi-renegotiation and other noisy paths are not equivalent.

## D056 — L2 research control

L2 is ONE_RENEG + D24 aligned, market Entry, sweep-extreme SL, +1R or 4 active-hour cap.

## D057 — generalized ANY_ALIGN is density extension, not core authority

Allowing D14-only alignment adds trades but produces thin/cost-sensitive economics. Core L2 retains D24 alignment.

## D058 — causal H priority is decided at trigger authorization

If a DIRECT parent is H-authorized, later H pending non-fill cannot be used to resurrect L. Future fill outcome is not available at the routing decision.

## D059 — L lifecycle tuning family is closed on consumed data

1R harvest, pure 4h hold, 50/50 partial, BE residual, +0.5R lock and midpoint routing form a real WR/payoff frontier. Do not search nearby fractions/hours to numerically hit targets.

## D060 — H 4h impatience exit is rejected

Requiring +1R within 4 active hours cuts slow-starting eventual TP5 winners and materially reduces H EV.

## D061 — mature D24 does not replace local path quality

Noisy M1 paths remain negative even when D24 is aligned and mature. Direction authority and local negotiation quality are separate stages.

## D062 — mature D24 does not replace H destination state

D24 aligned+mature non-HH events do not support the H +3/+5 lifecycle. MENV HH remains necessary for large destination.

## D063 — L2 D24 age is shadow only

Consumed-panel mature L2 is much stronger than fresh L2, but market recurrence is imperfect and external N is too small. Do not promote an age gate or mature-runner lifecycle before independent validation.

## D064 — event source is not direction authority by definition

OB/FVG/high-low/liquidity labels are researcher-defined candidate locations. Event-source studies must separate location/movement state, body-close interaction, direction authority and execution pipeline.

## D065 — chart-only direction research excludes spread

Spread/slippage may not be embedded in directional labels. Execution belongs in monetization/execution stages. Earlier spread-contaminated FVG directional claims were discarded.

## D066 — FVG duplicate-weighting correction

Overlapping FVG zones can share touch/confirm times. Joins must include unique event/zone identity. Prior shallow-tree results affected by duplicated weighting were withdrawn.

## D067 — FVG research closed

After correcting event identity and chart-only direction labels, M15 FVG is weak as an independent authority and H1 FVG's small tilt does not survive path/cost economics. No active FVG branch remains.

## D068 — alternative source proliferation is closed

M5 liquidity, previous-H4 range, PDH/PDL direct strategies, M15 confirmed pivots, opening range, breakout/retest, delayed failed-break, generic pullback and M15 BOS retest did not produce robust replacement modules. Do not rescue via threshold tuning.

## D069 — existing M5 BOS confirmation is quality, not needless delay

A simpler sweep-candle displacement confirmation increased N but destroyed L economics. Do not weaken M5 BOS solely to increase trade count.

## D070 — recovery->M5 conversion is a density descriptor

This conversion rate strongly explains market opportunity density but does not reliably predict EV/WR. It may be used in outcome-blind market-suitability screening for density only.

## D071 — freeze current role-conditioned core

The current consumed-panel comparison control is:

```text
H  = DIRECT + D24 aligned + MENV HH
L1 = DIRECT + D14=D24=local, excluding H-authorized parent
L2 = ONE_RENEG + D24 aligned
```

Combined: `253 trades / WR 54.55% / avg positive 1.269R / EV +0.304R / net +76.96R / 11 of 13 market-years positive`.

This is a research freeze, not production authority.

## D072 — stop same-panel micro-tuning by default

Next claim-grade work should use new outcome-blind data and execution validation. GOLD2021 remains untouched.
