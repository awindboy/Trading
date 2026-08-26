# V3-003G — Candidate B GOLD# 2022 Independent Validation Result

Status: `INDEPENDENT LEVEL-A VALIDATION RESULT / FAIL / NO PRODUCTION AUTHORITY`  
Date: `2026-08-27`  
Repository HEAD before validation: `551f6a16a54e4b234d9e1d7acaf2943dff1fd888`  
Candidate: `V3_DUAL_RELOAD_CANDIDATE_B`  
Validation market: `GOLD#`  
Validation period: `2022`  
Discovery/development period: `2023-2025 — CLOSED FOR CANDIDATE-B TUNING`  
2021: `UNTOUCHED`

## 0. Decision

The frozen Candidate B **fails** the one-time 2022 Level-A validation contract.

Frozen primary criteria were:

```text
realized positive-trade rate >= 50%
average positive trade > 1R
spread-adjusted Level-A expectancy > 0R
```

Observed Candidate-B result:

```text
24 accepted trades
6 positive
positive rate = 25.00%
average positive = +1.458R
expectancy = -0.385R/trade
total = -9.25R
max negative streak = 8
sequence drawdown ~= 10.25R
```

Therefore:

```text
positive rate >= 50%   FAIL
avg positive > 1R      PASS
expectancy > 0R        FAIL

FINAL CLASSIFICATION   FAIL
```

This is not classified `INCONCLUSIVE`. The accepted 2022 sample (`n=24`) is comparable
to a full discovery-year sample, and the exact Clopper-Pearson 95% interval for 6/24
positive trades is approximately:

```text
9.77% .. 46.71%
```

Even the upper 95% bound is below the pre-registered 50% target.

No Candidate-B threshold, filter, payoff rule, direction rule or exposure rule may be
changed using this 2022 outcome.

---

# 1. Validation-data audit

Input:

```text
GOLD#_M1_202201030100_202212302357.csv
SHA-256:
837efd61ff2240ea7b6a1af80517f7d979c7a11f7699560fa0cb0cc6166912d7
```

Coverage:

```text
rows                 354,439
start                 2022-01-03 01:00
end                   2022-12-30 23:57
duplicate timestamps  0
OHLC geometry errors   0
negative spread rows   0
```

Spread:

```text
median  18 points
mean    18.02 points
p90     25 points
p99     36 points
max     200 points
```

The CSV does not embed broker/account/server metadata, so exact environment identity
cannot be proven from the file alone. Its schema, symbol naming and spread scale are
compatible with the prior GOLD# discovery exports.

The validation used the same M1 Bid/Ask spread treatment as discovery.

---

# 2. Frozen definitions were not changed

The run used the pre-committed `V3_003F_VALIDATION_CONTRACT.md`.

Candidate B remained:

```text
Candidate-A M15 adaptive DC source k=2

Module H:
Candidate A
-> clean M1 path
-> direct M1 ownership transfer
-> 50% accepted-leg pullback
-> sweep-extreme SL
-> +3R realize 25%
-> residual BE
-> +5R

Module L:
virtual Candidate-A failure
-> context survives
-> deeper adaptive M15 liquidity
-> atomic same-M1 recovery
-> fresh M5 re-acceptance
-> checkpoint=min(1R,0.5 D1 ATR)
-> realize 50%
-> residual BE
-> residual +2R

Exposure:
same-direction coexistence allowed
opposite-direction coexistence blocked
```

Not inserted after seeing 2022:

```text
BOTH exclusion
mentor-wave L expansion
OWNER_ONLY preference
compact-acceptance threshold
direction/session/calendar veto
new risk cap
```

---

# 3. Candidate A already weakens upstream

2022 frozen k=2 Candidate A:

```text
39 candidates
17 reached +1R before SL
43.59% +1R survival
```

Direction:

```text
LONG   14 / 7 +1R = 50.0%
SHORT  25 / 10 +1R = 40.0%
```

The zero-spread counterfactual is also exactly `17/39 = 43.59%`.

Discovery reference was approximately:

```text
2023 60.0%
2024 65.5%
2025 63.0%
```

Therefore the validation failure begins before H/L payoff management. It is not primarily
explained by the Candidate-B exposure rule or by ordinary spread friction.

This is a diagnostic only. Candidate A is not retuned on 2022.

---

# 4. Module H2 validation — FAILS standalone health diagnostic

Frozen H2 50% pullback:

```text
20 fills
1 TP5
16 SL
3 BE
```

Primary H payoff (`+3R -> BE -> +5R`):

```text
EV = -0.550R/trade
```

Candidate-B harvest payoff:

```text
positive = 4/20 = 20.0%
average positive = +1.688R
EV = -0.463R/trade
```

Direction breadth:

```text
SHORT:
12 trades
1 TP5 / 11 SL / 0 BE
primary EV  -0.500R
harvest EV  -0.542R

LONG:
8 trades
0 TP5 / 5 SL / 3 BE
primary EV  -0.625R
harvest EV  -0.344R
```

Both directions are negative.

## 4.1 Exact mirror reverses the discovery relationship

Same physical H2 fill time and same risk, reverse direction:

```text
original +5R = 1/20
exact mirror +5R = 6/20
```

By original trade direction:

```text
SHORT originals: 1/12 TP5
their mirrors:    4/12 TP5

LONG originals:  0/8 TP5
their mirrors:    2/8 TP5
```

This is strong evidence that the directional/reload relationship found in 2023-2025 does
not generalize unchanged into 2022.

Do not convert this into a reversal strategy using 2022.

