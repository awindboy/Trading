# V13 LTF ML / Tail-Persistence Checkpoint — 2026-09-29

Status: `USEFUL REPRESENTATION / SIZING AUTHORITY REJECTED`

## Why ML was reconsidered

V10 showed that strong economics did not require a high win rate: broad participation plus larger exposure in persistent right-tail runs could work. The LTF pullback study therefore tested ML primarily as a **conviction/tail head**, not merely as a veto classifier.

## Feature families

The current dataset contains raw and H4-ATR180-normalized causal coordinates including:

- M30 pullback depth, impulse size, pullback duration;
- prior survived envelope, envelope ratio, prior successful correction count;
- M15 POI family, width, age, wick/close penetration, reject/accept distances;
- M15 candle/path body, range, close location, opposite wick, tick-volume relative state, path efficiency/alignment;
- H1 alignment/body/range;
- H4 HA body/range and raw-close-vs-HA state.

## Chronological outer-year rebreak classification

Training uses prior years only; labels crossing the next outer-year boundary are purged.

Robust logistic AUC:

```text
                2024    2025    2026
Location only   0.716   0.686   0.688
+ POI reaction  0.747   0.709   0.734
Full path       0.777   0.746   0.758
```

This is real incremental information: reaction/path features improve rebreak classification in every evaluated year.

Remaining-MFE regression also ranked future excursion moderately:

```text
Spearman
2024 0.341
2025 0.315
2026 0.361
```

## What failed

Direct realized P/L prediction was weak:

```text
P/L regression Spearman
2024 0.050
2025 0.085
2026 0.110
```

The model can identify continued movement/MFE better than it can identify what survives until the eventual H4 flip. Giveback is a separate problem.

A hurdle/tail score improved ranking of rebreak/tail excursion but score-based 2x/3x sizing did not beat same-count random-upsize controls reliably in 2024/2025. Therefore it is not sizing authority.

Proof-stage ML was worse: after actual M30 prior-extreme rebreak, additional-P/L classification AUC was approximately:

```text
2024 0.508
2025 0.473
2026 0.449
```

This is effectively random and is rejected.

The V10-style fixed 180-H4 realized-feedback upgrade was also tested without retuning the window. It failed especially in 2024, where feedback-enabled proof trades were strongly negative. It is not promoted.

## Current ML decision

Keep the feature/OOF infrastructure as instrumentation. Do **not** use current ML as:

- entry veto authority;
- 2x/3x size authority;
- proof-stage runner selector;
- era exception mechanism.

The next research should first repair the market-state representation (true all-correction envelope) and actual execution semantics. ML can be retested only after that base is stable.
