# V5-001A — Previous-Day Boundary Proxy Results

Status: `OBSERVABLE PROXY INSUFFICIENT`
Date: `2026-08-27`
Strategy authority: `NONE`

## 1. Question

Does first interaction with the previous broker-day high/low behave like a special market boundary after accounting
for a simple internal-range placebo and causal pre-state?

This is a mechanism-discovery test, not a trading-system test.

## 2. Data

Open V5 development data only:

```text
GOLD#    2023-2025
BTCUSD#  2023-2025
XAUEUR#  2023-2025
USDJPY#  2023-2025
```

No V4 external vault data and no GOLD# 2021 were opened.

Ledger:

```text
7,488 events
99 columns
```

By reference:

```text
PD_EXTREME_HIGH   1,781
PD_EXTREME_LOW    1,440
PD_PLACEBO_Q75    2,260
PD_PLACEBO_Q25    2,007
```

Full local CSV.gz SHA256:

```text
1625c49e9d97b229e8f842735fff3d3dd0cf51fa5a459d1394eafa4a5111dc19
```

The full ledger is derived data and is not required in Git. `scripts/v5_001_build_boundary_ledger.py`
reconstructs it from the frozen raw inputs.

## 3. Frozen reference definitions

For each broker-calendar day, previous completed day:

```text
H = previous-day high
L = previous-day low
R = H - L

extreme high  = H, upward first crossing
extreme low   = L, downward first crossing

placebo Q75   = L + 0.75R, upward first crossing
placebo Q25   = L + 0.25R, downward first crossing
```

Only the first crossing of each reference/direction/day is recorded.

The placebo was frozen before full outcome interpretation to challenge the assumption that an outer boundary is special.

## 4. Data quality

Horizon completion:

```text
5m    99.95%
15m   99.92%
30m   99.88%
60m   99.76%
240m  99.35%
```

Gap-through events:

```text
4.82%
```

XAUEUR# contains zero recorded spread in part of the source data; 5.69% of XAUEUR event rows have zero spread.
This study makes no P/L claim, but the limitation is preserved.

## 5. The result that would have fooled us

Unmatched pooled data initially looked favorable to extreme boundaries.

Boundary-signed close displacement normalized by previous-day range:

```text
                    EXTREME     PLACEBO
15m mean             +0.0245     +0.0073
60m mean             +0.0258     +0.0069
240m mean            +0.0385     +0.0239
```

At 60m:

```text
P(resolution > 0)
EXTREME  48.90%
PLACEBO  47.36%
```

The mean is positive while the median is slightly negative. The apparent positive result is therefore tail-sensitive,
not a simple high-probability continuation effect.

If analysis stopped here, V5 could incorrectly promote previous-day extremes.

## 6. Recursive falsification checkpoint 1 — same-day paired placebo

For each extreme crossing, compare the internal Q75/Q25 crossing on the same symbol/day/direction when available.

Paired sample:

```text
2,907 pairs
```

Extreme minus placebo boundary-signed displacement:

```text
15m   -0.00679 previous-day ranges
60m   -0.02971
240m  -0.09987
```

Fraction where extreme displacement is larger:

```text
15m   45.68%
60m   39.59%
240m  27.79%
```

Interpretation:

The pooled extreme advantage was heavily affected by **selection**. Days that manage to reach the previous-day
extreme are already unusual directional days. An internal line crossed earlier on the same day often captures more of
that same move.

This comparison is itself not perfect because the event timestamps differ, so a second control is required.

## 7. Recursive falsification checkpoint 2 — causal pre-state matching

Within each:

```text
symbol x year x direction
```

match every EXTREME event to the nearest PLACEBO event using only causal pre-event state:

- signed 60m return;
- signed 240m return;
- 60m realized volatility;
- 60m directional efficiency;
- 60m/240m range ratio;
- tick-volume z-score;
- time-of-day sin/cos.

No future path enters the match.

Weighted matched result:

```text
60m signed-resolution difference        -0.00271 previous-day ranges
60m pre->post momentum-change difference -0.00009 log-return units
```

Market-year-direction sign stability:

```text
resolution difference negative in 13 / 24 groups
momentum-change difference negative in 15 / 24 groups
```

There is no robust directional boundary-specific effect left.

A weak descriptive clue remains:

```text
matched 60m |resolution| difference = +0.01229 previous-day ranges
positive in 17 / 24 groups
```

This may indicate that extreme interactions occur in somewhat more violent/bifurcating paths, but it is not stable
enough to promote and may still be volatility/normalization related.

## 8. Recursive falsification checkpoint 3 — what does pre-state actually explain?

PCA on the complete EXTREME interaction path:

```text
PC1  46.2%  directional resolution / acceptance axis
PC2  21.8%  two-sided excursion / interaction-intensity axis
PC3   9.5%  early acceptance vs later reversal axis
```

Causal pre-state has only weak/stable association with PC1 direction.

The strongest recurring associations are with PC2 **interaction intensity**:

```text
median market-year Spearman:
pre 15m realized vol       ~ +0.378
tick-volume z60            ~ +0.229
60m/240m range ratio       ~ +0.198
```

The tick-volume and range-ratio signs are positive in all 12 market-years.

But this is not directional alpha. The simpler explanation is that an already active/volatile approach produces a
larger two-sided post-contact path.

Therefore:

```text
predicting HOW VIOLENT the interaction is
!=
predicting WHICH SIDE wins
```

## 9. Recursive falsification checkpoint 4 — confirmation geometry

Five-minute boundary occupancy strongly describes where price is at 60m:

```text
5m beyond fraction <= 0.2 -> mean 60m resolution -0.0728
5m beyond fraction >= 0.8 -> mean 60m resolution +0.1165
```

However the **additional** displacement from 5m to 60m is approximately flat:

```text
low-occupancy group   +0.0017
high-occupancy group  +0.0004
```

Interpretation:

Waiting five minutes makes the current state much easier to classify, but little incremental directional movement is
created by the classification itself.

This recreates a failure mode already seen in V3: confirmation can buy apparent directional certainty by consuming
trade geometry.

No V5 rule may equate `confirmed acceptance` with economic edge without testing what payoff remains **after**
confirmation.

## 10. Corpus regression — return to first principles

The first boundary proxy was chosen for objectivity, not because successful traders uniformly privilege the previous day.

Returning to the source corpus:

- Brandt's rectangle is a prolonged supply/demand equilibrium whose own range creates the relevant boundary.
- Crabel writes that a trading range is first simply a range; the later label is unknown, and the edge is in the
  character inside the range.
- Crabel's mark-up model explicitly starts with release from contraction into expansion.
- Turtle breakouts are rolling extremes, but their success does not require most boundaries to continue; the system's
  payoff architecture tolerates many failed breakouts.

Therefore `previous-day high/low` conflated at least two different ideas:

```text
meaningful balance boundary
vs
generic rolling/extreme trend trigger
```

## 11. Frozen conclusion

Classification:

```text
OBSERVABLE PROXY INSUFFICIENT
```

Specifically:

- Do **not** promote previous-day high/low as a privileged V5 boundary.
- Do **not** interpret the unmatched pooled mean as evidence.
- Do **not** rescue PDH/PDL with session/direction/threshold filters.
- Do **not** call five-minute acceptance an edge.
- Preserve the possibility that **balance-generated boundaries** are a different research object.

V5-001A is closed.

Next phase must be pre-registered before its outcome is inspected.
