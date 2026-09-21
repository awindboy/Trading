# V10 Progression / Damage-Repair and MA-Band Exploration Checkpoint

- Date: 2026-09-21
- Base Git HEAD: `438f6b4d588330b4cd2f1cae7cba968f14df36e4`
- Status: `CONSUMED-DATA EXPLORATION / NO STRATEGY OR EA AUTHORITY`
- Scope: test a semantic progression/damage-repair filter and explore normalized multi-timeframe MA ribbons around the existing V10 HA-primary candidate set.
- Promotion: none.

## 1. Authority and evidence boundary

This work follows the current V10 HA-primary routing. HA remains the participation clock. The MA ribbon is research instrumentation only and does not create, veto, size, or exit a live/production order.

The study uses consumed 2022-2026 raw M1 evidence. The R7G economic slice contains 1,649 resolved intended candidates from 2024-2026. The 66 positive-weight MT5 rows that did not resolve to the frozen causal universe were excluded; this includes execution-state mismatches and does not reinterpret the user's market-closed order failures.

Source hashes:

- raw M1: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
- frozen causal universe: `f352a99c746752ca259da33dbdaee9d8f0cb874bd01cf520a487fe1bdbf82609`
- MT5 R7G events: `c4348a34aa35d1e9793283cebbf1a028327c10e3e1c5a4fde2a9e74e3ff801a7`

## 2. Causal construction and liquidity-era normalization

H4, H1, and M15 bars were rebuilt chronologically from raw M1. The tested ribbons were:

- length: 20 and 60;
- average: SMA and linearly weighted WMA;
- input: raw close, raw `(open + close) / 2`, and FAST-HA `(HA open + HA close) / 2`.

Normalization was deliberately split by meaning:

- distance, span, and slope: same-timeframe causal Wilder ATR180;
- support, ordering, and penetration: fraction of MA lines, which is price-scale free;
- adaptive tail diagnostics: thresholds taken only from observations before the evaluated calendar year;
- reporting: 2024, 2025, and 2026 kept separate before pooling.

This is necessary rather than cosmetic. Median H4 ATR180 changed from `9.66` in 2022 and `8.92` in 2023 to `19.85` in 2025 and `45.48` in 2026. Relative H4 ATR/price also rose from roughly `0.47-0.58%` in 2022-2025 to `1.06%` in 2026.

MA1 is retained as the fast edge but excluded from support and penetration counts because MA1 equals the current input by definition. Penetration therefore means consecutive MA2..MAN lines crossed against the trade direction.

## 3. Progression and damage-repair result: reject

The exact semantic proposal was:

- progression proof: a completed raw H4 close beyond the launch PHA raw extreme;
- progression gate: allow only one selected, still-unproven Child per FAST run;
- damage-repair gate: after a same-direction unproven Child stops, block that direction until the proof level is repaired;
- no Parent direction veto.

R7G-weighted pooled result:

| Policy | Executed | Stops | Max stop streak | Delta R | L6+ positive-R retained |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 1,649 | 232 | 5 | 0.00 | 100.0% |
| Progression | 1,271 | 191 | 4 | -250.99 | 72.2% |
| Damage-repair | 418 | 52 | 4 | -320.42 | 39.9% |
| Combined | 316 | 47 | 4 | -509.22 | 25.8% |

Progression lost R in every evaluated year: `-4.73R`, `-156.78R`, and `-89.48R`. Damage-repair was `+1.31R` in 2024 but `-155.78R` in 2025 and `-165.94R` in 2026.

Conclusion: the rules reduce the count of stopped Children but suppress the right tail much more severely. Requiring a completed close beyond the launch-PHA extreme is too late to be a useful permission rule. These exact rules are rejected; they should not be rescued by threshold tuning.

## 4. What the MA ribbon actually contains

The useful information was not a binary trend label. It was the normalized directional geometry between price and the ribbon.

The strongest all-universe STOP separator was H1 WMA20 on OC2, using directional fast-to-slow span / ATR. Its STOP AUC was:

- 2022: `0.750`
- 2023: `0.699`
- 2024: `0.706`
- 2025: `0.737`
- 2026: `0.752`

