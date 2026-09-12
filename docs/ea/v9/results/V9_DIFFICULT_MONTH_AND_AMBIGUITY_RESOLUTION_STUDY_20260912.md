# V9 Difficult-Month + Ambiguity Resolution Study

Date: `2026-09-12`
Status: `CONSUMED-DATA ATLAS EVIDENCE / NOT STRATEGY AUTHORITY`
GitHub base HEAD: `b7ad4da10383699a38434a163a5e8e72db15b5d5`

## Scope

Strict information-known boundaries:

```text
2025 known_at < 2025-07-01 00:00
2026 Jan-Feb known_at < 2026-03-01 00:00
```

No July warmup. No Dec-2025 warmup for Jan-2026. No 2021.

This study closes two open Atlas questions:

1. Why was 2025-05 materially harder?
2. Should UNRESOLVED / AMBIGUOUS be forcibly classified?

## 1. 2025-05 is explained by state composition

Compared with the mean of the other consumed 2025 months:

```text
strong H4 authority inside directional time
May:   74.0%
others: 80.9%

weak H4 authority
May:   26.0%
others: 19.1%

H4 local-interrupt share
May:   32.3%
others: 23.8%

H4 neutral share
May:   10.1%
others: 7.5%

H1 interruption share inside directional H4
May:   32.4%
others: 29.0%
```

The H1 nested auction did not disappear. It spent more time inside stressed larger authority.

Outcome topology:

```text
H1 realign rate
May:   59.3%
other 2025 months mean: 80.8%

median H1 interruption bars to resolution
May:   5.0
others mean: 3.7

H4 directional side changes
May:   9
others mean: 4.8

median directional transition buffer
May:   16h
other-month median: 12h
```

Conclusion:

```text
2025-05
= more weak authority
+ more interruption
+ more actual side-change activity
+ slower resolution
```

No May-specific rule is required.

## 2. H4 confidence explains much of the May difficulty

Within 2025-05 H1 interruption cycles:

```text
H4 macro side 3/3 agreement
20 cycles
75.0% H1 realign

H4 macro side 2/3 agreement
7 cycles
14.3% H1 realign
```

These are small descriptive subsets and must not become entry thresholds.

The useful conclusion is semantic:

> local counterflow should not receive the same repair presumption when the slower H4 authority is already internally disputed.

## 3. UNRESOLVED is a legitimate intermediate state

`UNRESOLVED_UP / DOWN` means the causal H4 views retain a directional macro majority but disagree on exact role.

When UNRESOLVED was entered directly from migration:

### 2025

```text
34 cases
67.6% -> same migration
23.5% -> neutralized
 8.8% -> opposite side
```

### 2026 Jan-Feb

```text
11 cases
54.5% -> same migration
36.4% -> neutralized
 9.1% -> opposite side
```

Therefore UNRESOLVED is neither a hidden migration signal nor a hidden reversal signal.

It is best read as:

> directional authority remains, but campaign role is disputed.

## 4. AMBIGUOUS should not be given a tiebreaker

`AMBIGUOUS` means the three H4 views cannot produce a directional macro majority.

2025 episodes with a prior directional side:

```text
22 episodes
next migration same as prior:     11
next migration opposite to prior: 11
```

This 50/50 result is important because the project is specifically trying to avoid manufactured certainty.

2026 had only three comparable episodes and all resolved opposite; sample is too small to alter the conclusion.

Current rule for research representation:

```text
AMBIGUOUS
-> do not force direction
-> retain auction-reset interpretation
-> let later migration earn authority
```

## 5. Boundary audit correction

An earlier working ledger retained one June-source bar whose information-known timestamp was exactly:

```text
2025-07-01 00:00
```

That is outside the consumed boundary even though its source timestamp was June 30.

The final scripts and final ledger bundle remove it.

This changes the strict 2025 H4 migration-interruption count from the earlier working `67` to final `66`.

All final authority documents must use the strict count.

## 6. Research implication

The hard month and uncertainty study made the grammar simpler rather than more complex.

Retain:

```text
STRONG / WEAK / NEUTRAL authority
MIGRATION / LOCAL_INTERRUPT
H1 ALIGNED / H1_INTERRUPT
UNRESOLVED / AMBIGUOUS
```

Do not add:

- May-specific filters;
- special transition indicators;
- ambiguity tiebreakers;
- fixed interruption duration thresholds;
- fixed object/sweep counts.

The next research target should be route/destination and Parent continuity inside this hierarchy.
