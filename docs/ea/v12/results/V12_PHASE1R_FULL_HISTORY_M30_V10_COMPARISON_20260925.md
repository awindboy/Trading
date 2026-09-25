# V12 Phase 1R — full-history M30 versus V10 comparison

Status: **complete and reproducible / later-window improvement, full-history failure / no action authority**  
Date: `2026-09-25`

## Causal reconstruction

The M30 session-path policy was not fit once on all history and backfilled.
All 2022 candidates were traded as warmup. Four annual expanding models then
used only outcomes known by each year boundary to trade 2023, 2024, 2025, and
2026 through `2026-09-18 23:57`.

Across the 2023–2026 after-stop test cohorts, the policy excluded 641 of 3,817
candidates and removed 339 of 1,004 repeat stops (`33.76%`). Two independent
six-file builds are byte-identical.

## Full M30 history

| Policy | Children | Stops | Stops / 100 | Net R | R / 100 | PF | DD | Max streak | >=5R tail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M30 baseline | 17,012 | 4,820 | 28.33 | 384.61 | 2.26 | 1.053 | 108.92 | 5 | 2,121.03 |
| M30 session path | 16,371 | 4,481 | 27.37 | 329.97 | 2.02 | 1.048 | 95.25 | 6 | 1,884.23 |

The policy removes `7.03%` of all stops while removing `3.77%` of Children, but
loses `54.64R` and retains only `88.84%` of >=5R tail. Scaling it back to the
baseline's stopped-unit budget produces `354.93R`, only `92.28%` of baseline.
The apparent Phase-1P advantage is therefore not stable across full history.

The source of instability is visible by year. Policy minus baseline is
`-52.70R` in 2023, `-28.63R` in 2024, `+9.51R` in 2025, and `+17.18R` in 2026.
Filtering can also concatenate remaining stopped trades, so the full-history
maximum streak worsens from five to six despite fewer total stops.

## Fixed V10 window

The only direct comparison uses the selected-R7G interval from
`2024-10-01 01:00` through `2026-08-28 23:57`.

| Policy | Children | Units | Stopped units / 100 | Net R | R / 100 | PF | DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| M30 baseline | 6,898 | 6,898 | 28.89 | 189.88 | 2.75 | 1.065 | 92.01 |
| M30 session path | 6,572 | 6,572 | 27.63 | 209.76 | 3.19 | 1.076 | 67.62 |
| V10 R7G actual units | 1,649 | 3,881 | 12.52 | 741.01 | 19.09 | 1.682 | 57.00 |

The M30 policy improves its own later-window baseline by `19.89R`, removes
`8.88%` of all stops, and retains `91.93%` of tail. It is nevertheless far
below V10. At equal V10 funded units, M30 produces `123.87R` with `1,072.41`
stopped units versus V10's `741.01R` and `486` stopped units. At equal 486
stopped units, M30 produces only `56.14R`.

## Decision

The one-third repeat-stop reduction is real within the targeted cohort, but it
does not translate into a full-history V10 replacement. It is later-era
conditional and still funds far too many low-quality M30 attempts. Do not
promote the session-path score, annual model, top-quintile threshold, or larger
M30 size. The useful retained question is whether this state can modify an
already selective higher-quality base rather than replace V10 with all M30
`k=1` Children.
