# V9 ERA4 Multi-Child Runtime Checkpoint

Date: `2026-09-14`
Status: `RESEARCH CHECKPOINT / PROPOSED FREEZE CANDIDATE / NOT LIVE AUTHORITY`
Base GitHub HEAD: `4d40f095d8a7e0ccbdd74ac380d8ac29411cbc03`
Market: `GOLD#`

## 1. Data scope

By explicit user override, the complete supplied M1 period is research-consumable:

`2022-01-03 01:00` through `2026-08-28 23:57`.

The authoritative M1 SHA remains:

`626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

Uploaded H4 was checked against H4 reconstructed from authoritative M1 across all 7,199 H4 buckets; OHLC mismatch count was zero.

## 2. Era-scale definition

```text
ERA_SCALE(t)
= previous fully completed H4 Wilder ATR180
```

Structural-risk ratio:

```text
ERA_RISK = abs(Entry - causal H1 structural SL) / ERA_SCALE(t)
```

Entry eligibility candidate:

```text
ERA_SCALE available
AND valid causal H1 structural SL
AND ERA_RISK <= 4
```

If `ERA_RISK > 4`, no Child is opened. The Hard SL is never moved to `4 x ATR180`; the original H1 structural price remains the only Hard SL.

## 3. Why ATR180

Across calendar years, absolute H1 structural SL distance changed dramatically, while median `SL/ATR180` remained approximately stable around 1.66-1.85.

Among compared H4 ATR windows `14/60/120/180/240/360`, ATR180 produced the lowest calendar-year coefficient of variation for the median normalized structural distance in the full-era study.

The >4 ATR180 tail was strongly loss-making in fixed-size price PnL and was already negative before the extreme 2026 cases.

## 4. Exact causal runtime result

Runtime:

`scripts/v9_multichild_era_runtime.py`

Runtime computes ATR180 only from finalized H4 bars and evaluates the cap at the actual eligible Arrival. It does not preload a future ATR value.

Full sequential result:

```text
accepted Children                  1,250
resolved                           1,101
ambiguous                            148
rejected ERA_RISK > 4                85
ATR180 warm-up rejections             29
no-valid-H1-structure rejections        2
```

Accepted trade core was compared with the independent full-era replay + causal ATR180 mapping:

```text
Entry timestamp mismatch   0
Direction mismatch         0
Entry price mismatch       0
Hard SL mismatch           0
SL distance mismatch       0
Status mismatch            0
Exit timestamp mismatch    0
Exit price mismatch        0
R mismatch                 0
ATR180 mismatch            0
```

Replay was completed through serialized split/resume state across the full 1,648,545-row M1 source.

## 5. Economic result — fixed-size price PnL first

All-Child / hold-until-CHALLENGED:

```text
Gross PnL        +10,968.57
PF                 1.887
WR                43.96%
DD              1,085.58
1x spread PnL   +10,777.57
1x spread PF       1.864
3x spread PnL   +10,395.57
3x spread PF       1.820
Ambiguity worst  +6,792.31
Worst-case PF       1.411
```

This packet treats normalized R as secondary diagnostics. Fixed-size GOLD price PnL is the primary economic comparator unless future authority explicitly chooses equal-money-risk position sizing.

## 6. Direction split after ERA4

```text
UP     +11,755.92 / PF 3.235
DOWN      -787.35 / PF 0.889
```

Do not respond by banning SHORT. See the path-asymmetry diagnostic.

## 7. Current status

ERA4 is a strong research freeze candidate for structural-risk eligibility.

The exposure/management baseline should no longer be assumed to be blind all-Child challenge holding; the role-based comparator in the companion diagnostic materially improves direction robustness and drawdown without a numeric Child cap.
