# V8 Research Inference Guardrails Addendum — 2026-09-03

Status: `ACTIVE PROJECT RULE`
Production authority: `NONE`
Market: `GOLD#`
Reserve: `GOLD# 2021 UNTOUCHED`

## 1. Why this addendum exists

During V8-A-N-SLOW research, several useful components were at risk of being discarded because a downstream formulation failed. The recurring error was **declaring the strategy or signal "failed" before identifying exactly which causal question, transfer, execution wrapper, or payoff architecture had failed**.

This addendum prevents that mistake from recurring.

## 2. Failure must be named at the correct level

Never use the unqualified statement `V8 failed` or `the signal failed` when only one downstream test was negative.

Use one of the following levels:

1. `DATA / PARITY FAILURE`
   - raw-data mismatch, wrong ATR anchoring, population reconstruction mismatch, timestamp/execution mismatch, censoring error, or instrumentation interference.
   - This is **not strategy evidence**.

2. `SEMANTIC / TARGET MISMATCH`
   - a feature predicts a different object than the one being tested.
   - Example: structural retention is not the same as same-direction movement; P15 is movement-onset probability, not terminal persistence.

3. `INCREMENTAL-FEATURE FAILURE`
   - a feature adds no information after proper causal controls.
   - Example: repeatedly recomputed micro3 adds little after geometry/process controls.
   - This does **not** erase its valid acceptance-time ranking role.

4. `TRANSFER FAILURE`
   - a relation valid in another architecture does not transfer to current Slow-N ACCEPTANCE.
   - Example: older N2 M1 synchronization and B34 directional efficiency did not transfer.
   - The historical result remains valid in its original population unless separately falsified.

5. `ENTRY / DIRECTION FAILURE`
   - the tested entry-direction formulation is not economically predictive.
   - This does not invalidate movement onset, structural state, or winner-continuation evidence.

6. `EXIT / PAYOFF FAILURE`
   - a specific stop/TP/runner/timeout wrapper fails.
   - This does not automatically invalidate the upstream setup.

7. `CAPITAL-ALLOCATION FAILURE`
   - the edge is too small, too overlapping, or too coarse for account constraints/minimum lot.
   - This is an implementation/economic issue, not automatically a signal failure.

8. `FULL STRATEGY FAILURE`
   - allowed only after a fully specified, executable, cost-adjusted, preregistered end-to-end system fails across its intended validation scope without a narrower explanation above.

## 3. Mandatory decomposition before any negative verdict

Before closing a branch, write explicitly:

```text
What exactly was predicted?
What exact population was used?
What information was causal at the decision time?
Was the result incremental over the correct geometry/state control?
Was the failure about direction, survival, continuation, exit, execution, or capital sizing?
Did the relation fail in later-year / direction / P0-P2 robustness, or only in one cell?
Does a negative downstream wrapper actually contradict the upstream claim?
```

If these cannot be answered, do not issue a strategy-level verdict.

## 4. Specific V8 corrections now permanent

### 4.1 Retention is not movement

`structure intact` means the accepted structure survived; it does not mean price delivered a large same-direction excursion.

Longer survival mainly increases further survival probability. It barely changes the next-15m movement distribution by itself.

### 4.2 Progress is a distinct winner-continuation question

Among retained structures, realized early movement matters. `MFE15/S` materially ranks later large extension, especially +0.50S and +0.75S outcomes.

Therefore do not discard retention because it is not direction alpha, and do not call progress a replacement for retention. They answer different questions.

### 4.3 Structural break is not automatically the trade stop

Wick damage and even close damage can occur before eventual large winners. A structural label can remain useful as a state variable without being the final executable stop.

### 4.4 MFE is opportunity, not capturable P/L

Large observed MFE does not authorize assuming perfect capture. Exit architecture must be tested separately and causally.

### 4.5 Aggregate expectancy is not an account replay

Average R tables do not answer what a real USD 1,000 account with 0.01-lot granularity, overlapping trades, margin use, spread, and dynamic risk sizing would have experienced.

A chronological replay is required before any account-level conclusion.

### 4.6 P0/P2 are not two simultaneously traded strategies by default

P0 is the deterministic Phase-0 execution realization. P2 is an alternate deterministic de-overlap realization used for robustness. Do not combine their trades or cherry-pick the better realization unless a future architecture explicitly preregisters that behavior.

For the current realistic account replay, use **one chronological P0 execution path** and leave P2 outside the trading decision.

## 5. No variant treadmill

Do not respond to one disappointing P/L table by immediately creating another TP/SL/filter variant.

Before creating a new variant, state which previously supported mechanism it is intended to test. If it only exists to improve a viewed P/L number, reject it as outcome tuning.

A negative architecture can be archived as `wrapper-negative` while preserving upstream evidence for later refinement.

## 6. Evidence-status vocabulary

Use these labels consistently:

- `SUPPORTED MECHANISM`
- `SUPPORTED RANKING SIGNAL`
- `COMPONENT-NEGATIVE`
- `TRANSFER-FAIL`
- `ECONOMIC-WRAPPER-NEGATIVE`
- `EXECUTION / DATA FAIL-CLOSED`
- `UNRESOLVED`
- `FULL STRATEGY FAILURE` only under Section 2.8

## 7. Current preserved V8 evidence

The following evidence remains alive and must not be discarded merely because one economic wrapper is weak:

- Slow-N P15 fresh75: movement-episode onset / excursion opportunity.
- reveal -> pullback -> reclaim: causal ACCEPTANCE lifecycle.
- micro3: acceptance-time structural-quality prior.
- dynamic geometry/process: structural survival/damage hazard.
- PRISTINE / DAMAGED / CLOSE_BROKEN: structural state semantics.
- realized early MFE among intact structures: winner-continuation ranking, especially for larger future extension.
- fixed GOLD points are nonstationary relative to H4 ATR scale S.

Separately, repeated tested **GOLD-internal static ACCEPTANCE direction filters** are closed as a research branch. That closure must not be generalized to the modules above.

## 8. Reserve

`GOLD# 2021` remains locked and untouched.
