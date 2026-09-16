# V10 HA-Primary Risk Architecture Checkpoint

Date: `2026-09-17`  
Status: `CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY`  
Market: `GOLD# ONLY`  
Base GitHub HEAD at study start: `95536c3ef250f4eb217a6490b4e3b10f86dbc7d5`

## 1. Why V10 risk needed to be reopened

The active V10 participation clock is H4 HA, but its Hard SL was inherited from V9:

```text
nearest active causal opposite H1 swing liquidity
```

That stop was semantically natural for V9 liquidity-object entries. V10 instead participates in H4 HA trends and stacks Children as a HA run develops.

Project direction therefore changed:

> H1 liquidity structural SL remains a historical comparator, but it is no longer the preferred active V10 risk design.

The V10 risk question is now:

```text
Where has this HA-trend Child failed strongly enough
that waiting for the final opposite H4 HA close is unnecessary?
```

## 2. Research order

The study deliberately separated three questions:

```text
A. Hard-SL geometry
B. monetary risk allocation per Child
C. aggregate campaign risk ceiling
```

This prevents a sizing improvement from being mistaken for a better stop, or vice versa.

The study population is the existing 1,159 bounded-m3 selected signals. The local research engine reconstructed the H1-structural fixed-lot comparator at:

```text
+14,931.10 / PF 1.558 / DD 2,586.13
```

while GitHub authority records:

```text
+14,827.57 / PF 1.553 / DD 2,638.04
```

The local reconstruction is about `+103.53` higher (~0.7%), so the new SL studies are comparative research evidence rather than a replacement authority ledger.

## 3. SL families tested

Families included:

```text
NHA only / no early Hard SL
current H1 structural comparator
entry PHA raw extreme
entry FAST HA body boundary
entry STD HA body boundary
previous H4 raw extreme
previous FAST HA extreme
previous STD HA extreme
previous SLOW HA extreme
current-run FAST / STD extremes
H1 FAST / STD HA body boundaries
conditional CHOP tightening
```

## 4. Strongest clean HA-native candidate: previous completed H4 STD HA extreme

Definition:

```text
LONG Child
-> previous completed H4 STD HA low

SHORT Child
-> previous completed H4 STD HA high
```

`STD` uses the existing standard HA representation (`w1/a0.50`).

The stop is fixed when the Child is admitted. It is not trailed after entry.

Semantic interpretation:

```text
k1:
new trend participation should not completely violate the previous opposite/transition HA extreme

k2+:
a newly added Child assumes the immediately previous completed HA structure remains valid
```

## 5. Fixed-lot comparison

| Stop family | PnL | PF | DD |
|---|---:|---:|---:|
| NHA only | +12,813.21 | 1.438 | 4,031.26 |
| H1 structural comparator | +14,931.10 | 1.558 | 2,586.13 |
| Previous H4 raw extreme | +14,153.60 | 1.530 | 2,741.10 |
| Previous FAST HA extreme | +14,273.92 | 1.533 | 2,560.13 |
| **Previous STD HA extreme** | **+14,357.83** | **1.538** | **2,552.97** |
| Previous SLOW HA extreme | +14,297.99 | 1.536 | 2,548.44 |
| Entry STD HA body | +12,749.82 | 1.610 | 2,176.85 |
| H1 FAST HA body | +8,935.57 | 1.523 | 1,285.21 |

The important result is not that the previous-STD stop beats every comparator. It is that an H4 HA-native stop preserves most of the H1-liquidity comparator economics without V9 liquidity semantics.

## 6. Stop geometry

Current H1 structural comparator:

```text
median distance 30.24
P10 roughly 12.36
```

Previous H4 STD HA extreme:

```text
valid 1,158 / 1,159
invalid 1
P1 4.55
P5 8.21
P10 10.72
median 28.85
P90 68.65
```

The overall distance scale is surprisingly close to the inherited H1 structural stop.

This matters because the candidate does not achieve similar economics merely by becoming universally loose or universally tight.

## 7. Why HA body stops are not enough

Entry/H1 HA body boundaries often reduce fixed-lot DD and can look attractive, but their lower stop-distance tail is extremely small.

Example H1 FAST HA body:

```text
median distance ~6.75
P1 ~0.18
observed minimum ~0.03
```

With money-risk sizing this can imply extreme lot sizes.

Therefore:

```text
"tighter stop"
!=
"better risk design"
```

A V10 Hard SL must be both:

```text
semantically meaningful invalidation
AND
stable enough to size money risk against
```

## 8. Conditional CHOP tightening

A consumed-data post-hoc candidate used:

```text
normal regime
-> previous H4 STD HA extreme

CHOP-risk regime
-> tighter H1 FAST HA body / H4 raw fallback
```

Fixed-lot result:

```text
PnL +15,611.10
PF 1.700
DD 1,308.27
June approximately -231
```

However:

```text
P1 stop distance ~0.37
minimum tail reaches micro-stop territory
87 eventual NHA winners were cut
about +4,149.89 gross eventual-NHA winner PnL was cut
```

This creates monetary-risk sizing / leverage instability and is not ready for promotion.

Current interpretation:

> CHOP-aware tighter invalidation is a valid research lane, but admission/NEUTRAL should solve most churn before the stop layer is made aggressively tight.

## 9. SL cannot solve reversal churn alone

