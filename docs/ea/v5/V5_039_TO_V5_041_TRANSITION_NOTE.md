# V5-039 to V5-041 — Transition Note to V6

Status: `TRANSITIONAL SCRATCH / NOT CLAIM-GRADE`
Date: `2026-08-28`

## V5-039

A causal SPDR GLD physical-holdings-flow scratch runner was prepared with next-day activation and controls.
It was not completed because the project direction was reset away from unrelated external-variable hunting.

```text
NO RESULT
NO PASS/FAIL
```

## V5-040

The project returned to the user's intended direction: modern methods to solve V3's generalization limitation.

Exact V3-003C broad event parity was reconstructed:

```text
2023 84
2024 86
2025 67
```

A GOLD-only event-conditioned raw-path diagnostic remained chronologically unstable:

```text
2024 ensemble-style AUC ~0.456
2025 ensemble-style AUC ~0.572
pooled OOF             ~0.504
month-cluster CI       ~0.424..0.579
mirror                 ~0.476
```

The initial formal aeon runner design was caught before use with implementation/spec concerns; later local raw-convolution/Ridge diagnostics produced the summarized transitional results. Therefore treat these numbers as scratch evidence, not a claim-grade frozen model benchmark.

## Label/path audit

Symmetric path taxonomy:

```text
W_CONTINUE +1->+2 before 0
W_GIVEBACK +1->0 before +2
L_RECOVER  -1->0 before -2
L_CONTINUE -1->-2 before 0
```

Counts:

```text
                 2023  2024  2025  total
W_CONTINUE         22    20    18    60
W_GIVEBACK         21    26    17    64
L_RECOVER          22    18    19    59
L_CONTINUE         19    22    13    54
```

Refined labels did not remove chronological instability.

## V5-041 cross-market context

Synchronized same-broker context:

```text
GOLD# + XAUEUR# + USDJPY#
```

reduced/reversed some of the 2024 weakness and improved 2025 robust-endpoint discrimination:

```text
                         GOLD only   +context
2024 extreme AUC           0.486       0.514
2025 extreme AUC           0.645       0.709
2024 ordinal rho          -0.034      +0.030
2025 ordinal rho          +0.084      +0.191
```

But real context had roughly 30 channels versus about 10 for GOLD-only.
The mandatory same-capacity `GOLDx3` placebo was not completed.

This unresolved question is the exact starting point of V6-001A.
