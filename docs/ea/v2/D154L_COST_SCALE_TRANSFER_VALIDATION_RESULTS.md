# D-154L — Cost-Scale Transfer Validation Results

Status: COMPLETE / VALIDATION-ONLY / NO STRATEGY CHANGE  
Date: 2026-08-23

## Frozen hypothesis

Primary market-period metric:

```text
median spread / Root-contact->accepted-CHOCH mean M1 true range
```

Expected direction:

```text
higher relative execution friction -> lower Fill->+1R survival
```

No threshold was registered.

## Integrity

```text
GOLD23 context      66 fills: 34 +1R / 31 SL / 1 censored
GOLD24 validation   52 fills: 24 +1R / 28 SL
BTC25 validation   127 fills: 60 +1R / 67 SL
SILVER25 validation 46 fills: 18 +1R / 28 SL
```

D154K snapshot coverage was complete. No execution divergence or cancel rejection.

## Results

```text
cell       survival     spread/TR   spread/R    spread/FVG
GOLD23     52.3%        0.5487      0.0423      0.8966
GOLD24     46.2%        0.5723      0.0425      0.8311
GOLD25     56.6%        0.3417      0.0281      0.4615
BTC25      47.2%        1.0147      0.0632      1.0256
SILVER25   39.1%        1.7011      0.1471      2.0992
CADJPY25   26.5%        2.1255      0.1496      2.6875
```

Within the 2025 cross-market panel:

```text
spread/TR: GOLD < BTC < SILVER < CADJPY
survival:  GOLD > BTC > SILVER > CADJPY
```

The discovery endpoints GOLD25/CADJPY25 were not relabeled as validation; BTC25 and SILVER25 independently fell between them in the registered direction.

## Decision

```text
cross-market cost-scale mechanism = SUPPORTED
per-trade spread threshold         = NOT SUPPORTED
universal temporal determinant     = NOT ESTABLISHED
```

GOLD23/GOLD24/GOLD25 show that similar cost scale can coexist with different yearly performance. Execution friction is an important transfer/viability mechanism, not the whole strategy edge.
