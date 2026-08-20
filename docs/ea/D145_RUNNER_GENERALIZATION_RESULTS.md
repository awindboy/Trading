# D-145 Runner Generalization Results

Date: 2026-08-21
Research build: `1.92R1L7`
Phase: `RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT`
Strategy authority: **NONE**
Baseline strategy semantics: **D134 execution core unchanged**
2021: **KEEP UNTOUCHED**

## Research question

D-145 did not optimize a fixed TP. It asked:

> Given the same valid actual Fill, why does one market state produce only a local ~1R reaction while another produces 2R or more directional delivery?

Comparison:

```text
continuation actual Fill
-> +1R before SL?
-> among +1R successes: +2R before SL or exhaust before +2R?
```

This separates:

```text
A. Entry survival = Fill -> +1R
B. Winner continuation = +1R -> +2R+
```

## Evidence panel and source identities

| File | Scope used | SHA-256 |
|---|---|---|
| `GOLD23.csv` | GOLD 2023 | `8154d3eb5665e0ba28594406de07f4655fe2e4a45b21afc0f1a30a8aa6f75d09` |
| `GOLD24.csv` | GOLD 2024 segment | `e944dbf13e001fbf190073e121c1d74b88be72db0da2e026cf18dc1f47de4b96` |
| `GOLD(5).csv` | GOLD 2025 | `6b01d742205c1fe3910891af11083400fba768ad70c2e60c7ae30670ab2b2d09` |
| `BTCUSD(3).csv` | BTCUSD 2025 | `00d896c1971bbe028d7f14f9757d20516ac4759767c0a4c25cb7efa8544163c8` |
| `SILVER(5).csv` | SILVER 2025 | `0c8f1fc470d3f7e35c9c780fb8e996599b5c5a69c45e9778698c8947797a7774` |
| `CADJPY(5).csv` | CADJPY 2025 | `bae8cb6151dea6308e5759341d3c0d2ccdff05ee8dbb56c3fbc279c3651d026e` |

`GOLD24.csv` contains an appended prior GOLD-2023 run followed by GOLD-2024. The 2023 portion matches the separate 2023 source; only the 2024 segment is counted as GOLD-2024 evidence.

## Exact-tick outcome panel

Continuation-only:

| Market-year | Fill | +1R | +2R | +3R | P(+2R | +1R) |
|---|---:|---:|---:|---:|---:|
| GOLD 2023 | 64 | 35 | 27 | 22 | 77.1% |
| GOLD 2024 | 52 | 24 | 17 | 10 | 70.8% |
| GOLD 2025 | 51 | 30 | 20 | 16 | 66.7% |
| BTCUSD 2025 | 114 | 54 | 40 | 34 | 75.5%* |
| SILVER 2025 | 45 | 18 | 7 | 6 | 38.9% |
| CADJPY 2025 | 111 | 30 | 18 | 10 | 60.0% |

`*` One BTCUSD +1R success is right-censored for +2R and is excluded from the comparable denominator, so BTC comparable +1R denominator is 53.

All six:

```text
continuation fills = 437
+1R successes = 191
resolved +1R successes with comparable +2R outcome = 190
+2R successes = 129
P(+2R | +1R) = 67.9%
```

This pooled rate is descriptive, not a fixed-2R authorization.

## Entry survival remains unsolved

2025 cross-market continuation:

| Symbol | Fill | +1R | Fill -> +1R |
|---|---:|---:|---:|
| GOLD | 51 | 30 | 58.8% |
| BTCUSD | 114 | 54 | 47.4% |
| SILVER | 45 | 18 | 40.0% |
| CADJPY | 111 | 30 | 27.0% |
| **Total** | **321** | **132** | **41.1%** |

Therefore the current Entry architecture does not satisfy the final >=50% realized win-rate requirement across markets.

## Strongest surviving runner relationship — M30 maturity at +1R

`one_r_m30_range_progress` measures scenario-direction position inside current M30 protected-to-external range:

```text
protected = 0
current directional external = 1
```

Lower progress means less of the current directional M30 structure has been consumed.

Median progress among +1R successes with a valid comparable M30 range:

| Market-year | Exhaust before +2R | +2R runner |
|---|---:|---:|
| GOLD 2023 | 1.061 | 0.691 |
| GOLD 2024 | 0.867 | 0.644 |
| GOLD 2025 | 0.918 | 0.796 |
| BTCUSD 2025 | 0.955 | 0.788 |
| SILVER 2025 | 0.946 | 0.724 |
| CADJPY 2025 | 0.770 | 0.565 |

Consistency:

```text
6 / 6 market-year aggregates
11 / 11 comparable market-year x direction cells

runner progress < exhaust progress
```

Coverage:

```text
resolved +1R conditional population = 190
valid comparable M30 scenario-direction range = 147
```

Missing M30 range states are not imputed or converted to a pass/fail state.

## Supporting relationship — remaining M30 room / actual risk

At +1R, median current-price-to-M30-external distance divided by actual Fill-to-SL risk:

| Market-year | Exhaust before +2R | +2R runner |
|---|---:|---:|
| GOLD 2023 | -0.05R | 1.31R |
| GOLD 2024 | 0.62R | 1.62R |
| GOLD 2025 | 0.23R | 0.95R |
| BTCUSD 2025 | 0.17R | 0.80R |
| SILVER 2025 | 0.60R | 1.21R |
| CADJPY 2025 | 0.87R | 2.84R |

This is useful supporting evidence but is not a pure market-state variable because the denominator is trade risk.

## Cross-market hypothesis pruning

The following did not survive strongly enough to become primary runner variables:

```text
M30 net directional advance
FVG -> Fill elapsed time
FVG -> Fill favorable displacement
simple latest-12 M30 progression
simple PB count
time-to-1R / 1R speed
M1 same-direction continuation
standalone M30 leg-expansion rule
```

They reversed or weakened by market/year/direction.

## Path cleanliness warning

Across all six market-year aggregate cells, eventual +2R runners had higher median adverse excursion before first +1R than the later-exhausting group.

Do not interpret this as `high MAE is good`.

The correct negative conclusion is:

```text
fast +1R != generally better runner
low pre-1R MAE != generally better runner
straight-line path != generally better runner
```

A clean-path quality filter can remove genuine runners.

## M30 maturity is not an Entry filter

Fill-time M30 range progress does not show a stable relationship between `<1R failure` and `+1R success` across the same markets.

Therefore:

```text
M30 maturity @ +1R
= continuation-state variable

M30 maturity
!= proven Entry authorization variable
```

Do not use it to repair the 41.1% 2025 cross-market Fill-to-1R result.

## Working interpretation

Best current model:

```text
valid Root/FVG Entry
        |
        v
local reaction / Entry survival
        |
       +1R
        |
        v
current M30 protected -> external delivery maturity
        |
        +-- mature / near external
        |      -> local reaction may exhaust before another full R
        |
        +-- meaningful directional range remains
               -> another full R of delivery is more likely
```

This is still descriptive. It does not prove that current M30 external is itself causal.

## Not authorized

D-145 does not authorize:

```text
fixed 1R TP
fixed 2R TP
progress < X hold rule
remaining-room > X R hold rule
M30 maturity Entry veto
M30 expansion score
quality-score combination
direction-specific threshold
new strategy authority
```

No D-145 result changes `AGENTS.md` or `EA_SPEC.md`.

## Next

D-146 tests whether post-+1R M30 structure evolution explains why mature-state exceptions still run and why room-rich states sometimes fail.

See `docs/ea/D146_CONTINUATION_STATE_AUDIT.md`.