Other stable representations included M15 SMA60 on HA midpoint and H4 WMA20 OC2 slope. This supports three observations:

1. H1 20 and M15 60 behave like related elapsed-time horizons; raw line count is not the portable object.
2. WMA improved the directional distance representation, but SMA produced the cleanest extreme full-breach pocket.
3. HA midpoint works, but did not dominate raw close or OC2. A second HA transformation is not automatically superior just because V10 begins from HA.

The within-current-H4 LTF `repair` path was weak and inconsistent. Current band geometry was more informative than trying to narrate a noisy intrabar repair sequence.

## 5. How many lines must be breached?

There is no invariant answer.

- H1 SMA-close 20: crossing 13-19 of the 19 counted lines produced 16 stops in 26 cases (`61.5%` stop rate). The annual stop rates were `66.7%`, `77.8%`, and `50.0%`.
- H1 WMA-OC2 20: the same 13-19 line bucket produced only 9 stops in 37 cases (`24.3%`) and retained a positive mean R.
- M15 SMA-close 60: crossing 40-59 of 59 lines produced 16 stops in 44 cases (`36.4%`), with annual stop rates `28.6%`, `47.4%`, and `27.8%`.
- Intermediate breach buckets were not monotonic. Some deep penetrations still belonged to profitable continuation journeys.

Therefore “N번째 선이 깨지면 추세 종료” is not supported. A defensible state variable needs at least ribbon family, elapsed-time horizon, normalized H4 slope/span, and current LTF deterioration together. Penetration depth alone is a lossy description.

## 6. Economic filter diagnostics

Stable STOP discrimination did not automatically produce a stable trading gate.

The best pooled prior-only 2.5% tail was M15 SMA-OC2 60 health:

- blocked 23 candidates, including 14 stops and 6 positive Children;
- stop count 232 -> 218;
- `+14.71R` pooled;
- L6+ positive-R retention `99.18%`;
- annual delta: `+4.00R`, `+13.76R`, `-3.05R`.

No single feature/tail combination was positive in all of 2024, 2025, and 2026.

A fixed semantic intersection of weak H4 WMA-OC2 20 slope and strong M15 WMA-OC2 60 deterioration was less destructive:

- 20% prior-only tails: blocked 34, including 15 stops and 8 positive Children;
- stops 232 -> 217; maximum stop streak 5 -> 4;
- pooled `+11.30R`; L6+ positive-R retention `98.52%`;
- annual delta: `+4.03R`, `+8.74R`, `-1.47R`.

This is still a post-hoc interaction on consumed evidence and it also fails the all-year sign check. It is not promoted.

## 7. Research decision

1. Reject the tested progression and damage-repair permissions.
2. Retain MA ribbons as a promising state representation, not as a trend label or standalone veto.
3. Do not promote a fixed breached-line count, MA type, price source, or threshold.
4. If this branch continues, freeze one semantic hypothesis before additional evaluation: `weak normalized H4 campaign slope + materially deteriorated M15 ribbon`, with the threshold defined from prior-only era-normalized history.
5. Judge that frozen hypothesis on new chronology or a deliberately held-out slice. Do not continue variant scanning on the same consumed periods and call the winner validation.

## 8. Reproducible artifacts

- Study runner: `research/v10/explore_v10_progression_ma_bands.py`
- Regenerable local output directory: `output/v10_progression_ma_bands_20260921` (removed during repository cleanup)
- Manifest: `V10_PROGRESSION_MA_BAND_MANIFEST.json`
- Progression results: `V10_PROGRESSION_POLICY_SUMMARY.csv`
- Stable feature table: `V10_MA_BAND_STOP_STABILITY.csv`
- Breached-line table: `V10_MA_BAND_BREACHED_LINES.csv`
- Prior-only frontier: `V10_MA_BAND_CAUSAL_QUANTILE_FRONTIER.csv`
- Annual frontier: `V10_MA_BAND_CAUSAL_QUANTILE_BY_YEAR.csv`
- Fixed interaction annual audit: `V10_MA_BAND_FIXED_INTERACTIONS_BY_YEAR.csv`
