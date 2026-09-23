# V11 Wave edge initial diagnostic

Date: `2026-09-22`

Status: `CONSUMED DEVELOPMENT EVIDENCE / NO INCREMENTAL EDGE ESTABLISHED / NO TRADE AUTHORITY`

## Question

Does the fixed Wave Candle representation improve identification of avoidable V10 R7G Hard-SL Children without materially deleting the persistent-run right tail?

Two causal observation points were fixed:

1. the completed H4 Wave immediately before Child entry;
2. the forming H4 Wave at exactly +60 minutes, using completed M5 only.

The +60m test also compared the change from the +30m compressed Wave snapshot. It did not expose the ordered raw M5 path.

## Inputs and parity

- raw M1 SHA-256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`;
- R3 universe SHA-256: `f352a99c746752ca259da33dbdaee9d8f0cb874bd01cf520a487fe1bdbf82609`;
- MT5 R7G event export SHA-256: `c4348a34aa35d1e9793283cebbf1a028327c10e3e1c5a4fde2a9e74e3ff801a7`;
- 6,770 universe rows;
- 1,649 matched resolved positive-weight R7G Children;
- zero direction and stage mismatches;
- 1,395 Children alive with an exact usable +60m observation;
- 66 later MT5 events had no resolved universe match and were not backfilled.

## Fixed Wave coordinates

- path efficiency;
- direction-aligned settlement fraction;
- settlement dispersion divided by prior H4 ATR180;
- KDE density at selected HA close;
- selected close distance from the KDE peak divided by ATR180;
- direction-favorable KDE mass fraction;
- normalized KDE entropy.

Wave evolution added only four fixed +30m-to-+60m changes: efficiency, settlement fraction, favorable density mass, and direction-aligned settlement-centroid migration.

## Main result

Low efficiency and weak favorable settlement had pooled STOP AUCs of `0.677` and `0.647` before entry. They were real descriptive associations, but they were strongly redundant with the outer shell: efficiency had Spearman `0.717` correlation with direction-aligned HA body/ATR, and settlement fraction had `0.618` correlation.

Wave-specific density shape was weak:

```text
close-density ratio STOP AUC     0.522
KDE peak-gap STOP AUC            0.514
KDE entropy STOP AUC             0.483
```

Fixed temporal logistic comparisons were:

| Observation | Test | Outer shell | Outer + Wave | + Wave evolution |
| --- | ---: | ---: | ---: | ---: |
| completed pre-entry | 2025 | 0.697 | 0.667 | — |
| completed pre-entry | 2026 | 0.772 | 0.772 | — |
| forming +60m | 2025 | 0.720 | 0.715 | 0.708 |
| forming +60m | 2026 | 0.762 | 0.755 | 0.749 |

Thus the fixed Wave coordinates did not add stable STOP discrimination beyond the H4/FAST-HA shell.

## Economic regret

The q80/q90 score tails were fixed from earlier training scores and applied to later outer years. They are diagnostics, not candidate thresholds.

At q90:

| Action diagnostic | 2025 delta weighted R | 2026 delta weighted R | 2025 L6+ retention | 2026 L6+ retention |
| --- | ---: | ---: | ---: | ---: |
| reject completed-Wave high-risk entries | -3.74R | +7.47R | 97.5% | 91.1% |
| exit forming-Wave-evolution high-risk Children at +60m | -5.26R | +5.46R | 98.2% | 98.8% |

The sign changed by year. The forming q90 diagnostic reduced the 2025 maximum stop streak from five to three but did not reduce the 2026 maximum streak of three. This is not a stable strategy improvement.

## Decision

- Do not integrate Wave v0.5 as an entry veto, +60m exit, score, or threshold.
- Do not rescue the result by scanning bandwidths, density thresholds, checkpoints, model families, or direction exclusions on consumed history.
- Keep Wave Candle as a representation and observation tool only.
- A future V11 hypothesis must explain what information it adds beyond outer H4/FAST-HA geometry and must be frozen before new chronology is observed.

## Reproduction

- script: `research/v11/analyze_v11_wave_edge.py`;
- script SHA-256: `1d288eae2133504db862e22640156ea90cec687d4360e3b72d2954f69ec7f080`;
- script size: `29,233` bytes;
- local output: ignored `output/v11_wave_edge_20260922/`;
- Python compile: passed;
- all large ledgers and score outputs remain local and have no authority.
