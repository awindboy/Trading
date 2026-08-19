# Regime Research 2023–2025

Last updated: 2026-08-20
Status: REGIME RESEARCH V1 FROZEN / DIRECT DEVELOPMENT VALIDATED / 2022 FIRST OOS PASS / NO BASELINE STRATEGY AUTHORITY
Baseline: Mentor deterministic V1 / build 1.91 / `ROOT_OB_DISTAL_20`

## 1. Research protocol

This is the durable ledger for regime-feature discovery. Favorable **and unfavorable** experiments are recorded so multiple-testing and backtest-overfitting risk remain visible.

Dataset roles were frozen before OOS and are now recorded as:

```text
2023–2025 = Development / Research set
2022      = first sealed OOS — opened only after D-137 freeze; PASS
2021      = preferred final untouched confirmation
```

The rule before opening 2022 was: do not inspect or tune against 2022 before an exact regime definition is frozen. That rule was followed. If the model is changed after viewing 2022, the changed model is V2 and 2022 is no longer untouched OOS evidence for it.

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

Current uploaded copy:

```text
mentor_v1_structure_events(20260819-103841).csv
rows = 234,277
SHA-256 = 1bd119c4d3aea9ab759a24541de71be01d0379fa948927bede2a1dae5b9d7b65
```

The hash exactly matches the previously recorded build-1.91 2025 ledger (`mentor_v1_structure_events(20260818-165949).csv`). The current reconstruction reproduces the established 2025 clean result:

```text
58 closed trades / 14 wins / +8.68R
EXTERNAL_CONTINUATION = 51 trades / +15.94R
execution divergence = 0
```

The same frozen PLAN-time feature formulas used for 2023–2024 have now been re-run on this raw 2025 ledger. See section 15.

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

Historical pre-2025 note: this modestly improved 2024 and DD relative to the PLAN-freeze clean-persistent reconstruction, but reduced total R. Section 15 contains the completed 2025 recheck and final V1 judgment.

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

A post-hoc `CLEAN_PERSISTENT + retracement depth < 0.8` subset produces 20 trades / +39.22R including +1.69R in 2024. It was exploratory; section 15 records its 2025 result and why it remains excluded.

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

> Historical 2023–2024 ranking. Section 15 supersedes this ranking after the frozen-formula 2025 recheck.


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

> The raw-2025 recheck required below is now complete. Section 15 records the resulting freeze decision.


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

> Historical pre-2025 conclusion. Section 15–16 supersede the candidate selection after raw-2025 validation.


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


## 15. 2025 frozen-formula recheck and Regime Research V1 freeze

### 15.1 Validation discipline

The 2025 ledger was **not** used to alter the formulas established during the 2023–2024 feature pass.

For each closed clean trade:

```text
snapshot = scenario PLAN freeze
eligible structure = only objects with available_at <= plan_frozen_at
scope for regime study = EXTERNAL_CONTINUATION
```

Feature reconstruction against the saved 2023–2024 snapshot reproduced all previously recorded formulas to numerical precision before applying them to 2025. This includes progression, protected-break count, path efficiency, impulse/retracement, leg expansion, retracement depth, range compression, overlap, location, maturity, and `directional_advance_norm`.

2025 continuation feature coverage:

```text
clean EXTERNAL_CONTINUATION trades = 51
full latest-12-wave context = 50
```

The one trade without 12 confirmed M30 waves is not assigned a 12-wave regime feature state.

### 15.2 Parent `M30_CLEAN_PERSISTENT` survives

Frozen parent definition:

```text
latest 12 confirmed M30 waves
progression >= 2/3
M30 PROTECTED_BREAK inside same 12-wave span <= 1
```

2025 result:

```text
8 trades / 4 wins / 50.0%
+4.58R
mean +0.57R/trade
Max DD -4.04R
longest losing streak 4
```

Canonical PLAN-freeze development result becomes:

