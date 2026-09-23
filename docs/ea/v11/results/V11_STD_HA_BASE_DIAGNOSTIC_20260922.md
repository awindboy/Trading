# V11 STD-HA base diagnostic

Date: `2026-09-22`

Status: `CONSUMED DEVELOPMENT EVIDENCE / STD WHOLE-BASE REPLACEMENT REJECTED / NO TRADE AUTHORITY`

## Question

Would rebuilding the liquidity/NHA study on H4 STD HA, rather than FAST HA, remove noisy PHA/NHA alternation and reduce stopped Children?

This is not a relabel of FAST runs. FAST and STD HA, their runs, each Child direction, entry, prior-STD-HA Hard SL, first opposite-HA exit, and same-M1 ambiguity were independently replayed from chronological raw M1. The rebuilt FAST baseline matched all 6,770 rows of the official V10 universe with zero direction, `k`, `L`, stop, or R mismatch.

## Main comparison

| Measure | FAST base | STD base |
| --- | ---: | ---: |
| resolved Children | 6,770 | 6,696 |
| Hard-SL Children | 1,784 | 2,249 |
| stop rate | 26.35% | 33.59% |
| completed run-ending NHA events | 2,066 | 1,506 |
| mean run length | 3.24 | 4.23 |
| one-bar triplet rotations | 26 | 7 |
| short-run triplet rotations (`L<=2`) | 252 | 94 |
| maximum stop streak | 11 | 11 |

STD did what smoothing should do: NHA/run endings fell `27.1%`, one-bar triplets fell `73.1%`, and short-run triplets fell `62.7%`. But it did not reduce the actual stop problem. Total stops increased by `465` (`+26.1%`), stop rate rose `7.24pp`, and the maximum stop streak did not improve. STD's total stop rate was worse in every calendar year from 2022 through the partial 2026 sample.

This rebuild takes run origin and neighboring run length from the complete HA stream even when that run's k1 Child was structurally invalid. The earlier FAST opportunity-derived diagnostic could not see those missing k1 rows; the complete chain therefore reports 252 rather than 247 FAST short-run triplets and moves 24 FAST events from route-present/no-progress to in-transit. Trade outcomes are unchanged, and the official FAST ledger still matches exactly.

The reason is timing. STD keeps the old HA direction alive longer. A final old-direction Child therefore has more time to hit its fixed structural SL before STD prints the opposite color. At run-ending events, prior-direction Child stop rates were `57.6%` for STD in-transit counterflow and `77.4%` for STD route-present/no-progress, versus `29.0%` and `73.5%` under FAST.

## The useful part: first Child after a completed STD flip

STD was better only at the new run's `k1` boundary:

| Measure | FAST k1 | STD k1 |
| --- | ---: | ---: |
| Children | 2,101 | 1,596 |
| stops | 636 | 464 |
| stop rate | 30.27% | 29.07% |
| sum R | +149.81R | +213.46R |

STD generated 505 fewer k1 attempts and 172 fewer k1 stops. The improvement was not era-stable, however: STD k1 stop rate was lower in 2022-2023, almost unchanged in 2025, and higher in 2024 and partial 2026.

After k1 the whole-base result deteriorated. STD `k2+` produced 1,785 stops versus 1,148 for FAST. Longer color persistence is therefore not the same as safer repeated participation.

The liquidity explanation remained descriptive but did not become a clean gate. Following an STD NHA, new-direction k1 stop rates were `16.8%` after H4-arrival/route-remains, `32.3%` after in-transit counterflow, and `29.0%` after route-present/no-progress. That ordering is directionally useful, but it does not isolate all avoidable stops and grants no veto authority.

## Economic caution

Uncapped sum R favored STD (`+649.25R` versus `+378.77R`), but this was not a clean robustness win:

- STD raw price-unit P/L was lower (`+5,404` versus `+12,048`);
- capping each Child at `6R` produced `-33.49R` for STD versus `+87.00R` for FAST;
- at a `10R` cap, STD remained slightly lower (`+232.24R` versus `+246.55R`);
- STD's maximum `116.88R` observation came from only `0.205` points of initial risk.

The uncapped result therefore reflects the risk-normalized right tail, including a very small-denominator extreme. It is not enough to promote STD as the new strategy base.

## Decision

- Reject replacing the entire FAST participation clock with STD HA.
- Retain STD as an observation coordinate and a narrow restart hypothesis: a completed STD flip may define a cleaner first independent Child than FAST, but this has not been tested with a frozen V11 admission contract or future-only chronology.
- Do not treat fewer HA color changes as evidence of fewer stops. Smoothing hides some counterflow until after the old-direction Child has already failed.
- Do not create a `k1-only STD` rule from this consumed sample. That would be a new trading contract requiring pre-registration and post-`2026-09-18 23:57` evidence.

## Reproduction

- script: `research/v11/analyze_v11_std_ha_liquidity_reason.py`;
- script SHA-256: `335712a408e4c4a7e01a547a6feb6ec736072655099732070075b8fe85f6bdd2`;
- script size: `23,365` bytes;
- local output: ignored `output/v11_std_ha_liquidity_reason_20260922/`;
- raw M1 SHA-256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`;
- official FAST universe SHA-256: `f352a99c746752ca259da33dbdaee9d8f0cb874bd01cf520a487fe1bdbf82609`;
- rebuilt FAST validation: 6,770/6,770 matched, zero categorical mismatches, max R error below `4e-15`;
- ledger SHA-256: `ae4d3577b62e23e9bbe3bb811a2d12a8426a42b328125e44b2f474b26b7d972f`;
- Python compile and manifest/hash checks: passed.
