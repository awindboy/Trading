# V8-A-N N2 M1 Shadow Research Result

Date: 2026-09-02  
Status: **DEVELOPMENT EVIDENCE ONLY / NOT PROMOTED**  
Population: frozen N1 = 1.50ATR fresh P15 75-cross, GOLD#, 2024-2026  
2021: **UNTOUCHED**

## 1. Question

Does completed M1 chart information add genuinely useful short-horizon direction information for the frozen N1 population, especially between M5 context and exact-decision raw tick structure?

N1 and N2-R1 were not changed.

## 2. Causality

All M1 features use only bars with `M1 bar_start < decision`.

No future M1 bar is used. Confirmed M1 swing pivots require two completed right-side bars before they can enter the structure state.

The V4 raw-tick alignment audit had already passed before this study.

## 3. Predefined M1 questions

The M1 layer was treated as a separate market-information layer rather than duplicating many standard indicators.

- `M1_RECENT_DIR`: majority direction of completed 1m / 2m / 3m net movement.
- `M1_PRESSURE`: majority of latest body, CLV, wick balance, 3-bar body sum, and 3m displacement.
- `M1_STRUCTURE`: majority of causal confirmed swing-high progression, swing-low progression, and close relative to the midpoint of the latest confirmed swing high/low.
- `M1_SWEEP_RECLAIM`: last completed M1 bar versus the preceding 10-minute high/low range.
- `M1_STOCH`: completed M1 Stochastic 14,3,3 K versus D.
- `M1_FASTSLOW`: EMA3/EMA8 relation plus causal slopes.
- `M1_EXPANSION`: recent 3m average range versus the preceding 9m average range; context only.

## 4. M1 standalone result

M1 by itself is **not** a general direction engine.

Approximate pooled accuracies:

- M1 recent direction: 49.6%
- M1 pressure: 49.8%
- M1 structure: 51.5%
- M1 sweep/reclaim: 50.5%
- M1 stochastic: 48.4%
- M1 EMA3/8 fast-slow: 50.2%

Therefore the result does **not** justify an M1-majority voter or another generic indicator ensemble.

## 5. Broad finding: M1 structure conditions N2-R1 quality

`M1_STRUCTURE == N2-R1 direction`:

- N = 832
- pooled N2 accuracy = 59.86%
- 2024 = 60.07%
- 2025 = 60.12%
- 2026 = 59.15%

When M1 structure disagrees with N2-R1:

- N = 1010
- pooled N2 accuracy = 55.35%
- 2024 = 55.42%
- 2025 = 53.78%
- 2026 = 57.49%

The agreement subset is not a label-imbalance artifact: pooled `label_up` is about 50.5%.

Quarterly result for the agreement subset is above 50% in all 11 available quarters, although the amount of uplift versus baseline varies by quarter.

Interpretation: M1 confirmed structure is weak alone but appears useful as an **N2 confidence/context layer**.

## 6. Main cross-scale synchronization finding

Let `D` be the completed M5 Stochastic direction (`K>D => LONG`, otherwise SHORT).

The previously found raw-tick relation `0001` means, relative to D:

- NET: opposite D
- MOVE: opposite D
- CLV: opposite D
- last RUN: same as D

This is a late raw-tick run reversal toward the M5 Stochastic direction while slower tick measures still point against it.

### 6.1 Existing tick relation alone

`M5 Stoch D + tick 0001 -> D`

- N = 175
- 2024 = 63.38%
- 2025 = 68.75%
- 2026 = 62.50%
- pooled = 65.14%

### 6.2 Add M1 recent price state

Require completed M1 recent direction (majority 1m/2m/3m net movement) to still be **opposite D**:

- N = 117
- 2024 = 66.04%
- 2025 = 70.00%
- 2026 = 62.50%
- pooled = 66.67%

The corresponding 10-minute shifted tick placebo with the same current chart condition was only 38.18% pooled.

This supports the interpretation that the aligned tick event contains trigger-local information rather than merely duplicating a broad regime.

### 6.3 Add M1 Stochastic synchronization

Require completed M1 Stochastic to be **same direction as M5 Stochastic D**:

- N = 57
- 2024 = 71.43%
- 2025 = 72.73%
- 2026 = 71.43%
- pooled = 71.93%

The corresponding shifted-tick placebo was 47.12% pooled.

This was the top 2024 result among the constrained symmetric `M1 state × 4-bit tick pattern` family with the applied sample floors, and it transferred in the same direction to 2025 and 2026.

A family-wise within-study permutation audit gave approximately `p=0.0010` for the observed minimum annual accuracy. This is useful internal multiplicity evidence, **not independent validation**, because 2024-2026 are already consumed development data and the preceding tick research influenced the hypothesis space.

### 6.4 Stronger transition subset

If M1 Stochastic was opposite M5 Stochastic around three minutes earlier and is now aligned with it, while tick relation is `0001`:

- N = 40
- pooled = 75.0%
- 2024 = 76.92%
- 2025 = 70.59%
- 2026 = 80.00%

This is mechanistically attractive but too small for promotion.

## 7. Working market interpretation

The strongest current pattern is not ordinary multi-timeframe agreement.

It is closer to:

```text
M5 Stochastic direction = D
        ↓
M1 price remains in a short pullback / counter-move
        ↓
M1 oscillator is already synchronized with D
        ↓
slower raw-tick NET/MOVE/CLV still point against D
        ↓
the latest raw-tick RUN flips to D
        ↓
D has unusually high first-hit probability
```

This is consistent with a **pullback-ending / re-synchronization** hypothesis.

The useful information appears to be the *temporal ordering* of disagreement and re-alignment, not a generic majority vote.

## 8. Development-only trusted-state hierarchy

A simple research hierarchy was evaluated without changing N1:

1. If causal M1 structure and N2-R1 agree, use N2-R1.
2. If they disagree but the `M5 Stoch + tick 0001` synchronization event is present, use the M5 Stoch/tick direction.
3. Otherwise classify the state as unresolved for this high-confidence subset.

Result:

- N = 905
- coverage of all N1 = 42.11%
- pooled direction accuracy = 60.44%
- 2024 = 60.18%
- 2025 = 60.98%
- 2026 = 60.00%
- mean frequency ≈ 28.3 events/month

For comparison, N2-R1 on exactly the same trusted population was 59.12%.

This is a meaningful development improvement, but it is still constructed on consumed data and is **not production authority**.

## 9. What failed / what not to do

- Do not create an M1 majority-vote engine. M1 standalone voters are near 50%.
- Do not add M1 RSI/MACD/MA/Stoch as many independent votes merely to increase voter count.
- Do not optimize M1 lookbacks or Stochastic parameters now.
- Do not use 2021 to promote this discovery.
- Do not reopen N3 exit tuning yet solely from this development result.
- Do not promote the 75% N=40 subset.

## 10. Research decision

M1 should be retained, but its role is now clearer:

- **M5:** broader short-horizon context.
- **M1:** causal micro-structure and transition state.
- **raw tick:** final local sequencing / re-synchronization evidence.

The next valuable experiment is not another indicator scan. It is a frozen shadow probe that explicitly tracks the time sequence:

`M5 direction -> M1 counter-move -> M1 structure/oscillator transition -> raw-tick last-run flip`.

The new M1 findings are strong enough to justify that focused experiment, but not strong enough to update production or use the 2021 reserve.
