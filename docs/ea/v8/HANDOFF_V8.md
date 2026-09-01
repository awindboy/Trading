# V8 Development Handoff

Last updated: `2026-09-02`
Current phase: `V8-A-N-SLOW / ONSET + EXTENSION MAPPED / DIRECTION BOTTLENECK`
Production authority: `NONE`
Market: `GOLD#`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`
Base Git HEAD for this update: `45925b29fbec7d52509652e5787654624ecc0848`

## 1. Read this first

The active Slow-N movement architecture now separates two questions.

```text
ONSET
T_onset = 0.25 * previous-completed H4 ATR14
P15 fresh75
=> is a movement episode starting?

EXTENSION
T_ext = 0.75 * previous-completed H4 ATR14
P60 / P120 / P240
=> how likely is the episode to travel materially farther?
```

Both scales use the H4 block containing the M5 **decision timestamp** and Wilder ATR14 from the immediately previous fully completed H4 bar. No partial H4 value is allowed.

Direction remains separate and unfrozen.

## 2. ONSET movement population

Phase-0:

```text
2024 fresh75 N653 / hit15 78.10%
2025 fresh75 N535 / hit15 78.50%
2026 fresh75 N321 / hit15 76.01%
```

Phase-2:

```text
2024 N733 / 80.22%
2025 N579 / 76.34%
2026 N292 / 78.08%
```

Phase-0 vs Phase-2 event-set Jaccard = `57.22%`.

Interpretation: aggregate movement quality is stable, exact fresh membership is only moderately stable.

## 3. New higher-horizon extension result

Movement-only target screen:

```text
H = 60 / 120 / 240m
k = 0.50 / 0.75 / 1.00 H4 ATR
```

Annual base rates were stable across 2022-2026.

Retained research target:

```text
T_ext = 0.75 * previous-completed H4 ATR14
2026 median distance ~30.28p
```

Joint survival model:

```text
P60 <= P120 <= P240 structurally
```

AUC range by year:

```text
P60  .814/.769/.777
P120 .759/.703/.718
P240 .730/.665/.661
```

Phase-2 is materially similar.

`P120` is the central extension research coordinate.

No EXT trigger is frozen and EXT probability is not an entry veto.

## 4. Critical finding — ONSET predicts larger episodes

Without selecting new events, current Phase-0 ONSET fresh75 later reached:

```text
0.50 H4 ATR within 60m:
71.36 / 71.59 / 68.22%

0.75 H4 ATR within 120m:
62.63 / 58.69 / 56.07%

1.00 H4 ATR within 240m:
54.82 / 51.21 / 48.91%
```

Unconditional annual base rates for these three questions are only roughly `19-25%`.

Interpretation:

> ONSET fresh75 is not merely a small 15-minute burst detector; it marks the beginning of a larger volatility episode at roughly 2-3x unconditional frequency.

This supports preserving ONSET and using EXT as a separate continuation/holding context.

## 5. Higher horizon did not solve direction

The following mandatory-direction approaches failed to transfer robustly:

1. separate `P_UP/P_DOWN` using the movement representation;
2. signed M1/M5 multi-horizon path representation;
3. signed direction on the fixed-0.75 survival-fresh population.

Representative first-touch accuracy stayed near chance or reversed by year.

Therefore:

```text
longer horizon != solved direction
```

Do not choose a horizon/target from whichever year gives the best direction result.

## 6. Current direction evidence

No frozen Slow-N direction engine.

### Failed families

Generic deterministic chart voting, standalone Stoch, market-question panels, standalone M1 questions, BB-A/C/D, generic tick majority, and the new generic higher-horizon direction models are negative evidence.

### BB-B retained

```text
middle residence
-> trigger closes above upper Bollinger band
-> absolute SMA distance AWAY
predict UP
```

```text
Phase-0 N64 65.63%
Phase-2 N63 65.08%
```

Small-sample development candidate only.

### Stoch/M1/tick re-synchronization retained as mechanism hypothesis

Old/new tick-covered overlap:

```text
relative 0001 N45 / 66.67%
-10m placebo N40 / 45.00%
```

Full new ONSET tick extraction is still missing.

## 7. Mandatory-fresh objective

The strategy research target remains:

> every ONSET fresh event must receive LONG or SHORT; no abstention layer merely to inflate WR.

Therefore EXT probability may not be used to delete low-EXT trades.

If direction is later frozen, EXT may be tested for:

- holding horizon;
- runner permission;
- target distance;
- exit architecture;

while preserving all ONSET entries.

## 8. Next work order

1. Read `V8_A_N_SLOW_HIGHER_HORIZON_EXTENSION_RESEARCH_20260902.md`.
2. Preserve ONSET and EXT as separate movement questions.
3. Full V4-aligned raw-tick extraction for every ONSET fresh75 event.
4. Exact `Stoch D + relative 0001` + -10m placebo on full coverage.
5. Full M1 oscillator alignment/transition transfer.
6. BB-B x temporal-transition interaction.
7. Native Slow-N Path Clearance.
8. Recover/redefine M1 confirmed structure with parity.
9. No additional generic higher-horizon direction search without new information.
10. Freeze direction.
11. Only then preregister economics, including possible EXT-conditioned holding/runner logic.
12. Keep 2021 locked.

## 9. Reading order

1. `AGENTS_V8.md`
2. this `HANDOFF_V8.md`
3. `V8_A_N_SLOW_HIGHER_HORIZON_EXTENSION_RESEARCH_20260902.md`
4. `V8_A_N_SLOW_DOWNSTREAM_REVALIDATION_RESULT_20260902.md`
5. `DECISIONS_V8_SLOW_N_RESET_ADDENDUM_20260902.md`
6. `RESEARCH_STATE_V8.md`
7. `BACKLOG_V8.md`