```text
39 trades / 15 wins / 38.5%
+52.49R
mean +1.35R/trade
Max DD -8.17R
longest losing streak 8

2023 +47.22R
2024  +0.69R
2025  +4.58R
```

Direction totals across the full development set:

```text
LONG  = 17 trades / +16.78R
SHORT = 22 trades / +35.71R
```

However direction-by-year is not uniformly positive:

```text
2024 SHORT = -0.64R
2025 SHORT = -1.73R
```

The parent state therefore survives, but still leaves room for a genuinely independent regime dimension.

### 15.3 R-004 update — weak progression is NOT a stable BAD veto

The prior 2023–2024 observation:

```text
progression <= 0.50
2023 -4.29R
2024 -23.51R
```

reverses materially in 2025:

```text
2025: 12 trades / 4 wins / +11.32R
```

The combined 2023–2025 subset remains negative (`-16.48R`), but the sign is not stable by year.

**Final V1 judgment:** do **not** authorize `progression <= 0.50` as a standalone BAD-regime veto. Progression remains useful only inside the positive parent state.

### 15.4 R-004 update — `directional_advance_norm` fails transfer

The earlier illustrative `directional_advance_norm > 1/3` result was:

```text
2023 +31.66R
2024  +4.12R
```

The same unmodified split in 2025 gives:

```text
16 trades / 3 wins
-7.89R
mean -0.49R/trade
0 positive active quarters / 3
SHORT = -6.79R
```

Threshold sensitivity also loses the clean monotonic pattern:

| threshold | 2025 trades | 2025 Total R |
|---|---:|---:|
| > 0.20 | 27 | +4.69R |
| > 0.25 | 25 | +2.32R |
| > 0.30 | 20 | -6.40R |
| > 1/3 | 16 | -7.89R |
| > 0.40 | 7 | +1.20R |

**Final V1 judgment:** reject `directional_advance_norm` as the frozen persistence replacement. Do not stack it onto progression.

### 15.5 Structural churn becomes the strongest BAD-state observation

`PB >= 2` inside the same latest-12-wave span remains adverse in every development year:

```text
2023 -1.06R
2024 -11.64R
2025 -5.58R
```

Combined:

```text
55 trades / 11 wins
-18.28R
mean -0.33R/trade
```

This is stronger cross-year BAD-state evidence than weak progression alone.

No separate PB veto is added because the parent positive state already requires `PB <= 1`.

### 15.6 Expansion recheck — impulse/retracement remains supporting evidence only

The exact 2023–2024 lower-quartile boundary (`impulse_retrace_ratio <= 0.8824268`) remains weak in 2025:

```text
10 trades / -4.45R
```

A natural `impulse_retrace_ratio > 1` split is strong in 2025:

```text
35 trades / +26.44R
```

but was still negative in 2024 when used standalone. Inside `M30_CLEAN_PERSISTENT`, all eight 2025 parent trades already satisfy `impulse_retrace_ratio > 1`, so the condition removes nothing in 2025.

**Final V1 judgment:** do not add an impulse/retracement threshold to V1.

### 15.7 Expansion recheck — recent M30 leg expansion survives and is non-redundant

The earlier post-hoc subset:

```text
M30_CLEAN_PERSISTENT
+ leg_expansion_ratio > 1
```

was intentionally not promoted on 2023–2024 alone.

The exact formula is:

```text
leg_expansion_ratio =
mean(abs(size) of the 4 most recent M30 wave-to-wave legs)
/
mean(abs(size) of the preceding 4 M30 wave-to-wave legs)
```

The latest 12 waves contain 11 wave-to-wave legs. The oldest three legs are not used in this ratio.

Interpretation of the frozen threshold:

```text
ratio > 1
=> recent four structural legs are larger on average
   than the immediately preceding four structural legs
```

2025 recheck:

```text
5 trades / 4 wins / 80.0%
+7.61R
mean +1.52R/trade
Max DD -1.02R
longest losing streak 1
```

