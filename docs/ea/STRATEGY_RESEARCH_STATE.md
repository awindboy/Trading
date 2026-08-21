# Strategy Robustness Research State

Last updated: 2026-08-21
Repository base before handoff package: `c541b19d68ac1589575bfaf1ab07abf1ee296a09`
Current code/research identity: `1.93R1L9 / EXIT_ARCHITECTURE_RESEARCH_V1`
Current research phase: **D-147 EXIT ARCHITECTURE RESEARCH V1 — IMPLEMENTED / COMPILE + BASELINE PARITY PENDING**
Strategy authority: **UNCHANGED; ORIGINAL MODE IS BASELINE CONTROL**
2021: **UNTOUCHED**

## Objective

The project does not target a cosmetic 50% hit rate at 1R.

The target remains:

```text
realized win rate >= 50%
+
average winner / target meaningfully > 1R
+
positive expectancy after spread/commission/slippage
+
robustness across symbols and periods
```

A 50% win rate at exactly 1R is gross breakeven and is not the project objective.

## Current baseline interpretation

The current deterministic baseline often pursues distant structural liquidity objectives. That architecture naturally creates low structural-TP hit rates and dependence on occasional large winners.

D-144 showed that on GOLD 2025 many structural-objective losers first reached meaningful positive R.

D-145 then separated:

```text
Entry survival: Fill -> +1R
Winner continuation: +1R -> +2R+
```

These are now distinct research problems.

## Entry survival status

2025 continuation:

```text
GOLD    30/51  = 58.8%
BTCUSD  54/114 = 47.4%
SILVER  18/45  = 40.0%
CADJPY  30/111 = 27.0%

total = 132/321 = 41.1%
```

Therefore the current Entry architecture is not yet broadly compatible with the final >=50% win-rate requirement.

No D-145 runner feature has been proven to solve this problem.

## Winner-continuation status

Development/generalization panel:

```text
GOLD 2023
GOLD 2024
GOLD 2025
BTCUSD 2025
SILVER 2025
CADJPY 2025
```

Resolved +1R conditional population:

```text
190 trades
129 reached +2R before SL
P(+2R | +1R) = 67.9%
```

Pooled probability is descriptive only.

### Strongest surviving relationship

At first +1R, eventual +2R runners had lower M30 protected-to-current-external range progress than trades that exhausted before +2R.

Relationship direction:

```text
6 / 6 market-year aggregate cells
11 / 11 comparable market-year x direction cells
```

Valid M30 scenario-direction range coverage:

```text
147 / 190
```

Missing range states are not imputed.

Current interpretation:

> A Root/FVG entry can create a local reaction. Once +1R is reached, continuation for another R is related to how mature the current M30 directional protected-to-external delivery already is.

This relationship is not yet proven causal.

### Supporting relationship

Risk-normalized remaining distance to current M30 external is larger for runners in all six market-year aggregate cells.

Because its denominator is actual Fill-to-SL risk and direction-level consistency is weaker, it remains supporting evidence rather than the primary state variable.

## Demoted / rejected simple runner explanations

Do not promote the following from D-145:

```text
M30 net directional advance
FVG -> Fill elapsed time
FVG -> Fill favorable displacement
simple M30 progression
simple PB count
time-to-1R / 1R speed
M1 same-direction continuation
standalone M30 leg-expansion rule
clean-path / low-MAE quality
```

They are unstable across markets/directions or do not discriminate the intended problem robustly.

## Important negative result

M30 maturity is not a stable discriminator of `Fill -> +1R` success.

Therefore it is not an Entry filter.

Also, +2R runners often had more adverse excursion before first +1R than later-exhausting trades. Do not use low MAE / fast +1R as a generic quality gate.

## D-146 hypothesis

D-146 asks whether M30 external is a true causal waypoint or only a descriptive proxy.

Primary hypothesis:

```text
+1R reached near mature M30 external
+
still reaches +2R
-> an outward same-direction M30 structure refresh often occurs after +1R
```

Counterpart:

```text
+1R reached with room
+
fails before +2R
-> M30 protected structure deteriorates / owner changes / opposite event appears before +2R
```

If post-+1R structure changes do not explain these exceptions, M30 maturity must be treated as descriptive rather than promoted into exit architecture.

## D-146 strategy boundary

D-146 is measurement-only.

No:

```text
fixed TP replacement
dynamic close
progress threshold
remaining-room threshold
Entry veto
runner score
direction-specific special rule
```

`AGENTS.md` and `EA_SPEC.md` remain unchanged.

## Frozen Regime Research V1

Historical Frozen Regime Research V1 remains preserved as prior evidence:

`M30_CLEAN_PERSISTENT_EXPANDING`

It is not automatically combined with D-145 runner maturity, and no composite score is authorized.

2021 remains untouched.

## Next decisions

1. Compile the D-146 shadow tracker and validate audit OFF/ON non-interference.
2. Validate D-146 event integrity and runtime on GOLD 2025.
3. Test whether post-+1R M30 state transitions explain +2R success/failure across the development panel.
4. Only if a causal mechanism survives, design one controlled winner-extension strategy variant.
5. Separately open the Entry-survival causal study needed to lift Fill->+1R toward the final >=50% requirement.

Detailed evidence:
- `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md`

Next measurement contract:
- `docs/ea/D146_CONTINUATION_STATE_AUDIT.md`

## D-147 controlled exit-architecture branch

The next controlled strategy research branch is now D-147. It asks how much of the current realized-performance problem comes from post-fill profit giveback rather than Entry survival.

It intentionally does **not** use the D-145 M30 progress relationship as a threshold. The first comparison isolates mechanical exit architecture:

```text
ORIGINAL vs R_STEP_TRAILING vs R_STEP_PARTIAL
```

All three share the same Entry, original normalized SL, frozen structural objective, and initial structural TP. `R_STEP_PARTIAL` uses a frozen 50% of remaining volume at each newly reached integer R; no pooled parameter optimization is authorized.

Entry survival (`Fill -> +1R`) remains a separate causal study. A good D-147 result cannot be used as evidence that the Entry architecture has been fixed.
