# V3-003F — Candidate B Independent Validation Contract

Status: `FROZEN PRE-VALIDATION CONTRACT`  
Date: `2026-08-27`  
Candidate: `V3_DUAL_RELOAD_CANDIDATE_B`  
Validation data: `GOLD# 2022`  
2021: `UNTOUCHED`

## 1. Purpose

This file must be committed **before** the 2022 validation vault is opened.
Its purpose is to prevent post-validation threshold rescue.

2022 may answer whether Candidate B generalizes. It may not be used to redesign Candidate B.

## 2. Frozen definitions

The exact definitions are those in `V3_003F_DUAL_RELOAD_DISCOVERY_FREEZE.md`.
No 2022 result may change:

```text
Candidate-A source = M15 adaptive DC k=2
Candidate-A delivery-state definition
Candidate-A strong-acceptance definition

H clean-M1 requirement
H direct-transfer requirement
H pullback = 50% accepted leg
H sweep-extreme SL
H +3R 25% realize
H residual BE
H final +5R

L deep adaptive M15 requalification
L atomic same-M1 recovery
L fresh M5 re-acceptance
L checkpoint=min(1R,0.5D1 ATR)
L 50% realize
L residual BE
L residual +2R

exposure:
same-direction coexistence allowed
opposite-direction coexistence blocked
```

Not frozen into Candidate B:

```text
BOTH exclusion
mentor-wave L expansion
OWNER_ONLY preference
compact-acceptance thresholds
calendar/direction/session vetoes
```

## 3. One-run rule

The first complete 2022 Candidate-B Level-A run is the validation result.

If code/replay correctness is later shown to be wrong, a corrected rerun is allowed only when:

1. the bug is documented;
2. the correction is strategy-semantic neutral;
3. the original failed run is retained;
4. no threshold or rule is changed because of 2022 P/L.

## 4. Primary validation criteria

Primary combined Candidate-B criteria:

```text
realized positive-trade rate >= 50%
average positive trade > 1R
spread-adjusted Level-A expectancy > 0R
```

All three must hold for a clean `PASS`.

If sample size is too small for a useful conclusion, classify `INCONCLUSIVE`; do not loosen rules to manufacture
trades.

## 5. Module diagnostics

These diagnostics explain failure but do not change the primary contract.

### H2

Report:

```text
n / TP5 / SL / BE
EV under primary +3R->BE->5R
EV and positive rate under Candidate-B +3R 25% harvest
LONG/SHORT breadth
exact mirror +5R count
```

H is a high-R specialist. It does not independently need a >=50% positive rate, but its standalone expectancy
should remain positive for a healthy validation.

### L

Report:

```text
physical n
checkpoint rate
full +1R rate
residual +2R rate
mean realized R
exact-mirror checkpoint rate
```

Because L is sparse, a very small 2022 L sample may be `INCONCLUSIVE` rather than an automatic fail.
Do not change the L source family after seeing the result.

### H3 shadow

Record BOTH observations without affecting Candidate-B trades.

```text
If a 2022 BOTH H trade reaches +5R:
    BOTH exclusion shadow is falsified.

If no BOTH H winner occurs:
    record independent support only.
```

Do not insert the exclusion into the primary 2022 result.

## 6. Exposure diagnostics

Report:

```text
same-direction overlap count
opposite-direction blocked candidate count
maximum concurrent accepted positions
maximum nominal concurrent module-risk units
H->L linked lifecycle count
```

Do not introduce a new portfolio risk cap from 2022 P/L.
Sizing is a later execution/portfolio stage.

## 7. Cost and execution boundary

The 2022 Level-A result uses the same causal M1/Bid-Ask spread treatment as discovery.
It is not final production authority.

If Candidate B passes Level A:

```text
2022 PASS
-> exact-tick replay
-> commission/slippage/swap sensitivity
-> MT5 Strategy Tester reproduction
-> execution parity
-> only then EA implementation consideration
```

If Candidate B fails:

```text
record the failure
freeze the failed result
return to architecture research on a NEW discovery allocation
```

Do not tune Candidate B on 2022.

## 8. 2021 rule

2021 remains untouched regardless of the 2022 result until a new explicit research decision defines its role.
