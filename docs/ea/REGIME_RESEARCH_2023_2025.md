# Regime Research 2023–2025

Last updated: 2026-08-19
Status: ACTIVE DEVELOPMENT-SET RESEARCH / NO STRATEGY AUTHORITY
Baseline: Mentor deterministic V1 / build 1.91 / `ROOT_OB_DISTAL_20`

## 1. Research protocol

This is the durable ledger for regime-feature discovery. Favorable **and unfavorable** experiments are recorded so multiple-testing and backtest-overfitting risk remain visible.

Dataset roles are frozen:

```text
2023–2025 = Development / Research set
2022      = SEALED first OOS validation
2021      = preferred final untouched confirmation if later available
```

Do not inspect or tune against 2022 before a regime definition is explicitly frozen. If a frozen model is changed after viewing 2022, 2022 is no longer OOS.

No result in this file changes `AGENTS.md` or baseline EA semantics. All feature snapshots must use only information causally available at the research snapshot time.

## 2. Data provenance and calculation QA

### 2023–2024 raw ledger

Current uploaded copy:

`mentor_v1_structure_events(20260819-094816).csv`

```text
rows = 442,722
SHA-256 = 16be6cc44e57dadd9e32250d3e8df9cd1de4e14575a55c0732bc3427a237744e
```

The hash is identical to the 2023–2024 ledger used by the earlier strategy-edge audit.

The current reconstruction exactly reproduces the previously recorded clean outcomes:

| Year | Trades | Wins | Net R | Mean R/trade |
|---|---:|---:|---:|---:|
| 2023 | 70 | 23 | +44.94R | +0.642R |
| 2024 | 55 | 5 | -35.56R | -0.646R |

Continuation-only attribution also reproduces the prior audit:

```text
2023: 64 trades / +48.31R
2024: 48 trades / -28.45R
```

The known `FILLED_AFTER_STRATEGY_CANCELLATION` contaminated trade is excluded. Tester-end open positions are not treated as closed outcomes.

### 2025 raw ledger

Previous audit provenance:

```text
mentor_v1_structure_events(20260818-165949).csv
rows = 234,277
SHA-256 = 1bd119c4d3aea9ab759a24541de71be01d0379fa948927bede2a1dae5b9d7b65
```

That raw file was not available in the current runtime. Therefore previously recorded 2025 results are preserved, but newly introduced feature formulas in sections 5–10 are **not claimed as 2025-validated** until the raw ledger is re-run.

## 3. Prior-session discoveries that were not yet committed

### R-001 — 12-wave progression + 72h stability

Definition:

```text
scope = EXTERNAL_CONTINUATION
latest 12 confirmed M30 waves
M30 directional progression >= 60%
M30 PROTECTED_BREAK during prior 72h = 0
```

Previously recorded development-set attribution:

```text
52 trades / 18 wins / 34.6%
Total = +46.81R
Mean = +0.90R/trade
Max DD ≈ -6R
Longest losing streak = 4

2023: 30 trades / +40.28R
2024:  9 trades /  +5.27R
2025: 13 trades /  +1.27R
```

This was encouraging but retained an arbitrary clock-window threshold.

### R-002 — 72h protected-break churn BAD-regime evidence

Previously recorded:

```text
M30 PROTECTED_BREAK >= 2 during prior 72h

2023:  4 trades / -0.28R
2024:  5 trades / -5.00R
2025: 15 trades / -15.00R

Total = 24 trades / 1 win / ≈ -20.3R
```

Interpretation: repeated M30 protected breaks are a plausible quantitative representation of structural churn. This is evidence, not a veto rule.

### R-003 — `M30_CLEAN_PERSISTENT`

Clock time was removed and the state was defined only from M30 structure:

```text
scope = EXTERNAL_CONTINUATION
window = latest 12 confirmed M30 waves

LONG success:
new HIGH > previous HIGH
or new LOW > previous LOW

SHORT success:
new HIGH < previous HIGH
or new LOW < previous LOW

progression =
direction-consistent same-side comparisons
/ all same-side comparisons

required progression >= 2/3

M30 STRUCTURE_PROTECTED_BREAK
inside the same 12-wave span <= 1
```

State vocabulary:

```text
M30_CLEAN_PERSISTENT
UNKNOWN
```

Previously recorded 2023–2025 development-set result:

```text
36 trades / 15 wins / 41.7%
Total = +55.32R
Mean = +1.54R/trade
Max DD ≈ -6R
Longest losing streak = 6

2023: 21 trades / +46.93R
2024:  8 trades /  +2.82R
2025:  7 trades /  +5.58R

positive quarters = 8
negative quarters = 2
```

This is currently the strongest **three-year** regime discovery. It remains research-only because it was discovered on the Development Set.

## 4. Strict causal reconstruction — PLAN-freeze snapshot

For all new feature work, the research snapshot is fixed to the scenario `PLAN` freeze time. Only M30 objects with `available_at <= plan_frozen_at` are used.

This stricter reconstruction of the same conceptual `M30_CLEAN_PERSISTENT` state gives:

