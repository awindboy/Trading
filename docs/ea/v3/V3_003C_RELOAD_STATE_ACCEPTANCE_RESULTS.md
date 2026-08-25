# V3-003C — GOLD Reload State × Local Acceptance Interaction

Status: `DISCOVERY RESULT / FIRST REPRODUCIBLE RELOAD CANDIDATE / NO STRATEGY AUTHORITY`  
Date: `2026-08-26`  
Market: `GOLD# ONLY`  
Environment: `XM Ultra Low / XMGlobal-MT5 7`  
Discovery data: `2023-2025 M1`  
Validation vault: `2022 — CLOSED`  
Untouched: `2021`

## 1. Purpose

V3-002 reported a promising but sparsely documented selective-continuation family near:

```text
2023 38 trades / +1R 55.3%
2024 46 trades / +1R 56.5%
2025 43 trades / +1R 62.8%
```

The exact standalone Python implementation that produced those counts was not committed.
Therefore V3-003C does **not** claim exact parity with that historical population and does
not reverse-engineer thresholds merely to reproduce those numbers.

Instead this phase builds a new fully reproducible Level-A control from the accepted raw
GOLD history and asks a narrower causal question:

> Does a local liquidity reaction become directionally useful only when a higher delivery
> state and a sufficiently decisive local acceptance are simultaneously present?

This follows the V3-003 architecture:

```text
known/active delivery
-> intermediate opposite-side liquidity reaction
-> local acceptance back with delivery
-> RELOAD continuation candidate
```

## 2. Replay boundary

Input rows:

```text
2023 353,036
2024 353,837
2025 351,929
total 1,058,802
```

Level-A replay includes:
- causal M1 -> M5/M15/M30/H1 aggregation;
- causal source/swing availability;
- persistent liquidity lifecycle until physical consumption;
- same-M1 penetration + close recovery;
- spread-aware trigger-close Entry and short-side barrier handling;
- conservative same-bar +1R/SL ordering;
- exact mirror-direction replay at the same event/risk;
- physically deduplicated same-timestamp reaction population.

Not included yet:
- exact tick ordering;
- commission;
- slippage;
- swap;
- MT5 broker/order microstructure reproduction.

Therefore no result below is final profitability or EA authority.

## 3. Reference physical reaction population

Reference source detector for the reproducible control:

```text
M15 adaptive directional-change swing
k = 2.0 * trailing ATR
```

The exact `k=2.0` point is **not** promoted as a universal strategy parameter. It is the
reference implementation for the already-identified intermediate-prominence source region.
Natural M15/M30 source-scale sensitivity is reported separately.

Physical reaction lifecycle:

```text
causally confirmed intermediate liquidity
-> remains active until first physical consumption
-> M1 wick penetrates the level
-> same M1 closes back inside
-> pre-sweep M5 BOS-owner state is opposite the reaction direction
-> sweep extreme remains intact
-> first completed M5 owner transition back with reaction direction
-> trigger-close Entry
-> sweep-extreme SL
```

Reference broad control:

| Year | N | spread-adjusted +1R |
| --- | ---: | ---: |
| 2023 | 84 | 51.19% |
| 2024 | 86 | 53.49% |
| 2025 | 67 | 52.24% |

This is the common population used for the state/acceptance interaction test.

## 4. Delivery-state definition

The candidate delivery state is intentionally compact and uses no fitted P/L score.

At the **sweep time**, delivery is considered active when either:

### A. structural expansion renewal

Reuse the previously frozen V1 structural expansion concept:

```text
M30 mentor-wave expansion ratio =
mean(abs(recent 4 M30 wave-to-wave legs))
/
mean(abs(previous 4 M30 wave-to-wave legs))

active when ratio > 1.0
```

The `> 1.0` boundary was not selected from V3-003C P/L. It has the direct structural
meaning that the recent M30 leg group is larger than the prior group and was already frozen
in earlier regime research.

### B. explicit HTF delivery ownership

