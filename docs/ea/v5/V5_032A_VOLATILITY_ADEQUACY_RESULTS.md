# V5-032A — First Cross Volatility Adequacy Results

Status: `FAILED FROZEN GATE / CLOSED`
Date: `2026-08-27`
Parent: `V5-030A`

Frozen condition:

```text
ATR14 on completed 240m setup bar
>
median ATR14 of previous 20 completed 240m bars
```

No threshold search was performed.

Development subset:

```text
N                    155
WR                   61.29%
avg positive net R   0.993R
EV                  +0.212R
```

Year EV:

```text
2023  +0.493R
2024  +0.162R
2025  +0.066R
```

Market EV:

```text
BTCUSD#  +0.317R
GOLD#    +0.431R
XAUEUR#  +0.096R
USDJPY#  -0.027R
```

Consumed GOLD# 2022 diagnostic:

```text
N 12 / WR 50.0% / avg positive 0.864R / EV -0.087R
```

The pre-registered gate required:
- at least 240 resolved development trades;
- average positive net >1R;
- three or more positive markets;
- no material deterioration;
- supportive/neutral consumed 2022 diagnostic.

The condition fails on sample size, avg-positive-R and the 2022 diagnostic.

Decision:

```text
REJECT VOL_ADEQUATE
RETURN TO UNFILTERED V5-030A
NO ATR THRESHOLD RESCUE
```