Development-set combined result:

```text
20 trades / 13 wins / 65.0%
+53.85R
mean +2.69R/trade
Max DD -3.01R
longest losing streak 3

2023: 12 trades / +43.88R
2024:  3 trades /  +2.36R
2025:  5 trades /  +7.61R
```

Direction totals:

```text
LONG  = 12 trades / +16.46R
SHORT =  8 trades / +37.39R
```

Year-direction cells:

```text
2023 LONG  +10.15R
2023 SHORT +33.73R
2024 LONG   -1.00R  (1 trade)
2024 SHORT  +3.37R
2025 LONG   +7.31R
2025 SHORT  +0.29R
```

Quarter character across the 12 development quarters:

```text
positive quarters = 7
negative quarters = 2
zero-trade quarters = 3
```

Trade-state clustering by identical PLAN time + direction gives 16 selected regime clusters for 20 trades, so the result is not solely the product of exact duplicate trade rows.

Most importantly, this expansion feature is genuinely non-redundant with the parent structure:

```text
Spearman rho with progression ≈ +0.02
Spearman rho with PB count    ≈ +0.02
```

Threshold sensitivity near the natural boundary is also not knife-edge:

```text
> 0.9: 21 trades / +52.84R / every year positive
> 1.0: 20 trades / +53.85R / every year positive
> 1.1: 20 trades / +53.85R / every year positive
```

The exact `>1.0` threshold is frozen because it has the simplest structural meaning, not because it maximizes R.

A descriptive Fisher comparison of winners inside the parent state gives approximately `13/20` wins for `leg_expansion_ratio > 1` versus `2/19` for `<= 1` (`p ≈ 0.00056`). This is **not** treated as formal statistical proof because trade outcomes are dependent and multiple features were tested.

### 15.8 Other exploratory subsets remain excluded

Several earlier exploratory combinations also remain positive in 2025, but they are not promoted:

```text
CLEAN_PERSISTENT + retracement_depth < 0.8
2025: 5 trades / +3.22R

CLEAN_PERSISTENT + owner BOS count 2..10
2025: 4 trades / +3.59R

CLEAN_PERSISTENT + source in first directional half
2025: 1 trade / +3.39R
```

Reasons for exclusion:

- arbitrary development-derived cutoff;
- strong redundancy with persistence/cleanliness;
- tiny sample;
- weak causal justification compared with the natural expansion ratio;
- risk of rebuilding PD/maturity veto logic from hindsight.

H1/M30 agreement also removes none of the eight 2025 parent trades, so it adds no 2025 information.

## 16. Regime Research V1 — FROZEN FOR 2022 OOS

Development feature search stops here for V1.

Frozen state name:

`M30_CLEAN_PERSISTENT_EXPANDING`

Exact definition:

```text
Scope:
EXTERNAL_CONTINUATION

Snapshot:
scenario PLAN freeze

Required causal context:
latest 12 confirmed M30 waves
with available_at <= PLAN freeze

Persistence:
directional progression >= 2/3

Structural stability:
M30 STRUCTURE_PROTECTED_BREAK
inside the same 12-wave span <= 1

Expansion:
leg_expansion_ratio > 1.0

leg_expansion_ratio =
mean(abs(last 4 M30 wave-to-wave legs))
/
mean(abs(previous 4 M30 wave-to-wave legs))
```

State vocabulary:

```text
M30_CLEAN_PERSISTENT_EXPANDING
UNKNOWN
```

No new BAD state is created from the complement.

Conceptual axes:

```text
DIRECTION
+ PERSISTENCE
+ STRUCTURAL STABILITY
+ EXPANSION
```

No EMA/ADX/ATR/RSI, no quality score, no H1/M30 agreement veto, and no PD-location veto are added.

### 16.1 Why the model is frozen now

The selected expansion feature:

1. was identified on 2023–2024 and then survived the same-formula 2025 recheck;
2. improves the parent state's development expectancy and drawdown while remaining positive in every year;
3. is nearly uncorrelated with progression/PB, so it represents a different concept;
4. has a natural threshold (`recent leg scale > previous leg scale`);
5. does not require any external indicator or new future-dependent label.

The sample remains small (`20 trades`). That is a reason to seek OOS evidence, not a reason to continue tuning the Development Set.

### 16.2 Frozen 2022 OOS evaluation contract

2022 must be evaluated in three layers:

```text
A. clean EXTERNAL_CONTINUATION baseline
B. parent M30_CLEAN_PERSISTENT
C. frozen M30_CLEAN_PERSISTENT_EXPANDING V1
```

Classification for V1:

```text
INCONCLUSIVE
if clean closed V1 trades < 5

PASS candidate
if clean closed V1 trades >= 5
and Total R > 0
and mean R/trade > 0
and Max DD is less severe than baseline continuation
and longest losing streak is no worse than baseline continuation

FAIL
otherwise
```

The expansion axis is separately considered supported only if V1 does not underperform the parent `M30_CLEAN_PERSISTENT` state on **both** expectancy and drawdown.

Do not change any formula or threshold after 2022 is opened.

If 2022 causes a change, the changed model is Regime Research V2 and must use 2021 or later forward/paper data as its next untouched confirmation.

### 16.3 Historical direct-implementation bridge before OOS

The following subsection records the pre-OOS bridge exactly as it existed after the D-137 freeze. The compile/direct-validation gate has since been completed; Sections 17–20 contain the resulting direct Development and 2022 OOS evidence.

D-138 prepared a separate MT5 research implementation because post-filtering the build-1.91 ledger is not sufficient to prove direct-execution behavior. Removing one scenario may change later same-direction add-ons, opposite-direction conflicts, same-entry contributor merge, pending lifecycle, and later opportunity availability.

Control remains untouched:

```text
mt5/experts/MentorDeterministicV1EA.mq5
build 1.91
```

Research variant prepared at that stage:

```text
mt5/experts/MentorDeterministicV1EA_RegimeResearchV1.mq5
research build identity = 1.92R1
```

At the D-138 pre-OOS stage the variant had two frozen modes:

```text
M30_CLEAN_PERSISTENT
M30_CLEAN_PERSISTENT_EXPANDING
```

All numeric thresholds remain hard-coded to the D-137 freeze.

The gate is evaluated at the baseline-equivalent PLAN moment, specifically after the Root has a valid map/scope and objective family but before the scenario is stored. If the selected regime mode fails, that physical Root identity becomes research-terminal; it cannot wait for the regime to become favorable later. This preserves the original PLAN-time attribution logic as closely as possible.

Passing regime values are frozen into `V1ScenarioPlan` and logged through:

```text
REGIME_RESEARCH_PLAN_ACCEPTED
REGIME_RESEARCH_PLAN_REJECTED
```

A rejected Root may still produce detector/audit `ROOT_CONTACT_OBSERVED` and optional-child context, because physical detection remains unchanged. It never receives a stored research scenario, so it cannot reach `SCENARIO_ROOT_CONTACT_BOUND`, Sweep/CHoCH strategy stages, FVG selection, contributor merge, or order authorization.

The D-138 formula translation was independently checked against all saved closed-trade PLAN snapshots from the original Development Set ledgers. `progression` and PB count match exactly; `leg_expansion_ratio` matches within floating-point epsilon. This verifies formula identity but not compilation or direct-execution portfolio state.

The pre-OOS local acceptance gate was:

```text
MetaEditor compile = 0 errors
2023–2025 PLAN-time classification parity spot-checks = PASS
rejected same-Root later replan = 0
rejected Root merge/order participation = 0
smoke-fixture execution divergence = 0
```

After that gate, the planned 2022 OOS comparison was three **direct Strategy Tester runs** rather than one baseline run plus purely offline filtering:

