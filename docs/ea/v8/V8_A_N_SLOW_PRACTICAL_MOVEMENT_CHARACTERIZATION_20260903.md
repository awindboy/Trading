# V8-A-N-SLOW Practical Movement / Payoff Characterization — 2026-09-03

Status: `DEVELOPMENT EVIDENCE / MOVEMENT CHARACTERIZATION COMPLETE / NO PRODUCTION AUTHORITY`
Market: `GOLD#`
Evidence: `2024-2026 consumed development evidence, P0/P2`
Reserve: `GOLD# 2021 untouched`

## 1. Purpose

The structural phase established that structural retention is real but is not generic same-direction continuation. This phase asks the practical question required before explicit TP/SL optimization:

> once ACCEPTANCE exists, how much favorable movement does price actually offer, how much survives as current displacement, how much is given back, and can early realized progress identify large-winner continuation?

Acceptance close is used only as a causal observation reference price. It is **not** frozen as an entry price.

Per project direction, the reconstructed current Slow-N P0/P2 population is treated as the exact downstream authority. Small historical parity differences are not reopened.

## 2. Measurements

For each accepted event, from the acceptance reference price:

- MFE at 5/10/15/30/60/120/240m;
- current directional displacement at the checkpoint;
- giveback = MFE - current displacement;
- structural state = `PRISTINE / DAMAGED / CLOSE_BROKEN`;
- first-hit time for `0.10 / 0.25 / 0.50 / 0.75 S`;
- target-before-wick-break and target-before-close-break ordering;
- future MFE after 5/10/15m checkpoints;
- 2024-derived progress quantiles carried unchanged into 2025/2026.

`S = previous-completed H4 ATR14`.

No P/L, cost, SL or TP optimization is performed here.

## 3. MFE is relatively stable in S units; fixed points are not

Representative median MFE ranges across P0/P2 and years:

```text
15m  ~0.18-0.22 S
30m  ~0.26-0.28 S
60m  ~0.34-0.38 S
120m ~0.45-0.51 S
240m ~0.52-0.61 S
```

Absolute GOLD movement changes dramatically with volatility. Median S is approximately:

```text
2024 ~11.9
2025 ~19.5-20.3
2026 ~42.7-43.0
```

Therefore fixed targets imply very different normalized difficulty:

```text
+10 points ~= 0.84 S in 2024
+10 points ~= 0.49-0.51 S in 2025
+10 points ~= 0.23 S in 2026
```

A fixed-point exit can still be an implementation choice, but it is not a stable market-scale statement across volatility regimes.

## 4. Large excursion exists, but passive time holding does not preserve it

A critical result is the separation between MFE and terminal displacement.

At 60m, median MFE is roughly `0.34-0.38S`, while median directional close displacement is around zero.

At 240m, median MFE reaches roughly `0.52-0.61S`, while median directional close displacement remains around zero or slightly negative in most cells.

Median giveback by 240m is roughly `0.55-0.66S`.

Therefore:

```text
large available excursion
!=
large profit retained by passive time holding
```

The eventual strategy needs a capture/runner architecture; simply waiting longer is not supported.

## 5. First-hit timing

Across P0/P2 and 2024-2026, conditional median first-hit time is approximately:

```text
0.10S: 3-5m
0.25S: 13-15m
0.50S: 30-41m
0.75S: 51-61m
```

Within 240m, approximate hit rates are:

```text
0.10S: 89-91%
0.25S: 75-78%
0.50S: 50-58%
0.75S: 37-40%
```

Small excursion is common and fast; large excursion is materially less common and slower.

## 6. Structural break cannot mechanically become the eventual trade stop

Among eventual `0.75S` winners, only roughly 29-39% reach the target before the first wick break and roughly 40-51% before the first M1-close break, depending on year/phase.

Equivalently, many eventual large winners first experience structural damage, and roughly half or more can experience a close break before later reaching `0.75S`.

This does **not** mean close break should be ignored. It means structural-state failure semantics and actual trade-stop semantics are different research questions.

The prior negative remains mandatory: post-break equal-distance direction is near chance. Do not reinterpret break as a reversal signal.

## 7. Adverse excursion before large winners

Among eventual winners, meaningful adverse movement before target is common.

For `0.50S` and `0.75S` winners, median MAE before target is generally around `0.15-0.21S`.

The 75th percentile is often around `0.33-0.44S`, and the 90th percentile can exceed `0.60S`.

Therefore a very tight fixed structural stop would remove a substantial fraction of eventual large winners. This is descriptive evidence only; it does not authorize a wider SL.

## 8. Early realized MFE is specifically informative for large-winner continuation

The strongest new practical signal is realized MFE at an early checkpoint.

At 15m, restricting to events whose M1-close structure is still intact:

```text
MFE15/S -> future additional 0.50S within the 60m window
P0 2025 AUC .677
P0 2026 AUC .716
P2 2025 AUC .657
P2 2026 AUC .679
```

For a larger future `+0.75S` move, discrimination is stronger but sample size is smaller:

```text
P0 2025 .764
P0 2026 .820
P2 2025 .745
P2 2026 .786
```

The relationship is weaker for only `+0.25S` continuation.

Interpretation:

> realized early progress is more useful for distinguishing large-winner continuation than for predicting small routine continuation.