```text
M30 causal BOS-owner == reaction direction
AND
H1 causal BOS-owner == reaction direction
```

The combined research state is:

```text
DELIVERY_ACTIVE = M30_EXPANSION_RENEWED OR M30_H1_OWNER_AGREEMENT
```

This state by itself improved the reference control to approximately:

```text
2023 56 / 55.36%
2024 44 / 61.36%
2025 41 / 56.10%
```

It is still not sufficient for promotion.

## 5. Strong local acceptance definition

The failure taxonomy showed that most losing candidates did **not** lose the higher delivery
state first. Instead, local M5 acceptance often broke back against the trade while delivery
was still alive.

A natural, price-geometric acceptance comparison was therefore tested.

For each reaction:

```text
source penetration =
absolute directional overshoot beyond the swept liquidity level

acceptance margin =
directional M5 trigger close beyond the exact M5 structure level
that the owner transition actually broke
```

No ATR threshold is required for the final comparison because both are price distances.

Define:

```text
STRONG_LOCAL_ACCEPTANCE = acceptance_margin > source_penetration
```

Interpretation:

> The market must accept beyond local structure by more distance than it overshot the
> source liquidity during the sweep.

This is not a candle-size rule and not an FVG rule. It compares **rejection depth** with
**actual structure acceptance**.

## 6. The decisive result is an interaction, not a standalone filter

The full 2x2 state table is:

### 2023

| Delivery | Strong acceptance | N | Reaction-direction +1R | Exact mirror |
| --- | --- | ---: | ---: | ---: |
| no | no | 9 | 55.56% | 44.44% |
| no | yes | 19 | 36.84% | 63.16% |
| yes | no | 16 | 43.75% | 50.00% |
| **yes** | **yes** | **40** | **60.00%** | **35.00%** |

### 2024

| Delivery | Strong acceptance | N | Reaction-direction +1R | Exact mirror |
| --- | --- | ---: | ---: | ---: |
| no | no | 13 | 46.15% | 46.15% |
| no | yes | 29 | 44.83% | 51.72% |
| yes | no | 15 | 53.33% | 40.00% |
| **yes** | **yes** | **29** | **65.52%** | **27.59%** |

### 2025

| Delivery | Strong acceptance | N | Reaction-direction +1R | Exact mirror |
| --- | --- | ---: | ---: | ---: |
| no | no | 10 | 60.00% | 40.00% |
| no | yes | 16 | 37.50% | 56.25% |
| yes | no | 14 | 42.86% | 57.14% |
| **yes** | **yes** | **27** | **62.96%** | **33.33%** |

This is the main V3-003C result.

Important interpretation:

```text
strong local acceptance alone       != edge
higher delivery state alone         = incomplete
state + decisive acceptance together = first coherent reload candidate
```

The same apparently strong local reaction can mean something different outside the correct
auction/delivery state.

This directly supports the V3-003 architectural premise that **state and module cannot be
studied independently**.

## 7. Reference reload candidate

Frozen development candidate for future comparison:

```text
INTERMEDIATE persistent liquidity
-> atomic penetration + same-M1 recovery
-> local M5 correction was opposite beforehand
-> DELIVERY_ACTIVE at sweep
-> first M5 acceptance back with delivery
-> acceptance_margin > source_penetration
-> trigger-close Entry
-> sweep-extreme SL
```

Spread-adjusted standardized +1R:

| Year | N | +1R | Costless +1R | Exact mirror |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 40 | **60.00%** | 60.00% | 35.00% |
| 2024 | 29 | **65.52%** | 68.97% | 27.59% |
| 2025 | 27 | **62.96%** | 62.96% | 33.33% |

Total reference population = `96` events.

One-active-standardized-trade-at-a-time deduplication removes only one 2023 overlap and does
not weaken the result materially:

```text
2023 39 / 61.54%
2024 29 / 65.52%
2025 27 / 62.96%
```

Therefore simple event overlap is not driving the result.

