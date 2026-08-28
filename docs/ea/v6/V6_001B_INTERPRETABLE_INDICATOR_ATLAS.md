# V6-001B — Interpretable Indicator Atlas

Status: `ACTIVE INDICATOR-FIRST LINE / INITIAL EXPLORATORY ATLAS COMPLETE / NO STRATEGY AUTHORITY`  
Date: `2026-08-28`  
Primary market: `GOLD#`  
Population: exact V3-003C broad event anchor  
Production authority: `NONE`

## 1. User-intent correction

V6 is not an AI/ML research program.

The active intent is:

> use interpretable technical/market-state indicators to understand and overcome the generalization limitation exposed by V3.

AI/ML classifiers, representation learning, convolution probes, or model-capacity comparisons are not active V6 research priorities.

`V6-001A` remains a historical/preregistered cross-market cleanup child but is SHELVED and must not be executed unless the user explicitly reopens it.

## 2. Research object

Preserve the exact broad V3 event population and attach causal, completed-bar indicators to the event.

Broad event parity:

```text
2023 84
2024 86
2025 67
TOTAL 237
```

Path labels:

```text
L_CONTINUE
L_RECOVER
W_GIVEBACK
W_CONTINUE
```

Stage contrasts remain separate:

```text
ENTRY_SURVIVAL       = W_* vs L_*
WINNER_CONTINUATION  = W_CONTINUE vs W_GIVEBACK
LOSS_RECOVERY        = L_RECOVER vs L_CONTINUE
```

## 3. Governance

This atlas is an exploratory map, not an indicator tournament.

Rules:

- no AI/ML model;
- no threshold optimization;
- no indicator parameter sweep;
- no timeframe sweep beyond the fixed H1/H4 atlas below;
- no choosing a trading rule from the best pooled number;
- report all tested indicator families;
- decompose by year and direction before interpreting a pooled relation;
- any follow-up filter/regime hypothesis requires a separate frozen child before 2022 or any new validation environment is used.

The first atlas was chosen and described in chat immediately after the user corrected the research direction, before interpreting the resulting values. Because this was not yet frozen in GitHub, its findings are classified `EXPLORATORY ONLY`.

## 4. Fixed indicator atlas

### H1 and H4 price-state indicators

Fixed conventional definitions:

- DMI/ADX(14)
- Aroon(25)
- RSI(14)
- Bollinger %B and Bandwidth(20,2)
- MACD(12,26,9) histogram and 3-bar change
- Stochastic %K(14)
- Williams %R(14)
- ROC(12)
- Donchian(20) relative location
- Keltner width using EMA20 and ATR10
- Choppiness(14)
- ADX 3-bar change
- Bollinger Bandwidth 5-bar ratio

Direction-sensitive values are transformed into event-direction coordinates only; e.g.:

```text
dmi_align = event_dir * (+DI - -DI)
rsi_align = event_dir * (RSI - 50)
```

### H1 participation indicators

Because broker M1 data contains tick volume but no real exchange volume:

- RVOL(20)
- MFI(14) using tick volume
- CMF(20) using tick volume
- normalized OBV 20-bar change

These are broker-feed activity proxies, not physical centralized volume.

## 5. Causal boundary

At each event trigger time:

- only fully completed H1/H4 bars are visible;
- H1 feature availability = H1 bar end;
- H4 feature availability = H4 bar end;
- no current unfinished bar values;
- no future fill;
- no outcome-derived feature.

## 6. First result — simple directional indicators do not solve V3

The initial H1 audit showed that direction-adjusted:

- DMI;
- RSI;
- Aroon;
- Bollinger relative location;
- MFI;
- CMF;
- OBV;
- daily/local participation-style measures

changed sign or materially changed meaning across 2023/2024/2025.

The same conclusion survived when the population was decomposed into Entry survival, winner continuation, and loss recovery instead of using one four-way ordinal score.

Therefore:

```text
add RSI/MACD/DMI/etc as one more directional veto
```

is NOT supported.

This is consistent with the old V3 warning that fixed-horizon momentum and broad price-feature mining did not generalize.

## 7. H4 audit and recursive falsification

At pooled year level, H4 ADX and volatility-width measures initially looked weakly more favorable in stronger paths.

Before promoting that interpretation, the result was decomposed by LONG/SHORT.

Most apparent pooled relations weakened or reversed across direction cells.

The strict atlas summary found only one relation with the same probability-superiority sign across all six `year x direction` Entry-survival cells:

```text
H4 ADX(14): higher in W_* than L_*
probability superiority range = 0.518 .. 0.577
mean absolute deviation from 0.5 ~= 0.044
```

This is extremely weak.

Some cell medians also move in the opposite order even though rank probability remains slightly above 0.5.

Classification:

```text
NOT A FILTER
NOT AN EDGE
NOT VALIDATION-READY
WEAK EXPLORATORY CLUE ONLY
```

The correct interpretation is not `ADX works`.

The only defensible statement is:

> among the standard indicators tested so far, broad H4 trend-strength state is the only dimension that did not immediately reverse sign across all year-direction Entry-survival cells, but the effect is too small to explain V3's collapse by itself.

## 8. What has already been falsified in this atlas

Do not reopen without a distinct causal formulation:

- standalone H1 directional oscillator veto;
- standalone H1 DMI direction filter;
- standalone H1 participation/volume-proxy filter;
- simple H1/H4 relative-location oscillator filter;
- pooled-only interpretation without direction decomposition.

## 9. Next research direction

Do NOT threshold ADX from this result.

The next V6 indicator work should ask a stronger mechanistic question:

> Is V3 failure related to the **transition of market state** rather than the absolute level of a standard indicator?

The next atlas layer should therefore emphasize causally fixed state-change measurements such as:

```text
trend strengthening vs weakening
volatility expansion vs contraction
multi-timeframe state agreement vs disagreement
activity expansion vs decay
relative-location transition rather than oscillator level
```

These remain indicators, but they measure regime transition rather than attempting to predict the trade directly.

A separate child must be frozen before any one transition measure is promoted or tested on 2022.

## 10. Reproduction

Committed/recommended artifacts:

```text
scripts/v6_001b_indicator_atlas.py
docs/ea/v6/ledgers/v6_001b_broad_event_path_ledger.csv
```

Run:

```powershell
python .\scripts\v6_001b_indicator_atlas.py <GOLD_2023_2025_M1_ZIP> .\docs\ea\v6\ledgers\v6_001b_broad_event_path_ledger.csv --out .\v6_001b_indicator_atlas_out
```

Expected event parity is exactly `84 / 86 / 67`.

The script outputs:

```text
indicator_ordinal_by_year.csv
indicator_stage_by_year_direction.csv
indicator_atlas_summary.json
```

No output has production or Entry-rule authority.
