# V8-A-N-SLOW Higher-Horizon Extension Probability Research — 2026-09-02

Status: `DEVELOPMENT EVIDENCE / EXTENSION LAYER RETAINED / NO DIRECTION OR PRODUCTION AUTHORITY`
Market: `GOLD#`
Base Git HEAD: `45925b29fbec7d52509652e5787654624ecc0848`
Raw source SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`

## 1. Research question

The current Slow-N onset detector asks:

```text
scale = previous-completed H4 Wilder ATR14
T_onset = 0.25 * scale
P15 = P(reach +/-T_onset within 15m)
fresh75 = previous P15 <75%, current P15 >=75%
```

This research asks whether the same slow H4 scale can support a larger and longer movement-probability layer:

> after a decision, how likely is GOLD to travel a materially larger H4-normalized distance over 60-240 minutes?

A second question is explicitly tested and separated:

> does increasing the horizon and distance make mandatory LONG/SHORT direction materially easier?

No trade P/L, stop/target optimization or 2021 data are used to select the movement target family.

## 2. Target-family screen

Predeclared research grid:

```text
Horizon H = 60 / 120 / 240 minutes
Distance k = 0.50 / 0.75 / 1.00 * previous-completed H4 ATR14
```

For each M5 decision:

```text
H4 block = block containing the decision timestamp
scale = Wilder ATR14 from the immediately previous fully completed H4 bar
T = k * scale
T is constant for the entire H4 decision block
```

The label is direction-blind:

```text
either_hit(H,k) =
    future high >= C0 + T
    OR
    future low <= C0 - T