```text
31 trades / 11 wins / 35.5%
Total = +47.90R
Mean = +1.55R/trade
Max DD = -8.17R
Longest losing streak = 8

2023: 21 trades / +47.22R
2024: 10 trades / +0.69R
```

Direction split:

```text
2023 LONG  = +9.14R
2023 SHORT = +38.07R
2024 LONG  = +1.32R
2024 SHORT = -0.64R
```

So the state is positive by year, but the strict reconstruction is not uniformly positive by direction. It also remains tail-dependent: the top three winners produce about 53% of all positive R in this 31-trade subset.

The exact snapshot epoch used in the previous session was not durably recorded. From this document onward, `PLAN freeze` is the canonical discovery snapshot because it is earlier and unambiguously causal.

Coverage:

```text
clean continuation trades = 112
12-wave M30 feature context available = 111
M30 owner-maturity context available = 101
```

## 5. R-004 — Persistence strength and structural churn

### 5.1 Directional progression distribution

The progression relationship is the clearest cross-year structural pattern found so far.

```text
progression <= 0.50
44 trades / 6 wins / -27.80R
2023 = -4.29R
2024 = -23.51R
Max DD = -28.78R
Longest losing streak = 11
positive quarters = 0 / 8

progression > 0.70
20 trades / 6 wins / +28.89R
2023 = +28.26R
2024 = +0.64R
Max DD = -4.17R
Longest losing streak = 4
```

A descriptive Fisher exact comparison of `progression <= 0.50` versus higher progression gives approximately `p = 0.042`. Because trades are not independent and multiple features were inspected, this is supporting evidence only.

**Research judgment:** very weak progression is the strongest newly measured BAD-regime candidate. Persistence remains the primary regime axis.

### 5.2 Protected-break count inside the same 12-wave span

```text
PB = 0
32 trades / +36.84R
2023 = +37.51R
2024 = -0.67R

PB >= 2
36 trades / -12.70R
2023 = -1.06R
2024 = -11.64R
```

Protected-break churn has weaker standalone separation than progression, but the adverse sign repeats across the two available years and is consistent with the prior three-year 72h result.

**Research judgment:** retain as the structural-stability axis, not as a standalone classifier.

### 5.3 Progression magnitude

A magnitude-aware persistence descriptor was added:

```text
directional_advance_norm =
median signed same-side advance in trade direction
/ median absolute M30 swing-leg size
```

Its distribution is strongly ordered. The highest quartile produces:

```text
28 trades / 11 wins / +40.96R
2023 = +36.84R
2024 = +4.12R
```

A broad threshold sensitivity check is also not knife-edge:

| directional_advance_norm | Trades | Total R | 2023 R | 2024 R |
|---|---:|---:|---:|---:|
| > 0.20 | 48 | +52.24R | +52.17R | +0.07R |
| > 0.25 | 43 | +51.56R | +51.49R | +0.07R |
| > 0.30 | 32 | +36.92R | +34.84R | +2.08R |
| > 1/3 | 27 | +35.78R | +31.66R | +4.12R |
| > 0.40 | 23 | +28.98R | +27.19R | +1.79R |

For the illustrative `> 1/3` split:

```text
Max DD = -4.74R
Longest losing streak = 4
2023 LONG  = +4.81R
2023 SHORT = +26.85R
2024 LONG  = +2.76R
2024 SHORT = +1.36R
```

This is one of the strongest **new** findings. However, Spearman correlation with the original progression score is about `0.84`. It is mostly a magnitude-aware representation of the same persistence information, not a clean new dimension.

**Research judgment:** RETAIN. Study as a possible replacement/refinement of binary progression, not as another stacked filter.

## 6. R-005 — Expansion / compression

Tested causal representations:

- median directional impulse / median counter-direction retracement;
- recent directional impulse size / earlier impulse size;
- recent absolute swing-leg expansion / earlier legs;
- recent six-wave range / prior six-wave range.

### 6.1 Impulse versus retracement

The weakest quartile of `impulse_retrace_ratio` is consistently poor:

```text
ratio ≈ 0.63–0.88
28 trades / -20.30R
2023 = -5.01R
2024 = -15.30R
```

But high ratios alone do not make 2024 consistently profitable.

Conditional descriptive test:

```text
M30_CLEAN_PERSISTENT
+ median directional impulse > median retracement

26 trades / 9 wins
Total = +38.94R
Max DD = -6.17R
Longest losing streak = 6
2023 = +36.25R
2024 = +2.69R
```

This modestly improves 2024 and DD relative to the PLAN-freeze clean-persistent reconstruction, but reduces total R and has not been rechecked on 2025.

### 6.2 Generic expansion

Recent impulse expansion and generic leg expansion look attractive in pooled data but change sign between 2023 and 2024. Range compression/expansion also does not produce a stable monotonic relationship.

A post-hoc `CLEAN_PERSISTENT + leg_expansion_ratio > 1` subset produces only 15 trades and +46.24R. Because it removes more than half the clean-persistent sample, this is recorded as an **overfit warning**, not a rule candidate.

