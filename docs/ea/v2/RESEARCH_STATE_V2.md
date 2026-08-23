# V2 Research State

Last updated: 2026-08-23  
Phase: `D-154N PENDING-TO-FILL QUOTE-SIDE DELAY / DEPTH AUDIT`  
Current tested base: `2.10R0L10 / D154K`  
Target build: `2.11R0L11 / D154M`  
Authority: `docs/ea/v2/AGENTS_V2.md`  
2021: `KEEP UNTOUCHED`

## Primary objective

Build a robust continuation strategy with:
- realized WR >=50% as a baseline condition;
- average winner meaningfully >1R;
- positive cost-adjusted expectancy;
- persistence across periods and markets.

No threshold stack is justified merely because it raises in-sample WR.

## Axis A — Fill -> +1R Entry survival

Status: **PRIMARY BOTTLENECK / EXECUTION-TRANSFER MECHANISM UNDER CAUSAL TEST**

2025:
```text
GOLD25    56.6%
BTC25     47.2%
SILVER25  39.1%
CADJPY25  26.5%
```

D154A-J removed many M1/HTF timing and geometry explanations.

D154K/L currently support one cross-market mechanism:
```text
higher broker spread relative to causal M1 reaction scale
-> lower cross-market Fill->+1R survival
```

This is not yet a per-trade Entry gate.

D154M now asks whether actual quote-side barrier mechanics directly flip SL-first outcomes.

## Axis B — +1R -> +2R winner continuation

Keep separate.

Lower M30 protected-to-external progress at +1R remains the strongest descriptive continuation relation. It is not Entry authority.

## Axis C — post+1R / post+2R profit preservation

V3E `BANK_2R_LOCK_ONE` remains provisional research reference only.

## D154M governance

Population:
```text
actual filled EXTERNAL_CONTINUATION
```

Actual outcome:
```text
D151 executable-side Fill->+1R / original-SL race
```

Shadow:
```text
LONG ASK vs same +1R / SL
SHORT BID vs same +1R / SL
```

No fill/barrier modification. No zero-spread synthetic price.

Primary result:
```text
count and rate of ACTUAL_SL_TO_SHADOW_PLUS_1R
```

Report by market and direction.

Do not:
- optimize a spread threshold;
- exclude a symbol from the same sample;
- widen SL;
- change Entry/FVG;
- infer cost is the only temporal regime variable.


## D154M result

Post-Fill quote-side friction is causal but partial. CADJPY25 had 17/83 actual SL-first trades flip to entry-side-quote +1R, BTC25 had 7/67, while SILVER25 had 0/28. D154L cost-scale remains a market-level viability relation, but cannot be equated with this one barrier mechanism.

## D154N governance

Test pending-placement -> opposite-quote first Entry touch -> executable-quote Entry touch / actual Fill delay and depth. No pending offset, spread threshold, direction exception or strategy change.
