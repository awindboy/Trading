# D-149 SP / EM V1 RESULTS AND V2 PLAN

Date: 2026-08-21  
Repository base: `b3068c0b445005fe455405ed18fb1f82198231df`  
V1 identity: `1.95R1L11 / SP_EM_RESEARCH_V1`  
V2 target identity: `1.96R1L12 / SP_EM_RESEARCH_V2`  
Strategy authority: **UNCHANGED — ORIGINAL + EM_OFF remains baseline control**  
2021: **KEEP UNTOUCHED**

## 1. Why this document exists

D-149 moved the project from descriptive diagnosis into two controlled solution tracks:

```text
SP = Smart Partial
     solve +1R winner giveback while preserving large runners

EM = Episode Management
     solve clustered genuine Entry-survival failures without mining a static Entry filter
```

The first GOLD 2025 V1 implementation produced meaningful evidence. This document freezes that evidence before any V2 change and pre-registers the exact V2 corrections. V1 modes remain available as controls.

## 2. Source ledgers

User-provided GOLD 2025 ledgers:

```text
GOLD_SP.csv
SHA-256 = 739610b8825917b1fffbf524b0609f158f2c01f4409ecb9495af53f05cf6231f

GOLD_EM.csv
SHA-256 = 3854fd923ea6f18f55a57e984fec9149db25c181aa2ed1d3532cbe71039f4533

GOLD_SPEM.csv
SHA-256 = cbf887f1012afe8074f46b7968efdf7e171422af9b8fe3e1ad05c8fe9cd55175
```

All three passed the D-149 V1 ledger analyzer with:

```text
execution divergence = 0
cancel rejected = 0
unresolved fills = 0
```

The comparison baseline is the already validated GOLD 2025 ORIGINAL continuation population.

## 3. GOLD 2025 continuation result

| Variant | Trades | Wins | WR | Avg winner | Avg loser | Expectancy | Total R | Max DD | Longest nonpositive streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ORIGINAL | 51 | 14 | 27.45% | +3.827R | about -1.10R | +0.254R | +12.934R | 19.53R | 11 |
| D147 mechanical PARTIAL | 51 | 24 | 47.06% | +1.402R | -0.894R | +0.187R | +9.522R | 7.66R | 6 |
| **SP V1** | **51** | **22** | **43.14%** | **+1.880R** | **-0.872R** | **+0.315R** | **+16.071R** | **11.05R** | **6** |
| EM V1 | 29 | 8 | 27.59% | +4.842R | -1.067R | +0.563R | +16.339R | 15.13R | 14 |
| SP+EM V1 | 30 | 13 | 43.33% | +2.256R | -0.775R | +0.538R | +16.149R | 8.29R | 7 |

The EM expectancy values are not promotion evidence by themselves because EM removed a large share of opportunities. EM must be judged by the membership it removed and by the loss-cluster objective.

## 4. SP V1 — primary positive result

SP V1 used the D-145/D-146 winner-continuation finding only at the stage where it was discovered: first +1R.

State rule:

```text
STRONG_RUNNER
= current M30 direction matches trade
+ valid current M30 protected/external geometry
+ current M30 external is at or beyond the original +2R price

DEFAULT
= all other / state unavailable
```

No pooled progress threshold was fitted.

GOLD 2025 continuation state counts:

```text
STRONG_RUNNER = 11
DEFAULT       = 19
```

Observed +2R continuation:

```text
STRONG_RUNNER = 9 / 11 = 81.8%
DEFAULT       = 4 / 19 = 21.1%
```

This is the strongest direct evidence so far that the generalized +1R M30 continuation state can be turned into exit-management behavior without being misused as an Entry filter.

### SP V1 economic effect

Relative to ORIGINAL continuation:

```text
WR          27.45% -> 43.14%
avg winner   3.827R -> 1.880R
expectancy   0.254R -> 0.315R
Total       12.934R -> 16.071R
Max DD      19.53R  -> 11.05R
loss streak 11      -> 6
```

Relative to D147 mechanical PARTIAL, SP preserved materially more winner size and more total/expected R while retaining much of the WR/streak improvement.

Classification:

```text
SP V1 = PROMISING / RETAIN AS CONTROL
```

It is not yet promoted because this is one development symbol-year strategy run.

## 5. SP V1 defects discovered by live strategy execution

### 5.1 DEFAULT did not always lock a positive aggregate result

Five continuation DEFAULT trades reached +1R and received the fixed 50% V1 partial but still finished slightly negative after the remainder and trading costs.

Therefore a blind fixed 50% DEFAULT fraction does not implement the actual economic objective:

> once a DEFAULT trade reaches +1R, realize enough that an original-SL fallback of the remainder is expected to leave a small positive aggregate result.

This motivates a protected-volume calculation, not a new return-optimized fraction.