within H minutes
```

### Annual either-hit base rates

| Horizon | k | 2022 | 2023 | 2024 | 2025 | 2026 YTD |
|---:|---:|---:|---:|---:|---:|---:|
| 60 | 0.50 | 22.20% | 22.57% | 22.80% | 22.96% | 21.20% |
| 60 | 0.75 | 8.99% | 9.98% | 9.38% | 8.38% | 8.02% |
| 60 | 1.00 | 4.23% | 4.83% | 4.39% | 3.60% | 3.77% |
| 120 | 0.50 | 42.00% | 40.55% | 42.11% | 44.73% | 41.45% |
| 120 | 0.75 | 20.94% | 21.06% | 21.39% | 20.48% | 18.96% |
| 120 | 1.00 | 10.71% | 11.62% | 11.03% | 10.06% | 9.87% |
| 240 | 0.50 | 65.53% | 62.67% | 65.06% | 69.38% | 66.54% |
| 240 | 0.75 | 40.46% | 39.09% | 41.26% | 42.10% | 38.38% |
| 240 | 1.00 | 24.70% | 24.27% | 24.87% | 24.51% | 21.90% |

The annual base-rate stability is strong across the whole grid. The main design issue is therefore **useful difficulty**, not calendar drift.

## 3. Target choice for a higher-horizon survival surface

The retained research target is:

```text
T_ext = 0.75 * previous-completed H4 ATR14
```

and one joint survival surface reports:

```text
P60  = P(reach +/-T_ext within 60m)
P120 = P(reach +/-T_ext within 120m)
P240 = P(reach +/-T_ext within 240m)
```

Reason for `0.75`:

- `0.50` becomes very common by 240m (`~63-69%`), so it is less selective as a large-extension definition;
- `1.00` is very rare at 60m (`~3.6-4.8%`), creating sparse high-probability states;
- `0.75` spans a useful survival range:
  - P60 base `~8-10%`;
  - P120 base `~19-21%`;
  - P240 base `~38-42%`;
- 2026 median distance is approximately `30.28p`, materially larger than the current onset target (`~10.09p`).

This is a structural movement choice. No direction accuracy or trade economics were used to select `0.75`.

## 4. Survival-model construction

The extension probe reuses the A2/Slow-N 86-feature causal representation.

Barrier-dependent features are rebuilt using:

```text
barrier = 0.75 * previous-completed H4 ATR14
```

rather than reusing the 0.25-target barrier features.

Four mutually exclusive classes:

```text
class 0: first +/-T_ext hit before 60m
class 1: first hit from 60m through <120m
class 2: first hit from 120m through <240m
class 3: no hit within 240m
```

Therefore:

```text
P60  = P(class0)
P120 = P(class0) + P(class1)
P240 = P(class0) + P(class1) + P(class2)
```

This structurally guarantees:

```text
P60 <= P120 <= P240
```

Training/evaluation discipline:

- chronological evaluation years `2024 / 2025 / 2026`;
- training label must fully resolve before the evaluation boundary;
- strict 240-minute purge for the joint surface;
- Phase-0: outcome-blind `m5_index % 5 == 0` de-overlap;
- Phase-2: outcome-blind `m5_index % 5 == 2` robustness realization;
- 2026 is partial through 2026-08-28;
- 2021 is not opened.

## 5. Extension survival results

### Phase-0

| Horizon | 2024 AUC / fresh75 | 2025 AUC / fresh75 | 2026 AUC / fresh75 |
|---:|---:|---:|---:|
| P60 | .814 / 70.00% N90 | .769 / 68.97% N29 | .777 / 87.10% N31 |
| P120 | .759 / 74.25% N334 | .703 / 67.68% N198 | .718 / 70.59% N102 |
| P240 | .730 / 74.97% N899 | .665 / 68.40% N845 | .661 / 64.64% N461 |

### Phase-2

| Horizon | 2024 AUC / fresh75 | 2025 AUC / fresh75 | 2026 AUC / fresh75 |
|---:|---:|---:|---:|
| P60 | .815 / 77.27% N88 | .770 / 65.52% N29 | .776 / 90.48% N21 |
| P120 | .759 / 75.20% N375 | .702 / 68.20% N217 | .716 / 72.16% N97 |
| P240 | .730 / 73.56% N1006 | .666 / 68.22% N881 | .662 / 63.56% N461 |

Interpretation:

1. `P60` retains strong ranking AUC but fresh75 is sparse because a 0.75-H4-ATR move inside one hour is genuinely rare.
2. `P120` is the best current **central extension coordinate**: useful count, material target distance and moderate ranking power.
3. `P240` has abundant high-probability states but ranking AUC falls materially in 2025/2026.
4. Longer horizon does **not** automatically improve predictability; movement ranking information is diluted as the horizon expands.

Fresh-event identity remains model-realization sensitive. Phase-0/Phase-2 Jaccard:

| Horizon | 2024 | 2025 | 2026 |
|---:|---:|---:|---:|
| 60 | .483 | .381 | .333 |
| 120 | .509 | .531 | .432 |
| 240 | .536 | .622 | .595 |

Do not freeze an extension fresh trigger from one model phase alone.

## 6. Key finding: current Slow-N fresh is already an extension-onset detector

The existing Phase-0 onset fresh75 population (`0.25 H4 ATR / P15`) was evaluated against larger future movements without changing its selection.

### Realized larger movement after current onset fresh75

| Larger target | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| 0.50 H4 ATR within 60m | 71.36% | 71.59% | 68.22% |
| 0.75 H4 ATR within 120m | 62.63% | 58.69% | 56.07% |
| 1.00 H4 ATR within 240m | 54.82% | 51.21% | 48.91% |

Compare unconditional base rates:

```text
0.50 / 60m  ~21-23%
0.75 / 120m ~19-21%
1.00 / 240m ~22-25%
```

Therefore the current 15-minute fresh75 event is not merely identifying a small local burst. It enriches the probability of a much larger volatility episode by roughly 2-3x.

Retained interpretation:

> current Slow-N fresh75 is best treated as an **onset detector**, while the higher-horizon surface estimates **extension / continuation magnitude probability**.

## 7. Does the extension model add information inside current fresh?

The independent higher-horizon movement scores were evaluated only inside the current onset-fresh population.

AUC inside current fresh:

```text
0.50 / 60m:
2024 .569 / 2025 .562 / 2026 .649

0.75 / 120m:
2024 .597 / 2025 .586 / 2026 .557

1.00 / 240m:
2024 .642 / 2025 .548 / 2026 .563
```

The additional discrimination is modest and not uniformly stable.

Interpretation:

- the onset trigger itself already captures much of the expansion state;
- extension probability may still be useful for **holding/target architecture later**;
- current evidence does not justify using extension probability as a hard entry filter.

This matters because the active strategy objective remains **mandatory trading of all fresh events**, not abstention to inflate WR.

## 8. Higher horizon did not solve mandatory direction

Two direct direction architectures were tested.

### A. Reuse movement representation as separate P_UP / P_DOWN models

On higher-horizon fresh events, mandatory direction remained unstable.

Examples:

```text
60m / 0.50:
first-touch accuracy 48.4 / 54.1 / 43.2%

120m / 0.75:
47.8 / 56.7 / 51.3%

