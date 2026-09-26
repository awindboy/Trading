# V13 handoff

Last synchronized: `2026-09-26`
Status: `BASELINE 0 FROZEN / ACTUAL-TICK STRUCTURAL PARITY CONFIRMED / HA-0 MEASUREMENT NEXT`

## Resume point

V13 has moved from “build the simple EA” to “use the simple EA to learn HA.”

The latest uploaded MT5 report is an extended real-tick run through
`2026-09-26`. Its canonical prefix confirms the intended Journey/Child structure:

```text
965 closed Journeys through the canonical source cutoff
3,858 Children inside those 965 closed Journeys
+ one open Journey (J966) beginning 2026-08-28 20:00
```

Those counts match the deterministic H4 sanity reconstruction. The report is
not the official exact-window economic receipt because it extends beyond
`2026-08-28` and used `1:500` leverage rather than the frozen protocol's `1:100`.
See the diagnostic receipt.

## Read first

1. refresh GitHub `main`;
2. read `AGENTS_V13.md`;
3. read the authority map and this handoff;
4. read `RESEARCH_STATE_V13.md`;
5. read `V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md`;
6. read `V13_HA_RESEARCH_ROADMAP_20260926.md`.

## Baseline in one block

```text
standard H4 HA only
same-color run = Journey
one Child after every completed same-color H4 HA
maximum 10 Children
first opposite completed H4 HA = close all
same event then starts opposite Journey
1 fixed unit per Child
no SL / no TP / no filters / no ML
```

## What was learned conceptually

Do not overinterpret the current simple strategy.

The useful result is that it exposes HA behavior:

- smoothing creates long same-color persistence during directional moves;
- the same persistence delays reversal confirmation;
- later Children naturally enter farther along the move and can give back more
  before an opposite color appears;
- short choppy runs and long persistent runs are two manifestations of the same
  smoothing mechanism.

This is not authority to ban SHORTs, lower the ten-Child cap, or add a fixed
late-Child rule.

## Immediate next work — HA-0

Do **not** change the EA strategy.

Build an observation ledger for every completed H4 bar / Child / Journey with:

```text
standard HA OHLC
HA Delta and absolute Delta
HA body and full range
body/range strength
upper and lower wick lengths/ratios
directional-wick and opposite-wick state
no-opposite-wick flag
same-color streak
Delta/body expansion or contraction
raw OHLC morphology
raw-price <-> HA displacement
```

Freeze these fields at the completed-bar decision time.

Store future outcomes separately: bars/time to opposite color, Journey final
length, MFE/MAE, peak time, giveback to HA exit, and Child/Journey terminal PnL.

First question:

> How does standard HA morphology evolve from Journey birth through persistent
> trend, contraction, raw-price turn and eventual opposite-color confirmation?

No threshold and no trading change is authorized in HA-0.

## Following order

After HA-0, follow the roadmap. Do not jump directly to EMA/ADX/ML merely because
external sources combine them successfully in examples.
