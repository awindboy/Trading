# V10 Next Research Contract — R7G Causal Sizing / Execution Validation

Date: `2026-09-17`
Status: `ACTIVE FOLLOW-UP CONTRACT / SHADOW ONLY`
Market: `GOLD# ONLY`
Base checkpoint: `V10_R6_R7_ML_SIZING_AND_M1_ECONOMICS_CHECKPOINT_20260917.md`

## 1. Frozen hypothesis

Do not retune the R7G core on the already-consumed 2024-2026 evidence.

Frozen research semantics:

```text
base action = R4

only when R4 weight == 1:
    if R5 EV > 0
    and recent prior-exited eligible Child mean R over last 180 completed H4 bars > 0:
        shadow weight = 3
    else:
        shadow weight = 1

all other R4 weights remain unchanged
```

No direct next-HA prediction is added.
No new entry is created.
No R4 entry is removed.
No exit rule changes.

## 2. Immediate objective

Turn the promising consumed-data sizing observation into a reproducible, execution-compatible shadow experiment.

Required order:

1. exact row-level source population receipt;
2. exact R4/R5 input parity;
3. exact completed-H4 index parity from raw M1;
4. exact prior-exited feedback-set parity;
5. Python/MQL Boolean sizing-action parity;
6. actual-tick fill / spread / stop execution accounting;
7. account-risk lot calculation;
8. campaign committed-risk ledger;
9. future-only shadow logging.

## 3. Required reporting

Every economic report must show all three units separately:

```text
A. structural R
B. GOLD price-PnL / price movement
C. account-currency PnL under an explicitly stated lot/risk contract
```

Do not call price-PnL "actual dollars earned".

For B/C reports, include at minimum:

- gross profit;
- gross loss;
- net PnL;
- PF;
- win/loss counts;
- year;
- quarter;
- stage;
- direction;
- stage × direction;
- final run-length bucket;
- stop vs FAST-NHA exit;
- R4 vs R7G delta;
- upgrade-only economics;
- spread / cost sensitivity;
- maximum simultaneous committed risk.

## 4. Risk contract

Do not invent a campaign risk ceiling from the consumed data.

Instead, first persist the unconstrained committed-risk path under exact Child lot sizing.
Then study candidate campaign risk ceilings as explicit research hypotheses with their own ledgers.

A risk-cap scan must not silently become authority.

## 5. Negative-results guardrail

Do not reopen broad scans of:

- next-HA classifiers;
- generic negative-R classifiers;
- model families / hyperparameters;
- arbitrary feedback horizons;
- stage/direction exclusions;
- fixed no-chase / cooldown / retry rules.

The current evidence already shows that statistical predictability often fails to translate into sizing economics.

## 6. Validation boundary

All 2024-2026 historical rows are consumed development evidence.

`GOLD# 2021` remains sealed unless a separate, explicit, frozen validation contract releases it.

The preferred next evidence is future-only shadow data after the historical cutoff, with the R7G rule frozen before observation.

## 7. Promotion gate

R7G cannot become strategy / EA authority until all of the following hold:

- exact reproducibility receipt;
- exact Python/MQL action parity;
- actual-tick execution semantics;
- explicit account-risk lot sizing;
- campaign committed-risk accounting;
- cost-sensitive economics;
- forward-only evidence;
- no dependence on a post-hoc subgroup exclusion.
