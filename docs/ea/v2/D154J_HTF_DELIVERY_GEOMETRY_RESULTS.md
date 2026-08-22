# D-154J — HTF Delivery Geometry Results

Status: COMPLETE / NO STRATEGY CHANGE  
Date: 2026-08-23  
Population: GOLD25 + CADJPY25 actual filled EXTERNAL_CONTINUATION trades  
Control: V3E mode 9, EM OFF, D151 ON

## Integrity

Both full-year runs were execution-clean and the dual-symbol Q1 D154J OFF/ON comparison passed non-interference.

```text
GOLD25    53 fills: 30 PLUS_1R / 23 SL_FIRST = 56.6%
CADJPY25 113 fills: 30 PLUS_1R / 83 SL_FIRST = 26.5%
```

## Primary result

The hypothesis that CADJPY underperforms because entries occur later / more exhausted inside the active protected-to-external HTF span is rejected.

Descriptive Fill-stage medians:

```text
plan progress:
GOLD      ~0.585
CADJPY    ~0.501

remaining fraction:
GOLD      ~0.381
CADJPY    ~0.499

remaining distance in initial R:
GOLD      ~1.59R
CADJPY    ~2.44R
```

CADJPY generally entered with more, not less, HTF room remaining. Root-contact -> CHOCH progress change was also similar across the two markets.

The performance gap remained large after matching direction and broad nested map state. Current HTF structural labels and protected/external progress therefore do not explain the transfer gap.

No HTF progress threshold, symbol-specific gate or baseline change is promoted from D-154J.