This is the first practical bridge from structural validity to runner characterization.

## 9. 2024-frozen quantile validation

To avoid choosing a threshold from 2025/2026 outcomes, the 2024 close-intact MFE15 distribution was used to freeze quartile boundaries.

The 2024 Q75 boundary is approximately:

```text
P0 0.555S
P2 0.546S
```

Applied unchanged to future years:

### Future additional 0.50S

```text
P0 2025 top-Q: 56.5% vs lower-75% 20.7%
P0 2026 top-Q: 42.9% vs lower-75% 20.8%
P2 2025 top-Q: 48.1% vs lower-75% 24.1%
P2 2026 top-Q: 45.5% vs lower-75% 23.1%
```

### Future additional 0.75S

```text
P0 2025 top-Q: 39.1% vs lower-75% 6.9%
P0 2026 top-Q: 35.7% vs lower-75% 7.5%
P2 2025 top-Q: 29.6% vs lower-75% 7.2%
P2 2026 top-Q: 36.4% vs lower-75% 9.6%
```

This is promising validation evidence, but **Q75 / ~0.55S is not a frozen trading threshold**.

## 10. Direction and quarter stress

For close-intact 15m events, MFE15 predicting future `+0.50S` remains positive in both directions:

```text
P0 2025 SHORT .684 / LONG .610
P0 2026 SHORT .725 / LONG .719
P2 2025 SHORT .699 / LONG .615
P2 2026 SHORT .625 / LONG .745
```

Substantial 2025/2026 quarter cells are also positive, roughly `.62-.74` in the checked cells.

No direction or quarter permission rule is frozen.

## 11. Giveback is not the primary runner signal

At 15m, current displacement and giveback ratio are less stable than MFE15 itself for future large continuation.

Within close-intact events, MFE15 remains the most stable compact variable. Splitting already-progressed events by whether they had given back more or less than roughly 50% does not produce a reliable ordering across phases/years.

Interpretation:

> the useful information appears to be that the market has demonstrated a sufficiently large favorable excursion, not merely that the current close is still near the local maximum.

Do not create a giveback threshold from current evidence.

## 12. Timing of runner recognition

Fixed checkpoints show:

- 5m: generally too early / weaker;
- 10m: useful early signal, but materially weaker than 15m in several cells;
- 15m: strongest and most stable current runner characterization.

A purely fixed 15m wait may still be late for execution. A causal progress-event formulation was also checked.

First M1-close progress milestones while close structure remains intact:

```text
+0.25S milestone coverage ~32-41%, median time ~8-10m
then future +0.50S ~31-40%
then future +0.75S ~17-23%

+0.50S milestone coverage ~19-26%, median time ~19-23m
then future +0.50S ~36-41%
then future +0.75S ~18-27%
```

These event-triggered milestones are causal but do not outperform the 15m MFE characterization enough to freeze an early runner trigger yet.

## 13. Small-move vs runner interpretation

By 15m, roughly 40-43% of future-valid events have already shown at least `0.25S` MFE, while only roughly 14-17% have shown `0.50S`.

Among 15m close-intact events:

```text
already hit 0.25S by 15m:
future +0.50S ~32-35%
future +0.75S ~16-22%

not yet hit 0.25S by 15m:
future +0.50S ~14-20%
future +0.75S ~3-6%
```

This supports a conceptual two-problem architecture:

```text
Problem A: routine excursion capture
small movement is common and fast

Problem B: runner preservation
large future continuation is concentrated among close-intact events that have already demonstrated strong early MFE
```

It does not yet specify an entry, partial-exit size, TP, trailing stop, or SL.

## 14. Decisions from this phase

1. Use S-normalized movement as the primary research scale; keep fixed GOLD points only as implementation/economic views.
2. Treat MFE and retained displacement as separate quantities.
3. Do not use passive fixed-time holding as the default exit concept.
4. Do not equate structural break with a finalized SL.
5. Retain `close-intact + realized early MFE` as the primary runner-continuation candidate.
6. Do not freeze `0.55S`, Q75, or any giveback threshold.
7. 15m is the strongest current characterization checkpoint; 10m remains the main earlier-timing challenger.
8. Movement characterization is mature enough to preregister explicit economics research.
9. Keep 2021 locked.

## 15. Next phase

Next research is **preregistered entry / risk / partial-profit / runner economics**.

Before examining P/L outcomes, freeze candidate architectures and parameter families from structural/movement semantics rather than optimizing on realized profit.

The first comparison should include at minimum:

- simple single-exit control;
- small-profit + runner split;
- state/progress-conditioned runner retention;
- structural-vs-price-distance stop semantics;
- cost-adjusted R expectancy, WR, average winner, DD and loss streaks;
- P0/P2, year, direction and regime robustness.

`GOLD# 2021` remains untouched.

## 16. Result files

See `results/v8_practical_movement_20260903/`:

- `movement_horizon_summary.csv`
- `target_hit_timing_summary.csv`
- `mae_before_target_summary.csv`
- `target_vs_structural_break_ordering.csv`
- `runner_checkpoint_auc.csv`
- `runner_2024frozen_quartile_validation.csv`
- `runner_topq_vs_lower75_ci.csv`
- `runner_direction_stress.csv`
- `runner_quarter_stress.csv`
- `progress_milestone_summary.csv`
