# V3 Research State

Status: `ACTIVE`
Phase: `V3-003D DUAL RELOAD MODULE RESEARCH`
Date: `2026-08-26`

## Problem statement

Current V2 cannot yet demonstrate the required combination of:
- sufficient sample density;
- >=50% realized WR;
- winner payoff >1R;
- positive cost-adjusted expectancy;
- multi-year / multi-market robustness.

The immediate bottleneck is not only profitability. The current deterministic
Entry architecture itself produces a sparse population.

Therefore V3 changes the research unit from:

```text
current EA fills
```

to:

```text
raw-market event/opportunity universe
```

## What is preserved

Preserved from the project:

- GitHub as Single Source of Truth;
- no look-ahead;
- discovery/validation separation;
- causal event availability;
- MT5 as final execution validator;
- exact execution concerns remain separate;
- Entry survival vs winner continuation vs exit separation;
- V2/V3E exit evidence is not discarded.

## What is reopened

V3 may independently test:

- alternative swing definitions;
- alternative external/internal structure state;
- local live-swing CHOCH;
- M1 vs M5 vs adaptive trigger;
- richer liquidity families;
- alternative Root/context definitions;
- continuation, reversal and internal-rotation strategy families;
- FVG/OB execution selection;
- session/retest architecture;
- strategy-derived market suitability.

No existing V1/V2 definition is privileged merely because it is already coded.

## Dataset governance

Discovery:
`2023-2025`

Validation vault:
`2022`

Untouched:
`2021`

The exact use of each dataset must be written into every V3 experiment record.

## Initial benchmark

The first V3 benchmark is not P/L.

It is a frequency/coverage census answering:

1. How many independent structure/reaction opportunities exist?
2. Where does V2 discard them?
3. How many causal Entry candidates are produced by alternative trigger families?
4. Are candidate counts stable across 2023, 2024 and 2025?

Only after this census do we compare Entry-survival economics.

## Current no-authority list

No V3 strategy has production authority.

No current finding authorizes:
- new V3 Entry;
- new V3 SL;
- new V3 TP;
- live AI/ML inference;
- 2022/2021 inspection for discovery;
- replacement of the V2 EA.

## V3-002 conclusion / V3-003 active state ??2026-08-25

Current research classification:

```text
raw-data laboratory                    ACTIVE
sweep-only Entry edge                  REJECTED
mandatory FVG-retest Entry             REJECTED / DEMOTED
FVG as displacement footprint          PROMISING CONTEXT ONLY
fixed-horizon direction model          REJECTED
trade-level winner/loser ML mining     STRUCTURAL_CEILING_SUSPECTED
forced reversal on HTF conflict        REJECTED
selective continuation                 PROMISING / NOT VALIDATED
broad SL widening                      REJECTED
auction-state reconstruction           ACTIVE NEXT PHASE
cross-market expansion                 DEFERRED
```

The active question is no longer:

```text
Which sweep/FVG parameter makes the best trade?
```

It is:

```text
Which GOLD auction state is active,
and which strategy module belongs to that state?
```
## V3-003D current state — dual reload modules (2026-08-26)

Current classification:

```text
V3_RELOAD_CANDIDATE_A                     FROZEN DEVELOPMENT BENCHMARK
Candidate A as strategic-destination rule DEMOTED / LOCAL-TIMING BENCHMARK
R-only research objective                 DEMOTED
Module L deep reload requalification      PROMISING / SMALL SAMPLE / REPRODUCIBILITY NEXT
Module H structural-pullback 5R            PROMISING / REPRODUCIBILITY NEXT
Module H 10R extension                     DEFERRED
atomic same-bar recovery                   SUPPORTED VS DELAYED NEGATIVE CONTROL
generic M1 early trigger                   REJECTED
delayed-recovery equivalence               REJECTED
broad SL widening                          REJECTED
M1/M5 structural runner trailing           REJECTED
+1R/+2R BE for Module H                    REJECTED
+3R BE for Module H                        PROMISING CONTROL
true deterministic destination hierarchy   UNSOLVED
other auction-state modules                DEFERRED BY CURRENT USER ROUTING
2022 validation                            CLOSED
2021                                       UNTOUCHED
```

Research must now report both economic and physical market scale:

```text
R
absolute GOLD dollars
M30 ATR units
D1 ATR units
time / holding period
spread/risk
scenario/context invalidation
```

The next mandatory work is to reproduce Module L/H current-session discovery evidence in
committed scripts and immutable ledgers before further strategy tuning.

## V3-003E current state — replay restored, dual-module improvement active

Current classification:

```text
V3_RELOAD_CANDIDATE_A                  FROZEN DEVELOPMENT BENCHMARK
Candidate-A integrated replay          REPRODUCED / COMMITTED
Module L deep requalification          REPRODUCED / VERY SMALL SAMPLE
Module L protected-runner payoff       CURRENT PRIMARY L PAYOFF CONTROL
Module L generic-pivot expansion       REJECTED
Module L mentor-wave expansion         EXPLORATORY / SMALL
Module H k2-50% base                    REPRODUCED
Module H direct ownership transfer     STRONG H-SPECIFIC DISCOVERY
Module H BOTH exclusion                PROMISING SHADOW / NOT FROZEN
Module H +3R -> BE                     PRIMARY H PROTECTION CONTROL
Module H +3R 25% harvest               SECONDARY POSITIVE-FREQUENCY CONTROL
H -> later L requalification           REPRODUCED EPISODE PHENOMENON
combined H/L economics                 DESCRIPTIVE ONLY
H swept-liquidity body-close exit      PENDING / STARTED NOT COMPLETED
H +2R 50% protection                   PENDING / STARTED NOT COMPLETED
true deterministic destination         UNSOLVED
other auction-state modules            DEFERRED BY USER
2022                                   CLOSED
2021                                   UNTOUCHED
```

Current reproduced Level-A headline:

```text
L:
11/11 positive under checkpoint-50%-residual2R
mean +1.131R
7/11 residual +2R

H direct+notBOTH shadow:
40 trades
14 TP5
23 SL
3 BE
+47R
+1.175R/trade

descriptive H + L combined:
46 episodes
positive 52.17%
avg positive +3.249R
EV +1.292R
max negative streak 5
max DD ~7R
```

These are discovery results only. No 2022 validation, exact-tick authority or EA promotion
exists.

Immediate priority:

```text
1. verify V3-003E parity on session start
2. finish the two interrupted H experiments
3. continue H remaining-loss taxonomy without sacrificing +5R winners
4. expand L only through meaningful liquidity semantics
5. formalize deterministic H/L episode risk/exposure
```