### 5.2 Static Fill-price BE did not guarantee nonnegative aggregate P&L

One STRONG continuation case:

```text
+1R -> 25% partial
+2R -> remaining SL moved to actual Fill
later BE exit
exit profit = +22.48 USD
swap        = -32.05 USD
aggregate   = -9.57 USD ≈ -0.105R
```

Thus price BE and economic BE are different when carry/fees exist. V2 must maintain a forward-only **current-known-cost-adjusted BE** after +2R.

### 5.3 Volume granularity

V1 produced three all-scope partial-infeasible cases. A true partial is impossible when the broker minimum/step cannot leave both a valid closed slice and a valid remainder.

V2 distinguishes:

```text
STRONG infeasible -> preserve full runner; do not replace with full close
DEFAULT infeasible -> +1R full-close fallback is permitted and logged
```

The DEFAULT fallback is an execution-granularity policy, not the normal exit architecture.

### 5.4 Stage-scope defect

SP V1 also ran on reversal scenarios although the underlying D-145/D-146 runner evidence was discovered on EXTERNAL_CONTINUATION.

V2 is therefore explicitly:

```text
EXTERNAL_CONTINUATION only
```

No reversal rule is inferred from continuation research.

## 6. SP V2 frozen design

Mode:

```text
V1_EXIT_SMART_PARTIAL_V2
```

V1 `V1_EXIT_SMART_PARTIAL` remains unchanged as a control.

### 6.1 STRONG behavior

Keep the existing structural state and fraction:

```text
+1R STRONG_RUNNER -> close 25% of current position when broker-valid
remainder -> frozen structural TP
```

There is no new threshold fit from the V1 result.

### 6.2 DEFAULT protected realization

At first +1R, search broker-valid close volumes from smallest upward.

For each candidate, model:

```text
known realized/current cash
+ gross P&L of candidate close at current executable price
+ gross P&L of remaining volume if it later exits at original normalized SL
```

Choose the **minimum** close volume whose modeled terminal cash is at least:

```text
+0.05R
```

The `0.05R` is a small architecture/cost guard, not a fitted performance optimum. It exists because future close commission/slippage cannot be known exactly at +1R.

If no true protected partial is broker-feasible, DEFAULT may full-close at +1R and must log that fallback.

### 6.3 +2R cost-adjusted BE

Once +2R has been observed, the remainder's protective SL must be at least Fill and may advance farther in the favorable direction when current-known costs/carry require it.

Target condition:

```text
known realized/current cash
+ modeled remainder P&L at protective SL
>= +0.01R
```

The target is recalculated while the position remains open and can only move forward. It never loosens the SL. Structural TP remains unchanged.

`0.01R` is a small positive guard rather than a fitted profit target. It cannot guarantee every final broker cash result against unknown future slippage/commission, so validation must check actual net outcomes.

## 7. EM V1 — negative result

EM V1 attempted to manage risk at `frozen map owner + direction` episode level.

GOLD 2025 continuation:

```text
ORIGINAL fills = 51
EM V1 fills    = 29
WR             = 27.59%
longest streak = 14
```

The isolated EM streak worsened from 11 to 14 despite heavy trade suppression. Therefore V1 did not solve the user's target problem.

Classification:

```text
EM V1 = DEMOTED / RETAIN AS NEGATIVE CONTROL
```

### 7.1 Which EM V1 component failed

V1 block counts:

```text
same-episode concurrent exposure = 20
first-loss requires fresh delivery = 6
```

Mapping blocked IDs back to the clean ORIGINAL population:

```text
concurrency rule:
17 baseline fills
5 winners / 12 losers
about -0.259R total

no-refresh rule:
5 baseline fills
1 winner / 4 losers
about -3.146R total
```

The concurrency rule removed many opportunities for little net protection and can remove SP-recoverable/winning trades. It is rejected for V2.

The post-failure fresh-delivery requirement removed fewer opportunities with a much more favorable loss concentration. It is retained.

### 7.2 Why owner-only locking is insufficient

The longest EM-only loss streak crossed many different map-owner episodes. The problem can therefore be a broader state in which the Entry architecture repeatedly fails even as owners rotate.

EM must move from:

```text
same owner lost -> suppress owner
```

toward:

```text
Entry architecture failed repeatedly -> stop risking new money until the architecture proves +1R survival again
```

## 8. D-148 evidence that constrains EM

Clean GOLD 2023-2025 continuation taxonomy:

```text
167 fills
89 immediate +1R = 53.3%
78 SL-first      = 46.7%
```

Among 78 SL-first failures:

```text
27 / 78 = 34.6%
recovered original +1R before H1/M30 support loss

51 / 78 = 65.4%
lost H1/M30 support before recovery
```

Among the 27 recoveries:

```text
18 original Root invalidated first
 9 original Root stayed valid
```