## 8. Direction breadth

| Year | SHORT | LONG |
| --- | ---: | ---: |
| 2023 | 20 / 65.0% | 20 / 55.0% |
| 2024 | 12 / 58.3% | 17 / 70.6% |
| 2025 | 14 / 64.3% | 13 / 61.5% |

No direction veto is authorized.

## 9. Temporal breadth and the remaining weak cell

Quarter results are descriptive only:

```text
2023 Q1  9 / 44.4%
2023 Q2 10 / 70.0%
2023 Q3 12 / 58.3%
2023 Q4  9 / 66.7%

2024 Q1  5 / 60.0%
2024 Q2  9 / 55.6%
2024 Q3  3 / 100.0%
2024 Q4 12 / 66.7%

2025 Q1 12 / 83.3%
2025 Q2  3 / 0.0%
2025 Q3  9 / 55.6%
2025 Q4  3 / 66.7%
```

`2025 Q2 = 0/3` is too small to justify a quarter/session veto.

Costless replay is also `0/3`, so that weak cell is not explained by spread.

No calendar gate is authorized.

## 10. Winner continuation remains available

Within the M15-k2 reference candidate, among trades that reached +1R:

```text
P(+2R | +1R)
2023 66.7%
2024 57.9%
2025 52.9%

P(+3R | +1R)
2023 41.7%
2024 52.6%
2025 41.2%

P(+5R | +1R)
2023 20.8%
2024 36.8%
2025 35.3%
```

This is descriptive continuation evidence only. Do not mix an exit optimization into the
Entry/state validation phase.

## 11. Failure lifecycle taxonomy

For candidate losers, shadow replay separately tracks:

```text
local M5 trigger invalidation
vs
dynamic delivery-state loss
```

### 2023 — 16 losses

```text
8  LOCAL_TRIGGER_FAIL_STATE_ALIVE_AT_SL
4  SL_WITH_LOCAL_AND_STATE_ALIVE
3  LOCAL_FAIL_THEN_STATE_LOSS_PRE_SL
1  STATE_STALE_AT_TRIGGER
```

### 2024 — 10 losses

```text
8  LOCAL_TRIGGER_FAIL_STATE_ALIVE_AT_SL
1  LOCAL_FAIL_THEN_STATE_LOSS_PRE_SL
1  STATE_STALE_AT_TRIGGER
```

### 2025 — 10 losses

```text
6  LOCAL_TRIGGER_FAIL_STATE_ALIVE_AT_SL
2  LOCAL_FAIL_THEN_STATE_LOSS_PRE_SL
2  STATE_LOSS_PRE_SL
```

The dominant remaining loss class is therefore:

> Local acceptance fails while the higher delivery state is still alive.

This is evidence that the next improvement problem is closer to **correction completion /
acceptance persistence** than another broad HTF direction classifier.

However local invalidation is not automatically an exit rule: some eventual +1R winners
also experience local re-failure before reaching +1R, especially in 2023.

## 12. Post-SL counterfactual taxonomy

Among reference-candidate losses, the original +1R path was tracked after the original SL
against dynamic delivery-state loss.

```text
                         +1R recovered before state loss   state loss first
2023                              4                              12
2024                              4                               6
2025                              4                               6
```

This preserves the important distinction:

```text
trigger / local-source failure
!=
full delivery-premise failure
```

It does **not** authorize broad SL widening. Several recoveries happen only after the local
source has failed materially, and the prior V2/V3 work already rejected generic SL widening.

## 13. Objective maturity did not explain the remaining losses

Using the nearest causally active M30/H1 structural objective at Entry, the natural geometry
split was:

```text
objective lies before +1R
vs
objective lies at or beyond +1R
```

Reference-candidate +1R:

```text
2023: before 60.9% / at-or-beyond 58.8%
2024: before 80.0% / at-or-beyond 50.0%
2025: before 66.7% / at-or-beyond 60.0%
```

There is no stable evidence that a nearby objective is the failure mechanism.

