# D-154K — Cross-Scale Reaction / Noise Results

Status: COMPLETE / SHADOW-ONLY / NO STRATEGY CHANGE  
Date: 2026-08-23

## Integrity

Q1 OFF/ON parity passed after the terminal-source synchronization fix.

Full-year:
```text
GOLD25    53 fills: 30 PLUS_1R / 23 SL_FIRST = 56.6%
CADJPY25 113 fills: 30 PLUS_1R / 83 SL_FIRST = 26.5%
```

All fills had D154K snapshots. No execution divergence, cancel rejection, or censoring.

## Key result

Strategy geometry relative to local Root-reaction M1 true range was broadly similar:

```text
                         GOLD25      CADJPY25
1R / reaction TR         11.6660     12.3577
Root width / TR           6.0349      6.4529
FVG width / TR            0.6279      0.7944
reaction efficiency       0.0381      0.0380
```

Execution friction was very different:

```text
spread / reaction TR      0.3417      2.1255
spread / 1R               0.0281      0.1496
spread / FVG              0.4615      2.6875
```

Tick scale:

```text
median spread ticks       40          42
median reaction TR ticks  126.17      20.04
median risk ticks         1748        274
```

Conclusion:
- simple local-noise/risk mismatch is not the explanation;
- relative broker friction is the dominant cross-market scale contrast;
- no per-trade threshold or symbol gate is promoted.
