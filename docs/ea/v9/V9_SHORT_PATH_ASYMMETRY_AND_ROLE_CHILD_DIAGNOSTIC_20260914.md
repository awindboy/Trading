# V9 SHORT Path Asymmetry and Role-Child Diagnostic

Date: `2026-09-14`
Status: `CONSUMED-DATA DIAGNOSTIC / ROLE-BASED MANAGEMENT CANDIDATE`

## 1. SHORT weakness is not mainly next-liquidity direction accuracy

With ERA4 eligibility:

```text
next H4 liquidity continues current primary
DOWN  ~73.1%
UP    ~74.7%
```

Therefore the large PnL difference does not come from DOWN being unable to identify the next same-side H4-liquidity delivery.

## 2. Immediate-Arrival path quality is asymmetric

Resolved trade path, normalized by entry-time ATR180:

```text
median MFE
DOWN  ~1.67 S
UP    ~2.53 S

median MAE
DOWN  ~1.00 S
UP    ~0.84 S
```

Median primary-direction return after immediate Arrival entry:

```text
24 hours
DOWN  about -0.35 S
UP    about +0.29 S
```

This indicates that DOWN Arrival entries tend to experience more adverse rebound / less immediate expansion even when the higher-level delivery sequence later continues.

## 3. CHALLENGED giveback is similar; pre-challenge expansion is not

For trades exiting at CHALLENGED:

```text
median peak-to-challenge giveback
DOWN ~2.28 S
UP   ~2.37 S
```

but median favorable expansion before challenge is roughly:

```text
DOWN ~2.48 S
UP   ~3.37 S
```

So the challenge resolver gives back a similar market-scale distance in both directions. UP usually generated more expansion before the giveback; DOWN frequently did not.

## 4. Repeated DOWN participation

Pooled fixed-size PnL under all-Child challenge holding:

```text
DOWN first Child   +763.60
DOWN second        +438.72
DOWN third          -11.50
DOWN fourth+      -1,978.17
```

The fourth+ DOWN cohort is negative in every calendar year 2022-2026.

This must **not** be converted directly into `max 3 shorts` authority. Child count is descriptive evidence of a later-stage route problem, not yet a causal trading rule.

## 5. Threshold-free role-based comparator

A semantically cleaner policy was tested:

```text
FIRST ACTUALLY ACCEPTED CHILD IN ACTIVE ROUTE
= ANCHOR_CHILD
= independent H1 structural SL
= hold through same-side H4 liquidity
= exit at CHALLENGED

EVERY LATER ACCEPTED CHILD IN SAME ROUTE
= CONTINUATION_CHILD
= independent H1 structural SL
= exit at first subsequent H4-liquidity Arrival
```

If SL and semantic exit occur in the same M1, that Child is ambiguous.

No direction-specific exception is used. No Child count maximum is used. No partial percentage is used.

## 6. Role-based result

Fixed-size gross:

```text
Entries       1,250
Resolved      1,139
PnL          +8,530.74
PF              2.023
WR             65.6%
DD             440.35
Max concurrent Children = 2
```

Direction:

```text
DOWN   +1,561.09 / PF 1.345
UP     +6,969.65 / PF 2.826
```

Costs:

```text
1x observed spread  +8,336.60 / PF 1.992
3x observed spread  +7,948.32 / PF 1.931
```

All M1 ambiguities forced to structural loss:

```text
+5,442.83 / PF 1.476 / DD 758.06
```

Gross result is positive in each calendar year 2022-2026.

## 7. Why this comparator is conceptually important

It restores the Parent/Child distinction:

- Anchor participates in the larger Parent route and preserves the right-tail runner.
- Continuation Child is a local attempt created by a later delivery and realizes at the next H4-liquidity state transition.
- Later local Children no longer all accumulate the same eventual CHALLENGED giveback.
- Simultaneous exposure falls naturally to 2 without inventing an exposure cap.

The gross total is lower than blind all-Child challenge holding, but PF, WR, drawdown, SHORT performance, and exposure shape improve substantially.

## 8. Negative evidence retained

The formerly hidden July 2025 month remains negative and was not repaired after reveal.

2022 is gross-positive under role management but becomes negative when every M1 ambiguity is forced to a full structural loss. Exact execution semantics therefore remain material.

## 9. Do not promote yet

Do not yet freeze:

- SHORT prohibition;
- max-3 Child rule;
- ERA directional trend filter;
- fixed TP;
- partial exit fraction.

The role-based policy is the next strongest mechanical management candidate and should proceed to exact execution/fill validation.
