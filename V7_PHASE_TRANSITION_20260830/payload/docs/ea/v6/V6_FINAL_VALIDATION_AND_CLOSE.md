# V6 Final Validation and Close

Status: `CLOSED / NO PROMOTED STRATEGY`
Date: `2026-08-30`
Final code control: `MentorDeterministicV6EA.mq5` R0.3 lineage
Production authority: `NONE`

## 1. Why V6 is closed

V6 built a role-conditioned H/L1/L2 architecture that looked strong on the consumed
13-market-year panel but failed to retain the combined edge in factor-diverse external/temporal validation.

The user has decided not to continue developing the previous mentor-style trading method.

V6 is therefore closed as a strategy-development generation.

## 2. Frozen consumed control

```text
H + L1 + L2
N 253
WR 54.55%
avg positive 1.269R
EV +0.304R
net +76.96R
11/13 market-years positive
```

This was always a research freeze, not production authority.

## 3. MT5 R0.3 parity/economics milestone

R0.3 corrected:
- feature warmup borrowing;
- sweep-time D14/D24 prior snapshot semantics.

GOLD population parity:
- M5 annual events: 113 / 84 / 86 / 67
- fills: 20 / 17 / 13 / 12
- total fills: 62

Observed MT5 composite on the GOLD control:

```text
N 62
WR 50.0%
avg positive about 1.514R
EV about +0.345R
net about +21.36R
```

The historical scratch-ledger reproducibility caveat remains documented.

## 4. Gold-family external replication

New XM Ultra Low Gold-family histories:
- XAUJPY#
- XAUCNH#
- GAUCNH#
- GAUUSD#

They were highly correlated and therefore count as one Gold-family replication,
not four independent confirmations.

Descriptive pooled result:

```text
N 52
WR 55.77%
avg positive 0.874R
EV +0.093R
net +4.825R
```

Module decomposition:

```text
H  N4  WR 0%      EV -1.000R
L1 N15 WR 66.67%  EV +0.407R
L2 N33 WR 57.58%  EV +0.082R
```

Interpretation:
hit rate partially replicated, but the H payoff role did not.

## 5. 2026 factor-diverse holdout

Markets:
- GOLD#
- BTCUSD#
- USDJPY#

Carry-aware descriptive result:

```text
N 42
WR 45.24%
avg positive 1.013R
EV -0.034R
net -1.432R
```

By module:

```text
H  N8  WR 25.00%  avg positive 2.625R  EV -0.094R
L1 N15 WR 26.67%  EV -0.443R
L2 N19 WR 68.42%  EV +0.314R
```

Interpretation:
- combined frozen architecture failed;
- L1 portable hit-rate hypothesis failed;
- H multi-R function appeared, but edge was not validated;
- L2 was the most repeatable module.

## 6. L2 conclusion

L2 (`ONE_RENEG + D24 aligned`) is retained as a **historical research finding**.

It is not promoted as a standalone final strategy because:
- payoff architecture remains too small;
- project final avg-positive target is not solved;
- cost-adjusted independent proof is incomplete;
- the user is closing this strategy family.

D24-age remains shadow-only historical evidence.
Do not tune or revive it under V6.

## 7. Final V6 decision

```text
COMBINED V6: FAILED EXTERNAL/TEMPORAL VALIDATION
H: PAYOFF FUNCTION OBSERVED, EDGE NOT VALIDATED
L1: FAILED TO REPLICATE
L2: REPLICATED AS RESEARCH FINDING, NOT FINAL STRATEGY
PRODUCTION: NONE
```

No threshold rescue.

No further strategy-semantic V6 development.

Allowed future V6 work is limited to:
- reproducibility,
- archival correction,
- parity bug documentation,
- historical comparison.

V7 is the active generation.
