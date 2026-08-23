# D-154UL — Ultra Low Execution-Environment Validation

Status: ACTIVE VALIDATION / NO STRATEGY CHANGE  
Date: 2026-08-23  
EA: existing `2.11R0L11 / D154M`  
Account environment: XM Ultra Low  
Ultra Low symbols:

```text
GOLD#
BTCUSD#
SILVER#
CADJPY#
```

## Why this phase precedes D154N

The Standard-account research established:

1. D154K/L:
   relative spread to the causal M1 reaction/FVG/risk scale is strongly associated with cross-market transfer degradation.
2. D154M:
   post-Fill executable quote-side friction is a direct causal loss mechanism in CADJPY and BTC, but not a universal explanation because SILVER had zero post-Fill quote flips.

The live research environment has now changed from the prior Standard account to Ultra Low. That creates a natural execution-environment experiment before adding more instrumentation.

D154N remains queued. Do not change D154N's hypothesis from D154UL results.

## Frozen Standard 2025 benchmark

```text
          fills  actual +1R    D154M shadow +1R   spread/TR   spread/R   spread/FVG
GOLD       53     30 = 56.6%    31 = 58.5%         0.3417     0.0281     0.4615
BTCUSD    127     60 = 47.2%    67 = 52.8%         1.0147     0.0632     1.0256
SILVER     46     18 = 39.1%    18 = 39.1%         1.7011     0.1471     2.0992
CADJPY    113     30 = 26.5%    47 = 41.6%         2.1255     0.1496     2.6875
```

D154M Standard SL-first -> shadow +1R flips:

```text
GOLD      1
BTCUSD    7
SILVER    0
CADJPY   17
```

These values are historical evidence. Never overwrite them with Ultra Low results.

## Ultra Low validation

Same calendar year:

```text
2025-01-01 .. 2025-12-31
Every tick based on real ticks
```

Run:

```text
GOLD#
BTCUSD#
SILVER#
CADJPY#
```

Same EA/research settings:
- V3E mode 9;
- EM OFF;
- D151 ON;
- D154K ON;
- D154M ON;
- other D154 research toggles OFF.

## Non-interference

Before full-year evidence:

```text
GOLD# Q1 2025: D154K+M OFF vs ON
CADJPY# Q1 2025: D154K+M OFF vs ON
```

Strip D154K/D154M research rows and normalize logger counters. Canonical strategy rows must match exactly.

## Primary natural-experiment questions

For each Standard symbol vs its `#` Ultra Low counterpart:

1. Did `spread / reaction M1 TR` fall?
2. Did `spread / actual 1R` fall?
3. Did `spread / selected FVG width` fall?
4. Did actual Fill->+1R survival rise?
5. Did D154M `SL_FIRST -> shadow PLUS_1R` flips fall?
6. Did the number/population of actual fills change materially?

The sixth question matters: a lower-spread feed can alter which pending orders actually fill, so Standard vs Ultra Low is an environment comparison, not automatically a paired-trade experiment.

## Interpretation boundaries

A supportive causal pattern would be:

```text
relative spread decreases
+
actual +1R survival increases
+
D154M post-Fill quote flips decrease
```

especially in markets where Standard friction was high.

But:
- do not require all markets to respond identically;
- do not fit a spread threshold;
- do not declare Ultra Low universally superior from one year;
- do not compare only net P/L because commission/contract/account economics are not yet normalized in this audit;
- do not reinterpret different fill populations as exact matched trades.

No Entry/SL/TP/sizing/SP/EM rule changes are authorized.

## Data synchronization

The `#` symbols are separate MT5 symbols. The Strategy Tester may need to download their historical real-tick data on first use.

Do not delete the old Standard-symbol history. Let MT5 synchronize the `#` symbol history automatically during the first tests. This preserves the prior Standard environment as historical evidence.
