# V8-A-N Fresh-High N1 → N4 Research Results — 2026-09-01

Status: `DEVELOPMENT RESEARCH / NO PRODUCTION AUTHORITY`
Market: `GOLD#`
Base Git HEAD: `9dda6ed5e66024296f6485e5a570c675d30319ee`
Reserve: `GOLD# 2021 LOCKED`

## 1. Scope

This study continued directly from:

`V8_A_N_ATR_NORMALIZED_MOVEMENT_RESEARCH_20260901.md`

The research order was:

```text
N1 normalized fresh-high trigger selection
        ↓
N2 mandatory direction engine
        ↓
N3 ATR-consistent SL/TP
        ↓
N4 comparison versus fixed-$10 fresh75 controls
```

The N1 trigger was selected without using LONG/SHORT labels or P/L.

The first N2 rule was frozen from 2024 before opening its 2025/2026 direction results. That rule failed. After this failure, 2024-2026 were explicitly reclassified as consumed normalized-direction development evidence. A second robust/maximin development engine was then built using all three years. It has no independent-validation authority.

No GOLD# 2021 data were used.

---

## 2. N1 — normalized fresh-high trigger selection

Candidates:

```text
previous P15(k ATR) < 75%
current P15(k ATR) >= 75%

k = 1.25 / 1.50 / 2.00
```

Selection criteria were movement-only:

- P15/P30/P60 realized normalized movement;
- count and monthly stability;
- trigger spacing/clustering;
- causal ATR/barrier distribution;
- session/context distribution;
- probability/rank shape;
- practical frequency.

No direction label or trade result was used.

### 2.1 Movement realization

Authoritative normalized movement table:

| k | Year | N | P15 hit | P30 hit | P60 hit |
|---:|---:|---:|---:|---:|---:|
| 1.25 | 2024 | 1958 | 81.38% | 95.18% | 99.49% |
| 1.25 | 2025 | 2230 | 79.03% | 94.43% | 99.28% |
| 1.25 | 2026 | 1690 | 77.09% | 93.78% | 98.86% |
| 1.50 | 2024 | 809 | 81.64% | 93.92% | 98.88% |
| 1.50 | 2025 | 834 | 77.85% | 91.77% | 98.18% |
| 1.50 | 2026 | 551 | 80.04% | 93.77% | 97.80% |
| 2.00 | 2024 | 180 | 80.90% | 91.01% | 97.75% |
| 2.00 | 2025 | 151 | 73.29% | 88.36% | 97.26% |
| 2.00 | 2026 | 131 | 75.19% | 87.60% | 98.45% |

2026 is through the available 2026-08-28 history and is therefore a partial calendar year.

### 2.2 Frequency / clustering

#### 1.25 ATR

```text
median trigger spacing:
2024 70m
2025 70m
2026 60m

next trigger <=60m:
~47.6% / 47.5% / 52.1%

active-day median trigger count:
7 / 8 / 10
```

This is very high frequency, but approximately half of triggers occur within one hour of a previous trigger. It therefore repeatedly samples the same volatility episode.

#### 1.50 ATR

```text
N:
2024 809
2025 834
2026 551 through Aug-28

monthly mean:
67.4 / 69.5 / 68.9

median trigger spacing:
362.5m / 327.5m / 380m

next trigger <=60m:
30.4% / 25.9% / 23.4%

active-day median trigger count:
3 / 3 / 3
```

This retains useful trading frequency while substantially reducing repeated sampling of one episode.

Median consensus ranks were approximately 99th percentile, so these are genuinely unusual movement states.

#### 2.00 ATR

```text
median trigger spacing:
1615m / 2310m / 1570m

active-day median:
1 / 1 / 1
```

The sample becomes too sparse for the project's high-frequency objective and for robust direction research.

### 2.3 N1 decision

**Freeze `1.50 ATR fresh-75` as N1.**

Exact movement trigger:

```text
scale = causal pre-decision M5 Wilder ATR14
barrier = 1.50 * scale

previous completed M5 P15_1.50ATR < 75%
current completed M5 P15_1.50ATR >= 75%
=> N1 movement trigger
```

