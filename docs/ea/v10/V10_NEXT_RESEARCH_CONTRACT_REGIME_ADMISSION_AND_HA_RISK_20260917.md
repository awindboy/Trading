# V10 Next Research Contract — Regime-Aware Reverse Admission + HA-Primary Risk

Date: `2026-09-17`  
Status: `ACTIVE SHADOW RESEARCH CONTRACT`  
Production authority: `NONE`  
Market: `GOLD# ONLY`

## 1. Current research routing override

Per current project direction, do **not** spend the immediate research cycle on rebuilding already-consumed reproducibility work.

The 2026-09-16 actual-tick/reproducibility documents remain historical evidence and their execution caveats remain true, but they are no longer the immediate research queue.

Current work order:

```text
A. keep H4 as the main HA campaign clock
B. separate FAST-NHA exit from reverse admission
C. introduce an explicit NEUTRAL / chop-risk state
D. replace V9-derived H1 liquidity SL as the active risk direction
   with HA-primary stop research
E. move sizing from fixed lot to Child money-risk + campaign risk budget
F. integrate these layers while preserving trend right tail
```

## 2. Frozen research direction: H4 remains main

Do not move the main campaign clock to H1.

The consumed H1-main study showed much higher turnover and near-1 PF under FAST H1. H1/M30/M15 should remain internal delivery / confirmation / regime layers.

## 3. Reverse-admission semantics

Current working state machine:

```text
existing LONG campaign
-> completed opposite FAST H4 HA
-> EXIT LONG

then independently:
Is the new SHORT direction admissible now?

YES -> SHORT campaign may start
NO  -> NEUTRAL
```

The same applies symmetrically from SHORT to LONG.

No fixed wait bar, cooldown, retry count, or no-chase distance may be invented.

## 4. Regime layer

Primary research coordinates:

```text
ADX trend strength
H4 path efficiency
recent FAST/H4 flip activity
```

The role is:

```text
trendable / trustworthy reversal environment
vs
alternating / chop-risk environment
```

Do not use ADX as direction. Do not promote an absolute ADX threshold from the current scan.

## 5. Direction layer

Once the regime permits or once NEUTRAL needs to be released, use compact independent direction evidence.

Primary families:

```text
EMA direction / slope geometry
DI direction / spread
modified FAST phase
M15/M30/H1 HA directional delivery
STD/SLOW HA phase context
```

Keep the representation compact. Do not return to feature soup.

## 6. Hard-SL research baseline

The current leading HA-native comparator is:

```text
LONG Child  -> previous completed H4 STD HA low
SHORT Child -> previous completed H4 STD HA high
```

The price is fixed at Child admission.

The old nearest-active H1 liquidity stop remains a historical comparator only; do not assume it is V10 authority.

## 7. Stop design objective

Do not optimize only for smaller fixed-lot loss.

A candidate Hard SL must jointly satisfy:

```text
HA-trend invalidation meaning
survival of large trend winners
reasonable stop-distance distribution
stable money-risk sizing
no micro-stop leverage explosion
```

Track at minimum:

```text
stop-hit count
stop distance P1/P5/P10/median/P90
NHA winners cut by stop
removed gross loss
removed gross profit
L1-2 / L3-5 / L6+ economics
LONG / SHORT
2025 / 2026
```

## 8. Child money-risk sizing

For each admitted Child:

```text
desired money risk = equity * child_risk_fraction
lot = desired money risk / broker stop-value-per-lot
```

Use the Child's actual fixed HA Hard SL distance.

Do not cap lot size with an invented numeric limit in research. Instead report when stop geometry creates unrealistic leverage and reject/repair the SL family semantically.

## 9. W as a risk weight

Research may compare:

```text
Equal risk:
W1 = 1 risk unit
W3 = 1 risk unit

W-proportional:
W1 = 1 risk unit
W3 = 3 risk units

compressed/intermediate mappings
```

No multiplier is authority merely because the consumed scan is monotonic.

## 10. Campaign aggregate risk

At every new Child:

```text
open campaign committed risk
= sum(initial risk budgets of surviving Children)
```

Research a ceiling:

```text
open committed risk <= C risk units
```

`C` is a risk ceiling, not an entry-alpha threshold.

If the desired new Child exceeds remaining budget, preserve both explicit comparators:

```text
PARTIAL -> use remaining risk budget
SKIP    -> reject new Child
```

Current evidence favors partial allocation at tighter caps, but it is not promoted.

## 11. Do not solve chop in the stop layer alone

The current evidence is explicit:

```text
better Hard SL
!=
removal of repeated alternating entry churn
```

Therefore:

```text
Regime / NEUTRAL
-> controls whether the reverse campaign is admitted

Hard SL
-> controls loss of an admitted Child

Campaign risk cap
-> controls aggregate account exposure
```

These remain separate semantic layers.

## 12. Integrated test order

When resuming research:

```text
1. Freeze current bounded-m3 selected-signal population as the comparison cohort.
2. Apply reverse-admission / NEUTRAL candidate while keeping current risk fixed.
3. Apply previous-STD HA Hard SL while keeping admission fixed.
4. Apply money-risk sizing while keeping signal/stop fixed.
5. Apply campaign risk ceiling while keeping all earlier semantics fixed.
6. Only then combine the best stable semantic choices.
```

Always report incremental deltas so the source of improvement remains identifiable.

## 13. Right-tail guardrail

V10 is paid by large trend runs.

Every integrated candidate must report:

```text
gross profit / gross loss
L1-2 / L3-5 / L6-8 / L9-11 / L12+
top-1 / top-5 / top-10 winner contribution
large-run positive gross-profit retention
weighted position-hours
max concurrent committed risk
```

A chop filter that merely removes the right tail is not progress.

## 14. Current non-authority reference results

Regime-aware conditional NEUTRAL scans reached roughly `+17.4k` to `+17.9k` in the consumed sample, versus `+14,827.57` bounded-m3 authority reference, but these are post-hoc scans.

The clean previous-STD HA stop reconstructed at `+14,357.83 / PF 1.538 / DD 2,552.97` under the local fixed-lot engine and maintained `+401.88 risk-R / PF_R 1.467` under W-proportional money-risk accounting.

These are research reference points only.

## 15. Promotion boundary

No V10 production rule is promoted by this contract.

Before any later promotion, the integrated architecture still needs:

```text
fixed causal semantics
out-of-sample / forward evidence
broker-executable lot calculation
actual-tick behavior for the new Hard SL and campaign exit
right-tail acceptance
risk-appetite decision for the base account percentage
```

The immediate research objective is architectural clarity, not production promotion.
