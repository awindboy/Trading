# V9 Paper Trading Journal — April 2025 Frozen Summary

Date frozen: `2026-09-09`
Causal month-end boundary: `2025-04-30 23:58`
Status: `APRIL COMPLETE / P038 OPEN CARRY`

## Closed trades

| Trade | Side | Result |
|---|---|---:|
| P006 | LONG | +29.70R |
| P007 | SHORT | -2.03R |
| P008 | LONG | -4.55R |
| P009 | SHORT | +0.29R |
| P010 | SHORT | -1.00R |
| P011 | SHORT | -1.72R |
| P012 | SHORT | -1.33R |
| P013 | SHORT | -1.54R |
| P014 | SHORT | -1.19R |
| P015 | LONG | -0.86R |
| P016 | SHORT | -2.96R |
| P017 | LONG | +16.77R |
| P018 | SHORT | -1.93R |
| P019 | LONG | -2.21R |
| P020 | SHORT | -1.36R |
| P021 | LONG | -0.69R |
| P022 | LONG | -1.32R |
| P023 | LONG | -0.49R |
| P024 | LONG | -1.24R |
| P025 | SHORT | -1.29R |
| P026 | LONG | -1.11R |
| P027 | SHORT | -0.59R |
| P028 | LONG | -1.20R |
| P029 | LONG | +24.17R |
| P030 | SHORT | -2.36R |
| P031 | LONG | +23.05R |
| P032 | SHORT | +10.58R |
| P033 | SHORT | -1.32R |
| P034 | LONG | -0.98R |
| P035 | SHORT | -1.45R |
| P036 | SHORT | -4.39R |
| P037 | LONG | -1.17R |

Closed sum: `+62.28R` including March carry P006.
April-new-entry closed sum: `+32.58R`.

These R values use the contemporaneous April accounting references. They are frozen historical evidence and must not be recalculated as if the May Hard-SL rule had existed.

## Open carry P038

```text
Trade: P038
Side: SHORT
Entry: 3326.04
April legacy accounting reference: 3331.29
April month-end price: 3288.42
Month-end MTM: about +7.17 legacy-R
MFE through April: 3266.86 / about +11.27 legacy-R
Status: OPEN / CARRY TO MAY
```

May transition rule: prospectively arm 3331.29 as a one-time protective stop at the May boundary before any May reveal. It is a grandfathered risk cap, not an initial Hard SL and not stop-placement evidence. Do not rewrite April history.

## Mandatory postmortem tags

```text
LARGE PARENT WINNERS: P006, P017, P029, P031, P032
SEVERE GIVEBACK: P009, P035, P036
SAME-AUCTION CHURN: P019-P023
RETRY MATCHED FAMILY: P024/P026/P028 -> P029
REVIEW-LATENCY CONTAMINATION: P007/P008/P016/P030/P036 (at minimum explicitly identified during replay)
```

For detailed diagnosis read `results/V9_APR25_COMPLETION_AND_PIPELINE_POSTMORTEM_20260909.md`.