Reasons:

1. P15 movement realization remains ~78-82% across years.
2. P30/P60 realization remains extremely high.
3. signal count is large enough for automation and research;
4. monthly cadence is much more stable than fixed-$10 fresh75;
5. clustering is materially lower than 1.25ATR;
6. 2ATR is unnecessarily sparse;
7. selection was made without directional P/L.

N1 is now frozen for the next direction research.

---

## 3. N2 — first direction freeze and falsification

Direction target for the first N2 experiment:

```text
among N1 triggers,
which side reaches +/-1.50 ATR first within 60 minutes?
```

Same-M1-bar two-sided hits are ambiguous and excluded from direction-label accuracy.

Resolved direction populations:

```text
2024 797 / 809
2025 814 / 834
2026 538 / 551
```

The direction target was approximately balanced between UP and DOWN.

### 3.1 Initial 2024-only rule

The first rule was created using 2024 only.

LONG votes:

```text
1. trailing 5m M1 range / ATR >= 2.841
2. completed H4 RSI7 3-bar slope >= -1.686
3. M5 MFI14 <= 52.21
4. completed H4 wick-skew >= -0.157
5. completed H1 range / H1 ATR >= 0.788

LONG if >=3 votes
otherwise SHORT
```

2024 discovery was approximately 59.6%.

It was then frozen and opened unchanged:

| Year | N resolved | Direction accuracy |
|---|---:|---:|
| 2024 | 797 | 59.60% |
| 2025 | 814 | **48.28%** |
| 2026 | 538 | **49.44%** |

### 3.2 Decision

The 2024-only N2 rule is rejected.

Do not adjust its thresholds to rescue 2025/2026.

This is direct evidence that a seemingly stable 2024 indicator combination did not transfer to later normalized-trigger years.

At this point 2025/2026 normalized direction outcomes became consumed development evidence.

---

## 4. N2-R1 — robust development engine after validation consumption

After the first N2 falsification, a new research objective was explicitly opened:

> find a deterministic rule whose **minimum** direction accuracy is as stable as possible across the already-consumed 2024/2025/2026 development years.

This is post-hoc development, not independent validation.

### 4.1 Search space

The normalized N1 population was described using hundreds of causal features from:

- M1 activity/price pressure;
- M5/M15/H1/H4 candle geometry;
- completed and partial HTF state;
- EMA/HMA/momentum/efficiency;
- RSI/Stochastic/MFI/CCI/MACD/Bollinger and composites;
- tick-volume/activity features;
- previous-day location;
- time/session context;
- V8-A-N probability shape.

Regularized broad logistic models showed poor chronological transfer. Simple deterministic maximin voting was more stable.

### 4.2 N2-R1 rule

LONG votes:

```text
1. H4 signed-volume(3) >= +0.119909
2. H4 ROC1 >= -0.075533%
3. M1 240m move-count imbalance <= +0.042017
4. trailing 5m range / M5 ATR >= 2.661190
5. V8-A-N P60_1.50ATR >= 0.987684
6. H4 Bollinger width / H4 ATR <= 3.514138
7. M15 body / M15 ATR <= 0.272129

LONG if >=5 votes
otherwise SHORT
```

Development accuracy:

| Year | N resolved | Accuracy |
|---|---:|---:|
| 2024 | 797 | **57.34%** |
| 2025 | 814 | **57.62%** |
| 2026 | 538 | **57.43%** |

The primary positive property is stability, not absolute accuracy.

### 4.3 Interpretation

The engine mixes:

- broad H4 directional/activity state;
- long-window M1 move imbalance;
- immediate expansion magnitude;
- high normalized movement persistence;
- M15/H4 exhaustion/regime information.

It is not promoted as a proven trading theory.

Because the rule was selected using all three years, its ~57.5% result is a development ceiling estimate only.

---

## 5. N3 — preregistered ATR-consistent risk/payoff family

After fixing N2-R1 for development comparison, the following family was tested without adding intermediate TP values:

```text
entry = next M5 open after N1 trigger
direction = N2-R1
risk = 1.0 * trigger ATR

A: SL 1.0 ATR / TP 1.0 ATR
B: SL 1.0 ATR / TP 1.25 ATR
C: SL 1.0 ATR / TP 1.50 ATR

primary horizon = 60m
if neither barrier is hit, close at the 60m observed price

same-M1-bar SL+TP ambiguity:
conservative SL-first treatment
```

The 60m time-stop rate was near zero, so a 480m sensitivity run was almost identical.

### 5.1 Results

#### SL 1ATR / TP 1ATR

| Year | N | WR | Avg winner | EV | PF |
|---|---:|---:|---:|---:|---:|
| 2024 | 809 | 54.64% | 1.00R | +0.093R | 1.20 |
| 2025 | 834 | 54.80% | 1.00R | +0.096R | 1.21 |
| 2026 | 551 | 55.72% | 1.00R | +0.114R | 1.26 |

Stable positive gross expectancy, but average winner is not meaningfully above 1R.

#### SL 1ATR / TP 1.25ATR

| Year | N | WR | Avg winner | EV | PF |
|---|---:|---:|---:|---:|---:|
| 2024 | 809 | 49.94% | 1.25R | +0.124R | 1.25 |
| 2025 | 834 | 49.04% | 1.25R | +0.103R | 1.20 |
| 2026 | 551 | 51.18% | 1.25R | +0.153R | 1.31 |

This has better expectancy than 1R, but 2024/2025 fall just below the project WR>=50% requirement.

#### SL 1ATR / TP 1.50ATR

| Year | N | WR | Avg winner | EV | PF |
|---|---:|---:|---:|---:|---:|
| 2024 | 809 | 45.36% | ~1.50R | +0.134R | 1.25 |
| 2025 | 834 | 46.16% | ~1.49R | +0.150R | 1.28 |
| 2026 | 551 | 47.55% | 1.50R | +0.191R | 1.37 |

Gross expectancy improves, but WR is clearly below the required 50%.

### 5.2 One-position sensitivity

Because most trades resolve quickly, enforcing one-position-only changed counts and metrics only marginally.

Therefore the main conclusion is not an artifact of overlapping positions.

### 5.3 N3 decision

None of the preregistered N3 variants simultaneously satisfies:

```text
WR >=50% in every studied year
AND
average winner meaningfully >1R
```

Do not insert 1.10/1.15/1.20 ATR targets immediately to rescue the result.

The correct next bottleneck is direction/execution information, not fine-grained TP optimization.

---

## 6. Execution-cost warning

The M1 proxy uses bar OHLC and is not an MT5 real-tick execution result.

More importantly, a 1ATR risk unit can be small in quiet years.

Using the recorded GOLD# M1 spread field and a 0.01 price point as a rough entry-spread proxy:

| Year | Median spread price | Median spread / 1ATR risk | 75th pct | 95th pct |
|---|---:|---:|---:|---:|
| 2024 | ~$0.18 | **13.7% R** | 19.8% | 34.1% |
| 2025 | ~$0.17 | **6.1% R** | 8.8% | 15.6% |
| 2026 | ~$0.24 | **4.9% R** | 7.0% | 13.3% |

This is only a stress proxy, not an exact transaction-cost deduction.

However, it shows a new structural issue:

> volatility normalization stabilizes the movement target, but a small ATR-denominated stop can make execution cost a much larger fraction of risk in quiet regimes.

A simple subtraction of one median spread from gross EV would nearly erase the 2024 N3 edge.

Therefore no V8-A-N trading candidate may be promoted without real-tick fill-relative testing.

Possible later research may consider a minimum executable risk floor or larger normalized risk scale, but that must be opened as a new predeclared experiment rather than used to rescue N3 retroactively.

---

## 7. N4 — comparison with fixed-$10 fresh75 controls

The strongest existing fixed-$10 development control remains:

```text
fresh fixed-$10 P15 75-cross
existing fixed-$10 direction engine
SL $10
TP $13
nominal payoff ~1.30R
```

Comparison on the common 2025/2026 development years:

| Strategy | 2025 WR | 2025 EV | 2026 WR | 2026 EV |
|---|---:|---:|---:|---:|
| fixed fresh75, 1R | 59.65% | +0.193R | 58.87% | +0.177R |
| fixed fresh75, ~1.30R | **52.63%** | **+0.207R** | **52.07%** | **+0.198R** |
| normalized 1.5ATR N1 + N2-R1, TP1ATR | 54.80% | +0.096R | 55.72% | +0.114R |
| normalized N1 + N2-R1, TP1.25ATR | 49.04% | +0.103R | 51.18% | +0.153R |
| normalized N1 + N2-R1, TP1.50ATR | 46.16% | +0.150R | 47.55% | +0.191R |

Current verdict:

- **movement layer:** normalized V8-A-N is clearly more portable;
- **trigger cadence:** normalized 1.5ATR is much more stable and abundant across regimes;
- **direction layer:** current normalized direction engine is weaker than the old fixed-$10 development engine;
- **combined trading result:** the current normalized strategy does not yet beat the fixed-$10 $10/$13 development control on the project's joint WR/payoff criterion;
- **cost sensitivity:** normalized 1ATR risk is materially more exposed to spread in low-volatility regimes.

Therefore V8-A-N is retained, but the complete normalized strategy is **not promoted**.

---

## 8. Main research conclusion

The normalized research did not fail.

It isolated the actual bottleneck.

```text
V8-A-N movement prediction:
strong / stable / retained

N1 fresh 1.50ATR movement trigger:
strong / high precision / frozen

OHLC + indicator direction:
only ~57.5% robust development accuracy

simple ATR 1/1.25/1.5 payoff family:
positive gross expectancy
but no variant satisfies both WR>=50% and winner>1R across all years

execution cost:
material concern in quiet ATR regimes
```

The next useful work is **not** to search 1.17ATR or 1.22ATR TP.

The next useful work is to improve direction using genuinely new causal information on the already-frozen N1 population.

---

## 9. Next research direction

Keep N1 frozen:

```text
1.50 ATR fresh P15 75-cross
```

Next N2 research should prioritize information that was not fully represented in the broad OHLC/indicator tournament:

1. raw XM tick/quote microstructure immediately before the trigger;
2. bid/ask update imbalance;
3. quote-arrival acceleration;
4. spread expansion/tightening;
5. sub-minute persistence/reversal;
6. if available later, CME GC centralized volume/order-flow;
7. macro-event surprise/context as a separate information-source branch.

The test should compare trigger-local features against shifted placebo windows.

Do not change N1 while researching N2.

Do not reopen N3 until direction or execution information improves materially.

---

## 10. Evidence status

```text
N1:
frozen development trigger

N2 initial 2024-only:
falsified

N2-R1:
robust post-hoc development engine / no validation authority

N3:
predeclared simple payoff family completed / no dual-criterion winner

N4:
normalized complete strategy currently inferior to fixed-$10 1.30R development control

2024-2026:
consumed normalized direction/economics development evidence

2021:
LOCKED / UNTOUCHED
```

No production authority exists.

---

## 11. Result artifacts

Stored under:

`docs/ea/v8/results/v8_a_n_n1_n4_20260901/`

Important files:

- `n1_trigger_structural_comparison.csv`
- `n1_monthly_counts_context.csv`
- `n1_frozen_k1.50_trigger_ledger.csv`
- `n2_initial_2024_rule_spec.csv`
- `n2_initial_rule_validation.csv`
- `n2_r1_robust_development_rule_spec.csv`
- `n2_r1_direction_metrics.csv`
- `n2_r1_resolved_direction_ledger.csv`
- `n3_atr_exit_60m_results.csv`
- `n3_one_position_sensitivity.csv`
- `n3_entry_spread_risk_proxy.csv`
- `n3_spread_cost_stress_proxy.csv`
- `n4_strategy_comparison.csv`
