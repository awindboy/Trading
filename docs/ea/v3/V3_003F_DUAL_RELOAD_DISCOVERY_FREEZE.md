# V3-003F — Dual Reload Discovery Freeze

Status: `DISCOVERY FREEZE / VALIDATION-READY LEVEL-A CANDIDATE / NO PRODUCTION AUTHORITY`  
Date: `2026-08-27`  
Expected repository base: `fa8b4f447fa4990d3a26afd745d8743fe228d63a`  
Market: `GOLD# ONLY`  
Discovery/development data: `2023-2025 M1`  
Validation vault: `2022 — STILL CLOSED`  
Untouched: `2021`

## 0. Purpose

This document closes the current GOLD dual-reload discovery cycle at a deliberate intermediate endpoint.
It does **not** authorize an EA change or live trading. It freezes one exact Level-A candidate and records
all material caveats before the one-time 2022 validation vault is opened.

The previous V3-003E result remains immutable historical authority. V3-003F adds the final work that was
still missing there:

1. finish the two interrupted Module-H experiments;
2. finish the natural `source-k × pullback` robustness audit;
3. cross-check H state branches with an independent mentor-wave liquidity semantic;
4. finish the Module-L payoff/sample-expansion audit;
5. correct the prior H/L exposure-overlap assumption;
6. define deterministic module ordering/exposure semantics;
7. freeze the exact candidate to be taken into 2022 without retuning.

---

# 1. Startup parity — PASSED

Raw GOLD 2023-2025 M1 replay again reproduced the committed V3-003E authority:

```text
Candidate A, M15 adaptive DC k=2:
2023 40
2024 29
2025 27

Module L primary:
11 physical trades
11 checkpoint hits
10 full +1R hits
1 exact-mirror checkpoint
7 residual +2R hits

Module H k2 / 50% base:
48 fills
14 TP5
31 SL
3 BE

Module H H2 direct-transfer:
44 fills
14 TP5
27 SL
3 BE
EV +0.9773R/trade under +3R->BE->5R
```

A parity failure remains a reproducibility bug, not permission to retune.

---

# 2. The two interrupted H experiments are now CLOSED

## 2.1 Body-close back through original swept liquidity

Hypothesis:

> after H fill, a body close back through the original swept-liquidity price may identify a genuine
> failed rejection before the sweep-extreme SL.

The test preserved all 14 known H2 TP5 winners.

### M1 completed-body close

```text
3 doomed H trades exited early
mean body-exit ~= -0.908R
H2 EV: +0.9773R -> +0.9836R
```

### M5 completed-body close

```text
2 doomed H trades exited early
mean body-exit ~= -0.881R
H2 EV: +0.9773R -> +0.9827R
```

Decision:

```text
REJECT AS MATERIAL ECONOMIC IMPROVEMENT
```

The event is causally meaningful but occurs too near the original SL. Do not add the extra exit state.

## 2.2 +2R 50% protection

Variant:

```text
+2R:
    realize 50%
    residual keeps original SL
+3R:
    residual -> BE
+5R:
    final exit
```

Reference H2 result:

```text
44 trades
positive = 20 / 44 = 45.45%
avg positive = +2.675R
EV = +0.670R/trade
```

It raises H positive-trade frequency but materially sacrifices the large-tail expectancy and does not solve
the core drawdown/loss-streak problem.

Decision:

```text
REJECT AS PRIMARY H PROTECTION
```

Preserve:

```text
H primary payoff control:
+3R -> BE -> +5R

H secondary portfolio/positive-frequency control:
+3R -> realize 25%
residual -> BE
final -> +5R
```

---

# 3. Module H — final discovery classification

## 3.1 H2 direct-transfer is the freeze-eligible H core

Reference H2:

```text
Candidate A
-> clean M1 ownership path
-> 50% accepted-leg pullback
-> direct M1 ownership transfer
-> sweep-extreme SL
-> +3R -> BE
-> +5R
```

