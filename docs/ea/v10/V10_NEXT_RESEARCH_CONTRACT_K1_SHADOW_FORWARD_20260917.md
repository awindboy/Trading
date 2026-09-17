# V10 Next Research Contract — K1 Shadow Forward and EA Parity

Date: `2026-09-17`  
Status: `ACTIVE NEXT CONTRACT / NO TRADE AUTHORITY`

## 1. Objective

Test whether the R3 K1 extreme-STOP hypothesis survives genuinely future-hidden operation without changing its representation, preprocessing, hyperparameters, calibration method, or action semantics.

This contract does not authorize 2021 reserve use, live orders, or production promotion.

## 2. Frozen shadow hypothesis

```text
candidate population
= existing R2-selected k1 Child only

features
= exact 21-column K1_STOP_FEATURES order

preprocessing
= RobustScaler quantile_range=(10, 90)

classifier
= LogisticRegression C=0.5

calibration
= Platt sigmoid fit from chronological OOF predictions only

reference
= q97.5 of calibrated OOF k1 scores

shadow action
= veto this k1 Child only

catch-up
= none
```

Training evidence ends at raw M1 `2026-08-28 23:57:00`.

The current regenerated future-shadow threshold is recorded in the manifest under:

`results/r3_k1stop_20260917/V10_R3_K1STOP_FUTURE_SHADOW_MANIFEST_20260917.json`

It must not be recalculated from forward outcomes.

## 3. Gate A — resolve R2 policy semantics

Before R3 EA work, choose and document one R2 candidate-generator contract:

```text
per-Child conditional-NEUTRAL
or
run-latched admission
```

Current mismatch: six historical actions.

Required evidence:

- exact mismatch ledger;
- chosen semantic authority;
- Python and MQL candidate-generator parity with zero mismatches.

Do not hide this difference inside the R3 model.

## 4. Gate B — causal feature parity

Implement R3 as shadow instrumentation first.

For every R2-selected k1 event, persist:

```text
signal_id
decision_ts
21 ordered raw features
fitted RobustScaler center and scale application
raw logistic score
calibrated probability
frozen q97.5 reference
hypothetical veto / keep action
actual R2 action
```

Required checks:

- higher timeframes reconstructed from completed causal bars;
- previous-run features update only after the previous run resolves;
- no answer-sheet field enters the feature vector;
- Python and MQL feature values match within an explicit numeric tolerance;
- Python and MQL probability/action parity is exact at the Boolean decision level;
- signal clock uses the canonical `decision_ts / effective_ts` contract.

Until this gate passes, the model has no execution authority.

## 5. Gate C — future-only shadow collection

Forward evidence must begin strictly after the training cutoff.

Before collection starts, freeze and hash:

- model bundle;
- scaler state;
- coefficients and intercept;
- Platt slope/intercept;
- q97.5 reference;
- feature order;
- source/runtime version;
- evaluation horizon and stopping rule.

Do not tune on accumulating forward outcomes. Do not backfill missed events. Do not replace the threshold because the early sample is uncomfortable.

HistGB may be logged as a diagnostic disagreement score, but it has no veto authority.

## 6. Required forward evaluation

Evaluate the shadow policy against the unchanged R2 candidate generator:

```text
event count and risk units abstained
STOP precision among abstentions
positive-child and L6+ right-tail regret
delta raw PnL and structural R
PF_R and DD_R
run-block uncertainty
year / regime / direction breakdown
same-M1 execution ambiguity incidents
```

Judge decision quality before headline PnL.

## 7. Reserve rule

`GOLD# 2021` remains untouched.

Using it requires a separate explicit allocation decision that freezes the complete model/policy before opening the file. Nothing in this contract grants that authority.

## 8. Promotion boundary

The shadow candidate remains rejected for promotion if any of the following is true:

- Python/MQL feature or action parity is not exact;
- forward data are reused for threshold/model tuning;
- only aggregate metrics exist without event ledgers;
- benefit depends on one ambiguous intraminute convention;
- right-tail regret is hidden by a favorable headline;
- EA candidate-generation semantics differ from the research ledger;
- independent evidence is absent.

Passing this contract would justify a new validation decision, not automatic production deployment.