```text
A. original build-1.91 control / EXTERNAL_CONTINUATION baseline
B. research EA / M30_CLEAN_PERSISTENT parent mode
C. research EA / M30_CLEAN_PERSISTENT_EXPANDING V1 mode
```

Direct trade counts need not equal old post-filtered Development Set counts after execution state diverges causally; PLAN-time regime classification must match the frozen formula.

`AGENTS.md` and `EA_SPEC.md` baseline strategy authority remain unchanged. No research model is promoted before OOS review and a later explicit decision.

## 17. Direct MT5 Development-Set validation

The frozen formula was then implemented as a direct Strategy Tester research variant. This step is necessary because post-filtering a baseline ledger cannot reproduce all later portfolio-state consequences of suppressing a scenario.

The direct research implementation leaves the D-134 execution core unchanged after the PLAN-time regime gate.

### 17.1 Direct-run provenance

#### Expansion V1 full-audit run — 2023–2025

```text
uploaded file = 25.csv
period = 2023-01-01 ~ 2025-12-31
rows = 608,893
bytes = 236,873,208
SHA-256 = e43cd7e12e672d21afc63ed2bbcb5837ea5ca0dd8f1270401979ac203a2f7ca3
mode = M30_CLEAN_PERSISTENT_EXPANDING
execution divergence = 0
```

This was the original high-volume audit run before compact logging.

#### Parent compact run — 2023–2025

```text
uploaded file = 25(1).csv
period = 2023-01-01 ~ 2025-12-31
rows = 9,710
bytes = 5,477,452
SHA-256 = aeba85cc7fe396d21db4e93d2967f8dd27513d7e61c66faba174a04b096257c2
mode = M30_CLEAN_PERSISTENT
execution divergence = 0
```

The compact logger reduced the multi-year event ledger from hundreds of MB to a few MB while preserving the M30 regime inputs, regime verdicts, execution milestones, position outcomes, and divergence/error events required for research analysis.

### 17.2 Regime formula implementation parity

The full-audit Expansion run contains:

```text
REGIME_RESEARCH_PLAN_ACCEPTED = 428
REGIME_RESEARCH_PLAN_REJECTED = 2,208

EXTERNAL_CONTINUATION:
accepted = 428
rejected = 1,910

EXTERNAL_REVERSAL:
accepted = 0
rejected = 298
```

The 2,338 `EXTERNAL_CONTINUATION` regime decisions were independently recomputed from the logged M30 wave and protected-break history.

Result:

```text
progression mismatch = 0
protected-break-count mismatch = 0
leg-expansion-ratio classification mismatch = 0
final PASS/REJECT mismatch = 0
```

This is direct evidence that the frozen PLAN-time formula was translated correctly into the research EA.

### 17.3 Parent direct execution

`M30_CLEAN_PERSISTENT`:

```text
46 trades / 15 wins / 32.6%
Total = +45.436530R
Mean = +0.987751R/trade
R profit factor = 2.45
Max DD = -11.204262R
Longest losing streak = 11

2023: 23 trades / 9 wins / +45.219207R
2024: 14 trades / 2 wins /  -3.364869R
2025:  9 trades / 4 wins /  +3.582192R
```

Execution:

```text
pending accepted = 59
filled = 46
closed = 46
execution divergence = 0
```

### 17.4 Frozen Expansion V1 direct execution

`M30_CLEAN_PERSISTENT_EXPANDING`:

```text
24 trades / 13 wins / 54.2%
Total = +49.797314R
Mean = +2.074888R/trade
R profit factor = 5.44
Max DD = -5.173397R
Longest losing streak = 5

2023: 12 trades / 8 wins / +43.879687R
2024:  7 trades / 1 win  /  -1.687467R
2025:  5 trades / 4 wins /  +7.605095R
```

Execution:

```text
pending accepted = 34
filled = 24
closed = 24
execution divergence = 0
```

