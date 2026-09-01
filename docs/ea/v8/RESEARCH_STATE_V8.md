# V8 Research State

Status: `ACTIVE / V8-A-N-SLOW ONSET + EXTENSION / DIRECTION BOTTLENECK`
Date: `2026-09-02`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## Movement — ONSET

```text
T_onset = 0.25 * previous-completed H4 Wilder ATR14
P15 fresh75
```

Phase-0 fresh75:

```text
2024 N653 78.10%
2025 N535 78.50%
2026 N321 76.01%
```

Phase-2 remains similar. Exact fresh membership Jaccard = `57.22%`.

Status: `PROVISIONAL ONSET MOVEMENT AUTHORITY / MODEL TRAINING NOT FINAL`.

## Movement — EXTENSION

Research-only surface:

```text
T_ext = 0.75 * previous-completed H4 ATR14
P60 / P120 / P240
P120 = central research coordinate
```

AUC Phase-0:

```text
P60  .814 / .769 / .777
P120 .759 / .703 / .718
P240 .730 / .665 / .661
```

Current ONSET fresh later reaches larger distances at:

```text
0.50ATR/60m  71.36 / 71.59 / 68.22%
0.75ATR/120m 62.63 / 58.69 / 56.07%
1.00ATR/240m 54.82 / 51.21 / 48.91%
```

Interpretation: ONSET identifies the start of a broader volatility episode; EXT estimates likely continuation magnitude/horizon.

Status: `RETAINED RESEARCH CONTEXT / NO EXT TRIGGER / NO ENTRY FILTER AUTHORITY`.

## Direction

No frozen Slow-N direction engine.

New higher-horizon direct direction models also failed to transfer. Longer horizon is not a solution by itself.

Retained candidates:

1. BB-B expansion context:
   - Phase-0 N64 65.63%
   - Phase-2 N63 65.08%
2. Stoch/M1/tick temporal re-synchronization:
   - overlap-only relative0001 N45 66.67%
   - -10m placebo 45.00%

Full ONSET raw-tick coverage remains the next critical missing information source.

## Mandatory-entry constraint

Every ONSET fresh event remains eligible for mandatory LONG/SHORT.

EXT probability cannot be used as an abstention filter to inflate WR.

## Economics

Closed until direction is frozen.

Later EXT use may be studied for holding/runner/target architecture without deleting ONSET entries.

## Next ordering

1. full ONSET raw tick extraction;
2. `0001` + placebo + M1 transition;
3. BB-B interaction;
4. native Path Clearance;
5. M1 structure parity/redefinition;
6. direction freeze;
7. preregister EXT-conditioned exit/holding economics;
8. MT5 real-tick execution;
9. keep 2021 locked.
