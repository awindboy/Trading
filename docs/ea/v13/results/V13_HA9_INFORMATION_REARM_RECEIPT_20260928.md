# V13 HA-9 information-based re-arm receipt

Last synchronized: `2026-09-28`
Status: `CONSUMED DEVELOPMENT + POST-CUTOFF QUASI-HOLDOUT / REJECTED / NOT ACTION AUTHORITY`

## 1. Question

After an accepted add-on closes negative by `PROOF_TIMEOUT` or
`BREAKOUT_LOCK`, can later same-Journey add-ons be blocked until genuinely new
causal information appears?

Predeclared information events were:

- the new completed signal H4 breaks the failed Child's favorable extreme;
- a fresh close beyond a previously confirmed causal raw progress swing;
- the signal H4's internal H1 path has no opposition;
- signal-H4 absolute HA delta re-expands beyond the failed signal H4;
- the logical OR of those events.

Child #1 is always retained. A skipped Child creates no later failure event.

## 2. One-failure re-arm is only exposure reduction

Canonical actual ledger:

| Gate after one failed Child | Selected | Wins | Losses | WR | Net USD | DD | Skipped W/L |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| None | 3,858 | 2,118 | 1,734 | 54.98% | +3,067.50 | 1,313.10 | 0 / 0 |
| Failed extreme break | 3,270 | 1,777 | 1,489 | 54.41% | +2,954.39 | 1,080.18 | 341 / 245 |
| Fresh raw-swing close | 2,958 | 1,571 | 1,383 | 53.18% | +2,485.87 | 1,017.00 | 547 / 351 |
| H1 no opposition | 3,183 | 1,724 | 1,453 | 54.27% | +2,879.10 | 1,100.33 | 394 / 281 |
| H4 delta re-expansion | 3,062 | 1,624 | 1,435 | 53.09% | +2,399.56 | 1,093.74 | 494 / 299 |
| Any new information | 3,365 | 1,826 | 1,533 | 54.36% | +2,761.82 | 1,082.72 | 292 / 201 |

Every gate removes more winning than losing Children and lowers win rate.
Lower DD is explained by lower exposure, not by identifying repeat-loss
opportunities. These mechanisms are rejected.

## 3. Two-failure history is more selective but still weak

Requiring two consecutive accepted tactical failures before arming the gate
reduced the intervention substantially.

| Gate after two failures | Selected | Wins | Losses | WR | Net USD | DD | Streak | Skipped W/L |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Extreme break | 3,784 | 2,076 | 1,702 | 54.95% | +3,083.48 | 1,338.93 | 13 | 42 / 32 |
| Any bar information | 3,793 | 2,084 | 1,703 | 55.03% | +3,099.42 | 1,338.93 | 13 | 34 / 31 |

Fresh raw-swing close added no selections beyond extreme/H1/delta information
in the `any` combination.

The two-failure `any bar information` version removed 31 losses and 34 wins.
It raised net by only `$31.92`, worsened DD by `$25.83`, and reduced maximum
loss streak by one. Its apparent benefit was concentrated in 2024:

```text
2024: losses -17, net +71.90, DD improved
2025: losses  -4, net -36.47, DD unchanged
2026: losses -10, net  -3.51, DD worsened
```

This is not a stable separation of bad repeat entries.

## 4. Post-cutoff quasi-holdout

The two-failure `any bar information` rule was frozen before inspecting the
post-cutoff re-arm sequence. On 99 usable Children:

| Policy | Selected | Wins | Losses | Net USD | DD | Streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Actual | 99 | 51 | 48 | +7.13 | 477.37 | 8 |
| Two-failure re-arm | 94 | 47 | 47 | -18.12 | 493.33 | 8 |

It skipped five Children: four winners and one loser, with `+$25.25` skipped
net. The result is the opposite of the intended repeat-loss selection.

## 5. Boundary and decision

This audit uses the actual C2..C10 opportunity set. Skipping a Child could free
a slot beyond actual C10, and those replacement opportunities are not created.
That limits exact strategy economics. It does not rescue the mechanism: even
within the observed opportunity set, the gate selects winners for removal at
least as often as losses and fails the post-cutoff direction check.

Rejected:

- one-failure information re-arm;
- two-failure extreme re-arm;
- two-failure any-information re-arm;
- parameterizing a fixed cooldown to rescue the same idea.

The next research should separate existing runner retention from permission to
add a new late Child. It should not continue searching for a better cooldown or
another minor re-arm exception.

## 6. Reproduction artifacts

- `research/v13/ha9_information_rearm_audit.py`
- `output/v13_ha9_information_rearm_20260928/summary.json`
- post-cutoff reconstruction in
  `research/v13/ha9_timeout_extension_holdout.py`