240m / 1.00:
48.9 / 60.0 / 53.3%
```

### B. Signed multi-horizon path representation

A new causal signed representation included:

- normalized net movement over 5/15/30/60/120/240/480/1440m;
- efficiency / directional body balance / aggregate CLV;
- signed tick-volume balance;
- current M5 candle geometry;
- M5 Stoch/RSI/MACD/DMI/Bollinger signed state;
- M1 1/3/5/10/15/30m net path, efficiency, CLV, body and signed activity.

It was trained as:

```text
P(first target side = UP | meaningful move resolves)
```

with mandatory LONG/SHORT at inference.

The relationship still failed to transfer consistently. Representative Phase-0 first-touch accuracy:

```text
60m / 0.50:
52.3 / 46.3 / 52.7%

120m / 0.75:
53.8 / 50.0 / 50.0%

240m / 1.00:
55.4 / 41.3 / 55.6%
```

Using the fixed `0.75 H4 ATR` survival-fresh population also failed:

```text
P60 fresh direction:
50.8 / 65.0 / 37.0%

P120 fresh direction:
55.6 / 47.8 / 47.2%

P240 fresh direction:
52.2 / 50.0 / 56.7%
```

Conclusion:

> the hypothesis “direction becomes easy if the movement horizon is lengthened” is falsified on current development evidence.

Do not rescue it by horizon/target cherry-picking.

## 9. Research decision

### Retain

1. Current `0.25 H4 ATR / P15 fresh75` as the provisional **ONSET movement trigger**.
2. Open a separate research-only extension layer:

```text
V8-A-N-SLOW-EXT

T_ext = 0.75 * previous-completed H4 ATR14
P60 / P120 / P240
```

3. Treat `P120` as the central extension coordinate for research, with P60/P240 as short/long context.
4. Preserve the requirement that every onset fresh event remains eligible for mandatory direction; extension probability is not an abstention filter.

### Reject / do not promote

- replacing the onset trigger merely because a longer horizon exists;
- using higher-horizon P_UP/P_DOWN as the current direction engine;
- claiming that longer horizon solves the ~50% direction bottleneck;
- threshold-tuning extension probability from trade outcomes;
- opening 2021.

## 10. Implication for future strategy architecture

If direction is eventually solved, the natural architecture becomes:

```text
Slow-N ONSET
0.25 H4 ATR / P15 fresh75
        |
        +--> mandatory LONG/SHORT direction
        |
        +--> Slow-N EXTENSION
             0.75 H4 ATR
             P60 / P120 / P240
             |
             +--> later holding / runner / target architecture
```

This separates:

- **whether a movement episode is beginning**;
- **which direction to trade**;
- **how far / how long the episode may extend**.

A variable discovered for extension must not automatically become an entry veto.

## 11. Next research order

1. Keep the existing onset N1 population as the mandatory-entry population.
2. Preserve `V8-A-N-SLOW-EXT` as shadow movement context; do not freeze an EXT fresh trigger yet.
3. Resume the main direction bottleneck:
   - full V4-aligned raw-tick extraction for all onset fresh events;
   - exact relative `0001` transfer + -10m placebo;
   - M1 oscillator transition on full tick coverage;
   - BB-B x temporal-transition interaction;
   - native Path Clearance;
   - M1 confirmed-structure recovery/redefinition.
4. Do not do more generic higher-horizon direction-model search unless new information is added.
5. After direction is frozen, explicitly preregister an exit study using EXT probability for holding/runner decisions **without dropping low-EXT onset trades**.
6. Final probability architecture and MT5 surface can be built only after the ONSET/EXT model training protocol is frozen.
7. Keep `GOLD# 2021` locked.

## 12. QA / validation

- raw CSV SHA256 matched the authoritative manifest;
- no 2021 rows were present or opened;
- H4 target scale was constant within every H4 decision block (`max unique ATR per block = 1`);
- joint survival class sums guarantee zero horizon-order violations;
- survival base rates independently reconciled to direct future-excursion counts (maximum difference <0.01 percentage point);
- Phase-0 and Phase-2 were both checked;
- 2026 is explicitly partial through 2026-08-28;
- direction failures are reported rather than rescued by target/horizon selection.

## 13. Reproducibility artifacts

Stored under:

`docs/ea/v8/results/v8_a_n_slow_extension_20260902/`

including:

- annual/quarter target-family base rates;
- Phase-0 binary movement screen;
- current-onset extension realization;
- fixed-0.75 survival model metrics;
- Phase-0/Phase-2 fresh-event Jaccard;
- higher-horizon direction failure tables.


Research-only model coefficients/scalers are stored under:

`config/v8_a_n_slow_extension_probe_20260902/models_h4_075_p60_p120_p240_probe.json`

This pack is a reproducibility probe, not final probability authority.
