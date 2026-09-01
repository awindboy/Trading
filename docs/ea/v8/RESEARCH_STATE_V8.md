# V8 Research State

Status: `ACTIVE / V8-A-N-SLOW DOWNSTREAM REVALIDATION`
Date: `2026-09-02`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## Movement layer

Current provisional Slow-N scale:

```text
T = 0.25 * previous-completed H4 Wilder ATR14
decision-block aligned
T fixed for the H4 block
```

Phase-0 fresh75:

```text
2024 N653 78.10%
2025 N535 78.50%
2026 N321 76.01%
```

Phase-2 robustness:

```text
2024 N733 80.22%
2025 N579 76.34%
2026 N292 78.08%
```

Exact fresh-event membership is only moderately stable across phases (`Jaccard 57.22%`), so downstream candidates require cross-phase robustness.

## Direction layer

No frozen Slow-N direction engine.

### Failed transfer families

Generic deterministic chart voting, standalone Stoch, market-question panel, standalone M1 questions, BB-A/C/D and generic tick majority are negative evidence.

### Current positive candidates

`BB-B`:

```text
middle residence -> upper-band outside close -> SMA-distance AWAY
predict UP
```

Pooled:

```text
Phase-0 N64 65.63%
Phase-2 N63 65.08%
```

`Stoch/M1/tick re-synchronization`:

```text
old/new tick-covered overlap only
relative 0001 N45 66.67%
-10m placebo 45.00%
```

Promising but not full-population evidence.

## Instrumentation

- V4 tick wall-clock alignment remains authority.
- Legacy M1 confirmed-structure generator has a reproducibility gap; do not use old percentages as new evidence.
- New `V8SlowNP15ContextIndicator.mq5` is Phase-0 research visualization only.

## Economics

Closed until direction is frozen.

## Next ordering

1. full Slow-N raw tick extraction;
2. full `0001`/M1 transition transfer test;
3. native Path Clearance;
4. BB-B x temporal transition;
5. M1 structure parity/redefinition;
6. direction freeze;
7. exits/economics/execution;
8. keep 2021 locked.
