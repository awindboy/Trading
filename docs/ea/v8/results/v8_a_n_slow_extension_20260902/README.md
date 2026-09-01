# V8-A-N-SLOW extension result tables

Status: development evidence only.

Source:
`GOLD#_M1_202201030100_202608282357.csv`
SHA256:
`626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

Main definitions:

```text
H4 scale = Wilder ATR14 from immediately previous completed H4 bar
target held constant for H4 decision block
```

Files:

- `target_family_annual_base_rates.csv`: 60/120/240 x 0.50/0.75/1.00 movement census.
- `target_family_quarterly_base_rates.csv`: quarter stress.
- `target_family_phase0_binary_model_metrics.csv`: phase-0 independent movement model screen for all 9 coordinates.
- `target075_survival_model_metrics.csv`: joint 0.75-H4-ATR P60/P120/P240 Phase-0/Phase-2 metrics.
- `target075_survival_fresh_jaccard.csv`: fresh75 event identity sensitivity.
- `current_fresh_extension_realization.csv`: larger-move realization after current 0.25/P15 onset fresh75.
- `extension_model_on_current_fresh.csv`: added ranking of higher-horizon scores inside current onset fresh events.
- direction `*_fail.csv` files: mandatory direction falsification diagnostics.

2026 is partial through 2026-08-28. 2021 is not used.