Reference:

```text
44 fills
14 TP5
27 SL
3 BE
raw H EV +0.9773R/trade
```

Direct-transfer remains the strongest H-specific eligibility fact. Across the natural adaptive source/pullback
panel, non-direct +5R winners remain zero. In the independent mentor-wave H reconstruction, the four
non-direct fills were also all SL.

This is stage-specific authority:

```text
direct-transfer as generic Candidate-A gate = NOT AUTHORIZED
direct-transfer as H large-tail eligibility  = FROZEN INTO H2 CANDIDATE
```

## 3.2 The natural geometry surface is broad enough to freeze the reference

The existing positive-frequency H management (`+3R 25% harvest`) plus primary L was evaluated over:

```text
source k = 1.5 / 2.0 / 2.5
pullback = 25% / 50% / 75% / 100%
```

With the final exposure contract defined in Section 7, every `k >= 2` natural cell remains:

```text
positive-rate >= 50%
average positive > 2R
EV > 0
```

Observed minima across those eight cells:

```text
positive rate    50.0%
avg positive     +2.073R
EV               +0.600R/trade
```

The `k=1.5` cells remain only about `40.7%~42.7%` positive despite positive EV. This is consistent with the
physical-support audit: low-prominence `k=1.5-only` H events strongly dilute the edge.

Therefore `k=2 / 50%` is frozen as the exact reference **because it is the existing development benchmark
inside a broad viable neighborhood**, not because it is the best isolated grid point.

## 3.3 H3 / BOTH exclusion — stronger evidence, still NOT frozen

Define:

```text
owner_agree = M30 owner == direction AND H1 owner == direction
BOTH = M30 expansion > 1 AND owner_agree
```

Adaptive k2/50 H2:

```text
BOTH: 4 fills / 0 TP5 / 4 SL
```

Independent mentor-wave H:

```text
BOTH: 6 fills / 0 TP5 / 3 SL / 3 BE
```

Two physical events overlap across source semantics. Physical dedupe gives:

```text
8 unique BOTH H fills
0 TP5
5 SL
3 BE
```

This is meaningful cross-semantic negative evidence. However:

```text
2025 BOTH observations = 0
```

in both source families.

Decision:

```text
H3 BOTH exclusion = VALIDATION SHADOW ONLY
H3 is NOT part of the frozen primary candidate
```

If 2022 produces a BOTH +5R winner, the exclusion shadow is falsified. If it again produces no BOTH winner,
that is independent support, but it still must not be retrofitted into Candidate B during the validation run.

## 3.4 Delivery sub-branches: what generalized and what did not

Adaptive H2:

```text
EXP_ONLY   34 / 10 TP5 / 21 SL / 3 BE / EV +0.853R
OWNER_ONLY  6 /  4 TP5 /  2 SL          / EV +3.000R
```

Mentor-wave direct H:

```text
EXP_ONLY   27 / 8 TP5 / 17 SL / 2 BE / EV +0.852R
OWNER_ONLY  4 / 0 TP5 /  3 SL / 1 BE / EV -0.750R
```

The almost identical EXP_ONLY expectancy is notable. OWNER_ONLY is source-semantic dependent and therefore
must not become a new gate or sizing tier.

The previously observed `compact acceptance / M30 ATR` relationship also remains exploratory only because
its direction was not stable in the independent semantic cross-check.

---

# 4. Module L — final discovery classification

Primary causal architecture remains:

```text
virtual Candidate-A failure
-> higher context alive
-> deeper meaningful adaptive M15 liquidity
-> atomic same-M1 penetration + close recovery
-> fresh same-direction M5 re-acceptance
-> REAL Entry
-> checkpoint=min(1R,0.5 D1 ATR)
-> realize 50%
-> residual BE
-> residual +2R
```

Reference:

```text
11 trades
11 / 11 positive under current protected-runner payoff
7 / 11 residual +2R
mean +1.131R/trade
exact-mirror checkpoint 1 / 11
```

