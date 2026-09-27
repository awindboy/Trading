# V13 X1 — ECB daily dollar-proxy observation receipt

Date: `2026-09-28`
Status: `CONSUMED DEVELOPMENT / NEGATIVE PROXY RESULT / NO STRATEGY ACTION`
Contract: `../V13_X1_ECB_DOLLAR_OBSERVATION_CONTRACT_20260928.md`
Source: `research/v13/x1_ecb_dollar_observation.py`
Local generated audit: `output/v13_x1_ecb_dollar_20260928/` (not in Git)

## Decision

Adding the *delayed ECB EUR/USD daily reference rate* to H4/H1 HA state did
not improve chronological prediction of a **losing complete Journey**. The
highest predicted-loss group caught no excess repeat losses and gained several
very large winning Journeys. Stop this specific proxy branch; do not turn its
score, sign or rank into a Child veto, exit, position size or EA change. This
does **not** establish that genuine intraday USD data are useless; the ECB
series is bilateral, daily and intentionally delayed.

## Source and causal-quality checks

- Latest GitHub `main` checked before the run: `be88fa2be516963b2dcd196819f9b2fd026b077a`.
- Official ECB series: `EXR.D.USD.EUR.SP00.A` (USD per euro), 1,191 daily
  observations from 2022-01-03 to 2026-08-28; 0 duplicate dates, 0 missing
  values, all 1,191 with observation status `A`.
- ECB normally publishes around 16:00 Central European time on working days.
  Because GOLD# broker-time UTC offset was not established, each decision used
  only the latest ECB observation dated **at least two broker-calendar days
  earlier**. No same-day fixing was used. Weekend/holiday carry-forward was
  allowed. The as-of source age among 4,108 H4 decisions was minimum 2,
  median 2 and maximum 6 days; 24 decision rows exceeded 5 days.
- Before loading any future Journey outcome, the separate X1 feature ledger
  covered all 4,108 HA-8A decision rows, including 966 Journey births, with
  no missing external feature or duplicate `(signal, journey)` key. It used
  541 distinct eligible ECB dates from 2023-12-29 to 2026-08-26.
- The reused GOLD# H4 and HA-8A feature hashes matched their existing V13
  receipts. Reconstructed economic parity was 965 closed Journeys, 3,858
  Children and +8,147.11 idealized GOLD price points. This is **not** actual-
  tick MT5 P/L, nor dollars, nor the official exact-window economic receipt.
- ECB API provides the currently published historical series. This run did
  not audit individual point-in-time revisions/vintages; the conservative
  publication-date lag alone does not prove an old rate was never corrected.

The independent source was registered as S20 in the V13 source-register
addendum *before* evaluating outcomes. ECB dataset and timing references:

- https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A
- https://data.ecb.europa.eu/help/api/data
- https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html

## Frozen target and chronological comparison

Only the first Child's decision features represented each Journey at birth.
The target was whether the *whole* Journey's Baseline-0 Child-sum PnL ended
negative. Previous Journey loss was used only for a repeated-loss diagnostic.
The model family was fixed-penalty logistic regression; the two added ECB
coordinates were normalized one- and five-publication-step changes in
`-log(EUR/USD)`. Train folds contained only Journeys already **closed** before
the first decision of the subsequent test block. No random split, threshold
search or trading action was performed.

Of 965 closed Journeys, 777 received chronological OOF predictions (2024-H2
through cutoff). Of those, 590 lost (`75.9%`); 441 losses followed an already
losing Journey. The high loss frequency alongside positive aggregate points is
why winner size/right-tail preservation must be evaluated together with hit
rate.

| OOF model | Brier ↓ | Log loss ↓ | AUC ↑ | Fixed-bin ECE ↓ |
| --- | ---: | ---: | ---: | ---: |
| Training-fold base rate | 0.18521 | 0.55962 | 0.5032 | 0.04328 |
| H4 morphology + ordered H1 | 0.18706 | 0.56832 | 0.5462 | 0.06762 |
| H4/H1 + delayed ECB EUR/USD | **0.18888** | **0.57319** | **0.5416** | **0.07175** |

The ECB addition worsened Brier by `0.00182` relative to H4/H1, and H4/H1
itself did not beat the simple base rate on Brier. All four chronological
blocks had worse Brier after adding ECB:

| Test block | H4/H1 | + ECB |
| --- | ---: | ---: |
| 2024-H2 (191 Journeys) | 0.17295 | 0.17565 |
| 2025-H1 (168) | 0.22968 | 0.23435 |
| 2025-H2 (178) | 0.16582 | 0.16626 |
| 2026 through cutoff (240) | 0.18422 | 0.18435 |

The year×side Brier difference favored ECB in only two of six slices, both
very slightly; four worsened. The 2025-H1 model was particularly unstable.

## Loss concentration versus right-tail false warnings

The highest predicted-loss 20% contains 156 Journeys for each model. This is
a fixed descriptive rank bucket, **not a proposed veto threshold**.

| Diagnostic | H4/H1 | H4/H1 + ECB |
| --- | ---: | ---: |
| Losing Journeys / 156 | 122 | 120 |
| Winning Journeys / 156 | 34 | 36 |
| Repeated losing Journeys / 441 overall | 89 | 85 |
| Gross winning points in bucket | +1,820.43 | +7,503.85 |
| Gross losing points in bucket | -2,967.88 | -3,764.05 |
| Bucket net points | -1,147.45 | **+3,739.80** |
| >=10-bar Journeys in bucket | 8 | 10 |
| Their net points | +1,031.28 | **+6,710.82** |

The ECB score did not enrich losses: 120/156 = `76.9%` versus `75.9%` in
the whole OOF cohort. It identified 85/441 = `19.3%` of repeat losses with
20.1% of the Journeys. Compared with H4/H1's bucket, 30 Journeys entered
and 30 left. The entered group had **22 losses and 8 winners** but net
`+4,788.67` points; the removed group had **24 losses and 6 winners** and net
`-98.58`. Three entered very large winners contributed `+5,635.66` points
between them. Their eventual long continuation is known only after the fact;
it cannot become a causal exclusion rule.

## Boundaries and next step

This is a negative test of one **daily, bilateral, delayed** dollar proxy, not
of all external-dollar information. Its observations are much slower than H4;
the conservative two-day lag prevents publication leakage but may erase the
effect under investigation. This is consumed-history, idealized-price
evidence; no variant was traded in the MT5 tester. Do not tune lag/periods or
add a dollar sign rule to rescue this result.

If V13 continues external-source research, first obtain a timestamped,
same-broker intraday USD-related series with 2022 warm-up and complete
2024-01-01..2026-08-28 coverage, verify source clock and as-of parity, then
freeze a **new** single-family contract. Do not label EUR/USD as DXY or use
this X1 result as evidence of an H4 dollar-index edge. The official exact-
window real-tick Baseline-0 MT5 receipt and untouched future validation remain
required before economic promotion.

## Reproduction hashes

```text
GOLD# H4:       b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf
HA-8A features: dc2a082cddd16359da8cb518cd535747297beecad521d40821034e0bf543be0d
ECB CSV:        811e60d7937dcac1e8ad45d57d5c3f6492f0ee18452a12bcb32fc34a7cea74d8
X1 features:    b835657f78c34255c14f4187fad6721cfbdcba50c53a6da0a5e45d2fd878673e
```
