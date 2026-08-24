# V3 Research State

Status: `ACTIVE`
Phase: `V3-001 RAW DATA LAB BOOTSTRAP`
Date: `2026-08-24`

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