Therefore EM must not try to turn all losses into winners. Its purpose is to prevent repeated expenditure during demonstrated Entry-survival failure clusters while allowing causal requalification.

## 9. EM V2 frozen design

Mode:

```text
V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2
```

V1 `V1_EM_CAUSAL_EPISODE_V1` remains unchanged as a control.

### 9.1 Genuine EM failure

Only:

```text
real EXTERNAL_CONTINUATION fill
-> original SL exit
-> +1R was never reached first
```

counts as a genuine EM Entry failure.

A trade that reaches +1R and later gives back is an exit-management problem. It resets the global Entry-failure streak rather than adding an EM failure.

### 9.2 Local fresh-delivery gate

After a genuine failure in an episode, a later setup under that same episode must have fresh same-direction map delivery after the failure before new authorization/shadow qualification.

This retains the useful V1 component.

### 9.3 Global quarantine trigger

```text
2 consecutive genuine Entry failures
-> QUARANTINE
```

The count is frozen before V2 testing and must not be optimized from GOLD 2025. It reflects the explicit design objective of tolerating one or two unavoidable losses but preventing a five/eight/ten-loss slide.

### 9.4 Quarantine behavior

Quarantine does not expire by time.

New real continuation submissions are blocked. When an otherwise eligible setup exists and its local refresh requirement is satisfied, at most one no-broker shadow setup is armed.

Before shadow fill, it remains valid only while:

```text
frozen objective has not already delivered
original Root is still active
the frozen H1/M30 owner still holds same-direction authority
```

Shadow fill uses the already-frozen strategy Entry price. After shadow fill, exact executable-side barriers are:

```text
LONG  -> Bid
SHORT -> Ask
```

and the terminal is:

```text
+1R before original SL -> requalify / release quarantine
original SL first      -> shadow failure / keep quarantine
```

A canceled shadow setup does not requalify the strategy.

### 9.5 Requalification cost

The successful shadow setup itself is intentionally not traded.

```text
shadow +1R success
-> quarantine released
-> next eligible setup is the first new real trade
```

This is the explicit cost of requiring causal evidence that the Entry architecture is working again.

An already-open real trade that was submitted before quarantine and later reaches +1R can also release quarantine because it provides the same causal survival evidence.

### 9.6 Existing exposure boundary

V2 does not force-cancel existing pending/filled real exposure when quarantine starts. It only blocks authorization of **new** risk.

This prevents the EM experiment from becoming entangled with the still-separate pending-cancellation/execution-lifecycle problem.

Consequently, the first V2 test may still show more than two losses immediately around the trigger if multiple real positions were already live. That is an explicit interpretation boundary, not a hidden defect.

## 10. V2 validation contract

First validate implementation, then strategy behavior.

Required sequence:

```text
1. MetaEditor compile = 0 errors
2. ORIGINAL + EM_OFF control parity vs D149 V1
3. GOLD 2025 SP V2 + EM_OFF
4. GOLD 2025 ORIGINAL + EM V2
5. GOLD 2025 SP V2 + EM V2
```

Do not change constants between these runs.

Primary metrics:

```text
realized WR
average winner / loser R
cost-adjusted expectancy
total R
max drawdown
longest nonpositive streak
winner concentration
```

SP V2 specific:

```text
STRONG / DEFAULT state counts
protected DEFAULT partial count
DEFAULT full-close granularity fallback count
actual final net result of +1R DEFAULT trades
cost-adjusted BE moves / refreshes / rejections
actual final net result after +2R
```

EM V2 specific:

```text
genuine Entry failure count
quarantine entries / releases
new-risk blocks
local no-refresh blocks
shadow armed / filled / +1R / SL / canceled / censored
number of real losses after quarantine trigger caused by pre-existing exposure
number and R of baseline opportunities skipped during quarantine
requalification winners sacrificed in shadow
```

If GOLD 2025 execution and causal ordering are coherent, run unchanged V2 on GOLD 2023 and 2024. Only after multi-year direction is known should V2 expand cross-market.

## 11. Prohibited interpretation / tuning

Do not after seeing GOLD 2025 V2:

```text
fit a new M30 progress cutoff
change STRONG 25% because another fraction looks best
optimize the two-failure quarantine count
add a time cooldown
add a generic quality score
turn EM into a direction veto
reuse post-+1R state as Entry authorization
```

If a V2 relationship fails on the next independent years/markets, document the failure rather than fitting it back to GOLD 2025.

## 12. Current classification

```text
SP V1 = PROMISING CONTROL
EM V1 = DEMOTED CONTROL
SP V2 = IMPLEMENTED RESEARCH VARIANT / VALIDATION PENDING
EM V2 = IMPLEMENTED RESEARCH VARIANT / VALIDATION PENDING
ORIGINAL + EM_OFF = BASELINE CONTROL
AGENTS / EA_SPEC authority = UNCHANGED
2021 = UNTOUCHED
```