Residual-target replay confirmed that +2R is the strongest natural integer-R residual target:

```text
residual +2R: 7/11 reached / mean L payoff +1.131R
residual +3R: 3/11 / +0.903R
residual +4R: 2/11 / +0.858R
residual +5R: 0/11 / +0.494R
```

Decision:

```text
L Entry architecture = FROZEN FOR VALIDATION
L protected-runner payoff = FROZEN FOR VALIDATION
main weakness = sample density
```

## 4.1 Mentor-wave L expansion remains exploratory

Mentor-wave deep requalification produced four physical trades, of which two overlap the adaptive primary.
The two unique additions were:

```text
+0.5R
-1.0R
```

Physical union:

```text
13 trades
12 positive = 92.31%
mean +0.918R/trade
```

This is not enough unique evidence to expand L authority. Generic pivots and k=1.0-only additions remain
rejected.

---

# 5. H -> L lifecycle is retained, without hindsight routing

Five H2 losses are linked to later primary-L requalification through exact prior Candidate-A trigger identity.
All five are sequential:

```text
H resolves first
-> later L trigger occurs
```

Current L payoff makes four of the five linked H->L sequences net-positive.

The correct interpretation is:

```text
fast reload branch:
Candidate A -> H

if H fails and context remains alive:
correction can continue -> deeper reload -> L
```

This is not permission to skip H because L may appear later.

Episode identity is frozen as:

```text
reload_parent_id = (direction, Candidate-A trigger_time)
```

An L trade whose `prior_trigger_time` equals an actual H trigger belongs to the same temporal reload lifecycle.
An L trade without such an actual H fill remains a standalone deep-reload trade.

---

# 6. Correction to the previous overlap assumption

The prior V3-003E narrative said standalone L did not overlap H exposure in the current sample. A final H2
interval audit shows that statement was too strong.

Observed H/L active-position overlaps:

```text
3 H-L overlaps
- 1 opposite-direction overlap
- 2 same-direction overlaps
```

Observed H/H overlaps:

```text
3 H-H overlaps
- 1 opposite-direction overlap
- 2 same-direction overlaps
```

There were no L triggers inside the pending interval of the H fills that actually occurred, but active-position
overlap is real and must be governed explicitly.

This correction is material because the previous descriptive episode DD was not a fully authoritative portfolio
DD calculation.

---

# 7. Frozen exposure contract for Candidate B

Three canonical exposure descriptions were audited:

```text
ALL_INDEPENDENT
SERIAL_ONE_POSITION
OPPOSITE_DIRECTION_BLOCK
```

The selected contract is **not selected from P/L**. It is selected because it matches the existing deterministic
EA execution principle and resolves causal directional conflict without inventing a new score or risk threshold:

```text
same-direction coexistence / add-on = allowed
opposite-direction coexistence       = blocked
```

Every authorized H or L entry retains one nominal module-risk unit for research accounting. No new live sizing
or portfolio-risk percentage is authorized.

Discovery observed a maximum of three simultaneous same-direction positions under this rule. This is a risk
fact to carry into exact-tick/MT5 work, not permission to lever 3R live.

The two blocked discovery entries were H trades, but their outcomes were **not** used to select this policy.

---

# 8. Frozen validation candidate — V3_DUAL_RELOAD_CANDIDATE_B

The exact Level-A candidate to take into 2022 is now frozen as:

## Common substrate

```text
V3_RELOAD_CANDIDATE_A
M15 adaptive directional-change source k=2
active delivery state
strong M5 acceptance:
acceptance_margin > liquidity_penetration
```

Candidate A remains a timing/reaction substrate, not strategic-destination authority by itself.

## Module H in Candidate B

```text
Candidate A
-> clean M1 ownership path
-> first 50% accepted-leg pullback
-> direct M1 ownership transfer
-> sweep-extreme SL
-> +3R: realize 25%
-> residual SL -> BE
-> final +5R
```