### 17.5 Direct Parent versus Expansion is a clean nested comparison

Every one of the 24 Expansion trades is present in the Parent direct run.

For all common trades:

```text
scenario identity = same
fill = same
SL = same
TP = same
exit = same
R difference = 0
```

Expansion therefore removes exactly 22 Parent trades:

```text
22 trades / 2 wins / 20 losses
Total = -4.360784R
Mean = -0.198217R/trade
R profit factor = 0.78

2023: 11 removed / +1.339520R
2024:  7 removed / -1.677402R
2025:  4 removed / -4.022903R
```

The 2023 removed group is still positive only because one approximately `+11.35R` winner offsets ten losses. The 2024 and 2025 removed groups are negative.

**Development direct judgment:** the expansion axis adds incremental information beyond the Parent state. It improves mean expectancy, total R, drawdown, loss streak, and win rate while removing a direct-execution group with negative aggregate expectancy.

### 17.6 Why direct execution supersedes offline post-filter performance

The frozen offline Expansion attribution was:

```text
20 trades / +53.847843R
```

The direct Expansion run was:

```text
24 trades / +49.797314R
```

The original offline 20 trades are all reproduced in the direct run with identical R. Four additional direct trades explain the difference.

Two are genuine causal portfolio-state effects:

1. **same-entry contributor state change** — a baseline execution master Root failed the regime gate, but other same-entry PASS Roots remained and could merge into an executable research scenario;
2. **opposite-direction exposure release** — a FAIL opposite-direction position was removed by the regime gate, so a later PASS setup was no longer blocked by `OPPOSITE_DIRECTION_EXPOSURE_CONFLICT`.

The other two are late-December 2024 baseline-path positions that were already filled but were excluded from the older calendar-bounded closed-trade attribution because they closed in early 2025.

Therefore:

```text
offline post-filter
= discovery / PLAN-classification evidence

direct Strategy Tester
= final implemented-variant performance authority
```

Future year-level studies should cohort trades by entry year and allow positions opened near year-end to reach their terminal outcome instead of treating December 31 as a forced analytical censoring boundary.

## 18. 2022 first sealed OOS direct validation

The model was not changed after D-137 froze the formula and before 2022 was opened.

Three direct layers were evaluated:

```text
A. baseline no regime gate
B. M30_CLEAN_PERSISTENT Parent
C. M30_CLEAN_PERSISTENT_EXPANDING frozen V1
```

### 18.1 OOS file provenance

#### Parent + Expansion combined compact ledger

```text
uploaded file = 25(2).csv
rows = 6,766
bytes = 3,279,300
SHA-256 = 7a9df6350eed1f93938b485ae3eecde8ddf42464a734d5b29e7e2b4a56e26bd1
```

This CSV contains two appended EA runs:

```text
run 1 = M30_CLEAN_PERSISTENT
run 2 = M30_CLEAN_PERSISTENT_EXPANDING
```

Each run is separated by its own `EA_START`.

#### Baseline no-gate compact ledger

```text
uploaded file = no_gate.csv
rows = 6,857
bytes = 4,383,745
SHA-256 = 40c0bf0f744504f9d12ff7a777fc85a8366ab2b3bd168a23f6a35599f944b42a
mode = BASELINE_NO_REGIME_GATE
execution divergence = 0
```

### 18.2 2022 baseline

All scopes:

```text
85 trades / 17 wins / 20.0%
Total = -19.209190R
Mean = -0.225990R/trade
Max DD = -24.339604R
Longest losing streak = 13
```

The pre-registered OOS comparison uses `EXTERNAL_CONTINUATION` only:

```text
72 trades / 15 wins / 20.8%
Total = -14.476581R
Mean = -0.201064R/trade
Max DD = -20.764118R
Longest losing streak = 18
```

Baseline reversal was also negative:

```text
13 trades / 2 wins
-4.732610R
```

### 18.3 2022 Parent

