# V11 independent skeleton and progress-ladder diagnostic

Date: `2026-09-23`

Status: `CONSUMED-DATA CLOSURE DIAGNOSTIC / NO TRADE AUTHORITY`

## Why this diagnostic matters

V11 Stage 0-5 changed capital handling around the selected V10 R7G ledger. They
were useful portfolio diagnostics but not a genuinely new strategy skeleton.
This final experiment removed that dependency:

- no V10 event ledger;
- no V10 stop label;
- no FAST HA in the primary candidate definition;
- candidates reconstructed directly from raw chronological M1 and completed H4.

## Source

- GOLD# M1 rows: `1,648,545`;
- range: `2022-01-03` through `2026-08-28`;
- completed H4 bars: `7,199`;
- duplicate timestamps: `0`;
- invalid OHLC rows: `0`;
- raw source SHA-256:
  `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`.

All observations are consumed development evidence.

## Primary skeleton

`STD_SLOW_MEMORY` uses agreement between STD and SLOW HA to establish or reverse
the Parent phase. Disagreement preserves the existing phase memory. One Child is
opened per phase reversal. Its Hard SL is the opposite raw-H4 extreme of the
causal transition bridge.

This was a true candidate-generation change, not a filter over V10 selections.

## Phase comparison

| Skeleton | Journeys | Own-stop rate | Total R |
| --- | ---: | ---: | ---: |
| FAST reference | 2,048 | 47.06% | +109.49R |
| STD | 1,558 | 53.38% | +222.56R |
| SLOW | 1,050 | 52.34% | +138.51R |
| STD+SLOW memory | 1,018 | 41.85% | +173.85R |

STD+SLOW memory recorded 426 stopped journeys, 28.68% win rate, maximum stop
streak 9, and median initial risk 0.897 causal H4 ATR. Its lower stop rate cannot
be read in isolation because the bridge-based Hard SL is wider than the simpler
comparators. More importantly, stability failed: SHORT totaled `-13.93R` and
partial 2026 totaled `-1.10R`.

## Raw-settlement progress ladder

The second experiment kept every STD+SLOW-memory candidate and varied only the
capital release:

| Policy | Units | Stopped units | Full-size stops | Total R |
| --- | ---: | ---: | ---: | ---: |
| one unit | 1,018 | 426 | n/a | +173.85R |
| immediate three units | 3,054 | 1,278 | 426 | +521.56R |
| progress ladder | 2,009 | 601 | 43 | +294.42R |

The ladder reduced maximum full-size stop streak to 2, but R per exposed unit
fell from `0.1708` for one-unit participation to `0.1466`. Ladder win rate was
23.58%, SHORT totaled `-53.69R`, and partial 2026 totaled only `+0.90R`.

## Finding

The independent skeleton demonstrates two separate facts:

1. changing HA phase memory can change the stop population, but the observed
   advantage is entangled with structural stop width and is not side/year robust;
2. a progress ladder can reduce full-size stop clusters by staging exposure, but
   it does not identify or remove stopped Children.

V11 therefore closes without a validated stop-recognition mechanism, trading
rule, or production EA. Its durable outputs are the Wave Candle observation
instrument, the causal tooling discipline, and the requirement to audit stopped
and right-tail capital jointly.

## Reproduction

- phase space: `research/v11/analyze_v11_new_skeleton_phase_space.py`;
- progress ladder: `research/v11/analyze_v11_new_skeleton_progress_ladder.py`;
- large outputs: ignored
  `output/v11_new_skeleton_phase_space_20260923/` and
  `output/v11_new_skeleton_progress_ladder_20260923/`.

Retained hashes:

- phase summary:
  `dbb508951cb03493e4c6c16e29413baea7e3857976adf5846058ea3eb60210a5`;
- phase journeys:
  `a2f7d942d97a7881882aaf8f435cc583f0b88a765076b74904f50a49f416eb66`;
- H4 state:
  `282aa0e39645f0cbe24dd55794f7246c28eb35e7b80c308c6834437b81bbb6d2`;
- progress ledger:
  `908446e422dbc5ddc680805e75fe8578959735ec801d23e78c0d244ef65dc408`;
- progress summary:
  `4b92b0c130520eb8f263c86e4ccf341d80c42e43aaa5fd54f3a00b1af25f264d`.