**Research judgment:** retain `impulse_retrace_ratio` for study; reject generic expansion thresholds as standalone regime rules.

## 7. R-006 — Structure cleanliness / overlap

Cleanliness was represented using only existing structure:

- signed 12-wave path efficiency;
- median retracement depth;
- overlap between successive directional impulse price intervals.

Results:

- low path efficiency is weak in aggregate, but every 2024 path-efficiency quartile remains negative;
- deep retracement is weak overall, but the relation is not stable enough by year;
- explicit impulse-overlap quartiles fail to transfer from 2023 to 2024.

A post-hoc `CLEAN_PERSISTENT + retracement depth < 0.8` subset produces 20 trades / +39.22R including +1.69R in 2024, but the cutoff is exploratory and 2025 is unverified.

**Research judgment:** no standalone cleanliness rule. Much of the useful cleanliness information is already carried by progression/persistence.

## 8. R-007 — Trend maturity

M30 maturity was measured causally as:

- owner age in hours;
- confirmed M30 waves since owner start;
- M30 BOS count since owner start.

No early/mid/late definition remains consistently favorable across both years. 2023 generally benefits from mature directional episodes while 2024 remains weak across maturity buckets.

Small profitable bands can be selected inside `M30_CLEAN_PERSISTENT`, but the resulting samples are too small to distinguish information from selection.

**Research judgment:** reject maturity as a standalone regime axis for now.

## 9. R-008 — H1/M30 agreement

Broad H1/M30 trend-agreement groups are positive in 2023 and negative in 2024. Agreement alone does not solve the regime problem.

Within `M30_CLEAN_PERSISTENT`, both H1 and M30 agreeing with trade direction leaves:

```text
20 trades / +28.44R
2023 = +21.72R
2024 = +6.72R
```

Only four 2024 observations remain, so this is not sufficient evidence for a veto.

**Research judgment:** agreement stays context-only.

## 10. R-009 — Structural location

Root midpoint and plan reference price were normalized inside the frozen map range in the trade direction.

No stable monotonic relationship transfers across 2023 and 2024.

A `CLEAN_PERSISTENT + source in first directional half` subset is positive but contains only 10 trades. This is too small and too close to a post-hoc PD-style veto to promote.

**Research judgment:** reject structural location as a standalone regime rule. PD Array remains context/reference only.

## 11. Candidate ranking after the full feature pass

### A. Primary three-year candidate — `M30_CLEAN_PERSISTENT`

Why it remains first:

1. simple structural interpretation;
2. prior-session development result is positive in 2023, 2024, and 2025;
3. strict PLAN-freeze reconstruction stays positive in both currently available raw years;
4. no external indicator dependency;
5. combines two logically different ideas: persistence and structural stability.

### B. Strong BAD-regime evidence

```text
very weak M30 progression
and/or
repeated M30 protected breaks
```

The cleanest new bad-state observation is `progression <= 0.50`: 44 trades / -27.80R / zero positive quarters in the 2023–2024 reconstruction.

### C. Strong alternate persistence representation — `directional_advance_norm`

This is highly promising across thresholds and direction splits, but is strongly redundant with progression. It should be tested as an **alternative persistence representation**, not added as another independent filter.

### D. Secondary conditional axis — impulse versus retracement

`median directional impulse > median retracement` may add expansion information to the clean-persistent state. It is not promoted until the same frozen formula is re-derived on raw 2025.

## 12. What this search did NOT support

Do not add the following from this feature pass:

```text
arbitrary expansion threshold
impulse-overlap threshold
trend-age cutoff
owner BOS-count band
H1/M30 agreement veto
PD/range-location veto
multi-factor quality score
```

Several of these can generate very attractive 2023–2024 curves after selection. That is exactly why they are rejected or left exploratory.

## 13. Multiple-testing ledger and stopping rule

The favorable numbers above were found after testing several related structural representations. They are discovery evidence, not OOS proof.

Do not keep stacking filters until the development curve becomes prettier.

Before opening 2022:

1. recover/re-run the raw 2025 ledger for R-004 through R-009 using the exact PLAN-freeze formulas;
2. reject features whose relationship materially changes sign in 2025;
3. prefer at most 2–4 non-redundant axes;
4. freeze the exact Regime Research V1 definition, formulas, thresholds, and snapshot epoch;
5. only then run 2022 as first OOS.

If the 2025 recheck leaves only `M30_CLEAN_PERSISTENT`, that is an acceptable result. Simplicity is preferable to a Development-Set-optimized composite.

## 14. Current conclusion

The first major hypothesis has survived the full structured feature pass:

```text
BULLISH / BEARISH direction label alone
is not enough.

Tradable continuation appears to require at least:
DIRECTION
+ PERSISTENCE
+ STRUCTURAL STABILITY
```

The strongest new refinement is that persistence likely has both a **consistency** component and a **magnitude** component. Expansion may add information, but cleanliness, maturity, H1/M30 agreement, and structural location do not independently justify strategy filters.

No EA strategy semantics change is authorized by this report.