`M30_CLEAN_PERSISTENT`:

```text
16 trades / 3 wins / 18.8%
Total = -3.825354R
Mean = -0.239085R/trade
Max DD = -5.741120R
Longest losing streak = 5
R profit factor = 0.71
execution divergence = 0
```

The Parent drastically reduces baseline drawdown and trade count but remains negative in 2022.

### 18.4 2022 frozen Expansion V1

`M30_CLEAN_PERSISTENT_EXPANDING`:

```text
6 trades / 1 win / 16.7%
Total = +0.994756R
Mean = +0.165793R/trade
Max DD = -3.012334R
Longest losing streak = 3
R profit factor = 1.20
execution divergence = 0
```

Trade R sequence:

```text
-1.008R
-1.003R
-1.002R
+6.023R
-1.011R
-1.004R
----------------
+0.995R
```

The positive OOS result is therefore tail-dependent and based on a small sample. This is a material caveat, not a reason to alter the frozen definition.

### 18.5 Frozen OOS contract evaluation

The D-137 contract was:

```text
INCONCLUSIVE
if V1 clean closed trades < 5

PASS candidate
if:
trades >= 5
Total R > 0
mean R/trade > 0
Max DD less severe than 2022 continuation baseline
longest losing streak no worse than 2022 continuation baseline

FAIL
otherwise
```

Observed:

```text
V1 trades = 6                         -> PASS
Total R = +0.994756R                 -> PASS
Mean R = +0.165793R/trade            -> PASS
V1 Max DD = -3.012334R
Baseline continuation DD = -20.764118R
                                         -> PASS
V1 longest loss streak = 3
Baseline continuation streak = 18
                                         -> PASS
```

Classification:

```text
2022 FIRST OOS = PASS
```

### 18.6 Expansion axis versus Parent in OOS

The expansion component had a separate support requirement: V1 must not underperform the Parent on **both** expectancy and drawdown.

Observed:

```text
Parent mean R = -0.239085
V1 mean R     = +0.165793

Parent Max DD = -5.741120R
V1 Max DD     = -3.012334R
```

V1 improves both.

All six V1 trades are exact members of the Parent run with identical R. Expansion removes ten Parent-only trades:

```text
10 trades / 2 wins / 8 losses
Total = -4.820111R
Mean = -0.482011R/trade
R profit factor = 0.40
```

So the incremental expansion axis also transfers directionally to the first untouched OOS year.

## 19. Research status after first OOS

The frozen V1 has now passed three increasingly strict gates:

```text
Development discovery + 2025 same-formula transfer
-> PASS

Direct MT5 Development execution
-> PASS as an incremental Parent refinement

First sealed 2022 OOS contract
-> PASS
```

This is stronger evidence than the original Development-only result, but it is still not sufficient to declare universal robustness.

Reasons to remain conservative:

```text
2022 V1 trade count = 6
2022 positive result depends on one +6R-class winner
baseline and Parent are both negative in 2022
development performance is still tail-sensitive
only one truly untouched OOS year has been opened
```

The preferred next step remains a final untouched 2021 confirmation.

## 20. Strategy authority and stopping rule

No formula or threshold is changed after the 2022 result.

Frozen V1 remains:

```text
M30_CLEAN_PERSISTENT_EXPANDING
progression >= 2/3
PB <= 1
leg_expansion_ratio > 1.0
```

Current authority status:

```text
Research V1 = OOS-supported research model
AGENTS.md = unchanged
EA_SPEC.md = unchanged
build 1.91 baseline = preserved control
```

Do not automatically promote the model into baseline strategy authority from one OOS year.

Next:

```text
2021 frozen A/B/C confirmation
-> explicit promotion / no-promotion decision
-> only then update AGENTS.md and EA_SPEC.md if promotion is approved
```

Any formula or threshold change made after viewing 2022 defines **Regime Research V2**. 2022 cannot be used as untouched OOS evidence for that changed model.