Do not add an objective-room veto from this result.

## 14. Execution friction is not the main explanation

Reference candidate spread-adjusted vs zero-spread diagnostic:

```text
2023 60.0% vs 60.0%
2024 65.5% vs 69.0%
2025 63.0% vs 63.0%
```

The interaction survives before execution friction.

Exact-tick execution is still required before strategy authority, but current weakness is
not primarily a nominal-spread artifact.

## 15. Source-scale sensitivity

Natural source variants using the **same state and acceptance semantics**:

### M15 adaptive DC source

```text
k=1.5
2023 67 / 53.7%
2024 53 / 62.3%
2025 41 / 53.7%

k=2.0 reference
2023 40 / 60.0%
2024 29 / 65.5%
2025 27 / 63.0%

k=2.5
2023 32 / 56.3%
2024 18 / 66.7%
2025 18 / 66.7%
```

### M30 adaptive DC source

```text
k=1.5
2023 36 / 61.1%
2024 17 / 64.7%
2025 15 / 66.7%

k=2.0
2023 24 / 62.5%
2024 12 / 58.3%
2025 11 / 72.7%
```

Interpretation:
- the relationship is not unique to literal M15;
- very noisy low-prominence sources weaken it;
- intermediate/prominent physical liquidity is the better semantic abstraction;
- do not optimize `k` from P/L.

An outcome-blind M15+M30 same-k=2 union, deduplicated by physical reaction, gives:

```text
2023 44 / 59.1%
2024 30 / 66.7%
2025 27 / 63.0%
```

This is sensitivity evidence, not a new promoted source selector.

## 16. Reversal falsification

A useful negative control is the cell:

```text
NO delivery state
+
strong local acceptance
```

Reaction-direction +1R:

```text
2023 36.8%
2024 44.8%
2025 37.5%
```

Exact mirror:

```text
2023 63.2%
2024 51.7%
2025 56.3%
```

This does **not** authorize forced reversal.

Natural source sensitivity leaves 2024 mirror behavior too weak/unstable for reversal
authority. The correct current routing remains:

```text
DELIVERY + STRONG ACCEPTANCE
    -> continuation candidate

no delivery / weak acceptance / conflict
    -> NO TRADE for now
```

## 17. Statistical caution

Reference annual Wilson 95% intervals are wide because the candidate is sparse:

```text
2023 24/40, 60.0%, interval roughly 44.6%–73.7%
2024 19/29, 65.5%, interval roughly 47.3%–80.1%
2025 17/27, 63.0%, interval roughly 44.2%–78.5%
```

Events are also not fully statistically independent.

Therefore the development result is promising, not proof.

## 18. Decision

V3-003C establishes the first **reproducible, interpretable GOLD reload candidate** in the
current V3 line:

```text
market state provides directional permission
AND
local structure acceptance confirms correction completion strongly enough
```

Key project decision:

> Do not promote `delivery state` or `local acceptance` independently. The observed edge is
> the interaction.

No EA change is authorized.

No FVG hard gate is reintroduced.

No objective-room, quarter, session, direction, spread, or SL-widening veto is authorized.

The historical V3-002 `38/46/43` selective population remains a benchmark but is not claimed
to be exactly reproduced.

## 19. Next phase

Freeze this exact reference candidate as `V3_RELOAD_CANDIDATE_A` for comparison.

Next work should be separated into two tracks:

### Track A — candidate integrity / independent validation preparation

```text
1. keep exact definitions frozen;
2. preserve 2022 closed until the validation input is intentionally supplied;
3. when 2022 is opened, run once without retuning;
4. reject rather than move thresholds if validation reverses;
5. only after independent survival move to exact tick / MT5.
```

### Track B — separate development research

The frozen candidate is not modified while studying:

```text
correction-completion / acceptance-persistence alternatives
```

Any new variant is a new candidate and must beat Candidate A without using 2022 for tuning.

2021 remains untouched.