`BOTH` exclusion is not included.

## Module L in Candidate B

```text
Candidate-A virtual failure
-> delivery context remains alive
-> deeper meaningful adaptive M15 liquidity
-> atomic same-M1 recovery
-> fresh same-direction M5 re-acceptance
-> real Entry
-> checkpoint=min(1R,0.5 D1 ATR)
-> realize 50%
-> residual BE
-> residual +2R
```

## Exposure in Candidate B

```text
same-direction coexistence allowed
opposite-direction coexistence blocked
```

## Discovery reference under the frozen combined contract

```text
53 accepted trades
positive trades = 28 / 53 = 52.83%
average positive = +2.775R
EV = +0.994R/trade
total = +52.69R
```

Annual descriptive cells:

| Year | N | Positive | Avg positive | EV |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 24 | 50.00% | +2.540R | +0.770R |
| 2024 | 17 | 58.82% | +2.620R | +1.130R |
| 2025 | 12 | 50.00% | +3.500R | +1.250R |

Leave-one-year-out for the exact k2/50 reference remains:

```text
omit 2023: positive 55.17% / EV +1.179R
omit 2024: positive 50.00% / EV +0.930R
omit 2025: positive 53.66% / EV +0.919R
```

These values include the recorded M1 spread model but **do not** yet include full commission/slippage/swap
or exact intrabar execution. They are not live expectancy claims.

---

# 9. What is frozen, shadowed, rejected, and still unsolved

```text
V3_RELOAD_CANDIDATE_A               FROZEN COMMON DEVELOPMENT BENCHMARK
V3_DUAL_RELOAD_CANDIDATE_B          FROZEN FOR ONE-TIME 2022 LEVEL-A VALIDATION

Module H2 direct-transfer            FROZEN INTO CANDIDATE B
H 50% pullback                       FROZEN REFERENCE GEOMETRY FOR VALIDATION
H +3R 25% harvest                    FROZEN CANDIDATE-B H MANAGEMENT
H3 BOTH exclusion                    SHADOW ONLY / NOT IN CANDIDATE B
H body-close invalidation            REJECTED AS MATERIAL IMPROVEMENT
H +2R 50% protection                 REJECTED AS PRIMARY CONTROL
OWNER_ONLY premium                   REJECTED AS GENERAL GATE
compact-acceptance ratio             EXPLORATORY ONLY

Module L adaptive deep reload        FROZEN INTO CANDIDATE B
Module L protected runner            FROZEN INTO CANDIDATE B
mentor-wave L union                  EXPLORATORY / NOT IN CANDIDATE B
generic-pivot L expansion            REJECTED
k=1.0-only L expansion               REJECTED

Exposure opposite-direction block    FROZEN VALIDATION EXECUTION CONTRACT
live sizing / portfolio risk %       UNSOLVED / NOT AUTHORIZED
exact tick execution                 NEXT ONLY AFTER 2022 OFFLINE VALIDATION
MT5 EA implementation                NOT AUTHORIZED
```

---

# 10. Discovery stop rule

The 2023-2025 data have now been used extensively. Continuing to mine them for another small filter would
increase overfit risk more than research value.

Therefore after this package is applied:

> **Do not add another 2023-2025 gate, threshold, exception, session veto, direction veto, or payoff tweak to
> Candidate B before the 2022 validation run.**

The discovery line is intentionally stopped here.

---

# 11. Next step

Read `V3_003F_VALIDATION_CONTRACT.md` before opening 2022.

The next legitimate strategy-research action is:

```text
freeze this repository state
-> obtain/verify GOLD# 2022 M1 without inspecting outcomes during rule design
-> run Candidate B exactly once at Level A
-> report PASS / FAIL / INCONCLUSIVE without retuning
```

2021 remains untouched.

No production EA change is authorized by V3-003F.