For the shortest final FAST runs, replacing H1 structural with previous-STD HA extreme did not materially remove the large loss pool.

Therefore:

```text
reverse-admission layer
-> avoid repeated bad flip entries

Hard-SL layer
-> control the loss of a Child that was admitted anyway
```

must remain separate.

## 10. Money-risk sizing

The current fixed-lot research mapping:

```text
W1 -> 0.01 lot
W3 -> 0.03 lot
```

does not equalize account risk because stop distance varies.

The new candidate interpretation is:

```text
1 risk unit = r% of current equity

W1 -> 1 risk unit
W3 -> q risk units

actual lots
= desired money risk / broker-value-of-stop-distance
```

`r` and `q` are not promoted constants.

## 11. Equal Child risk vs W-weighted risk

With previous-STD HA stop:

### Every selected Child = 1 risk unit

```text
+170.80 risk-R
PF_R 1.382
DD 28.67 risk-R
max committed 5 risk units
```

### W1 = 1 risk unit, W3 = 3 risk units

```text
+401.88 risk-R
PF_R 1.467
DD 60.21 risk-R
max committed 12 risk units
```

The W3 cohort had better Child quality in this consumed sample:

```text
W1 average ~+0.095R / Child
W3 average ~+0.201R / Child
```

The W3 risk multiplier scan improved monotonically up to the tested `3.0` endpoint, but that endpoint is not promoted because the W map itself is already a consumed-data research construct.

## 12. Campaign aggregate risk ceiling

For live/open Children in one campaign:

```text
campaign committed risk
= sum(each Child's initial money-risk budget still alive)
```

Candidate constraint:

```text
campaign committed risk <= C risk units
```

`C` is a risk ceiling, not an alpha feature.

### Previous-STD stop + W-proportional risk, partial size-down

| Cap | Total R | PF_R | DD_R | Entries | Max committed |
|---:|---:|---:|---:|---:|---:|
| 3 | +223.67 | 1.347 | 43.78 | 744 | 3 |
| 4 | +284.52 | 1.380 | 52.69 | 1,028 | 4 |
| 6 | **+368.31** | **1.441** | 58.78 | 1,078 | 6 |
| 8 | **+400.02** | **1.467** | 60.21 | 1,153 | 8 |
| 10 | +401.54 | 1.467 | 60.21 | 1,158 | 10 |
| 12 / no effective cap | +401.88 | 1.467 | 60.21 | 1,158 | 12 |

The noteworthy observation is that reducing maximum committed risk from 12 to 8 units retained almost all consumed-data R. A cap of 6 retained roughly 91.6% of no-cap R while halving the maximum committed risk.

Do not promote `6` or `8` from this scan.

## 13. Partial size-down vs skip

When remaining campaign budget is less than the desired new Child risk:

```text
PARTIAL:
allocate the remaining risk budget

SKIP:
reject the new Child completely
```

At loose caps the results are similar. At tighter caps the partial approach preserved more expectancy. Example around cap 4:

```text
partial +284.52R
skip    +263.95R
```

This makes partial risk allocation the cleaner working comparator, not an authority rule.

## 14. Interpreting account-percent risk

If:

```text
1 risk unit = r% of equity
```

then a W-proportional mapping would mean:

```text
W1 = r%
W3 = 3r%
Campaign cap C = C*r%
```

The value of `r` should not be optimized for raw PnL. It is a risk-appetite / acceptable-DD decision.

In the consumed previous-STD W-proportional result, closed-sequence DD was about `60.21 risk units`. A rough linear interpretation illustrates why a W1 base of 1% would be very aggressive; exact compounded-equity and simultaneous-exposure simulation remains separate work.

## 15. Current HA-primary risk architecture

Working hypothesis:

```text
H4 FAST participation signal
        |
        v
previous completed H4 STD HA extreme
        |
        v
fixed Child Hard SL
        |
        v
stop distance
        |
        v
money-risk budget for this Child
        |
        v
lot size derived from broker tick/contract value
        |
        v
campaign aggregate-risk check
        |
        +-- enough budget -> full desired risk
        |
        +-- insufficient -> partial remaining risk comparator
```

Independent campaign exit remains:

```text
first opposite completed FAST H4 HA
-> exit surviving campaign Children
```

A Child that hits its own Hard SL remains dead.

## 16. Authority boundary

Supported as the leading research direction:

```text
H4 HA-native Hard SL semantics
previous completed H4 STD HA extreme as the cleanest current candidate
Child-level money-risk sizing
campaign-level aggregate risk ceiling
```

Not promoted:

```text
previous-STD stop as production rule
W1=1 / W3=3 monetary risk
any base account %
any campaign cap value
partial size-down as production behavior
CHOP-tight micro stop
```

## 17. Persisted result artifacts

- `results/V10_HA_SL_FAMILY_SUMMARY_20260917.csv`
- `results/V10_PREV_STD_HA_STOP_SIGNAL_LEDGER_20260917.csv`
- `results/V10_W3_RISK_MULTIPLIER_SCAN_PREV_STD_HA_20260917.csv`
- `results/V10_CAMPAIGN_RISK_CAP_SCAN_20260917.csv`
- `results/V10_HA_RISK_RESEARCH_CHECKPOINT_20260917.json`

Unlike the earlier session-only indicator scan, the main HA-risk candidate has a row-level selected-signal stop ledger persisted in this update.