## 4.2 Direct-transfer remains selective, but is insufficient

Before H2 direct eligibility, the 2022 50% H population was:

```text
24 fills
1 TP5
19 SL
4 BE
```

Non-direct:

```text
4 fills
0 TP5
3 SL
1 BE
```

Direct transfer still removes only non-winners in this year, but the retained direct
population itself has negative expectancy. Thus:

```text
direct-transfer relationship = still selective
direct-transfer + current higher-state architecture = not sufficient to generalize
```

---

# 5. H3 / BOTH validation shadow

The pre-registered H3 shadow diagnostic produced:

```text
BOTH fills = 5
TP5        = 0
SL         = 4
BE         = 1
```

So 2022 gives independent support to the prior observation that BOTH is poor for +5R H.

However:

```text
H3 was NOT part of Candidate B
```

and must **not** be inserted retroactively to rescue the failed primary validation.

The shadow is supported; Candidate B still fails.

Other branch diagnostics:

```text
EXP_ONLY:
11 trades / 0 TP5 / 9 SL / 2 BE / primary EV -0.818R

OWNER_ONLY:
4 trades / 1 TP5 / 3 SL / primary EV +0.500R
```

The discovery EXP_ONLY robustness does not survive 2022. Do not create a 2022-derived
OWNER_ONLY gate.

---

# 6. Module L validation — FAILS precision relationship

Primary L physical population:

```text
5 trades
checkpoint hit      2/5 = 40%
full +1R            2/5 = 40%
residual +2R        1/5 = 20%
mean realized R     -0.200R/trade
```

Exact mirror checkpoint:

```text
3/5 = 60%
```

The five realized L payoffs were:

```text
+0.5R
-1.0R
-1.0R
-1.0R
+1.5R
```

This is not merely a small-sample absence of extra runners. The primary checkpoint
relationship itself reverses relative to discovery:

```text
discovery primary L:
original checkpoint 11/11
mirror checkpoint    1/11

2022 validation:
original checkpoint  2/5
mirror checkpoint    3/5
```

Module L is sparse, but this result is clearly negative diagnostic evidence rather than a
reason to expand the source family on 2022.

---

# 7. H -> L lifecycle also fails to reproduce economically

Four of the five 2022 L trades were linked to an actual H2 parent trigger.

Linked sequence nets under Candidate-B H management plus current L payoff:

```text
-0.5R
-2.0R
-2.0R
+0.5R
```

Therefore:

```text
linked H->L lifecycles = 4
net-positive          = 1/4
```

Discovery had shown a much more constructive recovery relationship.

The causal linkage still exists mechanically; its economic recovery property does not
generalize to 2022.

---

# 8. Frozen exposure rule is not the cause of failure

Diagnostic-only policy comparison:

```text
ALL_INDEPENDENT
25 trades
positive 24.0%
EV -0.410R

SERIAL_ONE_POSITION
23 trades
positive 21.74%
EV -0.435R

FROZEN OPPOSITE_DIRECTION_BLOCK
24 trades
positive 25.0%
EV -0.385R
```

The frozen policy blocks one H entry, which was a losing H trade.

Final frozen exposure diagnostics:

```text
opposite-direction blocked candidates = 1
maximum concurrent accepted positions = 2
maximum nominal concurrent module-risk units = 2
accepted same-direction overlap pairs = 1
```

The strategy remains strongly negative under every canonical exposure description.
Exposure ordering does not explain the validation failure.

---

# 9. Why this is a genuine validation failure

The failure is broad:

```text
Candidate A +1R survival       weak
H2 standalone expectancy       negative
H exact mirror                 stronger than original
L checkpoint precision         weak
L mirror                       stronger than original
H->L recovery economics        weak
combined positive rate         25%
combined expectancy            negative
```

At the same time:

```text
trade count                    sufficient for an annual validation read
average positive payoff        still >1R
BOTH shadow                    remains negative
direct-transfer non-direct set remains non-winning
```

The problem is therefore not that all prior research was meaningless. Several local
relationships persist, but the **complete directional reload architecture does not generalize
as frozen**.

This distinction matters:

```text
some components retain descriptive structure
!=
Candidate B passes independent validation
```

Candidate B fails.

---

# 10. Governance decision after the FAIL

2022 status is now:

```text
CONSUMED INDEPENDENT VALIDATION
DO NOT USE TO RETUNE CANDIDATE B
```

Candidate B status:

```text
FROZEN FAILED VALIDATION ARTIFACT
NOT ELIGIBLE FOR EXACT-TICK / MT5 PROMOTION
```

2023-2025 status for Candidate B:

```text
DISCOVERY HISTORY
DO NOT REOPEN FOR THRESHOLD RESCUE
```

2021:

```text
UNTOUCHED
```

Do not inspect 2021 to rescue Candidate B.

The next architecture-research cycle requires a **new discovery allocation selected before
looking at its outcomes**. Possible future allocations may include a pre-frozen GOLD-like
cross-market universe or a later independent GOLD period, but that decision belongs to a new
research protocol.

No exact-tick promotion, MT5 implementation, EA change or live-trading authority follows
from this validation.

---

# 11. One-line result

> `V3_DUAL_RELOAD_CANDIDATE_B` does not survive GOLD# 2022 independent Level-A validation:
> the positive rate falls to 25% and expectancy to -0.385R/trade, with both H and L directional
> evidence weakening or reversing; freeze the failure, consume 2022, keep 2021 untouched, and
> start any next architecture cycle only on a newly pre-registered discovery allocation.
